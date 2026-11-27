#!/usr/bin/env python3
"""lpc.py - driver for the Lisa Pascal compiler, like the Workshop "P(ascal" command.

Runs the front end (.TEXT -> .I), chains to the code generator (.I -> .OBJ)
when PROGCOMM.TEXT requests it ($G+, the default in 3.0), and optionally links
with ../linker/lisalinker.py when --link is given.
"""

from __future__ import annotations

import io
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import code as code_cli      # noqa: E402
import pascal as pascal_cli  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    """Drive the two-pass Lisa Pascal compilation pipeline and optional linker step.

    Parses ``--2.0``/``--3.0``, ``--link[=libs]``, and ``--pack`` options, prepends
    ``$G+`` when command-line arguments are supplied without an explicit ``$G`` flag,
    and runs the front end. If ``PROGCOMM.TEXT`` begins with ``'For Code Gen'``,
    chains to the MC68000 code generator with empty stdin and optionally invokes
    ``lisalinker.py`` on the newly written ``.OBJ`` output.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    build30 = True
    link = ''
    pack = False

    while args:
        a = args[0]
        if a == '--2.0':
            build30 = False
            args.pop(0)
        elif a == '--3.0':
            build30 = True
            args.pop(0)
        elif a == '--link':
            link = 'IOSPASLIB'
            args.pop(0)
        elif a.startswith('--link='):
            link = a[len('--link='):]
            args.pop(0)
        elif a == '--pack':
            pack = True
            args.pop(0)
        else:
            break

    if pack and not link:
        print('lpc.py: --pack needs --link')
        return 2

    # The first argument that is not a $ option answers "Input file": it must
    # be a Pascal source. An .OBJ there is a common mistake (trying to link
    # an already compiled program), so say what to run instead.
    source = next((a for a in args if not a.startswith('$')), '')
    if source.upper().endswith('.OBJ'):
        stem = source[:-len('.OBJ')]
        libs = (link or 'IOSPASLIB').replace(',', ' ')
        print(f'lpc.py: {source} is an object file, but lpc.py compiles Pascal source.')
        print('To compile the source and link it in one step:')
        print(f'  python3 {sys.argv[0]} --link={(link or "IOSPASLIB")} {stem}')
        print(f'To link an already compiled {source}, run the linker directly:')
        print(f'  python3 {os.path.relpath(os.path.join(ROOT, "linker", "lisalinker.py"))} -o {stem}.OUT {source} {libs}')
        return 2

    if args:
        has_g = any(a[:2].upper() == '$G' for a in args)
        if not has_g:
            args = ['$G+'] + args

    exe_path = os.path.join(HERE, 'pascal.py')
    rc = pascal_cli.main(args, build30=build30, exe_path=exe_path)
    if rc != 0:
        return rc

    progcomm = 'PROGCOMM.TEXT'
    first_line = ''
    second_line = ''
    if os.path.isfile(progcomm):
        with open(progcomm, 'r', encoding='latin-1') as fp:
            lines = fp.read().splitlines()
            if len(lines) >= 1:
                first_line = lines[0]
            if len(lines) >= 2:
                second_line = lines[1]

    if first_line == 'For Code Gen':
        print()
        code_exe = os.path.join(HERE, 'code.py')
        saved_stdin = sys.stdin
        try:
            sys.stdin = io.StringIO('')
            if not link:
                return code_cli.main([], build30=build30, exe_path=code_exe)
            obj_stem = re.sub(r'\.[iI]$', '', second_line)
            mark_time = time.time() - 0.001
            rc = code_cli.main([], build30=build30, exe_path=code_exe)
        finally:
            sys.stdin = saved_stdin
        if rc != 0:
            return 1

        linker_dir = os.path.join(ROOT, 'linker')
        if linker_dir not in sys.path:
            sys.path.insert(0, linker_dir)
        import lisalinker  # type: ignore

        found = lisalinker.find_ci(obj_stem + '.OBJ') or ''
        if not found or os.path.getmtime(found) < mark_time:
            print(f'lpc.py: the code generator wrote no {obj_stem}.OBJ: not linked')
            return 1
        print()
        print(f"Linking {found} with {link.replace(',', ' ')}")
        link_inputs = [x for x in link.split(',') if x != '']
        cmd = [sys.executable, os.path.join(linker_dir, 'lisalinker.py')]
        if pack:
            cmd.append('-p')
        cmd += ['-o', found, found] + link_inputs
        return subprocess.call(cmd)
    elif link:
        print('lpc.py: the code generator did not run: not linked')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
