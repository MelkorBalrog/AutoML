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

"""Tests for double-click behaviour in SafetyManagementExplorer."""

from __future__ import annotations

import sys
from pathlib import Path
import types

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))
sys.path.append(str(ROOT / "tests"))

from gui.controls import messagebox
from gui.safety_management_explorer import SafetyManagementExplorer
from analysis.safety_management import SafetyManagementToolbox
from mainappsrc.models.sysml.sysml_repository import SysMLRepository


class DummyTree:
    def __init__(self, iid: str):
        self._iid = iid

    def selection(self):
        return [self._iid]


class TestSafetyManagementExplorerDoubleClick:
    def test_double_click_opens_arch_window(self, monkeypatch):
        SysMLRepository._instance = None

        class DummyToolbox(SafetyManagementToolbox):
            def __init__(self):
                super().__init__()
                self.diagrams = {}
                self.listed = False

            def list_diagrams(self):
                self.listed = True
                self.diagrams = {"Diag1": "123"}
                return self.diagrams

        toolbox = DummyToolbox()

        opened = {"id": None}

        def open_arch_window(diag_id):
            opened["id"] = diag_id

        app = types.SimpleNamespace(
            window_controllers=types.SimpleNamespace(open_arch_window=open_arch_window)
        )

        explorer = SafetyManagementExplorer.__new__(SafetyManagementExplorer)
        explorer.app = app
        explorer.toolbox = toolbox
        explorer.tree = DummyTree("iid1")
        explorer.item_map = {"iid1": ("diagram", "Diag1")}

        explorer._on_double_click(None)

        assert toolbox.listed, "diagram list not refreshed"
        assert opened["id"] == "123", "diagram not opened"

    def test_missing_diagram_shows_error(self, monkeypatch):
        SysMLRepository._instance = None

        class DummyToolbox(SafetyManagementToolbox):
            def __init__(self):
                super().__init__()
                self.diagrams = {}

            def list_diagrams(self):
                self.diagrams = {}
                return self.diagrams

        toolbox = DummyToolbox()

        opened = {"called": False}

        def open_arch_window(diag_id):
            opened["called"] = True

        app = types.SimpleNamespace(
            window_controllers=types.SimpleNamespace(open_arch_window=open_arch_window)
        )

        explorer = SafetyManagementExplorer.__new__(SafetyManagementExplorer)
        explorer.app = app
        explorer.toolbox = toolbox
        explorer.tree = DummyTree("iid1")
        explorer.item_map = {"iid1": ("diagram", "Diag1")}

        errors: list[tuple[str, str]] = []
        monkeypatch.setattr(messagebox, "showerror", lambda t, m: errors.append((t, m)))

        explorer._on_double_click(None)

        assert errors, "missing diagram error not shown"
        assert not opened["called"], "diagram unexpectedly opened"
