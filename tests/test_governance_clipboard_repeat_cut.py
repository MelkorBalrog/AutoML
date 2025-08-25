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
"""Test cut then paste between multiple governance diagrams."""

import os
import sys
import types

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from AutoML import AutoMLApp
from mainappsrc.core.diagram_clipboard_manager import DiagramClipboardManager
from gui.windows.architecture import SysMLObject, ARCH_WINDOWS, _get_next_id

from tests.test_governance_clipboard_repeat import MultiRepo, make_window, _boundary, _task


def test_copy_then_cut_between_governance_diagrams():
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

    win1._on_focus_in()
    app.copy_node()
    win2._on_focus_in()
    app.paste_node()

    # Now cut the task from win2 and paste into win3
    task2 = next(o for o in win2.objects if o.obj_type == "Task")
    win2.selected_obj = task2
    win2._on_focus_in()
    app.cut_node()

    b3 = _boundary("Area3")
    win3 = make_window(app, repo, 3)
    win3.objects = [b3]

    win3._on_focus_in()
    app.paste_node()

    assert any(o.obj_type == "Task" for o in win3.objects)
    assert all(o.obj_type != "Task" for o in win2.objects)
