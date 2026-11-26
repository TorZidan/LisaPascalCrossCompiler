#!/bin/bash
# Linker test: compile the QuickDraw samples BOXES and QDSAMPLE (tests/workshop-QD)
# with lpc.py, link them with linker/lisalinker.py as QD/M/*.TEXT link them on
# the Lisa, and compare with the programs linked by the Workshop 1.0 and 2.0
# Linker (tests/workshop-QD/ref-workshop*).
#
#   BOXES     must be identical, byte for byte.
#   QDSAMPLE  identical except for the 250 bytes of INITICON that the Lisa
#             code generator of the time did not compact (see run_obj_tests.sh)
#             and the PC-relative displacements that cross it.
#
# Packed code (linker/lisapack.py):
#   * every PackedCode block of the libraries in libs/workshop*, unpacked
#     with that boot folder's SYSTEM.UNPACK, must pack again to the same bytes;
#   * BOXES linked with -p (packed) must unpack to the code of the
#     Workshop-linked BOXES.
#
# lpc.py --link (compile and link in one command, Lisa file names):
#   * lpc.py --link='IOSPASLIB,IOSFPLIB,<QD/QDSTUFF' QD/BOXES (Workshop 2.0
#     boot folder) must leave QD/BOXES.OBJ identical to the Lisa-linked BOXES;
#   * with --pack it must unpack to the same code;
#   * a unit cannot be linked: a clear message, exit status not 0;
#   * a missing library: the message names the boot-folder library that has
#     the undefined names.
#
#   tests/run_link_tests.sh                  the 3.0 build
#   BUILD=2.0 tests/run_link_tests.sh        the 2.0 build
NEW="$(cd "$(dirname "$0")/.." && pwd)"
LPC="$NEW/pascal/lpc.py"
AUDIT="$NEW/pascal/audit_8char.py"
case "${BUILD:-3.0}" in
  3.0)    LPCOPT= ;;
  2.0)    LPCOPT=--2.0 ;;
  *)      echo "BUILD must be 3.0 or 2.0"; exit 1 ;;
esac
W=$(mktemp -d)
cp -r "$NEW/tests/workshop-QD/QD" "$W/"
cp "$NEW/pascal/PASERRS.ERR" "$W/"
chmod -R u+w "$W"
cd "$W"
Q=QD; QDSTUFF="$Q/QUICKDRAW.obj $Q/GRAFLIB.obj $Q/GRAFUTIL.obj $Q/GRAF3D.obj $Q/HWINTL.obj $Q/UNITSTD.obj $Q/UNITHZ.obj $Q/STORAGE.obj $Q/FONTMGR.obj $Q/QDSUPPORT.obj"
fail=0
for src in BOXES QDSAMPLE; do
  if ! LISA_BOOT="$NEW/libs/workshop2.0" "$AUDIT" -q "QD/$src"; then
    echo "QD/$src: audit_8char FAILED"; fail=$((fail+1)); continue
  fi
  printf '$G+\nQD/%s\n\n\n' "$src" | LISA_BOOT="$NEW/libs/workshop2.0" "$LPC" $LPCOPT > "$src.log" 2>&1
  if [ ! -f "QD/$src.OBJ" ]; then
    echo "QD/$src: compile FAILED"; fail=$((fail+1)); continue
  fi
  for v in 1.0 2.0; do
    B="$NEW/libs/workshop$v"
    libs="$(ls "$B"/* | grep -i '/iospaslib.obj$')"
    [ "$src" = BOXES ] && libs="$libs $(ls "$B"/* | grep -i '/iosfplib.obj$')"
    out="X$src-$v.obj"; map="X$src-$v.map"
    if ! python3 "$NEW/linker/lisalinker.py" -w $v -o "$out" -m "$map" "QD/$src.OBJ" $libs $QDSTUFF > "link-$src-$v.log" 2>&1; then
      echo "QD/$src: link FAILED (Workshop $v libraries)"; cat "link-$src-$v.log"; fail=$((fail+1)); continue
    fi
    ref="$NEW/tests/workshop-QD/ref-workshop$v/$src.obj"
    if [ "$src" = BOXES ]; then
      if cmp -s "$out" "$ref"; then r="identical"; else r="DIFFERENT"; fail=$((fail+1)); fi
    else
      r=$(python3 -I "$NEW/linker/cmpshift.py" "$out" "$map" "$ref" INITICON 250) || fail=$((fail+1))
    fi
    printf '%-12s linked with Workshop %s libraries: %s\n' "QD/$src" "$v" "$r"
  done
done
for v in 1.0 2.0 3.0; do
  B="$NEW/libs/workshop$v"
  libs=$(ls "$B"/*.obj)
  if python3 "$NEW/linker/lisapack.py" "$B/SYSTEM.UNPACK" check $libs > "pack-$v.log"; then
    n=$(awk '{s+=$2} END {print s}' "pack-$v.log")
    echo "packed code  Workshop $v libraries: all $n PackedCode blocks pack again to the same bytes"
  else
    echo "packed code  Workshop $v libraries: DIFFERENT"; cat "pack-$v.log"; fail=$((fail+1))
  fi
done
B="$NEW/libs/workshop2.0"
if python3 "$NEW/linker/lisalinker.py" -w 2.0 --table "$B/SYSTEM.UNPACK" -o XBOXES-packed.obj QD/BOXES.OBJ \
     "$B/IOSPASLIB.obj" "$B/IOSFPLIB.obj" $QDSTUFF > link-packed.log 2>&1 &&
   python3 "$NEW/linker/lisapack.py" "$B/SYSTEM.UNPACK" unpack XBOXES-packed.obj XBOXES-unpacked.obj &&
   python3 -c '
import sys
sys.path.insert(0, sys.argv[1])
from lisaobj import *
code = lambda f: [b.body for b in read_blocks(open(f, "rb").read()) if b.type == CODEBLOCK]
sys.exit(0 if code(sys.argv[2]) == code(sys.argv[3]) else 1)' "$NEW/linker" XBOXES-unpacked.obj "$NEW/tests/workshop-QD/ref-workshop2.0/BOXES.obj"; then
  echo "packed code  QD/BOXES linked with -p: $(wc -c < XBOXES-packed.obj) bytes, unpacks to the Workshop-linked code"
else
  echo "packed code  QD/BOXES linked with -p: DIFFERENT"; fail=$((fail+1))
fi
# lpc.py --link
B="$NEW/libs/workshop2.0"
ref="$NEW/tests/workshop-QD/ref-workshop2.0/BOXES.obj"
rm -f QD/BOXES.OBJ
LISA_BOOT="$B" "$LPC" $LPCOPT --link='IOSPASLIB,IOSFPLIB,<QD/QDSTUFF' QD/BOXES < /dev/null > lpc-link.log 2>&1
if cmp -s QD/BOXES.OBJ "$ref"; then r=identical; else r=DIFFERENT; fail=$((fail+1)); fi
echo "lpc.py --link: QD/BOXES.OBJ $r to the Lisa-linked BOXES"
rm -f QD/BOXES.OBJ
LISA_BOOT="$B" "$LPC" $LPCOPT --link='IOSPASLIB,IOSFPLIB,<QD/QDSTUFF' --pack QD/BOXES < /dev/null > lpc-pack.log 2>&1
if python3 "$NEW/linker/lisapack.py" "$B/SYSTEM.UNPACK" unpack QD/BOXES.OBJ BOXES-unpacked.obj 2> /dev/null &&
   python3 -c '
import sys
sys.path.insert(0, sys.argv[1])
from lisaobj import *
code = lambda f: [b.body for b in read_blocks(open(f, "rb").read()) if b.type == CODEBLOCK]
sys.exit(0 if code(sys.argv[2]) == code(sys.argv[3]) else 1)' "$NEW/linker" BOXES-unpacked.obj "$ref"; then
  echo "lpc.py --link --pack: QD/BOXES.OBJ $(wc -c < QD/BOXES.OBJ) bytes, unpacks to the Lisa-linked code"
else
  echo "lpc.py --link --pack: DIFFERENT"; fail=$((fail+1))
fi
cp "$NEW/tests/base_tests/T_CLSU.TEXT" .
"$AUDIT" -q T_CLSU || { echo "T_CLSU: audit_8char FAILED"; fail=$((fail+1)); }
if "$LPC" $LPCOPT --link T_CLSU < /dev/null > lpc-unit.log 2>&1; then
  echo "lpc.py --link on a unit: FAILED (it linked)"; fail=$((fail+1))
elif grep -q 'no main program' lpc-unit.log; then
  echo "lpc.py --link on a unit: refused ($(grep -o 'no main program.*' lpc-unit.log))"
else
  echo "lpc.py --link on a unit: FAILED, no message"; cat lpc-unit.log; fail=$((fail+1))
fi
LISA_BOOT="$B" "$LPC" $LPCOPT --link='IOSPASLIB,<QD/QDSTUFF' QD/BOXES < /dev/null > lpc-missing.log 2>&1
if grep -q 'defined in IOSFPLIB.obj (boot folder)' lpc-missing.log; then
  echo "lpc.py --link without IOSFPLIB: the message names IOSFPLIB.obj"
else
  echo "lpc.py --link without IOSFPLIB: FAILED"; cat lpc-missing.log; fail=$((fail+1))
fi
cat > DUPWARN.TEXT << 'EOF'
program DupWarn;
uses QuickDraw;
procedure SelectAll; begin end;
begin SelectAll end.
EOF
"$AUDIT" DUPWARN > dup-audit.log 2>&1 || { echo "DUPWARN: audit_8char exited non-zero on warning"; fail=$((fail+1)); }
if grep -q 'WARNING SELECTAL.*OTHRWORK' dup-audit.log; then
  echo "audit_8char on duplicate library entry: warns about SELECTAL in OTHRWORK"
else
  echo "audit_8char on duplicate library entry: FAILED"; cat dup-audit.log; fail=$((fail+1))
fi
"$LPC" $LPCOPT --link=IOSPASLIB,SYS1LIB DUPWARN < /dev/null > dup-link.log 2>&1
if [ -f DUPWARN.OBJ ] && grep -q 'Warning - Duplicate entry definitions: entry SELECTAL in OTHRWORK' dup-link.log; then
  echo "lpc.py --link on duplicate library entry: warns about SELECTAL in OTHRWORK"
else
  echo "lpc.py --link on duplicate library entry: FAILED"; cat dup-link.log; fail=$((fail+1))
fi
cd /; [ $fail -eq 0 ] && rm -rf "$W" || echo "kept $W"
echo "link tests: $fail failed"
exit $fail
