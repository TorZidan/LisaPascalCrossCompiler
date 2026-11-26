#!/bin/sh
# Download LisaSolstice 1.0 (https://github.com/GyroPilot/Apple-LisaSolstice),
# audit, compile and link its Pascal sources (with its six {$I} picture include
# files) and phrase file, and verify byte-for-byte identity against {T419326}Obj
# and {T419326}PHRASE on releases/LISASOLSTICE_1_0.dc42.
#
#   tests/downloaded_apps/run_lisasolstice_test.sh
#   BUILD=2.0 tests/downloaded_apps/run_lisasolstice_test.sh
#   APP_URL=<url> APP_DC42=<url> tests/downloaded_apps/run_lisasolstice_test.sh
APP_NAME="LisaSolstice 1.0"
APP_REPO="https://github.com/GyroPilot/Apple-LisaSolstice"
APP_PREFIX="SOL"
APP_TOOL_ID="419326"
APP_SRC_URL="${APP_URL:-https://raw.githubusercontent.com/GyroPilot/Apple-LisaSolstice/main/sources}"
APP_DC42_URL="${APP_DC42:-https://raw.githubusercontent.com/GyroPilot/Apple-LisaSolstice/main/releases/LISASOLSTICE_1_0.dc42}"
APP_UNITS="GLOBALS UNIT FNBUS NET ASTRO VIEW PIC MAP PHO"
APP_LINK_UNITS="GLOBALS UNIT FNBUS NET ASTRO VIEW PIC MAP PHO"
APP_INCLUDES="PHOA PHOB PHOH PHOK PHOL PHOP"
APP_LIBS="IOSFPLIB,IOSPASLIB,SYS1LIB,SYS2LIB"

. "$(dirname "$0")/common.sh"
run_gyropilot_app_test
