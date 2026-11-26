"""Base data structures, constants, and driver for the Lisa Pascal Front End."""

from __future__ import annotations

import enum
import sys
from typing import Optional

from lisalib import (
    AbortCompilation,
    IOFCB,
    IONewline,
    LisaRuntime,
    PasHaltException,
    RegMask,
    TextFile,
    UntypedFile,
    alfa8,
)

TITLE = 'Lisa Pascal Compiler '
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

D1st = D4
Dnth = D7
A1st = A3
Anth = A4

Byte = 1
WORD = 2
LONG = 3

SLinkOffset = 8
MAXREFS = 100
ALFALEN = 8

BuffBlockSize = 16
BuffByteSize = BuffBlockSize * 512

InbufBLockSize = 8
InbufByteSize = InbufBLockSize * 512

MaxErrs = 10
MAXDISPLAY = 16
MAXLEVEL = 8
MAXUNITS = 256
NUMRW = 44
MAXFILES = 5
MaxCondDepth = 20
MAXLNUM = 65100


class Symbol(enum.IntEnum):
    """Lexical token codes and scanner character classes for Lisa Pascal, UCSD units, and Clascal."""

    IDENTSY = 0
    ICONSTSY = 1
    RCONSTSY = 2
    DOSY = 3
    OFSY = 4
    TOSY = 5
    FORSY = 6
    ASSIGNSY = 7
    NILSY = 8
    IFSY = 9
    THENSY = 10
    ELSESY = 11
    DOWNTOSY = 12
    BEGINSY = 13
    ENDSY = 14
    WITHSY = 15
    GOTOSY = 16
    CONSTSY = 17
    VARSY = 18
    TYPESY = 19
    ARRAYSY = 20
    RECORDSY = 21
    SETSY = 22
    FILESY = 23
    FUNCTSY = 24
    PROCSY = 25
    LABELSY = 26
    PACKEDSY = 27
    PROGRAMSY = 28
    STRINGSY = 29
    CASESY = 30
    WHILESY = 31
    UNTILSY = 32
    REPEATSY = 33
    CCONSTSY = 34
    SCONSTSY = 35
    LPARENSY = 36
    RPARENSY = 37
    LBRACKSY = 38
    RBRACKSY = 39
    PERIODSY = 40
    COMMASY = 41
    SEMISY = 42
    COLONSY = 43
    UPARROWSY = 44
    OTHERSY = 45
    # UCSD Symbols
    UNITSY = 46
    USESSY = 47
    INTERSY = 48
    IMPLESY = 49
    INTRINSY = 50
    # Clascal symbols
    SUBCLSY = 51
    METHSY = 52
    # Unary Operators
    ATSIGNSY = 53
    NOTSY = 54
    # Multops
    STARSY = 55
    SLASHSY = 56
    DIVSY = 57
    MODSY = 58
    ANDSY = 59
    # Addops
    PLUSSY = 60
    MINUSSY = 61
    ORSY = 62
    # Relops
    LTSY = 63
    GTSY = 64
    LESY = 65
    GESY = 66
    EQSY = 67
    NESY = 68
    INSY = 69
    # Error and End-of-File symbols
    ERRSY = 70
    EOFSY = 71
    # Character classes
    DOLLARSY = 72
    LBRACECL = 73
    BLANKCL = 74
    LETCL = 75
    DIGITCL = 76


# Standard parser symbol sets (frozen sets of Symbol)
BlockBegSy = frozenset({
    Symbol.LABELSY, Symbol.CONSTSY, Symbol.TYPESY, Symbol.VARSY,
    Symbol.PROCSY, Symbol.FUNCTSY, Symbol.BEGINSY, Symbol.METHSY,
})
ConstBegSys = frozenset({
    Symbol.PLUSSY, Symbol.MINUSSY, Symbol.ICONSTSY, Symbol.RCONSTSY,
    Symbol.SCONSTSY, Symbol.CCONSTSY, Symbol.IDENTSY, Symbol.LPARENSY,
    Symbol.NOTSY, Symbol.LBRACKSY,
})
SimpTypeBegSys = (frozenset({Symbol.LPARENSY}) | ConstBegSys) - frozenset({Symbol.SCONSTSY})
TypeDels = frozenset({
    Symbol.ARRAYSY, Symbol.FILESY, Symbol.RECORDSY,
    Symbol.SETSY, Symbol.STRINGSY, Symbol.SUBCLSY,
})
TypeBegSys = frozenset({Symbol.UPARROWSY, Symbol.PACKEDSY}) | TypeDels | SimpTypeBegSys
SelectSys = frozenset({Symbol.UPARROWSY, Symbol.PERIODSY, Symbol.LBRACKSY})
FacBegSys = frozenset({
    Symbol.ICONSTSY, Symbol.RCONSTSY, Symbol.SCONSTSY, Symbol.CCONSTSY,
    Symbol.IDENTSY, Symbol.LPARENSY, Symbol.LBRACKSY, Symbol.NOTSY,
    Symbol.NILSY, Symbol.ATSIGNSY,
})
StatBegSys = frozenset({
    Symbol.BEGINSY, Symbol.GOTOSY, Symbol.IFSY, Symbol.WHILESY,
    Symbol.REPEATSY, Symbol.FORSY, Symbol.WITHSY, Symbol.CASESY,
})
IdDecBegSys = frozenset({Symbol.LABELSY, Symbol.CONSTSY, Symbol.TYPESY, Symbol.VARSY})
DecBegSys = IdDecBegSys | frozenset({Symbol.PROCSY, Symbol.FUNCTSY})
AllBegSys = BlockBegSy | StatBegSys


class TypeForms(enum.IntEnum):
    """Structural form discriminators for symbol-table type descriptors (``T``)."""

    SCALAR = 0
    SUBRANGE = 1
    CLASSES = 2
    POINTERS = 3
    SETS = 4
    ARRAYS = 5
    RECORDS = 6
    FILES = 7
    TAGFIELD = 8
    VARIANT = 9
    STRINGS = 10
    SCONST = 11
    PROCVALUES = 12


class DeclKind(enum.IntEnum):
    """Distinguishes compiler-predefined intrinsics (``STANDARD``) from user declarations (``DECLARED``)."""

    STANDARD = 0
    DECLARED = 1


class NodeKind(enum.IntEnum):
    """Variant tags for unified symbol-table entries and expression AST nodes (``N``)."""

    IDENTNODE = 0
    UNNODE = 1
    BINNODE = 2
    TRINODE = 3
    CSTNODE = 4
    REGISTER = 5
    ASGNNODE = 6
    CSE = 7


class NameClass(enum.IntEnum):
    """Symbol-table identifier categories for ``IDENTNODE`` records."""

    CONSTS = 0
    TYPES = 1
    VARS = 2
    FIELD = 3
    PROC = 4
    FUNC = 5
    UNITS = 6


class AccessKind(enum.IntEnum):
    """Addressing modes for variables and parameters (``DRCT`` value/local vs. ``INDRCT`` ``VAR`` reference)."""

    DRCT = 0
    INDRCT = 1


class PFkind(enum.IntEnum):
    """Procedure and function declaration flavors, including Clascal methods, ``INLINE``, and ``C`` routines."""

    DECL = 0
    EXTDECL = 1
    FORWDECL = 2
    FORMAL = 3
    METHDECL = 4
    FORWMETHDECL = 5
    INLINEDECL = 6
    CDECL = 7


class UnitKind(enum.IntEnum):
    """Compilation unit linkage flavors (regular, intrinsic, or shared intrinsic)."""

    REGUNIT = 0
    INTRUNIT = 1
    SHARUNIT = 2


class StmtTypes(enum.IntEnum):
    """Statement AST node opcodes (``Stmt.StmtOp``), including control flow, calls, and CSE temporaries."""

    BEGINST = 0
    ASSIGNST = 1
    IFST = 2
    WHILEST = 3
    REPST = 4
    WITHST = 5
    FORTOST = 6
    FORDOWNST = 7
    CALLST = 8
    GOTOST = 9
    CASEST = 10
    CSTMTST = 11
    LABEDST = 12
    METHODCALL = 13
    TEMPST = 14
    NULLST = 15


class Where(enum.IntEnum):
    """Lexical scope kinds stored in ``Display`` entries (block, ``WITH`` record, parameter list, or class)."""

    BLK = 0
    REC = 1
    PARAMS = 2
    KLASS = 3


class CondState(enum.IntEnum):
    """``$IFC``/``$ELSEC``/``$ENDC`` conditional-compilation states (``LOOK*`` compiles, ``MATCH*`` skips)."""

    NULL = 0
    LOOKELSE = 1
    LOOKEND = 2
    MATCHELSE = 3
    MATCHEND = 4


class RegContents(enum.IntEnum):
    """Pass-1 optimizer descriptors for values held in 68000 registers."""

    NADA = 0
    WITHSEL = 1
    GLOBALBASE = 2
    AVARIABLE = 3


class InputFileTypes(enum.IntEnum):
    """Source stream kinds pushed onto ``OpenFileStack`` (``USES`` unit, ``$I`` include, or primary source)."""

    USED = 0
    INCLUDED = 1
    SOURCE = 2


# ---- AST and Symbol Table Records ----

class IntList:
    """Singly linked list of integer constants for ``CASE`` labels and variant-record selector tags."""

    __slots__ = ('IntVal', 'NextInt')

    def __init__(self, val: int = 0, nxt: Optional['IntList'] = None) -> None:
        self.IntVal: int = val
        self.NextInt: Optional['IntList'] = nxt


class T:
    """Symbol table type descriptor.

    Stores allocation size (``Bytes`` and bit-packed ``Bits``), ``FType`` file-containment
    flag, and form-specific attributes for scalars, subranges, pointers, sets, packed/unpacked
    arrays and records, variant tags, files, strings, and Clascal classes.
    """

    def __init__(self, form: TypeForms = TypeForms.SCALAR) -> None:
        self.Bytes: int = 0
        self.Bits: int = 0
        self.Marked: bool = False
        self.FType: bool = False
        self.Form: TypeForms = form
        # SCALAR
        self.ScalKind: DeclKind = DeclKind.STANDARD
        self.MaxConst: Optional['N'] = None
        # SUBRANGE
        self.RangeOf: Optional['T'] = None
        self.Min: int = 0
        self.Max: int = 0
        # POINTERS
        self.PointerTo: Optional['T'] = None
        # SETS
        self.SetOf: Optional['T'] = None
        # ARRAYS
        self.ArrayOf: Optional['T'] = None
        self.IndexedBy: Optional['T'] = None
        self.PckdArr: bool = False
        self.BitPackd: bool = False
        self.BitsPerEl: int = 1
        # RECORDS
        self.PckdRec: bool = False
        self.Fields: Optional['N'] = None
        self.FstField: Optional['N'] = None
        self.VarPart: Optional['T'] = None
        # TAGFIELD
        self.TagName: Optional['N'] = None
        self.Variants: Optional['T'] = None
        # VARIANT
        self.VarFldLst: Optional['N'] = None
        self.NextVar: Optional['T'] = None
        self.SubVar: Optional['T'] = None
        self.VarValus: Optional[IntList] = None
        # FILES
        self.PckdFile: bool = False
        self.FileOf: Optional['T'] = None
        # STRINGS, SCONST
        self.StringLen: int = 0
        # CLASSES
        self.WasDeclared: bool = False
        self.NeedsInit: bool = False
        self.SuperClass: Optional['T'] = None
        self.TotalOrder: Optional['T'] = None
        self.ClassLevel: int = 0
        self.SizeInstance: int = 0
        self.LastOddMethod: int = 0
        self.LastEvenMethod: int = 0
        self.MethodOff: int = 0
        self.MethodLevel: int = 0
        self.ItsId: Optional['N'] = None
        self.ClFields: Optional['N'] = None
        self.ClFstField: Optional['N'] = None
        self.ClFstMethod: Optional['N'] = None
        self.CrProc: Optional['N'] = None

    def copy(self) -> 'T':
        """Return a shallow copy of this type descriptor."""
        t = T(self.Form)
        t.copy_from(self)
        return t

    def copy_from(self, other: 'T') -> None:
        """Overwrite all attributes of this type descriptor from ``other``."""
        self.__dict__.update(other.__dict__)


class LabRec:
    """Block-scoped ``LABEL`` entry mapping a user label number to internal I-code and non-local jump IDs."""

    __slots__ = ('NextLabel', 'LabelNo', 'ILabelNo', 'GlobRefNo', 'Defined')

    def __init__(self) -> None:
        self.NextLabel: Optional['LabRec'] = None
        self.LabelNo: int = 0
        self.ILabelNo: int = 0
        self.GlobRefNo: int = -1
        self.Defined: bool = False


class InlineCode:
    """Singly linked list node holding one 16-bit 68000 machine word for an ``INLINE`` routine."""

    __slots__ = ('InlineWord', 'NextInlineWord')

    def __init__(self, word: int = 0, nxt: Optional['InlineCode'] = None) -> None:
        self.InlineWord: int = word
        self.NextInlineWord: Optional['InlineCode'] = nxt


class StrValRec:
    """Linked 8-character (``Alfa``) chunk of a string or packed character-array literal."""

    __slots__ = ('StrPart', 'Next')

    def __init__(self, part: str = '        ', nxt: Optional['StrValRec'] = None) -> None:
        self.StrPart: str = alfa8(part)
        self.Next: Optional['StrValRec'] = nxt


class SetValRec:
    """Linked 32-element bitset chunk of a constant set literal."""

    __slots__ = ('NextSet', 'SetVal')

    def __init__(self, nxt: Optional['SetValRec'] = None, s: Optional[set[int]] = None) -> None:
        self.NextSet: Optional['SetValRec'] = nxt
        self.SetVal: set[int] = set(s) if s is not None else set()


class Valu:
    """Constant value record storing integer, 32-bit real, chunked string, or chunked set literals."""

    __slots__ = ('Ivalu', 'Rvalu', 'Svalu', 'SvaluLen', 'SetValu', 'MaxSetEl')

    def __init__(self) -> None:
        self.Ivalu: int = 0
        self.Rvalu: float = 0.0
        self.Svalu: Optional[StrValRec] = None
        self.SvaluLen: int = 0
        self.SetValu: Optional[SetValRec] = None
        self.MaxSetEl: int = 0

    def copy(self) -> 'Valu':
        """Return a copy of this constant value record."""
        v = Valu()
        v.set_from(self)
        return v

    def set_from(self, other: 'Valu') -> None:
        """Copy all constant fields from ``other`` into this record."""
        self.Ivalu = other.Ivalu
        self.Rvalu = other.Rvalu
        self.Svalu = other.Svalu
        self.SvaluLen = other.SvaluLen
        self.SetValu = other.SetValu
        self.MaxSetEl = other.MaxSetEl


class N:
    """Symbol table identifier / AST expression node.

    Represents scoped BST symbol-table entries (``IDENTNODE`` for constants, types,
    variables, record fields, routines, and units) as well as expression AST nodes
    (unary/binary/ternary operators, constants, inline assignments, registers, and CSEs).
    Note: LeftArg / LeftPt and TripN / TriPt share properties so code using
    either variant field name accesses the same underlying reference.
    """

    def __init__(self, node: NodeKind = NodeKind.IDENTNODE) -> None:
        self.Node: NodeKind = node
        # IDENTNODE
        self.Name: str = '        '
        self.Llink: Optional['N'] = None
        self.Rlink: Optional['N'] = None
        self.Next: Optional['N'] = None
        self.IdType: Optional[T] = None
        self.Class: NameClass = NameClass.CONSTS
        # CONSTS
        self.ValueOf: Valu = Valu()
        # VARS
        self.Vkind: AccessKind = AccessKind.DRCT
        self.IsSELF: bool = False
        self.UNIVflag: bool = False
        self.InRegister: int = -1
        self.Vlev: int = 0
        self.Voff: int = 0
        # FIELD
        self.FOff: int = 0
        self.PckdField: bool = False
        self.BitOff: int = 0
        # PROC, FUNC
        self.PFdeclKind: DeclKind = DeclKind.DECLARED
        self.Key: int = 1
        self.PFlev: int = 0
        self.PFargList: Optional['N'] = None
        self.PFdecl: PFkind = PFkind.DECL
        self.MethodLevel: int = 0
        self.MethodNo: int = 0
        self.ParmBytes: int = 0
        self.Lc: int = 0
        self.RtnNo: int = -1
        self.InlineCode: Optional[InlineCode] = None
        self.PFOff: int = 0
        # UNITS
        self.Ulev: int = 0
        self.ULc: int = 0
        self.Utop: int = 0
        self.Ukind: UnitKind = UnitKind.REGUNIT
        self.HasClasses: bool = False
        # REGISTER
        self.Reg: int = 0
        self.Load: int = 0
        self.LoadSize: int = 0
        self.LoadExpr: Optional['N'] = None
        # CSE
        self.CSEpN: Optional['N'] = None
        self.CSEIndex: int = 0
        # UNNODE
        self.UnOp: int = 0
        self.UnSubOp: int = 0
        self.UnArg: Optional['N'] = None
        # BINNODE
        self.BinOp: int = 0
        self.BinSubOp: int = 0
        self.RightArg: Optional['N'] = None
        self._left: object = None  # overlaid LeftArg (pN) / LeftPt (pT)
        # TRINODE
        self.TriOp: int = 0
        self.Tri1: Optional['N'] = None
        self.OrigTri1: Optional['N'] = None
        self.Tri2: Optional['N'] = None
        self.TriSuper: Optional[T] = None
        self._tri3: object = None  # overlaid TripN (pN) / TriPt (pT)
        # CSTNODE
        self.CstType: Optional[T] = None
        self.CstValu: Valu = Valu()
        # ASGNNODE
        self.AsgnOp: int = 0
        self.AsgnVar: Optional['N'] = None
        self.AsgnExpr: Optional['N'] = None
        self.AsgnpN: Optional['N'] = None

    @property
    def LeftArg(self) -> Optional['N']:
        """Left child ``N`` operand of a ``BINNODE`` (overlaid with ``LeftPt``)."""
        return self._left

    @LeftArg.setter
    def LeftArg(self, val: Optional['N']) -> None:
        self._left = val

    @property
    def LeftPt(self) -> Optional[T]:
        """Type descriptor ``T`` attached to a ``BINNODE`` such as ``RNGCHK`` (overlaid with ``LeftArg``)."""
        return self._left

    @LeftPt.setter
    def LeftPt(self, val: Optional[T]) -> None:
        self._left = val

    @property
    def TripN(self) -> Optional['N']:
        """Third ``N`` operand of a ``TRINODE`` such as a method target (overlaid with ``TriPt``)."""
        return self._tri3

    @TripN.setter
    def TripN(self, val: Optional['N']) -> None:
        self._tri3 = val

    @property
    def TriPt(self) -> Optional[T]:
        """Array/string type descriptor ``T`` on an ``INDEX`` ``TRINODE`` (overlaid with ``TripN``)."""
        return self._tri3

    @TriPt.setter
    def TriPt(self, val: Optional[T]) -> None:
        self._tri3 = val

    def copy(self) -> 'N':
        """Return a shallow node copy with independent ``Valu`` constant records."""
        n = N(self.Node)
        n.copy_from(self)
        return n

    def copy_from(self, other: 'N') -> None:
        """Copy all attributes and nested ``Valu`` records from ``other`` into this node."""
        self.__dict__.update(other.__dict__)
        self.ValueOf = other.ValueOf.copy()
        self.CstValu = other.CstValu.copy()


class Stmt:
    """Statement AST node.

    Linked via ``NextStmt`` to form statement sequences, carrying source line numbers
    (``StmtNumb``) and variant fields for compound blocks, assignments, loops, conditionals,
    ``WITH`` scopes, calls, ``CASE`` arms, labels, and optimizer CSE temporaries.
    """

    def __init__(self, op: StmtTypes = StmtTypes.NULLST) -> None:
        self.NextStmt: Optional['Stmt'] = None
        self.StmtNumb: int = 0
        self.StmtOp: StmtTypes = op
        # BEGINST
        self.SubSt: Optional['Stmt'] = None
        # METHODCALL, ASSIGNST
        self.AssOp: int = 0
        self.Flippable: bool = False
        self.AssSubOp: int = 0
        self.AssVar: Optional[N] = None
        self.AssExpr: Optional[N] = None
        # FORTOST, FORDOWNST
        self.ForVar: Optional[N] = None
        self.ForInit: Optional[N] = None
        self.ForLimit: Optional[N] = None
        self.ForSt: Optional['Stmt'] = None
        self.ForSize: int = 0
        self.xForVar1: Optional[N] = None
        self.xForVar2: Optional[N] = None
        # IFST
        self.IfExpr: Optional[N] = None
        self.ThenSt: Optional['Stmt'] = None
        self.ElseSt: Optional['Stmt'] = None
        # WITHST
        self.WithVar: Optional[N] = None
        self.WithBody: Optional['Stmt'] = None
        # REPST, WHILEST
        self.CondExpr: Optional[N] = None
        self.LoopStmt: Optional['Stmt'] = None
        # CALLST
        self.ProcpN: Optional[N] = None
        self.pArgList: Optional[N] = None
        # GOTOST
        self.GotoLab: Optional[LabRec] = None
        self.LabLev: int = 0
        # CASEST
        self.CaseExpr: Optional[N] = None
        self.CStmtList: Optional['Stmt'] = None
        self.OtherStmt: Optional['Stmt'] = None
        # CSTMTST
        self.CaseVals: Optional[IntList] = None
        self.ThisCase: Optional['Stmt'] = None
        # LABEDST
        self.StLab: Optional[LabRec] = None
        self.LabStmt: Optional['Stmt'] = None
        # TEMPST
        self.TempNode: Optional[N] = None
        self.TempLevel: int = 0
        self.TempCSEregs: RegMask = RegMask()

    def copy(self) -> 'Stmt':
        """Return a shallow copy of this statement node with an independent ``TempCSEregs`` mask."""
        s = Stmt(self.StmtOp)
        s.copy_from(self)
        return s

    def copy_from(self, other: 'Stmt') -> None:
        """Copy all fields from ``other`` into this statement node."""
        self.__dict__.update(other.__dict__)
        self.TempCSEregs = other.TempCSEregs.copy()


class Attr:
    """Synthesized expression attribute carrying size code (``ASize``), static type (``Typtr``), and AST (``TreePtr``)."""

    __slots__ = ('ASize', 'Typtr', 'TreePtr')

    def __init__(self, asize: int = 0, typtr: Optional[T] = None, tree_ptr: Optional[N] = None) -> None:
        self.ASize: int = asize
        self.Typtr: Optional[T] = typtr
        self.TreePtr: Optional[N] = tree_ptr

    def copy(self) -> 'Attr':
        """Return a shallow copy of this expression attribute."""
        return Attr(self.ASize, self.Typtr, self.TreePtr)

    def set_from(self, other: 'Attr') -> None:
        """Copy ``ASize``, ``Typtr``, and ``TreePtr`` from ``other``."""
        self.ASize = other.ASize
        self.Typtr = other.Typtr
        self.TreePtr = other.TreePtr


class VarRef:
    """Per-procedure variable reference count entry used by the pass-1 register allocator."""

    __slots__ = ('PVar', 'Refs')

    def __init__(self) -> None:
        self.PVar: Optional[N] = None
        self.Refs: int = 0


class RegDesc:
    """Pass-1 optimizer descriptor tracking what value a 68000 register currently holds."""

    __slots__ = ('Contents', 'RLevel', 'PVar')

    def __init__(self) -> None:
        self.Contents: RegContents = RegContents.NADA
        self.RLevel: int = 0
        self.PVar: Optional[N] = None

    def copy(self) -> 'RegDesc':
        """Return a copy of this register descriptor."""
        r = RegDesc()
        r.Contents = self.Contents
        r.RLevel = self.RLevel
        r.PVar = self.PVar
        return r

    def set_from(self, other: 'RegDesc') -> None:
        """Copy register tracking state from ``other``."""
        self.Contents = other.Contents
        self.RLevel = other.RLevel
        self.PVar = other.PVar


class ErrRecord:
    """Diagnostic entry accumulated for the current source line (column position, error number, identifier)."""

    __slots__ = ('Pos', 'Nbr', 'Name')

    def __init__(self, pos: int = 0, nbr: int = 0, name: str = '        ') -> None:
        self.Pos: int = pos
        self.Nbr: int = nbr
        self.Name: str = alfa8(name)

    def copy(self) -> 'ErrRecord':
        """Return a copy of this line error record."""
        return ErrRecord(self.Pos, self.Nbr, self.Name)


class OpenFileEntry:
    """Saved file handle, input buffer cursors, line counters, and pending diagnostics for nested source files."""

    def __init__(self) -> None:
        self.LastRelBlkRead: int = 0
        self.NextChToRead: int = 0
        self.LastValidByte: int = 0
        self.NumValidBlocks: int = 0
        self.LineNbr: int = 0
        self.PrevLnbr: int = 0
        self.FName: str = ''
        self.SrcFile: UntypedFile = UntypedFile()
        self.SrcEolSource: bool = False
        self.BufSaved: bool = False
        self.LPrinted: bool = False
        self.ErrIdx: int = 0
        self.ErrLst: list[ErrRecord] = [ErrRecord() for _ in range(MaxErrs + 1)]  # 1..10
        self.pCurL: int = 0
        self.CurL: str = ''
        self.PrevL: str = ''


class DisplayEntry:
    """Lexical scope display-stack frame holding a scope's symbol BST, block labels, ``WITH`` record, or class."""

    def __init__(self) -> None:
        self.NameTree: Optional[N] = None
        self.Occur: Where = Where.BLK
        # BLK
        self.ProcBase: int = 0
        self.Labels: Optional[LabRec] = None
        self.ExitLabel: Optional[LabRec] = None
        self.RootLink: Optional[N] = None
        # REC
        self.RecPckd: bool = False
        self.RecAcc: AccessKind = AccessKind.DRCT
        self.RecLevel: int = 0
        # KLASS
        self.KType: Optional[T] = None
        self.WVar: Optional[N] = None


class WithRefEntry:
    """Optimizer tracking entry for active ``WITH`` statements, counting indirect references and pointer mutation."""

    __slots__ = ('Refs', 'Indirect', 'PUpArrow', 'EverChange')

    def __init__(self) -> None:
        self.Refs: int = 0
        self.Indirect: bool = False
        self.PUpArrow: Optional[N] = None
        self.EverChange: bool = False


class PascalCompilerBase:
    """Holds all global state of the Pascal compiler and the main/finalize lifecycle."""

    def __init__(self, rt: LisaRuntime, build30: bool = True) -> None:
        """Allocate default scanner, symbol-table, I/O, ``Display``, I-code, debug, and optimizer state."""
        self.rt: LisaRuntime = rt
        self.build30: bool = build30

        self.Token: Symbol = Symbol.ERRSY
        self.Ident: str = '        '
        self.IntVal: int = 0
        self.RealVal: float = 0.0
        self.StrVal: Optional[StrValRec] = None
        self.Ch: str = ' '
        self.DotDot: bool = False
        self.DotFlag: bool = False

        self.ChClass: list[Symbol] = [Symbol.ERRSY] * 256
        self.RWsymbol: list[Symbol] = [Symbol.ERRSY] * (NUMRW + 1)  # 1..44
        self.RWnames: list[str] = ['        '] * (NUMRW + 1)       # 1..44
        self.LRWnames: list[int] = [0] * 9                          # 0..8

        self.IntPtr: Optional[T] = None
        self.SIntPtr: Optional[T] = None
        self.LIntPtr: Optional[T] = None
        self.RealPtr: Optional[T] = None
        self.CharPtr: Optional[T] = None
        self.BoolPtr: Optional[T] = None
        self.TextPtr: Optional[T] = None
        self.InterPtr: Optional[T] = None
        self.NilPtr: Optional[T] = None
        self.Str0Ptr: Optional[T] = None
        self.Str1Ptr: Optional[T] = None
        self.AlfaPtr: Optional[T] = None

        self.uCstPtr: Optional[N] = None
        self.uTypPtr: Optional[N] = None
        self.uVarPtr: Optional[N] = None
        self.uFldPtr: Optional[N] = None
        self.uPrcPtr: Optional[N] = None
        self.uFctPtr: Optional[N] = None

        self.OutputPtr: Optional[N] = None
        self.InputPtr: Optional[N] = None
        self.ReadPtr: Optional[N] = None
        self.WritePtr: Optional[N] = None

        self.KlassPtr: Optional[N] = None
        self.CkObCpPtr: Optional[N] = None
        self.CkObCnPtr: Optional[N] = None
        self.InObCpPtr: Optional[N] = None
        self.InObCnPtr: Optional[N] = None

        self.TopOfOpenFileStack: int = 0
        self.OpenFileStack: list[OpenFileEntry] = [OpenFileEntry() for _ in range(MAXFILES + 1)]  # 1..5

        self.InbufP: int = 0
        self.InbufLastValidByte: int = 0
        self.InbufNumValidBlocks: int = 0
        self.Inbuf: bytearray = bytearray(InbufByteSize)
        self.EolSource: bool = False
        self.SaveInbufP: bytearray = bytearray(InbufByteSize)

        self.ListingFCBP: Optional[IOFCB] = None
        self.ListingBufrP: Optional[bytearray] = None
        self.ListingOk: bool = True
        self.ListOpen: bool = False
        self.Listing: bool = False
        self.ConsListing: bool = False
        self.LinePrinted: bool = False
        self.AsmListOk: bool = True
        self.ShowAsmCode: bool = False
        self.NewListFile: bool = False
        self.NewAsmStatus: bool = False
        self.Pass2Listing: bool = False
        self.LineNumber: int = 0
        self.TotalLines: int = 1
        self.CurLine: str = ''
        self.PrevLine: str = ''
        self.pCurLine: int = -1
        self.PrevLn: int = 0
        self.LastLine: int = 0
        self.Left: str = '-'
        self.Right: str = '-'
        self.ProcLev: str = ' '
        self.NestLev: int = -1
        self.Blanks: str = ' ' * 80
        self.ShowPStr: str = ''

        self.Errors: int = 0
        self.ErrFile: TextFile = TextFile()
        self.ErrFName: str = ''
        self.ErrFileOpen: bool = False
        self.ErrIndex: int = 0
        self.ErrList: list[ErrRecord] = [ErrRecord() for _ in range(MaxErrs + 1)]  # 1..10
        self.LastErrLn: int = -1
        self.EofLn: int = -1
        self.EofLine: str = ''
        self.MsgFile: UntypedFile = UntypedFile()
        self.MsgFileOpen: bool = False
        self.Aborted: bool = True

        self.IOFlag: bool = True
        self.RangeFlag: bool = True
        self.OflowFlag: bool = False
        self.RodFlag: bool = False
        self.ForwChkFlag: bool = True
        self.CodeFlag: bool = True
        self.DbugFlag: bool = True
        self.StkXFlag: bool = True
        self.OptFlag: bool = True
        self.OptLimFlag: bool = True
        self.SwapFlag: bool = False
        self.CallGen: bool = True if build30 else False
        self.CallEditor: bool = False

        self.PrintErrors: bool = True
        self.InClassDecl: bool = False
        self.FlipBytes: bool = False
        self.InUnit: bool = False
        self.Using: bool = False
        self.InUses: bool = False
        self.InterFlag: bool = False

        self.AsmOnly: bool = False
        self.AsmProc: bool = False
        self.SaveA2D3: bool = False
        self.MacFlag: bool = False

        self.Ecmd: str = '\x1bE'
        self.Gcmd: str = '\x1bG'

        self.CurrentProc: Optional[N] = None
        self.HeapMark: int = 0
        self.ProcStmt: Optional[Stmt] = None

        self.SearchLibrary: bool = True
        self.IULibIn: bool = False

        self.UFname: str = '*SYSLIB.OBJ'
        self.NumUnits: int = 1
        self.InIU: bool = False
        self.FirstUBlock: int = 0
        self.FirstUByte: int = 0
        self.LastUBlock: int = 0
        self.LastUByte: int = 0
        self.IntFName: str = ''

        self.ForwPList: Optional[N] = None

        self.Level: int = 0
        self.Disx: int = 0
        self.Top: int = 0
        self.Display: list[DisplayEntry] = [DisplayEntry() for _ in range(MAXDISPLAY + 1)]  # 0..16

        self.gAttr: Attr = Attr()

        self.HandleCheck: bool = True
        self.WithDHandle: int = 0
        self.ExprDHandle: int = 0
        self.LHSDHandle: int = 0

        self.ThisClass: Optional[T] = None
        self.CurrClass: str = ''
        self.NextCrNbr: int = 0
        self.ProcPtr: Optional[T] = None
        self.NilClassPtr: Optional[T] = None
        self.ForwCList: Optional[N] = None

        self.CodeOpened: bool = False
        self.ICodeFile: UntypedFile = UntypedFile()
        self.Buff: bytearray = bytearray(BuffByteSize)
        self.ByteNo: int = 0
        self.BlockNo: int = 0

        self.ICodeName: str = ''
        self.ObjName: str = ''

        self.LocProcNo: int = 1
        self.UnitList: Optional[N] = None
        self.UnitsToInit: bool = False
        self.ClassesToInit: bool = False

        self.SegName: str = '        '
        self.ProgName: str = '        '

        self.DebugDebug: bool = False
        self.Debugging: TextFile = TextFile()
        self.DebugOpen: bool = False
        self.DebugFile: UntypedFile = UntypedFile()
        self.DbgBuf: bytearray = bytearray(512)
        self.DbgIdx: int = 0
        self.DbgBlkNum: int = 0

        self.CondTos: int = 0
        self.CondStack: list[CondState] = [CondState.NULL] * (MaxCondDepth + 1)
        self.CondRoot: Optional[N] = None
        self.ParsingOption: bool = False
        self.RBrackChar: str = '}'

        self.RegMask: RegMask = RegMask()
        self.WithLevel: int = 0
        self.WithRefs: list[WithRefEntry] = [WithRefEntry() for _ in range(MAXDISPLAY + 1)]
        self.iGlobalRefs: list[int] = [0] * (MAXDISPLAY + 1)
        self.sGlobalRefs: list[int] = [0] * (MAXUNITS + 1)
        self.CurRefs: int = 0
        self.VarRefs: list[VarRef] = [VarRef() for _ in range(MAXREFS + 1)]

        self.GlobalRegisters: list[RegDesc] = [RegDesc() for _ in range(16)]
        self.CurRegisters: list[RegDesc] = [RegDesc() for _ in range(16)]

        self.GlobFlippable: bool = False
        self.HasGlobalLabel: bool = False
        self.Forwcount: int = 0

    def run(self) -> int:
        """Run pass-1 compilation: prompt/initialize, parse and emit I-code, flush errors, and finalize."""
        try:
            self.Initialize()
            self.CallProg()
            self.rt.MarkTime()
            if self.ErrIndex == 0:
                if self.Listing and self.ListingFCBP is not None:
                    self.rt.PutcF(self.ListingFCBP, IONewline)
                    self.rt.PutLineS(self.ListingFCBP, self.rt.ReportTime())
                if not self.ConsListing:
                    sys.stdout.write('\n' + self.rt.ReportTime() + '\n')
        except AbortCompilation:
            pass
        except PasHaltException:
            return 1  # a fatal error

        # 999:
        if self.ErrIndex != 0:
            try:
                self.LinePrinted = True
                self.EolSource = True
                self.InbufP = 0
                self.Inbuf[0] = 32  # ' '
                self.InbufLastValidByte = 1
                self.NextCh()
            except AbortCompilation:
                pass

        self.Finalize()
        # The exit status: 1 when the compilation reported errors or was aborted
        return 1 if self.Aborted or self.Errors != 0 else 0
