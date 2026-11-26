"""Assembled Lisa Pascal Front-End Compiler class combining all relevant modules."""

from __future__ import annotations

from frontend_base import PascalCompilerBase
from pas_body import BodyMixin
from pas_dbg import DbgMixin
from pas_decl import DeclMixin
from pas_dump import DumpMixin
from pas_init import InitMixin
from pas_misc import MiscMixin
from pas_opt import OptMixin


class PascalCompiler(
    InitMixin,
    MiscMixin,
    DeclMixin,
    BodyMixin,
    OptMixin,
    DumpMixin,
    DbgMixin,
    PascalCompilerBase,
):
    """Lisa Pascal Compiler Front End in Python.

    Combines pass-1 initialization, source scanning, symbol-table management,
    declaration and statement/expression parsing, register/CSE optimization,
    binary I-code emission, and debug symbol dumping onto ``PascalCompilerBase``.
    """
