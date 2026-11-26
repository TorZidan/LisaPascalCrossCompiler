#!/bin/sh
# Download LISACom 1.7 (https://github.com/GyroPilot/Apple-LISACom), audit,
# compile and link its Pascal sources and phrase file, and verify byte-for-byte
# identity against {T419306}Obj and {T419306}PHRASE on LISACOM_1_7.dc42.
#
#   tests/downloaded_apps/run_lisacom_test.sh
#   BUILD=2.0 tests/downloaded_apps/run_lisacom_test.sh
#   APP_URL=<url> APP_DC42=<url> tests/downloaded_apps/run_lisacom_test.sh
APP_NAME="LISACom 1.7"
APP_REPO="https://github.com/GyroPilot/Apple-LISACom"
APP_PREFIX="LMX"
APP_TOOL_ID="419306"
APP_SRC_URL="${APP_URL:-https://raw.githubusercontent.com/GyroPilot/Apple-LISACom/main/sources}"
APP_DC42_URL="${APP_DC42:-https://raw.githubusercontent.com/GyroPilot/Apple-LISACom/main/LISACOM_1_7.dc42}"
APP_UNITS="GLOBALS"
APP_LINK_UNITS="GLOBALS"
APP_INCLUDES=""
APP_LIBS="IOSPASLIB,SYS1LIB,SYS2LIB"

. "$(dirname "$0")/common.sh"
run_gyropilot_app_test
