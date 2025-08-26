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

"""Convenience wrapper exposing AutoML launcher helpers."""

from importlib import util
from pathlib import Path

_spec = util.spec_from_file_location("automl_launcher", Path(__file__).with_name("AutoML.py"))
_launcher = util.module_from_spec(_spec)
assert _spec and _spec.loader  # for type checkers
_spec.loader.exec_module(_launcher)

ensure_ghostscript = _launcher.ensure_ghostscript
GS_PATH = _launcher.GS_PATH
os = _launcher.os
subprocess = _launcher.subprocess
main = _launcher.main

__all__ = [
    "ensure_ghostscript",
    "GS_PATH",
    "os",
    "subprocess",
    "main",
]

if __name__ == "__main__":
    main()
