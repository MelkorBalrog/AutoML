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

try:  # pragma: no cover - support direct module execution
    from .tk_utils import cancel_after_events, reparent_widget
except Exception:  # pragma: no cover - legacy path
    from tk_utils import cancel_after_events, reparent_widget

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from gui.utils.dockable_diagram_window import DockableDiagramWindow


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

        try:  # defer import to avoid circular dependencies
            from gui.utils.dockable_diagram_window import DockableDiagramWindow as DDW
        except Exception:  # pragma: no cover - fallback for legacy paths
            from dockable_diagram_window import DockableDiagramWindow as DDW

        dock = getattr(orig, "_dock_window", None)
        if isinstance(dock, DDW):
            try:
                if dock._notebook is source:
                    width = source.winfo_width() or 200
                    height = source.winfo_height() or 200
                    x = source.winfo_rootx()
                    y = source.winfo_rooty()
                    dock.float(width, height, x, y, text)
                else:
                    dock.dock(target, len(target.tabs()), text)
                    target.select(dock.content_frame)
            except tk.TclError as exc:
                try:
                    dock.dock(source, len(source.tabs()), text)
                    source.select(dock.content_frame)
                except tk.TclError:
                    pass
                raise exc
            return orig

        source.forget(orig)
        try:
            target.add(orig, text=text)
        except tk.TclError as exc:
            source.add(orig, text=text)
            source.select(orig)
            raise exc

        try:
            reparent_widget(orig, target)
            target.select(orig)
        except tk.TclError as exc:
            try:
                target.forget(orig)
            except tk.TclError:
                pass
            if orig.master is not source:
                try:
                    reparent_widget(orig, source)
                except tk.TclError:
                    pass
            source.add(orig, text=text)
            source.select(orig)
            raise exc

        return orig
