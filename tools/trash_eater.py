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

"""Explicit resource cleanup at application lifecycle boundaries."""

from typing import Callable, Optional

try:  # pragma: no cover - psutil may not be installed
    import psutil
except Exception:  # pragma: no cover - optional dependency
    psutil = None

from .memory_manager import manager as memory_manager


class TrashEater:
    """Evaluate memory pressure and clean resources synchronously.

    Parameters
    ----------
    threshold:
        Fractional memory usage (0.0 - 1.0) beyond which cleanup is triggered.
    usage_provider:
        Optional callable returning current memory usage fraction.  Defaults to
        :func:`psutil.virtual_memory` when available.
    manager:
        Memory manager instance responsible for cleanup.
    """

    def __init__(
        self,
        threshold: float = 0.75,
        usage_provider: Optional[Callable[[], float]] = None,
        manager=memory_manager,
    ) -> None:
        self.threshold = threshold
        self.usage_provider = usage_provider or self._get_usage
        self.manager = manager

    @staticmethod
    def _get_usage() -> float:
        """Return the current memory usage as a fraction."""
        if psutil is None:
            return 0.0
        try:
            return psutil.virtual_memory().percent / 100.0
        except Exception:
            return 0.0

    def cleanup(self, *, force: bool = True) -> None:
        """Clean now, or only under pressure when ``force`` is false."""
        usage = self.usage_provider()
        if force or usage >= self.threshold:
            self.manager.cleanup()

    def check_once(self) -> None:
        """Perform one explicit memory-pressure check."""

        self.cleanup(force=False)


# Shared default instance for convenience
manager_eater = TrashEater()

__all__ = ["TrashEater", "manager_eater"]
