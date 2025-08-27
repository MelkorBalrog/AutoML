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

"""Simple canvas window with toolbox for editing GSN diagrams."""

import csv
import tkinter as tk
from tkinter import ttk, simpledialog, filedialog
import webbrowser
import os
import sys
import subprocess
import copy
import json
import weakref
from pathlib import Path
from typing import Optional

from mainappsrc.models.gsn import GSNNode, GSNDiagram
from .gsn_config_window import GSNElementConfig
from gui.dialogs.gsn_connection_config import GSNConnectionConfig
from gui.controls import messagebox
from gui.styles.style_manager import StyleManager
from gui.utils.icon_factory import create_icon
from gui.controls.button_utils import set_uniform_button_width, max_button_reqwidth
from gui import TranslucidButton

GSN_WINDOWS: set[weakref.ReferenceType] = set()


class ModuleSelectDialog(simpledialog.Dialog):  # pragma: no cover - requires tkinter
    """Simple dialog presenting a read-only list of module names."""

    def __init__(self, parent, title: str, options: list[str]):
        self.options = options
        self.selection = ""
        super().__init__(parent, title)

    def body(self, master):  # pragma: no cover - requires tkinter
        ttk.Label(master, text="Module:").pack(padx=5, pady=5)
        self.var = tk.StringVar(value=self.options[0] if self.options else "")
        combo = ttk.Combobox(
            master,
            textvariable=self.var,
            values=self.options,
            state="readonly",
        )
        combo.pack(padx=5, pady=5)
        return combo

    def apply(self):  # pragma: no cover - requires tkinter
        self.selection = self.var.get()


class GSNDiagramWindow(tk.Frame):
    """Display a :class:`GSNDiagram` inside a notebook tab with basic tools."""

    TOOLBOX_BUTTONS = [
        "Goal",
        "Strategy",
        "Solution",
        "Assumption",
        "Justification",
        "Context",
        "Module",
        "Solved By",
        "In Context Of",
        "Zoom In",
        "Zoom Out",
        "Export CSV",
    ]

    def __init__(self, master, app, diagram: GSNDiagram, icon_size: int = 16):
        super().__init__(master)
        self.app = app
        self.diagram = diagram
        self.icon_size = icon_size

        # toolbox with buttons to add nodes and connectors
        self.toolbox_container = ttk.Frame(self)
        self.toolbox_container.pack(side=tk.LEFT, fill=tk.Y)
        self.toolbox_canvas = tk.Canvas(self.toolbox_container, highlightthickness=0)
        self.toolbox_canvas.pack(side=tk.LEFT, fill=tk.Y, expand=True)
        self.toolbox_scroll = ttk.Scrollbar(
            self.toolbox_container, orient=tk.VERTICAL, command=self.toolbox_canvas.yview
        )
        self.toolbox_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.toolbox_canvas.configure(yscrollcommand=self.toolbox_scroll.set)
        self.toolbox = ttk.Frame(self.toolbox_canvas)
        self._toolbox_window = self.toolbox_canvas.create_window(
            (0, 0), window=self.toolbox, anchor="nw"
        )
        self.toolbox.bind(
            "<Configure>",
            lambda e: self.toolbox_canvas.configure(
                scrollregion=self.toolbox_canvas.bbox("all"), width=e.width
            ),
        )

        style = StyleManager.get_instance()

        def _color(name: str, default: str) -> str:
            c = style.get_color(name)
            return default if c == "#FFFFFF" else c

        self._icons = {
            "Goal": create_icon("rect", _color("Goal", "#2e8b57"), size=self.icon_size),
            "Strategy": create_icon(
                "parallelogram", _color("Strategy", "#8b008b"), size=self.icon_size
            ),
            "Solution": create_icon("circle", _color("Solution", "#1e90ff"), size=self.icon_size),
            "Assumption": create_icon(
                "ellipse", _color("Assumption", "#b22222"), size=self.icon_size
            ),
            "Justification": create_icon(
                "ellipse", _color("Justification", "#ff8c00"), size=self.icon_size
            ),
            "Context": create_icon("ellipse", _color("Context", "#696969"), size=self.icon_size),
            "Module": create_icon("folder", _color("Module", "#b8860b"), size=self.icon_size),
            "Solved By": create_icon("arrow", _color("Solved By", "black"), size=self.icon_size),
            "In Context Of": create_icon(
                "relation", _color("In Context Of", "black"), size=self.icon_size
            ),
            "Zoom In": create_icon("plus", "black", size=self.icon_size),
            "Zoom Out": create_icon("minus", "black", size=self.icon_size),
            "Export CSV": create_icon("disk", "black", size=self.icon_size),
        }

        node_cmds = [
            ("Goal", self.add_goal),
            ("Strategy", self.add_strategy),
            ("Solution", self.add_solution),
            ("Assumption", self.add_assumption),
            ("Justification", self.add_justification),
            ("Context", self.add_context),
            ("Module", self.add_module),
        ]
        try:
            node_frame = ttk.LabelFrame(
                self.toolbox,
                text="Elements",
                style="Toolbox.TLabelframe",
            )
        except TypeError:
            node_frame = ttk.LabelFrame(
                self.toolbox,
                text="Elements",
            )
        node_frame.pack(side=tk.TOP, fill=tk.X)
        for name, cmd in node_cmds:
            TranslucidButton(
                node_frame,
                text=name,
                command=cmd,
                image=self._icons.get(name),
                compound=tk.LEFT,
            ).pack(fill=tk.X, padx=2, pady=2)

        rel_cmds = [
            ("Solved By", self.connect_solved_by),
            ("In Context Of", self.connect_in_context),
        ]
        try:
            rel_frame = ttk.LabelFrame(
                self.toolbox,
                text="Relationships",
                style="Toolbox.TLabelframe",
            )
        except TypeError:
            rel_frame = ttk.LabelFrame(
                self.toolbox,
                text="Relationships",
            )
        rel_frame.pack(side=tk.TOP, fill=tk.X)
        for name, cmd in rel_cmds:
            TranslucidButton(
                rel_frame,
                text=name,
                command=cmd,
                image=self._icons.get(name),
                compound=tk.LEFT,
            ).pack(fill=tk.X, padx=2, pady=2)

        util_cmds = [
            ("Zoom In", self.zoom_in),
            ("Zoom Out", self.zoom_out),
            ("Export CSV", self.export_csv),
        ]
        util_frame = ttk.Frame(self.toolbox)
        util_frame.pack(side=tk.TOP, fill=tk.X)
        for name, cmd in util_cmds:
            TranslucidButton(
                util_frame,
                text=name,
                command=cmd,
                image=self._icons.get(name),
                compound=tk.LEFT,
            ).pack(fill=tk.X, padx=2, pady=2)

        # Ensure the toolbox is wide enough to display button text
        self.after_idle(self._fit_toolbox)

        # drawing canvas with scrollbars so large diagrams remain accessible
        canvas_frame = ttk.Frame(self)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(
            canvas_frame,
            width=800,
            height=600,
            bg=StyleManager.get_instance().canvas_bg,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        hbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        vbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        hbar.grid(row=1, column=0, sticky="ew")
        vbar.grid(row=0, column=1, sticky="ns")
        canvas_frame.rowconfigure(0, weight=1)
        canvas_frame.columnconfigure(0, weight=1)
        self.pack(fill=tk.BOTH, expand=True)

        self.id_to_node = {}
        self.id_to_relation = {}
        self.selected_node: Optional[GSNNode] = None
        self._selected_connection: Optional[tuple[GSNNode, GSNNode]] = None
        self._drag_node: Optional[GSNNode] = None
        self._drag_offset = (0, 0)
        self._connect_mode: Optional[str] = None
        self._connect_parent: Optional[GSNNode] = None
        self._pending_add_type: Optional[str] = None
        self.zoom = 1.0
        self._temp_conn_anim = None
        self._temp_conn_offset = 0
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Double-1>", self._on_double_click)
        self.canvas.bind("<Delete>", self._on_delete)
        self.canvas.bind("<BackSpace>", self._on_delete)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)
        # Provide a context menu for nodes and relationships via right-click.
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<FocusIn>", self._on_focus_in)
        GSN_WINDOWS.add(weakref.ref(self))
        self.refresh()
        self._bind_shortcuts()

    def _on_focus_in(self, _event=None) -> None:
        if self.app:
            self.app.active_gsn_window = self

    def _fit_toolbox(self) -> None:
        """Resize toolbox to the smallest width that shows all button text."""
        self.toolbox.update_idletasks()

        button_width = max_button_reqwidth(self.toolbox) + 4
        scroll_width = self.toolbox_scroll.winfo_reqwidth()
        self.toolbox_container.configure(width=button_width + scroll_width)
        self.toolbox_canvas.configure(width=button_width)
        self.toolbox_canvas.itemconfig(self._toolbox_window, width=button_width)

        def _set_uniform_width(widget: tk.Misc) -> None:
            for child in getattr(widget, "winfo_children", lambda: [])():
                if hasattr(child, "pack_configure"):
                    try:
                        child.pack_configure(fill=tk.X, expand=True)
                    except Exception:
                        pass
                _set_uniform_width(child)

        _set_uniform_width(self.toolbox)
        set_uniform_button_width(self.toolbox)

    # ------------------------------------------------------------------
    def _sync_from_originals(self) -> None:
        """Synchronise cloned nodes with their original counterparts."""
        for node in getattr(self.diagram, "nodes", []):
            original = getattr(node, "original", None)
            if original and original is not node:
                node.user_name = original.user_name
                node.description = original.description
                node.manager_notes = getattr(original, "manager_notes", "")

    # ------------------------------------------------------------------
    def refresh_from_repository(self) -> None:  # pragma: no cover - requires tkinter
        """Refresh the diagram and sync cloned nodes on tab activation."""
        self._sync_from_originals()
        self.refresh()

    # ------------------------------------------------------------------
    def refresh(self):  # pragma: no cover - requires tkinter
        # Ensure the diagram has access to the application for SPI lookups
        setattr(self.diagram, "app", getattr(self, "app", None))
        self.canvas.delete("all")
        self.id_to_node = {n.unique_id: n for n in self.diagram._traverse()}
        self.id_to_relation = {}
        for parent in self.diagram._traverse():
            for child in parent.children:
                rel_id = self._rel_id(parent, child)
                self.id_to_relation[rel_id] = (parent, child)
        self.diagram.draw(self.canvas, zoom=self.zoom)
        if self.selected_node:
            bbox = self.canvas.bbox(self.selected_node.unique_id)
            if bbox:
                self.canvas.create_rectangle(*bbox, outline="red", width=2)
        selected_conn = getattr(self, "_selected_connection", None)
        if selected_conn:
            tag = self._rel_id(*selected_conn)
            for item in self.canvas.find_withtag(tag):
                typ = self.canvas.type(item)
                if typ == "line":
                    self.canvas.itemconfigure(item, fill="red", width=2)
                else:
                    self.canvas.itemconfigure(item, outline="red")
        # update scroll region to encompass all drawn items
        bbox = self.canvas.bbox("all") or (0, 0, 0, 0)
        self.canvas.configure(scrollregion=bbox)

    # ------------------------------------------------------------------
    def redraw(self):
        self.canvas.configure(bg=StyleManager.get_instance().canvas_bg)
        self.refresh()

    # ------------------------------------------------------------------
    def _bind_shortcuts(self):
        """Bind common keyboard shortcuts for undo/redo actions."""
        if self.app:
            self.bind("<Control-z>", lambda e: self.app.undo())
            self.bind("<Control-y>", lambda e: self.app.redo())

    # The following methods simply extend the diagram with new nodes.
    # Placement is very rudimentary but sufficient for tests.
    def _add_node(self, node_type: str):  # pragma: no cover - requires tkinter
        """Prepare to add a node once the user clicks a location."""
        self._pending_add_type = node_type
        configure = getattr(self.canvas, "configure", None)
        if configure:
            configure(cursor="tcross")

    def add_goal(self):  # pragma: no cover - requires tkinter
        self._add_node("Goal")

    def add_strategy(self):  # pragma: no cover - requires tkinter
        self._add_node("Strategy")

    def add_solution(self):  # pragma: no cover - requires tkinter
        self._add_node("Solution")

    def add_assumption(self):  # pragma: no cover - requires tkinter
        self._add_node("Assumption")

    def add_justification(self):  # pragma: no cover - requires tkinter
        self._add_node("Justification")

    def add_context(self):  # pragma: no cover - requires tkinter
        self._add_node("Context")

    def add_module(self):  # pragma: no cover - requires tkinter
        app = getattr(self, "app", None)
        if not app:
            return
        modules = getattr(app, "gsn_modules", [])
        if not modules:
            return
        names = [m.name for m in modules]
        dialog = ModuleSelectDialog(self, "Add Existing Module", names)
        name = dialog.selection
        if not name:
            return
        undo = getattr(app, "push_undo_state", None)
        if undo:
            undo()
        node = GSNNode(name, "Module", x=50, y=50)
        self.diagram.add_node(node)
        self.selected_node = node
        self.refresh()

    def connect_solved_by(self):  # pragma: no cover - GUI interaction stub
        self._connect_mode = "solved"
        self._connect_parent = None
        # Change the cursor to indicate connection mode.
        configure = getattr(self.canvas, "configure", None)
        if configure:
            configure(cursor="tcross")

    def connect_in_context(self):  # pragma: no cover - GUI interaction stub
        self._connect_mode = "context"
        self._connect_parent = None
        configure = getattr(self.canvas, "configure", None)
        if configure:
            configure(cursor="hand2")

    def _on_click(self, event):  # pragma: no cover - requires tkinter
        raw_x, raw_y = event.x, event.y
        cx = self.canvas.canvasx(raw_x)
        cy = self.canvas.canvasy(raw_y)
        if getattr(self, "_pending_add_type", None):
            app = getattr(self, "app", None)
            undo = getattr(app, "push_undo_state", None)
            if undo:
                undo()
            node = GSNNode(
                self._pending_add_type,
                self._pending_add_type,
                x=cx / self.zoom,
                y=cy / self.zoom,
            )
            self.diagram.add_node(node)
            self.selected_node = node
            self._pending_add_type = None
            configure = getattr(self.canvas, "configure", None)
            if configure:
                configure(cursor="")
            self.refresh()
            return
        if not hasattr(self, "selected_connection"):
            self.selected_connection = None
        if not hasattr(self, "_selected_conn_id"):
            self._selected_conn_id = ""
        node = self._node_at(raw_x, raw_y)
        connection = self._connection_at(cx, cy)
        app = getattr(self, "app", None)
        if self._connect_mode:
            self._connect_parent = node
            return
        selected_conn = getattr(self, "_selected_connection", None)
        if selected_conn and node:
            parent, child = selected_conn
            if node not in (parent, child):
                self._move_connection(parent, child, node)
            self._selected_connection = None
            self.selected_node = node
            if app:
                app.selected_node = node
            self.refresh()
            return
        if connection:
            self._selected_connection = connection
            self.selected_node = None
            if app:
                app.selected_node = None
            self.refresh()
            return
        if not node:
            self.selected_node = None
            self._selected_connection = None
            if app:
                app.selected_node = None
            self.refresh()
            return
        undo = getattr(app, "push_undo_state", None)
        if undo:
            undo()
        self.selected_node = node
        self._selected_connection = None
        self._drag_node = node
        sx, sy = node.x * self.zoom, node.y * self.zoom
        self._drag_offset = (cx - sx, cy - sy)
        if app:
            app.selected_node = node
        self.refresh()

    def _move_subtree(self, node: GSNNode, dx: float, dy: float, visited: set[str] | None = None) -> None:
        """Move *node* and all its descendants by ``dx`` and ``dy``.

        A ``visited`` set is used to avoid processing the same node multiple
        times when the diagram contains shared children.  Each node's
        coordinates are updated in place.
        """
        if visited is None:
            visited = set()
        if node.unique_id in visited:
            return
        visited.add(node.unique_id)
        node.x += dx
        node.y += dy
        for child in getattr(node, "children", []):
            self._move_subtree(child, dx, dy, visited)

    def _on_drag(self, event):  # pragma: no cover - requires tkinter
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        if self._connect_mode and self._connect_parent:
            self.canvas.delete("_temp_conn")
            px, py = (
                self._connect_parent.x * self.zoom,
                self._connect_parent.y * self.zoom,
            )
            # Show a dotted preview line with an arrow while establishing a
            # connection.  The line is animated to provide visual feedback
            # during the drag operation.
            arrow = tk.LAST
            self.canvas.create_line(
                px,
                py,
                cx,
                cy,
                fill="dimgray",
                dash=(2, 2),
                smooth=True,
                arrow=arrow,
                tags="_temp_conn",
            )
            if getattr(self, "_temp_conn_anim", None) is None:
                self._temp_conn_offset = 0
                self._animate_temp_connection()
            return
        if not self._drag_node:
            return
        nx = (cx - self._drag_offset[0]) / self.zoom
        ny = (cy - self._drag_offset[1]) / self.zoom
        dx = nx - self._drag_node.x
        dy = ny - self._drag_node.y
        # Move the dragged node along with all of its children so the
        # relative layout of the subtree remains intact.
        self._move_subtree(self._drag_node, dx, dy)
        self.refresh()

    def _on_release_strategy1(self, event):
        return self._node_at(getattr(event, "x", 0), getattr(event, "y", 0))

    def _on_release_strategy2(self, event):
        x = getattr(event, "x", 0)
        y = getattr(event, "y", 0)
        return self._node_at(x, y)

    def _on_release_strategy3(self, event):
        try:
            return self._node_at(event.x, event.y)
        except Exception:
            return None

    def _on_release_strategy4(self, event):
        coords = (
            float(getattr(event, "x", 0)),
            float(getattr(event, "y", 0)),
        )
        return self._node_at(*coords)

    def _on_release(self, event):  # pragma: no cover - requires tkinter
        if self._connect_mode and self._connect_parent:
            self.canvas.delete("_temp_conn")
            anim = getattr(self, "_temp_conn_anim", None)
            if anim:
                self.canvas.after_cancel(anim)
                self._temp_conn_anim = None
            node = None
            for strat in (
                self._on_release_strategy1,
                self._on_release_strategy2,
                self._on_release_strategy3,
                self._on_release_strategy4,
            ):
                node = strat(event)
                if node:
                    break
            if node and node is not self._connect_parent:
                relation = self._connect_mode
                app = getattr(self, "app", None)
                undo = getattr(app, "push_undo_state", None)
                if undo:
                    undo()
                try:
                    self._connect_parent.add_child(node, relation=relation)
                except ValueError as exc:
                    showerror = getattr(messagebox, "showerror", None)
                    if showerror:
                        showerror("Invalid Relationship", str(exc))
            self._connect_mode = None
            self._connect_parent = None
            configure = getattr(self.canvas, "configure", None)
            if configure:
                configure(cursor="")
            self.refresh()
            return
        self._drag_node = None

    def _animate_temp_connection(self):  # pragma: no cover - requires tkinter
        find = getattr(self.canvas, "find_withtag", None)
        configure = getattr(self.canvas, "itemconfigure", None)
        if not (find and configure):
            self._temp_conn_anim = None
            return
        line = find("_temp_conn")
        if line:
            offset = getattr(self, "_temp_conn_offset", 0)
            offset = (offset + 2) % 8
            self._temp_conn_offset = offset
            configure(line[0], dashoffset=offset)
            self._temp_conn_anim = self.canvas.after(100, self._animate_temp_connection)
        else:
            self._temp_conn_anim = None

    def _open_work_product(self, name: str) -> None:
        """Attempt to open *name* as a work product.

        The method first defers to application helpers when available and
        falls back to opening *name* as a local file or URL via the default
        web browser.  This ensures double-clicking a solution node with a
        work product still performs a sensible action even outside the full
        application context.
        """

        app = getattr(self, "app", None)

        if app:
            # Prefer a dedicated helper when available
            opener = getattr(app, "open_work_product", None)
            if callable(opener):
                opener(name)
                return

            # Fallback to tool actions when the work product corresponds to a tool
            actions = getattr(app, "tool_actions", {})
            action = actions.get(name)
            if callable(action):
                action()
                return

        if name:
            path = Path(name)
            if path.exists():
                try:
                    if os.name == "nt":
                        os.startfile(path)  # type: ignore[attr-defined]
                    elif sys.platform == "darwin":
                        subprocess.run(["open", str(path)], check=False)
                    else:
                        subprocess.run(["xdg-open", str(path)], check=False)
                except Exception:
                    webbrowser.open(path.resolve().as_uri())
            else:
                webbrowser.open(name)

    def _on_double_click(self, event):  # pragma: no cover - requires tkinter
        raw_x, raw_y = event.x, event.y
        cx = self.canvas.canvasx(raw_x)
        cy = self.canvas.canvasy(raw_y)
        node = self._node_at(raw_x, raw_y)
        if node:
            if node.node_type == "Solution":
                link = getattr(node, "evidence_link", "")
                work = getattr(node, "work_product", "")
                if link and work:
                    choice = messagebox.askyesnocancel(
                        "Open Solution",
                        "Open work product?\nYes: Work Product\nNo: Evidence Link",
                    )
                    if choice is None:
                        return
                    if choice:
                        self._open_work_product(work)
                    else:
                        webbrowser.open(link)
                elif work:
                    self._open_work_product(work)
                elif link:
                    webbrowser.open(link)
                else:
                    app = getattr(self, "app", None)
                    undo = getattr(app, "push_undo_state", None)
                    if undo:
                        undo()
                    GSNElementConfig(self, node, self.diagram)
                    self.refresh()
                    return
                self.refresh()
                return
            app = getattr(self, "app", None)
            undo = getattr(app, "push_undo_state", None)
            if undo:
                undo()
            GSNElementConfig(self, node, self.diagram)
            self.refresh()
            return
        conn = self._connection_at(cx, cy)
        if conn:
            parent, child = conn
            app = getattr(self, "app", None)
            undo = getattr(app, "push_undo_state", None)
            if undo:
                undo()
            GSNConnectionConfig(self, parent, child, self.diagram)
            self.refresh()
            return

    # ------------------------------------------------------------------
    def _on_right_click(self, event):  # pragma: no cover - requires tkinter
        """Show a context menu for the element under the cursor."""
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        node = self._node_at(cx, cy)
        conn = self._connection_at(cx, cy)
        if not node and not conn:
            return
        menu = tk.Menu(self, tearoff=0)
        if node:
            menu.add_command(
                label="Edit", command=lambda n=node: self._edit_node(n)
            )
            menu.add_command(
                label="Delete", command=lambda n=node: self._delete_node(n)
            )
        elif conn:
            parent, child = conn
            menu.add_command(
                label="Edit",
                command=lambda p=parent, c=child: self._edit_connection(p, c),
            )
            menu.add_command(
                label="Delete",
                command=lambda p=parent, c=child: self._delete_connection(p, c),
            )
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:  # pragma: no cover - no-op on simple stubs
            # ``grab_release`` avoids blocking further events if available.
            grab = getattr(menu, "grab_release", None)
            if grab:
                grab()

    # ------------------------------------------------------------------
    def _edit_node(self, node: GSNNode) -> None:  # pragma: no cover - requires tkinter
        app = getattr(self, "app", None)
        undo = getattr(app, "push_undo_state", None)
        if undo:
            undo()
        GSNElementConfig(self, node, self.diagram)
        self.refresh()

    def _delete_node(self, node: GSNNode) -> None:  # pragma: no cover - requires tkinter
        app = getattr(self, "app", None)
        undo = getattr(app, "push_undo_state", None)
        if undo:
            undo()
        if node in self.diagram.nodes:
            self.diagram.nodes.remove(node)
        for parent in list(getattr(node, "parents", [])):
            if node in parent.children:
                parent.children.remove(node)
            if node in parent.context_children:
                parent.context_children.remove(node)
            if parent in node.parents:
                node.parents.remove(parent)
        for child in list(getattr(node, "children", [])):
            if node in child.parents:
                child.parents.remove(node)
        self.refresh()

    def _edit_connection(self, parent: GSNNode, child: GSNNode) -> None:  # pragma: no cover - requires tkinter
        app = getattr(self, "app", None)
        undo = getattr(app, "push_undo_state", None)
        if undo:
            undo()
        GSNConnectionConfig(self, parent, child, self.diagram)
        self.refresh()

    def _delete_connection(self, parent: GSNNode, child: GSNNode) -> None:  # pragma: no cover - requires tkinter
        app = getattr(self, "app", None)
        undo = getattr(app, "push_undo_state", None)
        if undo:
            undo()
        if child in parent.children:
            parent.children.remove(child)
        if parent in child.parents:
            child.parents.remove(parent)
        if child in parent.context_children:
            parent.context_children.remove(child)
        self.refresh()

    def _node_at_strategy1(self, x: float, y: float) -> Optional[GSNNode]:
        canvasx = getattr(self.canvas, "canvasx", lambda v: v)
        canvasy = getattr(self.canvas, "canvasy", lambda v: v)
        cx, cy = canvasx(x), canvasy(y)
        items = self.canvas.find_overlapping(cx - 5, cy - 5, cx + 5, cy + 5)
        for item in items:
            for tag in self.canvas.gettags(item):
                node = self.id_to_node.get(tag)
                if node:
                    return node
        return None

    def _node_at_strategy2(self, x: float, y: float) -> Optional[GSNNode]:
        """Return node using the closest item only when the pointer is over it.

        The original implementation simply returned the closest canvas item
        regardless of the click position.  ``Canvas.find_closest`` always
        yields an item which meant that clicking on empty space would
        incorrectly select the nearest node.  To avoid random selections we
        now verify that the pointer actually lies within the bounding box of
        the closest item before looking up the corresponding node.
        """

        canvasx = getattr(self.canvas, "canvasx", lambda v: v)
        canvasy = getattr(self.canvas, "canvasy", lambda v: v)
        cx, cy = canvasx(x), canvasy(y)
        for item in self.canvas.find_closest(cx, cy):
            bbox = getattr(self.canvas, "bbox", lambda *_: None)(item)
            if bbox:
                x1, y1, x2, y2 = bbox
                if x1 <= cx <= x2 and y1 <= cy <= y2:
                    node = self._node_from_canvas_item(item)
                    if node:
                        return node
        return None

    def _node_from_canvas_item(self, item) -> Optional[GSNNode]:
        """Return the node associated with a canvas item, if any."""
        for tag in self.canvas.gettags(item):
            node = self.id_to_node.get(tag)
            if node:
                return node
        return None

    def _node_at_strategy3(self, x: float, y: float) -> Optional[GSNNode]:
        canvasx = getattr(self.canvas, "canvasx", lambda v: v)
        canvasy = getattr(self.canvas, "canvasy", lambda v: v)
        cx, cy = canvasx(x), canvasy(y)
        for tag, node in self.id_to_node.items():
            bbox = getattr(self.canvas, "bbox", lambda *_: None)(tag)
            if not bbox:
                continue
            x1, y1, x2, y2 = bbox
            if x1 <= cx <= x2 and y1 <= cy <= y2:
                return node
        return None

    def _node_at_strategy4(self, x: float, y: float) -> Optional[GSNNode]:
        canvasx = getattr(self.canvas, "canvasx", lambda v: v)
        canvasy = getattr(self.canvas, "canvasy", lambda v: v)
        cx, cy = canvasx(x), canvasy(y)
        diagram = getattr(self, "diagram", None)
        if diagram is None:
            return None
        for node in diagram._traverse():
            if (cx - node.x) ** 2 + (cy - node.y) ** 2 <= (20 * self.zoom) ** 2:
                return node
        return None

    def _node_at(self, x: float, y: float) -> Optional[GSNNode]:
        for strat in (
            self._node_at_strategy1,
            self._node_at_strategy2,
            self._node_at_strategy3,
            self._node_at_strategy4,
        ):
            node = strat(x, y)
            if node:
                return node
        return None

    def _rel_id(self, parent: GSNNode, child: GSNNode) -> str:
        # Match the connection tag format used by :mod:`gsn.diagram`.
        return f"{parent.unique_id}->{child.unique_id}"

    def _connection_at(self, x: float, y: float):
        items = self.canvas.find_overlapping(x - 5, y - 5, x + 5, y + 5)
        relations = getattr(self, "id_to_relation", {})
        for item in items:
            for tag in self.canvas.gettags(item):
                rel = relations.get(tag)
                if rel:
                    return rel
        return None

    def _move_connection(
        self, parent: GSNNode, old_child: GSNNode, new_child: Optional[GSNNode]
    ) -> None:
        """Reattach an existing relationship to a new child node.

        If *new_child* is ``None`` the move is cancelled and the original
        connection is left intact.  This ensures accidental drops on empty
        space do not delete the relationship.
        """

        # Abort when the connection was not dropped on a valid node.
        if new_child is None:
            return

        app = getattr(self, "app", None)
        undo = getattr(app, "push_undo_state", None)
        if undo:
            undo()
        relation = "context" if old_child in parent.context_children else "solved"
        if old_child in parent.children:
            parent.children.remove(old_child)
        if parent in old_child.parents:
            old_child.parents.remove(parent)
        if old_child in parent.context_children:
            parent.context_children.remove(old_child)
        parent.add_child(new_child, relation=relation)

    def _on_delete(self, event):  # pragma: no cover - requires tkinter
        if self._selected_connection:
            app = getattr(self, "app", None)
            undo = getattr(app, "push_undo_state", None)
            if undo:
                undo()
            parent, child = self._selected_connection
            if child in parent.children:
                parent.children.remove(child)
            if parent in child.parents:
                child.parents.remove(parent)
            if child in parent.context_children:
                parent.context_children.remove(child)
            self._selected_connection = None
            self.refresh()
        
    def _clone_node_strategy1(self, node: GSNNode) -> GSNNode | None:
        return getattr(node, "original", node)

    def _clone_node_strategy2(self, node: GSNNode) -> GSNNode | None:
        return node.original if hasattr(node, "original") else node

    def _clone_node_strategy3(self, node: GSNNode) -> GSNNode | None:
        return (getattr(node, "original", None) or node)

    def _clone_node_strategy4(self, node: GSNNode) -> GSNNode | None:
        return getattr(node, "original", node)

    def _clone_node(self, node: GSNNode) -> GSNNode | None:
        for strat in (
            self._clone_node_strategy1,
            self._clone_node_strategy2,
            self._clone_node_strategy3,
            self._clone_node_strategy4,
        ):
            snap = strat(node)
            if snap is not None:
                return snap
        return None

    def _reconstruct_node_strategy1(self, snap: GSNNode, offset=(20, 20)) -> GSNNode:
        clone = snap.clone()
        clone.x = snap.x + offset[0]
        clone.y = snap.y + offset[1]
        return clone

    def _reconstruct_node_strategy2(self, snap: GSNNode, offset=(30, 30)) -> GSNNode:
        return self._reconstruct_node_strategy1(snap, offset)

    def _reconstruct_node_strategy3(self, snap: GSNNode, offset=(40, 40)) -> GSNNode:
        return self._reconstruct_node_strategy1(snap, offset)

    def _reconstruct_node_strategy4(self, snap: GSNNode, offset=(50, 50)) -> GSNNode:
        return self._reconstruct_node_strategy1(snap, offset)

    def _reconstruct_node(self, snap: GSNNode) -> Optional[GSNNode]:
        for strat in (
            self._reconstruct_node_strategy1,
            self._reconstruct_node_strategy2,
            self._reconstruct_node_strategy3,
            self._reconstruct_node_strategy4,
        ):
            try:
                return strat(snap)
            except Exception:
                continue
        return None

    def copy_selected(self, _event=None) -> None:
        if not self.app or not self.selected_node:
            return
        snap = self._clone_node(self.selected_node)
        if snap is not None:
            self.app.diagram_clipboard.diagram_clipboard = snap
            self.app.diagram_clipboard.diagram_clipboard_type = "GSN"
            if self.selected_node.parents:
                parent = self.selected_node.parents[0]
                rel = (
                    "context"
                    if self.selected_node in parent.context_children
                    else "solved"
                )
            else:
                rel = "solved"
            self.app.diagram_clipboard.clipboard_relation = rel

    def cut_selected(self, _event=None) -> None:
        if not self.app or not self.selected_node:
            return
        self.copy_selected()
        if self.selected_node in self.diagram.nodes:
            self.diagram.nodes.remove(self.selected_node)
        for p in list(self.selected_node.parents):
            if self.selected_node in p.children:
                p.children.remove(self.selected_node)
        self.selected_node = None
        self.refresh()

    def paste_selected(self, _event=None) -> None:
        if not self.app or not getattr(self.app.diagram_clipboard, "diagram_clipboard", None):
            return
        clip_type = getattr(self.app.diagram_clipboard, "diagram_clipboard_type", None)
        if clip_type and clip_type != "GSN":
            messagebox.showwarning(
                "Paste", "Clipboard contains incompatible diagram element."
            )
            return
        node = self._reconstruct_node(self.app.diagram_clipboard.diagram_clipboard)
        if not node:
            return
        if node not in self.diagram.nodes:
            self.diagram.add_node(node)
        self.id_to_node[node.unique_id] = node
        self.selected_node = node
        self.refresh()

    def _on_mousewheel(self, event):  # pragma: no cover - requires tkinter
        delta = getattr(event, "delta", 0)
        num = getattr(event, "num", 0)
        if delta > 0 or num == 4:
            self.zoom_in()
        else:
            self.zoom_out()

    def zoom_in(self):  # pragma: no cover - GUI interaction stub
        self.zoom *= 1.2
        self.refresh()

    def zoom_out(self):  # pragma: no cover - GUI interaction stub
        self.zoom /= 1.2
        self.refresh()

    def export_csv(self):  # pragma: no cover - GUI interaction stub
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV", "*.csv")]
        )
        if not path:
            return
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Name", "Type", "Description", "Children", "Context"])
            for node in self.diagram.nodes:
                children = ";".join(c.unique_id for c in node.children)
                context = ";".join(c.unique_id for c in node.context_children)
                writer.writerow(
                    [
                        node.unique_id,
                        node.user_name,
                        node.node_type,
                        node.description,
                        children,
                        context,
                    ]
                )
