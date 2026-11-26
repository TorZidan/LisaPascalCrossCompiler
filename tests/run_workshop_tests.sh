#!/bin/sh
# Run run_obj_tests.sh once per Workshop version (1.0, 2.0, 3.0): each run
# uses that version's boot volume (libs/workshopX).  Each output is compared
# with its baseline, tests/obj_baseline-workshopX-build3.0.txt (the 3.0 build,
# the default) or tests/obj_baseline-workshopX-build2.0.txt (BUILD=2.0); --save
# writes the baselines instead.
cd "$(dirname "$0")"
status=0
for v in 1.0 2.0 3.0; do
  out=$(WORKSHOP=$v ./run_obj_tests.sh)
  base=obj_baseline-workshop$v-build${BUILD:-3.0}.txt
  echo "=== Workshop $v: $(echo "$out" | grep 'failed or different')"
  echo "$out" | grep -E '^(Gen/|iulib/|QD/)' | sed 's/^/    /'
  if [ "$1" = "--save" ]; then
    echo "$out" > "$base"; echo "    baseline saved: tests/$base"
  elif [ -f "$base" ]; then
    if echo "$out" | diff "$base" - > /dev/null; then
      echo "    same as tests/$base"
    else
      echo "    CHANGED compared with tests/$base:"; echo "$out" | diff "$base" - | sed 's/^/      /'; status=1
    fi
  else
    echo "    (no baseline yet: run with --save)"
  fi
done
exit $status
