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

import types
import sys

# Provide dummy PIL modules so AutoML can be imported without Pillow
sys.modules.setdefault("PIL", types.ModuleType("PIL"))
sys.modules.setdefault("PIL.Image", types.ModuleType("PIL.Image"))
sys.modules.setdefault("PIL.ImageDraw", types.ModuleType("PIL.ImageDraw"))
sys.modules.setdefault("PIL.ImageFont", types.ModuleType("PIL.ImageFont"))
sys.modules.setdefault("PIL.ImageTk", types.ModuleType("PIL.ImageTk"))

import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from AutoML import AutoMLApp
from mainappsrc.models.gsn import GSNNode, GSNDiagram, GSNModule


def _minimal_app():
    app = AutoMLApp.__new__(AutoMLApp)
    app.top_events = []
    app.root_node = None
    app.fmea_entries = []
    app.fmeas = []
    app.fmedas = []
    app.mechanism_libraries = []
    app.selected_mechanism_libraries = []
    app.mission_profiles = []
    app.reliability_analyses = []
    app.hazop_docs = []
    app.hara_docs = []
    app.stpa_docs = []
    app.threat_docs = []
    app.fi2tc_docs = []
    app.tc2fi_docs = []
    app.hazop_entries = []
    app.fi2tc_entries = []
    app.tc2fi_entries = []
    app.scenario_libraries = []
    app.odd_libraries = []
    app.faults = []
    app.malfunctions = []
    app.hazards = []
    app.failures = []
    app.project_properties = {}
    app.reviews = []
    app.review_data = types.SimpleNamespace(name=None)
    app.update_odd_elements = lambda: None
    app.update_failure_list = lambda: None
    app.load_default_mechanisms = lambda: None
    app.update_hazard_list = lambda: None
    app.update_hara_statuses = lambda: None
    app.update_fta_statuses = lambda: None
    app.get_all_basic_events = lambda: []
    app.get_all_nodes = lambda te: []
    app.get_all_fmea_entries = lambda: []
    app.update_global_requirements_from_nodes = lambda *args, **kwargs: None
    app.sync_hara_to_safety_goals = lambda: None
    app.close_page_diagram = lambda: None
    app.update_views = lambda: None
    return app


def test_gsn_roundtrip_serialisation():
    # build a simple module/diagram structure
    root1 = GSNNode("G1", "Goal")
    strat = GSNNode("S1", "Strategy")
    root1.add_child(strat)
    diag1 = GSNDiagram(root1)
    diag1.add_node(strat)
    mod = GSNModule("Pkg", diagrams=[diag1])

    root2 = GSNNode("G2", "Goal")
    diag2 = GSNDiagram(root2)

    app = _minimal_app()
    app.gsn_modules = [mod]
    app.gsn_diagrams = [diag2]

    data = app.export_model_data(include_versions=False)

    new_app = _minimal_app()
    new_app.apply_model_data(data, ensure_root=False)

    assert len(new_app.gsn_modules) == 1
    loaded_mod = new_app.gsn_modules[0]
    assert loaded_mod.name == "Pkg"
    assert len(loaded_mod.diagrams) == 1
    assert loaded_mod.diagrams[0].root.user_name == "G1"
    assert loaded_mod.diagrams[0].root.children[0].node_type == "Strategy"
    assert len(new_app.gsn_diagrams) == 1
    assert new_app.gsn_diagrams[0].root.user_name == "G2"
