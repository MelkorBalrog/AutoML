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

import tkinter as tk
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from analysis.safety_management import SafetyManagementToolbox, GovernanceModule
from mainappsrc.models.sysml.sysml_repository import SysMLRepository
from AutoML import AutoMLApp


class DummyListbox:
    def __init__(self):
        self.items = []
        self.colors = []

    def get(self, *_):
        return self.items

    def insert(self, index, item):
        self.items.insert(index if isinstance(index, int) else len(self.items), item)

    def itemconfig(self, index, foreground="black"):
        self.colors.append((index, foreground))


class DummyMenu:
    def __init__(self):
        self.state = None

    def entryconfig(self, _idx, state=tk.DISABLED):
        self.state = state


def test_repository_phase_enables_work_product():
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    repo.active_phase = "P1"
    diag = repo.create_diagram("Governance Diagram", name="Gov")
    diag.tags.append("safety-management")
    toolbox = SafetyManagementToolbox()
    toolbox.modules = [GovernanceModule(name="P1"), GovernanceModule(name="P2")]
    toolbox.diagrams = {"Gov": diag.diag_id}
    toolbox.set_active_module("P1")

    app = AutoMLApp.__new__(AutoMLApp)
    lb = DummyListbox()
    info = AutoMLApp.WORK_PRODUCT_INFO["GSN Argumentation"]
    app.tool_listboxes = {info[0]: lb}
    app.tool_categories = {info[0]: []}
    app.tool_actions = {}
    wp_menu = DummyMenu()
    parent_menu = DummyMenu()
    app.work_product_menus = {"GSN Argumentation": [(wp_menu, 0)], "GSN": [(parent_menu, 0)]}
    app.enabled_work_products = set()
    app.enable_process_area = lambda area: None
    app.tool_to_work_product = {info[1]: name for name, info in AutoMLApp.WORK_PRODUCT_INFO.items()}
    app.update_views = lambda: None
    app.safety_mgmt_toolbox = toolbox
    app.refresh_tool_enablement = AutoMLApp.refresh_tool_enablement.__get__(app, AutoMLApp)
    app.enable_work_product = AutoMLApp.enable_work_product.__get__(app, AutoMLApp)
    app.disable_work_product = AutoMLApp.disable_work_product.__get__(app, AutoMLApp)

    toolbox.add_work_product("Gov", "GSN Argumentation", "")
    toolbox.on_change = app.refresh_tool_enablement
    app.refresh_tool_enablement()

    assert "GSN Argumentation" in app.enabled_work_products
    assert "GSN" in app.enabled_work_products
    assert wp_menu.state == tk.NORMAL
    assert parent_menu.state == tk.NORMAL
