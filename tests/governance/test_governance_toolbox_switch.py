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

import sys
from pathlib import Path
import types

sys.path.append(str(Path(__file__).resolve().parents[1]))

from gui.architecture import GovernanceDiagramWindow


def test_switch_toolbox_combines_governance_elements():
    win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)

    class Frame:
        def __init__(self):
            self.packed = False

        def pack(self, *a, **k):
            self.packed = True

        def pack_forget(self, *a, **k):
            self.packed = False

    ent_frame = Frame()
    ai_frame = Frame()
    win._toolbox_frames = {
        "Entities": [ent_frame],
        "Safety & AI Lifecycle": [ai_frame],
    }

    win.toolbox_var = types.SimpleNamespace(get=lambda: "Entities")
    GovernanceDiagramWindow._switch_toolbox(win)
    assert ent_frame.packed
    assert not ai_frame.packed

    win.toolbox_var = types.SimpleNamespace(get=lambda: "Safety & AI Lifecycle")
    GovernanceDiagramWindow._switch_toolbox(win)
    assert ai_frame.packed
    assert not ent_frame.packed

