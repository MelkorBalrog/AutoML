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
import pytest
import tkinter as tk
from tkinter import ttk

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "gui", "utils"))
from closable_notebook import ClosableNotebook  # type: ignore


class TestClosableNotebookScrollbars:
    def _build_scrollable_frame(self, master: tk.Widget):
        frame = ttk.Frame(master)
        canvas = tk.Canvas(frame, width=100, height=100)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        for i in range(50):
            canvas.create_text(0, i * 20, anchor="nw", text=f"Item {i}")
        canvas.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return frame, canvas, scrollbar

    def _detach_first_tab(self, nb: ClosableNotebook):
        class E: ...

        press = E(); press.x = 5; press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True
        release = E()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)
        win = nb._floating_windows[0]
        new_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        return win, new_nb

    def test_scrollbar_rebind_after_detach(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        frame, canvas, scrollbar = self._build_scrollable_frame(nb)
        nb.add(frame, text="Toolbox")
        root.update_idletasks()

        _, new_nb = self._detach_first_tab(nb)
        new_frame = new_nb.nametowidget(new_nb.tabs()[0])
        new_canvas = next(c for c in new_frame.winfo_children() if isinstance(c, tk.Canvas))
        new_scrollbar = next(s for s in new_frame.winfo_children() if isinstance(s, ttk.Scrollbar))

        new_canvas.yview_moveto(1)
        assert new_scrollbar.get()[0] > 0

        cmd = new_scrollbar.cget("command")
        new_scrollbar.tk.call(cmd, "moveto", 0)
        assert new_canvas.yview()[0] == 0

        region = new_canvas.cget("scrollregion")
        assert region not in ("", "0 0 0 0")
        root.destroy()

    def test_scrollbar_resizes_after_detach(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        frame, canvas, scrollbar = self._build_scrollable_frame(nb)
        nb.add(frame, text="Toolbox")
        root.update_idletasks()

        win, new_nb = self._detach_first_tab(nb)
        new_frame = new_nb.nametowidget(new_nb.tabs()[0])
        new_canvas = next(c for c in new_frame.winfo_children() if isinstance(c, tk.Canvas))
        new_scrollbar = next(s for s in new_frame.winfo_children() if isinstance(s, ttk.Scrollbar))

        win.geometry("200x200")
        new_canvas.update_idletasks()
        new_canvas.yview_moveto(1)
        assert new_scrollbar.get()[0] > 0
        root.destroy()
