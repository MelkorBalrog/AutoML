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
"""Regression test for repeated clipboard operations across governance diagrams."""

import os
import sys
import types

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from AutoML import AutoMLApp
from mainappsrc.core.diagram_clipboard_manager import DiagramClipboardManager
from gui.windows.architecture import SysMLObject, ARCH_WINDOWS, _get_next_id


class MultiRepo:
    def __init__(self, *diag_types):
        self.diagrams = {
            i + 1: types.SimpleNamespace(diag_type=t, elements=[])
            for i, t in enumerate(diag_types)
        }

    def diagram_read_only(self, _id):
        return False


def make_window(app, repo, diagram_id):
    from tests.test_cross_diagram_clipboard import make_window as _make_window

    return _make_window(app, repo, diagram_id)


def _boundary(name):
    return SysMLObject(
        obj_id=_get_next_id(),
        obj_type="System Boundary",
        x=0,
        y=0,
        element_id=None,
        width=80,
        height=40,
        properties={"name": name},
        requirements=[],
        locked=False,
        hidden=False,
        collapsed={},
    )


def _task(boundary):
    return SysMLObject(
        obj_id=_get_next_id(),
        obj_type="Task",
        x=10,
        y=10,
        element_id=None,
        width=80,
        height=40,
        properties={"boundary": str(boundary.obj_id)},
        requirements=[],
        locked=False,
        hidden=False,
        collapsed={},
    )


def test_clipboard_reuse_between_multiple_governance_diagrams():
    ARCH_WINDOWS.clear()
    app = AutoMLApp.__new__(AutoMLApp)
    app.diagram_clipboard = DiagramClipboardManager(app)
    app.diagram_clipboard.diagram_clipboard = None
    app.diagram_clipboard.diagram_clipboard_type = None
    app.selected_node = None
    app.root_node = None
    app.diagram_clipboard.clipboard_node = None
    app.diagram_clipboard.cut_mode = False

    repo = MultiRepo("Governance Diagram", "Governance Diagram", "Governance Diagram")

    b1 = _boundary("Area1")
    t1 = _task(b1)
    win1 = make_window(app, repo, 1)
    win1.objects = [b1, t1]
    win1.selected_obj = t1

    b2 = _boundary("Area2")
    win2 = make_window(app, repo, 2)
    win2.objects = [b2]

    # First copy/paste
    win1._on_focus_in()
    app.copy_node()
    win2._on_focus_in()
    app.paste_node()
    assert any(o.obj_type == "Task" for o in win2.objects)

    # Second copy/paste using the new task in win2
    task_in_win2 = next(o for o in win2.objects if o.obj_type == "Task")
    win2.selected_obj = task_in_win2

    b3 = _boundary("Area3")
    win3 = make_window(app, repo, 3)
    win3.objects = [b3]

    win2._on_focus_in()
    app.copy_node()
    win3._on_focus_in()
    app.paste_node()

    assert any(o.obj_type == "Task" for o in win3.objects)
