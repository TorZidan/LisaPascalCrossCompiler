# `LCORBGLIB` (`lcorbglib.obj`) — LisaCalc & LisaGraph 2.0 Shared Calculation & Matrix Library

[Back to Library Index](LIBRARIES.md)

Shared Lisa Office System 2.0 spreadsheet and charting engine (`MatMgr`, `Parser`, `Compute`, `CoMgr`, `TEExec`, `LCFExec`, `FEGlobals`, `BGEnv`, `Stubs`) used by LisaCalc and LisaGraph.

- **Object file**: `libs/workshop2.0/lcorbglib.obj` (Intrinsic library (packed, no embedded `INTERFACE`))
- **Contents**: 9 units, 278 procedures/functions

> [!NOTE]
> `libs/workshop2.0/lcorbglib.obj` contains packed MC68000 code segments and `UnitBlock` headers for linking, without an `InterfLoc` block or embedded `INTERFACE` text (so `USES` cannot load its interfaces from `lcorbglib.obj` via `INTRINSIC.LIB`). On a Workshop 2.0 system, programs supply separate unit `.obj` interface files via `{$U ...}` (for example, `USES {$U QD/QuickDraw} QuickDraw;`) when compiling, and link against `lcorbglib.obj`. The routines and signatures below are cross-checked against the unpacked `lcorbglib.obj` binary.

## Importing and Linking

```pascal
USES {$U BGEnv.obj} BGEnv;
```

```sh
LISA_BOOT=libs/workshop2.0 pascal/lpc.py --2.0 --link=IOSPASLIB,IOSFPLIB,SYS1LIB,sys2lib,lcorbglib MYPROG
```

## Units in This Library

| Unit | 8-Char Symbol | `USES` Dependencies | Routines | Summary |
|---|---|---|---|---|
| [`BGEnv`](#unit-bgenv) | `BGENV` | `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `DBEnv`, `FEDec`, `FieldEdit`, `SysCall`, `Events` | 0 | Declares shared charting types, constants, and globals used jointly by LisaCalc and LisaGraph (Business Graphics), including `GraphTypes` (bar, stacked/solid bar, line, scatter, pie, area, and bar-line/scatter hybrids), `TitleNames`, `TAnotRec` annotation records, `tGraphProportion`, `AxisCntl` and `LegendCntl` descriptors, and refresh/editing state variables (`RefreshRect`, `BGRefreshRgn`, `GType`, `BGPreview`, `BGFld`, `XAxis`, `BarBoolean`, `RgrsBoolean`, `BGMarkFlag`). |
| [`CoMgr`](#unit-comgr) | `COMGR` | `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `DBEnv`, `FEDec`, `FieldEdit`, `TEEnv`, `SysCall`, `FPLib`, `PMDecl`, `PrStdInfo`, `PrPublic`, `MatMgr`, `Events`, `Folders`, `Menus`, `AlertMgr`, `WmlStd`, `WmlSb`, `WmlGrow`, `TM`, `FEGlobals`, `Scrap`, `MathLib` | 54 | Manages the LisaCalc and LisaGraph status panels and modeless dialog boxes, combining the Coordinates Display manager (`CoMgr`), Formula Display manager (`FormMgr`), Dialog Box manager (`DiMgr` and `AppDiBox`), and panel FieldEdit selection manager (`LCSMgr`). |
| [`Compute`](#unit-compute) | `COMPUTE` | `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `DBEnv`, `FEDec`, `FieldEdit`, `TEEnv`, `SysCall`, `FPLib`, `PMDecl`, `PrStdInfo`, `MatMgr`, `Parser`, `Events`, `WmlStd`, `WmlSb`, `TM`, `International`, `MathLib` | 1 | Evaluates compiled spreadsheet formulas (`lastFormula`) on the floating-point calculation stack for a given cell coordinate, resolving relative paste displacements, cell/range references, dates, and built-in functions. |
| [`FEGlobals`](#unit-feglobals) | `FEGLOBAL` | `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `DBEnv`, `FEDec`, `FieldEdit`, `TEEnv`, `SysCall`, `FPLib`, `PMDecl`, `PrStdInfo`, `PrPublic`, `MatMgr`, `Events`, `Folders`, `Menus`, `AlertMgr`, `WmlStd`, `WmlSb`, `WmlGrow`, `TM`, `Scrap` | 29 | Provides shared front-end globals, worksheet printing and automatic page-break calculation (`LCPr`), Alert Manager wrappers, scrap folder rendering, undo state tracking, and FieldEdit state serialization for LisaCalc and LisaGraph. |
| [`LCFExec`](#unit-lcfexec) | `LCFEXEC` | `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `DBEnv`, `FEDec`, `FieldEdit`, `TEEnv`, `SysCall`, `Psyscall`, `FPLib`, `PMDecl`, `PrStdInfo`, `PrPublic`, `MatMgr`, `Events`, `Folders`, `Menus`, `AlertMgr`, `WmlStd`, `WmlCrs`, `WmlSb`, `WmlGrow`, `TM`, `FEGlobals`, `CoMgr`, `TEExec`, `BGEnv`, `Scrap`, `LCUt`, `FilerComm` | 21 | Implements the shared Folder Executive event loop, process initialization, exception cleanup, panel layout/splitting, scroll bar rendering, and Business Graphics callback dispatch for LisaCalc and LisaGraph. |
| [`MatMgr`](#unit-matmgr) | `MATMGR` | `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `DBEnv`, `FEDec`, `FieldEdit`, `TEEnv`, `SysCall`, `Psyscall`, `FPLib`, `PMDecl`, `PrStdInfo`, `PrPublic`, `Events`, `Scrap`, `WmlStd`, `WmlSb`, `TM`, `International`, `UUniversalText`, `BGEnv` | 87 | Implements the sparse spreadsheet Matrix Manager shared by LisaCalc and LisaGraph, managing cell storage and reference counting, attributes and formats, formula compilation/decompilation and dependency recalculation, row/column snip widths and remapping, undo/scrap buffers, and matrix file I/O. |
| [`Parser`](#unit-parser) | `PARSER` | `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `DBEnv`, `FEDec`, `FieldEdit`, `TEEnv`, `SysCall`, `FPLib`, `PMDecl`, `PrStdInfo`, `MatMgr`, `International`, `MathLib`, `BGEnv` | 9 | Provides lexical/numeric packing utilities, coordinate range normalization, leap-year calculation, and buffered text-formatting output routines used by the spreadsheet formula parser and decompiler. |
| [`Stubs`](#unit-stubs) | `STUBS` | `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `GrafUtil`, `DBEnv`, `FEDec`, `FieldEdit`, `TEEnv`, `SysCall`, `FPLib`, `PMDecl`, `PrStdInfo`, `MatMgr`, `Parser`, `Events`, `Windows`, `Scrap`, `MathLib` | 44 | Provides diagnostic, tracing, memory-inspection, and interactive test-harness formatting routines for debugging Matrix Manager cells, compiled formulas, calculation stacks, floating-point environments, and paste-relative structures. |
| [`TEExec`](#unit-teexec) | `TEEXEC` | `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `DBEnv`, `FEDec`, `FieldEdit`, `TEEnv`, `SysCall`, `FPLib`, `PMDecl`, `PrStdInfo`, `PrPublic`, `MatMgr`, `Events`, `Folders`, `Menus`, `AlertMgr`, `WmlStd`, `WmlSb`, `WmlGrow`, `TM`, `FEGlobals`, `CoMgr`, `Scrap`, `BGEnv` | 33 | Bridges user interface menu commands, keyboard navigation, mouse selection/dragging, cell entry, recalculation triggers, and multi-operation undo between the Folder Executive, Table Manager, and Matrix Manager. |

---

## Unit BGEnv

Declares shared charting types, constants, and globals used jointly by LisaCalc and LisaGraph (Business Graphics), including `GraphTypes` (bar, stacked/solid bar, line, scatter, pie, area, and bar-line/scatter hybrids), `TitleNames`, `TAnotRec` annotation records, `tGraphProportion`, `AxisCntl` and `LegendCntl` descriptors, and refresh/editing state variables (`RefreshRect`, `BGRefreshRgn`, `GType`, `BGPreview`, `BGFld`, `XAxis`, `BarBoolean`, `RgrsBoolean`, `BGMarkFlag`).

- **Import**: `USES {$U BGEnv.obj} BGEnv;`
- **Unit kind**: `INTRINSIC` (`BGENV`)
- **Interface dependencies**: `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `DBEnv`, `FEDec`, `FieldEdit`, `SysCall`, `Events`

*This unit exports constants, data types, and/or global variables only (no callable procedures or functions).*

---

## Unit CoMgr

Manages the LisaCalc and LisaGraph status panels and modeless dialog boxes, combining the Coordinates Display manager (`CoMgr`), Formula Display manager (`FormMgr`), Dialog Box manager (`DiMgr` and `AppDiBox`), and panel FieldEdit selection manager (`LCSMgr`).

- **Import**: `USES {$U CoMgr.obj} CoMgr;`
- **Unit kind**: `INTRINSIC` (`COMGR`)
- **Interface dependencies**: `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `DBEnv`, `FEDec`, `FieldEdit`, `TEEnv`, `SysCall`, `FPLib`, `PMDecl`, `PrStdInfo`, `PrPublic`, `MatMgr`, `Events`, `Folders`, `Menus`, `AlertMgr`, `WmlStd`, `WmlSb`, `WmlGrow`, `TM`, `FEGlobals`, `Scrap`, `MathLib`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `clrUndo` | `procedure clrUndo;` | Releases Matrix Manager undo buffers (and private cell scrap if no longer owned), accepts inherited scrap, and resets undo state to `uNothing` before a new operation. |
| `DiBoxScroll` | `procedure DiBoxScroll(where: point; myhsbHit: Thsb; myIconHit: TIcon);` | Handles scroll-bar arrow, page, or thumb scrolling (`myhsbHit`, `myIconHit`) inside a scrollable dialog box such as the Function Hints box. |
| `disMissDi` | `procedure disMissDi(menu: integer; menuIndex: Integer; var response: diResponse);` | Evaluates whether menu selection `(menu, menuIndex)` is permitted while a dialog box is open, returning `OkAction`, `IgnoreAction`, or `DiGone` after dismissing the dialog. |
| `initDiFlds` | `procedure initDiFlds;` | Allocates the four reusable dialog-box FieldEdit text fields (`diHfld[1..4]`) and their field-state handles at startup. |
| `putCWidPrecBox` | `procedure putCWidPrecBox(diBox: diBoxKind; initStr: resultStr);` | Opens a prompt dialog box querying either column width or decimal precision (`diBox`), initialized with default value string `initStr`. |
| `PutFuncHints` | `procedure PutFuncHints(InitBoxSize: integer);` | Opens a scrollable dialog box of height `InitBoxSize` displaying built-in spreadsheet function syntax hints. |
| `putRepBox` | `procedure putRepBox;` | Opens the interactive Paste Relative (Replicate) dialog box for choosing relative versus absolute coordinate references across pasted formulas. |
| `removeDiBox` | `procedure removeDiBox;` | Highlights the Go-Away button briefly, cleans up state for the active dialog box kind, and removes the dialog box from screen. |
| `ButLeftEdge` | `function ButLeftEdge: integer;` | Calculates and returns the horizontal pixel coordinate for right-aligning standard action buttons inside `DialogFolder`. |
| `CoMgStuff` | `procedure CoMgStuff(mode: FIOKind; lcVer: integer; VAR status: integer);` | Serializes or restores the Formula Display's FieldEdit field and state during document suspend/unsuspend when `formPnl` is active. |
| `drawCo` | `procedure drawCo;` | Draws the Coordinates Display FieldEdit field (`coFldH`) inside the coordinates status panel (`coPnl`). |
| `emptyCoDisp` | `procedure emptyCoDisp;` | Clears all text and resets the selection state in the Coordinates Display field (`coFldH`). |
| `getCoRg` | `procedure getCoRg(var coRg: range; var status: integer; var errRec: errRecord);` | Parses the text currently in the Coordinates Display field via `CellRange` into `coRg`, returning parse `status` and `errRec`. |
| `getRgName` | `procedure getRgName(rg: range; rgNameX: ptrData; var numBytes: integer);` | Formats cell/table range `rg` into its textual coordinate or range name (such as `A1` or `B2..D5`) in `rgNameX^`, returning its byte length in `numBytes`. |
| `initCo` | `procedure initCo;` | Allocates and initializes the FieldEdit fields and states for both the main Coordinates Display (`coFldH`) and the Scrap Coordinates Display (`ScoFldH`). |
| `reDrawCo` | `procedure reDrawCo;` | Updates the Coordinates Display field bounds from `coPnl`'s current rectangle and redraws the coordinates text. |
| `shoNewCo` | `procedure shoNewCo(aRg: range);` | Formats range `aRg` into textual coordinates and displays it in the Coordinates Display panel. |
| `addDiBox` | `procedure addDiBox(height: integer; DoItProcX, GoAwayProcX: procPtr; addScrollBars, checkboxes: boolean);` | Opens the dialog box panel at `height` pixels with optional Do-It (`DoItProcX`) and Go-Away (`GoAwayProcX`) callbacks, scroll bars, and checkboxes. |
| `findDiPart` | `procedure findDiPart(var pt: point; var fKind: fldKind; var pnlFldH: hndField; var pnlFSH: hndFstate; var specProcX: procPtr);` | Hit-tests dialog-panel point `pt` to identify the `fldKind` (`plainTxt`, `BtnArea`, `aChkRow`, or `noSel`) and returns the corresponding field handles or checkbox callback. |
| `initDi` | `procedure initDi;` | Resets Dialog Box Manager counters for fields, labels, checkbox rows, buttons, and custom graphics callbacks to empty. |
| `putDiFld` | `procedure putDiFld(fldH: hndField; fsH: hndFstate; var status: integer);` | Registers editable FieldEdit field `(fldH, fsH)` in the active dialog box's tab-order list and draws it in `dialogPnl`. |
| `putDiLbl` | `procedure putDiLbl(lblX: lblFldX);` | Registers static label descriptor `lblX` in the active dialog box and renders its label text. |
| `PutGraphics` | `Procedure PutGraphics(GrafProcX: ProcPtr);` | Registers custom dialog drawing callback `GrafProcX` and invokes it immediately (and on subsequent dialog redraws) to render non-field graphics. |
| `reDrawDi` | `procedure reDrawDi;` | Redraws the entire active dialog box, including custom graphics, static labels, editable fields, checkboxes, and buttons. |
| `rmvDiBox` | `procedure rmvDiBox;` | Collapses the dialog box height to zero, hides dialog buttons, resets Dialog Box Manager structures, and restores focus to `tblPnl`. |
| `setDiPnl` | `procedure setDiPnl;` | Initializes the dialog box panel state with a zero pixel height during document open/close setup. |
| `drawForm` | `procedure drawForm;` | Draws the Formula Display FieldEdit field (`formFldH`) inside the formula status panel (`formPnl`). |
| `endRgInsert` | `procedure endRgInsert;` | Clears the remembered formula range-insertion interval (`rgIntrvl`) so subsequent Option-clicked range names insert at the caret rather than replacing the last inserted range. |
| `enterForm` | `procedure enterForm(rowId, colId: idType; var status: integer; var errRec: errRecord);` | Submits the formula text in `formFldH` to the Matrix Manager (`CellFormula`) for cell `(rowId, colId)`, returning compilation `status` and `errRec`. |
| `emptyFormDisp` | `procedure emptyFormDisp;` | Clears all text and resets FieldEdit state in the Formula Display panel (`formFldH`). |
| `initForm` | `procedure initForm;` | Allocates and initializes the Formula Display FieldEdit field (`formFldH`), disables formula editing initially, and clears range-insertion state. |
| `newFormRg` | `procedure newFormRg(formRg: range; var status: integer);` | Formats range `formRg` as a textual range reference and inserts it into the Formula Display (replacing `rgIntrvl` if active or inserting at the current selection). |
| `reDrawForm` | `procedure reDrawForm;` | Updates `formFldH` coordinates to match `formPnl`'s current rectangle and redraws the Formula Display. |
| `shoNewForm` | `procedure shoNewForm(rowId, colId: idType);` | Decompiles and displays the formula (if any) of cell `(rowId, colId)` in the Formula Display panel and enables formula editing. |
| `doPnlAct` | `procedure doPnlAct(Activate: boolean);` | Activates or deactivates visual selection highlighting in the status/dialog panel managed by `LCSMgr` upon folder activation or deactivation. |
| `doPnlSel` | `procedure doPnlSel(pnl: pnlIndex; pnlPoint: point; var nbh: rect; var timeout: integer);` | Starts a mouse selection, button press, or checkbox toggle at `pnlPoint` inside status/dialog panel `pnl`, returning drag neighborhood `nbh` and blink `timeout`. |
| `endOtherSel` | `procedure endOtherSel(pnl: pnlIndex);` | Ends any FieldEdit text selection and visual feedback in panel `pnl` without disturbing `LCSMgr`'s active panel tracking. |
| `endPnlSel` | `procedure endPnlSel;` | Ends the active FieldEdit text selection and removes screen highlighting in the current `LCSMgr` status or dialog panel while retaining field text. |
| `GetPnlFldKind` | `procedure GetPnlFldKind(var theFldKind: fldKind);` | Returns the `fldKind` (`plainTxt`, `noSel`, `BtnArea`, or `aChkRow`) of the current selection in `LCSMgr`. |
| `jumpAField` | `procedure jumpAField(dir: moveDir; var timeout: integer);` | Moves the text selection forward or backward (`dir`) to the next or previous editable field in the active dialog box and selects all of its text. |
| `LCSMStuff` | `procedure LCSMStuff(mode: FIOKind; lcVer: integer; VAR status: integer);` | Restores `LCSMgr` panel selection state (reconnecting `formPnl` on unsuspend or resetting to `nullPnlSel` on open) during file open/unsuspend. |
| `nullPnlSel` | `procedure nullPnlSel;` | Resets `LCSMgr` selection tracking to `nullPnl` and `noSel` with nil field handles. |
| `nullSelIn` | `procedure nullSelIn(pnl: pnlIndex);` | Clears `LCSMgr` selection state via `nullPnlSel` if the active panel selection currently resides in `pnl`. |
| `newNbhPnl` | `procedure newNbhPnl(pnlPoint: point; var nbh: rect; var timeout: integer);` | Extends the active FieldEdit text selection or tracks button/checkbox state when the mouse drags to `pnlPoint` in a status or dialog panel. |
| `peekAtNewSel` | `procedure peekAtNewSel(pnl: pnlIndex; pnlPoint: point; var fKind: fldKind);` | Determines what `fldKind` would be hit if the mouse went down at `pnlPoint` inside status or dialog panel `pnl` without altering state. |
| `pnlEdit` | `procedure pnlEdit(editKind: editType; var status: integer);` | Performs a Cut, Copy, Paste, or Clear (`editKind`) on the plain-text FieldEdit selection in the active status or dialog panel. |
| `pnlKey` | `procedure pnlKey(ch: char; shiftflag: boolean; var timeout: integer; var status: integer);` | Inserts or deletes character `ch` (handling Backspace and Shift-Backspace forward delete) in the active status or dialog panel's FieldEdit field. |
| `pnlMseUp` | `procedure pnlMseUp(pnlPoint: point; var timeout: integer; var newSel: boolean);` | Completes a mouse-up at `pnlPoint` in the active status or dialog panel (starting caret blink or firing a clicked button/checkbox) and sets `newSel`. |
| `pnlSelAll` | `procedure pnlSelAll(pnl: pnlIndex; var timeout: integer);` | Selects all text in the editable field of status or dialog panel `pnl` and returns the caret blink `timeout`. |
| `pnlSelFld` | `procedure pnlSelFld(var timeout: integer);` | Selects all text in the current `LCSMgr` plain-text field (such as on a triple-click) and returns the updated `timeout`. |
| `pnlTimOut` | `procedure pnlTimOut(var timeout: integer);` | Handles timer events for the active status or dialog panel field by redrawing invalidated text or blinking the insertion caret. |
| `pnlUndo` | `procedure pnlUndo(pnl: pnlIndex; var status: integer);` | Undoes the most recent FieldEdit edit in status or dialog panel `pnl` and redraws the field. |
| `pnlWSel` | `procedure pnlWSel(P: point; var nbh: rect; var timeout: integer);` | Selects the entire word surrounding point `P` on a double-click in the active status or dialog panel field, returning `nbh` and `timeout`. |
| `shoPnlErr` | `procedure shoPnlErr(pnl: pnlIndex; status: integer; errRec: errRecord; var timeout: integer);` | Highlights the offending character interval (`errRec.errSpot`) inside panel `pnl` and displays the associated syntax/parse error alert. |

---

## Unit Compute

Evaluates compiled spreadsheet formulas (`lastFormula`) on the floating-point calculation stack for a given cell coordinate, resolving relative paste displacements, cell/range references, dates, and built-in functions.

- **Import**: `USES {$U Compute.obj} Compute;`
- **Unit kind**: `INTRINSIC` (`COMPUTE`)
- **Interface dependencies**: `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `DBEnv`, `FEDec`, `FieldEdit`, `TEEnv`, `SysCall`, `FPLib`, `PMDecl`, `PrStdInfo`, `MatMgr`, `Parser`, `Events`, `WmlStd`, `WmlSb`, `TM`, `International`, `MathLib`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `calculate` | `procedure calculate(var calcResult: valueType; rowId, colId: integer);` | Decodes and evaluates the compiled p-code formula in `lastFormula` at cell `(rowId, colId)` (resolving relative coordinates, ranges, operators, and functions) and returns the result in `calcResult`. |

---

## Unit FEGlobals

Provides shared front-end globals, worksheet printing and automatic page-break calculation (`LCPr`), Alert Manager wrappers, scrap folder rendering, undo state tracking, and FieldEdit state serialization for LisaCalc and LisaGraph.

- **Import**: `USES {$U FEGlobals.obj} FEGlobals;`
- **Unit kind**: `INTRINSIC` (`FEGLOBAL`)
- **Interface dependencies**: `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `DBEnv`, `FEDec`, `FieldEdit`, `TEEnv`, `SysCall`, `FPLib`, `PMDecl`, `PrStdInfo`, `PrPublic`, `MatMgr`, `Events`, `Folders`, `Menus`, `AlertMgr`, `WmlStd`, `WmlSb`, `WmlGrow`, `TM`, `Scrap`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `lcprFmt` | `procedure lcprFmt;` | Displays the Print Manager's Format for Printing dialog (`PrPrfDlg`) and, if printer preferences changed, resolves table fonts and reconfigures Business Graphics. |
| `lcprinit` | `procedure lcprinit;` | Performs one-time initialization of the Print Manager (`PrMgrInit`), axis-to-snip mappings, and default worksheet print margins for the process. |
| `lcPrint` | `procedure lcPrint(selOnly: boolean; thePRmode: PrMenuSuppress);` | Runs the Print Instance dialog (`FPrInsDlg`) and prints either the entire worksheet or the current selection (`selOnly`). |
| `LCReDoBreaks` | `procedure LCReDoBreaks;` | Recomputes all automatic row and column page breaks across the worksheet based on current paper printable dimensions and snip widths. |
| `resolveFont` | `procedure resolveFont;` | Synchronizes printer font metrics with the current printer configuration, updating the table display font when `Printer Font` display mode is active. |
| `FamFromIndex` | `function FamFromIndex(index: integer): TFam;` | Maps a font-menu index constant (`FC10`, `FC12`, `FT10`, `FT12`, `FT15`, `FT20`) to its corresponding Font Manager family ID (`TFam`). |
| `FinalDataSnip` | `function FinalDataSnip(aKind: SnipKind): idtype;` | Finds and returns the highest row or column snip ID (`aKind`) that contains non-blank cell contents (or `mInfSnip` if the table is empty). |
| `ClrScrapFld` | `procedure ClrScrapFld;` | Syncs the scrap panel size, erases the `ScrapFolder` port rectangle, and updates its scroll bars. |
| `cWidened` | `procedure cWidened(undoable: boolean);` | Records `uColWid` undo state (if `undoable` is `true`), posts undo menu wording, and recomputes page breaks after a column grid line is dragged. |
| `doCautionAlert` | `function doCautionAlert(alertNum: integer): boolean;` | Displays caution alert `alertNum` from `allAlerts`, refreshes the document folder afterward, and returns the user's boolean confirmation. |
| `doDTalert` | `procedure doDTalert(DTM: longint; var whenString: TParamAlert);` | Formats modification timestamp `DTM` into alert parameter string `whenString` via the Alert Manager's `DTAlert`. |
| `doPnlDrawAlert` | `procedure doPnlDrawAlert(alertNum: integer; pnl: pnlIndex);` | Draws non-modal status alert message `alertNum` centered inside panel `pnl` (such as during file loading or activation). |
| `doGetAlert` | `procedure doGetAlert(alertNum: integer; MessPtr: TPStr255);` | Retrieves alert message string `alertNum` from `allAlerts` into `MessPtr^` without displaying an alert box. |
| `doNoteALert` | `procedure doNoteALert(alertNum: integer);` | Displays informational Note alert `alertNum` and triggers a folder update when dismissed. |
| `doParamAlert` | `procedure doParamAlert(maxNum: integer);` | Formats integer `maxNum` as a string and substitutes it as the first parameter (`^0`) for the next alert via `ParamAlert`. |
| `doReadALert` | `procedure doReadALert(alertRefNum, alertVerNum: integer);` | Reads the application's compiled alert phrase file (`alertRefNum`, `alertVerNum`) into `allAlerts`. |
| `doStopALert` | `procedure doStopALert(alertNum: integer);` | Displays modal Stop alert `alertNum` and refreshes the document folder afterward. |
| `doWaitALert` | `procedure doWaitALert(alertNum: integer);` | Displays non-dismissable Wait alert `alertNum` and refreshes the document folder when cleared. |
| `doWouldALert` | `procedure doWouldALert(alertNum: integer);` | Updates Edit-menu Undo item phrasing via `WouldAlert` for alert phrase `alertNum`. |
| `DrwScrScrollBars` | `procedure DrwScrScrollBars(state: boolean);` | Paints or hides the horizontal/vertical scroll bars and grow icon inside `ScrapFolder` depending on `state` and folder activation. |
| `FailedAlert` | `procedure FailedAlert;` | Displays Stop alert #2 to notify the user that an Alert Manager operation failed. |
| `getKeyPair` | `procedure getKeyPair(var Keys: keyPair);` | Extracts the ASCII key and modifier state (`shftKey`, `cmdKey`, `specKey`, or `noKey`) from the latest `WMEvent` into `Keys`. |
| `GetScrKind` | `procedure GetScrKind(var sKind: scrapKind);` | Queries the global Scrap Manager and maps the current scrap format into `scrapKind` (`txtKind`, `cellsKind`, `graphKind`, or `noKind`). |
| `GetWordInfo` | `procedure GetWordInfo(MessPtr: TPStr255);` | Retrieves localized UI label string #11 from `allAlerts` into `MessPtr^`. |
| `PackField` | `Procedure PackField(HFld: hndField; HFS: hndFState; HBuffer: hnddata; var bufLen: integer; var lenInstalled: integer);` | Serializes a FieldEdit field (`HFld`), its `fieldState` (`HFS`), text bytes, and formatting runs into relocatable data handle `HBuffer` (growing it if needed). |
| `putSysStr` | `procedure putSysStr(h, v: integer; strng: str80);` | Draws string `strng` at `(h, v)` in the system font, substituting any `'\|'` character with the Lisa Apple/Command symbol from `WMfont`. |
| `setUndo` | `procedure setUndo(op: undoOpKind; pnl: pnlIndex);` | Records undoable operation kind `op` and target panel `pnl` in `undoRec`. |
| `shoScrapFld` | `procedure shoScrapFld;` | Clears `ScrapFolder`, renders the current universal-text/FieldEdit scrap via `DrawScrap`, and draws scrap scroll bars. |
| `UnpackField` | `Procedure UnpackField(HFld: HndField; HFS: HndFState; HBuffer: HndData);` | Restores a FieldEdit field (`HFld`), its `fieldState` (`HFS`), text data, and formatting runs from a buffer previously packed by `PackField`. |

---

## Unit LCFExec

Implements the shared Folder Executive event loop, process initialization, exception cleanup, panel layout/splitting, scroll bar rendering, and Business Graphics callback dispatch for LisaCalc and LisaGraph.

- **Import**: `USES {$U LCFExec.obj} LCFExec;`
- **Unit kind**: `INTRINSIC` (`LCFEXEC`)
- **Interface dependencies**: `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `DBEnv`, `FEDec`, `FieldEdit`, `TEEnv`, `SysCall`, `Psyscall`, `FPLib`, `PMDecl`, `PrStdInfo`, `PrPublic`, `MatMgr`, `Events`, `Folders`, `Menus`, `AlertMgr`, `WmlStd`, `WmlCrs`, `WmlSb`, `WmlGrow`, `TM`, `FEGlobals`, `CoMgr`, `TEExec`, `BGEnv`, `Scrap`, `LCUt`, `FilerComm`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `InitBGprocs` | `procedure InitBGprocs(AnotSelect: ProcPtr; BGDown: ProcPtr; BGExit: ProcPtr; BGGetThumb: ProcPtr; BGKey: ProcPtr; BGMenuCommand: ProcPtr; BGMove: ProcPtr; BGNewRgImg: ProcPtr; BGScroll: ProcPtr; BGSetGrfx: ProcPtr; BGTmOut: ProcPtr; BGUp: ProcPtr; DOBGAct: ProcPtr; DrawGraph: ProcPtr; EraseBG: ProcPtr; FxBGStuff: ProcPtr; InitBGPnl: ProcPtr; InitBGStorage: ProcPtr; TtlSelect: ProcPtr; BGReConFig: ProcPtr; BGrgChged: ProcPtr; FxBgFree: ProcPtr);` | Registers the twenty-two Business Graphics (LisaGraph) callback procedure pointers invoked by the shared Folder Executive when running as LisaGraph. |
| `lcGrafErrProc` | `procedure lcGrafErrProc(errNum: integer);` | Handles fatal QuickDraw graphics errors (`errNum`) by halting the process. |
| `LastWishes` | `procedure LastWishes(environPtr: P_env_blk; excepDataPtr: P_ex_data);` | Executes the `Sys_Terminate` exception handler on normal or abnormal process exit to clean up open resources and notify the Filer. |
| `lcBGReConFig` | `procedure lcBGReConFig;` | Invokes the registered Business Graphics `BGReConfig` callback after page setup or panel configuration changes. |
| `lcBGSetGrfx` | `procedure lcBGSetGrfx;` | Invokes the registered Business Graphics `BGSetGrfx` callback to configure graph port/layout state. |
| `LCBGmainloop` | `procedure LCBGmainloop;` | Runs the main event and idle/caret-timeout loop shared by LisaCalc and LisaGraph until termination. |
| `NewInitFexec` | `procedure NewInitFexec(var initStatus: integer);` | Performs one-time process initialization of heaps, data segments, menus, alerts, panels, Matrix Manager, Table Manager, and printing for LisaCalc or LisaGraph. |
| `ProcessEvent` | `procedure ProcessEvent;` | Dispatches the current Window Manager event (`WMEvent`)—mouse down/up, key, menu, scroll, folder activate/deactivate, update, or Filer message—to the appropriate handler. |
| `chgStatPnl` | `procedure chgStatPnl(keepFormula: boolean);` | Updates the Coordinates Display, Formula Display, and menu states in the status panel to reflect a newly selected current range. |
| `chkScrapSize` | `procedure chkScrapSize;` | Synchronizes `cScrapPnl`'s dimensions with `ScrapFolder^.portRect` whenever the Scrap window has been resized. |
| `dividPnls` | `procedure dividPnls;` | Draws panel divider lines and static panel title labels (such as coordinates, formula, and wide-angle headings) inside the document folder. |
| `doGoTo` | `procedure doGoTo(newRange: range);` | Scrolls the table to bring `newRange` into view, selects it (when in values mode), and sets undo state to `uGoTo`. |
| `editTried` | `procedure editTried(status: integer);` | Synchronizes inter-panel displays, scrolls the edited cell into view if needed, or displays an error alert after a keystroke or clipboard edit returning `status`. |
| `fxNewRgImg` | `procedure fxNewRgImg;` | Notifies Business Graphics via `BGNewRgImg` to recompute data bounds and replot the graph when Matrix Manager values change. |
| `fxRgChged` | `procedure fxRgChged(rg: range);` | Notifies Business Graphics when a cell range `rg` has been redrawn or modified. |
| `setApp2Pnls` | `procedure setApp2Pnls;` | Recalculates widths, heights, and offsets of all status, table, wide-angle, and graph panels when `FolderPnl` is resized or split. |
| `shoNewRx` | `procedure shoNewRx(oldRg: range; newRg: range; just: rgJust);` | Scrolls the table view via `shoNewRg` so `newRg` is visible with justification `just` and updates the table scroll-bar thumb positions. |
| `BGSetThumb` | `procedure BGSetThumb;` | Queries current Business Graphics thumb positions via `BGGetThumb` and updates `BGHsbH` and `BGHsbV` without repainting the scroll bars. |
| `BGDrawScrolls` | `procedure BGDrawScrolls;` | Positions and paints both the table scroll bars (`LCDrawScrolls`) and the Business Graphics horizontal/vertical scroll bars. |
| `LCDrawScrolls` | `procedure LCDrawScrolls;` | Positions and paints the table horizontal, vertical, and split-gray scroll bars along with the folder grow icon. |
| `updFolder` | `procedure updFolder(forceUpdate: boolean);` | Services an update event for the document folder, scrap folder, or dialog folder by redrawing invalidated status, table, dialog, and Business Graphics regions. |

---

## Unit MatMgr

Implements the sparse spreadsheet Matrix Manager shared by LisaCalc and LisaGraph, managing cell storage and reference counting, attributes and formats, formula compilation/decompilation and dependency recalculation, row/column snip widths and remapping, undo/scrap buffers, and matrix file I/O.

- **Import**: `USES {$U MatMgr.obj} MatMgr;`
- **Unit kind**: `INTRINSIC` (`MATMGR`)
- **Interface dependencies**: `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `DBEnv`, `FEDec`, `FieldEdit`, `TEEnv`, `SysCall`, `Psyscall`, `FPLib`, `PMDecl`, `PrStdInfo`, `PrPublic`, `Events`, `Scrap`, `WmlStd`, `WmlSb`, `TM`, `International`, `UUniversalText`, `BGEnv`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `aRgInScrap` | `function aRgInScrap(value: ptrData; wideFlg: boolean; var numBytes: integer): boolean;` | Returns `true` if the local scrap contains matrix cells and copies the formatted text of the scrap's top-left cell into `value` (updating `numBytes`). |
| `allocBlock` | `function allocBlock(numBytes: integer): THContents;` | Allocates a `numBytes`-byte relocatable block in the matrix heap zone (`mxHz`), increments `numHandles`, and returns its `THContents` handle (or `nil` on failure). |
| `CellAttr` | `procedure CellAttr(rowId, colId: idType; var attrRec: attrRecord);` | Reads and unpacks the alignment, numeric/money format, decimal places, protection, and highlight attributes of cell `(rowId, colId)` (or blank-cell defaults) into `attrRec`. |
| `CellBit` | `function CellBit(rowId, colId: idType; bitNum: bitKind): boolean;` | Returns the boolean state of status/marker flag `bitNum` (such as `BInvalid`, `BCircle`, `B1Marked`, `B2Marked`, or `BCellSeen`) for cell `(rowId, colId)`. |
| `CellBlank` | `function CellBlank(rowId, colId: idType): boolean;` | Returns `true` if cell `(rowId, colId)` is unallocated or has no stored value (`oh = 0`). |
| `CellContents` | `procedure CellContents(mode: IOModeType; rowId, colId: idType; fullinfo: boolean; var cnRec: cnRecord; var status: integer);` | Reads and unpacks (`mmRead`, full or abbreviated via `fullinfo`) or packs and writes (`mmWrite`) cell contents record `cnRec` at `(rowId, colId)`. |
| `CellFlags` | `procedure CellFlags(rowId, colId: idType; var attr: TAttr);` | Returns the packed attribute bitfield `TAttr` for cell `(rowId, colId)` (or blank-cell default attributes if unallocated). |
| `CellHasRule` | `function CellHasRule(rowId, colId: idType): boolean;` | Returns `true` if cell `(rowId, colId)` has a compiled formula (`pkHasRule`) associated with it. |
| `CellHasValue` | `function CellHasValue(rowId, colId: idType): boolean;` | Returns `true` if cell `(rowId, colId)` currently holds a numeric value (`tNumber`). |
| `CellInterval` | `procedure CellInterval(rowId, colId: idType; formula: ptrData; PRdata: TPPRrecord; relstr: boolean; var numBytes: integer; resetPRdata: boolean);` | Decompiles the formula at `(rowId, colId)` into `formula` (up to `numBytes` chars) in relative or absolute form (`relstr`) and records coordinate character intervals in `PRdata`. |
| `CellRange` | `procedure CellRange(coordinate: ptrData; numBytes: integer; var result: range; var status: integer; var error: errRecord);` | Parses `numBytes` characters of coordinate/range text at `coordinate` into logical `range` `result`, returning parse `status` and `error` details. |
| `CellType` | `procedure CellType(rowId, colId: idType; var result: cellKind);` | Returns the data kind (`tBlank`, `tNumber`, `tText`, `tDate`, `tPage`, etc.) of cell `(rowId, colId)` in `result`. |
| `ChangeBlockSize` | `procedure ChangeBlockSize(hContents: THContents; newSize: longint; noSizeErr: boolean; var status: integer);` | Resizes matrix heap handle `hContents` to `newSize` bytes (enforcing the 32,000-byte limit unless `noSizeErr` is `true`) and returns `status`. |
| `claimUndoBuffer` | `procedure claimUndoBuffer(reclaim: boolean);` | Commits pending format/width/break undo state into the matrix and reclaims cell and formula handles stored in the undo or scrap buffer (`FBufPtr`). |
| `clearBuffers` | `procedure clearBuffers(claimScrap: boolean);` | Reclaims memory held by the Matrix Manager's undo buffer (and also its private cell scrap if `claimScrap` is `true`) before starting a new operation. |
| `CloseMatrix` | `procedure CloseMatrix(fileName: PtrStrType; closeInfo: FIOKind; DTC: longint; checkAbort: boolean; var status: integer);` | Serializes the matrix cells, row/column attribute and break vectors, Table Manager view bands, and front-end state (`FxDataStuff`) to file `fileName`. |
| `ClrFormErrors` | `procedure ClrFormErrors;` | Restores formula cell/range references that were marked as move-errors back to their original coordinates when an in-progress cut/move is canceled or overwritten. |
| `convertformula` | `procedure convertformula(rowId, colId: idType; pFormula: TPFmla);` | Converts all shared paste-relative displacement coordinates and ranges in `pFormula` at `(rowId, colId)` into direct cell references. |
| `CoordInRange` | `function CoordInRange(rowId, colId: idType; rg: range): boolean;` | Returns `true` if cell coordinate `(rowId, colId)` falls inclusively within range `rg`. |
| `dateString` | `procedure dateString(date: dateType; var result: resultStr);` | Formats `date` into `result` according to international date order and delimiter pattern `dataFormat.dateFormat`. |
| `DecRefCnt` | `procedure DecRefCnt(hContents: THContents; inrule: boolean; claimData: boolean);` | Decrements the reference count of formula (`inrule = true`) or cell-value handle `hContents` and frees the handle back to `mxHz` when its count reaches zero. |
| `displaycell` | `procedure displaycell(rowId, colId: integer);` | Triggers a table redraw of single cell `(rowId, colId)` if the cell is currently visible according to `SnipVis`. |
| `DisplayRange` | `procedure DisplayRange(rg: range);` | Requests the Table Manager (`NewRgImg`) to redraw `rg` and notifies Business Graphics (`FxRgChged`) when running in LisaGraph. |
| `expandrange` | `procedure expandrange(var rg: range; whole: boolean);` | Expands open-ended (`mInfSnip` / `pInfSnip`) row or column bounds in `rg` to concrete `1..idMax` (if `whole` is `true`) or `1..lastSnip` bounds. |
| `FBufClose` | `procedure FBufClose(var status: integer);` | Flushes any buffered output and closes the active Matrix Manager I/O stream (`oDisk`, `oScrap`, or `oMem`). |
| `FBufInit` | `procedure FBufInit(mode: IOModeType; buffertype: IOtype; filename: PtrStrType; usePassWord: boolean; var status: integer);` | Initializes buffered Matrix Manager reading or writing (`mode`) targeting a disk file, scrap segment, undo memory block, or in-memory buffer (`buffertype`). |
| `FBufStuff` | `procedure FBufStuff(sizekind: FBufKind; value: ptrData; var length, status: integer);` | Reads or writes `length` bytes of data at `value` (according to record framing `sizekind`) through the active Matrix Manager buffered I/O stream. |
| `FinalSnip` | `function FinalSnip(snip: snipKind): integer;` | Returns the highest allocated row or column snip ID (`CT^.lastSnip[snip]`) in the active matrix or scrap table. |
| `FindPCel` | `function FindPCel(rowId, colId: idType; canCreate: boolean): TPCel;` | Looks up and returns a direct pointer (`TPCel`) to cell `(rowId, colId)` in the active matrix or scrap, allocating the row vector and cell if `canCreate` is `true`. |
| `FixRange` | `procedure FixRange(var rg: range);` | Normalizes the row and column endpoints of `rg` (setting `mInfSnip`/`pInfSnip` or matching single-cell/heading coordinates) to match `rg.rKind`. |
| `FxDataStuff` | `procedure FxDataStuff(mode: FIOkind; verNumPres: boolean; var status: integer);` | Reads or writes LisaCalc/LisaGraph Folder Executive, Coordinates/Formula panel, Selection Manager, printing, and graph state via `FBufStuff` during file open/close/suspend. |
| `GetModeInfo` | `procedure GetModeInfo(var flags: ModeInfo);` | Populates `flags` (`ModeInfo`) with current Matrix Manager settings including find flags, print options, recalculation mode, circle mode, show-formulas state, table font, and `AppKind`. |
| `GetPRcoords` | `procedure GetPRcoords(var rowId, colId: integer);` | Replaces `(rowId, colId)` with the base cell coordinates (`lastformula.row`, `lastformula.col`) of the shared formula at that cell. |
| `GetRefCnt` | `function GetRefCnt(hContents: THContents; inrule: boolean): integer;` | Returns the current reference count of shared formula (`inrule = true`) or cell data handle `hContents` (or `mInfSnip` if unshared or `nil`). |
| `GetValue` | `procedure GetValue(rowId, colId: integer; fullinfo: boolean; var result: valueType);` | Unpacks the value of cell `(rowId, colId)` into `result` (returning full NaN/text descriptors if `fullinfo` is `true` or numeric defaults with optional cell circling if `false`). |
| `InitMatMgr` | `procedure InitMatMgr(var status: integer; application: AppKind);` | Initializes the Matrix Manager state, heaps, and parser tables (`LisaCalcTables`) for the specified `application` (`AppKind`). |
| `initparser` | `procedure initparser(var status: integer);` | Initializes or loads the lexical character classes, operator tokens, keyword tables, and grammar tables (`LisaCalcTables`) for the formula parser. |
| `IsTextstring` | `function IsTextstring(var number: valueType; var money: boolean): boolean;` | Checks whether the newly parsed expression in `eval` is a literal text string (`PUSHTEXT`), or evaluates its numeric value into `number` and sets `money` if currency-prefixed. |
| `mmMapFormulas` | `procedure mmMapFormulas(pasting: boolean; uRg, sRg: range; passNum: mmMapKind; var vector: mapInfoRec; var estimate: longint; var resFlag: boolean);` | Walks all formulas in the matrix during cut, paste, insert, or error-clear passes (`passNum`) to estimate handle growth, split shared formulas, and remap moved coordinate references. |
| `mmPRchkBox` | `procedure mmPRchkBox(absolute: boolean; chrinterval: interval; boxLabel: ptrdata; numBytes: integer; var bitset: boolean);` | Toggles relative/absolute row and column flags in `PRdataPtr` for Paste Relative checkboxes falling within character selection `chrinterval` of `boxLabel`. |
| `mmGetPRInfo` | `procedure mmGetPRInfo(aBoxLabel: ptrData; Formula: ptrData; rBoxLabel: ptrData; var numBytes: integer; CellLabel: ptrData; var numLByte: integer; var butData: PRflags; mode: idModeType);` | Formats the formula, relative/absolute checkbox strings (`aBoxLabel`, `rBoxLabel`), cell label, and navigation button flags (`butData`) for the current cell in the Paste Relative dialog. |
| `mmSendPRinfo` | `procedure mmSendPRinfo;` | Applies the user's chosen row/column relative-versus-absolute flags from `PRdataPtr` into the shared formula's `PRdata` bit array. |
| `mmSetBreak` | `procedure mmSetBreak(forced, state: boolean; aRg: range);` | Sets or clears (`state`) forced user page breaks (`forced = true`, recorded with undo support) or automatic page breaks across the row/column snips of `aRg`. |
| `mmSetWids` | `procedure mmSetWids(tableStyle: tblMode);` | Switches table display mode (`tableStyle`: values, show-formulas, or print preview) and recomputes column widths and folded-formula row heights accordingly. |
| `NewSnips` | `procedure NewSnips(var rg: range; source: srcType; ignoreUndo: boolean; ignoreProctect: boolean; var status: integer);` | Executes row, column, or cell-range cut, copy, paste, paste-relative, insert, or clear operations (`source`) on `rg`, managing undo/scrap buffers, protection checks, and formula remapping. |
| `NextCell` | `procedure NextCell(mode: mcType; curCell: range; var nxtCell: range);` | Computes the next 1-cell or heading range `nxtCell` adjacent to `curCell` in movement direction `mode` (`mmRight`, `mmLeft`, `mmUp`, `mmDown`, `mmBegOfRow`, etc.). |
| `NextFormula` | `function NextFormula(var rowId, colId: idType): boolean;` | Advances `(rowId, colId)` across allocated matrix rows and columns to the next cell containing a formula (`pkHasRule`), returning `false` when no more formulas exist. |
| `NextPRcell` | `procedure NextPRcell;` | Advances the Paste Relative dialog cursor (`PRinfo.row`, `PRinfo.col`) to the next cell in the pasted destination range. |
| `NumOfCoords` | `function NumOfCoords(formula: ptrData; rg: range; aFormula: ptrData; vector: mapInfoRec; mapExternal: boolean; relative: boolean; setRelInfo: boolean; var relInfo: PRTfmla): integer;` | Counts coordinate and range references in compiled `formula` (optionally remapping coordinates into `aFormula` via `vector` and populating relative/absolute flags in `relInfo`). |
| `NumOfFormulaFolds` | `procedure NumOfFormulaFolds;` | Computes line-wrapped (`FoldedFormula`) line counts for every formula in the matrix and adjusts each row's pixel height to fit its tallest folded formula. |
| `OpenMatrix` | `procedure OpenMatrix(fileName: PtrStrType; loadFile: boolean; checkAbort: boolean; openInfo: FIOKind; var tableInfo: tableRecord; var status: integer);` | Loads a saved worksheet matrix (or initializes an empty matrix when `fileName` is empty), restoring cells, snip attributes/breaks, view bands, and `tableInfo`. |
| `OutOfHeapSpace` | `function OutOfHeapSpace(hz: THz; bytesNeeded: integer): integer;` | Grow-zone callback for `mxHz` and `theHeap` that expands the underlying OS data segment to satisfy a `bytesNeeded` allocation request and returns the byte increment. |
| `parse` | `function parse(operation: parseKind; dataline: ptrdata; numBytes: integer; row, col: integer; var error: errRecord): boolean;` | Lexes and parses `numBytes` bytes of input `dataline` at cell `(row, col)` as a formula (`PFormula`), literal/numeric value (`PValue`), or range (`PCoordinate`), emitting p-code into `eval`. |
| `PrevPRcell` | `procedure PrevPRcell;` | Moves the Paste Relative dialog cursor (`PRinfo.row`, `PRinfo.col`) backward to the previous cell in the pasted destination range. |
| `PutValue` | `procedure PutValue(rowId, colId: integer; value: valueType; inrule: boolean; var status: integer);` | Packs `valueType` variant `value` into compact storage and stores it in cell `(rowId, colId)` either as a formula's cached result (`inrule = true`) or as a standalone cell value. |
| `ReadMMscrap` | `procedure ReadMMscrap(var status: integer);` | Reads serialized cell-matrix data, row/column dimensions, attributes, and formulas from the system Scrap into the Matrix Manager's local scrap structures. |
| `recalc` | `procedure recalc(rowId, colId: idType; var status: integer; inrule: boolean);` | Triggers matrix dependency recalculation after a change at `(rowId, colId)`, updating visible cells (`SetVisSnips`) when automatic or on-demand recalculation is active. |
| `resetPRdata` | `procedure resetPRdata(rowId, colId: idType; PRdata: TPPRrecord);` | Copies a shared formula's saved relative/absolute flags at `(rowId, colId)` into `PRdata` and resets the formula's `PRdata` bits to relative (`true`). |
| `RginScrap` | `procedure RginScrap(var rg: range);` | Returns the bounding cell `range` of the Matrix Manager's local cell scrap in `rg`, or `aNullRg` if no cell scrap is present. |
| `rstr` | `procedure rstr(number: extended; var result: resultStr; decplaces, format: byte; numdigits: integer; var scientific: boolean);` | Formats extended-precision floating-point `number` into string `result` according to `decplaces`, format code `format`, and digit limit `numdigits`, setting `scientific` if exponential notation was used. |
| `ScrapAbsent` | `function ScrapAbsent: boolean;` | Returns `true` if the Matrix Manager's local cell scrap handle (`ScrapPtr`) is `nil`. |
| `SetCellAttr` | `procedure SetCellAttr(attrRec: attrRecord; field: attrType; rg: range);` | Applies cell attribute `field` from `attrRec` to range `rg` (recording undo state in `mmUndoInfo`) and refreshes affected table cells on screen. |
| `SetCellBit` | `procedure SetCellBit(rowId, colId: idType; state: boolean; bitType: bitKind);` | Sets boolean marker/status bit `bitType` to `state` on cell `(rowId, colId)` (allocating blank cells when circling missing values). |
| `SetCharInfo` | `procedure SetCharInfo(fontId: TLfntId);` | Computes default row heights, heading dimensions, and character-based column widths for the active table from font metrics of `fontId`. |
| `SetImage` | `procedure SetImage(state: boolean);` | Enables or disables external view redrawing (`imageflag`, such as replotting the Business Graphics chart) during batch or fast data entry. |
| `SetMapVectors` | `procedure SetMapVectors(var vector: mapInfoRec);` | Populates `vector` (`mapInfoRec`) with row and column snip-ID remapping entries (`rmOk`, `rmDel`, `rmReName`) for an active cut, paste, or insert operation. |
| `SetReCalc` | `procedure SetReCalc(state: calcState);` | Configures worksheet recalculation mode to manual (`mmCalcMan`), automatic (`mmCalcAuto`), or immediate one-shot recalculation (`mmCalcNow`). |
| `SetRgBits` | `procedure SetRgBits(var rg: range; bitType: bitKind; state: boolean; action: byte);` | Performs batch matrix pass `action` (`0..14`, such as clearing markers, invalidating ranges, uncircling, finding protected/circled/matching cells, or refreshing invalid cells) over `rg`. |
| `SetVecWidth` | `procedure SetVecWidth(snip: snipKind; width: integer; rg: range);` | Stores pixel `width` directly into the `vecWid` snip-width vector for all rows or columns (`snip`) spanned by `rg`. |
| `SfromN` | `procedure SfromN(var answer: resultStr; num: longint; base: integer; alphabet: char);` | Converts integer `num` into string `answer` using radix `base` (10 for row numbers or bijective base-26 with `alphabet = 'A'` for column letters). |
| `ShrinkSegMemory` | `procedure ShrinkSegMemory(Hz: THz; beSmart: boolean; var errnum: integer);` | Compacts heap zone `Hz` and shrinks its underlying OS data segment memory and disk allocation when excess free space is available. |
| `SnipExist` | `function SnipExist(snip: snipKind; snipId: idType): boolean;` | Returns `true` if row or column `snipId` of kind `snip` is currently allocated (`vecSnip[snip, snipId] <> absent`) in the matrix. |
| `SwitchTable` | `procedure SwitchTable(ScrapTable: boolean; var tableInfo: tableRecord);` | Switches Matrix Manager and Table Manager context between the main worksheet matrix and the Scrap matrix (`ScrapTable`), returning that table's `tableInfo`. |
| `unPackValue` | `procedure unPackValue(hContents: THContents; pValue: TPValue; fullinfo: boolean; var result: valueType; var assume: boolean);` | Unpacks stored cell/formula value `(hContents, pValue)` into `result` (and `FP0` during formula evaluation), setting `assume` if a non-numeric/blank value defaulted to zero. |
| `WordFromLexeme` | `procedure WordFromLexeme(lexeme: symbol; maxBytes: integer; word: PtrStrType);` | Looks up the text representation of parser `lexeme` in `WordBuffer` and copies up to `maxBytes` bytes into Pascal string `word^`. |
| `WriteMMscrap` | `procedure WriteMMscrap(var status: integer);` | Serializes the Matrix Manager's local cell scrap (range header, row/column sizes, cell attributes, values, and unshared formulas) to the global system Scrap. |
| `CellFormula` | `procedure CellFormula(mode: IOModeType; rowId, colId: idType; formula: ptrData; var numBytes, status: integer; var error: errRecord);` | Decompiles (`mmRead`) or parses, stores, and evaluates (`mmWrite`) the formula text at `formula` (`numBytes` chars) for cell `(rowId, colId)`, returning `status` and `error`. |
| `CellInfo` | `procedure CellInfo(parName: cellParType; mode: IOModeType; rowId, colId: idType; var cellRec: cellRecord);` | Reads unpacked display attributes (`align`, `font`, `protected`, `hiLite`, `dim`) for cell or row/column heading `(rowId, colId)` into `cellRec`. |
| `CellRun` | `procedure CellRun(mode: IOModeType; rowId, colId: idType; value: ptrRuns; var numRuns, status: integer);` | Returns the count of FieldEdit formatting runs (`numRuns := 0` in LisaCalc and LisaGraph) and `ok` status for cell `(rowId, colId)`. |
| `CellValue` | `procedure CellValue(mode: IOModeType; rowId, colId: idType; value: ptrData; wideFlg: boolean; var numBytes, status: integer);` | Formats cell or heading `(rowId, colId)` as display or wide-angle text (`mmRead`), or parses and stores `numBytes` input characters (`mmWrite`, inferring `$` money format when applicable). |
| `FoldedFormula` | `procedure FoldedFormula(rowId, colId: idType; formula: ptrData; var numBytes: integer);` | Decompiles the formula at `(rowId, colId)` into `formula` with embedded carriage returns (`chr(13)`) so each line fits within the column's pixel width. |
| `GetSnipId` | `procedure GetSnipId(snip: snipKind; mode: idModeType; position: fract; refId: idType; var snipId: idType);` | Computes a row or column `snipId` in the current table by `mode`: first (`mmfirst`), last (`mmlast`), adjacent (`mmnext`/`mmprior` from `refId`), or proportional (`mmfraction` at `position`). |
| `mmBreakSnip` | `function mmBreakSnip(aKind: snipKind; aSnip: idType): Boolean;` | Returns `true` if a forced or automatic page break is active at `aKind` snip `aSnip` (returning `false` when viewing the scrap or print preview). |
| `mmMapSnip` | `procedure mmMapSnip(snip: snipKind; oldSnipId: idType; var newSnipId: idType; var status: integer);` | Maps `oldSnipId` of kind `snip` through the active cut/paste/insert mapping vector (`pVector`) into `newSnipId` and mapping status (`rmOk`, `rmDel`, or `rmReName`). |
| `SetSnipWidth` | `procedure SetSnipWidth(rg: range; width: integer);` | Sets the pixel width of all columns in `aColRg` or `aWTBoxRg` range `rg` to `width` (clamped to `maxLenWav` characters) with undo support. |
| `SnipLT` | `function SnipLT(snip: snipKind; snipId1, snipId2: idType): boolean;` | Returns `true` if `snipId1` precedes `snipId2` along axis `snip`, properly ordering `mInfSnip` (`-infinity`) and `pInfSnip` (`+infinity`). |
| `SnipWidth` | `function SnipWidth(snip: snipKind; snipId: idType): integer;` | Returns the pixel height (for `rowKind`) or pixel width (for `colKind`) of `snipId` (including `mInfSnip` title headings) in the active matrix or scrap table. |

---

## Unit Parser

Provides lexical/numeric packing utilities, coordinate range normalization, leap-year calculation, and buffered text-formatting output routines used by the spreadsheet formula parser and decompiler.

- **Import**: `USES {$U Parser.obj} Parser;`
- **Unit kind**: `INTRINSIC` (`PARSER`)
- **Interface dependencies**: `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `DBEnv`, `FEDec`, `FieldEdit`, `TEEnv`, `SysCall`, `FPLib`, `PMDecl`, `PrStdInfo`, `MatMgr`, `International`, `MathLib`, `BGEnv`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `LeapYear` | `function LeapYear(year: integer): integer;` | Returns `1` if `year` is a Gregorian leap year (divisible by 4, excluding century years not divisible by 400) or `0` otherwise. |
| `packnum` | `procedure packnum(number: longreal; var numValue: variantType; var typeOfNum: numType);` | Determines the most compact lossless storage representation (`typeOfNum`: byte, 16-bit integer, short real, long real, or NaN) for `number` and packs it into `numValue`. |
| `startwrite` | `procedure startwrite(message: ptrData; maxlen: integer);` | Initializes the parser/decompiler output buffer pointer to `message` with maximum capacity `maxlen` bytes and resets `messagelen`. |
| `writecoord` | `procedure writecoord(coord: pident; var colwidth: byte);` | Appends encoded cell coordinate `coord` in `A1` column-letter/row-number notation (respecting `$` absolute markers) to the active `startwrite` message buffer. |
| `writefnum` | `procedure writefnum(number: extended; docommas: boolean);` | Formats `number` with fixed decimal places and optional thousands commas (`docommas`) and appends it to the active `startwrite` message buffer. |
| `writechar` | `procedure writechar(ch: char);` | Appends single character `ch` to the active `startwrite` message buffer if space remains below `messagemax`. |
| `writenum` | `procedure writenum(number: extended);` | Formats extended-precision `number` in floating format (up to `maxDecPlaces` digits) and appends it to the active `startwrite` message buffer. |
| `writestring` | `procedure writestring(message: str80);` | Appends all characters of Pascal string `message` to the active `startwrite` message buffer. |
| `writeword` | `procedure writeword(lexeme: symbol);` | Looks up the keyword or operator text for `lexeme` via `WordFromLexeme` and appends it to the active `startwrite` message buffer. |

---

## Unit Stubs

Provides diagnostic, tracing, memory-inspection, and interactive test-harness formatting routines for debugging Matrix Manager cells, compiled formulas, calculation stacks, floating-point environments, and paste-relative structures.

- **Import**: `USES {$U Stubs.obj} Stubs;`
- **Unit kind**: `INTRINSIC` (`STUBS`)
- **Interface dependencies**: `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `GrafUtil`, `DBEnv`, `FEDec`, `FieldEdit`, `TEEnv`, `SysCall`, `FPLib`, `PMDecl`, `PrStdInfo`, `MatMgr`, `Parser`, `Events`, `Windows`, `Scrap`, `MathLib`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `ArrToStr` | `procedure ArrToStr(var result: str80; data: ptrData; len: integer);` | Copies up to `len` (capped at 80) bytes from raw byte array `data` into Pascal string `result`. |
| `DebugMess` | `procedure DebugMess(messnumber: integer);` | Prints the diagnostic Matrix Manager trace or close-progress message corresponding to `messnumber`. |
| `displayvalue` | `procedure displayvalue(rowId, colId: integer; value: longreal);` | Formats `longreal` `value` for cell `(rowId, colId)` and prints it to the debug output when `debug[10]` is enabled. |
| `displaylint` | `procedure displaylint(row, col: integer; value: longint);` | Converts 32-bit `longint` `value` to `longreal` and outputs it via `displayvalue` for cell `(row, col)`. |
| `dispAt` | `procedure dispAt(rg: range; row, col: integer);` | Formats the column/row title coordinates of `rg`'s top-left corner and renders them at debug test-grid cell `(row, col)`. |
| `dispPasses` | `procedure dispPasses(numPasses: integer; completed: boolean);` | Records recalculation pass count `numPasses` and completion flag `completed` into diagnostic timer slot `timer[3]`. |
| `dispRg` | `procedure dispRg(rg: range);` | Displays `'ok'` (for `aNullRg`) or the top-left coordinate of `rg` on the debug test-program status line. |
| `dumpcalc` | `procedure dumpcalc(calc: calcStack; iCell: valueType; iresult: valueType; iRow, iCol: integer; itt: boolean; calcpt: integer; maxpt: integer; row, col: integer);` | Dumps the formula evaluation `calcStack` entries (`0..maxpt`), active `calcpt` pointer, iteration coordinates, and intermediate `valueType` results to debug output. |
| `dumpenv` | `procedure dumpenv(myEnviron: Environ);` | Prints the floating-point environment flags and exception bits in `myEnviron` for debugging. |
| `dumpformula` | `procedure dumpformula(formula: ptrData);` | Prints the raw compiled p-code byte sequence and total byte length of `formula` until `PUSHEND` (or mouse/key abort). |
| `dumpPRinfo` | `procedure dumpPRinfo(infonum: integer; aFormula, rFormula: ptrData; numbyte1, numbyte2: integer; PRdata: PRrecord; offAxis: boolean);` | Prints diagnostic Paste Relative formula strings (`aFormula`, `rFormula`), character intervals, and `PRrecord` state for debug trace `infonum`. |
| `dumpRefs` | `procedure dumpRefs;` | Prompts for row/column offsets and prints a grid of cell and formula reference counts across the matrix for debugging. |
| `dumpShared` | `procedure dumpShared(formPtr: THFmla);` | Prints the base coordinates, `(dv, dh)` offsets, coordinate count, reference count, and `PRdata` bits of shared formula handle `formPtr`. |
| `errorprint` | `procedure errorprint(error: errRecord; textline: ptrData; textlength: integer);` | Prints `textlength` bytes of `textline` and marks the character position indicated by `error` in the debug test harness. |
| `getbutton` | `function getbutton: boolean;` | Returns `true` if key code 6 is currently held down to interrupt diagnostic dumps. |
| `inv` | `procedure inv(rowId, colId: integer; shade: integer);` | Highlights debug test-grid cell `(rowId, colId)` by erasing (`< 0`), inverting (`0`), or gray-shading (`1`, `2`) its rectangle. |
| `highlight` | `procedure highlight(rowId: integer; colId: integer; index: integer; numchr: integer);` | Inverts the rectangle covering `numchr` characters starting at 1-based character `index` inside debug test-grid cell `(rowId, colId)`. |
| `meminfo` | `procedure meminfo(rowId, colId: integer; cellinfo: boolean);` | Prints heap handle sizes, reference counts, and cell/formula memory usage details for cell `(rowId, colId)` or the overall matrix. |
| `OSerror` | `procedure OSerror(routine, mmerror: str40; error: integer);` | Logs an operating-system call failure (`routine`, `mmerror`, and numeric `error` code) when Matrix Manager debug tracing is enabled. |
| `putatext` | `procedure putatext(rowId, colId: integer; message: ptrData; len: integer);` | Converts `len` bytes at `message` into a string and draws it left-aligned in debug test-grid cell `(rowId, colId)`. |
| `puttext` | `procedure puttext(rowId, colId: integer; message: str255; align: byte);` | Draws clipped text `message` with alignment `align` inside debug test-grid cell `(rowId, colId)`. |
| `readInteger` | `function readInteger(var int: integer): boolean;` | Reads a line of digits via `readTextLine`, parses it into `int`, and returns `true` if a valid non-aborted integer was entered. |
| `readTextLine` | `procedure readTextLine(var gotbutton: boolean; var temp: str255; echo1, echo2: boolean; echo2row, echo2col: integer);` | Reads characters interactively until Return into `temp` (with optional screen echoing at `(echo2row, echo2col)`), setting `gotbutton` if aborted. |
| `RodStuff` | `function RodStuff(menuitem: integer): boolean;` | Executes interactive Matrix Manager debug menu command `menuitem` (dumping cells, heaps, formulas, flags, or test operations). |
| `StatusMess` | `procedure StatusMess(status: integer);` | Translates Matrix Manager `status` code into a human-readable diagnostic message and prints it when status tracing is enabled. |
| `TraceMess` | `procedure TraceMess(messnumber: integer);` | Prints indented routine entry/exit trace messages corresponding to `messnumber` for Matrix Manager debugging. |
| `wAttr` | `function wAttr(value: TAttr): char;` | Writes a formatted summary of packed cell attributes `value` (`TAttr`: flags, format, alignment, decimal places, protection) to standard output and returns `' '`. |
| `wExc` | `function wExc: char;` | Reads and prints active floating-point exception flags from the FPU environment and returns `' '`. |
| `wClip` | `function wClip: char;` | Prints the bounding box (`left, top, right, bottom`) of `thePort^.clipRgn` to standard output and returns `' '`. |
| `wHex` | `function wHex(num: longint): char;` | Formats and prints the low 24 bits of `num` as a 6-digit hexadecimal string and returns `' '`. |
| `wKind` | `function wKind(kind: cnNumKind): char;` | Writes the symbolic name of `cnNumKind` (`cNumber`, `cOther`, or `cPenny`) to standard output and returns `' '`. |
| `wMap` | `function wMap(value: integer): char;` | Writes the symbolic name of snip-mapping code `value` (`rmDel`, `rmRename`, or `rmOk`) to standard output and returns `' '`. |
| `wNAN` | `function wNAN(value: cnSymKind): char;` | Writes the symbolic name of `cnSymKind` NaN/value tag `value` (`syNone`, `syError`, `syNa`, `syText`, `syDzero`, etc.) to standard output and returns `' '`. |
| `wBool` | `function wBool(flag: boolean): char;` | Returns `'T'` if `flag` is `true` or `'F'` if `flag` is `false`. |
| `wNUM` | `function wNUM(number: longreal): char;` | Converts `longreal` `number` to `extended` and prints it via `wxNUM`, returning the final character. |
| `wxNUM` | `function wxNUM(number: extended): char;` | Formats `extended` `number` via `rstr`, writes all but its last character to standard output, and returns the last character for `write(...)` chaining. |
| `wRect` | `function wRect(r: rect): char;` | Prints the coordinates (`left, top, right, bottom`) of rectangle `r` to standard output and returns `' '`. |
| `wRg` | `function wRg(rg: range): char;` | Prints the `rKind` name and `(loRow, loCol, hiRow, hiCol)` coordinates of range `rg` to standard output and returns `' '`. |
| `wSHR` | `function wSHR(value: shareKind): char;` | Writes the symbolic name of formula sharing state `value` (`fSingle`, `fShared`, `fSeen`, `fAseen`, or `fAbsolute`) to standard output and returns `' '`. |
| `wSRC` | `function wSRC(value: srcType): char;` | Writes the symbolic name of `srcType` operation `value` (`mmNull`, `mmScrap`, `mmUndo`, `mmCopy`, `mmClear`, `mmRelative`, etc.) to standard output and returns `' '`. |
| `wSNIP` | `function wSNIP(value: snipKind): char;` | Writes `'rowKind'` or `'colKind'` for `value` to standard output and returns `' '`. |
| `wTEXT` | `function wTEXT(value: variantType): char;` | Writes the character slice described by `value.textinfo` (`hcontents`, `index`, `len`) delimited by `'..'` to standard output and returns `' '`. |
| `wVAL` | `function wVAL(value: valueType): char;` | Writes both the numeric value and `cnSymKind` tag of `valueType` `value` to standard output and returns `' '`. |
| `wWords` | `function wWords(value: symbol): char;` | Looks up and writes the text token of parser symbol `value` to standard output and returns `' '`. |

---

## Unit TEExec

Bridges user interface menu commands, keyboard navigation, mouse selection/dragging, cell entry, recalculation triggers, and multi-operation undo between the Folder Executive, Table Manager, and Matrix Manager.

- **Import**: `USES {$U TEExec.obj} TEExec;`
- **Unit kind**: `INTRINSIC` (`TEEXEC`)
- **Interface dependencies**: `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `DBEnv`, `FEDec`, `FieldEdit`, `TEEnv`, `SysCall`, `FPLib`, `PMDecl`, `PrStdInfo`, `PrPublic`, `MatMgr`, `Events`, `Folders`, `Menus`, `AlertMgr`, `WmlStd`, `WmlSb`, `WmlGrow`, `TM`, `FEGlobals`, `CoMgr`, `Scrap`, `BGEnv`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `chgMenuLC` | `procedure chgMenuLC;` | Updates enable/disable states and checkmarks across all LisaCalc menus (File/Print, Edit, Type Style, Page Layout, Format, Protect, and Calculate). |
| `chgMenuBG` | `procedure chgMenuBG;` | Updates enable/disable states and checkmarks across all LisaGraph menus according to whether the table panel or graph panel is active. |
| `ChgMenuScrap` | `procedure ChgMenuScrap;` | Updates File/Print menu enable states when the `ScrapFolder` window is the active folder. |
| `ChgTblFont` | `procedure ChgTblFont(NewFontFam: TFam);` | Changes the active table display font to `NewFontFam` (if different), updates Matrix Manager and Table Selection Manager metrics, and redraws the folder. |
| `doUndo` | `procedure doUndo;` | Executes the Edit-menu Undo/Redo command for the last recorded operation in `undoRec` (text edit, cell/snip cut-paste-insert, attribute/width/break change, font change, or Go To). |
| `FontCommand` | `procedure FontCommand(undoing: boolean; var newCR: boolean);` | Processes a Type Style menu selection (or its Undo when `undoing` is `true`) to switch either the printer font or the screen table font mode. |
| `newAlignProt` | `procedure newAlignProt(field: attrType);` | Applies a newly selected cell alignment (`aAlign`) or protection/invisibility setting from the Format or Protect menu to `g.curRange`. |
| `newFormat` | `procedure newFormat;` | Handles a Format-menu numeric/money format command on `g.curRange`, either prompting for decimal precision (`putCWidPrecBox`) or applying the format immediately. |
| `putUpMenus` | `procedure putUpMenus;` | Clears the menu bar and installs the menu set appropriate for the active window (`ScrapFolder`, LisaCalc, or LisaGraph). |
| `setNewformat` | `procedure setNewformat(numPlaces: integer);` | Applies pending format attributes (`g.attributes` with `numPlaces` decimal places) to the Matrix Manager, enters and reselects `g.curRange`, and updates menu checkmarks. |
| `setTblFont` | `procedure setTblFont(NewFontFam: TFam);` | Sets `TblFntId.Fam` to `NewFontFam`, loads its Font Manager metrics, and updates Matrix Manager character dimensions via `SetCharInfo` without redrawing. |
| `doKeyedMove` | `procedure doKeyedMove(dir: moveDir; var status: integer);` | Moves the single-cell selection and `g.curRange` one step in direction `dir` (scrolling into view and selecting the target cell) after a directional enter key. |
| `DrwCellScrap` | `procedure DrwCellScrap;` | Switches temporarily to the Scrap table (`SwitchTable(true, ...)`), renders the cell-matrix scrap and scroll bars inside `ScrapFolder`, and switches back to the main table. |
| `enterCalc` | `procedure enterCalc(firstEnter: boolean; reSelCR: boolean; calcOnEnterOnly: boolean; delayCalc: boolean; var status: integer);` | Commits any pending cell or formula edit (if `firstEnter`), optionally reselects `g.curRange` (`reSelCR`), and triggers or defers matrix recalculation (`calcOnEnterOnly`, `delayCalc`). |
| `enterReSelect` | `procedure enterReSelect(var status: integer);` | Commits any pending edit in single-cell `g.curRange`, triggers recalculation if changed, and reselects the cell. |
| `forceCalc` | `procedure forceCalc(reSelCR: boolean);` | Forces an immediate worksheet recalculation without performing a cell enter, optionally reselecting `g.curRange` (`reSelCR`) and reporting any calculation alerts. |
| `forceEnter` | `function forceEnter(var status: integer): integer;` | Commits any pending cell or formula edit and triggers recalculation without reselecting `g.curRange`, returning the resulting `status`. |
| `initMSpecs` | `procedure initMSpecs;` | Initializes the `MoveSpecs` key-binding table mapping Tab, Return, Enter, and arrow/keypad keys (with Shift/Option modifiers) to cell movement directions. |
| `insertSnip` | `procedure insertSnip(numSnips: integer; var newCR: boolean);` | Inserts `numSnips` blank rows or columns at the currently selected grid line (`g.curRange`) via `NewSnips`, recording undo state and updating `newCR`. |
| `moveAction` | `function moveAction(ch: char): moveDir;` | Looks up the latest key event (`getKeyPair`) in `MoveSpecs`, posts undo/alert phrasing via `doWouldALert`, and returns the implied `moveDir` (or `noMove`). |
| `ReturnRgFB` | `procedure ReturnRgFB(var timeout: integer);` | Restores range highlight feedback for `g.curRange` (and caret blink timeout if a Table Editor panel is active). |
| `selectRg` | `procedure selectRg(newRg: range; hilite: cellseltype);` | Replaces `g.curRange` with `newRg`, scrolls it into view, establishes Table Selection Manager highlighting (`hilite`), and makes `tblPnl` active. |
| `SelInLeftCorner` | `procedure SelInLeftCorner;` | Collapse-selects the top-left cell of a row or column range (`g.curRange`) so formula/value editing targets a concrete cell. |
| `tblEditPnl` | `function tblEditPnl(aPnl: pnlIndex): boolean;` | Returns `true` if panel `aPnl` is managed by the Table Editor (`tblPnl` or `widePnl`). |
| `tblMseDn` | `procedure tblMseDn(mouseRel: point; var newCR: boolean);` | Handles a mouse-down at `mouseRel` in `tblPnl`, committing any prior cell edit, handling Option-click formula range pointing or double/triple clicks, and starting a new table selection. |
| `tblMseMvd` | `procedure tblMseMvd(mouseRel: point; var newCR: boolean);` | Extends the active table selection or Option-dragged formula range when the mouse moves to `mouseRel` outside `g.curNbrhood`, setting `newCR` if `g.curRange` changed. |
| `TEedits` | `procedure TEedits(var status: integer; var txtChg: boolean; var newCR: boolean);` | Executes an Edit-menu Cut, Copy, Paste, Paste Relative, Paste Values, or Clear command when `tblPnl` or `widePnl` is active, setting `txtChg` and `newCR`. |
| `TEkey` | `procedure TEkey(ch: char; var wasMove: boolean; var status: integer);` | Processes character `ch` when `tblPnl` or `widePnl` is active, either committing and moving on a directional enter key (`wasMove = true`) or inserting `ch` into the edited cell. |
| `TEmseUp` | `procedure TEmseUp(mouseRel: point; var newCR: boolean);` | Handles mouse-up at `mouseRel` for `tblPnl` or `widePnl`, finalizing grid resizes, range selections, or pending cell enters and setting `newCR`. |
| `TEreInit` | `procedure TEreInit(freshStart: boolean);` | Reinitializes the Table Editor display (`ReBldTbl` on `freshStart`, or restoring saved selection feedback) and renders the active table. |
| `TERestore` | `procedure TERestore;` | Discards uncommitted in-cell or formula edits (`Restore Original`), reselects `g.curRange` from Matrix Manager contents, and sets undo state to `uRestore`. |
| `wideMseDn` | `procedure wideMseDn(mouseRel: point);` | Handles single, double, or triple mouse-down clicks at `mouseRel` inside the wide-angle-view panel (`widePnl`) to position or extend the text selection. |
| `wideMseMvd` | `procedure wideMseMvd(mouseRel: point);` | Extends the wide-angle-view text selection (and synchronized cell highlight) when the mouse drags to `mouseRel` outside `g.curNbrhood`. |
