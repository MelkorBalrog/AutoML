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
from mainappsrc.models.sysml.sysml_repository import SysMLRepository


def test_safety_management_process_area_available(monkeypatch):
    repo = SysMLRepository.reset_instance()
    diag = repo.create_diagram("Governance Diagram", name="Gov1")
    diag.tags.append("safety-management")

    win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
    win.repo = repo
    win.diagram_id = diag.diag_id
    win.objects = []
    win.connections = []
    win.zoom = 1.0
    win.sort_objects = lambda: None
    win._sync_to_repository = lambda: None
    win.redraw = lambda: None

    captured = {}

    class DummyDialog:
        def __init__(self, parent, title, options):
            captured["options"] = options
            self.selection = ""

    monkeypatch.setattr(GovernanceDiagramWindow, "_SelectDialog", DummyDialog)

    win.add_work_product()

    assert "Safety & Security Management" in captured["options"]
    assert len(captured["options"]) == len(set(captured["options"]))
