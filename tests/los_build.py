#!/usr/bin/env python3
"""Parser and executor for the Lisa Workshop 3.0 ALEX/MAKE exec/macro files that build the Lisa Office System's libraries and applications.

Build the Lisa Office System from the sources on a Lisa disk image,
following the Workshop exec files on that image, and compare every output
with the one built on the Lisa (also on the image).  Used by
tests/run_lisa_sources_build_tests.sh, which documents it.

A target T is the exec file ALEX/MAKE/T.TEXT (by default ALL_NODISKS: the
image's whole build), or, without one, ALEX/ASM/T, ALEX/COMP/T and
ALEX/LINK/T; a name with a slash is one exec file (ALEX/LINK/SYS1LIB).  The
exec files are run in order, $SUBMIT ALEX/... recursively (each once), with
the parameters of $SUBMIT FILE(...) for $IF %n='' THEN / $ELSE / $ENDIF:
  $SUBMIT BUILD/ASSEMB(...), A{ssemble}, R{un}CHANGESEG, R{un}...FIXMOVE
                                     assemble with assembler/assembler.py,
                                     as tests/asm_build.py does
  P{ascal Compile}SRC                compile: source, listing, output
  P{ascal Compile}?                  the same, with the name of the
                                     intrinsic.lib to use first
  $SUBMIT BUILD/COMP(SRC[,OBJ[,LIB]])   compile, as BUILD/COMP.TEXT does
  L{inker}INPUT                      link: inputs up to an empty answer,
                                     then listing, then output
  L{inker}?                          the same, after the options (lines
                                     that start with + or -: +I, +M OLD NEW,
                                     +P, -O, +F, +W and the next line)
  F{ilemgr}C{opy}SRC / DEST          copy a file of this build or the image
  F{ilemgr}R{ename}OLD / NEW         a link output renamed: compared under NEW
  R{un}Alert / SRC / OUT             compile phrase file SRC.TEXT into OUT[PHRASE]
                                     with alert/alert.py
  R{un}IUMANAGER                     not run here: its output file (an
                                     intrinsic unit directory) is taken
                                     from the image
Other commands (FileMgr deletes, programs such as InstallTool and PACKSEG,
$SUBMIT BUILD/INSTALL, ...) are listed as skipped; comments that
span lines and what follows $ENDEXEC are ignored, as the Exec processor
does.  An output that a later step writes again (a program compiled into
P.OBJ, then linked into P.OBJ) is only compared in its final form.

Files come from the image, unchanged ("LisaFileSystemToolPerFile.py
get-binary"): the exec files, the sources and their include files ({$I name}
and (*$Iname*)), and every input that this run does not build: the units
named by $U, the libraries, and INTRINSIC.LIB.  A $U name that is not a file
on the image is an intrinsic unit, which the compiler finds through
INTRINSIC.LIB.

The boot volume is the image: the compiler's boot folder is the Workshop 3.0
one with the image's INTRINSIC.LIB and the libraries it lists put in their
place, so that the interfaces of intrinsic units are those the Lisa build
read.
"""
from __future__ import annotations

from collections.abc import Sequence
import os
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
NEW = os.path.dirname(HERE)
IMAGE = os.environ.get('LOS_IMAGE') or os.path.join(
    HERE, 'LOSandWorkshop3.0_WithCompiledLisaSources_DO_NOT_COMMIT.image')
TOOL = os.path.join(NEW, 'file-system-tools', 'LisaFileSystemToolPerFile.py')
BUILD = os.environ.get('BUILD', '3.0')


def check_image_exists(script_name: str) -> bool:
    """Verify IMAGE exists on disk, printing a human-readable explanation if missing."""
    if os.path.isfile(IMAGE):
        return True
    default_rel = 'tests/LOSandWorkshop3.0_WithCompiledLisaSources_DO_NOT_COMMIT.image'
    sys.stderr.write(
        f'ERROR: Disk image not found: {IMAGE}\n\n'
        f'This test requires a Lisa Office System Workshop 3.0 build image\n'
        f'(by default, {default_rel}).\n'
        f'Because that image contains copyrighted Apple Lisa source files,\n'
        f'it is not included in this repository.\n\n'
        f'To run this test locally, place the image at:\n'
        f'  {default_rel}\n'
        f'or point LOS_IMAGE to your copy:\n'
        f'  LOS_IMAGE=/path/to/image {script_name}\n'
    )
    return False



class Failed(Exception):
    """Raised when extracting an input, compiling, assembling, linking, or comparing outputs fails."""
    pass


class Unsupported(Exception):
    """Raised when an exec file uses a Workshop Linker option not supported by lisalinker.py."""
    pass


# Reference .OBJ files on the disk image were compiled on a Lisa with the
# Pascal compiler for Workshop 3.0:
#   * BUILD=3.0 (default: our Workshop 3.0 compiler): KNOWN_DIFFS is empty and
#     all 456 files on the image must match 100% byte-for-byte (WS30_ONLY is
#     never printed).
#   * BUILD=2.0 (forcing our Workshop 2.0 compiler, --2.0, against the
#     Workshop 3.0 reference image): 3 units differ because of a Workshop 3.0
#     code-generator optimization on boolean register variables.  KNOWN_DIFFS
#     lists those 3 units so the test explains why they differ instead of
#     failing (a link output whose inputs differ is also re-linked from the
#     Lisa-built inputs on the image, and that link must still be identical).
WS30_ONLY = ('compiled on the Lisa with the Pascal compiler for Workshop 3.0, whose code '
             'generator sets a boolean register variable in place (ANDI.W #1 on the register '
             'itself, not on a copy, 2 bytes shorter); the Workshop 2.0 build does not. ')
KNOWN_DIFFS: dict[str, str] = {}
if BUILD == '2.0':
    KNOWN_DIFFS.update({'LIBFP/NEWFPLIB': WS30_ONLY, 'LIBFP/MATHLIB': WS30_ONLY, 'LIBTK/UTEXT': WS30_ONLY})


def lisa_lines(data: bytes) -> list[str]:
    """the lines of a Lisa .TEXT file (header page, NULs and DLE
    indentation removed)"""
    t = data[1024:].replace(b'\0', b'')
    t = re.sub(rb'\x10(.)', lambda m: b' ' * max(m.group(1)[0] - 32, 0), t, flags=re.S)
    return t.decode('latin-1').split('\r')


def exec_lines(data: bytes, args: Sequence[str] = ()) -> list[str]:
    """the lines of an exec file, without comments that span lines ({ on
    one line, } on a later one: commented-out commands) and the lines of
    $IF branches not taken (conditions %n='' and %n<>'', with the
    parameters of $SUBMIT FILE(...)); those lines are left empty, so the
    line count stays the same"""
    lines = lisa_lines(data)
    out, active = [], [True]
    for line in lines:
        s = line.strip().upper()
        m = re.match(r"\$IF\s+%(\d)\s*(=|<>)\s*''\s+THEN", s)
        if m:
            n = int(m.group(1))
            empty = not (n < len(args) and args[n])
            active.append(active[-1] and (empty if m.group(2) == '=' else not empty))
            out.append('')
            continue
        if s.startswith('$ELSE') and len(active) > 1:
            active[-1] = not active[-1] and active[-2]
            out.append('')
            continue
        if s.startswith('$ENDIF') and len(active) > 1:
            active.pop()
            out.append('')
            continue
        out.append(line if active[-1] else '')
    lines = out
    # the Exec processor stops at $ENDEXEC: what follows are notes
    for k, line in enumerate(lines):
        if line.strip().upper().startswith('$ENDEXEC'):
            lines = lines[:k + 1]
            break
    text = '\r'.join(lines)
    text = text.replace('~{', '\x01').replace('~}', '\x02')
    text = re.sub(r'\{[^}]*\r[^}]*\}', lambda m: '\r' * m.group(0).count('\r'), text)
    text = text.replace('\x01', '~{').replace('\x02', '~}')
    return text.split('\r')


def stem(name: str) -> str:
    """Strip a trailing .TEXT or .OBJ suffix (case-insensitive) and surrounding whitespace from a Lisa file name."""
    return re.sub(r'\.(TEXT|OBJ)$', '', name.strip(), flags=re.I)


def answers(line: str) -> str:
    """an exec file line as the answer it gives: comments removed and ~{ / ~} unescaped"""
    s = line.replace('~{', '\x01').replace('~}', '\x02')
    s = re.sub(r'\{[^}]*\}', '', s).strip()
    return s.replace('\x01', '{').replace('\x02', '}')


def alert_output_name(src: str, out_arg: str) -> str:
    """Return the Lisa output filename that the Alert tool writes for (src, out_arg)."""
    alert_dir = os.path.join(NEW, 'alert')
    if alert_dir not in sys.path:
        sys.path.insert(0, alert_dir)
    from alert import split_input_stem, strip_lisa_volume, su_add_extension
    s = out_arg.strip()
    if not s:
        vol_dir, rootname = split_input_stem(src)
        return f'{vol_dir}{rootname}PHRASE'
    return su_add_extension(strip_lisa_volume(s), 'PHRASE')


def parse_exec(lines: Sequence[str]) -> list[tuple[Any, ...] | list[Any]]:
    """the steps of an exec file, in order: ('compile', src, out, iulib),
    ['link', out, inputs, options, renamed] (renamed: the name a FileMgr
    Rename gives the output, else None), the assembler steps of
    tests/asm_build.py (('asm', src, out, seg), ('changeseg', obj, seg),
    ('fixmove', obj)), ('submit', exec file) for $SUBMIT ALEX/..., and
    ('skip', text)"""
    import asm_build
    steps, i, filemgr = [], 0, False
    while i < len(lines):
        if not filemgr:
            r = asm_build.asm_step(lines, i)
            if r:
                steps.append(r[0])
                i = r[1]
                continue
        raw = lines[i].strip()
        i += 1
        m = re.match(r'\$SUBMIT\s+(ALEX/\S+?)(\((.*)\))?\s*(\{.*)?$', raw, re.I)
        if m:
            args = tuple(a.strip() for a in m.group(3).split(',')) if m.group(3) else ()
            steps.append(('submit', m.group(1), args))
            continue
        if filemgr or raw.startswith('F{ilemgr}'):
            if not filemgr:
                steps.append(('skip', re.sub(r'\{([^}]*)\}', r'(\1) ', raw).strip()))
            m = re.search(r'C\{opy\}(\S+)', raw)
            if m and i < len(lines):
                # FileMgr Copy SRC, DEST (SYSTEMOS copies LIBHW/HWINTL.OBJ into OBJECT/)
                steps.append(('copy', m.group(1), answers(lines[i])))
            m = re.search(r'R\{ename\}(\S+)', raw)
            if m and i < len(lines):
                # FileMgr Rename OLD, NEW: a link output that is renamed is on
                # the image under its new name (LIBHW/SYSTEM.LLD.OBJ ->
                # LIBHW/SYSTEM.LLD)
                old, new = m.group(1), answers(lines[i])
                for s in reversed(steps):
                    if s[0] == 'link' and (s[1] + '.OBJ').upper() == old.upper():
                        s[4] = new
                        break
            filemgr = 'Q{uit}' not in raw
            continue
        if re.match(r'R\{un\}IUMANAGER\b', raw, re.I) and i + 1 < len(lines):
            # IUManager edits an intrinsic unit directory (input file, output
            # file, then its commands); it does not run here: its output is
            # taken from the image
            steps.append(('iumanager', answers(lines[i + 1]) or answers(lines[i]) or 'INTRINSIC.LIB'))
            i += 2
            continue
        if re.match(r'R\{un\}ALERT\b', raw, re.I) and i + 1 < len(lines):
            src, out_arg = answers(lines[i]), answers(lines[i + 1])
            i += 2
            steps.append(('alert', src, out_arg, alert_output_name(src, out_arg)))
            continue
        m = re.match(r'P\{ascal Compile\}(\S*)', raw)
        if m:
            src = m.group(1)
            iulib = None
            if src == '?':
                iulib, src = answers(lines[i]), answers(lines[i + 1])
                i += 2
            _listing, out = answers(lines[i]), answers(lines[i + 1])
            i += 2
            steps.append(('compile', stem(src), stem(out or src), iulib))
            continue
        m = re.match(r'\$SUBMIT\s+BUILD/COMP\((.*)\)', raw, re.I)
        if m:
            args = [a.strip() for a in m.group(1).split(',')]
            args += [''] * (3 - len(args))
            steps.append(('compile', stem(args[0]), stem(args[1] or args[0]), args[2] or 'intrinsic.lib'))
            continue
        m = re.match(r'L\{inker\}(\S*)', raw)
        if m:
            first, options = m.group(1), []
            if first == '?':
                # the options: lines that start with + or -, up to an empty
                # line or the first input file
                while answers(lines[i])[:1] in ('+', '-'):
                    opt = answers(lines[i])
                    i += 1
                    if opt.upper() == '+W':
                        # +W: the intrinsic unit directory, on the next line
                        opt += ' ' + answers(lines[i])
                        i += 1
                    options.append(opt)
                if not answers(lines[i]):
                    i += 1
                first = answers(lines[i])
                i += 1
            inputs = [stem(first)]
            while answers(lines[i]):
                inputs += [stem(x) for x in answers(lines[i]).split()]
                i += 1
            out = answers(lines[i + 2])
            i += 3
            steps.append(['link', stem(out), inputs, options, None])   # None: not renamed
            continue
        if answers(raw) and not raw.startswith('$EXEC') and not raw.startswith('$ENDEXEC') \
                and not raw.startswith('${') and raw != '$':
            steps.append(('skip', answers(raw)))
    return steps


class Build:
    """Workspace manager that extracts sources and libraries from a Lisa disk image, runs the cross-build tools, and compares outputs."""

    def __init__(self, work: str) -> None:
        """Set up the temporary build, reference, and Workshop boot directories in work from a copy of the Lisa disk image."""
        self.work = work
        self.image = os.path.join(work, 'los.image')
        self.dir = os.path.join(work, 'build')
        self.ref = os.path.join(work, 'ref')
        os.makedirs(self.dir)
        os.makedirs(self.ref)
        shutil.copyfile(IMAGE, self.image)       # only this copy is read
        self.built = set()                       # outputs of this run (upper case)
        self.differ = set()                      # of them, those that differ from the image's
        self.relinked = {}                       # link output: the same link from the Lisa-built inputs
        self.from_image = []
        self.boot_files = []
        self.make_boot()

    def get(self, lisa_name: str, host: str, optional: bool = False) -> bool:
        """copy a file from the image; with optional, False if the image
        has no such file"""
        os.makedirs(os.path.dirname(host) or '.', exist_ok=True)
        r = subprocess.run([sys.executable, TOOL, 'get-binary', self.image, lisa_name, host],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        if r.returncode == 3 and optional:
            return False
        if r.returncode != 0:
            raise Failed('cannot get %s from the image:\n%s' % (lisa_name, r.stdout[-500:]))
        return True

    def make_boot(self) -> None:
        """the boot volume for the compiler: on the Lisa it is this image, so
        the boot folder is the Workshop 3.0 one with the image's INTRINSIC.LIB
        and the libraries it lists ("-#BOOT-SYS1LIB.OBJ", ...) put in their
        place.  The compiler reads the interfaces of intrinsic units from them
        (a unit named by $U that is not a file, such as {$U UnitStd})."""
        self.boot = os.path.join(self.work, 'boot')
        shutil.copytree(os.environ.get('LISA_BOOT') or os.path.join(NEW, 'libs', 'workshop3.0'), self.boot, symlinks=True)
        sys.path.insert(0, os.path.join(NEW, 'linker'))
        from lisaobj import read_blocks, be16, be32, STRINGBLOCK

        def put(name: str) -> bool:
            for e in os.listdir(self.boot):
                if e.lower() == name.lower():
                    os.remove(os.path.join(self.boot, e))
            return self.get(name, os.path.join(self.boot, name), optional=True)
        put('INTRINSIC.LIB')
        data = open(os.path.join(self.boot, 'INTRINSIC.LIB'), 'rb').read()
        for b in read_blocks(data):
            if b.type == STRINGBLOCK:
                for i in range(be16(b.body)):
                    addr = be32(b.body, 2 + 6 * i + 2)
                    name = data[addr + 1:addr + 1 + data[addr]].decode('latin-1')
                    name = re.sub(r'^-[^-]*-', '', name).strip()
                    if name and not name.startswith('*') and put(name):
                        self.boot_files.append(name)

    def get_text(self, lisa_name: str, host: str) -> bytes:
        """a .TEXT file as it is on the disk (header page, 1 KB pages): a
        unit's .OBJ holds its interface pages as they are, so the compiler
        must read them unchanged ("get" would convert to host text)"""
        self.get(lisa_name, host)
        return open(host, 'rb').read()

    def path(self, lisa_name: str) -> str:
        """Return the uppercase host path inside the build directory for lisa_name."""
        return os.path.join(self.dir, lisa_name.upper())

    def have(self, lisa_name: str) -> bool:
        """Return True if lisa_name already exists in the local build directory."""
        return os.path.exists(self.path(lisa_name))

    def need(self, lisa_name: str, optional: bool = False) -> None:
        """a file this step reads: from the image unless it is here"""
        if not self.have(lisa_name):
            if not self.get(lisa_name, self.path(lisa_name), optional):
                return
            self.from_image.append(lisa_name.upper())

    # ---- the ALEX/ASM steps: assembler/assembler.py, CHANGESEG, FIXMOVE
    def assemble(self, src: str, out: str, seg: str) -> None:
        """assemble SRC.TEXT (with its .INCLUDE files) into OUT.OBJ, as
        BUILD/ASSEMB.TEXT or A{ssemble} do; with seg, then CHANGESEG"""
        todo, first = [src], True
        while todo:
            n = todo.pop()
            n = n if n.upper().endswith('.TEXT') else n + '.TEXT'
            if self.have(n):
                continue
            if first:
                self.get(n, self.path(n))
            else:
                self.need(n)
            first = False
            for line in lisa_lines(open(self.path(n), 'rb').read()):
                m = re.match(r"\s*\.INCLUDE\s+([^\s;]+)", line, re.I)
                if m:
                    todo.append(m.group(1))
        log = os.path.join(self.work, 'asm-%s.log' % os.path.basename(out))
        with open(log, 'w') as f:
            r = subprocess.run([sys.executable, os.path.join(NEW, 'assembler', 'assembler.py'), src, '', out],
                               cwd=self.dir, stdout=f, stderr=subprocess.STDOUT)
        if r.returncode != 0 or not self.have(out + '.OBJ'):
            raise Failed('the assembler, %s (see %s)' % (src, log))
        self.built.add(out.upper())
        if seg:
            self.changeseg(out, seg)

    def copy(self, src: str, dest: str) -> None:
        """FileMgr Copy: a file of this build or of the image"""
        self.need(src, optional=True)
        if not self.have(src):
            print('  not copied: no %s' % src.upper())
            return
        os.makedirs(os.path.dirname(self.path(dest)) or '.', exist_ok=True)
        shutil.copyfile(self.path(src), self.path(dest))
        print('  copied %s to %s' % (src.upper(), dest.upper()))
        if stem(src).upper() in self.built:
            self.built.add(stem(dest).upper())

    def changeseg(self, out: str, seg: str) -> None:
        """Rewrite all module segment names in out.OBJ to seg, matching Workshop CHANGESEG."""
        sys.path.insert(0, os.path.join(NEW, 'assembler'))
        from changeseg import change_segments
        p = self.path(out + '.OBJ')
        data = open(p, 'rb').read()
        with open(p, 'wb') as f:
            f.write(change_segments(data, seg))

    def fixmove(self, out: str) -> None:
        """Replace 'MQVE' with 'MOVE' in the first 1024 bytes of out.OBJ, matching LIBQD/FIXMOVE."""
        p = self.path(out + '.OBJ')
        data = open(p, 'rb').read()
        with open(p, 'wb') as f:
            f.write(data[:1024].replace(b'MQVE', b'MOVE') + data[1024:])

    def compile(self, src: str, out: str, iulib: str | None) -> None:
        """Fetch src.TEXT, its {$I} include files, and {$U} unit .OBJ files from the image as needed, and compile src into out.OBJ with lpc.py."""
        data = self.get_text(src + '.TEXT', self.path(src + '.TEXT'))
        text = '\r'.join(lisa_lines(data))
        # include files, also those of include files; a name that is not on
        # the image is in a branch of $IFC that is not compiled (e.g.
        # {$I libdb/poolrout.text} and {$I l:poolrout.text})
        todo, seen = [text], set()
        while todo:
            t = todo.pop()
            # {$I name}, also (*$Iname*) (the OS sources); not $IFC, $I+, $I-
            for inc in re.findall(r'\$I(?!FC\b)\s*([^\s}*)+-][^\s}*)]*)', t, re.I):
                inc = inc if re.search(r'\.TEXT$', inc, re.I) else inc + '.TEXT'
                if inc.upper() in seen:
                    continue
                seen.add(inc.upper())
                self.need(inc, optional=True)
                if self.have(inc):
                    todo.append('\r'.join(lisa_lines(open(self.path(inc), 'rb').read())))
        for unit in re.findall(r'\$U\s+([^\s}*)]+)', text, re.I):
            # not a file: an intrinsic unit, found through INTRINSIC.LIB
            self.need(unit if re.search(r'\.OBJ$', unit, re.I) else unit + '.OBJ', optional=True)
        args = [os.path.join(NEW, 'pascal', 'lpc.py')] + (['--2.0'] if BUILD == '2.0' else [])
        if iulib:
            self.need(iulib)
            args += ['?', iulib.upper()]
        args += [src.upper(), '', out.upper()]
        # a Lisa file name such as OBJECT/X is a host path: its folder must exist
        os.makedirs(os.path.dirname(self.path(out)) or '.', exist_ok=True)
        log = os.path.join(self.work, 'compile-%s.log' % os.path.basename(out))
        env = dict(os.environ, LISA_BOOT=self.boot)
        audit_cmd = [
            sys.executable,
            os.path.join(NEW, 'pascal', 'audit_8char.py'),
            '-q',
            '--no-units',
            '--boot',
            self.boot,
            src.upper(),
        ]
        audit_res = subprocess.run(
            audit_cmd, cwd=self.dir, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env
        )
        if audit_res.returncode != 0:
            raise Failed('audit_8char %s:\n%s' % (src, audit_res.stdout))
        with open(log, 'w') as f:
            res = subprocess.run(args, cwd=self.dir, stdin=subprocess.DEVNULL, stdout=f, stderr=subprocess.STDOUT, env=env)
        if res.returncode != 0 or not self.have(out + '.OBJ'):
            raise Failed('compiling %s (see %s)' % (src, log))
        self.built.add(out.upper())

    def link(self, out: str, inputs: Sequence[str], options: Sequence[str]) -> None:
        """Link inputs into out.OBJ with lisalinker.py using translated Workshop Linker options, and relink against Lisa-built inputs if any local input differed."""
        args = [sys.executable, os.path.join(NEW, 'linker', 'lisalinker.py')]
        for opt in options:
            o = opt.split()
            if o[0].upper() == '+I':
                args.append('-i')
                self.need('INTRINSIC.LIB')
            elif o[0].upper() == '+P':
                args.append('-P')
            elif o[0].upper() == '-O':
                args.append('--no-osdata')
            elif o[0].upper() == '+F':
                args.append('--domain0')
            elif o[0].upper() == '+M' and len(o) == 3:
                args += ['-s', '%s=%s' % (o[1], o[2])]
            elif o[0].upper() == '+W' and len(o) == 2:
                self.need(o[1])
                args += ['--iulib', o[1].upper()]
            else:
                raise Unsupported('linker option %s is not supported' % opt)
        for i in inputs:
            if i.upper() not in self.built:
                self.need(i + '.OBJ')
        os.makedirs(os.path.dirname(self.path(out)) or '.', exist_ok=True)
        log = os.path.join(self.work, 'link-%s.log' % os.path.basename(out))
        args += ['-m', os.path.join(self.work, os.path.basename(out) + '.map'), '-o', out.upper()]
        args += [i.upper() for i in inputs]
        with open(log, 'w') as f:
            r = subprocess.run(args, cwd=self.dir, stdout=f, stderr=subprocess.STDOUT)
        if r.returncode != 0:
            raise Failed('linking %s:\n%s' % (out, open(log).read()))
        self.built.add(out.upper())
        # inputs built here that differ from the image's: link again from the
        # Lisa-built ones, to check the Linker apart from the compiler
        changed = [i for i in inputs if i.upper() in self.differ]
        if changed:
            lisa = os.path.join(self.work, 'lisa-inputs')
            alt = []
            for i in inputs:
                if i.upper() in self.differ:
                    host = os.path.join(lisa, i.upper() + '.OBJ')
                    self.get(i + '.OBJ', host)
                    alt.append(host)
                else:
                    alt.append(i.upper())
            relinked = os.path.join(self.work, 'relinked', out.upper() + '.OBJ')
            os.makedirs(os.path.dirname(relinked), exist_ok=True)
            k = args.index('-o')
            r = subprocess.run(args[:k] + ['-o', relinked] + alt, cwd=self.dir,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            if r.returncode != 0:
                raise Failed('linking %s from the Lisa-built inputs:\n%s' % (out, r.stdout))
            self.relinked[out.upper()] = (relinked, changed)

    def alert(self, src: str, out_arg: str, out_file: str) -> None:
        """Fetch src.TEXT (and any $include .TEXT files) from the image and compile out_file with alert/alert.py."""
        src_file = src if src.upper().endswith('.TEXT') else src + '.TEXT'
        data = self.get_text(src_file, self.path(src_file))
        todo = [lisa_lines(data)]
        seen = {src_file.upper()}
        while todo:
            for line in todo.pop():
                if line.startswith('$') and not line.startswith('$~'):
                    inc = line[1:].split('~')[0].strip()
                    if inc and not inc.endswith('.') and not inc.upper().endswith('.TEXT'):
                        inc += '.TEXT'
                    if inc and inc.upper() not in seen:
                        seen.add(inc.upper())
                        self.need(inc, optional=True)
                        if self.have(inc):
                            todo.append(lisa_lines(open(self.path(inc), 'rb').read()))
        os.makedirs(os.path.dirname(self.path(out_file)) or '.', exist_ok=True)
        log = os.path.join(self.work, 'alert-%s.log' % os.path.basename(out_file))
        args = [sys.executable, os.path.join(NEW, 'alert', 'alert.py'), src.upper(), out_arg.upper()]
        with open(log, 'w') as f:
            r = subprocess.run(args, cwd=self.dir, stdin=subprocess.DEVNULL, stdout=f, stderr=subprocess.STDOUT)
        if r.returncode != 0 or not self.have(out_file):
            raise Failed('alert %s -> %s (see %s)' % (src, out_file, log))
        self.built.add(out_file.upper())

    def compare_phrase(self, out_file: str) -> str:
        """Compare a generated PHRASE file byte-for-byte against the copy on the disk image."""
        ref = os.path.join(self.ref, out_file.upper().replace('/', '-'))
        ours = open(self.path(out_file), 'rb').read()
        name = '  %-22s %6d bytes, ' % (out_file.upper(), len(ours))
        if not self.get(out_file, ref, optional=True):
            print(name + 'built (not on the image)')
            return 'missing'
        theirs = open(ref, 'rb').read()
        if ours == theirs:
            note = ' (listed in KNOWN_DIFFS as a difference: remove it there)' if out_file.upper() in KNOWN_DIFFS else ''
            print(name + 'identical' + note)
            return 'same'
        self.differ.add(out_file.upper())
        print(name + 'DIFFERENT from the image (%d bytes)' % len(theirs))
        if out_file.upper() in KNOWN_DIFFS:
            print('  %22s known difference: %s' % ('', KNOWN_DIFFS[out_file.upper()]))
            return 'known'
        return 'different'

    def compare(self, out: str, renamed: str | None = None) -> str:
        """'same', 'known' (a known difference, see KNOWN_DIFFS, or a link whose
        only differences come from its inputs) or 'different'; renamed: the
        name the output has on the image"""
        lisa = renamed or out + '.OBJ'
        ref = os.path.join(self.ref, lisa.replace('/', '-'))
        self.get(lisa, ref)
        ours = open(self.path(out + '.OBJ'), 'rb').read()
        theirs = open(ref, 'rb').read()
        name = '  %-22s %6d bytes, ' % (out.upper() + '.OBJ', len(ours))
        if renamed:
            name = '  %-22s %6d bytes, ' % ('%s.OBJ (on the image: %s)' % (out.upper(), renamed.upper()), len(ours))
        if ours == theirs:
            note = ' (listed in KNOWN_DIFFS as a difference: remove it there)' if out.upper() in KNOWN_DIFFS else ''
            print(name + 'identical' + note)
            return 'same'
        self.differ.add(out.upper())
        print(name + 'DIFFERENT from the image (%d bytes)' % len(theirs))
        if out.upper() in self.relinked:
            path, changed = self.relinked[out.upper()]
            if open(path, 'rb').read() == theirs:
                print('  %22s linked from the Lisa-built %s instead: identical' % ('', ' '.join(changed)))
                return 'known'
            print('  %22s linked from the Lisa-built %s instead: still DIFFERENT' % ('', ' '.join(changed)))
        if out.upper() in KNOWN_DIFFS:
            print('  %22s known difference: %s' % ('', KNOWN_DIFFS[out.upper()]))
            return 'known'
        return 'different'


def main(targets: Sequence[str]) -> int:
    """Expand Workshop ALEX exec files for targets, run all assemble, compile, and link steps, and verify outputs against the Lisa disk image."""
    if not check_image_exists('tests/run_lisa_sources_build_tests.sh'):
        return 1
    if not os.path.isfile(TOOL):
        print('FAILED: no %s' % TOOL)
        return 1
    work = tempfile.mkdtemp()
    try:
        b = Build(work)
        unsupported = []
        count = {'n': 0, 'bad': 0, 'known': 0}

        def compare(out: str, renamed: str | None = None) -> None:
            r = b.compare(out, renamed)
            count['n'] += 1
            count['bad'] += r == 'different'
            count['known'] += r == 'known'

        done = set()

        def expand(path: str, args: Sequence[str] = ()) -> list[tuple[str, tuple[Any, ...] | list[Any]]]:
            """the steps of the exec file ALEX/... (with the parameters
            args), with $SUBMIT ALEX/... expanded (an exec file that was
            already expanded is not run again): [(exec file, step)]"""
            if path.upper() in done:
                return []
            done.add(path.upper())
            host = os.path.join(work, path.replace('/', '-') + '.TEXT')
            if not b.get(path + '.TEXT', host, optional=True):
                return [(path, ('skip', 'not on the image'))]
            out = []
            for s in parse_exec(exec_lines(open(host, 'rb').read(), args)):
                out += expand(s[1], s[2]) if s[0] == 'submit' else [(path, s)]
            return out

        steps = []
        for t in targets:
            if '/' in t:
                steps += expand(t)
            elif b.get('ALEX/MAKE/%s.TEXT' % t, os.path.join(work, 'ALEX-MAKE-%s.TEXT' % t), optional=True):
                steps += expand('ALEX/MAKE/' + t)
            else:
                for kind in ('ASM', 'COMP', 'LINK'):
                    steps += expand('ALEX/%s/%s' % (kind, t))
        # an output that a later step writes again (a program compiled into
        # P.OBJ and then linked into P.OBJ) is only compared in its final form
        written = [s[2].upper() if s[0] in ('compile', 'asm') else s[1].upper() if s[0] == 'link'
                   else s[3].upper() if s[0] == 'alert' else None
                   for p, s in steps]

        def final(k: int, out: str) -> bool:
            if out.upper() in written[k + 1:]:
                print('  %s.OBJ: written again by a later step' % out.upper())
                return False
            return True
        assembled = []

        def compare_assembled() -> None:
            for out in assembled:
                compare(out)
            assembled.clear()
        current = None
        for k, (path, s) in enumerate(steps):
            if assembled and (s[0] not in ('asm', 'changeseg', 'fixmove') or path != current):
                compare_assembled()     # the end of the assembler steps
            if path != current:
                print('%s:' % path)
                current = path
            if s[0] == 'asm':
                b.assemble(*s[1:])
                if final(k, s[2]):
                    assembled.append(s[2])
            elif s[0] == 'changeseg':
                b.changeseg(s[1], s[2])
            elif s[0] == 'copy':
                b.copy(s[1], s[2])
            elif s[0] == 'iumanager':
                b.get(s[1], b.path(s[1]))
                print('  IUManager (not run here): %s taken from the image' % s[1].upper())
            elif s[0] == 'fixmove':
                b.fixmove(s[1])
            elif s[0] == 'compile':
                b.compile(*s[1:])
                if final(k, s[2]):
                    compare(s[2])
            elif s[0] == 'alert':
                b.alert(*s[1:])
                if final(k, s[3]):
                    r = b.compare_phrase(s[3])
                    if r != 'missing':
                        count['n'] += 1
                        count['bad'] += r == 'different'
                        count['known'] += r == 'known'
            elif s[0] == 'link':
                try:
                    b.link(*s[1:4])
                except Unsupported as e:
                    print('  not linked: %s (%s)' % (s[1].upper(), e))
                    unsupported.append(s[1].upper())
                    continue
                print('  linked %s from %s%s' % (s[1].upper(), ' '.join(s[2]),
                                                ' (options %s)' % ', '.join(s[3]) if s[3] else ''))
                if final(k, s[1]):
                    compare(s[1], s[4])
            else:
                print('  skipped: %s' % s[1])
        compare_assembled()
        n, bad, known = count['n'], count['bad'], count['known']
        objs = [f for f in b.from_image if not f.endswith('.TEXT')]
        incs = [f for f in b.from_image if f.endswith('.TEXT')]
        if objs:
            print('not built here, taken from the image: %s' % ' '.join(objs))
        if incs:
            print('%d include files' % len(incs))
        print('boot folder: Workshop 3.0, with the image\'s INTRINSIC.LIB %s' % ' '.join(b.boot_files))
        if bad:
            raise Failed('%d of %d files differ from the Lisa-built ones (in %s)' % (bad, n, b.ref))
        print('%d files: %d identical to the Lisa-built ones on the image%s%s' % (
            n, n - known, ', %d known differences' % known if known else '',
            '; not linked (unsupported): %s' % ' '.join(unsupported) if unsupported else ''))
        print('PASSED')
        shutil.rmtree(work)
        return 0
    except Failed as e:
        print('FAILED: %s' % e)
        print('files kept in %s' % work)
        return 1


if __name__ == '__main__':
    sys.exit(main([a.upper() for a in sys.argv[1:]] or ['ALL_NODISKS']))
