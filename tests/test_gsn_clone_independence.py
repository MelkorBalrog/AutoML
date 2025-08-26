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
import os
import sys

sys.modules.setdefault("PIL", types.ModuleType("PIL"))
sys.modules.setdefault("PIL.Image", types.ModuleType("PIL.Image"))
sys.modules.setdefault("PIL.ImageDraw", types.ModuleType("PIL.ImageDraw"))
sys.modules.setdefault("PIL.ImageFont", types.ModuleType("PIL.ImageFont"))
sys.modules.setdefault("PIL.ImageTk", types.ModuleType("PIL.ImageTk"))

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from mainappsrc.models.gsn import GSNNode, GSNDiagram
from AutoML import AutoMLApp
from mainappsrc.managers.diagram_clipboard_manager import DiagramClipboardManager


def _make_app(root, diagram):
    app = AutoMLApp.__new__(AutoMLApp)
    app.diagram_clipboard = DiagramClipboardManager(app)
    app.root_node = root
    app.top_events = []
    app.analysis_tree = types.SimpleNamespace(selection=lambda: [], item=lambda *a, **k: {})
    app.diagram_clipboard.cut_mode = False
    app.selected_node = root
    app.update_views = lambda: None
    app._find_gsn_diagram = lambda n: diagram
    return app


def test_paste_clone_is_away_and_independent():
    root = GSNNode("Root", "Goal", x=0, y=0)
    child = GSNNode("Child", "Goal", x=10, y=10)
    root.add_child(child)
    diagram = GSNDiagram(root)

    app = _make_app(root, diagram)
    app.diagram_clipboard.clipboard_node = child
    app.paste_node()

    clone = root.children[-1]
    assert clone is not child
    assert not clone.is_primary_instance

    clone.x += 50
    clone.y += 60
    AutoMLApp.sync_nodes_by_id(app, clone)

    assert (root.x, root.y) == (0, 0)
    assert (clone.x, clone.y) == (150, 160)


def test_only_name_description_notes_sync():
    root = GSNNode("Root", "Goal")
    clone = root.clone()
    diagram = GSNDiagram(root)
    diagram.add_node(clone)

    app = _make_app(root, diagram)

    clone.user_name = "C"
    clone.description = "desc"
    clone.manager_notes = "note"
    clone.spi_target = "SPI"
    AutoMLApp.sync_nodes_by_id(app, clone)

    assert (root.user_name, root.description, root.manager_notes) == ("C", "desc", "note")
    assert root.spi_target == ""
