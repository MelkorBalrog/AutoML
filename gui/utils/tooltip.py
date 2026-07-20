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

import tkinter as tk
import threading
from tkinter import ttk, font as tkfont

from .tk_lifecycle_registry import TkLifecycleRegistry

class ToolTip:
    """Simple tooltip for Tkinter widgets.

    By default the tooltip is displayed when the mouse hovers over the
    associated widget.  The ``show`` and ``hide`` methods can also be used to
    control the tooltip manually (e.g. for notebook tabs).
    """

    def __init__(self, widget, text: str, delay: int = 500, *, automatic: bool = True):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tipwindow = None
        self.id = None
        self.active = True
        toplevel = getattr(widget, "winfo_toplevel", None)
        root = toplevel() if callable(toplevel) else widget
        self.lifecycle = TkLifecycleRegistry(root, threading.get_ident())
        if automatic:
            self.lifecycle.bind(self, widget, "<Enter>", self._schedule)
        # Always hide the tooltip when the pointer leaves the widget so
        # tooltips shown manually disappear as expected.
        self.lifecycle.bind(self, widget, "<Leave>", self._hide)

    def _schedule(self, _event=None):
        self._unschedule()
        self.id = self.lifecycle.after(self, self.widget, self.delay, self._show)

    def _show(self, x: int | None = None, y: int | None = None):
        if self.tipwindow or not self.text:
            return

        # If explicit coordinates aren't provided, fall back to the current
        # pointer location so the tooltip follows the cursor.  Handle x and y
        # independently to avoid "unbound" errors when only one value is given.
        if x is None or y is None:
            px, py = self.widget.winfo_pointerxy()
            if x is None:
                x = px
            if y is None:
                y = py

        # Offset slightly so the cursor stays over the widget, otherwise some
        # widgets (e.g. notebook tabs) immediately receive a <Leave> event when
        # the tooltip window appears on top of the pointer.
        x += 1
        y += 1
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        # Ensure the tooltip stays above other windows
        try:
            tw.wm_attributes("-topmost", True)
            tw.wm_attributes("-alpha", 0.9)
        except tk.TclError:
            pass

        lines = self.text.split("\n")
        max_len = max((len(line) for line in lines), default=1)
        width = min(max_len, 80)
        height = min(len(lines), 20)
        need_h = max_len > width
        need_v = len(lines) > height

        try:
            fixed_font = tkfont.nametofont("TkFixedFont").copy()
            fixed_font.configure(size=8)
        except tk.TclError:  # pragma: no cover - platform specific
            fixed_font = tkfont.Font(family="Courier", size=8)

        text = tk.Text(
            tw,
            width=width,
            height=height,
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            wrap="none",
            # Use a fixed-width font so table-like tooltip content stays aligned
            font=fixed_font,
        )
        vbar = ttk.Scrollbar(tw, orient="vertical", command=text.yview)
        hbar = ttk.Scrollbar(tw, orient="horizontal", command=text.xview)
        if need_v:
            text.configure(yscrollcommand=vbar.set)
            vbar.grid(row=0, column=1, sticky="ns")
        if need_h:
            text.configure(xscrollcommand=hbar.set)
            hbar.grid(row=1, column=0, sticky="ew")
        text.insert("1.0", self.text)
        text.configure(state="disabled")
        text.grid(row=0, column=0, sticky="nsew")
        tw.grid_columnconfigure(0, weight=1)
        tw.grid_rowconfigure(0, weight=1)
        tw.wm_geometry(f"+{x}+{y}")

    def show(self, x: int | None = None, y: int | None = None):
        """Show the tooltip immediately."""
        self._hide()
        self._show(x, y)

    def hide(self):
        """Hide the tooltip immediately."""
        self._hide()

    def _hide(self, _event=None):
        self._unschedule()
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

    def _unschedule(self):
        if self.id:
            self.lifecycle.cancel(self.id)
            self.id = None

    def dispose(self):
        """Remove callbacks before the tooltip owner is destroyed."""
        if not self.active:
            return
        self._hide()
        self.active = False
        self.lifecycle.dispose_component(self)
