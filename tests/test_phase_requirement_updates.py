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

import types
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from gui.safety_management_toolbox import SafetyManagementWindow
from gui import safety_management_toolbox as smt
from analysis.models import global_requirements


class DummyGov:
    def __init__(self, reqs):
        self._reqs = reqs

    def generate_requirements(self):
        return self._reqs


def _setup_window(monkeypatch):
    win = SafetyManagementWindow.__new__(SafetyManagementWindow)
    toolbox = types.SimpleNamespace(
        diagrams={"D": "id1", "L": "id2"},
        diagrams_for_module=lambda phase: {"D"} if phase == "Phase1" else {"L"} if phase == "GLOBAL" else set(),
        list_modules=lambda: ["Phase1", "GLOBAL"],
        module_for_diagram=lambda name: "Phase1" if name == "D" else "GLOBAL",
        list_diagrams=lambda: {"D", "L"},
    )
    win.toolbox = toolbox
    win.app = types.SimpleNamespace()
    win._display_requirements = (
        lambda *args, **kwargs: types.SimpleNamespace(
            refresh_table=lambda ids: None
        )
    )
    monkeypatch.setattr(smt.SysMLRepository, "get_instance", lambda: object())
    return win


def test_phase_requirement_updates_existing(monkeypatch):
    win = _setup_window(monkeypatch)

    # First generation with organizational type
    monkeypatch.setattr(
        smt.GovernanceDiagram,
        "from_repository",
        lambda repo, diag_id: DummyGov([("Req", "organizational")]),
    )
    global_requirements.clear()
    win.generate_phase_requirements("Phase1")
    rids = list(global_requirements.keys())
    assert len(rids) == 1
    rid1 = rids[0]
    assert global_requirements[rid1]["phase"] == "Phase1"
    assert global_requirements[rid1]["req_type"] == "organizational"
    assert global_requirements[rid1]["status"] == "draft"

    # Regenerate with a different type; old requirement becomes obsolete and a
    # new one is created
    monkeypatch.setattr(
        smt.GovernanceDiagram,
        "from_repository",
        lambda repo, diag_id: DummyGov([("Req", "product")]),
    )
    win.generate_phase_requirements("Phase1")
    assert len(global_requirements) == 2
    assert global_requirements[rid1]["status"] == "obsolete"
    new_rid = next(r for r in global_requirements if r != rid1)
    assert global_requirements[new_rid]["req_type"] == "product"
    assert global_requirements[new_rid]["status"] == "draft"


def test_phase_requirement_no_change(monkeypatch):
    win = _setup_window(monkeypatch)

    monkeypatch.setattr(
        smt.GovernanceDiagram,
        "from_repository",
        lambda repo, diag_id: DummyGov([("Req", "organizational")]),
    )
    global_requirements.clear()
    win.generate_phase_requirements("Phase1")
    rid = next(iter(global_requirements))

    # Regenerate without changes; requirement should remain and not become obsolete
    win.generate_phase_requirements("Phase1")
    assert len(global_requirements) == 1
    assert global_requirements[rid]["status"] == "draft"


def test_lifecycle_requirements_visible_in_phases(monkeypatch):
    win = _setup_window(monkeypatch)

    req_map = {
        "id1": [("Phase req", "organizational")],
        "id2": [("Life req", "organizational")],
    }

    def from_repo(_repo, diag_id):
        return DummyGov(req_map[diag_id])

    monkeypatch.setattr(smt.GovernanceDiagram, "from_repository", from_repo)

    captured = {}
    def display_stub(title, ids):
        captured.setdefault(title, ids)
        return types.SimpleNamespace(refresh_table=lambda ids: None)
    win._display_requirements = display_stub

    global_requirements.clear()
    # Generate lifecycle requirement
    win.generate_lifecycle_requirements()
    life_rid = next(iter(global_requirements))
    assert global_requirements[life_rid]["phase"] is None

    # Generate phase requirements; lifecycle requirement should be included
    win.generate_phase_requirements("Phase1")
    ids = captured.get("Phase1 Requirements", [])
    assert life_rid in ids


def test_delete_obsolete(monkeypatch):
    win = _setup_window(monkeypatch)
    global_requirements.clear()
    global_requirements.update(
        {
            "obs": {"status": "obsolete"},
            "keep": {"status": "draft"},
        }
    )

    shown = []

    def _info(*args, **kwargs):
        shown.append(args)

    monkeypatch.setattr(smt, "messagebox", types.SimpleNamespace(showinfo=_info))

    win.delete_obsolete_requirements()
    assert "obs" not in global_requirements
    assert "keep" in global_requirements
    assert shown  # ensure message displayed


def test_lifecycle_tab_refresh(monkeypatch):
    win = _setup_window(monkeypatch)
    monkeypatch.setattr(
        smt.GovernanceDiagram,
        "from_repository",
        lambda repo, diag_id: DummyGov([("Req", "organizational")]),
    )

    frames: list[types.SimpleNamespace] = []

    def display_stub(title, ids):
        frame = types.SimpleNamespace()

        def refresh_table(ids_list):
            frame.ids = list(ids_list)

        frame.refresh_table = refresh_table
        frame.refresh_table(ids)
        frames.append(frame)
        return frame

    win._display_requirements = display_stub

    global_requirements.clear()
    win.generate_lifecycle_requirements()
    frame = frames[0]
    assert frame.ids  # initial requirement present

    global_requirements.clear()  # simulate deletion
    frame.refresh_from_repository()
    assert not frame.ids
