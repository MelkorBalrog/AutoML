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


def test_ui_setup_mixin_defines_setup_style():
    tree = ast.parse(Path("mainappsrc/ui/ui_setup.py").read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "UISetupMixin":
            if any(isinstance(n, ast.FunctionDef) and n.name == "setup_style" for n in node.body):
                return
            break
    raise AssertionError("UISetupMixin.setup_style is not defined")
