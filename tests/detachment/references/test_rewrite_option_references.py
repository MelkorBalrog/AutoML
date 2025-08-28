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
"""Tests for ``rewrite_option_references`` helper."""

import os
import tkinter as tk
import pytest
from tkinter import ttk

from closable_notebook import ClosableNotebook


class NullConfigFrame(ttk.Frame):
    """Frame whose ``configure`` call returns ``None`` when queried."""

    def configure(self, *args, **kwargs):  # type: ignore[override]
        if args or kwargs:
            return super().configure(*args, **kwargs)
        return None


class TestRewriteOptionReferences:
    @pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
    def test_handles_null_config(self):
        root = tk.Tk()
        nb = ClosableNotebook(root)
        orig = ttk.Frame(nb)
        clone = NullConfigFrame(nb)
        mapping = {orig: clone}
        nb.rewrite_option_references(mapping)
        root.destroy()
