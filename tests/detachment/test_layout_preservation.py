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

import os
import sys
import tkinter as tk
from tkinter import ttk
import pytest

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "gui", "utils"))
from closable_notebook import ClosableNotebook


class TestLayoutPreservation:
    def test_control_geometry_unchanged_after_detach(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        container = ttk.Frame(nb)
        text = tk.Text(container)
        text.pack(side="left")
        vsb = ttk.Scrollbar(container, orient="vertical")
        vsb.pack(side="right", fill="y")
        nb.add(container, text="Tab1")
        nb.update_idletasks()
        text_before = text.pack_info()
        vsb_before = vsb.pack_info()

        class Event: ...

        press = Event(); press.x = 5; press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True
        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)

        assert nb._floating_windows, "Tab did not detach"
        text_after = text.pack_info()
        vsb_after = vsb.pack_info()
        assert text_before == text_after
        assert vsb_before == vsb_after
        root.destroy()

    def test_mixed_geometry_unchanged_after_detach(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        container = ttk.Frame(nb)
        nb.add(container, text="Tab1")

        pack_frame = ttk.Frame(container)
        pack_frame.pack(side="top")
        pack_lbl = ttk.Label(pack_frame, text="p")
        pack_lbl.pack(side="left")

        grid_frame = ttk.Frame(container)
        grid_frame.pack(side="top")
        grid_lbl = ttk.Label(grid_frame, text="g")
        grid_lbl.grid(row=0, column=0)

        place_frame = ttk.Frame(container, width=20, height=20)
        place_frame.pack(side="top")
        place_lbl = ttk.Label(place_frame, text="pl")
        place_lbl.place(x=5, y=5)

        nb.update_idletasks()
        pack_before = pack_lbl.pack_info()
        grid_before = grid_lbl.grid_info()
        place_before = place_lbl.place_info()
        for info in (grid_before, place_before):
            for key in ("in", "in_", "before", "after"):
                info.pop(key, None)

        class Event: ...

        press = Event(); press.x = 5; press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True
        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)

        assert nb._floating_windows, "Tab did not detach"
        pack_after = pack_lbl.pack_info()
        grid_after = grid_lbl.grid_info()
        place_after = place_lbl.place_info()
        for info in (grid_after, place_after):
            for key in ("in", "in_", "before", "after"):
                info.pop(key, None)

        assert pack_before == pack_after
        assert grid_before == grid_after
        assert place_before == place_after
        root.destroy()
