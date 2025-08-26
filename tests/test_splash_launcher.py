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

import importlib
import sys
from types import ModuleType


def test_launcher_invokes_main(monkeypatch):
    dummy = importlib.import_module("tests.dummy_module")
    dummy.called["main"] = False

    from tools.splash_launcher import SplashLauncher

    launcher = SplashLauncher(module_name="tests.dummy_module")
    launcher.launch()

    assert dummy.called["main"] is True


def test_launcher_prefers_project_gui(monkeypatch):
    """Ensure an external ``gui`` package doesn't shadow the project one."""
    monkeypatch.setitem(sys.modules, "gui", ModuleType("gui"))
    sys.modules.pop("AutoML.tools.splash_launcher", None)
    sys.modules.pop("tools.splash_launcher", None)
    module = importlib.import_module("AutoML.tools.splash_launcher")
    assert module.SplashScreen.__module__ == "AutoML.gui.windows.splash_screen"
