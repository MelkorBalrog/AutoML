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

"""Expose AutoML application classes at the package root."""

import tkinter as tk
from tkinter import ttk, simpledialog, filedialog, scrolledtext

try:  # pragma: no cover - optional heavy dependencies
    from .mainappsrc.core.automl_core import (
        AutoMLApp,
        FaultTreeNode,
        AutoML_Helper,
        messagebox,
        GATE_NODE_TYPES,
    )
    from .mainappsrc.safety_analysis import SafetyAnalysis_FTA_FMEA
    if __package__ and __package__.startswith("AutoML"):
        from AutoML.config.automl_constants import PMHF_TARGETS
    else:
        from config.automl_constants import PMHF_TARGETS
    from analysis.models import HazopDoc
    from gui.dialogs.edit_node_dialog import EditNodeDialog
    from analysis.risk_assessment import AutoMLHelper
except Exception:  # pragma: no cover - allow importing package without extras
    AutoMLApp = FaultTreeNode = AutoML_Helper = messagebox = None
    GATE_NODE_TYPES = SafetyAnalysis_FTA_FMEA = PMHF_TARGETS = None
    HazopDoc = EditNodeDialog = AutoMLHelper = None
    __all__ = []
else:
    __all__ = [
        "AutoMLApp",
        "FaultTreeNode",
        "AutoML_Helper",
        "AutoMLHelper",
        "messagebox",
        "tk",
        "ttk",
        "simpledialog",
        "filedialog",
        "scrolledtext",
        "GATE_NODE_TYPES",
        "PMHF_TARGETS",
        "HazopDoc",
        "EditNodeDialog",
        "SafetyAnalysis_FTA_FMEA",
    ]

from .AutoML import (
    parse_args,
    ensure_packages,
    ensure_ghostscript,
    install_best,
    start_watchdog_thread,
    start_cleanup_thread,
    manager_eater,
    ThreadPoolExecutor,
    _bootstrap,
)

__all__.extend(
    [
        "parse_args",
        "ensure_packages",
        "ensure_ghostscript",
        "install_best",
        "start_watchdog_thread",
        "start_cleanup_thread",
        "manager_eater",
        "ThreadPoolExecutor",
        "_bootstrap",
    ]
)
