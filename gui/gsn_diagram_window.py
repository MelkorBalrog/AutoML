"""Simple canvas window with toolbox for editing GSN diagrams."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, simpledialog
import webbrowser
from typing import Optional

from gsn import GSNNode, GSNDiagram
from .gsn_config_window import GSNElementConfig
from .gsn_connection_config import GSNConnectionConfig


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
    ]

    def __init__(self, master, app, diagram: GSNDiagram):
        super().__init__(master)
        self.app = app
        self.diagram = diagram

        # toolbox with buttons to add nodes and connectors
        self.toolbox = ttk.Frame(self)
        self.toolbox.pack(side=tk.TOP, fill=tk.X)
        btn_cmds = [
            ("Goal", self.add_goal),
            ("Strategy", self.add_strategy),
            ("Solution", self.add_solution),
            ("Assumption", self.add_assumption),
            ("Justification", self.add_justification),
            ("Context", self.add_context),
            ("Module", self.add_module),
            ("Solved By", self.connect_solved_by),
            ("In Context Of", self.connect_in_context),
            ("Zoom In", self.zoom_in),
            ("Zoom Out", self.zoom_out),
        ]
        for name, cmd in btn_cmds:
            ttk.Button(self.toolbox, text=name, command=cmd).pack(side=tk.LEFT)

        # drawing canvas with scrollbars so large diagrams remain accessible
        canvas_frame = ttk.Frame(self)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(canvas_frame, width=800, height=600, bg="white")
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
        self.zoom = 1.0
        self._temp_conn_anim = None
        self._temp_conn_offset = 0
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Double-1>", self._on_double_click)
        self.canvas.bind("<Delete>", self._on_delete)
        self.canvas.bind("<BackSpace>", self._on_delete)
        # Provide a context menu for nodes and relationships via right-click.
        self.canvas.bind("<Button-3>", self._on_right_click)
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

    # The following methods simply extend the diagram with new nodes.
    # Placement is very rudimentary but sufficient for tests.
    def _add_node(self, node_type: str):  # pragma: no cover - requires tkinter
        app = getattr(self, "app", None)
        undo = getattr(app, "push_undo_state", None)
        if undo:
            undo()
        node = GSNNode(node_type, node_type, x=50, y=50)
        self.diagram.add_node(node)
        self.selected_node = node
        self.refresh()

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
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        if not hasattr(self, "selected_connection"):
            self.selected_connection = None
        if not hasattr(self, "_selected_conn_id"):
            self._selected_conn_id = ""
        node = self._node_at(cx, cy)
        connection = self._connection_at(cx, cy)
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
            self.refresh()
            return
        if connection:
            self._selected_connection = connection
            self.selected_node = None
            self.refresh()
            return
        if not node:
            self.selected_node = None
            self._selected_connection = None
            self.refresh()
            return
        app = getattr(self, "app", None)
        undo = getattr(app, "push_undo_state", None)
        if undo:
            undo()
        self.selected_node = node
        self._selected_connection = None
        self._drag_node = node
        sx, sy = node.x * self.zoom, node.y * self.zoom
        self._drag_offset = (cx - sx, cy - sy)
        self.refresh()

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
        self._drag_node.x = nx
        self._drag_node.y = ny
        self.refresh()

    def _on_release(self, event):  # pragma: no cover - requires tkinter
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        if self._connect_mode and self._connect_parent:
            self.canvas.delete("_temp_conn")
            anim = getattr(self, "_temp_conn_anim", None)
            if anim:
                self.canvas.after_cancel(anim)
                self._temp_conn_anim = None
            node = self._node_at(cx, cy)
            if node and node is not self._connect_parent:
                # Use the current connect mode to decide whether this is a
                # solved-by or in-context-of relationship.
                relation = self._connect_mode
                app = getattr(self, "app", None)
                undo = getattr(app, "push_undo_state", None)
                if undo:
                    undo()
                self._connect_parent.add_child(node, relation=relation)
            self._connect_mode = None
            self._connect_parent = None
            # Restore the default cursor once the connection is made.
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

    def _on_double_click(self, event):  # pragma: no cover - requires tkinter
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        node = self._node_at(cx, cy)
        if node:
            if (
                node.node_type == "Solution"
                and getattr(node, "evidence_link", "")
            ):
                webbrowser.open(node.evidence_link)
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

    def _node_at(self, x: float, y: float) -> Optional[GSNNode]:
        items = self.canvas.find_overlapping(x - 5, y - 5, x + 5, y + 5)
        for item in items:
            for tag in self.canvas.gettags(item):
                node = self.id_to_node.get(tag)
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
        self, parent: GSNNode, old_child: GSNNode, new_child: GSNNode
    ) -> None:
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

    def zoom_in(self):  # pragma: no cover - GUI interaction stub
        self.zoom *= 1.2
        self.refresh()

    def zoom_out(self):  # pragma: no cover - GUI interaction stub
        self.zoom /= 1.2
        self.refresh()
