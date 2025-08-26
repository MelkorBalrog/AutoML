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

import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import mainappsrc.ui.app_lifecycle_ui as app_lifecycle_ui
from mainappsrc.ui.app_lifecycle_ui import AppLifecycleUI


def test_tool_tab_not_duplicated(monkeypatch):
    class DummyListbox:
        def __init__(self, master, height=10):
            self.items = []

        def configure(self, **kwargs):
            pass

        def pack(self, *args, **kwargs):
            pass

        def bind(self, *args, **kwargs):
            pass

        def insert(self, index, item):
            self.items.append(item)

        def get(self, start, end):
            return tuple(self.items)

        def yview(self, *args, **kwargs):
            pass

    class DummyScrollbar:
        def __init__(self, *args, **kwargs):
            pass

        def pack(self, *args, **kwargs):
            pass

        def set(self, *args, **kwargs):
            pass

    class DummyFrame:
        def __init__(self, master):
            pass

        def pack(self, *args, **kwargs):
            pass

    class DummyNotebook:
        def __init__(self):
            self._tabs = []
            self._titles = {}

        def add(self, widget, text):
            tab_id = f"id{len(self._tabs)}"
            self._tabs.append(tab_id)
            self._titles[tab_id] = text

        def tabs(self):
            return list(self._tabs)

        def tab(self, tab_id, option):
            assert option == "text"
            return self._titles[tab_id]

        def forget(self, tab_id):
            self._tabs.remove(tab_id)
            self._titles.pop(tab_id, None)
    monkeypatch.setattr(app_lifecycle_ui, "ttk", types.SimpleNamespace(Frame=lambda master: DummyFrame(master), Scrollbar=lambda master, orient, command: DummyScrollbar()))
    monkeypatch.setattr(
        app_lifecycle_ui,
        "tk",
        types.SimpleNamespace(
            Listbox=lambda master, height=10: DummyListbox(master, height),
            END="end",
            LEFT="left",
            RIGHT="right",
            BOTH="both",
            Y="y",
        ),
    )
    monkeypatch.setattr(app_lifecycle_ui.AppLifecycleUI, "_update_tool_tab_visibility", lambda self: None)
    class DummyApp:
        tools_nb = DummyNotebook()
        tool_listboxes = {}
        _tool_tab_titles = {}
        _tool_all_tabs = []
        _tool_tab_offset = 0
        MAX_VISIBLE_TABS = 5
        MAX_TOOL_TAB_TEXT_LENGTH = 20
        def on_tool_list_double_click(self, event):
            pass
        def _update_tool_tab_visibility(self):
            pass
    ui = AppLifecycleUI(DummyApp(), None)
    ui._add_tool_category("Area", ["Tool1"])
    ui._add_tool_category("Area", ["Tool2"])
    assert len(ui.tools_nb.tabs()) == 1
    lb = ui.tool_listboxes["Area"]
    assert lb.items == ["Tool1", "Tool2"]
