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
"""Project properties management utilities."""

from __future__ import annotations

from typing import Any, Mapping

from analysis.utils import (
    CONTROLLABILITY_PROBABILITIES,
    EXPOSURE_PROBABILITIES,
    SEVERITY_PROBABILITIES,
    normalize_probability_mapping,
    update_probability_tables,
)


class ProjectPropertiesManager:
    """Handle loading and normalising project configuration."""

    def __init__(self, project_properties: dict[str, Any]):
        self.project_properties = project_properties

    def load_project_properties(self, data: Mapping[str, Any]) -> dict[str, Any]:
        """Load project properties from *data* and normalise probability keys."""

        props = data.get("project_properties", self.project_properties)
        props["exposure_probabilities"] = normalize_probability_mapping(
            props.get("exposure_probabilities") or EXPOSURE_PROBABILITIES
        )
        props["controllability_probabilities"] = normalize_probability_mapping(
            props.get("controllability_probabilities")
            or CONTROLLABILITY_PROBABILITIES
        )
        props["severity_probabilities"] = normalize_probability_mapping(
            props.get("severity_probabilities") or SEVERITY_PROBABILITIES
        )
        self.project_properties = props
        update_probability_tables(
            props.get("exposure_probabilities"),
            props.get("controllability_probabilities"),
            props.get("severity_probabilities"),
        )
        return self.project_properties
