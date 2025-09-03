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
"""Tests ensuring toolbox contents survive focus changes."""

import copy
import types
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[2]))

import gui.architecture as arch
from gui.architecture import GovernanceDiagramWindow
from mainappsrc.models.sysml.sysml_repository import SysMLRepository


class DummyWidget:
    def __init__(self, *_, **__):
        pass

    def pack(self, *_, **__):
        pass

    def pack_forget(self, *_, **__):
        pass

    def bind(self, *_, **__):
        pass

    def configure(self, *_, **__):
        pass

    def destroy(self, *_, **__):
        pass

    def after(self, *_, **__):
        pass


class TestToolboxFocusPersistence:
    """Grouped tests validating toolbox state after focus events."""

    def _init(self, repo):
        def fake_sysml_init(
            self,
            master,
            title,
            tools,
            diagram_id=None,
            app=None,
            history=None,
            relation_tools=None,
            tool_groups=None,
        ):
            self.app = app
            self.repo = repo
            self.diagram_id = diagram_id
            self.toolbox = DummyWidget()
            self.tools_frame = DummyWidget()
            self.rel_frame = DummyWidget()
            self.toolbox_selector = DummyWidget()
            self.toolbox_var = types.SimpleNamespace(get=lambda: "", set=lambda v: None)
            self.relation_tools = relation_tools or []
            self._toolbox_frames = {}
            self.canvas = types.SimpleNamespace(
                master=DummyWidget(), configure=lambda *a, **k: None
            )
            self._sync_to_repository = lambda: None

        return fake_sysml_init

    def test_relation_tools_survive_focus_out(self, monkeypatch):
        SysMLRepository._instance = None
        repo = SysMLRepository.get_instance()
        diag = repo.create_diagram("Governance Diagram")
        defs_data = {"Entities": {"nodes": [], "relations": ["Rel"], "externals": {}}}
        monkeypatch.setattr(arch, "_toolbox_defs", lambda: copy.deepcopy(defs_data))
        monkeypatch.setattr(arch.SysMLDiagramWindow, "__init__", self._init(repo))
        monkeypatch.setattr(arch, "draw_icon", lambda *a, **k: None)
        monkeypatch.setattr(
            arch.GovernanceDiagramWindow, "refresh_from_repository", lambda self, e=None: None
        )
        monkeypatch.setattr(arch.ttk, "Combobox", DummyWidget)
        monkeypatch.setattr(arch.ttk, "Frame", DummyWidget)
        monkeypatch.setattr(arch.ttk, "LabelFrame", DummyWidget)
        monkeypatch.setattr(arch.ttk, "Button", DummyWidget)

        win = GovernanceDiagramWindow(None, None, diagram_id=diag.diag_id)
        win.relation_tools = ["Rel"]
        win._rebuild_toolboxes()
        win._on_focus_out()
        win._rebuild_toolboxes()
        ents = win._frame_loaders["Entities"].__defaults__[0]
        assert ents["relations"] == ["Rel"]

    def test_focus_out_does_not_clear_state(self, monkeypatch):
        SysMLRepository._instance = None
        repo = SysMLRepository.get_instance()
        diag = repo.create_diagram("Governance Diagram")
        monkeypatch.setattr(arch.SysMLDiagramWindow, "__init__", self._init(repo))
        monkeypatch.setattr(arch.GovernanceDiagramWindow, "refresh_from_repository", lambda self, e=None: None)

        win = GovernanceDiagramWindow(None, None, diagram_id=diag.diag_id)
        win.relation_tools = ["Foo"]
        win._on_focus_out()
        assert win.relation_tools == ["Foo"]

