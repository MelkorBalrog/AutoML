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

"""Reopen detached tab content by rebuilding fresh widget trees."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class DetachedTabReopener:
    """Recreate tab content inside a detached notebook without cloning widgets."""

    _WINDOW_ATTR_SUFFIXES = ("_window", "_dialog")

    def __init__(
        self,
        tab_widget: tk.Widget,
        notebook: ttk.Notebook,
        title: str,
    ) -> None:
        self.tab_widget = tab_widget
        self.notebook = notebook
        self.title = title

    def reopen(self) -> tk.Widget | None:
        """Create a new tab widget with fresh contents."""

        container = ttk.Frame(self.notebook)
        window, attr_name = self._find_primary_window()
        if window is not None:
            rebuilt = self._build_from_window(window, container)
            if rebuilt is not None:
                self._attach_reopened_window(container, rebuilt, attr_name)
                return container
        rebuilt = self._build_from_tab_class(container)
        if rebuilt is not None:
            self._attach_reopened_window(container, rebuilt, None)
            return container
        return None

    def _find_primary_window(self) -> tuple[tk.Widget | None, str | None]:
        for name in ("gsn_window", "arch_window"):
            window = getattr(self.tab_widget, name, None)
            if isinstance(window, tk.Widget):
                return window, name
        for attr, value in vars(self.tab_widget).items():
            if not attr.endswith(self._WINDOW_ATTR_SUFFIXES):
                continue
            if isinstance(value, tk.Widget):
                return value, attr
        for name in dir(self.tab_widget):
            if not name.endswith(self._WINDOW_ATTR_SUFFIXES):
                continue
            value = getattr(self.tab_widget, name, None)
            if isinstance(value, tk.Widget):
                return value, name
        window = self._find_child_window(self.tab_widget)
        if window is not None:
            return window, None
        return None, None

    def _find_child_window(self, root: tk.Widget) -> tk.Widget | None:
        try:
            children = root.winfo_children()
        except Exception:
            return None
        for child in children:
            if self._is_detached_window(child):
                return child
            found = self._find_child_window(child)
            if found is not None:
                return found
        return None

    def _is_detached_window(self, widget: tk.Widget) -> bool:
        if getattr(widget, "app", None) is not None:
            return True
        if getattr(widget, "diagram", None) is not None:
            return True
        if getattr(widget, "diagram_id", None) is not None:
            return True
        return False

    def _build_from_tab_class(self, container: ttk.Frame) -> tk.Widget | None:
        try:
            widget = self.tab_widget.__class__(container)
        except Exception:
            return None
        if hasattr(widget, "pack"):
            widget.pack(fill=tk.BOTH, expand=True)
        return widget

    def _build_from_window(self, window: tk.Widget, container: ttk.Frame) -> tk.Widget | None:
        cls = window.__class__
        app = getattr(window, "app", None)
        diagram = getattr(window, "diagram", None)
        diagram_id = getattr(window, "diagram_id", None)
        history = getattr(window, "diagram_history", None)
        if diagram is not None:
            rebuilt = self._safe_create(cls, container, app, diagram)
            return self._finalize_rebuild(rebuilt)
        if diagram_id is not None:
            rebuilt = self._safe_create(
                cls,
                container,
                app,
                diagram_id=diagram_id,
                history=history,
            )
            return self._finalize_rebuild(rebuilt)
        rebuilt = self._safe_create(cls, container, app)
        return self._finalize_rebuild(rebuilt)

    def _finalize_rebuild(self, rebuilt: tk.Widget | None) -> tk.Widget | None:
        if rebuilt is None:
            return None
        if hasattr(rebuilt, "pack"):
            rebuilt.pack(fill=tk.BOTH, expand=True)
        return rebuilt

    def _safe_create(self, cls, container: tk.Widget, app, **kwargs) -> tk.Widget | None:
        try:
            return cls(container, app, **kwargs)
        except Exception:
            return None

    def _attach_reopened_window(
        self,
        container: ttk.Frame,
        rebuilt: tk.Widget,
        attr_name: str | None,
    ) -> None:
        setattr(container, "_detached_content", rebuilt)
        if attr_name:
            setattr(container, attr_name, rebuilt)
