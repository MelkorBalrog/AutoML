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

"""Grouped regression tests for the single-thread lifecycle subsystems."""

import ast
from pathlib import Path

import pytest

from tools.crash_report_logger import SynchronousHealthReporter
from tools.diagnostics_manager import EventDiagnosticsManager
from tools.model_loader import LazyModelLoader
from tools.trash_eater import TrashEater
from tools.worker_lifecycle import ProjectWorkerRegistry


class TestStartupSubsystem:
    def test_launcher_has_no_thread_constructors(self) -> None:
        tree = ast.parse(Path("AutoML.py").read_text(encoding="utf-8"))
        imports = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
        assert "threading" not in imports
        assert "concurrent.futures" not in imports


class TestDiagnosticsSubsystem:
    def test_events_are_processed_synchronously(self) -> None:
        diagnostics = EventDiagnosticsManager()
        diagnostics.record_event("startup", False)
        diagnostics.process_events()
        assert diagnostics.errors == ["startup"]


class TestModelCleanupSubsystem:
    def test_release_triggers_explicit_cleanup(self, monkeypatch) -> None:
        import importlib

        calls = []
        module = importlib.import_module("tools.model_loader")
        monkeypatch.setattr(module.memory_manager, "cleanup", lambda: calls.append("cleanup"))
        LazyModelLoader().release("model")
        assert calls == ["cleanup"]


class TestCrashReportingSubsystem:
    def test_health_report_is_immediate(self) -> None:
        reporter = SynchronousHealthReporter()
        report = reporter.report("startup", healthy=True)
        assert report.phase == "startup"
        assert reporter.reports == [report]


class TestTrashCleanupSubsystem:
    def test_cleanup_is_explicit(self) -> None:
        class Manager:
            calls = 0
            def cleanup(self) -> None:
                self.calls += 1
        manager = Manager()
        TrashEater(manager=manager).cleanup()
        assert manager.calls == 1


class TestShutdownSubsystem:
    def test_registered_worker_blocks_root_destruction(self) -> None:
        class Worker:
            def is_alive(self) -> bool:
                return True
        registry = ProjectWorkerRegistry()
        registry._workers["unexpected"] = Worker()
        with pytest.raises(AssertionError, match="remain registered"):
            registry.assert_stopped()

    def test_empty_registry_allows_root_destruction(self) -> None:
        ProjectWorkerRegistry().assert_stopped()
