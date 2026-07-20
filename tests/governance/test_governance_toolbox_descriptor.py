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

"""Grouped semantic-state and descriptor/view verification tests."""

from types import SimpleNamespace

from gui.windows.architecture import (
    GovernanceDiagramWindow,
    GovernanceToolboxState,
    ToolboxButtonDescriptor,
    ToolboxCategoryDescriptor,
)


class TestGovernanceToolboxSemanticState:
    def test_snapshot_preserves_valid_category_tool_and_diagram(self):
        category = ToolboxCategoryDescriptor(
            "Entities", (ToolboxButtonDescriptor("entities/0", "Role", "Role", "elements"),)
        )
        state = GovernanceToolboxState("diagram-1", (category,), "Entities", "Role")
        window = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
        window.toolbox_state = state
        window.toolbox_var = SimpleNamespace(get=lambda: "Entities")
        window.current_tool = "Role"

        snapshot = window._snapshot_detached_state()

        assert snapshot.diagram_id == "diagram-1"
        assert snapshot.active_category == "Entities"
        assert snapshot.current_tool == "Role"


class TestGovernanceToolboxDescriptorVerification:
    def test_reports_missing_and_unexpected_category_and_button_ids(self):
        button = ToolboxButtonDescriptor("entities/0", "Role", "Role", "elements")
        window = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
        window.toolbox_state = GovernanceToolboxState(
            "diagram-1", (ToolboxCategoryDescriptor("Entities", (button,)),), "Entities"
        )
        window._toolbox_frames = {"Unexpected": []}
        window._loaded_toolbox_frames = {}

        report = window.verify_toolbox_view()

        assert report["missing_category_ids"] == ["Entities"]
        assert report["unexpected_category_ids"] == ["Unexpected"]
        assert report["missing_button_ids"] == ["entities/0"]
