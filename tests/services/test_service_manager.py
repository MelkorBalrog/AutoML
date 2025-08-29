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
"""Tests for the threaded service manager."""

from __future__ import annotations

import threading
import time

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mainappsrc.services import service_manager


class FaultyService:
    def __init__(self) -> None:
        self.runs = 0
        self.stop = threading.Event()

    def run(self) -> None:
        self.runs += 1
        if self.runs == 1:
            raise RuntimeError("boom")
        self.stop.wait()

    def shutdown(self) -> None:
        self.stop.set()


class PausableService:
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


class PausableService:
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


class TestServiceManagerLifecycle:
    def test_start_and_pause_service(self) -> None:
        """Services start in threads and pause when released."""
        service = service_manager.request("dummy", PausableService)
        assert service.running.wait(1.0)
        thread = service_manager._services["dummy"].thread
        service_manager.release("dummy")
        assert service.paused.is_set()
        assert thread.is_alive()
        service_manager.shutdown("dummy")

    def test_shutdown_service(self) -> None:
        """Services can be terminated explicitly."""
        service = service_manager.request("dummy2", PausableService)
        assert service.running.wait(1.0)
        thread = service_manager._services["dummy2"].thread
        service_manager.release("dummy2")
        service_manager.shutdown("dummy2")
        thread.join(1.0)
        assert not thread.is_alive()

    def test_release_waits_for_thread(self) -> None:
        """Releasing a service waits for its thread to finish."""
        service = service_manager.request("dummy2", DummyService)
        assert service.running.wait(1.0)
        thread = service_manager._services["dummy2"].thread
        service_manager.release("dummy2")
        thread.join(1.0)
        assert not thread.is_alive()


class TestServiceManagerRecovery:
    def test_restart_faulted_service(self) -> None:
        """Faulted services are restarted by the manager."""
        service = service_manager.request("faulty", FaultyService)
        for _ in range(50):
            if service.runs >= 2:
                break
            time.sleep(0.05)
        service_manager.release("faulty")
        assert service.runs >= 2
        service_manager.shutdown("faulty")


class TestServiceManagerThreadOptions:
    def test_non_daemon_thread_and_join(self) -> None:
        """Service threads can run non-daemon and be joined."""

        class BlockingService:
            def __init__(self) -> None:
                self.started = threading.Event()
                self.stop = threading.Event()

            def run(self) -> None:
                self.started.set()
                self.stop.wait()

            def shutdown(self) -> None:
                self.stop.set()

        service_manager.request("block", BlockingService, daemon=False)
        assert service_manager._services["block"].thread.daemon is False
        assert service_manager._services["block"].instance.started.wait(1.0)
        service_manager._services["block"].instance.shutdown()
        service_manager.join("block")
        service_manager.release("block")
        service_manager.shutdown("block")


class TestServiceManagerPauseResume:
    def test_pause_and_resume_service(self) -> None:
        """Services pause when unused and resume on demand."""
        service = service_manager.request("pausable", PausableService)
        assert service.running.wait(1.0)
        thread = service_manager._services["pausable"].thread
        service_manager.release("pausable")
        assert service.paused.is_set()
        service_manager.request("pausable", PausableService)
        assert not service.paused.is_set()
        assert service_manager._services["pausable"].thread is thread
        service_manager.release("pausable")
        service_manager.shutdown("pausable")

    def test_resume_restarts_dead_thread(self) -> None:
        """Resuming a paused service restarts its thread if needed."""
        service = service_manager.request("restart", PausableService)
        assert service.running.wait(1.0)
        service_manager.release("restart")
        service.stop.set()  # kill the thread after pausing
        thread = service_manager._services["restart"].thread
        thread.join()
        service.stop.clear()
        service_manager.request("restart", PausableService)
        assert service_manager._services["restart"].thread is not thread
        service_manager.release("restart")
        service_manager.shutdown("restart")
