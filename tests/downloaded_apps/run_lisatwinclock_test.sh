#!/bin/sh
# Download LisaTwinClock 1.3 (https://github.com/GyroPilot/Apple-LisaTwinClock),
# audit, compile and link its Pascal sources and phrase file, and verify
# byte-for-byte identity against {T419313}Obj and {T419313}PHRASE on
# releases/LISATWINCLOCK_1_3.dc42.
#
#   tests/downloaded_apps/run_lisatwinclock_test.sh
#   BUILD=2.0 tests/downloaded_apps/run_lisatwinclock_test.sh
#   APP_URL=<url> APP_DC42=<url> tests/downloaded_apps/run_lisatwinclock_test.sh
APP_NAME="LisaTwinClock 1.3"
APP_REPO="https://github.com/GyroPilot/Apple-LisaTwinClock"
APP_PREFIX="TWC"
APP_TOOL_ID="419313"
APP_SRC_URL="${APP_URL:-https://raw.githubusercontent.com/GyroPilot/Apple-LisaTwinClock/main/sources}"
APP_DC42_URL="${APP_DC42:-https://raw.githubusercontent.com/GyroPilot/Apple-LisaTwinClock/main/releases/LISATWINCLOCK_1_3.dc42}"
APP_UNITS="GLOBALS UNIT FNBUS NET"
APP_LINK_UNITS="GLOBALS UNIT FNBUS NET"
APP_INCLUDES=""
APP_LIBS="IOSPASLIB,SYS1LIB,SYS2LIB"

. "$(dirname "$0")/common.sh"
run_gyropilot_app_test
