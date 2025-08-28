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

"""Regression tests for explorer toolbar cloning on tab detachment."""

from __future__ import annotations

import types
import tkinter as tk
from tkinter import ttk
import pytest

from gui.utils.closable_notebook import ClosableNotebook
from mainappsrc.core.open_windows_features import Open_Windows_Features


class DummyLifecycleUI:
    """Minimal lifecycle UI to create tabs for testing."""

    def __init__(self, nb: ClosableNotebook) -> None:
        self.nb = nb

    def _new_tab(self, title: str):  # pragma: no cover - exercised indirectly
        frame = ttk.Frame(self.nb)
        self.nb.add(frame, text=title)
        return frame


class TestExplorerToolbar:
    def _setup_app(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")

        nb = ClosableNotebook(root)
        app = types.SimpleNamespace(
            doc_nb=nb,
            lifecycle_ui=DummyLifecycleUI(nb),
            safety_mgmt_toolbox=types.SimpleNamespace(
                modules=[], diagrams={}, list_diagrams=lambda: None
            ),
            refresh_all=lambda: None,
        )
        features = Open_Windows_Features(app)
        return root, nb, app, features

    def _detach_explorer(self):
        root, nb, app, features = self._setup_app()
        features.manage_safety_management()
        tab_id = nb.tabs()[0]
        nb._detach_tab(tab_id, 50, 50)
        win = nb._floating_windows[0]
        nb2 = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        clone = nb2.nametowidget(nb2.tabs()[0])
        return root, win, clone

    def test_detached_toolbar_buttons_present(self) -> None:
        root, win, clone = self._detach_explorer()

        toolbar = next(
            (
                child
                for child in clone.winfo_children()
                if isinstance(child, (tk.Frame, ttk.Frame))
                and any(isinstance(c, ttk.Button) for c in child.winfo_children())
            ),
            None,
        )
        assert toolbar is not None
        assert toolbar.winfo_children()

        win.destroy()
        root.destroy()

    def test_detached_toolbar_refresh_invokes_clone(self) -> None:
        root, win, clone = self._detach_explorer()

        toolbar = next(
            (
                child
                for child in clone.winfo_children()
                if isinstance(child, (tk.Frame, ttk.Frame))
                and any(isinstance(c, ttk.Button) for c in child.winfo_children())
            ),
            None,
        )
        assert toolbar is not None
        refresh = next(
            (b for b in toolbar.winfo_children() if isinstance(b, ttk.Button) and b["text"] == "Refresh"),
            None,
        )
        assert refresh is not None

        called = {"flag": False}

        def _populate(self):
            called["flag"] = True

        clone.populate = types.MethodType(_populate, clone)
        refresh.invoke()
        assert called["flag"]

        win.destroy()
        root.destroy()

