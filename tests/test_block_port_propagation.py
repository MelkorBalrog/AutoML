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
from gui.architecture import (
    add_composite_aggregation_part,
    propagate_block_port_changes,
)
from mainappsrc.models.sysml.sysml_repository import SysMLRepository

class BlockPortPropagationTests(unittest.TestCase):
    def setUp(self):
        SysMLRepository._instance = None
        self.repo = SysMLRepository.get_instance()

    def test_add_port_propagates_to_parts(self):
        repo = self.repo
        whole = repo.create_element("Block", name="Whole")
        part = repo.create_element("Block", name="Part", properties={"ports": "a"})
        ibd = repo.create_diagram("Internal Block Diagram")
        repo.link_diagram(whole.elem_id, ibd.diag_id)
        add_composite_aggregation_part(repo, whole.elem_id, part.elem_id)
        part.properties["ports"] = "a, b"
        propagate_block_port_changes(repo, part.elem_id)
        part_obj = next(o for o in ibd.objects if o.get("obj_type") == "Part")
        ports = [
            o["properties"]["name"]
            for o in ibd.objects
            if o.get("obj_type") == "Port" and o.get("properties", {}).get("parent") == str(part_obj["obj_id"])
        ]
        self.assertEqual(set(ports), {"a", "b"})

    def test_remove_port_propagates_to_parts(self):
        repo = self.repo
        whole = repo.create_element("Block", name="Whole")
        part = repo.create_element("Block", name="Part", properties={"ports": "a, b"})
        ibd = repo.create_diagram("Internal Block Diagram")
        repo.link_diagram(whole.elem_id, ibd.diag_id)
        add_composite_aggregation_part(repo, whole.elem_id, part.elem_id)
        part.properties["ports"] = "b"
        propagate_block_port_changes(repo, part.elem_id)
        part_obj = next(o for o in ibd.objects if o.get("obj_type") == "Part")
        ports = [
            o["properties"]["name"]
            for o in ibd.objects
            if o.get("obj_type") == "Port" and o.get("properties", {}).get("parent") == str(part_obj["obj_id"])
        ]
        self.assertEqual(ports, ["b"])

if __name__ == "__main__":
    unittest.main()
