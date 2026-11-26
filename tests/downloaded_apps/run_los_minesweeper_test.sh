#!/bin/sh
# Download LOS Minesweeper (https://github.com/alexthecat123/los_minesweeper),
# audit, compile and link its Pascal sources and phrase file, and verify
# byte-for-byte identity against {T201}Obj and {T201}PHRASE on
# los_minesweeper.dc42.
#
#   tests/downloaded_apps/run_los_minesweeper_test.sh
#   BUILD=2.0 tests/downloaded_apps/run_los_minesweeper_test.sh
#   APP_URL=<url> APP_DC42=<url> tests/downloaded_apps/run_los_minesweeper_test.sh
APP_NAME="LOS Minesweeper"
APP_REPO="https://github.com/alexthecat123/los_minesweeper"
APP_PREFIX="MINESWEEPER"
APP_TOOL_ID="201"
APP_SRC_URL="${APP_URL:-https://raw.githubusercontent.com/alexthecat123/los_minesweeper/main/src}"
APP_DC42_URL="${APP_DC42:-https://raw.githubusercontent.com/alexthecat123/los_minesweeper/main/los_minesweeper.dc42}"
APP_UNITS="GLOBALS GAME DRAW DIALOG"
APP_LINK_UNITS="GLOBALS GAME DRAW DIALOG"
APP_INCLUDES=""
APP_LIBS="IOSPASLIB,SYS1LIB,SYS2LIB,PRLIB"

. "$(dirname "$0")/common.sh"
run_downloaded_app_test
