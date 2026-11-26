# `PRLIB` (`PRLib.obj`) — Lisa Print Manager, Dialogs & Background Spooler Library

[Back to Library Index](LIBRARIES.md)

Lisa printing architecture (`PrStdProcs`, `PrPublic`, `PrMgr`, `PrDlgMgr`, `PrSpool`, `PrBuf`, `PrFileProcs`, `PrEvents`, `Queues`) for QuickDraw page imaging, print dialogs, spool files, and printer drivers.

- **Object file**: `libs/workshop3.0/PRLib.obj` (Intrinsic library)
- **Contents**: 9 units, 140 top-level procedures/functions

## Importing and Linking

```pascal
USES PrBuf, PrDlgMgr, PrEvents;
```

```sh
pascal/lpc.py --link=IOSPASLIB,SYS1LIB,PRLIB MYPROG
```

## Units in This Library

| Unit | 8-Char Symbol | `USES` Dependencies | Routines | Summary |
|---|---|---|---|---|
| [`PrBuf`](#unit-prbuf) | `PRBUF` | `SysCall`, `PMDecl`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `PrStdInfo` | 7 | Buffers and sorts text runs and horizontal or vertical rule commands within a QuickDraw print band for character and daisy-wheel printer drivers. Coalesces adjacent text and overlapping rules before invoking driver-supplied check, scan-line, and dump callbacks. |
| [`PrDlgMgr`](#unit-prdlgmgr) | `PRDLGMGR` | `SysCall`, `UnitStd`, `UnitHz`, `HWInt`, `QuickDraw`, `FontMgr`, `Storage`, `Events`, `Folders`, `WmlStd`, `WmlCrs`, `PMDecl`, `PrStdInfo` | 44 | Implements the Print Manager dialog box framework, including modal event loops, blinking text-entry carets, checkforms, button groups (menus), and interactive buttons. Supports mouse hit-testing, keyboard parameter entry, and screen updates inside the Lisa dialog folder. |
| [`PrEvents`](#unit-prevents) | `PREVENTS` | `UnitStd`, `SysCall`, `PMDecl`, `UnitHz`, `Storage`, `QuickDraw`, `GrafUtil`, `FontMgr`, `PrStdInfo`, `PrStdProcs` | 16 | Provides interprocess event-channel communication between foreground applications and background Print Manager daemon and printer driver processes. Supports synchronous call channels, asynchronous notifications, print job submission and cancellation, and multi-packet data transfers. |
| [`PrFileProcs`](#unit-prfileprocs) | `PRFILEPR` | `SysCall`, `PMDecl`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `PrStdInfo`, `PrStdProcs` | 5 | Provides low-level Lisa OS file I/O wrappers for reading, writing, and positioning print spool files. |
| [`PrMgr`](#unit-prmgr) | `PRMGR` | `UnitStd`, `SysCall`, `HWInt`, `PMDecl`, `UnitHz`, `Storage`, `QuickDraw`, `GrafUtil`, `FontMgr`, `FmgrUtil`, `Events`, `Menus`, `Windows`, `Folders`, `WmlCrs`, `AlertMgr`, `PMM`, `PrStdInfo`, `PrStdProcs`, `Queues`, `PrEvents`, `PrDlgMgr` | 15 | Implements core Print Manager initialization, shared data-segment binding, printer setup and job dialogs, alert presentation, and print record validation. Coordinates foreground applications with background printer processes via shared memory and event channels. |
| [`PrPublic`](#unit-prpublic) | `PRPUBLIC` | `SysCall`, `PMDecl`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `PrStdInfo` | 16 | Exposes the public application-level Print Manager interface for initializing printing, validating and comparing print records, displaying setup and print dialogs, and bracketing spooled document and page drawing. |
| [`PrSpool`](#unit-prspool) | `PRSPOOL` | `HWInt`, `SysCall`, `PMDecl`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `Events`, `Folders`, `Menus`, `Windows`, `WmlStd`, `WmlCrs`, `AlertMgr`, `PrStdInfo`, `PrStdProcs`, `PrFileProcs`, `Queues`, `PrEvents`, `PrDlgMgr`, `PrMgr` | 5 | Captures QuickDraw page drawing into disk-backed print spool files and submits spooled page blocks to the background print supervisor. Manages private spooling heap zones, disk-space reservation, spooling alerts, page-range filtering, and user abort handling. |
| [`PrStdProcs`](#unit-prstdprocs) | `PRSTDPRO` | `SysCall`, `PMDecl`, `HWInt`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `PrStdInfo` | 21 | Provides shared Print Manager utility, hardware port I/O, process scheduling, bitmap inspection, and 68000 block/bitwise helper routines used by printer drivers and spooler units. |
| [`Queues`](#unit-queues) | `QUEUES` | `UnitStd`, `UnitHz` | 11 | Implements synchronized singly linked queues of heap handles with mutual-exclusion locking, insertion, removal, length queries, and callback-based enumeration. |

---

## Unit PrBuf

Buffers and sorts text runs and horizontal or vertical rule commands within a QuickDraw print band for character and daisy-wheel printer drivers. Coalesces adjacent text and overlapping rules before invoking driver-supplied check, scan-line, and dump callbacks.

- **Import**: `USES PrBuf;`
- **Unit kind**: `INTRINSIC` (`PRBUF`)
- **Interface dependencies**: `SysCall`, `PMDecl`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `PrStdInfo`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `PbClose` | `PROCEDURE PbClose;` | Frees the dynamic character data buffer, command array, and state handle allocated for the current print buffer session. |
| `PbDumpBand` | `PROCEDURE PbDumpBand;` | Iterates over every scan line in the current port rectangle, invoking the installed scan-line callback and executing buffered text and rule dump callbacks sorted by coordinate before resetting the buffer. |
| `PbHRule` | `PROCEDURE PbHRule(cLength: TC);` | Clips a horizontal rule of signed pixel length cLength from the current pen location against the port clip region, coalescing or queuing a pbCmdHRule command and advancing pnLoc.h. |
| `PbOffSet` | `PROCEDURE PbOffSet(HOff, VOff: Integer);` | Sets the global horizontal and vertical print-buffer coordinate offsets HOffSet and VOffSet to HOff and VOff. |
| `PbOpen` | `PROCEDURE PbOpen(install: TPbInstall);` | Allocates and initializes the print command and text buffers on TheHeap and registers the caller's check, dump, and scan-line callbacks from install. |
| `PbText` | `PROCEDURE PbText(cCount: TC; p: TP);` | Clips cCount characters starting at pointer p against the port clip region, coalescing contiguous same-style characters into pbCmdText commands and advancing pnLoc.h by the text width. |
| `PbVRule` | `PROCEDURE PbVRule(cLength: TC);` | Clips a vertical rule of signed pixel length cLength from the current pen location against the port clip region, coalescing or queuing a pbCmdVRule command and advancing pnLoc.v. |

---

## Unit PrDlgMgr

Implements the Print Manager dialog box framework, including modal event loops, blinking text-entry carets, checkforms, button groups (menus), and interactive buttons. Supports mouse hit-testing, keyboard parameter entry, and screen updates inside the Lisa dialog folder.

- **Import**: `USES PrDlgMgr;`
- **Unit kind**: `INTRINSIC` (`PRDLGMGR`)
- **Interface dependencies**: `SysCall`, `UnitStd`, `UnitHz`, `HWInt`, `QuickDraw`, `FontMgr`, `Storage`, `Events`, `Folders`, `WmlStd`, `WmlCrs`, `PMDecl`, `PrStdInfo`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `DlgMgrInit` | `PROCEDURE DlgMgrInit;` | Initializes PrDlgMgr globals including the shared empty string handle hspNil, frame pen sizes, caret blink state, and cleared dialog callback pointers. |
| `PauseEvt` | `PROCEDURE PauseEvt(dt: TC);` | Yields the CPU to other processes until dt ticks have elapsed or a mouse button-down or key-down event is queued. |
| `FMseInFldr` | `FUNCTION FMseInFldr(pwnd: WindowPtr; VAR pt: Point): TF;` | Sets the current port to pwnd, reads the local mouse position into pt, and returns TRUE if pt lies within pwnd's visible region. |
| `PrStrToNum` | `PROCEDURE PrStrToNum(spNum: TSp; VAR c: TC);` | Parses the unsigned decimal digit string spNum into integer c (returning 0 for an empty string). |
| `PrNumToStr` | `PROCEDURE PrNumToStr(c: TC; VAR spNum: TSp);` | Converts signed integer c into decimal string spNum, returning an empty string when c is 0. |
| `PrCkEvent` | `PROCEDURE PrCkEvent(event: EventRecord);` | Handles buttonDown, keyDown, and folderUpdate events in dialogFolder for the active checkform hckfmPrCk and command callback procCkCmd. |
| `PrCkTrkMse` | `PROCEDURE PrCkTrkMse;` | Tracks the mouse position inside dialogFolder against the active checkform hckfmPrCk and updates the standard cursor accordingly. |
| `CaretMove` | `PROCEDURE CaretMove(pwnd: WindowPtr; h, v: TC);` | Moves the text-entry caret to coordinates (h, v) in window pwnd and inverts the caret rectangle on screen. |
| `CaretSynch` | `PROCEDURE CaretSynch;` | Ensures the text-entry caret is erased (undrawn) on screen before drawing or handling dialog events. |
| `CaretKill` | `PROCEDURE CaretKill;` | Erases the active text-entry caret if visible and detaches it from its window. |
| `CaretFlip` | `PROCEDURE CaretFlip;` | Inverts the 1-pixel-wide vertical caret bar at the current caret position using the port's font ascent and descent, updating the blink timestamp. |
| `CaretBlink` | `PROCEDURE CaretBlink;` | Toggles the caret's visibility via CaretFlip if a caret window is active and the blink interval has elapsed. |
| `DlgInstall` | `PROCEDURE DlgInstall(fKey: TF; pEvent, pIdle, pEnd: TProc);` | Installs the active dialog configuration into dbox, setting whether keyboard input is accepted (fKey) and registering the event, idle, and end callbacks (pEvent, pIdle, pEnd). |
| `DlgEvent` | `PROCEDURE DlgEvent(event: EventRecord);` | Sets the current port to dialogFolder and dispatches event to the installed dialog event callback dbox.procEvent. |
| `DlgIdle` | `PROCEDURE DlgIdle;` | Invokes the installed dialog idle callback dbox.procIdle with dialogFolder active and blinks the caret if keyboard input is enabled. |
| `DlgEnd` | `PROCEDURE DlgEnd(fDismiss: TF);` | Terminates the active dialog by killing any caret, invoking dbox.procEnd with fDismiss, collapsing dialogFolder height to zero, clearing callbacks, and resetting the cursor. |
| `DlgOpen` | `PROCEDURE DlgOpen(dv: TC);` | Opens dialogFolder to vertical height dv, resets its origin and clip rectangle, and clears its interior to white. |
| `FDlgEvent` | `FUNCTION FDlgEvent(VAR event: EventRecord): TF;` | Polls the Window Manager event queue for an event belonging to dialogFolder (or dismissing events outside it), converting event.where to local coordinates and returning TRUE when an event is dequeued. |
| `DlgMain` | `PROCEDURE DlgMain;` | Runs the modal dialog loop until dialogFolder is hidden, dispatching queued dialog events via DlgEvent or calling DlgIdle while yielding to other processes. |
| `FDlgDone` | `FUNCTION FDlgDone: TF;` | Returns TRUE if dialogFolder is no longer visible, indicating that the active dialog has finished. |
| `FCkfmSelect` | `FUNCTION FCkfmSelect(hckfm: THckfm; ptMse: Point; VAR iMu, iBtn: TB): TF;` | Tracks the mouse while the button remains pressed over checkform hckfm starting at ptMse, highlighting hit buttons and returning TRUE with the selected menu and button indices in iMu and iBtn. |
| `CkFmSetUp` | `PROCEDURE CkFmSetUp(hckfm: THckfm; fInit: TF; setIdMuActv: TSetIdMu);` | Configures checkform hckfm by activating menus whose IDs are in setIdMuActv, resetting button defaults or erasing newly inactive menus according to fInit, and clearing editable text/number buttons. |
| `CkfmShow` | `PROCEDURE CkfmShow(hckfm: THckfm; fInit: TF);` | Draws all active menus in checkform hckfm, skipping already-visible menus when fInit is TRUE. |
| `CkfmTrkMse` | `PROCEDURE CkfmTrkMse(hckfm: THckfm; pWnd: WindowPtr);` | Updates the cursor to the check-mark hit cursor when the mouse in window pWnd is over an active non-dismiss button in checkform hckfm, or to the inactive cursor otherwise. |
| `CkfmKeys` | `PROCEDURE CkfmKeys(hckfm: THckfm; iMu, iBtn: TB);` | Selects button iBtn of menu iMu in checkform hckfm as the active keyboard-entry field (blanking its text and placing the caret), or kills the caret if either index is nil. |
| `CkfmAddCh` | `PROCEDURE CkfmAddCh(hckfm: THckfm; ch: CHAR);` | Processes typed character ch for the active keyboard field in checkform hckfm, handling backspace, advancing to the next editable field on Tab/Return, or appending ch. |
| `FCkfmNxtKey` | `FUNCTION FCkfmNxtKey(hckfm: THckfm; VAR iMuNxt, iBtnNxt: TB): TF;` | Searches checkform hckfm after (iMuNxt, iBtnNxt) for the next visible numeric or string entry button, updating iMuNxt and iBtnNxt and returning TRUE if found. |
| `CkfmSp` | `PROCEDURE CkfmSp(hckfm: THckfm; iMu, iBtn: TB; VAR sp: TSp; fNew: TF);` | Retrieves or appends the text of button iBtn in menu iMu of checkform hckfm into string sp (clearing sp first if fNew is TRUE and concatenating any adjacent continuation button). |
| `FCkfmHit` | `FUNCTION FCkfmHit(hckfm: THckfm; iMu, iBtn: TB): TF;` | Returns TRUE if button iBtn (or the user default button when iBtn is iBtnStd) is currently selected in menu iMu of checkform hckfm. |
| `MuShow` | `PROCEDURE MuShow(hmu: THmu);` | Draws all buttons of menu hmu, highlights its currently selected button iBtnOn, and marks the menu visible if it is active. |
| `MuErase` | `PROCEDURE MuErase(hmu: THmu);` | Erases all buttons of menu hmu from the screen and marks the menu not visible if it is currently displayed. |
| `MuPush` | `PROCEDURE MuPush(hmu: THmu; iBtn: TB);` | Changes the selected button in menu hmu to iBtn (resolving iBtnStd to iBtnUsr), unhighlighting the previous selection and highlighting the new button if visible. |
| `FMuHit` | `FUNCTION FMuHit(hmu: THmu; ptMse: Point; VAR iBtn: TB): TF;` | Tests whether point ptMse lies inside a visible, interactive button of visible menu hmu, setting iBtn to the hit button index and returning TRUE if hit. |
| `BtnDraw` | `PROCEDURE BtnDraw(btn: TBtn);` | Draws visible button btn's frame (square, oval, or round-rect unless informational or iconic) and renders its label string at the aligned text origin. |
| `BtnErase` | `PROCEDURE BtnErase(btn: TBtn);` | Erases the union of visible button btn's bounding rectangle and rendered label string bounds. |
| `BtnFill` | `PROCEDURE BtnFill(btn: TBtn; fFlip: TF);` | Inverts or clears to white the interior shape (or XORs the icon mask) of visible button btn according to fFlip. |
| `BtnPtSp` | `PROCEDURE BtnPtSp(btn: TBtn; VAR ptSp: Point; VAR dhSp: TC);` | Computes the baseline drawing origin ptSp and pixel width dhSp for button btn's string according to its horizontal alignment quadrant and font metrics. |
| `BtnWrite` | `PROCEDURE BtnWrite(btn: TBtn; sp: TSp);` | Copies string sp (truncated to smax) into visible button btn's string handle, clears the button interior to white, and redraws the button. |
| `BtnAddCh` | `PROCEDURE BtnAddCh(btn: TBtn; ch: CHAR);` | Appends character ch to visible numeric or string input button btn (flashing the button on invalid or overflow input), scrolls existing text if needed, draws ch, and advances the caret. |
| `BtnBkSp` | `PROCEDURE BtnBkSp(btn: TBtn);` | Deletes the last character from visible editable button btn, erases and re-centers/scrolls the remaining text, and repositions the caret. |
| `BtnBind` | `PROCEDURE BtnBind(VAR lx: TLx);` | Configures QuickDraw font, face, text mode, and pen size/pattern from button lexical descriptor lx, falling back to sysText if font metrics lookup fails. |
| `BtnSetSp` | `PROCEDURE BtnSetSp(btn: TBtn; sp: TSp; showIt: TF);` | Copies string sp (clamped to smax) into visible button btn's string handle and, if showIt is TRUE, erases and redraws the button. |
| `BtnReappear` | `PROCEDURE BtnReappear(hmu: THmu; iBtn: TB);` | Marks button iBtn in menu hmu as visible if hidden and draws it immediately when the menu is visible. |
| `BtnVanish` | `PROCEDURE BtnVanish(hmu: THmu; iBtn: TB);` | Deselects and erases button iBtn in menu hmu if visible and marks the button hidden. |

---

## Unit PrEvents

Provides interprocess event-channel communication between foreground applications and background Print Manager daemon and printer driver processes. Supports synchronous call channels, asynchronous notifications, print job submission and cancellation, and multi-packet data transfers.

- **Import**: `USES PrEvents;`
- **Unit kind**: `INTRINSIC` (`PREVENTS`)
- **Interface dependencies**: `UnitStd`, `SysCall`, `PMDecl`, `UnitHz`, `Storage`, `QuickDraw`, `GrafUtil`, `FontMgr`, `PrStdInfo`, `PrStdProcs`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `PrAccept` | `FUNCTION PrAccept(VAR Chan: Channel): PrMessage;` | Blocks on open receive event channel Chan until an OS event arrives and returns the received PrMessages command byte (or ENull on error). |
| `PrCall` | `PROCEDURE PrCall(VAR cError: TC; PrID: TL; Message: PrMessages; mess1, mess2, mess3, mess4: TL);` | Sends Message with four longint arguments (mess1..mess4) to process PrID's '.K' call channel followed by an ENull wakeup on its main channel, returning any OS status in cError. |
| `PrCloseChan` | `PROCEDURE PrCloseChan(VAR Chan: Channel);` | Closes and destroys the Lisa OS event channel described by Chan. |
| `PrDeferToBgd` | `PROCEDURE PrDeferToBgd(PrID: TL; Message: PrMessages; mess1, mess2, mess3, mess4: TL);` | Sends Message over process PrID's call channel via PrCall and suspends the calling foreground process until the background process finishes and reactivates it. |
| `PrIDtoPath` | `PROCEDURE PrIDtoPath(PrID: TL; VAR path: PathName);` | Formats 32-bit process ID PrID as an 8-digit uppercase hexadecimal string in path for naming Lisa OS event channels. |
| `PrOffer` | `PROCEDURE PrOffer(VAR Chan: Channel; Message: PrMessages);` | Writes Message into Chan.EvBlock and transmits the event block over already-open event channel Chan via SEND_EVENT_CHN. |
| `PrOpenChan` | `PROCEDURE PrOpenChan(VAR Chan: Channel; Rx: TF);` | Creates and opens an event channel named after the calling process ID in Chan for receiving (when Rx is TRUE) or sending (when Rx is FALSE). |
| `PrOpenCall` | `PROCEDURE PrOpenCall(VAR Chan: Channel; ExProc: LongAdr);` | Declares exception handler ExProc and creates and opens a '.K' receive call channel named after the calling process ID in Chan. |
| `PrJobCount` | `PROCEDURE PrJobCount(PrID: TL; VAR cjob: INTEGER);` | Queries background supervisor process PrID with an EJobCount notification and returns the active print job count from its EReply message in cjob. |
| `PrNotify` | `PROCEDURE PrNotify(PrID: TL; Message: PrMessages; mess1, mess2, mess3, mess4: TL);` | Sends asynchronous notification Message with four longint parameters (mess1..mess4) to process PrID's main event channel. |
| `PrPrintRequest` | `PROCEDURE PrPrintRequest(PrID: TL; lFileName, ncopies, PrntrID, PortID: TL);` | Sends an EPrintRequest notification to background supervisor PrID with spool file ID lFileName, copy count ncopies, printer ID PrntrID, and port PortID. |
| `PrPrintStop` | `PROCEDURE PrPrintStop(PrID: TL; lFileName, ncopies, PrntrID, PortID: TL);` | Sends an EPrintTerminate notification to process PrID to cancel printing for spool file lFileName, copy count ncopies, printer ID PrntrID, and port PortID. |
| `PrSendMessage` | `PROCEDURE PrSendMessage(VAR cError: INTEGER; VAR Chan: Channel; Message: PrMessages);` | Opens Chan.ChName for transmission, offers Message via PrOffer, closes the channel, and returns the open status in cError. |
| `PrWaitMessage` | `FUNCTION PrWaitMessage(VAR Chan: Channel): PrMessage;` | Opens Chan.ChName for reception, waits for and returns one PrMessages value via PrAccept, and closes the channel. |
| `PrStuffData` | `PROCEDURE PrStuffData(PrID: TL; dataPtr: TP; nbytes: TC);` | Transmits nbytes of arbitrary data from dataPtr to process PrID as a sequence of numbered 38-byte EStuffed event messages. |
| `PrUpdate` | `PROCEDURE PrUpdate;` | Notifies the background print supervisor process via an EMetrics call that printer configuration settings have been updated. |

---

## Unit PrFileProcs

Provides low-level Lisa OS file I/O wrappers for reading, writing, and positioning print spool files.

- **Import**: `USES PrFileProcs;`
- **Unit kind**: `INTRINSIC` (`PRFILEPR`)
- **Interface dependencies**: `SysCall`, `PMDecl`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `PrStdInfo`, `PrStdProcs`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `OpenBlock` | `PROCEDURE OpenBlock(VAR error: Integer; Var FileRec: TPrFileRec; access: MSet);` | Opens the Lisa OS file named in FileRec.FileName with access mode set access (creating the file first if error 948 indicates it does not exist), storing the reference number in FileRec.RefNum and status in error. |
| `WriteBlock` | `PROCEDURE WriteBlock(VAR error: Integer; p: TP; lCount: LongInt; RefNum: Integer);` | Writes lCount sequential bytes from buffer pointer p to open file RefNum via Write_Data, returning the OS error code in error. |
| `ReadBlock` | `PROCEDURE ReadBlock(VAR error: Integer; p: TP; lCount: LongInt; RefNum: Integer);` | Reads lCount sequential bytes from open file RefNum into buffer pointer p via Read_Data, returning the OS error code in error. |
| `PfSetPos` | `PROCEDURE PfSetPos(VAR error: Integer; lPos: TL; RefNum: Integer);` | Positions the file marker of open file RefNum to absolute byte offset lPos, returning any OS error code in error. |
| `PfSavePos` | `PROCEDURE PfSavePos(VAR error: Integer; VAR lPos: TL; RefNum: Integer);` | Retrieves the current file marker position of open file RefNum into lPos via Info, returning any OS error code in error. |

---

## Unit PrMgr

Implements core Print Manager initialization, shared data-segment binding, printer setup and job dialogs, alert presentation, and print record validation. Coordinates foreground applications with background printer processes via shared memory and event channels.

- **Import**: `USES PrMgr;`
- **Unit kind**: `INTRINSIC` (`PRMGR`)
- **Interface dependencies**: `UnitStd`, `SysCall`, `HWInt`, `PMDecl`, `UnitHz`, `Storage`, `QuickDraw`, `GrafUtil`, `FontMgr`, `FmgrUtil`, `Events`, `Menus`, `Windows`, `Folders`, `WmlCrs`, `AlertMgr`, `PMM`, `PrStdInfo`, `PrStdProcs`, `Queues`, `PrEvents`, `PrDlgMgr`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `PrMgrInit` | `PROCEDURE PrMgrInit;` | Initializes the Print Manager and dialog manager for a foreground application and loads the Print Manager alert phrase file (requires InitAlerts beforehand). |
| `PrBgdInit` | `PROCEDURE PrBgdInit;` | Initializes the Print Manager, dialog manager, and window manager cursors for a background print process. |
| `PrGlobalInit` | `PROCEDURE PrGlobalInit;` | Resets global Print Manager state variables (error code, background dialog flag, parent process ID, initialization flag, and spool alert flag) once at system boot. |
| `PrWaitDad` | `PROCEDURE PrWaitDad;` | Yields the CPU repeatedly until the background father print process completes initialization or is marked absent. |
| `PrPrfDlg` | `PROCEDURE PrPrfDlg(VAR prprf: TPrRec; VAR fNewStl: TF; fPgSzSuppress: TF);` | Displays the 'Format for Printer...' dialog (and printer selection dialog if needed) for print record prprf, optionally suppressing custom paper sizes when fPgSzSuppress is TRUE and setting fNewStl if formatting changed. |
| `FPrInsDlg` | `FUNCTION FPrInsDlg(VAR prprf: TPrRec; VAR fNewStl: TF; prmode: PrMenuSuppress): TF;` | Displays the 'Print...' job dialog for print record prprf with menu-suppression mode prmode, updating prprf and fNewStl and returning TRUE if the user confirmed OK. |
| `PrBgdDlg` | `PROCEDURE PrBgdDlg;` | Requests the background print supervisor process to display the 'Monitor the Printer' status dialog. |
| `PrDlgDefault` | `PROCEDURE PrDlgDefault(fPgSzSuppress: TF; Prmode: PrMenuSuppress; MaxHeight, MaxWidth, MinHeight, MinWidth: TC);` | Configures default dialog options in DlgSettings, including custom-page-size suppression fPgSzSuppress, menu suppression Prmode, and paper height/width bounds (MaxHeight, MaxWidth, MinHeight, MinWidth). |
| `PrMgrDSBind` | `PROCEDURE PrMgrDSBind(VAR cErr: TC);` | Opens or binds the shared Print Manager data segment into memory with reference counting, setting pPrMgrDS and returning any OS error in cErr. |
| `PrMgrDSUnBind` | `PROCEDURE PrMgrDSUnBind(VAR cErr: TC);` | Decrements the shared Print Manager data-segment bind count and unbinds the segment when the count reaches zero, returning any OS error in cErr. |
| `PrOtherAlert` | `FUNCTION PrOtherAlert(AFile: TAlertFile; AlertN: TC; AlertT: TAlertKind; BGD: TF): TC;` | Hides any active spooling wait alert and displays alert AlertN of kind AlertT from alert file AFile (using BackgroundAlert when BGD is TRUE), returning the user's button choice. |
| `PrPrfDefault` | `PROCEDURE PrPrfDefault(VAR prprf: TPrRec);` | Initializes print record prprf from the system default printer in shared memory (or fallback ROM/68K defaults) and resets its job page-range and copy fields. |
| `fPrPrfEq` | `FUNCTION fPrPrfEq(VAR prprf1, prprf2: TPrRec): TF;` | Performs a byte-for-byte comparison of print records prprf1 and prprf2 and returns TRUE if they are identical. |
| `FPrPrfValid` | `FUNCTION FPrPrfValid(VAR prprf: TPrRec): TF;` | Checks whether print record prprf has the current PrVersion and matches an installed printer ID in the shared Print Manager queue. |
| `PrLFntID` | `PROCEDURE PrLFntID(VAR prprf: TPrRec; famIn: TC; setIn: Style; VAR lFntid: TLFntID);` | Constructs a long font identifier lFntid combining the target device from prprf, font family famIn, and text style setIn. |

---

## Unit PrPublic

Exposes the public application-level Print Manager interface for initializing printing, validating and comparing print records, displaying setup and print dialogs, and bracketing spooled document and page drawing.

- **Import**: `USES PrPublic;`
- **Unit kind**: `INTRINSIC` (`PRPUBLIC`)
- **Interface dependencies**: `SysCall`, `PMDecl`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `PrStdInfo`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `PsYieldCpu` | `PROCEDURE PsYieldCpu;` | Temporarily lowers the calling process priority and yields the CPU so background printing processes can run. |
| `PrGlobalInit` | `PROCEDURE PrGlobalInit;` | Resets global Print Manager state variables once per system boot before starting background print processes. |
| `FPrPrfValid` | `FUNCTION FPrPrfValid(VAR prprf: TPrRec): TF;` | Returns TRUE if print record prprf has the current version number and corresponds to a valid registered printer. |
| `PrPrfDefault` | `PROCEDURE PrPrfDefault(VAR prprf: TPrRec);` | Populates uninitialized print record prprf with default printer settings and standard single-copy job parameters. |
| `fPrPrfEq` | `FUNCTION fPrPrfEq(VAR prprf1, prprf2: TPrRec): TF;` | Compares print records prprf1 and prprf2 byte-for-byte and returns TRUE if they are equivalent. |
| `PrDocStart` | `Function PrDocStart(Var PrRec: TPrRec; Var PrPort: TPrPort; LDSN: INTEGER; DoSpoolAlert: Boolean): Boolean;` | Begins spooling a document using PrRec, opening QuickDraw printing port PrPort, allocating a private spool data segment at LDSN, optionally enabling the spooling alert (DoSpoolAlert), and returning TRUE if disk space and setup succeed. |
| `PrPageStart` | `FUNCTION PrPageStart(VAR prinsIn: TPrRec; VAR PrPort: TPrPort): TF;` | Begins a new document page on PrPort for print job prinsIn, opening a spooled QuickDraw picture and returning TRUE if the page falls within the requested page range and no abort occurred. |
| `PrPageEnd` | `FUNCTION PrPageEnd(VAR prinsIn: TPrRec; VAR PrPort: TPrPort): TF;` | Closes the current page's QuickDraw picture on PrPort, flushes full spool batches to disk for prinsIn, and returns TRUE once the last requested page has been reached or printing is aborted. |
| `PrDocEnd` | `PROCEDURE PrDocEnd(VAR prinsIn: TPrRec; VAR PrPort: TPrPort);` | Finalizes document spooling for prinsIn and PrPort, closing the spool file and data segment, notifying the background print supervisor of the final block, or cleaning up on abort. |
| `PrMgrInit` | `PROCEDURE PrMgrInit;` | Initializes the Print Manager and loads its alert phrase file for the calling application (after InitAlerts has been called). |
| `PrPrfDlg` | `PROCEDURE PrPrfDlg(VAR prprf: TPrRec; VAR fNewStl: TF; fPgSzSuppress: TF);` | Presents the 'Intended/Format for Printer...' setup dialog for print record prprf, setting fNewStl if printer formatting changed and honoring custom-page-size suppression fPgSzSuppress. |
| `FPrInsDlg` | `FUNCTION FPrInsDlg(VAR prprf: TPrRec; VAR fNewStl: TF; prmode: PrMenuSuppress): TF;` | Presents the 'Print...' job dialog for print record prprf with suppression mode prmode, setting fNewStl if formatting changed and returning TRUE if the user clicked OK. |
| `PrSpoolAbort` | `Procedure PrSpoolAbort;` | Sets the spooler abort flag to cancel the active print spooling loop as if the user had pressed Apple-Period. |
| `PrBgdDlg` | `PROCEDURE PrBgdDlg;` | Invokes the background print supervisor's 'Monitor the Printer' status dialog. |
| `PrDlgDefault` | `PROCEDURE PrDlgDefault(fPgSzSuppress: TF; Prmode: PrMenuSuppress; MaxHeight, MaxWidth, MinHeight, MinWidth: TC);` | Sets default dialog constraints for nested Print Manager dialogs, specifying custom-size suppression fPgSzSuppress, menu mode Prmode, and paper dimension limits (MaxHeight, MaxWidth, MinHeight, MinWidth). |
| `PrLFntID` | `PROCEDURE PrLFntID(VAR prprf: TPrRec; famIn: TC; setIn: Style; VAR lFntid: TLFntID);` | Builds a long font ID lFntid from print record prprf's output device, font family famIn, and face style setIn. |

---

## Unit PrSpool

Captures QuickDraw page drawing into disk-backed print spool files and submits spooled page blocks to the background print supervisor. Manages private spooling heap zones, disk-space reservation, spooling alerts, page-range filtering, and user abort handling.

- **Import**: `USES PrSpool;`
- **Unit kind**: `INTRINSIC` (`PRSPOOL`)
- **Interface dependencies**: `HWInt`, `SysCall`, `PMDecl`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `Events`, `Folders`, `Menus`, `Windows`, `WmlStd`, `WmlCrs`, `AlertMgr`, `PrStdInfo`, `PrStdProcs`, `PrFileProcs`, `Queues`, `PrEvents`, `PrDlgMgr`, `PrMgr`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `PrDocEnd` | `PROCEDURE PrDocEnd(Var PrRec: TPrRec; Var PrPort: TPrPort);` | Completes document spooling for PrRec and PrPort by flushing and closing any open spool file, releasing the spool data segment, raising a page-range note alert if no pages matched, and sending the final print request (or cleaning up if aborted). |
| `PrDocStart` | `Function PrDocStart(Var PrRec: TPrRec; Var PrPort: TPrPort; LDSN: INTEGER; DoSpoolAlert: Boolean): Boolean;` | Initializes document spooling for PrRec by creating the private data segment on LDSN, initializing the spool heap and QuickDraw capture port PrPort, creating the first spool file (showing the spooling alert when DoSpoolAlert is TRUE), and returning TRUE on success. |
| `PrPageEnd` | `Function PrPageEnd(Var PrRec: TPrRec; Var PrPort: TPrPort): Boolean;` | Finishes spooling the current page on PrPort for PrRec by closing and recording the QuickDraw picture length, submitting full 5-page spool files, yielding the CPU, and returning TRUE if the end of the requested page range or an abort is reached. |
| `PrPageStart` | `Function PrPageStart(Var PrRec: TPrRec; Var PrPort: TPrPort): Boolean;` | Advances the document page counter for PrRec and, if within the requested page range, reserves disk blocks and opens a streamed QuickDraw picture on PrPort (or hides the pen to skip out-of-range pages), returning TRUE when the page should be drawn. |
| `PrSpoolAbort` | `Procedure PrSpoolAbort;` | Sets the internal PrAbort flag to TRUE so subsequent spooling calls abort and clean up the active print job. |

---

## Unit PrStdProcs

Provides shared Print Manager utility, hardware port I/O, process scheduling, bitmap inspection, and 68000 block/bitwise helper routines used by printer drivers and spooler units.

- **Import**: `USES PrStdProcs;`
- **Unit kind**: `INTRINSIC` (`PRSTDPRO`)
- **Interface dependencies**: `SysCall`, `PMDecl`, `HWInt`, `UnitStd`, `UnitHz`, `Storage`, `QuickDraw`, `FontMgr`, `PrStdInfo`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `PsCopy` | `PROCEDURE PsCopy(Src, Dst: TL; len: TC);` | Copies len bytes of memory from linear source address Src to destination address Dst using MoveLeft. |
| `PsOpenPort` | `PROCEDURE PsOpenPort(Var Error: Integer; Port: Integer);` | Mounts, configures (disabling auto-LF and setting 9600-baud 8N1/DTR/timeout on RS-232 ports PortA or PortB), and opens hardware printer port Port, returning any OS error in Error. |
| `PsClosePort` | `PROCEDURE PsClosePort(Var Error: Integer; Port: Integer);` | Closes the active printer port object, re-enables break-on-close via DEVICE_CONTROL, and unmounts hardware port Port, returning any OS error in Error. |
| `PsInPort` | `PROCEDURE PsInPort(Var Error: Integer; p: TP; c: TC);` | Reads c sequential bytes from the open hardware printer port into buffer p, returning any OS error in Error. |
| `PsOutPort` | `PROCEDURE PsOutPort(Var Error: Integer; p: TP; c: TC);` | Writes c sequential bytes from buffer p to the open hardware printer port, returning any OS error in Error. |
| `PsPortName` | `PROCEDURE PsPortName(Port: Integer; shandle: THsp);` | Formats encoded hardware port identifier Port into a localized human-readable port description (such as slot/connector/device, parallel, or serial A/B) stored in string handle shandle. |
| `PsPortToDevName` | `PROCEDURE PsPortToDevName(Port: Integer; VAR DevName: e_name);` | Converts encoded hardware port number Port into a Lisa OS '#' device name string (such as '#10#1') in DevName. |
| `PsPreemptive` | `Procedure PsPreemptive;` | Restores the calling process to preemptive scheduling via Sched_Class(error, FALSE). |
| `PsNonPreemptive` | `Procedure PsNonPreemptive;` | Locks the calling process into non-preemptive scheduling via Sched_Class(error, TRUE). |
| `PsNumToStr` | `PROCEDURE PsNumToStr(c, w: TC; pstr: TpSp; z: CHAR);` | Converts non-negative integer c into a decimal string left-padded with character z to at least width w and appends it to pstr^. |
| `PsYieldCpu` | `PROCEDURE PsYieldCpu;` | Lowers the current process priority to 120, yields the CPU via YIELD_CPU, and restores the original priority. |
| `fClrBitmap` | `FUNCTION fClrBitmap(VAR bits: Bitmap; rCheck: Rect): TF;` | Intersects rCheck with bits.bounds and returns TRUE if all bytes within that bitmap rectangle are zero. |
| `InitDeBug` | `Procedure InitDeBug;` | Opens the '-Printer' debug output text file when PrDebug is enabled. |
| `PrAnd` | `FUNCTION PrAnd(c1, c2: TC): TC;` | Returns the 16-bit bitwise AND of integers c1 and c2. |
| `ClrBitmap` | `PROCEDURE ClrBitmap(pBitmap: TP);` | Zeros all scan-line words in the QuickDraw BitMap record pointed to by pBitmap. |
| `fClrBits` | `FUNCTION fClrBits(VAR bits: Bitmap; rCheck: Rect): TF;` | Scans the byte region of bitmap bits spanned by rCheck and returns TRUE if every tested byte is zero. |
| `fEQBlk` | `FUNCTION fEQBlk(a, b: TP; l: TL): TF;` | Compares l bytes at memory pointers a and b byte-for-byte and returns TRUE if the two blocks are identical. |
| `MoveBlk` | `PROCEDURE MoveBlk(a, b: TP; l: TL);` | Copies l bytes sequentially from source pointer a to destination pointer b. |
| `PrShRight` | `FUNCTION PrShRight(c1, n2: TC): TC;` | Performs a 16-bit unsigned logical right shift of c1 by n2 bits and returns the result. |
| `PrShLeft` | `FUNCTION PrShLeft(c1, n2: TC): TC;` | Performs a 16-bit logical left shift of c1 by n2 bits and returns the result. |
| `GetFileName` | `Procedure GetFileName(Var PrFileId: TPrFileId);` | Builds a spool file name of the form '[P<Id><BlockNum>]' in PrFileId.sFileName using 4-digit hexadecimal values of PrFileId.Id and PrFileId.BlockNum. |

---

## Unit Queues

Implements synchronized singly linked queues of heap handles with mutual-exclusion locking, insertion, removal, length queries, and callback-based enumeration.

- **Import**: `USES Queues;`
- **Unit kind**: `INTRINSIC` (`QUEUES`)
- **Interface dependencies**: `UnitStd`, `UnitHz`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `QueueFree` | `PROCEDURE QueueFree(Queue: hQueue);` | Releases the spin/in-use lock on queue header handle Queue. |
| `QueueInit` | `PROCEDURE QueueInit(Queue: hQueue);` | Initializes queue header handle Queue to empty (Head := NIL, Tail := Queue) and marks it not in use. |
| `QueueInUse` | `PROCEDURE QueueInUse(Queue: hQueue);` | Spins/waits until queue header handle Queue is free and marks it as in use for atomic manipulation. |
| `Enqueue` | `PROCEDURE Enqueue(Queue, Item: hQueue);` | Acquires Queue's lock and appends element handle Item to the tail of Queue. |
| `Dequeue` | `FUNCTION Dequeue(Queue: hQueue): hQueue;` | Acquires Queue's lock and removes and returns the first element handle from Queue (or NIL if the queue is empty). |
| `InsertBefore` | `FUNCTION InsertBefore(Queue, Successor, Item: hQueue): TF;` | Inserts Item immediately before Successor in Queue under lock and returns TRUE, or returns FALSE if Successor is not in Queue. |
| `InsertAfter` | `FUNCTION InsertAfter(Queue, Predecessor, Item: hQueue): TF;` | Inserts Item immediately after Predecessor in Queue under lock and returns TRUE, or returns FALSE if Predecessor is not in Queue. |
| `Unqueue` | `FUNCTION Unqueue(Queue, Item: hQueue): TF;` | Removes specific element handle Item from Queue under lock and returns TRUE, or returns FALSE if Item is not found. |
| `QueueLength` | `FUNCTION QueueLength(Queue: hQueue): TC;` | Counts and returns the number of elements currently linked in Queue under lock. |
| `QueuePeek` | `FUNCTION QueuePeek(Queue: hQueue): hQueue;` | Returns the head element handle of Queue without removing it (or NIL if empty). |
| `EnumerateQueue` | `FUNCTION EnumerateQueue(Queue: hQueue; FUNCTION FuncHandle(Queue: hQueue; arg: hQueue): BOOLEAN; arg: hQueue): hQueue;` | Iterates through Queue under lock, invoking FuncHandle(element, arg) on each element until FuncHandle returns FALSE (returning that stopping element) or the end is reached (returning NIL). |
