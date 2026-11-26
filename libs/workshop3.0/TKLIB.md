# `TKLIB` (`TKLIB.obj`) — Lisa Clascal Application Toolkit Core Library

[Back to Library Index](LIBRARIES.md)

Core Clascal object-oriented application framework (`UObject`, `UDraw`, `UABC`): root `TObject` hierarchy, collections, streams, 32-bit `LRect`/`LPoint` QuickDraw pads, documents, windows, panes, views, selections, menus, and undoable commands.

- **Object file**: `libs/workshop3.0/TKLIB.obj` (Intrinsic library (interface stripped in `libs/workshop3.0/`))
- **Contents**: 3 units, 142 top-level procedures/functions, 39 Clascal classes (540 methods)

> [!NOTE]
> `libs/workshop3.0/TKLIB.obj` in this repository is a link-only stub whose embedded `INTERFACE` text was stripped (`INTRINSIC.LIB` still indexes its units). The unit interfaces and signatures below were extracted from the unstripped Workshop 3.0 / Lisa Office System `TKLIB.OBJ` build library.

## Importing and Linking

```pascal
USES UABC, UDraw, UObject;
```

```sh
pascal/lpc.py --link=IOSPASLIB,SYS1LIB,PRLIB,TKLIB MYPROG
```

## Units in This Library

| Unit | 8-Char Symbol | `USES` Dependencies | Top-Level Routines | Clascal Classes (Methods) | Summary |
|---|---|---|---|---|---|
| [`UABC`](#unit-uabc) | `UABC` | `UnitStd`, `UnitHz`, `UObject`, `SysCall`, `PSysCall`, `QuickDraw`, `FontMgr`, `UDraw`, `PMDecl`, `Events`, `Folders`, `Menus`, `AlertMgr`, `WmlStd`, `WmlCrs`, `WmlSb`, `WmlGrow`, `Scrap`, `PrStdInfo`, `PrPublic`, `FilerComm` | 9 | 25 (324) | Implements the generic Lisa Toolkit application framework (Application Base Classes), orchestrating TProcess event loops, TDocManager document persistence, TClipboard exchange, undoable TCommand execution, TWindow/TPanel/TBand/TPane view hierarchies, TSelection input, TMenuBar menus, and WYSIWYG pagination and printing. |
| [`UDraw`](#unit-udraw) | `UDRAW` | `UnitStd`, `UnitHz`, `UObject`, `SysCall`, `PasLibCall`, `PPasLibC`, `QuickDraw`, `FontMgr`, `Events`, `Folders`, `FilerComm` | 90 | 3 (49) | Extends Lisa QuickDraw with 32-bit coordinate geometry (LPoint, LRect, LPattern), font/type-style mapping (TTypeStyle), and the core display-area and coordinate-projection classes (TArea, TPad, TBranchArea). |
| [`UObject`](#unit-uobject) | `UOBJECT` | `UnitStd`, `UnitHz`, `SysCall`, `PSysCall`, `UClascal`, `PMDecl`, `PMM`, `PasLibCall`, `PPasLibC`, `HWInt` | 43 | 11 (167) | Provides the foundational Clascal root class (TObject), relocatable heap and Lisa OS data-segment management, class metadata and version conversion, dynamic indexed collections (TCollection, TList, TArray, TString, TFile), and sequential scanners/streams (TScanner subclasses). |

---

## Unit UABC

Implements the generic Lisa Toolkit application framework (Application Base Classes), orchestrating TProcess event loops, TDocManager document persistence, TClipboard exchange, undoable TCommand execution, TWindow/TPanel/TBand/TPane view hierarchies, TSelection input, TMenuBar menus, and WYSIWYG pagination and printing.

- **Import**: `USES UABC;`
- **Unit kind**: `INTRINSIC` (`UABC`)
- **Interface dependencies**: `UnitStd`, `UnitHz`, `UObject`, `SysCall`, `PSysCall`, `QuickDraw`, `FontMgr`, `UDraw`, `PMDecl`, `Events`, `Folders`, `Menus`, `AlertMgr`, `WmlStd`, `WmlCrs`, `WmlSb`, `WmlGrow`, `Scrap`, `PrStdInfo`, `PrPublic`, `FilerComm`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `GetPrefixPart` | `PROCEDURE GetPrefixPart(wholeName: S255; VAR filePart: TFilePath);` | Extracts the brace-delimited Lisa OS prefix component (such as '{DxxxTyyy}' or '{Tnn}') from wholeName into filePart. |
| `ToolOfFile` | `FUNCTION ToolOfFile(wholeName: S255): LONGINT;` | Parses and returns the numeric Lisa tool ID from the '{Tnn}' prefix embedded in pathname wholeName, or 0 if none is present. |
| `ToolOfProcess` | `FUNCTION ToolOfProcess(processId: LONGINT): LONGINT;` | Queries Lisa OS process information for processId and returns the numeric tool ID of the tool running in that process. |
| `PicTextBegin` | `PROCEDURE PicTextBegin(alignment: TAlignment);` | Inserts a QuickDraw picture comment marking the start of a grouped text sequence with specified alignment when generating a Clipboard Universal Picture (genClipPic). |
| `PicTextEnd` | `PROCEDURE PicTextEnd;` | Inserts a QuickDraw picture comment marking the end of a grouped text sequence when generating a Clipboard Universal Picture (genClipPic). |
| `PicGrpBegin` | `PROCEDURE PicGrpBegin;` | Inserts a QuickDraw picture comment marking the start of a grouped set of graphic objects when generating a Clipboard Universal Picture (genClipPic). |
| `PicGrpEnd` | `PROCEDURE PicGrpEnd;` | Inserts a QuickDraw picture comment marking the end of a grouped set of graphic objects when generating a Clipboard Universal Picture (genClipPic). |
| `InitProcess` | `PROCEDURE InitProcess;` | Initializes the Toolkit runtime environment, main process data segment and heap, QuickDraw/Window Manager state, and global UABC variables before creating TProcess. |
| `GetTime` | `FUNCTION GetTime: LONGINT;` | Returns the current system elapsed time in centiseconds matching the clock base used for Window Manager eventTime and idle-loop timing. |

### Clascal Classes

#### `TProcess = SUBCLASS OF TObject`

Singleton application controller that manages process startup and shutdown, the main Window Manager and Filer event loop, cursor tracking, phrase-file alerts, inter-process events, and open TDocManager instances.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap): TProcess;` | Allocates and initializes the singleton TProcess application controller in heap and assigns it to global process. |
| `ChangeCursor` | `PROCEDURE ChangeCursor(cursorNumber: TCursorNumber);` | Requests a cursor shape change to cursorNumber by invoking DoCursorChange if cursorNumber differs from cursorShape. |
| `DoCursorChange` | `PROCEDURE DoCursorChange(cursorNumber: TCursorNumber);` | Sets the Window Manager/QuickDraw cursor image corresponding to cursorNumber (subclasses override for custom cursors >= firstUserCursor). |
| `TrackCursor` | `PROCEDURE TrackCursor;` | Updates the mouse cursor shape according to the mouse position over the active window, dialog box, menu bar, or desktop. |
| `ArgAlert` | `PROCEDURE ArgAlert(whichArg: TAlertArg; argText: S255);` | Substitutes string argText for parameter placeholder ^1..^5 (whichArg) in the next Alert Manager message. |
| `Ask` | `FUNCTION Ask(phraseNumber: INTEGER): INTEGER;` | Displays a multi-button question alert for phraseNumber from phraseFile and returns the button number chosen by the user. |
| `BeginWait` | `PROCEDURE BeginWait(phraseNumber: INTEGER);` | Displays a non-modal wait alert box with phraseNumber while a long operation is in progress. |
| `Caution` | `FUNCTION Caution(phraseNumber: INTEGER): BOOLEAN;` | Displays an OK/Cancel caution alert for phraseNumber and returns TRUE if the user clicks OK. |
| `CountAlert` | `PROCEDURE CountAlert(whichCtr: TAlertCounter; counter: INTEGER);` | Sets numeric alert counter whichCtr (7..9) to counter to select singular/plural phrasing in the next alert. |
| `DrawAlert` | `PROCEDURE DrawAlert(phraseNumber: INTEGER; marginLRect: LRect);` | Formats alert text for phraseNumber and draws it directly inside 32-bit rectangle marginLRect on the focused pad. |
| `EndWait` | `PROCEDURE EndWait;` | Dismisses the wait alert box previously put up by BeginWait. |
| `GetAlert` | `PROCEDURE GetAlert(phraseNumber: INTEGER; VAR theText: S255);` | Retrieves the localized phrase string for phraseNumber from phraseFile into theText without displaying an alert box. |
| `Note` | `PROCEDURE Note(phraseNumber: INTEGER);` | Displays an informational Note alert for phraseNumber (or queues it in currentDocument.pendingNote if running in the background). |
| `RememberCommand` | `PROCEDURE RememberCommand(cmdNumber: TCmdNumber);` | Records cmdNumber as the most recent command or user action for ^C and ^K command-name substitution in alerts. |
| `Phrase` | `FUNCTION Phrase(error: INTEGER): INTEGER;` | Maps a Lisa OS or Toolkit error code error to its corresponding alert phrase number (defaulting to phUnknown). |
| `Stop` | `PROCEDURE Stop(phraseNumber: INTEGER);` | Displays a modal Stop alert for phraseNumber to report an unrecoverable command refusal or error. |
| `Commence` | `PROCEDURE Commence(phraseVersion: INTEGER);` | Completes process startup after TProcess.CREATE by opening the tool's phrase file (verifying phraseVersion), menus, and Clipboard. |
| `Complete` | `PROCEDURE Complete(allIsWell: BOOLEAN);` | Suspends or closes all open documents and the Clipboard, releases resources, and terminates the process cleanly (or abnormally if allIsWell is FALSE). |
| `AbortRequest` | `FUNCTION AbortRequest: BOOLEAN;` | Polls the Window Manager event queue for an Apple-Period abort keystroke (when allowAbort is TRUE) and returns TRUE if requested. |
| `AbortXferSequential` | `PROCEDURE AbortXferSequential(whichWay: xReadWrite; pFirst: Ptr; numBytes, chunkSize: LONGINT; fs: TFileScanner);` | Reads or writes numBytes on file scanner fs in chunkSize increments while checking AbortRequest between chunks (setting fs.error := erAborted on abort). |
| `ObeyEvents` | `PROCEDURE ObeyEvents(FUNCTION StopCondition: BOOLEAN);` | Runs the event-dispatch and idle/cursor-tracking loop until amDying becomes TRUE or StopCondition returns TRUE when no events are pending. |
| `ObeyFilerEvent` | `PROCEDURE ObeyFilerEvent;` | Processes a Desktop Manager Filer event (such as opening, putting away, suspending, copying, or printing a document or terminating the tool). |
| `ObeyTheEvent` | `PROCEDURE ObeyTheEvent;` | Dispatches the current Window Manager event (activate, deactivate, button-down, key-down, update, folder move/grow, Filer, or private event). |
| `Run` | `PROCEDURE Run;` | Executes the standard Toolkit application lifecycle by calling Commence, running ObeyEvents until termination, and calling Complete(TRUE). |
| `HandlePrivateEvent` | `PROCEDURE HandlePrivateEvent(typeOfEvent: INTEGER; fromProcess: LONGINT; when: LONGINT; otherData: LONGINT); DEFAULT;` | Hook invoked when an application-defined inter-process event (typeOfEvent >= firstPrivateEvent) arrives from fromProcess. |
| `SendEvent` | `PROCEDURE SendEvent(typeOfEvent: INTEGER; targetProcess: LONGINT; otherData: LONGINT);` | Sends an inter-process event of typeOfEvent with payload otherData to Lisa OS process targetProcess. |
| `BindCurrentDocument` | `PROCEDURE BindCurrentDocument;` | Binds currentDocument's data segment into memory (and unbinds any other document) so its heap and objects are addressable. |
| `NewDocManager` | `FUNCTION NewDocManager(volumePrefix: TFilePath; openAsTool: BOOLEAN): TDocManager; DEFAULT;` | Factory method overridden by subclasses to instantiate an application-specific TDocManager subclass for volumePrefix. |
| `CopyExternalDoc` | `PROCEDURE CopyExternalDoc(VAR error: INTEGER; externalName, volumePrefix: TFilePath); DEFAULT;` | Copies external document files to volumePrefix when the user pastes an application icon from the Clipboard into a Filer folder or disk. |

#### `TDocDirectory = SUBCLASS OF TObject`

Root directory object stored via a document heap's prelude that binds the document's TWindow and saved TClassWorld metadata for persistence and class-version conversion.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsWindow: TWindow; itsClassWorld: TClassWorld): TDocDirectory;` | Allocates and initializes a TDocDirectory in the document heap storing itsWindow and class-version table itsClassWorld. |
| `Adopt` | `PROCEDURE Adopt;` | Updates SELF.classWorld in the document heap to match the running application's current myWorld after version conversion. |

#### `TDocManager = SUBCLASS OF TObject`

Document lifecycle and storage manager that controls a document's Lisa OS data segments, relocatable heap, saved and suspended disk files, version assimilation, and TWindow.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsPathPrefix: TFilePath): TDocManager;` | Allocates and initializes a TDocManager in mainHeap for the document identified by Desktop Manager prefix itsPathPrefix. |
| `WindowWithId` | `FUNCTION WindowWithId(wmgrID: TWindowID): TWindow;` | Returns SELF.window if its Window Manager ID matches wmgrID, or NIL otherwise. |
| `Complete` | `PROCEDURE Complete(allIsWell: BOOLEAN);` | Closes or suspends the document during process shutdown and cleans up its data segments according to allIsWell. |
| `NewWindow` | `FUNCTION NewWindow(heap: THeap; wmgrID: TWindowID): TWindow; DEFAULT;` | Factory method overridden by subclasses to allocate and return the document's TWindow (and views/panels) in heap. |
| `Close` | `PROCEDURE Close(afterSuspend: BOOLEAN);` | Closes external files, frees or unbinds the document's window and data segments (preserving suspend files if afterSuspend is TRUE), and removes SELF from docList. |
| `CloseFiles` | `PROCEDURE CloseFiles;` | Hook for subclasses to close any auxiliary disk files held open by the document before the document closes or suspends. |
| `Open` | `PROCEDURE Open(VAR error: INTEGER; wmgrID: TWindowID; VAR OpenedSuspended: Boolean);` | Opens the document into Window Manager folder wmgrID from its suspended state if present, saved file if present, or as blank stationery, setting OpenedSuspended. |
| `OpenBlank` | `PROCEDURE OpenBlank(VAR error: INTEGER; wmgrID: TWindowID);` | Creates a fresh document data segment and heap, calls NewWindow and window.BlankStationery, and binds it to wmgrID. |
| `OpenSaved` | `PROCEDURE OpenSaved(VAR error: INTEGER; wmgrID: TWindowID);` | Loads the document's saved disk file into new data segments, assimilates class versions, and attaches its window to wmgrID. |
| `OpenSuspended` | `PROCEDURE OpenSuspended(VAR error: INTEGER; wmgrID: TWindowID);` | Reattaches the document's existing suspended Lisa OS data segments, assimilates class versions if needed, and binds its window to wmgrID. |
| `RevertVersion` | `PROCEDURE RevertVersion(VAR error: INTEGER; wmgrID: TWindowID);` | Discards unsaved changes after user confirmation and reloads the document from its last saved disk version (or blank stationery). |
| `SaveVersion` | `PROCEDURE SaveVersion(VAR error: INTEGER; volumePrefix: TFilePath; andContinue: BOOLEAN);` | Writes the document's data segments to its saved disk file at volumePrefix, resetting change counters if andContinue is TRUE. |
| `Suspend` | `PROCEDURE Suspend(VAR error: INTEGER);` | Flushes and unbinds the document's Lisa OS data segments into persistent suspend files so the document can resume instantaneously later. |
| `Assimilate` | `PROCEDURE Assimilate(VAR error: INTEGER);` | Checks the opened document's saved TClassWorld against myWorld, prompts the user if version conversion is needed, and runs ConvertHeap. |
| `Bind` | `PROCEDURE Bind; DEFAULT;` | Maps the document's Lisa OS data segments into the process's logical address space and sets boundDocument to SELF. |
| `ConserveMemory` | `PROCEDURE ConserveMemory(maxExcess: LONGINT; fGC: BOOLEAN);` | Compacts the document heap (optionally running mark-and-sweep garbage collection if fGC is TRUE) and shrinks excess segment space to at most maxExcess. |
| `Deactivate` | `PROCEDURE Deactivate;` | Conserves document memory and unbinds the document's data segments when its window is deactivated. |
| `DfltHeapSize` | `FUNCTION DfltHeapSize: LONGINT;` | Returns the default initial byte size (docDsBytes unless overridden) for a newly created document heap. |
| `ExpandMemory` | `PROCEDURE ExpandMemory(bytesNeeded: LONGINT);` | Grows the document's Lisa OS data segment(s) (adding continuation segments if necessary) to accommodate bytesNeeded additional heap bytes. |
| `KillSegments` | `PROCEDURE KillSegments(first, last: INTEGER);` | Unbinds and deletes the document's Lisa OS data segments from index first through last. |
| `MakeSegments` | `PROCEDURE MakeSegments(VAR error: INTEGER; oldSegments: INTEGER; newDocSize: LONGINT);` | Allocates or resizes the document's Lisa OS data segments from oldSegments count to cover newDocSize total bytes. |
| `ResumeAfterOpen` | `PROCEDURE ResumeAfterOpen(VAR error: INTEGER; wmgrID: TWindowID);` | Reconnects the opened document's TWindow and pane GrafPorts to Window Manager folder wmgrID and restores its saved window dimensions. |
| `SetSegSize` | `PROCEDURE SetSegSize(VAR error: INTEGER; minSize, maxExcess: LONGINT);` | Adjusts the total size of the document's data segments so they hold at least minSize bytes with no more than maxExcess spare bytes. |
| `Unbind` | `PROCEDURE Unbind; DEFAULT;` | Unmaps the document's Lisa OS data segments from the process's address space and clears boundDocument. |

#### `TClipboard = SUBCLASS OF TDocManager`

Specialized TDocManager that manages the system Clipboard document, cut/copy undo backup, and public/private Scrap representations (TView, QuickDraw Picture, Universal Text, and icon).

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap): TClipboard;` | Allocates and initializes the global TClipboard document manager attached to the Window Manager's scrapFolder. |
| `AboutToCut` | `PROCEDURE AboutToCut;` | Prepares the Clipboard before a Cut or Copy command by backing up the previous Clipboard state for UndoCut and claiming ownership. |
| `BeginCut` | `PROCEDURE BeginCut;` | Initializes a fresh Clipboard heap and blank TWindow so a TCutCopyCommand can install a cut or copied TView/TSelection. |
| `EndCut` | `PROCEDURE EndCut;` | Finalizes populating the Clipboard window after a Cut or Copy and updates the visible Clipboard window if open. |
| `CommitCut` | `PROCEDURE CommitCut;` | Discards the backed-up pre-cut Clipboard copy once the Cut or Copy command can no longer be undone. |
| `UndoCut` | `FUNCTION UndoCut: BOOLEAN;` | Restores the previous Clipboard contents saved by AboutToCut when undoing a Cut or Copy command, returning TRUE on success. |
| `Inspect` | `PROCEDURE Inspect;` | Examines the system Scrap upon window activation to update hasView, hasPicture, hasUniversalText, hasIcon, cuttingTool, and cuttingProcessID. |
| `Publicize` | `PROCEDURE Publicize;` | Exports the private Clipboard TView as public QuickDraw Picture and Universal Text Scrap items when switching to another process. |

#### `TCommand = SUBCLASS OF TObject`

Encapsulated user action supporting doPhase, undoPhase, and redoPhase execution, commit finalization, selection highlighting and revelation, and model-object command filtering.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsCmdNumber: TCmdNumber; itsImage: TImage; isUndoable: BOOLEAN; itsRevelation: TRevelation): TCommand;` | Allocates and initializes a TCommand for menu command itsCmdNumber targeting itsImage with undoability flag isUndoable and selection scroll mode itsRevelation. |
| `EachVirtualPart` | `PROCEDURE EachVirtualPart(PROCEDURE DoToObject(filteredObj: TObject));` | Hook overridden by filtered commands to enumerate the post-command virtual sequence of model objects to DoToObject while doing is TRUE. |
| `FilterAndDo` | `PROCEDURE FilterAndDo(actualObj: TObject; PROCEDURE DoToObject(filteredObj: TObject));` | Hook overridden by filtered commands to pass a transformed virtual view of actualObj to DoToObject while the command is uncommitted. |
| `Commit` | `PROCEDURE Commit; DEFAULT;` | Finalizes and makes permanent the effect of an undoable command before it is freed and superseded by a new command. |
| `Perform` | `PROCEDURE Perform(cmdPhase: TCmdPhase); DEFAULT;` | Executes, undoes, or redoes the command's state transition according to cmdPhase (doPhase, undoPhase, or redoPhase). |

#### `TCutCopyCommand = SUBCLASS OF TCommand`

Standard undoable TCommand subclass that coordinates cutting or copying the active TSelection into the global TClipboard.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsCmdNumber: TCmdNumber; itsImage: TImage; isCutCmd: BOOLEAN): TCutCopyCommand;` | Allocates and initializes an undoable Cut (isCutCmd = TRUE) or Copy (isCutCmd = FALSE) command for itsCmdNumber and itsImage. |
| `DoCutCopy` | `PROCEDURE DoCutCopy(clipSelection: TSelection; deleteOriginal: BOOLEAN; cmdPhase: TCmdPhase); DEFAULT;` | Hook overridden by subclasses to copy the active selection into clipSelection in doPhase and delete/restore the original data when deleteOriginal is TRUE. |

#### `TPasteCommand = SUBCLASS OF TCommand`

Standard undoable TCommand subclass that coordinates pasting a TSelection or QuickDraw PicHandle from the global TClipboard into the active view.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsCmdNumber: TCmdNumber; itsImage: TImage): TPasteCommand;` | Allocates and initializes an undoable Paste command for itsCmdNumber and target image itsImage. |
| `DoPaste` | `PROCEDURE DoPaste(clipSelection: TSelection; pic: PicHandle; cmdPhase: TCmdPhase); DEFAULT;` | Hook overridden by subclasses to insert Clipboard selection clipSelection or QuickDraw picture pic during doPhase/redoPhase and remove it in undoPhase. |

#### `TImage = SUBCLASS OF TObject`

Drawable visual element with a 32-bit extentLRect inside a TView, providing hit-testing, mouse tracking, cursor feedback, invalidation, and command-filtered part enumeration.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsExtent: LRect; itsView: TView): TImage;` | Allocates and initializes a TImage in heap with 32-bit bounding box itsExtent belonging to parent view itsView. |
| `CursorAt` | `FUNCTION CursorAt(mouseLPt: lPoint): TCursorNumber; DEFAULT;` | Returns the cursor shape number to display when the mouse is at 32-bit view point mouseLPt (noCursor by default). |
| `Draw` | `PROCEDURE Draw; DEFAULT;` | Renders the visual representation of SELF onto the currently focused TPad. |
| `EachActualPart` | `PROCEDURE EachActualPart(PROCEDURE DoToObject(filteredObj: TObject)); DEFAULT;` | Enumerates the uncommitted/actual model objects backing SELF to DoToObject (delegating by default to the owning TWindow.EachActualPart). |
| `EachVirtualPart` | `PROCEDURE EachVirtualPart(PROCEDURE DoToObject(filteredObj: TObject)); DEFAULT;` | Enumerates SELF's model objects through TWindow.FilterDispatch so active filtered commands present their virtual state to DoToObject. |
| `FilterAndDo` | `PROCEDURE FilterAndDo(actualObj: TObject; PROCEDURE DoToObject(filteredObj: TObject));` | Passes single model object actualObj through TWindow.FilterDispatch for SELF and invokes DoToObject on the resulting virtual object. |
| `HaveView` | `PROCEDURE HaveView(view: TView); DEFAULT;` | Assigns view as the owning TView of SELF (overridden by composite subclasses to propagate to sub-images). |
| `Hit` | `FUNCTION Hit(mouseLPt: lPoint): BOOLEAN; DEFAULT;` | Returns TRUE if 32-bit view coordinate mouseLPt hits SELF (testing LPtInLRect(mouseLPt, SELF.extentLRect) by default). |
| `Invalidate` | `PROCEDURE Invalidate;` | Invalidates SELF.extentLRect on the currently focused pad so it will be redrawn on the next update. |
| `LaunchLayoutBox` | `FUNCTION LaunchLayoutBox(view: TView): TImage; DEFAULT;` | Creates and returns a draggable layout-box TImage representing SELF in page-design view view (or NIL by default). |
| `OffSetBy` | `PROCEDURE OffSetBy(deltaLPt: LPoint); DEFAULT;` | Translates SELF.extentLRect (and any sub-parts in overrides) by 32-bit vector deltaLPt. |
| `OffSetTo` | `PROCEDURE OffSetTo(newTopLeft: LPoint);` | Moves SELF so that SELF.extentLRect.topLeft is positioned at 32-bit view coordinate newTopLeft. |
| `MouseMove` | `PROCEDURE MouseMove(mouseLPt: lPoint); DEFAULT;` | Handles incremental mouse movement to 32-bit view point mouseLPt during a mouse drag that started in SELF. |
| `MousePress` | `PROCEDURE MousePress(mouseLPt: lPoint); DEFAULT;` | Handles an initial mouse-button press at 32-bit view point mouseLPt within SELF. |
| `MouseRelease` | `PROCEDURE MouseRelease; DEFAULT;` | Handles releasing the mouse button at the conclusion of a mouse-tracking sequence in SELF. |
| `MouseTrack` | `PROCEDURE MouseTrack(mPhase: TMousePhase; mouseLPt: LPoint); DEFAULT;` | Clamps mouseLPt to extentLRect (unless allowMouseOutside is TRUE) and dispatches mPress, mMove, or mRelease to MousePress, MouseMove, or MouseRelease. |
| `ReactToPrinterChange` | `PROCEDURE ReactToPrinterChange; DEFAULT;` | Notifies SELF that printer metrics or page formatting changed so it can recalculate layout or pagination. |
| `RecalcExtent` | `PROCEDURE RecalcExtent; DEFAULT;` | Recomputes SELF.extentLRect from its constituent parts when content changes. |
| `Resize` | `PROCEDURE Resize(newExtent: LRect); DEFAULT;` | Changes SELF.extentLRect to newExtent and invalidates affected areas. |
| `SeesSameAs` | `FUNCTION SeesSameAs(image: TImage): BOOLEAN; DEFAULT;` | Returns TRUE if SELF and image view the same underlying model data for command-filtering purposes (defaulting to image = SELF). |

#### `TView = SUBCLASS OF TImage`

Scrollable, optionally printable 32-bit coordinate canvas (TImage subclass) displayed in a TPanel, managing view resolution, page breaks, selections, and cross-panel drag reception.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsPanel: TPanel; itsExtent: LRect; itsPrintManager: TPrintManager; itsDfltMargins: LRect; itsFitPagesPerfectly: BOOLEAN; itsRes: Point; isMainView: BOOLEAN): TView;` | Allocates and initializes a TView in heap attached to itsPanel with 32-bit bounds itsExtent, resolution itsRes, and optional itsPrintManager. |
| `BeInPanel` | `PROCEDURE BeInPanel(panel: TPanel);` | Attaches SELF to panel and creates or updates SELF.screenPad to map between view resolution and screen resolution. |
| `GetStdScroll` | `PROCEDURE GetStdScroll(VAR deltaLStd: LPoint);` | Returns the view's single-step arrow scroll increment in deltaLStd, scaled by the containing panel's zoom factor if zoomed. |
| `MaxPageToPrint` | `FUNCTION MaxPageToPrint: LONGINT;` | Returns the highest 1-based page number containing printable content in SELF (used to default the Print dialog's page range). |
| `AddStripOfPages` | `PROCEDURE AddStripOfPages(vhs: VHSelect); DEFAULT;` | Expands SELF's extentLRect by adding an extra row (vhs = v) or column (vhs = h) strip of pages via printManager. |
| `ForceBreakAt` | `FUNCTION ForceBreakAt(vhs: VHSelect; precedingLocation: LONGINT; proposedLocation: LONGINT): LONGINT;` | Adjusts a proposed automatic page-break coordinate along axis vhs (after precedingLocation) to avoid splitting indivisible content, returning the chosen break coordinate. |
| `RedoBreaks` | `PROCEDURE RedoBreaks; DEFAULT;` | Recomputes automatic page breaks across SELF by delegating to SELF.printManager.RedoBreaks if printable. |
| `RemapManualBreaks` | `PROCEDURE RemapManualBreaks(FUNCTION NewBreakLocation(vhs: VHSelect; oldBreak: LONGINT): LONGINT);` | Updates all manual page-break coordinates in SELF.printManager by applying callback NewBreakLocation along each axis. |
| `DoReceive` | `FUNCTION DoReceive(selection: TSelection; lPtInView: LPoint): BOOLEAN;` | Attempts to accept cross-panel dragged selection dropped at 32-bit view point lPtInView, returning TRUE if accepted (FALSE by default). |
| `OKToDrawIn` | `FUNCTION OKToDrawIn(lRectInView: LRect): BOOLEAN;` | Returns TRUE if incremental direct drawing inside lRectInView is safe without full pane invalidation (FALSE by default). |
| `SetMinViewSize` | `PROCEDURE SetMinViewSize(VAR minLRect: LRect);` | Computes the minimum 32-bit bounding rectangle required to enclose SELF's content into minLRect. |
| `CreateUniversalText` | `PROCEDURE CreateUniversalText;` | Hook invoked by TClipboard.Publicize when SELF is the Clipboard view to write a Universal Text stream representation to the Scrap. |
| `SetFunctionValue` | `PROCEDURE SetFunctionValue(keyword: S255; VAR itsValue: S255);` | Expands heading variable keywords such as 'PAGE' and 'TITLE' into their text values in itsValue during header/footer rendering. |
| `NoSelection` | `FUNCTION NoSelection: TSelection;` | Creates and returns an empty TSelection (with kind = nothingKind) associated with SELF. |

#### `TPaginatedView = SUBCLASS OF TView`

Decorator TView wrapping an unpaginated main TView to display multi-page WYSIWYG page margins, headers/footers, and page numbers on screen.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsUnpaginatedView: TView): TPaginatedView;` | Allocates and initializes a TPaginatedView in heap that projects itsUnpaginatedView onto a grid of simulated pages. |
| `AdornPageOnScreen` | `PROCEDURE AdornPageOnScreen;` | Draws the simulated page border, margin guidelines, page number badge, and visible THeading images on the currently focused TMarginPad. |
| `DepagifyLPoint` | `PROCEDURE DepagifyLPoint(pagLPt: LPoint; VAR unPagLPt: LPoint);` | Maps a 32-bit point pagLPt in paginated screen-page coordinates back to the corresponding point unPagLPt in unpaginatedView. |
| `DoOnPages` | `PROCEDURE DoOnPages(focusOnInterior: BOOLEAN; PROCEDURE DoOnAPage);` | Iterates over all simulated pages intersecting the focused pane's visLRect, focusing theMarginPad or theBodyPad (per focusOnInterior) and invoking DoOnAPage. |
| `PagifyLPoint` | `PROCEDURE PagifyLPoint(unPagLPt: LPoint; VAR pagLPt: LPoint);` | Maps a 32-bit point unPagLPt in unpaginatedView coordinates to its corresponding point pagLPt on the paginated page grid. |

#### `TPageView = SUBCLASS OF TView`

Specialized TView used during interactive page-layout design to display and edit a template page's margins and THeading boxes.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsPrintManager: TPrintManager): TPageView;` | Allocates and initializes a single-page template TPageView for interactively editing margins and THeading boxes of itsPrintManager. |

#### `THeading = SUBCLASS OF TImage`

Header or footer TImage managed by TPrintManager with configurable page alignment, offset, page-number range, and odd/even page filtering.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsPrintManager: TPrintManager; itsExtentLRect: LRect; itsPageAlignment: TPageAlignment; itsOffsetFromAlignment: LPoint): THeading;` | Allocates and initializes a header/footer THeading image for itsPrintManager with bounds itsExtentLRect, corner/center anchor itsPageAlignment, and offset itsOffsetFromAlignment. |
| `ChangePageAlignment` | `PROCEDURE ChangePageAlignment(newPageAlignment: TPageAlignment);` | Changes the heading's anchor corner/center to newPageAlignment and repositions its extentLRect on the page accordingly. |
| `ShouldDraw` | `FUNCTION ShouldDraw(pageNumber: LONGINT): BOOLEAN;` | Returns TRUE if pageNumber falls within minPage..maxPage and satisfies the oddOnly/evenOnly parity filter. |
| `ShouldFrame` | `FUNCTION ShouldFrame: BOOLEAN; DEFAULT;` | Returns TRUE if a dotted layout border should be drawn around the heading (TRUE on screen, FALSE when printing by default). |
| `AdjustForPage` | `PROCEDURE AdjustForPage(pageNumber: LONGINT; editing: BOOLEAN); DEFAULT;` | Hook invoked before drawing or editing the heading on pageNumber so subclasses can substitute page-dependent text variables. |
| `LocateOnPage` | `PROCEDURE LocateOnPage(editing: BOOLEAN);` | Recomputes and offsets SELF.extentLRect relative to printManager.paperLRect according to pageAlignment and offsetFromAlignment. |

#### `TPrintManager = SUBCLASS OF TObject`

Pagination and printing controller for a TView that maintains automatic and manual page breaks, page margins, THeading lists, printer metrics, and LisaPrint job execution.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap): TPrintManager;` | Allocates an uninitialized TPrintManager instance in heap (subsequently configured via Init). |
| `Init` | `PROCEDURE Init(itsMainView: TView; itsDfltMargins: LRect);` | Binds the print manager to itsMainView, sets initial pageMargins to itsDfltMargins, creates page-break arrays and default headings, and computes initial breaks. |
| `AddStripOfPages` | `PROCEDURE AddStripOfPages(vhs: VHSelect);` | Appends one page-width or page-height strip to the main view's extent along axis vhs and recalculates page breaks. |
| `ChangeMargins` | `PROCEDURE ChangeMargins(margins: LRect);` | Updates pageMargins to margins, recomputes contentLRect, relocates headings, and recalculates page breaks across the view. |
| `ClearPageBreaks` | `PROCEDURE ClearPageBreaks(automatic: BOOLEAN);` | Removes all automatic page breaks (if automatic is TRUE) or all manual and automatic page breaks (if FALSE), then recalculates pagination. |
| `DrawBreaks` | `PROCEDURE DrawBreaks(manualOnly: BOOLEAN);` | Draws manual page-break lines (and automatic page-break lines when manualOnly is FALSE) across the focused TPad. |
| `DrawOneBreak` | `PROCEDURE DrawOneBreak(pageBreak: LONGINT; vhs: vhSelect);` | Draws a single horizontal or vertical page-break line at view coordinate pageBreak (using manualBreakPen if negative, autoBreakPen if positive). |
| `DrawPage` | `PROCEDURE DrawPage;` | Renders the currently configured page on theMarginPad and theBodyPad, drawing applicable THeading items, optional body frame, and the main view slice. |
| `EnterPageEditing` | `PROCEDURE EnterPageEditing;` | Switches the view's panel into interactive page-layout design mode using a TPageView and puts up the headings/margins layout dialog box. |
| `GetPageLimits` | `PROCEDURE GetPageLimits(pageNumber: LONGINT; VAR viewLRect: LRect);` | Computes the 32-bit sub-rectangle viewLRect of the main view that maps onto 1-based pageNumber. |
| `NewPaginatedView` | `FUNCTION NewPaginatedView(object: TObject): TPaginatedView;` | Factory method that creates and returns a TPaginatedView wrapping SELF.view for previewing actual pages. |
| `NewPageView` | `FUNCTION NewPageView(object: TObject): TView;` | Factory method that creates and returns a TPageView for designing page margins and headings. |
| `PageWith` | `FUNCTION PageWith(VAR lPtInView: LPoint; VAR strip: Point): LONGINT;` | Clamps lPtInView to the main view and returns the 1-based page number containing it, along with its 2D page-grid indices in strip. |
| `Print` | `PROCEDURE Print(printPref: TPrReserve);` | Executes a LisaPrint job using print preferences printPref, iterating through the selected page range and calling DrawPage or SkipPage. |
| `ReactToPrinterChange` | `PROCEDURE ReactToPrinterChange;` | Updates printerMetrics, paperLRect, printableLRect, contentLRect, headings, and page breaks after the target printer or format changes. |
| `RedoBreaks` | `PROCEDURE RedoBreaks;` | Recomputes all automatic horizontal and vertical page breaks across SELF.view while preserving existing manual breaks. |
| `SetBreak` | `PROCEDURE SetBreak(vhs: VHSelect; where: LONGINT; isAutomatic: BOOLEAN);` | Inserts a manual (isAutomatic = FALSE, stored negative) or automatic (isAutomatic = TRUE) page break at coordinate where along axis vhs. |
| `SetDfltHeadings` | `PROCEDURE SetDfltHeadings; DEFAULT;` | Populates SELF.headings with the application's default initial header/footer THeading objects. |
| `SkipPage` | `PROCEDURE SkipPage(pageNumber: LONGINT);` | Hook invoked during printing for each pageNumber outside the user-requested page range. |

#### `TSelection = SUBCLASS OF TObject`

Representation of the user's current selection in a TView, handling highlighting, mouse-drag selection, keyboard input, idle blinking, undo save/restore, and command dispatch.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsView: TView; itsKind: INTEGER; itsAnchorLPt: LPoint): TSelection;` | Allocates and initializes a TSelection of kind itsKind in itsView anchored at 32-bit view coordinate itsAnchorLPt. |
| `FreedAndReplacedBy` | `FUNCTION FreedAndReplacedBy(selection: TSelection): TSelection;` | Replaces SELF in place with selection via Become(selection) (freeing the old selection) and returns the surviving TSelection handle. |
| `GetHysteresis` | `PROCEDURE GetHysteresis(VAR hysterPt: Point); DEFAULT;` | Returns the minimum pixel movement delta hysterPt (stdHHysteresis, stdVHysteresis by default) required before a click becomes a drag. |
| `HaveView` | `PROCEDURE HaveView(view: TView);` | Rebinds SELF's view, panel, and window references to view (and propagates to coSelection if non-NIL). |
| `MarkChanged` | `PROCEDURE MarkChanged; DEFAULT;` | Increments the change counters on the owning TWindow and bound TDocManager to record that the document has been modified. |
| `CanDoCommand` | `FUNCTION CanDoCommand(cmdNumber: TCmdNumber; VAR checkIt: BOOLEAN): BOOLEAN; DEFAULT;` | Returns TRUE if SELF (or coSelection/window) can execute menu command cmdNumber, setting checkIt if the menu item should display a checkmark. |
| `CantDoCmd` | `PROCEDURE CantDoCmd(cmdNumber: TCmdNumber); DEFAULT;` | Displays an appropriate refusal Stop alert explaining why command cmdNumber cannot be performed on SELF. |
| `CantDoIt` | `PROCEDURE CantDoIt; DEFAULT;` | Displays phNoSel if SELF.kind is nothingKind or phSelCant otherwise to report that an operation is invalid for the current selection. |
| `DoKey` | `PROCEDURE DoKey(ascii: CHAR; keycap: Byte; shiftKey, appleKey, optionKey: BOOLEAN);` | Processes a keyboard event (ascii, keycap, and modifier flags), dispatching Backspace, Forward-Space, Return, Enter, Tab, Clear, or printable characters. |
| `NewCommand` | `FUNCTION NewCommand(cmdNumber: TCmdNumber): TCommand; DEFAULT;` | Creates and returns a TCommand object to execute menu command cmdNumber on SELF (or delegates to coSelection or window.NewCommand). |
| `PerformCommand` | `PROCEDURE PerformCommand(command: TCommand; cmdPhase: TCmdPhase); DEFAULT;` | Executes command phase cmdPhase of command on SELF when the command delegates work to the selection. |
| `IdleBegin` | `PROCEDURE IdleBegin(centiSeconds: LONGINT); DEFAULT;` | Hook invoked when the user stops input for centiSeconds (used by insertion-point selections to begin cursor blinking). |
| `IdleContinue` | `PROCEDURE IdleContinue(centiSeconds: LONGINT); DEFAULT;` | Hook invoked periodically during idle loops at centiSeconds (used to toggle insertion-point caret blinking). |
| `IdleEnd` | `PROCEDURE IdleEnd(centiSeconds: LONGINT); DEFAULT;` | Hook invoked at centiSeconds before processing a new event to restore selection appearance after idling. |
| `KeyBack` | `PROCEDURE KeyBack(fWord: BOOLEAN); DEFAULT;` | Handles the Backspace key on SELF (deleting the preceding word if fWord/Option is TRUE, or refusing via CantDoCmd by default). |
| `KeyChar` | `PROCEDURE KeyChar(ch: CHAR); DEFAULT;` | Handles typing printable character ch into SELF (refusing via CantDoCmd(uTyping) unless overridden). |
| `KeyClear` | `PROCEDURE KeyClear; DEFAULT;` | Handles pressing the Clear key on SELF by invoking window.DoCommand(uClear) after highlighting the Edit menu. |
| `KeyEnter` | `PROCEDURE KeyEnter(dh, dv: INTEGER); DEFAULT;` | Handles pressing the Enter key with directional modifiers (dh, dv) on SELF (refusing via CantDoCmd(uEnter) unless overridden). |
| `KeyForward` | `PROCEDURE KeyForward(fWord: BOOLEAN); DEFAULT;` | Handles forward-delete keystrokes on SELF (by word if fWord is TRUE; refusing via CantDoCmd(uForwardSpace) by default). |
| `KeyPause` | `PROCEDURE KeyPause; DEFAULT;` | Hook invoked during an idle pause after typing so incremental typing commands can update layout or screen state. |
| `KeyReturn` | `PROCEDURE KeyReturn; DEFAULT;` | Handles pressing the Return key on SELF (refusing via CantDoCmd(uReturn) unless overridden). |
| `KeyTab` | `PROCEDURE KeyTab(fBackward: BOOLEAN); DEFAULT;` | Handles pressing Tab (or Shift-Tab when fBackward is TRUE) on SELF (refusing via CantDoCmd(uTab) unless overridden). |
| `SelectParagraphs` | `PROCEDURE SelectParagraphs;` | Expands a text selection to paragraph boundaries on triple-click (forwarding to coSelection if non-NIL). |
| `Highlight` | `PROCEDURE Highlight(highTransit: THighTransit); DEFAULT;` | Draws or removes visual highlighting for SELF on the currently focused pane according to transition highTransit. |
| `DeSelect` | `PROCEDURE DeSelect; DEFAULT;` | Unhighlights SELF across all panes of its panel and replaces SELF with view.NoSelection. |
| `DrawGhost` | `PROCEDURE DrawGhost; DEFAULT;` | Draws an XOR ghost outline of SELF during a cross-panel drag operation. |
| `MousePress` | `PROCEDURE MousePress(mouseLPt: LPoint); DEFAULT;` | Initiates selection tracking at 32-bit view point mouseLPt (delegating to view.MouseTrack by default). |
| `MouseMove` | `PROCEDURE MouseMove(mouseLPt: LPoint); DEFAULT;` | Updates the selection as the mouse drags to 32-bit view point mouseLPt. |
| `MouseRelease` | `PROCEDURE MouseRelease; DEFAULT;` | Completes selection tracking when the mouse button is released. |
| `MoveBackToAnchor` | `PROCEDURE MoveBackToAnchor; DEFAULT;` | Restores a dragged selection to its original anchor position when a cross-panel drop is refused by the destination TView.DoReceive. |
| `Restore` | `PROCEDURE Restore; DEFAULT;` | Swaps panel.selection and panel.undoSelection to restore the saved selection during Undo or Redo. |
| `Save` | `PROCEDURE Save; DEFAULT;` | Clones SELF into panel.undoSelection before executing an undoable command so the prior selection can be restored on Undo. |
| `Reveal` | `PROCEDURE Reveal(asMuchAsPossible: BOOLEAN); DEFAULT;` | Scrolls SELF.panel as needed to bring SELF.boundLRect into view (showing as much as possible if asMuchAsPossible is TRUE). |

#### `TWindow = SUBCLASS OF TArea`

Top-level Lisa Window Manager folder (TArea subclass) containing a tree of TPanel splits and managing activation, menus, undoable command history, selections, dialog boxes, and printing.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsWmgrID: TWindowID; itsResizability: BOOLEAN): TWindow;` | Allocates and initializes a TWindow in heap associated with Window Manager GrafPort itsWmgrID and grow-box flag itsResizability. |
| `GetTitle` | `PROCEDURE GetTitle(VAR title: S255);` | Retrieves the title string displayed in the Window Manager folder tab of SELF into title. |
| `IsActive` | `FUNCTION IsActive: BOOLEAN;` | Returns TRUE if SELF is currently the active frontmost window (SELF.wmgrID = activeWindowID). |
| `IsVisible` | `FUNCTION IsVisible: BOOLEAN;` | Returns TRUE if SELF's Window Manager GrafPort is currently visible on the Lisa desktop. |
| `SetWmgrId` | `PROCEDURE SetWmgrId(itsWmgrId: TWindowID);` | Sets SELF.wmgrID to itsWmgrId and updates the port GrafPtr of every TPane across all panels in the window. |
| `DownEventAt` | `PROCEDURE DownEventAt(mousePt: Point); DEFAULT;` | Updates multi-click state in clickState (single, double, or triple click and modifier keys) and dispatches a mouse-down at mousePt. |
| `PutUpDialogBox` | `PROCEDURE PutUpDialogBox(dialogBox: TDialogBox); DEFAULT;` | Attaches modal or modeless dialogBox to SELF, displays it via Appear, and shifts selection focus to it. |
| `TakeDownDialogBox` | `PROCEDURE TakeDownDialogBox; DEFAULT;` | Dismisses and hides SELF.dialogBox, restores selection focus to SELF, and frees the dialog box if freeOnDismissal is TRUE. |
| `Highlight` | `PROCEDURE Highlight(highTransit: THighTransit); DEFAULT;` | Applies selection highlight transition highTransit to selectWindow's active selection across all panes of its selectPanel. |
| `Update` | `PROCEDURE Update(doHilite: BOOLEAN); DEFAULT;` | Processes pending QuickDraw update regions for SELF (and its dialogBox if present) via BeginUpdate/EndUpdate, optionally highlighting the selection. |
| `DownInSizeBox` | `PROCEDURE DownInSizeBox(mousePt: Point); DEFAULT;` | Tracks dragging of the window's bottom-right grow icon from mousePt using ResizeFeedback and resizes the window folder. |
| `Resize` | `PROCEDURE Resize(moving: BOOLEAN); DEFAULT;` | Synchronizes SELF's outer/inner bounds and panel tree with its Window Manager portRect after a move (moving = TRUE) or grow. |
| `ResizeTo` | `PROCEDURE ResizeTo(newSize: Point); DEFAULT;` | Resizes SELF's Window Manager folder to inner dimensions newSize and reflows all child panels. |
| `CanDoCommand` | `FUNCTION CanDoCommand(cmdNumber: TCmdNumber; VAR checkIt: BOOLEAN): BOOLEAN; DEFAULT;` | Returns TRUE if SELF can currently perform menu command cmdNumber (delegating to CanDoStdCommand by default) and sets checkIt. |
| `CanDoStdCommand` | `FUNCTION CanDoStdCommand(cmdNumber: TCmdNumber; VAR checkIt: BOOLEAN): BOOLEAN; DEFAULT;` | Evaluates enablement and checkmark state checkIt for standard Toolkit File/Print, Edit, Undo/Redo, Page Layout, Zoom, and Debug commands. |
| `CommitLast` | `PROCEDURE CommitLast; DEFAULT;` | Commits SELF.lastCmd (calling lastCmd.Commit if doing is TRUE) and clears lastCmd so it can no longer be undone. |
| `DoCommand` | `PROCEDURE DoCommand(cmdNumber: TCmdNumber); DEFAULT;` | Creates a TCommand for cmdNumber via selectPanel.selection.NewCommand and executes it via PerformCommand. |
| `LoadMenuBar` | `PROCEDURE LoadMenuBar; DEFAULT;` | Clears and populates global menuBar with all menus for which SELF.WantMenu returns TRUE. |
| `MenuEventAt` | `PROCEDURE MenuEventAt(mousePt: Point); DEFAULT;` | Updates menu item enablement and checkmarks via SetupMenus, tracks a menu-bar click at mousePt, and executes the chosen command. |
| `NewCommand` | `FUNCTION NewCommand(cmdNumber: TCmdNumber): TCommand; DEFAULT;` | Creates a TCommand for cmdNumber when the active selection delegates command creation to the window (calling NewStdCommand by default). |
| `NewStdCommand` | `FUNCTION NewStdCommand(cmdNumber: TCmdNumber): TCommand;` | Instantiates or executes built-in Toolkit commands (Save, Revert, Set Aside, Put Away, Print, Cut, Copy, Paste, Undo/Redo, Page Preview, Zoom, Breaks, and Debug). |
| `PerformCommand` | `PROCEDURE PerformCommand(newCommand: TCommand);` | Commits the prior command, saves the selection if newCommand is undoable, unhighlights, runs newCommand.Perform(doPhase), reveals, and rehighlights. |
| `PerformLast` | `PROCEDURE PerformLast(cmdPhase: TCmdPhase);` | Runs undoPhase or redoPhase on SELF.lastCmd, swapping the current and saved undo selections and updating highlighting and scroll position. |
| `SaveCommand` | `PROCEDURE SaveCommand(command: TCommand);` | Replaces and frees any previous SELF.lastCmd, storing command as the new undoable command (or freeing command immediately if not undoable). |
| `SetupMenus` | `PROCEDURE SetupMenus;` | Queries selectWindow.selectPanel.selection.CanDoCommand for every loaded menu command, updating Undo/Redo wording and item enable/check states. |
| `UndoLast` | `PROCEDURE UndoLast;` | Toggles SELF.lastCmd between undoPhase and redoPhase via PerformLast, or shows a Stop alert if no undoable command exists. |
| `WantMenu` | `FUNCTION WantMenu(menuID: INTEGER; inClipboard: BOOLEAN): BOOLEAN;` | Returns TRUE if menu resource menuID should be installed in the menu bar when SELF (or the Clipboard if inClipboard) is active. |
| `AbortEvent` | `PROCEDURE AbortEvent;` | Hook invoked when an abort event arrives from the Window Manager while SELF is active. |
| `RestoreSelection` | `PROCEDURE RestoreSelection;` | Restores the saved undo selection and undo selectPanel/selectWindow when undoing or redoing lastCmd. |
| `RevealSelection` | `PROCEDURE RevealSelection(asMuchAsPossible, doHilite: BOOLEAN);` | Scrolls selectWindow.selectPanel to reveal its active selection (per asMuchAsPossible) and highlights it if doHilite is TRUE. |
| `SaveSelection` | `PROCEDURE SaveSelection;` | Saves the current selectWindow, selectPanel, clickPanel, and cloned selection state before performing an undoable command. |
| `Activate` | `PROCEDURE Activate;` | Activates SELF on a Window Manager activate event by updating, framing active scroll bars, checking printer metrics, inspecting the Clipboard, and loading menus. |
| `Deactivate` | `PROCEDURE Deactivate;` | Deactivates SELF by committing lastCmd, hiding any dialog box, dimming scroll bars, recording a Window Manager suspend picture, publicizing the Clipboard, and giving up control. |
| `BlankStationery` | `PROCEDURE BlankStationery; DEFAULT;` | Initializes a newly created blank document window (creating a default scrollable/splittable TPanel and status TView unless overridden). |
| `StashPicture` | `PROCEDURE StashPicture(highTransit: THighTransit);` | Records a QuickDraw picture of SELF's entire outerRect into the Window Manager folder via WMOpenPicture/WMClosePicture for desktop display while inactive. |
| `NameToPrefix` | `PROCEDURE NameToPrefix(VAR error, offset: INTEGER; VAR name, prefix: TFilePath);` | Requests the Desktop Manager to translate hierarchical desktop icon pathname name ('<disk<folder<icon') into Lisa OS file prefix prefix. |
| `PrefixToName` | `PROCEDURE PrefixToName(VAR error, offset: INTEGER; VAR prefix, name: TFilePath);` | Requests the Desktop Manager to translate Lisa OS file prefix ('-vol-{DxxxTyyy}') into hierarchical desktop icon pathname name. |
| `CursorFeedback` | `FUNCTION CursorFeedback: TCursorNumber;` | Determines and returns the appropriate TCursorNumber for the current mouse location within SELF or its active dialogBox. |
| `PickStdCursor` | `PROCEDURE PickStdCursor;` | Samples the current mouse position in SELF's GrafPort and updates the cursor via process.ChangeCursor(SELF.CursorFeedback). |
| `AcceptNewPrintingInfo` | `PROCEDURE AcceptNewPrintingInfo(document: TDocManager; prReserve: TPrReserve);` | Stores updated printer preference record prReserve into document, refreshes printerMetrics, and notifies each panel's view via ReactToPrinterChange. |
| `ChkPrMismatch` | `PROCEDURE ChkPrMismatch;` | Validates the document's saved print preferences against currently installed printers upon activation and updates metrics if changed. |
| `GetPrinterMetrics` | `PROCEDURE GetPrinterMetrics;` | Extracts paper bounds, printable bounds, and printer DPI resolution from the bound document's print preferences into SELF.printerMetrics. |
| `Print` | `PROCEDURE Print(panel: TPanel; nixPgRange: BOOLEAN; nixWholeDialog: BOOLEAN);` | Runs the LisaPrint dialog (optionally suppressing page-range or the entire dialog) and prints panel's view. |
| `EachActualPart` | `PROCEDURE EachActualPart(PROCEDURE DoToObject(filteredObj: TObject));` | Hook overridden by window subclasses to enumerate the window's uncommitted model objects to DoToObject during command filtering. |
| `EachVirtualPart` | `PROCEDURE EachVirtualPart(PROCEDURE DoToObject(filteredObj: TObject));` | Enumerates the window's virtual model objects to DoToObject by dispatching through FilterDispatch. |
| `FilterAndDo` | `PROCEDURE FilterAndDo(actualObj: TObject; PROCEDURE DoToObject(filteredObj: TObject));` | Passes model object actualObj through FilterDispatch to apply any active filtered TCommand before calling DoToObject. |
| `FilterDispatch` | `PROCEDURE FilterDispatch(actualObj: TObject; image: TImage; PROCEDURE DoToObject(filteredObj: TObject));` | Routes part enumeration or single-object lookup through lastCmd.FilterAndDo/EachVirtualPart if lastCmd is actively filtering image, or directly to actual objects otherwise. |
| `IdleBegin` | `PROCEDURE IdleBegin(centiSeconds: LONGINT);` | Forwards idle-start notification at centiSeconds to the active selection in selectWindow.selectPanel. |
| `IdleContinue` | `PROCEDURE IdleContinue(centiSeconds: LONGINT);` | Forwards periodic idle notification at centiSeconds to the active selection in selectWindow.selectPanel. |
| `IdleEnd` | `PROCEDURE IdleEnd(centiSeconds: LONGINT);` | Forwards idle-termination notification at centiSeconds to the active selection in selectWindow.selectPanel. |

#### `TDialogBox = SUBCLASS OF TWindow`

Subordinate TWindow displayed for modal or modeless dialogs with configurable responses to keystrokes, menu commands, and clicks in the main window.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsResizability: BOOLEAN; itsHeight: INTEGER; itsKeyResponse, itsMenuResponse, itsDownInMainWindowResponse: TDiResponse): TDialogBox;` | Allocates and initializes a TDialogBox of pixel height itsHeight attached to dialogFolder with dispatch rules for keys, menus, and main-window clicks. |
| `Appear` | `PROCEDURE Appear;` | Displays the dialog box window on screen via the Window Manager and activates its selection. |
| `BeDismissed` | `PROCEDURE BeDismissed; DEFAULT;` | Hook invoked when the dialog box is dismissed via diDismissDialogBox (calling currentWindow.TakeDownDialogBox by default). |
| `Disappear` | `PROCEDURE Disappear; DEFAULT;` | Unhighlights the dialog selection and hides the dialogFolder window from the screen. |

#### `TBand = SUBCLASS OF TArea`

Row or column strip of TPane viewports within a TPanel controlled by a single TScroller scroll box so its panes scroll together along scrollDir.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsPanel: TPanel; itsInnerRect: Rect; itsScroller: TScroller; itsDir: VHSelect): TBand;` | Allocates and initializes a TBand of panes in itsPanel with bounds itsInnerRect controlled by scroll box itsScroller along axis itsDir. |
| `ViewLCd` | `FUNCTION ViewLCd: LONGINT;` | Returns the 32-bit view coordinate currently aligned with the top (scrollDir = v) or left (scrollDir = h) edge of the band's panes. |
| `OffsetPanes` | `PROCEDURE OffsetPanes(deltaLPt: LPoint);` | Offsets the viewedLRect of every TPane in the band by 32-bit vector deltaLPt without redrawing. |
| `ScrollBy` | `PROCEDURE ScrollBy(deltaLCd: LONGINT);` | Scrolls all panes in the band (and any synchronized TSideBand) along scrollDir by 32-bit deltaLCd, blitting pixels with ScrollRect and updating the scroll thumb. |
| `ScrollStep` | `PROCEDURE ScrollStep(icon: TEnumIcons; deltaLStd: LONGINT);` | Performs a discrete scroll step along scrollDir in response to clicking scroll-bar icon (arrow step deltaLStd or page flip). |
| `ScrollTo` | `PROCEDURE ScrollTo(viewLCd: LONGINT);` | Scrolls the band along scrollDir so its leading edge displays 32-bit view coordinate viewLCd. |
| `ThumbPos` | `FUNCTION ThumbPos: INTEGER;` | Computes and returns the proportional 0..1000 scroll-bar thumb position representing the band's current ViewLCd within its scrollable range. |
| `ThumbTo` | `PROCEDURE ThumbTo(newThumbPos: INTEGER);` | Scrolls all panes in the band to the 32-bit view coordinate corresponding to proportional thumb position newThumbPos. |
| `ResizePanes` | `PROCEDURE ResizePanes(newViewLCd: LONGINT);` | Updates the viewedLRect of each pane in the band so its leading edge starts at 32-bit view coordinate newViewLCd. |

#### `TSideBand = SUBCLASS OF TBand`

Ruler or header TBand docked along the top, bottom, left, or right edge of a TPanel that stays synchronized along its scroll axis with an adjacent content TBand.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsPanel: TPanel; itsInnerRect: Rect; itsDir: VHSelect; itsTopOrLeft: BOOLEAN; itsViewLCd: LONGINT): TSideBand;` | Allocates and initializes a non-scrolled header/ruler TSideBand along the top/left (itsTopOrLeft = TRUE) or bottom/right edge of itsPanel. |
| `CoBand` | `FUNCTION CoBand: TBand;` | Returns the adjacent interior content TBand in the same panel whose orthogonal splits and scrolling stay synchronized with SELF. |

#### `TPanel = SUBCLASS OF TArea`

Subdividable rectangular area inside a TWindow that displays a TView through one or more split TPane viewports with optional scroll bars, side bands, zooming, and page preview.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsWindow: TWindow; minHeight, minWidth: INTEGER; itsVAbilities, itsHAbilities: TAbilities): TPanel;` | Allocates and initializes a TPanel in itsWindow with minimum inner size (minWidth, minHeight) and vertical/horizontal scroll/split abilities. |
| `HaveView` | `PROCEDURE HaveView(view: TView);` | Installs view into SELF (updating currentView, panes, and selection) and refreshes scroll bars. |
| `NewView` | `FUNCTION NewView(object: TObject; itsExtent: LRect; itsPrintManager: TPrintManager; itsDfltMargins: LRect; itsFitPerfectlyOnPages: BOOLEAN): TView;` | Convenience helper that creates a printable main TView for SELF with bounds itsExtent, print manager itsPrintManager, and margins itsDfltMargins. |
| `NewStatusView` | `FUNCTION NewStatusView(object: TObject; itsExtent: LRect): TView;` | Convenience helper that creates a non-printable status/control TView of bounds itsExtent at screen resolution for SELF. |
| `ComputeContentRect` | `PROCEDURE ComputeContentRect;` | Calculates SELF.contentRect by insetting innerRect by any active top/left and bottom/right TSideBand thicknesses. |
| `DecideAboutBars` | `PROCEDURE DecideAboutBars(newOuterRect: Rect);` | Determines whether horizontal and vertical scroll bars and a grow box should be visible for newOuterRect based on panel abilities and window borders. |
| `FindBranchThatIsResized` | `FUNCTION FindBranchThatIsResized: TBranchArea;` | Walks up parentBranch ancestors to locate the TBranchArea split divider (if any) that dragging SELF's bottom-right grow icon resizes. |
| `PaneShowing` | `FUNCTION PaneShowing(anLRect: LRect): TPane;` | Returns the first TPane in SELF whose viewedLRect intersects 32-bit view rectangle anLRect, or NIL if none shows it. |
| `SetInnerRect` | `PROCEDURE SetInnerRect(newInnerRect: Rect); OVERRIDE;` | Sets SELF.innerRect to newInnerRect, updates contentRect, and recomputes outerRect including visible scroll bars. |
| `SetOuterRect` | `PROCEDURE SetOuterRect(newOuterRect: Rect); OVERRIDE;` | Configures scroll-bar visibility for newOuterRect, sets outerRect and innerRect, and updates contentRect. |
| `Divide` | `FUNCTION Divide(vhs: VHSelect; fromEdgeOfPanel: INTEGER; units: TUnitsFromEdge; whoCanResizeIt: TResizability; minSize: INTEGER; itsVAbilities, itsHAbilities: TAbilities): TPanel;` | Creates a new sibling TPanel and inserts a TBranchArea splitting SELF's space along axis vhs at fromEdgeOfPanel (in pixels or percent). |
| `Insert` | `PROCEDURE Insert(panel: TPanel; vhs: VHSelect; fromEdgeOfPanel: INTEGER; units: TUnitsFromEdge; whoCanResizeIt: TResizability);` | Splits SELF's space with existing panel along axis vhs at fromEdgeOfPanel by inserting a TBranchArea in the window's panelTree. |
| `Remove` | `PROCEDURE Remove;` | Detaches SELF from its window's panelTree and panels list (without freeing SELF) and expands its sibling area to fill the vacated space. |
| `Replace` | `PROCEDURE Replace(panel: TPanel);` | Substitutes panel for SELF in the window's panelTree and panels list (without freeing SELF) and resizes panel to SELF's bounds. |
| `DownInSizeBox` | `PROCEDURE DownInSizeBox(mousePt: Point);` | Tracks dragging of the panel's internal split-resize box from mousePt and redivides resizeBranch (or delegates to window.DownInSizeBox). |
| `HitScroller` | `PROCEDURE HitScroller(vhs: VHSelect; mousePt: Point; scroller: TScroller; icon: TEnumIcons);` | Handles a mouse press at mousePt on icon (thumb, arrows, page-flip, gray bar, or split skewer) of scroller along axis vhs. |
| `BeginSelection` | `PROCEDURE BeginSelection;` | Prepares SELF to start a new mouse selection by committing any pending command, deselecting the prior selection, and making SELF the selectPanel. |
| `BeSelectPanel` | `PROCEDURE BeSelectPanel(inSelectWindow: BOOLEAN);` | Designates SELF as its window's active selectPanel (and makes SELF.window the selectWindow if inSelectWindow is TRUE). |
| `CursorAt` | `FUNCTION CursorAt(mousePt: Point): TCursorNumber;` | Returns the TCursorNumber for window-relative point mousePt (arrow over scroll bars, or delegating to the TPane containing mousePt). |
| `Highlight` | `PROCEDURE Highlight(selection: TSelection; highTransit: THighTransit);` | Focuses each TPane of SELF in turn and draws selection with highlight transition highTransit. |
| `Invalidate` | `PROCEDURE Invalidate;` | Marks SELF.outerRect invalid in its window's GrafPort so the entire panel redraws on the next update. |
| `InvalLRect` | `PROCEDURE InvalLRect(lRectInView: LRect);` | Invalidates 32-bit view rectangle lRectInView across every TPane currently viewing SELF. |
| `OKToDrawIn` | `FUNCTION OKToDrawIn(lRectInView: LRect): BOOLEAN;` | Returns TRUE if direct drawing in lRectInView is permitted by currentView and at most one pane displays lRectInView. |
| `OnAllPadsDo` | `PROCEDURE OnAllPadsDo(PROCEDURE DoOnThePad);` | Iterates over every TPane in SELF, focusing each pane and invoking callback DoOnThePad whenever its visLRect is non-empty. |
| `Rescroll` | `PROCEDURE Rescroll;` | Clamps pane scroll positions after a view resize or zoom change and updates all scroll-bar thumbs. |
| `SetZoomFactor` | `PROCEDURE SetZoomFactor(zoomNumerator, zoomDenominator: Point);` | Sets the panel's magnification ratio to zoomNumerator / zoomDenominator, updates all panes, rescrolls, and invalidates the panel. |
| `Preview` | `PROCEDURE Preview(newMode: TPreviewMode);` | Switches the panel's page-preview mode to newMode (mPrvwMargins via TPaginatedView, mPrvwBreaks, or mPrvwOff) and refreshes the display. |
| `PrintView` | `PROCEDURE PrintView(printPref: TPrReserve);` | Prints SELF.view through its TPrintManager using print preference record printPref. |
| `AutoScroll` | `PROCEDURE AutoScroll(mousePt: Point);` | Automatically scrolls the clicked pane when mousePt is dragged outside its innerRect during mouse tracking. |
| `DoScrolling` | `PROCEDURE DoScrolling(inArea: TArea; itsPane: TPane; hOk, vOk: BOOLEAN; VAR deltaLPt: LPoint);` | Scrolls inArea (either a single TPane or an entire TBand) by 32-bit deltaLPt along axes permitted by hOk and vOk. |
| `PaneToScroll` | `FUNCTION PaneToScroll(VAR anLRect: LRect; hMinToSee, vMinToSee: INTEGER): TPane;` | Selects and returns the best TPane to scroll so at least (hMinToSee, vMinToSee) pixels of anLRect become visible, or NIL if already visible. |
| `RevealLRect` | `PROCEDURE RevealLRect(VAR anLRect: LRect; hMinToSee, vMinToSee: INTEGER);` | Scrolls the pane chosen by PaneToScroll (if any) so that at least (hMinToSee, vMinToSee) pixels of anLRect are visible. |
| `CleanUpPanes` | `PROCEDURE CleanUpPanes(deleteList: TList);` | Removes and frees all obsolete panes in deleteList from SELF.panes and band pane lists while preserving lastClick coordinates. |
| `MakeBand` | `PROCEDURE MakeBand(vhs: VHSelect; scroller, prevScroller: TScroller);` | Creates a new split TBand and its cross-band TPane tiles along axis vhs when splitting prevScroller into scroller. |
| `MoveSplitBefore` | `PROCEDURE MoveSplitBefore(scroller: TScroller; newSkwrCd: INTEGER);` | Repositions or merges the split divider preceding scroller to coordinate newSkwrCd, resizing or removing affected bands and panes. |
| `NewBand` | `FUNCTION NewBand(heap: THeap; myInnerRect: Rect; scroller: TScroller; vhs: VHSelect): TBand;` | Factory method that allocates and returns a new TBand for SELF with bounds myInnerRect and scroll box scroller along axis vhs. |
| `NewPane` | `FUNCTION NewPane(heap: THeap; innerRect: Rect; viewedLRect: LRect): TPane;` | Factory method that allocates and returns a new TPane in heap for SELF mapping viewedLRect into innerRect. |
| `RemakePanes` | `PROCEDURE RemakePanes;` | Rebuilds the initial bands and pane grid for SELF from its contentRect, side bands, and currentView. |
| `RememberSplit` | `PROCEDURE RememberSplit(vhs: VHSelect; atCd: INTEGER);` | Records a split coordinate atCd along axis vhs in deletedSplits when panel shrinking temporarily forces a split pane out of existence. |
| `RepaneOrthogonalBands` | `PROCEDURE RepaneOrthogonalBands(vhs: VHSelect);` | Rebuilds the pane lists of bands orthogonal to axis vhs so row and column bands reference the exact same TPane grid. |
| `RestoreSplits` | `PROCEDURE RestoreSplits;` | Recreates previously saved pane splits from deletedSplits when the panel grows large enough to accommodate them again. |
| `ShowSideBand` | `PROCEDURE ShowSideBand(vhs: VHSelect; topOrLeft: BOOLEAN; size: INTEGER; viewLCd: LONGINT);` | Creates, resizes, or removes a top/left or bottom/right TSideBand of thickness size viewing coordinate viewLCd along axis vhs. |
| `SideBandRect` | `PROCEDURE SideBandRect(vhs: VHSelect; topOrLeft: BOOLEAN; VAR bandRect: Rect);` | Computes the innerRect in bandRect for a top/left or bottom/right TSideBand along axis vhs relative to SELF.contentRect. |
| `ResizeBand` | `PROCEDURE ResizeBand(vhs: VHSelect; band: TBand; newViewLCd: LONGINT; fInvalidate: BOOLEAN);` | Changes the starting view coordinate of band along axis vhs to newViewLCd, invalidating affected panes if fInvalidate is TRUE. |

#### `TPane = SUBCLASS OF TPad`

Individual TPad viewport tile within a TPanel (at the intersection of a horizontal and vertical TBand) that renders a scrolled portion of currentView and tracks mouse input.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsPanel: TPanel; itsInnerRect: Rect; itsViewedLRect: LRect): TPane;` | Allocates and initializes a TPane in heap inside itsPanel mapping 32-bit view rectangle itsViewedLRect into port rectangle itsInnerRect. |
| `HaveView` | `PROCEDURE HaveView(view: TView);` | Binds the pane to view, reconfiguring its pad resolutions, zoom factor, and viewedLRect. |
| `GetScrollLimits` | `PROCEDURE GetScrollLimits(VAR viewedLRect, scrollableLRect: LRect);` | Returns the pane's currently visible 32-bit viewedLRect and the total scrollableLRect bounds of currentView (including scrollPastEnd). |
| `MouseTrack` | `PROCEDURE MouseTrack(mPhase: TMousePhase; mousePt: Point);` | Handles mouse press, drag (with hysteresis, autoscrolling, and cross-panel ghosting), and release at port coordinate mousePt in SELF. |
| `CursorAt` | `FUNCTION CursorAt(mousePt: Point): TCursorNumber;` | Converts port coordinate mousePt to a 32-bit view LPoint and returns currentView.CursorAt (defaulting to arrowCursor if noCursor). |
| `Resize` | `PROCEDURE Resize(newInnerRect: Rect; vhs: VHSelect);` | Resizes the pane's innerRect to newInnerRect along axis vhs and updates its projected viewedLRect. |
| `ScrollBy` | `PROCEDURE ScrollBy(VAR deltaLPt: LPoint);` | Scrolls the pane's orthogonal horizontal and vertical TBands by 32-bit vector deltaLPt and updates their scroll thumbs. |
| `ScrollToReveal` | `PROCEDURE ScrollToReveal(VAR anLRect: LRect; hMinToSee, vMinToSee: INTEGER);` | Computes the minimal scroll delta needed to bring (hMinToSee, vMinToSee) of anLRect into SELF and scrolls via ScrollBy. |

#### `TMarginPad = SUBCLASS OF TPad`

Full-page outer TPad used during printing and TPaginatedView rendering to project page coordinates for drawing margins, page adornments, and THeading headers/footers.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap): TMarginPad;` | Allocates an unconfigured TMarginPad and its companion TBodyPad in heap for rendering page margins and headings. |
| `Rework` | `PROCEDURE Rework(itsView: TView; itsOrigin: Point; itsRes: Point; itsPageNumber: LONGINT; itsZoomFactor: TScaler; itsPort: GrafPtr);` | Configures SELF and its bodyPad to project page itsPageNumber of itsView at resolution itsRes, origin itsOrigin, and zoom itsZoomFactor in itsPort. |
| `SetForPage` | `PROCEDURE SetForPage(itsPageNumber: LONGINT; itsOrigin: Point);` | Retargets SELF and its bodyPad to page number itsPageNumber at port origin itsOrigin while keeping existing resolution and zoom settings. |

#### `TBodyPad = SUBCLASS OF TPad`

Page-interior TPad nested inside a TMarginPad that clips and maps a single page's contentLRect slice of the main TView during printing or page preview.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsMarginPad: TMarginPad): TBodyPad;` | Allocates and initializes a TBodyPad in heap paired with outer page pad itsMarginPad. |
| `Recompute` | `PROCEDURE Recompute;` | Recalculates SELF's innerRect, nonNullBody clip bounds, and 32-bit viewedLRect slice from marginPad's current page and printManager. |
| `SetForPage` | `PROCEDURE SetForPage(itsPageNumber: LONGINT);` | Updates SELF's mapped 32-bit view slice and nonNullBody clipping rectangle for 1-based page itsPageNumber. |

#### `TScroller = SUBCLASS OF TObject`

Wrapper around a Lisa Window Manager scroll box (TSBoxID) inside a TScrollBar, managing thumb positioning, scroll icons, and split-skewer dragging for a TBand.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsScrollBar: TScrollBar; itsId: TSBoxID): TScroller;` | Allocates and initializes a TScroller wrapper in heap for Window Manager scroll-box handle itsId inside itsScrollBar. |
| `GetSize` | `PROCEDURE GetSize(VAR boxRect: Rect);` | Retrieves the 16-bit port bounding rectangle of SELF's Window Manager scroll box into boxRect. |
| `ScrollDir` | `FUNCTION ScrollDir: VHSelect;` | Returns the scroll orientation (v or h) of SELF's Window Manager scroll box. |
| `SetSize` | `PROCEDURE SetSize(ownerRect: Rect);` | Sets the bounding rectangle of SELF's Window Manager scroll box to align with ownerRect. |
| `ThumbRange` | `FUNCTION ThumbRange: INTEGER;` | Returns the pixel travel span available for moving the scroll thumb inside SELF's scroll box. |
| `TrackSkewer` | `PROCEDURE TrackSkewer(mousePt: Point; VAR newSkwrCd: INTEGER; VAR scroller, prevScroller: TScroller);` | Tracks user dragging of a split-bar skewer from mousePt, returning the new split coordinate newSkwrCd and neighboring scrollers. |
| `TrackThumb` | `PROCEDURE TrackThumb(mousePt: Point; VAR oldThumbPos, newThumbPos: INTEGER);` | Tracks user dragging of the scroll thumb from mousePt, returning the initial oldThumbPos and new 0..1000 position newThumbPos. |
| `FillIcon` | `PROCEDURE FillIcon(icon: TEnumIcons; fBlack: BOOLEAN);` | Highlights (fBlack = TRUE) or unhighlights (fBlack = FALSE) scroll-box control icon in the active GrafPort. |
| `MoveThumb` | `PROCEDURE MoveThumb(newThumbPos: INTEGER);` | Moves the visual thumb indicator in SELF's scroll box to proportional 0..1000 position newThumbPos and redraws it if visible. |
| `ResplitAt` | `PROCEDURE ResplitAt(newSkwrCd: INTEGER; prevScroller: TScroller);` | Moves the boundary between prevScroller and SELF to coordinate newSkwrCd, coalescing scrollers if either shrinks below minimum size. |
| `SplitAt` | `PROCEDURE SplitAt(newSkwrCd: INTEGER; VAR nextScroller: TScroller);` | Splits SELF's Window Manager scroll box at coordinate newSkwrCd and creates a new TScroller returned in nextScroller. |

#### `TScrollBar = SUBCLASS OF TObject`

Horizontal or vertical scroll-bar strip attached to a TPanel containing a chain of one or more split TScroller boxes.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; vhs: VHSelect; outerRect: Rect; itsVisibility: BOOLEAN): TScrollBar;` | Allocates and initializes a horizontal or vertical TScrollBar along outerRect with initial TScroller box and visibility itsVisibility. |
| `ChangeVisibility` | `PROCEDURE ChangeVisibility(needsBothBars: BOOLEAN; bandOuterRect: Rect; itsAbilities: TAbilities);` | Updates SELF.isVisible and adjusts scroll-box icons (thumb, arrows, split skewer, and grow-box space) for bandOuterRect and itsAbilities. |
| `DownAt` | `FUNCTION DownAt(mousePt: Point; VAR scroller: TScroller; VAR icon: TEnumIcons): BOOLEAN;` | Tests whether port coordinate mousePt hits any TScroller in SELF, returning TRUE along with the hit scroller and scroll-bar icon. |
| `Draw` | `PROCEDURE Draw;` | Paints all TScroller scroll boxes belonging to SELF if SELF.isVisible is TRUE (or paints an inactive frame when window is inactive). |
| `Erase` | `PROCEDURE Erase;` | Erases the entire scroll-bar strip covered by SELF's TScroller chain to white. |

#### `TMenuBar = SUBCLASS OF TObject`

Global menu-bar manager that loads menu definitions from the phrase file, maps TCmdNumber IDs to Window Manager menu/item indices, and handles command-key and menu-click dispatch.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsScanner: TFileScanner): TMenuBar;` | Reads menu and command definitions from phrase-file scanner itsScanner, allocates MenuInfo records, and builds the command-number mapping table. |
| `Check` | `PROCEDURE Check(cmdNumber: TCmdNumber; checked: BOOLEAN);` | Places or removes a checkmark next to the menu item corresponding to cmdNumber according to checked. |
| `Enable` | `PROCEDURE Enable(cmdNumber: TCmdNumber; canBeChosen: BOOLEAN);` | Enables (canBeChosen = TRUE) or dims (canBeChosen = FALSE) the menu item corresponding to cmdNumber. |
| `BuildCmdName` | `PROCEDURE BuildCmdName(destCmd, templateCmd: TCmdNumber; param: TPString);` | Constructs the menu item text for destCmd by substituting param (or the default buzzword if NIL) into the template string of templateCmd. |
| `GetCmdName` | `FUNCTION GetCmdName(cmdNumber: TCmdNumber; pName: TPString): BOOLEAN;` | Looks up cmdNumber in the menu table, optionally copies its item text into pName^ (if non-NIL), and returns TRUE if found. |
| `PutCmdName` | `PROCEDURE PutCmdName(cmdNumber: TCmdNumber; pName: TPString);` | Replaces the displayed menu item text for cmdNumber with the Pascal string pointed to by pName. |
| `CmdKey` | `FUNCTION CmdKey(ch: CHAR): TCmdNumber;` | Maps an Apple-key character ch to its matching loaded menu item's TCmdNumber (highlighting its menu title), or returns noCmdNumber. |
| `DownAt` | `FUNCTION DownAt(mousePt: Point): TCmdNumber;` | Tracks a mouse-down in the Window Manager menu bar starting at mousePt and returns the selected TCmdNumber (or noCmdNumber). |
| `Draw` | `PROCEDURE Draw;` | Draws the currently loaded menu titles in the Lisa Window Manager menu bar. |
| `EndCmd` | `PROCEDURE EndCmd;` | Unhighlights the active menu title in the menu bar after a menu or Apple-key command finishes executing. |
| `HighlightMenu` | `PROCEDURE HighlightMenu(withCmd: TCmdNumber);` | Highlights the menu-bar title of the menu containing command withCmd (used for keyboard equivalents such as Clear). |
| `Delete` | `PROCEDURE Delete(menuID: INTEGER);` | Removes the menu with ID menuID from the active Window Manager menu bar and marks it unloaded. |
| `Insert` | `PROCEDURE Insert(menuID, beforeId: INTEGER);` | Inserts the menu with ID menuID into the Window Manager menu bar before beforeId and marks it loaded. |
| `Unload` | `PROCEDURE Unload;` | Removes all currently loaded menus from the Window Manager menu bar. |
| `MenuWithID` | `FUNCTION MenuWithID(menuID: INTEGER): Ptr;` | Returns a pointer to the Window Manager MenuInfo record for menuID, or NIL if menuID is out of range. |

---

## Unit UDraw

Extends Lisa QuickDraw with 32-bit coordinate geometry (LPoint, LRect, LPattern), font/type-style mapping (TTypeStyle), and the core display-area and coordinate-projection classes (TArea, TPad, TBranchArea).

- **Import**: `USES UDraw;`
- **Unit kind**: `INTRINSIC` (`UDRAW`)
- **Interface dependencies**: `UnitStd`, `UnitHz`, `UObject`, `SysCall`, `PasLibCall`, `PPasLibC`, `QuickDraw`, `FontMgr`, `Events`, `Folders`, `FilerComm`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `InitQDWM` | `PROCEDURE InitQDWM;` | Initializes QuickDraw, the Lisa Window Manager, Filer communication, standard pens/patterns, and screen resolution globals for a Toolkit process. |
| `TrmntExceptionHandler` | `PROCEDURE TrmntExceptionHandler;` | Handles process termination exceptions by notifying the Desktop Manager (ImDying) and invoking crashPad.Crash if registered. |
| `InitErrorAbort` | `PROCEDURE InitErrorAbort(error: INTEGER);` | Aborts application startup and reports initFailed (or user abort) to the Desktop Manager Filer if error is positive or an abort event occurred. |
| `Reduce` | `PROCEDURE Reduce(VAR numerator, denominator: INTEGER);` | Divides numerator and denominator by their greatest common divisor to reduce a rational scale factor to lowest terms. |
| `FPtPlusPt` | `FUNCTION FPtPlusPt(operand1, operand2: Point): LONGINT;` | Adds two 16-bit QuickDraw Points component-wise and returns the resulting Point packed as a 32-bit LONGINT. |
| `FPtMinusPt` | `FUNCTION FPtMinusPt(operand1, operand2: Point): LONGINT;` | Subtracts operand2 from operand1 component-wise and returns the resulting 16-bit Point packed as a 32-bit LONGINT. |
| `FPtMulInt` | `FUNCTION FPtMulInt(operand1: Point; operand2: INTEGER): LONGINT;` | Multiplies both coordinates of 16-bit Point operand1 by scalar operand2 and returns the resulting Point packed as a 32-bit LONGINT. |
| `FPtDivInt` | `FUNCTION FPtDivInt(operand1: Point; operand2: INTEGER): LONGINT;` | Divides both coordinates of 16-bit Point operand1 by scalar operand2 and returns the resulting Point packed as a 32-bit LONGINT. |
| `FPtMaxPt` | `FUNCTION FPtMaxPt(operand1, operand2: Point): LONGINT;` | Computes the component-wise maximum of operand1 and operand2 and returns the resulting 16-bit Point packed as a 32-bit LONGINT. |
| `FPtMinPt` | `FUNCTION FPtMinPt(operand1, operand2: Point): LONGINT;` | Computes the component-wise minimum of operand1 and operand2 and returns the resulting 16-bit Point packed as a 32-bit LONGINT. |
| `FDiagRect` | `FUNCTION FDiagRect(operand1: Rect): LONGINT;` | Computes the diagonal extent (botRight minus topLeft) of 16-bit Rect operand1 and returns the resulting Point packed as a LONGINT. |
| `BoolToStr` | `PROCEDURE BoolToStr(bool: BOOLEAN; str: TPstring);` | Formats BOOLEAN value bool as 'TRUE' or 'FALSE' into the Pascal string pointed to by str. |
| `LIntDivLInt` | `FUNCTION LIntDivLInt(i, j: LONGINT): LONGINT;` | Divides 32-bit LONGINT i by 32-bit LONGINT j using signed 32-bit integer division. |
| `LIntDivInt` | `FUNCTION LIntDivInt(i: LONGINT; j: INTEGER): LONGINT;` | Divides 32-bit LONGINT i by 16-bit INTEGER j and returns the signed 32-bit quotient. |
| `LIntMulInt` | `FUNCTION LIntMulInt(i: LONGINT; j: INTEGER): LONGINT;` | Multiplies 32-bit LONGINT i by 16-bit INTEGER j and returns the signed 32-bit product. |
| `LIntOvrInt` | `FUNCTION LIntOvrInt(i: LONGINT; j: INTEGER): LONGINT;` | Divides 32-bit LONGINT i by 16-bit INTEGER j with symmetric half-divisor rounding toward the nearest integer. |
| `PtPlusPt` | `PROCEDURE PtPlusPt(operand1, operand2: Point; VAR result: Point);` | Adds 16-bit QuickDraw Points operand1 and operand2 component-wise and stores the sum in result. |
| `PtMinusPt` | `PROCEDURE PtMinusPt(operand1, operand2: Point; VAR result: Point);` | Subtracts 16-bit Point operand2 from operand1 component-wise and stores the difference in result. |
| `PtMulInt` | `PROCEDURE PtMulInt(operand1: Point; operand2: INTEGER; VAR result: Point);` | Multiplies both coordinates of 16-bit Point operand1 by scalar operand2 and stores the scaled point in result. |
| `PtDivInt` | `PROCEDURE PtDivInt(operand1: Point; operand2: INTEGER; VAR result: Point);` | Divides both coordinates of 16-bit Point operand1 by scalar operand2 and stores the quotient point in result. |
| `RectPlusRect` | `PROCEDURE RectPlusRect(operand1, operand2: Rect; VAR result: Rect);` | Adds the corresponding top, left, bottom, and right coordinates of 16-bit Rects operand1 and operand2 into result. |
| `RectMinusRect` | `PROCEDURE RectMinusRect(operand1, operand2: Rect; VAR result: Rect);` | Subtracts the corresponding top, left, bottom, and right coordinates of 16-bit Rect operand2 from operand1 into result. |
| `AlignRect` | `PROCEDURE AlignRect(VAR dstRect: Rect; srcRect: Rect; vhs: VHSelect);` | Copies the top/bottom (vhs = v) or left/right (vhs = h) edges from srcRect into dstRect. |
| `LengthRect` | `FUNCTION LengthRect(r: Rect; vhs: VHSelect): INTEGER;` | Returns the vertical height (vhs = v) or horizontal width (vhs = h) of 16-bit Rect r. |
| `RectHasPt` | `FUNCTION RectHasPt(dstRect: Rect; pt: Point): BOOLEAN;` | Returns TRUE if 16-bit Point pt lies within or on the inclusive boundaries (topLeft <= pt <= botRight) of dstRect. |
| `RectHavePt` | `PROCEDURE RectHavePt(dstRect: Rect; VAR pt: Point);` | Clamps 16-bit Point pt in place so both of its coordinates lie within the inclusive bounds of dstRect. |
| `RectsNest` | `FUNCTION RectsNest(outer, inner: Rect): BOOLEAN;` | Returns TRUE if 16-bit Rect inner lies completely inside or on the edges of outer. |
| `RectifyRect` | `PROCEDURE RectifyRect(VAR dstRect: Rect);` | Swaps top with bottom and/or left with right of dstRect as needed so that topLeft <= botRight. |
| `RectIsVisible` | `FUNCTION RectIsVisible(rectInPort: Rect): BOOLEAN;` | Returns TRUE if 16-bit port rectangle rectInPort intersects the current focusRgn visibility region. |
| `PointToStr` | `PROCEDURE PointToStr(pt: Point; str: TPstring);` | Formats 16-bit QuickDraw Point pt as a readable coordinate pair in the Pascal string pointed to by str. |
| `RectToStr` | `PROCEDURE RectToStr(r: Rect; str: TPstring);` | Formats 16-bit QuickDraw Rect r as a readable coordinate string in the Pascal string pointed to by str. |
| `LPtPlusLPt` | `PROCEDURE LPtPlusLPt(operand1, operand2: LPoint; VAR result: LPoint);` | Adds 32-bit LPoints operand1 and operand2 component-wise and stores the sum in result. |
| `LPtMinusLPt` | `PROCEDURE LPtMinusLPt(operand1, operand2: LPoint; VAR result: LPoint);` | Subtracts 32-bit LPoint operand2 from operand1 component-wise and stores the difference in result. |
| `LPtMulInt` | `PROCEDURE LPtMulInt(operand1: LPoint; operand2: INTEGER; VAR result: LPoint);` | Multiplies both 32-bit coordinates of LPoint operand1 by 16-bit scalar operand2 and stores the product in result. |
| `LPtDivInt` | `PROCEDURE LPtDivInt(operand1: LPoint; operand2: INTEGER; VAR result: LPoint);` | Divides both 32-bit coordinates of LPoint operand1 by 16-bit scalar operand2 and stores the quotient in result. |
| `EqualLPt` | `FUNCTION EqualLPt(operand1, operand2: LPoint): BOOLEAN;` | Returns TRUE if 32-bit LPoints operand1 and operand2 have identical horizontal and vertical coordinates. |
| `LRectPlusLRect` | `PROCEDURE LRectPlusLRect(operand1, operand2: LRect; VAR result: LRect);` | Adds the corresponding top, left, bottom, and right 32-bit coordinates of LRects operand1 and operand2 into result. |
| `LRectMinusLRect` | `PROCEDURE LRectMinusLRect(operand1, operand2: LRect; VAR result: LRect);` | Subtracts the corresponding top, left, bottom, and right 32-bit coordinates of LRect operand2 from operand1 into result. |
| `EqualLRect` | `FUNCTION EqualLRect(rectA, rectB: LRect): BOOLEAN;` | Returns TRUE if 32-bit LRects rectA and rectB have identical top, left, bottom, and right coordinates. |
| `EmptyLRect` | `FUNCTION EmptyLRect(r: LRect): BOOLEAN;` | Returns TRUE if 32-bit LRect r is empty (right <= left or bottom <= top). |
| `AlignLRect` | `PROCEDURE AlignLRect(VAR destLRect: LRect; srcLRect: LRect; vhs: VHSelect);` | Copies the top/bottom (vhs = v) or left/right (vhs = h) 32-bit edges from srcLRect into destLRect. |
| `LengthLRect` | `FUNCTION LengthLRect(r: LRect; vhs: VHSelect): LONGINT;` | Returns the 32-bit vertical height (vhs = v) or horizontal width (vhs = h) of LRect r. |
| `LRectHasLPt` | `FUNCTION LRectHasLPt(destLRect: LRect; pt: LPoint): BOOLEAN;` | Returns TRUE if 32-bit LPoint pt lies within or on the inclusive boundaries (topLeft <= pt <= botRight) of destLRect. |
| `LRectHaveLPt` | `PROCEDURE LRectHaveLPt(destLRect: LRect; VAR pt: LPoint);` | Clamps 32-bit LPoint pt in place so both of its coordinates lie within the inclusive bounds of destLRect. |
| `LRectsNest` | `FUNCTION LRectsNest(outer, inner: LRect): BOOLEAN;` | Returns TRUE if 32-bit LRect inner is completely contained within or on the boundaries of outer. |
| `RectifyLRect` | `PROCEDURE RectifyLRect(VAR destLRect: LRect);` | Swaps top with bottom and/or left with right of 32-bit destLRect as needed so that topLeft <= botRight. |
| `LRectIsVisible` | `FUNCTION LRectIsVisible(srcLRect: LRect): BOOLEAN;` | Returns TRUE if 32-bit view rectangle srcLRect intersects the currently focused TPad's visible visLRect. |
| `LPointToStr` | `PROCEDURE LPointToStr(pt: LPoint; str: TPstring);` | Formats 32-bit LPoint pt as a readable coordinate pair in the Pascal string pointed to by str. |
| `LRectToStr` | `PROCEDURE LRectToStr(r: LRect; str: TPstring);` | Formats 32-bit LRect r as a readable coordinate string in the Pascal string pointed to by str. |
| `SetLPt` | `PROCEDURE SetLPt(VAR destPt: LPoint; itsH, itsV: LONGINT);` | Assigns 32-bit horizontal coordinate itsH and vertical coordinate itsV to destPt. |
| `SetLRect` | `PROCEDURE SetLRect(VAR dstRect: LRect; itsLeft, itsTop, itsRight, itsBottom: LONGINT);` | Assigns 32-bit boundary coordinates itsLeft, itsTop, itsRight, and itsBottom to dstRect. |
| `OffsetLRect` | `PROCEDURE OffsetLRect(VAR dstRect: LRect; dh, dv: LONGINT);` | Translates 32-bit LRect dstRect horizontally by dh and vertically by dv. |
| `InsetLRect` | `PROCEDURE InsetLRect(VAR dstRect: LRect; dh, dv: LONGINT);` | Shrinks (positive) or expands (negative) 32-bit LRect dstRect inward by dh horizontally and dv vertically. |
| `SectLRect` | `FUNCTION SectLRect(srcRectA, srcRectB: LRect; VAR dstRect: LRect): BOOLEAN;` | Computes the intersection of 32-bit LRects srcRectA and srcRectB into dstRect and returns TRUE if the intersection is non-empty. |
| `UnionLRect` | `PROCEDURE UnionLRect(srcRectA, srcRectB: LRect; VAR dstRect: LRect);` | Computes the smallest 32-bit LRect bounding both srcRectA and srcRectB and stores it in dstRect. |
| `LPtInLRect` | `FUNCTION LPtInLRect(pt: LPoint; r: LRect): BOOLEAN;` | Returns TRUE if the pixel below and to the right of 32-bit LPoint pt lies inside LRect r (top <= v < bottom and left <= h < right). |
| `IsSmallPt` | `FUNCTION IsSmallPt(srcPt: LPoint): BOOLEAN;` | Returns TRUE if both coordinates of 32-bit LPoint srcPt fit within the 16-bit QuickDraw Point range. |
| `IsSmallRect` | `FUNCTION IsSmallRect(srcRect: LRect): BOOLEAN;` | Returns TRUE if both corner points of 32-bit LRect srcRect fit within the 16-bit QuickDraw Rect range. |
| `DrawLText` | `PROCEDURE DrawLText(textBuf: Ptr; startByte, numBytes: INTEGER);` | Draws numBytes of text starting at startByte in textBuf on the currently focused TPad at the current pen location. |
| `MoveToL` | `PROCEDURE MoveToL(h, v: LONGINT);` | Moves the QuickDraw pen on the currently focused TPad to 32-bit view coordinates (h, v) without drawing. |
| `MoveL` | `PROCEDURE MoveL(dh, dv: LONGINT);` | Offsets the QuickDraw pen on the currently focused TPad by 32-bit view deltas (dh, dv) without drawing. |
| `LineToL` | `PROCEDURE LineToL(h, v: LONGINT);` | Draws a line on the currently focused TPad from the current pen position to 32-bit view coordinates (h, v). |
| `LineL` | `PROCEDURE LineL(dh, dv: LONGINT);` | Draws a line on the currently focused TPad from the current pen position by 32-bit relative view deltas (dh, dv). |
| `FrameLRect` | `PROCEDURE FrameLRect(r: LRect);` | Draws a hollow outline inside 32-bit view rectangle r on the currently focused TPad using the current pen. |
| `PaintLRect` | `PROCEDURE PaintLRect(r: LRect);` | Paints the interior of 32-bit view rectangle r on the currently focused TPad with the current pen pattern and mode. |
| `EraseLRect` | `PROCEDURE EraseLRect(r: LRect);` | Erases the interior of 32-bit view rectangle r on the currently focused TPad with the port's background pattern. |
| `InvrtLRect` | `PROCEDURE InvrtLRect(r: LRect);` | Inverts all pixels inside 32-bit view rectangle r on the currently focused TPad. |
| `FillLRect` | `PROCEDURE FillLRect(r: LRect; lPat: LPattern);` | Fills the interior of 32-bit view rectangle r on the currently focused TPad with 32-bit view-aligned pattern lPat. |
| `FrameLOval` | `PROCEDURE FrameLOval(r: LRect);` | Draws a hollow oval outline inscribed in 32-bit view rectangle r on the currently focused TPad. |
| `PaintLOval` | `PROCEDURE PaintLOval(r: LRect);` | Paints the interior of an oval inscribed in 32-bit view rectangle r on the currently focused TPad. |
| `EraseLOval` | `PROCEDURE EraseLOval(r: LRect);` | Erases the interior of an oval inscribed in 32-bit view rectangle r on the currently focused TPad. |
| `InvrtLOval` | `PROCEDURE InvrtLOval(r: LRect);` | Inverts all pixels inside an oval inscribed in 32-bit view rectangle r on the currently focused TPad. |
| `FillLOval` | `PROCEDURE FillLOval(r: LRect; lPat: LPattern);` | Fills an oval inscribed in 32-bit view rectangle r on the currently focused TPad with view-aligned pattern lPat. |
| `FrameLRRect` | `PROCEDURE FrameLRRect(r: LRect; ovalWidth, ovalHeight: INTEGER);` | Draws a hollow rounded-corner rectangle inside 32-bit view rectangle r with corner diameters (ovalWidth, ovalHeight) on the focused TPad. |
| `PaintLRRect` | `PROCEDURE PaintLRRect(r: LRect; ovalWidth, ovalHeight: INTEGER);` | Paints a rounded-corner rectangle inside 32-bit view rectangle r with corner diameters (ovalWidth, ovalHeight) on the focused TPad. |
| `EraseLRRect` | `PROCEDURE EraseLRRect(r: LRect; ovalWidth, ovalHeight: INTEGER);` | Erases a rounded-corner rectangle inside 32-bit view rectangle r with corner diameters (ovalWidth, ovalHeight) on the focused TPad. |
| `InvrtLRRect` | `PROCEDURE InvrtLRRect(r: LRect; ovalWidth, ovalHeight: INTEGER);` | Inverts pixels inside a rounded-corner rectangle in 32-bit view rectangle r with corner diameters (ovalWidth, ovalHeight) on the focused TPad. |
| `FillLRRect` | `PROCEDURE FillLRRect(r: LRect; ovalWidth, ovalHeight: INTEGER; lPat: LPattern);` | Fills a rounded-corner rectangle in 32-bit view rectangle r with corner diameters (ovalWidth, ovalHeight) using pattern lPat on the focused TPad. |
| `FrameLArc` | `PROCEDURE FrameLArc(r: LRect; startAngle, arcAngle: INTEGER);` | Draws an elliptical arc outline inscribed in 32-bit view rectangle r from startAngle spanning arcAngle degrees on the focused TPad. |
| `PaintLArc` | `PROCEDURE PaintLArc(r: LRect; startAngle, arcAngle: INTEGER);` | Paints a wedge-shaped elliptical sector inscribed in 32-bit view rectangle r from startAngle spanning arcAngle degrees on the focused TPad. |
| `EraseLArc` | `PROCEDURE EraseLArc(r: LRect; startAngle, arcAngle: INTEGER);` | Erases a wedge-shaped elliptical sector inscribed in 32-bit view rectangle r from startAngle spanning arcAngle degrees on the focused TPad. |
| `InvrtLArc` | `PROCEDURE InvrtLArc(r: LRect; startAngle, arcAngle: INTEGER);` | Inverts pixels in a wedge-shaped elliptical sector inscribed in 32-bit view rectangle r from startAngle spanning arcAngle degrees on the focused TPad. |
| `FillLArc` | `PROCEDURE FillLArc(r: LRect; startAngle, arcAngle: INTEGER; lPat: LPattern);` | Fills a wedge-shaped elliptical sector in 32-bit view rectangle r from startAngle spanning arcAngle degrees with pattern lPat on the focused TPad. |
| `ClonePicture` | `FUNCTION ClonePicture(pic: PicHandle; toHeap: THeap): PicHandle;` | Allocates and returns a copy of QuickDraw picture handle pic in target heap toHeap. |
| `ResizeFeedback` | `PROCEDURE ResizeFeedback(mousePt: Point; minPt, maxPt: Point; outerRect: Rect; tabHeight, sbWidth, sbHeight: INTEGER; VAR newPt: Point);` | Tracks mouse dragging with XOR rubber-band frame feedback (including optional title tab and scroll-bar outlines) constrained between minPt and maxPt, returning the final corner in newPt. |
| `PushFocus` | `PROCEDURE PushFocus;` | Pushes the currently focused TArea (focusArea) onto focusStack so focus can be temporarily switched to another area. |
| `PopFocus` | `PROCEDURE PopFocus;` | Pops the previously saved TArea from focusStack and restores GrafPort focus to it (if non-NIL). |
| `MakeTypeStyle` | `PROCEDURE MakeTypeStyle(itsFamily: INTEGER; itsSize: INTEGER; itsFaces: Style; VAR typeStyle: TTypeStyle);` | Constructs a TTypeStyle record from Toolkit font family itsFamily, size index itsSize, and QuickDraw character style set itsFaces. |
| `QDFontNumber` | `FUNCTION QDFontNumber(typeStyle: TTypeStyle): INTEGER;` | Maps a Toolkit TTypeStyle (family and size indices) to the corresponding Lisa QuickDraw font ID number. |
| `SetQDTypeStyle` | `PROCEDURE SetQDTypeStyle(typeStyle: TTypeStyle);` | Sets the current QuickDraw GrafPort's text font (TextFont) and character style faces (TextFace) according to typeStyle. |

### Clascal Classes

#### `TArea = SUBCLASS OF TObject`

Abstract rectangular display region in 16-bit GrafPort coordinates with inner and outer bounds, border insets, focus management, framing, hit-testing, and resizing.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsRect: Rect): TArea; ABSTRACT;` | Abstract constructor that initializes a TArea in heap with initial bounding rectangle itsRect. |
| `ChildWithPt` | `FUNCTION ChildWithPt(pt: Point; childList: TList; VAR nearestPt: Point): TArea;` | Finds and returns the child TArea in childList whose outerRect contains clamped point pt, returning the point clamped to that child's innerRect in nearestPt. |
| `GetBorder` | `PROCEDURE GetBorder(VAR border: Rect); DEFAULT;` | Returns the border thickness insets (outerRect minus innerRect; default (-1, -1, 1, 1) for a 1-pixel frame) in border. |
| `GetMinExtent` | `PROCEDURE GetMinExtent(VAR minExtent: Point; windowIsResizingIt: BOOLEAN); ABSTRACT;` | Abstract method returning the minimum allowable outer width and height of the area in minExtent during user or window resizing. |
| `SetOuterRect` | `PROCEDURE SetOuterRect(newOuterRect: Rect);` | Sets outerRect to newOuterRect and recomputes innerRect by subtracting the area's GetBorder deltas. |
| `SetInnerRect` | `PROCEDURE SetInnerRect(newInnerRect: Rect);` | Sets innerRect to newInnerRect and recomputes outerRect by adding the area's GetBorder deltas. |
| `Erase` | `PROCEDURE Erase;` | Erases SELF.innerRect to white in the currently focused GrafPort. |
| `Focus` | `PROCEDURE Focus; ABSTRACT;` | Abstract method that configures the active QuickDraw GrafPort, origin, and clipping region for drawing into SELF. |
| `Frame` | `PROCEDURE Frame; DEFAULT;` | Draws the border outline, dividers, or scroll bars around SELF outside its innerRect. |
| `Refresh` | `PROCEDURE Refresh(rActions: TActions; highTransit: THighTransit); ABSTRACT;` | Abstract method that performs the requested display actions (rErase, rFrame, rBackground, rDraw) and highlight transition highTransit on SELF. |
| `DownAt` | `FUNCTION DownAt(mousePt: Point): BOOLEAN; ABSTRACT;` | Abstract hit-handling method invoked when a mouse-down occurs at port coordinate mousePt; returns TRUE if handled by SELF. |
| `ResizeInside` | `PROCEDURE ResizeInside(newInnerRect: Rect); ABSTRACT;` | Abstract method that resizes SELF and any child areas so its interior bounds match newInnerRect. |
| `ResizeOutside` | `PROCEDURE ResizeOutside(newOuterRect: Rect); ABSTRACT;` | Abstract method that resizes SELF and any child areas so its exterior bounds match newOuterRect. |

#### `TPad = SUBCLASS OF TArea`

Coordinate-mapping TArea that projects a 32-bit LRect view space onto a 16-bit QuickDraw GrafPort with scrolling, resolution scaling, zooming, clipping, and 32-bit drawing primitives.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsInnerRect: Rect; itsViewedLRect: LRect; itsPadRes, itsViewRes: Point; itsPort: GrafPtr): TPad;` | Allocates and initializes a TPad in heap that maps 32-bit view region itsViewedLRect (at itsViewRes) onto 16-bit port rectangle itsInnerRect (at itsPadRes) in itsPort. |
| `Redefine` | `PROCEDURE Redefine(itsInnerRect: Rect; itsViewedLRect: LRect; itsPadRes, itsViewRes: Point; itsZoomFactor: TScaler; itsPort: GrafPtr);` | Reconfigures SELF's innerRect, viewedLRect, pad/view resolutions, zoomFactor, GrafPort, net scaleFactor, and coordinate offsets. |
| `DistToLDist` | `PROCEDURE DistToLDist(distInPort: Point; VAR lDistInView: LPoint);` | Scales a 16-bit GrafPort delta vector distInPort into a 32-bit view-space distance vector lDistInView. |
| `PatToLPat` | `PROCEDURE PatToLPat(patInPort: Pattern; VAR lPatInView: LPattern);` | Converts an 8x8 QuickDraw port Pattern patInPort into a view-origin-aligned 32-bit LPattern lPatInView. |
| `PtToLPt` | `PROCEDURE PtToLPt(ptInPort: Point; VAR lPtInView: LPoint);` | Transforms a 16-bit GrafPort coordinate ptInPort into the corresponding 32-bit view coordinate lPtInView. |
| `RectToLRect` | `PROCEDURE RectToLRect(rectInPort: Rect; VAR lRectInView: LRect);` | Transforms a 16-bit GrafPort rectangle rectInPort into the corresponding 32-bit view rectangle lRectInView. |
| `LDistToDist` | `PROCEDURE LDistToDist(lDistInView: LPoint; VAR distInPort: Point);` | Scales a 32-bit view-space distance vector lDistInView into a 16-bit GrafPort delta vector distInPort. |
| `LPatToPat` | `PROCEDURE LPatToPat(lPatInView: LPattern; VAR patInPort: Pattern);` | Shifts 32-bit view pattern lPatInView by the pad's scroll offset so it aligns seamlessly in 16-bit port Pattern patInPort. |
| `LPtToPt` | `PROCEDURE LPtToPt(lPtInView: LPoint; VAR ptInPort: Point);` | Projects a 32-bit view coordinate lPtInView into 16-bit GrafPort coordinate ptInPort (clamped to availLRect). |
| `LRectToRect` | `PROCEDURE LRectToRect(lRectInView: LRect; VAR rectInPort: Rect);` | Projects a 32-bit view rectangle lRectInView into 16-bit GrafPort rectangle rectInPort (clamped to availLRect). |
| `OffsetBy` | `PROCEDURE OffsetBy(deltaLPt: LPoint);` | Translates SELF.viewedLRect and scroll offsets by 32-bit deltaLPt without redrawing the screen. |
| `SetScrollOffset` | `PROCEDURE SetScrollOffset(VAR newOffset: LPoint);` | Updates scrollOffset to newOffset and recalculates the 16-bit GrafPort origin, 32-bit cdOffset, and availLRect. |
| `ClipFurtherTo` | `PROCEDURE ClipFurtherTo(rBand: rect);` | Intersects SELF.clippedRect with port rectangle rBand to further restrict the clipping region on the next Focus. |
| `Focus` | `PROCEDURE Focus; OVERRIDE;` | Sets QuickDraw's current GrafPort to SELF.port, configures SELF.origin, intersects clippedRect with visRgn into padRgn, and computes visLRect. |
| `InvalLRect` | `PROCEDURE InvalLRect(r: LRect);` | Projects 32-bit view rectangle r into port coordinates and adds its intersection with clippedRect to the window's update region. |
| `InvalRect` | `PROCEDURE InvalRect(r: Rect);` | Adds the intersection of 16-bit port rectangle r and SELF.clippedRect to the window's QuickDraw update region. |
| `SetPen` | `PROCEDURE SetPen(pen: PenState);` | Sets the current GrafPort's QuickDraw pen state to pen. |
| `SetPenToHighlight` | `PROCEDURE SetPenToHighlight(highTransit: THighTransit);` | Configures the QuickDraw pen state from highPen[highTransit] to render XOR or dim selection highlighting. |
| `SetZoomFactor` | `PROCEDURE SetZoomFactor(zoomNumerator, zoomDenominator: point); DEFAULT;` | Sets SELF.zoomFactor to zoomNumerator / zoomDenominator (reduced to lowest terms) and recomputes pad scaling and viewedLRect. |
| `DrawLText` | `PROCEDURE DrawLText(textBuf: Ptr; startByte, numBytes: INTEGER);` | Draws numBytes of text from textBuf+startByte at the current pen location on SELF, scaling font size if the pad is zoomed. |
| `DrawLLine` | `PROCEDURE DrawLLine(newLPt: LPoint);` | Draws a line in SELF's GrafPort from the current pen location to projected 32-bit view point newLPt. |
| `DrawLPicture` | `PROCEDURE DrawLPicture(pic: PicHandle; r: LRect);` | Projects 32-bit destination rectangle r into port coordinates and draws QuickDraw picture pic within it. |
| `DrawLRect` | `PROCEDURE DrawLRect(verb: GrafVerb; r: LRect);` | Executes QuickDraw GrafVerb verb (frame, paint, erase, invert, or fill) on projected 32-bit rectangle r. |
| `DrawLRRect` | `PROCEDURE DrawLRRect(verb: GrafVerb; r: LRect; ovalWidth, ovalHeight: INTEGER);` | Executes QuickDraw GrafVerb verb on projected 32-bit rounded rectangle r with scaled corner diameters (ovalWidth, ovalHeight). |
| `DrawLOval` | `PROCEDURE DrawLOval(verb: GrafVerb; r: LRect);` | Executes QuickDraw GrafVerb verb on an oval inscribed in projected 32-bit rectangle r. |
| `DrawLArc` | `PROCEDURE DrawLArc(verb: GrafVerb; r: LRect; startAngle, arcAngle: INTEGER);` | Executes QuickDraw GrafVerb verb on an elliptical arc in projected 32-bit rectangle r from startAngle through arcAngle. |
| `DrawLBits` | `PROCEDURE DrawLBits(VAR srcBits: BitMap; VAR srcRect: Rect; VAR dstLRect: LRect; mode: INTEGER; maskRgn: RgnHandle);` | Projects dstLRect to port coordinates and transfers bitmap srcBits (from srcRect) using QuickDraw CopyBits with mode and maskRgn. |
| `Crash` | `PROCEDURE Crash; ABSTRACT;` | Abstract emergency termination callback invoked on crashPad by TrmntExceptionHandler when the process aborts. |
| `BindHeap` | `FUNCTION BindHeap(activeVsClip, doBind: BOOLEAN): THeap; ABSTRACT;` | Abstract debugging hook invoked on crashPad to bind or query the active document or Clipboard heap. |

#### `TBranchArea = SUBCLASS OF TArea`

Binary split-tree TArea node that arranges an elderChild and youngerChild area horizontally or vertically and manages proportional or user-driven resizing.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; vhs: VHSelect; hasElderFirst: BOOLEAN; whoCanResizeIt: TResizability; itsElderChild, itsYoungerChild: TArea): TBranchArea;` | Allocates and initializes a binary TBranchArea splitting itsElderChild and itsYoungerChild along axis vhs with resizability flags whoCanResizeIt. |
| `GetMinExtent` | `PROCEDURE GetMinExtent(VAR minExtent: Point; windowIsResizingIt: BOOLEAN); OVERRIDE;` | Computes the combined minimum outer dimensions required by elderChild and youngerChild along and across arrangement. |
| `OtherChild` | `FUNCTION OtherChild(child: TArea): TArea;` | Returns youngerChild if child is elderChild, or elderChild if child is youngerChild. |
| `ReplaceChild` | `PROCEDURE ReplaceChild(child, newChild: TArea);` | Replaces child (either elderChild or youngerChild) with newChild and updates newChild.parentBranch to SELF. |
| `TopLeftChild` | `FUNCTION TopLeftChild: TArea;` | Returns whichever of elderChild or youngerChild is positioned at the top or left (elderChild when elderFirst is TRUE). |
| `ResizeOutside` | `PROCEDURE ResizeOutside(newOuterRect: Rect); OVERRIDE;` | Resizes SELF's outer bounds to newOuterRect and adjusts elderChild and youngerChild proportionally or per their resizability rules. |
| `Redivide` | `PROCEDURE Redivide(newCd: INTEGER);` | Moves the internal split boundary between elderChild and youngerChild to coordinate newCd and resizes both children. |

---

## Unit UObject

Provides the foundational Clascal root class (TObject), relocatable heap and Lisa OS data-segment management, class metadata and version conversion, dynamic indexed collections (TCollection, TList, TArray, TString, TFile), and sequential scanners/streams (TScanner subclasses).

- **Import**: `USES UObject;`
- **Unit kind**: `INTRINSIC` (`UOBJECT`)
- **Interface dependencies**: `UnitStd`, `UnitHz`, `SysCall`, `PSysCall`, `UClascal`, `PMDecl`, `PMM`, `PasLibCall`, `PPasLibC`, `HWInt`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `Min` | `FUNCTION Min(i, j: LONGINT): LONGINT;` | Returns the smaller of two 32-bit LONGINT values. |
| `Max` | `FUNCTION Max(i, j: LONGINT): LONGINT;` | Returns the larger of two 32-bit LONGINT values. |
| `XferLeft` | `PROCEDURE XferLeft(source, dest: Ptr; nBytes: INTEGER);` | Copies nBytes of memory from source to dest moving upward from lowest to highest address for overlapping left shifts. |
| `XferRight` | `PROCEDURE XferRight(source, dest: Ptr; nBytes: INTEGER);` | Copies nBytes of memory from source to dest moving downward from highest to lowest address for overlapping right shifts. |
| `EqualBytes` | `FUNCTION EqualBytes(source, dest: Ptr; nBytes: INTEGER): BOOLEAN;` | Compares nBytes starting at source and dest and returns TRUE if the two memory blocks are byte-for-byte identical. |
| `LIntAndLInt` | `FUNCTION LIntAndLInt(i, j: LONGINT): LONGINT;` | Computes and returns the bitwise logical AND of two 32-bit LONGINT values. |
| `LIntOrLInt` | `FUNCTION LIntOrLInt(i, j: LONGINT): LONGINT;` | Computes and returns the bitwise logical OR of two 32-bit LONGINT values. |
| `LIntXorLInt` | `FUNCTION LIntXorLInt(i, j: LONGINT): LONGINT;` | Computes and returns the bitwise exclusive OR (XOR) of two 32-bit LONGINT values. |
| `NewObject` | `FUNCTION NewObject(heap: THeap; itsClass: TClass): TObject;` | Allocates a new relocatable Clascal object of class itsClass in heap and initializes its class slice-table pointer. |
| `NewDynObject` | `FUNCTION NewDynObject(heap: THeap; itsClass: TClass; dynBytes: INTEGER): TObject;` | Allocates a new Clascal object of class itsClass in heap with dynBytes additional dynamic bytes beyond its fixed class fields. |
| `ResizeDynObject` | `PROCEDURE ResizeDynObject(object: TObject; newTotalBytes: INTEGER);` | Resizes the relocatable heap block backing dynamic Clascal object so its total byte size becomes newTotalBytes. |
| `NewOrRecycledObject` | `FUNCTION NewOrRecycledObject(heap: THeap; itsClass: TClass; VAR chainHead: TObject): TObject;` | Pops and reinitializes a recycled object from the free list at chainHead if non-NIL, or allocates a new itsClass instance in heap. |
| `RecycleObject` | `PROCEDURE RecycleObject(object: TObject; VAR chainHead: TObject);` | Pushes object onto the singly linked recycle chain headed by chainHead for reuse instead of freeing its heap block. |
| `Free` | `PROCEDURE Free(object: TObject);` | Frees object and its known dependents by calling object.Free if object is non-NIL, or does nothing when object is NIL. |
| `Superclass` | `FUNCTION Superclass(class: TClass): TClass;` | Returns the TClass descriptor for the immediate superclass of class, or NIL if class is TObject. |
| `ClassDescendsFrom` | `FUNCTION ClassDescendsFrom(descendant, ancestor: TClass): BOOLEAN;` | Returns TRUE if descendant is equal to ancestor or inherits from ancestor in the Clascal class hierarchy. |
| `NameOfClass` | `PROCEDURE NameOfClass(class: TClass; VAR className: TClassName);` | Copies the registered 8-character Clascal class name of class into className. |
| `SizeOfClass` | `FUNCTION SizeOfClass(class: TClass): INTEGER;` | Returns the fixed instance byte size (including the class pointer) declared for instances of class. |
| `UnitAuthor` | `PROCEDURE UnitAuthor(companyAndAuthor: TAuthorName);` | Registers the company and author string for the current Clascal unit in myWorld during unit class initialization. |
| `ClassAuthor` | `PROCEDURE ClassAuthor(companyAndAuthor: TAuthorName; classAlias: TClassName);` | Registers an optional author string and persistent 8-character class alias for the current Clascal class during class initialization. |
| `ClassVersion` | `PROCEDURE ClassVersion(itsVersion, oldestItCanRead: Byte);` | Registers the current version byte and oldest readable version byte for the current Clascal class during class initialization. |
| `ValidObject` | `FUNCTION ValidObject(hndl: Handle): BOOLEAN;` | Returns TRUE if hndl is a valid relocatable heap handle referencing a well-formed Clascal object. |
| `ABCBreak` | `PROCEDURE ABCBreak(s: S255; errCode: LONGINT);` | Reports diagnostic message s and status code errCode and halts or enters the Toolkit debugger upon an assertion failure. |
| `ClascalError` | `PROCEDURE ClascalError(error: INTEGER);` | Signals a Clascal runtime error with code error (such as calling an ABSTRACT method or failing a heap allocation). |
| `LIntToHex` | `PROCEDURE LIntToHex(decNumber: LONGINT; hexNumber: TPString);` | Formats 32-bit decNumber as an 8-character uppercase hexadecimal string into the Pascal string pointed to by hexNumber. |
| `LIntToStr` | `PROCEDURE LIntToStr(decNumber: LONGINT; str: TPString);` | Converts signed 32-bit decNumber into its decimal ASCII string representation in the Pascal string pointed to by str. |
| `IntToStr` | `PROCEDURE IntToStr(decNumber: INTEGER; str: TPString);` | Converts signed 16-bit decNumber into its decimal ASCII string representation in the Pascal string pointed to by str. |
| `HexStrToLInt` | `PROCEDURE HexStrToLInt(hexString: TPString; VAR decNumber: LONGINT; VAR result: TConvResult);` | Parses hexadecimal digits from hexString into 32-bit decNumber and sets result to report validity, syntax error, or overflow. |
| `StrToLInt` | `PROCEDURE StrToLInt(str: TPString; VAR decNumber: LONGINT; VAR result: TConvResult);` | Parses a signed decimal integer from str into 32-bit decNumber and sets result to cvValid, cvNoNumber, cvBadNumber, or cvOverflow. |
| `StrToInt` | `PROCEDURE StrToInt(str: TPString; VAR decNumber: INTEGER; VAR result: TConvResult);` | Parses a signed decimal integer from str into 16-bit decNumber and sets result to cvValid, cvNoNumber, cvBadNumber, or cvOverflow. |
| `TrimBlanks` | `PROCEDURE TrimBlanks(str: TPString);` | Strips leading and trailing space characters in place from the Pascal string pointed to by str. |
| `CharUpperCased` | `FUNCTION CharUpperCased(ch: CHAR): CHAR;` | Converts character ch to uppercase (including Lisa accented characters) and returns the uppercase character. |
| `StrUpperCased` | `PROCEDURE StrUpperCased(str: TPString);` | Converts every character in the Pascal string pointed to by str to uppercase in place. |
| `SplitFilePath` | `PROCEDURE SplitFilePath(VAR fullPath, itsCatalog, itsFilePart: TFilePath);` | Splits Lisa OS pathname fullPath into its volume/catalog prefix itsCatalog and leaf entry name itsFilePart. |
| `LatestError` | `PROCEDURE LatestError(newError: INTEGER; VAR previousError: INTEGER);` | Updates previousError with newError while preserving the first positive fatal error code (or first negative warning code if no error occurred). |
| `NewHeap` | `FUNCTION NewHeap(VAR error: INTEGER; heapStart, numBytes: LONGINT; numObjects: INTEGER): THeap;` | Creates and initializes a UnitHz relocatable object heap of numBytes bytes at heapStart with numObjects initial master pointers. |
| `MakeDataSegment` | `FUNCTION MakeDataSegment(VAR error, dsRefnum: INTEGER; firstTryVolume, thenTryVolume: TFilePath; ldsn, memBytes, diskBytes: INTEGER): LONGINT;` | Creates and binds a Lisa OS data segment at logical segment ldsn on firstTryVolume (or fallback thenTryVolume) with memBytes RAM and diskBytes disk size, returning its base address. |
| `SetHeap` | `PROCEDURE SetHeap(heap: THeap);` | Sets heap as the active default THeap zone for subsequent heap operations. |
| `GetHeap` | `PROCEDURE GetHeap(VAR heap: THeap);` | Returns the currently active default THeap zone in heap. |
| `NeedConversion` | `FUNCTION NeedConversion(exClassWorld: TClassWorld; VAR olderVersion, newerVersion: BOOLEAN): BOOLEAN;` | Compares saved class table exClassWorld against the running process's myWorld to test whether heap objects need version conversion and sets olderVersion and newerVersion. |
| `ConvertHeap` | `PROCEDURE ConvertHeap(heap: THeap; exClassWorld: TClassWorld);` | Converts all Clascal objects in heap from the saved exClassWorld class layouts and versions to the current myWorld definitions. |
| `MarkHeap` | `PROCEDURE MarkHeap(heap: THeap; mpAddress: LONGINT);` | Marks all reachable Clascal objects in heap via non-recursive depth-first traversal starting from the root master pointer at mpAddress. |
| `SweepHeap` | `PROCEDURE SweepHeap(heap: THeap; report: BOOLEAN);` | Sweeps all objects in heap after MarkHeap, clearing mark bits on live objects and either printing unmarked garbage classes (report = TRUE) or freeing unmarked objects (report = FALSE). |

### Clascal Classes

#### `TObject = SUBCLASS OF NIL`

Root Clascal class for all heap-allocated Lisa Toolkit objects, providing allocation, shallow and deep cloning, deallocation, stream serialization, and class-version conversion.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap): TObject; ABSTRACT;` | Abstract constructor signature for initializing a newly allocated or subclass-supplied TObject in heap. |
| `Become` | `PROCEDURE Become(object: TObject);` | Swaps the master pointers of SELF and object so all existing handles to SELF now reference object, then frees the former SELF. |
| `Class` | `FUNCTION Class: TClass;` | Returns the TClass slice-table pointer identifying the runtime Clascal class of SELF. |
| `CloneObject` | `FUNCTION CloneObject(heap: THeap): TObject;` | Allocates and returns a shallow byte-for-byte duplicate of SELF in heap without cloning dependent objects. |
| `Clone` | `FUNCTION Clone(heap: THeap): TObject; DEFAULT;` | Clones SELF into heap along with any owned dependent objects (defaulting to CloneObject unless overridden). |
| `FreeObject` | `PROCEDURE FreeObject; DEFAULT;` | Releases the heap storage occupied by SELF itself without freeing any dependent objects it references. |
| `Free` | `PROCEDURE Free; DEFAULT;` | Frees SELF and its owned dependent objects (defaulting to FreeObject unless overridden by subclasses). |
| `Heap` | `FUNCTION Heap: THeap;` | Returns the THeap zone in which SELF is allocated. |
| `HeapBytes` | `FUNCTION HeapBytes: INTEGER;` | Returns the total number of bytes currently occupied by SELF's heap block. |
| `Read` | `PROCEDURE Read(s: TStringScanner);` | Deserializes SELF's fields and owned dependent objects from stream scanner s. |
| `Write` | `PROCEDURE Write(s: TStringScanner);` | Serializes SELF's class identity, fields, and owned dependent objects to stream scanner s. |
| `Convert` | `PROCEDURE Convert(fromVersion: Byte);` | Hook invoked during heap version conversion to finish upgrading SELF's state from saved class version fromVersion. |
| `JoinClass` | `FUNCTION JoinClass(newClass: TClass): TObject;` | Rebinds SELF's class pointer (and resizes its heap block if needed) to migrate SELF into newClass during version conversion. |

#### `TCollection = SUBCLASS OF TObject`

Abstract base class for variable-size indexed collections that store contiguous dynamic member elements with an internal edit-slack hole.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; initialSlack: INTEGER): TCollection;` | Initializes a TCollection (allocating one if object is NIL) in heap with initialSlack member slots in its edit hole. |
| `Clone` | `FUNCTION Clone(heap: THeap): TObject; OVERRIDE;` | Creates a copy of the collection in heap with its edit hole compacted out. |
| `MemberBytes` | `FUNCTION MemberBytes: INTEGER; ABSTRACT;` | Abstract function returning the size in bytes of each individual element stored in the collection. |
| `Equals` | `FUNCTION Equals(otherCollection: TCollection): BOOLEAN;` | Returns TRUE if SELF and otherCollection have the same MemberBytes, element count, and byte-identical member contents. |
| `StartEdit` | `PROCEDURE StartEdit(withSlack: INTEGER);` | Sets holeStd to withSlack so subsequent insertions and deletions retain an internal slack hole to avoid repeated heap reallocations. |
| `StopEdit` | `PROCEDURE StopEdit;` | Compacts out any unused edit hole in the collection's heap block and resets holeStd to zero to conserve memory. |
| `InsManyAt` | `PROCEDURE InsManyAt(i: LONGINT; otherCollection: TCollection; index, howMany: LONGINT);` | Inserts howMany contiguous members from otherCollection (starting at index) into SELF before element position i. |
| `InsNullsAt` | `PROCEDURE InsNullsAt(i, howMany: LONGINT);` | Inserts howMany zero-filled member slots into SELF before element position i. |
| `AddrMember` | `FUNCTION AddrMember(i: LONGINT): LONGINT;` | Computes the transient physical memory address of member i (accounting for dynStart and any preceding edit hole). |
| `CopyMembers` | `PROCEDURE CopyMembers(dstAddr, startIndex, howMany: LONGINT);` | Copies howMany members starting at 1-based startIndex out of SELF (bridging any internal hole) to memory address dstAddr. |
| `EditAt` | `PROCEDURE EditAt(atIndex: LONGINT; deltaMembers: INTEGER);` | Repositions and resizes the internal edit hole at atIndex to accommodate adding or removing deltaMembers elements. |
| `ResizeColl` | `PROCEDURE ResizeColl(membersPlusHole: INTEGER);` | Resizes SELF's underlying dynamic heap block to hold membersPlusHole total member slots without altering collection header fields. |
| `ShiftColl` | `PROCEDURE ShiftColl(afterSrcIndex, afterDstIndex, howMany: INTEGER);` | Shifts howMany contiguous members within SELF's dynamic storage from afterSrcIndex to afterDstIndex without updating header fields. |

#### `TList = SUBCLASS OF TCollection`

Dynamic indexed collection of Clascal TObject references stored as relocatable heap handles.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; initialSlack: INTEGER): TList;` | Allocates or initializes an empty TList of TObject handles in heap with initialSlack reserved hole slots. |
| `Clone` | `FUNCTION Clone(heap: THeap): TObject; OVERRIDE;` | Clones the TList in heap and recursively clones every non-NIL TObject element it contains. |
| `Free` | `PROCEDURE Free; OVERRIDE;` | Frees every TObject element stored in the list and then frees the TList object itself. |
| `MemberBytes` | `FUNCTION MemberBytes: INTEGER; OVERRIDE;` | Returns SIZEOF(TObject) (4 bytes) as the element byte size of a TList. |
| `Each` | `PROCEDURE Each(PROCEDURE DoToObject(object: TObject)); DEFAULT;` | Invokes callback procedure DoToObject sequentially on each TObject element in the list from first to last. |
| `Pos` | `FUNCTION Pos(after: LONGINT; object: TObject): LONGINT;` | Searches forward starting after index after for object and returns its 1-based index, or 0 if not found. |
| `Scanner` | `FUNCTION Scanner: TListScanner;` | Creates and returns a forward TListScanner positioned before the first element of SELF. |
| `ScannerFrom` | `FUNCTION ScannerFrom(firstToScan: LONGINT; scanDirection: TScanDirection): TListScanner; DEFAULT;` | Creates and returns a TListScanner over SELF starting at firstToScan in direction scanDirection. |
| `At` | `FUNCTION At(i: LONGINT): TObject; DEFAULT;` | Returns the TObject reference stored at 1-based index i in the list. |
| `First` | `FUNCTION First: TObject; DEFAULT;` | Returns the first TObject element in the list (or NIL if the list is empty). |
| `Last` | `FUNCTION Last: TObject; DEFAULT;` | Returns the last TObject element in the list (or NIL if the list is empty). |
| `ManyAt` | `FUNCTION ManyAt(i, howMany: LONGINT): TList; DEFAULT;` | Creates and returns a new TList in the same heap containing howMany object references copied starting at index i. |
| `InsAt` | `PROCEDURE InsAt(i: LONGINT; object: TObject); DEFAULT;` | Inserts object into the list immediately before 1-based index i. |
| `InsFirst` | `PROCEDURE InsFirst(object: TObject);` | Inserts object at the beginning (index 1) of the list. |
| `InsLast` | `PROCEDURE InsLast(object: TObject);` | Appends object after the last element of the list. |
| `DelAll` | `PROCEDURE DelAll(freeOld: BOOLEAN); DEFAULT;` | Removes all elements from the list, first calling Free on each removed element if freeOld is TRUE. |
| `DelAt` | `PROCEDURE DelAt(i: LONGINT; freeOld: BOOLEAN); DEFAULT;` | Removes the element at 1-based index i from the list, freeing the removed TObject if freeOld is TRUE. |
| `DelFirst` | `PROCEDURE DelFirst(freeOld: BOOLEAN);` | Removes the first element from the list, freeing the removed TObject if freeOld is TRUE. |
| `DelLast` | `PROCEDURE DelLast(freeOld: BOOLEAN);` | Removes the last element from the list, freeing the removed TObject if freeOld is TRUE. |
| `DelManyAt` | `PROCEDURE DelManyAt(i, howMany: LONGINT; freeOld: BOOLEAN); DEFAULT;` | Removes howMany consecutive elements starting at index i, freeing each removed TObject if freeOld is TRUE. |
| `DelObject` | `PROCEDURE DelObject(object: TObject; freeOld: BOOLEAN);` | Finds the first occurrence of object in the list and removes it (if present), freeing it if freeOld is TRUE. |
| `PopLast` | `FUNCTION PopLast: TObject;` | Removes and returns the last TObject element in the list without freeing it (or returns NIL if empty). |
| `PutAt` | `PROCEDURE PutAt(i: LONGINT; object: TObject; freeOld: BOOLEAN); DEFAULT;` | Replaces the element at 1-based index i with object, optionally freeing the displaced TObject when freeOld is TRUE. |

#### `TArray = SUBCLASS OF TCollection`

Dynamic indexed collection of fixed-size byte records stored contiguously inside a relocatable heap object.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; initialSlack, bytesPerRecord: INTEGER): TArray;` | Allocates or initializes a TArray in heap storing fixed-length records of bytesPerRecord bytes with initialSlack slack slots. |
| `MemberBytes` | `FUNCTION MemberBytes: INTEGER; OVERRIDE;` | Returns SELF.recordBytes as the byte size of each record in the array. |
| `Each` | `PROCEDURE Each(PROCEDURE DoToRecord(pRecord: Ptr)); DEFAULT;` | Invokes DoToRecord with a transient pointer to each record in the array from first to last. |
| `Pos` | `FUNCTION Pos(after: LONGINT; pRecord: Ptr): LONGINT;` | Searches forward after index after for a record matching the recordBytes at pRecord and returns its 1-based index, or 0 if not found. |
| `Scanner` | `FUNCTION Scanner: TArrayScanner;` | Creates and returns a forward TArrayScanner positioned at the beginning of SELF. |
| `ScannerFrom` | `FUNCTION ScannerFrom(firstToScan: LONGINT; scanDirection: TScanDirection): TArrayScanner; DEFAULT;` | Creates and returns a TArrayScanner over SELF starting at firstToScan in direction scanDirection. |
| `At` | `FUNCTION At(i: LONGINT): Ptr; DEFAULT;` | Returns a transient Ptr to the record at 1-based index i (valid until heap compaction). |
| `First` | `FUNCTION First: Ptr;` | Returns a transient Ptr to the first record in the array. |
| `GetAt` | `PROCEDURE GetAt(i: LONGINT; pRecord: Ptr); DEFAULT;` | Copies the record at 1-based index i (recordBytes bytes) into the buffer pointed to by pRecord. |
| `Last` | `FUNCTION Last: Ptr;` | Returns a transient Ptr to the last record in the array. |
| `ManyAt` | `FUNCTION ManyAt(i, howMany: LONGINT): TArray; DEFAULT;` | Creates and returns a new TArray containing howMany records copied starting from 1-based index i. |
| `InsAt` | `PROCEDURE InsAt(i: LONGINT; pRecord: Ptr); DEFAULT;` | Inserts the record pointed to by pRecord into the array before 1-based index i. |
| `InsFirst` | `PROCEDURE InsFirst(pRecord: Ptr);` | Inserts the record pointed to by pRecord at the beginning (index 1) of the array. |
| `InsLast` | `PROCEDURE InsLast(pRecord: Ptr);` | Appends the record pointed to by pRecord to the end of the array. |
| `DelAll` | `PROCEDURE DelAll; DEFAULT;` | Deletes all records from the array, resetting its size to zero. |
| `DelAt` | `PROCEDURE DelAt(i: LONGINT); DEFAULT;` | Deletes the record at 1-based index i from the array. |
| `DelFirst` | `PROCEDURE DelFirst;` | Deletes the first record from the array. |
| `DelLast` | `PROCEDURE DelLast;` | Deletes the last record from the array. |
| `DelManyAt` | `PROCEDURE DelManyAt(i, howMany: LONGINT); DEFAULT;` | Deletes howMany consecutive records starting at 1-based index i from the array. |
| `PutAt` | `PROCEDURE PutAt(i: LONGINT; pRecord: Ptr); DEFAULT;` | Copies the record pointed to by pRecord over the existing record at 1-based index i. |

#### `TString = SUBCLASS OF TCollection`

Dynamic indexed collection of CHAR elements supporting Pascal string conversion and QuickDraw text width measurement and drawing.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; initialSlack: INTEGER): TString;` | Allocates or initializes a dynamic character TString in heap with initialSlack reserved character slots. |
| `MemberBytes` | `FUNCTION MemberBytes: INTEGER; OVERRIDE;` | Returns 1 (SIZEOF(CHAR)) as the byte size of each character element in the TString. |
| `Each` | `PROCEDURE Each(PROCEDURE DoToCharacter(character: CHAR));` | Invokes callback procedure DoToCharacter sequentially on each character in the TString from first to last. |
| `Pos` | `FUNCTION Pos(after: LONGINT; character: CHAR): LONGINT;` | Searches forward after index after for character and returns its 1-based index, or 0 if not found. |
| `Scanner` | `FUNCTION Scanner: TStringScanner;` | Creates and returns a forward TStringScanner positioned at the start of SELF. |
| `ScannerFrom` | `FUNCTION ScannerFrom(firstToScan: LONGINT; scanDirection: TScanDirection): TStringScanner;` | Creates and returns a TStringScanner over SELF starting at firstToScan in direction scanDirection. |
| `At` | `FUNCTION At(i: LONGINT): CHAR;` | Returns the CHAR at 1-based index i in the TString. |
| `First` | `FUNCTION First: CHAR;` | Returns the first CHAR in the TString. |
| `Last` | `FUNCTION Last: CHAR;` | Returns the last CHAR in the TString. |
| `ManyAt` | `FUNCTION ManyAt(i, howMany: LONGINT): TString;` | Creates and returns a new TString containing howMany characters copied starting from 1-based index i. |
| `ToPStr` | `PROCEDURE ToPStr(pStr: TPString);` | Copies up to 255 characters of SELF into the Pascal string pointed to by pStr. |
| `ToPStrAt` | `PROCEDURE ToPStrAt(i, howMany: LONGINT; pStr: TPString);` | Copies howMany characters starting at 1-based index i from SELF into the Pascal string pointed to by pStr. |
| `InsAt` | `PROCEDURE InsAt(i: LONGINT; character: CHAR);` | Inserts character into the TString immediately before 1-based index i. |
| `InsFirst` | `PROCEDURE InsFirst(character: CHAR);` | Inserts character at the beginning (index 1) of the TString. |
| `InsLast` | `PROCEDURE InsLast(character: CHAR);` | Appends character to the end of the TString. |
| `InsPStrAt` | `PROCEDURE InsPStrAt(i: LONGINT; pStr: TPString);` | Inserts all characters of Pascal string pStr^ into SELF starting before 1-based index i. |
| `DelAll` | `PROCEDURE DelAll;` | Removes all characters from the TString, setting its length to zero. |
| `DelAt` | `PROCEDURE DelAt(i: LONGINT);` | Removes the character at 1-based index i from the TString. |
| `DelFirst` | `PROCEDURE DelFirst;` | Removes the first character from the TString. |
| `DelLast` | `PROCEDURE DelLast;` | Removes the last character from the TString. |
| `DelManyAt` | `PROCEDURE DelManyAt(i, howMany: LONGINT);` | Removes howMany consecutive characters starting at 1-based index i from the TString. |
| `PutAt` | `PROCEDURE PutAt(i: LONGINT; character: CHAR);` | Replaces the character at 1-based index i in the TString with character. |
| `Draw` | `PROCEDURE Draw(i: LONGINT; howMany: INTEGER);` | Draws howMany characters starting at 1-based index i of SELF into the current QuickDraw GrafPort (bridging any internal hole). |
| `Width` | `FUNCTION Width(i: LONGINT; howMany: INTEGER): INTEGER;` | Measures and returns the QuickDraw pixel width of howMany characters starting at 1-based index i in the current GrafPort font. |

#### `TFile = SUBCLASS OF TCollection`

Collection wrapper representing a Lisa OS disk file with pathname, password protection, catalog operations, and active TFileScanner streams.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsPath: TFilePath; itsPassword: TPassword): TFile;` | Allocates or initializes a TFile descriptor in heap bound to Lisa OS pathname itsPath and password itsPassword. |
| `Free` | `PROCEDURE Free; OVERRIDE;` | Closes and frees all open TFileScanner instances in scanners and then frees the TFile object itself (without deleting the disk file). |
| `Clone` | `FUNCTION Clone(heap: THeap): TObject; OVERRIDE;` | Triggers a runtime error because TFile descriptors cannot be cloned. |
| `MemberBytes` | `FUNCTION MemberBytes: INTEGER; OVERRIDE;` | Returns 1 (one byte per character) as the element size of a byte-addressed disk file. |
| `Scanner` | `FUNCTION Scanner: TFileScanner;` | Creates and opens a read/write TFileScanner ([fRead, fWrite]) positioned at byte 0 of the disk file. |
| `ScannerFrom` | `FUNCTION ScannerFrom(firstToScan: LONGINT; manip: TAccesses): TFileScanner;` | Creates and opens a TFileScanner on SELF with access flags manip positioned at byte offset firstToScan. |
| `ChangePassword` | `PROCEDURE ChangePassword(VAR error: INTEGER; newPassword: TPassword);` | Changes the Lisa OS catalog password protecting SELF's disk file to newPassword and updates SELF.password on success. |
| `Delete` | `PROCEDURE Delete(VAR error: INTEGER);` | Closes any active scanners and deletes the underlying Lisa OS disk file at SELF.path, returning any OS status in error. |
| `Exists` | `FUNCTION Exists(VAR error: INTEGER): BOOLEAN;` | Checks the Lisa OS catalog for SELF.path and returns TRUE if the file exists, setting error if a catalog failure occurs. |
| `WhenModified` | `FUNCTION WhenModified(VAR error: INTEGER): LONGINT;` | Queries the Lisa OS catalog entry for SELF.path and returns its last-modified timestamp as a LONGINT. |
| `Rename` | `PROCEDURE Rename(VAR error: INTEGER; newFileName: TFilePath);` | Renames the Lisa OS disk file at SELF.path to newFileName and updates SELF.path on success. |
| `VerifyPassword` | `FUNCTION VerifyPassword(VAR error: INTEGER; password: TPassword): BOOLEAN;` | Checks whether password grants access to the Lisa OS disk file at SELF.path and returns TRUE if valid. |

#### `TScanner = SUBCLASS OF TObject`

Base sequential iterator over a TCollection that tracks the inter-element scan position, scan direction, and end-of-collection state.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; itsCollection: TCollection; itsInitialPosition: LONGINT; scanDirection: TScanDirection): TScanner;` | Initializes a TScanner attached to itsCollection at starting index itsInitialPosition in direction scanDirection. |
| `Close` | `PROCEDURE Close; DEFAULT;` | Flushes buffers and closes the underlying OS file if the scanner is disk-backed (no-op for in-memory scanners). |
| `Open` | `PROCEDURE Open; DEFAULT;` | Reopens the underlying OS file and primes its buffer if the scanner is disk-backed (no-op for in-memory scanners). |
| `Allocate` | `PROCEDURE Allocate(slack: LONGINT); DEFAULT;` | Pre-allocates slack edit capacity on the underlying collection (equivalent to collection.StartEdit(slack) in memory). |
| `Compact` | `PROCEDURE Compact; DEFAULT;` | Releases unused slack space in the underlying collection (equivalent to collection.StopEdit in memory). |
| `Advance` | `FUNCTION Advance(PROCEDURE DoToCurrent(anotherMember: BOOLEAN)): BOOLEAN;` | Advances the scanner by one increment step if not done or at end, invokes DoToCurrent with whether a member is available, and returns that boolean. |
| `Done` | `PROCEDURE Done; DEFAULT;` | Sets scanDone to TRUE so subsequent Scan calls immediately return FALSE to terminate a scan loop. |
| `Reverse` | `PROCEDURE Reverse; DEFAULT;` | Negates increment to reverse the scanner's traversal direction and updates atEnd accordingly. |
| `Seek` | `PROCEDURE Seek(newPosition: LONGINT); DEFAULT;` | Moves the scanner's position to newPosition (clamped to valid collection bounds) and updates atEnd and scanDone. |
| `Skip` | `PROCEDURE Skip(deltaPos: LONGINT); DEFAULT;` | Offsets the scanner's current position by deltaPos (clamped to valid collection bounds) and updates end-of-scan state. |

#### `TListScanner = SUBCLASS OF TScanner`

Sequential scanner for traversing, appending, replacing, and deleting TObject elements in a TList.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; itsList: TList; itsInitialPosition: LONGINT; itsScanDirection: TScanDirection): TListScanner;` | Allocates or initializes a TListScanner over itsList starting at itsInitialPosition in direction itsScanDirection. |
| `Free` | `PROCEDURE Free; OVERRIDE;` | Compacts the scanned TList if editing slack was active and frees the TListScanner object. |
| `Obtain` | `FUNCTION Obtain: TObject; DEFAULT;` | Returns the TObject element most recently passed over by the scanner. |
| `Scan` | `FUNCTION Scan(VAR nextObject: TObject): BOOLEAN; DEFAULT;` | Advances past the next element in the TList, assigns it to nextObject, and returns TRUE (or returns FALSE at the end). |
| `Append` | `PROCEDURE Append(object: TObject); DEFAULT;` | Inserts object into the TList at the current scan position and advances the scanner past it. |
| `Delete` | `PROCEDURE Delete(freeOld: BOOLEAN); DEFAULT;` | Removes the TObject element just scanned over (optionally freeing it if freeOld is TRUE) and adjusts position. |
| `DeleteRest` | `PROCEDURE DeleteRest(freeOld: BOOLEAN); DEFAULT;` | Deletes all remaining TObject elements ahead of position in the scan direction, freeing them if freeOld is TRUE. |
| `Replace` | `PROCEDURE Replace(object: TObject; freeOld: BOOLEAN); DEFAULT;` | Replaces the TObject element just scanned over with object (freeing the old element if freeOld is TRUE) without moving position. |

#### `TArrayScanner = SUBCLASS OF TScanner`

Sequential scanner for traversing, appending, replacing, and deleting fixed-length records in a TArray.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; itsArray: TArray; itsInitialPosition: LONGINT; itsScanDirection: TScanDirection): TArrayScanner;` | Allocates or initializes a TArrayScanner over itsArray starting at itsInitialPosition in direction itsScanDirection. |
| `Free` | `PROCEDURE Free; OVERRIDE;` | Compacts the scanned TArray if editing slack was active and frees the TArrayScanner object. |
| `Obtain` | `FUNCTION Obtain: Ptr; DEFAULT;` | Returns a transient Ptr to the record most recently passed over by the scanner. |
| `Scan` | `FUNCTION Scan(VAR pNextRecord: Ptr): BOOLEAN; DEFAULT;` | Advances past the next record in the TArray, sets pNextRecord to point to it, and returns TRUE (or FALSE at the end). |
| `Append` | `PROCEDURE Append(pRecord: Ptr); DEFAULT;` | Inserts the record at pRecord into the TArray at the current scan position and advances past it. |
| `Delete` | `PROCEDURE Delete; DEFAULT;` | Deletes the record most recently scanned over from the TArray and adjusts position. |
| `DeleteRest` | `PROCEDURE DeleteRest; DEFAULT;` | Deletes all remaining records ahead of position in the scan direction from the TArray. |
| `Replace` | `PROCEDURE Replace(pRecord: Ptr); DEFAULT;` | Overwrites the record most recently scanned over with the record at pRecord while maintaining position. |

#### `TStringScanner = SUBCLASS OF TScanner`

Sequential character scanner and binary serialization stream over a TString supporting typed reading and writing of numbers, Pascal strings, TArray instances, and TObject graphs.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; itsString: TString; itsInitialPosition: LONGINT; itsScanDirection: TScanDirection): TStringScanner;` | Allocates or initializes a TStringScanner over itsString starting at itsInitialPosition in direction itsScanDirection. |
| `Free` | `PROCEDURE Free; OVERRIDE;` | Compacts the scanned TString if editing slack was active and frees the TStringScanner object. |
| `Obtain` | `FUNCTION Obtain: CHAR; DEFAULT;` | Returns the CHAR most recently passed over by the scanner. |
| `Scan` | `FUNCTION Scan(VAR nextChar: CHAR): BOOLEAN; DEFAULT;` | Advances past the next character in the TString, stores it in nextChar, and returns TRUE (or FALSE at the end). |
| `Append` | `PROCEDURE Append(character: CHAR); DEFAULT;` | Inserts character at the current scan position in the TString and advances past it. |
| `Delete` | `PROCEDURE Delete; DEFAULT;` | Deletes the character most recently scanned over from the TString and adjusts position. |
| `DeleteRest` | `PROCEDURE DeleteRest; DEFAULT;` | Deletes all remaining characters ahead of position in the scan direction from the TString. |
| `Replace` | `PROCEDURE Replace(character: CHAR); DEFAULT;` | Replaces the character most recently scanned over with character while maintaining position. |
| `ReadArray` | `FUNCTION ReadArray(heap: THeap; bytesPerRecord: INTEGER): TArray;` | Reads a serialized element count and contiguous record bytes from the stream and returns a newly allocated TArray in heap. |
| `ReadNumber` | `FUNCTION ReadNumber(numBytes: SizeOfNumber): LONGINT;` | Reads a numBytes (1..4) integer from the stream (signed when numBytes is even, unsigned when odd) and returns it as a LONGINT. |
| `ReadObject` | `FUNCTION ReadObject(heap: THeap): TObject;` | Reads a serialized class identifier (or NIL marker), allocates the Clascal instance in heap, invokes object.Read(SELF), and returns it. |
| `WriteArray` | `PROCEDURE WriteArray(a: TArray);` | Writes TArray a's element count and raw contiguous record bytes to the stream (inverse of ReadArray). |
| `WriteNumber` | `PROCEDURE WriteNumber(value: LONGINT; numBytes: SizeOfNumber);` | Writes the low-order numBytes (1..4) bytes of value sequentially to the stream. |
| `WriteObject` | `PROCEDURE WriteObject(object: TObject);` | Writes object's class identifier (or a NIL marker if NIL) to the stream and invokes object.Write(SELF). |
| `XferContiguous` | `PROCEDURE XferContiguous(whichWay: xReadWrite; collection: TCollection);` | Reads or writes (per whichWay) a TCollection's element count and contiguous member bytes non-recursively. |
| `XferFields` | `PROCEDURE XferFields(whichWay: xReadWrite; object: TObject);` | Reads or writes (per whichWay) all fixed instance fields of object except its leading class pointer. |
| `XferPString` | `PROCEDURE XferPString(whichWay: xReadWrite; pStr: TPString);` | Reads or writes (per whichWay) the length byte followed by the character bytes of Pascal string pStr^. |
| `XferSequential` | `PROCEDURE XferSequential(whichWay: xReadWrite; pFirst: Ptr; numBytes: LONGINT); DEFAULT;` | Transfers numBytes sequentially between the stream at SELF.position and memory buffer pFirst (updating actual and position). |
| `XferRandom` | `PROCEDURE XferRandom(whichWay: xReadWrite; pFirst: Ptr; numBytes: LONGINT; mode: TIOMode; offset: LONGINT); DEFAULT;` | Transfers numBytes between memory buffer pFirst and the stream at the location specified by I/O positioning mode and offset. |

#### `TFileScanner = SUBCLASS OF TStringScanner`

Buffered sequential and random-access stream scanner over a Lisa OS disk TFile, extending TStringScanner with OS file refnum management and disk-page allocation.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; itsFile: TFile; manip: TAccesses): TFileScanner;` | Creates and opens a TFileScanner on itsFile with Lisa OS access modes manip and registers it in itsFile.scanners. |
| `FreeObject` | `PROCEDURE FreeObject; OVERRIDE;` | Closes the underlying OS file refnum, unregisters SELF from its TFile.scanners list, and frees the scanner object. |
| `Free` | `PROCEDURE Free; OVERRIDE;` | Closes and frees SELF, and if SELF was the last scanner attached to its TFile, frees the TFile object as well. |
| `Close` | `PROCEDURE Close; OVERRIDE;` | Flushes pending file output and closes the Lisa OS file refnum while preserving SELF.position for a later Open. |
| `Open` | `PROCEDURE Open; OVERRIDE;` | Opens (creating if writable and absent) the TFile's Lisa OS disk file, seeks to SELF.position, and records its refnum. |
| `Allocate` | `PROCEDURE Allocate(slack: LONGINT); OVERRIDE;` | Pre-allocates unused Lisa OS disk pages corresponding to slack bytes to reduce disk fragmentation during writes. |
| `Compact` | `PROCEDURE Compact; OVERRIDE;` | Truncates unused pre-allocated disk pages from the Lisa OS file back to free disk space. |
| `Seek` | `PROCEDURE Seek(newPosition: LONGINT); OVERRIDE;` | Sets the file stream position to byte offset newPosition (clamped to 0..file size) and updates end-of-file state. |
| `Skip` | `PROCEDURE Skip(deltaPos: LONGINT); OVERRIDE;` | Advances or rewinds the file stream position by deltaPos bytes and updates end-of-file state. |
| `Obtain` | `FUNCTION Obtain: CHAR; OVERRIDE;` | Reads and returns the character immediately preceding the current file position. |
| `Scan` | `FUNCTION Scan(VAR nextChar: CHAR): BOOLEAN; OVERRIDE;` | Reads the next character from the disk file into nextChar, advances position, and returns FALSE on EOF or I/O error. |
| `Append` | `PROCEDURE Append(character: CHAR); OVERRIDE;` | Writes character at the current file position and advances position by one byte. |
| `Delete` | `PROCEDURE Delete; OVERRIDE;` | Moves the file scanner position back by one byte (acting as Skip(-1) on disk files). |
| `DeleteRest` | `PROCEDURE DeleteRest; OVERRIDE;` | Truncates the Lisa OS disk file at SELF.position, discarding all bytes beyond the current position. |
| `Replace` | `PROCEDURE Replace(character: CHAR); OVERRIDE;` | Overwrites the character immediately preceding SELF.position in the disk file while keeping SELF.position unchanged. |
| `XferSequential` | `PROCEDURE XferSequential(whichWay: xReadWrite; pFirst: Ptr; numBytes: LONGINT); OVERRIDE;` | Reads or writes numBytes sequentially between the open Lisa OS file at SELF.position and buffer pFirst, updating actual and error. |
| `XferRandom` | `PROCEDURE XferRandom(whichWay: xReadWrite; pFirst: Ptr; numBytes: LONGINT; mode: TIOMode; offset: LONGINT); OVERRIDE;` | Reads or writes numBytes between buffer pFirst and the open Lisa OS file using positioning mode (fAbsolute, fRelative, fSequential) and offset. |
