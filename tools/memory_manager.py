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

import gc
import importlib
from typing import Any, Callable, Dict, Set

try:  # pragma: no cover - optional dependency
    import psutil
except Exception:  # pragma: no cover - psutil may not be installed
    psutil = None


class MemoryManager:
    """Manage cached objects and subprocesses.

    Objects are loaded on demand via :meth:`lazy_load`.  Keys can be marked as
    active with :meth:`mark_active`; any remaining cached objects and processes
    are discarded by :meth:`cleanup`.
    """

    def __init__(self) -> None:
        self._cache: Dict[str, Any] = {}
        self._active: Set[str] = set()
        self._procs: Dict[str, Any] = {}

    def lazy_load(self, key: str, loader: Callable[[], Any]) -> Any:
        """Return cached object for *key*, loading it if necessary."""
        if key not in self._cache:
            self._cache[key] = loader()
        self._active.add(key)
        return self._cache[key]

    def mark_active(self, key: str) -> None:
        """Mark *key* as currently needed."""
        self._active.add(key)

    def register_process(self, key: str, proc: Any) -> None:
        """Register a subprocess keyed by *key* for later cleanup."""
        if psutil is not None and not isinstance(proc, psutil.Process):
            proc = psutil.Process(proc.pid)
        self._procs[key] = proc
        self._active.add(key)

    def cleanup(self) -> None:
        """Drop inactive cached objects and terminate unused processes."""
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
        if inactive:
            gc.collect()

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
