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

"""Compatibility layer exposing :mod:`ConfigService` globals."""

from mainappsrc.services.config import config_service
from analysis.requirement_rule_generator import (
    regenerate_requirement_patterns as _regen_patterns,
)


# ---------------------------------------------------------------------------
# Paths and loaded configuration
# ---------------------------------------------------------------------------
_CONFIG_PATH = config_service.config_path
_PATTERN_PATH = config_service.pattern_path
_REPORT_TEMPLATE_PATH = config_service.report_template_path
GATE_NODE_TYPES = config_service.gate_node_types

# Generate requirement patterns on import so consumers have up-to-date data.
# Already handled by ConfigService initialisation.


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def _reload_local_config() -> None:
    """Reload gate node types from the external configuration file."""
    config_service.reload_local_config()


def regenerate_requirement_patterns() -> None:
    """Regenerate requirement patterns via the analysis service."""
    _regen_patterns()


# Global Unique ID counter and helper instance
unique_node_id_counter = config_service.unique_node_id_counter
AutoML_Helper = config_service.automl_helper

__all__ = [
    "_reload_local_config",
    "unique_node_id_counter",
    "AutoML_Helper",
    "regenerate_requirement_patterns",
    "GATE_NODE_TYPES",
    "_CONFIG_PATH",
    "_PATTERN_PATH",
    "_REPORT_TEMPLATE_PATH",
]
