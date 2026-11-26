#!/bin/sh
# Check the command-line mode of pascal/pascal.py, pascal/code.py and pascal/lpc.py:
# arguments answer the prompts in order, and missing answers take the default.
# Each check compares with the files made by answering the same prompts on
# stdin (the interactive way).
#   BUILD=2.0 tests/run_cmdline_tests.sh        the 2.0 build (default: 3.0)
cd "$(dirname "$0")"
NEW=$(cd .. && pwd)
case "${BUILD:-3.0}" in
  3.0)    OPT="" ;;
  2.0)    OPT="--2.0" ;;
  *)      echo "BUILD must be 3.0 or 2.0"; exit 1 ;;
esac
PASCAL="$NEW/pascal/pascal.py"; CODE="$NEW/pascal/code.py"; LPC="$NEW/pascal/lpc.py"; AUDIT="$NEW/pascal/audit_8char.py"
W=$(mktemp -d)
cp base_tests/T_ARITH.TEXT base_tests/T_ERRS.TEXT "$NEW/pascal/PASERRS.ERR" "$W/"
cd "$W"
pass=0; fail=0
check() { # description, condition result (0 = ok)
  if [ "$2" -eq 0 ]; then echo "  ok    $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi
}
same() { cmp -s "$1" "$2"; echo $?; }

# 8-character identifier audit before compiling Pascal sources
"$AUDIT" -q T_ARITH && "$AUDIT" -q T_ERRS
check "audit_8char.py passes on T_ARITH.TEXT and T_ERRS.TEXT" $?

# front end + code generator on stdin (reference interactive run)
printf '$G-\nT_ARITH\n\n\n' | "$PASCAL" $OPT > /dev/null 2>&1; cp T_ARITH.I stdin.I
printf 'T_ARITH\n\n' | "$CODE" $OPT > /dev/null 2>&1; mv T_ARITH.OBJ stdin.OBJ
rm -f T_ARITH.I PROGCOMM.TEXT

# front end: arguments vs stdin answers
"$PASCAL" $OPT '$G-' T_ARITH < /dev/null > /dev/null 2>&1
check "pascal.py '\$G-' T_ARITH writes the same T_ARITH.I as the answers on stdin" $(same T_ARITH.I stdin.I)

# code generator: arguments vs stdin answers
"$CODE" $OPT T_ARITH < /dev/null > /dev/null 2>&1
check "code.py T_ARITH writes the same T_ARITH.OBJ as the answers on stdin" $(same T_ARITH.OBJ stdin.OBJ)
rm -f T_ARITH.OBJ T_ARITH.I PROGCOMM.TEXT

# lpc.py: both passes from one argument
"$LPC" $OPT T_ARITH < /dev/null > /dev/null 2>&1; st=$?
check "lpc.py T_ARITH writes the same T_ARITH.OBJ as the two-pass run" $(same T_ARITH.OBJ stdin.OBJ)
check "... and exits with status 0" $st
[ ! -f T_ARITH.I ] && [ ! -f PROGCOMM.TEXT ]; check "lpc.py T_ARITH leaves no T_ARITH.I or PROGCOMM.TEXT behind" $?
rm -f T_ARITH.OBJ

# options and a listing file
"$LPC" $OPT '$ASM+' T_ARITH T_ARITH.LST < /dev/null > /dev/null 2>&1
grep -q 'LINK    A6' T_ARITH.LST.TEXT 2>/dev/null; check "lpc.py '\$ASM+' T_ARITH T_ARITH.LST writes a listing with the disassembly" $?
check "... and the same T_ARITH.OBJ" $(same T_ARITH.OBJ stdin.OBJ)

# output name
rm -f T_ARITH.OBJ
"$LPC" $OPT T_ARITH '' OTHER < /dev/null > /dev/null 2>&1
[ -f OTHER.OBJ ] && [ ! -f T_ARITH.OBJ ]; check "lpc.py T_ARITH '' OTHER writes OTHER.OBJ" $?

# a program with errors finishes instead of waiting for input
timeout 30 "$LPC" $OPT T_ERRS < /dev/null > errors.log 2>&1; st=$?
[ $st -ne 124 ] && grep -q 'Compilation complete - 6 errors found' errors.log; check "lpc.py T_ERRS reports 6 errors and finishes" $?
[ ! -f T_ERRS.OBJ ]; check "... and writes no T_ERRS.OBJ" $?
[ $st -eq 1 ]; check "... and exits with status 1" $?
rm -f T_ERRS.I PROGCOMM.TEXT
"$PASCAL" $OPT T_ERRS < /dev/null > /dev/null 2>&1; st=$?
[ $st -eq 1 ]; check "pascal.py T_ERRS exits with status 1" $?

echo "$pass passed, $fail failed"
cd /; rm -rf "$W"
[ $fail -eq 0 ]
