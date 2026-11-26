"""Host runtime and library units for the Apple Lisa Pascal compiler in Python.

Implements the host versions of the Lisa library units the compiler uses
(LisaIO, StdUnit, IOPrimitives, ProgComm, PasDefs, FileIO, ObjIO, IUMan,
ObjInter, FPLib, Dates, Times, HideSysCall, PaslibCall, HWInt) and
numeric/string/set helpers matching 16-bit/32-bit Apple Lisa Pascal.
"""

from __future__ import annotations

import datetime
import enum
import math
import os
import struct
import sys
import time
from typing import Any, Callable, Optional


class AbortCompilation(Exception):
    """Raised to emulate global GOTO 999 to the Finalize label."""


class PasHaltException(Exception):
    """Raised by PasDefs.PasHalt."""


# ---- Integer, float, set, and Pascal string helpers ----

def i8(x: int) -> int:
    """Wrap an integer to signed 8-bit two's-complement range (-128..127), matching FileIO.FileByte."""
    return ((int(x) + 128) & 0xFF) - 128


def u8(x: int) -> int:
    """Mask an integer to unsigned 8-bit range (0..255), matching Lisa Pascal Byte."""
    return int(x) & 0xFF


def i16(x: int) -> int:
    """Wrap an integer to signed 16-bit two's-complement range (-32768..32767), matching Lisa Pascal Integer."""
    return ((int(x) + 32768) & 0xFFFF) - 32768


def u16(x: int) -> int:
    """Mask an integer to unsigned 16-bit word range (0..65535)."""
    return int(x) & 0xFFFF


def i32(x: int) -> int:
    """Wrap an integer to signed 32-bit two's-complement range, matching Lisa Pascal LongInt."""
    return ((int(x) + 2147483648) & 0xFFFFFFFF) - 2147483648


def u32(x: int) -> int:
    """Mask an integer to unsigned 32-bit longword range (0..4294967295)."""
    return int(x) & 0xFFFFFFFF


def pdiv(a: int, b: int) -> int:
    """Pascal DIV: integer division truncating toward zero."""
    if b == 0:
        raise ZeroDivisionError("Pascal DIV by zero")
    q = abs(int(a)) // abs(int(b))
    return -q if (a < 0) ^ (b < 0) else q


def pmod(a: int, b: int) -> int:
    """Pascal MOD: remainder with sign matching dividend (a - (a DIV b) * b)."""
    return int(a) - pdiv(a, b) * int(b)


def odd(x: int) -> bool:
    """Pascal Odd(x): return True when the least significant bit of x is 1."""
    return (int(x) & 1) != 0


def f32(x: float) -> float:
    """Round a Python float to IEEE-754 32-bit Single precision."""
    try:
        return struct.unpack('>f', struct.pack('>f', float(x)))[0]
    except OverflowError:
        return math.copysign(float('inf'), float(x))


def f32_to_be_bytes(x: float) -> bytes:
    """Big-endian 4-byte IEEE-754 Single representation."""
    try:
        return struct.pack('>f', float(x))
    except OverflowError:
        return struct.pack('>f', math.copysign(float('inf'), float(x)))


def p_f32(s: str) -> float:
    """FPLib.p_f32: decimal string -> IEEE-754 32-bit Single."""
    t = s.strip()
    if not t:
        return 0.0
    try:
        return f32(float(t))
    except ValueError:
        return 0.0


def pround(x: float) -> int:
    """Pascal Round(): round-to-nearest-even -> LongInt."""
    return int(round(float(x)))


def ptrunc(x: float) -> int:
    """Pascal Trunc(): truncate toward zero -> LongInt."""
    return int(float(x))


def alfa8(s: str = '        ') -> str:
    """Normalize to an 8-character space-padded Alfa string."""
    if len(s) >= 8:
        return s[:8]
    return s + ' ' * (8 - len(s))


def ppos(sub: str, s: str) -> int:
    """1-based Pascal Pos(sub, s); returns 0 if not found."""
    if not sub:
        return 0
    idx = s.find(sub)
    return idx + 1 if idx >= 0 else 0


def pcopy(s: str, start: int, count: int) -> str:
    """1-based Pascal Copy(s, start, count)."""
    if count <= 0:
        return ''
    i = max(1, int(start)) - 1
    if i >= len(s):
        return ''
    return s[i:i + int(count)]


def pdelete(s: str, index: int, count: int) -> str:
    """1-based Pascal Delete(s, index, count) returning the updated string."""
    if index < 1 or index > len(s) or count <= 0:
        return s
    return s[:index - 1] + s[index - 1 + count:]


def pinsert(src: str, dst: str, index: int, max_len: int = 255) -> str:
    """1-based Pascal Insert(src, dst, index) returning the updated string."""
    idx = max(1, min(len(dst) + 1, int(index))) - 1
    res = dst[:idx] + src + dst[idx:]
    return res[:max_len]


def pset_ch(s: str, index: int, ch: str) -> str:
    """1-based character assignment S[index] := ch."""
    idx = index - 1
    if idx < 0:
        return s
    if idx >= len(s):
        s = s + ' ' * (idx - len(s) + 1)
    return s[:idx] + ch[0] + s[idx + 1:]


def pget_ch(s: str, index: int) -> str:
    """1-based character read S[index] (returns '\\x00' if out of range)."""
    idx = index - 1
    if 0 <= idx < len(s):
        return s[idx]
    return '\x00'


class RegMask:
    """Variant overlay of iMask: Integer (16-bit signed) and sMask: SET OF 0..15."""

    __slots__ = ('sMask',)

    def __init__(self, initial_mask: int = 0) -> None:
        """Initialize the register mask from an optional 16-bit integer bitmask."""
        self.sMask: set[int] = set()
        if initial_mask:
            self.iMask = initial_mask

    @property
    def iMask(self) -> int:
        """Return the 0..15 register set packed as a signed 16-bit MC68000 register mask."""
        m = 0
        for b in self.sMask:
            if 0 <= b <= 15:
                m |= (1 << b)
        return i16(m)

    @iMask.setter
    def iMask(self, val: int) -> None:
        """Unpack a 16-bit register mask word into the 0..15 bit set."""
        u = u16(val)
        self.sMask = {b for b in range(16) if (u & (1 << b)) != 0}

    def copy(self) -> 'RegMask':
        """Return an independent shallow copy of this register mask."""
        r = RegMask()
        r.sMask = set(self.sMask)
        return r


# ---- Enums from LisaIO / StdUnit / IOPrimitives / ObjIO ----

class LisaCloseOpt(enum.IntEnum):
    """Close disposition modes for LisaIO untyped and text files (NORMAL, LOCK, PURGE, CRUNCH)."""
    NORMAL = 0
    LOCK = 1
    PURGE = 2
    CRUNCH = 3


class PromptState(enum.IntEnum):
    """Result states returned by StdUnit interactive/command-line prompt routines."""
    SUDefault = 0
    SUEscape = 1
    SUNone = 2
    SUOptions = 3
    SUValid = 4
    SUInvalid = 5


class ErrTextRet(enum.IntEnum):
    """Status codes returned by StdUnit error-message file lookup (SUGetErrText)."""
    SUOk = 0
    SUBadEFOpen = 1
    SUBadEFRead = 2
    SUErrNNotFound = 3


class ConvNState(enum.IntEnum):
    """Validation states for StdUnit decimal string-to-integer conversions."""
    SUValidN = 0
    SUNoN = 1
    SUBadN = 2
    SUNOverFlow = 3


class IOModes(enum.IntEnum):
    """Access modes (read or write) for IOPrimitives buffered streams."""
    IORead = 0
    IOWrite = 1


class IOCloseKind(enum.IntEnum):
    """Close disposition modes for IOPrimitives file control blocks."""
    IONormal = 0
    IOLock = 1
    IOPurge = 2
    IOCrunch = 3


class IODevType(enum.IntEnum):
    """Device classifications for IOPrimitives streams (block file, keyboard, console, printer)."""
    IOBlkDev = 0
    IOKbDev = 1
    IOConsDev = 2
    IOPrDev = 3


class BlockType(enum.IntEnum):
    """Record type tags for invariant blocks in Lisa Workshop .OBJ and INTRINSIC.LIB files."""
    ModuleName = 0
    EndBlock = 1
    EntryPoint = 2
    External = 3
    StartAddress = 4
    CodeBlock = 5
    Relocation = 6
    CommonReloc = 7
    CommonDef = 8
    ShortExternal = 9
    DInitDef = 10
    DInitData = 11
    DInitRef = 12
    DInitDRef = 13
    QuickLoad = 14
    OldExecutable = 15
    LibModule = 16
    LibEntry = 17
    UnitBlock = 18
    InterfLoc = 19
    PhysicalExec = 20
    Executable = 21
    VersionCtrl = 22
    SegmentTable = 23
    UnitTable = 24
    SegLocation = 25
    OldUntLoc = 26
    StringBlock = 27
    MACExecutable = 28
    PackedCode = 29
    PackTable = 30
    DInitCRef = 31
    UnitLocation = 32
    OSData = 33
    DebugSymbols = 34
    DebugEntry = 35
    DebugCommon = 36
    EOFMark = 37
    UnknownBlock = 38


class VariantType(enum.IntEnum):
    """Sub-record variant tags for variable-length entries inside Lisa .OBJ blocks."""
    NoVariant = 0
    RefVariant = 1
    ShortRef = 2
    ModVariant = 3
    Comments = 4
    SegVariant = 5
    UnitVariant = 6
    IntfLocVariant = 7
    SegLocVariant = 8
    UnitLocVariant = 9
    OldULVariant = 10
    StringVariant = 11
    SftSysVariant = 12
    JumpTVariant = 13
    JTSegVariant = 14
    ObjectCode = 15
    ProcHeap = 16
    OldJumpTV = 17
    OldJTSegV = 18
    MACJumpTV = 19
    Jump4TV = 20
    UnknownVariant = 21


class ObjFileType(enum.IntEnum):
    """Object file role classifications stored in ObjIO VersionCtrl blocks."""
    OldObjFile = 0
    IUDirectory = 1
    IULibrary = 2
    MainProg = 3
    IntrinUnit = 4
    RegUnit = 5
    RegModule = 6
    DbgFile = 7
    PITFile = 8


# ---- Constants from StdUnit / IOPrimitives / ObjIO / PasDefs ----

SUMaxStrLeng = 255
SUNullStr = ''
SUSpace = ' '
SUOrdCR = 13
SUMaxPNLeng = 66
SUMaxVNLeng = 33
SUMaxFNLeng = 32
SUVolSuffix = '-'

SUBell = '\x07'
SUBackSpace = '\x08'
SUCr = '\x0d'
SUTab = '\x09'
SUEsc = '\x1b'
SUDle = '\x10'
SUNul = '\x00'

IOMaxStr = 132
IOMaxStP1 = 133
IOBlkSize = 6
IOByteSize = 3072
IOBytSizeM1 = 3071
IOIncMax = 5
IOPvtErr = 32000
IOOpnErr = 32001
IOIncErr = 32002
IOBfrErr = 32003
IOMem1Err = 32004
IOMem2Err = 32005
IOEndfile = '\x03'
IONewline = '\x0d'

NameStrLen = 8
MaxLStringLen = 80
TMAXSEGS = 4096
TMAXUNITS = 4096
TMAXFILES = 1024
TMAXSYSS = 127
IU_MAXUNITS = 512


# ---- File and Object File structures ----

class UntypedFile:
    """Emulates Pascal untyped FILE opened via LisaIO."""

    def __init__(self) -> None:
        """Initialize an unopened 512-byte block file slot (disk-backed or in-memory .TEXT image)."""
        self.in_use: bool = False
        self.is_image: bool = False
        self.image: bytes = b''
        self.host_path: str = ''
        self.fp = None
        self.next_block: int = 0


class TextFile:
    """Emulates Pascal Text file opened via LisaIO."""

    def __init__(self) -> None:
        """Initialize an unopened LisaIO text stream."""
        self.is_open: bool = False
        self.is_console: bool = False
        self.host_path: str = ''
        self.fp = None

    def write(self, *items: Any) -> None:
        """Write stringified items to the host file or standard output when bound to CONSOLE:."""
        s = ''.join(str(x) for x in items)
        if self.is_console or self.fp is None:
            sys.stdout.write(s)
        else:
            self.fp.write(s)

    def writeln(self, *items: Any) -> None:
        """Write stringified items followed by a newline."""
        self.write(*items, '\n')


class IOFCB:
    """Emulates IOPrimitives IOFCB."""

    def __init__(self) -> None:
        """Initialize a 3072-byte (6-block) buffered file control block and pending atomic-write paths."""
        self.Filename: str = ''
        self.DevType: IODevType = IODevType.IOBlkDev
        self.fp = None
        self.LineNbr: int = 0
        self.Bufr: bytearray = bytearray(IOByteSize)
        self.BufrCp: int = 0
        self.BlkNbr: int = 0
        self.CurrLine: str = ''
        self.CurrLen: int = 0
        self.Mode: IOModes = IOModes.IORead
        self.LastBlk: int = 0
        self.LastByte: int = 0
        self.Eol: bool = False
        self.EndPage: int = 0
        self._pend_final: Optional[str] = None
        self._pend_temp: Optional[str] = None


class FileDesc:
    """Emulates FileIO.FileDesc."""

    def __init__(self, n_blocks: int = 0) -> None:
        """Initialize a byte-addressed ObjIO/FileIO file descriptor."""
        self.fp = None
        self.OldFile: bool = False
        self.MaxBlks: int = n_blocks
        self.host_name: str = ''
        self.is_open: bool = False


class ObjDesc:
    """Emulates ObjIO.ObjDesc."""

    def __init__(self, n_blocks: int = 4) -> None:
        """Initialize an ObjIO object file handle tracking the next sequential block offset."""
        self.ObjFile: FileDesc = FileDesc(n_blocks)
        self.NextBlock: int = 0


class ObjBlock:
    """Emulates ObjIO.ObjBlock with all variant sub-records flattened cleanly."""

    def __init__(self) -> None:
        """Initialize a blank ObjIO invariant block record with default fields for all block types."""
        self.Variant: VariantType = VariantType.NoVariant
        self.NrVariants: int = 0
        self.BlockHeader: BlockType = BlockType.UnknownBlock
        # bModuleName
        self.ModuleName: str = '        '
        self.SegmentName: str = '        '
        self.CSize: int = 0
        # bEntryPoint / bExternal / bShortExternal
        self.LinkName: str = '        '
        self.UserName: str = '        '
        self.Loc: int = 0
        # bStartAddress
        self.Start: int = 0
        self.GSize: int = 0
        # bCodeBlock
        self.Addr: int = 0
        # bRelocation / bInterfLoc / bOSData
        self.Reserved: int = 0
        # bCommonReloc / bCommonDef
        self.CommonName: str = '        '
        self.DSize: int = 0
        # bUnitBlock
        self.UnitName: str = '        '
        self.CodeAddr: int = 0
        self.TextAddr: int = 0
        self.TextSize: int = 0
        self.GlobalSize: int = 0
        self.UnitType: int = 0
        # bVersionCtrl
        self.sysNum: int = 0
        self.minSys: int = 0
        self.maxSys: int = 0
        self.Reserv1: int = 0
        self.Reserv2: int = 0
        self.Reserv3: int = 0
        # counts
        self.nSegments: int = 0
        self.nUnits: int = 0
        self.maxunit: int = 0
        self.nStrings: int = 0


class ObjVarBlock:
    """Emulates ObjIO.ObjVarBlock."""

    def __init__(self) -> None:
        """Initialize a blank ObjIO variant sub-record holder."""
        self.VarHeader: VariantType = VariantType.NoVariant
        self.bRefVariant: int = 0
        self.bShortRef: int = 0
        self.bModVariant: int = 0
        # bIntfLocVariant
        self.UnitName: str = '        '
        self.IfLoc: int = 0


class OldULVariant:
    """Emulates ObjIO.iOldULVariant."""

    def __init__(self, unit_name: str = '        ', unit_num: int = 0,
                 file_num: int = 0, unit_type: int = 0, data_size: int = 0) -> None:
        """Initialize a 16-byte INTRINSIC.LIB UnitLocation directory entry."""
        self.UnitName: str = unit_name
        self.UnitNumber: int = unit_num
        self.FileNumber: int = file_num
        self.UnitType: int = unit_type
        self.DataSize: int = data_size


_HEADER_BYTES = {
    BlockType.ModuleName: 0x80,
    BlockType.EndBlock: 0x81,
    BlockType.EntryPoint: 0x82,
    BlockType.External: 0x83,
    BlockType.StartAddress: 0x84,
    BlockType.CodeBlock: 0x85,
    BlockType.Relocation: 0x86,
    BlockType.CommonReloc: 0x87,
    BlockType.CommonDef: 0x88,
    BlockType.ShortExternal: 0x89,
    BlockType.UnitBlock: 0x92,
    BlockType.InterfLoc: 0x93,
    BlockType.VersionCtrl: 0x99,
    BlockType.SegmentTable: 0x9A,
    BlockType.UnitTable: 0x9B,
    BlockType.SegLocation: 0x9C,
    BlockType.UnitLocation: 0x9D,
    BlockType.StringBlock: 0x9E,
    BlockType.EOFMark: 0x00,
}

_BYTE_TO_BLOCK = {v: k for k, v in _HEADER_BYTES.items()}

_INVAR_SIZES = {
    BlockType.ModuleName: 20,
    BlockType.EndBlock: 4,
    BlockType.EntryPoint: 20,
    BlockType.External: 16,
    BlockType.StartAddress: 8,
    BlockType.CodeBlock: 4,
    BlockType.Relocation: 2,
    BlockType.CommonReloc: 8,
    BlockType.CommonDef: 12,
    BlockType.ShortExternal: 16,
    BlockType.UnitBlock: 26,
    BlockType.InterfLoc: 2,
    BlockType.VersionCtrl: 24,
    BlockType.SegmentTable: 2,
    BlockType.UnitTable: 4,
    BlockType.SegLocation: 2,
    BlockType.UnitLocation: 2,
    BlockType.StringBlock: 2,
}

_VAR_SIZE_OF = {
    BlockType.InterfLoc: 12,
    BlockType.UnitLocation: 16,
}


# ---- LisaRuntime (combines LisaIO, StdUnit, IOPrimitives, ProgComm, ObjIO, IUMan, ObjInter, Dates, Times) ----

def convert_to_lisa_text(src: bytes) -> bytes:
    """Convert a Unix LF text file into a 1 KB-paged Lisa .TEXT image.

    Emits a 1024-byte NUL header page followed by 1024-byte NUL-padded text pages
    containing whole CR-terminated lines with 8-column tabs expanded and leading
    spaces compressed as DLE (0x10) plus (32 + count).
    """
    out = bytearray(1024)  # 1024-byte header page of NULs
    page = bytearray()
    i = 0
    n = len(src)
    while i < n:
        line_bytes = bytearray()
        while i < n and src[i] != 10:
            if src[i] != 13:
                line_bytes.append(src[i])
            i += 1
        i += 1  # skip LF
        # expand tabs to 8 columns
        while 9 in line_bytes:
            lead = line_bytes.index(9)
            spaces = 8 - (lead % 8)
            line_bytes[lead:lead + 1] = b' ' * spaces
        # DLE-compress leading blanks
        lead = 0
        while lead < len(line_bytes) and line_bytes[lead] == 32:
            lead += 1
        if lead > 223:
            lead = 223
        if lead > 0:
            enc = bytes([16, 32 + lead]) + bytes(line_bytes[lead:]) + b'\r'
        else:
            enc = bytes(line_bytes) + b'\r'
        if len(enc) > 1023:
            enc = enc[:1022] + b'\r'
        if len(page) + len(enc) > 1023:
            if len(page) > 0:
                out.extend(page)
                out.extend(b'\x00' * (1024 - len(page)))
                page.clear()
        page.extend(enc)
    if len(page) > 0:
        out.extend(page)
        out.extend(b'\x00' * (1024 - len(page)))
    return bytes(out)


class LisaRuntime:
    """Per-invocation runtime environment: the host library units."""

    def __init__(self, args: Optional[list[str]] = None, exe_path: Optional[str] = None) -> None:
        """Initialize per-run state for LisaIO, StdUnit, IOPrimitives, ProgComm, PasDefs, ObjIO, IUMan, and timers."""
        self.args: list[str] = list(args) if args is not None else []
        self.su_cmd_line: bool = len(self.args) > 0
        self.next_arg: int = 0
        self.exe_path: str = os.path.abspath(exe_path or sys.argv[0])
        self._in_out_res: int = 0
        self.stdin_eof: bool = False

        # StdUnit
        self.SUOsBootV: str = ''
        self.SUMyProcV: str = ''
        self.SUNullS: str = ''
        self.SUExecStopped: bool = False

        # IOPrimitives
        self.IOInTotal: int = 0
        self.IOOutTotal: int = 0
        self.IOObjExt: bool = False
        self.IONoExt: bool = False
        self.IONoDLEs: bool = False

        # ProgComm
        self.pc_bufr: str = ''
        self.pc_key: str = ''
        self.pc_read_pos: int = 0
        self.PCRunCmd: str = ''

        # PasDefs
        self.pd_errors: int = 0
        self.pd_listing_file: TextFile = TextFile()
        self.pd_listing_file.is_console = True
        self.pd_list_flag: bool = False

        # ObjIO
        self.OIAllowAbort: bool = True

        # IUMan & ObjInter
        self.IUMaxUnits: int = 0
        self.IUMaxFNames: int = 0
        self.iuLibUnts: list[Optional[OldULVariant]] = [None] * (IU_MAXUNITS + 1)
        self.iuLibStrs: list[Optional[str]] = [None] * (TMAXFILES + 1)
        self.iuLibFile: Optional[ObjDesc] = None
        self.iuLibName: str = ''
        self.WhichFile: str = ''
        self._oi_iuloc: list[int] = [-1] * (IU_MAXUNITS + 1)
        self._oi_this_fnum: int = 0

        # Times
        self._t1_ms: int = 0
        self._elapsed_ms: int = 0
        self._report_str: str = ''

    @property
    def io_result(self) -> int:
        """IOResult: returns InOutRes and resets it to 0."""
        res = self._in_out_res
        self._in_out_res = 0
        return res

    @io_result.setter
    def io_result(self, val: int) -> None:
        """Record the latest UCSD/Lisa I/O status code in InOutRes."""
        self._in_out_res = int(val)

    # ---- LisaIO name resolution ----

    @staticmethod
    def strip_volume(s: str) -> str:
        """Strip leading Lisa volume prefixes ('*name', '-vol-name', or stacked '-#BOOT-*name') from a path."""
        s = s.strip()
        while True:
            if len(s) > 0 and s[0] == '*':
                s = s[1:]
            elif len(s) > 1 and s[0] == '-':
                idx = s.find('-', 1)
                if idx >= 0:
                    s = s[idx + 1:]
                else:
                    s = s[1:]
            else:
                break
        return s

    @staticmethod
    def has_volume(s: str) -> bool:
        """Return True if the Lisa pathname starts with a '*' boot-volume or '-vol-' volume prefix."""
        s = s.strip()
        return len(s) > 1 and (s[0] == '*' or s[0] == '-')

    def boot_dir(self) -> str:
        """Locate the host directory acting as the Lisa Workshop boot volume ($LISA_BOOT or libs/workshop3.0)."""
        d = os.environ.get('LISA_BOOT', '')
        if not d:
            exe_dir = os.path.dirname(self.exe_path)
            cand = os.path.abspath(os.path.join(exe_dir, '..', 'libs', 'workshop3.0'))
            if not os.path.isdir(cand):
                cand = os.path.abspath(os.path.join(exe_dir, '..', '..', 'libs', 'workshop3.0'))
            d = cand
        return d.rstrip('/')

    @staticmethod
    def find_ci(dir_path: str, name: str) -> str:
        """Find an entry matching ``name`` case-insensitively inside ``dir_path``, or return '' if absent."""
        if not dir_path:
            dir_path = '.'
        exact = os.path.join(dir_path, name)
        if os.path.exists(exact):
            return name
        try:
            entries = os.listdir(dir_path)
        except OSError:
            return ''
        low = name.lower()
        for e in entries:
            if e.lower() == low:
                return e
        return ''

    def _host_name1(self, lisa_name: str, dir0: str) -> str:
        """Resolve a Lisa pathname relative to ``dir0`` by stripping volume prefixes and matching components case-insensitively."""
        s = self.strip_volume(lisa_name)
        if dir0 != '.':
            s = dir0 + '/' + s
        absolute = s.startswith('/')
        if absolute:
            cur_dir = ''
            res = ''
            s = s[1:]
        else:
            cur_dir = '.'
            res = ''
        for part in s.split('/'):
            if not part:
                continue
            search_dir = '/' if (absolute and cur_dir == '') else cur_dir
            real = self.find_ci(search_dir, part)
            if not real:
                real = part
            if res == '':
                res = ('/' + real) if absolute else real
            else:
                res = res + '/' + real
            cur_dir = res
        return res

    def host_name(self, lisa_name: str) -> str:
        """Map a Lisa filename to a host path, falling back to the boot volume directory when a volume prefix is present."""
        h = self._host_name1(lisa_name, '.')
        if self.has_volume(lisa_name) and not os.path.isfile(h):
            b = self._host_name1(lisa_name, self.boot_dir())
            if os.path.isfile(b):
                h = b
        return h

    def host_name_read(self, lisa_name: str) -> str:
        """Map a Lisa filename for reading, searching the boot volume directory when a relative unprefixed file is absent locally."""
        h = self.host_name(lisa_name)
        trimmed = lisa_name.strip()
        if (not os.path.isfile(h) and not self.has_volume(lisa_name)
                and len(trimmed) > 0 and not trimmed.startswith('/')):
            b = self._host_name1(lisa_name, self.boot_dir())
            if os.path.isfile(b):
                h = b
        return h

    # ---- LisaIO untyped and text files ----

    def reset_untyped(self, f: UntypedFile, name: Optional[str] = None) -> None:
        """Open an existing untyped file in 512-byte blocks, transparently converting LF .TEXT files into paged Lisa .TEXT images."""
        if name is None:
            if f.fp is not None:
                try:
                    f.fp.seek(0)
                    self.io_result = 0
                except OSError:
                    self.io_result = 10
            return
        h = self.host_name_read(name)
        if not h or not os.path.isfile(h):
            self.io_result = 10
            return
        f.in_use = True
        f.is_image = False
        f.image = b''
        f.host_path = h
        f.next_block = 0
        if h.upper().endswith('.TEXT'):
            try:
                with open(h, 'rb') as fp:
                    data = fp.read()
                if b'\n' in data:
                    f.is_image = True
                    f.image = convert_to_lisa_text(data)
            except OSError:
                f.in_use = False
                self.io_result = 10
                return
        if not f.is_image:
            try:
                f.fp = open(h, 'rb')
            except OSError:
                f.in_use = False
                self.io_result = 10
                return
        self.io_result = 0

    def rewrite_untyped(self, f: UntypedFile, name: str) -> None:
        """Create or truncate a read/write untyped 512-byte block file at the mapped host path."""
        h = self.host_name(name)
        try:
            fp = open(h, 'w+b')
        except OSError:
            f.in_use = False
            self.io_result = 8
            return
        f.in_use = True
        f.is_image = False
        f.image = b''
        f.host_path = h
        f.fp = fp
        f.next_block = 0
        self.io_result = 0

    def close_untyped(self, f: UntypedFile, opt: LisaCloseOpt = LisaCloseOpt.NORMAL) -> None:
        """Close an untyped file and delete its backing host file when ``opt`` is ``LisaCloseOpt.PURGE``."""
        if not f.in_use:
            if f.fp is not None:
                try:
                    f.fp.close()
                except OSError:
                    pass
                f.fp = None
            self.io_result = 0
            return
        p = f.host_path
        if not f.is_image and f.fp is not None:
            try:
                f.fp.close()
            except OSError:
                pass
            f.fp = None
        f.in_use = False
        f.image = b''
        if opt == LisaCloseOpt.PURGE and p:
            try:
                os.remove(p)
            except OSError:
                pass
        self.io_result = 0

    def block_read(self, f: UntypedFile, buf: bytearray, count: int, block: int) -> int:
        """Read up to ``count`` 512-byte blocks starting at ``block`` into ``buf``, returning the number of whole blocks read."""
        if not f.in_use:
            self.io_result = 103
            return 0
        if count <= 0:
            self.io_result = 0
            return 0
        if f.is_image:
            off = block * 512
            avail = len(f.image) - off
            if avail <= 0:
                self.io_result = 0
                return 0
            got = min(count, avail // 512)
            nbytes = got * 512
            buf[:nbytes] = f.image[off:off + nbytes]
        else:
            if f.fp is None:
                self.io_result = 103
                return 0
            try:
                f.fp.seek(0, os.SEEK_END)
                total_blocks = f.fp.tell() // 512
                if block >= total_blocks:
                    self.io_result = 0
                    return 0
                f.fp.seek(block * 512)
                raw = f.fp.read(count * 512)
                got = len(raw) // 512
                nbytes = got * 512
                buf[:nbytes] = raw[:nbytes]
            except OSError:
                self.io_result = 99
                return 0
        f.next_block = block + got
        self.io_result = 0
        return got

    def block_write(self, f: UntypedFile, buf: bytes | bytearray, count: int, block: int) -> int:
        """Write ``count`` 512-byte blocks from ``buf`` at 512-byte offset ``block``, zero-padding short buffers."""
        if not f.in_use or f.is_image or f.fp is None:
            self.io_result = 103
            return 0
        if count <= 0:
            self.io_result = 0
            return 0
        try:
            f.fp.seek(block * 512)
            nbytes = count * 512
            chunk = bytes(buf[:nbytes])
            if len(chunk) < nbytes:
                chunk += b'\x00' * (nbytes - len(chunk))
            f.fp.write(chunk)
            done = count
        except OSError:
            self.io_result = 101
            return 0
        f.next_block = block + done
        self.io_result = 0
        return done

    def reset_text(self, f: TextFile, name: str) -> None:
        """Open an existing text file for reading using Latin-1 byte-transparent encoding."""
        h = self.host_name_read(name)
        try:
            f.fp = open(h, 'r', encoding='latin-1')
            f.host_path = h
            f.is_console = False
            f.is_open = True
            self.io_result = 0
        except OSError:
            f.is_open = False
            self.io_result = 10

    def rewrite_text(self, f: TextFile, name: str = 'CONSOLE:') -> None:
        """Open a text file for writing, routing CONSOLE: variants to standard output."""
        u = self.strip_volume(name).upper()
        if u in ('', 'CONSOLE', 'CONSOLE:', 'CONSOLE.TEXT'):
            f.fp = None
            f.host_path = ''
            f.is_console = True
            f.is_open = True
            self.io_result = 0
            return
        h = self.host_name(name)
        try:
            f.fp = open(h, 'w', encoding='latin-1')
            f.host_path = h
            f.is_console = False
            f.is_open = True
            self.io_result = 0
        except OSError:
            f.is_open = False
            self.io_result = 8

    def close_text(self, f: TextFile, opt: LisaCloseOpt = LisaCloseOpt.NORMAL) -> None:
        """Close a text file and remove the underlying host file if ``opt`` is ``LisaCloseOpt.PURGE``."""
        p = f.host_path
        if f.fp is not None:
            try:
                f.fp.close()
            except OSError:
                pass
            f.fp = None
        f.is_open = False
        if opt == LisaCloseOpt.PURGE and p:
            try:
                os.remove(p)
            except OSError:
                pass
        self.io_result = 0

    # ---- StdUnit ----

    def SUInit(self) -> None:
        """Initialize StdUnit global strings, volume names, and execution-stopped state."""
        self.SUNullS = ''
        self.SUOsBootV = ''
        self.SUMyProcV = ''
        self.SUExecStopped = False

    def SUDone(self) -> None:
        """Finalize StdUnit state on program termination (no-op on the host)."""
        pass

    @staticmethod
    def SUUpCh(ch: str) -> str:
        """Convert an ASCII lowercase character ('a'..'z') to uppercase."""
        if 'a' <= ch <= 'z':
            return chr(ord(ch) - 32)
        return ch

    @staticmethod
    def SULowCh(ch: str) -> str:
        """Convert an ASCII uppercase character ('A'..'Z') to lowercase."""
        if 'A' <= ch <= 'Z':
            return chr(ord(ch) + 32)
        return ch

    @staticmethod
    def SUUpStr(s: str) -> str:
        """Return ``s`` with all ASCII lowercase letters converted to uppercase."""
        return ''.join(chr(ord(c) - 32) if 'a' <= c <= 'z' else c for c in s)

    @staticmethod
    def SULowStr(s: str) -> str:
        """Return ``s`` with all ASCII uppercase letters converted to lowercase."""
        return ''.join(chr(ord(c) + 32) if 'A' <= c <= 'Z' else c for c in s)

    @classmethod
    def SUEqStr(cls, s1: str, s2: str) -> bool:
        """Compare two strings for ASCII case-insensitive equality."""
        return cls.SUUpStr(s1) == cls.SUUpStr(s2)

    @staticmethod
    def SUTrimLeading(s: str) -> str:
        """Strip leading space and tab characters from ``s``."""
        i = 0
        while i < len(s) and s[i] in (' ', '\t'):
            i += 1
        return s[i:]

    @staticmethod
    def SUTrimTrailing(s: str) -> str:
        """Strip trailing space and tab characters from ``s``."""
        i = len(s)
        while i > 0 and s[i - 1] in (' ', '\t'):
            i -= 1
        return s[:i]

    @classmethod
    def SUTrimBlanks(cls, s: str) -> str:
        """Strip both leading and trailing spaces and tabs from ``s``."""
        return cls.SUTrimTrailing(cls.SUTrimLeading(s))

    @staticmethod
    def SUAddCh(s: str, ch: str, max_len: int) -> tuple[str, bool]:
        """Append a character to ``s`` up to ``max_len``, returning ``(result, overflow)``."""
        ovf = len(s) >= max_len
        if not ovf:
            s = s + ch[0]
        return s, ovf

    @staticmethod
    def SUIsVolName(fn: str) -> bool:
        """Return True if ``fn`` is a bare Lisa volume prefix ('-vol' with no closing '-')."""
        return len(fn) > 1 and fn[0] == '-' and ('-' not in fn[1:])

    @staticmethod
    def SUVolPart(path_n: str) -> str:
        """Extract the leading '-vol-' volume prefix or directory path up to the final '/'."""
        if len(path_n) > 1 and path_n[0] == '-':
            idx = path_n.find('-', 1)
            if idx >= 0:
                return path_n[:idx + 1]
            return ''
        idx = path_n.rfind('/')
        if idx >= 0:
            return path_n[:idx + 1]
        return ''

    @classmethod
    def SUAddExtension(cls, fn: str, def_ext: str, max_len: int = SUMaxStrLeng) -> tuple[str, bool]:
        """Append ``def_ext`` unless ``fn`` already ends with it or has a trailing '.' suppressing extensions."""
        if not fn:
            return fn, False
        if fn.endswith('.'):
            return fn[:-1], False
        if not def_ext:
            return fn, False
        u = cls.SUUpStr(fn)
        e = cls.SUUpStr(def_ext)
        if len(u) >= len(e) and u.endswith(e):
            return fn, False
        if len(fn) + len(def_ext) > max_len:
            return fn, True
        return fn + def_ext, False

    @classmethod
    def SUSplitFN(cls, path_n: str) -> tuple[str, str, str]:
        """Returns (cat_n, fn, ext)."""
        cat_n = cls.SUVolPart(path_n)
        s = path_n[len(cat_n):]
        dot = s.rfind('.')
        if dot >= 0:
            ext = s[dot:]
            s = s[:dot]
        else:
            ext = ''
        return cat_n, s, ext

    @staticmethod
    def SUMakeFN(cat_n: str, fn: str, ext: str) -> tuple[str, bool]:
        """Concatenate catalog/volume prefix, filename stem, and extension up to ``SUMaxStrLeng``, returning ``(path, overflow)``."""
        ovf = len(cat_n) + len(fn) + len(ext) > SUMaxStrLeng
        return (cat_n + fn + ext)[:SUMaxStrLeng], ovf

    @classmethod
    def SUChkFN(cls, fn: str, def_vol: str, def_fn: str, def_ext: str) -> tuple[str, PromptState]:
        """Validate a prompt filename response, applying defaults or detecting '?', ESC, and '$'-options."""
        fn = cls.SUTrimBlanks(fn)
        if len(fn) == 0:
            if def_fn != '':
                fn = def_vol + def_fn
                fn, _ = cls.SUAddExtension(fn, def_ext, SUMaxStrLeng)
                return fn, PromptState.SUDefault
            return fn, PromptState.SUNone
        if fn == '?':
            return fn, PromptState.SUOptions
        if fn[0] == SUEsc:
            return fn, PromptState.SUEscape
        if fn[0] != '$':
            if def_vol != '' and ('/' not in fn) and fn[0] != '-':
                fn = def_vol + fn
            fn, ovf = cls.SUAddExtension(fn, def_ext, SUMaxStrLeng)
        else:
            ovf = False
        return fn, (PromptState.SUInvalid if ovf else PromptState.SUValid)

    def _read_stdin_char(self) -> Optional[str]:
        """Read a single raw byte from standard input as a 1-character string, or return None at EOF."""
        if self.stdin_eof:
            return None
        b = sys.stdin.buffer.read(1) if hasattr(sys.stdin, 'buffer') else sys.stdin.read(1).encode('latin-1')
        if not b:
            self.stdin_eof = True
            return None
        return chr(b[0])

    def SUGetCh(self) -> str:
        """Read a single character from standard input, mapping LF to CR and EOF to ESC."""
        sys.stdout.flush()
        ch = self._read_stdin_char()
        if ch is None:
            return SUEsc
        if ch == '\n':
            return SUCr
        return ch

    def SUGetLine(self) -> tuple[str, PromptState]:
        """Read a prompt response from command-line arguments (when started with args) or standard input."""
        sys.stdout.flush()
        if self.su_cmd_line:
            if self.next_arg < len(self.args):
                s = self.args[self.next_arg]
                self.next_arg += 1
            else:
                s = ''
            sys.stdout.write(s + '\n')
            if len(s) > 0 and s[0] == SUEsc:
                return s, PromptState.SUEscape
            if len(s) == 0:
                return s, PromptState.SUNone
            return s, PromptState.SUValid

        if self.stdin_eof:
            sys.stdout.write('\n')
            return '', PromptState.SUEscape
        chars = []
        got_any = False
        while True:
            ch = self._read_stdin_char()
            if ch is None:
                break
            got_any = True
            if ch == '\n':
                break
            chars.append(ch)
        if not got_any:
            sys.stdout.write('\n')
            return '', PromptState.SUEscape
        s = ''.join(chars)
        if s.endswith('\r'):
            s = s[:-1]
        s = s[:SUMaxStrLeng]
        if len(s) > 0 and s[0] == SUEsc:
            return s, PromptState.SUEscape
        if len(s) == 0:
            return s, PromptState.SUNone
        return s, PromptState.SUValid

    def SUGetStr(self, def_val: str) -> tuple[str, PromptState]:
        """Read a prompt string, substituting ``def_val`` with ``SUDefault`` when the response is empty."""
        s, pstate = self.SUGetLine()
        if pstate == PromptState.SUNone and def_val != '':
            return def_val, PromptState.SUDefault
        return s, pstate

    def SUGetFN(self, def_vol: str, def_fn: str, def_ext: str) -> tuple[str, PromptState]:
        """Read a filename prompt response and normalize it with ``SUChkFN`` unless aborted with ESC."""
        fn, pstate = self.SUGetLine()
        if pstate == PromptState.SUEscape:
            return fn, pstate
        return self.SUChkFN(fn, def_vol, def_fn, def_ext)

    def SUWaitEscOrSp(self) -> PromptState:
        """Wait for a line response, returning ``SUEscape`` on ESC/EOF or ``SUValid`` otherwise."""
        _, pstate = self.SUGetLine()
        if pstate != PromptState.SUEscape:
            pstate = PromptState.SUValid
        return pstate

    def SUWaitSp(self) -> None:
        """Wait for user acknowledgement before continuing."""
        self.SUWaitEscOrSp()

    def SUGetBool(self, default: bool) -> bool:
        """Read a boolean prompt response, returning ``default`` on empty input or True when starting with 'Y'/'T'."""
        s, _ = self.SUGetLine()
        if len(s) == 0:
            return default
        return self.SUUpCh(s[0]) in ('Y', 'T')

    def SUErrText(self, err_fn: str, err_n: int) -> str:
        """Format a fallback error message string for Lisa OS error number ``err_n``."""
        return f'Error {err_n}'

    def SUStopExec(self) -> int:
        """Mark Workshop exec-file execution as stopped due to an error and return status 0."""
        self.SUExecStopped = True
        return 0

    def SUInitSysVols(self) -> None:
        """Reset StdUnit boot and process volume names."""
        self.SUOsBootV = ''
        self.SUMyProcV = ''

    def SUSysReset(self, f: UntypedFile, fn: str) -> int:
        """Open a compiler system file, searching the current directory and executable directories."""
        self.reset_untyped(f, fn)
        io_status = self.io_result
        if io_status != 0:
            exe_dir = os.path.dirname(self.exe_path)
            for cand_dir in (exe_dir, os.path.dirname(exe_dir)):
                alt = os.path.join(cand_dir, fn)
                self.reset_untyped(f, alt)
                io_status = self.io_result
                if io_status == 0:
                    break
        return io_status

    # ---- IOPrimitives ----

    @classmethod
    def _is_console_name(cls, name: str) -> bool:
        """Return True if ``name`` refers to the Lisa CONSOLE or PRINTER device."""
        n = cls.SUUpStr(cls.SUTrimBlanks(name))
        if n.startswith('-'):
            n = n[1:]
        if n.endswith(':'):
            n = n[:-1]
        if n.endswith('.TEXT'):
            n = n[:-5]
        return n in ('CONSOLE', 'PRINTER')

    def InitIO(self) -> None:
        """Initialize IOPrimitives byte counters and filename/DLE mode flags."""
        self.IOInTotal = 0
        self.IOOutTotal = 0
        self.IOObjExt = False
        self.IONoExt = False
        self.IONoDLEs = False

    def EndIO(self) -> None:
        """Flush standard output at the conclusion of IOPrimitives buffered I/O."""
        sys.stdout.flush()

    def _flush_out(self, fcb: IOFCB) -> None:
        """Write buffered bytes in ``fcb.Bufr`` to the underlying host file and reset ``BufrCp``."""
        if fcb.BufrCp > 0:
            if fcb.DevType not in (IODevType.IOConsDev, IODevType.IOPrDev) and fcb.fp is not None:
                try:
                    fcb.fp.write(fcb.Bufr[:fcb.BufrCp])
                except OSError:
                    pass
            fcb.BufrCp = 0

    def OpenF(self, fname: str, fcb: Optional[IOFCB], mode: IOModes,
              bufr: Optional[bytearray] = None) -> tuple[int, IOFCB]:
        """Open an IOPrimitives stream; existing output targets write to a ``.new~`` temp file committed on ``CloseF``."""
        if fcb is None:
            fcb = IOFCB()
        fcb.Filename = fname
        fcb.LineNbr = 0
        fcb.BufrCp = 0
        fcb.BlkNbr = 0
        fcb.CurrLine = ''
        fcb.CurrLen = 0
        fcb.Mode = mode
        fcb._pend_final = None
        fcb._pend_temp = None
        if bufr is not None:
            fcb.Bufr = bufr
        elif fcb.Bufr is None:
            fcb.Bufr = bytearray(IOByteSize)

        if self._is_console_name(fname):
            fcb.DevType = IODevType.IOConsDev
            return 0, fcb

        fcb.DevType = IODevType.IOBlkDev
        h = self.host_name_read(fname) if mode == IOModes.IORead else self.host_name(fname)
        if mode == IOModes.IOWrite and os.path.isfile(h):
            fcb._pend_final = h
            fcb._pend_temp = h + '.new~'
            h = fcb._pend_temp
        try:
            fcb.fp = open(h, 'wb' if mode == IOModes.IOWrite else 'rb')
            r = 0
        except OSError:
            fcb.fp = None
            r = 10 if mode == IOModes.IORead else 8
        if mode == IOModes.IORead:
            fcb.LastBlk = 0
            fcb.LastByte = 0
            fcb.Eol = False
        else:
            fcb.EndPage = 0
        return r, fcb

    def CloseF(self, fcb: Optional[IOFCB], close_kind: IOCloseKind) -> None:
        """Flush and close an IOPrimitives stream, atomically replacing or purging output files per ``close_kind``."""
        if fcb is None:
            return
        if fcb.DevType in (IODevType.IOConsDev, IODevType.IOPrDev):
            sys.stdout.flush()
            return
        if fcb.Mode == IOModes.IOWrite:
            self._flush_out(fcb)
        if fcb.fp is not None:
            try:
                fcb.fp.close()
            except OSError:
                pass
            fcb.fp = None
        if fcb._pend_temp is not None and fcb._pend_final is not None:
            if close_kind == IOCloseKind.IOPurge:
                try:
                    os.remove(fcb._pend_temp)
                except OSError:
                    pass
            else:
                try:
                    os.replace(fcb._pend_temp, fcb._pend_final)
                except OSError:
                    pass
            fcb._pend_temp = None
            fcb._pend_final = None
            return
        if close_kind == IOCloseKind.IOPurge:
            try:
                os.remove(self.host_name(fcb.Filename))
            except OSError:
                pass

    def GetcF(self, fcb: IOFCB) -> str:
        """Read one character from ``fcb``, translating LF to ``IONewline`` (CR) and EOF to ``IOEndfile`` (ETX)."""
        if fcb.DevType in (IODevType.IOConsDev, IODevType.IOKbDev):
            ch = self._read_stdin_char()
            if ch is None:
                return IOEndfile
            return IONewline if ch == '\n' else ch
        if fcb.fp is None:
            return IOEndfile
        b = fcb.fp.read(1)
        if not b:
            return IOEndfile
        ch = chr(b[0])
        return IONewline if ch == '\n' else ch

    def GetLine(self, fcb: IOFCB) -> tuple[bool, str]:
        """Read a CR-terminated line of up to ``IOMaxStr`` (132) characters from ``fcb``, returning ``(not_eof, line)``."""
        chars = []
        while True:
            c = self.GetcF(fcb)
            if c not in (IONewline, IOEndfile) and len(chars) < IOMaxStr:
                chars.append(c)
            if c in (IONewline, IOEndfile):
                break
        line = ''.join(chars)
        ok = not (c == IOEndfile and len(line) == 0)
        return ok, line

    def PutcF(self, fcb: IOFCB, c: str) -> None:
        """Write one character to ``fcb``, translating ``IONewline`` (CR) to LF and buffering block-device output."""
        if c == IONewline:
            c = '\n'
        self.IOOutTotal += 1
        if fcb.DevType in (IODevType.IOConsDev, IODevType.IOPrDev):
            sys.stdout.write(c)
        else:
            if fcb.BufrCp > IOBytSizeM1:
                self._flush_out(fcb)
            fcb.Bufr[fcb.BufrCp] = ord(c[0]) & 0xFF
            fcb.BufrCp += 1

    def PutStrS(self, fcb: IOFCB, s: str, width: int) -> None:
        """Write ``s`` to ``fcb`` formatted to ``width`` (>0 right-justified, <0 left-justified, truncating if ``0 < |width| <= len(s)``)."""
        w = abs(width)
        if 0 < w <= len(s):
            for i in range(w):
                self.PutcF(fcb, s[i])
        else:
            if width > 0:
                for _ in range(w - len(s)):
                    self.PutcF(fcb, ' ')
            for ch in s:
                self.PutcF(fcb, ch)
            if width < 0:
                for _ in range(w - len(s)):
                    self.PutcF(fcb, ' ')

    def PutLineS(self, fcb: IOFCB, line: str) -> None:
        """Write ``line`` followed by ``IONewline`` to ``fcb``."""
        self.PutStrS(fcb, line, 0)
        self.PutcF(fcb, IONewline)

    @staticmethod
    def PutIntP(n: int, width: int) -> str:
        """Format integer ``n`` to ``width`` (>0 blank-padded, <0 zero-padded after any leading minus sign)."""
        s = str(abs(int(n)))
        if width >= 0:
            if n < 0:
                s = '-' + s
            if len(s) < width:
                s = ' ' * (width - len(s)) + s
        else:
            pad_target = abs(width) - (1 if n < 0 else 0)
            if len(s) < pad_target:
                s = '0' * (pad_target - len(s)) + s
            if n < 0:
                s = '-' + s
        return s

    @staticmethod
    def IOError(io_status: int, msg: str) -> bool:
        """Report positive Lisa I/O error codes to standard output with a bell character and return True on error."""
        if io_status > 0:
            sys.stdout.write(f'{SUBell}{msg} (I/O error {io_status})\n')
            return True
        return False

    # ---- ProgComm ----

    PCFileName = 'PROGCOMM.TEXT'
    PCBufrMax = 1023
    PCText = 1

    def PCInit(self) -> None:
        """Reset the in-memory ProgComm inter-pass communication buffer and run command."""
        self.pc_bufr = ''
        self.pc_key = ''
        self.pc_read_pos = 0
        self.PCRunCmd = ''

    def PCSetRunCmd(self, rc: str) -> None:
        """Record the Workshop shell command to chain to after the current compiler pass."""
        self.PCRunCmd = rc

    def PCReWrite(self, write_type: int, key: str) -> None:
        """Start a new in-memory ProgComm message buffer tagged with header ``key``."""
        self.pc_bufr = ''
        self.pc_key = key

    def PCReset(self, read_type: int, key: str) -> bool:
        """Load ``PROGCOMM.TEXT`` into the read buffer if its first line matches ``key`` (e.g. 'For Code Gen')."""
        if not os.path.isfile(self.PCFileName):
            return False
        try:
            with open(self.PCFileName, 'r', encoding='latin-1') as fp:
                raw_lines = fp.read().splitlines()
        except OSError:
            return False
        if not raw_lines or raw_lines[0] != key:
            return False
        self.pc_bufr = ''.join(line + '\r' for line in raw_lines[1:])
        self.pc_read_pos = 0
        self.pc_key = key
        return True

    def PCClose(self, kill_bufr: bool, key: str) -> bool:
        """Write the keyed ProgComm buffer to ``PROGCOMM.TEXT``, or delete a matching ``PROGCOMM.TEXT`` when ``kill_bufr`` is True."""
        if kill_bufr:
            self.pc_bufr = ''
            if os.path.isfile(self.PCFileName):
                try:
                    with open(self.PCFileName, 'r', encoding='latin-1') as fp:
                        first = fp.readline().rstrip('\r\n')
                    if first == key:
                        os.remove(self.PCFileName)
                except OSError:
                    pass
            return True
        try:
            with open(self.PCFileName, 'w', encoding='latin-1') as fp:
                fp.write(key + '\n')
                for ch in self.pc_bufr:
                    if ch == '\r':
                        fp.write('\n')
                    else:
                        fp.write(ch)
            return True
        except OSError:
            return False

    def PCPutCh(self, ch: str) -> bool:
        """Append one character to the ProgComm buffer if within the 1024-byte capacity."""
        ok = len(self.pc_bufr) <= self.PCBufrMax
        if ok:
            self.pc_bufr += ch[0]
        return ok

    def PCGetCh(self) -> tuple[bool, str]:
        """Read the next character from the ProgComm buffer, returning ``(ok, ch)``."""
        if self.pc_read_pos < len(self.pc_bufr):
            ch = self.pc_bufr[self.pc_read_pos]
            self.pc_read_pos += 1
            return True, ch
        return False, '\x00'

    def PCPutLine(self, line: str) -> bool:
        """Append a CR-terminated line to the ProgComm buffer if capacity permits."""
        ok = len(self.pc_bufr) + len(line) + 1 <= self.PCBufrMax + 1
        if ok:
            self.pc_bufr += line + '\r'
        return ok

    def PCGetLine(self) -> tuple[bool, str]:
        """Read characters up to the next CR from the ProgComm buffer, returning ``(ok, line)``."""
        ok = self.pc_read_pos < len(self.pc_bufr)
        chars = []
        while True:
            got, ch = self.PCGetCh()
            if not got or ch == '\r':
                break
            chars.append(ch)
        return ok, ''.join(chars)

    # ---- PasDefs ----

    def InitPasDefs(self) -> None:
        """Reset PasDefs error counter and direct listing output to the console."""
        self.pd_errors = 0
        self.pd_listing_file = TextFile()
        self.pd_listing_file.is_console = True
        self.pd_list_flag = False

    def pd_FatalError(self, s: str) -> None:
        """Report a fatal compiler error, stop Workshop exec processing, wait for space/ESC, and raise ``PasHaltException``."""
        self.SUStopExec()
        self.pd_listing_file.writeln(f'*** Fatal Error - {s} ***')
        self.pd_errors += 1
        if self.pd_list_flag:
            sys.stdout.write(f'*** Fatal Error - {s} ***\n')
        sys.stdout.write('Type <sp> to continue.')
        sys.stdout.flush()
        while True:
            ch = self.SUGetCh()
            if ch in (' ', SUEsc):
                break
        raise PasHaltException()

    # ---- FileIO & ObjIO ----

    def InitObjFile(self, n_blocks: int = 4) -> ObjDesc:
        """Allocate an initialized ``ObjDesc`` handle for reading or writing a Lisa .OBJ file."""
        return ObjDesc(n_blocks)

    def OpenObjFile(self, obj: ObjDesc, filename: str, new_file: bool) -> None:
        """Open a Lisa .OBJ or library file for creating (``new_file=True``) or reading, resetting ``NextBlock`` to 0."""
        hn = self.host_name(filename) if new_file else self.host_name_read(filename)
        obj.ObjFile.host_name = hn
        obj.ObjFile.OldFile = not new_file
        obj.NextBlock = 0
        try:
            obj.ObjFile.fp = open(hn, 'w+b' if new_file else 'rb')
            obj.ObjFile.is_open = True
            self.io_result = 0
        except OSError:
            obj.ObjFile.fp = None
            obj.ObjFile.is_open = False
            self.io_result = 8 if new_file else 10

    def ZeroObjEnd(self, obj: ObjDesc) -> None:
        """Pad the open .OBJ file with NUL bytes up to the next 512-byte block boundary."""
        fp = obj.ObjFile.fp
        if fp is None:
            return
        pos = fp.tell()
        n = (512 - (pos % 512)) % 512
        if n > 0:
            fp.write(b'\x00' * n)

    def CloseObjFile(self, obj: ObjDesc, save: bool) -> None:
        """Close an .OBJ file, deleting newly created files when ``save`` is False."""
        if obj.ObjFile.is_open:
            if obj.ObjFile.fp is not None:
                try:
                    obj.ObjFile.fp.close()
                except OSError:
                    pass
                obj.ObjFile.fp = None
            obj.ObjFile.is_open = False
            if not save and not obj.ObjFile.OldFile and obj.ObjFile.host_name:
                try:
                    os.remove(obj.ObjFile.host_name)
                except OSError:
                    pass

    @staticmethod
    def GetObjPtr(obj: ObjDesc) -> int:
        """Return the current byte offset within an open .OBJ file."""
        if obj.ObjFile.is_open and obj.ObjFile.fp is not None:
            return obj.ObjFile.fp.tell()
        return 0

    @staticmethod
    def GetObjBlockPtr(obj: ObjDesc) -> int:
        """Return the byte offset of the next sequential .OBJ block header."""
        return obj.NextBlock

    @staticmethod
    def SetObjPtr(obj: ObjDesc, byte_ptr: int) -> None:
        """Seek to ``byte_ptr`` in an .OBJ file, extending with NUL bytes if seeking past EOF."""
        fp = obj.ObjFile.fp
        if fp is None:
            return
        fp.seek(0, os.SEEK_END)
        size = fp.tell()
        if byte_ptr > size:
            fp.write(b'\x00' * (byte_ptr - size))
        fp.seek(byte_ptr)

    @staticmethod
    def SetObjBlockPtr(obj: ObjDesc, byte_ptr: int) -> None:
        """Set the byte offset recorded for the next .OBJ block header."""
        obj.NextBlock = byte_ptr

    @staticmethod
    def FileEOF(fdesc: FileDesc) -> bool:
        """Return True if the file descriptor is closed or positioned at or past EOF."""
        if fdesc.fp is None:
            return True
        pos = fdesc.fp.tell()
        fdesc.fp.seek(0, os.SEEK_END)
        end = fdesc.fp.tell()
        fdesc.fp.seek(pos)
        return pos >= end

    @staticmethod
    def SetObjInvar(b: ObjBlock, invar_type: BlockType, var_size: int) -> None:
        """Configure ``b`` with block tag ``invar_type`` and variant payload byte size ``var_size``."""
        b.BlockHeader = invar_type
        b.Variant = VariantType.NoVariant
        b.NrVariants = var_size

    @staticmethod
    def GetObjSeq(obj: ObjDesc, nr_bytes: int) -> bytes:
        """Read ``nr_bytes`` raw bytes from ``obj``, zero-padding any short read at EOF."""
        if nr_bytes <= 0 or obj.ObjFile.fp is None:
            return b''
        got = obj.ObjFile.fp.read(nr_bytes)
        if len(got) < nr_bytes:
            got += b'\x00' * (nr_bytes - len(got))
        return got

    @classmethod
    def GetObjByte(cls, obj: ObjDesc) -> int:
        """Read an unsigned 8-bit byte from ``obj``."""
        b = cls.GetObjSeq(obj, 1)
        return b[0] if b else 0

    @classmethod
    def GetObjWord(cls, obj: ObjDesc) -> int:
        """Read a big-endian signed 16-bit MC68000 word from ``obj``."""
        b = cls.GetObjSeq(obj, 2)
        return struct.unpack('>h', b)[0]

    @classmethod
    def GetObjLong(cls, obj: ObjDesc) -> int:
        """Read a big-endian signed 32-bit MC68000 longword from ``obj``."""
        b = cls.GetObjSeq(obj, 4)
        return struct.unpack('>i', b)[0]

    @classmethod
    def GetObjName(cls, obj: ObjDesc) -> str:
        """Read an 8-character fixed-width ``NameString`` (Latin-1) from ``obj``."""
        return cls.GetObjSeq(obj, 8).decode('latin-1')

    @staticmethod
    def PutObjSeq(obj: ObjDesc, data: bytes | bytearray) -> None:
        """Write raw bytes sequentially to ``obj``."""
        if len(data) > 0 and obj.ObjFile.fp is not None:
            obj.ObjFile.fp.write(data)

    @classmethod
    def PutObjByte(cls, obj: ObjDesc, b: int) -> None:
        """Write an unsigned 8-bit byte to ``obj``."""
        cls.PutObjSeq(obj, bytes([b & 0xFF]))

    @classmethod
    def PutObjWord(cls, obj: ObjDesc, w: int) -> None:
        """Write a 16-bit integer to ``obj`` in big-endian MC68000 byte order."""
        cls.PutObjSeq(obj, struct.pack('>H', u16(w)))

    @classmethod
    def PutObjLong(cls, obj: ObjDesc, val: int) -> None:
        """Write a 32-bit integer to ``obj`` in big-endian MC68000 byte order."""
        cls.PutObjSeq(obj, struct.pack('>I', u32(val)))

    @classmethod
    def PutObjName(cls, obj: ObjDesc, name: str) -> None:
        """Write an 8-character space-padded ``NameString`` to ``obj``."""
        cls.PutObjSeq(obj, alfa8(name).encode('latin-1'))

    @classmethod
    def PutObjWords(cls, obj: ObjDesc, words: list[int], nr_bytes: int) -> None:
        """Write ``nr_bytes`` from a 16-bit word array to ``obj`` in big-endian MC68000 byte order."""
        out = bytearray()
        for idx in range(nr_bytes // 2):
            w = u16(words[idx])
            out.append((w >> 8) & 0xFF)
            out.append(w & 0xFF)
        if nr_bytes & 1:
            w = u16(words[nr_bytes // 2])
            out.append((w >> 8) & 0xFF)
        cls.PutObjSeq(obj, out)

    @classmethod
    def PutObjVar(cls, obj: ObjDesc, var_type: VariantType, stuff: ObjVarBlock) -> None:
        """Write a single ``ObjVarBlock`` variant entry (RefVariant, ShortRef, or ModVariant) to ``obj``."""
        if var_type == VariantType.RefVariant:
            cls.PutObjLong(obj, stuff.bRefVariant)
        elif var_type == VariantType.ShortRef:
            cls.PutObjWord(obj, stuff.bShortRef)
        elif var_type == VariantType.ModVariant:
            cls.PutObjWord(obj, stuff.bModVariant)
        else:
            sys.stdout.write(f'*** PutObjVar: variant {int(var_type)} not supported\n')

    @classmethod
    def GetObjVar(cls, obj: ObjDesc, var_type: VariantType, stuff: ObjVarBlock) -> None:
        """Read a single ``ObjVarBlock`` variant entry (such as a 12-byte ``IntfLocVariant``) from ``obj``."""
        stuff.VarHeader = var_type
        if var_type == VariantType.RefVariant:
            stuff.bRefVariant = cls.GetObjLong(obj)
        elif var_type == VariantType.ShortRef:
            stuff.bShortRef = cls.GetObjWord(obj)
        elif var_type == VariantType.ModVariant:
            stuff.bModVariant = cls.GetObjWord(obj)
        elif var_type == VariantType.IntfLocVariant:
            stuff.UnitName = cls.GetObjName(obj)
            stuff.IfLoc = cls.GetObjLong(obj)
        else:
            sys.stdout.write(f'*** GetObjVar: variant {int(var_type)} not supported\n')

    @classmethod
    def GetObjInvar(cls, obj: ObjDesc, stuff: ObjBlock) -> None:
        """Read a 4-byte Lisa .OBJ block header (1-byte tag + 24-bit big-endian size) and decode its invariant fields."""
        cls.SetObjPtr(obj, obj.NextBlock)
        h = cls.GetObjByte(obj)
        stuff.BlockHeader = _BYTE_TO_BLOCK.get(h, BlockType.UnknownBlock)
        hi = cls.GetObjByte(obj)
        w = u16(cls.GetObjWord(obj))
        size = hi * 65536 + w
        if size < 4:
            stuff.BlockHeader = BlockType.EOFMark
            size = 4
        stuff.Variant = VariantType.NoVariant
        invar_sz = _INVAR_SIZES.get(stuff.BlockHeader, 0)
        stuff.NrVariants = size - 4 - invar_sz
        if stuff.BlockHeader == BlockType.UnknownBlock:
            stuff.NrVariants = 0
        vsz = _VAR_SIZE_OF.get(stuff.BlockHeader, 0)
        if vsz > 0:
            stuff.NrVariants = pdiv(stuff.NrVariants, vsz)

        bh = stuff.BlockHeader
        if bh == BlockType.ModuleName:
            stuff.ModuleName = cls.GetObjName(obj)
            stuff.SegmentName = cls.GetObjName(obj)
            stuff.CSize = cls.GetObjLong(obj)
        elif bh == BlockType.EndBlock:
            stuff.CSize = cls.GetObjLong(obj)
        elif bh == BlockType.EntryPoint:
            stuff.LinkName = cls.GetObjName(obj)
            stuff.UserName = cls.GetObjName(obj)
            stuff.Loc = cls.GetObjLong(obj)
        elif bh in (BlockType.External, BlockType.ShortExternal):
            stuff.LinkName = cls.GetObjName(obj)
            stuff.UserName = cls.GetObjName(obj)
        elif bh == BlockType.StartAddress:
            stuff.Start = cls.GetObjLong(obj)
            stuff.GSize = cls.GetObjLong(obj)
        elif bh == BlockType.CodeBlock:
            stuff.Addr = cls.GetObjLong(obj)
        elif bh == BlockType.CommonReloc:
            stuff.CommonName = cls.GetObjName(obj)
        elif bh == BlockType.InterfLoc:
            stuff.Reserved = cls.GetObjWord(obj)
        elif bh == BlockType.SegmentTable:
            stuff.nSegments = cls.GetObjWord(obj)
        elif bh == BlockType.UnitTable:
            stuff.nUnits = cls.GetObjWord(obj)
            stuff.maxunit = cls.GetObjWord(obj)
        elif bh == BlockType.SegLocation:
            stuff.nSegments = cls.GetObjWord(obj)
        elif bh == BlockType.UnitLocation:
            stuff.nUnits = cls.GetObjWord(obj)
        elif bh == BlockType.StringBlock:
            stuff.nStrings = cls.GetObjWord(obj)
        elif bh == BlockType.UnitBlock:
            stuff.UnitName = cls.GetObjName(obj)
            stuff.CodeAddr = cls.GetObjLong(obj)
            stuff.TextAddr = cls.GetObjLong(obj)
            stuff.TextSize = cls.GetObjLong(obj)
            stuff.GlobalSize = cls.GetObjLong(obj)
            stuff.UnitType = cls.GetObjWord(obj)
        obj.NextBlock += size

    @classmethod
    def PutObjInvar(cls, obj: ObjDesc, stuff: ObjBlock) -> None:
        """Write a 4-byte Lisa .OBJ block header (1-byte tag + 24-bit big-endian total size) and its invariant payload."""
        hb = _HEADER_BYTES.get(stuff.BlockHeader, -1)
        if hb < 0:
            sys.stdout.write(
                f'*** PutObjInvar: block type {int(stuff.BlockHeader)} not supported by the host ObjIO\n'
            )
            return
        cls.SetObjPtr(obj, obj.NextBlock)
        size = 4 + _INVAR_SIZES.get(stuff.BlockHeader, 0) + stuff.NrVariants
        cls.PutObjByte(obj, hb)
        cls.PutObjByte(obj, (size >> 16) & 0xFF)
        cls.PutObjWord(obj, i16(size & 0xFFFF))

        bh = stuff.BlockHeader
        if bh == BlockType.ModuleName:
            cls.PutObjName(obj, stuff.ModuleName)
            cls.PutObjName(obj, stuff.SegmentName)
            cls.PutObjLong(obj, stuff.CSize)
        elif bh == BlockType.EndBlock:
            cls.PutObjLong(obj, stuff.CSize)
        elif bh == BlockType.EntryPoint:
            cls.PutObjName(obj, stuff.LinkName)
            cls.PutObjName(obj, stuff.UserName)
            cls.PutObjLong(obj, stuff.Loc)
        elif bh in (BlockType.External, BlockType.ShortExternal):
            cls.PutObjName(obj, stuff.LinkName)
            cls.PutObjName(obj, stuff.UserName)
        elif bh == BlockType.StartAddress:
            cls.PutObjLong(obj, stuff.Start)
            cls.PutObjLong(obj, stuff.GSize)
        elif bh == BlockType.CodeBlock:
            cls.PutObjLong(obj, stuff.Addr)
        elif bh == BlockType.Relocation:
            cls.PutObjWord(obj, stuff.Reserved)
        elif bh == BlockType.CommonReloc:
            cls.PutObjName(obj, stuff.CommonName)
        elif bh == BlockType.CommonDef:
            cls.PutObjName(obj, stuff.CommonName)
            cls.PutObjLong(obj, stuff.DSize)
        elif bh == BlockType.UnitBlock:
            cls.PutObjName(obj, stuff.UnitName)
            cls.PutObjLong(obj, stuff.CodeAddr)
            cls.PutObjLong(obj, stuff.TextAddr)
            cls.PutObjLong(obj, stuff.TextSize)
            cls.PutObjLong(obj, stuff.GlobalSize)
            cls.PutObjWord(obj, stuff.UnitType)
        obj.NextBlock += size

    # ---- IUMan & ObjInter ----

    def InitIUMan(self) -> None:
        """Initialize IUMan unit and library filename directory tables for ``INTRINSIC.LIB``."""
        self.iuLibUnts = [None] * (IU_MAXUNITS + 1)
        self.iuLibStrs = [None] * (TMAXFILES + 1)
        self.IUMaxUnits = 0
        self.IUMaxFNames = 0
        self.iuLibName = ''
        if self.iuLibFile is None:
            self.iuLibFile = self.InitObjFile(4)

    def ReadIULib(self) -> None:
        """Parse ``UnitLocation`` ($9D) and ``StringBlock`` ($9E) directory tables from an open ``INTRINSIC.LIB`` file."""
        assert self.iuLibFile is not None
        self.SetObjPtr(self.iuLibFile, 0)
        self.SetObjBlockPtr(self.iuLibFile, 0)
        b = ObjBlock()
        while True:
            self.GetObjInvar(self.iuLibFile, b)
            if b.BlockHeader == BlockType.UnitLocation:
                for _ in range(b.nUnits):
                    uname = self.GetObjName(self.iuLibFile)
                    unum = self.GetObjWord(self.iuLibFile)
                    fnum = self.GetObjByte(self.iuLibFile)
                    utype = self.GetObjByte(self.iuLibFile)
                    dsize = self.GetObjLong(self.iuLibFile)
                    if 1 <= unum <= IU_MAXUNITS:
                        self.iuLibUnts[unum] = OldULVariant(uname, unum, fnum, utype, dsize)
                        if unum > self.IUMaxUnits:
                            self.IUMaxUnits = unum
            elif b.BlockHeader == BlockType.StringBlock:
                n = min(b.nStrings, TMAXFILES)
                nums = []
                addrs = []
                for _ in range(n):
                    nums.append(self.GetObjWord(self.iuLibFile))
                    addrs.append(self.GetObjLong(self.iuLibFile))
                for num, addr in zip(nums, addrs):
                    if 1 <= num <= TMAXFILES:
                        self.SetObjPtr(self.iuLibFile, addr)
                        ln = self.GetObjByte(self.iuLibFile)
                        s = self.GetObjSeq(self.iuLibFile, ln).decode('latin-1') if ln > 0 else ''
                        if len(s) > 0 and s[0] not in ('-', '*'):
                            s = '*' + s
                        self.iuLibStrs[num] = s
                        if num > self.IUMaxFNames:
                            self.IUMaxFNames = num
            if b.BlockHeader == BlockType.EOFMark or self.FileEOF(self.iuLibFile.ObjFile):
                break

    def EachIUUnit(self, visit: Callable[[int], None]) -> None:
        """Invoke ``visit(unit_num)`` in ascending unit-number order for every registered unit in ``INTRINSIC.LIB``."""
        for i in range(1, self.IUMaxUnits + 1):
            if self.iuLibUnts[i] is not None:
                visit(i)

    def IntrinIndirect(self, iulib_in: bool, this_unit: str,
                       read_it: Callable[[str, int], None], fname: str) -> bool:
        """Look up unit ``fname`` via ``INTRINSIC.LIB`` and pass its library path and ``InterfLoc`` ($93) byte offset to ``read_it``.

        Lazily loads ``WhichFile`` on first call, skips units in the same library file as
        ``this_unit``, caches per-unit interface offsets from the target ``.OBJ`` library, and returns updated ``iulib_in``.
        """
        this_unit = alfa8(this_unit)
        fname = alfa8(fname)
        if not iulib_in:
            self.InitPasDefs()
            self.InitIUMan()
            assert self.iuLibFile is not None
            self.OpenObjFile(self.iuLibFile, self.WhichFile, False)
            if self.io_result <= 0:
                self.ReadIULib()
                iulib_in = True
                self.CloseObjFile(self.iuLibFile, True)
                self._oi_this_fnum = 0

                def find_this(idx: int) -> None:
                    u = self.iuLibUnts[idx]
                    if u is not None and u.UnitName == this_unit:
                        self._oi_this_fnum = u.FileNumber

                self.EachIUUnit(find_this)
                self._oi_iuloc = [-1] * (IU_MAXUNITS + 1)

        if iulib_in:
            fnum_box = [0]
            unum_box = [0]

            def find_uname(idx: int) -> None:
                u = self.iuLibUnts[idx]
                if u is not None and u.UnitName == fname:
                    fnum_box[0] = u.FileNumber
                    unum_box[0] = idx

            self.EachIUUnit(find_uname)
            fnum = fnum_box[0]
            unum = unum_box[0]
            if fnum != 0 and fnum != self._oi_this_fnum:
                lib_str = self.iuLibStrs[fnum] or ''
                if self._oi_iuloc[unum] > 0:
                    read_it(lib_str, self._oi_iuloc[unum])
                elif self._oi_iuloc[unum] == -1:
                    assert self.iuLibFile is not None
                    self.OpenObjFile(self.iuLibFile, lib_str, False)
                    if self.io_result <= 0:
                        in_block = ObjBlock()
                        self.GetObjInvar(self.iuLibFile, in_block)
                        if in_block.BlockHeader == BlockType.VersionCtrl:
                            while True:
                                self.GetObjInvar(self.iuLibFile, in_block)
                                if in_block.BlockHeader in (
                                    BlockType.InterfLoc, BlockType.ModuleName, BlockType.EOFMark
                                ):
                                    break
                            if in_block.BlockHeader == BlockType.InterfLoc:
                                ov = ObjVarBlock()
                                for _ in range(in_block.NrVariants):
                                    self.GetObjVar(self.iuLibFile, VariantType.IntfLocVariant, ov)
                                    unam = ov.UnitName
                                    fl = ov.IfLoc

                                    def set_floc(idx: int, unam: str = unam, fl: int = fl) -> None:
                                        u = self.iuLibUnts[idx]
                                        if u is not None and u.FileNumber == fnum and u.UnitName == unam:
                                            self._oi_iuloc[idx] = fl

                                    self.EachIUUnit(set_floc)
                            else:
                                def no_ifaces(idx: int) -> None:
                                    u = self.iuLibUnts[idx]
                                    if u is not None and u.FileNumber == fnum:
                                        self._oi_iuloc[idx] = 0

                                self.EachIUUnit(no_ifaces)
                        else:
                            self.pd_FatalError(f'Bad object file: {lib_str}')
                        self.CloseObjFile(self.iuLibFile, True)
                    else:
                        def no_ifaces_open(idx: int) -> None:
                            u = self.iuLibUnts[idx]
                            if u is not None and u.FileNumber == fnum:
                                self._oi_iuloc[idx] = 0

                        self.EachIUUnit(no_ifaces_open)
                    if self._oi_iuloc[unum] > 0:
                        read_it(lib_str, self._oi_iuloc[unum])
        return iulib_in

    # ---- Dates & Times ----

    @staticmethod
    def GetTD() -> str:
        """Returns the current time and date as a string."""
        months = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')
        now = datetime.datetime.now()
        yy = now.year % 100
        return (f'{now.hour:02d}:{now.minute:02d}:{now.second:02d} '
                f'{now.day:02d}-{months[now.month - 1]}-{yy:02d} ')

    def StartTimer(self) -> None:
        """Record the current monotonic millisecond timestamp as the start of a timed pass."""
        self._report_str = ''
        self._t1_ms = int(time.monotonic() * 1000) & 0x7FFFFFFF

    def MarkTime(self) -> None:
        """Compute and store elapsed milliseconds since ``StartTimer`` was called."""
        t2 = int(time.monotonic() * 1000) & 0x7FFFFFFF
        self._elapsed_ms = max(0, t2 - self._t1_ms)

    def ReportTime(self) -> str:
        """Format the elapsed pass duration recorded by ``MarkTime`` as ``'Elapsed time: S.MMM seconds.'``."""
        if not self._report_str:
            secs = self._elapsed_ms // 1000
            ms = self._elapsed_ms % 1000
            self._report_str = f'Elapsed time: {secs}.{ms:03d} seconds.'
        return self._report_str
