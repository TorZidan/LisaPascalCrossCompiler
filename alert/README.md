# Lisa Menu/Phrase File Generator (`alert/`)

A Python version of the Lisa Workshop 3.0 Menu/Phrase File Generator
(`Alert` / `ALERT.OBJ`: `Lisa Menu/Phrase File Generator`): it reads an
alert/menu phrase source file (`.TEXT`) and writes the binary `PHRASE` file
read at run time by `AlertMgr`'s `InitMP`, `OpenPhraseFile`, and `ReadAlerts`,
byte for byte.

| File | Role |
|---|---|
| `alert.py` | Menu/Phrase File Generator: CLI & interactive dialog, parser, and binary `PHRASE` writer |

## Original Lisa Sources & Executables

* **Workshop 3.0 source:** `LISA_OS/TKALERT.TEXT` (identical copy at
  `LISA_OS/Linkmaps and Misc. 3.0/TKALERT.TEXT.unix.txt`) in the Computer
  History Museum `Lisa_Source` archive. Compiling `TKALERT.TEXT` with `{$D-}`
  and linking against Workshop 3.0 (`IOSPASLIB`, `SYS1LIB`, `SULIB`, `SYSCALL`)
  produces all 16,340 bytes of machine code identically to `alert.obj` on the
  Workshop 3.0 disk image (`Lisa_Toolkit/TK3/TK-ALERT.OBJ` is the `{$D+}` link
  of the same source).
* **Earlier LOS 1.0 source (alerts only, before menus/`InitMP`):**
  `LISA_OS/LIBS/LIBAM/libam-ALERTGEN.TEXT.unix.txt` (`12/26/82 -- A4`), with
  the runtime reader in `LISA_OS/LIBS/LIBAM/LIBAM-ALERTMGR.TEXT.unix.txt`.

## Use

```sh
alert/alert.py LosSerialFtpClientAlerts.text '{T197001}'  # -> {T197001}PHRASE
alert/alert.py MYTOOL                                     # MYTOOL.text -> MYTOOLPHRASE
alert/alert.py +L MYTOOL                                  # list tokenized input (+L, -L, /L)
alert/alert.py                                            # interactive, as on the Lisa
printf 'LosSerialFtpClientAlerts.text\n{T197001}\n' | alert/alert.py
```

*(Note: in Workshop `$EXEC` scripts such as `LosSerialFtpClientMake.text`,
`~{T197001~}` uses `~` to escape `{` and `}` from `$EXEC` comment stripping;
the actual answer passed to `Alert` is `{T197001}`, producing
`{T197001}PHRASE`.)*

Arguments answer the prompts in order, as on the Lisa:

```text
Lisa Menu/Phrase File Generator

Type ? to set the options.

Input File Name [.TEXT] LosSerialFtpClientAlerts.text
Output File Name [LosSerialFtpClientAlertsPHRASE] {T197001}
```

* `.text` is added to the input file name unless already present (or suppressed
  with a trailing `.`); `PHRASE` is appended to the output file name unless it
  already ends with `PHRASE` (case-insensitive) or a trailing `.`.
* Answering `?` at either file prompt (or passing `+L`, `-L`, or `/L` on the
  command line) enables tokenized-input listing to stdout.
* Input files may be host text files, Lisa `.TEXT` files (1024-byte header
  page, `CR` line endings, `DLE` leading-space compression), or CHM
  `Lisa_Source` files with a trailing `0xFF` marker.
* Include directives `$FILENAME`, `$FILENAME~SECTION`, and `$~SECTION` (up to
  2 nesting levels), `;` comment lines, and leading `~` line-quote characters
  work as in `TKALERT.TEXT`.

## Verification Status

Verified byte for byte against **34 `PHRASE` binaries** across the Lisa Office
System 3.0 build image (`../tests/run_lisa_sources_build_tests.sh`, all 17
system and application phrase files) and all 17 phrase-using desktop tools in
[`../tests/downloaded_apps/`](../tests/downloaded_apps/README.md) (16
Lisa-built `.dc42` images plus `LisaSerialFtpClient.dc42`):

| Phrase Binary | Source | Bytes | Result |
|---|---|---:|---|
| `{T197000}PHRASE` (LosTextEditor) | `LosTextEditorAlerts.text` | 1,669 | identical |
| `SYSTEM.CIALERTS.PHRASE` | `LIBPR/libpr-cialerts.text` | 2,346 | identical |
| `SYSTEM.CNALERTS.PHRASE` | `LIBPR/LIBPR-CNALERTS.TEXT` | 2,114 | identical |
| `SYSTEM.DW.PHRASE` | `LIBPR/LIBPR-DAISYWHEELALERT.TEXT` | 2,531 | identical |
| `SYSTEM.PARENT.PHRASE` | `LIBPR/LIBPR-PARENTALERT.TEXT` | 3,483 | identical |
| `SYSTEM.PR.PHRASE` | `LIBPR/libpr-PRALERT.TEXT` | 2,459 | identical |
| `APDM/DMALEXPHRASE` (Desktop Mgr) | `APDM/APDM-ALERT.TEXT` + `$ApDm/Alert2` | 47,010 | identical |
| `{T11}PHRASE` (Preferences) | `APPW/appw-alerts.text` | 11,209 | identical |
| `{T12}PHRASE` (Calculator) | `APHP/aphp-T12ALERT.TEXT` | 4,617 | identical |
| `{T13}PHRASE` (Clock) | `APCL/APCL-T13ALERT.TEXT` | 2,142 | identical |
| `{T102}PHRASE` (LisaProject) | `APLP/aplp-t8alert.text` | 14,908 | identical |
| `{T103}dbcPHRASE` (LisaList DBC) | `APLL/apll-t5dbc.text` | 4,359 | identical |
| `{T103}lmPHRASE` (LisaList) | `APLL/APLL-T5LM.TEXT` | 22,300 | identical |
| `{T104}PHRASE` (LisaTerminal) | `APLT/aplt-t10menus.text` | 11,689 | identical |
| `{T105}PHRASE` (LisaWrite) | `APLW/APLW.T1ALERT.TEXT` | 12,613 | identical |
| `{T106}PHRASE` (LisaDraw) | `APLD/APLD-T4ALERT_MENUS.TEXT` | 9,437 | identical |
| `{T107}PHRASE` (LisaCalc) | `APLC/aplc-T3ALERT.TEXT` | 27,443 | identical |
| `{T108}PHRASE` (LisaGraph) | `APBG/APBG-T2ALERT.TEXT` | 26,117 | identical |

## Binary `PHRASE` Format Summary

1. **Menu section** (present only when `cacheSize > 0` and at least 1 menu is defined):
   * `menuCount` (`uint16` big-endian)
   * For each menu:
     * `menuId` (`uint16`), `enableFlags` (4 bytes: `packed array[1..32] of boolean`, bit 0 of byte 0 = menu enable, bit `k` = item `k`), `menuLen` (`uint16`, padded to even)
     * `title` (`len` byte + ASCII bytes)
     * Each item: `len` byte + text + `appleChar` (1 byte, `' '` if none) + `noMark` (`0x00`) + `styleChar` (1 byte, `' '` if none)
     * End-of-menu 4-byte sentinel (`00 DC FD DC`, from `HAllocate(hz, 1)` written out as 4 bytes in `WrMenus`), plus `01` (`wasOdd = TRUE`) if `menuLen` was odd before padding
   * Command number table (`itemCount` `uint16`, followed by sorted 4-byte `(comId: int16, menu: uint8, item: uint8)` records for items with `#comId > 0`)
   * `cacheSize` (`uint16`), `cacheBytes` (`uint16`)
2. **Alert section**:
   * `version` (`uint16`)
   * 5 sign definitions (`?`, `wait`, `stop`, `note`, `caution`): 16-byte space-padded `string[15]`, `signPoints` (`uint16`), and `signPoints + 1` QuickDraw `Point`s (`v: int16, h: int16`)
   * `lastButn` (`uint16`, `1..6`) and `lastButn + 1` 16-byte space-padded button strings (`Cancel`, `OK`, ...)
   * `numAlerts` (`uint16`) and `numAlerts` 6-byte `TAlertInfo` records:
     * `alertNumber` (`uint16`)
     * `(alertKind << 4) | (fBox0 << 3) | (fBox1 << 2) | (fBox2 << 1) | fBox3` (`uint8`)
     * `(vol0 << 6) | (vol1 << 4) | (vol2 << 2) | vol3` (`uint8`)
     * `textLength` (`int16`: byte count, or `-index` for `=n` equated alerts)
   * Concatenated tokenized alert text blocks (word-length/token byte + characters; `getProc` stageless alerts store a single raw Pascal string)
   * 1-byte checksum so the sum of all bytes in the file modulo 256 equals `50` (`(50 - sum) & 0xFF`)
