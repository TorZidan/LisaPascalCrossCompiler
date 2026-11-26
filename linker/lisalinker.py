#!/usr/bin/env python3
"""lisalinker - a linker for Lisa Pascal object files that writes the same
linked program as the Lisa Workshop's Linker.

    lisalinker.py [-w 3.0] [-p] -o OUT[.OBJ] [-m MAP.txt] INPUT ...
    lisalinker.py -i [-s OLD=NEW] [--iulib INTRINSIC.LIB] -o LIB[.OBJ] INPUT ...

Inputs, in order, as on the Lisa (e.g. QD/M/BOXES.TEXT):
  * the main program and other unlinked modules (as written by the code
    generator or the assembler),
  * regular units (unit files: a UnitBlock, then their modules),
  * intrinsic libraries (IOSPASLIB, IOSFPLIB, ...): their entry points
    have absolute addresses; references to them become IU traps.

The rules below were derived from the format description in the Lisa
Development System Internals Documentation (Feb 1984, pp.102-141) and checked
byte for byte against the Workshop-linked BOXES and QDSAMPLE (README.md).
  1. Module selection: starting from the main program (the module with a
     StartAddress block), every module that is referenced, directly or
     indirectly, is included.  LinkNames that start with '$' are local to
     their file.
  2. Segments: modules are grouped by their SegmentName, the blank (main)
     segment first, then in the order the names first appear in the input
     files; within a segment in input order.  Segments get MMU numbers from
     18 up (logical address = MMU * 128K); the code starts 8 bytes into the
     segment, after the CodeBlock header.
  3. References (ShortExternal: a 16-bit field at the reference, the
     instruction word in front of it):
       same segment       PC-relative       JSR/JMP/PEA/LEA d(PC)
       other segment      jump table        JSR/JMP/PEA/LEA d(A5)
       intrinsic unit     IU trap           IUJSR/IUJMP/IUPEA/IULEA
     CommonReloc: the 16-bit A5 offset gets the base of the unit's globals,
     which lie below the main program's in the order the Lisa Linker's
     depth-first search reaches them (see layout_globals).
  4. Output: VersionCtrl, UnitTable, Executable (segment table, jump table),
     SegmentTable, then per segment ModuleName 'MainProg', [StartAddress],
     CodeBlock, EndBlock, and EOFMark.
  5. With -p, the code segments are packed (lisapack.py), as PACKSEG does.
  6. With -i, intrinsic units are linked into an intrinsic library
     (lisaintrinsic.py).
Not done yet: External (32-bit) references and Relocation blocks.
"""
from __future__ import annotations

import argparse
from collections.abc import Callable, Collection, Iterable
import itertools
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lisaobj import (
    CODEBLOCK, COMMONRELOC, ENDBLOCK, ENTRYPOINT, EOFMARK, EXECUTABLE,
    EXTERNAL, MODULENAME, OSDATA, PHYSICALEXEC, RELOCATION, SEGMENTTABLE,
    SHORTEXTERNAL, STARTADDRESS, UNITBLOCK, UNITTABLE, VERSIONCTRL,
    be16, be32, block, name8, pack_name8, pad512, read_blocks, sbe16,
)

# What the Workshop versions' Linkers do differently (1.0 and 2.0 are the same):
#   first_mmu     MMU number of the program's first segment
#   version_ctrl  the VersionCtrl block (its fields are "reserved")
#   os_data       an OSData block of that many zero bytes after VersionCtrl
#   jt_old_stuff  the "Old Stuff" after the jump table descriptors:
#                 MOVEA.L (A0)+,A1; MOVE.L A0,-(A7); JMP (A1)
PROFILES = {
    '2.0': dict(first_mmu=18, version_ctrl=struct.pack('>6L', 0x10000, 0x10000, 0x17F00, 0, 0, 0),
                os_data=0, jt_old_stuff=bytes.fromhex('22582f084ed1')),
    '3.0': dict(first_mmu=1, version_ctrl=bytes(24), os_data=514, jt_old_stuff=b''),
}
PROFILES['1.0'] = PROFILES['2.0']
SEG_SIZE = 0x20000             # 128 KB per MMU
JT_SEG_DELTA = 256             # Executable header values the Workshop linker writes
STK_SEG_DELTA = 256


class LinkError(Exception):
    """error raised when linking fails (missing files, undefined symbols, or unsupported relocations)"""
    pass


def name_key(name: str) -> str:
    """the order in which the Linker sorts LinkNames (jump table
    descriptors, intrinsic jump vectors): '$' and '%' after all letters
    (a '$' label after the procedures: the Canon printer driver; '%' names
    after the others: IOSPASLIB), and a name after the longer names it is a
    prefix of (LINETO before LINE: QDSAMPLE)"""
    return name.translate(NAME_ORDER).ljust(8, '\x7f')


NAME_ORDER = str.maketrans({'$': '\x7d', '%': '\x7e'})


def pc_relative(op: int) -> int:
    """the d(PC) form of a JSR, JMP, PEA or LEA instruction word that has an
    absolute address (abs.W or abs.L, as in assembler modules): the Linker
    makes them PC-relative (JSR abs.L: BOXES; LEA abs.W: SYS1LIB)"""
    if (op & 0x3F) in (0x38, 0x39) and ((op & 0xFFC0) in (0x4E80, 0x4EC0, 0x4840) or (op & 0xF1C0) == 0x41C0):
        return (op & ~0x3F) | 0x3A
    return op


class Module:
    """an unlinked object module parsed from a ModuleName..EndBlock sequence"""
    def __init__(self, f: InputFile, name: str, segname: str) -> None:
        self.file = f              # InputFile
        self.name = name
        self.segname = segname
        self.entries = []          # [(linkname, username, loc)]
        self.shortrefs = []        # [(linkname, username, [offsets])]
        self.longrefs = []         # [(linkname, username, [offsets])]
        self.commonrefs = []       # [(unitname, [offsets])]
        self.blockrefs = []        # [('ent' | 'ext' | 'com', name)] in block order
        self.relocs = []           # [offsets]
        self.start = None          # (start, gsize) of the main program
        self.code = b''
        self.seg = None            # Segment, once placed
        self.offset = None         # offset of the code in its segment

    def key(self, linkname: str) -> tuple[int, str] | str:
        """the symbol table key of a name referenced or defined here"""
        return (self.file.index, linkname) if linkname.startswith('$') else linkname


class InputFile:
    """a parsed Lisa object input file: unlinked modules, a regular unit, or an intrinsic library"""
    def __init__(self, path: str, index: int) -> None:
        self.path = path
        self.index = index
        self.data = open(path, 'rb').read()
        self.blocks = read_blocks(self.data)
        self.kind = 'modules'      # 'modules', 'unit', 'library'
        self.unit = None           # (name, globalsize, unittype) of a unit file
        self.modules = []
        self.lib_entries = {}      # library: linkname -> absolute address
        self.lib_entry_segs = {}   # library: linkname -> segment name
        self.lib_units = []        # library: [(name, number, type)]
        self.lib_segments = []     # library: [(name, number, v1, v2)]
        self.read()

    def read(self) -> None:
        """classify the file and extract its unit metadata, library tables, or unlinked modules"""
        if self.blocks and self.blocks[0].type == VERSIONCTRL:
            self.kind = 'library'
        m = None
        for b in self.blocks:
            d, t = b.body, b.type
            if t == UNITBLOCK and self.kind != 'library':
                self.kind = 'unit'
                self.unit = (name8(d, 0), be32(d, 20), be16(d, 24))
                self.unit_text = (be32(d, 12), be32(d, 16))    # file address and size of the interface pages
            elif t == UNITTABLE and self.kind == 'library':
                for i in range(be16(d)):
                    q = 4 + 12 * i
                    self.lib_units.append((name8(d, q), be16(d, q + 8), be16(d, q + 10)))
            elif t == SEGMENTTABLE and self.kind == 'library':
                for i in range(be16(d)):
                    q = 2 + 18 * i
                    self.lib_segments.append((name8(d, q), be16(d, q + 8), d[q + 10:q + 14], d[q + 14:q + 18]))
            elif t == MODULENAME:
                m = Module(self, name8(d, 0), name8(d, 8))
            elif t == ENTRYPOINT:
                ln = name8(d, 0)
                if self.kind == 'library':
                    if ln not in self.lib_entries:
                        self.lib_entries[ln] = be32(d, 16)
                        self.lib_entry_segs[ln] = m.segname if m is not None else ''
                else:
                    m.entries.append((ln, name8(d, 8), be32(d, 16)))
                    m.blockrefs.append(('ent', ln))
            elif t == SHORTEXTERNAL:
                m.shortrefs.append((name8(d, 0), name8(d, 8), [be16(d, i) for i in range(16, len(d), 2)]))
                m.blockrefs.append(('ext', name8(d, 0)))
            elif t == EXTERNAL:
                m.longrefs.append((name8(d, 0), name8(d, 8), [be32(d, i) for i in range(16, len(d), 4)]))
                m.blockrefs.append(('ext', name8(d, 0)))
            elif t == COMMONRELOC:
                m.commonrefs.append((name8(d, 0), [be32(d, i) for i in range(8, len(d), 4)]))
                m.blockrefs.append(('com', name8(d, 0)))
            elif t == RELOCATION:
                m.relocs.extend(be32(d, i) for i in range(2, len(d), 4))
            elif t == STARTADDRESS:
                m.start = (be32(d, 0), be32(d, 4))
            elif t == CODEBLOCK:
                m.code = d[4:]
            elif t == ENDBLOCK and m is not None:
                if self.kind != 'library':
                    self.modules.append(m)
                m = None


class Segment:
    """a program code segment assigned to an MMU slot (base = MMU * 128 KB)"""
    def __init__(self, name: str, mmu: int) -> None:
        self.name = name
        self.mmu = mmu
        self.base = mmu * SEG_SIZE          # CodeBlock address
        self.modules = []
        self.image = bytearray()

    def code_addr(self, offset: int) -> int:
        """logical 24-bit address of byte offset in this segment (8 bytes past the CodeBlock header)"""
        return self.base + 8 + offset


class Linker:
    """Lisa Workshop Linker: selects reachable modules, lays out segments, globals, and jump table, and patches code"""
    def __init__(self, paths: Iterable[str], workshop: str = '3.0') -> None:
        self.profile = PROFILES[workshop]
        self.files = [InputFile(p, i) for i, p in enumerate(paths)]
        self.symbols = {}         # key -> (Module, loc)
        self.intrinsic = {}       # linkname -> absolute address
        self.warnings: list[str] = []
        self.remap_local_names()
        defined_in: dict[str, tuple[str, str]] = {}
        for f in self.files:
            fname = os.path.basename(f.path)
            for name, addr in f.lib_entries.items():
                seg = f.lib_entry_segs.get(name, '')
                if not name.startswith('$'):
                    if name in defined_in:
                        first_file, _ = defined_in[name]
                        where = f'{seg} ({fname})' if seg else fname
                        self.warnings.append(
                            f'Warning - Duplicate entry definitions: entry {name.strip()} in {where} (keeping {first_file})'
                        )
                    else:
                        defined_in[name] = (fname, seg)
                self.intrinsic.setdefault(name, addr)
            for m in f.modules:
                for ln, un, loc in m.entries:
                    if not ln.startswith('$'):
                        if ln in defined_in:
                            first_file, _ = defined_in[ln]
                            where = f'{m.segname} ({fname})' if m.segname else fname
                            self.warnings.append(
                                f'Warning - Duplicate entry definitions: entry {ln.strip()} in {where} (keeping {first_file})'
                            )
                        else:
                            defined_in[ln] = (fname, m.segname)
                    self.symbols.setdefault(m.key(ln), (m, loc))

    def remap_local_names(self) -> None:
        """the names the Linker gives the file-local names ($nnnnnnn: the
        compiler's names of nested procedures), which it sorts by
        (CVTLOCAL, LOCALNAM, INCLNAME): the digits are a decimal number
        written backwards ($9100000 is 19); the Linker adds a base to it and
        writes it back the same way, zero-padded.  The base is 0 for the
        first file, then 1 + the highest number so far."""
        self.local_name = {}      # (file index, linkname) -> the Linker's name
        base = top = 0
        for f in self.files:
            names = set()
            for m in f.modules:
                for ln, un, loc in m.entries:
                    names.add(ln)
                for ln, un, offs in m.shortrefs + m.longrefs:
                    names.add(ln)
            for ln in names:
                digits = ln[1:].rstrip()
                if ln.startswith('$') and digits.isdigit() and len(ln) <= 8:
                    n = int(digits[::-1]) + base
                    top = max(top, n + 1)
                    # 7 digits, the lowest first
                    self.local_name[(f.index, ln)] = '$' + str(n % 10 ** 7).rjust(7, '0')[::-1]
            base = top

    def sort_name(self, m: Module, ln: str) -> str:
        """the name the Linker sorts a symbol by"""
        return self.local_name.get((m.file.index, ln), ln) if ln.startswith('$') else ln

    # ---- 1. module selection ----
    def select(self) -> None:
        """select all modules reachable from the single main program and check for undefined symbols"""
        mains = [m for f in self.files for m in f.modules if m.start is not None]
        if not mains:
            raise LinkError('no main program among the inputs (a unit is not linked on its own, '
                            'but as part of the program that uses it)')
        if len(mains) > 1:
            raise LinkError('%d main programs: %s' % (len(mains), ' '.join(m.name for m in mains)))
        self.main = mains[0]
        keep, todo = set(), [self.main]
        self.undefined = set()
        while todo:
            m = todo.pop()
            if id(m) in keep:
                continue
            keep.add(id(m))
            for ln, un, offs in m.shortrefs + m.longrefs:
                k = m.key(ln)
                if k in self.symbols:
                    todo.append(self.symbols[k][0])
                elif ln not in self.intrinsic:
                    self.undefined.add(ln)
        self.modules = [m for f in self.files for m in f.modules if id(m) in keep]
        if self.undefined:
            msg = 'undefined: ' + ' '.join(sorted(self.undefined))
            hints = where_defined(self.undefined, [f.path for f in self.files])
            if hints:
                msg += '\n' + '\n'.join('  defined in %s (boot folder): %s' % (lib, ' '.join(sorted(names)))
                                         for lib, names in hints.items())
            raise LinkError(msg)

    # ---- 2. segments ----
    def place(self) -> None:
        """assign MMU numbers to segments in first-appearance order (main segment first) and concatenate module code"""
        # segment order: the order in which the segment names first appear
        # among all modules of the input files (also modules that are not
        # linked in: checked against QDSAMPLE, where QDMisc comes before
        # Hardware although its first linked module comes after Hardware's).
        # A segment none of whose modules is linked is still a segment, with
        # an MMU number but no code (LisaDesk's flrDebug)
        names = []
        for f in self.files:
            for m in f.modules:
                if m.segname not in names:
                    names.append(m.segname)
        names.sort(key=lambda n: n != '')         # the main segment (blank name) first
        used_mmus = {n for f in self.files for (_, n, _, _) in f.lib_segments}
        self.segments, byname, mmu = [], {}, self.profile['first_mmu']
        for n in names:
            while mmu in used_mmus:
                mmu += 1
            byname[n] = Segment(n, mmu)
            self.segments.append(byname[n])
            mmu += 1
        for m in self.modules:
            s = byname[m.segname]
            m.seg, m.offset = s, len(s.image)
            s.modules.append(m)
            s.image += m.code

    def address(self, m: Module, ln: str) -> tuple[int, Module]:
        """absolute address of a symbol referenced from module m"""
        tm, loc = self.symbols[m.key(ln)]
        return tm.seg.code_addr(tm.offset + loc), tm

    # ---- unit globals ----
    def layout_globals(self) -> None:
        """Regular units' globals lie below the main program's globals: the
        first unit's area ends at A5 - MainSize, the next one below it, and
        so on.  The order is the one in which the Lisa Linker's depth-first
        search first reaches each unit (DFSDIR of ObjIOLib's GRAPHS unit,
        whose tree-arc callback allocates a unit's area and prints "Global
        area: UNIT at $offset"; read from the Workshop 3.0 Linker.Obj):

        * The graph has a vertex per module and per regular unit.  The
          Linker reads the input files in order and, in each module, its
          blocks in order; every reference (an External or ShortExternal
          block to a name of a module in the inputs, or a CommonReloc to a
          regular unit) adds an arc from the module.
        * A reference to a name that no module read so far defines (or to
          a unit whose unit file was not read yet) goes to a placeholder for
          the name.  When a module defining the name (or the unit's file) is
          read, every arc to the placeholder is moved to it: re-added, newest
          first, from the same source.
        * ObjIOLib's ADDARC puts a new arc at the head of its source's arc
          list, and the search follows the list from the head: the newest
          arc first.  The search starts at the main program's module, and
          a unit's area is allocated when the unit is first reached.

        Checked against BOXES and QDSAMPLE (Workshop 1.0/2.0 Linker) and
        the Canon and C.Itoh printer drivers (Workshop 3.0 Linker).  Units
        that are never reached get no space and do not count in DataSize
        (QDSAMPLE, which does not use Graf3D)."""
        self.main_size = self.main.start[1]
        sizes = {f.unit[0]: f.unit[1] for f in self.files if f.kind == 'unit'}
        regular = set(sizes) - set(self.intrinsic_units)
        clock = itertools.count()
        arcs = {}              # vertex -> [(time, target)]
        waiting = {}           # placeholder name -> [(time, source)]
        found = {}             # name -> vertex

        def add_arc(source: int, name: str | tuple[int, str] | tuple[str, str]) -> None:
            if name in found:
                arcs.setdefault(source, []).append((next(clock), found[name]))
            else:
                waiting.setdefault(name, []).append((next(clock), source))

        def define(name: str | tuple[int, str] | tuple[str, str], vertex: int | tuple[str, str]) -> None:
            if name in found:
                return
            found[name] = vertex
            for _, source in sorted(waiting.pop(name, []), reverse=True):
                arcs.setdefault(source, []).append((next(clock), vertex))

        for f in self.files:
            if f.kind == 'unit' and f.unit[0] in regular:
                define(('unit', f.unit[0]), ('unit', f.unit[0]))
            for m in f.modules:
                for kind, name in m.blockrefs:
                    if kind == 'ent':
                        define(m.key(name), id(m))
                    elif kind == 'com':
                        if name in regular:
                            add_arc(id(m), ('unit', name))
                    elif m.key(name) in self.symbols:
                        add_arc(id(m), m.key(name))

        order, seen = [], {id(self.main)}
        stack = [iter(sorted(arcs.get(id(self.main), []), reverse=True))]
        while stack:
            for _, v in stack[-1]:
                if v not in seen:
                    seen.add(v)
                    if isinstance(v, tuple):
                        order.append(v[1])
                    stack.append(iter(sorted(arcs.get(v, []), reverse=True)))
                    break
            else:
                stack.pop()
        self.unit_base, base = {}, -self.main_size
        for unit in order:
            self.unit_base[unit] = base
            base -= sizes[unit]
        self.data_size = sum(sizes[u] for u in order)

    # ---- jump table ----
    def build_jump_table(self) -> None:
        """descriptor 0 is the main program's entry point, then one per
        name that is referenced from another segment: grouped by segment (in
        segment order), alphabetically by LinkName, where a name sorts after
        the longer names it is a prefix of (LINETO before LINE, checked
        against QDSAMPLE).  Names of the same address get a descriptor each
        (an assembler module with several .DEF names at 0: LisaTerminal)"""
        cross = {}
        for m in self.modules:
            for ln, un, offs in m.shortrefs + m.longrefs:
                k = m.key(ln)
                if k in self.symbols:
                    target, tm = self.address(m, ln)
                    if tm.seg is not m.seg:
                        cross.setdefault(k, (target, tm.seg, self.sort_name(tm, ln)))
        order = {s.mmu: i for i, s in enumerate(self.segments)}
        self.entry = self.main.seg.code_addr(self.main.offset + self.main.start[0])
        keys = sorted(cross, key=lambda k: (order[cross[k][1].mmu], name_key(cross[k][2])))
        self.descriptors = [self.entry] + [cross[k][0] for k in keys]
        self.desc_names = [self.main.name] + [cross[k][2] for k in keys]
        self.desc_index = {k: i + 1 for i, k in enumerate(keys)}
        # the jump table lies at JTLaddr: $F80000 + JTSegDelta + 4 * maxunit
        # (the data pointer table, one long per intrinsic unit number), and
        # A5 = $F80000 - StkSegDelta
        self.jtl_addr = 0xF80000 + JT_SEG_DELTA + 4 * self.max_unit
        self.a5 = a5 = 0xF80000 - STK_SEG_DELTA
        self.desc_base = self.jtl_addr - a5 + 2 + 12 * len(self.segments) + 2

    def jt_offset(self, key: tuple[int, str] | str) -> int:
        """the A5 offset of the jump table descriptor of a name (its symbol key)"""
        return self.desc_base + 6 * self.desc_index[key]

    # ---- intrinsic units and segments used (from the libraries given) ----
    def closure(self) -> None:
        """the UnitTable and SegmentTable: every unit and segment of the
        intrinsic libraries in the input list ("inclusion of a file in the
        Linker input list is taken as a reference to all the segments in
        the file")"""
        units, isegs = {}, {}
        for f in self.files:
            for u in f.lib_units:
                units.setdefault(u[0], u)
            for sg in f.lib_segments:
                isegs.setdefault(sg[0], sg)
        self.units = sorted(units.values(), key=lambda u: u[1])        # by unit number
        self.isegs = sorted(isegs.values(), key=lambda sg: sg[1])      # by MMU number
        self.max_unit = max([u[1] for u in self.units], default=0)
        self.intrinsic_units = {name: num for name, num, typ in self.units}

    # ---- 3. references ----
    def patch(self, jt_offset: Callable[[tuple[int, str] | str], int]) -> None:
        """patch all references; jt_offset(key) gives the A5 offset of the
        jump table descriptor of a name in another segment"""
        for m in self.modules:
            img = m.seg.image
            here = m.offset
            for ln, un, offs in m.shortrefs:
                for r in offs:
                    p = here + r                    # the 16-bit field
                    op = be16(img, p - 2)
                    if ln in self.intrinsic and m.key(ln) not in self.symbols:
                        self.patch_iu(img, p, op, self.intrinsic[ln], m, ln)
                        continue
                    target, tm = self.address(m, ln)
                    if tm.seg is m.seg:
                        disp = target - m.seg.code_addr(p)
                        struct.pack_into('>h', img, p, disp)
                        if pc_relative(op) != op:       # abs.W/abs.L -> d(PC)
                            struct.pack_into('>H', img, p - 2, pc_relative(op))
                    else:
                        struct.pack_into('>H', img, p - 2, self.to_a5(op, m, ln))
                        struct.pack_into('>h', img, p, jt_offset(m.key(ln)))
            for unit, offs in m.commonrefs:
                if unit in self.intrinsic_units:
                    # an intrinsic unit's globals: the A5 offset of its entry
                    # in the data pointer table, which ends at JTLaddr
                    d = self.jtl_addr - self.a5 - 4 * (self.max_unit + 1 - self.intrinsic_units[unit])
                    for r in offs:
                        p = here + r
                        struct.pack_into('>H', img, p, (be16(img, p) + d) & 0xFFFF)
                    continue
                if unit not in self.unit_base:
                    raise LinkError('%s: globals of unknown unit %s' % (m.name, unit))
                for r in offs:
                    p = here + r
                    v = (be16(img, p) + self.unit_base[unit]) & 0xFFFF
                    struct.pack_into('>H', img, p, v)
            if m.longrefs or m.relocs:
                raise LinkError('%s: External/Relocation blocks are not supported yet' % m.name)

    @staticmethod
    def to_a5(op: int, m: Module, ln: str) -> int:
        """the d(A5) form of a PC-relative (or absolute) instruction word"""
        op = pc_relative(op)
        if op in (0x4EBA, 0x4EB9, 0x4EB8):
            return 0x4EAD                   # JSR d(A5)
        if op in (0x4EFA, 0x4EF9, 0x4EF8):
            return 0x4EED                   # JMP d(A5)
        if op == 0x487A:
            return 0x486D                   # PEA d(A5)
        if (op & 0xF1FF) == 0x41FA:
            return op - 0x41FA + 0x41ED     # LEA d(A5),An
        raise LinkError('%s: cannot make $%04X a jump table reference (%s)' % (m.name, op, ln))

    @staticmethod
    def patch_iu(img: bytearray, p: int, op: int, addr: int, m: Module, ln: str) -> None:
        """the IU trap form of an instruction, with the 24-bit address, as
        the Linker writes it (Linker.Obj, Phase2): the opcode without its
        address mode bits selects the trap, written as a long: JSR $A0000000
        + address, JMP $A4000000 + address, PEA $AC000000 + address, LEA An
        $A8000000 + address/2 + An * $800000; the word that was in the
        address field (normally 0) is added.  The IU trap handler (the
        CodeBlock of INTRINSIC.LIB) decodes these forms."""
        word = sbe16(img, p)
        op = pc_relative(op) & 0xFFC0
        if op == 0x4E80:
            v = 0xA0000000 + addr + word            # IUJSR
        elif op == 0x4EC0:
            v = 0xA4000000 + addr + word            # IUJMP
        elif op == 0x4840:
            v = 0xAC000000 + addr + word            # IUPEA
        elif (op & 0xF1C0) == 0x41C0 and (op >> 9) & 7 != 7:
            v = 0xA8000000 + (addr >> 1) + word + ((op >> 9) & 7) * 0x800000    # IULEA An
        else:
            raise LinkError('%s: cannot make $%04X an IU trap (%s)' % (m.name, op, ln))
        struct.pack_into('>L', img, p - 2, v & 0xFFFFFFFF)


# ---- 4. output ----
# Executable header values as the Workshop linker writes them (its defaults)
DYN_STACK, MAX_STACK, MIN_HEAP, MAX_HEAP = 10240, 131072, 4096, 131072


def write_program(lk: Linker) -> bytes:
    """serialize a linked main program into a 512-byte-padded Lisa executable (.OBJ)"""
    out = bytearray()
    out += block(VERSIONCTRL, lk.profile['version_ctrl'])
    if lk.profile['os_data']:
        out += block(OSDATA, bytes(lk.profile['os_data']))
    if lk.units:
        body = struct.pack('>HH', len(lk.units), lk.max_unit)
        for name, num, typ in lk.units:
            body += pack_name8(name) + struct.pack('>HH', num, typ)
        out += block(UNITTABLE, body)
    segtab = b''
    if lk.isegs:
        body = struct.pack('>H', len(lk.isegs))
        for name, num, v1, v2 in lk.isegs:
            body += pack_name8(name) + struct.pack('>H', num) + v1 + v2
        segtab = block(SEGMENTTABLE, body)
    # the code records, to know their file addresses
    jt_size = 2 + 12 * len(lk.segments) + 2 + 6 * len(lk.descriptors) + len(lk.profile['jt_old_stuff'])
    pos = len(out) + 4 + 40 + jt_size + len(segtab)
    recs, segfile = b'', []
    for s in lk.segments:
        if not s.modules:
            segfile.append(0)                 # an empty segment: no code in the file
            continue
        r = block(MODULENAME, pack_name8('MainProg') + pack_name8(s.name) + struct.pack('>L', 0))
        if s is lk.main.seg:
            # as in the main program's module (the entry point is jump table descriptor 0)
            r += block(STARTADDRESS, struct.pack('>LL', lk.main.start[0], lk.main_size))
        segfile.append(pos + len(r))
        cb = block(CODEBLOCK, struct.pack('>L', s.base) + bytes(s.image))
        r += cb + block(ENDBLOCK, struct.pack('>L', len(s.image)))
        recs += r
        pos += len(r)
    hdr = struct.pack('>L9L', lk.jtl_addr, jt_size, lk.data_size, lk.main_size, JT_SEG_DELTA,
                      STK_SEG_DELTA, DYN_STACK, MAX_STACK, MIN_HEAP, MAX_HEAP)
    jt = struct.pack('>H', len(lk.segments))
    for s, fa in zip(lk.segments, segfile):
        jt += struct.pack('>LHHL', fa, 0, len(s.image) + 8, s.base)      # not packed
    jt += struct.pack('>H', len(lk.descriptors))
    for a in lk.descriptors:
        jt += struct.pack('>HL', 0x4EF9, a)                              # JMP.L
    jt += lk.profile['jt_old_stuff']
    out += block(EXECUTABLE, hdr + jt)
    out += segtab
    out += recs
    out += block(EOFMARK, b'')
    return pad512(bytes(out))


# ---- file names, as the Workshop's Linker takes them ----
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def boot_dir() -> str:
    """the folder that plays the boot volume: $LISA_BOOT, else
    libs/workshop3.0 (as for the compiler, pascal/lisalib.py boot_dir)"""
    return os.environ.get('LISA_BOOT') or os.path.join(REPO, 'libs', 'workshop3.0')


def find_ci(path: str) -> str | None:
    """path, with each component matched ignoring case; None if not found"""
    parts = path.split('/')
    cur = '/' if path.startswith('/') else '.'
    for part in parts:
        if part in ('', '.'):
            continue
        cand = os.path.join(cur, part)
        if not os.path.exists(cand):
            try:
                match = [e for e in os.listdir(cur) if e.lower() == part.lower()]
            except OSError:
                return None
            if not match:
                return None
            cand = os.path.join(cur, match[0])
        cur = cand
    return os.path.normpath(cur)


def host_name(name: str, ext: str = '.OBJ') -> str:
    """the host file of a Lisa file name: a volume prefix ("*X", "-vol-X")
    is dropped; the name is tried as given and with ext, ignoring case,
    in the current directory and then in the boot folder"""
    n = name.strip()
    if n.startswith('*'):
        n = n[1:]
    elif n.startswith('-') and '-' in n[1:]:
        n = n[n.index('-', 1) + 1:]
    cands = [n] if n.lower().endswith(ext.lower()) else [n, n + ext]
    for d in ('.', boot_dir()):
        for c in cands:
            h = find_ci(c if os.path.isabs(c) or d == '.' else os.path.join(d, c))
            if h and os.path.isfile(h):
                return h
    raise LinkError('file not found: %s' % name)


def input_files(names: Iterable[str]) -> list[str]:
    """the input list: "<file" reads a command file (.TEXT), one name per
    line, as in QD/M/BOXES.TEXT's "<QD/QDSTUFF"; blank lines are skipped"""
    out = []
    for name in names:
        if name.startswith('<'):
            text = open(host_name(name[1:], '.TEXT'), encoding='latin1').read()
            out += input_files([l.strip() for l in text.splitlines() if l.strip()])
        else:
            out.append(host_name(name))
    return out


def where_defined(names: Collection[str], used: Collection[str]) -> dict[str, list[str]]:
    """{library file in the boot folder: names it defines} for names, to
    say which library is missing from the input list"""
    hints = {}
    try:
        files = sorted(os.listdir(boot_dir()))
    except OSError:
        return hints
    for f in files:
        p = os.path.join(boot_dir(), f)
        if not f.lower().endswith('.obj') or os.path.abspath(p) in map(os.path.abspath, used):
            continue
        try:
            lib = InputFile(p, -1)
        except Exception:
            continue
        found = [n for n in names if n in lib.lib_entries]
        if found:
            hints[f] = found
    return hints


def guess_workshop(paths: Iterable[str]) -> str:
    """the Workshop version of the libraries: the VersionCtrl SysNum field
    is 1 in the 1.0 and 2.0 libraries, 0 in the 3.0 ones"""
    for p in paths:
        d = open(p, 'rb').read(8)
        if d[:1] == bytes([VERSIONCTRL]):
            return '2.0' if be32(d, 4) == 0x10000 else '3.0'
    return '3.0'


def link(inputs: Iterable[str], workshop: str = '3.0', physical: bool = False, os_data: bool = True, domain0: bool = False) -> tuple[Linker, bytes]:
    """os_data False: the Linker's -O (no OSData block); domain0: +F
    (system code that runs in domain 0, which cannot use MMUs 1-16: the
    segments start at MMU 17)"""
    lk = Linker(inputs, workshop)
    lk.profile = dict(lk.profile)
    if not os_data:
        lk.profile['os_data'] = 0
    if domain0:
        lk.profile['first_mmu'] = max(lk.profile['first_mmu'], 17)
    lk.select()
    lk.place()
    if physical:
        if len(lk.segments) != 1:
            raise LinkError('+P (physical link): only a program of one segment is supported, '
                            'not %d segments' % len(lk.segments))
        lk.segments[0].base = 0             # the code is loaded at address 0
    lk.closure()
    lk.layout_globals()
    lk.build_jump_table()
    if physical and len(lk.descriptors) > 1:
        raise LinkError('+P (physical link): calls between segments are not supported')
    lk.patch(lk.jt_offset)
    return lk, (write_physical(lk) if physical else write_program(lk))


# PhysicalExec (+P): the values of the Workshop 3.0 Linker (Linker.Obj, segment
# Phase2: LINKMAIN and the routine that writes the Executable block)
PHYS_JTL_ADDR = 0xFFFFAB00                  # a constant there
PHYS_JT_SEG_DELTA, PHYS_STK_SEG_DELTA = 0x100, 0x2000   # as in LIBHW's SYSTEM.LLD
PHYS_TRAP_STUB = struct.pack('>LHHLH', 0x487AFFFE, 0x4267, 0x4E4E, 0x3F3C0004, 0x4E4E)


def write_physical(lk: Linker) -> bytes:
    """a program linked with +P (physical link: it runs before the MMU is
    set up, e.g. LIBHW's SYSTEM.LLD): no VersionCtrl or OSData, a
    PhysicalExec block ($97) instead of the Executable block, and the code
    at address 0.  The PhysicalExec block, as the Workshop 3.0 Linker writes
    it (it is read into memory at JTLaddr = $FFFFAB00):
      * JTLaddr, JTSize (the size of what follows), DataSize, MainSize,
        JTSegDelta ($100), StkSegDelta ($2000);
      * the number of segments, then 32 bytes per segment: the address of
        its jump table entry, the file address of its ModuleName block, its
        code size, 20 bytes 0;
      * the end of the jump table (JTLaddr + 16 + 32 x segments), then the
        entry: the main program's offset, NOP, JSR to the stub below;
      * 3 longs 0, -1, JTLaddr, and the stub PEA *; CLR.W -(SP); TRAP #14;
        MOVE.W #4,-(SP); TRAP #14.
    Checked against SYSTEM.LLD (one segment)."""
    out = bytearray()
    if lk.units:
        body = struct.pack('>HH', len(lk.units), lk.max_unit)
        for name, num, typ in lk.units:
            body += pack_name8(name) + struct.pack('>HH', num, typ)
        out += block(UNITTABLE, body)
    segtab = b''
    if lk.isegs:
        body = struct.pack('>H', len(lk.isegs))
        for name, num, v1, v2 in lk.isegs:
            body += pack_name8(name) + struct.pack('>H', num) + v1 + v2
        segtab = block(SEGMENTTABLE, body)
    s = lk.segments[0]
    jtl = PHYS_JTL_ADDR
    table_size = 16 + 32 * len(lk.segments)
    jt_end = jtl + table_size
    entry_addr = jtl + 2 + 32 * len(lk.segments) + 4      # the entry, after the end address
    stub_addr = jt_end + 20
    modpos = len(out) + 4 + 24 + table_size + 34 + len(segtab)
    table = struct.pack('>H', len(lk.segments))
    table += struct.pack('>LLL', entry_addr, modpos, len(s.image)) + bytes(20)
    table += struct.pack('>LLHHh', jt_end, lk.main.offset + lk.main.start[0],
                         0x4E71, 0x4EBA, stub_addr - (entry_addr + 8))   # NOP; JSR d(PC)
    tail = struct.pack('>5L', 0, 0, 0, 0xFFFFFFFF, jtl) + PHYS_TRAP_STUB
    hdr = struct.pack('>6L', jtl, table_size + len(tail), lk.data_size, lk.main_size,
                      PHYS_JT_SEG_DELTA, PHYS_STK_SEG_DELTA)
    out += block(PHYSICALEXEC, hdr + table + tail)
    out += segtab
    assert len(out) == modpos
    out += block(MODULENAME, pack_name8('MainProg') + pack_name8(s.name) + struct.pack('>L', 0))
    out += block(STARTADDRESS, struct.pack('>LL', lk.main.start[0], lk.main_size))
    out += block(CODEBLOCK, struct.pack('>L', 0) + bytes(s.image))
    out += block(ENDBLOCK, struct.pack('>L', len(s.image)))
    out += block(EOFMARK, b'')
    return pad512(bytes(out))


def write_map(lk: Linker, path: str) -> None:
    """a link map: segments, modules (offset in the segment, size, file),
    unit globals and the jump table"""
    with open(path, 'w') as f:
        for s in lk.segments:
            f.write("segment '%s' MMU %d $%06X %d bytes\n" % (s.name, s.mmu, s.base, len(s.image)))
            for m in s.modules:
                f.write('  module %-8s $%06X %6d  %s\n' % (m.name, m.offset, len(m.code), os.path.basename(m.file.path)))
        f.write('main program globals %d bytes\n' % lk.main_size)
        for unit, base in sorted(lk.unit_base.items(), key=lambda x: -x[1]):
            f.write('  unit globals %-8s A5%+d\n' % (unit, base))
        for i, a in enumerate(lk.descriptors):
            f.write('  descriptor %3d A5+$%04X $%06X %s\n' % (i, lk.desc_base + 6 * i, a, lk.desc_names[i]))


def main() -> None:
    """CLI entry point for linking Lisa programs (-P, -p) or intrinsic libraries (-i)"""
    ap = argparse.ArgumentParser(
        description='link Lisa Pascal object files as the Workshop Linker does',
        epilog='Input names are Lisa file names: .OBJ is added when needed, case is '
               'ignored, and a name not found in the current directory is looked up in '
               'the boot folder ($LISA_BOOT, else libs/workshop3.0).  "<FILE" reads more '
               'names from the text file FILE[.TEXT].')
    ap.add_argument('inputs', nargs='+', help='object files and libraries, in link order')
    ap.add_argument('-o', '--output', required=True, help='the linked program (.OBJ is added)')
    ap.add_argument('-m', '--map', help='write a link map')
    ap.add_argument('-p', '--pack', action='store_true',
                    help='pack the code segments, as PACKSEG does, with the boot folder\'s SYSTEM.UNPACK')
    ap.add_argument('--table', help='the pack table for -p (default: SYSTEM.UNPACK in the boot folder)')
    ap.add_argument('-i', '--intrinsic', action='store_true',
                    help='intrinsic link (Lisa option +I): link intrinsic units into an intrinsic '
                         'library, with their interfaces (lisaintrinsic.py)')
    ap.add_argument('-s', '--seg-map', action='append', default=[], metavar='OLD=NEW',
                    help='put the modules of segment OLD into segment NEW (Lisa option +M OLD NEW)')
    ap.add_argument('--iulib', help='the intrinsic unit directory for -i, which gives the unit and '
                                    'segment numbers (default: INTRINSIC.LIB, in the current '
                                    'directory or the boot folder)')
    ap.add_argument('-P', '--physical', action='store_true',
                    help='physical link (Lisa option +P): a program that runs before the MMU '
                         'is set up, with its code at address 0 (one segment only)')
    ap.add_argument('--no-osdata', action='store_true',
                    help='no OSData block (Lisa option -O; +O, the default, emits it for main programs)')
    ap.add_argument('--domain0', action='store_true',
                    help='system code that runs in domain 0 and cannot use MMUs 1-16 (Lisa option +F)')
    ap.add_argument('-w', '--workshop', choices=sorted(PROFILES),
                    help='write the program as this Workshop version\'s Linker does '
                         '(default: the version of the libraries)')
    args = ap.parse_args()
    # as on the Lisa, .OBJ is added unless the name ends in .OBJ
    # ("LIBPR/System.PR_IJP" is written as "LIBPR/System.PR_IJP.OBJ")
    out = args.output if args.output.upper().endswith('.OBJ') else args.output + '.OBJ'
    out = find_ci(out) or out          # replace an existing file of that name, whatever its case
    import lisaintrinsic
    # run as a script, this module is __main__: lisaintrinsic has the
    # LinkError of the module lisalinker
    errors = (LinkError, ValueError, lisaintrinsic.LinkError)
    seg_map = {}
    for sm in args.seg_map:
        old, sep, new = sm.partition('=')
        if not sep or not old or not new:
            ap.error('-s needs OLD=NEW, not %r' % sm)
        seg_map[old] = new
    if seg_map and not args.intrinsic:
        ap.error('-s is only supported with -i')
    try:
        inputs = input_files(args.inputs)
        if args.intrinsic:
            if args.pack or args.table or args.physical:
                raise LinkError('-p and -P are not supported with -i')
            lk, data = lisaintrinsic.link_intrinsic(inputs, args.iulib or host_name('INTRINSIC.LIB', ''),
                                                    seg_map, args.workshop or guess_workshop(inputs))
            open(out, 'wb').write(data)
            if args.map:
                lisaintrinsic.write_map(lk, args.map)
            for s in lk.segments:
                print('segment %-10s MMU %3d  $%06X  %5d bytes, %3d modules, %3d entry points' % (
                    "'%s'" % s.name, s.mmu, s.base, len(s.image), len(s.modules), len(s.vector)))
            print('%s: %d bytes, intrinsic library' % (out, len(data)))
            return
        lk, data = link(inputs, args.workshop or guess_workshop(inputs), args.physical,
                        not args.no_osdata, args.domain0)
        for w in lk.warnings:
            print(w, file=sys.stderr)
        if args.pack or args.table:
            import lisapack
            table = args.table or host_name('SYSTEM.UNPACK', '')
            data = lisapack.pack_program(data, lisapack.read_table(table))
    except errors as e:
        sys.exit('lisalinker: %s' % e)
    open(out, 'wb').write(data)
    if args.map:
        write_map(lk, args.map)
    for s in lk.segments:
        print('segment %-10s MMU %3d  $%06X  %5d bytes, %3d modules' % (
            "'%s'" % s.name, s.mmu, s.base, len(s.image), len(s.modules)))
    print('%d jump table descriptors, main globals %d, unit globals %d' % (
        len(lk.descriptors), lk.main_size, lk.data_size))
    print('%s: %d bytes%s' % (out, len(data), ', packed' if args.pack or args.table else ''))


if __name__ == '__main__':
    main()
