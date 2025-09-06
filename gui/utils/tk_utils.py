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
import logging
import tkinter as tk
import typing as t


logger = logging.getLogger(__name__)


def cancel_after_events(widget: tk.Widget, cancelled: set[str] | None = None) -> None:
    """Cancel Tk ``after`` callbacks tied to *widget* and its children."""

    if cancelled is None:
        cancelled = set()

    tkapp = getattr(widget, "tk", None)
    if tkapp is None or getattr(tkapp, "call", None) is None:
        return

    root = _safe_root(widget)
    tcl_cmds = getattr(root, "_tclCommands", None) if root else None

    def _delete_command(cmd: str | None) -> None:
        if not cmd or not tcl_cmds or cmd not in tcl_cmds:
            return
        try:
            root.deletecommand(cmd)  # type: ignore[union-attr]
        except Exception:
            logger.debug("Failed to delete Tcl command %s", cmd, exc_info=True)

    def _cancel_ident(ident: str, script: str | None = None) -> None:
        try:
            tkapp.call("after", "cancel", ident)
        except Exception:
            logger.debug("Failed to cancel 'after' id %s", ident, exc_info=True)
            return
        cancelled.add(ident)
        for cmd in (ident, script):
            _delete_command(cmd)
        try:
            tkapp.call("after", "info", ident)
            logger.debug("Unhandled after id still scheduled: %s", ident)
        except Exception:
            pass

    _cancel_widget_ids(widget, tkapp, _cancel_ident, cancelled)
    _cancel_global_ids(widget, tkapp, _cancel_ident, cancelled)
    _cancel_widget_attrs(widget, _cancel_ident, cancelled)
    _purge_widget_scripts(widget, root, tcl_cmds)

    for child in widget.winfo_children():
        cancel_after_events(child, cancelled)


def _safe_root(widget: tk.Widget) -> tk.Tk | None:
    try:
        return widget._root()  # type: ignore[attr-defined]
    except Exception:
        return None


def _info_script(tkapp: tk.Misc, ident: str) -> str | None:
    try:
        return tkapp.call("after", "info", ident)
    except Exception:
        return None


def _cancel_widget_ids(
    widget: tk.Widget,
    tkapp: tk.Misc,
    cancel: t.Callable[[str, str | None], None],
    cancelled: set[str],
) -> None:
    try:
        widget_ids = tkapp.call("after", "info", str(widget))
    except Exception:
        return
    if isinstance(widget_ids, str):
        widget_ids = (widget_ids,)
    for ident in widget_ids:
        if ident and ident not in cancelled:
            script = _info_script(tkapp, ident)
            cancel(ident, script if isinstance(script, str) else None)


def _cancel_global_ids(
    widget: tk.Widget,
    tkapp: tk.Misc,
    cancel: t.Callable[[str, str | None], None],
    cancelled: set[str],
) -> None:
    try:
        all_ids = tkapp.call("after", "info")
    except Exception:
        return
    if isinstance(all_ids, str):
        all_ids = (all_ids,)
    wid = str(widget)
    for ident in all_ids:
        if not isinstance(ident, str) or ident in cancelled:
            continue
        if ident.startswith(wid):
            script = _info_script(tkapp, ident)
            cancel(ident, script if isinstance(script, str) else None)
            continue
        script = _info_script(tkapp, ident)
        if isinstance(script, str) and wid in script:
            cancel(ident, script)


def _cancel_widget_attrs(
    widget: tk.Widget,
    cancel: t.Callable[[str, str | None], None],
    cancelled: set[str],
) -> None:
    try:
        for name in dir(widget):
            if name.endswith(("_anim", "_after", "_timer", "_animate")):
                ident = getattr(widget, name, None)
                if isinstance(ident, str) and ident not in cancelled:
                    script = _info_script(widget.tk, ident)
                    cancel(ident, script if isinstance(script, str) else None)
    except Exception:
        logger.debug("Failed scanning widget attributes for after ids", exc_info=True)


def _purge_widget_scripts(
    widget: tk.Widget,
    root: tk.Tk | None,
    tcl_cmds: dict[str, t.Any] | None,
) -> None:
    if not root or not tcl_cmds:
        return
    wid = str(widget)
    for name in list(tcl_cmds):
        try:
            func = tcl_cmds[name]
            if wid in name or wid in repr(func):
                root.deletecommand(name)
        except Exception:
            logger.debug("Failed to purge Tcl command %s", name, exc_info=True)


def reparent_widget(widget: tk.Widget, new_parent: tk.Widget) -> None:
    """Reparent *widget* into *new_parent*'s toplevel window."""

    wid = int(widget.winfo_id())
    pid = int(new_parent.winfo_toplevel().winfo_id())
    tkapp = widget.tk
    success = False
    errors: list[str] = []

    try:
        if tkapp.call(
            "info", "commands", "::tk::unsupported::ReparentWindow"
        ):
            try:
                tkapp.call(
                    "::tk::unsupported::ReparentWindow",
                    widget._w,
                    new_parent.winfo_toplevel()._w,
                )
                success = True
            except tk.TclError as exc:
                errors.append(f"ReparentWindow failed: {exc}")
    except tk.TclError as exc:  # pragma: no cover - command lookup failure
        errors.append(f"ReparentWindow lookup failed: {exc}")

    if sys.platform.startswith("win"):
        if ctypes.windll.user32.SetParent(wid, pid) != 0:
            success = True
        else:
            errors.append("SetParent failed")
    elif not success:  # pragma: no cover - non-Windows platforms
        errors.append("OS-level reparenting not implemented")

    if not success:
        raise tk.TclError("; ".join(errors) if errors else "reparenting failed")
