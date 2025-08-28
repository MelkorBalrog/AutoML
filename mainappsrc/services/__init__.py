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
"""Lazy service registry for application modules.

This package exposes all service classes and singletons via attributes
that are imported on first access.  Delayed imports avoid circular
initialisation issues during application start-up while preserving a
central access point for :mod:`automl_core` and other modules.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any, Dict, Tuple

# Mapping of public attribute names to ``(module, attribute)`` pairs.  Each
# entry will be imported only when accessed through ``__getattr__``.
_SERVICE_ATTRS: Dict[str, Tuple[str, str]] = {
    # App lifecycle and UI services
    "AppInitializationService": (
        "mainappsrc.services.app_init.app_initialization_service",
        "AppInitializationService",
    ),
    "UISetupService": (
        "mainappsrc.services.ui.ui_setup_service",
        "UISetupService",
    ),
    "WindowControllersService": (
        "mainappsrc.services.windows.window_controllers_service",
        "WindowControllersService",
    ),
    # Versioning and reporting
    "VersioningReviewService": (
        "mainappsrc.services.versioning.versioning_review_service",
        "VersioningReviewService",
    ),
    "ReportingExportService": (
        "mainappsrc.services.reporting.reporting_export_service",
        "ReportingExportService",
    ),
    # Miscellaneous helpers
    "ManagersFacadeService": (
        "mainappsrc.services.managers.managers_facade_service",
        "ManagersFacadeService",
    ),
    "NodeCloneServiceInterface": (
        "mainappsrc.services.node_clone.node_clone_service_interface",
        "NodeCloneServiceInterface",
    ),
    "ViewUpdateService": (
        "mainappsrc.services.view.view_update_service",
        "ViewUpdateService",
    ),
    "DataAccessQueriesService": (
        "mainappsrc.services.data_access.data_access_queries_service",
        "DataAccessQueriesService",
    ),
    "MathService": (
        "mainappsrc.services.math_service",
        "MathService",
    ),
    # Configuration services
    "config_service": (
        "mainappsrc.services.config.config_service",
        "config_service",
    ),
    "user_config_service": (
        "mainappsrc.services.config.user_config_service",
        "user_config_service",
    ),
    # Project structure and history
    "StructureTreeOperationsService": (
        "mainappsrc.services.project_structure.structure_tree_operations_service",
        "StructureTreeOperationsService",
    ),
    "UndoRedoService": (
        "mainappsrc.services.undo.undo_redo_service",
        "UndoRedoService",
    ),
    # Navigation and synchronisation
    "NavigationInputService": (
        "mainappsrc.services.navigation.navigation_input_service",
        "NavigationInputService",
    ),
    "SyncingAndIdsService": (
        "mainappsrc.services.syncing.syncing_and_ids_service",
        "SyncingAndIdsService",
    ),
    # Analysis and validation
    "AnalysisUtilsService": (
        "mainappsrc.services.analysis.analysis_utils_service",
        "AnalysisUtilsService",
    ),
    "SafetyAnalysisService": (
        "mainappsrc.services.safety_analysis.safety_analysis_service",
        "SafetyAnalysisService",
    ),
    "ValidationConsistencyService": (
        "mainappsrc.services.validation.validation_consistency_service",
        "ValidationConsistencyService",
    ),
    "SafetyUIService": (
        "mainappsrc.services.safety_ui.safety_ui_service",
        "SafetyUIService",
    ),
    "DiagramRendererService": (
        "mainappsrc.services.diagram.diagram_renderer_service",
        "DiagramRendererService",
    ),
    # Editing helpers
    "EditorsService": (
        "mainappsrc.services.editing.editors_service",
        "EditorsService",
    ),
}
# Public sequence of all registered service attribute names
SERVICE_CLASSES = tuple(_SERVICE_ATTRS.keys())
# Backward compatibility alias for older code expecting SERVICE_MODULES
SERVICE_MODULES = SERVICE_CLASSES

__all__ = list(SERVICE_CLASSES)


def __getattr__(name: str) -> Any:  # pragma: no cover - simple delegation
    """Dynamically import and return a service attribute.

    Parameters
    ----------
    name:
        The attribute requested by the importing module.
    """
    try:
        module_name, attr_name = _SERVICE_ATTRS[name]
    except KeyError as exc:  # pragma: no cover - defensive programming
        raise AttributeError(f"module 'mainappsrc.services' has no attribute {name!r}") from exc
    module = import_module(module_name)
    return getattr(module, attr_name)
