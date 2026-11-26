#!/bin/sh
# Download Lisa Reversi 1.0 (https://github.com/GyroPilot/Apple-LisaReversi),
# audit, compile and link its Pascal sources and phrase file, and verify
# byte-for-byte identity against {T419309}Obj and {T419309}PHRASE on
# releases/LISA_REVERSI_1_0.dc42.
#
#   tests/downloaded_apps/run_lisareversi_test.sh
#   BUILD=2.0 tests/downloaded_apps/run_lisareversi_test.sh
#   APP_URL=<url> APP_DC42=<url> tests/downloaded_apps/run_lisareversi_test.sh
APP_NAME="Lisa Reversi 1.0"
APP_REPO="https://github.com/GyroPilot/Apple-LisaReversi"
APP_PREFIX="RVS"
APP_TOOL_ID="419309"
APP_SRC_URL="${APP_URL:-https://raw.githubusercontent.com/GyroPilot/Apple-LisaReversi/main/sources}"
APP_DC42_URL="${APP_DC42:-https://raw.githubusercontent.com/GyroPilot/Apple-LisaReversi/main/releases/LISA_REVERSI_1_0.dc42}"
APP_UNITS="GLOBALS"
APP_LINK_UNITS="GLOBALS"
APP_INCLUDES=""
APP_LIBS="IOSPASLIB,SYS1LIB,SYS2LIB"

. "$(dirname "$0")/common.sh"
run_gyropilot_app_test
