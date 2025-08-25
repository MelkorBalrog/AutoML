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
from mainappsrc.core.diagram_clipboard_manager import DiagramClipboardManager
from gui.architecture import SysMLDiagramWindow, _get_next_id, ARCH_WINDOWS, SysMLObject


class DummyRepo:
    def __init__(self):
        self.diagrams = {
            1: types.SimpleNamespace(diag_type="Governance Diagram", elements=[]),
            2: types.SimpleNamespace(diag_type="Governance Diagram", elements=[]),
        }

    def diagram_read_only(self, _id):
        return False


class DummyNotebook:
    def __init__(self):
        self.tabs = {}
        self._selected = None

    def add(self, name, tab):
        self.tabs[name] = tab
        if self._selected is None:
            self._selected = name

    def select(self, name=None):
        if name is None:
            return self._selected
        self._selected = name

    def nametowidget(self, name):
        return self.tabs[name]


def _make_window(app, repo, diagram_id, tab):
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
    win._rebuild_toolboxes = lambda: None
    win.refresh_from_repository = lambda e=None: None
    win._on_focus_in = types.MethodType(SysMLDiagramWindow._on_focus_in, win)
    win.master = tab
    ARCH_WINDOWS.add(weakref.ref(win))
    return win


def test_paste_respects_selected_governance_tab():
    ARCH_WINDOWS.clear()
    app = AutoMLApp.__new__(AutoMLApp)
    app.diagram_clipboard = DiagramClipboardManager(app)
    app.selected_node = None
    app.root_node = None
    app.diagram_clipboard.clipboard_node = None
    app.diagram_clipboard.cut_mode = False
    repo = DummyRepo()
    app._get_diag_type = lambda win: repo.diagrams.get(win.diagram_id).diag_type
    nb = DummyNotebook()
    app.doc_nb = nb

    class StubControllers:
        def __init__(self, app):
            self.app = app

        def _focused_cbn_window(self):
            return None

        def _focused_gsn_window(self):
            return None

        def _focused_arch_window(self, clip_type=None):
            sel = nb.select()
            tab = nb.nametowidget(sel)
            return getattr(tab, "arch_window", None)

    app._window_controllers = StubControllers(app)

    tab1 = types.SimpleNamespace()
    tab2 = types.SimpleNamespace()
    nb.add("t1", tab1)
    nb.add("t2", tab2)

    win1 = _make_window(app, repo, 1, tab1)
    win2 = _make_window(app, repo, 2, tab2)
    tab1.arch_window = win1
    tab2.arch_window = win2

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

    win1.objects = [obj]
    win1.selected_obj = obj
    win1._on_focus_in()

    win1.copy_selected()
    assert app.diagram_clipboard.diagram_clipboard is not None

    nb.select("t2")
    assert app.window_controllers._focused_arch_window("Governance Diagram") is win2
    app.paste_node()

    assert len(win2.objects) == 1
