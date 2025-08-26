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

"""Mix-in responsible for constructing application services and managers."""

from mainappsrc.subapps.tree_subapp import TreeSubApp
from mainappsrc.subapps.project_editor_subapp import ProjectEditorSubApp
from mainappsrc.subapps.risk_assessment_subapp import RiskAssessmentSubApp
from mainappsrc.subapps.reliability_subapp import ReliabilitySubApp

from mainappsrc.services import (
    UndoRedoService,
    NavigationInputService,
    SyncingAndIdsService,
    ManagersFacadeService,
    VersioningReviewService,
    ReportingExportService,
    EditorsService,
    AnalysisUtilsService,
    SafetyAnalysisService,
    DataAccessQueriesService,
    ValidationConsistencyService,
    SafetyUIService,
    DiagramRendererService,
)

from mainappsrc.subapps.diagram_export_subapp import DiagramExportSubApp
from mainappsrc.subapps.use_case_diagram_subapp import UseCaseDiagramSubApp
from mainappsrc.subapps.activity_diagram_subapp import ActivityDiagramSubApp
from mainappsrc.subapps.block_diagram_subapp import BlockDiagramSubApp
from mainappsrc.subapps.internal_block_diagram_subapp import InternalBlockDiagramSubApp
from mainappsrc.subapps.control_flow_diagram_subapp import ControlFlowDiagramSubApp


class ServiceInitMixin:
    """Initialise service objects used by :class:`AutoMLApp`."""

    def setup_services(self) -> None:
        """Create sub-applications, managers and helper utilities."""
        from .automl_core import AutoML_Helper  # local import to avoid circular

        self.tree_app = TreeSubApp()
        self.project_editor_app = ProjectEditorSubApp()
        self.risk_app = RiskAssessmentSubApp()
        self.reliability_app = ReliabilitySubApp()
        self.safety_analysis = SafetyAnalysisService(self)
        self.fta_app = self.safety_analysis
        self.fmea_service = self.safety_analysis
        self.fmeda_manager = self.safety_analysis
        self.fmeda = self.safety_analysis
        self.helper = AutoML_Helper
        self.syncing_service = SyncingAndIdsService(self)
        from mainappsrc.services import DiagramRendererService
        self.diagram_service = DiagramRendererService(self)
        self.diagram_renderer = self.diagram_service
        self.nav_input = NavigationInputService(self)
        for _name in (
            "go_back",
            "back_all_pages",
            "focus_on_node",
            "on_canvas_click",
            "on_canvas_double_click",
            "on_canvas_drag",
            "on_canvas_release",
            "on_analysis_tree_double_click",
            "on_analysis_tree_right_click",
            "on_analysis_tree_select",
            "on_ctrl_mousewheel",
            "on_ctrl_mousewheel_page",
            "on_right_mouse_press",
            "on_right_mouse_drag",
            "on_right_mouse_release",
            "on_tool_list_double_click",
            "on_treeview_click",
            "show_context_menu",
            "open_search_toolbox",
        ):
            setattr(self, _name, getattr(self.nav_input, _name))
        self.undo_manager = UndoRedoService(self)
        managers = ManagersFacadeService(self)
        self.user_manager = managers.user_manager
        self.project_manager = managers.project_manager
        self.cyber_manager = managers.cyber_manager
        self.diagram_export_app = DiagramExportSubApp(self)
        self.use_case_diagram_app = UseCaseDiagramSubApp(self)
        self.activity_diagram_app = ActivityDiagramSubApp(self)
        self.block_diagram_app = BlockDiagramSubApp(self)
        self.internal_block_diagram_app = InternalBlockDiagramSubApp(self)
        self.control_flow_diagram_app = ControlFlowDiagramSubApp(self)
        self.sotif_manager = managers.sotif_manager
        self.cta_manager = managers.cta_manager
        self.requirements_manager = managers.requirements_manager
        self.review_manager = managers.review_manager
        self.safety_case_manager = managers.safety_case_manager
        self.mission_profile_manager = managers.mission_profile_manager
        self.scenario_library_manager = managers.scenario_library_manager
        self.odd_library_manager = managers.odd_library_manager
        self.drawing_manager = managers.drawing_manager
        self.managers = managers
        self.versioning_review = VersioningReviewService(self)
        self.data_access_queries = DataAccessQueriesService(self)
        self.validation_consistency = ValidationConsistencyService(self)
        self.reporting_export = ReportingExportService(self)
        self.editors_service = EditorsService(self)
        self.analysis_utils_service = AnalysisUtilsService(self)
        self.probability_reliability = self.analysis_utils_service.probability_reliability
        self.safety_ui_service = SafetyUIService(self)
