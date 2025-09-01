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

"""Regression tests for canvas cloning with button images."""

import os
import sys
import tkinter as tk
import pytest

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "gui", "utils"))

from closable_notebook import ClosableNotebook


class TestCanvasCloneButtonImage:
    """Grouped tests verifying canvas clones avoid duplicate images."""

    def setup_method(self) -> None:
        try:
            self.root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        self.nb = ClosableNotebook(self.root)
        self.canvas = tk.Canvas(self.nb, width=50, height=50)
        self.nb.add(self.canvas, text="C")
        self.img = tk.PhotoImage(width=1, height=1)
        self.button = tk.Button(self.canvas, image=self.img)
        self.canvas.create_window(10, 10, window=self.button)

    def teardown_method(self) -> None:
        self.root.destroy()

    def test_clone_contains_no_extra_images(self) -> None:
        clone, _, _ = self.nb._clone_widget(self.canvas, self.nb)
        images = [i for i in clone.find_all() if clone.type(i) == "image"]
        assert not images, "clone contains duplicate images"
