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
from gui.architecture import (
    SysMLDiagramWindow,
    _get_next_id,
    ARCH_WINDOWS,
    SysMLObject,
)


class DummyRepo:
    def __init__(self):
        self.diagrams = {
            1: types.SimpleNamespace(diag_type="Governance Diagram", elements=[]),
            2: types.SimpleNamespace(diag_type="Governance Diagram", elements=[]),
        }

    def diagram_read_only(self, _id):
        return False


def make_window(app, repo, diagram_id):
    win = SysMLDiagramWindow.__new__(SysMLDiagramWindow)
    win.app = app
    win.repo = repo
    win.diagram_id = diagram_id
    win.objects = []
    win.selected_obj = None
    win.remove_object = lambda o: win.objects.remove(o)
    win._sync_to_repository = lambda: None
    win.redraw = lambda: None
    win.update_property_view = lambda: None
    win.sort_objects = lambda: None
    win._rebuild_toolboxes = lambda: None
    win.refresh_from_repository = lambda e=None: None
    return win


def setup_app():
    app = AutoMLApp.__new__(AutoMLApp)
    app.diagram_clipboard = DiagramClipboardManager(app)
    app.diagram_clipboard.diagram_clipboard = None
    app.diagram_clipboard.diagram_clipboard_type = None
    app.selected_node = None
    app.root_node = None
    app.diagram_clipboard.clipboard_node = None
    app.diagram_clipboard.cut_mode = False
    repo = DummyRepo()
    win1 = make_window(app, repo, 1)
    win2 = make_window(app, repo, 2)
    ARCH_WINDOWS.clear()
    ARCH_WINDOWS.add(weakref.ref(win1))
    ARCH_WINDOWS.add(weakref.ref(win2))
    return app, win1, win2


def _make_obj():
    return SysMLObject(
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


def test_arch_window_strategies():
    app, win1, win2 = setup_app()
    # Strategy1: active window with focus
    app.active_arch_window = win1
    win1.has_focus = True
    assert app._arch_window_strategy1() is win1

    # Strategy2: some other window has focus
    win1.has_focus = False
    win2.has_focus = True
    assert app._arch_window_strategy2() is win2

    # Strategy3: active window without focus
    assert app._arch_window_strategy3() is win1

    # Strategy4: fallback when no focus and no active
    app.active_arch_window = None
    win2.has_focus = False
    assert app._arch_window_strategy4() in {win1, win2}


def test_paste_uses_focused_window():
    app, win1, win2 = setup_app()
    obj = _make_obj()
    win1.objects = [obj]
    win1.selected_obj = obj

    win1.copy_selected()
    assert app.diagram_clipboard.diagram_clipboard is not None
    app.active_arch_window = win1

    win1.has_focus = False
    win2.has_focus = True

    app.paste_node()
    assert len(win2.objects) == 1
    assert win2.objects[0] is not obj
