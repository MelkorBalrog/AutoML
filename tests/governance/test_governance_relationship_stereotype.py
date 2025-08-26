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
import sys

# Provide dummy PIL modules so tests can run without the Pillow dependency.
sys.modules.setdefault("PIL", types.ModuleType("PIL"))
sys.modules.setdefault("PIL.Image", types.ModuleType("PIL.Image"))
sys.modules.setdefault("PIL.ImageTk", types.ModuleType("PIL.ImageTk"))

from gui.architecture import GovernanceDiagramWindow, SysMLObject
from gui.toolboxes import allowed_action_labels
from gui.stpa_window import StpaWindow
from analysis.models import StpaDoc
from mainappsrc.models.sysml.sysml_repository import SysMLRepository
from analysis.safety_management import (
    SafetyManagementToolbox,
    SafetyWorkProduct,
    SAFETY_ANALYSIS_WORK_PRODUCTS,
)


class DummyCanvas:
    def canvasx(self, x):
        return x

    def canvasy(self, y):
        return y

    def configure(self, **kwargs):
        pass


class GovernanceRelationshipStereotypeTests(unittest.TestCase):
    def setUp(self):
        SysMLRepository.reset_instance()
        self.repo = SysMLRepository.get_instance()
        from gui import architecture
        self._orig_conn_dialog = architecture.ConnectionDialog

    def tearDown(self):
        from gui import architecture
        architecture.ConnectionDialog = self._orig_conn_dialog
        SysMLRepository.reset_instance()

    def _create_window(self, tool, src, dst, diag):
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
        win.current_tool = tool
        win.start = None
        win.temp_line_end = None
        win.selected_obj = None
        win.connections = []
        win._sync_to_repository = lambda: None
        from gui import architecture
        architecture.ConnectionDialog = lambda *args, **kwargs: None
        return win

    def test_propagate_relationship_stereotype(self):
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
            properties={"name": "Risk Assessment"},
        )
        o2 = SysMLObject(
            2,
            "Work Product",
            0,
            100,
            element_id=e2.elem_id,
            properties={"name": "FTA"},
        )
        diag.objects = [o1.__dict__, o2.__dict__]
        win = self._create_window("Propagate", o1, o2, diag)
        event1 = types.SimpleNamespace(x=0, y=0, state=0)
        GovernanceDiagramWindow.on_left_press(win, event1)
        event2 = types.SimpleNamespace(x=0, y=100, state=0)
        GovernanceDiagramWindow.on_left_press(win, event2)
        self.assertEqual(repo.relationships[0].stereotype, "propagate")

    def test_used_by_relationship_stereotype(self):
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
            properties={"name": "Architecture Diagram"},
        )
        o2 = SysMLObject(
            2,
            "Work Product",
            0,
            100,
            element_id=e2.elem_id,
            properties={"name": "FTA"},
        )
        diag.objects = [o1.__dict__, o2.__dict__]
        win = self._create_window("Used By", o1, o2, diag)
        event1 = types.SimpleNamespace(x=0, y=0, state=0)
        GovernanceDiagramWindow.on_left_press(win, event1)
        event2 = types.SimpleNamespace(x=0, y=100, state=0)
        GovernanceDiagramWindow.on_left_press(win, event2)
        self.assertEqual(repo.relationships[0].stereotype, "used by")

    def test_used_after_review_relationship_stereotype(self):
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
            properties={"name": "Architecture Diagram"},
        )
        o2 = SysMLObject(
            2,
            "Work Product",
            0,
            100,
            element_id=e2.elem_id,
            properties={"name": "FTA"},
        )
        diag.objects = [o1.__dict__, o2.__dict__]
        win = self._create_window("Used after Review", o1, o2, diag)
        event1 = types.SimpleNamespace(x=0, y=0, state=0)
        GovernanceDiagramWindow.on_left_press(win, event1)
        event2 = types.SimpleNamespace(x=0, y=100, state=0)
        GovernanceDiagramWindow.on_left_press(win, event2)
        self.assertEqual(repo.relationships[0].stereotype, "used after review")

    def test_used_after_approval_relationship_stereotype(self):
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
            properties={"name": "Architecture Diagram"},
        )
        o2 = SysMLObject(
            2,
            "Work Product",
            0,
            100,
            element_id=e2.elem_id,
            properties={"name": "FTA"},
        )
        diag.objects = [o1.__dict__, o2.__dict__]
        win = self._create_window("Used after Approval", o1, o2, diag)
        event1 = types.SimpleNamespace(x=0, y=0, state=0)
        GovernanceDiagramWindow.on_left_press(win, event1)
        event2 = types.SimpleNamespace(x=0, y=100, state=0)
        GovernanceDiagramWindow.on_left_press(win, event2)
        self.assertEqual(repo.relationships[0].stereotype, "used after approval")

    def test_used_relations_reject_non_analysis_targets(self):
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
            properties={"name": "FTA"},
        )
        o2 = SysMLObject(
            2,
            "Work Product",
            0,
            100,
            element_id=e2.elem_id,
            properties={"name": "Architecture Diagram"},
        )
        diag.objects = [o1.__dict__, o2.__dict__]
        for rel in ["Used By", "Used after Review", "Used after Approval"]:
            repo.relationships.clear()
            win = self._create_window(rel, o1, o2, diag)
            event1 = types.SimpleNamespace(x=0, y=0, state=0)
            GovernanceDiagramWindow.on_left_press(win, event1)
            event2 = types.SimpleNamespace(x=0, y=100, state=0)
            GovernanceDiagramWindow.on_left_press(win, event2)
            self.assertEqual(repo.relationships, [])

    def test_stpa_to_architecture_used_relationships(self):
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
            properties={"name": "STPA"},
        )
        o2 = SysMLObject(
            2,
            "Work Product",
            0,
            100,
            element_id=e2.elem_id,
            properties={"name": "Architecture Diagram"},
        )
        diag.objects = [o1.__dict__, o2.__dict__]
        for rel in ["Used By", "Used after Review", "Used after Approval"]:
            repo.relationships.clear()
            win = self._create_window(rel, o1, o2, diag)
            event1 = types.SimpleNamespace(x=0, y=0, state=0)
            GovernanceDiagramWindow.on_left_press(win, event1)
            event2 = types.SimpleNamespace(x=0, y=100, state=0)
            GovernanceDiagramWindow.on_left_press(win, event2)
            self.assertEqual(repo.relationships[0].stereotype, rel.lower())

    def test_used_relationship_validation(self):
        repo = self.repo
        diag = repo.create_diagram("Governance Diagram", name="Gov")
        e1 = repo.create_element("Block", name="E1")
        e2 = repo.create_element("Block", name="E2")
        win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
        win.repo = repo
        win.diagram_id = diag.diag_id
        rels = ["Used By", "Used after Review", "Used after Approval"]
        for rel in rels:
            o1 = SysMLObject(
                1,
                "Work Product",
                0,
                0,
                element_id=e1.elem_id,
                properties={"name": "Mission Profile"},
            )
            o2 = SysMLObject(
                2,
                "Work Product",
                0,
                100,
                element_id=e2.elem_id,
                properties={"name": "Architecture Diagram"},
            )
            valid, _ = GovernanceDiagramWindow.validate_connection(win, o1, o2, rel)
            self.assertFalse(valid)
            o2 = SysMLObject(
                2,
                "Work Product",
                0,
                100,
                element_id=e2.elem_id,
                properties={"name": "FTA"},
            )
            valid, _ = GovernanceDiagramWindow.validate_connection(win, o1, o2, rel)
            self.assertTrue(valid)

    def test_odd_scenario_library_used_relationships(self):
        repo = self.repo
        diag = repo.create_diagram("Governance Diagram", name="Gov")
        e1 = repo.create_element("Block", name="E1")
        e2 = repo.create_element("Block", name="E2")
        win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
        win.repo = repo
        win.diagram_id = diag.diag_id
        rels = ["Used By", "Used after Review", "Used after Approval"]
        for rel in rels:
            o1 = SysMLObject(
                1,
                "Work Product",
                0,
                0,
                element_id=e1.elem_id,
                properties={"name": "ODD"},
            )
            o2 = SysMLObject(
                2,
                "Work Product",
                0,
                100,
                element_id=e2.elem_id,
                properties={"name": "Scenario Library"},
            )
            valid, _ = GovernanceDiagramWindow.validate_connection(win, o1, o2, rel)
            self.assertTrue(valid)

    def test_scenario_library_odd_used_relationships_invalid(self):
        repo = self.repo
        diag = repo.create_diagram("Governance Diagram", name="Gov")
        e1 = repo.create_element("Block", name="E1")
        e2 = repo.create_element("Block", name="E2")
        win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
        win.repo = repo
        win.diagram_id = diag.diag_id
        rels = ["Used By", "Used after Review", "Used after Approval"]
        for rel in rels:
            o1 = SysMLObject(
                1,
                "Work Product",
                0,
                0,
                element_id=e1.elem_id,
                properties={"name": "Scenario Library"},
            )
            o2 = SysMLObject(
                2,
                "Work Product",
                0,
                100,
                element_id=e2.elem_id,
                properties={"name": "ODD"},
            )
            valid, _ = GovernanceDiagramWindow.validate_connection(win, o1, o2, rel)
            self.assertFalse(valid)

    def test_analysis_targets_inputs_for_odd_scenario_library(self):
        repo = self.repo
        toolbox = SafetyManagementToolbox()
        diag = repo.create_diagram("Governance Diagram", name="Gov")
        toolbox.diagrams = {"Gov": diag.diag_id}
        e1 = repo.create_element("Block", name="E1")
        e2 = repo.create_element("Block", name="E2")
        repo.add_element_to_diagram(diag.diag_id, e1.elem_id)
        repo.add_element_to_diagram(diag.diag_id, e2.elem_id)
        o1 = SysMLObject(
            1,
            "Work Product",
            0,
            0,
            element_id=e1.elem_id,
            properties={"name": "ODD"},
        )
        o2 = SysMLObject(
            2,
            "Work Product",
            0,
            100,
            element_id=e2.elem_id,
            properties={"name": "Scenario Library"},
        )
        diag.objects = [o1.__dict__, o2.__dict__]
        win = self._create_window("Used By", o1, o2, diag)
        event1 = types.SimpleNamespace(x=0, y=0, state=0)
        GovernanceDiagramWindow.on_left_press(win, event1)
        event2 = types.SimpleNamespace(x=0, y=100, state=0)
        GovernanceDiagramWindow.on_left_press(win, event2)
        diag.connections = [c.__dict__ for c in win.connections]
        toolbox.work_products = [
            SafetyWorkProduct("Gov", "ODD", ""),
            SafetyWorkProduct("Gov", "Scenario Library", ""),
        ]
        self.assertEqual(toolbox.analysis_targets("ODD"), {"Scenario Library"})
        self.assertEqual(toolbox.analysis_inputs("Scenario Library"), {"ODD"})

    def test_used_relationship_requires_dependency(self):
        repo = self.repo
        diag = repo.create_diagram("Governance Diagram", name="Gov")
        e1 = repo.create_element("Block", name="E1")
        e2 = repo.create_element("Block", name="E2")
        win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
        win.repo = repo
        win.diagram_id = diag.diag_id
        rels = ["Used By", "Used after Review", "Used after Approval"]
        for rel in rels:
            o1 = SysMLObject(
                1,
                "Work Product",
                0,
                0,
                element_id=e1.elem_id,
                properties={"name": "STPA"},
            )
            o2 = SysMLObject(
                2,
                "Work Product",
                0,
                100,
                element_id=e2.elem_id,
                properties={"name": "HARA"},
            )
            valid, _ = GovernanceDiagramWindow.validate_connection(win, o1, o2, rel)
            self.assertFalse(valid)

    def test_analysis_inputs_used_after_approval_visibility(self):
        repo = self.repo
        toolbox = SafetyManagementToolbox()
        diag = repo.create_diagram("Governance Diagram", name="Gov")
        toolbox.diagrams = {"Gov": diag.diag_id}
        e1 = repo.create_element("Block", name="E1")
        e2 = repo.create_element("Block", name="E2")
        repo.add_element_to_diagram(diag.diag_id, e1.elem_id)
        repo.add_element_to_diagram(diag.diag_id, e2.elem_id)
        o1 = SysMLObject(
            1,
            "Work Product",
            0,
            0,
            element_id=e1.elem_id,
            properties={"name": "Architecture Diagram"},
        )
        o2 = SysMLObject(
            2,
            "Work Product",
            0,
            100,
            element_id=e2.elem_id,
            properties={"name": "FTA"},
        )
        diag.objects = [o1.__dict__, o2.__dict__]
        win = self._create_window("Used By", o1, o2, diag)
        event1 = types.SimpleNamespace(x=0, y=0, state=0)
        GovernanceDiagramWindow.on_left_press(win, event1)
        event2 = types.SimpleNamespace(x=0, y=100, state=0)
        GovernanceDiagramWindow.on_left_press(win, event2)
        diag.connections = [c.__dict__ for c in win.connections]
        toolbox.work_products = [
            SafetyWorkProduct("Gov", "Architecture Diagram", ""),
            SafetyWorkProduct("Gov", "FTA", ""),
        ]
        self.assertEqual(toolbox.analysis_inputs("FTA"), set())
        self.assertEqual(toolbox.analysis_inputs("FTA", reviewed=True), set())
        self.assertEqual(toolbox.analysis_inputs("FTA", approved=True), {"Architecture Diagram"})

    def test_analysis_inputs_specific_analyses(self):
        repo = self.repo
        toolbox = SafetyManagementToolbox()
        diag = repo.create_diagram("Governance Diagram", name="Gov")
        toolbox.diagrams = {"Gov": diag.diag_id}
        e_arch = repo.create_element("Block", name="EA")
        repo.add_element_to_diagram(diag.diag_id, e_arch.elem_id)
        o_arch = SysMLObject(
            1,
            "Work Product",
            0,
            0,
            element_id=e_arch.elem_id,
            properties={"name": "Architecture Diagram"},
        )
        diag.objects = [o_arch.__dict__]
        toolbox.work_products = [SafetyWorkProduct("Gov", "Architecture Diagram", "")]
        analyses = [
            "FI2TC",
            "TC2FI",
            "STPA",
            "Risk Assessment",
            "Threat Analysis",
            "FMEA",
            "FMEDA",
        ]
        connections = []
        for idx, name in enumerate(analyses, start=2):
            e = repo.create_element("Block", name=f"E{idx}")
            repo.add_element_to_diagram(diag.diag_id, e.elem_id)
            o = SysMLObject(
                idx,
                "Work Product",
                0,
                idx * 100,
                element_id=e.elem_id,
                properties={"name": name},
            )
            diag.objects.append(o.__dict__)
            win = self._create_window("Used By", o_arch, o, diag)
            event1 = types.SimpleNamespace(x=0, y=0, state=0)
            GovernanceDiagramWindow.on_left_press(win, event1)
            event2 = types.SimpleNamespace(x=0, y=idx * 100, state=0)
            GovernanceDiagramWindow.on_left_press(win, event2)
            connections.extend(c.__dict__ for c in win.connections)
            toolbox.work_products.append(SafetyWorkProduct("Gov", name, ""))
            diag.connections = list(connections)
            self.assertEqual(toolbox.analysis_inputs(name), {"Architecture Diagram"})

    def test_used_relationships_mutually_exclusive(self):
        repo = self.repo
        repo.active_phase = "P1"
        e1 = repo.create_element("Block", name="E1")
        e2 = repo.create_element("Block", name="E2")
        diag1 = repo.create_diagram("Governance Diagram", name="Gov1")
        diag2 = repo.create_diagram("Governance Diagram", name="Gov2")
        repo.add_element_to_diagram(diag1.diag_id, e1.elem_id)
        repo.add_element_to_diagram(diag1.diag_id, e2.elem_id)
        repo.add_element_to_diagram(diag2.diag_id, e1.elem_id)
        repo.add_element_to_diagram(diag2.diag_id, e2.elem_id)
        o1a = SysMLObject(
            1,
            "Work Product",
            0,
            0,
            element_id=e1.elem_id,
            properties={"name": "Architecture Diagram"},
        )
        o2a = SysMLObject(
            2,
            "Work Product",
            0,
            100,
            element_id=e2.elem_id,
            properties={"name": "FMEA"},
        )
        diag1.objects = [o1a.__dict__, o2a.__dict__]
        win1 = self._create_window("Used By", o1a, o2a, diag1)
        event1 = types.SimpleNamespace(x=0, y=0, state=0)
        GovernanceDiagramWindow.on_left_press(win1, event1)
        event2 = types.SimpleNamespace(x=0, y=100, state=0)
        GovernanceDiagramWindow.on_left_press(win1, event2)

        o1b = SysMLObject(
            1,
            "Work Product",
            0,
            0,
            element_id=e1.elem_id,
            properties={"name": "Architecture Diagram"},
        )
        o2b = SysMLObject(
            2,
            "Work Product",
            0,
            100,
            element_id=e2.elem_id,
            properties={"name": "FMEA"},
        )
        diag2.objects = [o1b.__dict__, o2b.__dict__]
        win2 = self._create_window("Used after Review", o1b, o2b, diag2)
        event3 = types.SimpleNamespace(x=0, y=0, state=0)
        GovernanceDiagramWindow.on_left_press(win2, event3)
        event4 = types.SimpleNamespace(x=0, y=100, state=0)
        GovernanceDiagramWindow.on_left_press(win2, event4)
        self.assertEqual(len(repo.relationships), 1)

    def test_analysis_targets_used_after_review_visibility(self):
        repo = self.repo
        toolbox = SafetyManagementToolbox()
        diag = repo.create_diagram("Governance Diagram", name="Gov")
        toolbox.diagrams = {"Gov": diag.diag_id}
        e1 = repo.create_element("Block", name="E1")
        e2 = repo.create_element("Block", name="E2")
        repo.add_element_to_diagram(diag.diag_id, e1.elem_id)
        repo.add_element_to_diagram(diag.diag_id, e2.elem_id)
        o1 = SysMLObject(
            1,
            "Work Product",
            0,
            0,
            element_id=e1.elem_id,
            properties={"name": "Architecture Diagram"},
        )
        o2 = SysMLObject(
            2,
            "Work Product",
            0,
            100,
            element_id=e2.elem_id,
            properties={"name": "FTA"},
        )
        diag.objects = [o1.__dict__, o2.__dict__]
        win = self._create_window("Used after Review", o1, o2, diag)
        event1 = types.SimpleNamespace(x=0, y=0, state=0)
        GovernanceDiagramWindow.on_left_press(win, event1)
        event2 = types.SimpleNamespace(x=0, y=100, state=0)
        GovernanceDiagramWindow.on_left_press(win, event2)
        diag.connections = [c.__dict__ for c in win.connections]
        toolbox.work_products = [
            SafetyWorkProduct("Gov", "Architecture Diagram", ""),
            SafetyWorkProduct("Gov", "FTA", ""),
        ]
        self.assertEqual(toolbox.analysis_targets("Architecture Diagram"), set())
        self.assertEqual(
            toolbox.analysis_targets("Architecture Diagram", reviewed=True), {"FTA"}
        )
        self.assertEqual(
            toolbox.analysis_targets("Architecture Diagram", approved=True), {"FTA"}
        )

    def test_analysis_targets_used_after_approval_visibility(self):
        repo = self.repo
        toolbox = SafetyManagementToolbox()
        diag = repo.create_diagram("Governance Diagram", name="Gov")
        toolbox.diagrams = {"Gov": diag.diag_id}
        e1 = repo.create_element("Block", name="E1")
        e2 = repo.create_element("Block", name="E2")
        repo.add_element_to_diagram(diag.diag_id, e1.elem_id)
        repo.add_element_to_diagram(diag.diag_id, e2.elem_id)
        o1 = SysMLObject(
            1,
            "Work Product",
            0,
            0,
            element_id=e1.elem_id,
            properties={"name": "Architecture Diagram"},
        )
        o2 = SysMLObject(
            2,
            "Work Product",
            0,
            100,
            element_id=e2.elem_id,
            properties={"name": "FTA"},
        )
        diag.objects = [o1.__dict__, o2.__dict__]
        win = self._create_window("Used after Approval", o1, o2, diag)
        event1 = types.SimpleNamespace(x=0, y=0, state=0)
        GovernanceDiagramWindow.on_left_press(win, event1)
        event2 = types.SimpleNamespace(x=0, y=100, state=0)
        GovernanceDiagramWindow.on_left_press(win, event2)
        diag.connections = [c.__dict__ for c in win.connections]
        toolbox.work_products = [
            SafetyWorkProduct("Gov", "Architecture Diagram", ""),
            SafetyWorkProduct("Gov", "FTA", ""),
        ]
        self.assertEqual(toolbox.analysis_targets("Architecture Diagram"), set())
        self.assertEqual(
            toolbox.analysis_targets("Architecture Diagram", reviewed=True), set()
        )
        self.assertEqual(
            toolbox.analysis_targets("Architecture Diagram", approved=True), {"FTA"}
        )

    def test_analysis_inputs_mapping(self):
        repo = self.repo
        toolbox = SafetyManagementToolbox()
        diag = repo.create_diagram("Governance Diagram", name="Gov")
        toolbox.diagrams = {"Gov": diag.diag_id}
        e1 = repo.create_element("Block", name="E1")
        e2 = repo.create_element("Block", name="E2")
        repo.add_element_to_diagram(diag.diag_id, e1.elem_id)
        repo.add_element_to_diagram(diag.diag_id, e2.elem_id)
        o1 = SysMLObject(
            1,
            "Work Product",
            0,
            0,
            element_id=e1.elem_id,
            properties={"name": "Architecture Diagram"},
        )
        o2 = SysMLObject(
            2,
            "Work Product",
            0,
            100,
            element_id=e2.elem_id,
            properties={"name": "FTA"},
        )
        diag.objects = [o1.__dict__, o2.__dict__]
        win = self._create_window("Used By", o1, o2, diag)
        event1 = types.SimpleNamespace(x=0, y=0, state=0)
        GovernanceDiagramWindow.on_left_press(win, event1)
        event2 = types.SimpleNamespace(x=0, y=100, state=0)
        GovernanceDiagramWindow.on_left_press(win, event2)
        diag.connections = [c.__dict__ for c in win.connections]
        toolbox.work_products = [
            SafetyWorkProduct("Gov", "Architecture Diagram", ""),
            SafetyWorkProduct("Gov", "FTA", ""),
        ]
        self.assertEqual(toolbox.analysis_inputs("FTA"), {"Architecture Diagram"})

    def test_analysis_inputs_trace_propagation(self):
        repo = self.repo
        toolbox = SafetyManagementToolbox()
        diag = repo.create_diagram("Governance Diagram", name="Gov")
        toolbox.diagrams = {"Gov": diag.diag_id}
        e1 = repo.create_element("Block", name="E1")
        e2 = repo.create_element("Block", name="E2")
        e3 = repo.create_element("Block", name="E3")
        repo.add_element_to_diagram(diag.diag_id, e1.elem_id)
        repo.add_element_to_diagram(diag.diag_id, e2.elem_id)
        repo.add_element_to_diagram(diag.diag_id, e3.elem_id)
        o1 = SysMLObject(1, "Work Product", 0, 0, element_id=e1.elem_id, properties={"name": "Architecture Diagram"})
        o2 = SysMLObject(2, "Work Product", 0, 100, element_id=e2.elem_id, properties={"name": "Requirement Specification"})
        o3 = SysMLObject(3, "Work Product", 0, 200, element_id=e3.elem_id, properties={"name": "HAZOP"})
        diag.objects = [o1.__dict__, o2.__dict__, o3.__dict__]

        # Trace from Architecture Diagram to Requirement Specification
        win = self._create_window("Trace", o1, o2, diag)
        event1 = types.SimpleNamespace(x=0, y=0, state=0)
        GovernanceDiagramWindow.on_left_press(win, event1)
        event2 = types.SimpleNamespace(x=0, y=100, state=0)
        GovernanceDiagramWindow.on_left_press(win, event2)
        trace_conn = win.connections[0]

        # Used By from Requirement Specification to HAZOP
        win2 = self._create_window("Used By", o2, o3, diag)
        event3 = types.SimpleNamespace(x=0, y=100, state=0)
        GovernanceDiagramWindow.on_left_press(win2, event3)
        event4 = types.SimpleNamespace(x=0, y=200, state=0)
        GovernanceDiagramWindow.on_left_press(win2, event4)
        diag.connections = [trace_conn.__dict__, *[c.__dict__ for c in win2.connections]]

        toolbox.work_products = [
            SafetyWorkProduct("Gov", "Architecture Diagram", ""),
            SafetyWorkProduct("Gov", "Requirement Specification", ""),
            SafetyWorkProduct("Gov", "HAZOP", ""),
        ]
        self.assertEqual(
            toolbox.analysis_inputs("HAZOP"),
            {"Architecture Diagram", "Requirement Specification"},
        )

    def test_analysis_inputs_cross_module(self):
        repo = self.repo
        toolbox = SafetyManagementToolbox()
        # Two diagrams in different lifecycle modules
        diag1 = repo.create_diagram("Governance Diagram", name="Prototype")
        diag2 = repo.create_diagram("Governance Diagram", name="Design")
        toolbox.diagrams = {"Prototype": diag1.diag_id, "Design": diag2.diag_id}

        # Architecture and Requirement in Prototype, HAZOP in Design
        ea = repo.create_element("Block", name="A")
        er = repo.create_element("Block", name="R")
        eh = repo.create_element("Block", name="H")
        repo.add_element_to_diagram(diag1.diag_id, ea.elem_id)
        repo.add_element_to_diagram(diag1.diag_id, er.elem_id)
        repo.add_element_to_diagram(diag2.diag_id, er.elem_id)
        repo.add_element_to_diagram(diag2.diag_id, eh.elem_id)
        oa = SysMLObject(1, "Work Product", 0, 0, element_id=ea.elem_id, properties={"name": "Architecture Diagram"})
        orq = SysMLObject(2, "Work Product", 0, 100, element_id=er.elem_id, properties={"name": "Requirement Specification"})
        oh = SysMLObject(3, "Work Product", 0, 0, element_id=eh.elem_id, properties={"name": "HAZOP"})
        diag1.objects = [oa.__dict__, orq.__dict__]
        diag2.objects = [orq.__dict__, oh.__dict__]

        # Trace in Prototype
        win1 = self._create_window("Trace", oa, orq, diag1)
        event1 = types.SimpleNamespace(x=0, y=0, state=0)
        GovernanceDiagramWindow.on_left_press(win1, event1)
        event2 = types.SimpleNamespace(x=0, y=100, state=0)
        GovernanceDiagramWindow.on_left_press(win1, event2)

        # Used By in Design
        win2 = self._create_window("Used By", orq, oh, diag2)
        event3 = types.SimpleNamespace(x=0, y=100, state=0)
        GovernanceDiagramWindow.on_left_press(win2, event3)
        event4 = types.SimpleNamespace(x=0, y=0, state=0)
        GovernanceDiagramWindow.on_left_press(win2, event4)

        diag1.connections = [c.__dict__ for c in win1.connections]
        diag2.connections = [c.__dict__ for c in win2.connections]

        toolbox.work_products = [
            SafetyWorkProduct("Prototype", "Architecture Diagram", ""),
            SafetyWorkProduct("Prototype", "Requirement Specification", ""),
            SafetyWorkProduct("Design", "HAZOP", ""),
        ]

        self.assertEqual(
            toolbox.analysis_inputs("HAZOP"),
            {"Architecture Diagram", "Requirement Specification"},
        )

    def test_analysis_inputs_all_safety_analyses(self):
        repo = self.repo
        toolbox = SafetyManagementToolbox()
        diag = repo.create_diagram("Governance Diagram", name="Gov")
        toolbox.diagrams = {"Gov": diag.diag_id}

        ea = repo.create_element("Block", name="EA")
        repo.add_element_to_diagram(diag.diag_id, ea.elem_id)
        oa = SysMLObject(1, "Work Product", 0, 0, element_id=ea.elem_id, properties={"name": "Architecture Diagram"})
        objects = [oa.__dict__]
        connections = []

        for idx, analysis in enumerate(SAFETY_ANALYSIS_WORK_PRODUCTS, start=2):
            e = repo.create_element("Block", name=f"E{idx}")
            repo.add_element_to_diagram(diag.diag_id, e.elem_id)
            o = SysMLObject(idx, "Work Product", 0, idx * 100, element_id=e.elem_id, properties={"name": analysis})
            objects.append(o.__dict__)
            win = self._create_window("Used By", oa, o, diag)
            event1 = types.SimpleNamespace(x=0, y=0, state=0)
            GovernanceDiagramWindow.on_left_press(win, event1)
            event2 = types.SimpleNamespace(x=0, y=idx * 100, state=0)
            GovernanceDiagramWindow.on_left_press(win, event2)
            connections.extend(c.__dict__ for c in win.connections)

        diag.objects = objects
        diag.connections = connections

        toolbox.work_products = [SafetyWorkProduct("Gov", "Architecture Diagram", "")]
        toolbox.work_products.extend(
            SafetyWorkProduct("Gov", a, "") for a in SAFETY_ANALYSIS_WORK_PRODUCTS
        )

        excluded = {
            "Mission Profile",
            "Reliability Analysis",
            "Safety & Security Case",
            "GSN Argumentation",
        }
        for analysis in SAFETY_ANALYSIS_WORK_PRODUCTS - excluded:
            self.assertEqual(toolbox.analysis_inputs(analysis), {"Architecture Diagram"})

    def test_hazop_functions_hidden_until_governed(self):
        repo = self.repo
        toolbox = SafetyManagementToolbox()
        app = types.SimpleNamespace(
            get_all_action_labels=lambda: ["Func1"],
            safety_mgmt_toolbox=toolbox,
        )
        self.assertEqual(allowed_action_labels(app, "HAZOP"), [])
        diag = repo.create_diagram("Governance Diagram", name="Gov")
        toolbox.diagrams = {"Gov": diag.diag_id}
        e1 = repo.create_element("Block", name="E1")
        e2 = repo.create_element("Block", name="E2")
        repo.add_element_to_diagram(diag.diag_id, e1.elem_id)
        repo.add_element_to_diagram(diag.diag_id, e2.elem_id)
        o1 = SysMLObject(1, "Work Product", 0, 0, element_id=e1.elem_id, properties={"name": "Architecture Diagram"})
        o2 = SysMLObject(2, "Work Product", 0, 100, element_id=e2.elem_id, properties={"name": "HAZOP"})
        diag.objects = [o1.__dict__, o2.__dict__]
        win = self._create_window("Used By", o1, o2, diag)
        event1 = types.SimpleNamespace(x=0, y=0, state=0)
        GovernanceDiagramWindow.on_left_press(win, event1)
        event2 = types.SimpleNamespace(x=0, y=100, state=0)
        GovernanceDiagramWindow.on_left_press(win, event2)
        diag.connections = [c.__dict__ for c in win.connections]
        self.assertEqual(allowed_action_labels(app, "HAZOP"), ["Func1"])

    def test_hazop_functions_visible_via_traces(self):
        repo = self.repo
        toolbox = SafetyManagementToolbox()
        app = types.SimpleNamespace(
            get_all_action_labels=lambda: ["Func1"],
            safety_mgmt_toolbox=toolbox,
        )
        self.assertEqual(allowed_action_labels(app, "HAZOP"), [])
        diag = repo.create_diagram("Governance Diagram", name="Gov")
        toolbox.diagrams = {"Gov": diag.diag_id}
        e1 = repo.create_element("Block", name="E1")
        e2 = repo.create_element("Block", name="E2")
        e3 = repo.create_element("Block", name="E3")
        repo.add_element_to_diagram(diag.diag_id, e1.elem_id)
        repo.add_element_to_diagram(diag.diag_id, e2.elem_id)
        repo.add_element_to_diagram(diag.diag_id, e3.elem_id)
        o1 = SysMLObject(1, "Work Product", 0, 0, element_id=e1.elem_id, properties={"name": "Architecture Diagram"})
        o2 = SysMLObject(2, "Work Product", 0, 100, element_id=e2.elem_id, properties={"name": "Requirement Specification"})
        o3 = SysMLObject(3, "Work Product", 0, 200, element_id=e3.elem_id, properties={"name": "HAZOP"})
        diag.objects = [o1.__dict__, o2.__dict__, o3.__dict__]

        win = self._create_window("Trace", o1, o2, diag)
        event1 = types.SimpleNamespace(x=0, y=0, state=0)
        GovernanceDiagramWindow.on_left_press(win, event1)
        event2 = types.SimpleNamespace(x=0, y=100, state=0)
        GovernanceDiagramWindow.on_left_press(win, event2)
        trace_conn = win.connections[0]

        win2 = self._create_window("Used By", o2, o3, diag)
        event3 = types.SimpleNamespace(x=0, y=100, state=0)
        GovernanceDiagramWindow.on_left_press(win2, event3)
        event4 = types.SimpleNamespace(x=0, y=200, state=0)
        GovernanceDiagramWindow.on_left_press(win2, event4)
        diag.connections = [trace_conn.__dict__, *[c.__dict__ for c in win2.connections]]

        self.assertEqual(allowed_action_labels(app, "HAZOP"), ["Func1"])

    def test_fi2tc_tc2fi_functions_hidden_until_governed(self):
        repo = self.repo
        toolbox = SafetyManagementToolbox()
        app = types.SimpleNamespace(
            get_all_action_labels=lambda: ["Func1"],
            safety_mgmt_toolbox=toolbox,
        )
        for analysis in ("FI2TC", "TC2FI"):
            self.assertEqual(allowed_action_labels(app, analysis), [])
        diag = repo.create_diagram("Governance Diagram", name="Gov")
        toolbox.diagrams = {"Gov": diag.diag_id}
        e_arch = repo.create_element("Block", name="EA")
        repo.add_element_to_diagram(diag.diag_id, e_arch.elem_id)
        o_arch = SysMLObject(1, "Work Product", 0, 0, element_id=e_arch.elem_id, properties={"name": "Architecture Diagram"})
        diag.objects = [o_arch.__dict__]
        for idx, analysis in enumerate(("FI2TC", "TC2FI"), start=2):
            e = repo.create_element("Block", name=f"E{idx}")
            repo.add_element_to_diagram(diag.diag_id, e.elem_id)
            o = SysMLObject(idx, "Work Product", 0, idx * 100, element_id=e.elem_id, properties={"name": analysis})
            diag.objects.append(o.__dict__)
            win = self._create_window("Used By", o_arch, o, diag)
            event1 = types.SimpleNamespace(x=0, y=0, state=0)
            GovernanceDiagramWindow.on_left_press(win, event1)
            event2 = types.SimpleNamespace(x=0, y=idx * 100, state=0)
            GovernanceDiagramWindow.on_left_press(win, event2)
            diag.connections = getattr(diag, "connections", []) + [c.__dict__ for c in win.connections]
            self.assertEqual(allowed_action_labels(app, analysis), ["Func1"])

    def test_allowed_action_labels_respects_review_states(self):
        repo = self.repo
        toolbox = SafetyManagementToolbox()
        app = types.SimpleNamespace(
            get_all_action_labels=lambda: ["Func1"],
            safety_mgmt_toolbox=toolbox,
            current_review=types.SimpleNamespace(reviewed=False, approved=False),
        )
        diag = repo.create_diagram("Governance Diagram", name="Gov")
        toolbox.diagrams = {"Gov": diag.diag_id}
        e1 = repo.create_element("Block", name="E1")
        e2 = repo.create_element("Block", name="E2")
        repo.add_element_to_diagram(diag.diag_id, e1.elem_id)
        repo.add_element_to_diagram(diag.diag_id, e2.elem_id)
        o1 = SysMLObject(1, "Work Product", 0, 0, element_id=e1.elem_id, properties={"name": "Architecture Diagram"})
        o2 = SysMLObject(2, "Work Product", 0, 100, element_id=e2.elem_id, properties={"name": "HAZOP"})
        diag.objects = [o1.__dict__, o2.__dict__]
        diag.connections = [
            {
                "src": 1,
                "dst": 2,
                "conn_type": "Used after Approval",
                "stereotype": "used after approval",
            }
        ]
        self.assertEqual(allowed_action_labels(app, "HAZOP"), [])
        app.current_review.reviewed = True
        self.assertEqual(allowed_action_labels(app, "HAZOP"), [])
        app.current_review.approved = True
        self.assertEqual(allowed_action_labels(app, "HAZOP"), ["Func1"])

    def test_reliability_requires_mission_profile_connection(self):
        repo = self.repo
        toolbox = SafetyManagementToolbox()
        diag = repo.create_diagram("Governance Diagram", name="Gov")
        toolbox.diagrams = {"Gov": diag.diag_id}
        e_mp = repo.create_element("Block", name="MP")
        e_rel = repo.create_element("Block", name="RA")
        repo.add_element_to_diagram(diag.diag_id, e_mp.elem_id)
        repo.add_element_to_diagram(diag.diag_id, e_rel.elem_id)
        o_mp = SysMLObject(1, "Work Product", 0, 0, element_id=e_mp.elem_id, properties={"name": "Mission Profile"})
        o_rel = SysMLObject(2, "Work Product", 0, 100, element_id=e_rel.elem_id, properties={"name": "Reliability Analysis"})
        diag.objects = [o_mp.__dict__, o_rel.__dict__]
        self.assertEqual(toolbox.analysis_inputs("Reliability Analysis"), set())
        win_conn = self._create_window("Used By", o_mp, o_rel, diag)
        event1 = types.SimpleNamespace(x=0, y=0, state=0)
        GovernanceDiagramWindow.on_left_press(win_conn, event1)
        event2 = types.SimpleNamespace(x=0, y=100, state=0)
        GovernanceDiagramWindow.on_left_press(win_conn, event2)
        diag.connections = [c.__dict__ for c in win_conn.connections]
        self.assertEqual(toolbox.analysis_inputs("Reliability Analysis"), {"Mission Profile"})

    def test_stpa_control_actions_hidden_until_governed(self):
        repo = self.repo
        toolbox = SafetyManagementToolbox()
        cfd = repo.create_diagram("Control Flow Diagram", name="CFD")
        cfd.connections = [
            {"src": 1, "dst": 2, "conn_type": "Control Action", "name": "CA"}
        ]
        stpa_doc = StpaDoc("S1", cfd.diag_id, [])
        app = types.SimpleNamespace(active_stpa=stpa_doc, safety_mgmt_toolbox=toolbox)
        win = StpaWindow.__new__(StpaWindow)
        win.app = app
        self.assertEqual(win._get_control_actions(), [])
        gov = repo.create_diagram("Governance Diagram", name="Gov")
        toolbox.diagrams = {"Gov": gov.diag_id}
        e1 = repo.create_element("Block", name="E1")
        e2 = repo.create_element("Block", name="E2")
        repo.add_element_to_diagram(gov.diag_id, e1.elem_id)
        repo.add_element_to_diagram(gov.diag_id, e2.elem_id)
        o1 = SysMLObject(1, "Work Product", 0, 0, element_id=e1.elem_id, properties={"name": "Architecture Diagram"})
        o2 = SysMLObject(2, "Work Product", 0, 100, element_id=e2.elem_id, properties={"name": "STPA"})
        gov.objects = [o1.__dict__, o2.__dict__]
        gov.connections = [
            {
                "src": 1,
                "dst": 2,
                "conn_type": "Used By",
                "stereotype": "used by",
            }
        ]
        self.assertEqual(win._get_control_actions(), ["<<control action>> CA"])

    def test_analysis_inputs_used_after_review_visibility(self):
        repo = self.repo
        toolbox = SafetyManagementToolbox()
        diag = repo.create_diagram("Governance Diagram", name="Gov")
        toolbox.diagrams = {"Gov": diag.diag_id}
        e1 = repo.create_element("Block", name="E1")
        e2 = repo.create_element("Block", name="E2")
        repo.add_element_to_diagram(diag.diag_id, e1.elem_id)
        repo.add_element_to_diagram(diag.diag_id, e2.elem_id)
        o1 = SysMLObject(
            1,
            "Work Product",
            0,
            0,
            element_id=e1.elem_id,
            properties={"name": "Architecture Diagram"},
        )
        o2 = SysMLObject(
            2,
            "Work Product",
            0,
            100,
            element_id=e2.elem_id,
            properties={"name": "FTA"},
        )
        diag.objects = [o1.__dict__, o2.__dict__]
        win = self._create_window("Used after Review", o1, o2, diag)
        event1 = types.SimpleNamespace(x=0, y=0, state=0)
        GovernanceDiagramWindow.on_left_press(win, event1)
        event2 = types.SimpleNamespace(x=0, y=100, state=0)
        GovernanceDiagramWindow.on_left_press(win, event2)
        diag.connections = [c.__dict__ for c in win.connections]
        toolbox.work_products = [
            SafetyWorkProduct("Gov", "Architecture Diagram", ""),
            SafetyWorkProduct("Gov", "FTA", ""),
        ]
        self.assertEqual(toolbox.analysis_inputs("FTA"), set())
        self.assertEqual(toolbox.analysis_inputs("FTA", reviewed=True), {"Architecture Diagram"})
        self.assertEqual(toolbox.analysis_inputs("FTA", approved=True), {"Architecture Diagram"})

    def test_analysis_inputs_used_after_approval_visibility(self):
        repo = self.repo
        toolbox = SafetyManagementToolbox()
        diag = repo.create_diagram("Governance Diagram", name="Gov")
        toolbox.diagrams = {"Gov": diag.diag_id}
        e1 = repo.create_element("Block", name="E1")
        e2 = repo.create_element("Block", name="E2")
        repo.add_element_to_diagram(diag.diag_id, e1.elem_id)
        repo.add_element_to_diagram(diag.diag_id, e2.elem_id)
        o1 = SysMLObject(
            1,
            "Work Product",
            0,
            0,
            element_id=e1.elem_id,
            properties={"name": "Architecture Diagram"},
        )
        o2 = SysMLObject(
            2,
            "Work Product",
            0,
            100,
            element_id=e2.elem_id,
            properties={"name": "FTA"},
        )
        diag.objects = [o1.__dict__, o2.__dict__]
        win = self._create_window("Used after Approval", o1, o2, diag)
        event1 = types.SimpleNamespace(x=0, y=0, state=0)
        GovernanceDiagramWindow.on_left_press(win, event1)
        event2 = types.SimpleNamespace(x=0, y=100, state=0)
        GovernanceDiagramWindow.on_left_press(win, event2)
        diag.connections = [c.__dict__ for c in win.connections]
        toolbox.work_products = [
            SafetyWorkProduct("Gov", "Architecture Diagram", ""),
            SafetyWorkProduct("Gov", "FTA", ""),
        ]
        self.assertEqual(toolbox.analysis_inputs("FTA"), set())
        self.assertEqual(toolbox.analysis_inputs("FTA", reviewed=True), set())
        self.assertEqual(toolbox.analysis_inputs("FTA", approved=True), {"Architecture Diagram"})


if __name__ == "__main__":
    unittest.main()

