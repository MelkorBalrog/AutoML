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
from analysis import CausalBayesianNetwork


def build_network():
    cbn = CausalBayesianNetwork()
    cbn.add_node("Rain", cpd=0.3)
    cbn.add_node(
        "WetGround",
        parents=["Rain"],
        cpd={(True,): 0.9, (False,): 0.1},
    )
    cbn.add_node(
        "SlipperyRoad",
        parents=["WetGround"],
        cpd={(True,): 0.8, (False,): 0.05},
    )
    return cbn


def test_slippery_road_probability():
    cbn = build_network()
    assert cbn.query("SlipperyRoad") == pytest.approx(0.305, rel=1e-3)


def test_slippery_road_given_rain():
    cbn = build_network()
    p = cbn.query("SlipperyRoad", {"Rain": True})
    assert p == pytest.approx(0.725, rel=1e-3)


def test_intervention_matches_conditioning_for_root():
    cbn = build_network()
    p_do = cbn.intervention("SlipperyRoad", {"Rain": True})
    p_cond = cbn.query("SlipperyRoad", {"Rain": True})
    assert p_do == pytest.approx(p_cond, rel=1e-6)


def test_missing_cpd_defaults_to_uniform_probability():
    cbn = CausalBayesianNetwork()
    cbn.add_node("Rain", cpd=0.5)
    cbn.add_node("WetGround", parents=["Rain"], cpd={(True,): 0.9})
    assert cbn.query("WetGround") == pytest.approx(0.7, rel=1e-3)


def test_truth_table_auto_fill():
    cbn = CausalBayesianNetwork()
    cbn.add_node("A", cpd=0.4)
    cbn.add_node("B", parents=["A"], cpd={(True,): 0.7})
    rows = cbn.cpd_rows("B")
    assert len(rows) == 2
    assert rows[0][0] == (False,)
    assert rows[0][1] == pytest.approx(0.5)
    # probability of parent combination P(A=False) = 0.6
    assert rows[0][2] == pytest.approx(0.6, rel=1e-3)
    assert rows[1][2] == pytest.approx(0.4, rel=1e-3)
    # total probability for row A=True is 0.4 * 0.7
    assert rows[1][3] == pytest.approx(0.28, rel=1e-3)

def test_marginal_probability_propagation():
    cbn = CausalBayesianNetwork()
    cbn.add_node("Rain", cpd=0.3)
    cbn.add_node("WetGround", parents=["Rain"], cpd={(True,): 0.9, (False,): 0.1})
    cbn.add_node(
        "SlipperyRoad",
        parents=["WetGround"],
        cpd={(True,): 0.8, (False,): 0.05},
    )
    probs = cbn.marginal_probabilities()
    assert probs["Rain"] == pytest.approx(0.3, rel=1e-3)
    assert probs["WetGround"] == pytest.approx(0.34, rel=1e-3)
    assert probs["SlipperyRoad"] == pytest.approx(0.305, rel=1e-3)
    cbn.cpds["Rain"] = 0.6
    probs = cbn.marginal_probabilities()
    assert probs["WetGround"] == pytest.approx(0.58, rel=1e-3)
    assert probs["SlipperyRoad"] == pytest.approx(0.485, rel=1e-3)


def test_cpd_rows_respect_parent_dependencies():
    cbn = CausalBayesianNetwork()
    cbn.add_node("A", cpd=0.5)
    cbn.add_node("B", parents=["A"], cpd={(True,): 0.9, (False,): 0.1})
    # Conditional probabilities of C are irrelevant; set all to 1 so joint column
    # mirrors P(A,B) directly.
    all_true = {
        (False, False): 1.0,
        (False, True): 1.0,
        (True, False): 1.0,
        (True, True): 1.0,
    }
    cbn.add_node("C", parents=["A", "B"], cpd=all_true)

    rows = cbn.cpd_rows("C")
    # Expected joint distribution of (A, B) taking into account the dependency
    # of B on A.
    expected = [0.45, 0.05, 0.05, 0.45]
    for row, exp in zip(rows, expected):
        assert row[2] == pytest.approx(exp, rel=1e-3)
