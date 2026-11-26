"""The core of the Lisa Workshop 68000 Assembler (assembler.py is the program).

It works as the Workshop 3.0 Assembler does; see
README.md for the rules and how they were found.  In short:

* One pass over the source.  Each instruction gets its form when it is read,
  from what is known at that point; a symbol defined later is a forward
  reference, its field is patched at the end of the procedure.
* The instruction set is the opcode table N68K.OPCODES, the file the Lisa
  Assembler reads: each mnemonic, with or without its size suffix, has an
  opcode word and an operand class.
* Generic instructions get the shortest form for what is known: 0(An) is
  (An); ADD/SUB #1..8 is ADDQ/SUBQ; CMP #n is CMPI; MOVE #0 is CLR; MOVE.L
  #n,Dn with -128..127 is MOVEQ; a branch to a known label in range is short.
* Expressions are evaluated from left to right, without precedence; < and >
  are brackets.  Names have 8 significant characters.
* Each .PROC or .FUNC is a module of the object file: ModuleName, EntryPoint
  records (the procedure and its .DEF names), ShortExternal records (the
  .REF names, with the offsets of their uses, the last one first),
  CodeBlock, EndBlock.  The entries and references come in the order of
  the Lisa Assembler's symbol table (hasher).
"""
from __future__ import annotations

from collections.abc import Iterable
import os
import re
import struct
import sys
from typing import Any, NoReturn

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'linker'))
from lisaobj import (MODULENAME, ENTRYPOINT, SHORTEXTERNAL, CODEBLOCK, ENDBLOCK,   # noqa: E402
                     EOFMARK, block, pack_name8, pad512)


class AsmError(Exception):
    """an error in a source line; num is the Lisa Assembler's error number
    (Workshop User's Guide, Appendix A.1)"""
    def __init__(self, msg: str, num: int | None = None) -> None:
        Exception.__init__(self, msg)
        self.num = num if num is not None else error_number(msg)


# the Lisa Assembler's error numbers for the messages used here
ERROR_NUMBERS = [
    ('undefined', 1), ('out of range', 2), ('too far', 20), ('unknown opcode', 33),
    ('unknown directive', 33), ('operand(s) expected', 27), ('missing operand', 27),
    ('bad expression', 26), ('missing >', 26), ('bad number', 30), ('defined twice', 9),
    ('register list', 53), ('data register', 51), ('address register', 52),
    ('not a label', 21), ('location', 21), ('.ORG backwards', 15), ('include', 37),
    ('macros nested', 34), ('without .IF', 7), ('.EQU', 11), ('external', 8),
    ('immediate', 62), ('needs a number', 24), ('displacement', 2), ('bad operand', 56),
]


def error_number(msg: str) -> int:
    """map an assembler error message to its Lisa Assembler error number (Appendix A.1)"""
    for text, num in ERROR_NUMBERS:
        if text in msg:
            return num
    return 10                           # Improper format


# ---------------------------------------------------------------- opcode table

def read_opcodes(path: str) -> dict[str, tuple[int, int]]:
    """N68K.OPCODES: 12-byte records (after a header record): the mnemonic (8
    characters), the opcode word, the operand class, and a byte not used here"""
    data = open(path, 'rb').read()
    table = {}
    for i in range(12, len(data) - 11, 12):
        r = data[i:i + 12]
        if r[0] == 0:
            break
        name = r[:8].decode('latin1').rstrip()
        table[name] = (struct.unpack('>H', r[8:10])[0], r[10])
    return table


# ---------------------------------------------------------------- source text

def read_text(path: str) -> list[str]:
    """the lines of a source file: a Lisa .TEXT file (a 1024-byte header,
    lines ending in CR, DLE n for n-32 blanks, NULs at the end of each page)
    or a plain host text file"""
    data = open(path, 'rb').read()
    lisa = len(data) >= 1024 and len(data) % 1024 == 0 and b'\n' not in data
    if lisa:
        data = data[1024:]
    out, i = bytearray(), 0
    while i < len(data):
        c = data[i]
        if c == 16 and i + 1 < len(data):
            out += b' ' * max(0, data[i + 1] - 32)
            i += 2
            continue
        if c == 13:
            out += b'\n'
        elif c != 0 or not lisa:
            out.append(c)
        i += 1
    text = out.decode('latin1').replace('\r\n', '\n').replace('\r', '\n')
    lines = text.split('\n')
    if lines and lines[-1] == '':
        lines.pop()
    return lines


def find_ci(path: str) -> str | None:
    """path with each component matched ignoring case, or None"""
    cur = '/' if path.startswith('/') else '.'
    for part in path.split('/'):
        if part in ('', '.'):
            continue
        cand = os.path.join(cur, part)
        if not os.path.exists(cand):
            try:
                match = [e for e in os.listdir(cur) if e.lower() == part.lower()]
            except OSError:
                return None
            if not match:
                return None
            cand = os.path.join(cur, match[0])
        cur = cand
    return os.path.normpath(cur)


def source_file(name: str) -> str | None:
    """the host file of a Lisa file name (.TEXT is added unless given; a
    volume prefix such as -WORK- is dropped)"""
    n = re.sub(r'^-[^-]*-', '', name.strip())
    cands = [n] if n.upper().endswith('.TEXT') else [n + '.TEXT', n]
    for c in cands:
        p = find_ci(c)
        if p and os.path.isfile(p):
            return p
    return None


# ---------------------------------------------------------------- values

class Value:
    """an expression value: a number, a location in a module (rel), a .REF
    name (ext), a string, or not known yet (fwd: a forward reference)"""
    __slots__ = ('n', 'rel', 'ext', 'fwd', 's')

    def __init__(self, n: int = 0, rel: Module | None = None, ext: str | None = None,
                 fwd: bool = False, s: str | None = None) -> None:
        self.n, self.rel, self.ext, self.fwd, self.s = n, rel, ext, fwd, s

    @property
    def absolute(self) -> bool:
        """true if this value is a known constant (not relocatable, external, or forward)"""
        return self.rel is None and self.ext is None and not self.fwd


def to32(n: int) -> int:
    """wrap integer n into signed 32-bit range"""
    n &= 0xFFFFFFFF
    return n - (1 << 32) if n & 0x80000000 else n


class Symbol:
    """symbol table entry: absolute equate ('abs'), procedure-relative label ('rel'), or external ('.REF', 'ext')"""
    __slots__ = ('kind', 'value', 'module')

    def __init__(self, kind: str, value: int, module: Module | None = None) -> None:
        self.kind, self.value, self.module = kind, value, module   # kind: abs, rel, ext


class Module:
    """one assembled .PROC or .FUNC module: its machine code, .DEF/.REF lists, local symbols, and forward patches"""
    def __init__(self, name: str, seg: str, func: bool, nargs: int) -> None:
        self.name, self.seg, self.func, self.nargs = name, seg, func, nargs
        self.code = bytearray()
        self.defs = []             # .DEF names, in order
        self.refs = {}             # .REF name -> [offsets of the address words]
        self.ref_order = []
        self.symbols = {}          # this procedure's labels and equates
        self.patches = []          # (offset, kind, expression, base, line)
        self.linemap = []          # (offset, file, line number, source line): where the code comes from
        self.patch_lines = {}      # patch offset -> its source line, for error messages


# ---------------------------------------------------------------- the assembler

DIRECTIVES = ['PROC', 'FUNC', 'DEF', 'REF', 'SEG', 'MAIN', 'EQU', 'BYTE', 'WORD', 'LONG',
              'ASCII', 'BLOCK', 'ALIGN', 'ORG', 'RORG', 'MACRO', 'ENDM', 'IF', 'ELSE', 'ENDC',
              'INCLUDE', 'LIST', 'NOLIST', 'TITLE', 'PAGE', 'MACROLIST', 'NOMACROLIST',
              'PATCHLIST', 'NOPATCHLIST', 'END']

SIZE_BITS = {'B': 0x00, 'W': 0x40, 'L': 0x80}
# a blank next to one of these does not end the operand field
OPERATOR_CHARS = ',+-*/\\|&^~!=<>#'
CONDITIONS = 'T F HI LS CC CS NE EQ VC VS PL MI GE LT GT LE'.split()


class Assembler:
    """single-pass 68000 assembler matching Workshop 3.0 Assembler Ver 3.5"""
    def __init__(self, opcodes: dict[str, tuple[int, int]]) -> None:
        self.ops = opcodes
        self.regs = {n: v for n, (v, c) in opcodes.items() if c == 0}
        self.special = {n: v for n, (v, c) in opcodes.items() if c == 25}
        self.globals = {}          # symbols defined outside procedures
        self.macros = {}
        self.module = None
        self.modules = []
        self.seg = ''
        self.errors = []
        self.lines = 0
        self.local_scope = 0
        self.ended = False
        self.seen = []             # (module number, event, name): when names are first met
        self.messages = []         # (file, line, error number, message, source line)
        self.warnings = []         # (file, line, message, source line): the +E check
        self.rows = []             # the listing: (module, offset, file, line, source, macro depth)
        self.efficiency = False    # option +E
        self.defining = None       # the macro being defined
        self.cond = [True]         # .IF nesting: is each level assembled
        self.cond_skip = [False]   # inside a level that is not assembled at all
        self.lineno = 0
        self.where = ''

    # ---- errors
    def error(self, msg: str, num: int | None = None) -> None:
        """record a formatted assembler error with file, line number, and Lisa error code"""
        line = getattr(self, 'curline', '')
        num = num if num is not None else error_number(msg)
        self.errors.append('%s, line %d: %s  [%s]' % (self.where, self.lineno, msg, line.strip()[:60]))
        self.messages.append((self.where, self.lineno, num, msg, line))

    # ---- symbols
    def symtab(self) -> dict[str, Symbol]:
        """active symbol table: the current procedure's table if inside one, else the global table"""
        return self.module.symbols if self.module else self.globals

    def lookup(self, name: str) -> Symbol | None:
        """look up symbol name (scoping '@n' local labels), checking current procedure then globals"""
        if name.startswith('@'):
            name = '%s#%d' % (name, self.local_scope)
        if self.module and name in self.module.symbols:
            return self.module.symbols[name]
        return self.globals.get(name)

    def define(self, name: str, sym: Symbol) -> None:
        """define symbol name in the active symbol table, flagging duplicate definitions"""
        self.note('def-' + sym.kind, name)
        if name.startswith('@'):
            name = '%s#%d' % (name, self.local_scope)
        tab = self.symtab()
        old = tab.get(name)
        if old is not None and old.kind != 'ext' and not (old.kind == sym.kind and old.value == sym.value):
            self.error('label %s defined twice' % name)
        tab[name] = sym

    def note(self, event: str, name: str) -> None:
        """record when a symbol is first seen so table_order reproduces LINKERIN's bucket chain order"""
        self.seen.append((len(self.modules) + (self.module is not None), event, name))

    @staticmethod
    def symname(name: str) -> str:
        """normalize a symbol name to uppercase, truncating non-local names to 8 characters"""
        name = name.upper()
        return name if name.startswith('@') else name[:8]

    # ---- expressions
    TOKEN = re.compile(r"""\s*(?:
        (?P<num>\$[0-9A-Fa-f]+|[0-9][0-9A-Fa-f]*[HhOoBb]?\b|[0-9]+)|
        (?P<str>'(?:[^']|'')*'|"(?:[^"]|"")*")|
        (?P<id>[A-Za-z_%@.][A-Za-z0-9_%@.$]*)|
        (?P<op><>|[-+*/\\|&^~!=<>(),*#]))""", re.X)

    def tokens(self, text: str) -> list[tuple[str, str]]:
        """tokenize an expression string into (kind, token) pairs"""
        out, pos = [], 0
        text = text.strip()
        while pos < len(text):
            m = self.TOKEN.match(text, pos)
            if not m or m.end() == pos:
                raise AsmError('bad expression: %s' % text)
            pos = m.end()
            kind = m.lastgroup
            out.append((kind, m.group(kind)))
        return out

    def expr(self, text: str, allow_fwd: bool = True) -> Value:
        """evaluate an expression"""
        self._toks, self._i = self.tokens(text), 0
        v = self._expr(allow_fwd)
        if self._i != len(self._toks):
            raise AsmError('bad expression: %s' % text)
        return v

    def _peek(self) -> tuple[str | None, str | None]:
        return self._toks[self._i] if self._i < len(self._toks) else (None, None)

    def _expr(self, allow_fwd: bool) -> Value:
        """evaluate a binary expression strictly left-to-right without operator precedence"""
        v = self._term(allow_fwd)
        while True:
            kind, tok = self._peek()
            if kind != 'op' or tok not in ('+', '-', '*', '/', '\\', '|', '&', '^', '!', '=', '<>'):
                return v
            self._i += 1
            w = self._term(allow_fwd)
            v = self.binop(tok, v, w)

    def _term(self, allow_fwd: bool) -> Value:
        """evaluate a unary operator, '<...>' bracketed subexpression, '*', literal, or symbol"""
        kind, tok = self._peek()
        self._i += 1
        if kind == 'op' and tok == '-':
            w = self._term(allow_fwd)
            return self.binop('-', Value(0), w)
        if kind == 'op' and tok == '+':
            return self._term(allow_fwd)
        if kind == 'op' and tok == '~':
            w = self._term(allow_fwd)
            if not w.absolute:
                return Value(fwd=True) if w.fwd else self._bad()
            return Value(to32(~w.n))
        if kind == 'op' and tok == '<':
            v = self._expr(allow_fwd)
            k2, t2 = self._peek()
            if t2 != '>':
                raise AsmError('missing >')
            self._i += 1
            return v
        if kind == 'op' and tok == '*':
            if not self.module:
                raise AsmError('* outside a procedure')
            return Value(self.pc, rel=self.module)
        if kind == 'num':
            return Value(self.number(tok))
        if kind == 'str':
            s = tok[1:-1].replace(tok[0] * 2, tok[0])
            n = 0
            for ch in s[:4]:
                n = (n << 8) | ord(ch)
            return Value(to32(n), s=s)
        if kind == 'id':
            name = self.symname(tok)
            self.note('use', name)
            sym = self.lookup(name)
            if sym is None:
                if not allow_fwd:
                    raise AsmError('undefined symbol %s' % tok)
                return Value(fwd=True)
            if sym.kind == 'abs':
                return Value(sym.value)
            if sym.kind == 'rel':
                return Value(sym.value, rel=sym.module)
            if sym.kind == 'ext':
                return Value(0, ext=name)
        raise AsmError('bad expression')

    def _bad(self) -> NoReturn:
        raise AsmError('bad expression')

    @staticmethod
    def number(tok: str) -> int:
        """parse a decimal, '$hex', 'nnnH', 'nnnO' octal, or 'nnnB' binary literal"""
        t = tok.upper()
        if t.startswith('$'):
            return to32(int(t[1:], 16))
        if t.endswith('H'):
            return to32(int(t[:-1], 16))
        if t.endswith('O') and re.fullmatch(r'[0-7]+O', t):
            return int(t[:-1], 8)
        if t.endswith('B') and re.fullmatch(r'[01]+B', t):
            return int(t[:-1], 2)
        if re.fullmatch(r'[0-9]+', t):
            return to32(int(t))
        raise AsmError('bad number %s' % tok)

    def binop(self, op: str, a: Value, b: Value) -> Value:
        """apply binary operator op to Value operands a and b"""
        if a.fwd or b.fwd:
            return Value(fwd=True)
        if op in ('=', '<>'):
            if a.s is not None and b.s is not None:
                eq = a.s.upper() == b.s.upper()
            else:
                eq = (a.n, a.rel, a.ext) == (b.n, b.rel, b.ext)
            return Value(int(eq if op == '=' else not eq))
        if op == '+':
            if a.ext or b.ext:
                if a.ext and b.absolute:
                    return Value(a.n + b.n, ext=a.ext)
                if b.ext and a.absolute:
                    return Value(a.n + b.n, ext=b.ext)
                raise AsmError('bad use of an external name')
            if a.rel and b.rel:
                raise AsmError('cannot add two locations')
            return Value(to32(a.n + b.n), rel=a.rel or b.rel)
        if op == '-':
            if a.ext or b.ext:
                if a.ext and b.absolute:
                    return Value(a.n - b.n, ext=a.ext)
                raise AsmError('bad use of an external name')
            if a.rel and b.rel:
                if a.rel is not b.rel:
                    raise AsmError('locations in different procedures')
                return Value(to32(a.n - b.n))
            if b.rel:
                raise AsmError('cannot subtract a location from a number')
            return Value(to32(a.n - b.n), rel=a.rel)
        if not (a.absolute and b.absolute):
            raise AsmError('operator %s needs numbers' % op)
        x, y = a.n, b.n
        if op == '*':
            return Value(to32(x * y))
        if op == '/':
            if y == 0:
                raise AsmError('division by zero')
            q = abs(x) // abs(y)
            return Value(q if (x < 0) == (y < 0) else -q)
        if op == '\\':
            if y == 0:
                raise AsmError('division by zero')
            r = abs(x) % abs(y)
            return Value(r if x >= 0 else -r)
        if op in ('|', '!'):
            return Value(to32(x | y))
        if op == '&':
            return Value(to32(x & y))
        if op == '^':
            return Value(to32(x ^ y))
        raise AsmError('bad operator %s' % op)

    # ---- operands
    @staticmethod
    def split_operands(text: str) -> list[str]:
        """split at top-level commas (not inside quotes, ( ) or < >)"""
        out, cur, depth, q = [], '', 0, None
        for ch in text:
            if q:
                cur += ch
                if ch == q:
                    q = None
                continue
            if ch in '\'"':
                q = ch
            elif ch in '(':
                depth += 1
            elif ch in ')':
                depth -= 1
            elif ch == ',' and depth == 0:
                out.append(cur)
                cur = ''
                continue
            cur += ch
        out.append(cur)
        return [o.strip() for o in out]

    def reg(self, text: str) -> int | None:
        """a register number 0-15 (D0-D7, A0-A7), or None"""
        r = self.regs.get(text.upper())
        if r is None or r > 15:
            return None
        return r

    def index_reg(self, text: str) -> tuple[int, bool]:
        """an index register: (number 0-15, long)"""
        r = self.regs.get(text.upper())
        if r is None:
            raise AsmError('bad index register %s' % text)
        return r & 15, bool(r & 16)

    def ea(self, text: str) -> dict[str, Any]:
        """parse an effective address: a dict with mode, reg, and its
        extension: ('imm', Value), ('d16', Value), ('d8x', Value, xreg, long),
        ('abs', Value), ('pc16', Value), ('pc8x', Value, xreg, long)"""
        t = text.strip()
        u = t.upper()
        if not t:
            raise AsmError('missing operand')
        if t.startswith('#'):
            return {'mode': 7, 'reg': 4, 'ext': ('imm', self.expr(t[1:])), 'etext': t[1:]}
        r = self.reg(t)
        if r is not None:
            return {'mode': 1 if r >= 8 else 0, 'reg': r & 7, 'ext': None, 'r': r}
        if u in self.special:
            return {'mode': 'special', 'reg': self.special[u], 'ext': None, 'name': u}
        m = re.fullmatch(r'-\(\s*([^)]*?)\s*\)', t)
        if m and self.reg(m.group(1)) is not None and self.reg(m.group(1)) >= 8:
            return {'mode': 4, 'reg': self.reg(m.group(1)) & 7, 'ext': None}
        m = re.fullmatch(r'\(\s*([^),]*?)\s*\)(\+?)', t)
        if m and self.reg(m.group(1)) is not None and self.reg(m.group(1)) >= 8:
            return {'mode': 3 if m.group(2) else 2, 'reg': self.reg(m.group(1)) & 7, 'ext': None}
        if t.endswith(')') and '(' in t:
            # disp(An) disp(An,Xi) disp(PC) disp(PC,Xi), disp may be empty
            depth, k = 0, len(t) - 1
            while k >= 0:
                if t[k] == ')':
                    depth += 1
                elif t[k] == '(':
                    depth -= 1
                    if depth == 0:
                        break
                k -= 1
            disp_text, inner = t[:k].strip(), [x.strip() for x in t[k + 1:-1].split(',')]
            base = inner[0].upper()
            disp = self.expr(disp_text) if disp_text else Value(0)
            if base == 'PC':
                if len(inner) == 1:
                    return {'mode': 7, 'reg': 2, 'ext': ('pc16', disp), 'etext': disp_text}
                xr, xl = self.index_reg(inner[1])
                return {'mode': 7, 'reg': 3, 'ext': ('pc8x', disp, xr, xl), 'etext': disp_text}
            b = self.reg(base)
            if b is not None and b < 8 and len(inner) == 1:
                # label(Dn) is label(PC,Dn)
                xr, xl = self.index_reg(inner[0])
                return {'mode': 7, 'reg': 3, 'ext': ('pc8x', disp, xr, xl), 'etext': disp_text}
            if b is not None and b >= 8:
                if len(inner) == 1:
                    if disp.absolute and disp.n == 0:
                        return {'mode': 2, 'reg': b & 7, 'ext': None}       # 0(An) is (An)
                    return {'mode': 5, 'reg': b & 7, 'ext': ('d16', disp), 'etext': disp_text}
                xr, xl = self.index_reg(inner[1])
                return {'mode': 6, 'reg': b & 7, 'ext': ('d8x', disp, xr, xl), 'etext': disp_text}
            raise AsmError('bad operand %s' % t)
        v = self.expr(t)
        if v.ext:
            return {'mode': 7, 'reg': 0, 'ext': ('ext', v), 'etext': t}
        if v.rel or v.fwd:
            return {'mode': 7, 'reg': 2, 'ext': ('pc16', v), 'etext': t}
        if -32768 <= v.n <= 32767:
            return {'mode': 7, 'reg': 0, 'ext': ('abs', v), 'etext': t}
        return {'mode': 7, 'reg': 1, 'ext': ('abs', v), 'etext': t}

    # ---- code output
    @property
    def pc(self) -> int:
        """current byte offset in the active procedure's code buffer"""
        return len(self.module.code)

    def emit16(self, w: int) -> None:
        """append a big-endian 16-bit word to the current module's code"""
        self.module.code += struct.pack('>H', w & 0xFFFF)

    def emit32(self, w: int) -> None:
        """append a big-endian 32-bit longword to the current module's code"""
        self.module.code += struct.pack('>L', w & 0xFFFFFFFF)

    def patch(self, kind: str, text_or_value: str | None, base: int | None = None,
              off: int | None = None) -> None:
        """a field whose value is not known yet: reserve it (unless off is
        given: a field already emitted), fill it in at the end of the
        procedure"""
        size = {'pc16': 2, 'pc8': 1, 'x8': 1, 'w': 2, 'l': 4, 'b': 1}[kind]
        reserve = off is None
        if reserve:
            off = self.pc
        self.module.patches.append((off, kind, text_or_value, base, self.where, self.lineno, self.local_scope))
        self.module.patch_lines[off] = getattr(self, 'curline', '')
        if reserve:
            self.module.code += bytes(size)

    def emit_ext(self, ea: dict[str, Any], size: str) -> None:
        """the extension words of an effective address"""
        ext = ea['ext']
        if ext is None:
            return
        kind = ext[0]
        v = ext[1]
        if kind == 'imm':
            if v.ext:
                raise AsmError('immediate external name')
            if v.fwd or v.rel:
                self.patch('l' if size == 'L' else 'w', ea.get('etext'))
                return
            if size == 'L':
                self.emit32(v.n)
            else:
                self.emit16(v.n)          # a byte immediate too: the low word of the value
        elif kind == 'd16':
            if v.fwd:
                self.patch('w', ea.get('etext'))
            elif not v.absolute:
                raise AsmError('displacement must be a number')
            else:
                self.emit16(v.n)
        elif kind == 'd8x':
            xr, xl = ext[2], ext[3]
            if not v.absolute:
                raise AsmError('displacement must be a number')
            self.emit16((xr << 12) | (0x800 if xl else 0) | (v.n & 0xFF))
        elif kind == 'abs':
            if ea['reg'] == 1:
                self.emit32(v.n)
            else:
                self.emit16(v.n)
        elif kind == 'ext':
            self.ref(v.ext)
            self.emit16(v.n)
        elif kind == 'pc16':
            base = self.pc
            if v.fwd:
                self.patch('pc16', ea.get('etext'), base)
            elif v.rel is self.module:
                self.emit16(v.n - base)
            elif v.absolute:
                self.emit16(v.n)
            else:
                raise AsmError('location in another procedure')
        elif kind == 'pc8x':
            base = self.pc
            xr, xl = ext[2], ext[3]
            if v.fwd:
                self.emit16((xr << 12) | (0x800 if xl else 0))
                self.patch('x8', ea.get('etext'), base, off=base + 1)
                return
            if v.rel is not self.module:
                raise AsmError('bad PC-relative operand')
            d = v.n - base
            if not -128 <= d <= 127:
                raise AsmError('indexed displacement out of range')
            self.emit16((xr << 12) | (0x800 if xl else 0) | (d & 0xFF))

    def ref(self, name: str) -> None:
        """record a ShortExternal reference to .REF symbol name at the current PC"""
        m = self.module
        if name not in m.refs:
            m.refs[name] = []
            m.ref_order.append(name)
        m.refs[name].append(self.pc)

    # ---- statements
    def assemble_file(self, path: str) -> None:
        """read and assemble the top-level source file at path and finalize any open procedure"""
        self.where = os.path.basename(path)
        self.read(path, top=True)
        self.end_module()

    def read(self, path: str, top: bool = False) -> None:
        """read lines from source or .INCLUDE file path and process them"""
        lines = read_text(path)
        where, lineno = self.where, getattr(self, 'lineno', 0)
        self.where = os.path.basename(path)
        self.process(lines)
        self.where, self.lineno = where, lineno

    def process(self, lines: list[str], macro_depth: int = 0) -> None:
        """assemble a sequence of source or macro-expanded lines"""
        for k, line in enumerate(lines):
            if self.ended:
                return
            if macro_depth == 0:
                self.lineno = k + 1
                self.lines += 1
            try:
                self.statement(line, macro_depth)
            except AsmError as e:
                self.error(str(e), e.num)

    def split_line(self, line: str) -> tuple[str | None, str, str]:
        """label, opcode, operand field.  A label starts in column 1 (or is
        an @ label).  The operand field ends at a blank outside quotes,
        except a blank next to a comma or before a parenthesis: comments
        need no semicolon, but operands may have blanks around their parts
        (MOVE.L  atld (A6), A0)."""
        line = line.replace('\t', ' ')
        label = None
        rest = line
        if line and line[0] not in ' ;' and not line.startswith('.'):
            m = re.match(r'([^\s:;]+):?', line)
            label = m.group(1)
            rest = line[m.end():]
        rest = rest.strip()
        if label is None and rest.startswith('@'):
            m = re.match(r'(@[0-9]+):?', rest)
            if m:
                label = m.group(1)
                rest = rest[m.end():].strip()
        if rest.startswith(';') or not rest:
            return label, '', ''
        m = re.match(r'([^\s;]+)', rest)
        op = m.group(1)
        rest = rest[m.end():].lstrip()
        operand, q, i = '', None, 0
        while i < len(rest):
            ch = rest[i]
            if q:
                operand += ch
                if ch == q:
                    q = None
                i += 1
                continue
            if ch == ';':
                break
            if ch == ' ':
                j = i
                while j < len(rest) and rest[j] == ' ':
                    j += 1
                nxt = rest[j] if j < len(rest) else ''
                prev = operand[-1:] if operand else ''
                if prev and nxt and (prev in OPERATOR_CHARS or nxt in OPERATOR_CHARS or
                                     (nxt == '(' and re.match(r'\(\s*([AD][0-7]|SP|PC)\b', rest[j:], re.I))):
                    i = j
                    continue
                break
            if ch in '\'"':
                q = ch
            operand += ch
            i += 1
        return label, op, operand

    def statement(self, line: str, depth: int) -> None:
        """parse and execute one source line (macro body capture, conditional, directive, macro call, or instruction)"""
        self.curline = line
        m = self.module
        self.rows.append((m, len(m.code) if m else None, self.where, self.lineno, line, depth))
        if m is not None and self.defining is None:
            m.linemap.append((len(m.code), self.where, self.lineno, line))
        # inside a macro definition: collect the lines
        if self.defining is not None:
            label, op, operand = self.split_line(line)
            if self.directive(op) == 'ENDM':
                self.defining = None
            else:
                self.macros[self.defining].append(line)
            return
        label, op, operand = self.split_line(line)
        d = self.directive(op)
        # conditional assembly
        if d in ('IF', 'ELSE', 'ENDC'):
            self.conditional(d, operand)
            return
        if not all(self.cond):
            return
        if d == 'MACRO':
            name = (operand or label or '').upper()[:8]
            if not name:
                raise AsmError('macro without a name')
            self.macros[name] = []
            self.defining = name
            return
        if d == 'EQU':
            if not label:
                raise AsmError('.EQU without a label')
            v = self.expr(operand)
            if v.fwd:
                raise AsmError('.EQU of an undefined symbol')
            name = self.symname(label)
            if v.rel:
                self.define(name, Symbol('rel', v.n, v.rel))
            else:
                self.define(name, Symbol('abs', v.n))
            return
        if label:
            self.label(label)
        if not op:
            return
        if d:
            self.do_directive(d, operand, label)
            return
        name = op.upper()
        if name[:8] in self.macros and '.' not in name:
            self.expand(name[:8], operand, depth)
            return
        if name in self.macros:
            self.expand(name, operand, depth)
            return
        if self.module is None:
            raise AsmError('instruction outside a procedure: %s' % op)
        self.instruction(name, operand)

    def label(self, text: str) -> None:
        """define a procedure-relative label at the current PC and advance local '@' scope if non-local"""
        name = self.symname(text)
        if not name.startswith('@'):
            self.local_scope += 1
        if self.module is None:
            raise AsmError('label outside a procedure: %s' % text)
        self.define(name, Symbol('rel', self.pc, self.module))

    def directive(self, op: str) -> str | None:
        """return the canonical directive name for op (dot-prefixed or opcode-table class 21), or None"""
        if not op:
            return None
        u = op.upper()
        if u.startswith('.'):
            key = u[1:9]
            for d in DIRECTIVES:
                if d[:8] == key:
                    return d
            raise AsmError('unknown directive %s' % op)
        e = self.ops.get(u)
        if e and e[1] == 21 and e[0] < 0x100 and u in ('EQU', 'END', 'ORG', 'RORG', 'PAGE', 'LIST',
                                                         'NOL', 'NOLIST', 'ENDC', 'MACRO', 'ENDM'):
            return {'NOL': 'NOLIST'}.get(u, u)
        return None

    def conditional(self, d: str, operand: str) -> None:
        """handle .IF, .ELSE, and .ENDC conditional assembly directives"""
        if d == 'IF':
            if not all(self.cond):
                self.cond.append(False)
                self.cond_skip.append(True)
                return
            v = self.expr(operand, allow_fwd=False)
            self.cond.append(v.n != 0 if v.s is None or len(v.s) <= 4 else True)
            self.cond_skip.append(False)
        elif d == 'ELSE':
            if len(self.cond) <= 1:
                raise AsmError('.ELSE without .IF')
            if not self.cond_skip[-1]:
                self.cond[-1] = not self.cond[-1]
        else:
            if len(self.cond) <= 1:
                raise AsmError('.ENDC without .IF')
            self.cond.pop()
            self.cond_skip.pop()

    def expand(self, name: str, operand: str, depth: int) -> None:
        """expand macro name, substituting %1..%9 with comma-separated operands"""
        if depth >= 5:
            raise AsmError('macros nested too deeply')
        args = self.split_operands(operand) if operand else []

        def sub(m: re.Match[str]) -> str:
            n = int(m.group(1))
            return args[n - 1] if 0 < n <= len(args) else ''
        body = [re.sub(r'%(\d)', sub, line) for line in self.macros[name]]
        self.process(body, depth + 1)

    # ---- directives
    def do_directive(self, d: str, operand: str, label: str | None) -> None:
        """execute an assembler directive (.PROC/.FUNC, .DEF, .REF, .SEG, data emission, .ALIGN, .ORG, .INCLUDE, .END)"""
        if d in ('PROC', 'FUNC'):
            parts = self.split_operands(operand)
            name = self.symname(parts[0])
            nargs = self.expr(parts[1]).n if len(parts) > 1 and parts[1] else 0
            self.end_module()
            self.module = Module(name, self.seg, d == 'FUNC', nargs)
            self.note('proc', name)
            self.module.symbols[name] = Symbol('rel', 0, self.module)     # the procedure's own name
            self.local_scope += 1
        elif d == 'DEF':
            if self.module is None:
                raise AsmError('.DEF outside a procedure')
            for n in self.split_operands(operand):
                self.module.defs.append(self.symname(n))
                self.note('dotdef', self.symname(n))
        elif d == 'REF':
            for n in self.split_operands(operand):
                name = self.symname(n)
                self.note('ref', name)
                self.symtab()[name] = Symbol('ext', 0)
        elif d == 'SEG':
            s = operand.strip()
            if s[:1] in '\'"':
                s = s[1:-1]
            self.seg = s[:8]
        elif d in ('BYTE', 'WORD', 'LONG'):
            for t in self.split_operands(operand):
                v = self.expr(t)
                if d == 'BYTE':
                    if not v.absolute:
                        raise AsmError('.BYTE needs a number')
                    self.module.code.append(v.n & 0xFF)
                elif d == 'WORD':
                    if v.fwd or v.rel:
                        self.patch('w', t)
                    elif v.ext:
                        self.ref(v.ext)
                        self.emit16(0)
                    else:
                        self.emit16(v.n)
                else:
                    if v.fwd or v.rel:
                        self.patch('l', t)
                    else:
                        self.emit32(v.n)
        elif d == 'ASCII':
            s = operand.strip()
            if len(s) < 2 or s[0] not in '\'"' or s[-1] != s[0]:
                raise AsmError('.ASCII needs a string')
            self.module.code += s[1:-1].encode('latin1')
        elif d == 'BLOCK':
            parts = self.split_operands(operand)
            n = self.expr(parts[0], allow_fwd=False).n
            fill = self.expr(parts[1], allow_fwd=False).n & 0xFF if len(parts) > 1 else 0
            self.module.code += bytes([fill]) * n
        elif d == 'ALIGN':
            n = self.expr(operand, allow_fwd=False).n
            while n > 1 and self.pc % n:
                self.module.code.append(0)
        elif d in ('ORG', 'RORG'):
            n = self.expr(operand, allow_fwd=False).n
            if n < self.pc:
                raise AsmError('.ORG backwards')
            self.module.code += bytes(n - self.pc)
        elif d == 'INCLUDE':
            p = source_file(operand)
            if p is None:
                raise AsmError('cannot open include file %s' % operand)
            self.read(p)
        elif d == 'END':
            self.ended = True
        elif d == 'MAIN':
            pass
        # listing directives: LIST NOLIST TITLE PAGE MACROLIST NOMACROLIST
        # PATCHLIST NOPATCHLIST, and ENDM without MACRO

    # ---- end of a procedure: patches, then the module is complete
    def end_module(self) -> None:
        """resolve forward patches, pad code to an even byte length, validate .DEF labels, and close the current module"""
        m = self.module
        if m is None:
            return
        saved = self.local_scope
        for off, kind, what, base, where, lineno, scope in m.patches:
            self.where, self.lineno, self.local_scope = where, lineno, scope
            self.curline = m.patch_lines.get(off, '')
            try:
                v = self.expr(what, allow_fwd=False)
                if kind == 'pc16':
                    if v.rel is not m:
                        raise AsmError('not a location in this procedure: %s' % what)
                    struct.pack_into('>h', m.code, off, check16(v.n - base))
                    d = v.n - base
                    if self.efficiency and -128 <= d <= 127 and d != 0 and base == off:
                        self.warnings.append((where, lineno, 'short instruction possible', self.source_at(m, off)))
                elif kind == 'pc8':
                    d = v.n - base
                    if v.rel is not m or not -128 <= d <= 127:
                        raise AsmError('short branch out of range: %s' % what)
                    if d == 0:
                        struct.pack_into('>H', m.code, off - 1, 0x4E71)     # to the next instruction: NOP
                    else:
                        m.code[off] = d & 0xFF
                elif kind == 'x8':
                    d = v.n - base
                    if v.rel is not m or not -128 <= d <= 127:
                        raise AsmError('indexed displacement out of range: %s' % what)
                    m.code[off] = d & 0xFF
                elif kind == 'w':
                    struct.pack_into('>H', m.code, off, v.n & 0xFFFF)
                elif kind == 'l':
                    struct.pack_into('>L', m.code, off, v.n & 0xFFFFFFFF)
            except AsmError as e:
                self.error(str(e))
        self.local_scope = saved
        if len(m.code) % 2:
            m.code.append(0)                      # a procedure has an even length
        for name in m.defs:
            sym = m.symbols.get(name)
            if sym is None or sym.kind != 'rel':
                self.error('.DEF %s: not a label of %s' % (name, m.name))
        self.modules.append(m)
        self.module = None

    def source_at(self, m: Module, off: int) -> str:
        """return the source line corresponding to code offset off in module m"""
        line = ''
        for o, f, n, l in m.linemap:
            if o <= off:
                line = l
        return line

    # ---- listing
    def listing(self, pretty: bool = False, title: str = '', date: str = '') -> list[str]:
        """the listing: location, code and source line.  The fields that
        were patched (forward references) are shown as **** unless pretty
        (option +P), which shows their values"""
        out, page, n = [], 0, 0
        ends = {}
        nxt = {}
        for i, (m, off, f, ln, src, depth) in enumerate(self.rows):
            if m is not None:
                nxt.setdefault(id(m), []).append(i)
        for k, idx in nxt.items():
            for a, b in zip(idx, idx[1:] + [None]):
                ends[a] = self.rows[b][1] if b is not None else len(self.rows[a][0].code)
        patched = {}
        for m in self.modules:
            for off, kind, what, base, where, lineno, scope in m.patches:
                size = {'pc16': 2, 'pc8': 1, 'x8': 1, 'w': 2, 'l': 4, 'b': 1}[kind]
                for k in range(size):
                    patched[(id(m), off + k)] = True

        def header() -> list[str]:
            return ['', '%sPAGE - %d  FILE: %s' % ('MC68000 Assembley Pretty Listing  (Ver 3.5)        ' + date + '  '
                                                  if pretty else '', page, title), '']
        for i, (m, off, f, ln, src, depth) in enumerate(self.rows):
            if n % 60 == 0:
                page += 1
                out += header()
            n += 1
            mark = '#' if depth else ' '
            if m is None:
                out.append('       %-21s%s %s' % ('', mark, src))
                continue
            end = ends.get(i, off)
            code = m.code[off:end]
            hexes = []
            for k in range(0, len(code), 2):
                pair = ''
                for j in range(k, min(k + 2, len(code))):
                    pair += '**' if (not pretty and patched.get((id(m), off + j))) else '%02X' % code[j]
                hexes.append(pair)
            first = ' '.join(hexes[:3])
            out.append('%05X| %-20s %s %s' % (off, first, mark, src))
            for k in range(3, len(hexes), 3):
                out.append('%05X| %-20s' % (off + 2 * k, ' '.join(hexes[k:k + 3])))
        return out

    # ---- instructions
    def instruction(self, name: str, operand: str) -> None:
        """look up mnemonic name in N68K.OPCODES and dispatch to its operand-class encoder"""
        ops = self.split_operands(operand) if operand else []
        size = None
        base = name
        if '.' in name:
            base, suffix = name.rsplit('.', 1)
            if suffix in ('B', 'W', 'L', 'S'):
                size = suffix
        entry = self.ops.get(name)
        if entry is None:
            raise AsmError('unknown opcode %s' % name)
        opcode, cls = entry
        handler = getattr(self, 'class%d' % cls, None)
        if handler is None:
            raise AsmError('opcode %s not supported (class %d)' % (name, cls))
        self.inst_start = self.pc
        handler(base, opcode, size or 'W', ops, name)

    @staticmethod
    def imm_value(ea: dict[str, Any]) -> int | None:
        """the value of a known immediate operand, else None"""
        if ea['mode'] == 7 and ea['reg'] == 4 and ea['ext'][1].absolute:
            return ea['ext'][1].n
        return None

    def need(self, ops: list[str], n: int) -> None:
        """require exactly n operands, raising AsmError otherwise"""
        if len(ops) != n:
            raise AsmError('%d operand(s) expected' % n)

    def opword(self, w: int) -> None:
        """emit the 16-bit 68000 instruction opcode word"""
        self.emit16(w)

    def eabits(self, ea: dict[str, Any]) -> int:
        """return the 6-bit (mode << 3 | reg) effective-address field, rejecting special registers"""
        if ea['mode'] == 'special':
            raise AsmError('bad use of %s' % ea['name'])
        return (ea['mode'] << 3) | ea['reg']

    # class 2: ABCD ADDX SBCD SUBX  Dy,Dx  or  -(Ay),-(Ax)
    def class2(self, base: str, op: int, size: str, ops: list[str], name: str) -> None:
        """encode class 2: ABCD, ADDX, SBCD, SUBX (Dy,Dx or -(Ay),-(Ax))"""
        self.need(ops, 2)
        s, d = self.ea(ops[0]), self.ea(ops[1])
        if s['mode'] == 0 and d['mode'] == 0:
            self.opword(op | (d['reg'] << 9) | s['reg'])
        elif s['mode'] == 4 and d['mode'] == 4:
            self.opword(op | (d['reg'] << 9) | 8 | s['reg'])
        else:
            raise AsmError('bad operands for %s' % name)

    # class 3: ADD SUB AND OR (generic)
    def class3(self, base: str, op: int, size: str, ops: list[str], name: str) -> None:
        """encode class 3: generic ADD, SUB, AND, OR (selecting ADDQ/SUBQ, ADDA/SUBA, or ADDI/SUBI/ANDI/ORI when applicable)"""
        self.need(ops, 2)
        s, d = self.ea(ops[0]), self.ea(ops[1])
        q = self.imm_value(s)
        if base in ('ADD', 'SUB') and q is not None and 1 <= q <= 8:
            return self.class18(base + 'Q', (0x5000 if base == 'ADD' else 0x5100) | SIZE_BITS[size], size, ops, name)
        if d['mode'] == 1 and base in ('ADD', 'SUB'):
            return self.class10(base + 'A', (0xD0C0 if base == 'ADD' else 0x90C0), size, ops, name)
        if s['mode'] == 7 and s['reg'] == 4:
            if d['mode'] == 'special' and base in ('AND', 'OR'):
                imm = {'AND': 0x0200, 'OR': 0x0000}[base]
                return self.class4(base + 'I', imm | SIZE_BITS[size], size, ops, name)
            imm = {'ADD': 0x0600, 'SUB': 0x0400, 'AND': 0x0200, 'OR': 0x0000}[base]
            return self.class4(base + 'I', imm | SIZE_BITS[size], size, ops, name)
        if d['mode'] == 0:
            self.opword(op | (d['reg'] << 9) | self.eabits(s))
            self.emit_ext(s, size)
        elif s['mode'] == 0:
            self.opword(op | 0x100 | (s['reg'] << 9) | self.eabits(d))
            self.emit_ext(d, size)
        else:
            raise AsmError('bad operands for %s' % name)

    # class 4: ADDI SUBI ANDI ORI EORI CMPI  #imm,EA  (ANDI/ORI/EORI also to SR, CCR)
    def class4(self, base: str, op: int, size: str, ops: list[str], name: str) -> None:
        """encode class 4: immediate ADDI, SUBI, ANDI, ORI, EORI, CMPI (#imm,EA or #imm,SR/CCR)"""
        self.need(ops, 2)
        s, d = self.ea(ops[0]), self.ea(ops[1])
        if not (s['mode'] == 7 and s['reg'] == 4):
            raise AsmError('%s needs an immediate source' % name)
        if d['mode'] == 'special':
            if d['name'] == 'SR':
                self.opword((op & 0xFF00) | 0x7C)
                self.emit_ext(s, 'W')
            elif d['name'] == 'CCR':
                self.opword((op & 0xFF00) | 0x3C)
                self.emit_ext(s, 'B')
            else:
                raise AsmError('bad operand %s' % d['name'])
            return
        self.opword(op | self.eabits(d))
        self.emit_ext(s, size)
        self.emit_ext(d, size)

    # class 5: shifts and rotates
    def class5(self, base: str, op: int, size: str, ops: list[str], name: str) -> None:
        """encode class 5: bit shifts and rotates (ASL, ASR, LSL, LSR, ROL, ROR, ROXL, ROXR)"""
        typ = (op >> 3) & 3
        left = (op >> 8) & 1
        if len(ops) == 1:
            d = self.ea(ops[0])
            self.opword(0xE0C0 | (typ << 9) | (left << 8) | self.eabits(d))
            self.emit_ext(d, 'W')
            return
        self.need(ops, 2)
        s, d = self.ea(ops[0]), self.ea(ops[1])
        if d['mode'] != 0:
            raise AsmError('bad operands for %s' % name)
        sz = SIZE_BITS[size]
        if s['mode'] == 0:
            self.opword(0xE000 | (s['reg'] << 9) | (left << 8) | sz | 0x20 | (typ << 3) | d['reg'])
        elif s['mode'] == 7 and s['reg'] == 4:
            v = s['ext'][1]
            if not v.absolute or not 1 <= v.n <= 8:
                raise AsmError('shift count must be 1 to 8')
            self.opword(0xE000 | ((v.n & 7) << 9) | (left << 8) | sz | (typ << 3) | d['reg'])
        else:
            raise AsmError('bad operands for %s' % name)

    # class 6: branches
    def class6(self, base: str, op: int, size: str, ops: list[str], name: str) -> None:
        """encode class 6: Bcc, BRA, and BSR branches (auto-shortening known in-range displacements)"""
        self.need(ops, 1)
        v = self.expr(ops[0])
        short = (op & 0xFF) == 1
        cc = op & 0xFF00
        start = self.pc
        if short:
            self.opword(cc)
            if v.fwd:
                self.patch('pc8', ops[0], start + 2, off=start + 1)
                return
            if v.rel is not self.module:
                raise AsmError('branch to %s: not a label here' % ops[0])
            dsp = v.n - (start + 2)
            if -128 <= dsp <= 127 and dsp != 0:
                self.module.code[start + 1] = dsp & 0xFF
                return
            self.emit16(check16(dsp))          # a known label too far for .S: the long form
            return
        self.opword(cc)
        if v.fwd:
            self.patch('pc16', ops[0], start + 2)
        elif v.ext:
            self.ref(v.ext)
            self.emit16(0)
        elif v.rel is self.module:
            dsp = v.n - (start + 2)
            if -128 <= dsp <= 127 and dsp != 0:
                self.module.code[start + 1] = dsp & 0xFF            # a known label near: short
                return
            self.emit16(check16(dsp))
        else:
            raise AsmError('branch to %s: not a label here' % ops[0])

    # class 7: BTST BSET BCLR BCHG  Dn,EA or #n,EA
    def class7(self, base: str, op: int, size: str, ops: list[str], name: str) -> None:
        """encode class 7: bit operations BTST, BSET, BCLR, BCHG (Dn,EA or #n,EA)"""
        self.need(ops, 2)
        s, d = self.ea(ops[0]), self.ea(ops[1])
        if s['mode'] == 0:
            self.opword(op | 0x100 | (s['reg'] << 9) | self.eabits(d))
        elif s['mode'] == 7 and s['reg'] == 4:
            self.opword(op | 0x800 | self.eabits(d))
            self.emit_ext(s, 'B')
        else:
            raise AsmError('bad operands for %s' % name)
        self.emit_ext(d, 'B')

    # class 8: one effective address
    def class8(self, base: str, op: int, size: str, ops: list[str], name: str) -> None:
        """encode class 8: single-effective-address instructions (CLR, NEG, NOT, TST, JMP, JSR, PEA, Scc, TAS, NBCD)"""
        self.need(ops, 1)
        d = self.ea(ops[0])
        self.opword(op | self.eabits(d))
        self.emit_ext(d, size)

    # class 9: CMPM (Ay)+,(Ax)+
    def class9(self, base: str, op: int, size: str, ops: list[str], name: str) -> None:
        """encode class 9: CMPM (Ay)+,(Ax)+"""
        self.need(ops, 2)
        s, d = self.ea(ops[0]), self.ea(ops[1])
        if s['mode'] != 3 or d['mode'] != 3:
            raise AsmError('bad operands for %s' % name)
        self.opword(op | (d['reg'] << 9) | s['reg'])

    # class 10: ADDA SUBA CMPA MOVEA LEA  EA,An
    def class10(self, base: str, op: int, size: str, ops: list[str], name: str) -> None:
        """encode class 10: address-register destination ADDA, SUBA, CMPA, MOVEA, LEA (EA,An)"""
        self.need(ops, 2)
        s, d = self.ea(ops[0]), self.ea(ops[1])
        if d['mode'] != 1:
            raise AsmError('%s needs an address register' % name)
        if base in ('ADDA', 'SUBA', 'CMPA') and size == 'L':
            op |= 0x100
        if base == 'MOVEA' and size == 'L':
            op = 0x2040
        self.opword(op | (d['reg'] << 9) | self.eabits(s))
        self.emit_ext(s, size)

    # class 11: EXT SWAP  Dn
    def class11(self, base: str, op: int, size: str, ops: list[str], name: str) -> None:
        """encode class 11: data-register EXT and SWAP (Dn)"""
        self.need(ops, 1)
        d = self.ea(ops[0])
        if d['mode'] != 0:
            raise AsmError('%s needs a data register' % name)
        self.opword(op | d['reg'])

    # class 12: CMP (generic) MULU MULS DIVU DIVS CHK  EA,Dn
    def class12(self, base: str, op: int, size: str, ops: list[str], name: str) -> None:
        """encode class 12: CMP (selecting CMPA/CMPI when applicable), MULU, MULS, DIVU, DIVS, CHK (EA,Dn)"""
        self.need(ops, 2)
        s, d = self.ea(ops[0]), self.ea(ops[1])
        if base == 'CMP':
            if d['mode'] == 1:
                return self.class10('CMPA', 0xB0C0, size, ops, name)
            if s['mode'] == 7 and s['reg'] == 4:
                return self.class4('CMPI', 0x0C00 | SIZE_BITS[size], size, ops, name)
        if d['mode'] != 0:
            raise AsmError('%s needs a data register' % name)
        sz = size if base == 'CMP' else 'W'
        self.opword(op | (d['reg'] << 9) | self.eabits(s))
        self.emit_ext(s, sz)

    # class 13: MOVE
    def class13(self, base: str, op: int, size: str, ops: list[str], name: str) -> None:
        """encode class 13: MOVE (including SR/CCR/USP transfers and CLR/MOVEQ optimizations)"""
        self.need(ops, 2)
        s, d = self.ea(ops[0]), self.ea(ops[1])
        if d['mode'] == 'special':
            if d['name'] == 'SR':
                self.opword(0x46C0 | self.eabits(s))
                self.emit_ext(s, 'W')
            elif d['name'] == 'CCR':
                self.opword(0x44C0 | self.eabits(s))
                self.emit_ext(s, 'W')
            elif d['name'] == 'USP' and s['mode'] == 1:
                self.opword(0x4E60 | s['reg'])
            else:
                raise AsmError('bad MOVE')
            return
        if s['mode'] == 'special':
            if s['name'] == 'SR':
                self.opword(0x40C0 | self.eabits(d))
                self.emit_ext(d, 'W')
            elif s['name'] == 'USP' and d['mode'] == 1:
                self.opword(0x4E68 | d['reg'])
            else:
                raise AsmError('bad MOVE')
            return
        if size == 'B' and d['mode'] == 1:
            raise AsmError('MOVE.B to an address register')
        q = self.imm_value(s)
        if q is not None and d['mode'] != 1:
            if q == 0:
                self.opword(0x4200 | SIZE_BITS[size] | self.eabits(d))   # CLR
                self.emit_ext(d, size)
                return
            if size == 'L' and d['mode'] == 0 and -128 <= q <= 127:
                self.opword(0x7000 | (d['reg'] << 9) | (q & 0xFF))        # MOVEQ
                return
        self.opword(op | (d['reg'] << 9) | (d['mode'] << 6) | self.eabits(s))
        self.emit_ext(s, size)
        self.emit_ext(d, size)

    # class 14: MOVEM
    def class14(self, base: str, op: int, size: str, ops: list[str], name: str) -> None:
        """encode class 14: MOVEM register-list transfers (reversing mask for -(An) predecrement)"""
        self.need(ops, 2)
        if size == 'L':
            op = 0x48C0
        if self.is_reglist(ops[0]):
            mask = self.reglist(ops[0])
            d = self.ea(ops[1])
            if d['mode'] == 4:
                mask = int('{:016b}'.format(mask)[::-1], 2)
            self.opword(op | self.eabits(d))
            self.emit16(mask)
            self.emit_ext(d, size)
        else:
            s = self.ea(ops[0])
            mask = self.reglist(ops[1])
            self.opword(op | 0x400 | self.eabits(s))
            self.emit16(mask)
            self.emit_ext(s, size)

    def is_reglist(self, text: str) -> bool:
        """true if text parses as a valid MOVEM register list"""
        try:
            self.reglist(text)
            return True
        except AsmError:
            return False

    def reglist(self, text: str) -> int:
        """parse a '/' and '-' separated MOVEM register list into a 16-bit register mask"""
        mask = 0
        for part in text.split('/'):
            rng = part.split('-')
            a = self.reg(rng[0].strip())
            if a is None:
                raise AsmError('bad register list %s' % text)
            b = a if len(rng) == 1 else self.reg(rng[1].strip())
            if b is None or len(rng) > 2:
                raise AsmError('bad register list %s' % text)
            for r in range(min(a, b), max(a, b) + 1):
                mask |= 1 << r
        return mask

    # class 15: MOVEP  Dx,d(Ay) or d(Ay),Dx
    def class15(self, base: str, op: int, size: str, ops: list[str], name: str) -> None:
        """encode class 15: MOVEP peripheral data transfers between Dx and d(Ay)"""
        self.need(ops, 2)
        s, d = self.ea(ops[0]), self.ea(ops[1])
        if size == 'L':
            op = 0x0148
        if s['mode'] == 0 and d['mode'] in (2, 5):
            self.opword(op | 0x80 | (s['reg'] << 9) | d['reg'])
            self.emit_ext(d, 'W') if d['mode'] == 5 else self.emit16(0)
        elif s['mode'] in (2, 5) and d['mode'] == 0:
            self.opword(op | (d['reg'] << 9) | s['reg'])
            self.emit_ext(s, 'W') if s['mode'] == 5 else self.emit16(0)
        else:
            raise AsmError('bad operands for MOVEP')

    # class 16: MOVEQ #d,Dn
    def class16(self, base: str, op: int, size: str, ops: list[str], name: str) -> None:
        """encode class 16: MOVEQ #imm,Dn"""
        self.need(ops, 2)
        s, d = self.ea(ops[0]), self.ea(ops[1])
        if not (s['mode'] == 7 and s['reg'] == 4) or d['mode'] != 0:
            raise AsmError('bad operands for MOVEQ')
        v = s['ext'][1]
        if not v.absolute:
            raise AsmError('MOVEQ needs a number')
        self.opword(op | (d['reg'] << 9) | (v.n & 0xFF))

    # class 17: no operands
    def class17(self, base: str, op: int, size: str, ops: list[str], name: str) -> None:
        """encode class 17: operandless instructions (NOP, RTS, RTE, RTR, TRAPV, RESET, ILLEGAL)"""
        self.opword(op)

    # class 18: ADDQ SUBQ  #q,EA
    def class18(self, base: str, op: int, size: str, ops: list[str], name: str) -> None:
        """encode class 18: quick immediate ADDQ and SUBQ (#1..#8,EA)"""
        self.need(ops, 2)
        s, d = self.ea(ops[0]), self.ea(ops[1])
        v = s['ext'][1] if s['mode'] == 7 and s['reg'] == 4 else None
        if v is None or not v.absolute or not 1 <= v.n <= 8:
            raise AsmError('%s needs #1 to #8' % name)
        self.opword(op | ((v.n & 7) << 9) | self.eabits(d))
        self.emit_ext(d, size)

    # class 19: EOR  Dn,EA  (EOR #imm,EA is EORI)
    def class19(self, base: str, op: int, size: str, ops: list[str], name: str) -> None:
        """encode class 19: EOR Dn,EA (or EORI when source is #imm)"""
        self.need(ops, 2)
        s, d = self.ea(ops[0]), self.ea(ops[1])
        if s['mode'] == 7 and s['reg'] == 4:
            return self.class4('EORI', 0x0A00 | SIZE_BITS[size], size, ops, name)
        if s['mode'] != 0:
            raise AsmError('bad operands for EOR')
        self.opword(op | (s['reg'] << 9) | self.eabits(d))
        self.emit_ext(d, size)

    # class 20: DBcc  Dn,label
    def class20(self, base: str, op: int, size: str, ops: list[str], name: str) -> None:
        """encode class 20: DBcc Dn,label loop instructions"""
        self.need(ops, 2)
        d = self.ea(ops[0])
        if d['mode'] != 0:
            raise AsmError('%s needs a data register' % name)
        self.opword(op | d['reg'])
        v = self.expr(ops[1])
        start = self.pc
        if v.fwd:
            self.patch('pc16', ops[1], start)
        elif v.rel is self.module:
            self.emit16(check16(v.n - start))
        else:
            raise AsmError('%s to %s: not a label here' % (name, ops[1]))

    # class 21: EXG LINK STOP TRAP UNLK
    def class21(self, base: str, op: int, size: str, ops: list[str], name: str) -> None:
        """encode class 21: miscellaneous instructions EXG, LINK, UNLK, TRAP, and STOP"""
        if base == 'EXG':
            self.need(ops, 2)
            a, b = self.ea(ops[0]), self.ea(ops[1])
            if a['mode'] == 0 and b['mode'] == 0:
                self.opword(0xC140 | (a['reg'] << 9) | b['reg'])
            elif a['mode'] == 1 and b['mode'] == 1:
                self.opword(0xC148 | (a['reg'] << 9) | b['reg'])
            elif a['mode'] == 0 and b['mode'] == 1:
                self.opword(0xC188 | (a['reg'] << 9) | b['reg'])
            elif a['mode'] == 1 and b['mode'] == 0:
                self.opword(0xC188 | (b['reg'] << 9) | a['reg'])
            else:
                raise AsmError('bad operands for EXG')
        elif base == 'LINK':
            self.need(ops, 2)
            a, s = self.ea(ops[0]), self.ea(ops[1])
            if a['mode'] != 1 or not (s['mode'] == 7 and s['reg'] == 4):
                raise AsmError('bad operands for LINK')
            self.opword(0x4E50 | a['reg'])
            self.emit_ext(s, 'W')
        elif base == 'UNLK':
            self.need(ops, 1)
            a = self.ea(ops[0])
            if a['mode'] != 1:
                raise AsmError('bad operand for UNLK')
            self.opword(0x4E58 | a['reg'])
        elif base == 'TRAP':
            self.need(ops, 1)
            s = self.ea(ops[0])
            v = s['ext'][1] if s['mode'] == 7 and s['reg'] == 4 else None
            if v is None or not v.absolute or not 0 <= v.n <= 15:
                raise AsmError('TRAP needs #0 to #15')
            self.opword(0x4E40 | v.n)
        elif base == 'STOP':
            self.need(ops, 1)
            s = self.ea(ops[0])
            self.opword(0x4E72)
            self.emit_ext(s, 'W')
        else:
            raise AsmError('%s not supported' % name)

    # ---- the object file
    def object_file(self) -> bytes:
        """serialize all assembled modules into a 512-byte-padded Lisa .OBJ byte string"""
        out = bytearray()
        for m in self.modules:
            out += block(MODULENAME, pack_name8(m.name) + pack_name8(m.seg) + struct.pack('>L', 0))
            for name, loc in self.entries(m):
                out += block(ENTRYPOINT, pack_name8(name) + pack_name8(name) + struct.pack('>L', loc))
            for name in self.ref_names(m):
                # the offsets of the references, the last one first
                out += block(SHORTEXTERNAL, pack_name8(name) + pack_name8(name) +
                             b''.join(struct.pack('>H', o) for o in reversed(m.refs[name])))
            code = bytes(m.code)
            out += block(CODEBLOCK, struct.pack('>L', 0) + code)
            out += block(ENDBLOCK, struct.pack('>L', len(code)))
        out += block(EOFMARK, b'')
        return pad512(bytes(out))

    def entries(self, m: Module) -> list[tuple[str, int]]:
        """return [(name, offset)] for module m's procedure entry and .DEF labels in HASHER bucket order"""
        out = {m.name: 0}
        for name in m.defs:
            sym = m.symbols.get(name)
            if sym is not None and sym.kind == 'rel':
                out.setdefault(name, sym.value)
        return [(n, out[n]) for n in self.table_order(m, out)]

    def ref_names(self, m: Module) -> list[str]:
        """return module m's .REF symbol names in HASHER bucket order"""
        return self.table_order(m, m.ref_order)

    def table_order(self, m: Module, names: Iterable[str]) -> list[str]:
        """the order in which the Lisa Assembler writes these names: it
        walks its symbol table (256 hash buckets, each a chain with the
        newest symbol first) and puts each name at the head of a list
        (LINKERIN, ADDTOLIS).  So the names come by bucket from 255 down to
        0, and within a bucket in the order they were first mentioned."""
        k = self.modules.index(m) + 1
        first = {}
        for i, (mod, event, name) in enumerate(self.seen):
            if (mod == 0 or mod == k) and name not in first:
                first[name] = i
        return sorted(names, key=lambda n: (-hasher(n), first.get(n, len(self.seen))))


def hasher(name: str) -> int:
    """the Lisa Assembler's hash of a symbol name (HASHER): 0..255"""
    h = 0
    for ch in name.ljust(8)[:8]:
        h = ((h + h) & 0xFFFF) ^ ord(ch)
    if h & 0x8000:
        h -= 0x10000                      # a 16-bit Integer
    lo = h & 0xFF
    q = abs(h) // 256
    h = q if h >= 0 else -q               # DIV truncates toward zero
    return (h ^ lo) & 0xFF


def check16(n: int) -> int:
    """verify signed 16-bit displacement range (-32768..32767), raising AsmError if exceeded"""
    if not -32768 <= n <= 32767:
        raise AsmError('displacement out of range')
    return n


def assemble(path: str, opcodes: dict[str, tuple[int, int]], efficiency: bool = False) -> Assembler:
    """assemble source file path with opcode table opcodes and return the populated Assembler instance"""
    a = Assembler(opcodes)
    a.efficiency = efficiency
    a.where = os.path.basename(path)
    a.assemble_file(path)
    if a.defining is not None:
        a.error('missing .ENDM of macro %s' % a.defining, 36)
    if len(a.cond) > 1:
        a.error('missing .ENDC', 87)
    return a
