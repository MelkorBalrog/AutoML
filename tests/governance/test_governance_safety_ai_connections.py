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

from gui.architecture import GovernanceDiagramWindow, SysMLObject
from mainappsrc.models.sysml.sysml_repository import SysMLRepository


class GovernanceSafetyAIConnectionTests(unittest.TestCase):
    def setUp(self):
        SysMLRepository.reset_instance()
        self.repo = SysMLRepository.get_instance()

    def tearDown(self):
        SysMLRepository.reset_instance()

    def _window(self, diag):
        return types.SimpleNamespace(repo=self.repo, diagram_id=diag.diag_id)

    def _make_nodes(self):
        repo = self.repo
        e1 = repo.create_element("Block", name="E1")
        e2 = repo.create_element("Block", name="E2")
        diag = repo.create_diagram("Governance Diagram", name="Gov")
        repo.add_element_to_diagram(diag.diag_id, e1.elem_id)
        repo.add_element_to_diagram(diag.diag_id, e2.elem_id)
        gobj = SysMLObject(1, "Action", 0, 0, element_id=e1.elem_id)
        aiobj = SysMLObject(2, "AI Database", 0, 100, element_id=e2.elem_id)
        diag.objects = [gobj.__dict__, aiobj.__dict__]
        return diag, gobj, aiobj

    def _make_ai_pair(self, src_type, dst_type):
        repo = self.repo
        e1 = repo.create_element("Block", name="E1")
        e2 = repo.create_element("Block", name="E2")
        diag = repo.create_diagram("Governance Diagram", name="Gov")
        repo.add_element_to_diagram(diag.diag_id, e1.elem_id)
        repo.add_element_to_diagram(diag.diag_id, e2.elem_id)
        src = SysMLObject(1, src_type, 0, 0, element_id=e1.elem_id)
        dst = SysMLObject(2, dst_type, 0, 100, element_id=e2.elem_id)
        diag.objects = [src.__dict__, dst.__dict__]
        return diag, src, dst

    def test_safety_ai_relationship_between_governance_and_ai(self):
        diag, gobj, aiobj = self._make_nodes()
        win = self._window(diag)
        valid, _ = GovernanceDiagramWindow.validate_connection(win, gobj, aiobj, "Annotation")
        self.assertFalse(valid)
        valid, _ = GovernanceDiagramWindow.validate_connection(win, aiobj, gobj, "Annotation")
        self.assertFalse(valid)

    def test_flow_from_governance_to_ai_allowed(self):
        diag, gobj, aiobj = self._make_nodes()
        win = self._window(diag)
        valid, _ = GovernanceDiagramWindow.validate_connection(win, gobj, aiobj, "Flow")
        self.assertTrue(valid)

    def test_ai_training_direction(self):
        diag, db, ann = self._make_ai_pair("AI Database", "ANN")
        win = self._window(diag)
        valid, _ = GovernanceDiagramWindow.validate_connection(win, db, ann, "AI training")
        self.assertTrue(valid)
        diag, ann, db = self._make_ai_pair("ANN", "AI Database")
        win = self._window(diag)
        valid, _ = GovernanceDiagramWindow.validate_connection(win, ann, db, "AI training")
        self.assertFalse(valid)

    def test_model_evaluation_direction(self):
        diag, ann, db = self._make_ai_pair("ANN", "AI Database")
        win = self._window(diag)
        valid, _ = GovernanceDiagramWindow.validate_connection(win, ann, db, "Model evaluation")
        self.assertTrue(valid)
        diag, db, ann = self._make_ai_pair("AI Database", "ANN")
        win = self._window(diag)
        valid, _ = GovernanceDiagramWindow.validate_connection(win, db, ann, "Model evaluation")
        self.assertFalse(valid)

    def test_tune_connection(self):
        diag, db, ann = self._make_ai_pair("AI Database", "ANN")
        win = self._window(diag)
        valid, _ = GovernanceDiagramWindow.validate_connection(win, db, ann, "Tune")
        self.assertTrue(valid)
        valid, _ = GovernanceDiagramWindow.validate_connection(win, ann, db, "Tune")
        self.assertTrue(valid)

    def test_hyperparameter_validation_connection(self):
        diag, db, ann = self._make_ai_pair("AI Database", "ANN")
        win = self._window(diag)
        valid, _ = GovernanceDiagramWindow.validate_connection(win, db, ann, "Hyperparameter Validation")
        self.assertTrue(valid)
        valid, _ = GovernanceDiagramWindow.validate_connection(
            win, ann, db, "Hyperparameter Validation"
        )
        self.assertTrue(valid)

    def test_field_risk_evaluation_enforces_allowed_targets(self):
        # Valid connection: AI Database -> Data acquisition
        diag, db, da = self._make_ai_pair("AI Database", "Data acquisition")
        win = self._window(diag)
        valid, _ = GovernanceDiagramWindow.validate_connection(
            win, db, da, "Field risk evaluation"
        )
        self.assertTrue(valid)

        # Invalid connection: AI Database -> Work Product
        repo = self.repo
        e1 = repo.create_element("Block", name="E1")
        e2 = repo.create_element("Block", name="E2")
        diag2 = repo.create_diagram("Governance Diagram", name="Gov2")
        repo.add_element_to_diagram(diag2.diag_id, e1.elem_id)
        repo.add_element_to_diagram(diag2.diag_id, e2.elem_id)
        db_obj = SysMLObject(1, "AI Database", 0, 0, element_id=e1.elem_id)
        wp_obj = SysMLObject(2, "Work Product", 0, 100, element_id=e2.elem_id)
        diag2.objects = [db_obj.__dict__, wp_obj.__dict__]
        win2 = self._window(diag2)
        valid, _ = GovernanceDiagramWindow.validate_connection(
            win2, db_obj, wp_obj, "Field risk evaluation"
        )
        self.assertFalse(valid)


if __name__ == "__main__":
    unittest.main()
