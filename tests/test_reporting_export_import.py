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


def test_automl_core_imports_reporting_service():
    code = Path("mainappsrc/core/automl_core.py").read_text()
    tree = ast.parse(code)
    assert any(
        isinstance(node, ast.ImportFrom)
        and node.module == "mainappsrc.services.reporting"
        and any(alias.name == "ReportingExportService" for alias in node.names)
        for node in ast.walk(tree)
    ), "ReportingExportService import missing in automl_core"
