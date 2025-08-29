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
"""Regression tests for :mod:`tools.thread_manager` stop logic."""

from __future__ import annotations

import threading

from tools.thread_manager import ThreadManager


class TestStopAllBehaviour:
    """Grouped checks for stop-all handling."""

    def test_stop_all_skips_current_thread(self) -> None:
        errors: list[threading.ExceptHookArgs] = []

        def hook(args: threading.ExceptHookArgs) -> None:
            errors.append(args)

        old_hook = threading.excepthook
        threading.excepthook = hook

        mgr = ThreadManager(interval=0.05)

        def worker() -> None:
            mgr.stop_all()

        t = mgr.register("worker", worker, daemon=False)
        t.join()

        threading.excepthook = old_hook
        assert not errors
