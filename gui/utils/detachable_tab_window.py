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
        self._cloned_widget: tk.Widget | None = None
        self._clone_mapping: dict[tk.Widget, tk.Widget] | None = None
        self._hidden_in_origin = False

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
        self._clone_tab_into_notebook()

    def dock_back(self) -> None:
        """Return the tab to its originating notebook."""

        if not is_main_thread():
            dispatch_to_ui(self.root, self.dock_back)
            return
        if not self.origin_notebook or not self.tab_widget:
            return
        self._restore_original_tab()
        if self._window is not None:
            cancel_after_events(self._window)
            self._shutdown_resizer()
            try:
                self._window.destroy()
            except Exception:
                pass
            self._window = None
        self._cloned_widget = None
        self._clone_mapping = None
        if callable(self.on_dock):
            self.on_dock(self.tab_widget)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _dispatch_dock_back(self) -> None:
        dispatch_to_ui(self.root, self.dock_back)

    def _clone_tab_into_notebook(self) -> None:
        if self._notebook is None:
            return
        clone = self._clone_tab_contents()
        if clone is None:
            clone = self._rebuild_tab_contents()
        if clone is None:
            return
        self._cloned_widget = clone
        try:
            self._notebook.insert(0, clone, text=self.metadata.title)
        except tk.TclError:
            try:
                self._notebook.add(clone, text=self.metadata.title)
            except tk.TclError:
                return
        self._notebook.select(clone)
        self._hide_original_tab()
        self._activate_clone_hooks(clone)
        if self._resizer is not None:
            self._resizer.add_target(clone)

    def _clone_tab_contents(self) -> tk.Widget | None:
        if self._notebook is None:
            return None
        try:
            clone, mapping, _layouts = self._notebook._clone_widget(
                self.tab_widget, self._notebook
            )
        except Exception:
            return None
        self._clone_mapping = mapping
        return clone

    def _rebuild_tab_contents(self) -> tk.Widget | None:
        if self._notebook is None:
            return None
        for attr in ("gsn_window", "arch_window"):
            window = getattr(self.tab_widget, attr, None)
            clone = self._rebuild_from_window(window)
            if clone is not None:
                return clone
        try:
            return self.tab_widget.__class__(self._notebook)
        except Exception:
            return None

    def _rebuild_from_window(self, window: tk.Widget | None) -> tk.Widget | None:
        if window is None:
            return None
        if self._notebook is None:
            return None
        cls = window.__class__
        app = getattr(window, "app", None)
        if hasattr(window, "diagram"):
            try:
                return cls(self._notebook, app, window.diagram)
            except Exception:
                return None
        diagram_id = getattr(window, "diagram_id", None)
        history = getattr(window, "diagram_history", None)
        if diagram_id is not None:
            try:
                return cls(
                    self._notebook,
                    app,
                    diagram_id=diagram_id,
                    history=history,
                )
            except Exception:
                return None
        return None

    def _activate_clone_hooks(self, clone: tk.Widget) -> None:
        for name in ("_rebuild_toolboxes", "_activate_parent_phase", "_switch_toolbox"):
            func = getattr(clone, name, None)
            if callable(func):
                try:
                    func()
                except Exception:
                    pass

    def _hide_original_tab(self) -> None:
        if self._hidden_in_origin:
            return
        try:
            self.origin_notebook.tab(self.tab_widget, state="hidden")
            self._hidden_in_origin = True
        except tk.TclError:
            pass

    def _restore_original_tab(self) -> None:
        if not self._hidden_in_origin:
            return
        try:
            self.origin_notebook.tab(self.tab_widget, state="normal")
            self.origin_notebook.select(self.tab_widget)
        except tk.TclError:
            pass
        self._hidden_in_origin = False

    def _install_resizer(self) -> None:
        if self._window is None or self._notebook is None:
            return
        try:
            self._resizer = WindowResizeController(self._window, self._notebook)
        except Exception:
            self._resizer = None
        if self._resizer is not None:
            self._resizer.set_primary_target(self._notebook)
            if self._cloned_widget is not None:
                self._resizer.add_target(self._cloned_widget)

    def _shutdown_resizer(self) -> None:
        if self._resizer is None:
            return
        try:
            self._resizer.shutdown()
        except Exception:
            pass
        self._resizer = None
