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
"""Tests for ``WidgetTransferManager`` with ``DockableDiagramWindow``."""

from __future__ import annotations

import tkinter as tk
import pytest

from gui.utils.closable_notebook import ClosableNotebook
from gui.utils.widget_transfer_manager import WidgetTransferManager
from gui.utils.dockable_diagram_window import DockableDiagramWindow


@pytest.mark.detachment
class TestWidgetTransferManagerDockable:
    def test_dockable_diagram_reattaches_via_dock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb1 = ClosableNotebook(root)
        nb1.pack()
        nb2 = ClosableNotebook(root)
        nb2.pack()
        dock_win = DockableDiagramWindow(root)
        frame = tk.Frame(dock_win.content_frame)
        frame.pack()
        dock_win.content_frame._dock_window = dock_win
        dock_win.dock(nb1, 0, "Tab1")

        manager = WidgetTransferManager()
        called: dict[str, bool] = {"dock": False}

        def fake_dock(notebook: ClosableNotebook, index: int, title: str) -> None:
            called["dock"] = True
            notebook.add(dock_win.content_frame, text=title)

        monkeypatch.setattr(dock_win, "dock", fake_dock)

        def boom(*_args, **_kwargs) -> None:  # pragma: no cover - ensure not called
            raise AssertionError("reparent_widget should not be called")

        monkeypatch.setattr(
            "gui.utils.widget_transfer_manager.reparent_widget",
            boom,
        )

        tab_id = nb1.tabs()[0]
        moved = manager.detach_tab(nb1, tab_id, nb2)
        assert called["dock"]
        assert moved is dock_win.content_frame
        assert nb2.nametowidget(nb2.tabs()[0]) is dock_win.content_frame
        root.destroy()
