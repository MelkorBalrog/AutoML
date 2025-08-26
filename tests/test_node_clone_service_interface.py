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
"""Tests for :class:`NodeCloneServiceInterface`."""

from __future__ import annotations

import os
import sys
import types
from unittest.mock import patch

# Provide dummy PIL modules so AutoML can be imported without Pillow
sys.modules.setdefault("PIL", types.ModuleType("PIL"))
sys.modules.setdefault("PIL.Image", types.ModuleType("PIL.Image"))
sys.modules.setdefault("PIL.ImageDraw", types.ModuleType("PIL.ImageDraw"))
sys.modules.setdefault("PIL.ImageFont", types.ModuleType("PIL.ImageFont"))
sys.modules.setdefault("PIL.ImageTk", types.ModuleType("PIL.ImageTk"))

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from AutoML import FaultTreeNode  # type: ignore
from mainappsrc.services.node_clone import NodeCloneServiceInterface


def test_interface_delegates_to_core_service():
    """Interface should forward calls to the underlying core service."""
    with patch(
        "mainappsrc.services.node_clone.node_clone_service_interface.NodeCloneService"
    ) as mock_service:
        interface = NodeCloneServiceInterface()
        interface.clone_node_preserving_id("n", "p")
        mock_service.return_value.clone_node_preserving_id.assert_called_once_with(
            "n", "p"
        )


def test_interface_clones_fault_tree_node_attributes():
    """Cloning through the interface should mirror core behaviour."""
    interface = NodeCloneServiceInterface()
    original = FaultTreeNode("orig", "Basic Event")
    clone = interface.clone_node_preserving_id(original)
    assert clone.user_name == original.user_name
    assert clone.original is original
    assert clone.x == original.x + 100
    assert clone.y == original.y + 100
    assert clone.unique_id != original.unique_id
