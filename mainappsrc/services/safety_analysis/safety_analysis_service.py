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

"""Service facade for safety analysis helpers."""

from __future__ import annotations
import tkinter as tk
from tkinter import font as tkFont
from typing import Iterable

from analysis import utils as analysis_utils
from analysis.utils import (
    FMEAService as _FMEAServiceImpl,
    SafetyAnalysis_FTA_FMEA as _SafetyAnalysisImpl,
)
from mainappsrc.models.fta.fault_tree_node import FaultTreeNode


class FMEAService:
    """Thin wrapper around :class:`analysis.utils.FMEAService`."""

    def __init__(self, app: tk.Misc) -> None:
        self._impl = _FMEAServiceImpl(app)

    def __getattr__(self, name: str):
        return getattr(self._impl, name)

class SafetyAnalysis_FTA_FMEA:
    """Thin wrapper around :class:`analysis.utils.SafetyAnalysis_FTA_FMEA`."""

    def __init__(self, app: tk.Misc) -> None:
        self._impl = _SafetyAnalysisImpl(app)

    def __getattr__(self, name: str):
        return getattr(self._impl, name)


class SafetyAnalysisService:
    """Wrap :class:`SafetyAnalysis_FTA_FMEA` and expose utility helpers."""

    def __init__(self, app: object) -> None:
        self.app = app
        self._impl = SafetyAnalysis_FTA_FMEA(app)

    def __getattr__(self, name: str):
        return getattr(self._impl, name)

    # ------------------------------------------------------------------
    # FMEDA metric helpers
    def compute_fmeda_metrics(self, events: Iterable[FaultTreeNode]):
        """Compute FMEDA metrics for ``events``."""

        return analysis_utils.compute_fmeda_metrics(
            events,
            getattr(self.app, "reliability_components", []),
            self.get_safety_goal_asil,
        )

    # ------------------------------------------------------------------
    # Probability and reliability helpers moved from probability_reliability.py

    def update_probability_tables(
        self,
        exposure: dict | None,
        controllability: dict | None,
        severity: dict | None,
    ) -> None:
        """Delegate probability table updates to shared utility."""

        analysis_utils.update_probability_tables(
            exposure, controllability, severity
        )

    # ------------------------------------------------------------------
    def compute_failure_prob(self, node, failure_mode_ref=None, formula=None):
        """Return probability of failure for ``node`` based on FIT rate."""

        return analysis_utils.compute_failure_prob(
            self.app, node, failure_mode_ref, formula
        )

    # ------------------------------------------------------------------
    def update_basic_event_probabilities(self):
        """Update failure probabilities for all basic events."""

        analysis_utils.update_basic_event_probabilities(self.app)

    # ------------------------------------------------------------------
    def calculate_pmfh(self):
        """Calculate probabilistic metric for hardware failures."""

        analysis_utils.calculate_pmfh(self.app)

    # ------------------------------------------------------------------
    def calculate_overall(self):
        """Calculate overall assurance levels for top events."""

        analysis_utils.calculate_overall(self.app)

    # ------------------------------------------------------------------
    def _build_probability_frame(
        self,
        parent,
        title: str,
        levels: range,
        values: dict,
        row: int,
        dialog_font: tkFont.Font,
    ) -> dict:
        """Create a labelled frame of probability entries."""

        return analysis_utils.build_probability_frame(
            self.app, parent, title, levels, values, row, dialog_font
        )

    # ------------------------------------------------------------------
    def assurance_level_text(self, level):
        return analysis_utils.assurance_level_text(self.app, level)

    # ------------------------------------------------------------------
    def metric_to_text(self, metric_type, value):
        return analysis_utils.metric_to_text(self.app, metric_type, value)

    # ------------------------------------------------------------------
    def analyze_common_causes(self, node):
        return analysis_utils.analyze_common_causes(self.app, node)

    # ------------------------------------------------------------------
    def build_cause_effect_data(self):
        """Collect cause and effect chain information."""

        return analysis_utils.build_cause_effect_data(self.app)

    # ------------------------------------------------------------------
    def _build_cause_effect_graph(self, row):
        """Return nodes, edges and positions for a cause-and-effect diagram."""

        return analysis_utils.build_cause_effect_graph(row)

    # ------------------------------------------------------------------
    def render_cause_effect_diagram(self, row):
        """Render *row* as a PIL image matching the on-screen diagram."""

        return analysis_utils.render_cause_effect_diagram(row)

    # ------------------------------------------------------------------
    def sync_cyber_risk_to_goals(self):
        return analysis_utils.sync_cyber_risk_to_goals(self.app)


__all__ = ["SafetyAnalysisService", "FMEAService", "SafetyAnalysis_FTA_FMEA"]

