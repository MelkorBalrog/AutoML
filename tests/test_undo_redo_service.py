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
"""Tests for :mod:`UndoRedoService`."""

from __future__ import annotations

import types
import sys
import importlib.util
from pathlib import Path


def _load_service(monkeypatch):
    """Load the service module with a stubbed ``mainappsrc`` package."""

    dummy_pkg = types.SimpleNamespace()
    managers_pkg = types.SimpleNamespace()
    undo_pkg = types.SimpleNamespace(UndoRedoManager=object)
    monkeypatch.setitem(sys.modules, "mainappsrc", dummy_pkg)  # type: ignore[arg-type]
    monkeypatch.setitem(sys.modules, "mainappsrc.managers", managers_pkg)  # type: ignore[arg-type]
    monkeypatch.setitem(
        sys.modules, "mainappsrc.managers.undo_manager", undo_pkg
    )  # type: ignore[arg-type]

    path = Path("mainappsrc/services/undo/undo_redo_service.py")
    spec = importlib.util.spec_from_file_location("undo_redo_service", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore[assignment]
    return module


def test_service_delegates_to_manager(monkeypatch):
    """Service should forward calls to the underlying manager."""

    calls = []

    class DummyManager:
        def __init__(self, app):
            calls.append("init")

        def push_undo_state(self):
            calls.append("push")

    module = _load_service(monkeypatch)
    monkeypatch.setattr(module, "UndoRedoManager", DummyManager)

    app = types.SimpleNamespace()
    service = module.UndoRedoService(app)
    service.push_undo_state()

    assert calls == ["init", "push"]


def test_service_init_mixin_references_service():
    """Ensure ``ServiceInitMixin`` is wired to use ``UndoRedoService``."""

    content = Path("mainappsrc/core/service_init_mixin.py").read_text()
    assert "UndoRedoService" in content


