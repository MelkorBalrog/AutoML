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

"""Common fixtures for detachment regression tests."""

import os
import sys
import types
import tkinter as tk
import pytest

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "gui", "utils"))

from closable_notebook import ClosableNotebook
from mainappsrc.models.gsn import GSNNode, GSNDiagram


class DummyToolbox:
    """Minimal stand-in for :class:`SafetyManagementToolbox`."""

    def __init__(self) -> None:
        self.diagrams: dict[str, str] = {}


class DummyGSNDiagramWindow(tk.Frame):
    """Simplified GSN diagram tab used for detachment tests."""

    def __init__(self, master, app, diagram):
        super().__init__(master)
        self.app = app
        self.diagram = diagram
        self.zoom = 1.0

    def zoom_in(self) -> None:
        self.zoom *= 1.1


@pytest.fixture
def tk_root():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk not available")
    yield root
    root.destroy()


@pytest.fixture
def toolbox() -> DummyToolbox:
    return DummyToolbox()


@pytest.fixture
def gsn_diagram_window(tk_root, toolbox):
    node = GSNNode("Goal", "Goal")
    diagram = GSNDiagram(node)
    app = types.SimpleNamespace(safety_mgmt_toolbox=toolbox)
    win = DummyGSNDiagramWindow(tk_root, app, diagram)
    nb = ClosableNotebook(tk_root)
    nb.add(win, text="GSN")
    nb.update_idletasks()
    return nb, win
