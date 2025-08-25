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
from types import SimpleNamespace

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from AutoML import AutoMLApp
from mainappsrc.core.diagram_clipboard_manager import DiagramClipboardManager
from gui.architecture import SysMLDiagramWindow, _get_next_id, SysMLObject, ARCH_WINDOWS


class DummyRepo:
    def __init__(self):
        self.diagrams = {
            1: SimpleNamespace(diag_type="Governance Diagram", elements=[], name="d1"),
            2: SimpleNamespace(diag_type="Governance Diagram", elements=[], name="d2"),
            3: SimpleNamespace(diag_type="Governance Diagram", elements=[], name="d3"),
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
    return win


def test_multiple_copy_cut_paste_governance_diagrams():
    ARCH_WINDOWS.clear()
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

    win1 = make_window(app, repo, 1)
    win1.selected_obj = obj
    win1.objects = [obj]

    win2 = make_window(app, repo, 2)
    win3 = make_window(app, repo, 3)

    # First copy/paste from win1 to win2
    win1._on_focus_in()
    app.copy_node()
    win2._on_focus_in()
    app.paste_node()
    assert len(win2.objects) == 1

    # Second copy/paste from win2 to win3
    win2.selected_obj = win2.objects[0]
    win2._on_focus_in()
    app.copy_node()
    win3._on_focus_in()
    app.paste_node()
    assert len(win3.objects) == 1

    # Cut/paste back to win1
    win3.selected_obj = win3.objects[0]
    win3._on_focus_in()
    app.cut_node()
    win1._on_focus_in()
    app.paste_node()
    assert len(win3.objects) == 0
    assert len(win1.objects) == 2
