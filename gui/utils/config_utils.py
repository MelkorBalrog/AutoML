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


from __future__ import annotations

"""Configuration helpers and global state for AutoML."""

from pathlib import Path
from typing import Any

from config import load_diagram_rules
from analysis.requirement_rule_generator import regenerate_requirement_patterns
from analysis.risk_assessment import AutoMLHelper

# ---------------------------------------------------------------------------
# Paths and loaded configuration
# ---------------------------------------------------------------------------
_CONFIG_PATH = (
    Path(__file__).resolve().parents[2]
    / "config"
    / "rules"
    / "diagram_rules.json"
)
_CONFIG: dict[str, Any] = load_diagram_rules(_CONFIG_PATH)
GATE_NODE_TYPES: set[str] = set(_CONFIG.get("gate_node_types", []))

_PATTERN_PATH = (
    Path(__file__).resolve().parents[2]
    / "config"
    / "patterns"
    / "requirement_patterns.json"
)
_REPORT_TEMPLATE_PATH = (
    Path(__file__).resolve().parents[2]
    / "config"
    / "templates"
    / "product_report_template.json"
)

# Generate requirement patterns on import so consumers have up-to-date data.
regenerate_requirement_patterns()


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------
def _reload_local_config() -> None:
    """Reload gate node types from the external configuration file."""
    global _CONFIG
    _CONFIG = load_diagram_rules(_CONFIG_PATH)
    GATE_NODE_TYPES.clear()
    GATE_NODE_TYPES.update(_CONFIG.get("gate_node_types", []))
    regenerate_requirement_patterns()


# Global Unique ID counter and helper instance
unique_node_id_counter = 1
AutoML_Helper = AutoMLHelper()

__all__ = [
    "_reload_local_config",
    "unique_node_id_counter",
    "AutoML_Helper",
    "GATE_NODE_TYPES",
    "_CONFIG_PATH",
    "_PATTERN_PATH",
    "_REPORT_TEMPLATE_PATH",
]

