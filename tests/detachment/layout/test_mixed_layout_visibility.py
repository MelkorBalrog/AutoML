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

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "gui", "utils"))
from closable_notebook import ClosableNotebook


class TestMixedLayoutDetachment:
    def test_widgets_visible_after_detach(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        container = ttk.Frame(nb)
        nb.add(container, text="Tab1")

        pack_frame = ttk.Frame(container)
        pack_frame.pack(side="top")
        ttk.Label(pack_frame, text="pack").pack()

        grid_frame = ttk.Frame(container)
        grid_frame.pack(side="top")
        ttk.Label(grid_frame, text="grid").grid(row=0, column=0)

        place_frame = ttk.Frame(container, width=20, height=20)
        place_frame.pack(side="top")
        ttk.Label(place_frame, text="place").place(x=5, y=5)

        nb.update_idletasks()

        class Event: ...

        press = Event(); press.x = 5; press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True
        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)

        assert nb._floating_windows, "Tab did not detach"
        win = nb._floating_windows[-1]
        new_nb = next((w for w in win.winfo_children() if isinstance(w, ClosableNotebook)), None)
        assert new_nb is not None, "Detached window missing notebook"
        tab_widget = new_nb.nametowidget(new_nb.tabs()[0])
        labels = [child for frame in tab_widget.winfo_children() for child in frame.winfo_children()]
        texts = {lbl.cget("text") for lbl in labels if isinstance(lbl, ttk.Label)}
        assert {"pack", "grid", "place"} <= texts
        for lbl in labels:
            assert lbl.winfo_ismapped()
        root.destroy()
