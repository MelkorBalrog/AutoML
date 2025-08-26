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

import unittest
import types
import os
import sys

# Provide dummy PIL modules so AutoML can be imported without Pillow
sys.modules.setdefault("PIL", types.ModuleType("PIL"))
sys.modules.setdefault("PIL.Image", types.ModuleType("PIL.Image"))
sys.modules.setdefault("PIL.ImageDraw", types.ModuleType("PIL.ImageDraw"))
sys.modules.setdefault("PIL.ImageFont", types.ModuleType("PIL.ImageFont"))
sys.modules.setdefault("PIL.ImageTk", types.ModuleType("PIL.ImageTk"))

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from AutoML import AutoMLApp, FaultTreeNode
from mainappsrc.models.sysml.sysml_repository import SysMLRepository
from mainappsrc.managers.undo_manager import UndoRedoManager

class FTAUndoRedoTests(unittest.TestCase):
    def setUp(self):
        # minimal app without Tk initialization
        self.app = AutoMLApp.__new__(AutoMLApp)
        self.app.top_events = []
        self.app.root_node = None
        self.app.selected_node = None
        # stub analysis tree and view updates
        self.app.analysis_tree = types.SimpleNamespace(selection=lambda: ())
        self.app.update_views = lambda: None
        self.app.undo_manager = UndoRedoManager(self.app)
        # minimal persistence of state for undo/redo
        self.app.export_model_data = lambda include_versions=False: {
            "top_events": [n.to_dict() for n in self.app.top_events],
            "root_node": self.app.root_node.to_dict() if self.app.root_node else None,
        }
        def apply_model_data(state):
            self.app.top_events = [FaultTreeNode.from_dict(d) for d in state["top_events"]]
            self.app.root_node = (
                FaultTreeNode.from_dict(state["root_node"]) if state["root_node"] else None
            )
        self.app.apply_model_data = apply_model_data
        SysMLRepository.reset_instance()

    def test_undo_redo_top_event_creation_and_deletion(self):
        self.app.create_top_event_for_malfunction("M1")
        self.assertEqual(len(self.app.top_events), 1)
        self.app.undo()
        self.assertEqual(len(self.app.top_events), 0)
        self.app.redo()
        self.assertEqual(len(self.app.top_events), 1)
        self.app.delete_top_events_for_malfunction("M1")
        self.assertEqual(len(self.app.top_events), 0)
        self.app.undo()
        self.assertEqual(len(self.app.top_events), 1)
        self.app.redo()
        self.assertEqual(len(self.app.top_events), 0)

    def test_undo_redo_add_node(self):
        self.app.create_top_event_for_malfunction("M1")
        self.app.selected_node = self.app.root_node
        self.app.add_node_of_type("GATE")
        self.assertEqual(len(self.app.root_node.children), 1)
        self.app.undo()
        self.assertEqual(len(self.app.root_node.children), 0)
        self.app.redo()
        self.assertEqual(len(self.app.root_node.children), 1)

if __name__ == "__main__":
    unittest.main()
