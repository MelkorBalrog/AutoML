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
from pathlib import Path

# Ensure project root on path and stub optional GUI modules
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

sys.modules.setdefault('PIL', types.ModuleType('PIL'))
sys.modules.setdefault('PIL.Image', types.ModuleType('PIL.Image'))
sys.modules.setdefault('PIL.ImageDraw', types.ModuleType('PIL.ImageDraw'))
sys.modules.setdefault('PIL.ImageFont', types.ModuleType('PIL.ImageFont'))
sys.modules.setdefault('PIL.ImageTk', types.ModuleType('PIL.ImageTk'))

from mainappsrc.models.fta.fault_tree_node import FaultTreeNode
from mainappsrc.services.safety_analysis import SafetyAnalysisService


class SimpleComponent:
    def __init__(self, name, fit):
        self.name = name
        self.fit = fit
        self.quantity = 1
        self.sub_boms = []


class DummyRiskApp:
    def get_safety_goal_asil(self, app, sg_name):
        return "QM"


class DummyApp:
    def __init__(self):
        self.reliability_components = [SimpleComponent("CompA", 100.0)]
        self.risk_app = DummyRiskApp()


def test_compute_fmeda_metrics_basic():
    app = DummyApp()
    service = SafetyAnalysisService(app)

    parent = FaultTreeNode("CompA", "FUNCTION")
    event = FaultTreeNode("BE", "BASIC EVENT", parent=parent)
    event.fmeda_fault_fraction = 1.0
    event.fmeda_diag_cov = 0.5

    metrics = service.compute_fmeda_metrics([event])
    assert metrics["total"] == 100.0
    assert metrics["spfm_raw"] == 50.0
    assert metrics["lpfm_raw"] == 0.0
