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

from gui.safety_management_toolbox import SafetyManagementWindow, SafetyManagementToolbox
from mainappsrc.models.sysml.sysml_repository import SysMLRepository
from gui import safety_management_toolbox as smt
from analysis.models import global_requirements


def test_ai_elements_generate_ai_safety_requirements(monkeypatch):
    repo = SysMLRepository.reset_instance()
    diag = repo.create_diagram("Governance Diagram", name="AI Gov")
    e1 = repo.create_element("Block", name="DB")
    e2 = repo.create_element("Block", name="NN")
    diag.objects = [
        {"obj_id": 1, "obj_type": "AI Database", "x": 0, "y": 0, "element_id": e1.elem_id, "properties": {"name": "DB"}},
        {"obj_id": 2, "obj_type": "ANN", "x": 100, "y": 0, "element_id": e2.elem_id, "properties": {"name": "NN"}},
    ]
    diag.connections = [
        {"src": 1, "dst": 2, "conn_type": "AI training", "name": "", "properties": {}}
    ]

    toolbox = SafetyManagementToolbox()
    toolbox.diagrams["AI Gov"] = diag.diag_id

    class DummyTab:
        def __init__(self):
            self.children = []

        def winfo_children(self):
            return list(self.children)

    tabs = []

    def _new_tab(title):
        tab = DummyTab()
        tabs.append((title, tab))
        return tab

    trees = []

    class DummyFrame:
        def __init__(self, master):
            self.master = master
            self.children = []
            master.children.append(self)

        def winfo_children(self):
            return list(self.children)

        def rowconfigure(self, *args, **kwargs):
            pass

        def columnconfigure(self, *args, **kwargs):
            pass

        def pack(self, **kwargs):
            pass

        def destroy(self):
            self.master.children.remove(self)

    class DummyScrollbar:
        def __init__(self, master, orient=None, command=None):
            self.master = master
            master.children.append(self)

        def grid(self, *args, **kwargs):
            pass

        def set(self, *args):
            pass

        def destroy(self):
            self.master.children.remove(self)

    class DummyTree:
        def __init__(self, master, columns, show="headings"):
            self.rows = []
            trees.append(self)
            master.children.append(self)

        def heading(self, col, text=""):
            pass

        def insert(self, parent, idx, values):
            self.rows.append(values)

        def configure(self, **kwargs):
            pass

        def yview(self, *args):
            pass

        def xview(self, *args):
            pass

        def grid(self, *args, **kwargs):
            pass

        def get_children(self):
            return list(range(len(self.rows)))

        def delete(self, *items):
            self.rows = []

    monkeypatch.setattr(smt.ttk, "Frame", DummyFrame)
    monkeypatch.setattr(smt.ttk, "Scrollbar", DummyScrollbar)
    monkeypatch.setattr(smt.ttk, "Treeview", DummyTree)

    win = SafetyManagementWindow.__new__(SafetyManagementWindow)
    win.toolbox = toolbox
    win.app = types.SimpleNamespace(_new_tab=_new_tab)
    win.diag_var = types.SimpleNamespace(get=lambda: "AI Gov")

    global_requirements.clear()
    win.generate_requirements()

    assert tabs
    assert trees and trees[0].rows
    assert all(row[1] == "AI safety" for row in trees[0].rows)
