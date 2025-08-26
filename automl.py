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
"""Compatibility wrapper exposing launcher utilities under a stable module name."""

from importlib import util
from pathlib import Path

_spec = util.spec_from_file_location("automl_launcher", Path(__file__).with_name("AutoML.py"))
_launcher = util.module_from_spec(_spec)
_spec.loader.exec_module(_launcher)  # type: ignore[attr-defined]

GS_PATH = _launcher.GS_PATH
REQUIRED_PACKAGES = _launcher.REQUIRED_PACKAGES
memory_manager = _launcher.memory_manager
importlib = _launcher.importlib
subprocess = _launcher.subprocess
os = _launcher.os


def ensure_ghostscript() -> None:
    """Delegate to launcher while honoring patched globals."""
    _launcher.GS_PATH = GS_PATH
    _launcher.os = os
    _launcher.subprocess = subprocess
    _launcher.ensure_ghostscript()


def ensure_packages() -> None:
    """Delegate to launcher while honoring patched globals."""
    _launcher.REQUIRED_PACKAGES = REQUIRED_PACKAGES
    _launcher.importlib = importlib
    _launcher.subprocess = subprocess
    _launcher.memory_manager = memory_manager
    _launcher.ensure_packages()

__all__ = [
    "ensure_ghostscript",
    "ensure_packages",
    "GS_PATH",
    "REQUIRED_PACKAGES",
    "memory_manager",
    "importlib",
    "subprocess",
    "os",
]
