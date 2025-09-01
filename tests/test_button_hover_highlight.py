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

import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
from gui.controls.button_utils import add_hover_highlight

pytestmark = [pytest.mark.controls, pytest.mark.hover]


def _sum_rgb(value):
    if isinstance(value, tuple):
        return sum(value[:3])
    return sum(int(value[i : i + 2], 16) for i in (1, 3, 5))


def _get_rgb(value):
    if isinstance(value, tuple):
        return value[:3]
    return tuple(int(value[i : i + 2], 16) for i in (1, 3, 5))


def test_add_hover_highlight_swaps_to_lighter_image():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk not available")

    img = tk.PhotoImage(width=2, height=2)
    img.put("#808080", to=(0, 0, 2, 2))
    btn = ttk.Button(root, image=img)
    hover_img = add_hover_highlight(btn, img)

    btn.event_generate("<Enter>")
    root.update_idletasks()

    assert btn.cget("image") == str(hover_img)
    # Entire image should be lighter
    assert _sum_rgb(hover_img.get(0, 0)) >= _sum_rgb(img.get(0, 0)) + 60
    # Bottom pixels receive an extra boost creating a light glow
    assert _sum_rgb(hover_img.get(0, 1)) >= _sum_rgb(hover_img.get(0, 0)) + 30
    root.destroy()


def test_add_hover_highlight_blends_white_and_green():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk not available")

    img = tk.PhotoImage(width=2, height=2)
    img.put("#808080", to=(0, 0, 2, 2))
    btn = ttk.Button(root, image=img)
    hover_img = add_hover_highlight(btn, img)

    bottom = hover_img.get(0, 1)
    top = hover_img.get(0, 0)

    def _rgb(value):
        if isinstance(value, tuple):
            return value[:3]
        return tuple(int(value[i : i + 2], 16) for i in (1, 3, 5))

    br, bg, bb = _rgb(bottom)
    tr, tg, tb = _rgb(top)

    assert bg - max(br, bb) >= 40
    assert abs(tr - tg) < 5 and abs(tg - tb) < 5
    root.destroy()


def test_add_hover_highlight_lightens_black_pixels():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk not available")

    img = tk.PhotoImage(width=2, height=2)
    img.put("#000000", to=(0, 0, 2, 2))
    btn = ttk.Button(root, image=img)
    hover_img = add_hover_highlight(btn, img)

    top = _sum_rgb(hover_img.get(0, 0))
    bottom = _sum_rgb(hover_img.get(0, 1))

    assert top > 0
    assert bottom > top
    root.destroy()


def test_add_hover_highlight_preserves_transparency_and_glow():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk not available")

    img = tk.PhotoImage(width=2, height=2)
    img.put("#0000ff80", to=(0, 0, 2, 2))
    btn = ttk.Button(root, image=img)
    hover_img = add_hover_highlight(btn, img)

    bottom = hover_img.get(0, 1)
    top = hover_img.get(0, 0)
    if isinstance(bottom, tuple) and len(bottom) == 4:
        br, bg, bb, ba = bottom
        tr, tg, tb, ta = top
        assert bg - max(br, bb) >= 40
        assert ba == ta == 128
    root.destroy()

