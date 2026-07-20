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

"""Host transition orchestration without cross-parent widget transfer."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .dockable_diagram_window import DockableDiagramWindow


class WidgetTransferManager:
    """Reconstruct managed visuals; never move a live Tk widget."""

    def detach_tab(
        self, source: ttk.Notebook, tab_id: str, target: ttk.Notebook
    ) -> tk.Widget:
        """Replace a managed source visual with a destination-owned visual."""

        original = source.nametowidget(tab_id)
        title = source.tab(tab_id, "text")
        dock = getattr(original, "_dock_window", None)
        if not isinstance(dock, DockableDiagramWindow):
            raise RuntimeError(
                "cross-parent transfer is removed; provide a reconstruction lifecycle"
            )
        if dock.content_frame is not original:
            raise RuntimeError("tab is not the active visual owned by its dock manager")
        source.forget(original)
        rebuilt = dock.attach(target, index=len(target.tabs()), title=title)
        rebuilt._dock_window = dock
        return rebuilt
