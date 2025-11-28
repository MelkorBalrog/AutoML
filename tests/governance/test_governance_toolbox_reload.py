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
from tools.memory_manager import manager as memory_manager


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


def _reset_memory_manager():
    memory_manager.discard_prefix("")
    memory_manager._active.clear()


class DummyToolbox:
    def __init__(self):
        self._callbacks = {}
        self._counter = 0

    def after(self, _delay, func):
        self._counter += 1
        self._callbacks[self._counter] = func
        return self._counter

    def after_cancel(self, ident):
        self._callbacks.pop(ident, None)


class DummyFrame:
    def __init__(self):
        self.destroyed = False
        self.packed = False

    def pack(self, *a, **k):
        self.packed = True

    def pack_forget(self, *a, **k):
        self.packed = False

    def destroy(self):
        self.destroyed = True

    def winfo_exists(self):
        return not self.destroyed


def _build_window(choice: str = "Governance Core"):
    _reset_memory_manager()
    win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
    win.diagram_id = "diag-cleanup"
    win.toolbox = DummyToolbox()
    win._toolbox_frames = {}
    win._frame_loaders = {choice: DummyFrame}
    win.toolbox_var = types.SimpleNamespace(get=lambda: choice)
    return win


def test_active_governance_toolbox_survives_cleanup():
    win = _build_window()
    GovernanceDiagramWindow._switch_toolbox(win)
    frame = win._toolbox_frames["Governance Core"][0]

    memory_manager.cleanup()

    assert frame in win._toolbox_frames["Governance Core"]
    assert not frame.destroyed


def test_toolbox_heartbeat_marks_active_between_cleanups():
    win = _build_window()
    GovernanceDiagramWindow._switch_toolbox(win)
    frame = win._toolbox_frames["Governance Core"][0]

    memory_manager.cleanup()

    assert win.toolbox._callbacks
    # Run the scheduled heartbeat to refresh active status
    for cb in list(win.toolbox._callbacks.values()):
        cb()

    memory_manager.cleanup()

    assert frame in win._toolbox_frames["Governance Core"]
    assert not frame.destroyed
