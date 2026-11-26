Boot volume for Workshop 2.0.  Use it with:
    LISA_BOOT=/path/to/LisaPascalCrossCompiler/libs/workshop2.0 pascal/lpc.py --2.0 MYPROG
(the default boot volume is libs/workshop3.0).  See LIBRARIES.md and the
per-library *.md files in this folder for full unit and routine signatures.

From a Workshop 2.0 disk dump, copied unchanged (only the extension is
written in lowercase, .obj):
  INTRINSIC.LIB   (identical to the dump's INTRINSIC.LIB)
  objiolib.obj  IOSPASLIB.obj  SYS1LIB.obj  IOSFPLIB.obj  sys2lib.obj
  lcorbglib.obj  SULIB.obj
Not found in the dump: *IUPASLIB.OBJ, TKLIB.OBJ, TFOLDERLIB.OBJ.

Unlike Workshop 3.0, only three 2.0 library files contain embedded interface
text:
  SULIB.obj (StdUnit), IOSPASLIB.obj (PasLib, PasHeap, BlockIO, BlkIOIntr),
  and IOSFPLIB.obj (FPLib).
SYS1LIB.obj, sys2lib.obj, objiolib.obj and lcorbglib.obj contain code only
(no InterfLoc block, 30-byte UnitBlock headers), so QuickDraw, HWInt, UnitStd,
... cannot be found through INTRINSIC.LIB.  On a Workshop 2.0 system those
interfaces came from separate unit files named with {$U ...}, e.g. the dump's
QD folder: {$U QD/QuickDraw} QuickDraw.

The 2.0 StdUnit interface uses {$IFC ForOS}: a program using it must define
it, e.g. {$SETC ForOS := TRUE} (the compiler's sources do so in FLAGS.TEXT),
otherwise error 261.

Also SYSCALL.obj and PASLIBCALL.obj, the plain unit files of Workshop 2.0:
they are not in INTRINSIC.LIB, and a program names them with {$U SysCall.obj},
which is looked up here when it is not in the current directory.

SYSTEM.UNPACK: the pack table for packed code (a PackTable block, 520 bytes),
from the boot volume of
lisaem-profile-5MB-FreshInstallOf_LOS2.0_andWorkshop2.0.dc42 (identical in
lisaem-profile-5MB-FreshInstallOf-Workshop1.0.dc42).  Used by
linker/lisalinker.py -p and linker/lisapack.py; see linker/README.md.
