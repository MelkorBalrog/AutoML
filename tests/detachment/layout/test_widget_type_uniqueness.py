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

"""Grouped tests ensuring single widget instances after detachment."""

import tkinter as tk
from tkinter import ttk

import pytest

from gui.utils.closable_notebook import ClosableNotebook


def _detach_notebook(nb: ClosableNotebook) -> ttk.Frame:
    class Event:
        ...

    press = Event()
    press.x = 5
    press.y = 5
    nb._on_tab_press(press)
    nb._dragging = True
    release = Event()
    release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
    release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
    nb._on_tab_release(release)
    float_nb = nb._floating_windows[0].winfo_children()[0]
    return float_nb.nametowidget(float_nb.tabs()[0])


class DummyToolbox(ttk.Frame):
    """Simple stand-in for toolbox widgets."""
    pass


class TestWidgetTypeUniqueness:
    def setup_method(self) -> None:
        try:
            self.root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        self.nb = ClosableNotebook(self.root)
        self.container = ttk.Frame(self.nb)
        self.nb.add(self.container, text="tab")

    def teardown_method(self) -> None:
        if hasattr(self, "root"):
            self.root.destroy()

    def _detach(self) -> ttk.Frame:
        self.nb.update_idletasks()
        return _detach_notebook(self.nb)

    def test_buttons_unique(self) -> None:
        ttk.Button(self.container, text="b").pack()
        detached = self._detach()
        clones = [w for w in detached.winfo_children() if isinstance(w, ttk.Button)]
        assert len(clones) == 1

    def test_canvases_unique(self) -> None:
        tk.Canvas(self.container, width=5, height=5).pack()
        detached = self._detach()
        clones = [w for w in detached.winfo_children() if isinstance(w, tk.Canvas)]
        assert len(clones) == 1

    def test_toolboxes_unique(self) -> None:
        DummyToolbox(self.container).pack()
        detached = self._detach()
        clones = [w for w in detached.winfo_children() if isinstance(w, DummyToolbox)]
        assert len(clones) == 1

    def test_scrollbars_unique(self) -> None:
        tk.Scrollbar(self.container).pack()
        detached = self._detach()
        clones = [w for w in detached.winfo_children() if isinstance(w, tk.Scrollbar)]
        assert len(clones) == 1
