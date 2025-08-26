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

import json
import types
from pathlib import Path

from gui import architecture


def test_governance_task_rule_allows_action(tmp_path, monkeypatch):
    cfg = {
        "connection_rules": {
            "Governance Diagram": {"Produces": {"Task": ["Work Product"]}}
        }
    }
    path = tmp_path / "diagram_rules.json"
    path.write_text(json.dumps(cfg))
    orig_path = architecture._CONFIG_PATH
    monkeypatch.setattr(architecture, "_CONFIG_PATH", path)
    architecture.reload_config()
    win = architecture.GovernanceDiagramWindow.__new__(architecture.GovernanceDiagramWindow)
    win.repo = types.SimpleNamespace(diagrams={})
    win.diagram_id = "d"
    win.repo.diagrams["d"] = types.SimpleNamespace(diag_type="Governance Diagram")
    src = architecture.SysMLObject(1, "Action", 0, 0)
    dst = architecture.SysMLObject(2, "Work Product", 0, 0)
    valid, _ = architecture.GovernanceDiagramWindow.validate_connection(win, src, dst, "Produces")
    assert valid
    monkeypatch.setattr(architecture, "_CONFIG_PATH", orig_path)
    architecture.reload_config()
