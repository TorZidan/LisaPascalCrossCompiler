#!/usr/bin/env python3
"""Packed code: the Lisa's code compression (PackedCode blocks, $A0).

    lisapack.py TABLE unpack IN.obj OUT.obj    unpack every PackedCode block
    lisapack.py TABLE pack   IN.obj OUT.obj    pack the code segments of a linked
                                               program (as PACKSEG does)
    lisapack.py TABLE check  IN.obj ...        unpack and pack again each PackedCode
                                               block; it must give the same bytes

TABLE is a PackTable block ($A1; the Lisa keeps it in the file SYSTEM.UNPACK):
header byte, reserved byte, size (2 bytes), version (4 bytes, must be 1), then
256 words.  Words of the code that are in the table are replaced by their
1-byte index.

Packed format (from the Lisa OS unpacker, LISA_OS/OS/source-UNPACK.TEXT, which
reads the block backwards, and Alex Anderson-McLeod's PACKSEG, which writes it,
github.com/alexthecat123/LisaSourceCompilation src/ALEX-PACKSEG.TEXT):
  * the code words are taken in groups of 8; each group is written as its
    items (a 1-byte table index, or the 2 bytes of a word not in the table)
    followed by a flag byte, where bit i (i = 0 for the first word of the
    group) is 1 for an index;
  * the last group may be shorter; then, if the length so far is even, a
    slack byte 0 and the byte 2*i, else the byte 2*i + 1, where i is the bit
    number of the last word: the total length is even.
  The unpacker starts at the last byte: bit 0 says whether a slack byte is
  there, bits 1-3 give the bit number of the last word.

PackedCode block: $A0, size (3 bytes, of the whole block), address (4 bytes),
unpacked code size (4 bytes), packed code.  The unpacked block is a CodeBlock
($85): size, address, code.
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence
import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lisaobj import (
    CODEBLOCK, ENTRYPOINT, EOFMARK, EXECUTABLE, PACKEDCODE, PACKTABLE,
    STARTADDRESS, be16, be32, block, pad512, read_blocks,
)


def read_table(path: str) -> list[int]:
    """read the 256-word PackTable ($A1, version 1) from path"""
    d = open(path, 'rb').read()
    if d[0] != PACKTABLE:
        raise ValueError('%s: not a PackTable block' % path)
    size = be16(d, 2)
    if be32(d, 4) != 1:
        raise ValueError('%s: pack table version %d, not 1' % (path, be32(d, 4)))
    return [be16(d, i) for i in range(8, size, 2)]


def unpack(packed: bytes | bytearray, size: int, table: Sequence[int]) -> bytes:
    """the code of size bytes, from the packed bytes (as UNPACKCODE does,
    from the end backwards)"""
    out = bytearray(size)
    o = size
    i = len(packed) - 1
    last = packed[i]
    i -= 1
    if not last & 1:
        i -= 1                      # the slack byte
    bit = (last >> 1) & 7
    while o > 0:
        flags = packed[i]
        i -= 1
        while bit >= 0 and o > 0:
            if flags >> bit & 1:
                struct.pack_into('>H', out, o - 2, table[packed[i]])
                i -= 1
            else:
                out[o - 2:o] = packed[i - 1:i + 1]
                i -= 2
            o -= 2
            bit -= 1
        bit = 7
    if i != -1:
        raise ValueError('packed code: %d bytes left over' % (i + 1))
    return bytes(out)


def pack(code: bytes | bytearray, table: Sequence[int]) -> bytes:
    """the packed bytes of code (an even number of bytes), as PACKSEG
    does: a word gets the lowest table index 1..255 that holds it (index 0
    is never used)"""
    if len(code) % 2 or not code:
        raise ValueError('code size %d: must be even and not 0' % len(code))
    index = {}
    for j in range(len(table) - 1, 0, -1):
        index[table[j]] = j
    out = bytearray()
    n = len(code) // 2
    for g in range(0, n, 8):
        flags = 0
        for b in range(min(8, n - g)):
            w = be16(code, 2 * (g + b))
            if w in index:
                out.append(index[w])
                flags |= 1 << b
            else:
                out += code[2 * (g + b):2 * (g + b) + 2]
        out.append(flags)
    last_bit = (n - 1) % 8
    if len(out) % 2 == 0:
        out += bytes([0, 2 * last_bit])
    else:
        out.append(2 * last_bit + 1)
    return bytes(out)


def packed_block(addr: int, code: bytes | bytearray, table: Sequence[int]) -> bytes:
    """encode a PackedCode block ($A0) for code loaded at addr"""
    return block(PACKEDCODE, struct.pack('>LL', addr, len(code)) + pack(code, table))


def unpack_block(body: bytes, table: Sequence[int]) -> tuple[int, bytes]:
    """a PackedCode block's body -> (address, code)"""
    addr, size = be32(body, 0), be32(body, 4)
    return addr, unpack(body[8:], size, table)


def pack_program(data: bytes, table: Sequence[int]) -> bytes:
    """pack a linked program as PACKSEG does: each CodeBlock becomes a
    PackedCode block, StartAddress and EntryPoint blocks are dropped, and the
    Executable's segment entries get the PackedCode blocks' file addresses
    and sizes (SizeUnpacked stays: the code size + 8)"""
    out = bytearray()
    exe_at = None
    segs = []                       # (unpacked block size, file address, packed size)
    for b in read_blocks(data):
        if b.type in (STARTADDRESS, ENTRYPOINT):
            continue
        if b.type == EOFMARK:
            break
        if b.type == EXECUTABLE:
            exe_at = len(out)
        if b.type == CODEBLOCK:
            pb = packed_block(be32(b.body), b.body[4:], table)
            segs.append((len(b.body) + 4, len(out), len(pb)))
            out += pb
        else:
            out += data[b.offset:b.offset + 4 + len(b.body)]
    if exe_at is None:
        raise ValueError('not a linked program (no Executable block)')
    v = exe_at + 4 + 40             # the segment table of the Executable
    # a segment without code (SizeUnpacked 8, file address 0) has no CodeBlock
    entries = [v + 2 + 12 * k for k in range(be16(out, v)) if be16(out, v + 2 + 12 * k + 6) != 8]
    if len(entries) != len(segs):
        raise ValueError('%d segments with code in the Executable, %d CodeBlocks' % (len(entries), len(segs)))
    for q, (usize, addr, psize) in zip(entries, segs):
        if be16(out, q + 6) != usize:
            raise ValueError('segment size %d in the Executable, CodeBlock %d' % (be16(out, q + 6), usize))
        struct.pack_into('>LH', out, q, addr, psize)
    out += block(EOFMARK, b'')
    return pad512(bytes(out))


def unpack_program(data: bytes, table: Sequence[int]) -> bytes:
    """the inverse (without the StartAddress block, which is lost)"""
    out = bytearray()
    exe_at = None
    segs = []
    for b in read_blocks(data):
        if b.type == EOFMARK:
            break
        if b.type == EXECUTABLE:
            exe_at = len(out)
        if b.type == PACKEDCODE:
            addr, code = unpack_block(b.body, table)
            segs.append(len(out))
            out += block(CODEBLOCK, struct.pack('>L', addr) + code)
        else:
            out += data[b.offset:b.offset + 4 + len(b.body)]
    if exe_at is not None:
        v = exe_at + 4 + 40
        entries = [v + 2 + 12 * k for k in range(be16(out, v)) if be16(out, v + 2 + 12 * k + 6) != 8]
        for q, addr in zip(entries, segs):
            struct.pack_into('>LH', out, q, addr, 0)
    out += block(EOFMARK, b'')
    return pad512(bytes(out))


def check(table: Sequence[int], paths: Iterable[str]) -> int:
    """verify that every PackedCode block in paths unpacks and repacks to identical bytes"""
    bad = 0
    for path in paths:
        n = same = 0
        for b in read_blocks(open(path, 'rb').read()):
            if b.type == PACKEDCODE:
                n += 1
                addr, code = unpack_block(b.body, table)
                if pack(code, table) == b.body[8:]:
                    same += 1
        print('%-40s %3d PackedCode blocks, %3d pack again to the same bytes' % (path, n, same))
        bad += n - same
    return bad


def main() -> None:
    """CLI entry point for unpacking, packing, or checking Lisa object files"""
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    table = read_table(sys.argv[1])
    cmd = sys.argv[2]
    if cmd == 'check':
        sys.exit(1 if check(table, sys.argv[3:]) else 0)
    data = open(sys.argv[3], 'rb').read()
    if cmd == 'unpack':
        open(sys.argv[4], 'wb').write(unpack_program(data, table))
    elif cmd == 'pack':
        open(sys.argv[4], 'wb').write(pack_program(data, table))
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
