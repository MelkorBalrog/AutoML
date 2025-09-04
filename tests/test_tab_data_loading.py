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
from pathlib import Path
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
from gui.utils.closable_notebook import ClosableNotebook


class DummyTab:
    def __init__(self):
        self.methods = []
        self.events = []

    def load_data(self):
        self.methods.append("load")

    def unload_data(self):
        self.methods.append("unload")

    def event_generate(self, name):
        self.events.append(name)


@pytest.mark.parametrize("strategy", [1, 2, 3, 4])
def test_tab_data_loading(strategy):
    nb = ClosableNotebook.__new__(ClosableNotebook)
    nb._data_strategy = strategy
    nb._focused_tab = None

    tabs = {"t1": DummyTab(), "t2": DummyTab()}

    def select():
        return nb._current

    nb.select = select
    nb.nametowidget = lambda widget_id: tabs[widget_id]
    nb._get_widget = lambda widget_id: tabs.get(widget_id)
    nb._call_method = ClosableNotebook._call_method.__get__(nb)

    nb._current = "t1"
    nb._handle_tab_focus()
    nb._current = "t2"
    nb._handle_tab_focus()

    t1, t2 = tabs["t1"], tabs["t2"]

    if strategy == 1:
        assert t1.methods == ["load"]
        assert t1.events == []
        assert t2.methods == ["load"]
    elif strategy == 2:
        assert t1.methods == ["load", "unload"]
        assert t1.events == []
        assert t2.methods == ["load"]
    elif strategy == 3:
        assert t1.methods == []
        assert t1.events == ["<<TabLoaded>>", "<<TabUnloaded>>"]
        assert t2.events == ["<<TabLoaded>>"]
    else:
        assert t1.methods == ["load", "unload"]
        assert t1.events == ["<<TabLoaded>>", "<<TabUnloaded>>"]
        assert t2.methods == ["load"]
        assert t2.events == ["<<TabLoaded>>"]
