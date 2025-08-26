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

from gui.architecture import GovernanceDiagramWindow
import gui.architecture as arch


class DummyMenu:
    """Simple stand-in for tk.Menu capturing added commands."""

    def __init__(self, *a, **k):
        self.commands = []
        created_menus.append(self)

    def add_command(self, label, command):
        self.commands.append((label, command))

    def add_separator(self):
        pass

    def tk_popup(self, *a, **k):
        pass


created_menus = []


def fake_init(self, master=None, app=None, diagram_id=None, history=None):
    self.canvas = types.SimpleNamespace(canvasx=lambda v: v, canvasy=lambda v: v)
    self.find_connection = lambda x, y: None
    self.repo = types.SimpleNamespace(
        diagrams={"d": types.SimpleNamespace(diag_type="Governance Diagram")},
        get_linked_diagram=lambda eid: None,
    )
    self.diagram_id = "d"
    self.objects = [obj1, obj2, obj3]
    self.find_object = lambda x, y: obj2
    self.selected_obj = None
    self.selected_conn = None
    self.copy_selected = lambda: None
    self.cut_selected = lambda: None
    self.paste_selected = lambda: None
    self.remove_part_diagram = lambda o: None
    self.remove_part_model = lambda o: None
    self.delete_selected = lambda: None
    self.redraw = lambda: None
    self._set_diagram_father = lambda: None


obj1 = types.SimpleNamespace(
    obj_id=1, obj_type="Task", x=0, y=0, width=10, height=10, properties={}, element_id=None
)
obj2 = types.SimpleNamespace(
    obj_id=2, obj_type="Task", x=0, y=0, width=10, height=10, properties={}, element_id=None
)
obj3 = types.SimpleNamespace(
    obj_id=3, obj_type="Task", x=0, y=0, width=10, height=10, properties={}, element_id=None
)


def test_governance_context_menu_has_layer_commands(monkeypatch):
    monkeypatch.setattr(arch.tk, "Menu", DummyMenu)
    monkeypatch.setattr(arch.GovernanceDiagramWindow, "__init__", fake_init)

    win = GovernanceDiagramWindow(None, None)
    event = types.SimpleNamespace(x=0, y=0, x_root=0, y_root=0)
    win.show_context_menu(event)
    menu = created_menus[-1]
    labels = {label for label, _ in menu.commands}
    assert {"Bring to Front", "Send to Back", "Move Forward", "Move Backward"} <= labels

    cmds = {label: cmd for label, cmd in menu.commands}

    win.objects = [obj1, obj2, obj3]
    cmds["Bring to Front"]()
    assert win.objects == [obj1, obj3, obj2]

    win.objects = [obj1, obj2, obj3]
    cmds["Send to Back"]()
    assert win.objects == [obj2, obj1, obj3]

    win.objects = [obj1, obj2, obj3]
    cmds["Move Forward"]()
    assert win.objects == [obj1, obj3, obj2]

    win.objects = [obj1, obj2, obj3]
    cmds["Move Backward"]()
    assert win.objects == [obj2, obj1, obj3]
