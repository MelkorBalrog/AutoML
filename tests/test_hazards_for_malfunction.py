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
import sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from mainappsrc.automl_core import AutoMLApp
from analysis.models import HazopDoc, HazopEntry
from mainappsrc.subapps.risk_assessment_subapp import RiskAssessmentSubApp


class HazardsForMalfunctionTests(unittest.TestCase):
    def test_returns_linked_hazards(self):
        app = AutoMLApp.__new__(AutoMLApp)
        app.risk_app = RiskAssessmentSubApp()
        entry = HazopEntry(
            function="F",
            malfunction="M",
            mtype="No/Not",
            scenario="",
            conditions="",
            hazard="HZ",
            safety=True,
            rationale="",
            covered=False,
            covered_by="",
        )
        app.hazop_docs = [HazopDoc("HZDOC", [entry])]
        self.assertEqual(app.get_hazards_for_malfunction("M"), ["HZ"])

    def test_hazop_doc_serialization_round_trip(self):
        entry = HazopEntry(
            function="F",
            malfunction="M",
            mtype="Deviation",
            scenario="S",
            conditions="C",
            hazard="HZ",
            safety=True,
            rationale="Because",
            covered=True,
            covered_by="Requirement",
            component="Comp",
        )
        doc = HazopDoc("Doc", [entry])

        data = doc.to_dict()
        restored = HazopDoc.from_dict(data)

        self.assertEqual(restored.name, doc.name)
        self.assertEqual(len(restored.entries), 1)
        self.assertTrue(restored.entries[0].safety)
        self.assertTrue(restored.entries[0].covered)
        self.assertEqual(restored.entries[0].component, "Comp")


if __name__ == "__main__":
    unittest.main()
