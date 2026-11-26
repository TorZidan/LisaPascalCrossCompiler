# `IOSPASLIB` (`IOSPaslib.obj`) — Lisa OS 1.0 Pascal Runtime Library

[Back to Library Index](LIBRARIES.md)

Core Workshop 1.0 Pascal runtime support (`PasLib`, `BlkIOIntr`, `BlockIO`, `PasHeap`): standard text/typed/untyped file I/O, `BlockRead`/`BlockWrite`, console routing, and Pascal dynamic heap management.

- **Object file**: `libs/workshop1.0/IOSPaslib.obj` (Intrinsic library)
- **Contents**: 4 units, 48 procedures/functions

## Importing and Linking

```pascal
USES BlkIOIntr, BlockIO, PasHeap;
```

```sh
LISA_BOOT=libs/workshop1.0 pascal/lpc.py --2.0 --link=IOSPaslib MYPROG
```

## Units in This Library

| Unit | 8-Char Symbol | `USES` Dependencies | Routines | Summary |
|---|---|---|---|---|
| [`BlkIOIntr`](#unit-blkiointr) | `BLKIOINT` | `SysCall` | 2 | Holds per-process private Pascal I/O runtime state (`IORslt`, standard `INPUT`/`OUTPUT` FIBs, resident restart environment, and console window flags) and internal I/O result accessors for Workshop 1.0/2.0. |
| [`BlockIO`](#unit-blockio) | `BLOCKIO` | `SysCall`, `psyscall`, `BlkIOIntr` | 35 | Implements the shared intrinsic (`INTRINSIC SHARED`) Pascal I/O runtime backing standard `Reset`, `Rewrite`, `Close`, `BlockRead`, `BlockWrite`, `Get`, `Put`, `Read`/`ReadLn`, `Write`/`WriteLn`, `Seek`, and `GotoXY`, along with Workshop Shell console routing, Exec script input, and output redirection. |
| [`PasHeap`](#unit-pasheap) | `PASHEAP` | `SysCall` | 11 | Implements the Lisa Pascal dynamic memory manager backing compiler intrinsics `New`, `Mark`, `Release`, `MemAvail`, and `HeapResult` over a private Lisa OS data segment that grows and shrinks in 512-byte-aligned increments. |
| [`PasLib`](#unit-paslib) | `PASLIB` | — | 0 | Core Lisa Pascal compiler runtime intrinsic unit whose object code supplies the low-level MC68000 assembly support routines (`%_BEGIN`, `%_INIT`, `%_TERM`, 32-bit integer arithmetic, string and set operations, range checks, and formatted text `Read`/`Write` dispatchers) implicitly linked into compiled Pascal programs; its Pascal interface exports no direct user-callable declarations. |

---

## Unit BlkIOIntr

Holds per-process private Pascal I/O runtime state (`IORslt`, standard `INPUT`/`OUTPUT` FIBs, resident restart environment, and console window flags) and internal I/O result accessors for Workshop 1.0/2.0.

- **Import**: `USES BlkIOIntr;`
- **Unit kind**: `INTRINSIC` (`BLKIOINT`)
- **Interface dependencies**: `SysCall`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `FIORESULT` | `FUNCTION FIORESULT: INTEGER;` | Returns the calling process's stored `IORslt` status code from the most recent Pascal I/O operation (implementing `IOResult`). |
| `%_setiorslt` | `procedure %_setiorslt(ior: integer);` | Sets the calling process's Pascal `IORslt` status variable to `ior` (used internally by `FPLib` and text I/O scanners). |

---

## Unit BlockIO

Implements the shared intrinsic (`INTRINSIC SHARED`) Pascal I/O runtime backing standard `Reset`, `Rewrite`, `Close`, `BlockRead`, `BlockWrite`, `Get`, `Put`, `Read`/`ReadLn`, `Write`/`WriteLn`, `Seek`, and `GotoXY`, along with Workshop Shell console routing, Exec script input, and output redirection.

- **Import**: `USES BlockIO;`
- **Unit kind**: `INTRINSIC SHARED` (`BLOCKIO`)
- **Interface dependencies**: `SysCall`, `psyscall`, `BlkIOIntr`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `FINIT` | `PROCEDURE FINIT(VAR F: FIB; WINDOW: WINDOWP; recbytes: INTEGER);` | Compiler intrinsic that initializes File Information Block `F` with window pointer `WINDOW` and record byte size `recbytes` (`0` = interactive, `-2` = text, `-1` = untyped, `> 0` = typed record size). |
| `FOPEN` | `PROCEDURE FOPEN(VAR F: FIB; VAR FTITLE: pathname; FOPENOLD: BOOLEAN; JUNK: longint);` | Compiler intrinsic backing `Reset` (`FOPENOLD = TRUE`) and `Rewrite` (`FOPENOLD = FALSE`) that opens or creates Lisa OS file or pseudo-device `FTITLE` (`-CONSOLE`, `-KEYBOARD`, `-PRINTER`) on FIB `F`. |
| `FCLOSE` | `PROCEDURE FCLOSE(VAR F: FIB; FTYPE: integer);` | Compiler intrinsic backing `Close` that flushes buffers, commits or purges temporary rewrite files, and closes FIB `F` according to `FTYPE` (`CNormal`, `CLock`, `CPurge`, `CCrunch`). |
| `FBLOCKIO` | `FUNCTION FBLOCKIO(VAR F: FIB; A: longint; NBLOCKS, RBLOCK: INTEGER; DOREAD: BOOLEAN): INTEGER;` | Compiler intrinsic backing `BlockRead` (`DOREAD = TRUE`) and `BlockWrite` (`DOREAD = FALSE`) that transfers `NBLOCKS` 512-byte blocks between memory address `A` and FIB `F` at block `RBLOCK` (`-1` for sequential), returning blocks transferred. |
| `FGET` | `PROCEDURE FGET(VAR F: FIB);` | Compiler intrinsic backing `Get(F)` that loads the next record or character into `F.FWindow^`, expanding DLE blank-compression runs and skipping 1 KB page NUL padding on text files. |
| `FPUT` | `PROCEDURE FPUT(VAR F: FIB);` | Compiler intrinsic backing `Put(F)` that copies the current record or character from `F.FWindow^` into `F`'s 512-byte buffer, flushing full blocks and padding 1 KB text pages as needed. |
| `FWRITELN` | `PROCEDURE FWRITELN(VAR F: FIB);` | Writes an end-of-line carriage return (`CHR(13)`) to open text file or console `FIB` `F` via `FWRITECHAR`. |
| `FWRITECHAR` | `PROCEDURE FWRITECHAR(VAR F: FIB; charaddr: longaddr; count: integer);` | Writes `count` characters from `charaddr` to open `FIB` `F`, handling console/window routing, output redirection, `.TEXT` DLE blank compression, and `-PRINTER` Lisa character translation. |
| `FREADLN` | `PROCEDURE FREADLN(VAR F: FIB);` | Advances open text or console `FIB` `F` past the current end-of-line marker and clears `FEOLN` so subsequent input begins on the next line. |
| `FREADCHAR` | `FUNCTION FREADCHAR(VAR F: FIB): CHAR;` | Reads and returns the next character from open `FIB` `F` (advancing its buffer window via `FGET` when `FSTATE = FNEEDCHAR`) and marks the buffer as needing the next character. |
| `FSEEK` | `PROCEDURE FSEEK(VAR F: FIB; RECORDNUM: integer);` | Compiler intrinsic backing `Seek(F, RECORDNUM)` that flushes any dirty buffer and positions typed file `F` to 0-based record `RECORDNUM`. |
| `GOTOXY` | `PROCEDURE GOTOXY(X, Y: INTEGER);` | Positions the console cursor at 0-based column `X` (`0..87`) and row `Y` (`0..31`), delegating to the active terminal window or emitting a Soroc `ESC '='` cursor sequence. |
| `PAbortFlag` | `function PAbortFlag: boolean;` | Checks whether Apple-Period was pressed on the console or window terminal, clearing `PAbortKeyF` and returning `TRUE` if an abort key was detected. |
| `GetGPrefix` | `PROCEDURE GetGPrefix(Var prefix: pathname);` | Returns the shared Workshop global working directory pathname (`globWorkDir`) in `prefix`. |
| `ScreenCtr` | `procedure ScreenCtr(contrfun: integer);` | Sends screen-control command `contrfun` (clear screen/line or move cursor home/left/right/up/down) to the console or `PasTerm.VScreenCtr`. |
| `GetPrDevice` | `procedure GetPrDevice(var PrDevice: e_name);` | Returns the shared default printer device name (`PrintDevice`) in `PrDevice`. |
| `PaslibVersion` | `function PaslibVersion: integer;` | Returns the integer version identifier (`1105`) of the shared `PASLIB` / `BlockIO` runtime unit. |
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
| `blockiosetup` | `PROCEDURE blockiosetup(firsttime: boolean; var regis: envirRec);` | Per-process initialization hook called by `%_INIT` that binds `8(A5)`/`12(A5)` to local `PInputfile`/`POutputfile` and records restart registers `regis` on `firsttime`, or resets flags and applies `globWorkDir` on subsequent runs. |
| `getFileaddr` | `procedure getFileaddr(var infaddr: longint; var outfaddr: longint);` | Returns the runtime memory addresses of the standard `INPUT` and `OUTPUT` `FIB` variables in `infaddr` and `outfaddr` during `%_INIT` program startup. |
| `PasCleanup` | `procedure PasCleanup;` | Flushes and closes open Pascal runtime I/O files and cleans up terminal-window state during process termination. |
| `CkResident` | `function CkResident(var regis: envirRec): boolean;` | Process termination hook called by `%_TERM`/`%_HALT` that invokes `PasTerm.CleanUp` for windowed apps or suspends a Workshop resident tool (notifying `resident_channel` and restoring `regis` to return `TRUE` on restart). |
| `Pflushread` | `function Pflushread(var f: fib): boolean;` | Checks pending keyboard/console input availability or flushes unread input state on open `FIB` `f`. |
| `InitTFproc` | `procedure InitTFproc(procadr: longint);` | Registers the `TFolder` terminal-emulator dispatch entry point (`procadr`) used by `BlockIO` to route standard console I/O into a folder window. |
| `funitiocall` | `procedure funitiocall(unitno: integer; bufaddr: longint; nbytes: integer; blocknum: integer; mode: integer; unitcode: integer);` | Unsupported UCSD low-level device I/O stub (`UnitRead`, `UnitWrite`, `UnitClear`) on Lisa OS that sets `IORslt` to `inotimpl` (`6010`). |
| `funitbusy` | `function funitbusy(unitno: integer): boolean;` | Unsupported UCSD `UnitBusy` stub on Lisa OS that sets `IORslt` to `inotimpl` (`6010`) and returns `TRUE`. |

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

*This unit exports constants, data types, and/or global variables only (no callable procedures or functions).*
