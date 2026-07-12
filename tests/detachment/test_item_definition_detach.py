# SPDX-License-Identifier: GPL-3.0-or-later
"""Regression tests for detaching the Item Definition editor tab."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import pytest

from gui.utils.closable_notebook import ClosableNotebook
from mainappsrc.core.editors import Editors


class _LifecycleUI:
    def __init__(self, notebook: ClosableNotebook) -> None:
        self.notebook = notebook

    def _new_tab(self, title: str) -> ttk.Frame:
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=title)
        self.notebook.select(frame)
        return frame


class _App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.doc_nb = ClosableNotebook(root)
        self.doc_nb.pack(fill=tk.BOTH, expand=True)
        self.lifecycle_ui = _LifecycleUI(self.doc_nb)
        self.item_definition = {"description": "Existing desc", "assumptions": "Existing asm"}


def _texts(widget: tk.Widget) -> set[str]:
    values: set[str] = set()
    pending = [widget]
    while pending:
        current = pending.pop()
        try:
            text = current.cget("text")
        except Exception:
            text = ""
        if text:
            values.add(str(text))
        try:
            pending.extend(current.winfo_children())
        except Exception:
            pass
    return values


def test_item_definition_detaches_with_form_content() -> None:
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk not available")
    root.withdraw()
    try:
        app = _App(root)
        Editors(app).show_item_definition_editor()
        tab_id = app.doc_nb.select()

        app.doc_nb._detach_tab(tab_id, 50, 50)

        assert app.doc_nb._floating_windows, "Item Definition did not detach"
        win = app.doc_nb._floating_windows[0]
        labels = _texts(win)
        assert "Item Description:" in labels
        assert "Assumptions:" in labels
        assert "Save" in labels
    finally:
        root.destroy()


def test_item_definition_failed_rebuild_keeps_original_tab() -> None:
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk not available")
    root.withdraw()
    try:
        app = _App(root)
        Editors(app).show_item_definition_editor()
        tab_id = app.doc_nb.select()
        tab = app.doc_nb.nametowidget(tab_id)

        def fail(_parent: tk.Widget) -> tk.Widget:
            raise RuntimeError("boom")

        tab._detach_factory = fail
        app.doc_nb._detach_tab(tab_id, 50, 50)

        assert str(tab) in app.doc_nb.tabs()
        assert not app.doc_nb._floating_windows
    finally:
        root.destroy()
