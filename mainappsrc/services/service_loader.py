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
"""Lazy service registry leveraging the shared memory manager.

Services are constructed on first use and discarded once released.
The registry uses :mod:`tools.memory_manager` to cache active
services.  Callers can acquire services via :meth:`get` and should
release them with :meth:`release` when finished.  The :meth:`use`
context manager automates this pattern.
"""

from __future__ import annotations

import threading
from contextlib import contextmanager
from typing import Any

from tools.memory_manager import manager as memory_manager
from tools.thread_manager import manager as thread_manager
from mainappsrc import services


class LazyServiceRegistry:
    """Provide on-demand access to application services."""

    def __init__(self, app: Any, interval: float = 60.0) -> None:
        self._app = app
        self._interval = interval
        self._stop = threading.Event()
        self._name = f"service_registry_{id(self)}"
        thread_manager.register(self._name, self._monitor, daemon=True)

    def _monitor(self) -> None:
        while not self._stop.is_set():
            self._stop.wait(self._interval)
            memory_manager.cleanup()

    def shutdown(self) -> None:
        self._stop.set()
        thread = thread_manager.unregister(self._name)
        if thread:
            thread.join()

    def get(self, name: str) -> Any:
        """Return service *name*, creating it if necessary."""

        return memory_manager.lazy_load(
            name, lambda: getattr(services, name)(self._app)
        )

    def release(self, name: str) -> None:
        """Destroy cached instance of service *name*."""

        memory_manager._active.discard(name)  # type: ignore[attr-defined]
        memory_manager.cleanup()

    @contextmanager
    def use(self, name: str):
        """Context manager yielding a lazily loaded service.

        The service is automatically released when the context exits.
        """

        service = self.get(name)
        try:
            yield service
        finally:
            self.release(name)
