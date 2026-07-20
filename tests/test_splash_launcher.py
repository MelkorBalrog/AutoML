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
import types

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


class TestSplashLauncherThreadOwnership:
    """Group thread-affinity tests for every centralized Tk startup operation."""

    def test_complete_gui_startup_uses_root_owner_thread(self, monkeypatch):
        events = []
        owner_thread = threading.get_ident()

        def record(operation, identity):
            events.append((operation, identity, threading.get_ident()))

        class FakeRoot:
            def __init__(self):
                record("splash-root creation", self)

            def withdraw(self):
                record("splash withdrawal", self)

            def mainloop(self):
                record("splash event loop", self)

            def after(self, delay, callback):
                operation = "startup scheduled" if delay == 250 else f"close scheduled:{delay}"
                events.append((operation, self, threading.get_ident()))
                callback()

            def destroy(self):
                record("root destruction", self)

        class FakeSplash:
            def __init__(self, root, **kwargs):
                self.on_close = kwargs["on_close"]

            def close(self):
                record("splash closure", self)
                self.on_close()

        class FakeApplicationRoot:
            def __init__(self):
                record("application-root creation", self)

            def mainloop(self):
                record("application event loop", self)

        application_module = types.ModuleType("thread_affinity_application")

        def application_main():
            application_root = FakeApplicationRoot()
            application_root.mainloop()

        application_module.main = application_main
        splash_screen_module = types.ModuleType("gui.windows.splash_screen")
        splash_screen_module.SplashScreen = FakeSplash
        monkeypatch.setitem(sys.modules, "gui.windows.splash_screen", splash_screen_module)
        monkeypatch.setattr(splash_module.tk, "Tk", FakeRoot)

        launcher = splash_module.SplashLauncher(loader=lambda: application_module)
        launcher.launch()

        required = {
            "splash-root creation",
            "splash closure",
            "root destruction",
            "application-root creation",
            "splash event loop",
            "application event loop",
            "startup scheduled",
            "close scheduled:1000",
        }
        observed = {operation for operation, _, _ in events}
        assert required <= observed
        assert {thread_id for _, _, thread_id in events} == {owner_thread}
        assert launcher._owner_thread_id == owner_thread

    def test_event_loop_starts_before_loader_and_delayed_close(self, monkeypatch):
        """The splash must be drawable before synchronous startup begins."""

        events = []

        class FakeRoot:
            def withdraw(self):
                events.append("withdraw")

            def after(self, delay, callback):
                if delay == 250:
                    events.append(("startup scheduled", delay))
                    self.callback = callback
                else:
                    events.append(("close scheduled", delay))
                    callback()

            def mainloop(self):
                events.append("mainloop")
                self.callback()

            def destroy(self):
                events.append("destroy")

        class FakeSplash:
            def __init__(self, _root, **kwargs):
                self.on_close = kwargs["on_close"]

            def close(self):
                events.append("close")
                self.on_close()

        application = types.SimpleNamespace(main=lambda: events.append("application"))
        splash_screen_module = types.ModuleType("gui.windows.splash_screen")
        splash_screen_module.SplashScreen = FakeSplash
        monkeypatch.setitem(sys.modules, "gui.windows.splash_screen", splash_screen_module)
        monkeypatch.setattr(splash_module.tk, "Tk", FakeRoot)

        splash_module.SplashLauncher(loader=lambda: events.append("load") or application).launch()

        assert events.index("mainloop") < events.index("load")
        assert ("close scheduled", 1000) in events
        assert events[-1] == "application"

    def test_thread_assertion_reports_actionable_context(self):
        launcher = splash_module.SplashLauncher()
        launcher._owner_thread_id = -1
        launcher._root_creation_site = "test creation site"
        window = object()

        try:
            launcher._assert_owner_thread("test operation", window)
        except AssertionError as error:
            diagnostic = str(error)
        else:  # pragma: no cover - assertion is enabled in development tests
            raise AssertionError("thread-affinity assertion did not run")

        assert f"current_thread={threading.get_ident()!r}" in diagnostic
        assert "owner_thread=-1" in diagnostic
        assert "operation='test operation'" in diagnostic
        assert f"widget={window!r}" in diagnostic
        assert "creation_site='test creation site'" in diagnostic
