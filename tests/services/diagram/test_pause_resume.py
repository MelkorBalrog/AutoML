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
"""Tests for diagram service thread reuse after pause and resume."""

from __future__ import annotations

import threading
import time
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from mainappsrc.services import service_manager

pytestmark = [pytest.mark.services, pytest.mark.diagram]


class PausableService:
    """Minimal service supporting pause and resume."""

    def __init__(self) -> None:
        self.running = threading.Event()
        self.paused = threading.Event()
        self.stop = threading.Event()

    def run(self) -> None:
        self.running.set()
        while not self.stop.is_set():
            if self.paused.is_set():
                time.sleep(0.01)
                continue
            time.sleep(0.01)

    def pause(self) -> None:
        self.paused.set()

    def resume(self) -> None:
        self.paused.clear()

    def shutdown(self) -> None:
        self.stop.set()


class TestDiagramServicePauseResume:
    """Grouped checks for thread reuse when diagrams reopen."""

    def test_reuses_thread_on_resume(self) -> None:
        """Thread objects persist across release and request."""
        service = service_manager.request("diagram-test", PausableService)
        assert service.running.wait(1.0)
        thread = service_manager._services["diagram-test"].thread

        service_manager.release("diagram-test")
        assert service.paused.wait(1.0)

        service_manager.request("diagram-test", PausableService)
        thread2 = service_manager._services["diagram-test"].thread
        assert thread is thread2
        assert thread2.is_alive()

        service_manager.shutdown("diagram-test")
