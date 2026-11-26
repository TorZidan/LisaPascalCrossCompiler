#!/usr/bin/env python3
"""Dump the blocks of a Lisa .OBJ file (as written by the code generator).
usage: objdump.py FILE.OBJ"""
from __future__ import annotations

import sys
NAMES = {0x80:'ModuleName',0x81:'EndBlock',0x82:'EntryPoint',0x83:'External',
         0x84:'StartAddress',0x85:'CodeBlock',0x86:'Relocation',0x87:'CommonReloc',
         0x88:'CommonDef',0x89:'ShortExternal',0x92:'UnitBlock',0x00:'EOFMark'}
def be(b: bytes) -> int:
    """Decode a big-endian unsigned integer from byte sequence b."""
    return int.from_bytes(b,'big')
def sbe(b: bytes) -> int:
    """Decode a big-endian signed two's-complement integer from byte sequence b."""
    return int.from_bytes(b,'big',signed=True)
def nm(b: bytes) -> str:
    """Decode a fixed-length Latin-1 symbol or segment name field."""
    return b.decode('latin1')
def dump(path: str) -> None:
    """Read a Lisa Workshop .OBJ file and print each block's offset, type name, and decoded header or hex payload."""
    d=open(path,'rb').read(); p=0
    while p+4<=len(d):
        t=d[p]; size=be(d[p+1:p+4]); b=d[p+4:p+size]
        n=NAMES.get(t,'?%02x'%t)
        if t==0x80: s='%s seg=%r csize=%d'%(nm(b[0:8]),nm(b[8:16]),be(b[16:20]))+(' comments=%r'%b[20:] if len(b)>20 else '')
        elif t==0x81: s='csize=%d'%be(b[0:4])
        elif t==0x82: s='%s %s loc=%d'%(nm(b[0:8]),nm(b[8:16]),be(b[16:20]))
        elif t==0x83: s='%s %s refs=%s'%(nm(b[0:8]),nm(b[8:16]),[be(b[i:i+4]) for i in range(16,len(b),4)])
        elif t==0x89: s='%s %s refs=%s'%(nm(b[0:8]),nm(b[8:16]),[be(b[i:i+2]) for i in range(16,len(b),2)])
        elif t==0x87: s='%s refs=%s'%(nm(b[0:8]),[be(b[i:i+4]) for i in range(8,len(b),4)])
        elif t==0x84: s='start=%d gsize=%d'%(be(b[0:4]),be(b[4:8]))
        elif t==0x85:
            code=b[4:]
            s='addr=%d %d bytes\n'%(be(b[0:4]),len(code))+'\n'.join('      %04x: %s'%(i,' '.join(code[j:j+2].hex() for j in range(i,min(i+16,len(code)),2))) for i in range(0,len(code),16))
        elif t==0x92: s='%s codeaddr=%d textaddr=%d textsize=%d globalsize=%d type=%d'%(nm(b[0:8]),be(b[8:12]),be(b[12:16]),be(b[16:20]),be(b[20:24]),be(b[24:26]))
        elif t==0: print('%06x EOFMark size=%d'%(p,size)); break
        else: s=b.hex()
        print('%06x %-13s %s'%(p,n,s))
        if size<4: break
        p+=size
    print('file size', len(d))
for f in sys.argv[1:]: dump(f)
