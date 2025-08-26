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

"""Tests for tab-aware clipboard operations in governance diagrams."""

from __future__ import annotations

import types

from AutoML import AutoMLApp
from mainappsrc.managers.diagram_clipboard_manager import DiagramClipboardManager
from gui.controls.window_controllers import WindowControllers
from gui.architecture import ARCH_WINDOWS, SysMLObject, _get_next_id
from tests.test_cross_diagram_clipboard import DummyRepo, make_window


class _Notebook:
    """Simple notebook stub tracking selected tabs."""

    def __init__(self) -> None:
        self.tabs: dict[str, types.SimpleNamespace] = {}
        self._sel = ""

    def add(self, name: str, tab: types.SimpleNamespace) -> None:
        self.tabs[name] = tab
        if not self._sel:
            self._sel = name

    def select(self, name: str | None = None) -> str | None:
        if name is None:
            return self._sel
        self._sel = name
        return None

    def nametowidget(self, name: str) -> types.SimpleNamespace:
        return self.tabs[name]


def _setup_app() -> tuple[AutoMLApp, _Notebook, types.SimpleNamespace, types.SimpleNamespace, SysMLObject]:
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
    win1 = make_window(app, repo, 1)
    win2 = make_window(app, repo, 2)

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

    nb = _Notebook()
    tab1 = types.SimpleNamespace(arch_window=win1, gsn_window=None, winfo_children=lambda: [])
    tab2 = types.SimpleNamespace(arch_window=win2, gsn_window=None, winfo_children=lambda: [])
    nb.add("t1", tab1)
    nb.add("t2", tab2)
    app.doc_nb = nb
    app.diagram_tabs = {"1": tab1, "2": tab2}
    app._window_has_focus = lambda w: False
    def _win_in_tab(win):
        sel = nb.select()
        tab = nb.nametowidget(sel)
        return getattr(tab, "arch_window", None) is win or getattr(tab, "gsn_window", None) is win
    app._window_in_selected_tab = _win_in_tab
    app._window_controllers = WindowControllers(app)

    return app, nb, win1, win2, obj


def test_governance_clipboard_respects_tab_focus():
    for mode in ("copy", "cut"):
        app, nb, win1, win2, obj = _setup_app()
        if mode == "copy":
            app.copy_node()
            assert obj in win1.objects
        else:
            app.cut_node()
            assert obj not in win1.objects

        nb.select("t2")
        app.paste_node()

        assert any(o.obj_type == "Plan" for o in win2.objects)
        if mode == "copy":
            assert obj in win1.objects
        else:
            assert obj in win2.objects
