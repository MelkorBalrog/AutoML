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

from .undo_manager import UndoRedoManager
from mainappsrc.services.navigation import NavigationInputService
from mainappsrc.services.syncing import SyncingAndIdsService

from mainappsrc.managers.user_manager import UserManager
from mainappsrc.managers.project_manager import ProjectManager
from mainappsrc.managers.cyber_manager import CyberSecurityManager
from mainappsrc.managers.drawing_manager import DrawingManager
from mainappsrc.subapps.diagram_export_subapp import DiagramExportSubApp
from mainappsrc.subapps.use_case_diagram_subapp import UseCaseDiagramSubApp
from mainappsrc.subapps.activity_diagram_subapp import ActivityDiagramSubApp
from mainappsrc.subapps.block_diagram_subapp import BlockDiagramSubApp
from mainappsrc.subapps.internal_block_diagram_subapp import InternalBlockDiagramSubApp
from mainappsrc.subapps.control_flow_diagram_subapp import ControlFlowDiagramSubApp
from mainappsrc.managers.sotif_manager import SOTIFManager
from mainappsrc.managers.cta_manager import ControlTreeManager
from mainappsrc.managers.requirements_manager import RequirementsManagerSubApp
from mainappsrc.managers.review_manager import ReviewManager
from mainappsrc.managers.safety_case_manager import SafetyCaseManager
from mainappsrc.managers.mission_profile_manager import MissionProfileManager
from mainappsrc.managers.scenario_library_manager import ScenarioLibraryManager
from mainappsrc.managers.odd_library_manager import OddLibraryManager
from .versioning_review import Versioning_Review
from .data_access_queries import DataAccess_Queries
from .validation_consistency import Validation_Consistency
from .reporting_export import Reporting_Export
from mainappsrc.services.editing.editors_service import EditorsService
from mainappsrc.services.analysis.analysis_utils_service import AnalysisUtilsService
from mainappsrc.services.safety_analysis import SafetyAnalysisService


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
        from mainappsrc.services.diagram import DiagramRendererService
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
        self.undo_manager = UndoRedoManager(self)
        self.user_manager = UserManager(self)
        self.project_manager = ProjectManager(self)
        self.cyber_manager = CyberSecurityManager(self)
        self.diagram_export_app = DiagramExportSubApp(self)
        self.use_case_diagram_app = UseCaseDiagramSubApp(self)
        self.activity_diagram_app = ActivityDiagramSubApp(self)
        self.block_diagram_app = BlockDiagramSubApp(self)
        self.internal_block_diagram_app = InternalBlockDiagramSubApp(self)
        self.control_flow_diagram_app = ControlFlowDiagramSubApp(self)
        self.sotif_manager = SOTIFManager(self)
        self.cta_manager = ControlTreeManager(self)
        self.requirements_manager = RequirementsManagerSubApp(self)
        self.review_manager = ReviewManager(self)
        self.safety_case_manager = SafetyCaseManager(self)
        self.mission_profile_manager = MissionProfileManager(self)
        self.scenario_library_manager = ScenarioLibraryManager(self)
        self.odd_library_manager = OddLibraryManager(self)
        self.drawing_manager = DrawingManager(self)
        self.versioning_review = Versioning_Review(self)
        self.data_access_queries = DataAccess_Queries(self)
        self.validation_consistency = Validation_Consistency(self)
        self.reporting_export = Reporting_Export(self)
        self.editors_service = EditorsService(self)
        self.analysis_utils_service = AnalysisUtilsService(self)
        self.probability_reliability = self.analysis_utils_service.probability_reliability
