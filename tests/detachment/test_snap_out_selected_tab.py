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

"""Regression coverage for detachable notebook tab handling."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from mainappsrc.ui.app_lifecycle_ui import AppLifecycleUI


class _DummyApp:
    """Lightweight stand-in for the owning application."""


class _MissingTabNotebook:
    """Notebook stub that simulates a missing widget lookup."""

    def winfo_exists(self) -> bool:
        return True

    def select(self) -> str:
        return "missing_tab"

    def nametowidget(self, tab_id: str):
        raise KeyError(tab_id)

    def tabs(self):  # pragma: no cover - compatibility shim
        return []


class TestSnapOutSelectedTab:
    """Grouped regression tests for tab detachment safety."""

    def test_ignores_missing_selected_tab(self) -> None:
        root = tk.Tk()
        root.withdraw()
        try:
            ui = AppLifecycleUI(_DummyApp(), root)
            ui.doc_nb = _MissingTabNotebook()

            ui.snap_out_selected_tab()
        finally:
            root.destroy()

    def test_handles_destroyed_tab_widget(self) -> None:
        root = tk.Tk()
        root.withdraw()
        notebook = ttk.Notebook(root)
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Detached")
        notebook.select(frame)
        frame.destroy()
        try:
            ui = AppLifecycleUI(_DummyApp(), root)
            ui.doc_nb = notebook

            ui.snap_out_selected_tab()
        finally:
            root.destroy()
