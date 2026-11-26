"""Optimizer and global register binder mixin for the Lisa Pascal Front End."""

from __future__ import annotations

from typing import Optional

from lisalib import odd
from frontend_base import (
    A1st,
    A6,
    AccessKind,
    Anth,
    D1st,
    DeclKind,
    Dnth,
    LONG,
    MAXDISPLAY,
    MAXREFS,
    N,
    NameClass,
    NodeKind,
    PFkind,
    RegContents,
    SLinkOffset,
    Stmt,
    StmtTypes,
    TypeForms,
    UnitKind,
)



def with_vkind(pVar: N) -> int:
    """Vkind of the identifier of a WITH variable, as the original reads it.
    In the original's variant record, Vkind (the first field of the VARS
    variant) is at the place of PFdeclKind (the first field of the PROC/FUNC
    variant).  WITH on a function's own name inside it (the function result,
    e.g. WITH DummyCdd DO in APPW/UPREF) reads PFdeclKind = DECLARED (1) as
    Vkind = INDRCT, so the WITH counts as indirect."""
    if pVar.Class in (NameClass.PROC, NameClass.FUNC):
        return int(pVar.PFdeclKind)
    return int(pVar.Vkind)

class OptMixin:
    """AST optimizer and register allocator: constant/expression folding,
    side-effect and flippability analysis, variable/WITH/global-base reference
    counting, common subexpression binding, and D4-D7/A3-A4 register assignment."""

    def Optimize(self, fStmt: Optional[Stmt], FpN: Optional[N]) -> None:
        """Fold assignments of the form v := v +/- expr and v := expr + v into
        in-place ADDTO/SUBFROM (AssOp 41/42) operations across statement tree fStmt."""
        IncDec = 0

        def SameExpr(ApN: Optional[N], BpN: Optional[N]) -> bool:
            """Return True if two side-effect-free AST expression subtrees are structurally equivalent, ignoring range-check wrappers."""
            if BpN is not None and ApN is not None:
                if ApN.Node == BpN.Node:
                    if ApN.Node == NodeKind.IDENTNODE:
                        if ApN is BpN:
                            return ApN.Class != NameClass.FUNC
                    elif ApN.Node == NodeKind.UNNODE:
                        if ApN.UnOp == BpN.UnOp and ApN.UnSubOp == BpN.UnSubOp:
                            if ApN.UnOp in (12, 15, 43):
                                return SameVar(ApN, BpN)
                            if ApN.UnOp in (23, 31):
                                return True
                            return SameExpr(ApN.UnArg, BpN.UnArg)
                    elif ApN.Node == NodeKind.BINNODE:
                        if ApN.BinOp == BpN.BinOp and ApN.BinSubOp == BpN.BinSubOp:
                            if ApN.BinOp in (46, 47):
                                return SameExpr(ApN.RightArg, BpN.RightArg)
                            return (
                                SameExpr(ApN.LeftArg, BpN.LeftArg)
                                and SameExpr(ApN.RightArg, BpN.RightArg)
                            )
                    elif ApN.Node == NodeKind.TRINODE:
                        return SameVar(ApN, BpN)
                    elif ApN.Node == NodeKind.CSTNODE:
                        if ApN is BpN:
                            return True
                        if self.CompTypes(ApN.CstType, BpN.CstType):
                            if ApN.CstType is not None and ApN.CstType.Form in (
                                TypeForms.SCALAR,
                                TypeForms.SUBRANGE,
                            ):
                                if self.CompTypes(ApN.CstType, self.RealPtr):
                                    return ApN.CstValu.Rvalu == BpN.CstValu.Rvalu
                                return ApN.CstValu.Ivalu == BpN.CstValu.Ivalu
            return False

        def SameVar(ApN: Optional[N], BpN: Optional[N]) -> bool:
            """Return True if two AST variable-selector trees designate the same storage location, unwrapping ORD/ORD4 casts on BpN."""
            if BpN is not None and ApN is not None:
                if BpN.Node == NodeKind.BINNODE and BpN.BinOp == 178:
                    lKey = BpN.LeftArg.Key
                    if lKey == 10 or lKey == 32:
                        BpN = BpN.RightArg.LeftArg

                if BpN is not None and ApN.Node == BpN.Node:
                    if ApN.Node == NodeKind.IDENTNODE:
                        if ApN is BpN:
                            return ApN.Class == NameClass.VARS or ApN.Class == NameClass.FIELD
                    elif ApN.Node == NodeKind.UNNODE:
                        if ApN.UnOp == BpN.UnOp and ApN.UnSubOp == BpN.UnSubOp:
                            if ApN.UnOp in (12, 15, 43):
                                return SameVar(ApN.UnArg, BpN.UnArg)
                    elif ApN.Node == NodeKind.BINNODE:
                        pass
                    elif ApN.Node == NodeKind.TRINODE:
                        if ApN.TriOp == BpN.TriOp and ApN.TriOp == 16:
                            return SameVar(ApN.Tri1, BpN.Tri1) and SameExpr(ApN.Tri2, BpN.Tri2)
                    elif ApN.Node == NodeKind.CSTNODE:
                        pass
            return False

        def WalkTree(stmt: Optional[Stmt]) -> None:
            """Recursively traverse statements and rewrite 16/32-bit self-add/subtract assignments (unwrapping POINTER casts) into ADDTO/SUBFROM."""
            nonlocal IncDec
            while stmt is not None:
                op = stmt.StmtOp
                if op == StmtTypes.BEGINST:
                    WalkTree(stmt.SubSt)
                elif op == StmtTypes.ASSIGNST:
                    assert stmt.AssExpr is not None
                    if stmt.AssExpr.Node == NodeKind.BINNODE:
                        lBinOp = stmt.AssExpr.BinOp
                        FoundIt = False

                        if lBinOp == 178:
                            if stmt.AssExpr.LeftArg.Key == 18:
                                stmt.AssExpr = stmt.AssExpr.RightArg.LeftArg
                                assert stmt.AssExpr is not None
                                lBinOp = stmt.AssExpr.BinOp
                                if stmt.AssExpr.Node != NodeKind.BINNODE:
                                    lBinOp = 0

                        if 64 <= lBinOp <= 67:
                            if SameVar(stmt.AssVar, stmt.AssExpr.LeftArg):
                                FoundIt = True
                            elif lBinOp <= 65:
                                if SameVar(stmt.AssVar, stmt.AssExpr.RightArg):
                                    lpN = stmt.AssExpr.RightArg
                                    stmt.AssExpr.RightArg = stmt.AssExpr.LeftArg
                                    stmt.AssExpr.LeftArg = lpN
                                    FoundIt = True
                        if FoundIt:
                            IncDec += 1
                            if lBinOp <= 65:
                                stmt.AssOp = 41
                            else:
                                stmt.AssOp = 42
                            if odd(lBinOp):
                                stmt.AssSubOp = 4
                            else:
                                stmt.AssSubOp = 2
                            stmt.AssExpr = stmt.AssExpr.RightArg
                elif op in (StmtTypes.FORTOST, StmtTypes.FORDOWNST):
                    WalkTree(stmt.ForSt)
                elif op == StmtTypes.IFST:
                    WalkTree(stmt.ThenSt)
                    WalkTree(stmt.ElseSt)
                elif op == StmtTypes.WITHST:
                    WalkTree(stmt.WithBody)
                elif op in (StmtTypes.REPST, StmtTypes.WHILEST):
                    WalkTree(stmt.LoopStmt)
                elif op == StmtTypes.CALLST:
                    pass
                elif op == StmtTypes.GOTOST:
                    pass
                elif op == StmtTypes.CASEST:
                    WalkTree(stmt.CStmtList)
                    WalkTree(stmt.OtherStmt)
                elif op == StmtTypes.CSTMTST:
                    WalkTree(stmt.ThisCase)
                elif op == StmtTypes.LABEDST:
                    WalkTree(stmt.LabStmt)
                stmt = stmt.NextStmt

        WalkTree(fStmt)

    def RegLookup(self, SContents: RegContents, pVarb: Optional[N], SLevel: int) -> int:
        """Search CurRegisters (A3-A4 and D4-D7) for a bound variable (AVARIABLE) or
        lexical/unit frame base (GLOBALBASE at SLevel), returning the register index or -1."""
        if SContents == RegContents.AVARIABLE:
            for i in range(A1st, Anth + 1):
                cr = self.CurRegisters[i]
                if cr.Contents == RegContents.AVARIABLE and cr.PVar is pVarb:
                    return i
            for i in range(D1st, Dnth + 1):
                cr = self.CurRegisters[i]
                if cr.Contents == RegContents.AVARIABLE and cr.PVar is pVarb:
                    return i
        else:
            for i in range(A1st, Anth + 1):
                cr = self.CurRegisters[i]
                if cr.Contents == RegContents.GLOBALBASE and cr.RLevel == SLevel:
                    return i
        return -1

    def BindSelector(self, fVarb: Optional[N]) -> Optional[N]:
        """Rewrite a variable selector AST subtree to substitute bound REGISTER nodes
        (with dereference UNNODEs for VAR parameters) or (Voff + Areg)^ base-displacement
        nodes for intermediate and intrinsic-unit globals."""
        if fVarb is None:
            return None
        orig = fVarb
        node = orig.Node
        if node == NodeKind.IDENTNODE:
            if orig.Class in (NameClass.FUNC, NameClass.PROC, NameClass.CONSTS):
                pass
            elif orig.Class == NameClass.VARS:
                lLev = orig.Vlev
                lOff = orig.Voff
                VReg = self.RegLookup(RegContents.AVARIABLE, fVarb, 0)
                if VReg != -1:
                    PReg = N(NodeKind.REGISTER)
                    if orig.Vkind == AccessKind.INDRCT:
                        PU = N(NodeKind.UNNODE)
                        PU.Node = NodeKind.UNNODE
                        PU.UnOp = 12
                        PU.UnArg = PReg
                        fVarb = PU
                    else:
                        fVarb = PReg
                    PReg.Node = NodeKind.REGISTER
                    PReg.Reg = VReg
                    PReg.Load = 0
                    PReg.LoadExpr = None
                    PReg.LoadSize = 0
                elif lLev < 0 or (lLev > 1 and lLev != self.Level):
                    VReg = self.RegLookup(RegContents.GLOBALBASE, None, lLev)
                    if VReg != -1:
                        PU = N(NodeKind.BINNODE)
                        PReg = N(NodeKind.REGISTER)
                        PU.Node = NodeKind.BINNODE
                        PU.BinOp = 12
                        PU.BinSubOp = lOff
                        PU.LeftArg = PReg
                        PU.RightArg = None
                        PReg.Node = NodeKind.REGISTER
                        PReg.Reg = VReg
                        PReg.Load = 0
                        PReg.LoadExpr = None
                        PReg.LoadSize = 0
                        if orig.Vkind == AccessKind.INDRCT:
                            PU1 = N(NodeKind.UNNODE)
                            PU1.Node = NodeKind.UNNODE
                            PU1.UnOp = 12
                            PU1.UnArg = PU
                            fVarb = PU1
                        else:
                            fVarb = PU
            elif orig.Class == NameClass.FIELD:
                pass
        elif node == NodeKind.UNNODE:
            if orig.UnOp == 22:
                if orig.UnSubOp == 0:
                    orig.UnArg = self.BindSelector(orig.UnArg)
            elif orig.UnOp != 43:
                orig.UnArg = self.BindExpr(orig.UnArg)
        elif node == NodeKind.BINNODE:
            if orig.BinOp == 15 or orig.BinOp == 12:
                orig.LeftArg = self.BindSelector(orig.LeftArg)
        elif node == NodeKind.TRINODE:
            if orig.TriOp == 16:
                orig.Tri1 = self.BindSelector(orig.Tri1)
                orig.Tri2 = self.BindExpr(orig.Tri2)
            elif orig.TriOp == 184:
                orig.Tri1 = self.BindUCall(orig.TripN, orig.Tri2, orig.Tri1)
        elif node == NodeKind.REGISTER:
            if orig.LoadExpr is not None:
                orig.LoadExpr = self.BindExpr(orig.LoadExpr)
        elif node == NodeKind.CSTNODE:
            pass
        return fVarb

    def BindExpr(self, fExpr: Optional[N]) -> Optional[N]:
        """Recursively rewrite an expression AST to substitute allocated register references in operands, selectors, and function/method calls."""
        if fExpr is None:
            return None
        orig = fExpr
        node = orig.Node
        if node in (NodeKind.REGISTER, NodeKind.IDENTNODE):
            fExpr = self.BindSelector(fExpr)
        elif node == NodeKind.UNNODE:
            if (12 <= orig.UnOp <= 14) or orig.UnOp in (22, 43, 62, 63):
                fExpr = self.BindSelector(fExpr)
            else:
                if orig.UnOp not in (23, 31, 4):
                    orig.UnArg = self.BindExpr(orig.UnArg)
        elif node == NodeKind.BINNODE:
            if orig.BinOp in (12, 15) or (16 <= orig.BinOp <= 21):
                fExpr = self.BindSelector(fExpr)
            elif orig.BinOp == 176:
                TemppN: Optional[N] = None
                TemppN = self.BindUCall(orig.LeftArg, orig.RightArg, TemppN)
            elif orig.BinOp == 178:
                self.Bindsfcall(orig.LeftArg, orig.RightArg)
            else:
                if orig.BinOp != 46 and orig.BinOp != 47:
                    orig.LeftArg = self.BindExpr(orig.LeftArg)
                orig.RightArg = self.BindExpr(orig.RightArg)
        elif node == NodeKind.TRINODE:
            fExpr = self.BindSelector(fExpr)
        return fExpr

    def BindVarParm(self, ArgList: Optional[N]) -> Optional[N]:
        """Bind register references in the current by-reference actual argument and advance ArgList."""
        if ArgList is not None:
            ArgList.LeftArg = self.BindExpr(ArgList.LeftArg)
            ArgList = ArgList.RightArg
        return ArgList

    def BindValParm(self, ArgList: Optional[N]) -> Optional[N]:
        """Bind register references in the current by-value actual argument and advance ArgList."""
        if ArgList is not None:
            ArgList.LeftArg = self.BindExpr(ArgList.LeftArg)
            ArgList = ArgList.RightArg
        return ArgList

    def Bindsfcall(self, fProc: Optional[N], pArgs: Optional[N]) -> None:
        """Bind register references across the actual arguments of standard built-in function fProc (including Clascal THISCLASS and INCLASS)."""
        assert fProc is not None
        Key = fProc.Key
        if Key in (1, 14, 2, 4, 7, 8, 12, 13, 15, 17):
            pArgs = self.BindValParm(pArgs)
        elif Key in (5, 6, 34):
            pArgs = self.BindVarParm(pArgs)
        elif Key in (11, 16, 9):
            pArgs = self.BindValParm(pArgs)
        elif Key in (3, 10, 18, 26, 32, 35):
            assert pArgs is not None
            pArgs.LeftArg = self.BindExpr(pArgs.LeftArg)
        elif Key == 19:
            pArgs = self.BindValParm(pArgs)
        elif Key == 20:
            pArgs = self.BindVarParm(pArgs)
            pArgs = self.BindVarParm(pArgs)
        elif Key == 21:
            while pArgs is not None:
                pArgs = self.BindVarParm(pArgs)
        elif Key == 22:
            pArgs = self.BindVarParm(pArgs)
            pArgs = self.BindValParm(pArgs)
            pArgs = self.BindValParm(pArgs)
            pArgs = self.BindVarParm(pArgs)
        elif Key in (23, 24):
            pArgs = self.BindVarParm(pArgs)
            pArgs = self.BindVarParm(pArgs)
            pArgs = self.BindValParm(pArgs)
            if pArgs is not None:
                pArgs = self.BindValParm(pArgs)
        elif Key in (25, 31, 33):
            pass
        elif Key == 27:
            pArgs = self.BindValParm(pArgs)
        elif Key in (28, 29):
            pArgs = self.BindValParm(pArgs)
            pArgs = self.BindValParm(pArgs)
            pArgs = self.BindVarParm(pArgs)
        elif Key == 30:
            pArgs = self.BindValParm(pArgs)
        elif Key == 36:
            pArgs = self.BindValParm(pArgs)
            if pArgs is not None:
                if pArgs.BinOp == int(NodeKind.IDENTNODE):
                    pArgs = self.BindVarParm(pArgs)
                else:
                    pArgs = self.BindValParm(pArgs)

    def BindUCall(self, fProc: Optional[N], FArgs: Optional[N], fClVar: Optional[N]) -> Optional[N]:
        """Bind register references across actual arguments of user routine or Clascal method fProc, and bind the method receiver fClVar."""
        assert fProc is not None
        Formals = fProc.PFargList
        Actuals = FArgs
        while Formals is not None:
            if Formals.Class == NameClass.VARS:
                n_bytes = self.FullBytes(Formals.IdType)
                if Formals.Vkind == AccessKind.DRCT:
                    assert Formals.IdType is not None
                    if Formals.IdType.Form == TypeForms.SETS or n_bytes > 4:
                        Actuals = self.BindVarParm(Actuals)
                    else:
                        Actuals = self.BindValParm(Actuals)
                else:
                    Actuals = self.BindVarParm(Actuals)
            else:
                assert Actuals is not None
                Actuals = Actuals.RightArg
            Formals = Formals.Next
        if fProc.PFdecl == PFkind.METHDECL or fProc.PFdecl == PFkind.FORWMETHDECL:
            if fClVar is not None:
                fClVar = self.BindExpr(fClVar)
        return fClVar

    def BindCallStmt(self, fStmt: Optional[Stmt]) -> None:
        """Bind register references in a procedure call statement (READ/WRITE, standard procedures, or user-defined procedures)."""
        def get_slot(slot: tuple[N, str]) -> Optional[N]:
            return getattr(slot[0], slot[1])

        def bind_slot(slot: tuple[N, str]) -> None:
            setattr(slot[0], slot[1], self.BindExpr(getattr(slot[0], slot[1])))

        def ReadWrite(stmt: Stmt) -> None:
            """Bind register references for READ, READLN, WRITE, and WRITELN file, value, and colon width/precision arguments."""
            assert stmt.ProcpN is not None
            Key = stmt.ProcpN.Key
            pArgs = stmt.pArgList
            if Key in (8, 9):
                assert pArgs is not None
                FileArg: tuple[N, str] = (pArgs, 'LeftArg')
                pArgs = pArgs.RightArg
                while pArgs is not None:
                    bind_slot(FileArg)
                    pArgs.LeftArg = self.BindExpr(pArgs.LeftArg)
                    pArgs = pArgs.RightArg
                if Key == 9:
                    bind_slot(FileArg)
            elif Key in (10, 11):
                assert pArgs is not None
                FileArg = (pArgs, 'LeftArg')
                pArgs = pArgs.RightArg
                while pArgs is not None:
                    bind_slot(FileArg)
                    lOp = pArgs.BinOp
                    Colon1: Optional[tuple[N, str]] = None
                    Colon2: Optional[tuple[N, str]] = None
                    Arg: tuple[N, str] = (pArgs, 'LeftArg')
                    arg_node = get_slot(Arg)
                    if arg_node is not None and arg_node.Node == NodeKind.BINNODE and arg_node.BinOp == 0:
                        Colon1 = (arg_node, 'RightArg')
                        Arg = (arg_node, 'LeftArg')
                        arg_node = get_slot(Arg)
                        if arg_node is not None and arg_node.Node == NodeKind.BINNODE and arg_node.BinOp == 0:
                            Colon2 = Colon1
                            Colon1 = (arg_node, 'RightArg')
                            Arg = (arg_node, 'LeftArg')
                    if lOp <= 4:
                        bind_slot(Arg)
                    else:
                        bind_slot(Arg)
                        if lOp == 6:
                            assert Colon1 is not None
                            bind_slot(Colon1)
                            Colon1 = Colon2
                    if Colon1 is not None:
                        bind_slot(Colon1)
                    if lOp == 4 and Colon2 is not None:
                        bind_slot(Colon2)
                    pArgs = pArgs.RightArg
                if Key == 11:
                    bind_slot(FileArg)

        def BindStdProc(stmt: Stmt) -> None:
            """Bind register references in actual arguments of standard built-in procedures (NEW, RESET, DELETE, MOVELEFT, UNITREAD, etc.)."""
            assert stmt.ProcpN is not None
            Key = stmt.ProcpN.Key
            if Key != 29:
                pArgs = stmt.pArgList
                if Key in (1, 15, 20, 27):
                    pArgs = self.BindVarParm(pArgs)
                    pArgs = self.BindValParm(pArgs)
                elif Key in (2, 3, 4, 5, 12):
                    pArgs = self.BindVarParm(pArgs)
                elif Key in (6, 7):
                    pArgs = self.BindVarParm(pArgs)
                    if pArgs is not None:
                        pArgs = self.BindVarParm(pArgs)
                elif Key in (16, 24):
                    pArgs = self.BindVarParm(pArgs)
                    pArgs = self.BindValParm(pArgs)
                    pArgs = self.BindValParm(pArgs)
                elif Key in (17, 22, 23):
                    pArgs = self.BindVarParm(pArgs)
                    pArgs = self.BindVarParm(pArgs)
                    pArgs = self.BindValParm(pArgs)
                elif Key in (18, 19, 28):
                    pArgs = self.BindValParm(pArgs)
                    pArgs = self.BindVarParm(pArgs)
                    pArgs = self.BindValParm(pArgs)
                    if Key <= 19:
                        if pArgs is not None:
                            pArgs = self.BindValParm(pArgs)
                        if pArgs is not None:
                            pArgs = self.BindValParm(pArgs)
                elif Key == 21:
                    pass
                elif Key == 25:
                    pArgs = self.BindValParm(pArgs)
                elif Key == 26:
                    pArgs = self.BindValParm(pArgs)
                    pArgs = self.BindValParm(pArgs)

        assert fStmt is not None and fStmt.ProcpN is not None
        if fStmt.ProcpN.PFdeclKind == DeclKind.STANDARD:
            if 8 <= fStmt.ProcpN.Key <= 11:
                ReadWrite(fStmt)
            else:
                BindStdProc(fStmt)
        else:
            TemppN: Optional[N] = None
            TemppN = self.BindUCall(fStmt.ProcpN, fStmt.pArgList, TemppN)

    def BindStmt(self, fStmt: Optional[Stmt]) -> None:
        """Recursively substitute allocated register references across statement list fStmt,
        binding indirect WITH record addresses (@WithVar) into WITHSEL address registers (A3-A4)
        for the duration of their WITH bodies."""
        while fStmt is not None:
            op = fStmt.StmtOp
            if op == StmtTypes.BEGINST:
                self.BindStmt(fStmt.SubSt)
            elif op == StmtTypes.ASSIGNST:
                assert fStmt.AssVar is not None
                skip = (
                    fStmt.AssVar.Node == NodeKind.REGISTER
                    and self.GlobalRegisters[fStmt.AssVar.Reg].Contents == RegContents.GLOBALBASE
                )
                if not skip:
                    fStmt.AssVar = self.BindExpr(fStmt.AssVar)
                    fStmt.AssExpr = self.BindExpr(fStmt.AssExpr)
            elif op in (StmtTypes.FORTOST, StmtTypes.FORDOWNST):
                fStmt.ForInit = self.BindExpr(fStmt.ForInit)
                fStmt.ForLimit = self.BindExpr(fStmt.ForLimit)
                fStmt.ForVar = self.BindExpr(fStmt.ForVar)
                self.BindStmt(fStmt.ForSt)
            elif op == StmtTypes.IFST:
                fStmt.IfExpr = self.BindExpr(fStmt.IfExpr)
                self.BindStmt(fStmt.ThenSt)
                self.BindStmt(fStmt.ElseSt)
            elif op == StmtTypes.WITHST:
                self.WithLevel += 1
                WithReg = -1
                PVar = fStmt.WithVar
                assert PVar is not None
                while PVar.Node == NodeKind.BINNODE and PVar.BinOp == 15:
                    PVar = PVar.LeftArg
                    assert PVar is not None
                if PVar.Node != NodeKind.IDENTNODE:
                    self.WithRefs[self.WithLevel].Indirect = True
                else:
                    self.WithRefs[self.WithLevel].Indirect = (
                        with_vkind(PVar) != AccessKind.DRCT or PVar.Vlev != self.Level
                    )
                fStmt.WithVar = self.BindExpr(fStmt.WithVar)
                if self.WithRefs[self.WithLevel].Indirect:
                    for i in range(A1st, Anth + 1):
                        gr = self.GlobalRegisters[i]
                        if gr.Contents == RegContents.WITHSEL and gr.RLevel == self.WithLevel:
                            WithReg = i
                    if WithReg != -1:
                        self.CurRegisters[WithReg].set_from(self.GlobalRegisters[WithReg])
                        PReg = N(NodeKind.REGISTER)
                        pAtSign = N(NodeKind.UNNODE)
                        PReg.Node = NodeKind.REGISTER
                        PReg.Reg = WithReg
                        PReg.Load = 0
                        PReg.LoadExpr = pAtSign
                        PReg.LoadSize = LONG
                        pAtSign.Node = NodeKind.UNNODE
                        pAtSign.UnSubOp = 0
                        pAtSign.UnOp = 22
                        pAtSign.UnArg = fStmt.WithVar
                        fStmt.WithVar = PReg
                self.BindStmt(fStmt.WithBody)
                self.WithLevel -= 1
                if WithReg != -1:
                    self.CurRegisters[WithReg].Contents = RegContents.NADA
            elif op == StmtTypes.REPST:
                self.BindStmt(fStmt.LoopStmt)
                fStmt.CondExpr = self.BindExpr(fStmt.CondExpr)
            elif op == StmtTypes.WHILEST:
                fStmt.CondExpr = self.BindExpr(fStmt.CondExpr)
                self.BindStmt(fStmt.LoopStmt)
            elif op == StmtTypes.CALLST:
                self.BindCallStmt(fStmt)
            elif op == StmtTypes.METHODCALL:
                assert fStmt.AssVar is not None
                fStmt.AssVar.Tri1 = self.BindUCall(
                    fStmt.AssVar.TripN, fStmt.AssVar.Tri2, fStmt.AssVar.Tri1
                )
            elif op == StmtTypes.GOTOST:
                pass
            elif op == StmtTypes.CASEST:
                fStmt.CaseExpr = self.BindExpr(fStmt.CaseExpr)
                self.BindStmt(fStmt.CStmtList)
                self.BindStmt(fStmt.OtherStmt)
            elif op == StmtTypes.CSTMTST:
                self.BindStmt(fStmt.ThisCase)
            elif op == StmtTypes.LABEDST:
                self.BindStmt(fStmt.LabStmt)
            fStmt = fStmt.NextStmt

    def InitRefTable(self) -> None:
        """Reset the VarRefs candidate table (CurRefs = -1) before counting local variable references."""
        self.CurRefs = -1

    def RefLocal(self, pVarb: Optional[N]) -> None:
        """Record a reference in VarRefs to a register-eligible local scalar/pointer variable
        (<= 4 bytes) or VAR parameter not forced into memory, starting parameters at -1 to
        account for entry load cost."""
        if pVarb is None or pVarb.IdType is None:
            return
        id_type = pVarb.IdType
        if pVarb.Class == NameClass.VARS:
            if (
                (id_type.Form <= TypeForms.POINTERS and self.FullBytes(id_type) <= 4)
                or pVarb.Vkind == AccessKind.INDRCT
            ) and pVarb.InRegister != -2:
                for i in range(self.CurRefs + 1):
                    vr = self.VarRefs[i]
                    if vr.PVar is pVarb:
                        vr.Refs += 1
                        return
                if self.CurRefs < MAXREFS:
                    self.CurRefs += 1
                    vr = self.VarRefs[self.CurRefs]
                    vr.PVar = pVarb
                    if pVarb.Voff <= 0:
                        vr.Refs = 1
                    else:
                        vr.Refs = -1

    def PutInMemory(self, pVarb: Optional[N]) -> None:
        """Force variable pVarb to remain in stack memory (InRegister = -2) when addressed,
        passed by reference, or accessed non-locally, removing it from VarRefs if local."""
        if pVarb is None:
            return
        if pVarb.Node == NodeKind.IDENTNODE and pVarb.Class == NameClass.VARS:
            pVarb.InRegister = -2
            if pVarb.Vlev == self.Level:
                for i in range(self.CurRefs + 1):
                    if self.VarRefs[i].PVar is pVarb:
                        for j in range(i, self.CurRefs):
                            self.VarRefs[j].PVar = self.VarRefs[j + 1].PVar
                            self.VarRefs[j].Refs = self.VarRefs[j + 1].Refs
                        self.CurRefs -= 1
                        return

    def RefSelector(self, fVarb: Optional[N]) -> None:
        """Accumulate reference counts for local variables, depth-weighted intermediate
        frame links (iGlobalRefs), intrinsic unit globals (sGlobalRefs), and indirect WITH
        selectors (WithRefs), while forcing addressed or uplevel-referenced variables into memory."""
        if fVarb is None:
            return
        node = fVarb.Node
        if node == NodeKind.IDENTNODE:
            if fVarb.Class == NameClass.CONSTS:
                pass
            elif fVarb.Class in (NameClass.FUNC, NameClass.PROC, NameClass.VARS):
                if fVarb.Class == NameClass.VARS:
                    lLev = fVarb.Vlev
                elif fVarb.PFdecl == PFkind.FORMAL:
                    lLev = fVarb.PFlev
                else:
                    lLev = fVarb.PFlev + 1
                if lLev == self.Level:
                    self.RefLocal(fVarb)
                elif lLev > 1:
                    self.iGlobalRefs[lLev] += self.Level - lLev
                    self.PutInMemory(fVarb)
                elif lLev < 0:
                    UnitpN = self.UnitList
                    while UnitpN is not None:
                        if UnitpN.Ulev == lLev and UnitpN.Ukind != UnitKind.REGUNIT:
                            self.sGlobalRefs[-lLev] += 1
                            break
                        UnitpN = UnitpN.Next
            elif fVarb.Class == NameClass.FIELD:
                pass
        elif node == NodeKind.UNNODE:
            if fVarb.UnOp == 22:
                self.PutInMemory(fVarb.UnArg)
                if fVarb.UnSubOp == 0:
                    self.RefSelector(fVarb.UnArg)
            elif fVarb.UnOp != 43:
                self.RefExpr(fVarb.UnArg)
            else:
                wr = self.WithRefs[fVarb.UnSubOp]
                if wr.Indirect:
                    wr.Refs += 1
        elif node == NodeKind.BINNODE:
            if fVarb.BinOp == 15:
                self.RefSelector(fVarb.LeftArg)
        elif node == NodeKind.TRINODE:
            if fVarb.TriOp == 16:
                self.RefSelector(fVarb.Tri1)
                self.RefExpr(fVarb.Tri2)
            elif fVarb.TriOp == 184:
                self.GlobFlippable = False
                self.RefUCall(fVarb.TripN, fVarb.Tri2, fVarb.Tri1)
        elif node == NodeKind.CSTNODE:
            pass

    def RefExpr(self, fExpr: Optional[N]) -> None:
        """Traverse expression fExpr to tally variable/base references and clear GlobFlippable
        on function/method calls or condition-code-dependent relational operators."""
        if fExpr is None:
            return
        node = fExpr.Node
        if node == NodeKind.IDENTNODE:
            self.RefSelector(fExpr)
        elif node == NodeKind.UNNODE:
            if (12 <= fExpr.UnOp <= 14) or fExpr.UnOp in (22, 43, 62, 63):
                self.RefSelector(fExpr)
            else:
                if fExpr.UnOp != 23 and fExpr.UnOp != 31:
                    self.RefExpr(fExpr.UnArg)
        elif node == NodeKind.BINNODE:
            BinopX = fExpr.BinOp
            if BinopX == 15 or (16 <= BinopX <= 21):
                self.RefSelector(fExpr)
            elif BinopX == 176:
                self.GlobFlippable = False
                self.RefUCall(fExpr.LeftArg, fExpr.RightArg, None)
            elif BinopX == 178:
                self.RefSfCall(fExpr.LeftArg, fExpr.RightArg)
            else:
                if (
                    (92 <= BinopX <= 109)
                    or (122 <= BinopX <= 133)
                    or (144 <= BinopX <= 155)
                    or (163 <= BinopX <= 167)
                ):
                    self.GlobFlippable = False
                if BinopX != 46 and BinopX != 47:
                    self.RefExpr(fExpr.LeftArg)
                self.RefExpr(fExpr.RightArg)
        elif node == NodeKind.TRINODE:
            self.RefSelector(fExpr)
        elif node == NodeKind.CSTNODE:
            pass

    def RefVarParm(self, ArgList: Optional[N]) -> Optional[N]:
        """Force a by-reference actual argument into memory, count its references, and advance ArgList."""
        if ArgList is not None:
            self.PutInMemory(ArgList.LeftArg)
            self.RefExpr(ArgList.LeftArg)
            ArgList = ArgList.RightArg
        return ArgList

    def RefValParm(self, ArgList: Optional[N]) -> Optional[N]:
        """Count variable and base references in a by-value actual argument and advance ArgList."""
        if ArgList is not None:
            self.RefExpr(ArgList.LeftArg)
            ArgList = ArgList.RightArg
        return ArgList

    def RefSfCall(self, fProc: Optional[N], pArgs: Optional[N]) -> None:
        """Count variable/base references and mark by-reference arguments in memory for standard function call fProc."""
        assert fProc is not None
        Key = fProc.Key
        if Key in (1, 14, 2, 4, 7, 8, 12, 13, 15, 17):
            pArgs = self.RefValParm(pArgs)
        elif Key in (5, 6, 34):
            pArgs = self.RefVarParm(pArgs)
        elif Key in (11, 16, 9):
            pArgs = self.RefValParm(pArgs)
        elif Key in (3, 10, 18, 26, 32):
            assert pArgs is not None
            self.RefExpr(pArgs.LeftArg)
        elif Key == 19:
            pArgs = self.RefValParm(pArgs)
        elif Key == 20:
            pArgs = self.RefVarParm(pArgs)
            pArgs = self.RefVarParm(pArgs)
        elif Key == 21:
            while pArgs is not None:
                pArgs = self.RefVarParm(pArgs)
        elif Key == 22:
            pArgs = self.RefVarParm(pArgs)
            pArgs = self.RefValParm(pArgs)
            pArgs = self.RefValParm(pArgs)
            pArgs = self.RefVarParm(pArgs)
        elif Key in (23, 24):
            pArgs = self.RefVarParm(pArgs)
            pArgs = self.RefVarParm(pArgs)
            pArgs = self.RefValParm(pArgs)
            if pArgs is not None:
                pArgs = self.RefValParm(pArgs)
        elif Key in (25, 31, 33):
            pass
        elif Key == 27:
            pArgs = self.RefValParm(pArgs)
        elif Key in (28, 29):
            pArgs = self.RefValParm(pArgs)
            pArgs = self.RefValParm(pArgs)
            pArgs = self.RefVarParm(pArgs)
        elif Key == 30:
            pArgs = self.RefValParm(pArgs)

    def RefUCall(self, fProc: Optional[N], FArgs: Optional[N], fClVar: Optional[N]) -> None:
        """Count references across actual arguments of user routine or Clascal method fProc
        (forcing VAR, set, and >4-byte value arguments into memory) and its receiver fClVar."""
        assert fProc is not None
        Formals = fProc.PFargList
        Actuals = FArgs
        while Formals is not None:
            if Formals.Class == NameClass.VARS:
                n_bytes = self.FullBytes(Formals.IdType)
                if Formals.Vkind == AccessKind.DRCT:
                    assert Formals.IdType is not None
                    if Formals.IdType.Form == TypeForms.SETS or n_bytes > 4:
                        Actuals = self.RefVarParm(Actuals)
                    else:
                        Actuals = self.RefValParm(Actuals)
                else:
                    Actuals = self.RefVarParm(Actuals)
            else:
                assert Actuals is not None
                Actuals = Actuals.RightArg
            Formals = Formals.Next
        if fProc.PFdecl == PFkind.METHDECL or fProc.PFdecl == PFkind.FORWMETHDECL:
            if fClVar is not None:
                self.RefExpr(fClVar)

    def RefCallStmt(self, fStmt: Optional[Stmt]) -> None:
        """Count variable/base references and mark memory-bound arguments for a procedure call statement."""
        def ReadWrite(stmt: Stmt) -> None:
            """Count references for READ/READLN/WRITE/WRITELN arguments, forcing file variables, READ targets, and string/packed-array WRITE operands into memory."""
            assert stmt.ProcpN is not None
            Key = stmt.ProcpN.Key
            pArgs = stmt.pArgList
            if Key in (8, 9):
                assert pArgs is not None
                FileArg = pArgs.LeftArg
                self.PutInMemory(FileArg)
                pArgs = pArgs.RightArg
                while pArgs is not None:
                    self.RefExpr(FileArg)
                    self.PutInMemory(pArgs.LeftArg)
                    self.RefExpr(pArgs.LeftArg)
                    pArgs = pArgs.RightArg
                if Key == 9:
                    self.RefExpr(FileArg)
            elif Key in (10, 11):
                assert pArgs is not None
                FileArg = pArgs.LeftArg
                self.PutInMemory(FileArg)
                pArgs = pArgs.RightArg
                while pArgs is not None:
                    self.RefExpr(FileArg)
                    lOp = pArgs.BinOp
                    Colon1: Optional[N] = None
                    Colon2: Optional[N] = None
                    Arg = pArgs.LeftArg
                    assert Arg is not None
                    if Arg.Node == NodeKind.BINNODE and Arg.BinOp == 0:
                        Colon1 = Arg.RightArg
                        Arg = Arg.LeftArg
                        assert Arg is not None
                        if Arg.Node == NodeKind.BINNODE and Arg.BinOp == 0:
                            Colon2 = Colon1
                            Colon1 = Arg.RightArg
                            Arg = Arg.LeftArg
                    if lOp <= 4:
                        self.RefExpr(Arg)
                    else:
                        self.PutInMemory(Arg)
                        self.RefExpr(Arg)
                        if lOp == 6:
                            self.RefExpr(Colon1)
                            Colon1 = Colon2
                    if Colon1 is not None:
                        self.RefExpr(Colon1)
                    if lOp == 4 and Colon2 is not None:
                        self.RefExpr(Colon2)
                    pArgs = pArgs.RightArg
                if Key == 11:
                    self.RefExpr(FileArg)

        def RefStdProc(stmt: Stmt) -> None:
            """Count references and mark VAR arguments in memory for standard built-in procedure calls."""
            assert stmt.ProcpN is not None
            Key = stmt.ProcpN.Key
            if Key != 29:
                pArgs = stmt.pArgList
                if Key in (1, 15, 20, 27):
                    pArgs = self.RefVarParm(pArgs)
                    pArgs = self.RefValParm(pArgs)
                elif Key in (2, 3, 4, 5, 12):
                    pArgs = self.RefVarParm(pArgs)
                elif Key in (6, 7):
                    pArgs = self.RefVarParm(pArgs)
                    if pArgs is not None:
                        pArgs = self.RefVarParm(pArgs)
                elif Key in (16, 24):
                    pArgs = self.RefVarParm(pArgs)
                    pArgs = self.RefValParm(pArgs)
                    pArgs = self.RefValParm(pArgs)
                elif Key in (17, 22, 23):
                    pArgs = self.RefVarParm(pArgs)
                    pArgs = self.RefVarParm(pArgs)
                    pArgs = self.RefValParm(pArgs)
                elif Key in (18, 19, 28):
                    pArgs = self.RefValParm(pArgs)
                    pArgs = self.RefVarParm(pArgs)
                    pArgs = self.RefValParm(pArgs)
                    if Key <= 19:
                        if pArgs is not None:
                            pArgs = self.RefValParm(pArgs)
                        if pArgs is not None:
                            pArgs = self.RefValParm(pArgs)
                elif Key == 21:
                    pass
                elif Key == 25:
                    pArgs = self.RefValParm(pArgs)
                elif Key == 26:
                    pArgs = self.RefValParm(pArgs)
                    pArgs = self.RefValParm(pArgs)

        assert fStmt is not None and fStmt.ProcpN is not None
        if fStmt.ProcpN.PFdeclKind == DeclKind.STANDARD:
            if 8 <= fStmt.ProcpN.Key <= 11:
                ReadWrite(fStmt)
            else:
                RefStdProc(fStmt)
        else:
            self.RefUCall(fStmt.ProcpN, fStmt.pArgList, None)

    def RefStmt(self, fStmt: Optional[Stmt]) -> None:
        """Traverse statements to gather reference statistics for register allocation,
        set assignment Flippable flags, weight FOR-loop control variables (3x), track
        indirect and invariant-pointer WITH statements, and detect non-local GOTOs."""
        while fStmt is not None:
            op = fStmt.StmtOp
            if op == StmtTypes.BEGINST:
                self.RefStmt(fStmt.SubSt)
            elif op == StmtTypes.ASSIGNST:
                self.GlobFlippable = True
                self.RefExpr(fStmt.AssVar)
                self.RefExpr(fStmt.AssExpr)
                assert fStmt.AssVar is not None
                fStmt.Flippable = (
                    self.GlobFlippable
                    and fStmt.AssVar.Node != NodeKind.REGISTER
                    and 32 <= fStmt.AssOp <= 35
                )
            elif op in (StmtTypes.FORTOST, StmtTypes.FORDOWNST):
                self.RefExpr(fStmt.ForInit)
                self.RefExpr(fStmt.ForLimit)
                self.RefExpr(fStmt.ForVar)
                self.RefExpr(fStmt.ForVar)
                self.RefExpr(fStmt.ForVar)
                self.RefStmt(fStmt.ForSt)
            elif op == StmtTypes.IFST:
                self.RefExpr(fStmt.IfExpr)
                self.RefStmt(fStmt.ThenSt)
                self.RefStmt(fStmt.ElseSt)
            elif op == StmtTypes.WITHST:
                self.WithLevel += 1
                PVar = fStmt.WithVar
                assert PVar is not None
                while PVar.Node == NodeKind.BINNODE and PVar.BinOp == 15:
                    PVar = PVar.LeftArg
                    assert PVar is not None
                pActual = PVar
                wr = self.WithRefs[self.WithLevel]
                if PVar.Node != NodeKind.IDENTNODE:
                    wr.Indirect = True
                    if PVar.Node == NodeKind.UNNODE and PVar.UnOp == 12:
                        pActual = PVar.UnArg
                else:
                    wr.Indirect = with_vkind(PVar) != AccessKind.DRCT or (
                        PVar.Vlev != self.Level and PVar.Vlev > 1
                    )
                if wr.PUpArrow is not None:
                    if pActual is not wr.PUpArrow:
                        wr.EverChange = True
                wr.PUpArrow = pActual
                self.RefExpr(fStmt.WithVar)
                self.RefStmt(fStmt.WithBody)
                self.WithLevel -= 1
            elif op == StmtTypes.REPST:
                self.RefStmt(fStmt.LoopStmt)
                self.RefExpr(fStmt.CondExpr)
            elif op == StmtTypes.WHILEST:
                self.RefExpr(fStmt.CondExpr)
                self.RefStmt(fStmt.LoopStmt)
            elif op == StmtTypes.CALLST:
                self.RefCallStmt(fStmt)
            elif op == StmtTypes.METHODCALL:
                assert fStmt.AssVar is not None
                self.RefUCall(fStmt.AssVar.TripN, fStmt.AssVar.Tri2, fStmt.AssVar.Tri1)
            elif op == StmtTypes.GOTOST:
                pass
            elif op == StmtTypes.CASEST:
                self.RefExpr(fStmt.CaseExpr)
                self.RefStmt(fStmt.CStmtList)
                self.RefStmt(fStmt.OtherStmt)
            elif op == StmtTypes.CSTMTST:
                self.RefStmt(fStmt.ThisCase)
            elif op == StmtTypes.LABEDST:
                assert fStmt.StLab is not None
                if fStmt.StLab.GlobRefNo >= 0:
                    self.HasGlobalLabel = True
                self.RefStmt(fStmt.LabStmt)
            fStmt = fStmt.NextStmt

    def BindRegisters(self, ProcStmt: Optional[Stmt], ProcpN: Optional[N]) -> Optional[Stmt]:
        """Score reference counts and allocate MC68000 registers D4-D7 and A3-A4 across
        WITH pointers, intermediate static links, intrinsic unit bases, and hot local/parameter
        variables; rewrite ProcStmt to use bound registers and synthesize entry/exit loads."""
        IsMethodCreate = False

        def CleanRegs() -> None:
            """Reset all allocatable register descriptors (D4-D7 and A3-A4) in GlobalRegisters and CurRegisters to NADA."""
            for reg_i in range(D1st, Dnth + 1):
                self.GlobalRegisters[reg_i].Contents = RegContents.NADA
                self.CurRegisters[reg_i].Contents = RegContents.NADA
            for reg_i in range(A1st, Anth + 1):
                self.GlobalRegisters[reg_i].Contents = RegContents.NADA
                self.CurRegisters[reg_i].Contents = RegContents.NADA

        def AssignParameter(RegI: int) -> None:
            """Record RegI in RegMask and prepend a prolog assignment loading a register-bound
            parameter (or its @ address for VAR parameters), or append SELF := RegI at the end
            of a Clascal CREATE constructor."""
            nonlocal ProcStmt
            gr = self.GlobalRegisters[RegI]
            if gr.Contents != RegContents.NADA:
                self.RegMask.sMask.add(RegI)
                if gr.Contents == RegContents.AVARIABLE:
                    pvar = gr.PVar
                    assert pvar is not None
                    if pvar.Voff > 0:
                        if pvar.IsSELF and IsMethodCreate:
                            PLStmt = ProcStmt
                            assert PLStmt is not None
                            while PLStmt.NextStmt is not None:
                                PLStmt = PLStmt.NextStmt
                            PAsgStmt = Stmt(StmtTypes.ASSIGNST)
                            PReg = N(NodeKind.REGISTER)
                            PAsgStmt.StmtNumb = 0
                            PAsgStmt.Flippable = False
                            PAsgStmt.StmtOp = StmtTypes.ASSIGNST
                            PAsgStmt.AssExpr = PReg
                            PAsgStmt.AssVar = pvar
                            PAsgStmt.AssOp = 34
                            PAsgStmt.AssSubOp = 0
                            PAsgStmt.NextStmt = None
                            PLStmt.NextStmt = PAsgStmt
                        else:
                            PAsgStmt = Stmt(StmtTypes.ASSIGNST)
                            PReg = N(NodeKind.REGISTER)
                            PAsgStmt.StmtNumb = 0
                            PAsgStmt.Flippable = False
                            PAsgStmt.StmtOp = StmtTypes.ASSIGNST
                            PAsgStmt.AssOp = 34
                            if pvar.Vkind != AccessKind.INDRCT:
                                fb = self.FullBytes(pvar.IdType)
                                if fb <= 1:
                                    PAsgStmt.AssOp = 32
                                elif fb == 2:
                                    PAsgStmt.AssOp = 33
                                PAsgStmt.AssExpr = pvar
                            else:
                                pAtSign = N(NodeKind.UNNODE)
                                pAtSign.Node = NodeKind.UNNODE
                                pAtSign.UnSubOp = 0
                                pAtSign.UnOp = 22
                                pAtSign.UnArg = pvar
                                PAsgStmt.AssExpr = pAtSign
                            PAsgStmt.AssSubOp = 0
                            PAsgStmt.AssVar = PReg
                            PAsgStmt.NextStmt = ProcStmt
                            ProcStmt = PAsgStmt
                        PReg.Node = NodeKind.REGISTER
                        PReg.Load = 0
                        PReg.LoadExpr = None
                        PReg.LoadSize = 0
                        PReg.Reg = RegI

        self.WithLevel = 0
        for i in range(MAXDISPLAY + 1):
            wr = self.WithRefs[i]
            wr.Refs = 0
            wr.EverChange = False
            wr.PUpArrow = None
            self.iGlobalRefs[i] = -1

        for i in range(self.NumUnits + 1):
            self.sGlobalRefs[i] = -1

        self.InitRefTable()

        self.HasGlobalLabel = False
        self.RefStmt(ProcStmt)

        if self.HasGlobalLabel:
            return ProcStmt

        CleanRegs()
        Saved = 0
        for i in range(MAXDISPLAY + 1):
            wr = self.WithRefs[i]
            if wr.PUpArrow is not None and not wr.EverChange:
                pup = wr.PUpArrow
                if pup.Node == NodeKind.IDENTNODE and pup.IdType is not None:
                    if pup.Class == NameClass.VARS and pup.IdType.Form == TypeForms.POINTERS:
                        for j in range(self.CurRefs + 1):
                            vr = self.VarRefs[j]
                            if vr.PVar is pup:
                                vr.Refs += wr.Refs
                                wr.Refs = 0

        AltUses = [0] * 16
        for i in range(Anth, A1st - 1, -1):
            AltUses[i] = 0

        for i in range(self.CurRefs + 1):
            vr = self.VarRefs[i]
            AFlag = False
            pvar = vr.PVar
            assert pvar is not None
            if pvar.Vkind == AccessKind.INDRCT:
                AFlag = True
            elif pvar.IdType is not None:
                AFlag = pvar.IdType.Form in (TypeForms.POINTERS, TypeForms.CLASSES)
            if AFlag:
                for j in range(Anth, A1st - 1, -1):
                    if vr.Refs > AltUses[j]:
                        for k in range(A1st, j):
                            AltUses[k] = AltUses[k + 1]
                        AltUses[j] = vr.Refs
                        break

        AWith = 0
        AIGlobal = 1
        ASGlobal = 2
        MaxIs = AWith
        MaxIdx = 0

        ARegs = Anth
        Bnd = A1st
        i = Anth
        k = Anth
        goto_30 = False
        while i >= Bnd:
            lMaxRefs = 0
            for j in range(MAXDISPLAY + 1):
                if self.WithRefs[j].Refs > lMaxRefs:
                    MaxIs = AWith
                    MaxIdx = j
                    lMaxRefs = self.WithRefs[j].Refs
                if self.iGlobalRefs[j] > lMaxRefs:
                    MaxIs = AIGlobal
                    MaxIdx = j
                    lMaxRefs = self.iGlobalRefs[j]
            for j in range(self.NumUnits + 1):
                if self.sGlobalRefs[j] > lMaxRefs:
                    MaxIs = ASGlobal
                    MaxIdx = j
                    lMaxRefs = self.sGlobalRefs[j]

            while (lMaxRefs * 2) < AltUses[k]:
                k -= 1
                Bnd += 1
                if i < Bnd:
                    goto_30 = True
                    break
            if goto_30:
                break

            gr = self.GlobalRegisters[i]
            if MaxIs != ASGlobal:
                gr.RLevel = MaxIdx
            else:
                gr.RLevel = -MaxIdx
            if lMaxRefs != 0:
                ARegs = i - 1
                if MaxIs == AWith:
                    gr.Contents = RegContents.WITHSEL
                    Saved += 4 * self.WithRefs[MaxIdx].Refs
                    self.WithRefs[MaxIdx].Refs = 0
                    self.CurRegisters[i].Contents = RegContents.NADA
                elif MaxIs == AIGlobal:
                    gr.Contents = RegContents.GLOBALBASE
                    Saved += 4 * self.iGlobalRefs[MaxIdx]
                    self.iGlobalRefs[MaxIdx] = 0
                    self.CurRegisters[i].set_from(gr)
                else:
                    gr.Contents = RegContents.GLOBALBASE
                    Saved += 4 * self.sGlobalRefs[MaxIdx]
                    self.sGlobalRefs[MaxIdx] = 0
                    self.CurRegisters[i].set_from(gr)
            i -= 1

        TotalRegs = (Anth - A1st + Dnth - D1st) + (ARegs - Anth) + 1
        if self.CurRefs < TotalRegs:
            NewCurRefs = self.CurRefs
        else:
            NewCurRefs = TotalRegs
        for i in range(NewCurRefs + 1):
            lMaxRefs = -1
            for j in range(i, self.CurRefs + 1):
                if self.VarRefs[j].Refs > lMaxRefs:
                    lMaxRefs = self.VarRefs[j].Refs
                    MaxIdx = j
            if lMaxRefs <= 0:
                NewCurRefs = i - 1
                break
            tmp_pvar = self.VarRefs[i].PVar
            tmp_refs = self.VarRefs[i].Refs
            self.VarRefs[i].PVar = self.VarRefs[MaxIdx].PVar
            self.VarRefs[i].Refs = self.VarRefs[MaxIdx].Refs
            self.VarRefs[MaxIdx].PVar = tmp_pvar
            self.VarRefs[MaxIdx].Refs = tmp_refs

        self.CurRefs = NewCurRefs

        DRegs = Dnth
        for i in range(self.CurRefs + 1):
            j = -1
            vr = self.VarRefs[i]
            pvar = vr.PVar
            assert pvar is not None and pvar.IdType is not None
            form = pvar.IdType.Form
            lSaved = vr.Refs * 2
            if form == TypeForms.POINTERS or form == TypeForms.CLASSES or pvar.Vkind == AccessKind.INDRCT:
                if ARegs >= A1st:
                    j = ARegs
                    ARegs -= 1
                    lSaved *= 2
                else:
                    j = DRegs
                    DRegs -= 1
            elif DRegs >= D1st:
                j = DRegs
                DRegs -= 1
            if j != -1:
                gr = self.GlobalRegisters[j]
                gr.Contents = RegContents.AVARIABLE
                gr.PVar = vr.PVar
                vr.PVar.InRegister = j
                Saved += lSaved
                self.CurRegisters[j].set_from(gr)

        TotalRegs = TotalRegs + (DRegs - Dnth)
        if TotalRegs == (Anth - A1st + Dnth - D1st):
            if Saved <= 4:
                CleanRegs()
        else:
            if Saved <= 8:
                CleanRegs()

        MinLevel = MAXDISPLAY + 1
        MinReg = 0
        for i in range(A1st, Anth + 1):
            gr = self.GlobalRegisters[i]
            if gr.Contents != RegContents.NADA:
                self.RegMask.sMask.add(i)
                if gr.Contents == RegContents.GLOBALBASE:
                    if gr.RLevel < 0:
                        PAsgStmt = Stmt(StmtTypes.ASSIGNST)
                        PBase = N(NodeKind.UNNODE)
                        PReg = N(NodeKind.REGISTER)
                        PAsgStmt.StmtNumb = 0
                        PAsgStmt.StmtOp = StmtTypes.ASSIGNST
                        PAsgStmt.Flippable = False
                        PAsgStmt.AssOp = 34
                        PAsgStmt.AssSubOp = 0
                        PAsgStmt.AssVar = PReg
                        PAsgStmt.AssExpr = PBase
                        PAsgStmt.NextStmt = ProcStmt
                        ProcStmt = PAsgStmt

                        PReg.Node = NodeKind.REGISTER
                        PReg.Load = 0
                        PReg.LoadSize = 0
                        PReg.LoadExpr = None
                        PReg.Reg = i

                        PBase.Node = NodeKind.UNNODE
                        PBase.UnSubOp = -gr.RLevel
                        PBase.UnOp = 4
                        PBase.UnArg = None
                    elif gr.RLevel < MinLevel:
                        MinLevel = gr.RLevel
                        MinReg = i

        if MinLevel <= MAXDISPLAY:
            PAsgStmt = Stmt(StmtTypes.ASSIGNST)
            PBase = N(NodeKind.BINNODE)
            PReg = N(NodeKind.REGISTER)
            PAsgStmt.StmtNumb = 0
            PAsgStmt.StmtOp = StmtTypes.ASSIGNST
            PAsgStmt.Flippable = False
            PAsgStmt.AssOp = 34
            PAsgStmt.AssSubOp = 0
            PAsgStmt.AssVar = PReg
            PAsgStmt.AssExpr = PBase
            PAsgStmt.NextStmt = ProcStmt
            ProcStmt = PAsgStmt

            PReg.Node = NodeKind.REGISTER
            PReg.Load = 0
            PReg.LoadSize = 0
            PReg.LoadExpr = None
            PReg.Reg = MinReg

            PReg = N(NodeKind.REGISTER)
            PNewBase: Optional[N] = None
            PNewReg: Optional[N] = None
            for i in range(MinLevel, self.Level):
                assert PBase is not None and PReg is not None
                PBase.Node = NodeKind.BINNODE
                PBase.BinOp = 12
                PBase.BinSubOp = SLinkOffset
                PBase.LeftArg = PReg
                PBase.RightArg = None

                PReg.Node = NodeKind.REGISTER
                PReg.Load = 0
                if i == (self.Level - 1):
                    PReg.Reg = A6
                    PReg.LoadExpr = None
                    PReg.LoadSize = 0
                else:
                    GReg = self.RegLookup(RegContents.GLOBALBASE, None, i + 1)
                    if GReg != -1:
                        PReg.Reg = GReg
                    else:
                        PReg.Reg = MinReg
                    PNewBase = N(NodeKind.BINNODE)
                    PReg.LoadExpr = PNewBase
                    PReg.LoadSize = LONG
                    PNewReg = N(NodeKind.REGISTER)
                PBase = PNewBase
                PReg = PNewReg

        self.BindStmt(ProcStmt)

        assert ProcpN is not None
        IsMethodCreate = ProcpN.PFdecl == PFkind.METHDECL and ProcpN.MethodNo == 0
        for i in range(D1st, Dnth + 1):
            AssignParameter(i)
        for i in range(A1st, Anth + 1):
            AssignParameter(i)

        return ProcStmt

    def GlobalOptimize(self, fstmt: Optional[Stmt], thisprocpn: Optional[N]) -> Optional[Stmt]:
        """No-op hook for global flow / common subexpression optimization, returning fstmt unchanged."""
        return fstmt
