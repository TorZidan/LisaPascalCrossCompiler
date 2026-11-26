#!/usr/bin/env python3
"""changeseg.py - put all the modules of an object file into one segment, as
the Workshop's CHANGESEG does when it is answered "Y{es, map all segments}"
(BUILD/ASSEMB.TEXT runs it after the Assembler when a segment name is given).

    changeseg.py FILE.OBJ NAME      the segment name of every ModuleName block
                                    becomes NAME (up to 8 characters, as typed)
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'linker'))
from lisaobj import MODULENAME, read_blocks, pack_name8     # noqa: E402


def change_segments(data: bytes, name: str) -> bytes:
    """set the SegmentName field of every ModuleName block in data to name"""
    out = bytearray(data)
    for b in read_blocks(data):
        if b.type == MODULENAME:
            out[b.offset + 12:b.offset + 20] = pack_name8(name[:8])
    return bytes(out)


def main(argv: list[str]) -> None:
    """rewrite all segment names in an object file in place"""
    if len(argv) != 2:
        sys.exit(__doc__)
    path, name = argv
    data = open(path, 'rb').read()
    open(path, 'wb').write(change_segments(data, name))


if __name__ == '__main__':
    main(sys.argv[1:])
