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

"""Main application package initializer."""

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_submodule_map = {
    # Core modules (dependencies first)
    "page_diagram": "core.page_diagram",
    "event_dispatcher": "core.event_dispatcher",
    "diagram_renderer": "core.diagram_renderer",
    # UI helpers migrated from core
    "app_lifecycle_ui": "ui.app_lifecycle_ui",
    "core.app_lifecycle_ui": "ui.app_lifecycle_ui",
    "safety_ui": "ui.safety_ui",
    "core.safety_ui": "ui.safety_ui",
    "ui_setup": "ui.ui_setup",
    "core.ui_setup": "ui.ui_setup",
    "node_utils": "gui.utils.node_utils",
    "core.node_utils": "gui.utils.node_utils",
    "fmea_service": "core.fmea_service",
    "safety_analysis": "core.safety_analysis",
    "automl_core": "core.automl_core",
    # Managers
    "cta_manager": "managers.cta_manager",
    "cyber_manager": "managers.cyber_manager",
    "fmeda_manager": "managers.fmeda_manager",
    "governance_manager": "managers.governance_manager",
    "gsn_manager": "managers.gsn_manager",
    "paa_manager": "managers.paa_manager",
    "project_manager": "managers.project_manager",
    "repository_manager": "managers.repository_manager",
    "requirements_manager": "managers.requirements_manager",
    "review_manager": "managers.review_manager",
    "sotif_manager": "managers.sotif_manager",
    "user_manager": "managers.user_manager",
    "diagram_clipboard_manager": "managers.diagram_clipboard_manager",
    "core.diagram_clipboard_manager": "managers.diagram_clipboard_manager",
    "project_properties_manager": "managers.project_properties_manager",
    "core.project_properties_manager": "managers.project_properties_manager",
    "undo_manager": "managers.undo_manager",
    "core.undo_manager": "managers.undo_manager",
    # Sub-apps
    "activity_diagram_subapp": "subapps.activity_diagram_subapp",
    "block_diagram_subapp": "subapps.block_diagram_subapp",
    "control_flow_diagram_subapp": "subapps.control_flow_diagram_subapp",
    "diagram_export_subapp": "subapps.diagram_export_subapp",
    "fta_subapp": "subapps.fta_subapp",
    "internal_block_diagram_subapp": "subapps.internal_block_diagram_subapp",
    "project_editor_subapp": "subapps.project_editor_subapp",
    "reliability_subapp": "subapps.reliability_subapp",
    "risk_assessment_subapp": "subapps.risk_assessment_subapp",
    "style_subapp": "subapps.style_subapp",
    "tree_subapp": "subapps.tree_subapp",
    "use_case_diagram_subapp": "subapps.use_case_diagram_subapp",
}

for old, new in _submodule_map.items():
    sys.modules[f"{__name__}.{old}"] = importlib.import_module(f".{new}", __name__)

from .core.automl_core import AutoMLApp
from .core.page_diagram import PageDiagram
from .managers.fmeda_manager import FMEDAManager
from .services.diagram import DiagramRendererService
import importlib as _importlib

# Avoid importing the main AutoML launcher during package initialisation
# to prevent circular dependencies when :mod:`AutoML` itself imports
# modules from ``mainappsrc``.  If the launcher is already being imported,
# use the existing module reference instead of importing again.
AutoML = sys.modules.get("AutoML")
if AutoML is None:  # pragma: no cover - import only when needed externally
    try:
        AutoML = _importlib.import_module("AutoML")
    except Exception:  # pragma: no cover - safety net for optional dependency
        AutoML = None

__all__ = [
    "AutoMLApp",
    "PageDiagram",
    "FMEDAManager",
    "DiagramRendererService",
    "AutoML",
]
