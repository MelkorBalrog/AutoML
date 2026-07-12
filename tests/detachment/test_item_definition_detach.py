# Author: Miguel Marina <karel.capek.robotics@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import os
import tkinter as tk
from types import SimpleNamespace
from tkinter import ttk

import pytest

from gui.utils.closable_notebook import ClosableNotebook
from mainappsrc.core.editors import Editors


pytestmark = pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")


class MinimalLifecycleUI:
    """Minimal lifecycle helper exposing the tab API Editors needs."""

    def __init__(self, doc_nb: ClosableNotebook) -> None:
        self.doc_nb = doc_nb

    def _new_tab(self, title: str) -> ttk.Frame:
        tab = ttk.Frame(self.doc_nb)
        self.doc_nb.add(tab, text=title)
        self.doc_nb.select(tab)
        return tab


@pytest.fixture
def item_definition_app():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk not available")
    root.withdraw()
    doc_nb = ClosableNotebook(root)
    doc_nb.pack(fill="both", expand=True)
    app = SimpleNamespace(
        root=root,
        doc_nb=doc_nb,
        item_definition={
            "description": "Brake controller item definition",
            "assumptions": "Nominal operating assumptions",
        },
    )
    app.lifecycle_ui = MinimalLifecycleUI(doc_nb)
    yield app
    try:
        doc_nb.close_all_floating()
    finally:
        root.destroy()


def _descendants(widget: tk.Widget) -> list[tk.Widget]:
    widgets: list[tk.Widget] = []
    for child in widget.winfo_children():
        widgets.append(child)
        widgets.extend(_descendants(child))
    return widgets


def _textual_content(widget: tk.Widget) -> str:
    chunks: list[str] = []
    try:
        text = widget.cget("text")
    except tk.TclError:
        text = ""
    if text:
        chunks.append(str(text))
    if isinstance(widget, tk.Text):
        chunks.append(widget.get("1.0", "end").strip())
    return "\n".join(chunk for chunk in chunks if chunk)


def _all_textual_content(widget: tk.Widget) -> str:
    return "\n".join(
        content
        for candidate in [widget, *_descendants(widget)]
        if (content := _textual_content(candidate))
    )


def test_item_definition_tab_detaches_with_visible_editor_content(item_definition_app) -> None:
    app = item_definition_app
    Editors(app).show_item_definition_editor()
    app.root.update_idletasks()

    original_tab_id = str(app._item_def_tab)
    app.doc_nb._detach_tab(original_tab_id, 25, 25)
    app.root.update_idletasks()

    assert app.doc_nb._floating_windows, "Item Definition tab did not detach"
    detached = app.doc_nb._floating_windows[-1]
    descendants = _descendants(detached)
    textual_content = _all_textual_content(detached)

    assert descendants, "Detached Item Definition window is blank"
    assert any(widget.winfo_ismapped() for widget in descendants), (
        "Detached Item Definition window contains no visible widgets"
    )
    assert "Item Description:" in textual_content
    assert "Assumptions:" in textual_content
    assert "Save" in textual_content


def test_item_definition_detach_failure_keeps_original_tab(item_definition_app) -> None:
    app = item_definition_app
    Editors(app).show_item_definition_editor()
    app.root.update_idletasks()

    original_tab = app._item_def_tab
    original_tab._detach_factory = lambda _parent: (_ for _ in ()).throw(
        RuntimeError("forced detach factory failure")
    )
    original_tab_id = str(original_tab)

    app.doc_nb._detach_tab(original_tab_id, 25, 25)
    app.root.update_idletasks()

    assert original_tab_id in app.doc_nb.tabs()
    assert app.doc_nb.tab(original_tab_id, "text") == "Item Definition"
    assert not app.doc_nb._floating_windows
