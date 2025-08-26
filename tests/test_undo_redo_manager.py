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

"""Unit tests for :class:`UndoRedoManager`."""

from __future__ import annotations

import types

import pytest

import mainappsrc.managers.undo_manager as um
from mainappsrc.managers.undo_manager import UndoRedoManager


class DummyApp:
    """Minimal stand-in for :class:`AutoMLApp`."""

    def __init__(self):
        self.value = 0
        self.diagram_tabs = {}

    def export_model_data(self, include_versions: bool = False):  # pragma: no cover - simple
        return {"value": self.value}

    def apply_model_data(self, state):  # pragma: no cover - simple
        self.value = state["value"]

    def refresh_all(self):  # pragma: no cover - simple
        pass


def test_push_undo_and_redo(monkeypatch):
    app = DummyApp()
    manager = UndoRedoManager(app)

    class DummyRepo:
        def push_undo_state(self, *a, **k):
            pass

        def undo(self, *a, **k):
            pass

        def redo(self, *a, **k):
            pass

    repo = DummyRepo()
    monkeypatch.setattr(um.SysMLRepository, "get_instance", lambda: repo)

    app.value = 1
    manager.push_undo_state(sync_repo=False)
    app.value = 2
    manager.push_undo_state(sync_repo=False)
    assert len(manager._undo_stack) == 2

    manager.undo()
    assert app.value == 1
    manager.redo()
    assert app.value == 2
