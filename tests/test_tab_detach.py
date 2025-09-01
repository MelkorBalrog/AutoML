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

"""Tests for simplified tab detachment behaviour."""

import os
import sys
import tkinter as tk
from tkinter import ttk

import pytest

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(root_dir)
from gui.utils.closable_notebook import ClosableNotebook


class TestTabDetachment:
    """Grouped tests verifying basic tab detachment."""

    def _setup_notebook(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        frame = ttk.Frame(nb)
        nb.add(frame, text="Tab1")
        nb.update_idletasks()
        return root, nb, frame

    def test_detach_closes_tab_and_opens_window(self):
        root, nb, frame = self._setup_notebook()

        class Event:
            pass

        press = Event()
        press.x = 5
        press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True
        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)

        assert nb.tabs() == []
        assert len(nb._floating_windows) == 1
        win = nb._floating_windows[0]
        assert frame.master is win
        win.destroy()
        root.destroy()

    def test_window_title_matches_tab_text(self):
        root, nb, frame = self._setup_notebook()

        class Event:
            pass

        press = Event()
        press.x = 5
        press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True
        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)

        win = nb._floating_windows[0]
        assert win.title() == "Tab1"
        win.destroy()
        root.destroy()
