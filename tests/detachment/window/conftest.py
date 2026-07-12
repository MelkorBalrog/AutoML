# SPDX-License-Identifier: GPL-3.0-or-later
"""Fixtures for detached window tests."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import pytest

from gui.utils.closable_notebook import ClosableNotebook


@pytest.fixture
def notebooks() -> tuple[tk.Tk, ClosableNotebook, ClosableNotebook, ttk.Frame, ttk.Label]:
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk not available")
    nb1 = ClosableNotebook(root)
    nb1.pack()
    frame = ttk.Frame(nb1)
    lbl = ttk.Label(frame, text="Content")
    lbl.pack()
    nb1.add(frame, text="T1")
    top = tk.Toplevel(root)
    nb2 = ClosableNotebook(top)
    nb2.pack()
    yield root, nb1, nb2, frame, lbl
    try:
        root.destroy()
    except tk.TclError:
        pass
