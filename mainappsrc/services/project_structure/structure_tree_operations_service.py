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

"""Service wrapping :mod:`structure_tree_operations` helpers."""

from __future__ import annotations

from ...core.structure_tree_operations import Structure_Tree_Operations


class StructureTreeOperationsService:
    """Facade delegating tree manipulation to :class:`Structure_Tree_Operations`."""

    def __init__(self, app: object) -> None:
        self._ops = Structure_Tree_Operations(app)

    def insert_node_in_tree(self, parent_item, node):
        return self._ops.insert_node_in_tree(parent_item, node)

    def move_subtree(self, node, dx, dy):
        return self._ops.move_subtree(node, dx, dy)

    def find_node_by_id(self, node, unique_id, visited=None):
        return self._ops.find_node_by_id(node, unique_id, visited)

    def is_descendant(self, node, possible_ancestor):
        return self._ops.is_descendant(node, possible_ancestor)

    def remove_node(self):
        return self._ops.remove_node()

    def remove_connection(self, node):
        return self._ops.remove_connection(node)

    def delete_node_and_subtree(self, node):
        return self._ops.delete_node_and_subtree(node)

    def find_node_by_id_all(self, unique_id):
        return self._ops.find_node_by_id_all(unique_id)

    def get_all_nodes_no_filter(self, node):
        return self._ops.get_all_nodes_no_filter(node)

    def get_all_nodes(self, node=None):
        return self._ops.get_all_nodes(node)

    def get_all_nodes_table(self, root_node):
        return self._ops.get_all_nodes_table(root_node)

    def get_all_nodes_in_model(self):
        return self._ops.get_all_nodes_in_model()

    def node_map_from_data(self, top_events):
        return self._ops.node_map_from_data(top_events)


__all__ = ["StructureTreeOperationsService"]
