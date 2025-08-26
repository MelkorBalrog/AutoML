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
"""Facade combining analysis utilities and probability calculations."""

from __future__ import annotations

from gui.utils.analysis_utils import AnalysisUtilsMixin
from ...core.probability_reliability import Probability_Reliability


class AnalysisUtilsService(AnalysisUtilsMixin):
    """Wrap :class:`AnalysisUtilsMixin` and :class:`Probability_Reliability`."""

    def __init__(self, app: object) -> None:
        self.app = app
        self.probability_reliability = Probability_Reliability(app)

    # ------------------------------------------------------------------
    # Convenience delegations to probability/reliability helpers
    def update_probability_tables(self, exposure=None, controllability=None, severity=None) -> None:
        """Update probability tables using shared helper."""
        self.probability_reliability.update_probability_tables(
            exposure, controllability, severity
        )

    def compute_failure_prob(self, *args, **kwargs):
        """Delegate failure probability computation."""
        return self.probability_reliability.compute_failure_prob(*args, **kwargs)

    def calculate_pmfh(self):
        """Delegate PMFH calculation."""
        return self.probability_reliability.calculate_pmfh()

    def calculate_overall(self):
        """Delegate overall metric calculation."""
        return self.probability_reliability.calculate_overall()

    def metric_to_text(self, metric_type, value):
        return self.probability_reliability.metric_to_text(metric_type, value)

    def assurance_level_text(self, level):
        return self.probability_reliability.assurance_level_text(level)

    def analyze_common_causes(self, node):
        return self.probability_reliability.analyze_common_causes(node)

    def sync_cyber_risk_to_goals(self):
        return self.probability_reliability.sync_cyber_risk_to_goals()

    def build_cause_effect_data(self):
        return self.probability_reliability.build_cause_effect_data()

    def build_cause_effect_graph(self, row):
        return self.probability_reliability._build_cause_effect_graph(row)

    def render_cause_effect_diagram(self, row):
        return self.probability_reliability.render_cause_effect_diagram(row)


__all__ = ["AnalysisUtilsService"]
