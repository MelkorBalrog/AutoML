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

from __future__ import annotations

"""Custom control widgets for the AutoML GUI.

The messagebox module is imported lazily to avoid circular import issues.  It
depends on high level widgets defined in :mod:`gui.__init__`, so importing it
at module import time would cause a partially initialised package when
``gui`` itself loads controls.  ``__getattr__`` performs a deferred import when
``messagebox`` is first requested.
"""


from types import ModuleType
import importlib

from . import button_utils, mac_button_style

__all__ = ["button_utils", "mac_button_style", "messagebox", "window_controllers"]


def __getattr__(name: str) -> ModuleType:
    """Dynamically import submodules on first access.

    Parameters
    ----------
    name:
        Attribute name being accessed.
    """

    if name == "messagebox":
        return importlib.import_module(f"{__name__}.messagebox")
    if name == "window_controllers":
        return importlib.import_module(f"{__name__}.window_controllers")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
