# `SULIB` (`SUlib.obj`) — Workshop Standard Utility & Shell Communication Library

[Back to Library Index](LIBRARIES.md)

Lisa Workshop utility units providing string/byte manipulation, raw console and serial I/O primitives, Workshop shell communication, and inter-program parameter passing.

- **Object file**: `libs/workshop3.0/SUlib.obj` (Intrinsic library)
- **Contents**: 4 units, 87 top-level procedures/functions

## Importing and Linking

```pascal
USES IOPrimitives, ProgComm, ShellComm;
```

```sh
pascal/lpc.py --link=IOSPASLIB,SULIB MYPROG
```

## Units in This Library

| Unit | 8-Char Symbol | `USES` Dependencies | Routines | Summary |
|---|---|---|---|---|
| [`IOPrimitives`](#unit-ioprimitives) | `IOPRIMIT` | `StdUnit` | 22 | Implements buffered, block-oriented text and file I/O primitives for Lisa Workshop command-line tools, supporting 1 KB paged Lisa `.TEXT` files with DLE blank compression, nested include-file input stacks, system-volume file lookup, and formatted string/integer line output. |
| [`ProgComm`](#unit-progcomm) | `PROGCOMM` | `StdUnit`, `ShellComm` | 11 | Provides the client-side inter-program communication interface for Lisa Workshop tools, allowing a running program to read or write a keyed 1024-byte shared text buffer (`ShellComm`), schedule the next Workshop Shell command, return status strings, and query or update Shell flags. |
| [`ShellComm`](#unit-shellcomm) | `SHELLCOM` | `StdUnit` | 12 | Implements the shared intrinsic (`INTRINSIC SHARED`) storage and routines backing `ProgComm` and the Lisa Workshop Shell, maintaining the 1024-byte inter-tool text buffer, chained run-command string, return string, and Exec/editor state flags across processes. |
| [`StdUnit`](#unit-stdunit) | `STDUNIT` | `SysCall`, `PasLibCall`, `PPasLibC` | 42 | Provides standard utility routines for Lisa Workshop tools, including ASCII case conversion, string trimming and bounded concatenation, Lisa `-volume-catalog/file.ext` pathname parsing, interactive console prompts with default/escape handling, OS error-message file lookup, Exec script control, and integer/string conversions. |

---

## Unit IOPrimitives

Implements buffered, block-oriented text and file I/O primitives for Lisa Workshop command-line tools, supporting 1 KB paged Lisa `.TEXT` files with DLE blank compression, nested include-file input stacks, system-volume file lookup, and formatted string/integer line output.

- **Import**: `USES IOPrimitives;`
- **Unit kind**: `INTRINSIC` (`IOPRIMIT`)
- **Interface dependencies**: `StdUnit`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `InitIO` | `PROCEDURE InitIO;` | Initializes `IOPrimitives` internal state, line counters, control characters, and file-extension flags before any I/O operations. |
| `EndIO` | `PROCEDURE EndIO;` | Flushes and closes all open files managed by `IOPrimitives` prior to program exit. |
| `OpenF` | `FUNCTION OpenF(Fname: SUStr; VAR FCB: IOFCBP; Mode: IOModes; Bufr: IOBufrP): Integer;` | Opens disk file or device `Fname` in `IORead` or `IOWrite` `Mode` using file control block `FCB` and 3072-byte buffer `Bufr` (allocating private ones on the heap if `NIL`), returning the `IOResult` status. |
| `CreateF` | `FUNCTION CreateF(Fname: SUStr; VAR FCB: IOFCBP; Bufr: IOBufrP): Integer;` | Creates and opens output file `Fname` in `IOWrite` mode using `FCB` and `Bufr`, returning the `IOResult` status. |
| `SysOpenF` | `FUNCTION SysOpenF(Fname: SUStr; VAR FCB: IOFCBP; Mode: IOModes; Bufr: IOBufrP): Integer;` | Opens volume-less system file `Fname` in `Mode` by searching the current prefix, OS boot volume, and current process volume in order, returning the `IOResult` status. |
| `CloseF` | `PROCEDURE CloseF(FCB: IOFCBP; CloseKind: IOCloseKind);` | Flushes buffered output and closes `FCB` with disposition `CloseKind` (`IONormal`, `IOLock`, `IOPurge`, `IOCrunch`), or closes all `IOPrimitives` files when `FCB` is `NIL`. |
| `PushInput` | `FUNCTION PushInput(Fname: SUStr): Integer;` | Pushes the current input file (`IOCurrFCB`) onto the include-file stack (up to `IOIncMax = 5` levels) and opens `Fname` as the active input file, returning the `IOResult` status. |
| `PopInput` | `FUNCTION PopInput: Boolean;` | Closes the current pushed include file and restores the previous input file and block position from the include stack, returning `FALSE` on reread error. |
| `NextPage` | `PROCEDURE NextPage(FCB: IOFCBP);` | Advances `FCB^.BufrCp` up to the next 1024-byte Lisa `.TEXT` page boundary, refilling the input buffer if needed. |
| `FillBufr` | `PROCEDURE FillBufr(FCB: IOFCBP);` | Refills `FCB^.Bufr` with the next sequential chunk of up to `IOBlkSize` (6) 512-byte disk blocks from `FCB`. |
| `SeekBlock` | `PROCEDURE SeekBlock(FCB: IOFCBP; Block: Integer);` | Positions input file `FCB` to 512-byte block `Block` and refills `FCB^.Bufr` starting at that block. |
| `FilePosition` | `PROCEDURE FilePosition(FCB: IOFCBP; VAR Block, Byte: Integer);` | Returns the current 512-byte `Block` index and `Byte` offset within that block for open file `FCB`. |
| `GetcF` | `FUNCTION GetcF(FCB: IOFCBP; VAR c: Char): Char;` | Reads and returns the next character from `FCB` (also storing it in `c`), automatically expanding DLE leading-space codes, skipping page-padding NULs, and refilling the buffer. |
| `GetLine` | `FUNCTION GetLine(FCB: IOFCBP; Line: IOStrP): Boolean;` | Reads the next DLE-expanded text line (up to `IOMaxStr = 132` characters) from `FCB` into `Line^`, returning `FALSE` at end of file. |
| `PutcF` | `PROCEDURE PutcF(FCB: IOFCBP; c: Char);` | Appends character `c` to `FCB`'s output line buffer, DLE-compressing leading blanks and transferring the line into the 1024-byte paged output buffer when `IONewline` is written. |
| `PutLineP` | `PROCEDURE PutLineP(FCB: IOFCBP; Line: IOStrP);` | Writes the string pointed to by `Line` followed by an `IONewline` character to output file `FCB`. |
| `PutLineS` | `PROCEDURE PutLineS(FCB: IOFCBP; Line: IOStr);` | Writes string value `Line` followed by an `IONewline` character to output file `FCB`. |
| `PutStrP` | `PROCEDURE PutStrP(FCB: IOFCBP; S: IOStrP; Width: Integer);` | Writes string `S^` to output file `FCB` in a field of `Width` characters (full string if `0`, right-justified if `> 0`, left-justified if `< 0`, or truncated to `\|Width\|` if shorter than `S^`). |
| `PutStrS` | `PROCEDURE PutStrS(FCB: IOFCBP; S: IOStr; Width: Integer);` | Writes string value `S` to output file `FCB` in a field of `Width` characters (full string if `0`, right-justified if `> 0`, left-justified if `< 0`, or truncated to `\|Width\|` if shorter than `S`). |
| `PutIntP` | `FUNCTION PutIntP(N: LongInt; Width: Integer): IOStrP;` | Formats 32-bit integer `N` into a static string buffer of width `Width` (space-padded when `Width > 0`, leading-zero-padded after any sign when `Width < 0`) and returns a pointer (`IOStrP`) to it. |
| `IOError` | `FUNCTION IOError(IOStatus: Integer; Msg: SUStr): Boolean;` | Returns `FALSE` when `IOStatus <= 0`; when `IOStatus > 0`, prints `Msg` and the corresponding OS or `IOPrimitives` error description to the console and returns `TRUE`. |
| `SysReset` | `FUNCTION SysReset(F: IOTextP; FN: SUStr): Integer;` | Opens Pascal `Text` file `F^` for input on volume-less filename `FN` by trying the current prefix, boot volume, and process volume in order, returning the `IOResult` status. |

---

## Unit ProgComm

Provides the client-side inter-program communication interface for Lisa Workshop tools, allowing a running program to read or write a keyed 1024-byte shared text buffer (`ShellComm`), schedule the next Workshop Shell command, return status strings, and query or update Shell flags.

- **Import**: `USES ProgComm;`
- **Unit kind**: `INTRINSIC` (`PROGCOMM`)
- **Interface dependencies**: `StdUnit`, `ShellComm`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `PCInit` | `PROCEDURE PCInit;` | Initializes `ProgComm` state and sets `PCBufrPtr` to point to the shared 1024-byte inter-program communication buffer. |
| `PCSetRunCmd` | `PROCEDURE PCSetRunCmd(RC: SUStr);` | Schedules Workshop command line `RC` via `ShellComm` to be executed automatically when the current program exits. |
| `PCSetRetStr` | `PROCEDURE PCSetRetStr(RS: SUStr);` | Sets return string `RS` in `ShellComm` to pass a status or result value back to the Workshop Shell or active Exec script. |
| `PCReWrite` | `PROCEDURE PCReWrite(WriteType: INTEGER; Key: SUStr);` | Clears and opens the shared 1024-byte program-communication buffer for writing under format `WriteType` (`PCText`, `PCAny`, `PCNone`) and tag `Key`. |
| `PCReset` | `FUNCTION PCReset(ReadType: INTEGER; Key: SUStr): BOOLEAN;` | Opens the shared program-communication buffer for reading from byte 0 if its current payload matches `ReadType` and owner tag `Key`, returning `TRUE` on match. |
| `PCClose` | `FUNCTION PCClose(KillBufr: BOOLEAN; Key: SUStr): BOOLEAN;` | Closes the shared program-communication buffer associated with `Key`, clearing and invalidating the buffer if `KillBufr` is `TRUE`. |
| `PCPutCh` | `FUNCTION PCPutCh(Ch: CHAR): BOOLEAN;` | Appends character `Ch` to the shared program-communication buffer, returning `FALSE` if the 1024-byte capacity is exceeded. |
| `PCGetCh` | `FUNCTION PCGetCh(VAR Ch: CHAR): BOOLEAN;` | Reads the next character from the shared program-communication buffer into `Ch`, returning `FALSE` when no unread characters remain. |
| `PCPutLine` | `FUNCTION PCPutLine(L: SUStr): BOOLEAN;` | Appends string `L` followed by a carriage return (`#13`) to the shared program-communication buffer, returning `FALSE` if it does not fit. |
| `PCGetLine` | `FUNCTION PCGetLine(VAR L: SUStr): BOOLEAN;` | Reads the next carriage-return-delimited line from the shared program-communication buffer into `L`, returning `FALSE` at end of buffer. |
| `PCShellCmd` | `FUNCTION PCShellCmd(Cmd: INTEGER; P: SUStrP): BOOLEAN;` | Invokes Workshop Shell state command `Cmd` (such as getting or setting `ReallyStop` or `UnSavedEdits` flags) with optional string parameter `P`. |

---

## Unit ShellComm

Implements the shared intrinsic (`INTRINSIC SHARED`) storage and routines backing `ProgComm` and the Lisa Workshop Shell, maintaining the 1024-byte inter-tool text buffer, chained run-command string, return string, and Exec/editor state flags across processes.

- **Import**: `USES ShellComm;`
- **Unit kind**: `INTRINSIC SHARED` (`SHELLCOM`)
- **Interface dependencies**: `StdUnit`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `SCInit` | `PROCEDURE SCInit;` | Initializes the shared `ShellComm` buffer (`SCBufr`), command/return strings (`SCRunCmnd`, `SCRetStr`), and Exec/editor state flags. |
| `SCSetRunCmd` | `PROCEDURE SCSetRunCmd(RC: SUStr);` | Stores Workshop command string `RC` into shared variable `SCRunCmnd` so the Shell runs that command next. |
| `SCSetRetStr` | `PROCEDURE SCSetRetStr(RS: SUStr);` | Stores tool return string `RS` into shared variable `SCRetStr` for retrieval by the Workshop Shell or Exec processor. |
| `SCSetExecAbort` | `PROCEDURE SCSetExecAbort(B: BOOLEAN);` | Sets shared flag `SCExecAbort` to `B` to indicate whether the Workshop Shell should abort an active Exec file. |
| `SCReWrite` | `PROCEDURE SCReWrite(WriteType: INTEGER; Key: SUStr);` | Resets the shared 1024-byte `SCBufr` for writing with content kind `WriteType` (`SCText`, `SCAny`, `SCNone`) and owner `Key`. |
| `SCReset` | `FUNCTION SCReset(ReadType: INTEGER; Key: SUStr): BOOLEAN;` | Rewinds `SCBufr` for reading if its stored content kind matches `ReadType` and its owner tag matches `Key`, returning `TRUE` on success. |
| `SCClose` | `FUNCTION SCClose(KillBufr: BOOLEAN; Key: SUStr): BOOLEAN;` | Finalizes reading or writing `SCBufr` under tag `Key`, discarding and clearing the buffer contents when `KillBufr` is `TRUE`. |
| `SCPutCh` | `FUNCTION SCPutCh(Ch: CHAR): BOOLEAN;` | Appends character `Ch` to the shared 1024-byte `SCBufr` buffer, returning `FALSE` if the buffer is full. |
| `SCGetCh` | `FUNCTION SCGetCh(VAR Ch: CHAR): BOOLEAN;` | Reads the next character from `SCBufr` into `Ch`, returning `FALSE` when the end of written data is reached. |
| `SCPutLine` | `FUNCTION SCPutLine(L: SUStr): BOOLEAN;` | Appends string `L` and a trailing carriage return (`#13`) to `SCBufr`, returning `FALSE` if insufficient buffer space remains. |
| `SCGetLine` | `FUNCTION SCGetLine(VAR L: SUStr): BOOLEAN;` | Extracts the next carriage-return-terminated line from `SCBufr` into `L`, returning `FALSE` when no unread data remains. |
| `SCShellCmd` | `FUNCTION SCShellCmd(Cmd: INTEGER; P: SUStrP): BOOLEAN;` | Executes shared Workshop Shell flag command `Cmd` (`SC_SetReallyStop`, `SC_GetReallyStop`, `SC_SetUnSavedEdits`, `SC_GetUnSavedEdits`) using parameter `P`. |

---

## Unit StdUnit

Provides standard utility routines for Lisa Workshop tools, including ASCII case conversion, string trimming and bounded concatenation, Lisa `-volume-catalog/file.ext` pathname parsing, interactive console prompts with default/escape handling, OS error-message file lookup, Exec script control, and integer/string conversions.

- **Import**: `USES StdUnit;`
- **Unit kind**: `INTRINSIC` (`STDUNIT`)
- **Interface dependencies**: `SysCall`, `PasLibCall`, `PPasLibC`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `SUInit` | `PROCEDURE SUInit;` | Initializes `StdUnit` control-character globals (`SUBell`, `SUBackSpace`, `SUCr`, `SUTab`, `SUEsc`, `SUDle`, `SUNul`), `SUNullS`, and the `SUKeyBoard` input file. |
| `SUDone` | `PROCEDURE SUDone;` | Closes `SUKeyBoard` and cleans up `StdUnit` resources before tool termination. |
| `SUUpCh` | `FUNCTION SUUpCh(Ch: CHAR): CHAR;` | Converts ASCII lowercase character `Ch` (`'a'..'z'`) to uppercase and returns all other characters unchanged. |
| `SULowCh` | `FUNCTION SULowCh(Ch: CHAR): CHAR;` | Converts ASCII uppercase character `Ch` (`'A'..'Z'`) to lowercase and returns all other characters unchanged. |
| `SUUpStr` | `PROCEDURE SUUpStr(S: SUStrP);` | Converts all ASCII lowercase letters in string `S^` to uppercase in place. |
| `SULowStr` | `PROCEDURE SULowStr(S: SUStrP);` | Converts all ASCII uppercase letters in string `S^` to lowercase in place. |
| `SUEqStr` | `FUNCTION SUEqStr(S1: SUStrP; S2: SUStrP): BOOLEAN;` | Performs a case-insensitive comparison of `S1^` and `S2^` and returns `TRUE` if both strings match. |
| `SUEq2Str` | `FUNCTION SUEq2Str(S1: SUStrP; S2: SUStr): BOOLEAN;` | Performs a case-insensitive comparison of string pointer `S1^` and string value `S2` and returns `TRUE` if they match. |
| `SUTrimLeading` | `PROCEDURE SUTrimLeading(S: SUStrP);` | Deletes all leading space and tab characters from string `S^` in place. |
| `SUTrimTrailing` | `PROCEDURE SUTrimTrailing(S: SUStrP);` | Deletes all trailing space and tab characters from string `S^` in place. |
| `SUTrimBlanks` | `PROCEDURE SUTrimBlanks(S: SUStrP);` | Deletes both leading and trailing space and tab characters from string `S^` in place. |
| `SUAddCh` | `PROCEDURE SUAddCh(S: SUStrP; Ch: CHAR; MaxStrLeng: INTEGER; VAR OverFlow: BOOLEAN);` | Appends character `Ch` to `S^` if `Length(S^) < MaxStrLeng`, setting `OverFlow` to `TRUE` if no room remains. |
| `SUConcat` | `PROCEDURE SUConcat(S1: SUStrP; S2: SUStrP);` | Concatenates string `S2^` onto the end of `S1^` in place. |
| `SUAddStr` | `PROCEDURE SUAddStr(S1: SUStrP; S2: SUStrP; MaxStrLeng: INTEGER; VAR OverFlow: BOOLEAN);` | Appends `S2^` onto `S1^` when `Length(S1^) + Length(S2^) <= MaxStrLeng`, setting `OverFlow` to `TRUE` otherwise. |
| `SUSetStr` | `PROCEDURE SUSetStr(Dest: SUStrP; Src: SUStrP);` | Copies string `Src^` into destination string `Dest^`. |
| `SUCopyStr` | `PROCEDURE SUCopyStr(Dest: SUStrP; Src: SUStrP; Start, Count: INTEGER);` | Copies up to `Count` characters starting at 1-based position `Start` of `Src^` into `Dest^`. |
| `SUIsVolName` | `FUNCTION SUIsVolName(FN: SUStrP): BOOLEAN;` | Returns `TRUE` if `FN^` has the form of a bare Lisa volume prefix (starts with `'-'` and contains no second `'-'`). |
| `SUVolPart` | `PROCEDURE SUVolPart(PathN: SUStrP; VolN: SUStrP);` | Extracts the leading Lisa volume/catalog prefix (such as `-vol-` or directory path) from `PathN^` into `VolN^`. |
| `SUAddExtension` | `PROCEDURE SUAddExtension(FN: SUStrP; DefExt: SUStr; MaxStrLeng: INTEGER; VAR OverFlow: BOOLEAN);` | Appends default extension `DefExt` to `FN^` unless `FN^` already ends with `DefExt` (case-insensitively) or ends with a literal `'.'` (which is stripped), setting `OverFlow` if `MaxStrLeng` would be exceeded. |
| `SUSplitFN` | `PROCEDURE SUSplitFN(PathN: SUStrP; CatN: SUStrP; FN: SUStrP; Ext: SUStrP);` | Splits pathname `PathN^` into its volume/catalog prefix `CatN^`, base filename `FN^`, and dot extension `Ext^`. |
| `SUMakeFN` | `PROCEDURE SUMakeFN(PathN: SUStrP; CatN: SUStrP; FN: SUStrP; Ext: SUStr; VAR OverFlow: BOOLEAN);` | Concatenates catalog prefix `CatN^`, base filename `FN^`, and extension `Ext` into `PathN^`, setting `OverFlow` if the result exceeds `SUMaxStrLeng`. |
| `SUChkFN` | `PROCEDURE SUChkFN(FN: SUStrP; VAR PState: PromptState; DefVol: SUStr; DefFN: SUStr; DefExt: SUStr);` | Trims and validates filename response `FN^`, applying defaults (`DefVol`, `DefFN`, `DefExt`) and setting `PState` (`SUDefault`, `SUNone`, `SUOptions` for `'?'`, `SUEscape`, `SUValid`, or `SUInvalid`). |
| `SUGetCh` | `PROCEDURE SUGetCh(VAR Ch: CHAR);` | Reads a single unbuffered character from `SUKeyBoard` (or standard input) into `Ch`. |
| `SUGetLine` | `PROCEDURE SUGetLine(S: SUStrP; VAR PState: PromptState);` | Reads an interactive response line from the console into `S^` and sets `PState` to `SUEscape`, `SUNone`, or `SUValid`. |
| `SUGetStr` | `PROCEDURE SUGetStr(S: SUStrP; VAR PState: PromptState; DefVal: SUStr);` | Reads an interactive line into `S^`, substituting `DefVal` and `PState = SUDefault` when an empty line is entered. |
| `SUGetFN` | `PROCEDURE SUGetFN(FN: SUStrP; VAR PState: PromptState; DefVol: SUStr; DefFN: SUStr; DefExt: SUStr);` | Reads a filename line from the console into `FN^` and validates/completes it via `SUChkFN` with `DefVol`, `DefFN`, and `DefExt`. |
| `SUGetInt` | `PROCEDURE SUGetInt(VAR I: INTEGER; VAR PState: PromptState; DefVal: INTEGER);` | Reads a console line and parses a 16-bit integer into `I` (or assigns `DefVal` with `SUDefault` if empty), setting `PState` accordingly. |
| `SUWaitEscOrSp` | `PROCEDURE SUWaitEscOrSp(VAR PState: PromptState);` | Waits for the user to press Space (`PState = SUValid`) or Escape/Clear (`PState = SUEscape`). |
| `SUWaitSp` | `PROCEDURE SUWaitSp;` | Pauses execution until the user presses the Space bar (or Escape). |
| `SUGetChInSet` | `PROCEDURE SUGetChInSet(VAR Ch: CHAR; Chars: SUSetOfChar);` | Repeatedly reads keyboard characters until one belonging to set `Chars` is typed, returning it in `Ch`. |
| `SUGetYesNo` | `FUNCTION SUGetYesNo: BOOLEAN;` | Reads a yes/no response from the console and returns `TRUE` for `'Y'`/`'y'` and `FALSE` for `'N'`/`'n'`. |
| `SUGetBool` | `FUNCTION SUGetBool(Default: BOOLEAN): BOOLEAN;` | Reads a boolean response from the console, returning `Default` on empty input or `TRUE` when the response starts with `'Y'` or `'T'` (case-insensitively). |
| `SUGetErrText` | `PROCEDURE SUGetErrText(ErrFN: SUStr; ErrN: INTEGER; ErrMsg: SUStrP; VAR ErrRet: ErrTextRet);` | Looks up error number `ErrN` in Lisa Workshop error message file `ErrFN`, returning the message in `ErrMsg^` and lookup status (`SUOk`, `SUBadEFOpen`, `SUBadEFRead`, `SUErrNNotFound`) in `ErrRet`. |
| `SUErrText` | `PROCEDURE SUErrText(ErrFN: SUStr; ErrN: INTEGER; ErrMsg: SUStrP);` | Looks up error `ErrN` in error file `ErrFN` and stores its text (or a fallback `'Error <ErrN>'` message on lookup failure) in `ErrMsg^`. |
| `SUStopExec` | `PROCEDURE SUStopExec(VAR ErrNum: INTEGER);` | Aborts any active Workshop Exec script with a diagnostic message and returns the resulting OS error code in `ErrNum`. |
| `SUCloseExec` | `PROCEDURE SUCloseExec(VAR ErrNum: INTEGER);` | Terminates any active Workshop Exec script without reporting an error and restores console input, returning the OS status in `ErrNum`. |
| `SUInitSysVols` | `PROCEDURE SUInitSysVols;` | Queries Lisa OS to initialize global volume-name strings `SUOsBootV` (boot volume) and `SUMyProcV` (current process program volume). |
| `SUSysReset` | `PROCEDURE SUSysReset(F: SUFileP; FN: SUStr; VAR IOStatus: INTEGER);` | Opens untyped file `F^` on volume-less system file `FN` by searching the current prefix, boot volume, and process volume in order, returning `IOResult` in `IOStatus`. |
| `SUIntToStr` | `PROCEDURE SUIntToStr(N: INTEGER; S: SUStrP);` | Converts 16-bit signed integer `N` into its decimal ASCII string representation in `S^`. |
| `SULIntToStr` | `PROCEDURE SULIntToStr(N: LONGINT; S: SUStrP);` | Converts 32-bit signed integer `N` into its decimal ASCII string representation in `S^`. |
| `SUStrToInt` | `PROCEDURE SUStrToInt(NS: SUStrP; VAR N: INTEGER; VAR CState: ConvNState);` | Parses decimal string `NS^` (ignoring leading/trailing whitespace) into 16-bit integer `N` and sets `CState` (`SUValidN`, `SUNoN`, `SUBadN`, `SUNOverFlow`). |
| `SUStrToLInt` | `PROCEDURE SUStrToLInt(NS: SUStrP; VAR N: LONGINT; VAR CState: ConvNState);` | Parses decimal string `NS^` (ignoring leading/trailing whitespace) into 32-bit `LONGINT` `N` and sets `CState` (`SUValidN`, `SUNoN`, `SUBadN`, `SUNOverFlow`). |
