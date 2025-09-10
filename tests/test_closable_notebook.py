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

"""Tests for the :mod:`gui.utils.closable_notebook` module."""

import os
import tkinter as tk

import pytest

from gui.utils.closable_notebook import ClosableNotebook
from gui.utils.dockable_diagram_window import DockableDiagramWindow
from tkinter import ttk


@pytest.mark.closable_notebook
class TestCancelAfterEvents:
    @pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
    def test_cancel_after_events_cancels_widget_after(self) -> None:
        root = tk.Tk()
        root.withdraw()
        btn = tk.Button(root)
        ident = btn.after(1000000, lambda: None)
        nb = ClosableNotebook(root)
        nb._cancel_after_events(btn)
        assert ident not in btn.tk.call("after", "info", str(btn))
        root.destroy()


@pytest.mark.closable_notebook
class TestCanvasWindows:
    @pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
    def test_update_canvas_windows(self) -> None:
        root = tk.Tk()
        root.withdraw()
        nb = ClosableNotebook(root)
        canvas = tk.Canvas(nb)
        frame = tk.Frame(canvas)
        lst = tk.Listbox(frame)
        lst.insert("end", "item")
        lst.pack()
        canvas.create_window(0, 0, window=frame, anchor="nw")
        clone, mapping, layouts = nb._clone_widget(canvas, nb)
        nb.update_canvas_windows(mapping)
        item = clone.find_all()[0]
        win_path = clone.itemcget(item, "window")
        assert win_path
        clone_win = clone.nametowidget(win_path)
        assert isinstance(clone_win, tk.Frame)
        root.destroy()


@pytest.mark.detached_tab
@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
class TestDetachedTab:
    """Detached tab regression tests."""

    def test_detached_tab_has_single_toolbox_and_diagram(self):
        root = tk.Tk()
        nb = ClosableNotebook(root)
        frame = ttk.Frame(nb)
        ttk.Frame(frame, name="toolbox").pack(side="left")
        tk.Canvas(frame, name="diagram").pack(side="right")
        nb.add(frame, text="Tab1")
        nb.update_idletasks()

        class Event: ...

        press = Event(); press.x = 5; press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True
        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)

        win = nb._floating_windows[0]
        new_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        new_frame = new_nb.nametowidget(new_nb.tabs()[0])
        toolboxes = [w for w in new_frame.winfo_children() if w.winfo_name() == "toolbox"]
        diagrams = [w for w in new_frame.winfo_children() if w.winfo_name() == "diagram"]
        assert len(toolboxes) == 1
        assert len(diagrams) == 1
        root.destroy()

    def test_dock_window_detach_passes_title(self):
        root = tk.Tk()
        nb = ClosableNotebook(root)
        frame = ttk.Frame(nb)

        class SpyDock(DockableDiagramWindow):
            def __init__(self, content):
                super().__init__(content)
                self.args = None

            def float(self, width, height, x, y, title):
                self.args = (width, height, x, y, title)
                super().float(width, height, x, y, title)

        dock = SpyDock(frame)
        frame._dock_window = dock
        nb.add(frame, text="Docked")
        tab_id = nb.tabs()[0]
        nb._detach_tab(tab_id, 5, 5)
        assert dock.args[-1] == "Docked"
        for w in list(nb._floating_windows):
            w.destroy()
        root.destroy()

    def test_detach_forgets_tab_before_float(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = tk.Tk()
        nb = ClosableNotebook(root)
        frame = ttk.Frame(nb)
        dock = DockableDiagramWindow(frame)
        frame._dock_window = dock
        nb.add(frame, text="Docked")
        tab_id = nb.tabs()[0]

        called = {"float": False}

        def spy_float(width, height, x, y, title):  # noqa: ANN001 - test helper
            # Tab should be removed from the original notebook before floating
            assert tab_id not in nb.tabs()
            called["float"] = True

        monkeypatch.setattr(dock, "float", spy_float)
        nb._detach_tab(tab_id, 5, 5)
        assert called["float"]
        for w in list(nb._floating_windows):
            w.destroy()
        root.destroy()
