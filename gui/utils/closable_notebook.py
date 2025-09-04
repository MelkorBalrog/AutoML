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

"""Custom ttk.Notebook widget with detachable tabs.

The widget behaves like a regular :class:`ttk.Notebook` but displays a close
button on the left of each tab. Tabs can also be dragged out of the notebook to
create a new floating window. Dragging a tab from a floating window back onto a
notebook re-attaches it to that notebook.
"""


import logging
import typing as t
import tkinter as tk
import weakref
import re
from tkinter import ttk
try:  # pragma: no cover - allow local imports in tests
    from .widget_transfer_manager import WidgetTransferManager
except Exception:  # pragma: no cover - fallback when run as script
    from widget_transfer_manager import WidgetTransferManager

logger = logging.getLogger(__name__)


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


class ClosableNotebook(ttk.Notebook):
    """Notebook widget with an 'x' button on the left side of each tab."""

    _style_initialized = False
    _close_img: tk.PhotoImage | None = None
    _tab_hosts: weakref.WeakKeyDictionary[tk.Widget, tk.Toplevel] = (
        weakref.WeakKeyDictionary()
    )

    def __init__(self, master: tk.Widget | None = None, **kw):
        if not ClosableNotebook._style_initialized:
            # Create the close button image and register style elements only once
            ClosableNotebook._close_img = self._create_close_image()
            style = ttk.Style()
            style.element_create(
                "close",
                "image",
                ClosableNotebook._close_img,
                border=8,
                sticky="",
            )
            style.layout(
                "ClosableNotebook.Tab",
                [
                    (
                        "Notebook.tab",
                        {
                            "sticky": "nswe",
                            "children": [
                                (
                                    "Notebook.padding",
                                    {
                                        "side": "top",
                                        "sticky": "nswe",
                                        "children": [
                                            (
                                                "Notebook.focus",
                                                {
                                                    "side": "top",
                                                    "sticky": "nswe",
                                                    "children": [
                                                        (
                                                            "close",
                                                            {
                                                                "side": "left",
                                                                "sticky": "",
                                                            },
                                                        ),
                                                        (
                                                            "Notebook.label",
                                                            {
                                                                "side": "left",
                                                                "sticky": "",
                                                            },
                                                        ),
                                                    ],
                                                },
                                            )
                                        ],
                                    },
                                )
                            ],
                        },
                    )
                ],
            )
            style.layout("ClosableNotebook", style.layout("TNotebook"))
            ClosableNotebook._style_initialized = True
        kw["style"] = "ClosableNotebook"
        super().__init__(master, **kw)
        self._active: int | None = None
        self._closing_tab: str | None = None
        self.protected: set[str] = set()
        self._drag_data: dict[str, int | None] = {"tab": None, "x": 0, "y": 0}
        self._dragging = False

        # ------------------------------------------------------------------
        # Data loading/unloading strategy handling
        # ------------------------------------------------------------------
        # A small strategy system is used to experiment with different ways of
        # loading and unloading tab data on focus changes.  The active strategy
        # is selected via the ``AUTOML_DATA_STRATEGY`` environment variable to
        # make it easy for tests to exercise all implementations.  Strategy 4
        # is the default and most feature complete option.
        import os

        try:
            self._data_strategy = int(os.environ.get("AUTOML_DATA_STRATEGY", "4"))
        except ValueError:
            self._data_strategy = 4
        self._focused_tab: str | None = None
        # Cache application root so floating windows always attach to the main
        # window even when this notebook resides in a detached toplevel.
        self._app_root = self._root()
        # ``_root_bindings`` store identifiers for bindings that temporarily
        # attach to the containing toplevel while a drag operation is active.
        # This ensures that we still receive ``<B1-Motion>`` and
        # ``<ButtonRelease-1>`` events even when the pointer is dragged outside
        # of the notebook's visible area.  The internal Tk widget base class
        # defines a ``_root()`` method which returns the containing toplevel.
        # A previous version of this class used an attribute named ``_root`` to
        # keep track of the bound toplevel and inadvertently shadowed that
        # method.  When Tk's event dispatch code later attempted to call
        # ``_root()`` it ended up invoking the attribute instead, resulting in a
        # ``TypeError: 'NoneType' object is not callable``.  Use distinct names
        # for our bookkeeping attributes to avoid clashing with Tk internals.
        self._drag_root: tk.Misc | None = None
        self._drag_root_motion: str | None = None
        self._drag_root_release: str | None = None
        self._floating_windows: list[tk.Toplevel] = []

        self.bind("<ButtonPress-1>", self._on_press, True)
        self.bind("<B1-Motion>", self._on_motion)
        self.bind("<ButtonRelease-1>", self._on_release, True)
        # Refresh the newly selected tab whenever focus changes
        self.bind("<<NotebookTabChanged>>", self._on_tab_changed, True)
        self.bind("<FocusIn>", self._on_focus_in, True)

    # ------------------------------------------------------------------
    # Tab management
    # ------------------------------------------------------------------

    def add(self, child: tk.Widget, **kw: t.Any) -> None:  # type: ignore[override]
        host = ClosableNotebook._tab_hosts.get(child)
        if host is not None and host.winfo_exists():
            host.deiconify()
            host.lift()
            try:
                host.focus_force()
            except tk.TclError:
                pass
            return
        super().add(child, **kw)
        if isinstance(self.master, tk.Toplevel):
            ClosableNotebook._tab_hosts[child] = self.master

            def _forget(_e: tk.Event, w: tk.Widget = child) -> None:
                ClosableNotebook._tab_hosts.pop(w, None)

            self.master.bind("<Destroy>", _forget, add="+")
        else:
            ClosableNotebook._tab_hosts.pop(child, None)

    # ------------------------------------------------------------------
    # Floating window helpers
    # ------------------------------------------------------------------

    def close_all_floating(self) -> None:
        """Destroy every floating window detached from this notebook."""
        for win in list(self._floating_windows):
            try:
                self._cancel_after_events(win)
            except Exception:
                pass
            try:
                win.destroy()
            except Exception:
                pass
        self._floating_windows.clear()

    # ------------------------------------------------------------------
    # Backwards compatible helpers
    # ------------------------------------------------------------------
    #
    # Older code as well as the unit tests in this repository expect the
    # notebook to expose ``_on_tab_press`` and ``_on_tab_release`` methods
    # that behave like the bound event handlers above.  The original file
    # was refactored to use the shorter ``_on_press``/``_on_release`` names
    # but the helper methods were accidentally dropped.  Without them the
    # tests fail with ``AttributeError`` and dragging a tab programmatically
    # is impossible.  Provide tiny wrappers so the old API continues to
    # work.

    def _on_tab_press(
        self, event: tk.Event
    ) -> str | None:  # pragma: no cover - thin wrapper
        return self._on_press(event)

    def _on_tab_release(
        self, event: tk.Event
    ) -> None:  # pragma: no cover - thin wrapper
        self._on_release(event)

    def _on_tab_motion(
        self, event: tk.Event
    ) -> None:  # pragma: no cover - thin wrapper
        self._on_motion(event)

    # ------------------------------------------------------------------
    # Tab focus handling
    # ------------------------------------------------------------------

    def _on_tab_changed(self, _event: tk.Event) -> None:
        self._handle_tab_focus()

    def _on_focus_in(self, _event: tk.Event) -> None:
        self._handle_tab_focus()

    def _handle_tab_focus(self) -> None:
        """Handle data loading/unloading and refresh for the active tab."""
        current = self.select()
        if not current:
            return
        try:
            widget = self.nametowidget(current)
        except Exception:
            return

        # Dispatch to the chosen strategy.  Each strategy aims to only keep the
        # data for the focused tab in memory.
        strategies = {
            1: self._strategy_load_only,
            2: self._strategy_swap_load_unload,
            3: self._strategy_event_based,
            4: self._strategy_swap_event_based,
        }
        strategies.get(self._data_strategy, self._strategy_swap_event_based)(widget)

        # Existing refresh behaviour retained for backward compatibility
        for name in ("refresh_from_repository", "populate"):
            method = getattr(widget, name, None)
            if callable(method):
                method()
                break

    # ------------------------------------------------------------------
    # Data loading/unloading strategies
    # ------------------------------------------------------------------

    def _get_widget(self, widget_id: str) -> tk.Widget | None:
        try:
            return self.nametowidget(widget_id)
        except Exception:
            return None

    def _call_method(self, widget: tk.Widget | None, name: str) -> None:
        if not widget:
            return
        method = getattr(widget, name, None)
        if callable(method):
            method()

    def _strategy_load_only(self, widget: tk.Widget) -> None:
        """Strategy 1: load data for the active tab only."""
        self._call_method(widget, "load_data")
        self._focused_tab = self.select()

    def _strategy_swap_load_unload(self, widget: tk.Widget) -> None:
        """Strategy 2: load current tab and unload previous tab."""
        current = self.select()
        if self._focused_tab and self._focused_tab != current:
            prev = self._get_widget(self._focused_tab)
            self._call_method(prev, "unload_data")
        self._call_method(widget, "load_data")
        self._focused_tab = current

    def _strategy_event_based(self, widget: tk.Widget) -> None:
        """Strategy 3: notify tabs via events."""
        current = self.select()
        if self._focused_tab and self._focused_tab != current:
            prev = self._get_widget(self._focused_tab)
            if prev:
                prev.event_generate("<<TabUnloaded>>")
        widget.event_generate("<<TabLoaded>>")
        self._focused_tab = current

    def _strategy_swap_event_based(self, widget: tk.Widget) -> None:
        """Strategy 4: combine method calls with events."""
        current = self.select()
        if self._focused_tab and self._focused_tab != current:
            prev = self._get_widget(self._focused_tab)
            self._call_method(prev, "unload_data")
            if prev:
                prev.event_generate("<<TabUnloaded>>")
        self._call_method(widget, "load_data")
        widget.event_generate("<<TabLoaded>>")
        self._focused_tab = current

    def _create_close_image(self, size: int = 10) -> tk.PhotoImage:
        img = tk.PhotoImage(width=size, height=size)
        img.put("white", to=(0, 0, size - 1, size - 1))
        for i in range(size):
            img.put("black", (i, i))
            img.put("black", (size - 1 - i, i))
        return img

    def _on_press(self, event: tk.Event) -> str | None:
        element = self.identify(event.x, event.y)
        try:
            index = self.index(f"@{event.x},{event.y}")
        except tk.TclError:
            index = None
        if "close" in element and index is not None:
            tab_id = self.tabs()[index]
            if tab_id in self.protected:
                return "break"
            self.state(["pressed"])
            self._active = index
            return "break"

        self._drag_data = {"tab": index, "x": event.x_root, "y": event.y_root}
        # While the mouse button is held down we want to continue receiving
        # motion and release events even if the pointer leaves the notebook's
        # area.  Temporarily bind to the toplevel that contains this notebook
        # so those events are forwarded to the handlers below.  The bindings
        # are removed again in ``_reset_drag`` once the drag operation ends.
        self._drag_root = self.winfo_toplevel()
        self._drag_root_motion = self._drag_root.bind(
            "<B1-Motion>", self._on_motion, add="+"
        )
        self._drag_root_release = self._drag_root.bind(
            "<ButtonRelease-1>", self._on_release, add="+"
        )
        return None

    def _on_motion(self, event: tk.Event) -> None:
        if self._drag_data["tab"] is None:
            return
        dx = abs(event.x_root - self._drag_data["x"])
        dy = abs(event.y_root - self._drag_data["y"])
        if dx > 5 or dy > 5:
            self._dragging = True

    def _on_release(self, event: tk.Event) -> None:
        if self._handle_close(event):
            return
        tab_index = self._drag_data["tab"]
        if tab_index is not None:
            self._finalize_drag(tab_index, event)
        self._reset_drag()

    def _handle_close(self, event: tk.Event) -> bool:
        if not self.instate(["pressed"]):
            return False
        element = self.identify(event.x, event.y)
        index = self.index(f"@{event.x},{event.y}")
        if "close" in element and self._active == index:
            tab_id = self.tabs()[index]
            if tab_id in self.protected:
                self.state(["!pressed"])
                self._active = None
                self._reset_drag()
                return True
            child = self.nametowidget(tab_id)
            self._closing_tab = tab_id
            self.event_generate("<<NotebookTabClosed>>")
            try:
                self._cancel_after_events(child)
            except Exception:
                pass
            if tab_id in self.tabs():
                try:
                    self.forget(tab_id)
                except tk.TclError:
                    pass
            try:
                child.destroy()
            except Exception:
                pass
        self.state(["!pressed"])
        self._active = None
        self._reset_drag()
        return True

    def _finalize_drag(self, tab_index: int, event: tk.Event) -> None:
        if not (self._dragging or self._is_outside(event)):
            return
        try:
            tab_id = self.tabs()[tab_index]
        except IndexError:
            return
        target = self._target_notebook(event.x_root, event.y_root)
        if target is None:
            # No notebook could be resolved under the pointer; detach to a
            # floating window instead of raising ``TclError`` or ``KeyError``.
            self._detach_tab(tab_id, event.x_root, event.y_root)
            return
        if target is self:
            # Dropping back onto the originating notebook requires no action.
            return
        self._move_tab(tab_id, target)

    def _is_outside(self, event: tk.Event) -> bool:
        return (
            event.x < 0
            or event.y < 0
            or event.x >= self.winfo_width()
            or event.y >= self.winfo_height()
        )

    def _target_notebook(self, x: int, y: int) -> t.Optional["ClosableNotebook"]:
        """Return the notebook under screen coordinates ``(x, y)``.

        ``winfo_containing`` may raise ``TclError`` or ``KeyError`` when the
        underlying widget hierarchy changes during a drag operation (for
        instance if a widget is destroyed mid-drag).  In such cases ``None`` is
        returned so callers can gracefully fall back to detaching the tab.
        """

        try:
            widget = self.winfo_containing(x, y)
        except (tk.TclError, KeyError):
            return None
        while widget is not None and not isinstance(widget, ClosableNotebook):
            widget = widget.master
        return widget

    def _move_tab(self, tab_id: str, target: "ClosableNotebook") -> bool:
        """Move *tab_id* to *target* notebook using Tk's native commands.

        ``after`` callbacks tied to the tab are cancelled before any widgets
        are forgotten to avoid orphaned Tcl commands such as ``*_animate``.
        On failure, the tab is fully restored to its source notebook and a
        :class:`RuntimeError` is raised instead of falling back to cloning.
        """

        text = self.tab(tab_id, "text")
        child = self.nametowidget(tab_id)
        index = self.index(tab_id)

        def _safe_forget(nb: "ClosableNotebook", widget: tk.Widget) -> None:
            if widget.master is nb or str(widget) in nb.tabs():
                try:
                    self._cancel_after_events(widget)
                except Exception:
                    pass
                try:
                    nb.forget(widget)
                except tk.TclError:
                    # Tcl may destroy the notebook between the failed add and
                    # the cleanup. This previously surfaced as:
                    #   TclError: can't invoke "ttk::notebook" command:
                    #             application has been destroyed
                    # Guard the call so race conditions do not bubble up.
                    pass

        def _restore() -> None:
            self.add(child, text=text)
            if self.index(child) != index:
                self.insert(index, child)
            self.select(child)

        try:
            self._cancel_after_events(child)
        except Exception:
            pass
        self.forget(tab_id)
        ClosableNotebook._tab_hosts.pop(child, None)
        try:
            try:
                child.tk.call("winfo", "reparent", child._w, target._w)
            except tk.TclError:
                pass
            target.add(child, text=text)
            target.select(child)
        except tk.TclError as exc:
            _safe_forget(target, child)
            _restore()
            logger.error("Failed to move tab %s: %s", child, exc)
            raise RuntimeError(f"Failed to move tab {child}") from exc
        moved = child.master is target
        if not moved:
            _safe_forget(target, child)
            _restore()
            logger.error("Tab %s was not reparented to %s", child, target)
            raise RuntimeError(f"Failed to move tab {child}")
        if isinstance(self.master, tk.Toplevel) and not self.tabs():
            try:
                self._cancel_after_events(self.master)
            except Exception:
                pass
            self.master.destroy()
        return True

    def _detach_tab(self, tab_id: str, x: int, y: int) -> None:
        """Detach *tab_id* into a new floating window at *(x, y)*.

        Tk ``after`` callbacks tied to the original tab are cancelled before it
        is forgotten to prevent orphaned Tcl commands such as ``*_animate``.
        """

        from .detached_window import DetachedWindow

        text = self.tab(tab_id, "text")
        self.update_idletasks()
        width = self.winfo_width() or 200
        height = self.winfo_height() or 200
        dw = DetachedWindow(self._app_root, width, height, x, y)
        self._floating_windows.append(dw.win)

        def _on_destroy(_e, w=dw.win) -> None:
            try:
                self._cancel_after_events(w)
            except Exception:
                pass
            if w in self._floating_windows:
                self._floating_windows.remove(w)

        dw.win.bind("<Destroy>", _on_destroy, add="+")

        manager = WidgetTransferManager(self)
        child = manager.detach_tab(tab_id, dw.nb)
        dw._ensure_toolbox(child)
        dw._activate_hooks(child)


    def _replace_widget_paths(
        self, script: str, mapping: dict[tk.Widget, tk.Widget]
    ) -> str:
        """Return *script* with widget paths replaced per *mapping*."""

        name_pairs = sorted(
            ((str(o), str(c)) for o, c in mapping.items()),
            key=lambda x: -len(x[0]),
        )
        for src, dst in name_pairs:
            script = re.sub(
                rf"(?<!\S){re.escape(src)}(?!\S)",
                dst,
                script,
            )
        return script

    def rewrite_option_references(self, mapping: dict[tk.Widget, tk.Widget]) -> None:
        """Rewrite widget configuration options to point at cloned widgets."""

        ref_opts = {
            "command",
            "yscrollcommand",
            "xscrollcommand",
            "textvariable",
            "variable",
            "postcommand",
        }
        for _orig, clone in mapping.items():
            try:
                config = clone.configure() or {}
            except Exception:
                continue
            if not isinstance(config, dict):
                continue
            for opt in ref_opts:
                if opt not in config:
                    continue
                try:
                    value = clone.cget(opt)
                except Exception:
                    continue
                if not isinstance(value, str):
                    continue
                new_value = self._replace_widget_paths(value, mapping)
                if new_value != value:
                    try:
                        clone.configure({opt: new_value})
                    except Exception:
                        pass
            if isinstance(clone, tk.Menu):
                try:
                    end = clone.index("end") or -1
                except Exception:
                    end = -1
                for i in range(end + 1):
                    try:
                        cmd = clone.entrycget(i, "command")
                    except Exception:
                        continue
                    if not isinstance(cmd, str):
                        continue
                    new_cmd = self._replace_widget_paths(cmd, mapping)
                    if new_cmd != cmd:
                        try:
                            clone.entryconfigure(i, command=new_cmd)
                        except Exception:
                            pass

    def _reset_drag(self) -> None:
        self._drag_data = {"tab": None, "x": 0, "y": 0}
        self._dragging = False
        if self._drag_root is not None:
            if self._drag_root_motion:
                try:
                    self._drag_root.unbind("<B1-Motion>", self._drag_root_motion)
                except tk.TclError:
                    pass
            if self._drag_root_release:
                try:
                    self._drag_root.unbind("<ButtonRelease-1>", self._drag_root_release)
                except tk.TclError:
                    pass
            self._drag_root = None
            self._drag_root_motion = None
            self._drag_root_release = None
