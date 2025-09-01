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

"""Regression tests confirming toolbox caches stay isolated per diagram."""

from __future__ import annotations

import types
from dataclasses import dataclass

from tools.memory_manager import manager as memory_manager


@dataclass
class _DummyFrame:
    """Minimal stand-in for a Tk frame preserving toolbox data."""

    elements: list[str]
    relations: list[str]

    def pack(self, *_, **__):  # pragma: no cover - no GUI side effects
        pass

    def pack_forget(self):  # pragma: no cover - no GUI side effects
        pass

    def winfo_exists(self) -> bool:  # pragma: no cover - always alive
        return True


class _DummyWindow:
    """Simplified diagram window exposing ``_switch_toolbox`` hooks."""

    def __init__(self, elements: list[str], relations: list[str]):
        self.toolbox_var = types.SimpleNamespace(get=lambda: "Rel")
        self._toolbox_frames: dict[str, list[_DummyFrame]] = {}
        self._frame_loaders = {"Rel": lambda: _DummyFrame(elements, relations)}
        self.diagram_id = "0"

    def switch(self) -> None:
        choice = self.toolbox_var.get()
        frames = self._toolbox_frames.setdefault(choice, [])
        diag_id = getattr(self, "diagram_id", "0")
        key = f"{diag_id}:{id(self)}:toolbox:{choice}"
        loader = self._frame_loaders.get(choice)
        if loader:
            frame = memory_manager.lazy_load(key, loader)
            if frame not in frames:
                frames.append(frame)
        else:
            memory_manager.mark_active(key)
        frames[:] = [f for f in frames if True]
        for frame in frames:
            if frame and hasattr(frame, "pack"):
                frame.pack()
        memory_manager.cleanup()

    def on_close(self) -> None:
        prefix = f"{self.diagram_id}:{id(self)}:toolbox:"
        memory_manager.discard_prefix(prefix)
        memory_manager.cleanup()


def _open_window(elements: list[str], relations: list[str]) -> _DummyWindow:
    win = _DummyWindow(elements, relations)
    win.switch()
    return win


class TestSequentialToolboxPersistence:
    """Grouped tests validating toolbox isolation across diagrams."""

    def test_related_elements_persist(self) -> None:
        memory_manager.cleanup()
        win1 = _open_window(["A"], ["R1"])
        frame1 = win1._toolbox_frames["Rel"][0]
        win1.on_close()
        win2 = _open_window(["B"], ["R2"])
        frame2 = win2._toolbox_frames["Rel"][0]
        assert frame1.elements == ["A"]
        assert frame2.elements == ["B"]
        win2.on_close()

    def test_relationships_persist(self) -> None:
        memory_manager.cleanup()
        win1 = _open_window(["A"], ["R1"])
        frame1 = win1._toolbox_frames["Rel"][0]
        win1.on_close()
        win2 = _open_window(["B"], ["R2"])
        frame2 = win2._toolbox_frames["Rel"][0]
        assert frame1.relations == ["R1"]
        assert frame2.relations == ["R2"]
        win2.on_close()
