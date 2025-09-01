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
import pytest

from analysis.causal_bayesian_network import CausalBayesianNetworkDoc
from gui.causal_bayesian_network_window import CausalBayesianNetworkWindow


class DummyFrame:
    def winfo_reqwidth(self):
        return 20

    def winfo_reqheight(self):
        return 10

    def update_idletasks(self):
        pass

    def destroy(self):
        pass


class DummyCanvas:
    def __init__(self):
        self.coords_map = {}
        self.next_id = 1

    def create_window(self, *a, **k):
        i = self.next_id
        self.next_id += 1
        self.coords_map[i] = (0, 0)
        return i

    def create_oval(self, *a, **k):
        i = self.next_id
        self.next_id += 1
        self.coords_map[i] = (0, 0)
        return i

    def create_text(self, *a, **k):
        i = self.next_id
        self.next_id += 1
        self.coords_map[i] = (0, 0)
        return i

    def itemconfigure(self, *a, **k):
        pass

    def coords(self, win, *args):
        if args:
            self.coords_map[win] = (args[0], args[1])
        return self.coords_map.get(win, (0, 0))

    def move(self, win, dx, dy):
        x, y = self.coords_map.get(win, (0, 0))
        self.coords_map[win] = (x + dx, y + dy)

    def delete(self, *a, **k):
        pass


def _make_window():
    doc = CausalBayesianNetworkDoc(name="d")
    doc.network.add_node("A", cpd=0.5)
    doc.positions["A"] = [(0, 0)]
    doc.types["A"] = "variable"
    app = types.SimpleNamespace(active_cbn=doc, cbn_docs=[doc])

    win = object.__new__(CausalBayesianNetworkWindow)
    win.app = app
    win.NODE_RADIUS = 10
    win.nodes = {}
    win.id_to_node = {}
    win.edges = []
    win.tables = {}
    win.canvas = DummyCanvas()
    win.drawing_helper = types.SimpleNamespace(_fill_gradient_circle=lambda *a, **k: [])
    win._update_scroll_region = lambda: None
    win.current_tool = "Select"
    win.selected_node = None
    win.selection_rect = None

    def _place_table_stub(name, idx):
        frame = DummyFrame()
        win_id = win.canvas.create_window(0, 0)
        tables = win.tables.setdefault(name, [])
        while len(tables) <= idx:
            tables.append(None)
        tables[idx] = (win_id, frame, None)
        x, y = doc.positions.get(name, [(0, 0)])[idx]
        win._position_table(name, idx, x, y)

    win._place_table = _place_table_stub
    win._update_table = lambda *a, **k: None

    win._draw_node("A", 0, 0, "variable", idx=0)
    tbl_id = win.tables["A"][0][0]
    return win, tbl_id


@pytest.mark.parametrize(
    "method",
    [
        "_drag_table_strategy1",
        "_drag_table_strategy2",
        "_drag_table_strategy3",
        "_drag_table_strategy4",
    ],
)
def test_drag_table_strategies_move_table(method):
    win, tbl_id = _make_window()
    initial = win.canvas.coords(tbl_id)
    getattr(win, method)("A", 0, 30, 40)
    assert win.canvas.coords(tbl_id) != initial


def test_on_drag_moves_table():
    win, tbl_id = _make_window()
    win.drag_node = ("A", 0)
    win.drag_offset = (0, 0)
    event = types.SimpleNamespace(x=25, y=35)
    before = win.canvas.coords(tbl_id)
    win.on_drag(event)
    assert win.canvas.coords(tbl_id) != before
