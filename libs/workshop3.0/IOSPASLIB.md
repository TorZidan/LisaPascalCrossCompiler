# `IOSPASLIB` (`iospaslib.obj`) — Lisa OS Pascal & Clascal Runtime Library

[Back to Library Index](LIBRARIES.md)

Core Pascal and Clascal runtime support: standard I/O, UCSD-compatible block file I/O (`BlockRead`/`BlockWrite`), Pascal dynamic heap management, `TTerminal` console abstraction, and Clascal object/method dispatch.

- **Object file**: `libs/workshop3.0/iospaslib.obj` (Intrinsic library)
- **Contents**: 5 units, 67 top-level procedures/functions, 1 Clascal class (13 methods)

## Importing and Linking

```pascal
USES BlkIOIntr, BlockIO, PasHeap;
```

```sh
pascal/lpc.py --link=IOSPASLIB MYPROG
```

## Units in This Library

| Unit | 8-Char Symbol | `USES` Dependencies | Top-Level Routines | Clascal Classes (Methods) | Summary |
|---|---|---|---|---|---|
| [`BlkIOIntr`](#unit-blkiointr) | `BLKIOINT` | `SysCall`, `UClascal` | 3 | 1 (13) | Holds per-process private Pascal I/O runtime state (`IORslt`, standard `INPUT`/`OUTPUT` FIBs, resident restart environment, and window nesting counters) and declares the abstract `TTerminal` Clascal hook class used by `UStdTerm` to route console and printer I/O into Desktop/Workshop windows. |
| [`BlockIO`](#unit-blockio) | `BLOCKIO` | `SysCall`, `psyscall`, `BlkIOIntr` | 34 | 0 | Implements the shared intrinsic (`INTRINSIC SHARED`) Pascal I/O runtime backing standard `Reset`, `Rewrite`, `Close`, `BlockRead`, `BlockWrite`, `Get`, `Put`, `Read`/`ReadLn`, `Write`/`WriteLn`, `Seek`, and `GotoXY`, along with Workshop Shell console routing, Exec script input, and output redirection. |
| [`PasHeap`](#unit-pasheap) | `PASHEAP` | `SysCall` | 11 | 0 | Implements the Lisa Pascal dynamic memory manager backing compiler intrinsics `New`, `Mark`, `Release`, `MemAvail`, and `HeapResult` over a private Lisa OS data segment that grows and shrinks in 512-byte-aligned increments. |
| [`PasLib`](#unit-paslib) | `PASLIB` | — | 0 | 0 | Core Lisa Pascal compiler runtime intrinsic unit whose object code supplies the low-level MC68000 assembly support routines (`%_BEGIN`, `%_INIT`, `%_TERM`, 32-bit integer arithmetic, string and set operations, range checks, and formatted text `Read`/`Write` dispatchers) implicitly linked into compiled Pascal programs; its Pascal interface exports no direct user-callable declarations. |
| [`UClascal`](#unit-uclascal) | `UCLASCAL` | `SysCall` | 19 | 0 | Implements the Clascal object-oriented runtime system, building per-class method slice tables and class/author/alias metadata dictionaries during program initialization and providing compiler intrinsics for dynamic `InClass` membership tests and range-checked object typecasts. |

---

## Unit BlkIOIntr

Holds per-process private Pascal I/O runtime state (`IORslt`, standard `INPUT`/`OUTPUT` FIBs, resident restart environment, and window nesting counters) and declares the abstract `TTerminal` Clascal hook class used by `UStdTerm` to route console and printer I/O into Desktop/Workshop windows.

- **Import**: `USES BlkIOIntr;`
- **Unit kind**: `INTRINSIC` (`BLKIOINT`)
- **Interface dependencies**: `SysCall`, `UClascal`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `%_FIORESULT` | `FUNCTION %_FIORESULT: INTEGER;` | Returns the calling process's stored `IORslt` status code from the most recent Pascal I/O operation (implementing `IOResult`). |
| `%_Setiorslt` | `PROCEDURE %_Setiorslt(ior: integer);` | Sets the calling process's Pascal `IORslt` status variable to `ior` (used internally by `FPLib` and text I/O scanners). |
| `%_Backupinput` | `PROCEDURE %_Backupinput(var f: text);` | Marks text file `f`'s FIB state as `FGotChar` so its current lookahead character `f^` will be re-consumed on the next read. |

### Clascal Classes

#### `TTerminal = SUBCLASS OF NIL`

Abstract Clascal root class (`SUBCLASS OF NIL`) defining the virtual console and printer dispatch interface implemented by `UStdTerm` to redirect standard Pascal terminal and `-PRINTER` I/O into a window environment.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE: TTerminal; Abstract;` | Abstract constructor stub overridden by concrete terminal subclasses (such as in `UStdTerm`) to instantiate a virtual terminal. |
| `VWrite` | `PROCEDURE VWrite(VAR str: Tstr255); Abstract;` | Abstract method that writes up to 255 characters from `str` to the virtual terminal window. |
| `VRead` | `FUNCTION VRead: CHAR; Abstract;` | Abstract method that reads and returns the next input character from the virtual terminal window. |
| `VGotoxy` | `PROCEDURE VGotoxy(x, y: INTEGER); Abstract;` | Abstract method that moves the virtual terminal cursor to column `x` and row `y`. |
| `VKeyPress` | `FUNCTION VKeyPress: BOOLEAN; Abstract;` | Abstract method that returns `TRUE` if a character keystroke is waiting in the virtual terminal input queue. |
| `VAbortKey` | `FUNCTION VAbortKey: BOOLEAN; Abstract;` | Abstract method that returns `TRUE` if the user pressed the Apple-Period abort key combination in the terminal window. |
| `VScreenCtr` | `PROCEDURE VScreenCtr(contrfun: INTEGER); Abstract;` | Abstract method that performs terminal screen-control operation `contrfun` (clear screen/line or cursor motion) in the window. |
| `OpenPrinter` | `FUNCTION OpenPrinter: INTEGER; Abstract;` | Abstract method that opens a windowed print document for `-PRINTER` output and returns a Pascal `IOResult` code. |
| `PrWrite` | `FUNCTION PrWrite(VAR str: Tstr255): INTEGER; Abstract;` | Abstract method that writes string `str` to the open windowed printer stream and returns a Pascal `IOResult` code. |
| `ClosePrinter` | `FUNCTION ClosePrinter: INTEGER; Abstract;` | Abstract method that closes and submits the active windowed print document and returns a Pascal `IOResult` code. |
| `CleanUp` | `PROCEDURE CleanUp; Abstract;` | Abstract termination hook invoked by `%_CkResident` to handle window Set Aside or Put Away cleanup when a windowed program exits. |
| `SetupIOFile` | `PROCEDURE SetupIOFile;` | Configures the calling process's local `PInputfile` and `POutputfile` FIBs to route standard `INPUT` and `OUTPUT` through `unitWiConsole` (`PConsWindow := TRUE`). |
| `InWindow` | `PROCEDURE InWindow(yesno: BOOLEAN);` | Increments (`yesno = TRUE`) or decrements (`yesno = FALSE`) the `PInWindow` nesting counter so nested debug I/O bypasses the window and uses the alternate screen. |

---

## Unit BlockIO

Implements the shared intrinsic (`INTRINSIC SHARED`) Pascal I/O runtime backing standard `Reset`, `Rewrite`, `Close`, `BlockRead`, `BlockWrite`, `Get`, `Put`, `Read`/`ReadLn`, `Write`/`WriteLn`, `Seek`, and `GotoXY`, along with Workshop Shell console routing, Exec script input, and output redirection.

- **Import**: `USES BlockIO;`
- **Unit kind**: `INTRINSIC SHARED` (`BLOCKIO`)
- **Interface dependencies**: `SysCall`, `psyscall`, `BlkIOIntr`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `%_FINIT` | `PROCEDURE %_FINIT(VAR F: FIB; WINDOW: WINDOWP; recbytes: INTEGER);` | Compiler intrinsic that initializes File Information Block `F` with window pointer `WINDOW` and record byte size `recbytes` (`0` = interactive, `-2` = text, `-1` = untyped, `> 0` = typed record size). |
| `%_FOPEN` | `PROCEDURE %_FOPEN(VAR F: FIB; VAR FTITLE: pathname; FOPENOLD: BOOLEAN; JUNK: longint);` | Compiler intrinsic backing `Reset` (`FOPENOLD = TRUE`) and `Rewrite` (`FOPENOLD = FALSE`) that opens or creates Lisa OS file or pseudo-device `FTITLE` (`-CONSOLE`, `-KEYBOARD`, `-PRINTER`) on FIB `F`. |
| `%_FCLOSE` | `PROCEDURE %_FCLOSE(VAR F: FIB; FTYPE: integer);` | Compiler intrinsic backing `Close` that flushes buffers, commits or purges temporary rewrite files, and closes FIB `F` according to `FTYPE` (`CNormal`, `CLock`, `CPurge`, `CCrunch`). |
| `%_FBLOCKIO` | `FUNCTION %_FBLOCKIO(VAR F: FIB; A: longint; NBLOCKS, RBLOCK: INTEGER; DOREAD: BOOLEAN): INTEGER;` | Compiler intrinsic backing `BlockRead` (`DOREAD = TRUE`) and `BlockWrite` (`DOREAD = FALSE`) that transfers `NBLOCKS` 512-byte blocks between memory address `A` and FIB `F` at block `RBLOCK` (`-1` for sequential), returning blocks transferred. |
| `%_FGET` | `PROCEDURE %_FGET(VAR F: FIB);` | Compiler intrinsic backing `Get(F)` that loads the next record or character into `F.FWindow^`, expanding DLE blank-compression runs and skipping 1 KB page NUL padding on text files. |
| `%_FPUT` | `PROCEDURE %_FPUT(VAR F: FIB);` | Compiler intrinsic backing `Put(F)` that copies the current record or character from `F.FWindow^` into `F`'s 512-byte buffer, flushing full blocks and padding 1 KB text pages as needed. |
| `%_WRITELN` | `PROCEDURE %_WRITELN(VAR F: FIB);` | Compiler intrinsic backing `WriteLn` on FIB `F` that outputs a carriage-return (`#13`) end-of-line character via `%_WRITECHAR`. |
| `%_WRITECHAR` | `PROCEDURE %_WRITECHAR(VAR F: FIB; charaddr: longaddr; count: integer);` | Writes `count` characters from `charaddr` to FIB `F`, routing output to the console, `TTerminal` window, printer (with optional Lisa character translation), redirected output file, or disk buffer. |
| `%_READLN` | `PROCEDURE %_READLN(VAR F: FIB);` | Compiler intrinsic backing `ReadLn` on text FIB `F` that advances past the next end-of-line (`FEOLN`) or end-of-file (`FEOF`) and clears `FEOLN`. |
| `%_READCHAR` | `FUNCTION %_READCHAR(VAR F: FIB): CHAR;` | Compiler intrinsic that returns the next character from text/interactive FIB `F`, fetching via `%_FGET` if `FState = FNeedChar` and marking the window character consumed. |
| `%_FSEEK` | `PROCEDURE %_FSEEK(VAR F: FIB; RECORDNUM: integer);` | Compiler intrinsic backing `Seek(F, RECORDNUM)` that flushes any dirty buffer and positions typed file `F` to 0-based record `RECORDNUM`. |
| `%_FGOTOXY` | `PROCEDURE %_FGOTOXY(X, Y: INTEGER);` | Compiler intrinsic backing `GotoXY(X, Y)` that moves the cursor to column `X` (`0..87`) and row `Y` (`0..31`) via console escape sequence `ESC '='` or `PasTerm.VGotoxy`. |
| `PAbortFlag` | `function PAbortFlag: boolean;` | Checks whether Apple-Period was pressed on the console or window terminal, clearing `PAbortKeyF` and returning `TRUE` if an abort key was detected. |
| `GetGPrefix` | `PROCEDURE GetGPrefix(Var prefix: pathname);` | Returns the shared Workshop global working directory pathname (`globWorkDir`) in `prefix`. |
| `ScreenCtr` | `procedure ScreenCtr(contrfun: integer);` | Sends screen-control command `contrfun` (clear screen/line or move cursor home/left/right/up/down) to the console or `PasTerm.VScreenCtr`. |
| `GetPrDevice` | `procedure GetPrDevice(var PrDevice: e_name);` | Returns the shared default printer device name (`PrintDevice`) in `PrDevice`. |
| `PTranLisaChar` | `PROCEDURE PTranLisaChar(toTranslate: boolean);` | Sets per-process flag `PTrLisaChar` to `toTranslate` to enable or disable Lisa character set mapping when printing to C. Itoh or daisy-wheel printers. |
| `PaslibVersion` | `FUNCTION PaslibVersion: INTEGER;` | Returns the integer version identifier (`1105`) of the shared `PASLIB` / `BlockIO` runtime unit. |
| `BlockIOInit` | `PROCEDURE BlockIOInit;` | Initializes shared `BlockIO` state once at system boot, locking `PASLIB1`, mounting `-ALTCONSOLE`, opening global `inputfile`/`outputfile`, and cleaning up temporary rewrite files. |
| `BlockIOdisinit` | `procedure BlockIOdisinit;` | Closes the shared console OS reference number when invoked by the initial Shell process that called `BlockIOInit`. |
| `lockPaslib` | `procedure lockPaslib(var errnum: integer);` | Locks the `PASLIB1` runtime code segment in physical memory via `lockseg` for the Filer/Shell, returning any OS error in `errnum`. |
| `lockPasiolib` | `procedure lockPasiolib(var errnum: integer);` | Locks the `PASIOLIB` runtime code segment in physical memory via `lockseg` for the Filer/Shell, returning any OS error in `errnum`. |
| `moveconsole` | `procedure moveconsole(var errnum: integer; applconsole: consoledest);` | Switches the active Pascal console stream (`alscreen`, `mainscreen`, `xsorocA`, `xsorocB`) to `applconsole`, mounting and configuring the target console driver. |
| `ExecReset` | `PROCEDURE ExecReset(VAR errnum: INTEGER; VAR execfile: pathname; stopexec: BOOLEAN);` | Opens Workshop Exec command script `execfile` as the shared console input stream (`stopexec = FALSE`), or closes it and restores `-CONSOLE` input (`stopexec = TRUE`). |
| `ExecFlag` | `FUNCTION ExecFlag: BOOLEAN;` | Returns `TRUE` if shared console input is currently reading commands from an active Workshop Exec script file. |
| `OutputRedirect` | `PROCEDURE OutputRedirect(VAR errnum: INTEGER; VAR outfile: pathname; stopoutput: BOOLEAN);` | Redirects shared console output to text file `outfile` (`stopoutput = FALSE`), or closes the redirect file and restores `-CONSOLE` (`stopoutput = TRUE`). |
| `OutputRFlag` | `FUNCTION OutputRFlag: BOOLEAN;` | Returns `TRUE` if shared console output is currently redirected to a file via `OutputRedirect`. |
| `DSPaslibCall` | `procedure DSPaslibCall(VAR ProcParam: dsProcParam);` | Executes Workshop Shell control request `ProcParam` (`dsResProg`, `dsSoftPwbtn`, `dsPrintDev`, `dsSetGPrefix`, `dsEnbDisk`, or `dsGetDiskEnbF`) on shared `BlockIO` state. |
| `%_PDSPaslibCall` | `procedure %_PDSPaslibCall(VAR ProcParam: pdsProcParam);` | No-op Workshop Shell expansion stub accepting variant request record `ProcParam` (`pdsProcParam`). |
| `%_blockiosetup` | `PROCEDURE %_blockiosetup(firsttime: boolean; var regis: envirRec);` | Per-process initialization hook called by `%_INIT` that binds `8(A5)`/`12(A5)` to local `PInputfile`/`POutputfile` and records restart registers `regis` on `firsttime`, or resets flags and applies `globWorkDir` on subsequent runs. |
| `%_CkResident` | `function %_CkResident(var regis: envirRec): boolean;` | Process termination hook called by `%_TERM`/`%_HALT` that invokes `PasTerm.CleanUp` for windowed apps or suspends a Workshop resident tool (notifying `resident_channel` and restoring `regis` to return `TRUE` on restart). |
| `%_pkeypress` | `function %_pkeypress(var f: fib): boolean;` | Compiler intrinsic helper for `KeyPressed(f)` that returns `TRUE` if unread input is available on FIB `f` (window terminal, active Exec script, keyboard queue, or RS-232 port). |
| `%_funitiocall` | `procedure %_funitiocall(unitno: integer; bufaddr: longint; nbytes: integer; blocknum: integer; mode: integer; unitcode: integer);` | Unsupported UCSD low-level device I/O stub (`UnitRead`, `UnitWrite`, `UnitClear`) on Lisa OS that sets `IORslt` to `inotimpl` (`6010`). |
| `%_funitbusy` | `function %_funitbusy(unitno: integer): boolean;` | Unsupported UCSD `UnitBusy` stub on Lisa OS that sets `IORslt` to `inotimpl` (`6010`) and returns `TRUE`. |

---

## Unit PasHeap

Implements the Lisa Pascal dynamic memory manager backing compiler intrinsics `New`, `Mark`, `Release`, `MemAvail`, and `HeapResult` over a private Lisa OS data segment that grows and shrinks in 512-byte-aligned increments.

- **Import**: `USES PasHeap;`
- **Unit kind**: `INTRINSIC` (`PASHEAP`)
- **Interface dependencies**: `SysCall`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `PLINITHEAP` | `procedure PLINITHEAP(var ernum, refnum: integer; size, delta: longint; ldsn: integer; swapable: boolean);` | Creates the calling process's private Pascal heap data segment at `ldsn` with initial byte size `size` and growth step `delta` (rounded up to 512-byte blocks, disk-backed if `swapable` is `TRUE`), returning OS `ernum` and `refnum`. |
| `%_NEW` | `procedure %_NEW(var ptr: PHTP; size: integer);` | Compiler intrinsic backing `New(ptr)` that allocates `size` bytes (even-aligned, treating `-32768` as `+32768` and auto-initializing or growing the heap segment as needed) and stores the pointer in `ptr`. |
| `%_NEWL` | `procedure %_NEWL(var ptr: PHTP; lsize: longint);` | Compiler intrinsic for 32-bit heap allocation that allocates `lsize` (`longint`) even-aligned bytes on the Pascal heap (auto-growing the heap segment as needed) and stores the pointer in `ptr`. |
| `%_MARK` | `procedure %_MARK(var ptr: PHTP);` | Compiler intrinsic backing `Mark(ptr)` that initializes the Pascal heap if needed and saves the current top-of-heap pointer (`HEAPPTR`) into `ptr`. |
| `%_RELSE` | `procedure %_RELSE(var ptr: PHTP);` | Compiler intrinsic backing `Release(ptr)` that rewinds the Pascal heap pointer to `ptr` and shrinks the underlying OS data segment in `HEAPDELTA` steps when excess blocks are freed. |
| `%_MEMAV` | `function %_MEMAV: LONGINT;` | Compiler intrinsic backing `MemAvail` that returns the number of 16-bit words currently available for allocation in the Pascal heap. |
| `%_HHeapRes` | `function %_HHeapRes: integer;` | Returns the status code (`HerrResult`) from the last Pascal heap operation (`0` on success, `6151..6154` for heap errors, or an OS error code) for `HeapResult`. |
| `%_pphhpreinit` | `procedure %_pphhpreinit;` | Process startup hook that initializes `PasHeap` state to an unallocated null heap and permits a subsequent `PLINITHEAP` call. |
| `%_pphhreinit` | `procedure %_pphhreinit;` | Resident-process restart hook that clears `HerrResult`, re-enables `PLINITHEAP`, and releases any allocated heap blocks back to `HEAPSTART`. |
| `%_phwordsavail` | `function %_phwordsavail: longint;` | Internal helper called by `%_MEMAV` that calculates available 16-bit heap words bounded by unused heap segment bytes, safe OS swap space (`MEM_INFO`), and `LDSN` address limits. |
| `%_disp` | `procedure %_disp(var ptr: PHTP; size: longint);` | No-op compiler intrinsic stub for `Dispose(ptr)` (as `PasHeap` uses stack-oriented `Mark`/`Release` deallocation) that clears `HerrResult` to `0`. |

---

## Unit PasLib

Core Lisa Pascal compiler runtime intrinsic unit whose object code supplies the low-level MC68000 assembly support routines (`%_BEGIN`, `%_INIT`, `%_TERM`, 32-bit integer arithmetic, string and set operations, range checks, and formatted text `Read`/`Write` dispatchers) implicitly linked into compiled Pascal programs; its Pascal interface exports no direct user-callable declarations.

- **Import**: `USES PasLib;`
- **Unit kind**: `INTRINSIC` (`PASLIB`)

*This unit exports constants, data types, and/or global variables only (no callable procedures, functions, or Clascal methods).*

---

## Unit UClascal

Implements the Clascal object-oriented runtime system, building per-class method slice tables and class/author/alias metadata dictionaries during program initialization and providing compiler intrinsics for dynamic `InClass` membership tests and range-checked object typecasts.

- **Import**: `USES UClascal;`
- **Unit kind**: `INTRINSIC` (`UCLASCAL`)
- **Interface dependencies**: `SysCall`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `InitClascal` | `PROCEDURE InitClascal(PROCEDURE FinishedProc(error: INTEGER));` | Installs Clascal completion/error callback `FinishedProc` (called with `0` at the end of `%_Pgm2` or an error code on failure) and clears `pleaseInitClascal`. |
| `QUnitAuthor` | `PROCEDURE QUnitAuthor(VAR companyAndAuthor: TA32);` | Registers 32-character `companyAndAuthor` identifier as the default Toolkit author attribute for classes subsequently initialized in the current unit. |
| `QClassAuthor` | `PROCEDURE QClassAuthor(VAR companyAndAuthor: TA32);` | Sets the 32-character Toolkit `companyAndAuthor` metadata attribute on the class currently being initialized. |
| `QClassAlias` | `PROCEDURE QClassAlias(VAR classAlias: TA8);` | Assigns an 8-character Toolkit `classAlias` name to the class currently being initialized. |
| `QClassVersion` | `PROCEDURE QClassVersion(itsVersion, oldestItCanRead: TByte);` | Sets the object serialization format version (`itsVersion`) and oldest readable version (`oldestItCanRead`) on the class currently being initialized. |
| `CiToCn` | `PROCEDURE CiToCn(index: INTEGER; VAR className: TS8);` | Converts 1-based class index `index` into its 8-character uppercase class name `className`. |
| `CpToCn` | `PROCEDURE CpToCn(stp: TPSliceTable; VAR className: TS8);` | Converts class slice-table pointer `stp` into its 8-character uppercase class name `className`. |
| `CiOfCp` | `FUNCTION CiOfCp(stp: TPSliceTable): INTEGER;` | Returns the 1-based runtime class index stored for class slice-table pointer `stp`. |
| `SizeOfCp` | `FUNCTION SizeOfCp(stp: TPSliceTable): INTEGER;` | Returns the declared instance byte size (`objectSize`) recorded for class slice-table pointer `stp`. |
| `LookupInHashArray` | `FUNCTION LookupInHashArray(tblSize: INTEGER; hashKey: LONGINT; toInsert: BOOLEAN; FUNCTION Compare(index: INTEGER): THashCompare): INTEGER;` | Performs linear-probing lookup in a hash table of size `tblSize` starting from `hashKey` using comparator `Compare`, returning `> 0` (hole when `toInsert`, match otherwise), `< 0` (existing match when `toInsert`, hole otherwise), or `0` if full. |
| `CallPC` | `FUNCTION CallPC: LONGINT;` | Reads the caller's MC68000 stack frame and returns the caller's 32-bit return address (`LONGINT`). |
| `%_Pgm1` | `PROCEDURE %_Pgm1;` | Compiler-emitted Clascal startup prologue invoked before unit initialization that allocates growable stack arrays for classes and method tables, enters non-preemptive mode, installs `JMP %_MethodCall` at `0(A5)`, and jumps back to its caller. |
| `%_Unit` | `PROCEDURE %_Unit;` | Compiler-emitted guard at the start of each `$CLASSES+` unit initialization block that records the caller's PC in `pHashUnit^` and exits the caller immediately if that unit has already been initialized. |
| `%_Class` | `PROCEDURE %_Class(itsClassName, itsSuperName: TS8; itsSTP: TPSliceTable; itsEvenMethods, itsOddMethods, itsObjSize: INTEGER);` | Compiler-emitted class initializer that registers `itsClassName` under `itsSuperName` with size `itsObjSize`, inherits superclass method slices into `itsSTP`, and interprets trailing method `JSR` descriptors to populate method pointers. |
| `%_Pgm2` | `PROCEDURE %_Pgm2;` | Compiler-emitted Clascal startup epilogue invoked after all units initialize that fills abstract slices with `_Abstract`, packs class names and sizes into slice tables, calls `FinishedProc(0)`, and frees temporary init tables. |
| `%_CkObCP` | `FUNCTION %_CkObCP(ordObject, ordSTP: LONGINT): LONGINT;` | Compiler-emitted range-checked typecast intrinsic (`TFoo(obj)` for `TFoo` in the same unit) that returns `ordObject` if `NIL` or a member/subclass of `ordSTP`, and aborts via `FinishedProc(3333)` otherwise. |
| `%_CkObCN` | `FUNCTION %_CkObCN(ordObject: LONGINT; VAR className: TS8): LONGINT;` | Compiler-emitted range-checked typecast intrinsic (`TFoo(obj)` for `TFoo` in another unit) that returns `ordObject` if `NIL` or a member/subclass of `className`, and aborts via `FinishedProc(3333)` otherwise. |
| `%_InObCP` | `FUNCTION %_InObCP(ordObject, ordSTP: LONGINT): BOOLEAN;` | Compiler-emitted `InClass(obj, TFoo)` intrinsic (for `TFoo` in the same unit) that returns `TRUE` if `ordObject` is non-`NIL` and its class or a superclass matches slice-table pointer `ordSTP`. |
| `%_InObCN` | `FUNCTION %_InObCN(ordObject: LONGINT; VAR className: TS8): BOOLEAN;` | Compiler-emitted `InClass(obj, TFoo)` intrinsic (for `TFoo` in another unit) that returns `TRUE` if `ordObject` is non-`NIL` and its class or a superclass matches 8-character `className`. |
