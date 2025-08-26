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

from gui.architecture import GovernanceDiagramWindow, SysMLObject
from mainappsrc.models.sysml.sysml_repository import SysMLRepository


def test_work_product_combo_filters_process_area(monkeypatch):
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

    captured = []

    class DummyDialog:
        def __init__(self, parent, title, options):
            captured.append(options)
            self.selection = ""

    monkeypatch.setattr(GovernanceDiagramWindow, "_SelectDialog", DummyDialog)

    # Without process area, FI2TC should not be listed
    win.add_work_product()
    assert "FI2TC" not in captured[-1]

    # Add required process area and try again
    area = SysMLObject(1, "System Boundary", 0, 0, properties={"name": "Hazard & Threat Analysis"})
    win.objects.append(area)
    win.add_work_product()
    assert "FI2TC" in captured[-1]
