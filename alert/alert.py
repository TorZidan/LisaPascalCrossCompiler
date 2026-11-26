#!/usr/bin/env python3
"""alert.py - the Lisa Workshop Menu/Phrase File Generator ('Alert' tool),
analogous to Alert.Obj (TKALERT.TEXT) in Workshop 3.0.

It compiles a human-readable alert and menu phrase source file (.TEXT) into
the binary PHRASE file read at run time by AlertMgr's InitMP / ReadAlerts /
OpenPhraseFile:

    alert.py LosSerialFtpClientAlerts.text '{T197001}'   -> {T197001}PHRASE
    alert.py MYTOOL                                      -> MYTOOLPHRASE
    alert.py +L MYTOOL                                   list tokenized input
    alert.py                                             interactive / stdin

Arguments answer the Alert tool's prompts in order: Input File Name (default
extension .TEXT) and Output File Name (default: <input stem>PHRASE; 'PHRASE'
is appended unless already present).  Missing answers take the default.
A leading +L / -L / /L argument (or answering '?' at a file prompt) sets the
tokenized-input listing option, as on the Lisa.

Both host text files and Lisa .TEXT files (1024-byte header page, CR lines,
DLE space compression) are accepted, as well as CHM Lisa_Source archive files
with trailing 0xFF markers.  Exit status is 1 on error.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
import os
import re
import struct
import sys
from typing import NoReturn, TextIO

VERSION = 'V1.0'

ALERT_LIMIT = 2000
TEXT_LIMIT = 2000
MENU_LIMIT = 30
ITEM_LIMIT = 32
TABLE_LIMIT = 300
NEST_LIMIT = 2
MAX_BUTN = 6
SIGN_STR_LENGTH = 15

KIND_WORD = 256

# Citation / control token codes (stored in alert text as 256 + ci*)
CI_L = -1       # ^L forced new line
CI_QM = -2      # ^? non-default ask button
CI_EM = -3      # ^! default ask button
CI_N = -4       # ^N cite alert number
CI_C = -5       # ^C cite last command
CI_0 = -6       # ^0..^5 cite parameter 0..5
CI_S1 = -15     # ^7..^77777 1..5-digit counter #7
CI_E1 = -20     # ^8..^88888 1..5-digit counter #8
CI_N1 = -25     # ^9..^99999 1..5-digit counter #9

# TAlertKind ordinals (shared between AlertGen and AlertMgr)
GET_PROC = 0
DRAW_PROC = 1
ASK_PROC = 2
WAIT_PROC = 3
STOP_PROC = 4
NOTE_PROC = 5
CAUTION_PROC = 6
CAUTION_OK_PROC = 7
CAUTION_CANCEL_PROC = 8
CAUTION_STOP_PROC = 9
CAUTION_NOTE_PROC = 10
CAUTION_INSIST_PROC = 11

SIGN_ORDER = [ASK_PROC, WAIT_PROC, STOP_PROC, NOTE_PROC, CAUTION_PROC]
SIGN_NAMES = {
    ASK_PROC: '?',
    WAIT_PROC: 'wait',
    STOP_PROC: 'stop',
    NOTE_PROC: 'note',
    CAUTION_PROC: 'caution',
}

# Built-in icon polygon tables (Point = record v, h: integer end)
# Each entry is (signPoints, [(h0, v0), (h1, v1), ...]); written as (v, h) big-endian.
SIGN_GEOMETRY = {
    ASK_PROC: (4, [
        (66, 44),
        (66, 10), (117, 44), (66, 78), (15, 44),
    ]),
    WAIT_PROC: (8, [
        (66, 25),
        (65, 78), (67, 78), (116, 12), (116, 11),
        (115, 10), (17, 10), (16, 11), (16, 12),
    ]),
    STOP_PROC: (8, [
        (66, 44),
        (87, 10), (117, 30), (117, 58), (87, 78),
        (45, 78), (15, 58), (15, 30), (45, 10),
    ]),
    NOTE_PROC: (4, [
        (66, 44),
        (30, 20), (102, 20), (102, 68), (30, 68),
    ]),
    CAUTION_PROC: (8, [
        (66, 68),
        (65, 7), (67, 7), (121, 79), (121, 80),
        (120, 81), (12, 81), (11, 80), (11, 79),
    ]),
}

# In TKALERT.TEXT, RdMenus allocates a 1-byte sentinel block (HAllocate(hz, 1))
# with byte 0 set to 0, then WrMenus writes 4 bytes (texts[h]^^[0] + 4) from
# the freshly-initialized AlertGenDS heap zone (0xDC fill + 0xFDDC free header).
MENU_END_SENTINEL = b'\x00\xdc\xfd\xdc'

KEYWORDS = {
    'stop', 'caution', 'note', 'wait', 'ask', 'draw',
    'ok', 'cancel', 'insist',
    '=', 'silent', 'soft', 'medium', 'loud', 'alert',
    '+', ';',
}

TOKEN_EXPLANATIONS = {
    CI_L: '<new line>',
    CI_N: '<cite number>',
    CI_C: '<cite command>',
    CI_0: '<cite param 0>',
    CI_0 - 1: '<cite param 1>',
    CI_0 - 2: '<cite param 2>',
    CI_0 - 3: '<cite param 3>',
    CI_0 - 4: '<cite param 4>',
    CI_0 - 5: '<cite param 5>',
    CI_S1: '<1-digit counter#7>',
    CI_S1 - 1: '<2-digit counter#7>',
    CI_S1 - 2: '<3-digit counter#7>',
    CI_S1 - 3: '<4-digit counter#7>',
    CI_S1 - 4: '<5-digit counter#7>',
    CI_E1: '<1-digit counter#8>',
    CI_E1 - 1: '<2-digit counter#8>',
    CI_E1 - 2: '<3-digit counter#8>',
    CI_E1 - 3: '<4-digit counter#8>',
    CI_E1 - 4: '<5-digit counter#8>',
    CI_N1: '<1-digit counter#9>',
    CI_N1 - 1: '<2-digit counter#9>',
    CI_N1 - 2: '<3-digit counter#9>',
    CI_N1 - 3: '<4-digit counter#9>',
    CI_N1 - 4: '<5-digit counter#9>',
    CI_QM: '<ask button>',
    CI_EM: '<ask default>',
}


class AlertError(Exception):
    """Fatal error raised by Mistake / IOerror in AlertGen."""


# ------------------------------------------------------------------ file utils

def strip_archive_trailing_0xff(data: bytes) -> bytes:
    """Strip the trailing 0xFF byte appended to CHM Lisa_Source text files."""
    i = data.rfind(b'\xff')
    if i >= 0 and all(b in (0x0D, 0x0A) for b in data[i + 1:]):
        return data[:i]
    return data


def read_text_lines(path: str | os.PathLike[str]) -> list[str]:
    """Read lines from a Lisa .TEXT file or a host text file."""
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
            elif c != 0:
                out.append(c)
            i += 1
        text = out.decode('latin1')
    else:
        data = strip_archive_trailing_0xff(data)
        text = data.decode('latin1').replace('\r\n', '\n').replace('\r', '\n')
    lines = text.split('\n')
    if lines and lines[-1] == '':
        lines.pop()
    # Pascal Str255 readln truncates lines at 255 characters
    return [line[:255] for line in lines]


def find_ci(path: str) -> str | None:
    """Resolve path on the host matching each component case-insensitively."""
    if not path:
        return None
    cur = '/' if path.startswith('/') else '.'
    for part in path.split('/'):
        if part in ('', '.'):
            continue
        if part == '..':
            cur = os.path.join(cur, '..')
            continue
        cand = os.path.join(cur, part)
        if not os.path.exists(cand):
            try:
                matches = [e for e in os.listdir(cur) if e.lower() == part.lower()]
            except OSError:
                return None
            if not matches:
                return None
            cand = os.path.join(cur, matches[0])
        cur = cand
    return os.path.normpath(cur)


def strip_lisa_volume(name: str) -> str:
    """Drop a leading Lisa volume prefix (-VOL-, *name, or VOL:) while keeping
    host paths intact."""
    n = name.strip()
    if n.startswith('*'):
        return n[1:]
    m = re.match(r'^-[^/-]*-(.*)$', n)
    if m:
        return m.group(1)
    if '/' not in n and ':' in n:
        return n.split(':', 1)[1]
    return n


def su_add_extension(name: str, def_ext: str) -> str:
    """SULib SUAddExtension: trailing '.' suppresses the default extension."""
    if not name:
        return name
    if name.endswith('.'):
        return name[:-1]
    if not def_ext:
        return name
    if name.upper().endswith(def_ext.upper()):
        return name
    return name + def_ext


def resolve_input_file(name: str, base_dirs: Iterable[str] | None = None) -> str | None:
    """Locate an input or $include .TEXT file on the host."""
    raw = strip_lisa_volume(name)
    if not raw:
        return None
    dirs = list(base_dirs or ['.'])
    with_ext = su_add_extension(raw, '.text')
    rel_cands = [with_ext]
    if with_ext != raw:
        rel_cands.append(raw)
    for c in list(rel_cands):
        rel_cands.append(c + '.unix.txt')
        if '/' in c:
            # CHM Lisa_Source naming: ApDm/Alert2.text -> APDM-ALERT2.TEXT.unix.txt
            flat = c.replace('/', '-')
            rel_cands.extend([flat, flat + '.unix.txt'])

    for d in dirs:
        for c in rel_cands:
            target = c if os.path.isabs(c) else os.path.join(d, c)
            found = find_ci(target)
            if found and os.path.isfile(found):
                return found
    return None


def split_input_stem(name: str) -> tuple[str, str]:
    """Split a cleaned input name into (dir_prefix, rootname) for the default
    output name, matching SUSplitFN after SUAddExtension(..., '.text')."""
    raw = strip_lisa_volume(name)
    with_ext = su_add_extension(raw, '.text')
    slash = with_ext.rfind('/')
    if slash >= 0:
        vol = with_ext[:slash + 1]
        base = with_ext[slash + 1:]
    else:
        vol = ''
        base = with_ext
    # Strip .unix.txt if a CHM archive filename was passed directly
    if base.lower().endswith('.unix.txt'):
        base = base[:-9]
    dot = base.rfind('.')
    root = base[:dot] if dot >= 0 else base
    return vol, root


# ----------------------------------------------------------------- data models

def pad_sign_str(s: str) -> bytes:
    """16-byte Pascal string[15] where bytes after length are padded with ' '."""
    b = s.encode('latin1')
    return bytes([len(b)]) + b.ljust(SIGN_STR_LENGTH, b' ')


class AlertInfo:
    """In-memory representation of TKALERT.TEXT TAlertInfo (6-byte alert descriptor)."""

    __slots__ = ('alert_number', 'alert_kind', 'f_box', 'volumes', 'text_length')

    def __init__(self, alert_number: int = 0, alert_kind: int = GET_PROC,
                 f_box: Iterable[bool] | None = None, volumes: Iterable[int] | None = None,
                 text_length: int = 0) -> None:
        """Initialize an alert descriptor with number, kind, stage box flags, volumes, and text length."""
        self.alert_number = alert_number
        self.alert_kind = alert_kind
        self.f_box = list(f_box) if f_box is not None else [False, False, False, False]
        self.volumes = list(volumes) if volumes is not None else [0, 0, 0, 0]
        self.text_length = text_length

    def copy(self) -> AlertInfo:
        """Return a copy of this AlertInfo with independent stage lists."""
        return AlertInfo(
            self.alert_number,
            self.alert_kind,
            self.f_box,
            self.volumes,
            self.text_length,
        )

    @property
    def stageless(self) -> bool:
        """Return True when this alert is a stageless GetAlert phrase (GET_PROC)."""
        return self.alert_kind == GET_PROC

    def pack(self) -> bytes:
        """Pack this descriptor into its 6-byte big-endian PHRASE file representation."""
        b2 = (
            ((self.alert_kind & 0x0F) << 4)
            | ((1 if self.f_box[0] else 0) << 3)
            | ((1 if self.f_box[1] else 0) << 2)
            | ((1 if self.f_box[2] else 0) << 1)
            | (1 if self.f_box[3] else 0)
        )
        b3 = (
            ((self.volumes[0] & 0x03) << 6)
            | ((self.volumes[1] & 0x03) << 4)
            | ((self.volumes[2] & 0x03) << 2)
            | (self.volumes[3] & 0x03)
        )
        return struct.pack('>HBBh', self.alert_number, b2, b3, self.text_length)


class MenuRecord:
    """In-memory representation of a parsed menu block (TKALERT.TEXT TmenuInfo plus item chunks)."""

    __slots__ = ('menu_id', 'enable_flags', 'menu_len', 'chunks', 'num_items')

    def __init__(self, menu_id: int) -> None:
        """Initialize an empty menu record for menu_id with all 32 item enable bits set."""
        self.menu_id = menu_id
        self.enable_flags = bytearray([0xFF, 0xFF, 0xFF, 0xFF])
        self.menu_len = 0
        self.chunks = []
        self.num_items = 0

    def disable_flag_for_item(self, item_index_1based: int) -> None:
        """Clear the initial enable bit for 1-based menu item item_index_1based."""
        # In TKALERT.TEXT: enableFlags[ItemsinMenu + 1] := FALSE
        # packed array[1..32] of boolean stores index i at byte (i-1)>>3, bit (i-1)&7.
        # For i = item_index_1based + 1, (i - 1) == item_index_1based.
        bit_pos = item_index_1based
        self.enable_flags[bit_pos >> 3] &= ~(1 << (bit_pos & 7))


# ------------------------------------------------------------------- generator

class AlertGenerator:
    """Exact port of TKALERT.TEXT (Lisa Menu/Phrase File Generator)."""

    def __init__(self, list_alerts: bool = False, out_stream: TextIO = sys.stdout) -> None:
        """Initialize generator state, alert/menu tables, include stack, and line scanner."""
        self.list_alerts = list_alerts
        self.out = out_stream

        self.parsing = 'alerts'         # 'alerts' or 'menus'
        self.its_version = 0
        self.cache_size = 0
        self.cache_bytes = 0

        self.sign_strings = {}          # TAlertSign -> 16-byte bytes
        self.butt_strings = []          # list of 16-byte bytes (0..lastButn)

        self.alerts = []                # 0-based list corresponding to Pascal 1..numAlerts
        self.texts = []                 # 0-based list of bytes
        self.alert_number = -1
        self.index = 0                  # 1-based current alert index
        self.num_alerts = 0

        self.menus = []                 # list of MenuRecord
        self.menu_count = 0             # 1-based while parsing menus
        self.items_in_menu = {}         # 1-based menu_count -> ItemsinMenu[menuCount]
        self.table = []                 # list of [com_id, menu, item]

        # Open file stack (0..NEST_LIMIT): each entry is [display_name, host_path, lines, pos]
        self.file_stack = []

        # Line scanner state (source, 1-based poss, current byte this)
        self.source = ''
        self.poss = 0
        self.this = 13
        self.single_word = ''

    def emit(self, text: str = '') -> None:
        """Write a line followed by a newline to the generator's output stream."""
        self.out.write(text + '\n')

    def emit_raw(self, text: str) -> None:
        """Write text without a trailing newline to the generator's output stream."""
        self.out.write(text)

    def mistake(self, msg: str) -> NoReturn:
        """Report a fatal alert or menu syntax error with location context and raise AlertError."""
        self.emit()
        if self.parsing == 'alerts':
            self.emit('Fatal error in Phrase File, Alert Section.\x07')
            if self.alert_number < 0:
                self.emit('At the beginning of the file')
            else:
                self.emit('At alert number %d.' % self.alert_number)
        else:
            self.emit('Fatal error in Menu File.\x07')
            if self.menu_count < 0:
                self.emit('At the beginning of the file')
            else:
                items = self.items_in_menu.get(self.menu_count, 1) - 1
                self.emit('At menu %d item %d' % (self.menu_count, items))
        self.emit()
        self.emit('Error is... %s.' % msg)
        self.emit()
        raise AlertError(msg)

    # --------------------------------------------------------- input & include

    def open_root_file(self, display_name: str, host_path: str) -> None:
        """Load the top-level input .TEXT file onto the include file stack."""
        lines = read_text_lines(host_path)
        self.file_stack = [[display_name, host_path, lines, 0]]

    def _readln_current(self) -> tuple[str, bool]:
        """Pascal readln(ucsdFiles[nestLevel], s) + eof(ucsdFiles[nestLevel]).
        Returns (s, is_eof)."""
        entry = self.file_stack[-1]
        lines, pos = entry[2], entry[3]
        if pos >= len(lines):
            return '', True
        entry[3] = pos + 1
        return lines[pos], False

    def read_next(self) -> str:
        """Read the next logical source line, expanding $include directives and skipping ';' comments."""
        while True:
            if not self.file_stack:
                self.mistake('A line with just a zero should precede EOF')
            s, is_eof = self._readln_current()
            if is_eof:
                if self.list_alerts and len(self.file_stack) > 1:
                    self.emit('(End Include File %s)' % s)
                self.file_stack.pop()
                continue
            if len(s) > 0:
                if s[0] == '$':
                    if len(s) >= 2 and s[1] == '~':
                        if self.list_alerts and len(self.file_stack) > 1:
                            self.emit('(Stop Reading Include File %s)' % s)
                        self.file_stack.pop()
                        continue
                    tilde = s.find('~')
                    if tilde < 0:
                        inc_spec = s[1:]
                        marker = ''
                    else:
                        inc_spec = s[1:tilde]
                        marker = '$' + s[tilde:]
                    inc_name = su_add_extension(inc_spec, '.text')
                    if self.list_alerts:
                        self.emit('(Begin Include File %s)' % inc_name)
                    if len(self.file_stack) > NEST_LIMIT:
                        self.mistake('Include files nested too deep')
                    cur_dir = os.path.dirname(os.path.abspath(self.file_stack[-1][1]))
                    root_dir = os.path.dirname(os.path.abspath(self.file_stack[0][1]))
                    search_dirs = ['.', cur_dir]
                    if root_dir not in search_dirs:
                        search_dirs.append(root_dir)
                    parent_dir = os.path.dirname(cur_dir)
                    if parent_dir and parent_dir not in search_dirs:
                        search_dirs.append(parent_dir)
                    inc_path = resolve_input_file(inc_name, search_dirs)
                    if inc_path is None:
                        self.mistake('Cannot open include file %s' % inc_name)
                    inc_lines = read_text_lines(inc_path)
                    self.file_stack.append([inc_name, inc_path, inc_lines, 0])
                    if marker:
                        while True:
                            ms, meof = self._readln_current()
                            if meof:
                                self.mistake('Include file does not have a marker named %s' % marker)
                            if ms == marker:
                                break
                    continue
                elif s[0] == ';':
                    continue
                elif s[0] == '~':
                    s = s[1:]
            return s

    @staticmethod
    def blank_line(s: str) -> bool:
        """Return True if s consists solely of space characters (or is empty)."""
        return all(ch == ' ' for ch in s)

    # ---------------------------------------------------------- lexical parser

    def advance(self) -> None:
        """Advance the scanner one character in self.source, setting self.this to 13 (CR) at EOL."""
        self.poss += 1
        if self.poss > len(self.source):
            self.this = 13
        else:
            self.this = ord(self.source[self.poss - 1])

    def start_parse(self, s: str) -> None:
        """Reset the line scanner to the beginning of line s."""
        self.source = s
        self.poss = 0
        self.advance()

    def include_char(self) -> None:
        """Append the current character byte to self.single_word and advance the scanner."""
        self.single_word += chr(self.this)
        self.advance()

    def parse_keyword(self) -> str:
        """Scan and validate the next alert header keyword or punctuation token, returning 'cr' at EOL."""
        self.single_word = ''
        while self.this == 32:
            self.advance()
        if self.this in (ord('+'), ord(';'), ord('=')):
            self.include_char()
        else:
            while (97 <= self.this <= 122) or (65 <= self.this <= 90):
                if self.this <= 90:
                    self.this += 32
                self.include_char()
        if len(self.single_word) == 0:
            if self.poss <= len(self.source):
                # Pascal copy(source, poss+1, length(source)-poss)
                extra = self.source[self.poss:]
                self.mistake('Extra characters: ' + extra)
            return 'cr'
        if self.list_alerts:
            self.emit_raw(self.single_word + ' ')
        if self.single_word not in KEYWORDS:
            self.mistake('Unknown keyword: ' + self.single_word)
        return self.single_word

    def parse_number(self) -> int:
        """Scan and return a non-negative decimal integer from the current line."""
        d = 0
        val = 0
        while self.this == 32:
            self.advance()
        while self.this != 32 and self.this != 13:
            if 48 <= self.this <= 57:
                val = 10 * val + (self.this - 48)
                d += 1
                self.advance()
            else:
                if self.parsing == 'alerts':
                    self.mistake('Nondigit in alert number or version number')
                else:
                    self.mistake('Nondigit in menuid or command number')
        if d == 0:
            if self.parsing == 'alerts':
                self.mistake('Alert number expected')
            else:
                self.mistake('Menuid or command number expected')
        if self.list_alerts:
            self.emit_raw('%d ' % val)
        return val

    # ----------------------------------------------------------- alert parsing

    def _equation(self, alert_info: AlertInfo) -> None:
        """Resolve an '= <alert_num>' text-sharing equation against a previously defined alert."""
        k = self.parse_number()
        if k < 1:
            self.mistake("Can't equate to 0")
        if k > self.alert_number:
            self.mistake("Can't equate to a later alert")
        for i in range(1, self.index + 1):
            if self.alerts[i - 1].alert_number == k:
                alert_info.text_length = -i
                return
        self.mistake("Can't equate to an undefined alert")

    def _parse_qualifier(self, alert_info: AlertInfo) -> None:
        """Parse the required button qualifier following a 'caution' severity keyword."""
        kw = self.parse_keyword()
        mapping = {
            'stop': CAUTION_STOP_PROC,
            'note': CAUTION_NOTE_PROC,
            'cancel': CAUTION_CANCEL_PROC,
            'ok': CAUTION_OK_PROC,
            'insist': CAUTION_INSIST_PROC,
        }
        if kw not in mapping:
            self.mistake('Caution not followed by qualifier')
        alert_info.alert_kind = mapping[kw]

    def _parse_severity(self, alert_info: AlertInfo) -> None:
        """Parse the alert severity keyword (stop, note, caution, wait, ask, draw, or stageless EOL)."""
        kw = self.parse_keyword()
        if kw == 'stop':
            alert_info.alert_kind = STOP_PROC
        elif kw == 'note':
            alert_info.alert_kind = NOTE_PROC
        elif kw == 'caution':
            self._parse_qualifier(alert_info)
        elif kw == 'wait':
            alert_info.alert_kind = WAIT_PROC
        elif kw == 'ask':
            alert_info.alert_kind = ASK_PROC
        elif kw == 'draw':
            alert_info.alert_kind = DRAW_PROC
        elif kw == 'cr':
            alert_info.alert_kind = GET_PROC
        else:
            self.mistake('Alert number not followed by severity')

    def _parse_stages(self, alert_info: AlertInfo) -> None:
        """Parse up to four semicolon-separated alert stages of volume and box visibility responses."""
        rpt = False
        responses = [[0, False] for _ in range(4)]
        for i in range(4):
            if rpt:
                responses[i] = list(responses[i - 1])
            else:
                tone_vol = 0
                f_box = False
                sound = False
                sight = False
                more = True
                while more:
                    kw = self.parse_keyword()
                    if kw == 'silent':
                        sound = True
                        tone_vol = 0
                    elif kw == 'soft':
                        sound = True
                        tone_vol = 1
                    elif kw == 'medium':
                        sound = True
                        tone_vol = 2
                    elif kw == 'loud':
                        sound = True
                        tone_vol = 3
                    elif kw == 'alert':
                        sight = True
                        f_box = True
                    elif kw == '+':
                        if sound == sight:
                            self.mistake('Bad use of +')
                    elif kw == ';':
                        if sound or sight:
                            more = False
                        else:
                            self.mistake('extra ;')
                    elif kw == 'cr':
                        more = False
                        rpt = True
                    elif kw == '=':
                        more = False
                        rpt = True
                        self._equation(alert_info)
                    else:
                        self.mistake('bad word in stage')
                if rpt and not (sound or sight):
                    self.mistake('missing stage')
                responses[i] = [tone_vol, f_box]
            alert_info.volumes[i] = responses[i][0]
            alert_info.f_box[i] = responses[i][1]

    def parse_header(self, header_line: str, alert_info: AlertInfo) -> None:
        """Parse an alert header line into alert_info, setting self.alert_number (0 terminates alerts)."""
        self.start_parse(header_line)
        self.alert_number = self.parse_number()
        if self.alert_number > 0:
            alert_info.alert_number = self.alert_number
            alert_info.text_length = 0
            alert_info.f_box = [False, False, False, False]
            self._parse_severity(alert_info)
            if not alert_info.stageless:
                if alert_info.text_length == 0:
                    self._parse_stages(alert_info)
                if self.parse_keyword() != 'cr':
                    self.mistake('too many stages')
        if self.list_alerts:
            self.emit()

    def parse_word(self, prev_kind: int) -> tuple[bool, int]:
        """Parse next word/control token from current text line.
        Returns (not_eol, kind)."""
        self.single_word = ''
        kind = prev_kind
        if self.this == ord('^'):
            self.advance()
            ch = self.this
            if ch == ord('^'):
                kind = KIND_WORD
                self.include_char()
            elif ch in (ord('L'), ord('l')):
                kind = CI_L + 256
                self.advance()
            elif ch in (ord('C'), ord('c')):
                kind = CI_C + 256
                self.advance()
            elif 48 <= ch <= 53:
                kind = CI_0 + 256 - (ch - 48)
                self.advance()
            elif ch in (ord('N'), ord('n')):
                kind = CI_N + 256
                self.advance()
            elif ch in (ord('?'), ord('!')):
                kind = (CI_QM if ch == ord('?') else CI_EM) + 256
                self.advance()
                while self.this != 13 and self.this != ord('^'):
                    self.include_char()
            elif ch in (ord('7'), ord('8'), ord('9')):
                cn = ch
                digits = 1
                self.advance()
                while self.this == cn:
                    if digits < 5:
                        digits += 1
                    self.advance()
                kind = (CI_S1 + 1 - digits - 5 * (cn - ord('7'))) + 256
            else:
                kind = KIND_WORD
                self.single_word = '^'
                self.include_char()
        else:
            kind = KIND_WORD
            while self.this not in (32, 13, ord('^')):
                self.include_char()
            while self.this == 32:
                self.include_char()
            if self.this == 13 and len(self.single_word) > 0:
                self.single_word += ' '

        eol = (len(self.single_word) == 0) and (kind == KIND_WORD)
        if self.list_alerts:
            explanation = TOKEN_EXPLANATIONS.get(kind - 256, '')
            self.emit_raw(explanation)
            self.emit_raw(self.single_word)
            if eol:
                self.emit()
        return (not eol), kind

    def parse_text(self, text_line: str, alert_text: bytearray) -> None:
        """Tokenize one alert body line and append length-prefixed words and '^' control codes to alert_text."""
        def append_token(wd_len: int, s: str) -> None:
            """Append a single length/control byte and optional Latin-1 word bytes, enforcing TEXT_LIMIT."""
            if len(alert_text) + 1 + len(s) > TEXT_LIMIT:
                self.mistake('Text too long')
            alert_text.append(wd_len & 0xFF)
            if s:
                alert_text.extend(s.encode('latin1'))

        self.start_parse(text_line)
        kind = KIND_WORD
        while True:
            more, kind = self.parse_word(kind)
            if not more:
                break
            if kind != KIND_WORD:
                append_token(kind, '')
            if kind in (KIND_WORD, CI_QM + 256, CI_EM + 256):
                append_token(len(self.single_word), self.single_word)

    def rd_alerts(self) -> None:
        """Read the version, optional cache parameters, sign/button labels, and all alert definitions."""
        text_line = self.read_next()
        self.start_parse(text_line)
        self.its_version = self.parse_number()
        if self.list_alerts:
            self.emit('Version number = %d' % self.its_version)

        text_line = self.read_next()
        self.start_parse(text_line)
        if 48 <= self.this <= 57:
            self.cache_size = self.parse_number()
            if self.list_alerts:
                self.emit('cacheSize = %d' % self.cache_size)

            text_line = self.read_next()
            self.start_parse(text_line)
            self.cache_bytes = self.parse_number()
            if self.list_alerts:
                self.emit('cacheBytes = %d' % self.cache_bytes)

            text_line = self.read_next()
            self.start_parse(text_line)

        for idx, p in enumerate(SIGN_ORDER):
            if idx > 0:
                text_line = self.read_next()
            if self.list_alerts:
                self.emit('%s = %s' % (SIGN_NAMES[p], text_line))
            if len(text_line) > SIGN_STR_LENGTH:
                self.mistake('Sign name too long')
            self.sign_strings[p] = pad_sign_str(text_line)

        d = 0
        while True:
            text_line = self.read_next()
            if self.blank_line(text_line):
                break
            if d > MAX_BUTN:
                self.mistake('Too many Butns defined')
            if self.list_alerts:
                if d == 0:
                    self.emit('cancel = %s' % text_line)
                elif d == 1:
                    self.emit('ok = %s' % text_line)
                else:
                    self.emit('   %s' % text_line)
            if len(text_line) > SIGN_STR_LENGTH:
                self.mistake('Butn name too long')
            self.butt_strings.append(pad_sign_str(text_line))
            d += 1

        if len(self.butt_strings) < 2:
            self.mistake('Require nonblank text for cancel and ok')

        alert_info = AlertInfo()
        while True:
            while True:
                alert_header = self.read_next()
                if not self.blank_line(alert_header):
                    break
            self.parse_header(alert_header, alert_info)
            if self.alert_number == 0:
                break

            overriding = False
            if self.index > 0 and self.alert_number <= self.alerts[self.num_alerts - 1].alert_number:
                for i in range(1, self.num_alerts + 1):
                    if self.alerts[i - 1].alert_number == self.alert_number:
                        self.index = i
                        overriding = True
                if not overriding:
                    self.mistake('Alert numbers must appear in ascending order')
            if not overriding:
                self.index = self.num_alerts + 1
                self.num_alerts = self.index
                if self.index > ALERT_LIMIT:
                    self.mistake('More than 2000 alerts!')
                self.alerts.append(alert_info.copy())
                self.texts.append(b'')
            else:
                self.alerts[self.index - 1] = alert_info.copy()

            cur_alert = self.alerts[self.index - 1]
            equated = cur_alert.text_length < 0
            alert_text = bytearray()
            while True:
                text_line = self.read_next()
                if self.blank_line(text_line):
                    break
                if cur_alert.stageless:
                    if self.list_alerts:
                        self.emit(text_line)
                    if len(alert_text) > 0:
                        self.mistake('Only one line of text allowed when no severity')
                    raw = text_line.encode('latin1')
                    alert_text.append(len(raw))
                    alert_text.extend(raw)
                else:
                    self.parse_text(text_line, alert_text)

            if self.list_alerts:
                self.emit()

            needs_text = any(cur_alert.f_box) or cur_alert.stageless
            if equated:
                if len(alert_text) > 0:
                    self.mistake('there should not be text after an equated alert')
                text_provided = -self.index
                while text_provided < 0:
                    eq_index = -text_provided
                    text_provided = self.alerts[eq_index - 1].text_length
                if text_provided == 0 and needs_text:
                    self.mistake("the equated alert doesn't have any text")
                self.texts[self.index - 1] = b''
            else:
                if len(alert_text) == 0 and needs_text:
                    self.mistake('no text for alert')
                cur_alert.text_length = len(alert_text)
                self.texts[self.index - 1] = bytes(alert_text)

        self.emit()
        self.emit('All %d alerts read.' % self.num_alerts)

    # ------------------------------------------------------------ menu parsing

    def rd_menus(self) -> None:
        """Read all menu definitions and command mappings up to the terminating menu ID 0."""
        self.emit('Reading the menus.')
        self.menu_count = 1
        item_count = 1
        self.table = []

        while True:
            text_line = self.read_next()
            if not self.blank_line(text_line):
                break

        while True:
            self.items_in_menu[self.menu_count] = 0
            self.start_parse(text_line)
            menu_id = self.parse_number()
            if menu_id == 0:
                break
            if self.menu_count > MENU_LIMIT:
                self.mistake('Too many menus')

            menu = MenuRecord(menu_id)
            title = self.read_next()
            if self.list_alerts:
                self.emit(title)
            title_bytes = title.encode('latin1')
            menu.chunks.append(bytes([len(title_bytes)]) + title_bytes)
            menu.menu_len = len(title_bytes) + 1
            self.items_in_menu[self.menu_count] = 1

            while True:
                text_line = self.read_next()
                self.start_parse(text_line)
                length = len(text_line)
                if length == 0:
                    break
                if item_count > TABLE_LIMIT:
                    self.mistake('Too many menu items')

                cur_item_idx = self.items_in_menu[self.menu_count]
                sharp = text_line.find('#') + 1  # 1-based pos('#', textline)
                if sharp == 0 or sharp < length - 8 or sharp == length:
                    com_id = -1
                else:
                    self.poss = sharp
                    self.advance()
                    com_id = self.parse_number()
                    length = sharp - 1

                if com_id == 0 or (
                    text_line[0] in ('.', '-') and length == 1 and com_id <= 0
                ):
                    menu.disable_flag_for_item(cur_item_idx)

                # Extract('\', styleChar) then Extract('/', appleChar) on prefix of length
                work = text_line[:length]
                style_char = ' '
                if len(work) > 2 and work[-2] == '\\':
                    c = work[-1]
                    if 'a' <= c <= 'z':
                        c = c.upper()
                    style_char = c
                    work = work[:-2]

                apple_char = ' '
                if len(work) > 2 and work[-2] == '/':
                    c = work[-1]
                    if 'a' <= c <= 'z':
                        c = c.upper()
                    apple_char = c
                    work = work[:-2]

                length = len(work)
                if self.list_alerts:
                    self.emit(work)

                work_bytes = work.encode('latin1')
                item_bytes = (
                    bytes([length])
                    + work_bytes
                    + bytes([ord(apple_char), 0, ord(style_char)])
                )
                menu.chunks.append(item_bytes)
                menu.menu_len += length + 4

                self.table.append([com_id, self.menu_count, cur_item_idx])
                item_count += 1
                self.items_in_menu[self.menu_count] = cur_item_idx + 1

            menu.chunks.append(MENU_END_SENTINEL)
            menu.menu_len += 4
            menu.num_items = self.items_in_menu[self.menu_count] - 1

            if self.items_in_menu[self.menu_count] > ITEM_LIMIT:
                self.mistake('Too many menu items in one menu')

            if self.list_alerts:
                self.emit('Menu %d has %d items' % (self.menu_count, menu.num_items))
                self.emit('and is %d bytes long' % menu.menu_len)
                self.emit()

            self.menus.append(menu)
            self.menu_count += 1

            while True:
                text_line = self.read_next()
                if not self.blank_line(text_line):
                    break

        self.menu_count -= 1
        if self.menu_count > 0:
            self.emit('All %d menus read.' % self.menu_count)
        else:
            self.emit('No menus in file.')

    def sort_table(self) -> None:
        """Exact port of TKALERT.TEXT sortTable: sort commands with comId > 0
        ascending and drop comId <= 0."""
        n = len(self.table)
        for i in range(n - 1):
            for j in range(i + 1, n):
                ci, cj = self.table[i][0], self.table[j][0]
                if ci <= 0 or ci > cj > 0:
                    self.table[i], self.table[j] = self.table[j], self.table[i]
        keep = 0
        for i in range(n, 0, -1):
            if self.table[i - 1][0] > 0:
                keep = i
                break
        self.table = self.table[:keep]

    # ----------------------------------------------------------- binary writer

    def build_phrase_bytes(self) -> bytes:
        """Serialize menus, command table, alert headers, icon polygons, texts, and checksum to bytes."""
        buf = bytearray()

        if len(self.menus) > 0:
            self.emit('writing menus')
            buf += struct.pack('>H', len(self.menus))
            for menu in self.menus:
                mlen = menu.menu_len
                was_odd = bool(mlen & 1)
                if was_odd:
                    mlen += 1
                buf += struct.pack('>H4sH', menu.menu_id, bytes(menu.enable_flags), mlen)
                for chunk in menu.chunks:
                    buf += chunk
                if was_odd:
                    buf.append(1)       # writeNext(@wasOdd, 1) where TRUE = 1
            buf += struct.pack('>H', len(self.table))
            for com_id, m_idx, i_idx in self.table:
                buf += struct.pack('>hBB', com_id, m_idx, i_idx)

            self.emit('writing alert header')
            buf += struct.pack('>HH', self.cache_size, self.cache_bytes)

        self.emit('writing alerts')
        buf += struct.pack('>H', self.its_version)
        for p in SIGN_ORDER:
            buf += self.sign_strings[p]
            npts, pts = SIGN_GEOMETRY[p]
            buf += struct.pack('>H', npts)
            for h, v in pts:
                buf += struct.pack('>hh', v, h)     # Point = record v, h: integer end

        last_butn = len(self.butt_strings) - 1
        buf += struct.pack('>H', last_butn)
        for bs in self.butt_strings:
            buf += bs

        buf += struct.pack('>H', self.num_alerts)
        for a in self.alerts:
            buf += a.pack()
        for a, t in zip(self.alerts, self.texts):
            if a.text_length > 0:
                buf += t

        raw_ck = (50 - (sum(buf) & 0xFF)) & 0xFF
        signed_ck = raw_ck - 256 if raw_ck >= 128 else raw_ck
        self.emit()
        self.emit('Checksum = %d' % signed_ck)
        buf.append(raw_ck)
        return bytes(buf)

    def wr_measure(self) -> bool:
        """Print alert cache memory statistics and return True if configured cache values are below suggested minimums."""
        sizeof_alert_rec = 10
        hz_blk_ovhd = 20
        sizeof_cached_alert = 14
        tot = 0
        big = 0
        for i, a in enumerate(self.alerts, 1):
            if i != 2:
                length = a.text_length
                tot += length
                if length > big:
                    big = length
        # Pascal integer div truncates toward zero
        avga = int(tot / self.num_alerts) + hz_blk_ovhd + 1
        lrga = big + hz_blk_ovhd + 1
        ovhd = sizeof_alert_rec + sizeof_cached_alert + self.alerts[1].text_length + 3 * hz_blk_ovhd
        insz = (1 + self.num_alerts) * 6 + hz_blk_ovhd

        self.emit()
        self.emit('MINIMUM cacheSize value = overhead + cacheFactor*cacheSize + indexSize + largestAlert')
        self.emit()
        self.emit('overhead = %d' % ovhd)
        self.emit('cacheFactor = %d' % sizeof_cached_alert)
        self.emit('indexSize = %d' % insz)
        self.emit('Average alert = %d' % avga)
        self.emit('Largest alert = %d' % lrga)
        self.emit()

        sugg = ovhd + sizeof_cached_alert * 3 + (insz + 120) + max(lrga, 500) + avga * 3 + 300
        sugg = (sugg - (sugg % 100)) + 100

        self.emit("The suggested value for 'cache size' is 3.")
        self.emit("The suggested value for 'cache bytes' is %d." % sugg)
        self.emit('     (NOTE: the sugested numbers take into account alerts used for printing,')
        self.emit('           arguments to alerts, and extra space for expansion.')
        self.emit()

        warned = False
        if self.cache_size > 0:
            if self.cache_size < 3:
                self.emit('Your value of cache size (%d) is less than recommended.' % self.cache_size)
                warned = True
            if self.cache_bytes < sugg:
                self.emit('Your value of cache bytes (%d) is less than recommended.' % self.cache_bytes)
                warned = True
            if warned:
                self.emit('\x07You might want to increase the value(s) an re-run this program.')
        return warned

    def compile(self, display_input_name: str, host_input_path: str) -> tuple[bytes, bool]:
        """Parse input file and return (phrase_bytes, warned_small_cache)."""
        self.alert_number = -1
        self.index = 0
        self.num_alerts = 0
        self.menu_count = 0
        self.cache_size = 0
        self.cache_bytes = 0
        self.parsing = 'alerts'

        self.open_root_file(display_input_name, host_input_path)
        self.rd_alerts()

        if self.cache_size == 0:
            self.emit('No cache size/cache bytes in input file; assuming old file format (no menus)')
        else:
            self.parsing = 'menus'
            self.rd_menus()
            self.sort_table()

        self.file_stack.clear()
        self.alert_number = -1

        if self.num_alerts <= 0:
            self.mistake('There are no alerts in the file.')

        self.alert_number = self.alerts[-1].alert_number
        if self.alerts[0].alert_number != 1 or self.alerts[0].alert_kind == GET_PROC:
            self.mistake('You forgot to define alert #1 as the default non-GetAlert.')
        if self.num_alerts < 2 or self.alerts[1].alert_number != 2:
            self.mistake('You forgot to define alert #2 as the Swan Song alert.')
        elif self.alerts[1].text_length < 1:
            self.mistake('Alert #2 must contain text.')

        data = self.build_phrase_bytes()
        warned = self.wr_measure()
        return data, warned


# --------------------------------------------------------------- CLI & dialog

class Dialog:
    """Answers prompts from command-line arguments (echoed, as in Workshop)
    or interactively from stdin."""

    def __init__(self, args: Iterable[str]) -> None:
        """Initialize prompt reader with optional pre-supplied command-line answers."""
        self.args = list(args)
        self.from_args = bool(args)

    def ask(self, prompt: str) -> tuple[str, bool]:
        """Display prompt and return (answer, is_eof) from queued CLI arguments or stdin."""
        sys.stdout.write(prompt)
        sys.stdout.flush()
        if self.from_args:
            ans = self.args.pop(0) if self.args else ''
            print(ans)
            return ans, False
        line = sys.stdin.readline()
        if not line:
            print()
            return '', True
        ans = line.rstrip('\r\n')
        if not sys.stdin.isatty():
            print(ans)
        return ans, False

    def wait_space(self) -> None:
        """Pause for a line from stdin when running interactively without CLI arguments."""
        if self.from_args or not sys.stdin.isatty():
            return
        sys.stdout.write('Type SPACE to continue.')
        sys.stdout.flush()
        sys.stdin.readline()


def do_options(dialog: Dialog, list_alerts: bool) -> bool:
    """Prompt for the '?' interactive options menu and return the updated list_alerts flag."""
    print()
    default_str = 'Yes' if list_alerts else 'No'
    ans, eof = dialog.ask(
        'Do you want to list tokenized input to the console? (Y or N)  [%s] ' % default_str
    )
    print()
    if eof or ans.strip() == '':
        return list_alerts
    return ans.strip()[0].upper() in ('Y', 'T')


def main(argv: Sequence[str]) -> int:
    """Run the Lisa Menu/Phrase File Generator CLI and return a process exit code."""
    list_alerts = False
    args = list(argv)

    # Leading CLI option switches (+L, -L, /L)
    while args and args[0].upper() in ('+L', '-L', '/L'):
        sw = args.pop(0).upper()
        list_alerts = sw in ('+L', '/L')

    print('Lisa Menu/Phrase File Generator (%s)' % VERSION)
    print()
    print('Type ? to set the options.')
    print()

    dialog = Dialog(args)

    while True:
        ans, eof = dialog.ask('Input File Name [.TEXT] ')
        s = ans.strip()
        if eof or s == '' or s.startswith('\x1b'):
            return 0
        if s == '?':
            list_alerts = do_options(dialog, list_alerts)
            continue

        vol_dir, rootname = split_input_stem(s)
        if not rootname:
            return 0

        disp_in = su_add_extension(strip_lisa_volume(s), '.text')
        src_path = resolve_input_file(s)
        if src_path is None:
            print('Error opening input file.')
            print(disp_in)
            print()
            if dialog.from_args or not sys.stdin.isatty():
                return 1
            continue
        break

    def_out_display = '%s%sPHRASE' % (vol_dir, rootname)
    while True:
        out_ans, eof = dialog.ask('Output File Name [%s] ' % def_out_display)
        if eof and not dialog.from_args:
            return 1
        os_str = out_ans.strip()
        if os_str.startswith('\x1b'):
            return 1
        if os_str == '?':
            list_alerts = do_options(dialog, list_alerts)
            continue
        if os_str == '':
            out_name = def_out_display
        else:
            cleaned_out = strip_lisa_volume(os_str)
            out_name = su_add_extension(cleaned_out, 'PHRASE')
        break

    out_path = find_ci(out_name) or out_name

    gen = AlertGenerator(list_alerts=list_alerts)
    try:
        phrase_bytes, warned = gen.compile(disp_in, src_path)
        if warned:
            dialog.wait_space()
        os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
        with open(out_path, 'wb') as f:
            f.write(phrase_bytes)
    except AlertError:
        dialog.wait_space()
        return 1
    except OSError as exc:
        print('Error writing output file %s: %s' % (out_path, exc))
        return 1

    print()
    print('File %s generated successfully' % out_name)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
