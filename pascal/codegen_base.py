"""Base data structures, constants, and driver for the MC68000 Code Generator."""

from __future__ import annotations

import enum
import sys
from typing import Optional

from lisalib import (
    AbortCompilation,
    IOCloseKind,
    IOFCB,
    IONewline,
    LisaCloseOpt,
    LisaRuntime,
    ObjBlock,
    ObjDesc,
    PasHaltException,
    RegMask,
    UntypedFile,
    alfa8,
    i16,
    i32,
    pdiv,
    pmod,
    u16,
    u32,
)

TITLE = 'Lisa Pascal MC68000 Code Generator '
VERSION = 'V1.0 (23-Nov-2026)'

D0 = 0
D1 = 1
D2 = 2
D3 = 3
D4 = 4
D5 = 5
D6 = 6
D7 = 7

A0 = 8
A1 = 9
A2 = 10
A3 = 11
A4 = 12
A5 = 13
A6 = 14
SP = 15

Dlow = D0
Dhigh = D3
Alow = A0
Ahigh = A2
A1st = A3
Anth = A4
D1st = D4
Dnth = D7

ByteOp = 1
WordOp = 2
LongOp = 3
Quad = 4

MAXUNITS = 256
MAXCODE = 4000
MAXEXT = 200
MAX_PATHNAME = 255
EMITDEPOSIT = False
ALFALEN = 8
MAXLNUM = 65000
OPFNAME = 'N68K.OPCODES'


class CAttrKind(enum.IntEnum):
    """Operand addressing and value-representation kinds for CAttr descriptors."""

    NUL = 0
    EXPR = 1
    ADDR = 2
    INDX = 3
    CNST = 4
    COND = 5
    VARB = 6
    BOOL = 7
    STCK = 8
    BITZ = 9


class GCondition(enum.IntEnum):
    """Signed (LT..NE) and unsigned (HI, LS) relational condition codes for COND."""

    LT = 0
    LE = 1
    GT = 2
    GE = 3
    EQ = 4
    NE = 5
    HI = 6
    LS = 7


class ConstKind(enum.IntEnum):
    """Compile-time constant categories stored in a Valu record."""

    SCALCNST = 0
    REALCNST = 1
    STRCNST = 2
    PAOCCNST = 3
    SETCNST = 4


class Flags(enum.IntEnum):
    """Per-word code-buffer tags driving span-dependent jump optimization."""

    ABSI = 0
    JMPS = 1
    JMPL = 2
    NOPI = 3
    CASJ = 4


class StrCRec:
    """Linked-list node holding an 8-character chunk of a string or PAOC literal."""

    __slots__ = ('StrVal', 'Next')

    def __init__(self, str_val: str = '        ', nxt: Optional['StrCRec'] = None) -> None:
        self.StrVal: str = alfa8(str_val)
        self.Next: Optional['StrCRec'] = nxt


class IntList:
    """Singly linked list of 16-bit words for set bitmasks and patch-offset chains."""

    __slots__ = ('Int', 'Next')

    def __init__(self, val: int = 0, nxt: Optional['IntList'] = None) -> None:
        self.Int: int = val
        self.Next: Optional['IntList'] = nxt


class Valu:
    """Constant value record.

    Stores scalar/pointer/real words in IValu[0..1] (high word first), string or
    PAOC character chains in StrValu, or multi-word set bitmasks in SetValu.
    """

    __slots__ = ('CstKind', 'IValu', 'Len', 'StrValu', 'SetBytes', 'SetValu', 'FrontAddress')

    def __init__(self) -> None:
        self.CstKind: ConstKind = ConstKind.SCALCNST
        self.IValu: list[int] = [0, 0]  # 2 x 16-bit signed Integers (high word first)
        self.Len: int = 0
        self.StrValu: Optional[StrCRec] = None
        self.SetBytes: int = 0
        self.SetValu: Optional[IntList] = None
        self.FrontAddress: bool = False

    def copy(self) -> 'Valu':
        """Return a shallow copy of this constant descriptor with a cloned IValu pair."""
        v = Valu()
        v.CstKind = self.CstKind
        v.IValu = [self.IValu[0], self.IValu[1]]
        v.Len = self.Len
        v.StrValu = self.StrValu
        v.SetBytes = self.SetBytes
        v.SetValu = self.SetValu
        v.FrontAddress = self.FrontAddress
        return v

    def set_from(self, other: 'Valu') -> None:
        """Copy all constant fields in place from another Valu record."""
        self.CstKind = other.CstKind
        self.IValu[0] = other.IValu[0]
        self.IValu[1] = other.IValu[1]
        self.Len = other.Len
        self.StrValu = other.StrValu
        self.SetBytes = other.SetBytes
        self.SetValu = other.SetValu
        self.FrontAddress = other.FrontAddress


def ValuLInt(v: Valu) -> int:
    """Combine big-endian 16-bit words v.IValu[0..1] into a signed 32-bit LongInt."""
    return i32(i16(v.IValu[0]) * 65536 + u16(v.IValu[1]))


def SetValuLInt(v: Valu, val: int) -> None:
    """Split a 32-bit integer into big-endian 16-bit words v.IValu[0] (high) and v.IValu[1] (low)."""
    u = u32(val)
    v.IValu[0] = i16((u >> 16) & 0xFFFF)
    v.IValu[1] = i16(u & 0xFFFF)


class BigCRef:
    """Pending PC-relative literal-pool reference for a string, PAOC, or set constant."""

    __slots__ = ('Loc', 'StartLoc', 'BigVal', 'Next')

    def __init__(self) -> None:
        self.Loc: int = 0
        self.StartLoc: int = 0
        self.BigVal: Valu = Valu()
        self.Next: Optional['BigCRef'] = None


class CAttr:
    """Expression / operand descriptor record.

    Tracks whether an evaluated subexpression resides in a register (EXPR/BOOL/BITZ),
    indirect address (ADDR), base+index EA (INDX), lexical/common variable (VARB),
    literal (CNST), CPU condition codes (COND), or stack top (STCK).
    """

    __slots__ = (
        'cKind', 'ExReg', 'AOffset', 'AdReg', 'VOffset', 'VLev',
        'InOffset', 'InxAReg', 'InxRReg', 'LongIndex', 'CValu', 'CC',
    )

    def __init__(self, ckind: CAttrKind = CAttrKind.NUL) -> None:
        self.cKind: CAttrKind = ckind
        self.ExReg: int = -1
        self.AOffset: int = 0
        self.AdReg: int = -1
        self.VOffset: int = 0
        self.VLev: int = 0
        self.InOffset: int = 0
        self.InxAReg: int = -1
        self.InxRReg: int = -1
        self.LongIndex: bool = False
        self.CValu: Valu = Valu()
        self.CC: GCondition = GCondition.LT

    def copy(self) -> 'CAttr':
        """Return an independent copy of this operand descriptor and its embedded Valu."""
        c = CAttr(self.cKind)
        c.ExReg = self.ExReg
        c.AOffset = self.AOffset
        c.AdReg = self.AdReg
        c.VOffset = self.VOffset
        c.VLev = self.VLev
        c.InOffset = self.InOffset
        c.InxAReg = self.InxAReg
        c.InxRReg = self.InxRReg
        c.LongIndex = self.LongIndex
        c.CValu = self.CValu.copy()
        c.CC = self.CC
        return c

    def set_from(self, other: 'CAttr') -> None:
        """Overwrite all fields of this operand descriptor from another CAttr."""
        self.cKind = other.cKind
        self.ExReg = other.ExReg
        self.AOffset = other.AOffset
        self.AdReg = other.AdReg
        self.VOffset = other.VOffset
        self.VLev = other.VLev
        self.InOffset = other.InOffset
        self.InxAReg = other.InxAReg
        self.InxRReg = other.InxRReg
        self.LongIndex = other.LongIndex
        self.CValu.set_from(other.CValu)
        self.CC = other.CC


class ProcRef:
    """External symbol descriptor tracking linker/user names, lexical level, and patch offsets."""

    __slots__ = ('LinkName', 'UserName', 'RefList', 'Next', 'PFLev')

    def __init__(self) -> None:
        self.LinkName: str = '        '
        self.UserName: str = '        '
        self.RefList: Optional[IntList] = None
        self.Next: Optional['ProcRef'] = None
        self.PFLev: int = 0


class LabelRec:
    """Binary-search-tree node for an internal I-code label and its forward-reference chain."""

    __slots__ = ('LabelNo', 'Llink', 'Rlink', 'Defined', 'RefList', 'Loc')

    def __init__(self, label_no: int = 0) -> None:
        self.LabelNo: int = label_no
        self.Llink: Optional['LabelRec'] = None
        self.Rlink: Optional['LabelRec'] = None
        self.Defined: bool = False
        self.RefList: Optional[IntList] = None
        self.Loc: int = 0


class UserLabel:
    """Pascal user-label record mapping source label number to internal and global linker IDs."""

    __slots__ = ('UserNo', 'IntNo', 'LinkerNo', 'Next')

    def __init__(self) -> None:
        self.UserNo: int = 0
        self.IntNo: int = 0
        self.LinkerNo: int = -1
        self.Next: Optional['UserLabel'] = None


class CodComRec:
    """Binary-search-tree node recording a COMMON block symbol and its A5-offset relocations."""

    __slots__ = ('Left', 'Right', 'HashNo', 'CommonNo', 'CommonKind', 'Name', 'RefList')

    def __init__(self) -> None:
        self.Left: Optional['CodComRec'] = None
        self.Right: Optional['CodComRec'] = None
        self.HashNo: int = 0
        self.CommonNo: int = 0
        self.CommonKind: int = 0
        self.Name: str = '        '
        self.RefList: Optional[IntList] = None


class RegSlot:
    """Reference-count entry tracking active allocations of an MC68000 register."""

    __slots__ = ('Count',)

    def __init__(self) -> None:
        self.Count: int = 0


class WithEntry:
    """Saved WITH-statement base descriptor and pointer-indirection flag."""

    __slots__ = ('Cat', 'Indirect')

    def __init__(self) -> None:
        self.Cat: CAttr = CAttr()
        self.Indirect: bool = False


class FCAllEntry:
    """Nested function-call state storing result byte size, saved-register mask, and stack flag."""

    __slots__ = ('Size', 'RegMask', 'OnStack')

    def __init__(self) -> None:
        self.Size: int = 0
        self.RegMask: int = 0
        self.OnStack: bool = False


class Opcodes:
    """Binary-search-tree node holding an 8-char assembler opcode from N68K.OPCODES."""

    __slots__ = ('Opcode', 'Llink', 'Rlink')

    def __init__(self, opcode: str = '        ') -> None:
        self.Opcode: str = alfa8(opcode)
        self.Llink: Optional['Opcodes'] = None
        self.Rlink: Optional['Opcodes'] = None


class CodeGeneratorBase:
    """Holds all global state and the main/finalize lifecycle."""

    def __init__(self, rt: LisaRuntime, build30: bool = True) -> None:
        """Initialize pass-2 code buffers, register slots, symbol tables, and listing/file handles."""
        self.rt: LisaRuntime = rt
        self.build30: bool = build30

        self.Ic: int = 0
        self.Lc: int = 0
        self.LastCode: int = 0
        self.ProcLvl: int = 0
        self.Funct: bool = False
        self.Op: int = 0
        self.CurrCode: int = 0
        self.CaPatchLoc: int = 0
        self.DumpProcInfo: int = 0

        self.gCAttr: CAttr = CAttr()
        self.SavedPL: Optional[ProcRef] = None
        self.ProcList: Optional[ProcRef] = None
        self.BigCList: Optional[BigCRef] = None

        self.Reg: list[RegSlot] = [RegSlot() for _ in range(16)]
        self.CodeBuff: list[int] = [0] * (MAXCODE + 1)
        self.CodeBytes: bytearray = bytearray((MAXCODE + 1) * 2)  # populated by SwapCodeBuff
        self.Tags: list[Flags] = [Flags.ABSI] * (MAXCODE + 1)
        self.Delta: list[int] = [0] * (MAXCODE + 1)
        self.pLineNumber: list[int] = [0] * (MAXCODE + 1)
        self.pLblRef: list[int] = [0] * (MAXCODE + 1)
        self.pLblDef: list[int] = [0] * (MAXCODE + 1)

        self.RegSaveAttr: CAttr = CAttr()
        self.RegMask: RegMask = RegMask()

        self.WithLevel: int = 0
        self.WithCAttr: list[WithEntry] = [WithEntry() for _ in range(11)]  # 1..10

        self.ExtTmp: CAttr = CAttr()
        self.HaveExtTmp: bool = False
        self.RealTmp: CAttr = CAttr()
        self.HaveRealTmp: bool = False
        self.DblTmp: CAttr = CAttr()
        self.HaveDblTmp: bool = False

        self.LabelTree: Optional[LabelRec] = None
        self.ULabelList: Optional[UserLabel] = None
        self.NextLabel: int = 0

        self.UserProcs: list[Optional[ProcRef]] = [None] * (MAXEXT + 1)

        self.FCAllLevel: int = 0
        self.FCAllInfo: list[FCAllEntry] = [FCAllEntry() for _ in range(11)]  # 1..10

        self.GlobalLabels: bool = False
        self.SaveA6CAttr: CAttr = CAttr()
        self.SaveSpCAttr: CAttr = CAttr()
        self.GotoCAttr: CAttr = CAttr()

        self.CSizeHi: int = 0
        self.CSizeLo: int = 0

        self.ShortJumps: list[int] = [0] * 6  # 1..5

        self.A2Used: bool = False
        self.D3Used: bool = False
        self.ShortCalls: bool = False
        self.UnitFlag: bool = False

        self.UTextAddr: int = 0
        self.UTextSize: int = 0

        self.CommonTree: Optional[CodComRec] = None
        self.UserPNam: str = '        '
        self.CurrSeg: str = ''
        self.PrevSeg: str = ''

        self.MacFlag: bool = False
        self.SaveA2D3: bool = False

        self.InFile: UntypedFile = UntypedFile()
        self.InOpen: bool = False
        self.InBuff: bytearray = bytearray(512)
        self.InBlock: int = 0
        self.InByte: int = 0
        self.DeleteI: bool = False

        self.OutFile: Optional[ObjDesc] = None
        self.OutBlock: ObjBlock = ObjBlock()
        self.OutOpen: bool = False

        self.LineNumber: int = 0
        self.EndLineNbr: int = 0
        self.FirstLNum: int = 0
        self.LNum: int = 0

        self.CListFile: Optional[IOFCB] = None
        self.CListBufr: Optional[bytearray] = None
        self.CListOpen: bool = False

        self.ListFile: Optional[IOFCB] = None
        self.ListBufr: Optional[bytearray] = None
        self.ListOpen: bool = False
        self.Listing: bool = False
        self.AsmOnly: bool = False
        self.AsmProc: bool = False
        self.ShowAsmCode: bool = False
        self.AltListing: bool = False
        self.ListingOk: bool = False
        self.UseAsmIcode: bool = False
        self.ConsListing: bool = False
        self.FirstLine: bool = False
        self.FirstOnCons: bool = False
        self.LnOvflo: bool = False
        self.OpcodeTbl: Optional[Opcodes] = None

        self.DateStr: str = ''
        self.LkUpCalled: bool = False
        self.Substituted: bool = False
        self.Hex: str = '0123456789ABCDEF'

        self.Aborted: bool = False

    @property
    def Errors(self) -> int:
        """Current count of code-generation errors stored in the shared Pascal runtime."""
        return self.rt.pd_errors

    @Errors.setter
    def Errors(self, val: int) -> None:
        self.rt.pd_errors = val

    def ValuLInt(self, v: Valu) -> int:
        """Return the signed 32-bit integer represented by v.IValu[0..1]."""
        return ValuLInt(v)

    def SetValuLInt(self, v: Valu, val: int) -> None:
        """Store a signed 32-bit integer into v.IValu[0..1] in big-endian word order."""
        SetValuLInt(v, val)

    def SwapCodeBuff(self) -> None:
        """Populate self.CodeBytes with big-endian bytes of CodeBuff[0..Ic//2]."""
        limit = pdiv(self.Ic, 2)
        for idx in range(limit + 1):
            w = u16(self.CodeBuff[idx])
            self.CodeBytes[2 * idx] = (w >> 8) & 0xFF
            self.CodeBytes[2 * idx + 1] = w & 0xFF

    def Finalize(self) -> None:
        """Close .OBJ, .I, and listing files, report total generated code size, and shut down runtime I/O."""
        if self.OutOpen and self.OutFile is not None:
            anyway_flag = False
            if not self.Aborted and self.Errors != 0:
                sys.stdout.write('\n')
                sys.stdout.write(f'*** There were {self.Errors} errors ***\n')
                sys.stdout.write('Do you want to save the code file anyway? ')
                anyway_flag = self.rt.SUGetBool(False)

            if not self.Aborted and (self.Errors == 0 or anyway_flag):
                self.rt.CloseObjFile(self.OutFile, True)
                s1 = self.rt.PutIntP(self.CSizeHi, 1)
                s2 = self.rt.PutIntP(pdiv(self.CSizeLo, 10), 1)
                s3 = self.rt.PutIntP(pmod(self.CSizeLo, 10), 1)
                s = f'Total code size = {s1}{s2}{s3}'
                if self.Listing and not self.AsmOnly and self.ListFile is not None:
                    self.rt.PutcF(self.ListFile, IONewline)
                    self.rt.PutLineS(self.ListFile, s)
                if not self.ConsListing:
                    sys.stdout.write('\n')
                    sys.stdout.write(s + '\n')
            else:
                self.rt.CloseObjFile(self.OutFile, False)

        if self.InOpen:
            if self.DeleteI:
                self.rt.close_untyped(self.InFile, LisaCloseOpt.PURGE)
            else:
                self.rt.close_untyped(self.InFile, LisaCloseOpt.NORMAL)

        if self.CListOpen:
            self.rt.CloseF(self.CListFile, IOCloseKind.IONormal)
        if self.ListOpen:
            self.rt.CloseF(self.ListFile, IOCloseKind.IOLock)

        if self.Aborted:
            self.KillExec()
            sys.stdout.write('\nCode generation aborted!\n')

        self.rt.SUDone()
        self.rt.EndIO()

    def run(self) -> int:
        """Execute pass-2 initialization, module/unit code generation, timing report, and finalization."""
        try:
            self.Initialize()
            self.Middleize()
            self.rt.MarkTime()
            if self.Listing and not self.AsmOnly and self.ListFile is not None:
                line = self.rt.ReportTime()
                line = line[:8] + 'code generator ' + line[8:]
                self.rt.PutcF(self.ListFile, IONewline)
                self.rt.PutLineS(self.ListFile, line)
            if not self.ConsListing:
                sys.stdout.write('\n' + self.rt.ReportTime() + '\n')
            if self.MacFlag:
                if self.Listing and not self.AsmOnly and self.ListFile is not None:
                    self.rt.PutcF(self.ListFile, IONewline)
                    self.rt.PutLineS(self.ListFile, 'MACINTOSH code generated.')
                if not self.ConsListing:
                    sys.stdout.write('\nMACINTOSH code generated.\n')
        except AbortCompilation:
            pass
        except PasHaltException:
            return 1  # a fatal error
        self.Finalize()
        # The exit status: 1 when the compilation reported errors or was aborted
        return 1 if self.Aborted or self.Errors != 0 else 0
