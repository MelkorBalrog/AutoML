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

"""Tests for empty notebook background rendering."""

import tkinter as tk
from tkinter import ttk

import pytest

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from gui.closable_notebook import ClosableNotebook


class TestClosableNotebookBackground:
    """Group background behaviour tests."""

    @pytest.fixture(autouse=True)
    def setup_notebook(self):
        try:
            self.root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        self.nb = ClosableNotebook(self.root)
        self.nb.pack()
        self.root.update_idletasks()
        yield
        self.nb.destroy()
        self.root.destroy()

    def test_background_visible_when_empty(self):
        assert self.nb._bg_canvas.winfo_ismapped()

    def test_background_hidden_after_tab_added(self):
        frame = ttk.Frame(self.nb)
        self.nb.add(frame, text="Tab")
        self.root.update_idletasks()
        assert not self.nb._bg_canvas.winfo_ismapped()
