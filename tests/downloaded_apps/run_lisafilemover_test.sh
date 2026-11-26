#!/bin/sh
# Download LisaFileMover 1.1 (https://github.com/GyroPilot/Apple-LisaFileMover),
# audit, compile and link its Pascal sources and phrase file, and verify
# byte-for-byte identity against {T419311}Obj and {T419311}PHRASE on
# LISAFILEMOVER_1_1.dc42.
#
#   tests/downloaded_apps/run_lisafilemover_test.sh
#   BUILD=2.0 tests/downloaded_apps/run_lisafilemover_test.sh
#   APP_URL=<url> APP_DC42=<url> tests/downloaded_apps/run_lisafilemover_test.sh
APP_NAME="LisaFileMover 1.1"
APP_REPO="https://github.com/GyroPilot/Apple-LisaFileMover"
APP_PREFIX="LFU"
APP_TOOL_ID="419311"
APP_SRC_URL="${APP_URL:-https://raw.githubusercontent.com/GyroPilot/Apple-LisaFileMover/main/sources}"
APP_DC42_URL="${APP_DC42:-https://raw.githubusercontent.com/GyroPilot/Apple-LisaFileMover/main/LISAFILEMOVER_1_1.dc42}"
APP_UNITS="GLOBALS UNIT"
APP_LINK_UNITS="GLOBALS UNIT"
APP_INCLUDES=""
APP_LIBS="IOSPASLIB,SYS1LIB,SYS2LIB"

. "$(dirname "$0")/common.sh"
run_gyropilot_app_test
