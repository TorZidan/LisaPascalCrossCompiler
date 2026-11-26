# `QPLIB` (`QPLIB.obj`) — Lisa QuickPort Windowing, Graphics & Terminal Emulation Library

[Back to Library Index](LIBRARIES.md)

QuickPort environment allowing traditional Pascal programs to run in Lisa Office System desktop windows with mouse/QuickDraw graphics (`UQPGraph`), printing (`UQPPrint`), and extensible Clascal terminal emulation (`UStdTerm`, `UVT100`, `USoroc`).

- **Object file**: `libs/workshop3.0/QPLIB.obj` (Intrinsic library (interface stripped in `libs/workshop3.0/`))
- **Contents**: 5 units, 38 top-level procedures/functions, 20 Clascal classes (27 methods)

> [!NOTE]
> `libs/workshop3.0/QPLIB.obj` in this repository is a link-only stub whose embedded `INTERFACE` text was stripped (`INTRINSIC.LIB` still indexes its units). The unit interfaces and signatures below were extracted from the unstripped Workshop 3.0 / Lisa Office System `QPLIB.OBJ` build library.

## Importing and Linking

```pascal
USES UQPGraph, UQPPrint, USoroc;
```

```sh
pascal/lpc.py --link=IOSPASLIB,SYS1LIB,PRLIB,QPLIB MYPROG
```

## Units in This Library

| Unit | 8-Char Symbol | `USES` Dependencies | Top-Level Routines | Clascal Classes (Methods) | Summary |
|---|---|---|---|---|---|
| [`UQPGraph`](#unit-uqpgraph) | `UQPGRAPH` | `UObject`, `QuickDraw`, `UDraw`, `UABC`, `UTKUniversalText`, `UText`, `UDialog`, `BlkIOIntr`, `UStdTerm`, `SysCall` | 8 | 1 (1) | Provides QuickPort QuickDraw graphics panel support, capturing QuickDraw drawing operations into a persistent panel picture and supplying non-polling and blocking mouse/keyboard event routines for Pascal programs. |
| [`UQPPrint`](#unit-uqpprint) | `UQPPRINT` | `SysCall`, `PasLibCall`, `PPasLibC`, `PMDecl`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `PrStdInfo`, `PrPublic` | 7 | 0 | Implements QuickPort text printer output using the Lisa Print Manager, handling print dialog setup, line/page wrapping, form feeds, printable margins, and font changes. |
| [`USoroc`](#unit-usoroc) | `USOROC` | `UObject`, `QuickDraw`, `UDraw`, `UABC`, `UTKUniversalText`, `UText`, `UDialog`, `BlkIOIntr`, `UStdTerm` | 0 | 1 (1) | Implements a Soroc IQ-120 video terminal emulator subclass of TStdTerm for QuickPort windows, interpreting Soroc escape sequences, direct cursor addressing, and arrow-key mappings. |
| [`UStdTerm`](#unit-ustdterm) | `USTDTERM` | `UObject`, `QuickDraw`, `UDraw`, `UABC`, `UTKUniversalText`, `UText`, `UDialog`, `SysCall`, `UClascal`, `BlkIOIntr`, `UQPPrint`, `Hardware` | 23 | 17 (24) | Implements the QuickPort Toolkit application framework and standard terminal emulator, providing Clascal process/document/window/view/selection classes, clipboard cut/copy/paste support, and procedural screen, cursor, tab, font, and keyboard controls. |
| [`UVT100`](#unit-uvt100) | `UVT100` | `UObject`, `QuickDraw`, `UDraw`, `UABC`, `UTKUniversalText`, `UText`, `UDialog`, `BlkIOIntr`, `UStdTerm` | 0 | 1 (1) | Implements a DEC VT100 and VT52 video terminal emulator subclass of TStdTerm for QuickPort windows, supporting ANSI/VT52 escape sequences, scrolling regions, character sets, and keypad modes. |

---

## Unit UQPGraph

Provides QuickPort QuickDraw graphics panel support, capturing QuickDraw drawing operations into a persistent panel picture and supplying non-polling and blocking mouse/keyboard event routines for Pascal programs.

- **Import**: `USES UQPGraph;`
- **Unit kind**: `INTRINSIC` (`UQPGRAPH`)
- **Interface dependencies**: `UObject`, `QuickDraw`, `UDraw`, `UABC`, `UTKUniversalText`, `UText`, `UDialog`, `BlkIOIntr`, `UStdTerm`, `SysCall`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `VGetMouse` | `PROCEDURE VGetMouse(VAR pt: Point);` | Returns the current mouse location in graphics-panel view coordinates in pt while servicing pending Toolkit events. |
| `MouseButton` | `FUNCTION MouseButton: BOOLEAN;` | Returns TRUE if the physical Lisa mouse button is currently pressed down. |
| `MouseEvent` | `FUNCTION MouseEvent(VAR aMouseEvent: TMouseEvent): BOOLEAN;` | Dequeues the next mouse down, drag, up, or multi-click record from QuickPort's mouse queue into aMouseEvent and returns TRUE, or clears aMouseEvent and returns FALSE if the queue is empty. |
| `VStillDown` | `FUNCTION VStillDown: BOOLEAN;` | Returns TRUE if the mouse button is currently depressed and no further mouse events are waiting in the QuickPort mouse queue. |
| `WaitMouseEvent` | `PROCEDURE WaitMouseEvent(VAR aMouseEvent: TMouseEvent);` | Suspends/processes Toolkit events without busy-waiting until a mouse event arrives in the QuickPort graphics panel and returns it in aMouseEvent. |
| `WaitEvent` | `PROCEDURE WaitEvent(VAR fromKeyboard: BOOLEAN);` | Blocks while servicing Toolkit events until either keyboard type-ahead or a mouse event is available, setting fromKeyboard to TRUE when keyboard input is ready. |
| `QPGrafPicSize` | `FUNCTION QPGrafPicSize: INTEGER;` | Returns the current byte size (picSize) of the QuickDraw picture recording output in the QuickPort graphics panel. |
| `QPScrollRect` | `PROCEDURE QPScrollRect(dstRect: Rect; dh, dv: INTEGER; updateRgn: RgnHandle);` | Scrolls rectangle dstRect by (dh, dv) pixels in the QuickPort graphics panel, updating updateRgn, tracking cumulative scroll offsets, and invalidating exposed pad areas. |

### Clascal Classes

#### `TQPGraph = SUBCLASS OF TObject`

Clascal initializer class whose class initialization enables the QuickPort QuickDraw graphics panel and opens its capture GrafPort.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE: TQPGraph;` | Allocates and returns a TQPGraph instance on mainHeap so linking the unit triggers graphics-panel initialization. |

---

## Unit UQPPrint

Implements QuickPort text printer output using the Lisa Print Manager, handling print dialog setup, line/page wrapping, form feeds, printable margins, and font changes.

- **Import**: `USES UQPPrint;`
- **Unit kind**: `INTRINSIC` (`UQPPRINT`)
- **Interface dependencies**: `SysCall`, `PasLibCall`, `PPasLibC`, `PMDecl`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `PrStdInfo`, `PrPublic`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `vwp_Init` | `procedure vwp_Init;` | Initializes the Print Manager for QuickPort text printing and resets line-wrap, open-printer, and line-spacing state. |
| `vwp_Reset` | `function vwp_Reset: boolean;` | Opens a QuickPort print job (initializing PrMgr if needed, setting default printer parameters, starting document and first page spooling in 10-pitch font), and returns TRUE if ready to print. |
| `vwp_Close` | `function vwp_Close: boolean;` | Ends the current spooled page and document for an open QuickPort print job and returns TRUE, or returns FALSE if the printer was not open. |
| `vwp_W_Str` | `function vwp_W_Str(pStr: tPStr): boolean;` | Renders text string pStr^ onto the active QuickPort print port, handling leading CR, LF, and FF control characters, automatic line wraparound, and page breaks, and returning FALSE if the printer is closed. |
| `PrChangeFont` | `procedure PrChangeFont(Font: integer);` | Changes the QuickPort printer GrafPort font to Font, recomputes vertical line spacing from its font metrics, and advances the pen baseline (or starts a new page on overflow). |
| `PrWrapAround` | `procedure PrWrapAround(TurnOn: boolean);` | Enables (when TurnOn is TRUE) or disables (when TurnOn is FALSE) automatic right-margin line wrapping for QuickPort printer text output. |
| `PrPageRect` | `procedure PrPageRect(l, t, r, b: integer);` | Sets the printable page margin rectangle PageBounds for QuickPort text printing to (l, t, r, b). |

---

## Unit USoroc

Implements a Soroc IQ-120 video terminal emulator subclass of TStdTerm for QuickPort windows, interpreting Soroc escape sequences, direct cursor addressing, and arrow-key mappings.

- **Import**: `USES USoroc;`
- **Unit kind**: `INTRINSIC` (`USOROC`)
- **Interface dependencies**: `UObject`, `QuickDraw`, `UDraw`, `UABC`, `UTKUniversalText`, `UText`, `UDialog`, `BlkIOIntr`, `UStdTerm`

### Clascal Classes

#### `TSOROC = SUBCLASS OF TStdTerm`

TStdTerm subclass that emulates a Soroc video terminal in a QuickPort window, maintaining escape-sequence parser state, margins, and arrow-key translation.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: Theap): TSOROC;` | Allocates or initializes a TSOROC terminal emulator on heap with 80x24 dimensions, wraparound enabled, and Soroc escape-parser state reset. |

---

## Unit UStdTerm

Implements the QuickPort Toolkit application framework and standard terminal emulator, providing Clascal process/document/window/view/selection classes, clipboard cut/copy/paste support, and procedural screen, cursor, tab, font, and keyboard controls.

- **Import**: `USES UStdTerm;`
- **Unit kind**: `INTRINSIC` (`USTDTERM`)
- **Interface dependencies**: `UObject`, `QuickDraw`, `UDraw`, `UABC`, `UTKUniversalText`, `UText`, `UDialog`, `SysCall`, `UClascal`, `BlkIOIntr`, `UQPPrint`, `Hardware`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `QPConfig` | `PROCEDURE QPConfig(config: TQPConfigRec);` | Configures the QuickPort window layout and options from config (scrollback buffer retention, Apple-Period pass-through, optional input panel, and split text/graphics panel geometry) prior to screen I/O. |
| `SetupTermPara` | `PROCEDURE SetupTermPara(termpara: TTermPara);` | Sets terminal dimensions (rowsize, columnsize), line wraparound, XON/XOFF flow-control keys, and cursor shape from termpara prior to screen I/O. |
| `VRead` | `PROCEDURE VRead(VAR ch: CHAR; VAR keycap: Byte; VAR applekey, shiftkey, optionkey: BOOLEAN);` | Reads one un-echoed, unmapped keystroke from the active terminal ConsTerm, returning the ASCII character ch, hardware keycap, and Apple, Shift, and Option modifier states. |
| `ClearScreen` | `PROCEDURE ClearScreen(clearkind: INTEGER);` | Clears all or part of the terminal screen or current line according to clearkind (whole screen, cursor-to-end/start of screen, whole line, or cursor-to-end/start of line). |
| `VGotoxy` | `PROCEDURE VGotoxy(x, y: INTEGER);` | Moves the terminal cursor to 0-based column x and row y relative to the screen home position and updates cursor highlighting. |
| `MoveCursor` | `PROCEDURE MoveCursor(scroll: BOOLEAN; xdistance, ydistance: INTEGER);` | Moves the terminal cursor relatively by xdistance columns and ydistance rows, scrolling the screen vertically when scroll is TRUE and vertical bounds are exceeded. |
| `SetTab` | `PROCEDURE SetTab(column: INTEGER);` | Sets a horizontal tab stop at 0-based column (or at the current cursor column when column < 0). |
| `ClearTab` | `PROCEDURE ClearTab(clearAll: BOOLEAN; column: INTEGER);` | Clears all horizontal tab stops when clearAll is TRUE, or clears the tab stop at column (using the current cursor column if column < 0) when clearAll is FALSE. |
| `StopInput` | `PROCEDURE StopInput;` | Locks keyboard input so subsequent user keystrokes in the QuickPort window are ignored until StartInput is called. |
| `StartInput` | `PROCEDURE StartInput;` | Unlocks keyboard input in the QuickPort window after a prior StopInput call. |
| `ChangeCharStyle` | `PROCEDURE ChangeCharStyle(newstyle: Style);` | Changes the active terminal character face style (such as bold, italic, underline, or inverse) to newstyle for subsequent text output. |
| `QPYield_CPU` | `PROCEDURE QPYield_CPU;` | Processes pending Toolkit user, menu, and window events during compute-bound loops and yields the CPU. |
| `VStrWrite` | `PROCEDURE VStrWrite(VAR str: Tstr255);` | Writes printable string str (containing no control characters) starting at the current terminal cursor position with line wraparound and screen scrolling. |
| `VGetLine` | `PROCEDURE VGetLine(lineNo: INTEGER; VAR line: Tstr255; delete: BOOLEAN);` | Copies terminal or scrollback row lineNo (-1..maxLines-1) into string line without moving the cursor, optionally deleting that row when delete is TRUE. |
| `VPutLine` | `PROCEDURE VPutLine(lineNo: INTEGER; VAR line: Tstr255; insert: BOOLEAN);` | Inserts string line at terminal or scrollback row lineNo (scrolling and redrawing) when insert is TRUE, or replaces row lineNo's text in place when insert is FALSE. |
| `VScrollLines` | `PROCEDURE VScrollLines(topRegion, bottomRegion: INTEGER; scrollhowmanylines: INTEGER);` | Scrolls the rendered pixel region between terminal rows topRegion and bottomRegion vertically by scrollhowmanylines lines (positive scrolls down) without modifying line data structures. |
| `RedrawScreen` | `PROCEDURE RedrawScreen;` | Repaints all visible lines and cursor highlighting across the entire terminal panel. |
| `RedrawLine` | `PROCEDURE RedrawLine(lineNo: INTEGER);` | Repaints terminal or scrollback row lineNo across all panes of the terminal panel while preserving cursor highlighting. |
| `ChangeMaxColumns` | `PROCEDURE ChangeMaxColumns(newColumns: INTEGER);` | Changes the terminal width to newColumns (selecting 12-pitch text font up to 80 columns or 20-pitch text font up to 132 columns), homes the cursor, clears the screen, and invalidates the panel. |
| `ChangeFont` | `PROCEDURE ChangeFont(newfont: INTEGER);` | Switches the current terminal output font to fixed-pitch font ID newfont (such as VT100 line-drawing graphics font) while preserving the current character style. |
| `BindDocheap` | `PROCEDURE BindDocheap;` | Binds the active QuickPort document's memory heap via its TTermDocManager before accessing window or view objects. |
| `CkPutAway` | `PROCEDURE CkPutAway;` | Checks after processing Toolkit events whether the QuickPort document was put away (closed) and, if so, cleanly completes and terminates the process. |
| `NotToWait` | `FUNCTION NotToWait: BOOLEAN;` | Returns TRUE unconditionally as a predicate for TProcess.ObeyEvents so pending events are processed only until idle without blocking. |

### Clascal Classes

#### `TTermProcess = SUBCLASS OF TProcess`

TProcess subclass representing a QuickPort application process and creating its TTermDocManager instance.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE: TTermProcess;` | Creates and initializes the QuickPort TTermProcess singleton for managing Toolkit events and terminal documents. |

#### `TTermDocManager = SUBCLASS OF TDocManager`

TDocManager subclass that binds and opens QuickPort terminal documents and creates TVanWindow instances.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsPathPrefix: TFilePath): TTermDocManager;` | Creates a TTermDocManager on heap initialized with the document path prefix itsPathPrefix. |

#### `TTermView = SUBCLASS OF TView`

TView subclass that renders scrollable terminal text lines, handles mouse selection presses, and exports universal text to the clipboard.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsPanel: TPanel; itsExtent: LRect; itsLines: TArray): TTermView;` | Creates a TTermView on heap attached to itsPanel with view bounds itsExtent and optional clipboard line array itsLines. |

#### `TInputView = SUBCLASS OF TView`

TView subclass that displays buffered type-ahead and pasted keyboard input in the optional QuickPort input panel.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsPanel: TPanel; itsExtent: LRect): TInputView;` | Creates a TInputView on heap attached to itsPanel with view bounds itsExtent for displaying queued keyboard input. |

#### `TTermCutCopyCmd = SUBCLASS OF TCutCopyCommand`

TCutCopyCommand subclass that copies or cuts a TTermSelection text range from the terminal view to the clipboard.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsCmdNumber: TCmdNumber; itsView: TView; itsSelection: TTermSelection): TTermCutCopyCmd;` | Creates a TTermCutCopyCmd on heap for command itsCmdNumber operating on terminal view itsView and text selection itsSelection. |

#### `TTermPasteCmd = SUBCLASS OF TPasteCommand`

TPasteCommand subclass that pastes text from the clipboard into the QuickPort terminal input buffer.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsCmdNumber: TCmdNumber; itsView: TView): TTermPasteCmd;` | Creates a TTermPasteCmd on heap for command itsCmdNumber targeting terminal view itsView. |

#### `TTermSelection = SUBCLASS OF TSelection`

TSelection subclass that manages character-coordinate text selections and cursor highlighting in a QuickPort terminal view.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsView: TView; itsKind: INTEGER; itsCharPos: TCoordinate; itsAnchorLPt: LPoint): TTermSelection;` | Creates a TTermSelection on heap in itsView with selection kind itsKind, initial character coordinate itsCharPos, and anchor point itsAnchorLPt. |
| `QPHighlight` | `PROCEDURE QPHighlight(highTransit: THighTransit; cursorpoint: Point);` | Updates the terminal cursor highlight at cursorpoint and paints or erases the selected text range for transition highTransit. |
| `SetRange` | `PROCEDURE SetRange(sXY, eXY: TCoordinate; startIsAnchor: BOOLEAN);` | Sets the terminal selection start and end character coordinates to sXY and eXY, recording sXY as the anchor when startIsAnchor is TRUE (otherwise eXY). |

#### `TGraphView = SUBCLASS OF TView`

TView subclass that stores, scrolls, and replays the recorded QuickDraw PicHandle in the QuickPort graphics panel.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsPanel: TPanel; itsExtent: LRect): TGraphView;` | Creates a TGraphView on heap attached to itsPanel with bounds itsExtent and an initially empty QuickDraw picture and zero scroll offsets. |

#### `TGraphCutCopyCmd = SUBCLASS OF TCutCopyCommand`

TCutCopyCommand subclass that copies the QuickPort graphics panel picture selection to the clipboard.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsCmdNumber: TCmdNumber; itsView: TView; itsSelection: TGraphSelection): TGraphCutCopyCmd;` | Creates a TGraphCutCopyCmd on heap for command itsCmdNumber to copy itsSelection from graphics view itsView to the clipboard. |

#### `TGraphSelection = SUBCLASS OF TSelection`

TSelection subclass representing the selection state of the QuickPort QuickDraw graphics panel for clipboard Copy commands.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsView: TView; itsKind: INTEGER; itsAnchorLPt: LPoint): TGraphSelection;` | Creates a TGraphSelection on heap in graphics view itsView with selection kind itsKind and anchor point itsAnchorLPt. |

#### `TInputBuffer = SUBCLASS OF TObject`

Buffer object holding a run of typed or pasted input characters along with optional modifier-key and keycap metadata.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; fromKeyboard: BOOLEAN): TInputBuffer;` | Creates a TInputBuffer on heap sized for keyboard type-ahead (with a modifier-key array) when fromKeyboard is TRUE or for pasted text otherwise. |

#### `TVanWindow = SUBCLASS OF TWindow`

TWindow subclass implementing the QuickPort 'vanilla' window containing terminal text, optional input, and QuickDraw graphics panels plus type-ahead queues.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsWmgrID: TWindowID): TVanWindow;` | Creates a QuickPort TVanWindow on heap for Window Manager ID itsWmgrID with an initialized keyboard type-ahead buffer queue. |
| `DoKey` | `PROCEDURE DoKey(ascii: CHAR; keycap: Byte; shiftKey, appleKey, optionKey: BOOLEAN);` | Handles an active-window keystroke (ascii, keycap, and Shift/Apple/Option flags), processing XON/XOFF output flow control or appending the key to the type-ahead buffer. |

#### `TTermWriteUnivText = SUBCLASS OF TTKWriteUnivText`

TTKWriteUnivText subclass that streams selected TTermView lines and character attributes into Toolkit universal text format.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsDataArray: TString; itsDataSize: INTEGER; itsView: TTermView): TTermWriteUnivText;` | Creates a TTermWriteUnivText writer on heap using data buffer itsDataArray of size itsDataSize to stream text from itsView. |

#### `TTermDialog = SUBCLASS OF TDialog`

TDialog subclass managing the QuickPort terminal settings dialog for column width (80/132), line wraparound, and periodic tab stops.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsView: TView): TTermDialog;` | Creates a TTermDialog on heap associated with view itsView for configuring terminal columns, wraparound, and tab stops. |
| `SetupDialog` | `PROCEDURE SetupDialog;` | Populates the terminal settings dialog controls from ConsTerm's current column count, wraparound flag, and first tab-stop interval. |

#### `TTermLine = SUBCLASS OF TObject`

Dynamically sized line object storing up to 133 characters and optional per-run font/style attributes for a single terminal row.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE: TTermLine;` | Allocates an empty dynamic TTermLine object on ConsTerm's heap initialized to zero length and maximum character capacity. |

#### `TStdTerm = SUBCLASS OF TObject`

Base QuickPort terminal controller managing screen and scrollback line buffers, cursor position and shape, tab stops, text attributes, and XON/XOFF flow control.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: Theap): TStdTerm;` | Creates and initializes a TStdTerm instance on heap with default 80x24 screen dimensions, block cursor, XON/XOFF keys, cleared tabs, and 12-pitch font metrics. |
| `VWrite` | `PROCEDURE VWrite(VAR str: Tstr255);` | Writes string str to the standard terminal, dispatching a leading control character via QPMoveCursor or CtrKeyWrite and rendering printable text via VStrWrite. |
| `CtrKeyWrite` | `PROCEDURE CtrKeyWrite(ctrch: CHAR);` | Processes a single terminal control character ctrch (such as CR, LF, BS, HT, BEL, or form-feed), updating cursor position, screen text, or speaker beep. |
| `VRead` | `PROCEDURE VRead(VAR ach: char; VAR keycap: Byte; VAR applekey, shiftkey, optionkey: BOOLEAN);` | Reads the next character ach, keycap code, and Apple/Shift/Option modifier flags from the window's type-ahead queue, processing Toolkit events until input arrives. |

#### `TPasTerm = SUBCLASS OF TTERMINAL`

TTerminal subclass that bridges Paslib standard Pascal console and printer I/O hooks to the active QuickPort TStdTerm and UQPPrint routines.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE: TPasTerm;` | Initializes and returns the static TPasTerm bridge object linking Paslib's console and printer hooks to QuickPort. |

---

## Unit UVT100

Implements a DEC VT100 and VT52 video terminal emulator subclass of TStdTerm for QuickPort windows, supporting ANSI/VT52 escape sequences, scrolling regions, character sets, and keypad modes.

- **Import**: `USES UVT100;`
- **Unit kind**: `INTRINSIC` (`UVT100`)
- **Interface dependencies**: `UObject`, `QuickDraw`, `UDraw`, `UABC`, `UTKUniversalText`, `UText`, `UDialog`, `BlkIOIntr`, `UStdTerm`

### Clascal Classes

#### `TVT100 = SUBCLASS OF TStdTerm`

TStdTerm subclass that emulates a DEC VT100/VT52 terminal in a QuickPort window with ANSI/VT52 escape parsing, scrolling margins, alternate character sets, and application keypad modes.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: Theap): TVT100;` | Allocates or initializes a TVT100 terminal emulator on heap with 80x24 dimensions, VT52/ANSI parser state, US character sets, and 12/20-pitch graphics font IDs. |
