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

"""Ensure hazard analysis work products do not activate risk assessment tools."""

from mainappsrc.core.automl_core import AutoMLApp
from mainappsrc.core.validation_consistency import Validation_Consistency


def test_hazop_does_not_enable_risk_assessment():
    app = AutoMLApp.__new__(AutoMLApp)
    app.WORK_PRODUCT_INFO = AutoMLApp.WORK_PRODUCT_INFO
    app.WORK_PRODUCT_PARENTS = AutoMLApp.WORK_PRODUCT_PARENTS
    app.work_product_menus = {}
    app.tool_listboxes = {}
    app.tool_actions = {}
    app.enabled_work_products = set()
    app.update_views = lambda: None
    app.validation_consistency = Validation_Consistency(app)

    app.enable_work_product("HAZOP")

    assert "HAZOP" in app.enabled_work_products
    assert "Risk Assessment" not in app.enabled_work_products
