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

from gui.gsn_diagram_window import GSNDiagramWindow, GSNNode, GSNDiagram


def _make_window(app, diag):
    win = object.__new__(GSNDiagramWindow)
    win.app = app
    win.diagram = diag
    win.id_to_node = {n.unique_id: n for n in diag.nodes}
    win.canvas = types.SimpleNamespace(
        delete=lambda *a, **k: None,
        find_overlapping=lambda *a, **k: [],
        find_closest=lambda *a, **k: [],
        bbox=lambda *a, **k: None,
        gettags=lambda i: [],
    )
    win.refresh = lambda: None
    return win


def test_gsn_copy_paste_clones_with_independent_positions():
    root1 = GSNNode("A", "Goal", x=0, y=0)
    diag1 = GSNDiagram(root1)
    app = types.SimpleNamespace(gsn_diagrams=[diag1], gsn_modules=[])
    app.diagram_clipboard = types.SimpleNamespace(
        diagram_clipboard=None,
        diagram_clipboard_type=None,
        clipboard_node=None,
        cut_mode=False,
        clipboard_relation=None,
        diagram_clipboard_parent_name=None,
    )
    win1 = _make_window(app, diag1)

    snap1 = win1._clone_node_strategy1(root1)
    snap2 = win1._clone_node_strategy2(root1)
    snap3 = win1._clone_node_strategy3(root1)
    snap4 = win1._clone_node_strategy4(root1)
    assert snap1 is snap2 is snap3 is snap4 is root1
    win1.selected_node = root1
    win1.copy_selected()
    assert app.diagram_clipboard.diagram_clipboard is root1
    assert app.diagram_clipboard.diagram_clipboard_type == "GSN"

    root2 = GSNNode("B", "Goal", x=0, y=0)
    diag2 = GSNDiagram(root2)
    app.gsn_diagrams.append(diag2)
    win2 = _make_window(app, diag2)

    clones = [
        win2._reconstruct_node_strategy1(root1),
        win2._reconstruct_node_strategy2(root1),
        win2._reconstruct_node_strategy3(root1),
        win2._reconstruct_node_strategy4(root1),
    ]
    for c in clones:
        assert c is not root1
        assert c.original is root1

    win2.paste_selected()
    clone = diag2.nodes[-1]
    assert clone is not root1
    assert clone.original is root1
    assert (clone.x, clone.y) == (root1.x + 20, root1.y + 20)

    clone.x += 30
    clone.y += 40
    assert (root1.x, root1.y) == (0, 0)

    clone.description = "new"
    original = clone.original
    attrs = (
        "user_name",
        "description",
        "work_product",
        "evidence_link",
        "spi_target",
        "manager_notes",
    )
    for n in diag1.nodes + diag2.nodes:
        if getattr(n, "original", n) is original:
            for attr in attrs:
                setattr(n, attr, getattr(clone, attr))
    assert root1.description == "new"
