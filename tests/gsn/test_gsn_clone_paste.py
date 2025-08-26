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

from mainappsrc.models.gsn import GSNNode, GSNDiagram
from gui.gsn_diagram_window import GSNDiagramWindow


def test_copy_paste_creates_clone():
    root = GSNNode("Root", "Goal")
    child = GSNNode("Child", "Goal")
    root.add_child(child)
    diag = GSNDiagram(root)

    app = types.SimpleNamespace()
    app.diagram_clipboard = types.SimpleNamespace(
        diagram_clipboard=None,
        diagram_clipboard_type=None,
        clipboard_node=None,
        cut_mode=False,
        clipboard_relation=None,
        diagram_clipboard_parent_name=None,
    )
    win = GSNDiagramWindow.__new__(GSNDiagramWindow)
    win.app = app
    win.diagram = diag
    win.id_to_node = {child.unique_id: child}
    win.selected_node = child
    win.refresh = lambda: None

    win.copy_selected()
    assert app.diagram_clipboard.diagram_clipboard is child

    app.sync_nodes_by_id = lambda n: setattr(n.original, "description", n.description)
    win.paste_selected()
    assert len(diag.nodes) == 2
    clone = diag.nodes[-1]
    assert clone.original is child.original
    clone.description = "updated"
    app.sync_nodes_by_id(clone)
    assert child.description == "updated"
