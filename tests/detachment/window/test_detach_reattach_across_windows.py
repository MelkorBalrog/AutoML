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

"""Tests for detaching and reattaching tabs across windows."""

from __future__ import annotations

import pytest
import tkinter as tk
from tkinter import ttk

from gui.utils.closable_notebook import ClosableNotebook
from gui.utils.widget_transfer_manager import WidgetTransferManager


@pytest.fixture
def notebooks() -> tuple[tk.Tk, ClosableNotebook, ClosableNotebook, ttk.Frame, ttk.Label]:
    """Create two notebooks in separate windows for detachment tests."""
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk not available")
    nb1 = ClosableNotebook(root)
    nb1.pack()
    frame = ttk.Frame(nb1)
    lbl = ttk.Label(frame, text="hi")
    lbl.pack()
    nb1.add(frame, text="Tab1")
    top = tk.Toplevel(root)
    nb2 = ClosableNotebook(top)
    nb2.pack()
    yield root, nb1, nb2, frame, lbl
    root.destroy()


@pytest.mark.detachment
@pytest.mark.reparenting
class TestDetachReattachAcrossWindows:
    def test_detach_and_reattach_between_windows(
        self, notebooks: tuple[tk.Tk, ClosableNotebook, ClosableNotebook, ttk.Frame, ttk.Label]
    ) -> None:
        root, nb1, nb2, frame, lbl = notebooks
        manager = WidgetTransferManager()

        tab_id = nb1.tabs()[0]
        moved = manager.detach_tab(nb1, tab_id, nb2)
        assert lbl.winfo_exists()
        assert lbl.master is moved
        assert moved is frame
        assert nb2.nametowidget(nb2.tabs()[0]) is frame

        tab_id2 = nb2.tabs()[0]
        moved_back = manager.detach_tab(nb2, tab_id2, nb1)
        assert lbl.master is moved_back
        assert moved_back is frame
        assert nb1.nametowidget(nb1.tabs()[0]) is frame

    def test_tab_registers_before_widget_reparent(
        self, notebooks: tuple[tk.Tk, ClosableNotebook, ClosableNotebook, ttk.Frame, ttk.Label], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root, nb1, nb2, frame, _lbl = notebooks
        manager = WidgetTransferManager()

        def fake_reparent(orig: tk.Widget, target: tk.Widget) -> None:
            assert nb2.tabs(), "tab not registered before reparent"
            assert frame.master is nb1
            raise tk.TclError("boom")

        monkeypatch.setattr("gui.utils.widget_transfer_manager.reparent_widget", fake_reparent)
        tab_id = nb1.tabs()[0]
        with pytest.raises(tk.TclError):
            manager.detach_tab(nb1, tab_id, nb2)
        assert not nb2.tabs()
        assert nb1.nametowidget(nb1.tabs()[0]) is frame

    def test_fallback_when_placeholder_fails(
        self,
        notebooks: tuple[tk.Tk, ClosableNotebook, ClosableNotebook, ttk.Frame, ttk.Label],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        root, nb1, nb2, frame, _lbl = notebooks
        manager = WidgetTransferManager()

        original_add = nb2.add
        calls: dict[str, int] = {"n": 0}

        def failing_add(child: tk.Widget, **kw) -> None:
            if calls["n"] == 0:
                calls["n"] += 1
                raise tk.TclError("boom")
            original_add(child, **kw)

        monkeypatch.setattr(nb2, "add", failing_add)

        tab_id = nb1.tabs()[0]
        moved = manager.detach_tab(nb1, tab_id, nb2)
        assert calls["n"] == 1
        assert moved is frame
        assert nb2.nametowidget(nb2.tabs()[0]) is frame
