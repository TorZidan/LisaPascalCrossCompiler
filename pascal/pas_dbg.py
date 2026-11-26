"""Debug symbol and AST dump mixin for the Lisa Pascal Front End."""

from __future__ import annotations

import struct
import sys
from typing import Optional

from frontend_base import (
    DeclKind,
    N,
    NameClass,
    NodeKind,
    Stmt,
    StmtTypes,
    T,
    TypeForms,
)
from lisalib import (
    alfa8,
    u16,
    u32,
)


def _ord_ptr(obj: object) -> int:
    """Return a 31-bit non-negative pointer/marker integer for debug output."""
    if obj is None:
        return 0
    if isinstance(obj, int):
        return obj & 0x7FFFFFFF
    return id(obj) & 0x7FFFFFFF


class DbgMixin:
    """Implements debug symbol and AST output routines."""

    def DbgOut(self, a: int) -> None:
        """Append one byte to the 512-byte binary ``.DBG`` buffer, flushing full blocks to ``DebugFile``."""
        if self.DebugOpen:
            if self.DbgIdx <= 511:
                self.DbgBuf[self.DbgIdx] = a & 0xFF
                self.DbgIdx += 1
            else:
                if self.rt.block_write(self.DebugFile, self.DbgBuf, 1, self.DbgBlkNum) != 1:
                    self.Error(420)
                self.DbgBuf[0] = a & 0xFF
                self.DbgIdx = 1
                self.DbgBlkNum += 1

    def DbgOut2(self, a: int) -> None:
        """Write a 16-bit integer to the binary ``.DBG`` file in big-endian byte order."""
        u = u16(a)
        self.DbgOut((u >> 8) & 0xFF)
        self.DbgOut(u & 0xFF)

    def DbgOutN(self, l: int, N: int) -> None:
        """Write the low-order ``N`` big-endian bytes (zero-padded if ``N > 4``) of 32-bit integer ``l``."""
        BytesInParam = 4
        b = struct.pack('>I', u32(l))
        if N > BytesInParam:
            for _ in range(BytesInParam, N):
                self.DbgOut(0)
            N = BytesInParam
        if N > 0:
            for byte in b[BytesInParam - N:]:
                self.DbgOut(byte)

    def DumpFatherPointer(self, FatherP: Optional[N], SonP: Optional[N]) -> None:
        """Emit a ``0xC4`` parent-link record binding nested routine ``SonP`` to enclosing routine ``FatherP``."""
        if FatherP is not None:
            if FatherP.Class in (NameClass.PROC, NameClass.FUNC):
                self.DbgOut(0xC4)
                self.DbgOutN(1 + 3 + 8 + 8 + 8 + 4, 3)
                son_name = alfa8(SonP.Name) if SonP is not None else '        '
                seg_name = alfa8(self.SegName)
                father_name = alfa8(FatherP.Name)
                for i in range(8):
                    self.DbgOut(ord(son_name[i]))
                for i in range(8):
                    self.DbgOut(ord(seg_name[i]))
                for i in range(8):
                    self.DbgOut(ord(father_name[i]))
                self.DbgOutN(_ord_ptr(FatherP), 4)

    def DumpSyms(
        self,
        ProcBase: int,
        NameTree: Optional[N],
        StmtP: Optional[Stmt],
        NodeP: Optional[N],
    ) -> None:
        """Dump formatted symbols, types, and statements to ``$D`` text output and ``0xC0`` records to ``.DBG``."""
        Max0: int = 0
        Min0: int = 0
        Max1: int = 0
        Marker: bool = False

        def MarkTypes(nP: Optional[N]) -> None:
            """Set ``Marked = Marker`` on all type descriptors reachable from identifier BST ``nP``."""

            def Mark(tP: Optional[T]) -> None:
                """Recursively mark ``tP`` and its non-pointer component types while tracking address bounds."""
                nonlocal Max0, Min0, Max1
                if tP is not None:
                    tp_ord = _ord_ptr(tP)
                    if Marker:
                        if Max0 < tp_ord:
                            Max0 = tp_ord
                        if Min0 > tp_ord:
                            Min0 = tp_ord
                    else:
                        if Max1 < tp_ord:
                            Max1 = tp_ord
                    tP.Marked = Marker
                    if tP.Form == TypeForms.SCALAR:
                        pass
                    elif tP.Form == TypeForms.SUBRANGE:
                        Mark(tP.RangeOf)
                    elif tP.Form == TypeForms.POINTERS:
                        # PointerTo will be picked up later
                        pass
                    elif tP.Form == TypeForms.SETS:
                        Mark(tP.SetOf)
                    elif tP.Form == TypeForms.ARRAYS:
                        Mark(tP.ArrayOf)
                        Mark(tP.IndexedBy)
                    elif tP.Form == TypeForms.RECORDS:
                        Mark(tP.VarPart)
                    elif tP.Form == TypeForms.TAGFIELD:
                        Mark(tP.Variants)
                    elif tP.Form == TypeForms.VARIANT:
                        Mark(tP.NextVar)
                        Mark(tP.SubVar)
                    elif tP.Form == TypeForms.FILES:
                        Mark(tP.FileOf)

            if nP is not None:
                MarkTypes(nP.Llink)
                Mark(nP.IdType)
                MarkTypes(nP.Rlink)

        def WriteNode(PNode: Optional[N], Indent: int, DoIndent: bool) -> None:
            """Format an ``N`` identifier or expression AST subtree to the ``$D`` text debug log."""
            if DoIndent:
                self.Debugging.write(' ' * max(0, Indent))
            self.Debugging.write(f'{_ord_ptr(PNode):9d}')
            if PNode is None:
                if not DoIndent:
                    self.Debugging.writeln()
            else:
                if PNode.Node == NodeKind.IDENTNODE:
                    self.Debugging.write(
                        f' Id: {alfa8(PNode.Name):>9s}'
                        f'{_ord_ptr(PNode.Llink):9d}'
                        f'{_ord_ptr(PNode.Rlink):9d}'
                        f'{_ord_ptr(PNode.Next):9d}'
                        f' type={_ord_ptr(PNode.IdType):9d}'
                    )
                    if PNode.Class == NameClass.CONSTS:
                        self.Debugging.write(f' Const {PNode.ValueOf.Ivalu:6d}')
                    elif PNode.Class == NameClass.TYPES:
                        self.Debugging.write(' Type  ')
                    elif PNode.Class == NameClass.VARS:
                        self.Debugging.write(
                            f' Var   {int(PNode.Vkind):6d}{PNode.Vlev:6d}{PNode.Voff:6d}'
                        )
                    elif PNode.Class == NameClass.FIELD:
                        self.Debugging.write(
                            f' Field {PNode.FOff:6d}'
                            f'{1 if PNode.PckdField else 0:2d}'
                            f'{PNode.BitOff:3d}'
                        )
                    elif PNode.Class in (NameClass.PROC, NameClass.FUNC):
                        if PNode.Class == NameClass.PROC:
                            self.Debugging.write(' Proc  ')
                        else:
                            self.Debugging.write(' Func  ')
                    elif PNode.Class == NameClass.UNITS:
                        self.Debugging.write(f' Unit  {PNode.Ulev:6d}{PNode.ULc:6d}')
                    self.Debugging.writeln()
                elif PNode.Node == NodeKind.REGISTER:
                    self.Debugging.writeln(
                        f' Register: {PNode.Reg:4d} load={PNode.Load:3d}'
                        f' size={PNode.LoadSize:6d}{_ord_ptr(PNode.LoadExpr):9d}'
                    )
                    if PNode.LoadExpr is not None:
                        WriteNode(PNode.LoadExpr, Indent, True)
                elif PNode.Node == NodeKind.UNNODE:
                    self.Debugging.writeln(
                        f' Una: op={PNode.UnOp:3d} subop={PNode.UnSubOp:6d}'
                        f'{_ord_ptr(PNode.UnArg):9d}'
                    )
                    WriteNode(PNode.UnArg, Indent, True)
                elif PNode.Node == NodeKind.BINNODE:
                    self.Debugging.writeln(
                        f' Bin: op={PNode.BinOp:3d} subop={PNode.BinSubOp:6d}'
                        f'{_ord_ptr(PNode.LeftArg):9d}{_ord_ptr(PNode.RightArg):9d}'
                    )
                    if PNode.BinOp != 46:  # RangeCheck
                        self.Debugging.write(' ' * max(0, Indent + 2) + 'Leftarg: ')
                        WriteNode(PNode.LeftArg, Indent + 2, False)
                    self.Debugging.write(' ' * max(0, Indent + 2) + 'Rightarg: ')
                    WriteNode(PNode.RightArg, Indent + 2, False)
                elif PNode.Node == NodeKind.TRINODE:
                    self.Debugging.writeln(
                        f' Tri: op={PNode.TriOp:3d}'
                        f'{_ord_ptr(PNode.Tri1):9d}'
                        f'{_ord_ptr(PNode.Tri2):9d}'
                        f'{_ord_ptr(PNode.TriSuper):9d}'
                        f'{_ord_ptr(PNode.TripN):9d}'
                    )
                    self.Debugging.write(' ' * max(0, Indent + 2) + 'Tri1: ')
                    WriteNode(PNode.Tri1, Indent + 2, False)
                    self.Debugging.write(' ' * max(0, Indent + 2) + 'Tri2: ')
                    WriteNode(PNode.Tri2, Indent + 2, False)
                    if PNode.TriOp != 16:  # index
                        self.Debugging.write(' ' * max(0, Indent + 2) + 'Tripn: ')
                        WriteNode(PNode.TripN, Indent + 2, True)
                elif PNode.Node == NodeKind.CSTNODE:
                    self.Debugging.writeln(
                        f' Cst: {_ord_ptr(PNode.CstType):9d}{PNode.CstValu.Ivalu:6d}'
                    )
                elif PNode.Node == NodeKind.CSE:
                    self.Debugging.writeln(
                        f' CSE: {_ord_ptr(PNode.CSEpN):9d}{PNode.CSEIndex:6d}'
                    )
                    WriteNode(PNode.CSEpN, Indent + 2, False)
                elif PNode.Node == NodeKind.ASGNNODE:
                    self.Debugging.writeln(
                        f' Asgnnode: op={PNode.AsgnOp:3d}'
                        f'{_ord_ptr(PNode.AsgnVar):9d}'
                        f'{_ord_ptr(PNode.AsgnExpr):9d}'
                        f'{_ord_ptr(PNode.AsgnpN):9d}'
                    )
                    self.Debugging.write(' ' * max(0, Indent + 2) + 'AsgnVar: ')
                    WriteNode(PNode.AsgnVar, Indent + 2, False)
                    self.Debugging.write(' ' * max(0, Indent + 2) + 'AsgnExpr: ')
                    WriteNode(PNode.AsgnExpr, Indent + 2, False)
                    self.Debugging.write(' ' * max(0, Indent + 2) + 'AsgnpN: ')
                    WriteNode(PNode.AsgnpN, Indent + 2, True)

        def WriteType(FTypeP: T) -> None:
            """Format a single ``T`` type descriptor and its variant fields to the ``$D`` text debug log."""
            self.Debugging.write(f'Type - {_ord_ptr(FTypeP):6d}')
            self.Debugging.write(
                f'{1 if FTypeP.Marked else 0:2d}'
                f'{FTypeP.Bytes:6d}'
                f'{FTypeP.Bits:2d}'
                f'{1 if FTypeP.FType else 0:2d}'
            )
            if FTypeP.Form == TypeForms.SCALAR:
                self.Debugging.write(' Scalar')
                if FTypeP.ScalKind == DeclKind.STANDARD:
                    self.Debugging.write(' Standard')
                elif FTypeP.ScalKind == DeclKind.DECLARED:
                    self.Debugging.write(f' Declared{_ord_ptr(FTypeP.MaxConst):6d}')
            elif FTypeP.Form == TypeForms.SUBRANGE:
                self.Debugging.write(
                    f' Subrange{_ord_ptr(FTypeP.RangeOf):6d}{FTypeP.Min:6d}{FTypeP.Max:6d}'
                )
            elif FTypeP.Form == TypeForms.POINTERS:
                self.Debugging.write(f' Pointer{_ord_ptr(FTypeP.PointerTo):6d}')
            elif FTypeP.Form == TypeForms.SETS:
                self.Debugging.write(f' Set{_ord_ptr(FTypeP.SetOf):6d}')
            elif FTypeP.Form == TypeForms.ARRAYS:
                self.Debugging.write(
                    f' Array{_ord_ptr(FTypeP.IndexedBy):6d}'
                    f'{_ord_ptr(FTypeP.ArrayOf):6d}'
                    f'{1 if FTypeP.PckdArr else 0:2d}'
                    f'{1 if FTypeP.BitPackd else 0:2d}'
                    f'{int(FTypeP.BitsPerEl):2d}'
                )
            elif FTypeP.Form == TypeForms.RECORDS:
                self.Debugging.write(
                    f' Record{1 if FTypeP.PckdRec else 0:2d}'
                    f'{_ord_ptr(FTypeP.Fields):6d}'
                    f'{_ord_ptr(FTypeP.FstField):6d}'
                    f'{_ord_ptr(FTypeP.VarPart):6d}'
                )
            elif FTypeP.Form == TypeForms.TAGFIELD:
                self.Debugging.write(
                    f' Tag{_ord_ptr(FTypeP.TagName):6d}{_ord_ptr(FTypeP.Variants):6d}'
                )
            elif FTypeP.Form == TypeForms.VARIANT:
                self.Debugging.write(
                    f' Variant{_ord_ptr(FTypeP.VarFldLst):6d}'
                    f'{_ord_ptr(FTypeP.NextVar):6d}'
                    f'{_ord_ptr(FTypeP.SubVar):6d}'
                    f'{_ord_ptr(FTypeP.VarValus):6d}'
                )
            elif FTypeP.Form == TypeForms.FILES:
                self.Debugging.write(
                    f' File{1 if FTypeP.PckdFile else 0:2d}{_ord_ptr(FTypeP.FileOf):6d}'
                )
            elif FTypeP.Form == TypeForms.STRINGS:
                self.Debugging.write(f' String{FTypeP.StringLen:6d}')
            elif FTypeP.Form == TypeForms.SCONST:
                self.Debugging.write(f' StringConst{FTypeP.StringLen:6d}')
            self.Debugging.writeln()

        def DumpNodes(nP: Optional[N]) -> None:
            """Traverse identifier BST ``nP`` and print each ``IDENTNODE`` along with newly marked ``T`` types."""

            def DumpTypes(tP: Optional[T]) -> None:
                """Print ``tP`` once if marked, clear ``Marked``, and recursively dump its component types and fields."""
                if tP is not None and tP.Marked:
                    tP.Marked = False
                    WriteType(tP)
                    if tP.Form == TypeForms.SCALAR:
                        pass
                    elif tP.Form == TypeForms.SUBRANGE:
                        DumpTypes(tP.RangeOf)
                    elif tP.Form == TypeForms.POINTERS:
                        DumpTypes(tP.PointerTo)
                    elif tP.Form == TypeForms.SETS:
                        DumpTypes(tP.SetOf)
                    elif tP.Form == TypeForms.ARRAYS:
                        DumpTypes(tP.IndexedBy)
                        DumpTypes(tP.ArrayOf)
                    elif tP.Form == TypeForms.RECORDS:
                        DumpTypes(tP.VarPart)
                        DumpNodes(tP.Fields)
                    elif tP.Form == TypeForms.TAGFIELD:
                        DumpTypes(tP.Variants)
                    elif tP.Form == TypeForms.VARIANT:
                        DumpTypes(tP.NextVar)
                        DumpTypes(tP.SubVar)
                    elif tP.Form == TypeForms.FILES:
                        DumpTypes(tP.FileOf)
                    elif tP.Form == TypeForms.STRINGS:
                        pass
                    elif tP.Form == TypeForms.SCONST:
                        pass

            if nP is not None:
                if nP.Node == NodeKind.IDENTNODE:
                    DumpNodes(nP.Rlink)
                WriteNode(nP, 0, False)
                DumpTypes(nP.IdType)
                if nP.Node == NodeKind.IDENTNODE:
                    DumpNodes(nP.Llink)

        def DumpStmt(fStmt: Optional[Stmt], Indent: int) -> None:
            """Recursively pretty-print a statement AST chain and its operand nodes to ``Debugging``."""

            def NodeDescr(fNode: Optional[N], Name: str) -> None:
                """Write an indented operand label ``Name`` followed by formatted AST node ``fNode``."""
                self.Debugging.write(' ' * max(0, Indent + 4) + Name)
                WriteNode(fNode, Indent + 4 + len(Name), False)

            while fStmt is not None:
                self.Debugging.write(' ' * max(0, Indent) + f'{fStmt.StmtNumb:3d}')
                if fStmt.StmtOp == StmtTypes.BEGINST:
                    self.Debugging.writeln(' BEGIN')
                    DumpStmt(fStmt.SubSt, Indent + 2)
                elif fStmt.StmtOp in (StmtTypes.METHODCALL, StmtTypes.ASSIGNST):
                    flip_str = 'TRUE' if fStmt.Flippable else 'FALSE'
                    self.Debugging.writeln(
                        f' ASSIGN {fStmt.AssOp:4d} flipbl={flip_str}{fStmt.AssSubOp:4d}'
                    )
                    NodeDescr(fStmt.AssVar, 'assvar')
                    NodeDescr(fStmt.AssExpr, 'assexpr')
                elif fStmt.StmtOp in (StmtTypes.FORTOST, StmtTypes.FORDOWNST):
                    self.Debugging.writeln(f' FOR{fStmt.ForSize:4d}')
                    NodeDescr(fStmt.ForVar, 'forvar')
                    NodeDescr(fStmt.ForInit, 'forinit')
                    NodeDescr(fStmt.ForLimit, 'forlimit')
                    DumpStmt(fStmt.ForSt, Indent + 2)
                elif fStmt.StmtOp == StmtTypes.IFST:
                    self.Debugging.writeln(' IF')
                    NodeDescr(fStmt.IfExpr, 'ifexpr')
                    self.Debugging.write(' ' * max(0, Indent + 4) + 'THEN')
                    DumpStmt(fStmt.ThenSt, Indent + 2)
                    if fStmt.ElseSt is not None:
                        self.Debugging.write(' ' * max(0, Indent + 4) + 'ELSE')
                        DumpStmt(fStmt.ElseSt, Indent + 2)
                elif fStmt.StmtOp == StmtTypes.WITHST:
                    self.Debugging.writeln(' WITH')
                    NodeDescr(fStmt.WithVar, 'withvar')
                    DumpStmt(fStmt.WithBody, Indent + 2)
                elif fStmt.StmtOp in (StmtTypes.REPST, StmtTypes.WHILEST):
                    self.Debugging.writeln(' REP/WHILE')
                    NodeDescr(fStmt.CondExpr, 'condexpr')
                    DumpStmt(fStmt.LoopStmt, Indent + 2)
                elif fStmt.StmtOp == StmtTypes.CALLST:
                    self.Debugging.writeln(' CALL')
                    NodeDescr(fStmt.ProcpN, 'procpn')
                    NodeDescr(fStmt.pArgList, 'parglist')
                elif fStmt.StmtOp == StmtTypes.GOTOST:
                    self.Debugging.writeln(
                        f' GOTO{_ord_ptr(fStmt.GotoLab):9d} lev={fStmt.LabLev:8d}'
                    )
                elif fStmt.StmtOp == StmtTypes.CASEST:
                    self.Debugging.writeln(' CASE')
                    NodeDescr(fStmt.CaseExpr, 'caseexpr')
                    DumpStmt(fStmt.CStmtList, Indent + 2)
                    self.Debugging.write(' ' * max(0, Indent + 4) + 'OTHERWISE')
                    DumpStmt(fStmt.OtherStmt, Indent + 2)
                elif fStmt.StmtOp == StmtTypes.CSTMTST:
                    self.Debugging.write(' CSTMTST, casevals = ')
                    cnt = 6
                    lIntP = fStmt.CaseVals
                    while lIntP is not None:
                        cnt += 1
                        if cnt > 10:
                            sys.stdout.write('\n')
                            cnt = 1
                        self.Debugging.write(f'{lIntP.IntVal:6d}')
                        lIntP = lIntP.NextInt
                    self.Debugging.writeln()
                    DumpStmt(fStmt.ThisCase, Indent + 2)
                elif fStmt.StmtOp == StmtTypes.LABEDST:
                    self.Debugging.writeln(f' LABEL{_ord_ptr(fStmt.StLab):9d}')
                    DumpStmt(fStmt.LabStmt, Indent + 2)
                elif fStmt.StmtOp == StmtTypes.TEMPST:
                    self.Debugging.writeln(
                        f' TEMPSTMT{fStmt.TempCSEregs.iMask:9d}{fStmt.TempLevel:6d}'
                    )
                elif fStmt.StmtOp == StmtTypes.NULLST:
                    self.Debugging.writeln(' NULLST')
                fStmt = fStmt.NextStmt

        GlobalStuff = (self.Top == 1) and (NodeP is not None)
        HeaderSize = 1 + 3 + 8 + 8 + 4 + 4 + 4 + 4 + 4

        if self.DebugDebug:
            if NodeP is not None:
                self.Debugging.writeln(
                    f"Symbols for '{alfa8(NodeP.Name)}' segment '{alfa8(self.SegName)}'"
                )
            else:
                self.Debugging.writeln(f'Symbols for level {self.Top}')
            Max0 = 0
            Min0 = _ord_ptr(ProcBase)
            Max1 = 0
            Marker = True
            MarkTypes(NameTree)
            Marker = False
            if self.Top > 0:
                for lLev in range(self.Top - 1, -1, -1):
                    MarkTypes(self.Display[lLev].NameTree)
            DumpNodes(NameTree)
            DumpStmt(StmtP, 0)

        HeapBase = _ord_ptr(ProcBase)
        if self.DebugDebug:
            self.Debugging.writeln(
                f'HeapBase {HeapBase:6d}, NameTree {_ord_ptr(NameTree)}'
                f', StmtP {_ord_ptr(StmtP):6d}, NodeP {_ord_ptr(NodeP):6d}'
            )
        if _ord_ptr(NameTree) > 0:
            HeapBase = min(HeapBase, _ord_ptr(NameTree))
        if _ord_ptr(StmtP) > 0:
            HeapBase = min(HeapBase, _ord_ptr(StmtP))
        if _ord_ptr(NodeP) > 0:
            HeapBase = min(HeapBase, _ord_ptr(NodeP))

        # Python AST/symbol objects are not raw 68000 heap bytes, so HeapSize = 0
        HeapTop = HeapBase
        HoleBase = HeapBase
        HoleTop = HeapBase
        HeapSize = 0

        UsesSize = 0
        if GlobalStuff:
            UsesList = self.UnitList
            while UsesList is not None:
                if UsesList.Ulev != -1:
                    UsesSize += 1
                UsesList = UsesList.Next
            if UsesSize > 0:
                HeaderSize += 4 + 4
        UsesSize = UsesSize * (4 + 4 + 8)

        if self.DebugDebug:
            self.Debugging.writeln(
                f'level {self.Top:2d}, RecSize {HeaderSize + UsesSize + HeapSize:6d}'
                f', HeapBase {HeapBase:6d}, NameTree {_ord_ptr(NameTree):6d}'
                f', HeapTop {HeapTop:6d}'
            )

        if self.DebugOpen:
            self.DbgOut(0xC0)
            self.DbgOutN(HeaderSize + UsesSize + HeapSize, 3)

            if NodeP is not None:
                node_name = alfa8(NodeP.Name)
                for i in range(8):
                    self.DbgOut(ord(node_name[i]))
            else:
                for _ in range(8):
                    self.DbgOut(ord(' '))
            seg_name = alfa8(self.SegName)
            for i in range(8):
                self.DbgOut(ord(seg_name[i]))

            self.DbgOutN(HeapBase, 4)
            self.DbgOutN(_ord_ptr(NameTree), 4)
            self.DbgOutN(_ord_ptr(StmtP), 4)
            self.DbgOutN(_ord_ptr(NodeP), 4)

            self.DbgOutN(UsesSize, 4)
            if UsesSize > 0:
                self.DbgOutN(HoleBase, 4)
                self.DbgOutN(HoleTop, 4)
                UsesList = self.UnitList
                while UsesList is not None:
                    if UsesList.Ulev != -1:
                        self.DbgOutN(_ord_ptr(UsesList), 4)
                        self.DbgOutN(_ord_ptr(UsesList.Utop), 4)
                        u_name = alfa8(UsesList.Name)
                        for i in range(8):
                            self.DbgOut(ord(u_name[i]))
                    UsesList = UsesList.Next

        if self.DebugDebug:
            self.Debugging.writeln(f'DumpSyms, dumped {HeapSize} bytes')

        if self.DebugOpen and self.Top > 0:
            self.DumpFatherPointer(self.Display[self.Top - 1].RootLink, NodeP)
