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

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from AutoML import AutoMLApp
from mainappsrc.models.sysml.sysml_repository import SysMLRepository
from mainappsrc.managers.undo_manager import UndoRedoManager


class AppUndoTaskMultistepTests(unittest.TestCase):
    def _make_app_repo(self):
        SysMLRepository.reset_instance()
        repo = SysMLRepository.get_instance()
        diag = repo.create_diagram("Governance Diagram", name="Gov")
        app = AutoMLApp.__new__(AutoMLApp)
        app.undo_manager = UndoRedoManager(app)
        app.export_model_data = lambda include_versions=False: repo.to_dict()
        app.apply_model_data = lambda data: repo.from_dict(data)
        app.push_undo_state = AutoMLApp.push_undo_state.__get__(app)
        app.undo = AutoMLApp.undo.__get__(app)
        app.redo = AutoMLApp.redo.__get__(app)
        app.diagram_tabs = {}
        app.refresh_all = lambda: None
        return app, repo, diag

    def test_task_add_move_rename_resize_move_rename_undo_redo(self):
        for strat in ("v1", "v2", "v3", "v4"):
            with self.subTest(strategy=strat):
                app, repo, diag = self._make_app_repo()

                app.push_undo_state(strategy=strat)
                obj = {
                    "obj_id": 1,
                    "obj_type": "Task",
                    "user_name": "T1",
                    "x": 1.0,
                    "y": 1.0,
                    "width": 10.0,
                    "height": 10.0,
                }
                diag.objects.append(obj)

                # Move to position B
                app.push_undo_state(strategy=strat)
                obj["x"], obj["y"] = 5.0, 5.0

                # Rename
                app.push_undo_state(strategy=strat)
                obj["user_name"] = "N1"

                # Resize
                app.push_undo_state(strategy=strat)
                obj["width"], obj["height"] = 20.0, 20.0

                # Move again
                app.push_undo_state(strategy=strat)
                obj["x"], obj["y"] = 8.0, 8.0

                # Rename again
                app.push_undo_state(strategy=strat)
                obj["user_name"] = "N2"

                # Undo rename 2
                app.undo(strategy=strat)
                obj = repo.diagrams[diag.diag_id].objects[0]
                self.assertEqual(obj["user_name"], "N1")
                self.assertEqual((obj["x"], obj["y"]), (8.0, 8.0))
                self.assertEqual((obj["width"], obj["height"]), (20.0, 20.0))

                # Undo move to C
                app.undo(strategy=strat)
                obj = repo.diagrams[diag.diag_id].objects[0]
                self.assertEqual((obj["x"], obj["y"]), (5.0, 5.0))
                self.assertEqual(obj["user_name"], "N1")
                self.assertEqual((obj["width"], obj["height"]), (20.0, 20.0))

                # Undo resize
                app.undo(strategy=strat)
                obj = repo.diagrams[diag.diag_id].objects[0]
                self.assertEqual((obj["width"], obj["height"]), (10.0, 10.0))
                self.assertEqual(obj["user_name"], "N1")
                self.assertEqual((obj["x"], obj["y"]), (5.0, 5.0))

                # Undo rename 1
                app.undo(strategy=strat)
                obj = repo.diagrams[diag.diag_id].objects[0]
                self.assertEqual(obj["user_name"], "T1")
                self.assertEqual((obj["x"], obj["y"]), (5.0, 5.0))

                # Undo move to B
                app.undo(strategy=strat)
                obj = repo.diagrams[diag.diag_id].objects[0]
                self.assertEqual((obj["x"], obj["y"]), (1.0, 1.0))

                # Undo addition
                app.undo(strategy=strat)
                self.assertEqual(len(repo.diagrams[diag.diag_id].objects), 0)

                # Redo addition
                app.redo(strategy=strat)
                obj = repo.diagrams[diag.diag_id].objects[0]
                self.assertEqual((obj["x"], obj["y"]), (1.0, 1.0))
                self.assertEqual(obj["user_name"], "T1")
                self.assertEqual((obj["width"], obj["height"]), (10.0, 10.0))

                # Redo move to B
                app.redo(strategy=strat)
                obj = repo.diagrams[diag.diag_id].objects[0]
                self.assertEqual((obj["x"], obj["y"]), (5.0, 5.0))

                # Redo rename 1
                app.redo(strategy=strat)
                obj = repo.diagrams[diag.diag_id].objects[0]
                self.assertEqual(obj["user_name"], "N1")

                # Redo resize
                app.redo(strategy=strat)
                obj = repo.diagrams[diag.diag_id].objects[0]
                self.assertEqual((obj["width"], obj["height"]), (20.0, 20.0))

                # Redo move to C
                app.redo(strategy=strat)
                obj = repo.diagrams[diag.diag_id].objects[0]
                self.assertEqual((obj["x"], obj["y"]), (8.0, 8.0))

                # Redo rename 2
                app.redo(strategy=strat)
                obj = repo.diagrams[diag.diag_id].objects[0]
                self.assertEqual(obj["user_name"], "N2")
