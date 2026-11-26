# `OBJIOLIB` (`ObjIOLib.obj`) — Workshop Object File, Intrinsic Unit Manager & Data Structure Library

[Back to Library Index](LIBRARIES.md)

Lisa Workshop compiler/linker support library for reading and writing `.OBJ` files (`ObjIO`), managing `INTRINSIC.LIB` (`IUMan`), buffered file I/O (`FileIO`), segmented pools (`MemMan`), and compiler data structures (`Lists`, `Trees`, `Graphs`, `Parts`, `Refs`, `PasDefs`).

- **Object file**: `libs/workshop3.0/ObjIOLib.obj` (Intrinsic library)
- **Contents**: 10 units, 135 top-level procedures/functions

## Importing and Linking

```pascal
USES FileIO, Graphs, IUMan;
```

```sh
pascal/lpc.py --link=IOSPASLIB,OBJIOLIB MYPROG
```

## Units in This Library

| Unit | 8-Char Symbol | `USES` Dependencies | Routines | Summary |
|---|---|---|---|---|
| [`FileIO`](#unit-fileio) | `FILEIO` | `PasDefs`, `MemMan` | 25 | Provides block-buffered binary stream I/O with random byte positioning, big-endian byte/word/longint transfers, memory peek/poke helpers, hexadecimal formatting, and 16-bit bitwise integer operations. |
| [`Graphs`](#unit-graphs) | `GRAPHS` | `PasDefs`, `MemMan`, `Lists` | 23 | Implements dynamic directed and undirected graph data structures backed by MemMan and Lists, supporting vertex and arc creation, incidence/adjacency iteration, directed depth-first search, and undirected breadth-first search. |
| [`IUMan`](#unit-iuman) | `IUMAN` | `StdUnit`, `PasDefs`, `MemMan`, `FileIO`, `ObjIO` | 14 | Manages Lisa OS intrinsic unit library directories (INTRINSIC.LIB), reading and writing unit/segment location tables, file string tables, and dotted 4-part system version records, as well as installing units and copying compact interface text. |
| [`Lists`](#unit-lists) | `LISTS` | `PasDefs`, `MemMan` | 10 | Provides generic singly linked list operations parameterized by caller-supplied link-accessor and ordering callbacks, used to thread integer-indexed records in Graphs, Parts, and Refs. |
| [`MemMan`](#unit-memman) | `MEMMAN` | `PasDefs` | 9 | Implements a segmented 256-slot-per-row index allocator and checked heap-allocation helpers used by Workshop compiler and linker data structures. |
| [`ObjIO`](#unit-objio) | `OBJIO` | `PasDefs`, `FileIO` | 25 | Reads and writes Apple Lisa object, executable, and intrinsic library files composed of typed invariant header blocks and variant record arrays. |
| [`Parts`](#unit-parts) | `PARTS` | `PasDefs`, `MemMan`, `Lists` | 11 | Implements disjoint set partitions grouping integer members into equivalence classes backed by dynamically expandable row tables and linked member lists. |
| [`PasDefs`](#unit-pasdefs) | `PASDEFS` | `StdUnit` | 6 | Defines core Lisa Pascal Workshop compiler and tool types, listing file state, error counters, and diagnostic warning, error, and fatal-abort reporting routines. |
| [`Refs`](#unit-refs) | `REFS` | `PasDefs`, `MemMan`, `Lists` | 7 | Manages dynamically expandable singly linked lists of integer reference locations indexed by symbol or entity head IDs for linker and object-file tools. |
| [`Trees`](#unit-trees) | `TREES` | `PasDefs`, `MemMan` | 5 | Implements dynamically expandable binary search trees of 8-character identifier names with lookup, insertion, and in-order traversal. |

---

## Unit FileIO

Provides block-buffered binary stream I/O with random byte positioning, big-endian byte/word/longint transfers, memory peek/poke helpers, hexadecimal formatting, and 16-bit bitwise integer operations.

- **Import**: `USES FileIO;`
- **Interface dependencies**: `PasDefs`, `MemMan`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `InitFile` | `PROCEDURE InitFile(VAR FilePtr: FileHandle; nBlocks: Integer);` | Allocates and initializes a FileDesc descriptor in FilePtr with a block buffer of nBlocks 512-byte blocks (requiring at least 2 blocks). |
| `IAnd` | `FUNCTION IAnd(I, J: Integer): Integer;` | Returns the 16-bit bitwise AND of integers I and J. |
| `IOr` | `FUNCTION IOr(I, J: Integer): Integer;` | Returns the 16-bit bitwise inclusive OR of integers I and J. |
| `IXOr` | `FUNCTION IXOr(I, J: Integer): Integer;` | Returns the 16-bit bitwise exclusive OR (XOR) of integers I and J. |
| `INot` | `FUNCTION INot(I: Integer): Integer;` | Returns the 16-bit bitwise one's complement (NOT) of integer I. |
| `PeekB` | `FUNCTION PeekB(P: Ptr; SkipB: Integer): Byte;` | Reads and returns the unsigned byte (0..255) located SkipB bytes past memory pointer P. |
| `PokeB` | `PROCEDURE PokeB(P: Ptr; SkipB: Integer; B: Byte);` | Writes unsigned byte B (0..255) to the memory address SkipB bytes past pointer P. |
| `ToHex` | `PROCEDURE ToHex(P: Ptr; SkipN, NrN: Integer; VAR S: LString);` | Converts NrN 4-bit nibbles starting at nibble offset SkipN from pointer P (high nibble first) into uppercase hexadecimal string S. |
| `WriteHex` | `PROCEDURE WriteHex(VAR F: Text; P: Ptr; SkipN, NrN: Integer);` | Writes NrN 4-bit nibbles starting at nibble offset SkipN from pointer P as uppercase hexadecimal digits to text file F. |
| `OpenFile` | `PROCEDURE OpenFile(VAR FilePtr: FileHandle; FileName: LString; NewFile: boolean);` | Opens existing binary file FileName (when NewFile is FALSE) or creates/rewrites it (when NewFile is TRUE) and associates it with buffered descriptor FilePtr. |
| `ZeroFileEnd` | `PROCEDURE ZeroFileEnd(FilePtr: FileHandle);` | Pads FilePtr with zero bytes from its current byte position up to the next 512-byte block boundary. |
| `CloseFile` | `PROCEDURE CloseFile(FilePtr: FileHandle; Save: boolean);` | Flushes any dirty buffer and closes FilePtr, locking/saving the file when Save is TRUE or purging a newly created file when Save is FALSE. |
| `GetFilePtr` | `PROCEDURE GetFilePtr(FilePtr: FileHandle; VAR BytePtr: LongInt);` | Returns the current 0-based byte read/write offset of FilePtr in BytePtr. |
| `SetFilePtr` | `PROCEDURE SetFilePtr(FilePtr: FileHandle; BytePtr: LongInt);` | Positions FilePtr's read/write pointer to absolute byte offset BytePtr, extending a new file with zero blocks if necessary. |
| `SkipBytes` | `PROCEDURE SkipBytes(FilePtr: FileHandle; NrBytes: LongInt);` | Advances or rewinds FilePtr's current byte position by signed offset NrBytes. |
| `FileEOF` | `FUNCTION FileEOF(FilePtr: FileHandle): boolean;` | Returns TRUE if FilePtr's read/write position has reached end-of-file. |
| `CopySeq` | `PROCEDURE CopySeq(InFile, OutFile: FileHandle; NrBytes: LongInt);` | Copies NrBytes sequential bytes from current position in InFile to current position in OutFile. |
| `GetSeq` | `PROCEDURE GetSeq(FilePtr: FileHandle; Stuff: Ptr; NrBytes: LongInt);` | Reads NrBytes sequential bytes from FilePtr into memory buffer Stuff (zero-filling any trailing bytes past EOF). |
| `GetByte` | `PROCEDURE GetByte(FilePtr: FileHandle; VAR B: Byte);` | Reads one unsigned byte (0..255) from FilePtr into B and advances the file position by 1. |
| `GetWord` | `PROCEDURE GetWord(FilePtr: FileHandle; VAR W: Integer);` | Reads a big-endian 16-bit signed integer from FilePtr into W and advances the file position by 2. |
| `GetLong` | `PROCEDURE GetLong(FilePtr: FileHandle; VAR L: LongInt);` | Reads a big-endian 32-bit signed LongInt from FilePtr into L and advances the file position by 4. |
| `PutSeq` | `PROCEDURE PutSeq(FilePtr: FileHandle; Stuff: Ptr; NrBytes: LongInt);` | Writes NrBytes sequential bytes from memory buffer Stuff to FilePtr at its current byte position. |
| `PutByte` | `PROCEDURE PutByte(FilePtr: FileHandle; B: Byte);` | Writes unsigned byte B (0..255) to FilePtr and advances the file position by 1. |
| `PutWord` | `PROCEDURE PutWord(FilePtr: FileHandle; W: Integer);` | Writes 16-bit integer W in big-endian byte order to FilePtr and advances the file position by 2. |
| `PutLong` | `PROCEDURE PutLong(FilePtr: FileHandle; L: LongInt);` | Writes 32-bit LongInt L in big-endian byte order to FilePtr and advances the file position by 4. |

---

## Unit Graphs

Implements dynamic directed and undirected graph data structures backed by MemMan and Lists, supporting vertex and arc creation, incidence/adjacency iteration, directed depth-first search, and undirected breadth-first search.

- **Import**: `USES Graphs;`
- **Interface dependencies**: `PasDefs`, `MemMan`, `Lists`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `AddArc` | `PROCEDURE AddArc(graph: GraphHandle; init, term: Vertex; VAR newA: Arc; FUNCTION GetMore(n, row: integer): boolean);` | Allocates a new directed arc in graph from vertex init to vertex term (expanding arc storage via GetMore if needed), links it into init's outgoing and term's incoming lists, and returns it in newA. |
| `AddVertex` | `PROCEDURE AddVertex(graph: GraphHandle; VAR newV: Vertex; FUNCTION GetMore(n, row: integer): boolean);` | Allocates a new isolated vertex in graph (expanding vertex storage via GetMore if needed), initializes its incoming and outgoing arc lists, and returns it in newV. |
| `DeleteArc` | `PROCEDURE DeleteArc(graph: GraphHandle; oldArc: Arc);` | Unlinks oldArc from its initial vertex's outgoing list and terminal vertex's incoming list in graph and frees oldArc's index. |
| `DeleteVertex` | `PROCEDURE DeleteVertex(graph: GraphHandle; oldVertex: Vertex);` | Frees isolated vertex oldVertex from graph, or reports an error if oldVertex still has incident arcs. |
| `FindArc` | `FUNCTION FindArc(graph: GraphHandle; init, term: Vertex): Arc;` | Searches outgoing arcs of vertex init in graph for an arc to vertex term and returns its Arc index (or NullItem if none exists). |
| `OppositeVertex` | `FUNCTION OppositeVertex(graph: GraphHandle; a: Arc; oneVertex: Vertex): Vertex;` | Returns the endpoint of arc a opposite to oneVertex in graph, reporting an error if oneVertex is neither endpoint of a. |
| `InitVertex` | `FUNCTION InitVertex(graph: GraphHandle; a: Arc): Vertex;` | Returns the initial (tail/source) vertex of directed arc a in graph. |
| `TermVertex` | `FUNCTION TermVertex(graph: GraphHandle; a: Arc): Vertex;` | Returns the terminal (head/target) vertex of directed arc a in graph. |
| `IsSource` | `FUNCTION IsSource(graph: GraphHandle; v: Vertex): boolean;` | Returns TRUE if vertex v in graph has no incoming arcs. |
| `IsSink` | `FUNCTION IsSink(graph: GraphHandle; v: Vertex): boolean;` | Returns TRUE if vertex v in graph has no outgoing arcs. |
| `IsIsolated` | `FUNCTION IsIsolated(graph: GraphHandle; v: Vertex): boolean;` | Returns TRUE if vertex v in graph has neither incoming nor outgoing arcs. |
| `EachVertex` | `PROCEDURE EachVertex(graph: GraphHandle; PROCEDURE Visit(v: Vertex));` | Invokes callback Visit(v) for every currently allocated vertex v in graph. |
| `EachArc` | `PROCEDURE EachArc(graph: GraphHandle; PROCEDURE Visit(a: Arc));` | Invokes callback Visit(a) for every currently allocated arc a in graph. |
| `EachInArc` | `PROCEDURE EachInArc(graph: GraphHandle; v: Vertex; PROCEDURE Visit(inArc: Arc));` | Invokes callback Visit(inArc) for each arc directed into vertex v in graph. |
| `EachOutArc` | `PROCEDURE EachOutArc(graph: GraphHandle; v: Vertex; PROCEDURE Visit(outArc: Arc));` | Invokes callback Visit(outArc) for each arc directed out of vertex v in graph. |
| `EachIncidentArc` | `PROCEDURE EachIncidentArc(graph: GraphHandle; v: Vertex; PROCEDURE Visit(incidentArc: Arc));` | Invokes callback Visit(incidentArc) for every incoming and outgoing arc incident on vertex v in graph. |
| `EachPredecessorVertex` | `PROCEDURE EachPredecessorVertex(graph: GraphHandle; v: Vertex; PROCEDURE Visit(predecessor: Vertex));` | Invokes callback Visit(predecessor) for the initial vertex of each incoming arc of vertex v in graph. |
| `EachSuccessorVertex` | `PROCEDURE EachSuccessorVertex(graph: GraphHandle; v: Vertex; PROCEDURE Visit(successor: Vertex));` | Invokes callback Visit(successor) for the terminal vertex of each outgoing arc of vertex v in graph. |
| `EachAdjacentVertex` | `PROCEDURE EachAdjacentVertex(graph: GraphHandle; v: Vertex; PROCEDURE Visit(adjacent: Vertex));` | Invokes callback Visit(adjacent) for every predecessor and successor vertex adjacent to vertex v in graph. |
| `InitGLists` | `PROCEDURE InitGLists;` | Initializes the shared ListOpsRec link-accessor callback tables used for graph incoming and outgoing arc lists. |
| `InitGraph` | `PROCEDURE InitGraph(VAR graph: GraphHandle; nVertices, nArcs: longint; FUNCTION MoreVerts(n, row: integer): boolean; FUNCTION MoreArcs(n, row: integer): boolean);` | Allocates and initializes a new GraphHandle in graph with initial capacity for nVertices vertices and nArcs arcs and expansion callbacks MoreVerts and MoreArcs. |
| `DFSDir` | `PROCEDURE DFSDir(g: GraphHandle; start: Vertex; PROCEDURE First(vi, a, vt: Vertex); PROCEDURE Again(vi, a, vt: Vertex); PROCEDURE Done(v: Vertex));` | Performs a directed depth-first traversal of graph g starting from vertex start, calling First(vi, a, vt) on tree arcs, Again(vi, a, vt) on arcs to already-visited vertices, and Done(v) on vertex completion. |
| `BFSUnDir` | `PROCEDURE BFSUnDir(g: GraphHandle; start: Vertex; FUNCTION Test(v: Vertex; VAR cont: boolean): boolean);` | Performs an undirected breadth-first search of graph g starting at vertex start, calling Test(v, cont) on each visited vertex until Test stops the search or cont is set FALSE. |

---

## Unit IUMan

Manages Lisa OS intrinsic unit library directories (INTRINSIC.LIB), reading and writing unit/segment location tables, file string tables, and dotted 4-part system version records, as well as installing units and copying compact interface text.

- **Import**: `USES IUMan;`
- **Interface dependencies**: `StdUnit`, `PasDefs`, `MemMan`, `FileIO`, `ObjIO`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `InitIUMan` | `PROCEDURE InitIUMan;` | Initializes IUMan global tables, system configuration bounds, and the default '-INTRINSIC.LIB' object file descriptor iuLibFile. |
| `EachIUSeg` | `PROCEDURE EachIUSeg(PROCEDURE visit(s: integer));` | Invokes callback visit(s) for each valid intrinsic segment entry index s in iuLibSegs. |
| `EachIUUnit` | `PROCEDURE EachIUUnit(PROCEDURE visit(u: integer));` | Invokes callback visit(u) for each valid intrinsic unit entry index u in iuLibUnts. |
| `EachIUFile` | `PROCEDURE EachIUFile(PROCEDURE visit(f: integer));` | Invokes callback visit(f) for each valid intrinsic library file-name entry index f in iuLibFNam. |
| `VersToStr` | `PROCEDURE VersToStr(VAR s: LString; VAR vers: Longint);` | Formats packed 32-bit VersVal version number vers (System.Release.Version.InterFLevel) into dotted decimal string s. |
| `WriteVers` | `PROCEDURE WriteVers(VAR f: text; vers: Longint; len: integer);` | Formats packed 32-bit version number vers via VersToStr and writes it padded to field width len to text file f. |
| `StrToVers` | `PROCEDURE StrToVers(s: LString; VAR vers: Longint);` | Parses dotted decimal version string s into packed 32-bit VersVal longint vers. |
| `ReadVers` | `PROCEDURE ReadVers(VAR vers: Longint; VAR stat: PromptState; DefL: Longint);` | Reads a version string from standard input (defaulting to DefL on empty input), parses it into vers, and returns the input PromptState in stat. |
| `VerifyVers` | `PROCEDURE VerifyVers(minfile: Longint; maxfile: Longint; msg: LString);` | Verifies that file version bounds [minfile..maxfile] are compatible with the active system configuration, reporting an Error with msg on mismatch. |
| `ReadIULib` | `FUNCTION ReadIULib(allocDelta, unitsOnly, filter: boolean; SSNam: PLString): boolean;` | Reads VersionCtrl, StringBlock, UnitLocation/OldUntLoc, and (unless unitsOnly is TRUE) SegLocation blocks from iuLibFile into IUMan tables, optionally reserving delta growth slots (allocDelta) and filtering by subsystem name SSNam. |
| `WriteIULib` | `PROCEDURE WriteIULib(VCtrl: ObjFileType; SysC: Longint; ModL: integer; TimeS: Longint; VAR iuOutFile: ObjHandle; RootIdx: integer);` | Writes a complete intrinsic unit directory or library object file (VersionCtrl, UnitLocation, SegLocation, StringBlock, and copied object blocks) to iuOutFile using file type VCtrl, configuration SysC, mod level ModL, timestamp TimeS, and root index RootIdx. |
| `WriteIUVers` | `PROCEDURE WriteIUVers(VCtrl: ObjFileType; SysC: Longint; ModL: integer; TimeS: Longint; VAR iuOutFile: ObjHandle; RootIdx: integer; EmitOSBlk: boolean);` | Writes a VersionCtrl block (with VCtrl, SysC, ModL, TimeS, and RootIdx) and, when EmitOSBlk is TRUE, an OSData block to object file iuOutFile. |
| `IUInstall` | `function IUInstall(VAR FName: LString; FNum: integer; VAR vFile: ObjHandle; VAR PName: LString; PITSeg: integer): boolean;` | Opens object file FName (or PIT file PName for PITSeg) for file table entry FNum via vFile, validates and installs its UnitTable, SegmentTable, UnitBlock, and EndBlock records into IUMan tables, and returns TRUE on success. |
| `CopyInter` | `PROCEDURE CopyInter(inF, outF: ObjHandle; VAR outBlock: ObjBlock; NBytes, bufP: Longint);` | Copies NBytes of Pascal INTERFACE text starting at offset bufP in inF to outF while stripping non-directive comments and updating outBlock's block size. |

---

## Unit Lists

Provides generic singly linked list operations parameterized by caller-supplied link-accessor and ordering callbacks, used to thread integer-indexed records in Graphs, Parts, and Refs.

- **Import**: `USES Lists;`
- **Interface dependencies**: `PasDefs`, `MemMan`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `AddItem` | `PROCEDURE AddItem(list: ListHandle; LHead: Head; NewItem: Item);` | Prepends item NewItem to the front of singly linked list LHead in list store list using its setFirst/getFirst/setNext callbacks. |
| `DeleteItem` | `PROCEDURE DeleteItem(list: ListHandle; LHead: Head; OldItem: Item);` | Unlinks item OldItem from singly linked list LHead in list store list, raising a fatal error if OldItem is not on the list. |
| `EachItem` | `PROCEDURE EachItem(list: ListHandle; LHead: Head; PROCEDURE Visit(LItem: Item));` | Traverses singly linked list LHead in list store list from head to tail, invoking Visit(LItem) on each item. |
| `FirstItem` | `FUNCTION FirstItem(list: ListHandle; LHead: Head): Item;` | Returns the first Item at the head of list LHead in list store list (or NullItem if empty). |
| `InitList` | `PROCEDURE InitList(list: ListHandle; NewList: Head);` | Initializes list head NewList in list store list to empty (NullItem). |
| `InitLStore` | `PROCEDURE InitLStore(VAR list: ListHandle; LO: ListOpsPtr; LS: longint);` | Allocates and initializes a ListHandle in list bound to callback table LO and underlying storage address LS. |
| `InsertItem` | `PROCEDURE InsertItem(list: ListHandle; LHead: Head; NewItem: Item);` | Inserts NewItem into singly linked list LHead in list store list in sorted order according to list's before comparison callback. |
| `ListEmpty` | `FUNCTION ListEmpty(list: ListHandle; LHead: Head): boolean;` | Returns TRUE if singly linked list LHead in list store list contains no items. |
| `ListSize` | `FUNCTION ListSize(list: ListHandle; LHead: Head): integer;` | Counts and returns the number of items in singly linked list LHead in list store list. |
| `ReverseList` | `PROCEDURE ReverseList(list: ListHandle; LHead: Head);` | Reverses the link order of all items in singly linked list LHead in list store list in place. |

---

## Unit MemMan

Implements a segmented 256-slot-per-row index allocator and checked heap-allocation helpers used by Workshop compiler and linker data structures.

- **Import**: `USES MemMan;`
- **Interface dependencies**: `PasDefs`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `InitMem` | `PROCEDURE InitMem(VAR mem: MMHandle; numElements: longint; FUNCTION GetMore(n, row: integer): boolean);` | Allocates and initializes a MemMan index allocator in mem for numElements initial slots, reserving index NullItem and invoking GetMore to initialize each 256-slot row. |
| `MMAllocate` | `FUNCTION MMAllocate(mem: MMHandle; FUNCTION GetMore(n, row: integer): boolean): integer;` | Finds, marks allocated, and returns the lowest free element index in mem, expanding the row table via GetMore if all current slots are in use. |
| `Reserve` | `PROCEDURE Reserve(mem: MMHandle; i: integer; FUNCTION GetMore(n, row: integer): boolean);` | Marks specific element index i as allocated in mem (expanding via GetMore if needed), reporting an error if i is out of range or already allocated. |
| `Free` | `PROCEDURE Free(mem: MMHandle; i: integer);` | Marks element index i as free in mem and updates FirstFree if i precedes it, reporting an error if i is out of range. |
| `IsFree` | `FUNCTION IsFree(mem: MMHandle; i: integer): boolean;` | Returns TRUE if element index i in mem is currently unallocated (MMFree). |
| `EachAllocated` | `PROCEDURE EachAllocated(mem: MMHandle; PROCEDURE visit(i: integer));` | Invokes callback visit(i) in ascending order for every allocated element index i (excluding NullItem) in mem. |
| `HeapAlloc` | `PROCEDURE HeapAlloc(VAR p: MemPtr; n: longint; m: longint);` | Allocates n * m bytes on the Pascal heap and stores the resulting pointer in p, halting with an error if the request exceeds 32 KB or heap space is exhausted. |
| `MMRows` | `FUNCTION MMRows(n: longint): integer;` | Computes and returns the number of 256-element MemMan table rows required to hold n elements. |
| `NullMore` | `FUNCTION NullMore(n, row: integer): boolean;` | Serves as a no-op MemMan GetMore expansion callback that always returns FALSE when dynamic growth is disallowed. |

---

## Unit ObjIO

Reads and writes Apple Lisa object, executable, and intrinsic library files composed of typed invariant header blocks and variant record arrays.

- **Import**: `USES ObjIO;`
- **Interface dependencies**: `PasDefs`, `FileIO`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `InitObjFile` | `PROCEDURE InitObjFile(VAR ObjPtr: ObjHandle; nBlocks: integer);` | Allocates an ObjDesc object-file handle in ObjPtr with an nBlocks-block FileIO buffer and initializes its block-header and variant size tables. |
| `OpenObjFile` | `PROCEDURE OpenObjFile(VAR ObjPtr: ObjHandle; FileName: LString; NewFile: boolean);` | Opens existing object file FileName (when NewFile is FALSE) or creates a new one (when NewFile is TRUE) on ObjPtr and resets its block pointer to 0. |
| `ZeroObjEnd` | `PROCEDURE ZeroObjEnd(ObjPtr: ObjHandle);` | Pads object file ObjPtr with zero bytes from its current byte position to the next 512-byte block boundary. |
| `CloseObjFile` | `PROCEDURE CloseObjFile(ObjPtr: ObjHandle; Save: boolean);` | Flushes and closes object file ObjPtr, saving/locking it if Save is TRUE or deleting a newly created file if Save is FALSE. |
| `GetObjPtr` | `PROCEDURE GetObjPtr(ObjPtr: ObjHandle; VAR BytePtr: FileAddr);` | Returns the current byte read/write offset within object file ObjPtr in BytePtr. |
| `GetObjBlockPtr` | `PROCEDURE GetObjBlockPtr(ObjPtr: ObjHandle; VAR BytePtr: FileAddr);` | Returns the file byte offset of the next sequential invariant block header in ObjPtr in BytePtr. |
| `SetObjPtr` | `PROCEDURE SetObjPtr(ObjPtr: ObjHandle; BytePtr: FileAddr);` | Positions ObjPtr's byte read/write pointer to BytePtr without altering the next sequential invariant block pointer. |
| `SetObjBlockPtr` | `PROCEDURE SetObjBlockPtr(ObjPtr: ObjHandle; BytePtr: FileAddr);` | Sets ObjPtr's next sequential invariant block file offset to BytePtr. |
| `SkipObjBytes` | `PROCEDURE SkipObjBytes(ObjPtr: ObjHandle; NrBytes: longint);` | Advances or rewinds ObjPtr's byte read/write pointer by NrBytes bytes without changing its next-block pointer. |
| `SetObjInvar` | `PROCEDURE SetObjInvar(VAR B: ObjBlock; InvarType: BlockType; VarSize: longint);` | Initializes ObjBlock header B with block type InvarType, its default variant type, and variant count computed from VarSize (halting if VarSize is not a multiple of the variant record size). |
| `CopyObjSeq` | `PROCEDURE CopyObjSeq(InObj, OutObj: ObjHandle; NrBytes: integer);` | Copies NrBytes raw bytes from current position in object file InObj to current position in OutObj. |
| `GetObjInvar` | `PROCEDURE GetObjInvar(ObjPtr: ObjHandle; VAR Stuff: ObjBlock);` | Seeks to ObjPtr's next block boundary, reads and decodes the 4-byte block header and invariant fields into Stuff, and advances NextBlock to the following block. |
| `GetObjVar` | `PROCEDURE GetObjVar(ObjPtr: ObjHandle; VarType: VariantType; VAR Stuff: ObjVarBlock);` | Reads one variant sub-record of type VarType from ObjPtr's current position into Stuff. |
| `GetObjName` | `PROCEDURE GetObjName(ObjPtr: ObjHandle; VAR N: NameString);` | Reads an 8-character packed NameString identifier from ObjPtr into N. |
| `GetObjSeq` | `PROCEDURE GetObjSeq(ObjPtr: ObjHandle; Stuff: Ptr; NrBytes: integer);` | Reads NrBytes sequential bytes from ObjPtr into memory buffer Stuff. |
| `GetObjByte` | `PROCEDURE GetObjByte(ObjPtr: ObjHandle; VAR B: Byte);` | Reads one unsigned byte (0..255) from ObjPtr into B. |
| `GetObjWord` | `PROCEDURE GetObjWord(ObjPtr: ObjHandle; VAR W: integer);` | Reads a big-endian 16-bit signed integer from ObjPtr into W. |
| `GetObjLong` | `PROCEDURE GetObjLong(ObjPtr: ObjHandle; VAR L: longint);` | Reads a big-endian 32-bit signed LongInt from ObjPtr into L. |
| `PutObjInvar` | `PROCEDURE PutObjInvar(ObjPtr: ObjHandle; VAR Stuff: ObjBlock);` | Seeks to ObjPtr's NextBlock offset, writes the 4-byte block header (type byte and 24-bit block size) and invariant record fields from Stuff, and advances NextBlock by the total block size. |
| `PutObjVar` | `PROCEDURE PutObjVar(ObjPtr: ObjHandle; VarType: VariantType; VAR Stuff: ObjVarBlock);` | Writes one variant sub-record of type VarType from Stuff to ObjPtr at its current byte position. |
| `PutObjName` | `PROCEDURE PutObjName(ObjPtr: ObjHandle; N: NameString);` | Writes 8-character packed NameString N to ObjPtr at its current byte position. |
| `PutObjSeq` | `PROCEDURE PutObjSeq(ObjPtr: ObjHandle; Stuff: Ptr; NrBytes: integer);` | Writes NrBytes sequential bytes from memory buffer Stuff to ObjPtr at its current byte position. |
| `PutObjByte` | `PROCEDURE PutObjByte(ObjPtr: ObjHandle; B: Byte);` | Writes unsigned byte B (0..255) to ObjPtr at its current byte position. |
| `PutObjWord` | `PROCEDURE PutObjWord(ObjPtr: ObjHandle; W: integer);` | Writes 16-bit integer W in big-endian byte order to ObjPtr at its current byte position. |
| `PutObjLong` | `PROCEDURE PutObjLong(ObjPtr: ObjHandle; L: longint);` | Writes 32-bit LongInt L in big-endian byte order to ObjPtr at its current byte position. |

---

## Unit Parts

Implements disjoint set partitions grouping integer members into equivalence classes backed by dynamically expandable row tables and linked member lists.

- **Import**: `USES Parts;`
- **Interface dependencies**: `PasDefs`, `MemMan`, `Lists`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `NewClass` | `PROCEDURE NewClass(partH: PartHandle; cl: Class);` | Initializes equivalence class cl in partition partH with an empty member list. |
| `AddMember` | `PROCEDURE AddMember(partH: PartHandle; mem: Member; cl: Class);` | Assigns member mem to equivalence class cl in partition partH and prepends mem to cl's member list. |
| `DeleteMember` | `PROCEDURE DeleteMember(partH: PartHandle; mem: Member; cl: Class);` | Removes member mem from equivalence class cl's member list in partition partH and clears mem's class assignment to NullItem. |
| `IsEmptyClass` | `FUNCTION IsEmptyClass(partH: PartHandle; cl: Class): boolean;` | Returns TRUE if equivalence class cl in partition partH has no members. |
| `EachMember` | `PROCEDURE EachMember(partH: PartHandle; cl: Class; PROCEDURE Visit(m: Member));` | Invokes callback Visit(m) for every member m belonging to equivalence class cl in partition partH. |
| `ClassOf` | `FUNCTION ClassOf(partH: PartHandle; mem: Member): Class;` | Returns the equivalence Class to which member mem currently belongs in partition partH (or NullItem if unassigned). |
| `RevMembers` | `PROCEDURE RevMembers(partH: PartHandle; cl: Class);` | Reverses the order of the member list of equivalence class cl in partition partH. |
| `InitPLists` | `PROCEDURE InitPLists;` | Initializes the shared ListOpsRec link-accessor callback table used for partition class member lists. |
| `MoreMembers` | `FUNCTION MoreMembers(partH: PartHandle; n, newRow: integer): boolean;` | Allocates and initializes row newRow of 256 MemberRec entries in partH's member table, updating capacity to n and returning TRUE. |
| `MoreClasses` | `FUNCTION MoreClasses(partH: PartHandle; n, newRow: integer): boolean;` | Allocates and initializes row newRow of 256 class-head entries in partH's class table, updating capacity to n and returning TRUE. |
| `InitPartition` | `FUNCTION InitPartition(nCl, nMem: longint; abst: PartHandle): PartHandle;` | Allocates and initializes a new PartHandle for nCl classes and nMem members (reusing abst if non-NIL) and returns the handle. |

---

## Unit PasDefs

Defines core Lisa Pascal Workshop compiler and tool types, listing file state, error counters, and diagnostic warning, error, and fatal-abort reporting routines.

- **Import**: `USES PasDefs;`
- **Interface dependencies**: `StdUnit`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `InitPasDefs` | `PROCEDURE InitPasDefs;` | Resets the global error count to zero, opens ListingFile on '-CONSOLE', and sets ListFlag to FALSE. |
| `PasHalt` | `PROCEDURE PasHalt;` | Stops any active Workshop exec script via SUStopExec and halts program execution. |
| `SumErrors` | `PROCEDURE SumErrors;` | Writes the total number of detected errors to ListingFile (and to standard output when ListFlag is TRUE). |
| `Warning` | `PROCEDURE Warning(s: LString);` | Writes formatted warning message '*** Warning - <s> ***' to ListingFile without incrementing the error count. |
| `Error` | `PROCEDURE Error(s: LString);` | Writes formatted error message '*** Error - <s> ***' to ListingFile, aborts any running exec script, and increments errors. |
| `FatalError` | `PROCEDURE FatalError(s: LString);` | Aborts any running exec script, writes '*** Fatal Error - <s> ***' to ListingFile (and console if ListFlag is TRUE), waits for the user to press Space, and halts via PasHalt. |

---

## Unit Refs

Manages dynamically expandable singly linked lists of integer reference locations indexed by symbol or entity head IDs for linker and object-file tools.

- **Import**: `USES Refs;`
- **Interface dependencies**: `PasDefs`, `MemMan`, `Lists`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `AddRef` | `FUNCTION AddRef(rh: RefHandle; head: Ref; l: integer; FUNCTION GetMore(n, row: integer): boolean): Ref;` | Allocates a new Ref node in rh (expanding via GetMore if needed), sets its reference location refloc to l, prepends it to reference list head, and returns the new Ref index. |
| `EachRef` | `PROCEDURE EachRef(rh: RefHandle; head: Ref; PROCEDURE Visit(i: Ref));` | Invokes callback Visit(i) for each Ref node i in reference list head of rh. |
| `MoreHeads` | `FUNCTION MoreHeads(rh: RefHandle; n, row: integer): boolean;` | Allocates and initializes row of 256 reference-list head entries in rh^.refHeads up to capacity n and returns TRUE. |
| `NewRefList` | `PROCEDURE NewRefList(rh: RefHandle; head: Ref);` | Initializes reference list head in rh to an empty list. |
| `InitRLists` | `PROCEDURE InitRLists;` | Initializes the shared ListOpsRec link-accessor and comparison callback table used for reference lists. |
| `InitRefs` | `FUNCTION InitRefs(nHeads, nRefs: longint): RefHandle;` | Allocates and initializes a RefHandle with initial capacity for nHeads reference-list heads and nRefs reference entries. |
| `CopyRefLists` | `PROCEDURE CopyRefLists(rh: RefHandle; old, new: Ref);` | Copies the head pointer of reference list old to reference list new in rh so new points to the same chain of references. |

---

## Unit Trees

Implements dynamically expandable binary search trees of 8-character identifier names with lookup, insertion, and in-order traversal.

- **Import**: `USES Trees;`
- **Interface dependencies**: `PasDefs`, `MemMan`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `EnterNode` | `FUNCTION EnterNode(t: TreeHandle; VAR newN: NameString; PROCEDURE duplicate(t: TreeHandle; VAR np: NameString; n: Node); PROCEDURE newNode(t: TreeHandle; VAR x: NameString; VAR newN: Node)): Node;` | Searches binary search tree t for identifier newN, calling duplicate(t, newN, n) if node n already exists or allocating and linking a new leaf via newNode(t, newN, n), and returns the node index. |
| `TLookUp` | `FUNCTION TLookUp(t: TreeHandle; VAR x: NameString): Node;` | Searches binary search tree t for identifier x and returns its Node index, or NullNode (-32768) if x is not present. |
| `InOTraverse` | `PROCEDURE InOTraverse(t: TreeHandle; PROCEDURE Visit(i: Node));` | Performs an in-order traversal of binary search tree t, invoking Visit(i) on each node in sorted key order. |
| `InitNameTree` | `FUNCTION InitNameTree(n: longint): TreeHandle;` | Allocates and initializes an empty NameString binary search tree with initial capacity for n nodes and returns its TreeHandle. |
| `GrowTree` | `FUNCTION GrowTree(t: TreeHandle; n, row: integer): boolean;` | Allocates row of 256 node and NameString entries to expand tree t to capacity n and returns TRUE. |
