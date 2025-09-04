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

from __future__ import annotations

"""Utilities for moving Tk widgets between notebooks."""

import typing as t
import tkinter as tk
from tkinter import ttk

if t.TYPE_CHECKING:  # pragma: no cover
    from .closable_notebook import ClosableNotebook
else:  # pragma: no cover
    ClosableNotebook = ttk.Notebook


class WidgetTransferManager:
    """Move widgets between :class:`ttk.Notebook` containers.

    The manager captures geometry, cancels ``after`` callbacks, rebinds events
    and restores layout information when widgets are moved across notebooks.
    """

    def __init__(self, notebook: "ClosableNotebook") -> None:
        self._notebook = notebook
        self._geometry: dict[tk.Widget, tuple[str, dict[str, t.Any]]] = {}

    # ------------------------------------------------------------------
    # helpers
    def _capture_geometry(self, widget: tk.Widget) -> None:
        try:
            manager = widget.winfo_manager()
        except Exception:
            return
        opts: dict[str, t.Any]
        if manager == "pack":
            opts = widget.pack_info()
        elif manager == "grid":
            opts = widget.grid_info()
        elif manager == "place":
            opts = widget.place_info()
        else:
            manager = ""
            opts = {}
        self._geometry[widget] = (manager, opts)

    def _restore_geometry(self, widget: tk.Widget) -> None:
        info = self._geometry.get(widget)
        if not info:
            return
        manager, opts = info
        try:
            if manager == "pack":
                widget.pack(**opts)
            elif manager == "grid":
                widget.grid(**opts)
            elif manager == "place":
                widget.place(**opts)
        except Exception:
            pass

    def _rebind_events(self, widget: tk.Widget) -> None:
        try:
            sequences = widget.bind()
            for seq in sequences:
                cmd = widget.bind(seq)
                if cmd:
                    widget.bind(seq, cmd)
        except Exception:
            pass
        for child in widget.winfo_children():
            self._rebind_events(child)

    # ------------------------------------------------------------------
    # public api
    def detach_tab(
        self, tab_id: str, target_notebook: "ClosableNotebook"
    ) -> tk.Widget | None:
        """Detach *tab_id* from the source notebook to *target_notebook*.

        ``after`` callbacks tied to the widget tree are cancelled before the tab
        is removed.  Event bindings are re-established on the moved or cloned
        widget and geometry information is stored for later restoration.
        """

        nb = self._notebook
        text = nb.tab(tab_id, "text")
        orig = nb.nametowidget(tab_id)
        self._capture_geometry(orig)
        cancelled: set[str] = set()
        nb._cancel_after_events(orig, cancelled)
        moved = nb._move_tab(tab_id, target_notebook)
        if moved or orig.master is target_notebook:
            child = orig
        else:
            nb.forget(orig)
            nb._tab_hosts.pop(orig, None)
            mapping: dict[tk.Widget, tk.Widget] = {}
            child, mapping, _layouts = nb._clone_widget(
                orig, target_notebook, mapping, cancelled=cancelled
            )
            nb._reassign_widget_references(mapping)
            target_notebook.add(child, text)
        self._rebind_events(child)
        return child

    def reattach_tab(
        self, widget: tk.Widget, source_notebook: "ClosableNotebook"
    ) -> tk.Widget | None:
        """Reattach *widget* to *source_notebook* and restore its geometry."""

        self._capture_geometry(widget)
        cancelled: set[str] = set()
        tnb = source_notebook
        tnb._cancel_after_events(widget, cancelled)
        tab_id = str(widget)
        moved = (
            widget.master._move_tab(tab_id, tnb)
            if hasattr(widget.master, "_move_tab")
            else False
        )
        if moved or widget.master is tnb:
            self._restore_geometry(widget)
            self._rebind_events(widget)
            return widget
        return None
