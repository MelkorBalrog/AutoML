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
import builtins
import sys

import tools.splash_launcher as splash_module


class TestSplashLauncher:
    """Group SplashLauncher tests."""

    def test_launcher_invokes_main(self, monkeypatch):
        dummy = importlib.import_module("tests.dummy_module")
        dummy.called["main"] = False

        launcher = splash_module.SplashLauncher(module_name="tests.dummy_module")
        launcher.launch()

        assert dummy.called["main"] is True

    def test_version_fallback(self, monkeypatch):
        monkeypatch.setitem(sys.modules, "mainappsrc", None)
        monkeypatch.setitem(sys.modules, "mainappsrc.version", None)

        real_import = builtins.__import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "mainappsrc.version":
                raise ModuleNotFoundError
            return real_import(name, globals, locals, fromlist, level)

        monkeypatch.setattr(builtins, "__import__", fake_import)

        importlib.reload(splash_module)

        assert splash_module.VERSION == "0.0.0"
