# Author: Miguel Marina <karel.capek.robotics@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 Capek System Safety & Robotic Solutions
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""Thin C API wrapper for core arithmetic services."""

from __future__ import annotations

import ctypes
from pathlib import Path
import subprocess

_LIB_NAME = "libcore_api.so"
_SRC_PATH = Path(__file__).with_suffix(".c")
_LIB_PATH = Path(__file__).with_name(_LIB_NAME)


def _build_library() -> None:
    """Compile the C source into a shared library if missing."""
    subprocess.check_call(
        ["gcc", "-shared", "-o", str(_LIB_PATH), "-fPIC", str(_SRC_PATH)]
    )


if not _LIB_PATH.exists():
    _build_library()

_lib = ctypes.CDLL(str(_LIB_PATH))
_lib.add.argtypes = (ctypes.c_int, ctypes.c_int)
_lib.add.restype = ctypes.c_int


def add(left: int, right: int) -> int:
    """Return the sum of two integers using the compiled C library."""
    return int(_lib.add(left, right))


__all__ = ["add"]
