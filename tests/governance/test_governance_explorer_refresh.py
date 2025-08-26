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

import sys
from pathlib import Path
import types
from tkinter import simpledialog

sys.path.append(str(Path(__file__).resolve().parents[1]))

from mainappsrc.models.sysml.sysml_repository import SysMLRepository
from analysis.safety_management import SafetyManagementToolbox
from gui.safety_management_explorer import SafetyManagementExplorer


def test_new_diagram_refreshes_toolbox(monkeypatch):
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    toolbox = SafetyManagementToolbox()

    refreshed = {"called": False}
    def refresh_diagrams():
        refreshed["called"] = True

    app = types.SimpleNamespace(
        safety_mgmt_window=types.SimpleNamespace(refresh_diagrams=refresh_diagrams)
    )

    explorer = SafetyManagementExplorer.__new__(SafetyManagementExplorer)
    explorer.app = app
    explorer.toolbox = toolbox
    explorer.tree = types.SimpleNamespace(selection=lambda: ["root"])
    explorer.item_map = {"root": ("root", None)}
    explorer.populate = lambda: None

    monkeypatch.setattr(simpledialog, "askstring", lambda *a, **k: "Gov1")

    explorer.new_diagram()

    assert refreshed["called"], "toolbox not refreshed"
    assert "Gov1" in toolbox.list_diagrams()
