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

from mainappsrc.models.gsn import GSNNode, GSNDiagram
from gui.gsn_config_window import GSNElementConfig


class DummyVar:
    def __init__(self, value=""):
        self.value = value
    def get(self):
        return self.value


class DummyText:
    def __init__(self, text=""):
        self.text = text
    def get(self, *_args, **_kwargs):
        return self.text


def _configure(node, diagram, name="", desc="", notes=""):
    cfg = GSNElementConfig.__new__(GSNElementConfig)
    cfg.node = node
    cfg.diagram = diagram
    cfg.name_var = DummyVar(name or node.user_name)
    cfg.desc_text = DummyText(desc or node.description)
    cfg.notes_text = DummyText(notes or node.manager_notes)
    cfg.destroy = lambda: None
    cfg._on_ok()


def test_goal_clone_and_original_sync():
    original = GSNNode("Orig", "Goal")
    diag = GSNDiagram(original)
    clone = original.clone()
    diag.add_node(clone)

    _configure(clone, diag, name="Updated", desc="Desc", notes="Note")
    assert original.user_name == "Updated"
    assert original.description == "Desc"
    assert clone.user_name == "Updated"
    assert clone.description == "Desc"
    assert clone.manager_notes == "Note"
    assert original.is_primary_instance
    assert not clone.is_primary_instance

    _configure(original, diag, name="New", desc="NewDesc", notes="NewNote")
    assert clone.user_name == "New"
    assert clone.description == "NewDesc"
    assert clone.manager_notes == "NewNote"
