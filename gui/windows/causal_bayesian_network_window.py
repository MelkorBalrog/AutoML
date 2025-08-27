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
import tkinter.font as tkfont
from tkinter import ttk, simpledialog
from itertools import product
import re
import copy
import json
import weakref

from analysis.causal_bayesian_network import CausalBayesianNetworkDoc
from gui.utils.name_utils import collect_work_product_names, unique_name_v4
from gui.controls import messagebox
from gui import TranslucidButton
from gui.utils.tooltip import ToolTip
from gui.utils.drawing_helper import FTADrawingHelper
from gui.styles.style_manager import StyleManager
from gui.utils.icon_factory import create_icon as draw_icon
from gui.controls.button_utils import set_uniform_button_width, max_button_reqwidth


CBN_WINDOWS: set[weakref.ReferenceType] = set()


class CausalBayesianNetworkWindow(tk.Frame):
    """Editor for Causal Bayesian Network analyses with diagram support."""

    NODE_RADIUS = 30

    def __init__(self, master, app, icon_size: int = 16):
        super().__init__(master)
        self.app = app
        self.icon_size = icon_size
        if isinstance(master, tk.Toplevel):
            master.title("Causal Bayesian Network Analysis")

        top = ttk.Frame(self)
        top.pack(fill=tk.X)
        ttk.Label(top, text="Analysis:").pack(side=tk.LEFT)
        self.doc_var = tk.StringVar()
        self.doc_cb = ttk.Combobox(top, textvariable=self.doc_var, state="readonly")
        self.doc_cb.pack(side=tk.LEFT, padx=2)
        TranslucidButton(top, text="New", command=self.new_doc).pack(side=tk.LEFT)
        TranslucidButton(top, text="Rename", command=self.rename_doc).pack(side=tk.LEFT)
        TranslucidButton(top, text="Delete", command=self.delete_doc).pack(side=tk.LEFT)
        self.doc_cb.bind("<<ComboboxSelected>>", self.select_doc)

        body = ttk.Frame(self)
        body.pack(fill=tk.BOTH, expand=True)

        self.toolbox = ttk.Frame(body)
        self._icons = {
            "Variable": draw_icon("circle", "lightgray", size=self.icon_size),
            "Triggering Condition": draw_icon("circle", "lightblue", size=self.icon_size),
            "Existing Triggering Condition": draw_icon(
                "circle", "lightblue", size=self.icon_size
            ),
            "Functional Insufficiency": draw_icon(
                "circle", "lightyellow", size=self.icon_size
            ),
            "Existing Functional Insufficiency": draw_icon(
                "circle", "lightyellow", size=self.icon_size
            ),
            "Existing Malfunction": draw_icon(
                "circle", "lightgreen", size=self.icon_size
            ),
            "Relationship": draw_icon("relation", "black", size=self.icon_size),
        }
        for name in (
            "Variable",
            "Triggering Condition",
            "Existing Triggering Condition",
            "Functional Insufficiency",
            "Existing Functional Insufficiency",
            "Existing Malfunction",
            "Relationship",
        ):
            TranslucidButton(
                self.toolbox,
                text=name,
                image=self._icons.get(name),
                compound=tk.LEFT,
                command=lambda t=name: self.select_tool(t),
            ).pack(fill=tk.X, padx=2, pady=2)
        set_uniform_button_width(self.toolbox)
        # Pack then immediately hide so order relative to the canvas is preserved
        self.toolbox.pack(side=tk.LEFT, fill=tk.Y)
        self.toolbox.pack_forget()
        self.current_tool = "Select"

        self.after_idle(self._fit_toolbox)

        self.canvas_container = ttk.Frame(body)
        self.canvas_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(
            self.canvas_container,
            background=StyleManager.get_instance().canvas_bg,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        xbar = ttk.Scrollbar(self.canvas_container, orient=tk.HORIZONTAL, command=self.canvas.xview)
        xbar.grid(row=1, column=0, sticky="ew")
        ybar = ttk.Scrollbar(self.canvas_container, orient=tk.VERTICAL, command=self.canvas.yview)
        ybar.grid(row=0, column=1, sticky="ns")
        self.canvas_container.rowconfigure(0, weight=1)
        self.canvas_container.columnconfigure(0, weight=1)
        self.canvas.configure(xscrollcommand=xbar.set, yscrollcommand=ybar.set)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Double-1>", self.on_double_click)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.drawing_helper = FTADrawingHelper()

        # allow multiple instances of the same model node on a diagram
        self.nodes = {}  # name -> list[(oval_id, text_id, fill_tag)]
        self.tables = {}  # name -> list[(window_id, frame, treeview)]
        self.id_to_node = {}  # canvas id -> (name, index)
        self.edges = []  # (line_id, src, dst)
        self.edge_start = None
        self.drag_node = None
        self.selected_node = None  # (name, index)
        self.selection_rect = None
        self.temp_edge_line = None
        self.temp_edge_anim = None
        self.temp_edge_offset = 0

        self.zoom_level = 1.0
        self.base_radius = self.NODE_RADIUS
        self.base_font_size = 10
        self.text_font = tkfont.Font(size=self.base_font_size)

        self.refresh_docs()
        self.pack(fill=tk.BOTH, expand=True)
        self._bind_shortcuts()
        self.focus_set()
        self.bind("<FocusIn>", self._on_focus_in)
        CBN_WINDOWS.add(weakref.ref(self))

    # ------------------------------------------------------------------
    def refresh_docs(self) -> None:
        names = [doc.name for doc in getattr(self.app, "cbn_docs", [])]
        self.doc_cb.configure(values=names)
        if names:
            current = self.doc_var.get()
            if current not in names:
                self.doc_var.set(names[0])
            self.select_doc()
        else:
            self.doc_var.set("")
            self.app.active_cbn = None
            self.canvas.delete("all")
        self._update_toolbox_visibility()
    # ------------------------------------------------------------------
    def redraw(self):
        self.canvas.configure(background=StyleManager.get_instance().canvas_bg)
        self.select_doc()

    # ------------------------------------------------------------------
    def select_doc(self, *_):
        name = self.doc_var.get()
        for doc in getattr(self.app, "cbn_docs", []):
            if doc.name == name:
                self.app.active_cbn = doc
                break
        else:
            self.app.active_cbn = None
        self.load_doc()
        self._update_toolbox_visibility()

    # ------------------------------------------------------------------
    def _update_toolbox_visibility(self) -> None:
        if self.doc_var.get():
            if not self.toolbox.winfo_ismapped():
                self.toolbox.pack(side=tk.LEFT, fill=tk.Y, before=self.canvas_container)
        else:
            self.toolbox.pack_forget()

    def _on_focus_in(self, _event=None) -> None:
        if self.app:
            self.app._cbn_window = self

    # ------------------------------------------------------------------
    def _fit_toolbox(self) -> None:
        """Ensure all toolbox buttons share the width of the longest."""
        self.toolbox.update_idletasks()
        set_uniform_button_width(self.toolbox)

        button_width = max_button_reqwidth(self.toolbox)

        def _set_uniform(widget: tk.Misc) -> None:
            for child in getattr(widget, "winfo_children", lambda: [])():
                if hasattr(child, "pack_configure"):
                    try:
                        child.pack_configure(fill=tk.X, expand=True)
                    except Exception:
                        pass
                _set_uniform(child)

        _set_uniform(self.toolbox)
        self.toolbox.configure(width=button_width)

    # ------------------------------------------------------------------
    def new_doc(self) -> None:
        name = simpledialog.askstring("New Analysis", "Name:", parent=self)
        if not name or self._doc_name_exists(name):
            if name:
                messagebox.showerror("New Analysis", "Analysis name already exists")
            return
        doc = CausalBayesianNetworkDoc(name)
        if not hasattr(self.app, "cbn_docs"):
            self.app.cbn_docs = []
        self.app.cbn_docs.append(doc)
        toolbox = getattr(self.app, "safety_mgmt_toolbox", None)
        if toolbox:
            toolbox.register_created_work_product("Causal Bayesian Network Analysis", name)
        self.refresh_docs()
        self.doc_var.set(name)
        self.select_doc()

    def _doc_name_exists(self, name: str) -> bool:
        docs = list(getattr(self.app, "cbn_docs", []))
        checks = [
            lambda n: any(d.name == n for d in docs),
            lambda n: any(d.name.lower() == n.lower() for d in docs),
            lambda n: any(d.name.strip() == n.strip() for d in docs),
            lambda n: any(d.name.split()[0] == n.split()[0] for d in docs),
        ]
        return any(check(name) for check in checks)

    # ------------------------------------------------------------------
    def rename_doc(self) -> None:
        old = self.doc_var.get()
        if not old:
            return
        new = simpledialog.askstring("Rename Analysis", "Name:", initialvalue=old, parent=self)
        if not new or new == old:
            return
        docs = getattr(self.app, "cbn_docs", [])
        for doc in docs:
            if doc.name == old:
                new = unique_name_v4(new, collect_work_product_names(self.app, ignore=doc, diagram_type="cbn"))
                doc.name = new
                toolbox = getattr(self.app, "safety_mgmt_toolbox", None)
                if toolbox:
                    toolbox.rename_document("Causal Bayesian Network Analysis", old, new)
                break
        self.refresh_docs()
        self.doc_var.set(new)

    # ------------------------------------------------------------------
    def delete_doc(self) -> None:
        name = self.doc_var.get()
        if not name:
            return
        docs = getattr(self.app, "cbn_docs", [])
        for idx, doc in enumerate(docs):
            if doc.name == name:
                del docs[idx]
                toolbox = getattr(self.app, "safety_mgmt_toolbox", None)
                if toolbox:
                    toolbox.register_deleted_work_product("Causal Bayesian Network Analysis", name)
                break
        self.refresh_docs()

    # ------------------------------------------------------------------
    def select_tool(self, tool: str) -> None:
        self.current_tool = tool
        self.edge_start = None
        self.drag_node = None
        if tool != "Select":
            self._highlight_node(None)

        configure = getattr(self.canvas, "configure", None)
        if configure:
            node_tools = {
                "Variable",
                "Triggering Condition",
                "Existing Triggering Condition",
                "Functional Insufficiency",
                "Existing Functional Insufficiency",
                "Existing Malfunction",
            }
            if tool == "Relationship":
                configure(cursor="tcross")
            elif tool in node_tools:
                configure(cursor="crosshair")
            else:
                configure(cursor="")

    # ------------------------------------------------------------------
    def on_click(self, event) -> None:
        doc = getattr(self.app, "active_cbn", None)
        if not doc:
            return
        if self.current_tool == "Variable":
            undo = getattr(self.app, "push_undo_state", None)
            if undo:
                undo()
            name = simpledialog.askstring("Variable", "Name:", parent=self)
            if not name or name in doc.network.nodes:
                self.select_tool("Select")
                return
            x, y = event.x, event.y
            doc.network.add_node(name, cpd=0.5)
            self._add_position(doc, name, (x, y))
            doc.types[name] = "variable"
            self._draw_node(name, x, y, "variable")
            self.select_tool("Select")
        elif self.current_tool in ("Triggering Condition", "Functional Insufficiency"):
            prompt = self.current_tool
            name = simpledialog.askstring(prompt, "Name:", parent=self)
            if not name or name in doc.network.nodes:
                self.select_tool("Select")
                return
            undo = getattr(self.app, "push_undo_state", None)
            if undo:
                undo()
            x, y = event.x, event.y
            doc.network.add_node(name, cpd=0.5)
            self._add_position(doc, name, (x, y))
            kind = "trigger" if self.current_tool == "Triggering Condition" else "insufficiency"
            doc.types[name] = kind
            self._draw_node(name, x, y, kind)
            if kind == "trigger" and hasattr(self.app, "add_triggering_condition"):
                self.app.add_triggering_condition(name)
            elif kind == "insufficiency" and hasattr(
                self.app, "add_functional_insufficiency"
            ):
                self.app.add_functional_insufficiency(name)
            self.select_tool("Select")
        elif self.current_tool == "Existing Triggering Condition":
            names = self._select_triggering_conditions()
            if not names:
                self.select_tool("Select")
                return
            undo = getattr(self.app, "push_undo_state", None)
            if undo:
                undo()
            x, y = event.x, event.y
            for idx, name in enumerate(names):
                if name in doc.network.nodes:
                    continue
                nx = x + idx * (2 * self.NODE_RADIUS + 10)
                doc.network.add_node(name, cpd=0.5)
                self._add_position(doc, name, (nx, y))
                doc.types[name] = "trigger"
                self._draw_node(name, nx, y, "trigger")
            if hasattr(self.app, "update_triggering_condition_list"):
                self.app.update_triggering_condition_list()
            self.select_tool("Select")
        elif self.current_tool == "Existing Functional Insufficiency":
            names = self._select_functional_insufficiencies()
            if not names:
                self.select_tool("Select")
                return
            undo = getattr(self.app, "push_undo_state", None)
            if undo:
                undo()
            x, y = event.x, event.y
            for idx, name in enumerate(names):
                if name in doc.network.nodes:
                    continue
                nx = x + idx * (2 * self.NODE_RADIUS + 10)
                doc.network.add_node(name, cpd=0.5)
                self._add_position(doc, name, (nx, y))
                doc.types[name] = "insufficiency"
                self._draw_node(name, nx, y, "insufficiency")
            if hasattr(self.app, "update_functional_insufficiency_list"):
                self.app.update_functional_insufficiency_list()
        elif self.current_tool == "Existing Malfunction":
            names = self._select_malfunctions()
            if not names:
                return
            undo = getattr(self.app, "push_undo_state", None)
            if undo:
                undo()
            x, y = event.x, event.y
            for idx, name in enumerate(names):
                if name in doc.network.nodes:
                    continue
                nx = x + idx * (2 * self.NODE_RADIUS + 10)
                doc.network.add_node(name, cpd=0.5)
                self._add_position(doc, name, (nx, y))
                doc.types[name] = "malfunction"
                self._draw_node(name, nx, y, "malfunction")
        elif self.current_tool == "Relationship":
            node = self._find_node(event.x, event.y)
            if not node:
                self.select_tool("Select")
                return
            self.edge_start = node[0]
            self._highlight_node(None)
        else:  # Select tool
            node = self._find_node(event.x, event.y)
            if node:
                undo = getattr(self.app, "push_undo_state", None)
                if undo:
                    undo()
            self.drag_node = node
            self.drag_offset = (0, 0)
            self._highlight_node(node)
            if node:
                name, idx = node
                x, y = doc.positions.get(name, [(0, 0)])[idx]
                self.drag_offset = (x - event.x, y - event.y)

    # ------------------------------------------------------------------
    def on_drag(self, event) -> None:
        doc = getattr(self.app, "active_cbn", None)
        if not doc:
            return
        if self.current_tool == "Select" and self.drag_node:
            name, idx = self.drag_node
            old_x, old_y = doc.positions.get(name, [(0, 0)])[idx]
            x, y = event.x + self.drag_offset[0], event.y + self.drag_offset[1]
            dx, dy = x - old_x, y - old_y
            doc.positions[name][idx] = (x, y)
            oval_id, text_id, fill_tag = self.nodes[name][idx]
            r = self.NODE_RADIUS
            # Move the gradient fill, node outline and label together
            self.canvas.move(fill_tag, dx, dy)
            self.canvas.move(oval_id, dx, dy)
            self.canvas.move(text_id, dx, dy)
            for line_id, src, dst in self.edges:
                if src == name or dst == name:
                    x1, y1 = doc.positions[src][0]
                    x2, y2 = doc.positions[dst][0]
                    dx, dy = x2 - x1, y2 - y1
                    dist = (dx ** 2 + dy ** 2) ** 0.5 or 1
                    sx = x1 + dx / dist * r
                    sy = y1 + dy / dist * r
                    tx = x2 - dx / dist * r
                    ty = y2 - dy / dist * r
                    self.canvas.coords(line_id, sx, sy, tx, ty)
            self._drag_table(name, idx, x, y)
            if self.selected_node == (name, idx) and self.selection_rect:
                self.canvas.coords(self.selection_rect, x - r, y - r, x + r, y + r)
            self._update_scroll_region()
        elif self.current_tool == "Relationship" and self.edge_start:
            x1, y1 = doc.positions.get(self.edge_start, [(0, 0)])[0]
            if self.temp_edge_line is None:
                self.temp_edge_line = self.canvas.create_line(
                    x1, y1, event.x, event.y, dash=(2, 2)
                )
                self.temp_edge_offset = 0
                self._animate_temp_edge()
            else:
                self.canvas.coords(self.temp_edge_line, x1, y1, event.x, event.y)
            self._update_scroll_region()

    # ------------------------------------------------------------------
    def on_release(self, event) -> None:
        doc = getattr(self.app, "active_cbn", None)
        if not doc:
            return
        if self.current_tool == "Select":
            self.drag_node = None
        elif self.current_tool == "Relationship" and self.edge_start:
            dst = self._find_node(event.x, event.y)
            src = self.edge_start
            if dst and dst[0] != src:
                kind_src = doc.types.get(src)
                kind_dst = doc.types.get(dst[0])
                if kind_src == "insufficiency" and kind_dst == "trigger":
                    messagebox.showerror(
                        "Invalid Relationship",
                        "Functional insufficiency cannot connect to a triggering condition.",
                        parent=self,
                    )
                elif kind_src == "malfunction":
                    messagebox.showerror(
                        "Invalid Relationship",
                        "Malfunction nodes cannot connect to other nodes.",
                        parent=self,
                    )
                else:
                    undo = getattr(self.app, "push_undo_state", None)
                    if undo:
                        undo()
                    self._draw_edge(src, dst[0])
                    parents = doc.network.parents.setdefault(dst[0], [])
                    if src not in parents:
                        parents.append(src)
                        doc.network.cpds[dst[0]] = {}
                        self._rebuild_table(dst[0])
            self.edge_start = None
            if self.temp_edge_line:
                self.canvas.delete(self.temp_edge_line)
                self.temp_edge_line = None
            if self.temp_edge_anim:
                self.after_cancel(self.temp_edge_anim)
                self.temp_edge_anim = None
            self.select_tool("Select")

    # ------------------------------------------------------------------
    def _animate_temp_edge(self):
        if self.temp_edge_line:
            self.temp_edge_offset = (self.temp_edge_offset + 2) % 12
            self.canvas.itemconfigure(
                self.temp_edge_line, dashoffset=self.temp_edge_offset
            )
            self.temp_edge_anim = self.after(100, self._animate_temp_edge)

    # ------------------------------------------------------------------
    def _highlight_node(self, node: tuple | None) -> None:
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
            self.selection_rect = None
        self.selected_node = node
        if not node:
            return
        doc = getattr(self.app, "active_cbn", None)
        if not doc:
            return
        name, idx = node
        x, y = doc.positions.get(name, [(0, 0)])[idx]
        r = self.NODE_RADIUS
        self.selection_rect = self.canvas.create_rectangle(
            x - r, y - r, x + r, y + r, outline="red", dash=(2, 2)
        )

    # ------------------------------------------------------------------
    def on_double_click(self, event) -> None:
        doc = getattr(self.app, "active_cbn", None)
        if not doc:
            return
        node = self._find_node(event.x, event.y)
        if not node:
            return
        name, _idx = node
        undo = getattr(self.app, "push_undo_state", None)
        if undo:
            undo()
        parents = doc.network.parents.get(name, [])
        if not parents:
            prob = simpledialog.askfloat(
                "Prior",
                f"P({name}=True)",
                minvalue=0.0,
                maxvalue=1.0,
                parent=self,
            )
            if prob is not None:
                doc.network.cpds[name] = prob
                self._update_all_tables()
            return
        cpds = {}
        for combo in product([True, False], repeat=len(parents)):
            label = ", ".join(
                f"{p}={'T' if val else 'F'}" for p, val in zip(parents, combo)
            )
            prob = simpledialog.askfloat(
                "CPD",
                f"P({name}=True | {label})",
                minvalue=0.0,
                maxvalue=1.0,
                parent=self,
            )
            if prob is None:
                return
            cpds[combo] = prob
        doc.network.cpds[name] = cpds
        self._update_all_tables()

    # ------------------------------------------------------------------
    def _fill_tag_strategy1(self, name: str, idx: int) -> str:
        safe = re.sub(r"\W", "_", name)
        return f"fill_{safe}_{idx}"

    # ------------------------------------------------------------------
    def _fill_tag_strategy2(self, name: str, idx: int) -> str:
        safe = re.sub(r"\W", "_", name)
        return f"fill_{safe}_{idx}_s2"

    # ------------------------------------------------------------------
    def _fill_tag_strategy3(self, name: str, idx: int) -> str:
        safe = re.sub(r"\W", "_", name)
        return f"fill_{safe}_{idx}_s3"

    # ------------------------------------------------------------------
    def _fill_tag_strategy4(self, name: str, idx: int) -> str:
        safe = re.sub(r"\W", "_", name)
        return f"fill_{safe}_{idx}_s4"

    # ------------------------------------------------------------------
    def _generate_fill_tag(self, name: str, idx: int) -> str:
        for fn in (
            self._fill_tag_strategy1,
            self._fill_tag_strategy2,
            self._fill_tag_strategy3,
            self._fill_tag_strategy4,
        ):
            tag = fn(name, idx)
            if tag:
                return tag
        raise ValueError("Unable to generate fill tag")

    # ------------------------------------------------------------------
    def _draw_node(
        self, name: str, x: float, y: float, kind: str | None = None, idx: int | None = None
    ) -> None:
        """Draw a node as a filled circle with a text label."""
        r = self.NODE_RADIUS
        if kind == "trigger":
            color = "lightblue"
            stereo = "triggering condition"
        elif kind == "insufficiency":
            color = "lightyellow"
            stereo = "functional insufficiency"
        elif kind == "malfunction":
            color = "lightgreen"
            stereo = "malfunction"
        elif kind == "variable":
            color = "lightgray"
            stereo = "variable"
        else:
            color = "lightyellow"
            stereo = None
        self.nodes.setdefault(name, [])
        idx = idx if idx is not None else len(self.nodes[name])
        fill_tag = self._generate_fill_tag(name, idx)
        fill_ids = self.drawing_helper._fill_gradient_circle(
            self.canvas, x, y, r, color, tag=fill_tag
        ) or []
        oval = self.canvas.create_oval(
            x - r,
            y - r,
            x + r,
            y + r,
            outline=StyleManager.get_instance().outline_color,
            fill="",
        )
        label = f"<<{stereo}>>\n{name}" if stereo else name
        font = getattr(self, "text_font", None)
        if font:
            text = self.canvas.create_text(x, y, text=label, font=font)
        else:
            text = self.canvas.create_text(x, y, text=label)
        self.nodes[name].insert(idx, (oval, text, fill_tag))
        self.id_to_node[oval] = (name, idx)
        self.id_to_node[text] = (name, idx)
        for fid in fill_ids:
            self.id_to_node[fid] = (name, idx)
        self._place_table(name, idx)
        self._update_scroll_region()

    # ------------------------------------------------------------------
    def _draw_edge(self, src: str, dst: str, src_idx: int = 0, dst_idx: int = 0) -> None:
        doc = getattr(self.app, "active_cbn", None)
        if not doc:
            return
        x1, y1 = doc.positions.get(src, [(0, 0)])[src_idx]
        x2, y2 = doc.positions.get(dst, [(0, 0)])[dst_idx]
        r = self.NODE_RADIUS
        dx, dy = x2 - x1, y2 - y1
        dist = (dx ** 2 + dy ** 2) ** 0.5 or 1
        sx = x1 + dx / dist * r
        sy = y1 + dy / dist * r
        tx = x2 - dx / dist * r
        ty = y2 - dy / dist * r
        line = self.canvas.create_line(sx, sy, tx, ty, arrow=tk.LAST)
        self.edges.append((line, src, dst))
        self._update_scroll_region()

    # ------------------------------------------------------------------
    def _place_table(self, name: str, idx: int) -> None:
        doc = getattr(self.app, "active_cbn", None)
        if not doc:
            return
        parents = doc.network.parents.get(name, [])
        prob_col = f"P({name}=T)"
        if parents:
            joint_col = f"P({name}=T, parents)"
            cols = list(parents) + [joint_col]
        else:
            cols = [prob_col]
        frame = ttk.Frame(self.canvas)
        label_text = (
            f"Prior probability of {name}" if not parents else f"Conditional probabilities for {name}"
        )
        label = ttk.Label(frame, text=label_text)
        label.pack(side=tk.TOP, fill=tk.X)
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(side=tk.TOP, fill=tk.BOTH)
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=0)
        for c in cols:
            tree.heading(c, text=c)
            is_prob = c == prob_col or (parents and c == joint_col)
            tree.column(c, width=80 if is_prob else 60, anchor=tk.CENTER)
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.columnconfigure(0, weight=1)
        if not parents:
            info = f"Prior probability that {name} is True"
        else:
            info = (
                "Each row shows a combination of parent values; "
                f"{joint_col} is the joint probability that the parents take that combination "
                f"and {name} is True"
            )
        ToolTip(tree, info)
        tree.bind("<Double-1>", lambda e, n=name, i=idx: self.edit_cpd_row(n, i))
        win = self.canvas.create_window(0, 0, window=frame, anchor="nw")
        tables = self.tables.setdefault(name, [])
        while len(tables) <= idx:
            tables.append(None)
        if tables[idx]:
            old_win, old_frame, _ = tables[idx]
            self.canvas.delete(old_win)
            old_frame.destroy()
        tables[idx] = (win, frame, tree)
        self._update_table(name, idx)
        x, y = doc.positions.get(name, [(0, 0)])[idx]
        self._position_table(name, idx, x, y)
        self._update_scroll_region()

    # ------------------------------------------------------------------
    def _table_lookup_strategy1(self, name: str, idx: int):
        try:
            return self.tables[name][idx]
        except Exception:
            return None

    def _table_lookup_strategy2(self, name: str, idx: int):
        tables = self.tables.get(name)
        if tables and idx < len(tables):
            return tables[idx]
        return None

    def _table_lookup_strategy3(self, name: str, idx: int):
        if name in self.tables:
            tables = self.tables[name]
            return tables[idx] if idx < len(tables) else None
        return None

    def _table_lookup_strategy4(self, name: str, idx: int):
        tables = self.tables.get(name, [])
        return next((t for i, t in enumerate(tables) if i == idx), None)

    def _get_table(self, name: str, idx: int):
        for strat in (
            self._table_lookup_strategy1,
            self._table_lookup_strategy2,
            self._table_lookup_strategy3,
            self._table_lookup_strategy4,
        ):
            tbl = strat(name, idx)
            if tbl:
                return tbl
        return None

    # ------------------------------------------------------------------
    def _update_table(self, name: str, idx: int) -> None:
        doc = getattr(self.app, "active_cbn", None)
        tbl = self._get_table(name, idx)
        if not doc or not tbl:
            return
        win, frame, tree = tbl
        tree.delete(*tree.get_children())
        parents = doc.network.parents.get(name, [])
        rows = doc.network.cpd_rows(name)
        if not parents:
            tree.insert("", "end", values=[f"{rows[0][1]:.3f}"])
        else:
            for combo, prob, combo_prob, joint in rows:
                row = ["T" if val else "F" for val in combo]
                row.append(f"{joint:.3f}")
                tree.insert("", "end", values=row)
        tree.configure(height=len(rows))
        frame.update_idletasks()
        self.canvas.itemconfigure(
            win, width=frame.winfo_reqwidth(), height=frame.winfo_reqheight()
        )
        x, y = doc.positions.get(name, [(0, 0)])[idx]
        self._position_table(name, idx, x, y)

    # ------------------------------------------------------------------
    def _position_table(self, name: str, idx: int, x: float, y: float) -> None:
        tbl = self._get_table(name, idx)
        if not tbl:
            return
        win, frame, _ = tbl
        frame.update_idletasks()
        w, h = frame.winfo_reqwidth(), frame.winfo_reqheight()
        r = self.NODE_RADIUS
        self.canvas.itemconfigure(win, width=w, height=h)
        self.canvas.coords(win, x + r + 10, y - h / 2)

    # ------------------------------------------------------------------
    def _drag_table_strategy1(self, name: str, idx: int, x: float, y: float) -> None:
        self._position_table(name, idx, x, y)

    def _drag_table_strategy2(self, name: str, idx: int, x: float, y: float) -> None:
        if self._get_table(name, idx):
            self._position_table(name, idx, x, y)

    def _drag_table_strategy3(self, name: str, idx: int, x: float, y: float) -> None:
        if not self._get_table(name, idx):
            self._place_table(name, idx)
        self._position_table(name, idx, x, y)

    def _drag_table_strategy4(self, name: str, idx: int, x: float, y: float) -> None:
        try:
            self._update_table(name, idx)
        finally:
            self._position_table(name, idx, x, y)

    def _drag_table(self, name: str, idx: int, x: float, y: float) -> None:
        for strat in (
            self._drag_table_strategy1,
            self._drag_table_strategy2,
            self._drag_table_strategy3,
            self._drag_table_strategy4,
        ):
            try:
                strat(name, idx, x, y)
                break
            except Exception:
                continue

    # ------------------------------------------------------------------
    def _update_all_tables(self) -> None:
        doc = getattr(self.app, "active_cbn", None)
        if not doc:
            return
        for name, tables in self.tables.items():
            for idx, tbl in enumerate(tables):
                if tbl:
                    self._update_table(name, idx)

    # ------------------------------------------------------------------
    def _rebuild_table(self, name: str) -> None:
        doc = getattr(self.app, "active_cbn", None)
        if name in self.tables:
            for win, frame, _ in self.tables.pop(name):
                self.canvas.delete(win)
                frame.destroy()
        count = len(doc.positions.get(name, [])) if doc else 0
        for idx in range(count):
            self._place_table(name, idx)

    # ------------------------------------------------------------------
    def add_cpd_row(self, name: str) -> None:
        doc = getattr(self.app, "active_cbn", None)
        if not doc:
            return
        parents = doc.network.parents.get(name, [])
        if not parents:
            prob = simpledialog.askfloat(
                "Prior", f"P({name}=True)", minvalue=0.0, maxvalue=1.0, parent=self
            )
            if prob is not None:
                undo = getattr(self.app, "push_undo_state", None)
                if undo:
                    undo()
                doc.network.cpds[name] = prob
                self._update_all_tables()
            return
        values = []
        for p in parents:
            val = simpledialog.askstring(f"{p}", "T/F", parent=self)
            if val is None:
                return
            values.append(val.strip().upper().startswith("T"))
        prob = simpledialog.askfloat(
            "Probability", f"P({name}=True)", minvalue=0.0, maxvalue=1.0, parent=self
        )
        if prob is None:
            return
        undo = getattr(self.app, "push_undo_state", None)
        if undo:
            undo()
        doc.network.cpds.setdefault(name, {})[tuple(values)] = prob
        self._update_all_tables()

    # ------------------------------------------------------------------
    def edit_cpd_row(self, name: str, idx: int) -> None:
        doc = getattr(self.app, "active_cbn", None)
        tbl = self._get_table(name, idx)
        if not doc or not tbl:
            return
        parents = doc.network.parents.get(name, [])
        _, _, tree = tbl
        item = tree.focus()
        if not item:
            return
        values = tree.item(item, "values")
        if not parents:
            prob = simpledialog.askfloat(
                "Prior", f"P({name}=True)", minvalue=0.0, maxvalue=1.0, parent=self
            )
            if prob is not None:
                undo = getattr(self.app, "push_undo_state", None)
                if undo:
                    undo()
                doc.network.cpds[name] = prob
                self._update_all_tables()
            return
        current = tuple(v == "T" for v in values[:-1])
        prob = simpledialog.askfloat(
            "Probability", f"P({name}=True)", minvalue=0.0, maxvalue=1.0, parent=self
        )
        if prob is None:
            return
        undo = getattr(self.app, "push_undo_state", None)
        if undo:
            undo()
        doc.network.cpds[name][current] = prob
        self._update_all_tables()

    # ------------------------------------------------------------------
    class _SelectExistingDialog(simpledialog.Dialog):
        """Dialog with a combobox and list to choose existing names."""

        def __init__(self, parent, title: str, options: list[str]):
            self._choices = options
            self._selected: list[str] = []
            super().__init__(parent, title)

        def body(self, master):
            ttk.Label(master, text="Name:").grid(row=0, column=0, sticky="e")
            self._var = tk.StringVar()
            self._combo = ttk.Combobox(
                master, values=self._choices, textvariable=self._var, state="readonly"
            )
            self._combo.grid(row=0, column=1, padx=5, pady=5)
            ttk.Button(master, text="Add", command=self._add).grid(row=0, column=2)
            self._lb = tk.Listbox(master, height=5)
            self._lb.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
            return self._combo

        def _add(self):
            val = self._var.get().strip()
            if val and val not in self._selected:
                self._selected.append(val)
                self._lb.insert(tk.END, val)

        def apply(self):
            if not self._selected:
                val = self._var.get().strip()
                if val:
                    self._selected.append(val)
            self.result = self._selected

    def _select_triggering_conditions(self) -> list[str]:
        """Return existing triggering conditions chosen by the user."""
        tcs = sorted(getattr(self.app, "triggering_conditions", []))
        if not tcs:
            messagebox.showinfo(
                "No Triggering Conditions",
                "No triggering conditions available.",
                parent=self,
            )
            return []
        dlg = self._SelectExistingDialog(
            self, "Existing Triggering Conditions", tcs
        )
        return dlg.result or []

    # ------------------------------------------------------------------
    def _select_functional_insufficiencies(self) -> list[str]:
        """Return existing functional insufficiencies chosen by the user."""
        fis = sorted(getattr(self.app, "functional_insufficiencies", []))
        if not fis:
            messagebox.showinfo(
                "No Functional Insufficiencies",
                "No functional insufficiencies available.",
                parent=self,
            )
            return []
        dlg = self._SelectExistingDialog(
            self, "Existing Functional Insufficiencies", fis
        )
        return dlg.result or []

    # ------------------------------------------------------------------
    def _select_malfunctions(self) -> list[str]:
        """Return a list of existing malfunctions chosen by the user."""
        mals = sorted(getattr(self.app, "malfunctions", []))
        if not mals:
            messagebox.showinfo("No Malfunctions", "No malfunctions available.", parent=self)
            return []
        prompt = ", ".join(mals)
        sel = simpledialog.askstring(
            "Existing Malfunctions",
            f"Names (comma separated):\n{prompt}",
            parent=self,
        )
        if not sel:
            return []
        return [n.strip() for n in sel.split(",") if n.strip() in mals]

    # ------------------------------------------------------------------
    def _find_node_strategy1(self, x: float, y: float) -> tuple | None:
        """Locate a node by checking overlapping canvas items."""
        canvasx = getattr(self.canvas, "canvasx", lambda v: v)
        canvasy = getattr(self.canvas, "canvasy", lambda v: v)
        cx, cy = canvasx(x), canvasy(y)
        ids = self.canvas.find_overlapping(cx - 1, cy - 1, cx + 1, cy + 1)
        for i in ids:
            node = self.id_to_node.get(i)
            if node:
                return node
        return None

    def _find_node_strategy2(self, x: float, y: float) -> tuple | None:
        """Locate a node using the closest canvas item."""
        canvasx = getattr(self.canvas, "canvasx", lambda v: v)
        canvasy = getattr(self.canvas, "canvasy", lambda v: v)
        cx, cy = canvasx(x), canvasy(y)
        ids = self.canvas.find_closest(cx, cy)
        for i in ids:
            node = self.id_to_node.get(i)
            if node:
                return node
        return None

    def _find_node_strategy3(self, x: float, y: float) -> tuple | None:
        """Locate a node by checking drawn ovals' bounding boxes."""
        canvasx = getattr(self.canvas, "canvasx", lambda v: v)
        canvasy = getattr(self.canvas, "canvasy", lambda v: v)
        cx, cy = canvasx(x), canvasy(y)
        for name, items in self.nodes.items():
            for idx, (oval_id, _, _) in enumerate(items):
                x1, y1, x2, y2 = self.canvas.coords(oval_id)
                if x1 <= cx <= x2 and y1 <= cy <= y2:
                    return (name, idx)
        return None

    def _find_node_strategy4(self, x: float, y: float) -> tuple | None:
        """Locate a node using stored positions and a radius check."""
        doc = getattr(self.app, "active_cbn", None)
        if not doc:
            return None
        canvasx = getattr(self.canvas, "canvasx", lambda v: v)
        canvasy = getattr(self.canvas, "canvasy", lambda v: v)
        cx, cy = canvasx(x), canvasy(y)
        r = self.NODE_RADIUS
        for name, pos_list in doc.positions.items():
            for idx, (nx, ny) in enumerate(pos_list):
                if (cx - nx) ** 2 + (cy - ny) ** 2 <= r ** 2:
                    return (name, idx)
        return None

    def _find_node(self, x: float, y: float) -> tuple | None:
        """Find a node at the given canvas coordinates using multiple strategies."""
        for strat in (
            self._find_node_strategy1,
            self._find_node_strategy2,
            self._find_node_strategy3,
            self._find_node_strategy4,
        ):
            node = strat(x, y)
            if node:
                return node
        return None

    # ------------------------------------------------------------------
    def load_doc(self) -> None:
        self.canvas.delete("all")
        self.nodes.clear()
        for tables in self.tables.values():
            for _, frame, _ in tables:
                frame.destroy()
        self.tables.clear()
        self.id_to_node.clear()
        self.edges.clear()
        doc = getattr(self.app, "active_cbn", None)
        if not doc:
            return
        for name in doc.network.nodes:
            pos_list = doc.positions.get(name) or [(100, 100)]
            doc.positions[name] = list(pos_list)
            kind = doc.types.get(name)
            for idx, (x, y) in enumerate(doc.positions[name]):
                self._draw_node(name, x, y, kind, idx)
        for child, parents in doc.network.parents.items():
            for parent in parents:
                if parent in doc.network.nodes and child in doc.network.nodes:
                    self._draw_edge(parent, child)
        self._update_scroll_region()

    # ------------------------------------------------------------------
    def refresh_from_repository(self, _event=None) -> None:
        """Refresh the canvas after undo/redo operations."""
        self.refresh_docs()

    # ------------------------------------------------------------------
    def _update_scroll_region(self) -> None:
        if not hasattr(self.canvas, "bbox") or not hasattr(self.canvas, "configure"):
            return
        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.configure(scrollregion=bbox)

    # ------------------------------------------------------------------
    def _bind_shortcuts(self) -> None:
        if self.app:
            self.bind("<Control-z>", lambda e: self.app.undo())
            self.bind("<Control-y>", lambda e: self.app.redo())
            self.bind("<Control-plus>", lambda e: self.zoom(1.1))
            self.bind("<Control-minus>", lambda e: self.zoom(0.9))
            self.bind("<Control-=>", lambda e: self.zoom(1.1))

    # ------------------------------------------------------------------
    def zoom(self, factor: float) -> None:
        self.zoom_level *= factor
        self.NODE_RADIUS = self.base_radius * self.zoom_level
        self.canvas.scale("all", 0, 0, factor, factor)
        doc = getattr(self.app, "active_cbn", None)
        if doc:
            for name, pos_list in doc.positions.items():
                doc.positions[name] = [(x * factor, y * factor) for (x, y) in pos_list]
        if hasattr(self, "text_font"):
            self.text_font.configure(size=int(self.base_font_size * self.zoom_level))
        self._update_scroll_region()

    # ------------------------------------------------------------------
    def on_right_click(self, event) -> None:  # pragma: no cover - requires tkinter
        doc = getattr(self.app, "active_cbn", None)
        if not doc:
            return
        node = self._find_node(event.x, event.y)
        if not node:
            return
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(
            label="Rename", command=lambda n=node[0]: self._prompt_rename_node(n)
        )
        menu.add_command(label="Delete", command=lambda n=node: self._delete_node(n))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:  # pragma: no cover - no-op on simple stubs
            grab = getattr(menu, "grab_release", None)
            if grab:
                grab()

    # ------------------------------------------------------------------
    def _prompt_rename_node(self, name: str) -> None:
        doc = getattr(self.app, "active_cbn", None)
        if not doc:
            return
        new = simpledialog.askstring("Edit Node", "Name:", initialvalue=name, parent=self)
        if not new or new == name:
            return
        if new in doc.network.nodes:
            messagebox.showerror("Edit Node", "Name already exists", parent=self)
            return
        undo = getattr(self.app, "push_undo_state", None)
        if undo:
            undo()
        self._rename_node(name, new)
        self._update_all_tables()

    # ------------------------------------------------------------------
    def _delete_node(self, node) -> None:
        doc = getattr(self.app, "active_cbn", None)
        if not doc:
            return
        name = node[0] if isinstance(node, tuple) else node
        delete_model = messagebox.askyesno(
            "Delete Node",
            "Delete node from model?\nNo removes it from diagram only.",
            parent=self,
        )
        undo = getattr(self.app, "push_undo_state", None)
        if undo:
            undo()
        if delete_model:
            if name in doc.network.nodes:
                doc.network.nodes.remove(name)
            doc.network.cpds.pop(name, None)
            doc.network.parents.pop(name, None)
            for child, parents in list(doc.network.parents.items()):
                if name in parents:
                    parents.remove(name)
                    doc.network.cpds[child] = {}
                    self._rebuild_table(child)
        instances = self.nodes.get(name, [])
        if instances:
            # remove all diagram instances for simplicity
            for oval_id, text_id, fill_tag in instances:
                self.canvas.delete(oval_id)
                self.canvas.delete(text_id)
                find_withtag = getattr(self.canvas, "find_withtag", None)
                if find_withtag:
                    for fid in find_withtag(fill_tag):
                        self.canvas.delete(fid)
                        self.id_to_node.pop(fid, None)
                self.id_to_node.pop(oval_id, None)
                self.id_to_node.pop(text_id, None)
        self.nodes.pop(name, None)
        if name in self.tables:
            for win, frame, _ in self.tables.pop(name):
                self.canvas.delete(win)
                frame.destroy()
        doc.positions.pop(name, None)
        doc.types.pop(name, None)
        if self.selected_node and self.selected_node[0] == name:
            self._highlight_node(None)
        for line, src, dst in self.edges[:]:
            if src == name or dst == name:
                self.canvas.delete(line)
                self.edges.remove((line, src, dst))
        self._update_scroll_region()

    # ------------------------------------------------------------------
    def _rename_node(self, old: str, new: str) -> None:
        doc = getattr(self.app, "active_cbn", None)
        if not doc:
            return
        doc.network.nodes = [new if n == old else n for n in doc.network.nodes]
        doc.network.cpds[new] = doc.network.cpds.pop(old)
        if old in doc.network.parents:
            doc.network.parents[new] = doc.network.parents.pop(old)
        for child, parents in doc.network.parents.items():
            doc.network.parents[child] = [new if p == old else p for p in parents]
        doc.positions[new] = doc.positions.pop(old)
        doc.types[new] = doc.types.pop(old)
        tables = self.tables.pop(old, [])
        for win, frame, _ in tables:
            self.canvas.delete(win)
            frame.destroy()
        instances = self.nodes.pop(old, [])
        find_withtag = getattr(self.canvas, "find_withtag", None)
        new_instances = []
        for idx, (oval_id, text_id, old_fill_tag) in enumerate(instances):
            new_tag = self._generate_fill_tag(new, idx)
            new_instances.append((oval_id, text_id, new_tag))
            self.id_to_node[oval_id] = (new, idx)
            self.id_to_node[text_id] = (new, idx)
            if find_withtag:
                for fid in find_withtag(old_fill_tag):
                    self.canvas.itemconfigure(fid, tags=(new_tag,))
                    self.id_to_node[fid] = (new, idx)
        self.nodes[new] = new_instances
        kind = doc.types.get(new)
        if kind == "trigger":
            stereo = "triggering condition"
        elif kind == "insufficiency":
            stereo = "functional insufficiency"
        elif kind == "malfunction":
            stereo = "malfunction"
        elif kind == "variable":
            stereo = "variable"
        else:
            stereo = None
        label = f"<<{stereo}>>\n{new}" if stereo else new
        if hasattr(self, "text_font"):
            self.canvas.itemconfigure(text_id, text=label, font=self.text_font)
        else:
            self.canvas.itemconfigure(text_id, text=label)
        for idx, (line, src, dst) in enumerate(self.edges):
            s = new if src == old else src
            d = new if dst == old else dst
            self.edges[idx] = (line, s, d)
        self._rebuild_table(new)
        for child, parents in doc.network.parents.items():
            if new in parents and child != new:
                self._rebuild_table(child)

    # ------------------------------------------------------------------
    def _clone_node_strategy1(self, node: tuple) -> tuple | None:
        doc = getattr(self.app, "active_cbn", None)
        if not doc:
            return None
        name, idx = node
        if name not in doc.network.nodes:
            return None
        return (doc, name, idx)

    def _clone_node_strategy2(self, node: tuple) -> tuple | None:
        snap = self._clone_node_strategy1(node)
        if snap:
            return snap
        return None

    def _clone_node_strategy3(self, node: tuple) -> tuple | None:
        snap = self._clone_node_strategy1(node)
        if snap:
            return (lambda s: s)(snap)
        return None

    def _clone_node_strategy4(self, node: tuple) -> tuple | None:
        return self._clone_node_strategy1(node)

    def _clone_node(self, node: tuple) -> tuple | None:
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
    def _add_position_strategy1(self, doc, name, pos):
        doc.positions.setdefault(name, []).append(pos)
        return len(doc.positions[name]) - 1

    def _add_position_strategy2(self, doc, name, pos):
        doc.positions.setdefault(name, [])
        doc.positions[name] += [pos]
        return len(doc.positions[name]) - 1

    def _add_position_strategy3(self, doc, name, pos):
        lst = doc.positions.get(name)
        if lst is None:
            doc.positions[name] = [pos]
            return 0
        lst.append(pos)
        return len(lst) - 1

    def _add_position_strategy4(self, doc, name, pos):
        return self._add_position_strategy1(doc, name, pos)

    def _add_position(self, doc, name, pos):
        for strat in (
            self._add_position_strategy1,
            self._add_position_strategy2,
            self._add_position_strategy3,
            self._add_position_strategy4,
        ):
            try:
                idx = strat(doc, name, pos)
                return idx
            except Exception:
                continue
        return 0

    def _reconstruct_node_strategy1(self, snap, doc, offset=(20, 20)) -> tuple:
        src_doc, name, idx = snap
        # share underlying network structures so edits in one diagram
        # propagate to all others referencing the same document
        if doc.network.nodes is not src_doc.network.nodes:
            doc.network.nodes = src_doc.network.nodes
        if doc.network.parents is not src_doc.network.parents:
            doc.network.parents = src_doc.network.parents
        if doc.network.cpds is not src_doc.network.cpds:
            doc.network.cpds = src_doc.network.cpds
        if doc.types is not src_doc.types:
            doc.types = src_doc.types
        if name not in doc.network.nodes:
            doc.network.nodes.append(name)
        doc.types.setdefault(name, src_doc.types.get(name, "variable"))
        src_pos = src_doc.positions.get(name, [(0.0, 0.0)])[idx]
        new_pos = (src_pos[0] + offset[0], src_pos[1] + offset[1])
        new_idx = self._add_position(doc, name, new_pos)
        return (name, new_idx)

    def _reconstruct_node_strategy2(self, snap, doc, offset=(30, 30)) -> tuple:
        return self._reconstruct_node_strategy1(snap, doc, offset)

    def _reconstruct_node_strategy3(self, snap, doc, offset=(40, 40)) -> tuple:
        return self._reconstruct_node_strategy1(snap, doc, offset)

    def _reconstruct_node_strategy4(self, snap, doc, offset=(50, 50)) -> tuple:
        return self._reconstruct_node_strategy1(snap, doc, offset)

    def _reconstruct_node(self, snap, doc) -> tuple | None:
        for strat in (
            self._reconstruct_node_strategy1,
            self._reconstruct_node_strategy2,
            self._reconstruct_node_strategy3,
            self._reconstruct_node_strategy4,
        ):
            try:
                return strat(snap, doc)
            except Exception:
                continue
        return None

    def copy_selected(self, _event=None) -> None:
        if not self.app or not self.selected_node:
            return
        snap = self._clone_node(self.selected_node)
        if snap:
            self.app.diagram_clipboard.diagram_clipboard = snap
            self.app.diagram_clipboard.diagram_clipboard_type = "Causal Bayesian Network"

    def cut_selected(self, _event=None) -> None:
        if not self.app or not self.selected_node:
            return
        self.copy_selected()
        self._delete_node(self.selected_node)
        self.selected_node = None

    def paste_selected(self, _event=None) -> None:
        doc = getattr(self.app, "active_cbn", None)
        if not doc or not self.app or not getattr(self.app.diagram_clipboard, "diagram_clipboard", None):
            return
        clip_type = getattr(self.app.diagram_clipboard, "diagram_clipboard_type", None)
        if clip_type and clip_type != "Causal Bayesian Network":
            messagebox.showwarning("Paste", "Clipboard contains incompatible diagram element.")
            return
        res = self._reconstruct_node(self.app.diagram_clipboard.diagram_clipboard, doc)
        if not res:
            return
        name, idx = res
        x, y = doc.positions[name][idx]
        kind = doc.types.get(name)
        self._draw_node(name, x, y, kind, idx)
        for parent in doc.network.parents.get(name, []):
            if parent in doc.network.nodes:
                self._draw_edge(parent, name, 0, idx)

