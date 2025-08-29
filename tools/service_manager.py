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
"""Thread service manager supporting pause and resume.

The :class:`ServiceManager` wraps worker threads in :class:`PausableService`
containers.  Services are reference counted: acquiring an existing service
resumes its thread while releasing a service merely pauses it. Threads are
terminated only when :meth:`shutdown_all` is invoked, preventing premature
shutdowns while diagrams remain open.
"""

from __future__ import annotations

from dataclasses import dataclass
import threading
from typing import Any, Callable, Dict, Tuple


@dataclass
class PausableService:
    """Run *target* inside a pausable thread."""

    target: Callable[..., Any]
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]
    thread: threading.Thread
    resume: threading.Event
    stop: threading.Event

    @classmethod
    def start(
        cls, target: Callable[..., Any], args: Tuple[Any, ...], kwargs: Dict[str, Any]
    ) -> "PausableService":
        resume = threading.Event()
        resume.set()
        stop = threading.Event()

        def runner() -> None:
            while not stop.is_set():
                resume.wait()
                target(stop, resume, *args, **kwargs)

        thread = threading.Thread(target=runner, daemon=True)
        thread.start()
        return cls(target, args, kwargs, thread, resume, stop)

    def pause(self) -> None:
        self.resume.clear()

    def resume_thread(self) -> None:
        self.resume.set()

    def stop_thread(self) -> None:
        self.stop.set()
        self.resume.set()
        if self.thread.is_alive():
            self.thread.join()


class ServiceManager:
    """Reference-counted service lifecycle controller."""

    def __init__(self) -> None:
        self._services: Dict[str, Tuple[PausableService, int]] = {}
        self._lock = threading.Lock()

    def acquire(
        self, name: str, target: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> PausableService:
        """Return a running service for *name*, starting it if needed."""
        with self._lock:
            if name in self._services:
                svc, count = self._services[name]
                self._services[name] = (svc, count + 1)
                svc.resume_thread()
                return svc
            svc = PausableService.start(target, args, kwargs)
            self._services[name] = (svc, 1)
            return svc

    def release(self, name: str) -> None:
        """Decrease reference count and pause service when unused."""
        with self._lock:
            entry = self._services.get(name)
            if not entry:
                return
            svc, count = entry
            count -= 1
            if count <= 0:
                self._services[name] = (svc, 0)
                svc.pause()
            else:
                self._services[name] = (svc, count)
                svc.pause()

    def shutdown_all(self) -> None:
        """Terminate all managed service threads."""
        with self._lock:
            services = list(self._services.values())
            self._services.clear()
        for svc, _ in services:
            svc.stop_thread()


manager = ServiceManager()

__all__ = ["PausableService", "ServiceManager", "manager"]
