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


def test_global_relation_not_duplicated(monkeypatch):
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    diag = repo.create_diagram("Governance Diagram")

    ai_data = {"nodes": [], "relations": ["Flow", "Assess"], "externals": {}}
    defs_data = {"Entities": {"nodes": [], "relations": ["Bar"], "externals": {}},
                 "Safety & AI Lifecycle": ai_data}
    monkeypatch.setattr(arch, "_toolbox_defs", lambda: defs_data)

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
        self.rel_frame = DummyWidget()
        self.toolbox_selector = DummyWidget()
        self.toolbox_var = types.SimpleNamespace(get=lambda: "", set=lambda v: None)
        self.relation_tools = relation_tools or []
        self._toolbox_frames = {}
        self.canvas = types.SimpleNamespace(master=DummyWidget())

    monkeypatch.setattr(arch.SysMLDiagramWindow, "__init__", fake_sysml_init)
    monkeypatch.setattr(arch, "draw_icon", lambda *a, **k: None)
    monkeypatch.setattr(arch.GovernanceDiagramWindow, "refresh_from_repository", lambda self: None)
    monkeypatch.setattr(arch.ttk, "Combobox", DummyWidget)
    monkeypatch.setattr(arch.ttk, "Frame", DummyWidget)
    monkeypatch.setattr(arch.ttk, "LabelFrame", DummyWidget)
    monkeypatch.setattr(arch.ttk, "Button", DummyWidget)

    win = GovernanceDiagramWindow(None, None, diagram_id=diag.diag_id)
    # Relation "Flow" should be removed from the category since it exists in the
    # global relation toolbox.
    assert ai_data["relations"] == ["Assess"]


def test_category_relations_deduplicated(monkeypatch):
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    diag = repo.create_diagram("Governance Diagram")

    defs_data = {
        "Artifacts": {
            "nodes": [],
            "relations": ["Approves"],
            "externals": {
                "Roles": {"nodes": [], "relations": ["Approves", "Manage"]},
                "Processes": {"nodes": [], "relations": ["Approves"]},
            },
        }
    }
    monkeypatch.setattr(arch, "_toolbox_defs", lambda: defs_data)

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
        self.canvas = types.SimpleNamespace(master=DummyWidget())

    monkeypatch.setattr(arch.SysMLDiagramWindow, "__init__", fake_sysml_init)
    monkeypatch.setattr(arch, "draw_icon", lambda *a, **k: None)
    monkeypatch.setattr(
        arch.GovernanceDiagramWindow, "refresh_from_repository", lambda self: None
    )
    monkeypatch.setattr(arch.ttk, "Combobox", DummyWidget)
    monkeypatch.setattr(arch.ttk, "Frame", DummyWidget)
    monkeypatch.setattr(arch.ttk, "LabelFrame", DummyWidget)
    monkeypatch.setattr(arch.ttk, "Button", DummyWidget)

    GovernanceDiagramWindow(None, None, diagram_id=diag.diag_id)
    art = defs_data["Artifacts"]
    assert art["relations"] == ["Approves"]
    assert art["externals"]["Roles"]["relations"] == ["Manage"]
    assert art["externals"]["Processes"]["relations"] == []


def test_governance_core_relations_deduplicated(monkeypatch):
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    diag = repo.create_diagram("Governance Diagram")

    defs_data = {
        "Governance Core": {
            "nodes": [],
            "relations": ["Propagate", "Propagate", "Re-use"],
            "externals": {
                "Artifacts": {"nodes": [], "relations": ["Propagate", "Re-use", "Re-use"]},
                "Entities": {"nodes": [], "relations": ["Propagate"]},
            },
        }
    }
    monkeypatch.setattr(arch, "_toolbox_defs", lambda: defs_data)

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
        self.canvas = types.SimpleNamespace(master=DummyWidget())

    monkeypatch.setattr(arch.SysMLDiagramWindow, "__init__", fake_sysml_init)
    monkeypatch.setattr(arch, "draw_icon", lambda *a, **k: None)
    monkeypatch.setattr(
        arch.GovernanceDiagramWindow, "refresh_from_repository", lambda self: None
    )
    monkeypatch.setattr(arch.ttk, "Combobox", DummyWidget)
    monkeypatch.setattr(arch.ttk, "Frame", DummyWidget)
    monkeypatch.setattr(arch.ttk, "LabelFrame", DummyWidget)
    monkeypatch.setattr(arch.ttk, "Button", DummyWidget)

    GovernanceDiagramWindow(None, None, diagram_id=diag.diag_id)
    core = defs_data["Governance Core"]
    assert core["relations"] == ["Propagate", "Re-use"]
    assert core["externals"]["Artifacts"]["relations"] == []
    assert core["externals"]["Entities"]["relations"] == []


def test_relations_deduplicated_across_categories(monkeypatch):
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    diag = repo.create_diagram("Governance Diagram")

    defs_data = {
        "First": {"nodes": [], "relations": ["Link"], "externals": {}},
        "Second": {"nodes": [], "relations": ["Link", "Trace"], "externals": {}},
    }
    monkeypatch.setattr(arch, "_toolbox_defs", lambda: defs_data)

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
        self.canvas = types.SimpleNamespace(master=DummyWidget())

    monkeypatch.setattr(arch.SysMLDiagramWindow, "__init__", fake_sysml_init)
    monkeypatch.setattr(arch, "draw_icon", lambda *a, **k: None)
    monkeypatch.setattr(
        arch.GovernanceDiagramWindow, "refresh_from_repository", lambda self: None
    )
    monkeypatch.setattr(arch.ttk, "Combobox", DummyWidget)
    monkeypatch.setattr(arch.ttk, "Frame", DummyWidget)
    monkeypatch.setattr(arch.ttk, "LabelFrame", DummyWidget)
    monkeypatch.setattr(arch.ttk, "Button", DummyWidget)

    GovernanceDiagramWindow(None, None, diagram_id=diag.diag_id)
    assert defs_data["First"]["relations"] == ["Link"]
    assert defs_data["Second"]["relations"] == ["Trace"]
