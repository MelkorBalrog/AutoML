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

"""Application state initialisation helpers for :class:`AutoMLApp`.

The :class:`AppInitializer` concentrates the large collection of lists,
probability tables and other default state values required by
``AutoMLApp``.  Separating this logic keeps ``AutoMLApp.__init__``
focused on orchestrating high-level services and UI configuration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from analysis.utils import (
    update_probability_tables,
    EXPOSURE_PROBABILITIES,
    CONTROLLABILITY_PROBABILITIES,
    SEVERITY_PROBABILITIES,
)
from gui.toolboxes.safety_management_toolbox import SafetyManagementToolbox
from mainappsrc.managers.governance_manager import GovernanceManager
from mainappsrc.managers.product_goal_manager import ProductGoalManager
from mainappsrc.managers.gsn_manager import GSNManager
from mainappsrc.core.structure_tree_operations import Structure_Tree_Operations
from gui.utils.drawing_helper import fta_drawing_helper
from mainappsrc.managers.project_properties_manager import ProjectPropertiesManager
from mainappsrc.managers.diagram_clipboard_manager import DiagramClipboardManager

if TYPE_CHECKING:  # pragma: no cover - for type checkers only
    from .automl_core import AutoMLApp


class AppInitializer:
    """Populate default attributes for :class:`AutoMLApp`."""

    def __init__(self, app: "AutoMLApp") -> None:
        self.app = app

    # NOTE: The cyclomatic complexity of this method is low as it consists of
    # sequential assignments.  Keeping it simple aids ISO 26262 arguments.
    def initialize(self) -> None:
        """Initialise application state on the provided ``app`` instance."""

        app = self.app

        # Basic caches and state containers
        app.top_events = []
        app.cta_events = []
        app.paa_events = []
        app.fta_root_node = None
        app.cta_root_node = None
        app.paa_root_node = None
        app.analysis_tabs = {}
        app.shared_product_goals = {}
        app.product_goal_manager = ProductGoalManager()
        app.selected_node = None
        app.clone_offset_counter = {}
        app._loaded_model_paths = []

        app.clipboard_node = None
        app.diagram_clipboard = DiagramClipboardManager(app)
        app.active_arch_window = None
        app.cut_mode = False
        app.page_history = []
        app.project_properties = {
            "pdf_report_name": "AutoML-Analyzer PDF Report",
            "pdf_detailed_formulas": True,
            "exposure_probabilities": EXPOSURE_PROBABILITIES.copy(),
            "controllability_probabilities": CONTROLLABILITY_PROBABILITIES.copy(),
            "severity_probabilities": SEVERITY_PROBABILITIES.copy(),
        }
        update_probability_tables(
            app.project_properties["exposure_probabilities"],
            app.project_properties["controllability_probabilities"],
            app.project_properties["severity_probabilities"],
        )
        app.project_properties_manager = ProjectPropertiesManager(app.project_properties)
        app.item_definition = {"description": "", "assumptions": ""}
        app.safety_concept = {
            "functional": "",
            "technical": "",
            "cybersecurity": "",
        }
        app.mission_profiles = []
        app.fmeda_components = []
        app.reliability_analyses = []
        app.reliability_components = []
        app.reliability_total_fit = 0.0
        app.spfm = 0.0
        app.lpfm = 0.0
        app.reliability_dc = 0.0

        # Lists of user-defined entities
        app.faults = []
        app.malfunctions = []
        app.hazards = []
        app.hazard_severity = {}
        app.failures = []
        app.triggering_conditions = []
        app.functional_insufficiencies = []
        app.triggering_condition_nodes = []
        app.functional_insufficiency_nodes = []
        app.hazop_docs = []
        app.hara_docs = []
        app.stpa_docs = []
        app.threat_docs = []
        app.active_hazop = None
        app.active_hara = None
        app.active_stpa = None
        app.active_threat = None
        app.hazop_entries = []
        app.hara_entries = []
        app.stpa_entries = []
        app.threat_entries = []
        app.fi2tc_docs = []
        app.tc2fi_docs = []
        app.active_fi2tc = None
        app.active_tc2fi = None
        app.cbn_docs = []
        app.active_cbn = None
        app.cybersecurity_goals = []
        app.arch_diagrams = []
        app.management_diagrams = []
        app.gsn_modules = []
        app.gsn_diagrams = []
        app.gsn_manager = GSNManager(app)
        app.diagram_tabs = {}
        app.reviews = []
        app.review_data = None
        app.review_window = None
        app.governance_manager = GovernanceManager(app)
        app.safety_mgmt_toolbox = SafetyManagementToolbox()
        app.governance_manager.attach_toolbox(app.safety_mgmt_toolbox)
        if not hasattr(app, "probability_reliability"):
            app.probability_reliability = None
        app.current_user = ""
        app.comment_target = None
        app._undo_stack = []
        app._redo_stack = []
        app.enabled_work_products = set()
        app.work_product_menus = {}
        app.versions = []
        app.diff_nodes = []
        app.fi2tc_entries = []
        app.tc2fi_entries = []
        app.scenario_libraries = []
        app.odd_libraries = []
        app.odd_elements = []
        app.update_odd_elements()
        app.fta_drawing_helper = fta_drawing_helper
        app.structure_tree_operations = Structure_Tree_Operations(app)
        app.mechanism_libraries = []
        app.selected_mechanism_libraries = []
        app.load_default_mechanisms()

        # Managers instantiated here but used elsewhere
        # (currently none; placeholder for future extensions)

__all__ = ["AppInitializer"]
