#!/bin/sh
# Assemble the Lisa Office System's 68000 assembly sources with
# assembler/assembler.py, as the Workshop exec files on a Lisa disk image do,
# and compare every object file with the one the Lisa Assembler made (also on
# the image).  The work is done by tests/asm_build.py.
#
# The targets are those of the image's ALEX/ASM/*.TEXT exec files, 28 in all:
#   LIBPL LIBHW LIBFP LIBSM LIBIN LIBDB LIBQD LIBFM LIBWM LIBAM LIBPR_PRLIB
#   LIBPR_DAISY LIBPR_CANON LIBPR_CITOH LIBUT LIBTE LIBTK LIBQP APDM APLC APLD
#   APLL APLP APLT APLW APPW PREDRIVER SYSTEMOS
# They assemble 105 sources (with about 50 include files, many macros, the
# Pascal run time, QuickDraw, the floating point packages, the OS's assembly
# parts) into 105 object files.
#
# The steps are read from the exec files: $SUBMIT BUILD/ASSEMB(SRC,OBJ,SEG)
# and A{ssemble}SRC, then the post-processing they do: CHANGESEG (all
# modules into one segment, assembler/changeseg.py) and LIBQD's FIXMOVE
# (MQVE becomes MOVE: a procedure cannot be named MOVE).  Every file is taken
# from the image, unchanged, with "LisaFileSystemToolPerFile.py get-binary":
# the exec files, the sources, their .INCLUDE files (also nested ones) and
# the Lisa-built objects to compare with.
#
# The test passes when every object file is identical, byte for byte, to the
# one on the image.
#
#   tests/run_asm_test.sh                   all 28 targets (about 20 seconds)
#   tests/run_asm_test.sh LIBPL LIBQD       some of them
#   LOS_IMAGE=<image> tests/run_asm_test.sh
#
# Defaults: LOS_IMAGE=tests/LOSandWorkshop3.0_WithCompiledLisaSources_DO_NOT_COMMIT.image.
# Because that disk image contains copyrighted Lisa source files, it is not
# included in this repository (so this test is not part of run_all.sh).
# The disk image is read with file-system-tools/LisaFileSystemToolPerFile.py;
# it is copied into a temporary folder first and only that copy is read. The
# temporary folder is deleted after success and kept after a failure.
exec python3 "$(dirname "$0")/asm_build.py" "$@"
