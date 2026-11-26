#!/usr/bin/env python3
"""Parser and executor for the Lisa Workshop 3.0 ALEX/ASM exec/macro files that build the Lisa Office System's libraries and applications.

Assemble the Lisa Office System's assembly sources on a Lisa disk image
with assembler/assembler.py, as the Workshop exec files on that image do, and
compare every object file with the one the Lisa Assembler made (also on the
image).  Used by tests/run_asm_test.sh, which documents it.

For target T, the steps are read from ALEX/ASM/T.TEXT:
  A{ssemble}SRC                           assemble: source, listing, output
  $SUBMIT BUILD/ASSEMB(SRC[,OBJ[,SEG]])   assemble SRC.TEXT into OBJ.OBJ (default
                                          SRC); with SEG, CHANGESEG then puts all
                                          its modules into segment SEG
                                          (BUILD/ASSEMB.TEXT)
  R{un}CHANGESEG / OBJ / Y{es...}SEG      the same, as a separate step
  R{un}LIBQD/FIXMOVE.OBJ / OBJ            replace MQVE by MOVE in the first 1024
                                          bytes of OBJ (libqd/fixmove.text: a
                                          procedure cannot be named MOVE)
Other commands (FileMgr deletes, other programs) are skipped.
"""
from __future__ import annotations

from collections.abc import Sequence
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
NEW = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(NEW, 'assembler'))
from los_build import IMAGE, TOOL, check_image_exists, lisa_lines, stem, answers  # noqa: E402
from changeseg import change_segments                            # noqa: E402

# the targets of the image's ALEX/ASM exec files
ALL = ['LIBPL', 'LIBHW', 'LIBFP', 'LIBSM', 'LIBIN', 'LIBDB', 'LIBQD', 'LIBFM', 'LIBWM',
       'LIBAM', 'LIBPR_PRLIB', 'LIBPR_DAISY', 'LIBPR_CANON', 'LIBPR_CITOH', 'LIBUT', 'LIBTE',
       'LIBTK', 'LIBQP', 'APDM', 'APLC', 'APLD', 'APLL', 'APLP', 'APLT', 'APLW', 'APPW',
       'PREDRIVER', 'SYSTEMOS']

# objects known to differ from the Lisa-built ones, and why
KNOWN_DIFFS: dict[str, str] = {}


class Failed(Exception):
    """Raised when extracting a file, assembling a source, or verifying outputs fails."""
    pass


class Job:
    """Isolated workspace and Lisa disk-image copy for assembling and comparing ALEX/ASM targets."""

    def __init__(self, work: str) -> None:
        """Create build and reference directories under work and copy the base Lisa disk image."""
        self.work = work
        self.image = os.path.join(work, 'los.image')
        self.dir = os.path.join(work, 'build')
        self.ref = os.path.join(work, 'ref')
        os.makedirs(self.dir)
        os.makedirs(self.ref)
        shutil.copyfile(IMAGE, self.image)       # only this copy is read
        self.got = set()

    def get(self, lisa_name: str, host: str, optional: bool = False) -> bool:
        """Extract lisa_name raw from the working disk image to host via LisaFileSystemToolPerFile.py get-binary."""
        os.makedirs(os.path.dirname(host) or '.', exist_ok=True)
        r = subprocess.run([sys.executable, TOOL, 'get-binary', self.image, lisa_name, host],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        if r.returncode == 3 and optional:
            return False
        if r.returncode != 0:
            raise Failed('cannot get %s from the image:\n%s' % (lisa_name, r.stdout[-500:]))
        return True

    def path(self, lisa_name: str) -> str:
        """Return the uppercase host path inside the build directory for lisa_name."""
        return os.path.join(self.dir, lisa_name.upper())

    def source(self, name: str) -> None:
        """a source file and, recursively, the files it .INCLUDEs"""
        todo = [name]
        while todo:
            n = todo.pop()
            n = n if n.upper().endswith('.TEXT') else n + '.TEXT'
            if n.upper() in self.got:
                continue
            self.got.add(n.upper())
            self.get(n, self.path(n))
            for line in lisa_lines(open(self.path(n), 'rb').read()):
                m = re.match(r"\s*\.INCLUDE\s+([^\s;]+)", line, re.I)
                if m:
                    todo.append(m.group(1))

    def assemble(self, src: str, out: str, seg: str) -> None:
        """Fetch src and its .INCLUDE dependencies, run assembler.py to produce out.OBJ, and optionally rename its segments to seg."""
        self.source(src)
        log = os.path.join(self.work, 'asm-%s.log' % os.path.basename(out))
        with open(log, 'w') as f:
            r = subprocess.run([sys.executable, os.path.join(NEW, 'assembler', 'assembler.py'),
                                src, '', out], cwd=self.dir, stdout=f, stderr=subprocess.STDOUT)
        if r.returncode != 0:
            raise Failed('assembling %s:\n%s' % (src, open(log).read()[-3000:]))
        if seg:
            self.changeseg(out, seg)

    def changeseg(self, out: str, seg: str) -> None:
        """Rewrite all module segment names in out.OBJ to seg, matching Workshop CHANGESEG."""
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

    def compare(self, out: str) -> str:
        """Compare the newly assembled out.OBJ byte-for-byte against the Lisa-built object on the image and return 'same', 'known', or 'different'."""
        ref = os.path.join(self.ref, out.replace('/', '-') + '.OBJ')
        self.get(out + '.OBJ', ref)
        ours, theirs = open(self.path(out + '.OBJ'), 'rb').read(), open(ref, 'rb').read()
        name = '  %-24s %6d bytes, ' % (out.upper() + '.OBJ', len(ours))
        if ours == theirs:
            note = ' (listed in KNOWN_DIFFS as a difference: remove it there)' if out.upper() in KNOWN_DIFFS else ''
            print(name + 'identical' + note)
            return 'same'
        print(name + 'DIFFERENT from the image (%d bytes)' % len(theirs))
        if out.upper() in KNOWN_DIFFS:
            print('  %24s known difference: %s' % ('', KNOWN_DIFFS[out.upper()]))
            return 'known'
        return 'different'


def asm_step(lines: Sequence[str], i: int) -> tuple[tuple[str, ...], int] | None:
    """the assembler step at lines[i]: (step, index of the next line), or
    None.  Steps: ('asm', src, out, seg), ('changeseg', obj, seg),
    ('fixmove', obj)"""
    raw = lines[i].strip()
    i += 1
    m = re.match(r'A\{ssemble\}(\S+)', raw)
    if m and i + 1 < len(lines):
        # A{ssemble}SRC, then the listing file and the output file (empty: none, default)
        src = stem(m.group(1))
        out = stem(answers(lines[i + 1])) or src
        return ('asm', src, out, ''), i + 2
    m = re.match(r'\$SUBMIT\s+BUILD/ASSEMB\((.*)\)', raw, re.I)
    if m:
        a = [x.strip() for x in m.group(1).split(',')] + ['', '']
        return ('asm', stem(a[0]), stem(a[1] or a[0]), a[2]), i
    m = re.match(r'R\{un\}(\S*FIXMOVE)(\.OBJ)?$', raw, re.I)
    if m and i < len(lines):
        # LIBQD/FIXMOVE (libqd/fixmove.text): "Assembler restrictions require
        # procedure Move to be assembled as MQVE"; it replaces MQVE by MOVE in
        # the first 1024 bytes of the object file
        return ('fixmove', stem(answers(lines[i]))), i + 1
    if raw.upper().startswith('R{UN}CHANGESEG') and i + 1 < len(lines):
        obj = stem(answers(lines[i]))
        seg = re.sub(r'^Y\{[^}]*\}', '', lines[i + 1].strip())
        return ('changeseg', obj, seg), i + 2
    return None


def parse_exec(lines: Sequence[str]) -> list[tuple[str, ...]]:
    """the assembler steps of an exec file (see asm_step), and ('skip', text)"""
    steps, i = [], 0
    while i < len(lines):
        r = asm_step(lines, i)
        if r:
            steps.append(r[0])
            i = r[1]
            continue
        raw = lines[i].strip()
        i += 1
        a = answers(raw)
        if a and not raw.startswith('$') and not raw.startswith('Y{') and not raw.startswith('F{'):
            steps.append(('skip', a))
    return steps


def main(targets: Sequence[str]) -> int:
    """Execute the ALEX/ASM build steps for targets and verify every assembled .OBJ against the reference disk image."""
    if not check_image_exists('tests/run_asm_test.sh'):
        return 1
    if not os.path.isfile(TOOL):
        print('FAILED: no %s' % TOOL)
        return 1
    work = tempfile.mkdtemp()
    try:
        j = Job(work)
        n = bad = known = 0
        for t in targets:
            host = os.path.join(work, 'ASM-%s.TEXT' % t)
            j.get('ALEX/ASM/%s.TEXT' % t, host)
            steps = parse_exec(lisa_lines(open(host, 'rb').read()))
            print('%s (ALEX/ASM/%s.TEXT):' % (t, t))
            outs = []
            for s in steps:
                if s[0] == 'asm':
                    j.assemble(s[1], s[2], s[3])
                    outs.append(s[2])
                elif s[0] == 'changeseg':
                    j.changeseg(s[1], s[2])
                elif s[0] == 'fixmove':
                    j.fixmove(s[1])
                else:
                    print('  skipped: %s' % s[1])
            for out in outs:
                n += 1
                r = j.compare(out)
                bad += r == 'different'
                known += r == 'known'
        if bad:
            raise Failed('%d of %d object files differ from the Lisa-built ones' % (bad, n))
        print('%d object files: %d identical to the Lisa-built ones on the image%s' % (
            n, n - known, ', %d known differences' % known if known else ''))
        print('PASSED')
        shutil.rmtree(work)
        return 0
    except Failed as e:
        print('FAILED: %s' % e)
        print('files kept in %s' % work)
        return 1


if __name__ == '__main__':
    sys.exit(main([a.upper() for a in sys.argv[1:]] or ALL))
