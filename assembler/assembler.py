#!/usr/bin/env python3
"""assembler.py - the Lisa Workshop 68000 Assembler, as the Workshop 3.0
Assembler (ASSEMBLER.OBJ) works: it reads a Lisa
assembly source (.TEXT) and writes an object file (.OBJ) for the Linker,
and optionally a listing.

    assembler.py MYPROG                     MYPROG.TEXT -> MYPROG.OBJ
    assembler.py MYPROG MYPROG.LST OTHER    input, listing file, output file
    assembler.py +P MYPROG MYPROG.LST       options first (+P, -P, +S, +E ...)
    assembler.py                            interactive, as on the Lisa
    printf 'MYPROG\\n\\n\\n' | assembler.py     answers on stdin

The arguments answer the Assembler's prompts in order: Input file, Listing
file (<CR> for none), Output file (default: the input name, with .OBJ).
Missing answers take the default.  An argument that starts with + or - (or
the answer ? to the input prompt) sets options, as on the Lisa:

    +P  Pretty Listing: the listing shows the values of forward references
        (else ****)
    +S  Print Space Avail
    +E  Code patching efficiency check: a warning for each forward branch
        that could have been a short branch

Lisa file names are accepted: .TEXT is added to the input name and .OBJ to
the output name unless given, case is ignored, and a volume prefix such as
-WORK- is dropped.  Source files may be Lisa .TEXT files or host text files.
The opcode table is N68K.OPCODES, the file the Lisa Assembler reads, in this
folder.  The exit status is 1 if there were errors.
"""
from __future__ import annotations

import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asm68k                       # noqa: E402

BANNER = 'ASSEMBLER - MC68000 (Ver 1.0)'
OPTIONS = [('P', 'Pretty Listing                   '),
           ('S', 'Print Space Avail                '),
           ('E', 'Code patching efficiency check   ')]


class Dialog:
    """the prompts; answers come from the arguments (echoed, as the Workshop
    shows them) or from stdin"""
    def __init__(self, args: list[str]) -> None:
        self.args = list(args)
        self.from_args = bool(args)

    def ask(self, prompt: str) -> str:
        """prompt and return the next answer from command-line arguments or stdin"""
        sys.stdout.write(prompt)
        sys.stdout.flush()
        if self.from_args:
            a = self.args.pop(0) if self.args else ''
            print(a)
            return a
        line = sys.stdin.readline()
        if not line:
            print()
            return ''
        a = line.rstrip('\n')
        if not sys.stdin.isatty():
            print(a)
        return a


def print_options(opts: dict[str, bool]) -> None:
    """print the Workshop Assembler option summary table"""
    print('Options:     Meaning                   Current Value.')
    for letter, meaning in OPTIONS:
        print('+%s        %s%s' % (letter, meaning, 'TRUE' if opts[letter] else 'FALSE'))
    print('?         Print options')
    print('<ret>     Accept options')


def set_options(text: str, opts: dict[str, bool]) -> bool:
    """+P -S ... : returns False for a bad option character"""
    t = text.strip()
    i = 0
    while i < len(t):
        if t[i] in '+-' and i + 1 < len(t) and t[i + 1].upper() in opts:
            opts[t[i + 1].upper()] = t[i] == '+'
            i += 2
        elif t[i] in ' ,':
            i += 1
        else:
            print('Bad option character: %s' % t[i])
            return False
    return True


def options_dialog(d: Dialog, opts: dict[str, bool]) -> None:
    """run the interactive 'options :' prompt loop until an empty line is entered"""
    while True:
        a = d.ask('options : ')
        if a.strip() == '':
            return
        if a.strip() == '?':
            print()
            print_options(opts)
            print()
            continue
        set_options(a, opts)


def default_ext(name: str, ext: str) -> str:
    """append ext to name unless it already ends with ext (case-insensitive)"""
    return name if name.upper().endswith(ext.upper()) else name + ext


def stem(name: str) -> str:
    """strip whitespace and any trailing .TEXT extension from name"""
    n = name.strip()
    return n[:-5] if n.upper().endswith('.TEXT') else n


def main(argv: list[str]) -> int:
    """run the Workshop 68000 Assembler CLI dialog, assemble the input, and write the .OBJ and optional listing"""
    opts = {'P': False, 'S': False, 'E': False}
    args = list(argv)
    # leading option arguments (+P -S ...)
    while args and args[0][:1] in '+-' and len(args[0]) > 1 and args[0][1].upper() in opts:
        set_options(args.pop(0), opts)
    print(BANNER)
    print()
    print()
    print_options(opts)
    d = Dialog(args)
    while True:
        name = d.ask('Input file - [.TEXT] ')
        if name.strip() == '?':
            print()
            options_dialog(d, opts)
            continue
        if name.strip() == '':
            return 0
        break
    src = asm68k.source_file(name)
    if src is None:
        print("Can't open '%s' for input." % default_ext(name.strip(), '.TEXT'))
        return 1
    listing = d.ask('Listing file (<CR> for none) - ').strip()
    out = d.ask('Output file - [%s][.OBJ] ' % stem(name)).strip() or stem(name)
    out = default_ext(out, '.OBJ')
    out = asm68k.find_ci(out) or out

    opcodes = asm68k.read_opcodes(os.path.join(HERE, 'N68K.OPCODES'))
    a = asm68k.assemble(src, opcodes, efficiency=opts['E'])
    print()
    for where, lineno, num, msg, line in a.messages:
        print(line.rstrip())
        print('*** Error number %d in line %d of %s: %s' % (num, lineno, where, msg))
    for where, lineno, msg, line in a.warnings:
        print('** short instruction possible: %s, line %d: %s' % (where, lineno, line.strip()))
    if listing:
        lines = a.listing(pretty=opts['P'], title=os.path.basename(src),
                          date=time.strftime('%d-%b-%y'))
        if listing.upper() == '-CONSOLE':
            print('\n'.join(lines))
        else:
            with open(default_ext(listing, '.TEXT') if '.' not in os.path.basename(listing) else listing, 'w') as f:
                f.write('\n'.join(lines) + '\n')
    if opts['S']:
        print('Memory available: plenty')
    if a.messages:
        print()
        print('%6d   Errors' % len(a.messages))
        print('ASSEMBLY ABORTED.')
        return 1
    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    with open(out, 'wb') as f:
        f.write(a.object_file())
    print('  Assembly complete: %6d lines' % a.lines)
    print('%6d   Errors' % 0)
    print('%6d   Warnings' % len(a.warnings))
    print('%s: %d procedures' % (out, len(a.modules)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
