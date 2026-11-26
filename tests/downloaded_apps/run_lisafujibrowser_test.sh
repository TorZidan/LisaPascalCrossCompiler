#!/bin/sh
# Download LisaFuji Browser 1.3 (https://github.com/GyroPilot/Apple-LisaFujiBrowser),
# audit, compile and link its Pascal sources and phrase file, and verify
# byte-for-byte identity against {T419314}Obj and {T419314}PHRASE on
# releases/LISAFUJI_BROWSER_1_3.dc42.
#
#   tests/downloaded_apps/run_lisafujibrowser_test.sh
#   BUILD=2.0 tests/downloaded_apps/run_lisafujibrowser_test.sh
#   APP_URL=<url> APP_DC42=<url> tests/downloaded_apps/run_lisafujibrowser_test.sh
APP_NAME="LisaFuji Browser 1.3"
APP_REPO="https://github.com/GyroPilot/Apple-LisaFujiBrowser"
APP_PREFIX="LFB"
APP_TOOL_ID="419314"
APP_SRC_URL="${APP_URL:-https://raw.githubusercontent.com/GyroPilot/Apple-LisaFujiBrowser/main/sources}"
APP_DC42_URL="${APP_DC42:-https://raw.githubusercontent.com/GyroPilot/Apple-LisaFujiBrowser/main/releases/LISAFUJI_BROWSER_1_3.dc42}"
APP_UNITS="GLOBALS FNBUS"
APP_LINK_UNITS="GLOBALS FNBUS"
APP_INCLUDES=""
APP_LIBS="IOSPASLIB,SYS1LIB,SYS2LIB"

. "$(dirname "$0")/common.sh"
run_gyropilot_app_test
