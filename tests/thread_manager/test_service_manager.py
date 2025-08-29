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
"""Grouped regression tests for :mod:`tools.service_manager`."""

from __future__ import annotations

import time

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.service_manager import ServiceManager


class TestServiceManagerLifecycle:
    """Lifecycle and pause/resume behaviour."""

    def test_reuses_paused_service(self) -> None:
        runs: list[int] = []

        def worker(stop, resume) -> None:  # type: ignore[no-untyped-def]
            runs.append(1)
            resume.clear()
            while not stop.is_set() and not resume.wait(0.01):
                pass

        mgr = ServiceManager()
        svc = mgr.acquire("demo", worker)
        time.sleep(0.05)
        assert runs
        thread = svc.thread
        mgr.release("demo")
        time.sleep(0.05)
        assert thread.is_alive()
        mgr.acquire("demo", worker)
        time.sleep(0.05)
        assert len(runs) > 1
        assert svc.thread is thread
        mgr.release("demo")
        mgr.shutdown_all()

    def test_shutdown_all_terminates_services(self) -> None:
        stop_called: list[bool] = []

        def worker(stop, resume) -> None:  # type: ignore[no-untyped-def]
            if stop.wait(0.01):
                stop_called.append(True)

        mgr = ServiceManager()
        mgr.acquire("demo", worker)
        mgr.release("demo")
        mgr.shutdown_all()
        assert stop_called
