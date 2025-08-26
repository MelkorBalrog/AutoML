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
"""Lowercase launcher shim for tests."""

from __future__ import annotations

import importlib.util
import os
import subprocess
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "_automl_launcher", Path(__file__).with_name("AutoML.py")
)
_launcher = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_launcher)  # type: ignore[arg-type]

ensure_ghostscript = _launcher.ensure_ghostscript
GS_PATH = _launcher.GS_PATH

__all__ = ["ensure_ghostscript", "GS_PATH", "os", "subprocess"]
