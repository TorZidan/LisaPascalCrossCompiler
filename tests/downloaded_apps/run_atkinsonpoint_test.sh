#!/bin/sh
# Download AtkinsonPoint 1.1 (https://github.com/GyroPilot/AtkinsonPoint),
# audit, compile and link its Pascal sources and phrase file, and verify
# byte-for-byte identity against {T419307}Obj and {T419307}PHRASE on
# AtkinsonPoint_v1_1.dc42.
#
#   tests/downloaded_apps/run_atkinsonpoint_test.sh
#   BUILD=2.0 tests/downloaded_apps/run_atkinsonpoint_test.sh
#   APP_URL=<url> APP_DC42=<url> tests/downloaded_apps/run_atkinsonpoint_test.sh
APP_NAME="AtkinsonPoint 1.1"
APP_REPO="https://github.com/GyroPilot/AtkinsonPoint"
APP_PREFIX="SLD"
APP_TOOL_ID="419307"
APP_SRC_URL="${APP_URL:-https://raw.githubusercontent.com/GyroPilot/AtkinsonPoint/main}"
APP_DC42_URL="${APP_DC42:-https://raw.githubusercontent.com/GyroPilot/AtkinsonPoint/main/AtkinsonPoint_v1_1.dc42}"
APP_UNITS="GLOBALS"
APP_LINK_UNITS="GLOBALS"
APP_INCLUDES=""
APP_LIBS="IOSPASLIB,SYS1LIB,SYS2LIB"

. "$(dirname "$0")/common.sh"
run_gyropilot_app_test
