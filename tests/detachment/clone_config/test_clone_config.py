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

"""Regression tests for cloning widget configuration."""

from __future__ import annotations

import tkinter as tk
import pytest

from gui.utils.closable_notebook import ClosableNotebook
from gui.controls.capsule_button import CapsuleButton
from gui import TranslucidButton


class NullConfigCanvas(tk.Canvas):
    """Canvas subclass returning ``None`` from ``configure`` when queried."""

    def configure(self, *args, **kwargs):  # type: ignore[override]
        if args or kwargs:
            return super().configure(*args, **kwargs)
        return None


@pytest.mark.skipif(CapsuleButton is None, reason="CapsuleButton unavailable")
class TestCloneConfig:
    """Grouped tests ensuring clone configuration succeeds for special widgets."""

    def _clone(self, builder):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        root.report_callback_exception = lambda exc, val, tb: (_ for _ in ()).throw(val)

        nb = ClosableNotebook(root)
        widget = builder(nb)
        nb.add(widget, text="tab")
        clone, _, _ = nb._clone_widget(widget, nb)
        root.destroy()
        return clone

    def test_capsule_button_clone(self):
        clone = self._clone(lambda nb: CapsuleButton(nb, text="Cap"))
        assert isinstance(clone, CapsuleButton)
        assert clone.cget("text") == "Cap"

    def test_translucid_button_clone(self):
        clone = self._clone(lambda nb: TranslucidButton(nb, text="Trans"))
        assert isinstance(clone, TranslucidButton)
        assert clone.cget("text") == "Trans"

    def test_canvas_subclass_clone(self):
        def builder(nb: ClosableNotebook):
            canvas = NullConfigCanvas(nb, width=40, height=40, bg="red")
            canvas.create_rectangle(0, 0, 10, 10, fill="blue")
            return canvas

        clone = self._clone(builder)
        assert isinstance(clone, NullConfigCanvas)
        assert clone.cget("bg") == "red"
        assert clone.find_all()
