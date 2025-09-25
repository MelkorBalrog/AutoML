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
import typing as t


GeometryState = tuple[str, dict[str, t.Any]]


def _capture_geometry_state(widget: tk.Widget) -> GeometryState | None:
    """Capture the geometry manager configuration for *widget* if available."""

    manager = ""
    try:
        manager = widget.winfo_manager()
    except Exception:
        manager = ""

    if not manager:
        return None

    fetchers: dict[str, t.Callable[[], dict[str, t.Any]]] = {}

    if hasattr(widget, "pack_info"):
        fetchers["pack"] = widget.pack_info  # type: ignore[assignment]
    if hasattr(widget, "grid_info"):
        fetchers["grid"] = widget.grid_info  # type: ignore[assignment]
    if hasattr(widget, "place_info"):
        fetchers["place"] = widget.place_info  # type: ignore[assignment]

    fetcher = fetchers.get(manager)
    if fetcher is None:
        return None

    try:
        options = fetcher()
    except Exception:
        return None

    if not isinstance(options, dict) or not options:
        return None

    return (manager, dict(options))


def _restore_geometry_state(
    widget: tk.Widget, new_parent: tk.Widget, state: GeometryState | None
) -> None:
    """Restore geometry manager settings for *widget* using *state*."""

    if state is None:
        return

    manager, options = state
    normalised = {
        ("in_" if key == "in" else key): value for key, value in options.items()
    }

    normalised["in_"] = new_parent

    try:
        if manager == "pack" and hasattr(widget, "pack_configure"):
            if hasattr(widget, "pack_forget"):
                try:
                    widget.pack_forget()  # type: ignore[attr-defined]
                except Exception:
                    pass
            widget.pack_configure(**normalised)  # type: ignore[arg-type]
        elif manager == "grid" and hasattr(widget, "grid_configure"):
            if hasattr(widget, "grid_forget"):
                try:
                    widget.grid_forget()  # type: ignore[attr-defined]
                except Exception:
                    pass
            widget.grid_configure(**normalised)  # type: ignore[arg-type]
        elif manager == "place" and hasattr(widget, "place_configure"):
            if hasattr(widget, "place_forget"):
                try:
                    widget.place_forget()  # type: ignore[attr-defined]
                except Exception:
                    pass
            widget.place_configure(**normalised)  # type: ignore[arg-type]
    except Exception:
        return


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


def _sync_widget_parents(widget: tk.Widget, new_parent: tk.Widget) -> None:
    """Synchronise Python-level parent references after reparenting."""

    try:
        old_parent = getattr(widget, "master", None)
    except Exception:
        old_parent = None

    if old_parent is new_parent:
        return

    name = getattr(widget, "_name", None)

    if name and hasattr(old_parent, "children"):
        try:
            old_parent.children.pop(name, None)
        except Exception:
            pass

    try:
        widget.master = new_parent
    except Exception:
        pass

    if name and hasattr(new_parent, "children"):
        try:
            new_parent.children[name] = widget
        except Exception:
            pass


def _notify_tk_reparent(widget: tk.Widget, new_parent: tk.Widget) -> None:
    """Inform Tk that *widget* now belongs to *new_parent*."""

    try:
        widget.place(in_=new_parent)
        widget.place_forget()
    except Exception:
        try:
            widget.tk.call("place", str(widget), "-in", str(new_parent))
            widget.tk.call("place", "forget", str(widget))
        except Exception:
            pass

    _sync_widget_parents(widget, new_parent)


def reparent_widget(widget: tk.Widget, new_parent: tk.Widget) -> None:
    """Reparent *widget* into *new_parent* using OS-level APIs."""

    if widget is new_parent or widget.master is new_parent:
        return

    geometry_state = _capture_geometry_state(widget)
    widget.update_idletasks()
    new_parent.update_idletasks()
    wid = int(widget.winfo_id())
    pid = int(new_parent.winfo_id())

    # First try Tk's cross-platform reparent command if available
    try:
        widget.tk.call("tk::unsupported::reparent", str(widget), str(new_parent))
    except tk.TclError:
        pass
    else:
        _notify_tk_reparent(widget, new_parent)
        _restore_geometry_state(widget, new_parent, geometry_state)
        return

    if sys.platform.startswith("win"):
        if ctypes.windll.user32.SetParent(wid, pid) == 0:
            # Fallback to Tk geometry manager when OS-level reparenting fails
            try:
                widget.place(in_=new_parent)
                widget.place_forget()
            except tk.TclError as exc:
                raise tk.TclError("SetParent failed") from exc
            raise tk.TclError("SetParent failed")
        _notify_tk_reparent(widget, new_parent)
        _restore_geometry_state(widget, new_parent, geometry_state)
    elif sys.platform.startswith("linux"):
        x11 = ctypes.cdll.LoadLibrary("libX11.so.6")
        display = x11.XOpenDisplay(None)
        if not display:
            raise tk.TclError("XOpenDisplay failed")
        try:
            x11.XReparentWindow(display, wid, pid, 0, 0)
            x11.XFlush(display)
        finally:
            x11.XCloseDisplay(display)
        _notify_tk_reparent(widget, new_parent)
        _restore_geometry_state(widget, new_parent, geometry_state)
    else:  # pragma: no cover - other platforms not implemented
        raise tk.TclError("OS-level reparenting not implemented")
