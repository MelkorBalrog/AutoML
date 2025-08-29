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
"""Tests for idle shutdown of diagram service threads."""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from mainappsrc.services import service_manager

pytestmark = [pytest.mark.services, pytest.mark.diagram]


class IdleService:
    """Service that can be paused and shut down."""

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

    def shutdown(self) -> None:
        self.stop.set()


class TestDiagramServiceIdleShutdown:
    """Grouped checks for idle thread termination."""

    def test_thread_stops_after_idle_timeout(self) -> None:
        """Threads terminate when left idle beyond timeout."""
        orig_interval = service_manager._interval
        orig_timeout = service_manager._idle_timeout
        service_manager._interval = 0.05
        service_manager._idle_timeout = 0.1

        service = service_manager.request("diagram-idle", IdleService)
        assert service.running.wait(1.0)
        thread = service_manager._services["diagram-idle"].thread

        service_manager.release("diagram-idle")
        assert service.paused.wait(1.0)

        time.sleep(1.2)
        assert "diagram-idle" not in service_manager._services
        assert not thread.is_alive()

        service_manager._interval = orig_interval
        service_manager._idle_timeout = orig_timeout
        service_manager.shutdown("diagram-idle")
