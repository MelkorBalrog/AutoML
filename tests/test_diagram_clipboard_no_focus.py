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
from gui.architecture import SysMLDiagramWindow, _get_next_id, ARCH_WINDOWS, SysMLObject
from gui.controls import messagebox


class DummyRepo:
    def __init__(self):
        self.diagrams = {1: types.SimpleNamespace(diag_type="Governance Diagram", elements=[])}

    def diagram_read_only(self, _id):
        return False


def make_window(app, repo):
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
    return win


def test_paste_without_active_window_uses_clipboard():
    app = AutoMLApp.__new__(AutoMLApp)
    app.diagram_clipboard = DiagramClipboardManager(app)
    app.diagram_clipboard.diagram_clipboard = None
    app.diagram_clipboard.diagram_clipboard_type = None
    app.selected_node = None
    app.root_node = None
    app.diagram_clipboard.clipboard_node = None
    app.diagram_clipboard.cut_mode = False

    repo = DummyRepo()
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

    win = make_window(app, repo)
    win.selected_obj = obj
    win.objects = [obj]
    ARCH_WINDOWS.add(weakref.ref(win))

    win.copy_selected()
    app.active_arch_window = None

    warnings = []
    orig = messagebox.showwarning
    messagebox.showwarning = lambda t, m: warnings.append((t, m))
    try:
        app.paste_node()
    finally:
        messagebox.showwarning = orig

    assert not warnings
    assert len(win.objects) == 2

