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
"""Tests for ``rebind_scrollbars`` helper."""

import os
import tkinter as tk
import pytest

from closable_notebook import ClosableNotebook


class TestRebindScrollbars:
    @pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
    def test_rewires_scrollbar_reference(self):
        root = tk.Tk()
        nb = ClosableNotebook(root)
        frame = tk.Frame(nb)
        lst = tk.Listbox(frame)
        scroll = tk.Scrollbar(frame, orient="vertical", command=lst.yview)
        lst.configure(yscrollcommand=scroll.set)
        lst.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        clone, mapping, layouts = nb._clone_widget(frame, nb)
        nb.rebind_scrollbars(mapping)
        clone_lst = mapping[lst]
        clone_scroll = mapping[scroll]
        assert str(clone_lst) in clone_scroll.cget("command")
        assert str(clone_scroll) in clone_lst.cget("yscrollcommand")
        root.destroy()
