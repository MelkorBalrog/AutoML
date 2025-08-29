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
"""Pausable background service management."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict


class PausableService(threading.Thread):
    """Thread executing *target* while supporting pause and stop."""

    def __init__(self, name: str, target: Callable[..., Any], args: tuple[Any, ...], kwargs: Dict[str, Any]):
        super().__init__(name=name, daemon=True)
        self._target = target
        self._args = args
        self._kwargs = kwargs
        self._pause = threading.Event()
        self._stop = threading.Event()
        self._pause.set()

    def run(self) -> None:  # pragma: no cover - trivial loop
        while not self._stop.is_set():
            self._pause.wait()
            if self._stop.is_set():
                break
            self._target(*self._args, **self._kwargs)

    def pause(self) -> None:
        self._pause.clear()

    def resume(self) -> None:
        self._pause.set()

    def stop(self) -> None:
        self._stop.set()
        self._pause.set()


@dataclass
class _ServiceEntry:
    service: PausableService
    refcount: int = 0
    last_release: float = field(default_factory=time.time)


class ServiceManager:
    """Manage pausable background services."""

    def __init__(self, idle_timeout: float = 30.0, check_interval: float = 1.0) -> None:
        self._services: Dict[str, _ServiceEntry] = {}
        self._lock = threading.Lock()
        self._idle_timeout = idle_timeout
        self._check_interval = check_interval
        self._shutdown = threading.Event()
        threading.Thread(target=self._watchdog, daemon=True).start()

    def acquire(self, name: str, target: Callable[..., Any], *args: Any, **kwargs: Any) -> PausableService:
        """Start or resume a named service thread."""
        with self._lock:
            entry = self._services.get(name)
            if entry:
                entry.refcount += 1
                if entry.service.is_alive():
                    entry.service.resume()
                else:
                    entry.service = PausableService(name, target, args, kwargs)
                    entry.service.start()
                return entry.service
            svc = PausableService(name, target, args, kwargs)
            svc.start()
            self._services[name] = _ServiceEntry(svc, 1)
            return svc

    def release(self, name: str) -> None:
        """Release a service reference and pause or stop as needed."""
        with self._lock:
            entry = self._services.get(name)
            if not entry:
                return
            entry.refcount = max(entry.refcount - 1, 0)
            entry.service.pause()
            if entry.refcount == 0:
                entry.last_release = time.time()

    def shutdown_all(self) -> None:
        """Stop and join all managed services."""
        with self._lock:
            entries = list(self._services.values())
            self._services.clear()
        for entry in entries:
            entry.service.stop()
            entry.service.join()
        self._shutdown.set()

    def _watchdog(self) -> None:  # pragma: no cover - timing dependent
        while not self._shutdown.is_set():
            time.sleep(self._check_interval)
            now = time.time()
            with self._lock:
                for name, entry in list(self._services.items()):
                    if entry.refcount == 0 and now - entry.last_release > self._idle_timeout:
                        entry.service.stop()
                        entry.service.join()
                        del self._services[name]


manager = ServiceManager()
