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

# Provide dummy PIL modules so AutoML can be imported without Pillow
import sys

sys.modules.setdefault("PIL", types.ModuleType("PIL"))
sys.modules.setdefault("PIL.Image", types.ModuleType("PIL.Image"))
sys.modules.setdefault("PIL.ImageTk", types.ModuleType("PIL.ImageTk"))
sys.modules.setdefault("PIL.ImageDraw", types.ModuleType("PIL.ImageDraw"))
sys.modules.setdefault("PIL.ImageFont", types.ModuleType("PIL.ImageFont"))

from mainappsrc.models.gsn import GSNNode, GSNDiagram
from gui.gsn_explorer import GSNExplorer
from AutoML import AutoMLApp
from mainappsrc.managers.undo_manager import UndoRedoManager


def test_gsn_diagram_undo_redo_rename(monkeypatch):
    root = GSNNode("G", "Goal")
    diag = GSNDiagram(root)

    app = AutoMLApp.__new__(AutoMLApp)
    app.gsn_diagrams = [diag]
    app.gsn_modules = []
    app.update_views = lambda: None
    app.undo_manager = UndoRedoManager(app)

    def export_model_data(include_versions=False):
        return {
            "gsn_diagrams": [d.to_dict() for d in app.gsn_diagrams],
            "gsn_modules": [m.to_dict() for m in app.gsn_modules],
        }

    def apply_model_data(data):
        app.gsn_diagrams = [GSNDiagram.from_dict(d) for d in data.get("gsn_diagrams", [])]
        app.gsn_modules = []

    app.export_model_data = export_model_data
    app.apply_model_data = apply_model_data
    app.push_undo_state = AutoMLApp.push_undo_state.__get__(app)
    app.undo = AutoMLApp.undo.__get__(app)
    app.redo = AutoMLApp.redo.__get__(app)

    explorer = GSNExplorer.__new__(GSNExplorer)
    explorer.app = app
    explorer.tree = types.SimpleNamespace(selection=lambda: ["i1"])
    explorer.item_map = {"i1": ("diagram", diag)}
    explorer.populate = lambda: None

    monkeypatch.setattr(
        "gui.gsn_explorer.simpledialog.askstring", lambda *a, **k: "New"
    )

    explorer.rename_item()
    assert app.gsn_diagrams[0].root.user_name == "New"

    app.undo()
    assert app.gsn_diagrams[0].root.user_name == "G"

    app.redo()
    assert app.gsn_diagrams[0].root.user_name == "New"


def test_gsn_explorer_refreshes_after_undo(monkeypatch):
    root = GSNNode("G", "Goal")
    diag = GSNDiagram(root)

    app = AutoMLApp.__new__(AutoMLApp)
    app.gsn_diagrams = [diag]
    app.gsn_modules = []
    app.update_views = lambda: None
    app.undo_manager = UndoRedoManager(app)

    def export_model_data(include_versions=False):
        return {
            "gsn_diagrams": [d.to_dict() for d in app.gsn_diagrams],
            "gsn_modules": [m.to_dict() for m in app.gsn_modules],
        }

    def apply_model_data(data):
        app.gsn_diagrams = [GSNDiagram.from_dict(d) for d in data.get("gsn_diagrams", [])]
        app.gsn_modules = []

    app.export_model_data = export_model_data
    app.apply_model_data = apply_model_data
    app.push_undo_state = AutoMLApp.push_undo_state.__get__(app)
    app.undo = AutoMLApp.undo.__get__(app)

    explorer = GSNExplorer.__new__(GSNExplorer)
    app._gsn_window = explorer
    explorer.app = app

    class DummyTree:
        def __init__(self):
            self.items = {}
            self.counter = 0
            self.selection_item = None

        def delete(self, *items):
            self.items = {}

        def get_children(self, item=""):
            return [iid for iid, meta in self.items.items() if meta["parent"] == item]

        def insert(self, parent, index, text="", image=None):
            iid = f"i{self.counter}"
            self.counter += 1
            self.items[iid] = {"parent": parent, "text": text}
            return iid

        def parent(self, item):
            return self.items[item]["parent"]

        def selection(self):
            return (self.selection_item,) if self.selection_item else ()

    explorer.tree = DummyTree()
    explorer.item_map = {}
    explorer.module_icon = None
    explorer.diagram_icon = None
    explorer.node_icons = {}
    explorer.default_node_icon = None
    explorer.populate()

    # select the diagram for renaming
    for iid, (typ, obj) in explorer.item_map.items():
        if obj is diag:
            explorer.tree.selection_item = iid
            break

    monkeypatch.setattr(
        "gui.gsn_explorer.simpledialog.askstring", lambda *a, **k: "New"
    )

    explorer.rename_item()
    assert diag.root.user_name == "New"
    assert any(meta["text"] == "New" for meta in explorer.tree.items.values())

    # ensure undo triggers explorer.refresh via refresh_all
    app.refresh_all = lambda: getattr(app, "_gsn_window").refresh()
    app.undo()

    texts = [meta["text"] for meta in explorer.tree.items.values()]
    assert "G" in texts and "New" not in texts

