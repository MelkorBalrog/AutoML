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
from gui.architecture import SysMLObject, SysMLDiagramWindow
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

class PartMultiplicityLabelTests(unittest.TestCase):
    def setUp(self):
        SysMLRepository._instance = None
        self.repo = SysMLRepository.get_instance()

    def test_label_shows_index_and_range(self):
        repo = self.repo
        whole = repo.create_element("Block", name="Whole")
        part_blk = repo.create_element("Block", name="PartB")
        repo.create_relationship(
            "Composite Aggregation",
            whole.elem_id,
            part_blk.elem_id,
            properties={"multiplicity": "1..*"},
        )
        ibd = repo.create_diagram("Internal Block Diagram")
        repo.link_diagram(whole.elem_id, ibd.diag_id)
        elem = repo.create_element(
            "Part", name="Part[1]", properties={"definition": part_blk.elem_id}
        )
        repo.add_element_to_diagram(ibd.diag_id, elem.elem_id)
        obj_data = {
            "obj_id": 1,
            "obj_type": "Part",
            "x": 0,
            "y": 0,
            "element_id": elem.elem_id,
            "width": 80.0,
            "height": 40.0,
            "properties": {"definition": part_blk.elem_id},
        }
        win = DummyWindow(ibd.diag_id)
        obj = SysMLObject(**obj_data)
        lines = win._object_label_lines(obj)
        self.assertIn("Part 1 : PartB [1..*]", lines)

if __name__ == "__main__":
    unittest.main()
