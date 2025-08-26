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

import os
import sys
import types
import weakref

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from AutoML import AutoMLApp
from mainappsrc.managers.diagram_clipboard_manager import DiagramClipboardManager
from gui.gsn_diagram_window import GSNNode, GSNDiagram, GSNDiagramWindow, GSN_WINDOWS
from gui.architecture import SysMLDiagramWindow, _get_next_id, SysMLObject, ARCH_WINDOWS


class DummyRepo:
    def __init__(self):
        self.diagrams = {1: types.SimpleNamespace(diag_type="Governance Diagram", elements=[])}

    def diagram_read_only(self, _id):
        return False


def make_arch_window(app, repo):
    win = SysMLDiagramWindow.__new__(SysMLDiagramWindow)
    win.app = app
    win.repo = repo
    win.diagram_id = 1
    win.selected_obj = None
    win.objects = []
    win.remove_object = lambda o: win.objects.remove(o)
    win._sync_to_repository = lambda: None
    win.redraw = lambda: None
    win.update_property_view = lambda: None
    win.sort_objects = lambda: None
    win._rebuild_toolboxes = lambda: None
    win._on_focus_in = types.MethodType(SysMLDiagramWindow._on_focus_in, win)
    return win


def test_copy_paste_respects_active_arch_diagram_when_gsn_exists():
    ARCH_WINDOWS.clear()
    GSN_WINDOWS.clear()
    app = AutoMLApp.__new__(AutoMLApp)
    app.diagram_clipboard = DiagramClipboardManager(app)
    app.diagram_clipboard.diagram_clipboard = None
    app.diagram_clipboard.diagram_clipboard_type = None
    app.selected_node = None
    app.root_node = None
    app.diagram_clipboard.clipboard_node = None
    app.diagram_clipboard.cut_mode = False

    # Setup GSN window with a selected node
    root = GSNNode("Root", "Goal")
    child = GSNNode("Child", "Solution")
    root.add_child(child)
    diag = GSNDiagram(root)
    win_gsn = GSNDiagramWindow.__new__(GSNDiagramWindow)
    win_gsn.app = app
    win_gsn.diagram = diag
    win_gsn.id_to_node = {n.unique_id: n for n in diag.nodes}
    win_gsn.selected_node = child
    win_gsn.focus_get = lambda: None
    win_gsn.winfo_toplevel = lambda: win_gsn
    win_gsn.copy_selected = lambda: (
        setattr(app.diagram_clipboard, "diagram_clipboard", child),
        setattr(app.diagram_clipboard, "diagram_clipboard_type", "GSN"),
    )
    win_gsn.paste_selected = lambda: diag.nodes.append(GSNNode("Extra", "Goal"))
    GSN_WINDOWS.add(weakref.ref(win_gsn))
    app.active_gsn_window = win_gsn

    # Setup architecture window with a selected object
    repo = DummyRepo()
    win_arch = make_arch_window(app, repo)
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
    win_arch.objects = [obj]
    win_arch.selected_obj = obj
    win_arch.copy_selected = lambda: (
        setattr(app.diagram_clipboard, "diagram_clipboard", obj),
        setattr(app.diagram_clipboard, "diagram_clipboard_type", repo.diagrams[1].diag_type),
    )
    win_arch.paste_selected = lambda: win_arch.objects.append("pasted")
    app.active_arch_window = win_arch

    tab_gsn = types.SimpleNamespace(gsn_window=win_gsn, winfo_children=lambda: [])
    tab_arch = types.SimpleNamespace(gsn_window=None, arch_window=win_arch, winfo_children=lambda: [])
    app.doc_nb = types.SimpleNamespace(select=lambda: "arch", nametowidget=lambda tid: {"gsn": tab_gsn, "arch": tab_arch}[tid])

    app.copy_node()
    assert app.diagram_clipboard.diagram_clipboard is obj

    app.paste_node()
    assert win_arch.objects[-1] == "pasted"
    assert len(diag.nodes) == 1  # unchanged by paste
