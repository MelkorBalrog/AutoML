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
import unittest

from gui.architecture import GovernanceDiagramWindow, SysMLObject
from mainappsrc.models.sysml.sysml_repository import SysMLRepository


class DummyCanvas:
    def canvasx(self, x):
        return x

    def canvasy(self, y):
        return y

    def configure(self, **kwargs):
        pass


class GovernanceTraceRelationshipTests(unittest.TestCase):
    def setUp(self):
        SysMLRepository.reset_instance()
        self.repo = SysMLRepository.get_instance()
        from gui import architecture

        self._orig_conn_dialog = architecture.ConnectionDialog

    def tearDown(self):
        from gui import architecture

        architecture.ConnectionDialog = self._orig_conn_dialog
        SysMLRepository.reset_instance()

    def _create_window(self, src, dst, diag):
        win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
        win.repo = self.repo
        win.diagram_id = diag.diag_id
        win.zoom = 1
        win.canvas = DummyCanvas()
        win.find_object = lambda x, y, prefer_port=False: src if win.start is None else dst
        win.validate_connection = GovernanceDiagramWindow.validate_connection.__get__(
            win, GovernanceDiagramWindow
        )
        win.update_property_view = lambda: None
        win.redraw = lambda: None
        win.current_tool = "Trace"
        win.start = None
        win.temp_line_end = None
        win.selected_obj = None
        win.connections = []
        win._sync_to_repository = lambda: None
        from gui import architecture

        architecture.ConnectionDialog = lambda *args, **kwargs: None
        return win

    def test_trace_relationship_creates_bidirectional_link(self):
        repo = self.repo
        e1 = repo.create_element("Block", name="E1")
        e2 = repo.create_element("Block", name="E2")
        diag = repo.create_diagram("Governance Diagram", name="Gov")
        repo.add_element_to_diagram(diag.diag_id, e1.elem_id)
        repo.add_element_to_diagram(diag.diag_id, e2.elem_id)
        o1 = SysMLObject(
            1,
            "Work Product",
            0,
            0,
            element_id=e1.elem_id,
            properties={"name": "WP1"},
        )
        o2 = SysMLObject(
            2,
            "Work Product",
            0,
            100,
            element_id=e2.elem_id,
            properties={"name": "WP2"},
        )
        diag.objects = [o1.__dict__, o2.__dict__]
        win = self._create_window(o1, o2, diag)
        event1 = types.SimpleNamespace(x=0, y=0, state=0)
        GovernanceDiagramWindow.on_left_press(win, event1)
        event2 = types.SimpleNamespace(x=0, y=100, state=0)
        GovernanceDiagramWindow.on_left_press(win, event2)
        conn = win.connections[0]
        self.assertEqual(conn.conn_type, "Trace")
        self.assertEqual(conn.arrow, "both")
        rel_types = {r.rel_type for r in repo.relationships}
        self.assertEqual(rel_types, {"Trace"})
        self.assertEqual(len(repo.relationships), 2)

    def test_trace_between_requirements_disallowed(self):
        repo = self.repo
        diag = repo.create_diagram("Governance Diagram", name="Gov")
        from analysis.models import REQUIREMENT_WORK_PRODUCTS

        wp_name = next(iter(REQUIREMENT_WORK_PRODUCTS))
        e1 = repo.create_element("Block", name="E1")
        e2 = repo.create_element("Block", name="E2")
        o1 = SysMLObject(
            1,
            "Work Product",
            0,
            0,
            element_id=e1.elem_id,
            properties={"name": wp_name},
        )
        o2 = SysMLObject(
            2,
            "Work Product",
            0,
            100,
            element_id=e2.elem_id,
            properties={"name": wp_name},
        )
        win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
        win.repo = repo
        win.diagram_id = diag.diag_id
        valid, msg = GovernanceDiagramWindow.validate_connection(win, o1, o2, "Trace")
        self.assertFalse(valid)
        self.assertIn("Requirement work products", msg)

    def test_trace_between_safety_analyses_disallowed(self):
        repo = self.repo
        diag = repo.create_diagram("Governance Diagram", name="Gov")
        e1 = repo.create_element("Block", name="E1")
        e2 = repo.create_element("Block", name="E2")
        o1 = SysMLObject(
            1,
            "Work Product",
            0,
            0,
            element_id=e1.elem_id,
            properties={"name": "FMEA"},
        )
        o2 = SysMLObject(
            2,
            "Work Product",
            0,
            100,
            element_id=e2.elem_id,
            properties={"name": "FTA"},
        )
        win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
        win.repo = repo
        win.diagram_id = diag.diag_id
        valid, msg = GovernanceDiagramWindow.validate_connection(win, o1, o2, "Trace")
        self.assertFalse(valid)
        self.assertIn("safety analysis", msg)

    def test_used_between_dependent_analyses_allowed(self):
        repo = self.repo
        diag = repo.create_diagram("Governance Diagram", name="Gov")
        e1 = repo.create_element("Block", name="E1")
        e2 = repo.create_element("Block", name="E2")
        o1 = SysMLObject(
            1,
            "Work Product",
            0,
            0,
            element_id=e1.elem_id,
            properties={"name": "Reliability Analysis"},
        )
        o2 = SysMLObject(
            2,
            "Work Product",
            0,
            100,
            element_id=e2.elem_id,
            properties={"name": "FMEA"},
        )
        win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
        win.repo = repo
        win.diagram_id = diag.diag_id
        valid, msg = GovernanceDiagramWindow.validate_connection(win, o1, o2, "Used By")
        self.assertTrue(valid)

    def test_used_between_safety_analyses_requires_dependency(self):
        repo = self.repo
        diag = repo.create_diagram("Governance Diagram", name="Gov")
        e1 = repo.create_element("Block", name="E1")
        e2 = repo.create_element("Block", name="E2")
        e3 = repo.create_element("Block", name="E3")
        fmea = SysMLObject(
            1,
            "Work Product",
            0,
            0,
            element_id=e1.elem_id,
            properties={"name": "FMEA"},
        )
        fta = SysMLObject(
            2,
            "Work Product",
            0,
            100,
            element_id=e2.elem_id,
            properties={"name": "FTA"},
        )
        threat = SysMLObject(
            3,
            "Work Product",
            0,
            200,
            element_id=e3.elem_id,
            properties={"name": "Threat Analysis"},
        )
        win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
        win.repo = repo
        win.diagram_id = diag.diag_id
        valid, msg = GovernanceDiagramWindow.validate_connection(win, fmea, fta, "Used By")
        self.assertFalse(valid)
        self.assertIn("Propagate", msg)
        valid, msg = GovernanceDiagramWindow.validate_connection(win, fmea, threat, "Used By")
        self.assertFalse(valid)
        self.assertIn("metamodel dependency", msg)

    def test_used_allows_odd_to_scenario_library(self):
        repo = self.repo
        diag = repo.create_diagram("Governance Diagram", name="Gov")
        e1 = repo.create_element("Block", name="E1")
        e2 = repo.create_element("Block", name="E2")
        odd = SysMLObject(
            1,
            "Work Product",
            0,
            0,
            element_id=e1.elem_id,
            properties={"name": "ODD"},
        )
        scenario_lib = SysMLObject(
            2,
            "Work Product",
            0,
            100,
            element_id=e2.elem_id,
            properties={"name": "Scenario Library"},
        )
        win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
        win.repo = repo
        win.diagram_id = diag.diag_id
        for rel in ["Used By", "Used after Review", "Used after Approval"]:
            valid, _ = GovernanceDiagramWindow.validate_connection(
                win, odd, scenario_lib, rel
            )
            self.assertTrue(valid)

    def test_used_allows_scenario_library_to_hazop(self):
        repo = self.repo
        diag = repo.create_diagram("Governance Diagram", name="Gov")
        e1 = repo.create_element("Block", name="E1")
        e2 = repo.create_element("Block", name="E2")
        scenario_lib = SysMLObject(
            1,
            "Work Product",
            0,
            0,
            element_id=e1.elem_id,
            properties={"name": "Scenario Library"},
        )
        hazop = SysMLObject(
            2,
            "Work Product",
            0,
            100,
            element_id=e2.elem_id,
            properties={"name": "HAZOP"},
        )
        win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
        win.repo = repo
        win.diagram_id = diag.diag_id
        for rel in ["Used By", "Used after Review", "Used after Approval"]:
            valid, _ = GovernanceDiagramWindow.validate_connection(
                win, scenario_lib, hazop, rel
            )
            self.assertTrue(valid)

    def test_used_disallows_scenario_library_to_odd(self):
        repo = self.repo
        diag = repo.create_diagram("Governance Diagram", name="Gov")
        e1 = repo.create_element("Block", name="E1")
        e2 = repo.create_element("Block", name="E2")
        scenario_lib = SysMLObject(
            1,
            "Work Product",
            0,
            0,
            element_id=e1.elem_id,
            properties={"name": "Scenario Library"},
        )
        odd = SysMLObject(
            2,
            "Work Product",
            0,
            100,
            element_id=e2.elem_id,
            properties={"name": "ODD"},
        )
        win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
        win.repo = repo
        win.diagram_id = diag.diag_id
        for rel in ["Used By", "Used after Review", "Used after Approval"]:
            valid, msg = GovernanceDiagramWindow.validate_connection(
                win, scenario_lib, odd, rel
            )
            self.assertFalse(valid)
            self.assertIn("metamodel dependency", msg)


if __name__ == "__main__":
    unittest.main()

