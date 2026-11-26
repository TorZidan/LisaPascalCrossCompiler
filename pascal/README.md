# Lisa Pascal Cross-Compiler (`pascal/`)

A Python 3 translation of the Apple Lisa Pascal two-pass compiler and MC68000
code generator, producing `.I` (I-code) and `.OBJ` (MC68000 object) files
identical, byte for byte, to `pascal.obj` and `code.obj` in Lisa Workshop.

## Executables

| Program | Description |
|---|---|
| `pascal/pascal.py` | Pascal front-end compiler for Workshop 1.0, 2.0, and 3.0 (`.TEXT` -> `.I`; `$G+` default in 3.0, `--2.0` selects the 1.0/2.0 build) |
| `pascal/code.py` | Motorola 68000 code generator for Workshop 1.0, 2.0, and 3.0 (`.I` -> `.OBJ`; `--2.0` selects the 1.0/2.0 build) |
| `pascal/lpc.py` | Driver combining front end + code generator + optional Linker (`--link`, `--pack`, `--2.0`) |
| `pascal/audit_8char.py` | Audits Pascal `.TEXT` files, `USES` units, and linked libraries for 8-character identifier collisions |

## Usage

```sh
# Compile MYPROG.TEXT -> MYPROG.OBJ (both passes, Workshop 3.0 build by default):
pascal/lpc.py MYPROG

# Compile for Workshop 1.0 / 2.0:
pascal/lpc.py --2.0 MYPROG

# Compile and link with ../linker/lisalinker.py:
pascal/lpc.py --link MYPROG
pascal/lpc.py --link=IOSPASLIB,SYS1LIB,SYS2LIB MYPROG
pascal/lpc.py --link --pack MYPROG

# Run individual passes directly (command-line answers or interactive stdin):
pascal/pascal.py '$G-' MYPROG       # -> MYPROG.I
pascal/code.py MYPROG               # MYPROG.I -> MYPROG.OBJ
pascal/lpc.py '$ASM+' MYPROG LST    # listing with 68000 disassembly

# Check a program (and its includes, USES units, and libraries) for 8-char collisions:
pascal/audit_8char.py MYPROG
```

## Code listings

Code listings use options at the front end's first prompt (via command-line
arguments such as `pascal/lpc.py '$ASM+' MYPROG MYPROG.LST`, or piped on
stdin):

| Options | Listing |
|---|---|
| `$ASM+` | Generated code interleaved under each source line: address, hex, label, 68000 instruction |
| `$ASM+` and `$ASM PROC` | Generated code emitted after each whole procedure |
| `$ASM+` and `$ASM ONLY` | Assembler source for the Workshop assembler (`.PROC`, `.REF`, labels, decimal constants) |

For example, `printf '$G+\n$ASM+\nMYPROG\nMYPROG.LST\n\n' | pascal/lpc.py`
produces a listing like:

```text
00000C 43FA 01E6      LEA     Cst0010,A1      ; 000001F4
000016 6EFA           BGT.S   *-$0004         ; 00000012
00002C 4EBA 0000      JSR     %_UNION
```

`$ASM ONLY` needs the assembler's opcode table `N68K.OPCODES` (in
[`../assembler/N68K.OPCODES`](../assembler/N68K.OPCODES)) in the current
directory. Without it, names that clash with opcodes are not renamed.

## Module Layout

| File | Role |
|---|---|
| `lisalib.py` | Host runtime: `LisaIO`, `StdUnit`, `IOPrimitives`, `ProgComm`, `PasDefs`, `FileIO`, `ObjIO`, `IUMan`, `ObjInter`, `FPLib`, `Dates`, `Times`, and 16/32-bit integer & IEEE-754 `Single` helpers |
| `frontend_base.py`, `frontend.py` | Front-end AST/symbol-table records, global state, and pass-1 driver |
| `pas_init.py` | Scanner tables, standard types/identifiers/intrinsics, options, and Workshop prompt dialog |
| `pas_misc.py` | File stack, lexer, `$IFC`/`$SETC` conditionals, `PASERRS.ERR` diagnostics, constant evaluator, symbol search, unit/program orchestration, I-code output |
| `pas_decl.py` | `USES`, `LABEL`, `CONST`, `TYPE`, Clascal `SUBCLASS`, `VAR`, `PROCEDURE`/`FUNCTION`/`INLINE` declarations |
| `pas_body.py` | Expressions, selectors, statements, standard procedure/function calls |
| `pas_opt.py` | Expression tree folding, reference counting, register & `WITH` binding, CSE |
| `pas_dump.py` | I-code emitter from optimized AST and symbol table |
| `pas_dbg.py` | `$D` debug symbol / AST dump |
| `codegen_base.py` | Code generator records (`CAttr`, `Valu`, labels, externals, commons), constants, shared state, and pass-2 driver loop |
| `codegen.py` | MC68000 code generator (`CodeGenerator`): listing merger, register allocator, effective-address emission, expression/statement/call codegen, short-branch optimization, literal-pool compaction, `.OBJ` output, and pass-2 initialization |
| `gen_disasm.py` | MC68000 disassembler for `$ASM+` / `$ASM ONLY` listings |
| `PASERRS.ERR` | Front-end compiler error message catalog |

## The file `PROGCOMM.TEXT`

`PROGCOMM.TEXT` is a temporary file. The compiler writes it and deletes it
itself; it is not a source file, and one that is left behind does no harm.

On the Lisa, the Workshop's `ProgComm` unit (in `SULib`) passes a text buffer
of up to 1024 characters from one program to the next one the Workshop shell
runs. The compiler uses it to hand over from the front end to the code
generator, and, after errors, to the Editor. A host process cannot hand memory
to the next one, so the host `ProgComm` (`lisalib.py`: `PCReWrite`,
`PCPutLine`, `PCClose`, `PCReset`, `PCGetLine`) keeps the buffer in
`PROGCOMM.TEXT` in the current directory. Its first line is the buffer's key,
followed by the buffer's lines:

| Key (first line) | Written by | Lines after the key | Read and deleted by |
|---|---|---|---|
| `For Code Gen` | Front end (`pascal/pascal.py`) at the end of a compile without errors when `$G+` is set (default in 3.0; `pascal/lpc.py` adds `$G+` unless a `$G` option is given): `ChainToEdOrGen` in `pas_misc.py` | The `.I` file, the output file (the name the code generator gives `.OBJ`; for `T.TEXT` both lines are `T.I`), `$I+`, plus `$ASM ONLY`, `$ASM PROC`, `$A+`, `$M+` when set | Code generator (`pascal/code.py`) on startup (`codegen.py`): takes the file names and options from the file instead of prompting, then deletes it |
| `For Editor` | Front end after an error when `E` (call Editor) is answered at `"Type SPACE to continue, CLEAR to exit, E to call Editor"`, or with `$E+` (`ListErrors` in `pas_misc.py`); or at the end of a compile with errors when `$E file` and `$E+` are set (`ChainToEdOrGen` in `pas_misc.py`) | First error message, source file, and error location (`line col line col`); or `Errors in PROGNAME`, error file, and `* 1 1 1 1` | No editor runs on the host; the next front-end run deletes it |

The front end also deletes any leftover `PROGCOMM.TEXT` with either key when it
starts (`pas_init.py`), so a stale buffer is never used. `pascal/lpc.py` starts
the code generator only when the file exists and its first line is
`For Code Gen`, and with `--link` takes the name of the `.OBJ` file to link
from its second line.

The file stays in the current directory when:

* `pascal/pascal.py` is run alone with `$G+` (or in the 3.0 build without a
  `$G` option), and `pascal/code.py` is not run after it;
* the code generator is interrupted before it has read the file (once read, it
  is deleted even if the files named in it cannot be opened);
* the front end wrote a `For Editor` buffer.

## Units: `{$U file}` and the intrinsic library

`USES` finds a unit's interface in two ways, as on the Lisa:

1. **Through `INTRINSIC.LIB`**, unless `{$U-}` is set. This file is the
   directory of the Lisa's intrinsic units, such as `StdUnit`, `QuickDraw`,
   `HWInt`, and `FPLib`. It names the library file that holds each unit (e.g.
   `SYS1LIB.OBJ`), and the interface is read from there. So `USES QuickDraw;`
   works without a file name.
2. **From the file named by `{$U file}`**: a unit `.OBJ` or a library file. A
   name without a volume (e.g. `{$U SysCall.obj}`) means the working volume,
   which on a Workshop system is normally the boot volume: it is looked up in
   the current directory first and then in the boot folder. This applies only
   to reading. Files that are written always go to the current directory.

The boot volume is a folder, chosen with `$LISA_BOOT`. Each folder also holds
that Workshop version's plain unit files `SYSCALL.obj` and `PASLIBCALL.obj`,
which are not in `INTRINSIC.LIB` (programs name them with `{$U SysCall.obj}`),
along with complete library, unit, procedure/function, and Clascal method
references (`USES` syntax, `--link` flags, signatures, and descriptions):

| Folder | Contents & API Reference |
|---|---|
| `libs/workshop3.0/` (default) | Workshop 3.0 `INTRINSIC.LIB` and 11 intrinsic library files from a 3.0 disk: `Sys1Lib`, `Sys2Lib`, `SUlib`, `iospaslib`, `IOSFPLIB`, `PRLib`, `ObjIOLib` (with interface text) and `LCORBGLIB`, `QPLIB`, `TKLIB`, `TK2LIB` (code only), plus `SYSCALL` and `PASLIBCALL`. See [`README.txt`](../libs/workshop3.0/README.txt) and [`LIBRARIES.md`](../libs/workshop3.0/LIBRARIES.md) (13 libraries, 99 units, 3,144 callables) |
| `libs/workshop2.0/` | Workshop 2.0 `INTRINSIC.LIB` and 7 intrinsic library files from a 2.0 disk: `SULIB`, `IOSPASLIB`, and `IOSFPLIB` contain interface text; `SYS1LIB`, `sys2lib`, `objiolib`, and `lcorbglib` contain code only (in 2.0 their interfaces came from separate unit files named with `{$U}`, e.g. `{$U QD/QuickDraw}`), plus `SYSCALL` and `PASLIBCALL`. See [`README.txt`](../libs/workshop2.0/README.txt) and [`LIBRARIES.md`](../libs/workshop2.0/LIBRARIES.md) (9 libraries, 84 units, 1,824 routines) |
| `libs/workshop1.0/` | Workshop 1.0 `INTRINSIC.LIB` and 6 intrinsic library files from a 1.0 disk: as in 2.0, `Sulib`, `IOSPaslib`, and `IOSFplib` contain interface text, while `Sys1lib`, `Sys2lib`, and `Objiolib` contain code only, plus `SYSCALL` and `PASLIBCALL`. See [`README.txt`](../libs/workshop1.0/README.txt) and [`LIBRARIES.md`](../libs/workshop1.0/LIBRARIES.md) (8 libraries, 59 units, 1,321 routines) |

```sh
LISA_BOOT=$PWD/libs/workshop2.0 pascal/lpc.py --2.0 MYPROG  # compile against Workshop 2.0
```

A few library files listed in `INTRINSIC.LIB` are not present on the source
disks (e.g. `*IUPASLIB`; see each folder's `README.txt`). A file name with a
volume prefix (`*X`, `-#BOOT-X`, `-X`) is looked up in the current directory
first and then in the boot folder. The 1.0 and 2.0 `INTRINSIC.LIB` library
names have no volume prefix; they are treated as boot-volume names. Typing `?`
at the `Input file` prompt asks for a different intrinsic library file, as on
the Lisa.
