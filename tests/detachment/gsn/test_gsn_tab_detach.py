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

"""Validate GSN diagram tabs remain functional after detachment."""

import pytest

from closable_notebook import ClosableNotebook


def test_gsn_window_zoom_after_detach(gsn_diagram_window, toolbox):
    nb, win = gsn_diagram_window
    win_cls = type(win)

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
    new_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
    new_win = next(w for w in new_nb.winfo_children() if isinstance(w, win_cls))
    zoom_before = new_win.zoom
    new_win.zoom_in()
    assert new_win.zoom > zoom_before
    assert toolbox is not None  # ensure fixture exercised
