#!/bin/sh
# Download the two LisaSerialFtp clients (https://github.com/TorZidan/LisaSerialFtp,
# src/client), programs that are part Pascal, part 68000 assembly:
#
#   LosSerialFtpClient   the Lisa Office System client, tool 197001:
#                        LosSerialFtpClient.text (about 7700 lines, QuickDraw,
#                        the Window Manager, ...) and LosSerialFtpClientAlerts.text,
#                        linked with IOSPASLIB, SYS1LIB and SYS2LIB
#   LisaSerialFtpClient  the Lisa Workshop client: LisaSerialFtpClient.text and
#                        LisaSerialFtpClientInclude.text (about 5200 lines in
#                        3 segments), linked with IOSPASLIB
#
# Most of their code is shared and is in six files both include ({$I ...}):
# LisaSerialFtpDecl.text, LisaSerialFtpUtil.text, LisaSerialFtpSerial.text,
# LisaSerialFtpProto.text, LisaSerialFtpXfer.text and LisaSerialFtpCmds.text.
# Both use the same 4 routines in 68000 assembly (LisaSerialFtpClientAsm.text;
# LosSerialFtpClientAsm.text includes it).
#
# Audit, assemble, compile and link both (the inputs of the project's
# LosSerialFtpClientMake.text / LisaSerialFtpClientMake.text) and the phrase
# file, and verify byte-for-byte identity against {T197001}Obj,
# {T197001}PHRASE and LisaSerialFtpClient.obj on LisaSerialFtpClient.dc42.
# Those were built with this cross-compiler (the project's src/client/make.sh),
# not on a Lisa: the test checks that the compiler still builds the same
# programs, and fails when the sources on GitHub are newer than the image.
#
#   tests/downloaded_apps/run_serialftp_test.sh
#   BUILD=2.0 tests/downloaded_apps/run_serialftp_test.sh
#   APP_URL=<url> APP_DC42=<url> tests/downloaded_apps/run_serialftp_test.sh
#                 (e.g. APP_URL=file:///path/to/src/client)
APP_NAME="LisaSerialFtp"
APP_REPO="https://github.com/TorZidan/LisaSerialFtp"
APP_PREFIX=""
APP_TOOL_ID="197001"
APP_SRC_URL="${APP_URL:-https://raw.githubusercontent.com/TorZidan/LisaSerialFtp/main/src/client}"
APP_SRC_NAME="%s.text"
APP_DC42_URL="${APP_DC42:-https://raw.githubusercontent.com/TorZidan/LisaSerialFtp/main/LisaSerialFtpClient.dc42}"
APP_MAIN="LosSerialFtpClient"
APP_ALERTS="LosSerialFtpClientAlerts"
APP_ASM="LisaSerialFtpClientAsm LosSerialFtpClientAsm"
APP_UNITS=""
APP_LINK_UNITS="LosSerialFtpClientAsm"
APP_INCLUDES="LisaSerialFtpDecl LisaSerialFtpUtil LisaSerialFtpSerial LisaSerialFtpProto LisaSerialFtpXfer LisaSerialFtpCmds LisaSerialFtpClientInclude"
APP_EXTRA_PROGS="LisaSerialFtpClient:LisaSerialFtpClientAsm,IOSPASLIB:LisaSerialFtpClient.obj"
APP_LIBS="IOSPASLIB,SYS1LIB,SYS2LIB"

. "$(dirname "$0")/common.sh"
run_downloaded_app_test
