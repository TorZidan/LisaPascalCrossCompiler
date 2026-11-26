#!/bin/sh
# Download 1000 Miles (https://github.com/wottle/LisaMiles), audit, compile and
# link its Pascal units, main program, icon-writer helper (MILES-MKICON.TEXT),
# and phrase file, and verify byte-for-byte identity against {T202}Obj and
# {T202}PHRASE on dist/1000-miles.dc42.
#
#   tests/downloaded_apps/run_lisamiles_test.sh
#   BUILD=2.0 tests/downloaded_apps/run_lisamiles_test.sh
#   APP_URL=<url> APP_DC42=<url> tests/downloaded_apps/run_lisamiles_test.sh
APP_NAME="1000 Miles 1.0"
APP_REPO="https://github.com/wottle/LisaMiles"
APP_PREFIX="MILES"
APP_TOOL_ID="202"
APP_SRC_URL="${APP_URL:-https://raw.githubusercontent.com/wottle/LisaMiles/main/src}"
APP_DC42_URL="${APP_DC42:-https://raw.githubusercontent.com/wottle/LisaMiles/main/dist/1000-miles.dc42}"
APP_UNITS="LOGIC ICONS LAYOUT CTRL GLOBALS DRAW"
APP_LINK_UNITS="GLOBALS DRAW CTRL LAYOUT ICONS LOGIC"
APP_INCLUDES=""
APP_EXTRA_PROGS="MKICON:IOSPASLIB,SYS1LIB"
APP_LIBS="IOSPASLIB,SYS1LIB,SYS2LIB"

. "$(dirname "$0")/common.sh"
run_downloaded_app_test
