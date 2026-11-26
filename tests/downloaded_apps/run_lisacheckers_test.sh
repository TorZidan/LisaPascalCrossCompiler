#!/bin/sh
# Download LisaCheckers 1.2 (https://github.com/GyroPilot/Apple-LisaCheckers),
# audit, compile and link its Pascal sources and phrase file, and verify
# byte-for-byte identity against {T419317}Obj and {T419317}PHRASE on
# releases/LISACHECKERS_1_2.dc42.
# Uses the Workshop 3.0 build (CKR/MAIN assigns unsigned 128..255 constants
# into QuickDraw Pattern).
#
#   tests/downloaded_apps/run_lisacheckers_test.sh
#   APP_URL=<url> APP_DC42=<url> tests/downloaded_apps/run_lisacheckers_test.sh
APP_NAME="LisaCheckers 1.2"
APP_REPO="https://github.com/GyroPilot/Apple-LisaCheckers"
APP_PREFIX="CKR"
APP_TOOL_ID="419317"
APP_SRC_URL="${APP_URL:-https://raw.githubusercontent.com/GyroPilot/Apple-LisaCheckers/main/sources}"
APP_DC42_URL="${APP_DC42:-https://raw.githubusercontent.com/GyroPilot/Apple-LisaCheckers/main/releases/LISACHECKERS_1_2.dc42}"
APP_UNITS="RULES FNBUS NET GLOBALS TWUNIT"
APP_LINK_UNITS="GLOBALS RULES NET FNBUS TWUNIT"
APP_INCLUDES=""
APP_LIBS="IOSPASLIB,SYS1LIB,SYS2LIB"

. "$(dirname "$0")/common.sh"
run_gyropilot_app_test
