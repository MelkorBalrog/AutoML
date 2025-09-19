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
"""Utilities that propagate toplevel resize events to managed widgets."""

from __future__ import annotations

import tkinter as tk
import typing as t


class WindowResizeController:
    """Keep a set of widgets sized with their host toplevel."""

    def __init__(self, win: tk.Misc, primary: tk.Widget | None = None) -> None:
        self.win = win
        self._primary: tk.Widget | None = None
        self._targets: list[tk.Widget] = []
        self._binding: str | None = None
        self._callback: t.Callable[[tk.Event], None] | None = None
        self._last_size: tuple[int, int] | None = None
        if primary is not None:
            self.set_primary_target(primary)
        self._bind_configure()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def set_primary_target(self, widget: tk.Widget | None) -> None:
        """Set *widget* as the primary resize target."""

        if widget is None:
            self._primary = None
            return
        self._primary = widget
        self.add_target(widget)

    def add_target(self, widget: tk.Widget | None) -> None:
        """Track an additional *widget* for resize updates."""

        if widget is None:
            return
        if widget not in self._targets:
            self._targets.append(widget)

    def remove_target(self, widget: tk.Widget | None) -> None:
        """Stop tracking *widget* for resize updates."""

        if widget is None:
            return
        try:
            self._targets.remove(widget)
        except ValueError:
            pass
        if widget is self._primary:
            self._primary = None

    @property
    def tracked_widgets(self) -> tuple[tk.Widget, ...]:
        """Return the widgets currently receiving resize updates."""

        return tuple(self._targets)

    @property
    def size(self) -> tuple[int, int] | None:
        """Return the last propagated size."""

        return self._last_size

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------
    def _bind_configure(self) -> None:
        """Attach the ``<Configure>`` handler to the managed toplevel."""

        try:
            self.win.wm_resizable(True, True)
        except Exception:
            pass

        def _callback(event: tk.Event) -> None:
            self._handle_configure(event)

        self._callback = _callback
        try:
            self._binding = self.win.bind("<Configure>", _callback, add="+")
        except Exception:
            self._binding = None

    def _handle_configure(self, event: tk.Event) -> None:
        """Apply the new size to each tracked widget."""

        widget = getattr(event, "widget", None)
        if widget not in (None, self.win):
            return
        width = self._get_dimension(event, "width")
        height = self._get_dimension(event, "height")
        if width <= 0 or height <= 0:
            return
        size = (width, height)
        if size == self._last_size:
            return
        self._last_size = size
        for target in list(self._targets):
            if not self._exists(target):
                try:
                    self._targets.remove(target)
                except ValueError:
                    pass
                continue
            self._resize_widget(target, width, height)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _get_dimension(event: tk.Event, name: str) -> int:
        try:
            value = getattr(event, name)
        except AttributeError:
            return 0
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _exists(widget: tk.Widget) -> bool:
        exists = getattr(widget, "winfo_exists", None)
        if callable(exists):
            try:
                return bool(exists())
            except Exception:
                return True
        return True

    def _resize_widget(self, widget: tk.Widget, width: int, height: int) -> None:
        self._configure_dimension(widget, "width", width)
        self._configure_dimension(widget, "height", height)
        self._ensure_geometry(widget)
        updater = getattr(widget, "update_idletasks", None)
        if callable(updater):
            try:
                updater()
            except Exception:
                pass
        self._notify(widget, width, height)

    @staticmethod
    def _configure_dimension(widget: tk.Widget, option: str, value: int) -> None:
        try:
            widget.configure(**{option: value})
        except Exception:
            pass

    def _ensure_geometry(self, widget: tk.Widget) -> None:
        manager = self._manager(widget)
        if manager == "pack":
            try:
                widget.pack_configure(expand=True, fill="both")
            except Exception:
                pass
        elif manager == "grid":
            info = self._grid_info(widget)
            try:
                widget.grid_configure(sticky="nsew")
            except Exception:
                pass
            master = getattr(widget, "master", None)
            if master is not None:
                row = info.get("row")
                column = info.get("column")
                if row is not None:
                    try:
                        master.grid_rowconfigure(int(row), weight=1)
                    except Exception:
                        pass
                if column is not None:
                    try:
                        master.grid_columnconfigure(int(column), weight=1)
                    except Exception:
                        pass
        elif manager == "place":
            try:
                widget.place_configure(relx=0, rely=0, relwidth=1.0, relheight=1.0)
            except Exception:
                pass

    @staticmethod
    def _manager(widget: tk.Widget) -> str:
        try:
            return widget.winfo_manager()
        except Exception:
            return ""

    @staticmethod
    def _grid_info(widget: tk.Widget) -> dict[str, t.Any]:
        try:
            info = widget.grid_info()
        except Exception:
            return {}
        if isinstance(info, dict):
            return info
        return {}

    @staticmethod
    def _notify(widget: tk.Widget, width: int, height: int) -> None:
        try:
            widget.event_generate(
                "<<HostWindowResized>>",
                when="tail",
                data=f"{width}x{height}",
            )
        except Exception:
            try:
                widget.event_generate("<<HostWindowResized>>", when="tail")
            except Exception:
                pass
