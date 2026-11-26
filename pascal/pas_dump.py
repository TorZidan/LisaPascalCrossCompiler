"""I-code emission mixin for the Lisa Pascal Front End."""

from __future__ import annotations

import struct
from typing import Optional

from frontend_base import (
    A1st,
    Anth,
    AccessKind,
    DeclKind,
    InlineCode,
    LabRec,
    MAXLNUM,
    N,
    NameClass,
    NodeKind,
    PFkind,
    Stmt,
    StmtTypes,
    T,
    TypeForms,
    UnitKind,
    Valu,
    WORD,
)
from lisalib import (
    alfa8,
    f32_to_be_bytes,
    i16,
    odd,
    pdiv,
    pmod,
    u16,
    u32,
)


class _ExtRec:
    """Module-local external routine entry mapping linker/user ``Alfa`` names to a 16-bit external index."""

    __slots__ = ('Next', 'LinkName', 'UserName', 'ExtNo')

    def __init__(self, link_name: str, user_name: str, ext_no: int) -> None:
        self.Next: Optional[_ExtRec] = None
        self.LinkName: str = link_name
        self.UserName: str = user_name
        self.ExtNo: int = ext_no


class DumpMixin:
    """Implements PROCEDURE Dump: serializes symbol-table units, procedures, Clascal method dispatches,
    expressions, and statements into buffered binary I-code for the pass-2 code generator."""

    def Dump(self, ProcTree: Optional[Stmt], ProcN: Optional[N], CallingUnits: bool) -> None:
        """Emit a unit header (``244``) or complete routine I-code module (``240``..``254``) for ``ProcN``."""
        MAXLBUFF = 8192

        LabNo: int = 0
        with_level: int = 0  # Local WithLevel in Dump, distinct from self.WithLevel
        NextExtNo: int = 0
        ExtList: Optional[_ExtRec] = None
        GlobalLabels: bool = False
        lByteNo: int = 0
        lBuff: bytearray = bytearray(MAXLBUFF + 1)
        UnitSet: set[int] = set()
        IntrinSet: set[int] = set()

        def Lout(fVal: int) -> None:
            """Append one byte to the routine-local I-code buffer ``lBuff`` (error 350 on overflow)."""
            nonlocal lByteNo
            if lByteNo < MAXLBUFF:
                lBuff[lByteNo] = fVal & 0xFF
                lByteNo += 1
            else:
                self.Error(350)
                lByteNo = 0

        def Lout2(fVal: int) -> None:
            """Append a 16-bit integer to ``lBuff`` in big-endian byte order."""
            u = u16(fVal)
            Lout((u >> 8) & 0xFF)
            Lout(u & 0xFF)

        def NextLabel() -> int:
            """Allocate and return the next sequential module-local internal label number."""
            nonlocal LabNo
            res = LabNo
            LabNo = i16(LabNo + 1)
            return res

        def MakeLName(n_val: int) -> str:
            """Format local routine number ``n_val`` as an 8-character ``$``-prefixed linker name."""
            n_val = i16(n_val)
            chars = ['$']
            for _ in range(2, 9):
                chars.append(chr(ord('0') + pmod(n_val, 10)))
                n_val = pdiv(n_val, 10)
            return ''.join(chars)

        def FindExt(fUserName: str, RtnNo: int, fLev: int) -> _ExtRec:
            """Look up or register a referenced routine in ``ExtList``, emitting opcode ``241`` on first use."""
            nonlocal ExtList, NextExtNo
            fUserName = alfa8(fUserName)
            if RtnNo < 0:
                lLinkName = fUserName
                if CallingUnits:
                    fUserName = ''.join(
                        chr(ord(ch) - 32) if 'a' <= ch <= 'z' else ch
                        for ch in fUserName
                    )
            else:
                lLinkName = MakeLName(RtnNo)

            def NewExt() -> _ExtRec:
                """Emit external-routine declaration opcode ``241`` to the module stream and allocate ``_ExtRec``."""
                nonlocal NextExtNo
                MAXEXT = 200  # maximum number of external routines in a single module
                if NextExtNo <= MAXEXT:
                    self.Out(241)
                    for idx in range(8):
                        self.Out(ord(lLinkName[idx]))
                    for idx in range(8):
                        self.Out(ord(fUserName[idx]))
                    self.Out2(NextExtNo)
                    self.Out(fLev)
                else:
                    self.Error(309)
                ext = _ExtRec(lLinkName, fUserName, NextExtNo)
                NextExtNo += 1
                return ext

            if ExtList is None:
                lExt = NewExt()
                ExtList = lExt
            else:
                lExt = ExtList
                MatchFlag = False
                while not MatchFlag:
                    if lExt.LinkName == lLinkName:
                        MatchFlag = True
                    else:
                        if lExt.Next is None:
                            lExt.Next = NewExt()
                            MatchFlag = True
                        lExt = lExt.Next
            return lExt

        def UnitIsRegular(fLev: int) -> bool:
            """Return ``True`` if negative scope level ``fLev`` identifies a regular (``REGUNIT``) unit."""
            res = False  # fix: default False when no unit matches (the original left the result unset)
            if fLev >= 0:
                res = False
            else:
                lp = self.UnitList
                while lp is not None:
                    if fLev == -lp.Ulev:
                        res = lp.Ukind == UnitKind.REGUNIT
                        lp = None
                    else:
                        lp = lp.Next
            return res

        def FindUnit(fLev: int) -> None:
            """Emit a unit-reference header record (``242``) on first access to unit ``fLev`` in this module."""
            if fLev not in UnitSet:
                lp = self.UnitList
                while lp is not None:
                    if fLev == -lp.Ulev:
                        self.Out(242)
                        nm = alfa8(lp.Name)
                        for idx in range(8):
                            self.Out(ord(nm[idx]))
                        self.Out(fLev)
                        self.Out(int(lp.Ukind))
                        if lp.Ukind != UnitKind.REGUNIT:
                            IntrinSet.add(fLev)
                        UnitSet.add(fLev)
                        lp = None
                    else:
                        lp = lp.Next

        def DumpJSR(fOp: int, fLev: int, RtnNo: int, fUserName: str) -> None:
            """Register routine ``fUserName`` via ``FindExt`` and emit call/parameter opcode ``fOp`` with its index."""
            lExt = FindExt(fUserName, RtnNo, fLev)
            Lout(fOp)
            Lout2(lExt.ExtNo)

        def OutIntCnst(fValue: int, fSize: int) -> None:
            """Emit a 1-, 2-, or 4-byte integer constant I-code (``CNST1``..``CNST4``) in big-endian order."""
            b = struct.pack('>I', u32(fValue))
            if fSize > 2:
                Lout(26)  # CNST4
                Lout(b[0])
                Lout(b[1])
            else:
                Lout(24 + (1 if fSize > 1 else 0))  # CNST1 / CNST2
            if fSize > 1:
                Lout(b[2])
            Lout(b[3])

        def DumpMethod(fOp: int, MethodNumber: int, MethodLevel: int) -> None:
            """Emit a Clascal virtual method dispatch I-code (``METHCALL`` = 253)."""
            Lout(253)  # METHCALL
            Lout(1 if fOp == 176 else 0)  # UFUNCALL
            Lout(MethodLevel)
            Lout(MethodNumber)

        def DumpInline(fOp: int, inline_code: Optional[InlineCode]) -> None:
            """Emit an ``INLINE`` machine-code call sequence (``INLINE`` = 252) with raw 16-bit 68000 words."""
            Lout(252)  # INLINE
            Lout(1 if fOp == 176 else 0)  # UFUNCALL

            n_words = 0
            p = inline_code
            while p is not None:
                n_words += 1
                p = p.NextInlineWord

            Lout2(n_words)

            while inline_code is not None:
                Lout2(inline_code.InlineWord)
                inline_code = inline_code.NextInlineWord

        def DumpCCall(
            StackSpace: int,
            IdType: Optional[T],
            fOp: int,
            fLev: int,
            RtnNo: int,
            fUserName: str,
        ) -> None:
            """Emit a ``C`` calling-convention call I-code (``CCALL`` = 251) with return size and stack cleanup bytes."""
            Lout(251)  # CCALL
            if fOp != 176:  # UFUNCALL
                Lout(0)
            elif IdType is self.RealPtr:
                Lout(8)
            else:
                Lout(4)
            lExt = FindExt(fUserName, RtnNo, fLev)
            Lout2(lExt.ExtNo)
            Lout2(StackSpace)

        def DumpSuper(fOp: int) -> None:
            """Emit a call to the Clascal ``%_SUPER`` runtime helper for ``SUPERSELF`` method dispatches."""
            CallName = '%_SUPER '
            lExt = FindExt(CallName, -1, 1)
            Lout(fOp)
            Lout2(lExt.ExtNo)

        def OutCnst(fValu: Valu, FType: Optional[T]) -> None:
            """Serialize a typed scalar, ``REAL``, ``STRING``, packed char array, or bitset constant to ``lBuff``."""
            lSize = self.FullBytes(FType)
            if FType.Form in (TypeForms.SCALAR, TypeForms.SUBRANGE):
                if self.CompTypes(FType, self.RealPtr):
                    b = f32_to_be_bytes(fValu.Rvalu)
                    Lout(26)  # CNST4
                    for byte in b:
                        Lout(byte)
                else:
                    OutIntCnst(fValu.Ivalu, lSize)
            elif FType.Form in (TypeForms.ARRAYS, TypeForms.STRINGS, TypeForms.SCONST):
                if FType.Form == TypeForms.ARRAYS:
                    Lout(29)  # PAOCNST
                else:
                    Lout(28)  # STRCNST
                Len = fValu.SvaluLen
                Lout(Len)
                j = 0
                lStr = fValu.Svalu
                for _ in range(1, Len + 1):
                    if j == 8:
                        lStr = lStr.Next
                        j = 0
                    j += 1
                    Lout(ord(lStr.StrPart[j - 1]))
            elif FType.Form == TypeForms.SETS:
                Lout(30)  # SETCNST
                Len = (pdiv(fValu.MaxSetEl, 16) + 1) * 2
                Lout(Len)
                j = 0
                lSet = fValu.SetValu
                for _ in range(1, Len + 1):
                    if j == 32:
                        if lSet is not None:
                            lSet = lSet.NextSet
                        j = 0
                    Bits = 0
                    Bit = 1
                    for k in range(j, j + 8):
                        if lSet is not None and k in lSet.SetVal:
                            Bits += Bit
                        Bit += Bit
                    j += 8
                    Lout(Bits)

        def LocalName(n_val: int) -> str:
            """Format local routine number ``n_val`` into an 8-character ``$``-prefixed module linker name."""
            n_val = i16(n_val)
            chars = ['$']
            for _ in range(2, 9):
                chars.append(chr(ord('0') + pmod(n_val, 10)))
                n_val = pdiv(n_val, 10)
            return ''.join(chars)

        def Selector(fVarb: Optional[N]) -> None:
            """Emit prefix lvalue/addressing I-code for variables, unit globals, registers, fields, and array indices."""
            if fVarb.Node == NodeKind.IDENTNODE:
                if fVarb.Class == NameClass.CONSTS:
                    OutCnst(fVarb.ValueOf, fVarb.IdType)
                elif fVarb.Class in (NameClass.FUNC, NameClass.PROC, NameClass.VARS):
                    if fVarb.Class == NameClass.VARS:
                        lOffset = fVarb.Voff
                        lLev = fVarb.Vlev
                        if fVarb.Vkind == AccessKind.INDRCT:
                            Lout(12)  # UPARROW
                    elif fVarb.PFdecl == PFkind.FORMAL:
                        lOffset = fVarb.PFOff
                        lLev = fVarb.PFlev
                    else:
                        lOffset = fVarb.ParmBytes
                        lLev = fVarb.PFlev + 1
                    if lLev == 1:
                        Op = 1  # GLOBAL
                    elif lLev == self.Level:
                        Op = 2  # LOCAL
                    elif lLev < 0:
                        Op = -lLev
                        FindUnit(Op)
                        if Op in IntrinSet:
                            Lout(15)  # Record Field
                            Lout2(lOffset)
                            Lout(12)  # Dereference
                            Lout(4)   # COMMON
                            lOffset = 0
                        else:
                            Lout(4)   # COMMON
                    else:
                        Lout(3)  # INTERM
                        Op = self.Level - lLev
                    Lout(Op)
                    Lout2(lOffset)
                elif fVarb.Class == NameClass.FIELD:
                    pass
            elif fVarb.Node == NodeKind.REGISTER:
                Lout(5)  # REGISTER
                Lout(fVarb.Reg)
                Lout(fVarb.Load)
                Lout(fVarb.LoadSize)
                if fVarb.LoadSize != 0:
                    Expression(fVarb.LoadExpr)
            elif fVarb.Node == NodeKind.UNNODE:
                if fVarb.UnOp == 4:  # INTRINSIC UNIT BASE
                    FindUnit(fVarb.UnSubOp)
                    Lout(4)  # COMMON
                    Lout(fVarb.UnSubOp)
                    Lout2(0)
                else:
                    if fVarb.UnOp != 22:  # ADDRESS
                        Lout(fVarb.UnOp)
                    if fVarb.UnOp in (62, 63, 43):  # EXTUFLD, EXTSFLD, WITHREC
                        Lout(fVarb.UnSubOp)
                    if fVarb.UnOp == 22:  # ADDRESS
                        if fVarb.UnSubOp == 0:
                            # remove @...^
                            WasVarParm = False
                            LocArg = fVarb.UnArg
                            if fVarb.UnArg.Node == NodeKind.UNNODE:
                                if fVarb.UnArg.UnOp == 12:  # ^
                                    LocArg = fVarb.UnArg.UnArg
                                else:
                                    Lout(22)
                            elif (
                                fVarb.UnArg.Node == NodeKind.IDENTNODE
                                and fVarb.UnArg.Class == NameClass.VARS
                                and fVarb.UnArg.Vkind == AccessKind.INDRCT
                            ):
                                WasVarParm = True
                                fVarb.UnArg.Vkind = AccessKind.DRCT
                            else:
                                Lout(22)
                            Selector(LocArg)
                            if WasVarParm:
                                fVarb.UnArg.Vkind = AccessKind.INDRCT
                        else:
                            if fVarb.UnArg.PFdecl == PFkind.FORMAL:
                                # parametric routine: PFOFF+4(A6)
                                Lout(2)  # local
                                Lout2(fVarb.UnArg.PFOff + 4)
                            else:
                                Lout(fVarb.UnOp)
                                lExt = FindExt(
                                    fVarb.UnArg.Name,
                                    fVarb.UnArg.RtnNo,
                                    fVarb.UnArg.PFlev,
                                )
                                Lout(fVarb.UnSubOp)
                                Lout2(lExt.ExtNo)
                    elif fVarb.UnOp == 12:  # ^
                        Expression(fVarb.UnArg)
                    elif fVarb.UnOp != 43:  # WITHREC
                        Selector(fVarb.UnArg)
            elif fVarb.Node == NodeKind.BINNODE:
                if fVarb.BinOp == 15:  # FIELD
                    Lout(15)
                    Lout2(fVarb.RightArg.FOff)
                    Selector(fVarb.LeftArg)
                elif fVarb.BinOp == 12:  # Binary ^
                    Lout(15)  # .
                    Lout2(fVarb.BinSubOp)
                    Lout(12)  # ^
                    Expression(fVarb.LeftArg)
                elif 32 <= fVarb.BinOp <= 34:  # inline assign
                    Lout(fVarb.BinOp)
                    Lout(fVarb.BinSubOp)
                    Expression(fVarb.LeftArg)
                    Expression(fVarb.RightArg)
            elif fVarb.Node == NodeKind.TRINODE:
                if fVarb.TriOp == 16:  # INDEX
                    if fVarb.TriPt.Form == TypeForms.ARRAYS:
                        lSize = self.FullBytes(fVarb.TriPt.ArrayOf)
                        Lo, _Hi = self.GetBounds(fVarb.TriPt.IndexedBy)
                        if fVarb.TriPt.BitPackd:
                            Op = 21
                        elif lSize == 1:
                            Op = 16
                        elif lSize == 2:
                            Op = 17
                        elif lSize == 4:
                            Op = 18
                        elif lSize == 8:
                            Op = 19
                        else:
                            Op = 20
                        Lout(Op)
                        if Op == 20:
                            Lout2(lSize)
                        elif Op == 21:
                            Lout(fVarb.TriPt.BitsPerEl)
                    else:
                        # form = STRINGS
                        Lo = 0
                        Lout(21)
                        Lout(8)
                    Lout2(Lo)
                    Selector(fVarb.Tri1)
                    Expression(fVarb.Tri2)
                elif fVarb.TriOp == 184:  # METHODCALL
                    DumpUCall(
                        fVarb.TripN,
                        fVarb.Tri2,
                        fVarb.Tri1,
                        fVarb.OrigTri1,
                        fVarb.TriSuper,
                    )
            elif fVarb.Node == NodeKind.CSTNODE:
                OutCnst(fVarb.CstValu, fVarb.CstType)
            elif fVarb.Node == NodeKind.ASGNNODE:
                Lout(fVarb.AsgnOp)
                Lout(3)
                Expression(fVarb.AsgnpN)
                Selector(fVarb.AsgnVar)
                Expression(fVarb.AsgnExpr)

        def Expression(fExpr: Optional[N]) -> None:
            """Emit prefix polish rvalue I-code for unary, binary, set, range-check, call, and constant AST nodes."""
            if fExpr.Node in (NodeKind.REGISTER, NodeKind.IDENTNODE):
                Selector(fExpr)
            elif fExpr.Node == NodeKind.UNNODE:
                if fExpr.UnOp in (4, 12, 13, 14, 22, 43, 62, 63):
                    Selector(fExpr)
                else:
                    Lout(fExpr.UnOp)
                    if fExpr.UnOp != 23 and fExpr.UnOp != 31:  # NIL, NULLSET
                        if fExpr.UnOp == 168:  # SING
                            Lout(fExpr.UnSubOp)
                        elif fExpr.UnOp == 170:  # AJDSET
                            Lout2(fExpr.UnSubOp)
                        Expression(fExpr.UnArg)
            elif fExpr.Node == NodeKind.BINNODE:
                if fExpr.BinOp in (12, 15, 16, 17, 18, 19, 20, 21):
                    Selector(fExpr)
                elif fExpr.BinOp == 176:  # UFCALL
                    DumpUCall(fExpr.LeftArg, fExpr.RightArg, None, None, None)
                elif fExpr.BinOp == 178:  # SFCALL
                    DumpSfCall(fExpr.LeftArg, fExpr.RightArg)
                else:
                    Lout(fExpr.BinOp)
                    if 150 <= fExpr.BinOp <= 155:  # PAOCLT..PAOCNE
                        Lout(fExpr.BinSubOp)
                        Lout(fExpr.BinSubOp)
                    elif (160 <= fExpr.BinOp <= 169) or (32 <= fExpr.BinOp <= 34):
                        Lout(fExpr.BinSubOp)
                    if fExpr.BinOp == 46:  # RNGCHK
                        Lo, Hi = self.GetBounds(fExpr.LeftPt)
                        Lout2(Lo)
                        Lout2(Hi)
                    elif fExpr.BinOp == 47:  # SRNGCHK
                        Lout(fExpr.BinSubOp)
                    else:
                        Expression(fExpr.LeftArg)
                    Expression(fExpr.RightArg)
            elif fExpr.Node == NodeKind.TRINODE:
                Selector(fExpr)
            elif fExpr.Node == NodeKind.CSTNODE:
                OutCnst(fExpr.CstValu, fExpr.CstType)
            elif fExpr.Node == NodeKind.ASGNNODE:
                Selector(fExpr)

        def ArgAddr(ArgList: Optional[N]) -> Optional[N]:
            """Emit a ``REFPARM`` (183) reference parameter from ``ArgList`` and return the remaining arguments."""
            if ArgList is not None:
                Lout(183)  # REFPARM
                Expression(ArgList.LeftArg)
                return ArgList.RightArg
            else:
                self.Error(1000)
                return None

        def ArgVal2(ArgList: Optional[N]) -> Optional[N]:
            """Emit a 2-byte ``VALPRM2`` (185) value parameter from ``ArgList`` and return the remaining arguments."""
            if ArgList is not None:
                Lout(185)  # VALPRM2
                Expression(ArgList.LeftArg)
                return ArgList.RightArg
            else:
                self.Error(1001)
                return None

        def ArgVal4(ArgList: Optional[N]) -> Optional[N]:
            """Emit a 4-byte ``VALPRM4`` (186) value parameter from ``ArgList`` and return the remaining arguments."""
            if ArgList is not None:
                Lout(186)  # VALPRM4
                Expression(ArgList.LeftArg)
                return ArgList.RightArg
            else:
                self.Error(1002)
                return None

        def DumpSfCall(fProc: Optional[N], pArgs: Optional[N]) -> None:
            """Emit inline or ``STDFCAL`` (178) I-code for built-in Pascal, UCSD, and Clascal standard functions."""
            Key = fProc.Key
            if Key in (
                2, 4, 5, 6, 7, 8, 12, 13, 15, 17,
                20, 21, 22, 23, 24, 25, 27, 28, 29, 30, 31, 33, 34,
            ):
                if Key in (2, 4, 7, 8, 13, 15):
                    lSize = 4
                elif Key in (5, 6, 34):
                    lSize = 129
                elif Key in (20, 23, 24, 25, 28, 29, 30, 33):
                    lSize = 130
                elif Key in (12, 17, 27, 31):
                    lSize = 132
                else:
                    lSize = 0
                Lout(190)  # PRMLIST
                Lout(182)  # FCTNRES
                Lout(lSize)

            if Key in (1, 14):  # ABS, SQR
                Lout(pArgs.BinOp)
                Expression(pArgs.LeftArg)
            elif Key in (2, 4, 7, 8, 12, 13, 15, 17):  # ARCTAN, COS, EXP, LN, ROUND, SIN, SQRT, TRUNC
                pArgs = ArgVal4(pArgs)
            elif Key in (5, 6, 34):  # EOF, EOLN, KEYPRESS
                pArgs = ArgAddr(pArgs)
            elif Key == 9:  # ODD
                Lout(111)  # ODD
                Expression(pArgs.LeftArg)
            elif Key in (11, 16):  # PRED, SUCC
                lOp = 64 if Key == 16 else 66  # ADD2 / SUB2
                lSize = pArgs.BinSubOp
                if lSize > 2:
                    lOp += 1  # 2-->4
                Lout(lOp)
                Expression(pArgs.LeftArg)
                OutIntCnst(1, lSize)
            elif Key in (3, 10, 18, 26, 32, 35):  # CHR, ORD, POINTER, SIZEOF, ORD4, THISCLASS
                Expression(pArgs.LeftArg)
            elif Key == 19:  # LENGTH
                if pArgs.LeftArg.Node == NodeKind.CSTNODE:
                    OutIntCnst(pArgs.LeftArg.CstValu.SvaluLen, 2)
                else:
                    Lout(62)   # EXTSFLD
                    Lout(136)  # 8-bits:8-bit-offset
                    Expression(pArgs.LeftArg)
            elif Key == 20:  # POS
                pArgs = ArgAddr(pArgs)
                pArgs = ArgAddr(pArgs)
            elif Key == 21:  # CONCAT
                n_cnt = 0
                lpN: Optional[N] = None
                while pArgs is not None:
                    lpN = pArgs.LeftArg
                    pArgs = ArgAddr(pArgs)
                    n_cnt += 1
                Lout(185)  # VALPRM2
                OutIntCnst(n_cnt - 1, 2)
                Lout(178)  # STDFCAL
                Lout(21)
                Expression(lpN)
            elif Key == 22:  # COPY
                pArgs = ArgAddr(pArgs)
                pArgs = ArgVal2(pArgs)
                pArgs = ArgVal2(pArgs)
                lpN = pArgs.LeftArg
                pArgs = ArgAddr(pArgs)
                Lout(178)  # STDFCAL
                Lout(22)
                Expression(lpN)
            elif Key in (23, 24):  # BLOCKREAD, BLOCKWRITE
                pArgs = ArgAddr(pArgs)
                pArgs = ArgAddr(pArgs)
                pArgs = ArgVal2(pArgs)
                if pArgs is not None:
                    pArgs = ArgVal2(pArgs)
                else:
                    Lout(185)  # VALPRM2
                    OutIntCnst(-1, 2)
            elif Key in (25, 31, 33):  # IORESULT, MEMAVAIL, HEAPRESULT
                pass
            elif Key == 27:  # PWROFTEN
                pArgs = ArgVal2(pArgs)
            elif Key in (28, 29):  # SCANEQ, SCANNE
                pArgs = ArgVal2(pArgs)
                pArgs = ArgVal2(pArgs)
                pArgs = ArgAddr(pArgs)
            elif Key == 30:  # UNITBUSY
                pArgs = ArgVal2(pArgs)
            elif Key == 36:  # INCLASS
                fProc = None
                if pArgs is not None:
                    if pArgs.RightArg is not None:
                        if pArgs.RightArg.BinSubOp == int(NodeKind.IDENTNODE):
                            fProc = self.InObCpPtr
                        else:
                            fProc = self.InObCnPtr
                if fProc is not None:
                    DumpUCall(fProc, pArgs, None, None, None)

            if Key in (
                2, 4, 5, 6, 7, 8, 12, 13, 15, 17,
                20, 23, 24, 25, 27, 28, 29, 30, 31, 33, 34,
            ):
                Lout(178)  # STDFCAL
                Lout(Key)

        def DumpUCall(
            fProc: Optional[N],
            FArgs: Optional[N],
            fClVar: Optional[N],
            OrigfClVar: Optional[N],
            SuperpT: Optional[T],
        ) -> None:
            """Emit parameter evaluation and call dispatch I-code for user, formal, ``INLINE``, ``C``, and Clascal calls."""

            def ReversePtrs(
                formals: Optional[N], actuals: Optional[N]
            ) -> tuple[Optional[N], Optional[N]]:
                """Reverse ``formals`` and ``actuals`` lists in place so ``C`` arguments push right-to-left."""
                Curr = formals
                formals = None
                while Curr is not None:
                    Nxt = Curr.Next
                    Curr.Next = formals
                    formals = Curr
                    Curr = Nxt

                Curr = actuals
                actuals = None
                while Curr is not None:
                    Nxt = Curr.RightArg
                    Curr.RightArg = actuals
                    actuals = Curr
                    Curr = Nxt

                return formals, actuals

            Lout(190)  # BPARMLST
            Ccall = fProc.PFdecl == PFkind.CDECL
            if fProc.Class == NameClass.FUNC:
                if not Ccall:
                    Lout(182)  # FCTNRES
                    Lout(self.FullBytes(fProc.IdType))
                lOp = 176  # UFUNCALL
            else:
                lOp = 177  # UPROCALL

            if Ccall:
                fProc.PFargList, FArgs = ReversePtrs(fProc.PFargList, FArgs)
            Formals = fProc.PFargList
            Actuals = FArgs
            StackSpace = 0
            while Formals is not None:
                if Formals.Class == NameClass.VARS:
                    if Formals.Vkind != AccessKind.DRCT:
                        Lout(183)  # REFPARM
                    else:
                        n_bytes = self.FullBytes(Formals.IdType)
                        if Formals.IdType.Form == TypeForms.SETS:
                            if Ccall:
                                Lout(188)  # LRGVPRM
                                Lout2(n_bytes)
                            else:
                                Lout(189)  # SETVPRM
                                Lout(n_bytes)
                        elif n_bytes > 4:
                            Lout(188)  # LRGVPRM
                            Lout2(n_bytes)
                        else:
                            if Ccall:
                                if Formals.IdType is not self.RealPtr:
                                    Lout(186)  # VPARAM4
                                else:
                                    Lout(187)  # VPARAM8
                                    StackSpace += 4
                            elif n_bytes == 1:
                                Lout(184)  # VPARAM1
                            elif n_bytes == 2:
                                Lout(185)  # VPARAM2
                            else:
                                Lout(186)  # VPARAM4
                    Expression(Actuals.LeftArg)
                else:
                    act_left = Actuals.LeftArg
                    if act_left.PFdecl == PFkind.FORMAL:
                        Lout(187)  # VPARAM8
                        Selector(act_left)
                    else:
                        DumpJSR(191, act_left.PFlev + 1, act_left.RtnNo, act_left.Name)
                Formals = Formals.Next
                Actuals = Actuals.RightArg
                StackSpace += 4

            if Ccall:
                fProc.PFargList, FArgs = ReversePtrs(fProc.PFargList, FArgs)

            if fProc.PFdecl == PFkind.FORMAL:
                if fProc.Class == NameClass.PROC:
                    lOp = 181  # PPCALL
                else:
                    lOp = 180  # PFCALL
                Lout(lOp)
                Selector(fProc)
            elif fProc.PFdecl in (PFkind.METHDECL, PFkind.FORWMETHDECL):
                if fClVar is not None:
                    Lout(186)  # VALPRM4
                    Expression(fClVar)
                if SuperpT is None:
                    DumpMethod(lOp, fProc.MethodNo, fProc.MethodLevel)
                elif fProc.MethodNo == 0:  # CREATE
                    if SuperpT.ItsId is None:
                        lName = 'No Name!'
                    else:
                        lName = SuperpT.ItsId.Name
                    DumpJSR(lOp, fProc.PFlev + 1, fProc.RtnNo, lName)
                else:
                    Lout(183)  # REFPARM
                    Op = -OrigfClVar.IdType.MethodLevel
                    lOffset = OrigfClVar.IdType.MethodOff
                    FindUnit(Op)
                    if Op in IntrinSet:
                        Lout(15)  # Record Field
                        Lout2(lOffset)
                        Lout(12)  # Dereference
                        Lout(4)   # COMMON
                        lOffset = 0
                    else:
                        Lout(4)   # COMMON
                    Lout(Op)
                    Lout2(lOffset)
                    Lout(185)  # VPARAM2
                    OutIntCnst(
                        pdiv(OrigfClVar.IdType.ClassLevel - SuperpT.ClassLevel, 2),
                        WORD,
                    )
                    Lout(185)  # VPARAM2
                    OutIntCnst(fProc.MethodLevel * 256 + fProc.MethodNo, WORD)
                    DumpSuper(lOp)
            elif fProc.PFdecl == PFkind.INLINEDECL:
                DumpInline(lOp, fProc.InlineCode)
            elif Ccall:
                DumpCCall(StackSpace, fProc.IdType, lOp, 2, fProc.RtnNo, fProc.Name)
            else:
                DumpJSR(lOp, fProc.PFlev + 1, fProc.RtnNo, fProc.Name)

        def DumpStmt(fStmt: Optional[Stmt]) -> None:
            """Walk a statement chain, emitting pass-2 line numbers and I-code for all executable constructs."""
            nonlocal with_level
            Lo: int = 0
            Hi: int = 0
            ThisLabNo: int = 0
            ExitLabNo: int = 0
            ElseLabNo: int = 0
            USED: int = 0
            Unused: int = 0

            def OutGoto(fLabLev: int, pLab: LabRec) -> None:
                """Emit a local branch (``JMPLULB`` = 198) or non-local branch (``JMPGULB`` = 199) to ``pLab``."""
                if fLabLev == self.Level:
                    Lout(198)  # JMPLULB
                    Lout2(pLab.LabelNo)
                    Lout2(pLab.ILabelNo)
                else:
                    Lout(199)  # JMPGULB
                    Lout(fLabLev)
                    if pLab.GlobRefNo < 0:
                        pLab.GlobRefNo = self.LocProcNo
                        self.LocProcNo += 1
                    Lout2(pLab.GlobRefNo)

            def DumpCallStmt(stmt: Stmt) -> None:
                """Dispatch a procedure call statement to formatted I/O, standard procedure, or ``DumpUCall``."""

                def ReadWrite(rw_stmt: Stmt) -> None:
                    """Decompose ``READ``/``READLN`` and ``WRITE``/``WRITELN`` argument lists into per-item ``STDPCAL`` calls."""
                    proc = rw_stmt.ProcpN
                    pArgs = rw_stmt.pArgList
                    if proc.Key in (8, 9):  # read, readln
                        FileArg = pArgs.LeftArg
                        pArgs = pArgs.RightArg
                        while pArgs is not None:
                            lOp = pArgs.BinOp
                            Arg = pArgs.LeftArg
                            if lOp <= 2:
                                lSubOp = pArgs.BinSubOp
                                Lout(lSubOp)
                                Lout(0)  # not flippable
                                Selector(Arg)
                                if lOp == 1 and lSubOp != 34:  # ASS4
                                    if lSubOp == 33:  # ASS2
                                        Lout(52)  # INT42
                                    else:
                                        Lout(53)  # INT41
                            Lout(190)  # BPRMLIST
                            Lout(183)  # REFPARAM
                            Selector(FileArg)
                            if lOp > 2:
                                Lout(183)  # REFPARM
                                Selector(Arg)
                                Lout(185)  # VARPRM2
                                OutIntCnst(pArgs.BinSubOp, 2)
                            Lout(179)  # STDPCAL
                            Lout(110 + lOp)
                            pArgs = pArgs.RightArg
                        if proc.Key == 9:
                            Lout(190)  # BPRMLIST
                            Lout(183)  # REFPARAM
                            Selector(FileArg)
                            Lout(179)  # STDPCAL
                            Lout(115)  # READLN
                    elif proc.Key in (10, 11):  # write, writeln
                        FileArg = pArgs.LeftArg
                        pArgs = pArgs.RightArg
                        while pArgs is not None:
                            Lout(190)  # BPRMLIST
                            Lout(183)  # REFPARAM
                            Selector(FileArg)
                            lOp = pArgs.BinOp
                            Colon1: Optional[N] = None
                            Colon2: Optional[N] = None
                            Arg = pArgs.LeftArg
                            if Arg.Node == NodeKind.BINNODE and Arg.BinOp == 0:  # COLON
                                Colon1 = Arg.RightArg
                                Arg = Arg.LeftArg
                                if Arg.Node == NodeKind.BINNODE and Arg.BinOp == 0:  # COLON
                                    Colon2 = Colon1
                                    Colon1 = Arg.RightArg
                                    Arg = Arg.LeftArg
                            if lOp <= 4:
                                if lOp == 0:
                                    lOp2 = 184  # VALPRM1
                                    lSize = 1
                                elif lOp == 1:
                                    lOp2 = 184  # VALPRM1
                                    lSize = 5
                                elif lOp == 2:
                                    lOp2 = 186  # VALPRM4
                                    lSize = 8
                                elif lOp == 3:
                                    lOp2 = 186  # VALPRM4
                                    lSize = 12
                                else:  # 4
                                    lOp2 = 186  # VALPRM4
                                    lSize = 12
                                Lout(lOp2)
                                Expression(Arg)
                            else:
                                Lout(183)  # REFPARM
                                Expression(Arg)
                                lSize = 0
                                if lOp == 6:
                                    Lout(185)  # VALPRM2
                                    Expression(Colon1)
                                    Colon1 = Colon2
                            Lout(185)  # VALPRM2
                            if Colon1 is None:
                                OutIntCnst(lSize, 2)
                            else:
                                Expression(Colon1)
                            if lOp == 4:
                                Lout(185)  # VALPRM2
                                if Colon2 is None:
                                    OutIntCnst(6, 2)
                                else:
                                    Expression(Colon2)
                            Lout(179)  # STDPCAL
                            Lout(100 + lOp)
                            pArgs = pArgs.RightArg
                        if proc.Key == 11:
                            Lout(190)  # BPRMLIST
                            Lout(183)  # REFPARAM
                            Selector(FileArg)
                            Lout(179)  # STDPCAL
                            Lout(107)  # WRITELN

                def DumpStdProc(sp_stmt: Stmt) -> None:
                    """Emit I-code for ``EXIT`` branches and built-in file, heap, string, memory, and unit procedures."""
                    proc = sp_stmt.ProcpN
                    Key = proc.Key
                    if Key == 29:  # EXIT
                        lLev = sp_stmt.pArgList.LeftArg.PFlev + 1
                        OutGoto(lLev, self.Display[lLev].ExitLabel)
                    else:
                        pArgs = sp_stmt.pArgList
                        Lout(190)  # PRMLIST
                        if Key in (1, 15, 20, 27):  # NEW, CLOSE, SEEK, DISPOSE
                            pArgs = ArgAddr(pArgs)
                            pArgs = ArgVal2(pArgs)
                        elif Key in (2, 3, 4, 5, 12):  # MARK, RELEASE, GET, PUT, PAGE
                            pArgs = ArgAddr(pArgs)
                        elif Key in (6, 7):  # RESET, REWRITE
                            SubOp = pArgs.BinSubOp
                            pArgs = ArgAddr(pArgs)
                            if pArgs is not None:
                                pArgs = ArgAddr(pArgs)
                            else:
                                Lout(186)  # VALPRM4
                                Lout(23)   # NIL
                            Lout(185)  # VALPRM2
                            OutIntCnst(SubOp, 2)
                        elif Key in (16, 24):  # DELETE, FILLCHAR
                            pArgs = ArgAddr(pArgs)
                            pArgs = ArgVal2(pArgs)
                            pArgs = ArgVal2(pArgs)
                        elif Key in (17, 22, 23):  # INSERT, MOVELEFT, MOVERIGHT
                            pArgs = ArgAddr(pArgs)
                            pArgs = ArgAddr(pArgs)
                            pArgs = ArgVal2(pArgs)
                        elif Key in (18, 19, 28):  # UNITREAD, UNITWRITE, UNITSTATUS
                            pArgs = ArgVal2(pArgs)
                            pArgs = ArgAddr(pArgs)
                            pArgs = ArgVal2(pArgs)
                            if Key <= 19:
                                if pArgs is None:
                                    Lout(185)  # VALPRM2
                                    OutIntCnst(0, 2)
                                else:
                                    pArgs = ArgVal2(pArgs)
                                if pArgs is None:
                                    Lout(185)  # VALPRM2
                                    OutIntCnst(0, 2)
                                else:
                                    pArgs = ArgVal2(pArgs)
                        elif Key == 21:  # HALT
                            pass
                        elif Key == 25:  # UNITCLEAR
                            pArgs = ArgVal2(pArgs)
                        elif Key == 26:  # GOTOXY
                            pArgs = ArgVal2(pArgs)
                            pArgs = ArgVal2(pArgs)
                        Lout(179)  # STDPCAL
                        Lout(Key)

                proc = stmt.ProcpN
                if proc.PFdeclKind == DeclKind.STANDARD:
                    if 8 <= proc.Key <= 11:
                        ReadWrite(stmt)
                    else:
                        DumpStdProc(stmt)
                else:
                    DumpUCall(proc, stmt.pArgList, None, None, None)

            def FindLoHi(stmt: Stmt) -> None:
                """Allocate ``CASE`` internal labels and find the minimum (``Lo``) and maximum (``Hi``) selector values."""
                nonlocal Lo, Hi, ExitLabNo, ElseLabNo, ThisLabNo
                Lo = 32767
                Hi = -32768
                lStmt = stmt.CStmtList
                ExitLabNo = NextLabel()
                ElseLabNo = NextLabel()
                while lStmt is not None:
                    lpInt = lStmt.CaseVals
                    ThisLabNo = NextLabel()
                    while lpInt is not None:
                        if lpInt.IntVal > Hi:
                            Hi = lpInt.IntVal
                        if lpInt.IntVal < Lo:
                            Lo = lpInt.IntVal
                        lpInt = lpInt.NextInt
                    lStmt = lStmt.NextStmt

            def CaseIsSmaller(stmt: Stmt) -> bool:
                """Return ``True`` when a dense jump table takes fewer code bytes than linear ``IF-THEN-ELSE`` checks."""
                nonlocal USED, Unused
                USED = 0
                Unused = 0
                for val_i in range(Lo, Hi + 1):
                    found = False
                    lStmt = stmt.CStmtList
                    while lStmt is not None and not found:
                        lpInt = lStmt.CaseVals
                        while lpInt is not None:
                            if lpInt.IntVal == val_i:
                                USED += 1
                                found = True
                                break
                            else:
                                lpInt = lpInt.NextInt
                        if not found:
                            lStmt = lStmt.NextStmt
                    if not found:
                        Unused += 1
                # IF 24+6*used+2*unused < 4+10*used THEN use_case_statement
                return Unused < 2 * USED - 10

            def DumpCaseStmt(stmt: Stmt) -> None:
                """Emit a dense jump-table ``CASE`` statement (``CASETAB`` mode 0), arm bodies, and ``ENDCASE``."""
                nonlocal ThisLabNo
                Lout(200)  # CASEJ
                Expression(stmt.CaseExpr)
                Lout(201)  # CASETAB
                Lout(0)    # use a jump table
                Lout2(Lo)
                Lout2(Hi)
                Lout2(ElseLabNo)
                for val_i in range(Lo, Hi + 1):
                    ThisLabNo = ElseLabNo
                    lStmt = stmt.CStmtList
                    found = False
                    while lStmt is not None:
                        lpInt = lStmt.CaseVals
                        ThisLabNo += 1
                        while lpInt is not None:
                            if lpInt.IntVal == val_i:
                                found = True
                                break
                            else:
                                lpInt = lpInt.NextInt
                        if found:
                            break
                        lStmt = lStmt.NextStmt
                    if not found:
                        ThisLabNo = ElseLabNo
                    Lout2(ThisLabNo)
                lStmt = stmt.CStmtList
                ThisLabNo = ElseLabNo
                while lStmt is not None:
                    ThisLabNo += 1
                    Lout(192)  # ILAB
                    Lout2(ThisLabNo)
                    DumpStmt(lStmt.ThisCase)
                    Lout(193)  # JMP
                    Lout2(ExitLabNo)
                    lStmt = lStmt.NextStmt
                Lout(192)  # ILAB
                Lout2(ElseLabNo)
                DumpStmt(stmt.OtherStmt)
                Lout(192)  # ILAB
                Lout2(ExitLabNo)
                Lout(204)  # ENDCASE

            def DumpIfThenElse(stmt: Stmt) -> None:
                """Emit a sparse comparison-chain ``CASE`` statement (``CASETAB`` mode 1), arm bodies, and ``ENDCASE``."""
                nonlocal ThisLabNo
                Lout(200)  # CASEJ
                Expression(stmt.CaseExpr)
                Lout(201)  # CASETAB
                Lout(1)    # use if then else
                Lout2(Lo)
                Lout2(Hi)
                Lout2(ElseLabNo)
                Lout2(USED)
                for val_i in range(Lo, Hi + 1):
                    ThisLabNo = ElseLabNo
                    lStmt = stmt.CStmtList
                    found = False
                    while lStmt is not None:
                        lpInt = lStmt.CaseVals
                        ThisLabNo += 1
                        while lpInt is not None:
                            if lpInt.IntVal == val_i:
                                Lout2(val_i)
                                Lout2(ThisLabNo)
                                found = True
                                break
                            else:
                                lpInt = lpInt.NextInt
                        if found:
                            break
                        lStmt = lStmt.NextStmt
                lStmt = stmt.CStmtList
                ThisLabNo = ElseLabNo
                while lStmt is not None:
                    ThisLabNo += 1
                    Lout(192)  # ILAB
                    Lout2(ThisLabNo)
                    DumpStmt(lStmt.ThisCase)
                    Lout(193)  # JMP
                    Lout2(ExitLabNo)
                    lStmt = lStmt.NextStmt
                Lout(192)  # ILAB
                Lout2(ElseLabNo)
                DumpStmt(stmt.OtherStmt)
                Lout(192)  # ILAB
                Lout2(ExitLabNo)
                Lout(204)  # ENDCASE

            def VarInExpr(v: Optional[N], e: Optional[N]) -> bool:
                """Return ``True`` if register node ``v`` is referenced anywhere inside expression ``e``."""
                r = False
                if e is not None:
                    if e.Node == NodeKind.IDENTNODE:
                        r = v is e
                    elif e.Node == NodeKind.UNNODE:
                        if e.UnOp in (12, 15, 43):
                            r = VarInExpr(v, e.UnArg)
                        elif e.UnOp in (23, 31):
                            r = False
                        else:
                            r = VarInExpr(v, e.UnArg)
                    elif e.Node == NodeKind.BINNODE:
                        if e.BinOp in (46, 47):
                            r = VarInExpr(v, e.RightArg)
                        else:
                            r = VarInExpr(v, e.LeftArg) or VarInExpr(v, e.RightArg)
                    elif e.Node == NodeKind.TRINODE:
                        if e.TriOp == 16:
                            r = VarInExpr(v, e.Tri1) or VarInExpr(v, e.Tri2)
                        else:
                            r = False
                    elif e.Node == NodeKind.CSTNODE:
                        r = False
                    elif e.Node == NodeKind.REGISTER:
                        r = v.Reg == e.Reg
                        if e.LoadExpr is not None:
                            r = r or VarInExpr(v, e.LoadExpr)
                    elif e.Node == NodeKind.ASGNNODE:
                        r = (
                            VarInExpr(v, e.AsgnVar)
                            or VarInExpr(v, e.AsgnExpr)
                            or VarInExpr(v, e.AsgnpN)
                        )
                return r

            while fStmt is not None:
                if self.Pass2Listing:
                    if fStmt.StmtNumb != self.LastLine:
                        if fStmt.StmtNumb != 0:
                            if fStmt.StmtNumb < 0:
                                TrueLn = fStmt.StmtNumb + 65536
                                if TrueLn > MAXLNUM:
                                    self.AsmListOk = False
                                    self.Pass2Listing = False
                            elif fStmt.StmtNumb > MAXLNUM:
                                self.AsmListOk = False
                                self.Pass2Listing = False

                            if self.Pass2Listing:
                                if self.NewListFile:
                                    Lout(205)  # line number
                                    Lout2(-1)  # listing file
                                    Filename = self.ListingFCBP.Filename
                                    Len = len(Filename)
                                    Lout(Len)
                                    for idx in range(Len):
                                        Lout(ord(Filename[idx]))
                                    self.NewListFile = False

                                if self.NewAsmStatus:
                                    Lout(205)  # line number
                                    Lout2(-2)  # new Asm status
                                    Lout(1 if self.ShowAsmCode else 0)
                                    self.NewAsmStatus = False

                                Lout(205)  # line number
                                Lout2(fStmt.StmtNumb)
                                self.LastLine = fStmt.StmtNumb

                if fStmt.StmtOp == StmtTypes.BEGINST:
                    DumpStmt(fStmt.SubSt)
                elif fStmt.StmtOp == StmtTypes.ASSIGNST:
                    g = True
                    if fStmt.AssOp == 34 and fStmt.Flippable:
                        if fStmt.AssVar.Node == NodeKind.REGISTER:
                            if A1st <= fStmt.AssVar.Reg <= Anth:
                                ass_expr = fStmt.AssExpr
                                if ass_expr.Node == NodeKind.BINNODE:
                                    if ass_expr.BinOp == 65:
                                        if ass_expr.RightArg.Node == NodeKind.UNNODE:
                                            if ass_expr.RightArg.UnOp == 49:
                                                left_arg = ass_expr.LeftArg
                                                if left_arg.Node == NodeKind.BINNODE:
                                                    if left_arg.BinOp == 178:  # sfcall
                                                        ll_arg = left_arg.LeftArg
                                                        if (
                                                            ll_arg.Node == NodeKind.IDENTNODE
                                                            and ll_arg.Key == 10  # ORD
                                                        ):
                                                            if not VarInExpr(
                                                                fStmt.AssVar, ass_expr.RightArg
                                                            ):
                                                                g = False
                    if g:
                        Lout(fStmt.AssOp)
                        if 32 <= fStmt.AssOp <= 35:
                            if fStmt.Flippable:
                                Lout(1)
                                Expression(fStmt.AssExpr)
                                Expression(fStmt.AssVar)
                            else:
                                Lout(0)
                                Expression(fStmt.AssVar)
                                Expression(fStmt.AssExpr)
                        else:
                            if fStmt.AssOp == 36:  # MULTASS
                                Lout(0)
                                Lout2(fStmt.AssSubOp)
                            elif fStmt.AssOp in (37, 39, 41, 42):
                                Lout(fStmt.AssSubOp)
                            elif fStmt.AssOp == 40:  # PAOCASS
                                Lout(fStmt.AssSubOp)
                                Lout(fStmt.AssSubOp)
                            Expression(fStmt.AssVar)
                            Expression(fStmt.AssExpr)
                    else:
                        Stmt1 = fStmt.copy()
                        Stmt1.AssExpr = fStmt.AssExpr.LeftArg.RightArg.LeftArg
                        Stmt1.NextStmt = None
                        Stmt2 = fStmt.copy()
                        Stmt2.AssOp = 41
                        Stmt2.AssSubOp = 2
                        Stmt2.AssExpr = fStmt.AssExpr.RightArg.UnArg
                        Stmt2.NextStmt = None
                        DumpStmt(Stmt1)
                        DumpStmt(Stmt2)
                elif fStmt.StmtOp == StmtTypes.IFST:
                    g = True
                    if fStmt.ThenSt is not None:
                        if fStmt.ThenSt.StmtOp == StmtTypes.GOTOST:
                            if fStmt.ThenSt.LabLev == self.Level:
                                g = False
                                Lout(195)  # JTRUE
                                Lout2(fStmt.ThenSt.GotoLab.ILabelNo)
                    if g:
                        Lab1 = NextLabel()
                        Lout(194)  # JFALSE
                        Lout2(Lab1)
                        Expression(fStmt.IfExpr)
                        DumpStmt(fStmt.ThenSt)
                        if fStmt.ElseSt is not None:
                            Lab2 = NextLabel()
                            Lout(193)  # JUMP
                            Lout2(Lab2)
                        Lout(192)  # DEFLAB
                        Lout2(Lab1)
                        if fStmt.ElseSt is not None:
                            DumpStmt(fStmt.ElseSt)
                            Lout(192)  # DEFLAB
                            Lout2(Lab2)
                    else:
                        Expression(fStmt.IfExpr)
                        if fStmt.ElseSt is not None:
                            DumpStmt(fStmt.ElseSt)
                elif fStmt.StmtOp == StmtTypes.WHILEST:
                    Lab1 = NextLabel()
                    Lout(192)  # DEFLAB
                    Lout2(Lab1)
                    if fStmt.CondExpr is None:
                        g = True
                    elif fStmt.CondExpr.Node != NodeKind.CSTNODE:
                        g = True
                    else:
                        g = fStmt.CondExpr.CstValu.Ivalu == 0
                    if g:
                        Lab2 = NextLabel()
                        Lout(194)  # JFALSE
                        Lout2(Lab2)
                        Expression(fStmt.CondExpr)
                    DumpStmt(fStmt.LoopStmt)
                    Lout(193)  # JUMP
                    Lout2(Lab1)
                    if g:
                        Lout(192)  # DEFLAB
                        Lout2(Lab2)
                elif fStmt.StmtOp == StmtTypes.REPST:
                    Lab1 = NextLabel()
                    Lout(192)  # DEFLAB
                    Lout2(Lab1)
                    DumpStmt(fStmt.LoopStmt)
                    if fStmt.CondExpr is None:
                        g = True
                    elif fStmt.CondExpr.Node != NodeKind.CSTNODE:
                        g = True
                    else:
                        g = fStmt.CondExpr.CstValu.Ivalu != 0
                    if g:
                        Lout(194)  # JFALSE
                        Lout2(Lab1)
                        Expression(fStmt.CondExpr)
                    else:
                        Lout(193)  # JUMP
                        Lout2(Lab1)
                elif fStmt.StmtOp == StmtTypes.WITHST:
                    with_level += 1
                    Lout(44)  # WITHBEG
                    Lout(with_level)

                    IsPtr = 0
                    wvar = fStmt.WithVar
                    if wvar.Node == NodeKind.UNNODE:
                        if wvar.UnOp == 12:  # ^
                            uarg = wvar.UnArg
                            if uarg.Node == NodeKind.IDENTNODE:
                                if uarg.Class == NameClass.VARS:
                                    if uarg.Vkind == AccessKind.DRCT and (
                                        uarg.Vlev == self.Level or UnitIsRegular(uarg.Vlev)
                                    ):
                                        IsPtr = 1
                                        Lout(IsPtr)
                                        Selector(uarg)
                            elif uarg.Node == NodeKind.REGISTER:
                                IsPtr = 1
                                Lout(IsPtr)
                                Selector(uarg)
                    elif wvar.Node == NodeKind.IDENTNODE:
                        if wvar.Class == NameClass.VARS:
                            if wvar.Vkind == AccessKind.INDRCT and wvar.Vlev == self.Level:
                                IsPtr = 1
                                Lout(IsPtr)
                                wvar.Vkind = AccessKind.DRCT
                                Selector(wvar)
                                wvar.Vkind = AccessKind.INDRCT

                    if IsPtr == 0:
                        Lout(0)
                        Selector(wvar)
                    DumpStmt(fStmt.WithBody)
                    Lout(45)  # WITHEND
                    Lout(with_level)
                    with_level -= 1
                elif fStmt.StmtOp == StmtTypes.METHODCALL:
                    DumpUCall(
                        fStmt.AssVar.TripN,
                        fStmt.AssVar.Tri2,
                        fStmt.AssVar.Tri1,
                        fStmt.AssVar.OrigTri1,
                        fStmt.AssVar.TriSuper,
                    )
                elif fStmt.StmtOp == StmtTypes.CALLST:
                    DumpCallStmt(fStmt)
                elif fStmt.StmtOp == StmtTypes.GOTOST:
                    OutGoto(fStmt.LabLev, fStmt.GotoLab)
                elif fStmt.StmtOp in (StmtTypes.FORTOST, StmtTypes.FORDOWNST):
                    Lout(202)  # FOR
                    Lout(fStmt.ForSize)
                    Selector(fStmt.ForVar)
                    Expression(fStmt.ForInit)
                    Expression(fStmt.ForLimit)
                    if fStmt.StmtOp == StmtTypes.FORTOST:
                        OutIntCnst(1, 2)
                    else:
                        OutIntCnst(-1, 2)
                    DumpStmt(fStmt.ForSt)
                    Lout(203)  # FOREND
                elif fStmt.StmtOp == StmtTypes.CASEST:
                    FindLoHi(fStmt)
                    if CaseIsSmaller(fStmt):
                        DumpCaseStmt(fStmt)
                    else:
                        DumpIfThenElse(fStmt)
                elif fStmt.StmtOp == StmtTypes.LABEDST:
                    st_lab = fStmt.StLab
                    if st_lab.GlobRefNo < 0:
                        lOp = 196  # LOCULAB
                    else:
                        lOp = 197  # GLOULAB
                    Lout(lOp)
                    Lout2(st_lab.LabelNo)
                    Lout2(st_lab.ILabelNo)
                    if st_lab.GlobRefNo >= 0:
                        Lout2(st_lab.GlobRefNo)
                    DumpStmt(fStmt.LabStmt)
                elif fStmt.StmtOp == StmtTypes.TEMPST:
                    Lout(0xCE)  # TEMPSTMT
                    Lout2(fStmt.TempCSEregs.iMask)

                fStmt = fStmt.NextStmt

        # ---- Main body of Dump ----
        if ProcN.Class == NameClass.UNITS:
            self.Out(244)
            uname = alfa8(ProcN.Name)
            for i in range(8):
                self.Out(ord(uname[i]))
            self.Out2(0)
            self.Out2(0)  # Text address
            self.Out2(0)
            self.Out2(0)  # Text size
            self.Out2(ProcN.ULc)  # Global size
            self.Out(int(ProcN.Ukind))  # Unit Kind
        else:
            LabNo = 0
            with_level = 0
            NextExtNo = 0
            lByteNo = 0
            ExtList = None
            UnitSet = set()
            IntrinSet = set()

            # Assign internal label numbers to user labels
            GlobalLabels = False
            lpLabel = self.Display[self.Level].Labels
            while lpLabel is not None:
                lpLabel.ILabelNo = NextLabel()
                if lpLabel.GlobRefNo >= 0:
                    GlobalLabels = True
                lpLabel = lpLabel.NextLabel

            # Assign internal label number to exit label
            lpLabel = self.Display[self.Level].ExitLabel
            lpLabel.ILabelNo = NextLabel()
            if lpLabel.GlobRefNo >= 0:
                GlobalLabels = True

            # Begin Module
            self.Out(240)
            uName = alfa8(ProcN.Name)
            if ProcN.RtnNo < 0:
                lName = uName
            else:
                lName = LocalName(ProcN.RtnNo)
            for i in range(8):
                self.Out(ord(lName[i]))
            if CallingUnits:
                for i in range(8):
                    ch = uName[i]
                    if 'a' <= ch <= 'z':
                        self.Out(ord(ch) - 32)
                    else:
                        self.Out(ord(ch))
            else:
                for i in range(8):
                    self.Out(ord(uName[i]))

            Father = '        '
            if ProcN.PFdecl == PFkind.METHDECL:
                if self.ThisClass is not None:
                    if self.ThisClass.ItsId is not None:
                        Father = alfa8(self.ThisClass.ItsId.Name)
            for i in range(8):
                self.Out(ord(Father[i]))

            seg_name = alfa8(self.SegName)
            for i in range(8):
                self.Out(ord(seg_name[i]))
            self.Out(1 if ProcN.Class == NameClass.FUNC else 0)
            self.Out(self.Level)
            self.Out2(ProcN.Lc)
            self.Out2(ProcN.ParmBytes)
            self.Out(2 * (1 if self.StkXFlag else 0) + (1 if GlobalLabels else 0))
            self.Out2(self.RegMask.iMask)

            # Copy large value parameters
            # Note: in Pascal N's variant record, PROC/FUNC parameters have
            # PFdeclKind = DECLARED (1 = Ord(INDRCT)) overlaid on Vkind, so
            # Vkind = DRCT is only True when Class = VARS and Vkind = DRCT.
            lpN = ProcN.PFargList
            lLc = ProcN.ParmBytes
            while lpN is not None:
                if lpN.Class == NameClass.VARS and lpN.Vkind == AccessKind.DRCT:
                    lSize = self.FullBytes(lpN.IdType)
                    if lSize > 4 and lpN.IdType.Form != TypeForms.SETS:
                        lLc -= 4
                        Lout(36)  # MULTASS
                        Lout(1)
                        Lout2(lSize)
                        Lout(2)   # LOCAL
                        Lout2(lpN.Voff)
                        Lout(12)  # PTR
                        Lout(2)   # LOCAL
                        Lout2(lLc)
                    else:
                        lLc -= lSize
                        if odd(lSize):
                            lLc -= 1
                else:
                    lLc -= 4
                lpN = lpN.Next

            DumpStmt(ProcTree)

            for i in range(lByteNo):
                self.Out(lBuff[i])

            if self.Pass2Listing:
                self.Out(205)  # line number
                self.Out2(-3)  # flush listing to TotalLines
                self.Out2(self.TotalLines)
                self.LastLine = self.TotalLines

            # End Module
            self.Out(254)
            if self.DbugFlag:
                self.Out(1)
            else:
                self.Out(0)
