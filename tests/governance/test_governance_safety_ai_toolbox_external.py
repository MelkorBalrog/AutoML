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
import warnings
from pathlib import Path
import sys
import types

sys.path.append(str(Path(__file__).resolve().parents[2]))
import mainappsrc  # type: ignore
import mainappsrc.ui  # type: ignore
ui_stub = types.ModuleType("mainappsrc.ui.app_lifecycle_ui")
ui_stub.AppLifecycleUI = object
sys.modules["mainappsrc.ui.app_lifecycle_ui"] = ui_stub

from gui import architecture


class TestSafetyAIToolboxExternal:
    def _write_config(self, tmp_path, cfg):
        path = tmp_path / "diagram_rules.json"
        path.write_text(json.dumps(cfg))
        return path

    def test_cross_toolbox_relations_listed(self, tmp_path, monkeypatch):
        cfg = {
            "ai_nodes": ["AI Node"],
            "governance_element_nodes": ["Task"],
            "connection_rules": {
                "Governance Diagram": {"Rel": {"AI Node": ["Task"]}}
            },
        }
        path = self._write_config(tmp_path, cfg)
        monkeypatch.setattr(architecture, "_CONFIG_PATH", path)
        architecture.reload_config()
        externals = architecture._external_relations_for(["AI Node"])
        assert externals == {"Processes": {"nodes": ["Task"], "relations": ["Rel"]}}

    def test_unmapped_relations_retained(self, tmp_path, monkeypatch):
        cfg = {
            "ai_nodes": ["AI Node"],
            "connection_rules": {
                "Governance Diagram": {"Rel": {"AI Node": ["Ghost"]}}
            },
        }
        path = self._write_config(tmp_path, cfg)
        monkeypatch.setattr(architecture, "_CONFIG_PATH", path)
        architecture.reload_config()
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            externals = architecture._external_relations_for(["AI Node"])
        assert externals == {"Unmapped": {"nodes": ["Ghost"], "relations": ["Rel"]}}
