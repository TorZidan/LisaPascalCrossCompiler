#!/bin/sh
# Build the Lisa Office System (libraries, applications, the operating
# system with its drivers and programs, and the installer) from the sources
# on a Lisa disk image, as the Workshop exec files on that image build them,
# and compare every output with the one built on the Lisa (also on the
# image).  The work is done by tests/los_build.py.
#
# By default it runs the image's whole build, ALEX/MAKE/ALL_NODISKS, which
# submits the other ALEX/MAKE exec files in its order: LIBOS LIBSM LIBIN
# LIBDB, the applications (calculator, clock, Preferences, LisaProject,
# LisaList, LisaTerminal, LisaWrite, LisaDraw, LisaCalc, LisaGraph, the
# Desktop Manager), InstallTool, the alert tool, the other libraries (SYS1LIB,
# SYS2LIB, PRLIB, QPLIB, the ToolKit, ...), PACKSEG, the OS (SYSTEM.OS, its
# boot and configurable drivers, the OS programs) and the installer (SYSLIB,
# INSTALL).  They assemble 105 sources with assembler/assembler.py, compile
# about 280 units and programs, link about 70 programs and libraries, and
# generate 17 alert/menu phrase files with alert/alert.py: 473 files on the
# image, all identical to the Lisa-built ones.
#
# The steps (assemble, compile, link, Alert, FileMgr copies and renames, with
# their answers and options; CHANGESEG and FIXMOVE after assembling) are read
# from the exec files, so the order of the steps, the inputs and the options
# are the image's.  Programs that do not run here are listed as skipped: the
# button tools, InstallTool, PACKSEG (the packed copies for the install disks,
# which are not on the image), $SUBMIT BUILD/INSTALL.  IUManager does not run
# here either: the intrinsic unit directory it writes is taken from the image.
#
# Every file is taken from the image, unchanged, with
# "LisaFileSystemToolPerFile.py get-binary" (a unit's .OBJ holds the 1 KB
# pages of its interface as they are on the disk, so the sources must keep
# their Lisa text layout): the exec files, the sources and their $I include
# files (also nested ones; a name that is not on the image is in a branch
# of $IFC that is not compiled), the files this run does not build (units
# named by $U that no target compiles, libraries that are linked into a
# target before they are built, INTRINSIC.LIB), and the Lisa-built files to
# compare with.  A $U
# name that is not a file (e.g. {$U UnitStd}) is an intrinsic unit, found
# through INTRINSIC.LIB.  The boot volume is the image: the compiler's boot
# folder is libs/workshop3.0 with the image's INTRINSIC.LIB and every library
# it lists put in their place.
#
# The test passes when every compiled and linked file is identical, byte for
# byte, to the one on the image.  With BUILD=2.0 there are known
# differences (tests/los_build.py, KNOWN_DIFFS), which are reported with their
# reason:
#   * 3 units (LIBFP/NEWFPLIB, MATHLIB, LIBTK/UTEXT):
#     the image was built with the Workshop 3.0 compiler, whose code generator
#     sets a boolean register variable in
#     place, not in a copy (pascal/codegen.py, LoadAOrd); the 3.0 build does
#     that too.  The libraries linked from them (IOSFPLIB, TK2LIB) are then
#     also linked from the Lisa-built units, and that link must be identical.
# LIBHW's SYSTEM.LLD is linked with +P (physical link: the linker's -P),
# SYSTEM.OS and the installer with -O (no OSData block) and +F (domain 0:
# segments from MMU 17).  A FileMgr Rename of a link output (SYSTEM.LLD.OBJ
# -> SYSTEM.LLD) is followed: the output is compared with the file of the
# new name.
#
# Not built: the targets the image's build does not build either (LisaImage,
# ALEX/MAKE/APIM, whose sources are not all on the image; CDTWIG, commented
# out of CDDRIVERS), and the install disks (ALEX/MAKE/DISKS, run by
# INSTALLER without a parameter: it copies the packed files to diskettes).
#
#   tests/run_lisa_sources_build_tests.sh                 the whole build (about 4 minutes)
#   tests/run_lisa_sources_build_tests.sh LIBPL APLW      some targets (ALEX/MAKE/<name>)
#   tests/run_lisa_sources_build_tests.sh ALEX/LINK/SYS1LIB   one exec file
#   BUILD=2.0 tests/run_lisa_sources_build_tests.sh       use the 2.0 build (default: 3.0)
#   LOS_IMAGE=<image> tests/run_lisa_sources_build_tests.sh
#
# Defaults: LOS_IMAGE=tests/LOSandWorkshop3.0_WithCompiledLisaSources_DO_NOT_COMMIT.image.
# Because that disk image contains copyrighted Lisa source files, it is not
# included in this repository (so this test is not part of run_all.sh).
# The disk image is read with file-system-tools/LisaFileSystemToolPerFile.py;
# it is copied into a temporary folder first and only that copy is read. The
# temporary folder is deleted after success and kept after a failure.
case "${BUILD:-3.0}" in
  3.0|2.0) ;;
  *) echo "BUILD must be 3.0 or 2.0"; exit 1 ;;
esac
exec python3 "$(dirname "$0")/los_build.py" "$@"
