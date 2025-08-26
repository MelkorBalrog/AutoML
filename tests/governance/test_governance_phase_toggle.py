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
import tkinter as tk
import sys
from pathlib import Path
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from mainappsrc.models.sysml.sysml_repository import SysMLRepository
from analysis.safety_management import SafetyManagementToolbox, GovernanceModule
from gui.architecture import GovernanceDiagramWindow, SysMLObject
from analysis.models import StpaDoc
from gui.stpa_window import StpaWindow


class DummyVar:
    def __init__(self):
        self.value = ""

    def set(self, val):
        self.value = val

    def get(self):
        return self.value


def test_open_governance_diagram_activates_phase():
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    diag = repo.create_diagram("Governance Diagram", name="Gov1")

    toolbox = SafetyManagementToolbox()
    toolbox.modules = [GovernanceModule(name="Phase1", diagrams=["Gov1"])]
    toolbox.diagrams = {"Gov1": diag.diag_id}

    app = types.SimpleNamespace(
        safety_mgmt_toolbox=toolbox,
        lifecycle_var=DummyVar(),
        refresh_tool_enablement_called=False,
    )

    def on_lifecycle_selected(_event=None):
        app.safety_mgmt_toolbox.set_active_module(app.lifecycle_var.get())
        app.refresh_tool_enablement_called = True

    app.on_lifecycle_selected = on_lifecycle_selected

    win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
    win.repo = repo
    win.diagram_id = diag.diag_id
    win.app = app

    GovernanceDiagramWindow._activate_parent_phase(win)

    assert toolbox.active_module == "Phase1"
    assert app.lifecycle_var.get() == "Phase1"
    assert app.refresh_tool_enablement_called


def test_open_governance_diagram_refreshes_tools():
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    diag = repo.create_diagram("Governance Diagram", name="GovRefresh")

    toolbox = SafetyManagementToolbox()
    toolbox.modules = [GovernanceModule(name="Phase1", diagrams=["GovRefresh"])]
    toolbox.diagrams = {"GovRefresh": diag.diag_id}

    calls = {"refresh": 0}

    class DummyVar:
        def __init__(self):
            self.val = ""

        def set(self, val):
            self.val = val

        def get(self):
            return self.val

    def on_lifecycle_selected():
        toolbox.set_active_module(app.lifecycle_var.get())

    def refresh_tool_enablement():
        calls["refresh"] += 1

    app = types.SimpleNamespace(
        safety_mgmt_toolbox=toolbox,
        lifecycle_var=DummyVar(),
        on_lifecycle_selected=on_lifecycle_selected,
        refresh_tool_enablement=refresh_tool_enablement,
    )

    win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
    win.repo = repo
    win.diagram_id = diag.diag_id
    win.app = app

    GovernanceDiagramWindow._activate_parent_phase(win)

    assert toolbox.active_module == "Phase1"
    assert calls["refresh"] == 1


def test_add_process_area_lists_scenario(monkeypatch):
    captured = {}

    def capture_dialog(self, parent, title, options):
        captured["options"] = options
        return types.SimpleNamespace(selection="")

    monkeypatch.setattr(GovernanceDiagramWindow, "_SelectDialog", capture_dialog)
    win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
    win.add_work_product()

    assert "Scenario" in captured["options"]


def test_added_work_product_respects_phase(monkeypatch):
    import sys

    PIL_stub = types.ModuleType("PIL")
    PIL_stub.Image = types.SimpleNamespace()
    PIL_stub.ImageTk = types.SimpleNamespace()
    PIL_stub.ImageDraw = types.SimpleNamespace()
    PIL_stub.ImageFont = types.SimpleNamespace()
    sys.modules.setdefault("PIL", PIL_stub)
    sys.modules.setdefault("PIL.Image", PIL_stub.Image)
    sys.modules.setdefault("PIL.ImageTk", PIL_stub.ImageTk)
    sys.modules.setdefault("PIL.ImageDraw", PIL_stub.ImageDraw)
    sys.modules.setdefault("PIL.ImageFont", PIL_stub.ImageFont)
    from AutoML import AutoMLApp
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    diag = repo.create_diagram("Governance Diagram", name="Gov2")

    toolbox = SafetyManagementToolbox()
    toolbox.modules = [
        GovernanceModule(name="P1"),
        GovernanceModule(name="P2", diagrams=["Gov2"]),
    ]
    toolbox.diagrams = {"Gov2": diag.diag_id}

    class DummyListbox:
        def __init__(self):
            self.items = []
            self.colors = []

        def get(self, *_):
            return self.items

        def insert(self, index, item):
            self.items.insert(index if isinstance(index, int) else len(self.items), item)

        def itemconfig(self, index, foreground="black"):
            self.colors.append(foreground)

    class DummyMenu:
        def __init__(self):
            self.state = None

        def entryconfig(self, _idx, state=tk.DISABLED):
            self.state = state

    class DummyVar:
        def __init__(self, value=""):
            self.value = value

        def get(self):
            return self.value

        def set(self, value):
            self.value = value

    app = AutoMLApp.__new__(AutoMLApp)
    lb = DummyListbox()
    menu = DummyMenu()
    app.tool_listboxes = {"Hazard & Threat Analysis": lb}
    app.tool_categories = {"Hazard & Threat Analysis": []}
    app.tool_actions = {}
    app.work_product_menus = {"HAZOP": [(menu, 0)]}
    app.enabled_work_products = set()
    app.enable_process_area = lambda area: None
    app.hazop_analysis = lambda: None
    app.tool_to_work_product = {
        info[1]: name for name, info in AutoMLApp.WORK_PRODUCT_INFO.items()
    }
    app.update_views = lambda: None
    app.refresh_tool_enablement = AutoMLApp.refresh_tool_enablement.__get__(
        app, AutoMLApp
    )
    app.enable_work_product = AutoMLApp.enable_work_product.__get__(
        app, AutoMLApp
    )
    app.on_lifecycle_selected = AutoMLApp.on_lifecycle_selected.__get__(
        app, AutoMLApp
    )
    app.lifecycle_var = DummyVar("P1")
    app.safety_mgmt_toolbox = toolbox
    toolbox.on_change = app.refresh_tool_enablement

    app.on_lifecycle_selected()

    win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
    win.repo = repo
    win.diagram_id = diag.diag_id
    win.objects = [
        SysMLObject(
            1,
            "System Boundary",
            0.0,
            0.0,
            width=200.0,
            height=150.0,
            properties={"name": "Hazard & Threat Analysis"},
        )
    ]
    win.sort_objects = lambda: None
    win._sync_to_repository = lambda: None
    win.redraw = lambda: None
    win.app = app

    class FakeDialog:
        def __init__(self, *args, **kwargs):
            self.selection = "HAZOP"

    monkeypatch.setattr(GovernanceDiagramWindow, "_SelectDialog", FakeDialog)

    win.add_work_product()
    assert menu.state == tk.DISABLED

    app.lifecycle_var.set("P2")
    app.on_lifecycle_selected()
    assert menu.state == tk.NORMAL


def test_work_product_disables_when_leaving_phase(monkeypatch):
    import sys

    PIL_stub = types.ModuleType("PIL")
    PIL_stub.Image = types.SimpleNamespace()
    PIL_stub.ImageTk = types.SimpleNamespace()
    PIL_stub.ImageDraw = types.SimpleNamespace()
    PIL_stub.ImageFont = types.SimpleNamespace()
    sys.modules.setdefault("PIL", PIL_stub)
    sys.modules.setdefault("PIL.Image", PIL_stub.Image)
    sys.modules.setdefault("PIL.ImageTk", PIL_stub.ImageTk)
    sys.modules.setdefault("PIL.ImageDraw", PIL_stub.ImageDraw)
    sys.modules.setdefault("PIL.ImageFont", PIL_stub.ImageFont)
    from AutoML import AutoMLApp
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    diag = repo.create_diagram("Governance Diagram", name="Gov3")

    toolbox = SafetyManagementToolbox()
    toolbox.modules = [
        GovernanceModule(name="P1"),
        GovernanceModule(name="P2", diagrams=["Gov3"]),
    ]
    toolbox.diagrams = {"Gov3": diag.diag_id}

    class DummyListbox:
        def __init__(self):
            self.items = []
            self.colors = []

        def get(self, *_):
            return self.items

        def insert(self, index, item):
            self.items.insert(index if isinstance(index, int) else len(self.items), item)

        def itemconfig(self, index, foreground="black"):
            self.colors.append(foreground)

    class DummyMenu:
        def __init__(self):
            self.state = None

        def entryconfig(self, _idx, state=tk.DISABLED):
            self.state = state

    class DummyVar:
        def __init__(self, value=""):
            self.value = value

        def get(self):
            return self.value

        def set(self, value):
            self.value = value

    app = AutoMLApp.__new__(AutoMLApp)
    lb = DummyListbox()
    menu = DummyMenu()
    app.tool_listboxes = {"Hazard & Threat Analysis": lb}
    app.tool_categories = {"Hazard & Threat Analysis": []}
    app.tool_actions = {}
    app.work_product_menus = {"HAZOP": [(menu, 0)]}
    app.enabled_work_products = set()
    app.enable_process_area = lambda area: None
    app.hazop_analysis = lambda: None
    app.tool_to_work_product = {
        info[1]: name for name, info in AutoMLApp.WORK_PRODUCT_INFO.items()
    }
    app.update_views = lambda: None
    app.refresh_tool_enablement = AutoMLApp.refresh_tool_enablement.__get__(
        app, AutoMLApp
    )
    app.enable_work_product = AutoMLApp.enable_work_product.__get__(
        app, AutoMLApp
    )
    app.on_lifecycle_selected = AutoMLApp.on_lifecycle_selected.__get__(
        app, AutoMLApp
    )
    app.lifecycle_var = DummyVar("P2")
    app.safety_mgmt_toolbox = toolbox
    toolbox.on_change = app.refresh_tool_enablement

    app.on_lifecycle_selected()

    win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
    win.repo = repo
    win.diagram_id = diag.diag_id
    win.objects = [
        SysMLObject(
            1,
            "System Boundary",
            0.0,
            0.0,
            width=200.0,
            height=150.0,
            properties={"name": "Hazard & Threat Analysis"},
        )
    ]
    win.sort_objects = lambda: None
    win._sync_to_repository = lambda: None
    win.redraw = lambda: None
    win.app = app

    class FakeDialog:
        def __init__(self, *args, **kwargs):
            self.selection = "HAZOP"

    monkeypatch.setattr(GovernanceDiagramWindow, "_SelectDialog", FakeDialog)

    win.add_work_product()
    assert menu.state == tk.NORMAL


@pytest.mark.parametrize(
    "analysis,parent",
    [
        ("FTA", None),
        ("Threat Analysis", "Qualitative Analysis"),
        ("FI2TC", "Qualitative Analysis"),
        ("TC2FI", "Qualitative Analysis"),
        ("FMEA", "Qualitative Analysis"),
        ("FMEDA", "Quantitative Analysis"),
        ("Causal Bayesian Network Analysis", "Quantitative Analysis"),
        ("Scenario Library", None),
        ("ODD", "Scenario Library"),
        ("Safety & Security Case", "GSN"),
        ("GSN Argumentation", "GSN"),
    ],
)
def test_work_product_group_activation(analysis, parent, monkeypatch):
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    diag = repo.create_diagram("Governance Diagram", name="GovX")

    toolbox = SafetyManagementToolbox()
    toolbox.modules = [
        GovernanceModule(name="P1"),
        GovernanceModule(name="P2", diagrams=["GovX"]),
    ]
    toolbox.diagrams = {"GovX": diag.diag_id}

    from AutoML import AutoMLApp

    class DummyListbox:
        def __init__(self):
            self.items = []
            self.item_colors = {}

        def get(self, *_):
            return self.items

        def insert(self, index, item):
            self.items.insert(index if isinstance(index, int) else len(self.items), item)

        def itemconfig(self, index, foreground="black"):
            try:
                item = self.items[index]
            except IndexError:
                return
            self.item_colors[item] = foreground

    class DummyMenu:
        def __init__(self):
            self.state = None

        def entryconfig(self, _idx, state=tk.DISABLED):
            self.state = state

    class DummyVar:
        def __init__(self, value=""):
            self.value = value

        def get(self):
            return self.value

        def set(self, value):
            self.value = value

    app = AutoMLApp.__new__(AutoMLApp)
    lb = DummyListbox()
    menu = DummyMenu()
    area = AutoMLApp.WORK_PRODUCT_INFO[analysis][0]
    app.tool_listboxes = {area: lb}
    app.tool_categories = {area: []}
    app.tool_actions = {}
    app.work_product_menus = {analysis: [(menu, 0)]}
    parent_menu = None
    if parent:
        parent_menu = DummyMenu()
        app.work_product_menus[parent] = [(parent_menu, 0)]
        pinfo = AutoMLApp.WORK_PRODUCT_INFO[parent]
        setattr(app, pinfo[2], lambda: None)

    info = AutoMLApp.WORK_PRODUCT_INFO[analysis]
    setattr(app, info[2], lambda: None)

    app.enabled_work_products = set()
    app.enable_process_area = lambda area: None
    app.tool_to_work_product = {
        info[1]: name for name, info in AutoMLApp.WORK_PRODUCT_INFO.items()
    }
    app.update_views = lambda: None
    app.refresh_tool_enablement = AutoMLApp.refresh_tool_enablement.__get__(
        app, AutoMLApp
    )
    app.enable_work_product = AutoMLApp.enable_work_product.__get__(
        app, AutoMLApp
    )
    app.on_lifecycle_selected = AutoMLApp.on_lifecycle_selected.__get__(
        app, AutoMLApp
    )
    app.lifecycle_var = DummyVar("P1")
    app.safety_mgmt_toolbox = toolbox
    toolbox.on_change = app.refresh_tool_enablement

    app.on_lifecycle_selected()

    win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
    win.repo = repo
    win.diagram_id = diag.diag_id
    win.objects = [
        SysMLObject(
            1,
            "System Boundary",
            0.0,
            0.0,
            width=200.0,
            height=150.0,
            properties={"name": "Safety Analysis"},
        ),
        SysMLObject(
            2,
            "System Boundary",
            0.0,
            0.0,
            width=200.0,
            height=150.0,
            properties={"name": "Hazard & Threat Analysis"},
        ),
        SysMLObject(
            3,
            "System Boundary",
            0.0,
            0.0,
            width=200.0,
            height=150.0,
            properties={"name": "Scenario"},
        ),
        SysMLObject(
            4,
            "System Boundary",
            0.0,
            0.0,
            width=200.0,
            height=150.0,
            properties={"name": "Safety & Security Management"},
        ),
    ]
    win.sort_objects = lambda: None
    win._sync_to_repository = lambda: None
    win.redraw = lambda: None
    win.app = app

    class FakeDialog:
        def __init__(self, *args, **kwargs):
            self.selection = analysis

    monkeypatch.setattr(GovernanceDiagramWindow, "_SelectDialog", FakeDialog)

    win.add_work_product()

    tool_name = AutoMLApp.WORK_PRODUCT_INFO[analysis][1]
    assert menu.state == tk.DISABLED
    assert lb.item_colors.get(tool_name) == "gray"
    if parent_menu:
        assert parent_menu.state == tk.DISABLED

    app.lifecycle_var.set("P2")
    app.on_lifecycle_selected()
    assert menu.state == tk.NORMAL
    assert lb.item_colors.get(tool_name) == "black"
    if parent_menu:
        assert parent_menu.state == tk.NORMAL


def test_open_diagram_updates_phase_combobox():
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    diag = repo.create_diagram("Governance Diagram", name="Gov4")

    toolbox = SafetyManagementToolbox()
    toolbox.modules = [GovernanceModule(name="P1", diagrams=["Gov4"])]
    toolbox.diagrams = {"Gov4": diag.diag_id}

    class DummyVar:
        def __init__(self, value=""):
            self.value = value

        def get(self):
            return self.value

        def set(self, value):
            self.value = value

    app = types.SimpleNamespace(
        safety_mgmt_toolbox=toolbox,
        lifecycle_var=DummyVar(),
        refresh_tool_enablement=lambda: None,
    )

    def on_lifecycle_selected():
        toolbox.set_active_module(app.lifecycle_var.get())

    app.on_lifecycle_selected = on_lifecycle_selected

    smw = types.SimpleNamespace(phase_var=DummyVar(), refresh_diagrams=lambda: None)
    app.safety_mgmt_window = smw

    win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
    win.repo = repo
    win.diagram_id = diag.diag_id
    win.app = app

    win._activate_parent_phase()

    assert app.lifecycle_var.get() == "P1"
    assert smw.phase_var.get() == "P1"


def test_select_document_updates_phase():
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    toolbox = SafetyManagementToolbox()
    toolbox.doc_phases = {"STPA": {"Doc1": "P1"}}

    class DummyVar2:
        def __init__(self, value=""):
            self.value = value

        def get(self):
            return self.value

        def set(self, value):
            self.value = value

    app = types.SimpleNamespace(
        safety_mgmt_toolbox=toolbox,
        lifecycle_var=DummyVar2(),
        refresh_tool_enablement=lambda: None,
    )

    def on_lifecycle_selected():
        toolbox.set_active_module(app.lifecycle_var.get())

    app.on_lifecycle_selected = on_lifecycle_selected
    smw = types.SimpleNamespace(phase_var=DummyVar2(), refresh_diagrams=lambda: None)
    app.safety_mgmt_window = smw
    app.stpa_docs = [StpaDoc("Doc1", "", [])]
    app.active_stpa = None
    app.stpa_entries = []

    win = StpaWindow.__new__(StpaWindow)
    win.app = app
    win.doc_var = DummyVar2("Doc1")
    win.diag_lbl = types.SimpleNamespace(config=lambda **kwargs: None)
    win.refresh = lambda: None

    win.select_doc()

    assert app.lifecycle_var.get() == "P1"
    assert smw.phase_var.get() == "P1"
