"""Declaration parser mixin for the Lisa Pascal Front End."""

from __future__ import annotations

from typing import Optional

from frontend_base import (
    MAXDISPLAY,
    MAXLEVEL,
    MAXUNITS,
    AccessKind,
    DeclKind,
    InputFileTypes,
    IntList,
    LabRec,
    N,
    NameClass,
    NodeKind,
    PFkind,
    SimpTypeBegSys,
    Symbol,
    T,
    TypeBegSys,
    TypeDels,
    TypeForms,
    UnitKind,
    Where,
)
from lisalib import i16, i32, odd, pdiv, pmod, ppos, pset_ch


class DeclMixin:
    """Declaration parser and symbol-table builder: USES unit/library interface
    loading, LABEL/CONST/TYPE/VAR declarations, packed/unpacked records and
    arrays, Clascal SUBCLASS hierarchies and method tables, and PROCEDURE/
    FUNCTION/INLINE/EXTERNAL/FORWARD/C headers."""

    def Declarations(
        self,
        FSys: set[Symbol] | frozenset[Symbol],
        fSymbol: Symbol,
        FpN: Optional[N],
        HeapMark: int,
        ClasspT: Optional[T],
    ) -> tuple[Optional[N], int]:
        """Parse a declaration block and populate lexical Display scopes for a
        PROGRAM, Clascal creation block (%_CRxxxx), PROCEDURE/FUNCTION/method
        body, UNIT INTERFACE/IMPLEMENTATION, USES interface, or local block."""

        def InsertMethod(lFpN: N, n_key: int, cls_pT: T) -> None:
            """Insert method lFpN into cls_pT.ClFstMethod ordered by MethodLevel*256+MethodNo."""
            cur = cls_pT.ClFstMethod
            prev: Optional[N] = None

            while cur is not None:
                if n_key <= (cur.MethodLevel * 256 + cur.MethodNo):
                    cur = None
                else:
                    prev = cur
                    cur = cur.Next

            if prev is None:
                lFpN.Next = cls_pT.ClFstMethod
                cls_pT.ClFstMethod = lFpN
            else:
                lFpN.Next = prev.Next
                prev.Next = lFpN

        def Typ(
            t_fsys: set[Symbol] | frozenset[Symbol],
            ClassAllowed: bool,
            ThisClass: Optional[N],
        ) -> Optional[T]:
            """Parse a Lisa Pascal or Clascal type specification—simple types,
            pointers, packed/unpacked arrays, files, records, sets, strings, or
            interface SUBCLASS definitions—and compute its storage size."""
            FileFlag: bool = False

            def NrOfBits(fVal: int) -> int:
                """Return the bit width needed to represent unsigned values in 0..fVal."""
                Count = 0
                while True:
                    fVal = pdiv(fVal, 2)
                    Count += 1
                    if fVal == 0:
                        break
                return Count

            def CalcSize(fT: Optional[T]) -> None:
                """Compute Bytes, Bits, packing metadata, and Clascal SizeInstance
                for type descriptor fT, word-aligning sizes larger than 1 byte."""
                DisplBytes: int = 0
                DisplBits: int = 0
                LPckdRec: bool = False
                lNumEls: int = 0

                def TotalBits(FpT_arg: Optional[T]) -> int:
                    """Return the packed bit width (Bytes * 8 + Bits) of FpT_arg, or 32 if None."""
                    if FpT_arg is not None:
                        return (FpT_arg.Bytes * 8) + FpT_arg.Bits
                    return 32

                def LByteCalc(n_div: int) -> None:
                    """Set fT.Bytes for large bit-packed arrays (>= 32768 elements) with n_div elements per byte, or -1 on >32 KB overflow."""
                    assert fT is not None
                    if n_div > 1:
                        lb = pdiv(lNumEls - 1, n_div) + 1
                    else:
                        lb = lNumEls
                    if lb > 32768:
                        fT.Bytes = -1
                    else:
                        fT.Bytes = i16(lb)

                def RecEvenLength() -> bool:
                    """Return True if the accumulated record size exceeds 1 byte and thus word-aligns to an even byte length."""
                    return ((DisplBits != 0) and (DisplBytes != 0)) or (DisplBytes > 1)

                def CalcFieldAddrs(FfldList: Optional[N], NoVariant: bool) -> None:
                    """Assign byte offsets (FOff), bit offsets (BitOff), and PckdField flags
                    for a record or class field list, unpacking isolated byte/word fields and
                    right-justifying remaining packed fields."""
                    nonlocal DisplBytes, DisplBits

                    def PackTightly() -> None:
                        """Initial pass assigning sequential byte/bit displacements for packed (1-16 bit) or word-aligned unpacked fields."""
                        nonlocal DisplBytes, DisplBits
                        lFldList = FfldList
                        while lFldList is not None:
                            FieldFullBytes = self.FullBytes(lFldList.IdType)
                            if (
                                (FieldFullBytes < 1000)
                                and (lFldList.IdType is not None)
                                and (lFldList.IdType.Form <= TypeForms.SUBRANGE)
                            ):
                                lTotalBits = TotalBits(lFldList.IdType)
                            else:
                                lTotalBits = 32
                            if LPckdRec:
                                lFldList.FOff = DisplBytes
                                lFldList.BitOff = DisplBits
                                if (lTotalBits + DisplBits) < 8:
                                    if odd(DisplBytes):
                                        lFldList.FOff = lFldList.FOff - 1
                                        lFldList.BitOff = lFldList.BitOff + 8
                                    lFldList.PckdField = True
                                    DisplBits = DisplBits + lTotalBits
                                elif (lTotalBits + DisplBits) == 8:
                                    lFldList.PckdField = (lTotalBits != 8) or (FieldFullBytes > 1)
                                    if odd(DisplBytes) and lFldList.PckdField:
                                        lFldList.FOff = lFldList.FOff - 1
                                        lFldList.BitOff = lFldList.BitOff + 8
                                    DisplBits = 0
                                    DisplBytes = i16(DisplBytes + 1)
                                elif ((lTotalBits + DisplBits) < 16) and (not odd(DisplBytes)):
                                    lFldList.PckdField = True
                                    DisplBytes = i16(DisplBytes + 1)
                                    DisplBits = DisplBits + lTotalBits - 8
                                elif ((lTotalBits + DisplBits) == 16) and (not odd(DisplBytes)):
                                    lFldList.PckdField = lTotalBits != 16
                                    DisplBits = 0
                                    DisplBytes = i16(DisplBytes + 2)
                                else:
                                    if odd(DisplBytes):
                                        DisplBytes = i16(DisplBytes + 1)
                                        DisplBits = 0
                                    if DisplBits != 0:
                                        DisplBits = 0
                                        DisplBytes = i16(DisplBytes + 2)
                                    lFldList.FOff = DisplBytes
                                    lFldList.BitOff = DisplBits
                                    if lTotalBits < 16:
                                        lFldList.PckdField = (lTotalBits != 8) or (
                                            FieldFullBytes > 1
                                        )
                                        DisplBits = pmod(lTotalBits, 8)
                                        DisplBytes = i16(DisplBytes + pdiv(lTotalBits, 8))
                                    else:
                                        lFldList.PckdField = False
                                        DisplBytes = i16(DisplBytes + FieldFullBytes)
                            else:
                                if odd(DisplBytes) and (FieldFullBytes > 1):
                                    DisplBytes = i16(DisplBytes + 1)
                                lFldList.FOff = DisplBytes
                                lFldList.PckdField = False
                                lFldList.BitOff = 0
                                DisplBytes = i16(DisplBytes + FieldFullBytes)
                            if DisplBytes < 0:
                                self.Error(309)
                                DisplBytes = 2
                            lFldList = lFldList.Next

                    PackTightly()

                    if LPckdRec:
                        lFldList = FfldList
                        Prevfield: Optional[N] = None
                        while lFldList is not None:
                            if Prevfield is not None:
                                if (
                                    Prevfield.PckdField
                                    and ((Prevfield.FOff + 2) == lFldList.FOff)
                                    and (Prevfield.BitOff != 0)
                                ):
                                    if (Prevfield.BitOff <= 8) and (
                                        TotalBits(Prevfield.IdType) <= 8
                                    ):
                                        Prevfield.BitOff = 8
                            Prevfield = lFldList
                            lFldList = lFldList.Next
                        if NoVariant and RecEvenLength():
                            if Prevfield is not None:
                                if (
                                    Prevfield.PckdField
                                    and (Prevfield.BitOff != 0)
                                    and (Prevfield.BitOff <= 8)
                                    and (TotalBits(Prevfield.IdType) <= 8)
                                ):
                                    Prevfield.BitOff = 8

                        # Look for fields which are "packed" but alone in bytes
                        Prevfield = None
                        lFldList = FfldList
                        while lFldList is not None:
                            if Prevfield is not None:
                                if (
                                    Prevfield.PckdField
                                    and (Prevfield.BitOff == 0)
                                    and ((Prevfield.FOff != lFldList.FOff) or (lFldList.BitOff == 8))
                                ):
                                    Prevfield.PckdField = self.FullBytes(Prevfield.IdType) > 1
                                if (
                                    Prevfield.PckdField
                                    and (Prevfield.BitOff == 0)
                                    and ((Prevfield.FOff + 2) == lFldList.FOff)
                                ):
                                    Prevfield.PckdField = False
                                if (
                                    Prevfield.PckdField
                                    and (Prevfield.BitOff == 8)
                                    and (Prevfield.FOff != lFldList.FOff)
                                ):
                                    Prevfield.PckdField = self.FullBytes(Prevfield.IdType) > 1
                                    if not Prevfield.PckdField:
                                        Prevfield.FOff = Prevfield.FOff + 1
                                        Prevfield.BitOff = 0

                                # Attempt to right justify any fields still packed
                                if (
                                    Prevfield.PckdField
                                    and ((Prevfield.FOff + 2) == lFldList.FOff)
                                    and (Prevfield.BitOff != 0)
                                ):
                                    Prevfield.BitOff = 16 - TotalBits(Prevfield.IdType)
                                if (
                                    Prevfield.PckdField
                                    and ((Prevfield.FOff + 1) == lFldList.FOff)
                                    and (Prevfield.BitOff != 0)
                                ):
                                    Prevfield.BitOff = 8 - TotalBits(Prevfield.IdType)
                                if (
                                    Prevfield.PckdField
                                    and (Prevfield.FOff == lFldList.FOff)
                                    and (lFldList.BitOff == 8)
                                    and (Prevfield.BitOff != 0)
                                ):
                                    Prevfield.BitOff = 8 - TotalBits(Prevfield.IdType)

                            Prevfield = lFldList
                            lFldList = lFldList.Next

                        if (Prevfield is not None) and NoVariant:
                            if Prevfield.PckdField:
                                if (Prevfield.BitOff == 0) and (
                                    RecEvenLength() or (DisplBits != 0)
                                ):
                                    Prevfield.PckdField = False
                                if Prevfield.BitOff == 8:
                                    Prevfield.PckdField = (TotalBits(Prevfield.IdType) == 8) and (
                                        self.FullBytes(Prevfield.IdType) == 2
                                    )
                                    if not Prevfield.PckdField:
                                        Prevfield.FOff = Prevfield.FOff + 1
                                        Prevfield.BitOff = 0

                                # Attempt to right justify final field if still packed
                                if RecEvenLength():
                                    if Prevfield.PckdField and (Prevfield.BitOff != 0):
                                        Prevfield.BitOff = 16 - TotalBits(Prevfield.IdType)
                                elif Prevfield.PckdField and (Prevfield.BitOff != 0):
                                    Prevfield.BitOff = 8 - TotalBits(Prevfield.IdType)

                def CalcVarPart(fTagField: Optional[T]) -> None:
                    """Recursively lay out all CASE record variants under fTagField and advance DisplBytes/DisplBits to the largest variant."""
                    nonlocal DisplBytes, DisplBits
                    if fTagField is not None:
                        InitBytes = DisplBytes
                        InitBits = DisplBits
                        MaxBytes = DisplBytes
                        MaxBits = DisplBits
                        lT = fTagField.Variants
                        while lT is not None:
                            DisplBytes = InitBytes
                            DisplBits = InitBits
                            CalcFieldAddrs(lT.VarFldLst, lT.SubVar is None)
                            CalcVarPart(lT.SubVar)
                            lT.Bytes = i16(DisplBytes + (1 if DisplBits != 0 else 0))
                            if odd(lT.Bytes):
                                lT.Bytes = i16(lT.Bytes + 1)
                            if lT.Bytes < 2:
                                lT.Bytes = 2
                            lT.Bits = 0
                            if (DisplBytes > MaxBytes) or (
                                (DisplBytes == MaxBytes) and (DisplBits > MaxBits)
                            ):
                                MaxBytes = DisplBytes
                                MaxBits = DisplBits
                            lT = lT.NextVar
                        DisplBytes = MaxBytes
                        DisplBits = MaxBits

                if fT is not None:
                    fT.Bytes = 0
                    fT.Bits = 0
                    form = fT.Form
                    if form == TypeForms.SCALAR:
                        if fT.MaxConst is not None:
                            ival = fT.MaxConst.ValueOf.Ivalu
                            if ival <= 127:
                                fT.Bits = NrOfBits(ival)
                            else:
                                fT.Bytes = 1
                                fT.Bits = NrOfBits(ival) - 8
                    elif form == TypeForms.SUBRANGE:
                        if fT.Min >= 0:
                            if fT.Max <= 127:
                                fT.Bits = NrOfBits(fT.Max)
                            elif fT.Max <= 32767:
                                fT.Bytes = 1
                                fT.Bits = NrOfBits(fT.Max) - 8
                            else:
                                fT.Bytes = 4
                        else:
                            if (-(fT.Min + 1)) > fT.Max:
                                BitCnt = NrOfBits(-(fT.Min + 1)) + 1
                            else:
                                BitCnt = NrOfBits(fT.Max) + 1
                            if BitCnt < 8:
                                fT.Bits = BitCnt
                            elif BitCnt < 16:
                                fT.Bits = BitCnt - 8
                                fT.Bytes = 1
                            else:
                                fT.Bytes = pdiv(BitCnt - 1, 8) + 1
                    elif form == TypeForms.RECORDS:
                        LPckdRec = fT.PckdRec
                        DisplBytes = 0
                        DisplBits = 0
                        if self.Errors == 0:
                            CalcFieldAddrs(fT.FstField, fT.VarPart is None)
                            CalcVarPart(fT.VarPart)
                        fT.Bytes = i16(DisplBytes + (1 if DisplBits != 0 else 0))
                        if fT.Bytes <= 1:
                            fT.Bytes = 2
                        if fT.Bytes < 0:
                            self.Error(309)
                    elif form == TypeForms.CLASSES:
                        fT.Bytes = 4
                        fT.Bits = 0
                        DisplBytes = 4
                        DisplBits = 0
                        if self.Errors == 0:
                            assert fT.SuperClass is not None
                            DisplBytes = fT.SuperClass.SizeInstance
                            DisplBits = 0
                            cls_fld = fT.ClFstField
                            while cls_fld is not None:
                                if cls_fld.FOff < 0:
                                    LPckdRec = False
                                    CalcFieldAddrs(cls_fld, True)
                                    break  # GOTO 10
                                cls_fld = cls_fld.Next
                        # 10:
                        fT.SizeInstance = i16(DisplBytes + (1 if DisplBits != 0 else 0))
                        if odd(fT.SizeInstance):
                            fT.SizeInstance = i16(fT.SizeInstance + 1)
                        if fT.SizeInstance < 0:
                            self.Error(309)
                    elif form in (TypeForms.VARIANT, TypeForms.TAGFIELD, TypeForms.SCONST):
                        self.Error(3001)
                    elif form == TypeForms.POINTERS:
                        fT.Bytes = 4
                    elif form == TypeForms.SETS:
                        lMin, lMax = self.GetBounds(fT.SetOf)
                        fT.Bits = 0
                        fT.Bytes = pdiv(lMax, 8) + 1
                    elif form == TypeForms.ARRAYS:
                        if (fT.ArrayOf is not None) and (fT.IndexedBy is not None):
                            lMin, lMax = self.GetBounds(fT.IndexedBy)
                            fT.Bits = 0
                            lNumEls = i32(lMax - lMin + 1)
                            NumEls = i16(lNumEls)
                            fT.Bytes = self.FullBytes(fT.ArrayOf)
                            if (fT.Bytes > 128) or (lNumEls > 128):
                                lBytes = i32(fT.Bytes * lNumEls)
                                # We allow 32768 bytes (Bytes := -32768) as a kludge
                                if lBytes > 32768:
                                    fT.Bytes = -1
                                else:
                                    fT.Bytes = i16(lBytes)
                            else:
                                fT.Bytes = i16(fT.Bytes * NumEls)
                                if fT.Bytes < 0:
                                    fT.Bytes = -1
                            if fT.PckdArr:
                                if (fT.ArrayOf.Bits == 0) and (
                                    fT.ArrayOf.Bytes != self.FullBytes(fT.ArrayOf)
                                ):
                                    if lNumEls >= 32768:
                                        LByteCalc(1)
                                    else:
                                        fT.Bytes = NumEls
                                    fT.BitPackd = True
                                    fT.BitsPerEl = 8
                                elif fT.ArrayOf.Bytes == 0:
                                    if fT.ArrayOf.Bits == 1:
                                        if lNumEls >= 32768:
                                            LByteCalc(8)
                                        else:
                                            fT.Bytes = pdiv(NumEls - 1, 8) + 1
                                        fT.BitPackd = True
                                        fT.BitsPerEl = 1
                                    elif fT.ArrayOf.Bits == 2:
                                        if lNumEls >= 32768:
                                            LByteCalc(4)
                                        else:
                                            fT.Bytes = pdiv(NumEls - 1, 4) + 1
                                        fT.BitPackd = True
                                        fT.BitsPerEl = 2
                                    elif (fT.ArrayOf.Bits == 3) or (fT.ArrayOf.Bits == 4):
                                        if lNumEls >= 32768:
                                            LByteCalc(2)
                                        else:
                                            fT.Bytes = pdiv(NumEls - 1, 2) + 1
                                        fT.BitPackd = True
                                        fT.BitsPerEl = 4
                            if fT.Bytes == -1:
                                self.Error(309)
                                fT.Bytes = 1
                    elif form == TypeForms.FILES:
                        if fT.FileOf is not None:
                            fT.Bytes = i16(600 + self.FullBytes(fT.FileOf))
                            if fT.Bytes < 0:
                                self.Error(309)
                        else:
                            fT.Bytes = 80
                    elif form == TypeForms.STRINGS:
                        fT.Bytes = fT.StringLen + 1

                    if (fT.Bytes != 1) and odd(fT.Bytes):
                        fT.Bytes = i16(fT.Bytes + 1)

            def SimpleType(st_fsys: set[Symbol] | frozenset[Symbol]) -> Optional[T]:
                """Parse an enumerated scalar type, constant subrange low..high, or named
                type identifier (recording undeclared names as forward CLASSES on ForwCList)."""
                res_pT: Optional[T] = None
                if self.Token not in SimpTypeBegSys:
                    self.Skip(21, st_fsys | SimpTypeBegSys)
                if self.Token in SimpTypeBegSys:
                    if self.Token == Symbol.LPARENSY:
                        s_lpN: Optional[N] = None
                        ord_val = 0
                        res_pT = T(TypeForms.SCALAR)
                        res_pT.FType = False
                        res_pT.Form = TypeForms.SCALAR
                        res_pT.ScalKind = DeclKind.DECLARED
                        OldTop = self.Top
                        while self.Display[self.Top].Occur == Where.REC:
                            self.Top -= 1
                        while True:
                            self.Scan()
                            if self.Token == Symbol.IDENTSY:
                                lpN2 = N(NodeKind.IDENTNODE)
                                lpN2.Name = self.Ident
                                lpN2.Next = s_lpN
                                lpN2.IdType = res_pT
                                lpN2.Class = NameClass.CONSTS
                                lpN2.ValueOf.Ivalu = ord_val
                                lpN2.Node = NodeKind.IDENTNODE
                                s_lpN = lpN2
                                self.EnterId(s_lpN)
                                ord_val += 1
                                self.Scan()
                            else:
                                self.Error(29)
                            if self.Token not in (st_fsys | {Symbol.COMMASY, Symbol.RPARENSY}):
                                self.Skip(20, st_fsys | {Symbol.COMMASY, Symbol.RPARENSY})
                            if self.Token != Symbol.COMMASY:
                                break
                        self.Top = OldTop
                        res_pT.MaxConst = s_lpN
                        CalcSize(res_pT)
                        if self.Token == Symbol.RPARENSY:
                            self.Scan()
                        else:
                            self.Error(32)
                    elif self.Token == Symbol.IDENTSY:
                        lName = self.Ident
                        self.Scan()
                        if self.Token == Symbol.COLONSY:
                            s_lpN = self.SearchAll({NameClass.CONSTS})
                            assert s_lpN is not None
                            if s_lpN.IdType is not None:
                                if s_lpN.IdType.Form > TypeForms.SUBRANGE:
                                    self.Error(143)
                                elif self.CompTypes(s_lpN.IdType, self.RealPtr):
                                    self.Error(108)
                            self.Scan()
                            lValu, s_lpT = self.Constant(st_fsys)
                            if s_lpT is not None:
                                if s_lpT.Form > TypeForms.SUBRANGE:
                                    self.Error(143)
                                elif self.CompTypes(s_lpT, self.RealPtr):
                                    self.Error(108)
                            if not self.CompTypes(s_lpT, s_lpN.IdType):
                                self.Error(106)
                            res_pT = T(TypeForms.SUBRANGE)
                            res_pT.FType = False
                            res_pT.Form = TypeForms.SUBRANGE
                            res_pT.RangeOf = s_lpT
                            res_pT.Min = s_lpN.ValueOf.Ivalu
                            res_pT.Max = lValu.Ivalu
                            if res_pT.Min > res_pT.Max:
                                self.Error(105)
                            CalcSize(res_pT)
                        else:
                            self.Ident = lName
                            self.PrintErrors = False
                            s_lpN = self.SearchAll({NameClass.TYPES})
                            self.PrintErrors = True

                            if s_lpN is None:
                                s_lpN = self.ForwCList
                                found_forw = False
                                while s_lpN is not None:
                                    if self.Ident == s_lpN.Name:
                                        res_pT = s_lpN.IdType
                                        found_forw = True
                                        break  # GOTO 10
                                    s_lpN = s_lpN.Next

                                if not found_forw:
                                    res_pT = T(TypeForms.CLASSES)
                                    s_lpN = N(NodeKind.IDENTNODE)

                                    res_pT.Bytes = 4
                                    res_pT.Bits = 0
                                    res_pT.Form = TypeForms.CLASSES
                                    res_pT.FType = False
                                    res_pT.ItsId = None
                                    res_pT.ClFields = None
                                    res_pT.ClFstField = None
                                    res_pT.ClFstMethod = None
                                    res_pT.SuperClass = self.NilClassPtr

                                    s_lpN.Name = self.Ident
                                    s_lpN.Next = self.ForwCList
                                    s_lpN.Class = NameClass.TYPES
                                    s_lpN.Node = NodeKind.IDENTNODE
                                    s_lpN.IdType = res_pT
                                    self.ForwCList = s_lpN
                                # 10:
                            else:
                                if s_lpN.IdType is not None:
                                    res_pT = s_lpN.IdType
                    else:
                        res_pT = T(TypeForms.SUBRANGE)
                        res_pT.FType = False
                        res_pT.Form = TypeForms.SUBRANGE
                        lValu, s_lpT = self.Constant(st_fsys | {Symbol.COLONSY})
                        res_pT.Min = lValu.Ivalu
                        res_pT.RangeOf = s_lpT
                        if s_lpT is not None:
                            if s_lpT.Form > TypeForms.SUBRANGE:
                                self.Error(143)
                            elif self.CompTypes(s_lpT, self.RealPtr):
                                self.Error(108)
                        if self.Token == Symbol.COLONSY:
                            self.Scan()
                        else:
                            self.Error(35)
                        lValu, s_lpT = self.Constant(st_fsys)
                        res_pT.Max = lValu.Ivalu
                        if res_pT.Max < res_pT.Min:
                            self.Error(105)
                        if not self.CompTypes(res_pT.RangeOf, s_lpT):
                            self.Error(106)
                        if s_lpT is not None:
                            if s_lpT.Form > TypeForms.SUBRANGE:
                                self.Error(143)
                            elif self.CompTypes(s_lpT, self.RealPtr):
                                self.Error(108)
                        CalcSize(res_pT)
                    if self.Token not in st_fsys:
                        self.Skip(20, st_fsys)
                return res_pT

            def FieldList(
                fl_fsys: set[Symbol] | frozenset[Symbol],
            ) -> tuple[Optional[N], Optional[T]]:
                """Parse a RECORD fixed field list and optional CASE variant section,
                checking tag types and duplicate variant case labels."""
                nonlocal FileFlag
                fTagFld: Optional[T] = None
                FfldList: Optional[N] = None
                GrouppN: Optional[N] = None
                LastpN: Optional[N] = None
                TagTypePt: Optional[T] = None

                if self.Token not in (fl_fsys | {Symbol.IDENTSY, Symbol.CASESY}):
                    self.Skip(26, fl_fsys | {Symbol.IDENTSY, Symbol.CASESY})
                while self.Token == Symbol.IDENTSY:
                    fl_exit = False
                    while not fl_exit:
                        if self.Token == Symbol.IDENTSY:
                            fl_lpN = N(NodeKind.IDENTNODE)
                            if FfldList is None:
                                FfldList = fl_lpN
                            else:
                                assert LastpN is not None
                                LastpN.Next = fl_lpN
                            if GrouppN is None:
                                GrouppN = fl_lpN
                            LastpN = fl_lpN
                            fl_lpN.Name = self.Ident
                            fl_lpN.Next = None
                            fl_lpN.Class = NameClass.FIELD
                            fl_lpN.Node = NodeKind.IDENTNODE
                            self.EnterId(fl_lpN)
                            self.Scan()
                        else:
                            self.Error(29)
                        if (self.Token != Symbol.COMMASY) and (self.Token != Symbol.COLONSY):
                            self.Skip(
                                20,
                                fl_fsys
                                | {Symbol.COMMASY, Symbol.COLONSY, Symbol.SEMISY, Symbol.CASESY},
                            )
                        if self.Token == Symbol.COMMASY:
                            self.Scan()
                        else:
                            fl_exit = True
                    if self.Token == Symbol.COLONSY:
                        self.Scan()
                    else:
                        self.Error(35)
                    fl_lpT = Typ(fl_fsys | {Symbol.CASESY, Symbol.SEMISY}, False, None)
                    while GrouppN is not None:
                        GrouppN.IdType = fl_lpT
                        GrouppN = GrouppN.Next
                    if fl_lpT is not None:
                        FileFlag = FileFlag or fl_lpT.FType
                    if self.Token == Symbol.SEMISY:
                        self.Scan()
                        if self.Token not in (fl_fsys | {Symbol.IDENTSY, Symbol.CASESY}):
                            self.Skip(26, fl_fsys | {Symbol.IDENTSY, Symbol.CASESY})

                if self.Token == Symbol.CASESY:
                    self.Scan()
                    TagNamepN = N(NodeKind.IDENTNODE)
                    TagPt = T(TypeForms.TAGFIELD)
                    TagNamepN.Name = '        '
                    TagNamepN.Next = None
                    TagNamepN.Llink = None
                    TagNamepN.Rlink = None
                    TagNamepN.Class = NameClass.FIELD
                    TagNamepN.IdType = None
                    TagNamepN.PckdField = False
                    TagNamepN.Node = NodeKind.IDENTNODE
                    TagPt.FType = False
                    TagPt.Form = TypeForms.TAGFIELD
                    TagPt.TagName = TagNamepN
                    TagPt.Variants = None
                    fTagFld = TagPt
                    if self.Token == Symbol.IDENTSY:
                        lName = self.Ident
                        self.Scan()
                        if self.Token == Symbol.COLONSY:
                            self.Scan()
                            if self.Token == Symbol.IDENTSY:
                                fl_lpN = self.SearchAll({NameClass.TYPES})
                                assert fl_lpN is not None
                                TagTypePt = fl_lpN.IdType
                                TagNamepN.IdType = TagTypePt
                                TagNamepN.Name = lName
                                if FfldList is None:
                                    FfldList = TagNamepN
                                else:
                                    assert LastpN is not None
                                    LastpN.Next = TagNamepN
                                self.EnterId(TagNamepN)
                                self.Scan()
                            else:
                                self.Skip(29, fl_fsys | {Symbol.OFSY, Symbol.LPARENSY})
                        else:
                            self.Ident = lName
                            fl_lpN = self.SearchAll({NameClass.TYPES})
                            assert fl_lpN is not None
                            TagTypePt = fl_lpN.IdType
                            TagNamepN.IdType = TagTypePt
                    else:
                        self.Skip(29, fl_fsys | {Symbol.OFSY, Symbol.LPARENSY})

                    if TagTypePt is not None:
                        if TagTypePt.Form > TypeForms.SUBRANGE:
                            self.Error(109)
                        elif self.CompTypes(self.RealPtr, TagTypePt):
                            self.Error(108)
                        FileFlag = FileFlag or TagTypePt.FType

                    if self.Token == Symbol.OFSY:
                        self.Scan()
                    else:
                        self.Error(42)

                    fl_exit = False
                    VarList: Optional[T] = None
                    while not fl_exit:
                        if self.Token not in ((fl_fsys | {Symbol.SEMISY}) - {Symbol.IDENTSY}):
                            Exit2Flag = False
                            iList: Optional[IntList] = None
                            while not Exit2Flag:
                                lValu, fl_lpT = self.Constant(
                                    fl_fsys | {Symbol.COMMASY, Symbol.COLONSY, Symbol.LPARENSY}
                                )
                                if not self.CompTypes(TagTypePt, fl_lpT):
                                    self.Error(110)
                                else:
                                    iList2 = IntList(lValu.Ivalu, iList)
                                    iList = iList2
                                    chk_list = iList.NextInt
                                    while chk_list is not None:
                                        if lValu.Ivalu == chk_list.IntVal:
                                            self.Error(160)
                                        chk_list = chk_list.NextInt
                                    VarPt_iter = VarList
                                    while VarPt_iter is not None:
                                        chk_list = VarPt_iter.VarValus
                                        while chk_list is not None:
                                            if lValu.Ivalu == chk_list.IntVal:
                                                self.Error(160)
                                            chk_list = chk_list.NextInt
                                        VarPt_iter = VarPt_iter.NextVar
                                if self.Token == Symbol.COMMASY:
                                    self.Scan()
                                else:
                                    Exit2Flag = True
                            if self.Token == Symbol.COLONSY:
                                self.Scan()
                            else:
                                self.Error(35)
                            if self.Token == Symbol.LPARENSY:
                                self.Scan()
                            else:
                                self.Error(31)
                            sub_flds, VarPt2 = FieldList(
                                fl_fsys | {Symbol.RPARENSY, Symbol.SEMISY}
                            )
                            VarPt = T(TypeForms.VARIANT)
                            VarPt.FType = False
                            VarPt.Form = TypeForms.VARIANT
                            VarPt.VarFldLst = sub_flds
                            VarPt.SubVar = VarPt2
                            VarPt.VarValus = iList
                            VarPt.NextVar = VarList
                            VarList = VarPt
                            if self.Token == Symbol.RPARENSY:
                                self.Scan()
                                if self.Token not in (fl_fsys | {Symbol.SEMISY}):
                                    self.Skip(20, fl_fsys | {Symbol.SEMISY})
                            else:
                                self.Error(32)
                        if self.Token == Symbol.SEMISY:
                            self.Scan()
                        else:
                            fl_exit = True
                    TagPt.Variants = VarList
                return FfldList, fTagFld

            def ClassList(
                cl_fsys: set[Symbol] | frozenset[Symbol],
                cl_FpT: T,
                cl_ThisClass: Optional[N],
            ) -> None:
                """Parse a Clascal SUBCLASS OF <SuperId | NIL> body: resolve the superclass,
                enter instance fields, parse method headers (ABSTRACT, OVERRIDE, DEFAULT),
                assign even/odd method-table slots with SELF parameter offsets, and validate CREATE."""
                nonlocal FileFlag
                self.InClassDecl = True

                if self.Token != Symbol.OFSY:
                    self.Skip(800, cl_fsys | {Symbol.IDENTSY})
                else:
                    self.Scan()

                # Determine superclass pointer
                if (self.Token != Symbol.IDENTSY) and (self.Token != Symbol.NILSY):
                    self.Skip(801, cl_fsys | {Symbol.IDENTSY, Symbol.FUNCTSY, Symbol.PROCSY})
                    SuperC = self.NilClassPtr
                else:
                    if self.Token == Symbol.NILSY:
                        SuperpN = None
                        SuperC = self.NilClassPtr
                    else:
                        SuperpN = self.SearchAll({NameClass.TYPES})
                        if SuperpN is None:
                            SuperC = self.NilClassPtr
                        else:
                            SuperC = SuperpN.IdType
                            if SuperC is None:
                                SuperC = self.NilClassPtr
                            elif SuperC.Form != TypeForms.CLASSES:
                                self.Error(807)
                                SuperC = self.NilClassPtr
                    self.Scan()

                assert SuperC is not None

                # Parse the fields
                if self.Token not in (cl_fsys | {Symbol.IDENTSY, Symbol.FUNCTSY, Symbol.PROCSY}):
                    self.Skip(26, cl_fsys | {Symbol.IDENTSY, Symbol.FUNCTSY, Symbol.PROCSY})

                GrouppN: Optional[N] = None
                CFields: Optional[N] = None
                LastpN: Optional[N] = None
                while self.Token == Symbol.IDENTSY:
                    cl_exit = False
                    while not cl_exit:
                        if self.Token == Symbol.IDENTSY:
                            cl_lpN = N(NodeKind.IDENTNODE)
                            if CFields is None:
                                CFields = cl_lpN
                            else:
                                assert LastpN is not None
                                LastpN.Next = cl_lpN
                            if GrouppN is None:
                                GrouppN = cl_lpN
                            LastpN = cl_lpN
                            cl_lpN.Name = self.Ident
                            cl_lpN.Next = None
                            cl_lpN.Class = NameClass.FIELD
                            cl_lpN.Node = NodeKind.IDENTNODE
                            cl_lpN.FOff = -1
                            Errs = self.Errors
                            self.EnterId(cl_lpN)
                            if Errs == self.Errors:
                                found_sup, _ = self.SearchClasses(SuperC, True)
                                if found_sup is not None:
                                    self.Error(100)
                            self.Scan()
                        else:
                            self.Error(29)
                        if (self.Token != Symbol.COMMASY) and (self.Token != Symbol.COLONSY):
                            self.Skip(
                                20,
                                cl_fsys
                                | {
                                    Symbol.COMMASY,
                                    Symbol.COLONSY,
                                    Symbol.SEMISY,
                                    Symbol.FUNCTSY,
                                    Symbol.PROCSY,
                                },
                            )
                        if self.Token == Symbol.COMMASY:
                            self.Scan()
                        else:
                            cl_exit = True

                    if self.Token == Symbol.COLONSY:
                        self.Scan()
                    else:
                        self.Error(35)

                    cl_lpT = Typ(
                        cl_fsys | {Symbol.FUNCTSY, Symbol.PROCSY, Symbol.SEMISY}, False, None
                    )
                    while GrouppN is not None:
                        GrouppN.IdType = cl_lpT
                        GrouppN = GrouppN.Next

                    if self.Token == Symbol.SEMISY:
                        self.Scan()
                        if self.Token not in (
                            cl_fsys | {Symbol.IDENTSY, Symbol.FUNCTSY, Symbol.PROCSY}
                        ):
                            self.Skip(
                                26, cl_fsys | {Symbol.IDENTSY, Symbol.FUNCTSY, Symbol.PROCSY}
                            )

                # Parse the method heads
                EvenMethodNumber = 0
                OddMethodNumber = 0
                KlassLevel = SuperC.ClassLevel + 2
                SeenCreate = False
                cl_FpT.ClFstMethod = None

                while (self.Token == Symbol.PROCSY) or (self.Token == Symbol.FUNCTSY):
                    m_token = self.Token
                    self.Scan()
                    if self.Token == Symbol.IDENTSY:
                        if cl_ThisClass is not None:
                            if cl_ThisClass.Name == self.Ident:
                                self.Scan()
                                if self.Token == Symbol.PERIODSY:
                                    self.Scan()
                                else:
                                    self.Error(51)

                    ForwCLst = self.ForwCList
                    ForwPLst = self.ForwPList
                    EnterIt = False
                    cl_lpN = PFHead(
                        cl_fsys | {Symbol.ENDSY, Symbol.IDENTSY},
                        m_token,
                        None,
                        False,
                        EnterIt,
                        None,
                    )
                    EnterIt = True

                    cl_lpN.PFdecl = PFkind.FORWMETHDECL
                    if self.Token != Symbol.IDENTSY:
                        Even = True
                    else:
                        Even = False
                        if self.Ident == 'ABSTRACT':
                            cl_lpN.RtnNo = 0
                            cl_lpN.PFdecl = PFkind.METHDECL
                        elif self.Ident == 'OVERRIDE':
                            self.Ident = cl_lpN.Name
                            lpN1, _ = self.SearchClasses(SuperC, True)
                            if lpN1 is None:
                                self.Error(818)
                            else:
                                if not self.CompFormals(lpN1.PFargList, cl_lpN.PFargList, True):
                                    self.Error(116)
                                if lpN1.IdType is not cl_lpN.IdType:
                                    self.Error(117)
                                self.ForwCList = ForwCLst
                                self.ForwPList = ForwPLst
                                EnterIt = False
                        elif self.Ident != 'DEFAULT ':
                            self.Error(20)
                        self.Scan()
                        if self.Token == Symbol.SEMISY:
                            self.Scan()

                    if EnterIt:
                        SaveIdent = self.Ident
                        self.Ident = cl_lpN.Name
                        found_sup, _ = self.SearchClasses(SuperC, True)
                        if found_sup is not None:
                            self.Error(100)
                        else:
                            self.EnterId(cl_lpN)
                        self.Ident = SaveIdent
                        if cl_lpN.Name == 'CREATE  ':
                            SeenCreate = True
                            cl_lpN.MethodNo = 0
                            cl_lpN.MethodLevel = 0
                        else:
                            if Even:
                                EvenMethodNumber += 1
                                cl_lpN.MethodNo = EvenMethodNumber
                                cl_lpN.MethodLevel = KlassLevel
                            else:
                                OddMethodNumber += 1
                                cl_lpN.MethodNo = OddMethodNumber
                                cl_lpN.MethodLevel = KlassLevel + 1
                            cl_lpN.ParmBytes = cl_lpN.ParmBytes + 4
                            lpN1 = cl_lpN.PFargList
                            while lpN1 is not None:
                                if lpN1.Class == NameClass.VARS:
                                    if lpN1.Voff >= 0:
                                        lpN1.Voff = lpN1.Voff + 4
                                else:
                                    lpN1.PFOff = lpN1.PFOff + 4
                                lpN1 = lpN1.Next

                        cl_lpN.Next = None
                        InsertMethod(
                            cl_lpN, cl_lpN.MethodLevel * 256 + cl_lpN.MethodNo, cl_FpT
                        )

                if not SeenCreate:
                    self.Error(802)

                cl_FpT.Bytes = 0
                cl_FpT.Bits = 0
                cl_FpT.Form = TypeForms.CLASSES
                cl_FpT.FType = False
                cl_FpT.WasDeclared = self.Level < -1
                cl_FpT.NeedsInit = not cl_FpT.WasDeclared
                self.ClassesToInit = self.ClassesToInit or cl_FpT.NeedsInit
                cl_FpT.ItsId = None
                cl_FpT.ClFields = self.Display[self.Top].NameTree
                cl_FpT.ClFstField = CFields
                cl_FpT.SuperClass = SuperC
                cl_FpT.TotalOrder = None
                cl_FpT.LastEvenMethod = EvenMethodNumber
                cl_FpT.LastOddMethod = OddMethodNumber
                cl_FpT.ClassLevel = KlassLevel
                cl_FpT.CrProc = None
                cl_FpT.MethodLevel = -1
                cl_FpT.MethodOff = -1

                FileFlag = False
                self.InClassDecl = False

            # Body of Typ
            FpT: Optional[T] = self.IntPtr
            if self.Token not in TypeBegSys:
                self.Skip(25, t_fsys | TypeBegSys)
            ClassAllowed = ClassAllowed and (self.Token == Symbol.SUBCLSY)
            if self.Token in TypeBegSys:
                if self.Token in SimpTypeBegSys:
                    FpT = SimpleType(t_fsys)
                elif self.Token == Symbol.UPARROWSY:
                    self.Scan()
                    if self.Token == Symbol.IDENTSY:
                        FpT = T(TypeForms.POINTERS)
                        FpT.Form = TypeForms.POINTERS
                        FpT.PointerTo = None
                        FpT.FType = False
                        self.PrintErrors = False
                        t_lpN = self.SearchAll({NameClass.TYPES})
                        self.PrintErrors = True
                        if t_lpN is None:
                            t_lpN = N(NodeKind.IDENTNODE)
                            t_lpN.Name = self.Ident
                            t_lpN.IdType = FpT
                            t_lpN.Class = NameClass.TYPES
                            t_lpN.Next = self.ForwPList
                            t_lpN.Node = NodeKind.IDENTNODE
                            self.ForwPList = t_lpN
                        else:
                            FpT.PointerTo = t_lpN.IdType
                        CalcSize(FpT)
                        self.Scan()
                    else:
                        self.Error(29)
                else:
                    PackedFlag = self.Token == Symbol.PACKEDSY
                    if PackedFlag:
                        self.Scan()
                    if self.Token == Symbol.ARRAYSY:
                        self.Scan()
                        FpT = T(TypeForms.ARRAYS)
                        FpT.Form = TypeForms.ARRAYS
                        FpT.ArrayOf = None
                        FpT.PckdArr = PackedFlag
                        FpT.BitPackd = False
                        arr_lpT: Optional[T] = FpT
                        if self.Token == Symbol.LBRACKSY:
                            self.Scan()
                        else:
                            self.Error(33)
                        arr_exit = False
                        while not arr_exit:
                            lpT2 = SimpleType(
                                t_fsys | {Symbol.COMMASY, Symbol.RBRACKSY, Symbol.OFSY}
                            )
                            if lpT2 is not None:
                                if lpT2.Form > TypeForms.SUBRANGE:
                                    self.Error(112)
                                elif self.CompTypes(lpT2, self.RealPtr):
                                    self.Error(111)
                                elif (lpT2 is self.IntPtr) or (lpT2 is self.LIntPtr):
                                    self.Error(113)
                                elif lpT2.Form == TypeForms.SUBRANGE:
                                    if (lpT2.Max - lpT2.Min) > 32768:
                                        self.Error(311)
                            assert arr_lpT is not None
                            arr_lpT.IndexedBy = lpT2
                            if self.Token == Symbol.COMMASY:
                                lpT3 = T(TypeForms.ARRAYS)
                                lpT3.ArrayOf = arr_lpT
                                arr_lpT = lpT3
                                arr_lpT.Form = TypeForms.ARRAYS
                                arr_lpT.PckdArr = PackedFlag
                                arr_lpT.BitPackd = False
                                self.Scan()
                            else:
                                arr_exit = True
                        if self.Token == Symbol.RBRACKSY:
                            self.Scan()
                        else:
                            self.Error(34)
                        if self.Token == Symbol.OFSY:
                            self.Scan()
                        else:
                            self.Error(42)
                        lpT2 = Typ(t_fsys, False, None)
                        while arr_lpT is not None:
                            lpT3_prev = arr_lpT.ArrayOf
                            arr_lpT.ArrayOf = lpT2
                            if lpT2 is not None:
                                arr_lpT.FType = lpT2.FType
                            lpT2 = arr_lpT
                            arr_lpT = lpT3_prev
                            CalcSize(lpT2)
                    elif self.Token == Symbol.FILESY:
                        FpT = T(TypeForms.FILES)
                        FpT.FType = True
                        FpT.Form = TypeForms.FILES
                        FpT.PckdFile = PackedFlag
                        self.Scan()
                        if self.Token in t_fsys:
                            FpT.FileOf = None
                        else:
                            if self.Token == Symbol.OFSY:
                                self.Scan()
                            else:
                                self.Error(42)
                            FpT.FileOf = Typ(t_fsys, False, None)
                        CalcSize(FpT)
                    elif self.Token == Symbol.RECORDSY:
                        OldTop = self.Top
                        if self.Top < MAXDISPLAY:
                            self.Top += 1
                            self.Display[self.Top].NameTree = None
                            self.Display[self.Top].Occur = Where.REC
                        else:
                            self.Error(300)
                        self.Scan()
                        FileFlag = False
                        rec_flds, rec_var = FieldList(
                            (t_fsys - {Symbol.SEMISY}) | {Symbol.ENDSY}
                        )
                        FpT = T(TypeForms.RECORDS)
                        FpT.Form = TypeForms.RECORDS
                        FpT.FType = FileFlag
                        FpT.PckdRec = PackedFlag
                        FpT.Fields = self.Display[self.Top].NameTree
                        FpT.VarPart = rec_var
                        FpT.FstField = rec_flds
                        self.Top = OldTop
                        if self.Token == Symbol.ENDSY:
                            self.Scan()
                        else:
                            self.Error(44)
                        CalcSize(FpT)
                    elif self.Token == Symbol.SETSY:
                        self.Scan()
                        if self.Token == Symbol.OFSY:
                            self.Scan()
                        else:
                            self.Error(42)
                        set_lpT = SimpleType(t_fsys)
                        FpT = T(TypeForms.SETS)
                        FpT.Form = TypeForms.SETS
                        FpT.FType = False
                        FpT.SetOf = set_lpT
                        if set_lpT is not None:
                            if set_lpT.Form > TypeForms.SUBRANGE:
                                self.Error(109)
                            elif set_lpT is self.LIntPtr:
                                self.Error(301)
                            elif self.CompTypes(set_lpT, self.RealPtr):
                                self.Error(108)
                            else:
                                if set_lpT.Form == TypeForms.SUBRANGE:
                                    if (set_lpT.Min < 0) or (set_lpT.Max > 4087):
                                        self.Error(301)
                                else:
                                    _, b_max = self.GetBounds(set_lpT)
                                    if b_max > 4087:
                                        self.Error(301)
                        CalcSize(FpT)
                    elif self.Token == Symbol.STRINGSY:
                        self.Scan()
                        if self.Token == Symbol.LBRACKSY:
                            self.Scan()
                        else:
                            self.Error(33)
                        lValu, str_lpT = self.Constant(t_fsys | {Symbol.RBRACKSY})
                        if str_lpT is not self.IntPtr:
                            self.Error(107)
                        elif (lValu.Ivalu <= 0) or (lValu.Ivalu > 255):
                            self.Error(302)
                        FpT = T(TypeForms.STRINGS)
                        FpT.FType = False
                        FpT.Form = TypeForms.STRINGS
                        FpT.StringLen = lValu.Ivalu
                        if self.Token == Symbol.RBRACKSY:
                            self.Scan()
                        else:
                            self.Error(34)
                        CalcSize(FpT)
                    elif self.Token == Symbol.SUBCLSY:
                        if not ClassAllowed:
                            self.Error(803)
                        ClassAllowed = False

                        OldTop = self.Top
                        if self.Top < MAXDISPLAY:
                            self.Top += 1
                            self.Display[self.Top].NameTree = None
                            self.Display[self.Top].Occur = Where.KLASS
                            self.Display[self.Top].KType = None
                            self.Display[self.Top].WVar = None
                        else:
                            self.Error(300)
                        self.Scan()
                        FileFlag = False
                        FpT = T(TypeForms.CLASSES)
                        ClassList(
                            (t_fsys - {Symbol.SEMISY}) | {Symbol.ENDSY}, FpT, ThisClass
                        )
                        self.Top = OldTop
                        if self.Token == Symbol.ENDSY:
                            self.Scan()
                        else:
                            self.Error(44)
                        CalcSize(FpT)
                    else:
                        self.Skip(25, t_fsys)
                if self.Token not in t_fsys:
                    self.Skip(20, t_fsys)
            return FpT

        def IntriDecl() -> None:
            """Parse an INTRINSIC unit header ([CODE n] [SHARED] [DATA n]; INTERFACE) and set FpN.Ukind."""
            assert FpN is not None
            FpN.Ukind = UnitKind.INTRUNIT
            if self.Token == Symbol.IDENTSY:
                if self.Ident == 'CODE    ':
                    self.Scan()
                    self.Scan()
            if (self.Token == Symbol.IDENTSY) and (self.Ident == 'SHARED  '):
                FpN.Ukind = UnitKind.SHARUNIT
                self.Scan()
            if self.Token == Symbol.IDENTSY:
                if self.Ident == 'DATA    ':
                    self.Scan()
                    self.Scan()
            if self.Token == Symbol.SEMISY:
                self.Scan()
            else:
                self.Error(36)
            if self.Token == Symbol.INTERSY:
                self.Scan()
            else:
                self.Error(53)

        def UsesDecl(u_fsys: set[Symbol] | frozenset[Symbol]) -> None:
            """Parse a USES clause, loading each referenced unit's INTERFACE declarations
            from intrinsic or regular unit/library files into negative lexical levels while
            preserving current source-line listing state."""
            u_lpN: Optional[N] = None
            DummyHeap: int = 0
            LibFound: bool = False

            def FindUnit(FName: str, Start: int) -> bool:
                """Locate unit FName in a library (0x90), unlinked unit (0x92), or intrinsic
                library (0x99/0x92) file starting at Start, seek to its embedded INTERFACE
                source text, strip the high-bit HasClasses marker if set, and prime Scan."""
                lBlock: int = 0
                lByte: int = 0
                sBlock: int = 0
                lBuff = bytearray(512)

                def NextByte() -> int:
                    """Read the next unsigned byte from the open unit/library file across 512-byte blocks."""
                    nonlocal lBlock, lByte
                    if lByte > 511:
                        lBlock = lBlock + pdiv(lByte, 512)
                        lByte = pmod(lByte, 512)
                        if (
                            self.rt.block_read(
                                self.OpenFileStack[self.TopOfOpenFileStack].SrcFile,
                                lBuff,
                                1,
                                lBlock,
                            )
                            != 1
                        ):
                            self.Error(404)
                    b_val = lBuff[lByte]
                    lByte += 1
                    return b_val

                def NextInt(n_bytes: int) -> int:
                    """Read an n_bytes big-endian unsigned integer from the unit/library header."""
                    k = 0
                    for _ in range(n_bytes):
                        k = k * 256 + NextByte()
                    return k

                if Start == 0:
                    lBlock = -1
                    lByte = 512
                    hdr = NextByte()
                else:
                    lBlock = pdiv(Start, 512)
                    lByte = pmod(Start, 512)
                    if (
                        self.rt.block_read(
                            self.OpenFileStack[self.TopOfOpenFileStack].SrcFile,
                            lBuff,
                            1,
                            lBlock,
                        )
                        != 1
                    ):
                        self.Error(404)
                    sBlock = lBlock
                    hdr = NextByte()

                FoundIt = False
                if hdr == 144:  # Library file
                    while hdr == 144:
                        Size = NextInt(3)
                        FoundIt = True
                        for idx in range(8):
                            if FName[idx] != chr(NextByte()):
                                FoundIt = False
                        if FoundIt:
                            _ = NextInt(4)
                            _ = NextInt(4)
                            TextAddr = pdiv(NextInt(3), 2)
                            self.FileSeek(TextAddr)
                            self.FillInbuf()
                            if self.Inbuf[self.InbufP] > 127:
                                assert u_lpN is not None
                                u_lpN.HasClasses = True
                                self.Inbuf[self.InbufP] = self.Inbuf[self.InbufP] - 128
                            self.Ch = ' '
                            self.EolSource = True
                            self.Scan()
                            return FoundIt  # GOTO 5
                        lByte = lByte + Size - 12
                        hdr = NextByte()
                elif (hdr == 146) and (Start == 0):  # unlinked Unit file
                    _ = NextInt(3)
                    FoundIt = True
                    for idx in range(8):
                        if FName[idx] != chr(NextByte()):
                            FoundIt = False
                    if FoundIt:
                        _ = NextInt(4)
                        TextAddr = pdiv(NextInt(3), 2)
                        self.FileSeek(TextAddr)
                        self.FillInbuf()
                        if self.Inbuf[self.InbufP] > 127:
                            assert u_lpN is not None
                            u_lpN.HasClasses = True
                            self.Inbuf[self.InbufP] = self.Inbuf[self.InbufP] - 128
                        self.Ch = ' '
                        self.EolSource = True
                        self.Scan()
                elif (hdr == 0x99) or (hdr == 0x92):  # I.U. Library file
                    FoundIt = False
                    while True:
                        Size = NextInt(3)
                        if hdr == 0x92:
                            FoundIt = True
                            for idx in range(8):
                                lCh = chr(NextByte())
                                if FName[idx] != lCh:
                                    FoundIt = False
                            if FoundIt:
                                if Size > 30:
                                    _ = NextInt(4)
                                    _ = NextInt(4)
                                    _ = NextInt(4)
                                    _ = NextInt(4)
                                    _ = NextInt(2)
                                    self.FileSeek(sBlock)
                                    self.FillInbuf()
                                    if lBlock == sBlock:
                                        self.InbufP = lByte
                                    else:
                                        self.InbufP = lByte + 512
                                    if self.Inbuf[self.InbufP] > 127:
                                        assert u_lpN is not None
                                        u_lpN.HasClasses = True
                                        self.Inbuf[self.InbufP] = self.Inbuf[self.InbufP] - 128
                                    self.Ch = ' '
                                    self.EolSource = True
                                    self.Scan()
                                    return FoundIt  # GOTO 5
                                else:
                                    FoundIt = False
                                    return FoundIt  # GOTO 5
                            Size = Size - 8
                        lByte = lByte + Size - 4
                        hdr = NextByte()
                        sBlock = lBlock
                        if FoundIt or (hdr == 0x00):
                            break
                else:
                    FoundIt = False
                # 5:
                return FoundIt

            def ReadInterface(FName: str, fLoc: int) -> None:
                """Open intrinsic library file FName at offset fLoc and parse the target unit's INTERFACE."""
                nonlocal u_lpN, DummyHeap, LibFound
                if self.OpenNewFile(FName, InputFileTypes.USED):
                    assert u_lpN is not None
                    if FindUnit(u_lpN.Name, fLoc):
                        u_lpN, DummyHeap = self.Declarations(
                            u_fsys | {Symbol.IMPLESY}, Symbol.USESSY, u_lpN, DummyHeap, None
                        )
                        LibFound = True
                    self.PreviousFile()

            OldLevel = self.Level
            u_exit = False

            while not u_exit:
                if self.Token == Symbol.IDENTSY:
                    if not self.Using:
                        u_lpN = self.SearchLocal(self.Display[1].NameTree)
                        if u_lpN is None:
                            if self.NumUnits < MAXUNITS:
                                self.NumUnits += 1
                            else:
                                self.Error(307)
                            self.Level = -self.NumUnits
                            u_lpN = N(NodeKind.IDENTNODE)
                            u_lpN.Node = NodeKind.IDENTNODE
                            u_lpN.Name = self.Ident
                            u_lpN.Next = self.UnitList
                            u_lpN.Class = NameClass.UNITS
                            u_lpN.Ulev = self.Level
                            u_lpN.ULc = 0
                            u_lpN.Ukind = UnitKind.REGUNIT
                            u_lpN.HasClasses = False

                            lNameTree = self.Display[self.Top].NameTree
                            self.Display[self.Top].NameTree = None
                            self.EnterId(u_lpN)
                            self.UnitList = u_lpN

                            self.Scan()
                            lCh = self.Ch
                            lToken = self.Token
                            lIdent = self.Ident
                            lIntVal = self.IntVal
                            lRealVal = self.RealVal
                            lStrVal = self.StrVal
                            pCurL = self.pCurLine
                            if self.pCurLine > 0:
                                self.CurLine = self.CurLine[: self.pCurLine]
                            else:
                                self.CurLine = ''
                            if not self.EolSource:
                                idx = self.InbufP
                                while (idx < len(self.Inbuf)) and (self.Inbuf[idx] != 13):
                                    self.pCurLine += 1
                                    self.CurLine = pset_ch(
                                        self.CurLine, self.pCurLine, chr(self.Inbuf[idx])
                                    )
                                    idx += 1
                            EndOfLine = self.pCurLine
                            lCurLine = self.CurLine[: max(0, EndOfLine)]

                            if self.Listing:
                                self.TotalLines = self.ListLine(self.TotalLines)
                            else:
                                self.TotalLines += 1
                                self.LinePrinted = True
                            self.pCurLine = pCurL

                            self.Using = True
                            LibFound = False

                            if self.SearchLibrary:
                                assert FpN is not None
                                self.IULibIn = self.rt.IntrinIndirect(
                                    self.IULibIn, FpN.Name, ReadInterface, u_lpN.Name
                                )

                            goto_9 = False
                            if not LibFound:
                                if self.OpenNewFile(self.UFname, InputFileTypes.USED):
                                    if FindUnit(u_lpN.Name, 0):
                                        u_lpN, DummyHeap = self.Declarations(
                                            u_fsys | {Symbol.IMPLESY},
                                            Symbol.USESSY,
                                            u_lpN,
                                            DummyHeap,
                                            None,
                                        )
                                    else:
                                        self.Error(190)
                                    self.PreviousFile()
                                else:
                                    if self.rt.io_result > 0:
                                        self.Error(403)
                                        goto_9 = True

                            if not goto_9:
                                assert u_lpN is not None
                                self.Display[self.Top].NameTree = lNameTree
                                self.UnitsToInit = self.UnitsToInit or u_lpN.HasClasses

                            # 9:
                            DummyHeap = 0
                            assert u_lpN is not None
                            u_lpN.Utop = DummyHeap
                            self.Ch = lCh
                            self.Token = lToken
                            self.Ident = lIdent
                            self.IntVal = lIntVal
                            self.RealVal = lRealVal
                            self.StrVal = lStrVal
                            self.pCurLine = EndOfLine
                            self.CurLine = lCurLine
                            if self.ErrIndex > 0:
                                self.ListErrors()
                            self.pCurLine = pCurL
                            self.CurLine = self.CurLine[: max(0, pCurL)]

                        self.Using = False
                        if self.Token not in (u_fsys | {Symbol.COMMASY, Symbol.SEMISY}):
                            self.Skip(20, u_fsys | {Symbol.COMMASY, Symbol.SEMISY})
                    else:
                        self.Scan()
                else:
                    self.Skip(29, u_fsys | {Symbol.COMMASY, Symbol.SEMISY})

                if self.Token == Symbol.COMMASY:
                    self.Scan()
                else:
                    u_exit = True

            if self.Token == Symbol.SEMISY:
                self.Scan()
            else:
                u_exit = True
            self.Level = OldLevel

        def LabelDecl(lb_fsys: set[Symbol] | frozenset[Symbol]) -> None:
            """Parse a LABEL declaration list (0..9999) and register LabRec entries in Display[Level].Labels."""
            lb_exit = False
            while not lb_exit:
                if self.Token == Symbol.ICONSTSY:
                    if self.IntVal >= 10000:
                        self.Error(173)
                    lpLabRec = self.Display[self.Level].Labels
                    while lpLabRec is not None:
                        if self.IntVal == lpLabRec.LabelNo:
                            self.Error(156)
                        lpLabRec = lpLabRec.NextLabel
                    lpLabRec = LabRec()
                    lpLabRec.NextLabel = self.Display[self.Level].Labels
                    lpLabRec.LabelNo = self.IntVal
                    lpLabRec.Defined = False
                    lpLabRec.GlobRefNo = -1
                    self.Display[self.Level].Labels = lpLabRec
                    self.Scan()
                else:
                    self.Error(30)
                if self.Token not in (lb_fsys | {Symbol.COMMASY, Symbol.SEMISY}):
                    self.Skip(20, lb_fsys | {Symbol.COMMASY, Symbol.SEMISY})
                if self.Token == Symbol.COMMASY:
                    self.Scan()
                else:
                    lb_exit = True
            if self.Token == Symbol.SEMISY:
                self.Scan()
            else:
                self.Error(36)

        def ConstDecl(cd_fsys: set[Symbol] | frozenset[Symbol]) -> None:
            """Parse CONST declarations (ident = constant;) and enter CONSTS symbol nodes into the current scope."""
            if self.Token != Symbol.IDENTSY:
                self.Skip(29, cd_fsys | {Symbol.IDENTSY})
            while self.Token == Symbol.IDENTSY:
                cd_lpN = N(NodeKind.IDENTNODE)
                cd_lpN.Name = self.Ident
                cd_lpN.Next = None
                cd_lpN.Class = NameClass.CONSTS
                cd_lpN.Node = NodeKind.IDENTNODE
                self.Scan()
                if self.Token == Symbol.EQSY:
                    self.Scan()
                else:
                    self.Error(37)
                lValu, cd_lpT = self.Constant(cd_fsys | {Symbol.SEMISY})
                cd_lpN.IdType = cd_lpT
                cd_lpN.ValueOf = lValu.copy()
                self.EnterId(cd_lpN)
                if self.Token == Symbol.SEMISY:
                    self.Scan()
                    if self.Token not in (cd_fsys | {Symbol.IDENTSY}):
                        self.Skip(20, cd_fsys | {Symbol.IDENTSY})
                else:
                    self.Error(36)

        def TypeDecl(td_fsys: set[Symbol] | frozenset[Symbol]) -> None:
            """Parse TYPE declarations, backpatch forward class (ForwCList) and pointer
            (ForwPList) references, link Clascal classes into SuperClass.TotalOrder,
            verify CREATE return types, and report unresolved forward types."""
            if self.Token != Symbol.IDENTSY:
                self.Skip(29, td_fsys | {Symbol.IDENTSY})
            while self.Token == Symbol.IDENTSY:
                td_lpN = N(NodeKind.IDENTNODE)
                td_lpN.Name = self.Ident
                td_lpN.Next = None
                td_lpN.Class = NameClass.TYPES
                td_lpN.Node = NodeKind.IDENTNODE
                self.Scan()
                if self.Token == Symbol.EQSY:
                    self.Scan()
                else:
                    self.Error(37)
                NotEquate = self.Token != Symbol.IDENTSY
                td_lpT = Typ(
                    td_fsys | {Symbol.SEMISY}, self.InterFlag or self.InUses, td_lpN
                )
                td_lpN.IdType = td_lpT

                if (td_lpT is not None) and (td_lpT.Form == TypeForms.CLASSES):
                    lpN2 = self.ForwCList
                    lpN3: Optional[N] = None
                    while lpN2 is not None:
                        if td_lpN.Name == lpN2.Name:
                            if lpN2 is self.ForwCList:
                                self.ForwCList = self.ForwCList.Next
                            else:
                                assert lpN3 is not None
                                lpN3.Next = lpN2.Next
                            fwd_t = lpN2.IdType
                            assert fwd_t is not None
                            fwd_t.Marked = td_lpT.Marked
                            fwd_t.FType = td_lpT.FType
                            fwd_t.Form = td_lpT.Form
                            fwd_t.WasDeclared = td_lpT.WasDeclared
                            fwd_t.NeedsInit = td_lpT.NeedsInit
                            fwd_t.SuperClass = td_lpT.SuperClass
                            fwd_t.LastEvenMethod = td_lpT.LastEvenMethod
                            fwd_t.LastOddMethod = td_lpT.LastOddMethod
                            fwd_t.ClFields = td_lpT.ClFields
                            fwd_t.ClFstField = td_lpT.ClFstField
                            fwd_t.ClFstMethod = td_lpT.ClFstMethod
                            fwd_t.MethodOff = td_lpT.MethodOff
                            fwd_t.MethodLevel = td_lpT.MethodLevel
                            fwd_t.SizeInstance = td_lpT.SizeInstance
                            fwd_t.ClassLevel = td_lpT.ClassLevel
                            fwd_t.CrProc = td_lpT.CrProc
                            td_lpT = fwd_t
                            break  # GOTO 10
                        else:
                            lpN3 = lpN2
                        lpN2 = lpN2.Next
                    # 10:
                    td_lpN.IdType = td_lpT

                    if NotEquate:
                        td_lpT.ItsId = td_lpN
                        assert td_lpT.SuperClass is not None
                        td_lpT.TotalOrder = td_lpT.SuperClass.TotalOrder
                        td_lpT.SuperClass.TotalOrder = td_lpT
                else:
                    lpN2 = self.ForwPList
                    lpN3 = None
                    while lpN2 is not None:
                        if lpN2.Name == td_lpN.Name:
                            assert lpN2.IdType is not None
                            lpN2.IdType.PointerTo = td_lpN.IdType
                            if lpN2 is self.ForwPList:
                                self.ForwPList = self.ForwPList.Next
                            else:
                                assert lpN3 is not None
                                lpN3.Next = lpN2.Next
                        else:
                            lpN3 = lpN2
                        lpN2 = lpN2.Next

                self.EnterId(td_lpN)

                if (td_lpT is not None) and (td_lpT.Form == TypeForms.CLASSES) and NotEquate:
                    self.Ident = 'CREATE  '
                    cr_pN = self.SearchLocal(td_lpT.ClFields)
                    BadCreate = False
                    if cr_pN is not None:
                        BadCreate = True
                        if cr_pN.Class == NameClass.FUNC:
                            if cr_pN.IdType is not None:
                                BadCreate = cr_pN.IdType is not td_lpT
                    if BadCreate:
                        self.Error(811)

                if self.Token == Symbol.SEMISY:
                    self.Scan()
                    if self.Token not in (td_fsys | {Symbol.IDENTSY}):
                        self.Skip(20, td_fsys | {Symbol.IDENTSY})
                else:
                    self.Error(36)

            if self.ForwPList is not None:
                while self.ForwPList is not None:
                    self.NError(114, self.ForwPList.Name)
                    self.ForwPList = self.ForwPList.Next

            if self.ForwCList is not None:
                while self.ForwCList is not None:
                    self.NError(114, self.ForwCList.Name)
                    self.ForwCList = self.ForwCList.Next

        def VarDecl(vd_fsys: set[Symbol] | frozenset[Symbol]) -> None:
            """Parse VAR declarations, allocate negative stack-frame (Lc) or unit-global
            (ULc) offsets (Voff) with word alignment and 32 KB overflow checks, and report
            any unresolved forward types."""
            assert FpN is not None
            if FpN.Class == NameClass.UNITS:
                lLc = i16(-FpN.ULc)
            else:
                lLc = i16(-FpN.Lc)
            while True:
                vd_exit = False
                lpN2: Optional[N] = None
                while not vd_exit:
                    if self.Token == Symbol.IDENTSY:
                        vd_lpN = N(NodeKind.IDENTNODE)
                        vd_lpN.InRegister = -1
                        vd_lpN.Name = self.Ident
                        vd_lpN.Next = lpN2
                        vd_lpN.Class = NameClass.VARS
                        vd_lpN.IdType = None
                        vd_lpN.Vlev = self.Level
                        vd_lpN.Voff = 0
                        vd_lpN.Vkind = AccessKind.DRCT
                        vd_lpN.Node = NodeKind.IDENTNODE
                        vd_lpN.IsSELF = False
                        vd_lpN.UNIVflag = False
                        self.EnterId(vd_lpN)
                        lpN2 = vd_lpN
                        self.Scan()
                    else:
                        self.Error(29)
                    if self.Token not in (
                        vd_fsys | {Symbol.COMMASY, Symbol.COLONSY} | TypeDels
                    ):
                        self.Skip(
                            20,
                            vd_fsys
                            | {Symbol.COMMASY, Symbol.COLONSY, Symbol.SEMISY}
                            | TypeDels,
                        )
                    if self.Token == Symbol.COMMASY:
                        self.Scan()
                    else:
                        vd_exit = True
                if self.Token == Symbol.COLONSY:
                    self.Scan()
                else:
                    self.Error(35)
                vd_lpT = Typ(vd_fsys | {Symbol.SEMISY} | TypeDels, False, None)
                if vd_lpT is not None:
                    lpTSize = self.FullBytes(vd_lpT)
                    while lpN2 is not None:
                        lpN2.IdType = vd_lpT
                        if lpTSize != 1:
                            if odd(lLc):
                                lLc = i16(lLc - 1)
                        lLc = i16(lLc - lpTSize)
                        lpN2.Voff = lLc
                        if lLc >= 0:
                            if self.Level > 1:
                                self.Error(312)
                            else:
                                self.Error(313)
                            lLc = 0
                        lpN2 = lpN2.Next
                if self.Token == Symbol.SEMISY:
                    self.Scan()
                    if self.Token not in (vd_fsys | {Symbol.IDENTSY}):
                        self.Skip(20, vd_fsys | {Symbol.IDENTSY})
                else:
                    self.Error(36)
                if (self.Token != Symbol.IDENTSY) and (self.Token not in TypeDels):
                    break

            if odd(lLc):
                lLc = i16(lLc - 1)
            if FpN.Class == NameClass.UNITS:
                FpN.ULc = i16(-lLc)
            else:
                FpN.Lc = i16(-lLc)

            if self.ForwPList is not None:
                while self.ForwPList is not None:
                    self.NError(115, self.ForwPList.Name)
                    self.ForwPList = self.ForwPList.Next

            if self.ForwCList is not None:
                while self.ForwCList is not None:
                    self.NError(115, self.ForwCList.Name)
                    self.ForwCList = self.ForwCList.Next

        def PFHead(
            pf_fsys: set[Symbol] | frozenset[Symbol],
            fToken: Symbol,
            _FpN_unused: Optional[N],
            FormalFlag: bool,
            EnterIt: bool,
            pf_ClasspT: Optional[T],
        ) -> N:
            """Parse a PROCEDURE or FUNCTION header—supporting normal, nested, interface,
            formal-parameter, FORWARD-resolved, and Clascal method/override declarations—and
            validate parameter and return types."""
            ForwFlag: bool = False
            pf_lpN: Optional[N] = None

            def Override(ov_FpN: N) -> N:
                """Clone inherited Clascal method symbol ov_FpN and its formal parameters
                into subclass pf_ClasspT, preserving MethodLevel/MethodNo while assigning a new RtnNo."""
                assert pf_ClasspT is not None
                OldTop = self.Top
                OldLevel = self.Level
                if (self.Top + 1) < MAXDISPLAY:
                    self.Top += 1
                    self.Display[self.Top].NameTree = pf_ClasspT.ClFields
                    self.Display[self.Top].Occur = Where.KLASS
                    self.Display[self.Top].KType = None
                    self.Display[self.Top].WVar = None
                else:
                    self.Error(303)
                lFpN = N(NodeKind.IDENTNODE)
                InsertMethod(lFpN, ov_FpN.MethodLevel * 256 + ov_FpN.MethodNo, pf_ClasspT)
                lFpN.Name = ov_FpN.Name
                lFpN.Class = ov_FpN.Class
                lFpN.IdType = ov_FpN.IdType
                lFpN.PFdeclKind = ov_FpN.PFdeclKind
                lFpN.PFdecl = PFkind.FORWMETHDECL
                lFpN.PFargList = None
                lFpN.PFlev = ov_FpN.PFlev
                lFpN.Node = NodeKind.IDENTNODE
                lFpN.RtnNo = self.LocProcNo
                self.LocProcNo += 1
                lFpN.MethodNo = ov_FpN.MethodNo
                lFpN.MethodLevel = ov_FpN.MethodLevel
                lFpN.Lc = ov_FpN.Lc
                lFpN.ParmBytes = ov_FpN.ParmBytes
                Errs = self.Errors
                self.EnterId(lFpN)
                if self.Errors == Errs:
                    pf_ClasspT.ClFields = self.Display[self.Top].NameTree
                if self.Level <= 0:
                    self.Level = 2
                elif self.Level < MAXLEVEL:
                    self.Level += 1
                else:
                    self.Error(303)
                if self.Top < MAXDISPLAY:
                    self.Top += 1
                self.Display[self.Top].NameTree = None
                self.Display[self.Top].Occur = Where.PARAMS
                arg_pN = ov_FpN.PFargList
                LastApN: Optional[N] = None
                while arg_pN is not None:
                    if arg_pN.Class == NameClass.VARS:
                        npN = N(NodeKind.IDENTNODE)
                        npN.IsSELF = False
                        npN.UNIVflag = False
                        npN.Vkind = arg_pN.Vkind
                        npN.InRegister = -1
                        npN.Vlev = arg_pN.Vlev
                        npN.Voff = arg_pN.Voff
                    else:
                        npN = N(NodeKind.IDENTNODE)
                        npN.PFdeclKind = arg_pN.PFdeclKind
                        npN.PFlev = arg_pN.PFlev
                        npN.PFargList = arg_pN.PFargList
                        npN.PFdecl = arg_pN.PFdecl
                        npN.PFOff = arg_pN.PFOff
                    npN.Node = NodeKind.IDENTNODE
                    npN.Name = arg_pN.Name
                    npN.IdType = arg_pN.IdType
                    npN.Class = arg_pN.Class
                    npN.Next = None
                    if LastApN is not None:
                        LastApN.Next = npN
                    LastApN = npN
                    self.EnterId(npN)
                    arg_pN = arg_pN.Next
                lFpN.PFargList = self.Display[self.Top].NameTree
                self.Top = OldTop
                self.Level = OldLevel
                return lFpN

            def GetAType() -> Optional[T]:
                """Look up a parameter or function result type name, creating or reusing a forward CLASSES entry on ForwCList if undeclared."""
                if self.InClassDecl:
                    self.PrintErrors = False
                ga_lpN = self.SearchAll({NameClass.TYPES})
                if self.InClassDecl:
                    self.PrintErrors = True

                ga_FpT: Optional[T] = None
                if ga_lpN is None:
                    ga_lpN = self.ForwCList
                    found_forw = False
                    while ga_lpN is not None:
                        if self.Ident == ga_lpN.Name:
                            ga_FpT = ga_lpN.IdType
                            found_forw = True
                            break  # GOTO 10
                        ga_lpN = ga_lpN.Next

                    if not found_forw:
                        ga_FpT = T(TypeForms.CLASSES)
                        ga_FpT.Bytes = 4
                        ga_FpT.Bits = 0
                        ga_FpT.Form = TypeForms.CLASSES
                        ga_FpT.FType = False
                        ga_FpT.ClFields = None
                        ga_FpT.ClFstField = None
                        ga_FpT.ClFstMethod = None
                        ga_FpT.SuperClass = None

                        ga_lpN = N(NodeKind.IDENTNODE)
                        ga_lpN.Name = self.Ident
                        ga_lpN.Next = self.ForwCList
                        ga_lpN.Class = NameClass.TYPES
                        ga_lpN.Node = NodeKind.IDENTNODE
                        ga_lpN.IdType = ga_FpT
                        self.ForwCList = ga_lpN
                    # 10:
                else:
                    ga_FpT = ga_lpN.IdType

                return ga_FpT

            def ParameterList(
                pl_fsys: set[Symbol] | frozenset[Symbol],
                fSy: set[Symbol] | frozenset[Symbol],
            ) -> tuple[Optional[N], int]:
                """Parse formal value, VAR, UNIV, and procedural/functional parameters,
                assigning positive stack-frame offsets (Voff/PFOff) and negative local copy
                slots (FrameLLc) for non-set value parameters larger than 4 bytes."""
                assert pf_lpN is not None
                PARAMS: Optional[N] = None
                LastpN: Optional[N] = None
                lLc: int = 0
                FrameLLc: int = 0

                if self.Token not in (fSy | {Symbol.LPARENSY}):
                    self.Skip(23, pl_fsys | fSy | {Symbol.LPARENSY})
                if self.Token == Symbol.LPARENSY:
                    self.Scan()
                    if (
                        (self.Token != Symbol.IDENTSY)
                        and (self.Token != Symbol.VARSY)
                        and (self.Token != Symbol.FUNCTSY)
                        and (self.Token != Symbol.PROCSY)
                    ):
                        self.Skip(
                            23,
                            pl_fsys
                            | {
                                Symbol.IDENTSY,
                                Symbol.RPARENSY,
                                Symbol.VARSY,
                                Symbol.FUNCTSY,
                                Symbol.PROCSY,
                            },
                        )
                    while (
                        (self.Token == Symbol.IDENTSY)
                        or (self.Token == Symbol.VARSY)
                        or (self.Token == Symbol.FUNCTSY)
                        or (self.Token == Symbol.PROCSY)
                    ):
                        OldLastpN = LastpN
                        pl_lpT: Optional[T] = None
                        lUNIVflag = False
                        lKind = AccessKind.DRCT
                        if (self.Token == Symbol.FUNCTSY) or (self.Token == Symbol.PROCSY):
                            p_tok = self.Token
                            self.Scan()
                            lLpN = PFHead(
                                pl_fsys | {Symbol.RPARENSY, Symbol.SEMISY},
                                p_tok,
                                None,
                                True,
                                True,
                                None,
                            )
                            lLpN.PFdecl = PFkind.FORMAL
                            pl_lpT = lLpN.IdType
                            if LastpN is None:
                                PARAMS = lLpN
                            else:
                                LastpN.Next = lLpN
                            LastpN = lLpN
                        else:
                            if self.Token == Symbol.VARSY:
                                lKind = AccessKind.INDRCT
                                self.Scan()
                            else:
                                lKind = AccessKind.DRCT
                            pl_exit = False
                            while not pl_exit:
                                if self.Token == Symbol.IDENTSY:
                                    lLpN = N(NodeKind.IDENTNODE)
                                    lLpN.InRegister = -1
                                    lLpN.IdType = None
                                    lLpN.IsSELF = False
                                    lLpN.Name = self.Ident
                                    lLpN.Next = None
                                    lLpN.Node = NodeKind.IDENTNODE
                                    lLpN.Class = NameClass.VARS
                                    lLpN.Vkind = lKind
                                    lLpN.Vlev = self.Level
                                    if LastpN is None:
                                        PARAMS = lLpN
                                    else:
                                        LastpN.Next = lLpN
                                    self.EnterId(lLpN)
                                    LastpN = lLpN
                                    self.Scan()
                                else:
                                    self.Error(21)
                                if self.Token not in (
                                    pl_fsys | {Symbol.COMMASY, Symbol.COLONSY}
                                ):
                                    self.Skip(
                                        23,
                                        pl_fsys
                                        | {
                                            Symbol.COMMASY,
                                            Symbol.SEMISY,
                                            Symbol.RPARENSY,
                                            Symbol.COLONSY,
                                        },
                                    )
                                if self.Token == Symbol.COMMASY:
                                    self.Scan()
                                else:
                                    pl_exit = True
                            if self.Token == Symbol.COLONSY:
                                self.Scan()
                                if self.Token == Symbol.IDENTSY:
                                    if self.Ident == 'UNIV    ':
                                        lUNIVflag = True
                                        self.Scan()
                                    pl_lpT = GetAType()
                                    if lUNIVflag:
                                        lUNIVflag = self.Token == Symbol.IDENTSY
                                        if lUNIVflag:
                                            self.Scan()
                                    else:
                                        self.Scan()
                                else:
                                    self.Error(29)
                                if pl_lpT is not None:
                                    if (lKind == AccessKind.DRCT) and pl_lpT.FType:
                                        self.Error(119)
                                if self.Token not in {Symbol.SEMISY, Symbol.RPARENSY}:
                                    self.Skip(23, pl_fsys | {Symbol.SEMISY, Symbol.RPARENSY})
                            else:
                                self.Error(35)

                        if OldLastpN is None:
                            iter_pN = PARAMS
                        else:
                            iter_pN = OldLastpN.Next
                        while iter_pN is not None:
                            iter_pN.IdType = pl_lpT
                            LargeValue = False
                            if iter_pN.Class == NameClass.VARS:
                                iter_pN.UNIVflag = lUNIVflag
                                if lKind == AccessKind.INDRCT:
                                    lpTSize = 4
                                elif pl_lpT is not None:
                                    lpTSize = self.FullBytes(pl_lpT)
                                    if (lpTSize > 4) and (pl_lpT.Form != TypeForms.SETS):
                                        FrameLLc = i16(FrameLLc + lpTSize)
                                        LargeValue = True
                                        lpTSize = 4
                                else:
                                    lpTSize = 2
                            else:
                                lpTSize = 8
                                pl_lpT = None
                            lLc = i16(lLc - lpTSize)
                            if odd(lLc):
                                lLc = i16(lLc - 1)
                            if i16(lLc - 1) >= 0:
                                self.Error(310)
                                lLc = 0
                            if iter_pN.Class == NameClass.VARS:
                                if LargeValue:
                                    iter_pN.Voff = i16(-FrameLLc)
                                else:
                                    iter_pN.Voff = lLc
                                    if pl_lpT is not None:
                                        if (pl_lpT.Form == TypeForms.SETS) and (lpTSize == 1):
                                            iter_pN.Voff = i16(iter_pN.Voff + 1)
                            else:
                                iter_pN.PFOff = lLc
                            iter_pN = iter_pN.Next

                        if self.Token == Symbol.SEMISY:
                            self.Scan()
                            if self.Token not in (pl_fsys | {Symbol.IDENTSY, Symbol.VARSY}):
                                self.Skip(
                                    23,
                                    pl_fsys
                                    | {
                                        Symbol.IDENTSY,
                                        Symbol.RPARENSY,
                                        Symbol.PROCSY,
                                        Symbol.FUNCTSY,
                                        Symbol.VARSY,
                                    },
                                )

                    if not ForwFlag:
                        pf_lpN.Lc = FrameLLc
                    if self.Token == Symbol.RPARENSY:
                        self.Scan()
                        if self.Token not in (pl_fsys | fSy):
                            self.Skip(20, fSy | pl_fsys)
                    else:
                        self.Error(32)

                if pf_lpN.PFlev != 1:
                    lLc = i16(lLc - 4)
                lLc = i16(lLc - 8)
                iter_pN = PARAMS
                while iter_pN is not None:
                    if iter_pN.Class == NameClass.VARS:
                        if (iter_pN.Vkind == AccessKind.DRCT) and (iter_pN.IdType is not None):
                            LargeValue = (self.FullBytes(iter_pN.IdType) > 4) and (
                                iter_pN.IdType.Form != TypeForms.SETS
                            )
                        else:
                            LargeValue = False
                        if not LargeValue:
                            iter_pN.Voff = i16(iter_pN.Voff - lLc)
                    else:
                        iter_pN.PFOff = i16(iter_pN.PFOff - lLc)
                    iter_pN = iter_pN.Next
                pBytes = i16(-lLc)
                return PARAMS, pBytes

            # Body of PFHead
            ForwFlag = False
            if self.Top < MAXDISPLAY:
                self.Display[self.Top + 1].ProcBase = 0
            else:
                self.Error(303)

            if self.Token == Symbol.IDENTSY:
                HigherLevel = False
                if pf_ClasspT is not None:
                    if pf_ClasspT.ClFields is not None:
                        pf_lpN, HigherLevel = self.SearchClasses(pf_ClasspT, False)
                        if pf_lpN is not None:
                            if pf_lpN.Class == NameClass.PROC:
                                ForwFlag = (
                                    (pf_lpN.PFdeclKind == DeclKind.DECLARED)
                                    and (fToken == Symbol.PROCSY)
                                    and (HigherLevel or (pf_lpN.PFdecl == PFkind.FORWMETHDECL))
                                )
                                if not ForwFlag:
                                    self.Error(100)
                            elif pf_lpN.Class == NameClass.FUNC:
                                ForwFlag = (
                                    (pf_lpN.PFdeclKind == DeclKind.DECLARED)
                                    and (fToken == Symbol.FUNCTSY)
                                    and (HigherLevel or (pf_lpN.PFdecl == PFkind.FORWMETHDECL))
                                )
                                if not ForwFlag:
                                    self.Error(100)
                            else:
                                self.Error(153)
                            if HigherLevel:
                                if ForwFlag:
                                    pf_lpN = Override(pf_lpN)
                            elif ForwFlag and (pf_lpN.MethodNo != 0):
                                pf_lpN.RtnNo = self.LocProcNo
                                self.LocProcNo += 1

                if not ForwFlag:
                    pf_lpN = self.SearchLocal(self.Display[self.Top].NameTree)
                    if pf_lpN is not None:
                        if pf_lpN.Class == NameClass.PROC:
                            ForwFlag = (
                                (pf_lpN.PFdeclKind == DeclKind.DECLARED)
                                and (pf_lpN.PFdecl == PFkind.FORWDECL)
                                and (fToken == Symbol.PROCSY)
                            )
                        elif pf_lpN.Class == NameClass.FUNC:
                            ForwFlag = (
                                (pf_lpN.PFdeclKind == DeclKind.DECLARED)
                                and (pf_lpN.PFdecl == PFkind.FORWDECL)
                                and (fToken == Symbol.FUNCTSY)
                            )
                        else:
                            self.Error(153)

                if not ForwFlag:
                    pf_lpN = N(NodeKind.IDENTNODE)
                    if fToken == Symbol.PROCSY:
                        pf_lpN.Class = NameClass.PROC
                        pf_lpN.IdType = self.ProcPtr
                    else:
                        pf_lpN.Class = NameClass.FUNC
                        pf_lpN.IdType = None
                    pf_lpN.Node = NodeKind.IDENTNODE
                    pf_lpN.Name = self.Ident
                    pf_lpN.Next = None
                    pf_lpN.PFdeclKind = DeclKind.DECLARED
                    pf_lpN.PFdecl = PFkind.DECL
                    pf_lpN.Lc = 0
                    pf_lpN.ParmBytes = 0
                    pf_lpN.InlineCode = None
                    if self.Level > 1:
                        pf_lpN.PFlev = self.Level
                    else:
                        pf_lpN.PFlev = 1
                    if (self.Level > 1) or (self.InUnit and not self.InterFlag):
                        pf_lpN.RtnNo = self.LocProcNo
                        self.LocProcNo += 1
                    else:
                        pf_lpN.RtnNo = -1
                    if EnterIt:
                        self.EnterId(pf_lpN)

                self.Scan()
                if self.Token == Symbol.PERIODSY:
                    self.Error(23)
                    self.Scan()
                    if self.Token == Symbol.IDENTSY:
                        self.Scan()
            else:
                self.Error(29)
                pf_lpN = N(NodeKind.IDENTNODE)
                if fToken == Symbol.FUNCTSY:
                    assert self.uFctPtr is not None
                    pf_lpN.copy_from(self.uFctPtr)
                else:
                    assert self.uPrcPtr is not None
                    pf_lpN.copy_from(self.uPrcPtr)

            assert pf_lpN is not None

            OldTop = self.Top
            OldLevel = self.Level
            if self.Top < MAXDISPLAY:
                if self.Level <= 0:
                    self.Level = 2
                elif self.Level < MAXLEVEL:
                    self.Level += 1
                else:
                    self.Error(303)
                self.Top += 1
                self.Display[self.Top].NameTree = None
                self.Display[self.Top].Occur = Where.PARAMS
            else:
                self.Error(303)

            lSys: set[Symbol] = {Symbol.SEMISY}
            if FormalFlag:
                lSys = lSys | {Symbol.RPARENSY}
            if fToken == Symbol.FUNCTSY:
                lSys = lSys | {Symbol.COLONSY}

            pList, pBytes = ParameterList(pf_fsys, lSys)
            if ForwFlag:
                if pList is not None:
                    if not self.CompFormals(pf_lpN.PFargList, pList, True):
                        self.Error(116)
            else:
                pf_lpN.PFargList = pList
                pf_lpN.ParmBytes = pBytes

            if fToken == Symbol.FUNCTSY:
                if self.Token == Symbol.COLONSY:
                    self.Scan()
                    if self.Token == Symbol.IDENTSY:
                        FuncType = GetAType()
                        if ForwFlag:
                            if pf_lpN.IdType is not FuncType:
                                self.Error(117)
                        pf_lpN.IdType = FuncType
                        if pf_lpN.IdType is not None:
                            if pf_lpN.IdType.Form > TypeForms.POINTERS:
                                self.Error(118)
                                pf_lpN.IdType = None
                        self.Scan()
                    else:
                        self.Skip(29, pf_fsys | {Symbol.SEMISY})
                elif (not ForwFlag) or (pList is not None):
                    self.Error(120)

            if not FormalFlag:
                if self.Token == Symbol.SEMISY:
                    self.Scan()
                else:
                    self.Error(36)
            if self.Token not in pf_fsys:
                self.Skip(20, pf_fsys)
            self.Top = OldTop
            self.Level = OldLevel
            return pf_lpN

        def GetExitLabel() -> LabRec:
            """Create the implicit routine/program exit LabRec (LabelNo = 10000 + Level) targeted by EXIT."""
            lLab = LabRec()
            lLab.NextLabel = None
            lLab.LabelNo = 10000 + self.Level
            lLab.GlobRefNo = -1
            lLab.Defined = True
            return lLab

        def DclMasterTbl(mt_FpN: N) -> None:
            """Reserve space in unit global storage (ULc) for master method tables of all
            Clascal classes needing initialization ((ClassLevel + 3) * 4 bytes per class)
            and record each class's MethodOff."""
            assert self.NilClassPtr is not None
            CurClass = self.NilClassPtr.TotalOrder
            if mt_FpN.Ukind == UnitKind.SHARUNIT:
                if mt_FpN.ULc == 0:
                    mt_FpN.ULc = 4

            while CurClass is not None:
                if CurClass.NeedsInit:
                    mt_FpN.ULc = i16(mt_FpN.ULc + (CurClass.ClassLevel + 3) * 4)
                    CurClass.MethodOff = i16(-mt_FpN.ULc + 4)
                CurClass = CurClass.TotalOrder

        # Body of Declarations
        if fSymbol == Symbol.PROGRAMSY:
            self.Display[self.Top].NameTree = FpN
            self.Display[self.Top].Occur = Where.BLK
            self.Display[self.Top].Labels = None
            self.Display[self.Top].ExitLabel = GetExitLabel()
            self.Display[self.Top].RootLink = FpN

            if self.Token == Symbol.USESSY:
                self.Scan()
                UsesDecl(FSys)

            while True:
                ExitFlag = True
                self.ForwPList = None
                self.ForwCList = None
                if self.Token == Symbol.LABELSY:
                    self.Scan()
                    LabelDecl(FSys)
                    ExitFlag = False
                if self.Token == Symbol.CONSTSY:
                    self.Scan()
                    ConstDecl(FSys)
                    ExitFlag = False
                if self.Token == Symbol.TYPESY:
                    self.Scan()
                    TypeDecl(FSys)
                    ExitFlag = False
                if self.Token == Symbol.VARSY:
                    self.Scan()
                    VarDecl(FSys)
                    ExitFlag = False
                if ExitFlag:
                    break

        elif fSymbol in (Symbol.BEGINSY, Symbol.ENDSY):
            FpN = N(NodeKind.IDENTNODE)
            FpN.Node = NodeKind.IDENTNODE
            FpN.Class = NameClass.PROC
            FpN.PFdeclKind = DeclKind.DECLARED
            FpN.PFdecl = PFkind.METHDECL
            FpN.IdType = None
            FpN.Next = None
            FpN.PFlev = 1
            FpN.RtnNo = self.LocProcNo
            self.LocProcNo += 1
            FpN.PFargList = None
            FpN.ParmBytes = 0
            FpN.Lc = 0
            self.NextCrNbr += 1
            n_num = self.NextCrNbr
            cr_name = '%_CR0000'
            for idx in range(5, 9):
                cr_name = pset_ch(cr_name, idx, chr(ord('0') + pmod(n_num, 10)))
                n_num = pdiv(n_num, 10)
            FpN.Name = cr_name

            HeapMark = 0
            self.Level = 2
            if self.Top < MAXDISPLAY:
                self.Top += 1
                self.Display[self.Top].NameTree = None
                self.Display[self.Top].Occur = Where.BLK
                self.Display[self.Top].Labels = None
                self.Display[self.Top].ExitLabel = GetExitLabel()
                self.Display[self.Top].RootLink = FpN
            else:
                self.Error(303)

        elif fSymbol in (Symbol.PROCSY, Symbol.FUNCTSY):
            FpN = PFHead(FSys, fSymbol, FpN, False, True, ClasspT)
            HeapMark = 0
            if self.Level <= 0:
                self.Level = 2
            elif self.Level < MAXLEVEL:
                self.Level += 1
            else:
                self.Error(303)
            if self.Top < MAXDISPLAY:
                self.Top += 1
                self.Display[self.Top].NameTree = FpN.PFargList
                self.Display[self.Top].Occur = Where.BLK
                self.Display[self.Top].Labels = None
                self.Display[self.Top].ExitLabel = GetExitLabel()
                self.Display[self.Top].RootLink = FpN
            else:
                self.Error(303)

            if FpN.PFdecl == PFkind.FORWMETHDECL:
                # Install SELF
                self_pN = N(NodeKind.IDENTNODE)
                self_pN.InRegister = -1
                self_pN.IdType = ClasspT
                self_pN.Name = 'SELF    '
                self_pN.Next = None
                self_pN.Node = NodeKind.IDENTNODE
                self_pN.Class = NameClass.VARS
                self_pN.Vkind = AccessKind.DRCT
                self_pN.IsSELF = True
                self_pN.UNIVflag = False
                self_pN.Vlev = self.Level
                if FpN.Name == 'CREATE  ':
                    self_pN.Voff = FpN.ParmBytes
                else:
                    self_pN.Voff = 8
                self.EnterId(self_pN)

                # Install SUPERSELF
                sup_pN = N(NodeKind.IDENTNODE)
                assert ClasspT is not None
                sup_pN.IdType = ClasspT.SuperClass
                sup_pN.Name = 'SUPERSEL'
                sup_pN.Next = None
                sup_pN.Node = NodeKind.IDENTNODE
                sup_pN.Class = NameClass.TYPES
                self.EnterId(sup_pN)

                if FpN.Class == NameClass.FUNC:
                    # Install return result
                    ret_pN = N(NodeKind.IDENTNODE)
                    ret_pN.InRegister = -2
                    ret_pN.IdType = FpN.IdType
                    ret_pN.Name = FpN.Name
                    ret_pN.Next = None
                    ret_pN.Node = NodeKind.IDENTNODE
                    ret_pN.Class = NameClass.VARS
                    ret_pN.Vkind = AccessKind.DRCT
                    ret_pN.IsSELF = False
                    ret_pN.UNIVflag = False
                    ret_pN.Vlev = self.Level
                    ret_pN.Voff = FpN.ParmBytes
                    self.EnterId(ret_pN)

            while True:
                ExitFlag = True
                self.ForwCList = None
                self.ForwPList = None
                if self.Token == Symbol.LABELSY:
                    self.Scan()
                    LabelDecl(FSys)
                    ExitFlag = False
                if self.Token == Symbol.CONSTSY:
                    self.Scan()
                    ConstDecl(FSys)
                    ExitFlag = False
                if self.Token == Symbol.TYPESY:
                    self.Scan()
                    TypeDecl(FSys)
                    ExitFlag = False
                if self.Token == Symbol.VARSY:
                    self.Scan()
                    VarDecl(FSys)
                    ExitFlag = False
                if ExitFlag:
                    break

        elif fSymbol == Symbol.UNITSY:
            self.InterFlag = True
            self.Display[self.Top].NameTree = FpN
            self.Display[self.Top].Occur = Where.BLK
            self.Display[self.Top].Labels = None
            self.Display[self.Top].ExitLabel = None
            self.Display[self.Top].RootLink = None

            if self.Token == Symbol.INTRINSY:
                self.Scan()
                IntriDecl()
                self.InIU = True
            FSys = FSys | {Symbol.IMPLESY}

            if self.Token == Symbol.USESSY:
                self.Scan()
                UsesDecl(FSys)

            while True:
                ExitFlag = True
                self.ForwCList = None
                self.ForwPList = None
                if self.Token == Symbol.CONSTSY:
                    self.Scan()
                    ConstDecl(FSys)
                    ExitFlag = False
                if self.Token == Symbol.TYPESY:
                    self.Scan()
                    TypeDecl(FSys)
                    ExitFlag = False
                if self.Token == Symbol.VARSY:
                    self.Scan()
                    VarDecl(FSys)
                    ExitFlag = False
                if (self.Token == Symbol.FUNCTSY) or (self.Token == Symbol.PROCSY):
                    lToken = self.Token
                    self.Scan()
                    lpN = PFHead(
                        FSys | {Symbol.IDENTSY, Symbol.IMPLESY},
                        lToken,
                        None,
                        False,
                        True,
                        None,
                    )
                    has_body, HeapMark = self.HasBody(
                        FSys | {Symbol.IMPLESY}, lpN, HeapMark
                    )
                    if has_body:
                        lpN.PFdecl = PFkind.FORWDECL
                        self.Forwcount += 1
                    ExitFlag = False
                if ExitFlag:
                    break

            self.LastUBlock = (
                self.OpenFileStack[self.TopOfOpenFileStack].LastRelBlkRead
                + 2 * pdiv(self.InbufP, 1024)
            )
            self.LastUByte = pmod(self.InbufP, 1024)
            self.InterFlag = False
            FSys = FSys - {Symbol.IMPLESY}

            if self.ClassesToInit:
                assert FpN is not None
                DclMasterTbl(FpN)

            if self.Token == Symbol.IMPLESY:
                self.Scan()
            else:
                self.Skip(52, FSys)

            while True:
                ExitFlag = True
                self.ForwCList = None
                self.ForwPList = None
                if self.Token == Symbol.CONSTSY:
                    self.Scan()
                    ConstDecl(FSys)
                    ExitFlag = False
                if self.Token == Symbol.TYPESY:
                    self.Scan()
                    TypeDecl(FSys)
                    ExitFlag = False
                if self.Token == Symbol.VARSY:
                    self.Scan()
                    VarDecl(FSys)
                    ExitFlag = False
                if ExitFlag:
                    break

        elif fSymbol == Symbol.USESSY:
            if self.Token == Symbol.INTRINSY:
                self.Scan()
                IntriDecl()
            else:
                if self.InIU:
                    self.Error(54)
                if self.Token == Symbol.INTERSY:
                    self.Scan()
                else:
                    self.Skip(53, FSys)

            if self.Token == Symbol.USESSY:
                self.Scan()
                UsesDecl(FSys)

            while True:
                ExitFlag = True
                self.ForwCList = None
                self.ForwPList = None
                self.InUses = True
                if self.Token == Symbol.CONSTSY:
                    self.Scan()
                    ConstDecl(FSys)
                    ExitFlag = False
                if self.Token == Symbol.TYPESY:
                    self.Scan()
                    TypeDecl(FSys)
                    ExitFlag = False
                if self.Token == Symbol.VARSY:
                    self.Scan()
                    VarDecl(FSys)
                    ExitFlag = False
                if (self.Token == Symbol.FUNCTSY) or (self.Token == Symbol.PROCSY):
                    lToken = self.Token
                    self.Scan()
                    lpN = PFHead(
                        FSys | {Symbol.IDENTSY, Symbol.IMPLESY},
                        lToken,
                        None,
                        False,
                        True,
                        None,
                    )
                    has_body, HeapMark = self.HasBody(
                        FSys | {Symbol.IMPLESY}, lpN, HeapMark
                    )
                    if has_body:
                        if self.RodFlag:
                            lpN.PFdecl = PFkind.FORWDECL
                        else:
                            lpN.PFdecl = PFkind.EXTDECL
                    ExitFlag = False
                if ExitFlag:
                    break

            if self.Token != Symbol.IMPLESY:
                self.Error(52)
            self.InUses = False
            if not self.LinePrinted:
                self.CurLine = self.CurLine[: max(0, self.pCurLine)]
                TempStr = self.rt.SUUpStr(self.CurLine)
                pos_idx = ppos('IMPLEMEN', TempStr)
                if pos_idx > 0:
                    self.CurLine = self.rt.SUTrimBlanks(self.CurLine[: pos_idx - 1])
                    self.pCurLine = len(self.CurLine)
                    self.LinePrinted = self.pCurLine == 0
            self.EolSource = True
            self.InbufP = 0
            self.Inbuf[0] = 32  # ' '
            self.InbufLastValidByte = 1
            self.NextCh()

        elif fSymbol in (Symbol.LABELSY, Symbol.CONSTSY, Symbol.TYPESY, Symbol.VARSY):
            while True:
                ExitFlag = True
                self.ForwCList = None
                self.ForwPList = None
                if self.Token == Symbol.LABELSY:
                    self.Scan()
                    LabelDecl(FSys)
                    ExitFlag = False
                if self.Token == Symbol.CONSTSY:
                    self.Scan()
                    ConstDecl(FSys)
                    ExitFlag = False
                if self.Token == Symbol.TYPESY:
                    self.Scan()
                    TypeDecl(FSys)
                    ExitFlag = False
                if self.Token == Symbol.VARSY:
                    self.Scan()
                    VarDecl(FSys)
                    ExitFlag = False
                if ExitFlag:
                    break

        return FpN, HeapMark
