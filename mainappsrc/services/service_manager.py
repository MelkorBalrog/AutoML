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
"""Threaded service loader and monitor."""

from __future__ import annotations

from dataclasses import dataclass
import threading
import time
from typing import Any, Callable, Dict

from tools.thread_manager import manager as thread_manager


@dataclass
class _ServiceInfo:
    instance: Any
    thread: threading.Thread
    refcount: int
    recoverable: bool


class ServiceManager:
    """Manage application services in dedicated threads.

    Services are instantiated lazily when :meth:`request` is called and run on
    monitored threads.  When released they are shut down and their threads are
    stopped.  A lightweight watchdog periodically checks whether recoverable
    services are still alive and restarts them if necessary.
    """

    def __init__(self, interval: float = 1.0) -> None:
        self._services: Dict[str, _ServiceInfo] = {}
        self._lock = threading.Lock()
        self._interval = interval
        thread_manager.register("service_manager", self._watchdog, daemon=True)

    def request(
        self,
        name: str,
        factory: Callable[[], Any],
        *,
        recoverable: bool = True,
    ) -> Any:
        """Return an existing service or create a new threaded instance."""
        with self._lock:
            info = self._services.get(name)
            if info:
                info.refcount += 1
                return info.instance
            instance = factory()
            target = getattr(instance, "run", None)
            if not callable(target):  # pragma: no cover - defensive
                raise AttributeError(f"Service '{name}' missing callable 'run' method")
            thread = thread_manager.register(f"service:{name}", target)
            self._services[name] = _ServiceInfo(instance, thread, 1, recoverable)
            return instance

    def release(self, name: str) -> None:
        """Decrease the reference count and stop the service if unused."""
        with self._lock:
            info = self._services.get(name)
            if not info:
                return
            info.refcount -= 1
            if info.refcount <= 0:
                thread_manager.unregister(f"service:{name}")
                shutdown = getattr(info.instance, "shutdown", None)
                if callable(shutdown):
                    shutdown()
                del self._services[name]

    def _watchdog(self) -> None:  # pragma: no cover - simple loop
        while True:
            time.sleep(self._interval)
            with self._lock:
                for name, info in list(self._services.items()):
                    if info.recoverable and not info.thread.is_alive():
                        thread = thread_manager.register(
                            f"service:{name}", getattr(info.instance, "run")
                        )
                        info.thread = thread


manager = ServiceManager()
