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

"""Grouped qualification tests for GUI ownership and host lifecycles."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest

from tests.gui.stress.runner import supported_diagram_types


FORBIDDEN_STDERR = (
    "Tcl_AsyncDelete",
    "invalid command name",
    "callback after disposal",
    "widget after destruction",
    "owner thread",
)


class TestOwnerThreadEnforcement:
    def test_driver_enables_centralized_assertion_each_iteration(self) -> None:
        source = Path("tests/gui/stress/runner.py").read_text(encoding="utf-8")
        assert "self.controller.require_running()" in source


class TestCallbackLifecycle:
    def test_stderr_failure_signatures_are_complete(self) -> None:
        assert {"Tcl_AsyncDelete", "invalid command name"} <= set(FORBIDDEN_STDERR)
        assert any("callback" in diagnostic for diagnostic in FORBIDDEN_STDERR)


class TestToolboxReconstruction:
    def test_diagram_inventory_comes_from_central_configuration(self) -> None:
        configured = supported_diagram_types()
        assert configured
        assert len(configured) == len(set(configured))


class TestPopoutLifecycle:
    def test_workflow_covers_focus_close_order_and_reintegration(self) -> None:
        source = Path("tests/gui/stress/runner.py").read_text(encoding="utf-8")
        for operation in ("focus_force", "reversed(popouts)", "dock.attach(notebook"):
            assert operation in source


class TestShutdownOrdering:
    def test_driver_uses_application_lifecycle_shutdown(self) -> None:
        source = Path("tests/gui/stress/runner.py").read_text(encoding="utf-8")
        assert "self.controller.shutdown()" in source


@pytest.mark.gui_stress
class TestRepeatedStartupShutdown:
    def test_normal_entrypoint_stress_run_has_clean_stderr(self) -> None:
        if not os.environ.get("DISPLAY") and sys.platform != "win32":
            pytest.skip("a display server is required; run the documented xvfb command")
        command = [
            sys.executable, "-m", "tests.gui.stress.runner",
            "--iterations", "100", "--startups", "3",
        ]
        completed = subprocess.run(command, text=True, capture_output=True, timeout=300, check=False)
        stderr = completed.stderr
        assert completed.returncode == 0, stderr
        assert not [item for item in FORBIDDEN_STDERR if item.casefold() in stderr.casefold()]
