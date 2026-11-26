# Lisa 68000 Assembler (`assembler/`)

A Python version of the Lisa Workshop's 68000 Assembler: it reads a Lisa
assembly source (`.TEXT`) and writes the object file (`.OBJ`) that the Workshop
3.0 Assembler (`ASSEMBLER.OBJ`) writes, byte for byte, for the Linker
([`../linker/`](../linker/README.md)).

| File | Role |
|---|---|
| `assembler.py` | CLI & interactive dialog, options, and listing writer |
| `asm68k.py` | One-pass MC68000 assembler implementation |
| `N68K.OPCODES` | Opcode table file read by the Lisa Assembler |
| `changeseg.py` | Places all modules of an `.OBJ` file into one segment, as the Workshop's `CHANGESEG` does (`BUILD/ASSEMB.TEXT` runs it) |

## Use

```sh
assembler/assembler.py MYPROG                   # MYPROG.TEXT -> MYPROG.OBJ
assembler/assembler.py MYPROG MYPROG.LST OUT    # input, listing file, output file
assembler/assembler.py +P MYPROG MYPROG.LST     # options first
assembler/assembler.py                          # interactive, as on the Lisa
assembler/changeseg.py MYPROG.OBJ SEGNAME       # all modules into segment SEGNAME
```

Arguments answer the Assembler's prompts in order, as on the Lisa:

```text
ASSEMBLER - MC68000 (Ver 1.0)


Options:     Meaning                   Current Value.
+P        Pretty Listing                   FALSE
+S        Print Space Avail                FALSE
+E        Code patching efficiency check   FALSE
?         Print options
<ret>     Accept options
Input file - [.TEXT] MYPROG
Listing file (<CR> for none) -
Output file - [MYPROG][.OBJ]
```

A missing answer takes the default. `?` at the input prompt (or an argument
like `+P`) sets the options:

* `+P` pretty listing: the listing shows the resolved values of forward
  references, otherwise `****`.
* `+E` code patching efficiency check: warns on each forward branch that could
  have been a short branch.
* `+S` is accepted.

Errors are reported with the Lisa Assembler's error numbers (Workshop User's
Guide, Appendix A.1), with the file and line; no object file is written and the
exit status is `1`.

File names are Lisa names: `.TEXT` is added to the input name and `.OBJ` to the
output name unless given, case is ignored, and a volume prefix (`-WORK-`) is
dropped. `.INCLUDE` names are resolved the same way, relative to the current
folder. Sources can be Lisa `.TEXT` files (header page, DLE indentation) or
host text files.

## Status

| Source | Result |
|---|---|
| Lisa Office System assembly sources: the 28 `ALEX/ASM` exec files on the OS source image, 105 sources with ~50 include files (Pascal runtime, QuickDraw, floating-point packages, OS assembly modules, LisaWrite, LisaCalc, ...) | **All 105 objects identical, byte for byte**, to the Lisa-built ones (`../tests/run_asm_test.sh`) |
| Full Lisa Office System build (`../tests/run_lisa_sources_build_tests.sh`: assemble, compile, link, and phrase generation following `ALEX/MAKE/ALL_NODISKS`) | **All 473 of 473 files identical**, including the libraries, applications, and `SYSTEM.OS` linked from the 105 assembled objects |
| LisaSerialFtp's `LisaSerialFtpClientAsm.text` and `LosSerialFtpClientAsm.text` | Assembled and linked into both `LisaSerialFtpClient.obj` and `{T197001}Obj` (`../tests/downloaded_apps/run_serialftp_test.sh`, verified byte-for-byte against `LisaSerialFtpClient.dc42`; an earlier Lisa-linked `LisaSerialFtpClient.obj` was also verified byte-identical) |
| Objects made by the Workshop 1.0/2.0 Assembler (`../tests/workshop-QD/QD`: `UNIT68K`, `FM68K`) | All 33 procedures whose source on the OS image is unchanged have identical code, entry points, and references (their segment was set by the build); the remaining procedures come from different source revisions |

The listing is the one feature not compared against a Lisa-generated file: its
layout follows the Workshop guide's example (location, code, source line, `#`
for macro expansions). The Workshop 1.0 and 2.0 Assemblers wrote the same
object format, as far as their objects show.

Not implemented: `.SYMBOLS` files, `.ORG`/`.RORG` beyond padding to the
location, Motorola-style directives in the opcode table other than `EQU`,
`END`, `ORG`, `RORG`, `PAGE`, `LIST`, `NOL`/`NOLIST`, `ENDC`, `MACRO`, `ENDM`
(`DC`, `DS`, `SET`, `IFEQ`, ...), and 32-bit `External` references /
`Relocation` blocks (none of the sources above uses them).

## Rules

Taken from the Workshop User's Guide (Beta, April 1983, Chapter 6:
[`../docs/Workshop_Users_Guide_Beta_Apr83.pdf`](../docs/Workshop_Users_Guide_Beta_Apr83.pdf)),
the Pascal Development System Manual
([`../docs/Lisa_Development_System_Manual_Mar85.pdf`](../docs/Lisa_Development_System_Manual_Mar85.pdf)),
the 1984 Workshop User's Guide Appendix A.1
([`../docs/Workshop_User_Guide.pdf`](../docs/Workshop_User_Guide.pdf)), and —
where the manuals are silent or differ — from the 105 Lisa-built objects and
from `Assembler.Obj` itself (routine names in the binary: `HASHER`, `LINKERIN`,
`DUMPENTR`, ...).

1. **Lines.** A label starts in column 1, with an optional colon. A local label
   is `@` followed by digits; it may be indented, and its scope ends at the
   next regular label. A directive starts with `.` and may be in column 1. `;`
   starts a comment, and a comment needs no `;`: the operand field ends at a
   blank, except a blank next to an operator or comma, or before `(An)`. Thus
   `MOVE.L  atld (A6), A0` and `hz .EQU PARAMSIZE + 8 - 4` are single operand
   fields.
2. **Names** have 8 significant characters, case-insensitive (macro names
   included).
3. **Expressions** are evaluated strictly left to right, without operator
   precedence: `+ - * / \ (mod) & | ^ ~`, plus `=` and `<>` in `.IF`; `<` and
   `>` group subexpressions. Numbers: decimal, `$hex`, `nnnH`, `nnnO` (octal),
   `nnnB` (binary); strings in `'` or `"`. `*` is the current location.
4. **One pass.** An instruction's encoding is chosen when read. A symbol not
   yet defined is a forward reference filled in at the end of the procedure, so
   the optimizations below apply only to already-known values, and a forward
   branch is word-sized unless `.S` is written:
   * `0(An)` becomes `(An)`;
   * `ADD`/`SUB #1..8` becomes `ADDQ`/`SUBQ` (including to an address
     register); `ADD`/`SUB` to an address register becomes `ADDA`/`SUBA`;
   * `ADD`/`SUB`/`AND`/`OR #n` becomes `ADDI`/`SUBI`/`ANDI`/`ORI`, `CMP #n`
     becomes `CMPI` (including to a data register), `EOR #n` becomes `EORI`;
   * `MOVE #0` becomes `CLR`; `MOVE.L #n,Dn` with `-128..127` becomes `MOVEQ`;
   * a branch to a known label within `-128..127` is short (with or without
     `.S`); a `.S` branch to a known label out of range becomes word-sized;
   * a forward `.S` branch to the immediately following instruction
     (displacement 0) becomes `NOP`.
5. **Operands.** A label in the current procedure is PC-relative; `label(Dn)`
   is `label(PC,Dn)`. A `.REF` name is an absolute short address of `0` with a
   `ShortExternal` record, which the Linker turns into PC-relative, jump-table,
   or IU-trap form. Other numbers are absolute short if they fit in signed 16
   bits, else absolute long. A byte immediate is stored as the low word of its
   value (`#-1` is `FFFF`).
6. **Procedures.** Each `.PROC`/`.FUNC` is one module; its name is a label at
   offset `0`. Symbols defined before the first `.PROC` (equates, macros) are
   global; a procedure's symbols are local to it (the Lisa Assembler snapshots
   its symbol table after the global header and restores it after each
   procedure). Procedure code is padded to an even byte length.
7. **Object file.** Per module: `ModuleName` (from the last `.SEG`),
   `EntryPoint` records, `ShortExternal` records, one `CodeBlock` at `0`, and
   `EndBlock`; `EOFMark` at the end, padded to 512 bytes. Each `ShortExternal`
   lists the offsets of its uses in reverse order (last use first).
8. **Order of entries and references.** The Assembler stores symbols in a
   256-bucket hash table, inserting each newly mentioned name at the head of
   its bucket. At the end of a procedure, `LINKERIN` walks buckets `0..255` and
   prepends each `.DEF` name (and the procedure name) to the entries list and
   each `.REF` name to the references list — so records appear by bucket from
   `255` down to `0`, and within a bucket in the order first mentioned. Hash
   (`HASHER`) over the 8 blank-padded characters:
   `h := (h + h) XOR ord(c)` in 16 bits, then
   `((h DIV 256) XOR (h AND $FF)) AND $FF`.
9. **Macros.** `.MACRO name` ... `.ENDM`; `%1`..`%9` expand top-level
   comma-separated arguments; up to 5 nested macro calls.
10. **Conditionals.** `.IF expr` / `.ELSE` / `.ENDC` (nestable); string
    literals may be compared with `=` and `<>`.

## Post-processing in Office System builds

The Office System's exec files post-process certain assembled objects, and the
test harnesses do the same:

* **`CHANGESEG`** (`changeseg.py`): rewrites all module segment names in an
  `.OBJ` file (`$SUBMIT BUILD/ASSEMB(SRC,OBJ,SEG)`, or `R{un}CHANGESEG`).
* **`LIBQD`'s `FIXMOVE`** (`libqd/fixmove.text`): *"Assembler restrictions
  require procedure Move to [be] assembled as MQVE"* — replaces `MQVE` with
  `MOVE` in the first 1024 bytes of `LINES.OBJ`.
