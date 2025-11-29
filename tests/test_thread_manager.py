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

import logging
import threading
import time

from tools.thread_manager import ThreadManager


class TestThreadManager:
    def test_thread_manager_restarts_dead_thread(self) -> None:
        runs = {"count": 0}

        def worker() -> None:
            runs["count"] += 1

        manager = ThreadManager(interval=0.05)
        manager.register("t1", worker, daemon=True)
        time.sleep(0.15)  # allow thread to run and be restarted
        assert runs["count"] >= 2
        manager.stop_all()

    def test_register_current_thread(self) -> None:
        manager = ThreadManager(interval=0.05)
        current = manager.register_current("main")
        assert current is threading.current_thread()
        manager._check_threads()  # ensure no restart attempt
        manager.stop_all()

    def test_stop_all_signals_stop_event(self) -> None:
        stop_event = threading.Event()
        started = threading.Event()

        def worker(event: threading.Event) -> None:
            started.set()
            event.wait()

        manager = ThreadManager(interval=0.05)
        thread = manager.register(
            "stoppable",
            worker,
            args=(stop_event,),
            stop_event=stop_event,
        )
        assert started.wait(timeout=1.0)
        manager.stop_all(timeout=0.5)
        assert stop_event.is_set()
        assert not thread.is_alive()

    def test_stop_all_warns_on_unresponsive_thread(self, caplog) -> None:
        caplog.set_level(logging.WARNING)

        def stubborn() -> None:
            time.sleep(0.5)

        manager = ThreadManager(interval=0.05)
        manager.register("stubborn", stubborn)
        manager.stop_all(timeout=0.05)
        assert any(
            "did not exit within" in record.message for record in caplog.records
        )
