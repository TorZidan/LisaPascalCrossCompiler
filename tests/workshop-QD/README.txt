QD/
  The QD folder of the Workshop 1.0 and 2.0 disks (identical in both):
  QuickDraw unit files (QUICKDRAW.obj, GRAF3D.obj, QDSUPPORT.obj, ...),
  link/make scripts (QDSTUFF.TEXT, M/BOXES.TEXT, M/QDSAMPLE.TEXT), and the
  sources of two sample programs, QDSAMPLE.TEXT and BOXES.TEXT.

ref-workshop1.0/, ref-workshop2.0/
  The Lisa-built, LINKED sample programs QDSAMPLE.obj and BOXES.obj from each
  disk.  They differ only in the linked-in library code: the 2.0 programs were
  relinked, not recompiled.

Tests using this directory:
  * tests/run_obj_tests.sh compiles both samples and compares each procedure
    against ref-workshop1.0/ and ref-workshop2.0/ with tools/cmplinked.py.
    All 10 procedures match except QDSAMPLE's INITICON: the Lisa version was
    built by an older code generator without literal-pool compaction, so its
    pool keeps 5 duplicate strings (250 bytes more) and the PEA offsets into
    the pool differ.
  * tests/run_link_tests.sh links the compiled samples with linker/lisalinker.py
    against libs/workshop1.0 and libs/workshop2.0, verifying that BOXES is
    byte-for-byte identical to ref-workshop{1.0,2.0}/BOXES.obj and QDSAMPLE
    matches apart from INITICON's 250-byte literal-pool shift.
