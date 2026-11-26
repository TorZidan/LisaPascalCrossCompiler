# `SYS1LIB` (`SYS1LIB.obj`) — Lisa System 1 Consolidated GUI, QuickDraw, Printing & Desktop Library

[Back to Library Index](LIBRARIES.md)

Consolidated Lisa Office System 2.0 GUI, desktop, and printing framework (43 units): `QuickDraw`, `Windows`, `Events`, `Menus`, `Folders`, `AlertMgr`, `FontMgr`, `FieldEdit`, `Scrap`, `UnitHz`/`Storage`, `WmlSb`, `International`, `PMM`, `HWInt`, `FilerComm`, and Dot-Matrix (`Ci*`), Canon (`Cp*`), and Daisy-Wheel (`Rh*`) printing.

- **Object file**: `libs/workshop2.0/SYS1LIB.obj` (Intrinsic library (packed, no embedded `INTERFACE`))
- **Contents**: 43 units, 858 procedures/functions

> [!NOTE]
> `libs/workshop2.0/SYS1LIB.obj` contains packed MC68000 code segments and `UnitBlock` headers for linking, without an `InterfLoc` block or embedded `INTERFACE` text (so `USES` cannot load its interfaces from `SYS1LIB.obj` via `INTRINSIC.LIB`). On a Workshop 2.0 system, programs supply separate unit `.obj` interface files via `{$U ...}` (for example, `USES {$U QD/QuickDraw} QuickDraw;`) when compiling, and link against `SYS1LIB.obj`. The routines and signatures below are cross-checked against the unpacked `SYS1LIB.obj` binary.

## Importing and Linking

```pascal
USES {$U AlertMgr.obj} AlertMgr;
```

```sh
LISA_BOOT=libs/workshop2.0 pascal/lpc.py --2.0 --link=IOSPASLIB,SYS1LIB MYPROG
```

## Units in This Library

| Unit | 8-Char Symbol | `USES` Dependencies | Routines | Summary |
|---|---|---|---|---|
| [`AlertMgr`](#unit-alertmgr) | `ALERTMGR` | `HWInt`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `FmgrUtil`, `SysCall`, `PSysCall`, `PMDecl`, `PMM`, `Events`, `Folders`, `Menus`, `Windows`, `WmlStd`, `WmlCrs`, `DBEnv` | 29 | Implements the Lisa Alert Manager for loading localized `.PHRASE` files, formatting parameterized alert messages and live counters, managing an LRU alert text cache, and displaying modal or background Ask, Caution, Note, Stop, and Wait alert boxes with rounded-rectangle buttons. |
| [`CiDev`](#unit-cidev) | `CIDEV` | `SysCall`, `PMDecl`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `Events`, `Menus`, `Windows`, `Folders`, `WmlStd`, `WmlCrs`, `AlertMgr`, `PrStdInfo`, `PrStdProcs`, `Queues`, `PrEvents`, `PrDlgMgr`, `PrMgr`, `CiGlobals` | 25 | Low-level device driver interface for the Apple Dot Matrix Printer (C. Itoh), providing buffered escape-command output, deferred 1/144-inch vertical paper positioning, print-pitch and style control, European character set mapping, and 8-pin horizontal/vertical raster band printing. |
| [`CiProcs`](#unit-ciprocs) | `CIPROCS` | `SysCall`, `PMDecl`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `PrStd`, `PrBuf`, `CiDev` | 8 | High-level Print Shop driver unit for the Apple Dot Matrix Printer (C. Itoh), managing printer port lifecycle, page and band metric calculation, draft `StdText` command buffering, raster band dumping, and page ejection. |
| [`CpDev`](#unit-cpdev) | `CPDEV` | `SysCall`, `PMDecl`, `UnitStd`, `QuickDraw`, `PrStd` | 27 | Low-level device driver interface for the parallel Canon Inkjet printer, providing buffered command output, deferred 1/144-inch vertical paper positioning, character pitch and style selection, horizontal/vertical bitmap band printing, and raw or run-length-encoded raster graphics transmission. |
| [`CpProcs`](#unit-cpprocs) | `CPPROCS` | `SysCall`, `PMDecl`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `PrStd`, `PrBuf`, `CpDev` | 7 | High-level Print Shop driver unit for the parallel Canon Inkjet printer, managing device session open/close and abort cleanup, page and band metric calculation, band rasterization/dumping, and page ejection. |
| [`DBEnv`](#unit-dbenv) | `DBENV` | — | 0 | Defines foundational low-level byte and integer array, pointer, and handle types (`byte`, `data`, `ptrdata`, `hnddata`, `intdata`, `ptrintdata`, and `hndintdata`) shared across Lisa database, Field Editor, and Office System units. |
| [`Events`](#unit-events) | `EVENTS` | `SysCall`, `PSysCall`, `HWInt`, `UnitStd`, `UnitHz`, `Storage`, `PMDecl`, `PMM`, `QuickDraw`, `FontMgr` | 26 | Implements the Lisa Window Manager Event Manager (`Events` shared intrinsic), providing per-process event queueing, low-level keyboard/mouse interrupt classification, active-process polling, screen printing, and event journal recording and playback. |
| [`FEDec`](#unit-fedec) | `FEDEC` | `UnitStd`, `UnitHz`, `QuickDraw`, `FontMgr`, `Storage`, `DBEnv` | 0 | Declares shared constants and data structures for the Lisa Field Editor (`FieldEdit` and `FldUt`), including error codes (`fldFull`..`FENotUndoable`), alignment and style-change constants, edit operation tags (`noOp`..`formulaToValueOp`), selection/highlighting types (`interval`, `txSel`, `TtySel`, `TtyHilight`), and core editing records (`field`, `fieldState`, `run`, `undoInfo`, `ScrapRec`). |
| [`FieldEdit`](#unit-fieldedit) | `FIELDEDI` | `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `SysCall`, `Events`, `Folders`, `WmlStd`, `WmlSb`, `DBEnv`, `FEDec`, `Scrap`, `UnitFmt`, `PMDecl`, `PrStdInfo`, `UnitCs`, `FldUt` | 52 | Implements the single-line Lisa Field Editor for Office System applications and dialogs, supporting multi-run styled text, mouse point/word/drag selection, caret blinking, gap-buffer character and word editing, scrap/stream cut-copy-paste, and single-level undo. |
| [`FilerComm`](#unit-filercomm) | `FILERCOM` | `SysCall`, `PSysCall`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `GrafUtil`, `WmlStd`, `WmlSb`, `FontMgr`, `Events`, `Windows`, `Folders`, `Scrap` | 7 | Provides the interprocess communication protocol between Lisa Office System applications and the Desktop Manager (Filer), handling document open/close/copy/print/terminate events, catalog pathname-to-prefix translation, document diskfile copying, and scrap icon references. |
| [`FldUt`](#unit-fldut) | `FLDUT` | `UnitStd`, `UnitHz`, `QuickDraw`, `FontMgr`, `Storage`, `SysCall`, `Events`, `DBEnv`, `FEDec`, `PMDecl`, `PrStdInfo`, `UnitFmt`, `UnitCs`, `Scrap` | 2 | Bridges the Lisa Field Editor with the Universal Text (`UnitCs`) character stream architecture so field scrap data can be read sequentially as formatted text runs by other Office System tools. |
| [`FmgrUtil`](#unit-fmgrutil) | `FMGRUTIL` | `UnitStd`, `UnitHz`, `SysCall`, `QuickDraw`, `FontMgr`, `Storage` | 4 | Provides Font Manager utility routines for extracting and drawing icons, 8x8 QuickDraw patterns, and 16x16 cursors stored as character glyphs in special system icon, pattern, and cursor font families. |
| [`Folders`](#unit-folders) | `FOLDERS` | `HWInt`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `SysCall`, `Events`, `PMDecl`, `PMM`, `Windows` | 40 | Implements high-level Lisa Window Manager folder operations, managing desktop document folders and system windows (`dialogFolder`, `alertFolder`, `menuFolder`, `scrapFolder`), window activation/deactivation handoffs, update/invalidation regions, process cleanup, and refresh pictures. |
| [`FontMgr`](#unit-fontmgr) | `FONTMGR` | `UnitStd`, `UnitHz`, `SysCall`, `PSysCall` | 11 | Implements the shared Lisa Font Manager (`FontMgr`), managing the `FMDATA` font cache segment, `SYSTEM.FONTLIB` strike loading, device-specific font substitution heuristics, font locking, and character width and metric queries for screen and printer devices. |
| [`GrafUtil`](#unit-grafutil) | `GRAFUTIL` | `QuickDraw` | 14 | Provides QuickDraw utility routines for 32-bit bitwise logic and shifting, big-endian bit-array testing and manipulation, 32x32-to-64-bit signed multiplication, and 16.16 `Fixed`-point arithmetic. |
| [`HWInt`](#unit-hwint) | `HWINT` | — | 73 | Provides the low-level Lisa Hardware Interface to 6522 VIAs, COPS keyboard/mouse controller, level 1/2 disk and vertical-retrace interrupts, hardware cursor and busy cursor, primary/alternate screen buffers, display contrast and power control, speaker tone generation, keyboard maps/queues, timers/alarms, and the hardware clock/calendar. |
| [`International`](#unit-international) | `INTERNAT` | `UnitStd` | 11 | Provides locale-aware international character and string processing for European and US markets, including accented uppercase/lowercase shifting, multi-strength character/string identity matching, and two-pass lexicographic magnitude comparison with ligature expansion. |
| [`Menus`](#unit-menus) | `MENUS` | `HWInt`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `SysCall`, `Events`, `Windows`, `Folders` | 20 | Implements the Lisa Menu Manager (`Menus` shared intrinsic) for building, reading, inserting, enabling/disabling, marking, rendering, and tracking pull-down menus and Command-key shortcuts in the desktop menu bar. |
| [`PMDecl`](#unit-pmdecl) | `PMDECL` | `SysCall` | 0 | Declares constants and record types for the Parameter Memory Manager (`PMM`) and configurable device descriptors (`SYSTEM.CDD`), including `TNibble`, `TBootStuff`, `TOutPutStuff`, `TInputStuff`, `TInternalStuff`, `TypeConnect`, `Ch_info`, `cddEntry`, `cddHeader`, and `systemCdd`. |
| [`PMM`](#unit-pmm) | `PMM` | `HWInt`, `SysCall`, `UnitStd`, `PMDecl` | 15 | Implements the shared Parameter Memory Manager (`PMM`) for reading, updating, defaulting, and persisting non-volatile Lisa configuration settings (boot volume, screen contrast, fade delay, beep volume, key repeat/double-click rates, mouse scaling, and attached device records) and applying them to hardware drivers. |
| [`PrBuf`](#unit-prbuf) | `PRBUF` | `SysCall`, `PMDecl`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `PrStdInfo` | 6 | Buffers and sorts text runs and horizontal or vertical rule commands within a QuickDraw print band for character and daisy-wheel printer drivers. Coalesces adjacent text and overlapping rules before invoking driver-supplied check, scan-line, and dump callbacks. |
| [`PrFile`](#unit-prfile) | `PRFILE` | `SysCall`, `PMDecl`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `PrStd` | 11 | Implements Print Shop spool-file recording for background printing, serializing `TPfHeader` job headers, `TPfPage` page directory tables, per-band QuickDraw pictures, and `PicComment`-encoded tabs and rules to disk. |
| [`PrMgr`](#unit-prmgr) | `PRMGR` | `UnitStd`, `SysCall`, `PMDecl`, `QuickDraw`, `Events`, `Windows`, `Folders`, `Menus`, `AlertMgr`, `PrStd`, `PrMgrUtil` | 10 | Implements core Print Manager initialization, shared data-segment binding, printer setup and job dialogs, alert presentation, and print record validation. Coordinates foreground applications with background printer processes via shared memory and event channels. |
| [`PrMgrUtil`](#unit-prmgrutil) | `PRMGRUTI` | `UnitStd`, `SysCall`, `PMDecl`, `PMM`, `QuickDraw`, `FontMgr`, `Menus`, `PrStd` | 13 | Provides Print Manager utility routines in `Sys2Lib` for querying available printers, reading and converting Parameter Memory printer configuration records, comparing and modifying `TPrRec` preferences, building long font IDs, and dispatching Print Manager folder menu commands. |
| [`PrProcs`](#unit-prprocs) | `PRPROCS` | `SysCall`, `PMDecl`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `PrStd`, `PrBuf`, `PrFile` | 28 | Core application-facing Print Shop printing unit in Workshop 1.0/2.0, providing the `PrDocStart`/`PrStartPage`/`PrNextBand`/`PrDumpBand`/`PrEndPage`/`PrDocEnd` banded printing loop, printing `GrafPort` setup, printer-adapted QuickDraw `PrStd*` bottlenecks, and `Tab`/`HRule`/`VRule` drawing primitives. |
| [`PrStd`](#unit-prstd) | `PRSTD` | `UnitStd`, `SysCall`, `PMDecl`, `QuickDraw` | 13 | Foundational Print Shop unit in Workshop 1.0/2.0 defining shared print records, factory-default style and Parameter Memory initializers, print-preference validation and version repair, blank-bitmap testing, low-level `Ps*` port I/O, and background-daemon synchronization. |
| [`QuickDraw`](#unit-quickdraw) | `QUICKDRA` | — | 145 | Implements Bill Atkinson's Lisa QuickDraw graphics library, providing `GrafPort` management, clipping, cursors, pen and line drawing, styled text rendering and measurement, `Point`/`Rect`/`Polygon`/`Region` geometry and graphical verbs, `BitMap` blitting/scrolling, `Picture` recording/playback, bottleneck procedures, and color/planar bit selection. |
| [`RhDev`](#unit-rhdev) | `RHDEV` | `SysCall`, `PMDecl`, `UnitStd`, `QuickDraw`, `PrStd` | 13 | Low-level device driver interface for the Apple/Qume Daisy Wheel printer, managing buffered escape-command transmission, incremental 1/120-inch horizontal and 1/48-inch vertical carriage positioning, program-control spoke/ribbon/impression firing, and form-feed handling. |
| [`RhProcs`](#unit-rhprocs) | `RHPROCS` | `SysCall`, `PMDecl`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `PrStd`, `PrBuf`, `RhDev` | 11 | High-level Print Shop driver unit for the Apple/Qume Daisy Wheel printer, implementing port/device lifecycle control, page and band metric computation, spoke-mapped `StdText` capture, tab and horizontal/vertical rule buffering, and band output. |
| [`Scrap`](#unit-scrap) | `SCRAP` | `UnitStd`, `UnitHz`, `SysCall`, `UnitFile`, `QuickDraw`, `FontMgr`, `Storage`, `Events`, `Folders`, `WmlStd`, `WmlSb`, `UnitFmt`, `PMDecl`, `PrStdInfo`, `UnitCs`, `UnitFigAtom`, `UnitFf` | 26 | Manages the shared inter-application Clipboard (Scrap), supporting application-specific scrap handles, QuickDraw universal pictures (ScrapUG), and formatted Universal Text control streams (ScrapCs). Provides process ownership transfer, two-segment undoable Cut/Copy transactions, and on-demand data-segment binding. |
| [`Storage`](#unit-storage) | `STORAGE` | `UnitStd`, `UnitHz` | 11 | Provides QuickDraw-compatible dynamic memory allocation routines (Ptr and Handle management) layered over a UnitHz heap zone (theHeap). |
| [`Sys1Lock`](#unit-sys1lock) | `SYS1LOCK` | `UnitStd`, `SysCall` | 9 | Provides per-segment wrapper procedures used by the Desktop Manager (Filer) to lock individual SYS1LIB intrinsic code segments into physical memory via LockSeg. |
| [`UnitCs`](#unit-unitcs) | `UNITCS` | `UnitStd`, `UnitHz`, `SysCall`, `Storage`, `QuickDraw`, `FontMgr`, `PMDecl`, `PrStdInfo`, `UnitFmt` | 22 | Implements the polymorphic Control Stream (TCs) framework used by LisaWrite, Field Editor, Scrap, and Universal Text to sequence runs and track logical position intervals (TLp, TInt) across formatted text, ruler, page, and figure streams. |
| [`UnitFf`](#unit-unitff) | `UNITFF` | `UnitStd`, `UnitHz`, `SysCall`, `UnitFile`, `QuickDraw`, `FontMgr`, `Storage`, `UnitFmt`, `PMDecl`, `PrStdInfo`, `UnitCs` | 11 | Implements formatted-file control streams (tycsFf, .LOTUS format) that read and write 512-byte pages containing text runs, character and paragraph formatting bytecodes, headers/footers, and embedded figure references. |
| [`UnitFile`](#unit-unitfile) | `UNITFILE` | `UnitStd`, `UnitHz`, `SysCall`, `PSysCall` | 16 | Provides fixed-block and virtual-object (TVofil) file I/O integrated with UnitHz named-object demand paging (FilCbOfN, FilFSwapInN, FilSwapOutN). |
| [`UnitFmt`](#unit-unitfmt) | `UNITFMT` | `UnitStd`, `UnitHz`, `QuickDraw`, `FontMgr` | 11 | Encodes, decodes, and applies compact formatting bytecodes (fop / rgfbc) that modify character style attributes (TArce), paragraph margins and spacing (TArpe), and tab-stop descriptors (TTbd). |
| [`UnitHz`](#unit-unithz) | `UNITHZ` | `UnitStd`, `SysCall` | 25 | Implements the Lisa heap zone manager (THz), supporting relocatable handle blocks (tybkStd), non-relocatable pointer blocks (tybkNrel), demand-swapped named objects (tybkN), heap compaction, and data-segment growth. |
| [`UnitStd`](#unit-unitstd) | `UNITSTD` | — | 21 | Defines core scalar, pointer, character-slice (TAchad), and doubly-linked offset-list (TLld) types along with low-level memory move, binary search, division, bitfield, and ASCII case-conversion utilities. |
| [`Windows`](#unit-windows) | `WINDOWS` | `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `SysCall`, `Events` | 29 | Implements the internal Lisa Window Manager display list, visible/clipping/update region calculations, z-order management, window movement and resizing, process/focus activation, and dynamic window-title strings underlying Folders. |
| [`WmlCrs`](#unit-wmlcrs) | `WMLCRS` | `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `FmgrUtil`, `WmlStd` | 3 | Manages the standard Window Manager Library (WML) system cursors—such as arrow, I-beam, scroll arrows, split skewers, crosshairs, hourglass, and hidden cursor—loaded from syscursor. |
| [`WmlGrow`](#unit-wmlgrow) | `WMLGROW` | `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `WmlStd`, `SysCall`, `Events`, `Folders` | 7 | Implements window grow-box geometry, rendering, hit-testing, and interactive XOR-frame rubber-band resizing for Lisa windows. |
| [`WmlSb`](#unit-wmlsb) | `WMLSB` | `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `WmlStd`, `SysCall`, `Events` | 42 | Implements Window Manager Library (WML) scroll bars and split-pane scroll boxes (TSb), supporting arrow, page-flip, thumb, and split-skewer layout, hit-testing, rendering, pane splitting, and interactive dragging. |
| [`WmlStd`](#unit-wmlstd) | `WMLSTD` | `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr` | 4 | Defines shared QuickDraw type aliases and graphics-state save/restore helpers (PenSave, PenRestore, WmlTxtSave, WmlTxtRestore) used across the Window Manager Library. |

---

## Unit AlertMgr

Implements the Lisa Alert Manager for loading localized `.PHRASE` files, formatting parameterized alert messages and live counters, managing an LRU alert text cache, and displaying modal or background Ask, Caution, Note, Stop, and Wait alert boxes with rounded-rectangle buttons.

- **Import**: `USES {$U AlertMgr.obj} AlertMgr;`
- **Unit kind**: `INTRINSIC` (`ALERTMGR`)
- **Interface dependencies**: `HWInt`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `FmgrUtil`, `SysCall`, `PSysCall`, `PMDecl`, `PMM`, `Events`, `Folders`, `Menus`, `Windows`, `WmlStd`, `WmlCrs`, `DBEnv`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `AskAlert` | `function AskAlert(alertFile: TAlertFile; alertNumber: integer): integer;` | Displays a multi-button Ask alert box defined by the phrase file, tracks user dismissal, and returns the 1-based index of the button selected. |
| `ArgAlert` | `procedure ArgAlert(n: TArgAlert; s: Str255);` | Stores string `s` into alert text citation slot `n` (`0..5`, substituted for `^0`..`^5` in alert messages). |
| `BeepAlert` | `procedure BeepAlert(volume: integer);` | Signals the user at alert intensity `volume` (`0..3`) by sounding an 880 Hz speaker tone or flashing the menu bar according to Parameter Memory settings. |
| `ButnPushed` | `function ButnPushed(first, last: TButn; VAR pushed: TButn; pt: Point): boolean;` | Tracks mouse movement while the button remains depressed across shown alert buttons `first..last`, inverting any hit button and returning `TRUE` with its index in `pushed` if released inside one. |
| `CautionAlert` | `function CautionAlert(alertFile: TAlertFile; alertNumber: integer): boolean;` | Displays a two-button (OK/Cancel) Caution alert box from the phrase file and returns `TRUE` if the user chooses OK or `FALSE` if canceled. |
| `CalcButWidth` | `function CalcButWidth(topButn, botButn: TButn; VAR height: integer): integer;` | Computes and returns the uniform pixel width needed to fit the labels of alert buttons `topButn` through `botButn` (including rounded-corner margins) and sets `height` to the standard button height. |
| `CountAlert` | `procedure CountAlert(whichCounter: TCountAlert; countValue: integer);` | Updates numeric alert counter `whichCounter` (`7..9`, referenced as `^7`..`^9` in wait alerts) to `countValue` and redraws the right-justified value in its on-screen counter box. |
| `DrawAlert` | `procedure DrawAlert(alertFile: TAlertFile; alertNumber: integer; marginRect: Rect);` | Formats and draws the text of a `drawProc` alert message from `alertFile` directly inside `marginRect` in the current QuickDraw port without opening the alert folder. |
| `DTAlert` | `procedure DTAlert(alertFile: TAlertFile; osDT: longint; VAR userString: TParamAlert);` | Formats the elapsed time between OS timestamp `osDT` and current GMT as a localized relative time string in `userString` using phrase-file entries 901 through 909. |
| `GetAlert` | `procedure GetAlert(alertFile: TAlertFile; alertNumber: integer; pStr: TPstr255);` | Retrieves the raw phrase string of `alertNumber` from `alertFile` into `pStr^` without displaying an alert box. |
| `GetButn` | `procedure GetButn(d: TButn; pStr: TPstr255);` | Copies the title string of alert button `d` into `pStr^`. |
| `HideButn` | `procedure HideButn(d: TButn);` | Erases alert button `d`'s hit box in the current port and clears its shown, pushed, and default state flags. |
| `InitAlerts` | `procedure InitAlerts(cacheSize, cacheBytes: integer; hz: THz; idleProcPtr, errProcPtr: procPtr);` | Initializes the Alert Manager on heap zone `hz`, allocating an LRU alert cache (`cacheSize` slots, `cacheBytes` capacity) and registering optional idle and error callback procedures. |
| `LdSgAl` | `procedure LdSgAl;` | Forces the main Alert Manager code segment (`alert`) to be swapped into memory via a no-op call. |
| `LocateAlert` | `procedure LocateAlert(top: integer);` | Sets the preferred top vertical screen coordinate (`top`) for the next alert box to be displayed. |
| `LockAlert` | `procedure LockAlert(alertFile: TAlertFile; alertNumber: integer);` | Loads the message text for `alertNumber` from `alertFile` into the alert cache and locks its cache slot against eviction. |
| `NoteAlert` | `procedure NoteAlert(alertFile: TAlertFile; alertNumber: integer);` | Displays a single-button (OK) informational Note alert box from `alertFile` and waits for the user to dismiss it. |
| `NthAlert` | `function NthAlert(ordinal: INTEGER; alertFile: TAlertFile; VAR alertNumber, numStages: integer; VAR alertKind: TAlertKind): BOOLEAN;` | Inspects the alert entry at 1-based index `ordinal` in `alertFile`, returning `TRUE` along with its `alertNumber`, escalation stage count (`numStages`), and `alertKind` if valid. |
| `OpenPhraseFile` | `procedure OpenPhraseFile(VAR refNum: integer; path: pathName);` | Appends `'PHRASE'` to `path`, opens the phrase file for reading, verifies its checksum if marked scavenged, and returns the OS file reference number in `refNum`. |
| `ParamAlert` | `procedure ParamAlert(cite1, cite2, cite3: Str255);` | Sets alert citation parameters 1, 2, and 3 (`^1`, `^2`, and `^3`) to `cite1`, `cite2`, and `cite3` respectively. |
| `PushButn` | `procedure PushButn(d: TButn; f: boolean);` | Updates the visual pushed state of shown alert button `d` to `f` by inverting its rounded-rectangle hit box when its state changes. |
| `ReadAlerts` | `function ReadAlerts(refNum, version: integer): TAlertFile;` | Reads the version header, alert sign icons, standard button titles, and alert directory from open phrase file `refNum`, returning a newly allocated `TAlertFile` handle. |
| `ReshowButn` | `procedure ReshowButn(d: TButn);` | Redraws alert button `d` at its existing hit-box position and default-border state if it is currently marked as shown. |
| `SetButWidths` | `procedure SetButWidths(width: integer);` | Sets the pixel width used when drawing subsequent alert buttons to `width`. |
| `ShowButn` | `procedure ShowButn(d: TButn; h, v: integer; fDefault: boolean);` | Draws rounded-rectangle alert button `d` at `(h, v)` in the current port with a centered label and a heavy border when `fDefault` is `TRUE`. |
| `StopAlert` | `procedure StopAlert(alertFile: TAlertFile; alertNumber: integer);` | Displays a single-button (OK) Stop alert box from `alertFile` to report an error or critical condition and waits for user dismissal. |
| `UnlockAlerts` | `procedure UnlockAlerts;` | Clears the lock flag on every slot in the Alert Manager cache so locked alert texts become eligible for LRU eviction. |
| `WaitAlert` | `procedure WaitAlert(alertFile: TAlertFile; alertNumber: integer);` | Displays a buttonless Wait alert box with an immediate busy cursor while an operation is in progress, keeping it on screen until `EndWaitAlert` is called. |
| `WouldAlert` | `procedure WouldAlert(VAR menu: menuInfo; itemIndex: integer);` | Records the text of item `itemIndex` in `menu` as the command citation string (`^C` / `^K`) and increments the consecutive menu-command counter for staged alerts. |

---

## Unit CiDev

Low-level device driver interface for the Apple Dot Matrix Printer (C. Itoh), providing buffered escape-command output, deferred 1/144-inch vertical paper positioning, print-pitch and style control, European character set mapping, and 8-pin horizontal/vertical raster band printing.

- **Import**: `USES {$U CiDev.obj} CiDev;`
- **Interface dependencies**: `SysCall`, `PMDecl`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `Events`, `Menus`, `Windows`, `Folders`, `WmlStd`, `WmlCrs`, `AlertMgr`, `PrStdInfo`, `PrStdProcs`, `Queues`, `PrEvents`, `PrDlgMgr`, `PrMgr`, `CiGlobals`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `CiDevClose` | `PROCEDURE CiDevClose;` | Flushes deferred vertical motion, resets the C. Itoh dot-matrix printer to forward 6-LPI US character mode, and flushes the output buffer. |
| `CiDevOpen` | `PROCEDURE CiDevOpen(fFastGraf, fPEStop: Boolean);` | Initializes `CiDev` state and resets the C. Itoh dot-matrix printer, configuring fast-graphics mode (`fFastGraf`) and paper-empty stop behavior (`fPEStop`). |
| `CiSetBiDir` | `PROCEDURE CiSetBiDir(fBiDir: Boolean);` | Enables (`fBiDir = TRUE`) or disables (`fBiDir = FALSE`) bidirectional print-head motion on the C. Itoh dot-matrix printer. |
| `CiSetBpi` | `PROCEDURE CiSetBpi(tybpi: TTybpi);` | Emits the C. Itoh escape sequence selecting horizontal dot/character pitch `tybpi` (`72` through `160` bits per inch). |
| `CiSetEmph` | `PROCEDURE CiSetEmph(fEmph: Boolean);` | Enables (`fEmph = TRUE`) or disables (`fEmph = FALSE`) emphasized boldface printing on the C. Itoh dot-matrix printer. |
| `CiSetLFFwd` | `PROCEDURE CiSetLFFwd(fFwd: Boolean);` | Sets the C. Itoh paper line-feed direction to forward (`fFwd = TRUE`) or reverse (`fFwd = FALSE`). |
| `CiSetLineHt` | `PROCEDURE CiSetLineHt(c144ths: Integer);` | Sets the C. Itoh line-feed step distance to `c144ths` (in 1/144-inch increments, up to 99). |
| `CiSetPEStop` | `PROCEDURE CiSetPEStop(fPEStop: Boolean);` | Configures the C. Itoh printer to halt (`fPEStop = TRUE`) or ignore paper-out sensor signals (`fPEStop = FALSE`) when paper runs out. |
| `CiSetUL` | `PROCEDURE CiSetUL(fUL: Boolean);` | Enables (`fUL = TRUE`) or disables (`fUL = FALSE`) hardware-underlined character printing on the C. Itoh dot-matrix printer. |
| `CiSetWide` | `PROCEDURE CiSetWide(fWide: Boolean);` | Enables (`fWide = TRUE`) or disables (`fWide = FALSE`) elongated double-width character printing on the C. Itoh dot-matrix printer. |
| `CiBindV` | `PROCEDURE CiBindV;` | Executes any deferred vertical paper movement (`CiGotoV`/`CiDeltaV`) by emitting the required forward or reverse line-feed commands to the C. Itoh printer. |
| `CiDeltaV` | `PROCEDURE CiDeltaV(c144ths: Integer);` | Adjusts the deferred vertical paper target position on the C. Itoh printer by relative offset `c144ths` (in 1/144-inch units). |
| `CiGotoV` | `PROCEDURE CiGotoV(c144ths: Integer);` | Sets the deferred absolute vertical paper position on the current page to `c144ths` (in 1/144-inch units). |
| `CiNewPage` | `PROCEDURE CiNewPage;` | Advances paper to the top of the next form, flushes buffered output, and resets the C. Itoh vertical page position. |
| `CiSetFormLng` | `PROCEDURE CiSetFormLng(cPg144ths: Integer);` | Sets the logical page form height tracked by `CiDev` to `cPg144ths` (in 1/144-inch units). |
| `CiPrBand` | `PROCEDURE CiPrBand(p: TP; cBits, c144ths: Integer; tybpi: TTybpi; fBitDbl, fBiDir: Boolean);` | Prints an 8-scanline pin band of `cBits` columns from `p` at density `tybpi` (with optional bit-doubling `fBitDbl` and bidirectional mode `fBiDir`) and advances vertically by `c144ths`. |
| `CiPrBMHoriz` | `PROCEDURE CiPrBMHoriz(pBM: QDPtr; cBits, cScans, cRowBytes: Integer; tybpi: TTybpi; tyspi: TTyspi; fBitDbl, fBiDir: Boolean);` | Slices and prints QuickDraw bitmap `pBM` (`cBits` by `cScans`, `cRowBytes` per row) in horizontal landscape orientation on the C. Itoh printer at resolutions `tybpi` and `tyspi`. |
| `CiPrBMVert` | `PROCEDURE CiPrBMVert(pBM: QDPtr; cBits, cScans, cRowBytes: Integer; tybpi: TTybpi; tyspi: TTyspi; fBitDbl, fBiDir: Boolean);` | Slices and prints QuickDraw bitmap `pBM` (`cBits` by `cScans`, `cRowBytes` per row) in vertical portrait 8-scanline bands on the C. Itoh printer at resolutions `tybpi` and `tyspi`. |
| `CiPrGraf` | `PROCEDURE CiPrGraf(p: TP; cBits: Integer; fFastGraf: Boolean);` | Emits a C. Itoh bit-image graphics command (`ESC S` or fast-graphics mode when `fFastGraf` is `TRUE`) followed by `cBits` 8-pin vertical byte columns from `p`. |
| `CiPrTab` | `PROCEDURE CiPrTab(cPos: Integer);` | Flushes deferred vertical motion and emits a C. Itoh dot-column horizontal tab command (`ESC F`) to position `cPos`. |
| `CiPrText` | `PROCEDURE CiPrText(p: TP; cCount: Integer);` | Flushes deferred vertical motion and outputs `cCount` text bytes from `p` to the C. Itoh printer, switching hardware national character sets as needed for accented Lisa characters. |
| `CiDmpBuf` | `PROCEDURE CiDmpBuf;` | Writes all bytes currently queued in `CiDev`'s internal output buffer to the printer port and resets the buffer index. |
| `CiHRes` | `FUNCTION CiHRes(tybpi: TTybpi): Integer;` | Returns the horizontal resolution in dots per inch (`72`, `80`, `96`, `120`, `136`, or `160`) corresponding to density selector `tybpi`. |
| `CiMaxBits` | `FUNCTION CiMaxBits(tybpi: TTybpi; fBitDbl: Boolean): Integer;` | Returns the maximum number of horizontal dots across an 8-inch scanline at density `tybpi`, halved when horizontal bit-doubling (`fBitDbl`) is enabled. |
| `CiOut` | `PROCEDURE CiOut(b: TB);` | Appends byte `b` to `CiDev`'s output buffer, automatically flushing via `CiDmpBuf` when the buffer fills. |

---

## Unit CiProcs

High-level Print Shop driver unit for the Apple Dot Matrix Printer (C. Itoh), managing printer port lifecycle, page and band metric calculation, draft `StdText` command buffering, raster band dumping, and page ejection.

- **Import**: `USES {$U CiProcs.obj} CiProcs;`
- **Unit kind**: `INTRINSIC` (`CIPROCS`)
- **Interface dependencies**: `SysCall`, `PMDecl`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `PrStd`, `PrBuf`, `CiDev`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `CiOpen` | `PROCEDURE CiOpen(VAR prRec: TPrRec);` | Opens the C. Itoh printer port for `prRec`, allocates/installs QuickDraw band or draft text buffers, and initializes the hardware via `CiDevOpen`. |
| `CiClose` | `PROCEDURE CiClose(VAR prRec: TPrRec);` | Resets the C. Itoh printer via `CiDevClose` and closes the OS printer port configured in `prRec`. |
| `CiCleanup` | `PROCEDURE CiCleanup(VAR prRec: TPrRec);` | Cleans up an aborted C. Itoh print job for `prRec`, ejecting any partially printed page before closing the device and port. |
| `CiMetrics` | `PROCEDURE CiMetrics(VAR prRec: TPrRec);` | Computes C. Itoh horizontal/vertical resolution, paper bounds, and printable rectangle metrics into `prRec` for the selected paper size, orientation, and print mode. |
| `CiXMetrics` | `PROCEDURE CiXMetrics(VAR prRec: TPrRec);` | Computes extended C. Itoh band-buffering metrics (`rBand`, `rBounds`, and `lBandSize`) in `prRec` for draft text or raster band printing. |
| `CiDumpBand` | `PROCEDURE CiDumpBand(VAR prRec: TPrRec);` | Outputs the current rendered band for `prRec` to the C. Itoh printer, either flushing buffered draft text scanlines or printing the band bitmap via `CiPrBMVert`/`CiPrBMHoriz`. |
| `CiEjectPage` | `PROCEDURE CiEjectPage;` | Advances the C. Itoh printer to the next page via `CiNewPage` if the current page is marked dirty, then clears the dirty flag. |
| `CiStdText` | `PROCEDURE CiStdText(count: TC; textAddr: QDPtr; numer, denom: Point);` | Custom QuickDraw `textProc` bottleneck for C. Itoh draft printing that records `count` characters at `textAddr` into the print command buffer (`PbText`) unless aborted. |

---

## Unit CpDev

Low-level device driver interface for the parallel Canon Inkjet printer, providing buffered command output, deferred 1/144-inch vertical paper positioning, character pitch and style selection, horizontal/vertical bitmap band printing, and raw or run-length-encoded raster graphics transmission.

- **Import**: `USES {$U CpDev.obj} CpDev;`
- **Unit kind**: `INTRINSIC` (`CPDEV`)
- **Interface dependencies**: `SysCall`, `PMDecl`, `UnitStd`, `QuickDraw`, `PrStd`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `CpDevInit` | `PROCEDURE CpDevInit;` | Initializes internal driver state and buffers for the parallel Canon Inkjet printer. |
| `CpDevOpen` | `PROCEDURE CpDevOpen(fFastGraf, fPEStop: BOOLEAN);` | Opens and resets the parallel Canon Inkjet printer, configuring fast-graphics mode (`fFastGraf`) and paper-empty stop behavior (`fPEStop`). |
| `CpDevClose` | `PROCEDURE CpDevClose;` | Flushes deferred vertical motion and buffered output and resets the parallel Canon Inkjet printer to its default idle state. |
| `CpSetBiDir` | `PROCEDURE CpSetBiDir(fBiDir: BOOLEAN);` | Enables (`fBiDir = TRUE`) or disables (`fBiDir = FALSE`) bidirectional print-head motion on the parallel Canon Inkjet printer. |
| `CpSetBpi` | `PROCEDURE CpSetBpi(tybpi: TTybpi);` | Emits the escape sequence selecting horizontal dot/character density `tybpi` on the parallel Canon Inkjet printer. |
| `CpSetEmph` | `PROCEDURE CpSetEmph(fEmph: BOOLEAN);` | Enables (`fEmph = TRUE`) or disables (`fEmph = FALSE`) emphasized boldface text mode on the parallel Canon Inkjet printer. |
| `CpSetLFFwd` | `PROCEDURE CpSetLFFwd(fFwd: BOOLEAN);` | Sets the parallel Canon Inkjet paper line-feed direction to forward (`fFwd = TRUE`) or reverse (`fFwd = FALSE`). |
| `CpSetLineHt` | `PROCEDURE CpSetLineHt(c144ths: INTEGER);` | Sets the parallel Canon Inkjet line-feed step height to `c144ths` (in 1/144-inch units). |
| `CpSetPEStop` | `PROCEDURE CpSetPEStop(fPEStop: BOOLEAN);` | Configures the parallel Canon Inkjet printer to stop (`fPEStop = TRUE`) or continue (`fPEStop = FALSE`) when paper-out is detected. |
| `CpSetUL` | `PROCEDURE CpSetUL(fUL: BOOLEAN);` | Enables (`fUL = TRUE`) or disables (`fUL = FALSE`) hardware-underlined character printing on the parallel Canon Inkjet printer. |
| `CpSetWide` | `PROCEDURE CpSetWide(fWide: BOOLEAN);` | Enables (`fWide = TRUE`) or disables (`fWide = FALSE`) elongated double-width character printing on the parallel Canon Inkjet printer. |
| `CpBindV` | `PROCEDURE CpBindV;` | Commits any deferred vertical paper movement (`CpGotoV`/`CpDeltaV`) by emitting the corresponding line-feed commands to the parallel Canon Inkjet printer. |
| `CpDeltaV` | `PROCEDURE CpDeltaV(c144ths: INTEGER);` | Adjusts the deferred vertical paper target position on the parallel Canon Inkjet printer by relative offset `c144ths` (in 1/144-inch units). |
| `CpGotoV` | `PROCEDURE CpGotoV(c144ths: INTEGER);` | Sets the deferred absolute vertical paper position on the current page to `c144ths` (in 1/144-inch units). |
| `CpNewPage` | `PROCEDURE CpNewPage;` | Advances paper to the top of the next form, flushes the output buffer, and resets the Canon Inkjet vertical page coordinate. |
| `CpSetFormLng` | `PROCEDURE CpSetFormLng(cPg144ths: INTEGER);` | Sets the logical page form height tracked by `CpDev` to `cPg144ths` (in 1/144-inch units). |
| `CpPrBand` | `PROCEDURE CpPrBand(p: TP; cScans: INTEGER);` | Prints a raster band of `cScans` scanlines from `p` on the parallel Canon Inkjet printer and advances the vertical paper position. |
| `CpPrBMHoriz` | `PROCEDURE CpPrBMHoriz(pBM: QDPtr; rBand: Rect);` | Extracts and prints band `rBand` of QuickDraw bitmap `pBM` in horizontal landscape orientation on the parallel Canon Inkjet printer. |
| `CpPrBMVert` | `PROCEDURE CpPrBMVert(pBM: QDPtr; rBand: Rect);` | Extracts and prints band `rBand` of QuickDraw bitmap `pBM` in vertical portrait orientation on the parallel Canon Inkjet printer. |
| `CpPrGraf` | `PROCEDURE CpPrGraf(p: TP; cBytes: INTEGER);` | Emits a Canon Inkjet raw bit-image graphics escape command followed by `cBytes` of uncompressed raster bytes from `p`. |
| `CpPrRun` | `PROCEDURE CpPrRun(p: TP; cBytes: INTEGER);` | Emits a Canon Inkjet run-length-encoded graphics escape command followed by `cBytes` of repeat-coded raster data from `p`. |
| `CpPrTab` | `PROCEDURE CpPrTab(cPos: INTEGER);` | Commits deferred vertical motion and tabs the parallel Canon Inkjet print head horizontally to position `cPos`. |
| `CpPrText` | `PROCEDURE CpPrText(p: TP; cChars: INTEGER);` | Commits deferred vertical motion and outputs `cChars` text characters from `p` to the parallel Canon Inkjet printer with character-set mapping. |
| `CpDmpBuf` | `PROCEDURE CpDmpBuf;` | Flushes all bytes queued in `CpDev`'s internal output buffer to the parallel printer port. |
| `CpHRes` | `FUNCTION CpHRes(tybpi: TTybpi): INTEGER;` | Returns the horizontal resolution in dots per inch corresponding to density selector `tybpi` on the parallel Canon Inkjet printer. |
| `CpMaxBits` | `FUNCTION CpMaxBits(tybpi: TTybpi; cWidth10ths: INTEGER): INTEGER;` | Returns the maximum horizontal dot count across paper width `cWidth10ths` (in tenths of an inch) at density `tybpi` on the parallel Canon Inkjet printer. |
| `CpOut` | `PROCEDURE CpOut(b: TB);` | Appends byte `b` to `CpDev`'s output buffer, automatically flushing via `CpDmpBuf` when full. |

---

## Unit CpProcs

High-level Print Shop driver unit for the parallel Canon Inkjet printer, managing device session open/close and abort cleanup, page and band metric calculation, band rasterization/dumping, and page ejection.

- **Import**: `USES {$U CpProcs.obj} CpProcs;`
- **Unit kind**: `INTRINSIC` (`CPPROCS`)
- **Interface dependencies**: `SysCall`, `PMDecl`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `PrStd`, `PrBuf`, `CpDev`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `CpOpen` | `PROCEDURE CpOpen(VAR prRec: TPrRec);` | Opens the parallel Canon Inkjet printer port for `prRec`, initializes QuickDraw band/text buffers, and resets the device via `CpDevOpen`. |
| `CpClose` | `PROCEDURE CpClose(VAR prRec: TPrRec);` | Resets the parallel Canon Inkjet printer via `CpDevClose` and closes the OS port configured in `prRec`. |
| `CpCleanup` | `PROCEDURE CpCleanup(VAR prRec: TPrRec);` | Cleans up an aborted parallel Canon Inkjet print job for `prRec`, ejecting any dirty page before closing the device and port. |
| `CpMetrics` | `PROCEDURE CpMetrics(VAR prRec: TPrRec);` | Computes parallel Canon Inkjet resolution, paper rectangle, and printable page bounds into `prRec` for the selected format. |
| `CpXMetrics` | `PROCEDURE CpXMetrics(VAR prRec: TPrRec);` | Computes extended parallel Canon Inkjet band-buffering metrics (`rBand`, `rBounds`, and `lBandSize`) in `prRec`. |
| `CpDumpBand` | `PROCEDURE CpDumpBand(VAR prRec: TPrRec);` | Renders and transmits the current page band for `prRec` to the parallel Canon Inkjet printer in draft text or raster bitmap mode. |
| `CpEjectPage` | `PROCEDURE CpEjectPage;` | Advances the parallel Canon Inkjet printer to the next sheet via `CpNewPage` if the current page is marked dirty, clearing the dirty flag. |

---

## Unit DBEnv

Defines foundational low-level byte and integer array, pointer, and handle types (`byte`, `data`, `ptrdata`, `hnddata`, `intdata`, `ptrintdata`, and `hndintdata`) shared across Lisa database, Field Editor, and Office System units.

- **Import**: `USES {$U DBEnv.obj} DBEnv;`
- **Unit kind**: `INTRINSIC` (`DBENV`)

*This unit exports constants, data types, and/or global variables only (no callable procedures or functions).*

---

## Unit Events

Implements the Lisa Window Manager Event Manager (`Events` shared intrinsic), providing per-process event queueing, low-level keyboard/mouse interrupt classification, active-process polling, screen printing, and event journal recording and playback.

- **Import**: `USES {$U Events.obj} Events;`
- **Unit kind**: `INTRINSIC SHARED` (`EVENTS`)
- **Interface dependencies**: `SysCall`, `PSysCall`, `HWInt`, `UnitStd`, `UnitHz`, `Storage`, `PMDecl`, `PMM`, `QuickDraw`, `FontMgr`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `Abort` | `FUNCTION Abort: BOOLEAN;` | Drains low-level hardware input without generating updates and returns `TRUE` if an `abortEvent` (Command-Period) is queued for the calling process. |
| `Button` | `FUNCTION Button: BOOLEAN;` | Returns `TRUE` if the mouse button is currently depressed (supporting journal playback and Monkey testing) and resets the busy-cursor delay when the caller is active. |
| `CheckEvents` | `PROCEDURE CheckEvents(updateOK: BOOLEAN);` | Pulls all pending hardware key and mouse transitions from the interrupt queue, classifies them into window events via `CheckWindow`, and sends a window update if `updateOK` is `TRUE` and no events remain. |
| `DeleteEvent` | `PROCEDURE DeleteEvent(evHandle: EventHandle);` | Unlinks and disposes the event node referenced by `evHandle` from the Window Manager event queue and unlocks the queue. |
| `ElapsTime` | `FUNCTION ElapsTime: LongInt;` | Returns the elapsed time since system boot in microseconds (computed as the hardware millisecond `Timer` multiplied by 1000). |
| `EventAvail` | `FUNCTION EventAvail: BOOLEAN;` | Processes pending low-level input and returns `TRUE` if the oldest queued event belongs to the calling process, or wakes the owning process at the queue head otherwise. |
| `FirstEvent` | `FUNCTION FirstEvent: EventHandle;` | Drains low-level hardware input without generating updates and returns an `EventHandle` to the oldest event in the Window Manager queue, or `NIL` if empty. |
| `GetEvent` | `PROCEDURE GetEvent(VAR event: EventRecord);` | Removes and returns the oldest queued `EventRecord` for the calling process, yielding or suspending the process until one arrives and locking the queue if `folderDeactivate` is returned. |
| `GetEvFrom` | `PROCEDURE GetEvFrom(fromProcess: ProcessID; VAR event: EventRecord);` | Waits for, copies into `event`, and deletes the first non-deactivate event in the queue sent from `fromProcess` to the calling process. |
| `GetKeys` | `PROCEDURE GetKeys(VAR keys: KeySet);` | Returns the current down/up state of all 128 physical keyboard and switch keycodes in `keys` (supporting journal recording and playback). |
| `GetMouse` | `PROCEDURE GetMouse(VAR pt: Point);` | Returns the current mouse position in `pt` converted to the local coordinates of `thePort` (supporting journal playback and Monkey testing). |
| `ImActive` | `FUNCTION ImActive: BOOLEAN;` | Returns `TRUE` if the calling OS process is currently the active desktop process (`activeProcess`). |
| `InitEvents` | `PROCEDURE InitEvents;` | Performs one-time initialization of the Window Manager event queue in `wmHeap`, setting up sentinel nodes, default click/caret timings, and the hourglass busy cursor. |
| `LetOthersRun` | `PROCEDURE LetOthersRun;` | Yields the CPU to other ready processes, first lowering the calling process's priority to 120 if it is not the active process. |
| `NextEvent` | `FUNCTION NextEvent(evHandle: EventHandle): EventHandle;` | Returns an `EventHandle` to the event node immediately following `evHandle` in the Window Manager queue, or `NIL` at the tail. |
| `PeekEvent` | `FUNCTION PeekEvent(VAR event: EventRecord): BOOLEAN;` | Returns `TRUE` and copies the next available `EventRecord` for the calling process into `event` (with `event.where` converted to local window coordinates) without removing it from the queue. |
| `PrintScreen` | `PROCEDURE PrintScreen;` | Dumps the entire Lisa primary screen bitmap to a configured dot-matrix printer. |
| `PushEvent` | `PROCEDURE PushEvent(VAR event: EventRecord);` | Inserts `event` at the front (head) of the Window Manager event queue in `wmHeap` and wakes the target process. |
| `SendEvent` | `PROCEDURE SendEvent(VAR event: EventRecord; toPrcs: ProcessId);` | Appends a copy of `event` addressed to process `toPrcs` at the tail of the Window Manager event queue in `wmHeap`. |
| `StillDown` | `FUNCTION StillDown: BOOLEAN;` | Returns `TRUE` only if the mouse button is currently held down and no mouse-button transition events are waiting in the event queue. |
| `Time` | `FUNCTION Time: LongInt;` | Returns the elapsed time since system boot in hundredths of a second (`1/100` second ticks), supporting journal recording and playback. |
| `WakeUpHead` | `PROCEDURE WakeUpHead;` | Activates the OS process targeted by the event at the head of the Window Manager queue, discarding orphaned events and cleaning up if that process has died. |
| `StartPlayback` | `PROCEDURE StartPlayback(fileName: PathName; journalMode: INTEGER);` | Opens event journal file `fileName`, flushes pending hardware and Window Manager events, and starts replaying recorded input events in `journalMode`. |
| `StartRecording` | `PROCEDURE StartRecording(fileName: PathName; journalMode: INTEGER);` | Creates and opens event journal file `fileName` and starts recording keyboard, mouse, button, and timing state transitions in `journalMode`. |
| `StopPlayback` | `PROCEDURE StopPlayback;` | Stops active event journal playback, re-enables hardware cursor tracking, and closes the playback file. |
| `StopRecording` | `PROCEDURE StopRecording;` | Writes an end-of-journal record, disables event journal recording, and closes the recording file. |

---

## Unit FEDec

Declares shared constants and data structures for the Lisa Field Editor (`FieldEdit` and `FldUt`), including error codes (`fldFull`..`FENotUndoable`), alignment and style-change constants, edit operation tags (`noOp`..`formulaToValueOp`), selection/highlighting types (`interval`, `txSel`, `TtySel`, `TtyHilight`), and core editing records (`field`, `fieldState`, `run`, `undoInfo`, `ScrapRec`).

- **Import**: `USES {$U FEDec.obj} FEDec;`
- **Unit kind**: `INTRINSIC` (`FEDEC`)
- **Interface dependencies**: `UnitStd`, `UnitHz`, `QuickDraw`, `FontMgr`, `Storage`, `DBEnv`

*This unit exports constants, data types, and/or global variables only (no callable procedures or functions).*

---

## Unit FieldEdit

Implements the single-line Lisa Field Editor for Office System applications and dialogs, supporting multi-run styled text, mouse point/word/drag selection, caret blinking, gap-buffer character and word editing, scrap/stream cut-copy-paste, and single-level undo.

- **Import**: `USES {$U FieldEdit.obj} FieldEdit;`
- **Unit kind**: `INTRINSIC` (`FIELDEDI`)
- **Interface dependencies**: `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `SysCall`, `Events`, `Folders`, `WmlStd`, `WmlSb`, `DBEnv`, `FEDec`, `Scrap`, `UnitFmt`, `PMDecl`, `PrStdInfo`, `UnitCs`, `FldUt`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `FEInit` | `procedure FEInit(hz: THz; passtrpl: Ttriple; var errnum: integer);` | Initializes the Field Editor on heap zone `hz`, setting up Modern/Classic font mapping tables, dim caret/selection patterns, word-break triples (`passtrpl`), and undo structures. |
| `FETerminate` | `procedure FETerminate;` | Converts a Field Editor scrap (`scrapFE`) owned by the calling process into a Universal Text stream (`tycsFld`) prior to application termination. |
| `LdFESeg` | `procedure LdFESeg;` | Forces the main Field Editor code segment (`FEothrwk`) to be swapped into memory via a no-op call. |
| `UseSubstituteFont` | `procedure UseSubstituteFont(Substitute: Boolean; DevtoSub: Integer);` | Enables (`Substitute = TRUE`) or disables (`Substitute = FALSE`) printer font substitution for device `DevtoSub` during Field Editor measurement and drawing. |
| `SetFCoords` | `procedure SetFCoords(hf: hndField; hfs: hndFState; c: Rect);` | Sets the bounding rectangle (`coords`) of field `hf` to `c` and updates cached display state and `selectRect` in `hfs` if the field is being edited. |
| `SetFAlign` | `procedure SetFAlign(hf: hndField; hfs: hndFState; a: byte);` | Sets the horizontal alignment (`left`, `right`, or `center`) of field `hf` to `a` and invalidates cached display state in `hfs`. |
| `SetFPad` | `procedure SetFPad(hf: hndField; hfs: hndFState; pad: byte);` | Sets the horizontal drawing margin padding (`drawPad`, in pixels) of field `hf` to `pad` and invalidates cached display state in `hfs`. |
| `SetFProtect` | `procedure SetFProtect(hf: hndField; hfs: hndFState; p: boolean);` | Sets the edit-protection flag (`protect`) of field `hf` to `p`. |
| `InitFState` | `procedure InitFState(hf: hndField; hfs: hndFState);` | Initializes `fieldState` handle `hfs` for editing field `hf`, clearing selection highlighting and setting up the internal gap-buffer pointers. |
| `CreateField` | `function CreateField(c: Rect; iLen, gLen: integer; a: byte; pad: byte; iFmts, gFmts: integer; fontNum: integer; p: boolean): hndField;` | Allocates and initializes a new `field` handle on the Field Editor heap with bounds `c`, character capacity/grow (`iLen`, `gLen`), alignment `a`, padding `pad`, format-run capacity/grow (`iFmts`, `gFmts`), initial `fontNum`, and protection flag `p`. |
| `RemoveField` | `procedure RemoveField(hf: hndField);` | Deallocates the character data handle, format-run handle, and `field` structure `hf` from their heap zone. |
| `FmtFromLp` | `function FmtFromLp(hf: hndField; hfs: hndFState; lp: integer): integer;` | Returns the 0-based index in `hf^^.fmtInfo` of the character format run governing logical position `lp`. |
| `FmtFromInt` | `procedure FmtFromInt(hf: hndField; hfs: HndFState; Int: interval; var Plain: boolean; var result: run);` | Computes the common formatting across character interval `Int` in field `hf`, returning the intersected style and font (`-1` if mixed) in `result` and setting `Plain` to `TRUE` if no styles are set anywhere in `Int`. |
| `SetRunInterval` | `procedure SetRunInterval(hf: hndField; hfs: hndFState; fontNum: integer; format: integer; int: interval; var errNum: integer);` | Applies font or style operation `format` (with `fontNum` when setting a font) over character interval `int` in field `hf` and merges any resulting duplicate adjacent runs. |
| `SetRunFormat` | `procedure SetRunFormat(hf: hndField; hfs: hndFState; fontNum: integer; format: integer; var errNum: integer);` | Applies non-undoable programmatic formatting `format` to the active selection in `hfs`—or to every run in `hf` when `hfs` is `NIL`—ignoring the field protection flag. |
| `UpdateRun` | `procedure UpdateRun(hf: hndField; hfs: hndFState; fontNum: integer; format: integer; var errNum: integer);` | Applies user-requested font or style formatting `format` to the current selection in field `hf` (honoring field protection) and records the change as separately undoable. |
| `VertCoords` | `procedure VertCoords(hf: hndField; var ascent, descent: integer);` | Computes the maximum font `ascent` and `descent` (including underline allowance) across all format runs in field `hf`. |
| `MoveField` | `procedure MoveField(hf: hndField; hfs: hndFState; dx: Point);` | Recomputes and stores `hf^^.coords` around anchor point `dx` using field `hf`'s maximum font ascent/descent, text width, padding, and alignment. |
| `DrawField` | `procedure DrawField(hf: hndField; hfs: hndFState; showSelect, erase: boolean);` | Draws the text contents and optional selection highlight (`showSelect`) of field `hf` within its current `coords` in `thePort`, optionally erasing the background first (`erase`). |
| `DrawFldAt` | `procedure DrawFldAt(hf: hndField; hfs: hndFState; dx: Point; showSelect, erase: boolean);` | Updates field `hf`'s coordinates around anchor point `dx`, optionally erases the union of its old and new bounds (`erase`), and renders its text and selection (`showSelect`). |
| `SetSel` | `procedure SetSel(hf: hndField; hfs: hndFState; lpFst: integer; lpLim: integer; selType: TtySel);` | Sets the selection and anchor in `hfs` to `[lpFst, lpLim)` with granularity `selType`, using a caret highlight when `lpFst = lpLim` or inversion otherwise. |
| `SelectAll` | `procedure SelectAll(hf: hndField; hfs: hndFState; var t: integer);` | Initializes `hfs`, selects and highlights the entire contents of field `hf` (or places a caret if empty), and starts caret blink timer `t` when entering a field from the keyboard. |
| `ExitField` | `procedure ExitField(hf: hndField; hfs: hndFState);` | Finishes editing field `hf` by turning off selection highlighting, packing characters across the editing gap buffer, and removing redundant format runs so `hfs` can be discarded. |
| `CompactField` | `procedure CompactField(hf: hndField);` | Shrinks the heap blocks of `hf^^.curValue` and `hf^^.fmtInfo` in multiples of `growLen` and `growFmts` to reclaim unused space after `ExitField`. |
| `ErrorSelect` | `procedure ErrorSelect(hf: hndField; hfs: hndFState; lpFst: integer; lpLim: integer; var t: integer);` | Selects and highlights interval `[lpFst, lpLim)` in field `hf` and starts caret blink timer `t` so the user can correct a validation error. |
| `HilightSel` | `procedure HilightSel(hf: hndField; hfs: hndFState; fShow: boolean);` | Turns visual highlighting of the current selection in `hfs` on (`fShow = TRUE`) or off (`fShow = FALSE`). |
| `ChangeSelHilight` | `procedure ChangeSelHilight(hf: hndField; hfs: hndFState; toDim: boolean);` | Switches the selection highlight of field `hf` between normal active highlighting and inactive dim gray highlighting (`toDim = TRUE`). |
| `LpFromX` | `function LpFromX(x: integer; hf: hndField; hfs: hndFState; seltype: ttysel): integer;` | Converts horizontal pixel coordinate `x` in field `hf` into a logical character position, returning the containing character for word selection (`tySelWd`) or the nearest caret boundary otherwise. |
| `LwFromLp` | `procedure LwFromLp(orig: integer; hf: hndField; hfs: hndFState; var lWord: interval; Var FoundWord: boolean);` | Finds the word containing logical position `orig` in field `hf`, returning its expanded `[lpFst, lpLim)` interval in `lWord` and setting `FoundWord` to `TRUE` if found. |
| `CompressedLp` | `function CompressedLp(lp: integer; hf: hndField; hfs: hndFState; var valid: boolean): integer;` | Translates an expanded buffer index `lp` in field `hf` to a compressed logical position with the temporary editing gap removed, setting `valid` to `FALSE` if `lp` lies inside the gap. |
| `ExpandedLp` | `function ExpandedLp(lp: integer; hf: hndField; hfs: hndFState): integer;` | Translates a compressed logical character position `lp` into its actual index in `hf^^.curValue` by adding the temporary editing gap in `hfs`. |
| `RepSelect` | `procedure RepSelect(lp: integer; hf: hndField; hfs: hndFState);` | Replicates a point caret selection at logical position `lp` in field `hf` and highlights it to mirror selection in a duplicate view. |
| `Select` | `procedure Select(dxy: Point; hf: hndField; hfs: hndFState; var n: Rect; var t: integer);` | Processes a mouse-down click at `dxy` in field `hf` by placing and highlighting the insertion caret, setting drag neighborhood `n`, and disabling caret blinking (`t := -1`). |
| `RepWordSelect` | `procedure RepWordSelect(int: interval; hf: hndField; hfs: hndFState);` | Replicates a word selection across interval `int` in field `hf` and highlights it to mirror double-click selection in a duplicate view. |
| `SelectWord` | `procedure SelectWord(dxy: Point; hf: hndField; hfs: hndFState; var n: rect; var t: integer);` | Processes a double-click at `dxy` in field `hf` by selecting and highlighting the word (or adjacent character) under the mouse, setting drag neighborhood `n`, and stopping caret blinking (`t := -1`). |
| `RepGrowSel` | `procedure RepGrowSel(chlp: integer; hf: hndField; hfs: hndFState);` | Replicates drag-extension of the current selection to logical position `chlp` in field `hf`, updating selection highlighting relative to the anchor. |
| `GrowSel` | `procedure GrowSel(dxy: Point; hf: hndField; hfs: hndFState; var n: Rect);` | Extends or shrinks the active point or word selection in field `hf` to mouse drag position `dxy` and updates mouse neighborhood rectangle `n`. |
| `CaretErased` | `procedure CaretErased(hf: hndField; hfs: hndFState);` | Synchronizes `hfs` state (`visCaret := FALSE`, `selectOn := FALSE`) after the caller has externally erased the caret on screen. |
| `StartBlink` | `procedure StartBlink(var t: integer);` | Sets blink timer `t` to `CaretOffTime` upon mouse-button release to initiate periodic caret blinking. |
| `BlinkCaret` | `procedure BlinkCaret(hf: hndField; hfs: hndFState; var t: integer);` | Inverts the active insertion caret rectangle in field `hf` on a blink timeout and updates `t` to the next on/off blink duration. |
| `CaretOn` | `procedure CaretOn(hf: hndField; hfs: hndFState);` | Ensures that an active insertion caret in field `hf` is visibly drawn before processing keyboard character or word edits. |
| `InsCh` | `procedure InsCh(ch: char; hf: hndField; hfs: hndFState; var errNum: integer);` | Inserts character `ch` into field `hf` at the current selection (replacing any selected text, growing the buffer if needed, and saving undo state), or returns `fldProtected` or `fldFull` in `errNum`. |
| `Backspace` | `procedure Backspace(hf: hndField; hfs: hndFState; var errNum: integer);` | Deletes the current selection or backs over one character preceding the caret in field `hf` via the backspace gap pointer, returning any error in `errNum`. |
| `Forwardspace` | `procedure Forwardspace(hf: hndField; hfs: hndFState; var errNum: integer);` | Restores one character previously backed over by `Backspace` in field `hf` by advancing the backspace pointer, or sets `errNum` to `invalidEdit`. |
| `BackWord` | `procedure BackWord(hf: hndField; hfs: hndFState; var errNum: integer);` | Deletes from the caret back to the start of the current or previous word in field `hf` by retreating the backspace pointer, or sets `errNum` on error. |
| `ForwardWord` | `procedure ForwardWord(hf: hndField; hfs: hndFState; var errNum: integer);` | Restores the last word backed over by `BackWord` in field `hf` by advancing the backspace pointer across that word, or sets `errNum` to `invalidEdit`. |
| `DrawScrap` | `procedure DrawScrap(var errnum: integer);` | Draws the Field Editor scrap (`scrapFE`) inside the system `scrapFolder` port, returning `invScrapType` or scrap-access errors in `errnum`. |
| `CutCopyField` | `procedure CutCopyField(hf: hndField; hfs: hndFState; fCut: boolean; fIntoScrap: boolean; var errNum: integer);` | Cuts (`fCut = TRUE`) or copies (`fCut = FALSE`) the current selection in field `hf`, writing the selected text and formatting into the system scrap when `fIntoScrap` is `TRUE`. |
| `PasteField` | `procedure PasteField(hf: hndField; hfs: hndFState; var errNum: integer; pasteFmt: boolean; PasteLimit: integer);` | Replaces the current selection in field `hf` with up to `PasteLimit` characters from the system scrap or Universal Text stream, optionally preserving format runs when `pasteFmt` is `TRUE`. |
| `UndoEdit` | `procedure UndoEdit(hf: hndField; hfs: hndFState; var errNum: integer);` | Undoes the most recent editing or formatting operation performed on field `hf` using the Field Editor's saved undo record. |
| `ClearField` | `procedure ClearField(hf: hndField; hfs: hndFState; var errNum: integer);` | Clears the entire text contents of field `hf` regardless of the current selection (saving undo state when `hfs` is non-`NIL`), or returns `fldProtected` in `errNum`. |
| `qualifies` | `Function qualifies(lp: integer; hf: hndfield; hfs: hndfstate): boolean;` | Returns `TRUE` if the character at compressed logical position `lp` in field `hf` qualifies as part of a word under the character-class triple rules given to `FEInit`. |

---

## Unit FilerComm

Provides the interprocess communication protocol between Lisa Office System applications and the Desktop Manager (Filer), handling document open/close/copy/print/terminate events, catalog pathname-to-prefix translation, document diskfile copying, and scrap icon references.

- **Import**: `USES {$U FilerComm.obj} FilerComm;`
- **Unit kind**: `INTRINSIC SHARED` (`FILERCOM`)
- **Interface dependencies**: `SysCall`, `PSysCall`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `GrafUtil`, `WmlStd`, `WmlSb`, `FontMgr`, `Events`, `Windows`, `Folders`, `Scrap`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `CopyDoc` | `PROCEDURE CopyDoc(VAR error: INTEGER; fromPrefix, toPrefix: Pathname; useLdsn: INTEGER; theOp: FCopyOp; VAR docSize: LONGINT);` | Copies all OS diskfiles of a document from `fromPrefix` to `toPrefix` using data segment `useLdsn`, updating file timestamps per `theOp` and returning total disk blocks in `docSize`. |
| `DoFilingCmd` | `PROCEDURE DoFilingCmd(whichCmd: FilingCmd);` | Sends an application filing menu command (`cmdClose` or `cmdClosAll`) to the Desktop Manager (Filer) when chosen by the user. |
| `GetAddParms` | `PROCEDURE GetAddParms(VAR error: INTEGER; theEvent: EventRecord; VAR theFilerExt: FilerExt);` | Extracts the extended `FilerExt` parameters (operation code, diskfile refnum, password, and document prefixes) attached to a `filerEvent` in `theEvent`. |
| `TellFiler` | `PROCEDURE TellFiler(VAR error: INTEGER; what: FReply; why: FReason; myFolder: WindowPtr);` | Sends a completion reply (`what`) and status reason (`why`) for window `myFolder` back to the Desktop Manager (Filer) in response to a Filer request or unsolicited close/initialization failure. |
| `NameToPrefix` | `PROCEDURE NameToPrefix(VAR err, offset: INTEGER; myFolder: WindowPtr; name: Pathname; VAR prefix: Pathname);` | Queries the Desktop Manager catalog to translate a hierarchical desktop icon pathname (`name`) into its OS diskfile name prefix (`prefix`), returning the offending character `offset` on error. |
| `PrefixToName` | `PROCEDURE PrefixToName(VAR err, offset: INTEGER; myFolder: WindowPtr; prefix: Pathname; VAR name: Pathname);` | Queries the Desktop Manager catalog to translate an OS diskfile name prefix (`prefix`) into its hierarchical desktop icon pathname (`name`). |
| `CopyDiskfile` | `PROCEDURE CopyDiskfile(VAR err: INTEGER; source, destination: Pathname; bufrAdrs, bufrSize: LONGINT; theOp: FCopyOp; VAR osErr: INTEGER);` | Copies a single OS diskfile from `source` to `destination` for the Filer using the caller-provided transfer buffer (`bufrAdrs`, `bufrSize`) and timestamp mode `theOp`. |

---

## Unit FldUt

Bridges the Lisa Field Editor with the Universal Text (`UnitCs`) character stream architecture so field scrap data can be read sequentially as formatted text runs by other Office System tools.

- **Import**: `USES {$U FldUt.obj} FldUt;`
- **Unit kind**: `INTRINSIC` (`FLDUT`)
- **Interface dependencies**: `UnitStd`, `UnitHz`, `QuickDraw`, `FontMgr`, `Storage`, `SysCall`, `Events`, `DBEnv`, `FEDec`, `PMDecl`, `PrStdInfo`, `UnitFmt`, `UnitCs`, `Scrap`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `CreateFldUt` | `function CreateFldUt(StreamHeap: THz): TB;` | Allocates and initializes a Universal Text input character stream (`TFldUT` ICS of type `tycsFld`) in `StreamHeap` with `SeqLpdFld` registered as its sequential read callback, returning its stream index. |
| `SeqLpdFld` | `procedure SeqLpdFld(Lpd: TLpd; var achad: Tachad);` | Advances character stream descriptor `Lpd` and returns in `achad` the longest contiguous character and style run from the underlying Field Editor scrap field within the requested interval. |

---

## Unit FmgrUtil

Provides Font Manager utility routines for extracting and drawing icons, 8x8 QuickDraw patterns, and 16x16 cursors stored as character glyphs in special system icon, pattern, and cursor font families.

- **Import**: `USES {$U FmgrUtil.obj} FmgrUtil;`
- **Unit kind**: `INTRINSIC` (`FMGRUTIL`)
- **Interface dependencies**: `UnitStd`, `UnitHz`, `SysCall`, `QuickDraw`, `FontMgr`, `Storage`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `GetIcon` | `FUNCTION GetIcon(fam: Tfam; cc: TCc; VAR rSrc: Rect; VAR bmSrc: BitMap; VAR cError: TC): TF;` | Maps character code `cc` in icon font family `fam` to its glyph `BitMap` (`bmSrc`) and bounding `Rect` (`rSrc`), returning `TRUE` if the icon was retrieved without error. |
| `DrawIcon` | `PROCEDURE DrawIcon(fam: Tfam; rDst: Rect; cc: TCc; cmode: TC; VAR cError: TC);` | Draws the icon glyph at character code `cc` in font family `fam` centered within destination rectangle `rDst` using QuickDraw transfer mode `cmode`. |
| `GetPattern` | `PROCEDURE GetPattern(fam: Tfam; ccPat: TCc; VAR pat: Pattern; VAR cError: TC);` | Extracts the 8x8 QuickDraw `Pattern` stored at character code `ccPat` in pattern font family `fam` into `pat`. |
| `GetCursor` | `PROCEDURE GetCursor(fam: Tfam; ccData, ccMask: TCc; VAR curse: Cursor; VAR cError: TC);` | Extracts a 16x16 QuickDraw `Cursor` (`curse`) from cursor font family `fam` using character codes `ccData` for the image bitmap and `ccMask` for the mask bitmap. |

---

## Unit Folders

Implements high-level Lisa Window Manager folder operations, managing desktop document folders and system windows (`dialogFolder`, `alertFolder`, `menuFolder`, `scrapFolder`), window activation/deactivation handoffs, update/invalidation regions, process cleanup, and refresh pictures.

- **Import**: `USES {$U Folders.obj} Folders;`
- **Unit kind**: `INTRINSIC SHARED` (`FOLDERS`)
- **Interface dependencies**: `HWInt`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `SysCall`, `Events`, `PMDecl`, `PMM`, `Windows`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `BeginUpdate` | `PROCEDURE BeginUpdate(folder: WindowPtr);` | Begins handling a `folderUpdate` event for `folder` by intersecting its `visRgn` with `updateRgn` and clearing `updateRgn`. |
| `DialogHeight` | `PROCEDURE DialogHeight(height: INTEGER; fUpdate: BOOLEAN);` | Resizes the system `dialogFolder` banner to `height` pixels, hiding it if `height <= 0` or making it visible and redrawing it (with optional update events per `fUpdate`). |
| `DisposeFolder` | `PROCEDURE DisposeFolder(folder: WindowPtr);` | Removes `folder` from the desktop window list, flushes its queued events and refresh picture, disposes its regions and title, and redraws uncovered windows behind it. |
| `EndUpdate` | `PROCEDURE EndUpdate(folder: WindowPtr);` | Completes update redrawing for `folder` by recalculating and restoring its normal visible region (`visRgn`) after `BeginUpdate`. |
| `FlushInput` | `PROCEDURE FlushInput(window: WindowPtr);` | Deletes pending button, key, activate, deactivate, and abort events for `window` (or for all windows when `window = NIL`), brings `activeFolder` to the front, and unlocks the event queue. |
| `FlushWindow` | `PROCEDURE FlushWindow(window: WindowPtr);` | Deletes all queued events addressed to `window` as well as any `folderDeactivate` events sent from `window`, and unlocks the event queue. |
| `FlushProcess` | `PROCEDURE FlushProcess(process: ProcessID);` | Deletes all queued events addressed to `process` as well as any `folderDeactivate` events sent from `process`, and unlocks the event queue. |
| `FolderSize` | `PROCEDURE FolderSize(folder: WindowPtr; width, height: INTEGER; fUpdate: BOOLEAN);` | Resizes `folder`'s content port to `width` by `height` pixels (clamped to screen limits) and optionally posts update events when `fUpdate` is `TRUE`. |
| `GetFldrRefCon` | `FUNCTION GetFldrRefCon(folder: WindowPtr): LongInt;` | Returns the 32-bit application reference constant (`refCon`) associated with `folder`. |
| `GetFldrTitle` | `PROCEDURE GetFldrTitle(folder: WindowPtr; VAR title: Str255);` | Copies the title string of `folder` into `title`. |
| `GetWindInfo` | `PROCEDURE GetWindInfo(window: WindowPtr; VAR info: WindowInfo);` | Copies `window`'s visibility, tab presence, and allowed user-action flags (`okMove`, `okGrow`, `okFront`, `okClose`, `okActivate`) into `info`. |
| `GiveControl` | `PROCEDURE GiveControl(event: EventRecord);` | Completes handling of a `folderDeactivate` event by unhighlighting the deactivating folder's tab, pushing a `folderActivate` event for the new folder/process to the head of the queue, lowering caller priority, and waking the new process. |
| `GiveWindow` | `PROCEDURE GiveWindow(window: WindowPtr; toProcess: ProcessId);` | Discards any cached refresh picture for `window` and reassigns ownership of `window` to process `toProcess`. |
| `HeDied` | `PROCEDURE HeDied(deadProcess: ProcessID);` | Cleans up Window Manager state when `deadProcess` terminates by flushing its events and transferring active folder control back to the Filer if `deadProcess` was active. |
| `HideFolder` | `PROCEDURE HideFolder(folder: WindowPtr);` | Makes `folder` invisible on the desktop and redraws any windows newly exposed behind it. |
| `HiLiteTab` | `PROCEDURE HiLiteTab(folder: WindowPtr; fHiLite: BOOLEAN);` | Highlights (`fHiLite = TRUE`) or unhighlights (`fHiLite = FALSE`) the title tab of `folder`. |
| `ImDying` | `PROCEDURE ImDying;` | Notifies the Window Manager from a process's termination exception handler that the calling process is terminating (`HeDied(My_ID)`). |
| `InitWM` | `PROCEDURE InitWM;` | Performs one-time boot initialization of the shared `WMDATA` segment, `wmHeap`, and system windows (`menuFolder`, `alertFolder`, `dialogFolder`, `filerFolder`, `scrapFolder`), called by the Filer. |
| `InvalidateRgn` | `PROCEDURE InvalidateRgn(folder: WindowPtr; rgn: RgnHandle);` | Adds region `rgn` (in `folder`'s local coordinates) to `folder`'s `updateRgn` so it will be redrawn (compatibility wrapper around `InvalRgn`). |
| `InvalRect` | `PROCEDURE InvalRect(badRect: Rect);` | Adds rectangle `badRect` (in local coordinates of `thePort`) to the current window's `updateRgn` to schedule an update event. |
| `InvalRgn` | `PROCEDURE InvalRgn(badRgn: RgnHandle);` | Adds region `badRgn` (in local coordinates of `thePort`) to the current window's `updateRgn` to schedule an update event. |
| `LocateDialog` | `PROCEDURE LocateDialog(top, height: integer);` | Positions the system `dialogFolder` at vertical coordinate `top` (clamped on screen) with height `height`, showing it when `height > 0` or hiding it otherwise. |
| `MakeFldrActive` | `PROCEDURE MakeFldrActive(folder: WindowPtr; reasonWhy: LongInt);` | Initiates activation of `folder` with cause code `reasonWhy` and brings `folder` to the front of the desktop window list. |
| `MakeTopActive` | `PROCEDURE MakeTopActive;` | Activates the frontmost visible desktop document folder that permits activation. |
| `MoveFolder` | `PROCEDURE MoveFolder(folder: WindowPtr; hGlobal, vGlobal: INTEGER);` | Moves the top-left corner of `folder`'s content rectangle to global screen coordinates `(hGlobal, vGlobal)` without resizing it. |
| `NewFolder` | `FUNCTION NewFolder(folderRect: Rect; title: Str255; visible: BOOLEAN; behind: WindowPtr; refCon: LongInt; process: ProcessId; whichIcon: INTEGER; overlay: INTEGER): WindowPtr;` | Creates a new desktop folder window with bounds `folderRect`, tab `title`, visibility, Z-order (`behind`), `refCon`, owning `process`, close icon (`whichIcon`), and tool `overlay`, returning its `WindowPtr`. |
| `OpenWM` | `PROCEDURE OpenWM;` | Maps the shared Font Manager and Window Manager (`WMDATA`) data segments into the calling application process's address space. |
| `SetFldrTitle` | `PROCEDURE SetFldrTitle(folder: WindowPtr; title: Str255);` | Sets `folder`'s tab title to `title` and redraws the title tab if visible. |
| `SetFldrRefCon` | `PROCEDURE SetFldrRefCon(folder: WindowPtr; data: LongInt);` | Sets the 32-bit application reference constant (`refCon`) stored in `folder` to `data`. |
| `SetWindInfo` | `PROCEDURE SetWindInfo(window: WindowPtr; VAR info: WindowInfo);` | Updates `window`'s manipulation permission flags, tab presence, and visibility from `info`, showing or hiding the folder if `visible` changed. |
| `ShowFolder` | `PROCEDURE ShowFolder(folder: WindowPtr);` | Makes `folder` visible at its current position in the window list and draws its frame and newly exposed regions. |
| `TakeControl` | `PROCEDURE TakeControl(event: EventRecord; keepMenus, keepDialog: BOOLEAN);` | Completes handling of a `folderActivate` event by discarding any cached refresh picture, highlighting `event.who`'s tab, marking it active, restoring the arrow cursor, and optionally clearing the menu bar and dialog folder. |
| `TakeWindow` | `PROCEDURE TakeWindow(window: WindowPtr);` | Discards any cached refresh picture for `window` and assigns ownership of `window` to the calling process (`My_ID`). |
| `ValidRect` | `PROCEDURE ValidRect(goodRect: Rect);` | Subtracts rectangle `goodRect` (in local coordinates of `thePort`) from the current window's `updateRgn` to prevent unnecessary redrawing. |
| `ValidRgn` | `PROCEDURE ValidRgn(goodRgn: RgnHandle);` | Subtracts region `goodRgn` (in local coordinates of `thePort`) from the current window's `updateRgn` to prevent unnecessary redrawing. |
| `WMClosePicture` | `PROCEDURE WMClosePicture;` | Closes the automatic window refresh `Picture` opened by `WMOpenPicture`, discarding it on overflow or restoring pen visibility if `window` was hidden. |
| `WMKillPicture` | `PROCEDURE WMKillPicture(window: WindowPtr);` | Disposes of any QuickDraw refresh `Picture` (`windowPic`) saved for `window` and resets its handle to `NIL`. |
| `WMKillProcess` | `PROCEDURE WMKillProcess(process: ProcessID);` | Flushes all queued events for `process` and disposes of all non-system folder windows owned by `process`. |
| `WMOpenPicture` | `PROCEDURE WMOpenPicture(window: WindowPtr);` | Starts recording a QuickDraw refresh `Picture` (`windowPic`) for `window` in `wmHeap`, or hides the pen if `window` is invisible. |
| `WMStartDoc` | `PROCEDURE WMStartDoc(window: WindoWPtr);` | Highlights `window`'s tab, triggers the busy cursor immediately, and sets `window` as the active input window while opening a document (unless an activate/deactivate event is already pending). |

---

## Unit FontMgr

Implements the shared Lisa Font Manager (`FontMgr`), managing the `FMDATA` font cache segment, `SYSTEM.FONTLIB` strike loading, device-specific font substitution heuristics, font locking, and character width and metric queries for screen and printer devices.

- **Import**: `USES {$U FontMgr.obj} FontMgr;`
- **Interface dependencies**: `UnitStd`, `UnitHz`, `SysCall`, `PSysCall`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `FMinit` | `PROCEDURE FMinit(VAR cError: TC);` | Performs one-time boot initialization of the Font Manager, creating the shared `FMDATA` heap segment, loading substitution heuristics, and indexing `SYSTEM.FONTLIB`. |
| `FMOpen` | `PROCEDURE FMOpen(VAR cError: TC);` | Opens and maps the shared Font Manager heap data segment (`FMDATA`, LDSN 16) into the calling process's address space. |
| `FMCloseLib` | `PROCEDURE FMCloseLib(VAR cError: TC);` | Closes the OS file reference (`cRefnumLib`) to the open system font library file. |
| `FMCacheSize` | `PROCEDURE FMCacheSize(lCacheSize: TL; VAR cError: TC);` | Grows or shrinks the shared Font Manager heap zone and `FMDATA` data segment toward `lCacheSize` bytes when the size difference exceeds 1000 bytes. |
| `FMAddFont` | `FUNCTION FMAddFont(str30: TStr30; modifier: TModifier; dev: TDev; VAR cError: TC): TFam;` | Registers user font file `str30` with style `modifier` and device `dev` in a free slot of the Font Manager heuristic table, returning its assigned `TFam` family ID. |
| `FMDelfont` | `PROCEDURE FMDelfont(lfntid: TLfntid);` | Removes a user-registered font (`lfntid`) from the Font Manager heuristic table and frees its named object entry in the font cache. |
| `FMSwapFont` | `FUNCTION FMSwapFont(VAR lfntid: TLfntid; VAR cError: TC): TPcharstyle;` | Maps `lfntid`, swaps its font strike bitmap and character width table into the Font Manager heap if needed, and returns a pointer to its `TCharStyle` record. |
| `FMLockFont` | `PROCEDURE FMLockFont(VAR lfntid: TLfntid; flock: TF; VAR cError: TC);` | Swaps the font designated by `lfntid` into the Font Manager heap and locks (`flock = TRUE`) or unlocks (`flock = FALSE`) its named object in memory. |
| `FMFontMetrics` | `FUNCTION FMFontMetrics(VAR lfntid: TLfntid; VAR finfo: TFinfo; VAR cError: TC): TF;` | Retrieves the `FontInfo` vertical and horizontal metrics (`ascent`, `descent`, `widMax`, `leading`) for `lfntid`, returning `TRUE` on success and any error or substitution code in `cError`. |
| `FMFontWidths` | `FUNCTION FMFontWidths(VAR lfntid: TLfntid; VAR hmpccwid: THmpccwid; VAR dExtra: TB; VAR cError: TC): TF;` | Retrieves a handle to the 256-byte character width array (`hmpccwid`) and extra style width (`dExtra`) for `lfntid`, returning `TRUE` on success. |
| `FMMapFont` | `PROCEDURE FMMapFont(VAR lfntid: TLfntid; VAR cError: TC);` | Maps `lfntid` in place to a font family and style supported on its specified output device, setting `cError` to `substitution` (`-3024`) if a fallback mapping was required. |

---

## Unit GrafUtil

Provides QuickDraw utility routines for 32-bit bitwise logic and shifting, big-endian bit-array testing and manipulation, 32x32-to-64-bit signed multiplication, and 16.16 `Fixed`-point arithmetic.

- **Import**: `USES {$U GrafUtil.obj} GrafUtil;`
- **Interface dependencies**: `QuickDraw`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `BitAnd` | `FUNCTION BitAnd(long1, long2: LongInt): LongInt;` | Returns the 32-bit bitwise logical AND of `long1` and `long2`. |
| `BitOr` | `FUNCTION BitOr(long1, long2: LongInt): LongInt;` | Returns the 32-bit bitwise logical inclusive OR of `long1` and `long2`. |
| `BitXor` | `FUNCTION BitXor(long1, long2: LongInt): LongInt;` | Returns the 32-bit bitwise logical exclusive OR (XOR) of `long1` and `long2`. |
| `BitNot` | `FUNCTION BitNot(long: LongInt): LongInt;` | Returns the 32-bit bitwise one's complement (logical NOT) of `long`. |
| `BitShift` | `FUNCTION BitShift(long: LongInt; count: INTEGER): LongInt;` | Logically shifts `long` left by `count` bits when `count > 0` or right by `\|count\|` bits when `count < 0`, zero-filling vacated bits. |
| `BitTst` | `FUNCTION BitTst(bytePtr: QDPtr; bitNum: LongInt): BOOLEAN;` | Tests bit `bitNum` offset from `bytePtr` (numbered big-endian from the high-order bit of `bytePtr^`) and returns `TRUE` if the bit is 1. |
| `BitSet` | `PROCEDURE BitSet(bytePtr: QDPtr; bitNum: LongInt);` | Sets bit `bitNum` offset from `bytePtr` (numbered big-endian from the high-order bit of `bytePtr^`) to 1. |
| `BitClr` | `PROCEDURE BitClr(bytePtr: QDPtr; bitNum: LongInt);` | Clears bit `bitNum` offset from `bytePtr` (numbered big-endian from the high-order bit of `bytePtr^`) to 0. |
| `LongMul` | `PROCEDURE LongMul(a, b: LongInt; VAR dst: Int64Bit);` | Multiplies signed 32-bit integers `a` and `b` and stores the signed 64-bit product in `dst`. |
| `FixMul` | `FUNCTION FixMul(a, b: Fixed): Fixed;` | Multiplies two 16.16 `Fixed`-point numbers `a` and `b` and returns their rounded 16.16 `Fixed` product. |
| `FixRatio` | `FUNCTION FixRatio(numer, denom: INTEGER): Fixed;` | Divides 16-bit integer `numer` by `denom` and returns the quotient as a 16.16 `Fixed`-point value. |
| `HiWord` | `FUNCTION HiWord(x: Fixed): INTEGER;` | Returns the high-order 16-bit word (integer part) of 32-bit `Fixed` value `x`. |
| `LoWord` | `FUNCTION LoWord(x: Fixed): INTEGER;` | Returns the low-order 16-bit word (fractional part) of 32-bit `Fixed` value `x`. |
| `FixRound` | `FUNCTION FixRound(x: Fixed): INTEGER;` | Rounds 16.16 `Fixed`-point number `x` to the nearest 16-bit integer. |

---

## Unit HWInt

Provides the low-level Lisa Hardware Interface to 6522 VIAs, COPS keyboard/mouse controller, level 1/2 disk and vertical-retrace interrupts, hardware cursor and busy cursor, primary/alternate screen buffers, display contrast and power control, speaker tone generation, keyboard maps/queues, timers/alarms, and the hardware clock/calendar.

- **Import**: `USES {$U HWInt.obj} HWInt;`
- **Unit kind**: `INTRINSIC` (`HWINT`)

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `DriverInit` | `Procedure DriverInit;` | Initializes Hardware Interface data areas, 6522 VIAs, and level 1 and level 2 interrupt vectors at boot time, identifying the installed I/O board version. |
| `DiskDriver` | `Procedure DiskDriver(routine: LogicalAddress);` | Installs the interrupt handler at `routine` for parallel-port hard disk level 1 interrupts. |
| `TwiggyDriver` | `Procedure TwiggyDriver(routine: LogicalAddress);` | Installs the interrupt handler at `routine` for built-in Twiggy (or micro-floppy) drive level 1 interrupts. |
| `DiskSync` | `Procedure DiskSync(busy: Boolean);` | Synchronizes access to the shared parallel-port VIA between disk/printer drivers and screen contrast routines (`busy = TRUE` before port use, `FALSE` after). |
| `NMISync` | `Procedure NMISync;` | Resynchronizes COPS keyboard/mouse controller input and output transfers that were interrupted by a non-maskable interrupt (NMI). |
| `COPSSync` | `Procedure COPSSync;` | Aborts any partial multi-byte COPS packet and resets pollable key states to up after external diagnostic code borrows the level 2 COPS interrupt vector. |
| `Poll` | `Procedure Poll;` | Polls hardware registers for pending COPS, vertical retrace, and timer interrupts while running with CPU interrupts disabled. |
| `MouseLocation` | `Procedure MouseLocation(var x: Pixels; var y: Pixels);` | Returns the current mouse coordinates in screen pixels (`x` in `0..719`, `y` in `0..363`). |
| `MouseUpdates` | `Procedure MouseUpdates(delay: MilliSeconds);` | Sets the approximate interval in milliseconds (`0..28` ms in 4 ms increments) between updates to the software mouse location. |
| `MouseScaling` | `Procedure MouseScaling(scale: Boolean);` | Enables (`scale = TRUE`) or disables (`scale = FALSE`) fine/coarse speed scaling and 3:2 horizontal aspect compensation for mouse movement. |
| `MouseThresh` | `Procedure MouseThresh(threshold: Pixels);` | Sets the per-update pixel-movement sum `threshold` (`0..256`) that separates fine and coarse scaled mouse motion. |
| `MouseOdometer` | `Function MouseOdometer: ManyPixels;` | Returns the cumulative sum of unscaled horizontal and vertical mouse motion in pixels since system boot. |
| `CursorLocation` | `Procedure CursorLocation(x: Pixels; y: Pixels);` | Sets the screen pixel position `(x, y)` of the cursor hotspot when automatic mouse tracking is disabled. |
| `CursorTracking` | `Procedure CursorTracking(track: Boolean);` | Enables (`track = TRUE`) or disables (`track = FALSE`) automatic cursor tracking of mouse movement, snapping the mouse coordinates to the cursor when enabled. |
| `CursorImage` | `Procedure CursorImage(hotX: Pixels; hotY: Pixels; height: CursorHeight; data: CursorPtr; mask: CursorPtr);` | Sets the primary cursor's hotspot `(hotX, hotY)`, pixel `height` (`0..32`), 16-pixel-wide `data` bitmap, and `mask` bitmap. |
| `CursorHide` | `Procedure CursorHide;` | Removes the cursor from the screen and increments the nested hide depth counter (must be balanced by `CursorDisplay`). |
| `CursorShield` | `Procedure CursorShield(left: Pixels; top: Pixels; right: Pixels; bottom: Pixels);` | Removes the cursor from the screen if its image intersects rectangle `(left, top, right, bottom)`, incrementing the hide counter for a matching `CursorDisplay`. |
| `CursorDisplay` | `Procedure CursorDisplay;` | Decrements the nested cursor hide/shield counter and redisplays the cursor when the count returns to zero. |
| `CursorObscure` | `Procedure CursorObscure;` | Temporarily removes the cursor from the screen until the next cursor or tracked mouse movement. |
| `CursorInit` | `Procedure CursorInit;` | Unconditionally clears all prior hide, shield, obscure, and busy-cursor states and immediately displays the normal cursor. |
| `CursorReInit` | `Procedure CursorReInit;` | Clears all prior cursor hide, shield, and obscure counts and redisplays the cursor while preserving the current busy-cursor status. |
| `BusyImage` | `Procedure BusyImage(hotX: Pixels; hotY: Pixels; height: CursorHeight; data: CursorPtr; mask: CursorPtr);` | Sets the busy cursor's hotspot `(hotX, hotY)`, pixel `height` (`0..32`), 16-pixel-wide `data` bitmap, and `mask` bitmap. |
| `BusyDelay` | `Procedure BusyDelay(delay: MilliSeconds);` | Displays the normal cursor now and schedules the busy cursor to appear automatically if `BusyDelay` is not called again within `delay` milliseconds. |
| `FrameCounter` | `Function FrameCounter: Frames;` | Returns the unsigned 32-bit vertical retrace frame counter incremented at approximately 60 Hz since boot. |
| `ScreenSize` | `Procedure ScreenSize(var x: Pixels; var y: Pixels);` | Returns the horizontal (`x`, 720) and vertical (`y`, 364) pixel dimensions of the Lisa display. |
| `ScreenAddr` | `Function ScreenAddr: LogicalAddress;` | Returns the logical memory base address of the primary (graphics) display frame buffer. |
| `AltScreenAddr` | `Function AltScreenAddr: LogicalAddress;` | Returns the logical memory base address of the alternate (debugging) display frame buffer. |
| `ScreenKeybd` | `Function ScreenKeybd: VisibleScreen;` | Returns which display screen and matching keyboard queue (`0` = primary, `1` = alternate) is currently visible and active. |
| `SetScreenKeybd` | `Procedure SetScreenKeybd(screen: VisibleScreen);` | Selects the visible display screen and active keyboard input queue (`0` = primary, `1` = alternate). |
| `Contrast` | `Function Contrast: ScreenContrast;` | Returns the current display contrast setting (`0` = maximum contrast to `255` = minimum contrast). |
| `SetContrast` | `Procedure SetContrast(contrast: ScreenContrast);` | Immediately sets the hardware display contrast level to `contrast` (`0..255`). |
| `RampContrast` | `Procedure RampContrast(contrast: ScreenContrast);` | Gradually ramps the display contrast level to `contrast` (`0..255`) over approximately one second via interrupt-driven steps. |
| `DimContrast` | `Function DimContrast: ScreenContrast;` | Returns the contrast setting (`0..255`) used when the screen automatically dims during user inactivity. |
| `SetDimContrast` | `Procedure SetDimContrast(contrast: ScreenContrast);` | Sets the contrast level (`contrast`, `0..255`) to which the screen dims after the inactivity fade delay. |
| `FadeDelay` | `Function FadeDelay: MilliSeconds;` | Returns the approximate inactivity period in milliseconds before the display automatically dims to `DimContrast`. |
| `SetFadeDelay` | `Procedure SetFadeDelay(delay: MilliSeconds);` | Sets the approximate user-inactivity delay in milliseconds before automatic screen dimming and brightens the screen if dimmed. |
| `PowerDown` | `Procedure PowerDown;` | Commands the Lisa power-control hardware to turn off main machine power while maintaining the battery-backed clock/calendar. |
| `PowerCycle` | `Procedure PowerCycle(delay: Seconds);` | Powers off the machine and programs the hardware clock/calendar to automatically reboot after `delay` seconds. |
| `Volume` | `Function Volume: SpeakerVolume;` | Returns the current hardware speaker volume setting (`0` = softest to `7` = loudest). |
| `SetVolume` | `Procedure SetVolume(volume: SpeakerVolume);` | Sets the hardware speaker volume level to `volume` (`0..7`). |
| `Noise` | `Procedure Noise(waveLength: MicroSeconds);` | Starts continuous square-wave audio output from the speaker with period `waveLength` microseconds (`8..8191`) until `Silence` or `Beep` is called. |
| `Silence` | `Procedure Silence;` | Stops any tone currently sounding on the Lisa speaker. |
| `Beep` | `Procedure Beep(waveLength: MicroSeconds; duration: MilliSeconds);` | Produces a square-wave tone of period `waveLength` microseconds from the speaker for `duration` milliseconds. |
| `Keyboard` | `Function Keyboard: KeybdId;` | Returns the hardware identification byte (manufacturer, physical layout, and keycap legends) of the attached physical keyboard. |
| `Legends` | `Function Legends: KeybdId;` | Returns the currently active keyboard layout/legends code used to decode keystrokes. |
| `SetLegends` | `Procedure SetLegends(id: KeybdId);` | Sets the software keyboard decoding map to match keyboard layout/legends code `id` until changed again or a keyboard is plugged in. |
| `KeyIsDown` | `Function KeyIsDown(key: KeyCap): Boolean;` | Polls the hardware key state map and returns `TRUE` if physical keycode `key` (`0..127`) is currently down. |
| `KeyMap` | `Procedure KeyMap(var keys: KeyCapSet);` | Returns the instantaneous 128-bit hardware key state bitmap (one bit per pollable keycode) in `keys`. |
| `KeybdPeek` | `Function KeybdPeek(repeats: Boolean; index: KeybdQIndex; var event: KeyEvent): Boolean;` | Inspects entry `index` (`1, 2, ...`) in the primary keyboard event queue without removing it (generating repeats if `repeats` is `TRUE`), returning `TRUE` if copied into `event`. |
| `AltKeyPeek` | `Function AltKeyPeek(repeats: Boolean; index: KeybdQIndex; var event: KeyEvent): Boolean;` | Inspects entry `index` (`1, 2, ...`) in the alternate keyboard event queue without removing it (generating repeats if `repeats` is `TRUE`), returning `TRUE` if copied into `event`. |
| `KeybdEvent` | `Function KeybdEvent(repeats: Boolean; wait: Boolean; var event: KeyEvent): Boolean;` | Dequeues the next `KeyEvent` from the primary keyboard queue (optionally synthesizing repeats when `repeats` is `TRUE` and waiting when `wait` is `TRUE`), returning `TRUE` if an event was returned. |
| `AltKeyEvent` | `Function AltKeyEvent(repeats: Boolean; wait: Boolean; var event: KeyEvent): Boolean;` | Dequeues the next `KeyEvent` from the alternate keyboard queue (with optional auto-repeats and blocking wait), returning `TRUE` if an event was returned. |
| `RepeatRate` | `Procedure RepeatRate(var initial: MilliSeconds; var subsequent: MilliSeconds);` | Returns the current `initial` auto-repeat delay and `subsequent` repeat interval for held keys, both in milliseconds. |
| `SetRepeatRate` | `Procedure SetRepeatRate(initial: MilliSeconds; subsequent: MilliSeconds);` | Sets the `initial` auto-repeat delay and `subsequent` repeat interval for held keys, both in milliseconds. |
| `KeyPushed` | `Procedure KeyPushed(key: KeyCap);` | Notifies the keyboard driver that hardware pseudo-key `key` (disk inserted, disk eject button, or power button) was actuated. |
| `NMIKey` | `Function NMIKey: KeyCap;` | Returns the physical keycode (`0` if none) currently programmed to generate a non-maskable interrupt (NMI). |
| `SetNMIKey` | `Procedure SetNMIKey(key: KeyCap);` | Programs physical keycode `key` (`0` to disable) to generate a non-maskable interrupt (NMI) instead of a normal key event. |
| `ToggleKey` | `Function ToggleKey: KeyCap;` | Returns the physical keycode (`0` if none) currently assigned to toggle between primary and alternate screens/keyboards with Option. |
| `SetToggleKey` | `Procedure SetToggleKey(key: KeyCap);` | Assigns physical keycode `key` (`0` to disable) as the `<Option-Toggle>` shortcut for switching between the primary and alternate screen/keyboard. |
| `KeyToAscii` | `Function KeyToAscii(key: KeyCap; State: Integer): Ascii;` | Translates physical keycode `key` and modifier `State` (Option, Shift, and Caps Lock bits) into its corresponding ASCII character under the active keyboard legends. |
| `MicroTimer` | `Function MicroTimer: MicroSeconds;` | Returns the current 32-bit free-running microsecond timer value (2-microsecond resolution) elapsed since boot. |
| `Timer` | `Function Timer: MilliSeconds;` | Returns the current 32-bit free-running millisecond timer value elapsed since boot. |
| `AlarmAssign` | `Procedure AlarmAssign(var alarm: AlarmNumber; routine: LogicalAddress);` | Allocates one of the 20 millisecond-timer alarms, binds interrupt handler `routine` to it, and returns its `AlarmNumber` in `alarm` (`0` if all are in use). |
| `AlarmReturn` | `Procedure AlarmReturn(alarm: AlarmNumber);` | Frees millisecond-timer `alarm` so it can be reassigned to another caller. |
| `AlarmAbsolute` | `Procedure AlarmAbsolute(alarm: AlarmNumber; time: MilliSeconds);` | Schedules `alarm` to invoke its associated interrupt callback when the hardware millisecond `Timer` reaches `time`. |
| `AlarmRelative` | `Procedure AlarmRelative(alarm: AlarmNumber; delay: MilliSeconds);` | Schedules `alarm` to invoke its associated interrupt callback `delay` milliseconds after the current time. |
| `AlarmOff` | `Procedure AlarmOff(alarm: AlarmNumber);` | Disables any pending trigger on `alarm` without deallocating the alarm number. |
| `DateTime` | `Procedure DateTime(var date: DateArray);` | Reads the current year (`1980..1995`), day-of-year (`1..366`), hour, minute, and second from the hardware clock/calendar into `date`. |
| `SetDateTime` | `Procedure SetDateTime(date: DateArray);` | Sets the hardware clock/calendar and system timestamp from the year, day-of-year, hour, minute, and second values in `date`. |
| `DateToTime` | `Procedure DateToTime(date: DateArray; var time: Seconds);` | Converts `date` (`DateArray` for years `1901..2030`) into unsigned seconds elapsed since midnight January 1, 1901 in `time`. |
| `TimeStamp` | `Function TimeStamp: Seconds;` | Returns the current hardware clock/calendar time as unsigned seconds elapsed since midnight January 1, 1901. |
| `SetTimeStamp` | `Procedure SetTimeStamp(time: Seconds);` | Sets the hardware clock/calendar and system date/time from `time` (unsigned seconds since midnight January 1, 1901, within `1980..1995`). |
| `TimeToDate` | `Procedure TimeToDate(time: Seconds; var date: DateArray);` | Converts `time` (unsigned seconds since midnight January 1, 1901) into year, day-of-year, hour, minute, and second fields in `date`. |

---

## Unit International

Provides locale-aware international character and string processing for European and US markets, including accented uppercase/lowercase shifting, multi-strength character/string identity matching, and two-pass lexicographic magnitude comparison with ligature expansion.

- **Import**: `USES {$U International.obj} International;`
- **Unit kind**: `INTRINSIC` (`INTERNAT`)
- **Interface dependencies**: `UnitStd`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `InitInternational` | `PROCEDURE InitInternational(VAR errnum: INTEGER);` | Initializes the `International` text-processing unit and sets `errnum` to `0`. |
| `UpStrShift` | `PROCEDURE UpStrShift(sP: CompStrP);` | Shifts all lowercase letters (including accented international characters) in Pascal string `sP^` to uppercase in place. |
| `UpChrShift` | `PROCEDURE UpChrShift(pc: CompChrP; length: INTEGER);` | Shifts `length` characters starting at `pc` to uppercase in place using the international upshift table. |
| `DownStrShift` | `PROCEDURE DownStrShift(sP: CompStrP);` | Shifts all uppercase letters (including accented international characters) in Pascal string `sP^` to lowercase in place. |
| `DownChrShift` | `PROCEDURE DownChrShift(pc: CompChrP; length: INTEGER);` | Shifts `length` characters starting at `pc` to lowercase in place using the international downshift table. |
| `CompStrMagnitude` | `FUNCTION CompStrMagnitude(string1, string2: CompStrP; veryWeak: BOOLEAN): INTEGER;` | Performs a two-pass international lexicographic comparison of Pascal strings `string1^` and `string2^` (expanding ligatures and returning `0` early on `CompVeryWeak` equality when `veryWeak` is `TRUE`), returning `-1`, `0`, or `1`. |
| `CompChrMagnitude` | `FUNCTION CompChrMagnitude(char1, char2: CompChrP; length1, length2: INTEGER; veryWeak: BOOLEAN): INTEGER;` | Performs a two-pass international lexicographic comparison of character buffers `char1` (`length1`) and `char2` (`length2`) with ligature expansion, returning `-1`, `0`, or `1`. |
| `CompareChar` | `FUNCTION CompareChar(ch1, ch2: CHAR; kind: KindOfCompare): BOOLEAN;` | Returns `TRUE` if `ch1` and `ch2` are equivalent under comparison strength `kind` (`CompAbsolute` exact, `CompStrong` case-insensitive, `CompWeak` shared accent/family, or `CompVeryWeak` base character family). |
| `CharsMatching` | `PROCEDURE CharsMatching(ch: CHAR; kind: KindOfCompare; matchingChars: CompChrP; VAR nOfMatchigChars: INTEGER);` | Finds all character codes (`0..255`) equivalent to `ch` under comparison strength `kind`, storing them in `matchingChars` and their count in `nOfMatchigChars` (`0` if `MaximumCharsMatching` is reached). |
| `CompStrIdentity` | `FUNCTION CompStrIdentity(string1, string2: CompStrP; kind: KindOfCompare): BOOLEAN;` | Returns `TRUE` if Pascal strings `string1^` and `string2^` have the same length and matching characters under comparison strength `kind`. |
| `CompChrIdentity` | `FUNCTION CompChrIdentity(char1, char2: CompChrP; length1, length2: INTEGER; kind: KindOfCompare): BOOLEAN;` | Returns `TRUE` if character arrays `char1` (`length1`) and `char2` (`length2`) have equal length and matching characters under comparison strength `kind`. |

---

## Unit Menus

Implements the Lisa Menu Manager (`Menus` shared intrinsic) for building, reading, inserting, enabling/disabling, marking, rendering, and tracking pull-down menus and Command-key shortcuts in the desktop menu bar.

- **Import**: `USES {$U Menus.obj} Menus;`
- **Unit kind**: `INTRINSIC SHARED` (`MENUS`)
- **Interface dependencies**: `HWInt`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `SysCall`, `Events`, `Windows`, `Folders`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `CalcMenuSize` | `PROCEDURE CalcMenuSize(VAR menu: MenuInfo);` | Scans the item strings and Command-key shortcuts in `menu.menuData` to compute and update `menu.menuWidth` and `menu.menuHeight`. |
| `CheckItem` | `PROCEDURE CheckItem(VAR menu: MenuInfo; item: INTEGER; checked: BOOLEAN);` | Places (`checked = TRUE`) or clears (`checked = FALSE`) a checkmark symbol next to 1-based item `item` in `menu`. |
| `ChooseTxtItem` | `PROCEDURE ChooseTxtItem(VAR menu: MenuInfo; menuRect: Rect; hitPt: Point; VAR whichItem: INTEGER);` | Standard menu selection callback (`ChooseProc`) that hit-tests `hitPt` against enabled items in `menuRect`, updates item inversion highlighting, and returns the chosen 1-based index in `whichItem` (`0` if none). |
| `ClearMenuBar` | `PROCEDURE ClearMenuBar;` | Removes all application menus from the menu bar (leaving only the permanent Filer desktop menu slot) and redraws the menu bar. |
| `DeleteMenu` | `PROCEDURE DeleteMenu(menuId: INTEGER);` | Removes the menu identified by `menuId` from the menu bar list and shifts the horizontal positions of subsequent menus left. |
| `DisableItem` | `PROCEDURE DisableItem(VAR menu: MenuInfo; item: INTEGER);` | Disables 1-based item `item` in `menu` so it is drawn dimmed and cannot be chosen. |
| `DisableMenu` | `PROCEDURE DisableMenu(VAR menu: MenuInfo);` | Disables `menu` as a whole (`enableFlags[0] := FALSE`) so its menu bar title and all items appear dimmed and cannot be chosen. |
| `DrawMenuBar` | `PROCEDURE DrawMenuBar;` | Erases and redraws the menu bar and all installed menu titles (dimming disabled menus) when the calling process is active. |
| `DrawTxtMenu` | `PROCEDURE DrawTxtMenu(VAR menu: MenuInfo; menuRect: Rect);` | Standard menu rendering callback (`DrawProc`) that draws item strings, separator lines, marks, icons, character styles, Command-key shortcuts, and disabled dimming for `menu` within `menuRect`. |
| `EnableItem` | `PROCEDURE EnableItem(VAR menu: MenuInfo; item: INTEGER);` | Enables 1-based item `item` in `menu` so it appears normal and can be selected by the user. |
| `EnableMenu` | `PROCEDURE EnableMenu(VAR menu: MenuInfo);` | Enables `menu` as a whole (`enableFlags[0] := TRUE`) so its title and enabled items can be selected. |
| `GetItem` | `PROCEDURE GetItem(VAR menu: MenuInfo; item: INTEGER; itemString: ItemPtr);` | Copies the text of 1-based item `item` in `menu` into `itemString^` (or sets `itemString^` to empty if out of range). |
| `HiLiteMenu` | `PROCEDURE HiLiteMenu(menuId: INTEGER);` | Inverts the menu bar title of `menuId` while unhighlighting any previously highlighted menu title, or clears all title highlighting when `menuId = 0`. |
| `InitMenus` | `PROCEDURE InitMenus;` | Performs one-time initialization of the Menu Manager (configuring the permanent desktop menu slot and clearing the menu bar), called at boot by the Filer. |
| `InsertMenu` | `PROCEDURE InsertMenu(VAR menu: MenuInfo; beforeId: INTEGER);` | Inserts `menu` into the menu bar immediately before the menu with ID `beforeId`, or appends it at the right end if `beforeId` is not present. |
| `MarkItem` | `PROCEDURE MarkItem(VAR menu: MenuInfo; item: INTEGER; whichMark: INTEGER);` | Sets the left-margin mark character of 1-based `item` in `menu` to `CHR(whichMark)` (such as `noMark`, `checkMark`, or `appleMark`). |
| `MenuSelect` | `PROCEDURE MenuSelect(startPt: Point; VAR whichMenu, whichItem: INTEGER);` | Tracks mouse dragging from `startPt` across the menu bar and pull-down menus until button release, returning the selected `whichMenu` ID and `whichItem` index (`0` if none). |
| `MenuKey` | `PROCEDURE MenuKey(ch: CHAR; VAR whichMenu, whichItem: INTEGER);` | Searches the current menu bar for an enabled item matching Command-key character `ch`, returning its `whichMenu` ID and `whichItem` index (or `0, 0` if not found or disabled). |
| `ReadMenu` | `PROCEDURE ReadMenu(VAR menuFile: TEXT; VAR menu: MenuInfo);` | Reads a text menu specification (ID, title, items, `/key` shortcuts, and `\style` codes) from `menuFile`, allocates `menu.menuData` on `theHeap`, and calculates the menu's dimensions. |
| `SetItem` | `PROCEDURE SetItem(VAR menu: MenuInfo; item: INTEGER; itemString: ItemPtr);` | Replaces the text of 1-based `item` in `menu` with `itemString^` (preserving its shortcut, mark, and style bytes), reallocates `menu.menuData`, and recalculates the menu's size. |

---

## Unit PMDecl

Declares constants and record types for the Parameter Memory Manager (`PMM`) and configurable device descriptors (`SYSTEM.CDD`), including `TNibble`, `TBootStuff`, `TOutPutStuff`, `TInputStuff`, `TInternalStuff`, `TypeConnect`, `Ch_info`, `cddEntry`, `cddHeader`, and `systemCdd`.

- **Import**: `USES {$U PMDecl.obj} PMDecl;`
- **Unit kind**: `INTRINSIC` (`PMDECL`)
- **Interface dependencies**: `SysCall`

*This unit exports constants, data types, and/or global variables only (no callable procedures or functions).*

---

## Unit PMM

Implements the shared Parameter Memory Manager (`PMM`) for reading, updating, defaulting, and persisting non-volatile Lisa configuration settings (boot volume, screen contrast, fade delay, beep volume, key repeat/double-click rates, mouse scaling, and attached device records) and applying them to hardware drivers.

- **Import**: `USES {$U PMM.obj} PMM;`
- **Unit kind**: `INTRINSIC SHARED` (`PMM`)
- **Interface dependencies**: `HWInt`, `SysCall`, `UnitStd`, `PMDecl`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `PmInit` | `Procedure PmInit(var error: integer);` | Reads non-volatile Parameter Memory via the OS (resetting to defaults and writing back if both Parameter Memory and disk snapshot are corrupt, error `-622`) and initializes `PMBeep_Flash`. |
| `PMReadConfig` | `Procedure PMReadConfig(var error: integer; var NextEntry: longint; var Config: ConfigDev);` | Reads the next device configuration entry (`Config`) from the cached Parameter Memory image, advancing `NextEntry`. |
| `PMWriteConfig` | `Procedure PMWriteConfig(var error: integer; var NextEntry: longint; var Config: ConfigDev);` | Stores device configuration entry `Config` into the cached Parameter Memory image at `NextEntry` and advances `NextEntry`. |
| `PMReadInput` | `Procedure PMReadInput(Var InputInfo: TInputStuff);` | Copies the keyboard initial repeat, subsequent repeat, and mouse double-click nibble settings from cached Parameter Memory into `InputInfo`. |
| `PMWriteInput` | `Procedure PMWriteInput(InputInfo: TInputStuff);` | Updates keyboard repeat and double-click settings in cached Parameter Memory from `InputInfo` and applies the new key repeat rate to the hardware driver. |
| `PMReadOutPut` | `Procedure PMReadOutPut(Var OutputInfo: TOutputStuff);` | Copies normal contrast, dim contrast, beep volume, and screen fade-delay nibble settings from cached Parameter Memory into `OutputInfo`. |
| `PMWriteOutPut` | `Procedure PMWriteOutPut(OutputInfo: TOutputStuff);` | Updates screen contrast, dim contrast, beep volume, and fade-delay settings in cached Parameter Memory from `OutputInfo` and immediately applies them to `PMBeep_Flash` and hardware drivers. |
| `PMReadBoot` | `Procedure PMReadBoot(Var BootInfo: TBootStuff);` | Copies the extended-memory test flag and boot volume number from cached Parameter Memory into `BootInfo`. |
| `PMWriteBoot` | `Procedure PMWriteBoot(BootInfo: TBootStuff);` | Updates the extended-memory test flag and boot volume number in cached Parameter Memory from `BootInfo`. |
| `PMWrite` | `Procedure PMWrite;` | Writes the in-memory Parameter Memory record out to non-volatile Parameter Memory and the OS snapshot via `Write_PMem`. |
| `DimConvert` | `Function DimConvert(Contrast: Integer): Integer;` | Converts a `0..16` Parameter Memory dim-contrast nibble into a hardware `ScreenContrast` byte value (`(Contrast + 5) * 5 + 90`) suitable for `SetDimContrast`. |
| `ConvertCont` | `Function ConvertCont(Contrast: Integer): Integer;` | Converts a `0..16` Parameter Memory normal-contrast nibble into a hardware `ScreenContrast` byte value (`Contrast * 5 + 90`) suitable for `SetContrast`. |
| `PMReadDevolp` | `Procedure PMReadDevolp(Var IntrnlInfo: TInternalStuff);` | Copies internal development settings (`MouseOn`, `Mem_Loss`, and `ScaleMouse`) from cached Parameter Memory into `IntrnlInfo`. |
| `PMWriteDevolp` | `Procedure PMWriteDevolp(IntrnlInfo: TInternalStuff);` | Updates internal development settings (`MouseOn`, `Mem_Loss`, and `ScaleMouse`) in cached Parameter Memory from `IntrnlInfo` and applies `MouseScaling` to the hardware driver. |
| `DefaultPM` | `Procedure DefaultPM;` | Resets all non-device-configuration fields in the in-memory Parameter Memory record (contrast, volume, fade delay, click/repeat timings, boot volume, and mouse flags) to factory defaults. |

---

## Unit PrBuf

Buffers and sorts text runs and horizontal or vertical rule commands within a QuickDraw print band for character and daisy-wheel printer drivers. Coalesces adjacent text and overlapping rules before invoking driver-supplied check, scan-line, and dump callbacks.

- **Import**: `USES {$U PrBuf.obj} PrBuf;`
- **Unit kind**: `INTRINSIC` (`PRBUF`)
- **Interface dependencies**: `SysCall`, `PMDecl`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `PrStdInfo`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `PbClose` | `PROCEDURE PbClose;` | Frees the dynamic character data buffer, command array, and state handle allocated for the current print buffer session. |
| `PbDumpBand` | `PROCEDURE PbDumpBand;` | Iterates over every scan line in the current port rectangle, invoking the installed scan-line callback and executing buffered text and rule dump callbacks sorted by coordinate before resetting the buffer. |
| `PbHRule` | `PROCEDURE PbHRule(cLength: TC);` | Clips a horizontal rule of signed pixel length cLength from the current pen location against the port clip region, coalescing or queuing a pbCmdHRule command and advancing pnLoc.h. |
| `PbOpen` | `PROCEDURE PbOpen(install: TPbInstall);` | Allocates and initializes the print command and text buffers on TheHeap and registers the caller's check, dump, and scan-line callbacks from install. |
| `PbText` | `PROCEDURE PbText(cCount: TC; p: TP);` | Clips cCount characters starting at pointer p against the port clip region, coalescing contiguous same-style characters into pbCmdText commands and advancing pnLoc.h by the text width. |
| `PbVRule` | `PROCEDURE PbVRule(cLength: TC);` | Clips a vertical rule of signed pixel length cLength from the current pen location against the port clip region, coalescing or queuing a pbCmdVRule command and advancing pnLoc.v. |

---

## Unit PrFile

Implements Print Shop spool-file recording for background printing, serializing `TPfHeader` job headers, `TPfPage` page directory tables, per-band QuickDraw pictures, and `PicComment`-encoded tabs and rules to disk.

- **Import**: `USES {$U PrFile.obj} PrFile;`
- **Unit kind**: `INTRINSIC` (`PRFILE`)
- **Interface dependencies**: `SysCall`, `PMDecl`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `PrStd`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `PfDocStart` | `PROCEDURE PfDocStart(prins: TPrins);` | Creates and opens a spool file for background print job `prins`, initializing the `TPfPage` page directory handle and writing the initial `TPfHeader` record. |
| `PfStartPage` | `PROCEDURE PfStartPage;` | Grows the spool-file page directory for a new page and records its starting byte offset in the open spool file. |
| `PfNextBand` | `PROCEDURE PfNextBand(rNextBand: Rect);` | Opens a QuickDraw `PicHandle` (`OpenPicture`) framed to `rNextBand` to capture drawing operations for the next spooled band. |
| `PfDumpBand` | `PROCEDURE PfDumpBand;` | Closes the current band `PicHandle`, writes its serialized QuickDraw picture data to the spool file, updates the page length, and disposes the picture. |
| `PfEndPage` | `PROCEDURE PfEndPage;` | Marks completion of band recording for the current page in the background spool file. |
| `PfDocEnd` | `PROCEDURE PfDocEnd;` | Trims trailing empty pages, writes the finalized page directory and `TPfHeader` to the spool file, closes the file, and submits it to the background spooler. |
| `PfOffsetPage` | `PROCEDURE PfOffsetPage(h, v: TC);` | Stores horizontal and vertical page offsets `(h, v)` in the current page's `TPfPage` directory entry in the spool file. |
| `PfTab` | `PROCEDURE PfTab(cLng: TC);` | Records a `pfPicTab` QuickDraw `PicComment` specifying a horizontal tab of `cLng` dots from the current pen location into the open spool picture. |
| `PfHRule` | `PROCEDURE PfHRule(cLng: TC);` | Records a `pfPicHRule` QuickDraw `PicComment` specifying a horizontal rule of `cLng` dots from the current pen location into the open spool picture. |
| `PfVRule` | `PROCEDURE PfVRule(cLng: TC);` | Records a `pfPicVRule` QuickDraw `PicComment` specifying a vertical rule of `cLng` dots from the current pen location into the open spool picture. |
| `PfCleanup` | `PROCEDURE PfCleanup;` | Closes and disposes any in-progress spool `PicHandle` and closes the open spool file when spooling is aborted. |

---

## Unit PrMgr

Implements core Print Manager initialization, shared data-segment binding, printer setup and job dialogs, alert presentation, and print record validation. Coordinates foreground applications with background printer processes via shared memory and event channels.

- **Import**: `USES {$U PrMgr.obj} PrMgr;`
- **Unit kind**: `INTRINSIC` (`PRMGR`)
- **Interface dependencies**: `UnitStd`, `SysCall`, `PMDecl`, `QuickDraw`, `Events`, `Windows`, `Folders`, `Menus`, `AlertMgr`, `PrStd`, `PrMgrUtil`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `FPrInsDlg` | `FUNCTION FPrInsDlg(VAR cError: TC; VAR prprf, prins: TPrRec; VAR fNewStl: TF): TF;` | Displays the 'Print...' job dialog for print record prprf with menu-suppression mode prmode, updating prprf and fNewStl and returning TRUE if the user confirmed OK. |
| `PrPrfDlg` | `PROCEDURE PrPrfDlg(VAR cError: TC; VAR prprf: TPrRec; VAR fNewStl: TF; fPgSzSuppress: TF);` | Displays the 'Format for Printer...' dialog (and printer selection dialog if needed) for print record prprf, optionally suppressing custom paper sizes when fPgSzSuppress is TRUE and setting fNewStl if formatting changed. |
| `PrArbDlg` | `PROCEDURE PrArbDlg(VAR cError: TC; VAR prprf: TPrRec; VAR fNewStl: TF);` | Displays the printer arbitration dialog to reconcile `prprf` with currently configured printers, returning any error in `cError` and setting `fNewStl` if formatting metrics changed. |
| `PrBgdDlg` | `PROCEDURE PrBgdDlg(VAR cError: TC; fDoIdle: TF);` | Requests the background print supervisor process to display the 'Monitor the Printer' status dialog. |
| `PrBgdIdle` | `PROCEDURE PrBgdIdle;` | Performs periodic idle processing for the Print Manager's background spooler status dialog and interprocess events. |
| `PrBgdErr` | `PROCEDURE PrBgdErr(cError: TC);` | Notifies the Print Manager of background printing error `cError` so the appropriate background printer alert can be displayed. |
| `PrBgdUpd` | `PROCEDURE PrBgdUpd;` | Redraws the Print Manager's background printing status dialog/folder in response to a window update event. |
| `PrAlertNone` | `PROCEDURE PrAlertNone;` | Displays the standard Print Manager alert informing the user that no printers are currently configured (`CPrAvail = 0`). |
| `PrCheckErr` | `PROCEDURE PrCheckErr(cError: TC);` | Evaluates Print Shop status code `cError` after a printing-loop call, presenting any required disk-full or printer alerts and handling recovery flow. |
| `PrErrMsg` | `PROCEDURE PrErrMsg(cError: TC);` | Displays the Print Manager alert dialog corresponding to printing error code `cError`. |

---

## Unit PrMgrUtil

Provides Print Manager utility routines in `Sys2Lib` for querying available printers, reading and converting Parameter Memory printer configuration records, comparing and modifying `TPrRec` preferences, building long font IDs, and dispatching Print Manager folder menu commands.

- **Import**: `USES {$U PrMgrUtil.obj} PrMgrUtil;`
- **Unit kind**: `INTRINSIC` (`PRMGRUTI`)
- **Interface dependencies**: `UnitStd`, `SysCall`, `PMDecl`, `PMM`, `QuickDraw`, `FontMgr`, `Menus`, `PrStd`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `FPrArbRqd` | `FUNCTION FPrArbRqd(VAR prprf: TPrRec): TF;` | Returns `TRUE` if print preference record `prprf` is invalid or conflicts with the currently configured printers and requires user arbitration via `PrArbDlg`. |
| `CPrAvail` | `FUNCTION CPrAvail: TC;` | Returns the number of printers currently configured and available in Parameter Memory / the Print Manager. |
| `PrDev` | `FUNCTION PrDev(VAR prprf: TPrRec): TDeviceType;` | Returns the QuickDraw/Font Manager `TDeviceType` identifier corresponding to the target printer configured in `prprf`. |
| `FPrFldrMenu` | `FUNCTION FPrFldrMenu(menuID, item: TC): TF;` | Processes menu selection `(menuID, item)` while a Print Manager dialog or background status folder is active, returning `TRUE` if handled. |
| `PrLFntID` | `FUNCTION PrLFntID(VAR prprf: TPrRec; lfntid: TLFntID): TLFntID;` | Constructs a long font identifier lFntid combining the target device from prprf, font family famIn, and text style setIn. |
| `FPrMatch` | `FUNCTION FPrMatch(VAR prprf1, prprf2: TPrRec): TF;` | Returns `TRUE` if print records `prprf1` and `prprf2` specify compatible physical printer hardware configurations. |
| `PrPmRead` | `PROCEDURE PrPmRead(VAR pmRec: TPrPmWd);` | Reads the active printer configuration word (`pmRec`) from Lisa non-volatile Parameter Memory (`PMem`). |
| `PrPmToCfg` | `PROCEDURE PrPmToCfg(pmRec: TPrPmWd; VAR prprf: TPrRec);` | Applies hardware printer configuration fields from Parameter Memory word `pmRec` to print preference record `prprf`. |
| `PrSetSpool` | `PROCEDURE PrSetSpool(VAR prins: TPrRec; fSpool: TF);` | Enables (`fSpool = TRUE`) or disables (`fSpool = FALSE`, switching to direct foreground printing) spool-file generation in job record `prins`. |
| `FPrStlEq` | `FUNCTION FPrStlEq(VAR prprf1, prprf2: TPrRec): TF;` | Returns `TRUE` if print preference records `prprf1` and `prprf2` have equivalent page-style and metric settings, avoiding document reformatting. |
| `PrSubFont` | `PROCEDURE PrSubFont(VAR prprf: TPrRec; fSubFont: TF);` | Sets the font-substitution flag (`fSubFont`) in `prprf` controlling whether standard fonts are substituted when targeting a daisy-wheel printer. |
| `PrTypeR` | `PROCEDURE PrTypeR(VAR prprf: TPrRec; fLqp: TF; wheel: TEwhcl);` | Configures typewriter/daisy-wheel attributes in `prprf`, setting letter-quality printer mode (`fLqp`) and print-wheel pitch/spoke family (`wheel`). |
| `IPgPaper` | `FUNCTION IPgPaper(VAR prprf: TPrRec): TC;` | Returns the standard paper-size index (`iPg8x11`, `iPg8x14`, A4, etc.) matching the paper dimensions in `prprf`. |

---

## Unit PrProcs

Core application-facing Print Shop printing unit in Workshop 1.0/2.0, providing the `PrDocStart`/`PrStartPage`/`PrNextBand`/`PrDumpBand`/`PrEndPage`/`PrDocEnd` banded printing loop, printing `GrafPort` setup, printer-adapted QuickDraw `PrStd*` bottlenecks, and `Tab`/`HRule`/`VRule` drawing primitives.

- **Import**: `USES {$U PrProcs.obj} PrProcs;`
- **Unit kind**: `INTRINSIC` (`PRPROCS`)
- **Interface dependencies**: `SysCall`, `PMDecl`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `PrStd`, `PrBuf`, `PrFile`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `PrDocStart` | `PROCEDURE PrDocStart(VAR cError: TC; VAR prins: TPrRec; ldsn: TC);` | Begins spooling a document using PrRec, opening QuickDraw printing port PrPort, allocating a private spool data segment at LDSN, optionally enabling the spooling alert (DoSpoolAlert), and returning TRUE if disk space and setup succeed. |
| `PrStartPage` | `PROCEDURE PrStartPage(VAR cError: TC);` | Begins a new page in the active Print Shop job, setting `cError` to indicate whether to image bands, skip an out-of-range page, restart unspooled, or abort. |
| `PrNextBand` | `FUNCTION PrNextBand(VAR rBand: Rect): TF;` | Advances to the next band strip on the current page, updating the printing `GrafPort` clip region, returning the band bounds in `rBand`, and returning `FALSE` after the last band. |
| `PrDumpBand` | `PROCEDURE PrDumpBand(VAR cError: TC);` | Flushes the rendered band in the printing `GrafPort` to the spool file or active printer driver, returning any error or recovery code in `cError`. |
| `PrEndPage` | `PROCEDURE PrEndPage(VAR cError: TC);` | Completes the current printed or skipped page, ejecting the sheet in foreground mode or finalizing the spooled page and returning any status code in `cError`. |
| `PrDocEnd` | `PROCEDURE PrDocEnd(VAR cError: TC);` | Finalizes document spooling for prinsIn and PrPort, closing the spool file and data segment, notifying the background print supervisor of the final block, or cleaning up on abort. |
| `PrCleanup` | `PROCEDURE PrCleanup(VAR prins: TPrRec);` | Aborts and cleans up active Print Shop job resources, open spool files, or direct device connections for `prins`. |
| `PrMetrics` | `PROCEDURE PrMetrics(VAR prprf: TPrRec; VAR info: TPrInfo);` | Computes and returns in `info` (`TPrInfo`) the device resolution, full paper rectangle, and printable page bounds corresponding to print record `prprf`. |
| `PrXMetrics` | `PROCEDURE PrXMetrics(VAR prins: TPrRec);` | Computes extended per-band buffer dimensions and byte sizes (`rBand`, `rBounds`, and `lBandSize`) in `prins` via the target printer driver. |
| `PrSetPort` | `PROCEDURE PrSetPort(VAR prPort: GrafPort; pProcs: QDProcsPtr);` | Initializes and selects `prPort` as the active QuickDraw printing `GrafPort`, installing custom bottleneck record `pProcs` (or default printer bottlenecks when `NIL`). |
| `PrUnsetPort` | `PROCEDURE PrUnsetPort;` | Closes and releases internal regions of the active printing `GrafPort` at the end of a print session. |
| `PrSetOrigin` | `PROCEDURE PrSetOrigin(h, v: TC);` | Sets the QuickDraw coordinate origin `(h, v)` of the active printing `GrafPort` while keeping band clipping aligned. |
| `PrOffsetPage` | `PROCEDURE PrOffsetPage(dh, dv: TC);` | Offsets the printable page origin on the physical sheet by `(dh, dv)` device dots for the current page. |
| `PrStuffPort` | `PROCEDURE PrStuffPort(VAR prPort: GrafPort; VAR procs: QDProcs);` | Initializes `prPort` as a printing `GrafPort` and populates `procs` with the Print Shop's standard `PrStd*` QuickDraw bottleneck procedures. |
| `PrStdText` | `PROCEDURE PrStdText(count: TC; textAddr: QDPtr; numer, denom: Point);` | Custom QuickDraw `textProc` printing bottleneck that maps colors, renders device-tuned underlines with descender clearance when needed, and calls `StdText`. |
| `PrStdLine` | `PROCEDURE PrStdLine(newPt: Point);` | Custom QuickDraw `lineProc` printing bottleneck that maps colors, scales pen patterns (preserving solid horizontal/vertical rules), and calls `StdLine`. |
| `PrStdRect` | `PROCEDURE PrStdRect(verb: GrafVerb; r: Rect);` | Custom QuickDraw `rectProc` printing bottleneck that maps colors, scales fill/pen patterns for printer resolution, and calls `StdRect`. |
| `PrStdRRect` | `PROCEDURE PrStdRRect(verb: GrafVerb; r: Rect; ovalWidth, ovalHeight: TC);` | Custom QuickDraw `rRectProc` printing bottleneck that maps colors, scales fill/pen patterns for printer resolution, and calls `StdRRect` with corner diameters `ovalWidth` and `ovalHeight`. |
| `PrStdOval` | `PROCEDURE PrStdOval(verb: GrafVerb; r: Rect);` | Custom QuickDraw `ovalProc` printing bottleneck that maps colors, scales fill/pen patterns for printer resolution, and calls `StdOval`. |
| `PrStdArc` | `PROCEDURE PrStdArc(verb: GrafVerb; r: Rect; startAngle, arcAngle: TC);` | Custom QuickDraw `arcProc` printing bottleneck that maps colors, scales fill/pen patterns for printer resolution, and calls `StdArc` over `startAngle` and `arcAngle`. |
| `PrStdPoly` | `PROCEDURE PrStdPoly(verb: GrafVerb; poly: PolyHandle);` | Custom QuickDraw `polyProc` printing bottleneck that maps colors, scales fill/pen patterns for printer resolution, and calls `StdPoly` on `poly`. |
| `PrStdRgn` | `PROCEDURE PrStdRgn(verb: GrafVerb; rgn: RgnHandle);` | Custom QuickDraw `rgnProc` printing bottleneck that maps colors, scales fill/pen patterns for printer resolution, and calls `StdRgn` on `rgn`. |
| `PrStdBits` | `PROCEDURE PrStdBits(VAR srcBits: BitMap; VAR srcRect, dstRect: Rect; mode: TC; maskRgn: RgnHandle);` | Custom QuickDraw `bitsProc` printing bottleneck that maps colors and transfers `srcBits` from `srcRect` to `dstRect` with `mode` and `maskRgn` via `StdBits`. |
| `Tab` | `PROCEDURE Tab(cLength: TC);` | Advances the printing pen horizontally by `cLength` device dots using a hardware/spool tab operation (drawing an underline segment first if `Underline` is active). |
| `TabTo` | `PROCEDURE TabTo(hPos: TC);` | Moves the printing pen horizontally to target coordinate `hPos` via `Tab`. |
| `HRule` | `PROCEDURE HRule(cLength: TC);` | Draws a 1-device-dot-thick horizontal rule of signed length `cLength` from the current pen location and advances the pen horizontally by `cLength`. |
| `VRule` | `PROCEDURE VRule(cLength: TC);` | Draws a 1-device-dot-thick vertical rule of signed length `cLength` from the current pen location and advances the pen vertically by `cLength`. |
| `PrSysDbg` | `PROCEDURE PrSysDbg(f1, f2, f3: TF);` | Sets internal Print Shop manager (`f1`), device-driver (`f2`), and procedure-trace (`f3`) debug logging flags. |

---

## Unit PrStd

Foundational Print Shop unit in Workshop 1.0/2.0 defining shared print records, factory-default style and Parameter Memory initializers, print-preference validation and version repair, blank-bitmap testing, low-level `Ps*` port I/O, and background-daemon synchronization.

- **Import**: `USES {$U PrStd.obj} PrStd;`
- **Unit kind**: `INTRINSIC SHARED` (`PRSTD`)
- **Interface dependencies**: `UnitStd`, `SysCall`, `PMDecl`, `QuickDraw`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `PrGlobalDefault` | `PROCEDURE PrGlobalDefault;` | Initializes global Print Shop shared state and default printer preference settings. |
| `PrPmDefault` | `PROCEDURE PrPmDefault(VAR pmRec: TPrPmWd);` | Populates Parameter Memory printer configuration word `pmRec` (`TPrPmWd`) with default printer type, port, paper size, and sheet-feeder settings. |
| `PrPrfDefault` | `PROCEDURE PrPrfDefault(VAR prprf: TPrRec);` | Initializes print record prprf from the system default printer in shared memory (or fallback ROM/68K defaults) and resets its job page-range and copy fields. |
| `FPrPrfValid` | `FUNCTION FPrPrfValid(VAR prprf: TPrRec): TF;` | Checks whether print record prprf has the current PrVersion and matches an installed printer ID in the shared Print Manager queue. |
| `PrPrfFix` | `PROCEDURE PrPrfFix(VAR prprf: TPrRec);` | Repairs or migrates an invalid or obsolete `TPrRec` print preference record (`prprf`) in place so that its version, configuration, and metrics are valid. |
| `PrStlDefault` | `PROCEDURE PrStlDefault(VAR prprf: TPrRec);` | Initializes the page-style, paper-size, orientation, and device-metric fields of `prprf` to defaults for its target device. |
| `FClrBitmap` | `FUNCTION FClrBitmap(VAR bits: BitMap; rCheck: Rect): TF;` | Intersects rCheck with bits.bounds and returns TRUE if all bytes within that bitmap rectangle are zero. |
| `PsOpenPort` | `PROCEDURE PsOpenPort(VAR error: INTEGER; port: TPrPort);` | Mounts, configures (disabling auto-LF and setting 9600-baud 8N1/DTR/timeout on RS-232 ports PortA or PortB), and opens hardware printer port Port, returning any OS error in Error. |
| `PsClosePort` | `PROCEDURE PsClosePort(VAR error: INTEGER; port: TPrPort);` | Closes the active printer port object, re-enables break-on-close via DEVICE_CONTROL, and unmounts hardware port Port, returning any OS error in Error. |
| `PsInPort` | `PROCEDURE PsInPort(VAR error: INTEGER; p: TP; c: TC);` | Reads c sequential bytes from the open hardware printer port into buffer p, returning any OS error in Error. |
| `PsOutPort` | `PROCEDURE PsOutPort(VAR error: INTEGER; p: TP; c: TC);` | Writes c sequential bytes from buffer p to the open hardware printer port, returning any OS error in Error. |
| `PsYieldCpu` | `PROCEDURE PsYieldCpu;` | Temporarily lowers the calling process priority and yields the CPU so background printing processes can run. |
| `PsWaitBack` | `PROCEDURE PsWaitBack(bkSet: TSetPrBk);` | Polls the background print daemon while yielding CPU until the daemon's state matches one of the status values in `bkSet` (`TSetPrBk`). |

---

## Unit QuickDraw

Implements Bill Atkinson's Lisa QuickDraw graphics library, providing `GrafPort` management, clipping, cursors, pen and line drawing, styled text rendering and measurement, `Point`/`Rect`/`Polygon`/`Region` geometry and graphical verbs, `BitMap` blitting/scrolling, `Picture` recording/playback, bottleneck procedures, and color/planar bit selection.

- **Import**: `USES {$U QuickDraw.obj} QuickDraw;`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `InitGraf` | `PROCEDURE InitGraf(globalPtr: QDPtr);` | Initializes QuickDraw global variables (`thePort`, standard patterns, `arrow` cursor, `screenBits`, and `randSeed`) in the caller's `QDGlobals` block pointed to by `globalPtr`. |
| `OpenPort` | `PROCEDURE OpenPort(port: GrafPtr);` | Allocates new `visRgn` and `clipRgn` regions for `port`, initializes all `GrafPort` fields to default values via `InitPort`, and makes `port` the current `thePort`. |
| `InitPort` | `PROCEDURE InitPort(port: GrafPtr);` | Reinitializes an already-opened `GrafPort` (`port`) to default screen bitmap, rectangular `visRgn`, wide-open `clipRgn`, normal pen/text/color state, and sets `thePort := port`. |
| `ClosePort` | `PROCEDURE ClosePort(port: GrafPtr);` | Disposes of the `visRgn` and `clipRgn` region handles owned by `port` before the `GrafPort` record itself is released. |
| `SetPort` | `PROCEDURE SetPort(port: GrafPtr);` | Makes `port` the current QuickDraw drawing port (`thePort`). |
| `GetPort` | `PROCEDURE GetPort(VAR port: GrafPtr);` | Returns a pointer to the current QuickDraw `GrafPort` (`thePort`) in `port`. |
| `GrafDevice` | `PROCEDURE GrafDevice(device: INTEGER);` | Sets `thePort^.device` to `device` so the Font Manager selects font strikes and metrics appropriate for that output device. |
| `SetPortBits` | `PROCEDURE SetPortBits(bm: BitMap);` | Sets the destination bitmap (`thePort^.portBits`) of the current `GrafPort` to `bm`. |
| `PortSize` | `PROCEDURE PortSize(width, height: INTEGER);` | Changes the bottom-right corner of `thePort^.portRect` so the current port has dimensions `width` by `height` without moving its top-left corner. |
| `MovePortTo` | `PROCEDURE MovePortTo(leftGlobal, topGlobal: INTEGER);` | Moves the position of `thePort^.portRect` on `portBits` so its top-left corner lies at `(leftGlobal, topGlobal)` in `portBits.bounds` coordinates. |
| `SetOrigin` | `PROCEDURE SetOrigin(h, v: INTEGER);` | Shifts the local coordinate system of `thePort` so its `portRect.topLeft` becomes `(h, v)`, offsetting `portBits.bounds`, `portRect`, and `visRgn` accordingly. |
| `SetClip` | `PROCEDURE SetClip(rgn: RgnHandle);` | Copies region `rgn` into `thePort^.clipRgn` as the current port's clipping region. |
| `GetClip` | `PROCEDURE GetClip(rgn: RgnHandle);` | Copies the current port's clipping region (`thePort^.clipRgn`) into existing region handle `rgn`. |
| `ClipRect` | `PROCEDURE ClipRect(r: Rect);` | Sets the current port's clipping region (`thePort^.clipRgn`) to rectangle `r`. |
| `BackPat` | `PROCEDURE BackPat(pat: Pattern);` | Sets the background pattern (`thePort^.bkPat`) used by `Erase` operations and `ScrollRect` in the current port to `pat`. |
| `InitCursor` | `PROCEDURE InitCursor;` | Sets the current screen cursor image to the standard QuickDraw `arrow` and resets the cursor hide level to 0 so the cursor is visible. |
| `SetCursor` | `PROCEDURE SetCursor(crsr: Cursor);` | Changes the current 16x16 screen cursor bitmap, mask, and hotspot to `crsr`. |
| `HideCursor` | `PROCEDURE HideCursor;` | Hides the screen cursor (if currently visible) and decrements the QuickDraw cursor visibility level. |
| `ShowCursor` | `PROCEDURE ShowCursor;` | Increments the QuickDraw cursor visibility level (up to 0) and redisplays the cursor when the level reaches 0. |
| `ObscureCursor` | `PROCEDURE ObscureCursor;` | Temporarily hides the cursor image on screen until the next time the mouse moves. |
| `HidePen` | `PROCEDURE HidePen;` | Decrements `thePort^.pnVis` so subsequent line, shape, and frame drawing operations in `thePort` do not render pixels on the bitmap. |
| `ShowPen` | `PROCEDURE ShowPen;` | Increments `thePort^.pnVis`, re-enabling visible pen drawing in `thePort` once `pnVis` reaches 0. |
| `GetPen` | `PROCEDURE GetPen(VAR pt: Point);` | Returns the current graphics pen location (`thePort^.pnLoc`) in `pt` in local coordinates. |
| `GetPenState` | `PROCEDURE GetPenState(VAR pnState: PenState);` | Saves the current port's pen location, size, transfer mode, and pattern into `pnState`. |
| `SetPenState` | `PROCEDURE SetPenState(pnState: PenState);` | Restores the current port's pen location, size, transfer mode, and pattern from `pnState`. |
| `PenSize` | `PROCEDURE PenSize(width, height: INTEGER);` | Sets the width and height of the graphics pen in `thePort` to `(width, height)` pixels. |
| `PenMode` | `PROCEDURE PenMode(mode: INTEGER);` | Sets the pattern transfer mode (`patCopy`, `patOr`, `patXor`, `patBic`, or negated variants) of the pen in `thePort` to `mode`. |
| `PenPat` | `PROCEDURE PenPat(pat: Pattern);` | Sets the 8x8 drawing pattern (`pnPat`) of the graphics pen in `thePort` to `pat`. |
| `PenNormal` | `PROCEDURE PenNormal;` | Resets the graphics pen in `thePort` to size `(1, 1)`, mode `patCopy`, and pattern `black`. |
| `MoveTo` | `PROCEDURE MoveTo(h, v: INTEGER);` | Moves the graphics pen in `thePort` to local coordinates `(h, v)` without drawing. |
| `Move` | `PROCEDURE Move(dh, dv: INTEGER);` | Moves the graphics pen in `thePort` by relative offset `(dh, dv)` from its current location without drawing. |
| `LineTo` | `PROCEDURE LineTo(h, v: INTEGER);` | Draws a line with the current pen from `thePort^.pnLoc` to `(h, v)` and updates `pnLoc` to `(h, v)`. |
| `Line` | `PROCEDURE Line(dh, dv: INTEGER);` | Draws a line with the current pen from `thePort^.pnLoc` by relative offset `(dh, dv)` and advances `pnLoc` by `(dh, dv)`. |
| `TextFont` | `PROCEDURE TextFont(font: INTEGER);` | Sets the font family number (`thePort^.txFont`) used for subsequent text drawing and measurement in `thePort` to `font`. |
| `TextFace` | `PROCEDURE TextFace(face: Style);` | Sets the character style set (`thePort^.txFace`, such as `bold`, `italic`, `underline`, `outline`, `shadow`) in `thePort` to `face`. |
| `TextMode` | `PROCEDURE TextMode(mode: INTEGER);` | Sets the source transfer mode (`srcOr`, `srcXor`, `srcBic`, `srcCopy`, etc.) for drawing text in `thePort` to `mode`. |
| `TextSize` | `PROCEDURE TextSize(size: INTEGER);` | Sets the point size (`thePort^.txSize`, `0` for default family size) for text in `thePort` to `size`. |
| `SpaceExtra` | `PROCEDURE SpaceExtra(extra: LongInt);` | Sets the `Fixed`-point extra pixel width (`thePort^.spExtra`) added to each space character for justified text in `thePort` to `extra`. |
| `DrawChar` | `PROCEDURE DrawChar(ch: char);` | Draws single character `ch` at `thePort^.pnLoc` using the current port's font, style, size, and mode, advancing `pnLoc.h` by its width. |
| `DrawString` | `PROCEDURE DrawString(s: Str255);` | Draws Pascal string `s` starting at `thePort^.pnLoc` and advances `pnLoc.h` by the rendered string width. |
| `DrawText` | `PROCEDURE DrawText(textBuf: QDPtr; firstByte, byteCount: INTEGER);` | Draws `byteCount` characters starting at byte offset `firstByte` in `textBuf` at `thePort^.pnLoc` and advances `pnLoc.h`. |
| `CharWidth` | `FUNCTION CharWidth(ch: CHAR): INTEGER;` | Returns the horizontal pixel advance width of character `ch` in the current port's font, style, size, and `spExtra`. |
| `StringWidth` | `FUNCTION StringWidth(s: Str255): INTEGER;` | Returns the total horizontal pixel width of Pascal string `s` in the current port's font, style, size, and `spExtra`. |
| `TextWidth` | `FUNCTION TextWidth(textBuf: QDPtr; firstByte, byteCount: INTEGER): INTEGER;` | Returns the total horizontal pixel width of `byteCount` characters starting at `firstByte` in `textBuf` in the current port's text attributes. |
| `GetFontInfo` | `PROCEDURE GetFontInfo(VAR info: FontInfo);` | Returns the `FontInfo` metrics (`ascent`, `descent`, `widMax`, `leading`) of the current port's active font, style, and size in `info`. |
| `AddPt` | `PROCEDURE AddPt(src: Point; VAR dst: Point);` | Adds the horizontal and vertical coordinates of `src` to `dst` (`dst.h := dst.h + src.h`, `dst.v := dst.v + src.v`). |
| `SubPt` | `PROCEDURE SubPt(src: Point; VAR dst: Point);` | Subtracts the horizontal and vertical coordinates of `src` from `dst` (`dst.h := dst.h - src.h`, `dst.v := dst.v - src.v`). |
| `SetPt` | `PROCEDURE SetPt(VAR pt: Point; h, v: INTEGER);` | Assigns horizontal coordinate `h` and vertical coordinate `v` to `pt`. |
| `EqualPt` | `FUNCTION EqualPt(pt1, pt2: Point): BOOLEAN;` | Returns `TRUE` if points `pt1` and `pt2` have identical `h` and `v` coordinates. |
| `ScalePt` | `PROCEDURE ScalePt(VAR pt: Point; fromRect, toRect: Rect);` | Scales the horizontal and vertical dimensions in `pt` proportionally from the width and height of `fromRect` to those of `toRect` (clamping non-zero sizes to at least 1). |
| `MapPt` | `PROCEDURE MapPt(VAR pt: Point; fromRect, toRect: Rect);` | Maps point `pt` linearly from its relative position within `fromRect` to the corresponding position within `toRect`. |
| `LocalToGlobal` | `PROCEDURE LocalToGlobal(VAR pt: Point);` | Converts `pt` from the local coordinate system of `thePort` into global coordinates (where `(0, 0)` is the top-left of `portBits`). |
| `GlobalToLocal` | `PROCEDURE GlobalToLocal(VAR pt: Point);` | Converts `pt` from global coordinates into the local coordinate system of `thePort`. |
| `SetRect` | `PROCEDURE SetRect(VAR r: Rect; left, top, right, bottom: INTEGER);` | Assigns coordinates `(left, top, right, bottom)` to rectangle `r`. |
| `EqualRect` | `FUNCTION EqualRect(rect1, rect2: Rect): BOOLEAN;` | Returns `TRUE` if `rect1` and `rect2` have identical `top`, `left`, `bottom`, and `right` coordinates. |
| `EmptyRect` | `FUNCTION EmptyRect(r: Rect): BOOLEAN;` | Returns `TRUE` if rectangle `r` encloses no pixels (`r.left >= r.right` or `r.top >= r.bottom`). |
| `OffsetRect` | `PROCEDURE OffsetRect(VAR r: Rect; dh, dv: INTEGER);` | Translates rectangle `r` horizontally by `dh` and vertically by `dv`. |
| `MapRect` | `PROCEDURE MapRect(VAR r: Rect; fromRect, toRect: Rect);` | Maps the `topLeft` and `botRight` corners of rectangle `r` linearly from `fromRect` to `toRect`. |
| `InsetRect` | `PROCEDURE InsetRect(VAR r: Rect; dh, dv: INTEGER);` | Shrinks (for positive `dh`, `dv`) or expands (for negative `dh`, `dv`) rectangle `r` inward on left/right by `dh` and on top/bottom by `dv`. |
| `SectRect` | `FUNCTION SectRect(src1, src2: Rect; VAR dstRect: Rect): BOOLEAN;` | Computes the intersection of `src1` and `src2` into `dstRect` (setting `(0,0,0,0)` if disjoint) and returns `TRUE` if the intersection is non-empty. |
| `UnionRect` | `PROCEDURE UnionRect(src1, src2: Rect; VAR dstRect: Rect);` | Computes into `dstRect` the smallest rectangle that encloses both `src1` and `src2`. |
| `PtInRect` | `FUNCTION PtInRect(pt: Point; r: Rect): BOOLEAN;` | Returns `TRUE` if the pixel below and to the right of `pt` lies inside rectangle `r` (`r.left <= pt.h < r.right` and `r.top <= pt.v < r.bottom`). |
| `Pt2Rect` | `PROCEDURE Pt2Rect(pt1, pt2: Point; VAR dstRect: Rect);` | Constructs in `dstRect` the smallest normalized rectangle enclosing points `pt1` and `pt2`. |
| `FrameRect` | `PROCEDURE FrameRect(r: Rect);` | Draws a hollow outline just inside rectangle `r` using the current port's pen size, pattern, and mode (or appends `r` to an open region). |
| `PaintRect` | `PROCEDURE PaintRect(r: Rect);` | Fills the interior of rectangle `r` using the current port's pen pattern (`pnPat`) and pen transfer mode (`pnMode`). |
| `EraseRect` | `PROCEDURE EraseRect(r: Rect);` | Fills rectangle `r` with the current port's background pattern (`bkPat`) in `patCopy` mode. |
| `InvertRect` | `PROCEDURE InvertRect(r: Rect);` | Inverts every pixel inside rectangle `r` in the current port. |
| `FillRect` | `PROCEDURE FillRect(r: Rect; pat: Pattern);` | Fills rectangle `r` with specified pattern `pat` in `patCopy` mode. |
| `FrameRoundRect` | `PROCEDURE FrameRoundRect(r: Rect; ovWd, ovHt: INTEGER);` | Draws a hollow rounded-corner outline inside `r` with corner oval curvature `(ovWd, ovHt)` using the current pen. |
| `PaintRoundRect` | `PROCEDURE PaintRoundRect(r: Rect; ovWd, ovHt: INTEGER);` | Paints the interior of rounded rectangle `r` with corner curvature `(ovWd, ovHt)` using `thePort`'s pen pattern and mode. |
| `EraseRoundRect` | `PROCEDURE EraseRoundRect(r: Rect; ovWd, ovHt: INTEGER);` | Erases rounded rectangle `r` with corner curvature `(ovWd, ovHt)` using `thePort`'s background pattern (`bkPat`). |
| `InvertRoundRect` | `PROCEDURE InvertRoundRect(r: Rect; ovWd, ovHt: INTEGER);` | Inverts all pixels inside rounded rectangle `r` with corner curvature `(ovWd, ovHt)`. |
| `FillRoundRect` | `PROCEDURE FillRoundRect(r: Rect; ovWd, ovHt: INTEGER; pat: Pattern);` | Fills rounded rectangle `r` with corner curvature `(ovWd, ovHt)` using pattern `pat` in `patCopy` mode. |
| `FrameOval` | `PROCEDURE FrameOval(r: Rect);` | Draws a hollow oval outline inscribed inside rectangle `r` using the current port's pen size, pattern, and mode. |
| `PaintOval` | `PROCEDURE PaintOval(r: Rect);` | Paints the interior of the oval inscribed in rectangle `r` using `thePort`'s pen pattern and mode. |
| `EraseOval` | `PROCEDURE EraseOval(r: Rect);` | Erases the oval inscribed in rectangle `r` using `thePort`'s background pattern (`bkPat`). |
| `InvertOval` | `PROCEDURE InvertOval(r: Rect);` | Inverts all pixels inside the oval inscribed in rectangle `r`. |
| `FillOval` | `PROCEDURE FillOval(r: Rect; pat: Pattern);` | Fills the oval inscribed in rectangle `r` with pattern `pat` in `patCopy` mode. |
| `FrameArc` | `PROCEDURE FrameArc(r: Rect; startAngle, arcAngle: INTEGER);` | Draws an elliptical arc along the perimeter of the oval inscribed in `r` from `startAngle` through `arcAngle` degrees using the current pen. |
| `PaintArc` | `PROCEDURE PaintArc(r: Rect; startAngle, arcAngle: INTEGER);` | Paints a pie-shaped wedge of the oval inscribed in `r` from `startAngle` through `arcAngle` degrees using `thePort`'s pen pattern and mode. |
| `EraseArc` | `PROCEDURE EraseArc(r: Rect; startAngle, arcAngle: INTEGER);` | Erases a pie-shaped wedge of the oval inscribed in `r` from `startAngle` through `arcAngle` degrees using `thePort`'s background pattern. |
| `InvertArc` | `PROCEDURE InvertArc(r: Rect; startAngle, arcAngle: INTEGER);` | Inverts all pixels inside the pie-shaped wedge of `r` spanning `startAngle` through `arcAngle` degrees. |
| `FillArc` | `PROCEDURE FillArc(r: Rect; startAngle, arcAngle: INTEGER; pat: Pattern);` | Fills the pie-shaped wedge of `r` spanning `startAngle` through `arcAngle` degrees with pattern `pat` in `patCopy` mode. |
| `PtToAngle` | `PROCEDURE PtToAngle(r: Rect; pt: Point; VAR angle: INTEGER);` | Computes in `angle` (`0..359` degrees clockwise from 12 o'clock, aspect-adjusted to `r`) the angle from the center of `r` to `pt`. |
| `OpenPoly` | `FUNCTION OpenPoly: PolyHandle;` | Allocates a new `Polygon` handle, hides the pen, and begins recording subsequent `Line`/`LineTo` segments as polygon vertices. |
| `ClosePoly` | `PROCEDURE ClosePoly;` | Stops recording polygon vertices begun by `OpenPoly`, computes the polygon's `polyBBox`, and restores pen visibility. |
| `KillPoly` | `PROCEDURE KillPoly(poly: PolyHandle);` | Deallocates the memory occupied by polygon handle `poly`. |
| `OffsetPoly` | `PROCEDURE OffsetPoly(poly: PolyHandle; dh, dv: INTEGER);` | Translates `poly`'s bounding box and all of its vertices horizontally by `dh` and vertically by `dv`. |
| `MapPoly` | `PROCEDURE MapPoly(poly: PolyHandle; fromRect, toRect: Rect);` | Maps `poly`'s bounding box and all of its vertices linearly from `fromRect` to `toRect`. |
| `FramePoly` | `PROCEDURE FramePoly(poly: PolyHandle);` | Draws the outline edges of polygon `poly` using the current port's pen. |
| `PaintPoly` | `PROCEDURE PaintPoly(poly: PolyHandle);` | Paints the interior of polygon `poly` using `thePort`'s pen pattern and mode. |
| `ErasePoly` | `PROCEDURE ErasePoly(poly: PolyHandle);` | Erases the interior of polygon `poly` using `thePort`'s background pattern (`bkPat`). |
| `InvertPoly` | `PROCEDURE InvertPoly(poly: PolyHandle);` | Inverts all pixels inside polygon `poly`. |
| `FillPoly` | `PROCEDURE FillPoly(poly: PolyHandle; pat: Pattern);` | Fills the interior of polygon `poly` with pattern `pat` in `patCopy` mode. |
| `NewRgn` | `FUNCTION NewRgn: RgnHandle;` | Allocates a new QuickDraw `Region` initialized to the empty region `(0, 0, 0, 0)` and returns its `RgnHandle`. |
| `DisposeRgn` | `PROCEDURE DisposeRgn(rgn: RgnHandle);` | Releases the heap memory occupied by region handle `rgn`. |
| `CopyRgn` | `PROCEDURE CopyRgn(srcRgn, dstRgn: RgnHandle);` | Copies the mathematical structure and bounding box of `srcRgn` into existing region handle `dstRgn`. |
| `SetEmptyRgn` | `PROCEDURE SetEmptyRgn(rgn: RgnHandle);` | Resets existing region `rgn` to the empty region `(0, 0, 0, 0)`. |
| `SetRectRgn` | `PROCEDURE SetRectRgn(rgn: RgnHandle; left, top, right, bottom: INTEGER);` | Sets existing region `rgn` to the simple rectangle `(left, top, right, bottom)` (or empty if degenerate). |
| `RectRgn` | `PROCEDURE RectRgn(rgn: RgnHandle; r: Rect);` | Sets existing region `rgn` to the area of rectangle `r` (or empty if `r` is empty). |
| `OpenRgn` | `PROCEDURE OpenRgn;` | Allocates temporary region-collection storage, hides the pen, and begins accumulating subsequent `Line` and `Frame` calls as region contours. |
| `CloseRgn` | `PROCEDURE CloseRgn(dstRgn: RgnHandle);` | Assembles the contours recorded since `OpenRgn` into `dstRgn`, frees temporary region storage, and restores pen visibility. |
| `OffsetRgn` | `PROCEDURE OffsetRgn(rgn: RgnHandle; dh, dv: INTEGER);` | Translates region `rgn` horizontally by `dh` and vertically by `dv`. |
| `MapRgn` | `PROCEDURE MapRgn(rgn: RgnHandle; fromRect, toRect: Rect);` | Maps and scales region `rgn` from `fromRect` to `toRect`. |
| `InsetRgn` | `PROCEDURE InsetRgn(rgn: RgnHandle; dh, dv: INTEGER);` | Shrinks (for positive `dh`, `dv`) or expands (for negative `dh`, `dv`) all boundary points of `rgn` horizontally by `dh` and vertically by `dv`. |
| `SectRgn` | `PROCEDURE SectRgn(srcRgnA, srcRgnB, dstRgn: RgnHandle);` | Computes the geometric intersection of `srcRgnA` and `srcRgnB` and stores the resulting region in `dstRgn`. |
| `UnionRgn` | `PROCEDURE UnionRgn(srcRgnA, srcRgnB, dstRgn: RgnHandle);` | Computes the geometric union of `srcRgnA` and `srcRgnB` and stores the resulting region in `dstRgn`. |
| `DiffRgn` | `PROCEDURE DiffRgn(srcRgnA, srcRgnB, dstRgn: RgnHandle);` | Subtracts `srcRgnB` from `srcRgnA` and stores the difference region in `dstRgn`. |
| `XorRgn` | `PROCEDURE XorRgn(srcRgnA, srcRgnB, dstRgn: RgnHandle);` | Computes the symmetric difference (exclusive-OR) of `srcRgnA` and `srcRgnB` and stores the resulting region in `dstRgn`. |
| `EqualRgn` | `FUNCTION EqualRgn(rgnA, rgnB: RgnHandle): BOOLEAN;` | Returns `TRUE` if `rgnA` and `rgnB` enclose identical sets of pixels (or if both are empty). |
| `EmptyRgn` | `FUNCTION EmptyRgn(rgn: RgnHandle): BOOLEAN;` | Returns `TRUE` if region `rgn` encloses no pixels. |
| `PtInRgn` | `FUNCTION PtInRgn(pt: Point; rgn: RgnHandle): BOOLEAN;` | Returns `TRUE` if the pixel below and to the right of `pt` is contained within region `rgn`. |
| `RectInRgn` | `FUNCTION RectInRgn(r: Rect; rgn: RgnHandle): BOOLEAN;` | Returns `TRUE` if rectangle `r` intersects region `rgn` in at least one pixel. |
| `FrameRgn` | `PROCEDURE FrameRgn(rgn: RgnHandle);` | Draws a hollow frame just inside the boundary of `rgn` using the current port's pen size, pattern, and mode. |
| `PaintRgn` | `PROCEDURE PaintRgn(rgn: RgnHandle);` | Paints the interior of region `rgn` using `thePort`'s pen pattern and mode. |
| `EraseRgn` | `PROCEDURE EraseRgn(rgn: RgnHandle);` | Erases the interior of region `rgn` using `thePort`'s background pattern (`bkPat`). |
| `InvertRgn` | `PROCEDURE InvertRgn(rgn: RgnHandle);` | Inverts all pixels inside region `rgn`. |
| `FillRgn` | `PROCEDURE FillRgn(rgn: RgnHandle; pat: Pattern);` | Fills the interior of region `rgn` with pattern `pat` in `patCopy` mode. |
| `ScrollRect` | `PROCEDURE ScrollRect(dstRect: Rect; dh, dv: INTEGER; updateRgn: rgnHandle);` | Shifts pixels inside `dstRect` (clipped to `visRgn` and `clipRgn`) by `(dh, dv)`, fills vacated area with `bkPat`, and returns the newly exposed region in `updateRgn`. |
| `CopyBits` | `PROCEDURE CopyBits(srcBits, dstBits: BitMap; srcRect, dstRect: Rect; mode: INTEGER; maskRgn: RgnHandle);` | Transfers (and scales if `srcRect` and `dstRect` differ in size) a rectangular image from `srcBits` to `dstBits` using transfer `mode`, clipped to `maskRgn` (and port regions when `dstBits` is `thePort^.portBits`). |
| `OpenPicture` | `FUNCTION OpenPicture(picFrame: Rect): PicHandle;` | Allocates a new `Picture` with frame `picFrame`, hides the pen, and begins recording subsequent QuickDraw drawing calls in `thePort` into the returned `PicHandle`. |
| `ClosePicture` | `PROCEDURE ClosePicture;` | Stops recording QuickDraw commands into the active picture opened by `OpenPicture` and restores pen visibility. |
| `DrawPicture` | `PROCEDURE DrawPicture(myPicture: PicHandle; dstRect: Rect);` | Plays back recorded QuickDraw picture `myPicture` in `thePort`, scaling and mapping all coordinates from `myPicture^^.picFrame` into `dstRect`. |
| `PicComment` | `PROCEDURE PicComment(kind, dataSize: INTEGER; dataHandle: QDHandle);` | Inserts or dispatches an application- or printer-specific picture comment of type `kind` (with `dataSize` bytes in `dataHandle`) via `commentProc`. |
| `KillPicture` | `PROCEDURE KillPicture(myPicture: PicHandle);` | Releases the heap memory occupied by QuickDraw picture `myPicture`. |
| `SetStdProcs` | `PROCEDURE SetStdProcs(VAR procs: QDProcs);` | Populates `QDProcs` record `procs` with pointers to all thirteen standard QuickDraw low-level bottleneck routines (`StdText` through `StdPutPic`). |
| `StdText` | `PROCEDURE StdText(count: INTEGER; textAddr: QDPtr; numer, denom: Point);` | Standard low-level QuickDraw bottleneck procedure that renders `count` characters from `textAddr` scaled by `numer` over `denom`. |
| `StdLine` | `PROCEDURE StdLine(newPt: Point);` | Standard low-level QuickDraw bottleneck procedure that draws a line from `thePort^.pnLoc` to `newPt` (or records it into an open polygon, region, or picture). |
| `StdRect` | `PROCEDURE StdRect(verb: GrafVerb; r: Rect);` | Standard low-level QuickDraw bottleneck procedure that executes `GrafVerb` `verb` (`frame`, `paint`, `erase`, `invert`, `fill`) on rectangle `r`. |
| `StdRRect` | `PROCEDURE StdRRect(verb: GrafVerb; r: Rect; ovWd, ovHt: INTEGER);` | Standard low-level QuickDraw bottleneck procedure that executes `GrafVerb` `verb` on rounded rectangle `r` with corner oval `(ovWd, ovHt)`. |
| `StdOval` | `PROCEDURE StdOval(verb: GrafVerb; r: Rect);` | Standard low-level QuickDraw bottleneck procedure that executes `GrafVerb` `verb` on the oval inscribed in rectangle `r`. |
| `StdArc` | `PROCEDURE StdArc(verb: GrafVerb; r: Rect; startAngle, arcAngle: INTEGER);` | Standard low-level QuickDraw bottleneck procedure that executes `GrafVerb` `verb` on the arc/wedge of `r` from `startAngle` through `arcAngle`. |
| `StdPoly` | `PROCEDURE StdPoly(verb: GrafVerb; poly: PolyHandle);` | Standard low-level QuickDraw bottleneck procedure that executes `GrafVerb` `verb` on polygon `poly`. |
| `StdRgn` | `PROCEDURE StdRgn(verb: GrafVerb; rgn: RgnHandle);` | Standard low-level QuickDraw bottleneck procedure that executes `GrafVerb` `verb` on region `rgn`. |
| `StdBits` | `PROCEDURE StdBits(VAR srcBits: BitMap; VAR srcRect, dstRect: Rect; mode: INTEGER; maskRgn: RgnHandle);` | Standard low-level QuickDraw bottleneck procedure that blits and scales `srcRect` from `srcBits` into `dstRect` of `thePort^.portBits` with `mode` and `maskRgn`. |
| `StdComment` | `PROCEDURE StdComment(kind, dataSize: INTEGER; dataHandle: QDHandle);` | Standard low-level QuickDraw bottleneck procedure for picture comments, recording `kind` and `dataHandle` when a picture is open and ignoring them otherwise. |
| `StdTxMeas` | `FUNCTION StdTxMeas(count: INTEGER; textAddr: QDPtr; VAR numer, denom: Point; VAR info: FontInfo): INTEGER;` | Standard low-level QuickDraw bottleneck function that measures `count` bytes of text at `textAddr`, updating scaling (`numer`, `denom`) and `info` and returning unscaled pixel width. |
| `StdGetPic` | `PROCEDURE StdGetPic(dataPtr: QDPtr; byteCount: INTEGER);` | Standard low-level QuickDraw bottleneck procedure that reads `byteCount` bytes from the picture currently being played back into `dataPtr`. |
| `StdPutPic` | `PROCEDURE StdPutPic(dataPtr: QDPtr; byteCount: INTEGER);` | Standard low-level QuickDraw bottleneck procedure that appends `byteCount` bytes from `dataPtr` to the picture currently being recorded and updates `picSize`. |
| `GetPixel` | `FUNCTION GetPixel(h, v: INTEGER): BOOLEAN;` | Inspects the pixel immediately below and to the right of local coordinates `(h, v)` in `thePort^.portBits` and returns `TRUE` if it is black (1). |
| `Random` | `FUNCTION Random: INTEGER;` | Advances `randSeed` using QuickDraw's linear congruential generator and returns a pseudo-random signed 16-bit integer in `-32767..32767`. |
| `StuffHex` | `PROCEDURE StuffHex(thingptr: QDPtr; s: Str255);` | Parses hexadecimal digits from string `s` (ignoring non-hex characters) and stores the decoded bytes sequentially starting at `thingptr`. |
| `ForeColor` | `PROCEDURE ForeColor(color: LongInt);` | Sets the foreground color planar code (`thePort^.fgColor`) in the current port to `color` (such as `blackColor`, `redColor`, etc.). |
| `BackColor` | `PROCEDURE BackColor(color: LongInt);` | Sets the background color planar code (`thePort^.bkColor`) in the current port to `color` (such as `whiteColor`, `cyanColor`, etc.). |
| `ColorBit` | `PROCEDURE ColorBit(whichBit: INTEGER);` | Sets `thePort^.colrBit` to `whichBit` (`0..31`) to tell QuickDraw which color plane is currently being rendered into. |

---

## Unit RhDev

Low-level device driver interface for the Apple/Qume Daisy Wheel printer, managing buffered escape-command transmission, incremental 1/120-inch horizontal and 1/48-inch vertical carriage positioning, program-control spoke/ribbon/impression firing, and form-feed handling.

- **Import**: `USES {$U RhDev.obj} RhDev;`
- **Unit kind**: `INTRINSIC` (`RHDEV`)
- **Interface dependencies**: `SysCall`, `PMDecl`, `UnitStd`, `QuickDraw`, `PrStd`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `RhDevOpen` | `PROCEDURE RhDevOpen(cFormLength: TC; tyPort: TPrPort; fPgmCtl: TF);` | Opens and initializes the Daisy Wheel printer on `tyPort`, resetting carriage coordinates, setting form length `cFormLength` (in 1/48-inch units), and configuring program-control mode `fPgmCtl`. |
| `RhDevClose` | `PROCEDURE RhDevClose;` | Emits hardware reset escape commands to restore the Qume/Apple Daisy Wheel printer to standard mode and flushes the output buffer. |
| `RhCmd` | `PROCEDURE RhCmd;` | Outputs an ASCII `ESC` prefix byte via `RhOut` to start a Daisy Wheel escape command sequence. |
| `RhFlushBuffer` | `PROCEDURE RhFlushBuffer;` | Writes all buffered command and print bytes in `RhDev` out to the Daisy Wheel printer port and resets the buffer count. |
| `RhGotoX` | `PROCEDURE RhGotoX(xIn: TC);` | Sets the target horizontal Daisy Wheel carriage coordinate to `xIn` (in 1/120-inch increments). |
| `RhGotoY` | `PROCEDURE RhGotoY(yIn: TC);` | Sets the target vertical Daisy Wheel paper coordinate to `yIn` (in 1/48-inch increments). |
| `RhGotoXY` | `PROCEDURE RhGotoXY(xIn, yIn: TC);` | Sets both the target horizontal (`xIn`, in 1/120-inch units) and vertical (`yIn`, in 1/48-inch units) coordinates of the Daisy Wheel carriage. |
| `RhNewPage` | `PROCEDURE RhNewPage;` | Advances the Daisy Wheel paper to the top of the next sheet (or prompts for manual cut-sheet insertion), flushes buffered commands, and resets the vertical position. |
| `RhOut` | `PROCEDURE RhOut(a: TA);` | Appends command or data byte `a` to `RhDev`'s output buffer, flushing via `RhFlushBuffer` when the buffer reaches capacity. |
| `RhPrSpoke` | `PROCEDURE RhPrSpoke(spoke: TSpoke; cRibbon, cImpression: TC; fHalfUp: TF);` | Prints Daisy Wheel spoke `spoke` in program-control mode using ribbon advance `cRibbon`, hammer impression `cImpression`, and optional half-step vertical offset `fHalfUp`. |
| `RhSetFormLng` | `PROCEDURE RhSetFormLng(cFormLength: TC);` | Emits the Daisy Wheel escape command setting physical page form length to `cFormLength` (in 1/48-inch units). |
| `RhSetPgmCtl` | `PROCEDURE RhSetPgmCtl(fPgmCtl: TF);` | Enables (`fPgmCtl = TRUE`) or disables (`fPgmCtl = FALSE`) Qume Daisy Wheel program-control spoke-addressing mode. |
| `RhSetReverse` | `PROCEDURE RhSetReverse(fReverse: TF);` | Enables (`fReverse = TRUE`) or disables (`fReverse = FALSE`) right-to-left reverse horizontal carriage motion on the Daisy Wheel printer. |

---

## Unit RhProcs

High-level Print Shop driver unit for the Apple/Qume Daisy Wheel printer, implementing port/device lifecycle control, page and band metric computation, spoke-mapped `StdText` capture, tab and horizontal/vertical rule buffering, and band output.

- **Import**: `USES {$U RhProcs.obj} RhProcs;`
- **Unit kind**: `INTRINSIC` (`RHPROCS`)
- **Interface dependencies**: `SysCall`, `PMDecl`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `PrStd`, `PrBuf`, `RhDev`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `RhOpen` | `PROCEDURE RhOpen(VAR prins: TPrRec);` | Opens the Daisy Wheel printer port for `prins`, loads print-wheel spoke tables, installs QuickDraw capture bottlenecks, and initializes the printer via `RhDevOpen`. |
| `RhClose` | `PROCEDURE RhClose(VAR prins: TPrRec);` | Resets the Daisy Wheel printer via `RhDevClose` and closes the underlying OS port specified in `prins`. |
| `RhCleanup` | `PROCEDURE RhCleanup(VAR prins: TPrRec);` | Aborts an active Daisy Wheel print job for `prins`, ejecting any partially printed sheet before closing the device and port. |
| `RhMetrics` | `PROCEDURE RhMetrics(VAR prstl: TPrRec);` | Computes Daisy Wheel resolution (`120`x`48` dpi), paper rectangle, and printable area bounds into `prstl` for the configured paper size, orientation, and feeder. |
| `RhXMetrics` | `PROCEDURE RhXMetrics(VAR prins: TPrRec);` | Computes extended Daisy Wheel band-buffering metrics (`rBand`, `rBounds`, and `lBandSize`) into `prins` for draft or graphics mode. |
| `RhDumpBand` | `PROCEDURE RhDumpBand(VAR prRec: TPrRec);` | Flushes and prints all buffered text, tab, horizontal-rule, and vertical-rule commands falling within the current band of `prRec` on the Daisy Wheel printer. |
| `RhEjectPage` | `PROCEDURE RhEjectPage;` | Advances the Daisy Wheel printer to the next sheet via `RhNewPage` if the current page is marked dirty, then clears the dirty flag. |
| `RhStdText` | `PROCEDURE RhStdText(cCount: TC; textBuf: QDPtr; numer, denom: Point);` | Custom QuickDraw `textProc` bottleneck for the Daisy Wheel driver that maps colors, adjusts font pitch/wheel metrics, and buffers `cCount` characters from `textBuf`. |
| `RhTab` | `PROCEDURE RhTab(cLength: TC);` | Records a Daisy Wheel horizontal tab of `cLength` dots from the current pen position, emitting an underline rule first if `Underlined` is set in `txFace`. |
| `RhHRule` | `PROCEDURE RhHRule(cLength: TC);` | Records a horizontal rule of `cLength` dots at the current QuickDraw pen position into the Daisy Wheel command buffer (`PbHRule`). |
| `RhVRule` | `PROCEDURE RhVRule(cLength: TC);` | Records a vertical rule of `cLength` dots at the current QuickDraw pen position into the Daisy Wheel command buffer (`PbVRule`). |

---

## Unit Scrap

Manages the shared inter-application Clipboard (Scrap), supporting application-specific scrap handles, QuickDraw universal pictures (ScrapUG), and formatted Universal Text control streams (ScrapCs). Provides process ownership transfer, two-segment undoable Cut/Copy transactions, and on-demand data-segment binding.

- **Import**: `USES {$U Scrap.obj} Scrap;`
- **Unit kind**: `INTRINSIC SHARED` (`SCRAP`)
- **Interface dependencies**: `UnitStd`, `UnitHz`, `SysCall`, `UnitFile`, `QuickDraw`, `FontMgr`, `Storage`, `Events`, `Folders`, `WmlStd`, `WmlSb`, `UnitFmt`, `PMDecl`, `PrStdInfo`, `UnitCs`, `UnitFigAtom`, `UnitFf`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `InitScrap` | `PROCEDURE InitScrap(VAR InitErr: Integer);` | Initializes the shared Scrap data segments (ScrapOne, ScrapTwo, and UTDSeg), heap zones, and Lotus/figure backing files at boot time and assigns initial Scrap ownership to the Filer. |
| `KillScrapOwner` | `PROCEDURE KillScrapOwner(Who: ProcessId; VAR KillErr: TC);` | Transfers ownership of the Scrap folder back to the Filer and clears the dead process's Scrap table entry when the Scrap-owning process terminates. |
| `ReviveScrapOwner` | `PROCEDURE ReviveScrapOwner(Who: ProcessId);` | Transfers ownership of the Scrap folder from the Filer back to revived process Who and erases the Scrap window's port rectangle. |
| `DrawUScrap` | `PROCEDURE DrawUScrap(VAR DrawErr: TC);` | Erases the Scrap folder's content area and draws the QuickDraw universal picture (ScrapUG) currently stored in the Scrap, or returns ScrapNotPicture if none exists. |
| `BackOutOfScrap` | `PROCEDURE BackOutOfScrap;` | Recovers from an unrecoverable Scrap access error by unbinding the active Scrap data segment, restoring the saved undo Scrap, and discarding the failed Scrap state. |
| `OpenScrap` | `PROCEDURE OpenScrap(VAR OpenErr: Integer);` | Sets OpenErr to 0 as a backward-compatible no-op stub, since Scrap data segments are opened automatically on first use by each process. |
| `DSegOfScrap` | `FUNCTION DSegOfScrap: Integer;` | Ensures the active Scrap data segment is open for the calling process and returns its OS data-segment reference number (or 0 on error). |
| `AddrofScrapDSeg` | `FUNCTION AddrofScrapDSeg: LongInt;` | Returns the base virtual memory address at which the active Scrap data segment is mapped. |
| `HzOfScrap` | `FUNCTION HzOfScrap: THz;` | Returns the heap zone pointer (THz) of the active application-specific Scrap data segment. |
| `ClaimScrap` | `PROCEDURE ClaimScrap;` | Transfers ownership of the Scrap folder and ScrapProcess to the calling process without modifying or erasing the existing Scrap contents. |
| `InheritScrap` | `PROCEDURE InheritScrap(SaveOld: Boolean);` | Claims Scrap ownership for a new Cut or Copy operation, optionally switching to the alternate Scrap data segment to preserve the previous Scrap for Undo, and clears the Scrap window. |
| `UndoInheritScrap` | `PROCEDURE UndoInheritScrap(VAR UndoErr: integer);` | Swaps the current and saved Scrap states to restore the previous Scrap contents, owner process, and CurrScrapSet, and invalidates the Scrap window for repainting. |
| `AcceptInheritScrap` | `PROCEDURE AcceptInheritScrap;` | Commits the preceding InheritScrap operation by clearing the undo state and shrinking the dormant alternate Scrap data segment if it exceeds dormant size thresholds. |
| `EraseScrapData` | `PROCEDURE EraseScrapData(VAR EraseErr: integer);` | Clears the current Scrap contents prior to writing new data by initializing a fresh heap zone in the active Scrap data segment and emptying CurrScrapSet. |
| `StartPutScrap` | `PROCEDURE StartPutScrap(VAR PutErr: integer);` | Verifies Scrap ownership, opens and binds the active Scrap data segment, and enables read/write access for a Scrap write operation. |
| `PutScrap` | `PROCEDURE PutScrap(which: ScrapType; what: TH; VAR PutErr: integer);` | Records an application-specific ScrapType tag and data handle in the current Scrap and adds the type to CurrScrapSet. |
| `PutGrScrap` | `PROCEDURE PutGrScrap(What: PicHandle; VAR PutErr: integer);` | Stores QuickDraw picture handle What as the universal graphics representation (ScrapUG) of the current Scrap and adds ScrapUG to CurrScrapSet. |
| `PutCsScrap` | `PROCEDURE PutCsScrap(icsContents: TB; VAR PutCSErr: integer);` | Serializes Universal Text control stream icsContents and its embedded figures into the active Scrap's formatted .LOTUS/.FIGURES backing files in UTDSeg and adds ScrapCs to CurrScrapSet. |
| `EndPutScrap` | `PROCEDURE EndPutScrap(VAR PutErr: integer);` | Completes a Scrap write transaction by restoring read-only access on the active Scrap data segment and unbinding it from the calling process. |
| `StartGetScrap` | `PROCEDURE StartGetScrap(VAR GetErr: integer);` | Opens and binds the active Scrap data segment into the calling process's working set for reading Scrap contents. |
| `GetScrap` | `PROCEDURE GetScrap(VAR which: ScrapType; VAR what: TH);` | Returns the application-specific ScrapType identifier and data handle currently stored in the Scrap. |
| `GetGrScrap` | `PROCEDURE GetGrScrap(VAR What: PicHandle);` | Returns the QuickDraw PicHandle for the universal graphics representation stored in the Scrap (or NIL if none is present). |
| `GetCsScrap` | `PROCEDURE GetCsScrap(VAR Contents: TB);` | Returns the formatted-file control stream index (icsFf) for the Scrap's Universal Text contents, or icsNil if no valid Universal Text stream is stored. |
| `EndGetScrap` | `PROCEDURE EndGetScrap(VAR GetErr: integer);` | Completes a Scrap read transaction by unbinding the active Scrap data segment from the calling process's working set. |
| `bindUTDSeg` | `PROCEDURE bindUTDSeg(VAR BindErr: integer);` | Opens (if not yet open) and binds the shared Universal Text data segment (UTDSeg) into the calling process's memory space. |
| `unBindUTDSeg` | `PROCEDURE unBindUTDSeg(VAR UnBindErr: integer);` | Opens (if not yet open) and unbinds the shared Universal Text data segment (UTDSeg) from the calling process's working set. |

---

## Unit Storage

Provides QuickDraw-compatible dynamic memory allocation routines (Ptr and Handle management) layered over a UnitHz heap zone (theHeap).

- **Import**: `USES {$U Storage.obj} Storage;`
- **Interface dependencies**: `UnitStd`, `UnitHz`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `InitHeap` | `PROCEDURE InitHeap(startPtr, limitPtr: Ptr; errorProc: ProcPtr);` | Initializes theHeap as a new UnitHz heap zone spanning startPtr to limitPtr with 500 initial master pointers and errorProc as its zone-growth callback. |
| `SetHeap` | `PROCEDURE SetHeap(hz: Thz);` | Sets the current Storage/QuickDraw heap zone global (theHeap and ordHeap) to hz. |
| `GetHeap` | `PROCEDURE GetHeap(VAR hz: Thz);` | Returns the currently active Storage heap zone (theHeap) in hz. |
| `NewPtr` | `FUNCTION NewPtr(byteCount: INTEGER): Ptr;` | Allocates a non-relocatable block (tybkNrel) of byteCount bytes in theHeap and returns a pointer to its data. |
| `DisposePtr` | `PROCEDURE DisposePtr(p: Ptr);` | Frees a non-relocatable memory block previously allocated by NewPtr in theHeap. |
| `NewHandle` | `FUNCTION NewHandle(byteCount: INTEGER): Handle;` | Allocates a relocatable block of byteCount bytes in theHeap and returns its master-pointer Handle. |
| `DisposeHandle` | `PROCEDURE DisposeHandle(h: Handle);` | Frees the relocatable block and master pointer referenced by handle h in its owning heap zone if h is non-NIL. |
| `SetSize` | `PROCEDURE SetSize(h: Handle; newSize: INTEGER);` | Resizes the relocatable block referenced by handle h to newSize bytes within its owning heap zone. |
| `GetSize` | `FUNCTION GetSize(h: Handle): INTEGER;` | Returns the usable data size in bytes of the relocatable block referenced by handle h. |
| `LockHandle` | `PROCEDURE LockHandle(h: Handle);` | Temporarily locks relocatable heap block `h` in place (`LockHandleInConcrete`) so its master pointer can be dereferenced without compaction moving the block. |
| `UnlockHandle` | `PROCEDURE UnlockHandle(h: Handle);` | Unlocks previously locked relocatable heap block `h` (`UnlockHandleFromConcrete`) so heap compaction may relocate it again. |

---

## Unit Sys1Lock

Provides per-segment wrapper procedures used by the Desktop Manager (Filer) to lock individual SYS1LIB intrinsic code segments into physical memory via LockSeg.

- **Import**: `USES {$U Sys1Lock.obj} Sys1Lock;`
- **Unit kind**: `INTRINSIC` (`SYS1LOCK`)
- **Interface dependencies**: `UnitStd`, `SysCall`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `LkHotSeg` | `PROCEDURE LkHotSeg(VAR err: INTEGER);` | Locks the resident hot-path system library intrinsic code segment (`HotSeg`) in memory, returning any Lisa OS error code in `err`. |
| `LkGrafSeg` | `PROCEDURE LkGrafSeg(VAR err: INTEGER);` | Locks the GRAFSEG QuickDraw/graphics code segment of SYS1LIB into physical memory via LockSeg. |
| `LkFldSel` | `PROCEDURE LkFldSel(VAR err: INTEGER);` | Locks the Field Editor selection-handling intrinsic code segment (`FldSel`) in `Sys1Lib` in memory, returning any Lisa OS error code in `err`. |
| `LkWMCold` | `PROCEDURE LkWMCold(VAR err: INTEGER);` | Locks the WMcold Window Manager cold code segment of SYS1LIB into physical memory via LockSeg. |
| `LkPxHz` | `PROCEDURE LkPxHz(VAR err: INTEGER);` | Locks the Storage Manager heap-inspection/scrambling intrinsic code segment (`SegPxHz`) in memory, returning any Lisa OS error code in `err`. |
| `LkFmgrUtil` | `PROCEDURE LkFmgrUtil(VAR err: INTEGER);` | Locks the FmgrUtil Font Manager utility code segment of SYS1LIB into physical memory via LockSeg. |
| `LkWMWarm` | `PROCEDURE LkWMWarm(VAR err: INTEGER);` | Locks the WMwarm Window Manager warm-path code segment of SYS1LIB into physical memory via LockSeg. |
| `LkWMJrnl` | `PROCEDURE LkWMJrnl(VAR err: INTEGER);` | Locks the WMJrnl Window Manager journaling code segment of SYS1LIB into physical memory via LockSeg. |
| `LkFldEdit` | `PROCEDURE LkFldEdit(VAR err: INTEGER);` | Locks the Field Editor text-editing intrinsic code segment (`FldEdit`) in `Sys1Lib` in memory, returning any Lisa OS error code in `err`. |

---

## Unit UnitCs

Implements the polymorphic Control Stream (TCs) framework used by LisaWrite, Field Editor, Scrap, and Universal Text to sequence runs and track logical position intervals (TLp, TInt) across formatted text, ruler, page, and figure streams.

- **Import**: `USES {$U UnitCs.obj} UnitCs;`
- **Unit kind**: `INTRINSIC SHARED` (`UNITCS`)
- **Interface dependencies**: `UnitStd`, `UnitHz`, `SysCall`, `Storage`, `QuickDraw`, `FontMgr`, `PMDecl`, `PrStdInfo`, `UnitFmt`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `LpMinP` | `FUNCTION LpMinP(lp1: TLp; lp2: TLp): TLp;` | Returns the smaller of two 32-bit logical stream positions (lp1 and lp2). |
| `LpMaxP` | `FUNCTION LpMaxP(lp1: TLp; lp2: TLp): TLp;` | Returns the larger of two 32-bit logical stream positions (lp1 and lp2). |
| `PxRgcs` | `PROCEDURE PxRgcs;` | Prints diagnostic state for every allocated control stream slot (0 through icsMac - 1) in rghcs. |
| `PxAchad` | `PROCEDURE PxAchad(VAR achad: TAchad);` | Prints the index bounds, buffer address, and character contents (rendering tabs and carriage returns symbolically) of character slice achad for debugging. |
| `PxCs` | `PROCEDURE PxCs(ics: TB);` | Verifies interval list consistency and prints diagnostic details—including tracked intervals and class-specific state—for control stream ics. |
| `FreeInt` | `PROCEDURE FreeInt(ics: TB; oint: TC);` | Unlinks interval descriptor oint from its control stream's interval list and returns it to the global interval free list (lldInt). |
| `OintMark` | `FUNCTION OintMark(oint: TC; ics: TB; lpFst: TLp; lpLim: TLp; fValid: TF; ointParent: TC): TC;` | Allocates (when oint = ointNil) or reassigns an interval descriptor on control stream ics, updating its [lpFst..lpLim) bounds, validity flag, and parent interval offset. |
| `IcsCreate` | `FUNCTION IcsCreate(tycs: TTycs; cbCs: TC; hz: THz): TB;` | Allocates and initializes a control stream record of class tycs and byte size cbCs in heap zone hz, returning its stream index in rghcs. |
| `FreeIcs` | `PROCEDURE FreeIcs(ics: TB);` | Detaches tracked intervals, invokes the stream's class-specific iprocFreeIcs cleanup procedure, and frees the heap handle and process entry for control stream ics. |
| `PxLpd` | `PROCEDURE PxLpd(lpd: TLpd; VAR achad: TAchad);` | Prints the logical position fields, character and paragraph formatting records, and associated character slice of logical position descriptor lpd for debugging. |
| `SetLpd` | `PROCEDURE SetLpd(lpd: TLpd; ics: TB; lp: TLp; tyset: TTyset; VAR achad: TAchad);` | Initializes logical position descriptor lpd for control stream ics at logical position lp with formatting flags tyset and sequences the initial run into achad. |
| `SeqLpd` | `PROCEDURE SeqLpd(lpd: TLpd; VAR achad: TAchad);` | Advances lpd to the next contiguous run in its control stream via the stream's iprocSeqLpd dispatch procedure, populating achad and formatting descriptors. |
| `FParStart` | `FUNCTION FParStart(ics: TB; lp: TLp): TF;` | Returns TRUE if logical position lp in control stream ics lies at the beginning of a paragraph or at the end of the stream. |
| `FindLpFixed` | `PROCEDURE FindLpFixed(ics: TB; lp: TLp; VAR lpFixed: TLp);` | Dispatches to the iprocFindLpFixed procedure of control stream ics to find a stable formatting anchor position (lpFixed) at or preceding lp. |
| `FindLpFstPar` | `PROCEDURE FindLpFstPar(ics: TB; lp: TLp; VAR lpFixed: TLp);` | Sets lpFixed to the starting logical position (lpFstPar) of the paragraph containing lp in control stream ics. |
| `InitCs` | `PROCEDURE InitCs(hz: THz);` | Initializes the UnitCs subsystem in heap zone hz, allocating the stream table (rghcs), interval free list (lldInt), default logical position descriptors, and standard page layout (pglpStd). |
| `PxInt` | `PROCEDURE PxInt(oint: TC);` | Prints the logical position bounds, stream index, validity flag, and doubly-linked list offsets of interval descriptor oint for debugging. |
| `AdjustLps` | `PROCEDURE AdjustLps(ics: TB; lpFstInv: TLp; lpLimInv: TLp; dlpAdjust: TLp);` | Shifts logical position intervals following [lpFstInv..lpLimInv) by dlpAdjust in control stream ics and invalidates overlapping intervals and their parent intervals. |
| `FSelLpBounds` | `FUNCTION FSelLpBounds(lp: TLp; ics: TB; VAR lpFstSel, lpLimSel, lpFstAtom, lpLimAtom: TLp): TF;` | Invokes the iprocFSelLpBounds dispatch procedure of control stream ics to determine the outer selectable range and minimum atomic selection bounds around lp. |
| `TrueStdSelLpBounds` | `FUNCTION TrueStdSelLpBounds(lp: TLp; ics: TB; VAR lpFstSel, lpLimSel, lpFstAtom, lpLimAtom: TLp): TF;` | Computes default outer bounds [0..lpMax) and minimum atomic character or figure selection bounds around lp for standard text and figure streams, returning TRUE. |
| `FTextIcs` | `FUNCTION FTextIcs(ics: TB): TF;` | Returns TRUE if control stream ics holds textual content rather than a ruler, page-layout, or figure stream. |
| `PurgeIcsPrcs` | `PROCEDURE PurgeIcsPrcs;` | Frees all tracked intervals and control streams in rghcs owned by the calling process (My_Id). |

---

## Unit UnitFf

Implements formatted-file control streams (tycsFf, .LOTUS format) that read and write 512-byte pages containing text runs, character and paragraph formatting bytecodes, headers/footers, and embedded figure references.

- **Import**: `USES {$U UnitFf.obj} UnitFf;`
- **Unit kind**: `INTRINSIC SHARED` (`UNITFF`)
- **Interface dependencies**: `UnitStd`, `UnitHz`, `SysCall`, `UnitFile`, `QuickDraw`, `FontMgr`, `Storage`, `UnitFmt`, `PMDecl`, `PrStdInfo`, `UnitCs`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `PxHcsff` | `PROCEDURE PxHcsff(hcs: THcs);` | Prints the backing file index, stream limit, and TFfLeader header fields of a formatted-file control stream handle (hcs) for debugging. |
| `PxLeader` | `PROCEDURE PxLeader(VAR leader: TFfleader);` | Prints the password, format version, header/footer/body logical offsets, and page layout metrics of a TFfLeader record for debugging. |
| `SeqLpdFf` | `PROCEDURE SeqLpdFf(lpd: TLpd; VAR achad: TAChad);` | Sequences the next text run from a formatted-file control stream (tycsFf) at lpd^.lpLim, decoding page-level character and paragraph formatting bytecodes into lpd and copying text into achad. |
| `IcsFfCreate` | `FUNCTION IcsFfCreate(ifil: TC; icsFig: TB; hz: THz; VAR ffleader: TFfleader): TB;` | Creates a formatted-file control stream (tycsFf) backed by open file ifil and figure stream icsFig in heap zone hz, loading and returning its TFfLeader header. |
| `FreeFfIcs` | `PROCEDURE FreeFfIcs(icsFf: TB);` | Frees any attached figure stream, flushes and closes the backing UnitFile file, and deallocates formatted-file control stream icsFf. |
| `WriteIcsFf` | `PROCEDURE WriteIcsFf(icsDoc: TB; pglp: TPglp; tyrluFf: TTyRlU; ifil: TB; ifilFig: TB; hzDoc: THz);` | Serializes header, footer, and body text runs—along with any embedded figures—from stream icsDoc into 512-byte formatted-file pages in ifil (and ifilFig) and writes the TFfLeader header block. |
| `InitFF` | `PROCEDURE InitFF;` | Initializes the formatted-file control stream dispatch table (cspdFf) and opens the fallback System.BadPageMsg.Lotus page file if available. |
| `LpMacFf` | `FUNCTION LpMacFf(icsFf: TB): TLp;` | Returns the logical end-of-stream position (lpLim) of formatted-file control stream icsFf. |
| `SetLeaderOfIcsFfFromIFil` | `PROCEDURE SetLeaderOfIcsFfFromIFil(ics: TB; ifil: TC; hz: THz);` | Maps block 0 of file ifil in heap zone hz to load the TFfLeader header and compute the logical byte limit (lpLim) of formatted-file control stream ics. |
| `IfilOfFf` | `FUNCTION IfilOfFf(icsFf: TB): TB;` | Returns the UnitFile file index (ifil) backing formatted-file control stream icsFf. |
| `GetLeaderOfIcsFf` | `PROCEDURE GetLeaderOfIcsFf(icsFf: TB; VAR ffleader: TFfLeader);` | Copies the TFfLeader header record of formatted-file control stream icsFf into ffleader. |

---

## Unit UnitFile

Provides fixed-block and virtual-object (TVofil) file I/O integrated with UnitHz named-object demand paging (FilCbOfN, FilFSwapInN, FilSwapOutN).

- **Import**: `USES {$U UnitFile.obj} UnitFile;`
- **Unit kind**: `INTRINSIC SHARED` (`UNITFILE`)
- **Interface dependencies**: `UnitStd`, `UnitHz`, `SysCall`, `PSysCall`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `InitFiles` | `PROCEDURE InitFiles(hz: THz);` | Allocates and initializes the open-file descriptor table (rgStFile) in heap zone hz and marks all OS and Monitor file slots closed. |
| `IfilOpen` | `FUNCTION IfilOpen(VAR cError: TC; pathIn: String255; cbBlk: TC; setaccess: TSetaccess; hzWrite: THz; password: E_name): TB;` | Opens or creates the file at pathIn with block size cbBlk (0 for virtual-object files) and access mode setaccess, initializing its TVofil directory if needed and returning its ifil index. |
| `CloseIfil` | `PROCEDURE CloseIfil(VAR cError: TC; ifil: TB);` | Truncates open file ifil to its logical byte limit (ibLim), writes out its TVofil header (or deletes an empty virtual-object file), closes the OS file, and releases the ifil slot. |
| `FilCbOfN` | `FUNCTION FilCbOfN(n: TN): TC;` | Returns the byte length of UnitHz named file object n from either the file's fixed block size (cbBlk) or its virtual-object descriptor (TVod). |
| `FilFSwapInN` | `FUNCTION FilFSwapInN(hz: THz; n: TN): TF;` | Reads the disk data for UnitHz named file object n from its backing file into its heap block in hz, returning TRUE if all requested bytes are read without error. |
| `FilSwapOutN` | `PROCEDURE FilSwapOutN(hz: THz; n: TN);` | Writes the data of dirty UnitHz named file object n from heap zone hz to its backing file offset, extending the file on disk if necessary. |
| `NFromIfilIb` | `FUNCTION NFromIfilIb(ifil: TB; ib: TL): TN;` | Packs file index ifil and byte offset or virtual-object index ib into a 32-bit UnitHz named-object identifier (TN). |
| `CBlkOfIfil` | `FUNCTION CBlkOfIfil(ifil: TC): TC;` | Returns the number of blocks (using cbBlk, or 512-byte blocks for virtual-object files) spanned by the logical length (ibLim) of open file ifil. |
| `RenameFile` | `PROCEDURE RenameFile(VAR cError: TC; pathIn: String255; enameIn: TSp; password: E_name);` | Renames the Lisa OS file at pathIn to new entry name enameIn via Rename_Secure and returns any error code in cError. |
| `KillFile` | `PROCEDURE KillFile(VAR cError: TC; pathIn: String255; password: E_name);` | Deletes the Lisa OS file at pathIn via Kill_Secure and returns any filesystem error code in cError. |
| `FMonitorFile` | `FUNCTION FMonitorFile(path: String255): TF;` | Returns FALSE in Lisa OS builds, indicating that path refers to a native Lisa OS file rather than a legacy UCSD Monitor file. |
| `PathOfIfil` | `PROCEDURE PathOfIfil(ifil: TC; VAR path: String255; VAR password: e_name);` | Returns the pathname and password recorded for open file ifil (or empty strings if ifil is closed). |
| `SetIbLimOfIfil` | `PROCEDURE SetIbLimOfIfil(ifil: TB; ibLim: TL);` | Sets the logical end-of-file byte position (ibLim) recorded for open file ifil. |
| `RefnumOfIfil` | `FUNCTION RefnumOfIfil(ifil: TB): TC;` | Returns the Lisa OS file reference number for open file ifil, or -1 if ifil is invalid, closed, or a Monitor file. |
| `CleanIfil` | `PROCEDURE CleanIfil(VAR cError: TC; hz: THz; ifil: TB; fIgnoreDirty: TF);` | Unlocks and evicts (FreeN) all resident UnitHz named objects belonging to file ifil—writing dirty blocks unless fIgnoreDirty is TRUE—and returns and resets the file's accumulated error code. |
| `CErrOfIfil` | `FUNCTION CErrOfIfil(ifil: TB): TC;` | Returns the first swap-out filesystem error code accumulated for open file ifil. |

---

## Unit UnitFmt

Encodes, decodes, and applies compact formatting bytecodes (fop / rgfbc) that modify character style attributes (TArce), paragraph margins and spacing (TArpe), and tab-stop descriptors (TTbd).

- **Import**: `USES {$U UnitFmt.obj} UnitFmt;`
- **Unit kind**: `INTRINSIC SHARED` (`UNITFMT`)
- **Interface dependencies**: `UnitStd`, `UnitHz`, `QuickDraw`, `FontMgr`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `PxArce` | `PROCEDURE PxArce(VAR arce: TArce);` | Prints the character formatting flags, font index, and superscript offset of character descriptor arce for debugging. |
| `PxArpe` | `PROCEDURE PxArpe(VAR arpe: TArpe);` | Prints the margins, justification, spacing, and tab-stop descriptors of paragraph descriptor arpe for debugging. |
| `CfbcApplyIfld` | `FUNCTION CfbcApplyIfld(ifld: TC; wsval: TW; pval: TPc; rpe: TRpe; rce: TRce): TC;` | Applies a single formatting field operation (ifld with short value wsval and operand pointer pval) to paragraph descriptor rpe or character descriptor rce and returns the instruction's byte length. |
| `IfbcLstApplyRgfbc` | `FUNCTION IfbcLstApplyRgfbc(rgfbc: TRgb; rpe: TRpe; rce: TRce): TC;` | Executes a fopcEnd-terminated formatting bytecode array (rgfbc) against paragraph descriptor rpe and character descriptor rce, returning the byte offset of the terminating fopcEnd. |
| `AddRgfbc` | `PROCEDURE AddRgfbc(VAR hfcc: THfcc; hfccSrc: THfcc; hz: THz);` | Appends the formatting bytecodes from hfccSrc onto formatting command collection hfcc, allocating, copying-on-write, or growing hfcc in heap zone hz as needed. |
| `AddFop` | `PROCEDURE AddFop(VAR hfcc: THfcc; ifld: TB; sval: TW; pval: TPc; hz: THz);` | Appends a single formatting bytecode instruction for field ifld (with value sval/pval) followed by fopcEnd onto formatting command collection hfcc in heap zone hz. |
| `GenFopsDiff` | `PROCEDURE GenFopsDiff(hfcc: THfcc; tydst: TTydst; rcpeStd, rcpe: TP; hz: THz);` | Populates hfcc with the formatting bytecodes required to transform baseline descriptor rcpeStd into target character or paragraph descriptor rcpe. |
| `zzGenParFops` | `PROCEDURE zzGenParFops(hfcc: THfcc; rpe: TRpe; hz: THz);` | Populates hfcc with formatting bytecodes encoding all paragraph attributes and tab stops of paragraph descriptor rpe in heap zone hz. |
| `ItbFromX` | `FUNCTION ItbFromX(rgtbd: TRgtbd; itbLst: TC; x: TX): TC;` | Binary-searches sorted tab-stop array rgtbd[0..itbLst] and returns the index of the tab stop at or immediately left of horizontal coordinate x. |
| `InitFmt` | `PROCEDURE InitFmt;` | Initializes the Modern/Classic font mapping tables, default character and paragraph descriptors (arceStd, arpeStd, tbdNil), and formatting field bit-mask descriptors (argfld). |
| `PxRgfbc` | `PROCEDURE PxRgfbc(rgfbc: TRgb);` | Decodes and prints each formatting bytecode instruction in fopcEnd-terminated array rgfbc for debugging. |

---

## Unit UnitHz

Implements the Lisa heap zone manager (THz), supporting relocatable handle blocks (tybkStd), non-relocatable pointer blocks (tybkNrel), demand-swapped named objects (tybkN), heap compaction, and data-segment growth.

- **Import**: `USES {$U UnitHz.obj} UnitHz;`
- **Interface dependencies**: `UnitStd`, `SysCall`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `HAllocate` | `FUNCTION HAllocate(hz: THz; cb: TC): TH;` | Allocates a relocatable block of cb bytes in heap zone hz and returns its master-pointer handle (TH), or hNil if allocation fails. |
| `HzInit` | `FUNCTION HzInit(pFst: TP; pLim: TP; pBase: TP; ipPoolMac: TC; logIpnLim: TC; procCbMore: TProc; procCbOfN: TProc; procFSwapInN: TProc; procSwapOutN: TProc): THz;` | Initializes and returns a new heap zone (THz) spanning [pFst..pLim) with ipPoolMac initial master pointers, 2^logIpnLim named-object hash slots, and segment-growth and swap callbacks. |
| `PxHz` | `PROCEDURE PxHz(hz: THz);` | Prints a diagnostic dump of all contiguous heap blocks and the free-block ring in heap zone hz. |
| `ChangeSizeH` | `PROCEDURE ChangeSizeH(hz: THz; h: TH; cbNew: TC);` | Resizes the relocatable block or locked named object referenced by handle h in heap zone hz to cbNew bytes by shrinking, growing in place, or relocating the block. |
| `FreeBk` | `PROCEDURE FreeBk(hz: THz; h: TH; tybk: TTybk);` | Marks the heap block referenced by h (of type tybk) free in heap zone hz, inserts it into the free list, and returns its master pointer to the free pool if applicable. |
| `AllocBk` | `PROCEDURE AllocBk(hz: THz; hDst: TH; cb: TC; tybk: TTybk);` | Allocates a block of type tybk (tybkStd, tybkNrel, or tybkN) with cb data bytes in heap zone hz—compacting, evicting named objects, or growing the zone as needed—and stores its data pointer in hDst^. |
| `PMapN` | `FUNCTION PMapN(hz: THz; nSrc: TN): TP;` | Maps named object nSrc into heap zone hz (allocating a tybkN block and swapping in its data via procFSwapInN if not resident), updates its usage age, and returns a pointer to its data. |
| `PCreateNob` | `FUNCTION PCreateNob(hz: THz; nSrc: TN; cbData: TC): TP;` | Allocates a new unlocked, clean named-object block (tybkN) of cbData bytes for name nSrc in heap zone hz, registers it in the named-object hash table, and returns a pointer to its data. |
| `SetFDirty` | `PROCEDURE SetFDirty(hz: THz; n: TN; fDirty: TF);` | Sets or clears the dirty flag (fDirty) on resident named object n in heap zone hz so dirty objects are swapped out before eviction. |
| `SetCbFree` | `PROCEDURE SetCbFree(hz: THz; cbFree: TL; fEnlargeHz: TF);` | Ensures at least cbFree free bytes are available in heap zone hz by evicting unlocked named objects and, when fEnlargeHz is TRUE, expanding the zone via procCbMore. |
| `CbDataOfH` | `FUNCTION CbDataOfH(hz: THz; h: TH): TC;` | Returns the usable data byte count (excluding block header overhead) of the relocatable or locked named-object block referenced by handle h in heap zone hz. |
| `PAllocate` | `FUNCTION PAllocate(hz: THz; cb: TC): TP;` | Allocates a non-relocatable block (tybkNrel) of cb bytes in heap zone hz and returns a direct pointer (TP) to its data. |
| `FreeH` | `PROCEDURE FreeH(hz: THz; h: TH);` | Frees the standard relocatable block (tybkStd) or named-object block (tybkN) referenced by handle h in heap zone hz. |
| `FreeP` | `PROCEDURE FreeP(hz: THz; p: TP);` | Frees the non-relocatable block (tybkNrel) pointed to by p in heap zone hz. |
| `FreeN` | `PROCEDURE FreeN(hz: THz; n: TN);` | Evicts unlocked named object n from heap zone hz (swapping its data out first if dirty) and removes its entry from the named-object hash table. |
| `ReleaseBkNrel` | `PROCEDURE ReleaseBkNrel(hz: THz; pFstRelease: TP);` | Frees all non-relocatable blocks (tybkNrel) in heap zone hz located at or above address pFstRelease. |
| `PLstFree` | `FUNCTION PLstFree(hz: THz): TP;` | Coalesces adjacent free blocks in heap zone hz and returns a pointer to the highest-addressed free block (or pNil if none exists). |
| `HzFromH` | `FUNCTION HzFromH(h: TH): THz;` | Derives and returns the owning heap zone pointer (THz) of a pool-allocated relocatable handle h from its block back-pointer (or hzNil if base-relative). |
| `FCheckHzOk` | `FUNCTION FCheckHzOk(hz: THz; VAR cBkStd: TC): TF;` | Audits the structural consistency of heap zone hz—checking contiguous blocks, free links, master pointers, and named objects—and returns TRUE if valid along with the tybkStd block count in cBkStd. |
| `HLockN` | `FUNCTION HLockN(hz: THz; n: TN; fNeedH: TF): TH;` | Swaps in and locks named object n in heap zone hz against eviction, optionally allocating and returning a master-pointer handle (TH) to its data when fNeedH is TRUE. |
| `UnlockN` | `PROCEDURE UnlockN(hz: THz; n: TN);` | Unlocks named object n in heap zone hz and releases any master-pointer handle previously assigned to it by HLockN. |
| `EnlargeHz` | `PROCEDURE EnlargeHz(hz: THz; cbMore: TL);` | Incorporates cbMore newly added bytes at the end of heap zone hz by advancing its sentinel block (bkLst) and increasing cbFree. |
| `CbShrinkHz` | `FUNCTION CbShrinkHz(hz: THz; cbLess: TL): TL;` | Evicts unlocked named objects, compacts heap zone hz, trims up to cbLess free bytes from the end of the zone, and returns the actual byte reduction. |
| `CbOfHz` | `FUNCTION CbOfHz(hz: THz): TL;` | Returns the total size in bytes of heap zone hz from its zone header through its end sentinel block. |
| `CbMoreGrowSeg` | `FUNCTION CbMoreGrowSeg(hz: THz; cbNeed: TC): TC;` | Expands the Lisa OS data segment containing heap zone hz in 2048-byte increments via Size_DataSeg to satisfy cbNeed bytes and returns the memory byte increase. |

---

## Unit UnitStd

Defines core scalar, pointer, character-slice (TAchad), and doubly-linked offset-list (TLld) types along with low-level memory move, binary search, division, bitfield, and ASCII case-conversion utilities.

- **Import**: `USES {$U UnitStd.obj} UnitStd;`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `CMin` | `FUNCTION CMin(c1: TC; c2: TC): TC;` | Returns the smaller of two 16-bit signed integers (c1 and c2). |
| `CMax` | `FUNCTION CMax(c1: TC; c2: TC): TC;` | Returns the larger of two 16-bit signed integers (c1 and c2). |
| `MoveAchad` | `PROCEDURE MoveAchad(VAR achadDst: TAchad; VAR achadSrc: TAchad);` | Copies achadDst.ichLim - achadDst.ichFst bytes from achadSrc (starting at ichFst) into achadDst (starting at ichFst). |
| `MoveRgch` | `PROCEDURE MoveRgch(rgchDst: TRgch; rgchSrc: TRgch; cb: TC);` | Copies cb bytes from rgchSrc to rgchDst, safely preserving data when source and destination ranges overlap. |
| `MoveOvRgch` | `PROCEDURE MoveOvRgch(rgchDst: TRgch; rgchSrc: TRgch; cb: TC);` | Copies cb bytes from rgchSrc to rgchDst in 68000 assembly, selecting forward or reverse longword/byte transfers to handle overlapping memory blocks. |
| `DivMod` | `PROCEDURE DivMod(num: TC; denom: TC; VAR quotient: TC; VAR rem: TC);` | Computes both the integer quotient (num DIV denom) and remainder (num MOD denom) of num divided by denom. |
| `IBinSearch` | `FUNCTION IBinSearch(rgc: TRgc; icLst: TC; c: TC): TC;` | Performs a binary search over sorted 16-bit integer array rgc^[0..icLst] and returns the largest index whose value is less than or equal to c (or 0 if c < rgc^[0]). |
| `Break` | `PROCEDURE Break(bkcd: TC);` | Triggers a deliberate address-0 fault (after optionally printing breakpoint code bkcd in debug builds) to halt execution in the debugger. |
| `MoveOlle` | `PROCEDURE MoveOlle(lld: Tlld; olle: TC; VAR olleDstFst: TC; VAR olleSrcFst: TC);` | Unlinks the list element at byte offset olle from doubly-linked offset list olleSrcFst (if non-nil) within lld and inserts it at the head of olleDstFst. |
| `PxLld` | `PROCEDURE PxLld(lld: TLld);` | Prints the free-list head, limit offset, and doubly-linked free elements of offset-list descriptor lld when debug tracing is enabled. |
| `InitOlleFree` | `PROCEDURE InitOlleFree(lld: TLld; olleFreeFst: TC; cbAlle: TC);` | Partitions the buffer range from olleFreeFst to lld^.olleLim into elements of cbAlle bytes and links them onto the free list lld^.olleFreeFst. |
| `IchCr` | `FUNCTION IchCr(VAR achad: TAchad; fFwd: TF): TC;` | Scans character slice achad forward from ichFst (if fFwd is TRUE) or backward from ichLim - 1 for a carriage return (ASCII 13) and returns its index (or the scan bound if absent). |
| `WAnd` | `FUNCTION WAnd(w1, w2: TW): TW;` | Returns the 16-bit bitwise AND of words w1 and w2. |
| `WXor` | `FUNCTION WXor(w1, w2: TW): TW;` | Returns the 16-bit bitwise exclusive-OR (XOR) of words w1 and w2. |
| `WNot` | `FUNCTION WNot(w: TW): TW;` | Returns the 16-bit bitwise one's complement (NOT) of word w. |
| `WShLft` | `FUNCTION WShLft(w: TW; cbitSh: TW): TW;` | Logically shifts 16-bit word w left by cbitSh bits, zero-filling the vacated low-order bits. |
| `WShRt` | `FUNCTION WShRt(w: TW; cbitSh: TW): TW;` | Logically shifts 16-bit word w right by cbitSh bits, zero-filling the vacated high-order bits. |
| `AsgnField` | `PROCEDURE AsgnField(p: TP; ib: TW; mskNotFld: TW; val: TW; cbitSh: TC);` | Inserts bitfield value val (shifted left by cbitSh) into the 16-bit word at byte offset ib from pointer p while preserving bits selected by mskNotFld. |
| `ValOfField` | `FUNCTION ValOfField(p: TP; ib: TW; mskNotFld: TW; cbitSh: TC): TW;` | Extracts and logically right-shifts (by cbitSh) the bitfield masked by NOT mskNotFld from the 16-bit word at byte offset ib from pointer p. |
| `UpperCh` | `FUNCTION UpperCh(ch: CHAR): CHAR;` | Converts character ch (with ASCII code >= 'a') by subtracting 32 to uppercase and returns other characters unchanged. |
| `MakeSpUpper` | `PROCEDURE MakeSpUpper(VAR sp: TSp);` | Converts characters in 80-character string sp (TSp) to uppercase in place via UpperCh. |

---

## Unit Windows

Implements the internal Lisa Window Manager display list, visible/clipping/update region calculations, z-order management, window movement and resizing, process/focus activation, and dynamic window-title strings underlying Folders.

- **Import**: `USES {$U Windows.obj} Windows;`
- **Unit kind**: `INTRINSIC SHARED` (`WINDOWS`)
- **Interface dependencies**: `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `SysCall`, `Events`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `BringToFront` | `PROCEDURE BringToFront(window: WindowPeek; reDraw: BOOLEAN);` | Moves window to the front of the normal window list (just behind dialogFolder), subtracts its structure region from formerly overlapping windows' visRgns, optionally repaints it, and recalculates its visRgn. |
| `CalcVis` | `PROCEDURE CalcVis(window: WindowPeek);` | Computes window^.port.visRgn in local coordinates by intersecting grayRgn with contRgn and subtracting the structure regions of all visible windows in front of it, refreshing any windowPic content. |
| `CalcVisBehind` | `PROCEDURE CalcVisBehind(startWindow: WindowPeek; clobbered: RgnHandle);` | Recalculates the visible region (CalcVis) of startWindow and of every visible window behind it whose content bounding box intersects clobbered. |
| `ChangeProcess` | `PROCEDURE ChangeProcess(window: WindowPtr; newProcess: ProcessID);` | Reassigns window ownership to newProcess, updates activeFolder and keyProcess if needed, and retargets any queued events referencing window to newProcess. |
| `CheckWindow` | `PROCEDURE CheckWindow(VAR event: EventRecord);` | Routes a raw input event from CheckEvents—dispatching Command-Period aborts, disk/power events to the Filer, mouse-down hit tests, mouse-up events to buttonWindow, and keystrokes to keyWindow. |
| `ClipAbove` | `PROCEDURE ClipAbove(window: WindowPeek);` | Sets wmPort^.clipRgn to its intersection with grayRgn minus the structure regions of all visible windows in front of window. |
| `DeleteWindow` | `PROCEDURE DeleteWindow(window: WindowPeek);` | Unlinks window from the depth-ordered Window Manager display list. |
| `DisposeString` | `PROCEDURE DisposeString(sh: StringHandle);` | Frees a dynamic StringHandle previously allocated by NewString. |
| `DrawNew` | `PROCEDURE DrawNew(window: WindowPeek; fUpdate: BOOLEAN);` | Repaints the XOR difference between window's saved old regions and its new structure and content regions across window and windows behind it, updates visRgns, and disposes the saved regions. |
| `GetWindTitle` | `PROCEDURE GetWindTitle(window: WindowPeek; VAR title: Str255);` | Copies the title string of window into title (or sets title to an empty string if window is NIL). |
| `HideWindow` | `PROCEDURE HideWindow(window: WindowPeek);` | Marks window invisible without changing its z-order or active state, repaints newly exposed windows behind it, recalculates visRgns, and empties window^.updateRgn. |
| `HiLiteWindow` | `PROCEDURE HiLiteWindow(window: WindowPeek; fHiLite: BOOLEAN);` | Updates window^.hilited to fHiLite (when okActivate is true) and calls its windowProc to redraw its title tab clipped against windows in front of it. |
| `HitContent` | `PROCEDURE HitContent(window: WindowPeek; event: EventRecord);` | Handles a mouse-down in window's content area by posting buttonDown if window is already the key, alert, or dialog window, or otherwise activating and bringing window to the front. |
| `InsertWindow` | `PROCEDURE InsertWindow(window, behind: WindowPeek);` | Inserts window into the depth-ordered display list immediately behind behind (or just in front of filerFolder when behind is NIL). |
| `MakeActive` | `PROCEDURE MakeActive(window: WindowPeek; event: EventRecord);` | Directs future keystrokes to window (if okActivate is true) as the new keyWindow/keyProcess and sends a folderDeactivate event to the previously active window. |
| `MoveWindow` | `PROCEDURE MoveWindow(windPeek: WindowPeek; dh, dv: INTEGER; bringFront: BOOLEAN);` | Moves windPeek by (dh, dv) pixels in global coordinates (blitting directly when fully visible or hiding and re-showing otherwise), optionally brings it to the front, and posts a folderMoved event. |
| `NewString` | `FUNCTION NewString(str: Str255): StringHandle;` | Allocates a relocatable StringHandle of Length(str) + 1 bytes on the current heap and copies str into it. |
| `PaintBehind` | `PROCEDURE PaintBehind(startWindow: WindowPeek; clobbered: RgnHandle);` | Repaints desktop background/gray areas and invokes PaintOne for startWindow and every visible window behind it within clobbered. |
| `PaintOne` | `PROCEDURE PaintOne(window: WindowPeek; clobbered: RgnHandle);` | Draws window's frame via its windowProc (clipped to clobbered and windows above), erases exposed content (or fills filerFolder with gray), and merges exposed content into updateRgn. |
| `PrevWindow` | `FUNCTION PrevWindow(window: WindowPeek): WindowPeek;` | Walks the display list from menuFolder to return the window immediately in front of window (returning filerFolder when window is NIL). |
| `SaveOld` | `PROCEDURE SaveOld(window: WindowPeek);` | Saves copies of window's current strucRgn and contRgn (or empty regions if invisible) into oldStructure and oldContent for a subsequent DrawNew call. |
| `SendUpdate` | `PROCEDURE SendUpdate;` | Sends a folderUpdate event to activeFolder (if visible with a non-empty updateRgn and no windowPic) or to the frontmost visible window needing an update. |
| `SetActWindow` | `PROCEDURE SetActWindow(window: WindowPeek);` | Sets activeFolder and activeProcess to window and its owner, assigns shared menu, alert, and dialog folders to that process, and adjusts OS process priorities. |
| `SetString` | `PROCEDURE SetString(sh: StringHandle; str: Str255);` | Resizes existing StringHandle sh to Length(str) + 1 bytes and copies str into it. |
| `SetWindTitle` | `PROCEDURE SetWindTitle(window: WindowPeek; title: Str255);` | Updates window's title handle and pixel width, recalculates its structure regions, and repaints and updates visRgns for the old and new title-tab area. |
| `ShowWindow` | `PROCEDURE ShowWindow(window: WindowPeek);` | Marks window visible without changing its z-order or activeFolder, recalculates its regions, repaints window and affected areas, and queues an update. |
| `TopActive` | `PROCEDURE TopActive;` | Activates the frontmost visible normal window behind dialogFolder, or activates filerFolder if no normal window is visible. |
| `UpShift` | `FUNCTION UpShift(ch: CHAR): CHAR;` | Converts lowercase ASCII letter ch ('a'..'z') to uppercase and leaves all other characters unchanged. |
| `WindowSize` | `PROCEDURE WindowSize(window: WindowPeek; width, height: INTEGER; fUpdate: BOOLEAN);` | Resizes window's portRect to width by height (when okGrow is true), recalculates its regions, redraws its frame, and updates newly exposed or resized regions. |

---

## Unit WmlCrs

Manages the standard Window Manager Library (WML) system cursors—such as arrow, I-beam, scroll arrows, split skewers, crosshairs, hourglass, and hidden cursor—loaded from syscursor.

- **Import**: `USES {$U WmlCrs.obj} WmlCrs;`
- **Unit kind**: `INTRINSIC` (`WMLCRS`)
- **Interface dependencies**: `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `FmgrUtil`, `WmlStd`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `InitWmlCrs` | `PROCEDURE InitWmlCrs(VAR cError: TC);` | Loads all standard WML cursor shapes and masks (icrsInactive through icrsGEIbeam) from syscursor, selects the inactive arrow cursor, and makes the cursor visible. |
| `SetStdCursor` | `PROCEDURE SetStdCursor(icrs: TC);` | Sets the active cursor to standard WML cursor index icrs (hiding it for icrsHidden, showing without shape change for icrsEscape, or installing argcrs[icrs]). |
| `IcrsCurrent` | `FUNCTION IcrsCurrent: TC;` | Returns the standard WML cursor index (icrsFirst..icrsLast) currently in effect. |

---

## Unit WmlGrow

Implements window grow-box geometry, rendering, hit-testing, and interactive XOR-frame rubber-band resizing for Lisa windows.

- **Import**: `USES {$U WmlGrow.obj} WmlGrow;`
- **Unit kind**: `INTRINSIC` (`WMLGROW`)
- **Interface dependencies**: `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `WmlStd`, `SysCall`, `Events`, `Folders`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `GetGrowRect` | `PROCEDURE GetGrowRect(VAR rGrow: TR);` | Computes the 24x16-pixel grow-box rectangle (rGrow) at the bottom-right corner of thePort^.portRect. |
| `PaintGrow` | `PROCEDURE PaintGrow;` | Erases the current port's grow-box rectangle and draws the grow-box glyph from WMFont. |
| `FGrowHit` | `FUNCTION FGrowHit(pt: TPt): TF;` | Returns TRUE if local point pt lies within the current port's grow-box rectangle. |
| `DragFrame` | `PROCEDURE DragFrame(ptMouse: TPt; fDrawScrolls: TF; VAR ptNewBR: TPt);` | Tracks the mouse while the button stays down to drag a gray XOR window-resize outline (optionally showing scroll-bar borders) and returns the proposed local bottom-right corner in ptNewBR. |
| `InitXorFrame` | `PROCEDURE InitXorFrame;` | Captures the current window's global frame and title-tab coordinates, saves thePort, and switches to deskPort with a gray XOR pen for XorFrame drawing. |
| `XorFrame` | `PROCEDURE XorFrame(ptFrameBR: TPt; fDrawScrolls: TF);` | Draws or erases (in gray XOR mode on deskPort) the window resize outline—including any title-tab line and optional scroll-bar borders—with global bottom-right corner ptFrameBR. |
| `EndXorFrame` | `PROCEDURE EndXorFrame;` | Restores normal pen attributes and resets the current QuickDraw port to the port saved by InitXorFrame. |

---

## Unit WmlSb

Implements Window Manager Library (WML) scroll bars and split-pane scroll boxes (TSb), supporting arrow, page-flip, thumb, and split-skewer layout, hit-testing, rendering, pane splitting, and interactive dragging.

- **Import**: `USES {$U WmlSb.obj} WmlSb;`
- **Unit kind**: `INTRINSIC` (`WMLSB`)
- **Interface dependencies**: `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `WmlStd`, `SysCall`, `Events`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `InitWmlSb` | `PROCEDURE InitWmlSb;` | Initializes WmlSb module globals, including scroll-box, thumb, and skewer dimensions, orthogonal axis mapping (TyvhNOT), and WMFont arrow and page-flip symbol tables. |
| `InitSbList` | `PROCEDURE InitSbList(VAR sbList: TSbList; hz: THz);` | Initializes scroll-box list sbList to an empty list associated with heap zone hz. |
| `SbCreate` | `FUNCTION SbCreate(VAR sbList: TSbList; hsbBefore: THSb; tyvhSb: TTyvh; ptTopLeft: TPt; cdBotRt: TCd): THSb;` | Allocates and initializes a horizontal or vertical scroll box (THSb) extending from ptTopLeft to cdBotRt in sbList.hz and links it into sbList after hsbBefore. |
| `KillSb` | `PROCEDURE KillSb(VAR sbList: TSbList; hsbKill: THSb);` | Unlinks scroll box hsbKill from sbList (promoting the following pane to head if hsbKill was a scroll-bar head) and frees its heap handle. |
| `GetSbRect` | `PROCEDURE GetSbRect(hsb: THSb; VAR r: TR);` | Returns the bounding rectangle (r) of scroll box hsb. |
| `SetSbRect` | `PROCEDURE SetSbRect(hsb: THSb; r: TR);` | Sets the bounding rectangle of scroll box hsb to r. |
| `RefconSb` | `FUNCTION RefconSb(hsb: THSb): TL;` | Returns the 32-bit application reference constant (refCon) stored in scroll box hsb. |
| `SetSbRefcon` | `PROCEDURE SetSbRefcon(hsb: THSb; refcon: TL);` | Stores 32-bit application reference constant refcon in scroll box hsb. |
| `HsbFirst` | `FUNCTION HsbFirst(VAR sbList: TSbList): THSb;` | Returns the first scroll-box handle (hsbFst) in sbList, or hsbNil if the list is empty. |
| `HsbNext` | `FUNCTION HsbNext(hsb: THSb): THSb;` | Returns the next scroll-box handle after hsb in the TSbList chain, or hsbNil at the end. |
| `HsbPrev` | `FUNCTION HsbPrev(hsb: THSb): THSb;` | Returns the previous scroll-box handle before hsb in the TSbList chain, or hsbNil at the head. |
| `TyvhOfSb` | `FUNCTION TyvhOfSb(hsb: THSb): TTyvh;` | Returns the orientation selector (tyvhH or tyvhV) of scroll box hsb. |
| `SetSbIcons` | `PROCEDURE SetSbIcons(hsb: THSb; siconNew: TSicon);` | Sets the set of icons (sicon, such as skewer, arrows, page-flip buttons, and thumb) eligible for display in scroll box hsb. |
| `GetSbIcons` | `PROCEDURE GetSbIcons(hsb: THSb; VAR sicon: TSicon);` | Copies the configured set of eligible icons (sicon) of scroll box hsb into sicon. |
| `GetVisIcons` | `PROCEDURE GetVisIcons(hsb: THSb; VAR siconVis: TSicon);` | Copies the set of icons currently visible (siconVis) in scroll box hsb into siconVis. |
| `CThumbPos` | `FUNCTION CThumbPos(hsb: THSb): TC;` | Returns the current thumb position of scroll box hsb in thousandths (0..1000). |
| `SetThumb` | `PROCEDURE SetThumb(hsb: THSb; cNewThumb: TC);` | Clamps cNewThumb to 0..1000 and updates the stored thumb position of scroll box hsb without redrawing. |
| `MoveSb` | `PROCEDURE MoveSb(hsb: THSb; ptNewTL: TPt);` | Moves the bounding rectangle of scroll box hsb so its top-left corner is at ptNewTL while preserving its width and height. |
| `AdjSbCorner` | `PROCEDURE AdjSbCorner(hsb: THSb; dcdAdjust: TCd; fTopLeft: TF);` | Shifts either the top/left (fTopLeft = TRUE) or bottom/right (fTopLeft = FALSE) coordinate of scroll box hsb along its scroll axis by dcdAdjust pixels. |
| `PaintSb` | `PROCEDURE PaintSb(hsb: THSb);` | Fills and frames scroll box hsb, computes which icons fit within its length, and draws its visible skewer, scroll arrows, page-flip icons, and thumb. |
| `EraseSb` | `PROCEDURE EraseSb(hsb: THSb);` | Erases the bounding rectangle of scroll box hsb in the current QuickDraw port. |
| `PaintArw` | `PROCEDURE PaintArw(hsb: THSb; iconWhichArw: TIcon; fBlack: TF);` | Redraws a visible arrow or page-flip icon (iconWhichArw) of scroll box hsb in either highlighted filled-black (fBlack = TRUE) or normal outline form. |
| `HsbFromPt` | `FUNCTION HsbFromPt(VAR sbList: TSbList; pt: TPt): THSb;` | Searches sbList and returns the first scroll-box handle whose bounding rectangle contains pt (or hsbNil if none contains it). |
| `FSbHit` | `FUNCTION FSbHit(VAR sbList: TSbList; pt: TPt; VAR hsbHit: THSb; VAR iconHit: TIcon): TF;` | Checks whether point pt lies inside any scroll box in sbList, returning TRUE along with the hit scroll box (hsbHit) and specific icon or shaft region (iconHit) when hit. |
| `FlushRects` | `PROCEDURE FlushRects(VAR rH, rV: TR);` | Computes the standard flush-bottom horizontal (rH) and flush-right vertical (rV) scroll-bar rectangles for thePort^.portRect, excluding the corner grow box. |
| `MkPosts` | `PROCEDURE MkPosts(hsb: THSb; VAR posts: TPosts);` | Computes the coordinate fenceposts (posts[iconSkewer..iconArwB]) marking the end of each icon and gray-shaft region along scroll box hsb's axis. |
| `SplitSb` | `PROCEDURE SplitSb(VAR sbList: TSbList; hsbOld: THSb; VAR hsbNew: THSb; cdCut: TCd);` | Splits scroll box hsbOld at coordinate cdCut along its axis, allocating a new continuation scroll box hsbNew linked immediately after hsbOld on the same scroll bar. |
| `AdjSplitBetween` | `PROCEDURE AdjSplitBetween(hsbBefore, hsbAfter: THSb; dcdAdjust: TCd);` | Moves the shared split boundary between adjacent scroll boxes hsbBefore and hsbAfter by dcdAdjust pixels along their scroll axis. |
| `HsbNextOnSbar` | `FUNCTION HsbNextOnSbar(hsb: THSb): THSb;` | Returns the next split-pane scroll box on the same scroll bar after hsb, or hsbNil if hsb is the last box on its scroll bar. |
| `HsbPrevOnSbar` | `FUNCTION HsbPrevOnSbar(hsb: THSb): THSb;` | Returns the preceding split-pane scroll box on the same scroll bar before hsb, or hsbNil if hsb is the head of its scroll bar. |
| `HsbSbarHead` | `FUNCTION HsbSbarHead(hsb: THSb): THSb;` | Walks backward from hsb to return the head scroll box (fHead = TRUE) of its scroll bar. |
| `HsbSbarTail` | `FUNCTION HsbSbarTail(hsb: THSb): THSb;` | Walks forward from hsb along the same scroll bar to return its tail (last) scroll box. |
| `FSbarHead` | `FUNCTION FSbarHead(hsb: THSb): TF;` | Returns TRUE if scroll box hsb is the head (first) scroll box of its scroll bar. |
| `SlideSbar` | `PROCEDURE SlideSbar(hsb: THSb; dcdAdjust: TCd);` | Translates every scroll box on the scroll bar containing hsb by dcdAdjust pixels perpendicular to its scroll axis. |
| `PaintSbar` | `PROCEDURE PaintSbar(hsb: THSb);` | Paints all scroll boxes from head to tail on the scroll bar containing hsb. |
| `EraseSbar` | `PROCEDURE EraseSbar(hsb: THSb);` | Erases the bounding rectangles of all scroll boxes from head to tail on the scroll bar containing hsb. |
| `SetupMvThumb` | `PROCEDURE SetupMvThumb(hsb: THSb);` | Saves the current pen state and caches shaft pixel limits and thumb geometry for scroll box hsb prior to MoveThumb calls. |
| `MoveThumb` | `PROCEDURE MoveThumb(cNewThumb: TC);` | Sets the thumb position of the scroll box prepared by SetupMvThumb to cNewThumb (0..1000) and repaints the old and new thumb rectangles if its pixel coordinate changed. |
| `DragThumb` | `PROCEDURE DragThumb(hsb: THSb; ptMouse: TPt; VAR cThumbUp: TC);` | Tracks the mouse while the button remains down to drag an XOR ghost outline of hsb's thumb within its shaft, moves the thumb on release, and returns the final 0..1000 position in cThumbUp. |
| `FixRLimits` | `PROCEDURE FixRLimits(hsb: THSb; VAR rLimits: TR);` | Populates the scroll-axis limits of rLimits to span either the entire scroll bar (when hsb is the head) or the adjacent pair hsbPrv..hsb for skewer dragging. |
| `DragSkewer` | `PROCEDURE DragSkewer(hsbDwn: THSb; ptMouse: TPt; rLimits: TR; VAR ptSkewerUp: TPt);` | Tracks the mouse while the button remains down to drag a gray XOR split-skewer line within rLimits for scroll box hsbDwn and returns the final skewer point in ptSkewerUp. |
| `HideSBorder` | `PROCEDURE HideSBorder(r: TR);` | Fills the right and bottom scroll-bar strips of rectangle r with white and frames the remaining content area. |

---

## Unit WmlStd

Defines shared QuickDraw type aliases and graphics-state save/restore helpers (PenSave, PenRestore, WmlTxtSave, WmlTxtRestore) used across the Window Manager Library.

- **Import**: `USES {$U WmlStd.obj} WmlStd;`
- **Unit kind**: `INTRINSIC` (`WMLSTD`)
- **Interface dependencies**: `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `PenSave` | `PROCEDURE PenSave;` | Saves the current QuickDraw port's pen state (GetPenState) into a module-level variable for a subsequent PenRestore. |
| `PenRestore` | `PROCEDURE PenRestore;` | Restores the current QuickDraw port's pen state (SetPenState) from the state last saved by PenSave. |
| `WmlTxtSave` | `PROCEDURE WmlTxtSave;` | Saves thePort's current text font, face, and mode and switches the port to WMFont, plain style, and SrcOr mode for WML symbol rendering. |
| `WmlTxtRestore` | `PROCEDURE WmlTxtRestore;` | Restores thePort's text font, face, and transfer mode to the values saved by WmlTxtSave. |
