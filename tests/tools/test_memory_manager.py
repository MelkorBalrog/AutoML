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

import threading

from tools.memory_manager import MemoryManager


class TestMemoryManager:
    """Grouped tests for memory cleanup and monitoring."""

    def test_cleanup_discards_inactive_objects(self) -> None:
        manager = MemoryManager(interval=0.05, max_usage_percent=100)
        try:
            manager.lazy_load("a", lambda: object())
            with manager._lock:
                manager._active.clear()
            manager.cleanup()
            assert manager._cache == {}
        finally:
            manager.shutdown()

    def test_discard_prefix_removes_keys(self) -> None:
        manager = MemoryManager(interval=0.05, max_usage_percent=100)
        try:
            manager.lazy_load("d1:toolbox:core", lambda: object())
            manager.lazy_load("d1:toolbox:extra", lambda: object())
            manager.lazy_load("d2:toolbox:core", lambda: object())
            manager.discard_prefix("d1:toolbox:")
            with manager._lock:
                assert "d1:toolbox:core" not in manager._cache
                assert "d1:toolbox:extra" not in manager._cache
                assert "d2:toolbox:core" in manager._cache
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
        with manager._lock:
            manager._active.clear()
        try:
            time.sleep(0.1)
            assert manager._cache == {}
            assert called["value"] is True
        finally:
            manager.shutdown()

    def test_concurrent_access_preserves_active(self) -> None:
        manager = MemoryManager(interval=0.05, max_usage_percent=100)
        try:
            manager.lazy_load("keep", lambda: object())
            manager.lazy_load("tmp", lambda: object())
            with manager._lock:
                manager._active.discard("tmp")

            t_cleanup = threading.Thread(target=manager.cleanup)

            def mark_later() -> None:
                time.sleep(0.01)
                manager.mark_active("keep")

            t_mark = threading.Thread(target=mark_later)
            t_cleanup.start()
            t_mark.start()
            t_cleanup.join()
            t_mark.join()

            with manager._lock:
                assert "keep" in manager._cache
                assert "tmp" not in manager._cache
        finally:
            manager.shutdown()
