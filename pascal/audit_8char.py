#!/usr/bin/env python3
"""Audit Lisa Pascal source files for 8-character identifier-prefix collisions.

Lisa Pascal truncates identifiers to 8 characters and folds ASCII case, so two
identifiers sharing the same 8-character prefix (case-insensitive) denote the
same symbol.  This tool checks any Pascal program or unit source file for:
  * two module-scope identifiers (constants, types, enumeration literals,
    global variables, procedures, or functions) whose 8-character prefixes
    collide; and
  * a module-scope identifier whose 8-character prefix collides with an
    identifier exported by the INTERFACE section of a unit listed in USES
    (resolved from explicit unit arguments, {$U ...} unit files, or the
    active boot volume's INTRINSIC.LIB); and
  * (warning) a global linker entry point (top-level PROGRAM procedure/function
    or UNIT INTERFACE procedure/function) whose 8-character prefix duplicates an
    EntryPoint in one of the linked intrinsic libraries, which triggers
    "Warning - Duplicate entry definitions" in the Lisa Workshop Linker.

Usage:
  pascal/audit_8char.py [-q] [--boot DIR] [--libs LIB,...] [--fail-on-warn] [--no-units] <source_file> [unit_file ...]

Exit status is 0 if no collisions are found, or non-zero (1) if the audit fails.
"""

from __future__ import annotations

import argparse
import collections
import os
import re
import struct
import sys
from typing import Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BOOT = os.path.normpath(os.path.join(HERE, '..', 'libs', 'workshop3.0'))

MODULENAME = 0x80
ENTRYPOINT = 0x82
UNITBLOCK = 0x92
INTERFLOC = 0x93
VERSIONCTRL = 0x99
UNITLOCATION = 0x9D
STRINGBLOCK = 0x9E
EOFMARK = 0x00

PASCAL_KEYWORDS = {
    'and', 'array', 'begin', 'case', 'const', 'div', 'do', 'downto', 'else', 'end',
    'file', 'for', 'function', 'goto', 'if', 'in', 'label', 'mod', 'nil', 'not',
    'of', 'or', 'packed', 'procedure', 'program', 'record', 'repeat', 'set',
    'then', 'to', 'type', 'until', 'uses', 'var', 'while', 'with', 'xor',
    'intrinsic', 'interface', 'implementation', 'requires', 'unit', 'subclass',
    'override', 'abstract', 'default', 'forward', 'external', 'inline',
    'abs', 'chr', 'copy', 'delete', 'dispose', 'exit', 'false', 'get', 'high',
    'inc', 'insert', 'length', 'low', 'new', 'odd', 'ord', 'ord4', 'pred', 'put',
    'read', 'readln', 'reset', 'rewrite', 'round', 'seek', 'setlength', 'setord',
    'sizeof', 'sqr', 'succ', 'true', 'trunc', 'val', 'write', 'writeln', 'eof',
    'eoln', 'close', 'open', 'append', 'blockread', 'blockwrite', 'assign',
    'rename', 'pack', 'unpack', 'integer', 'longint', 'boolean', 'char', 'real',
    'string', 'text', 'shared', 'data',
}


def key8(name: str) -> str:
    """Return the lowercase 8-character significant prefix of a Lisa Pascal identifier."""
    return name[:8].lower()


def resolve_source_path(path: str, base_dirs: Sequence[str] = ()) -> str | None:
    """Resolve a Pascal source or unit filename (with or without .TEXT/.OBJ, case-insensitively)."""
    _, ext = os.path.splitext(path)
    has_known_ext = ext.lower() in ('.text', '.pas', '.obj', '.lib')
    search_roots = [''] + [d for d in base_dirs if d]
    for base in search_roots:
        full = os.path.join(base, path) if base else path
        cands = [full] if has_known_ext else [full, full + '.TEXT', full + '.text', full + '.pas']
        for cand in cands:
            if os.path.isfile(cand):
                return cand
            parent = os.path.dirname(cand) or '.'
            target = os.path.basename(cand).lower()
            if os.path.isdir(parent):
                for entry in os.listdir(parent):
                    if entry.lower() == target:
                        hit = os.path.join(parent, entry)
                        if os.path.isfile(hit):
                            return hit
    return None


def decode_lisa_text_bytes(raw: bytes) -> str:
    """Decode either a Lisa 1 KB paged .TEXT/.OBJ-interface stream (with DLE indentation) or a host text file."""
    if raw.endswith(b'\xff'):
        raw = raw[:-1]
    if len(raw) >= 1024 and len(raw) % 1024 == 0 and b'\n' not in raw:
        raw = raw[1024:]
        paged = True
    else:
        paged = False
    if b'\x10' in raw or paged:
        out = bytearray()
        i = 0
        n = len(raw)
        while i < n:
            b = raw[i]
            if b == 0x10 and i + 1 < n:
                out += b' ' * max(raw[i + 1] - 32, 0)
                i += 2
            elif b == 0:
                if paged:
                    i = (i // 1024 + 1) * 1024
                else:
                    i += 1
            elif b == 13:
                out.append(10)
                i += 1
            else:
                out.append(b)
                i += 1
        return out.decode('latin-1')
    for enc in ('utf-8', 'latin-1'):
        try:
            return raw.decode(enc).replace('\r\n', '\n').replace('\r', '\n')
        except UnicodeDecodeError:
            pass
    return raw.decode('latin-1', errors='replace').replace('\r\n', '\n').replace('\r', '\n')


def read_text(path: str) -> str:
    """Read and decode a host or Lisa .TEXT Pascal file."""
    return decode_lisa_text_bytes(open(path, 'rb').read())


def extract_obj_unit_interface(obj_path: str, unit_8char: str | None = None) -> str | None:
    """Extract embedded Pascal INTERFACE text for unit_8char (or the sole unit) from a Lisa .OBJ file."""
    raw = open(obj_path, 'rb').read()
    pos = 0
    is_library = bool(raw and raw[0] == VERSIONCTRL)
    target = unit_8char.upper() if unit_8char else None

    while pos + 4 <= len(raw):
        btype = raw[pos]
        bsize = int.from_bytes(raw[pos + 1:pos + 4], 'big')
        if bsize < 4:
            bsize = 4
        body = raw[pos + 4:pos + bsize]
        if btype == EOFMARK:
            break
        if btype == UNITBLOCK and len(body) >= 26:
            u8 = body[0:8].decode('latin-1', errors='ignore').rstrip(' ').upper()
            if target is None or u8 == target:
                if not is_library:
                    toff = struct.unpack_from('>L', body, 12)[0]
                    tsz = struct.unpack_from('>L', body, 16)[0]
                    if toff > 0 and tsz > 0 and toff + tsz <= len(raw):
                        pages = raw[toff:toff + tsz]
                        buf = bytearray()
                        for p in range(0, len(pages), 1024):
                            buf += pages[p:p + 1024].rstrip(b'\0')
                        if buf and (buf[0] & 0x80):
                            buf[0] &= 0x7F
                        return decode_lisa_text_bytes(b'\n' + bytes(buf))
                elif len(body) > 26:
                    txt = bytearray(body[26:].rstrip(b'\0'))
                    if txt:
                        if txt[0] & 0x80:
                            txt[0] &= 0x7F
                        return decode_lisa_text_bytes(b'\n' + bytes(txt))
            if is_library and len(body) == 26 and (target is None or u8 == target):
                # Workshop 3.0 stores interface pages immediately after the 30-byte UnitBlock header
                # when InterfLoc points to this UnitBlock; scan page text if 'INTERFACE' follows.
                end_blk = pos + bsize
                probe = raw[end_blk:end_blk + 65536]
                if b'INTERFACE' in probe[:512] or b'interface' in probe[:512]:
                    # Read until next object block or IMPLEMENTATION
                    m_imp = re.search(rb'\bIMPLEMENTATION\b', probe, flags=re.I)
                    if m_imp:
                        chunk = bytearray(probe[:m_imp.end()].replace(b'\x00', b''))
                        if chunk and (chunk[0] & 0x80):
                            chunk[0] &= 0x7F
                        return decode_lisa_text_bytes(b'\n' + bytes(chunk))
        pos += bsize
    return None


def read_iulib_map(boot_dir: str) -> dict[str, str]:
    """Return {UNIT_8CHAR: absolute_library_obj_path} from boot_dir/INTRINSIC.LIB if present."""
    iulib_path = resolve_source_path('INTRINSIC.LIB', [boot_dir])
    if not iulib_path:
        return {}
    raw = open(iulib_path, 'rb').read()
    pos = 0
    unit_fnums: dict[str, int] = {}
    file_names: dict[int, str] = {}
    while pos + 4 <= len(raw):
        btype = raw[pos]
        bsize = int.from_bytes(raw[pos + 1:pos + 4], 'big')
        if bsize < 4:
            bsize = 4
        body = raw[pos + 4:pos + bsize]
        if btype == EOFMARK:
            break
        if btype == UNITLOCATION and len(body) >= 2:
            cnt = struct.unpack_from('>H', body, 0)[0]
            for i in range(cnt):
                q = 2 + 16 * i
                if q + 16 <= len(body):
                    u8 = body[q:q + 8].decode('latin-1', errors='ignore').rstrip(' ').upper()
                    fnum = body[q + 10]
                    unit_fnums[u8] = fnum
        elif btype == STRINGBLOCK and len(body) >= 2:
            cnt = struct.unpack_from('>H', body, 0)[0]
            for i in range(cnt):
                if 2 + 6 * (i + 1) <= len(body):
                    fnum, s_off = struct.unpack_from('>HL', body, 2 + 6 * i)
                    if s_off < len(raw):
                        slen = raw[s_off]
                        fname = raw[s_off + 1:s_off + 1 + slen].decode('latin-1', errors='ignore').strip()
                        # Strip Lisa volume prefix (e.g. '-#BOOT-Sys1Lib.obj' -> 'Sys1Lib.obj')
                        if fname.startswith('-') and '-' in fname[1:]:
                            fname = fname.split('-', 2)[2]
                        fname = fname.lstrip('*')
                        file_names[fnum] = fname
        pos += bsize

    result: dict[str, str] = {}
    for u8, fnum in unit_fnums.items():
        fn = file_names.get(fnum, '')
        if fn:
            resolved = resolve_source_path(fn, [boot_dir])
            if resolved:
                result[u8] = resolved
    return result


def tokenize(text: str) -> list[tuple[str, str]]:
    """Tokenize Pascal source into (KIND, VALUE) pairs: DIRECTIVE, STRING, IDENT, NUM, SYM."""
    tokens: list[tuple[str, str]] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch in (' ', '\t', '\r', '\n', '\x0c'):
            i += 1
            continue
        if ch == '{':
            j = text.find('}', i + 1)
            j = n if j == -1 else j + 1
            inner = text[i + 1:j - 1].strip()
            if inner.startswith('$'):
                tokens.append(('DIRECTIVE', inner))
            i = j
            continue
        if ch == '(' and i + 1 < n and text[i + 1] == '*':
            j = text.find('*)', i + 2)
            j = n if j == -1 else j + 2
            inner = text[i + 2:j - 2].strip() if j - i >= 4 else ''
            if inner.startswith('$'):
                tokens.append(('DIRECTIVE', inner))
            i = j
            continue
        if ch == "'":
            j = i + 1
            while j < n:
                if text[j] == "'":
                    j += 1
                    if j < n and text[j] == "'":
                        j += 1
                        continue
                    break
                j += 1
            tokens.append(('STRING', "''"))
            i = j
            continue
        if ch.isalpha() or ch in ('_', '%'):
            j = i + 1
            while j < n and (text[j].isalnum() or text[j] in ('_', '%')):
                j += 1
            tokens.append(('IDENT', text[i:j]))
            i = j
            continue
        if ch.isdigit() or ch == '$':
            j = i + 1
            while j < n and (text[j].isalnum() or (text[j] == '.' and j + 1 < n and text[j + 1] != '.')):
                j += 1
            tokens.append(('NUM', text[i:j]))
            i = j
            continue
        if text[i:i + 2] in (':=', '<=', '>=', '<>', '..'):
            tokens.append(('SYM', text[i:i + 2]))
            i += 2
            continue
        tokens.append(('SYM', ch))
        i += 1
    return tokens


def eval_cond(expr: str, syms: dict[str, int | bool]) -> bool:
    """Evaluate a Lisa Pascal $SETC/$IFC conditional expression against syms."""
    parts = re.findall(
        r'<=|>=|<>|=|\(|\)|\bAND\b|\bOR\b|\bNOT\b|\bTRUE\b|\bFALSE\b|\$[0-9A-Fa-f]+|\d+|[A-Za-z_]\w*',
        expr,
        flags=re.I,
    )
    py: list[str] = []
    for t in parts:
        tu = t.upper()
        if tu == 'AND':
            py.append(' and ')
        elif tu == 'OR':
            py.append(' or ')
        elif tu == 'NOT':
            py.append(' not ')
        elif tu == 'TRUE':
            py.append('True')
        elif tu == 'FALSE':
            py.append('False')
        elif t == '=':
            py.append(' == ')
        elif t == '<>':
            py.append(' != ')
        elif t in ('<=', '>=', '<', '>', '(', ')'):
            py.append(t)
        elif t.startswith('$'):
            py.append(str(int(t[1:], 16)))
        elif t.isdigit():
            py.append(t)
        else:
            py.append(repr(syms.get(tu, False)))
    try:
        return bool(eval(''.join(py), {'__builtins__': {}}))
    except Exception:
        return True


def expand_and_filter_tokens(
    text: str,
    base_dirs: Sequence[str] = (),
    syms: dict[str, int | bool] | None = None,
    seen_includes: set[str] | None = None,
) -> list[tuple[str, str]]:
    """Tokenize text, expanding active {$I file} includes and evaluating {$SETC}/{$IFC}/{$ELSEC}/{$ENDC}."""
    if syms is None:
        syms = {}
    if seen_includes is None:
        seen_includes = set()
    raw_toks = tokenize(text)
    out: list[tuple[str, str]] = []
    # Stack of (parent_active, branch_taken, cur_active)
    cond_stack: list[tuple[bool, bool, bool]] = [(True, False, True)]

    for tk, tv in raw_toks:
        cur_act = cond_stack[-1][2]
        if tk == 'DIRECTIVE':
            m_ifc = re.match(r'^\$IFC\b(.*)$', tv, flags=re.I | re.S)
            m_elsec = re.match(r'^\$ELSEC\b', tv, flags=re.I)
            m_endc = re.match(r'^\$ENDC\b', tv, flags=re.I)
            m_setc = re.match(r'^\$SETC\s+([A-Za-z_]\w*)\s*(?::=|=)\s*(.*)$', tv, flags=re.I | re.S)
            m_inc = re.match(r'^\$I(?!FC\b)\s*([^\s+-][^\s]*)$', tv, flags=re.I)
            if m_ifc:
                pa = cond_stack[-1][2]
                if pa:
                    val = eval_cond(m_ifc.group(1), syms)
                    cond_stack.append((True, val, val))
                else:
                    cond_stack.append((False, False, False))
                continue
            if m_elsec:
                if len(cond_stack) > 1:
                    pa, taken, _ = cond_stack[-1]
                    cond_stack[-1] = (pa, True, pa and not taken)
                continue
            if m_endc:
                if len(cond_stack) > 1:
                    cond_stack.pop()
                continue
            if not cur_act:
                continue
            if m_setc:
                syms[m_setc.group(1).upper()] = eval_cond(m_setc.group(2), syms)
                continue
            if m_inc:
                inc_name = m_inc.group(1).strip()
                inc_path = resolve_source_path(inc_name, base_dirs)
                if inc_path and os.path.abspath(inc_path) not in seen_includes:
                    seen_includes.add(os.path.abspath(inc_path))
                    inc_dirs = [os.path.dirname(os.path.abspath(inc_path))] + list(base_dirs)
                    out.extend(expand_and_filter_tokens(read_text(inc_path), inc_dirs, syms, seen_includes))
                continue
            out.append((tk, tv))
            continue
        if cur_act:
            out.append((tk, tv))
    return out


def parse_uses_clause(tokens: Sequence[tuple[str, str]]) -> list[tuple[str, str | None]]:
    """Extract [(unit_name, optional_$U_file)] from INTERFACE / PROGRAM USES clauses."""
    result: list[tuple[str, str | None]] = []
    i = 0
    n = len(tokens)
    while i < n:
        tk, tv = tokens[i]
        if tk == 'IDENT' and tv.upper() == 'IMPLEMENTATION':
            # Only inspect USES in PROGRAM header or UNIT INTERFACE (or IMPLEMENTATION USES too!)
            pass
        if tk == 'IDENT' and tv.upper() == 'USES':
            i += 1
            pending_ufile: str | None = None
            while i < n:
                k, v = tokens[i]
                if k == 'SYM' and v == ';':
                    i += 1
                    break
                if k == 'DIRECTIVE':
                    mu = re.match(r'^\$U\s+([^\s]+)$', v, flags=re.I)
                    if mu:
                        pending_ufile = mu.group(1).strip()
                elif k == 'IDENT':
                    result.append((v, pending_ufile))
                    pending_ufile = None
                i += 1
            continue
        i += 1
    return result


def extract_scope_identifiers(
    tokens: Sequence[tuple[str, str]],
    interface_only: bool = False,
    routines_only: bool = False,
) -> list[str]:
    """Extract top-level CONST, TYPE, enum, VAR, and PROCEDURE/FUNCTION names from tokens.

    Tracks nesting of RECORD..END, SUBCLASS..END, CASE..OF..END, and routine
    bodies (PROCEDURE/FUNCTION .. BEGIN..END) so record fields, Clascal class
    members, and procedure-local declarations are never mistaken for module-scope
    identifiers.  In a UNIT, repeating an INTERFACE procedure/function header in
    IMPLEMENTATION is recognized as the implementation of that routine rather than
    a duplicate declaration.  When routines_only is True, returns only routines
    that emit global linker EntryPoints (top-level PROGRAM routines or UNIT
    INTERFACE routines).
    """
    names: list[str] = []
    exported_routines: list[str] = []
    iface_routines: set[str] = set()
    in_implementation = False
    section: str | None = None  # 'CONST', 'TYPE', 'VAR', or None
    struct_depth = 0            # RECORD / SUBCLASS nesting depth inside TYPE/VAR
    methods_block = False       # Inside Clascal `METHODS OF ClassName ... END;`
    routine_depth = 0           # Nested PROCEDURE/FUNCTION depth awaiting/inside body
    begin_depth = 0             # BEGIN / CASE nesting inside routine or main block
    paren_depth = 0

    i = 0
    n = len(tokens)

    # Skip PROGRAM/UNIT header name so program/unit name itself isn't confused with vars
    while i < n:
        tk, tv = tokens[i]
        u = tv.upper() if tk == 'IDENT' else ''
        if u in ('PROGRAM', 'UNIT'):
            while i < n and not (tokens[i][0] == 'SYM' and tokens[i][1] == ';'):
                i += 1
            i += 1
            break
        if u in ('INTERFACE', 'INTRINSIC', 'USES', 'CONST', 'TYPE', 'VAR', 'PROCEDURE', 'FUNCTION', 'BEGIN'):
            break
        i += 1

    while i < n:
        tk, tv = tokens[i]
        u = tv.upper() if tk == 'IDENT' else ''

        if tk == 'SYM':
            if tv in ('(', '['):
                paren_depth += 1
            elif tv in (')', ']'):
                paren_depth = max(0, paren_depth - 1)

        # Stop at END. (end of program or unit)
        if u == 'END' and i + 1 < n and tokens[i + 1] == ('SYM', '.'):
            break

        if u == 'INTERFACE' and routine_depth == 0 and begin_depth == 0:
            section = None
            i += 1
            continue

        if u == 'IMPLEMENTATION' and routine_depth == 0 and begin_depth == 0:
            if interface_only:
                break
            in_implementation = True
            section = None
            struct_depth = 0
            i += 1
            continue

        # Skip USES ... ;
        if u == 'USES' and routine_depth == 0 and begin_depth == 0:
            while i < n and tokens[i] != ('SYM', ';'):
                i += 1
            i += 1
            continue

        # Skip LABEL ... ;
        if u == 'LABEL' and routine_depth == 0 and begin_depth == 0:
            section = None
            while i < n and tokens[i] != ('SYM', ';'):
                i += 1
            i += 1
            continue

        # Inside a routine declaration / body (or main program BEGIN..END block):
        if routine_depth > 0 or begin_depth > 0:
            if paren_depth == 0:
                if u in ('RECORD', 'SUBCLASS'):
                    struct_depth += 1
                elif struct_depth > 0 and u == 'END':
                    struct_depth -= 1
                elif struct_depth == 0:
                    if u in ('PROCEDURE', 'FUNCTION'):
                        prev = tokens[i - 1][1].upper() if i > 0 else ''
                        if prev not in ('=', ':', 'OF'):
                            # Advance past nested header; check if FORWARD/EXTERNAL/INLINE
                            j = i + 1
                            pd = 0
                            while j < n:
                                if tokens[j][1] == '(':
                                    pd += 1
                                elif tokens[j][1] == ')':
                                    pd = max(0, pd - 1)
                                elif pd == 0 and tokens[j] == ('SYM', ';'):
                                    j += 1
                                    break
                                j += 1
                            has_body = True
                            while j < n and tokens[j][0] == 'IDENT' and tokens[j][1].upper() in (
                                'FORWARD', 'EXTERNAL', 'INLINE', 'C', 'OVERRIDE', 'ABSTRACT', 'DEFAULT'
                            ):
                                mod_u = tokens[j][1].upper()
                                if mod_u in ('FORWARD', 'EXTERNAL', 'INLINE', 'ABSTRACT'):
                                    has_body = False
                                j += 1
                                if mod_u == 'INLINE' and j < n and tokens[j][1] == '(':
                                    ipd = 0
                                    while j < n:
                                        if tokens[j][1] == '(':
                                            ipd += 1
                                        elif tokens[j][1] == ')':
                                            ipd -= 1
                                            if ipd <= 0:
                                                j += 1
                                                break
                                        j += 1
                                if j < n and tokens[j] == ('SYM', ';'):
                                    j += 1
                            if has_body:
                                routine_depth += 1
                            i = j
                            continue
                    elif u in ('BEGIN', 'CASE'):
                        begin_depth += 1
                    elif u == 'END':
                        if begin_depth > 0:
                            begin_depth -= 1
                            if begin_depth == 0 and routine_depth > 0:
                                # End of a routine's BEGIN..END block!
                                routine_depth -= 1
            i += 1
            continue

        # Inside Clascal `METHODS OF ClassName ... (END; | BEGIN ... END;)` block in IMPLEMENTATION:
        if methods_block and routine_depth == 0 and begin_depth == 0 and paren_depth == 0:
            if u == 'END':
                methods_block = False
                i += 1
                continue
            if u == 'BEGIN':
                # Optional class-init `BEGIN ... END;` terminates the `METHODS OF` block when it closes!
                methods_block = False
                begin_depth = 1
                i += 1
                continue
            if u in ('PROCEDURE', 'FUNCTION'):
                j = i + 1
                pd = 0
                while j < n:
                    if tokens[j][1] == '(':
                        pd += 1
                    elif tokens[j][1] == ')':
                        pd = max(0, pd - 1)
                    elif pd == 0 and tokens[j] == ('SYM', ';'):
                        j += 1
                        break
                    j += 1
                routine_depth = 1
                i = j
                continue
            i += 1
            continue

        # Top-level (routine_depth == 0 and begin_depth == 0)
        if paren_depth == 0 and struct_depth == 0:
            if u == 'METHODS' and i + 1 < n and tokens[i + 1][1].upper() == 'OF':
                section = None
                methods_block = True
                i += 2
                continue
            if u in ('CONST', 'TYPE', 'VAR'):
                section = u
                i += 1
                continue
            if u == 'BEGIN':
                section = None
                begin_depth = 1
                i += 1
                continue
            if u in ('PROCEDURE', 'FUNCTION'):
                prev = tokens[i - 1][1].upper() if i > 0 else ''
                if prev not in ('=', ':', 'OF'):
                    section = None
                    j = i + 1
                    rname = ''
                    is_method_impl = False
                    if j < n and tokens[j][0] == 'IDENT':
                        rname = tokens[j][1]
                        j += 1
                        if j + 1 < n and tokens[j] == ('SYM', '.') and tokens[j + 1][0] == 'IDENT':
                            is_method_impl = True
                            j += 2
                    pd = 0
                    while j < n:
                        if tokens[j][1] == '(':
                            pd += 1
                        elif tokens[j][1] == ')':
                            pd = max(0, pd - 1)
                        elif pd == 0 and tokens[j] == ('SYM', ';'):
                            j += 1
                            break
                        j += 1
                    is_forward = False
                    has_body = not (interface_only or (not in_implementation and is_unit_tokens(tokens)))
                    while j < n and tokens[j][0] == 'IDENT' and tokens[j][1].upper() in (
                        'FORWARD', 'EXTERNAL', 'INLINE', 'C', 'OVERRIDE', 'ABSTRACT', 'DEFAULT'
                    ):
                        mod_u = tokens[j][1].upper()
                        if mod_u == 'FORWARD':
                            is_forward = True
                            has_body = False
                        elif mod_u in ('EXTERNAL', 'INLINE', 'ABSTRACT'):
                            has_body = False
                        j += 1
                        if mod_u == 'INLINE' and j < n and tokens[j][1] == '(':
                            ipd = 0
                            while j < n:
                                if tokens[j][1] == '(':
                                    ipd += 1
                                elif tokens[j][1] == ')':
                                    ipd -= 1
                                    if ipd <= 0:
                                        j += 1
                                        break
                                j += 1
                        if j < n and tokens[j] == ('SYM', ';'):
                            j += 1
                    if rname and not is_method_impl and not is_forward and not rname.startswith('%'):
                        k8 = key8(rname)
                        if not in_implementation and is_unit_tokens(tokens):
                            iface_routines.add(k8)
                            names.append(rname)
                            exported_routines.append(rname)
                        elif in_implementation and k8 in iface_routines:
                            # Matching IMPLEMENTATION body for an INTERFACE routine
                            pass
                        else:
                            names.append(rname)
                            if not is_unit_tokens(tokens):
                                exported_routines.append(rname)
                    if has_body:
                        routine_depth = 1
                    i = j
                    continue

        # Track RECORD / SUBCLASS nesting inside top-level TYPE / VAR
        if paren_depth == 0:
            if u in ('RECORD', 'SUBCLASS'):
                # Forward `TBar = SUBCLASS;` has `;` right after SUBCLASS
                if u == 'SUBCLASS' and i + 1 < n and tokens[i + 1] == ('SYM', ';'):
                    pass
                else:
                    struct_depth += 1
                i += 1
                continue
            if struct_depth > 0 and u == 'END':
                struct_depth -= 1
                i += 1
                continue

        if struct_depth == 0 and paren_depth == 0:
            prev = tokens[i - 1] if i > 0 else ('SYM', ';')
            at_stmt_start = prev == ('SYM', ';') or prev[1].upper() in ('CONST', 'TYPE', 'VAR')
            if section == 'CONST':
                if at_stmt_start and tk == 'IDENT' and i + 1 < n and tokens[i + 1] == ('SYM', '='):
                    names.append(tv)
            elif section == 'TYPE':
                if at_stmt_start and tk == 'IDENT' and i + 1 < n and tokens[i + 1] == ('SYM', '='):
                    names.append(tv)
                    # Check enumeration type `TypeName = (lit1, lit2, ...)`
                    if i + 2 < n and tokens[i + 2] == ('SYM', '('):
                        k = i + 3
                        while k < n and tokens[k] != ('SYM', ')'):
                            if tokens[k][0] == 'IDENT':
                                names.append(tokens[k][1])
                            k += 1
            elif section == 'VAR':
                # Collect `v1, v2, v3 : SomeType` at top level!
                if at_stmt_start and tk == 'IDENT':
                    # Scan comma-separated identifier list if followed by ':'
                    cand: list[str] = [tv]
                    k = i + 1
                    while k + 1 < n and tokens[k] == ('SYM', ',') and tokens[k + 1][0] == 'IDENT':
                        cand.append(tokens[k + 1][1])
                        k += 2
                    if k < n and tokens[k] == ('SYM', ':'):
                        names.extend(cand)
                        i = k + 1
                        continue

        i += 1

    target_list = exported_routines if routines_only else names
    return [nm for nm in target_list if nm.lower() not in PASCAL_KEYWORDS and not nm.startswith('%')]


def is_unit_tokens(tokens: Sequence[tuple[str, str]]) -> bool:
    """Return True if token stream represents a Pascal UNIT (has UNIT or INTERFACE header)."""
    for tk, tv in tokens[:40]:
        if tk == 'IDENT' and tv.upper() in ('UNIT', 'INTERFACE', 'INTRINSIC'):
            return True
        if tk == 'IDENT' and tv.upper() in ('PROGRAM', 'BEGIN'):
            return False
    return False


def unit_interface_ids_from_text(text: str, base_dirs: Sequence[str] = ()) -> list[str]:
    """Extract all exported INTERFACE identifiers from a unit's Pascal source text."""
    toks = expand_and_filter_tokens(text, base_dirs, {'FOROS': True, 'LIBRARYVERSION': 30})
    return extract_scope_identifiers(toks, interface_only=True)


def unit_interface_ids(path: str) -> list[str]:
    """Extract all exported INTERFACE identifiers from a unit .TEXT/.pas or .OBJ file."""
    if path.lower().endswith('.obj'):
        iface = extract_obj_unit_interface(path)
        return unit_interface_ids_from_text(iface, [os.path.dirname(path)]) if iface else []
    return unit_interface_ids_from_text(read_text(path), [os.path.dirname(path)])


def program_scope_ids(path: str) -> list[str]:
    """Extract all module-scope identifiers from a Pascal program or unit file."""
    abs_p = os.path.abspath(path)
    toks = expand_and_filter_tokens(
        read_text(abs_p), [os.path.dirname(abs_p)], {'FOROS': True, 'LIBRARYVERSION': 30}, {abs_p}
    )
    return extract_scope_identifiers(toks, interface_only=False)


def exported_entrypoint_routines(path: str) -> tuple[str | None, list[str]]:
    """Return (unit_name_if_unit_else_None, global_entrypoint_routine_names) for path."""
    abs_p = os.path.abspath(path)
    toks = expand_and_filter_tokens(
        read_text(abs_p), [os.path.dirname(abs_p)], {'FOROS': True, 'LIBRARYVERSION': 30}, {abs_p}
    )
    unit_name: str | None = None
    for idx, (tk, tv) in enumerate(toks[:40]):
        if tk == 'IDENT' and tv.upper() == 'UNIT':
            if idx + 1 < len(toks) and toks[idx + 1][0] == 'IDENT':
                unit_name = toks[idx + 1][1]
            elif idx + 2 < len(toks) and toks[idx + 1][1].upper() == 'INTRINSIC' and toks[idx + 2][0] == 'IDENT':
                unit_name = toks[idx + 2][1]
            break
    return unit_name, extract_scope_identifiers(toks, interface_only=False, routines_only=True)


def read_library_entrypoints(obj_path: str) -> dict[str, list[tuple[str, str]]]:
    """Read all non-local ($) EntryPoint records from a Lisa library/object file."""
    raw = open(obj_path, 'rb').read()
    pos = 0
    seg = ''
    fname = os.path.basename(obj_path)
    entries: dict[str, list[tuple[str, str]]] = collections.defaultdict(list)
    while pos + 4 <= len(raw):
        btype = raw[pos]
        bsize = int.from_bytes(raw[pos + 1:pos + 4], 'big')
        if bsize < 4:
            bsize = 4
        body = raw[pos + 4:pos + bsize]
        if btype == EOFMARK:
            break
        if btype == MODULENAME and len(body) >= 16:
            seg = body[8:16].decode('latin-1', errors='ignore').strip()
        elif btype == ENTRYPOINT and len(body) >= 8:
            ln = body[0:8].decode('latin-1', errors='ignore').strip()
            if ln and not ln.startswith('$'):
                k = key8(ln)
                loc = (fname, seg)
                if loc not in entries[k]:
                    entries[k].append(loc)
        pos += bsize
    return entries


def resolve_linked_libraries(
    prog_path: str,
    boot_dir: str,
    explicit_libs: Sequence[str] = (),
) -> list[str]:
    """Resolve the intrinsic library .OBJ files linked with prog_path."""
    abs_p = os.path.abspath(prog_path)
    search_dirs = [os.path.dirname(abs_p), os.getcwd(), boot_dir]
    iulib_map = read_iulib_map(boot_dir)

    if explicit_libs:
        libs: list[str] = []
        for lib in explicit_libs:
            cand = lib if lib.lower().endswith('.obj') else lib + '.obj'
            resolved = resolve_source_path(cand, search_dirs)
            if not resolved:
                sys.stderr.write(f'audit_8char.py: library file not found: {lib}\n')
            elif os.path.abspath(resolved) not in {os.path.abspath(x) for x in libs}:
                libs.append(resolved)
        return libs

    unit_name, _ = exported_entrypoint_routines(abs_p)
    if unit_name and unit_name[:8].upper() in iulib_map:
        # Intrinsic unit itself belongs to an intrinsic library; its own exports live there.
        return []

    toks = expand_and_filter_tokens(
        read_text(abs_p), search_dirs, {'FOROS': True, 'LIBRARYVERSION': 30}, {abs_p}
    )
    uses_list = parse_uses_clause(toks)
    libs = []
    seen_abs: set[str] = set()

    # Every linked Pascal program links IOSPASLIB if present in boot_dir.
    if unit_name is None:
        iospas = resolve_source_path('iospaslib.obj', [boot_dir])
        if iospas:
            seen_abs.add(os.path.abspath(iospas))
            libs.append(iospas)

    for uname, _ in uses_list:
        u8 = uname[:8].upper()
        if u8 in iulib_map:
            lib_obj = iulib_map[u8]
            if os.path.abspath(lib_obj) not in seen_abs:
                seen_abs.add(os.path.abspath(lib_obj))
                libs.append(lib_obj)
                if os.path.basename(lib_obj).lower() == 'sys1lib.obj':
                    sys2 = resolve_source_path('sys2lib.obj', [boot_dir])
                    if sys2 and os.path.abspath(sys2) not in seen_abs:
                        seen_abs.add(os.path.abspath(sys2))
                        libs.append(sys2)
    return libs


def warn_library_entrypoints(
    routines: Sequence[str],
    lib_paths: Sequence[str],
    quiet: bool = False,
    show_on_quiet: bool = False,
) -> bool:
    """Check global routines against library EntryPoints and print Workshop Linker duplicate-entry warnings."""
    lib_map: dict[str, list[tuple[str, str]]] = collections.defaultdict(list)
    for lp in lib_paths:
        for k, locs in read_library_entrypoints(lp).items():
            for loc in locs:
                if loc not in lib_map[k]:
                    lib_map[k].append(loc)

    hits: list[tuple[str, str, list[tuple[str, str]]]] = []
    for rname in routines:
        k = key8(rname)
        if k in lib_map:
            hits.append((k.upper(), rname, lib_map[k]))

    if not quiet or (hits and show_on_quiet):
        print('--- linker entry points vs libraries (warnings) ---')
        if not hits:
            print('  (no duplicate library entry definitions)')
        for k_up, rname, locs in hits:
            where = ', '.join(f'{seg} in {fn}' if seg else fn for fn, seg in locs)
            print(f'  WARNING {k_up}: routine {rname} duplicates library entry ({where})')
    return bool(hits)


def resolve_used_units(
    prog_path: str,
    boot_dir: str,
) -> list[tuple[str, list[str]]]:
    """Resolve and parse INTERFACE identifiers for every unit referenced in prog_path's USES clause."""
    abs_p = os.path.abspath(prog_path)
    src_dir = os.path.dirname(abs_p)
    search_dirs = [src_dir, os.getcwd(), boot_dir]
    toks = expand_and_filter_tokens(
        read_text(abs_p), search_dirs, {'FOROS': True, 'LIBRARYVERSION': 30}, {abs_p}
    )
    uses_list = parse_uses_clause(toks)
    if not uses_list:
        return []

    iulib_map = read_iulib_map(boot_dir)
    loaded: list[tuple[str, list[str]]] = []
    seen_u8: set[str] = set()

    for uname, ufile in uses_list:
        u8 = uname[:8].upper()
        if u8 in seen_u8:
            continue
        seen_u8.add(u8)

        iface_txt: str | None = None
        label = uname

        # 1. Explicit {$U file}
        if ufile:
            cand_obj = resolve_source_path(
                ufile if ufile.lower().endswith('.obj') else ufile + '.obj',
                search_dirs,
            )
            if cand_obj:
                iface_txt = extract_obj_unit_interface(cand_obj, u8)
                label = os.path.basename(cand_obj) + f' ({uname})'
            if iface_txt is None:
                cand_txt = resolve_source_path(ufile, search_dirs)
                if cand_txt and not cand_txt.lower().endswith('.obj'):
                    iface_txt = read_text(cand_txt)
                    label = os.path.basename(cand_txt)

        # 2. Intrinsic library lookup via INTRINSIC.LIB
        if iface_txt is None and u8 in iulib_map:
            lib_obj = iulib_map[u8]
            iface_txt = extract_obj_unit_interface(lib_obj, u8)
            label = f'{os.path.basename(lib_obj)}:{uname}'

        # 3. Plain <Unit>.obj or <Unit>.text in search_dirs
        if iface_txt is None:
            cand_obj = resolve_source_path(uname + '.obj', search_dirs)
            if cand_obj:
                iface_txt = extract_obj_unit_interface(cand_obj, u8)
                label = os.path.basename(cand_obj)
        if iface_txt is None:
            cand_txt = resolve_source_path(uname, search_dirs)
            if cand_txt and os.path.abspath(cand_txt) != abs_p:
                iface_txt = read_text(cand_txt)
                label = os.path.basename(cand_txt)

        if iface_txt is not None:
            ids = unit_interface_ids_from_text(iface_txt, search_dirs)
            loaded.append((label, ids))

    return loaded


def report(ids: Sequence[str], title: str, quiet: bool = False) -> dict[str, list[str]]:
    """Group identifiers by 8-char key and print any collisions."""
    groups: dict[str, list[str]] = collections.defaultdict(list)
    for n in ids:
        groups[key8(n)].append(n)
    # Flag any 8-char bucket with >1 entry (distinct >8-char names or duplicate declarations)
    dups = {k: v for k, v in groups.items() if len(v) > 1}
    if not quiet or dups:
        print(f'--- {title} ---')
        if not dups:
            print('  (no internal collisions)')
        for k, v in sorted(dups.items()):
            print(f'  COLLISION {k.upper()}: {", ".join(v)}')
    return dups


def cross(a: Sequence[str], b: Sequence[str], title: str, quiet: bool = False) -> bool:
    """Check whether any identifier in a collides on 8 characters with an imported unit identifier in b."""
    kb: dict[str, list[str]] = collections.defaultdict(list)
    for n in b:
        if n not in kb[key8(n)]:
            kb[key8(n)].append(n)
    hits: list[tuple[str, str, list[str]]] = []
    for n in a:
        if key8(n) in kb:
            hits.append((key8(n).upper(), n, kb[key8(n)]))
    if not quiet or hits:
        print(f'--- {title} ---')
        if not hits:
            print('  (no collisions)')
        for k_up, prog_n, unit_ns in hits:
            print(f'  COLLISION {k_up}: program {prog_n}  vs  unit {", ".join(unit_ns)}')
    return bool(hits)


def audit_file(
    prog_path: str,
    unit_paths: Sequence[str] = (),
    boot_dir: str | None = None,
    check_units: bool = True,
    lib_names: Sequence[str] = (),
    fail_on_warn: bool = False,
    quiet: bool = False,
) -> bool:
    """Audit prog_path for internal, unit, and library-entrypoint 8-char collisions; return True if clean."""
    resolved = resolve_source_path(prog_path, [os.getcwd()])
    if not resolved:
        sys.stderr.write(f'audit_8char.py: file not found: {prog_path}\n')
        return False

    boot = boot_dir or os.environ.get('LISA_BOOT') or DEFAULT_BOOT
    pids = program_scope_ids(resolved)
    if not quiet:
        print(f'{os.path.basename(resolved)}: program-scope identifiers: {len(pids)}')

    uids: list[str] = []
    if check_units:
        if unit_paths:
            for u in unit_paths:
                ur = resolve_source_path(u, [os.path.dirname(resolved), os.getcwd(), boot])
                if not ur:
                    sys.stderr.write(f'audit_8char.py: unit file not found: {u}\n')
                    return False
                ids = unit_interface_ids(ur)
                if not quiet:
                    print(f'  {os.path.basename(ur)}: {len(ids)} interface identifiers')
                uids.extend(ids)
        else:
            for label, ids in resolve_used_units(resolved, boot):
                if not quiet:
                    print(f'  {label}: {len(ids)} interface identifiers')
                uids.extend(ids)

    d1 = report(pids, 'program scope vs program scope', quiet=quiet)
    d2 = cross(pids, uids, 'program scope vs the units', quiet=quiet) if check_units else False

    warned = False
    if check_units or lib_names:
        _, exp_routines = exported_entrypoint_routines(resolved)
        lib_paths = resolve_linked_libraries(resolved, boot, explicit_libs=lib_names)
        if lib_paths:
            warned = warn_library_entrypoints(
                exp_routines, lib_paths, quiet=quiet, show_on_quiet=fail_on_warn
            )

    return not (d1 or d2 or (fail_on_warn and warned))


USAGE = """\
Usage:
  audit_8char.py [options] <source_file> [unit_file ...]

Audit a Lisa Pascal source file for 8-character identifier-prefix collisions.

Required arguments:
  <source_file>         Pascal source file to audit (e.g. MYPROG.TEXT or MYPROG)

Optional arguments:
  [unit_file ...]       Explicit unit .TEXT/.OBJ files to check against (if omitted,
                        units in the source file's USES clause are resolved automatically)
  -q, --quiet           Print output only when a collision fails the audit
  --boot <dir>          Boot folder containing INTRINSIC.LIB and unit .obj files
                        (default: $LISA_BOOT or ../libs/workshop3.0)
  --libs <l1,l2,...>    Comma-separated library .OBJ files to check for duplicate linker
                        entry points (default: inferred from USES via INTRINSIC.LIB)
  --fail-on-warn        Exit with status 1 if duplicate library entry warnings are found
  --no-units            Check internal module-scope collisions only (skip USES cross-check)
  -h, --help            Show this usage message and exit

Exit status:
  0  No 8-character identifier collisions found (warnings alone exit 0 unless --fail-on-warn)
  1  Audit failed (collision detected, missing file, or no arguments given)"""


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for auditing one Pascal source file against 8-character identifier rules."""
    raw_args = list(sys.argv[1:] if argv is None else argv)
    if not raw_args:
        print(USAGE)
        return 1
    if '-h' in raw_args or '--help' in raw_args:
        print(USAGE)
        return 0

    parser = argparse.ArgumentParser(add_help=False, usage='audit_8char.py [options] <source_file> [unit_file ...]')
    parser.add_argument('source')
    parser.add_argument('units', nargs='*')
    parser.add_argument('-q', '--quiet', action='store_true')
    parser.add_argument('--boot', default=None)
    parser.add_argument('--libs', default='')
    parser.add_argument('--fail-on-warn', action='store_true')
    parser.add_argument('--no-units', action='store_true')
    args = parser.parse_args(raw_args)
    lib_list = [x for x in re.split(r'[,\s]+', args.libs.strip()) if x] if args.libs else []
    ok = audit_file(
        args.source,
        unit_paths=args.units,
        boot_dir=args.boot,
        check_units=not args.no_units,
        lib_names=lib_list,
        fail_on_warn=args.fail_on_warn,
        quiet=args.quiet,
    )
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
