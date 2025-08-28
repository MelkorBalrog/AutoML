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

"""Analysis utilities for AutoML."""

from .sotif_validation import acceptance_rate, hazardous_behavior_rate, validation_time
from .confusion_matrix import compute_metrics, compute_metrics_from_target
from .causal_bayesian_network import CausalBayesianNetwork, CausalBayesianNetworkDoc

__all__ = [
    "acceptance_rate",
    "hazardous_behavior_rate",
    "validation_time",
    "compute_metrics",
    "CausalBayesianNetwork",
    "CausalBayesianNetworkDoc",
]


def __getattr__(name):
    if name == "SafetyManagementToolbox":
        from .safety_management import SafetyManagementToolbox as _SMT

        return _SMT
    if name in {"SafetyCase", "SafetyCaseLibrary"}:
        from .safety_case import SafetyCase, SafetyCaseLibrary

        return {"SafetyCase": SafetyCase, "SafetyCaseLibrary": SafetyCaseLibrary}[name]
    raise AttributeError(name)
