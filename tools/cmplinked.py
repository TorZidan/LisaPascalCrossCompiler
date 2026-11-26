#!/usr/bin/env python3
"""Compare the procedures of an unlinked .OBJ (as written by the code
generator) with the code in a linked Lisa program file.

usage: cmplinked.py OUR.OBJ LINKED.OBJ

For every module (procedure) of OUR.OBJ, its code is searched for in the
code blocks of LINKED.OBJ.  The bytes the linker fills in are skipped:
the 2-byte fields listed in ShortExternal blocks (and the PC-relative
JSR/JMP/PEA/LEA instruction word in front of each, which the linker turns
into a jump-table call or an intrinsic-unit trap), the 4-byte fields listed
in External and CommonReloc blocks (and, for External, the absolute
JMP/JSR/PEA/LEA instruction word in front, which the linker may turn into the
PC-relative form).  A module is reported as
  identical   - found, all other bytes equal
  NOT FOUND   - no exact match; the closest place is shown with the number
                of differing bytes
"""
from __future__ import annotations

from collections.abc import Iterator
import sys

def be(b: bytes) -> int:
    """Decode a big-endian unsigned integer from byte sequence b."""
    return int.from_bytes(b, 'big')

def blocks(d: bytes) -> Iterator[tuple[int, int, bytes]]:
    """Yield (block_type, offset, payload) tuples for each Workshop .OBJ block in d up to EOFMark."""
    p = 0
    while p + 4 <= len(d):
        t = d[p]; sz = be(d[p+1:p+4])
        yield t, p, d[p+4:p+sz]
        if t == 0 or sz < 4: return
        p += sz

def modules(d: bytes) -> Iterator[tuple[str, bytes | None, set[int]]]:
    """yield (name, code, maskset) for each module of an unlinked .OBJ"""
    name, code, mask, short, longr = None, None, set(), [], []
    for t, p, b in blocks(d):
        if t == 0x80:                         # ModuleName
            name, code, mask, short, longr = b[0:8].decode('latin1').strip(), None, set(), [], []
        elif t == 0x89:                       # ShortExternal: 2-byte refs
            for i in range(16, len(b), 2):
                r = be(b[i:i+2]); mask.update((r, r + 1)); short.append(r)
        elif t in (0x83, 0x87):               # External / CommonReloc: 4-byte refs
            start = 16 if t == 0x83 else 8
            for i in range(start, len(b), 4):
                r = be(b[i:i+4]); mask.update(range(r, r + 4))
                if t == 0x83: longr.append(r)
        elif t == 0x85:                       # CodeBlock
            code = b[4:]
            # The linker also rewrites the instruction word in front of a
            # short reference: JSR d(PC) ($4EBA) becomes JSR d(A5) ($4EAD,
            # jump-table call to another segment) or an intrinsic-unit trap
            # ($Axxx, IUJSR); likewise JMP/PEA/LEA d(PC).  Skip that word
            # when it is one of these PC-relative forms in our code.
            # Same for a 4-byte (absolute) reference: the linker turns
            # JMP/JSR/PEA/LEA abs.L ($4EF9, $4EB9, $4879, $41F9..) into the
            # PC-relative form when the target is in the same segment.
            for r in longr:
                if r >= 2:
                    w = be(code[r-2:r])
                    if w in (0x4EF9, 0x4EB9, 0x4879) or (w & 0xF1FF) == 0x41F9:
                        mask.update((r - 2, r - 1))
            # A short reference can also follow JMP/JSR abs.L ($4EF9/$4EB9,
            # e.g. a GOTO to a label of an enclosing procedure): the linker
            # makes it JMP/JSR d(PC) and the last 2 address bytes stay 0.
            for r in short:
                if r >= 2:
                    w = be(code[r-2:r])
                    if w in (0x4EBA, 0x4EFA, 0x487A, 0x4EF9, 0x4EB9) or (w & 0xF1FF) == 0x41FA:
                        mask.update((r - 2, r - 1))
        elif t == 0x81 and name is not None:  # EndBlock
            yield name, code, mask
            name = None

def search(code: bytes, mask: set[int], seg: bytes) -> tuple[int, int]:
    """Find the even byte offset in segment bytes seg minimizing unmasked byte differences against module code, returning (diff_count, offset)."""
    best = (len(code) + 1, -1)
    n = len(code)
    for off in range(0, len(seg) - n + 1, 2):
        diff = 0
        for i in range(n):
            if i not in mask and code[i] != seg[off + i]:
                diff += 1
                if diff >= best[0]: break
        if diff < best[0]:
            best = (diff, off)
            if diff == 0: break
    return best

def main() -> int:
    """Compare every procedure module in an unlinked .OBJ against the code segments of a linked Lisa executable."""
    ours = open(sys.argv[1], 'rb').read()
    linked = open(sys.argv[2], 'rb').read()
    segs = [b[4:] for t, p, b in blocks(linked) if t == 0x85]
    ok = bad = 0
    for name, code, mask in modules(ours):
        found = None
        for si, seg in enumerate(segs):
            diff, off = search(code, mask, seg)
            if found is None or diff < found[0]:
                found = (diff, si, off)
            if diff == 0: break
        diff, si, off = found
        masked = len(mask & set(range(len(code))))
        if diff == 0:
            ok += 1
            print('%-8s %5d bytes identical (segment %d, offset $%04X; %d linker bytes skipped)'
                  % (name, len(code), si, off, masked))
        else:
            bad += 1
            print('%-8s %5d bytes NOT FOUND: closest at segment %d offset $%04X, %d bytes differ'
                  % (name, len(code), si, off, diff))
    print('%d identical, %d not found' % (ok, bad))
    return 1 if bad else 0

if __name__ == '__main__':
    sys.exit(main())
