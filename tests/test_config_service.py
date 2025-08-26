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
from pathlib import Path

import importlib

cs_module = importlib.import_module("mainappsrc.services.config.config_service")


def test_reload_local_config_updates_gate_types(tmp_path, monkeypatch):
    cfg_path = tmp_path / "diagram_rules.json"
    cfg_path.write_text(json.dumps({"gate_node_types": ["NEW_GATE"]}))
    monkeypatch.setattr(cs_module.config_service, "config_path", cfg_path)

    called = {"val": False}

    def fake_regen(*args, **kwargs):
        called["val"] = True

    monkeypatch.setattr(cs_module, "regenerate_requirement_patterns", fake_regen)
    cs_module.config_service.reload_local_config()
    assert cs_module.config_service.gate_node_types == {"NEW_GATE"}
    assert called["val"]


def test_unique_id_generation():
    helper = cs_module.config_service.automl_helper
    helper.unique_node_id_counter = 1
    first = helper.get_next_unique_id()
    second = helper.get_next_unique_id()
    assert (first, second) == (1, 2)
    assert helper.unique_node_id_counter == 3
