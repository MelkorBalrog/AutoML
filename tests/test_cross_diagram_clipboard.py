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


import os
import sys
import types

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from AutoML import AutoMLApp
from mainappsrc.managers.diagram_clipboard_manager import DiagramClipboardManager
from gui.architecture import SysMLDiagramWindow, _get_next_id, SysMLObject, ARCH_WINDOWS
from gui.gsn_diagram_window import GSNDiagramWindow, GSN_WINDOWS
from mainappsrc.models.gsn import GSNNode, GSNDiagram
import weakref


class DummyRepo:
    def __init__(self, diag1_type, diag2_type):
        self.diagrams = {
            1: types.SimpleNamespace(diag_type=diag1_type, elements=[]),
            2: types.SimpleNamespace(diag_type=diag2_type, elements=[]),
        }

    def diagram_read_only(self, _id):
        return False


def make_window(app, repo, diagram_id):
    win = SysMLDiagramWindow.__new__(SysMLDiagramWindow)
    win.app = app
    win.repo = repo
    win.diagram_id = diagram_id
    win.selected_obj = None
    win.objects = []
    win.remove_object = lambda o: win.objects.remove(o)
    win._sync_to_repository = lambda: None
    win.redraw = lambda: None
    win.update_property_view = lambda: None
    win.sort_objects = lambda: None
    win.refresh_from_repository = lambda e=None: None
    win._on_focus_in = types.MethodType(SysMLDiagramWindow._on_focus_in, win)
    win._constrain_to_parent = lambda obj, parent: None
    def _stub_place_process_area(name, x, y):
        area = SysMLObject(
            obj_id=_get_next_id(),
            obj_type="System Boundary",
            x=x,
            y=y,
            element_id=None,
            width=80,
            height=40,
            properties={"name": name},
            requirements=[],
            locked=False,
            hidden=False,
            collapsed={},
        )
        win.objects.append(area)
        return area

    win._place_process_area = _stub_place_process_area
    win._rebuild_toolboxes = lambda: None
    return win


def make_gsn_window(app, diagram):
    win = GSNDiagramWindow.__new__(GSNDiagramWindow)
    win.app = app
    win.diagram = diagram
    win.id_to_node = {n.unique_id: n for n in diagram.nodes}
    win.selected_node = None
    win.canvas = types.SimpleNamespace(
        delete=lambda *a, **k: None,
        find_overlapping=lambda *a, **k: [],
        find_closest=lambda *a, **k: [],
        bbox=lambda *a, **k: None,
        gettags=lambda i: [],
    )
    win.refresh = lambda: None
    win.focus_get = lambda: win if getattr(win, "_focus", False) else None
    win.winfo_toplevel = lambda: win
    win._on_focus_in = types.MethodType(GSNDiagramWindow._on_focus_in, win)
    GSN_WINDOWS.add(weakref.ref(win))
    return win


class DummyNotebook:
    def __init__(self):
        self.tabs = {}
        self._selected = None

    def add(self, name, win):
        tab = types.SimpleNamespace(gsn_window=win)
        self.tabs[name] = tab
        if self._selected is None:
            self._selected = name
        return tab

    def select(self, name=None):
        if name is None:
            return self._selected
        self._selected = name

    def nametowidget(self, name):
        return self.tabs.get(name)


def test_copy_paste_between_same_type_diagrams():
    ARCH_WINDOWS.clear()
    app = AutoMLApp.__new__(AutoMLApp)
    app.diagram_clipboard = DiagramClipboardManager(app)
    app.diagram_clipboard.diagram_clipboard = None
    app.diagram_clipboard.diagram_clipboard_type = None
    app.selected_node = None
    app.root_node = None
    app.diagram_clipboard.clipboard_node = None
    app.diagram_clipboard.cut_mode = False
    repo = DummyRepo("Governance Diagram", "Governance Diagram")

    obj = SysMLObject(
        obj_id=_get_next_id(),
        obj_type="Plan",
        x=0,
        y=0,
        element_id=None,
        width=80,
        height=40,
        properties={},
        requirements=[],
        locked=False,
        hidden=False,
        collapsed={},
    )

    win1 = make_window(app, repo, 1)
    win1.selected_obj = obj
    win1.objects = [obj]

    win2 = make_window(app, repo, 2)

    win1._on_focus_in()
    app.copy_node()
    assert app.diagram_clipboard.diagram_clipboard is not None

    win2._on_focus_in()
    app.paste_node()

    assert len(win2.objects) == 1
    assert win2.objects[0] is not obj


def test_copy_paste_task_between_governance_diagrams():
    ARCH_WINDOWS.clear()
    app = AutoMLApp.__new__(AutoMLApp)
    app.diagram_clipboard = DiagramClipboardManager(app)
    app.diagram_clipboard.diagram_clipboard = None
    app.diagram_clipboard.diagram_clipboard_type = None
    app.selected_node = None
    app.root_node = None
    app.diagram_clipboard.clipboard_node = None
    app.diagram_clipboard.cut_mode = False
    repo = DummyRepo("Governance Diagram", "Governance Diagram")

    boundary1 = SysMLObject(
        obj_id=_get_next_id(),
        obj_type="System Boundary",
        x=0,
        y=0,
        element_id=None,
        width=80,
        height=40,
        properties={"name": "Area"},
        requirements=[],
        locked=False,
        hidden=False,
        collapsed={},
    )
    task = SysMLObject(
        obj_id=_get_next_id(),
        obj_type="Task",
        x=10,
        y=10,
        element_id=None,
        width=80,
        height=40,
        properties={"boundary": str(boundary1.obj_id)},
        requirements=[],
        locked=False,
        hidden=False,
        collapsed={},
    )

    win1 = make_window(app, repo, 1)
    win1.objects = [boundary1, task]
    win1.selected_obj = task

    boundary2 = SysMLObject(
        obj_id=_get_next_id(),
        obj_type="System Boundary",
        x=0,
        y=0,
        element_id=None,
        width=80,
        height=40,
        properties={"name": "Area"},
        requirements=[],
        locked=False,
        hidden=False,
        collapsed={},
    )
    win2 = make_window(app, repo, 2)
    win2.objects = [boundary2]

    win1._on_focus_in()
    app.copy_node()
    assert app.diagram_clipboard.diagram_clipboard is not None

    win2._on_focus_in()
    app.paste_node()

    assert len(win2.objects) == 3
    assert sum(1 for o in win2.objects if o.obj_type == "System Boundary") == 2
    assert any(o.obj_type == "Task" for o in win2.objects)


def test_copy_paste_governance_with_selected_node():
    ARCH_WINDOWS.clear()
    app = AutoMLApp.__new__(AutoMLApp)
    app.diagram_clipboard = DiagramClipboardManager(app)
    app.diagram_clipboard.diagram_clipboard = None
    app.diagram_clipboard.diagram_clipboard_type = None
    # Simulate leftover selected node from another analysis
    app.selected_node = types.SimpleNamespace(node_type="Event", parents=[])
    app.root_node = object()
    app.diagram_clipboard.clipboard_node = None
    app.diagram_clipboard.cut_mode = False
    repo = DummyRepo("Governance Diagram", "Governance Diagram")

    obj = SysMLObject(
        obj_id=_get_next_id(),
        obj_type="Plan",
        x=0,
        y=0,
        element_id=None,
        width=80,
        height=40,
        properties={},
        requirements=[],
        locked=False,
        hidden=False,
        collapsed={},
    )

    win1 = make_window(app, repo, 1)
    win1.objects = [obj]
    win1.selected_obj = obj

    win2 = make_window(app, repo, 2)

    win1._on_focus_in()
    app.copy_node()
    assert app.diagram_clipboard.diagram_clipboard is not None
    assert app.diagram_clipboard.clipboard_node is None

    win2._on_focus_in()
    app.paste_node()

    assert len(win2.objects) == 1
    assert win2.objects[0].obj_type == "Plan"


def test_cut_paste_between_governance_diagrams():
    ARCH_WINDOWS.clear()
    app = AutoMLApp.__new__(AutoMLApp)
    app.diagram_clipboard = DiagramClipboardManager(app)
    app.diagram_clipboard.diagram_clipboard = None
    app.diagram_clipboard.diagram_clipboard_type = None
    app.selected_node = None
    app.root_node = None
    app.diagram_clipboard.clipboard_node = None
    app.diagram_clipboard.cut_mode = False
    repo = DummyRepo("Governance Diagram", "Governance Diagram")

    obj = SysMLObject(
        obj_id=_get_next_id(),
        obj_type="Plan",
        x=0,
        y=0,
        element_id=None,
        width=80,
        height=40,
        properties={},
        requirements=[],
        locked=False,
        hidden=False,
        collapsed={},
    )

    win1 = make_window(app, repo, 1)
    win1.objects = [obj]
    win1.selected_obj = obj

    win2 = make_window(app, repo, 2)

    win1._on_focus_in()
    app.cut_node()
    assert app.diagram_clipboard.diagram_clipboard is not None

    win2._on_focus_in()
    app.paste_node()

    assert len(win1.objects) == 0
    assert len(win2.objects) == 1
    assert win2.objects[0].obj_type == "Plan"


def test_copy_paste_governance_replaces_node_clipboard():
    ARCH_WINDOWS.clear()
    app = AutoMLApp.__new__(AutoMLApp)
    app.diagram_clipboard = DiagramClipboardManager(app)
    app.diagram_clipboard.diagram_clipboard = None
    app.diagram_clipboard.diagram_clipboard_type = None
    # Simulate leftover clipboard node from a different analysis
    app.diagram_clipboard.clipboard_node = types.SimpleNamespace(
        unique_id="n1",
        parents=[],
        children=[],
        node_type="Goal",
        x=0,
        y=0,
        display_label="dummy",
        is_primary_instance=True,
    )
    app.selected_node = app.diagram_clipboard.clipboard_node
    app.root_node = object()
    app.diagram_clipboard.cut_mode = False
    repo = DummyRepo("Governance Diagram", "Governance Diagram")

    obj = SysMLObject(
        obj_id=_get_next_id(),
        obj_type="Plan",
        x=0,
        y=0,
        element_id=None,
        width=80,
        height=40,
        properties={},
        requirements=[],
        locked=False,
        hidden=False,
        collapsed={},
    )

    win1 = make_window(app, repo, 1)
    win1.objects = [obj]
    win1.selected_obj = obj

    win2 = make_window(app, repo, 2)

    win1._on_focus_in()
    # Directly invoke window copy to mimic context menu usage
    win1.copy_selected()
    assert app.diagram_clipboard.diagram_clipboard is not None
    assert app.diagram_clipboard.clipboard_node is None

    win2._on_focus_in()
    app.paste_node()

    assert len(win2.objects) == 1
    assert win2.objects[0].obj_type == "Plan"


def test_copy_paste_process_area_between_diagrams():
    ARCH_WINDOWS.clear()
    app = AutoMLApp.__new__(AutoMLApp)
    app.diagram_clipboard = DiagramClipboardManager(app)
    app.diagram_clipboard.diagram_clipboard = None
    app.diagram_clipboard.diagram_clipboard_type = None
    app.selected_node = None
    app.root_node = None
    app.diagram_clipboard.clipboard_node = None
    app.diagram_clipboard.cut_mode = False
    repo = DummyRepo("Governance Diagram", "Governance Diagram")

    area = SysMLObject(
        obj_id=_get_next_id(),
        obj_type="System Boundary",
        x=0,
        y=0,
        element_id=None,
        width=80,
        height=40,
        properties={"name": "Area"},
        requirements=[],
        locked=False,
        hidden=False,
        collapsed={},
    )

    win1 = make_window(app, repo, 1)
    win1.objects = [area]
    win1.selected_obj = area

    win2 = make_window(app, repo, 2)

    win1._on_focus_in()
    app.copy_node()
    assert app.diagram_clipboard.diagram_clipboard is not None

    win2._on_focus_in()
    app.paste_node()

    assert len(win2.objects) == 1
    assert win2.objects[0].obj_type == "System Boundary"


def test_copy_paste_between_gsn_diagrams():
    GSN_WINDOWS.clear()
    app = AutoMLApp.__new__(AutoMLApp)
    app.diagram_clipboard = DiagramClipboardManager(app)
    app.diagram_clipboard.diagram_clipboard = None
    app.diagram_clipboard.diagram_clipboard_type = None
    app.selected_node = None
    app.diagram_clipboard.clipboard_node = None
    app.diagram_clipboard.cut_mode = False
    root1 = GSNNode("R1", "Goal")
    child = GSNNode("C1", "Goal")
    root1.add_child(child)
    diag1 = GSNDiagram(root1)
    diag1.add_node(child)
    root2 = GSNNode("R2", "Goal")
    diag2 = GSNDiagram(root2)
    app.gsn_diagrams = [diag1, diag2]
    app.gsn_modules = []
    win1 = make_gsn_window(app, diag1)
    win2 = make_gsn_window(app, diag2)
    nb = DummyNotebook()
    nb.add("t1", win1)
    nb.add("t2", win2)
    app.doc_nb = nb
    win1.selected_node = child
    win1._focus = True
    nb.select("t1")
    app.copy_node()
    nb.select("t2")
    app.paste_node()
    assert len(diag2.nodes) == 2
    assert diag2.nodes[-1].original is child.original


def test_cut_paste_between_gsn_diagrams():
    GSN_WINDOWS.clear()
    app = AutoMLApp.__new__(AutoMLApp)
    app.diagram_clipboard = DiagramClipboardManager(app)
    app.diagram_clipboard.diagram_clipboard = None
    app.diagram_clipboard.diagram_clipboard_type = None
    app.selected_node = None
    app.diagram_clipboard.clipboard_node = None
    app.diagram_clipboard.cut_mode = False
    root1 = GSNNode("R1", "Goal")
    child = GSNNode("C1", "Goal")
    root1.add_child(child)
    diag1 = GSNDiagram(root1)
    diag1.add_node(child)
    root2 = GSNNode("R2", "Goal")
    diag2 = GSNDiagram(root2)
    app.gsn_diagrams = [diag1, diag2]
    app.gsn_modules = []
    win1 = make_gsn_window(app, diag1)
    win2 = make_gsn_window(app, diag2)
    nb = DummyNotebook()
    nb.add("t1", win1)
    nb.add("t2", win2)
    app.doc_nb = nb
    win1.selected_node = child
    win1._focus = True
    nb.select("t1")
    app.cut_node()
    nb.select("t2")
    app.paste_node()
    assert child not in diag1.nodes
    assert any(n.original is child.original for n in diag2.nodes)
