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

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from AutoML import AutoMLApp


def test_explorer_panel_starts_visible_and_pinned():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk not available")
    app = AutoMLApp(root)
    assert app.explorer_pane.winfo_manager() == "panedwindow"
    assert app._explorer_pinned is True
    assert app._explorer_pin_btn.cget("text") == "Unpin"
    app._schedule_explorer_hide(delay=0)
    root.update()
    assert app.explorer_pane.winfo_manager() == "panedwindow"
    root.destroy()


def test_toggle_explorer_panel():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk not available")
    app = AutoMLApp(root)
    app.toggle_explorer_pin()  # unpin
    app._schedule_explorer_hide(delay=0)
    root.update()
    assert app.explorer_pane.winfo_manager() == ""
    app.show_explorer()
    assert app.explorer_pane.winfo_manager() == "panedwindow"
    app.toggle_explorer_pin()  # pin again
    app.hide_explorer()
    assert app.explorer_pane.winfo_manager() == "panedwindow"
    root.destroy()
