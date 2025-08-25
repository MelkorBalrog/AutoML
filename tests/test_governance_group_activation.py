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
import tkinter as tk
import pytest
import types

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

    def size(self):
        return len(self.items)

    def delete(self, i):
        del self.items[i]


class DummyMenu:
    def __init__(self):
        self.state = None

    def entryconfig(self, _idx, state=tk.DISABLED):
        self.state = state


@pytest.mark.parametrize(
    "work_product,parent",
    [
        ("FTA", "Quantitative Analysis"),
        ("Safety & Security Case", "GSN"),
        ("GSN Argumentation", "GSN"),
        ("FMEA", "Qualitative Analysis"),
        ("Prototype Assurance Analysis", "Qualitative Analysis"),
        ("FMEDA", "Quantitative Analysis"),
        ("Causal Bayesian Network Analysis", "Quantitative Analysis"),
        ("Mission Profile", "Quantitative Analysis"),
        ("Reliability Analysis", "Quantitative Analysis"),
    ],
)
def test_work_product_groups_follow_phase(work_product, parent):
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    diag = repo.create_diagram("Governance Diagram", name="Gov")
    toolbox = SafetyManagementToolbox()
    toolbox.modules = [GovernanceModule(name="P1", diagrams=["Gov"]), GovernanceModule(name="P2")]
    toolbox.diagrams = {"Gov": diag.diag_id}
    toolbox.set_active_module("P1")

    app = AutoMLApp.__new__(AutoMLApp)
    lb = DummyListbox()
    area = AutoMLApp.WORK_PRODUCT_INFO[work_product][0]
    app.tool_listboxes = {area: lb}
    app.tool_categories = {area: []}
    app.tool_actions = {}
    wp_menu = DummyMenu()
    parent_menu = wp_menu if work_product == parent else DummyMenu()
    app.work_product_menus = {work_product: [(wp_menu, 0)]}
    if parent not in app.work_product_menus:
        app.work_product_menus[parent] = [(parent_menu, 0)]
    app.enabled_work_products = set()
    app.enable_process_area = lambda area: None
    app.tool_to_work_product = {info[1]: name for name, info in AutoMLApp.WORK_PRODUCT_INFO.items()}
    app.update_views = lambda: None
    app.lifecycle_ui = types.SimpleNamespace(_remove_tool_category=lambda n: None)
    app.safety_mgmt_toolbox = toolbox
    app.refresh_tool_enablement = AutoMLApp.refresh_tool_enablement.__get__(app, AutoMLApp)
    app.enable_work_product = AutoMLApp.enable_work_product.__get__(app, AutoMLApp)
    app.disable_work_product = AutoMLApp.disable_work_product.__get__(app, AutoMLApp)

    toolbox.add_work_product("Gov", work_product, "")
    toolbox.on_change = app.refresh_tool_enablement
    app.refresh_tool_enablement()

    assert work_product in app.enabled_work_products
    assert parent in app.enabled_work_products
    assert wp_menu.state == tk.NORMAL
    assert parent_menu.state == tk.NORMAL
    assert area in app.tool_listboxes

    toolbox.set_active_module("P2")
    app.refresh_tool_enablement()
    assert work_product not in app.enabled_work_products
    assert parent not in app.enabled_work_products
    assert wp_menu.state == tk.DISABLED
    assert parent_menu.state == tk.DISABLED
    assert area not in app.tool_listboxes
    # Reset global toolbox to avoid side effects on other tests
    from analysis import safety_management as _sm
    _sm.ACTIVE_TOOLBOX = None

