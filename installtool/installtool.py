#!/usr/bin/env python3
"""installtool.py - the Lisa Workshop Tool Install utility ('InstallTool'),
analogous to InstallTool.Obj (LISA_OS/TKIN/tkin-source.TEXT).

It registers a Workshop-built Office System tool ({T<id>}Obj, plus optional
{T<id>}PHRASE and {T<id>}ICON) into the Lisa Office System desktop on a Lisa
disk image (DC42 or raw ProFile/Widget):

  1. Updates the Filer desktop database '{!CATALOG}' on the image (replacing
     any existing tool with the same tool ID if requested, computing the tool's
     block count and creation timestamp across all '{T<id>}*' files, inserting
     the tool record, and adding/updating/removing its '<Name> Paper'
     stationery pad record).
  2. Writes the 88-byte Filer LabelFmt metadata into the OS file label of
     '{T<id>}Obj' (hint page 0 at MDDF flabel_offset).

Usage examples (matching LosSerialFtpClientMake.text lines 73-80):

    installtool.py --image disk.image Y '' 197001 N N 'Serial FTP'
    installtool.py Y disk.image 197001 N N 'Serial FTP'
    printf 'Y\\n\\n197001\\nN\\nN\\nSerial FTP\\n' | installtool.py -i disk.image
    installtool.py --image disk.image              # interactive

Positional arguments answer InstallTool's prompts in order, echoed as in the
Workshop:
  1. Automatically overwrite an existing tool with the same number? (Y/N) [NO]
  2. Device name (host disk image path, or blank/[PARAPORT] when --image or
     $LISA_IMAGE is set)
  3. Tool ID number (e.g. 197001)
     (3b. If tool ID exists and prompt 1 was N: replace current tool? Y/N)
  4. Does your tool create documents? (Y/N) [YES]
     (4b. If YES: Can your tool handle MORE THAN ONE document at a time? Y/N)
  5. Do you wish to specify a different opening rectangle? (Y/N) [NO]
     (5b..5e. If YES: left, top, right, bottom)
  6. Name of your tool (e.g. 'Serial FTP')
     (6b. If another tool already has that name: new name or <CR> to keep)
"""

from __future__ import annotations

from collections.abc import Collection, Iterable, Sequence
import os
import struct
import sys
import tempfile
import time
from typing import Any, NoReturn

HERE = os.path.dirname(os.path.abspath(__file__))

# LisaFileSystemTool: the project's file-system-tools folder (or the folder given with --fs-tool)
DEFAULT_FS_DIRS = [
    os.path.normpath(os.path.join(HERE, '..', 'file-system-tools')),
]


def _import_fs_tool(extra_dir: str | None = None) -> type[Any]:
    """Import and return FileSystemWithPerFileCommands from extra_dir or ../file-system-tools."""
    search = ([extra_dir] if extra_dir else []) + DEFAULT_FS_DIRS
    for d in search:
        if d and os.path.isfile(os.path.join(d, 'LisaFileSystemToolPerFile.py')):
            if d not in sys.path:
                sys.path.insert(0, d)
            from LisaFileSystemToolPerFile import FileSystemWithPerFileCommands
            return FileSystemWithPerFileCommands
    raise ImportError(
        'Cannot find LisaFileSystemToolPerFile.py in the project\'s file-system-tools folder (or the --fs-tool <dir> given).'
    )


# ------------------------------------------------------------ Filer / DB consts

CC_CLEAR = 27
LISA_EPOCH_OFFSET = 2177452800  # seconds between 1901-01-01 and 1970-01-01
DEFAULT_SERIAL_NO = 1970        # example Lisa serial number shown in PromptUser

# ObjectKind constants from LibFC/FilerComm.text
NIL_KIND = 0
DOC_PAD = 5
TOOL_KIND = 24

# Reserved catalog IDs from APDM/Cat.text
ID_NIL = 0
ID_DISK = 1
SPATIAL_VIEW = 0

# PropFlags bit positions (PACKED ARRAY [0..15] OF BOOLEAN in byte 0 / byte 1)
PROP_MANY_DOCS = 0x0100         # props[0] (manyDocs): bit 0 of byte 0 -> 0x0100 big-endian uint16
PROP_NO_DOCS = 0x0200           # props[1] (noDocs):   bit 1 of byte 0 -> 0x0200 big-endian uint16

# LIBDB null sentinel constants (libdb/dbdecl1.text)
NULL_INT1 = -128
NULL_INT2 = -32768
NULL_INT4 = -2147483648
MAX_INT16 = 32767

LABEL_VERSION = 2
LABEL_ERROR = 10040
FMAX_STR_LEN = 63

# LIBDB {!CATALOG} B-tree constants (libdb/pooler.text & apdm/cat.text)
CAT_DB_NAME = '{!CATALOG}'
DB_HEADER_SIZE = 512
DB_PAGE_SIZE = 2048
LEAF_TYPE = 0x9999
NONLEAF_TYPE = 0x9797
NIL_PTR = -1
FFILE_OK_BIT = 0x0010           # bit 4 in filelabel.flags
TCATREC_FIXED_SIZE = 56
PAGEDESC_SIZE = 12


# ---------------------------------------------- LIBIN International Collation
# Exact tables from LISA_OS/LIBS/LIBIN/libin-INTRTBL.TEXT & libin-INTRASM.TEXT
# used by LIBDB QASM COMPARE (CompChrMagnitude with veryWeak = True).

_FIRST_TBL = bytes([
    0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x2D,
    0x2E, 0x2F, 0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x3B,
    0x3C, 0x3D, 0x3E, 0x3F, 0x40, 0x41, 0x44, 0x45, 0x47, 0x48, 0x49, 0x4A, 0x4B, 0x4C,
    0x4D, 0x4E, 0x4F, 0x50, 0x51, 0x53, 0x55, 0x56, 0x57, 0x58, 0x59, 0x5A, 0x5B, 0x5C,
    0x5D, 0x5E, 0x5F, 0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x41, 0x44, 0x45, 0x47, 0x48,
    0x49, 0x4A, 0x4B, 0x4C, 0x4D, 0x4E, 0x4F, 0x50, 0x51, 0x53, 0x55, 0x56, 0x57, 0x58,
    0x59, 0x5A, 0x5B, 0x5C, 0x5D, 0x5E, 0x5F, 0x66, 0x67, 0x68, 0x6A, 0x69, 0x41, 0x43,
    0x46, 0x48, 0x52, 0x53, 0x5A, 0x41, 0x41, 0x41, 0x41, 0x41, 0x43, 0x46, 0x48, 0x48,
    0x48, 0x48, 0x4C, 0x4C, 0x4C, 0x4C, 0x52, 0x53, 0x53, 0x53, 0x53, 0x53, 0x5A, 0x5A,
    0x5A, 0x5A, 0x6B, 0x6C, 0x6D, 0x6E, 0x6F, 0x70, 0x71, 0x58, 0x72, 0x73, 0x74, 0x75,
    0x76, 0x77, 0x41, 0x53, 0x78, 0x79, 0x7A, 0x7B, 0x7C, 0x7D, 0x7E, 0x7F, 0x80, 0x81,
    0x82, 0x42, 0x54, 0x83, 0x41, 0x53, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89, 0x8A, 0x8B,
    0x8C, 0x8D, 0xCA, 0xCB, 0xCC, 0xCD, 0xCE, 0xCF, 0xD0, 0xD1, 0xD2, 0xD3, 0xD4, 0xD5,
    0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xDB, 0xDC, 0xDD, 0xDE, 0xDF, 0xE0, 0xE1, 0xE2, 0xE3,
    0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA, 0xEB, 0xEC, 0xED, 0xEE, 0xEF, 0xF0, 0xF1,
    0xF2, 0xF3, 0xF4, 0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA, 0xFB, 0xFC, 0xFD, 0xFE, 0x20,
])

_SECOND_TBL = bytes([
    0x00, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01,
    0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01,
    0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01,
    0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01,
    0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x02, 0x02, 0x02, 0x02, 0x03,
    0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02,
    0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x01, 0x01, 0x01, 0x01, 0x01, 0x0B, 0x01,
    0x01, 0x02, 0x01, 0x3D, 0x51, 0x03, 0x04, 0x05, 0x16, 0x06, 0x02, 0x02, 0x06, 0x04,
    0x07, 0x05, 0x03, 0x04, 0x05, 0x06, 0x02, 0x03, 0x04, 0x05, 0x48, 0x06, 0x03, 0x04,
    0x05, 0x5C, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x34, 0x01, 0x01, 0x01, 0x01,
    0x01, 0x01, 0x1F, 0x65, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01,
    0x01, 0x01, 0x01, 0x01, 0x2A, 0x70, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01,
    0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
])

_EXPAND = {
    0x80: 0x45, 0x8A: 0x65, 0xAE: 0x45, 0xBE: 0x65, 0xA7: 0x73,
    0x85: 0x45, 0x9A: 0x65, 0x86: 0x45, 0x9F: 0x65, 0xAF: 0x45, 0xBF: 0x65,
}

_DOWN_TBL = bytes([
    0x61, 0x62, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x6B, 0x6C, 0x6D, 0x6E,
    0x6F, 0x70, 0x71, 0x72, 0x73, 0x74, 0x75, 0x76, 0x77, 0x78, 0x79, 0x7A, 0x5B, 0x5C,
    0x5D, 0x5E, 0x5F, 0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6A,
    0x6B, 0x6C, 0x6D, 0x6E, 0x6F, 0x70, 0x71, 0x72, 0x73, 0x74, 0x75, 0x76, 0x77, 0x78,
    0x79, 0x7A, 0x7B, 0x7C, 0x7D, 0x7E, 0x7F, 0x8A, 0x8C, 0x8D, 0x8E, 0x96, 0x9A, 0x9F,
    0x87, 0x88, 0x89, 0x8A, 0x8B, 0x8C, 0x8D, 0x8E, 0x8F, 0x90, 0x91, 0x92, 0x93, 0x94,
    0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0x9B, 0x9C, 0x9D, 0x9E, 0x9F, 0xA0, 0xA1, 0xA2,
    0xA3, 0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xAB, 0xAC, 0xAD, 0xBE, 0xBF, 0xB0,
    0xB1, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6, 0xB7, 0xB8, 0xB9, 0xBA, 0xBB, 0xBC, 0xBD, 0xBE,
    0xBF, 0xC0, 0xC1, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9, 0xCA, 0xCB, 0xCC,
    0xCD, 0xCE, 0xCF, 0xD0, 0xD1, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA,
    0xDB, 0xDC, 0xDD, 0xDE, 0xDF, 0xE0, 0xE1, 0xE2, 0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8,
    0xE9, 0xEA, 0xEB, 0xEC, 0xED, 0xEE, 0xEF, 0xF0, 0xF1, 0xF2, 0xF3, 0xF4, 0xF5, 0xF6,
    0xF7, 0xF8, 0xF9, 0xFA, 0xFB, 0xFC, 0xFD, 0xFE, 0xFF, 0x69,
])

_WEAK_TBL = bytes([
    0x1F, 0x00, 0x00, 0x00, 0x3F, 0x00, 0x00, 0x00, 0x5F, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x7F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x9F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x21, 0x00, 0x00, 0x00, 0x01, 0x02, 0x04, 0x00,
    0x08, 0x00, 0x00, 0x21, 0x22, 0x24, 0x28, 0x41, 0x42, 0x44, 0x48, 0x00, 0x61, 0x62,
    0x64, 0x00, 0x68, 0x81, 0x82, 0x84, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x40,
])


def _very_weak_equal(b1: bytes, b2: bytes) -> bool:
    """Return True if byte strings b1 and b2 match under LIBIN case- and accent-insensitive equality."""
    if len(b1) != len(b2):
        return False
    for c1, c2 in zip(b1, b2):
        if c1 >= 65:
            c1 = _DOWN_TBL[c1 - 65]
        if c2 >= 65:
            c2 = _DOWN_TBL[c2 - 65]
        if c1 == c2:
            continue
        if c1 < 97 or c2 < 97:
            return False
        w1 = _WEAK_TBL[c1 - 97] if (c1 - 97) < len(_WEAK_TBL) else 0
        w2 = _WEAK_TBL[c2 - 97] if (c2 - 97) < len(_WEAK_TBL) else 0
        if w1 == 0 or w2 == 0 or (w1 & 0xE0) != (w2 & 0xE0):
            return False
    return True


def _expand_stream(b: bytes) -> list[int]:
    """Expand two-character ligatures (such as AE, OE, ss) into byte sequences per LIBIN _EXPAND."""
    out = []
    for c in b:
        out.append(c)
        if c >= 32 and _SECOND_TBL[c - 32] > 10 and c in _EXPAND:
            out.append(_EXPAND[c])
    return out


def comp_chr_magnitude(b1: bytes, b2: bytes) -> int:
    """Exact port of LIBIN CompChrMagnitude(b1, b2, len(b1), len(b2), veryWeak=True).
    Returns -1, 0, or +1."""
    if _very_weak_equal(b1, b2):
        return 0
    s1 = _expand_stream(b1)
    s2 = _expand_stream(b2)
    for c1, c2 in zip(s1, s2):
        w1 = _FIRST_TBL[c1 - 32] if c1 >= 32 else c1
        w2 = _FIRST_TBL[c2 - 32] if c2 >= 32 else c2
        if w1 != w2:
            return 1 if w1 > w2 else -1
    if len(s1) != len(s2):
        return 1 if len(s1) > len(s2) else -1
    for c1, c2 in zip(s1, s2):
        w1 = _SECOND_TBL[c1 - 32] if c1 >= 32 else c1
        w2 = _SECOND_TBL[c2 - 32] if c2 >= 32 else c2
        if w1 != w2:
            return 1 if w1 > w2 else -1
    return 0


def to_s32(v: int) -> int:
    """Convert integer v to a signed 32-bit two's-complement Python int."""
    v &= 0xFFFFFFFF
    return v - 0x100000000 if v & 0x80000000 else v


# ---------------------------------------------------- TCatRec & LabelFmt models

class InstallAbort(Exception):
    """Raised when Conclude(FALSE) or CLEAR aborts InstallTool."""
    def __init__(self, exit_code: int = 1) -> None:
        """Initialize abort exception with the desired process exit_code."""
        super().__init__()
        self.exit_code = exit_code


class CatRec:
    """In-memory representation of APDM/Cat.text TcatRec (56-byte fixed part +
    variable-length Mac-Roman object name)."""

    def __init__(
        self,
        parent_id: int = ID_DISK,
        name: str = '',
        self_id: int = ID_NIL,
        obj_kind: int = NIL_KIND,
        obj_state: int = NULL_INT1,
        view: int = SPATIAL_VIEW,
        props: int = 0,
        open_rect: tuple[int, int, int, int] = (40, 10, 290, 640),   # QuickDraw Rect: (top, left, bottom, right)
        closed_pt: tuple[int, int] = (MAX_INT16, MAX_INT16),  # QuickDraw Point: (v, h)
        created: int = NULL_INT4,
        modified: int = NULL_INT4,
        obj_size: int = 0,
        tool_id: int = NULL_INT4,
        split: int = NULL_INT2,
        unused2: int = NULL_INT4,
        extra: bytes = b'',
        pad_byte: int = 0,
    ) -> None:
        """Initialize a Filer catalog record with desktop coordinates, flags, timestamps, and tool metadata."""
        self.parent_id = parent_id
        self.name = name[:FMAX_STR_LEN]
        self.self_id = self_id
        self.obj_kind = obj_kind
        self.obj_state = obj_state
        self.view = view
        self.props = props
        self.open_rect = tuple(open_rect)
        self.closed_pt = tuple(closed_pt)
        self.created = to_s32(created)
        self.modified = to_s32(modified)
        self.obj_size = obj_size
        self.tool_id = to_s32(tool_id)
        self.split = split
        self.unused2 = to_s32(unused2)
        self.extra = bytes(extra)
        self.pad_byte = pad_byte

    def copy(self) -> CatRec:
        """Return a copy of this catalog record."""
        return CatRec(
            parent_id=self.parent_id,
            name=self.name,
            self_id=self.self_id,
            obj_kind=self.obj_kind,
            obj_state=self.obj_state,
            view=self.view,
            props=self.props,
            open_rect=self.open_rect,
            closed_pt=self.closed_pt,
            created=self.created,
            modified=self.modified,
            obj_size=self.obj_size,
            tool_id=self.tool_id,
            split=self.split,
            unused2=self.unused2,
            extra=self.extra,
            pad_byte=self.pad_byte,
        )

    @property
    def no_docs(self) -> bool:
        """Return True if the tool's noDocs property flag is set (tool does not create documents)."""
        return bool(self.props & PROP_NO_DOCS)

    @no_docs.setter
    def no_docs(self, val: bool) -> None:
        """Set or clear the noDocs bit in self.props."""
        if val:
            self.props |= PROP_NO_DOCS
        else:
            self.props &= ~PROP_NO_DOCS

    @property
    def many_docs(self) -> bool:
        """Return True if the tool's manyDocs property flag is set (handles multiple open documents)."""
        return bool(self.props & PROP_MANY_DOCS)

    @many_docs.setter
    def many_docs(self, val: bool) -> None:
        """Set or clear the manyDocs bit in self.props."""
        if val:
            self.props |= PROP_MANY_DOCS
        else:
            self.props &= ~PROP_MANY_DOCS

    def key_tuple(self) -> tuple[int, bytes, int]:
        """Return the raw (parent_id, mac_roman_name, unsigned_self_id) tuple for this record's key."""
        return (self.parent_id, self.name.encode('mac-roman', 'replace'), self.self_id & 0xFFFFFFFF)

    def compare_key(self, other: CatRec) -> int:
        """Compare this record's B-tree sort key (parent_id, LIBIN-collated name, self_id) with other."""
        if self.parent_id != other.parent_id:
            return -1 if self.parent_id < other.parent_id else 1
        nb1 = self.name.encode('mac-roman', 'replace')
        nb2 = other.name.encode('mac-roman', 'replace')
        c = comp_chr_magnitude(nb1, nb2)
        if c != 0:
            return c
        u1 = self.self_id & 0xFFFFFFFF
        u2 = other.self_id & 0xFFFFFFFF
        if u1 != u2:
            return -1 if u1 < u2 else 1
        return 0

    def to_bytes(self) -> bytes:
        """Serialize this catalog record to big-endian TcatRec bytes, word-aligned with pad_byte."""
        name_bytes = self.name.encode('mac-roman')[:FMAX_STR_LEN]
        name_off = TCATREC_FIXED_SIZE
        name_sz = len(name_bytes)
        extra_off = name_off + name_sz
        extra_sz = len(self.extra)
        top, left, bottom, right = self.open_rect
        cv, ch = self.closed_pt
        fixed = struct.pack(
            '>ihhihbbHhhhhhhiiiihihh',
            self.parent_id,
            name_sz,
            name_off,
            self.self_id,
            self.obj_kind,
            self.obj_state,
            self.view,
            self.props & 0xFFFF,
            top,
            left,
            bottom,
            right,
            cv,
            ch,
            to_s32(self.created),
            to_s32(self.modified),
            self.obj_size,
            to_s32(self.tool_id),
            self.split,
            to_s32(self.unused2),
            extra_sz,
            extra_off,
        )
        raw = bytearray(fixed) + name_bytes + self.extra
        if len(raw) & 1:
            raw.append(self.pad_byte & 0xFF)
        return bytes(raw)

    @classmethod
    def from_bytes(cls, buf: bytes) -> CatRec:
        """Deserialize a CatRec instance from raw TcatRec record bytes."""
        (
            pid, nsz, noff, sid, kind, st, view, props,
            top, left, bottom, right, cv, ch,
            dtc, dtm, osz, tid, split, un2, esz, eoff,
        ) = struct.unpack_from('>ihhihbbHhhhhhhiiiihihh', buf, 0)
        name_bytes = buf[noff:noff + nsz]
        extra_bytes = buf[eoff:eoff + esz] if esz > 0 else b''
        used = TCATREC_FIXED_SIZE + nsz + esz
        pad = buf[used] if (used & 1) and len(buf) > used else 0
        return cls(
            parent_id=pid,
            name=name_bytes.decode('mac-roman'),
            self_id=sid,
            obj_kind=kind,
            obj_state=st,
            view=view,
            props=props,
            open_rect=(top, left, bottom, right),
            closed_pt=(cv, ch),
            created=dtc,
            modified=dtm,
            obj_size=osz,
            tool_id=tid,
            split=split,
            unused2=un2,
            extra=extra_bytes,
            pad_byte=pad,
        )


def build_label_fmt_bytes(
    name: str,
    no_docs: bool,
    many_docs: bool,
    open_rect: tuple[int, int, int, int],
) -> bytes:
    """Pack the 88-byte APDM/Globals LabelFmt record."""
    name_bytes = name.encode('mac-roman')[:FMAX_STR_LEN]
    name_field = bytes([len(name_bytes)]) + name_bytes.ljust(FMAX_STR_LEN, b'\x00')
    top, left, bottom, right = open_rect
    return struct.pack(
        '>H64shBBhhhhhii',
        LABEL_VERSION,
        name_field,
        TOOL_KIND,
        1 if no_docs else 0,
        1 if many_docs else 0,
        top,
        left,
        bottom,
        right,
        NULL_INT2,  # split := nullInt2
        0,          # totalSize := 0
        1,          # parentID := 1
    )


# --------------------------------------------------------- {!CATALOG} DB file

class FilerCatalogDB:
    """Reader/writer for the Filer's LIBDB '{!CATALOG}' B-tree database file."""

    def __init__(self, raw_bytes: bytes) -> None:
        """Parse the 512-byte LIBDB header and load all leaf catalog records from raw_bytes."""
        if len(raw_bytes) < DB_HEADER_SIZE + DB_PAGE_SIZE:
            raise ValueError('Catalog file is shorter than 2560 bytes')
        check1, db_vers = struct.unpack_from('>HB', raw_bytes, 0)
        check2 = struct.unpack_from('>H', raw_bytes, 0x42)[0]
        if check1 != LEAF_TYPE or check2 != NONLEAF_TYPE or db_vers != 1:
            raise ValueError('File is not a valid LIBDB {!CATALOG} database')

        self.header = bytearray(raw_bytes[:DB_HEADER_SIZE])
        (
            _c1, _dbv, self.user_vers, self.update_version, self.flags,
            self.first_page, self.last_page, self.nrecs, self.page_size,
            self.nfields, self.nkeys, self.nsort, self.vflds, self.kvflds,
            self.depth, self.root_offset, self.freelist, self.labellist,
            self.labeltickets, self.ticket_high, self.next_id, self.ticket_fld,
        ) = struct.unpack_from('>HBBHHIIIHHHHHHHiiiihih', self.header, 0)

        if self.page_size != DB_PAGE_SIZE or self.first_page != DB_HEADER_SIZE:
            raise ValueError('Unsupported {!CATALOG} page layout')

        # Walk the leaf chain starting from the leftmost leaf to load all CatRecs
        self.raw_full = bytearray(raw_bytes)
        self.records = self._load_all_records()

    def _read_page_records(self, page_off: int) -> tuple[int, int, int, list[bytes]]:
        """Extract (page_type, prior_offset, next_offset, raw_records) from the 2048-byte page at page_off."""
        pg = self.raw_full[page_off:page_off + DB_PAGE_SIZE]
        nkeys, ptype, prior_off, next_off = struct.unpack_from(
            '>HHii', pg, DB_PAGE_SIZE - PAGEDESC_SIZE
        )
        offs = [
            struct.unpack_from('>H', pg, DB_PAGE_SIZE - PAGEDESC_SIZE - 2 - 2 * k)[0]
            for k in range(nkeys + 1)
        ]
        recs = [bytes(pg[offs[i]:offs[i + 1]]) for i in range(nkeys)]
        return ptype, prior_off, next_off, recs

    def _leftmost_leaf_offset(self) -> int:
        """Descend from root_offset along first-child pointers to locate the leftmost leaf page offset."""
        off = self.root_offset
        for _ in range(self.depth - 1):
            ptype, _p, _n, recs = self._read_page_records(off)
            if ptype != NONLEAF_TYPE or not recs:
                raise ValueError('Corrupt nonleaf page in {!CATALOG}')
            off = struct.unpack_from('>i', recs[0], 0)[0]
        return off

    def _load_all_records(self) -> list[CatRec]:
        """Walk the doubly linked leaf page chain and decode every CatRec in key order."""
        if self.nrecs == 0 or self.root_offset == NIL_PTR:
            return []
        off = self._leftmost_leaf_offset()
        out = []
        visited = set()
        while off != NIL_PTR:
            if off in visited:
                raise ValueError('Cycle in {!CATALOG} leaf chain')
            visited.add(off)
            ptype, _prior, nxt, raw_recs = self._read_page_records(off)
            if ptype != LEAF_TYPE:
                raise ValueError('Expected leaf page in {!CATALOG}')
            for r in raw_recs:
                out.append(CatRec.from_bytes(r))
            off = nxt
        return out

    def find_obj(
        self,
        name: str = '',
        kinds: Collection[int] | None = None,
        tool_id: int = -1,
    ) -> tuple[int, CatRec] | tuple[None, None]:
        """Port of APDM/Cat ObjInCat: returns (index, CatRec) or (None, None)."""
        for idx, rec in enumerate(self.records):
            if kinds is not None and rec.obj_kind not in kinds:
                continue
            if tool_id != -1 and rec.tool_id != tool_id:
                continue
            if name != '' and rec.name != name:
                continue
            return idx, rec
        return None, None

    def delete_at(self, index: int) -> None:
        """Remove the catalog record at position index."""
        del self.records[index]

    def insert_rec(self, rec: CatRec, gen_id: bool = True) -> int:
        """Insert rec in LIBDB key order, optionally assigning next_id, and return its self_id."""
        if gen_id:
            rec.self_id = self.next_id
            self.next_id += 1
        elif rec.self_id >= self.next_id:
            self.next_id = rec.self_id + 1

        ins_pos = len(self.records)
        for i, existing in enumerate(self.records):
            c = rec.compare_key(existing)
            if c == 0:
                raise ValueError('Duplicate key in {!CATALOG}')
            if c < 0:
                ins_pos = i
                break
        self.records.insert(ins_pos, rec)
        return rec.self_id

    def update_at(self, index: int, new_rec: CatRec) -> None:
        """Replace the record at index with new_rec, re-inserting it at its updated sort position."""
        del self.records[index]
        self.insert_rec(new_rec, gen_id=False)

    @staticmethod
    def _pack_page(raw_recs: Sequence[bytes], ptype: int, prior_off: int, next_off: int) -> bytes:
        """Pack raw record slices, offset directory, and 12-byte trailer into a 2048-byte B-tree page."""
        pg = bytearray([0xFF] * DB_PAGE_SIZE)
        pos = 0
        offs = [0]
        for r in raw_recs:
            pg[pos:pos + len(r)] = r
            pos += len(r)
            offs.append(pos)
        for k, o in enumerate(offs):
            struct.pack_into('>H', pg, DB_PAGE_SIZE - PAGEDESC_SIZE - 2 - 2 * k, o)
        struct.pack_into('>HHii', pg, DB_PAGE_SIZE - PAGEDESC_SIZE, len(raw_recs), ptype, prior_off, next_off)
        return bytes(pg)

    @staticmethod
    def _fits_in_page(raw_recs: Sequence[bytes]) -> bool:
        """Return True if raw_recs plus their offset table and page descriptor fit in one 2048-byte page."""
        total_rec_bytes = sum(len(r) for r in raw_recs)
        desc_and_offs = PAGEDESC_SIZE + 2 * (len(raw_recs) + 1)
        return total_rec_bytes + desc_and_offs <= DB_PAGE_SIZE

    def to_bytes(self) -> bytes:
        """Rebuild the {!CATALOG} header and B-tree pages from self.records and return the file bytes."""
        encoded = [r.to_bytes() for r in self.records]
        self.nrecs = len(encoded)
        self.update_version = (self.update_version + 1) & 0xFFFF
        self.flags |= FFILE_OK_BIT

        # Fast/exact path when everything fits in a single leaf page at 0x200
        if self._fits_in_page(encoded):
            self.depth = 1
            self.root_offset = DB_HEADER_SIZE
            leaf_page = self._pack_page(encoded, LEAF_TYPE, NIL_PTR, NIL_PTR)
            num_existing_pages = max(1, (len(self.raw_full) - DB_HEADER_SIZE) // DB_PAGE_SIZE)
            if num_existing_pages == 1:
                self.last_page = DB_HEADER_SIZE + DB_PAGE_SIZE
                pages_bytes = leaf_page
            else:
                # Preserve existing file length if catalog previously had extra pages
                pages = bytearray(self.raw_full[DB_HEADER_SIZE:])
                pages[:DB_PAGE_SIZE] = leaf_page
                pages_bytes = bytes(pages)
        else:
            # Multi-page B-tree build: pack leaves (~70% fill on splits) and build nonleaf root
            leaf_chunks = []
            cur = []
            for r in encoded:
                if cur and not self._fits_in_page(cur + [r]):
                    leaf_chunks.append(cur)
                    cur = [r]
                else:
                    cur.append(r)
            if cur:
                leaf_chunks.append(cur)

            pages_list = []
            leaf_offsets = [DB_HEADER_SIZE + i * DB_PAGE_SIZE for i in range(len(leaf_chunks))]
            for i, chunk in enumerate(leaf_chunks):
                prior_off = leaf_offsets[i - 1] if i > 0 else NIL_PTR
                next_off = leaf_offsets[i + 1] if i + 1 < len(leaf_chunks) else NIL_PTR
                pages_list.append(self._pack_page(chunk, LEAF_TYPE, prior_off, next_off))

            # Nonleaf entry for nsort=1 (fldParent): 4-byte page_ptr + 4-byte parentId
            nonleaf_recs = []
            for off, chunk in zip(leaf_offsets, leaf_chunks):
                first_pid = struct.unpack_from('>i', chunk[0], 0)[0]
                nonleaf_recs.append(struct.pack('>ii', off, first_pid))

            root_off = DB_HEADER_SIZE + len(pages_list) * DB_PAGE_SIZE
            pages_list.append(self._pack_page(nonleaf_recs, NONLEAF_TYPE, NIL_PTR, NIL_PTR))
            self.depth = 2
            self.root_offset = root_off
            self.last_page = DB_HEADER_SIZE + len(pages_list) * DB_PAGE_SIZE
            pages_bytes = b''.join(pages_list)

        hdr = bytearray(self.header)
        struct.pack_into(
            '>HBBHHIIIHHHHHHHiiiihih',
            hdr,
            0,
            LEAF_TYPE,
            1,
            self.user_vers,
            self.update_version,
            self.flags,
            self.first_page,
            self.last_page,
            self.nrecs,
            self.page_size,
            self.nfields,
            self.nkeys,
            self.nsort,
            self.vflds,
            self.kvflds,
            self.depth,
            self.root_offset,
            self.freelist,
            self.labellist,
            self.labeltickets,
            self.ticket_high,
            self.next_id,
            self.ticket_fld,
        )
        return bytes(hdr) + pages_bytes


# --------------------------------------------------- Volume inspection & write

def scan_tool_files(fs: Any, tool_id: int) -> tuple[int, int]:
    """Port of tkin-source.TEXT ToolSize: scan all root-level files starting
    with '{T<tool_id>}' (case-insensitive) and return (size_blks, created_s32)."""
    prefix_upper = ('{T%d}' % tool_id).upper()
    datasize = fs._mddf_u16(0x7E) or 512
    hintsize = fs._mddf_u16(0xA2) or 1

    created = NULL_INT4
    size_blks = 0

    if not fs.is_flat_catalog_volume():
        for _leaf, _idx, rec in fs._bt_scan_entries():
            etype = rec[36]
            if etype != 3:  # fileentry only
                continue
            par_id = (rec[1] << 8) | rec[2]
            if par_id != 0:
                continue
            raw_name = rec[3:35].split(b'\x00', 1)[0].decode('mac-roman', 'replace')
            if not raw_name.upper().startswith(prefix_upper):
                continue
            file_dtc = struct.unpack_from('>i', rec, 40)[0]
            file_size = struct.unpack_from('>I', rec, 48)[0]
            phys_size = struct.unpack_from('>I', rec, 52)[0]
            fs_ovrhd = struct.unpack_from('>H', rec, 56)[0] or hintsize
            if phys_size == 0 and file_size > 0:
                phys_size = ((file_size + datasize - 1) // datasize) * datasize
            if file_dtc > created:
                created = file_dtc
            file_blks = (phys_size + datasize - 1) // datasize
            size_blks += file_blks + fs_ovrhd
    else:
        cat_data, rootmax = fs._flat_read_rootcatalog()
        for slot in range(rootmax):
            rec = cat_data[slot * 54:(slot + 1) * 54]
            nlen = rec[0]
            cetype = rec[34]
            if cetype != 3 or nlen == 0:
                continue
            raw_name = rec[1:1 + nlen].decode('mac-roman', 'replace')
            if not raw_name.upper().startswith(prefix_upper):
                continue
            sfile = struct.unpack_from('>H', rec, 36)[0]
            se = fs._slist_entry(sfile)
            if se is None or se[0] == 0:
                continue
            hint_rel, _faddr, fsize, _ver = se
            hp = fs.read_sector(fs._mddf_sector_number + hint_rel)
            file_dtc = struct.unpack_from('>i', hp, 0x2E)[0]
            phys_size = ((fsize + datasize - 1) // datasize) * datasize
            if file_dtc > created:
                created = file_dtc
            file_blks = (phys_size + datasize - 1) // datasize
            size_blks += file_blks + hintsize

    if created == NULL_INT4:
        created = to_s32(int(time.time()) + LISA_EPOCH_OFFSET)
    return size_blks, created


def locate_tool_obj_sfile(fs: Any, tool_id: int) -> int | None:
    """Find s-file number of '{T<tool_id>}obj' (case-insensitive), or None."""
    target = '{T%d}obj' % tool_id
    loc = fs._locate_named_file(target)
    if loc.status == 'file':
        return loc.sfile
    return None


def commit_install_to_image(
    fs: Any,
    new_cat_bytes: bytes,
    obj_sfile: int,
    label_bytes: bytes,
) -> None:
    """Write both the updated {!CATALOG} and {T<id>}obj's file label to the disk image."""
    mddf = fs._mddf_sector_number
    flabel_off = fs._mddf_u16(0xA8)  # MDDF offset 168: flabel_offset (384 on standard LOS volumes)
    if flabel_off < 0x80 or flabel_off + len(label_bytes) > 512:
        raise RuntimeError('Unexpected MDDF flabel_offset %d' % flabel_off)

    # Locate {!CATALOG}
    cat_loc = fs._locate_named_file(CAT_DB_NAME)
    if cat_loc.status != 'file':
        raise RuntimeError("Could not locate '%s' on disk image" % CAT_DB_NAME)
    cat_se = fs._slist_entry(cat_loc.sfile)
    if cat_se is None:
        raise RuntimeError("Missing slist entry for '%s'" % CAT_DB_NAME)
    _cat_hint, cat_fileaddr, cat_filesize, _cat_ver = cat_se

    modified = set()
    if len(new_cat_bytes) == cat_filesize:
        # In-place update of {!CATALOG}'s existing data sectors (exact match to OpenScan update)
        cat_pages = fs._data_page_chain(cat_fileaddr)
        if len(cat_pages) * 512 < len(new_cat_bytes):
            raise RuntimeError("'%s' data chain shorter than filesize" % CAT_DB_NAME)
        for i, rel_p in enumerate(cat_pages):
            chunk = new_cat_bytes[i * 512:(i + 1) * 512]
            if not chunk:
                break
            sec_buf = bytearray(512)
            sec_buf[:len(chunk)] = chunk
            abs_sn = mddf + rel_p
            fs._mem_write_sector_data(abs_sn, bytes(sec_buf))
            modified.add(abs_sn)
    else:
        # {!CATALOG} grew (page split): replace_file reuses existing sectors and allocates new ones
        saved_stdout = sys.stdout
        try:
            sys.stdout = open(os.devnull, 'w')
            with tempfile.NamedTemporaryFile(delete=False) as tf:
                tf.write(new_cat_bytes)
                tmp_path = tf.name
            try:
                rc = fs.replace_file(tmp_path, CAT_DB_NAME)
                if rc != 0:
                    raise RuntimeError("Failed to write grown '%s' to image" % CAT_DB_NAME)
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        finally:
            sys.stdout.close()
            sys.stdout = saved_stdout

    # Update {T<id>}obj's hint page label (Write_Label syscall equivalent)
    obj_se = fs._slist_entry(obj_sfile)
    if obj_se is None or obj_se[0] <= 0:
        raise RuntimeError('Bad slist entry for tool object s-file %d' % obj_sfile)
    obj_hint_abs = mddf + obj_se[0]
    hint_buf = bytearray(fs.read_sector(obj_hint_abs))
    hint_buf[flabel_off:flabel_off + len(label_bytes)] = label_bytes
    fs._mem_write_sector_data(obj_hint_abs, bytes(hint_buf))
    modified.add(obj_hint_abs)

    fs._flush_modified_sectors(modified)
    if fs._is_dc42_format:
        fs.fix_dc42_checksum(confirm=False)


# --------------------------------------------------------------- CLI & Dialog

class Dialog:
    """Answers InstallTool prompts from CLI args (echoed) or from stdin."""

    def __init__(self, args: Iterable[str]) -> None:
        """Initialize prompt reader with optional positional CLI answers."""
        self.args = list(args)
        self.from_args = bool(args)

    def read_line(self, prompt: str) -> str:
        """Prompt and return the next answer string from CLI arguments or stdin."""
        sys.stdout.write(prompt)
        sys.stdout.flush()
        if self.from_args:
            if not self.args:
                print()
                raise EOFError('No more command-line answers for prompt: %r' % prompt)
            ans = self.args.pop(0)
            print(ans)
            return ans
        line = sys.stdin.readline()
        if not line:
            print()
            raise EOFError('End of input')
        ans = line.rstrip('\r\n')
        if not sys.stdin.isatty():
            print(ans)
        return ans

    def get_yn(self, prompt: str, default: bool) -> bool:
        """Prompt for a Yes/No response (port of TKIN GetYN), returning default on empty input."""
        ans = self.read_line(prompt)
        while True:
            low = ans.lower()
            if len(low) == 0:
                return default
            if ord(low[0]) == CC_CLEAR:
                raise InstallAbort(1)
            if low[0] == 'y':
                return True
            if low[0] == 'n':
                return False
            print()
            ans = self.read_line(' Y or N ? ')

    def get_num(self, prompt: str) -> int:
        """Prompt repeatedly until a valid base-10 integer is entered, aborting on CLEAR."""
        while True:
            ans = self.read_line(prompt)
            print()
            if len(ans) > 0:
                if ord(ans[0]) == CC_CLEAR:
                    raise InstallAbort(1)
                s = ans.strip()
                try:
                    return int(s, 10)
                except ValueError:
                    if self.from_args:
                        raise ValueError('Invalid integer %r' % ans)


def print_usage() -> None:
    """Print command-line usage and option help to stdout."""
    print(
        'Usage: installtool.py [-i IMAGE | --image IMAGE] [--fs-tool DIR] '
        '[OVERWRITE DEVICE TOOL_ID DOCS ... TOOL_NAME]\n\n'
        'Installs a Workshop-built Office System tool ({T<id>}Obj) into {!CATALOG}\n'
        'and writes its Filer label on a Lisa disk image.\n\n'
        'Options:\n'
        '  -i, --image IMAGE   Lisa disk image file (used when device prompt is\n'
        '                      blank / PARAPORT; can also be set via $LISA_IMAGE,\n'
        '                      or given directly at the device prompt)\n'
        '  --fs-tool DIR       Folder with LisaFileSystemToolPerFile.py (default: ../file-system-tools)\n'
        '  -h, --help          Show this help message and exit'
    )


def parse_cli(argv: Sequence[str]) -> tuple[str, str | None, list[str]]:
    """Parse CLI flags (-i/--image, --fs-tool, -h/--help) and return (image_opt, fs_tool_opt, positional_args)."""
    image_opt = os.environ.get('LISA_IMAGE', '')
    fs_tool_opt = None
    pos = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ('-h', '--help'):
            print_usage()
            sys.exit(0)
        elif a in ('-i', '--image'):
            if i + 1 >= len(argv):
                sys.stderr.write('installtool.py: %s requires an image path\n' % a)
                sys.exit(1)
            image_opt = argv[i + 1]
            i += 2
        elif a.startswith('--image='):
            image_opt = a.split('=', 1)[1]
            i += 1
        elif a == '--fs-tool':
            if i + 1 >= len(argv):
                sys.stderr.write('installtool.py: --fs-tool requires a directory\n')
                sys.exit(1)
            fs_tool_opt = argv[i + 1]
            i += 2
        elif a.startswith('--fs-tool='):
            fs_tool_opt = a.split('=', 1)[1]
            i += 1
        else:
            pos.append(a)
            i += 1
    return image_opt, fs_tool_opt, pos


def error_check(err: int, fn_name: str) -> NoReturn:
    """Print an InstallTool catalog/label failure message (port of TKIN ErrorCheck) and raise InstallAbort."""
    print('The call to <%s> failed. The error number reported was %d' % (fn_name, err))
    print('Error %d' % err)
    raise InstallAbort(1)


def main(argv: Sequence[str]) -> int:
    """Run the interactive or scripted Lisa Workshop Tool Install workflow and return an exit status."""
    image_opt, fs_tool_opt, pos_args = parse_cli(argv)
    try:
        FSClass = _import_fs_tool(fs_tool_opt)
    except ImportError as exc:
        sys.stderr.write('%s\n' % exc)
        return 1

    dialog = Dialog(pos_args)

    try:
        # ---- Initialize ----
        print(' ' * 25 + 'TOOL INSTALL')
        print()
        print()
        print('Tool Install allows programs developed on the ')
        print('Workshop to be used with the Office System. ')
        print()
        print()
        print('         *******  WARNING  *******')
        print('Each tool must have a unique number, one that is')
        print('different from all other tool numbers on the same')
        print('Office System disk.')
        print()

        print('Do you want to automatically overwrite an existing tool')
        allow_same_number = dialog.get_yn(
            '      with the same number? ( Y or N ) [NO] >> ', False
        )
        print()
        print()

        cat_rec = CatRec(parent_id=ID_DISK)
        hold_name = ''

        # ---- OpenCatalog ----
        print('If your tool is not on the device that you want to install it on,')
        print('then enter CLEAR to exit the program and move your tool')
        print('to the proper device. ')
        print()
        dev_ans = dialog.read_line(
            'Please enter the name of the device your tool is on. [PARAPORT]. >> '
        )
        print()
        if len(dev_ans) > 0 and ord(dev_ans[0]) == CC_CLEAR:
            return 0

        if len(dev_ans) == 0:
            dev_display = 'paraport'
        else:
            dev_display = dev_ans

        # Resolve host disk image path from dev_ans or --image / $LISA_IMAGE
        cleaned_dev = dev_ans.strip()
        if cleaned_dev.startswith('-') and cleaned_dev.endswith('-') and len(cleaned_dev) > 2:
            cleaned_dev = cleaned_dev[1:-1]

        if cleaned_dev and os.path.isfile(cleaned_dev):
            image_path = cleaned_dev
        elif image_opt:
            image_path = image_opt
        elif cleaned_dev:
            # User gave a path that does not exist (or a Lisa device name without --image)
            sys.stderr.write(
                "Cannot find disk image '%s' (pass a valid disk image path or use --image <disk.image>).\n"
                % dev_ans
            )
            error_check(948, 'OpenCat')
        else:
            sys.stderr.write(
                'No disk image specified for [PARAPORT]: pass --image <disk.image>, set LISA_IMAGE, '
                'or enter the disk image path at the device prompt.\n'
            )
            error_check(948, 'OpenCat')

        # Ensure the disk image has {!CATALOG} and read it (suppress LisaFileSystemTool chatter)
        saved_stdout = sys.stdout
        cat_status = None
        try:
            sys.stdout = open(os.devnull, 'w')
            fs = FSClass(image_path)
            cat_loc = fs._locate_named_file(CAT_DB_NAME)
            cat_status = cat_loc.status
            cat_bytes = (
                fs.read_file_as_bytes(CAT_DB_NAME, binary=True)
                if cat_status == 'file'
                else None
            )
        except Exception as exc:
            sys.stdout.close()
            sys.stdout = saved_stdout
            sys.stderr.write('Error opening disk image %s: %s\n' % (image_path, exc))
            error_check(948, 'OpenCat')
        else:
            sys.stdout.close()
            sys.stdout = saved_stdout

        if cat_status != 'file' or not cat_bytes:
            sys.stderr.write(
                '%s: not a Lisa Office System 3.0 disk! (missing %s)\n'
                % (image_path, CAT_DB_NAME)
            )
            error_check(948, 'OpenCat')

        try:
            cat_db = FilerCatalogDB(cat_bytes)
        except ValueError:
            error_check(3418, 'OpenCat')

        # ---- PromptUser ----
        print('Each tool must have a unique number.  One such number')
        print('is %d, which is the serial number of this Lisa.' % DEFAULT_SERIAL_NO)
        print('If you are developing multiple tools on the same machine, may I')
        print('suggest that you multiply this number by 100 and add an offset.')

        while True:
            print()
            cat_rec.tool_id = dialog.get_num('Please enter your tool id number >> ')
            existing_idx, existing_rec = cat_db.find_obj(
                name='', kinds={TOOL_KIND}, tool_id=cat_rec.tool_id
            )
            if existing_rec is not None:
                if allow_same_number:
                    reply = True
                else:
                    print('There is already a tool with the number %d.' % cat_rec.tool_id)
                    reply = dialog.get_yn(
                        'Do you wish to replace the current tool? ( Y or N ) [NO] >> ',
                        False,
                    )
                if reply:
                    cat_rec.parent_id = existing_rec.parent_id
                    cat_rec.closed_pt = existing_rec.closed_pt
                    cat_rec.open_rect = existing_rec.open_rect
                    hold_name = existing_rec.name
                    cat_db.delete_at(existing_idx)
                    break
            else:
                break

        print()
        creates_docs = dialog.get_yn(
            'Does your tool create documents? ( Y or N ) [YES] >> ', True
        )
        cat_rec.no_docs = not creates_docs
        cat_rec.many_docs = not cat_rec.no_docs
        print()

        if cat_rec.many_docs:
            print('Can your tool handle MORE THAN ONE document at a time? ')
            cat_rec.many_docs = dialog.get_yn(
                "If you don't know press RETURN. ( Y or N ) [NO] >> ", False
            )

        print()
        top, left, bottom, right = cat_rec.open_rect
        print('The stationery opening rectangle is defaulted to')
        print('%d, %d, %d, %d' % (left, top, right, bottom))
        print()
        if dialog.get_yn(
            'Do you wish to specify a different one? ( Y or N ) [NO] >> ', False
        ):
            left = dialog.get_num('left   >> ')
            top = dialog.get_num('top    >> ')
            right = dialog.get_num('right  >> ')
            bottom = dialog.get_num('bottom >> ')
            cat_rec.open_rect = (top, left, bottom, right)

        print()
        obj_name = dialog.read_line('Please enter the name of your tool. >> ')
        if len(obj_name) > 0 and ord(obj_name[0]) == CC_CLEAR:
            raise InstallAbort(1)
        obj_name = obj_name[:FMAX_STR_LEN]
        cat_rec.name = obj_name

        # SameName check
        while True:
            dup_idx, _dup_rec = cat_db.find_obj(name=obj_name, kinds={TOOL_KIND}, tool_id=-1)
            if dup_idx is None:
                break
            print()
            print('There already exists a tool with that name.')
            print()
            temp_name = dialog.read_line(
                'Please enter a new name (a [RETURN] will result in duplicate names). '
            )
            if len(temp_name) > 0 and ord(temp_name[0]) == CC_CLEAR:
                raise InstallAbort(1)
            if len(temp_name) == 0:
                break
            obj_name = temp_name[:FMAX_STR_LEN]
            cat_rec.name = obj_name

        print()

        # ---- Assignment ----
        cat_rec.obj_kind = TOOL_KIND
        size_blks, created_dtc = scan_tool_files(fs, cat_rec.tool_id)
        cat_rec.obj_size = size_blks
        cat_rec.created = created_dtc

        # ---- AddRecToCat ----
        try:
            cat_db.insert_rec(cat_rec.copy(), gen_id=True)
        except ValueError:
            error_check(2, 'AddCatRec')

        # ---- MakeLabel (validate {T<id>}obj exists BEFORE touching image!) ----
        saved_stdout = sys.stdout
        try:
            sys.stdout = open(os.devnull, 'w')
            obj_sfile = locate_tool_obj_sfile(fs, cat_rec.tool_id)
        finally:
            sys.stdout.close()
            sys.stdout = saved_stdout

        if obj_sfile is None:
            print('There appears to be a problem writing to the tool')
            print('object file label.  The problem may be that the')
            print('{T%d}obj file is not on the correct disk.' % cat_rec.tool_id)
            print()
            error_check(LABEL_ERROR, 'LabelIO')

        label_bytes = build_label_fmt_bytes(
            name=obj_name,
            no_docs=cat_rec.no_docs,
            many_docs=cat_rec.many_docs,
            open_rect=cat_rec.open_rect,
        )

        # ---- Stationery ----
        pad_idx, pad_rec = cat_db.find_obj(
            name=hold_name + ' Paper', kinds={DOC_PAD}, tool_id=cat_rec.tool_id
        )
        if pad_rec is not None and not cat_rec.no_docs:
            updated_pad = pad_rec.copy()
            updated_pad.no_docs = cat_rec.no_docs
            updated_pad.many_docs = cat_rec.many_docs
            updated_pad.open_rect = cat_rec.open_rect
            updated_pad.name = (obj_name + ' Paper')[:FMAX_STR_LEN]
            cat_db.update_at(pad_idx, updated_pad)
        elif not cat_rec.no_docs:
            new_pad = cat_rec.copy()
            new_pad.obj_kind = DOC_PAD
            new_pad.name = (obj_name + ' Paper')[:FMAX_STR_LEN]
            new_pad.obj_size = 0
            cat_db.insert_rec(new_pad, gen_id=True)
        elif pad_rec is not None:
            cat_db.delete_at(pad_idx)

        # ---- Commit {!CATALOG} and {T<id>}obj label to disk image ----
        new_cat_bytes = cat_db.to_bytes()
        try:
            commit_install_to_image(fs, new_cat_bytes, obj_sfile, label_bytes)
        except Exception as exc:
            sys.stderr.write('Error writing catalog/label to image: %s\n' % exc)
            error_check(3405, 'CloseCat')

        # ---- MakeIcon ----
        print()
        print('If the tool supports documents (e.g. LisaWrite) create a')
        print('design to appear on the document icon and store')
        print('this at character code 0 (zero) in the Font.')
        print()
        print('If the tool does not support documents (e.g. Calculator)')
        print('then have the icon created at character code 1 and its mask at')
        print('character code 2.')
        print()
        print('Then transfer the Font file to the same disk as the tool, ')
        print('and name it "{T<your tool #>}icon". (e.g. {T50}icon)')

        # ---- Conclude(TRUE) ----
        print()
        print('"%s" has been successfully installed in the Office System' % obj_name)
        print('and it will appear in the disk window associated with the device, %s.' % dev_display)
        print()
        return 0

    except InstallAbort as ab:
        return ab.exit_code
    except (EOFError, ValueError) as exc:
        sys.stderr.write('installtool.py: %s\n' % exc)
        return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
