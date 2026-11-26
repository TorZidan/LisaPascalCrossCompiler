# Lisa Tool Install Utility (`installtool/`)

A Python version of the Lisa Workshop 3.0 `InstallTool` utility
(`INSTALLTOOL.OBJ`): it registers a Workshop-built Office System tool
(`{T<id>}Obj`, plus optional `{T<id>}PHRASE` and `{T<id>}ICON`) into the Lisa
Office System desktop directly on a host Lisa disk image (DC42 or raw
ProFile/Widget).

| File | Role |
|---|---|
| `installtool.py` | Tool Install utility: CLI & interactive dialog, `{!CATALOG}` B-tree database reader/writer, `ToolSize` block/timestamp scanner, and `{T<id>}Obj` OS file-label writer |

## Original Lisa Sources & Executables

* **Workshop 3.0 source:** `LISA_OS/TKIN/tkin-source.TEXT.unix.txt` and
  `LISA_OS/TKIN/TKIN-ENTRY.TEXT.unix.txt` in the Computer History Museum
  `Lisa_Source` archive.
* **Supporting Office System & Database units:**
  * `APPS/APDM/APDM-CAT.TEXT.unix.txt` & `APPS/APDM/APDM-GLOBALS.TEXT.unix.txt`
    (`TCatRec`, `LabelFmt`, `LabelIO`, `OpenCat`, `AddCatRec`, `DelCatRec`,
    `UpdCatRec`, `ObjInCat`)
  * `LISA_OS/LIBS/LIBFC/libfc-FILERCOMM.TEXT.unix.txt` (`ObjectKind` values:
    `toolKind = 24`, `docPad = 5`)
  * `LISA_OS/LIBS/LIBDB/` (`filelabel`, `pagedesc`, `vltree`, `qasm` key
    comparison) and `LISA_OS/LIBS/LIBIN/` (`CompChrMagnitude` international
    collation tables)
  * `LISA_OS/OS/source-fsui3.text.unix.txt` (`Write_Label` / `UserLabel_IO` at
    `MDDF.flabel_offset`)
* **Workshop 3.0 executable:** `installtool.obj` (14,336 bytes) on the Workshop
  3.0 disk image.

## What `InstallTool` Does on Disk

1. **Opens `{!CATALOG}`** (the Filer's `LIBDB` B-tree database file on the
   target Lisa disk image; errors out with `not a Lisa Office System 3.0 disk!`
   if `{!CATALOG}` is not present).
2. **Handles existing tool conflicts (`SameToolID` / `SameName`):**
   * If a `toolKind` record with the same `toolID` already exists in
     `{!CATALOG}` and replacement is confirmed (`Y` at prompt 1 or at the
     per-tool prompt), preserves its container `parentID`, desktop icon
     position `closedPt`, and window `openRect`, records its old name, and
     removes the old tool record.
   * Warns if another tool with a different `toolID` already uses the same
     desktop name.
3. **Computes `ToolSize` and `created` (`Assignment`):** scans all root-level
   files on the volume whose name starts with `{T<id>}` (case-insensitive, such
   as `{T<id>}Obj`, `{T<id>}PHRASE`, `{T<id>}ICON`), summing
   `ceil(physSize / dataSize) + fs_Overhead` blocks and taking `max(dtc)`
   (32-bit signed Lisa timestamp).
4. **Updates `{!CATALOG}` (`AddRecToCat` & `Stationery`):**
   * Allocates the next unique `selfId` from `filelabel.tickets.low` and
     inserts the `toolKind` (`24`) `TCatRec` sorted by
     `(parentId, CompChrMagnitude(name, veryWeak=True), selfId)`.
   * If the tool creates documents (`noDocs = False`), updates or inserts its
     `<Name> Paper` stationery pad (`docPad = 5`, `objSize = 0`); if
     `noDocs = True` and an old `<OldName> Paper` existed, deletes it.
   * Increments `filelabel.updateversion` and sets `ffileok`.
5. **Writes the OS file label (`MakeLabel` / `LabelIO`):** packs the 88-byte
   version-2 `LabelFmt` record (`version = 2`, `name`, `kind = 24`, `toolOnly`,
   `multiDoc`, `windLoc`, `split = -32768`, `totalSize = 0`, `parentID = 1`)
   into hint page 0 of `{T<id>}Obj` at `MDDF.flabel_offset` (`0x180`), updating
   ProFile 20-byte tag checksums or DC42 header checksums via
   `LisaFileSystemTool`.

## Use

```sh
# Using --image (or $LISA_IMAGE) so the exact 6 answers from LosSerialFtpClientMake.text work verbatim:
installtool/installtool.py --image disk.image Y '' 197001 N N 'Serial FTP'

# Or passing the disk image path directly at the device prompt:
installtool/installtool.py Y disk.image 197001 N N 'Serial FTP'

# Piped answers on stdin (same 6 lines as LosSerialFtpClientMake.text lines 74-79):
printf 'Y\n\n197001\nN\nN\nSerial FTP\n' | installtool/installtool.py --image disk.image

# Interactive mode:
installtool/installtool.py --image disk.image
```

### Prompts (in order)

1. `Do you want to automatically overwrite an existing tool with the same number? ( Y or N ) [NO] >> `
2. `Please enter the name of the device your tool is on. [PARAPORT]. >> `
   *(host disk image path, or blank/`PARAPORT` when `-i`/`--image` or `$LISA_IMAGE` is set)*
3. `Please enter your tool id number >> `
   *(if the tool ID already exists and prompt 1 was `N`, asks `Do you wish to replace the current tool?`)*
4. `Does your tool create documents? ( Y or N ) [YES] >> `
   *(if `Y`, also asks `Can your tool handle MORE THAN ONE document at a time?`)*
5. `Do you wish to specify a different one? ( Y or N ) [NO] >> `
   *(default opening rectangle `10, 40, 640, 290`; if `Y`, asks `left`, `top`, `right`, `bottom`)*
6. `Please enter the name of your tool. >> `
   *(if another tool already uses that name, prompts for a new name or `<CR>` to keep)*

Uses `LisaFileSystemToolPerFile.py` from [`../file-system-tools/`](../file-system-tools/)
(another folder can be given with `--fs-tool <dir>`).
