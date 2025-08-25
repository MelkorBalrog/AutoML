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

from gui.architecture import GovernanceDiagramWindow


def test_switch_rebuilds_destroyed_frames():
    win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)

    class Frame:
        def __init__(self):
            self.destroyed = False

        def pack(self, *a, **k):
            if self.destroyed:
                raise RuntimeError("Frame destroyed")

        def pack_forget(self, *a, **k):
            pass

        def destroy(self):
            self.destroyed = True

        def winfo_exists(self):
            return not self.destroyed

    win._toolbox_frames = {"Entities": [], "Safety & AI Lifecycle": []}
    win._frame_loaders = {"Entities": Frame, "Safety & AI Lifecycle": Frame}

    win.toolbox_var = types.SimpleNamespace(get=lambda: "Entities")
    win._switch_toolbox()

    win.toolbox_var = types.SimpleNamespace(get=lambda: "Safety & AI Lifecycle")
    win._switch_toolbox()

    win.toolbox_var = types.SimpleNamespace(get=lambda: "Entities")
    win._switch_toolbox()

    frames = win._toolbox_frames["Entities"]
    assert len(frames) == 1
    assert frames[0].winfo_exists()
