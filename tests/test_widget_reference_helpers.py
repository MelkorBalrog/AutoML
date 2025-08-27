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

"""Tests for ClosableNotebook widget reference helpers."""

import os
import sys
import pytest
import tkinter as tk
from tkinter import ttk

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "gui", "utils"))
from closable_notebook import ClosableNotebook


class NullConfigFrame(ttk.Frame):
    """Frame whose configure() returns None when queried."""

    def configure(self, *args, **kwargs):  # type: ignore[override]
        if args or kwargs:
            return super().configure(*args, **kwargs)
        return None


class TestRewriteConfigOptions:
    @pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
    def test_handles_null_config(self):
        root = tk.Tk()
        nb = ClosableNotebook(root)
        orig = ttk.Frame(nb)
        clone = NullConfigFrame(nb)
        mapping = {orig: clone}
        nb._rewrite_config_options(mapping)
        root.destroy()

    @pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
    def test_rewires_scrollbar_reference(self):
        root = tk.Tk()
        nb = ClosableNotebook(root)
        frame = ttk.Frame(nb)
        lst = tk.Listbox(frame)
        scroll = tk.Scrollbar(frame, orient="vertical", command=lst.yview)
        lst.configure(yscrollcommand=scroll.set)
        lst.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        clone, mapping = nb._clone_widget(frame, nb)
        nb._rewrite_config_options(mapping)
        clone_lst = mapping[lst]
        clone_scroll = mapping[scroll]
        assert str(clone_lst) in clone_scroll.cget("command")
        assert str(clone_scroll) in clone_lst.cget("yscrollcommand")
        root.destroy()


class TestUpdateCanvasWindowItems:
    @pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
    def test_rewires_canvas_window_items(self):
        root = tk.Tk()
        nb = ClosableNotebook(root)
        canvas = tk.Canvas(nb)
        frame = tk.Frame(canvas)
        lst = tk.Listbox(frame)
        lst.insert("end", "item")
        lst.pack()
        canvas.create_window(0, 0, window=frame, anchor="nw")
        clone, mapping = nb._clone_widget(canvas, nb)
        nb._update_canvas_window_items(mapping)
        item = clone.find_all()[0]
        win_path = clone.itemcget(item, "window")
        assert win_path
        clone_win = clone.nametowidget(win_path)
        assert isinstance(clone_win, tk.Frame)
        root.destroy()

