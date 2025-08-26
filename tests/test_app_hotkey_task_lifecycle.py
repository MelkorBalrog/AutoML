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


class HotkeyTaskLifecycleTests(unittest.TestCase):
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
        app._undo_hotkey = AutoMLApp._undo_hotkey.__get__(app)
        app._redo_hotkey = AutoMLApp._redo_hotkey.__get__(app)
        app.diagram_tabs = {}
        app.refresh_all = lambda: None
        return app, repo, diag

    def test_task_lifecycle_via_hotkeys(self):
        for strat in ("v1", "v2", "v3", "v4"):
            with self.subTest(strategy=strat):
                app, repo, diag = self._make_app_repo()
                # ensure hotkeys use chosen strategy
                app.undo = lambda strategy=strat, _app=app: AutoMLApp.undo(_app, strategy=strat)
                app.redo = lambda strategy=strat, _app=app: AutoMLApp.redo(_app, strategy=strat)

                # baseline before adding task
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

                # Move to B
                app.push_undo_state(strategy=strat)
                obj["x"], obj["y"] = 5.0, 5.0

                # Rename
                app.push_undo_state(strategy=strat)
                obj["user_name"] = "N1"

                # Resize
                app.push_undo_state(strategy=strat)
                obj["width"], obj["height"] = 20.0, 20.0

                # Move to C
                app.push_undo_state(strategy=strat)
                obj["x"], obj["y"] = 8.0, 8.0

                # Rename again
                app.push_undo_state(strategy=strat)
                obj["user_name"] = "N2"

                # Undo rename 2
                app._undo_hotkey(None)
                obj = repo.diagrams[diag.diag_id].objects[0]
                self.assertEqual(obj["user_name"], "N1")
                self.assertEqual((obj["x"], obj["y"]), (8.0, 8.0))
                self.assertEqual((obj["width"], obj["height"]), (20.0, 20.0))

                # Undo move to C
                app._undo_hotkey(None)
                obj = repo.diagrams[diag.diag_id].objects[0]
                self.assertEqual((obj["x"], obj["y"]), (5.0, 5.0))
                self.assertEqual(obj["user_name"], "N1")
                self.assertEqual((obj["width"], obj["height"]), (20.0, 20.0))

                # Undo resize
                app._undo_hotkey(None)
                obj = repo.diagrams[diag.diag_id].objects[0]
                self.assertEqual((obj["width"], obj["height"]), (10.0, 10.0))
                self.assertEqual(obj["user_name"], "N1")
                self.assertEqual((obj["x"], obj["y"]), (5.0, 5.0))

                # Undo rename 1
                app._undo_hotkey(None)
                obj = repo.diagrams[diag.diag_id].objects[0]
                self.assertEqual(obj["user_name"], "T1")
                self.assertEqual((obj["x"], obj["y"]), (5.0, 5.0))

                # Undo move to B
                app._undo_hotkey(None)
                obj = repo.diagrams[diag.diag_id].objects[0]
                self.assertEqual((obj["x"], obj["y"]), (1.0, 1.0))

                # Undo addition
                app._undo_hotkey(None)
                self.assertEqual(len(repo.diagrams[diag.diag_id].objects), 0)

                # Redo addition
                app._redo_hotkey(None)
                obj = repo.diagrams[diag.diag_id].objects[0]
                self.assertEqual((obj["x"], obj["y"]), (1.0, 1.0))
                self.assertEqual(obj["user_name"], "T1")
                self.assertEqual((obj["width"], obj["height"]), (10.0, 10.0))

                # Redo move to B
                app._redo_hotkey(None)
                obj = repo.diagrams[diag.diag_id].objects[0]
                self.assertEqual((obj["x"], obj["y"]), (5.0, 5.0))

                # Redo rename 1
                app._redo_hotkey(None)
                obj = repo.diagrams[diag.diag_id].objects[0]
                self.assertEqual(obj["user_name"], "N1")

                # Redo resize
                app._redo_hotkey(None)
                obj = repo.diagrams[diag.diag_id].objects[0]
                self.assertEqual((obj["width"], obj["height"]), (20.0, 20.0))

                # Redo move to C
                app._redo_hotkey(None)
                obj = repo.diagrams[diag.diag_id].objects[0]
                self.assertEqual((obj["x"], obj["y"]), (8.0, 8.0))

                # Redo rename 2
                app._redo_hotkey(None)
                obj = repo.diagrams[diag.diag_id].objects[0]
                self.assertEqual(obj["user_name"], "N2")

