# `TK2LIB` (`TK2LIB.obj`) — Lisa Toolkit Dialog, Text & Universal Text Building Blocks

[Back to Library Index](LIBRARIES.md)

Higher-level Clascal Toolkit building blocks for modeless/modal dialog boxes and controls (`UDialog`), multi-font styled paragraph editing (`UText`), and Toolkit clipboard/stream text interchange (`UTKUniversalText`).

- **Object file**: `libs/workshop3.0/TK2LIB.obj` (Intrinsic library (interface stripped in `libs/workshop3.0/`))
- **Contents**: 3 units, 6 top-level procedures/functions, 53 Clascal classes (474 methods)

> [!NOTE]
> `libs/workshop3.0/TK2LIB.obj` in this repository is a link-only stub whose embedded `INTERFACE` text was stripped (`INTRINSIC.LIB` still indexes its units). The unit interfaces and signatures below were extracted from the unstripped Workshop 3.0 / Lisa Office System `TK2LIB.OBJ` build library.

## Importing and Linking

```pascal
USES UDialog, UText, UTKUniversalText;
```

```sh
pascal/lpc.py --link=IOSPASLIB,SYS1LIB,PRLIB,TKLIB,TK2LIB MYPROG
```

## Units in This Library

| Unit | 8-Char Symbol | `USES` Dependencies | Top-Level Routines | Clascal Classes (Methods) | Summary |
|---|---|---|---|---|---|
| [`UDialog`](#unit-udialog) | `UDIALOG` | `UObject`, `QuickDraw`, `UDraw`, `UABC`, `UTKUniversalText`, `UText` | 6 | 30 (277) | Provides the Lisa Toolkit Dialog Building Block (UDialog), implementing dialog windows, dialog views, interactive controls (buttons, checkboxes, radio clusters, text input frames, and legends), interactive dialog layout editing, and page header/margin design dialogs. |
| [`UText`](#unit-utext) | `UTEXT` | `UObject`, `QuickDraw`, `UDraw`, `UTKUniversalText`, `UABC` | 0 | 20 (181) | Provides the Lisa Toolkit Multiple-Paragraph Text Building Block (UText), implementing styled paragraph storage, word-wrapped line layout, linked multi-column text images, text selections and blinking insertion points, undoable editing/style commands, and clipboard Universal Text export. |
| [`UTKUniversalText`](#unit-utkuniversaltext) | `UTKUNIVE` | `UObject`, `UnitStd`, `UnitHz`, `QuickDraw`, `FontMgr`, `SysCall`, `PMDecl`, `PrStdInfo`, `UnitFmt`, `UnitCs`, `Events`, `Scrap` | 0 | 3 (16) | Provides the Lisa Toolkit Universal Text stream interface (UTKUniversalText) for reading and writing formatted character runs, paragraph margins, and tab descriptors to and from the Lisa system scrap. |

---

## Unit UDialog

Provides the Lisa Toolkit Dialog Building Block (UDialog), implementing dialog windows, dialog views, interactive controls (buttons, checkboxes, radio clusters, text input frames, and legends), interactive dialog layout editing, and page header/margin design dialogs.

- **Import**: `USES UDialog;`
- **Unit kind**: `INTRINSIC` (`UDIALOG`)
- **Interface dependencies**: `UObject`, `QuickDraw`, `UDraw`, `UABC`, `UTKUniversalText`, `UText`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `NewStdDialogWindow` | `FUNCTION NewStdDialogWindow(heap: THeap; itsHeight: INTEGER; itsKeyResponse, itsMenuResponse, itsDownInMainWindowResponse: TDiResponse): TDialogWindow;` | Allocates a standard non-resizable TDialogWindow of the specified height with a full-width control TPanel and an installed screen-resolution TDialogView. |
| `NewStdLegend` | `FUNCTION NewStdLegend(heap: THeap; itsChars: S255; itsXLoc, itsYLoc: LONGINT; itsView: TView; itsTypeStyle: TTypeStyle): TLegend;` | Creates and returns a TLegend displaying itsChars at (itsXLoc, itsYLoc) within itsView using the specified TTypeStyle. |
| `NewSysLegend` | `FUNCTION NewSysLegend(heap: THeap; itsChars: S255; itsXLoc, itsYLoc: LONGINT; itsView: TView): TLegend;` | Creates and returns a TLegend displaying itsChars at (itsXLoc, itsYLoc) within itsView rendered in the standard Lisa system font (sysTypeStyle). |
| `SetParaExtent` | `PROCEDURE SetParaExtent(paragraph: TParagraph; view: TView; location: LPoint; VAR extentLRect: LRect);` | Computes the view-coordinate bounding LRect for a TParagraph positioned at location in view, scaling from screen font metrics through the active printing or screen TPad. |
| `LRectAddBorders` | `PROCEDURE LRectAddBorders(baseLRect: LRect; borders: Rect; VAR resultLRect: LRect);` | Adds the signed left, top, right, and bottom offsets of borders to baseLRect and stores the expanded or inset rectangle in resultLRect. |
| `GetTextAndLocation` | `PROCEDURE GetTextAndLocation(phraseNumber: INTEGER; VAR itsChars: S255; VAR itsLocation: LPoint);` | Reads the alert phrase entry for phraseNumber and parses its '<text>@<h>,<v>' specification into caption string itsChars and view coordinate itsLocation. |

### Clascal Classes

#### `TDialogWindow = SUBCLASS OF TDialogBox`

Dialog box window subclass of TDialogBox that hosts a control TPanel, a TDialogView, and a main TDialog for modal or modeless user interaction.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsResizability: BOOLEAN; itsHeight: INTEGER; itsKeyResponse, itsMenuResponse, itsDownInMainWindowResponse: TDiResponse): TDialogWindow;` | Initializes a TDialogWindow with the given resizability, height, and TDiResponse policies for keyboard, menu, and main-window click events, defaulting controlPanel to selectPanel. |
| `Appear` | `PROCEDURE Appear; OVERRIDE;` | Displays the dialog window via SUPERSELF.Appear and notifies every TDialogImage in each panel's TDialogView via PrepareToAppear. |
| `BeDismissed` | `PROCEDURE BeDismissed; OVERRIDE;` | Dismisses the dialog window by pushing the default TButton of its controlPanel's TDialogView if one exists, or taking down the dialog box directly otherwise. |
| `CanDoCommand` | `FUNCTION CanDoCommand(cmdNumber: TCmdNumber; VAR checkIt: BOOLEAN): BOOLEAN; OVERRIDE;` | Enables the interactive dialog-editing command (uEditDialog) and delegates all other command inquiries to currentWindow.CanDoCommand. |
| `Disappear` | `PROCEDURE Disappear; OVERRIDE;` | Hides the dialog window via SUPERSELF.Disappear and clears the isShowing flag on its controlPanel's TDialogView. |
| `NewCommand` | `FUNCTION NewCommand(cmdNumber: TCmdNumber): TCommand; OVERRIDE;` | Launches a TDialogDesignWindow to seize interactive layout control when uEditDialog is chosen, or delegates other command numbers to currentWindow. |

#### `TDialogView = SUBCLASS OF TView`

View subclass of TView that manages a hierarchy of TDialog objects under a root dialog, dispatches mouse events to controls, and delegates non-dialog drawing and tracking to X-prefixed hook methods.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsExtentLRect: LRect; itsPanel: TPanel; itsPrintManager: TPrintManager; itsRes: Point): TDialogView;` | Initializes a TDialogView in itsPanel with itsExtentLRect, creates an empty master 'ROOT' TDialog and default TStyleSheet, and resets button and mouse-tracking state. |
| `Free` | `PROCEDURE Free; OVERRIDE;` | Frees the view's rootDialog hierarchy and styleSheet before freeing the TDialogView itself. |
| `AddDialog` | `PROCEDURE AddDialog(dialog: TDialog);` | Appends dialog as a child of rootDialog and records it as mainDialog on the enclosing TDialogWindow if none is set yet. |
| `AddNewDialog` | `FUNCTION AddNewDialog(itsKey: S4): TDialog;` | Creates a new TDialog with the 4-character resource key itsKey, installs it into this TDialogView via AddDialog, and returns it. |
| `ActivateDialog` | `PROCEDURE ActivateDialog(dialog: TDialog; whichWay: BOOLEAN);` | Activates or deactivates dialog within rootDialog according to whichWay and invalidates its screen extent when its active state changes. |
| `RemoveDialog` | `PROCEDURE RemoveDialog(dialog: TDialog; andFree: BOOLEAN);` | Removes dialog from rootDialog's children, invalidating its extent if visible and freeing the dialog object when andFree is TRUE. |
| `ReplaceDialog` | `PROCEDURE ReplaceDialog(oldDialog, newDialog: TDialog);` | Deletes and frees oldDialog from rootDialog and adds newDialog in its place. |
| `XCursorAt` | `FUNCTION XCursorAt(mouseLPt: LPoint): TCursorNumber; DEFAULT;` | Provides the default non-dialog cursor hook for subclasses, returning arrowCursor when no active dialog image claims mouseLPt. |
| `XDraw` | `PROCEDURE XDraw; DEFAULT;` | Provides a default no-op drawing hook for subclasses to render non-dialog content after rootDialog has been drawn. |
| `XMousePress` | `PROCEDURE XMousePress(mouseLPt: LPoint); DEFAULT;` | Provides a default no-op mouse-down hook for subclasses when a press at mouseLPt does not hit any active TDialogImage. |
| `XMouseMove` | `PROCEDURE XMouseMove(mouseLPt: LPoint); DEFAULT;` | Provides a default no-op mouse-drag hook for subclasses when pointer movement at mouseLPt is not claimed by any TDialogImage. |
| `XMouseRelease` | `PROCEDURE XMouseRelease; DEFAULT;` | Provides a default no-op mouse-up hook for subclasses when the mouse button is released without an active currentDialogImage. |
| `AbandonThatButton` | `PROCEDURE AbandonThatButton;` | Unhighlights hitButton across all pads of the panel and clears hitButton (and currentDialogImage if it matches hitButton). |
| `ButtonPushed` | `PROCEDURE ButtonPushed(button: TButton);` | Handles default button-push completion for a dialog box by pausing briefly, unhighlighting hitButton, dismissing the dialog box if appropriate, and dispatching button.cmdNumber. |
| `CheckboxHit` | `PROCEDURE CheckboxHit(checkbox: TCheckbox; toggleDirection: BOOLEAN);` | Provides an overrideable notification hook invoked when a TCheckbox in the view is toggled in toggleDirection. |
| `PushButton` | `PROCEDURE PushButton(button: TButton);` | Programmatically pushes button by delegating to the PushButton method of its parent TDialog. |
| `SetDefaultButton` | `PROCEDURE SetDefaultButton(button: TButton);` | Designates button as the view's defaultButton and sets its border pen size to a heavy (3, 2) outline. |
| `CursorAt` | `FUNCTION CursorAt(mouseLPt: LPoint): TCursorNumber; OVERRIDE;` | Returns magnetCursor while the mouse is held down, or queries rootDialog.CursorAt and falls back to XCursorAt. |
| `Draw` | `PROCEDURE Draw; OVERRIDE;` | Marks isShowing TRUE, draws all active dialogs under rootDialog, and calls XDraw to render any non-dialog view graphics. |
| `EachActualPart` | `PROCEDURE EachActualPart(PROCEDURE DoToObject(filteredObj: TObject)); OVERRIDE;` | Iterates over every constituent child image of rootDialog by passing DoToObject to rootDialog.EachActualPart. |
| `MouseMove` | `PROCEDURE MouseMove(mouseLPt: LPoint); OVERRIDE;` | Verifies whether currentDialogImage retains mouseLPt via StillMyMouse, otherwise probes rootDialog.DownAt or delegates to XMouseMove. |
| `MousePress` | `PROCEDURE MousePress(mouseLPt: LPoint); OVERRIDE;` | Initiates mouse tracking in the dialog view, routing mouseLPt to an active selection, a hit TDialogImage in rootDialog, or XMousePress. |
| `MouseRelease` | `PROCEDURE MouseRelease; OVERRIDE;` | Clears mouseIsDown and magnetCursor and dispatches the release event to currentDialogImage.MouseRelease or XMouseRelease. |
| `RecalcExtent` | `PROCEDURE RecalcExtent; OVERRIDE;` | Recomputes the view's overall extent as the union of rootDialog.extentLRect and nonDialogExtent, resizing the view accordingly. |

#### `TDialogImage = SUBCLASS OF TImage`

Abstract base TImage subclass for visual elements in a TDialogView, tracking parent linkage, active and editable state, hit-testing, and layout-box creation.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsExtent: LRect; itsId: S255; itsView: TView; withChildren: BOOLEAN): TDialogImage;` | Initializes a TDialogImage in itsView with itsExtent, setting parent to NIL, isActive and isEditable to TRUE, and withID to FALSE. |
| `ControlHit` | `PROCEDURE ControlHit(control: TDialogImage; toggleDirection: BOOLEAN); DEFAULT;` | Propagates a control activation or toggle notification upward to parent.ControlHit if parent is non-NIL. |
| `DownAt` | `FUNCTION DownAt(mouseLPt: LPoint): TDialogImage; DEFAULT;` | Tests Hit(mouseLPt) and, if hit, invokes SELF.MousePress(mouseLPt) and returns SELF, or returns NIL otherwise. |
| `Draw` | `PROCEDURE Draw; OVERRIDE;` | Renders the dialog image by calling SELF.DrawJustMe. |
| `DrawJustMe` | `PROCEDURE DrawJustMe; DEFAULT;` | Provides a default no-op self-drawing hook called after any child dialog images have been drawn. |
| `LaunchLayoutBox` | `FUNCTION LaunchLayoutBox(view: TView): TImage; OVERRIDE;` | Creates and returns a plain non-resizable TLayoutBox wrapping SELF for interactive layout in view when isActive is TRUE, or NIL if inactive. |
| `PrepareToAppear` | `PROCEDURE PrepareToAppear;` | Provides a default hook invoked on every dialog image in a TDialogWindow just as the window appears on screen. |
| `RecalcExtent` | `PROCEDURE RecalcExtent; OVERRIDE;` | Notifies parent.RecalcExtent when this dialog image's bounding rectangle changes. |
| `StillMyMouse` | `FUNCTION StillMyMouse(mouseLPt: LPoint): BOOLEAN; DEFAULT;` | Returns TRUE if mouseLPt still hits this dialog image during a drag, or FALSE to relinquish mouse tracking. |
| `AddImage` | `PROCEDURE AddImage(dialogImage: TDialogImage); DEFAULT;` | Provides a default no-op stub for adding a child TDialogImage, overridden by composite TImageWithID subclasses. |
| `ActivateImage` | `PROCEDURE ActivateImage(dialogImage: TDialogImage; whichWay: BOOLEAN); DEFAULT;` | Sets dialogImage.isActive to whichWay and invalidates its extent rectangle in the panel if its state changed. |
| `BringToFront` | `PROCEDURE BringToFront(dialogImage: TDialogImage); DEFAULT;` | Provides a default no-op stub for moving a child TDialogImage to the front of the drawing order, overridden in TImageWithID. |
| `ComeForward` | `PROCEDURE ComeForward; DEFAULT;` | Brings this dialog image to the front of its parent container by calling parent.BringToFront(SELF). |
| `DeleteImage` | `PROCEDURE DeleteImage(dialogImage: TDialogImage; andFree: BOOLEAN); DEFAULT;` | Provides a default no-op stub for removing a child TDialogImage, overridden in TImageWithID. |
| `EachActualPart` | `PROCEDURE EachActualPart(PROCEDURE DoToObject(filteredObj: TObject)); OVERRIDE;` | Overrides TImage.EachActualPart as a no-op for leaf dialog images without children. |
| `HasId` | `FUNCTION HasId(id: S255): BOOLEAN; DEFAULT;` | Returns FALSE by default for anonymous TDialogImage instances, overridden in TImageWithID. |
| `ObjectWithIDNumber` | `FUNCTION ObjectWithIDNumber(idNumber: INTEGER): TDialogImage; DEFAULT;` | Returns NIL by default for leaf TDialogImage instances without numbered children, overridden in TImageWithID. |
| `ObjWithId` | `FUNCTION ObjWithId(id: S255): TDialogImage; DEFAULT;` | Returns NIL by default for leaf TDialogImage instances without named children, overridden in TImageWithID. |
| `ReplaceImage` | `PROCEDURE ReplaceImage(replacee, newValue: TDialogImage); DEFAULT;` | Provides a default no-op stub for replacing a child TDialogImage, overridden in TImageWithID. |

#### `TImageWithID = SUBCLASS OF TDialogImage`

Composite TDialogImage subclass that maintains an uppercase string identifier, an integer ID number, and a TList of child TDialogImage components.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsExtent: LRect; itsId: S255; itsView: TView; withChildren: BOOLEAN): TImageWithID;` | Initializes a TImageWithID with an uppercased string ID, a parsed numeric idNumber (or noIDNumber), and an optional TList of child TDialogImage objects. |
| `Clone` | `FUNCTION Clone(heap: THeap): TObject; OVERRIDE;` | Clones this TImageWithID on heap, including a deep clone of its children TList if present. |
| `Free` | `PROCEDURE Free; OVERRIDE;` | Frees the children TList and all child dialog images before freeing this TImageWithID. |
| `AddImage` | `PROCEDURE AddImage(dialogImage: TDialogImage); OVERRIDE;` | Appends dialogImage to children, sets its parent and view, expands SELF.extentLRect by dialogImage.extentLRect, and notifies parent.RecalcExtent. |
| `ActivateImage` | `PROCEDURE ActivateImage(dialogImage: TDialogImage; whichWay: BOOLEAN); OVERRIDE;` | Updates dialogImage.isActive to whichWay and invalidates dialogImage.extentLRect in the panel when the state changes. |
| `BringToFront` | `PROCEDURE BringToFront(dialogImage: TDialogImage); OVERRIDE;` | Moves dialogImage to the end of children so it draws on top and recursively brings SELF to the front of its parent. |
| `CursorAt` | `FUNCTION CursorAt(mouseLPt: LPoint): TCursorNumber; OVERRIDE;` | Scans active children when mouseLPt lies within extentLRect and returns the first non-noCursor TCursorNumber reported. |
| `DeleteImage` | `PROCEDURE DeleteImage(dialogImage: TDialogImage; andFree: BOOLEAN); OVERRIDE;` | Removes dialogImage from children, invalidating its screen extent if currently showing and freeing it when andFree is TRUE. |
| `Draw` | `PROCEDURE Draw; OVERRIDE;` | Draws all active child dialog images and then calls DrawJustMe when extentLRect is visible in the current GrafPort. |
| `EachActualPart` | `PROCEDURE EachActualPart(PROCEDURE DoToObject(filteredObj: TObject)); OVERRIDE;` | Applies DoToObject to each child TDialogImage in SELF.children if the list is non-NIL. |
| `EachVirtualPart` | `PROCEDURE EachVirtualPart(PROCEDURE DoToObject(filteredObj: TObject)); OVERRIDE;` | Enumerates virtual parts by delegating DoToObject to EachActualPart. |
| `HasId` | `FUNCTION HasId(id: S255): BOOLEAN; OVERRIDE;` | Returns TRUE if this image's stored ID matches id after truncating to IDLength and converting to uppercase. |
| `HaveView` | `PROCEDURE HaveView(view: TView); OVERRIDE;` | Assigns view to SELF.view and recursively propagates HaveView(view) to every child dialog image. |
| `LaunchLayoutBox` | `FUNCTION LaunchLayoutBox(view: TView): TImage; OVERRIDE;` | Creates a composite TLayoutBox (with an ID title tab and child layout boxes) representing this TImageWithID in a TPlannerView, or returns NIL if inactive. |
| `ObjectWithIDNumber` | `FUNCTION ObjectWithIDNumber(idNumber: INTEGER): TDialogImage; OVERRIDE;` | Searches children (and recursively their descendants) for an image with withID TRUE whose idNumber equals idNumber, returning it or NIL. |
| `ObjWithId` | `FUNCTION ObjWithId(id: S255): TDialogImage; OVERRIDE;` | Searches children for a TImageWithID matching the uppercased string id, returning the matching TDialogImage or NIL. |
| `OffSetBy` | `PROCEDURE OffSetBy(deltaLPt: LPoint); OVERRIDE;` | Offsets SELF.extentLRect by deltaLPt and recursively offsets all child dialog images by the same delta. |
| `RecalcExtent` | `PROCEDURE RecalcExtent; OVERRIDE;` | Recomputes extentLRect as the union of all child dialog image extents, resizes SELF, and propagates RecalcExtent to parent. |
| `ReplaceImage` | `PROCEDURE ReplaceImage(replacee, newValue: TDialogImage); OVERRIDE;` | Replaces child dialog image replacee by deleting and freeing it and appending newValue via AddImage. |
| `StillMyMouse` | `FUNCTION StillMyMouse(mouseLPt: LPoint): BOOLEAN; OVERRIDE;` | Returns TRUE if mouseLPt still hits this TImageWithID, or FALSE to release mouse ownership. |

#### `TDialog = SUBCLASS OF TImageWithID`

Container TImageWithID identified by a 4-character resource key that groups controls in a TDialogView, constructs standard controls from phrase-file entries, and handles button and checkbox notifications.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsKey: S4; itsView: TView): TDialog;` | Initializes a TDialog with 4-character identifier itsKey in itsView and resets global stdButtonMetrics to standard Lisa button dimensions. |
| `NewButton` | `FUNCTION NewButton(itsPhrase: INTEGER; itsMetrics: TButtonMetrics; sameSizedButton: TButton; itsCmdNumber: TCmdNumber): TButton;` | Creates, installs, and returns a TButton whose caption, location, and idNumber are read from phrase-file entry itsPhrase, linked in width to sameSizedButton. |
| `NewCluster` | `FUNCTION NewCluster(itsPhrase: INTEGER): TCluster;` | Creates, installs, and returns an empty TCluster whose ID, initial alignment location, and idNumber come from phrase-file entry itsPhrase. |
| `NewFreeCheckbox` | `FUNCTION NewFreeCheckbox(itsPhrase: INTEGER; boxWidth: INTEGER; boxHeight: INTEGER; wantLabel: BOOLEAN; labelOffset: Point; itsTypeStyle: TTypeStyle): TCheckBox;` | Creates, installs, and returns a standalone TCheckbox whose label, location, and idNumber come from phrase-file entry itsPhrase. |
| `NewInputFrame` | `FUNCTION NewInputFrame(itsPhrase: INTEGER; promptTypeStyle: TTypeStyle; inputOffset: Point; inputTypeStyle: TTypeStyle; maxInputChars: INTEGER; itsBorders: Rect; drawInputLRect: BOOLEAN; drawHitLRect: BOOLEAN): TInputFrame;` | Creates, installs, and returns a TInputFrame whose prompt text and location come from itsPhrase, placing the editable input area at inputOffset from the prompt. |
| `NewLegend` | `FUNCTION NewLegend(itsPhrase: INTEGER; itsTypeStyle: TTypeStyle): TLegend;` | Creates, installs, and returns a TLegend whose text and baseline coordinates come from phrase-file entry itsPhrase rendered in itsTypeStyle. |
| `NewRowOfBoxes` | `FUNCTION NewRowOfBoxes(itsPhrase: INTEGER; numberOfBoxes: INTEGER; startingIDNumber: INTEGER; boxWidth: INTEGER; boxHeight: INTEGER; boxSpacing: INTEGER): TCluster;` | Creates, installs, and returns a horizontal TCluster of numberOfBoxes unlabeled checkboxes starting at the location from phrase-file entry itsPhrase. |
| `ButtonPushed` | `PROCEDURE ButtonPushed(button: TButton); DEFAULT;` | Handles a pushed TButton by forwarding the notification to the parent TDialog if nested, or to the owning TDialogView.ButtonPushed by default. |
| `CheckboxHit` | `PROCEDURE CheckboxHit(checkbox: TCheckbox; toggleDirection: BOOLEAN); DEFAULT;` | Handles a toggled TCheckbox by forwarding the notification to any parent TDialog/TDialogImage or to TDialogView.CheckboxHit by default. |
| `ControlHit` | `PROCEDURE ControlHit(control: TDialogImage; toggleDirection: BOOLEAN); OVERRIDE;` | Dispatches a control hit notification to ButtonPushed when control is a TButton or to CheckboxHit when control is a TCheckbox. |
| `PushButton` | `PROCEDURE PushButton(button: TButton);` | Highlights button on all panel pads if not already highlighted, records it as the view's hitButton, and invokes SELF.ButtonPushed(button). |
| `SelectInputFrame` | `PROCEDURE SelectInputFrame(inputFrame: TInputFrame);` | Selects inputFrame in the panel by installing a TFrameSelection whose coSelection highlights all characters in the frame's TTextImage. |
| `SetDefaultButton` | `PROCEDURE SetDefaultButton(button: TButton);` | Delegates default-button assignment upward to any parent TDialog or to the owning TDialogView.SetDefaultButton. |
| `AddStdButton` | `FUNCTION AddStdButton(itsId: S255; itsXLoc, itsYLoc: LONGINT; sameSizedButton: TButton; itsCmdNumber: TCmdNumber): TButton;` | Creates and installs a TButton with caption itsId at (itsXLoc, itsYLoc) using stdButtonMetrics, width-linked to sameSizedButton. |
| `AddOKButton` | `PROCEDURE AddOKButton(cmdNumber: TCmdNumber);` | Creates and installs a standard 'OK' TButton from phrase phOK associated with cmdNumber and sized to match any Cancel button. |
| `AddCancelButton` | `PROCEDURE AddCancelButton(cmdNumber: TCmdNumber);` | Creates and installs a standard 'Cancel' TButton from phrase phCancel associated with cmdNumber and sized to match any OK button. |
| `AddStdCluster` | `FUNCTION AddStdCluster(itsId: S255; itsXLoc, itsYLoc: LONGINT): TCluster;` | Creates, installs, and returns an empty TCluster with identifier itsId anchored at (itsXLoc, itsYLoc). |
| `AddStdFreeCheckbox` | `FUNCTION AddStdFreeCheckbox(itsId: S255; itsXLoc, itsYLoc: LONGINT): TCheckBox;` | Creates, installs, and returns a standalone TCheckbox with standard box dimensions, sysTypeStyle label itsId, and location (itsXLoc, itsYLoc). |
| `AddStdInputFrame` | `FUNCTION AddStdInputFrame(itsId: S255; itsXLoc: LONGINT; itsYLoc: LONGINT; maxInputChars: INTEGER): TInputFrame;` | Creates, installs, and returns a standard TInputFrame at (itsXLoc, itsYLoc) with sysTypeStyle prompt itsId and space for maxInputChars characters. |
| `AddStdLegend` | `FUNCTION AddStdLegend(itsId: S255; itsXLoc, itsYLoc: LONGINT; itsTypeStyle: TTypeStyle): TLegend;` | Creates, installs, and returns a TLegend displaying itsId at (itsXLoc, itsYLoc) in itsTypeStyle. |
| `AddSysLegend` | `FUNCTION AddSysLegend(itsId: S255; itsXLoc, itsYLoc: LONGINT): TLegend;` | Creates, installs, and returns a TLegend displaying itsId at (itsXLoc, itsYLoc) in the standard system font (sysTypeStyle). |
| `AddButton` | `FUNCTION AddButton(itsId: S255; itsLocation: LPoint; itsMetrics: TButtonMetrics; sameSizedButton: TButton; itsCmdNumber: TCmdNumber): TButton;` | Creates a TButton with explicit caption itsId, location, metrics, width-sharing peer sameSizedButton, and command number, and adds it to this dialog. |
| `AddFreeCheckbox` | `FUNCTION AddFreeCheckbox(itsID: S255; itsXLoc, itsYLoc: LONGINT; boxWidth: INTEGER; boxHeight: INTEGER; wantLabel: BOOLEAN; labelOffset: Point; itsTypeStyle: TTypeStyle): TCheckbox;` | Creates a standalone TCheckbox with explicit label itsID, coordinates, box dimensions, label offset, and typestyle, and adds it to this dialog. |
| `AddBigFreeCheckbox` | `FUNCTION AddBigFreeCheckbox(itsId: S255; itsXLoc, itsYLoc: LONGINT): TCheckbox;` | Creates and installs a large 36x24-pixel TCheckbox with an 18-point Classic label itsId at (itsXLoc, itsYLoc). |
| `AddRowOfBoxes` | `FUNCTION AddRowOfBoxes(itsID: S255; itsXLoc, itsYLoc: LONGINT; numberOfBoxes: INTEGER; startingIDNumber: INTEGER; boxWidth: INTEGER; boxHeight: INTEGER; boxSpacing: INTEGER): TCluster;` | Creates and installs a TCluster at (itsXLoc, itsYLoc) populated with numberOfBoxes horizontally spaced checkboxes numbered from startingIDNumber. |
| `AddInputFrame` | `FUNCTION AddInputFrame(itsId: S255; promptLocation: LPoint; promptTypeStyle: TTypeStyle; inputLocation: LPoint; inputTypeStyle: TTypeStyle; maxInputChars: INTEGER; itsBorders: Rect; drawInputLRect: BOOLEAN; drawHitLRect: BOOLEAN): TInputFrame;` | Creates a TInputFrame with explicit prompt and input locations, typestyles, character limit, border insets, and framing flags, and adds it to this dialog. |
| `DownAt` | `FUNCTION DownAt(mouseLPt: LPoint): TDialogImage; OVERRIDE;` | Scans active child dialog images when mouseLPt hits this dialog's extent and returns the first child claiming the mouse press via DownAt. |
| `RecalcExtent` | `PROCEDURE RecalcExtent; OVERRIDE;` | Recomputes this dialog's bounding rectangle from its children and triggers SELF.view.RecalcExtent when this is the top-level root dialog. |

#### `TButton = SUBCLASS OF TImageWithID`

Push-button control subclass of TImageWithID that draws a rounded-rectangle frame around a centered TLegend, highlights on mouse press, and triggers a command or dialog callback on release.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsId: S255; itsView: TView; itsLocation: LPoint; itsMetrics: TButtonMetrics; sameSizedButton: TButton; itsCmdNumber: TCmdNumber): TButton;` | Initializes a TButton at itsLocation with caption legend itsId, metrics itsMetrics, command number itsCmdNumber, and optional circular width-sharing link sameSizedButton. |
| `DrawJustMe` | `PROCEDURE DrawJustMe; OVERRIDE;` | Draws the button's rounded-rectangle frame using buttonMetrics.penState and inverts its interior if isHighlighted is TRUE. |
| `Highlight` | `PROCEDURE Highlight(highTransit: THighTransit);` | Inverts the button's rounded-rectangle interior and updates isHighlighted according to whether highTransit is hOffToOn. |
| `LaunchLayoutBox` | `FUNCTION LaunchLayoutBox(view: TView): TImage; OVERRIDE;` | Creates and returns a TButtonLayoutBox for dragging or editing this button inside a TPlannerView. |
| `MousePress` | `PROCEDURE MousePress(mouseLPt: LPoint); OVERRIDE;` | Highlights the button across all pads of its panel when pressed by the mouse. |
| `MouseRelease` | `PROCEDURE MouseRelease; OVERRIDE;` | Completes a button click on mouse release by calling PushButton(SELF) on the parent TDialog. |
| `RecalcExtent` | `PROCEDURE RecalcExtent; OVERRIDE;` | Recalculates the required width across this button and any linked nextSameSizedButton peers after a caption edit and updates their extents. |
| `Recompute` | `PROCEDURE Recompute(minWidth: INTEGER);` | Computes the button's rounded-rectangle LRect from its legend width, expansion ratio, and minWidth, centering the legend inside the button. |
| `StillMyMouse` | `FUNCTION StillMyMouse(mouseLPt: LPoint): BOOLEAN; OVERRIDE;` | Returns TRUE while mouseLPt remains inside the button, or unhighlights the button on all pads and returns FALSE when the pointer drags outside. |

#### `TCheckbox = SUBCLASS OF TImageWithID`

Toggleable checkbox control subclass of TImageWithID composed of a square TRectImage indicator box and an optional TLegend caption.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsId: S255; itsView: TView; itsLocation: LPoint; boxWidth: INTEGER; boxHeight: INTEGER; wantLabel: BOOLEAN; labelOffset: Point; itsTypeStyle: TTypeStyle): TCheckbox;` | Initializes a TCheckbox at itsLocation with a boxWidth-by-boxHeight TRectImage and an optional TLegend label offset by labelOffset. |
| `ChangeLabel` | `PROCEDURE ChangeLabel(newS255: S255);` | Updates the checkbox's TLegend text to newS255 and recalculates the checkbox's bounding extent. |
| `CursorAt` | `FUNCTION CursorAt(mouseLPt: LPoint): TCursorNumber; OVERRIDE;` | Returns checkCursor when mouseLPt hits the checkbox or noCursor otherwise. |
| `Draw` | `PROCEDURE Draw; OVERRIDE;` | Fills the checkbox's square indicator with black when selected or white when unselected, frames the box, and draws any attached TLegend. |
| `LaunchLayoutBox` | `FUNCTION LaunchLayoutBox(view: TView): TImage; OVERRIDE;` | Creates a composite TLayoutBox for this checkbox in a TPlannerView, using TImageWithID layout if labeled or wrapping just rectImage if unlabeled. |
| `MousePress` | `PROCEDURE MousePress(mouseLPt: LPoint); OVERRIDE;` | Toggles a standalone free checkbox on mouse press (respecting single-sense drag painting when paintFreeBoxes is enabled), redraws it, and calls ControlHit. |
| `Toggle` | `PROCEDURE Toggle;` | Inverts the boolean isSelected state of the checkbox without redrawing. |

#### `TCluster = SUBCLASS OF TImageWithID`

Radio-button group subclass of TImageWithID that manages a collection of TCheckbox children in which at most one checkbox is selected and highlighted at a time.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsId: S255; itsView: TView; itsLocation: LPoint): TCluster;` | Initializes an empty radio-button TCluster with identifier itsId and anchor coordinate itsLocation in itsView. |
| `NewAlignedCheckbox` | `FUNCTION NewAlignedCheckbox(itsPhrase: INTEGER; selectThisOne: BOOLEAN): TCheckbox;` | Creates and appends a vertically aligned TCheckbox from phrase-file entry itsPhrase, selecting it if selectThisOne is TRUE. |
| `NewCheckbox` | `FUNCTION NewCheckbox(itsPhrase: INTEGER; boxWidth: INTEGER; boxHeight: INTEGER; wantLabel: BOOLEAN; labelOffset: Point; itsTypeStyle: TTypeStyle; selectThisOne: BOOLEAN): TCheckbox;` | Creates and appends a TCheckbox whose label and location come from phrase-file entry itsPhrase with custom box dimensions and typestyle. |
| `AddRowOfBoxes` | `PROCEDURE AddRowOfBoxes(numberOfBoxes: INTEGER; startingIDNumber: INTEGER; boxWidth: INTEGER; boxHeight: INTEGER; boxSpacing: INTEGER);` | Appends a horizontal row of numberOfBoxes unlabeled checkboxes spaced by boxSpacing pixels with sequential ID numbers starting at startingIDNumber. |
| `SelectBox` | `PROCEDURE SelectBox(checkbox: TCheckbox);` | Deselects and redraws the previously selected hiLitBox if different, selects and redraws checkbox on all pads, and sends ControlHit notifications. |
| `AddAlignedCheckbox` | `FUNCTION AddAlignedCheckbox(itsId: S255; selectThisOne: BOOLEAN): TCheckbox;` | Creates and appends a standard checkbox labeled itsId aligned vertically below lastBox (or at the cluster's origin for the first box). |
| `AddCheckbox` | `FUNCTION AddCheckbox(itsID: S255; itsLocation: LPoint; boxWidth: INTEGER; boxHeight: INTEGER; wantLabel: BOOLEAN; labelOffset: Point; itsTypeStyle: TTypeStyle; selectThisOne: BOOLEAN): TCheckbox;` | Creates a TCheckbox at itsLocation with the specified dimensions and style, adds it to the cluster, and marks it selected if selectThisOne is TRUE. |
| `Hit` | `FUNCTION Hit(mouseLPt: LPoint): BOOLEAN; OVERRIDE;` | Tests whether mouseLPt hits any child TCheckbox in the cluster, recording the hit checkbox in SELF.hitBox and returning TRUE if found. |
| `MousePress` | `PROCEDURE MousePress(mouseLPt: LPoint); OVERRIDE;` | Selects SELF.hitBox (established by the preceding Hit test) and deselects any other checkbox in the cluster. |
| `StillMyMouse` | `FUNCTION StillMyMouse(mouseLPt: LPoint): BOOLEAN; OVERRIDE;` | Switches the cluster selection to whichever child checkbox mouseLPt currently hits during a drag, returning FALSE if outside all checkboxes. |

#### `TInputFrame = SUBCLASS OF TImageWithID`

Single-line text entry control subclass of TImageWithID pairing a prompt TLegend with an editable TTextDialogImage bounded by a maximum character count.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsId: S255; itsView: TView; promptLocation: LPoint; promptTypeStyle: TTypeStyle; inputLocation: LPoint; inputTypeStyle: TTypeStyle; maxInputChars: INTEGER; itsBorders: Rect; drawInputLRect: BOOLEAN; drawHitLRect: BOOLEAN): TInputFrame;` | Initializes a TInputFrame combining a prompt TLegend at promptLocation with an editable TTextDialogImage at inputLocation sized for maxInputChars. |
| `GetContents` | `PROCEDURE GetContents(VAR theStr: S255);` | Extracts the current text of the input frame's first paragraph into Pascal string theStr. |
| `SupplantContents` | `PROCEDURE SupplantContents(newStr: S255);` | Replaces the input frame's paragraph text with newStr, recomputes its TTextImage layout, and invalidates or updates the display. |
| `CursorAt` | `FUNCTION CursorAt(mouseLPt: LPoint): TCursorNumber; OVERRIDE;` | Returns the I-beam textCursor when mouseLPt lies within the input frame's hit area, or noCursor otherwise. |
| `Draw` | `PROCEDURE Draw; OVERRIDE;` | Draws the prompt legend, the editable TTextDialogImage, and optional gray input-box or hit-area border frames. |
| `LaunchLayoutBox` | `FUNCTION LaunchLayoutBox(view: TView): TImage; OVERRIDE;` | Creates a TLayoutBox for repositioning the input frame and its subparts in a TPlannerView, adjusting border offsets to match SELF.borders. |
| `MousePress` | `PROCEDURE MousePress(mouseLPt: LPoint); OVERRIDE;` | Clamps mouseLPt to the text area, locks magnetCursor to textCursor, installs a TFrameSelection on the panel, and forwards MousePress to the TTextImage. |
| `RecalcExtent` | `PROCEDURE RecalcExtent; OVERRIDE;` | Recomputes the input frame's extent as the union of its prompt and textDialogImage plus borders, resizes SELF, and notifies parent.RecalcExtent. |
| `StillMyMouse` | `FUNCTION StillMyMouse(mouseLPt: LPoint): BOOLEAN; OVERRIDE;` | Clamps mouseLPt to the editable text rectangle, forwards MouseMove to the panel's text coSelection, and returns TRUE to retain drag tracking. |

#### `TLegend = SUBCLASS OF TDialogImage`

Static or layout-editable text label subclass of TDialogImage backed by a styled TParagraph positioned at a baseline LPoint.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsChars: S255; itsView: TView; itsLocation: LPoint; itsTypeStyle: TTypeStyle): TLegend;` | Initializes a TLegend in itsView at baseline itsLocation containing a TParagraph populated with itsChars in itsTypeStyle. |
| `Free` | `PROCEDURE Free; OVERRIDE;` | Frees the underlying TParagraph and then frees the TLegend object. |
| `ChangeToPhrase` | `PROCEDURE ChangeToPhrase(newPhrase: INTEGER);` | Replaces the legend's text with the alert string for newPhrase and invalidates both the old and new bounding rectangles. |
| `ChangeString` | `PROCEDURE ChangeString(newString: S255);` | Replaces the legend's TParagraph characters with newString, updates its extent via GetBoxRight, and invalidates old and new screen bounds. |
| `GetString` | `PROCEDURE GetString(VAR itsString: S255);` | Copies the characters currently stored in the legend's TParagraph into Pascal string itsString. |
| `Draw` | `PROCEDURE Draw; OVERRIDE;` | Moves the QuickDraw pen to SELF.location and draws all characters of SELF.paragraph. |
| `GetBoxRight` | `PROCEDURE GetBoxRight;` | Computes the view-coordinate bounding LRect of SELF.paragraph at SELF.location via SetParaExtent and resizes the legend to match. |
| `LaunchLayoutBox` | `FUNCTION LaunchLayoutBox(view: TView): TImage; OVERRIDE;` | Creates and returns an editable TLegendLayoutBox when isEditable is TRUE, or delegates to TDialogImage.LaunchLayoutBox otherwise. |
| `OffsetBy` | `PROCEDURE OffsetBy(deltaLPt: LPoint); OVERRIDE;` | Adds deltaLPt to SELF.location and offsets the legend's extentLRect by the same vector. |
| `RecalcExtent` | `PROCEDURE RecalcExtent; OVERRIDE;` | Updates the legend's bounding box via GetBoxRight and propagates RecalcExtent to its parent dialog image. |

#### `TPicObject = SUBCLASS OF TImageWithID`

Dialog image subclass of TImageWithID that wraps and renders a QuickDraw PicHandle within a TDialogView.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsId: S255; itsView: TView; itsLocation: LPoint; itsPicHandle: PicHandle): TPicObject;` | Initializes a non-editable TPicObject at itsLocation with identifier itsId and bounding extent derived from itsPicHandle^^.picFrame. |
| `Free` | `PROCEDURE Free; OVERRIDE;` | Disposes of SELF.picture via KillPicture and frees the TPicObject. |
| `Draw` | `PROCEDURE Draw; OVERRIDE;` | Converts extentLRect to device coordinates on the current TPad and renders SELF.picture with QuickDraw DrawPicture. |

#### `TRectImage = SUBCLASS OF TDialogImage`

Geometric TDialogImage subclass that frames its bounding LRect using a stored QuickDraw PenState.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsExtent: LRect; itsId: S255; itsView: TView; itsPenState: PenState; withChildren: BOOLEAN): TRectImage;` | Initializes a TRectImage in itsView with bounding rectangle itsExtent and QuickDraw pen attributes itsPenState. |
| `Draw` | `PROCEDURE Draw; OVERRIDE;` | Restores SELF.penState and frames SELF.extentLRect using FrameLRect. |
| `LaunchLayoutBox` | `FUNCTION LaunchLayoutBox(view: TView): TImage; OVERRIDE;` | Creates and returns a resizable TLayoutBox with thin top borders wrapping this TRectImage for layout editing. |

#### `TTextDialogImage = SUBCLASS OF TImageWithID`

Reference-counted TImageWithID wrapper that embeds an editable UText TTextImage inside a dialog control or legend layout editor.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsExtent: LRect; itsId: S255; itsView: TView; itsTypeStyle: TTypeStyle; itsInitialChars: S255): TTextDialogImage;` | Initializes a reference-counted TTextDialogImage containing a growable TTextImage and single TEditPara initialized with itsInitialChars in itsTypeStyle. |
| `Free` | `PROCEDURE Free; OVERRIDE;` | Frees the underlying TText (and its owned TTextImage and paragraphs) before freeing this TTextDialogImage. |
| `ChangeRefCountBy` | `PROCEDURE ChangeRefCountBy(delta: INTEGER);` | Adjusts refCount by delta and frees this TTextDialogImage when refCount drops to zero or below. |
| `CursorAt` | `FUNCTION CursorAt(mouseLPt: LPoint): TCursorNumber; OVERRIDE;` | Returns textCursor when mouseLPt hits this TTextDialogImage, or noCursor otherwise. |
| `Draw` | `PROCEDURE Draw; OVERRIDE;` | Draws the embedded TTextImage. |
| `LaunchLayoutBox` | `FUNCTION LaunchLayoutBox(view: TView): TImage; OVERRIDE;` | Creates and returns a TLayoutBox configured for selecting (and optionally dragging) this TTextDialogImage in a TPlannerView. |
| `MousePress` | `PROCEDURE MousePress(mouseLPt: LPoint); OVERRIDE;` | Forwards mouse press coordinates mouseLPt to the embedded TTextImage.MousePress. |
| `OffsetBy` | `PROCEDURE OffsetBy(deltaLPt: LPoint); OVERRIDE;` | Offsets the embedded TTextImage and this image's extentLRect by deltaLPt. |

#### `TFrameSelection = SUBCLASS OF TSelection`

Selection wrapper subclass of TSelection for an active TInputFrame that enforces character-count limits, suppresses font-style menu commands, and cycles between input frames on Tab or Return.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsInputFrame: TInputFrame): TFrameSelection;` | Initializes a TFrameSelection of frameKind for itsInputFrame with boundLRect set to the text area and an empty coSelection. |
| `CanDoCommand` | `FUNCTION CanDoCommand(cmdNumber: TCmdNumber; VAR checkIt: BOOLEAN): BOOLEAN; OVERRIDE;` | Disables font family, size, and typestyle face menu commands within an input frame and delegates all other commands to SUPERSELF. |
| `KeyChar` | `PROCEDURE KeyChar(ch: CHAR); OVERRIDE;` | Forwards ch to coSelection.KeyChar if the paragraph has room below maxInputChars (or is replacing a range), otherwise displays a character-limit alert. |
| `KeyEnter` | `PROCEDURE KeyEnter(dh, dv: INTEGER); OVERRIDE;` | Advances or reverses focus to the adjacent TInputFrame via KeyTab when arrow or Enter keys produce a non-zero directional delta. |
| `KeyReturn` | `PROCEDURE KeyReturn; OVERRIDE;` | Advances focus to the next TInputFrame in the dialog by calling KeyTab(FALSE). |
| `KeyTab` | `PROCEDURE KeyTab(fBackward: BOOLEAN); OVERRIDE;` | Cycles the active TFrameSelection forward or backward (according to fBackward) to the next or previous active TInputFrame in the parent TDialog. |
| `MousePress` | `PROCEDURE MousePress(mouseLPt: LPoint); OVERRIDE;` | Delegates a repeat mouse press inside the already-selected input frame to SUPERSELF.MousePress and locks magnetCursor to textCursor. |
| `PerformCommand` | `PROCEDURE PerformCommand(command: TCommand; cmdPhase: TCmdPhase); OVERRIDE;` | Executes command via SUPERSELF, enforces the input frame's fixed inputTypeStyle, and truncates any pasted characters exceeding maxInputChars. |
| `Restore` | `PROCEDURE Restore; OVERRIDE;` | Restores currentDialogImage on the TDialogView to SELF.inputFrame and calls SUPERSELF.Restore during undo/redo. |

#### `TPlannerView = SUBCLASS OF TDialogView`

Interactive layout editor view subclass of TDialogView that constructs and manipulates parallel TLayoutBox wrappers for repositioning and editing images in a target TView.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsViewBeingPlanned: TView; itsPanel: TPanel; itsAllowSketching: BOOLEAN; itsRetainPickedBox: BOOLEAN): TPlannerView;` | Initializes a TPlannerView matching the extent and resolution of itsViewBeingPlanned to host interactive TLayoutBox wrappers in itsPanel. |
| `Init` | `PROCEDURE Init(itsListOfImages: TList);` | Populates rootDialog with TLayoutBox wrappers created via NewLayoutBox for every image in itsListOfImages and links same-sized TButtonLayoutBox peers. |
| `NewLayoutBox` | `FUNCTION NewLayoutBox(image: TImage): TLayoutBox;` | Creates and returns the TLayoutBox for image by invoking image.LaunchLayoutBox(SELF), or NIL if the image is not layout-editable. |
| `Free` | `PROCEDURE Free; OVERRIDE;` | Frees the TPlannerView and its rootDialog hierarchy of TLayoutBox wrappers without freeing the underlying planned images. |
| `Draw` | `PROCEDURE Draw; OVERRIDE;` | Draws every top-level TLayoutBox in the planner view via EachActualPart. |
| `CursorAt` | `FUNCTION CursorAt(mouseLPt: LPoint): TCursorNumber; OVERRIDE;` | Returns magnetCursor during an active mouse drag, or queries each TLayoutBox in rootDialog for the cursor at mouseLPt. |
| `MouseMove` | `PROCEDURE MouseMove(mouseLPt: LPoint); OVERRIDE;` | Delegates pointer drag movement directly to TView.MouseMove so the active layout selection tracks the drag. |
| `MousePress` | `PROCEDURE MousePress(mouseLPt: LPoint); OVERRIDE;` | Handles mouse presses in the layout view by extending an active legend edit or probing TLayoutBox.ConsiderMouse to start a TLayPickSelection drag. |
| `MouseRelease` | `PROCEDURE MouseRelease; OVERRIDE;` | Clears mouseIsDown and magnetCursor and delegates mouse release handling to TView.MouseRelease. |
| `EachActualPart` | `PROCEDURE EachActualPart(PROCEDURE DoToObject(filteredObj: TObject)); OVERRIDE;` | Applies DoToObject to every top-level TLayoutBox stored in rootDialog.children. |

#### `TLayoutBox = SUBCLASS OF TImageWithID`

Interactive manipulation handle subclass of TImageWithID in a TPlannerView that surrounds a target TImage (manipulee) with a draggable TTitleTab and optional frame.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; baseExtent: LRect; itsID: S255; itsParent: TLayoutBox; itsView: TView; itsManipulee: TImage; itsBorders: Rect; itsResizable: BOOLEAN; itsSuppression: BOOLEAN; withChildren: BOOLEAN): TLayoutBox;` | Initializes a TLayoutBox around baseExtent expanded by itsBorders, wrapping target image itsManipulee and attaching a TTitleTab captioned with itsID. |
| `Free` | `PROCEDURE Free; OVERRIDE;` | Frees SELF.titleTab and then frees this TLayoutBox and its child layout boxes. |
| `ChangeDragState` | `PROCEDURE ChangeDragState(enteringDrag: BOOLEAN);` | Sets hasDraggee to enteringDrag on this layout box and recursively on any enclosing parent TLayoutBox. |
| `ConsiderMouse` | `PROCEDURE ConsiderMouse(mouseLPt: LPoint; VAR madeSelection: BOOLEAN; VAR pickedLayoutBox: TLayoutBox); DEFAULT;` | Determines whether mouseLPt grabs this layout box's titleTab, picks a child layout box, or initiates an interior selection on SELF. |
| `CursorAt` | `FUNCTION CursorAt(mouseLPt: LPoint): TCursorNumber; OVERRIDE;` | Returns arrowCursor over titleTab, queries child layout boxes next, or returns arrowCursor for a draggable box. |
| `Draw` | `PROCEDURE Draw; OVERRIDE;` | Draws active child layout boxes and calls DrawJustMe whenever extentLRect is visible or hasDraggee is TRUE. |
| `DrawJustMe` | `PROCEDURE DrawJustMe; OVERRIDE;` | Draws titleTab, renders manipulee unless suppressDrawingManipulee is TRUE, and frames extentLRect if draggable and shouldFrame is TRUE. |
| `FreeManipulee` | `PROCEDURE FreeManipulee;` | Frees SELF.manipulee and clears the manipulee reference to NIL. |
| `Highlight` | `PROCEDURE Highlight(highTransit: THighTransit);` | Inverts and re-frames the bounding rectangle of SELF.titleTab to show selection state. |
| `MousePress` | `PROCEDURE MousePress(mouseLPT: LPoint); OVERRIDE;` | Dispatches a mouse press inside the layout box to the first child TLayoutBox that claims mouseLPt via DownAt. |
| `Move` | `PROCEDURE Move(deltaLPt: LPoint); DEFAULT;` | Offsets this layout box and its manipulee by deltaLPt and invalidates both the old and new bounding rectangles on all panel pads. |
| `NoTitleTab` | `FUNCTION NoTitleTab(heap: THeap): TTitleTab;` | Creates and returns a zero-height, captionless TTitleTab placeholder on heap for borderless layout boxes. |
| `OffsetBy` | `PROCEDURE OffsetBy(deltaLPt: LPoint); OVERRIDE;` | Offsets SELF.manipulee by deltaLPt if present and shifts this layout box, its titleTab, and child layout boxes via OffsetLayoutBoxBy. |
| `OffsetLayoutBoxBy` | `PROCEDURE OffsetLayoutBoxBy(deltaLPt: LPoint; textImageAsWell: BOOLEAN); DEFAULT;` | Offsets titleTab, SELF.extentLRect, and all child TLayoutBox wrappers by deltaLPt without moving manipulee again. |
| `RecalcExtent` | `PROCEDURE RecalcExtent; OVERRIDE;` | Recomputes this layout box's extent from its manipulee and child layout boxes plus borders, resizes SELF, and invalidates old and new bounds. |
| `Resize` | `PROCEDURE Resize(newExtent: LRect); OVERRIDE;` | Resizes titleTab to match the width and top of newExtent while preserving its height, then resizes this layout box. |
| `TabGrabbed` | `PROCEDURE TabGrabbed; DEFAULT;` | Provides a default no-op hook called when the user clicks the layout box's titleTab, overridden by TPageLayoutBox. |

#### `TLegendLayoutBox = SUBCLASS OF TLayoutBox`

Specialized TLayoutBox subclass for interactively dragging and inline-editing a TLegend via a temporary TTextDialogImage during dialog or page layout.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsView: TView; itsLegend: TLegend): TLegendLayoutBox;` | Initializes a TLegendLayoutBox wrapping itsLegend, adding plain drag borders if wouldBeDraggable is TRUE and enabling inline text selection. |
| `CursorAt` | `FUNCTION CursorAt(mouseLPt: LPoint): TCursorNumber; OVERRIDE;` | Returns arrowCursor over titleTab, textCursor over the editable legend interior, or noCursor outside. |
| `Draw` | `PROCEDURE Draw; OVERRIDE;` | Draws titleTab if draggable, renders the active editing textDialogImage (or manipulee legend when not being edited), and frames the box if draggable. |
| `OffsetBy` | `PROCEDURE OffsetBy(deltaLPt: LPoint); OVERRIDE;` | Offsets the wrapped TLegend, this layout box, and any active editing textDialogImage by deltaLPt. |
| `OffsetLayoutBoxBy` | `PROCEDURE OffsetLayoutBoxBy(deltaLPt: LPoint; textImageAsWell: BOOLEAN); OVERRIDE;` | Offsets the layout box bounds by deltaLPt and shifts any active textDialogImage horizontally (and vertically when textImageAsWell is TRUE). |
| `MousePress` | `PROCEDURE MousePress(mouseLPT: LPoint); OVERRIDE;` | Locks magnetCursor to textCursor, creates a TEditLegendSelection on the panel for inline editing of the legend, and passes MousePress to its TTextDialogImage. |
| `RecalcExtent` | `PROCEDURE RecalcExtent; OVERRIDE;` | Copies edited paragraph text and styles from textDialogImage back into the host TLegend, recalculates the legend's extent, and resizes parent layout boxes. |

#### `TButtonLayoutBox = SUBCLASS OF TLayoutBox`

Specialized TLayoutBox subclass for dragging a TButton by its ID title tab or editing its interior TLegend caption while keeping linked same-sized buttons synchronized.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsButton: TButton; itsView: TView): TButtonLayoutBox;` | Initializes a TButtonLayoutBox with an ID title tab around itsButton and adds a child TLegendLayoutBox for editing the button's caption. |
| `ConsiderMouse` | `PROCEDURE ConsiderMouse(mouseLPt: LPoint; VAR madeSelection: BOOLEAN; VAR pickedLayoutBox: TLayoutBox); OVERRIDE;` | Selects the button layout box for dragging when its titleTab is clicked, or starts inline caption editing in its child TLegendLayoutBox when the interior is clicked. |
| `CursorAt` | `FUNCTION CursorAt(mouseLPt: LPoint): TCursorNumber; OVERRIDE;` | Returns arrowCursor over the button's titleTab, textCursor over the button's caption interior, or noCursor outside. |
| `DrawJustMe` | `PROCEDURE DrawJustMe; OVERRIDE;` | Draws titleTab, asks the wrapped TButton to draw its rounded rectangle via DrawJustMe, and frames the outer layout box. |
| `OffsetBy` | `PROCEDURE OffsetBy(deltaLPt: LPoint); OVERRIDE;` | Offsets the button layout box and its wrapped TButton by deltaLPt and updates oldLegendTopLeft by the same delta. |
| `RecalcExtent` | `PROCEDURE RecalcExtent; OVERRIDE;` | Recenters the child TLegendLayoutBox after button caption edits and updates both this box and any width-linked nextSameSizedBox peers via RecalcJustMe. |
| `RecalcJustMe` | `PROCEDURE RecalcJustMe;` | Resizes this button layout box to match its wrapped TButton's current extent plus borders and invalidates old and new bounds on all pads. |

#### `TTitleTab = SUBCLASS OF TImage`

Image subclass of TImage that draws the framed header tab and optional ID caption along the top edge of a TLayoutBox.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsLayoutBox: TLayoutBox; itsHeight: INTEGER; itsCaption: S255): TTitleTab;` | Initializes a TTitleTab of height itsHeight across the top of itsLayoutBox with an optional centered TLegend caption in titleTypeStyle. |
| `Free` | `PROCEDURE Free; OVERRIDE;` | Frees the title tab's caption TLegend if present and frees the TTitleTab. |
| `Draw` | `PROCEDURE Draw; OVERRIDE;` | Fills the title tab's rectangle with white, frames it, and draws its caption legend if shouldDrawLegend is TRUE. |
| `OffsetBy` | `PROCEDURE OffsetBy(deltaLPt: LPoint); OVERRIDE;` | Offsets the caption legend (if any) and the title tab's extentLRect by deltaLPt. |
| `Resize` | `PROCEDURE Resize(newExtent: LRect); OVERRIDE;` | Resizes the title tab to newExtent, recenters its caption legend, and updates shouldDrawLegend based on whether the caption fits horizontally. |

#### `TLayPickSelection = SUBCLASS OF TSelection`

Selection subclass of TSelection representing a picked TLayoutBox being dragged or cleared within a TPlannerView.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsView: TPlannerView; itsKind: INTEGER; itsLayoutBox: TLayoutBox; itsAnchorLPt: LPoint): TLayPickSelection;` | Initializes a TLayPickSelection in itsView for dragging or deleting itsLayoutBox from anchor point itsAnchorLPt. |
| `CanDoCommand` | `FUNCTION CanDoCommand(cmdNumber: TCmdNumber; VAR checkIt: BOOLEAN): BOOLEAN; OVERRIDE;` | Enables the Clear command (uClear) for a selected layout box and delegates other command inquiries to SUPERSELF. |
| `Deselect` | `PROCEDURE Deselect; OVERRIDE;` | Clears currentLayoutBox on the TPlannerView, exits drag state on layoutBox, and deselects via SUPERSELF. |
| `Highlight` | `PROCEDURE Highlight(highTransit: THighTransit); OVERRIDE;` | Highlights or unhighlights the selected TLayoutBox according to highTransit. |
| `KeyClear` | `PROCEDURE KeyClear; OVERRIDE;` | Executes the Clear command (uClear) on the enclosing window when the Clear key is pressed while a layout box is picked. |
| `MouseMove` | `PROCEDURE MouseMove(mouseLPt: LPoint); OVERRIDE;` | Drags layoutBox by the mouse delta clamped to the planner view's boundaries, updating boundLRect and currLPt. |
| `MouseRelease` | `PROCEDURE MouseRelease; OVERRIDE;` | Creates and performs an undoable TLayMoveCmd if layoutBox was dragged to a new position, recalculates extents, and clears the pick selection unless retainPickedBox is TRUE. |
| `Restore` | `PROCEDURE Restore; OVERRIDE;` | Restores currentLayoutBox on the TPlannerView to SELF.layoutBox and invokes SUPERSELF.Restore. |

#### `TLayMoveCmd = SUBCLASS OF TCommand`

Undoable command subclass of TCommand that records and performs, undoes, or redoes a horizontal and vertical offset applied to a TLayoutBox.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsLayoutBox: TLayoutBox; itsHOffset, itsVOffset: LONGINT): TLayMoveCmd;` | Initializes an undoable uMoveLayoutBoxes command recording the target itsLayoutBox and its horizontal and vertical drag offsets. |
| `Perform` | `PROCEDURE Perform(cmdPhase: TCmdPhase); OVERRIDE;` | Moves layoutBox by (+hOffset, +vOffset) on redoPhase or (-hOffset, -vOffset) on undoPhase and recalculates manipulee and layout-box extents. |

#### `TEditLegendSelection = SUBCLASS OF TSelection`

Selection subclass of TSelection that manages inline text and typestyle editing of a TLegend inside a TLegendLayoutBox during interactive layout.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsLegendLayoutBox: TLegendLayoutBox; itsAnchorLPt: LPoint): TEditLegendSelection;` | Initializes an inline legend-editing selection for itsLegendLayoutBox, creating a temporary TTextDialogImage populated with the host TLegend's styled paragraph. |
| `Clone` | `FUNCTION Clone(heap: THeap): TObject; OVERRIDE;` | Increments the reference count on textDialogImage and returns a heap clone of this TEditLegendSelection. |
| `Deselect` | `PROCEDURE Deselect; OVERRIDE;` | Detaches textDialogImage from legendLayoutBox and deselects via SUPERSELF. |
| `Free` | `PROCEDURE Free; OVERRIDE;` | Frees this TEditLegendSelection and decrements the reference count of its temporary TTextDialogImage. |
| `CanDoCommand` | `FUNCTION CanDoCommand(cmdNumber: TCmdNumber; VAR checkIt: BOOLEAN): BOOLEAN; OVERRIDE;` | Disables font and face style commands if hostLegend uses the fixed system font (usesSysFont), or delegates to SUPERSELF otherwise. |
| `KeyBack` | `PROCEDURE KeyBack(fWord: BOOLEAN); OVERRIDE;` | Forwards Backspace to coSelection.KeyBack(fWord) and calls legendLayoutBox.RecalcExtent to resize the legend and any enclosing button or heading box. |
| `KeyChar` | `PROCEDURE KeyChar(ch: CHAR); OVERRIDE;` | Appends or replaces ch via coSelection.KeyChar if the legend has fewer than 255 characters and recalculates legendLayoutBox's extent, or shows a length alert. |
| `KeyEnter` | `PROCEDURE KeyEnter(dh, dv: INTEGER); OVERRIDE;` | Moves focus to the next or previous editable item via KeyTab when directional or Enter keys are pressed. |
| `KeyReturn` | `PROCEDURE KeyReturn; OVERRIDE;` | Ends inline legend editing by deselecting SELF when Return is pressed. |
| `MouseMove` | `PROCEDURE MouseMove(mouseLPt: LPoint); OVERRIDE;` | Forwards mouse drag coordinates to SUPERSELF.MouseMove unless a triple-click select-all is in progress. |
| `MousePress` | `PROCEDURE MousePress(mouseLPt: LPoint); OVERRIDE;` | Selects the entire legend text when triple-clicked, or delegates single and double clicks to SUPERSELF.MousePress. |
| `MouseRelease` | `PROCEDURE MouseRelease; OVERRIDE;` | Clears the tripleClick flag after a triple-click press, or delegates normal mouse releases to SUPERSELF.MouseRelease. |
| `NewCommand` | `FUNCTION NewCommand(cmdNumber: TCmdNumber): TCommand; OVERRIDE;` | Creates a command for cmdNumber via SUPERSELF.NewCommand to operate on the inline legend text coSelection. |
| `PerformCommand` | `PROCEDURE PerformCommand(command: TCommand; cmdPhase: TCmdPhase); OVERRIDE;` | Performs command via SUPERSELF, restores sysTypeStyle if hostLegend.usesSysFont is TRUE, and updates legendLayoutBox.RecalcExtent. |
| `Restore` | `PROCEDURE Restore; OVERRIDE;` | Reattaches SELF.textDialogImage to legendLayoutBox and restores the selection via SUPERSELF.Restore. |
| `Reveal` | `PROCEDURE Reveal(asMuchAsPossible: BOOLEAN); OVERRIDE;` | Synchronizes coSelection.boundLRect with SELF.boundLRect and scrolls the selection into view via SUPERSELF.Reveal. |

#### `TDialogDesignWindow = SUBCLASS OF TDialogWindow`

Interactive dialog-editor window subclass of TDialogWindow that temporarily replaces or overlays a host TDialogView with a TPlannerView for live dialog layout editing.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsHostDialogView: TDialogView): TDialogDesignWindow;` | Initializes a resizable TDialogDesignWindow containing a TPlannerView sized to edit the controls of itsHostDialogView. |
| `CanDoCommand` | `FUNCTION CanDoCommand(cmdNumber: TCmdNumber; VAR checkIt: BOOLEAN): BOOLEAN; OVERRIDE;` | Disables recursive uEditDialog, enables uStopEditDialog, and delegates all other command checks to SUPERSELF. |
| `NewCommand` | `FUNCTION NewCommand(cmdNumber: TCmdNumber): TCommand; OVERRIDE;` | Invokes RelinquishControl to exit dialog-editing mode when uStopEditDialog is selected, or delegates other commands to SUPERSELF. |
| `RelinquishControl` | `PROCEDURE RelinquishControl;` | Commits pending layout edits, takes down the design dialog window, applies any height changes back to the host dialog box, and redisplays or invalidates the host window. |
| `Resize` | `PROCEDURE Resize(moving: BOOLEAN); OVERRIDE;` | Resizes the design window via SUPERSELF and, when editing a non-resizable dialog box, updates the bottom extent of both the planner view and hostDialogView. |
| `SeizeControl` | `PROCEDURE SeizeControl;` | Suspends any active host dialog box, populates the design window's TPlannerView with layout boxes for hostDialogView's controls, and puts up the design dialog box. |

#### `TStdPrintManager = SUBCLASS OF TPrintManager`

Standard print manager subclass of TPrintManager that supplies default title and page-number TLegendHeading objects and launches interactive page-margin and heading editing.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap): TStdPrintManager;` | Allocates and initializes a TStdPrintManager instance on heap via TPrintManager.CREATE. |
| `EnterPageEditting` | `PROCEDURE EnterPageEditting; OVERRIDE;` | Commits the window's last command, creates a TPageDesignWindow if needed, and displays it as a dialog box for editing page margins and headings. |
| `Init` | `PROCEDURE Init(itsMainView: TView; itsDfltMargins: LRect); OVERRIDE;` | Initializes the print manager for itsMainView with itsDfltMargins and sets canEditPages to TRUE. |
| `ReactToPrinterChange` | `PROCEDURE ReactToPrinterChange; OVERRIDE;` | Updates print metrics via SUPERSELF.ReactToPrinterChange and resizes the layout panel view of any existing TPageDesignWindow to match pageView.extentLRect. |
| `SetDfltHeadings` | `PROCEDURE SetDfltHeadings; OVERRIDE;` | Installs default top-center '{Title}' and bottom-center '-{Page}-' TLegendHeading objects into SELF.headings. |

#### `TLegendHeading = SUBCLASS OF THeading`

Page header or footer subclass of THeading that maintains a template masterLegend and a page-substituted currentLegend for expanding '{Title}' and '{Page}' variables.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsPrintManager: TPrintManager; itsString: S255; itsTypeStyle: TTypeStyle; itsPageAlignment: TPageAlignment; itsOffsetFromAlignment: LPoint; itsBorders: Rect): TLegendHeading;` | Initializes a TLegendHeading for itsPrintManager with template string itsString, typestyle, page alignment, alignment offset, and border insets. |
| `Free` | `PROCEDURE Free; OVERRIDE;` | Frees both masterLegend and currentLegend before freeing the TLegendHeading. |
| `AdjustForPage` | `PROCEDURE AdjustForPage(pageNumber: LONGINT; editing: BOOLEAN); OVERRIDE;` | Populates currentLegend from masterLegend, substituting document title and pageNumber values for '{Title}' and '{Page}' placeholders when not editing. |
| `Draw` | `PROCEDURE Draw; OVERRIDE;` | Frames extentLRect if ShouldFrame returns TRUE and draws currentLegend. |
| `LaunchLayoutBox` | `FUNCTION LaunchLayoutBox(view: TView): TImage; OVERRIDE;` | Creates and returns a TLgHdngLayoutBox for positioning and editing this TLegendHeading in a TPagePlannerView. |
| `OffsetBy` | `PROCEDURE OffsetBy(deltaLPt: LPoint); OVERRIDE;` | Offsets currentLegend and the heading's extentLRect by deltaLPt. |
| `RecalcExtent` | `PROCEDURE RecalcExtent; OVERRIDE;` | Updates currentLegend's box bounds, expands them by SELF.borders, and resizes the heading to the resulting LRect. |
| `ShouldFrame` | `FUNCTION ShouldFrame: BOOLEAN; OVERRIDE;` | Returns FALSE by default so legend headings are printed and previewed without a surrounding border rectangle. |

#### `TPageDesignWindow = SUBCLASS OF TDialogWindow`

Split-panel dialog window subclass of TDialogWindow that pairs a TPageStatusDialog control panel with a TPagePlannerView for interactive page margin and header/footer design.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsHostView: TView): TPageDesignWindow;` | Initializes a resizable TPageDesignWindow for itsHostView with a top TPageStatusDialog control panel and a lower TPagePlannerView layout panel. |
| `Disappear` | `PROCEDURE Disappear; OVERRIDE;` | Invalidates the host view's panel when margin preview mode is active so updated headings redraw, then hides the window via SUPERSELF.Disappear. |
| `NewCommand` | `FUNCTION NewCommand(cmdNumber: TCmdNumber): TCommand; OVERRIDE;` | Deletes the currently selected heading layout box and its underlying THeading on uClear, or delegates other commands to SUPERSELF. |

#### `TPagePlannerView = SUBCLASS OF TPlannerView`

Page layout planner view subclass of TPlannerView that renders the page outline, patterned content margins, and draggable TPageLayoutBox wrappers for print headings.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsPrintManager: TPrintManager; itsPanel: TPanel): TPagePlannerView;` | Initializes a TPagePlannerView for itsPrintManager.pageView in itsPanel and builds layout boxes for all headings in itsPrintManager.headings. |
| `Draw` | `PROCEDURE Draw; OVERRIDE;` | Fills the page's printable contentLRect with marginPattern, frames the page and content rectangles, and draws all heading layout boxes. |

#### `TPageStatusDialog = SUBCLASS OF TDialog`

Control-panel TDialog in a TPageDesignWindow providing clusters, buttons, and input frames for configuring heading page ranges, odd/even placement, alignment, measurement units, and page margins.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsPanel: TPanel): TPageStatusDialog;` | Initializes the status TDialog in itsPanel with clusters, input frames, and action buttons for configuring page margins, units, and heading attributes. |
| `ButtonPushed` | `PROCEDURE ButtonPushed(button: TButton); OVERRIDE;` | Applies margin changes, creates a new TLegendHeading, updates the selected heading's parameters, restores defaults, or dismisses the TPageDesignWindow depending on which button was pushed. |
| `CheckboxHit` | `PROCEDURE CheckboxHit(checkbox: TCheckbox; toggleDirection: BOOLEAN); OVERRIDE;` | Updates marginTitle between quarter-inch and centimeter labels whenever the user toggles the measurement unitsCluster. |
| `DownAt` | `FUNCTION DownAt(mouseLPt: LPoint): TDialogImage; OVERRIDE;` | Clears currentHeading to NIL before delegating mouse hit-testing to SUPERSELF.DownAt. |
| `Draw` | `PROCEDURE Draw; OVERRIDE;` | Draws all dialog controls via SUPERSELF.Draw and renders dividing lines separating the heading controls from the margin controls. |
| `InspectHeadingParms` | `PROCEDURE InspectHeadingParms(VAR oddOnly, evenOnly: BOOLEAN; VAR pageAlignment: TPageAlignment; VAR minPage, maxPage: LONGINT);` | Reads oddOnly, evenOnly, pageAlignment, minPage, and maxPage settings out of the dialog's clusters and page-number input frames. |
| `SetHeadingParms` | `PROCEDURE SetHeadingParms(oddOnly, evenOnly: BOOLEAN; pageAlignment: TPageAlignment; minPage, maxPage: LONGINT);` | Updates oddEvenCluster, alignCluster, minPageFrame, and maxPageFrame to reflect the specified heading parameters. |

#### `TPageLayoutBox = SUBCLASS OF TLayoutBox`

Layout box subclass of TLayoutBox that wraps a print THeading inside a TPagePlannerView and updates the TPageStatusDialog when its title tab is grabbed.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsView: TView; itsHeading: THeading; itsResizable: BOOLEAN): TPageLayoutBox;` | Initializes a TPageLayoutBox in itsView wrapping print heading itsHeading with plain borders and optional resizability. |
| `FreeManipulee` | `PROCEDURE FreeManipulee; OVERRIDE;` | Removes and frees the wrapped THeading from the planned view's printManager.headings list and clears manipulee. |
| `TabGrabbed` | `PROCEDURE TabGrabbed; OVERRIDE;` | Loads the wrapped THeading's odd/even, alignment, and page-range settings into the TPageStatusDialog when its title tab is selected. |

#### `TLgHdngLayoutBox = SUBCLASS OF TPageLayoutBox`

Specialized TPageLayoutBox subclass that wraps a TLegendHeading and embeds a child TLegendLayoutBox so users can both drag and edit header/footer text on the page.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsView: TView; itsLegendHeading: TLegendHeading): TLgHdngLayoutBox;` | Initializes a TLgHdngLayoutBox positioned on the page for itsLegendHeading and attaches a child TLegendLayoutBox for editing its masterLegend. |
| `CursorAt` | `FUNCTION CursorAt(mouseLPt: LPoint): TCursorNumber; OVERRIDE;` | Returns arrowCursor over titleTab, textCursor over the heading's editable legend area, or noCursor outside. |
| `Draw` | `PROCEDURE Draw; OVERRIDE;` | Draws titleTab, frames the heading layout box, and renders its child legendLayoutBox when visible. |
| `MousePress` | `PROCEDURE MousePress(mouseLPT: LPoint); OVERRIDE;` | Clamps mouseLPt to legendLayoutBox, starts an inline TEditLegendSelection, updates the TPageStatusDialog via TabGrabbed, and passes MousePress to the text image. |
| `Move` | `PROCEDURE Move(deltaLPt: LPoint); OVERRIDE;` | Moves the layout box by deltaLPt, offsets the heading's masterLegend, and updates legendHeading.offsetFromAlignment. |
| `RecalcExtent` | `PROCEDURE RecalcExtent; OVERRIDE;` | Recomputes the heading and layout-box bounds after inline text or font edits, adjusting vertical baseline alignment and invalidating old and new rectangles. |

---

## Unit UText

Provides the Lisa Toolkit Multiple-Paragraph Text Building Block (UText), implementing styled paragraph storage, word-wrapped line layout, linked multi-column text images, text selections and blinking insertion points, undoable editing/style commands, and clipboard Universal Text export.

- **Import**: `USES UText;`
- **Unit kind**: `INTRINSIC` (`UTEXT`)
- **Interface dependencies**: `UObject`, `QuickDraw`, `UDraw`, `UTKUniversalText`, `UABC`

### Clascal Classes

#### `TParaFormat = SUBCLASS OF TObject`

Reference-counted paragraph formatting descriptor subclass of TObject specifying default TTypeStyle, word-wrap mode, alignment, indents, inter-paragraph spacing, line spacing, and tab stops.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsStyleSheet: TStyleSheet): TParaFormat;` | Initializes a TParaFormat associated with itsStyleSheet using 12-pitch Modern plain text, word-wrapping, left alignment, zero indents, and an empty tab TArray. |
| `SetTypeStyle` | `PROCEDURE SetTypeStyle(tStyle: TTypeStyle);` | Applies tStyle to the active QuickDraw GrafPort via SetQDTypeStyle. |
| `ChangeRefCountBy` | `PROCEDURE ChangeRefCountBy(delta: INTEGER);` | Adjusts refCount by delta and, if refCount reaches zero and permanent is FALSE, removes and frees this TParaFormat from its styleSheet (or frees it directly). |

#### `TParagraph = SUBCLASS OF TString`

Styled character string subclass of TString that pairs paragraph text with a run-length TArray of TStyleChange records for multi-font drawing, measurement, and word-boundary detection.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; initialSize: INTEGER; initialTypeStyle: TTypeStyle): TParagraph;` | Allocates a dynamic TParagraph of capacity initialSize and initializes its typeStyles run array with sentinel entries at -1 and MAXINT for initialTypeStyle. |
| `Free` | `PROCEDURE Free; OVERRIDE;` | Frees the typeStyles run array and then frees the TParagraph string object. |
| `Draw` | `PROCEDURE Draw(i: LONGINT; howMany: INTEGER); OVERRIDE;` | Draws howMany characters starting at 1-based string index i using the paragraph's styled character runs. |
| `Width` | `FUNCTION Width(i: LONGINT; howMany: INTEGER): INTEGER; OVERRIDE;` | Measures and returns the pixel width of howMany styled characters starting at 1-based string index i. |
| `DrawLine` | `PROCEDURE DrawLine(startLP, endLP: INTEGER; fDraw: BOOLEAN; fWidth: BOOLEAN; VAR width: INTEGER; VAR styleIndex: INTEGER);` | Iterates across typeStyles runs from logical position startLP to endLP, optionally drawing characters (fDraw) and/or computing their cumulative width (fWidth) while updating styleIndex. |
| `ChangeStyle` | `PROCEDURE ChangeStyle(startLP, endLP: INTEGER; PROCEDURE Change(VAR typeStyle: TTypeStyle); VAR styleOfStartLP: TTypeStyle);` | Applies caller procedure Change to every TTypeStyle run overlapping [startLP, endLP], splitting boundary runs, cleaning redundant runs, and returning the updated style at startLP. |
| `ChgFace` | `PROCEDURE ChgFace(startLP, endLP: INTEGER; newOnFaces: Style; VAR styleOfStartLP: TTypeStyle);` | Adds newOnFaces to (or clears all faces when newOnFaces is empty on) the character runs in [startLP, endLP] via ChangeStyle. |
| `ChgFontSize` | `PROCEDURE ChgFontSize(startLP, endLP: INTEGER; newFontSize: Byte; VAR styleOfStartLP: TTypeStyle);` | Sets fontSize to newFontSize across all TTypeStyle runs in [startLP, endLP] via ChangeStyle. |
| `ChgFontFamily` | `PROCEDURE ChgFontFamily(startLP, endLP: INTEGER; newFontFamily: Byte; VAR styleOfStartLP: TTypeStyle);` | Sets fontFamily to newFontFamily across all TTypeStyle runs in [startLP, endLP] via ChangeStyle. |
| `NewStyle` | `PROCEDURE NewStyle(startLP, endLP: INTEGER; newTypeStyle: TTypeStyle);` | Replaces the entire TTypeStyle across [startLP, endLP] with newTypeStyle via ChangeStyle. |
| `CleanRuns` | `PROCEDURE CleanRuns;` | Scans typeStyles and deletes adjacent TStyleChange entries that share the same logical position or identical font and face attributes. |
| `UpdateRuns` | `PROCEDURE UpdateRuns(atLP: INTEGER; replacedChars: INTEGER; insertedChars: INTEGER);` | Shifts and coalesces TStyleChange run positions at and after atLP when replacedChars characters are deleted and insertedChars characters are inserted. |
| `ReplPara` | `PROCEDURE ReplPara(fPos, numChars: INTEGER; otherPara: TParagraph; otherFPos, otherNumChars: INTEGER);` | Replaces numChars characters at logical position fPos with otherNumChars characters and their corresponding TStyleChange runs from otherPara starting at otherFPos. |
| `ReplTString` | `PROCEDURE ReplTString(fPos, numChars: INTEGER; otherString: TString; otherFPos, otherNumChars: INTEGER);` | Clamps fPos via FixLP, replaces numChars characters with otherNumChars characters from otherString starting at otherFPos, and updates typestyle run offsets. |
| `ReplPString` | `PROCEDURE ReplPString(fPos, numChars: INTEGER; pStr: TPString);` | Clamps fPos via FixLP, replaces numChars characters at fPos with the characters of Pascal string pStr (or deletes them if pStr is NIL), and updates typestyle runs. |
| `BuildExtentLRect` | `PROCEDURE BuildExtentLRect(baseLPt: LPoint; VAR extentLRect: LRect);` | Computes extentLRect from baseline point baseLPt using the paragraph's total character width and the maximum ascent, descent, and leading among its font runs. |
| `FixLP` | `FUNCTION FixLP(LP: INTEGER): INTEGER;` | Clamps logical character position LP to the valid range [0..SELF.size] of the paragraph. |
| `SetTypeStyle` | `PROCEDURE SetTypeStyle(tStyle: TTypeStyle);` | Sets the current QuickDraw GrafPort font and face attributes to tStyle via SetQDTypeStyle. |
| `StyleAt` | `PROCEDURE StyleAt(lp: INTEGER; VAR typeStyle: TTypeStyle);` | Looks up and returns in typeStyle the TTypeStyle active at logical character position lp. |
| `FindWordBounds` | `PROCEDURE FindWordBounds(orig: INTEGER; VAR first, last: INTEGER);` | Expands logical position orig left and right across word-qualifying characters via Qualifies to return the [first, last] bounds for double-click word selection. |
| `Qualifies` | `FUNCTION Qualifies(pos: INTEGER): BOOLEAN;` | Returns TRUE if the character at logical position pos (together with its neighbors, such as embedded apostrophes, hyphens, periods, or commas in numbers/words) belongs to a selectable word. |

#### `TEditPara = SUBCLASS OF TParagraph`

Editable paragraph subclass of TParagraph that binds a TParaFormat, tracks gap-buffer backspace and insertion state, and maintains a TList of TParaImage views displaying it.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; initialSize: INTEGER; itsFormat: TParaFormat): TEditPara;` | Initializes a dynamic TEditPara of initialSize bound to itsFormat, increments itsFormat's reference count, and creates an empty TList of TParaImage views. |
| `Free` | `PROCEDURE Free; OVERRIDE;` | Decrements format's reference count, frees the images TList container (without freeing its TParaImage elements), and frees the paragraph. |
| `BeginInsertion` | `PROCEDURE BeginInsertion(atLP: INTEGER; size: INTEGER);` | Positions the dynamic collection gap at atLP with at least size slack bytes and resets bsCount unless already backspacing at that hole. |
| `EndInsertion` | `PROCEDURE EndInsertion;` | Closes the collection editing gap via StopEdit and resets the backspace counter bsCount to zero. |
| `GrowSize` | `FUNCTION GrowSize: INTEGER;` | Returns the default editing slack size (200 characters) allocated when opening a paragraph for typing. |
| `InsertOneChar` | `PROCEDURE InsertOneChar(ch: CHAR; atLP: INTEGER);` | Opens a 1-character insertion slot at atLP, stores ch, and shifts typestyle runs via UpdateRuns. |
| `SetTypeStyle` | `PROCEDURE SetTypeStyle(tStyle: TTypeStyle); OVERRIDE;` | Delegates QuickDraw typestyle setup to SELF.format.SetTypeStyle(tStyle). |
| `EachImage` | `PROCEDURE EachImage(PROCEDURE ImageProc(paraImage: TParaImage));` | Invokes ImageProc on every TParaImage registered in SELF.images. |
| `DelImage` | `PROCEDURE DelImage(delImage: TParaImage; fFree: BOOLEAN);` | Removes delImage from SELF.images and optionally frees it when fFree is TRUE. |
| `InsImage` | `PROCEDURE InsImage(paraImage: TParaImage);` | Appends paraImage to SELF.images as a visual observer of this paragraph. |
| `DelImgIF` | `PROCEDURE DelImgIF(FUNCTION ShouldDelete(paraImage: TParaImage): BOOLEAN);` | Scans SELF.images and removes (without freeing) every TParaImage for which predicate ShouldDelete returns TRUE. |

#### `TLineInfo = SUBCLASS OF TObject`

Line-layout metadata subclass of TObject recording the logical character range (startLP, lastDrawnLP, endLP), bounding LRect, ascent, and validity flag of a single formatted text line.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap): TLineInfo;` | Allocates a TLineInfo record initialized as invalid with zeroed logical positions, ascent, and lineLRect. |
| `LeftCoord` | `FUNCTION LeftCoord(proposedLeftPixel: LONGINT): LONGINT;` | Returns the left pixel coordinate for highlighting or invalidating this line, defaulting to proposedLeftPixel unless overridden by subclasses. |
| `RightCoord` | `FUNCTION RightCoord(proposedRightPixel: LONGINT): LONGINT;` | Returns the right pixel coordinate for highlighting or invalidating this line, defaulting to proposedRightPixel unless overridden by subclasses. |

#### `TParaImage = SUBCLASS OF TImage`

Visual paragraph image subclass of TImage that breaks a TEditPara into wrapped TLineInfo lines within a TTextImage, renders styled lines, and maps between view coordinates and logical character positions.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsView: TView; itsParagraph: TEditPara; itsLRect: LRect; lineTop: LONGINT; lineLeft: LONGINT): TParaImage;` | Initializes a TParaImage in itsView for itsParagraph with initial bounds itsLRect and a single default TLineInfo at (lineLeft, lineTop). |
| `Free` | `PROCEDURE Free; OVERRIDE;` | Frees lineList (and its TLineInfo objects) before freeing the TParaImage. |
| `ComputeLineInfo` | `PROCEDURE ComputeLineInfo(curLine: TLineInfo; maxLineLen: INTEGER; VAR nextLP: INTEGER; VAR lRectNeeded: LRect);` | Provides a hook for computing custom TLineInfo bounds and nextLP for curLine within maxLineLen. |
| `DfltLineInfo` | `FUNCTION DfltLineInfo(lineTop: LONGINT; lineLeft: LONGINT): TLineInfo;` | Creates and returns a TLineInfo positioned at (lineLeft, lineTop) using the font ascent, descent, leading, and firstIndent of GetFormat. |
| `DrawLine` | `PROCEDURE DrawLine(startLP: INTEGER; fDraw: BOOLEAN; stopWidth, wrapWidth: INTEGER; VAR lineWidth, lastToDraw, endLP: INTEGER);` | Measures (and if fDraw is TRUE, draws) a single line from startLP up to stopWidth and word-wrap limit wrapWidth, handling tabs and returning lineWidth, lastToDraw, and endLP. |
| `DrawParaImage` | `PROCEDURE DrawParaImage(limitLRect: LRect; startLP: INTEGER; drawAction: TDrawAction; invalBits: BOOLEAN; VAR drawnLRect: LRect);` | Recomputes TLineInfo line breaks from startLP within limitLRect, optionally drawing or invalidating changed lines according to drawAction and returning drawnLRect. |
| `Draw` | `PROCEDURE Draw; OVERRIDE;` | Draws all formatted lines of this paragraph image by calling RedrawLines(0, MAXINT). |
| `FastDrawLine` | `PROCEDURE FastDrawLine(startLP, endLP: INTEGER; fDraw: BOOLEAN; fWidth: BOOLEAN; VAR width: INTEGER; VAR styleIndex: INTEGER);` | Temporarily installs SELF.GetFormat on the paragraph and delegates single-line drawing or width measurement over [startLP, endLP] to TParagraph.DrawLine. |
| `GetFormat` | `FUNCTION GetFormat: TParaFormat;` | Returns the TParaFormat governing this paragraph image (defaulting to SELF.paragraph.format). |
| `LineWithLPt` | `PROCEDURE LineWithLPt(pt: LPoint; VAR lineIndex: INTEGER; VAR lineInfo: TLineInfo);` | Finds the 1-based lineIndex and TLineInfo in lineList whose vertical (and horizontal) span contains view point pt. |
| `LocateLP` | `PROCEDURE LocateLP(LP: INTEGER; VAR lineIndex: INTEGER; VAR pixel: LONGINT);` | Finds the 1-based lineIndex and horizontal view coordinate pixel corresponding to logical character position LP. |
| `LpWithLPt` | `FUNCTION LpWithLPt(pt: LPoint): INTEGER;` | Maps view coordinate pt to the nearest logical character position (LP) within this paragraph image. |
| `OffSetBy` | `PROCEDURE OffSetBy(deltaLPt: LPoint); OVERRIDE;` | Offsets SELF.extentLRect and every TLineInfo.lineLRect in lineList by deltaLPt. |
| `ParaTextWidth` | `FUNCTION ParaTextWidth(startLP, endLP: INTEGER): INTEGER;` | Returns the pixel width of characters from startLP through endLP after passing SELF through active command filtering. |
| `RedrawLines` | `PROCEDURE RedrawLines(startLine: INTEGER; endLine: INTEGER);` | Draws formatted lines from 1-based index startLine through endLine inside a QuickDraw picture group, filtering through any active TStyleCmd. |
| `SeesSameAs` | `FUNCTION SeesSameAs(image: TImage): BOOLEAN; OVERRIDE;` | Returns TRUE if image is SELF or another TParaImage displaying the exact same TEditPara. |
| `InvalLinesWith` | `PROCEDURE InvalLinesWith(startLP, endLP: INTEGER);` | Marks this TParaImage as changed and clears the valid flag on every TLineInfo overlapping [startLP, endLP]. |
| `AdjustLineLPs` | `PROCEDURE AdjustLineLPs(atLP, deltaLP: INTEGER);` | Shifts startLP, lastDrawnLP, and endLP by deltaLP on all TLineInfo entries (and SELF.startLP/endLP) beyond atLP after an edit. |

#### `TStyleSheet = SUBCLASS OF TObject`

Collection container subclass of TObject holding a TList of TParaFormat definitions shared across a TText document.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap): TStyleSheet;` | Allocates a TStyleSheet on heap with an empty formats TList. |
| `Free` | `PROCEDURE Free; OVERRIDE;` | Frees the formats TList (and its TParaFormat members) before freeing the TStyleSheet. |
| `InitDefault` | `PROCEDURE InitDefault;` | Creates a default TParaFormat and appends it to SELF.formats. |

#### `TTextRange = SUBCLASS OF TObject`

Character-span descriptor subclass of TObject identifying a start and end TEditPara, paragraph list index, and logical character position (LP) within a TText.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; beginPara: TEditPara; beginIndex: LONGINT; beginLP: INTEGER; endPara: TEditPara; endIndex: LONGINT; endLP: INTEGER): TTextRange;` | Allocates and initializes a TTextRange spanning from (beginPara, beginIndex, beginLP) to (endPara, endIndex, endLP). |
| `AdjustBy` | `PROCEDURE AdjustBy(delta: INTEGER);` | Provides a hook for adjusting the logical character offsets of the text range by delta. |

#### `TText = SUBCLASS OF TObject`

Model-level multi-paragraph text document subclass of TObject managing an ordered TList of TEditPara paragraphs, a TStyleSheet, and all independent TTextImage chains viewing the text.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsStyleSheet: TStyleSheet): TText;` | Initializes an empty TText model with a paragraphs TList, a txtImgList of viewing TTextImage heads, and styleSheet itsStyleSheet. |
| `DfltTextImage` | `FUNCTION DfltTextImage(view: TView; imageLRect: LRect; imgIsGrowable: BOOLEAN): TTextImage;` | Creates a TTextImage in view with imageLRect, appends an empty TEditPara using the first TParaFormat in styleSheet, recomputes images, and returns the TTextImage. |
| `Free` | `PROCEDURE Free; OVERRIDE;` | Frees all viewing TTextImage chains and all owned TEditPara paragraphs via FreeSelf(TRUE). |
| `FreeSelf` | `PROCEDURE FreeSelf(freeParas: BOOLEAN);` | Frees all TTextImage chains in txtImgList, frees either all TEditPara objects (when freeParas is TRUE) or just the paragraphs list shell, and frees SELF. |
| `ChangeSelInOtherPanels` | `PROCEDURE ChangeSelInOtherPanels(textSelection: TTextSelection);` | Replicates textSelection into every other panel whose TTextImage in txtImgList views this TText. |
| `DelPara` | `PROCEDURE DelPara(delPara: TEditPara; fFree: BOOLEAN);` | Removes all TParaImage views of delPara across every TTextImage viewing this TText and optionally frees delPara. |
| `Draw` | `PROCEDURE Draw;` | Draws every registered TTextImage in txtImgList across all pads of their respective panels. |
| `HiliteRange` | `PROCEDURE HiliteRange(highTransit: THighTransit; textRange: TTextRange; wholePara: BOOLEAN);` | Highlights or unhighlights textRange across all TTextImage views by delegating its paragraph indices and LPs to HiliteParagraphs. |
| `HiliteParagraphs` | `PROCEDURE HiliteParagraphs(highTransit: THighTransit; startIndex: LONGINT; startLP: INTEGER; endIndex: LONGINT; endLP: INTEGER; wholePara: BOOLEAN);` | Highlights or unhighlights the span from (startIndex, startLP) to (endIndex, endLP) on all pads of every panel viewing this TText. |
| `InsParaAfter` | `PROCEDURE InsParaAfter(existingPara: TEditPara; newPara: TEditPara);` | Inserts newPara immediately after existingPara in SELF.paragraphs and creates corresponding TParaImage entries in every viewing TTextImage. |
| `Invalidate` | `PROCEDURE Invalidate;` | Invalidates changed lines on all pads of every TTextImage in txtImgList. |
| `MarkChanged` | `PROCEDURE MarkChanged(textRange: TTextRange);` | Marks the character span specified by textRange as changed in every TTextImage viewing this TText. |
| `RecomputeImages` | `PROCEDURE RecomputeImages;` | Recomputes line layout and draws or invalidates changed lines across all pads for every TTextImage in txtImgList. |
| `SelectAll` | `FUNCTION SelectAll(textImage: TTextImage): TTextSelection;` | Creates and returns a TTextSelection spanning from LP 0 of the first paragraph to the end of the last paragraph in textImage. |

#### `TTextImage = SUBCLASS OF TImage`

Visual text container subclass of TImage that lays out and renders a TList of TParaImage objects for a TText, supporting either dynamic vertical growth or linked multi-column text flow.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsView: TView; itsLRect: LRect; itsText: TText; isGrowable: BOOLEAN): TTextImage;` | Initializes a TTextImage in itsView over itsLRect for itsText, setting growsDynamically to isGrowable and initializing single-box chain pointers to SELF. |
| `Free` | `PROCEDURE Free; OVERRIDE;` | Frees every TTextImage and its imageList of TParaImage objects along the linked text-image chain starting from headTxtImg without freeing the underlying TText. |
| `FreeOneTextImage` | `PROCEDURE FreeOneTextImage;` | Frees only this single TTextImage and its imageList without traversing or updating prevTxtImg/nextTxtImg chain links. |
| `Draw` | `PROCEDURE Draw; OVERRIDE;` | Redraws visible TParaImage objects in imageList inside a QuickDraw picture group and recursively draws any linked nextTxtImg. |
| `DrawImages` | `PROCEDURE DrawImages(fDraw: BOOLEAN);` | Redraws visible TParaImage objects in imageList and recursively invokes DrawImages on any linked nextTxtImg. |
| `DrawOrInval` | `PROCEDURE DrawOrInval(invalBits: BOOLEAN);` | Draws or invalidates invalid TLineInfo rectangles in changed TParaImage entries across the text-image chain and optionally resets validity flags. |
| `HiliteText` | `PROCEDURE HiliteText(highTransit: THighTransit; startIndex: LONGINT; startLP: INTEGER; endIndex: LONGINT; endLP: INTEGER; wholePara: BOOLEAN);` | Inverts selection highlight rectangles (or draws the insertion caret) from (startIndex, startLP) to (endIndex, endLP) across visible TParaImage lines in this chain. |
| `FindParaAndLp` | `PROCEDURE FindParaAndLp(LPt: LPoint; VAR paraImage: TParaImage; VAR paraIndex: LONGINT; VAR aLP: INTEGER);` | Locates the TParaImage, 1-based paragraph index paraIndex, and logical character position aLP corresponding to view coordinate LPt. |
| `FindTextImage` | `FUNCTION FindTextImage(VAR mouseLPt: LPoint; VAR firstTxtImg: TTextImage): TTextImage;` | Finds the TTextImage in the linked chain that contains mouseLPt (or the nearest preceding non-empty TTextImage), clamping mouseLPt and returning the earlier chain member in firstTxtImg. |
| `ImageBottom` | `FUNCTION ImageBottom: LONGINT;` | Returns the bottom vertical coordinate of the last TParaImage in imageList, or extentLRect.top if imageList is empty. |
| `GetImageRange` | `PROCEDURE GetImageRange(firstIndex: LONGINT; VAR firstLP: INTEGER; lastIndex: LONGINT; VAR lastLP: INTEGER; VAR firstImage, lastImage: TParaImage);` | Clips the paragraph/LP span [firstIndex/firstLP .. lastIndex/lastLP] to the portion actually displayed by this TTextImage chain and returns firstImage and lastImage. |
| `ImageWith` | `FUNCTION ImageWith(paragraph: TEditPara; lp: INTEGER): TParaImage;` | Returns the TParaImage belonging to this TTextImage chain that displays logical position lp of paragraph, or NIL if not displayed. |
| `MousePress` | `PROCEDURE MousePress(mouseLPt: LPoint); OVERRIDE;` | Extends an existing TTextSelection on Shift-click or multi-click, or begins a new TInsertionPoint selection at mouseLPt. |
| `OffsetBy` | `PROCEDURE OffsetBy(deltaLPt: LPoint); OVERRIDE;` | Offsets SELF.extentLRect and every TParaImage in imageList by deltaLPt. |
| `AddImage` | `PROCEDURE AddImage(paraImage: TParaImage);` | Appends paraImage to the end of SELF.imageList. |
| `DelImagesWith` | `PROCEDURE DelImagesWith(delPara: TEditPara);` | Removes and frees all TParaImage instances displaying delPara that belong to this TTextImage chain. |
| `InsertNewPara` | `PROCEDURE InsertNewPara(existingPara, newPara: TEditPara);` | Creates and inserts a new TParaImage for newPara immediately after existingPara's TParaImage in the appropriate TTextImage of the chain. |
| `InvalAll` | `PROCEDURE InvalAll;` | Invalidates all TLineInfo entries and panel bounding rectangles across every TTextImage in the chain starting at headTxtImg. |
| `Invalidate` | `PROCEDURE Invalidate; OVERRIDE;` | Invalidates panel rectangles for offset or changed TParaImage lines and any vacated area above formerBottom across the chain. |
| `MarkChanged` | `PROCEDURE MarkChanged(startIndex: LONGINT; startLP: INTEGER; endIndex: LONGINT; endLP: INTEGER);` | Marks all TParaImage lines overlapping (startIndex, startLP) through (endIndex, endLP) as invalid so they will be reformatted and redrawn. |
| `NewTextSelection` | `FUNCTION NewTextSelection(firstPara: TEditPara; firstIndex: LONGINT; firstLP: INTEGER; lastPara: TEditPara; lastIndex: LONGINT; lastLP: INTEGER): TTextSelection;` | Factory method that creates a TInsertionPoint, TOneParaSelection, or TMultiParaSelection appropriate for the given paragraph and LP bounds. |
| `RecomputeImages` | `PROCEDURE RecomputeImages(drawAction: TDrawAction; invalBits: BOOLEAN);` | Reflows paragraphs across this TTextImage (and any linked column chain), growing extentLRect if growsDynamically is TRUE and drawing or invalidating updated lines. |
| `Resize` | `PROCEDURE Resize(newExtent: LRect); OVERRIDE;` | Updates SELF.extentLRect to newExtent and invalidates all displayed lines across the chain via InvalAll. |
| `SeesSameAs` | `FUNCTION SeesSameAs(image: TImage): BOOLEAN; OVERRIDE;` | Returns TRUE if image is SELF or a TParaImage/TTextImage viewing the same underlying TText object. |
| `SetFirstIndex` | `PROCEDURE SetFirstIndex;` | Initializes firstIndex to 1 so text display starts at the first paragraph unless overridden by a subclass. |
| `NewEditPara` | `FUNCTION NewEditPara(initialSize: INTEGER; itsFormat: TParaFormat): TEditPara;` | Factory method that allocates and returns a new TEditPara of initialSize and format itsFormat on SELF.Heap. |
| `NewParaImage` | `FUNCTION NewParaImage(itsParagraph: TEditPara; itsLRect: LRect; lineTop: LONGINT; lineLeft: LONGINT): TParaImage;` | Factory method that creates a TParaImage for itsParagraph, binds its textImage back-pointer to SELF, registers it on itsParagraph, and returns it. |
| `NewTextImage` | `FUNCTION NewTextImage(heap: THeap; itsView: TView; itsLRect: LRect; itsText: TText; isGrowable: BOOLEAN): TTextImage;` | Factory method that allocates and returns a new TTextImage instance on heap. |
| `TxtImgForClipBoard` | `FUNCTION TxtImgForClipBoard(heap: THeap; itsView: TView; itsLRect: LRect; itsText: TText; isGrowable: BOOLEAN): TTextImage;` | Factory method that creates and returns a TTextImage configured to display copied or cut text in the clipboard TTextView. |

#### `TTextView = SUBCLASS OF TView`

Scrollable or clipboard TView subclass that hosts a TTextImage, recomputes layout on demand before drawing, and exports Universal Text to the Lisa clipboard.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsPanel: TPanel; itsExtent: LRect): TTextView;` | Initializes a non-printable clipboard or standalone TTextView in itsPanel over itsExtent with a default TPrintManager and valid set to FALSE. |
| `CreateUniversalText` | `PROCEDURE CreateUniversalText; OVERRIDE;` | Serializes the panel's current TTextSelection to the system scrap via TTextWriteUnivText if Universal Text has not yet been generated. |
| `Draw` | `PROCEDURE Draw; OVERRIDE;` | Recomputes textImage layout if valid is FALSE, marks valid TRUE, and draws textImage. |
| `MousePress` | `PROCEDURE MousePress(mouseLPt: LPoint); OVERRIDE;` | Forwards mouse press coordinates mouseLPt to SELF.textImage.MousePress. |

#### `TTextWriteUnivText = SUBCLASS OF TTKWriteUnivText`

Universal Text writer subclass of TTKWriteUnivText that serializes the paragraphs and TStyleChange runs of a TTextSelection onto the system scrap.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsString: TString; itsDataSize: INTEGER; itsTextSel: TTextSelection): TTextWriteUnivText;` | Initializes a TTextWriteUnivText writer positioned at the start of itsTextSel's TTextRange and streams all selected runs to the Lisa scrap. |
| `FillParagraph` | `PROCEDURE FillParagraph; OVERRIDE;` | Fills SELF.data, characterDescriptor, and paragraphDescriptor with the next contiguous TStyleChange run from textSelection during Universal Text export. |

#### `TTextSelection = SUBCLASS OF TSelection`

Abstract base text selection subclass of TSelection representing a highlighted TTextRange or caret in a TTextImage and coordinating typing, clipboard, and typestyle commands.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsView: TView; itsTextImage: TTextImage; itsAnchorLPt: LPoint; beginPara: TEditPara; beginIndex: LONGINT; beginLP: INTEGER; endPara: TEditPara; endIndex: LONGINT; endLP: INTEGER): TTextSelection;` | Initializes a TTextSelection in itsView and itsTextImage with a TTextRange from (beginPara, beginIndex, beginLP) to (endPara, endIndex, endLP) and derives currTypeStyle from context. |
| `KeyText` | `PROCEDURE KeyText;` | Starts an undoable TTypingCmd on the window if amTyping is FALSE so subsequent keystrokes replace the selection. |
| `NewCommand` | `FUNCTION NewCommand(cmdNumber: TCmdNumber): TCommand; OVERRIDE;` | Creates and returns a TStyleCmd, TTextCutCopy, TTextPaste, or TClearTextCmd corresponding to menu command cmdNumber. |
| `NewStyleCmd` | `FUNCTION NewStyleCmd(heap: THeap; cmdNumber: TCmdNumber; textImage: TTextImage): TCommand;` | Creates and returns a TStyleCmd covering SELF.textRange for font or face command cmdNumber. |
| `NewCutCopyCmd` | `FUNCTION NewCutCopyCmd(heap: THeap; cmdNumber: TCmdNumber; textImage: TTextImage): TCommand; DEFAULT;` | Creates and returns a TTextCutCopy command for uCut or uCopy operating on textImage.text. |
| `StyleFromContext` | `PROCEDURE StyleFromContext; DEFAULT;` | Provides a default hook overridden by concrete selection subclasses to set currTypeStyle from the selected text or preceding character. |
| `DoChangeStyle` | `PROCEDURE DoChangeStyle(cmdNumber: TCmdNumber; paragraph: TParagraph; firstLP: INTEGER; lastLP: INTEGER; VAR newStyle: TTypeStyle);` | Applies font family, font size, or face style command cmdNumber to [firstLP, lastLP] of paragraph and returns the resulting style at firstLP in newStyle. |
| `ChangeStyle` | `PROCEDURE ChangeStyle(cmdNumber: TCmdNumber); DEFAULT;` | Provides the default style-change entry point overridden by TOneParaSelection and TMultiParaSelection to apply cmdNumber permanently. |
| `ChangeText` | `PROCEDURE ChangeText(PROCEDURE TextEdit; PROCEDURE Adjust); DEFAULT;` | Marks the current selection changed, executes caller procedures TextEdit and Adjust, and recomputes all TTextImage views unless deferUpdate is set. |
| `CopySelf` | `FUNCTION CopySelf(heap: THeap; view: TView): TMultiParaSelection; DEFAULT;` | Provides a default stub returning NIL, overridden by concrete selections to clone their selected text into a clipboard TMultiParaSelection. |
| `CutCopy` | `PROCEDURE CutCopy(clipSelection: TSelection; deleteOriginal: BOOLEAN); DEFAULT;` | Creates a clipboard TTextView, copies SELF into clipSelection via CopySelf, and deletes the original selection collapsing to a TInsertionPoint when deleteOriginal is TRUE. |
| `DeleteAndFree` | `PROCEDURE DeleteAndFree; DEFAULT;` | Provides a default no-op stub overridden by concrete range selections to delete and free their selected characters and paragraphs. |
| `DeleteButSave` | `FUNCTION DeleteButSave: TText; DEFAULT;` | Provides a default stub returning NIL, overridden by concrete range selections to remove selected text and return it in a saved TText for Undo. |
| `Highlight` | `PROCEDURE Highlight(highTransit: THighTransit); OVERRIDE;` | Highlights or unhighlights SELF.textRange in SELF.textImage's chain according to highTransit. |
| `BecomeInsertionPoint` | `FUNCTION BecomeInsertionPoint: TInsertionPoint;` | Replaces and frees SELF with a TInsertionPoint at the beginning of SELF.textRange and updates selections in other panels. |
| `GetHysteresis` | `PROCEDURE GetHysteresis(VAR hysterPt: Point); OVERRIDE;` | Sets mouse drag hysteresis hysterPt to (0, 0) so text selection tracking responds immediately to single-pixel pointer motion. |
| `MousePress` | `PROCEDURE MousePress(mouseLPt: LPoint); OVERRIDE;` | Extends the selection via MouseMove on Shift-click, or starts a new selection via textImage.MousePress otherwise. |
| `SelSize` | `FUNCTION SelSize: INTEGER; ABSTRACT;` | Abstract method returning the total number of characters in the selection. |
| `Invalidate` | `PROCEDURE Invalidate; DEFAULT;` | Invalidates all TTextImage views displaying SELF.textImage.text. |
| `ReplicateForOtherPanel` | `FUNCTION ReplicateForOtherPanel(itsTextImage: TTextImage): TTextSelection;` | Creates and returns an equivalent TTextSelection over the same TTextRange for another panel's itsTextImage. |

#### `TInsertionPoint = SUBCLASS OF TTextSelection`

Zero-length caret subclass of TTextSelection that manages cursor blinking during idle time and handles character typing, backspacing, forward deletion, return key splits, and pasting.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsView: TView; itsTextImage: TTextImage; itsAnchorLPt: LPoint; itsParagraph: TEditPara; itsIndex: LONGINT; itsLP: INTEGER): TInsertionPoint;` | Initializes a zero-width caret selection at (itsParagraph, itsIndex, itsLP) in itsTextImage, resolving itsIndex if zero and initializing blink state. |
| `IdleBegin` | `PROCEDURE IdleBegin(centiSeconds: LONGINT); OVERRIDE;` | Turns off the insertion caret highlight and schedules the next blink transition time when idle processing begins. |
| `IdleContinue` | `PROCEDURE IdleContinue(centiSeconds: LONGINT); OVERRIDE;` | Toggles the insertion caret highlight on and off whenever centiSeconds passes nextTransitTime during idle time. |
| `IdleEnd` | `PROCEDURE IdleEnd(centiSeconds: LONGINT); OVERRIDE;` | Ensures the insertion caret is left highlighted and disables blinking when idle processing ends. |
| `NewCutCopyCmd` | `FUNCTION NewCutCopyCmd(heap: THeap; cmdNumber: TCmdNumber; textImage: TTextImage): TCommand; OVERRIDE;` | Returns NIL because Cut and Copy commands are not applicable to a zero-length insertion point. |
| `StyleFromContext` | `PROCEDURE StyleFromContext; OVERRIDE;` | Sets currTypeStyle to the TTypeStyle of the character immediately preceding the insertion point (or LP 0 at paragraph start). |
| `CutCopy` | `PROCEDURE CutCopy(clipSelection: TSelection; deleteOriginal: BOOLEAN); OVERRIDE;` | Acts as a no-op override because a zero-length insertion point has no selected text to cut or copy. |
| `FinishPaste` | `PROCEDURE FinishPaste(clipSelection: TSelection; pic: PicHandle);` | Completes a paste at the insertion point by inserting either the clipboard's TMultiParaSelection text or Universal Text from the system scrap. |
| `InsertText` | `PROCEDURE InsertText(text: TText; isParaSelection: BOOLEAN; isWordSelection: BOOLEAN; universalText: BOOLEAN);` | Inserts paragraphs from text (or reads Universal Text runs from TTKReadUnivText when universalText is TRUE) at the insertion point, handling smart word spacing and paragraph splits. |
| `KeyBack` | `PROCEDURE KeyBack(fWord: BOOLEAN); OVERRIDE;` | Deletes the character (or merges with the previous paragraph at LP 0) before the insertion point within a TTypingCmd, tracking recoverable backspaced characters. |
| `KeyChar` | `PROCEDURE KeyChar(ch: CHAR); OVERRIDE;` | Starts a TTypingCmd if needed, inserts ch at newestLP, applies any pending styleCmdNumber typestyle, and advances newestLP. |
| `KeyClear` | `PROCEDURE KeyClear; OVERRIDE;` | Handles the Clear key at an insertion point (no-op or inherited alert since no range is selected). |
| `KeyForward` | `PROCEDURE KeyForward(fWord: BOOLEAN); OVERRIDE;` | Recovers a previously backspaced character at the editing gap when Forward-Backspace is pressed during typing. |
| `MouseMove` | `PROCEDURE MouseMove(mouseLPt: LPoint); OVERRIDE;` | Converts the insertion point into a TOneParaSelection or TMultiParaSelection when the user drags away from anchorLPt. |
| `MousePress` | `PROCEDURE MousePress(mouseLPt: LPoint); OVERRIDE;` | Extends selection on Shift-click, selects the surrounding word into a TOneParaSelection on double-click, or delegates to textImage.MousePress. |
| `MouseRelease` | `PROCEDURE MouseRelease; OVERRIDE;` | Synchronizes the insertion point across other panels viewing the same text and obscures the cursor on mouse release. |

#### `TOneParaSelection = SUBCLASS OF TTextSelection`

Contiguous text selection subclass of TTextSelection spanning characters, a double-clicked word, or a triple-clicked paragraph within a single TEditPara.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsView: TView; itsTextImage: TTextImage; itsAnchorLPt: LPoint; itsParagraph: TEditPara; itsIndex: LONGINT; oldLP: INTEGER; currLP: INTEGER): TOneParaSelection;` | Initializes a single-paragraph text selection on itsParagraph spanning [Min(oldLP, currLP) .. Max(oldLP, currLP)] with anchor oldLP. |
| `StyleFromContext` | `PROCEDURE StyleFromContext; OVERRIDE;` | Sets currTypeStyle to the TTypeStyle at the start LP of the selected range. |
| `CopySelf` | `FUNCTION CopySelf(heap: THeap; view: TView): TMultiParaSelection; OVERRIDE;` | Copies the selected characters and styles of this single-paragraph selection into a new clipboard TText and returns a TMultiParaSelection over it. |
| `DeleteAndFree` | `PROCEDURE DeleteAndFree; OVERRIDE;` | Deletes and frees the selected character span (or entire paragraph if isParaSelection is TRUE) and collapses textRange to firstLP. |
| `DeleteButSave` | `FUNCTION DeleteButSave: TText; OVERRIDE;` | Removes the selected character span (or paragraph) from the document and returns it inside a newly allocated TText for Undo. |
| `MouseMove` | `PROCEDURE MouseMove(mouseLPt: LPoint); OVERRIDE;` | Updates the highlighted selection within the paragraph as mouseLPt moves (honoring word or paragraph selection granularity), promoting to TMultiParaSelection if dragged into another paragraph. |
| `MouseRelease` | `PROCEDURE MouseRelease; OVERRIDE;` | Collapses a zero-width selection into a TInsertionPoint on release, or propagates the selection to other panels viewing the same TText. |

#### `TMultiParaSelection = SUBCLASS OF TTextSelection`

Contiguous text selection subclass of TTextSelection spanning characters or whole paragraphs across multiple TEditPara instances in a TText.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsView: TView; itsTextImage: TTextImage; itsAnchorLPt: LPoint; beginPara: TEditPara; beginIndex: LONGINT; beginLP: INTEGER; endPara: TEditPara; endIndex: LONGINT; endLP: INTEGER; beginIsAnchor: BOOLEAN): TMultiParaSelection;` | Initializes a multi-paragraph selection from (beginPara, beginIndex, beginLP) to (endPara, endIndex, endLP), recording either the beginning or end as the drag anchor. |
| `StyleFromContext` | `PROCEDURE StyleFromContext; OVERRIDE;` | Sets currTypeStyle to the TTypeStyle at firstLP of the first selected paragraph. |
| `CopySelf` | `FUNCTION CopySelf(heap: THeap; view: TView): TMultiParaSelection; OVERRIDE;` | Clones all selected partial and full paragraphs into a new clipboard TText and returns a TMultiParaSelection viewing the copy. |
| `Delete` | `FUNCTION Delete(saveIt: BOOLEAN): TText;` | Deletes all characters and intermediate paragraphs spanned by textRange, merging the remaining prefix of firstPara with the suffix of lastPara and returning the removed TText if saveIt is TRUE. |
| `DeleteAndFree` | `PROCEDURE DeleteAndFree; OVERRIDE;` | Deletes and discards the multi-paragraph selection by calling Delete(FALSE). |
| `DeleteButSave` | `FUNCTION DeleteButSave: TText; OVERRIDE;` | Deletes the multi-paragraph selection and returns the removed paragraphs in a TText object by calling Delete(TRUE). |
| `MouseMove` | `PROCEDURE MouseMove(mouseLPt: LPoint); OVERRIDE;` | Extends or shrinks the highlighted selection across paragraphs as mouseLPt moves relative to anchorPara, honoring character, word, or paragraph granularity. |
| `MouseRelease` | `PROCEDURE MouseRelease; OVERRIDE;` | Demotes the selection to a TInsertionPoint or TOneParaSelection if it ended within a single paragraph, or synchronizes other panels otherwise. |

#### `TClearTextCmd = SUBCLASS OF TCommand`

Undoable command subclass of TCommand that deletes the currently selected text for the Clear key or menu item while saving the removed TText for Undo.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsCmdNumber: TCmdNumber; itsImage: TImage; itsText: TText): TClearTextCmd;` | Initializes an undoable TClearTextCmd for itsCmdNumber (uClear) operating on itsImage and itsText. |
| `Free` | `PROCEDURE Free; OVERRIDE;` | Frees any savedText shell without double-freeing active document paragraphs and frees the TClearTextCmd. |
| `Commit` | `PROCEDURE Commit; OVERRIDE;` | Permanently frees savedText when the Clear command is committed and can no longer be undone. |
| `Perform` | `PROCEDURE Perform(cmdPhase: TCmdPhase); OVERRIDE;` | Saves and deletes the selected text into an insertion point on doPhase/redoPhase, or reinserts savedText on undoPhase. |

#### `TStyleCmd = SUBCLASS OF TCommand`

Undoable command subclass of TCommand that previews and commits font family, font size, or face attribute changes across a TTextSelection using paragraph object filtering.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsCmdNumber: TCmdNumber; itsImage: TImage; itsFirstIndex: LONGINT; itsLastIndex: LONGINT; itsLPFirst: INTEGER; itsLPLast: INTEGER; itsSelection: TTextSelection): TStyleCmd;` | Initializes an undoable TStyleCmd for font/face command itsCmdNumber over paragraph indices [itsFirstIndex..itsLastIndex] and LPs [itsLPFirst..itsLPLast]. |
| `Free` | `PROCEDURE Free; OVERRIDE;` | Clears the beingFiltered flag on all affected paragraphs, frees the cloned textSelection and temporary filteredStyles array, and frees the command. |
| `Commit` | `PROCEDURE Commit; OVERRIDE;` | Permanently applies cmdNumber to textSelection via ChangeStyle when the style command is committed. |
| `FilterAndDo` | `PROCEDURE FilterAndDo(actualObject: TObject; PROCEDURE DoToObject(filteredObject: TObject)); OVERRIDE;` | Temporarily substitutes previewed TStyleChange runs onto a paragraph whose beingFiltered flag is set while invoking DoToObject on its TParaImage. |
| `Perform` | `PROCEDURE Perform(cmdPhase: TCmdPhase); OVERRIDE;` | Toggles beingFiltered on the target paragraphs for doPhase, undoPhase, and redoPhase, updates currTypeStyle, and recomputes affected TTextImage views. |

#### `TTextCutCopy = SUBCLASS OF TCutCopyCommand`

Undoable clipboard command subclass of TCutCopyCommand that copies or cuts a TTextSelection into a clipboard TTextView.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsCmdNumber: TCmdNumber; itsImage: TImage; isCutCmd: BOOLEAN; itsText: TText): TTextCutCopy;` | Initializes a TTextCutCopy command for uCut or uCopy on itsImage and itsText, preserving selection highlighting during Copy. |
| `Free` | `PROCEDURE Free; OVERRIDE;` | Frees any saved Undo text and frees the TTextCutCopy command. |
| `DoCutCopy` | `PROCEDURE DoCutCopy(clipSelection: TSelection; deleteOriginal: BOOLEAN; cmdPhase: TCmdPhase); OVERRIDE;` | Copies the selected text to clipSelection (deleting and saving it for Undo when deleteOriginal is TRUE), and restores or removes it on undoPhase/redoPhase. |

#### `TTextPaste = SUBCLASS OF TPasteCommand`

Undoable clipboard command subclass of TPasteCommand that replaces the current TTextSelection with pasted TText paragraphs or Universal Text from the scrap.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsImage: TImage; itsText: TText): TTextPaste;` | Initializes an undoable uPaste command for itsImage and itsText with an empty pasteRange. |
| `Free` | `PROCEDURE Free; OVERRIDE;` | Frees any savedText shell and pasteRange before freeing the TTextPaste command. |
| `Commit` | `PROCEDURE Commit; OVERRIDE;` | Frees savedText permanently when the Paste command is committed. |
| `DoPaste` | `PROCEDURE DoPaste(clipSelection: TSelection; pic: PicHandle; cmdPhase: TCmdPhase); OVERRIDE;` | Replaces the current selection (saving deleted text in savedText) with pasted clipboard or Universal Text content on doPhase, and reverses or reapplies the edit on undoPhase/redoPhase. |

#### `TTypingCmd = SUBCLASS OF TCommand`

Undoable command subclass of TCommand that records a sequence of typed characters, backspaces, forward deletes, and paragraph breaks at a TInsertionPoint.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; heap: THeap; itsImage: TImage; itsText: TText): TTypingCmd;` | Initializes an undoable uTyping command for itsImage and itsText with a typingRange tracker and zeroed character/paragraph counters. |
| `Free` | `PROCEDURE Free; OVERRIDE;` | Frees savedText, detaches typingCmd from any active TInsertionPoint, frees typingRange and otherInsPts list shell, and frees the command. |
| `Commit` | `PROCEDURE Commit; OVERRIDE;` | Closes the active editing gap on the typed paragraph, clears typing state on the TInsertionPoint, and frees savedText. |
| `Perform` | `PROCEDURE Perform(cmdPhase: TCmdPhase); OVERRIDE;` | Deletes and saves any initial range selection into a TInsertionPoint to begin typing on doPhase, or swaps the typed range and savedText on undoPhase and redoPhase. |

---

## Unit UTKUniversalText

Provides the Lisa Toolkit Universal Text stream interface (UTKUniversalText) for reading and writing formatted character runs, paragraph margins, and tab descriptors to and from the Lisa system scrap.

- **Import**: `USES UTKUniversalText;`
- **Unit kind**: `INTRINSIC` (`UTKUNIVE`)
- **Interface dependencies**: `UObject`, `UnitStd`, `UnitHz`, `QuickDraw`, `FontMgr`, `SysCall`, `PMDecl`, `PrStdInfo`, `UnitFmt`, `UnitCs`, `Events`, `Scrap`

### Clascal Classes

#### `TTKUnivText = SUBCLASS OF TOBJECT`

Base Toolkit Universal Text stream subclass of TObject holding current TParaDescriptor, TCharDescriptor, and TString run buffers along with conversions to and from internal UnitCS stream descriptors.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; itsHeap: THeap; itsTString: TString; itsDataSize: INTEGER): TTKUnivText;` | Initializes a TTKUnivText stream object on itsHeap using caller buffer itsTString (or allocating an owned TString of itsDataSize if NIL) and a tabTable TArray. |
| `Free` | `PROCEDURE Free; OVERRIDE;` | Frees SELF.data if allocated internally (itsOurTString), frees paragraphDescriptor.tabTable, and frees the TTKUnivText object. |
| `RunToStream` | `PROCEDURE RunToStream;` | Converts SELF.characterDescriptor and SELF.paragraphDescriptor (including tab stops) into the internal UnitCS logical paragraph descriptor (LPD) for writing to the stream. |
| `StreamToTRun` | `PROCEDURE StreamToTRun;` | Populates SELF.characterDescriptor and SELF.paragraphDescriptor (including margins, alignment, spacing, and tabs) from the current internal UnitCS stream LPD. |
| `TabTableToArgTbd` | `PROCEDURE TabTableToArgTbd;` | Copies tab stop entries from paragraphDescriptor.tabTable into the internal UnitCS argTbd array in the current paragraph descriptor. |
| `ArgTbdToTabTable` | `PROCEDURE ArgTbdToTabTable;` | Populates paragraphDescriptor.tabTable with TTabDescriptor records converted from the internal UnitCS argTbd tab array. |

#### `TTKReadUnivText = SUBCLASS OF TTKUnivText`

Universal Text reader subclass of TTKUnivText that sequentially reads formatted character runs, tab-delimited table fields, lines, and paragraph descriptors from the system scrap.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; itsHeap: THeap; itsTString: TString; itsDataSize: INTEGER; LevelOfGranularity: TLevelOfGranularity): TTKReadUnivText;` | Opens the system scrap for Universal Text reading at the requested character/paragraph LevelOfGranularity, allocates an internal read buffer, and positions at the start via Restart. |
| `Free` | `PROCEDURE Free; OVERRIDE;` | Frees the internal lookahead TString buffer and invokes SUPERSELF.Free. |
| `ReadRun` | `PROCEDURE ReadRun;` | Reads the next uniform character/paragraph run from the system scrap into SELF.data and updates characterDescriptor and paragraphDescriptor. |
| `Restart` | `PROCEDURE Restart;` | Resets the Universal Text stream position and column counter to read from the beginning of the scrap. |
| `ScanTable` | `PROCEDURE ScanTable(VAR rows, tabColumns, tabStopColumns: INTEGER);` | Scans the entire Universal Text scrap from the beginning to count and return the number of carriage-return rows, tab-delimited columns, and tab-stop columns. |
| `ReadField` | `FUNCTION ReadField(maxFieldSize: INTEGER; VAR fieldOverflow: BOOLEAN; VAR fieldTerminator: CHAR; VAR tabType: TTabTypes): BOOLEAN;` | Reads the next tab- or return-delimited field (up to maxFieldSize characters) into SELF.data, reporting overflow, the terminating character, and the active TTabTypes alignment, or returns FALSE at end of scrap. |
| `ReadLine` | `FUNCTION ReadLine(maxLineSize: INTEGER; VAR lineOverflow: BOOLEAN; VAR lineTerminator: CHAR): BOOLEAN;` | Reads the next carriage-return-terminated line (up to maxLineSize characters) into SELF.data, reporting lineOverflow and lineTerminator, or returns FALSE at end of scrap. |
| `GetParaPicture` | `FUNCTION GetParaPicture(heap: THeap): PicHandle;` | Returns a QuickDraw PicHandle copied into heap for the current paragraph if associated picture data exists (stubbed to return NIL in Workshop 3.0). |

#### `TTKWriteUnivText = SUBCLASS OF TTKUnivText`

Universal Text writer subclass of TTKUnivText that binds to the system scrap and invokes subclass FillParagraph callbacks to serialize formatted text runs.

| Method | Signature | Description |
|---|---|---|
| `CREATE` | `FUNCTION CREATE(object: TObject; itsHeap: THeap; itsTString: TString; itsDataSize: INTEGER): TTKWriteUnivText;` | Initializes a Universal Text scrap writer, binds a UnitCS character stream invoking FillParagraph callbacks, writes the stream to the system scrap via PutCsScrap, and closes the scrap. |
| `FillParagraph` | `PROCEDURE FillParagraph;` | Abstract hook invoked repeatedly during scrap serialization for subclasses to supply the next run of characters and descriptors in SELF.data (calls ABCBreak if not overridden). |
