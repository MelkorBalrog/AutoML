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

        # First attempt: register a placeholder tab before reparenting the
        # widget so the target notebook is aware of the incoming tab.
        placeholder = tk.Frame(target)
        try:
            target.add(placeholder, text=text)
            index = target.index(placeholder)
            orig.update_idletasks()
            target.update_idletasks()
            reparent_widget(orig, target)
            target.insert(index, orig, text=text)
            target.forget(placeholder)
            placeholder.destroy()
            target.select(orig)
        except tk.TclError:
            # Roll back placeholder registration and fall back to the original
            # approach (reparent first, then add) for environments where the
            # placeholder technique fails.
            try:
                target.forget(placeholder)
                placeholder.destroy()
            except tk.TclError:
                pass

            # Reattach to source before retrying.
            source.add(orig, text=text)
            source.select(orig)

            source.forget(orig)
            try:
                orig.update_idletasks()
                target.update_idletasks()
                reparent_widget(orig, target)
                target.add(orig, text=text)
                target.select(orig)
            except tk.TclError as exc:
                try:
                    reparent_widget(orig, source)
                except tk.TclError:
                    pass
                source.add(orig, text=text)
                source.select(orig)
                raise exc

        return orig
