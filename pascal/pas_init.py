"""Initialization mixin for the Lisa Pascal Front End."""

from __future__ import annotations

import sys
from typing import Optional

from lisalib import (
    AbortCompilation,
    IOByteSize,
    IODevType,
    IOFCB,
    IOModes,
    IONewline,
    PromptState,
    SUEsc,
    SUMaxStrLeng,
    pcopy,
)
from frontend_base import (
    AccessKind,
    CondState,
    DeclKind,
    InbufByteSize,
    InputFileTypes,
    N,
    NameClass,
    NodeKind,
    PFkind,
    Symbol,
    T,
    TITLE,
    TypeForms,
    VERSION,
    Where,
)


class InitMixin:
    """Front-end initializer: character/reserved-word scanner tables, built-in
    types, constants, variables, standard procedures/functions, Clascal helper
    symbols, conditional-compilation state, command-line/interactive options,
    and Workshop file prompts."""

    def Initialize(self) -> None:
        """Reset compiler state, run Workshop file/option prompts, and populate scanner and level-0 symbol tables."""

        def KCSDefaults() -> None:
            """Clear low-memory floating-point scratch words on standalone monitor builds (no-op for Lisa OS)."""
            # ForOs = True -> no-op
            pass

        def InitScanner() -> None:
            """Initialize scanner lookahead buffers, reserved-word lookup tables, and ASCII ``ChClass`` mappings."""

            def InitRW1() -> None:
                """Populate ``RWnames`` with the 44 8-character reserved words sorted by unpadded keyword length."""
                self.RWnames[1] = 'IF      '
                self.RWnames[2] = 'OR      '
                self.RWnames[3] = 'DO      '
                self.RWnames[4] = 'OF      '
                self.RWnames[5] = 'TO      '
                self.RWnames[6] = 'IN      '
                self.RWnames[7] = 'END     '
                self.RWnames[8] = 'NIL     '
                self.RWnames[9] = 'FOR     '
                self.RWnames[10] = 'NOT     '
                self.RWnames[11] = 'DIV     '
                self.RWnames[12] = 'MOD     '
                self.RWnames[13] = 'AND     '
                self.RWnames[14] = 'SET     '
                self.RWnames[15] = 'VAR     '
                self.RWnames[16] = 'THEN    '
                self.RWnames[17] = 'CASE    '
                self.RWnames[18] = 'WITH    '
                self.RWnames[19] = 'TYPE    '
                self.RWnames[20] = 'FILE    '
                self.RWnames[21] = 'GOTO    '
                self.RWnames[22] = 'ELSE    '
                self.RWnames[23] = 'USES    '
                self.RWnames[24] = 'UNIT    '
                self.RWnames[25] = 'BEGIN   '
                self.RWnames[26] = 'LABEL   '
                self.RWnames[27] = 'WHILE   '
                self.RWnames[28] = 'UNTIL   '
                self.RWnames[29] = 'CONST   '
                self.RWnames[30] = 'ARRAY   '
                self.RWnames[31] = 'DOWNTO  '
                self.RWnames[32] = 'PACKED  '
                self.RWnames[33] = 'RECORD  '
                self.RWnames[34] = 'REPEAT  '
                self.RWnames[35] = 'STRING  '
                self.RWnames[36] = 'PROGRAM '
                self.RWnames[37] = 'METHODS '
                self.RWnames[38] = 'SUBCLASS'
                self.RWnames[39] = 'FUNCTION'
                self.RWnames[40] = 'PROCEDUR'
                self.RWnames[41] = 'INTERFAC'
                self.RWnames[42] = 'IMPLEMEN'
                self.RWnames[43] = 'OTHERWIS'
                self.RWnames[44] = 'INTRINSI'

            def InitRW2() -> None:
                """Populate ``LRWnames`` length-bucket end indices and parallel ``RWsymbol`` token codes."""
                self.LRWnames[0] = 0
                self.LRWnames[1] = 0
                self.LRWnames[2] = 6
                self.LRWnames[3] = 15
                self.LRWnames[4] = 24
                self.LRWnames[5] = 30
                self.LRWnames[6] = 35
                self.LRWnames[7] = 37
                self.LRWnames[8] = 44

                self.RWsymbol[1] = Symbol.IFSY
                self.RWsymbol[2] = Symbol.ORSY
                self.RWsymbol[3] = Symbol.DOSY
                self.RWsymbol[4] = Symbol.OFSY
                self.RWsymbol[5] = Symbol.TOSY
                self.RWsymbol[6] = Symbol.INSY
                self.RWsymbol[7] = Symbol.ENDSY
                self.RWsymbol[8] = Symbol.NILSY
                self.RWsymbol[9] = Symbol.FORSY
                self.RWsymbol[10] = Symbol.NOTSY
                self.RWsymbol[11] = Symbol.DIVSY
                self.RWsymbol[12] = Symbol.MODSY
                self.RWsymbol[13] = Symbol.ANDSY
                self.RWsymbol[14] = Symbol.SETSY
                self.RWsymbol[15] = Symbol.VARSY
                self.RWsymbol[16] = Symbol.THENSY
                self.RWsymbol[17] = Symbol.CASESY
                self.RWsymbol[18] = Symbol.WITHSY
                self.RWsymbol[19] = Symbol.TYPESY
                self.RWsymbol[20] = Symbol.FILESY
                self.RWsymbol[21] = Symbol.GOTOSY
                self.RWsymbol[22] = Symbol.ELSESY
                self.RWsymbol[23] = Symbol.USESSY
                self.RWsymbol[24] = Symbol.UNITSY
                self.RWsymbol[25] = Symbol.BEGINSY
                self.RWsymbol[26] = Symbol.LABELSY
                self.RWsymbol[27] = Symbol.WHILESY
                self.RWsymbol[28] = Symbol.UNTILSY
                self.RWsymbol[29] = Symbol.CONSTSY
                self.RWsymbol[30] = Symbol.ARRAYSY
                self.RWsymbol[31] = Symbol.DOWNTOSY
                self.RWsymbol[32] = Symbol.PACKEDSY
                self.RWsymbol[33] = Symbol.RECORDSY
                self.RWsymbol[34] = Symbol.REPEATSY
                self.RWsymbol[35] = Symbol.STRINGSY
                self.RWsymbol[36] = Symbol.PROGRAMSY
                self.RWsymbol[37] = Symbol.METHSY
                self.RWsymbol[38] = Symbol.SUBCLSY
                self.RWsymbol[39] = Symbol.FUNCTSY
                self.RWsymbol[40] = Symbol.PROCSY
                self.RWsymbol[41] = Symbol.INTERSY
                self.RWsymbol[42] = Symbol.IMPLESY
                self.RWsymbol[43] = Symbol.OTHERSY
                self.RWsymbol[44] = Symbol.INTRINSY

            self.Ch = ' '
            self.pCurLine = -1
            self.CurLine = ''
            self.PrevLine = ''
            self.DotFlag = False
            InitRW1()
            InitRW2()
            for idx in range(256):
                self.ChClass[idx] = Symbol.ERRSY
            for code in range(ord('0'), ord('9') + 1):
                self.ChClass[code] = Symbol.DIGITCL
            for code in range(ord('a'), ord('z') + 1):
                self.ChClass[code] = Symbol.LETCL
            for code in range(ord('A'), ord('Z') + 1):
                self.ChClass[code] = Symbol.LETCL
            self.ChClass[ord('_')] = Symbol.LETCL
            self.ChClass[3] = Symbol.EOFSY
            self.ChClass[9] = Symbol.BLANKCL
            self.ChClass[12] = Symbol.BLANKCL

            self.ChClass[ord(')')] = Symbol.RPARENSY
            self.ChClass[ord(',')] = Symbol.COMMASY
            self.ChClass[ord(';')] = Symbol.SEMISY
            self.ChClass[ord('^')] = Symbol.UPARROWSY
            self.ChClass[ord('[')] = Symbol.LBRACKSY
            self.ChClass[ord(']')] = Symbol.RBRACKSY
            self.ChClass[ord('*')] = Symbol.STARSY
            self.ChClass[ord('+')] = Symbol.PLUSSY
            self.ChClass[ord('-')] = Symbol.MINUSSY
            self.ChClass[ord('/')] = Symbol.SLASHSY
            self.ChClass[ord(' ')] = Symbol.BLANKCL
            self.ChClass[ord('=')] = Symbol.EQSY
            self.ChClass[ord('(')] = Symbol.LPARENSY
            self.ChClass[ord('<')] = Symbol.LTSY
            self.ChClass[ord('>')] = Symbol.GTSY
            self.ChClass[ord('.')] = Symbol.PERIODSY
            self.ChClass[ord(':')] = Symbol.COLONSY
            self.ChClass[ord('@')] = Symbol.ATSIGNSY
            self.ChClass[ord('{')] = Symbol.LBRACECL
            self.ChClass[ord("'")] = Symbol.SCONSTSY
            self.ChClass[ord('$')] = Symbol.DOLLARSY

        def InitStdTypes() -> None:
            """Allocate built-in scalar, subrange, text/interactive file, pointer, string, ``Alfa``, and Clascal types."""
            self.LIntPtr = T(TypeForms.SCALAR)
            self.LIntPtr.FType = False
            self.LIntPtr.Form = TypeForms.SCALAR
            self.LIntPtr.ScalKind = DeclKind.STANDARD
            self.LIntPtr.Bytes = 4
            self.LIntPtr.Bits = 0

            self.IntPtr = T(TypeForms.SUBRANGE)
            self.IntPtr.FType = False
            self.IntPtr.Form = TypeForms.SUBRANGE
            self.IntPtr.RangeOf = self.LIntPtr
            self.IntPtr.Min = -32767 - 1
            self.IntPtr.Max = 32767
            self.IntPtr.Bytes = 2
            self.IntPtr.Bits = 0

            self.SIntPtr = T(TypeForms.SUBRANGE)
            self.SIntPtr.FType = False
            self.SIntPtr.Form = TypeForms.SUBRANGE
            self.SIntPtr.RangeOf = self.LIntPtr
            self.SIntPtr.Min = -128
            self.SIntPtr.Max = 127
            self.SIntPtr.Bytes = 1
            self.SIntPtr.Bits = 0

            self.RealPtr = T(TypeForms.SCALAR)
            self.RealPtr.FType = False
            self.RealPtr.Form = TypeForms.SCALAR
            self.RealPtr.ScalKind = DeclKind.STANDARD
            self.RealPtr.Bytes = 4
            self.RealPtr.Bits = 0

            self.CharPtr = T(TypeForms.SCALAR)
            self.CharPtr.FType = False
            self.CharPtr.Form = TypeForms.SCALAR
            self.CharPtr.ScalKind = DeclKind.STANDARD
            self.CharPtr.Bytes = 1
            self.CharPtr.Bits = 0

            self.BoolPtr = T(TypeForms.SCALAR)
            self.BoolPtr.FType = False
            self.BoolPtr.Form = TypeForms.SCALAR
            self.BoolPtr.ScalKind = DeclKind.DECLARED
            self.BoolPtr.Bytes = 0
            self.BoolPtr.Bits = 1

            self.TextPtr = T(TypeForms.FILES)
            self.TextPtr.FType = True
            self.TextPtr.Form = TypeForms.FILES
            self.TextPtr.FileOf = self.CharPtr
            self.TextPtr.PckdFile = True
            self.TextPtr.Bytes = 602
            self.TextPtr.Bits = 0

            self.InterPtr = T(TypeForms.FILES)
            self.InterPtr.FType = True
            self.InterPtr.Form = TypeForms.FILES
            self.InterPtr.FileOf = self.CharPtr
            self.InterPtr.PckdFile = True
            self.InterPtr.Bytes = 602
            self.InterPtr.Bits = 0

            self.NilPtr = T(TypeForms.POINTERS)
            self.NilPtr.FType = False
            self.NilPtr.Form = TypeForms.POINTERS
            self.NilPtr.PointerTo = None
            self.NilPtr.Bytes = 4
            self.NilPtr.Bits = 0

            self.Str0Ptr = T(TypeForms.SCONST)
            self.Str0Ptr.FType = False
            self.Str0Ptr.Form = TypeForms.SCONST
            self.Str0Ptr.StringLen = 0
            self.Str0Ptr.Bytes = 1
            self.Str0Ptr.Bits = 0

            self.Str1Ptr = self.Str0Ptr.copy()
            self.Str1Ptr.StringLen = 1
            self.Str1Ptr.Bytes = 2

            self.AlfaPtr = T(TypeForms.ARRAYS)
            self.AlfaPtr.Form = TypeForms.ARRAYS
            self.AlfaPtr.PckdArr = True
            self.AlfaPtr.ArrayOf = self.CharPtr
            self.AlfaPtr.BitPackd = True
            self.AlfaPtr.BitsPerEl = 8
            self.AlfaPtr.Bits = 0
            self.AlfaPtr.Bytes = 8
            index_ptr = T(TypeForms.SUBRANGE)
            self.AlfaPtr.IndexedBy = index_ptr
            index_ptr.FType = False
            index_ptr.Form = TypeForms.SUBRANGE
            index_ptr.Min = 1
            index_ptr.Max = 8
            index_ptr.RangeOf = self.IntPtr
            index_ptr.Bits = 4
            index_ptr.Bytes = 0

            self.NilClassPtr = T(TypeForms.CLASSES)
            self.NilClassPtr.Bytes = 4
            self.NilClassPtr.Bits = 0
            self.NilClassPtr.FType = False
            self.NilClassPtr.Form = TypeForms.CLASSES
            self.NilClassPtr.WasDeclared = True
            self.NilClassPtr.SuperClass = None
            self.NilClassPtr.TotalOrder = None
            self.NilClassPtr.ClassLevel = -2
            self.NilClassPtr.SizeInstance = 4
            self.NilClassPtr.LastEvenMethod = 0
            self.NilClassPtr.LastOddMethod = 0
            self.NilClassPtr.MethodOff = 0
            self.NilClassPtr.MethodLevel = 0
            self.NilClassPtr.ItsId = None
            self.NilClassPtr.ClFields = None
            self.NilClassPtr.ClFstField = None
            self.NilClassPtr.ClFstMethod = None

            self.ProcPtr = T(TypeForms.PROCVALUES)
            self.ProcPtr.FType = False
            self.ProcPtr.Form = TypeForms.PROCVALUES
            self.ProcPtr.Bits = 0
            self.ProcPtr.Bytes = 4

        def InitStdNames() -> None:
            """Enter standard type names, ``TRUE``/``FALSE``/``MAXINT``, and ``INPUT``/``OUTPUT`` into scope level 0."""
            lpn = N(NodeKind.IDENTNODE)
            lpn.Name = 'INTEGER '
            lpn.IdType = self.IntPtr
            lpn.Next = None
            lpn.Class = NameClass.TYPES
            lpn.Node = NodeKind.IDENTNODE
            self.EnterId(lpn)

            lpn = N(NodeKind.IDENTNODE)
            lpn.Name = 'LONGINT '
            lpn.IdType = self.LIntPtr
            lpn.Next = None
            lpn.Class = NameClass.TYPES
            lpn.Node = NodeKind.IDENTNODE
            self.EnterId(lpn)

            lpn = N(NodeKind.IDENTNODE)
            lpn.Name = 'REAL    '
            lpn.IdType = self.RealPtr
            lpn.Next = None
            lpn.Class = NameClass.TYPES
            lpn.Node = NodeKind.IDENTNODE
            self.EnterId(lpn)

            lpn = N(NodeKind.IDENTNODE)
            lpn.Name = 'CHAR    '
            lpn.IdType = self.CharPtr
            lpn.Next = None
            lpn.Class = NameClass.TYPES
            lpn.Node = NodeKind.IDENTNODE
            self.EnterId(lpn)

            lpn = N(NodeKind.IDENTNODE)
            lpn.Name = 'BOOLEAN '
            lpn.IdType = self.BoolPtr
            lpn.Next = None
            lpn.Class = NameClass.TYPES
            lpn.Node = NodeKind.IDENTNODE
            self.EnterId(lpn)

            lpn = N(NodeKind.IDENTNODE)
            lpn.Name = 'FALSE   '
            lpn.IdType = self.BoolPtr
            lpn.Next = None
            lpn.Class = NameClass.CONSTS
            lpn.ValueOf.Ivalu = 0
            lpn.Node = NodeKind.IDENTNODE
            self.EnterId(lpn)

            lpn1 = N(NodeKind.IDENTNODE)
            lpn1.Name = 'TRUE    '
            lpn1.IdType = self.BoolPtr
            lpn1.Next = lpn
            lpn1.Class = NameClass.CONSTS
            lpn1.ValueOf.Ivalu = 1
            lpn1.Node = NodeKind.IDENTNODE
            self.EnterId(lpn1)
            assert self.BoolPtr is not None
            self.BoolPtr.MaxConst = lpn1

            lpn = N(NodeKind.IDENTNODE)
            lpn.Name = 'TEXT    '
            lpn.IdType = self.TextPtr
            lpn.Next = None
            lpn.Class = NameClass.TYPES
            lpn.Node = NodeKind.IDENTNODE
            self.EnterId(lpn)

            self.InputPtr = N(NodeKind.IDENTNODE)
            self.InputPtr.Name = 'INPUT   '
            self.InputPtr.IdType = self.TextPtr
            self.InputPtr.Next = None
            self.InputPtr.Class = NameClass.VARS
            self.InputPtr.Vkind = AccessKind.INDRCT
            self.InputPtr.Vlev = 1
            self.InputPtr.Voff = 8
            self.InputPtr.Node = NodeKind.IDENTNODE
            self.InputPtr.UNIVflag = False
            self.EnterId(self.InputPtr)

            self.OutputPtr = N(NodeKind.IDENTNODE)
            self.OutputPtr.Name = 'OUTPUT  '
            self.OutputPtr.IdType = self.TextPtr
            self.OutputPtr.Next = None
            self.OutputPtr.Class = NameClass.VARS
            self.OutputPtr.Vkind = AccessKind.INDRCT
            self.OutputPtr.Vlev = 1
            self.OutputPtr.Voff = 12
            self.OutputPtr.Node = NodeKind.IDENTNODE
            self.OutputPtr.UNIVflag = False
            self.EnterId(self.OutputPtr)

            lpn = N(NodeKind.IDENTNODE)
            lpn.Name = 'MAXINT  '
            lpn.IdType = self.IntPtr
            lpn.Next = None
            lpn.Class = NameClass.CONSTS
            lpn.ValueOf.Ivalu = 32767
            lpn.Node = NodeKind.IDENTNODE
            self.EnterId(lpn)

            lpn = N(NodeKind.IDENTNODE)
            lpn.Name = 'INTERACT'
            lpn.IdType = self.InterPtr
            lpn.Next = None
            lpn.Class = NameClass.TYPES
            lpn.Node = NodeKind.IDENTNODE
            self.EnterId(lpn)

        def DefFormArg(form_name: str, its_type: Optional[T],
                       kind: AccessKind, offset: int) -> N:
            """Build a formal parameter ``IDENTNODE`` for a compiler-synthesized Clascal runtime helper."""
            formal = N(NodeKind.IDENTNODE)
            formal.Name = form_name
            formal.Node = NodeKind.IDENTNODE
            formal.Class = NameClass.VARS
            formal.Vkind = kind
            formal.IdType = its_type
            formal.IsSELF = False
            formal.InRegister = -1
            formal.Vlev = 2
            formal.Voff = offset
            formal.Next = None
            formal.UNIVflag = False
            return formal

        def InitStdProcs() -> None:
            """Register standard procedures by dispatch ``Key`` and define the ``%_CLASS`` Clascal initializer."""
            proc_names = [
                '',
                'NEW     ', 'MARK    ', 'RELEASE ',
                'GET     ', 'PUT     ', 'RESET   ',
                'REWRITE ', 'READ    ', 'READLN  ',
                'WRITE   ', 'WRITELN ', 'PAGE    ',
                'PACK   *', 'UNPACK *', 'CLOSE   ',
                'DELETE  ', 'INSERT  ', 'UNITREAD',
                'UNITWRIT', 'SEEK    ', 'HALT    ',
                'MOVELEFT', 'MOVERIGH', 'FILLCHAR',
                'UNITCLEA', 'GOTOXY  ', 'DISPOSE*',
                'UNITSTAT', 'EXIT    ',
            ]
            for idx in range(1, 30):
                if proc_names[idx][7] != '*':
                    lpn = N(NodeKind.IDENTNODE)
                    lpn.Name = proc_names[idx]
                    lpn.IdType = None
                    lpn.Next = None
                    lpn.Class = NameClass.PROC
                    lpn.PFdeclKind = DeclKind.STANDARD
                    lpn.Key = idx
                    lpn.Node = NodeKind.IDENTNODE
                    self.EnterId(lpn)
                    if idx == 8:
                        self.ReadPtr = lpn
                    if idx == 10:
                        self.WritePtr = lpn

            # PROCEDURE %_Class(ThisCl, SuperCl: Alfa; VAR MasterP: LongInt;
            #                   EvenMethods, OddMethods, ClassSize: Integer);
            self.KlassPtr = N(NodeKind.IDENTNODE)
            self.KlassPtr.Name = '%_CLASS '
            self.KlassPtr.Node = NodeKind.IDENTNODE
            self.KlassPtr.Class = NameClass.PROC
            self.KlassPtr.PFdeclKind = DeclKind.DECLARED
            self.KlassPtr.PFdecl = PFkind.DECL
            self.KlassPtr.IdType = None
            self.KlassPtr.Next = None
            self.KlassPtr.PFlev = 1
            self.KlassPtr.RtnNo = -1
            self.KlassPtr.ParmBytes = 26
            self.KlassPtr.Lc = 16
            a1 = DefFormArg('ThisCl  ', self.AlfaPtr, AccessKind.DRCT, -8)
            a2 = DefFormArg('SuperCl ', self.AlfaPtr, AccessKind.DRCT, -16)
            a3 = DefFormArg('MasterP ', self.LIntPtr, AccessKind.INDRCT, 14)
            a4 = DefFormArg('EvenMeth', self.IntPtr, AccessKind.DRCT, 12)
            a5 = DefFormArg('OddMeth ', self.IntPtr, AccessKind.DRCT, 10)
            a6 = DefFormArg('ClasSize', self.IntPtr, AccessKind.DRCT, 8)
            a1.Next = a2
            a2.Next = a3
            a3.Next = a4
            a4.Next = a5
            a5.Next = a6
            self.KlassPtr.PFargList = a1

        def InitStdFuncs() -> None:
            """Register standard functions by dispatch ``Key`` and define Clascal cast/``INCLASS`` helper signatures."""
            func_names = [
                '',
                'ABS     ', 'ARCTAN  ', 'CHR     ',
                'COS     ', 'EOF     ', 'EOLN    ',
                'EXP     ', 'LN      ', 'ODD     ',
                'ORD     ', 'PRED    ', 'ROUND   ',
                'SIN     ', 'SQR     ', 'SQRT    ',
                'SUCC    ', 'TRUNC   ', 'POINTER ',
                'LENGTH  ', 'POS     ', 'CONCAT  ',
                'COPY    ', 'BLOCKREA', 'BLOCKWRI',
                'IORESULT', 'SIZEOF  ', 'PWROFTEN',
                'SCANEQ  ', 'SCANNE  ', 'UNITBUSY',
                'MEMAVAIL', 'ORD4    ', 'HEAPRESU',
                'KEYPRESS', 'THISCLAS', 'INCLASS ',
            ]
            for idx in range(1, 37):
                if func_names[idx][7] != '*':
                    lpn = N(NodeKind.IDENTNODE)
                    lpn.Name = func_names[idx]
                    lpn.IdType = None
                    lpn.Next = None
                    lpn.Class = NameClass.FUNC
                    lpn.PFdeclKind = DeclKind.STANDARD
                    lpn.Key = idx
                    lpn.Node = NodeKind.IDENTNODE
                    self.EnterId(lpn)

            # FUNCTION %_CkObCn(FromClass: LongInt; VAR ToClass: Alfa): LongInt;
            self.CkObCnPtr = N(NodeKind.IDENTNODE)
            self.CkObCnPtr.Name = '%_CKOBCN'
            self.CkObCnPtr.Node = NodeKind.IDENTNODE
            self.CkObCnPtr.Class = NameClass.FUNC
            self.CkObCnPtr.PFdeclKind = DeclKind.DECLARED
            self.CkObCnPtr.PFdecl = PFkind.DECL
            self.CkObCnPtr.IdType = self.LIntPtr
            self.CkObCnPtr.Next = None
            self.CkObCnPtr.PFlev = 1
            self.CkObCnPtr.RtnNo = -1
            self.CkObCnPtr.ParmBytes = 16
            self.CkObCnPtr.Lc = 8
            a1 = DefFormArg('FromClas', self.LIntPtr, AccessKind.DRCT, 12)
            a2 = DefFormArg('ToClass ', self.AlfaPtr, AccessKind.DRCT, -8)
            a1.Next = a2
            self.CkObCnPtr.PFargList = a1

            # FUNCTION %_CkObCp(FromId: LongInt; VAR ToClass: LongInt): LongInt;
            self.CkObCpPtr = N(NodeKind.IDENTNODE)
            self.CkObCpPtr.Name = '%_CKOBCP'
            self.CkObCpPtr.Node = NodeKind.IDENTNODE
            self.CkObCpPtr.Class = NameClass.FUNC
            self.CkObCpPtr.PFdeclKind = DeclKind.DECLARED
            self.CkObCpPtr.PFdecl = PFkind.DECL
            self.CkObCpPtr.IdType = self.LIntPtr
            self.CkObCpPtr.Next = None
            self.CkObCpPtr.PFlev = 1
            self.CkObCpPtr.RtnNo = -1
            self.CkObCpPtr.ParmBytes = 16
            self.CkObCpPtr.Lc = 0
            a1 = DefFormArg('FromId  ', self.LIntPtr, AccessKind.DRCT, 12)
            a2 = DefFormArg('ToClass ', self.LIntPtr, AccessKind.INDRCT, 8)
            a1.Next = a2
            self.CkObCpPtr.PFargList = a1

            # FUNCTION %_InObCn(Object: LongInt; VAR ClassName: Alfa): Boolean;
            self.InObCnPtr = N(NodeKind.IDENTNODE)
            self.InObCnPtr.Name = '%_INOBCN'
            self.InObCnPtr.Node = NodeKind.IDENTNODE
            self.InObCnPtr.Class = NameClass.FUNC
            self.InObCnPtr.PFdeclKind = DeclKind.DECLARED
            self.InObCnPtr.PFdecl = PFkind.DECL
            self.InObCnPtr.IdType = self.BoolPtr
            self.InObCnPtr.Next = None
            self.InObCnPtr.PFlev = 1
            self.InObCnPtr.RtnNo = -1
            self.InObCnPtr.ParmBytes = 16
            self.InObCnPtr.Lc = 8
            a1 = DefFormArg('Object  ', self.LIntPtr, AccessKind.DRCT, 12)
            a2 = DefFormArg('ClassNam', self.AlfaPtr, AccessKind.DRCT, -8)
            a1.Next = a2
            self.InObCnPtr.PFargList = a1

            # FUNCTION %_InObCp(Object: LongInt; VAR ClassName: LongInt): Boolean;
            self.InObCpPtr = N(NodeKind.IDENTNODE)
            self.InObCpPtr.Name = '%_INOBCP'
            self.InObCpPtr.Node = NodeKind.IDENTNODE
            self.InObCpPtr.Class = NameClass.FUNC
            self.InObCpPtr.PFdeclKind = DeclKind.DECLARED
            self.InObCpPtr.PFdecl = PFkind.DECL
            self.InObCpPtr.IdType = self.BoolPtr
            self.InObCpPtr.Next = None
            self.InObCpPtr.PFlev = 1
            self.InObCpPtr.RtnNo = -1
            self.InObCpPtr.ParmBytes = 16
            self.InObCpPtr.Lc = 0
            a1 = DefFormArg('Object  ', self.LIntPtr, AccessKind.DRCT, 12)
            a2 = DefFormArg('ClassNam', self.LIntPtr, AccessKind.INDRCT, 8)
            a1.Next = a2
            self.InObCpPtr.PFargList = a1

        def InitUnDecl() -> None:
            """Allocate sentinel undeclared ``IDENTNODE`` records used to suppress cascading lookup errors."""
            self.uCstPtr = N(NodeKind.IDENTNODE)
            self.uCstPtr.Name = '        '
            self.uCstPtr.IdType = None
            self.uCstPtr.Class = NameClass.CONSTS
            self.uCstPtr.Llink = None
            self.uCstPtr.Rlink = None
            self.uCstPtr.Next = None
            self.uCstPtr.ValueOf.Ivalu = 0
            self.uCstPtr.Node = NodeKind.IDENTNODE

            self.uTypPtr = N(NodeKind.IDENTNODE)
            self.uTypPtr.Name = '        '
            self.uTypPtr.IdType = None
            self.uTypPtr.Class = NameClass.TYPES
            self.uTypPtr.Llink = None
            self.uTypPtr.Rlink = None
            self.uTypPtr.Next = None
            self.uTypPtr.Node = NodeKind.IDENTNODE

            self.uVarPtr = N(NodeKind.IDENTNODE)
            self.uVarPtr.Name = '        '
            self.uVarPtr.IdType = None
            self.uVarPtr.Class = NameClass.VARS
            self.uVarPtr.Llink = None
            self.uVarPtr.Rlink = None
            self.uVarPtr.Next = None
            self.uVarPtr.Vkind = AccessKind.DRCT
            self.uVarPtr.Vlev = 0
            self.uVarPtr.Voff = 0
            self.uVarPtr.Node = NodeKind.IDENTNODE
            self.uVarPtr.UNIVflag = False

            self.uFldPtr = N(NodeKind.IDENTNODE)
            self.uFldPtr.Name = '        '
            self.uFldPtr.IdType = None
            self.uFldPtr.Class = NameClass.FIELD
            self.uFldPtr.Llink = None
            self.uFldPtr.Rlink = None
            self.uFldPtr.Next = None
            self.uFldPtr.PckdField = False
            self.uFldPtr.FOff = 0
            self.uFldPtr.BitOff = 0
            self.uFldPtr.Node = NodeKind.IDENTNODE

            self.uPrcPtr = N(NodeKind.IDENTNODE)
            self.uPrcPtr.Name = '        '
            self.uPrcPtr.IdType = None
            self.uPrcPtr.Class = NameClass.PROC
            self.uPrcPtr.Llink = None
            self.uPrcPtr.Rlink = None
            self.uPrcPtr.Next = None
            self.uPrcPtr.PFdeclKind = DeclKind.DECLARED
            self.uPrcPtr.PFlev = 0
            self.uPrcPtr.PFargList = None
            self.uPrcPtr.PFdecl = PFkind.DECL
            self.uPrcPtr.Lc = 0
            self.uPrcPtr.RtnNo = -1
            self.uPrcPtr.Node = NodeKind.IDENTNODE

            self.uFctPtr = N(NodeKind.IDENTNODE)
            self.uFctPtr.Name = '        '
            self.uFctPtr.IdType = None
            self.uFctPtr.Class = NameClass.FUNC
            self.uFctPtr.Llink = None
            self.uFctPtr.Rlink = None
            self.uFctPtr.Next = None
            self.uFctPtr.PFdeclKind = DeclKind.DECLARED
            self.uFctPtr.PFlev = 0
            self.uFctPtr.PFargList = None
            self.uFctPtr.PFdecl = PFkind.DECL
            self.uFctPtr.Lc = 0
            self.uFctPtr.RtnNo = -1
            self.uFctPtr.Node = NodeKind.IDENTNODE

        def InitConditional() -> None:
            """Initialize the ``$IFC`` conditional-compilation stack and seed ``CondRoot`` with ``FALSE`` and ``TRUE``."""
            self.CondTos = 0
            self.CondStack[self.CondTos] = CondState.NULL
            self.ParsingOption = False

            self.CondRoot = N()
            self.CondRoot.Name = 'FALSE   '
            self.CondRoot.ValueOf.Ivalu = 0
            self.CondRoot.Llink = None
            tpn = N()
            tpn.Name = 'TRUE    '
            tpn.ValueOf.Ivalu = 1
            tpn.Llink = None
            tpn.Rlink = None
            self.CondRoot.Rlink = tpn

        def ProcessOptions(opts_line: str, what_user_typed: PromptState) -> tuple[str, PromptState]:
            """Parse ``$``-prefixed compiler flags entered at the Workshop ``Input file -`` prompt."""
            length = len(opts_line)
            if length > 2 and opts_line[0] == '$':
                ch2 = self.rt.SUUpCh(opts_line[1])
                if ch2 == 'A':
                    if opts_line[2] in ('+', '-'):
                        self.SaveA2D3 = opts_line[2] == '+'
                        what_user_typed = PromptState.SUInvalid
                    elif length >= 5:
                        opts_line = self.rt.SUUpStr(opts_line)
                        if pcopy(opts_line, 2, 3) == 'ASM':
                            if opts_line[4] in ('+', '-'):
                                self.ShowAsmCode = opts_line[4] == '+'
                                self.NewAsmStatus = self.ShowAsmCode
                                self.AsmListOk = self.ShowAsmCode
                                what_user_typed = PromptState.SUInvalid
                            elif length >= 9:
                                if pcopy(opts_line, 5, 5) == ' ONLY':
                                    self.AsmOnly = True
                                    what_user_typed = PromptState.SUInvalid
                                elif pcopy(opts_line, 5, 5) == ' PROC':
                                    self.AsmProc = True
                                    what_user_typed = PromptState.SUInvalid
                elif ch2 == 'C':
                    if opts_line[2] in ('+', '-'):
                        self.CodeFlag = opts_line[2] == '+'
                        what_user_typed = PromptState.SUInvalid
                elif ch2 == 'D':
                    opts_line = pcopy(opts_line, 3, length - 2)
                    opts_line = self.rt.SUTrimBlanks(opts_line)
                    opts_line, _ = self.rt.SUAddExtension(opts_line, '.TEXT', SUMaxStrLeng)
                    sys.stdout.write(f'Opening debug file {opts_line}\n')
                    self.rt.rewrite_text(self.Debugging, opts_line)
                    self.DebugDebug = not self.rt.IOError(self.rt.io_result, "Can't open debug file")
                    what_user_typed = PromptState.SUInvalid
                elif ch2 == 'E':
                    if opts_line[2] in ('+', '-'):
                        self.CallEditor = opts_line[2] == '+'
                    else:
                        self.ErrFName = pcopy(opts_line, 3, length - 2)
                        self.ErrFName = self.rt.SUTrimBlanks(self.ErrFName)
                        self.ErrFName, _ = self.rt.SUAddExtension(self.ErrFName, '.TEXT', SUMaxStrLeng)
                        sys.stdout.write(f'Opening error file {self.ErrFName}\n')
                        self.ErrFName, _ = self.rt.SUAddExtension(self.ErrFName, '.TEXT', SUMaxStrLeng)
                        self.rt.rewrite_text(self.ErrFile, self.ErrFName)
                        self.ErrFileOpen = not self.rt.IOError(self.rt.io_result, "Can't open error file.")
                    what_user_typed = PromptState.SUInvalid
                elif ch2 == 'G':
                    if opts_line[2] in ('+', '-'):
                        self.CallGen = opts_line[2] == '+'
                        what_user_typed = PromptState.SUInvalid
                elif ch2 == 'L':
                    if opts_line[2] in ('+', '-'):
                        self.ListingOk = opts_line[2] == '+'
                        what_user_typed = PromptState.SUInvalid
                elif ch2 == 'M':
                    if opts_line[2] in ('+', '-'):
                        self.MacFlag = opts_line[2] == '+'
                        self.SaveA2D3 = self.MacFlag
                        what_user_typed = PromptState.SUInvalid
                elif ch2 == 'O':
                    opts_line = self.rt.SUUpStr(opts_line)
                    if length >= 4 and pcopy(opts_line, 2, 2) == 'OV':
                        if opts_line[3] in ('+', '-'):
                            self.OflowFlag = opts_line[3] == '+'
                            what_user_typed = PromptState.SUInvalid
                    if what_user_typed != PromptState.SUInvalid:
                        if length >= 5 and pcopy(opts_line, 2, 3) == 'OPT':
                            if opts_line[4] in ('+', '-'):
                                self.OptFlag = opts_line[4] == '+'
                                self.OptLimFlag = True
                                if length >= 6 and opts_line[5] in ('+', '-'):
                                    self.OptLimFlag = opts_line[5] == '-'
                                what_user_typed = PromptState.SUInvalid
                elif ch2 == 'R':
                    if opts_line[2] in ('+', '-'):
                        self.RangeFlag = opts_line[2] == '+'
                        what_user_typed = PromptState.SUInvalid
            return opts_line, what_user_typed

        # Body of Initialize
        self.Aborted = True
        KCSDefaults()
        self.rt.SUInit()
        self.rt.InitIO()
        self.rt.InitPasDefs()

        self.rt.PCInit()
        self.rt.PCClose(True, 'For Code Gen')
        self.rt.PCClose(True, 'For Editor')
        self.Ecmd = SUEsc + 'E'
        self.Gcmd = SUEsc + 'G'

        # All I-code and debug output packs big-endian explicitly rather than overlaying host RAM.
        self.FlipBytes = False
        self.ErrFileOpen = False
        self.MsgFileOpen = False
        self.CodeOpened = False
        self.DebugOpen = False
        self.DebugDebug = False
        self.TotalLines = 1
        self.Errors = 0
        self.ErrIndex = 0
        self.LastErrLn = -1
        self.EofLn = -1
        self.PrevLn = 0
        self.Forwcount = 0
        self.TopOfOpenFileStack = 0
        self.SaveInbufP = bytearray(InbufByteSize)
        self.ListingFCBP = IOFCB()
        self.ListingBufrP = bytearray(IOByteSize)
        self.ListOpen = False
        self.Listing = False
        self.NewListFile = False
        self.ConsListing = False
        self.ListingOk = True
        self.AsmListOk = True
        self.Pass2Listing = False
        self.NewAsmStatus = False
        self.ShowAsmCode = False
        self.LastLine = 0
        self.OptFlag = True
        self.OptLimFlag = True
        self.RangeFlag = True
        self.CodeFlag = True
        self.OflowFlag = False
        self.CallGen = True if self.build30 else False
        self.CallEditor = False
        self.AsmOnly = False
        self.AsmProc = False
        self.SaveA2D3 = False
        self.MacFlag = False

        date_str = self.rt.GetTD()[:20]
        sys.stdout.write(f'{TITLE}{VERSION}{" " * 23}{date_str}\n')
        sys.stdout.write('\n')

        ilib_what_user_typed = PromptState.SUNone

        while True:
            while True:
                sys.stdout.write('Input file - ')
                self.ObjName, what_user_typed = self.rt.SUGetFN('', '', '.TEXT')
                self.ObjName = self.rt.SUTrimBlanks(self.ObjName)
                if what_user_typed in (PromptState.SUEscape, PromptState.SUDefault, PromptState.SUNone):
                    raise AbortCompilation()
                if what_user_typed == PromptState.SUInvalid:
                    sys.stdout.write('Bad file name')
                if what_user_typed == PromptState.SUOptions:
                    while True:
                        sys.stdout.write('Name for Intrinsic.Lib to use in this Compile: ')
                        self.rt.WhichFile, ilib_what_user_typed = self.rt.SUGetFN('', '', '')
                        if ilib_what_user_typed == PromptState.SUEscape:
                            raise AbortCompilation()
                        if ilib_what_user_typed not in (PromptState.SUValid, PromptState.SUNone):
                            self.KillExec()
                        if ilib_what_user_typed in (PromptState.SUValid, PromptState.SUNone):
                            break
                if what_user_typed not in (PromptState.SUValid, PromptState.SUOptions):
                    self.KillExec()
                self.ObjName, what_user_typed = ProcessOptions(self.ObjName, what_user_typed)
                if what_user_typed == PromptState.SUValid:
                    break
            if not self.OpenNewFile(self.ObjName, InputFileTypes.SOURCE):
                self.rt.IOError(self.rt.io_result, "Can't open file")
                what_user_typed = PromptState.SUInvalid
                self.KillExec()
            if what_user_typed == PromptState.SUValid:
                break

        if ilib_what_user_typed == PromptState.SUNone:
            self.rt.SUInitSysVols()
            self.rt.WhichFile = self.rt.SUOsBootV + '-INTRINSIC.LIB'

        self.SearchLibrary = True
        self.IULibIn = False

        self.FillInbuf()

        if self.ListingOk:
            while True:
                sys.stdout.write('List file - ')
                list_fname, what_user_typed = self.rt.SUGetFN('', '', '.TEXT')
                if what_user_typed == PromptState.SUEscape:
                    raise AbortCompilation()
                if what_user_typed == PromptState.SUInvalid:
                    sys.stdout.write('Bad file name\n')
                    self.KillExec()
                if what_user_typed == PromptState.SUValid:
                    err_code, self.ListingFCBP = self.rt.OpenF(
                        list_fname, self.ListingFCBP, IOModes.IOWrite, self.ListingBufrP
                    )
                    if not self.rt.IOError(err_code, "Can't open file"):
                        self.Listing = True
                        self.ListOpen = True
                        self.ConsListing = self.ListingFCBP.DevType == IODevType.IOConsDev
                        self.NewListFile = self.ListingFCBP.DevType == IODevType.IOBlkDev
                    else:
                        what_user_typed = PromptState.SUInvalid
                        self.KillExec()
                if what_user_typed in (PromptState.SUValid, PromptState.SUNone, PromptState.SUDefault):
                    break

            self.Pass2Listing = self.Listing and self.NewListFile and self.AsmListOk

        vol, name, ext = self.rt.SUSplitFN(self.ObjName)
        def_fname, _ = self.rt.SUMakeFN(vol, name, '')

        while True:
            if self.CallGen:
                sys.stdout.write('Output file - ')
                self.ICodeName, what_user_typed = self.rt.SUGetFN('', def_fname, '.OBJ')
            else:
                sys.stdout.write('I-code file - ')
                self.ICodeName, what_user_typed = self.rt.SUGetFN('', def_fname, '.I')
            if what_user_typed == PromptState.SUEscape:
                raise AbortCompilation()
            if what_user_typed == PromptState.SUInvalid:
                sys.stdout.write('Bad file name\n')
                self.KillExec()
            if what_user_typed in (PromptState.SUValid, PromptState.SUNone, PromptState.SUDefault):
                if self.CallGen:
                    vol, name, ext = self.rt.SUSplitFN(self.ICodeName)
                    self.ICodeName, _ = self.rt.SUMakeFN(vol, name, '.I')
                    self.ObjName = self.ICodeName
                self.rt.rewrite_untyped(self.ICodeFile, self.ICodeName)
                if not self.rt.IOError(self.rt.io_result, "Can't open file"):
                    self.CodeOpened = True
                else:
                    what_user_typed = PromptState.SUInvalid
                    self.KillExec()
            if what_user_typed in (PromptState.SUValid, PromptState.SUNone, PromptState.SUDefault):
                break

        sys.stdout.write('\n')

        self.rt.StartTimer()

        if self.Listing:
            assert self.ListingFCBP is not None
            self.rt.PutStrS(self.ListingFCBP, TITLE + VERSION, 0)
            self.rt.PutStrS(
                self.ListingFCBP,
                ' ',
                79 - len(TITLE) - len(VERSION) - len(date_str),
            )
            self.rt.PutLineS(self.ListingFCBP, date_str)
            self.rt.PutcF(self.ListingFCBP, IONewline)

        self.Level = 0
        self.Top = 0
        d0 = self.Display[0]
        d0.NameTree = None
        d0.Occur = Where.BLK
        d0.Labels = None
        d0.RootLink = None
        d0.ProcBase = 0

        InitScanner()
        InitStdTypes()
        InitStdNames()
        InitStdProcs()
        InitStdFuncs()
        InitUnDecl()

        self.Level = 1
        self.Top = 1
        self.Display[1].ProcBase = 0

        self.PrintErrors = True
        self.IOFlag = True
        self.DbugFlag = True
        self.StkXFlag = True
        self.ForwChkFlag = True
        self.RodFlag = False
        self.ByteNo = 0
        self.BlockNo = 0
        self.LocProcNo = 1
        self.DbgIdx = 0
        self.DbgBlkNum = 0
        self.NumUnits = 1
        self.UnitList = None
        self.InUnit = False
        self.InterFlag = False
        self.InIU = False
        self.InClassDecl = False
        self.InUses = False
        self.HandleCheck = True
        self.NextCrNbr = 0
        self.ClassesToInit = False
        self.UnitsToInit = False
        self.CurrClass = ''
        self.ThisClass = None
        self.UFname = '*SYSLIB.OBJ'
        self.SegName = '        '
        self.ProgName = '        '
        self.SwapFlag = False
        self.Using = False
        self.Left = '-'
        self.Right = '-'
        self.ProcLev = ' '
        self.NestLev = -1
        self.Blanks = ' ' * 80
        InitConditional()
        self.Aborted = False
