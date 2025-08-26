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

"""Centralised configuration helpers for AutoML."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from config import load_diagram_rules
from analysis.requirement_rule_generator import regenerate_requirement_patterns
from analysis.risk_assessment import AutoMLHelper


class ConfigService:
    """Provide access to global configuration paths and helpers."""

    def __init__(self) -> None:
        base = Path(__file__).resolve().parents[3]
        self.config_path = base / "config" / "rules" / "diagram_rules.json"
        self.pattern_path = base / "config" / "patterns" / "requirement_patterns.json"
        self.report_template_path = (
            base / "config" / "templates" / "product_report_template.json"
        )
        self._config: dict[str, Any] = load_diagram_rules(self.config_path)
        self.gate_node_types: set[str] = set(self._config.get("gate_node_types", []))
        self.automl_helper = AutoMLHelper()
        self.unique_node_id_counter = 1
        regenerate_requirement_patterns()

    def reload_local_config(self) -> None:
        """Reload gate node types and regenerate requirement patterns."""
        self._config = load_diagram_rules(self.config_path)
        self.gate_node_types.clear()
        self.gate_node_types.update(self._config.get("gate_node_types", []))
        regenerate_requirement_patterns()


config_service = ConfigService()

__all__ = ["ConfigService", "config_service"]
