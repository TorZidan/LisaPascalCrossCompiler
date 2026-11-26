# Downloaded Lisa Application Tests (`tests/downloaded_apps/`)

End-to-end network tests that download real-world Apple Lisa Workshop and Office
System applications from GitHub, check 8-character identifier rules with
`pascal/audit_8char.py`, assemble any 68000 sources with
`assembler/assembler.py`, compile and link the Pascal units and programs with
`pascal/lpc.py` and `linker/lisalinker.py`, compile alert/menu phrase files with
`alert/alert.py`, and compare the resulting binaries byte for byte against the
executables and phrase files on each project's `.dc42` floppy disk image (17 of
the 18 images were built with Workshop 3.0 on a Lisa; `LisaSerialFtpClient.dc42`
is built with this cross-compiler).

Run all 18 application tests at once (or with `BUILD=2.0`):

```sh
tests/downloaded_apps/run_all.sh
BUILD=2.0 tests/downloaded_apps/run_all.sh
```

Any single script can also be pointed at local sources or disk images via
`APP_URL` and `APP_DC42` (e.g. `APP_URL=file:///path/to/src`).

| Script | Application & Repository | Tool ID | Checked Against `.dc42` |
|---|---|---|---|
| `run_los_minesweeper_test.sh` | LOS Minesweeper (`alexthecat123/los_minesweeper`) | `T201` | `{T201}Obj` (21,504 B) & `{T201}PHRASE` (2,266 B) on `los_minesweeper.dc42` |
| `run_lisamiles_test.sh` | 1000 Miles 1.0 (`wottle/LisaMiles`) | `T202` | `{T202}Obj` (27,648 B) & `{T202}PHRASE` (5,647 B) on `dist/1000-miles.dc42` (+ `MILES-MKICON` helper) |
| `run_lisacom_test.sh` | LISACom 1.7 (`GyroPilot/Apple-LISACom`) | `T419306` | `{T419306}Obj` (32,768 B) & `{T419306}PHRASE` (1,264 B) on `LISACOM_1_7.dc42` |
| `run_atkinsonpoint_test.sh` | AtkinsonPoint 1.1 (`GyroPilot/AtkinsonPoint`) | `T419307` | `{T419307}Obj` (6,656 B) & `{T419307}PHRASE` (3,272 B) on `AtkinsonPoint_v1_1.dc42` |
| `run_lisaslidepuzzle_test.sh` | Lisa Slide Puzzle 1.0 (`GyroPilot/Apple-LisaSlidePuzzle`) | `T419308` | `{T419308}Obj` (8,192 B) & `{T419308}PHRASE` (3,038 B) on `LISA_PUZZLE_1_0.dc42` |
| `run_lisareversi_test.sh` | Lisa Reversi 1.0 (`GyroPilot/Apple-LisaReversi`) | `T419309` | `{T419309}Obj` (12,288 B) & `{T419309}PHRASE` (3,195 B) on `LISA_REVERSI_1_0.dc42` |
| `run_lisafilemover_test.sh` | LisaFileMover 1.1 (`GyroPilot/Apple-LisaFileMover`) | `T419311` | `{T419311}Obj` (29,184 B) & `{T419311}PHRASE` (5,811 B) on `LISAFILEMOVER_1_1.dc42` |
| `run_lisafuji_test.sh` | LisaFuji 1.2 (`GyroPilot/Apple-LisaFuji`) | `T419312` | `{T419312}Obj` (83,968 B) & `{T419312}PHRASE` (2,154 B) on `LISAFUJI_1_2.dc42` |
| `run_lisatwinclock_test.sh` | LisaTwinClock 1.3 (`GyroPilot/Apple-LisaTwinClock`) | `T419313` | `{T419313}Obj` (32,768 B) & `{T419313}PHRASE` (2,108 B) on `LISATWINCLOCK_1_3.dc42` |
| `run_lisafujibrowser_test.sh` | LisaFuji Browser 1.3 (`GyroPilot/Apple-LisaFujiBrowser`) | `T419314` | `{T419314}Obj` (37,376 B) & `{T419314}PHRASE` (1,810 B) on `LISAFUJI_BROWSER_1_3.dc42` |
| `run_lisacheckers_test.sh` | LisaCheckers 1.2 (`GyroPilot/Apple-LisaCheckers`) | `T419317` | `{T419317}Obj` (36,864 B) & `{T419317}PHRASE` (3,493 B) on `LISACHECKERS_1_2.dc42` |
| `run_lisasalvo_test.sh` | LisaSalvo 1.2 (`GyroPilot/Apple-LisaSalvo`) | `T419322` | `{T419322}Obj` (34,304 B) & `{T419322}PHRASE` (2,449 B) on `LISASALVO_1_2.dc42` |
| `run_espfuji_test.sh` | ESPFuji 0.2 (`GyroPilot/ESPFuji`, `espfuji/lisa-tool`) | `T419324` | `{T419324}Obj` (11,776 B) & `{T419324}PHRASE` (1,319 B) on `ESPFUJI_0_2_REVD.dc42` |
| `run_lisafetch_test.sh` | LisaFetch 0.1 (`GyroPilot/Apple-LisaFetch`) | `T419325` | `{T419325}Obj` (20,992 B) & `{T419325}PHRASE` (1,238 B) on `LISAFETCH_0_1.dc42` |
| `run_lisasolstice_test.sh` | LisaSolstice 1.0 (`GyroPilot/Apple-LisaSolstice`) | `T419326` | `{T419326}Obj` (255,488 B) & `{T419326}PHRASE` (8,592 B) on `LISASOLSTICE_1_0.dc42` |
| `run_lisatattletale_test.sh` | Lisa TattleTale 1.0 (`GyroPilot/Apple-LisaTattleTale`) | `T419328` | `{T419328}Obj` (69,632 B) & `{T419328}PHRASE` (1,819 B) on `LISATATTLETALE_1_0.dc42` |
| `run_lostexteditor_test.sh` | LosTextEditor (`TorZidan/LisaOfficeSystemTextEditor`) | `T197000` | `{T197000}Obj` (43,520 B) & `{T197000}PHRASE` (1,669 B) on `LosTextEditor.dc42` |
| `run_serialftp_test.sh` | LisaSerialFtp clients (`TorZidan/LisaSerialFtp`, `src/client`, Pascal + 68000 assembly) | `T197001` | `{T197001}Obj` (59,392 B) & `{T197001}PHRASE` (1,450 B) on `LisaSerialFtpClient.dc42` (+ the Workshop client, `LisaSerialFtpClient.obj`, 51,712 B); the image is built with this cross-compiler |
