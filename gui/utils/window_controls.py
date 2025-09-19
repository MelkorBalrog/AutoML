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
"""Helpers for configuring standard window controls on Tk toplevels."""

from __future__ import annotations

import tkinter as tk


def restore_window_buttons(win: tk.Toplevel) -> None:
    """Ensure *win* exposes minimize, maximize, and close controls.

    Some window manager interactions (such as marking a window transient)
    can strip the default decoration buttons from a toplevel.  Attempt to
    restore the standard controls in a cross-platform best-effort fashion.
    """

    try:
        win.overrideredirect(False)
    except tk.TclError:
        pass

    for attr in ("-toolwindow", "-topmost"):
        try:
            win.wm_attributes(attr, False)
        except tk.TclError:
            continue

    try:
        win.resizable(True, True)
    except tk.TclError:
        pass

    # X11 window managers support configuring the window type.  Request a
    # normal decorated window in case the toplevel was previously downgraded
    # to a dialog style without full controls.
    try:
        win.wm_attributes("-type", "normal")
    except tk.TclError:
        pass
