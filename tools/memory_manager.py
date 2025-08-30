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

from __future__ import annotations

"""Simple memory management utilities for lazy loading and process cleanup.

The :class:`MemoryManager` centralizes lazy loading of modules or data and
tracks subprocesses so idle ones can be terminated.  It provides a minimal
framework for the tool to only keep resources required for the currently
visible data.
"""

import atexit
import ctypes
import gc
import importlib
import sys
import threading
import time
from typing import Any, Callable, Dict, Set

from .thread_manager import manager as thread_manager

try:  # pragma: no cover - optional dependency
    import psutil
except Exception:  # pragma: no cover - psutil may not be installed
    psutil = None


class MemoryManager:
    """Manage cached objects, subprocesses and trim process memory.

    Objects are loaded on demand via :meth:`lazy_load`.  Keys can be marked as
    active with :meth:`mark_active`; any remaining cached objects and processes
    are discarded by :meth:`cleanup`.  A background thread periodically checks
    memory pressure and invokes :meth:`cleanup` to free unused resources.
    """

    def __init__(self, interval: float = 60.0, max_usage_percent: float = 70.0) -> None:
        self._cache: Dict[str, Any] = {}
        self._active: Set[str] = set()
        self._procs: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._interval = interval
        self._max_usage = max_usage_percent
        self._stop_event = threading.Event()
        self._thread = thread_manager.register("memory_manager", self._monitor, daemon=True)

    def lazy_load(self, key: str, loader: Callable[[], Any]) -> Any:
        """Return cached object for *key*, loading it if necessary."""
        with self._lock:
            if key not in self._cache:
                self._cache[key] = loader()
            self._active.add(key)
            return self._cache[key]

    def mark_active(self, key: str) -> None:
        """Mark *key* as currently needed."""
        with self._lock:
            self._active.add(key)

    def register_process(self, key: str, proc: Any) -> None:
        """Register a subprocess keyed by *key* for later cleanup."""
        if psutil is not None and not isinstance(proc, psutil.Process):
            proc = psutil.Process(proc.pid)
        with self._lock:
            self._procs[key] = proc
            self._active.add(key)

    def discard_prefix(self, prefix: str) -> None:
        """Remove cached entries and processes starting with *prefix*."""
        with self._lock:
            keys = [k for k in self._cache if k.startswith(prefix)]
            for key in keys:
                obj = self._cache.pop(key, None)
                if obj is not None:
                    destroy = getattr(obj, "destroy", None)
                    if callable(destroy):
                        try:
                            destroy()
                        except Exception:
                            pass
                    del obj
            proc_keys = [k for k in self._procs if k.startswith(prefix)]
            for key in proc_keys:
                proc = self._procs.pop(key, None)
                if proc is not None:
                    try:
                        if psutil is not None:
                            if proc.is_running():
                                proc.terminate()
                                proc.wait(timeout=1)
                        else:
                            proc.terminate()
                            proc.wait(1)
                    except Exception:
                        pass
            self._active = {k for k in self._active if not k.startswith(prefix)}
        self._trim_memory()

    def cleanup(self) -> None:
        """Drop inactive cached objects and terminate unused processes."""
        with self._lock:
            inactive = set(self._cache) - self._active
            for key in inactive:
                obj = self._cache.pop(key, None)
                if obj is not None:
                    destroy = getattr(obj, "destroy", None)
                    if callable(destroy):
                        try:
                            destroy()
                        except Exception:  # pragma: no cover - best effort cleanup
                            pass
                    del obj

            for key, proc in list(self._procs.items()):
                if key not in self._active:
                    try:
                        if psutil is not None:
                            if proc.is_running():
                                proc.terminate()
                                proc.wait(timeout=1)
                        else:
                            proc.terminate()
                            proc.wait(1)
                    except Exception:
                        pass
                    finally:
                        self._procs.pop(key, None)
            self._active.clear()
        self._trim_memory()

    def _memory_percent(self) -> float:
        if psutil is not None:
            try:
                return psutil.Process().memory_percent()
            except Exception:  # pragma: no cover - best effort
                return 0.0
        return 0.0

    def _trim_memory(self) -> None:
        gc.collect()
        if sys.platform.startswith("linux"):
            try:
                ctypes.CDLL("libc.so.6").malloc_trim(0)
            except Exception:  # pragma: no cover - optional
                pass

    def _monitor(self) -> None:
        """Background thread monitoring memory usage."""
        while not self._stop_event.is_set():
            time.sleep(self._interval)
            if self._memory_percent() > self._max_usage:
                self.cleanup()

    def shutdown(self) -> None:
        """Stop the monitoring thread."""
        self._stop_event.set()
        thread = thread_manager.unregister("memory_manager")
        if thread and thread.is_alive():
            thread.join(timeout=1)


def lazy_import(name: str) -> Any:
    """Return a proxy module lazily imported on first attribute access."""

    class _LazyModule:
        def __getattr__(self, item: str) -> Any:  # pragma: no cover - proxy
            module = manager.lazy_load(name, lambda: importlib.import_module(name))
            return getattr(module, item)

    return _LazyModule()


def lazy_widget(key: str, loader: Callable[[], Any]) -> Any:
    """Lazily create a GUI widget using the shared memory manager."""
    return manager.lazy_load(key, loader)


manager = MemoryManager()
atexit.register(manager.shutdown)
