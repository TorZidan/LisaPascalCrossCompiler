#!/bin/sh
# End-to-end check: compile the compiler test suites with pascal/pascal.py
# (front end, .TEXT -> .I) and pascal/code.py (code generator, .I -> .OBJ),
# verify Lisa-built reference .OBJ files, and print md5 checksums of all
# generated .OBJ files:
#   * tests/base_tests/   language, optimizer, multi-unit, and Clascal tests
#   * tests/gen/          HIDESYSCALL unit from the Gen disk (compared vs Lisa .obj)
#   * tests/iulib/        intrinsic-library USES lookup via INTRINSIC.LIB
#   * tests/workshop-QD/  QuickDraw samples BOXES and QDSAMPLE vs Lisa-linked .obj
#
# Keep the scratch directory with KEEP=1.
#
# WORKSHOP=1.0, 2.0 or 3.0 runs every part with that Workshop's boot volume
# (libs/workshopX); see run_workshop_tests.sh.  Without WORKSHOP, the default
# boot volume (3.0) is used (Workshop 2.0 for the QuickDraw 1.0/2.0 samples).
# LISA_BOOT, if set, overrides the boot volume.
cd "$(dirname "$0")"
NEW=$(cd .. && pwd)
T="$NEW/tests"
if [ -n "$WORKSHOP" ]; then
  [ -d "$NEW/libs/workshop$WORKSHOP" ] || { echo "no boot volume $NEW/libs/workshop$WORKSHOP"; exit 1; }
  LISA_BOOT=${LISA_BOOT:-$NEW/libs/workshop$WORKSHOP}; export LISA_BOOT
fi
case "${BUILD:-3.0}" in
  3.0)    OPT="" ;;
  2.0)    OPT="--2.0" ;;
  *)      echo "BUILD must be 3.0 or 2.0"; exit 1 ;;
esac
PASCAL="$NEW/pascal/pascal.py"; CODE="$NEW/pascal/code.py"; LPC="$NEW/pascal/lpc.py"; AUDIT="$NEW/pascal/audit_8char.py"
echo "BUILD=${BUILD:-3.0}  WORKSHOP=${WORKSHOP:-default}  boot volume: $(echo "${LISA_BOOT:-default}" | sed "s|^$NEW/||")"
W=$(mktemp -d)
pass=0; fail=0

# --- core language, optimizer, multi-unit, and Clascal feature tests ---
mkdir -p "$W/base_tests"
cp "$T"/base_tests/*.TEXT "$NEW/pascal/PASERRS.ERR" "$W/base_tests/"
chmod -R u+w "$W"
cd "$W/base_tests"
for src in T_ARITH T_CTRL T_TYPES T_PROCS T_INLINE T_OPT \
           T_U2 T_U1 T_UM T_CLSU T_CLSM; do
  "$AUDIT" -q "$src" > "$src.audit.log" 2>&1 || {
    printf '%-24s AUDIT_8CHAR FAILED (see base_tests/%s.audit.log)\n' "base_tests/$src" "$src"; fail=$((fail+1)); continue
  }
  printf '%s\n\n\n' "$src" | "$PASCAL" $OPT > "$src.pas.log" 2>&1
  if [ ! -f "$src.I" ]; then
    printf '%-24s FRONT END FAILED (see base_tests/%s.pas.log)\n' "base_tests/$src" "$src"; fail=$((fail+1)); continue
  fi
  printf '%s\n\n' "$src" | "$CODE" $OPT > "$src.code.log" 2>&1
  if [ ! -f "$src.OBJ" ]; then
    printf '%-24s CODE GENERATOR FAILED (see base_tests/%s.code.log)\n' "base_tests/$src" "$src"; fail=$((fail+1))
  else
    printf '%-24s built %5d bytes\n' "base_tests/$src" "$(wc -c < "$src.OBJ")"
  fi
done

# --- the compiler's own small unit, built on the Lisa with this toolchain ---
mkdir -p "$W/gen/ref"
cd "$W/gen"
cp "$NEW/pascal/PASERRS.ERR" .
cp "$T/gen/FLAGS.TEXT" "$T/gen/HIDESYSCALL.TEXT" .
cp "$T/gen/HIDESYSCALL.obj" ref/HIDESYSCALL.OBJ
chmod -R u+w .
for src in HIDESYSCALL; do
  "$AUDIT" -q "$src" > "$src.audit.log" 2>&1 || {
    printf '%-24s AUDIT_8CHAR FAILED (see gen/%s.audit.log)\n' "Gen/$src" "$src"; fail=$((fail+1)); continue
  }
  printf '%s\n\n\n' "$src" | "$PASCAL" $OPT > "$src.pas.log" 2>&1
  printf '%s\n\n' "$src" | "$CODE" $OPT > "$src.code.log" 2>&1
  if [ ! -f "$src.OBJ" ]; then
    printf '%-24s FAILED (see gen/%s.*.log)\n' "Gen/$src" "$src"; fail=$((fail+1))
  elif cmp -s "$src.OBJ" "ref/$src.OBJ"; then
    printf '%-24s identical to Lisa .OBJ (%d bytes)\n' "Gen/$src" "$(wc -c < "$src.OBJ")"; pass=$((pass+1))
  else
    printf '%-24s DIFFERS from Lisa .OBJ: %s\n' "Gen/$src" "$(cmp "$src.OBJ" "ref/$src.OBJ" 2>&1 | head -1)"; fail=$((fail+1))
  fi
done

# --- intrinsic-library search: USES without {$U file}, found via INTRINSIC.LIB ---
mkdir -p "$W/iulib"
cp "$NEW"/tests/iulib/*.TEXT "$NEW/pascal/PASERRS.ERR" "$W/iulib/"
cd "$W/iulib"
for src in USESTD USESQD USESFP; do
  "$AUDIT" -q "$src" > "$src.audit.log" 2>&1 || {
    printf '%-24s AUDIT_8CHAR FAILED (see iulib/%s.audit.log)\n' "iulib/$src" "$src"; fail=$((fail+1)); continue
  }
  printf '%s\n\n\n' "$src" | "$PASCAL" $OPT > "$src.pas.log" 2>&1
  printf '%s\n\n' "$src" | "$CODE" $OPT > "$src.code.log" 2>&1
  if [ -f "$src.OBJ" ]; then
    printf '%-24s built %5d bytes (USES via INTRINSIC.LIB)\n' "iulib/$src" "$(wc -c < "$src.OBJ")"
  else
    printf '%-24s FAILED (see iulib/%s.*.log)\n' "iulib/$src" "$src"; fail=$((fail+1))
  fi
done

# --- QuickDraw samples (tests/workshop-QD: the QD folder of the Workshop 1.0
# and 2.0 disks, identical in both).  The Lisa .OBJ files are LINKED
# programs, one built for Workshop 1.0 and one for 2.0 (only relinked: the
# program code is the same), so each procedure is searched for in the linked
# code with tools/cmplinked.py, skipping the bytes the linker fills in.
# Expected: all procedures identical except QDSAMPLE's INITICON, whose Lisa
# version was built by a code generator without literal-pool compaction:
# it keeps 5 duplicate strings, 250 bytes more.
mkdir -p "$W/qd"
cp -r "$NEW/tests/workshop-QD/QD" "$W/qd/"
cp "$NEW/pascal/PASERRS.ERR" "$W/qd/"
chmod -R u+w "$W/qd"
cd "$W/qd"
for src in QDSAMPLE BOXES; do
  LISA_BOOT=${LISA_BOOT:-$NEW/libs/workshop2.0} "$AUDIT" -q "QD/$src" > "$src.audit.log" 2>&1 || {
    printf '%-24s AUDIT_8CHAR FAILED (see qd/%s.audit.log)\n' "QD/$src" "$src"; fail=$((fail+1)); continue
  }
  printf '$G+\nQD/%s\n\n\n' "$src" | LISA_BOOT=${LISA_BOOT:-$NEW/libs/workshop2.0} "$LPC" $OPT > "$src.log" 2>&1
  if [ -f "QD/$src.OBJ" ]; then
    for v in 1.0 2.0; do
      ref="$NEW/tests/workshop-QD/ref-workshop$v/$src.obj"
      r=$(python3 "$NEW/tools/cmplinked.py" "QD/$src.OBJ" "$ref" | tail -1)
      printf '%-24s %s (procedures vs Workshop %s linked .OBJ)\n' "QD/$src" "$r" "$v"
      python3 "$NEW/tools/cmplinked.py" "QD/$src.OBJ" "$ref" | grep 'NOT FOUND' | sed 's/^/                           /'
    done
  else
    printf '%-24s FAILED (see qd/%s.log)\n' "QD/$src" "$src"; fail=$((fail+1))
  fi
done
cd "$W"

echo "$pass identical, $fail failed or different"
# checksums of everything built, for regression checks:
#   tests/run_obj_tests.sh | diff tests/obj_baseline-build3.0.txt -
find . -iname '*.obj' ! -path './gen/ref/*' | sort | xargs md5sum | sed 's|  \./|  |'
if [ -n "$KEEP" ]; then echo "scratch dir: $W"; else rm -rf "$W"; fi
