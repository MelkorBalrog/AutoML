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
"""Verify governance folder structure persists through save/load."""

import importlib.util
import os
import sys
import types

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

spec = importlib.util.spec_from_file_location(
    "analysis.safety_management",
    os.path.join(os.path.dirname(__file__), "..", "..", "analysis", "safety_management.py"),
)
safety_management = importlib.util.module_from_spec(spec)
spec.loader.exec_module(safety_management)
SafetyManagementToolbox = safety_management.SafetyManagementToolbox
GovernanceModule = safety_management.GovernanceModule

from mainappsrc.core.reporting_export import Reporting_Export
from mainappsrc.managers.project_manager import ProjectManager
from mainappsrc.models.sysml.sysml_repository import SysMLRepository


class _MinimalApp:
    """Minimal application stub for export/import tests."""

    def __init__(self):
        self.update_odd_elements = lambda: None
        self.top_events = []
        self.cta_events = []
        self.paa_events = []
        self.fmeas = []
        self.fmedas = []
        self.mechanism_libraries = []
        self.mission_profiles = []
        self.reliability_analyses = []
        self.reliability_components = []
        self.reliability_total_fit = 0
        self.spfm = 0
        self.lpfm = 0
        self.reliability_dc = 0
        self.item_definition = {}
        self.safety_concept = {}
        self.fmeda_components = []
        self.current_user = None
        self.hazop_docs = []
        self.hara_docs = []
        self.stpa_docs = []
        self.threat_docs = []
        self.fi2tc_docs = []
        self.tc2fi_docs = []
        self.review_data = types.SimpleNamespace(name=None)
        self.reviews = []
        self.project_properties = {}
        self.selected_mechanism_libraries = []
        self.scenario_libraries = []
        self.odd_libraries = []
        self.odd_elements = []
        self.versions = []
        self.fmea_service = types.SimpleNamespace(get_settings_dict=lambda: {})
        self.requirements_manager = types.SimpleNamespace(export_state=lambda: {})
        self.arch_diagrams = []
        self.management_diagrams = []
        self.gsn_modules = []
        self.gsn_diagrams = []
        self.safety_mgmt_toolbox = SafetyManagementToolbox()
        self.enabled_work_products = set()
        self.project_manager = ProjectManager.__new__(ProjectManager)
        self.project_manager.app = self
        self.reporting_export = Reporting_Export(self)
        # Needed by ProjectManager.apply_model_data
        self.governance_manager = types.SimpleNamespace(
            attach_toolbox=lambda tb: None,
            set_active_module=lambda name: None,
        )
        self._refresh_phase_requirements_menu = lambda: None
        self.validation_consistency = types.SimpleNamespace(
            enable_work_product=lambda name, refresh=True: self.enabled_work_products.add(name),
            disable_work_product=lambda name: self.enabled_work_products.discard(name),
        )
        self._load_project_properties = lambda data: None
        self._load_fault_tree_events = lambda data, ensure_root: None

    def enable_work_product(self, name, *, refresh=True):
        self.enabled_work_products.add(name)


def test_folder_structure_roundtrip():
    """Saving and loading a project preserves governance folders."""
    app = _MinimalApp()
    tb = app.safety_mgmt_toolbox
    tb.create_diagram("Gov")
    tb.modules = [GovernanceModule("Phase", diagrams=["Gov"])]

    SysMLRepository._instance = types.SimpleNamespace(export_state=lambda: {})

    data = app.reporting_export.export_model_data(include_versions=False)
    assert data["safety_mgmt_toolbox"]["modules"][0]["name"] == "Phase"

    loaded = SafetyManagementToolbox.from_dict(data["safety_mgmt_toolbox"])
    assert loaded.modules[0].name == "Phase"
    assert loaded.modules[0].diagrams == ["Gov"]
