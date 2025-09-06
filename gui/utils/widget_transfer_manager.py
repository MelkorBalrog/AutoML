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

"""Utilities for moving widgets between notebooks without cloning."""

from __future__ import annotations

import tkinter as tk
import typing as t

try:  # pragma: no cover - support direct module execution
    from .tk_utils import cancel_after_events, reparent_widget
except Exception:  # pragma: no cover - legacy path
    from tk_utils import cancel_after_events, reparent_widget


class WidgetTransferManager:
    """Move widgets between notebooks while preserving their state."""

    def _transfer_children(
        self, orig: tk.Widget, new_container: tk.Widget
    ) -> None:
        for child in orig.winfo_children():
            geom_manager = child.winfo_manager()
            layout: dict[str, t.Any] | None = None
            if geom_manager == "pack":
                layout = child.pack_info()
            elif geom_manager == "grid":
                layout = child.grid_info()
            elif geom_manager == "place":
                layout = child.place_info()
            reparent_widget(child, new_container)
            try:
                if geom_manager == "pack" and layout is not None:
                    child.pack(**layout)
                elif geom_manager == "grid" and layout is not None:
                    child.grid(**layout)
                elif geom_manager == "place" and layout is not None:
                    child.place(**layout)
            except Exception:
                pass

    def _restore_failure(
        self,
        source: tk.Widget,
        orig: tk.Widget,
        target: tk.Widget,
        new_container: tk.Widget | None,
        text: str,
    ) -> None:
        if new_container is not None:
            for child in new_container.winfo_children():
                try:
                    reparent_widget(child, orig)
                except tk.TclError:
                    pass
            try:
                target.forget(new_container)
            except tk.TclError:
                pass
            new_container.destroy()
        source.add(orig, text=text)
        source.select(orig)

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

        source.forget(orig)
        new_container: tk.Widget | None = None
        try:
            new_container = orig.__class__(target)
            target.add(new_container, text=text)
            new_container.update_idletasks()
            self._transfer_children(orig, new_container)
            target.select(new_container)
            orig.destroy()
            return new_container
        except tk.TclError as exc:
            self._restore_failure(source, orig, target, new_container, text)
            raise exc
