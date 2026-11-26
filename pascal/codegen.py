"""MC68000 code generator (pass 2) for the Lisa Pascal cross-compiler."""

from __future__ import annotations

import enum
import sys
from typing import Optional

from codegen_base import (
    A0,
    A1st,
    A2,
    A5,
    A6,
    Ahigh,
    ALFALEN,
    Alow,
    Anth,
    BigCRef,
    ByteOp,
    CAttr,
    CAttrKind,
    CodComRec,
    CodeGeneratorBase,
    ConstKind,
    D0,
    D1st,
    D3,
    D7,
    Dhigh,
    Dlow,
    Dnth,
    EMITDEPOSIT,
    Flags,
    GCondition,
    IntList,
    LabelRec,
    LongOp,
    MAXCODE,
    MAXLNUM,
    MAXUNITS,
    Opcodes,
    OPFNAME,
    ProcRef,
    Quad,
    SP,
    StrCRec,
    TITLE,
    UserLabel,
    Valu,
    ValuLInt,
    VERSION,
    WordOp,
)
from gen_disasm import DisasmMixin
from lisalib import (
    AbortCompilation,
    BlockType,
    IOByteSize,
    IOCloseKind,
    IODevType,
    IOFCB,
    IOModes,
    IONewline,
    ObjVarBlock,
    PromptState,
    RegMask,
    SUBell,
    SUMaxStrLeng,
    UntypedFile,
    VariantType,
    alfa8,
    i16,
    i32,
    i8,
    odd,
    pcopy,
    pdelete,
    pdiv,
    pget_ch,
    pinsert,
    pmod,
    ppos,
    pset_ch,
    u32,
)


class _LblKinds(enum.IntEnum):
    """Disassembly label categories for code targets and literal-pool constants."""

    NormalLbl = 0
    SetLbl = 1
    PkdLbl = 2
    StrLbl = 3
    NoLbl = 4


class CodeGenerator(DisasmMixin, CodeGeneratorBase):
    """Lisa Pascal MC68000 Code Generator in Python.

    Translates intermediate .I files produced by pass 1 into Lisa .OBJ object
    modules and optional interleaved or standalone MC68000 assembly listings.
    """

    # ========================================================================
    # 1. Listing merger, I-code reader, emitters, registers, labels, and common tables
    # ========================================================================

    def KillExec(self) -> None:
        """Stop any active Workshop exec file and report OS errors on failure."""
        i = self.rt.SUStopExec()
        if i > 0:
            sys.stdout.write(f'Error number {i} killing OS exec.\n')
            strg = self.rt.SUErrText('OSErrs.Err', i)
            sys.stdout.write(f'{strg}\n')
            self.FirstOnCons = False
            self.rt.SUWaitSp()

    def CodError(self, N: int) -> None:
        """Report code-generator error N with current IC and I/O offsets, aborting on Escape."""
        self.KillExec()
        msg = self.rt.SUErrText('PasErrs.Err', N)
        self.Errors = self.Errors + 1
        sys.stdout.write('\n')
        sys.stdout.write(f'{SUBell}*** Within {self.UserPNam} (Error {N}): {msg} ***\n')
        loc = self.rt.GetObjPtr(self.OutFile) if self.OutFile is not None else 0
        sys.stdout.write(
            f'IC = {self.Ic}, IN = {self.InBlock}:{self.InByte}, '
            f'OUT = {pdiv(loc, 512)}:{pmod(loc, 512)}\n'
        )
        what_user_typed = self.rt.SUWaitEscOrSp()
        if what_user_typed == PromptState.SUEscape:
            self.Aborted = True
            raise AbortCompilation()
        sys.stdout.write('\n')
        self.FirstOnCons = False

    def VerifyId(self, OrigId: str) -> str:
        """Trim an 8-char identifier and pad with '%' in $ASM ONLY mode if it collides with an MC68000 opcode."""
        orig = alfa8(OrigId)

        def is_opcode(id_val: str) -> bool:
            if self.AsmOnly:
                p = self.OpcodeTbl
                while p is not None:
                    if p.Opcode == id_val:
                        return True
                    if p.Opcode < id_val:
                        p = p.Rlink
                    else:
                        p = p.Llink
            return False

        chars: list[str] = []
        i = 1
        ch = orig[0]
        while True:
            chars.append(ch)
            i += 1
            if i > ALFALEN:
                ch = ' '
            else:
                ch = orig[i - 1]
            if ch == ' ':
                break

        if i <= ALFALEN and is_opcode(orig):
            while True:
                chars.append('%')
                i += 1
                if i > ALFALEN:
                    break

        return ''.join(chars)

    def MakeGlobalLbl(self, LinkName: str) -> str:
        """Convert an internal '$xxxxxxx' global-label linker name into assembler form 'Gxxxxxx%'."""
        ln = alfa8(LinkName)
        return 'G' + ln[1 : ALFALEN - 1] + '%'

    def LkUp(self, Lc: int, Dest: int, Name: str) -> str:
        """Resolve an external procedure or global label name referenced at byte offset Lc for disassembly."""
        self.LkUpCalled = True
        i = Lc
        pL = self.SavedPL
        while pL is not None:
            lInt = pL.RefList
            while lInt is not None:
                if i == lInt.Int - self.Delta[pdiv(lInt.Int, 2)]:
                    if alfa8(pL.UserName)[0] != '*':
                        Name = self.VerifyId(pL.UserName)
                    else:
                        Name = self.MakeGlobalLbl(pL.LinkName)
                    self.Substituted = True
                lInt = lInt.Next
            pL = pL.Next
        return Name

    def MakeHex(self, Value: int, Width: int) -> str:
        """Format the low Width (1..8) hexadecimal digits of Value in uppercase."""
        if Width <= 0:
            return ''
        if Width > 8:
            Width = 8
        if Width < 1:
            Width = 1
        u = u32(Value)
        return ''.join(self.Hex[(u >> (4 * (7 - idx))) & 15] for idx in range(8 - Width, 8))

    def ListLine(
        self,
        Loc: int,
        LineNumber: int,
        Line: str,
        ShowingAsm: bool,
    ) -> tuple[int, str]:
        """Format and emit one compiler source listing line, inserting code offsets or $ASM ONLY comments."""
        assert self.ListFile is not None
        Col1 = 1
        Len = len(Line)
        while Col1 < Len and pget_ch(Line, Col1) == '\x0c':
            Col1 += 1
        Col5 = Col1 + 4

        if Col5 <= Len:
            Ch = pget_ch(Line, Col5)
        else:
            Ch = ' '

        if '0' <= Ch <= '9':
            LineNumber = 0
            i = Col5 - 4
            while True:
                Ch = pget_ch(Line, i)
                if '0' <= Ch <= '9':
                    LineNumber = LineNumber * 10 + ord(Ch) - ord('0')
                i += 1
                if i > Col5:
                    break

            if self.AsmOnly:
                Line = ';' + pcopy(Line, 19, len(Line) - 18)
            else:
                if ShowingAsm:
                    Line = pinsert('       ', Line, Col1 + 19, SUMaxStrLeng)
                elif pget_ch(Line, Col1 + 14) == ' ':
                    Line = pinsert('       ', Line, Col1 + 19, SUMaxStrLeng)
                else:
                    X = self.MakeHex(Loc, 6) + ' '
                    Line = pinsert(X, Line, Col1 + 19, SUMaxStrLeng)

            self.rt.PutLineS(self.ListFile, Line)
        elif not self.AsmOnly:
            if self.FirstLine:
                self.FirstLine = False
                if ppos('Lisa Pascal Compiler', Line) == 1:
                    self.rt.PutLineS(self.ListFile, Line)
                    self.rt.PutStrS(self.ListFile, TITLE + VERSION, 0)
                    self.rt.PutStrS(
                        self.ListFile,
                        ' ',
                        79 - len(TITLE) - len(VERSION) - len(self.DateStr),
                    )
                    self.rt.PutLineS(self.ListFile, self.DateStr)
                else:
                    if ppos('Elapsed', Line) == 1:
                        Line = pinsert('compilation ', Line, 9, SUMaxStrLeng)
                    self.rt.PutLineS(self.ListFile, Line)
            else:
                if ppos('Elapsed', Line) == 1:
                    Line = pinsert('compilation ', Line, 9, SUMaxStrLeng)
                self.rt.PutLineS(self.ListFile, Line)

        return LineNumber, Line

    def MakeListing(self) -> None:
        """Merge pass-1 source listing lines with disassembled MC68000 instructions and literal-pool data."""
        if self.LnOvflo:
            if self.FirstOnCons:
                sys.stdout.write('\n')
            sys.stdout.write(
                f'{SUBell}The listing file contains more than {MAXLNUM} lines!  '
                f'The rest of the listing will\n'
            )
            sys.stdout.write(
                'be produced, but it will *not* contain any code information.  This is due to a\n'
            )
            sys.stdout.write(
                f'limitation between the Compiler and the Code Generator...Sorry about that!{SUBell}\n'
            )
            if self.CListFile is not None:
                while True:
                    ok, Line = self.rt.GetLine(self.CListFile)
                    if not ok:
                        break
                    self.LineNumber, Line = self.ListLine(0, self.LineNumber, Line, True)
            sys.stdout.write('\n')
            self.FirstOnCons = False
            self.Listing = False
            self.ConsListing = False
            self.ListingOk = False
            return

        if not self.ShowAsmCode and self.LineNumber >= self.EndLineNbr:
            return

        if self.FirstLine and self.ConsListing:
            sys.stdout.write('\n')
            self.FirstOnCons = False

        if self.AsmProc:
            Last = self.EndLineNbr
        else:
            Last = self.FirstLNum - 1

        while self.LineNumber < Last:
            assert self.CListFile is not None
            ok, Line = self.rt.GetLine(self.CListFile)
            if not ok:
                return
            self.LineNumber, Line = self.ListLine(0, self.LineNumber, Line, True)

        if self.DumpProcInfo == 1:
            SizeIndex = pdiv(self.CaPatchLoc, 2)
        else:
            SizeIndex = -1

        assert self.ListFile is not None
        list_file = self.ListFile

        def PrntHex(Value: int, Width: int) -> None:
            self.rt.PutStrS(list_file, self.MakeHex(Value, Width), 0)

        def SetupLbl(LblNbr: int) -> tuple[str, _LblKinds]:
            if LblNbr < 8000:
                lbl_prefix = 'L'
                lbl_kind = _LblKinds.NormalLbl
            else:
                lbl_prefix = 'Cst'
                if LblNbr < 16000:
                    lbl_kind = _LblKinds.SetLbl
                    LblNbr -= 8000
                elif LblNbr < 24000:
                    lbl_kind = _LblKinds.PkdLbl
                    LblNbr -= 16000
                else:
                    lbl_kind = _LblKinds.StrLbl
                    LblNbr -= 24000
            return lbl_prefix + self.rt.PutIntP(LblNbr, -4), lbl_kind

        NextI = 0
        IcDIV2 = pdiv(self.Ic, 2)
        DoingCase = False
        CaseLbl = 0
        CaseLabel = ''

        def DisAss1Line(Index: int, Name: str) -> int:
            """Disassemble and emit the instruction, inline word, or CASE-table entry at word Index."""
            nonlocal DoingCase, CaseLbl, CaseLabel
            base_byte = 2 * Index
            InstLoc = Index + Index

            def DefineGlobalLbl(inst_loc: int) -> None:
                lpULab = self.ULabelList
                while lpULab is not None:
                    if lpULab.LinkerNo >= 0:
                        lpILab = self.LookUpILabel(lpULab.IntNo)
                        if inst_loc == (lpILab.Loc - self.Delta[pdiv(lpILab.Loc, 2)]):
                            link_name = self.MakeLName(lpULab.LinkerNo)
                            g_lbl = self.MakeGlobalLbl(link_name)
                            self.rt.PutLineS(list_file, '         .DEF    ' + g_lbl)
                            self.rt.PutLineS(list_file, g_lbl)
                            return
                    lpULab = lpULab.Next

            def DumpHex(bytes_shown: int, bytes_used: int) -> int:
                for _ in range(6):
                    if bytes_shown < bytes_used:
                        PrntHex(self.CodeBytes[base_byte + bytes_shown], 2)
                    else:
                        self.rt.PutStrS(list_file, '  ', 0)
                    if odd(bytes_shown):
                        self.rt.PutcF(list_file, ' ')
                    bytes_shown += 1
                return bytes_shown

            def ConvertHexConstants(operand: str) -> str:
                semi = ppos(';', operand)
                if semi > 0:
                    operand = operand[: semi - 1]
                operand = self.rt.SUTrimBlanks(operand) + ' '

                First = ppos('$', operand)
                while First > 0:
                    Valu = 0
                    Stop = False
                    last_idx = First + 1
                    while True:
                        ch = pget_ch(operand, last_idx)
                        if '0' <= ch <= '9':
                            Valu = i32(Valu * 16 + ord(ch) - ord('0'))
                        elif 'A' <= ch <= 'F':
                            Valu = i32(Valu * 16 + ord(ch) - ord('A') + 10)
                        else:
                            Stop = True
                        if not Stop:
                            last_idx += 1
                        else:
                            break

                    ValuLen = last_idx - First
                    if ValuLen < 6:
                        Valu = i16(Valu)

                    operand = pdelete(operand, First, ValuLen)
                    operand = pinsert(self.rt.PutIntP(Valu, 0), operand, First, 80)
                    First = ppos('$', operand)

                return self.rt.SUTrimBlanks(operand)

            def RefToLbl(LblNbr: int, operand: str) -> str:
                semi = ppos(';', operand)
                if semi == 0:
                    opnd = operand
                    comment = ''
                else:
                    opnd = self.rt.SUTrimBlanks(pcopy(operand, 1, semi - 1))
                    comment = pcopy(operand, semi, len(operand) - semi + 1)

                ref_lbl, _ = SetupLbl(LblNbr)

                lp = ppos('(', opnd)
                if lp == 0:
                    cm = ppos(',', opnd)
                    if cm == 0:
                        opnd = ref_lbl
                    else:
                        opnd = ref_lbl + pdelete(opnd, 1, cm - 1)
                else:
                    opnd = ref_lbl + pdelete(opnd, 1, lp - 1)

                pad = 16 - len(opnd)
                if pad > 0:
                    opnd = opnd + (' ' * pad)
                return opnd + comment

            def InsertProcHdr() -> None:
                self.rt.PutLineS(list_file, ';')
                if self.CurrSeg != self.PrevSeg:
                    self.rt.PutLineS(list_file, f"         .SEG    '{self.CurrSeg}'")
                    self.PrevSeg = self.CurrSeg

                if self.Funct:
                    self.rt.PutStrS(list_file, '         .FUNC   ', 0)
                elif self.ProcLvl != 1:
                    self.rt.PutStrS(list_file, '         .PROC   ', 0)
                else:
                    self.rt.PutStrS(list_file, '         .MAIN   ', 0)
                name_str = self.VerifyId(Name)
                self.rt.PutLineS(list_file, name_str)

                if self.SavedPL is not None:
                    pL = self.SavedPL
                    self.rt.PutLineS(list_file, ';')
                    while pL is not None:
                        self.rt.PutStrS(list_file, '         .REF    ', 0)
                        if alfa8(pL.UserName)[0] != '*':
                            name_str = self.VerifyId(pL.UserName)
                        else:
                            name_str = self.MakeGlobalLbl(pL.LinkName)
                        self.rt.PutLineS(list_file, name_str)
                        pL = pL.Next
                    self.rt.PutLineS(list_file, ';')

            Lbl = ''
            if self.pLblDef[Index] != 0:
                Lbl, _ = SetupLbl(abs(self.pLblDef[Index]))
            elif Index == 0 and not self.AsmOnly:
                Lbl = alfa8(Name)

            if self.pLineNumber[Index] >= 0:
                self.Substituted = False
                self.LkUpCalled = False
                BytesUsed, Opcode, Operand = self.Disassembler(0, self.CodeBytes, base_byte, True)
                if self.AsmOnly:
                    Operand = ConvertHexConstants(Operand)
                    if not self.LkUpCalled and Opcode == 'JMP' and Operand == '0':
                        Opnd = ''
                        Opnd = self.LkUp(2 * (Index + 1), 0, Opnd)
                        if self.Substituted:
                            Operand = Opnd
                semi = ppos(';', Operand)
                if semi > 0 and self.Substituted:
                    Operand = Operand[: semi - 1]
                if self.pLblRef[Index] != 0:
                    Operand = RefToLbl(abs(self.pLblRef[Index]), Operand)
                Inline = False
                DoingCase = False
            else:
                Inline = True
                BytesUsed = 2
                Opcode = '.WORD'
                if self.pLblRef[Index] < 0:
                    if not DoingCase:
                        DoingCase = True
                        CaseLbl += 1
                        CaseLabel = 'Case' + self.rt.PutIntP(CaseLbl, 1)
                        Lbl = CaseLabel
                    TempLbl, _ = SetupLbl(abs(self.pLblRef[Index]))
                    Operand = f'{TempLbl}-{CaseLabel}+2'
                else:
                    X = self.MakeHex(self.CodeBytes[base_byte], 2)
                    Y = self.MakeHex(self.CodeBytes[base_byte + 1], 2)
                    Operand = f'${X}{Y}'
                    DoingCase = False

            BytesShown = 0
            if self.AsmOnly:
                if Index == 0:
                    InsertProcHdr()
                DefineGlobalLbl(InstLoc)
            else:
                self.rt.PutStrS(list_file, ' ', 19)
                PrntHex(InstLoc, 6)
                self.rt.PutcF(list_file, ' ')
                BytesShown = DumpHex(BytesShown, BytesUsed)

            self.rt.PutStrS(list_file, Lbl, -(ALFALEN + 1))
            self.rt.PutStrS(list_file, Opcode, -ALFALEN)
            self.rt.PutLineS(list_file, Operand)

            if not self.AsmOnly and BytesShown < BytesUsed:
                while True:
                    self.rt.PutStrS(list_file, ' ', 19)
                    PrntHex(InstLoc + BytesShown, 6)
                    self.rt.PutcF(list_file, ' ')
                    BytesShown = DumpHex(BytesShown, BytesUsed)
                    self.rt.PutcF(list_file, IONewline)
                    if BytesShown >= BytesUsed:
                        break

            if (
                not Inline
                and self.CodeBytes[base_byte + 1] == 0x95
                and self.CodeBytes[base_byte] == 0x4E
            ):
                b2 = self.CodeBytes[base_byte + 2]
                b3 = self.CodeBytes[base_byte + 3]
                if self.AsmOnly:
                    self.rt.PutStrS(list_file, '         .BYTE   ', 0)
                else:
                    self.rt.PutStrS(list_file, ' ', 19)
                    PrntHex(Index + Index + 2, 6)
                    self.rt.PutcF(list_file, ' ')
                    PrntHex(b2, 2)
                    self.rt.PutcF(list_file, ' ')
                    PrntHex(b3, 2)
                    self.rt.PutStrS(list_file, '.BYTE   ', 27)
                self.rt.PutcF(list_file, '$')
                PrntHex(b2, 2)
                self.rt.PutcF(list_file, ',')
                self.rt.PutcF(list_file, '$')
                PrntHex(b3, 2)
                self.rt.PutLineS(list_file, '         ; lev#, proc#')
                BytesUsed += 2

            return BytesUsed

        def DumpData(Index: int) -> int:
            """Format and emit literal-pool string, PAOC, set, or MacsBug trailer data starting at word Index."""
            base_byte = 2 * Index
            if self.pLblDef[Index] != 0:
                Lbl, LblKind = SetupLbl(abs(self.pLblDef[Index]))
            else:
                Lbl = ';' if self.AsmOnly else ' '
                LblKind = _LblKinds.NoLbl

            Ascii = LblKind in (_LblKinds.PkdLbl, _LblKinds.StrLbl)
            InstLoc = Index + Index
            BytesUsed = 0

            if not self.AsmOnly and LblKind != _LblKinds.NoLbl:
                self.rt.PutStrS(list_file, ' ', 19)
                PrntHex(InstLoc, 6)
                self.rt.PutStrS(list_file, ' ', 16)
            self.rt.PutLineS(list_file, Lbl)

            if Index == SizeIndex:
                if not self.AsmOnly:
                    self.rt.PutStrS(list_file, ' ', 19)
                    PrntHex(InstLoc, 6)
                    self.rt.PutcF(list_file, ' ')
                    PrntHex(self.CodeBytes[base_byte], 2)
                    PrntHex(self.CodeBytes[base_byte + 1], 2)
                    self.rt.PutStrS(list_file, ' ', 11)
                self.rt.PutLineS(list_file, 'CstSize  .WORD   Last-CstSize-2')
                return 2

            scan_idx = Index
            while True:
                BytesUsed += 2
                scan_idx += 1
                if scan_idx >= IcDIV2 or self.pLblDef[scan_idx] != 0 or scan_idx == SizeIndex:
                    break

            def GetChunk(bytes_shown: int) -> tuple[int, str]:
                if self.AsmOnly:
                    MaxChunk = 58 if Ascii else 22
                else:
                    MaxChunk = 6
                Remaining = BytesUsed - bytes_shown
                chunk_size = MaxChunk if Remaining > MaxChunk else Remaining
                quote = "'"
                if Ascii:
                    first_quote = True
                    for idx_c in range(1, chunk_size + 1):
                        b_val = self.CodeBytes[base_byte + bytes_shown]
                        ch = chr(b_val)
                        if ch == "'":
                            if first_quote:
                                quote = '"'
                                first_quote = False
                            elif ch == quote:
                                return idx_c - 1, quote
                        elif ch == '"':
                            if first_quote:
                                quote = "'"
                                first_quote = False
                            elif ch == quote:
                                return idx_c - 1, quote
                        elif b_val < 32 or b_val > 127:
                            if idx_c == 1:
                                return 1, quote
                            return idx_c - 1, quote
                        bytes_shown += 1
                return chunk_size, quote

            def DumpHex(bytes_shown: int, chunk_size: int) -> None:
                for idx_h in range(1, 7):
                    if idx_h > chunk_size:
                        self.rt.PutStrS(list_file, '  ', 0)
                    else:
                        PrntHex(self.CodeBytes[base_byte + bytes_shown], 2)
                    if not odd(idx_h):
                        self.rt.PutcF(list_file, ' ')
                    bytes_shown += 1

            if LblKind != _LblKinds.StrLbl:
                BytesShown = 0
            else:
                b0 = self.CodeBytes[base_byte]
                if not self.AsmOnly:
                    self.rt.PutStrS(list_file, ' ', 19)
                    PrntHex(InstLoc, 6)
                    self.rt.PutcF(list_file, ' ')
                    PrntHex(b0, 2)
                    self.rt.PutStrS(list_file, ' ', 13)
                self.rt.PutStrS(list_file, '         .BYTE   ', 0)
                self.rt.PutLineS(list_file, self.rt.PutIntP(i8(b0), 1))
                BytesShown = 1

            while BytesShown < BytesUsed:
                ChunkSize, Quote = GetChunk(BytesShown)
                if not self.AsmOnly:
                    self.rt.PutStrS(list_file, ' ', 19)
                    PrntHex(InstLoc + BytesShown, 6)
                    self.rt.PutcF(list_file, ' ')
                    DumpHex(BytesShown, ChunkSize)

                if Ascii:
                    b_cur = self.CodeBytes[base_byte + BytesShown]
                    if ChunkSize == 1 and (b_cur < 32 or b_cur > 127):
                        self.rt.PutStrS(list_file, '         .BYTE   $', 0)
                        PrntHex(b_cur, 2)
                        BytesShown += 1
                    else:
                        self.rt.PutStrS(list_file, '         .ASCII  ', 0)
                        self.rt.PutcF(list_file, Quote)
                        for _ in range(ChunkSize):
                            self.rt.PutcF(list_file, chr(self.CodeBytes[base_byte + BytesShown]))
                            BytesShown += 1
                        self.rt.PutcF(list_file, Quote)
                else:
                    self.rt.PutStrS(list_file, '         .WORD   ', 0)
                    comment_chars = [' ; "']
                    for idx_w in range(1, ChunkSize + 1):
                        if idx_w == 1:
                            self.rt.PutcF(list_file, '$')
                        elif odd(idx_w):
                            self.rt.PutStrS(list_file, ',$', 0)
                        b_cur = self.CodeBytes[base_byte + BytesShown]
                        PrntHex(b_cur, 2)
                        ch_c = '.' if (b_cur < 32 or b_cur > 127) else chr(b_cur)
                        comment_chars.append(ch_c)
                        BytesShown += 1
                    if not self.AsmOnly and LblKind != _LblKinds.SetLbl:
                        for _ in range(pdiv(ChunkSize + 2, 2), 4):
                            self.rt.PutStrS(list_file, '      ', 0)
                        comment_chars.append('"')
                        self.rt.PutStrS(list_file, ''.join(comment_chars), 0)

                self.rt.PutcF(list_file, IONewline)

            return BytesUsed

        for i in range(IcDIV2):
            if not self.AsmProc:
                while (
                    self.LineNumber <= (abs(self.pLineNumber[i]) - 1)
                    and self.LineNumber < (self.LNum - 1)
                ):
                    assert self.CListFile is not None
                    ok, Line = self.rt.GetLine(self.CListFile)
                    if not ok:
                        return
                    self.LineNumber, Line = self.ListLine(
                        i + i, self.LineNumber, Line, self.ShowAsmCode
                    )

            if i == NextI:
                if self.ShowAsmCode:
                    if i < self.LastCode:
                        BytsUsed = DisAss1Line(i, self.UserPNam)
                    else:
                        BytsUsed = DumpData(i)
                    NextI = NextI + pdiv(BytsUsed, 2)

        if self.ShowAsmCode:
            if self.pLblDef[IcDIV2] != 0:
                Lbl, _ = SetupLbl(abs(self.pLblDef[IcDIV2]))
                if not self.AsmOnly:
                    self.rt.PutStrS(list_file, ' ', 19)
                    PrntHex(self.Ic, 6)
                    self.rt.PutStrS(list_file, ' ', 16)
                self.rt.PutLineS(list_file, Lbl)

            if self.DumpProcInfo == 1:
                if not self.AsmOnly:
                    self.rt.PutStrS(list_file, ' ', 19)
                    PrntHex(self.Ic, 6)
                    self.rt.PutStrS(list_file, ' ', 16)
                self.rt.PutLineS(list_file, 'Last')

        if not self.AsmProc:
            while self.LineNumber < self.EndLineNbr:
                assert self.CListFile is not None
                ok, Line = self.rt.GetLine(self.CListFile)
                if not ok:
                    return
                self.LineNumber, Line = self.ListLine(0, self.LineNumber, Line, True)

    def NextByte(self) -> int:
        """Read and return the next unsigned byte (0..255) from the 512-byte buffered .I stream."""
        if self.InByte > 511:
            self.InBlock += 1
            if self.rt.block_read(self.InFile, self.InBuff, 1, self.InBlock) != 1:
                self.CodError(409)
                self.Aborted = True
                raise AbortCompilation()
            self.InByte = 0

        res = self.InBuff[self.InByte] & 0xFF
        self.InByte += 1
        return res

    def NextWord(self) -> int:
        """Read a signed big-endian 16-bit integer from the .I input stream."""
        hi = self.NextByte()
        return i16((hi << 8) + self.NextByte())

    def GenWord(self, fOp: int, fTag: Flags) -> None:
        """Append a 16-bit word fOp with jump-optimization tag fTag to CodeBuff and advance Ic by 2."""
        self.CurrCode = pdiv(self.Ic, 2)
        if self.CurrCode <= MAXCODE:
            self.CodeBuff[self.CurrCode] = i16(fOp)
            self.pLineNumber[self.CurrCode] = self.LNum
            self.Tags[self.CurrCode] = fTag
            self.Ic += 2
        else:
            self.CodError(350)

    def Gen(self, fOp: int) -> None:
        """Emit a fixed 16-bit instruction or extension word tagged ABSI."""
        self.GenWord(fOp, Flags.ABSI)

    def GenR(self, fOp: int, r: int) -> None:
        """Emit opcode word fOp with register r encoded in bits 0..2."""
        self.GenWord(i16(fOp + pmod(r, 8)), Flags.ABSI)

    def GenRR(self, fOp: int, RR: int, r: int) -> None:
        """Emit opcode word fOp with register RR in bits 9..11 and register r in bits 0..2."""
        self.GenWord(i16(fOp + pmod(RR, 8) * 512 + pmod(r, 8)), Flags.ABSI)

    def PatchWord(self, fLoc: int, fValu: int) -> None:
        """Overwrite the 16-bit word in CodeBuff at byte offset fLoc with fValu."""
        self.CodeBuff[pdiv(fLoc, 2)] = i16(fValu)

    def GetReg(self, LoReg: int, HiReg: int) -> int:
        """Allocate the first free register in LoReg..HiReg and record A2/D3 usage when SaveA2D3 is set."""
        allocated = LoReg
        for i in range(LoReg, HiReg + 1):
            if self.Reg[i].Count <= 0:
                self.Reg[i].Count = 1
                allocated = i
                break
        else:
            sys.stdout.write(f'Register {LoReg}..{HiReg}\n')
            self.CodError(2001)
            allocated = LoReg

        if self.SaveA2D3:
            if allocated == A2:
                self.A2Used = True
            elif allocated == D3:
                self.D3Used = True
        return allocated

    def ReuseIfPossible(self, SAttr: CAttr, LoReg: int, HiReg: int) -> int:
        """Reuse a single-use register from SAttr within LoReg..HiReg for an upcoming GenEffAddr, or allocate a new one."""
        SAttr = SAttr.copy()
        i = -1
        if SAttr.cKind == CAttrKind.EXPR:
            if LoReg <= SAttr.ExReg <= HiReg:
                i = SAttr.ExReg
        elif SAttr.cKind == CAttrKind.ADDR:
            if LoReg <= SAttr.AdReg <= HiReg:
                i = SAttr.AdReg
        elif SAttr.cKind == CAttrKind.INDX:
            if LoReg <= SAttr.InxAReg <= HiReg:
                i = SAttr.InxAReg
            if LoReg <= SAttr.InxRReg <= HiReg:
                i = SAttr.InxRReg

        if i != -1:
            if self.Reg[i].Count > 1:
                i = self.GetReg(LoReg, HiReg)
            else:
                self.Reg[i].Count += 1
        else:
            i = self.GetReg(LoReg, HiReg)
        return i

    def FreeReg(self, fReg: int) -> None:
        """Decrement the reference count of scratch register fReg (D0..D3 or A0..A2)."""
        if D0 <= fReg <= Ahigh and (fReg <= Dhigh or fReg >= Alow):
            slot = self.Reg[fReg]
            if slot.Count <= 0:
                sys.stdout.write(f'Register {fReg}\n')
                self.CodError(2002)
                slot.Count = 0
            else:
                slot.Count -= 1

    def ClearRegs(self) -> None:
        """Reset reference counts to zero for all allocatable registers D0..A4."""
        for r in range(Dlow, Anth + 1):
            self.Reg[r].Count = 0

    def SaveRegs(self) -> int:
        """Push active registers in D0..A4 onto the stack via MOVE.L or MOVEM.L and return the restore mask."""
        LastReg = 0
        NRegs = 0
        lMask = 0
        lMask2 = 0
        Bit = 1
        for i in range(D0, Anth + 1):
            lMask = i16(lMask + lMask)
            if self.Reg[i].Count > 0:
                LastReg = i
                NRegs += 1
                lMask = i16(lMask + 1)
                lMask2 = i16(lMask2 + Bit)
            Bit = i16(Bit + Bit)
        for _ in range(Anth + 1, SP + 1):
            lMask = i16(lMask + lMask)

        if lMask != 0:
            if NRegs > 1:
                self.Gen(0x48E7)
                self.Gen(lMask)
            else:
                if LastReg <= D7:
                    self.GenR(0x2F00, LastReg)
                else:
                    self.GenR(0x2F08, LastReg)
        return i16(lMask2)

    def RestoreRegs(self, fRegMask: int) -> None:
        """Pop registers specified by post-increment bitmask fRegMask from the stack via MOVE.L or MOVEM.L."""
        fRegMask = i16(fRegMask)
        NRegs = 0
        LastReg = 0
        TempMask = fRegMask
        for i in range(16):
            if odd(TempMask):
                LastReg = i
                NRegs += 1
            TempMask = pdiv(TempMask, 2)

        if fRegMask != 0:
            if NRegs > 1:
                self.Gen(0x4CDF)
                self.Gen(fRegMask)
            else:
                if LastReg <= D7:
                    self.GenRR(0x2018, LastReg, SP)
                else:
                    self.GenRR(0x2058, LastReg, SP)

    def CheckClobber(self, fReg: int) -> int:
        """Copy fReg into a fresh scratch register if fReg is a register variable (D4..D7, A3..A4) or shared (Count > 1)."""
        if (A1st <= fReg <= Anth) or (Alow <= fReg <= Ahigh and self.Reg[fReg].Count > 1):
            NewReg = self.GetReg(Alow, Ahigh)
            fOp = 0x2008
            if NewReg >= A0:
                fOp += 0x40
            self.GenRR(fOp, NewReg, fReg)
            fReg = NewReg
        elif (D1st <= fReg <= Dnth) or (Dlow <= fReg <= Dhigh and self.Reg[fReg].Count > 1):
            NewReg = self.GetReg(Dlow, Dhigh)
            fOp = 0x2000
            if NewReg >= A0:
                fOp += 0x40
            self.GenRR(fOp, NewReg, fReg)
            fReg = NewReg
        return fReg

    def GetTemp(self, fCAttr: CAttr, fSize: int) -> None:
        """Allocate a word-aligned fSize-byte stack temporary in the current frame and populate fCAttr as VARB."""
        self.Lc = i16(self.Lc + fSize)
        fCAttr.cKind = CAttrKind.VARB
        fCAttr.VOffset = i16(-self.Lc)
        fCAttr.VLev = self.ProcLvl
        if odd(self.Lc):
            self.Lc = i16(self.Lc + 1)

    def FreeTemp(self, fCAttr: CAttr, fSize: int) -> None:
        """No-op placeholder for releasing a frame-allocated stack temporary."""
        pass

    def MakeLName(self, fLabelNo: int) -> str:
        """Format a global label number into an 8-character linker symbol '$ddddddd' (least-significant digit first)."""
        chars = ['$']
        for _ in range(2, ALFALEN + 1):
            chars.append(chr(ord('0') + pmod(fLabelNo, 10)))
            fLabelNo = pdiv(fLabelNo, 10)
        return ''.join(chars)

    def NewLabel(self) -> int:
        """Allocate and return a fresh negative internal label number for compiler-synthesized branches."""
        self.NextLabel = i16(self.NextLabel - 1)
        return self.NextLabel

    def LookUpILabel(self, fLabelNo: int) -> LabelRec:
        """Find or insert internal label fLabelNo in the procedure's LabelTree binary search tree."""
        def new_label_rec(lbl_no: int) -> LabelRec:
            rec = LabelRec(lbl_no)
            rec.Llink = None
            rec.Rlink = None
            rec.Defined = False
            rec.RefList = None
            return rec

        if self.LabelTree is None:
            self.LabelTree = new_label_rec(fLabelNo)
            return self.LabelTree

        lpLab = self.LabelTree
        while True:
            if lpLab.LabelNo == fLabelNo:
                return lpLab
            if lpLab.LabelNo < fLabelNo:
                if lpLab.Llink is None:
                    lpLab.Llink = new_label_rec(fLabelNo)
                    return lpLab.Llink
                lpLab = lpLab.Llink
            else:
                if lpLab.Rlink is None:
                    lpLab.Rlink = new_label_rec(fLabelNo)
                    return lpLab.Rlink
                lpLab = lpLab.Rlink

    def DefILabel(self, fLabNo: int) -> None:
        """Define internal label fLabNo at the current Ic and backpatch all queued forward branch words."""
        lpLab = self.LookUpILabel(fLabNo)
        lInt = lpLab.RefList
        while lInt is not None:
            self.PatchWord(lInt.Int, self.Ic)
            lInt = lInt.Next
        lpLab.Defined = True
        lpLab.Loc = self.Ic

    def ShiftMult(self, fValue: int) -> tuple[bool, int]:
        """Check whether fValue is a power of two in 1..256 (2**0..2**8) suitable for an MC68000 shift-immediate."""
        bits = 0
        if fValue > 0:
            while not odd(fValue):
                bits += 1
                fValue = pdiv(fValue, 2)
            ok = (fValue == 1) and (bits <= 8)
        else:
            ok = False
        return ok, bits

    def ExtRef(self) -> None:
        """Read an EXTREF I-code record and register the external procedure in ProcList and UserProcs."""
        lpRoc = ProcRef()
        lpRoc.LinkName = ''.join(chr(self.NextByte()) for _ in range(ALFALEN))
        lpRoc.UserName = ''.join(chr(self.NextByte()) for _ in range(ALFALEN))
        N = self.NextWord()
        lpRoc.PFLev = self.NextByte()
        lpRoc.RefList = None
        lpRoc.Next = self.ProcList
        self.ProcList = lpRoc
        self.UserProcs[N] = lpRoc

    def ComHash(self, N: int) -> int:
        """Compute the binary-tree hash key for COMMON unit number N."""
        return pmod(i16(N * 111), MAXUNITS)

    def ComRef(self) -> None:
        """Read a COMREF I-code record and insert its COMMON block descriptor into CommonTree."""
        lCom = CodComRec()
        lCom.Left = None
        lCom.Right = None
        lCom.Name = ''.join(chr(self.NextByte()) for _ in range(ALFALEN))
        lCom.CommonNo = self.NextByte()
        lHashNo = self.ComHash(lCom.CommonNo)
        lCom.CommonKind = self.NextByte()
        lCom.HashNo = lHashNo
        lCom.RefList = None
        if self.CommonTree is None:
            self.CommonTree = lCom
        else:
            mCom = self.CommonTree
            while True:
                if mCom.HashNo < lHashNo:
                    if mCom.Left is None:
                        mCom.Left = lCom
                        break
                    mCom = mCom.Left
                else:
                    if mCom.Right is None:
                        mCom.Right = lCom
                        break
                    mCom = mCom.Right

    def FindCommon(self, fCommonNo: int) -> Optional[CodComRec]:
        """Look up the CodComRec for COMMON unit number fCommonNo in CommonTree."""
        lHashNo = self.ComHash(fCommonNo)
        lCom = self.CommonTree
        while lCom is not None:
            if lCom.HashNo == lHashNo:
                return lCom
            if lCom.HashNo < lHashNo:
                lCom = lCom.Left
            else:
                lCom = lCom.Right
        return None

    def ComVRef(self, fCommonNo: int, fIc: int) -> None:
        """Record code-buffer byte offset fIc as a relocation site for COMMON block fCommonNo."""
        lCom = self.FindCommon(fCommonNo)
        assert lCom is not None
        lInt = IntList(fIc, lCom.RefList)
        lCom.RefList = lInt

    # ========================================================================
    # 2. Operand addressing, register loading, stores, comparisons, and sets
    # ========================================================================

    def GetBase(self, fLevel: int) -> int:
        """Return A5 for globals/common, A6 for the current frame, or walk static links 8(A6) to lexical level fLevel."""
        if fLevel <= 1:
            return A5
        if fLevel == self.ProcLvl:
            return A6
        A = self.GetReg(Alow, Ahigh)
        self.GenRR(i16(0x206E), A, 0)  # MOVE.L 8(A6),A
        self.Gen(8)
        for _ in range(fLevel, self.ProcLvl - 1):
            self.FreeReg(A)
            A2_reg = self.GetReg(Alow, Ahigh)
            self.GenRR(i16(0x2068), A2_reg, A)  # MOVE.L 8(A),A2
            self.Gen(8)
            A = A2_reg
        return A

    def GlobRef(self, fLinkName: str, fUserName: str, fRefLoc: int) -> None:
        """Record an external symbol reference at code byte offset fRefLoc in ProcList."""
        fLinkName = alfa8(fLinkName)
        fUserName = alfa8(fUserName)
        fRefLoc = i16(fRefLoc)
        lpRoc = self.ProcList
        Done = False
        while (not Done) and (lpRoc is not None):
            if lpRoc.LinkName == fLinkName:
                Done = True
            else:
                lpRoc = lpRoc.Next
        if not Done or lpRoc is None:
            lpRoc = ProcRef()
            lpRoc.RefList = None
            lpRoc.LinkName = fLinkName
            lpRoc.UserName = fUserName
            lpRoc.Next = self.ProcList
            self.ProcList = lpRoc
        lInt = IntList(fRefLoc, lpRoc.RefList)
        lpRoc.RefList = lInt

    def GenJump(self, fOp: int, fLab: int) -> None:
        """Emit a word-displacement branch fOp to internal label fLab, queuing forward references on LabelRec."""
        fOp = i16(fOp)
        fLab = i16(fLab)
        lpLab = self.LookUpILabel(fLab)
        if lpLab.Defined:
            self.GenWord(fOp, Flags.JMPL)
            self.GenWord(lpLab.Loc, Flags.ABSI)
        else:
            lInt = IntList(i16(self.Ic + 2), lpLab.RefList)
            lpLab.RefList = lInt
            self.GenWord(fOp, Flags.JMPL)
            self.GenWord(0, Flags.ABSI)

    def GenJSR(self, FName: str) -> None:
        """Emit a PC-relative (ShortCalls) or absolute-long JSR to external symbol FName and record its relocation."""
        fname = alfa8(FName)
        self.GlobRef(fname, fname, i16(self.Ic + 2))
        if self.ShortCalls:
            # JSR $+xxx
            self.Gen(i16(0x4EBA))
            self.Gen(0)
        else:
            # JSR xxx.L
            self.Gen(i16(0x4EB9))
            self.Gen(0)
            self.Gen(0)

    def LoadInt(self, fHi: int, fLo: int, fSize: int) -> int:
        """Load immediate constant (fHi:fLo) into a scratch data register using MOVEQ when in -128..127."""
        fHi = i16(fHi)
        fLo = i16(fLo)
        D = self.GetReg(Dlow, Dhigh)
        if fLo <= 127 and fLo >= 0 and fHi == 0:
            self.GenRR(i16(0x7000 + fLo), D, 0)  # MOVEQ #val,D
        elif fLo < 0 and fLo >= -128 and fHi == -1:
            self.GenRR(i16(0x7100 + fLo), D, 0)  # MOVEQ #val,D
        else:
            if fSize <= WordOp:
                Op = i16(0x303C)  # MOVE.W #,D
            else:
                Op = i16(0x203C)  # MOVE.L #,D
            self.GenRR(Op, D, 0)
            if fSize == LongOp:
                self.Gen(fHi)
            self.Gen(fLo)
        return D

    def FixIndxOffset(self, fCAttr: CAttr) -> None:
        """Fold an out-of-range INDX displacement (outside -128..127) into a fresh base register via LEA."""
        fCAttr.InOffset = i16(fCAttr.InOffset)
        if fCAttr.InOffset > 127 or fCAttr.InOffset < -128:
            self.FreeReg(fCAttr.InxAReg)
            A = self.GetReg(Alow, Ahigh)
            self.GenRR(i16(0x41E8), A, fCAttr.InxAReg)  # LEA off(XA),A
            self.Gen(fCAttr.InOffset)
            fCAttr.InOffset = 0
            fCAttr.InxAReg = A
        if fCAttr.InOffset < 0:
            fCAttr.InOffset = i16(fCAttr.InOffset + 256)

    def GenEffAddr(
        self,
        fOp: int,
        fCAttr: CAttr,
        fSize: int,
        iMMFlag: bool,
        iMMHi: int,
        iMMLo: int,
    ) -> None:
        """Emit instruction fOp encoded with the MC68000 effective address of fCAttr, freeing scratch registers."""
        fCAttr = fCAttr.copy()
        fOp = i16(fOp)
        iMMHi = i16(iMMHi)
        iMMLo = i16(iMMLo)

        def GenIMM() -> None:
            if iMMFlag:
                if fSize == LongOp:
                    self.Gen(iMMHi)
                self.Gen(iMMLo)

        ck = fCAttr.cKind
        if ck == CAttrKind.EXPR:
            if fCAttr.ExReg >= A0:
                fOp = i16(fOp + 8)
            self.GenR(fOp, fCAttr.ExReg)
            self.FreeReg(fCAttr.ExReg)
            GenIMM()
        elif ck == CAttrKind.ADDR:
            if i16(fCAttr.AOffset) == 0:
                self.GenR(i16(fOp + 16), fCAttr.AdReg)
                GenIMM()
            else:
                self.GenR(i16(fOp + 40), fCAttr.AdReg)
                GenIMM()
                self.Gen(i16(fCAttr.AOffset))
            self.FreeReg(fCAttr.AdReg)
        elif ck == CAttrKind.INDX:
            self.FixIndxOffset(fCAttr)
            self.GenR(i16(fOp + 48), fCAttr.InxAReg)
            GenIMM()
            Op = i16(fCAttr.InxRReg * 4096 + fCAttr.InOffset)
            if fCAttr.LongIndex:
                Op = i16(Op + 2048)
            self.Gen(Op)
            self.FreeReg(fCAttr.InxAReg)
            self.FreeReg(fCAttr.InxRReg)
        elif ck == CAttrKind.VARB:
            Base = self.GetBase(fCAttr.VLev)
            self.FreeReg(Base)
            self.GenR(i16(fOp + 40), Base)
            GenIMM()
            self.Gen(i16(fCAttr.VOffset))
            if fCAttr.VLev < 0:
                self.ComVRef(-fCAttr.VLev, i16(self.Ic - 2))
        elif ck == CAttrKind.CNST:
            cst_kind = fCAttr.CValu.CstKind
            if cst_kind == ConstKind.SCALCNST:
                self.Gen(i16(fOp + 60))
                GenIMM()
                if fSize == LongOp:
                    self.Gen(i16(fCAttr.CValu.IValu[0]))
                self.Gen(i16(fCAttr.CValu.IValu[1]))
            elif cst_kind in (ConstKind.STRCNST, ConstKind.PAOCCNST, ConstKind.SETCNST):
                self.Gen(i16(fOp + 58))
                self.Gen(0)
                lBigCRef = BigCRef()
                lBigCRef.Loc = i16(self.Ic - 2)
                lBigCRef.BigVal = fCAttr.CValu.copy()
                lBigCRef.StartLoc = -1
                lBigCRef.Next = self.BigCList
                self.BigCList = lBigCRef
        elif ck == CAttrKind.COND:
            self.CodError(2003)
        elif ck == CAttrKind.STCK:
            # i.e. (SP)+ not -(SP)
            self.Gen(i16(fOp + 31))
            GenIMM()
        elif ck == CAttrKind.BOOL:
            self.CodError(2004)
        elif ck == CAttrKind.BITZ:
            self.CodError(2005)

    def IncOffset(self, fCAttr: CAttr, fOffset: int) -> None:
        """Add byte displacement fOffset to an ADDR, INDX, or VARB operand descriptor."""
        fOffset = i16(fOffset)
        if fOffset != 0:
            if fCAttr.cKind == CAttrKind.ADDR:
                fCAttr.AOffset = i16(fCAttr.AOffset + fOffset)
            elif fCAttr.cKind == CAttrKind.INDX:
                fCAttr.InOffset = i16(fCAttr.InOffset + fOffset)
            elif fCAttr.cKind == CAttrKind.VARB:
                fCAttr.VOffset = i16(fCAttr.VOffset + fOffset)

    def MakeSetConst(self, fCAttr: CAttr) -> None:
        """Convert a small (<= 4-byte) SETCNST descriptor in place into an immediate SCALCNST."""
        lpInt = fCAttr.CValu.SetValu
        lCAttr = CAttr(CAttrKind.CNST)
        lCAttr.CValu.CstKind = ConstKind.SCALCNST
        if lpInt is not None:
            lCAttr.CValu.IValu[0] = i16(lpInt.Int)
            lCAttr.CValu.IValu[1] = lCAttr.CValu.IValu[0]
            lpInt = lpInt.Next
        else:
            lCAttr.CValu.IValu[1] = 0
        if lpInt is not None:
            lCAttr.CValu.IValu[1] = i16(lpInt.Int)
        else:
            lCAttr.CValu.IValu[0] = 0
        fCAttr.set_from(lCAttr)

    def PushAddress(self, fCAttr: CAttr) -> None:
        """Push the 32-bit effective address of fCAttr onto the stack via MOVE.L An,-(SP) or PEA."""
        fCAttr = fCAttr.copy()
        DoIt = True
        if fCAttr.cKind == CAttrKind.ADDR:
            if i16(fCAttr.AOffset) == 0:
                self.GenR(i16(0x2F08), fCAttr.AdReg)  # MOVE.L adreg,-(SP)
                DoIt = False
                self.FreeReg(fCAttr.AdReg)
        if DoIt:
            self.GenEffAddr(i16(0x4840), fCAttr, LongOp, False, 0, 0)  # PEA

    def ALoadAddress(self, fCAttr: CAttr, Areg: int) -> None:
        """Load the effective address of fCAttr directly into target address register Areg via LEA."""
        fCAttr = fCAttr.copy()
        self.GenEffAddr(i16(0x41C0 + (Areg - 8) * 512), fCAttr, LongOp, False, 0, 0)  # LEA

    def LoadAddress(self, fCAttr: CAttr) -> int:
        """Load the effective address of fCAttr into an address register, using ADDQ/SUBQ for small offsets."""
        fCAttr = fCAttr.copy()
        DoIt = True
        A = 0
        if fCAttr.cKind == CAttrKind.ADDR:
            aoff = i16(fCAttr.AOffset)
            if aoff <= 8 and aoff >= -8:
                DoIt = False
                A = fCAttr.AdReg
                if aoff != 0:
                    if aoff > 0:
                        A = self.CheckClobber(A)
                        self.GenRR(i16(0x5088), aoff, A)  # ADDQ.L #aoff,A
                    else:
                        A = self.CheckClobber(A)
                        self.GenRR(i16(0x5188), -aoff, A)  # SUBQ.L #-aof,A
        if DoIt:
            A = self.ReuseIfPossible(fCAttr, Alow, Ahigh)
            self.GenEffAddr(i16(0x41C0 + (A - 8) * 512), fCAttr, LongOp, False, 0, 0)  # LEA
        return A

    def PushInt(self, fValue: int, fSize: int) -> None:
        """Push signed 16-bit integer fValue onto the stack as a byte, word, or sign-extended longword."""
        fValue = i16(fValue)
        if fValue == 0:
            if fSize <= WordOp:
                self.Gen(i16(0x4267))  # CLR.W -(SP)
            else:
                self.Gen(i16(0x42A7))  # CLR.L -(SP)
        else:
            if fSize == ByteOp:
                self.Gen(i16(0x1F3C))  # MOVE.B #xxx,-(SP)
            elif fSize <= WordOp:
                self.Gen(i16(0x3F3C))  # MOVE.W #xxx,-(SP)
            else:
                self.Gen(i16(0x2F3C))  # MOVE.L #xxx,-(SP)
            if fSize == LongOp:
                if fValue < 0:
                    self.Gen(-1)
                else:
                    self.Gen(0)
            self.Gen(fValue)

    def LoadCC(self, fCAttr: CAttr) -> None:
        """Materialize a COND descriptor into a scratch data register via Scc and mark fCAttr as BOOL."""
        D = self.GetReg(Dlow, Dhigh)
        cc_op = {
            GCondition.LT: 13,
            GCondition.LE: 15,
            GCondition.GT: 14,
            GCondition.GE: 12,
            GCondition.EQ: 7,
            GCondition.NE: 6,
            GCondition.HI: 2,
            GCondition.LS: 3,
        }[fCAttr.CC]
        self.GenR(i16(0x50C0 + cc_op * 256), D)  # SCC D
        fCAttr.cKind = CAttrKind.BOOL
        fCAttr.ExReg = D

    def WriteAttr(self, fAttr: CAttr) -> None:
        """Print a human-readable trace of operand descriptor fAttr to stdout for debugging."""
        fAttr = fAttr.copy()
        ck = fAttr.cKind
        if ck == CAttrKind.EXPR:
            sys.stdout.write(f'EXPR {fAttr.ExReg}\n')
        elif ck == CAttrKind.BOOL:
            sys.stdout.write(f'BOOL {fAttr.ExReg}\n')
        elif ck == CAttrKind.BITZ:
            sys.stdout.write(f'BITZ {fAttr.ExReg}\n')
        elif ck == CAttrKind.ADDR:
            sys.stdout.write(f'ADDR {fAttr.AdReg:4d}{fAttr.AOffset:8d}\n')
        elif ck == CAttrKind.VARB:
            sys.stdout.write(f'VARB {fAttr.VOffset:8d}{fAttr.VLev:8d}\n')
        elif ck == CAttrKind.INDX:
            sys.stdout.write(f'INDX {fAttr.InxAReg:4d}{fAttr.InxRReg:4d}{fAttr.InOffset:8d}\n')
        elif ck == CAttrKind.CNST:
            sys.stdout.write('CNST \n')
        elif ck == CAttrKind.COND:
            sys.stdout.write(f'COND {int(fAttr.CC):4d}\n')

    def LoadAOrd(self, IntoReg: int, fCAttr: CAttr, fSize: int) -> None:
        """Load ordinal/pointer value fCAttr of size fSize into specific data or address register IntoReg."""
        if fCAttr.cKind == CAttrKind.CNST:
            if fCAttr.CValu.CstKind == ConstKind.SETCNST:
                self.MakeSetConst(fCAttr)
        else:
            DoIt = False
            D = 0
            if fCAttr.cKind == CAttrKind.COND:
                self.LoadCC(fCAttr)
            if fCAttr.cKind == CAttrKind.BOOL:
                D = fCAttr.ExReg
                DoIt = True
                if self.build30:
                    if D != IntoReg:
                        D = self.CheckClobber(D)
                else:
                    D = self.CheckClobber(D)
                if fSize == ByteOp:
                    self.GenR(i16(0x4400), D)  # NEG.B D
                else:
                    self.GenR(i16(0x0240), D)  # ANDI.W #1,D
                    self.Gen(1)
            elif fCAttr.cKind == CAttrKind.BITZ:
                D = fCAttr.ExReg  # fix: in the original source this was after CheckClobber(D), when D was not yet set
                if self.build30:
                    if D != IntoReg:
                        D = self.CheckClobber(D)
                else:
                    D = self.CheckClobber(D)
                DoIt = True
                self.GenR(i16(0x0240), D)  # ANDI.W #1,D
                self.Gen(1)
            if DoIt:
                if fSize == LongOp:
                    self.GenR(i16(0x48C0), D)  # EXT.L d
                fCAttr.cKind = CAttrKind.EXPR
        if fCAttr.cKind == CAttrKind.EXPR:
            if fCAttr.ExReg == IntoReg:
                return
        Op = 0
        if fSize == ByteOp:
            Op = i16(0x1000)
        elif fSize == WordOp:
            Op = i16(0x3000)
        elif fSize == LongOp:
            Op = i16(0x2000)
        D = IntoReg
        if IntoReg <= D7:
            DestPart = D * 512
        else:
            DestPart = (D - 8) * 512 + 64  # MOVEA
        self.GenEffAddr(i16(Op + DestPart), fCAttr, fSize, False, 0, 0)
        fCAttr.cKind = CAttrKind.EXPR
        fCAttr.ExReg = D

    def LoadD(self, fCAttr: CAttr, fSize: int, SetCC: bool) -> int:
        """Load operand fCAttr of size fSize into a D register, ensuring condition codes are set when SetCC is True."""
        DoIt = True
        D = 0
        if fCAttr.cKind == CAttrKind.EXPR:
            if ((fCAttr.ExReg <= Dhigh) or (not SetCC)) and (fCAttr.ExReg <= D7):
                D = fCAttr.ExReg
                DoIt = False
        elif fCAttr.cKind == CAttrKind.CNST:
            if fCAttr.CValu.CstKind == ConstKind.SETCNST:
                self.MakeSetConst(fCAttr)
            D = self.LoadInt(fCAttr.CValu.IValu[0], fCAttr.CValu.IValu[1], fSize)
            DoIt = False
        else:
            if fCAttr.cKind == CAttrKind.COND:
                self.LoadCC(fCAttr)
            if fCAttr.cKind == CAttrKind.BOOL:
                D = fCAttr.ExReg
                DoIt = False
                D = self.CheckClobber(D)
                if fSize == ByteOp:
                    self.GenR(i16(0x4400), D)  # NEG.B D
                else:
                    self.GenR(i16(0x0240), D)  # ANDI.W #1,D
                    self.Gen(1)
            elif fCAttr.cKind == CAttrKind.BITZ:
                D = fCAttr.ExReg  # fix: in the original source this was after CheckClobber(D), when D was not yet set
                D = self.CheckClobber(D)
                DoIt = False
                self.GenR(i16(0x0240), D)  # ANDI.W #1,D
                self.Gen(1)
            if not DoIt:
                if fSize == LongOp:
                    self.GenR(i16(0x48C0), D)  # EXT.L d
        if DoIt:
            Op = 0
            if fSize == ByteOp:
                Op = i16(0x1000)
            elif fSize == WordOp:
                Op = i16(0x3000)
            elif fSize == LongOp:
                Op = i16(0x2000)
            D = self.GetReg(Dlow, Dhigh)
            self.GenEffAddr(i16(Op + D * 512), fCAttr, fSize, False, 0, 0)
        fCAttr.cKind = CAttrKind.EXPR
        fCAttr.ExReg = D
        return D

    def LoaddWithPrefReg(self, PrefReg: int, fCAttr: CAttr, fSize: int) -> int:
        """Load fCAttr into PrefReg if specified (!= -1) or a scratch D register, copying if non-target reg would be clobbered."""
        if PrefReg != -1:
            self.LoadAOrd(PrefReg, fCAttr, fSize)
            D = fCAttr.ExReg
        else:
            D = self.LoadD(fCAttr, fSize, False)
        if D != PrefReg:
            D = self.CheckClobber(D)
            fCAttr.ExReg = D
        return D

    def IsQuickCnst(self, CValu: Valu) -> bool:
        """Return True if CValu is a non-zero scalar constant in the signed 8-bit MOVEQ range (-128..127)."""
        if CValu.CstKind != ConstKind.SCALCNST:
            return False
        iv0 = i16(CValu.IValu[0])
        iv1 = i16(CValu.IValu[1])
        return (iv1 <= 127 and iv1 > 0 and iv0 == 0) or (
            iv1 < 0 and iv1 >= -128 and iv0 == -1
        )

    def PushValue(self, fCAttr: CAttr, fSize: int) -> None:
        """Push the value of fCAttr (byte, word, longword, or 8-byte Quad) onto the hardware stack."""
        fCAttr = fCAttr.copy()
        if fCAttr.cKind != CAttrKind.STCK:
            if fSize < Quad:
                DoIt = True
                if fCAttr.cKind == CAttrKind.CNST:
                    QuickCnst = self.IsQuickCnst(fCAttr.CValu)
                    if fSize == LongOp and QuickCnst:
                        CnstD = self.LoadInt(
                            fCAttr.CValu.IValu[0], fCAttr.CValu.IValu[1], fSize
                        )
                        fCAttr.cKind = CAttrKind.EXPR
                        fCAttr.ExReg = CnstD
                        self.PushValue(fCAttr, LongOp)
                        DoIt = False
                    else:
                        if fCAttr.CValu.CstKind == ConstKind.SCALCNST:
                            if (
                                i16(fCAttr.CValu.IValu[0]) == 0
                                and i16(fCAttr.CValu.IValu[1]) == 0
                            ):
                                self.PushInt(0, fSize)
                                DoIt = False
                elif fCAttr.cKind in (CAttrKind.BOOL, CAttrKind.COND, CAttrKind.BITZ):
                    self.LoadD(fCAttr, fSize, False)
                if DoIt:
                    if fSize == ByteOp:
                        Op = i16(0x1F00)  # MOVE.B ?,-(SP)
                    elif fSize <= WordOp:
                        Op = i16(0x3F00)  # MOVE.W ?,-(SP)
                    else:
                        Op = i16(0x2F00)  # MOVE.L ?,-(SP)
                    self.GenEffAddr(Op, fCAttr, fSize, False, 0, 0)
            else:
                # QUAD
                self.IncOffset(fCAttr, 8)
                A = self.LoadAddress(fCAttr)
                A = self.CheckClobber(A)
                self.GenR(i16(0x2F20), A)  # MOVE.L -(A),-(SP)
                self.GenR(i16(0x2F20), A)  # MOVE.L -(A),-(SP)
                self.FreeReg(A)

    def Store(self, From_CAttr: CAttr, To_CAttr: CAttr, fSize: int) -> None:
        """Emit MOVE, MOVEQ, CLR, or SUBA.L An,An to store From_CAttr into To_CAttr at size fSize."""
        From_CAttr = From_CAttr.copy()
        To_CAttr = To_CAttr.copy()
        Op = 0
        if fSize == ByteOp:
            Op = i16(0x1000)  # MOVE.B
        elif fSize == WordOp:
            Op = i16(0x3000)  # MOVE.W
        elif fSize == LongOp:
            Op = i16(0x2000)  # MOVE.L

        InstSize = 0
        FreeXreg = False
        QuickCnst = False
        MoveQuick = False
        ClearFlag = False
        DstComFlag = False
        CommonFlag = False
        DstComLev = 0
        CommonLev = 0
        DestMode = 0
        DestReg = 0
        Inst = [0, 0, 0, 0]

        fck = From_CAttr.cKind
        if fck == CAttrKind.EXPR:
            Op = i16(Op + From_CAttr.ExReg)
        elif fck == CAttrKind.ADDR:
            if i16(From_CAttr.AOffset) == 0:
                Op = i16(Op + 8 + From_CAttr.AdReg)
            else:
                Op = i16(Op + 32 + From_CAttr.AdReg)
                InstSize = 1
                Inst[1] = i16(From_CAttr.AOffset)
        elif fck == CAttrKind.CNST:
            if (
                i16(From_CAttr.CValu.IValu[0]) == 0
                and i16(From_CAttr.CValu.IValu[1]) == 0
            ):
                ClearFlag = True
                if fSize == ByteOp:
                    Op = i16(0x4200)  # CLR.B
                elif fSize == WordOp:
                    Op = i16(0x4240)  # CLR.W
                elif fSize == LongOp:
                    Op = i16(0x4280)  # CLR.L
            else:
                QuickCnst = self.IsQuickCnst(From_CAttr.CValu)
                Op = i16(Op + 60)
                if fSize <= 2:
                    Inst[1] = i16(From_CAttr.CValu.IValu[1])
                    InstSize = 1
                else:
                    Inst[1] = i16(From_CAttr.CValu.IValu[0])
                    Inst[2] = i16(From_CAttr.CValu.IValu[1])
                    InstSize = 2
        elif fck == CAttrKind.INDX:
            self.FixIndxOffset(From_CAttr)
            Op = i16(Op + 40 + From_CAttr.InxAReg)
            InstSize = 1
            Inst[1] = i16(From_CAttr.InxRReg * 4096 + From_CAttr.InOffset)
            if From_CAttr.LongIndex:
                Inst[1] = i16(Inst[1] + 2048)
        elif fck == CAttrKind.VARB:
            Base = self.GetBase(From_CAttr.VLev)
            Op = i16(Op + 32 + Base)
            if From_CAttr.VLev < 0:
                CommonFlag = True
                CommonLev = -From_CAttr.VLev
            InstSize = 1
            Inst[1] = i16(From_CAttr.VOffset)
            From_CAttr.cKind = CAttrKind.ADDR
            From_CAttr.AdReg = Base  # So will free base
        elif fck in (CAttrKind.BOOL, CAttrKind.COND, CAttrKind.BITZ):
            D = self.LoadD(From_CAttr, fSize, False)
            Op = i16(Op + D)
            From_CAttr.cKind = CAttrKind.EXPR
            From_CAttr.ExReg = D  # So will free d
        elif fck == CAttrKind.STCK:
            Op = i16(Op + 31)

        tck = To_CAttr.cKind
        if tck == CAttrKind.EXPR:
            if To_CAttr.ExReg <= D7:
                DestMode = 0  # D direct
                DestReg = To_CAttr.ExReg
                MoveQuick = QuickCnst
            else:
                DestMode = 1  # A direct
                DestReg = To_CAttr.ExReg - 8
            self.FreeReg(To_CAttr.ExReg)
        elif tck == CAttrKind.ADDR:
            if i16(To_CAttr.AOffset) == 0:
                DestMode = 2
            else:
                DestMode = 5
                InstSize = InstSize + 1
                Inst[InstSize] = i16(To_CAttr.AOffset)
            DestReg = To_CAttr.AdReg - 8
            self.FreeReg(To_CAttr.AdReg)
        elif tck == CAttrKind.INDX:
            self.FixIndxOffset(To_CAttr)
            DestMode = 6
            DestReg = To_CAttr.InxAReg - 8
            InstSize = InstSize + 1
            Inst[InstSize] = i16(To_CAttr.InOffset + To_CAttr.InxRReg * 4096)
            if To_CAttr.LongIndex:
                Inst[InstSize] = i16(Inst[InstSize] + 2048)
            FreeXreg = True
            self.FreeReg(To_CAttr.InxAReg)
        elif tck == CAttrKind.VARB:
            Base = self.GetBase(To_CAttr.VLev)
            self.FreeReg(Base)
            if To_CAttr.VLev < 0:
                DstComFlag = True
                DstComLev = -To_CAttr.VLev
            DestMode = 5
            DestReg = Base - 8
            InstSize = InstSize + 1
            Inst[InstSize] = i16(To_CAttr.VOffset)
        elif tck == CAttrKind.STCK:
            DestMode = 4
            DestReg = 7

        if CommonFlag:
            self.ComVRef(CommonLev, i16(self.Ic + 2))
        if MoveQuick:
            # MOVEQ #val,D
            if i16(From_CAttr.CValu.IValu[0]) == 0:
                self.GenRR(i16(0x7000 + i16(From_CAttr.CValu.IValu[1])), DestReg, 0)
            else:
                self.GenRR(i16(0x7100 + i16(From_CAttr.CValu.IValu[1])), DestReg, 0)
        else:
            if fSize == LongOp and QuickCnst:
                if DstComFlag:
                    self.ComVRef(DstComLev, i16(self.Ic + InstSize * 2 - 2))
                CnstD = self.LoadInt(
                    From_CAttr.CValu.IValu[0], From_CAttr.CValu.IValu[1], fSize
                )
                self.GenRR(i16(0x2000 + CnstD + DestMode * 64), DestReg, 0)  # MOVE.L D,<ea>
                for i in range(3, InstSize + 1):
                    self.Gen(Inst[i])
                self.FreeReg(CnstD)
            else:
                if DstComFlag:
                    self.ComVRef(DstComLev, i16(self.Ic + InstSize * 2))
                if ClearFlag:
                    if DestMode == 1:  # Ai
                        self.GenRR(i16(0x91C8), DestReg, DestReg)  # SUBA.L Ai,Ai
                    else:
                        self.GenR(i16(Op + DestMode * 8), DestReg)
                else:
                    self.GenRR(i16(Op + DestMode * 64), DestReg, 0)
                for i in range(1, InstSize + 1):
                    self.Gen(Inst[i])

        if From_CAttr.cKind == CAttrKind.EXPR:
            self.FreeReg(From_CAttr.ExReg)
        elif From_CAttr.cKind == CAttrKind.ADDR:
            self.FreeReg(From_CAttr.AdReg)
        elif From_CAttr.cKind == CAttrKind.INDX:
            self.FreeReg(From_CAttr.InxAReg)
            self.FreeReg(From_CAttr.InxRReg)

        if FreeXreg:
            self.FreeReg(To_CAttr.InxRReg)

    def GenCompare(self, aCAttr: CAttr, bCAttr: CAttr, fSize: int) -> bool:
        """Emit TST, CMPI, CMP, or CMPA to compare aCAttr and bCAttr, returning True if operand order was reversed."""
        aCAttr = aCAttr.copy()
        bCAttr = bCAttr.copy()
        FreeExtra = False
        IsNotA = True
        result = False
        iMMFlag = False
        FreeFlag = False
        D = 0
        DExtra = 0
        iMMValLo = 0
        iMMValHi = 0
        lOp = 0
        lCAttr = CAttr()

        def DoCMPA(ANAttr: CAttr) -> None:
            nonlocal FreeFlag, D, IsNotA, lOp
            FreeFlag = True
            D = ANAttr.ExReg
            IsNotA = False
            if fSize == WordOp:
                lOp = i16(0xB0C0)
            else:
                lOp = i16(0xB1C0)
            lOp = i16(lOp + (D - 8) * 512)  # CMPA.? <ea>,A

        def DoMOVEAD(ANAttr: CAttr) -> None:
            nonlocal FreeFlag, FreeExtra, D, DExtra, IsNotA, lOp
            FreeFlag = True
            FreeExtra = True
            D = ANAttr.ExReg
            DExtra = self.GetReg(Dlow, Dhigh)
            IsNotA = False
            if fSize == WordOp:
                lOp = i16(0x3000)
            else:
                lOp = i16(0x2000)
            lOp = i16(lOp + DExtra * 512)  # MOVE.? A,D

        if aCAttr.cKind == CAttrKind.COND:
            D = self.LoadD(aCAttr, fSize, False)
        if bCAttr.cKind == CAttrKind.COND:
            D = self.LoadD(bCAttr, fSize, False)
        if aCAttr.cKind in (CAttrKind.BOOL, CAttrKind.BITZ):
            D = self.LoadD(aCAttr, fSize, False)
        if bCAttr.cKind in (CAttrKind.BOOL, CAttrKind.BITZ):
            D = self.LoadD(bCAttr, fSize, False)

        if aCAttr.cKind == CAttrKind.CNST:
            lCAttr = bCAttr.copy()
            result = True
            if lCAttr.cKind == CAttrKind.CNST:
                D = self.LoadD(lCAttr, fSize, False)
            if i16(aCAttr.CValu.IValu[0]) == 0 and i16(aCAttr.CValu.IValu[1]) == 0:
                if lCAttr.cKind == CAttrKind.EXPR and lCAttr.ExReg >= A0:
                    DoMOVEAD(lCAttr.copy())
                else:
                    lOp = i16(0x4A00)  # TST
            else:
                if lCAttr.cKind == CAttrKind.EXPR and lCAttr.ExReg >= A0:
                    DoCMPA(lCAttr.copy())
                    lCAttr = aCAttr.copy()
                else:
                    lOp = i16(0x0C00)  # CMPI
                    iMMFlag = True
                    iMMValHi = i16(aCAttr.CValu.IValu[0])
                    iMMValLo = i16(aCAttr.CValu.IValu[1])
        elif bCAttr.cKind == CAttrKind.CNST:
            lCAttr = aCAttr.copy()
            if i16(bCAttr.CValu.IValu[0]) == 0 and i16(bCAttr.CValu.IValu[1]) == 0:
                if lCAttr.cKind == CAttrKind.EXPR and lCAttr.ExReg >= A0:
                    DoMOVEAD(lCAttr.copy())
                else:
                    lOp = i16(0x4A00)  # TST
            else:
                if lCAttr.cKind == CAttrKind.EXPR and lCAttr.ExReg >= A0:
                    DoCMPA(lCAttr.copy())
                    lCAttr = bCAttr.copy()
                else:
                    lOp = i16(0x0C00)  # CMPI
                    iMMFlag = True
                    iMMValHi = i16(bCAttr.CValu.IValu[0])
                    iMMValLo = i16(bCAttr.CValu.IValu[1])
        else:
            if bCAttr.cKind == CAttrKind.STCK and aCAttr.cKind == CAttrKind.STCK:
                D = self.LoadD(bCAttr, fSize, False)
            if bCAttr.cKind == CAttrKind.EXPR:
                lCAttr = aCAttr.copy()
                result = True
                if bCAttr.cKind == CAttrKind.EXPR and bCAttr.ExReg >= A0:
                    DoCMPA(bCAttr.copy())
                else:
                    D = self.LoadD(bCAttr, fSize, False)
            else:
                if aCAttr.cKind == CAttrKind.EXPR and aCAttr.ExReg >= A0:
                    DoCMPA(aCAttr.copy())
                else:
                    D = self.LoadD(aCAttr, fSize, False)
                lCAttr = bCAttr.copy()
            if IsNotA:
                lOp = i16(-20480 + D * 512)  # CMP.? <ea>,D ($B000)
            FreeFlag = True

        if IsNotA:
            if fSize == WordOp:
                lOp = i16(lOp + 64)
            elif fSize == LongOp:
                lOp = i16(lOp + 128)
        self.GenEffAddr(lOp, lCAttr, fSize, iMMFlag, iMMValHi, iMMValLo)
        if FreeFlag:
            self.FreeReg(D)
        if FreeExtra:
            self.FreeReg(DExtra)
        return result

    def PushSet(self, fCAttr: CAttr, fBytes: int, PushSize: bool) -> None:
        """Push an fBytes-byte set onto the stack (inline MOVE for <= 4 bytes, loop for larger), optionally followed by its word-aligned byte size."""
        fCAttr = fCAttr.copy()
        fBytes = i16(fBytes)
        if fBytes <= 4:
            if fCAttr.cKind == CAttrKind.CNST:
                fCAttr.CValu.FrontAddress = True
            elif fBytes == 1:
                D = self.GetReg(Dlow, Dhigh)
                self.GenR(i16(0x4240), D)  # CLR.W D
                self.GenEffAddr(i16(0x1000 + D * 512), fCAttr, ByteOp, False, 0, 0)  # MOVE.B ?,D
                fCAttr.cKind = CAttrKind.EXPR
                fCAttr.ExReg = D
            if fBytes <= 2:
                # MOVE.W ?,-(SP)
                lOp = i16(0x3F00)
                lSize = WordOp
            else:
                # MOVE.L ?,-(SP)
                lOp = i16(0x2F00)
                lSize = LongOp
            self.GenEffAddr(lOp, fCAttr, lSize, False, 0, 0)
        else:
            if fCAttr.cKind != CAttrKind.CNST:
                self.IncOffset(fCAttr, fBytes)
            A = self.LoadAddress(fCAttr)
            D = self.LoadInt(0, pdiv(fBytes, 2), WordOp)
            A = self.CheckClobber(A)
            self.GenR(i16(0x3F20), A)  # MOVE.W -(A),-(SP)
            self.GenR(i16(0x5340), D)  # SUBQ.W #1,D
            self.Gen(i16(0x6EFA))      # BGT.S $-6
            self.FreeReg(A)
            self.FreeReg(D)
        if odd(fBytes):
            fBytes = i16(fBytes + 1)
        if PushSize:
            self.PushInt(fBytes, WordOp)

    def SetExpression(self, fOp: int) -> bool:
        """Evaluate a set I-code expression fOp into gCAttr or onto the stack, returning True if left on the stack."""
        FOnStack = False
        if fOp in (
            1,   # GLOBAL
            2,   # LOCAL
            3,   # INTER
            4,   # COMMON
            5,   # REGISTER
            12,  # UPARROW
            15,  # FIELD
            16,  # INDX1
            17,  # INDX2
            18,  # INDX4
            19,  # INDX8
            20,  # INDXBIG
            21,  # INDXPCK
            22,  # ADDRESS
            43,  # WITHREC
        ):
            self.Expression(fOp, -1, False)
        elif fOp == 30:  # SETCNST
            SetSize = self.NextByte()
            lInt: Optional[IntList] = None
            for i in range(1, SetSize + 1):
                if odd(i):
                    NewInt = IntList(self.NextByte(), lInt)
                    lInt = NewInt
                else:
                    assert lInt is not None
                    lInt.Int = i16(lInt.Int + self.NextByte() * 256)
            self.gCAttr.cKind = CAttrKind.CNST
            self.gCAttr.CValu = Valu()
            self.gCAttr.CValu.CstKind = ConstKind.SETCNST
            self.gCAttr.CValu.SetBytes = SetSize
            self.gCAttr.CValu.SetValu = lInt
            self.gCAttr.CValu.FrontAddress = False
        elif fOp == 31:  # NULLSET
            self.gCAttr.cKind = CAttrKind.CNST
            self.gCAttr.CValu = Valu()
            self.gCAttr.CValu.CstKind = ConstKind.SETCNST
            lInt = IntList(0, None)
            self.gCAttr.CValu.SetBytes = 1
            self.gCAttr.CValu.SetValu = lInt
            self.gCAttr.CValu.FrontAddress = False
        elif fOp in (160, 161, 162):  # UNION, DIFF, INTER
            SetSize = self.NextByte()
            LeftStack = self.SetExpression(self.NextByte())
            lCAttr = self.gCAttr.copy()
            RightStack = self.SetExpression(self.NextByte())
            FOnStack = LeftStack or RightStack or (SetSize > 4)
            if FOnStack:
                if not LeftStack:
                    self.PushSet(lCAttr, SetSize, True)
                if not RightStack:
                    self.PushSet(self.gCAttr, SetSize, True)
                if fOp == 160:
                    self.GenJSR('%_UNION ')
                elif fOp == 161:
                    if RightStack and (not LeftStack):
                        self.GenJSR('%_RDIFF ')
                    else:
                        self.GenJSR('%_DIFF  ')
                elif fOp == 162:
                    self.GenJSR('%_INTER ')
            else:
                if fOp == 160:
                    lOp = i16(-32767 - 1)  # OR ($8000)
                else:
                    lOp = i16(0xC000)      # AND
                if SetSize == 1:
                    lOpSize = 0
                    lSize = ByteOp
                elif SetSize == 2:
                    lOpSize = 64
                    lSize = WordOp
                else:
                    lOpSize = 128
                    lSize = LongOp
                lOp = i16(lOp + lOpSize)
                if fOp == 161:
                    D = self.LoadD(self.gCAttr, lSize, False)
                    D = self.CheckClobber(D)
                    self.gCAttr.ExReg = D
                    self.GenR(i16(0x4600 + lOpSize), D)  # NOT d
                if lCAttr.cKind == CAttrKind.EXPR:
                    D = lCAttr.ExReg
                    lCAttr = self.gCAttr.copy()
                else:
                    D = self.LoadD(self.gCAttr, lSize, False)
                if lCAttr.cKind == CAttrKind.CNST:
                    lInt = lCAttr.CValu.SetValu
                    lCAttr.CValu.CstKind = ConstKind.SCALCNST
                    if lInt is not None:
                        lCAttr.CValu.IValu[1] = i16(lInt.Int)
                        lCAttr.CValu.IValu[0] = lCAttr.CValu.IValu[1]
                        lInt = lInt.Next
                    else:
                        lCAttr.CValu.IValu[1] = 0
                    if lInt is not None:
                        lCAttr.CValu.IValu[1] = i16(lInt.Int)
                    else:
                        lCAttr.CValu.IValu[0] = 0
                D = self.CheckClobber(D)
                self.GenEffAddr(i16(lOp + D * 512), lCAttr, lSize, False, 0, 0)
                self.gCAttr.cKind = CAttrKind.EXPR
                self.gCAttr.ExReg = D
        elif fOp == 168:  # SINGSET
            _SetSize = self.NextByte()
            self.Expression(self.NextByte(), -1, False)
            self.PushValue(self.gCAttr, WordOp)
            self.GenJSR('%_SING  ')
            FOnStack = True
        elif fOp == 169:  # SETRANGE
            _SetSize = self.NextByte()
            self.Expression(self.NextByte(), -1, False)
            self.PushValue(self.gCAttr, WordOp)
            self.Expression(self.NextByte(), -1, False)
            self.PushValue(self.gCAttr, WordOp)
            self.GenJSR('%_RANGE ')
            FOnStack = True
        elif fOp == 170:  # ADJSET
            FinalSize = self.NextByte()
            InitSize = self.NextByte()
            if FinalSize == 1:
                FinalSize = 2
            FOnStack = self.SetExpression(self.NextByte())
            if self.gCAttr.cKind == CAttrKind.CNST and (not FOnStack) and FinalSize != 0:
                InitWords = pdiv(InitSize + 1, 2)
                FinalWords = pdiv(FinalSize + 1, 2)
                if InitWords > FinalWords:
                    for _ in range(FinalWords + 1, InitWords + 1):
                        assert self.gCAttr.CValu.SetValu is not None
                        self.gCAttr.CValu.SetValu = self.gCAttr.CValu.SetValu.Next
                else:
                    for _ in range(InitWords + 1, FinalWords + 1):
                        lInt = IntList(0, self.gCAttr.CValu.SetValu)
                        self.gCAttr.CValu.SetValu = lInt
                self.gCAttr.CValu.SetBytes = FinalSize
            else:
                if not FOnStack:
                    self.PushSet(self.gCAttr, InitSize, True)
                if FinalSize != 0:
                    self.PushInt(FinalSize, WordOp)
                    self.GenJSR('%_ADJ   ')
                    self.PushInt(FinalSize, WordOp)
                FOnStack = True
        return FOnStack

    # ========================================================================
    # 3. Expression and sub-expression code generation
    # ========================================================================

    def Expression(self, fOp: int, PrefReg: int, TrapV: bool) -> None:
        """Evaluate expression I-code opcode fOp into self.gCAttr, honoring target PrefReg and overflow checking TrapV."""
        def Push4Call(FName: str) -> None:
            """Evaluate one 32-bit operand onto the stack, call runtime routine FName, and mark gCAttr as STCK."""
            self.Expression(self.NextByte(), -1, False)
            self.PushValue(self.gCAttr, LongOp)
            self.GenJSR(FName)
            self.gCAttr.cKind = CAttrKind.STCK

        def Push44Call(FName: str) -> None:
            """Evaluate two 32-bit operands onto the stack, call runtime routine FName, and mark gCAttr as STCK."""
            self.Expression(self.NextByte(), -1, False)
            self.PushValue(self.gCAttr, LongOp)
            self.Expression(self.NextByte(), -1, False)
            self.PushValue(self.gCAttr, LongOp)
            self.GenJSR(FName)
            self.gCAttr.cKind = CAttrKind.STCK

        def PushAACall(FName: str) -> None:
            """Push the effective addresses of two operands, call runtime routine FName, and mark gCAttr as STCK."""
            self.Expression(self.NextByte(), -1, False)
            self.PushAddress(self.gCAttr)
            self.Expression(self.NextByte(), -1, False)
            self.PushAddress(self.gCAttr)
            self.GenJSR(FName)
            self.gCAttr.cKind = CAttrKind.STCK

        def LongTRAPV(D: int) -> None:
            """Check a 32-bit value in register D for signed 16-bit overflow via DIVS #1,D; TRAPV; EXT.L D."""
            # detect 16-bit overflow. Use property of divide instruction
            self.GenRR(i16(0x81F8), D, 4)
            self.Gen(1)               # DIVS #1,d
            self.Gen(i16(0x4E76))     # TRAPV
            self.GenR(i16(0x48C0), D)  # EXT.L D

        def GenIndex(ElementSize: int) -> None:
            """Generate unpacked array indexing for elements of ElementSize bytes, folding constant subscripts."""
            ElementSize = i16(ElementSize)
            Lo = i16(self.NextWord())
            self.Expression(self.NextByte(), -1, False)
            lCAttr = self.gCAttr.copy()
            self.Expression(self.NextByte(), -1, False)
            if self.gCAttr.cKind == CAttrKind.CNST:
                self.IncOffset(
                    lCAttr,
                    i16(ElementSize * i16(i16(self.gCAttr.CValu.IValu[1]) - Lo)),
                )
            else:
                D = self.LoadD(self.gCAttr, WordOp, False)
                AddFlag = False
                if ElementSize != 1:
                    D = self.CheckClobber(D)
                if lCAttr.cKind == CAttrKind.ADDR:
                    A = lCAttr.AdReg
                    lOffset = i16(lCAttr.AOffset)
                    lCAttr.cKind = CAttrKind.INDX
                    lCAttr.InOffset = i16(lOffset - Lo * ElementSize)
                    lCAttr.InxAReg = A
                    lCAttr.InxRReg = D
                    lCAttr.LongIndex = False
                elif lCAttr.cKind == CAttrKind.INDX:
                    lCAttr.InOffset = i16(lCAttr.InOffset - Lo * ElementSize)
                    AddFlag = True
                elif lCAttr.cKind == CAttrKind.VARB:
                    lOffset = i16(lCAttr.VOffset)
                    lVLev = lCAttr.VLev
                    lCAttr.cKind = CAttrKind.INDX
                    lCAttr.InOffset = i16(lOffset - Lo * ElementSize)
                    lCAttr.InxRReg = D
                    if lVLev >= 0:
                        lCAttr.InxAReg = self.GetBase(lVLev)
                    else:
                        A = self.GetReg(Alow, Ahigh)
                        self.GenRR(i16(0x41ED), A, 0)
                        self.Gen(lCAttr.InOffset)  # LEA off(A5),A
                        self.ComVRef(-lVLev, i16(self.Ic - 2))
                        lCAttr.InxAReg = A
                        lCAttr.InOffset = 0
                    lCAttr.LongIndex = False
                if ElementSize > 1:
                    ok, ShiftCount = self.ShiftMult(ElementSize)
                    if ok:
                        self.GenRR(i16(0xE140), ShiftCount, D)  # ASL.W #xx,D
                    else:
                        # MULS
                        self.GenRR(i16(0xC1FC), D, 0)
                        self.Gen(ElementSize)
                if AddFlag:
                    lCAttr.InxRReg = self.CheckClobber(lCAttr.InxRReg)
                    self.GenRR(i16(0xD040), lCAttr.InxRReg, D)  # ADD.W D,INXRREG
                    self.FreeReg(D)
            self.gCAttr.set_from(lCAttr)

        def PckdIndex() -> None:
            """Extract a signed or unsigned element from a packed array (1, 2, 4, or 8 bits per element)."""
            BitsPerEl = self.NextByte()
            Lo = i16(self.NextWord())
            Signed = BitsPerEl > 127
            if Signed:
                BitsPerEl = BitsPerEl - 128
            self.Expression(self.NextByte(), -1, False)
            lCAttr = self.gCAttr.copy()
            self.Expression(self.NextByte(), -1, False)
            D3_reg = self.LoadD(self.gCAttr, WordOp, False)
            DataMask = 0
            D2_reg = 0
            if BitsPerEl == 8:
                self.IncOffset(lCAttr, i16(-Lo))
            else:
                if Lo != 0:
                    D3_reg = self.CheckClobber(D3_reg)
                    if abs(Lo) <= 8:
                        if Lo > 0:
                            self.GenRR(i16(0x5140), Lo, D3_reg)   # SUBQ.W #lo,D3
                        else:
                            self.GenRR(i16(0x5040), -Lo, D3_reg)  # ADDQ.W #-lo,D3
                    else:
                        self.GenRR(i16(0x907C), D3_reg, 0)
                        self.Gen(Lo)  # SUBI.W #lo,D3
                DataMask = 0
                AddrMask = 0
                lBitsPerEl = BitsPerEl
                AShiftCount = 0
                for _ in range(1, BitsPerEl + 1):
                    DataMask = i16(DataMask * 2 + 1)
                while lBitsPerEl < 8:
                    AShiftCount = AShiftCount + 1
                    lBitsPerEl = lBitsPerEl * 2
                    AddrMask = i16(AddrMask * 2 + 1)
                D2_reg = self.GetReg(Dlow, Dhigh)
                if BitsPerEl == 1:
                    D = D2_reg
                    D2_reg = D3_reg
                    D3_reg = D
                    self.GenRR(i16(0x3000), D3_reg, D2_reg)       # MOVE.W D2,D3
                    self.GenRR(i16(0xE040), AShiftCount, D3_reg)  # ASR.W #sc,D3
                else:
                    self.GenRR(i16(0x1000), D2_reg, D3_reg)       # MOVE.B D3,D2
                    self.GenR(i16(0x0240), D2_reg)
                    self.Gen(AddrMask)                            # ANDI.W #am,D2
                    D3_reg = self.CheckClobber(D3_reg)
                    self.GenRR(i16(0xE040), AShiftCount, D3_reg)  # ASR.W #sc,D3
                    if AShiftCount < 3:
                        self.GenRR(i16(0xE108), 3 - AShiftCount, D2_reg)  # LSL.B #3-sc,D2

            self.gCAttr.cKind = CAttrKind.INDX
            self.gCAttr.LongIndex = False
            if lCAttr.cKind == CAttrKind.ADDR:
                self.gCAttr.InOffset = i16(lCAttr.AOffset)
                self.gCAttr.InxAReg = lCAttr.AdReg
            elif lCAttr.cKind == CAttrKind.INDX:
                D3_reg = self.CheckClobber(D3_reg)
                self.gCAttr.set_from(lCAttr)
                self.FreeReg(lCAttr.InxRReg)
                self.GenRR(i16(0xD040), D3_reg, lCAttr.InxRReg)  # ADD.W
            elif lCAttr.cKind == CAttrKind.VARB:
                if lCAttr.VLev > 0:
                    self.gCAttr.InOffset = i16(lCAttr.VOffset)
                    self.gCAttr.InxAReg = self.GetBase(lCAttr.VLev)
                else:
                    self.gCAttr.InOffset = 0
                    self.gCAttr.InxAReg = self.LoadAddress(lCAttr)
            self.gCAttr.InxRReg = D3_reg

            if BitsPerEl == 1:
                # optimize the packed array of boolean
                self.GenEffAddr(
                    i16(0x0100 + D2_reg * 512), self.gCAttr, LongOp, False, 0, 0
                )  # BTST D2,<ea>
                self.FreeReg(D2_reg)
                self.gCAttr.cKind = CAttrKind.COND
                self.gCAttr.CC = GCondition.NE
            elif BitsPerEl == 8:
                # optimize those bytes
                D = self.GetReg(Dlow, Dhigh)
                self.LoadAOrd(D, self.gCAttr, ByteOp)
                if Signed:
                    self.GenR(i16(0x4880), D)  # EXT.W D
                else:
                    self.GenR(i16(0x0240), D)
                    self.Gen(i16(0x00FF))      # ANDI.W #00ff,d
            else:
                D = self.LoadD(self.gCAttr, ByteOp, False)
                D = self.CheckClobber(D)
                self.gCAttr.ExReg = D
                self.GenRR(i16(0xE028), D2_reg, D)  # LSR.B D2,D
                self.FreeReg(D2_reg)
                if Signed:
                    self.GenRR(i16(0xE018), BitsPerEl, D)      # ROR.B #bpe,D
                    self.GenRR(i16(0xE000), 8 - BitsPerEl, D)  # ASR.B #8-bpe,D
                    self.GenR(i16(0x4880), D)                  # EXT.W D
                else:
                    self.GenR(i16(0x0240), D)
                    self.Gen(DataMask)                         # ANDI.W #datamask,d

        def ExtUField() -> None:
            """Extract an unsigned packed-record bitfield into gCAttr using BTST (1-bit), byte load, or shift+mask."""
            RightBit = self.NextByte()
            NumBits = pdiv(RightBit, 16)
            RightBit = pmod(RightBit, 16)
            self.Expression(self.NextByte(), -1, False)
            if NumBits == 1:
                if RightBit <= 7:
                    self.IncOffset(self.gCAttr, 1)
                self.GenEffAddr(
                    i16(0x0800), self.gCAttr, WordOp, True, 0, pmod(RightBit, 8)
                )  # BTST
                self.gCAttr.cKind = CAttrKind.COND
                self.gCAttr.CC = GCondition.NE
            else:
                if (RightBit == 8 or RightBit == 0) and NumBits == 8:
                    if RightBit == 0:
                        self.IncOffset(self.gCAttr, 1)
                    D = PrefReg
                    if D < 0:
                        D = self.GetReg(Dlow, Dhigh)
                    self.LoadAOrd(D, self.gCAttr, ByteOp)
                    self.GenR(i16(0x0240), D)
                    self.Gen(i16(0x00FF))  # ANDI.W #datamask,d
                else:
                    lSize = WordOp
                    if RightBit > 7:
                        lSize = ByteOp
                        RightBit = RightBit - 8
                    if PrefReg < A0:
                        D = self.LoaddWithPrefReg(PrefReg, self.gCAttr, lSize)
                    else:
                        D = self.LoadD(self.gCAttr, lSize, False)
                        D = self.CheckClobber(D)
                        self.gCAttr.ExReg = D
                    if RightBit > 0:
                        self.GenRR(i16(0xE048), RightBit, D)  # RSL.W #x,D
                    Mask = 0
                    for _ in range(1, NumBits + 1):
                        Mask = i16(Mask * 2 + 1)
                    self.GenR(i16(0x0240), D)
                    self.Gen(Mask)  # ANDI.W #mask,D

        def ExtSField() -> None:
            """Extract and sign-extend a signed packed-record bitfield via left-justify and arithmetic right shift."""
            RightBit = self.NextByte()
            NumBits = pdiv(RightBit, 16)
            RightBit = pmod(RightBit, 16)
            LeftBit = RightBit + NumBits - 1
            ShortFlag = LeftBit <= 7
            self.Expression(self.NextByte(), -1, False)
            if PrefReg < A0:
                D = self.LoaddWithPrefReg(PrefReg, self.gCAttr, WordOp)
            else:
                D = self.LoadD(self.gCAttr, WordOp, False)
                D = self.CheckClobber(D)
                self.gCAttr.ExReg = D
            if ShortFlag:
                Op = i16(0xE108)  # LSL.B
                ShiftCount = 7 - LeftBit
            else:
                Op = i16(0xE148)  # LSL.W
                ShiftCount = 15 - LeftBit
            if ShiftCount > 0:
                self.GenRR(Op, ShiftCount, D)
            RightBit = RightBit + ShiftCount
            if ShortFlag:
                Op = i16(0xE000)  # RSA.B
            else:
                Op = i16(0xE040)  # RSA.W
            if RightBit >= 8:
                self.GenR(Op, D)
                RightBit = RightBit - 8
            if RightBit > 0:
                self.GenRR(Op, RightBit, D)
            if ShortFlag:
                self.GenR(i16(0x4880), D)  # EXT.W

        def NumExpr(fOp_n: int, fSize: int, UsePrefReg: bool) -> bool:
            """Evaluate numeric subexpression fOp_n, materializing BOOL/COND/BITZ results into a data register."""
            self.Expression(fOp_n, -1, False)
            if self.gCAttr.cKind in (CAttrKind.BOOL, CAttrKind.COND, CAttrKind.BITZ):
                if UsePrefReg:
                    D = self.LoaddWithPrefReg(PrefReg, self.gCAttr, fSize)
                    if D == PrefReg:
                        UsePrefReg = False
                else:
                    self.LoadD(self.gCAttr, fSize, False)
            return UsePrefReg

        def Expr1(fOp: int, PrefReg: int) -> None:
            """Dispatch I-code opcodes 1..67: variables, dereferences, indexing, literals, range checks, type conversions, and integer add/sub."""
            NotOptimized = True
            lOp = 0
            D = 0
            lSize = 0

            def TryMOVEQ(aCAttr: CAttr) -> None:
                nonlocal NotOptimized
                if self.IsQuickCnst(aCAttr.CValu) and odd(fOp):
                    CnstD = self.LoadInt(
                        aCAttr.CValu.IValu[0], aCAttr.CValu.IValu[1], LongOp
                    )
                    aCAttr.cKind = CAttrKind.EXPR
                    aCAttr.ExReg = CnstD
                    NotOptimized = False
                    self.GenEffAddr(i16(lOp + D * 512), aCAttr, lSize, False, 0, 0)

            if fOp == 1:  # GLOBAL
                self.gCAttr.cKind = CAttrKind.VARB
                self.gCAttr.VLev = 1
                self.gCAttr.VOffset = i16(self.NextWord())
            elif fOp == 2:  # LOCAL
                self.gCAttr.cKind = CAttrKind.VARB
                self.gCAttr.VLev = self.ProcLvl
                self.gCAttr.VOffset = i16(self.NextWord())
            elif fOp == 3:  # INTER
                self.gCAttr.cKind = CAttrKind.VARB
                self.gCAttr.VLev = i16(self.ProcLvl - self.NextByte())
                self.gCAttr.VOffset = i16(self.NextWord())
            elif fOp == 4:  # COMMON
                self.gCAttr.cKind = CAttrKind.VARB
                self.gCAttr.VLev = i16(-self.NextByte())
                self.gCAttr.VOffset = i16(self.NextWord())
            elif fOp == 5:  # REGISTER
                self.gCAttr.cKind = CAttrKind.EXPR
                self.gCAttr.ExReg = self.NextByte()
                Count = self.NextByte()
                RSize = self.NextByte()
                if RSize != 0:
                    SaveAttr = self.gCAttr.copy()
                    self.Expression(self.NextByte(), self.gCAttr.ExReg, False)
                    lCAttr = self.gCAttr.copy()
                    self.gCAttr.set_from(SaveAttr)
                    if (
                        lCAttr.cKind != CAttrKind.EXPR
                        or self.gCAttr.ExReg != lCAttr.ExReg
                    ):
                        self.LoadAOrd(self.gCAttr.ExReg, lCAttr, RSize)
                if self.gCAttr.ExReg >= Dlow:
                    if self.gCAttr.ExReg <= Ahigh:
                        if self.gCAttr.ExReg <= Dhigh or self.gCAttr.ExReg >= Alow:
                            self.Reg[self.gCAttr.ExReg].Count = i16(
                                self.Reg[self.gCAttr.ExReg].Count + Count
                            )
            elif fOp == 12:  # UPARROW
                self.Expression(self.NextByte(), -1, False)
                DoIt = True
                A = 0
                if self.gCAttr.cKind == CAttrKind.EXPR:
                    if self.gCAttr.ExReg >= A0:
                        DoIt = False
                        A = self.gCAttr.ExReg
                if DoIt:
                    A = self.ReuseIfPossible(self.gCAttr, Alow, Ahigh)
                    self.GenEffAddr(
                        i16(8256 + (A - 8) * 512), self.gCAttr, LongOp, False, 0, 0
                    )  # MOVE.L ?,A
                self.gCAttr.cKind = CAttrKind.ADDR
                self.gCAttr.AdReg = A
                self.gCAttr.AOffset = 0
            elif fOp in (13, 14):  # FILE^, TEXT^
                self.Expression(self.NextByte(), -1, False)
                self.PushAddress(self.gCAttr)
                self.GenJSR('%_UPARR ')
                A = self.GetReg(Alow, Ahigh)
                self.GenRR(i16(0x205F), A, 0)  # MOVE.L (SP)+,A
                self.gCAttr.cKind = CAttrKind.ADDR
                self.gCAttr.AdReg = A
                self.gCAttr.AOffset = 0
            elif fOp == 15:  # FIELD
                lSize = i16(self.NextWord())
                self.Expression(self.NextByte(), -1, False)
                self.IncOffset(self.gCAttr, lSize)
            elif fOp == 16:  # INDX1
                GenIndex(1)
            elif fOp == 17:  # INDX2
                GenIndex(2)
            elif fOp == 18:  # INDX4
                GenIndex(4)
            elif fOp == 19:  # INDX8
                GenIndex(8)
            elif fOp == 20:  # INDXBIG
                GenIndex(self.NextWord())
            elif fOp == 21:  # INDXPCK
                PckdIndex()
            elif fOp == 22:  # ADDRESS
                i = self.NextByte()
                if i == 241:  # EXTREF
                    self.ExtRef()
                    self.CodError(2006)
                    i = self.NextByte()
                if i == 176 or i == 177:  # UFUNC or UPROC
                    i = self.NextWord()
                    proc = self.UserProcs[i]
                    assert proc is not None
                    self.GlobRef(proc.LinkName, proc.UserName, i16(self.Ic + 2))
                    A = PrefReg
                    if A <= D7:
                        A = self.GetReg(Alow, Ahigh)
                    if self.ShortCalls:
                        self.GenRR(i16(0x41FA), A, 0)
                        self.Gen(0)  # LEA $+xxx
                    else:
                        self.GenRR(i16(0x41F9), A, 0)
                        self.Gen(0)
                        self.Gen(0)  # LEA xxx.L
                else:
                    self.Expression(i, -1, False)
                    if PrefReg <= D7:
                        A = self.LoadAddress(self.gCAttr)
                    else:
                        A = PrefReg
                        self.ALoadAddress(self.gCAttr, A)
                self.gCAttr.cKind = CAttrKind.EXPR
                self.gCAttr.ExReg = A
            elif fOp == 23:  # NIL
                self.gCAttr.cKind = CAttrKind.CNST
                self.gCAttr.CValu = Valu()
                self.gCAttr.CValu.CstKind = ConstKind.SCALCNST
                self.gCAttr.CValu.IValu[0] = 0
                self.gCAttr.CValu.IValu[1] = 0
            elif fOp in (24, 25, 26, 27):  # CONST1, CONST2, CONST4, CONST8
                self.gCAttr.cKind = CAttrKind.CNST
                self.gCAttr.CValu = Valu()
                self.gCAttr.CValu.CstKind = ConstKind.SCALCNST
                sz = fOp - 23
                if sz == ByteOp:
                    i = self.NextByte()
                    if i > 127:
                        i = i - 256
                    self.gCAttr.CValu.IValu[1] = i16(i)
                    if i >= 0:
                        self.gCAttr.CValu.IValu[0] = 0
                    else:
                        self.gCAttr.CValu.IValu[0] = -1
                elif sz == WordOp:
                    self.gCAttr.CValu.IValu[1] = i16(self.NextWord())
                    self.gCAttr.CValu.IValu[0] = 0
                    if self.gCAttr.CValu.IValu[1] >= 0:
                        self.gCAttr.CValu.IValu[0] = 0
                    else:
                        self.gCAttr.CValu.IValu[0] = -1
                elif sz == LongOp:
                    self.gCAttr.CValu.IValu[0] = i16(self.NextWord())
                    self.gCAttr.CValu.IValu[1] = i16(self.NextWord())
                elif sz == Quad:
                    pass
            elif fOp in (28, 29):  # STRCNST, PAOCNST
                lSize = self.NextByte()
                lString: Optional[StrCRec]
                if lSize > 0:
                    lString = StrCRec('        ', None)
                else:
                    lString = None
                self.gCAttr.cKind = CAttrKind.CNST
                self.gCAttr.CValu = Valu()
                if fOp == 28:
                    self.gCAttr.CValu.CstKind = ConstKind.STRCNST
                else:
                    self.gCAttr.CValu.CstKind = ConstKind.PAOCCNST
                self.gCAttr.CValu.Len = lSize
                self.gCAttr.CValu.StrValu = lString
                Count = 0
                for _ in range(1, lSize + 1):
                    assert lString is not None
                    Count = Count + 1
                    if Count > 8:
                        lString.Next = StrCRec('        ', None)
                        lString = lString.Next
                        Count = 1
                    lString.StrVal = pset_ch(
                        lString.StrVal, Count, chr(self.NextByte())
                    )
            elif fOp in (32, 33, 34):  # inline ASSIGN 1, 2, 4
                DoIt = False
                SaveAttr = CAttr()
                lSize = i16(self.Op - 31)
                TriOp = self.NextByte() != 2
                if TriOp:
                    self.Expression(self.NextByte(), -1, False)
                    if self.gCAttr.cKind == CAttrKind.COND:
                        self.LoadCC(self.gCAttr)
                    SaveAttr = self.gCAttr.copy()
                self.Expression(self.NextByte(), -1, False)
                lCAttr = self.gCAttr.copy()
                if lCAttr.cKind == CAttrKind.EXPR:
                    # optimize those moves to register!
                    self.gCAttr.ExReg = lCAttr.ExReg
                    self.Expression(self.NextByte(), self.gCAttr.ExReg, False)
                    if (
                        self.gCAttr.cKind != CAttrKind.EXPR
                        or self.gCAttr.ExReg != self.gCAttr.ExReg
                    ):
                        lCAttr = self.gCAttr.copy()
                        self.LoadAOrd(self.gCAttr.ExReg, lCAttr, lSize)
                else:
                    self.Expression(self.NextByte(), -1, False)
                    if not TriOp:
                        if self.gCAttr.cKind == CAttrKind.EXPR:
                            self.Reg[self.gCAttr.ExReg].Count = i16(
                                self.Reg[self.gCAttr.ExReg].Count + 1
                            )
                        elif self.gCAttr.cKind == CAttrKind.ADDR:
                            self.Reg[self.gCAttr.AdReg].Count = i16(
                                self.Reg[self.gCAttr.AdReg].Count + 1
                            )
                        elif self.gCAttr.cKind == CAttrKind.INDX:
                            self.Reg[self.gCAttr.InxAReg].Count = i16(
                                self.Reg[self.gCAttr.InxAReg].Count + 1
                            )
                            self.Reg[self.gCAttr.InxRReg].Count = i16(
                                self.Reg[self.gCAttr.InxRReg].Count + 1
                            )
                        else:
                            SaveAttr = self.gCAttr.copy()
                            DoIt = True
                    self.Store(self.gCAttr, lCAttr, lSize)
                if TriOp or DoIt:
                    self.gCAttr.set_from(SaveAttr)
            elif fOp == 43:  # WITHREC
                i = self.NextByte()
                self.gCAttr.set_from(self.WithCAttr[i].Cat)
                if self.WithCAttr[i].Indirect:
                    if (
                        self.gCAttr.cKind == CAttrKind.EXPR
                        and self.gCAttr.ExReg >= A0
                    ):
                        A = self.gCAttr.ExReg
                    else:
                        A = self.GetReg(Alow, Ahigh)
                        self.GenEffAddr(
                            i16(0x2040 + (A - 8) * 512),
                            self.gCAttr,
                            LongOp,
                            False,
                            0,
                            0,
                        )  # MOVE.L g,A
                    self.gCAttr.cKind = CAttrKind.ADDR
                    self.gCAttr.AdReg = A
                    self.gCAttr.AOffset = 0
            elif fOp == 46:  # RANGE
                Lo = i16(self.NextWord())
                HI = i16(self.NextWord())
                self.Expression(self.NextByte(), -1, False)
                D = self.LoadD(self.gCAttr, WordOp, False)
                if Lo == 0:
                    self.GenRR(i16(0x41BC), D, 0)
                    self.Gen(HI)  # CHK #hi,D
                elif i16(HI - Lo) > 0:  # ie. within 15 bits
                    D2_reg = self.GetReg(Dlow, Dhigh)
                    self.GenRR(i16(0x3000), D2_reg, D)  # MOVE.W D,D2
                    if abs(Lo) <= 8:
                        if Lo > 0:
                            self.GenRR(i16(0x5140), Lo, D2_reg)   # SUBQ.W #lo,D2
                        else:
                            self.GenRR(i16(0x5040), -Lo, D2_reg)  # ADDQ.W #-lo,D2
                    else:
                        self.GenR(i16(0x0440), D2_reg)
                        self.Gen(Lo)  # SUBI.W #lo,D2
                    self.GenRR(i16(0x41BC), D2_reg, 0)
                    self.Gen(i16(HI - Lo))  # CHK #hi-lo,D2
                    self.FreeReg(D2_reg)
                else:
                    self.GenR(i16(0x3F00), D)  # MOVE.W D,-(SP)
                    self.PushInt(Lo, WordOp)
                    self.PushInt(HI, WordOp)
                    self.GenJSR('%_RCHCK ')
            elif fOp == 47:  # SRANGE
                HI = self.NextByte()
                self.Expression(self.NextByte(), -1, False)
                A = self.LoadAddress(self.gCAttr)
                self.GenR(i16(0x1F10), A)  # MOVE.B (A),-(SP)
                self.PushInt(HI, WordOp)
                self.GenJSR('%_SRCHK ')
                self.gCAttr.cKind = CAttrKind.ADDR
                self.gCAttr.AdReg = A
                self.gCAttr.AOffset = 0
            elif fOp in (48, 49, 50):  # INT12, INT24, INT14
                if odd(fOp):
                    lSize = WordOp
                else:
                    lSize = ByteOp
                self.Expression(self.NextByte(), -1, False)
                if self.gCAttr.cKind != CAttrKind.CNST:
                    D = self.LoadD(self.gCAttr, lSize, False)
                    self.gCAttr.ExReg = D
                    if not odd(fOp):
                        self.GenR(i16(0x4880), D)  # EXT.W D
                    if fOp >= 49:
                        self.GenR(i16(0x48C0), D)  # EXT.L D
            elif fOp in (51, 52, 53):  # INT21, INT42, INT41
                if fOp == 51:
                    lSize = WordOp
                else:
                    lSize = LongOp
                self.Expression(self.NextByte(), -1, False)
                DoIt = True
                if self.gCAttr.cKind != CAttrKind.CNST:
                    if self.gCAttr.cKind in (
                        CAttrKind.ADDR,
                        CAttrKind.VARB,
                        CAttrKind.INDX,
                    ):
                        DoIt = False
                    if DoIt or TrapV:
                        D = self.LoadD(self.gCAttr, lSize, False)
                    else:
                        self.IncOffset(self.gCAttr, fOp - 50)
                    if TrapV:
                        if lSize == LongOp:
                            LongTRAPV(D)
            elif fOp == 54:  # REAL48
                if not self.HaveExtTmp:
                    self.GetTemp(self.ExtTmp, 10)
                    self.HaveExtTmp = True
                self.Expression(self.NextByte(), -1, False)
                if self.gCAttr.cKind == CAttrKind.CNST:
                    if not self.HaveRealTmp:
                        self.GetTemp(self.RealTmp, 4)
                        self.HaveRealTmp = True
                    self.Store(self.gCAttr, self.RealTmp, LongOp)
                    self.gCAttr.set_from(self.RealTmp)
                self.PushAddress(self.gCAttr)
                self.PushAddress(self.ExtTmp)
                self.Gen(i16(0x3F3C))
                self.Gen(i16(0x100E))  # MOVE.W #FFSGL+FOZ2X,-(SP) ; real to ext
                if self.MacFlag:
                    self.Gen(i16(0xA9EB))  # _FP68K trap
                else:
                    self.GenJSR('FP68K   ')
                lCAttr = CAttr()
                self.GetTemp(lCAttr, 8)
                self.PushAddress(self.ExtTmp)
                self.PushAddress(lCAttr)
                self.Gen(i16(0x3F3C))
                self.Gen(i16(0x0810))  # MOVE.W #FFDBL+FOX2Z,-(SP) ; ext to dbl
                if self.MacFlag:
                    self.Gen(i16(0xA9EB))  # _FP68K trap
                else:
                    self.GenJSR('FP68K   ')
                self.gCAttr.set_from(lCAttr)
            elif fOp == 56:  # FLOAT4
                Push4Call('%I_FLT  ')
            elif fOp == 58:  # TRUNC4
                Push4Call('%_TRUNC ')
            elif fOp == 60:  # ROUND4
                Push4Call('%_ROUND ')
            elif fOp == 62:  # EXTUFLD
                ExtUField()
            elif fOp == 63:  # EXTSFLD
                ExtSField()
            elif fOp in (64, 65, 66, 67):  # IADD2, IADD4, ISUB2, ISUB4
                NotOptimized = True
                UsePrefReg = True
                if odd(fOp):
                    lSize = LongOp
                else:
                    lSize = WordOp
                UsePrefReg = NumExpr(self.NextByte(), lSize, UsePrefReg)
                lCAttr = self.gCAttr.copy()
                UsePrefReg = NumExpr(self.NextByte(), lSize, UsePrefReg)
                if (
                    self.gCAttr.cKind == CAttrKind.CNST
                    and lCAttr.cKind == CAttrKind.CNST
                ):
                    # fold those suckers
                    if fOp <= 65:
                        self.SetValuLInt(
                            self.gCAttr.CValu,
                            i32(
                                self.ValuLInt(lCAttr.CValu)
                                + self.ValuLInt(self.gCAttr.CValu)
                            ),
                        )
                    else:
                        self.SetValuLInt(
                            self.gCAttr.CValu,
                            i32(
                                self.ValuLInt(lCAttr.CValu)
                                - self.ValuLInt(self.gCAttr.CValu)
                            ),
                        )
                else:
                    if fOp <= 65:  # addition
                        lOp = i16(0xD040)  # ADD.W
                        if odd(fOp):
                            lOp = i16(lOp + 64)  # .W --> .L
                        if (
                            (
                                self.gCAttr.cKind == CAttrKind.EXPR
                                and self.gCAttr.ExReg >= Dhigh
                                and lCAttr.cKind == CAttrKind.EXPR
                            )
                            or (self.gCAttr.cKind == CAttrKind.CNST)
                            or (
                                lCAttr.cKind == CAttrKind.EXPR
                                and lCAttr.ExReg == PrefReg
                            )
                        ):
                            # addition commutes
                            tCAttr = self.gCAttr.copy()
                            self.gCAttr.set_from(lCAttr)
                            lCAttr = tCAttr
                        D = self.LoaddWithPrefReg(PrefReg, self.gCAttr, lSize)
                        if PrefReg >= A0:
                            D = D - 8
                            if odd(fOp):
                                lOp = i16(lOp + (0x1C0 - 0x80))  # -->ADDA.L
                            else:
                                lOp = i16(lOp + 0x80)            # -->ADDA.W
                        if lCAttr.cKind == CAttrKind.CNST:
                            iv1 = i16(lCAttr.CValu.IValu[1])
                            iv0 = i16(lCAttr.CValu.IValu[0])
                            if iv1 <= 8 and iv1 >= 0 and iv0 == 0:
                                NotOptimized = False
                                if iv1 != 0:
                                    lOp = i16(0x5080)  # ADDQ.L
                                    if fOp == 64:      # IADD2
                                        lOp = i16(0x5040)  # ADDQ.W
                                    if PrefReg >= A0:
                                        lOp = i16(lOp + 8)
                                    lOp = i16(lOp + pmod(iv1, 8) * 512)
                                    self.GenR(lOp, D)
                            else:
                                TryMOVEQ(lCAttr)
                        if NotOptimized:
                            self.GenEffAddr(
                                i16(lOp + D * 512), lCAttr, lSize, False, 0, 0
                            )
                    else:  # subtraction
                        lOp = i16(0x9040)  # SUB.W
                        if (
                            self.gCAttr.cKind == CAttrKind.EXPR
                            and self.gCAttr.ExReg == PrefReg
                        ):
                            # a-b --> -b+a
                            tCAttr = self.gCAttr.copy()
                            self.gCAttr.set_from(lCAttr)
                            lCAttr = tCAttr
                            lOp = i16(0x4440)  # NEG.W
                            if odd(fOp):
                                lOp = i16(lOp + 64)  # .W --> .L
                            self.GenEffAddr(lOp, lCAttr, lSize, False, 0, 0)
                            lOp = i16(0xD040)  # ADD.W
                        if (
                            self.gCAttr.cKind == CAttrKind.STCK
                            and lCAttr.cKind == CAttrKind.STCK
                        ):
                            D = self.LoadD(self.gCAttr, lSize, False)
                        if PrefReg >= A0:
                            self.LoadAOrd(PrefReg, lCAttr, lSize)
                            D = PrefReg - 8
                            if odd(fOp):
                                lOp = i16(lOp + 0x180)  # SUBA.L
                            else:
                                lOp = i16(lOp + 0x80)   # SUBA.W
                        else:
                            D = self.LoaddWithPrefReg(PrefReg, lCAttr, lSize)
                            if odd(fOp):
                                lOp = i16(lOp + 64)     # .W --> .L
                        if self.gCAttr.cKind == CAttrKind.CNST and PrefReg < A0:
                            iv1 = i16(self.gCAttr.CValu.IValu[1])
                            iv0 = i16(self.gCAttr.CValu.IValu[0])
                            if iv1 <= 8 and iv1 >= 0 and iv0 == 0:
                                NotOptimized = False
                                if iv1 != 0:
                                    lOp = i16(0x5180)  # SUBQ.L
                                    if fOp == 66:      # ISUB2
                                        lOp = i16(0x5140)  # SUBQ.W
                                    lOp = i16(lOp + pmod(iv1, 8) * 512)
                                    self.GenR(lOp, D)
                            else:
                                TryMOVEQ(self.gCAttr)
                        if NotOptimized:
                            self.GenEffAddr(
                                i16(lOp + D * 512), self.gCAttr, lSize, False, 0, 0
                            )
                    if TrapV:
                        self.Gen(i16(0x4E76))  # TRAPV
                    self.gCAttr.cKind = CAttrKind.EXPR
                    if PrefReg >= A0:
                        self.gCAttr.ExReg = PrefReg
                    else:
                        self.gCAttr.ExReg = D

        def Expr2(fOp: int, PrefReg: int) -> None:
            """Dispatch I-code opcodes 68..155: mul/div/mod/neg/abs/sqr, bitwise/boolean ops, scalar/float/string/PAOC comparisons."""
            if fOp == 68:  # IMULT2
                if PrefReg >= A0:
                    PrefReg = -1
                UsePrefReg = True
                UsePrefReg = NumExpr(self.NextByte(), WordOp, UsePrefReg)
                lCAttr = self.gCAttr.copy()
                UsePrefReg = NumExpr(self.NextByte(), WordOp, UsePrefReg)
                Optimized = False
                DoIt = True
                ShiftCnt = 0
                D = 0
                if lCAttr.cKind == CAttrKind.CNST:
                    DoIt = i16(lCAttr.CValu.IValu[1]) != 1
                    Optimized, ShiftCnt = self.ShiftMult(i16(lCAttr.CValu.IValu[1]))
                elif self.gCAttr.cKind == CAttrKind.CNST:
                    DoIt = i16(self.gCAttr.CValu.IValu[1]) != 1
                    Optimized, ShiftCnt = self.ShiftMult(
                        i16(self.gCAttr.CValu.IValu[1])
                    )
                    if Optimized:
                        self.gCAttr.set_from(lCAttr)
                if Optimized:
                    if DoIt:
                        D = self.LoaddWithPrefReg(PrefReg, self.gCAttr, WordOp)
                        self.GenRR(i16(0xE140), ShiftCnt, D)  # ASL.W #shiftcnt,d
                        if TrapV:
                            self.Gen(i16(0x4E76))  # TRAPV
                else:
                    if (
                        self.gCAttr.cKind == CAttrKind.EXPR
                        and self.gCAttr.ExReg == PrefReg
                    ):
                        D = self.LoaddWithPrefReg(PrefReg, self.gCAttr, WordOp)
                    elif lCAttr.cKind == CAttrKind.EXPR:
                        D = self.LoaddWithPrefReg(PrefReg, lCAttr, WordOp)
                        lCAttr = self.gCAttr.copy()
                    else:
                        D = self.LoadD(self.gCAttr, WordOp, False)
                        D = self.CheckClobber(D)
                    self.GenEffAddr(
                        i16(-15936 + D * 512), lCAttr, WordOp, False, 0, 0
                    )  # C1C0
                    if TrapV:
                        LongTRAPV(D)
                if not (Optimized and (not DoIt)):
                    self.gCAttr.cKind = CAttrKind.EXPR
                    self.gCAttr.ExReg = D
            elif fOp == 69:  # IMULT4
                if PrefReg >= A0:
                    PrefReg = -1
                self.Expression(self.NextByte(), -1, False)
                lCAttr = self.gCAttr.copy()
                self.Expression(self.NextByte(), -1, False)
                Optimized = False
                DoIt = True
                ShiftCnt = 0
                if lCAttr.cKind == CAttrKind.CNST:
                    DoIt = i16(lCAttr.CValu.IValu[1]) != 1
                    if i16(lCAttr.CValu.IValu[0]) == 0:
                        Optimized, ShiftCnt = self.ShiftMult(
                            i16(lCAttr.CValu.IValu[1])
                        )
                elif self.gCAttr.cKind == CAttrKind.CNST:
                    DoIt = i16(self.gCAttr.CValu.IValu[1]) != 1
                    if i16(self.gCAttr.CValu.IValu[0]) == 0:
                        Optimized, ShiftCnt = self.ShiftMult(
                            i16(self.gCAttr.CValu.IValu[1])
                        )
                    if Optimized:
                        self.gCAttr.set_from(lCAttr)
                if Optimized:
                    if DoIt:
                        D = self.LoaddWithPrefReg(PrefReg, self.gCAttr, LongOp)
                        self.GenRR(i16(0xE180), ShiftCnt, D)  # ASL.L #shiftcnt,d
                        if TrapV:
                            self.Gen(i16(0x4E76))  # TRAPV
                        self.gCAttr.ExReg = D
                else:
                    self.PushValue(lCAttr, LongOp)  # JSR %I_MUL4
                    self.PushValue(self.gCAttr, LongOp)
                    self.GenJSR('%I_MUL4 ')
                    self.gCAttr.cKind = CAttrKind.STCK
            elif fOp in (70, 72):  # IDIV2, IMOD2
                UsePrefReg = False
                UsePrefReg = NumExpr(self.NextByte(), WordOp, UsePrefReg)
                lCAttr = self.gCAttr.copy()
                UsePrefReg = NumExpr(self.NextByte(), WordOp, UsePrefReg)
                if (
                    self.gCAttr.cKind == CAttrKind.STCK
                    and lCAttr.cKind == CAttrKind.STCK
                ):
                    D = self.LoadD(self.gCAttr, WordOp, False)
                D = self.LoadD(lCAttr, WordOp, False)
                D = self.CheckClobber(D)
                self.GenR(i16(0x48C0), D)  # EXT.L
                self.GenEffAddr(
                    i16(-32320 + D * 512), self.gCAttr, WordOp, False, 0, 0
                )  # 81C0
                if fOp == 72:
                    self.GenR(i16(0x4840), D)  # SWAP d
                    self.GenR(i16(0x4A40), D)  # TST.W d
                elif TrapV:
                    self.Gen(i16(0x4E76))      # TRAPV
                self.gCAttr.cKind = CAttrKind.EXPR
                self.gCAttr.ExReg = D
            elif fOp == 71:  # IDIV4
                Push44Call('%I_DIV4 ')
            elif fOp == 73:  # IMOD4
                Push44Call('%I_MOD4 ')
            elif fOp in (74, 75, 76, 77):  # INEG2, INEG4, IABS2, IABS4
                if odd(fOp):
                    lOp = i16(0x4480)  # NEG.L
                    lSize = LongOp
                else:
                    lOp = i16(0x4440)  # NEG.W
                    lSize = WordOp
                self.Expression(self.NextByte(), -1, False)
                D = self.LoadD(self.gCAttr, lSize, fOp > 75)
                D = self.CheckClobber(D)
                self.gCAttr.ExReg = D
                if fOp > 75:
                    self.Gen(i16(0x6A02))  # BPL $+4
                self.GenR(lOp, D)
                if TrapV:
                    self.Gen(i16(0x4E76))  # TRAPV
            elif fOp == 78:  # ISQR2
                self.Expression(self.NextByte(), -1, False)
                D = self.LoadD(self.gCAttr, WordOp, False)
                D = self.CheckClobber(D)
                self.GenRR(i16(0xC1C0), D, D)
                if TrapV:
                    LongTRAPV(D)
                self.gCAttr.cKind = CAttrKind.EXPR
                self.gCAttr.ExReg = D
            elif fOp == 79:  # ISQR4
                self.Expression(self.NextByte(), -1, False)
                self.PushValue(self.gCAttr, LongOp)
                self.Gen(i16(0x2F17))  # MOVE.L (SP),-(SP)
                self.GenJSR('%I_MUL4 ')
                self.gCAttr.cKind = CAttrKind.STCK
            elif fOp in (80, 81, 82, 83, 84, 85):  # AND1..IOR4
                if fOp > 82:
                    lOp = i16(-32767 - 1)  # OR ($8000)
                else:
                    lOp = i16(0xC000)      # AND
                mOp = pmod(fOp - 80, 3)
                if mOp == 0:
                    lSize = ByteOp
                elif mOp == 1:
                    lSize = WordOp
                    lOp = i16(lOp + 0x40)
                else:
                    lSize = LongOp
                    lOp = i16(lOp + 0x80)
                self.Expression(self.NextByte(), -1, False)
                if self.gCAttr.cKind == CAttrKind.COND:
                    self.LoadCC(self.gCAttr)
                lCAttr = self.gCAttr.copy()
                self.Expression(self.NextByte(), -1, False)
                if self.gCAttr.cKind == CAttrKind.COND:
                    self.LoadCC(self.gCAttr)
                if (
                    self.gCAttr.cKind
                    in (CAttrKind.EXPR, CAttrKind.BOOL, CAttrKind.BITZ)
                    and self.gCAttr.ExReg == PrefReg
                ):
                    tCAttr = self.gCAttr.copy()
                    self.gCAttr.set_from(lCAttr)
                    lCAttr = tCAttr
                if lCAttr.cKind in (
                    CAttrKind.EXPR,
                    CAttrKind.BOOL,
                    CAttrKind.BITZ,
                ):
                    D = lCAttr.ExReg
                    tCAttr = self.gCAttr.copy()
                else:
                    if self.gCAttr.cKind in (CAttrKind.BOOL, CAttrKind.BITZ):
                        D = self.gCAttr.ExReg
                    else:
                        D = self.LoadD(self.gCAttr, lSize, False)
                    tCAttr = lCAttr.copy()
                if tCAttr.cKind in (CAttrKind.BOOL, CAttrKind.BITZ):
                    tCAttr.cKind = CAttrKind.EXPR
                if D != PrefReg:
                    D = self.CheckClobber(D)
                self.GenEffAddr(i16(lOp + D * 512), tCAttr, lSize, False, 0, 0)
                if fOp <= 82:
                    if (
                        self.gCAttr.cKind in (CAttrKind.BOOL, CAttrKind.BITZ)
                        and lCAttr.cKind in (CAttrKind.BOOL, CAttrKind.BITZ)
                    ):
                        if self.gCAttr.cKind == CAttrKind.BOOL:
                            self.gCAttr.cKind = lCAttr.cKind
                        else:
                            self.gCAttr.cKind = CAttrKind.BITZ
                    else:
                        self.gCAttr.cKind = CAttrKind.EXPR
                else:
                    if (
                        self.gCAttr.cKind == CAttrKind.BOOL
                        and lCAttr.cKind == CAttrKind.BOOL
                    ):
                        self.gCAttr.cKind = CAttrKind.BOOL
                    elif (
                        self.gCAttr.cKind
                        not in (CAttrKind.BOOL, CAttrKind.BITZ)
                        and lCAttr.cKind
                        not in (CAttrKind.BOOL, CAttrKind.BITZ)
                    ):
                        self.gCAttr.cKind = CAttrKind.EXPR
                    else:
                        self.gCAttr.cKind = CAttrKind.BITZ
                self.gCAttr.ExReg = D
            elif fOp in (89, 90, 91):  # NOT1, NOT2, NOT4
                if PrefReg >= A0:
                    PrefReg = -1
                lOp = i16(0x4600)  # NOT
                fOp = fOp - 89
                if fOp == 0:
                    lSize = ByteOp
                elif fOp == 1:
                    lSize = WordOp
                    lOp = i16(lOp + 64)
                else:
                    lSize = LongOp
                    lOp = i16(lOp + 128)
                self.Expression(self.NextByte(), -1, False)
                D = self.LoaddWithPrefReg(PrefReg, self.gCAttr, lSize)
                self.GenR(lOp, D)
                self.gCAttr.cKind = CAttrKind.EXPR
                self.gCAttr.ExReg = D
            elif 92 <= fOp <= 109:  # LT1..NE4
                fOp = fOp - 92
                rem = pmod(fOp, 3)
                if rem == 0:
                    lSize = ByteOp
                elif rem == 1:
                    lSize = WordOp
                else:
                    lSize = LongOp
                lCC = (
                    GCondition.LT,
                    GCondition.GT,
                    GCondition.LE,
                    GCondition.GE,
                    GCondition.EQ,
                    GCondition.NE,
                )[pdiv(fOp, 3)]
                UsePrefReg = False
                UsePrefReg = NumExpr(self.NextByte(), lSize, UsePrefReg)
                lCAttr = self.gCAttr.copy()
                UsePrefReg = NumExpr(self.NextByte(), lSize, UsePrefReg)
                if self.GenCompare(lCAttr, self.gCAttr, lSize):
                    if lCC == GCondition.LT:
                        lCC = GCondition.GT
                    elif lCC == GCondition.LE:
                        lCC = GCondition.GE
                    elif lCC == GCondition.GT:
                        lCC = GCondition.LT
                    elif lCC == GCondition.GE:
                        lCC = GCondition.LE
                self.gCAttr.cKind = CAttrKind.COND
                self.gCAttr.CC = lCC
            elif fOp == 110:  # BNOT
                if PrefReg >= A0:
                    PrefReg = -1
                self.Expression(self.NextByte(), -1, False)
                if self.gCAttr.cKind == CAttrKind.COND:
                    self.gCAttr.CC = {
                        GCondition.LT: GCondition.GE,
                        GCondition.LE: GCondition.GT,
                        GCondition.GT: GCondition.LE,
                        GCondition.GE: GCondition.LT,
                        GCondition.EQ: GCondition.NE,
                        GCondition.NE: GCondition.EQ,
                        GCondition.HI: GCondition.LS,
                        GCondition.LS: GCondition.HI,
                    }[self.gCAttr.CC]
                elif self.gCAttr.cKind in (CAttrKind.BOOL, CAttrKind.BITZ):
                    self.gCAttr.ExReg = self.CheckClobber(self.gCAttr.ExReg)
                    self.GenR(i16(0x5200), self.gCAttr.ExReg)  # ADDQ.B #1,D
                    if self.gCAttr.cKind == CAttrKind.BOOL:
                        self.gCAttr.cKind = CAttrKind.EXPR
                else:
                    D = self.LoaddWithPrefReg(PrefReg, self.gCAttr, ByteOp)
                    self.GenR(i16(0x0A00), D)
                    self.Gen(1)  # EORI.B #1,d
                    self.gCAttr.ExReg = D
            elif fOp == 111:  # ODD
                if PrefReg >= A0:
                    PrefReg = -1
                self.Expression(self.NextByte(), -1, False)
                D = self.LoaddWithPrefReg(PrefReg, self.gCAttr, ByteOp)
                self.GenR(i16(0x0240), D)
                self.Gen(1)  # ANDI.W #1,D
                self.gCAttr.ExReg = D
            elif fOp == 112:  # FADD4
                Push44Call('%F_ADD  ')
            elif fOp == 114:  # FSUB4
                Push44Call('%F_SUB  ')
            elif fOp == 116:  # FMUL4
                Push44Call('%F_MUL  ')
            elif fOp == 118:  # FDIV4
                Push44Call('%F_DIV  ')
            elif fOp == 122:  # FLT4
                Push44Call('%F_LT   ')
            elif fOp == 124:  # FGT4
                Push44Call('%F_GT   ')
            elif fOp == 126:  # FLE4
                Push44Call('%F_LE   ')
            elif fOp == 128:  # FGE4
                Push44Call('%F_GE   ')
            elif fOp == 130:  # FEQ4
                Push44Call('%F_EQ   ')
            elif fOp == 132:  # FNE4
                Push44Call('%F_NE   ')
            elif fOp == 134:  # FNEG4
                Push4Call('%F_NEG  ')
            elif fOp == 136:  # FABS
                Push4Call('%F_ABS  ')
            elif fOp == 138:  # FSQR4
                self.Expression(self.NextByte(), -1, False)
                self.PushValue(self.gCAttr, LongOp)
                self.Gen(i16(0x2F17))  # MOVE.L (SP),-(SP)
                self.GenJSR('%F_MUL  ')
                self.gCAttr.cKind = CAttrKind.STCK
            elif fOp == 140:  # TRAPV
                self.Expression(self.NextByte(), -1, True)
            elif fOp == 144:  # STRLT
                PushAACall('%S_LT   ')
            elif fOp == 145:  # STRGT
                PushAACall('%S_GT   ')
            elif fOp == 146:  # STRLE
                PushAACall('%S_LE   ')
            elif fOp == 147:  # STRGE
                PushAACall('%S_GE   ')
            elif fOp == 148:  # STREQ
                PushAACall('%S_EQ   ')
            elif fOp == 149:  # STRNE
                PushAACall('%S_NE   ')
            elif 150 <= fOp <= 155:  # PAOCLT..PAOCNE
                lSize = self.NextByte()
                mSize = self.NextByte()
                if lSize != mSize:
                    self.CodError(9000)
                self.Expression(self.NextByte(), -1, False)
                A1_reg = self.LoadAddress(self.gCAttr)
                self.Expression(self.NextByte(), -1, False)
                A2_reg = self.LoadAddress(self.gCAttr)
                D = self.LoadInt(0, i16(lSize - 1), WordOp)
                A1_reg = self.CheckClobber(A1_reg)
                A2_reg = self.CheckClobber(A2_reg)
                if fOp == 150 or fOp == 153:  # LT or GE
                    A = A1_reg
                    A1_reg = A2_reg
                    A2_reg = A
                self.GenRR(i16(0xB108), A1_reg, A2_reg)  # CMPM.B (A1)+,(A2)+
                self.GenR(i16(0x56C8), D)
                self.Gen(-4)                             # DBNE
                self.FreeReg(A1_reg)
                self.FreeReg(A2_reg)
                self.FreeReg(D)
                self.gCAttr.cKind = CAttrKind.COND
                if fOp in (150, 151):  # PAOCLT, PAOCGT
                    self.gCAttr.CC = GCondition.HI
                elif fOp in (152, 153):  # PAOCLE, PAOCGE
                    self.gCAttr.CC = GCondition.LS
                elif fOp == 154:  # PAOCEQ
                    self.gCAttr.CC = GCondition.EQ
                elif fOp == 155:  # PAOCNE
                    self.gCAttr.CC = GCondition.NE

        def Expr3(fOp: int, PrefReg: int) -> None:
            """Dispatch I-code opcodes >= 163: set membership (IN), set relational comparisons, and function calls."""
            if fOp == 163:  # IN
                SetSize = self.NextByte()
                self.Expression(self.NextByte(), -1, False)
                D = self.LoadD(self.gCAttr, WordOp, True)
                lLab1 = self.NewLabel()
                lLab2 = self.NewLabel()
                self.GenJump(i16(107 * 256), lLab2)  # BMI
                OnStack = self.SetExpression(self.NextByte())
                if OnStack:
                    D2_reg = self.GetReg(Dlow, Dhigh)
                    self.FreeReg(D2_reg)
                    self.GenRR(i16(0x3017), D2_reg, 0)  # MOVE.W (SP),D2
                    self.GenR(i16(0xE748), D2_reg)      # LSL.W #3,D2
                    self.GenR(i16(0x5340), D2_reg)      # SUBQ.W #1,D2
                    self.GenRR(i16(0xB040), D, D2_reg)  # CMP.W D2,D
                else:
                    self.GenRR(i16(0xB07C), D, 0)
                    self.Gen(i16(SetSize * 8 - 1))      # CMP.W #xx,D
                self.GenJump(i16(110 * 256), lLab1)     # BGT
                if OnStack:
                    D = self.CheckClobber(D)
                    D2_reg = self.GetReg(Dlow, Dhigh)
                    self.FreeReg(D2_reg)
                    self.GenRR(i16(0x3000), D2_reg, D)  # MOVE.W D,D2
                    self.GenR(i16(0xE648), D2_reg)      # LSR.W #3,D2
                    self.GenR(i16(0x4440), D2_reg)      # NEG.W D2
                    self.GenRR(i16(0xD057), D2_reg, 0)  # ADD.W (SP),D2
                    self.GenRR(i16(0x0130), D, SP)
                    self.Gen(i16(D2_reg * 4096 + 1))    # BTST D,1(SP,D2.W)
                elif self.gCAttr.cKind == CAttrKind.EXPR:
                    self.GenRR(256, D, self.gCAttr.ExReg)  # BTST D,exreg
                    self.FreeReg(self.gCAttr.ExReg)
                else:
                    if self.gCAttr.cKind != CAttrKind.CNST:
                        self.IncOffset(self.gCAttr, SetSize)
                    D = self.CheckClobber(D)
                    A = self.LoadAddress(self.gCAttr)
                    self.FreeReg(A)
                    D2_reg = self.GetReg(Dlow, Dhigh)
                    self.FreeReg(D2_reg)
                    self.GenRR(i16(0x3000), D2_reg, D)  # MOVE.W D,D2
                    self.GenR(i16(0xE648), D2_reg)      # LSR.W #3,D2
                    self.GenR(i16(0x4440), D2_reg)      # NEG.W D2
                    self.GenRR(i16(0x0130), D, A)
                    self.Gen(i16(D2_reg * 4096 + 255))  # BTST D,-1(A,D2.W)
                self.Gen(i16(0x0A3C))
                self.Gen(4)  # EORI.B #4,CCR
                self.DefILabel(lLab1)
                self.FreeReg(D)
                if OnStack:
                    self.Gen(i16(0xDEDF))  # ADDA.W (SP)+,SP
                self.DefILabel(lLab2)
                self.gCAttr.cKind = CAttrKind.COND
                self.gCAttr.CC = GCondition.EQ
            elif fOp in (164, 165, 166, 167):  # SETLE, SETGE, SETEQ, SETNE
                SetSize = self.NextByte()
                LeftStack = self.SetExpression(self.NextByte())
                lCAttr = self.gCAttr.copy()
                RightStack = self.SetExpression(self.NextByte())
                if SetSize > 4 or LeftStack or RightStack:
                    if not LeftStack:
                        self.PushSet(lCAttr, SetSize, True)
                    if not RightStack:
                        self.PushSet(self.gCAttr, SetSize, True)
                    if fOp == 164:
                        if RightStack and (not LeftStack):
                            self.GenJSR('%_SETGE ')
                        else:
                            self.GenJSR('%_SETLE ')
                    elif fOp == 165:
                        if RightStack and (not LeftStack):
                            self.GenJSR('%_SETLE ')
                        else:
                            self.GenJSR('%_SETGE ')
                    elif fOp == 166:
                        self.GenJSR('%_SETEQ ')
                    elif fOp == 167:
                        self.GenJSR('%_SETNE ')
                    self.gCAttr.cKind = CAttrKind.STCK
                else:
                    if SetSize == 1:
                        lOpSize = 0
                        lSize = ByteOp
                    elif SetSize == 2:
                        lOpSize = 64
                        lSize = WordOp
                    else:
                        lOpSize = 128
                        lSize = LongOp
                    D = self.LoadD(lCAttr, lSize, False)
                    D2_reg = self.LoadD(self.gCAttr, lSize, False)
                    if fOp == 165:  # >=
                        t = D
                        D = D2_reg
                        D2_reg = t
                    if fOp <= 165:
                        D2_reg = self.CheckClobber(D2_reg)
                        self.GenR(i16(0x4600 + lOpSize), D2_reg)  # NOT D2
                        D = self.CheckClobber(D)
                        self.GenRR(
                            i16(-16384 + lOpSize), D, D2_reg
                        )  # AND D2,D ($C000)
                    else:
                        # CMP D,D2
                        self.GenRR(
                            i16(-20480 + lOpSize), D, D2_reg
                        )  # ($B000)
                    self.gCAttr.cKind = CAttrKind.COND
                    if fOp == 167:  # <>
                        self.gCAttr.CC = GCondition.NE
                    else:
                        self.gCAttr.CC = GCondition.EQ
                    self.FreeReg(D)
                    self.FreeReg(D2_reg)
            elif fOp == 190:  # PARMLST
                self.GenCall()

        if fOp <= 67:
            Expr1(fOp, PrefReg)
        elif fOp <= 155:
            Expr2(fOp, PrefReg)
        else:
            Expr3(fOp, PrefReg)

    # ========================================================================
    # 4. Statements and standard/user/method/INLINE calls
    # ========================================================================

    def WithStmt(self) -> None:
        """Bind a WITH-statement record expression to WithCAttr[WithLevel], spilling computed addresses to a frame temp."""
        _i = self.NextByte()
        is_ptr = self.NextByte()
        self.Expression(self.NextByte(), -1, False)
        self.WithLevel = i16(self.WithLevel + 1)
        if self.gCAttr.cKind == CAttrKind.VARB and (
            self.gCAttr.VLev <= 1 or self.gCAttr.VLev == self.ProcLvl
        ):
            self.WithCAttr[self.WithLevel].Cat.set_from(self.gCAttr)
            self.WithCAttr[self.WithLevel].Indirect = is_ptr != 0
        else:
            self.WithCAttr[self.WithLevel].Indirect = True
            if self.gCAttr.cKind == CAttrKind.EXPR and (
                (D1st <= self.gCAttr.ExReg <= Dnth)
                or (A1st <= self.gCAttr.ExReg <= Anth)
            ):
                self.WithCAttr[self.WithLevel].Cat.set_from(self.gCAttr)
            else:
                lCAttr = CAttr()
                self.GetTemp(lCAttr, 4)
                self.WithCAttr[self.WithLevel].Cat.set_from(lCAttr)
                reg_a = self.LoadAddress(self.gCAttr.copy())
                self.gCAttr.cKind = CAttrKind.EXPR
                self.gCAttr.ExReg = reg_a
                self.Store(self.gCAttr.copy(), lCAttr.copy(), LongOp)

    def Assign1248(self) -> None:
        """Emit code for 1-, 2-, 4-, or 8-byte scalar assignment (opcodes 32..35), optimizing direct loads into register variables."""
        l_size = self.Op - 31
        flippable = self.NextByte()
        if flippable != 0:
            self.Expression(self.NextByte(), -1, False)
            lCAttr = self.gCAttr.copy()
            self.Expression(self.NextByte(), -1, False)
            self.Store(lCAttr.copy(), self.gCAttr.copy(), l_size)
        else:
            self.Expression(self.NextByte(), -1, False)
            lCAttr = self.gCAttr.copy()
            if lCAttr.cKind == CAttrKind.EXPR:
                ex_reg = lCAttr.ExReg
                self.Expression(self.NextByte(), ex_reg, False)
                if self.gCAttr.cKind != CAttrKind.EXPR or ex_reg != self.gCAttr.ExReg:
                    lCAttr = self.gCAttr.copy()
                    self.LoadAOrd(ex_reg, lCAttr, l_size)
            else:
                self.Expression(self.NextByte(), -1, False)
                self.Store(self.gCAttr.copy(), lCAttr.copy(), l_size)

    def AddToSubFrom(self, fOp: int) -> None:
        """Generate in-place ADDTO (41) or SUBFROM (42) using ADDQ/SUBQ, ADDI/SUBI, or register-to-memory ADD/SUB."""
        l_bytes = self.NextByte()
        imm_flag = False
        free_d_flag = False
        free_lhs = False
        add_quick = False
        imm_val_lo = 0
        imm_val_hi = 0
        reg_d = -1
        lhs_reg = -1
        if l_bytes == 2:
            l_size = WordOp
        else:
            l_size = LongOp
        self.Expression(self.NextByte(), -1, False)
        lCAttr = self.gCAttr.copy()
        self.Expression(self.NextByte(), -1, False)

        # optimize ADDI.L #d,<ea> to MOVEQ #d,Di / ADD.L Di,<ea> where -128 <= d <= 127
        if self.gCAttr.cKind == CAttrKind.CNST:
            cv = self.gCAttr.CValu
            add_quick = (cv.IValu[1] > 0) and (cv.IValu[0] == 0) and (cv.IValu[1] <= 8)
            if (l_size == LongOp and self.IsQuickCnst(cv)) and not add_quick:
                reg_d = self.LoadInt(cv.IValu[0], cv.IValu[1], LongOp)
                self.gCAttr.cKind = CAttrKind.EXPR
                self.gCAttr.ExReg = reg_d

        if self.gCAttr.cKind == CAttrKind.CNST:
            if add_quick:
                if fOp == 41:  # ADDTO
                    l_op = i16(0x5040)  # ADDQ.W
                else:
                    l_op = i16(0x5140)  # SUBQ.W
                l_op = i16(l_op + pmod(self.gCAttr.CValu.IValu[1], 8) * 512)
            elif lCAttr.cKind == CAttrKind.EXPR:  # LHS is a register
                if fOp == 41:  # ADDTO
                    l_op = i16(0xD000)  # ADD
                else:
                    l_op = i16(0x9000)  # SUB
                free_lhs = True
                lhs_reg = lCAttr.ExReg
                lCAttr = self.gCAttr.copy()
                if lhs_reg <= D7:
                    l_op = i16(l_op + (0x40 + lhs_reg * 512))
                    if l_size == LongOp:
                        l_op = i16(l_op + 0x40)  # .L
                else:
                    l_op = i16(l_op + (0xC0 + (lhs_reg - 8) * 512))
                    if l_size == LongOp:
                        if (
                            self.gCAttr.CValu.IValu[0] == 0
                            or self.gCAttr.CValu.IValu[0] == -1
                        ):
                            l_size = WordOp
                        else:
                            l_op = i16(l_op + 0x100)  # .L
            else:  # lhs a variable
                if fOp == 41:  # ADDTO
                    l_op = i16(0x0640)  # ADDI.W
                else:
                    l_op = i16(0x0440)  # SUBI.W
                imm_flag = True
                imm_val_lo = self.gCAttr.CValu.IValu[1]
                imm_val_hi = self.gCAttr.CValu.IValu[0]
        else:
            if lCAttr.cKind == CAttrKind.EXPR:  # LHS is a register
                if fOp == 41:  # ADDTO
                    l_op = i16(0xD000)  # ADD
                else:
                    l_op = i16(0x9000)  # SUB
                free_lhs = True
                lhs_reg = lCAttr.ExReg
                lCAttr = self.gCAttr.copy()
                if lhs_reg <= D7:
                    l_op = i16(l_op + (0x40 + lhs_reg * 512))
                    if l_size == LongOp:
                        l_op = i16(l_op + 0x40)  # .L
                else:
                    l_op = i16(l_op + (0xC0 + (lhs_reg - 8) * 512))
                    if l_size == LongOp:
                        l_op = i16(l_op + 0x100)  # .L
            else:  # lhs a variable
                free_d_flag = True
                reg_d = self.LoadD(self.gCAttr, l_size, False)
                if fOp == 41:  # ADDTO
                    l_op = i16(0xD140)  # ADD.W D,<ea>
                else:
                    l_op = i16(0x9140)  # SUB.W D,<ea>
                l_op = i16(l_op + reg_d * 512)

        if l_size == LongOp and not free_lhs:
            l_op = i16(l_op + 64)
        self.GenEffAddr(l_op, lCAttr.copy(), l_size, imm_flag, imm_val_hi, imm_val_lo)
        if free_d_flag:
            self.FreeReg(reg_d)
        if free_lhs:
            self.FreeReg(lhs_reg)

    def CopyLong(
        self, FromCAttr: CAttr, TocAttr: CAttr, fBytes: int, Tst: bool
    ) -> None:
        """Copy fBytes between aggregate operands using unrolled MOVE.L (An)+,(Am)+ (<= 16 bytes) or a counted loop."""
        reg_a = self.LoadAddress(TocAttr.copy())
        reg_a2 = self.LoadAddress(FromCAttr.copy())
        reg_a = self.CheckClobber(reg_a)
        reg_a2 = self.CheckClobber(reg_a2)
        if Tst:
            if not self.MacFlag:
                self.GenR(i16(0x4A10), reg_a2)  # TST.B (a)
        l_words = pdiv(fBytes, 2)
        if l_words <= 8:
            while l_words >= 2:
                self.GenRR(i16(0x20D8), reg_a, reg_a2)  # MOVE.L (A2)+,(A)+
                l_words -= 2
        else:
            reg_d = self.LoadInt(0, pdiv(l_words, 2), WordOp)
            self.GenRR(i16(0x20D8), reg_a, reg_a2)  # MOVE.L (A2)+,(A)+
            self.GenR(i16(0x5340), reg_d)  # SUBQ.W #1,D
            self.Gen(i16(0x6EFA))  # BGT $-6
            self.FreeReg(reg_d)
            l_words = pmod(l_words, 2)
        if l_words > 0:
            self.GenRR(i16(0x3090), reg_a, reg_a2)  # MOVE.W (A2),(A)
        self.FreeReg(reg_a)
        self.FreeReg(reg_a2)

    def AssignLong(self, fBytes: int, Tst: bool) -> None:
        """Evaluate destination and source aggregate expressions and copy fBytes via CopyLong."""
        self.Expression(self.NextByte(), -1, False)
        lCAttr = self.gCAttr.copy()
        self.Expression(self.NextByte(), -1, False)
        self.CopyLong(self.gCAttr, lCAttr, fBytes, Tst)

    def AssignSet(self) -> None:
        """Generate set assignment (opcode 37) from a stack-evaluated, memory, or immediate set expression."""
        set_size = self.NextByte()
        self.Expression(self.NextByte(), -1, False)
        lCAttr = self.gCAttr.copy()
        on_stack = self.SetExpression(self.NextByte())
        if on_stack:
            self.Gen(i16(0x548F))  # ADDQ.L #2,SP
            if set_size == 1:
                reg_d = self.GetReg(Dlow, Dhigh)
                self.GenR(i16(0x301F), reg_d)  # MOVE.W (SP)+,d
                self.gCAttr.cKind = CAttrKind.EXPR
                self.gCAttr.ExReg = reg_d
                self.Store(self.gCAttr.copy(), lCAttr.copy(), ByteOp)
            elif set_size <= 4:
                self.gCAttr.cKind = CAttrKind.STCK
                if set_size <= 2:
                    l_size = WordOp
                else:
                    l_size = LongOp
                self.Store(self.gCAttr.copy(), lCAttr.copy(), l_size)
            else:
                reg_a = self.LoadAddress(lCAttr.copy())
                reg_a = self.CheckClobber(reg_a)
                reg_d = self.LoadInt(0, pdiv(set_size, 2), WordOp)
                self.GenRR(i16(0x30DF), reg_a, 0)  # MOVE.W (SP)+,(A)+
                self.GenR(i16(0x5340), reg_d)  # SUBQ.W #1,D
                self.Gen(i16(0x6EFA))  # BGT $-6
                self.FreeReg(reg_a)
                self.FreeReg(reg_d)
        elif set_size > 4:
            if self.gCAttr.cKind == CAttrKind.CNST:
                self.gCAttr.CValu.FrontAddress = True
            self.CopyLong(self.gCAttr, lCAttr, set_size, False)
        else:
            if set_size == 1:
                l_size = ByteOp
            elif set_size == 2:
                l_size = WordOp
            else:
                l_size = LongOp
            if self.gCAttr.cKind == CAttrKind.CNST:
                self.MakeSetConst(self.gCAttr)
            self.Store(self.gCAttr.copy(), lCAttr.copy(), l_size)

    def AssignPacked(self) -> None:
        """Emit bit-masking and shifting instructions to store into a packed array element or packed record field."""
        l_op = self.NextByte()
        if l_op == 21:  # PCKDARR
            add_flag = False
            num_bits = self.NextByte()
            lo = self.NextWord()
            self.Expression(self.NextByte(), -1, False)
            lCAttr = self.gCAttr.copy()
            self.Expression(self.NextByte(), -1, False)
            reg_d = self.LoadD(self.gCAttr, WordOp, False)
            reg_d = self.CheckClobber(reg_d)
            if lCAttr.cKind == CAttrKind.ADDR:
                reg_a = lCAttr.AdReg
                l_offset = lCAttr.AOffset
                lCAttr.cKind = CAttrKind.INDX
                lCAttr.InOffset = l_offset
                lCAttr.InxRReg = reg_d
                lCAttr.InxAReg = reg_a
                lCAttr.LongIndex = False
            elif lCAttr.cKind == CAttrKind.INDX:
                add_flag = True
            elif lCAttr.cKind == CAttrKind.VARB:
                if lCAttr.VLev < 0:
                    lCAttr.InxAReg = self.LoadAddress(lCAttr.copy())
                    lCAttr.cKind = CAttrKind.INDX
                    lCAttr.InxRReg = reg_d
                    lCAttr.LongIndex = False
                    lCAttr.InOffset = 0
                else:
                    l_offset = lCAttr.VOffset
                    reg_a = self.GetBase(lCAttr.VLev)
                    lCAttr.cKind = CAttrKind.INDX
                    lCAttr.InxAReg = reg_a
                    lCAttr.InxRReg = reg_d
                    lCAttr.InOffset = l_offset
                    lCAttr.LongIndex = False
            self.Expression(self.NextByte(), -1, False)
            if num_bits == 8:
                if add_flag:
                    self.GenRR(i16(0xD040), reg_d, lCAttr.InxRReg)  # ADD.W inxrreg,D
                    self.FreeReg(lCAttr.InxRReg)
                    lCAttr.InxRReg = reg_d
                self.IncOffset(lCAttr, i16(-lo))
                self.Store(self.gCAttr.copy(), lCAttr.copy(), ByteOp)
            else:
                reg_d3 = self.LoadD(self.gCAttr, ByteOp, False)
                reg_d3 = self.CheckClobber(reg_d3)
                if lo != 0:
                    if abs(lo) <= 8:
                        if lo > 0:
                            self.GenRR(i16(0x5140), lo, reg_d)  # SUBQ.W #lo,D
                        else:
                            self.GenRR(i16(0x5040), -lo, reg_d)  # ADDQ.W #-lo,D
                    else:
                        self.GenR(i16(0x0440), reg_d)
                        self.Gen(i16(lo))  # SUBI.W #lo,D
                data_mask = 0
                for _ in range(1, num_bits + 1):
                    data_mask = i16(data_mask * 2 + 1)
                shift_count = 0
                while num_bits < 8:
                    num_bits = i16(num_bits * 2)
                    shift_count += 1
                addr_mask = 0
                for _ in range(1, shift_count + 1):
                    addr_mask = i16(addr_mask * 2 + 1)
                self.GenR(i16(0x0240), reg_d3)
                self.Gen(data_mask)  # ANDI.W #datamask,D3
                reg_d2 = self.GetReg(Dlow, Dhigh)
                self.GenRR(i16(0x3000), reg_d2, reg_d)  # MOVE.W D,D2
                self.GenR(i16(0x0240), reg_d2)
                self.Gen(addr_mask)  # ANDI.W #addrmask,D2
                if shift_count < 3:
                    self.GenRR(i16(0xE148), 3 - shift_count, reg_d2)  # LSL.W #3-sc,D2
                self.GenRR(i16(0xE048), shift_count, reg_d)  # LSR.W #sc,D
                if add_flag:
                    reg_d = self.CheckClobber(reg_d)
                    self.GenRR(i16(0xD040), reg_d, lCAttr.InxRReg)  # ADD.W inxrreg,D
                    self.FreeReg(lCAttr.InxRReg)
                    lCAttr.InxRReg = reg_d
                reg_a = self.LoadAddress(lCAttr.copy())
                reg_d = self.LoadInt(-1, i16(-data_mask - 1), ByteOp)  # MOVEQ #~datamask,D
                self.GenRR(i16(0xE138), reg_d2, reg_d)  # ROL.B D2,D
                self.GenRR(i16(0xE128), reg_d2, reg_d3)  # LSL.B D2,D3
                self.GenRR(i16(0xC110), reg_d, reg_a)  # AND.B D,(A)
                self.GenRR(i16(0x8110), reg_d3, reg_a)  # OR.B D3,(A)
                self.FreeReg(reg_a)
                self.FreeReg(reg_d2)
                self.FreeReg(reg_d3)
                self.FreeReg(reg_d)
        else:
            # 62 = UPCKFLD, 63 = SPCKFLD
            rightbit = self.NextByte()
            num_bits = pdiv(rightbit, 16)
            rightbit = pmod(rightbit, 16)
            data_mask = 0
            for _ in range(1, num_bits + 1):
                data_mask = i16(data_mask * 2 + 1)
            self.Expression(self.NextByte(), -1, False)
            lCAttr = self.gCAttr.copy()
            self.Expression(self.NextByte(), -1, False)
            if (rightbit == 8 or rightbit == 0) and num_bits == 8:
                if rightbit == 0:
                    self.IncOffset(lCAttr, 1)
                if self.gCAttr.cKind in (
                    CAttrKind.EXPR,
                    CAttrKind.ADDR,
                    CAttrKind.INDX,
                    CAttrKind.VARB,
                ):
                    self.IncOffset(self.gCAttr, 1)
                else:
                    _ = self.LoadD(self.gCAttr, WordOp, False)
                self.Store(self.gCAttr.copy(), lCAttr.copy(), ByteOp)
            else:
                if self.gCAttr.cKind == CAttrKind.CNST:
                    bit = 1
                    for _ in range(1, num_bits + 1):
                        bit = i16(bit + bit)
                    l_value = i16(self.gCAttr.CValu.IValu[1])
                    if l_value >= 0:
                        l_value = i16(pmod(l_value, bit))
                    else:
                        l_value = i16(l_value + bit)
                    for _ in range(1, rightbit + 1):
                        l_value = i16(l_value + l_value)
                        data_mask = i16(data_mask + data_mask)
                    if l_value == 0:
                        if lCAttr.cKind == CAttrKind.EXPR:
                            lCAttr.ExReg = self.CheckClobber(lCAttr.ExReg)
                        self.GenEffAddr(
                            i16(0x0240), lCAttr.copy(), WordOp, True, 0, i16(-data_mask - 1)
                        )
                    else:
                        reg_a = self.LoadAddress(lCAttr.copy())
                        self.GenR(i16(0x0250), reg_a)
                        self.Gen(i16(-data_mask - 1))  # ANDI.W #~dm,(A)
                        self.GenR(i16(0x0050), reg_a)
                        self.Gen(l_value)  # ORI.W #lval,(A)
                        self.FreeReg(reg_a)
                else:
                    if EMITDEPOSIT:
                        self.PushAddress(lCAttr.copy())
                        reg_d = self.LoadD(self.gCAttr, WordOp, False)
                        self.Gen(
                            i16(
                                i16(0xA080)
                                + pmod(num_bits, 16) * 0x100
                                + reg_d * 0x10
                                + rightbit
                            )
                        )
                        self.FreeReg(reg_d)
                    else:
                        if rightbit > 7:
                            rightbit = i16(rightbit - 8)
                            m_op = i16(0x0210)  # ANDI.B #x,(A)
                            l_op = i16(0x8110)  # OR.B D,(A)
                        else:
                            l_op = i16(0x8150)  # OR.W D,(A)
                            m_op = i16(0x0250)  # ANDI.W #x,(A)
                        reg_a = self.LoadAddress(lCAttr.copy())
                        reg_d = self.LoadD(self.gCAttr, WordOp, False)
                        reg_d = self.CheckClobber(reg_d)
                        self.GenR(i16(0x0240), reg_d)
                        self.Gen(data_mask)  # ANDI.W #mask,D
                        if rightbit > 0:
                            self.GenRR(i16(0xE148), rightbit, reg_d)  # LSL.W #rb,D
                        for _ in range(1, rightbit + 1):
                            data_mask = i16(data_mask * 2)
                        self.GenR(m_op, reg_a)
                        self.Gen(i16(-data_mask - 1))  # ANDI.? #~dm,(A)
                        self.GenRR(l_op, reg_d, reg_a)  # OR.? D,(A)
                        self.FreeReg(reg_d)
                        self.FreeReg(reg_a)

    def AssignString(self) -> None:
        """Assign a Pascal string value, folding short string constants (<= 3 chars) into immediate scalar stores."""
        l_bytes = self.NextByte()
        if l_bytes > 3:
            l_bytes += 1
            if odd(l_bytes):
                l_bytes += 1
            self.AssignLong(l_bytes, False)
        else:
            self.Expression(self.NextByte(), -1, False)
            lCAttr = self.gCAttr.copy()
            self.Expression(self.NextByte(), -1, False)
            if l_bytes == 0:
                l_size = ByteOp
            elif l_bytes == 1:
                l_size = WordOp
            else:
                l_size = LongOp
            if self.gCAttr.cKind == CAttrKind.CNST:
                l_str = '        '
                if self.gCAttr.CValu.StrValu is not None:
                    l_str = alfa8(self.gCAttr.CValu.StrValu.StrVal)
                if self.gCAttr.CValu.CstKind in (ConstKind.STRCNST, ConstKind.PAOCCNST):
                    self.gCAttr.CValu.IValu[0] = i16(self.gCAttr.CValu.Len)
                self.gCAttr.CValu.CstKind = ConstKind.SCALCNST
                self.gCAttr.CValu.IValu[1] = 0
                if l_bytes > 0:
                    self.gCAttr.CValu.IValu[1] = i16(l_bytes * 256 + (ord(l_str[0]) & 0xFF))
                    if l_bytes > 1:
                        self.gCAttr.CValu.IValu[0] = self.gCAttr.CValu.IValu[1]
                        self.gCAttr.CValu.IValu[1] = i16(
                            (ord(l_str[1]) & 0xFF) * 256 + (ord(l_str[2]) & 0xFF)
                        )
            self.Store(self.gCAttr.copy(), lCAttr.copy(), l_size)

    def AssignAlfa(self) -> None:
        """Assign a PACKED ARRAY OF CHAR value, folding constants up to 4 characters into a single scalar store."""
        l_bytes = self.NextByte()
        m_bytes = self.NextByte()
        if l_bytes != m_bytes:
            self.CodError(2010)
        if l_bytes > 4:
            if odd(l_bytes):
                l_bytes += 1
            self.AssignLong(l_bytes, False)
        else:
            self.Expression(self.NextByte(), -1, False)
            lCAttr = self.gCAttr.copy()
            self.Expression(self.NextByte(), -1, False)
            if l_bytes == 1:
                l_size = ByteOp
            elif l_bytes == 2:
                l_size = WordOp
            else:
                l_size = LongOp
            if self.gCAttr.cKind == CAttrKind.CNST:
                l_str = '        '
                if self.gCAttr.CValu.StrValu is not None:
                    l_str = alfa8(self.gCAttr.CValu.StrValu.StrVal)
                if self.gCAttr.CValu.CstKind in (ConstKind.STRCNST, ConstKind.PAOCCNST):
                    self.gCAttr.CValu.IValu[0] = i16(self.gCAttr.CValu.Len)
                self.gCAttr.CValu.CstKind = ConstKind.SCALCNST
                self.gCAttr.CValu.IValu[1] = i16(
                    (ord(l_str[0]) & 0xFF) * 256 + (ord(l_str[1]) & 0xFF)
                )
                if l_bytes > 2:
                    self.gCAttr.CValu.IValu[0] = self.gCAttr.CValu.IValu[1]
                    self.gCAttr.CValu.IValu[1] = i16(
                        (ord(l_str[2]) & 0xFF) * 256 + (ord(l_str[3]) & 0xFF)
                    )
            self.Store(self.gCAttr.copy(), lCAttr.copy(), l_size)

    def StdProcCall(self) -> None:
        """Emit a JSR to the runtime support routine implementing a standard Pascal or I/O procedure."""
        l_op = self.NextByte()
        if l_op < 100:
            tbl_lo = {
                1: '%_NEW   ',
                2: '%_MARK  ',
                3: '%_RELSE ',
                4: '%_GET   ',
                5: '%_PUT   ',
                6: '%_RESET ',
                7: '%_REWRT ',
                12: '%_PAGE  ',
                15: '%_CLOSE ',
                16: '%_DEL   ',
                17: '%_INS   ',
                18: '%_UREAD ',
                19: '%_UWRIT ',
                20: '%_SEEK  ',
                21: '%_HALT  ',
                22: '%_MOVEL ',
                23: '%_MOVER ',
                24: '%_FILLC ',
                25: '%_UCLR  ',
                26: '%_GOTOXY',
                27: '%_DISP  ',
                28: '%_UNITST',
            }
            name = tbl_lo.get(l_op)
            if name is not None:
                self.GenJSR(name)
        else:
            tbl_hi = {
                100: '%W_C    ',
                101: '%W_B    ',
                102: '%W_I    ',
                103: '%W_E    ',
                104: '%W_F    ',
                105: '%W_STR  ',
                106: '%W_PAOC ',
                107: '%W_LN   ',
                110: '%R_C    ',
                111: '%R_I    ',
                112: '%R_R    ',
                113: '%R_STR  ',
                114: '%R_PAOC ',
                115: '%R_LN   ',
            }
            name = tbl_hi.get(l_op)
            if name is not None:
                self.GenJSR(name)
        if 110 <= l_op <= 112:
            self.gCAttr.cKind = CAttrKind.STCK
            if l_op == 110:
                reg_d = self.GetReg(Dlow, Dhigh)
                self.GenR(i16(0x4240), reg_d)  # CLR.W D
                self.GenRR(i16(0x101F), reg_d, 0)  # MOVE.B (SP)+,D
                self.gCAttr.cKind = CAttrKind.EXPR
                self.gCAttr.ExReg = reg_d

    def StdFuncCall(self) -> None:
        """Emit a JSR to the runtime support routine implementing a standard Pascal intrinsic function."""
        l_op = self.NextByte()
        if l_op in (21, 22):  # CONCAT, COPY
            if l_op == 21:
                self.GenJSR('%_CAT   ')
            else:
                self.GenJSR('%_COPY  ')
            self.Expression(self.NextByte(), -1, False)
            self.FCAllInfo[self.FCAllLevel].OnStack = False
        else:
            tbl = {
                2: '%_ATAN  ',
                4: '%_COS   ',
                5: '%_EOF   ',
                6: '%_EOLN  ',
                7: '%_EXP   ',
                8: '%_LN    ',
                12: '%_ROUND ',
                13: '%_SIN   ',
                15: '%_SQRT  ',
                17: '%_TRUNC ',
                20: '%_POS   ',
                23: '%_BLKRD ',
                24: '%_BLKWR ',
                25: '%_IORES ',
                27: '%_PWR10 ',
                28: '%_SCANE ',
                29: '%_SCANN ',
                30: '%_UBUSY ',
                31: '%_MEMAV ',
                33: '%_HEAPRE',
                34: '%_KEYPRE',
            }
            name = tbl.get(l_op)
            if name is not None:
                self.GenJSR(name)
        if l_op in (
            2, 4, 5, 6, 7, 8, 12, 13, 15, 17, 20,
            23, 24, 25, 27, 28, 29, 30, 31, 33, 34,
        ):
            self.gCAttr.cKind = CAttrKind.STCK

    def JumpILabel(self) -> None:
        """Emit an unconditional BRA (JUMP) or condition-code branch (FJUMP/TJUMP) to an internal label."""
        l_op = self.Op
        l_lab = self.NextWord()
        if l_op == 193:  # JUMP
            l_op = i16(0x6000)
        else:
            self.Expression(self.NextByte(), -1, False)
            if l_op == 194:  # FJUMP
                if self.gCAttr.cKind == CAttrKind.COND:
                    fjump_map = {
                        GCondition.LT: 0x6C00,  # BGE
                        GCondition.LE: 0x6E00,  # BGT
                        GCondition.GT: 0x6F00,  # BLE
                        GCondition.GE: 0x6D00,  # BLT
                        GCondition.EQ: 0x6600,  # BNE
                        GCondition.NE: 0x6700,  # BEQ
                        GCondition.HI: 0x6300,  # BLS
                        GCondition.LS: 0x6200,  # BHI
                    }
                    l_op = i16(fjump_map[self.gCAttr.CC])
                else:
                    if self.gCAttr.cKind == CAttrKind.BOOL:
                        reg_d = self.gCAttr.ExReg
                    else:
                        reg_d = self.LoadD(self.gCAttr, ByteOp, True)
                    self.FreeReg(reg_d)
                    l_op = i16(0x6700)  # BEQ
            elif self.gCAttr.cKind == CAttrKind.COND:  # TJUMP
                tjump_map = {
                    GCondition.LT: 0x6D00,  # BLT
                    GCondition.LE: 0x6F00,  # BLE
                    GCondition.GT: 0x6E00,  # BGT
                    GCondition.GE: 0x6C00,  # BGE
                    GCondition.EQ: 0x6700,  # BEQ
                    GCondition.NE: 0x6600,  # BNE
                    GCondition.HI: 0x6200,  # BHI
                    GCondition.LS: 0x6300,  # BLS
                }
                l_op = i16(tjump_map[self.gCAttr.CC])
            else:
                if self.gCAttr.cKind == CAttrKind.BOOL:
                    reg_d = self.gCAttr.ExReg
                else:
                    reg_d = self.LoadD(self.gCAttr, ByteOp, True)
                self.FreeReg(reg_d)
                l_op = i16(0x6600)  # BNE
        self.GenJump(l_op, l_lab)

    def GenCall(self) -> None:
        """Process a call parameter-and-invocation sequence for user, standard, procedural-param, C, INLINE, or Clascal method calls."""
        def fct_end() -> None:
            """Pop or mark the function return value and restore caller-saved registers at the end of a call."""
            info = self.FCAllInfo[self.FCAllLevel]
            if info.OnStack:
                if info.RegMask == 0:
                    self.gCAttr.cKind = CAttrKind.STCK
                else:
                    d_reg = self.GetReg(Dlow, Dhigh)
                    if info.Size == 1:
                        self.GenRR(i16(0x101F), d_reg, 0)  # MOVE.B (SP)+,D
                    elif info.Size == 2:
                        self.GenRR(i16(0x301F), d_reg, 0)  # MOVE.W (SP)+,D
                    else:
                        self.GenRR(i16(0x201F), d_reg, 0)  # MOVE.L (SP)+,D
                    self.gCAttr.cKind = CAttrKind.EXPR
                    self.gCAttr.ExReg = d_reg
            if info.RegMask != 0:
                self.RestoreRegs(info.RegMask)
            self.FCAllLevel -= 1

        exit_flag = False
        while not exit_flag:
            self.Op = self.NextByte()
            op = self.Op
            if op in (176, 177):  # UFCALL, UPCALL
                n = self.NextWord()
                up = self.UserProcs[n]
                assert up is not None
                if up.PFLev > 2:
                    if up.PFLev == self.ProcLvl + 1:
                        self.Gen(i16(0x2F0E))  # MOVE.L A6,-(SP)
                    else:
                        base = self.GetBase(up.PFLev)
                        self.FreeReg(base)
                        self.GenR(i16(0x2F28), base)
                        self.Gen(8)  # MOVE.L 8(base),-(SP)
                self.GenJSR(up.LinkName)
                if self.Op == 176:
                    fct_end()
                exit_flag = True
            elif op == 178:  # SFCALL
                self.StdFuncCall()
                fct_end()
                exit_flag = True
            elif op == 179:  # SPCALL
                self.StdProcCall()
                exit_flag = True
            elif op in (180, 181):  # PFCALL, PPCALL
                self.Expression(self.NextByte(), -1, False)
                reg_a = self.LoadAddress(self.gCAttr.copy())
                reg_a = self.CheckClobber(reg_a)
                reg_d = self.GetReg(Dlow, Dhigh)
                self.GenRR(i16(0x2018), reg_a, reg_d)  # MOVE.L (A)+,D
                self.Gen(26370)  # BEQ.S $+4
                self.GenR(i16(0x2F00), reg_d)  # MOVE.L D,-(SP)
                self.GenRR(i16(0x2050), reg_a, reg_a)  # MOVE.L (A),A
                self.GenR(i16(0x4E90), reg_a)  # JSR (A)
                self.FreeReg(reg_a)
                self.FreeReg(reg_d)
                if self.Op == 180:
                    fct_end()
                exit_flag = True
            elif op == 182:  # FCTRSLT
                n = self.NextByte()
                self.FCAllLevel += 1
                info = self.FCAllInfo[self.FCAllLevel]
                info.Size = pmod(n, 16)
                info.RegMask = self.SaveRegs()
                info.OnStack = True
                if 0 < n < 16:
                    if n <= 2:
                        self.Gen(i16(0x4267))  # CLR.W -(SP)
                    else:
                        self.Gen(i16(0x42A7))  # CLR.L -(SP)
            elif op in (183, 188):  # REFPARM, VPRMBIG
                if self.Op == 188:
                    _l_size = self.NextWord()
                l_op = self.NextByte()
                if l_op == 12:  # UPARROW
                    self.Expression(self.NextByte(), -1, False)
                    self.PushValue(self.gCAttr.copy(), LongOp)
                else:
                    self.Expression(l_op, -1, False)
                    self.PushAddress(self.gCAttr.copy())
            elif op in (184, 185, 186, 187):  # VPARM1..8
                l_size = self.Op - 183
                self.Expression(self.NextByte(), -1, False)
                self.PushValue(self.gCAttr.copy(), l_size)
            elif op == 189:  # SETVPRM
                set_size = self.NextByte()
                on_stack = self.SetExpression(self.NextByte())
                if not on_stack:
                    self.PushSet(self.gCAttr.copy(), set_size, False)
                else:
                    self.Gen(i16(0x548F))  # ADDQ.L #2,SP
            elif op == 190:  # BEGCALL
                self.GenCall()
            elif op == 191:  # PFPARM
                n = self.NextWord()
                up = self.UserProcs[n]
                assert up is not None
                self.GlobRef(up.LinkName, up.UserName, i16(self.Ic + 2))
                if self.ShortCalls:
                    self.Gen(i16(0x487A))  # PEA $+xxx
                else:
                    self.Gen(i16(0x4879))
                    self.Gen(0)  # PEA xxx.L
                self.Gen(0)
                if up.PFLev > 2:
                    if up.PFLev == self.ProcLvl + 1:
                        self.Gen(i16(0x2F0E))  # MOVE.L A6,-(SP)
                    else:
                        base = self.GetBase(up.PFLev)
                        self.FreeReg(base)
                        self.GenR(i16(0x2F28), base)
                        self.Gen(8)  # MOVE.L 8(base),-(SP)
                else:
                    self.Gen(i16(0x42A7))  # CLR.L -(SP)
            elif op == 241:  # EXTREF
                self.ExtRef()
                self.CodError(2007)
            elif op == 251:  # CCALL
                l_reg_mask = self.SaveRegs()
                l_size = self.NextByte()
                proc_idx = self.NextWord()
                up = self.UserProcs[proc_idx]
                assert up is not None
                self.GenJSR(up.LinkName)
                n = self.NextWord()
                if n <= 8:
                    self.GenRR(i16(0x508F), pmod(n, 8), 0)  # ADDQ.L #N,SP
                else:
                    self.Gen(i16(0x4FEF))
                    self.Gen(i16(n))  # LEA #N(SP),SP
                if l_size > 0:
                    if l_size == 4:
                        reg_d = self.GetReg(Dlow, Dhigh)
                        if reg_d != D0:
                            self.GenRR(i16(0x2000), reg_d, D0)  # MOVE.L D0,D
                        self.gCAttr.cKind = CAttrKind.EXPR
                        self.gCAttr.ExReg = reg_d
                    else:
                        if not self.HaveExtTmp:
                            self.GetTemp(self.ExtTmp, 10)
                            self.HaveExtTmp = True
                        if not self.HaveDblTmp:
                            self.GetTemp(self.DblTmp, 8)
                            self.HaveDblTmp = True
                        if self.DblTmp.VLev <= 1:
                            l_op = i16(0x2B40)  # MOVE.L D0,DblTmp(A5)
                        else:
                            l_op = i16(0x2D40)  # MOVE.L D0,DblTmp(A6)
                        self.Gen(l_op)
                        self.Gen(i16(self.DblTmp.VOffset))
                        self.Gen(i16(l_op + 1))
                        self.Gen(i16(self.DblTmp.VOffset + 4))
                        self.PushAddress(self.DblTmp.copy())
                        self.PushAddress(self.ExtTmp.copy())
                        self.Gen(i16(0x3F3C))
                        self.Gen(i16(0x080E))  # MOVE.W #FFDBL+FOZ2X,-(SP)
                        if self.MacFlag:
                            self.Gen(i16(0xA9EB))  # _FP68K trap
                        else:
                            self.GenJSR('FP68K   ')
                        lCAttr = CAttr()
                        self.GetTemp(lCAttr, 4)
                        self.PushAddress(self.ExtTmp.copy())
                        self.PushAddress(lCAttr.copy())
                        self.Gen(i16(0x3F3C))
                        self.Gen(i16(0x1010))  # MOVE.W #FFSGL+FOX2Z,-(SP)
                        if self.MacFlag:
                            self.Gen(i16(0xA9EB))  # _FP68K trap
                        else:
                            self.GenJSR('FP68K   ')
                        self.gCAttr.set_from(lCAttr)
                if l_reg_mask != 0:
                    self.RestoreRegs(l_reg_mask)
                exit_flag = True
            elif op == 252:  # INLINE
                is_funct = self.NextByte() == 1
                cnt = self.NextWord()
                for _ in range(1, cnt + 1):
                    self.Gen(self.NextWord())
                    self.pLineNumber[self.CurrCode] = -self.LNum
                if is_funct:
                    fct_end()
                exit_flag = True
            elif op == 253:  # METHCALL
                is_funct = self.NextByte() == 1
                self.GenR(i16(0x4E90), A5)
                self.Gen(self.NextWord())
                if is_funct:
                    fct_end()
                exit_flag = True

    def ForStmt(self) -> None:
        """Generate FOR-loop initialization, body, ADDQ/SUBQ step, BVS boundary overflow guard, and limit test."""
        n = self.NextByte()
        if n == 1:
            l_size = ByteOp
        elif n == 2:
            l_size = WordOp
        else:
            l_size = LongOp
        self.Expression(self.NextByte(), -1, False)
        var_cattr = self.gCAttr.copy()
        self.Expression(self.NextByte(), -1, False)
        init_cattr = self.gCAttr.copy()
        self.Expression(self.NextByte(), -1, False)
        if self.gCAttr.cKind == CAttrKind.CNST:
            limit_cattr = self.gCAttr.copy()
        else:
            limit_cattr = CAttr()
            self.GetTemp(limit_cattr, n)
            self.Store(self.gCAttr.copy(), limit_cattr.copy(), l_size)
        self.Expression(self.NextByte(), -1, False)
        if self.gCAttr.cKind == CAttrKind.CNST:
            step_cattr = self.gCAttr.copy()
        else:
            step_cattr = CAttr()
            self.GetTemp(step_cattr, n)
            self.Store(self.gCAttr.copy(), step_cattr.copy(), l_size)
        self.Store(init_cattr.copy(), var_cattr.copy(), l_size)
        top_label = self.NewLabel()
        bottom_label = self.NewLabel()
        exit_label = self.NewLabel()
        self.GenJump(i16(0x6000), bottom_label)
        self.DefILabel(top_label)
        self.StmtList(203)  # FOREND
        if step_cattr.cKind == CAttrKind.CNST:
            if step_cattr.CValu.IValu[1] > 0:
                l_op = i16(0x5200)  # ADDQ
            else:
                l_op = i16(0x5300)  # SUBQ
            if l_size == WordOp:
                l_op = i16(l_op + 64)
            elif l_size == LongOp:
                l_op = i16(l_op + 128)
            self.GenEffAddr(l_op, var_cattr.copy(), l_size, False, 0, 0)
            over_flag = True
            if limit_cattr.cKind == CAttrKind.CNST:
                if step_cattr.CValu.IValu[1] > 0:
                    if l_size == ByteOp:
                        over_flag = limit_cattr.CValu.IValu[1] >= 127
                    elif l_size == WordOp:
                        over_flag = limit_cattr.CValu.IValu[1] >= 32767
                    else:
                        over_flag = ValuLInt(limit_cattr.CValu) >= 2147483647
                elif l_size == ByteOp:
                    over_flag = limit_cattr.CValu.IValu[1] <= -128
                elif l_size == WordOp:
                    over_flag = limit_cattr.CValu.IValu[1] <= -32768
                else:
                    over_flag = ValuLInt(limit_cattr.CValu) <= -2147483648
            if over_flag:
                self.GenJump(i16(0x6900), exit_label)  # BVS
            self.DefILabel(bottom_label)
            if self.GenCompare(var_cattr.copy(), limit_cattr.copy(), l_size):
                if step_cattr.CValu.IValu[1] > 0:
                    l_op = i16(0x6C00)  # BGE
                else:
                    l_op = i16(0x6F00)  # BLE
            elif step_cattr.CValu.IValu[1] > 0:
                l_op = i16(0x6F00)  # BLE
            else:
                l_op = i16(0x6C00)  # BGE
            self.GenJump(l_op, top_label)
            self.DefILabel(exit_label)
        else:
            self.CodError(2009)

    def CaseStmt(self) -> None:
        """Generate a CASE statement using either a bounds-checked PC-relative word jump table or a sequential compare chain."""
        self.Expression(self.NextByte(), -1, False)
        reg_d = self.LoadD(self.gCAttr, WordOp, True)
        _junk = self.NextByte()  # C9
        if_then_else_flag = self.NextByte()
        reg_d = self.CheckClobber(reg_d)
        lo = self.NextWord()
        hi = self.NextWord()
        else_label = self.NextWord()

        def sub_from_d(n: int) -> None:
            n = i16(n)
            if n != 0:
                if 0 < n <= 8:
                    self.GenR(i16(0x5140 + pmod(n, 8) * 512), reg_d)  # SUBQ.W #n,D
                elif -8 <= n < 0:
                    self.GenR(i16(0x5040 + pmod(-n, 8) * 512), reg_d)  # ADDQ.W #-n,D
                else:
                    self.GenR(i16(0x0440), reg_d)
                    self.Gen(n)  # SUBI.W

        if if_then_else_flag == 0:
            sub_from_d(lo)
            self.GenJump(i16(0x6B00), else_label)  # BMI
            self.GenR(i16(0x0C40), reg_d)
            self.Gen(i16(hi - lo))  # CMPI.W
            self.GenJump(i16(0x6E00), else_label)  # BGT
            self.GenR(i16(0xE348), reg_d)  # LSL.W #1
            self.GenRR(i16(0x303B), reg_d, 0)
            self.Gen(i16(reg_d * 4096 + 6))  # MOVE.W table(D.W),D
            self.Gen(i16(0x4EFB))
            self.Gen(i16(reg_d * 4096))  # JMP $(d)
            lo_ic = self.Ic
            self.FreeReg(reg_d)
            for _ in range(lo, hi + 1):
                self.GenWord(self.NextWord(), Flags.CASJ)
                self.pLineNumber[self.CurrCode] = -self.LNum
            hi_ic = self.Ic
            self.StmtList(204)  # ENDCASE
            l_ic = lo_ic
            while l_ic < hi_ic:
                idx = pdiv(l_ic, 2)
                l_lab = self.LookUpILabel(self.CodeBuff[idx])
                self.CodeBuff[idx] = l_lab.Loc
                l_ic += 2
        else:
            lv = 0
            cnt = self.NextWord()
            for _ in range(1, cnt + 1):
                v = self.NextWord()
                sub_from_d(i16(v - lv))
                self.GenJump(i16(0x6700), self.NextWord())  # BEQ
                lv = v
            self.FreeReg(reg_d)
            self.GenJump(i16(0x6000), else_label)  # BRA
            self.StmtList(204)  # ENDCASE

    def LineStmt(self) -> None:
        """Handle opcode 205 line-sync records: open compiler/output listing files, toggle $ASM+, set proc end line, or update LNum."""
        if self.ListingOk:
            i = self.NextWord()
            if i == -1:
                j = self.NextByte()
                clist_fname = ''.join(chr(self.NextByte()) for _ in range(j))

                if self.CListOpen:
                    self.rt.CloseF(self.CListFile, IOCloseKind.IONormal)
                self.CListOpen = False
                self.Listing = False
                self.ConsListing = False

                err, self.CListFile = self.rt.OpenF(
                    clist_fname, self.CListFile, IOModes.IORead, self.CListBufr
                )
                if self.rt.IOError(
                    err, f"Cannot open Compiler's listing file: {clist_fname}"
                ):
                    self.KillExec()
                    sys.stdout.write('\n')
                    sys.stdout.write('Ignore listing and continue with code generation? ')
                    if not self.rt.SUGetBool(True):
                        self.Aborted = True
                        raise AbortCompilation()
                    sys.stdout.write('\n')
                    self.FirstOnCons = False
                    if self.ListOpen:
                        self.rt.CloseF(self.ListFile, IOCloseKind.IOLock)
                    self.ListOpen = False
                    self.ListingOk = False
                else:
                    self.CListOpen = True
                    self.Listing = self.CListFile.DevType == IODevType.IOBlkDev

                if self.Listing:
                    if self.AltListing:
                        str1, str2, _str3 = self.rt.SUSplitFN(clist_fname)
                        str4, _ = self.rt.SUMakeFN(str1, str2, '')
                        if not self.FirstOnCons:
                            sys.stdout.write('\n')
                        while True:
                            sys.stdout.write('New list file - ')
                            clist_fname, what_user_typed = self.rt.SUGetFN(
                                '', str4, '.TEXT'
                            )
                            if what_user_typed == PromptState.SUEscape:
                                self.Aborted = True
                                raise AbortCompilation()
                            if what_user_typed == PromptState.SUInvalid:
                                sys.stdout.write('Bad file name\n')
                            if what_user_typed in (
                                PromptState.SUValid,
                                PromptState.SUNone,
                                PromptState.SUDefault,
                            ):
                                if self.ListOpen and self.ListFile is not None:
                                    s1 = self.rt.SUUpStr(clist_fname)
                                    s2 = self.rt.SUUpStr(self.ListFile.Filename)
                                    if s1 != s2:
                                        self.rt.CloseF(
                                            self.ListFile, IOCloseKind.IOLock
                                        )
                                        self.ListOpen = False
                                if not self.ListOpen:
                                    err2, self.ListFile = self.rt.OpenF(
                                        clist_fname,
                                        self.ListFile,
                                        IOModes.IOWrite,
                                        self.ListBufr,
                                    )
                                    if self.rt.IOError(
                                        err2, f'Cannot open listing file: {clist_fname}'
                                    ):
                                        what_user_typed = PromptState.SUInvalid
                            if what_user_typed == PromptState.SUInvalid:
                                self.KillExec()
                            if what_user_typed in (
                                PromptState.SUValid,
                                PromptState.SUNone,
                                PromptState.SUDefault,
                            ):
                                break
                        assert self.ListFile is not None
                        self.ConsListing = (
                            self.ListFile.DevType == IODevType.IOConsDev
                        )
                        self.ListOpen = True
                        sys.stdout.write('\n')
                        self.FirstOnCons = False
                    else:
                        if self.ListOpen:
                            self.rt.CloseF(self.ListFile, IOCloseKind.IOLock)
                        self.ListOpen = False
                        err2, self.ListFile = self.rt.OpenF(
                            clist_fname, self.ListFile, IOModes.IOWrite, self.ListBufr
                        )
                        if self.rt.IOError(
                            err2, f'Cannot open listing file: {clist_fname}'
                        ):
                            self.KillExec()
                            sys.stdout.write('\n')
                            sys.stdout.write(
                                'Ignore listing and continue with code generation? '
                            )
                            if not self.rt.SUGetBool(True):
                                self.Aborted = True
                                raise AbortCompilation()
                            sys.stdout.write('\n')
                            self.FirstOnCons = False
                            self.Listing = False
                            self.ConsListing = False
                            self.ListingOk = False
                        else:
                            self.ListOpen = True
                            self.ConsListing = (
                                self.ListFile.DevType == IODevType.IOConsDev
                            )
                            if not self.FirstOnCons:
                                sys.stdout.write('\n')
                            sys.stdout.write(
                                f'Listing file is {self.ListFile.Filename}\n'
                            )
                            sys.stdout.write('\n')
                            self.FirstOnCons = False

                if not self.Listing:
                    if self.ListOpen:
                        self.rt.CloseF(self.ListFile, IOCloseKind.IOLock)
                    self.ListOpen = False
                    self.ConsListing = False
                    self.rt.CloseF(self.CListFile, IOCloseKind.IONormal)
                    self.CListOpen = False
                    self.ListingOk = False
            elif i == -2:
                if self.UseAsmIcode:
                    self.ShowAsmCode = self.NextByte() == 1
                else:
                    _ = self.NextByte()
            elif i == -3:
                self.EndLineNbr = self.NextWord()
            else:
                self.LNum = i
                if i < 0:
                    self.LNum = self.LNum + 65536
                if self.FirstLNum == 0:
                    self.FirstLNum = self.LNum
                if self.LNum > MAXLNUM:
                    self.LnOvflo = True
        else:
            i = self.NextWord()
            if i == -1:
                j = self.NextByte()
                for _ in range(j):
                    _ = self.NextByte()
            elif i == -2:
                _ = self.NextByte()
            elif i == -3:
                _ = self.NextWord()

    def StmtList(self, EndOp: int) -> None:
        """Decode and emit statements from the .I stream until sentinel opcode EndOp is encountered."""
        self.Op = self.NextByte()
        while self.Op != EndOp:
            op = self.Op
            if op in (32, 33, 34, 35):
                self.Assign1248()
            elif op == 36:
                t = odd(self.NextByte())
                self.AssignLong(self.NextWord(), t)
            elif op == 37:
                self.AssignSet()
            elif op == 38:
                self.AssignPacked()
            elif op == 39:
                self.AssignString()
            elif op == 40:
                self.AssignAlfa()
            elif op in (41, 42):  # ADDTO, SUBFROM
                self.AddToSubFrom(self.Op)
            elif op == 44:
                self.WithStmt()
            elif op == 45:
                self.FreeTemp(self.WithCAttr[self.WithLevel].Cat.copy(), 4)
                self.WithLevel -= 1
                _ = self.NextByte()
            elif op == 190:
                self.GenCall()
            elif op == 192:
                self.DefILabel(self.NextWord())
            elif op in (193, 194, 195):
                self.JumpILabel()
            elif op in (196, 197):  # LULAB, GULAB
                user_lab_no = self.NextWord()
                int_lab_no = self.NextWord()
                self.DefILabel(int_lab_no)
                lp_ulab = UserLabel()
                lp_ulab.UserNo = user_lab_no
                lp_ulab.IntNo = int_lab_no
                lp_ulab.LinkerNo = -1
                lp_ulab.Next = self.ULabelList
                self.ULabelList = lp_ulab
                if self.Op == 197:  # GULAB
                    lab_link_no = self.NextWord()
                    lp_ulab.LinkerNo = lab_link_no
                    if self.ProcLvl > 1:
                        self.Gen(i16(0x4FEE))
                        self.Gen(0)  # LEA -lc(A6),SP
                    else:
                        self.Gen(i16(0x2E6D))
                        self.Gen(i16(self.SaveSpCAttr.VOffset))  # MOVE.L savesp(A5),SP
                        self.Gen(i16(0x2C6D))
                        self.Gen(i16(self.SaveA6CAttr.VOffset))  # MOVE.L saveA6(A5),A6
                    lCAttr = self.GotoCAttr.copy()
                    reg_d = self.LoadD(lCAttr, LongOp, False)
                    self.GenR(i16(0x2F00), reg_d)  # MOVE.L D,-(SP)
                    self.FreeReg(reg_d)
                    self.GenJSR('%_GOTO  ')
            elif op == 198:  # LGOTO
                _user_lab_no = self.NextWord()
                self.GenJump(i16(0x6000), self.NextWord())
            elif op == 199:  # GGOTO
                l_lev = self.NextByte()
                user_lab_no = self.NextWord()
                if l_lev > 1:
                    base = self.GetBase(l_lev)
                    self.FreeReg(base)
                    self.GenR(i16(0x2C48), base)  # MOVE.L A,A6
                self.Gen(i16(0x4EF9))
                self.Gen(0)
                self.Gen(0)  # JMP x.L
                l_name = self.MakeLName(user_lab_no)
                self.GlobRef(l_name, '***Label', i16(self.Ic - 4))
            elif op == 200:
                self.CaseStmt()
            elif op == 202:
                self.ForStmt()
            elif op == 205:
                self.LineStmt()
            elif op == 206:  # TEMPSTMT
                temp_mask = RegMask(self.NextWord())
                for reg_a in range(D0, A1st):
                    if reg_a in temp_mask.sMask:
                        self.Reg[reg_a].Count = 1
                    else:
                        self.Reg[reg_a].Count = 0
            elif op == 241:
                self.ExtRef()
            elif op == 242:
                self.ComRef()
            self.Op = self.NextByte()

    # ========================================================================
    # 5. Procedure assembly, branch shortening, literal-pool compaction, .OBJ output, and init
    # ========================================================================

    def GenProc(self) -> None:
        """Compile one procedure, function, method, or main program body into .OBJ records and optional listing output.

        Emits prologue/epilogue (LINK, stack probe, MOVEM, UNLK, parameter pop),
        shortens span-dependent branches, compacts the string/set literal pool,
        appends the MacsBug procedure name trailer, and writes .OBJ module blocks.
        """
        dis_lbl = 0
        big_c_start: Optional[BigCRef] = None

        def ref_lbl(index: int, dest_index: int, fwd: bool) -> None:
            """Assign and record a disassembly label number connecting instruction word index to target dest_index."""
            nonlocal dis_lbl
            if fwd:
                while self.Tags[dest_index] == Flags.NOPI:
                    dest_index += 1
            if self.pLblDef[dest_index] == 0:
                dis_lbl += 1
                self.pLblRef[index] = dis_lbl
                self.pLblDef[dest_index] = dis_lbl
            else:
                self.pLblRef[index] = self.pLblDef[dest_index]

        def find_short_jumps() -> None:
            """Iteratively convert in-range word branches (JMPL) to 8-bit short branches (JMPS) or NOPI and compute cumulative byte Deltas."""
            half_ic = pdiv(self.Ic, 2)
            if self.ShowAsmCode:
                for idx in range(half_ic):
                    self.Delta[idx] = 0
                    self.pLblRef[idx] = 0
                    self.pLblDef[idx] = 0
            else:
                for idx in range(half_ic):
                    self.Delta[idx] = 0

            pass_no = 0
            while True:
                num_shortened = 0
                pass_no += 1

                # Determine if any jumps can be shortened based on current deltas
                index = 0
                max_index = pdiv(self.Ic, 2)
                elim_flag = False
                while index < max_index:
                    tag = self.Tags[index]
                    if tag in (Flags.ABSI, Flags.NOPI, Flags.CASJ):
                        index += 1
                    elif tag == Flags.JMPS:
                        loc = index * 2 + 2 - self.Delta[index]
                        dest = self.CodeBuff[index + 1]
                        dest = dest - self.Delta[pdiv(dest, 2)]
                        diff = dest - loc
                        if diff == 0:
                            num_shortened += 1
                            self.Tags[index] = Flags.NOPI
                            elim_flag = True
                        index += 2
                    elif tag == Flags.JMPL:
                        loc = index * 2 + 2 - self.Delta[index]
                        dest = self.CodeBuff[index + 1]
                        dest = dest - self.Delta[pdiv(dest, 2)]
                        diff = dest - loc
                        if -128 <= diff <= 128:
                            if diff != 2:
                                num_shortened += 1
                                self.Tags[index] = Flags.JMPS
                                self.Tags[index + 1] = Flags.NOPI
                            else:
                                num_shortened += 2
                                self.Tags[index] = Flags.NOPI
                                self.Tags[index + 1] = Flags.NOPI
                                elim_flag = True
                        index += 2

                # Update delta values
                l_delta = 0
                for index in range(max_index):
                    self.Delta[index] = l_delta
                    if self.Tags[index] == Flags.NOPI:
                        l_delta += 2

                if pass_no <= 5:
                    self.ShortJumps[pass_no] = i16(
                        self.ShortJumps[pass_no] + num_shortened
                    )
                else:
                    self.ShortJumps[5] = i16(self.ShortJumps[5] + num_shortened)

                if ((num_shortened == 0) or (pass_no >= 5)) and not elim_flag:
                    break

        def squeeze_buffer() -> None:
            """Compact CodeBuff in place by removing NOPI words and resolving JMPS, JMPL, and CASJ displacements."""
            max_source_loc = pdiv(self.Ic, 2)
            source_loc = 0
            target_loc = 0
            while source_loc < max_source_loc:
                tag = self.Tags[source_loc]
                if tag == Flags.ABSI:
                    self.CodeBuff[target_loc] = self.CodeBuff[source_loc]
                    self.pLineNumber[target_loc] = self.pLineNumber[source_loc]
                    if self.ShowAsmCode:
                        self.pLblRef[target_loc] = self.pLblRef[source_loc]
                        self.pLblDef[target_loc] = self.pLblDef[source_loc]
                    target_loc += 1
                    source_loc += 1
                elif tag == Flags.JMPS:
                    jmp_dest = self.CodeBuff[source_loc + 1]
                    curr_loc = 2 * source_loc
                    jmp_dest1 = jmp_dest - self.Delta[pdiv(jmp_dest, 2)]
                    self.pLineNumber[target_loc] = self.pLineNumber[source_loc]
                    if self.ShowAsmCode:
                        if jmp_dest < curr_loc:
                            ref_lbl(source_loc, pdiv(jmp_dest1, 2), False)
                        else:
                            ref_lbl(source_loc, pdiv(jmp_dest, 2), True)
                        self.pLblRef[target_loc] = self.pLblRef[source_loc]
                        self.pLblDef[target_loc] = self.pLblDef[source_loc]
                    jmp_delta = jmp_dest1 - (curr_loc + 2 - self.Delta[source_loc])
                    if jmp_delta < 0:
                        jmp_delta += 256  # forces 1 byte
                    self.CodeBuff[target_loc] = i16(
                        self.CodeBuff[source_loc] + jmp_delta
                    )
                    target_loc += 1
                    source_loc += 2
                elif tag == Flags.JMPL:
                    jmp_dest = self.CodeBuff[source_loc + 1]
                    curr_loc = 2 * source_loc
                    jmp_dest1 = jmp_dest - self.Delta[pdiv(jmp_dest, 2)]
                    self.pLineNumber[target_loc] = self.pLineNumber[source_loc]
                    t_loc = target_loc + 1
                    self.pLineNumber[t_loc] = self.pLineNumber[source_loc]
                    if self.ShowAsmCode:
                        if jmp_dest < curr_loc:
                            ref_lbl(source_loc, pdiv(jmp_dest1, 2), False)
                        else:
                            ref_lbl(source_loc, pdiv(jmp_dest, 2), True)
                        self.pLblRef[target_loc] = self.pLblRef[source_loc]
                        self.pLblDef[target_loc] = self.pLblDef[source_loc]
                        self.pLblRef[t_loc] = self.pLblRef[source_loc]
                        self.pLblDef[t_loc] = self.pLblDef[source_loc]
                    jmp_delta = i16(jmp_dest1 - (curr_loc + 2 - self.Delta[source_loc]))
                    self.CodeBuff[target_loc] = self.CodeBuff[source_loc]
                    self.CodeBuff[t_loc] = jmp_delta
                    target_loc += 2
                    source_loc += 2
                elif tag == Flags.NOPI:
                    source_loc += 1
                elif tag == Flags.CASJ:
                    table_loc = target_loc * 2 - 2
                    while True:
                        jmp_dest = self.CodeBuff[source_loc]
                        self.pLineNumber[target_loc] = self.pLineNumber[source_loc]
                        if self.ShowAsmCode:
                            ref_lbl(source_loc, pdiv(jmp_dest, 2), True)
                            self.pLblRef[source_loc] = -self.pLblRef[source_loc]
                            self.pLblRef[target_loc] = self.pLblRef[source_loc]
                            self.pLblDef[target_loc] = self.pLblDef[source_loc]
                        jmp_delta = i16(
                            (jmp_dest - self.Delta[pdiv(jmp_dest, 2)]) - table_loc
                        )
                        self.CodeBuff[target_loc] = jmp_delta
                        target_loc += 1
                        source_loc += 1
                        if self.Tags[source_loc] != Flags.CASJ:
                            break
            self.Ic = target_loc * 2
            self.LastCode = target_loc

        def format_code() -> None:
            """Emit ModuleName, StartAddress, EntryPoint, External/ShortExternal, CommonReloc, CodeBlock, and EndBlock records to OutFile."""
            assert self.OutFile is not None

            def out_com_tree(f_com: Optional[CodComRec]) -> None:
                """Recursively emit CommonReloc .OBJ blocks for all COMMON symbols in CommonTree."""
                assert self.OutFile is not None
                if f_com is not None:
                    out_com_tree(f_com.Left)
                    out_com_tree(f_com.Right)
                    count = 0
                    l_int = f_com.RefList
                    while l_int is not None:
                        count += 1
                        l_int = l_int.Next

                    # Common Block Reference (SizeOf(iRefVariant) == 4)
                    self.rt.SetObjInvar(
                        self.OutBlock, BlockType.CommonReloc, count * 4
                    )
                    self.OutBlock.CommonName = f_com.Name
                    self.rt.PutObjInvar(self.OutFile, self.OutBlock)
                    l_int = f_com.RefList
                    while l_int is not None:
                        self.rt.PutObjLong(
                            self.OutFile,
                            l_int.Int - self.Delta[pdiv(l_int.Int, 2)],
                        )
                        l_int = l_int.Next

            self.rt.SetObjInvar(self.OutBlock, BlockType.ModuleName, 0)
            self.OutBlock.ModuleName = self.UserPNam
            self.OutBlock.SegmentName = seg_name
            self.OutBlock.CSize = 0
            self.rt.PutObjInvar(self.OutFile, self.OutBlock)

            if self.ProcLvl == 1:
                self.rt.SetObjInvar(self.OutBlock, BlockType.StartAddress, 0)
                self.OutBlock.Start = 0
                self.OutBlock.GSize = self.Lc
                self.rt.PutObjInvar(self.OutFile, self.OutBlock)

            self.rt.SetObjInvar(self.OutBlock, BlockType.EntryPoint, 0)
            self.OutBlock.LinkName = link_name
            self.OutBlock.UserName = self.UserPNam
            self.OutBlock.Loc = 0
            self.rt.PutObjInvar(self.OutFile, self.OutBlock)

            lp_ulab = self.ULabelList
            while lp_ulab is not None:
                if lp_ulab.LinkerNo >= 0:
                    lp_ilab = self.LookUpILabel(lp_ulab.IntNo)
                    l_name = self.MakeLName(lp_ulab.LinkerNo)

                    self.rt.SetObjInvar(self.OutBlock, BlockType.EntryPoint, 0)
                    self.OutBlock.LinkName = l_name
                    self.OutBlock.UserName = 'Label***'
                    self.OutBlock.Loc = (
                        lp_ilab.Loc - self.Delta[pdiv(lp_ilab.Loc, 2)]
                    )
                    self.rt.PutObjInvar(self.OutFile, self.OutBlock)
                lp_ulab = lp_ulab.Next

            self.SavedPL = self.ProcList
            ov = ObjVarBlock()
            while self.ProcList is not None:
                pl = self.ProcList
                l_int = pl.RefList
                cnt = 0
                while l_int is not None:
                    cnt += 1
                    l_int = l_int.Next
                if self.ShortCalls:
                    # SizeOf(iShortRef) == 2
                    self.rt.SetObjInvar(
                        self.OutBlock, BlockType.ShortExternal, cnt * 2
                    )
                    self.OutBlock.LinkName = pl.LinkName
                    self.OutBlock.UserName = pl.UserName
                    self.rt.PutObjInvar(self.OutFile, self.OutBlock)
                    ov.VarHeader = VariantType.ShortRef
                    l_int = pl.RefList
                    while l_int is not None:
                        ov.bShortRef = i16(
                            l_int.Int - self.Delta[pdiv(l_int.Int, 2)]
                        )
                        self.rt.PutObjVar(self.OutFile, VariantType.ShortRef, ov)
                        l_int = l_int.Next
                else:
                    # SizeOf(iRefVariant) == 4
                    self.rt.SetObjInvar(self.OutBlock, BlockType.External, cnt * 4)
                    self.OutBlock.LinkName = pl.LinkName
                    self.OutBlock.UserName = pl.UserName
                    self.rt.PutObjInvar(self.OutFile, self.OutBlock)
                    ov.VarHeader = VariantType.RefVariant
                    l_int = pl.RefList
                    while l_int is not None:
                        ov.bRefVariant = (
                            l_int.Int - self.Delta[pdiv(l_int.Int, 2)]
                        )
                        self.rt.PutObjVar(self.OutFile, VariantType.RefVariant, ov)
                        l_int = l_int.Next
                self.ProcList = pl.Next

            # Common Variable References
            out_com_tree(self.CommonTree)

            self.rt.SetObjInvar(self.OutBlock, BlockType.CodeBlock, self.Ic)
            self.OutBlock.Addr = 0
            self.rt.PutObjInvar(self.OutFile, self.OutBlock)
            self.rt.PutObjWords(self.OutFile, self.CodeBuff, self.Ic)

            self.rt.SetObjInvar(self.OutBlock, BlockType.EndBlock, 0)
            self.OutBlock.CSize = self.Ic
            self.rt.PutObjInvar(self.OutFile, self.OutBlock)

        def out_proc_info() -> None:
            """Emit the 8-char MacsBug/LisaBug procedure (and optional Clascal class) name trailer plus literal-pool size word."""
            temp_name = self.UserPNam
            if father != '        ' and father == self.UserPNam:
                temp_name = 'CREATE  '  # special kluge for CREATE

            hi_byte = 0
            for idx in range(1, ALFALEN + 1):
                ch_ord = ord(temp_name[idx - 1])
                if odd(idx):
                    if idx == 1:
                        hi_byte = (ch_ord + 128) & 0xFF
                    else:
                        hi_byte = ch_ord & 0xFF
                else:
                    if idx == 2 and father != '        ':
                        lo_byte = (ch_ord + 128) & 0xFF
                    else:
                        lo_byte = ch_ord & 0xFF
                    self.Gen(i16((hi_byte << 8) | lo_byte))
                    if self.ShowAsmCode:
                        self.pLblRef[self.CurrCode] = 0
                        self.pLblDef[self.CurrCode] = 0

            if father != '        ':
                for idx in range(1, ALFALEN + 1):
                    ch_ord = ord(father[idx - 1])
                    if odd(idx):
                        hi_byte = ch_ord & 0xFF
                    else:
                        lo_byte = ch_ord & 0xFF
                        self.Gen(i16((hi_byte << 8) | lo_byte))
                        if self.ShowAsmCode:
                            self.pLblRef[self.CurrCode] = 0
                            self.pLblDef[self.CurrCode] = 0

            self.CaPatchLoc = self.Ic
            self.Gen(0)  # size of constant area
            if self.ShowAsmCode:
                self.pLblRef[self.CurrCode] = 0
                self.pLblDef[self.CurrCode] = 0

        def gen_stk_expansion_code() -> None:
            """Emit a Lisa OS stack-expansion probe (TST.W -(Lc+4096)(SP)) ahead of LINK A6."""
            dyn_stk = 4096
            if self.Lc < 0:
                self.CodError(2012)
            else:
                if self.Lc + dyn_stk > 32767:
                    s = self.Lc + dyn_stk
                    self.Gen(i16(0x204F))  # MOVE.L A7,A0
                    self.Gen(i16(0x91FC))  # SUB.L #s,(A0)
                    self.Gen(i16((s >> 16) & 0xFFFF))
                    self.Gen(i16(s & 0xFFFF))
                    self.Gen(i16(0x4A50))  # TST.W (A0)
                else:
                    self.Gen(i16(0x4A6F))
                    self.Gen(i16(-self.Lc - dyn_stk))  # TST.W -s(A7)

        def find_set(set_p: BigCRef) -> tuple[BigCRef, int]:
            """Find the largest set constant in BigCList containing set_p on a valid word boundary for literal-pool sharing."""
            def next_set_byte(
                half: bool, p: Optional[IntList]
            ) -> tuple[int, bool, Optional[IntList]]:
                assert p is not None
                if half:
                    return pmod(p.Int, 256), False, p.Next
                else:
                    return pdiv(p.Int, 256), True, p

            def is_subset(
                new_set_p: BigCRef, pool_set_p: BigCRef, cur_pos: int
            ) -> tuple[bool, int]:
                if pool_set_p.BigVal.CstKind == ConstKind.SETCNST:
                    if new_set_p.BigVal.SetBytes <= pool_set_p.BigVal.SetBytes:
                        pool_p = pool_set_p.BigVal.SetValu
                        pool_half = False
                        new_p = new_set_p.BigVal.SetValu
                        new_half = False
                        pool_len = pool_set_p.BigVal.SetBytes
                        new_len = new_set_p.BigVal.SetBytes
                        limit = pool_len - new_len + 1
                        cur_pos = 1
                        first_byte, new_half, new_p = next_set_byte(new_half, new_p)
                        found = False

                        while cur_pos <= limit and not found:
                            pb, pool_half, pool_p = next_set_byte(pool_half, pool_p)
                            if first_byte != pb or not odd(cur_pos):
                                cur_pos += 1
                            else:
                                t_limit = cur_pos + new_len
                                t_pos = cur_pos + 1
                                t_pool_p = pool_p
                                t_pool_half = pool_half
                                t_new_p = new_p
                                t_new_half = new_half
                                matched = True

                                while t_pos < t_limit and matched:
                                    b1, t_pool_half, t_pool_p = next_set_byte(
                                        t_pool_half, t_pool_p
                                    )
                                    b2, t_new_half, t_new_p = next_set_byte(
                                        t_new_half, t_new_p
                                    )
                                    if b1 != b2:
                                        matched = False
                                    else:
                                        t_pos += 1

                                if not matched:
                                    cur_pos += 1
                                elif not odd(new_len):
                                    found = True
                                elif cur_pos < limit:
                                    cur_pos += 1
                                else:
                                    found = True

                        return found, cur_pos
                return False, cur_pos

            pool_set_p = big_c_start
            max_p: Optional[BigCRef] = None
            max_len = 0
            pos_val = 0
            pos_in_max = 0

            while pool_set_p is not None:
                if pool_set_p is not set_p:
                    ok, pos_val = is_subset(set_p, pool_set_p, pos_val)
                    if ok:
                        if pool_set_p.BigVal.SetBytes > max_len:
                            max_len = pool_set_p.BigVal.SetBytes
                            max_p = pool_set_p
                            pos_in_max = pos_val
                pool_set_p = pool_set_p.Next

            if max_p is None:
                pos_val = 1
            else:
                set_p = max_p
                pos_val = pos_in_max
            return set_p, pos_val

        def next_str_ch(
            j_idx: int, p: Optional[StrCRec]
        ) -> tuple[str, int, Optional[StrCRec]]:
            """Advance one character along a linked chain of 8-character StrCRec chunks."""
            j_idx += 1
            if j_idx > 8:
                j_idx = 1
                assert p is not None
                p = p.Next
            assert p is not None
            return p.StrVal[j_idx - 1], j_idx, p

        def find_str(str_p: BigCRef) -> tuple[BigCRef, int]:
            """Deduplicate STRCNST literals by exact match and PAOCCNST literals as word-aligned substrings in BigCList."""
            def is_substr(
                new_str_p: BigCRef, pool_str_p: BigCRef, cur_pos: int
            ) -> tuple[bool, int]:
                if new_str_p.BigVal.CstKind == ConstKind.STRCNST:
                    if pool_str_p.BigVal.CstKind == ConstKind.STRCNST:
                        if new_str_p.BigVal.Len == pool_str_p.BigVal.Len:
                            matched = True
                            pool_p = pool_str_p.BigVal.StrValu
                            new_p = new_str_p.BigVal.StrValu
                            while (
                                pool_p is not None and new_p is not None and matched
                            ):
                                if pool_p.StrVal != new_p.StrVal:
                                    matched = False
                                else:
                                    pool_p = pool_p.Next
                                    new_p = new_p.Next
                            if matched and pool_p is None and new_p is None:
                                return True, 1
                    return False, cur_pos
                elif pool_str_p.BigVal.CstKind == ConstKind.PAOCCNST:
                    if new_str_p.BigVal.Len <= pool_str_p.BigVal.Len:
                        pool_p = pool_str_p.BigVal.StrValu
                        pool_j = 0
                        new_p = new_str_p.BigVal.StrValu
                        new_j = 0
                        pool_len = pool_str_p.BigVal.Len
                        new_len = new_str_p.BigVal.Len
                        limit = pool_len - new_len + 1
                        cur_pos = 1
                        first_ch, new_j, new_p = next_str_ch(new_j, new_p)
                        found = False

                        while cur_pos <= limit and not found:
                            pch, pool_j, pool_p = next_str_ch(pool_j, pool_p)
                            if first_ch != pch or not odd(cur_pos):
                                cur_pos += 1
                            else:
                                t_limit = cur_pos + new_len
                                t_pos = cur_pos + 1
                                t_pool_p = pool_p
                                t_pool_j = pool_j
                                t_new_p = new_p
                                t_new_j = new_j
                                matched = True

                                while t_pos < t_limit and matched:
                                    c1, t_pool_j, t_pool_p = next_str_ch(
                                        t_pool_j, t_pool_p
                                    )
                                    c2, t_new_j, t_new_p = next_str_ch(
                                        t_new_j, t_new_p
                                    )
                                    if c1 != c2:
                                        matched = False
                                    else:
                                        t_pos += 1

                                if not matched:
                                    cur_pos += 1
                                elif not odd(new_len):
                                    found = True
                                elif cur_pos < limit:
                                    cur_pos += 1
                                else:
                                    found = True

                        return found, cur_pos
                return False, cur_pos

            pool_str_p = big_c_start
            max_p: Optional[BigCRef] = None
            max_len = 0
            pos_val = 0
            pos_in_max = 0

            while pool_str_p is not None:
                if pool_str_p is not str_p:
                    ok, pos_val = is_substr(str_p, pool_str_p, pos_val)
                    if ok:
                        if str_p.BigVal.CstKind == ConstKind.STRCNST:
                            return pool_str_p, pos_val
                        elif pool_str_p.BigVal.Len > max_len:
                            max_len = pool_str_p.BigVal.Len
                            max_p = pool_str_p
                            pos_in_max = pos_val
                pool_str_p = pool_str_p.Next

            if max_p is None:
                pos_val = 1
            else:
                str_p = max_p
                pos_val = pos_in_max
            return str_p, pos_val

        # GenProc main body
        self.FirstLNum = 0

        link_name = ''.join(chr(self.NextByte()) for _ in range(ALFALEN))
        s_link_name = link_name
        self.UserPNam = ''.join(chr(self.NextByte()) for _ in range(ALFALEN))
        s_user_pnam = self.UserPNam
        father = ''.join(chr(self.NextByte()) for _ in range(ALFALEN))
        seg_name = ''.join(chr(self.NextByte()) for _ in range(ALFALEN))
        self.CurrSeg = seg_name

        self.Funct = self.NextByte() == 1
        self.ProcLvl = self.NextByte()
        self.Lc = self.NextWord()
        param_bytes = self.NextWord()
        flags_byte = self.NextByte()
        self.GlobalLabels = odd(flags_byte)
        if self.MacFlag:
            stack_expansion = False
        else:
            stack_expansion = odd(pdiv(flags_byte, 2))
        mask_word = self.NextWord()  # mask of registers used
        self.RegMask.iMask = mask_word
        self.Ic = 0
        self.ClearRegs()
        for r in range(D0, SP + 1):
            if r in self.RegMask.sMask:
                self.Reg[r].Count = 1

        if self.SaveA2D3:
            self.RegMask.sMask = self.RegMask.sMask | {D3, A2}
            self.Reg[A2].Count = 1
            self.Reg[D3].Count = 1
            self.A2Used = False
            self.D3Used = False

        self.HaveExtTmp = False
        self.HaveRealTmp = False
        self.HaveDblTmp = False
        dis_lbl = 0
        self.ProcList = None
        self.BigCList = None
        self.LabelTree = None
        self.ULabelList = None
        self.CommonTree = None
        self.WithLevel = 0
        self.FCAllLevel = 0
        self.NextLabel = 0

        lc_patch_loc = 0
        movem_mark = 0
        movem_lnum = 0
        end_movem_mark = 0

        if self.ProcLvl == 1:
            self.GenJSR('%_BEGIN ')
            self.Gen(i16(0x4E56))
            self.Gen(0)
            self.Gen(i16(0x2C5F))  # MOVE.L (A7)+,A6
            if self.Lc < 0:
                self.CodError(2011)
            self.Gen(i16(0x4E55))  # LINK #-lc,A5
            lc_patch_loc = self.Ic
            self.Gen(i16(-self.Lc))
            self.Gen(i16(0x9FED))
            self.Gen(16)  # SUBA.L 16(A5),A7
            self.GenJSR('%_INIT  ')
            if self.GlobalLabels:
                self.GetTemp(self.SaveSpCAttr, 4)
                self.Gen(i16(0x2B4F))
                self.Gen(i16(self.SaveSpCAttr.VOffset))  # MOVE.L SP,savesp(A5)
                self.GetTemp(self.SaveA6CAttr, 4)
                self.Gen(i16(0x2B4E))
                self.Gen(i16(self.SaveA6CAttr.VOffset))  # MOVE.L A6,saveA6(A5)
        else:
            if stack_expansion:
                gen_stk_expansion_code()
            self.Gen(i16(0x4E56))
            lc_patch_loc = self.Ic
            self.Gen(i16(-self.Lc))  # LINK #-lc,A6
            if len(self.RegMask.sMask) > 0 or self.GlobalLabels:
                if self.GlobalLabels:
                    for r in range(D1st, Dnth + 1):
                        self.Reg[r].Count = 1
                    for r in range(A1st, Anth + 1):
                        self.Reg[r].Count = 1
                movem_mark = self.Ic
                movem_lnum = self.LNum
                self.RegMask.iMask = self.SaveRegs()
                end_movem_mark = self.Ic
                self.ClearRegs()

        if self.GlobalLabels:
            self.GetTemp(self.GotoCAttr, 4)
            base = self.GetBase(self.GotoCAttr.VLev)
            self.Gen(i16(0x42A7))
            self.GenJSR('%_LSTSG ')  # CLR.L -(SP)
            self.GenRR(8543, base, 0)
            self.Gen(i16(self.GotoCAttr.VOffset))  # MOVE.L (SP)+,goto(A?)

        if self.SaveA2D3:
            self.Reg[A2].Count = 0
            self.Reg[D3].Count = 0

        self.StmtList(254)  # ENDPROC
        self.DumpProcInfo = self.NextByte()

        if self.MacFlag and self.ProcLvl == 1:
            self.PatchWord(lc_patch_loc, 0)
        else:
            self.PatchWord(lc_patch_loc, i16(-self.Lc))

        if self.GlobalLabels and self.ProcLvl > 1:
            lc_patch_word = i16(-self.Lc - 4 * (Anth - A1st + Dnth - D1st + 2))
        else:
            lc_patch_word = i16(-self.Lc)

        lp_ulab = self.ULabelList
        while lp_ulab is not None:
            if lp_ulab.LinkerNo >= 0 and self.ProcLvl > 1:
                lp_ilab = self.LookUpILabel(lp_ulab.IntNo)
                self.PatchWord(lp_ilab.Loc + 2, lc_patch_word)
            lp_ulab = lp_ulab.Next

        if self.ProcLvl == 1:
            self.GenJSR('%_TERM  ')
            self.Gen(i16(0x4E5D))  # UNLK A5
            self.GenJSR('%_END   ')
            self.Gen(i16(0x4E75))  # RTS
            self.Gen(i16(0x4E5E))  # UNLK A6
            self.Gen(i16(0x4E75))  # RTS
        else:
            if self.SaveA2D3:
                if not (self.A2Used and self.D3Used):
                    save_ic = self.Ic
                    save_lnum = self.LNum
                    self.Ic = movem_mark
                    self.LNum = movem_lnum
                    self.ClearRegs()
                    for r in range(D0, SP + 1):
                        if r in self.RegMask.sMask:
                            self.Reg[r].Count = 1
                    if not self.A2Used:
                        self.Reg[A2].Count = 0
                    if not self.D3Used:
                        self.Reg[D3].Count = 0
                    self.RegMask.iMask = self.SaveRegs()
                    for idx in range(pdiv(self.Ic, 2), pdiv(end_movem_mark, 2)):
                        self.Tags[idx] = Flags.NOPI
                    self.Ic = save_ic
                    self.LNum = save_lnum
            self.RestoreRegs(self.RegMask.iMask)  # restore global registers
            self.Gen(i16(0x4E5E))  # UNLK A6
            if param_bytes <= 8:
                self.Gen(i16(0x4E75))  # RTS
            elif param_bytes == 12:
                self.Gen(i16(0x2E9F))  # MOVE.L (SP)+,(SP)
                self.Gen(i16(0x4E75))  # RTS
            else:
                self.Gen(i16(0x205F))  # MOVE.L (SP)+,A0
                if param_bytes <= 16:
                    self.GenRR(i16(0x504F), pmod(param_bytes, 8), 0)  # ADDQ.W #x,SP
                else:
                    self.Gen(i16(0xDEFC))
                    self.Gen(i16(param_bytes - 8))  # ADDA.w #x,SP
                self.Gen(i16(0x4ED0))  # JMP (A0)

        find_short_jumps()
        squeeze_buffer()
        if self.DumpProcInfo == 1:
            out_proc_info()

        # Output Big Constants
        prev_lbl_def = -1
        prev_lbl_ref = 0
        if self.ShowAsmCode:
            saved_ic = self.Ic
            self.Gen(0)
            self.Ic = saved_ic
            self.pLblRef[self.CurrCode] = 0
            self.pLblDef[self.CurrCode] = 0
            prev_lbl_def = -1
            dis_lbl = 0  # const lbls will be separate

        big_c_start = self.BigCList
        while self.BigCList is not None:
            bc = self.BigCList
            final_loc = bc.Loc - self.Delta[pdiv(bc.Loc, 2)]
            if bc.BigVal.CstKind == ConstKind.SETCNST:
                set_words = pdiv(bc.BigVal.SetBytes + 1, 2)
                set_p, pos = find_set(bc)
                if set_p.StartLoc >= 0:
                    dest = set_p.StartLoc + pos - 1
                    if bc.BigVal.FrontAddress:
                        self.PatchWord(final_loc, i16(dest - final_loc))
                    else:
                        dest = dest + 2 * set_words
                        self.PatchWord(final_loc, i16(dest - final_loc))
                else:
                    set_p.StartLoc = self.Ic
                    bc.StartLoc = self.Ic
                    dest = self.Ic + pos - 1
                    if bc.BigVal.FrontAddress:
                        self.PatchWord(final_loc, i16(dest - final_loc))
                    else:
                        dest = dest + 2 * set_words
                        self.PatchWord(final_loc, i16(dest - final_loc))
                    l_int = set_p.BigVal.SetValu
                    for _ in range(1, pdiv(set_p.BigVal.SetBytes + 1, 2) + 1):
                        assert l_int is not None
                        self.Gen(i16(l_int.Int))
                        l_int = l_int.Next
                        if self.ShowAsmCode:
                            saved_ic = self.Ic
                            self.Gen(0)
                            self.Ic = saved_ic
                            self.pLblRef[self.CurrCode] = 0
                            self.pLblDef[self.CurrCode] = 0
                if self.ShowAsmCode:
                    dis_lbl += 8000  # lbls 8000..15999 ==> sets
                    prev_lbl_ref = pdiv(final_loc - 2, 2)
                    prev_lbl_def = pdiv(dest, 2)
                    ref_lbl(pdiv(final_loc - 2, 2), pdiv(dest, 2), False)
                    idx = pdiv(set_p.StartLoc, 2)
                    if self.pLblDef[idx] == 0:
                        dis_lbl += 1
                        self.pLblDef[idx] = dis_lbl
                    idx = pdiv(set_p.StartLoc + pos - 1, 2)
                    if self.pLblDef[idx] == 0:
                        dis_lbl += 1
                        self.pLblDef[idx] = dis_lbl
                    dis_lbl -= 8000
            elif bc.BigVal.CstKind in (ConstKind.STRCNST, ConstKind.PAOCCNST):
                str_p, pos = find_str(bc)
                if str_p.StartLoc >= 0:
                    dest = str_p.StartLoc + pos - 1
                    self.PatchWord(final_loc, i16(dest - final_loc))
                else:
                    str_p.StartLoc = self.Ic
                    bc.StartLoc = self.Ic
                    dest = self.Ic + pos - 1
                    self.PatchWord(final_loc, i16(dest - final_loc))
                    half_valu = 0
                    if str_p.BigVal.CstKind == ConstKind.STRCNST:
                        half_valu = i16(str_p.BigVal.Len * 256)
                        count = 1
                    else:
                        count = 0
                    j_idx = 0
                    l_string = str_p.BigVal.StrValu
                    for _ in range(1, str_p.BigVal.Len + 1):
                        ch_s, j_idx, l_string = next_str_ch(j_idx, l_string)
                        if odd(count):
                            self.Gen(i16(half_valu + (ord(ch_s) & 0xFF)))
                            if self.ShowAsmCode:
                                saved_ic = self.Ic
                                self.Gen(0)
                                self.Ic = saved_ic
                                self.pLblRef[self.CurrCode] = 0
                                self.pLblDef[self.CurrCode] = 0
                        else:
                            half_valu = i16((ord(ch_s) & 0xFF) * 256)
                        count += 1
                    if odd(count):
                        self.Gen(half_valu)
                        if self.ShowAsmCode:
                            saved_ic = self.Ic
                            self.Gen(0)
                            self.Ic = saved_ic
                            self.pLblRef[self.CurrCode] = 0
                            self.pLblDef[self.CurrCode] = 0
                if self.ShowAsmCode:
                    if bc.BigVal.CstKind == ConstKind.PAOCCNST:
                        dis_lbl += 16000  # lbls 16000..23999 ==> PA of char
                    else:
                        dis_lbl += 24000  # lbls 24000..31999 ==> string
                    idx = pdiv(dest, 2)
                    if prev_lbl_def != idx:
                        ref_lbl(pdiv(final_loc - 2, 2), idx, False)
                    else:
                        j_lbl = self.pLblDef[prev_lbl_def] - 8000
                        if bc.BigVal.CstKind == ConstKind.PAOCCNST:
                            j_lbl += 16000
                        else:
                            j_lbl += 24000
                        self.pLblDef[prev_lbl_def] = j_lbl
                        self.pLblRef[prev_lbl_ref] = j_lbl
                        self.pLblRef[pdiv(final_loc - 2, 2)] = j_lbl
                    prev_lbl_def = -1
                    idx = pdiv(str_p.StartLoc, 2)
                    if self.pLblDef[idx] == 0:
                        dis_lbl += 1
                        self.pLblDef[idx] = dis_lbl
                    if bc.BigVal.CstKind == ConstKind.PAOCCNST:
                        dis_lbl -= 16000
                    else:
                        dis_lbl -= 24000
            self.BigCList = bc.Next

        if self.DumpProcInfo == 1:
            self.CodeBuff[pdiv(self.CaPatchLoc, 2)] = i16(
                self.Ic - self.CaPatchLoc - 2
            )

        format_code()

        if self.Listing:
            self.SwapCodeBuff()
            self.MakeListing()

        if not self.ConsListing:
            if self.FirstOnCons:
                sys.stdout.write('\n')
            if father != '        ' and father == self.UserPNam:
                line = 'CREATE  '
            else:
                line = s_user_pnam
            line = f'{line} - {s_link_name}    Code size ={self.rt.PutIntP(self.Ic, 7)}'
            sys.stdout.write(line + '\n')
            self.FirstOnCons = False

        self.CSizeLo = i16(self.CSizeLo + pmod(self.Ic, 100))
        self.CSizeHi = i16(self.CSizeHi + pdiv(self.Ic, 100))
        if self.CSizeLo >= 100:
            self.CSizeLo = i16(self.CSizeLo - 100)
            self.CSizeHi = i16(self.CSizeHi + 1)

    def UnitHeader(self) -> None:
        """Read a UNIT header record (opcode 244) from the .I file and emit the initial UnitBlock to OutFile."""
        unit_name = ''.join(chr(self.NextByte()) for _ in range(ALFALEN))
        _junk = self.NextByte()
        self.UTextAddr = pdiv(self.NextWord(), 2)
        _junk = self.NextByte()
        _junk = self.NextByte()
        self.UTextSize = pdiv(self.NextWord(), 2)
        _junk = self.NextByte()
        u_data_size = self.NextWord()
        u_kind = self.NextByte()

        # Unit Block
        assert self.OutFile is not None
        self.rt.SetObjInvar(self.OutBlock, BlockType.UnitBlock, 0)
        self.OutBlock.UnitName = unit_name
        self.OutBlock.CodeAddr = 30
        self.OutBlock.TextAddr = 0
        self.OutBlock.TextSize = self.UTextSize * 512
        self.OutBlock.GlobalSize = u_data_size
        self.OutBlock.UnitType = u_kind
        self.rt.PutObjInvar(self.OutFile, self.OutBlock)

        self.Op = self.NextByte()

    def UnitTail(self, l: int) -> None:
        """Backpatch UnitBlock.TextAddr to 512-byte-aligned offset l2 and copy unit interface text blocks from InFile to OutFile."""
        b = pdiv(l, 512)
        if pmod(l, 512) != 0:
            b += 1
        l2 = b * 512
        assert self.OutFile is not None
        self.rt.SetObjPtr(self.OutFile, 0)
        self.rt.SetObjBlockPtr(self.OutFile, 0)
        self.rt.GetObjInvar(self.OutFile, self.OutBlock)
        if self.OutBlock.BlockHeader != BlockType.UnitBlock:
            self.CodError(401)
        else:
            self.OutBlock.TextAddr = l2
            self.rt.SetObjPtr(self.OutFile, 0)
            self.rt.SetObjBlockPtr(self.OutFile, 0)
            self.rt.PutObjInvar(self.OutFile, self.OutBlock)
            if self.rt.io_result > 0:
                self.CodError(408)
            self.rt.SetObjPtr(self.OutFile, l2)
            self.rt.SetObjBlockPtr(self.OutFile, l2)
            from_block = self.UTextAddr
            for _ in range(1, self.UTextSize + 1):
                if self.rt.block_read(self.InFile, self.InBuff, 1, from_block) != 1:
                    self.CodError(409)
                self.rt.PutObjSeq(self.OutFile, self.InBuff[:512])
                if self.rt.io_result > 0:
                    self.CodError(400)
                from_block += 1

    def Middleize(self) -> None:
        """Process all unit/module records in the .I file, emit EOFMark and unit interface tail, and flush remaining listing lines."""
        self.Op = self.NextByte()
        if self.Op == 244:  # UNIT
            self.UnitFlag = True
            self.UnitHeader()
        elif self.Op == 240:
            self.UnitFlag = False
        else:
            if not self.FirstOnCons:
                sys.stdout.write('\n')
            sys.stdout.write(f'{SUBell}*** Input file is not an .I file ***\n')
            self.Aborted = True
            raise AbortCompilation()

        while self.Op == 240:  # MODULE
            self.GenProc()
            self.Op = self.NextByte()

        if self.Op != 255:  # ENDICODE
            self.CodError(2000)

        assert self.OutFile is not None
        self.rt.SetObjInvar(self.OutBlock, BlockType.EOFMark, 0)
        self.rt.PutObjInvar(self.OutFile, self.OutBlock)
        last_block = self.rt.GetObjPtr(self.OutFile)
        self.rt.ZeroObjEnd(self.OutFile)
        if self.UnitFlag:
            self.UnitTail(last_block)

        if self.Listing and self.CListFile is not None:
            while True:
                ok, line = self.rt.GetLine(self.CListFile)
                if not ok:
                    break
                self.LineNumber, line = self.ListLine(
                    0, self.LineNumber, line, True
                )
            if self.AsmOnly and self.ListFile is not None:
                self.rt.PutLineS(self.ListFile, ';')
                self.rt.PutLineS(self.ListFile, '         .END')

    def Initialize(self) -> None:
        """Initialize runtime services, open .I/.OBJ files via ProgComm or interactive prompts, parse $ options, and load N68K.OPCODES."""
        def open_opcodes_file(op_file: UntypedFile, fname: str) -> bool:
            """Search the process volume, OS boot volume, and current prefix for assembler opcode table fname."""
            io_rslt = 9999
            self.rt.SUInitSysVols()
            if self.rt.SUMyProcV != '':
                self.rt.reset_untyped(op_file, f'{self.rt.SUMyProcV}-{fname}')
                io_rslt = self.rt.io_result
            if io_rslt > 0 and self.rt.SUOsBootV != '':
                self.rt.reset_untyped(op_file, f'{self.rt.SUOsBootV}-{fname}')
                io_rslt = self.rt.io_result
            if io_rslt > 0:
                self.rt.reset_untyped(op_file, fname)
                io_rslt = self.rt.io_result
            return io_rslt <= 0

        def enter_opcode(opcode: str) -> None:
            """Insert an 8-character mnemonic into the self.OpcodeTbl binary search tree if not already present."""
            opcode = alfa8(opcode)
            p = Opcodes(opcode)
            if self.OpcodeTbl is None:
                self.OpcodeTbl = p
            else:
                p1: Optional[Opcodes] = self.OpcodeTbl
                dup = False
                prev: Opcodes = self.OpcodeTbl
                l_left = False
                while True:
                    assert p1 is not None
                    prev = p1
                    if p1.Opcode == opcode:
                        dup = True
                    elif p1.Opcode < opcode:
                        p1 = p1.Rlink
                        l_left = False
                    else:
                        p1 = p1.Llink
                        l_left = True
                    if dup or p1 is None:
                        break
                if not dup:
                    if l_left:
                        prev.Llink = p
                    else:
                        prev.Rlink = p

        def process_options(
            opts_line: str, what_user_typed: PromptState
        ) -> tuple[str, PromptState]:
            """Parse code-generator '$' flags ($A+/-, $ASM+/-, $ASM ONLY/PROC, $I+/-, $L+/-, $M+/-)."""
            orig_len = len(opts_line)
            if orig_len > 2 and pget_ch(opts_line, 1) == '$':
                opts_line = self.rt.SUTrimBlanks(opts_line)
                ch2 = self.rt.SUUpCh(pget_ch(opts_line, 2))
                ch3 = pget_ch(opts_line, 3)
                if ch2 == 'A':
                    if ch3 in ('+', '-'):
                        self.SaveA2D3 = ch3 == '+'
                        what_user_typed = PromptState.SUInvalid
                    elif orig_len >= 5:
                        opts_line = self.rt.SUUpStr(opts_line)
                        if pcopy(opts_line, 2, 3) == 'ASM':
                            ch5 = pget_ch(opts_line, 5)
                            if ch5 in ('+', '-'):
                                self.ShowAsmCode = ch5 == '+'
                                self.UseAsmIcode = False
                                what_user_typed = PromptState.SUInvalid
                            elif orig_len >= 9:
                                tail5 = pcopy(opts_line, 5, 5)
                                if tail5 == ' ONLY':
                                    self.AsmOnly = True
                                    what_user_typed = PromptState.SUInvalid
                                elif tail5 == ' PROC':
                                    self.AsmProc = True
                                    what_user_typed = PromptState.SUInvalid
                elif ch2 == 'I':
                    if ch3 in ('+', '-'):
                        self.DeleteI = ch3 == '+'
                        what_user_typed = PromptState.SUInvalid
                elif ch2 == 'L':
                    if ch3 in ('+', '-'):
                        self.AltListing = ch3 == '+'
                        self.ListingOk = self.AltListing
                        what_user_typed = PromptState.SUInvalid
                elif ch2 == 'M':
                    if ch3 in ('+', '-'):
                        self.MacFlag = ch3 == '+'
                        self.SaveA2D3 = self.MacFlag
                        what_user_typed = PromptState.SUInvalid
            return opts_line, what_user_typed

        self.rt.SUInit()
        self.rt.InitIO()
        self.rt.InitPasDefs()
        self.OutFile = self.rt.InitObjFile(8)
        if self.build30:
            self.rt.OIAllowAbort = False

        self.DateStr = self.rt.GetTD()
        sys.stdout.write(f"{TITLE}{VERSION}{' ' * 9}{self.DateStr}\n")
        sys.stdout.write('\n')

        self.Aborted = True
        self.InOpen = False
        self.OutOpen = False
        self.ListOpen = False
        self.CListOpen = False
        self.AltListing = False
        self.ListingOk = True
        self.UseAsmIcode = True
        self.ShowAsmCode = False
        self.Listing = False
        self.ConsListing = False
        self.AsmOnly = False
        self.AsmProc = False
        self.MacFlag = False
        self.SaveA2D3 = False
        self.DeleteI = False

        got_i_file = False
        l_name = ''
        f_name = ''
        self.rt.PCInit()
        if self.rt.PCReset(self.rt.PCText, 'For Code Gen'):
            ok_l, l_name = self.rt.PCGetLine()
            if ok_l and len(l_name) > 0:
                self.rt.reset_untyped(self.InFile, l_name)
                if self.rt.IOError(self.rt.io_result, f'Unable to open {l_name}'):
                    self.KillExec()
                else:
                    ok_f, f_name = self.rt.PCGetLine()
                    if not ok_f:
                        self.KillExec()
                        self.rt.close_untyped(self.InFile)
                    elif len(f_name) == 0:
                        self.KillExec()
                        self.rt.close_untyped(self.InFile)
                    else:
                        if_vol, if_name, _if_ext = self.rt.SUSplitFN(f_name)
                        f_name, _ = self.rt.SUMakeFN(if_vol, if_name, '.OBJ')
                        self.rt.OpenObjFile(self.OutFile, f_name, True)
                        if self.rt.IOError(
                            self.rt.io_result, f'Unable to open {f_name}'
                        ):
                            self.KillExec()
                            self.rt.close_untyped(self.InFile)
                        else:
                            self.InOpen = True
                            self.OutOpen = True
                            got_i_file = True
                            while True:
                                ok_opt, opts_line = self.rt.PCGetLine()
                                if not ok_opt:
                                    break
                                what_user_typed = PromptState.SUValid
                                opts_line, what_user_typed = process_options(
                                    opts_line, what_user_typed
                                )
                                if what_user_typed == PromptState.SUInvalid:
                                    sys.stdout.write(f'Input file - {opts_line}\n')
                            if_vol, if_name, _if_ext = self.rt.SUSplitFN(l_name)
                            l_name, _ = self.rt.SUMakeFN(if_vol, if_name, '')
                            sys.stdout.write(f'Input file - [.I] {l_name}\n')
                            if_vol, if_name, _if_ext = self.rt.SUSplitFN(f_name)
                            f_name, _ = self.rt.SUMakeFN(if_vol, if_name, '')
                            sys.stdout.write(
                                f'Output file - [{l_name}] [.OBJ] {f_name}\n'
                            )
            _ = self.rt.PCClose(True, 'For Code Gen')

        if not got_i_file:
            while True:
                while True:
                    sys.stdout.write('Input file - ')
                    l_name, what_user_typed = self.rt.SUGetFN('', '', '.I')
                    if what_user_typed in (
                        PromptState.SUEscape,
                        PromptState.SUDefault,
                        PromptState.SUNone,
                    ):
                        raise AbortCompilation()
                    if what_user_typed == PromptState.SUInvalid:
                        sys.stdout.write('Bad file name\n')
                    l_name, what_user_typed = process_options(l_name, what_user_typed)
                    if what_user_typed == PromptState.SUValid:
                        break
                self.rt.reset_untyped(self.InFile, l_name)
                if self.rt.IOError(self.rt.io_result, 'Unable to open input file.'):
                    what_user_typed = PromptState.SUInvalid
                    self.KillExec()
                if what_user_typed == PromptState.SUValid:
                    break
            self.InOpen = True

            while True:
                sys.stdout.write('Output file - ')
                if_vol, if_name, _if_ext = self.rt.SUSplitFN(l_name)
                if_vol_name, _ = self.rt.SUMakeFN(if_vol, if_name, '')
                f_name, what_user_typed = self.rt.SUGetFN('', if_vol_name, '.OBJ')
                if what_user_typed == PromptState.SUEscape:
                    raise AbortCompilation()
                if what_user_typed == PromptState.SUInvalid:
                    sys.stdout.write('Bad file name\n')
                if what_user_typed in (
                    PromptState.SUValid,
                    PromptState.SUNone,
                    PromptState.SUDefault,
                ):
                    self.rt.OpenObjFile(self.OutFile, f_name, True)
                    if self.rt.IOError(
                        self.rt.io_result, 'Unable to open output file.'
                    ):
                        what_user_typed = PromptState.SUInvalid
                if what_user_typed == PromptState.SUInvalid:
                    self.KillExec()
                if what_user_typed in (
                    PromptState.SUValid,
                    PromptState.SUNone,
                    PromptState.SUDefault,
                ):
                    break
            self.OutOpen = True

        self.rt.StartTimer()

        if self.AsmOnly:
            # load opcode table used to filter proc names by LkUp
            self.OpcodeTbl = None
            op_file = UntypedFile()
            if open_opcodes_file(op_file, OPFNAME):
                op_blk = bytearray(512)
                op_pos = 0
                op_eof = False
                op_rec_size = 12  # SizeOf(OpcodeRec): Alfa8 (8) + 2*Integer (4)
                cur_blk = -1

                def op_get() -> bytes:
                    nonlocal op_pos, op_eof, cur_blk
                    rec = bytearray(op_rec_size)
                    for k in range(op_rec_size):
                        blk_no = pdiv(op_pos + k, 512)
                        if blk_no != cur_blk and not op_eof:
                            cur_blk = blk_no
                            if self.rt.block_read(op_file, op_blk, 1, cur_blk) != 1:
                                op_eof = True
                        if not op_eof:
                            rec[k] = op_blk[pmod(op_pos + k, 512)]
                    op_pos += op_rec_size
                    return bytes(rec)

                _ = op_get()  # Reset's implicit Get
                op_buf = op_get()
                valid_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789%_ ')
                while True:
                    opcode_str = op_buf[:8].decode('latin-1')
                    ok = all(ch in valid_chars for ch in opcode_str)
                    if ok:
                        enter_opcode(opcode_str)
                    op_buf = op_get()
                    if op_eof or op_buf[0] == 0:
                        break
                self.rt.close_untyped(op_file)

        for idx in range(1, 6):
            self.ShortJumps[idx] = 0
        self.ShortCalls = True
        self.CSizeHi = 0
        self.CSizeLo = 0
        self.InBlock = -1
        self.InByte = 32767
        self.Hex = '0123456789ABCDEF'
        self.CurrSeg = '        '
        self.PrevSeg = '        '

        self.FirstLine = True
        self.FirstOnCons = True
        self.LNum = 0
        self.LineNumber = 0
        self.LnOvflo = False
        self.FirstLNum = 0
        self.EndLineNbr = 0
        self.ListFile = IOFCB()
        self.CListFile = IOFCB()
        self.CListBufr = bytearray(IOByteSize)
        self.ListBufr = bytearray(IOByteSize)
        self.pLineNumber = [0] * (MAXCODE + 1)
        self.pLblRef = [0] * (MAXCODE + 1)
        self.pLblDef = [0] * (MAXCODE + 1)
        self.Aborted = False
