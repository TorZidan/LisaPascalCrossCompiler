#!/usr/bin/env python3
"""Dump the blocks of any Lisa object file: unlinked modules, unit files,
intrinsic libraries and linked programs.

usage: lisadump.py [-c] FILE.obj      (-c: also show code bytes)
"""
from __future__ import annotations

import struct
import sys

from lisaobj import (
    CODEBLOCK, COMMONDEF, COMMONRELOC, ENDBLOCK, ENTRYPOINT, EOFMARK,
    EXECUTABLE, EXTERNAL, INTERFLOC, MODULENAME, OSDATA, RELOCATION,
    SEGLOCATION, SEGMENTTABLE, SHORTEXTERNAL, STARTADDRESS, STRINGBLOCK,
    UNITBLOCK, UNITLOCATION, UNITTABLE, VERSIONCTRL,
    be16, be32, name8, read_blocks,
)


def dump(path: str, show_code: bool = False) -> None:
    """print a summary of every block in a Lisa object file"""
    data = open(path, 'rb').read()
    for b in read_blocks(data):
        d, t = b.body, b.type
        s = ''
        if t == MODULENAME:
            s = '%-8s seg=%-8r csize=%d' % (name8(d, 0), name8(d, 8), be32(d, 16))
            if len(d) > 20:
                s += ' comments=%r' % d[20:]
        elif t == ENDBLOCK:
            s = 'csize=%d' % be32(d)
        elif t == ENTRYPOINT:
            s = '%-8s %-8s loc=%d' % (name8(d, 0), name8(d, 8), be32(d, 16))
        elif t == EXTERNAL:
            s = '%-8s %-8s refs=%s' % (name8(d, 0), name8(d, 8), [be32(d, i) for i in range(16, len(d), 4)])
        elif t == SHORTEXTERNAL:
            s = '%-8s %-8s refs=%s' % (name8(d, 0), name8(d, 8), [be16(d, i) for i in range(16, len(d), 2)])
        elif t == COMMONRELOC:
            s = '%-8s refs=%s' % (name8(d, 0), [be32(d, i) for i in range(8, len(d), 4)])
        elif t == COMMONDEF:
            s = '%-8s size=%d' % (name8(d, 0), be32(d, 8))
        elif t == RELOCATION:
            s = 'reserved=%d refs=%s' % (be16(d), [be32(d, i) for i in range(2, len(d), 4)])
        elif t == STARTADDRESS:
            s = 'start=%d gsize=%d' % (be32(d, 0), be32(d, 4))
        elif t == CODEBLOCK:
            s = 'addr=$%X  %d bytes' % (be32(d), len(d) - 4)
            if show_code:
                code = d[4:]
                s += ''.join('\n        %04x: %s' % (i, code[i:i + 16].hex(' ', 2)) for i in range(0, len(code), 16))
        elif t == UNITBLOCK:
            s = '%-8s codeaddr=%d textaddr=%d textsize=%d globalsize=%d type=%d' % (
                name8(d, 0), be32(d, 8), be32(d, 12), be32(d, 16), be32(d, 20), be16(d, 24))
        elif t == VERSIONCTRL:
            s = d.hex(' ', 4)
        elif t == UNITTABLE:
            n, mx = be16(d, 0), be16(d, 2)
            s = 'n=%d max=%d' % (n, mx)
            for i in range(n):
                q = 4 + 12 * i
                s += '\n        %-8s unit %3d  type %d' % (name8(d, q), be16(d, q + 8), be16(d, q + 10))
        elif t == SEGMENTTABLE:
            n = be16(d)
            s = 'n=%d' % n
            for i in range(n):
                q = 2 + 18 * i
                s += '\n        %-8s seg %3d  %s %s' % (name8(d, q), be16(d, q + 8), d[q + 10:q + 14].hex(), d[q + 14:q + 18].hex())
        elif t == EXECUTABLE:
            f = struct.unpack_from('>10L', d)
            s = ('JTLaddr=$%X JTSize=%d DataSize=%d MainSize=%d JTSegDelta=%d StkSegDelta=%d\n'
                 '        DynStack=%d MaxStack=%d MinHeap=%d MaxHeap=%d' % f)
            v = d[40:]
            nseg = be16(v)
            s += '\n        %d segments:' % nseg
            q = 2
            for i in range(nseg):
                fa, sp, su, ml = struct.unpack_from('>LHHL', v, q)
                s += '\n          file $%06X packed %5d unpacked %5d mem $%06X' % (fa, sp, su, ml)
                q += 12
            ndesc = be16(v, q)
            q += 2
            s += '\n        %d jump table descriptors:' % ndesc
            for i in range(ndesc):
                op, addr = struct.unpack_from('>HL', v, q)
                s += '\n          %3d  %04X $%06X' % (i, op, addr)
                q += 6
            if q < len(v):
                s += '\n        %d more bytes: %s' % (len(v) - q, v[q:].hex(' ', 2))
        elif t == SEGLOCATION:
            n = be16(d)
            s = 'n=%d' % n
            for i in range(n):
                q = 2 + 28 * i
                num, v1, v2, fnum, loc, sp, su = struct.unpack_from('>HLLHLHH', d, q + 8)
                s += '\n        %-8s seg %3d  file %2d at $%06X  packed %5d unpacked %5d  version %d %d' % (
                    name8(d, q), num, fnum, loc, sp, su, v1, v2)
        elif t == UNITLOCATION:
            n = be16(d)
            s = 'n=%d' % n
            for i in range(n):
                q = 2 + 16 * i
                num, fnum, typ, size = struct.unpack_from('>HBBL', d, q + 8)
                s += '\n        %-8s unit %3d  file %2d  type %d  globals %d' % (name8(d, q), num, fnum, typ, size)
        elif t == INTERFLOC:
            s = ''.join('\n        %-8s at $%06X' % (name8(d, q), be32(d, q + 8)) for q in range(2, len(d) - 11, 12))
        elif t == STRINGBLOCK:
            n = be16(d)
            s = 'n=%d' % n
            for i in range(n):
                fnum, addr = struct.unpack_from('>HL', d, 2 + 6 * i)
                name = data[addr + 1:addr + 1 + data[addr]].decode('latin1') if addr < len(data) else '?'
                s += '\n        file %2d  %s' % (fnum, name)
        elif t == OSDATA:
            s = '%d bytes, %d not zero' % (len(d), sum(1 for x in d if x))
        elif t == EOFMARK:
            s = ''
        else:
            s = d[:32].hex(' ', 2) + (' ...' if len(d) > 32 else '')
        print('%06X %-13s %s' % (b.offset, b.name, s))
    print('file size %d' % len(data))


if __name__ == '__main__':
    args = sys.argv[1:]
    code = '-c' in args
    for f in [a for a in args if a != '-c']:
        dump(f, code)
