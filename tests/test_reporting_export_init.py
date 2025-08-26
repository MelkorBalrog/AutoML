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

import ast
from pathlib import Path


def test_service_init_mixin_initialises_reporting_service():
    code = Path("mainappsrc/core/service_init_mixin.py").read_text()
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if any(
                isinstance(t, ast.Attribute)
                and t.attr == "reporting_export"
                and isinstance(t.value, ast.Name)
                and t.value.id == "self"
                for t in node.targets
            ):
                if (
                    isinstance(node.value, ast.Call)
                    and getattr(node.value.func, "id", None) == "ReportingExportService"
                ):
                    break
    else:
        raise AssertionError(
            "ServiceInitMixin.setup_services does not assign ReportingExportService to self.reporting_export"
        )
