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

"""Tests for widget reference reassignment in ClosableNotebook."""

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


def test_reassign_handles_null_config():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk not available")
    nb = ClosableNotebook(root)
    orig = ttk.Frame(nb)
    clone = NullConfigFrame(nb)
    mapping = {orig: clone}
    nb._reassign_widget_references(mapping)
    root.destroy()
