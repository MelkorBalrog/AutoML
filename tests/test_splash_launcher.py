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
import threading
import tkinter as tk
import types

import pytest
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

    def _make_loader(self, calls):
        def loader() -> types.SimpleNamespace:
            calls.append(("loader", threading.current_thread().name))
            return types.SimpleNamespace(
                main=lambda: calls.append(("main", threading.current_thread().name))
            )

        return loader

    def test_loader_runs_in_background_thread(self):
        calls: list[tuple[str, str]] = []
        loader = self._make_loader(calls)
        try:
            launcher = splash_module.SplashLauncher(loader=loader, post_delay=0)
        except tk.TclError:
            pytest.skip("Tk not available")
        launcher.launch()
        assert calls[0][1] != threading.current_thread().name
        assert calls[1][0] == "main"

    def test_main_called_after_launch(self):
        calls: list[tuple[str, str]] = []
        loader = self._make_loader(calls)
        try:
            launcher = splash_module.SplashLauncher(loader=loader, post_delay=0)
        except tk.TclError:
            pytest.skip("Tk not available")
        launcher.launch()
        assert ("main", threading.current_thread().name) in calls
