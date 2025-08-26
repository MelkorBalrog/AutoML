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

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from gui.architecture import GovernanceDiagramWindow
from analysis import SafetyManagementToolbox
from mainappsrc.models.sysml.sysml_repository import SysMLRepository
import pytest
import types


def test_add_generic_work_product(monkeypatch):
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    diag = repo.create_diagram("Governance Diagram", name="Gov1")
    diag.tags.append("safety-management")

    from analysis import safety_management as _sm
    prev_tb = _sm.ACTIVE_TOOLBOX
    toolbox = SafetyManagementToolbox()

    win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
    win.repo = repo
    win.diagram_id = diag.diag_id
    win.objects = []
    win.connections = []
    win.zoom = 1.0
    win.sort_objects = lambda: None
    win._sync_to_repository = lambda: None
    win.redraw = lambda: None

    enable_calls = []

    class DummyApp:
        safety_mgmt_toolbox = toolbox

        def enable_work_product(self, name, *, refresh=True):
            enable_calls.append(name)

    win.app = DummyApp()

    monkeypatch.setattr("gui.architecture.simpledialog.askstring", lambda *a, **k: "Custom WP")

    win.add_generic_work_product()

    assert enable_calls == ["Custom WP"]
    obj = next(
        o
        for o in win.objects
        if o.obj_type == "Work Product" and o.properties.get("name") == "Custom WP"
    )
    assert obj.properties.get("name_locked") != "1"
    assert any(wp.analysis == "Custom WP" for wp in toolbox.work_products)

    _sm.ACTIVE_TOOLBOX = prev_tb


def test_add_generic_work_product_name_conflict(monkeypatch):
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    diag = repo.create_diagram("Governance Diagram", name="Gov1")
    diag.tags.append("safety-management")

    from analysis import safety_management as _sm
    prev_tb = _sm.ACTIVE_TOOLBOX
    toolbox = SafetyManagementToolbox()

    win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
    win.repo = repo
    win.diagram_id = diag.diag_id
    win.objects = []
    win.connections = []
    win.zoom = 1.0
    win.sort_objects = lambda: None
    win._sync_to_repository = lambda: None
    win.redraw = lambda: None

    enable_calls = []
    errors = []

    class DummyApp:
        safety_mgmt_toolbox = toolbox
        WORK_PRODUCT_INFO = {"FMEA": ("Safety Analysis", "", "")}

        def enable_work_product(self, name, *, refresh=True):
            enable_calls.append(name)

    win.app = DummyApp()

    monkeypatch.setattr("gui.architecture.simpledialog.askstring", lambda *a, **k: "FMEA")
    monkeypatch.setattr("gui.architecture.messagebox.showerror", lambda *a, **k: errors.append(a))

    win.add_generic_work_product()

    assert enable_calls == []
    assert not any(o.obj_type == "Work Product" for o in win.objects)
    assert errors

    _sm.ACTIVE_TOOLBOX = prev_tb


def test_connection_creates_generic_work_product(monkeypatch):
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    diag = repo.create_diagram("Governance Diagram", name="Gov1")

    win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
    win.repo = repo
    win.diagram_id = diag.diag_id
    win.objects = []
    win.connections = []
    win.zoom = 1.0
    win.sort_objects = lambda: None
    win._sync_to_repository = lambda: None
    win.redraw = lambda: None
    win.app = types.SimpleNamespace(
        WORK_PRODUCT_INFO={},
        enable_work_product=lambda *a, **k: None,
        refresh_tool_enablement=lambda: None,
        safety_mgmt_toolbox=None,
    )

    src = win._place_work_product("Requirement Specification", 0.0, 0.0)

    connected = []
    win._connect_objects = lambda s, d, c: connected.append((s, d, c))

    monkeypatch.setattr(
        "gui.architecture.simpledialog.askstring", lambda *a, **k: "Custom WP"
    )

    win._create_obj_and_conn(src, 100.0, 100.0, "Derived from", "Document")

    obj = next(
        o for o in win.objects if o.obj_type == "Work Product" and o.properties.get("name") == "Custom WP"
    )
    assert obj.properties.get("name_locked") != "1"
    assert connected and connected[0][2] == "Derived from"
