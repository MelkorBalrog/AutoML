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
"""Regression tests for :mod:`tools.thread_manager`."""

from __future__ import annotations

import threading
import time

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.thread_manager import ThreadManager


class TestThreadManagerBehaviour:
    """Grouped checks for thread restart handling."""

    def test_restarts_unexpectedly_stopped_thread(self) -> None:
        runs = []

        def worker() -> None:
            runs.append(1)

        mgr = ThreadManager(interval=0.05)
        mgr.register("worker", worker)
        time.sleep(0.2)
        assert len(runs) > 1
        mgr.stop_all()

    def test_stopped_thread_not_restarted(self) -> None:
        stop = threading.Event()
        runs = []

        def worker() -> None:
            runs.append(1)
            while not stop.is_set():
                stop.wait(0.01)

        mgr = ThreadManager(interval=0.05)
        mgr.register("worker", worker, stop_event=stop)
        stop.set()
        time.sleep(0.2)
        assert len(runs) == 1
        assert not mgr._threads
        mgr.stop_all()
