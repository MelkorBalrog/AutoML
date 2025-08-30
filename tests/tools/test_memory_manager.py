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

"""Tests for :mod:`tools.memory_manager`."""

from __future__ import annotations

import time

from tools.memory_manager import MemoryManager


class TestMemoryManager:
    """Grouped tests for memory cleanup and monitoring."""

    def test_cleanup_discards_inactive_objects(self) -> None:
        manager = MemoryManager(interval=0.05, max_usage_percent=100)
        try:
            manager.lazy_load("a", lambda: object())
            manager._active.clear()
            manager.cleanup()
            assert manager._cache == {}
        finally:
            manager.shutdown()

    def test_monitor_triggers_on_threshold(self, monkeypatch) -> None:
        manager = MemoryManager(interval=0.05, max_usage_percent=50)
        called = {"value": False}

        def fake_percent() -> float:
            called["value"] = True
            return 99.0

        monkeypatch.setattr(manager, "_memory_percent", fake_percent)
        manager.lazy_load("a", lambda: object())
        manager._active.clear()
        try:
            time.sleep(0.1)
            assert manager._cache == {}
            assert called["value"] is True
        finally:
            manager.shutdown()
