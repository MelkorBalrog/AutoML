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

"""Tests for simplified tab detachment behaviour."""

import tkinter as tk

import pytest

from gui.utils.closable_notebook import ClosableNotebook

pytestmark = [pytest.mark.controls]


class TestTabDetachmentWindow:
    def test_detach_opens_toplevel(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        frame = tk.Frame(nb)
        nb.add(frame, text="Doc")
        nb.update_idletasks()
        tab_id = nb.tabs()[0]
        nb._detach_tab(tab_id, 20, 20)
        assert not nb.tabs(), "Tab should be removed after detachment"
        assert any(isinstance(w, tk.Toplevel) for w in root.winfo_children())
        root.destroy()
