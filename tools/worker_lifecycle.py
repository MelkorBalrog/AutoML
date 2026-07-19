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

"""Fail-fast lifecycle assertion for project-owned workers.

Production code does not register workers.  Keeping the assertion separate
provides a testable boundary that will fail if a future integration adds one.
"""

from __future__ import annotations

from typing import Protocol


class Worker(Protocol):
    """Minimal interface needed to verify a worker has terminated."""

    def is_alive(self) -> bool: ...


class ProjectWorkerRegistry:
    """Registry that rejects non-empty state at GUI destruction time."""

    def __init__(self) -> None:
        self._workers: dict[str, Worker] = {}

    @property
    def registered(self) -> tuple[str, ...]:
        return tuple(self._workers)

    def assert_stopped(self) -> None:
        alive = tuple(name for name, worker in self._workers.items() if worker.is_alive())
        assert not self._workers and not alive, (
            f"project-owned workers remain registered: {self.registered}; alive: {alive}"
        )


project_workers = ProjectWorkerRegistry()

__all__ = ["ProjectWorkerRegistry", "project_workers"]
