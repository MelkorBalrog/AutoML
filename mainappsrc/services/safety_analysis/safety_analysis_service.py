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

from typing import Iterable

from mainappsrc.core.safety_analysis import SafetyAnalysis_FTA_FMEA
from mainappsrc.models.fta.fault_tree_node import FaultTreeNode
from analysis.fmeda_utils import compute_fmeda_metrics as _compute_fmeda_metrics


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
        """Compute FMEDA metrics for ``events``.

        Parameters
        ----------
        events:
            Iterable of :class:`FaultTreeNode` instances representing
            failure modes to analyse.
        """
        return _compute_fmeda_metrics(
            list(events),
            getattr(self.app, "reliability_components", []),
            self.get_safety_goal_asil,
        )


__all__ = ["SafetyAnalysisService"]
