# `PASLIBCALL` (`PASLIBCALL.obj`) — Lisa Pascal 2.0 Runtime Configuration Calls

[Back to Library Index](LIBRARIES.md)

User-callable Pascal runtime configuration routines for heap sizing, console screen control, key-press polling (`PKeyPress`), character translation, and abort-key status.

- **Object file**: `libs/workshop2.0/PASLIBCALL.obj` (Plain unit (`.obj`))
- **Contents**: 1 unit, 5 procedures/functions

## Importing and Linking

```pascal
USES {$U PasLibCall.obj} PasLibCall;
```

```sh
LISA_BOOT=libs/workshop2.0 pascal/lpc.py --2.0 --link=IOSPASLIB,PASLIBCALL MYPROG
```

## Units in This Library

| Unit | 8-Char Symbol | `USES` Dependencies | Routines | Summary |
|---|---|---|---|---|
| [`PasLibCall`](#unit-paslibcall) | `PASLIBCA` | `SysCall` | 5 | Provides user-callable Pascal runtime support utilities for checking the Apple-Period abort key, querying the Workshop global directory prefix and default printer device, performing terminal screen control, controlling Lisa printer character translation, and pre-configuring the Pascal heap data segment. |

---

## Unit PasLibCall

Provides user-callable Pascal runtime support utilities for checking the Apple-Period abort key, querying the Workshop global directory prefix and default printer device, performing terminal screen control, controlling Lisa printer character translation, and pre-configuring the Pascal heap data segment.

- **Import**: `USES {$U PasLibCall.obj} PasLibCall;`
- **Unit kind**: `INTRINSIC` (`PASLIBCA`)
- **Interface dependencies**: `SysCall`

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `PKeyPress` | `function PKeyPress: boolean;` | Compiler intrinsic helper for `KeyPressed(f)` that returns `TRUE` if unread input is available on FIB `f` (window terminal, active Exec script, keyboard queue, or RS-232 port). |
| `PAbortFlag` | `function PAbortFlag: boolean;` | Polls whether the user pressed Apple-Period on the console or window terminal, clearing the latched flag and returning `TRUE` if an abort was requested. |
| `GetGPrefix` | `PROCEDURE GetGPrefix(VAR errnum: INTEGER; Var prefix: pathname);` | Returns the Workshop Shell's global working directory prefix in `prefix`. |
| `ScreenCtr` | `procedure ScreenCtr(contrfun: integer);` | Executes standard terminal screen-control function `contrfun` (`CclearScreen`, `CclearEScreen`, `CclearELine`, `CgoHome`, or cursor arrow movement) on the active console. |
| `PLINITHEAP` | `procedure PLINITHEAP(var ernum, refnum: integer; size, delta: longint; ldsn: integer; swapable: boolean);` | Pre-initializes the process's private Pascal heap data segment at `ldsn` with initial byte size `size` and growth increment `delta` (rounded to 512-byte blocks, swappable if `swapable` is `TRUE`), returning OS `ernum` and `refnum`. |
