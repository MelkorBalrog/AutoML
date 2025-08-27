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

import pytest
import tkinter as tk
from tkinter import ttk

from gui.utils.closable_notebook import ClosableNotebook


class TestDragMoves:
    def test_drag_tab_between_notebooks(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb1 = ClosableNotebook(root)
        nb2 = ClosableNotebook(root)
        nb1.pack(side="left")
        nb2.pack(side="right")
        frame = ttk.Frame(nb1)
        nb1.add(frame, text="Tab1")
        root.update_idletasks()

        class Event: ...

        press = Event(); press.x = 5; press.y = 5
        nb1._on_tab_press(press)
        nb1._dragging = True
        release = Event()
        release.x_root = nb2.winfo_rootx() + 10
        release.y_root = nb2.winfo_rooty() + 10
        nb1._on_tab_release(release)

        assert not nb1.tabs()
        assert frame.master is nb2
        root.destroy()


class TestDragDetachment:
    def test_drag_tab_outside_detaches(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        frame = ttk.Frame(nb)
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

        assert not nb.tabs()
        assert nb._floating_windows
        root.destroy()


class TestDragDestroyedWidget:
    def test_drag_onto_destroyed_widget_detaches(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb1 = ClosableNotebook(root)
        nb2 = ClosableNotebook(root)
        nb1.pack(side="left")
        nb2.pack(side="right")
        frame = ttk.Frame(nb1)
        nb1.add(frame, text="Tab1")
        root.update_idletasks()

        x = nb2.winfo_rootx() + 10
        y = nb2.winfo_rooty() + 10
        nb2.destroy()
        root.update_idletasks()

        class Event: ...

        press = Event(); press.x = 5; press.y = 5
        nb1._on_tab_press(press)
        nb1._dragging = True
        release = Event(); release.x_root = x; release.y_root = y
        nb1._on_tab_release(release)

        assert not nb1.tabs()
        assert nb1._floating_windows
        root.destroy()
