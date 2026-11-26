Boot volume for Workshop 1.0.  Use it with:
    LISA_BOOT=/path/to/LisaPascalCrossCompiler/libs/workshop1.0 pascal/lpc.py --2.0 MYPROG
(the default boot volume is libs/workshop3.0).  See LIBRARIES.md and the
per-library *.md files in this folder for full unit and routine signatures.

From a Workshop 1.0 disk dump, copied unchanged (only the extension is
written in lowercase, .obj):
  INTRINSIC.LIB   (identical to the dump's Intrinsic.lib)
  Objiolib.obj  IOSPaslib.obj  Sys1lib.obj  Sys2lib.obj  IOSFplib.obj  Sulib.obj
Not found in the dump: *IUPASLIB.OBJ, TELIB.OBJ, LCorBGlib.OBJ, DBLIB.OBJ,
TFOLDERLIB.OBJ, IMLIB.OBJ.

As in Workshop 2.0, only three library files contain embedded interface text:
  Sulib.obj (StdUnit), IOSFplib.obj (FPLib), IOSPaslib.obj (PasLib, PasHeap,
  BlockIO, BlkIOIntr).
Sys1lib.obj, Sys2lib.obj and Objiolib.obj contain code only, so QuickDraw,
HWInt, UnitStd, ... cannot be found through INTRINSIC.LIB; on a Workshop 1.0
system their interfaces came from separate unit files named with {$U ...}.
The StdUnit interface uses {$IFC ForOS}: define it, e.g. {$SETC ForOS := TRUE},
or get error 261.

Also SYSCALL.obj and PASLIBCALL.obj, the plain unit files of Workshop 1.0:
they are not in INTRINSIC.LIB, and a program names them with {$U SysCall.obj},
which is looked up here when it is not in the current directory.

SYSTEM.UNPACK: the pack table for packed code (a PackTable block, 520 bytes),
from the boot volume of lisaem-profile-5MB-FreshInstallOf-Workshop1.0.dc42
(identical in the LOS 2.0 + Workshop 2.0 image).  Used by
linker/lisalinker.py -p and linker/lisapack.py; see linker/README.md.
