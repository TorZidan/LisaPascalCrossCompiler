#!/bin/sh
# Download ESPFuji 0.2 REV D (https://github.com/GyroPilot/ESPFuji,
# espfuji/lisa-tool), audit, compile and link its Pascal sources and phrase
# file, and verify byte-for-byte identity against {T419324}Obj and
# {T419324}PHRASE on ESPFUJI_0_2_REVD.dc42.
#
#   tests/downloaded_apps/run_espfuji_test.sh
#   BUILD=2.0 tests/downloaded_apps/run_espfuji_test.sh
#   APP_URL=<url> APP_DC42=<url> tests/downloaded_apps/run_espfuji_test.sh
APP_NAME="ESPFuji 0.2"
APP_REPO="https://github.com/GyroPilot/ESPFuji"
APP_PREFIX="EFJ"
APP_TOOL_ID="419324"
APP_SRC_URL="${APP_URL:-https://raw.githubusercontent.com/GyroPilot/ESPFuji/main/espfuji/lisa-tool}"
APP_DC42_URL="${APP_DC42:-https://github.com/GyroPilot/ESPFuji/releases/download/v1.1.5/ESPFUJI_0_2_REVD.dc42}"
APP_UNITS="GLOBALS MBOX"
APP_LINK_UNITS="GLOBALS MBOX"
APP_INCLUDES=""
APP_LIBS="IOSPASLIB,SYS1LIB,SYS2LIB"

. "$(dirname "$0")/common.sh"
run_gyropilot_app_test
