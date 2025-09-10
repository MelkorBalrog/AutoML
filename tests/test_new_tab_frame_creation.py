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

"""Ensure ``_new_tab`` creates a dedicated frame for docking."""

from __future__ import annotations

import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import mainappsrc.ui.app_lifecycle_ui as app_lifecycle_ui


def test_new_tab_uses_separate_frame(monkeypatch):
    class DummyFrame:  # minimal stand-in for ttk.Frame
        pass

    class DummyNotebook:
        def __init__(self):
            self._tabs: list[str] = []
            self._widgets: dict[str, object] = {}
            self.selected = None

        def tabs(self):
            return list(self._tabs)

        def add(self, widget, text):
            tab_id = f"id{len(self._tabs)}"
            self._tabs.append(tab_id)
            self._widgets[tab_id] = widget

        def select(self, tab_id):
            self.selected = tab_id

    captured: dict[str, object] = {}

    def fake_frame(master):
        return DummyFrame()

    class DummyDock:
        def __init__(self, content):
            captured["content"] = content
            self.content_frame = content

        def dock(self, notebook, index, title):
            notebook.add(self.content_frame, text=title)

    monkeypatch.setattr(app_lifecycle_ui.ttk, "Frame", fake_frame)
    monkeypatch.setattr(app_lifecycle_ui, "DockableDiagramWindow", DummyDock)

    app = types.SimpleNamespace(
        doc_nb=DummyNotebook(), MAX_TAB_TEXT_LENGTH=20, MAX_VISIBLE_TABS=5
    )
    ui = app_lifecycle_ui.AppLifecycleUI(app, None)

    tab = ui._new_tab("Demo")

    assert isinstance(tab, DummyFrame)
    assert captured["content"] is tab
    assert tab is not app.doc_nb
    assert tab._dock_window  # tab gains reference to helper
