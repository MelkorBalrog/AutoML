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
import unittest
from unittest import mock

from mainappsrc.models.sysml.sysml_repository import SysMLRepository
from gui.architecture import ArchitectureManagerDialog, GovernanceDiagramWindow


class GovernanceActionsTests(unittest.TestCase):
    def setUp(self):
        SysMLRepository._instance = None
        self.repo = SysMLRepository.get_instance()

    def test_drop_creates_action(self):
        src = self.repo.create_diagram("Governance Diagram", name="Src")
        target = self.repo.create_diagram("Governance Diagram", name="Tgt")
        explorer = ArchitectureManagerDialog.__new__(ArchitectureManagerDialog)
        explorer.repo = self.repo
        with mock.patch("gui.controls.messagebox.showerror"):
            explorer._drop_on_diagram(f"diag_{src.diag_id}", target)
        obj = target.objects[0]
        elem = self.repo.elements[obj["element_id"]]
        self.assertEqual(obj["obj_type"], "Action")
        self.assertEqual(elem.elem_type, "Action")
        self.assertEqual(self.repo.get_linked_diagram(elem.elem_id), src.diag_id)

    def test_toolbox_creates_action(self):
        diag = self.repo.create_diagram("Governance Diagram")
        win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
        win.repo = self.repo
        win.diagram_id = diag.diag_id
        win.zoom = 1.0
        win.current_tool = "Action"
        win.objects = []
        win.connections = []
        win.selected_obj = None
        win.selected_objs = []
        win.selected_conn = None
        win.dragging_point_index = None
        win.dragging_endpoint = None
        win.start = None
        win.temp_line_end = None
        win.find_object = lambda *args, **kwargs: None
        win.ensure_text_fits = lambda obj: None
        win.sort_objects = lambda: None
        win._sync_to_repository = lambda: None
        win.redraw = lambda: None
        win.update_property_view = lambda: None
        win.canvas = types.SimpleNamespace(
            canvasx=lambda v: v, canvasy=lambda v: v, configure=lambda **kw: None
        )
        event = types.SimpleNamespace(x=10, y=10)
        GovernanceDiagramWindow.on_left_press(win, event)
        obj = win.objects[0]
        elem = self.repo.elements[obj.element_id]
        self.assertEqual(obj.obj_type, "Action")
        self.assertEqual(elem.elem_type, "Action")


if __name__ == "__main__":
    unittest.main()
