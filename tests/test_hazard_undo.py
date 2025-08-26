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
from AutoML import AutoMLApp
from mainappsrc.models.sysml.sysml_repository import SysMLRepository
from mainappsrc.managers.undo_manager import UndoRedoManager

class HazardSeverityUndoRedoTests(unittest.TestCase):
    def setUp(self):
        self.app = AutoMLApp.__new__(AutoMLApp)
        self.app.hazard_severity = {"H1": 1}
        self.app.hazards = ["H1"]
        self.app.hara_docs = []
        self.app.fi2tc_docs = []
        self.app.tc2fi_docs = []
        self.app.update_views = lambda: None
        self.app.undo_manager = UndoRedoManager(self.app)
        self.app.export_model_data = lambda include_versions=False: {
            "hazard_severity": self.app.hazard_severity.copy()
        }
        def apply_model_data(state):
            self.app.hazard_severity = state["hazard_severity"].copy()
        self.app.apply_model_data = apply_model_data
        SysMLRepository.reset_instance()

    def test_undo_redo_update_hazard_severity(self):
        self.app.update_hazard_severity("H1", 5)
        self.assertEqual(self.app.hazard_severity["H1"], 5)
        self.app.undo()
        self.assertEqual(self.app.hazard_severity["H1"], 1)
        self.app.redo()
        self.assertEqual(self.app.hazard_severity["H1"], 5)

if __name__ == "__main__":
    unittest.main()
