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

"""Fallback detachment tests for detachable tab windows."""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import ttk

import pytest

from gui.utils.closable_notebook import ClosableNotebook
from gui.utils.detachable_tab_window import DetachableTabWindow, DetachedTabMetadata
from gui.utils.dockable_diagram_window import DockableDiagramWindow


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
def test_transfer_fallback_moves_original_tab_when_reopen_fails(monkeypatch: pytest.MonkeyPatch):
    root = tk.Tk()
    nb = ClosableNotebook(root)
    frame = ttk.Frame(nb)
    dock = DockableDiagramWindow(frame)
    frame._dock_window = dock
    dock.dock(nb, 0, "Detached")
    metadata = DetachedTabMetadata(title="Fallback", diagram_id="d3", index=0)

    monkeypatch.setattr(
        "gui.utils.detachable_tab_window.DetachedTabReopener.reopen",
        lambda _self: None,
    )

    wrapper = DetachableTabWindow(root, frame, nb, metadata)
    try:
        wrapper.detach()
        assert wrapper._moved_tab is True
        assert frame.master is wrapper._notebook
        assert str(frame) not in nb.tabs()
        assert str(frame) in wrapper._notebook.tabs()

        wrapper.dock_back()
        assert frame.master is nb
        assert str(frame) in nb.tabs()
    finally:
        root.destroy()
