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
"""Service layer for application modules.

This package re-exports all individual service classes so callers can
import them from a central location, keeping :mod:`automl_core`
decoupled from the underlying module structure.
"""

from .app_init import AppInitializationService
from .ui import UISetupService
from .windows import WindowControllersService
from .versioning import VersioningReviewService
from .reporting import ReportingExportService
from .managers import ManagersFacadeService
from .node_clone import NodeCloneServiceInterface
from .view import ViewUpdateService
from .data_access import DataAccessQueriesService
from .config import config_service, user_config_service
from .project_structure import StructureTreeOperationsService
from .undo import UndoRedoService
from .navigation import NavigationInputService
from .syncing import SyncingAndIdsService
from .analysis import AnalysisUtilsService
from .safety_analysis import SafetyAnalysisService
from .validation import ValidationConsistencyService
from .safety_ui import SafetyUIService
from .diagram import DiagramRendererService
from .editing.editors_service import EditorsService

__all__ = [
    "AppInitializationService",
    "UISetupService",
    "WindowControllersService",
    "VersioningReviewService",
    "ReportingExportService",
    "ManagersFacadeService",
    "NodeCloneServiceInterface",
    "ViewUpdateService",
    "DataAccessQueriesService",
    "config_service",
    "user_config_service",
    "StructureTreeOperationsService",
    "UndoRedoService",
    "NavigationInputService",
    "SyncingAndIdsService",
    "AnalysisUtilsService",
    "SafetyAnalysisService",
    "ValidationConsistencyService",
    "SafetyUIService",
    "DiagramRendererService",
    "EditorsService",
]
