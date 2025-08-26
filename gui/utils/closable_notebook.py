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


import tkinter as tk
from tkinter import ttk


class ClosableNotebook(ttk.Notebook):
    """Notebook widget with an 'x' button on the left side of each tab."""

    _style_initialized = False
    _close_img: tk.PhotoImage | None = None

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
                                                        ("close", {"side": "left", "sticky": ""}),
                                                        ("Notebook.label", {"side": "left", "sticky": ""}),
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

    def _on_tab_press(self, event: tk.Event) -> str | None:  # pragma: no cover - thin wrapper
        return self._on_press(event)

    def _on_tab_release(self, event: tk.Event) -> None:  # pragma: no cover - thin wrapper
        self._on_release(event)

    def _on_tab_motion(self, event: tk.Event) -> None:  # pragma: no cover - thin wrapper
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
        if self.instate(["pressed"]):
            element = self.identify(event.x, event.y)
            index = self.index(f"@{event.x},{event.y}")
            if "close" in element and self._active == index:
                tab_id = self.tabs()[index]
                if tab_id in self.protected:
                    self.state(["!pressed"])
                    self._active = None
                    self._reset_drag()
                    return
                self._closing_tab = tab_id
                self.event_generate("<<NotebookTabClosed>>")
                if tab_id in self.tabs():
                    try:
                        self.forget(tab_id)
                    except tk.TclError:
                        pass
            self.state(["!pressed"])
            self._active = None
            self._reset_drag()
            return

        tab_index = self._drag_data["tab"]
        if tab_index is not None:
            outside = (
                event.x < 0
                or event.y < 0
                or event.x >= self.winfo_width()
                or event.y >= self.winfo_height()
            )
            if self._dragging or outside:
                try:
                    tab_id = self.tabs()[tab_index]
                except IndexError:
                    self._reset_drag()
                    return
                widget = self.winfo_containing(event.x_root, event.y_root)
                while widget is not None and not isinstance(widget, ClosableNotebook):
                    widget = widget.master
                if isinstance(widget, ClosableNotebook) and widget is not self:
                    self._move_tab(tab_id, widget)
                else:
                    self._detach_tab(tab_id, event.x_root, event.y_root)
        self._reset_drag()

    def _move_tab(self, tab_id: str, target: "ClosableNotebook") -> bool:
        """Move *tab_id* to *target* notebook.

        The previous implementation relied solely on the various
        ``tk::unsupported::reparent`` commands which are unavailable on some
        platforms, causing the tab to snap back to its source and the floating
        window to vanish immediately.  First try Tk's native ability to add an
        existing child to another notebook which works on standard builds.  If
        that fails fall back to the explicit reparent commands.  When all
        options fail the tab is reinserted into the original notebook so the
        widget remains accessible.
        """

        text = self.tab(tab_id, "text")
        child = self.nametowidget(tab_id)
        self.forget(tab_id)

        try:
            target.add(child, text=text)
            target.select(child)
            moved = True
        except tk.TclError:
            moved = False

        if not moved:
            # Try standard geometry-manager reparenting, which is available on
            # all Tk builds, before falling back to platform specific commands.
            try:
                child.pack_forget()
                child.pack(in_=target)
                child.pack_forget()
                target.add(child, text=text)
                target.select(child)
                moved = True
            except tk.TclError:
                moved = False

        if not moved:
            toplevel = target.winfo_toplevel()
            for cmd in (
                ("::tk::unsupported::reparent", child.winfo_id(), target.winfo_id()),
                ("::tk::unsupported::reparent", child._w, target._w),
                ("::tk::unsupported::reparent", child.winfo_id(), toplevel.winfo_id()),
                ("::tk::unsupported::reparent", child._w, toplevel._w),
                ("tk", "unsupported", "reparent", child.winfo_id(), target.winfo_id()),
                ("tk", "unsupported", "reparent", child._w, target._w),
                ("tk", "unsupported", "reparent", child.winfo_id(), toplevel.winfo_id()),
                ("tk", "unsupported", "reparent", child._w, toplevel._w),
                ("::tk::unsupported::ReparentWindow", child.winfo_id(), target.winfo_id()),
                ("::tk::unsupported::ReparentWindow", child._w, target._w),
                ("::tk::unsupported::ReparentWindow", child.winfo_id(), toplevel.winfo_id()),
                ("::tk::unsupported::ReparentWindow", child._w, toplevel._w),
                ("tk", "unsupported", "ReparentWindow", child.winfo_id(), target.winfo_id()),
                ("tk", "unsupported", "ReparentWindow", child._w, target._w),
                ("tk", "unsupported", "ReparentWindow", child.winfo_id(), toplevel.winfo_id()),
                ("tk", "unsupported", "ReparentWindow", child._w, toplevel._w),
            ):
                try:
                    child.tk.call(*cmd)
                    target.add(child, text=text)
                    target.select(child)
                    moved = True
                    break
                except tk.TclError:
                    continue
        if isinstance(self.master, tk.Toplevel) and not self.tabs():
            self.master.destroy()
        return moved

    def _detach_tab(self, tab_id: str, x: int, y: int) -> None:
        self.update_idletasks()
        width = self.winfo_width() or 200
        height = self.winfo_height() or 200
        child = self.nametowidget(tab_id)
        text = self.tab(tab_id, "text")
        win = tk.Toplevel(self)
        win.geometry(f"{width}x{height}+{x}+{y}")
        self._floating_windows.append(win)
        win.bind(
            "<Destroy>",
            lambda _e, w=win: self._floating_windows.remove(w)
            if w in self._floating_windows
            else None,
        )
        nb = ClosableNotebook(win)
        nb.pack(expand=True, fill="both")
        # ``tk::unsupported::reparent`` requires the target widget to be
        # realised.  Make sure the toplevel and its notebook both exist before
        # attempting to move the tab so that reparenting commands have a valid
        # window to target.
        win.update_idletasks()
        if self._move_tab(tab_id, nb):
            nb.select(child)
            child.update_idletasks()
        else:
            nb.destroy()
            try:
                child.pack(in_=win, expand=True, fill="both")
            except tk.TclError:
                self.add(child, text=text)
                self.select(child)
                if win in self._floating_windows:
                    self._floating_windows.remove(win)
                win.destroy()

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
                    self._drag_root.unbind(
                        "<ButtonRelease-1>", self._drag_root_release
                    )
                except tk.TclError:
                    pass
            self._drag_root = None
            self._drag_root_motion = None
            self._drag_root_release = None
