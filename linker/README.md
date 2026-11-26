# Lisa Linker (`linker/`)

A linker for Apple Lisa object files, in Python 3 (standard library only). It
links a main program with regular units and intrinsic libraries into an
executable `.OBJ` file identical, byte for byte, to the one written by the Lisa
Workshop Linker, or links intrinsic units into an intrinsic library (`-i`).

```sh
linker/lisalinker.py [-w VERSION] [-p] [-P] [--no-osdata] [--domain0] [-m MAP.txt] -o OUT[.OBJ] INPUT ...
linker/lisalinker.py -i [-s OLD=NEW] [--iulib INTRINSIC.LIB] [-m MAP.txt] -o LIB[.OBJ] INPUT ...

cd tests/workshop-QD          # with a compiled QD/BOXES.OBJ
LISA_BOOT=../../libs/workshop2.0 ../../linker/lisalinker.py \
    -o QD/XBOXES QD/BOXES IOSPASLIB IOSFPLIB '<QD/QDSTUFF'

linker/lisalinker.py -o LOSTEXTEDITOR LOSTEXTEDITOR_COMPILED IOSPASLIB SYS1LIB SYS2LIB PRLIB
```

Usually it is invoked through `pascal/lpc.py --link`, which compiles and links
in one command (see [`../README.md`](../README.md)).

* Give the inputs in the same order as on the Lisa (for example
  `tests/workshop-QD/QD/M/BOXES.TEXT` and `QD/QDSTUFF.TEXT`):
  * Names are Lisa file names: `.OBJ` is added when needed, case is ignored,
    and a volume prefix (`*X`, `-vol-X`) is dropped.
  * A file not found in the current directory is looked up in the boot folder:
    `$LISA_BOOT`, else `libs/workshop3.0`, as for the compiler.
  * `<FILE` reads more names, one per line, from the text file `FILE[.TEXT]`.
* `-w` selects the Workshop version whose Linker output to reproduce: `1.0`,
  `2.0` (the two are identical), or `3.0`. By default it is inferred from the
  libraries: their `VersionCtrl` `SysNum` is `1` in 1.0/2.0 and `0` in 3.0.
* `-o` names the output; as on the Lisa, `.OBJ` is appended unless the name
  already ends in `.OBJ` (`LIBPR/System.PR_IJP` becomes
  `LIBPR/System.PR_IJP.OBJ`).
* `-m` writes a link map: segments, modules, unit globals, and the jump table.
* `-P` performs a physical link (the Lisa Linker's `+P`), for a single-segment
  program that runs before the MMU is set up: its code is at address `0`, with
  a `PhysicalExec` block (`$97`) instead of `Executable` (see rule 9).
* `--no-osdata` omits the `OSData` block (the Lisa Linker's `-O`), and
  `--domain0` links system code running in domain 0, where MMUs 1–16 are
  unavailable so segments start at MMU 17 (`+F`). `SYSTEM.OS` and the installer
  are linked with both.
* `-p` packs the code segments, as `PACKSEG` does, using the boot folder's
  `SYSTEM.UNPACK` (`--table FILE` selects another pack table).
* When symbols are undefined, the error message also reports which library in
  the boot folder defines them.
* `-i` links intrinsic units into an intrinsic library (the Lisa Linker's `+I`
  option; see [Intrinsic libraries](#intrinsic-libraries)). `-s OLD=NEW` moves
  modules of segment `OLD` into segment `NEW` (`+M OLD NEW`). Unit and segment
  numbers come from `INTRINSIC.LIB` (in the current directory, the boot folder,
  or `--iulib`).

| File | Role |
|---|---|
| `lisaobj.py` | Object-block reader and writer: block types, big-endian fields, 8-character names |
| `lisadump.py` | Dumps any Lisa object file: modules, units, libraries, linked programs (`-c` dumps code bytes) |
| `lisalinker.py` | Program and CLI linker |
| `lisaintrinsic.py` | Intrinsic library linker (`-i`): links intrinsic units into an intrinsic library |
| `lisapack.py` | Packed code: unpacks and packs blocks and programs, and `check`s that packed blocks re-pack identically |
| `cmpshift.py` | Test helper: compares two linked programs whose main segments differ by one module's size |

## Status

Supported features: reading object files, linking main programs with regular
units and intrinsic libraries, multiple segments and jump tables, physical
links (`-P`), domain-0 / no-OSData system links, intrinsic-library builds
(`-i`), packed code (`-p`), and `pascal/lpc.py --link`. Verification results:

| Program | Linked with | Result |
|---|---|---|
| LosTextEditor (13 segments, 125 descriptors, 61 intrinsic units) | Workshop 3.0 `IOSPASLIB`, `SYS1LIB`, `SYS2LIB`, `PRLIB` | **Identical, byte for byte**, to `{T197000}Obj` on `LosTextEditor.dc42` (`../tests/downloaded_apps/run_lostexteditor_test.sh`) |
| 16 community Lisa Office System tools: LOS Minesweeper, 1000 Miles, LISACom, AtkinsonPoint, Lisa Slide Puzzle, Lisa Reversi, LisaFileMover, LisaFuji, LisaTwinClock, LisaFuji Browser, LisaCheckers, LisaSalvo, ESPFuji, LisaFetch, LisaSolstice, Lisa TattleTale (up to 10 segments, 255 KB linked) | Their compiled regular units and Workshop 3.0 `IOSPASLIB`, `SYS1LIB`, `SYS2LIB` (plus `PRLIB` and `IOSFPLIB` where used) | **All 16 identical, byte for byte**, to `{T<id>}Obj` on each project's `.dc42` disk image (`../tests/downloaded_apps/run_all.sh`) |
| LisaSerialFtpClient & LosSerialFtpClient (3 segments, 68 descriptors; Pascal + 68000 assembly; unreferenced procedures stripped) | Assembled `.OBJ` + Workshop 3.0 `IOSPASLIB` (and `SYS1LIB`, `SYS2LIB` for the LOS client) | **Identical, byte for byte**, to `{T197001}Obj` and `LisaSerialFtpClient.obj` on `LisaSerialFtpClient.dc42` (`../tests/downloaded_apps/run_serialftp_test.sh`; an earlier Lisa-linked `LisaSerialFtpClient.obj` was also verified byte-identical) |
| `BLESS` and `COPYMASTER` (Lisa Office System `LIBOS` target) | `SYS1LIB` and `IOSPASLIB` from `LOS_IMAGE` | **Identical, byte for byte**, to the Lisa-built `PROGS/*.OBJ` on the image (`../tests/run_lisa_sources_build_tests.sh LIBOS`) |
| `IOSPASLIB` (intrinsic library: 3 segments, 274 entry points, 5 Pascal units with interfaces + 16 assembler objects) | `-i -s SgPASres=PASIOLIB` and the image's `INTRINSIC.LIB` (`ALEX/LINK/LIBPL.TEXT`) | **Identical, byte for byte**, to the Lisa-built `LIBPL/IOSPASLIB.OBJ` (`../tests/run_lisa_sources_build_tests.sh LIBPL`) |
| `QPLIB` (intrinsic library: 4 segments, 5 units with interfaces; calls into `TKLIB`, `TK2LIB`, `PRLIB`, `SYS1LIB`, `IOSPASLIB`) | `-i` and the image's `INTRINSIC.LIB` (`ALEX/LINK/LIBQP.TEXT`) | **Identical, byte for byte**, to the Lisa-built `LIBQP/QPLIB.OBJ` (`../tests/run_lisa_sources_build_tests.sh LIBQP`) |
| `SYS1LIB` (275 KB: 963 blocks, 31 segments, from 6 targets' objects), `SYS2LIB` (134 KB), `PRLIB`, `TKLIB`, and the remaining programs of the 26 Office System library targets | As their `ALEX/LINK` exec files specify (`-i`, `-s`) | **Identical, byte for byte** (`../tests/run_lisa_sources_build_tests.sh`) |
| `IOSFPLIB`, `TK2LIB` | Same | **Identical, byte for byte** (under `BUILD=2.0`, 3 units differ in the compiler and link identically when given the Lisa-built units) |
| Canon and C.Itoh printer drivers (`SYSTEM.PR_IJP`, `SYSTEM.PR_DMP`) | Same | **Identical, byte for byte** |
| `SYSTEM.LLD` (`LIBHW`: loader hardware driver, linked with `+P`) | `-P` and `IOSPASLIB` (`ALEX/LINK/LIBHW.TEXT`) | **Identical, byte for byte**, to the Lisa-built `LIBHW/SYSTEM.LLD` |
| Office System applications (LisaWrite, LisaCalc & `LCORBGLIB`, LisaDraw, LisaGraph, LisaProject, LisaList, LisaTerminal, Desktop Manager, Preferences, Clock, Calculator, ...), `SYSTEM.OS` (`-O +F`), its drivers and OS programs (Shell, `BLESS`, ...), and the installer's `SYSLIB` (`+W APIN/INTRINSIC.LIB`) and `INSTALL` | As the image's `ALEX/LINK` exec files specify | **Identical, byte for byte**: ~70 programs and libraries across the full build (`../tests/run_lisa_sources_build_tests.sh`) |
| `BOXES` (4 segments, regular units) | Workshop 1.0 and 2.0 libraries | **Identical, byte for byte** (`../tests/run_link_tests.sh`) |
| `QDSAMPLE` | Workshop 1.0 and 2.0 libraries | Identical except `INITICON`: Lisa's is 250 bytes longer because its older code generator did not compact duplicate string literals (see `../tests/run_obj_tests.sh`); shifted PC-relative displacements and jump-table entries are verified too |

Packed code:

* Every `PackedCode` block across the libraries in `libs/workshop*` (113
  blocks) unpacks with that folder's `SYSTEM.UNPACK` and packs again to the
  exact same bytes.
* So do 124 of the 128 packed programs examined across Lisa ProFile images
  (Office System 1.0–3.1, Workshop 1.0–3.0); the remaining 4 are on a single
  image whose pages appear non-contiguous.

Not implemented:

* 32-bit `External` references and `Relocation` blocks: the Linker stops with
  an error if encountered (none of the programs above uses them).
* Packing an intrinsic library (`-p` with `-i`), and `PreLink`/`InstallLink`
  outputs (registering a library in `INTRINSIC.LIB` is `IUManager`'s job).
* Custom stack/heap size options (`Executable` headers use the Workshop
  Linker's default values).
* Main programs exceeding a single segment's 128 KB limit, or multi-segment
  `+P` physical links (no Lisa examples exist).

## Rules

Block formats follow the *Lisa Development System Internals Documentation*
(Feb 1984), pp. 102–141
([`../docs/Lisa_Develpment_System_Internals_Documentation_198402.pdf`](../docs/Lisa_Develpment_System_Internals_Documentation_198402.pdf)).
Additional layout rules required for byte-identical output were derived from
`Linker.Obj` and Lisa-linked `BOXES`, `QDSAMPLE`, `LosTextEditor`, and Office
System binaries:

1. **Module selection.**
   * The main program is the module with a `StartAddress` block.
   * Every module it references, directly or indirectly, is linked in;
     unreferenced modules of a unit are omitted.
   * Names starting with `$` are file-local (several `QD` files reuse the same
     `$` names).
   * Every segment named by a linked-in module is retained even if none of its
     code is kept: it receives an MMU number and a segment-table entry with
     file address `0` and size `8`, and no code blocks (e.g. `flrDebug`).
2. **Segments.**
   * The blank (main) segment comes first. Remaining segments follow in the
     order their names first appear across *all* modules of the input files,
     including unreferenced modules (in `QDSAMPLE`, `QDMisc` precedes
     `Hardware` for this reason).
   * Within a segment, modules are placed in input order.
   * MMU numbers start at `18` in 1.0/2.0 and `1` in 3.0, skipping MMU numbers
     used by the linked intrinsic libraries. A segment's code resides at
     `MMU * $20000 + 8`.
3. **References** (`ShortExternal`; the instruction word precedes the 16-bit
   displacement):
   * Same segment: `d(PC)`. `JSR`, `JMP`, `PEA`, and `LEA` with absolute
     addressing (`abs.W` or `abs.L`, from assembler modules) are converted to
     `d(PC)` as well (`LEA abs.W` in `SYS1LIB`).
   * Other segment: `d(A5)`, addressing the target's jump-table descriptor.
   * Intrinsic routine: an IU trap, where `hhllll` is the routine's address
     from the library's `EntryPoint` block: `$A0hh llll` (`IUJSR`),
     `$A4hh llll` (`IUJMP`), `$AChh llll` (`IUPEA`), or for `IULEA`
     `$A800 + 128 * reg + bits 16..22 of (addr / 2)` followed by the low word
     of `addr / 2` (adding any existing addend in the address word).
4. **Jump table.**
   * Descriptor 0 is the program's entry point.
   * Then one `JMP abs.L` descriptor per procedure called across segments,
     grouped by segment in segment order and sorted by `LinkName` within each
     group. A name that is a prefix of another sorts *after* the longer name
     (`LINETO` before `LINE`); `$` and `%` sort after letters (non-local `GOTO`
     `$` labels sort last, as in the Canon printer driver).
   * In 1.0/2.0 only, the 6 bytes `2258 2F08 4ED1` follow the descriptors.
   * Descriptors are per symbol name, not per address: aliased entry points at
     the same address each get a descriptor if called cross-segment
     (LisaTerminal has 5 names at one address).
   * Local `$nnnnnnn` names of nested procedures have reversed-digit decimal
     numbers (`$9100000` = 19), rebased per input file by `0` for the first
     file and `1 + max_seen` thereafter (`CVTLOCAL`, `LOCALNAM`, `INCLNAME` in
     `Linker.Obj`), then written back reversed before sorting.
   * `JTLaddr = $F80000 + JTSegDelta + 4 * max_intrinsic_unit_num` (the data
     pointer table). `A5 = $F80000 - StkSegDelta`.
5. **Globals.**
   * The main program's globals sit immediately below `A5`. Regular units'
     globals sit below them in the order the Linker's depth-first search
     (`DFSDIR` in `ObjIOLib`'s `GRAPHS` unit) first reaches each unit.
   * Each module and each regular unit is a graph vertex. Input files and
     blocks are read in order; each `External`/`ShortExternal` to an input
     module or `CommonReloc` to a regular unit prepends an arc (`ADDARC`) on
     the source module's adjacency list. Forward references attach to a
     placeholder vertex and are re-added newest-first (`MOVEREFS`) once the
     defining module or unit is read.
   * Because `ADDARC` prepends and `DFSDIR` traverses from the head, a module's
     newest reference is visited first, starting from the main program module.
     Unreached units occupy no global space; `DataSize` is the sum of reached
     units' globals, and `CommonReloc` fields receive each unit's base offset.
   * Intrinsic unit globals are accessed via the data pointer table ending at
     `JTLaddr`; their `CommonReloc` fields become `$1FC + 4 * unit_number` off
     `A5` (e.g. `EVENTS`, unit 10, becomes `MOVEA.L $224(A5),An`).
6. **Unit and segment tables.**
   * Union of those in all input intrinsic libraries, sorted by unit or segment
     number (including a library in the Linker input list references all of its
     segments).
7. **Output.**
   * `VersionCtrl`, `[OSData]`, `UnitTable`, `Executable`, `SegmentTable`, then
     per segment: `ModuleName` (`MainProg`), `StartAddress` (main segment
     only), `CodeBlock`, `EndBlock`; terminated by `EOFMark` and padded to 512
     bytes.
8. **Workshop versions (`-w`).** Workshop 1.0 and 2.0 write identical files;
   Workshop 3.0 differs in four places:

   | Feature | 1.0 / 2.0 | 3.0 |
   |---|---|---|
   | First program MMU number | `18` (`$240000`) | `1` (`$20000`) |
   | `VersionCtrl` | `00010000 00010000 00017f00 0 0 0` | All zeros |
   | `OSData` block after `VersionCtrl` | None | 514 zero bytes |
   | Trailing bytes after descriptors | `2258 2F08 4ED1` | None |

9. **Physical link (`+P` / `-P`).** Verified against `Linker.Obj` (`LINKMAIN`)
   and `SYSTEM.LLD`:
   * Omits `VersionCtrl` and `OSData`; emits `UnitTable`, `PhysicalExec`
     (`$97`), `SegmentTable`, then `ModuleName`, `StartAddress`, `CodeBlock` at
     address `0`, `EndBlock`, and `EOFMark`.
   * `PhysicalExec` loads at constant `JTLaddr = $FFFFAB00` with the 6 header
     longwords (`JTLaddr`, `JTSize`, `DataSize`, `MainSize`,
     `JTSegDelta = $100`, `StkSegDelta = $2000`), segment count and 32-byte
     segment records, jump-table end (`JTLaddr + 16 + 32 * segments`), main
     entry (`offset`, `NOP`, `JSR` to exit stub), constants `0, -1, JTLaddr`,
     and the exit stub (`PEA *`, `CLR.W -(SP)`, `TRAP #14`, `MOVE.W #4,-(SP)`,
     `TRAP #14`).

## Intrinsic libraries

`-i` links intrinsic units into an intrinsic library (`+I` on the Lisa),
verified byte for byte against `IOSPASLIB`, `SYS1LIB`, `SYS2LIB`, `PRLIB`,
`QPLIB`, `TKLIB`, `TK2LIB`, and `IOSFPLIB`:

1. **Modules.** Every module in the input files is linked. `-s OLD=NEW` (`+M`)
   renames segments on their 8-character case-folded prefix (`+m PrBtnInit PrInit`
   matches `PrBtnIni`), using the spelling from `INTRINSIC.LIB`.
2. **Segments.** Target segments of `-s` come first (in option order), followed
   by remaining segments in first-appearance order. Each segment receives its
   MMU number from `INTRINSIC.LIB`, with `CodeBlock` at `MMU * $20000` and code
   8 bytes after.
3. **Jump vector.** Each segment begins with one `JMP d(PC)` per non-`$` entry
   point, sorted by `LinkName` (`%` after letters, shorter prefixes after
   longer names), followed by the modules in input order.
4. **References.** Same-segment calls use `d(PC)` directly to the routine;
   cross-segment calls emit an IU trap to the target's jump-vector entry (or
   directly to the routine for `$` names); `CommonReloc` uses
   `$1FC + 4 * unit_number`.
5. **Output.** `VersionCtrl`, `SegLocation`, `InterfLoc`, `UnitTable`,
   `SegmentTable`, `UnitBlock`s (in reverse input order), then per segment:
   `ModuleName` (`IntrinSg`), `EntryPoint`s (modules in order, each module's
   entries reversed), `CodeBlock`, `EndBlock`, and `EOFMark`.
6. **Interfaces.** Each `UnitBlock` stores compressed `INTERFACE` text:
   non-directive comments stripped (without inserting spaces), whitespace runs
   collapsed, indentation and blank lines removed, strings preserved, laid out
   in 1024-byte pages (advancing to the next page with NUL padding when a line
   would leave fewer than 2 bytes free), terminated by 2 NULs (plus 1 if odd),
   with bit 7 of byte 0 preserving the unit-init flag.

## Packed code

Packing replaces frequent 16-bit code words with 1-byte indices into a 256-word
table (`SYSTEM.UNPACK`, a 520-byte `PackTable` block `$A1`, version 1):

* References: `LISA_OS/OS/source-UNPACK.TEXT` and `source-LOADER.TEXT` in the
  CHM Lisa sources, and Alex Anderson-McLeod's
  [`ALEX-PACKSEG.TEXT`](https://github.com/alexthecat123/LisaSourceCompilation/blob/main/src/ALEX-PACKSEG.TEXT)
  (no code was taken from it; `lisapack.py` implements the format from
  specification and was verified against 113 Lisa library blocks and 124 packed
  programs).
* Words are processed in groups of 8: each item is either a 1-byte table index
  (`1..255`, choosing the lowest matching index; `0` is unused) or a 2-byte
  literal word, followed by a flag byte whose bit *i* is `1` when item *i* is a
  table index.
* After the final group comes `2 * i` (where *i* is the bit index of the last
  word) preceded by a `0x00` slack byte if needed to make the total byte length
  even, or `2 * i + 1` with no slack byte when already even.
* Packing a linked program converts each `CodeBlock` into a `PackedCode` block
  (`$A0`: address, unpacked size, packed bytes), drops `StartAddress`, and
  updates each `Executable` segment entry's file offset and `SizePacked`
  (empty segments with `SizeUnpacked = 8` stay unchanged).
* Two tables exist: one shared by Office System and Workshop 1.0/2.0, and one
  for Workshop 3.0, stored in `libs/workshop*/SYSTEM.UNPACK` from fresh-install
  `.dc42` images.

## Related work

[pappadf/lisa-c](https://github.com/pappadf/lisa-c) (MIT) provides a modern C
toolchain for the Lisa whose `tools/lisalink.py` drives GNU `ld` on ELF objects
and `elf2lisa.py` emits Lisa executables. No code was taken from it; all block
layouts here come from Apple's Lisa documentation and Lisa-linked binaries.
