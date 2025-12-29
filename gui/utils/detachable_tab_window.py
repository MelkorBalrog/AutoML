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
from gui.utils.widget_transfer_manager import WidgetTransferManager
from gui.utils.window_resizer import WindowResizeController
from gui.utils.detached_tab_reopener import DetachedTabReopener


@dataclasses.dataclass
class DetachedTabMetadata:
    """Metadata tracked for a detached tab."""

    title: str
    diagram_id: str | None = None
    index: int | None = None


class DetachableTabWindow:
    """Wrapper around ``tk.Toplevel`` for hosting detached notebook tabs."""

    _DEFAULT_SIZE = (1200, 700)

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
        self._hidden_in_origin = False
        self._moved_tab = False

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
        self._configure_initial_geometry()

        toolbar = ttk.Frame(self._window)
        dock_btn = ttk.Button(toolbar, text="Dock", command=self.dock_back)
        dock_btn.pack(side=tk.RIGHT, padx=4, pady=2)
        ttk.Label(toolbar, text=self.metadata.title).pack(side=tk.LEFT, padx=8)
        toolbar.pack(fill=tk.X)

        self._notebook = ClosableNotebook(self._window)
        self._notebook.pack(fill=tk.BOTH, expand=True)
        self._install_resizer()
        self._clone_tab_into_notebook()
        if self._resizer is not None:
            self._resizer.sync_to_host()

    def dock_back(self) -> None:
        """Return the tab to its originating notebook."""

        if not is_main_thread():
            dispatch_to_ui(self.root, self.dock_back)
            return
        if not self.origin_notebook or not self.tab_widget:
            return
        if self._moved_tab:
            self._restore_moved_tab()
        else:
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
        if callable(self.on_dock):
            self.on_dock(self.tab_widget)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _dispatch_dock_back(self) -> None:
        dispatch_to_ui(self.root, self.dock_back)

    def _configure_initial_geometry(self) -> None:
        if self._window is None:
            return
        width = height = 0
        if self.origin_notebook is not None:
            try:
                self.origin_notebook.update_idletasks()
                width = self.origin_notebook.winfo_width()
                height = self.origin_notebook.winfo_height()
            except tk.TclError:
                width = height = 0
        if width <= 1 or height <= 1:
            width, height = self._DEFAULT_SIZE
        else:
            width = max(width, self._DEFAULT_SIZE[0])
            height = max(height, self._DEFAULT_SIZE[1])
        try:
            self._window.geometry(f"{width}x{height}")
            self._window.minsize(self._DEFAULT_SIZE[0], self._DEFAULT_SIZE[1])
        except tk.TclError:
            pass

    def _clone_tab_into_notebook(self) -> None:
        if self._notebook is None:
            return
        clone = self._reopen_tab_contents()
        if clone is None:
            if self._transfer_tab_contents():
                return
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
            self._register_resize_targets(clone)

    def _reopen_tab_contents(self) -> tk.Widget | None:
        if self._notebook is None:
            return None
        reopener = DetachedTabReopener(
            self.tab_widget,
            self._notebook,
            self.metadata.title,
        )
        return reopener.reopen()

    def _activate_clone_hooks(self, clone: tk.Widget) -> None:
        for name in ("_rebuild_toolboxes", "_activate_parent_phase", "_switch_toolbox"):
            func = getattr(clone, name, None)
            if callable(func):
                try:
                    func()
                except Exception:
                    pass

    def _register_resize_targets(self, root: tk.Widget) -> None:
        if self._resizer is None:
            return
        targets: tuple[type[tk.Widget], ...] = (
            tk.Frame,
            ttk.Frame,
            tk.LabelFrame,
            ttk.LabelFrame,
            tk.Canvas,
            ttk.Notebook,
            ClosableNotebook,
        )
        pending: list[tk.Widget] = [root]
        visited: set[tk.Widget] = set()
        while pending:
            widget = pending.pop()
            if widget in visited:
                continue
            visited.add(widget)
            if isinstance(widget, targets):
                self._resizer.add_target(widget)
            children = getattr(widget, "winfo_children", None)
            if callable(children):
                try:
                    pending.extend(children())
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

    def _restore_moved_tab(self) -> None:
        if (
            not self._moved_tab
            or self._notebook is None
            or self.origin_notebook is None
            or self.tab_widget is None
        ):
            return
        try:
            WidgetTransferManager().detach_tab(
                self._notebook, str(self.tab_widget), self.origin_notebook
            )
        except tk.TclError:
            return
        self._moved_tab = False

    def _install_resizer(self) -> None:
        if self._window is None or self._notebook is None:
            return
        try:
            self._resizer = WindowResizeController(
                self._window,
                self._notebook,
                use_win32_hook=False,
            )
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
