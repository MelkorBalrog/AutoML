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

"""Grouped tests ensuring bound command strings target cloned widgets."""

from __future__ import annotations

import os
import tkinter as tk

import pytest

from closable_notebook import ClosableNotebook


pytestmark = pytest.mark.detachment


class TestBoundCommandRewrites:
    """Hover and click command rewrites are applied to cloned widgets."""

    @pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
    def test_hover_binding_targets_clone(self) -> None:
        root = tk.Tk(); root.withdraw()
        nb = ClosableNotebook(root)
        frame = tk.Frame(nb, background="red")
        btn = tk.Button(frame, text="btn")
        btn.bind("<Enter>", f"{frame._w} configure -background blue")
        btn.pack(); nb.add(frame, text="Tab")
        nb.update_idletasks()
        clone, mapping, _layouts = nb._clone_widget(frame, nb)
        clone_btn = mapping[btn]; clone_frame = mapping[frame]
        clone_btn.event_generate("<Enter>")
        root.update()
        assert clone_frame.cget("background") == "blue"
        clone.destroy(); frame.destroy(); root.destroy()

    @pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
    def test_click_binding_targets_clone(self) -> None:
        root = tk.Tk(); root.withdraw()
        nb = ClosableNotebook(root)
        frame = tk.Frame(nb, background="red")
        btn = tk.Button(frame, text="btn")
        btn.bind("<Button-1>", f"{frame._w} configure -background green")
        btn.pack(); nb.add(frame, text="Tab")
        nb.update_idletasks()
        clone, mapping, _layouts = nb._clone_widget(frame, nb)
        clone_btn = mapping[btn]; clone_frame = mapping[frame]
        clone_btn.event_generate("<Button-1>")
        root.update()
        assert clone_frame.cget("background") == "green"
        clone.destroy(); frame.destroy(); root.destroy()
