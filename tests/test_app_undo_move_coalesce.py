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
import json

from AutoML import AutoMLApp
from mainappsrc.managers.undo_manager import UndoRedoManager


class AppUndoMoveCoalesceTests(unittest.TestCase):
    def _make_app(self):
        app = AutoMLApp.__new__(AutoMLApp)
        app.undo_manager = UndoRedoManager(app)
        state = {"diagrams": [{"objects": [{"x": 0.0, "y": 0.0}]}]}
        app._state = state

        def export_model_data(include_versions: bool = False):
            return json.loads(json.dumps(app._state))

        app.export_model_data = export_model_data
        app.push_undo_state = AutoMLApp.push_undo_state.__get__(app)
        return app

    def test_strategies_only_store_first_and_last(self):
        for strat in ("v1", "v2", "v3", "v4"):
            with self.subTest(strategy=strat):
                app = self._make_app()
                base_len = len(app.undo_manager._undo_stack)
                app.push_undo_state(strategy=strat)
                for i in range(1, 5):
                    app._state["diagrams"][0]["objects"][0]["x"] = float(i)
                    app._state["diagrams"][0]["objects"][0]["y"] = float(i)
                    app.push_undo_state(strategy=strat)
                self.assertEqual(len(app.undo_manager._undo_stack), base_len + 2)

    def test_undo_redo_restore_endpoints(self):
        from mainappsrc.models.sysml.sysml_repository import SysMLRepository, SysMLDiagram

        for strat in ("v1", "v2", "v3", "v4"):
            with self.subTest(strategy=strat):
                SysMLRepository.reset_instance()
                repo = SysMLRepository.get_instance()
                diag = SysMLDiagram(diag_id="d", diag_type="Use Case Diagram")
                repo.diagrams[diag.diag_id] = diag
                diag.objects.append({"obj_id": 1, "obj_type": "Block", "x": 0.0, "y": 0.0})

                app = AutoMLApp.__new__(AutoMLApp)
                app.undo_manager = UndoRedoManager(app)
                app.export_model_data = lambda include_versions=False: repo.to_dict()
                app.apply_model_data = lambda data: repo.from_dict(data)
                app.push_undo_state = AutoMLApp.push_undo_state.__get__(app)
                app.undo = AutoMLApp.undo.__get__(app)
                app.redo = AutoMLApp.redo.__get__(app)
                app.diagram_tabs = {}
                app.refresh_all = lambda: None

                app.push_undo_state(strategy=strat)
                for i in range(1, 5):
                    diag.objects[0]["x"] = float(i)
                    diag.objects[0]["y"] = float(i)
                    app.push_undo_state(strategy=strat)

                app.undo(strategy=strat)
                self.assertEqual(repo.diagrams[diag.diag_id].objects[0]["x"], 0.0)
                self.assertEqual(repo.diagrams[diag.diag_id].objects[0]["y"], 0.0)

                app.redo(strategy=strat)
                self.assertEqual(repo.diagrams[diag.diag_id].objects[0]["x"], 4.0)
                self.assertEqual(repo.diagrams[diag.diag_id].objects[0]["y"], 4.0)


if __name__ == "__main__":
    unittest.main()
