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

from AutoML import AutoMLApp
from mainappsrc.managers.diagram_clipboard_manager import DiagramClipboardManager
from gui.architecture import SysMLObject, ARCH_WINDOWS, _get_next_id
from tests.test_cross_diagram_clipboard import DummyRepo, make_window


def test_cut_paste_task_between_governance_diagrams():
    ARCH_WINDOWS.clear()
    app = AutoMLApp.__new__(AutoMLApp)
    app.diagram_clipboard = DiagramClipboardManager(app)
    app.diagram_clipboard.diagram_clipboard = None
    app.diagram_clipboard.diagram_clipboard_type = None
    app.selected_node = None
    app.root_node = None
    app.diagram_clipboard.clipboard_node = None
    app.diagram_clipboard.cut_mode = False
    repo = DummyRepo("Governance Diagram", "Governance Diagram")

    boundary1 = SysMLObject(
        obj_id=_get_next_id(),
        obj_type="System Boundary",
        x=0,
        y=0,
        element_id=None,
        width=80,
        height=40,
        properties={"name": "Area1"},
        requirements=[],
        locked=False,
        hidden=False,
        collapsed={},
    )
    task = SysMLObject(
        obj_id=_get_next_id(),
        obj_type="Task",
        x=10,
        y=10,
        element_id=None,
        width=80,
        height=40,
        properties={"boundary": str(boundary1.obj_id)},
        requirements=[],
        locked=False,
        hidden=False,
        collapsed={},
    )

    win1 = make_window(app, repo, 1)
    win1.objects = [boundary1, task]
    win1.selected_obj = task

    boundary2 = SysMLObject(
        obj_id=_get_next_id(),
        obj_type="System Boundary",
        x=0,
        y=0,
        element_id=None,
        width=80,
        height=40,
        properties={"name": "Area2"},
        requirements=[],
        locked=False,
        hidden=False,
        collapsed={},
    )
    win2 = make_window(app, repo, 2)
    win2.objects = [boundary2]

    win1._on_focus_in()
    win1.copy_selected()
    assert app.diagram_clipboard.diagram_clipboard is not None
    win1.objects.remove(task)
    app.diagram_clipboard.cut_mode = True

    win2._on_focus_in()
    app.paste_node()

    assert any(o.obj_type == "Task" for o in win2.objects)
    assert sum(1 for o in win2.objects if o.obj_type == "System Boundary") == 2
