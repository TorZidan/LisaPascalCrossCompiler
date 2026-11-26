#!/bin/sh
# Shared helper for Lisa Office System application download tests.
#
# Sourced by tests/downloaded_apps/run_*_test.sh after setting:
#   APP_NAME        human-readable application name and version
#   APP_REPO        GitHub repository URL
#   APP_PREFIX      Workshop prefix folder on disk (e.g. LMX, MINESWEEPER, MILES); empty:
#                   no folder, the sources keep their names (APP_SRC_NAME) in the work
#                   folder, as on one Lisa volume, and include each other by those names
#   APP_TOOL_ID     Lisa Office System tool number (e.g. 419306 for {T419306}Obj)
#   APP_SRC_URL     base URL of the sources
#   APP_SRC_NAME    optional: the name of a source at APP_SRC_URL, %s for its stem
#                   (default: <APP_PREFIX>-%s.TEXT)
#   APP_DC42_URL    URL for the reference DiskCopy 4.2 (.dc42) floppy image
#   APP_MAIN        optional: the stem of the main program (default: MAIN); the linked
#                   program is <APP_PREFIX>/<APP_PREFIX>.OBJ, or <APP_MAIN>.OBJ without a prefix
#   APP_ALERTS      optional: the stem of the alerts/menus phrase source (default: ALERTS)
#   APP_ASM         optional space-separated 68000 assembly source stems, assembled
#                   first into <stem>.OBJ (name them in APP_LINK_UNITS / APP_EXTRA_PROGS)
#   APP_UNITS       space-separated unit stems in compile order (e.g. "GLOBALS UNIT")
#   APP_LINK_UNITS  space-separated unit stems in link order (defaults to APP_UNITS)
#   APP_INCLUDES    optional space-separated {$I} include stems (e.g. "PHOA PHOB ...")
#   APP_EXTRA_PROGS optional space-separated "<STEM>:<LIBS>[:<REFERENCE>]" standalone
#                   programs; with <REFERENCE>, the linked program must be identical to
#                   the file of that name on the disk image
#   APP_LIBS        comma-separated Workshop 3.0 libraries (e.g. "IOSPASLIB,SYS1LIB,SYS2LIB")

run_downloaded_app_test() {
  SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
  NEW=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)

  case "${BUILD:-3.0}" in
    3.0)    LPCOPT="" ;;
    2.0)    LPCOPT="--2.0" ;;
    *)      echo "BUILD must be 3.0 or 2.0"; exit 1 ;;
  esac

  LPC="$NEW/pascal/lpc.py"
  AUDIT="$NEW/pascal/audit_8char.py"
  ALERT="$NEW/alert/alert.py"
  FSTOOL="$NEW/file-system-tools/LisaFileSystemToolPerFile.py"
  BOOT="${LISA_BOOT:-$NEW/libs/workshop3.0}"

  W=$(mktemp -d)
  fail() {
    echo "FAILED ($APP_NAME): $1"
    echo "files kept in $W"
    exit 1
  }

  get() { # url, dest
    echo "downloading $1"
    if command -v curl > /dev/null 2>&1; then
      curl -fsSL --connect-timeout 15 --max-time 60 "$1" -o "$2" || fail "download $1"
    elif command -v wget > /dev/null 2>&1; then
      wget -q --timeout=30 "$1" -O "$2" || fail "download $1"
    else
      fail "neither curl nor wget is installed"
    fi
  }

  SRC_NAME="${APP_SRC_NAME:-$APP_PREFIX-%s.TEXT}"
  MAIN="${APP_MAIN:-MAIN}"
  ALERTS="${APP_ALERTS:-ALERTS}"
  # P: the folder of the sources and outputs (Lisa file names <P><stem>)
  if [ -n "$APP_PREFIX" ]; then P="$APP_PREFIX/"; OUT="$APP_PREFIX/$APP_PREFIX"; else P=""; OUT="$MAIN"; fi
  src_name() { printf "$SRC_NAME" "$1"; }                 # stem -> name at APP_SRC_URL
  local_name() {                                          # stem -> file in the work folder
    if [ -n "$APP_PREFIX" ]; then echo "$P$1.TEXT"; else src_name "$1"; fi
  }

  mkdir -p "$W/$APP_PREFIX"
  for f in $APP_ASM $APP_UNITS "$MAIN" "$ALERTS" $APP_INCLUDES; do
    get "$APP_SRC_URL/$(src_name "$f")" "$W/$(local_name "$f")"
  done
  for ep in $APP_EXTRA_PROGS; do
    ep_stem=${ep%%:*}
    get "$APP_SRC_URL/$(src_name "$ep_stem")" "$W/$(local_name "$ep_stem")"
  done
  get "$APP_DC42_URL" "$W/reference.dc42"

  grep -q -i '^program ' "$W/$(local_name "$MAIN")" ||
    fail "downloaded $(src_name "$MAIN") is not a Pascal program source"

  cd "$W" || fail "cd $W"

  # 0. Assemble the 68000 sources (prompts: input file, listing file (none), output file).
  for a in $APP_ASM; do
    python3 "$NEW/assembler/assembler.py" "$P$a" '' "$P$a" < /dev/null > "asm-$a.log" 2>&1 ||
      { tail -20 "asm-$a.log"; fail "the assembler failed on $P$a (see $W/asm-$a.log)"; }
    [ -s "$P$a.OBJ" ] || fail "the assembler wrote no $P$a.OBJ (see $W/asm-$a.log)"
    echo "assembled: $P$a.OBJ, $(wc -c < "$P$a.OBJ") bytes"
  done

  # 1. Audit and compile each unit in Workshop COMP order.
  for u in $APP_UNITS; do
    LISA_BOOT="$BOOT" python3 "$AUDIT" "$P$u" < /dev/null > "audit-$u.log" 2>&1 || {
      cat "audit-$u.log"
      fail "audit_8char reported identifier collisions in $P$u (see $W/audit-$u.log)"
    }
    LISA_BOOT="$BOOT" python3 "$LPC" $LPCOPT "$P$u" '' "$P$u" < /dev/null > "compile-$u.log" 2>&1
    st=$?
    [ "$st" -eq 0 ] && [ -s "$P$u.OBJ" ] ||
      { tail -20 "compile-$u.log"; fail "compiling $P$u failed (see $W/compile-$u.log)"; }
  done

  # 2. Audit MAIN, then compile and link in one command following Workshop LINK order.
  LISA_BOOT="$BOOT" python3 "$AUDIT" "$P$MAIN" < /dev/null > audit-MAIN.log 2>&1 || {
    cat audit-MAIN.log
    fail "audit_8char reported identifier collisions in $P$MAIN (see $W/audit-MAIN.log)"
  }

  LINK_UNITS="${APP_LINK_UNITS:-$APP_UNITS}"
  LINK_LIST=""
  for u in $LINK_UNITS; do
    if [ -z "$LINK_LIST" ]; then
      LINK_LIST="$P$u"
    else
      LINK_LIST="$LINK_LIST,$P$u"
    fi
  done
  if [ -n "$LINK_LIST" ]; then
    LINK_LIST="$LINK_LIST,$APP_LIBS"
  else
    LINK_LIST="$APP_LIBS"
  fi

  LISA_BOOT="$BOOT" python3 "$LPC" $LPCOPT --link="$LINK_LIST" \
    "$P$MAIN" '' "$OUT" < /dev/null > compile-MAIN.log 2>&1
  st=$?
  # lpc.py prints "Linking" only after both passes succeeded: without it the compile failed
  grep -q '^Linking' compile-MAIN.log ||
    { tail -20 compile-MAIN.log; fail "compiling $P$MAIN failed (see $W/compile-MAIN.log)"; }
  [ "$st" -eq 0 ] || { tail -10 compile-MAIN.log; fail "linker failed on $P$MAIN (see $W/compile-MAIN.log)"; }
  [ -s "$OUT.OBJ" ] || fail "no linked $OUT.OBJ (see $W/compile-MAIN.log)"

  echo "$(grep 'Compilation complete' compile-MAIN.log | sed 's/^ *//')"
  echo "$(grep 'Total code size' compile-MAIN.log | sed 's/^ *//')"

  # 3. Compile alerts/menus phrase file with alert/alert.py.
  python3 "$ALERT" "$(local_name "$ALERTS")" "{T$APP_TOOL_ID}" < /dev/null > alert.log 2>&1 ||
    { cat alert.log; fail "alert.py failed on $(local_name "$ALERTS") (see $W/alert.log)"; }
  [ -s "{T$APP_TOOL_ID}PHRASE" ] || fail "alert.py wrote no {T$APP_TOOL_ID}PHRASE (see $W/alert.log)"

  # 4. Extract Lisa-built {T<id>}Obj and {T<id>}PHRASE from the .dc42 disk image and compare byte-for-byte.
  python3 "$FSTOOL" get-binary reference.dc42 "{T$APP_TOOL_ID}Obj" LISA_LINKED.OBJ > fs-obj.log 2>&1 ||
    { cat fs-obj.log; fail "extracting {T$APP_TOOL_ID}Obj from reference.dc42"; }
  cmp -s "$OUT.OBJ" LISA_LINKED.OBJ ||
    fail "linked $OUT.OBJ differs from {T$APP_TOOL_ID}Obj on reference.dc42"
  echo "linked: $(wc -c < "$OUT.OBJ") bytes, identical to {T$APP_TOOL_ID}Obj on the disk image"

  python3 "$FSTOOL" get-binary reference.dc42 "{T$APP_TOOL_ID}PHRASE" LISA_PHRASE.BIN > fs-phrase.log 2>&1 ||
    { cat fs-phrase.log; fail "extracting {T$APP_TOOL_ID}PHRASE from reference.dc42"; }
  cmp -s "{T$APP_TOOL_ID}PHRASE" LISA_PHRASE.BIN ||
    fail "compiled {T$APP_TOOL_ID}PHRASE differs from {T$APP_TOOL_ID}PHRASE on reference.dc42"
  echo "phrase: $(wc -c < "{T$APP_TOOL_ID}PHRASE") bytes, identical to {T$APP_TOOL_ID}PHRASE on the disk image"

  # 5. Audit, compile and link any extra Pascal programs in the repository, and compare
  #    each that names a reference file with that file on the disk image.
  for ep in $APP_EXTRA_PROGS; do
    ep_stem=${ep%%:*}
    ep_rest=${ep#*:}
    ep_libs=${ep_rest%%:*}
    ep_ref=""
    case "$ep_rest" in *:*) ep_ref=${ep_rest#*:} ;; esac
    LISA_BOOT="$BOOT" python3 "$AUDIT" "$P$ep_stem" < /dev/null > "audit-$ep_stem.log" 2>&1 || {
      cat "audit-$ep_stem.log"
      fail "audit_8char reported identifier collisions in $P$ep_stem (see $W/audit-$ep_stem.log)"
    }
    LISA_BOOT="$BOOT" python3 "$LPC" $LPCOPT --link="$ep_libs" \
      "$P$ep_stem" '' "$P$ep_stem" < /dev/null > "compile-$ep_stem.log" 2>&1
    st=$?
    grep -q '^Linking' "compile-$ep_stem.log" ||
      { tail -20 "compile-$ep_stem.log"; fail "compiling $P$ep_stem failed (see $W/compile-$ep_stem.log)"; }
    [ "$st" -eq 0 ] && [ -s "$P$ep_stem.OBJ" ] || fail "linker failed on $P$ep_stem (see $W/compile-$ep_stem.log)"
    if [ -n "$ep_ref" ]; then
      python3 "$FSTOOL" get-binary reference.dc42 "$ep_ref" "LISA_$ep_stem.OBJ" > "fs-$ep_stem.log" 2>&1 ||
        { cat "fs-$ep_stem.log"; fail "extracting $ep_ref from reference.dc42"; }
      cmp -s "$P$ep_stem.OBJ" "LISA_$ep_stem.OBJ" ||
        fail "linked $P$ep_stem.OBJ differs from $ep_ref on reference.dc42"
      echo "linked: $P$ep_stem.OBJ, $(wc -c < "$P$ep_stem.OBJ") bytes, identical to $ep_ref on the disk image"
    else
      echo "helper: $P$ep_stem.OBJ, $(wc -c < "$P$ep_stem.OBJ") bytes"
    fi
  done

  echo "PASSED ($APP_NAME)"
  cd /
  rm -rf "$W"
}

run_gyropilot_app_test() {
  run_downloaded_app_test
}
