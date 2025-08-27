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
import time
import tkinter as tk
import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from AutoML import AutoMLApp


def test_explorer_hover_debounce():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk not available")
    app = AutoMLApp(root)
    # Hover enter then leave before delay should not show explorer
    app.lifecycle_ui.on_explorer_tab_enter()
    app.lifecycle_ui.on_explorer_tab_leave()
    root.update()
    time.sleep(0.25)
    root.update()
    assert app.explorer_pane.winfo_manager() == ""
    # Hover and keep cursor; explorer should show
    app.lifecycle_ui.on_explorer_tab_enter()
    root.update()
    time.sleep(0.25)
    root.update()
    assert app.explorer_pane.winfo_manager() == "panedwindow"
    width = app.explorer_pane.winfo_width()
    assert 0 < width <= app._explorer_width
    root.destroy()
