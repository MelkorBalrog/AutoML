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
"""Lazy model loading utilities."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Callable

from tools.memory_manager import manager as memory_manager


class LazyModelLoader:
    """Load and release model parts on demand."""

    def get(self, name: str, loader: Callable[[], Any]) -> Any:
        """Return cached model *name*, loading it if necessary."""
        return memory_manager.lazy_load(name, loader)

    def proxy(self, name: str, loader: Callable[[], Any]) -> Any:
        """Return a proxy object lazily created on first attribute access."""

        class _LazyPart:
            def __getattr__(self, item: str) -> Any:  # pragma: no cover - proxy
                obj = memory_manager.lazy_load(name, loader)
                return getattr(obj, item)

            def __call__(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover - proxy
                obj = memory_manager.lazy_load(name, loader)
                return obj(*args, **kwargs)

        return _LazyPart()

    def release(self, name: str) -> None:
        """Release cached model *name* and trigger cleanup."""
        memory_manager._active.discard(name)  # type: ignore[attr-defined]
        memory_manager.cleanup()

    @contextmanager
    def use(self, name: str, loader: Callable[[], Any]):
        """Context manager yielding a lazily loaded model part."""
        model = self.get(name, loader)
        try:
            yield model
        finally:
            self.release(name)

    def cleanup(self) -> None:
        """Trigger cleanup of all inactive model parts."""
        memory_manager.cleanup()


model_loader = LazyModelLoader()
