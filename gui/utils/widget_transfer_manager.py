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


def cancel_after_events(widget: tk.Widget, cancelled: set[str] | None = None) -> None:
    """Cancel Tk ``after`` callbacks associated with *widget* and its children.

    This lightweight variant mirrors :func:`gui.utils.closable_notebook.cancel_after_events`
    but lives here to avoid circular imports. It recursively cancels callbacks to
    prevent ``invalid command name`` errors when widgets are moved or destroyed.
    """

    if cancelled is None:
        cancelled = set()
    try:
        for ident in widget.tk.call("after", "info", str(widget)):
            if ident not in cancelled:
                widget.after_cancel(ident)
                cancelled.add(ident)
    except Exception:
        pass
    for child in widget.winfo_children():
        cancel_after_events(child, cancelled)


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
        source.forget(orig)
        try:
            target.add(orig, text=text)
            target.select(orig)
        except tk.TclError as exc:
            # Roll back to the source notebook if re-parenting fails
            try:
                target.forget(orig)
            except tk.TclError:
                pass
            source.add(orig, text=text)
            source.select(orig)
            raise exc

        return orig
