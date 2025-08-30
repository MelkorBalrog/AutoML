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
import threading

from tools.thread_manager import ThreadManager


def test_thread_manager_restarts_dead_thread() -> None:
    runs = {"count": 0}

    def worker() -> None:
        runs["count"] += 1

    manager = ThreadManager(interval=0.05)
    manager.register("t1", worker, daemon=True)
    time.sleep(0.15)  # allow thread to run and be restarted
    assert runs["count"] >= 2
    manager.stop_all()


def test_register_current_thread() -> None:
    manager = ThreadManager(interval=0.05)
    current = manager.register_current("main")
    assert current is threading.current_thread()
    manager._check_threads()  # ensure no restart attempt
    manager.stop_all()
