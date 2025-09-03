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

from __future__ import annotations

"""Helper class managing notebooks detached into standalone windows."""

import tkinter as tk
from tkinter import ttk
import logging
import typing as t

if t.TYPE_CHECKING:  # pragma: no cover - for type checkers
    from .closable_notebook import ClosableNotebook

logger = logging.getLogger(__name__)


class DetachedWindow:
    """Manage a floating window hosting a :class:`ClosableNotebook`."""

    def __init__(
        self,
        owner: "ClosableNotebook",
        width: int,
        height: int,
        x: int,
        y: int,
    ) -> None:
        try:  # pragma: no cover - support standalone imports
            from .closable_notebook import ClosableNotebook
        except Exception:  # pragma: no cover
            from closable_notebook import ClosableNotebook

        self.owner = owner
        root_win = owner._app_root
        self.win = tk.Toplevel(root_win)
        self.win.transient(root_win)
        self.win.geometry(f"{width}x{height}+{x}+{y}")
        owner._floating_windows.append(self.win)

        def _on_destroy(_e, w=self.win) -> None:
            try:
                owner._cancel_after_events(w)
            except Exception:
                pass
            if w in owner._floating_windows:
                owner._floating_windows.remove(w)

        self.win.bind("<Destroy>", _on_destroy)
        self.nb = ClosableNotebook(self.win)
        self.nb.pack(expand=True, fill="both")

    def detach_tab(self, tab_id: str) -> None:
        """Move or clone *tab_id* from the owner into this window."""

        text = self.owner.tab(tab_id, "text")
        try:
            if not self.owner._move_tab(tab_id, self.nb):
                self.owner._clone_tab_contents(tab_id, self.nb, text, self.win)
            self.owner._post_clone_cleanup(self.nb)
        except Exception as exc:  # pragma: no cover - log and re-raise
            logger.exception("Failed to detach %s: %s", tab_id, exc)
            self.win.destroy()
            raise
