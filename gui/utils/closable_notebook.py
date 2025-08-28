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


import inspect
import logging
import typing as t
import tkinter as tk
import weakref
from tkinter import ttk

logger = logging.getLogger(__name__)


def cancel_after_events(widget: tk.Widget, cancelled: set[str] | None = None) -> None:
    """Cancel Tk ``after`` callbacks tied to *widget*.

    The function inspects both root-level and widget-specific ``after``
    callbacks, removing any entries whose command string contains the Tcl path
    of *widget*.  Command hooks associated with the widget are deleted and
    attributes ending in ``_anim``, ``_after`` or ``_timer`` are cancelled.  The
    operation recurses into child widgets so invoking it on a container will
    clear callbacks for the entire subtree.
    """

    if cancelled is None:
        cancelled = set()

    try:
        root = widget._root()
        tkapp = getattr(root, "tk", None)
        if tkapp is not None and getattr(tkapp, "_tclCommands", None) is not None:
            tcl_name = str(widget)
            try:
                info = tkapp.call("after", "info")
            except Exception:
                info = ()
            if isinstance(info, str):
                info = tkapp.splitlist(info)
            for i in range(0, len(info), 2):
                ident = info[i]
                script = info[i + 1] if i + 1 < len(info) else ""
                if ident in cancelled:
                    continue
                if tcl_name in str(script):
                    try:
                        root.after_cancel(ident)
                    except Exception:
                        pass
                    else:
                        cancelled.add(ident)
            try:
                widget_ids = tkapp.call("after", "info", tcl_name)
            except Exception:
                widget_ids = []
            if isinstance(widget_ids, str):
                widget_ids = [widget_ids]
            for ident in widget_ids:
                if ident in cancelled:
                    continue
                try:
                    widget.after_cancel(ident)
                except Exception:
                    pass
                else:
                    cancelled.add(ident)
            try:
                commands = getattr(tkapp, "_tclCommands", None) or []
                for cmd in list(commands):
                    if tcl_name in cmd:
                        try:
                            tkapp.deletecommand(cmd)
                        except Exception:
                            pass
            except Exception:
                pass
    except Exception:
        pass

    try:
        for name in dir(widget):
            if name.endswith(("_anim", "_after", "_timer")):
                ident = getattr(widget, name, None)
                if isinstance(ident, str) and ident not in cancelled:
                    try:
                        widget.after_cancel(ident)
                    except Exception:
                        pass
                    else:
                        cancelled.add(ident)
    except Exception:
        pass

    for child in widget.winfo_children():
        cancel_after_events(child, cancelled)


# Widget types whose text is only available through ``cget`` even when the
# constructor signature cannot be introspected (e.g. CapsuleButton subclasses)
_KNOWN_TEXT_WIDGETS = {"CapsuleButton"}

class ClosableNotebook(ttk.Notebook):
    """Notebook widget with an 'x' button on the left side of each tab."""

    _style_initialized = False
    _close_img: tk.PhotoImage | None = None
    _tab_hosts: weakref.WeakKeyDictionary[tk.Widget, tk.Toplevel] = weakref.WeakKeyDictionary()

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
            if tab_id in self.tabs():
                try:
                    self.forget(tab_id)
                except tk.TclError:
                    pass
            try:
                self._cancel_after_events(child)
            except Exception:
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

        The method first tries Tk's ``winfo`` reparenting to avoid cloning.  If
        the operation fails, the widget is restored to its original notebook and
        the caller may fall back to cloning.
        """

        text = self.tab(tab_id, "text")
        child = self.nametowidget(tab_id)
        self.forget(tab_id)
        ClosableNotebook._tab_hosts.pop(child, None)
        try:
            try:
                child.tk.call("winfo", "reparent", child._w, target._w)
            except tk.TclError:
                pass
            target.add(child, text=text)
            target.select(child)
            moved = True
        except tk.TclError:
            self.add(child, text=text)
            self.select(child)
            moved = False
        if isinstance(self.master, tk.Toplevel) and not self.tabs():
            self.master.destroy()
        return moved

    def _clone_widget(
        self,
        widget: tk.Widget,
        parent: tk.Widget,
        mapping: dict[tk.Widget, tk.Widget] | None = None,
        layouts: dict[tk.Widget, tuple[str, dict[str, t.Any]]] | None = None,
        cancelled: set[str] | None = None,
    ) -> tuple[
        tk.Widget,
        dict[tk.Widget, tk.Widget],
        dict[tk.Widget, tuple[str, dict[str, t.Any]]],
    ]:
        """Return a clone of *widget* re-parented into *parent*.

        ``mapping`` stores a relation of original widgets to their clones so
        options referencing sibling widgets can later be rewired. ``layouts``
        captures the geometry manager and options of each widget prior to
        cloning so they can be restored on the clone and all descendants.
        """

        if mapping is None:
            mapping = {}
        if layouts is None:
            layouts = {}
        self._cancel_after_events(widget, cancelled)

        try:
            manager = widget.winfo_manager()
        except Exception:  # pragma: no cover - best effort
            manager = ""
        info: dict[str, t.Any] = {}
        try:
            if manager == "pack":
                info = widget.pack_info()
            elif manager == "grid":
                info = widget.grid_info()
            elif manager == "place":
                info = widget.place_info()
        except Exception:
            info = {}
        layouts[widget] = (manager, info)

        cls = widget.__class__
        kwargs = self._collect_required_kwargs(widget, cls)
        # ``widgetName`` is an internal Tk option that propagates to the underlying
        # widget constructor as ``-widgetName``.  Most ttk widgets do not support
        # this option which results in a ``TclError`` when cloning detached tabs.
        # Drop it from the keyword arguments so cloning remains robust.
        kwargs.pop("widgetName", None)

        if isinstance(widget, tk.Canvas):
            clone_cls: type[tk.Canvas] = tk.Canvas
            filtered: dict[str, t.Any] = {}
            if isinstance(widget, CapsuleButton):
                clone_cls = CapsuleButton
                for opt in (
                    "text",
                    "command",
                    "state",
                    "image",
                    "compound",
                    "gradient",
                    "hover_gradient",
                    "hover_bg",
                ):
                    if opt in kwargs:
                        filtered[opt] = kwargs.pop(opt)
            clone = clone_cls(parent, **kwargs)
            mapping[widget] = clone
            self._copy_widget_config(widget, clone)
            self._copy_widget_state(widget, clone)
            if filtered:
                try:
                    clone.configure(**filtered)
                except Exception:
                    pass
            try:
                widget.tk.call("tk::canvas", "copy", widget._w, clone._w)
            except Exception:
                for item in widget.find_all():
                    coords = widget.coords(item)
                    item_type = widget.type(item)
                    opts = widget.itemconfig(item)
                    new_item = getattr(clone, f"create_{item_type}")(*coords)
                    for key, val in opts.items():
                        if isinstance(val, tuple) and len(val) >= 5:
                            clone.itemconfig(new_item, {key: val[4]})
                        elif isinstance(val, str):
                            clone.itemconfig(new_item, {key: val})
            for child in self._ordered_children(widget):
                if child in mapping:
                    continue
                child_clone, mapping, layouts = self._clone_widget(
                    child, clone, mapping, layouts, cancelled
                )
                mapping[child] = child_clone
            try:
                self._cancel_after_events(widget)
            except Exception:
                pass
            try:
                widget.destroy()
            except Exception:
                pass
            self._raise_widgets(widget, clone, mapping)
            return clone, mapping, layouts

        try:
            clone = cls(parent, **kwargs)
        except Exception as exc:  # pragma: no cover - extremely rare
            logger.error("Failed to instantiate %s under %s: %s", widget, parent, exc)
            raise
        mapping[widget] = clone
        self._copy_widget_config(widget, clone)
        self._copy_widget_state(widget, clone)
        for child in self._ordered_children(widget):
            try:
                child_clone, mapping, layouts = self._clone_widget(
                    child, clone, mapping, layouts, cancelled
                )
            except Exception as exc:
                logger.exception("Failed to clone child %s: %s", child, exc)
                raise
            if child_clone is None:
                logger.error("Failed to clone descendant %s", child)
                raise RuntimeError(f"Failed to clone descendant {child}")
            mapping[child] = child_clone

        try:  # Invoke toolbox rebuilds on governance diagram clones
            from gui.windows.architecture import GovernanceDiagramWindow

            if isinstance(clone, GovernanceDiagramWindow):
                orig_toolbox = getattr(widget, "toolbox", getattr(widget, "tools_frame", None))
                clone._rebuild_toolboxes()
                toolbox = getattr(clone, "toolbox", getattr(clone, "tools_frame", None))
                if isinstance(toolbox, tk.Widget):
                    try:
                        toolbox.pack(side="left")
                    except Exception:
                        pass
                    if isinstance(orig_toolbox, tk.Widget):
                        mapping[orig_toolbox] = toolbox
        except Exception:
            pass

        return clone, mapping, layouts


    def _ordered_children(self, widget: tk.Widget) -> list[tk.Widget]:
        """Return children of *widget* in geometry-manager order.

        Tk allows mixing geometry managers within a single container even though
        it is discouraged.  The previous implementation returned the first
        non-empty geometry list which silently dropped widgets managed by other
        strategies, leading to partially cloned tabs where only a subset of
        controls (typically those packed) appeared in the detached window.  To
        ensure every child is cloned we accumulate children from ``pack``,
        ``grid`` and ``place`` while preserving their relative order and falling
        back to ``winfo_children`` for any remaining widgets.
        """

        ordered: list[tk.Widget] = []
        for method in ("pack_slaves", "grid_slaves", "place_slaves"):
            try:
                for child in getattr(widget, method)():
                    if child not in ordered:
                        ordered.append(child)
            except Exception:
                continue

        for child in widget.winfo_children():
            if child not in ordered:
                ordered.append(child)

        return ordered

    def _copy_canvas_items(
        self,
        widget: tk.Canvas,
        clone: tk.Canvas,
        items: t.Iterable[int],
        mapping: dict[tk.Widget, tk.Widget],
        layouts: dict[tk.Widget, tuple[str, dict[str, t.Any]]],
        cancelled: set[str] | None,
    ) -> tuple[dict[tk.Widget, tk.Widget], dict[tk.Widget, tuple[str, dict[str, t.Any]]]]:
        """Clone canvas *items* from *widget* into *clone*.

        ``window`` items are cloned recursively and inserted using
        :meth:`~tkinter.Canvas.create_window` while other item types are
        recreated with the corresponding ``create_*`` method.
        """

        for item in items:
            coords = widget.coords(item)
            item_type = widget.type(item)
            opts = widget.itemconfig(item)
            if item_type == "window":
                path = widget.itemcget(item, "window")
                try:
                    child = widget.nametowidget(path)
                except Exception:
                    continue
                child_clone, mapping, layouts = self._clone_widget(
                    child, clone, mapping, layouts, cancelled
                )
                mapping[child] = child_clone
                cfg = {
                    k: v[4]
                    for k, v in opts.items()
                    if isinstance(v, tuple) and len(v) >= 5
                }
                cfg.pop("window", None)
                clone.create_window(*coords, window=child_clone, **cfg)
            else:
                creator = getattr(clone, f"create_{item_type}")
                new_item = creator(*coords)
                for key, val in opts.items():
                    if isinstance(val, tuple) and len(val) >= 5:
                        clone.itemconfig(new_item, {key: val[4]})
                    elif isinstance(val, str):
                        clone.itemconfig(new_item, {key: val})
        return mapping, layouts

    def _collect_required_kwargs(self, widget: tk.Widget, cls: type) -> dict[str, t.Any]:
        """Return constructor kwargs required to recreate *widget* of type *cls*.

        Some subclasses only expose ``*args``/``**kwargs`` in ``__init__``.  Walk
        the method resolution order to inspect base-class signatures for required
        parameters and fall back to widget introspection for known families like
        ``CapsuleButton`` when no signature information is available.  Optional
        parameters are copied when the widget defines a non-``None`` attribute
        with the same name so detached explorers retain external data sources
        such as ``app`` or ``toolbox``.
        """

        kwargs: dict[str, t.Any] = {}
        for base in inspect.getmro(cls):
            try:
                sig = inspect.signature(base.__init__)
            except Exception:
                continue
            params = list(sig.parameters.items())[1:]
            # Skip bases that only accept *args/**kwargs and provide no
            # information about available parameters.
            if all(
                p.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
                or name == "master"
                for name, p in params
            ):
                continue
            for name, param in params:
                if name == "master":
                    continue
                value = self._get_widget_value(widget, name)
                if param.default is inspect._empty:
                    if value is None and param.annotation in (str, "str"):
                        value = ""
                    if value is not None:
                        kwargs[name] = value
                elif value is not None:
                    kwargs[name] = value
            if kwargs:
                break

        if not kwargs:
            names = {c.__name__ for c in inspect.getmro(cls)}
            if names & _KNOWN_TEXT_WIDGETS:
                try:
                    kwargs["text"] = widget.cget("text")
                except Exception:
                    pass
        return kwargs

    def _get_widget_value(self, widget: tk.Widget, name: str) -> t.Any | None:
        if name in widget.keys():
            try:
                return widget.cget(name)
            except tk.TclError:
                return None
        if hasattr(widget, name):
            return getattr(widget, name)
        if hasattr(widget, f"_{name}"):
            return getattr(widget, f"_{name}")
        return None

    def _copy_widget_config(self, widget: tk.Widget, clone: tk.Widget) -> None:
        try:
            for opt in widget.configure():
                try:
                    clone.configure({opt: widget.cget(opt)})
                except tk.TclError:
                    continue
        except Exception:
            pass

    def _copy_widget_state(self, widget: tk.Widget, clone: tk.Widget) -> None:
        """Copy widget-specific state such as text contents."""
        try:
            if isinstance(widget, (tk.Entry, ttk.Entry)):
                clone.insert(0, widget.get())
            elif isinstance(widget, tk.Text):
                clone.insert("1.0", widget.get("1.0", "end"))
            elif isinstance(widget, tk.Listbox):
                for item in widget.get(0, "end"):
                    clone.insert("end", item)
                for idx in widget.curselection():
                    clone.selection_set(idx)
            elif isinstance(widget, ttk.Treeview):
                for iid in widget.get_children(""):
                    self._copy_tree_item(widget, clone, iid, "")
            elif isinstance(widget, tk.Canvas):
                try:
                    clone.configure(scrollregion=widget.cget("scrollregion"))
                except Exception:
                    pass
                try:
                    sequences = widget.tk.call("bind", widget._w).split()
                    for seq in sequences:
                        cmd = widget.bind(seq)
                        if cmd:
                            clone.bind(seq, cmd)
                except Exception:
                    pass
        except Exception:
            pass

    def _copy_widget_layout(
        self,
        widget: tk.Widget,
        clone: tk.Widget,
        mapping: dict[tk.Widget, tk.Widget],
        layouts: dict[tk.Widget, tuple[str, dict[str, t.Any]]],
    ) -> None:
        """Apply stored geometry options of *widget* to *clone* and descendants."""

        def recurse(src: tk.Widget, dst: tk.Widget) -> None:
            manager, info = layouts.get(src, ("", {}))
            if manager == "pack":
                self._apply_pack_layout(src, dst, mapping, dict(info))
            elif manager == "grid":
                self._apply_grid_layout(src, dst, mapping, dict(info))
            elif manager == "place":
                self._apply_place_layout(src, dst, mapping, dict(info))
            for child in self._ordered_children(src):
                child_clone = mapping.get(child)
                if child_clone is not None:
                    recurse(child, child_clone)

        recurse(widget, clone)

    def _apply_pack_layout(
        self,
        widget: tk.Widget,
        clone: tk.Widget,
        mapping: dict[tk.Widget, tk.Widget],
        info: dict[str, t.Any],
    ) -> None:
        try:
            for key in ("in", "in_"):
                info.pop(key, None)
            for key in ("before", "after"):
                ref = info.get(key)
                if ref:
                    try:
                        ref_widget = widget.nametowidget(ref)
                    except Exception:
                        ref_widget = None
                    clone_ref = mapping.get(ref_widget) if ref_widget else None
                    if clone_ref:
                        info[key] = clone_ref
                    else:
                        info.pop(key, None)
            try:
                clone.pack_forget()
            except Exception:
                pass
            clone.pack(**info)
            try:
                clone.pack_propagate(widget.pack_propagate())
            except Exception:
                pass
        except tk.TclError:
            pass

    def _apply_grid_layout(
        self,
        widget: tk.Widget,
        clone: tk.Widget,
        mapping: dict[tk.Widget, tk.Widget],
        info: dict[str, t.Any],
    ) -> None:
        try:
            for key in ("in", "in_"):
                info.pop(key, None)
            for key in ("before", "after"):
                ref = info.get(key)
                if ref:
                    try:
                        ref_widget = widget.nametowidget(ref)
                    except Exception:
                        ref_widget = None
                    clone_ref = mapping.get(ref_widget) if ref_widget else None
                    if clone_ref:
                        info[key] = clone_ref
                    else:
                        info.pop(key, None)
            try:
                clone.grid_forget()
            except Exception:
                pass
            clone.grid(**info)
            self._configure_grid_weights(widget, clone)
        except tk.TclError:
            pass

    def _configure_grid_weights(self, widget: tk.Widget, clone: tk.Widget) -> None:
        try:
            clone.grid_propagate(widget.grid_propagate())
            cols, rows = widget.grid_size()
            for r in range(rows):
                cfg = widget.grid_rowconfigure(r)
                if cfg:
                    clone.grid_rowconfigure(r, **cfg)
            for c in range(cols):
                cfg = widget.grid_columnconfigure(c)
                if cfg:
                    clone.grid_columnconfigure(c, **cfg)
            if widget is not clone:
                orig_parent = widget.master
                new_parent = clone.master
                try:
                    pcols, prows = orig_parent.grid_size()
                    for r in range(prows):
                        pcfg = orig_parent.grid_rowconfigure(r)
                        weight = pcfg.get("weight") if pcfg else 0
                        if weight:
                            new_parent.grid_rowconfigure(r, weight=weight)
                    for c in range(pcols):
                        pcfg = orig_parent.grid_columnconfigure(c)
                        weight = pcfg.get("weight") if pcfg else 0
                        if weight:
                            new_parent.grid_columnconfigure(c, weight=weight)
                except Exception:
                    pass
        except Exception:
            pass

    def _apply_place_layout(
        self,
        widget: tk.Widget,
        clone: tk.Widget,
        mapping: dict[tk.Widget, tk.Widget],
        info: dict[str, t.Any],
    ) -> None:
        try:
            for key in ("in", "in_"):
                info.pop(key, None)
            for key in ("before", "after"):
                ref = info.get(key)
                if ref:
                    try:
                        ref_widget = widget.nametowidget(ref)
                    except Exception:
                        ref_widget = None
                    clone_ref = mapping.get(ref_widget) if ref_widget else None
                    if clone_ref:
                        info[key] = clone_ref
                    else:
                        info.pop(key, None)
            try:
                clone.place_forget()
            except Exception:
                pass
            clone.place(**info)
        except tk.TclError:
            pass

    def _copy_tree_item(
        self,
        src: ttk.Treeview,
        dst: ttk.Treeview,
        item: str,
        parent: str,
    ) -> None:
        """Recursively copy a tree item from *src* to *dst*."""
        try:
            new_id = dst.insert(
                parent,
                "end",
                text=src.item(item, "text"),
                values=src.item(item, "values"),
                image=src.item(item, "image"),
                open=src.item(item, "open"),
            )
            for child in src.get_children(item):
                self._copy_tree_item(src, dst, child, new_id)
        except Exception:
            pass

    def _cancel_after_events(
        self, widget: tk.Widget, cancelled: set[str] | None = None
    ) -> None:
        """Wrapper for :func:`cancel_after_events` for backward compatibility."""

        cancel_after_events(widget, cancelled)
            
    def _ensure_fills(self, widget: tk.Widget) -> None:
        """Ensure *widget* expands to fill its immediate container.

        Only the geometry of ``widget`` itself is adjusted.  Child widgets keep
        their existing layout configuration regardless of whether they use
        ``pack``, ``grid`` or ``place``.
        """

        try:
            manager = widget.winfo_manager()
        except Exception:
            return

        try:
            if manager == "pack":
                widget.pack_configure(expand=True, fill="both")
            elif manager == "grid":
                widget.grid_configure(sticky="nsew")
            elif manager == "place":
                widget.place_configure(relx=0, rely=0, relwidth=1, relheight=1)
        except tk.TclError:
            pass

    def _raise_widgets(
        self,
        orig: tk.Widget,
        clone: t.Optional[tk.Widget] = None,
        mapping: t.Optional[dict[tk.Widget, tk.Widget]] = None,
        roots: t.Optional[dict[tk.Widget, tk.Widget]] = None,
    ) -> None:
        """Recursively lift *clone* mirroring *orig*'s stacking order.

        When *mapping* is provided the relationship between original widgets
        and their clones is resolved through it.  The list of children from the
        original widget is cached before any destruction so traversal remains
        safe even if the originals vanish during detachment.  ``roots`` allows
        additional original/clone pairs—such as toolbox canvases and buttons—
        to be lifted ahead of the primary traversal.
        """

        if roots:
            for o_root, c_root in roots.items():
                self._raise_widgets(o_root, c_root, mapping)

        target = clone or orig
        try:
            target.lift()
        except Exception:
            pass

        if mapping:
            children: list[tk.Widget]
            try:
                children = list(orig.winfo_children())
            except Exception:
                children = []
            for child_orig in children:
                clone_child = mapping.get(child_orig)
                self._raise_widgets(child_orig, clone_child, mapping)
            return

        for child in target.winfo_children():
            self._raise_widgets(child, child)

    def _detach_tab(self, tab_id: str, x: int, y: int) -> None:
        self.update_idletasks()
        width = self.winfo_width() or 200
        height = self.winfo_height() or 200
        text = self.tab(tab_id, "text")
        root_win = self._app_root
        win = tk.Toplevel(root_win)
        win.transient(root_win)
        win.geometry(f"{width}x{height}+{x}+{y}")
        self._floating_windows.append(win)
        def _on_destroy(_e, w=win) -> None:
            try:
                self._cancel_after_events(w)
            except Exception:
                pass
            if w in self._floating_windows:
                self._floating_windows.remove(w)

        win.bind("<Destroy>", _on_destroy)
        nb = ClosableNotebook(win)
        nb.pack(expand=True, fill="both")
        try:
            if not self._move_tab(tab_id, nb):
                orig = self.nametowidget(tab_id)
                cancelled: set[str] = set()
                self._cancel_after_events(orig, cancelled)
                self.forget(tab_id)
                mapping: dict[tk.Widget, tk.Widget] = {}
                new_widget, mapping, layouts = self._clone_widget(
                    orig, nb, mapping, cancelled=cancelled
                )
                self._cancel_after_events(new_widget, cancelled)
                self._copy_widget_layout(orig, new_widget, mapping, layouts)
                nb.add(new_widget, text=text)
                nb.select(new_widget)
                self._ensure_fills(new_widget)
                self._reassign_widget_references(mapping)
                toolbox_canvas_orig = getattr(orig, "toolbox_canvas", None)
                toolbox_canvas_clone = mapping.get(toolbox_canvas_orig) if mapping else None
                toolbox_orig = getattr(orig, "toolbox", None)
                toolbox_clone = mapping.get(toolbox_orig) if mapping else None
                roots: dict[tk.Widget, tk.Widget] = {}
                if (
                    isinstance(toolbox_canvas_orig, tk.Widget)
                    and isinstance(toolbox_canvas_clone, tk.Widget)
                ):
                    roots[toolbox_canvas_orig] = toolbox_canvas_clone

                try:  # Lazy import to avoid heavy dependency during module load
                    from gui.windows.architecture import GovernanceDiagramWindow
                except Exception:  # pragma: no cover - import errors are non-fatal
                    GovernanceDiagramWindow = None  # type: ignore

                if GovernanceDiagramWindow and isinstance(new_widget, GovernanceDiagramWindow):
                    for name in ("_rebuild_toolboxes", "_switch_toolbox"):
                        func = getattr(new_widget, name, None)
                        if callable(func):
                            try:
                                func()
                            except Exception:
                                pass
                    frame = getattr(new_widget, "toolbox", getattr(new_widget, "tools_frame", None))
                    if isinstance(frame, tk.Widget) and not frame.winfo_manager():
                        try:
                            frame.pack(side="left")
                        except Exception:
                            pass
                elif isinstance(toolbox_clone, tk.Widget) and not toolbox_clone.winfo_manager():
                    try:
                        toolbox_clone.pack(side="left")
                    except Exception:
                        pass

                self._raise_widgets(orig, new_widget, mapping, roots)
                self._cancel_after_events(orig, cancelled)
                orig.destroy()
                toolbar = self._find_toolbar_frame(new_widget)
                if toolbar is not None:
                    mapping.setdefault(toolbar, toolbar)
                self._remove_duplicate_widgets(win, nb, mapping)
                self._reassign_container_attributes(mapping)
                if toolbar is not None and not toolbar.winfo_children():
                    rebuild = getattr(new_widget, "_rebuild_toolbar", None)
                    if callable(rebuild):
                        try:
                            rebuild()
                        except Exception:
                            pass
                for name in ("_rebuild_toolboxes", "_activate_parent_phase"):
                    func = getattr(new_widget, name, None)
                    if callable(func):
                        try:
                            func()
                        except Exception:
                            pass
            else:
                tab = nb.tabs()[-1]
                child = nb.nametowidget(tab)
                self._ensure_fills(child)
                self._raise_widgets(child, child)
                nb.select(tab)
        except Exception:
            win.destroy()
            raise

    def rewrite_option_references(
        self, mapping: dict[tk.Widget, tk.Widget]
    ) -> None:
        """Rewrite widget configuration options to point at cloned widgets."""

        ref_opts = {
            "command",
            "yscrollcommand",
            "xscrollcommand",
            "textvariable",
            "variable",
        }
        name_map = {str(o): str(c) for o, c in mapping.items()}
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
                for src_name, dst_name in name_map.items():
                    if src_name in value:
                        try:
                            clone.configure({opt: value.replace(src_name, dst_name)})
                        except Exception:
                            pass

    def rebind_scrollbars(
        self, mapping: dict[tk.Widget, tk.Widget]
    ) -> None:
        """Rebind cloned scrollbars to their cloned targets."""

        for _orig, clone in mapping.items():
            if not isinstance(clone, tk.Scrollbar):
                continue
            try:
                cmd = clone.cget("command")
            except Exception:
                continue
            if not isinstance(cmd, str) or not cmd:
                continue
            parts = cmd.split()
            target_name = parts[0]
            method = parts[1] if len(parts) > 1 else ""
            try:
                target = clone.nametowidget(target_name)
            except Exception:
                continue
            view = method or (
                "xview" if clone.cget("orient") == "horizontal" else "yview"
            )
            try:
                clone.configure(command=getattr(target, view))
                if view == "xview":
                    target.configure(xscrollcommand=clone.set)
                else:
                    target.configure(yscrollcommand=clone.set)
                target.update_idletasks()
                try:
                    bbox = target.bbox("all")
                    if bbox:
                        target.configure(scrollregion=bbox)
                except Exception:
                    try:
                        target.event_generate("<Configure>")
                    except Exception:
                        pass
            except Exception:
                continue

    def update_canvas_windows(
        self, mapping: dict[tk.Widget, tk.Widget]
    ) -> None:
        """Update canvas window items to point at cloned windows."""

        name_map = {str(o): str(c) for o, c in mapping.items()}
        for _orig, clone in mapping.items():
            if not isinstance(clone, tk.Canvas):
                continue
            if not clone.winfo_exists():
                return
            try:
                for item in clone.find_all():
                    if clone.type(item) != "window":
                        continue
                    old = clone.itemcget(item, "window")
                    new = name_map.get(old)
                    if not new:
                        continue
                    try:
                        clone.itemconfigure(item, window=new)
                    except Exception:
                        pass
            except tk.TclError:
                continue

    def _reassign_widget_references(
        self, mapping: dict[tk.Widget, tk.Widget]
    ) -> None:
        """Rewrite internal widget references after cloning."""

        self.rewrite_option_references(mapping)
        live_mapping = {o: c for o, c in mapping.items() if c.winfo_exists()}
        if live_mapping:
            self.update_canvas_windows(live_mapping)
        self.rebind_scrollbars(mapping)

    def _reassign_container_attributes(
        self, mapping: dict[tk.Widget, tk.Widget]
    ) -> None:
        """Rebind attributes on cloned containers to point at cloned widgets."""

        def _rewrite(value: t.Any) -> t.Any:
            if isinstance(value, tk.Widget):
                return mapping.get(value, value)
            if isinstance(value, dict):
                updated: dict[t.Any, t.Any] = {}
                changed = False
                for k, v in value.items():
                    nk = _rewrite(k)
                    nv = _rewrite(v)
                    changed = changed or nk is not k or nv is not v
                    updated[nk] = nv
                return updated if changed else value
            if isinstance(value, list):
                new_list = [_rewrite(v) for v in value]
                return new_list if any(n is not o for n, o in zip(new_list, value)) else value
            if isinstance(value, tuple):
                new_tuple = tuple(_rewrite(v) for v in value)
                return new_tuple if new_tuple != value else value
            if isinstance(value, set):
                new_set = {_rewrite(v) for v in value}
                return new_set if new_set != value else value
            return value

        for orig, clone in mapping.items():
            module = getattr(orig.__class__, "__module__", "")
            if module.startswith("tkinter"):
                continue
            if not hasattr(orig, "__dict__") or not hasattr(clone, "__dict__"):
                continue
            for name, val in vars(orig).items():
                try:
                    setattr(clone, name, _rewrite(val))
                except Exception:
                    pass

    def _find_toolbar_frame(self, widget: tk.Widget) -> tk.Widget | None:
        """Return the first child frame containing toolbar buttons.

        Explorers construct a toolbar as a frame packed with several buttons.
        When cloning tabs this frame needs to be retained so detached windows
        keep their actions available.  The frame is identified heuristically as
        the first ``Frame`` descendant whose children include any ``Button``
        widgets.
        """

        for child in widget.winfo_children():
            if isinstance(child, (tk.Frame, ttk.Frame)):
                try:
                    if any(
                        isinstance(grand, (tk.Button, ttk.Button))
                        for grand in child.winfo_children()
                    ):
                        return child
                except Exception:
                    continue
        return None

    def _remove_duplicate_widgets(
        self,
        win: tk.Toplevel,
        nb: ttk.Notebook,
        mapping: dict[tk.Widget, tk.Widget],
    ) -> None:
        """Remove widgets that duplicate originals based on parent/child relationships."""

        keep: set[tk.Widget] = {win, nb} | set(mapping.values())
        # Record expected child names for every cloned parent *before* any
        # widgets are destroyed so pruning has a complete view of the original
        # hierarchy. This prevents lookups on partially destroyed widget trees.
        expected: dict[tk.Widget, set[str]] = {}
        reparented: set[tk.Widget] = set()
        for orig, clone in mapping.items():
            if isinstance(orig, tk.Canvas) and not orig.winfo_exists():
                reparented.add(clone)
                continue
            if not orig.winfo_exists():
                continue
            parent_clone = mapping.get(orig.master)
            if parent_clone is not None:
                expected.setdefault(parent_clone, set()).add(clone.winfo_name())
            else:
                reparented.add(clone)

        def prune(parent: tk.Widget) -> None:
            if not parent.winfo_exists():
                return
            for child in list(parent.winfo_children()):
                if not child.winfo_exists():
                    continue
                prune(child)
                if child in keep or child in reparented:
                    continue
                names = expected.get(parent, set())
                if child.winfo_name() in names or (
                    isinstance(child, (tk.Frame, ttk.Frame, ttk.Treeview))
                    and not any(
                        isinstance(gc, (tk.Button, ttk.Button))
                        for gc in child.winfo_children()
                    )
                ):
                    try:
                        self._cancel_after_events(child)
                    except Exception:
                        pass
                    try:
                        child.destroy()
                    except Exception:
                        pass

        prune(win)

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
