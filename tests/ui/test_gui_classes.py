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
import os
import sys
import inspect
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from gui.toolboxes import TC2FIWindow, RiskAssessmentWindow
from AutoML import AutoMLApp
from mainappsrc.managers.requirements_manager import RequirementsManagerSubApp
try:
    from gui.faults_gui import FaultsWindow
except Exception:  # pragma: no cover - optional dependency
    FaultsWindow = None

class RowDialogMethodTests(unittest.TestCase):
    def test_rowdialog_has_add_func_existing(self):
        self.assertTrue(hasattr(TC2FIWindow.RowDialog, 'add_func_existing'))


class FaultsGuiTests(unittest.TestCase):
    @unittest.skipIf(FaultsWindow is None, "faults_gui dependencies not available")
    def test_faults_window_has_double_click_handler(self):
        self.assertTrue(hasattr(FaultsWindow, 'on_table_double_clicked'))


class DoubleClickBindingTests(unittest.TestCase):
    def test_risk_assessment_double_click_binding(self):
        src = inspect.getsource(RiskAssessmentWindow.__init__)
        self.assertIn('bind("<Double-1>"', src)

    def test_product_goals_editor_double_click_binding(self):
        src = inspect.getsource(RequirementsManagerSubApp.show_product_goals_editor)
        self.assertIn('bind("<Double-1>"', src)


class ProductGoalsMatrixTests(unittest.TestCase):
    def test_matrix_has_all_columns_and_scrollbars(self):
        src = inspect.getsource(RequirementsManagerSubApp.show_safety_goals_matrix)
        for col in [
            'FTTI',
            'Acc Rate',
            'On Hours',
            'Val Target',
            'Profile',
            'Val Desc',
            'Acceptance',
            'Description',
        ]:
            self.assertIn(col, src)
        self.assertIn('xscrollcommand', src)
        self.assertIn('yscrollcommand', src)

if __name__ == '__main__':
    unittest.main()
