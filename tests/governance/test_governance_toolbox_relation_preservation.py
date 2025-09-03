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

import copy
import types
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import gui.architecture as arch
from gui.architecture import GovernanceDiagramWindow
from mainappsrc.models.sysml.sysml_repository import SysMLRepository


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


class TestRelationRetention:
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
            self.destroy = lambda: None

        return fake_sysml_init

    def test_global_relations_retained(self, monkeypatch):
        SysMLRepository._instance = None
        repo = SysMLRepository.get_instance()
        diag = repo.create_diagram("Governance Diagram")

        ai_data = {"nodes": [], "relations": ["Flow", "Assess"], "externals": {}}
        defs_data = {
            "Entities": {"nodes": [], "relations": ["Bar"], "externals": {}},
            "Safety & AI Lifecycle": ai_data,
        }
        monkeypatch.setattr(arch, "_toolbox_defs", lambda: copy.deepcopy(defs_data))

        monkeypatch.setattr(arch.SysMLDiagramWindow, "__init__", self._init(repo))
        monkeypatch.setattr(arch, "draw_icon", lambda *a, **k: None)
        monkeypatch.setattr(
            arch.GovernanceDiagramWindow, "refresh_from_repository", lambda self: None
        )
        monkeypatch.setattr(arch.ttk, "Combobox", DummyWidget)
        monkeypatch.setattr(arch.ttk, "Frame", DummyWidget)
        monkeypatch.setattr(arch.ttk, "LabelFrame", DummyWidget)
        monkeypatch.setattr(arch.ttk, "Button", DummyWidget)

        win = GovernanceDiagramWindow(None, None, diagram_id=diag.diag_id)
        win.relation_tools = ["Flow"]
        win._rebuild_toolboxes()
        ai_copy = win._frame_loaders["Safety & AI Lifecycle"].__defaults__[0]
        assert ai_copy["relations"] == ["Flow", "Assess"]

    def test_governance_core_keeps_global_relations(self, monkeypatch):
        SysMLRepository._instance = None
        repo = SysMLRepository.get_instance()
        diag = repo.create_diagram("Governance Diagram")

        defs_data = {
            "Entities": {"nodes": [], "relations": ["Trace"], "externals": {}},
        }
        monkeypatch.setattr(arch, "_toolbox_defs", lambda: copy.deepcopy(defs_data))
        monkeypatch.setattr(arch, "GOV_CORE_NODES", ["dummy"])
        monkeypatch.setattr(arch, "_relations_for", lambda nodes: ["Trace"])
        monkeypatch.setattr(
            arch,
            "_external_relations_for",
            lambda nodes: {"Entities": {"nodes": [], "relations": ["Trace"]}},
        )

        monkeypatch.setattr(arch.SysMLDiagramWindow, "__init__", self._init(repo))
        monkeypatch.setattr(arch, "draw_icon", lambda *a, **k: None)
        monkeypatch.setattr(
            arch.GovernanceDiagramWindow, "refresh_from_repository", lambda self: None
        )
        monkeypatch.setattr(arch.ttk, "Combobox", DummyWidget)
        monkeypatch.setattr(arch.ttk, "Frame", DummyWidget)
        monkeypatch.setattr(arch.ttk, "LabelFrame", DummyWidget)
        monkeypatch.setattr(arch.ttk, "Button", DummyWidget)

        win = GovernanceDiagramWindow(None, None, diagram_id=diag.diag_id)
        win.relation_tools = ["Trace"]
        win._rebuild_toolboxes()
        entities = win._frame_loaders["Entities"].__defaults__[0]
        core = win._frame_loaders["Governance Core"].__defaults__[0]
        assert entities["relations"] == ["Trace"]
        assert core["relations"] == ["Trace"]
        assert core["externals"]["Entities"]["relations"] == ["Trace"]


class TestCategoryPreservation:
    def _init(self, repo):
        def fake_sysml_init(
            self,
            master,
            title,
            tools,
            diagram_id=None,
            app=None,
            history=None,
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
            self._toolbox_frames = {}
            self.canvas = types.SimpleNamespace(
                master=DummyWidget(), configure=lambda *a, **k: None
            )

        return fake_sysml_init

    def test_category_relations_preserved(self, monkeypatch):
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
        monkeypatch.setattr(arch, "_toolbox_defs", lambda: copy.deepcopy(defs_data))
        monkeypatch.setattr(arch, "GOV_CORE_NODES", [])

        monkeypatch.setattr(arch.SysMLDiagramWindow, "__init__", self._init(repo))
        monkeypatch.setattr(arch, "draw_icon", lambda *a, **k: None)
        monkeypatch.setattr(
            arch.GovernanceDiagramWindow, "refresh_from_repository", lambda self: None
        )
        monkeypatch.setattr(arch.ttk, "Combobox", DummyWidget)
        monkeypatch.setattr(arch.ttk, "Frame", DummyWidget)
        monkeypatch.setattr(arch.ttk, "LabelFrame", DummyWidget)
        monkeypatch.setattr(arch.ttk, "Button", DummyWidget)

        win = GovernanceDiagramWindow(None, None, diagram_id=diag.diag_id)
        art = win._frame_loaders["Artifacts"].__defaults__[0]
        assert art["relations"] == ["Approves"]
        assert art["externals"]["Roles"]["relations"] == ["Approves", "Manage"]
        assert art["externals"]["Processes"]["relations"] == ["Approves"]

    def test_governance_core_relations_preserved(self, monkeypatch):
        SysMLRepository._instance = None
        repo = SysMLRepository.get_instance()
        diag = repo.create_diagram("Governance Diagram")
        monkeypatch.setattr(arch, "_toolbox_defs", lambda: {})
        monkeypatch.setattr(arch, "GOV_CORE_NODES", ["dummy"])
        monkeypatch.setattr(
            arch, "_relations_for", lambda nodes: ["Propagate", "Propagate", "Re-use"]
        )
        monkeypatch.setattr(
            arch,
            "_external_relations_for",
            lambda nodes: {
                "Artifacts": {"nodes": [], "relations": ["Propagate", "Re-use", "Re-use"]},
                "Entities": {"nodes": [], "relations": ["Propagate"]},
            },
        )

        monkeypatch.setattr(arch.SysMLDiagramWindow, "__init__", self._init(repo))
        monkeypatch.setattr(arch, "draw_icon", lambda *a, **k: None)
        monkeypatch.setattr(
            arch.GovernanceDiagramWindow, "refresh_from_repository", lambda self: None
        )
        monkeypatch.setattr(arch.ttk, "Combobox", DummyWidget)
        monkeypatch.setattr(arch.ttk, "Frame", DummyWidget)
        monkeypatch.setattr(arch.ttk, "LabelFrame", DummyWidget)
        monkeypatch.setattr(arch.ttk, "Button", DummyWidget)

        win = GovernanceDiagramWindow(None, None, diagram_id=diag.diag_id)
        core = win._frame_loaders["Governance Core"].__defaults__[0]
        assert core["relations"] == ["Propagate", "Propagate", "Re-use"]
        assert core["externals"]["Artifacts"]["relations"] == ["Propagate", "Re-use", "Re-use"]
        assert core["externals"]["Entities"]["relations"] == ["Propagate"]


class TestCrossCategoryRetention:
    def _init(self, repo):
        def fake_sysml_init(
            self,
            master,
            title,
            tools,
            diagram_id=None,
            app=None,
            history=None,
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
            self._toolbox_frames = {}
            self.canvas = types.SimpleNamespace(
                master=DummyWidget(), configure=lambda *a, **k: None
            )

        return fake_sysml_init

    def test_relations_preserved_across_categories(self, monkeypatch):
        SysMLRepository._instance = None
        repo = SysMLRepository.get_instance()
        diag = repo.create_diagram("Governance Diagram")

        defs_data = {
            "First": {"nodes": [], "relations": ["Link"], "externals": {}},
            "Second": {"nodes": [], "relations": ["Link", "Trace"], "externals": {}},
        }
        monkeypatch.setattr(arch, "_toolbox_defs", lambda: copy.deepcopy(defs_data))
        monkeypatch.setattr(arch, "GOV_CORE_NODES", [])
        monkeypatch.setattr(arch, "_relations_for", lambda nodes: [])
        monkeypatch.setattr(arch, "_external_relations_for", lambda nodes: {})

        monkeypatch.setattr(arch.SysMLDiagramWindow, "__init__", self._init(repo))
        monkeypatch.setattr(arch, "draw_icon", lambda *a, **k: None)
        monkeypatch.setattr(
            arch.GovernanceDiagramWindow, "refresh_from_repository", lambda self: None
        )
        monkeypatch.setattr(arch.ttk, "Combobox", DummyWidget)
        monkeypatch.setattr(arch.ttk, "Frame", DummyWidget)
        monkeypatch.setattr(arch.ttk, "LabelFrame", DummyWidget)
        monkeypatch.setattr(arch.ttk, "Button", DummyWidget)

        win = GovernanceDiagramWindow(None, None, diagram_id=diag.diag_id)
        first = win._frame_loaders["First"].__defaults__[0]
        second = win._frame_loaders["Second"].__defaults__[0]
        assert first["relations"] == ["Link"]
        assert second["relations"] == ["Link", "Trace"]

    def test_governance_core_does_not_prune_categories(self, monkeypatch):
        SysMLRepository._instance = None
        repo = SysMLRepository.get_instance()
        diag = repo.create_diagram("Governance Diagram")

        defs_data = {
            "Entities": {"nodes": [], "relations": ["Link"], "externals": {}},
        }
        monkeypatch.setattr(arch, "_toolbox_defs", lambda: copy.deepcopy(defs_data))
        monkeypatch.setattr(arch, "GOV_CORE_NODES", ["dummy"])
        monkeypatch.setattr(arch, "_relations_for", lambda nodes: ["Link", "Trace"])
        monkeypatch.setattr(arch, "_external_relations_for", lambda nodes: {})

        monkeypatch.setattr(arch.SysMLDiagramWindow, "__init__", self._init(repo))
        monkeypatch.setattr(arch, "draw_icon", lambda *a, **k: None)
        monkeypatch.setattr(
            arch.GovernanceDiagramWindow, "refresh_from_repository", lambda self: None
        )
        monkeypatch.setattr(arch.ttk, "Combobox", DummyWidget)
        monkeypatch.setattr(arch.ttk, "Frame", DummyWidget)
        monkeypatch.setattr(arch.ttk, "LabelFrame", DummyWidget)
        monkeypatch.setattr(arch.ttk, "Button", DummyWidget)

        win = GovernanceDiagramWindow(None, None, diagram_id=diag.diag_id)
        entities = win._frame_loaders["Entities"].__defaults__[0]
        core = win._frame_loaders["Governance Core"].__defaults__[0]
        assert entities["relations"] == ["Link"]
        assert core["relations"] == ["Link", "Trace"]


class TestGovernanceCorePersistence:
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
            self._toolbox_frames = {}
            self.canvas = types.SimpleNamespace(
                master=DummyWidget(), configure=lambda *a, **k: None
            )

        return fake_sysml_init

    def test_governance_core_consistent_across_windows(self, monkeypatch):
        SysMLRepository._instance = None
        repo = SysMLRepository.get_instance()
        diag = repo.create_diagram("Governance Diagram")

        monkeypatch.setattr(arch.SysMLDiagramWindow, "__init__", self._init(repo))
        monkeypatch.setattr(arch, "draw_icon", lambda *a, **k: None)
        monkeypatch.setattr(
            arch.GovernanceDiagramWindow, "refresh_from_repository", lambda self: None
        )
        monkeypatch.setattr(arch.ttk, "Combobox", DummyWidget)
        monkeypatch.setattr(arch.ttk, "Frame", DummyWidget)
        monkeypatch.setattr(arch.ttk, "LabelFrame", DummyWidget)
        monkeypatch.setattr(arch.ttk, "Button", DummyWidget)

        baseline = arch._toolbox_defs()["Governance Core"]["relations"].copy()
        GovernanceDiagramWindow(None, None, diagram_id=diag.diag_id)
        after_first = arch._toolbox_defs()["Governance Core"]["relations"].copy()
        GovernanceDiagramWindow(None, None, diagram_id=diag.diag_id)
        after_second = arch._toolbox_defs()["Governance Core"]["relations"].copy()

        assert baseline == after_first == after_second

    def test_core_survives_global_filters_between_windows(self, monkeypatch):
        SysMLRepository._instance = None
        repo = SysMLRepository.get_instance()
        diag = repo.create_diagram("Governance Diagram")

        defs_template = {
            "Entities": {"nodes": [], "relations": ["Trace"], "externals": {}},
        }

        monkeypatch.setattr(
            arch, "_toolbox_defs", lambda: copy.deepcopy(defs_template)
        )
        monkeypatch.setattr(arch, "GOV_CORE_NODES", ["dummy"])
        monkeypatch.setattr(arch, "_relations_for", lambda nodes: ["Link", "Trace"])
        monkeypatch.setattr(
            arch,
            "_external_relations_for",
            lambda nodes: {"Entities": {"nodes": [], "relations": ["Trace"]}},
        )
        monkeypatch.setattr(arch.SysMLDiagramWindow, "__init__", self._init(repo))
        monkeypatch.setattr(arch, "draw_icon", lambda *a, **k: None)
        monkeypatch.setattr(
            arch.GovernanceDiagramWindow, "refresh_from_repository", lambda self: None
        )
        monkeypatch.setattr(arch.ttk, "Combobox", DummyWidget)
        monkeypatch.setattr(arch.ttk, "Frame", DummyWidget)
        monkeypatch.setattr(arch.ttk, "LabelFrame", DummyWidget)
        monkeypatch.setattr(arch.ttk, "Button", DummyWidget)

        first = GovernanceDiagramWindow(None, None, diagram_id=diag.diag_id)
        first.relation_tools = ["Trace"]
        first._rebuild_toolboxes()

        second = GovernanceDiagramWindow(None, None, diagram_id=diag.diag_id)
        second.relation_tools = []
        second._rebuild_toolboxes()

        core = second._frame_loaders["Governance Core"].__defaults__[0]
        assert core["relations"] == ["Link", "Trace"]

    def test_core_survives_non_governance_window(self, monkeypatch):
        SysMLRepository._instance = None
        repo = SysMLRepository.get_instance()
        gov = repo.create_diagram("Governance Diagram")
        other = repo.create_diagram("Block Definition Diagram")

        monkeypatch.setattr(arch.SysMLDiagramWindow, "__init__", self._init(repo))
        monkeypatch.setattr(arch, "draw_icon", lambda *a, **k: None)
        monkeypatch.setattr(
            arch.GovernanceDiagramWindow, "refresh_from_repository", lambda self: None
        )
        monkeypatch.setattr(arch.ttk, "Combobox", DummyWidget)
        monkeypatch.setattr(arch.ttk, "Frame", DummyWidget)
        monkeypatch.setattr(arch.ttk, "LabelFrame", DummyWidget)
        monkeypatch.setattr(arch.ttk, "Button", DummyWidget)

        arch.SysMLDiagramWindow(None, None, None, diagram_id=other.diag_id)

        win = GovernanceDiagramWindow(None, None, diagram_id=gov.diag_id)
        core = win._frame_loaders["Governance Core"].__defaults__[0]
        template = arch._core_toolbox_template()
        assert core["relations"] == template["relations"]
        assert core["externals"] == template["externals"]


class TestNonCoreCategoryPersistence:
    def _init(self, repo):
        def fake_sysml_init(
            self,
            master,
            title,
            tools,
            diagram_id=None,
            app=None,
            history=None,
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
            self._toolbox_frames = {}
            self.canvas = types.SimpleNamespace(
                master=DummyWidget(), configure=lambda *a, **k: None
            )

        return fake_sysml_init

    def test_non_core_relations_persist_across_rebuilds(self, monkeypatch):
        SysMLRepository._instance = None
        repo = SysMLRepository.get_instance()
        diag = repo.create_diagram("Governance Diagram")

        defs_template = {
            "Entities": {"nodes": [], "relations": ["Link"], "externals": {}}
        }

        monkeypatch.setattr(arch, "_toolbox_defs", lambda: copy.deepcopy(defs_template))
        monkeypatch.setattr(arch, "GOV_CORE_NODES", ["dummy"])
        monkeypatch.setattr(arch, "_relations_for", lambda nodes: ["Link", "Trace"])
        monkeypatch.setattr(arch, "_external_relations_for", lambda nodes: {})

        monkeypatch.setattr(arch.SysMLDiagramWindow, "__init__", self._init(repo))
        monkeypatch.setattr(arch, "draw_icon", lambda *a, **k: None)
        monkeypatch.setattr(
            arch.GovernanceDiagramWindow, "refresh_from_repository", lambda self: None
        )
        monkeypatch.setattr(arch.ttk, "Combobox", DummyWidget)
        monkeypatch.setattr(arch.ttk, "Frame", DummyWidget)
        monkeypatch.setattr(arch.ttk, "LabelFrame", DummyWidget)
        monkeypatch.setattr(arch.ttk, "Button", DummyWidget)

        win = GovernanceDiagramWindow(None, None, diagram_id=diag.diag_id)
        entities1 = win._frame_loaders["Entities"].__defaults__[0]
        assert entities1["relations"] == ["Link"]
        win._rebuild_toolboxes()
        entities2 = win._frame_loaders["Entities"].__defaults__[0]
        assert entities2["relations"] == ["Link"]
        win._rebuild_toolboxes()
        entities3 = win._frame_loaders["Entities"].__defaults__[0]
        assert entities3["relations"] == ["Link"]


