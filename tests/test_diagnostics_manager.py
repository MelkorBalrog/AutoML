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

import asyncio
import time
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools.diagnostics_manager import (
    AsyncDiagnosticsManager,
    DiagnosticError,
    EventDiagnosticsManager,
    PassiveDiagnosticsManager,
    PollingDiagnosticsManager,
)


def test_polling_manager_rejects_callable_interval() -> None:
    with pytest.raises(TypeError):
        PollingDiagnosticsManager(interval=time.sleep)


def test_polling_manager_detects_failure() -> None:
    manager = PollingDiagnosticsManager(interval=0.01)
    manager.register_check("fail", lambda: False)
    manager.start()
    time.sleep(0.05)
    manager.stop()
    with pytest.raises(DiagnosticError):
        manager.raise_errors()


def test_event_manager_records_error() -> None:
    manager = EventDiagnosticsManager()
    manager.record_event("fail", False)
    manager.process_events()
    with pytest.raises(DiagnosticError):
        manager.raise_errors()


def test_passive_manager_runs_checks() -> None:
    manager = PassiveDiagnosticsManager()
    manager.run_check("fail", lambda: False)
    with pytest.raises(DiagnosticError):
        manager.raise_errors()


def test_async_manager_detects_failure() -> None:
    manager = AsyncDiagnosticsManager()

    async def bad() -> bool:
        return False

    manager.register_check("fail", bad)
    asyncio.run(manager.run_once())
    with pytest.raises(DiagnosticError):
        manager.raise_errors()


def test_recoverable_fault_recovers() -> None:
    manager = PassiveDiagnosticsManager()
    recovered = {"called": False}

    def check() -> bool:
        return False

    def recover() -> bool:
        recovered["called"] = True
        return True

    manager.run_check("r1", check, recover=recover, recoverable=True)
    manager.raise_errors()  # should not raise because recovered
    assert recovered["called"]


def test_nonrecoverable_fault_mitigates_and_notifies() -> None:
    manager = PassiveDiagnosticsManager()
    mitigated = {"called": False}

    def check() -> bool:
        return False

    def mitigate() -> str:
        mitigated["called"] = True
        return "degraded mode"

    manager.run_check("n1", check, mitigate=mitigate, recoverable=False)
    manager.raise_errors()  # should not raise because mitigated
    assert mitigated["called"]
    assert "degraded mode" in manager.notifications


def test_polling_failed_recovery_triggers_mitigation() -> None:
    manager = PollingDiagnosticsManager(interval=0.01)
    manager.register_check(
        "p1",
        lambda: False,
        recover=lambda: False,
        mitigate=lambda: "fallback",
        recoverable=True,
    )
    manager.start()
    time.sleep(0.05)
    manager.stop()
    manager.raise_errors()  # mitigated
    assert "fallback" in manager.notifications


def test_event_failed_recovery_triggers_mitigation() -> None:
    manager = EventDiagnosticsManager()
    manager.register_check(
        "e1",
        recover=lambda: False,
        mitigate=lambda: "fallback",
        recoverable=True,
    )
    manager.record_event("e1", False)
    manager.process_events()
    manager.raise_errors()  # mitigated
    assert "fallback" in manager.notifications


def test_passive_failed_recovery_triggers_mitigation() -> None:
    manager = PassiveDiagnosticsManager()

    def check() -> bool:
        return False

    manager.run_check(
        "s1",
        check,
        recover=lambda: False,
        mitigate=lambda: "fallback",
        recoverable=True,
    )
    manager.raise_errors()  # mitigated
    assert "fallback" in manager.notifications


def test_async_failed_recovery_triggers_mitigation() -> None:
    manager = AsyncDiagnosticsManager()

    async def bad() -> bool:
        return False

    manager.register_check(
        "a1",
        bad,
        recover=lambda: False,
        mitigate=lambda: "fallback",
        recoverable=True,
    )
    asyncio.run(manager.run_once())
    manager.raise_errors()  # mitigated
    assert "fallback" in manager.notifications
