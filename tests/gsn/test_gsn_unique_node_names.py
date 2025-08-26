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

from mainappsrc.models.gsn.nodes import GSNNode
from mainappsrc.models.gsn.diagram import GSNDiagram

def test_gsn_unique_node_names():
    root = GSNNode("Goal", "Goal")
    diagram = GSNDiagram(root)
    # clone should retain name
    clone = root.clone()
    diagram.add_node(clone)
    assert clone.user_name == "Goal"
    # new nodes with same name should be renamed
    n1 = GSNNode("Goal", "Goal")
    diagram.add_node(n1)
    n2 = GSNNode("Goal", "Goal")
    diagram.add_node(n2)
    assert n1.user_name == "Goal_1"
    assert n2.user_name == "Goal_2"
