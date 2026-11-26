#!/usr/bin/env python3
"""Test harness for the code generator's 68000 disassembler
(pascal/gen_disasm.py, a translation of the original Gen/util/D.TEXT; the
code generator uses it for $ASM+ listings).

    disasmtest.py HEXWORDS...      disassemble one instruction, e.g. 4E56 FFFC
    disasmtest.py -all             all 65536 first words (extension words
                                   0123 4567 89AB CDEF)
    disasmtest.py -file F OFF LEN  disassemble LEN bytes at byte offset OFF of
                                   file F (e.g. an .OBJ code block)

Output: offset (6 hex digits), the instruction's bytes (right-aligned in 20
columns), the opcode (left-aligned in 8 columns) and the operand; with -all:
the first word, the instruction's length, opcode and operand.
"""
from __future__ import annotations

from collections.abc import Sequence
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'pascal'))
from gen_disasm import DisasmMixin  # noqa: E402


class Disassembler(DisasmMixin):
    """Standalone wrapper around DisasmMixin with a no-op symbol lookup for testing 68000 disassembly."""

    def LkUp(self, Lc: int, Dest: int, Name: str) -> str:
        """Return Name unchanged without performing compiler symbol-table substitution."""
        # the code generator's LkUp substitutes names; here: nothing
        return Name


def one(d: Disassembler, buf: bytes | bytearray | memoryview, off: int) -> int:
    """Disassemble and print one 68000 instruction at byte offset off in buf, returning its byte length."""
    n, op, opnd = d.Disassembler(0, buf, off)
    hexbytes = ''.join('%02X' % b for b in buf[off:off + n])
    print('%06X %20s %-8s %s' % (off, hexbytes, op, opnd))
    return n


def main(args: Sequence[str]) -> int:
    """Run the disassembler CLI on hex instruction words, a binary file slice (-file), or all 65536 first words (-all)."""
    d = Disassembler()
    if args[:1] == ['-all']:
        buf = bytearray(512)
        buf[2:10] = bytes.fromhex('0123456789ABCDEF')
        for w in range(65536):
            buf[0], buf[1] = w >> 8, w & 255
            n, op, opnd = d.Disassembler(0, buf, 0)
            print('%04X %d %s %s' % (w, n, op, opnd))
    elif args[:1] == ['-file'] and len(args) == 4:
        off, length = int(args[2]), int(args[3])
        with open(args[1], 'rb') as f:
            f.seek(off)
            data = f.read(length)
        buf = bytearray(data) + bytearray(max(0, 512 - len(data)))
        pos = 0
        while pos < length:
            pos += one(d, buf, pos)
    elif args:
        buf = bytearray(512)
        for i, h in enumerate(args):
            w = int(h, 16)
            buf[2 * i], buf[2 * i + 1] = (w >> 8) & 255, w & 255
        one(d, buf, 0)
    else:
        print(__doc__.strip())
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
