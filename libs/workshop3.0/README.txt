Boot volume for Workshop 3.0 - the default (LISA_BOOT overrides it).
See LIBRARIES.md and the per-library *.md files in this folder for full unit,
procedure/function, and Clascal class/method signatures.

From a Workshop 3.0 disk dump, copied unchanged (only the extension is
written in lowercase, .obj):
  INTRINSIC.LIB   (identical to the dump's Intrinsic.Lib)
  ObjIOLib.obj  iospaslib.obj  Sys1Lib.obj  IOSFPLIB.obj  Sys2Lib.obj
  PRLib.obj  SUlib.obj  LCORBGLIB.obj  QPLIB.obj  TKLIB.obj  TK2LIB.obj
Not found in the dump: *IUPASLIB.OBJ.

Library files with embedded interface text (usable by USES through
INTRINSIC.LIB):
  Sys1Lib, Sys2Lib, SUlib, iospaslib, IOSFPLIB, PRLib, ObjIOLib.
LCORBGLIB, QPLIB, TKLIB and TK2LIB contain code only (no InterfLoc block):
they are used for linking, not for compiling.

Also SYSCALL.obj and PASLIBCALL.obj, the plain unit files of Workshop 3.0 (the
dump's SysCall.Obj and PasLibCall.Obj): they are not in INTRINSIC.LIB, and a
program names them with {$U SysCall.obj}, which is looked up here when it is
not in the current directory.

SYSTEM.UNPACK: the pack table for packed code (a PackTable block, 520 bytes),
from the boot volume of lisaem-profile-5MB-FreshInstallOf_PascalWorkshop3.0.dc42
(a LisaEm ProFile image of a fresh Pascal Workshop 3.0 install).  Used by
linker/lisalinker.py -p and linker/lisapack.py; see linker/README.md.
