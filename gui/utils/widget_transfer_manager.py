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

"""Utilities for moving widgets between notebooks by cloning."""

from __future__ import annotations

import tkinter as tk
import typing as t

try:  # pragma: no cover - support direct module execution
    from .tk_utils import cancel_after_events
except Exception:  # pragma: no cover - legacy path
    from tk_utils import cancel_after_events


class WidgetTransferManager:
    """Move widgets between notebooks while preserving their state."""

    def detach_tab(
        self,
        source: "tk.Widget",
        tab_id: str,
        target: "tk.Widget",
    ) -> tk.Widget:
        """Move *tab_id* from *source* notebook to *target* notebook.

        Parameters
        ----------
        source:
            Notebook containing the tab to detach.
        tab_id:
            Widget path of the tab to move.
        target:
            Notebook receiving the tab.

        Returns
        -------
        tk.Widget
            The moved widget.
        """

        orig = source.nametowidget(tab_id)
        text = source.tab(tab_id, "text")
        cancel_after_events(orig)
        clone = self._clone_widget(orig, target)
        source.forget(orig)
        try:
            orig.destroy()
        except Exception:
            pass
        target.add(clone, text=text)
        target.select(clone)
        return clone

    # ------------------------------------------------------------------
    # Cloning helpers
    # ------------------------------------------------------------------

    def _clone_widget(self, widget: tk.Widget, parent: tk.Widget) -> tk.Widget:
        """Recursively clone *widget* under *parent*."""

        cls: t.Type[tk.Widget] = widget.__class__
        clone = cls(parent)

        # Copy configuration options
        try:
            config = widget.configure()
        except tk.TclError:
            config = {}
        for opt, opts in config.items():
            if isinstance(opts, (tuple, list)) and len(opts) >= 2:
                value = opts[-1]
                try:
                    clone.configure({opt: value})
                except tk.TclError:
                    pass

        # Copy event bindings
        try:
            sequences = widget.tk.call("bind", widget._w).split()
        except Exception:
            sequences = []
        for seq in sequences:
            try:
                cmd = widget.bind(seq)
                if cmd:
                    clone.bind(seq, cmd)
            except Exception:
                continue

        # Recreate children
        for child in widget.winfo_children():
            child_clone = self._clone_widget(child, clone)
            self._apply_layout(child, child_clone)

        return clone

    def _apply_layout(self, orig: tk.Widget, clone: tk.Widget) -> None:
        """Apply geometry management of *orig* to *clone*."""

        manager = orig.winfo_manager()
        try:
            if manager == "pack":
                info = orig.pack_info()
                for key in ("in", "in_"):
                    info.pop(key, None)
                clone.pack(**info)
            elif manager == "grid":
                info = orig.grid_info()
                for key in ("in", "in_"):
                    info.pop(key, None)
                clone.grid(**info)
            elif manager == "place":
                info = orig.place_info()
                for key in ("in", "in_"):
                    info.pop(key, None)
                clone.place(**info)
        except Exception:
            pass
