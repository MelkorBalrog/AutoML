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
import os
import ctypes
import types
from pathlib import Path
import tkinter as tk

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
from gui.controls.capsule_button import CapsuleButton, _darken, _hex_to_rgb


class TestCapsuleButtonColor:
    def test_darken_accepts_system_color(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        try:
            assert _darken("SystemButtonFace").startswith("#")
        finally:
            root.destroy()

    def test_resolves_system_color_without_root(self, monkeypatch):
        if os.name != "nt":
            pytest.skip("Windows specific")
        monkeypatch.setattr(tk, "_default_root", None, raising=False)
        class DummyUser32:
            @staticmethod
            def GetSysColor(index):
                return 0x00332211
        monkeypatch.setattr(ctypes, "windll", types.SimpleNamespace(user32=DummyUser32()))
        assert _hex_to_rgb("SystemButtonFace") == (0x11, 0x22, 0x33)

class TestCapsuleButtonDimensions:
    def test_accepts_string_dimensions(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        try:
            btn = CapsuleButton(root, "Hi", width="80", height="26")
            assert int(btn["width"]) >= 80
            assert int(btn["height"]) == 26
        finally:
            root.destroy()
