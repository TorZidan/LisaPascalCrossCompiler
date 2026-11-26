#!/bin/sh
# Download LosTextEditor (https://github.com/TorZidan/LisaOfficeSystemTextEditor),
# a text editor tool for the Lisa Office System (about 5500 lines that use 18
# units: QuickDraw, the window manager, the Print Manager, ...), audit,
# compile and link it and its phrase file with the libraries of the project's
# LosTextEditorMake.text, and verify byte-for-byte identity against
# {T197000}Obj and {T197000}PHRASE on LosTextEditor.dc42 (built with the
# Workshop 3.0 on a Lisa).  The program is one source file, as a Workshop
# user would have it: 17 of the units come from INTRINSIC.LIB in the
# Workshop 3.0 boot volume, SysCall from the plain unit file SYSCALL.obj there.
#
#   tests/downloaded_apps/run_lostexteditor_test.sh
#   BUILD=2.0 tests/downloaded_apps/run_lostexteditor_test.sh
#   APP_URL=<url> APP_DC42=<url> tests/downloaded_apps/run_lostexteditor_test.sh
APP_NAME="LosTextEditor"
APP_REPO="https://github.com/TorZidan/LisaOfficeSystemTextEditor"
APP_PREFIX=""
APP_TOOL_ID="197000"
APP_SRC_URL="${APP_URL:-https://raw.githubusercontent.com/TorZidan/LisaOfficeSystemTextEditor/main}"
APP_SRC_NAME="%s.text"
APP_DC42_URL="${APP_DC42:-https://raw.githubusercontent.com/TorZidan/LisaOfficeSystemTextEditor/main/LosTextEditor.dc42}"
APP_MAIN="LosTextEditor"
APP_ALERTS="LosTextEditorAlerts"
APP_UNITS=""
APP_INCLUDES=""
APP_LIBS="IOSPASLIB,SYS1LIB,SYS2LIB,PRLIB"

. "$(dirname "$0")/common.sh"
run_downloaded_app_test
