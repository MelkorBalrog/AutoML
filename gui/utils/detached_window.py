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
"""Helpers for hosting detached diagrams in their own window."""

from __future__ import annotations

import tkinter as tk
import threading
from tkinter import ttk

from .closable_notebook import ClosableNotebook, cancel_after_events
from .window_controls import restore_window_buttons
from .window_resizer import WindowResizeController
from .tk_lifecycle_registry import TkLifecycleRegistry


class DetachedWindow:
    """Create a floating window embedding a :class:`ClosableNotebook`.

    Hosted visuals implement an explicit lifecycle.  No attributes are probed
    and no selector bindings are installed by this host.
    """

    def __init__(
        self, root: tk.Misc, width: int, height: int, x: int, y: int
    ) -> None:
        self.root = root
        self.active = True
        self.lifecycle = TkLifecycleRegistry(root, threading.get_ident())
        self.win = tk.Toplevel(root)
        restore_window_buttons(self.win)
        self.win.geometry(f"{width}x{height}+{x}+{y}")
        self.nb = ClosableNotebook(self.win)
        self.nb.pack(expand=True, fill="both")
        self._resizer: WindowResizeController | None = None
        self._resizer = WindowResizeController(self.win, self.nb)
        self._visuals: list[object] = []
        self.lifecycle.bind(self, self.win, "<Destroy>", self._on_destroy)

    # ------------------------------------------------------------------
    # Window setup helpers
    # ------------------------------------------------------------------
    def add(self, visual: object, text: str) -> tk.Widget:
        """Attach an object implementing the explicit visual contract."""
        from .dockable_diagram_window import DiagramContext, DiagramVisual

        if not isinstance(visual, DiagramVisual):
            raise TypeError("DetachedWindow.add requires a DiagramVisual")
        context = getattr(visual, "context", None)
        if not isinstance(context, DiagramContext):
            raise TypeError("visual must expose its widget-free DiagramContext")
        visual.attach(self.nb, context)
        widget = visual.widget
        if widget.master is not self.nb:
            raise RuntimeError("visual was not constructed for the detached host")
        self.nb.add(widget, text=text)
        self.nb.select(widget)
        self._resizer.add_target(widget)
        self._visuals.append(visual)
        visual.activate()
        return widget

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    def _on_destroy(self, _event: tk.Event) -> None:  # pragma: no cover - GUI event
        """Cancel pending callbacks when the window is destroyed."""
        if _event.widget is not self.win:
            return
        self.dispose()

    def dispose(self) -> None:
        """Drain window registrations and hosted visuals on the owner thread."""
        if not self.active:
            return
        cancel_after_events(self.win)
        for visual in tuple(self._visuals):
            visual.deactivate()
            visual.dispose()
        self._visuals.clear()
        if self._resizer is not None:
            self._resizer.shutdown()
        self._resizer = None
        self.lifecycle.dispose_component(self)
        self.active = False
