#!/bin/bash
# Run every test with the 3.0 build (the default) and compare each
# with its baseline: icode_baseline-build3.0.txt, obj_baseline-build3.0.txt,
# obj_baseline-workshopX-build3.0.txt.
# Also runs run_cmdline_tests.sh and run_link_tests.sh (pass/fail, no
# baseline).
# The 2.0 build is not run here; any single test script can still be run
# with it (BUILD=2.0 tests/<script>, baselines *-build2.0.txt).
# --save writes all baselines from the current results.
cd "$(dirname "$0")"
T=$(mktemp -d)
status=0
check() { # name, baseline, file
  if [ "$SAVE" = 1 ]; then cp "$3" "$2"; echo "  $1: baseline saved ($2)"
  elif diff "$2" "$3" > /dev/null; then echo "  $1: same as $2"
  else echo "  $1: CHANGED compared with $2:"; diff "$2" "$3" | sed 's/^/      /'; status=1; fi
}
[ "$1" = "--save" ] && SAVE=1
b=3.0
sfx=-build$b
echo "=== $b build"
BUILD=$b ./run_icode_tests.sh > $T/fe.txt; check "front end (.I)" icode_baseline$sfx.txt $T/fe.txt
BUILD=$b ./run_obj_tests.sh > $T/obj.txt;  check "both passes (.OBJ)" obj_baseline$sfx.txt $T/obj.txt
if BUILD=$b ./run_cmdline_tests.sh > $T/cl.txt; then
  echo "  command line: $(tail -1 $T/cl.txt)"
else
  echo "  command line: FAILED"; sed 's/^/    /' $T/cl.txt; status=1
fi
if BUILD=$b ./run_link_tests.sh > $T/lk.txt; then
  echo "  linker: $(tail -1 $T/lk.txt)"
else
  echo "  linker: FAILED"; sed 's/^/    /' $T/lk.txt; status=1
fi
for v in 1.0 2.0 3.0; do
  WORKSHOP=$v BUILD=$b ./run_obj_tests.sh > $T/w$v.txt
  check "Workshop $v" obj_baseline-workshop$v$sfx.txt $T/w$v.txt
done
rm -rf $T
exit $status
