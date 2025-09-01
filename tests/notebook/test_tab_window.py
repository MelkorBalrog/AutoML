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

"""Tests for notebook tab snapping behaviour."""

import tkinter as tk

from gui.utils.closable_notebook import ClosableNotebook


def test_detach_closes_tab_and_opens_window() -> None:
    root = tk.Tk()
    nb = ClosableNotebook(root)
    frame = tk.Frame(nb)
    nb.add(frame, text="Doc")
    root.update_idletasks()
    tab_id = nb.tabs()[0]
    nb._detach_tab(tab_id, 10, 10)
    root.update_idletasks()
    assert not nb.tabs()
    windows = [w for w in root.winfo_children() if isinstance(w, tk.Toplevel)]
    assert windows, "No new window created"
    win = windows[0]
    assert frame.winfo_toplevel() is win
    win.destroy()
    root.destroy()
