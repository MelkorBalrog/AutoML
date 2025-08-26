#!/usr/bin/env python3
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

"""Service responsible for cloning nodes within AutoML.

The :class:`NodeCloneService` encapsulates the logic required to clone
FaultTreeNode and GSNNode instances while preserving the relationships and
assigning new unique identifiers.  Offsetting the position of cloned nodes
prevents overlap with the original element, aiding visual distinction in
Diagrams.
"""

from __future__ import annotations

from typing import Optional

from ..models.fta.fault_tree_node import FaultTreeNode
from ..models.gsn.nodes import GSNNode, ALLOWED_AWAY_TYPES
from gui.utils.config_utils import AutoML_Helper


class NodeCloneService:
    """Clone AutoML nodes while generating unique IDs."""

    def clone_node_preserving_id(self, node, parent: Optional[GSNNode] = None):
        """Return a clone of *node* with a new unique ID.

        The function handles both FaultTreeNode and GSNNode instances.  For
        FaultTreeNode objects, a new :class:`FaultTreeNode` is created and the
        relevant attributes are copied across.  For :class:`GSNNode` instances
        the built-in ``clone`` method is used to ensure GSN-specific fields are
        preserved.  When *parent* is provided and the node represents a
        ``Context``, ``Assumption`` or ``Justification`` element the clone is
        automatically linked to *parent* using an ``in-context-of`` relation.
        """

        if isinstance(node, GSNNode):
            if node.node_type not in ALLOWED_AWAY_TYPES:
                raise ValueError(
                    "Only Goal, Solution, Context, Assumption, and Justification nodes can be cloned."
                )
            clone_parent = (
                parent
                if parent and node.node_type in {"Context", "Assumption", "Justification"}
                else None
            )
            new_node = node.clone(clone_parent)
            new_node.x = node.x + 100
            new_node.y = node.y + 100
            return new_node

        new_node = FaultTreeNode(node.user_name, node.node_type)
        new_node.unique_id = AutoML_Helper.get_next_unique_id()
        new_node.quant_value = getattr(node, "quant_value", None)
        new_node.gate_type = getattr(node, "gate_type", None)
        new_node.description = getattr(node, "description", "")
        new_node.rationale = getattr(node, "rationale", "")
        new_node.x = node.x + 100
        new_node.y = node.y + 100
        new_node.severity = getattr(node, "severity", None)
        new_node.input_subtype = getattr(node, "input_subtype", None)
        new_node.display_label = getattr(node, "display_label", "")
        new_node.equation = getattr(node, "equation", "")
        new_node.detailed_equation = getattr(node, "detailed_equation", "")
        new_node.is_page = getattr(node, "is_page", False)
        new_node.is_primary_instance = False
        new_node.original = node if node.is_primary_instance else node.original
        new_node.children = []
        return new_node
