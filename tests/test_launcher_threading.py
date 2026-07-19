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

import AutoML as launcher


class TestSequentialDependencyStartup:
    """Grouped checks for dependency work before GUI construction."""

    def test_ensure_packages_runs_sequentially(self, monkeypatch):
        fake_required = ["pkg1", "pkg2"]
        monkeypatch.setattr(launcher, "REQUIRED_PACKAGES", fake_required)
        monkeypatch.setattr(
            launcher.importlib, "import_module", lambda name: (_ for _ in ()).throw(ImportError())
        )
        events = []

        class FakeProc:
            def __init__(self, command):
                self.package = command[-1]
                events.append(("start", self.package))

            def wait(self):
                events.append(("finish", self.package))

        monkeypatch.setattr(launcher.subprocess, "Popen", lambda command: FakeProc(command))
        monkeypatch.setattr(launcher.memory_manager, "register_process", lambda *a, **k: None)
        monkeypatch.setattr(launcher.memory_manager, "cleanup", lambda: None)

        launcher.ensure_packages()

        assert events == [
            ("start", "pkg1"),
            ("finish", "pkg1"),
            ("start", "pkg2"),
            ("finish", "pkg2"),
        ]
