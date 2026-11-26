#!/bin/sh
# Download LisaFetch 0.1 (https://github.com/GyroPilot/Apple-LisaFetch), audit,
# compile and link its Pascal sources and phrase file, and verify byte-for-byte
# identity against {T419325}Obj and {T419325}PHRASE on releases/LISAFETCH_0_1.dc42.
#
#   tests/downloaded_apps/run_lisafetch_test.sh
#   BUILD=2.0 tests/downloaded_apps/run_lisafetch_test.sh
#   APP_URL=<url> APP_DC42=<url> tests/downloaded_apps/run_lisafetch_test.sh
APP_NAME="LisaFetch 0.1"
APP_REPO="https://github.com/GyroPilot/Apple-LisaFetch"
APP_PREFIX="LFT"
APP_TOOL_ID="419325"
APP_SRC_URL="${APP_URL:-https://raw.githubusercontent.com/GyroPilot/Apple-LisaFetch/main/sources}"
APP_DC42_URL="${APP_DC42:-https://raw.githubusercontent.com/GyroPilot/Apple-LisaFetch/main/releases/LISAFETCH_0_1.dc42}"
APP_UNITS="GLOBALS FNBUS"
APP_LINK_UNITS="GLOBALS FNBUS"
APP_INCLUDES=""
APP_LIBS="IOSPASLIB,SYS1LIB,SYS2LIB"

. "$(dirname "$0")/common.sh"
run_gyropilot_app_test
