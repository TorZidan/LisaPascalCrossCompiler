"""Intrinsic link: link intrinsic units into an intrinsic library file, as
the Workshop Linker does with its +I option (e.g. IOSPASLIB from the units
and assembler modules of the Office System's LIBPL folder).

The rules were derived from the format description in the Lisa Development
System Internals Documentation (Feb 1984, pp.102-141) and checked byte for
byte against the IOSPASLIB.OBJ that the Lisa built from those sources
(tests/run_lisa_sources_build_tests.sh LIBPL):

  1. Every module of the input files is linked (there is no main program to
     start a selection from).  Segment names can be renamed (+M OLD NEW).
  2. Segments are placed in the order their names first appear; each one
     gets the MMU number INTRINSIC.LIB gives it (IUManager defines them
     before the link).  The CodeBlock is at MMU * 128K, the code 8 bytes
     after it, as in a main program.
  3. Each segment begins with a jump vector: one JMP d(PC) for every entry
     point whose LinkName does not start with '$', sorted by LinkName (with
     '%' after the letters, and a name after the longer names it is a
     prefix of).  The modules follow, in input order.
  4. References: within a segment, d(PC) to the routine itself; to another
     segment, an IU trap to the routine's vector entry (to the routine itself
     for a '$' name, which has none).  CommonReloc: the A5 offset of the
     unit's data pointer, $1FC + 4 * unit number.
  5. Output: VersionCtrl, SegLocation (INTRINSIC.LIB's entries for this
     file, with the file locations and sizes of the code), InterfLoc,
     UnitTable, SegmentTable, the UnitBlocks with the compressed interfaces
     (units in reverse input order), then for each segment ModuleName
     'IntrinSg', its EntryPoints (the vector entries; modules in order,
     each module's entry points in reverse), CodeBlock, EndBlock; EOFMark.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
import struct

from lisaobj import (
    CODEBLOCK, ENDBLOCK, ENTRYPOINT, EOFMARK, INTERFLOC, MODULENAME,
    SEGLOCATION, SEGMENTTABLE, UNITBLOCK, UNITLOCATION, UNITTABLE, VERSIONCTRL,
    be16, block, name8, pack_name8, pad512, read_blocks,
)
from lisalinker import InputFile, Linker, LinkError, SEG_SIZE, name_key, pc_relative

# A5 offset of the data pointer of intrinsic unit n (the same in every
# program: the data pointer table ends at JTLaddr)
DATA_POINTER = 0x1FC


def read_iulib(path: str) -> tuple[dict[str, tuple[int, int, int]], dict[str, tuple[int, int, int, int]]]:
    """the unit and segment numbers from an intrinsic unit directory
    (INTRINSIC.LIB): {unit: (number, file, type)}, {segment: entry}"""
    units, segs = {}, {}
    for b in read_blocks(open(path, 'rb').read()):
        d = b.body
        if b.type == UNITLOCATION:
            for i in range(be16(d)):
                q = 2 + 16 * i
                num, fnum, typ, size = struct.unpack_from('>HBBL', d, q + 8)
                units[name8(d, q)] = (num, fnum, typ)
        elif b.type == SEGLOCATION:
            for i in range(be16(d)):
                q = 2 + 28 * i
                num, v1, v2, fnum = struct.unpack_from('>HLLH', d, q + 8)
                segs[name8(d, q)] = (num, v1, v2, fnum)
    if not units and not segs:
        raise LinkError('%s is not an intrinsic unit directory' % path)
    return units, segs


# ---- interfaces ----
def unit_text(f: InputFile) -> bytes:
    """the interface text of a unit file: its text pages without the NULs
    that fill each page"""
    addr, size = f.unit_text
    t = f.data[addr:addr + size]
    out = bytearray()
    for p in range(0, len(t), 1024):
        out += t[p:p + 1024].rstrip(b'\0')
    return bytes(out)


def compress_interface(t: bytes) -> bytes:
    """the interface as the Linker stores it in a library: comments removed
    (but not compiler options), blanks collapsed, no indentation or blank
    lines; strings and options kept as they are.  A comment does not stand
    for a blank ("integer{1..512};" becomes "integer;").  The high bit of
    the first byte (the compiler's "unit needs an init call" flag) moves to
    the first byte written."""
    flag = t[:1] and t[0] & 0x80
    s = bytearray(t)
    if flag:
        s[0] &= 0x7F
    # DLE indentation
    t, s, i = bytes(s), bytearray(), 0
    while i < len(t):
        if t[i] == 0x10 and i + 1 < len(t):
            s += b' ' * max(t[i + 1] - 32, 0)
            i += 2
        else:
            s.append(t[i])
            i += 1
    t, out, i, n, blank = bytes(s), bytearray(), 0, len(s), False

    def copy(j: int) -> int:
        nonlocal blank
        if blank and out and out[-1] != 13:
            out.append(32)
        blank = False
        out.extend(t[i:j])
        return j

    while i < n:
        c = t[i]
        if c == 0x7B or t.startswith(b'(*', i):            # { or (*
            close = b'}' if c == 0x7B else b'*)'
            j = t.find(close, i + 1 if c == 0x7B else i + 2)
            j = n if j < 0 else j + len(close)
            option = t.startswith(b'$', i + (1 if c == 0x7B else 2))
            i = copy(j) if option else j
        elif c == 0x27:                                    # 'string'
            j = t.find(b"'", i + 1)
            i = copy(n if j < 0 else j + 1)
        elif c == 32:
            blank, i = True, i + 1
        elif c == 13:
            blank, i = False, i + 1
            if out and out[-1] != 13:
                out.append(13)
        else:
            i = copy(i + 1)
    if out and out[-1] != 13:
        out.append(13)
    if flag and out:
        out[0] |= 0x80
    return bytes(out)


def lay_out_interface(text: bytes, base: int, block_at: int) -> bytes:
    """text pages: 1024 bytes, the first one beginning at the 512-byte file
    block that holds the UnitBlock (block_at: its file address; base: that of
    the text, which can be in the next block: SYS2LIB's RECOVERY); a line
    that does not leave at least 2 bytes free in the page starts the next
    one, the rest is NULs.  The text ends with 2 NULs and one more if its
    length is odd."""
    out = bytearray()
    page_end = block_at - block_at % 512 + 1024
    for line in text.split(b'\r')[:-1]:
        line += b'\r'
        while base + len(out) + len(line) > page_end - 2:
            out += bytes(max(page_end - base - len(out), 0))
            page_end += 1024
        out += line
    return bytes(out) + bytes(2 + len(out) % 2)


def vector_key(name: str) -> str:
    """sort key for an intrinsic segment's jump vector entries"""
    return name_key(name)


class IntrinsicSegment:
    """an intrinsic library segment with its MMU number, jump vector, and module code"""
    def __init__(self, name: str, num: int) -> None:
        self.name = name
        self.mmu = num
        self.base = num * SEG_SIZE
        self.modules = []
        self.image = bytearray()

    def code_addr(self, offset: int) -> int:
        """logical 24-bit address of byte offset in this segment (8 bytes past the CodeBlock header)"""
        return self.base + 8 + offset


class IntrinsicLinker(Linker):
    """linker for intrinsic libraries (Workshop Linker +I option)"""
    def __init__(self, paths: Iterable[str], iulib: str, seg_map: Mapping[str, str] | None = None, workshop: str = '3.0') -> None:
        super().__init__(paths, workshop)
        # segment names are 8 characters, and case does not matter
        # ("+m PrBtnInit PrInit" renames segment PrBtnIni; "+m fp68k fpsane")
        self.seg_map = {old[:8].upper(): new[:8] for old, new in (seg_map or {}).items()}
        self.iu_units, self.iu_segs = read_iulib(iulib)
        # the library's file number in INTRINSIC.LIB: that of its units.
        # Segment names that differ only in case (SYS2LIB's openclos and
        # LCORBGLIB's OpenClos) are told apart by it
        files = [self.iu_units[f.unit[0]][1] for f in self.files
                 if f.kind == 'unit' and f.unit[0] in self.iu_units]
        lib_file = files[0] if files else None
        self.iu_seg_names = {}
        for n, entry in self.iu_segs.items():
            if n.upper() not in self.iu_seg_names or entry[3] == lib_file:
                self.iu_seg_names[n.upper()] = n

    def select(self) -> None:
        """include all modules from every input file and check for undefined symbols"""
        self.modules = [m for f in self.files for m in f.modules]
        if not self.modules:
            raise LinkError('no modules to link')
        undefined = set()
        for m in self.modules:
            for ln, un, offs in m.shortrefs + m.longrefs:
                if m.key(ln) not in self.symbols and ln not in self.intrinsic:
                    undefined.add(ln)
        if undefined:
            raise LinkError('undefined: ' + ' '.join(sorted(undefined)))

    def place(self) -> None:
        """assign segments from INTRINSIC.LIB, build each segment's jump vector, and place module code"""
        # the target segments of +M come first, in the order of the options
        # (PRLIB: "+m PrBtnInit PrInit" puts PrInit before Pr, which the
        # first module uses); then the others in the order they first appear
        used = {self.seg_map.get(m.segname.upper(), m.segname).upper() for m in self.modules}
        names = []
        for new in self.seg_map.values():
            n = self.iu_seg_names.get(new.upper())
            if n and n.upper() in used and n not in names:
                names.append(n)
        for m in self.modules:
            seg = self.seg_map.get(m.segname.upper(), m.segname)
            if seg.upper() not in self.iu_seg_names:
                raise LinkError("segment '%s' is not in INTRINSIC.LIB (IUManager defines a library's "
                                'segments before it is linked)' % seg)
            m.segname = self.iu_seg_names[seg.upper()]       # as INTRINSIC.LIB spells it
            if m.segname not in names:
                names.append(m.segname)
        self.segments, byname = [], {}
        for n in names:
            byname[n] = IntrinsicSegment(n, self.iu_segs[n][0])
            self.segments.append(byname[n])
        for m in self.modules:
            byname[m.segname].modules.append(m)
        # the jump vector, then the modules
        for s in self.segments:
            exported = [(ln, un, m, loc) for m in s.modules for ln, un, loc in m.entries
                        if not ln.startswith('$')]
            s.vector = sorted(exported, key=lambda e: vector_key(e[0]))
            s.image = bytearray(4 * len(s.vector))
            for m in s.modules:
                m.seg, m.offset = s, len(s.image)
                s.image += m.code
            s.vector_addr = {}
            for i, (ln, un, m, loc) in enumerate(s.vector):
                disp = m.offset + loc - (4 * i + 2)
                struct.pack_into('>Hh', s.image, 4 * i, 0x4EFA, disp)       # JMP d(PC)
                s.vector_addr.setdefault(ln, s.code_addr(4 * i))
            # entry points as written: modules in order, each one's in reverse
            s.entries = [(ln, un, s.vector_addr[ln]) for m in s.modules
                         for ln, un, loc in reversed(m.entries) if not ln.startswith('$')]

    def units_of_library(self) -> list[tuple[InputFile, str, int, int]]:
        """the units in this library: (file, name, number, type)"""
        out = []
        for f in self.files:
            if f.kind == 'unit':
                name = f.unit[0]
                if name not in self.iu_units:
                    raise LinkError("unit '%s' is not in INTRINSIC.LIB" % name)
                out.append((f, name, self.iu_units[name][0], f.unit[2]))
        return out

    def patch(self) -> None:
        """resolve intra-segment PC-relative calls, cross-segment IU traps, and intrinsic unit CommonReloc offsets"""
        for m in self.modules:
            img, here = m.seg.image, m.offset
            for ln, un, offs in m.shortrefs:
                for r in offs:
                    p = here + r
                    op = be16(img, p - 2)
                    if m.key(ln) not in self.symbols:
                        self.patch_iu(img, p, op, self.intrinsic[ln], m, ln)
                        continue
                    tm, loc = self.symbols[m.key(ln)]
                    if tm.seg is m.seg:
                        struct.pack_into('>h', img, p, m.seg.code_addr(tm.offset + loc) - m.seg.code_addr(p))
                        if pc_relative(op) != op:       # abs.W/abs.L -> d(PC)
                            struct.pack_into('>H', img, p - 2, pc_relative(op))
                    else:
                        target = tm.seg.vector_addr.get(ln) or tm.seg.code_addr(tm.offset + loc)
                        self.patch_iu(img, p, op, target, m, ln)
            for unit, offs in m.commonrefs:
                if unit in self.iu_units:
                    d = DATA_POINTER + 4 * self.iu_units[unit][0]
                elif unit in self.intrinsic_units:
                    d = DATA_POINTER + 4 * self.intrinsic_units[unit]
                else:
                    raise LinkError('%s: globals of unit %s, which is not an intrinsic unit' % (m.name, unit))
                for r in offs:
                    p = here + r
                    struct.pack_into('>H', img, p, (be16(img, p) + d) & 0xFFFF)
            if m.longrefs or m.relocs:
                raise LinkError('%s: External/Relocation blocks are not supported yet' % m.name)


def write_library(lk: IntrinsicLinker) -> bytes:
    """serialize the linked IntrinsicLinker state into a 512-byte-padded Lisa intrinsic library (.OBJ)"""
    units = lk.units_of_library()
    # UnitTable and SegmentTable: this library's, and those of the
    # libraries in the input list
    table_units = {name: (name, num, typ) for f, name, num, typ in units}
    for name, num, typ in lk.units:
        table_units.setdefault(name, (name, num, typ))
    table_units = sorted(table_units.values(), key=lambda u: u[1])
    table_segs = {s.name: (s.name, s.mmu, bytes(4), bytes(4)) for s in lk.segments}
    for sg in lk.isegs:
        table_segs.setdefault(sg[0], sg)
    table_segs = sorted(table_segs.values(), key=lambda sg: sg[1])
    loc_segs = sorted(lk.segments, key=lambda s: s.mmu)

    out = bytearray(block(VERSIONCTRL, lk.profile['version_ctrl']))
    segloc_at = len(out)
    out += block(SEGLOCATION, bytes(2 + 28 * len(loc_segs)))       # filled in below
    interf_at = len(out)
    out += block(INTERFLOC, bytes(2 + 12 * len(units)))
    body = struct.pack('>HH', len(table_units), max([u[1] for u in table_units], default=0))
    for name, num, typ in table_units:
        body += pack_name8(name) + struct.pack('>HH', num, typ)
    out += block(UNITTABLE, body)
    body = struct.pack('>H', len(table_segs))
    for name, num, v1, v2 in table_segs:
        body += pack_name8(name) + struct.pack('>H', num) + v1 + v2
    out += block(SEGMENTTABLE, body)
    interf = struct.pack('>H', 0)
    for f, name, num, typ in reversed(units):
        interf += pack_name8(name) + struct.pack('>L', len(out))
        head = pack_name8(name) + struct.pack('>LLLLH', 0, 0, 0, f.unit[1], typ)
        text = lay_out_interface(compress_interface(unit_text(f)), len(out) + 4 + len(head), len(out))
        out += block(UNITBLOCK, head + text)
    out[interf_at + 4:interf_at + 4 + len(interf)] = interf
    code_at = {}
    for s in lk.segments:
        out += block(MODULENAME, pack_name8('IntrinSg') + pack_name8(s.name) + struct.pack('>L', 0))
        for ln, un, addr in s.entries:
            out += block(ENTRYPOINT, pack_name8(ln) + pack_name8(un) + struct.pack('>L', addr))
        code_at[s.name] = len(out)
        out += block(CODEBLOCK, struct.pack('>L', s.base) + bytes(s.image))
        out += block(ENDBLOCK, struct.pack('>L', len(s.image)))
    out += block(EOFMARK, b'')
    body = struct.pack('>H', len(loc_segs))
    for s in loc_segs:
        num, v1, v2, fnum = lk.iu_segs[s.name]
        body += pack_name8(s.name) + struct.pack('>HLLHLHH', num, v1, v2, fnum, code_at[s.name],
                                                 0, len(s.image) + 8)
    out[segloc_at + 4:segloc_at + 4 + len(body)] = body
    return pad512(bytes(out))


def link_intrinsic(inputs: Iterable[str], iulib: str, seg_map: Mapping[str, str] | None = None, workshop: str = '3.0') -> tuple[IntrinsicLinker, bytes]:
    """link input units and modules into an intrinsic library using unit/segment numbers from iulib"""
    lk = IntrinsicLinker(inputs, iulib, seg_map, workshop)
    lk.select()
    lk.closure()
    lk.place()
    lk.patch()
    return lk, write_library(lk)


def write_map(lk: IntrinsicLinker, path: str) -> None:
    """write an intrinsic library link map (segments, modules, vector entries, and units) to path"""
    with open(path, 'w') as f:
        for s in lk.segments:
            f.write("segment '%s' MMU %d $%06X %d bytes, %d vector entries\n" % (
                s.name, s.mmu, s.base, len(s.image), len(s.vector)))
            for m in s.modules:
                f.write('  module %-8s $%06X %6d  %s\n' % (m.name, m.offset, len(m.code), m.file.path))
            for ln, un, addr in sorted(s.entries, key=lambda e: e[2]):
                f.write('  entry  %-8s $%06X\n' % (ln, addr))
        for fl, name, num, typ in lk.units_of_library():
            f.write('unit %-8s number %3d type %d globals %d\n' % (name, num, typ, fl.unit[1]))
