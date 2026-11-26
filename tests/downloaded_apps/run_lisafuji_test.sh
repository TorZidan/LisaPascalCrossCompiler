#!/bin/sh
# Download LisaFuji 1.2 (https://github.com/GyroPilot/Apple-LisaFuji), audit,
# compile and link its Pascal sources and phrase file, and verify byte-for-byte
# identity against {T419312}Obj and {T419312}PHRASE on releases/LISAFUJI_1_2.dc42.
# Uses the Workshop 3.0 build (LFJ/MAP assigns unsigned 128..255 constants into
# QuickDraw Pattern).
#
#   tests/downloaded_apps/run_lisafuji_test.sh
#   APP_URL=<url> APP_DC42=<url> tests/downloaded_apps/run_lisafuji_test.sh
APP_NAME="LisaFuji 1.2"
APP_REPO="https://github.com/GyroPilot/Apple-LisaFuji"
APP_PREFIX="LFJ"
APP_TOOL_ID="419312"
APP_SRC_URL="${APP_URL:-https://raw.githubusercontent.com/GyroPilot/Apple-LisaFuji/main/sources}"
APP_DC42_URL="${APP_DC42:-https://raw.githubusercontent.com/GyroPilot/Apple-LisaFuji/main/releases/LISAFUJI_1_2.dc42}"
APP_UNITS="TWUNIT GLOBALS FNBUS MAP MORE ISS"
APP_LINK_UNITS="GLOBALS FNBUS TWUNIT MAP MORE ISS"
APP_INCLUDES=""
APP_LIBS="IOSFPLIB,IOSPASLIB,SYS1LIB,SYS2LIB"

. "$(dirname "$0")/common.sh"
run_gyropilot_app_test
