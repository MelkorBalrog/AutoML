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

"""Detachable tab window behavioural tests."""

import os
import tkinter as tk
from tkinter import ttk

import pytest

from gui.utils.closable_notebook import ClosableNotebook
from gui.utils.detachable_tab_window import DetachableTabWindow, DetachedTabMetadata
from gui.utils.dockable_diagram_window import DockableDiagramWindow


@pytest.mark.detached_tab
@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
class TestDetachableTabWindow:
    """Grouped tests for detach/dock lifecycle."""

    def _build_tab(self, root: tk.Misc):
        nb = ClosableNotebook(root)
        frame = ttk.Frame(nb)
        dock = DockableDiagramWindow(frame)
        frame._dock_window = dock
        dock.dock(nb, 0, "Detached")
        return nb, frame

    def test_detach_and_dock_restores_parent(self):
        root = tk.Tk()
        nb, frame = self._build_tab(root)
        metadata = DetachedTabMetadata(title="Detached", diagram_id="d1", index=0)
        wrapper = DetachableTabWindow(root, frame, nb, metadata)

        wrapper.detach()
        assert frame.master is not nb
        assert nb.tabs() == []

        wrapper.dock_back()
        assert frame.master is nb
        assert nb.tabs()
        root.destroy()

    def test_metadata_preserved_on_detach(self):
        root = tk.Tk()
        nb, frame = self._build_tab(root)
        metadata = DetachedTabMetadata(title="My Tab", diagram_id="diag-123", index=0)
        wrapper = DetachableTabWindow(root, frame, nb, metadata)

        wrapper.detach()
        assert wrapper.metadata.diagram_id == "diag-123"
        assert wrapper.metadata.title == "My Tab"
        root.destroy()

    def test_resizer_tracks_notebook_and_tab(self, monkeypatch: pytest.MonkeyPatch):
        root = tk.Tk()
        nb, frame = self._build_tab(root)
        metadata = DetachedTabMetadata(title="Resizable", diagram_id="d2", index=0)

        class StubResizer:
            def __init__(self, win, primary=None):  # noqa: ANN001 - stub signature
                self.win = win
                self.primary = primary
                self.targets: list[tk.Widget] = []
                self.shutdown_called = False

            def set_primary_target(self, widget):  # noqa: ANN001 - stub signature
                self.primary = widget

            def add_target(self, widget):  # noqa: ANN001 - stub signature
                self.targets.append(widget)

            def shutdown(self):
                self.shutdown_called = True

        monkeypatch.setattr(
            "gui.utils.detachable_tab_window.WindowResizeController", StubResizer
        )

        wrapper = DetachableTabWindow(root, frame, nb, metadata)
        try:
            wrapper.detach()

            assert isinstance(wrapper._resizer, StubResizer)
            assert wrapper._resizer.primary is wrapper._notebook
            assert frame in wrapper._resizer.targets

            resizer = wrapper._resizer
            wrapper.dock_back()

            assert resizer.shutdown_called
            assert wrapper._resizer is None
        finally:
            root.destroy()
