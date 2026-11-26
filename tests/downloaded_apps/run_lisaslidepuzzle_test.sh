#!/bin/sh
# Download Lisa Slide Puzzle 1.0 (https://github.com/GyroPilot/Apple-LisaSlidePuzzle),
# audit, compile and link its Pascal sources and phrase file, and verify
# byte-for-byte identity against {T419308}Obj and {T419308}PHRASE on
# releases/LISA_PUZZLE_1_0.dc42.
#
#   tests/downloaded_apps/run_lisaslidepuzzle_test.sh
#   BUILD=2.0 tests/downloaded_apps/run_lisaslidepuzzle_test.sh
#   APP_URL=<url> APP_DC42=<url> tests/downloaded_apps/run_lisaslidepuzzle_test.sh
APP_NAME="Lisa Slide Puzzle 1.0"
APP_REPO="https://github.com/GyroPilot/Apple-LisaSlidePuzzle"
APP_PREFIX="PZL"
APP_TOOL_ID="419308"
APP_SRC_URL="${APP_URL:-https://raw.githubusercontent.com/GyroPilot/Apple-LisaSlidePuzzle/main/sources}"
APP_DC42_URL="${APP_DC42:-https://raw.githubusercontent.com/GyroPilot/Apple-LisaSlidePuzzle/main/releases/LISA_PUZZLE_1_0.dc42}"
APP_UNITS="GLOBALS"
APP_LINK_UNITS="GLOBALS"
APP_INCLUDES=""
APP_LIBS="IOSPASLIB,SYS1LIB,SYS2LIB"

. "$(dirname "$0")/common.sh"
run_gyropilot_app_test
