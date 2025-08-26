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
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from gui.architecture import SysMLDiagramWindow, SysMLObject
from mainappsrc.models.sysml.sysml_repository import SysMLRepository


class DummyFont:
    def measure(self, text: str) -> int:
        return len(text)

    def metrics(self, name: str) -> int:
        return 1


class DummyWindow:
    _object_label_lines = SysMLDiagramWindow._object_label_lines

    def __init__(self, diag_id):
        self.repo = SysMLRepository.get_instance()
        self.zoom = 1.0
        self.font = DummyFont()
        self.diagram_id = diag_id

    def _wrap_text_to_width(self, text: str, _width: float) -> list[str]:
        return [text]


class GovernanceElementStereotypeTests(unittest.TestCase):
    def setUp(self):
        SysMLRepository._instance = None

    def test_task_label_includes_stereotype(self):
        repo = SysMLRepository.get_instance()
        diag = repo.create_diagram("Governance Diagram")
        elem = repo.create_element("Action", name="Draft Plan")
        obj = SysMLObject(1, "Action", 0.0, 0.0, element_id=elem.elem_id, properties={"name": "Draft Plan"})
        win = DummyWindow(diag.diag_id)
        lines = win._object_label_lines(obj)
        self.assertEqual("<<task>>", lines[0])
        self.assertEqual("Draft Plan", lines[1])

    def test_gateway_labels_hidden(self):
        repo = SysMLRepository.get_instance()
        diag = repo.create_diagram("Governance Diagram")
        win = DummyWindow(diag.diag_id)
        for idx, node_type in enumerate(["Decision", "Initial", "Final", "Merge"], start=1):
            elem = repo.create_element(node_type, name="Gate")
            obj = SysMLObject(
                idx,
                node_type,
                0.0,
                0.0,
                element_id=elem.elem_id,
                properties={"name": "Gate"},
            )
            lines = win._object_label_lines(obj)
            self.assertEqual([], lines)

    def test_system_boundary_label_has_no_stereotype(self):
        repo = SysMLRepository.get_instance()
        diag = repo.create_diagram("Governance Diagram")
        obj = SysMLObject(1, "System Boundary", 0.0, 0.0, properties={"name": "Area"})
        win = DummyWindow(diag.diag_id)
        lines = win._object_label_lines(obj)
        self.assertEqual(["Area"], lines)


if __name__ == "__main__":
    unittest.main()
