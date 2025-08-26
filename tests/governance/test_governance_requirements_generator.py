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

import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from analysis.governance import GovernanceDiagram


def test_generate_requirements_from_governance_diagram():
    diagram = GovernanceDiagram()
    diagram.add_task("Data Steward", node_type="Role")
    diagram.add_task("Review Data", node_type="Task")
    diagram.add_task("Report", node_type="Document")
    diagram.add_task("Policy DP-001", node_type="Policy")
    diagram.add_relationship("Data Steward", "Review Data", label="performs")
    diagram.add_relationship("Review Data", "Report", label="produces")
    diagram.add_relationship(
        "Data Steward", "Report", label="approves", condition="data validated"
    )
    diagram.add_relationship("Review Data", "Policy DP-001", label="governed by")

    reqs = diagram.generate_requirements()
    texts = [r.text for r in reqs]

    assert "Data Steward (Role) shall perform 'Review Data (Task)'." in texts
    assert "Review Data (Task) shall produce 'Report (Document)'." in texts
    assert "If data validated, Data Steward (Role) shall approve 'Report (Document)'." in texts
    assert "Review Data (Task) shall comply with 'Policy DP-001 (Policy)'." in texts
    assert "Organization shall review data." in texts

    perf_req = next(r for r in reqs if r.action == "perform")
    assert perf_req.subject == "Data Steward"
    assert perf_req.obj == "Review Data"

    approve_req = next(r for r in reqs if r.action == "approve")
    assert approve_req.condition == "data validated"
    assert approve_req.subject == "Data Steward"
    assert approve_req.obj == "Report"
    review_req = next(r for r in reqs if r.action == "review data")
    assert review_req.subject == "Organization"
    assert review_req.req_type == "organizational"

def test_ai_training_and_curation_requirements():
    diagram = GovernanceDiagram()
    diagram.add_task("Database1", node_type="AI Database")
    diagram.add_task("ANN1", node_type="ANN")
    diagram.add_task("Decision1", node_type="Decision")
    diagram.add_relationship(
        "Database1",
        "ANN1",
        condition="completion >= 0.98",
        conn_type="AI training",
    )
    diagram.add_relationship(
        "Decision1",
        "Database1",
        condition="completion < 0.98",
        conn_type="Curation",
    )
    reqs = diagram.generate_requirements()
    texts = [r.text for r in reqs]
    assert (
        "If completion >= 0.98, Engineering team shall train the ANN1 (ANN) using the Database1 (AI Database)."
        in texts
    )
    assert "If completion < 0.98, Engineering team shall curate 'Database1 (AI Database)'." in texts

    train_req = next(r for r in reqs if r.action == "train")
    assert train_req.subject == "Engineering team"
    assert train_req.obj == "ANN1"
    assert train_req.condition == "completion >= 0.98"

    curate_req = next(r for r in reqs if r.action == "curate")
    assert curate_req.subject == "Engineering team"
    assert curate_req.obj == "Database1"
    assert curate_req.condition == "completion < 0.98"


def test_acquisition_pattern_requirement():
    diagram = GovernanceDiagram()
    diagram.add_task("DB1", node_type="AI Database")
    diagram.add_task("DAQ1", node_type="Data acquisition")
    diagram.add_relationship("DB1", "DAQ1", conn_type="Acquisition")
    reqs = diagram.generate_requirements()
    texts = [r.text for r in reqs]
    assert "Engineering team shall acquire the DAQ1 (Data acquisition) using the DB1 (AI Database)." in texts

def test_propagate_by_review_pattern():
    diagram = GovernanceDiagram()
    diagram.add_task("WP1", node_type="Work Product")
    diagram.add_task("WP2", node_type="Work Product")
    diagram.add_relationship("WP1", "WP2", conn_type="Propagate by Review")
    reqs = diagram.generate_requirements()
    texts = [r.text for r in reqs]
    assert "WP1 (Work Product) shall propagate by review the WP2 (Work Product)." in texts

def test_data_acquisition_compartment_sources():
    diagram = GovernanceDiagram()
    diagram.add_task(
        "Acquire Data",
        node_type="Data acquisition",
        compartments=["Sensor A", "Sensor B"],
    )

    reqs = diagram.generate_requirements()
    texts = [r.text for r in reqs]

    assert "Engineering team shall acquire data from 'Sensor A'." in texts
    assert "Engineering team shall acquire data from 'Sensor B'." in texts

    data_reqs = [r for r in reqs if r.action == "acquire data from"]
    assert all(r.req_type == "AI safety" for r in data_reqs)
    assert all(r.subject == "Engineering team" for r in data_reqs)
    assert {r.obj for r in data_reqs} == {"Sensor A", "Sensor B"}


def test_data_acquisition_node_name_normalized():
    diagram = GovernanceDiagram()
    diagram.add_task(
        "Data acquisition",
        node_type="Data acquisition",
        compartments=["Sensor X"],
    )

    reqs = diagram.generate_requirements()
    texts = [r.text for r in reqs]

    assert "Engineering team shall acquire data from 'Sensor X'." in texts
    # Ensure the raw node name does not appear in generated text
    assert not any("shall Data acquisition" in t for t in texts)


def test_tasks_create_requirement_actions():
    diagram = GovernanceDiagram()
    diagram.add_task("Review Data", node_type="Task")
    diagram.add_task("Acquire Data", node_type="Data acquisition")

    reqs = diagram.generate_requirements()
    texts = [r.text for r in reqs]

    assert "Organization shall review data." in texts
    assert "Engineering team shall acquire data." in texts

    review_req = next(r for r in reqs if r.action == "review data")
    assert review_req.subject == "Organization"
    assert review_req.req_type == "organizational"
    acquire_req = next(r for r in reqs if r.action == "acquire data")
    assert acquire_req.subject == "Engineering team"
    assert acquire_req.req_type == "AI safety"


def test_generic_ai_relation_defaults_to_organizational():
    diagram = GovernanceDiagram()
    diagram.add_task("Policy", node_type="Policy")
    diagram.add_task("Role1", node_type="Role")
    diagram.add_relationship("Role1", "Policy", conn_type="Assesses")

    reqs = diagram.generate_requirements()
    assess_req = next(r for r in reqs if r.action == "assess" and r.subject == "Role1")
    assert assess_req.req_type == "organizational"


def test_complies_with_between_work_products():
    diagram = GovernanceDiagram()
    diagram.add_task("Requirement Specification", node_type="Work Product")
    diagram.add_task("Operational Requirement", node_type="Work Product")
    diagram.add_relationship(
        "Requirement Specification", "Operational Requirement", conn_type="Complies with"
    )

    reqs = diagram.generate_requirements()
    comp_req = next(r for r in reqs if r.action == "comply with")
    assert comp_req.subject == "Requirement Specification"
    assert comp_req.obj == "Operational Requirement"
    assert comp_req.req_type == "organizational"


def test_constrained_by_between_work_products():
    diagram = GovernanceDiagram()
    diagram.add_task("Requirement Specification", node_type="Work Product")
    diagram.add_task("Operational Requirement", node_type="Work Product")
    diagram.add_relationship(
        "Requirement Specification", "Operational Requirement", conn_type="Constrained by"
    )

    reqs = diagram.generate_requirements()
    comp_req = next(r for r in reqs if r.action == "comply with")
    assert comp_req.subject == "Requirement Specification"
    assert comp_req.constraint == "Operational Requirement"
    assert comp_req.req_type == "organizational"
