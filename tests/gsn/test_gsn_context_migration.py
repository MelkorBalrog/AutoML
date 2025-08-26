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

from mainappsrc.models.gsn import GSNNode


def test_legacy_context_entries_load_as_context():
    """Older models stored context nodes in both ``children`` and ``context``.
    Ensure they are treated purely as context relationships when loading."""

    # Simulate legacy serialised data where the context node ID appears in both
    # the ``children`` and ``context`` fields of the parent.
    root_data = {
        "unique_id": "1",
        "user_name": "G",
        "node_type": "Goal",
        "children": ["2"],
        "context": ["2"],
    }
    ctx_data = {
        "unique_id": "2",
        "user_name": "C",
        "node_type": "Context",
    }
    nodes = {}
    root = GSNNode.from_dict(root_data, nodes)
    ctx = GSNNode.from_dict(ctx_data, nodes)

    # Should not raise even though the ID is listed twice.
    GSNNode.resolve_references(nodes)

    assert ctx in root.children
    assert ctx in root.context_children
    assert root in ctx.parents
    # The context node should only appear once in the children list.
    assert root.children.count(ctx) == 1

