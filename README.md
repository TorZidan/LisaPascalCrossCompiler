# Apple Lisa Pascal Cross-Compiler, in Python

This repository contains the Apple Lisa Pascal cross-compiler and the other
Workshop tools needed to build Lisa programs and Office System desktop tools on
a modern host: the 68000 Assembler, the Linker, the alert/menu phrase-file
generator, the tool-install utility, and the icon and disk-image utilities. All
of them are written in Python 3 (standard library only) and produce outputs
identical, byte for byte, to those written by the Lisa Workshop.

The compiler ([`pascal/`](pascal/README.md)) is 1:1 translation of the  pascal
compiler `pascal.obj` in Workshop. It has two passes:

| Pass | Role | Program |
|---|---|---|
| Front end | `.TEXT` -> `.I` (I-code) | `pascal/pascal.py` |
| Code generator | `.I` -> `.OBJ` (MC68000) | `pascal/code.py` |

`pascal/lpc.py` runs both passes, and the Linker when asked. See
[`pascal/README.md`](pascal/README.md) for the compiler's modules.

## Run

Nothing needs to be built. The typical use is to run both passes
(`.TEXT` -> `.I` and then  `.I` -> `.OBJ`) in one command, the way it works
in Workshop (which is triggered by the default option `$G+`):

```sh
pascal/lpc.py MYPROG                              # MYPROG.TEXT -> MYPROG.OBJ
```

### Answers on the command line

Both passes ask the Workshop's questions (`Input file`, `List file`,
`I-code file` / `Output file`). **Arguments answer them in order**; a missing
answer takes the default, as if RETURN was pressed, so the program never waits
for input. An argument that starts with `$` is an option line, which the front
end accepts at its first prompt (`$G+`, `$ASM+`, `$ASM ONLY`, `$M+`, `$Efile`,
...; see [`pascal/README.md`](pascal/README.md#code-listings) for code
listings). The prompts and answers are shown, as in a Workshop session:

```sh
pascal/pascal.py '$G-' MYPROG                     # MYPROG.TEXT -> MYPROG.I
pascal/pascal.py '$G-' '$ASM+' MYPROG MYPROG.LST  # options, input file, listing file
pascal/code.py MYPROG                             # MYPROG.I -> MYPROG.OBJ
pascal/lpc.py --2.0 MYPROG                        # Like above, but for Workshop 2.0
pascal/lpc.py MYPROG '' OTHER                     # MYPROG.TEXT -> OTHER.OBJ, no listing file
```

`pascal/lpc.py` passes its arguments to the front end and puts `$G+` first
(unless a `$G` option is given). The front end then leaves `PROGCOMM.TEXT` (the
program-communication buffer; see
[`pascal/README.md`](pascal/README.md#the-file-progcommtext)) behind, and
`pascal/lpc.py` starts the
code generator, which reads the file names from it, compiles the `.I` file to
the `.OBJ` file, and deletes the `.I` file and `PROGCOMM.TEXT`. Running
`pascal/pascal.py` alone also chains to the code generator by default (`$G+` is
the default of the 3.0 build): it then leaves the `.I` file and `PROGCOMM.TEXT`
for `pascal/code.py`.

Only the line prompts are answered from the arguments. "Type SPACE to continue"
after an error and yes/no questions still read the keyboard (or stdin, where
end of input means ESC).

### Answers typed or piped

Without arguments the programs ask interactively, or read the answers from
stdin:

```sh
printf '$G+\nMYPROG\n\n\n' | pascal/lpc.py        # prompts: Input file / List file / Output file
printf '$G-\nMYPROG\n\n\n' | pascal/pascal.py     # -> MYPROG.I
printf 'MYPROG\n\n'        | pascal/code.py       # -> MYPROG.OBJ
```

An empty answer takes the default and end of input (Ctrl-D) acts as ESC.
`PASERRS.ERR`, the front end's error messages, is in `pascal/`.

### Linking

`pascal/lpc.py --link` compiles and then links the compiled program,
like the Workshop's `L(ink)` command, with `linker/lisalinker.py` (see
[`linker/README.md`](linker/README.md)). The linked program replaces the `.OBJ`,
as the Workshop's own exec files do (they link to `XNAME` and rename it to
`NAME.OBJ`). `--link` compiles the source (`MYPROG` below is `MYPROG.TEXT`) and
then links it; to link existing compiled `.OBJ` files, run `linker/lisalinker.py`
directly (see below):

```sh
# Compile and link MYPROG.TEXT in 1 step, with IOSPASLIB
pascal/lpc.py --link MYPROG

# Compile and link MYPROG.TEXT in 1 step, with IOSPASLIB, SYS1LIB, SYS2LIB, PRLIB
pascal/lpc.py --link=IOSPASLIB,SYS1LIB,SYS2LIB,PRLIB MYPROG

# Compile and link QD/BOXES.TEXT in 1 step, with IOSPASLIB, IOSFPLIB
# and the libraries listed in QD/QDSTUFF.TEXT (note the '<' there)
pascal/lpc.py --link='IOSPASLIB,IOSFPLIB,<QD/QDSTUFF' QD/BOXES

# Compile and link MYPROG.TEXT in 1 step, with IOSPASLIB, and also pack the code
pascal/lpc.py --link --pack MYPROG

# Just link an already compiled MYPROG.OBJ with IOSPASLIB, into XMYPROG.OBJ
linker/lisalinker.py -o XMYPROG MYPROG IOSPASLIB
```

* The libraries named after `--link=` (comma-separated), or after the program
  on the `lisalinker.py` command line, are linked after the program, in order,
  the way the Workshop's Linker takes them:
  * `.OBJ` is added when needed, and case is ignored.
  * A name that is not in the current directory is looked up in the boot folder
    (`$LISA_BOOT`, the same one the compiler uses; see
    [`pascal/README.md`](pascal/README.md#units-u-file-and-the-intrinsic-library)).
  * `<FILE` reads more names from the text file `FILE.TEXT`.
* Which libraries a program needs depends on the units it uses. When a name is
  undefined, the Linker says which library in the boot folder has it.
* The program file is written the way that boot folder's Workshop version
  writes it (1.0/2.0 or 3.0). `--pack` packs the code with the boot folder's
  `SYSTEM.UNPACK`.
* `linker/lisalinker.py` can also be run on its own:
  `lisalinker.py -o OUT IN... [-m MAP] [-p] [-w VERSION]`.
* With `-i` it links intrinsic units into an intrinsic library instead, as the
  Workshop Linker's `+I` option does (`-s OLD=NEW` is `+M OLD NEW`):
  `lisalinker.py -i -s SgPASres=PASIOLIB -o LIBPL/IOSPASLIB LIBPL/PASLIB ...`.
  The unit and segment numbers come from `INTRINSIC.LIB` (`--iulib`).
* `-P` is a physical link, the Workshop Linker's `+P`: a program that runs
  before the MMU is set up, with its code at address 0 (`LIBHW`'s `SYSTEM.LLD`;
  one segment only).

## Assembling

`assembler/assembler.py` is the Workshop's 68000 Assembler, in Python: it
writes the object file the Workshop 3.0 Assembler writes, byte for byte, for
the Linker. Its arguments answer the Assembler's prompts (input file, listing
file, output file), as on the Lisa:

```sh
assembler/assembler.py MYASM                      # MYASM.TEXT -> MYASM.OBJ
assembler/assembler.py +P MYASM MYASM.LST         # with a pretty listing
pascal/lpc.py --link=MYASM,IOSPASLIB MYPROG       # link it with a program
```

See [`assembler/README.md`](assembler/README.md).

## The two builds: 3.0 and 2.0

The compiler can run as either of two Workshop versions:

| Build | For | Select with | Tests |
|---|---|---|---|
| 3.0 (default) | Code written for Workshop 3.0 | `--3.0` (default) | `BUILD=3.0` (default) |
| 2.0 | Code written for Workshop 1.0 / 2.0 | `--2.0` before file arguments in `pascal/lpc.py`, `pascal/pascal.py`, or `pascal/code.py` | `BUILD=2.0` |

Differences between the 2.0 and 3.0 builds:

| Where | 2.0 | 3.0 |
|---|---|---|
| `pascal/pas_init.py` | `CallGen = False` | `CallGen = True`: the front end chains to the code generator by default (prompt `"Output file - [.OBJ]"`), as in Workshop 3.0; `$G-` switches it off |
| `pascal/pas_body.py` (`_Assignment`, `PCKDASS`) | `_MakeScSize(gAttr, 1)` rejects `128..255` | Allows unsigned byte constants `128..255` when assigning to a byte-packed array element such as QuickDraw `Pattern = PACKED ARRAY[0..7] OF 0..255` (range-checked against the element subrange first), as in the Workshop 3.0 compiler |
| `pascal/codegen.py` (`Init`) | — | `OIAllowAbort = False` (the Workshop 3.0 `ObjIOLib`'s abort flag; no effect on the host) |
| `pascal/codegen.py` (`LoadAOrd`, `BOOL` and `BITZ`) | `CheckClobber(D)` | `if D != IntoReg: CheckClobber(D)`, as in the Workshop 3.0 compiler |

In the repository's regression suite (`tests/run_icode_tests.sh`,
`tests/run_obj_tests.sh`), both builds produce identical `.I` and `.OBJ` files
(`tests/run_all.sh` runs the 3.0 build; `BUILD=2.0 tests/<script>` runs any
script with the 2.0 build). Across the full Lisa Office System source build
(`tests/run_lisa_sources_build_tests.sh`), 3 units (`NEWFPLIB`, `MATHLIB`,
`UTEXT`) depend on the 3.0 boolean-register change in `LoadAOrd`.

## Sample build scripts

You can easily automate all steps of the build process using linux shell scripts. 
See examples [here](https://github.com/TorZidan/LisaSerialFtp/blob/main/src/client/make.sh)
and [here](https://github.com/TorZidan/LisaOfficeSystemTextEditor/blob/main/make.sh).

## Getting the built files to your Lisa

Once you have cross-compiled and linked a Workshop program (`MYPROG.OBJ`) or an
Office System desktop tool (`{T<id>}Obj`, `{T<id>}PHRASE`, `{T<id>}ICON`), there
are two main ways to get the built files onto your Lisa.

Both approaches work in the **[LisaEm](https://github.com/arcanebyte/lisaem)** emulator
and on a **real Apple Lisa** using a ProFile hard-disk hardware emulator such as
**ESProfile** (whose hard-disk image files live on a microSD card) or a
floppy hardware emulator such as **FloppyEmu** or **ESFloppy**.

### Option 1: Write directly to a disk image (use `file-system-tools/` and `installtool/`)

[`file-system-tools/LisaFileSystemToolPerFile.py`](file-system-tools/LisaFileSystemToolPerFile.py)
reads and writes files directly on Lisa `.dc42` floppy images and raw/DC42
ProFile hard-disk images (`put` adds a file if absent or replaces it if already
present; `.TEXT` files are automatically converted into Lisa 1 KB text pages).

* **On a real Lisa with an ESProfile:** shut down the Lisa, move the microSD /
  SD card from the ESProfile to your PC, update the ProFile `.image` file on the
  card, then move the SD card back to the ESProfile and boot. (Or write to a
  `.dc42` floppy image on a FloppyEmu / ESFloppy and copy from it on the Lisa.)
* **In LisaEm:** close LisaEm first so it does not hold the disk image open, run
  `put` against your ProFile image (or against a `.dc42` floppy image and mount
  it via **File -> Insert Diskette**), then boot LisaEm.

**For a Lisa Workshop program:**

```sh
python3 file-system-tools/LisaFileSystemToolPerFile.py put disk.image MYPROG.OBJ MYPROG.OBJ
```

Boot into Lisa Workshop, press `R` (*Run*), and enter `MYPROG`. (If you placed
`MYPROG.OBJ` on a `.dc42` floppy image instead of the ProFile image, you can
copy it onto your hard disk inside Workshop: press `F` for *File-Mgr*, `C` for
*Copy*, and copy `-UPPER-MYPROG.OBJ` to `-LOWER-MYPROG.OBJ` on a Lisa 2/5 — on a
Lisa 2/10 the floppy drive is `-LOWER-` and the hard disk is `-UPPER-`.)

**For a Lisa Office System desktop tool** (compile alerts/menus with
[`alert/alert.py`](alert/README.md), convert a 48x32 PNG icon with
`icon-tool/png2lisaicon.py`, copy `{T<id>}Obj` / `PHRASE` / `ICON`, and register
the tool in `{!CATALOG}` with
[`installtool/installtool.py`](installtool/README.md)):

```sh
python3 alert/alert.py MyToolAlerts.text '{T197000}'
python3 icon-tool/png2lisaicon.py icon_48x32.png MyToolIcon.BIN

python3 file-system-tools/LisaFileSystemToolPerFile.py put disk.image MYTOOL.OBJ        '{T197000}Obj'
python3 file-system-tools/LisaFileSystemToolPerFile.py put disk.image '{T197000}PHRASE' '{T197000}PHRASE'
python3 file-system-tools/LisaFileSystemToolPerFile.py put disk.image MyToolIcon.BIN    '{T197000}ICON'

python3 installtool/installtool.py --image disk.image Y '' 197000 Y N 'My Tool'
```

### Option 2: Transfer over serial with [LisaSerialFtp](https://github.com/TorZidan/LisaSerialFtp)

[**LisaSerialFtp**](https://github.com/TorZidan/LisaSerialFtp) transfers binary
and `.TEXT` files between your PC and a running Lisa over **Serial Port B
(`RS232B`)** at up to **57,600 baud** with chunked CRC-16 verification —
avoiding SD-card swaps or emulator restarts on every edit-compile-run cycle. It
includes **both a Workshop client and a Lisa Office System desktop client**, and
you can use either one:

* **`LisaSerialFtpClient`** (`LisaSerialFtpClient.obj`): interactive console
  client for **Lisa Workshop**.
* **`LosSerialFtpClient`** (**Serial FTP**, tool `{T197001}`): native GUI
  desktop tool for the **Lisa Office System (LOS 3.1)**.

Both clients are pre-installed on `LisaSerialFtp`'s
`LisaSerialFtpClient.dc42` floppy image (and on its ready-to-boot ProFile image,
or you can copy them onto your existing ESProfile SD card / LisaEm disk image
once using Option 1 above; see the
[LisaSerialFtp installation guide](https://github.com/TorZidan/LisaSerialFtp#get-the-lisaserialftpclientobj-executable-into-workshop)).

> [!NOTE]
> **Reboot the Lisa after copying or updating system/desktop files.** After
> writing to a disk image on your PC, always boot the Lisa fresh (never resume a
> suspended emulator state whose cached filesystem metadata no longer matches
> the image on disk). Even when transferring over `LisaSerialFtp`, it is a good
> idea to **reboot the Lisa** (in LOS: **File/Print -> Shut Down**; in Workshop:
> `Q` to quit to the Environments Selector or reboot) after replacing an Office
> System desktop tool (`{T<id>}Obj`, `{T<id>}PHRASE`, `{T<id>}ICON`) or shared
> library so the OS and Desktop Manager pick up the updated files cleanly
> instead of using cached in-memory copies.

## Tests

The test suite in `tests/` combines clean-room feature tests with Lisa-built
reference `.obj` comparisons:

| Folder | Contents |
|---|---|
| `tests/base_tests/` | 12 compiler feature tests: arithmetic, control flow, packed/variant types, sets, strings, nested scopes, `INLINE`, multi-segment code, optimizer, multi-unit `USES`, Clascal subclassing/dispatch, and error recovery (`T_ERRS.TEXT`) |
| `tests/iulib/` | Intrinsic-library `USES` lookup tests (`INTRINSIC.LIB`) |
| `tests/gen/` | Gen disk: `FLAGS.TEXT`, `HIDESYSCALL.TEXT`, and Lisa-built `HIDESYSCALL.obj` |
| `tests/workshop-QD/` | QuickDraw sample programs (`BOXES`, `QDSAMPLE`) and Lisa-linked `.obj` references from Workshop 1.0 and 2.0 |

| Script | Checks |
|---|---|
| `tests/run_all.sh` | Runs everything below except the disassembler check, the downloaded-application tests (`tests/downloaded_apps/`), and the two Lisa source-image tests (`run_asm_test.sh`, `run_lisa_sources_build_tests.sh`), with the 3.0 build, each against its baseline (`--save` writes them) |
| `BUILD=2.0 tests/<script>` | Runs any test script below with the 2.0 build (baselines `*-build2.0.txt`); by default they use the 3.0 build (baselines `*-build3.0.txt`) |
| `tests/run_cmdline_tests.sh` | Command-line mode: arguments give the same files as answers on stdin, `pascal/lpc.py` matches the two-pass build, `$ASM+` listings, custom output names, and a program with errors (`T_ERRS`) finishes cleanly |
| `tests/run_link_tests.sh` | Linker ([`linker/`](linker/README.md)): compiles the QuickDraw samples `BOXES` and `QDSAMPLE`, links them with `linker/lisalinker.py` and the Workshop 1.0/2.0 libraries, and compares with the Lisa-linked programs (`BOXES` byte-identical; `QDSAMPLE` identical except `INITICON`). Also checks packed code: every `PackedCode` block in `libs/workshop*` must pack again to the same bytes, and `BOXES` linked with `-p` must unpack to the Lisa-linked code. Also checks `pascal/lpc.py --link` (with and without `--pack`), rejecting a unit, and naming the library that defines missing symbols |
| `tests/run_icode_tests.sh \| diff tests/icode_baseline-build3.0.txt -` | Front end: MD5 of the `.I` of every test program (including `T_ERRS`) |
| `tests/run_obj_tests.sh \| diff tests/obj_baseline-build3.0.txt -` | Both passes: each `.OBJ` against its Lisa-built reference, plus MD5 of all `.OBJ` files |
| `tests/run_workshop_tests.sh` | Runs `run_obj_tests.sh` once per Workshop version (`WORKSHOP=1.0`, `2.0`, `3.0`), comparing each against `tests/obj_baseline-workshopX-build3.0.txt` (`--save` writes them) |
| `tools/cmplinked.py OUR.OBJ LINKED.OBJ` | Finds each procedure of our `.OBJ` in a Lisa-linked program, skipping the bytes the Linker fills in |
| `tests/disasm/check_expected.sh` | Checks the code generator's 68000 disassembler (`pascal/gen_disasm.py`, used for `$ASM+` listings) against 113 hand-encoded instructions (`tests/disasm/expected.txt`); `tests/disasm/disasmtest.py` also disassembles one instruction, all 65,536 first words, or a byte range of a file |
| `tests/downloaded_apps/run_all.sh` | Runs all 18 downloaded-application tests in [`tests/downloaded_apps/`](tests/downloaded_apps/README.md): `run_los_minesweeper_test.sh`, `run_lisamiles_test.sh`, the 14 GyroPilot Lisa Office System desktop tools, `run_lostexteditor_test.sh`, and `run_serialftp_test.sh` — downloading sources, includes, alerts, and `.dc42` disk images, checking `audit_8char.py`, assembling/compiling/linking, running `alert/alert.py`, and verifying `{T<id>}Obj` and `{T<id>}PHRASE` byte for byte against each `.dc42` image. Needs network access, so it is not part of `tests/run_all.sh` |
| `tests/run_asm_test.sh` | Assembles the 68000 assembly sources of the Lisa Office System on `LOS_IMAGE` (`tests/LOSandWorkshop3.0_WithCompiledLisaSources_DO_NOT_COMMIT.image`) with `assembler/assembler.py`, following its 28 `ALEX/ASM/*` exec files (including `CHANGESEG` and `FIXMOVE`): 105 sources with their include files and macros, all byte-identical to the Lisa-built objects on the image. Not part of `run_all.sh` because the image contains copyrighted Lisa source files and is not in this repository |
| `tests/run_lisa_sources_build_tests.sh` | Builds the Lisa Office System from the sources on `LOS_IMAGE`, following its exec files from `ALEX/MAKE/ALL_NODISKS`: libraries, applications (LisaWrite, LisaCalc, LisaDraw, LisaGraph, LisaProject, LisaList, LisaTerminal, Desktop Manager, ...), `SYSTEM.OS` with its drivers and OS programs, and the installer. Assembles 105 sources with `assembler/assembler.py`, compiles ~280 units and programs, links ~70 programs and libraries, and generates 17 alert/menu phrase files with `alert/alert.py`: 473 files on the image (about 4 minutes), all byte-identical to the Lisa-built ones. Single targets (`APLW`) or exec files (`ALEX/LINK/SYS1LIB`) can be passed; with `BUILD=2.0`, the 3 expected unit differences are reported. Not part of `run_all.sh` because the image contains copyrighted Lisa source files and is not in this repository |

`run_obj_tests.sh` checks:

* **Core feature & Clascal tests** (`tests/base_tests/`): all 11 compilable
  units and programs build cleanly through both passes (`T_ERRS` intentionally
  tests front-end error recovery), with MD5 checksums recorded in
  `tests/obj_baseline*.txt`.
* **Byte-identical to the Lisa `.OBJ`:** the compiler's own unit
  `tests/gen/HIDESYSCALL.TEXT` (`SYSCALL.obj` and `PASLIBCALL.obj` resolved
  from each Workshop version's `libs/workshop*` folder; identical across 1.0,
  2.0, and 3.0).
* **The QuickDraw samples** `QDSAMPLE` and `BOXES` (`tests/workshop-QD/`, the
  `QD` folder of the Workshop 1.0 and 2.0 disks): their Lisa `.OBJ` files are
  linked programs (a 1.0 and a 2.0 build, which differ only in the linked
  libraries), so each procedure is compared with `tools/cmplinked.py`. All 10
  procedures are identical except `QDSAMPLE`'s `INITICON`, whose Lisa build
  predates literal-pool compaction and keeps 5 duplicate strings (250 bytes
  more); the instructions match apart from the `PEA` offsets into the pool.

## Layout

| Path | Description |
|---|---|
| [`pascal/`](pascal/README.md) | Compiler: `pascal.py` (front end), `code.py` (code generator), `lpc.py` (driver: front end, code generator if `$G+`, and Linker with `--link` / `--pack`; `--2.0` selects the 2.0 build), `audit_8char.py` (8-character identifier collision checker), compiler modules, `PASERRS.ERR` |
| [`assembler/`](assembler/README.md) | 68000 Assembler: `assembler.py`, `asm68k.py`, opcode table `N68K.OPCODES`, `changeseg.py` |
| [`linker/`](linker/README.md) | Linker: `lisalinker.py` (program and `-i` intrinsic-library linker), `lisaintrinsic.py`, `lisapack.py` (code packer/unpacker), `lisadump.py`, `lisaobj.py` |
| [`alert/`](alert/README.md) | Menu/Phrase File Generator (`alert.py`, equivalent to Workshop `Alert.obj`) |
| [`installtool/`](installtool/README.md) | Tool Install utility (`installtool.py`, equivalent to Workshop `InstallTool.obj`): registers an Office System desktop tool (`{T<id>}Obj`, `PHRASE`, `ICON`) on a Lisa disk image |
| `icon-tool/` | `png2lisaicon.py`: converts a 48x32 PNG into a Lisa Office System `{T<id>}ICON` desktop icon file |
| [`file-system-tools/`](file-system-tools/README.md) | `LisaFileSystemTool.py` and `LisaFileSystemToolPerFile.py`: read and write files on Lisa DC42 and ProFile disk images |
| `libs/workshop3.0/`, `libs/workshop2.0/`, `libs/workshop1.0/` | Workshop 3.0, 2.0, and 1.0 boot-volume libraries (`INTRINSIC.LIB`, intrinsic `.obj` libraries, `SYSCALL.obj`, `PASLIBCALL.obj`, `SYSTEM.UNPACK`, and API reference `.md` docs) |
| `tools/objdump.py` | Dumps the blocks of a Lisa `.OBJ` file |
| `tools/cmplinked.py` | Finds each procedure of a compiled `.OBJ` in a Lisa-linked program |
| `docs/` | Apple Lisa manuals used as references |
| `tests/` | Test suites, downloaded-app harnesses, scripts, and baselines |

## Host library units

The compiler itself used Lisa library units: `StdUnit`, `IOPrimitives`, and
`ProgComm` from `SULib`, `FileIO` and `ObjIO` from `ObjIOLib`, `PasDefs`,
`ObjInter`, `IUMan`, `HideSysCall`, `SysCall`, `PaslibCall`, `HWInt`, `FPLib`,
`Times`, `Dates`, and the UCSD/Lisa file intrinsics. Their host implementations
live in `pascal/lisalib.py` and match the Lisa interfaces (see
[`libs/workshop3.0/SULIB.md`](libs/workshop3.0/SULIB.md) and
[`libs/workshop3.0/OBJIOLIB.md`](libs/workshop3.0/OBJIOLIB.md)):

* `ObjIO` writes the Lisa object file format (block type byte, 3-byte size,
  big-endian fields).
* `IUMan` and `ObjInter` look a unit up in `INTRINSIC.LIB` (unit table `$9D`,
  file names `$9E`) and read its interface from the library file.
* File names are matched case-insensitively and Lisa volume prefixes (`-vol-`,
  `*`) are dropped. A plain Unix `.TEXT` file is presented to the compiler as a
  Lisa text file (1 KB header, 1 KB pages, DLE indentation, CR line ends).
  Lisa-format files and `.OBJ` files are read unchanged.
* Like the Lisa, `IOPrimitives` replaces a file opened for writing only when it
  is closed. The code generator relies on this: it reads the front end's
  listing and writes the merged listing under the same name.
  `PutStrS`/`PutIntP`/`IOError` follow the documentation in the `IOPrimitives`
  interface text found on the Gen disk.

## Known limitations

* **Disassembler not compared with a Lisa listing:** `pascal/gen_disasm.py` is
  checked against the instruction table, all 65,536 first words, and the test
  programs' listings, but not against a `$ASM+` listing produced on a Lisa.
* **`$D` symbol dump:** the front end's `$D` debug-symbol dump prints integer
  IDs standing in for Lisa heap pointers, so those pointer numbers differ from
  a dump made on a Lisa.
* **`MemAvail`** always reports 32,767 words.
* **Compile-time `$IFC` variables in certain unit interfaces:** an intrinsic
  unit whose embedded `INTERFACE` uses a compile-time `$IFC` variable without a
  prior `$SETC` (such as `ObjIOLib`'s `isIntrin`, or Workshop 1.0/2.0
  `StdUnit`'s `ForOS` unless `{$SETC ForOS := TRUE}` is set) gives error 261,
  just as on the Lisa.
