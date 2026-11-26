#!/bin/sh
# Run every downloaded-application test in tests/downloaded_apps/ (requires
# network access via curl or wget).
#
#   tests/downloaded_apps/run_all.sh
cd "$(dirname "$0")"
pass=0
fail=0
T=$(mktemp -d)

for script in ./run_*_test.sh; do
  name=$(basename "$script" .sh)
  if "$script" > "$T/$name.log" 2>&1; then
    summary=$(grep -E '^(linked:|PASSED)' "$T/$name.log" | tr '\n' ' ' | sed 's/  */ /g; s/ $//')
    printf '  ok    %-30s %s\n' "$name" "$summary"
    pass=$((pass + 1))
  else
    printf '  FAIL  %s\n' "$name"
    sed 's/^/        /' "$T/$name.log"
    fail=$((fail + 1))
  fi
done

rm -rf "$T"
echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ]
