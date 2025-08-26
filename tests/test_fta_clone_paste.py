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

import importlib.util
import os
import sys
import types
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "AutoML", repo_root / "__init__.py", submodule_search_locations=[str(repo_root)]
)
automl = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = automl
spec.loader.exec_module(automl)
AutoMLApp = automl.AutoMLApp
FaultTreeNode = automl.FaultTreeNode
messagebox = automl.messagebox
from mainappsrc.core.diagram_clipboard_manager import DiagramClipboardManager

page_module = importlib.import_module("mainappsrc.core.page_diagram")
PageDiagram = page_module.PageDiagram
fta_drawing_helper = page_module.fta_drawing_helper

def _make_app_with_nodes():
    app = AutoMLApp.__new__(AutoMLApp)
    app.diagram_clipboard = DiagramClipboardManager(app)
    app.top_events = []
    app.root_node = None
    app.selected_node = None
    app.analysis_tree = types.SimpleNamespace(selection=lambda: ())
    app.update_views = lambda: None
    app._diagram_copy_strategy1 = app._diagram_copy_strategy2 = lambda: False
    app._diagram_copy_strategy3 = app._diagram_copy_strategy4 = lambda: False
    app._find_gsn_diagram = lambda node: None
    app._find_cbn_diagram = lambda node: None
    app.window_controllers = types.SimpleNamespace(
        _focused_gsn_window=lambda: None,
        _focused_cbn_window=lambda: None,
        _focused_arch_window=lambda t=None: None,
    )
    messagebox.showinfo = lambda *a, **k: None
    messagebox.showwarning = lambda *a, **k: None
    return app


def test_fta_copy_paste_creates_clone():
    app = _make_app_with_nodes()
    root = FaultTreeNode("Root", "TOP EVENT")
    child = FaultTreeNode("Child", "GATE", parent=root)
    root.children.append(child)
    app.root_node = root
    app.top_events.append(root)
    app.selected_node = child

    app.copy_node()
    assert app.diagram_clipboard.clipboard_node is child

    app.selected_node = root
    app.paste_node()

    assert len(root.children) == 2
    pasted = root.children[-1]
    assert pasted is not child
    assert pasted.original is child
    assert not pasted.is_primary_instance


def test_fta_copy_paste_clone_across_module():
    app = _make_app_with_nodes()

    alt_spec = importlib.util.spec_from_file_location(
        "alt_fault_tree_node", repo_root / "mainappsrc/models/fta/fault_tree_node.py"
    )
    alt_module = importlib.util.module_from_spec(alt_spec)
    alt_spec.loader.exec_module(alt_module)
    AltFaultTreeNode = alt_module.FaultTreeNode

    root = AltFaultTreeNode("Root", "TOP EVENT")
    child = AltFaultTreeNode("Child", "GATE", parent=root)
    root.children.append(child)
    app.root_node = root
    app.top_events.append(root)
    app.selected_node = child

    app.copy_node()
    app.selected_node = root
    app.paste_node()

    assert len(root.children) == 2
    first, second = root.children
    assert first is child
    assert second is not child
    assert second.original is child


class DummyFont:
    def measure(self, text):
        return len(text) * 7

    def metrics(self, key):
        return 10


class DummyCanvas:
    def create_line(self, *a, **k):
        pass

    def create_rectangle(self, *a, **k):
        pass

    def create_polygon(self, *a, **k):
        pass

    def create_text(self, *a, **k):
        pass

    def create_oval(self, *a, **k):
        pass


def test_fta_clone_draws_original_shape(monkeypatch):
    root = FaultTreeNode("Root", "TOP EVENT")
    child = FaultTreeNode("Child", "GATE", parent=root)
    child.gate_type = "OR"
    root.children.append(child)
    clone = child.clone(parent=root)

    app = types.SimpleNamespace(
        project_properties={},
        get_node_fill_color=lambda n, m: "lightgray",
        occurrence_counts={},
    )

    pd = PageDiagram.__new__(PageDiagram)
    pd.app = app
    pd.root_node = root
    pd.canvas = DummyCanvas()
    pd.diagram_mode = "FTA"
    pd.zoom = 1.0
    pd.diagram_font = DummyFont()
    pd.selected_node = None

    called = {}

    def fake_or_clone(*args, **kwargs):
        called["or"] = True

    monkeypatch.setattr(fta_drawing_helper, "draw_rotated_or_gate_clone_shape", fake_or_clone)
    monkeypatch.setattr(fta_drawing_helper, "draw_circle_event_clone_shape", lambda *a, **k: called.setdefault("circle", True))
    monkeypatch.setattr(fta_drawing_helper, "draw_triangle_clone_shape", lambda *a, **k: called.setdefault("triangle", True))
    monkeypatch.setattr(fta_drawing_helper, "draw_rotated_and_gate_clone_shape", lambda *a, **k: called.setdefault("and", True))

    pd.draw_node(clone)

    assert called.get("or")
    assert "circle" not in called
