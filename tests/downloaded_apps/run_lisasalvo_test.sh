#!/bin/sh
# Download LisaSalvo 1.2 (https://github.com/GyroPilot/Apple-LisaSalvo), audit,
# compile and link its Pascal sources and phrase file, and verify byte-for-byte
# identity against {T419322}Obj and {T419322}PHRASE on releases/LISASALVO_1_2.dc42.
# Uses the Workshop 3.0 build (BSH/MAIN assigns unsigned 128..255 constants
# into QuickDraw Pattern).
#
#   tests/downloaded_apps/run_lisasalvo_test.sh
#   APP_URL=<url> APP_DC42=<url> tests/downloaded_apps/run_lisasalvo_test.sh
APP_NAME="LisaSalvo 1.2"
APP_REPO="https://github.com/GyroPilot/Apple-LisaSalvo"
APP_PREFIX="BSH"
APP_TOOL_ID="419322"
APP_SRC_URL="${APP_URL:-https://raw.githubusercontent.com/GyroPilot/Apple-LisaSalvo/main/sources}"
APP_DC42_URL="${APP_DC42:-https://raw.githubusercontent.com/GyroPilot/Apple-LisaSalvo/main/releases/LISASALVO_1_2.dc42}"
APP_UNITS="FNBUS NET GLOBALS TWUNIT"
APP_LINK_UNITS="GLOBALS NET FNBUS TWUNIT"
APP_INCLUDES=""
APP_LIBS="IOSPASLIB,SYS1LIB,SYS2LIB"

. "$(dirname "$0")/common.sh"
run_gyropilot_app_test
