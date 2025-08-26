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

import types
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import gui.architecture as arch
from gui.architecture import GovernanceDiagramWindow
from mainappsrc.models.sysml.sysml_repository import SysMLRepository


def test_governance_toolbox_excludes_fork_and_join(monkeypatch):
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    diag = repo.create_diagram("Governance Diagram")

    class DummyWidget:
        def __init__(self, *a, **k):
            pass

        def pack(self, *a, **k):
            pass

        def pack_forget(self, *a, **k):
            pass

        def bind(self, *a, **k):
            pass

        def configure(self, *a, **k):
            pass

        def destroy(self, *a, **k):
            pass

    def fake_sysml_init(self, master, title, tools, diagram_id=None, app=None, history=None, relation_tools=None, tool_groups=None):
        self.app = app
        self.repo = repo
        self.diagram_id = diagram_id
        self.toolbox = DummyWidget()
        self.tools_frame = DummyWidget()
        canvas_master = DummyWidget()
        self.canvas = types.SimpleNamespace(master=canvas_master)
        # Create dummy buttons for each tool
        self.tool_buttons = {name: DummyWidget() for name in tools}

    monkeypatch.setattr(arch.SysMLDiagramWindow, "__init__", fake_sysml_init)
    monkeypatch.setattr(arch, "draw_icon", lambda *a, **k: None)
    monkeypatch.setattr(arch.GovernanceDiagramWindow, "refresh_from_repository", lambda self: None)
    monkeypatch.setattr(arch.ttk, "Combobox", DummyWidget)
    monkeypatch.setattr(arch.ttk, "Frame", DummyWidget)
    monkeypatch.setattr(arch.ttk, "LabelFrame", DummyWidget)
    monkeypatch.setattr(arch.ttk, "Button", DummyWidget)

    win = GovernanceDiagramWindow(None, None, diagram_id=diag.diag_id)
    assert "Fork" not in win.tool_buttons
    assert "Join" not in win.tool_buttons
