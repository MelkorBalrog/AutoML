#!/usr/bin/env python3
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

import math
import sys
import json
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk
import os, sys
import threading
import time
base = os.path.dirname(__file__)
if base not in sys.path:
    sys.path.append(base)
parent = os.path.dirname(base)
if parent not in sys.path:
    sys.path.append(parent)
from typing import Any, Optional
from tkinter import ttk, filedialog, simpledialog, scrolledtext
from gui.dialogs.dialog_utils import askstring_fixed
from gui.controls import messagebox
from gui.utils import logger, add_treeview_scrollbars
from gui.controls.button_utils import enable_listbox_hover_highlight
from gui.utils.tooltip import ToolTip
from gui.styles.style_manager import StyleManager
from gui.toolboxes.review_toolbox import ReviewData, ReviewParticipant, ReviewComment
from functools import partial
from gui.toolboxes.safety_management_toolbox import SafetyManagementToolbox
from gui.explorers.safety_case_explorer import SafetyCaseExplorer
from gui.windows.gsn_diagram_window import GSN_WINDOWS
from gui.windows.causal_bayesian_network_window import CBN_WINDOWS
from gui.windows.gsn_config_window import GSNElementConfig
from mainappsrc.models.gsn import GSNDiagram, GSNModule
from mainappsrc.models.gsn.nodes import GSNNode, ALLOWED_AWAY_TYPES
from gui.utils.closable_notebook import ClosableNotebook
from gui.controls.mac_button_style import (
    apply_translucid_button_style,
    apply_purplish_button_style,
)
from gui.dialogs.user_select_dialog import UserSelectDialog
from gui.dialogs.decomposition_dialog import DecompositionDialog
from dataclasses import asdict
from pathlib import Path
from .event_handlers import EventHandlersMixin
from .persistence_wrappers import PersistenceWrappersMixin
from .service_init_mixin import ServiceInitMixin
from .page_diagram import PageDiagram
from .node_utils import resolve_original as resolve_node_original
from mainappsrc.services.app_init import AppInitializationService
from mainappsrc.services.ui import UISetupService
from analysis.mechanisms import (
    DiagnosticMechanism,
    MechanismLibrary,
    ANNEX_D_MECHANISMS,
    PAS_8800_MECHANISMS,
)
from pathlib import Path
from collections.abc import Mapping
from gui.utils.drawing_helper import FTADrawingHelper, fta_drawing_helper
from mainappsrc.core.event_dispatcher import EventDispatcher
from gui.controls.window_controllers import WindowControllers
from mainappsrc.core.top_event_workflows import Top_Event_Workflows
from mainappsrc.managers.review_manager import ReviewManager
from mainappsrc.managers.drawing_manager import DrawingManager
from .versioning_review import Versioning_Review
from .validation_consistency import Validation_Consistency
from .reporting_export import Reporting_Export
from .node_clone_service import NodeCloneService
from mainappsrc.services.view import ViewUpdateService
from analysis.user_config import (
    load_user_config,
    save_user_config,
    set_current_user,
    load_all_users,
    set_last_user,
    CURRENT_USER_NAME,
    CURRENT_USER_EMAIL,
)
from analysis.risk_assessment import (
    DERIVED_MATURITY_TABLE,
    ASSURANCE_AGGREGATION_AND,
    AND_DECOMPOSITION_TABLE,
    OR_DECOMPOSITION_TABLE,
    boolify,
    AutoMLHelper,
)
from analysis.models import (
    MissionProfile,
    ReliabilityComponent,
    ReliabilityAnalysis,
    HazopEntry,
    HaraEntry,
    HazopDoc,
    HaraDoc,
    StpaEntry,
    StpaDoc,
    FI2TCDoc,
    TC2FIDoc,
    DamageScenario,
    ThreatScenario,
    AttackPath,
    FunctionThreat,
    ThreatEntry,
    ThreatDoc,
    QUALIFICATIONS,
    COMPONENT_ATTR_TEMPLATES,
    RELIABILITY_MODELS,
    component_fit_map,
    ASIL_LEVEL_OPTIONS,
    ASIL_ORDER,
    ASIL_TARGETS,
    ASIL_TABLE,
    ASIL_DECOMP_SCHEMES,
    calc_asil,
    global_requirements,
    ensure_requirement_defaults,
    REQUIREMENT_TYPE_OPTIONS,
    REQUIREMENT_WORK_PRODUCTS,
    CAL_LEVEL_OPTIONS,
    CybersecurityGoal,
)
from gui.utils.safety_case_table import SafetyCaseTable
from gui.windows.architecture import (
    UseCaseDiagramWindow,
    ActivityDiagramWindow,
    BlockDiagramWindow,
    InternalBlockDiagramWindow,
    ControlFlowDiagramWindow,
    GovernanceDiagramWindow,
    ArchitectureManagerDialog,
    link_requirement_to_object,
    unlink_requirement_from_object,
    link_requirements,
    unlink_requirements,
    ARCH_WINDOWS,
)
from mainappsrc.models.sysml.sysml_repository import SysMLRepository
from .undo_manager import UndoRedoManager
from analysis.scenario_description import template_phrases
from mainappsrc.ui.app_lifecycle_ui import AppLifecycleUI
from tools.crash_report_logger import install_best, watchdog_best
from tools.thread_manager import manager as thread_manager
from mainappsrc.core.editing_labels_styling import Editing_Labels_Styling
import copy
import tkinter.font as tkFont
import builtins
from mainappsrc.managers.user_manager import UserManager
from mainappsrc.managers.project_manager import ProjectManager
from mainappsrc.managers.product_goal_manager import ProductGoalManager
from mainappsrc.ui.project_properties_dialog import ProjectPropertiesDialog
from mainappsrc.managers.sotif_manager import SOTIFManager
from mainappsrc.managers.cyber_manager import CyberSecurityManager
from mainappsrc.managers.cta_manager import ControlTreeManager
if __package__ and __package__.startswith("AutoML"):
    from AutoML.config.automl_constants import (
        dynamic_recommendations,
        WORK_PRODUCT_INFO as BASE_WORK_PRODUCT_INFO,
        WORK_PRODUCT_PARENTS as BASE_WORK_PRODUCT_PARENTS,
        PMHF_TARGETS,
    )
else:  # pragma: no cover - script context
    from config.automl_constants import (
        dynamic_recommendations,
        WORK_PRODUCT_INFO as BASE_WORK_PRODUCT_INFO,
        WORK_PRODUCT_PARENTS as BASE_WORK_PRODUCT_PARENTS,
        PMHF_TARGETS,
    )

builtins.REQUIREMENT_WORK_PRODUCTS = REQUIREMENT_WORK_PRODUCTS
builtins.SafetyCaseTable = SafetyCaseTable
try:
    from PIL import Image, ImageDraw, ImageFont
except ModuleNotFoundError:
    Image = ImageDraw = ImageFont = None
import os
import types
os.environ["GS_EXECUTABLE"] = r"C:\Program Files\gs\gs10.04.0\bin\gswin64c.exe"
import networkx as nx
# Import ReportLab for PDF export.
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak
from gui.styles.style_editor import StyleEditor
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak, SimpleDocTemplate, Image as RLImage
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO, StringIO
from email.utils import make_msgid
import html
import datetime
try:
    import PIL.Image as PILImage
except ModuleNotFoundError:
    PILImage = None
try:
    from reportlab.platypus import LongTable
except Exception:  # pragma: no cover - fallback when reportlab missing
    LongTable = None
from email.message import EmailMessage
import smtplib
import socket

styles = getSampleStyleSheet()  # Create the stylesheet.
preformatted_style = ParagraphStyle(name="Preformatted", fontName="Courier", fontSize=10)
if hasattr(styles, "add"):
    styles.add(preformatted_style)
else:  # pragma: no cover - fallback for minimal stubs
    styles["Preformatted"] = preformatted_style

# Characters used to display pass/fail status in metrics labels.
from analysis.constants import CHECK_MARK, CROSS_MARK
from analysis.utils import (
    append_unique_insensitive,
    EXPOSURE_PROBABILITIES,
    CONTROLLABILITY_PROBABILITIES,
    SEVERITY_PROBABILITIES,
)
from analysis.safety_management import SafetyManagementToolbox, ACTIVE_TOOLBOX
from analysis.causal_bayesian_network import CausalBayesianNetwork, CausalBayesianNetworkDoc
try:  # pragma: no cover - support direct module import
    from .version import VERSION
except Exception:  # pragma: no cover
    from mainappsrc.version import VERSION
try:  # pragma: no cover
    from .models.fta.fault_tree_node import FaultTreeNode, add_failure_mode as ft_add_failure_mode, refresh_tree as fault_tree_refresh, add_node_of_type as _add_node_of_type
except Exception:  # pragma: no cover
    import os, sys
    base = os.path.dirname(__file__)
    sys.path.append(base)
    sys.path.append(os.path.dirname(base))
    from models.fta.fault_tree_node import FaultTreeNode, add_failure_mode as ft_add_failure_mode, refresh_tree as fault_tree_refresh, add_node_of_type as _add_node_of_type

from .structure_tree_operations import Structure_Tree_Operations

from gui.toolboxes import (
    RequirementsExplorerWindow,
    DiagramElementDialog,
    _RequirementRelationDialog,
)


from pathlib import Path
from gui.dialogs.user_info_dialog import UserInfoDialog

from . import config_utils
from .config_utils import _reload_local_config

# Expose configuration helpers and global state
_CONFIG_PATH = config_utils._CONFIG_PATH
GATE_NODE_TYPES = config_utils.GATE_NODE_TYPES
_PATTERN_PATH = config_utils._PATTERN_PATH
_REPORT_TEMPLATE_PATH = config_utils._REPORT_TEMPLATE_PATH
unique_node_id_counter = config_utils.unique_node_id_counter
AutoML_Helper = config_utils.AutoML_Helper
import uuid

##########################################
# Edit Dialog 
##########################################
from gui.dialogs.edit_node_dialog import EditNodeDialog, DecompositionDialog
from gui.dialogs.fmea_row_dialog import FMEARowDialog
from gui.dialogs.req_dialog import ReqDialog
from gui.dialogs.select_base_event_dialog import SelectBaseEventDialog
from mainappsrc.ui.safety_ui import SafetyUIMixin

##########################################
# Main Application (Parent Diagram)
##########################################
class AutoMLApp(
    ServiceInitMixin,
    SafetyUIMixin,
    EventHandlersMixin,
    PersistenceWrappersMixin,
):
    """Main application window for AutoML Analyzer."""

    _instance: Optional["AutoMLApp"] = None

    #: Maximum number of characters displayed for a notebook tab title. Longer
    #: titles are truncated with an ellipsis to avoid giant tabs that overflow
    #: the working area.
    MAX_TAB_TEXT_LENGTH = 20
    GATE_NODE_TYPES = GATE_NODE_TYPES

    @property
    def fmedas(self):
        return self.safety_analysis.fmedas

    @fmedas.setter
    def fmedas(self, value):
        self.safety_analysis.fmedas = value

    #: Maximum characters shown for tool notebook tab titles. Tool tabs use
    #: a fixed width so they remain readable but long names are capped at this
    #: length and truncated with an ellipsis.
    MAX_TOOL_TAB_TEXT_LENGTH = 20

    #: Maximum number of tabs displayed at once in the tools and document
    #: notebooks. Additional tabs can be accessed via the navigation buttons.
    MAX_VISIBLE_TABS = 4

    WORK_PRODUCT_INFO = BASE_WORK_PRODUCT_INFO.copy()
    for _wp in REQUIREMENT_WORK_PRODUCTS:
        WORK_PRODUCT_INFO.setdefault(
            _wp,
            (
                "System Design (Item Definition)",
                "Requirements Editor",
                "show_requirements_editor",
            ),
        )

    # Mapping of work products to their parent menu categories.  When a
    # child work product is enabled its parent menu must also become
    # active so the submenu is reachable.
    WORK_PRODUCT_PARENTS = BASE_WORK_PRODUCT_PARENTS.copy()

    # Ensure all requirement work products activate the top-level Requirements
    # menu.  Each specific requirement specification (e.g. vehicle, functional
    # safety) is treated as a child of the generic "Requirements" category so
    # that declaring any of them on a governance diagram enables the
    # corresponding menu items.
    for _wp in REQUIREMENT_WORK_PRODUCTS:
        WORK_PRODUCT_PARENTS.setdefault(_wp, "Requirements")

    def classify_scenarios(self):
        """Delegate scenario classification to analysis service."""
        service = getattr(self, "analysis_utils_service", None)
        if service is None:  # pragma: no cover - fallback for tests
            from mainappsrc.services.analysis.analysis_utils_service import (
                AnalysisUtilsService,
            )

            service = AnalysisUtilsService(self)
        return service.classify_scenarios()

    def load_default_mechanisms(self):
        """Delegate default mechanism loading to analysis service."""
        service = getattr(self, "analysis_utils_service", None)
        if service is None:  # pragma: no cover - fallback for tests
            from mainappsrc.services.analysis.analysis_utils_service import (
                AnalysisUtilsService,
            )

            service = AnalysisUtilsService(self)
        return service.load_default_mechanisms()

    @property
    def window_controllers(self) -> WindowControllers:
        if not hasattr(self, "_window_controllers"):
            self._window_controllers = WindowControllers(self)
        return self._window_controllers

    @property
    def top_event_workflows(self) -> Top_Event_Workflows:
        if not hasattr(self, "_top_event_workflows"):
            self._top_event_workflows = Top_Event_Workflows(self)
        return self._top_event_workflows

    def __getattr__(self, name):  # pragma: no cover - simple delegation
        """Delegate missing attributes to UI helper services.

        ``UISetupService`` bundles several UI-related helpers that were
        previously mixed into :class:`AutoMLApp`.  Attribute lookups fall back
        first to the service itself and then to the composed
        :class:`AppLifecycleUI` instance so existing code continues to work
        without modification.
        """

        service = self.__dict__.get("ui_service")
        if service and (
            name in service.__dict__
            or any(name in cls.__dict__ for cls in service.__class__.mro())
        ):
            return getattr(service, name)
        ui = getattr(service, "lifecycle_ui", None)
        if ui and (
            name in ui.__dict__ or any(name in cls.__dict__ for cls in ui.__class__.mro())
        ):
            return getattr(ui, name)
        raise AttributeError(f"{type(self).__name__!r} object has no attribute {name!r}")

    def __init__(self, root):
        AutoMLApp._instance = self
        self.root = root
        self.ui_service = UISetupService(self, root)
        self.ui_service.initialize(root)
        self.lifecycle_ui = self.ui_service.lifecycle_ui
        self.labels_styling = Editing_Labels_Styling(self)
        self.top_events = []
        self.cta_events = []
        self.paa_events = []
        self.fta_root_node = None
        self.cta_root_node = None
        self.paa_root_node = None
        self.analysis_tabs = {}
        self.shared_product_goals = {}
        self.product_goal_manager = ProductGoalManager()
        self.selected_node = None
        self.clone_offset_counter = {}
        self.node_clone_service = NodeCloneService()
        self.view_update_service = ViewUpdateService(self)
        self._loaded_model_paths = []
        self.root.title("AutoML-Analyzer")
        self.messagebox = messagebox
        self.version = VERSION
        self.zoom = 1.0
        self.rc_dragged = False
        self.diagram_font = tkFont.Font(family="Arial", size=int(8 * self.zoom))
        self.setup_services()
        self.init_service = AppInitializationService(self)
        self.init_service.initialize()
        self.project_properties_manager = self.init_service.project_properties_manager
        self.diagram_clipboard = self.init_service.diagram_clipboard_manager

        menubar = tk.Menu(root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New AutoML Model", command=self.project_manager.new_model, accelerator="Ctrl+N")
        file_menu.add_command(label="Save AutoML Model", command=self.project_manager.save_model, accelerator="Ctrl+S")
        file_menu.add_command(label="Load AutoML Model", command=self.project_manager.load_model, accelerator="Ctrl+O")
        file_menu.add_command(label="Project Properties", command=self.edit_project_properties)
        file_menu.add_command(label="Save PDF Report", command=self.generate_pdf_report)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.confirm_close)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Edit Selected", command=self.edit_selected)
        edit_menu.add_command(label="Remove Connection", command=lambda: self.remove_connection(self.selected_node) if self.selected_node else None)
        edit_menu.add_command(label="Delete Node", command=lambda: self.delete_node_and_subtree(self.selected_node) if self.selected_node else None)
        edit_menu.add_command(label="Remove Node", command=self.remove_node)
        edit_menu.add_separator()
        edit_menu.add_command(label="Copy", command=self.copy_node, accelerator="Ctrl+C")
        edit_menu.add_command(label="Cut", command=self.cut_node, accelerator="Ctrl+X")
        edit_menu.add_command(label="Paste", command=self.paste_node, accelerator="Ctrl+V")
        edit_menu.add_separator()
        edit_menu.add_command(label="Edit User Name", command=self.user_manager.edit_user_name, accelerator="Ctrl+U")
        edit_menu.add_command(label="Edit Description", command=self.edit_description, accelerator="Ctrl+D")
        edit_menu.add_command(label="Edit Rationale", command=self.edit_rationale, accelerator="Ctrl+L")
        edit_menu.add_command(label="Edit Value", command=self.edit_value)
        edit_menu.add_command(label="Edit Gate Type", command=self.edit_gate_type, accelerator="Ctrl+G")
        edit_menu.add_command(label="Edit Severity", command=self.edit_severity, accelerator="Ctrl+E")
        edit_menu.add_command(label="Edit Controllability", command=self.edit_controllability)
        edit_menu.add_command(label="Edit Page Flag", command=self.edit_page_flag)
        search_menu = tk.Menu(menubar, tearoff=0)
        search_menu.add_command(
            label="Find...", command=self.open_search_toolbox, accelerator="Ctrl+F"
        )
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Zoom In", command=self.zoom_in, accelerator="Ctrl++")
        view_menu.add_command(label="Zoom Out", command=self.zoom_out, accelerator="Ctrl+-")
        view_menu.add_command(label="Style Editor", command=self.open_style_editor)
        view_menu.add_command(
            label="Light Mode",
            command=lambda: self.apply_style('pastel.xml'),
        )
        view_menu.add_command(label="Metrics", command=self.lifecycle_ui.open_metrics_tab)

        requirements_menu = tk.Menu(menubar, tearoff=0)
        requirements_menu.add_command(
            label="Requirements Matrix",
            command=self.show_requirements_matrix,
            state=tk.DISABLED,
        )
        matrix_idx = requirements_menu.index("end")
        requirements_menu.add_command(
            label="Requirements Editor",
            command=self.show_requirements_editor,
            state=tk.DISABLED,
        )
        editor_idx = requirements_menu.index("end")
        requirements_menu.add_command(
            label="Requirements Explorer",
            command=self.show_requirements_explorer,
            state=tk.DISABLED,
        )
        explorer_idx = requirements_menu.index("end")
        for wp in REQUIREMENT_WORK_PRODUCTS:
            self.work_product_menus.setdefault(wp, []).extend(
                [
                    (requirements_menu, matrix_idx),
                    (requirements_menu, editor_idx),
                    (requirements_menu, explorer_idx),
                ]
            )
        requirements_menu.add_command(
            label="Product Goals Matrix", command=self.show_safety_goals_matrix
        )
        requirements_menu.add_command(
            label="Product Goals Editor",
            command=self.show_product_goals_editor,
            state=tk.DISABLED,
        )
        self.work_product_menus.setdefault("Product Goal Specification", []).append(
            (requirements_menu, requirements_menu.index("end"))
        )
        requirements_menu.add_command(
            label="Safety Performance Indicators",
            command=self.show_safety_performance_indicators,
        )
        self.lifecycle_ui._add_lifecycle_requirements_menu(requirements_menu)
        self.phase_req_menu = tk.Menu(requirements_menu, tearoff=0)
        requirements_menu.add_cascade(
            label="Phase Requirements", menu=self.phase_req_menu
        )
        self._refresh_phase_requirements_menu()
        requirements_menu.add_command(
            label="Export Product Goal Requirements",
            command=self.export_product_goal_requirements,
        )
        review_menu = tk.Menu(menubar, tearoff=0)
        review_menu.add_command(label="Start Peer Review", command=self.start_peer_review)
        review_menu.add_command(label="Start Joint Review", command=self.start_joint_review)
        review_menu.add_command(label="Open Review Toolbox", command=self.open_review_toolbox)
        review_menu.add_command(label="Set Current User", command=self.user_manager.set_current_user)
        review_menu.add_command(label="Merge Review Comments", command=self.merge_review_comments)
        review_menu.add_command(label="Compare Versions", command=self.compare_versions)
        architecture_menu = tk.Menu(menubar, tearoff=0)
        architecture_menu.add_command(label="Use Case Diagram", command=self.window_controllers.open_use_case_diagram)
        architecture_menu.add_command(label="Activity Diagram", command=self.window_controllers.open_activity_diagram)
        architecture_menu.add_command(label="Block Diagram", command=self.window_controllers.open_block_diagram)
        architecture_menu.add_command(label="Internal Block Diagram", command=self.window_controllers.open_internal_block_diagram)
        architecture_menu.add_command(label="Control Flow Diagram", command=self.window_controllers.open_control_flow_diagram)
        architecture_menu.add_separator()
        architecture_menu.add_command(
            label="AutoML Explorer",
            command=self.manage_architecture,
            state=tk.DISABLED,
        )
        self.work_product_menus.setdefault("Architecture Diagram", []).append(
            (architecture_menu, architecture_menu.index("end"))
        )
        # --- Risk Assessment Menu ---
        risk_menu = tk.Menu(menubar, tearoff=0)
        risk_menu.add_command(
            label="HAZOP Analysis",
            command=self.open_hazop_window,
            state=tk.DISABLED,
        )
        self.work_product_menus.setdefault("HAZOP", []).append(
            (risk_menu, risk_menu.index("end"))
        )
        risk_menu.add_command(
            label="Risk Assessment",
            command=self.open_risk_assessment_window,
            state=tk.DISABLED,
        )
        self.work_product_menus.setdefault("Risk Assessment", []).append(
            (risk_menu, risk_menu.index("end"))
        )
        risk_menu.add_command(
            label="STPA Analysis",
            command=self.open_stpa_window,
            state=tk.DISABLED,
        )
        self.work_product_menus.setdefault("STPA", []).append(
            (risk_menu, risk_menu.index("end"))
        )
        risk_menu.add_command(
            label="Threat Analysis",
            command=self.open_threat_window,
            state=tk.DISABLED,
        )
        self.work_product_menus.setdefault("Threat Analysis", []).append(
            (risk_menu, risk_menu.index("end"))
        )
        risk_menu.add_command(label="Hazard Explorer", command=self.show_hazard_explorer)
        risk_menu.add_command(label="Hazards Editor", command=self.show_hazard_editor)
        risk_menu.add_command(label="Malfunctions Editor", command=self.show_malfunction_editor)
        risk_menu.add_command(label="Triggering Conditions", command=self.show_triggering_condition_list)
        risk_menu.add_command(label="Functional Insufficiencies", command=self.show_functional_insufficiency_list)
        risk_menu.add_separator()
        risk_menu.add_command(
            label="FI2TC Analysis",
            command=self.open_fi2tc_window,
            state=tk.DISABLED,
        )
        self.work_product_menus.setdefault("FI2TC", []).append(
            (risk_menu, risk_menu.index("end"))
        )
        risk_menu.add_command(
            label="TC2FI Analysis",
            command=self.open_tc2fi_window,
            state=tk.DISABLED,
        )
        self.work_product_menus.setdefault("TC2FI", []).append(
            (risk_menu, risk_menu.index("end"))
        )
                
        # --- Qualitative Analysis Menu ---
        qualitative_menu = tk.Menu(menubar, tearoff=0)
        qualitative_menu.add_command(
            label="FMEA Manager",
            command=self.fmea_service.show_fmea_list,
            state=tk.DISABLED,
        )
        self.work_product_menus.setdefault("FMEA", []).append(
            (qualitative_menu, qualitative_menu.index("end"))
        )

        cta_menu = tk.Menu(qualitative_menu, tearoff=0)
        cta_menu.add_command(label="Add Top Level Event", command=self.cta_manager.create_diagram)
        cta_menu.add_separator()
        cta_menu.add_command(label="Add Triggering Condition", command=lambda: self.add_node_of_type("Triggering Condition"))
        cta_indices = {"add_trigger": cta_menu.index("end")}
        cta_menu.add_command(label="Add Functional Insufficiency", command=lambda: self.add_node_of_type("Functional Insufficiency"))
        cta_indices["add_functional_insufficiency"] = cta_menu.index("end")
        qualitative_menu.add_cascade(label="CTA", menu=cta_menu, state=tk.DISABLED)
        self.work_product_menus.setdefault("CTA", []).append(
            (qualitative_menu, qualitative_menu.index("end"))
        )
        self.cta_manager.register_menu(cta_menu, cta_indices)
        qualitative_menu.add_command(
            label="Fault Prioritization",
            command=self.open_fault_prioritization_window,
        )

        paa_menu = tk.Menu(qualitative_menu, tearoff=0)
        paa_menu.add_command(
            label="Add Top Level Event",
            command=self.paa_manager.create_paa_diagram,
        )
        paa_menu.add_separator()
        paa_menu.add_command(
            label="Add Confidence",
            command=lambda: self.add_node_of_type("Confidence Level"),
            accelerator="Ctrl+Shift+C",
        )
        self._paa_menu_indices = {"add_confidence": paa_menu.index("end")}
        paa_menu.add_command(
            label="Add Robustness",
            command=lambda: self.add_node_of_type("Robustness Score"),
            accelerator="Ctrl+Shift+R",
        )
        self._paa_menu_indices["add_robustness"] = paa_menu.index("end")
        paa_menu.add_command(
            label="Add Gate",
            command=lambda: self.add_node_of_type("GATE"),
            accelerator="Ctrl+Shift+G",
        )
        self._paa_menu_indices["add_gate"] = paa_menu.index("end")
        paa_menu.add_separator()
        paa_menu.add_command(
            label="Calc Prototype Assurance Level (PAL)",
            command=self.calculate_overall,
            accelerator="Ctrl+R",
        )
        qualitative_menu.add_cascade(
            label="Prototype Assurance Analysis",
            menu=paa_menu,
            state=tk.DISABLED,
        )
        self.work_product_menus.setdefault("Prototype Assurance Analysis", []).append(
            (qualitative_menu, qualitative_menu.index("end"))
        )
        self.paa_menu = paa_menu
        
        # --- Quantitative Analysis Menu ---
        quantitative_menu = tk.Menu(menubar, tearoff=0)
        quantitative_menu.add_command(
            label="Mission Profiles",
            command=self.manage_mission_profiles,
            state=tk.DISABLED,
        )
        self.work_product_menus.setdefault("Mission Profile", []).append(
            (quantitative_menu, quantitative_menu.index("end"))
        )
                
        quantitative_menu.add_separator()
        quantitative_menu.add_command(label="Faults Editor", command=self.show_fault_editor)
        quantitative_menu.add_command(label="Failures Editor", command=self.show_failure_editor)
        quantitative_menu.add_separator()
        
        quantitative_menu.add_command(
            label="Mechanism Libraries", command=self.manage_mechanism_libraries
        )
        quantitative_menu.add_command(
            label="Reliability Analysis",
            command=self.open_reliability_window,
            state=tk.DISABLED,
        )
        self.work_product_menus.setdefault("Reliability Analysis", []).append(
            (quantitative_menu, quantitative_menu.index("end"))
        )
        quantitative_menu.add_command(
            label="Causal Bayesian Network",
            command=self.window_controllers.open_causal_bayesian_network_window,
            state=tk.DISABLED,
        )
        self.work_product_menus.setdefault("Causal Bayesian Network Analysis", []).append(
            (quantitative_menu, quantitative_menu.index("end"))
        )
        quantitative_menu.add_command(
            label="FMEDA Analysis",
            command=self.open_fmeda_window,
            state=tk.DISABLED,
        )
        self.work_product_menus.setdefault("FMEDA", []).append(
            (quantitative_menu, quantitative_menu.index("end"))
        )
        quantitative_menu.add_command(
            label="FMEDA Manager",
            command=self.show_fmeda_list,
            state=tk.DISABLED,
        )
        fta_menu = tk.Menu(quantitative_menu, tearoff=0)
        fta_menu.add_command(label="Add Top Level Event", command=self.create_fta_diagram)
        fta_menu.add_separator()
        fta_menu.add_command(label="Add Gate", command=lambda: self.add_node_of_type("GATE"), accelerator="Ctrl+Shift+G")
        self._fta_menu_indices = {"add_gate": fta_menu.index("end")}
        fta_menu.add_command(label="Add Basic Event", command=lambda: self.add_node_of_type("Basic Event"), accelerator="Ctrl+Shift+B")
        self._fta_menu_indices["add_basic_event"] = fta_menu.index("end")
        fta_menu.add_command(label="Add FMEA/FMEDA Event", command=self.add_basic_event_from_fmea)
        fta_menu.add_command(label="Add Gate from Failure Mode", command=self.add_gate_from_failure_mode)
        self._fta_menu_indices["add_gate_from_failure_mode"] = fta_menu.index("end")
        fta_menu.add_command(label="Add Fault Event", command=self.add_fault_event)
        self._fta_menu_indices["add_fault_event"] = fta_menu.index("end")
        fta_menu.add_separator()
        fta_menu.add_command(label="FTA-FMEA Traceability", command=self.show_traceability_matrix)
        fta_menu.add_command(
            label="FTA Cut Sets",
            command=self.show_cut_sets,
            state=tk.DISABLED,
        )
        fta_menu.add_command(label="Common Cause Toolbox", command=self.show_common_cause_view)
        fta_menu.add_command(label="Cause & Effect Chain", command=self.show_cause_effect_chain)
        fta_menu.add_separator()
        fta_menu.add_command(
            label="Calc PMHF",
            command=self.calculate_pmfh,
            accelerator="Ctrl+M",
        )
        self.fta_menu = fta_menu
        quantitative_menu.add_cascade(label="FTA", menu=fta_menu, state=tk.DISABLED)
        self.work_product_menus.setdefault("FTA", []).append(
            (quantitative_menu, quantitative_menu.index("end"))
        )
        
        libs_menu = tk.Menu(menubar, tearoff=0)
        libs_menu.add_command(
            label="Scenario Libraries",
            command=self.manage_scenario_libraries,
            state=tk.DISABLED,
        )
        self.work_product_menus.setdefault("Scenario Library", []).append(
            (libs_menu, libs_menu.index("end"))
        )
        libs_menu.add_command(
            label="ODD Libraries",
            command=self.manage_odd_libraries,
            state=tk.DISABLED,
        )
        self.work_product_menus.setdefault("ODD", []).append(
            (libs_menu, libs_menu.index("end"))
        )

        gsn_menu = tk.Menu(menubar, tearoff=0)
        gsn_menu.add_command(label="GSN Explorer", command=self.gsn_manager.manage_gsn)
        self.work_product_menus.setdefault("GSN Argumentation", []).append(
            (gsn_menu, gsn_menu.index("end"))
        )
        gsn_menu.add_command(
            label="Safety & Security Case Explorer", command=self.manage_safety_cases
        )
        self.work_product_menus.setdefault("Safety & Security Case", []).append(
            (gsn_menu, gsn_menu.index("end"))
        )

        # Add menus to the bar in the desired order
        menubar.add_cascade(label="File", menu=file_menu)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        menubar.add_cascade(label="Search", menu=search_menu)
        menubar.add_cascade(label="View", menu=view_menu)
        menubar.add_cascade(label="Requirements", menu=requirements_menu)
        idx = menubar.index("end")
        self.work_product_menus.setdefault("Requirements", []).append((menubar, idx))
        menubar.entryconfig(idx, state=tk.DISABLED)
        menubar.add_cascade(label="Architecture", menu=architecture_menu)
        idx = menubar.index("end")
        self.work_product_menus.setdefault("Architecture Diagram", []).append((menubar, idx))
        menubar.entryconfig(idx, state=tk.DISABLED)
        menubar.add_cascade(label="Scenario", menu=libs_menu)
        idx = menubar.index("end")
        self.work_product_menus.setdefault("Scenario Library", []).append((menubar, idx))
        self.work_product_menus.setdefault("ODD", []).append((menubar, idx))
        menubar.entryconfig(idx, state=tk.DISABLED)
        menubar.add_cascade(label="Risk Assessment", menu=risk_menu)
        idx = menubar.index("end")
        self.work_product_menus.setdefault("Risk Assessment", []).append((menubar, idx))
        menubar.entryconfig(idx, state=tk.DISABLED)
        menubar.add_cascade(label="Qualitative Analysis", menu=qualitative_menu)
        idx = menubar.index("end")
        self.work_product_menus.setdefault("Qualitative Analysis", []).append((menubar, idx))
        menubar.entryconfig(idx, state=tk.DISABLED)
        menubar.add_cascade(label="Quantitative Analysis", menu=quantitative_menu)
        idx = menubar.index("end")
        self.work_product_menus.setdefault("Quantitative Analysis", []).append((menubar, idx))
        menubar.entryconfig(idx, state=tk.DISABLED)
        menubar.add_cascade(label="GSN", menu=gsn_menu)
        idx = menubar.index("end")
        self.work_product_menus.setdefault("GSN", []).append((menubar, idx))
        menubar.entryconfig(idx, state=tk.DISABLED)
        menubar.add_cascade(label="Review", menu=review_menu)
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.lifecycle_ui.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        root.config(menu=menubar)

        # Container to hold the auto-hiding explorer tab and main pane
        self.top_frame = tk.Frame(root)
        self.top_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.main_pane = tk.PanedWindow(self.top_frame, orient=tk.HORIZONTAL)
        self.main_pane.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Initialise the log window but keep it hidden by default.
        self.log_frame = logger.init_log_window(root, height=7)
        # Status bar showing lifecycle phase and object metadata
        self.status_frame = ttk.Frame(root)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.toggle_log_button = ttk.Button(
            root, text="Show Logs", command=self.lifecycle_ui.toggle_logs
        )
        self.toggle_log_button.pack(side=tk.BOTTOM, fill=tk.X)
        logger.set_toggle_button(self.toggle_log_button)
        self.style.configure(
            "Phase.TLabel",
            background="#4a6ea9",
            foreground="white",
            font=("Arial", 10, "bold"),
        )
        self.active_phase_lbl = ttk.Label(
            self.status_frame, text="Active phase: None", style="Phase.TLabel"
        )
        self.active_phase_lbl.pack(side=tk.LEFT, padx=5)
        self.status_meta_vars = {
            "Name": tk.StringVar(value=""),
            "Type": tk.StringVar(value=""),
            "Author": tk.StringVar(value=""),
            "Tab": tk.StringVar(value=""),
            "WorkProduct": tk.StringVar(value=""),
            "Class": tk.StringVar(value=""),
        }
        for key, var in self.status_meta_vars.items():
            ttk.Label(self.status_frame, text=f"{key}:").pack(
                side=tk.LEFT, padx=(10, 0)
            )
            ttk.Label(self.status_frame, textvariable=var).pack(side=tk.LEFT)

        # Explorer pane with notebook and pin button (hidden by default)
        self.explorer_pane = ttk.Frame(self.main_pane)
        self.explorer_nb = ttk.Notebook(self.explorer_pane)
        self.explorer_nb.pack(fill=tk.BOTH, expand=True)
        self._explorer_width = 300
        self._explorer_auto_hide_id = None
        self._explorer_pinned = False
        self._explorer_pin_btn = ttk.Button(
            self.explorer_pane, text="Pin", command=self.lifecycle_ui.toggle_explorer_pin
        )
        self._explorer_pin_btn.pack(anchor="ne")
        self._explorer_tab = ttk.Label(
            self.top_frame,
            text="F\ni\nl\ne\ns",
            relief="raised",
            cursor="hand2",
        )
        self._explorer_tab.pack(side=tk.LEFT, fill=tk.Y)

        self.analysis_tab = ttk.Frame(self.explorer_nb)
        self.explorer_nb.add(self.analysis_tab, text="File Explorer")

        # --- Analyses Group ---
        self.analysis_group = ttk.LabelFrame(
            self.analysis_tab, text="Analyses & Architecture", style="Toolbox.TLabelframe"
        )
        self.analysis_group.pack(fill=tk.BOTH, expand=True)

        tree_frame = ttk.Frame(self.analysis_group)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        self.analysis_tree = ttk.Treeview(tree_frame)
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.analysis_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.analysis_tree.xview)
        self.analysis_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.analysis_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        # Maintain backwards compatibility with older code referencing
        # ``self.treeview`` for the main explorer tree.
        self.treeview = self.analysis_tree

        # --- Tools Section ---
        self.tools_group = ttk.LabelFrame(
            self.analysis_tab, text="Tools", style="Toolbox.TLabelframe"
        )
        self.tools_group.pack(fill=tk.BOTH, expand=False, pady=5)
        top = ttk.Frame(self.tools_group)
        top.pack(side=tk.TOP, fill=tk.X)
        ttk.Label(top, text="Lifecycle Phase:").pack(side=tk.LEFT)
        self.lifecycle_var = tk.StringVar(value="")
        self.lifecycle_cb = ttk.Combobox(
            top, textvariable=self.lifecycle_var, state="readonly"
        )
        self.lifecycle_cb.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Container holding navigation buttons and the tools notebook
        nb_container = ttk.Frame(self.tools_group)
        nb_container.pack(fill=tk.BOTH, expand=True)
        style = ttk.Style()
        apply_translucid_button_style(style)
        # Create a custom notebook style so that a layout is available.  Without a
        # ``TNotebook`` suffix in the style name, ttk cannot find the default
        # layout which led to ``_tkinter.TclError: Layout ToolsNotebook not
        # found`` when instantiating the notebook widget.  The following styles
        # derive from the standard ``TNotebook``/``TNotebook.Tab`` styles and
        # merely customise the tab appearance.
        style.configure(
            "ToolsNotebook.TNotebook",
            padding=0,
            background="#c0d4eb",
            lightcolor="#eaf2fb",
            darkcolor="#5a6d84",
            borderwidth=2,
            relief="raised",
        )
        style.configure(
            "ToolsNotebook.TNotebook.Tab",
            font=("Arial", 10),
            padding=(10, 5),
            width=20,
            background="#b5bdc9",
            foreground="#555555",
            borderwidth=1,
            relief="raised",
        )
        style.map(
            "ToolsNotebook.TNotebook.Tab",
            background=[("selected", "#4a6ea9"), ("!selected", "#b5bdc9")],
            foreground=[("selected", "white"), ("!selected", "#555555")],
        )
        self.tools_left_btn = ttk.Button(
            nb_container, text="<", width=2, command=self.lifecycle_ui._select_prev_tool_tab
        )
        self.tools_right_btn = ttk.Button(
            nb_container, text=">", width=2, command=self.lifecycle_ui._select_next_tool_tab
        )
        self.tools_left_btn.pack(side=tk.LEFT, fill=tk.Y)
        self.tools_right_btn.pack(side=tk.RIGHT, fill=tk.Y)
        self.tools_nb = ttk.Notebook(nb_container, style="ToolsNotebook.TNotebook")
        self.tools_nb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Track all tool tabs and which range is currently visible
        self._tool_all_tabs: list[str] = []
        self._tool_tab_offset = 0

        # Properties tab for displaying metadata
        self.prop_frame = ttk.Frame(self.tools_nb)
        self.prop_view = ttk.Treeview(
            self.prop_frame, columns=("field", "value"), show="headings"
        )
        self.prop_view.heading("field", text="Field")
        self.prop_view.heading("value", text="Value")
        # ------------------------------------------------------------------
        # NEVER DELETE OR TOUCH THIS:
        # Keep the field column fixed so the value column can expand to occupy
        # the remaining tab width, making long property values easier to read.
        # ------------------------------------------------------------------
        self.prop_view.column("field", width=120, anchor="w", stretch=False)
        self.prop_view.column("value", width=200, anchor="w", stretch=True)
        add_treeview_scrollbars(self.prop_view, self.prop_frame)
        # Bind resize handlers on the treeview, its container, and the notebook
        # via :class:`EventDispatcher` so the value column always fills the tab
        # width even before any manual resize. DO NOT REMOVE.
        self.root.after(0, self._resize_prop_columns)
        self.tools_nb.add(self.prop_frame, text="Properties")
        tab_id = self.tools_nb.tabs()[-1]
        self._tool_all_tabs.append(tab_id)
        self.lifecycle_ui._update_tool_tab_visibility()
        self._resize_prop_columns()

        # Tooltip helper for tabs (text may be clipped)
        self._tools_tip = ToolTip(self.tools_nb, "", automatic=False)

        self.tool_actions = {
            "Safety & Security Management": self.open_safety_management_toolbox,
            "Safety & Security Management Explorer": self.manage_safety_management,
            "Safety & Security Case Explorer": self.manage_safety_cases,
            "Safety Performance Indicators": self.show_safety_performance_indicators,
            "Fault Prioritization": self.open_fault_prioritization_window,
            "Cause & Effect Diagram": self.show_cause_effect_chain,
            "Diagram Rule Editor": self.open_diagram_rules_toolbox,
            "Requirement Pattern Editor": self.open_requirement_patterns_toolbox,
            "Report Template Manager": self.open_report_template_manager,
        }

        self.tool_categories: dict[str, list[str]] = {
            "Safety & Security Management": [
                "Safety & Security Management",
                "Safety & Security Management Explorer",
                "Safety & Security Case Explorer",
                "Safety Performance Indicators",
            ],
            "Safety Analysis": [
                "Fault Prioritization",
                "Cause & Effect Diagram",
                "Prototype Assurance Analysis",
            ],
            "Configuration": [
                "Diagram Rule Editor",
                "Requirement Pattern Editor",
                "Report Template Manager",
            ],
        }
        self.tool_to_work_product = {}
        for name, info in self.WORK_PRODUCT_INFO.items():
            tool_name = info[1]
            if tool_name:
                self.tool_to_work_product.setdefault(tool_name, set()).add(name)
        self.tool_to_work_product.setdefault(
            "Cause & Effect Diagram", set()
        ).add("FTA")
        self.tool_listboxes: dict[str, tk.Listbox] = {}
        self._tool_tab_titles: dict[str, str] = {}
        for cat, names in self.tool_categories.items():
            self.lifecycle_ui._add_tool_category(cat, names)

        self.pmhf_var = tk.StringVar(value="")
        self.pmhf_label = ttk.Label(self.analysis_tab, textvariable=self.pmhf_var, foreground="blue")
        self.pmhf_label.pack(side=tk.BOTTOM, fill=tk.X, pady=2)

        # Notebook for diagrams and analyses with navigation buttons
        self.doc_frame = ttk.Frame(self.main_pane)
        self.doc_nb = ClosableNotebook(self.doc_frame)
        # Mapping of tab identifiers to their full, untruncated titles.  The
        # displayed text may be shortened to keep tabs a reasonable size but we
        # keep the originals here for features like duplicate detection.
        self._tab_titles: dict[str, str] = {}
        self._doc_all_tabs: list[str] = []
        self._doc_tab_offset = 0
        _orig_select = self.doc_nb.select

        def _wrapped_select(tab_id=None):
            if tab_id is not None:
                self.lifecycle_ui._make_doc_tab_visible(tab_id)
            return _orig_select(tab_id)

        self.doc_nb.select = _wrapped_select
        self._tab_left_btn = ttk.Button(
            self.doc_frame,
            text="<",
            width=2,
            command=self.lifecycle_ui._select_prev_tab,
            style="Nav.TButton",
        )
        self._tab_right_btn = ttk.Button(
            self.doc_frame,
            text=">",
            width=2,
            command=self.lifecycle_ui._select_next_tab,
            style="Nav.TButton",
        )
        self._tab_left_btn.pack(side=tk.LEFT, fill=tk.Y)
        self._tab_right_btn.pack(side=tk.RIGHT, fill=tk.Y)
        self.doc_nb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.lifecycle_ui._update_doc_tab_visibility()
        self.main_pane.add(self.doc_frame, stretch="always")
        # Tooltip helper for document tabs
        self._doc_tip = ToolTip(self.doc_nb, "", automatic=False)

        # Centralised event binding
        self.event_dispatcher = EventDispatcher(self)
        self.event_dispatcher.register_keyboard_shortcuts()
        self.event_dispatcher.register_tab_events()

        # Do not open the FTA tab by default so the application starts with no
        # documents visible. The tab and the initial top event will be created
        # on demand when the user opens an FTA related view or adds a top level
        # event.  This avoids the spurious "Node 1" appearing at startup.
        # Initialize the canvas related attributes so tab-close callbacks work
        # before the FTA tab has ever been created.
        self.analysis_tabs = {}
        self.canvas_tab = None
        self.canvas_frame = None
        self.canvas = None
        self.hbar = None
        self.vbar = None
        self.page_diagram = None
        self.root_node = None
        self.top_events = []
        self.fmea_entries = []
        self.fmea_service = self.safety_analysis
        self.selected_node = None
        self.dragging_node = None
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.grid_size = 20
        self.update_views()
        # Track the last saved state so we can prompt on exit
        self.last_saved_state = json.dumps(self.export_model_data(), sort_keys=True)
        root.protocol("WM_DELETE_WINDOW", self.confirm_close)
        self.use_case_windows = []
        self.activity_windows = []
        self.block_windows = []
        self.ibd_windows = []

    # ------------------------------------------------------------------
    # UI lifecycle helper wrappers
    # ------------------------------------------------------------------
    def show_properties(self, *args, **kwargs):
        return self.lifecycle_ui.show_properties(*args, **kwargs)

    def _add_tool_category(self, *args, **kwargs):
        return self.lifecycle_ui._add_tool_category(*args, **kwargs)

    def _add_lifecycle_requirements_menu(self, *args, **kwargs):
        return self.lifecycle_ui._add_lifecycle_requirements_menu(*args, **kwargs)

    def _init_nav_button_style(self, *args, **kwargs):
        return self.lifecycle_ui._init_nav_button_style(*args, **kwargs)

    def _limit_explorer_size(self, *args, **kwargs):
        return self.lifecycle_ui._limit_explorer_size(*args, **kwargs)

    def _animate_explorer_show(self, *args, **kwargs):
        return self.lifecycle_ui._animate_explorer_show(*args, **kwargs)

    def _animate_explorer_hide(self, *args, **kwargs):
        return self.lifecycle_ui._animate_explorer_hide(*args, **kwargs)

    def _schedule_explorer_hide(self, *args, **kwargs):
        return self.lifecycle_ui._schedule_explorer_hide(*args, **kwargs)

    def _cancel_explorer_hide(self, *args, **kwargs):
        return self.lifecycle_ui._cancel_explorer_hide(*args, **kwargs)

    def show_explorer(self, *args, **kwargs):
        return self.lifecycle_ui.show_explorer(*args, **kwargs)

    def hide_explorer(self, *args, **kwargs):
        return self.lifecycle_ui.hide_explorer(*args, **kwargs)

    def toggle_explorer_pin(self, *args, **kwargs):
        return self.lifecycle_ui.toggle_explorer_pin(*args, **kwargs)

    def toggle_logs(self, *args, **kwargs):
        return self.lifecycle_ui.toggle_logs(*args, **kwargs)

    def open_metrics_tab(self, *args, **kwargs):
        return self.lifecycle_ui.open_metrics_tab(*args, **kwargs)

    def open_management_window(self, *args, **kwargs):
        return self.nav_input.open_management_window(*args, **kwargs)

    def _register_close(self, *args, **kwargs):
        return self.lifecycle_ui._register_close(*args, **kwargs)

    def _reregister_document(self, *args, **kwargs):
        return self.lifecycle_ui._reregister_document(*args, **kwargs)

    def touch_doc(self, *args, **kwargs):
        return self.lifecycle_ui.touch_doc(*args, **kwargs)

    def show_about(self, *args, **kwargs):
        return self.lifecycle_ui.show_about(*args, **kwargs)

    def _window_has_focus(self, *args, **kwargs):
        ui = getattr(self, "lifecycle_ui", None)
        if ui:
            return ui._window_has_focus(*args, **kwargs)
        return True

    def _window_in_selected_tab(self, *args, **kwargs):
        ui = getattr(self, "lifecycle_ui", None)
        if ui:
            return ui._window_in_selected_tab(*args, **kwargs)
        return True

    def _on_tab_change(self, *args, **kwargs):
        return self.lifecycle_ui._on_tab_change(*args, **kwargs)

    def _on_tab_close(self, *args, **kwargs):
        return self.lifecycle_ui._on_tab_close(*args, **kwargs)

    def _on_doc_tab_motion(self, *args, **kwargs):
        return self.lifecycle_ui._on_doc_tab_motion(*args, **kwargs)

    def _on_tool_tab_motion(self, *args, **kwargs):
        return self.lifecycle_ui._on_tool_tab_motion(*args, **kwargs)

    def _make_doc_tab_visible(self, *args, **kwargs):
        return self.lifecycle_ui._make_doc_tab_visible(*args, **kwargs)

    def _update_doc_tab_visibility(self, *args, **kwargs):
        return self.lifecycle_ui._update_doc_tab_visibility(*args, **kwargs)

    def _update_tool_tab_visibility(self, *args, **kwargs):
        return self.lifecycle_ui._update_tool_tab_visibility(*args, **kwargs)

    def _truncate_tab_title(self, *args, **kwargs):
        return self.lifecycle_ui._truncate_tab_title(*args, **kwargs)

    def _select_next_tab(self, *args, **kwargs):
        return self.lifecycle_ui._select_next_tab(*args, **kwargs)

    def _select_prev_tab(self, *args, **kwargs):
        return self.lifecycle_ui._select_prev_tab(*args, **kwargs)

    def _select_next_tool_tab(self, *args, **kwargs):
        return self.lifecycle_ui._select_next_tool_tab(*args, **kwargs)

    def _select_prev_tool_tab(self, *args, **kwargs):
        return self.lifecycle_ui._select_prev_tool_tab(*args, **kwargs)

    def _new_tab(self, *args, **kwargs):
        return self.lifecycle_ui._new_tab(*args, **kwargs)

    # ------------------------------------------------------------------
    # Label editing and styling helper wrappers
    # ------------------------------------------------------------------
    def edit_controllability(self, *args, **kwargs):
        return self.labels_styling.edit_controllability(*args, **kwargs)

    def edit_description(self, *args, **kwargs):
        return self.labels_styling.edit_description(*args, **kwargs)

    def edit_gate_type(self, *args, **kwargs):
        return self.labels_styling.edit_gate_type(*args, **kwargs)

    def edit_page_flag(self, *args, **kwargs):
        return self.labels_styling.edit_page_flag(*args, **kwargs)

    def edit_rationale(self, *args, **kwargs):
        return self.labels_styling.edit_rationale(*args, **kwargs)

    def edit_selected(self, *args, **kwargs):
        return self.labels_styling.edit_selected(*args, **kwargs)

    def edit_user_name(self, *args, **kwargs):
        return self.labels_styling.edit_user_name(*args, **kwargs)

    def edit_value(self, *args, **kwargs):
        return self.labels_styling.edit_value(*args, **kwargs)

    def rename_failure(self, *args, **kwargs):
        return self.labels_styling.rename_failure(*args, **kwargs)

    def rename_fault(self, *args, **kwargs):
        return self.labels_styling.rename_fault(*args, **kwargs)

    def rename_functional_insufficiency(self, *args, **kwargs):
        return self.labels_styling.rename_functional_insufficiency(*args, **kwargs)

    def rename_hazard(self, *args, **kwargs):
        return self.labels_styling.rename_hazard(*args, **kwargs)

    def rename_malfunction(self, *args, **kwargs):
        return self.labels_styling.rename_malfunction(*args, **kwargs)

    def rename_selected_tree_item(self, *args, **kwargs):
        return self.labels_styling.rename_selected_tree_item(*args, **kwargs)

    def rename_triggering_condition(self, *args, **kwargs):
        return self.labels_styling.rename_triggering_condition(*args, **kwargs)

    def apply_style(self, *args, **kwargs):
        return self.labels_styling.apply_style(*args, **kwargs)

    def format_failure_mode_label(self, *args, **kwargs):
        return self.labels_styling.format_failure_mode_label(*args, **kwargs)

    def _resize_prop_columns(self, *args, **kwargs):
        return self.labels_styling._resize_prop_columns(*args, **kwargs)

    def _spi_label(self, *args, **kwargs):
        return self.labels_styling._spi_label(*args, **kwargs)

    def _product_goal_name(self, *args, **kwargs):
        return self.labels_styling._product_goal_name(*args, **kwargs)

    def _create_icon(self, *args, **kwargs):
        return self.labels_styling._create_icon(*args, **kwargs)

    @property
    def fmeas(self):
        return self.safety_analysis.fmeas

    @fmeas.setter
    def fmeas(self, value):
        self.safety_analysis.fmeas = value

    def show_fmea_list(self):
        """Delegate to the safety analysis facade to display FMEA manager."""
        self.safety_analysis.show_fmea_list()

    def show_fmea_table(self, fmea=None, fmeda=False):
        """Delegate to safety analysis for rendering FMEA/FMeda tables."""
        return self.safety_analysis.show_fmea_table(fmea, fmeda)

    def show_fmeda_list(self):
        """Open the FMEDA document manager via the facade."""
        self.safety_analysis.show_fmeda_list()

        # --- Requirement Traceability Helpers used by reviews and matrix view ---
    def get_requirement_allocation_names(self, req_id):
        return self.requirements_manager.get_requirement_allocation_names(req_id)

    def get_requirement_goal_names(self, req_id):
        return self.requirements_manager.get_requirement_goal_names(req_id)

    def format_requirement(self, req, include_id=True):
        """Return a formatted requirement string without empty ASIL/CAL fields."""
        return self.requirements_manager.format_requirement(req, include_id)

    def format_requirement_with_trace(self, req):
        return self.requirements_manager.format_requirement_with_trace(req)

    def add_requirement(self, tree, refresh_cb):
        return self.requirements_manager.add_requirement(tree, refresh_cb)

    def edit_requirement(self, tree, refresh_cb):
        return self.requirements_manager.edit_requirement(tree, refresh_cb)

    def delete_requirement(self, tree, refresh_cb):
        return self.requirements_manager.delete_requirement(tree, refresh_cb)

    def link_requirement(self, tree, refresh_cb):
        return self.requirements_manager.link_requirement(tree, refresh_cb)

    def unlink_requirement(self, tree, refresh_cb):
        return self.requirements_manager.unlink_requirement(tree, refresh_cb)

    def export_requirements_to_csv(self):
        return self.requirements_manager.export_requirements_to_csv()

    def build_requirement_diff_html(self, review):
        return self.reporting_export.build_requirement_diff_html(review)

    def generate_recommendations_for_top_event(self, node):
        return self.safety_analysis.generate_recommendations_for_top_event(node)

    def back_all_pages(self):
        return self.nav_input.back_all_pages()

    def move_top_event_up(self):
        return self.safety_analysis.move_top_event_up()

    def move_top_event_down(self):
        return self.safety_analysis.move_top_event_down()

    def get_top_level_nodes(self):
        return self.data_access_queries.get_top_level_nodes()

    def get_all_nodes_no_filter(self, node):
        return self.structure_tree_operations.get_all_nodes_no_filter(node)

    def derive_requirements_for_event(self, event):
        return self.safety_analysis.derive_requirements_for_event(event)

    def get_combined_safety_requirements(self, node):
        return self.fta_app.get_combined_safety_requirements(self, node)

    def get_top_event(self, node):
        return self.safety_analysis.get_top_event(node)

    def aggregate_safety_requirements(self, node, all_nodes):
        return self.fta_app.aggregate_safety_requirements(self, node, all_nodes)

    def generate_top_event_summary(self, top_event):
        return self.safety_analysis.generate_top_event_summary(top_event)

    def get_all_nodes(self, node=None):
        return self.structure_tree_operations.get_all_nodes(node)

    def get_all_nodes_table(self, root_node):
        return self.structure_tree_operations.get_all_nodes_table(root_node)

    def get_all_nodes_in_model(self):
        return self.structure_tree_operations.get_all_nodes_in_model()

    def get_all_basic_events(self):
        return self.safety_analysis.get_all_basic_events()

    def get_all_gates(self):
        return self.safety_analysis.get_all_gates()

    def metric_to_text(self, metric_type, value):
        return self.probability_reliability.metric_to_text(metric_type, value)

    def assurance_level_text(self, level):
        return self.probability_reliability.assurance_level_text(level)

    def calculate_cut_sets(self, node):
        return self.safety_analysis.calculate_cut_sets(node)

    def build_hierarchical_argumentation(self, node, indent=0):
        return self.fta_app.build_hierarchical_argumentation(self, node, indent)

    def build_hierarchical_argumentation_common(self, node, indent=0, described=None):
        return self.fta_app.build_hierarchical_argumentation_common(self, node, indent, described)

    def build_page_argumentation(self, page_node):
        return self.fta_app.build_page_argumentation(self, page_node)

    def build_unified_recommendation_table(self):
        return self.reporting_export.build_unified_recommendation_table()

    def build_dynamic_recommendations_table(self):
        return self.reporting_export.build_dynamic_recommendations_table()

    def build_base_events_table_html(self):
        return self.reporting_export.build_base_events_table_html()

    def get_extra_recommendations_list(self, description, level):
        return self.data_access_queries.get_extra_recommendations_list(description, level)

    def get_extra_recommendations_from_level(self, description, level):
        return self.data_access_queries.get_extra_recommendations_from_level(description, level)

    def get_recommendation_from_description(self, description, level):
        return self.data_access_queries.get_recommendation_from_description(description, level)

    def build_argumentation(self, node):
        return self.fta_app.build_argumentation(self, node)

    def auto_create_argumentation(self, node, suppress_top_event_recommendations=False):
        return self.fta_app.auto_create_argumentation(self, node, suppress_top_event_recommendations)

    def analyze_common_causes(self, node):
        return self.probability_reliability.analyze_common_causes(node)

    def build_text_report(self, node, indent=0):
        return self.reporting_export.build_text_report(node, indent)

    def all_children_are_base_events(self, node):
        return self.safety_analysis.all_children_are_base_events(node)

    def build_simplified_fta_model(self, top_event):
        return self.safety_analysis.build_simplified_fta_model(top_event)

    @staticmethod
    def auto_generate_fta_diagram(fta_model, output_path):
        return FTASubApp.auto_generate_fta_diagram(fta_model, output_path)
        
    def find_node_by_id_all(self, unique_id):
        return self.structure_tree_operations.find_node_by_id_all(unique_id)

    def get_hazop_by_name(self, name):
        return self.safety_analysis.get_hazop_by_name(name)

    def get_hara_by_name(self, name):
        return self.safety_analysis.get_hara_by_name(name)

    def update_hara_statuses(self):
        return self.safety_analysis.update_hara_statuses()

    def update_fta_statuses(self):
        return self.safety_analysis.update_fta_statuses()

    def update_requirement_statuses(self):
        return self.requirements_manager.update_requirement_statuses()

    def get_safety_goal_asil(self, sg_name):
        return self.safety_analysis.get_safety_goal_asil(sg_name)

    def get_hara_goal_asil(self, sg_name):
        return self.safety_analysis.get_hara_goal_asil(sg_name)

    def get_cyber_goal_cal(self, goal_id):
        return self.safety_analysis.get_cyber_goal_cal(goal_id)

    def get_top_event_safety_goals(self, node):
        return self.safety_analysis.get_top_event_safety_goals(node)

    def get_safety_goals_for_malfunctions(self, malfunctions: list[str]) -> list[str]:
        return self.safety_analysis.get_safety_goals_for_malfunctions(malfunctions)

    def is_malfunction_used(self, name: str) -> bool:
        return self.safety_analysis.is_malfunction_used(name)

    def add_malfunction(self, name: str) -> None:
        return self.safety_analysis.add_malfunction(name)

    def add_fault(self, name: str) -> None:
        return self.safety_analysis.add_fault(name)

    def add_failure(self, name: str) -> None:
        return self.safety_analysis.add_failure(name)

    def add_hazard(self, name: str, severity: int | str = 1) -> None:
        return self.safety_analysis.add_hazard(name, severity)

    def add_triggering_condition(self, name: str) -> None:
        return self.safety_analysis.add_triggering_condition(name)

    def delete_triggering_condition(self, name: str) -> None:
        return self.safety_analysis.delete_triggering_condition(name)

    def add_functional_insufficiency(self, name: str) -> None:
        return self.safety_analysis.add_functional_insufficiency(name)

    def delete_functional_insufficiency(self, name: str) -> None:
        return self.safety_analysis.delete_functional_insufficiency(name)


    def _update_shared_product_goals(self):
        events = self.top_events + getattr(self, "cta_events", []) + getattr(self, "paa_events", [])
        self.shared_product_goals = self.product_goal_manager.update_shared_product_goals(
            events, getattr(self, "shared_product_goals", {})
        )


    def update_hazard_severity(self, hazard: str, severity: int | str) -> None:
        return self.safety_analysis.update_hazard_severity(hazard, severity)


    def calculate_fmeda_metrics(self, events):
        """Delegate FMEDA metric calculation to the safety analysis facade."""
        return self.safety_analysis.calculate_fmeda_metrics(events)

    def compute_fmeda_metrics(self, events):
        """Delegate detailed FMEDA metric computation to the safety analysis service."""
        return self.safety_analysis.compute_fmeda_metrics(events)

    def sync_hara_to_safety_goals(self):
        """Synchronise HARA results with safety goals via the risk sub-app."""
        return self.risk_app.sync_hara_to_safety_goals(self)

    def sync_cyber_risk_to_goals(self):
        return self.probability_reliability.sync_cyber_risk_to_goals()

    def add_top_level_event(self):
        return self.safety_analysis.add_top_level_event()

    def _build_probability_frame(self, parent, title: str, levels: range, values: dict, row: int, dialog_font):
        return self.probability_reliability._build_probability_frame(parent, title, levels, values, row, dialog_font)

    def edit_project_properties(self) -> None:
        """Open the project properties dialog."""
        ProjectPropertiesDialog(self).show()

    def create_diagram_image(self):  # pragma: no cover - delegation
        return self.diagram_renderer.create_diagram_image()

    def get_page_nodes(self, node):
        return self.data_access_queries.get_page_nodes(node)

    def capture_page_diagram(self, page_node):  # pragma: no cover - delegation
        return self.diagram_renderer.capture_page_diagram(page_node)

    def capture_event_diagram(self, *args, **kwargs):  # pragma: no cover - delegation
        return self.diagram_renderer.capture_event_diagram(*args, **kwargs)

    def capture_gsn_diagram(self, diagram):
        return self.diagram_renderer.capture_gsn_diagram(diagram)

    def capture_sysml_diagram(self, diagram):
        return self.diagram_renderer.capture_sysml_diagram(diagram)

    def capture_cbn_diagram(self, doc):
        return self.diagram_renderer.capture_cbn_diagram(doc)
    
    def draw_subtree_with_filter(self, canvas, root_event, visible_nodes):
        return self.diagram_renderer.draw_subtree_with_filter(canvas, root_event, visible_nodes)

    def draw_subtree(self, canvas, root_event):
        return self.diagram_renderer.draw_subtree(canvas, root_event)

    def draw_connections_subtree(self, canvas, node, drawn_ids):
        return self.diagram_renderer.draw_connections_subtree(canvas, node, drawn_ids)

    def draw_node_on_canvas_pdf(self, canvas, node):
        return self.diagram_renderer.draw_node_on_canvas_pdf(canvas, node)

    def rename_selected_tree_item(self):
        self.tree_app.rename_selected_tree_item(self)

    def save_diagram_png(self):  # pragma: no cover - delegation
        return self.diagram_renderer.save_diagram_png()

    def on_treeview_click(self, event):
        return self.nav_input.on_treeview_click(event)

    def on_analysis_tree_double_click(self, event):
        return self.nav_input.on_analysis_tree_double_click(event)

    def on_analysis_tree_right_click(self, event):
        return self.nav_input.on_analysis_tree_right_click(event)

    def on_analysis_tree_select(self, _event):
        return self.nav_input.on_analysis_tree_select(_event)

    def on_tool_list_double_click(self, event):
        return self.nav_input.on_tool_list_double_click(event)

    def _on_toolbox_change(self) -> None:
        self.governance_manager._on_toolbox_change()

    def apply_governance_rules(self) -> None:
        """Apply governance rules and refresh related UI elements."""
        self.governance_manager.apply_governance_rules()

    def refresh_tool_enablement(self) -> None:
        self.governance_manager.refresh_tool_enablement()

    def update_lifecycle_cb(self) -> None:
        self.governance_manager.update_lifecycle_cb()

    def _export_toolbox_dict(self) -> dict:
        toolbox = getattr(self, "safety_mgmt_toolbox", None)
        if toolbox is None:
            toolbox = SafetyManagementToolbox()
            self.governance_manager.attach_toolbox(toolbox)
            self.safety_mgmt_toolbox = toolbox
        return toolbox.to_dict()

    def on_lifecycle_selected(self, _event=None) -> None:
        phase = self.lifecycle_var.get()
        gm = getattr(self, "governance_manager", None)
        if gm is None:
            gm = GovernanceManager(self)
            self.governance_manager = gm
            gm.attach_toolbox(getattr(self, "safety_mgmt_toolbox", None))
        gm.on_lifecycle_selected(phase)


    def enable_process_area(self, area: str) -> str:  # pragma: no cover - delegation
        return self.validation_consistency.enable_process_area(area)

    def enable_work_product(self, name: str, *, refresh: bool = True) -> None:  # pragma: no cover - delegation
        return self.validation_consistency.enable_work_product(name, refresh=refresh)

    def can_remove_work_product(self, name: str) -> bool:  # pragma: no cover - delegation
        return self.validation_consistency.can_remove_work_product(name)

    def disable_work_product(self, name: str, *, force: bool = False, refresh: bool = True) -> bool:  # pragma: no cover - delegation
        return self.validation_consistency.disable_work_product(name, force=force, refresh=refresh)

    def open_work_product(self, name: str) -> None:
        """Open a diagram or analysis work product within the application."""
        wp = next(
            (wp for wp, info in self.WORK_PRODUCT_INFO.items() if info[1] == name or wp == name),
            None,
        )
        global_enabled = getattr(self, "enabled_work_products", set())
        smt = getattr(self, "safety_mgmt_toolbox", None)
        if smt and getattr(smt, "work_products", None):
            phase_enabled = smt.enabled_products()
        else:
            phase_enabled = global_enabled
        if wp and wp not in (global_enabled & phase_enabled):
            return
        action = self.tool_actions.get(name)
        if callable(action):
            action()
            return

        for diag in self.arch_diagrams:
            if getattr(diag, "name", "") == name or getattr(diag, "diag_id", "") == name:
                self.window_controllers.open_arch_window(diag.diag_id)
                return

        for idx, diag in enumerate(self.management_diagrams):
            if getattr(diag, "name", "") == name or getattr(diag, "diag_id", "") == name:
                self.nav_input.open_management_window(idx)
                return

        for diag in getattr(self, "all_gsn_diagrams", []):
            if getattr(diag.root, "user_name", "") == name or getattr(diag, "diag_id", "") == name:
                self.window_controllers.open_gsn_diagram(diag)
                return


    # ----------------------------------------------------------------------
    # NEVER DELETE OR TOUCH THIS: helper keeps the value column synced with
    # the Properties tab width. Removing this breaks property display.
    # ----------------------------------------------------------------------


    def on_ctrl_mousewheel(self, event):
        return self.nav_input.on_ctrl_mousewheel(event)

    def new_model(self):
        self.project_manager.new_model()

    def compute_occurrence_counts(self):
        counts = {}
        visited = set()

        if self.root_node is None:
            return counts

        def rec(node):
            if node.unique_id in visited:
                counts[node.unique_id] += 1
            else:
                visited.add(node.unique_id)
                counts[node.unique_id] = 1
            for child in node.children:
                rec(child)

        rec(self.root_node)
        return counts

    def get_node_fill_color(self, node, mode: str | None = None):
        """Return the fill color for *node* based on analysis mode.

        Parameters
        ----------
        node: FaultTreeNode | None
            Unused but kept for API compatibility.
        mode: str | None
            Explicit diagram mode to use.  Falls back to the currently
            focused canvas' ``diagram_mode`` when ``None``.
        """

        diagram_mode = mode or getattr(getattr(self, "canvas", None), "diagram_mode", "FTA")
        if diagram_mode == "CTA":
            return "#EE82EE"
        if diagram_mode == "PAA":
            return "#40E0D0"
        return "#FAD7A0"

    def on_right_mouse_press(self, event):
        return self.nav_input.on_right_mouse_press(event)

    def on_right_mouse_drag(self, event):
        return self.nav_input.on_right_mouse_drag(event)

    def on_right_mouse_release(self, event):
        return self.nav_input.on_right_mouse_release(event)

    def show_context_menu(self, event):
        return self.nav_input.show_context_menu(event)

    def on_canvas_click(self, event):
        return self.nav_input.on_canvas_click(event)

    def on_canvas_double_click(self, event):
        return self.nav_input.on_canvas_double_click(event)

    def on_canvas_drag(self, event):
        return self.nav_input.on_canvas_drag(event)

    def on_canvas_release(self, event):
        return self.nav_input.on_canvas_release(event)

    def move_subtree(self, node, dx, dy):
        return self.structure_tree_operations.move_subtree(node, dx, dy)

    def zoom_in(self):  # pragma: no cover - delegation
        return self.diagram_renderer.zoom_in()

    def zoom_out(self):  # pragma: no cover - delegation
        return self.diagram_renderer.zoom_out()


    # ------------------------------------------------------------------
    # Explorer panel show/hide helpers

    def auto_arrange(self):
        if self.root_node is None:
            return
        horizontal_gap = 150
        vertical_gap = 100
        next_y = [100]
        def layout(node, depth):
            node.x = depth * horizontal_gap + 100
            if not node.children:
                node.y = next_y[0]
                next_y[0] += vertical_gap
            else:
                for child in node.children:
                    layout(child, depth+1)
                node.y = (node.children[0].y + node.children[-1].y) / 2
        layout(self.root_node, 0)
        # --- Center the layout horizontally on the canvas ---
        all_nodes = self.get_all_nodes(self.root_node)
        if all_nodes:
            min_x = min(n.x for n in all_nodes)
            max_x = max(n.x for n in all_nodes)
            canvas_width = self.canvas.winfo_width()
            if canvas_width < 10:
                canvas_width = 800
            diagram_width = max_x - min_x
            offset = (canvas_width / self.zoom - diagram_width) / 2 - min_x
            for n in all_nodes:
                n.x += offset
        self.update_views()


    def get_all_triggering_conditions(self):
        return self.data_access_queries.get_all_triggering_conditions()

    def get_all_functional_insufficiencies(self):
        return self.data_access_queries.get_all_functional_insufficiencies()

    def get_all_scenario_names(self):
        return self.data_access_queries.get_all_scenario_names()

    def get_validation_targets_for_odd(self, element_name):
        """Wrapper for :class:`RiskAssessmentSubApp` ODD validation lookup."""
        return self.risk_app.get_validation_targets_for_odd(self, element_name)

    def get_scenario_exposure(self, name: str) -> int:
        return self.data_access_queries.get_scenario_exposure(name)

    def get_all_scenery_names(self):
        return self.data_access_queries.get_all_scenery_names()


    def get_all_function_names(self):
        return self.data_access_queries.get_all_function_names()

    def get_all_action_names(self):
        return self.data_access_queries.get_all_action_names()

    def get_all_action_labels(self) -> list[str]:
        return self.data_access_queries.get_all_action_labels()

    def get_use_case_for_function(self, func: str) -> str:
        return self.data_access_queries.get_use_case_for_function(func)

    def get_all_component_names(self):
        return self.data_access_queries.get_all_component_names()

    def get_all_part_names(self) -> list[str]:
        return self.data_access_queries.get_all_part_names()

    def get_all_malfunction_names(self):
        return self.data_access_queries.get_all_malfunction_names()

    def get_hazards_for_malfunction(self, malfunction: str, hazop_names=None) -> list[str]:
        """Wrapper for :class:`RiskAssessmentSubApp` hazard lookup."""
        return self.risk_app.get_hazards_for_malfunction(self, malfunction, hazop_names)

    def update_odd_elements(self):
        return self.safety_analysis.update_odd_elements()

    def update_hazard_list(self):
        return self.safety_analysis.update_hazard_list()

    def update_failure_list(self):
        return self.safety_analysis.update_failure_list()

    def update_triggering_condition_list(self):
        return self.safety_analysis.update_triggering_condition_list()

    def update_functional_insufficiency_list(self):
        return self.safety_analysis.update_functional_insufficiency_list()

    def get_entry_field(self, entry, field, default=""):
        return self.data_access_queries.get_entry_field(entry, field, default)

    def get_all_failure_modes(self):
        return self.safety_analysis.get_all_failure_modes()

    def get_all_fmea_entries(self):
        return self.safety_analysis.get_all_fmea_entries()

    def get_non_basic_failure_modes(self):
        return self.safety_analysis.get_non_basic_failure_modes()

    def get_available_failure_modes_for_gates(self, current_gate=None):
        return self.safety_analysis.get_available_failure_modes_for_gates(current_gate)

    def get_failure_mode_node(self, node):
        return self.safety_analysis.get_failure_mode_node(node)

    def get_component_name_for_node(self, node):
        return self.safety_analysis.get_component_name_for_node(node)

    def get_failure_modes_for_malfunction(self, malfunction: str) -> list[str]:
        return self.safety_analysis.get_failure_modes_for_malfunction(malfunction)

    def get_faults_for_failure_mode(self, failure_mode_node) -> list[str]:
        return self.safety_analysis.get_faults_for_failure_mode(failure_mode_node)

    def get_fit_for_fault(self, fault_name: str) -> float:
        return self.safety_analysis.get_fit_for_fault(fault_name)

    def update_views(self):
        """Refresh project views via the dedicated :class:`ViewUpdater`."""
        self.view_update_service.update_views()

    def update_basic_event_probabilities(self):
        return self.safety_analysis.update_basic_event_probabilities()

    def validate_float(self, value):
        """Return ``True`` if ``value`` resembles a float.

        This validator is tolerant of scientific-notation inputs that are
        entered incrementally (e.g. ``"1e"`` or ``"1e-"``) to keep the entry
        widget from rejecting keystrokes during editing.
        """

        if value in ("", "-", "+", ".", "-.", "+.", "e", "E", "e-", "e+", "E-", "E+"):
            return True
        try:
            float(value)
            return True
        except ValueError:
            lower = value.lower()
            if lower.endswith("e"):
                try:
                    float(lower[:-1])
                    return True
                except ValueError:
                    return False
            if lower.endswith(("e-", "e+")):
                try:
                    float(lower[:-2])
                    return True
                except ValueError:
                    return False
            return False

    def compute_failure_prob(self, node, failure_mode_ref=None, formula=None):
        return self.probability_reliability.compute_failure_prob(node, failure_mode_ref=failure_mode_ref, formula=formula)


    def propagate_failure_mode_attributes(self, fm_node):
        """Update basic events referencing ``fm_node`` and recompute probability."""
        return self.fmeda_manager.propagate_failure_mode_attributes(fm_node)


    def refresh_model(self):
        return self.safety_analysis.refresh_model()

    def refresh_all(self):
        return self.safety_analysis.refresh_all()

    def insert_node_in_tree(self, parent_item, node):
        return self.structure_tree_operations.insert_node_in_tree(parent_item, node)

    def redraw_canvas(self):
        return self.diagram_renderer.redraw_canvas()

    def create_diagram_image_without_grid(self):
        return self.diagram_renderer.create_diagram_image_without_grid()

    def draw_connections(self, node, drawn_ids=set()):
        return self.diagram_renderer.draw_connections(node, drawn_ids)

    def draw_node(self, node):
        return self.diagram_renderer.draw_node(node)

    def find_node_by_id(self, node, unique_id, visited=None):
        return self.structure_tree_operations.find_node_by_id(node, unique_id, visited)

    def is_descendant(self, node, possible_ancestor):
        return self.structure_tree_operations.is_descendant(node, possible_ancestor)

    def add_node_of_type(self, event_type):
        """Delegate creation of a node of ``event_type`` to model helper."""
        return _add_node_of_type(self, event_type)

    def add_basic_event_from_fmea(self):
        FaultTreeNode.add_basic_event_from_fmea(self)

    def remove_node(self):
        return self.structure_tree_operations.remove_node()

    def remove_connection(self, node):
        return self.structure_tree_operations.remove_connection(node)

    def delete_node_and_subtree(self, node):
        return self.structure_tree_operations.delete_node_and_subtree(node)

    # ------------------------------------------------------------------
    # Helpers for malfunctions and failure modes
    # ------------------------------------------------------------------
    def create_top_event_for_malfunction(self, name: str) -> None:
        return self.top_event_workflows.create_top_event_for_malfunction(name)

    def delete_top_events_for_malfunction(self, name: str) -> None:
        return self.safety_analysis.delete_top_events_for_malfunction(name)

    def add_gate_from_failure_mode(self):
        return self.top_event_workflows.add_gate_from_failure_mode()

    def add_fault_event(self):
        return self.safety_analysis.add_fault_event()

    def calculate_overall(self):
        return self.probability_reliability.calculate_overall()

    def calculate_pmfh(self):
        return self.probability_reliability.calculate_pmfh()

    def show_requirements_matrix(self):
        return self.editors_service.show_requirements_matrix()

    def show_item_definition_editor(self):
        return self.editors_service.show_item_definition_editor()

    def show_safety_concept_editor(self):
        return self.editors_service.show_safety_concept_editor()

    def show_requirements_editor(self):
        return self.editors_service.show_requirements_editor()

    def _show_fmea_table_impl(self, fmea=None, fmeda=False):
        return self.editors_service._show_fmea_table_impl(fmea, fmeda)

    def export_fmea_to_csv(self, fmea, path):
        return self.safety_analysis.export_fmea_to_csv(fmea, path)

    def export_fmeda_to_csv(self, fmeda, path):
        return self.safety_analysis.export_fmeda_to_csv(fmeda, path)


    def show_traceability_matrix(self):
        """Display a traceability matrix linking FTA basic events to FMEA components."""
        return self.requirements_manager.show_traceability_matrix()

    def collect_requirements_recursive(self, node):
        return self.safety_analysis.collect_requirements_recursive(node)

    def show_safety_goals_matrix(self):
        """Display product goals and derived requirements in a tree view."""
        return self.requirements_manager.show_safety_goals_matrix()

    def show_product_goals_editor(self):
        """Allow editing of top-level product goals."""
        return self.requirements_manager.show_product_goals_editor()

    def _parse_spi_target(self, target: str) -> tuple[str, str]:
        return self.safety_case_manager.parse_spi_target(target)

    def get_spi_targets(self) -> list[str]:
        return self.safety_case_manager.get_spi_targets()

    def show_safety_performance_indicators(self):
        return self.safety_case_manager.show_safety_performance_indicators()

    def refresh_safety_performance_indicators(self):
        return self.safety_case_manager.refresh_safety_performance_indicators()

    def refresh_safety_case_table(self):
        return self.safety_case_manager.refresh_safety_case_table()

    def show_safety_case(self):
        return self.safety_case_manager.show_safety_case()

    def export_product_goal_requirements(self):
        return self.reporting_export.export_product_goal_requirements()
    def generate_phase_requirements(self, phase: str) -> None:
        """Generate requirements for all governance diagrams in a phase."""
        self.open_safety_management_toolbox(show_diagrams=False)
        win = getattr(self, "safety_mgmt_window", None)
        if win:
            win.generate_phase_requirements(phase)

    def generate_lifecycle_requirements(self) -> None:
        """Generate requirements for all governance diagrams outside phases."""
        self.open_safety_management_toolbox(show_diagrams=False)
        win = getattr(self, "safety_mgmt_window", None)
        if win:
            win.generate_lifecycle_requirements()


    def _refresh_phase_requirements_menu(self) -> None:
        return self.requirements_manager.refresh_phase_requirements_menu()

    def export_cybersecurity_goal_requirements(self):
        return self.reporting_export.export_cybersecurity_goal_requirements()

    def build_cause_effect_data(self):
        return self.probability_reliability.build_cause_effect_data()

    def _build_cause_effect_graph(self, row):
        return self.probability_reliability._build_cause_effect_graph(row)

    def render_cause_effect_diagram(self, row):
        return self.probability_reliability.render_cause_effect_diagram(row)
    def show_cause_effect_chain(self):
        return self.safety_analysis.show_cause_effect_chain()

    def show_cut_sets(self):
        return self.safety_analysis.show_cut_sets()

    def show_common_cause_view(self):
        return self.safety_analysis.show_common_cause_view()

    def manage_mission_profiles(self):
        return self.mission_profile_manager.manage_mission_profiles()

    def manage_mechanism_libraries(self):
        return self.nav_input.manage_mechanism_libraries()

    def manage_scenario_libraries(self):
        return self.scenario_library_manager.manage_scenario_libraries()

    def manage_odd_libraries(self):
        return self.odd_library_manager.manage_odd_libraries()

    def open_reliability_window(self):
        return self.nav_input.open_reliability_window()

    def open_fmeda_window(self):
        return self.nav_input.open_fmeda_window()

    def open_hazop_window(self):
        return self.nav_input.open_hazop_window()

    def open_risk_assessment_window(self):
        return self.nav_input.open_risk_assessment_window()

    def open_stpa_window(self):
        return self.nav_input.open_stpa_window()

    def open_threat_window(self):
        return self.nav_input.open_threat_window()

    def open_fi2tc_window(self):
        return self.nav_input.open_fi2tc_window()

    def open_tc2fi_window(self):
        return self.nav_input.open_tc2fi_window()

    def open_fault_prioritization_window(self):
        return self.nav_input.open_fault_prioritization_window()

    def open_safety_management_toolbox(self, show_diagrams: bool = True):
        return self.nav_input.open_safety_management_toolbox(show_diagrams)

    def open_diagram_rules_toolbox(self):
        """Open editor for diagram rule configuration."""
        tab_exists = (
            hasattr(self, "_diagram_rules_tab") and self._diagram_rules_tab.winfo_exists()
        )
        editor_exists = (
            hasattr(self, "diagram_rules_editor")
            and self.diagram_rules_editor.winfo_exists()
        )
        if tab_exists:
            self.doc_nb.select(self._diagram_rules_tab)
            if editor_exists:
                return
            parent = self._diagram_rules_tab
        else:
            parent = self._diagram_rules_tab = self.lifecycle_ui._new_tab("Diagram Rules")

        from gui.diagram_rules_toolbox import DiagramRulesEditor

        self.diagram_rules_editor = DiagramRulesEditor(parent, self, _CONFIG_PATH)
        self.diagram_rules_editor.pack(fill=tk.BOTH, expand=True)

    def open_requirement_patterns_toolbox(self):
        """Open editor for requirement pattern definitions."""
        tab_exists = (
            hasattr(self, "_req_patterns_tab") and self._req_patterns_tab.winfo_exists()
        )
        editor_exists = (
            hasattr(self, "requirement_patterns_editor")
            and self.requirement_patterns_editor.winfo_exists()
        )
        if tab_exists:
            self.doc_nb.select(self._req_patterns_tab)
            if editor_exists:
                return
            parent = self._req_patterns_tab
        else:
            parent = self._req_patterns_tab = self.lifecycle_ui._new_tab("Requirement Patterns")

        from gui.requirement_patterns_toolbox import RequirementPatternsEditor

        self.requirement_patterns_editor = RequirementPatternsEditor(
            parent, self, _PATTERN_PATH
        )
        self.requirement_patterns_editor.pack(fill=tk.BOTH, expand=True)

    def open_report_template_toolbox(self):
        """Open editor for PDF report template configuration."""
        tab_exists = (
            hasattr(self, "_report_template_tab") and self._report_template_tab.winfo_exists()
        )
        editor_exists = (
            hasattr(self, "report_template_editor")
            and self.report_template_editor.winfo_exists()
        )
        if tab_exists:
            self.doc_nb.select(self._report_template_tab)
            if editor_exists:
                return
            parent = self._report_template_tab
        else:
            parent = self._report_template_tab = self.lifecycle_ui._new_tab("Report Template")

        from gui.report_template_toolbox import ReportTemplateEditor

        self.report_template_editor = ReportTemplateEditor(
            parent, self, _REPORT_TEMPLATE_PATH
        )
        self.report_template_editor.pack(fill=tk.BOTH, expand=True)

    def open_report_template_manager(self):
        """Open manager for multiple report templates."""
        tab_exists = (
            hasattr(self, "_report_template_mgr_tab")
            and self._report_template_mgr_tab.winfo_exists()
        )
        manager_exists = (
            hasattr(self, "report_template_manager")
            and self.report_template_manager.winfo_exists()
        )
        if tab_exists:
            self.doc_nb.select(self._report_template_mgr_tab)
            if manager_exists:
                return
            parent = self._report_template_mgr_tab
        else:
            parent = self._report_template_mgr_tab = self.lifecycle_ui._new_tab("Report Templates")

        from gui.report_template_manager import ReportTemplateManager

        self.report_template_manager = ReportTemplateManager(
            parent, self, _REPORT_TEMPLATE_PATH.parent
        )
        self.report_template_manager.pack(fill=tk.BOTH, expand=True)

    def reload_config(self) -> None:
        """Reload diagram rule configuration across all interested modules."""

        import sys

        _reload_local_config()

        for mod in list(sys.modules.values()):
            if hasattr(mod, "reload_config"):
                try:  # pragma: no cover - defensive programming
                    mod.reload_config()
                except Exception:
                    pass

        if hasattr(self, "canvas") and getattr(self.canvas, "winfo_exists", lambda: False)():
            self.redraw_canvas()
        pd = getattr(self, "page_diagram", None)
        if pd and getattr(pd.canvas, "winfo_exists", lambda: False)():
            pd.redraw_canvas()

    def open_search_toolbox(self):
        return self.nav_input.open_search_toolbox()

    def open_style_editor(self):
        """Open the diagram style editor window."""
        StyleEditor(self.root)



    def refresh_styles(self, event=None):
        """Redraw all open diagram windows using current styles."""
        if getattr(self, 'canvas', None):
            self.canvas.config(bg=StyleManager.get_instance().canvas_bg)
        for tab in getattr(self, 'diagram_tabs', {}).values():
            for child in tab.winfo_children():
                if hasattr(child, 'redraw'):
                    child.redraw()

    def show_hazard_explorer(self):
        return self.safety_analysis.show_hazard_explorer()

    def show_requirements_explorer(self):
        if hasattr(self, "_req_exp_tab") and self._req_exp_tab.winfo_exists():
            self.doc_nb.select(self._req_exp_tab)
        else:
            self._req_exp_tab = self.lifecycle_ui._new_tab("Requirements Explorer")
            self._req_exp_window = RequirementsExplorerWindow(self._req_exp_tab, self)
            self._req_exp_window.pack(fill=tk.BOTH, expand=True)


    def _create_fta_tab(self, diagram_mode: str = "FTA"):
        """Create the main FTA tab with canvas and bindings.

        Parameters
        ----------
        diagram_mode: str
            The operational mode of the diagram (``"FTA"`` or ``"CTA"``).
        """
        tabs = getattr(self, "analysis_tabs", {})
        existing = tabs.get(diagram_mode)
        
        if existing and existing["tab"].winfo_exists():
            self.canvas_tab = existing["tab"]
            self.canvas_frame = existing["tab"]
            self.canvas = existing["canvas"]
            self.hbar = existing["hbar"]
            self.vbar = existing["vbar"]
            self.diagram_mode = diagram_mode
            self.doc_nb.select(self.canvas_tab)
            self._update_analysis_menus(diagram_mode)
            return

        canvas_tab = ttk.Frame(self.doc_nb)
        self.doc_nb.add(canvas_tab, text="FTA" if diagram_mode == "FTA" else diagram_mode)

        canvas = tk.Canvas(canvas_tab, bg=StyleManager.get_instance().canvas_bg)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        hbar = ttk.Scrollbar(canvas_tab, orient=tk.HORIZONTAL, command=canvas.xview)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        vbar = ttk.Scrollbar(canvas_tab, orient=tk.VERTICAL, command=canvas.yview)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set,
                      scrollregion=(0, 0, 2000, 2000))
        canvas.bind("<ButtonPress-3>", self.on_right_mouse_press)
        canvas.bind("<B3-Motion>", self.on_right_mouse_drag)
        canvas.bind("<ButtonRelease-3>", self.on_right_mouse_release)
        canvas.bind("<Button-1>", self.on_canvas_click)
        canvas.bind("<B1-Motion>", self.on_canvas_drag)
        canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        canvas.bind("<Double-1>", self.on_canvas_double_click)
        canvas.bind("<Control-MouseWheel>", self.on_ctrl_mousewheel)

        canvas.diagram_mode = diagram_mode
        self.analysis_tabs[diagram_mode] = {
            "tab": canvas_tab,
            "canvas": canvas,
            "hbar": hbar,
            "vbar": vbar,
        }
        self.canvas_tab = canvas_tab
        self.canvas_frame = canvas_tab
        self.canvas = canvas
        self.hbar = hbar
        self.vbar = vbar
        self.diagram_mode = diagram_mode
        self.doc_nb.select(canvas_tab)
        self._update_analysis_menus(diagram_mode)

    def create_fta_diagram(self):
        """Initialize an FTA diagram and its top-level event."""
        self._create_fta_tab("FTA")
        self.add_top_level_event()
        if getattr(self, "fta_root_node", None):
            self.window_controllers.open_page_diagram(self.fta_root_node)

    def create_cta_diagram(self):
        """Initialize a CTA diagram and its top-level event."""
        self.cta_manager.create_diagram()

    def _update_analysis_menus(self, mode=None):
        """Enable or disable node-adding menu items based on diagram mode."""
        if mode is None:
            mode = getattr(self, "diagram_mode", "FTA")
        self.enable_fta_actions(mode == "FTA")
        self.cta_manager.enable_actions(mode == "CTA")
        self.validation_consistency.enable_paa_actions(mode == "PAA")

    @property
    def pages_and_paa(self):
        """Lazily create and return the Pages_and_PAA helper."""
        if not hasattr(self, "_pages_and_paa"):
            from .pages_and_paa import Pages_and_PAA

            self._pages_and_paa = Pages_and_PAA(self)
        return self._pages_and_paa

    def ensure_fta_tab(self):  # pragma: no cover - delegation
        return self.validation_consistency.ensure_fta_tab()

    def open_use_case_diagram(self):
        self.window_controllers.open_use_case_diagram()

    def open_activity_diagram(self):
        self.window_controllers.open_activity_diagram()

    def open_block_diagram(self):
        self.window_controllers.open_block_diagram()

    def open_internal_block_diagram(self):
        self.window_controllers.open_internal_block_diagram()

    def open_control_flow_diagram(self):
        self.window_controllers.open_control_flow_diagram()

    def open_causal_bayesian_network_window(self):
        self.window_controllers.open_causal_bayesian_network_window()

    def open_gsn_diagram(self, diagram):
        self.window_controllers.open_gsn_diagram(diagram)

    def open_arch_window(self, diag_id: str) -> None:
        self.window_controllers.open_arch_window(diag_id)

    def open_page_diagram(self, node, push_history=True):
        self.window_controllers.open_page_diagram(node, push_history)

    def manage_architecture(self):
        return self.nav_input.manage_architecture()

    def manage_gsn(self):
        self.gsn_manager.manage_gsn()

    def manage_safety_management(self):
        return self.nav_input.manage_safety_management()

    def manage_safety_cases(self):
        return self.safety_case_manager.manage_safety_cases()


    def _diagram_copy_strategy1(self):
        win = self.window_controllers._focused_cbn_window()
        if win and getattr(win, "selected_node", None) and getattr(win, "copy_selected", None):
            self.selected_node = None
            self.clipboard_node = None
            self.cut_mode = False
            win.copy_selected()
            return True
        return False

    def _diagram_copy_strategy2(self):
        win = self.window_controllers._focused_gsn_window()
        if win and getattr(win, "selected_node", None) and getattr(win, "copy_selected", None):
            self.selected_node = None
            self.clipboard_node = None
            self.cut_mode = False
            win.copy_selected()
            return True
        return False

    def _diagram_copy_strategy3(self):
        win = getattr(self, "active_arch_window", None)
        if win and getattr(win, "selected_obj", None) and getattr(win, "copy_selected", None):
            self.selected_node = None
            self.clipboard_node = None
            self.cut_mode = False
            win.copy_selected()
            return True
        return False

    def _diagram_copy_strategy4(self):
        for ref in list(ARCH_WINDOWS):
            win = ref()
            if win and getattr(win, "selected_obj", None) and getattr(win, "copy_selected", None):
                self.selected_node = None
                self.clipboard_node = None
                self.cut_mode = False
                win.copy_selected()
                return True
        return False

    def _diagram_cut_strategy1(self):
        win = self.window_controllers._focused_cbn_window()
        if win and getattr(win, "selected_node", None) and getattr(win, "cut_selected", None):
            self.selected_node = None
            self.clipboard_node = None
            self.cut_mode = False
            win.cut_selected()
            return True
        return False

    def _diagram_cut_strategy2(self):
        win = self.window_controllers._focused_gsn_window()
        if win and getattr(win, "selected_node", None) and getattr(win, "cut_selected", None):
            self.selected_node = None
            self.clipboard_node = None
            self.cut_mode = False
            win.cut_selected()
            return True
        return False

    def _diagram_cut_strategy3(self):
        win = getattr(self, "active_arch_window", None)
        if win and getattr(win, "selected_obj", None) and getattr(win, "cut_selected", None):
            self.selected_node = None
            self.clipboard_node = None
            self.cut_mode = False
            win.cut_selected()
            return True
        return False

    def _diagram_cut_strategy4(self):
        for ref in list(ARCH_WINDOWS):
            win = ref()
            if win and getattr(win, "selected_obj", None) and getattr(win, "cut_selected", None):
                self.selected_node = None
                self.clipboard_node = None
                self.cut_mode = False
                win.cut_selected()
                return True
        return False

    def copy_node(self):
        if self.diagram_clipboard:
            self.diagram_clipboard.copy_node()

    def cut_node(self):
        if self.diagram_clipboard:
            self.diagram_clipboard.cut_node()

    # ------------------------------------------------------------------
    def _reset_gsn_clone(self, node):
        if isinstance(node, GSNNode):
            node.unique_id = str(uuid.uuid4())
            old_children = list(getattr(node, "children", []))
            node.children = []
            node.parents = []
            node.context_children = []
            node.is_primary_instance = False
            if getattr(node, "original", None) is None:
                node.original = node
            for child in old_children:
                self._reset_gsn_clone(child)

    # ------------------------------------------------------------------
    def _clone_for_paste_strategy1(self, node, parent=None):
        if hasattr(node, "clone"):
            if parent and getattr(node, "node_type", None) in {"Context", "Assumption", "Justification"}:
                return node.clone(parent)
            return node.clone()
        import copy
        clone = copy.deepcopy(node)
        self._reset_gsn_clone(clone)
        return clone

    def _clone_for_paste_strategy2(self, node, parent=None):
        import copy
        if isinstance(node, GSNNode):
            if parent and node.node_type in {"Context", "Assumption", "Justification"}:
                return node.clone(parent)
            return node.clone()
        clone = copy.deepcopy(node)
        self._reset_gsn_clone(clone)
        return clone

    def _clone_for_paste_strategy3(self, node, parent=None):
        try:
            if parent and getattr(node, "node_type", None) in {"Context", "Assumption", "Justification"}:
                return node.clone(parent)  # type: ignore[attr-defined]
            return node.clone()  # type: ignore[attr-defined]
        except Exception:
            import copy
            clone = copy.deepcopy(node)
            self._reset_gsn_clone(clone)
            return clone

    def _clone_for_paste_strategy4(self, node, parent=None):
        import copy
        clone = copy.deepcopy(node)
        self._reset_gsn_clone(clone)
        return clone

    def _clone_for_paste(self, node, parent=None):
        for strat in (
            self._clone_for_paste_strategy1,
            self._clone_for_paste_strategy2,
            self._clone_for_paste_strategy3,
            self._clone_for_paste_strategy4,
        ):
            try:
                clone = strat(node, parent)
                if clone is not None:
                    return clone
            except ValueError:
                messagebox.showwarning("Clone", "Cannot clone this node type.")
                return None
            except Exception:
                continue
        messagebox.showwarning("Clone", "Cannot clone this node type.")
        return None

    def _prepare_node_for_paste(self, target):
        """Return appropriate node instance when pasting."""
        if (
            isinstance(self.clipboard_node, GSNNode)
            and target in getattr(self.clipboard_node, "parents", [])
        ):
            return self._clone_for_paste(self.clipboard_node)
        from mainappsrc.models.fta.fault_tree_node import FaultTreeNode

        if (
            isinstance(self.clipboard_node, FaultTreeNode)
            or type(self.clipboard_node).__name__ == "FaultTreeNode"
        ):
            return self._clone_for_paste(self.clipboard_node)
        return self.clipboard_node

    def paste_node(self):
        if self.diagram_clipboard:
            self.diagram_clipboard.paste_node()

    def _get_diag_type(self, win):
        repo = getattr(win, "repo", None)
        diag_id = getattr(win, "diagram_id", None)
        if repo and diag_id:
            diag = repo.diagrams.get(diag_id)
            if diag:
                return diag.diag_type
        return None


    def clone_node_preserving_id(self, node, parent=None):
        """Delegate cloning to :class:`NodeCloneService`."""
        return self.node_clone_service.clone_node_preserving_id(node, parent)

    def _find_gsn_diagram(self, node):
        """Return the GSN diagram containing ``node`` if known.

        The application keeps GSN diagrams either in ``gsn_diagrams`` or nested
        inside modules.  When pasting a GSN node we must ensure the element is
        registered with its diagram's ``nodes`` list so it is rendered
        correctly.  This helper performs a recursive search through all known
        diagrams and modules to locate the owning diagram of ``node``.
        """

        for diag in getattr(self, "gsn_diagrams", []):
            if node in getattr(diag, "nodes", []):
                return diag

        def _search_modules(modules):
            for mod in modules:
                for diag in getattr(mod, "diagrams", []):
                    if node in getattr(diag, "nodes", []):
                        return diag
                result = _search_modules(getattr(mod, "modules", []))
                if result:
                    return result
            return None

        return _search_modules(getattr(self, "gsn_modules", []))

    def _copy_attrs_no_xy_strategy1(self, target, source, attrs):
        tx, ty = getattr(target, "x", None), getattr(target, "y", None)
        for attr in attrs:
            setattr(target, attr, getattr(source, attr, None))
        if tx is not None:
            target.x = tx
        if ty is not None:
            target.y = ty

    def _copy_attrs_no_xy_strategy2(self, target, source, attrs):
        tx, ty = getattr(target, "x", None), getattr(target, "y", None)
        values = {a: getattr(source, a, None) for a in attrs if hasattr(source, a)}
        for a, v in values.items():
            setattr(target, a, v)
        if tx is not None:
            target.x = tx
        if ty is not None:
            target.y = ty

    def _copy_attrs_no_xy_strategy3(self, target, source, attrs):
        tx, ty = getattr(target, "x", None), getattr(target, "y", None)
        for attr in attrs:
            if attr in {"x", "y"}:
                continue
            setattr(target, attr, getattr(source, attr, None))
        if tx is not None:
            target.x = tx
        if ty is not None:
            target.y = ty

    def _copy_attrs_no_xy_strategy4(self, target, source, attrs):
        tx, ty = getattr(target, "x", None), getattr(target, "y", None)
        for attr in attrs:
            try:
                setattr(target, attr, getattr(source, attr))
            except Exception:
                continue
        if tx is not None:
            target.x = tx
        if ty is not None:
            target.y = ty

    def _copy_attrs_no_xy(self, target, source, attrs):
        for strat in (
            self._copy_attrs_no_xy_strategy1,
            self._copy_attrs_no_xy_strategy2,
            self._copy_attrs_no_xy_strategy3,
            self._copy_attrs_no_xy_strategy4,
        ):
            try:
                strat(target, source, attrs)
                return
            except Exception:
                continue

    def sync_nodes_by_id(self, updated_node):  # pragma: no cover - simple delegation
        """Delegate to :class:`Syncing_And_IDs` helper."""

        return self.syncing_and_ids.sync_nodes_by_id(updated_node)

       




    def edit_severity(self):
        messagebox.showinfo(
            "Severity",
            "Severity is determined from the risk assessment and cannot be edited here.",
        )



    def set_last_saved_state(self):
        """Record the current model state for change detection."""
        self.last_saved_state = json.dumps(self.export_model_data(), sort_keys=True)

    def has_unsaved_changes(self):
        """Return True if the model differs from the last saved state."""
        current_state = json.dumps(self.export_model_data(), sort_keys=True)
        return current_state != getattr(self, "last_saved_state", None)

    # ------------------------------------------------------------
    # ------------------------------------------------------------
    # Undo support
    # ------------------------------------------------------------
    def push_undo_state(self, strategy: str = "v4", sync_repo: bool = True) -> None:
        self.undo_manager.push_undo_state(strategy=strategy, sync_repo=sync_repo)

    def _push_undo_state_v1(self, state: dict, stripped: dict) -> bool:
        return self.undo_manager._push_undo_state_v1(state, stripped)

    def _push_undo_state_v2(self, state: dict, stripped: dict) -> bool:
        return self.undo_manager._push_undo_state_v2(state, stripped)

    def _push_undo_state_v3(self, state: dict, stripped: dict) -> bool:
        return self.undo_manager._push_undo_state_v3(state, stripped)

    def _push_undo_state_v4(self, state: dict, stripped: dict) -> bool:
        return self.undo_manager._push_undo_state_v4(state, stripped)

    def _undo_hotkey(self, event):
        """Keyboard shortcut handler for undo."""
        self.undo_manager.undo()
        return "break"

    def _redo_hotkey(self, event):
        """Keyboard shortcut handler for redo."""
        self.undo_manager.redo()
        return "break"

    def undo(self, strategy: str = "v4"):
        self.undo_manager.undo(strategy=strategy)

    def redo(self, strategy: str = "v4"):
        self.undo_manager.redo(strategy=strategy)

    def clear_undo_history(self) -> None:
        """Remove all undo and redo history."""
        self.undo_manager.clear_history()
    def confirm_close(self):
        """Prompt to save if there are unsaved changes before closing."""
        if self.has_unsaved_changes():
            result = messagebox.askyesnocancel("Unsaved Changes", "Save changes before exiting?")
            if result is None:
                return
            if result:
                self.save_model()
        # Previously, any loaded model paths were deleted on close, which could
        # remove user data. Avoid deleting files that were explicitly opened by
        # the user so their project files remain intact.
        # Ensure the Tk event loop terminates and all windows are destroyed
        self.root.quit()
        self.root.destroy()


    def export_model_data(self, include_versions=True):
        return self.reporting_export.export_model_data(include_versions)

    def _load_project_properties(self, data: dict) -> None:
        """Delegate project property loading to the manager."""
        self.project_properties = self.project_properties_manager.load_project_properties(
            data
        )

    def _load_fault_tree_events(self, data: dict, ensure_root: bool) -> None:
        return self.safety_analysis._load_fault_tree_events(data, ensure_root)
          
    def apply_model_data(self, data: dict, ensure_root: bool = True):
        return self.project_manager.apply_model_data(data, ensure_root)

    def _reset_on_load(self):
        """Close all open windows and clear state before loading a project."""

        if getattr(self, "page_diagram", None) is not None:
            self.close_page_diagram()

        for tab_id in list(getattr(self.doc_nb, "tabs", lambda: [])()):
            self.doc_nb._closing_tab = tab_id
            self.doc_nb.event_generate("<<NotebookTabClosed>>")
            if tab_id in getattr(self.doc_nb, "tabs", lambda: [])():
                try:
                    self.doc_nb.forget(tab_id)
                except Exception:
                    pass

        for win in (
            list(getattr(self, "use_case_windows", []))
            + list(getattr(self, "activity_windows", []))
            + list(getattr(self, "block_windows", []))
            + list(getattr(self, "ibd_windows", []))
        ):
            try:
                win.destroy()
            except Exception:
                pass
        self.use_case_windows = []
        self.activity_windows = []
        self.block_windows = []
        self.ibd_windows = []

        global AutoML_Helper, unique_node_id_counter
        SysMLRepository.reset_instance()
        AutoML_Helper = config_utils.AutoML_Helper = AutoMLHelper()
        unique_node_id_counter = config_utils.unique_node_id_counter = 1

        self.top_events = []
        self.cta_events = []
        self.root_node = None
        self.selected_node = None
        self.page_history = []
        self.undo_manager.clear_history()
        if getattr(self, "analysis_tree", None):
            self.analysis_tree.delete(*self.analysis_tree.get_children())

        self._reset_fta_state()

    def _prompt_save_before_load_v1(self):
        return messagebox.askyesnocancel(
            "Load Model", "Save current project before loading?"
        )

    def _prompt_save_before_load_v2(self):
        return messagebox.askyesnocancel(
            "Load Model", "Would you like to save before loading a new project?"
        )

    def _prompt_save_before_load_v3(self):
        message = "You have unsaved changes. Save before loading a project?"
        return messagebox.askyesnocancel("Load Model", message)

    def _prompt_save_before_load_v4(self):
        opts = {
            "title": "Load Model",
            "message": "Save changes before loading another project?",
        }
        return messagebox.askyesnocancel(**opts)

    def _prompt_save_before_load(self):
        return self._prompt_save_before_load_v3()


    def update_global_requirements_from_nodes(self,node):
        if hasattr(node, "safety_requirements"):
            for req in node.safety_requirements:
                # Use req["id"] as key; if already exists, you could update if needed.
                ensure_requirement_defaults(req)
                if req["id"] not in global_requirements:
                    global_requirements[req["id"]] = req
                else:
                    ensure_requirement_defaults(global_requirements[req["id"]])
        for child in node.children:
            self.update_global_requirements_from_nodes(child)

    def _generate_pdf_report(self):
        return self.reporting_export._generate_pdf_report()

    def generate_pdf_report(self):
        return self.reporting_export.generate_pdf_report()

    def generate_report(self):
        return self.reporting_export.generate_report()

    def build_html_report(self):
        return self.reporting_export.build_html_report()
    def resolve_original(self, node):
        return resolve_node_original(node)

    def go_back(self):
        return self.nav_input.go_back()

    def draw_page_subtree(self, page_root):
        return self.diagram_renderer.draw_page_subtree(page_root)

    def draw_page_grid(self):
        return self.diagram_renderer.draw_page_grid()

    def draw_page_connections_subtree(self, node, visited_ids):
        return self.diagram_renderer.draw_page_connections_subtree(node, visited_ids)

    def draw_page_nodes_subtree(self, node):
        return self.diagram_renderer.draw_page_nodes_subtree(node)

    def draw_node_on_page_canvas(self, *args, **kwargs):
        return self.diagram_renderer.draw_node_on_page_canvas(*args, **kwargs)

    def on_ctrl_mousewheel_page(self, event):
        return self.nav_input.on_ctrl_mousewheel_page(event)

    def close_page_diagram(self):
        return self.diagram_renderer.close_page_diagram()

    # --- Review Toolbox Methods ---
    def start_peer_review(self):
        return self.versioning_review.start_peer_review()

    def start_joint_review(self):
        return self.versioning_review.start_joint_review()

    def open_review_document(self, review):
        return self.versioning_review.open_review_document(review)

    def open_review_toolbox(self):
        return self.versioning_review.open_review_toolbox()

    def send_review_email(self, review):
        return self.versioning_review.send_review_email(review)

    def review_is_closed(self):
        return self.versioning_review.review_is_closed()

    def review_is_closed_for(self, review):
        return self.versioning_review.review_is_closed_for(review)

    def capture_diff_diagram(self, top_event):  # pragma: no cover - delegation
        return self.diagram_renderer.capture_diff_diagram(top_event)

    # --- End Review Toolbox Methods ---

    def compute_requirement_asil(self, req_id):
        return self.requirements_manager.compute_requirement_asil(req_id)

    def find_safety_goal_node(self, name):
        for te in self.top_events:
            if name in (te.safety_goal_description, te.user_name):
                return te
        return None

    def compute_validation_criteria(self, req_id):  # pragma: no cover - delegation
        return self.validation_consistency.compute_validation_criteria(req_id)

    def update_validation_criteria(self, req_id):  # pragma: no cover - delegation
        return self.validation_consistency.update_validation_criteria(req_id)

    def update_requirement_asil(self, req_id):
        req = global_requirements.get(req_id)
        if not req:
            return
        req["asil"] = self.compute_requirement_asil(req_id)

    def update_all_validation_criteria(self):  # pragma: no cover - delegation
        return self.validation_consistency.update_all_validation_criteria()

    def update_all_requirement_asil(self):
        for rid, req in global_requirements.items():
            if req.get("parent_id"):
                continue  # keep decomposition ASIL
            self.update_requirement_asil(rid)

    def update_base_event_requirement_asil(self):
        return self.safety_analysis.update_base_event_requirement_asil()

    def ensure_asil_consistency(self):
        """Sync safety goal ASILs from risk assessments and update requirement ASILs."""
        self.update_fta_statuses()
        self.sync_hara_to_safety_goals()
        self.update_hazard_list()
        self.update_all_requirement_asil()
        self.validation_consistency.update_all_validation_criteria()

    def invalidate_reviews_for_hara(self, name):
        return self.versioning_review.invalidate_reviews_for_hara(name)

    def invalidate_reviews_for_requirement(self, req_id):
        return self.versioning_review.invalidate_reviews_for_requirement(req_id)

    def add_version(self):
        return self.versioning_review.add_version()


    def compare_versions(self):
        return self.versioning_review.compare_versions()


    def merge_review_comments(self):
        return self.versioning_review.merge_review_comments()


    def calculate_diff_nodes(self, old_data):
        return self.review_manager.calculate_diff_nodes(old_data)


    def calculate_diff_between(self, data1, data2):
        return self.review_manager.calculate_diff_between(data1, data2)


    def node_map_from_data(self, top_events):
        return self.structure_tree_operations.node_map_from_data(top_events)


    def set_current_user(self):
        self.user_manager.set_current_user()

    def get_current_user_role(self):
        return self.data_access_queries.get_current_user_role()

    def focus_on_node(self, node):
        return self.nav_input.focus_on_node(node)

    def get_review_targets(self):
        return self.versioning_review.get_review_targets()


def load_user_data() -> tuple[dict, tuple[str, str]]:
    """Load cached users and last user config concurrently."""
    with ThreadPoolExecutor() as executor:
        users_future = executor.submit(load_all_users)
        config_future = executor.submit(load_user_config)
        return users_future.result(), config_future.result()


def _launch_app() -> None:
    root = tk.Tk()
    root.minsize(1200, 700)
    enable_listbox_hover_highlight(root)
    root.withdraw()
    users, (last_name, last_email) = load_user_data()
    if users:
        dlg = UserSelectDialog(root, users, last_name)
        if dlg.result:
            name, email = dlg.result
            if name == "New User...":
                info = UserInfoDialog(root, "", "").result
                if info:
                    name, email = info
                    save_user_config(name, email)
            else:
                email = users.get(name, email)
                set_last_user(name)
    else:
        dlg = UserInfoDialog(root, last_name, last_email)
        if dlg.result:
            name, email = dlg.result
            save_user_config(name, email)
    set_current_user(name, email)
    global AutoML_Helper
    AutoML_Helper = config_utils.AutoML_Helper = AutoMLHelper()
    root.deiconify()
    try:
        root.state("zoomed")
    except tk.TclError:
        try:
            root.attributes("-zoomed", True)
        except tk.TclError:
            pass
    app = AutoMLApp(root)
    root.mainloop()


def _watchdog_feeder(wd, stop_event, interval: float = 1.0) -> None:
    while not stop_event.is_set():
        time.sleep(interval)
        try:
            wd.feed()
        except Exception:
            break


def main() -> None:
    install_best()
    wd = watchdog_best(10.0)
    stop_event = threading.Event()
    thread_manager.register("watchdog", _watchdog_feeder, args=(wd, stop_event))
    try:
        _launch_app()
    finally:
        stop_event.set()
        thread_manager.stop_all()

if __name__ == "__main__":
    main()
