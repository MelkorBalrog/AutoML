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
"""Grouped tests ensuring background service threads operate."""

from __future__ import annotations

import time

from tools.crash_report_logger import start_watchdog_thread, stop_watchdog_thread
from tools.model_loader import start_cleanup_thread, stop_cleanup_thread, model_loader


def test_crash_watchdog_thread() -> None:
    stop, thread = start_watchdog_thread(timeout=0.2, interval=0.05)
    time.sleep(0.1)
    assert thread.is_alive()
    stop_watchdog_thread(stop)


def test_model_loader_cleanup_thread() -> None:
    model_loader.get("dummy", lambda: object())
    stop, thread = start_cleanup_thread(interval=0.05)
    time.sleep(0.1)
    assert thread.is_alive()
    stop_cleanup_thread(stop)
