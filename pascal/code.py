#!/usr/bin/env python3
"""CLI entry point for the Lisa Pascal MC68000 Code Generator (.I -> .OBJ)."""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from codegen import CodeGenerator  # noqa: E402
from lisalib import LisaRuntime    # noqa: E402


def main(argv: list[str] | None = None, build30: bool | None = None, exe_path: str | None = None) -> int:
    """Run the Lisa Pascal MC68000 code generator pass to translate .I code into a Lisa .OBJ file.

    Selects Workshop 3.0 or 2.0 mode from ``build30``, ``$BUILD``, or leading
    ``--2.0``/``--3.0`` flags, initializes ``LisaRuntime`` for ``PROGCOMM.TEXT`` or prompt
    input, and returns the code generator exit status.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    if build30 is None:
        build30 = os.environ.get('BUILD', '3.0') != '2.0'
    while args and args[0] in ('--2.0', '--3.0'):
        build30 = (args.pop(0) == '--3.0')
    rt = LisaRuntime(args=args, exe_path=exe_path or os.path.abspath(__file__))
    gen = CodeGenerator(rt=rt, build30=build30)
    return gen.run()


if __name__ == '__main__':
    sys.exit(main())
