# `SYS2LIB` (`Sys2Lib.obj`) — Lisa Database Engine & Table Manager Library

[Back to Library Index](LIBRARIES.md)

Lisa relational/record database subsystem (`Scan`, `Schema`, `VLTree`, `Pooler`, `Recovery`, `Heap`, `LabScan`, `LowLevel`, `CzCompact`, `DBDecl1`) and 2D spreadsheet/list Table Manager (`TM`, `TEEnv`, `LCUt`).

- **Object file**: `libs/workshop3.0/Sys2Lib.obj` (Intrinsic library)
- **Contents**: 13 units, 189 top-level procedures/functions

## Importing and Linking

```pascal
USES CzCompact, DBDecl1, Heap;
```

```sh
pascal/lpc.py --link=IOSPASLIB,SYS1LIB,SYS2LIB MYPROG
```

## Units in This Library

| Unit | 8-Char Symbol | `USES` Dependencies | Routines | Summary |
|---|---|---|---|---|
| [`CzCompact`](#unit-czcompact) | `CZCOMPAC` | `DBEnv`, `DBDecl1`, `SysCall`, `LowLevel`, `Pooler`, `Heap` | 3 | Provides heap compaction and retry-state management for the Lisa database heap zone (`czone`), relocating buffer pool, file, scan, record, and B-tree page-stack pointers when allocations run out of memory. |
| [`DBDecl1`](#unit-dbdecl1) | `DBDECL1` | `UnitStd`, `DBEnv`, `SysCall`, `psyscall`, `International` | 21 | Defines core Lisa database types, field/schema descriptors, and low-level 68000 assembly utilities for block memory moves, bitfield packing, 32/64-bit unsigned comparisons and arithmetic, page bitsets, multi-field record comparisons, key extraction, and List Manager field representation validation. |
| [`Heap`](#unit-heap) | `HEAP` | — | 4 | Implements a lightweight first-fit heap zone allocator (`zonedesc`) for Lisa database internal structures, supporting zone initialization, growth or shrinkage, non-compacting block allocation, and block deallocation. |
| [`LabScan`](#unit-labscan) | `LABSCAN` | `DBEnv`, `International`, `DBDecl1`, `SysCall`, `LowLevel`, `Pooler`, `Heap`, `CzCompact`, `VLTree`, `Scan` | 3 | Provides scan-based fetch, insert, and delete operations on variable-length label records stored in a Lisa database file's label B-tree. |
| [`LCUt`](#unit-lcut) | `LCUT` | `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `DBEnv`, `FEDec`, `FieldEdit`, `SysCall`, `TEEnv`, `PMDecl`, `PrStdInfo`, `Events`, `Scrap`, `UnitFile`, `UnitFmt`, `UnitCs`, `UnitFf` | 2 | Exports cell-matrix scrap contents from LisaCalc, LisaGraph, and LisaList to the global Lisa Scrap in tabbed Universal Text format upon folder deactivation. |
| [`LowLevel`](#unit-lowlevel) | `LOWLEVEL` | `DBEnv`, `DBDecl1`, `SysCall` | 3 | Maintains the global pathname prefix and encryption password prepended to file names during Lisa database file-system operations. |
| [`Pooler`](#unit-pooler) | `POOLER` | `DBEnv`, `International`, `DBDecl1`, `SysCall`, `LowLevel` | 10 | Manages the shared LRU page buffer pool for Lisa database B-tree and label files, handling page reads and writes, buffer locking and prioritized release, dirty-file status marking, checkpointing, invalidation, and file closing. |
| [`Recovery`](#unit-recovery) | `RECOVERY` | `DBEnv`, `International`, `DBDecl1`, `SysCall`, `LowLevel`, `Pooler`, `Heap`, `CzCompact`, `VLTree`, `Scan`, `LabScan`, `Schema` | 1 | Recovers damaged Lisa database and List Manager files by scavenging readable records, validating schemas and edit checks, deleting stale differential/index files, and rebuilding secondary indexes. |
| [`Scan`](#unit-scan) | `SCAN` | `DBEnv`, `International`, `DBDecl1`, `SysCall`, `LowLevel`, `Pooler`, `Heap`, `CzCompact`, `VLTree` | 8 | Implements cursor-based database scans (`scandesc`) over Lisa data files and B-tree indexes, supporting positioned fetches, insertions, updates, deletions, parameter validation, and index key sizing. |
| [`Schema`](#unit-schema) | `SCHEMA` | `DBEnv`, `International`, `DBDecl1`, `SysCall`, `LowLevel`, `Pooler`, `Heap`, `CzCompact`, `VLTree`, `Scan`, `LabScan` | 16 | Manages Lisa database file creation, cloning, deletion, B-tree buffer pool initialization, scan opening/closing/flushing, and high-level form schema and index metadata stored in file labels. |
| [`TEEnv`](#unit-teenv) | `TEENV` | `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `DBEnv`, `FEDec`, `FieldEdit` | 16 | Defines shared Table Editor environment types (panels, cell ranges, snips, view bands, and table configuration records) and provides panel GrafPort, coordinate conversion, clipping, and range helper routines. |
| [`TM`](#unit-tm) | `TM` | `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `DBEnv`, `FEDec`, `FieldEdit`, `TEEnv`, `WmlStd`, `WmlSb` | 89 | Implements the shared Table Manager and Table Selection Manager (`tmsProcs`) for tabular Lisa applications, handling split-view band layout, scrolling, cell/range highlighting and marquees, in-cell and wide-angle-view (`wavPnl`) FieldEdit text editing, and clipboard operations. |
| [`VLTree`](#unit-vltree) | `VLTREE` | `DBEnv`, `International`, `DBDecl1`, `SysCall`, `LowLevel`, `Pooler`, `Heap` | 13 | Implements variable-length B-tree (`VLTree`) page and key management for Lisa database data, index, and label files, including fast in-page insert/update/delete, page splitting, sibling rotation and coalescing, duplicate resolution, and keyed searches. |

---

## Unit CzCompact

Provides heap compaction and retry-state management for the Lisa database heap zone (`czone`), relocating buffer pool, file, scan, record, and B-tree page-stack pointers when allocations run out of memory.

- **Import**: `USES CzCompact;`
- **Unit kind**: `INTRINSIC` (`CZCOMPAC`)
- **Interface dependencies**: `DBEnv`, `DBDecl1`, `SysCall`, `LowLevel`, `Pooler`, `Heap`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `heap_compact` | `procedure heap_compact;` | Compacts the database heap zone (`czone`) in three phases, relocating all buffer-pool, file, scan, record, current-of-scan, and B-tree page-stack pointers. |
| `init_compact_state` | `function init_compact_state: states_de_compact;` | Initializes and returns the local compaction state (`first_try` or `no_try`) based on whether an enclosing database routine already owns heap compaction. |
| `retry_compact` | `function retry_compact(var error_code: integer; var local_state: states_de_compact): boolean;` | Compacts the database heap and returns `true` to request a retry when an operation fails with `nomem` on its `first_try`, updating local and global compaction state. |

---

## Unit DBDecl1

Defines core Lisa database types, field/schema descriptors, and low-level 68000 assembly utilities for block memory moves, bitfield packing, 32/64-bit unsigned comparisons and arithmetic, page bitsets, multi-field record comparisons, key extraction, and List Manager field representation validation.

- **Import**: `USES DBDecl1;`
- **Unit kind**: `INTRINSIC` (`DBDECL1`)
- **Interface dependencies**: `UnitStd`, `DBEnv`, `SysCall`, `psyscall`, `International`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `movelg` | `procedure movelg(p1, p2: ptrdata; nbytes: integer);` | Copies `nbytes` bytes from source `p1` to destination `p2` moving left-to-right (low to high addresses), supporting arbitrary odd or even byte alignments and counts. |
| `moverg` | `procedure moverg(p1, p2: ptrdata; nbytes: integer);` | Copies `nbytes` bytes from source `p1` to destination `p2` moving right-to-left (high to low addresses) for overlapping ranges, supporting odd or even alignments and counts. |
| `movelf` | `procedure movelf(p1, p2: ptrdata; nbytes: integer);` | Performs a fast longword-optimized left-to-right copy of `nbytes` bytes from word-aligned source `p1` to word-aligned destination `p2`. |
| `moverf` | `procedure moverf(p1, p2: ptrdata; nbytes: integer);` | Performs a fast longword-optimized right-to-left copy of `nbytes` bytes from word-aligned source `p1` to word-aligned destination `p2`. |
| `extract` | `function extract(pbyte: ptrdata; nbit, sbit: integer): integer;` | Extracts and returns an unsigned `nbit`-wide packed bitfield starting at bit position `sbit` (LSB = 0) from the 16-bit word at `pbyte`. |
| `deposit` | `procedure deposit(value: integer; pbyte: ptrdata; nbit, sbit: integer);` | Stores an unsigned `nbit`-wide integer `value` into the packed bitfield starting at bit position `sbit` (LSB = 0) within the 16-bit word at `pbyte`. |
| `mult424` | `function mult424(m4: fileptr; m2: integer): fileptr;` | Multiplies an unsigned 32-bit value `m4` by an unsigned 16-bit integer `m2` and returns the unsigned 32-bit product. |
| `comp44` | `function comp44(s1, s2: fileptr): integer;` | Compares two unsigned 32-bit file pointers `s1` and `s2`, returning `lt` (0), `gt` (1), or `eq` (2). |
| `comphand` | `function comphand(var s1, s2: fint8): integer;` | Compares two unsigned 64-bit record handles (`fint8`) `s1` and `s2`, returning `lt` (0), `gt` (1), or `eq` (2). |
| `div424` | `function div424(m4: fileptr; m2: integer; var r2: integer): fileptr;` | Divides an unsigned 32-bit dividend `m4` by an unsigned 16-bit divisor `m2`, returning the 32-bit quotient and storing the 16-bit remainder in `r2`. |
| `setset` | `procedure setset(pset: ptrdata; lastelement, nelements: integer);` | Populates a `nelements`-bit page-element bitset at `pset` with bits `0..lastelement-1` set to 1 and all remaining bits cleared. |
| `clearset` | `procedure clearset(pset: ptrdata; elements: integer);` | Clears all words of an `elements`-bit page-element bitset at `pset` to zero. |
| `clearbit` | `procedure clearbit(pset: ptrdata; bit: integer);` | Clears bit index `bit` in the page-element bitset pointed to by `pset`. |
| `inpset` | `function inpset(pset: ptrdata; bit: integer): boolean;` | Returns `true` if bit index `bit` is set in the page-element bitset pointed to by `pset`. |
| `setbit` | `procedure setbit(pset: ptrdata; bit: integer);` | Sets bit index `bit` to 1 in the page-element bitset pointed to by `pset`. |
| `pintersect` | `function pintersect(pset1, pset2: ptrbits; setelements: integer): boolean;` | Returns `true` if two `setelements`-bit page bitsets `pset1` and `pset2` have a non-empty intersection (at least one common bit set). |
| `compare` | `function compare(desc1, desc2: ptrrecptr; nfields: integer; prec1, prec2: ptrdata): integer;` | Compares `nfields` fields between database records `prec1` and `prec2` using field descriptors `desc1` and `desc2` (honoring field types, international string collation, and sort directions), returning `lt`, `gt`, or `eq`. |
| `extractkey` | `procedure extractkey(pdesc1, pdesc2: ptrrecptr; nflds: integer; pentry: ptrdata; pwhere: ptrdata; vflds: integer);` | Extracts `nflds` key fields from source data record `pentry` (described by `pdesc1`) into destination index key record `pwhere` (described by `pdesc2`), placing variable-length data starting at offset `vflds`. |
| `findchanges` | `function findchanges(pdesc1: ptrrecptr; nfields: integer; pbefore, pafter: ptrdata; pset: ptrbits): boolean;` | Compares `nfields` fields between `pbefore` and `pafter` using descriptor `pdesc1`, setting bit `i` in `pset` for each modified field and returning `true` if a ticket field changed. |
| `GetRepType` | `PROCEDURE GetRepType(var result: integer; DataType: INTEGER; CheckArray: CheckInfo; VAR RepType: Short; VAR Size: INTEGER);` | Determines the low-level database representation type (`RepType`) and byte size (`Size`) that List Manager uses for high-level field type `DataType` and edit-check descriptor `CheckArray`. |
| `ValidRepType` | `PROCEDURE ValidRepType(var result: integer; DataType: INTEGER; CheckArray: CheckInfo; RepType: Short; Size: INTEGER);` | Validates whether low-level representation `RepType` and `Size` are legal List Manager storage representations for high-level field type `DataType` and edit-check `CheckArray`. |

---

## Unit Heap

Implements a lightweight first-fit heap zone allocator (`zonedesc`) for Lisa database internal structures, supporting zone initialization, growth or shrinkage, non-compacting block allocation, and block deallocation.

- **Import**: `USES Heap;`
- **Unit kind**: `INTRINSIC` (`HEAP`)

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `init_heap` | `procedure init_heap(pzone: ptrzonedesc; initsize: integer; where: _ptr);` | Initializes heap zone descriptor `pzone^` for a contiguous memory region of `initsize` bytes starting at `where` with a single free block. |
| `grow_heap` | `function grow_heap(pzone: ptrzonedesc; growincr: integer): integer;` | Expands (`growincr > 0`) or shrinks (`growincr < 0`) the heap zone `pzone^` by `growincr` bytes, returning `noerr` or `nomem` if trailing space is insufficient to shrink. |
| `nnew` | `function nnew(pzone: ptrzonedesc; reqsize: integer; pdataptr: ptrptr): integer;` | Allocates a first-fit block of `reqsize` bytes in heap zone `pzone^` without compacting, storing the block address in `pdataptr^` and returning `noerr` or `nomem`. |
| `ndispose` | `procedure ndispose(pzone: ptrzonedesc; pdata: _ptr);` | Frees the allocated block at `pdata` in heap zone `pzone^` and coalesces it with adjacent free blocks on the doubly linked free list. |

---

## Unit LabScan

Provides scan-based fetch, insert, and delete operations on variable-length label records stored in a Lisa database file's label B-tree.

- **Import**: `USES LabScan;`
- **Unit kind**: `INTRINSIC` (`LABSCAN`)
- **Interface dependencies**: `DBEnv`, `International`, `DBDecl1`, `SysCall`, `LowLevel`, `Pooler`, `Heap`, `CzCompact`, `VLTree`, `Scan`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `lfetch` | `procedure lfetch(var ddresult: integer; scanid: integer; which: integer; nsearch: integer; plabrec: ptrlabelentry);` | Fetches a label record matching positioning mode `which` (`first`, `last`, `approx`, `exact`, `current`, `prior`, or `next`) on label scan `scanid` into `plabrec` and makes it current-of-scan. |
| `linsert` | `procedure linsert(var ddresult: integer; scanid: integer; plabrec: ptrlabelentry; size: integer; newticket: boolean);` | Inserts a `size`-byte label record `plabrec` into the file label via `scanid` (generating a new unique label ticket if `newticket` is `true`) and makes it current-of-scan. |
| `ldelete` | `procedure ldelete(var ddresult: integer; scanid: integer; which: integer; nsearch: integer; plabrec: ptrlabelentry);` | Deletes the current-of-scan label record on `scanid` (after optional repositioning via `which`, `nsearch`, and `plabrec`). |

---

## Unit LCUt

Exports cell-matrix scrap contents from LisaCalc, LisaGraph, and LisaList to the global Lisa Scrap in tabbed Universal Text format upon folder deactivation.

- **Import**: `USES LCUt;`
- **Unit kind**: `INTRINSIC` (`LCUT`)
- **Interface dependencies**: `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `DBEnv`, `FEDec`, `FieldEdit`, `SysCall`, `TEEnv`, `PMDecl`, `PrStdInfo`, `Events`, `Scrap`, `UnitFile`, `UnitFmt`, `UnitCs`, `UnitFf`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `WriteLCUT` | `procedure WriteLCUT(tblCharWid: integer; Tblfntid: TLfntid; var status: integer);` | Converts the current cell-matrix scrap into tabbed Universal Text format using font `Tblfntid` and character width `tblCharWid`, writing it to the system Scrap via `PutCSScrap`. |
| `InitLCutProcs` | `procedure InitLCutProcs(CellBlank: ProcPtr; CellInfo: ProcPtr; CellValue: ProcPtr; FinalDataSnip: ProcPtr; GetSnipId: ProcPtr; RgInScrap: ProcPtr; SnipWidth: ProcPtr; SwitchTable: ProcPtr);` | Registers the Matrix Manager callback procedures (`CellBlank`, `CellInfo`, `CellValue`, `FinalDataSnip`, `GetSnipId`, `RgInScrap`, `SnipWidth`, and `SwitchTable`) required by `WriteLCUT`. |

---

## Unit LowLevel

Maintains the global pathname prefix and encryption password prepended to file names during Lisa database file-system operations.

- **Import**: `USES LowLevel;`
- **Unit kind**: `INTRINSIC` (`LOWLEVEL`)
- **Interface dependencies**: `DBEnv`, `DBDecl1`, `SysCall`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `setprefix` | `procedure setprefix(newprefix: ptrpathname);` | Sets the current database pathname prefix string from `newprefix^`. |
| `setpasswd` | `procedure setpasswd(var newpasswd: e_name);` | Sets the current file-system password used when opening, creating, or deleting secure database files. |
| `prefix_name` | `procedure prefix_name(fname: ptrpathname);` | Appends relative filename `fname^` onto the global database pathname `prefix` buffer. |

---

## Unit Pooler

Manages the shared LRU page buffer pool for Lisa database B-tree and label files, handling page reads and writes, buffer locking and prioritized release, dirty-file status marking, checkpointing, invalidation, and file closing.

- **Import**: `USES Pooler;`
- **Unit kind**: `INTRINSIC` (`POOLER`)
- **Interface dependencies**: `DBEnv`, `International`, `DBDecl1`, `SysCall`, `LowLevel`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `lockbuff` | `procedure lockbuff(var presult: integer; var buffer: integer);` | Acquires and locks the lowest-priority unpinned buffer in the page pool (flushing it to disk first if dirty) and returns its index in `buffer`. |
| `relbuff` | `procedure relbuff(var presult: integer; buffer: integer; relpriority: integer);` | Decrements the lock count on pool buffer `buffer` and, when unlocked, updates its LRU replacement priority using `relpriority`. |
| `dowritenon` | `procedure dowritenon(var presult: integer; fileid: integer);` | Marks open database file `fileid` as written-on and clears the `ffileok` consistency flag in its on-disk file label before the first page modification. |
| `getpage` | `procedure getpage(var presult: integer; var buffer: integer; fileid: integer; rpage: fileptr; noinconsistent: boolean);` | Reads page `rpage` of file `fileid` into a locked pool buffer (reusing an existing cached buffer on hit or preempting the lowest-priority buffer on miss) and returns the buffer index. |
| `putpage` | `procedure putpage(var presult: integer; buffer: integer; fileid: integer; wpage: fileptr);` | Writes the contents of pool `buffer` to disk at page offset `wpage` of file `fileid` after ensuring the file label is marked written-on. |
| `checkpt` | `procedure checkpt(var presult: integer; fileid: integer; newstate: integer);` | Flushes all dirty buffers belonging to `fileid` to disk, transitions its buffers to `newstate` (`empty` or `clean`), and updates the file label consistency state. |
| `doclose` | `procedure doclose(var presult: integer; fileid: integer);` | Checkpoints all buffers for open database file `fileid` to disk, updates its file label, and closes the underlying OS file reference. |
| `no_room` | `function no_room(presult: integer): boolean;` | Returns `true` if OS file-system error code `presult` indicates an out-of-disk-space or EOF allocation failure. |
| `force_out` | `procedure force_out(var presult: integer; fileid: integer; wpage: fileptr);` | Writes page `wpage` of file `fileid` to disk immediately if it resides dirty in the buffer pool so subsequent writes do not exceed `LEOF + 1`. |
| `PageInvalidates` | `procedure PageInvalidates(fileid: integer);` | Marks all buffer-pool pages belonging to `fileid` as empty and resets their replacement priorities without writing them to disk. |

---

## Unit Recovery

Recovers damaged Lisa database and List Manager files by scavenging readable records, validating schemas and edit checks, deleting stale differential/index files, and rebuilding secondary indexes.

- **Import**: `USES Recovery;`
- **Unit kind**: `INTRINSIC` (`RECOVERY`)
- **Interface dependencies**: `DBEnv`, `International`, `DBDecl1`, `SysCall`, `LowLevel`, `Pooler`, `Heap`, `CzCompact`, `VLTree`, `Scan`, `LabScan`, `Schema`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `FileRecover` | `procedure FileRecover(var ddresult: integer; var warnings: elemset; oldprefix, newprefix, pfname, pnewname, precname: ptrpathname; procedure ECheck(EC: ecstr; ftype: integer; var Check: checkinfo; var result: integer); procedure indexmake(var ddresult: integer; ifilename, filename, tempdir1, tempdir2: ptrpathname; temp_ldsn: integer; nisort, nikeys: integer; piflds: ptridesc; duplok: boolean); procedure MarksRevenge(var result: integer; var warnings: elemset; lsid: integer); ToolsMarketCode: integer);` | Recovers damaged database or List Manager file `pfname` (using optional redundant schema `precname`) into `pnewname`, validating edit checks via `ECheck` and label records via `MarksRevenge`, removing stale differential/index files, and rebuilding indexes via `indexmake`. |

---

## Unit Scan

Implements cursor-based database scans (`scandesc`) over Lisa data files and B-tree indexes, supporting positioned fetches, insertions, updates, deletions, parameter validation, and index key sizing.

- **Import**: `USES Scan;`
- **Unit kind**: `INTRINSIC` (`SCAN`)
- **Interface dependencies**: `DBEnv`, `International`, `DBDecl1`, `SysCall`, `LowLevel`, `Pooler`, `Heap`, `CzCompact`, `VLTree`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `SParmsBad` | `function SParmsBad(scanid: integer; which: integer; nsearch: integer; pentry: ptrdata): integer;` | Validates scan parameters (`scanid`, positioning mode `which`, key field count `nsearch`, and word-aligned record pointer `pentry`), returning `noerr` or a specific error code. |
| `scanidbad` | `function scanidbad(scanid: integer): boolean;` | Returns `true` if `scanid` is out of range or does not refer to an active open scan descriptor in `pscantable`. |
| `pstack_validate` | `procedure pstack_validate(var sresult: integer);` | Ensures the shared B-tree page traversal stack (`pstack`) is allocated deep enough to handle `maxdepth + 1` levels, reallocating in `czone` if needed. |
| `keysize` | `function keysize(fileid: integer; pentry: ptrdata): integer;` | Computes and returns the word-rounded byte size of the index key record that would be extracted from data record `pentry` for index file `fileid`. |
| `einsert` | `procedure einsert(var sresult: integer; var offender: integer; scanid: integer; pentry: ptrdata; size: integer; newticket: boolean);` | Inserts `size`-byte data record `pentry` into `scanid`'s file (optionally generating a unique ticket), updates all open secondary indexes, and makes the new record current-of-scan. |
| `efetch` | `procedure efetch(var sresult: integer; scanid: integer; which: integer; nsearch: integer; pentry: ptrdata);` | Positions scan `scanid` according to `which` (`first`, `last`, `approx`, `exact`, `current`, `prior`, or `next`) using `nsearch` key fields, copies the target record into `pentry`, and makes it current-of-scan. |
| `eupdate` | `procedure eupdate(var sresult: integer; var offender: integer; scanid: integer; which: integer; nsearch: integer; pentry: ptrdata; pnewrec: ptrdata; size: integer);` | Replaces the current-of-scan record on `scanid` (after optional repositioning via `which`) with `size`-byte record `pnewrec`, updating all affected index files and keeping the updated record current-of-scan. |
| `edelete` | `procedure edelete(var sresult: integer; scanid: integer; which: integer; nsearch: integer; pentry: ptrdata);` | Deletes the current-of-scan record on `scanid` (after optional repositioning via `which`, `nsearch`, and `pentry`) and removes its corresponding entries from all open indexes. |

---

## Unit Schema

Manages Lisa database file creation, cloning, deletion, B-tree buffer pool initialization, scan opening/closing/flushing, and high-level form schema and index metadata stored in file labels.

- **Import**: `USES Schema;`
- **Unit kind**: `INTRINSIC` (`SCHEMA`)
- **Interface dependencies**: `DBEnv`, `International`, `DBDecl1`, `SysCall`, `LowLevel`, `Pooler`, `Heap`, `CzCompact`, `VLTree`, `Scan`, `LabScan`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `filldesc` | `procedure filldesc(var ddresult: integer; pfile: ptrfiledesc);` | Initializes runtime fields of in-memory file descriptor `pfile^` (`openid`, `fstatus`, `scans`, `pkeyfiles`, and variable-length field bounds) from OS file info for index building. |
| `makefile` | `procedure makefile(var ddresult: integer; pname: ptrpathname; pfdesc: ptrfiledesc);` | Creates a new database B-tree file at `pname`, initializes and writes its fixed file-label header from `pfdesc^`, and leaves the file open. |
| `openindexes` | `procedure openindexes(var ddresult: integer; var viafile: integer; scanid: integer; ifilename: ptrpathname; intent: integer; labelusage: integer);` | Opens the access-path (`via`) index and/or all update indexes recorded in the file label for `scanid` according to `labelusage` and `intent`. |
| `cvt_scan` | `procedure cvt_scan(var ddresult: integer; scanid, sintent, sviafile: integer);` | Converts open scan `scanid` between label-scan and data-scan access intents (`sintent`) and rebinds it to `sviafile`. |
| `initpool` | `procedure initpool(var ddresult: integer; first_time: boolean; heap_ldsn: integer; nbuff: integer; dheapsize: integer; pheapname: ptrpathname; dstype: Tdstype; pagesize: integer);` | Initializes or resizes the database heap data segment (`heap_ldsn` / `pheapname`) and page buffer pool (`nbuff` pages of `pagesize` bytes) before or during database intrinsic use. |
| `flushscan` | `procedure flushscan(var ddresult: integer; scanid: integer);` | Flushes all dirty buffers associated with `scanid`'s data file and indexes and rewrites their file labels to mark the files consistent on disk. |
| `closescan` | `procedure closescan(var ddresult: integer; scanid: integer);` | Closes open scan `scanid`, releasing its scan descriptor and closing any underlying data or index files that have no remaining readers or writers. |
| `openscan` | `procedure openscan(var ddresult: integer; onname, vianame: ptrpathname; var scanid: integer; sintent: integer);` | Opens a database or label scan with intent `sintent` (`readonly`, `update`, `labelreadonly`, or `labelupdate`) on file `onname` ordered via `vianame`, returning `scanid`. |
| `makedescfile` | `procedure makedescfile(var ddresult: integer; pname: ptrpathname; pfdesc: ptrfiledesc);` | Creates and closes a new database data file at `pname` initialized from low-level in-memory file descriptor `pfdesc^` without variable-length label records. |
| `clonefile` | `procedure clonefile(var ddresult: integer; sourcefile, filename: ptrpathname; needtomakefile: boolean);` | Creates or updates file `filename` by cloning the low-level file descriptor and high-level form schema from `sourcefile`. |
| `makeformfile` | `procedure makeformfile(var ddresult: integer; pform: ptrdata; pfname: ptrpathname; needtomakefile: boolean);` | Creates database file `pfname` (if `needtomakefile` is `true`) and writes the high-level form schema descriptor at `pform` into its file label, replacing any existing form. |
| `quick_label_scan` | `procedure quick_label_scan(var ddresult: integer; scanid: integer; sintent: integer; var lscanid: integer);` | Opens a lightweight `labelreadonly` or `labelupdate` label scan (`lscanid`) directly on the target file of an already-open scan `scanid`. |
| `get_header` | `procedure get_header(var ddresult: integer; scanid: integer; var head: header);` | Reads the high-level form schema `header` record (including version, field counts, and remaining byte size) from the file label associated with `scanid`. |
| `getform` | `procedure getform(var ddresult: integer; scanid: integer; pdesc: ptrdata);` | Reads the variable-length field descriptors of the high-level form schema associated with `scanid` into preallocated buffer `pdesc`. |
| `deletefile` | `procedure deletefile(var ddresult: integer; pfname: ptrpathname);` | Deletes database data file `pfname` along with all secondary index files registered in its file label. |
| `deleteindex` | `procedure deleteindex(var ddresult: integer; piname, pfname: ptrpathname);` | Removes secondary index `piname` from data file `pfname`'s label metadata and deletes the index file from disk. |

---

## Unit TEEnv

Defines shared Table Editor environment types (panels, cell ranges, snips, view bands, and table configuration records) and provides panel GrafPort, coordinate conversion, clipping, and range helper routines.

- **Import**: `USES TEEnv;`
- **Unit kind**: `INTRINSIC` (`TEENV`)
- **Interface dependencies**: `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `DBEnv`, `FEDec`, `FieldEdit`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `AdjRect` | `PROCEDURE AdjRect(Pnl: PnlIndex; VAR r: rect);` | Offsets panel-relative rectangle `r` by panel `Pnl`'s origin to convert it into folder-relative coordinates. |
| `AdjToPnl` | `PROCEDURE AdjToPnl(Pnl: PnlIndex; P: Point; VAR relPoint: Point);` | Converts folder-relative point `P` into coordinates relative to panel `Pnl` (clamped to the panel's bounds) in `relPoint`. |
| `allocPnl` | `PROCEDURE allocPnl(thePnl: PnlIndex);` | Allocates a `Panel` descriptor handle on `theHeap` and stores it in the global panel table at index `thePnl`. |
| `ChgPnlSize` | `PROCEDURE ChgPnlSize(P: PnlIndex; Width, Height: Pixel);` | Sets the width and height of panel `P`'s local `pnlRect` (clamping negative dimensions to zero). |
| `FreePnl` | `PROCEDURE FreePnl(thePnl: PnlIndex);` | Frees the heap handle for panel descriptor `thePnl` unless it is the dedicated offscreen `cCellPnl`. |
| `GetPnlBits` | `PROCEDURE GetPnlBits(P: pnlIndex; VAR b: bitptr);` | Returns a pointer `b` to the QuickDraw `portBits` bitmap of the `GrafPort` associated with panel `P`. |
| `GetPnloffset` | `PROCEDURE GetPnloffset(Pnl: pnlIndex; VAR offset: point);` | Returns the folder-relative top-left `offset` point of panel `Pnl`. |
| `GetPnlRect` | `PROCEDURE GetPnlRect(PNL: PnlIndex; VAR aPnlRect: Rect);` | Returns the panel-relative bounding rectangle `aPnlRect` of panel `PNL`. |
| `InitPnls` | `PROCEDURE InitPnls(var status: integer);` | Initializes standard panel indices, opens the offscreen cell editing port (`CellPort`) and bitmap, and allocates standard Table Editor panels. |
| `MovePnl` | `PROCEDURE MovePnl(P: PnlIndex; Offset: point);` | Sets the folder-relative origin offset of panel `P` to `Offset`. |
| `ptInPnl` | `FUNCTION ptInPnl(portptr: grafptr; loc: point; hipnl: pnlindex): PnlIndex;` | Finds and returns the index of the panel (`2..hipnl`) sharing `portptr` whose bounds contain folder-relative point `loc`, or `nullPnl` if none matches. |
| `rgEq` | `function rgEq(aRg, bRg: range): boolean;` | Returns `true` if ranges `aRg` and `bRg` have identical `rKind` and row/column boundary coordinates. |
| `SectPnl` | `Function SectPnl(Pnl: pnlIndex; portptr: grafptr; updrgn: rgnhandle; resultrgn: rgnhandle): BOOLEAN;` | Intersects folder update region `updrgn` with panel `Pnl`'s folder-relative bounds into `resultrgn` (shifted to panel coordinates) and returns `true` if non-empty. |
| `SetPnlPort` | `PROCEDURE SetPnlPort(P: PnlIndex);` | Activates panel `P`'s QuickDraw `GrafPort`, sets the coordinate origin to `-offset`, and clips to the panel's `pnlRect`. |
| `setRg` | `procedure setRg(var aRg: range; aKind: rgKind; aLoRow, aLoCol, aHiRow, aHiCol: idType);` | Populates `aRg` with the specified range kind `aKind` and row/column bounds (`aLoRow`, `aLoCol`, `aHiRow`, `aHiCol`). |
| `SetUpPnl` | `PROCEDURE SetUpPnl(P: PnlIndex; portptr: grafptr; width, Height: pixel; loc: point);` | Configures panel `P` with QuickDraw port `portptr`, panel dimensions `width` by `height`, and folder-relative origin `loc`. |

---

## Unit TM

Implements the shared Table Manager and Table Selection Manager (`tmsProcs`) for tabular Lisa applications, handling split-view band layout, scrolling, cell/range highlighting and marquees, in-cell and wide-angle-view (`wavPnl`) FieldEdit text editing, and clipboard operations.

- **Import**: `USES TM;`
- **Unit kind**: `INTRINSIC` (`TM`)
- **Interface dependencies**: `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `DBEnv`, `FEDec`, `FieldEdit`, `TEEnv`, `WmlStd`, `WmlSb`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `ChgRgBorders` | `procedure ChgRgBorders(newRg: range; shoMarquee: boolean);` | Updates displayed range border highlighting from the previous range to `newRg` and adjusts the animated marquee state according to `shoMarquee`. |
| `DumpSel` | `procedure DumpSel;` | Detaches the Table Manager from any active cell editing selection by resetting `editRow` and `editCol` to `nullSnip` so `underEdit` returns `false`. |
| `EndRgBorders` | `procedure EndRgBorders;` | Erases any currently displayed range highlight or border feedback across all table views and releases its internal border data structures. |
| `FindTblPt` | `procedure FindTblPt(hv: point; var PrtOfTbl: tblPart; var rg: range; var virtRect, screenRect: rect);` | Classifies table-panel point `hv` into its `tblPart` (`PrtOfTbl`), corresponding logical `range` (`rg`), virtual cell rectangle (`virtRect`), and clipped `screenRect`. |
| `getCR` | `procedure getCR(var rg: range);` | Copies the Table Manager's current range (`CurrRg`) into `rg`. |
| `getEditCell` | `procedure getEditCell(var theRow: idType; var theCol: idType);` | Returns the row and column snip IDs (`theRow`, `theCol`) of the cell currently undergoing editing, or `nullSnip` if none. |
| `grayOfBand` | `function grayOfBand(aKind: snipKind; aP: pixel): fract;` | Returns the proportion (in per-mille, `0..1000`) of off-table gray background currently visible in the `aKind` view band located at pixel `aP`. |
| `growBand` | `procedure growBand(aKind: snipKind; aP: pixel; var newP: pixel; var result: BGrowResult);` | Resizes (or deletes when `newP = -1`) the `aKind` split band containing pixel `aP` so its upper split-skewer boundary moves to `newP`, returning the outcome in `result`. |
| `LDtmgr` | `procedure LDtmgr;` | No-op segment-loader stub that forces the primary Table Manager code segment (`TEwork1`) into memory. |
| `LDtmLoFreq` | `procedure LDtmLoFreq;` | No-op segment-loader stub that forces the low-frequency Table Manager code segment (`TEcold`) into memory. |
| `NewRgBorders` | `procedure NewRgBorders(newRg: range; useMarquee: boolean);` | Builds and draws range border or selection marquee feedback across all split views for `newRg` when no range border is currently active. |
| `NewRgImg` | `procedure NewRgImg(rg: range);` | Redisplays all visible cells intersecting range `rg` across every split view after cell values or attributes have changed. |
| `PtIn1CRg` | `function PtIn1CRg(hv: point; targRg: range): boolean;` | Returns `true` if `targRg` is a single field-like range (single cell, row/column heading, or table heading) and table point `hv` lies within its visible display. |
| `ReBldTbl` | `procedure ReBldTbl(initRg: range);` | Loads new table parameters (`tmNewPars`), resets view bands (`tmLoadBands`), and installs a single unsplit view showing the upper-left corner of `initRg` without drawing. |
| `ScrBand` | `procedure ScrBand(aKind: snipKind; aP: pixel; scrScale: ScrollType; scrDir: ScrollDir; scrFract: fract; var didMove: boolean);` | Scrolls the `aKind` view band at pixel `aP` by increment, page, or thumb fraction (`scrScale`, `scrDir`, `scrFract`) and sets `didMove` if the band position changed. |
| `setCR` | `procedure setCR(rg: range);` | Sets the Table Manager's internal current range (`CurrRg`) to `rg` without altering screen feedback. |
| `shoNewRg` | `procedure shoNewRg(oldRg: range; newRg: range; just: rgJust);` | Scrolls the active view if necessary so that `newRg` becomes visible according to justification rule `just`. |
| `ShoNewWid` | `procedure ShoNewWid(aKind: snipKind; loSnip, hiSnip: idType);` | Reconstructs and redraws all view bands containing `aKind` snips in `loSnip..hiSnip` after their pixel widths or heights have changed. |
| `ShoTbl` | `procedure ShoTbl(shoRgnH: rgnHandle);` | Draws the entire table display (headings, grid lines, split skewers, cells, and highlights) from scratch within clip region `shoRgnH`. |
| `snipAllInBand` | `function snipAllInBand(aKind: snipKind; aP: pixel; snipId: idType): boolean;` | Returns `true` if the entire pixel width or height of `snipId` is completely visible within the `aKind` band at pixel `aP`. |
| `SplitBand` | `procedure SplitBand(aKind: snipKind; var atP: pixel; var didSplit: boolean);` | Splits the `aKind` view band at pixel `atP` into two independent scrollable bands separated by a skewer line, updating `atP` and setting `didSplit`. |
| `tmCurVwPt` | `procedure tmCurVwPt(var vwPt: point);` | Returns a table-panel point `vwPt` guaranteed to lie inside the currently active split view. |
| `tmCurVwSet` | `procedure tmCurVwSet(vwPt: point);` | Sets the active split view to the view containing table-panel point `vwPt`. |
| `tmFAct` | `procedure tmFAct(fActivate: boolean);` | Updates table selection highlight and marquee display state when the containing document folder is activated (`fActivate = true`) or deactivated. |
| `tmInit` | `procedure tmInit;` | Performs one-time initialization of table-independent Table Manager regions, band/snip free lists, and the offscreen cell rendering field. |
| `tmLoadBands` | `procedure tmLoadBands;` | Releases all existing view band and snip layout descriptors onto internal free lists in preparation for `tmLoadNextBand` calls. |
| `tmLoadNextBand` | `procedure tmLoadNextBand(aTmBand: tmBand);` | Installs a saved row or column band descriptor `aTmBand` into the Table Manager's screen layout (with `nullSnip` signaling completion). |
| `tmLoadState` | `procedure tmLoadState(atmstate: tmstate);` | Restores the Table Manager's saved highlight range, selection mode, visibility, border, and marquee flags from `atmstate`. |
| `tmNewPars` | `procedure tmNewPars;` | Initializes table-dependent layout metrics, heading dimensions, and grid/handle parameters from `TblPars` when loading or reconfiguring a table. |
| `tmNewSnips` | `procedure tmNewSnips(aKind: snipKind; priorSnip: idType; scrollit: boolean);` | Rebuilds band snip structures and updates affected views after `aKind` rows or columns following `priorSnip` have been inserted, deleted, or renumbered. |
| `tmNextBandRg` | `procedure tmNextBandRg(var bandsnip: snipKind; var bandloId, bandhiId: idType);` | Returns the orientation (`bandsnip`) and visible low/high snip IDs (`bandloId`, `bandhiId`) of the next view band during band iteration, or `nullSnip` when done. |
| `tmReDoViews` | `procedure tmReDoViews;` | Recomputes all split views from their current origin snips and redraws the entire table and active range highlights. |
| `tmReSize` | `procedure tmReSize;` | Recomputes band boundaries and redraws the table layout after the table panel (`tblPnl`) has been resized. |
| `tmSaveBands` | `procedure tmSaveBands;` | Initializes internal band iteration (starting with row bands, then column bands) prior to `tmSaveNextBand` or `tmNextBandRg` calls. |
| `tmSaveNextBand` | `procedure tmSaveNextBand(var aTmBand: tmBand);` | Returns the next `tmBand` layout descriptor in `aTmBand` (or sets `tmbLoId` to `nullSnip` when all row and column bands have been enumerated). |
| `tmsavestate` | `procedure tmsavestate(var atmstate: tmstate);` | Saves the Table Manager's current highlight range, selection, border, and marquee state into `atmstate`. |
| `tmSetRgFB` | `procedure tmSetRgFB(cRg: range; useMarquee: boolean);` | Establishes and draws range highlight feedback (with optional animated marquee `useMarquee`) for newly loaded current range `cRg`. |
| `tmShoBreaks` | `procedure tmShoBreaks;` | Redraws row and column grid lines across all views to reflect updated automatic or forced page-break indicators. |
| `tmShoNewTbl` | `procedure tmShoNewTbl;` | Renders the newly loaded table across the full table panel region (`tblRgnH`). |
| `TurnOffMarquee` | `procedure TurnOffMarquee;` | Removes any active selection marquee from visible range borders and suppresses marquee animation until `TurnOnMarquee` is called. |
| `TurnOnMarquee` | `procedure TurnOnMarquee;` | Re-enables and displays animated selection marquees around visible range borders. |
| `underEdit` | `function underEdit(aRow, aCol: idType): boolean;` | Returns `true` if table editing is enabled and the cell or heading at `(aRow, aCol)` is currently undergoing FieldEdit editing. |
| `visRgOfView` | `procedure visRgOfView(aPt: point; var aRg: range);` | Sets `aRg` to the rectangular range of all cells at least partially visible in the split view containing point `aPt`. |
| `InitProcInfo` | `procedure InitProcInfo(CellInfo: ProcPtr; CellRun: ProcPtr; CellValue: ProcPtr; FoldedFormula: ProcPtr; GetSnipId: ProcPtr; mmBreakSnip: ProcPtr; mmMapSnip: ProcPtr; SetSnipWidth: ProcPtr; SnipLT: ProcPtr; SnipWidth: ProcPtr; FatalError: ProcPtr);` | Registers the eleven Matrix Manager and error callback procedure pointers (`CellInfo`, `CellRun`, `CellValue`, `FoldedFormula`, `GetSnipId`, `mmBreakSnip`, `mmMapSnip`, `SetSnipWidth`, `SnipLT`, `SnipWidth`, and `FatalError`) used by the Table Manager. |
| `boldflds` | `PROCEDURE boldflds(var status: integer);` | Applies bold character formatting (`setbold`) to the FieldEdit text runs of both the in-cell selection field and the wide-angle-view field. |
| `CellChanged` | `Function CellChanged: Boolean;` | Returns `true` if text in either the in-cell FieldEdit field or the active wide-angle-view field has been modified since editing began. |
| `ChangeCellFont` | `PROCEDURE ChangeCellFont;` | Updates the font and field rectangle geometry of the active in-cell selection after a table font or column width change. |
| `ClearSel` | `PROCEDURE ClearSel(VAR status: integer);` | Clears the selected text (or entire field contents) in the active cell and wide-angle-view editing fields. |
| `CopySel` | `Procedure CopySel(VAR status: integer);` | Copies the currently selected text from the active cell or heading FieldEdit field into the system Scrap. |
| `CutSel` | `PROCEDURE CutSel(VAR status: integer);` | Cuts the currently selected text from the active cell or heading FieldEdit field into the system Scrap and updates the wide-angle view. |
| `DoSelAct` | `Procedure DoSelAct(Activate: boolean);` | Activates or deactivates visual caret/selection highlighting in the Table Selection Manager when the folder gains or loses focus. |
| `DoSelCR` | `PROCEDURE DoSelCR(aRg: Range; VAR timeout: INTEGER; hilite: cellseltype);` | Establishes selection state and visual cell/text highlighting (`selectCell`, `selectContents`, or `PutCaretAtEnd`) for range `aRg`, returning the caret blink `timeout`. |
| `DoTblSel` | `PROCEDURE DoTblSel(P: point; VAR Nbh: Rect; VAR Timeout: INTEGER);` | Initiates an in-cell text selection at table point `P` on mouse-down inside an already-selected cell, returning drag neighborhood `Nbh` and blink `Timeout`. |
| `DoWavSel` | `PROCEDURE DoWavSel(P: Point; VAR Nbh: Rect; VAR Timeout: Integer);` | Initiates a FieldEdit text selection at point `P` inside the wide-angle-view panel (`widePnl`), synchronizing cell feedback and returning `Nbh` and `Timeout`. |
| `EndCR` | `PROCEDURE EndCR;` | Ends the current selection and range, removing range borders, erasing the wide-angle view, and exiting FieldEdit fields. |
| `EnterSelection` | `PROCEDURE EnterSelection(VAR Status: Integer);` | Commits edited text and formatting runs from the active cell/wide-angle-view field back into the Matrix Manager via `CellValue` and `CellRun`. |
| `EraseWav` | `PROCEDURE EraseWav;` | Erases the wide-angle-view panel (`widePnl`) on screen while preserving its underlying `wavField` and `wavFstate` handles. |
| `ExitSel` | `PROCEDURE ExitSel;` | Exits FieldEdit editing and reinitializes field states for both the wide-angle-view and in-cell selection fields. |
| `ExtendSel` | `PROCEDURE ExtendSel(P: point; VAR nbh: Rect; VAR delta: INTEGER);` | Extends the current cell, range, or in-cell text selection to point `P` (such as on Shift-click or drag), returning updated `nbh` and timeout `delta`. |
| `GetSelKind` | `procedure GetSelKind(var theSelKind: selKind);` | Returns the Table Selection Manager's current selection kind (`SelKind`) in `theSelKind`. |
| `InitSelMgr` | `PROCEDURE InitSelMgr(wavActFlg: boolean; maxLenWav: integer; growdata: integer; growrun: integer);` | Initializes the Table Selection Manager, allocating the in-cell and wide-angle-view (`maxLenWav`) FieldEdit structures with growth increments `growdata` and `growrun`. |
| `InKey` | `PROCEDURE InKey(ch: char; shiftflag: boolean; cmdflag: Boolean; resetrun: boolean; VAR Timeout: INTEGER; VAR status: INTEGER);` | Processes a typed character `ch` (including Backspace and modifier flags) within the active cell and wide-angle-view FieldEdit fields, returning `Timeout` and `status`. |
| `LDsmgr` | `Procedure LDsmgr;` | No-op segment-loader stub that brings the Table Selection Manager code segment (`TEwork2`) into memory. |
| `MovePointer` | `Procedure MovePointer(P: Point; var pRg: range; var nbh: rect);` | Tracks Option-drag pointer movement to table point `P` during formula range pointing, updating pointed range `pRg` and drag neighborhood `nbh` without altering the active selection. |
| `MseUp` | `PROCEDURE MseUp(P: Point; VAR delta: INTEGER);` | Finalizes column-grid dragging or cell/text selection state when the mouse button is released at table point `P`, returning caret blink interval `delta`. |
| `NewNbh` | `PROCEDURE NewNbh(P: point; VAR nbh: Rect; VAR delta: INTEGER);` | Updates the dragged cell range, grid resize tracker, or in-cell text selection when the mouse moves outside its neighborhood to table point `P`, returning new `nbh` and `delta`. |
| `NewNbhWav` | `PROCEDURE NewNbhWav(P: Point; VAR nbh: Rect; VAR delta: Integer);` | Extends the text selection in the wide-angle-view panel (and mirrors it in the active cell) when the mouse drags to `P`, returning new `nbh` and `delta`. |
| `NewTimOut` | `PROCEDURE NewTimOut(VAR delta: INTEGER);` | Services a timer expiration for the Table Selection Manager by redrawing invalidated editing fields, blinking the text caret, or animating range marquees, returning the next timeout `delta`. |
| `NewWSel` | `PROCEDURE NewWSel(P: Point; Pnl: PnlIndex; VAR Nbh: Rect; VAR timeout: integer);` | Handles the second click of a double-click at point `P` in `Pnl` (`tblPnl` or `widePnl`) by selecting the surrounding word and returning `Nbh` and `timeout`. |
| `NullCR` | `PROCEDURE NullCR;` | Ends any active selection and resets `CurrRg` to `aNullRg` when a mouse-down occurs outside the table. |
| `NullSel` | `PROCEDURE NullSel;` | Resets the Table Selection Manager's selection kind (`TypeOfSel`) to `aNullSl`. |
| `PackSMGR` | `Procedure PackSMGR(hndsusdata: hnddata; offset: integer; curlen: integer; var leninstalled: integer; var newlen: integer);` | Serializes the Table Selection Manager's state, cell/wide-angle-view FieldEdit fields, and formatting runs into suspend buffer `hndsusdata` at `offset`. |
| `PasteSel` | `PROCEDURE PasteSel(pasteruns: boolean; PasteLimit: integer; var status: integer);` | Pastes text (and optional formatting runs up to `PasteLimit` characters) from the Scrap into the active cell and wide-angle-view FieldEdit fields. |
| `PointAtRg` | `Procedure PointAtRg(P: Point; var pRg: range; var nbh: rect);` | Computes the cell, row, column, or table range `pRg` pointed to by an Option-click at `P` (without changing the active selection) and returns drag neighborhood `nbh`. |
| `reDrawSel` | `PROCEDURE reDrawSel(showselect: boolean);` | Redraws the FieldEdit contents (and selection highlighting if `showselect` is `true`) in the active cell panel and wide-angle-view panel. |
| `ReInitSelMgr` | `PROCEDURE ReInitSelMgr;` | Resets Table Selection Manager state variables (`TypeOfSel`, `editRow`, `editCol`, `tGridh`, and `CurrRg`) to their null initial values. |
| `restoreRgFB` | `PROCEDURE restoreRgFB(var timeout: integer);` | Restores Table Manager range border/marquee feedback and restarts caret blinking (`timeout`) for the current selection. |
| `ReSelCR` | `PROCEDURE ReSelCR(VAR timeout: INTEGER; hilite: cellseltype);` | Re-establishes cell/text selection and `hilite` feedback on the existing `CurrRg` and returns the updated caret `timeout`. |
| `restoreflds` | `PROCEDURE restoreflds(var curtimeout: integer);` | Reloads the in-cell and wide-angle-view FieldEdit structures from `CurrRg` and restores selection feedback after unsuspending or reinitializing. |
| `resizeflds` | `PROCEDURE resizeflds;` | Recalculates the bounding and clipping rectangles of the active in-cell and wide-angle-view FieldEdit fields after column widths or panel sizes change. |
| `SelAllTxt` | `PROCEDURE SelAllTxt(VAR timeout: INTEGER);` | Selects all text in both the active cell field and the wide-angle-view field, refreshes the cell image, and starts caret/selection feedback (`timeout`). |
| `SelNewCell` | `PROCEDURE SelNewCell(P: point; hilite: cellseltype; VAR nbh: Rect; VAR timeout: integer);` | Selects the table cell or part under point `P` with highlighting mode `hilite`, returning drag neighborhood `nbh` and blink `timeout`. |
| `SetAnchorCell` | `PROCEDURE SetAnchorCell(RowId, colId: idtype);` | Sets the range-selection anchor cell coordinates (`strow`, `stcol`) to `(RowId, colId)`. |
| `SetCellStr` | `PROCEDURE SetCellStr(str: str40);` | Initializes the in-cell and wide-angle-view FieldEdit fields for the current range with initial string `str` and marks that cell as under edit. |
| `UNDOSEL` | `PROCEDURE UNDOSEL(VAR status: integer);` | Reverts the last FieldEdit text edit in the wide-angle-view and in-cell selection fields. |
| `ValidCoord` | `Function ValidCoord(rg: range): Boolean;` | Returns `true` if `rg` is a single-cell range (`a1CellRg`) with finite, non-null row and column snip IDs inside the cell area. |
| `WhTblSel` | `PROCEDURE WhTblSel(rg: range; var nbh: Rect; var timeout: integer);` | Selects the entire table (`aWTBoxSl`) with range `rg`, draws whole-table range borders, and returns table panel bounds in `nbh`. |
| `unboldflds` | `PROCEDURE unboldflds(var status: integer);` | Restores normal (non-bold) font styling (`setnormal`) to the FieldEdit text runs of both the in-cell and wide-angle-view fields. |
| `UnpackSMGR` | `Procedure UnpackSMGR(HndSdata: Hnddata; offset: integer);` | Restores the Table Selection Manager's state, FieldEdit text buffers, and formatting runs from suspend data handle `HndSdata` at `offset`. |

---

## Unit VLTree

Implements variable-length B-tree (`VLTree`) page and key management for Lisa database data, index, and label files, including fast in-page insert/update/delete, page splitting, sibling rotation and coalescing, duplicate resolution, and keyed searches.

- **Import**: `USES VLTree;`
- **Unit kind**: `INTRINSIC` (`VLTREE`)
- **Interface dependencies**: `DBEnv`, `International`, `DBDecl1`, `SysCall`, `LowLevel`, `Pooler`, `Heap`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `entrysize` | `function entrysize(firstfld, lastfld, doitfld, isize: integer; pedesc: ptrrecptr; prec: ptrdata): integer;` | Computes the even-rounded total byte size of record `prec` by adding the lengths of variable-length fields in `firstfld..lastfld` (using descriptor `pedesc`) to fixed size `isize`. |
| `quickinsert` | `function quickinsert(fileid: integer; pagetype: integer; pnewrec: ptrdata; size: integer; pfptr: ptrfileptr; canmove: boolean; index, buff1: integer; var ipage: fileptr; var iindex: integer): boolean;` | Inserts `size`-byte record `pnewrec` (and optional nonleaf page pointer `pfptr`) at `index` in buffered page `buff1` if it fits without splitting or rotating, returning `true` only if a split or rotation is required. |
| `quickDelete` | `function quickDelete(var kresult: integer; onfile: integer; qpage: fileptr; qindex: integer): boolean;` | Deletes the record at `(qpage, qindex)` in `onfile` directly in place if doing so does not cause B-tree page underflow, returning `true` if the deletion succeeded. |
| `quickUpdate` | `function quickUpdate(var kresult: integer; onfile: integer; pnewrec: ptrdata; size: integer; qpage: fileptr; qindex: integer): boolean;` | Replaces the record at `(qpage, qindex)` in `onfile` in place with `size`-byte `pnewrec` if no overflow, underflow, or record relocation occurs, returning `true` if updated. |
| `splitORrotate` | `function splitORrotate(var kresult: integer; fileid: integer; pagetype: integer; pnewrec: ptrdata; size: integer; pfptr: ptrfileptr; canmove: boolean; index, buff1: integer; leftsib, rightsib: fileptr; var buff2: integer; var ipage: fileptr; var iindex: integer; ps: ptrstackrec; var sibpage: fileptr): integer;` | Inserts `pnewrec` at `index` of full B-tree page `buff1` by rotating records into `leftsib` or `rightsib` if space permits or splitting `buff1` into a new page `buff2`. |
| `firstleaf` | `procedure firstleaf(var kresult: integer; fileid: integer; pagetype: integer; pnewrec: ptrdata; size: integer; var ipage: fileptr; var iindex: integer);` | Allocates and writes the initial root leaf or label page of `fileid` containing `size`-byte record `pnewrec`, returning its page address `ipage` and index `iindex`. |
| `pagedelete` | `function pagedelete(var kresult: integer; fileid: integer; pagetype: integer; buffer, index: integer; closestsib: fileptr; var rbuff: integer; var dpage: fileptr; var dindex: integer): integer;` | Deletes record `index` from B-tree page `buffer` in `fileid`, rotating from or coalescing with `closestsib` on underflow and returning the successor position `(dpage, dindex)` and disposition code. |
| `findduplicate` | `procedure findduplicate(var kresult: integer; fileid: integer; pedesc, psdesc: ptrrecptr; nsearch: integer; is_insert, duplimpossible: boolean; pkey: ptrdata; var buffer, index: integer; var stackinvalid: integer);` | Scans left or right across leaf pages from `(buffer, index)` to locate the first record matching `pkey` on `nsearch` fields, reporting whether traversal crossed pages in `stackinvalid`. |
| `nextprior` | `procedure nextprior(var kresult: integer; fileid: integer; var buffer, index: integer; which: integer);` | Advances (`which = next`) or backs up (`which = prior`) from `(buffer, index)` in `fileid` to the adjacent B-tree leaf record, crossing sibling page links as needed. |
| `find` | `procedure find(var kresult: integer; which: integer; nsearch: integer; fileid: integer; psdesc: ptrrecptr; pkey: ptrdata; var buffer: integer);` | Traverses the B-tree of `fileid` from root to leaf (`first`, `last`, `approx`, or `exact` on `pkey`), recording the path in `pstack` and returning the target leaf `buffer`. |
| `findkeyed` | `procedure findkeyed(var kresult: integer; which: integer; nsearch: integer; fileid: integer; psdesc: ptrrecptr; pkey: ptrdata; var buffer, buffindex: integer);` | Finds a keyed entry in `fileid` according to `which` (`first`, `last`, `approx`, `exact`, `next`, or `prior`), returning the locked leaf `buffer` and slot `buffindex`. |
| `insertkeyed` | `procedure insertkeyed(var kresult: integer; fileid: integer; pkey: ptrdata; size: integer; var ipage: fileptr; var iindex: integer);` | Inserts `size`-byte keyed record `pkey` into B-tree file `fileid` (propagating any leaf splits or rotations up the tree and rolling back on `noroom`), returning `(ipage, iindex)`. |
| `deletekeyed` | `procedure deletekeyed(var kresult: integer; fileid: integer; pkey: ptrdata; var dpage: fileptr; var dindex: integer);` | Deletes the entry matching `pkey` from B-tree file `fileid`, rebalancing ancestor pages on underflow and returning the successor record position `(dpage, dindex)`. |
