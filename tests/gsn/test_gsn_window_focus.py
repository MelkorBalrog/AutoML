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
import weakref

from AutoML import AutoMLApp
from mainappsrc.managers.diagram_clipboard_manager import DiagramClipboardManager
from gui.gsn_diagram_window import GSNDiagramWindow, GSNNode, GSNDiagram, GSN_WINDOWS


def _make_window(app, diag):
    win = GSNDiagramWindow.__new__(GSNDiagramWindow)
    win.app = app
    win.diagram = diag
    win.id_to_node = {n.unique_id: n for n in diag.nodes}
    win.canvas = types.SimpleNamespace(delete=lambda *a, **k: None)
    win.refresh = lambda: None
    win.focus_get = lambda: win if getattr(win, "has_focus", False) else None
    win.winfo_toplevel = lambda: win
    win._on_focus_in = types.MethodType(GSNDiagramWindow._on_focus_in, win)
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
    diag1 = GSNDiagram(GSNNode("A", "Goal"))
    diag2 = GSNDiagram(GSNNode("B", "Goal"))
    win1 = _make_window(app, diag1)
    win2 = _make_window(app, diag2)
    GSN_WINDOWS.clear()
    GSN_WINDOWS.add(weakref.ref(win1))
    GSN_WINDOWS.add(weakref.ref(win2))
    return app, win1, win2


def test_gsn_window_strategies():
    app, win1, win2 = setup_app()
    app.active_gsn_window = win1
    win1.has_focus = True
    assert app._gsn_window_strategy1() is win1
    win1.has_focus = False
    win2.has_focus = True
    assert app._gsn_window_strategy2() is win2
    assert app._gsn_window_strategy3() is win1
    app.active_gsn_window = None
    win2.has_focus = False
    assert app._gsn_window_strategy4() in {win1, win2}


def test_gsn_paste_uses_focused_window():
    app, win1, win2 = setup_app()
    node = win1.diagram.root
    win1.selected_node = node
    win1._on_focus_in()
    app.copy_node()
    assert app.diagram_clipboard.diagram_clipboard is node
    win1.has_focus = False
    win2.has_focus = True
    win2._on_focus_in()
    app.paste_node()
    assert win2.diagram.nodes[-1] is not node
