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

import gui.utils.config_utils as config_utils


def test_reload_local_config_updates_gate_types(tmp_path, monkeypatch):
    cfg_path = tmp_path / "diagram_rules.json"
    cfg_path.write_text(json.dumps({"gate_node_types": ["NEW_GATE"]}))
    monkeypatch.setattr(config_utils, "_CONFIG_PATH", cfg_path)

    called = {"val": False}

    def fake_regen(*args, **kwargs):
        called["val"] = True

    monkeypatch.setattr(config_utils, "regenerate_requirement_patterns", fake_regen)
    config_utils._reload_local_config()
    assert config_utils.GATE_NODE_TYPES == {"NEW_GATE"}
    assert called["val"]


def test_unique_id_generation(monkeypatch):
    config_utils.AutoML_Helper.unique_node_id_counter = 1
    first = config_utils.AutoML_Helper.get_next_unique_id()
    second = config_utils.AutoML_Helper.get_next_unique_id()
    assert (first, second) == (1, 2)
    assert config_utils.AutoML_Helper.unique_node_id_counter == 3
