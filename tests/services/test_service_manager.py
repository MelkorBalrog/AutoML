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
"""Tests for the new ServiceManager."""

from __future__ import annotations

import threading
import time

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mainappsrc.services.service_manager import ServiceManager


def _worker(ran: threading.Event) -> None:
    """Simple worker function that records execution."""
    ran.set()
    time.sleep(0.01)


class TestServiceManagerLifecycle:
    """Lifecycle management of background services."""

    def test_acquire_and_shutdown_service(self) -> None:
        manager = ServiceManager(check_interval=0.01)
        ran = threading.Event()
        service = manager.acquire("dummy", _worker, ran)
        assert ran.wait(1.0)
        entry = manager._services["dummy"]
        manager.release("dummy")
        manager.shutdown_all()
        assert not entry.service.is_alive()


class TestServiceManagerReferenceCounting:
    """Reference counting behaviour for shared services."""

    def test_release_pauses_only_on_zero_refcount(self) -> None:
        manager = ServiceManager(check_interval=0.01)
        ran = threading.Event()
        manager.acquire("dummy", _worker, ran)
        manager.acquire("dummy", _worker, ran)
        entry = manager._services["dummy"]
        assert entry.refcount == 2
        manager.release("dummy")
        assert entry.refcount == 1
        assert entry.service._pause.is_set()
        manager.release("dummy")
        assert not entry.service._pause.is_set()
        manager.shutdown_all()
