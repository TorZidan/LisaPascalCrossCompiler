#!/bin/sh
# Download Lisa TattleTale 1.0 (https://github.com/GyroPilot/Apple-LisaTattleTale),
# audit, compile and link its Pascal sources and phrase file, and verify
# byte-for-byte identity against {T419328}Obj and {T419328}PHRASE on
# releases/LISATATTLETALE_1_0.dc42.
# Uses the Workshop 3.0 build (TTL/GFX assigns unsigned 128..255 constants into
# QuickDraw Pattern).
#
#   tests/downloaded_apps/run_lisatattletale_test.sh
#   APP_URL=<url> APP_DC42=<url> tests/downloaded_apps/run_lisatattletale_test.sh
APP_NAME="Lisa TattleTale 1.0"
APP_REPO="https://github.com/GyroPilot/Apple-LisaTattleTale"
APP_PREFIX="TTL"
APP_TOOL_ID="419328"
APP_SRC_URL="${APP_URL:-https://raw.githubusercontent.com/GyroPilot/Apple-LisaTattleTale/main/sources}"
APP_DC42_URL="${APP_DC42:-https://raw.githubusercontent.com/GyroPilot/Apple-LisaTattleTale/main/releases/LISATATTLETALE_1_0.dc42}"
APP_UNITS="GLOBALS INFO GFX NET CAT"
APP_LINK_UNITS="GLOBALS INFO GFX NET CAT"
APP_INCLUDES=""
APP_LIBS="IOSPASLIB,SYS1LIB,SYS2LIB"

. "$(dirname "$0")/common.sh"
run_gyropilot_app_test
