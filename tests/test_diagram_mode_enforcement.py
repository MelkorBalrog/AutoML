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

import sys, types, pathlib

# Ensure repository root is on path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

# Stub PIL modules to allow importing AutoML without Pillow
sys.modules.setdefault("PIL", types.ModuleType("PIL"))
sys.modules.setdefault("PIL.Image", types.ModuleType("PIL.Image"))
sys.modules.setdefault("PIL.ImageDraw", types.ModuleType("PIL.ImageDraw"))
sys.modules.setdefault("PIL.ImageFont", types.ModuleType("PIL.ImageFont"))
sys.modules.setdefault("PIL.ImageTk", types.ModuleType("PIL.ImageTk"))

import importlib

AutoML = importlib.import_module("mainappsrc.core.automl_core")
AutoMLApp = AutoML.AutoMLApp
FaultTreeNode = AutoML.FaultTreeNode
import mainappsrc.core.page_diagram as page_module
PageDiagram = page_module.PageDiagram

import pytest

class DummyMenu:
    last = None

    def __init__(self, *args, **kwargs):
        DummyMenu.last = self
        self.entries = []

    def add_command(self, label, command=None, **kwargs):
        self.entries.append(label)

    def add_separator(self):
        pass

    def tk_popup(self, x, y):
        pass

    def entryconfig(self, index, state):
        # Used in _update_analysis_menus tests
        if len(self.entries) <= index:
            self.entries.extend([None] * (index - len(self.entries) + 1))
        self.entries[index] = (self.entries[index], state)


def _make_page_diagram(mode):
    app = types.SimpleNamespace(root=None, project_properties={})

    class Canvas:
        def __init__(self, mode):
            self.diagram_mode = mode

        def canvasx(self, v):
            return v

        def canvasy(self, v):
            return v

        def bind(self, *a, **k):
            pass

    canvas = Canvas(mode)
    root = FaultTreeNode("", "Top Event")
    root.x = root.y = 0
    page_module.tkFont = types.SimpleNamespace(Font=lambda *a, **k: object())
    page_module.fta_drawing_helper = types.SimpleNamespace()
    return PageDiagram(app, root, canvas)


def test_context_menu_cta(monkeypatch):
    pd = _make_page_diagram("CTA")
    monkeypatch.setattr(AutoML.tk, "Menu", DummyMenu)
    event = types.SimpleNamespace(x=0, y=0, x_root=0, y_root=0)
    pd.show_context_menu(event)
    entries = DummyMenu.last.entries
    assert "Add Triggering Condition" in entries
    assert "Add Functional Insufficiency" in entries
    assert "Add Gate" not in entries
    assert "Add Basic Event" not in entries


def test_context_menu_fta(monkeypatch):
    pd = _make_page_diagram("FTA")
    monkeypatch.setattr(AutoML.tk, "Menu", DummyMenu)
    event = types.SimpleNamespace(x=0, y=0, x_root=0, y_root=0)
    pd.show_context_menu(event)
    entries = DummyMenu.last.entries
    assert "Add Gate" in entries
    assert "Add Basic Event" in entries
    assert "Add Triggering Condition" not in entries
    assert "Add Functional Insufficiency" not in entries


def test_top_level_menu_gating():
    app = AutoMLApp.__new__(AutoMLApp)

    class Menu:
        def __init__(self):
            self.states = {}

        def entryconfig(self, index, state):
            self.states[index] = state

    app.fta_menu = Menu()
    app.cta_menu = Menu()
    app.paa_menu = Menu()
    app._fta_menu_indices = {
        "add_gate": 0,
        "add_basic_event": 1,
        "add_gate_from_failure_mode": 2,
        "add_fault_event": 3,
    }
    app._cta_menu_indices = {
        "add_trigger": 0,
        "add_functional_insufficiency": 1,
    }
    app._paa_menu_indices = {
        "add_confidence": 0,
        "add_robustness": 1,
    }

    app.diagram_mode = "CTA"
    app.enable_fta_actions = lambda *a, **k: None
    app.enable_cta_actions = lambda *a, **k: None
    app.enable_paa_actions = lambda *a, **k: None
    app.cta_manager = types.SimpleNamespace(enable_actions=lambda *a, **k: None)
    app.validation_consistency = types.SimpleNamespace(
        enable_paa_actions=lambda *a, **k: None
    )
    app._update_analysis_menus()
    tk = AutoML.tk
    assert all(state == tk.DISABLED for state in app.fta_menu.states.values())
    assert all(state == tk.NORMAL for state in app.cta_menu.states.values())

    app.diagram_mode = "FTA"
    app._update_analysis_menus()
    assert all(state == tk.NORMAL for state in app.fta_menu.states.values())
    assert all(state == tk.DISABLED for state in app.cta_menu.states.values())


def test_invalid_node_addition(monkeypatch):
    app = AutoMLApp.__new__(AutoMLApp)
    parent = FaultTreeNode("", "Top Event")
    parent.x = parent.y = 0
    parent.is_primary_instance = True
    app.selected_node = parent
    app.analysis_tree = types.SimpleNamespace(selection=lambda: ())
    app.update_views = lambda: None
    app.undo_manager = types.SimpleNamespace(push_undo_state=lambda *a, **k: None)
    app.diagram_mode = "CTA"

    warnings = []
    monkeypatch.setattr(
        AutoML.messagebox, "showwarning", lambda *a, **k: warnings.append(a)
    )
    app.add_node_of_type("Gate")
    assert warnings
    assert len(parent.children) == 0
