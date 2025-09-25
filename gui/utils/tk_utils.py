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

"""Helper utilities for working with Tk widgets."""

from __future__ import annotations

import sys
import ctypes
import tkinter as tk


def _update_widget_master(widget: tk.Widget, new_parent: tk.Widget) -> None:
    """Synchronise Tkinter's Python-level parent bookkeeping."""

    old_parent = getattr(widget, "master", None)
    if old_parent is new_parent:
        return

    try:
        name = widget.winfo_name()
    except Exception:
        name = None

    if isinstance(old_parent, tk.Misc) and name:
        try:
            old_children = getattr(old_parent, "children", None)
            if isinstance(old_children, dict):
                old_children.pop(name, None)
        except Exception:
            pass

    widget.master = new_parent

    if isinstance(new_parent, tk.Misc) and name:
        try:
            new_children = getattr(new_parent, "children", None)
            if isinstance(new_children, dict):
                new_children[name] = widget
        except Exception:
            pass


def cancel_after_events(widget: tk.Widget, cancelled: set[str] | None = None) -> None:
    """Cancel Tk ``after`` callbacks tied to *widget* and its children."""

    if cancelled is None:
        cancelled = set()

    def _cancel_ident(ident: str) -> None:
        tkapp_local = getattr(widget, "tk", None)
        if tkapp_local is None:
            return
        try:
            tkapp_local.call("after", "cancel", ident)
        except Exception:
            return
        try:
            root = widget._root()
        except Exception:
            root = None
        if root is not None:
            tcl_cmds = getattr(root, "_tclCommands", None)
            if tcl_cmds is not None and ident in tcl_cmds:
                try:
                    root.deletecommand(ident)
                except Exception:
                    pass
        cancelled.add(ident)

    tkapp = getattr(widget, "tk", None)
    if tkapp is not None and getattr(tkapp, "call", None) is not None:
        try:
            widget_ids = tkapp.call("after", "info", str(widget))
        except Exception:
            widget_ids = ()
        if isinstance(widget_ids, str):
            widget_ids = (widget_ids,)
        for ident in widget_ids:
            if ident and ident not in cancelled:
                _cancel_ident(ident)

        try:
            all_ids = tkapp.call("after", "info")
        except Exception:
            all_ids = ()
        if isinstance(all_ids, str):
            all_ids = (all_ids,)
        for ident in all_ids:
            if not isinstance(ident, str) or ident in cancelled:
                continue
            if ident.startswith(str(widget)):
                _cancel_ident(ident)
                continue
            try:
                script = tkapp.call("after", "info", ident)
            except Exception:
                continue
            if str(widget) in script:
                _cancel_ident(ident)

    try:
        for name in dir(widget):
            if name.endswith(("_anim", "_after", "_timer", "_animate")):
                ident = getattr(widget, name, None)
                if isinstance(ident, str) and ident not in cancelled:
                    _cancel_ident(ident)
    except Exception:
        pass

    for child in widget.winfo_children():
        cancel_after_events(child, cancelled)


def reparent_widget(widget: tk.Widget, new_parent: tk.Widget) -> None:
    """Reparent *widget* into *new_parent* using OS-level APIs."""

    if widget is new_parent or widget.master is new_parent:
        return

    widget.update_idletasks()
    new_parent.update_idletasks()
    wid = int(widget.winfo_id())
    pid = int(new_parent.winfo_id())

    # First try Tk's cross-platform reparent command if available
    try:
        widget.tk.call("tk::unsupported::reparent", str(widget), str(new_parent))
        _update_widget_master(widget, new_parent)
        return
    except tk.TclError:
        pass

    if sys.platform.startswith("win"):
        if ctypes.windll.user32.SetParent(wid, pid) == 0:
            # Fallback to Tk geometry manager when OS-level reparenting fails
            try:
                widget.tk.call("place", str(widget), "-in", str(new_parent))
                widget.tk.call("place", "forget", str(widget))
            except tk.TclError as exc:
                raise tk.TclError("SetParent failed") from exc
        _update_widget_master(widget, new_parent)
    elif sys.platform.startswith("linux"):
        x11 = ctypes.cdll.LoadLibrary("libX11.so.6")
        display = x11.XOpenDisplay(None)
        if not display:
            raise tk.TclError("XOpenDisplay failed")
        x11.XReparentWindow(display, wid, pid, 0, 0)
        x11.XFlush(display)
        x11.XCloseDisplay(display)
        try:
            widget.tk.call("place", str(widget), "-in", str(new_parent))
            widget.tk.call("place", "forget", str(widget))
        except tk.TclError:
            pass
        _update_widget_master(widget, new_parent)
    else:  # pragma: no cover - other platforms not implemented
        raise tk.TclError("OS-level reparenting not implemented")
    if widget.master is not new_parent:
        _update_widget_master(widget, new_parent)
