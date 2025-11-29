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

"""Detachable tab wrapper to host notebook content in a dedicated window."""

from __future__ import annotations

import dataclasses
import tkinter as tk
import typing as t

from tkinter import ttk

from gui.utils.closable_notebook import ClosableNotebook
from gui.utils.dockable_diagram_window import DockableDiagramWindow
from gui.utils.tk_utils import cancel_after_events, dispatch_to_ui, is_main_thread
from gui.utils.window_resizer import WindowResizeController


@dataclasses.dataclass
class DetachedTabMetadata:
    """Metadata tracked for a detached tab."""

    title: str
    diagram_id: str | None = None
    index: int | None = None


class DetachableTabWindow:
    """Wrapper around ``tk.Toplevel`` for hosting detached notebook tabs."""

    def __init__(
        self,
        root: tk.Misc,
        tab_widget: tk.Widget,
        origin_notebook: ttk.Notebook,
        metadata: DetachedTabMetadata,
        on_dock: t.Callable[[tk.Widget], None] | None = None,
    ) -> None:
        self.root = root
        self.tab_widget = tab_widget
        self.origin_notebook = origin_notebook
        self.metadata = metadata
        self.on_dock = on_dock
        self._window: tk.Toplevel | None = None
        self._notebook: ClosableNotebook | None = None
        self._resizer: WindowResizeController | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def detach(self) -> None:
        """Create a window and move the tab content into it."""

        if not is_main_thread():
            dispatch_to_ui(self.root, self.detach)
            return
        if not self.tab_widget or not self.origin_notebook:
            return
        if self._window and self._window.winfo_exists():
            try:
                self._window.deiconify()
                self._window.lift()
            except tk.TclError:
                pass
            return

        self._window = tk.Toplevel(self.root)
        self._window.title(self.metadata.title)
        self._window.protocol("WM_DELETE_WINDOW", self._dispatch_dock_back)

        toolbar = ttk.Frame(self._window)
        dock_btn = ttk.Button(toolbar, text="Dock", command=self.dock_back)
        dock_btn.pack(side=tk.RIGHT, padx=4, pady=2)
        ttk.Label(toolbar, text=self.metadata.title).pack(side=tk.LEFT, padx=8)
        toolbar.pack(fill=tk.X)

        self._notebook = ClosableNotebook(self._window)
        self._notebook.pack(fill=tk.BOTH, expand=True)
        self._install_resizer()
        self._move_to_notebook(self._notebook, 0)

    def dock_back(self) -> None:
        """Return the tab to its originating notebook."""

        if not is_main_thread():
            dispatch_to_ui(self.root, self.dock_back)
            return
        if not self.origin_notebook or not self.tab_widget:
            return
        index = self.metadata.index if self.metadata.index is not None else len(self.origin_notebook.tabs())
        self._move_to_notebook(self.origin_notebook, index)
        if self._window is not None:
            cancel_after_events(self._window)
            self._shutdown_resizer()
            try:
                self._window.destroy()
            except Exception:
                pass
            self._window = None
        if callable(self.on_dock):
            self.on_dock(self.tab_widget)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _dispatch_dock_back(self) -> None:
        dispatch_to_ui(self.root, self.dock_back)

    def _move_to_notebook(self, notebook: ttk.Notebook, index: int) -> None:
        dock = getattr(self.tab_widget, "_dock_window", None)
        if isinstance(dock, DockableDiagramWindow):
            dock.dock(notebook, index, self.metadata.title)
        else:
            cancel_after_events(self.tab_widget)
            try:
                notebook.insert(index, self.tab_widget, text=self.metadata.title)
            except tk.TclError:
                try:
                    notebook.add(self.tab_widget, text=self.metadata.title)
                except tk.TclError:
                    return
            notebook.select(self.tab_widget)

        if self._resizer is not None:
            self._resizer.add_target(self.tab_widget)

    def _install_resizer(self) -> None:
        if self._window is None or self._notebook is None:
            return
        try:
            self._resizer = WindowResizeController(self._window, self._notebook)
        except Exception:
            self._resizer = None
        if self._resizer is not None:
            self._resizer.set_primary_target(self._notebook)
            self._resizer.add_target(self.tab_widget)

    def _shutdown_resizer(self) -> None:
        if self._resizer is None:
            return
        try:
            self._resizer.shutdown()
        except Exception:
            pass
        self._resizer = None

