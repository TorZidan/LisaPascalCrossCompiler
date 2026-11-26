#!/usr/bin/env python3
"""Reassemble files of a Lisa 400K dc42 image by tag file-id / relative page."""
from __future__ import annotations

import sys, collections
def files(path: str) -> dict[int, tuple[list[tuple[int, int]], bytes]]:
    """Group 512-byte sectors of a 400K DC42 floppy image (84-byte header + 12-byte tags) by tag file_id and reassemble each file in relative-page order."""
    d=open(path,'rb').read()
    n=(len(d)-84)//524
    data=d[84:84+n*512]; tags=d[84+n*512:]
    by=collections.defaultdict(list)
    for b in range(n):
        t=tags[b*12:(b+1)*12]
        fid=int.from_bytes(t[4:6],'big'); rel=int.from_bytes(t[6:8],'big')
        by[fid].append((rel,b))
    out={}
    for fid,l in by.items():
        l.sort()
        out[fid]=(l, b''.join(data[b*512:(b+1)*512] for r,b in l))
    return out
def dectext(b: bytes) -> str:
    """Decode raw Lisa .TEXT page bytes to a Latin-1 string, expanding DLE (0x10) leading-space compression, converting CR to LF, and dropping NUL padding."""
    out=bytearray();i=0
    while i<len(b):
        c=b[i]
        if c==16 and i+1<len(b): out+=b' '*max(0,b[i+1]-32); i+=2; continue
        if c==13: out+=b'\n'
        elif c==0: pass
        else: out.append(c)
        i+=1
    return out.decode('latin1')

if __name__ == '__main__':
    # lisafiles.py IMAGE.dc42            list the files (id, pages)
    # lisafiles.py IMAGE.dc42 ID         print file ID (hex or decimal) as text
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    fs = files(sys.argv[1])
    if len(sys.argv) == 2:
        for fid, (l, raw) in sorted(fs.items()):
            print('id 0x%04x  %4d pages' % (fid, len(l)))
    else:
        fid = int(sys.argv[2], 0)
        sys.stdout.write(dectext(fs[fid][1][1024:]))
