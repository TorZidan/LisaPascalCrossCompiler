"""Read and write Lisa object files (Workshop object file format).

A Lisa object file is a sequence of blocks: 1 type byte, a 3-byte size (of
the whole block, including these 4 bytes), then the fields, big-endian.
The file ends with an EOFMark block ($00) and is padded to 512 bytes.

This module only knows the block layout; the linker (lisalinker.py) gives
the blocks their meaning.  Field layouts follow the ObjIO interface of
ObjIOLib (see ../libs/workshop3.0/OBJIOLIB.md) and the files written by
the Workshop's own compiler and linker.
"""
from __future__ import annotations

import struct

# block types
MODULENAME, ENDBLOCK, ENTRYPOINT, EXTERNAL, STARTADDRESS, CODEBLOCK = 0x80, 0x81, 0x82, 0x83, 0x84, 0x85
RELOCATION, COMMONRELOC, COMMONDEF, SHORTEXTERNAL = 0x86, 0x87, 0x88, 0x89
UNITBLOCK, INTERFLOC = 0x92, 0x93
PHYSICALEXEC = 0x97
EXECUTABLE, VERSIONCTRL, SEGMENTTABLE, UNITTABLE, SEGLOCATION, UNITLOCATION, STRINGBLOCK = \
    0x98, 0x99, 0x9A, 0x9B, 0x9C, 0x9D, 0x9E
PACKEDCODE, PACKTABLE, OSDATA = 0xA0, 0xA1, 0xB2
EOFMARK = 0x00

NAMES = {
    0x80: 'ModuleName', 0x81: 'EndBlock', 0x82: 'EntryPoint', 0x83: 'External',
    0x84: 'StartAddress', 0x85: 'CodeBlock', 0x86: 'Relocation', 0x87: 'CommonReloc',
    0x88: 'CommonDef', 0x89: 'ShortExternal', 0x92: 'UnitBlock', 0x93: 'InterfLoc',
    0x97: 'PhysicalExec', 0x98: 'Executable', 0x99: 'VersionCtrl', 0x9A: 'SegmentTable', 0x9B: 'UnitTable',
    0x9C: 'SegLocation', 0x9D: 'UnitLocation', 0x9E: 'StringBlock', 0xA0: 'PackedCode',
    0xA1: 'PackTable', 0xB2: 'OSData', 0x00: 'EOFMark',
}


def be16(b: bytes | bytearray, o: int = 0) -> int:
    """unsigned 16-bit big-endian integer at offset o"""
    return struct.unpack_from('>H', b, o)[0]


def sbe16(b: bytes | bytearray, o: int = 0) -> int:
    """signed 16-bit big-endian integer at offset o"""
    return struct.unpack_from('>h', b, o)[0]


def be32(b: bytes | bytearray, o: int = 0) -> int:
    """unsigned 32-bit big-endian integer at offset o"""
    return struct.unpack_from('>L', b, o)[0]


def name8(b: bytes | bytearray, o: int = 0) -> str:
    """an 8-character name field, trailing blanks removed"""
    return b[o:o + 8].decode('latin1').rstrip(' ')


def pack_name8(s: str) -> bytes:
    """encode s as an 8-byte blank-padded Latin-1 name field"""
    return s.encode('latin1').ljust(8, b' ')[:8]


class Block:
    """a single block from a Lisa object file: type byte, file offset, and payload"""
    def __init__(self, btype: int, offset: int, body: bytes) -> None:
        self.type = btype           # block type byte
        self.offset = offset        # file offset of the block
        self.body = body            # bytes after the 4-byte header

    @property
    def name(self) -> str:
        """human-readable ObjIO block type name, or hex fallback"""
        return NAMES.get(self.type, '$%02X' % self.type)

    def __repr__(self) -> str:
        return '<%s at $%X, %d bytes>' % (self.name, self.offset, len(self.body))


def read_blocks(data: bytes, start: int = 0) -> list[Block]:
    """the blocks of an object file, up to and including the EOFMark"""
    blocks, p = [], start
    while p + 4 <= len(data):
        t = data[p]
        size = int.from_bytes(data[p + 1:p + 4], 'big')
        if size < 4:
            size = 4
        blocks.append(Block(t, p, data[p + 4:p + size]))
        if t == EOFMARK:
            break
        p += size
    return blocks


def block(btype: int, body: bytes) -> bytes:
    """encode one block"""
    return bytes([btype]) + (4 + len(body)).to_bytes(3, 'big') + body


def pad512(data: bytes) -> bytes:
    """pad data with zero bytes to a multiple of 512 bytes"""
    return data + bytes(-len(data) % 512)
