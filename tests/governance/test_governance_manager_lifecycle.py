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

"""Tests for :class:`GovernanceManager` lifecycle propagation."""

from types import SimpleNamespace

from AutoML import AutoMLApp
from mainappsrc.managers.governance_manager import GovernanceManager


def test_app_delegates_phase_to_manager():
    app = AutoMLApp.__new__(AutoMLApp)
    app.lifecycle_var = SimpleNamespace(get=lambda: "PhaseA")
    captured = {}

    def fake_on_lifecycle_selected(phase):
        captured["phase"] = phase

    app.governance_manager = SimpleNamespace(on_lifecycle_selected=fake_on_lifecycle_selected)
    AutoMLApp.on_lifecycle_selected(app)
    assert captured["phase"] == "PhaseA"


def test_manager_refreshes_views_and_children():
    calls = {"update": 0, "child": 0, "refresh": 0, "phase": None}

    class DummyChild:
        def refresh_from_repository(self):
            calls["child"] += 1

        def winfo_children(self):
            return []

    app = SimpleNamespace(
        active_phase_lbl=SimpleNamespace(config=lambda **_: None),
        lifecycle_var=SimpleNamespace(set=lambda val: None),
        update_views=lambda: calls.__setitem__("update", calls["update"] + 1),
        diagram_tabs={"tab": DummyChild()},
    )
    gm = GovernanceManager(app)
    gm.refresh_tool_enablement = lambda: calls.__setitem__("refresh", calls["refresh"] + 1)

    gm.on_lifecycle_selected("P1")
    assert calls == {"update": 1, "child": 1, "refresh": 1, "phase": None}
