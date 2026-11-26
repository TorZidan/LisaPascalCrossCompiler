"""Statement and expression parser for the Lisa Pascal Front End."""

from __future__ import annotations

import sys
from typing import Callable, Optional

from frontend_base import (
    MAXDISPLAY,
    AccessKind,
    Attr,
    DeclKind,
    FacBegSys,
    IntList,
    LabRec,
    N,
    NameClass,
    NodeKind,
    PFkind,
    SelectSys,
    StatBegSys,
    Stmt,
    StmtTypes,
    StrValRec,
    Symbol,
    T,
    TypeForms,
    Where,
)
from lisalib import alfa8, f32, i16, i32, odd, pdiv

# Prebuilt symbol and name-class sets for fast set unions without allocation churn
_SET_RPAREN = frozenset({Symbol.RPARENSY})
_SET_LPAREN = frozenset({Symbol.LPARENSY})
_SET_UPARROW = frozenset({Symbol.UPARROWSY})
_SET_ASSIGN = frozenset({Symbol.ASSIGNSY})
_SET_IDENT = frozenset({Symbol.IDENTSY})
_SET_DO = frozenset({Symbol.DOSY})
_SET_ELSE = frozenset({Symbol.ELSESY})
_SET_THEN = frozenset({Symbol.THENSY})
_SET_SEMI = frozenset({Symbol.SEMISY})
_SET_SEMI_END = frozenset({Symbol.SEMISY, Symbol.ENDSY})
_SET_UNTIL_SEMI = frozenset({Symbol.UNTILSY, Symbol.SEMISY})
_SET_COMMA_DO = frozenset({Symbol.COMMASY, Symbol.DOSY})
_SET_COMMA_RBRACK = frozenset({Symbol.COMMASY, Symbol.RBRACKSY})
_SET_COMMA_COLON_RBRACK = frozenset({Symbol.COMMASY, Symbol.COLONSY, Symbol.RBRACKSY})
_SET_COMMA_RPAREN = frozenset({Symbol.COMMASY, Symbol.RPARENSY})
_SET_COMMA_COLON = frozenset({Symbol.COMMASY, Symbol.COLONSY})
_SET_COMMA_COLON_RPAREN = frozenset({Symbol.COMMASY, Symbol.COLONSY, Symbol.RPARENSY})
_SET_OF_COMMA_COLON = frozenset({Symbol.OFSY, Symbol.COMMASY, Symbol.COLONSY})
_SET_FOR_SYNC1 = frozenset({Symbol.ASSIGNSY, Symbol.TOSY, Symbol.DOWNTOSY, Symbol.DOSY})
_SET_FOR_SYNC2 = frozenset({Symbol.TOSY, Symbol.DOWNTOSY, Symbol.DOSY})

_MULTOPS = frozenset({
    Symbol.DIVSY, Symbol.STARSY, Symbol.MODSY, Symbol.ANDSY, Symbol.SLASHSY,
})
_ADDOPS = frozenset({Symbol.PLUSSY, Symbol.MINUSSY, Symbol.ORSY})
_RELOPS = frozenset({
    Symbol.LTSY, Symbol.GTSY, Symbol.LESY, Symbol.GESY,
    Symbol.EQSY, Symbol.NESY, Symbol.INSY,
})

_SEARCH_VARS = frozenset({NameClass.VARS})
_SEARCH_TYPES = frozenset({NameClass.TYPES})
_SEARCH_PROC_FUNC = frozenset({NameClass.PROC, NameClass.FUNC})
_SEARCH_VAR_FLD_FUNC_PROC = frozenset({
    NameClass.VARS, NameClass.FIELD, NameClass.FUNC, NameClass.PROC,
})
_SEARCH_VAR_FLD_FUNC_TYP = frozenset({
    NameClass.VARS, NameClass.FIELD, NameClass.FUNC, NameClass.TYPES,
})
_SEARCH_VAR_FLD_FUNC_CST_TYP = frozenset({
    NameClass.VARS, NameClass.FIELD, NameClass.FUNC, NameClass.CONSTS, NameClass.TYPES,
})
_SEARCH_VAR_FLD_PROC_FUNC_TYP = frozenset({
    NameClass.VARS, NameClass.FIELD, NameClass.PROC, NameClass.FUNC, NameClass.TYPES,
})


class BodyMixin:
    """Procedure/program body parser and AST builder: variable/field/method
    selectors, expression parsing and type/range checking, standard and
    user/method procedure and function calls, and structured statements."""

    # ---- AST node and type/size coercion helpers ----

    @staticmethod
    def _NewBinNode(fBinOp: int, fLeftArg: Optional[N], FrightArg: Optional[N]) -> N:
        """Allocate and initialize a binary AST node (`BINNODE`) with opcode `fBinOp`."""
        lpN = N(NodeKind.BINNODE)
        lpN.BinOp = fBinOp
        lpN.BinSubOp = 0
        lpN.LeftArg = fLeftArg
        lpN.RightArg = FrightArg
        return lpN

    @staticmethod
    def _NewUnNode(fUnOp: int, fUnArg: Optional[N]) -> N:
        """Allocate and initialize a unary AST node (`UNNODE`) with opcode `fUnOp`."""
        lpN = N(NodeKind.UNNODE)
        lpN.UnOp = fUnOp
        lpN.UnSubOp = 0
        lpN.UnArg = fUnArg
        return lpN

    def _MakeScSize(self, FAttr: Attr, ToSize: int) -> None:
        """Coerce scalar operand `FAttr` to byte width `ToSize` (1, 2, or 4).

        Updates constant nodes directly with compile-time range checks, or wraps
        runtime expressions in an integer size-conversion unary node (plus `TRAPV`
        when narrowing under `$OV+`).
        """
        lSize = FAttr.ASize
        if lSize != ToSize:
            lpT: Optional[T] = None
            Op = 0
            if ToSize == 1:
                lpT = self.SIntPtr
                if lSize == 2:
                    Op = 51  # INT21
                else:
                    Op = 53  # INT41
            elif ToSize == 2:
                lpT = self.IntPtr
                if lSize == 1:
                    Op = 48  # INT12
                else:
                    Op = 52  # INT42
            elif ToSize == 4:
                lpT = self.LIntPtr
                if lSize == 1:
                    Op = 50  # INT14
                else:
                    Op = 49  # INT24
            if FAttr.TreePtr is not None:
                if FAttr.TreePtr.Node == NodeKind.CSTNODE:
                    FAttr.TreePtr.CstType = lpT
                    if Op == 52:
                        if FAttr.TreePtr.CstValu.Ivalu < -32768 or FAttr.TreePtr.CstValu.Ivalu > 32767:
                            self.Error(169)
                    elif Op == 51 or Op == 53:
                        if FAttr.TreePtr.CstValu.Ivalu < -128 or FAttr.TreePtr.CstValu.Ivalu > 127:
                            self.Error(169)
                else:
                    FAttr.TreePtr = self._NewUnNode(Op, FAttr.TreePtr)
                    if self.OflowFlag:
                        if 51 <= Op <= 53:
                            FAttr.TreePtr = self._NewUnNode(0x8C, FAttr.TreePtr)  # TRAPV
            FAttr.ASize = ToSize

    def _MatchISizes(self, AAttr: Attr, BAttr: Attr) -> None:
        """Widen the narrower of two integer operand attributes so their byte sizes match."""
        ASize = AAttr.ASize
        BSize = BAttr.ASize
        if ASize != BSize:
            if ASize < BSize:
                self._MakeScSize(AAttr, BSize)
            else:
                self._MakeScSize(BAttr, ASize)

    def _MinSize2(self, FAttr: Attr) -> None:
        """Promote a 1-byte integer operand in `FAttr` to at least 2 bytes (`Integer`)."""
        if FAttr.ASize < 2:
            self._MakeScSize(FAttr, 2)

    def _MakeSetSize(self, FAttr: Attr, fSize: int) -> None:
        """Wrap set expression `FAttr` in an `ADJSET` node to resize it to `fSize` bytes."""
        FAttr.TreePtr = self._NewUnNode(170, FAttr.TreePtr)  # ADJSET
        FAttr.TreePtr.UnSubOp = fSize * 256 + FAttr.ASize
        FAttr.ASize = fSize

    def _MatchSetSizes(self, AAttr: Attr, BAttr: Attr) -> None:
        """Adjust two set operands to a common byte size (or dynamic size `0` if either is dynamic)."""
        if AAttr.ASize != BAttr.ASize:
            if AAttr.ASize == 0:
                self._MakeSetSize(BAttr, 0)
            elif BAttr.ASize == 0:
                self._MakeSetSize(AAttr, 0)
            elif AAttr.ASize > BAttr.ASize:
                self._MakeSetSize(BAttr, AAttr.ASize)
            else:
                self._MakeSetSize(AAttr, BAttr.ASize)

    def _Float(self, FAttr: Attr) -> None:
        """Convert an integer expression in `FAttr` to a 4-byte `Real` via `FLOAT44`."""
        self._MakeScSize(FAttr, 4)
        FAttr.TreePtr = self._NewUnNode(56, FAttr.TreePtr)  # FLOAT44
        FAttr.Typtr = self.RealPtr
        FAttr.ASize = 4

    def _PAoC(self, FpT: Optional[T]) -> bool:
        """Return `True` if `FpT` is a 1-based `PACKED ARRAY [1..N] OF Char` type."""
        if FpT is not None:
            if FpT.Form == TypeForms.ARRAYS and FpT.ArrayOf == self.CharPtr and FpT.PckdArr:
                if self.CompTypes(FpT.IndexedBy, self.IntPtr):
                    Lo, Hi = self.GetBounds(FpT.IndexedBy)
                    return Lo == 1
        return False

    def _InsertRangeCheck(self, MatchType: T, fAttr: Attr) -> None:
        """Check `fAttr` against subrange `MatchType`, folding constant errors or adding `RCHECK`."""
        if MatchType.Form == TypeForms.SUBRANGE:
            if (
                MatchType != self.SIntPtr
                and MatchType != self.IntPtr
                and fAttr.ASize <= 2
                and self.FullBytes(MatchType) <= 2
            ):
                Lo, Hi = self.GetBounds(MatchType)
                if fAttr.TreePtr is not None and fAttr.TreePtr.Node == NodeKind.CSTNODE:
                    if fAttr.TreePtr.CstValu.Ivalu < Lo or fAttr.TreePtr.CstValu.Ivalu > Hi:
                        self.Error(169)
                else:
                    self._MakeScSize(fAttr, 2)
                    fAttr.TreePtr = self._NewBinNode(46, None, fAttr.TreePtr)  # RCHECK
                    fAttr.TreePtr.LeftPt = MatchType

    def _CheckSubClass(self, FIdType: T, ToClass: str) -> None:
        """Emit a runtime Clascal object class check (`%_CkObCp` or `%_CkObCn`) for `gAttr`.

        Calls `%_CkObCp` with the class method-table descriptor when `ToClass` is declared
        in the current compilation, or `%_CkObCn` with the 8-byte class name otherwise.
        """
        lTreePtr = self.gAttr.TreePtr
        if FIdType.NeedsInit:
            # ToClass declared in this compilation
            Funct = self.CkObCpPtr  # %_CkObCp
            lpN = N(NodeKind.IDENTNODE)
            lpN.IdType = self.LIntPtr
            lpN.Next = None
            lpN.Class = NameClass.VARS
            lpN.Vkind = AccessKind.DRCT
            lpN.InRegister = -1
            lpN.Vlev = FIdType.MethodLevel
            lpN.Voff = FIdType.MethodOff
        else:
            # ToClass declared in another unit
            Funct = self.CkObCnPtr  # %_CkObCn
            lpN = N(NodeKind.CSTNODE)
            lpN.CstValu.SvaluLen = 8
            lpN.CstValu.Svalu = StrValRec(ToClass, None)
            cst_type = T(TypeForms.SCONST)
            cst_type.FType = False
            cst_type.Bits = 0
            cst_type.Bytes = 8
            cst_type.StringLen = 8
            lpN.CstType = cst_type

        self.gAttr.TreePtr = self._NewBinNode(0, lpN, None)
        self.gAttr.TreePtr = self._NewBinNode(0, lTreePtr, self.gAttr.TreePtr)
        self.gAttr.TreePtr = self._NewBinNode(176, Funct, self.gAttr.TreePtr)  # USRFUNC

    def _TypeConvert(
        self,
        FSys: set[Symbol] | frozenset[Symbol],
        GetArg: Callable[[set[Symbol] | frozenset[Symbol]], None],
        FpN: N,
    ) -> Optional[N]:
        """Parse an explicit `<TypeId>(arg)` cast using `GetArg` for expression or variable contexts.

        Adjusts scalar byte sizes when legal, emits Clascal subclass checks under `$R+`,
        and returns the resulting AST node.
        """
        self.Scan()
        GetArg(FSys | _SET_RPAREN)
        if FpN.IdType is not None:
            lSize = self.FullBytes(FpN.IdType)
            if self.gAttr.ASize == lSize:
                self.gAttr.Typtr = FpN.IdType
            elif self.gAttr.Typtr is not None:
                if (
                    self.gAttr.Typtr.Form <= TypeForms.POINTERS
                    and not self.CompTypes(self.gAttr.Typtr, self.RealPtr)
                    and (lSize == 1 or lSize == 2 or lSize == 4)
                ):
                    self._MakeScSize(self.gAttr, lSize)
                    self.gAttr.Typtr = FpN.IdType
                else:
                    self.Error(178)  # types don't match in size
            if self.RangeFlag:
                if FpN.IdType.Form == TypeForms.CLASSES:
                    self._CheckSubClass(FpN.IdType, FpN.Name)
        res_pN = self.gAttr.TreePtr
        if self.Token == Symbol.RPARENSY:
            self.Scan()
        else:
            self.Error(32)
        return res_pN

    @staticmethod
    def _SuperStar(Super: Optional[T], Sub: Optional[T]) -> Optional[T]:
        """Return `Super` if Clascal class `Sub` is equal to or inherits from `Super`, else `None`."""
        if Sub == Super:
            return Super
        while Sub is not None:
            if Sub.SuperClass == Super:
                return Super
            Sub = Sub.SuperClass
        return None

    # ---- Select and Selector ----

    def _Select(
        self,
        FSys: set[Symbol] | frozenset[Symbol],
        FAttr: Attr,
        Pckd: bool,
        PckdStorage: bool,
        SawClassId: bool,
    ) -> tuple[bool, bool, bool]:
        """Parse postfix selectors (`[...]`, `.field`/`.method`, `^`) applied to `FAttr`.

        Builds array/string `INDEX` nodes (with optional range checks), record/class `FIELD`
        accesses (including bit-field extraction and Clascal handle double-dereferencing),
        `METHODCALL` nodes (including superclass/creation qualification), and pointer/file
        dereferences, returning `(Pckd, PckdStorage, SawClassId)`.
        """
        SuperpT: Optional[T] = None
        if self.Token not in (SelectSys | FSys):
            self.Skip(28, SelectSys | FSys)
        while self.Token in SelectSys:
            if self.Token == Symbol.LBRACKSY:
                while True:
                    if FAttr.Typtr is not None:
                        if (
                            FAttr.Typtr.Form != TypeForms.ARRAYS
                            and FAttr.Typtr.Form != TypeForms.STRINGS
                        ):
                            self.Error(135)
                            FAttr.Typtr = None
                    self.Scan()
                    self._Expression(FSys | _SET_COMMA_RBRACK)
                    lpT = self.gAttr.Typtr
                    self._MakeScSize(self.gAttr, 2)
                    lpN = N(NodeKind.TRINODE)
                    lpN.TriOp = 16  # INDEX
                    lpN.TriPt = FAttr.Typtr
                    lpN.Tri1 = FAttr.TreePtr
                    lpN.OrigTri1 = lpN.Tri1
                    lpN.Tri2 = self.gAttr.TreePtr
                    FAttr.TreePtr = lpN
                    if FAttr.Typtr is not None:
                        ty = FAttr.Typtr
                        if ty.Form == TypeForms.ARRAYS:
                            if not self.CompTypes(ty.IndexedBy, lpT):
                                self.Error(136)
                            Lo, Hi = self.GetBounds(ty.IndexedBy)
                            if self.RangeFlag and self.gAttr.TreePtr is not None:
                                if self.gAttr.TreePtr.Node == NodeKind.CSTNODE:
                                    if (
                                        self.gAttr.TreePtr.CstValu.Ivalu < Lo
                                        or self.gAttr.TreePtr.CstValu.Ivalu > Hi
                                    ):
                                        self.Error(169)
                                else:
                                    FAttr.TreePtr.Tri2 = self._NewBinNode(
                                        46, None, FAttr.TreePtr.Tri2  # RCHECK
                                    )
                                    FAttr.TreePtr.Tri2.LeftPt = ty.IndexedBy
                            PckdStorage = ty.BitPackd
                            Pckd = ty.PckdArr
                            FAttr.Typtr = ty.ArrayOf
                            if PckdStorage:
                                FAttr.ASize = 2
                            else:
                                FAttr.ASize = self.FullBytes(FAttr.Typtr)
                        else:  # Form == STRINGS
                            if not self.CompTypes(lpT, self.IntPtr):
                                self.Error(136)
                            if self.RangeFlag and self.gAttr.TreePtr is not None:
                                if self.gAttr.TreePtr.Node == NodeKind.CSTNODE:
                                    if (
                                        self.gAttr.TreePtr.CstValu.Ivalu < 0
                                        or self.gAttr.TreePtr.CstValu.Ivalu > ty.StringLen
                                    ):
                                        self.Error(169)
                                else:
                                    FAttr.TreePtr.Tri2 = self._NewBinNode(
                                        46, None, FAttr.TreePtr.Tri2  # RCHECK
                                    )
                                    FAttr.TreePtr.Tri2.LeftPt = FAttr.Typtr
                            Pckd = True
                            PckdStorage = True
                            FAttr.Typtr = self.CharPtr
                            FAttr.ASize = 2
                    if self.Token != Symbol.COMMASY:
                        break
                if self.Token == Symbol.RBRACKSY:
                    self.Scan()
                else:
                    self.Error(34)

            elif self.Token == Symbol.PERIODSY:
                if FAttr.Typtr is not None:
                    if (
                        FAttr.Typtr.Form != TypeForms.RECORDS
                        and FAttr.Typtr.Form != TypeForms.CLASSES
                    ):
                        self.Error(137)
                        FAttr.Typtr = None
                self.Scan()
                if self.Token == Symbol.IDENTSY:
                    if FAttr.Typtr is not None:
                        if FAttr.Typtr.Form == TypeForms.RECORDS:
                            Pckd = FAttr.Typtr.PckdRec
                            lpN = self.SearchLocal(FAttr.Typtr.Fields)
                            self.Scan()
                            FAttr.TreePtr = self._NewBinNode(15, FAttr.TreePtr, lpN)  # FIELD
                            if lpN is not None:
                                FAttr.Typtr = lpN.IdType
                                PckdStorage = lpN.PckdField
                                if PckdStorage:
                                    Lo, Hi = self.GetBounds(lpN.IdType)
                                    FAttr.ASize = 2
                                    FAttr.TreePtr = self._NewUnNode(
                                        62 + (1 if Lo < 0 else 0),  # EXTUSFLD
                                        FAttr.TreePtr,
                                    )
                                    NumBits = lpN.IdType.Bytes * 8 + lpN.IdType.Bits
                                    MyRightBit = 16 - lpN.BitOff - NumBits
                                    FAttr.TreePtr.UnSubOp = NumBits * 16 + MyRightBit
                                else:
                                    FAttr.ASize = self.FullBytes(FAttr.Typtr)
                            else:
                                self.Error(147)
                                FAttr.Typtr = None
                        else:  # a CLASSES field
                            Pckd = False
                            lpN, _HigherLevel = self.SearchClasses(FAttr.Typtr, False)
                            self.Scan()
                            if lpN is not None:
                                if lpN.Class == NameClass.FIELD:
                                    self.ExprDHandle = self.ExprDHandle + 1
                                    if SawClassId:
                                        self.Error(809)
                                        FAttr.Typtr = None
                                        FAttr.TreePtr = None
                                    else:
                                        FAttr.Typtr = lpN.IdType
                                        FAttr.TreePtr = self._NewBinNode(
                                            15,  # FIELD
                                            self._NewUnNode(
                                                12,  # POINTERS
                                                self._NewUnNode(12, FAttr.TreePtr),  # POINTERS
                                            ),
                                            lpN,
                                        )
                                        FAttr.ASize = self.FullBytes(FAttr.Typtr)
                                else:  # METHOD
                                    if lpN.MethodNo == 0:  # 'CREATE'
                                        if SawClassId:
                                            SuperpT = FAttr.Typtr
                                        else:
                                            self.Error(809)
                                        MpN = None
                                    else:
                                        if SawClassId:
                                            self.Ident = 'SELF    '
                                            lpN2 = self.SearchAll(_SEARCH_VARS)
                                            FAttr.TreePtr = lpN2
                                            if lpN2.IsSELF:
                                                SuperpT = self._SuperStar(FAttr.Typtr, lpN2.IdType)
                                            if SuperpT is None:
                                                self.Error(810)
                                        MpN = FAttr.TreePtr
                                    self._Call(FSys, lpN)
                                    tpN = N(NodeKind.TRINODE)
                                    tpN.TriOp = 184  # METHODCALL
                                    tpN.TripN = lpN
                                    tpN.Tri1 = MpN
                                    tpN.OrigTri1 = tpN.Tri1
                                    tpN.Tri2 = self.gAttr.TreePtr
                                    tpN.TriSuper = SuperpT
                                    FAttr.TreePtr = tpN
                                    FAttr.ASize = self.gAttr.ASize
                                    FAttr.Typtr = self.gAttr.Typtr
                                    SawClassId = False
                            else:
                                self.Error(147)
                                FAttr.Typtr = None
                                FAttr.TreePtr = None
                else:
                    self.Error(29)

            elif self.Token == Symbol.UPARROWSY:
                if FAttr.Typtr is not None:
                    if FAttr.Typtr.Form == TypeForms.FILES:
                        FAttr.Typtr = FAttr.Typtr.FileOf
                        if FAttr.Typtr == self.CharPtr:
                            Op = 14  # TEXT
                        else:
                            Op = 13  # FILUP
                        FAttr.TreePtr = self._NewUnNode(Op, FAttr.TreePtr)
                        FAttr.ASize = self.FullBytes(FAttr.Typtr)
                        if Op == 14:
                            FAttr.TreePtr = self._NewUnNode(62, FAttr.TreePtr)  # EXTUFLD
                            FAttr.TreePtr.UnSubOp = 8 * 16 + 8
                    elif FAttr.Typtr.Form == TypeForms.POINTERS:
                        FAttr.Typtr = FAttr.Typtr.PointerTo
                        if FAttr.Typtr is None:
                            self.Error(184)
                        FAttr.TreePtr = self._NewUnNode(12, FAttr.TreePtr)  # POINTERS
                        FAttr.ASize = self.FullBytes(FAttr.Typtr)
                    else:
                        self.Error(138)
                        FAttr.Typtr = None
                self.Scan()

            if self.Token not in (FSys | SelectSys):
                self.Skip(20, FSys | SelectSys)
            SuperpT = None

        return Pckd, PckdStorage, SawClassId

    def _SelectorVariable(self, FSys: set[Symbol] | frozenset[Symbol]) -> None:
        """Parse a variable or type-cast variable reference within a selector, rejecting packed targets."""
        if self.Token == Symbol.IDENTSY:
            lpN = self.SearchAll(_SEARCH_VAR_FLD_FUNC_TYP)
            self.Scan()
        else:
            self.Error(29)
            lpN = self.uVarPtr
        self.gAttr.Typtr = lpN.IdType
        self.gAttr.TreePtr = lpN
        self.gAttr.ASize = self.FullBytes(self.gAttr.Typtr)
        PckdFlag, _PckdStorage = self._Selector(FSys, lpN)
        if PckdFlag:
            self.Error(165)

    def _Selector(
        self,
        FSys: set[Symbol] | frozenset[Symbol],
        FpN: Optional[N],
    ) -> tuple[bool, bool]:
        """Resolve base identifier `FpN` and parse any trailing postfix selectors into `gAttr`.

        Handles `WITH`-scoped record/class fields and methods, Clascal class qualifiers,
        explicit type conversions, and function-result selections before delegating to
        `_Select`, returning `(Pckd, PckdStorage)`.
        """
        PckdStorage = False
        Pckd = False
        SawClassId = False
        lAttr = self.gAttr.copy()
        if FpN is not None and FpN.Node == NodeKind.IDENTNODE:
            if self.Display[self.Disx].Occur == Where.KLASS:
                # WITH'ed class field or method
                if FpN.Class == NameClass.FIELD:
                    lpN = self._NewUnNode(43, None)  # WITHREC
                    if self.Level <= 1:
                        lpN.UnSubOp = self.Disx - 1
                    else:
                        lpN.UnSubOp = self.Disx - self.Level
                    lAttr.TreePtr = self._NewBinNode(15, lpN, FpN)  # FIELD
                else:  # METHOD
                    if FpN.MethodNo == 0:  # 'CREATE'
                        self.Error(809)
                        MpN = None
                    else:
                        MpN = self.Display[self.Disx].WVar
                        if MpN is None:
                            MpN = self._NewUnNode(43, None)  # WITHREC
                            if self.Level <= 1:
                                MpN.UnSubOp = self.Disx - 2
                            else:
                                MpN.UnSubOp = self.Disx - 1 - self.Level
                    self._Call(FSys, FpN)
                    tpN = N(NodeKind.TRINODE)
                    tpN.TriOp = 184  # METHODCALL
                    tpN.TripN = FpN
                    tpN.Tri1 = MpN
                    tpN.OrigTri1 = tpN.Tri1
                    tpN.Tri2 = self.gAttr.TreePtr
                    tpN.TriSuper = None
                    lAttr.TreePtr = tpN
                    lAttr.ASize = self.gAttr.ASize
            else:
                if FpN.Class == NameClass.TYPES:
                    if self.Token == Symbol.PERIODSY:
                        if lAttr.Typtr is not None:
                            if lAttr.Typtr.Form != TypeForms.CLASSES:
                                self.Error(808)
                                lAttr.Typtr = None
                        lAttr.TreePtr = None
                        SawClassId = True
                    elif self.Token == Symbol.LPARENSY:
                        FpN = self._TypeConvert(FSys, self._SelectorVariable, FpN)
                        lAttr = self.gAttr.copy()
                    else:
                        self.Skip(56, FSys)
                elif FpN.Class == NameClass.FIELD:
                    if self.Display[self.Disx].Occur == Where.REC:
                        Pckd = self.Display[self.Disx].RecPckd
                    lpN = self._NewUnNode(43, None)  # WITHREC
                    if self.Level <= 1:
                        lpN.UnSubOp = self.Disx - 1
                    else:
                        lpN.UnSubOp = self.Disx - self.Level
                    lAttr.TreePtr = self._NewBinNode(15, lpN, lAttr.TreePtr)  # FIELD
                    PckdStorage = FpN.PckdField
                    if PckdStorage:
                        Lo, Hi = self.GetBounds(lAttr.Typtr)
                        lAttr.ASize = 2
                        lAttr.TreePtr = self._NewUnNode(
                            62 + (1 if Lo < 0 else 0),  # EXTUSFLD
                            lAttr.TreePtr,
                        )
                        NumBits = lAttr.Typtr.Bytes * 8 + lAttr.Typtr.Bits
                        MyRightBit = 16 - FpN.BitOff - NumBits
                        lAttr.TreePtr.UnSubOp = NumBits * 16 + MyRightBit
                elif FpN.Class == NameClass.FUNC:
                    InFunc = False
                    for i in range(self.Top, 0, -1):
                        disp = self.Display[i]
                        if disp.Occur == Where.BLK:
                            if disp.RootLink == FpN:
                                InFunc = True
                    if (not InFunc) or (self.Token in (SelectSys | _SET_LPAREN)):
                        self.gAttr.TreePtr = None
                        self._Call(FSys | _SET_UPARROW, FpN)
                        if FpN.PFdeclKind == DeclKind.STANDARD:
                            lOp = 178  # STDFUNC
                        else:
                            lOp = 176  # USRFUNC
                        lAttr.TreePtr = self._NewBinNode(lOp, FpN, self.gAttr.TreePtr)
                        if self.Token not in SelectSys:
                            self.Error(28)
                    elif FpN.PFdeclKind == DeclKind.STANDARD:
                        self.Error(145)

        Pckd, PckdStorage, SawClassId = self._Select(FSys, lAttr, Pckd, PckdStorage, SawClassId)
        if SawClassId:
            self.Error(812)
        self.gAttr.set_from(lAttr)
        return Pckd, PckdStorage

    # ---- Expressions ----

    def _BuildSet(self, FSys: set[Symbol] | frozenset[Symbol]) -> None:
        """Parse a bracketed set constructor (`[...]`) into `gAttr`.

        Folds constant elements and `lo..hi` subranges into a set constant bitmap while
        combining non-constant elements and ranges via `SSET`, `SETR`, and `UNION` nodes.
        """
        self.Scan()
        SetType: Optional[T] = None
        SetTree: Optional[N] = None
        SetCstPart: Optional[N] = None
        if self.Token != Symbol.RBRACKSY:
            ExitFlag = False
            while True:
                self._Expression(FSys | _SET_COMMA_COLON_RBRACK)
                if SetType is None:
                    SetType = self.gAttr.Typtr
                elif not self.CompTypes(SetType, self.gAttr.Typtr):
                    self.Error(134)
                self._MakeScSize(self.gAttr, 2)
                if self.Token == Symbol.COLONSY:
                    self.Scan()
                    lpN = self.gAttr.TreePtr
                    self._Expression(FSys | _SET_COMMA_RBRACK)
                    if SetType is None:
                        SetType = self.gAttr.Typtr
                    elif not self.CompTypes(SetType, self.gAttr.Typtr):
                        self.Error(134)
                    self._MakeScSize(self.gAttr, 2)
                    if lpN is not None and self.gAttr.TreePtr is not None:
                        if (
                            lpN.Node == NodeKind.CSTNODE
                            and self.gAttr.TreePtr.Node == NodeKind.CSTNODE
                        ):
                            SetCstPart = self.UpdateSetConst(
                                lpN.CstValu.Ivalu,
                                self.gAttr.TreePtr.CstValu.Ivalu,
                                SetCstPart,
                            )
                            lpN = None
                        else:
                            lpN = self._NewBinNode(169, lpN, self.gAttr.TreePtr)  # SETR
                    else:
                        lpN = self._NewBinNode(169, lpN, self.gAttr.TreePtr)  # SETR
                elif self.gAttr.TreePtr is not None:
                    if self.gAttr.TreePtr.Node == NodeKind.CSTNODE:
                        SetCstPart = self.UpdateSetConst(
                            self.gAttr.TreePtr.CstValu.Ivalu,
                            self.gAttr.TreePtr.CstValu.Ivalu,
                            SetCstPart,
                        )
                        lpN = None
                    else:
                        lpN = self._NewUnNode(168, self.gAttr.TreePtr)  # SSET
                else:
                    lpN = self._NewUnNode(168, self.gAttr.TreePtr)  # SSET

                if SetTree is None:
                    SetTree = lpN
                elif lpN is not None:
                    SetTree = self._NewBinNode(160, SetTree, lpN)  # UNION

                if self.Token == Symbol.COMMASY:
                    self.Scan()
                else:
                    ExitFlag = True
                if ExitFlag:
                    break

            if SetType is not None:
                if SetType.Form > TypeForms.SUBRANGE:
                    self.Error(133)
                elif self.CompTypes(SetType, self.RealPtr):
                    self.Error(164)

        lpT = T(TypeForms.SETS)
        lpT.FType = False
        lpT.SetOf = SetType
        lpT.Bytes = 0
        lpT.Bits = 0
        self.gAttr.Typtr = lpT

        if SetCstPart is None:
            if SetTree is None:
                self.gAttr.TreePtr = self._NewUnNode(31, None)  # NULLSET
                self.gAttr.ASize = 1
            else:
                self.gAttr.TreePtr = SetTree
                self.gAttr.ASize = 0
        else:
            SetCstPart.CstType = lpT
            lpT.Bytes = pdiv(SetCstPart.CstValu.MaxSetEl, 8) + 1
            if lpT.Bytes > 1 and odd(lpT.Bytes):
                lpT.Bytes = lpT.Bytes + 1
            if SetTree is None:
                self.gAttr.TreePtr = SetCstPart
                self.gAttr.ASize = lpT.Bytes
            else:
                SetCstPart = self._NewUnNode(170, SetCstPart)  # ADJUST
                SetCstPart.UnSubOp = lpT.Bytes
                self.gAttr.TreePtr = self._NewBinNode(160, SetTree, SetCstPart)  # UNION
                self.gAttr.ASize = 0

        if self.Token == Symbol.RBRACKSY:
            self.Scan()
        else:
            self.Error(34)

    def _SetConstant(self, FpN: N) -> bool:
        """Populate `gAttr` with a `NULLSET` or set `CSTNODE` if `FpN` is a named set constant."""
        if FpN.IdType is not None:
            if FpN.IdType.Form == TypeForms.SETS:
                self.gAttr.Typtr = FpN.IdType
                if FpN.ValueOf.MaxSetEl == -1:
                    self.gAttr.TreePtr = self._NewUnNode(31, None)  # NULLSET
                    self.gAttr.ASize = 1
                else:
                    tree = N(NodeKind.CSTNODE)
                    tree.CstType = FpN.IdType
                    tree.CstValu = FpN.ValueOf.copy()
                    self.gAttr.TreePtr = tree
                    self.gAttr.ASize = FpN.IdType.Bytes
                return True
        return False

    @staticmethod
    def _NumBytes(fVal: int) -> int:
        """Return the minimum signed integer byte width (1, 2, or 4) needed to represent `fVal`."""
        if fVal > 127 or fVal < -128:
            if fVal > 32767 or fVal < -32768:
                return 4
            else:
                return 2
        else:
            return 1

    def _IntType(self, fSize: int) -> Optional[T]:
        """Return the standard signed integer type (`SIntPtr`, `IntPtr`, or `LIntPtr`) for `fSize`."""
        if fSize == 1:
            return self.SIntPtr
        elif fSize == 2:
            return self.IntPtr
        else:
            return self.LIntPtr

    def _Factor(self, FSys: set[Symbol] | frozenset[Symbol]) -> None:
        """Parse an expression factor into `gAttr`.

        Handles identifiers (constants, variables/fields, type casts, class qualifiers,
        and function/method calls), literals, parenthesized expressions, `NOT`, `NIL`,
        set constructors (`[...]`), and address-of (`@`) operands.
        """
        self.gAttr.TreePtr = None
        PckdFlag = False
        PckdStorage = False
        if self.Token not in FacBegSys:
            self.Skip(27, FSys | FacBegSys)
            self.gAttr.Typtr = None
        while True:
            if self.Token in FacBegSys:
                tok = self.Token
                if tok == Symbol.IDENTSY:
                    lpN = self.SearchAll(_SEARCH_VAR_FLD_FUNC_CST_TYP)
                    self.Scan()
                    cls = lpN.Class
                    if cls == NameClass.CONSTS:
                        if not self._SetConstant(lpN):
                            self.gAttr.Typtr = lpN.IdType
                            tree = N(NodeKind.CSTNODE)
                            tree.CstValu = lpN.ValueOf.copy()
                            if self.CompTypes(lpN.IdType, self.IntPtr):
                                self.gAttr.ASize = self._NumBytes(lpN.ValueOf.Ivalu)
                                tree.CstType = self._IntType(self.gAttr.ASize)
                            else:
                                self.gAttr.ASize = self.FullBytes(lpN.IdType)
                                tree.CstType = lpN.IdType
                            self.gAttr.TreePtr = tree

                    elif cls == NameClass.VARS or cls == NameClass.FIELD:
                        self.gAttr.Typtr = lpN.IdType
                        self.gAttr.TreePtr = lpN
                        self.gAttr.ASize = self.FullBytes(self.gAttr.Typtr)
                        PckdFlag, PckdStorage = self._Selector(FSys, lpN)

                    elif cls == NameClass.TYPES:
                        if self.Token == Symbol.LPARENSY:
                            lpN = self._TypeConvert(FSys, self._Expression, lpN)
                        else:
                            self.gAttr.Typtr = lpN.IdType
                            self.gAttr.TreePtr = lpN
                            self.gAttr.ASize = self.FullBytes(self.gAttr.Typtr)
                        if lpN is not None:
                            PckdFlag, PckdStorage = self._Selector(FSys, lpN)

                    elif cls == NameClass.FUNC:
                        if self.Display[self.Disx].Occur == Where.KLASS:
                            self.gAttr.Typtr = lpN.IdType
                            self.gAttr.TreePtr = lpN
                            self.gAttr.ASize = self.FullBytes(self.gAttr.Typtr)
                            PckdFlag, PckdStorage = self._Selector(FSys, lpN)
                        else:
                            self._Call(FSys, lpN)
                            if lpN.PFdeclKind == DeclKind.STANDARD:
                                lOp = 178  # STDFUNC
                            else:
                                lOp = 176  # USRFUNC
                            self.gAttr.TreePtr = self._NewBinNode(lOp, lpN, self.gAttr.TreePtr)
                            if self.Token in SelectSys:
                                SawClassId = False
                                PckdFlag, PckdStorage, SawClassId = self._Select(
                                    FSys, self.gAttr, PckdFlag, PckdStorage, SawClassId
                                )

                elif tok == Symbol.ICONSTSY:
                    self.gAttr.ASize = self._NumBytes(self.IntVal)
                    self.gAttr.Typtr = self._IntType(self.gAttr.ASize)
                    tree = N(NodeKind.CSTNODE)
                    tree.CstType = self.gAttr.Typtr
                    tree.CstValu.Ivalu = self.IntVal
                    self.gAttr.TreePtr = tree
                    self.Scan()

                elif tok == Symbol.RCONSTSY:
                    self.gAttr.Typtr = self.RealPtr
                    self.gAttr.ASize = 4
                    tree = N(NodeKind.CSTNODE)
                    tree.CstType = self.RealPtr
                    tree.CstValu.Rvalu = self.RealVal
                    self.gAttr.TreePtr = tree
                    self.Scan()

                elif tok == Symbol.CCONSTSY:
                    self.gAttr.Typtr = self.CharPtr
                    self.gAttr.ASize = 2
                    tree = N(NodeKind.CSTNODE)
                    tree.CstType = self.CharPtr
                    tree.CstValu.Ivalu = self.IntVal
                    self.gAttr.TreePtr = tree
                    self.Scan()

                elif tok == Symbol.SCONSTSY:
                    if self.IntVal > 0:
                        lpT = T(TypeForms.SCONST)
                        lpT.FType = False
                        lpT.StringLen = self.IntVal
                        lpT.Bits = 0
                        lpT.Bytes = self.IntVal
                        if lpT.Bytes != 1 and odd(lpT.Bytes):
                            lpT.Bytes = lpT.Bytes + 1
                    else:
                        lpT = self.Str0Ptr
                    self.gAttr.Typtr = lpT
                    self.gAttr.ASize = lpT.StringLen
                    tree = N(NodeKind.CSTNODE)
                    tree.CstType = lpT
                    tree.CstValu.Svalu = self.StrVal
                    tree.CstValu.SvaluLen = self.IntVal
                    self.gAttr.TreePtr = tree
                    self.Scan()

                elif tok == Symbol.LPARENSY:
                    self.Scan()
                    self._Expression(FSys | _SET_RPAREN)
                    if self.Token == Symbol.RPARENSY:
                        self.Scan()
                    else:
                        self.Error(32)

                elif tok == Symbol.NOTSY:
                    self.Scan()
                    self._Factor(FSys)
                    self.gAttr.ASize = 1
                    self.gAttr.TreePtr = self._NewUnNode(110, self.gAttr.TreePtr)  # NOT
                    if not self.CompTypes(self.gAttr.Typtr, self.BoolPtr):
                        self.Error(132)
                        self.gAttr.Typtr = None

                elif tok == Symbol.NILSY:
                    self.Scan()
                    self.gAttr.Typtr = self.NilPtr
                    self.gAttr.ASize = 4
                    self.gAttr.TreePtr = self._NewUnNode(23, None)  # NIL

                elif tok == Symbol.LBRACKSY:
                    self._BuildSet(FSys)

                elif tok == Symbol.ATSIGNSY:
                    self.Scan()
                    if self.Token == Symbol.IDENTSY:
                        lpN = self.SearchAll(_SEARCH_VAR_FLD_FUNC_PROC)
                        self.Scan()
                        if lpN.Class <= NameClass.FIELD:
                            self.gAttr.Typtr = lpN.IdType
                            self.gAttr.TreePtr = lpN
                            self.gAttr.ASize = self.FullBytes(self.gAttr.Typtr)
                            PckdFlag, PckdStorage = self._Selector(FSys, lpN)
                            if PckdFlag:
                                self.Error(163)
                            self.gAttr.TreePtr = self._NewUnNode(22, self.gAttr.TreePtr)  # ADDR
                        else:
                            self.gAttr.TreePtr = self._NewUnNode(22, lpN)  # ADDR
                            if lpN.PFdeclKind == DeclKind.DECLARED:
                                if lpN.Class == NameClass.PROC:
                                    self.gAttr.TreePtr.UnSubOp = 177  # PROC
                                else:
                                    self.gAttr.TreePtr.UnSubOp = 176  # FUNC
                            else:
                                self.Error(170)
                        self.gAttr.Typtr = self.NilPtr
                    else:
                        self.Error(29)
                        self.gAttr.Typtr = None
                    self.gAttr.ASize = 4

                if self.Token not in FSys:
                    self.Skip(20, FSys | FacBegSys)
            if self.Token in FSys:
                break

    def _Term(self, FSys: set[Symbol] | frozenset[Symbol]) -> None:
        """Parse multiplicative expressions (`*`, `/`, `DIV`, `MOD`, `AND`) over factors into `gAttr`."""
        sub_fsys = FSys | _MULTOPS
        self._Factor(sub_fsys)
        while self.Token in _MULTOPS:
            lAttr = self.gAttr.copy()
            lToken = self.Token
            self.Scan()
            self._Factor(sub_fsys)
            if lAttr.Typtr is not None and self.gAttr.Typtr is not None:
                if lToken == Symbol.ANDSY:
                    if (
                        self.CompTypes(lAttr.Typtr, self.BoolPtr)
                        and self.CompTypes(self.gAttr.Typtr, self.BoolPtr)
                    ):
                        self.gAttr.TreePtr = self._NewBinNode(
                            80, lAttr.TreePtr, self.gAttr.TreePtr  # AND
                        )
                    else:
                        self.Error(132)
                        self.gAttr.Typtr = None

                elif lToken == Symbol.DIVSY or lToken == Symbol.MODSY:
                    if (
                        self.CompTypes(lAttr.Typtr, self.IntPtr)
                        and self.CompTypes(self.gAttr.Typtr, self.IntPtr)
                    ):
                        self._MinSize2(lAttr)
                        self._MinSize2(self.gAttr)
                        self._MatchISizes(lAttr, self.gAttr)
                        Op = 1 if lAttr.ASize > 2 else 0
                        if lToken == Symbol.DIVSY:
                            self.gAttr.TreePtr = self._NewBinNode(
                                70 + Op, lAttr.TreePtr, self.gAttr.TreePtr  # IDIV
                            )
                            if self.OflowFlag and Op == 0:
                                self.gAttr.TreePtr = self._NewUnNode(
                                    0x8C, self.gAttr.TreePtr  # TRAPV
                                )
                        else:
                            self.gAttr.TreePtr = self._NewBinNode(
                                72 + Op, lAttr.TreePtr, self.gAttr.TreePtr  # MOD
                            )
                    else:
                        self.Error(131)
                        self.gAttr.Typtr = None

                elif lToken == Symbol.SLASHSY:
                    if self.CompTypes(lAttr.Typtr, self.IntPtr):
                        self._Float(lAttr)
                    if self.CompTypes(self.gAttr.Typtr, self.IntPtr):
                        self._Float(self.gAttr)
                    if (
                        self.CompTypes(self.gAttr.Typtr, self.RealPtr)
                        and self.CompTypes(lAttr.Typtr, self.RealPtr)
                    ):
                        self.gAttr.TreePtr = self._NewBinNode(
                            118, lAttr.TreePtr, self.gAttr.TreePtr  # RDIV
                        )
                    else:
                        self.Error(131)
                        self.gAttr.Typtr = None

                elif lToken == Symbol.STARSY:
                    if (
                        self.CompTypes(lAttr.Typtr, self.IntPtr)
                        and self.CompTypes(self.gAttr.Typtr, self.IntPtr)
                    ):
                        self._MinSize2(lAttr)
                        self._MinSize2(self.gAttr)
                        self._MatchISizes(lAttr, self.gAttr)
                        Op = 1 if lAttr.ASize > 2 else 0
                        self.gAttr.TreePtr = self._NewBinNode(
                            68 + Op, lAttr.TreePtr, self.gAttr.TreePtr  # IMULT
                        )
                        if self.OflowFlag:
                            self.gAttr.TreePtr = self._NewUnNode(
                                0x8C, self.gAttr.TreePtr  # TRAPV
                            )
                    else:
                        if self.CompTypes(lAttr.Typtr, self.IntPtr):
                            self._Float(lAttr)
                        if self.CompTypes(self.gAttr.Typtr, self.IntPtr):
                            self._Float(self.gAttr)
                        if (
                            self.CompTypes(lAttr.Typtr, self.RealPtr)
                            and self.CompTypes(self.gAttr.Typtr, self.RealPtr)
                        ):
                            self.gAttr.TreePtr = self._NewBinNode(
                                116, lAttr.TreePtr, self.gAttr.TreePtr  # RMULT
                            )
                        elif (
                            self.CompTypes(self.gAttr.Typtr, lAttr.Typtr)
                            and self.gAttr.Typtr.Form == TypeForms.SETS
                        ):
                            self._MatchSetSizes(self.gAttr, lAttr)
                            self.gAttr.TreePtr = self._NewBinNode(
                                162, lAttr.TreePtr, self.gAttr.TreePtr  # INTER
                            )
                            self.gAttr.TreePtr.BinSubOp = self.gAttr.ASize
                        else:
                            self.Error(131)
                            self.gAttr.Typtr = None

    def _SimpleExpression(self, FSys: set[Symbol] | frozenset[Symbol]) -> None:
        """Parse an optional leading sign (`+`/`-`) and additive operators (`+`, `-`, `OR`) over terms."""
        Negative = self.Token == Symbol.MINUSSY
        Signed = (self.Token == Symbol.PLUSSY) or Negative
        if Signed:
            self.Scan()
        sub_fsys = FSys | _ADDOPS
        self._Term(sub_fsys)
        if self.gAttr.Typtr is not None:
            if Signed:
                if self.CompTypes(self.gAttr.Typtr, self.IntPtr):
                    if Negative:
                        if self.gAttr.TreePtr is not None and self.gAttr.TreePtr.Node == NodeKind.CSTNODE:
                            self.gAttr.TreePtr.CstValu.Ivalu = i32(-self.gAttr.TreePtr.CstValu.Ivalu)
                        else:
                            self._MinSize2(self.gAttr)
                            Op = 1 if self.gAttr.ASize > 2 else 0
                            self.gAttr.TreePtr = self._NewUnNode(74 + Op, self.gAttr.TreePtr)  # INEG
                            if self.OflowFlag:
                                self.gAttr.TreePtr = self._NewUnNode(0x8C, self.gAttr.TreePtr)  # TRAPV
                elif self.CompTypes(self.gAttr.Typtr, self.RealPtr):
                    if Negative:
                        if self.gAttr.TreePtr is not None and self.gAttr.TreePtr.Node == NodeKind.CSTNODE:
                            self.gAttr.TreePtr.CstValu.Rvalu = f32(-self.gAttr.TreePtr.CstValu.Rvalu)
                        else:
                            self.gAttr.TreePtr = self._NewUnNode(134, self.gAttr.TreePtr)  # RNEG
                else:
                    self.Error(140)

        while self.Token in _ADDOPS:
            lToken = self.Token
            lAttr = self.gAttr.copy()
            self.Scan()
            self._Term(sub_fsys)
            if lAttr.Typtr is not None and self.gAttr.Typtr is not None:
                if lToken == Symbol.MINUSSY or lToken == Symbol.PLUSSY:
                    if (
                        self.CompTypes(lAttr.Typtr, self.IntPtr)
                        and self.CompTypes(self.gAttr.Typtr, self.IntPtr)
                    ):
                        self._MinSize2(lAttr)
                        self._MinSize2(self.gAttr)
                        self._MatchISizes(lAttr, self.gAttr)
                        Op = 1 if lAttr.ASize > 2 else 0
                        if lToken == Symbol.PLUSSY:
                            self.gAttr.TreePtr = self._NewBinNode(
                                64 + Op, lAttr.TreePtr, self.gAttr.TreePtr  # IADD
                            )
                        else:
                            self.gAttr.TreePtr = self._NewBinNode(
                                66 + Op, lAttr.TreePtr, self.gAttr.TreePtr  # ISUB
                            )
                        if self.OflowFlag:
                            self.gAttr.TreePtr = self._NewUnNode(0x8C, self.gAttr.TreePtr)  # TRAPV
                    else:
                        if self.CompTypes(lAttr.Typtr, self.IntPtr):
                            self._Float(lAttr)
                        if self.CompTypes(self.gAttr.Typtr, self.IntPtr):
                            self._Float(self.gAttr)
                        if (
                            self.CompTypes(lAttr.Typtr, self.RealPtr)
                            and self.CompTypes(self.gAttr.Typtr, self.RealPtr)
                        ):
                            if lToken == Symbol.PLUSSY:
                                self.gAttr.TreePtr = self._NewBinNode(
                                    112, lAttr.TreePtr, self.gAttr.TreePtr  # RADD
                                )
                            else:
                                self.gAttr.TreePtr = self._NewBinNode(
                                    114, lAttr.TreePtr, self.gAttr.TreePtr  # RSUB
                                )
                        elif (
                            self.CompTypes(lAttr.Typtr, self.gAttr.Typtr)
                            and lAttr.Typtr.Form == TypeForms.SETS
                        ):
                            self._MatchSetSizes(self.gAttr, lAttr)
                            if lToken == Symbol.PLUSSY:
                                self.gAttr.TreePtr = self._NewBinNode(
                                    160, lAttr.TreePtr, self.gAttr.TreePtr  # UNION
                                )
                            else:
                                self.gAttr.TreePtr = self._NewBinNode(
                                    161, lAttr.TreePtr, self.gAttr.TreePtr  # DIFF
                                )
                            self.gAttr.TreePtr.BinSubOp = self.gAttr.ASize
                        else:
                            self.Error(131)
                            self.gAttr.Typtr = None

                elif lToken == Symbol.ORSY:
                    if (
                        self.CompTypes(lAttr.Typtr, self.BoolPtr)
                        and self.CompTypes(self.gAttr.Typtr, self.BoolPtr)
                    ):
                        self.gAttr.TreePtr = self._NewBinNode(
                            83, lAttr.TreePtr, self.gAttr.TreePtr  # OR
                        )
                    else:
                        self.Error(132)
                        self.gAttr.Typtr = None

    def _Expression(self, FSys: set[Symbol] | frozenset[Symbol]) -> None:
        """Parse an expression with optional relational or `IN` operators into `gAttr`.

        Coerces mixed integer/real, packed-char/string-literal, char-constant/string, and
        Clascal class hierarchy operands before building the comparison or set-membership node.
        """
        self._SimpleExpression(FSys | _RELOPS)
        if self.Token in _RELOPS:
            lToken = self.Token
            lAttr = self.gAttr.copy()
            self.Scan()
            self._SimpleExpression(FSys)
            if lAttr.Typtr is not None and self.gAttr.Typtr is not None:
                if lToken in (
                    Symbol.LTSY, Symbol.GTSY, Symbol.LESY,
                    Symbol.GESY, Symbol.EQSY, Symbol.NESY,
                ):
                    if (
                        not self.CompTypes(lAttr.Typtr, self.gAttr.Typtr)
                        and lAttr.Typtr.Form != TypeForms.CLASSES
                    ):
                        if self.CompTypes(lAttr.Typtr, self.IntPtr):
                            self._Float(lAttr)
                        elif self.CompTypes(self.gAttr.Typtr, self.IntPtr):
                            self._Float(self.gAttr)
                        elif self._PAoC(lAttr.Typtr) and self.gAttr.Typtr.Form == TypeForms.SCONST:
                            Lo, Hi = self.GetBounds(lAttr.Typtr.IndexedBy)
                            if Hi - Lo + 1 != self.gAttr.Typtr.StringLen:
                                self.Error(167)
                            self.gAttr.Typtr = lAttr.Typtr
                            self.gAttr.TreePtr.CstType = lAttr.Typtr
                        elif self._PAoC(self.gAttr.Typtr) and lAttr.Typtr.Form == TypeForms.SCONST:
                            Lo, Hi = self.GetBounds(self.gAttr.Typtr.IndexedBy)
                            if Hi - Lo + 1 != lAttr.Typtr.StringLen:
                                self.Error(167)
                            lAttr.Typtr = self.gAttr.Typtr
                            lAttr.TreePtr.CstType = self.gAttr.Typtr
                        elif (
                            (lAttr.Typtr.Form == TypeForms.SCONST or lAttr.Typtr.Form == TypeForms.STRINGS)
                            and (
                                self.gAttr.Typtr == self.CharPtr
                                and self.gAttr.TreePtr is not None
                                and self.gAttr.TreePtr.Node == NodeKind.CSTNODE
                            )
                        ):
                            self.ChToString(self.gAttr)
                        elif (
                            (lAttr.Typtr.Form == TypeForms.SCONST or lAttr.Typtr.Form == TypeForms.STRINGS)
                            and (
                                self.gAttr.Typtr == self.CharPtr
                                and self.gAttr.TreePtr is not None
                                and self.gAttr.TreePtr.Node == NodeKind.CSTNODE
                            )
                        ):
                            self.ChToString(lAttr)

                    # Check CompTypes both ways because classes are not commutative.
                    lCompTypes = self.CompTypes(lAttr.Typtr, self.gAttr.Typtr)
                    if not lCompTypes:
                        lCompTypes = self.CompTypes(self.gAttr.Typtr, lAttr.Typtr)
                    if lCompTypes:
                        Op = 0
                        m = 1
                        SubOp = 0
                        form = self.gAttr.Typtr.Form
                        if form == TypeForms.SCALAR or form == TypeForms.SUBRANGE:
                            if self.CompTypes(self.gAttr.Typtr, self.RealPtr):
                                Op = 122  # RLT
                                m = 2
                            else:
                                self._MatchISizes(lAttr, self.gAttr)
                                Op = 92  # ILT
                                m = 3
                                if lAttr.ASize > 1:
                                    if lAttr.ASize > 2:
                                        Op = Op + 2
                                    else:
                                        Op = Op + 1
                        elif form == TypeForms.CLASSES or form == TypeForms.POINTERS:
                            if lToken != Symbol.EQSY and lToken != Symbol.NESY:
                                self.Error(128)
                            Op = 94
                            m = 3
                        elif form == TypeForms.SETS:
                            if lToken == Symbol.LTSY or lToken == Symbol.GTSY:
                                self.Error(129)
                            self._MatchSetSizes(self.gAttr, lAttr)
                            Op = 162
                            SubOp = self.gAttr.ASize
                        elif form == TypeForms.ARRAYS:
                            if not self.StringType(self.gAttr.Typtr):
                                self.Error(131)
                            Lo, Hi = self.GetBounds(self.gAttr.Typtr.IndexedBy)
                            Op = 150  # PACLT
                            SubOp = Hi
                        elif form == TypeForms.RECORDS:
                            self.Error(131)
                        elif form == TypeForms.FILES:
                            self.Error(130)
                        elif form == TypeForms.SCONST or form == TypeForms.STRINGS:
                            Op = 144  # STRLT

                        self.gAttr.TreePtr = self._NewBinNode(
                            Op + (int(lToken) - int(Symbol.LTSY)) * m,
                            lAttr.TreePtr,
                            self.gAttr.TreePtr,
                        )
                        self.gAttr.TreePtr.BinSubOp = SubOp
                        self.gAttr.Typtr = self.BoolPtr
                        self.gAttr.ASize = 1
                    else:
                        self.Error(144)
                        self.gAttr.Typtr = None

                elif lToken == Symbol.INSY:
                    if self.gAttr.Typtr.Form == TypeForms.SETS:
                        if self.CompTypes(lAttr.Typtr, self.gAttr.Typtr.SetOf):
                            self._MakeScSize(lAttr, 2)
                            self.gAttr.TreePtr = self._NewBinNode(
                                163, lAttr.TreePtr, self.gAttr.TreePtr  # IN
                            )
                            self.gAttr.TreePtr.BinSubOp = self.gAttr.ASize
                            self.gAttr.Typtr = self.BoolPtr
                            self.gAttr.ASize = 1
                        else:
                            self.Error(127)
                            self.gAttr.Typtr = None
                    else:
                        self.Error(131)
                        self.gAttr.Typtr = None
            else:
                self.gAttr.Typtr = None

    def _StringAss(self, ToType: Optional[T], FAttr: Attr) -> bool:
        """Check and coerce string or packed-char assignment compatibility from `FAttr` to `ToType`.

        Validates packed-char array lengths and string literal capacities, promotes single-char
        constants to strings, and inserts `SRNGCHK` under `$R+` when assigning dynamic strings.
        """
        StringFlag = False
        if ToType is not None and FAttr.Typtr is not None:
            if ToType.Form == TypeForms.ARRAYS:
                Min, lSize = self.GetBounds(ToType.IndexedBy)
                if self._PAoC(ToType):
                    if FAttr.Typtr.Form == TypeForms.ARRAYS:
                        Min, Max = self.GetBounds(FAttr.Typtr.IndexedBy)
                        if lSize != Max:
                            self.Error(167)
                        StringFlag = True
                    elif FAttr.Typtr.Form == TypeForms.SCONST:
                        if FAttr.Typtr.StringLen != lSize:
                            self.Error(167)
                        FAttr.TreePtr.CstType = ToType
                        StringFlag = True
            elif ToType.Form == TypeForms.STRINGS:
                if FAttr.Typtr == self.CharPtr and FAttr.TreePtr is not None:
                    if FAttr.TreePtr.Node == NodeKind.CSTNODE:
                        StringFlag = True
                        self.ChToString(FAttr)
                elif FAttr.Typtr.Form == TypeForms.STRINGS:
                    if self.RangeFlag:
                        FAttr.TreePtr = self._NewBinNode(47, None, FAttr.TreePtr)  # SRNGCHK
                        FAttr.TreePtr.BinSubOp = ToType.StringLen
                    StringFlag = True
                elif FAttr.Typtr.Form == TypeForms.SCONST:
                    StringFlag = True
                    if FAttr.Typtr.StringLen > ToType.StringLen:
                        self.Error(168)
        return StringFlag

    # ---- Procedure and Function Calls ----

    def _CallVariable(self, FSys: set[Symbol] | frozenset[Symbol]) -> None:
        """Parse an l-value actual argument, rejecting packed components and `$H+` handle fields."""
        OldExprDHandle = self.ExprDHandle
        if self.Token == Symbol.IDENTSY:
            lpN = self.SearchAll(_SEARCH_VAR_FLD_FUNC_TYP)
            self.Scan()
        else:
            self.Error(29)
            lpN = self.uVarPtr
        self.gAttr.Typtr = lpN.IdType
        self.gAttr.TreePtr = lpN
        self.gAttr.ASize = self.FullBytes(self.gAttr.Typtr)
        PckdFlag, _PckdStorage = self._Selector(FSys, lpN)
        if PckdFlag:
            self.Error(165)
        if self.HandleCheck and (self.ExprDHandle != OldExprDHandle):
            self.Error(815)

    @staticmethod
    def _IsConsTree(FpN: Optional[N]) -> bool:
        """Return `True` if AST node `FpN` is a compile-time constant (`CSTNODE`)."""
        if FpN is not None:
            return FpN.Node == NodeKind.CSTNODE
        return False

    def _RealString(self, FAttr: Attr) -> bool:
        """Return `True` if `FAttr` is a `String` or string literal (promoting a constant `Char`)."""
        lpT = FAttr.Typtr
        if lpT is not None:
            if lpT.Form == TypeForms.STRINGS or lpT.Form == TypeForms.SCONST:
                return True
            elif lpT == self.CharPtr and self._IsConsTree(FAttr.TreePtr):
                self.ChToString(FAttr)
                return True
            else:
                return False
        else:
            return True

    def _NewArg(self, FpN: Optional[N], fOp: int) -> N:
        """Append `gAttr.TreePtr` wrapped in a `BINNODE` (`fOp`) to right-linked argument list `FpN`."""
        lpN = self._NewBinNode(fOp, self.gAttr.TreePtr, None)
        if FpN is None:
            return lpN
        lpN2 = FpN
        while lpN2.RightArg is not None:
            lpN2 = lpN2.RightArg
        lpN2.RightArg = lpN
        return FpN

    def _LeftParen(self) -> None:
        """Consume a `(` token or report error 31."""
        if self.Token == Symbol.LPARENSY:
            self.Scan()
        else:
            self.Error(31)

    def _RightParen(self) -> None:
        """Consume a `)` token or report error 32."""
        if self.Token == Symbol.RPARENSY:
            self.Scan()
        else:
            self.Error(32)

    def _Comma(self) -> None:
        """Consume a `,` token or report error 38."""
        if self.Token == Symbol.COMMASY:
            self.Scan()
        else:
            self.Error(38)

    def _PListError(self, ActArgs: Optional[N], FormArgs: Optional[N]) -> bool:
        """Return `True` if procedural/functional parameter lists `ActArgs` and `FormArgs` differ."""
        err = False
        while ActArgs is not None and FormArgs is not None:
            if ActArgs.Class != FormArgs.Class:
                err = True
            elif ActArgs.Class == NameClass.VARS:
                if (
                    not self.EqTypes(ActArgs.IdType, FormArgs.IdType)
                    or ActArgs.Vkind != FormArgs.Vkind
                ):
                    err = True
            else:
                # ActArgs.Class == FUNC or PROC
                if self._PListError(ActArgs.PFargList, FormArgs.PFargList):
                    err = True
                if ActArgs.Class == NameClass.FUNC:
                    if ActArgs.IdType != FormArgs.IdType:
                        err = True
            ActArgs = ActArgs.Next
            FormArgs = FormArgs.Next
        if ActArgs is not None or FormArgs is not None:
            err = True
        return err

    def _CallNonStandard(self, FSys: set[Symbol] | frozenset[Symbol], FpN: N) -> None:
        """Parse and validate actual arguments for a declared, external, `CDECL`, or method call `FpN`.

        Handles value, `VAR`, `UNIV`, and procedural/functional parameters, applying C ABI
        widening (`LongInt`/double), subrange checks, and Clascal `$H+` handle-dereference checks.
        """
        FSys = FSys | _SET_COMMA_RPAREN
        FormArgList = FpN.PFargList
        ActArgList: Optional[N] = None
        lVKind = AccessKind.DRCT
        if self.Token == Symbol.LPARENSY:
            while True:
                self.Scan()
                if FormArgList is not None:
                    NormalParam = FormArgList.Class == NameClass.VARS
                    if NormalParam:
                        lVKind = FormArgList.Vkind
                else:
                    lVKind = AccessKind.DRCT
                    NormalParam = True

                if NormalParam:
                    if lVKind == AccessKind.DRCT:
                        self._Expression(FSys)
                    else:
                        self._CallVariable(FSys)
                elif self.Token == Symbol.IDENTSY:
                    lpN = self.SearchAll(_SEARCH_PROC_FUNC)
                    if lpN.PFdeclKind == DeclKind.STANDARD:
                        self.Error(154)
                    else:
                        if self._PListError(lpN.PFargList, FormArgList.PFargList):
                            self.Error(159)
                    if lpN.Class == NameClass.FUNC:
                        if lpN.IdType != FormArgList.IdType:
                            self.Error(126)
                    self.Scan()
                    self.gAttr.TreePtr = lpN
                else:
                    self.Skip(29, FSys)

                if FormArgList is not None:
                    if (
                        self.gAttr.Typtr is not None
                        and FormArgList.IdType is not None
                        and NormalParam
                    ):
                        lSize = self.FullBytes(FormArgList.IdType)
                        if FormArgList.Class == NameClass.VARS:
                            lUNIVflag = FormArgList.UNIVflag
                        else:
                            lUNIVflag = False
                        if lVKind == AccessKind.INDRCT:
                            if not lUNIVflag:
                                if not self.EqTypes(self.gAttr.Typtr, FormArgList.IdType):
                                    self.Error(125)
                        else:  # lVKind == DRCT
                            if not lUNIVflag:
                                if (
                                    FormArgList.IdType == self.RealPtr
                                    and self.CompTypes(self.gAttr.Typtr, self.IntPtr)
                                ):
                                    self._Float(self.gAttr)
                            if (
                                self._StringAss(FormArgList.IdType, self.gAttr)
                                or self.CompTypes(FormArgList.IdType, self.gAttr.Typtr)
                                or lUNIVflag
                            ):
                                if FormArgList.IdType.FType:
                                    self.Error(141)
                                if self.RangeFlag:
                                    self._InsertRangeCheck(FormArgList.IdType, self.gAttr)
                                if FormArgList.IdType.Form <= TypeForms.SUBRANGE:
                                    if FpN.PFdecl != PFkind.CDECL:
                                        self._MakeScSize(self.gAttr, lSize)
                                    elif self.CompTypes(self.gAttr.Typtr, self.IntPtr):
                                        self._MakeScSize(self.gAttr, 4)  # C wants LongInt
                                    elif FormArgList.IdType == self.RealPtr:
                                        # C wants Double Precision reals
                                        self.gAttr.TreePtr = self._NewUnNode(
                                            54, self.gAttr.TreePtr  # REAL48
                                        )
                                        self.gAttr.ASize = 8
                                elif FormArgList.IdType.Form == TypeForms.SETS:
                                    self._MakeSetSize(self.gAttr, lSize)
                            else:
                                self.Error(144)
                        if lUNIVflag:
                            if FpN.PFdecl != PFkind.CDECL:
                                if lSize != self.FullBytes(self.gAttr.Typtr):
                                    self.Error(125)
                    FormArgList = FormArgList.Next
                else:
                    self.Error(124)

                ActArgList = self._NewArg(ActArgList, 0)
                if self.Token != Symbol.COMMASY:
                    break
            self._RightParen()

        if FormArgList is not None:
            self.Error(124)
        self.gAttr.TreePtr = ActArgList
        self.gAttr.Typtr = FpN.IdType
        if FpN.Class == NameClass.FUNC:
            self.gAttr.ASize = self.FullBytes(self.gAttr.Typtr)
            if self.LHSDHandle > 0 and self.HandleCheck:
                self.Error(813)
        if self.WithDHandle > 0 and self.HandleCheck:
            self.Error(814)

    # ---- Standard Procedures ----

    def _xNewDispose(self, FSys: set[Symbol] | frozenset[Symbol]) -> None:
        """Compile `NEW` and `DISPOSE`, computing target byte size across optional variant tags."""
        ActArgList: Optional[N] = None
        TagPt: Optional[T] = None
        lpN: Optional[N] = None
        self._LeftParen()
        self._CallVariable(FSys | _SET_COMMA_RPAREN)
        ActArgList = self._NewArg(ActArgList, 0)
        if self.gAttr.Typtr is not None:
            if self.gAttr.Typtr.Form != TypeForms.POINTERS:
                self.Error(123)
            elif self.gAttr.Typtr.PointerTo is not None:
                lpN = N(NodeKind.CSTNODE)
                lpN.CstType = self.IntPtr
                lpN.CstValu.Ivalu = self.FullBytes(self.gAttr.Typtr.PointerTo)
                self.gAttr.TreePtr = lpN
                ActArgList = self._NewArg(ActArgList, 0)
                if self.gAttr.Typtr.PointerTo.Form == TypeForms.RECORDS:
                    TagPt = self.gAttr.Typtr.PointerTo.VarPart
        while self.Token == Symbol.COMMASY:
            self.Scan()
            lValu, lpT = self.Constant(FSys | _SET_COMMA_RPAREN)
            if TagPt is not None:
                if TagPt.TagName is not None:
                    if not self.CompTypes(TagPt.TagName.IdType, lpT):
                        self.Error(123)
                n_val = lValu.Ivalu
                FoundIt = False
                TagPt = TagPt.Variants
                while TagPt is not None and not FoundIt:
                    lIntVal = TagPt.VarValus
                    while lIntVal is not None and not FoundIt:
                        if lIntVal.IntVal == n_val:
                            FoundIt = True
                        else:
                            lIntVal = lIntVal.NextInt
                    if FoundIt:
                        lpN.CstValu.Ivalu = self.FullBytes(TagPt)
                        TagPt = TagPt.SubVar
                    else:
                        TagPt = TagPt.NextVar
            else:
                self.Error(151)
        self._RightParen()
        self.gAttr.TreePtr = ActArgList

    def _MarkRelease(self, FSys: set[Symbol] | frozenset[Symbol]) -> None:
        """Compile `MARK(p)` and `RELEASE(p)` heap-pointer procedures."""
        self._LeftParen()
        self._CallVariable(FSys | _SET_RPAREN)
        self.gAttr.TreePtr = self._NewBinNode(0, self.gAttr.TreePtr, None)
        if self.gAttr.Typtr is not None:
            if self.gAttr.Typtr.Form != TypeForms.POINTERS:
                self.Error(123)
        self._RightParen()

    def _ResetWrite(self, FSys: set[Symbol] | frozenset[Symbol]) -> None:
        """Compile `RESET(f, title)` and `REWRITE(f, title)`, encoding the file element kind in `BinSubOp`."""
        ArgList: Optional[N] = None
        self._LeftParen()
        self._CallVariable(FSys | _SET_COMMA_RPAREN)
        ArgList = self._NewArg(ArgList, 0)
        if self.gAttr.Typtr is not None:
            if self.gAttr.Typtr.Form == TypeForms.FILES:
                if self.gAttr.Typtr == self.TextPtr:
                    SubOp = -2
                elif self.gAttr.Typtr.FileOf is None:
                    SubOp = -1
                elif self.gAttr.Typtr == self.InterPtr:
                    SubOp = 0
                else:
                    SubOp = self.FullBytes(self.gAttr.Typtr.FileOf)
                ArgList.BinSubOp = SubOp
            else:
                self.Error(123)
        self._Comma()
        self._Expression(FSys | _SET_RPAREN)
        ArgList = self._NewArg(ArgList, 0)
        if self.gAttr.Typtr is not None:
            if not self._RealString(self.gAttr):
                self.Error(123)
        self._RightParen()
        self.gAttr.TreePtr = ArgList

    def _xRead(self, FSys: set[Symbol] | frozenset[Symbol], fKey: int) -> None:
        """Compile `READ` and `READLN` on `Text` files (defaulting to `Input`) and target variables."""
        ActArgList: Optional[N] = None
        FileArg: Optional[N] = None
        TextFlag = True
        DoneFlag = False
        if self.Token == Symbol.LPARENSY:
            self.Scan()
            self._CallVariable(FSys | _SET_COMMA_RPAREN)
            if self.gAttr.Typtr is not None:
                ty = self.gAttr.Typtr
                if ty.Form == TypeForms.FILES:
                    TextFlag = (ty.FileOf == self.CharPtr) and ty.PckdFile
                    if not TextFlag:
                        self.Error(148)
                    FileArg = self._NewArg(FileArg, 0)
                    if self.Token == Symbol.COMMASY:
                        self.Scan()
                        self._CallVariable(FSys | _SET_COMMA_RPAREN)
                    else:
                        DoneFlag = True
            while not DoneFlag:
                Op = 0
                SubOp = 0
                if TextFlag:
                    if self.CompTypes(self.gAttr.Typtr, self.IntPtr):
                        Op = 1
                        lSize = self.FullBytes(self.gAttr.Typtr)
                        if lSize == 1:
                            SubOp = 32  # ASS1
                        elif lSize == 2:
                            SubOp = 33  # ASS2
                        else:
                            SubOp = 34  # ASS4
                    elif self.CompTypes(self.gAttr.Typtr, self.RealPtr):
                        Op = 2
                        SubOp = 34  # ASS4
                    elif self.CompTypes(self.gAttr.Typtr, self.CharPtr):
                        Op = 0
                        SubOp = 33  # ASS2
                    elif self._RealString(self.gAttr):
                        Op = 3
                        SubOp = self.gAttr.Typtr.StringLen if self.gAttr.Typtr is not None else 0
                    elif self._PAoC(self.gAttr.Typtr):
                        Lo, Hi = self.GetBounds(self.gAttr.Typtr.IndexedBy)
                        Op = 4
                        SubOp = Hi
                    else:
                        self.Error(148)
                else:
                    Op = 0
                    SubOp = 0
                ActArgList = self._NewArg(ActArgList, Op)
                lpN = ActArgList
                while lpN.RightArg is not None:
                    lpN = lpN.RightArg
                lpN.BinSubOp = SubOp
                if self.Token == Symbol.COMMASY:
                    self.Scan()
                    self._CallVariable(FSys | _SET_COMMA_RPAREN)
                else:
                    DoneFlag = True
            self._RightParen()
        if fKey == 9 and not TextFlag:  # READLN
            self.Error(148)
        if fKey == 8 and ActArgList is None:  # READ
            self.Error(148)
        if FileArg is None:
            FileArg = self._NewBinNode(0, self.InputPtr, None)
        FileArg.RightArg = ActArgList
        self.gAttr.TreePtr = FileArg

    def _xWrite(self, FSys: set[Symbol] | frozenset[Symbol], fKey: int) -> None:
        """Compile `WRITE` and `WRITELN` on `Text` files (defaulting to `Output`) with `:width[:frac]` specifiers."""
        ActArgList: Optional[N] = None
        FileArg: Optional[N] = None
        TextFlag = True
        DoneFlag = False
        if self.Token == Symbol.LPARENSY:
            self.Scan()
            self._Expression(FSys | _SET_COMMA_COLON_RPAREN)
            if self.gAttr.Typtr is not None:
                ty = self.gAttr.Typtr
                if ty.Form == TypeForms.FILES:
                    TextFlag = (ty.FileOf == self.CharPtr) and ty.PckdFile
                    if not TextFlag:
                        self.Error(123)
                    FileArg = self._NewArg(FileArg, 0)
                    if self.Token == Symbol.COMMASY:
                        self.Scan()
                        self._Expression(FSys | _SET_COMMA_COLON_RPAREN)
                    else:
                        DoneFlag = True
            while not DoneFlag:
                Op = 0
                if TextFlag:
                    if self.CompTypes(self.gAttr.Typtr, self.IntPtr):
                        Op = 2
                        self._MakeScSize(self.gAttr, 4)
                    elif self.CompTypes(self.gAttr.Typtr, self.CharPtr):
                        Op = 0
                        self._MakeScSize(self.gAttr, 1)
                    elif self.CompTypes(self.gAttr.Typtr, self.BoolPtr):
                        Op = 1
                        self._MakeScSize(self.gAttr, 1)
                    elif self.CompTypes(self.gAttr.Typtr, self.RealPtr):
                        Op = 3
                    elif self._RealString(self.gAttr):
                        Op = 5
                    elif self._PAoC(self.gAttr.Typtr):
                        Op = 6
                        lpN = N(NodeKind.CSTNODE)
                        lpN.CstType = self.IntPtr
                        Lo, Hi = self.GetBounds(self.gAttr.Typtr.IndexedBy)
                        lpN.CstValu.Ivalu = Hi
                        self.gAttr.TreePtr = self._NewBinNode(0, self.gAttr.TreePtr, lpN)  # COLON
                    else:
                        self.Error(123)

                    if self.Token == Symbol.COLONSY:
                        lAttr = self.gAttr.copy()
                        self.Scan()
                        self._Expression(FSys | _SET_COMMA_COLON_RPAREN)
                        if not self.CompTypes(self.gAttr.Typtr, self.IntPtr):
                            self.Error(123)
                        else:
                            self._MakeScSize(self.gAttr, 2)
                        lAttr.TreePtr = self._NewBinNode(
                            0, lAttr.TreePtr, self.gAttr.TreePtr  # COLON
                        )
                        if self.Token == Symbol.COLONSY:
                            if Op != 3:
                                self.Error(121)
                            Op = 4
                            self.Scan()
                            self._Expression(FSys | _SET_COMMA_RPAREN)
                            if not self.CompTypes(self.gAttr.Typtr, self.IntPtr):
                                self.Error(123)
                            else:
                                self._MakeScSize(self.gAttr, 2)
                            lAttr.TreePtr = self._NewBinNode(
                                0, lAttr.TreePtr, self.gAttr.TreePtr  # COLON
                            )
                        self.gAttr.set_from(lAttr)
                    ActArgList = self._NewArg(ActArgList, Op)
                else:
                    ActArgList = self._NewArg(ActArgList, 0)

                if self.Token == Symbol.COMMASY:
                    self.Scan()
                    self._Expression(FSys | _SET_COMMA_COLON_RPAREN)
                else:
                    DoneFlag = True
            self._RightParen()
        if fKey == 11 and not TextFlag:  # WRITELN
            self.Error(123)
        if fKey == 10 and ActArgList is None:  # WRITE
            self.Error(123)
        if FileArg is None:
            FileArg = self._NewBinNode(0, self.OutputPtr, None)
        FileArg.RightArg = ActArgList
        self.gAttr.TreePtr = FileArg

    def _xClose(self, FSys: set[Symbol] | frozenset[Symbol]) -> None:
        """Compile `CLOSE(f [, NORMAL|LOCK|PURGE|CRUNCH])` on a file variable."""
        ArgList: Optional[N] = None
        n_val = 0
        self._LeftParen()
        self._CallVariable(FSys | _SET_COMMA_RPAREN)
        ArgList = self._NewArg(ArgList, 0)
        if self.gAttr.Typtr is not None:
            if self.gAttr.Typtr.Form != TypeForms.FILES:
                self.Error(123)
        if self.Token == Symbol.COMMASY:
            self.Scan()
            if self.Token == Symbol.IDENTSY:
                if self.Ident == 'NORMAL  ':
                    n_val = 0
                elif self.Ident == 'LOCK    ':
                    n_val = 1
                elif self.Ident == 'PURGE   ':
                    n_val = 2
                elif self.Ident == 'CRUNCH  ':
                    n_val = 3
                else:
                    self.Error(123)
                self.Scan()
            else:
                self.Error(123)
        lpN = N(NodeKind.CSTNODE)
        lpN.CstType = self.IntPtr
        lpN.CstValu.Ivalu = n_val
        self.gAttr.TreePtr = lpN
        ArgList = self._NewArg(ArgList, 0)
        self._RightParen()
        self.gAttr.TreePtr = ArgList

    def _GetPutPage(self, FSys: set[Symbol] | frozenset[Symbol], fKey: int) -> None:
        """Compile `GET(f)`, `PUT(f)`, and `PAGE(f)` (requiring a `Text` file for `PAGE`)."""
        self._LeftParen()
        self._CallVariable(FSys | _SET_RPAREN)
        self.gAttr.TreePtr = self._NewBinNode(0, self.gAttr.TreePtr, None)
        if self.gAttr.Typtr is not None:
            ty = self.gAttr.Typtr
            if ty.Form != TypeForms.FILES:
                self.Error(123)
            elif fKey == 12:  # PAGE
                if ty.FileOf != self.CharPtr or not ty.PckdFile:
                    self.Error(123)
        self._RightParen()

    def _PackUnpack(self, FSys: set[Symbol] | frozenset[Symbol], fKey: int) -> None:
        """Report error 306 for unsupported `PACK`/`UNPACK` calls and skip any argument list."""
        self.Error(306)
        if self.Token == Symbol.LPARENSY:
            while True:
                self.Scan()
                self._Expression(FSys | _SET_COMMA_RPAREN)
                if self.Token != Symbol.COMMASY:
                    break
            self._RightParen()

    def _InsrtDel(self, FSys: set[Symbol] | frozenset[Symbol], fKey: int) -> None:
        """Compile string intrinsics `INSERT(src, dst, index)` and `DELETE(dst, index, count)`."""
        ArgList: Optional[N] = None
        self._LeftParen()
        if fKey == 17:  # INSERT
            self._Expression(FSys | _SET_COMMA_RPAREN)
            ArgList = self._NewArg(ArgList, 0)
            if self.gAttr.Typtr is not None:
                if not self._RealString(self.gAttr):
                    self.Error(123)
            self._Comma()
        self._CallVariable(FSys | _SET_COMMA_RPAREN)
        ArgList = self._NewArg(ArgList, 0)
        if self.gAttr.Typtr is not None:
            if self.gAttr.Typtr.Form != TypeForms.STRINGS:
                self.Error(123)
        self._Comma()
        self._Expression(FSys | _SET_COMMA_RPAREN)
        if not self.CompTypes(self.gAttr.Typtr, self.IntPtr):
            self.Error(123)
        self._MakeScSize(self.gAttr, 2)
        ArgList = self._NewArg(ArgList, 0)
        if fKey == 16:  # DELETE
            self._Comma()
            self._Expression(FSys | _SET_RPAREN)
            if not self.CompTypes(self.gAttr.Typtr, self.IntPtr):
                self.Error(123)
            self._MakeScSize(self.gAttr, 2)
            ArgList = self._NewArg(ArgList, 0)
        self._RightParen()
        self.gAttr.TreePtr = ArgList

    def _UnitRWs(self, FSys: set[Symbol] | frozenset[Symbol], fKey: int) -> None:
        """Compile low-level device intrinsics `UNITREAD`, `UNITWRITE`, and `UNITSTATUS`."""
        ArgList: Optional[N] = None
        self._LeftParen()
        self._Expression(FSys | _SET_COMMA_RPAREN)
        self._MakeScSize(self.gAttr, 2)
        ArgList = self._NewArg(ArgList, 0)
        if not self.CompTypes(self.gAttr.Typtr, self.IntPtr):
            self.Error(123)
        self._Comma()
        self._CallVariable(FSys | _SET_COMMA_RPAREN)
        ArgList = self._NewArg(ArgList, 0)
        Count = 0
        while self.Token == Symbol.COMMASY:
            self.Scan()
            Count = Count + 1
            self._Expression(FSys | _SET_COMMA_RPAREN)
            self._MakeScSize(self.gAttr, 2)
            ArgList = self._NewArg(ArgList, 0)
            if not self.CompTypes(self.gAttr.Typtr, self.IntPtr):
                self.Error(123)
        if Count == 0 or Count > 3 or (Count > 1 and fKey == 28):  # UNITSTATUS
            self.Error(124)
        self._RightParen()
        self.gAttr.TreePtr = ArgList

    def _xSeek(self, FSys: set[Symbol] | frozenset[Symbol]) -> None:
        """Compile `SEEK(f, recnum)` on a file variable and integer record index."""
        ArgList: Optional[N] = None
        self._LeftParen()
        self._CallVariable(FSys | _SET_COMMA_RPAREN)
        ArgList = self._NewArg(ArgList, 0)
        if self.gAttr.Typtr is not None:
            if self.gAttr.Typtr.Form != TypeForms.FILES:
                self.Error(123)
        self._Comma()
        self._Expression(FSys | _SET_COMMA_RPAREN)
        self._MakeScSize(self.gAttr, 2)
        ArgList = self._NewArg(ArgList, 0)
        if not self.CompTypes(self.gAttr.Typtr, self.IntPtr):
            self.Error(123)
        self._RightParen()
        self.gAttr.TreePtr = ArgList

    def _MoveLR(self, FSys: set[Symbol] | frozenset[Symbol]) -> None:
        """Compile byte-move intrinsics `MOVELEFT(src, dst, count)` and `MOVERIGHT(src, dst, count)`."""
        ArgList: Optional[N] = None
        self._LeftParen()
        self._CallVariable(FSys | _SET_COMMA_RPAREN)
        ArgList = self._NewArg(ArgList, 0)
        self._Comma()
        self._CallVariable(FSys | _SET_COMMA_RPAREN)
        ArgList = self._NewArg(ArgList, 0)
        self._Comma()
        self._Expression(FSys | _SET_COMMA_RPAREN)
        self._MakeScSize(self.gAttr, 2)
        ArgList = self._NewArg(ArgList, 0)
        if not self.CompTypes(self.gAttr.Typtr, self.IntPtr):
            self.Error(123)
        self._RightParen()
        self.gAttr.TreePtr = ArgList

    def _xFill(self, FSys: set[Symbol] | frozenset[Symbol]) -> None:
        """Compile `FILLCHAR(dst, count, ch)` on a `Char` or packed `Char` array buffer."""
        ArgList: Optional[N] = None
        self._LeftParen()
        self._CallVariable(FSys | _SET_COMMA_RPAREN)
        ArgList = self._NewArg(ArgList, 0)
        if self.gAttr.Typtr is not None:
            ty = self.gAttr.Typtr
            if ty.Form == TypeForms.ARRAYS:
                if ty.ArrayOf != self.CharPtr or not ty.PckdArr:
                    self.Error(123)
            elif ty != self.CharPtr:
                self.Error(123)
        self._Comma()
        self._Expression(FSys | _SET_COMMA_RPAREN)
        self._MakeScSize(self.gAttr, 2)
        ArgList = self._NewArg(ArgList, 0)
        if not self.CompTypes(self.gAttr.Typtr, self.IntPtr):
            self.Error(123)
        self._Comma()
        self._Expression(FSys | _SET_COMMA_RPAREN)
        self._MakeScSize(self.gAttr, 2)
        ArgList = self._NewArg(ArgList, 0)
        if not self.CompTypes(self.gAttr.Typtr, self.CharPtr):
            self.Error(123)
        self._RightParen()
        self.gAttr.TreePtr = ArgList

    def _UClear(self, FSys: set[Symbol] | frozenset[Symbol]) -> None:
        """Compile `UNITCLEAR(unitnum)` for an integer device unit number."""
        ArgList: Optional[N] = None
        self._LeftParen()
        self._Expression(FSys | _SET_RPAREN)
        self._MakeScSize(self.gAttr, 2)
        ArgList = self._NewArg(ArgList, 0)
        if not self.CompTypes(self.gAttr.Typtr, self.IntPtr):
            self.Error(123)
        self._RightParen()
        self.gAttr.TreePtr = ArgList

    def _xGotoXY(self, FSys: set[Symbol] | frozenset[Symbol]) -> None:
        """Compile `GOTOXY(x, y)` cursor-positioning intrinsic with two integer coordinates."""
        ArgList: Optional[N] = None
        self._LeftParen()
        self._Expression(FSys | _SET_COMMA_RPAREN)
        self._MakeScSize(self.gAttr, 2)
        ArgList = self._NewArg(ArgList, 0)
        if not self.CompTypes(self.gAttr.Typtr, self.IntPtr):
            self.Error(123)
        self._Comma()
        self._Expression(FSys | _SET_RPAREN)
        self._MakeScSize(self.gAttr, 2)
        ArgList = self._NewArg(ArgList, 0)
        if not self.CompTypes(self.gAttr.Typtr, self.IntPtr):
            self.Error(123)
        self._RightParen()
        self.gAttr.TreePtr = ArgList

    def _xExit(self, FSys: set[Symbol] | frozenset[Symbol]) -> None:
        """Compile `EXIT(procname)`, matching `procname` against active enclosing routines on `Display`."""
        self._LeftParen()
        ArgList: Optional[N] = None
        if self.Token == Symbol.IDENTSY:
            lpN: Optional[N] = None
            found = False
            for i in range(self.Top, 0, -1):
                disp = self.Display[i]
                if disp.Occur == Where.BLK:
                    lpN = disp.RootLink
                    if lpN is not None:
                        if self.Ident == lpN.Name:
                            if lpN.Class == NameClass.PROC or lpN.Class == NameClass.FUNC:
                                found = True
                                break
            if not found:
                lpN = self.uPrcPtr
                self.Error(174)
            # 1:
            self.Scan()
            ArgList = self._NewBinNode(0, lpN, None)
        else:
            self.Error(29)
        self._RightParen()
        self.gAttr.TreePtr = ArgList

    def _CallStdProc(self, FSys: set[Symbol] | frozenset[Symbol], FpN: N) -> None:
        """Dispatch a standard built-in procedure call according to `FpN.Key`."""
        k = FpN.Key
        if k == 1 or k == 27:       # NEW, DISPOSE
            self._xNewDispose(FSys)
        elif k == 2 or k == 3:      # MARK, RELEASE
            self._MarkRelease(FSys)
        elif k == 4 or k == 5 or k == 12:  # GET, PUT, PAGE
            self._GetPutPage(FSys, k)
        elif k == 6 or k == 7:      # RESET, REWRITE
            self._ResetWrite(FSys)
        elif k == 8 or k == 9:      # READ, READLN
            self._xRead(FSys, k)
        elif k == 10 or k == 11:    # WRITE, WRITELN
            self._xWrite(FSys, k)
        elif k == 13 or k == 14:    # PACK, UNPACK
            self._PackUnpack(FSys, k)
        elif k == 15:               # CLOSE
            self._xClose(FSys)
        elif k == 16 or k == 17:    # DELETE, INSERT
            self._InsrtDel(FSys, k)
        elif k == 18 or k == 19 or k == 28:  # UNITREAD, UNITWRITE, UNITSTATUS
            self._UnitRWs(FSys, k)
        elif k == 20:               # SEEK
            self._xSeek(FSys)
        elif k == 21:               # HALT
            pass
        elif k == 22 or k == 23:    # MOVELEFT, MOVERIGHT
            self._MoveLR(FSys)
        elif k == 24:               # FILLCHAR
            self._xFill(FSys)
        elif k == 25:               # UNITCLEAR
            self._UClear(FSys)
        elif k == 26:               # GOTOXY
            self._xGotoXY(FSys)
        elif k == 29:               # EXIT
            self._xExit(FSys)

    # ---- Standard Functions ----

    def _NewTemp(self, FpT: Optional[T]) -> N:
        """Allocate an even-aligned stack temporary of type `FpT` in `CurrentProc`'s local frame."""
        lSize = self.FullBytes(FpT)
        lLc = -self.CurrentProc.Lc
        if odd(lLc):
            lLc = lLc - 1
        if odd(lSize):
            lSize = lSize + 1
        lLc = lLc - lSize
        self.CurrentProc.Lc = -lLc
        FpN = N(NodeKind.IDENTNODE)
        FpN.Class = NameClass.VARS
        FpN.IdType = None
        FpN.Vkind = AccessKind.DRCT
        FpN.Vlev = self.Level
        FpN.Voff = lLc
        return FpN

    def _Math(self, FSys: set[Symbol] | frozenset[Symbol]) -> None:
        """Compile unary math intrinsics (`ARCTAN`, `COS`, `EXP`, `LN`, `SIN`, `SQRT`), promoting integers to `Real`."""
        self._LeftParen()
        self._Expression(FSys | _SET_RPAREN)
        if self.CompTypes(self.gAttr.Typtr, self.IntPtr):
            self._Float(self.gAttr)
        self.gAttr.TreePtr = self._NewBinNode(0, self.gAttr.TreePtr, None)
        if not self.CompTypes(self.gAttr.Typtr, self.RealPtr):
            self.Error(122)
        self._RightParen()
        self.gAttr.ASize = 4

    def _xChr(self, FSys: set[Symbol] | frozenset[Symbol]) -> None:
        """Compile `CHR(n)`, inserting a `Char` range check under `$R+` and typing the result as `Char`."""
        self._LeftParen()
        self._Expression(FSys | _SET_RPAREN)
        self._MakeScSize(self.gAttr, 2)
        if self.RangeFlag:
            self.gAttr.TreePtr = self._NewBinNode(46, None, self.gAttr.TreePtr)  # RCHECK
            self.gAttr.TreePtr.LeftPt = self.CharPtr
        self.gAttr.TreePtr = self._NewBinNode(0, self.gAttr.TreePtr, None)
        if not self.CompTypes(self.gAttr.Typtr, self.IntPtr):
            self.Error(122)
        self._RightParen()
        self.gAttr.Typtr = self.CharPtr
        self.gAttr.ASize = 2

    def _xOdd(self, FSys: set[Symbol] | frozenset[Symbol]) -> None:
        """Compile `ODD(n)`, narrowing the integer argument to 1 byte and returning `Boolean`."""
        self._LeftParen()
        self._Expression(FSys | _SET_RPAREN)
        self._MakeScSize(self.gAttr, 1)
        self.gAttr.TreePtr = self._NewBinNode(0, self.gAttr.TreePtr, None)
        if not self.CompTypes(self.gAttr.Typtr, self.IntPtr):
            self.Error(122)
        self._RightParen()
        self.gAttr.Typtr = self.BoolPtr
        self.gAttr.ASize = 1

    def _xOrd(self, FSys: set[Symbol] | frozenset[Symbol], Ord4Flag: bool) -> None:
        """Compile `ORD(x)` and `ORD4(x)` on scalar, subrange, class, or pointer operands."""
        self._LeftParen()
        self._Expression(FSys | _SET_RPAREN)
        if self.gAttr.Typtr is not None:
            if (
                self.gAttr.Typtr.Form > TypeForms.POINTERS
                or self.CompTypes(self.gAttr.Typtr, self.RealPtr)
            ):
                self.Error(122)
        if self.gAttr.ASize <= 1:
            self.gAttr.Typtr = self.SIntPtr
        elif self.gAttr.ASize == 2:
            self.gAttr.Typtr = self.IntPtr
        else:
            self.gAttr.Typtr = self.LIntPtr
        if Ord4Flag:
            self._MakeScSize(self.gAttr, 4)
        self.gAttr.TreePtr = self._NewBinNode(0, self.gAttr.TreePtr, None)
        self._RightParen()

    def _PredSucc(self, FSys: set[Symbol] | frozenset[Symbol]) -> None:
        """Compile `PRED(x)` and `SUCC(x)` on discrete ordinal expressions."""
        self._LeftParen()
        self._Expression(FSys | _SET_RPAREN)
        self._MinSize2(self.gAttr)
        self.gAttr.TreePtr = self._NewBinNode(0, self.gAttr.TreePtr, None)
        self.gAttr.TreePtr.BinSubOp = self.gAttr.ASize
        if self.gAttr.Typtr is not None:
            if (
                self.gAttr.Typtr.Form > TypeForms.SUBRANGE
                or self.CompTypes(self.gAttr.Typtr, self.RealPtr)
            ):
                self.Error(122)
        self._RightParen()

    def _AbsSqr(self, FSys: set[Symbol] | frozenset[Symbol], fKey: int) -> None:
        """Compile `ABS(x)` and `SQR(x)` for integer or `Real` operands, adding `TRAPV` under `$OV+`."""
        self._LeftParen()
        self._Expression(FSys | _SET_RPAREN)
        if self.CompTypes(self.gAttr.Typtr, self.IntPtr):
            self._MinSize2(self.gAttr)
            if self.gAttr.ASize <= 2:
                lOp = 76  # ABS2
            else:
                lOp = 77  # ABS4
        elif self.CompTypes(self.gAttr.Typtr, self.RealPtr):
            lOp = 136  # FABS4
        else:
            self.Error(122)
            lOp = 76
        if fKey == 14:  # SQR
            lOp = lOp + 2  # ABS-->SQR
        self.gAttr.TreePtr = self._NewBinNode(lOp, self.gAttr.TreePtr, None)
        if self.OflowFlag:
            if lOp <= 79:
                self.gAttr.TreePtr = self._NewUnNode(0x8C, self.gAttr.TreePtr)  # TRAPV
        self._RightParen()

    def _EofEolnKeypress(self, FSys: set[Symbol] | frozenset[Symbol], fKey: int) -> None:
        """Compile `EOF`, `EOLN`, and `KEYPRESS` on an optional file variable (defaulting to `Input`)."""
        if self.Token == Symbol.LPARENSY:
            self.Scan()
            self._CallVariable(FSys | _SET_RPAREN)
            self.gAttr.TreePtr = self._NewBinNode(0, self.gAttr.TreePtr, None)
            if self.gAttr.Typtr is not None:
                ty = self.gAttr.Typtr
                if ty.Form != TypeForms.FILES:
                    self.Error(122)
                elif fKey == 6 or fKey == 34:  # EOLN or KEYPRESS
                    if not self.CompTypes(ty.FileOf, self.CharPtr):
                        self.Error(122)
            self._RightParen()
        else:
            self.gAttr.TreePtr = self._NewBinNode(0, self.InputPtr, None)
        self.gAttr.Typtr = self.BoolPtr
        self.gAttr.ASize = 1

    def _RoundTrunc(self, FSys: set[Symbol] | frozenset[Symbol]) -> None:
        """Compile `ROUND(x)` and `TRUNC(x)`, converting a `Real` expression to `LongInt`."""
        self._LeftParen()
        self._Expression(FSys | _SET_RPAREN)
        self.gAttr.TreePtr = self._NewBinNode(0, self.gAttr.TreePtr, None)
        if not self.CompTypes(self.gAttr.Typtr, self.RealPtr):
            self.Error(122)
        self._RightParen()
        self.gAttr.Typtr = self.LIntPtr
        self.gAttr.ASize = 4

    def _xPointer(self, FSys: set[Symbol] | frozenset[Symbol]) -> None:
        """Compile `POINTER(addr)`, converting an integer expression into a universal `NilPtr` pointer."""
        self._LeftParen()
        self._Expression(FSys | _SET_RPAREN)
        self._MakeScSize(self.gAttr, 4)
        self.gAttr.TreePtr = self._NewBinNode(0, self.gAttr.TreePtr, None)
        if self.gAttr.Typtr is not None:
            if self.gAttr.Typtr.Form == TypeForms.CLASSES:
                if not self.CompTypes(self.gAttr.Typtr, self.IntPtr):
                    self.Error(122)
        self._RightParen()
        self.gAttr.Typtr = self.NilPtr
        self.gAttr.ASize = 4

    def _LenPos(self, FSys: set[Symbol] | frozenset[Symbol], fKey: int) -> None:
        """Compile string functions `LENGTH(s)` and `POS(sub, s)`, returning `Integer`."""
        ArgList: Optional[N] = None
        self._LeftParen()
        self._Expression(FSys | _SET_COMMA_RPAREN)
        ArgList = self._NewArg(ArgList, 0)
        if not self._RealString(self.gAttr):
            self.Error(122)
        if fKey == 20:  # POS
            self._Comma()
            self._Expression(FSys | _SET_RPAREN)
            ArgList = self._NewArg(ArgList, 0)
            if not self._RealString(self.gAttr):
                self.Error(122)
        self._RightParen()
        self.gAttr.TreePtr = ArgList
        self.gAttr.Typtr = self.IntPtr
        self.gAttr.ASize = 2

    def _xConcat(self, FSys: set[Symbol] | frozenset[Symbol]) -> None:
        """Compile `CONCAT(s1, s2, ...)`, allocating a temporary `String` result capped at 255 chars."""
        ArgList: Optional[N] = None
        ExitFlag = False
        MaxSize = 0
        self._LeftParen()
        while True:
            self._Expression(FSys | _SET_COMMA_RPAREN)
            ArgList = self._NewArg(ArgList, 0)
            if self._RealString(self.gAttr):
                if self.gAttr.Typtr is not None:
                    MaxSize = MaxSize + self.gAttr.Typtr.StringLen
            else:
                self.Error(122)
            if self.Token == Symbol.COMMASY:
                self.Scan()
            else:
                ExitFlag = True
            if ExitFlag:
                break
        self._RightParen()
        if MaxSize > 255:
            MaxSize = 255
        lpT = T(TypeForms.STRINGS)
        lpT.Bytes = pdiv(MaxSize + 2, 2) * 2
        lpT.Bits = 0
        lpT.FType = False
        lpT.StringLen = MaxSize
        self.gAttr.TreePtr = self._NewTemp(lpT)
        ArgList = self._NewArg(ArgList, 0)
        self.gAttr.TreePtr = ArgList
        self.gAttr.Typtr = lpT

    def _xCopy(self, FSys: set[Symbol] | frozenset[Symbol]) -> None:
        """Compile `COPY(s, index, count)`, allocating a temporary `String` destination slot."""
        ArgList: Optional[N] = None
        self._LeftParen()
        self._Expression(FSys | _SET_COMMA_RPAREN)
        ArgList = self._NewArg(ArgList, 0)
        if not self._RealString(self.gAttr):
            self.Error(122)
        lpT = self.gAttr.Typtr
        self._Comma()
        self._Expression(FSys | _SET_COMMA_RPAREN)
        self._MakeScSize(self.gAttr, 2)
        ArgList = self._NewArg(ArgList, 0)
        if not self.CompTypes(self.gAttr.Typtr, self.IntPtr):
            self.Error(122)
        self._Comma()
        self._Expression(FSys | _SET_RPAREN)
        self._MakeScSize(self.gAttr, 2)
        ArgList = self._NewArg(ArgList, 0)
        if not self.CompTypes(self.gAttr.Typtr, self.IntPtr):
            self.Error(122)
        self._RightParen()
        self.gAttr.TreePtr = self._NewTemp(lpT)
        ArgList = self._NewArg(ArgList, 0)
        self.gAttr.TreePtr = ArgList
        self.gAttr.Typtr = lpT

    def _BlockRW(self, FSys: set[Symbol] | frozenset[Symbol]) -> None:
        """Compile untyped file functions `BLOCKREAD` and `BLOCKWRITE`, returning `Integer`."""
        ArgList: Optional[N] = None
        self._LeftParen()
        self._CallVariable(FSys | _SET_COMMA_RPAREN)
        ArgList = self._NewArg(ArgList, 0)
        if self.gAttr.Typtr is not None:
            if self.gAttr.Typtr.Form != TypeForms.FILES:
                self.Error(122)
            elif self.gAttr.Typtr.FileOf is not None:
                self.Error(122)
        self._Comma()
        self._CallVariable(FSys | _SET_COMMA_RPAREN)
        ArgList = self._NewArg(ArgList, 0)
        self._Comma()
        self._Expression(FSys | _SET_COMMA_RPAREN)
        self._MakeScSize(self.gAttr, 2)
        ArgList = self._NewArg(ArgList, 0)
        if not self.CompTypes(self.gAttr.Typtr, self.IntPtr):
            self.Error(122)
        if self.Token == Symbol.COMMASY:
            self.Scan()
            self._Expression(FSys | _SET_COMMA_RPAREN)
            self._MakeScSize(self.gAttr, 2)
            ArgList = self._NewArg(ArgList, 0)
            if not self.CompTypes(self.gAttr.Typtr, self.IntPtr):
                self.Error(122)
        self._RightParen()
        self.gAttr.TreePtr = ArgList
        self.gAttr.Typtr = self.IntPtr
        self.gAttr.ASize = 2

    def _xIOResMem(self, fKey: int) -> None:
        """Compile parameterless inquiries `IORESULT`, `HEAPRESULT` (`Integer`), and `MEMAVAIL` (`LongInt`)."""
        self.gAttr.TreePtr = None
        if fKey == 25 or fKey == 33:  # IORESULT or HEAPRESULT
            self.gAttr.Typtr = self.IntPtr
            self.gAttr.ASize = 2
        else:  # MEMAVAIL
            self.gAttr.Typtr = self.LIntPtr
            self.gAttr.ASize = 4

    def _xSizeOf(self, FSys: set[Symbol] | frozenset[Symbol]) -> None:
        """Compile `SIZEOF(x)` on a type name or variable, folding its byte or instance size to a constant."""
        ArgList: Optional[N] = None
        TypeFlag = False
        lpN: Optional[N] = None
        self._LeftParen()
        if self.Token == Symbol.IDENTSY:
            self.PrintErrors = False
            lpN = self.SearchAll(_SEARCH_TYPES)
            self.PrintErrors = True
            TypeFlag = lpN is not None
        if TypeFlag:
            lpT = lpN.IdType
            self.Scan()
        else:
            self._CallVariable(FSys | _SET_RPAREN)
            lpT = self.gAttr.Typtr
        cst = N(NodeKind.CSTNODE)
        cst.CstType = self.IntPtr
        if lpT is None:
            cst.CstValu.Ivalu = 0
        elif lpT.Form == TypeForms.CLASSES:
            cst.CstValu.Ivalu = lpT.SizeInstance
        else:
            cst.CstValu.Ivalu = self.FullBytes(lpT)
        self.gAttr.TreePtr = cst
        self.gAttr.Typtr = self.IntPtr
        ArgList = self._NewArg(ArgList, 0)
        self._RightParen()
        self.gAttr.TreePtr = ArgList
        self.gAttr.ASize = 2

    def _xPwrOf(self, FSys: set[Symbol] | frozenset[Symbol]) -> None:
        """Compile `PWROFTEN(exp)`, returning a `Real` power of ten for an integer exponent."""
        ArgList: Optional[N] = None
        self._LeftParen()
        self._Expression(FSys | _SET_RPAREN)
        self._MakeScSize(self.gAttr, 2)
        ArgList = self._NewArg(ArgList, 0)
        if not self.CompTypes(self.gAttr.Typtr, self.IntPtr):
            self.Error(122)
        self._RightParen()
        self.gAttr.TreePtr = ArgList
        self.gAttr.Typtr = self.RealPtr
        self.gAttr.ASize = 4

    def _ScanEqNe(self, FSys: set[Symbol] | frozenset[Symbol]) -> None:
        """Compile `SCANEQ(limit, ch, buf)` and `SCANNE(limit, ch, buf)` character-array scan functions."""
        ArgList: Optional[N] = None
        self._LeftParen()
        self._Expression(FSys | _SET_COMMA_RPAREN)
        self._MakeScSize(self.gAttr, 2)
        ArgList = self._NewArg(ArgList, 0)
        if not self.CompTypes(self.gAttr.Typtr, self.IntPtr):
            self.Error(122)
        self._Comma()
        self._Expression(FSys | _SET_COMMA_RPAREN)
        ArgList = self._NewArg(ArgList, 0)
        if not self.CompTypes(self.gAttr.Typtr, self.CharPtr):
            self.Error(122)
        self._Comma()
        self._CallVariable(FSys | _SET_RPAREN)
        ArgList = self._NewArg(ArgList, 0)
        if self.gAttr.Typtr is not None:
            ty = self.gAttr.Typtr
            if ty.Form == TypeForms.ARRAYS:
                if ty.ArrayOf != self.CharPtr or not ty.PckdArr:
                    self.Error(122)
            elif ty != self.CharPtr:
                self.Error(122)
        self._RightParen()
        self.gAttr.TreePtr = ArgList
        self.gAttr.Typtr = self.IntPtr
        self.gAttr.ASize = 2

    def _UBusy(self, FSys: set[Symbol] | frozenset[Symbol]) -> None:
        """Compile `UNITBUSY(unitnum)`, returning `Boolean` for an integer unit number."""
        ArgList: Optional[N] = None
        self._LeftParen()
        self._Expression(FSys | _SET_RPAREN)
        self._MakeScSize(self.gAttr, 2)
        ArgList = self._NewArg(ArgList, 0)
        if not self.CompTypes(self.gAttr.Typtr, self.IntPtr):
            self.Error(122)
        self._RightParen()
        self.gAttr.TreePtr = ArgList
        self.gAttr.Typtr = self.BoolPtr
        self.gAttr.ASize = 1

    def _xThisClass(self) -> None:
        """Compile Clascal `THISCLASS`, returning a pointer to the enclosing method's class descriptor."""
        if self.ThisClass is None:
            self.Error(819)
        else:
            lpN = N(NodeKind.IDENTNODE)
            lpN.Class = NameClass.VARS
            lpN.Vkind = AccessKind.DRCT
            lpN.Next = None
            lpN.IdType = self.LIntPtr
            lpN.InRegister = -1
            lpN.Vlev = self.ThisClass.MethodLevel
            lpN.Voff = self.ThisClass.MethodOff
            self.gAttr.TreePtr = self._NewUnNode(22, lpN)  # ADDR
            ArgList: Optional[N] = None
            ArgList = self._NewArg(ArgList, 0)
            self.gAttr.TreePtr = ArgList
            self.gAttr.Typtr = self.NilPtr
            self.gAttr.ASize = 4

    def _xInClass(self, FSys: set[Symbol] | frozenset[Symbol]) -> None:
        """Compile Clascal `INCLASS(obj, ClassName)`, testing whether `obj` belongs to `ClassName`."""
        ArgList: Optional[N] = None
        self._LeftParen()
        self._Expression(FSys | _SET_COMMA_RPAREN)
        ArgList = self._NewArg(ArgList, 0)
        if self.gAttr.Typtr is not None:
            if self.gAttr.Typtr.Form != TypeForms.CLASSES:
                self.Error(122)
        self._Comma()
        self.gAttr.TreePtr = None
        SubOp = -1  # -1 ==> error
        if self.Token == Symbol.IDENTSY:
            lpN = self.SearchAll(_SEARCH_TYPES)
            self.Scan()
        else:
            self.Error(29)
            lpN = None
        if lpN is not None:
            if lpN.IdType is not None:
                if lpN.IdType.Form != TypeForms.CLASSES:
                    self.Error(122)
                elif lpN.IdType.NeedsInit:
                    SubOp = int(NodeKind.IDENTNODE)
                    tree = N(NodeKind.IDENTNODE)
                    tree.IdType = self.LIntPtr
                    tree.Next = None
                    tree.Class = NameClass.VARS
                    tree.Vkind = AccessKind.DRCT
                    tree.InRegister = -1
                    tree.Vlev = lpN.IdType.MethodLevel
                    tree.Voff = lpN.IdType.MethodOff
                    self.gAttr.TreePtr = tree
                else:
                    SubOp = int(NodeKind.CSTNODE)
                    tree = N(NodeKind.CSTNODE)
                    tree.CstValu.SvaluLen = 8
                    tree.CstValu.Svalu = StrValRec(lpN.Name, None)
                    cst_type = T(TypeForms.SCONST)
                    cst_type.FType = False
                    cst_type.Bits = 0
                    cst_type.Bytes = 8
                    cst_type.StringLen = 8
                    tree.CstType = cst_type
                    self.gAttr.TreePtr = tree
        ArgList = self._NewArg(ArgList, 0)
        ArgList.RightArg.BinSubOp = SubOp
        self._RightParen()
        self.gAttr.TreePtr = ArgList
        self.gAttr.Typtr = self.BoolPtr
        self.gAttr.ASize = 1

    def _CallStdFunc(self, FSys: set[Symbol] | frozenset[Symbol], FpN: N) -> None:
        """Dispatch a standard built-in function call according to `FpN.Key`."""
        k = FpN.Key
        if k == 1 or k == 14:        # ABS, SQR
            self._AbsSqr(FSys, k)
        elif k in (2, 4, 7, 8, 13, 15):  # ARCTAN, COS, EXP, LN, SIN, SQRT
            self._Math(FSys)
        elif k == 3:                 # CHR
            self._xChr(FSys)
        elif k in (5, 6, 34):        # EOF, EOLN, KEYPRESS
            self._EofEolnKeypress(FSys, k)
        elif k == 9:                 # ODD
            self._xOdd(FSys)
        elif k == 10:                # ORD
            self._xOrd(FSys, False)
        elif k == 11 or k == 16:     # PRED, SUCC
            self._PredSucc(FSys)
        elif k == 12 or k == 17:     # ROUND, TRUNC
            self._RoundTrunc(FSys)
        elif k == 18:                # POINTER
            self._xPointer(FSys)
        elif k == 19 or k == 20:     # LENGTH, POS
            self._LenPos(FSys, k)
        elif k == 21:                # CONCAT
            self._xConcat(FSys)
        elif k == 22:                # COPY
            self._xCopy(FSys)
        elif k == 23 or k == 24:     # BLOCKREAD, BLOCKWRITE
            self._BlockRW(FSys)
        elif k in (25, 31, 33):      # IORESULT, MEMAVAIL, HEAPRESULT
            self._xIOResMem(k)
        elif k == 26:                # SIZEOF
            self._xSizeOf(FSys)
        elif k == 27:                # PWROFTEN
            self._xPwrOf(FSys)
        elif k == 28 or k == 29:     # SCANEQ, SCANNE
            self._ScanEqNe(FSys)
        elif k == 30:                # UNITBUSY
            self._UBusy(FSys)
        elif k == 32:                # ORD4
            self._xOrd(FSys, True)
        elif k == 35:                # THISCLASS
            self._xThisClass()
        elif k == 36:                # INCLASS
            self._xInClass(FSys)

    def _Call(self, FSys: set[Symbol] | frozenset[Symbol], FpN: N) -> None:
        """Compile a procedure or function call to `FpN` (standard or user/method-declared)."""
        if FpN.PFdeclKind == DeclKind.STANDARD:
            if FpN.Class == NameClass.PROC:
                self._CallStdProc(FSys, FpN)
            else:
                self._CallStdFunc(FSys, FpN)
        else:
            self._CallNonStandard(FSys, FpN)

    # ---- Statements ----

    def _Assignment(self, FSys: set[Symbol] | frozenset[Symbol], FpN: N) -> Stmt:
        """Parse an assignment (`lhs := rhs`) or standalone Clascal method call starting from `FpN`.

        Checks type, string, and `SELF` superclass compatibility, inserts range and size
        coercions, and chooses the scalar, packed, string, set, or block assignment opcode.
        """
        lNumbr = self.TotalLines
        lStmt = Stmt(StmtTypes.ASSIGNST)
        fStmt = lStmt
        Op = 0
        SubOp = 0
        lStmt.NextStmt = None
        lStmt.AssExpr = None
        lStmt.Flippable = False
        self.ExprDHandle = 0
        self.LHSDHandle = 0
        self.gAttr.Typtr = FpN.IdType
        self.gAttr.TreePtr = FpN
        self.gAttr.ASize = self.FullBytes(self.gAttr.Typtr)
        PckdFlag, PckdStorage = self._Selector(FSys | _SET_ASSIGN, FpN)
        lStmt.AssVar = self.gAttr.TreePtr

        if lStmt.AssVar is None:
            fStmt.StmtNumb = lNumbr
            return fStmt
        if lStmt.AssVar.Node == NodeKind.TRINODE:
            if lStmt.AssVar.TriOp == 184:  # METHODCALL
                if lStmt.AssVar.TripN.Class == NameClass.FUNC:
                    self.Error(804)
                lStmt.StmtOp = StmtTypes.METHODCALL
                fStmt.StmtNumb = lNumbr
                return fStmt

        self.LHSDHandle = self.ExprDHandle
        if self.Token == Symbol.ASSIGNSY:
            lAttr = self.gAttr.copy()
            self.Scan()
            self._Expression(FSys)
            if self.gAttr.Typtr is not None and lAttr.Typtr is not None:
                if (
                    self.CompTypes(lAttr.Typtr, self.RealPtr)
                    and self.CompTypes(self.gAttr.Typtr, self.IntPtr)
                ):
                    self._Float(self.gAttr)
                Ok = self.CompTypes(lAttr.Typtr, self.gAttr.Typtr)
                if not Ok:
                    Ok = self._StringAss(lAttr.Typtr, self.gAttr)
                if not Ok:
                    # 'SELF :=' is compatible with any superclass
                    if lStmt.AssVar is not None:
                        av = lStmt.AssVar
                        if (
                            av.Node == NodeKind.IDENTNODE
                            and av.IdType is not None
                            and av.Class == NameClass.VARS
                            and av.IsSELF
                        ):
                            Ok = self.CompTypes(self.gAttr.Typtr, lAttr.Typtr)
                if Ok:
                    if lAttr.Typtr.FType:
                        self.Error(141)
                    if self.RangeFlag:
                        self._InsertRangeCheck(lAttr.Typtr, self.gAttr)
                    if (
                        lAttr.Typtr.Form <= TypeForms.SUBRANGE
                        and not self.CompTypes(lAttr.Typtr, self.RealPtr)
                    ):
                        if lAttr.ASize != self.gAttr.ASize:
                            self._MakeScSize(self.gAttr, lAttr.ASize)
                    if lAttr.Typtr.Form == TypeForms.SETS:
                        Op = 37
                        SubOp = lAttr.ASize
                        if self.gAttr.ASize != lAttr.ASize:
                            self._MakeSetSize(self.gAttr, lAttr.ASize)
                    elif lAttr.Typtr.Form == TypeForms.STRINGS:
                        Op = 39
                        SubOp = lAttr.Typtr.StringLen
                        if (
                            self.gAttr.Typtr.Form == TypeForms.SCONST
                            or SubOp > self.gAttr.Typtr.StringLen
                        ):
                            SubOp = self.gAttr.Typtr.StringLen
                    elif self._PAoC(lAttr.Typtr):
                        Lo, Hi = self.GetBounds(lAttr.Typtr.IndexedBy)
                        Op = 40
                        SubOp = Hi
                    elif PckdStorage:
                        Op = 38  # PCKDASS
                        if lAttr.TreePtr is not None:
                            if lAttr.TreePtr.Node == NodeKind.TRINODE:  # --> Packed Array
                                if (
                                    self.build30
                                    and self.gAttr.TreePtr is not None
                                    and self.gAttr.TreePtr.Node == NodeKind.CSTNODE
                                    and 128 <= self.gAttr.TreePtr.CstValu.Ivalu <= 255
                                ):
                                    self.gAttr.TreePtr.CstType = self.SIntPtr
                                    self.gAttr.ASize = 1
                                else:
                                    self._MakeScSize(self.gAttr, 1)
                    elif lAttr.ASize <= 4:
                        if lAttr.ASize == 1:
                            Op = 32
                        else:
                            Op = 33 + (1 if lAttr.ASize > 2 else 0)
                    else:
                        Op = 36
                        SubOp = lAttr.ASize
                else:
                    self.Error(144)

            lStmt.AssExpr = self.gAttr.TreePtr
            lStmt.AssOp = Op
            lStmt.AssSubOp = SubOp
        else:
            self.Error(40)

        # 1:
        fStmt.StmtNumb = lNumbr
        return fStmt

    def _CompoundStatement(self, FSys: set[Symbol] | frozenset[Symbol]) -> Stmt:
        """Parse a semicolon-separated `BEGIN ... END` statement list into a `BEGINST` node."""
        lNumbr = self.TotalLines
        sub_fsys = FSys | _SET_SEMI_END
        while True:
            LastStmt = self._Statement(sub_fsys)
            fStmt = LastStmt
            if self.Token in StatBegSys:
                self.Error(36)
            if self.Token not in StatBegSys:
                break
        while self.Token == Symbol.SEMISY:
            self.Scan()
            while True:
                lStmt = self._Statement(sub_fsys)
                if LastStmt is None:
                    LastStmt = lStmt
                    fStmt = lStmt
                elif lStmt is not None:
                    LastStmt.NextStmt = lStmt
                    LastStmt = lStmt
                if self.Token in StatBegSys:
                    self.Error(36)
                if self.Token not in StatBegSys:
                    break

        if self.Token == Symbol.ENDSY:
            self.RightCheck()
            self.Scan()
        else:
            self.Error(44)

        beg = Stmt(StmtTypes.BEGINST)
        beg.NextStmt = None
        beg.SubSt = fStmt
        beg.StmtNumb = lNumbr
        return beg

    def _CaseStatement(self, FSys: set[Symbol] | frozenset[Symbol]) -> Stmt:
        """Parse a `CASE expr OF ... [OTHERWISE ...] END` statement with constant and `..` range labels."""
        lNumbr = self.TotalLines
        CaseStmt = Stmt(StmtTypes.CASEST)
        fStmt = CaseStmt
        LastCStmt: Optional[Stmt] = None
        CaseStmt.NextStmt = None
        CaseStmt.CStmtList = None
        CaseStmt.OtherStmt = None
        self.LHSDHandle = 0
        self.ExprDHandle = 0
        self._Expression(FSys | _SET_OF_COMMA_COLON)
        CaseType = self.gAttr.Typtr
        self._MakeScSize(self.gAttr, 2)
        CaseStmt.CaseExpr = self.gAttr.TreePtr

        if CaseType is not None:
            if (
                CaseType.Form > TypeForms.SUBRANGE
                or self.CompTypes(CaseType, self.RealPtr)
            ):
                self.Error(166)
                CaseType = None

        if self.Token == Symbol.OFSY:
            self.Scan()
        else:
            self.Error(42)

        ExitFlag = False
        Low = 0
        Hi = 0
        while True:
            if (
                self.Token != Symbol.SEMISY
                and self.Token != Symbol.ENDSY
                and self.Token != Symbol.OTHERSY
            ):
                Exit2Flag = False
                LastCons: Optional[IntList] = None
                while True:
                    lValu, ConsTyp1 = self.Constant(FSys | _SET_COMMA_COLON)
                    if ConsTyp1 is not None:
                        if self.CompTypes(CaseType, ConsTyp1):
                            Low = i16(lValu.Ivalu)
                        else:
                            self.Error(142)
                            Low = 0
                            ConsTyp1 = None

                    if self.Token == Symbol.COLONSY and self.DotDot:
                        self.Scan()
                        lValu, ConsTyp2 = self.Constant(FSys | _SET_COMMA_COLON)
                        if self.CompTypes(CaseType, ConsTyp2):
                            Hi = i16(lValu.Ivalu)
                            if Low > Hi:
                                self.Error(105)
                                Hi = Low
                                Low = Hi
                        else:
                            self.Error(142)
                            ConsTyp2 = None
                    else:
                        ConsTyp2 = ConsTyp1
                        Hi = Low

                    if ConsTyp1 is not None and ConsTyp2 is not None:
                        dup = False
                        lStmt = CaseStmt.CStmtList
                        while lStmt is not None:
                            ThisCons = lStmt.CaseVals
                            while ThisCons is not None:
                                if ThisCons.IntVal >= Low and ThisCons.IntVal <= Hi:
                                    self.Error(150)
                                    dup = True
                                    break
                                ThisCons = ThisCons.NextInt
                            if dup:
                                break
                            lStmt = lStmt.NextStmt

                        if not dup:
                            for CaseLabel in range(Low, Hi + 1):
                                ThisCons = IntList(CaseLabel, None)
                                if LastCons is None:
                                    ThisCStmt = Stmt(StmtTypes.CSTMTST)
                                    ThisCStmt.StmtNumb = 0
                                    ThisCStmt.NextStmt = None
                                    ThisCStmt.CaseVals = ThisCons
                                    ThisCStmt.ThisCase = None
                                    if LastCStmt is None:
                                        CaseStmt.CStmtList = ThisCStmt
                                    else:
                                        LastCStmt.NextStmt = ThisCStmt
                                    LastCStmt = ThisCStmt
                                else:
                                    LastCons.NextInt = ThisCons
                                LastCons = ThisCons

                    # 1:
                    if self.Token == Symbol.COMMASY:
                        self.Scan()
                    else:
                        Exit2Flag = True
                    if Exit2Flag:
                        break

                if self.Token == Symbol.COLONSY:
                    self.Scan()
                else:
                    self.Error(35)

                while True:
                    lStmt = self._Statement(FSys | _SET_SEMI)
                    if LastCStmt is not None:
                        LastCStmt.ThisCase = lStmt
                    if self.Token in StatBegSys:
                        self.Error(36)
                    if self.Token not in StatBegSys:
                        break

            if self.Token == Symbol.SEMISY:
                self.Scan()
            else:
                ExitFlag = True
            if ExitFlag:
                break

        if self.Token == Symbol.OTHERSY:
            self.Scan()
            lStmt = self._Statement(FSys | _SET_SEMI_END)
            CaseStmt.OtherStmt = lStmt
            if self.Token == Symbol.SEMISY:
                self.Scan()

        if self.Token == Symbol.ENDSY:
            self.RightCheck()
            self.Scan()
        else:
            self.Error(44)

        fStmt.StmtNumb = lNumbr
        return fStmt

    def _ForStatement(self, FSys: set[Symbol] | frozenset[Symbol]) -> Stmt:
        """Parse a `FOR v := init TO|DOWNTO limit DO stmt` loop over a local direct ordinal variable."""
        lNumbr = self.TotalLines
        fort: Optional[T] = None
        fStmt = Stmt(StmtTypes.FORTOST)
        fStmt.NextStmt = None
        fStmt.ForVar = None
        fStmt.ForInit = None
        fStmt.ForLimit = None
        lForSize = 2

        if self.Token == Symbol.IDENTSY:
            forn = self.SearchAll(_SEARCH_VARS)
            fStmt.ForVar = forn
            fort = forn.IdType
            lForSize = self.FullBytes(fort)
            if fort is not None:
                if fort.Form > TypeForms.SUBRANGE or self.CompTypes(fort, self.RealPtr):
                    self.Error(139)
                    fort = None
                elif forn.Vlev != self.Level or forn.Vkind != AccessKind.DRCT:
                    self.Error(172)
            self.Scan()
        else:
            self.Skip(29, FSys | _SET_FOR_SYNC1)

        if self.Token == Symbol.ASSIGNSY:
            self.Scan()
            self.LHSDHandle = 0
            self.ExprDHandle = 0
            self._Expression(FSys | _SET_FOR_SYNC2)
            self._MakeScSize(self.gAttr, lForSize)
            fStmt.ForInit = self.gAttr.TreePtr
            if self.gAttr.Typtr is not None:
                if not self.CompTypes(fort, self.gAttr.Typtr):
                    self.Error(140)
        else:
            self.Skip(40, FSys | _SET_FOR_SYNC2)

        if self.Token == Symbol.TOSY or self.Token == Symbol.DOWNTOSY:
            if self.Token == Symbol.DOWNTOSY:
                fStmt.StmtOp = StmtTypes.FORDOWNST
            self.Scan()
            self.LHSDHandle = 0
            self.ExprDHandle = 0
            self._Expression(FSys | _SET_DO)
            self._MakeScSize(self.gAttr, lForSize)
            fStmt.ForLimit = self.gAttr.TreePtr
            if self.gAttr.Typtr is not None:
                if not self.CompTypes(fort, self.gAttr.Typtr):
                    self.Error(140)
        else:
            self.Skip(48, FSys | _SET_DO)

        if self.Token == Symbol.DOSY:
            self.Scan()
        else:
            self.Error(47)

        fStmt.ForSt = self._Statement(FSys)
        fStmt.ForSize = lForSize
        fStmt.StmtNumb = lNumbr
        return fStmt

    def _GotoStatement(self) -> Stmt:
        """Parse a `GOTO label` statement, resolving the integer label across enclosing block scopes."""
        lNumbr = self.TotalLines
        lStmt = Stmt(StmtTypes.GOTOST)
        fStmt = lStmt
        lStmt.NextStmt = None
        lStmt.LabLev = self.Level
        lStmt.GotoLab = None

        if self.Token == Symbol.ICONSTSY:
            Lab: Optional[LabRec] = None
            lLevel = self.Level
            found = False
            for lev in range(self.Level, 0, -1):
                lLevel = lev
                Lab = self.Display[lev].Labels
                while Lab is not None:
                    if Lab.LabelNo == self.IntVal:
                        found = True
                        break
                    Lab = Lab.NextLabel
                if found:
                    break
            if not found:
                self.Error(158)
            # 1:
            self.Scan()
            lStmt.LabLev = lLevel
            lStmt.GotoLab = Lab
        else:
            self.Error(30)

        fStmt.StmtNumb = lNumbr
        return fStmt

    def _IfStatement(self, FSys: set[Symbol] | frozenset[Symbol]) -> Stmt:
        """Parse `IF cond THEN stmt [ELSE stmt]`, folding constant boolean conditions to the taken branch."""
        lNumbr = self.TotalLines
        self.LHSDHandle = 0
        self.ExprDHandle = 0
        self._Expression(FSys | _SET_THEN)
        IfStExpr = self.gAttr.TreePtr
        if not self.CompTypes(self.gAttr.Typtr, self.BoolPtr):
            self.Error(132)

        if self.Token == Symbol.THENSY:
            self.Scan()
        else:
            self.Error(45)

        ThenStmt = self._Statement(FSys | _SET_ELSE)

        if self.Token == Symbol.ELSESY:
            self.Scan()
            ElseStmt = self._Statement(FSys)
        else:
            ElseStmt = None

        if IfStExpr is None or IfStExpr.Node != NodeKind.CSTNODE:
            fStmt = Stmt(StmtTypes.IFST)
            fStmt.StmtNumb = lNumbr
            fStmt.NextStmt = None
            fStmt.IfExpr = IfStExpr
            fStmt.ThenSt = ThenStmt
            fStmt.ElseSt = ElseStmt
        elif IfStExpr.CstValu.Ivalu == 0:
            fStmt = Stmt(StmtTypes.BEGINST)
            fStmt.StmtNumb = lNumbr
            fStmt.NextStmt = None
            fStmt.SubSt = ElseStmt
        else:
            fStmt = Stmt(StmtTypes.BEGINST)
            fStmt.StmtNumb = lNumbr
            fStmt.NextStmt = None
            fStmt.SubSt = ThenStmt
        return fStmt

    def _RepeatStatement(self, FSys: set[Symbol] | frozenset[Symbol]) -> Stmt:
        """Parse a `REPEAT ... UNTIL cond` statement sequence and boolean exit condition into `REPST`."""
        lNumbr = self.TotalLines
        fStmt = Stmt(StmtTypes.REPST)
        fStmt.NextStmt = None
        fStmt.CondExpr = None

        sub_fsys = FSys | _SET_UNTIL_SEMI
        while True:
            lStmt = self._Statement(sub_fsys)
            fStmt.LoopStmt = lStmt
            LastStmt = lStmt
            if self.Token in StatBegSys:
                self.Error(36)
            if self.Token not in StatBegSys:
                break
        while self.Token == Symbol.SEMISY:
            self.Scan()
            while True:
                lStmt = self._Statement(sub_fsys)
                if LastStmt is None:
                    LastStmt = lStmt
                    fStmt.LoopStmt = lStmt
                elif lStmt is not None:
                    LastStmt.NextStmt = lStmt
                    LastStmt = lStmt
                if self.Token in StatBegSys:
                    self.Error(36)
                if self.Token not in StatBegSys:
                    break

        if self.Token == Symbol.UNTILSY:
            self.RightCheck()
            self.Scan()
            self.LHSDHandle = 0
            self.ExprDHandle = 0
            self._Expression(FSys)
            fStmt.CondExpr = self.gAttr.TreePtr
            if not self.CompTypes(self.gAttr.Typtr, self.BoolPtr):
                self.Error(132)
        else:
            self.Error(46)

        fStmt.StmtNumb = lNumbr
        return fStmt

    def _WhileStatement(self, FSys: set[Symbol] | frozenset[Symbol]) -> Stmt:
        """Parse a `WHILE cond DO stmt` loop into a `WHILEST` statement node."""
        lNumbr = self.TotalLines
        fStmt = Stmt(StmtTypes.WHILEST)
        fStmt.NextStmt = None
        self.LHSDHandle = 0
        self.ExprDHandle = 0
        self._Expression(FSys | _SET_DO)
        fStmt.CondExpr = self.gAttr.TreePtr
        if not self.CompTypes(self.gAttr.Typtr, self.BoolPtr):
            self.Error(132)

        if self.Token == Symbol.DOSY:
            self.Scan()
        else:
            self.Error(47)

        fStmt.LoopStmt = self._Statement(FSys)
        fStmt.StmtNumb = lNumbr
        return fStmt

    def _WithStatement(self, FSys: set[Symbol] | frozenset[Symbol]) -> Stmt:
        """Parse a `WITH v1, v2, ... DO stmt` construct over record variables and Clascal object handles.

        Pushes `REC` or `KLASS` entries onto `Display`, double-dereferences object handles into
        nested `WITHST` nodes as required, and tracks `$H+` handle-locking depth across `stmt`.
        """
        SaveWDHandle = self.WithDHandle
        lNumbr = self.TotalLines
        fStmt: Optional[Stmt] = None
        LastStmt: Optional[Stmt] = None
        ExitFlag = False
        OldTop = self.Top

        while True:
            PckdFlag = False
            if self.Token == Symbol.IDENTSY:
                lpN = self.SearchAll(_SEARCH_VAR_FLD_FUNC_TYP)
                self.Scan()
            else:
                self.Error(29)
                lpN = self.uVarPtr
            self.LHSDHandle = 0
            self.ExprDHandle = 0
            self.gAttr.Typtr = lpN.IdType
            self.gAttr.TreePtr = lpN
            self.gAttr.ASize = self.FullBytes(self.gAttr.Typtr)
            PckdFlag, _PckdStorage = self._Selector(FSys | _SET_COMMA_DO, lpN)
            lStmt = Stmt(StmtTypes.WITHST)
            lStmt.NextStmt = None
            lStmt.StmtNumb = lNumbr
            lStmt.WithVar = self.gAttr.TreePtr
            lStmt.WithBody = None
            if LastStmt is None:
                fStmt = lStmt
            else:
                LastStmt.WithBody = lStmt
            LastStmt = lStmt

            if self.gAttr.Typtr is not None:
                ty = self.gAttr.Typtr
                if ty.Form == TypeForms.RECORDS:
                    if self.Top < MAXDISPLAY:
                        self.Top = self.Top + 1
                        disp = self.Display[self.Top]
                        disp.NameTree = ty.Fields
                        disp.Occur = Where.REC
                        disp.RecPckd = ty.PckdRec
                    else:
                        self.Error(300)
                elif ty.Form == TypeForms.CLASSES:
                    self.ExprDHandle = 1
                    if (self.Top + 1) < MAXDISPLAY:
                        self.Top = self.Top + 1
                        disp = self.Display[self.Top]
                        disp.NameTree = ty.ClFields
                        disp.Occur = Where.KLASS
                        disp.KType = self.gAttr.Typtr
                        disp.WVar = None
                        Kluge = False
                        if lStmt.WithVar is not None:
                            wv = lStmt.WithVar
                            if wv.Node == NodeKind.IDENTNODE:
                                if wv.Class == NameClass.VARS:
                                    if wv.Vlev == self.Level and wv.Vlev > 1:
                                        disp.WVar = lStmt.WithVar
                            elif wv.Node == NodeKind.BINNODE:
                                Kluge = wv.BinOp == 176  # FUNC - type cast
                        if self.Display[self.Top].WVar is None and not Kluge:
                            # need another with
                            self.Top = self.Top + 1
                            disp2 = self.Display[self.Top]
                            disp2.NameTree = ty.ClFields
                            disp2.Occur = Where.KLASS
                            disp2.KType = self.gAttr.Typtr
                            disp2.WVar = None
                            lStmt = Stmt(StmtTypes.WITHST)
                            lStmt.NextStmt = None
                            lStmt.StmtNumb = lNumbr
                            lpN2 = self._NewUnNode(43, None)  # WITHREC
                            if self.Level <= 1:
                                lpN2.UnSubOp = self.Top - 2
                            else:
                                lpN2.UnSubOp = self.Top - 1 - self.Level
                            lStmt.WithVar = self._NewUnNode(
                                12, self._NewUnNode(12, lpN2)  # POINTERS
                            )
                            lStmt.WithBody = None
                            LastStmt.WithBody = lStmt
                            LastStmt = lStmt
                        else:
                            # the class var is a local or funct, so just with var^^
                            lStmt.WithVar = self._NewUnNode(
                                12, self._NewUnNode(12, lStmt.WithVar)  # POINTERS
                            )
                    else:
                        self.Error(300)
                else:
                    self.Error(137)

            if self.Token == Symbol.COMMASY:
                self.Scan()
            else:
                ExitFlag = True
            self.WithDHandle = self.WithDHandle + self.ExprDHandle
            if ExitFlag:
                break

        if self.Token == Symbol.DOSY:
            self.Scan()
        else:
            self.Error(47)

        LastStmt.WithBody = self._Statement(FSys)
        self.Top = OldTop
        self.WithDHandle = SaveWDHandle
        return fStmt

    def _Statement(self, FSys: set[Symbol] | frozenset[Symbol]) -> Optional[Stmt]:
        """Parse an optional statement label (`N:`) followed by a simple or structured Pascal statement."""
        fStmt: Optional[Stmt] = None
        lStmt: Optional[Stmt] = None

        if self.Token == Symbol.ICONSTSY:
            if self.IntVal <= 9999:
                Lab = self.Display[self.Level].Labels
                found = False
                while Lab is not None:
                    if Lab.LabelNo == self.IntVal:
                        if Lab.Defined:
                            self.Error(155)
                        else:
                            Lab.Defined = True
                        found = True
                        break
                    Lab = Lab.NextLabel
                if not found:
                    self.Error(158)
                # 1:
                fStmt = Stmt(StmtTypes.LABEDST)
                fStmt.StmtNumb = self.TotalLines
                fStmt.NextStmt = None
                fStmt.StLab = Lab
                fStmt.LabStmt = None
            else:
                self.Error(173)
            self.Scan()
            if self.Token == Symbol.COLONSY:
                self.Scan()
            else:
                self.Error(35)

        if self.Token not in (FSys | _SET_IDENT):
            self.Skip(20, FSys)
        if self.Token in (StatBegSys | _SET_IDENT):
            tok = self.Token
            if tok == Symbol.IDENTSY:
                self.LHSDHandle = 0
                self.ExprDHandle = 0
                lpN = self.SearchAll(_SEARCH_VAR_FLD_PROC_FUNC_TYP)
                self.Scan()
                if lpN.Class in (
                    NameClass.TYPES,
                    NameClass.VARS,
                    NameClass.FIELD,
                    NameClass.FUNC,
                ):
                    lStmt = self._Assignment(FSys, lpN)
                elif lpN.Class == NameClass.PROC:
                    if self.Display[self.Disx].Occur == Where.KLASS:
                        lStmt = self._Assignment(FSys, lpN)
                    else:
                        self._Call(FSys, lpN)
                        lStmt = Stmt(StmtTypes.CALLST)
                        lStmt.StmtNumb = self.TotalLines
                        lStmt.NextStmt = None
                        lStmt.ProcpN = lpN
                        lStmt.pArgList = self.gAttr.TreePtr

            elif tok == Symbol.BEGINSY:
                self.LeftCheck()
                self.Scan()
                lStmt = self._CompoundStatement(FSys)

            elif tok == Symbol.CASESY:
                self.LeftCheck()
                self.Scan()
                lStmt = self._CaseStatement(FSys)

            elif tok == Symbol.FORSY:
                self.Scan()
                lStmt = self._ForStatement(FSys)

            elif tok == Symbol.GOTOSY:
                self.Scan()
                lStmt = self._GotoStatement()

            elif tok == Symbol.IFSY:
                self.Scan()
                lStmt = self._IfStatement(FSys)

            elif tok == Symbol.REPEATSY:
                self.LeftCheck()
                self.Scan()
                lStmt = self._RepeatStatement(FSys)

            elif tok == Symbol.WHILESY:
                self.Scan()
                lStmt = self._WhileStatement(FSys)

            elif tok == Symbol.WITHSY:
                self.Scan()
                lStmt = self._WithStatement(FSys)

            if self.Token not in FSys:
                self.Skip(20, FSys)

        if fStmt is None:
            fStmt = lStmt
        else:
            fStmt.LabStmt = lStmt
        return fStmt

    # ---- Top-level Body ----

    def Body(self, FSys: set[Symbol] | frozenset[Symbol], PFName: str) -> Optional[Stmt]:
        """Parse the statement body of a program, procedure, function, or method up to `END`.

        Appends the hidden `ExitLabel` statement targeted by `EXIT(...)` and verifies that all
        declared labels in the current block have been defined.
        """
        if (not self.ConsListing) or (not self.Listing):
            sys.stdout.write(self.ShowProcName(self.CurrClass, PFName, self.Level) + '\n')

        self.WithDHandle = 0
        sub_fsys = FSys | _SET_SEMI_END
        while True:
            LastStmt = self._Statement(sub_fsys)
            BodyStmt = LastStmt
            if self.Token in StatBegSys:
                self.Error(36)
            if self.Token not in StatBegSys:
                break
        while self.Token == Symbol.SEMISY:
            self.Scan()
            while True:
                lStmt = self._Statement(sub_fsys)
                if LastStmt is None:
                    LastStmt = lStmt
                    BodyStmt = lStmt
                elif lStmt is not None:
                    LastStmt.NextStmt = lStmt
                    LastStmt = lStmt
                if self.Token in StatBegSys:
                    self.Error(36)
                if self.Token not in StatBegSys:
                    break

        if self.Token == Symbol.ENDSY:
            self.RightCheck()
            if self.Level > 1:
                self.ProcLev = chr(ord('A') + self.Level - 2)
            self.Scan()
        else:
            self.Error(44)

        # Define the hidden EXIT label
        exit_stmt = Stmt(StmtTypes.LABEDST)
        exit_stmt.StmtNumb = self.TotalLines
        exit_stmt.NextStmt = None
        exit_stmt.StLab = self.Display[self.Level].ExitLabel
        exit_stmt.LabStmt = None

        if BodyStmt is None:
            BodyStmt = exit_stmt
        else:
            LastStmt.NextStmt = exit_stmt

        Lab = self.Display[self.Level].Labels
        while Lab is not None:
            if not Lab.Defined:
                LabStr = str(Lab.LabelNo)
                LabName = alfa8(LabStr)
                self.NError(157, LabName)
            Lab = Lab.NextLabel

        return BodyStmt
