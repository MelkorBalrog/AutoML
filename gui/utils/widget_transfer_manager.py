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

"""Move widgets between notebooks without cloning."""

from __future__ import annotations

import tkinter as tk


class WidgetTransferManager:
    """Helper to move tabs between notebooks without cloning."""

    def __init__(self, source_notebook: "ClosableNotebook") -> None:
        self._source = source_notebook

    def detach_tab(
        self, tab_id: str, target_notebook: "ClosableNotebook"
    ) -> tk.Widget:
        """Move ``tab_id`` to ``target_notebook`` and return the widget."""

        orig = self._source.nametowidget(tab_id)
        text = self._source.tab(tab_id, "text")

        try:
            self._source._cancel_after_events(orig)  # type: ignore[attr-defined]
        except Exception:
            pass

        self._source.forget(orig)
        target_notebook.add(orig, text=text)
        try:
            target_notebook.select(orig)
        except Exception:
            pass
        return orig
