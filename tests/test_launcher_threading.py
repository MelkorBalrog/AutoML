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

import time
import automl as launcher


def test_ensure_packages_runs_in_parallel(monkeypatch):
    fake_required = ["pkg1", "pkg2"]
    monkeypatch.setattr(launcher, "REQUIRED_PACKAGES", fake_required)

    def fake_import_module(name):
        raise ImportError

    monkeypatch.setattr(launcher.importlib, "import_module", fake_import_module)

    class FakeProc:
        def __init__(self, *args, **kwargs):
            pass

        def wait(self):
            time.sleep(0.2)

    monkeypatch.setattr(launcher.subprocess, "Popen", lambda *a, **k: FakeProc())
    monkeypatch.setattr(launcher.memory_manager, "register_process", lambda *a, **k: None)
    monkeypatch.setattr(launcher.memory_manager, "cleanup", lambda: None)

    start = time.time()
    launcher.ensure_packages()
    elapsed = time.time() - start
    assert elapsed < 0.35
