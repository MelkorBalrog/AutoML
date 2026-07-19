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

"""Event-driven and passive diagnostics for monitoring tool integrity.

This module provides several experimental diagnostics manager
implementations.  Each variant offers a different strategy for detecting
integrity issues in running operations.  The intent is to evaluate which
approach best fits the tool before wider integration.

The following managers are available:

* :class:`EventDiagnosticsManager` -- collects explicit success/failure
  events from the application.
* :class:`PassiveDiagnosticsManager` -- exposes a simple ``run_check``
  method for ad-hoc validation.
* :class:`AsyncDiagnosticsManager` -- awaits registered asynchronous
  check coroutines.

Each manager attempts recovery and mitigation to correct detected
issues at runtime.  If neither strategy succeeds, a
:class:`DiagnosticError` is raised so callers can react to the
unhandled fault.
"""

from dataclasses import dataclass, field
import asyncio
from collections import deque

from typing import Awaitable, Callable, Dict, List, Optional, Tuple


class DiagnosticError(RuntimeError):
    """Raised when a diagnostics check reports failure."""


@dataclass
class DiagnosticsManagerBase:
    """Common interface for diagnostics managers."""

    errors: List[str] = field(default_factory=list)
    notifications: List[str] = field(default_factory=list)

    def _handle_failure(
        self,
        name: str,
        recoverable: bool,
        recover: Optional[Callable[[], bool]] = None,
        mitigate: Optional[Callable[[], Optional[str]]] = None,
    ) -> None:
        """Attempt recovery or mitigation for a failed check."""
        if self._attempt_recover(name, recoverable, recover):
            return
        if self._attempt_mitigate(name, mitigate):
            return
        self.errors.append(name)

    def _attempt_recover(
        self,
        name: str,
        recoverable: bool,
        recover: Optional[Callable[[], bool]],
    ) -> bool:
        if recoverable and recover:
            try:
                return bool(recover())
            except Exception as exc:  # pragma: no cover - rare
                self.errors.append(f"{name}: recovery error: {exc}")
        return False

    def _attempt_mitigate(
        self,
        name: str,
        mitigate: Optional[Callable[[], Optional[str]]],
    ) -> bool:
        if mitigate:
            try:
                msg = mitigate()
                if msg:
                    self.notifications.append(msg)
                return True
            except Exception as exc:  # pragma: no cover - rare
                self.errors.append(f"{name}: mitigation error: {exc}")
        return False

    def raise_errors(self) -> None:
        """Raise :class:`DiagnosticError` if any errors were collected."""
        if self.errors:
            raise DiagnosticError("; ".join(self.errors))


class EventDiagnosticsManager(DiagnosticsManagerBase):
    """Collects explicit success/failure events from the application."""

    def __init__(self) -> None:
        super().__init__()
        self._events: deque[tuple[str, bool]] = deque()
        self._meta: Dict[str, Tuple[bool, Optional[Callable[[], bool]], Optional[Callable[[], Optional[str]]]]] = {}

    def register_check(
        self,
        name: str,
        *,
        recover: Optional[Callable[[], bool]] = None,
        mitigate: Optional[Callable[[], Optional[str]]] = None,
        recoverable: bool = True,
    ) -> None:
        self._meta[name] = (recoverable, recover, mitigate)

    def record_event(self, name: str, ok: bool) -> None:
        self._events.append((name, ok))

    def process_events(self) -> None:
        while self._events:
            name, ok = self._events.popleft()
            if not ok:
                recoverable, recover, mitigate = self._meta.get(name, (True, None, None))
                self._handle_failure(name, recoverable, recover, mitigate)


class PassiveDiagnosticsManager(DiagnosticsManagerBase):
    """Runs checks on demand without background activity."""

    def run_check(
        self,
        name: str,
        func: Callable[[], bool],
        *,
        recover: Optional[Callable[[], bool]] = None,
        mitigate: Optional[Callable[[], Optional[str]]] = None,
        recoverable: bool = True,
    ) -> None:
        try:
            if not func():
                self._handle_failure(name, recoverable, recover, mitigate)
        except Exception as exc:  # pragma: no cover - rare
            self.errors.append(f"{name}: {exc}")


class AsyncDiagnosticsManager(DiagnosticsManagerBase):
    """Await registered asynchronous checks."""

    def __init__(self) -> None:
        super().__init__()
        self._checks: Dict[str, Tuple[Callable[[], Awaitable[bool]], bool, Optional[Callable[[], bool]], Optional[Callable[[], Optional[str]]]]] = {}

    def register_check(
        self,
        name: str,
        coro: Callable[[], Awaitable[bool]],
        *,
        recover: Optional[Callable[[], bool]] = None,
        mitigate: Optional[Callable[[], Optional[str]]] = None,
        recoverable: bool = True,
    ) -> None:
        self._checks[name] = (coro, recoverable, recover, mitigate)

    async def run_once(self) -> None:
        for name, (coro, recoverable, recover, mitigate) in list(self._checks.items()):
            try:
                if not await coro():
                    self._handle_failure(name, recoverable, recover, mitigate)
            except Exception as exc:  # pragma: no cover - rare
                self.errors.append(f"{name}: {exc}")


__all__ = [
    "DiagnosticError",
    "DiagnosticsManagerBase",
    "EventDiagnosticsManager",
    "PassiveDiagnosticsManager",
    "AsyncDiagnosticsManager",
]
