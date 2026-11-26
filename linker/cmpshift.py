#!/usr/bin/env python3
"""Compare two linked programs whose main segments differ only because one
module has a different size (QDSAMPLE's INITICON: the Lisa code generator
of the time did not compact its literal pool, 250 bytes more).

    cmpshift.py OURS.obj OURS.map LISA.obj MODULE DELTA

(OURS.map: the link map from lisalinker.py -m)

The check: all blocks other than the Executable, CodeBlocks and EndBlocks
are identical; the other segments' code is identical; the main segment's
code is identical outside MODULE, except for PC-relative displacements that
point back across MODULE (they differ by DELTA); the Executable headers are
identical, and the jump table descriptors are too, once those behind MODULE
in the main segment are moved by DELTA.  Prints a one-line result; exit status 1 if anything else differs.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lisaobj import CODEBLOCK, ENDBLOCK, EXECUTABLE, be16, be32, read_blocks, sbe16


def main() -> None:
    """compare two linked object files modulo a size delta in one main-segment module"""
    ours_path, map_path, lisa_path, module, delta = sys.argv[1:4] + [sys.argv[4], int(sys.argv[5])]
    A = read_blocks(open(ours_path, 'rb').read())
    B = read_blocks(open(lisa_path, 'rb').read())
    problems = []
    if [b.type for b in A] != [b.type for b in B]:
        print('DIFFERENT block structure')
        sys.exit(1)
    # MODULE's place in the main segment (the first segment of the map)
    start = None
    for line in open(map_path):
        w = line.split()
        if w[0] == 'segment' and start is None and w[1] != "''":
            break
        if w[0] == 'module' and w[1] == module:
            start, end = int(w[2][1:], 16), int(w[2][1:], 16) + int(w[3])
            break
    if start is None:
        print('DIFFERENT: no module %s in the main segment' % module)
        sys.exit(1)
    code_a = [b.body for b in A if b.type == CODEBLOCK]
    code_b = [b.body for b in B if b.type == CODEBLOCK]
    a0, b0 = code_a[0][4:], code_b[0][4:]
    if len(b0) - len(a0) != delta:
        print('DIFFERENT main segment size: %d vs %d' % (len(a0), len(b0)))
        sys.exit(1)
    if a0[:start] != b0[:start]:
        problems.append('main segment before %s' % module)
    for p in range(end, len(a0), 2):
        if a0[p:p + 2] != b0[p + delta:p + delta + 2]:
            op = be16(a0, p - 2)
            ok = (op in (0x4EBA, 0x4EFA, 0x487A) or (op & 0xF1FF) == 0x41FA) and \
                sbe16(b0, p + delta) - sbe16(a0, p) == -delta and p + sbe16(a0, p) < end
            if not ok:
                problems.append('main segment $%X' % p)
    for x, y in zip(code_a[1:], code_b[1:]):
        if x != y:
            problems.append('segment at $%X' % be32(x))
    # jump table descriptors
    ea = [b.body for b in A if b.type == EXECUTABLE][0]
    eb = [b.body for b in B if b.type == EXECUTABLE][0]
    if ea[:40] != eb[:40]:
        problems.append('Executable header')
    va, vb = ea[40:], eb[40:]
    q = 2 + 12 * be16(va)
    n = be16(va, q)
    if n != be16(vb, q):
        problems.append('number of descriptors')
    base = be32(code_a[0]) + 8
    for i in range(n):
        da, db = be32(va, q + 4 + 6 * i), be32(vb, q + 4 + 6 * i)
        if da >= base + end and da < base + 0x20000:
            da += delta
        if da != db:
            problems.append('descriptor %d' % i)
    if va[q + 2 + 6 * n:] != vb[q + 2 + 6 * n:]:
        problems.append('bytes after the descriptors')
    # all other blocks
    for x, y in zip(A, B):
        if x.type not in (EXECUTABLE, CODEBLOCK, ENDBLOCK) and x.body != y.body:
            problems.append(x.name)
    if problems:
        print('DIFFERENT: ' + ', '.join(problems[:8]))
        sys.exit(1)
    print('identical except %s (%d bytes at $%X..$%X, Lisa %d)' % (module, end - start, start, end, end - start + delta))


if __name__ == '__main__':
    main()
