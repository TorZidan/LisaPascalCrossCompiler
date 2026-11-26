#!/bin/sh
# Check the code generator's 68000 disassembler (pascal/gen_disasm.py, used
# for $ASM+ listings) against expected.txt: 113 hand-encoded instructions
# (hex words|opcode|operand, in the notation of the original Gen/util/D.TEXT).
# The harness disasmtest.py has other uses:
#   tests/disasm/disasmtest.py 4E56 FFFC          one instruction
#   tests/disasm/disasmtest.py -all               all 65536 first words
#   tests/disasm/disasmtest.py -file F OFF LEN    a byte range of a file (e.g. an .OBJ code block)
cd "$(dirname "$0")"
fail=0; n=0
while IFS='|' read -r hex op opnd; do
  n=$((n+1))
  out=$(python3 disasmtest.py $hex | cut -c29-)
  gop=${out%% *}; gopnd=${out#* }; [ "$gop" = "$out" ] && gopnd=""
  gopnd=$(echo "$gopnd" | sed 's/^ *//')
  if [ "$gop" != "$op" ] || [ "$gopnd" != "$opnd" ]; then
    echo "MISMATCH $hex: got [$gop|$gopnd] want [$op|$opnd]"; fail=$((fail+1))
  fi
done < expected.txt
echo "$fail mismatches of $n"
[ $fail -eq 0 ]
