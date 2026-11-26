#!/bin/sh
# Compile every base feature test with the front end and print an md5 of each
# .I file.  Save the output as a baseline and diff later runs against it:
#   tests/run_icode_tests.sh | diff tests/icode_baseline-build3.0.txt -
# Uses the 3.0 build, pascal/pascal.py (baseline: tests/icode_baseline-build3.0.txt);
# BUILD=2.0 uses pascal/pascal.py --2.0 (baseline: tests/icode_baseline-build2.0.txt).
cd "$(dirname "$0")"
NEW=$(cd .. && pwd)
case "${BUILD:-3.0}" in
  3.0)    OPT= ;;
  2.0)    OPT=--2.0 ;;
  *)      echo "BUILD must be 3.0 or 2.0"; exit 1 ;;
esac
P="$NEW/pascal/pascal.py"
CODE="$NEW/pascal/code.py"
AUDIT="$NEW/pascal/audit_8char.py"
W=$(mktemp -d)
cp "$NEW"/tests/base_tests/*.TEXT "$NEW/pascal/PASERRS.ERR" "$W/"
cd "$W"
for src in T_ARITH T_CTRL T_TYPES T_PROCS T_INLINE T_OPT \
           T_U2 T_U1 T_UM T_CLSU T_CLSM T_ERRS; do
  "$AUDIT" -q "$src" || { echo "audit_8char failed on $src" >&2; rm -rf "$W"; exit 1; }
  rm -f "$src.I" err.log.text PROGCOMM.TEXT
  res=$(printf '%s\n\n\n' "$src" | "$P" $OPT 2>&1 | grep 'Compilation complete')
  if [ -f "$src.I" ]; then sum=$(md5sum < "$src.I" | cut -c1-32); else sum=no-I-file; fi
  # Build .OBJ for units so dependent tests (T_U1, T_UM, T_CLSM) can read their interfaces
  case "$src" in
    T_U2|T_U1|T_CLSU) printf '%s\n\n' "$src" | "$CODE" $OPT > /dev/null 2>&1 ;;
  esac
  rm -f "$src.I" err.log.text PROGCOMM.TEXT
  printf '%-18s %s  %s\n' "base_tests/$src" "$sum" "$res"
done
cd /
rm -rf "$W"
