# `SYS2LIB` (`Sys2lib.obj`) — Lisa System 2 Higher-Level Desktop, Editing, Alert & Print Manager Library

[Back to Library Index](LIBRARIES.md)

Lisa OS 1.0 second-tier GUI, text/scrap, and dialog runtime (`AlertMgr`, `FieldEdit`, `FldUt`, `FEDec`, `Scrap`, `UnitCs`, `UnitFf`, `UnitFile`, `UnitFmt`, `WmlStd`, `WmlCrs`, `WmlGrow`, `WmlSb`, `PrMgr`, `PrMgrUtil`, `Sys2Lock`). (In Workshop 2.0 these units merged into `SYS1LIB.obj`, while database/Table Manager became `sys2lib.obj`.)

- **Object file**: `libs/workshop1.0/Sys2lib.obj` (Intrinsic library (packed, no embedded `INTERFACE`))
- **Contents**: 16 units, 253 procedures/functions

> [!NOTE]
> `libs/workshop1.0/Sys2lib.obj` contains packed MC68000 code segments and `UnitBlock` headers for linking, without an `InterfLoc` block or embedded `INTERFACE` text (so `USES` cannot load its interfaces from `Sys2lib.obj` via `INTRINSIC.LIB`). On a Workshop 1.0 system, programs supply separate unit `.obj` interface files via `{$U ...}` (for example, `USES {$U QD/QuickDraw} QuickDraw;`) when compiling, and link against `Sys2lib.obj`. The routines and signatures below are cross-checked against the unpacked `Sys2lib.obj` binary.

## Importing and Linking

```pascal
USES {$U AlertMgr.obj} AlertMgr;
```

```sh
LISA_BOOT=libs/workshop1.0 pascal/lpc.py --2.0 --link=IOSPaslib,Sys1lib,Sys2lib MYPROG
```

## Units in This Library

| Unit | 8-Char Symbol | `USES` Dependencies | Routines | Summary |
|---|---|---|---|---|
| [`AlertMgr`](#unit-alertmgr) | `ALERTMGR` | `HWInt`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `FmgrUtil`, `SysCall`, `PSysCall`, `PMDecl`, `PMM`, `Events`, `Folders`, `Menus`, `Windows`, `WmlStd`, `WmlCrs`, `DBEnv` | 29 | Implements the Lisa Alert Manager for loading localized `.PHRASE` files, formatting parameterized alert messages and live counters, managing an LRU alert text cache, and displaying modal or background Ask, Caution, Note, Stop, and Wait alert boxes with rounded-rectangle buttons. |
| [`FEDec`](#unit-fedec) | `FEDEC` | `UnitStd`, `UnitHz`, `QuickDraw`, `FontMgr`, `Storage`, `DBEnv` | 0 | Declares shared constants and data structures for the Lisa Field Editor (`FieldEdit` and `FldUt`), including error codes (`fldFull`..`FENotUndoable`), alignment and style-change constants, edit operation tags (`noOp`..`formulaToValueOp`), selection/highlighting types (`interval`, `txSel`, `TtySel`, `TtyHilight`), and core editing records (`field`, `fieldState`, `run`, `undoInfo`, `ScrapRec`). |
| [`FieldEdit`](#unit-fieldedit) | `FIELDEDI` | `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `SysCall`, `Events`, `Folders`, `WmlStd`, `WmlSb`, `DBEnv`, `FEDec`, `Scrap`, `UnitFmt`, `PMDecl`, `PrStdInfo`, `UnitCs`, `FldUt` | 52 | Implements the single-line Lisa Field Editor for Office System applications and dialogs, supporting multi-run styled text, mouse point/word/drag selection, caret blinking, gap-buffer character and word editing, scrap/stream cut-copy-paste, and single-level undo. |
| [`FldUt`](#unit-fldut) | `FLDUT` | `UnitStd`, `UnitHz`, `QuickDraw`, `FontMgr`, `Storage`, `SysCall`, `Events`, `DBEnv`, `FEDec`, `PMDecl`, `PrStdInfo`, `UnitFmt`, `UnitCs`, `Scrap` | 2 | Bridges the Lisa Field Editor with the Universal Text (`UnitCs`) character stream architecture so field scrap data can be read sequentially as formatted text runs by other Office System tools. |
| [`PrMgr`](#unit-prmgr) | `PRMGR` | `UnitStd`, `SysCall`, `PMDecl`, `QuickDraw`, `Events`, `Windows`, `Folders`, `Menus`, `AlertMgr`, `PrStd`, `PrMgrUtil` | 10 | Implements core Print Manager initialization, shared data-segment binding, printer setup and job dialogs, alert presentation, and print record validation. Coordinates foreground applications with background printer processes via shared memory and event channels. |
| [`PrMgrUtil`](#unit-prmgrutil) | `PRMGRUTI` | `UnitStd`, `SysCall`, `PMDecl`, `PMM`, `QuickDraw`, `FontMgr`, `Menus`, `PrStd` | 13 | Provides Print Manager utility routines in `Sys2Lib` for querying available printers, reading and converting Parameter Memory printer configuration records, comparing and modifying `TPrRec` preferences, building long font IDs, and dispatching Print Manager folder menu commands. |
| [`Scrap`](#unit-scrap) | `SCRAP` | `UnitStd`, `UnitHz`, `SysCall`, `UnitFile`, `QuickDraw`, `FontMgr`, `Storage`, `Events`, `Folders`, `WmlStd`, `WmlSb`, `UnitFmt`, `PMDecl`, `PrStdInfo`, `UnitCs`, `UnitFigAtom`, `UnitFf` | 26 | Manages the shared inter-application Clipboard (Scrap), supporting application-specific scrap handles, QuickDraw universal pictures (ScrapUG), and formatted Universal Text control streams (ScrapCs). Provides process ownership transfer, two-segment undoable Cut/Copy transactions, and on-demand data-segment binding. |
| [`Sys2Lock`](#unit-sys2lock) | `SYS2LOCK` | `UnitStd`, `SysCall` | 5 | Provides segment-locking procedures (`LkWmlHot`, `LkSgAl`, `LkWml`, `LkFldSel`, and `LkFldEdit`) in `Sys2Lib` that pin Window Manager Library (`WML`), Alert Manager, and Field Editor intrinsic code segments in memory via Lisa OS segment management. |
| [`UnitCs`](#unit-unitcs) | `UNITCS` | `UnitStd`, `UnitHz`, `SysCall`, `Storage`, `QuickDraw`, `FontMgr`, `PMDecl`, `PrStdInfo`, `UnitFmt` | 22 | Implements the polymorphic Control Stream (TCs) framework used by LisaWrite, Field Editor, Scrap, and Universal Text to sequence runs and track logical position intervals (TLp, TInt) across formatted text, ruler, page, and figure streams. |
| [`UnitFf`](#unit-unitff) | `UNITFF` | `UnitStd`, `UnitHz`, `SysCall`, `UnitFile`, `QuickDraw`, `FontMgr`, `Storage`, `UnitFmt`, `PMDecl`, `PrStdInfo`, `UnitCs` | 11 | Implements formatted-file control streams (tycsFf, .LOTUS format) that read and write 512-byte pages containing text runs, character and paragraph formatting bytecodes, headers/footers, and embedded figure references. |
| [`UnitFile`](#unit-unitfile) | `UNITFILE` | `UnitStd`, `UnitHz`, `SysCall`, `PSysCall` | 16 | Provides fixed-block and virtual-object (TVofil) file I/O integrated with UnitHz named-object demand paging (FilCbOfN, FilFSwapInN, FilSwapOutN). |
| [`UnitFmt`](#unit-unitfmt) | `UNITFMT` | `UnitStd`, `UnitHz`, `QuickDraw`, `FontMgr` | 11 | Encodes, decodes, and applies compact formatting bytecodes (fop / rgfbc) that modify character style attributes (TArce), paragraph margins and spacing (TArpe), and tab-stop descriptors (TTbd). |
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

## Unit Sys2Lock

Provides segment-locking procedures (`LkWmlHot`, `LkSgAl`, `LkWml`, `LkFldSel`, and `LkFldEdit`) in `Sys2Lib` that pin Window Manager Library (`WML`), Alert Manager, and Field Editor intrinsic code segments in memory via Lisa OS segment management.

- **Import**: `USES {$U Sys2Lock.obj} Sys2Lock;`
- **Unit kind**: `INTRINSIC` (`SYS2LOCK`)
- **Interface dependencies**: `UnitStd`, `SysCall`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `LkWmlHot` | `PROCEDURE LkWmlHot(VAR err: INTEGER);` | Locks the Window Manager Library (`WML`) hot-path control intrinsic code segment (`WmlHot`) in memory, returning any Lisa OS error code in `err`. |
| `LkSgAl` | `PROCEDURE LkSgAl(VAR err: INTEGER);` | Locks the Alert Manager intrinsic code segment (`SgAl`) in memory, returning any Lisa OS error code in `err`. |
| `LkWml` | `PROCEDURE LkWml(VAR err: INTEGER);` | Locks the Window Manager Library (`WML`) intrinsic code segment (`Wml`) in memory, returning any Lisa OS error code in `err`. |
| `LkFldSel` | `PROCEDURE LkFldSel(VAR err: INTEGER);` | Locks the Field Editor selection-handling intrinsic code segment (`FldSel`) in `Sys2Lib` in memory, returning any Lisa OS error code in `err`. |
| `LkFldEdit` | `PROCEDURE LkFldEdit(VAR err: INTEGER);` | Locks the Field Editor text-editing intrinsic code segment (`FldEdit`) in `Sys2Lib` in memory, returning any Lisa OS error code in `err`. |

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
