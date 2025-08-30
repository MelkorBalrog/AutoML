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
"""Tests for script option rewrites during widget cloning."""

import os
import tkinter as tk
import pytest

from closable_notebook import ClosableNotebook


class TestRewriteScriptOptions:
    @pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
    def test_button_command_targets_clone(self):
        root = tk.Tk()
        nb = ClosableNotebook(root)
        orig_lbl = tk.Label(nb, text="orig")
        orig_btn = tk.Button(nb, command=f"{orig_lbl._w} configure -text clone")
        clone_lbl = tk.Label(nb, text="orig")
        clone_btn = tk.Button(nb)
        clone_btn.configure(command=f"{orig_lbl._w} configure -text clone")
        mapping = {orig_lbl: clone_lbl, orig_btn: clone_btn}
        nb.rewrite_option_references(mapping)
        clone_btn.invoke()
        assert clone_lbl.cget("text") == "clone"
        assert orig_lbl.cget("text") == "orig"
        root.destroy()

    @pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
    def test_menu_command_targets_clone(self):
        root = tk.Tk()
        nb = ClosableNotebook(root)
        orig_lbl = tk.Label(nb, text="orig")
        clone_lbl = tk.Label(nb, text="orig")
        script = f"{orig_lbl._w} configure -text clone"
        orig_menu = tk.Menu(nb, tearoff=False)
        clone_menu = tk.Menu(nb, tearoff=False)
        orig_menu.add_command(label="Change", command=script)
        clone_menu.add_command(label="Change", command=script)
        mapping = {orig_lbl: clone_lbl, orig_menu: clone_menu}
        nb.rewrite_option_references(mapping)
        clone_menu.invoke(0)
        assert clone_lbl.cget("text") == "clone"
        assert orig_lbl.cget("text") == "orig"
        root.destroy()
