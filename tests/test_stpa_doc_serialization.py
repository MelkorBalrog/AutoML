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

from types import SimpleNamespace
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from analysis.models import StpaDoc, StpaEntry
from mainappsrc.core.reporting_export import Reporting_Export


def test_export_model_data_serializes_stpa_docs(monkeypatch):
    """STPA documents should be included in model export output."""

    doc = StpaDoc("S1", "", [StpaEntry("", "", "", "", "", [])])
    app = SimpleNamespace(
        update_odd_elements=lambda: None,
        review_manager=SimpleNamespace(reviews=[]),
        review_data=None,
        top_events=[],
        cta_events=[],
        paa_events=[],
        fmeas=[],
        fmedas=[],
        mechanism_libraries=[],
        selected_mechanism_libraries=[],
        mission_profiles=[],
        reliability_analyses=[],
        reliability_components=[],
        reliability_total_fit=0.0,
        spfm=0.0,
        lpfm=0.0,
        reliability_dc=0.0,
        item_definition="",
        safety_concept="",
        fmeda_components=[],
        current_user="",
        hazop_docs=[],
        hara_docs=[],
        stpa_docs=[doc],
        threat_docs=[],
        fi2tc_docs=[],
        tc2fi_docs=[],
        project_properties={},
        scenario_libraries=[],
        odd_libraries=[],
        odd_elements=[],
        versions=[],
        fmea_service=SimpleNamespace(get_settings_dict=lambda: {}),
        requirements_manager=SimpleNamespace(export_state=lambda: {}),
        arch_diagrams=[],
        management_diagrams=[],
        gsn_modules=[],
        gsn_diagrams=[],
        safety_mgmt_toolbox=SimpleNamespace(to_dict=lambda: {}),
        enabled_work_products=[],
    )
    monkeypatch.setattr(
        "mainappsrc.core.reporting_export.SysMLRepository.get_instance",
        lambda: None,
    )
    data = Reporting_Export(app).export_model_data()
    assert data["stpa_docs"] == [doc.to_dict()]
