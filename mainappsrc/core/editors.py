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

"""Editor helpers extracted from :mod:`automl_core`.

This module centralises UI editors and tables formerly implemented on
:class:`~mainappsrc.core.automl_core.AutoMLApp`.
"""

import csv
import uuid
import textwrap
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog
from typing import Any

from analysis.models import (
    ASIL_LEVEL_OPTIONS,
    CAL_LEVEL_OPTIONS,
    REQUIREMENT_TYPE_OPTIONS,
    global_requirements,
    ASIL_TARGETS,
    COMPONENT_ATTR_TEMPLATES,
)
from analysis.constants import CHECK_MARK, CROSS_MARK
from gui.controls import messagebox
from gui.controls.mac_button_style import apply_translucid_button_style
from gui.dialogs.req_dialog import ReqDialog
from gui.dialogs.fmea_row_dialog import FMEARowDialog
from gui.dialogs.select_base_event_dialog import SelectBaseEventDialog
from gui.toolboxes import DiagramElementDialog, _RequirementRelationDialog
from gui.windows.architecture import (
    link_requirement_to_object,
    unlink_requirement_from_object,
    link_requirements,
    unlink_requirements,
)
from mainappsrc.models.fta.fault_tree_node import FaultTreeNode
from mainappsrc.models.sysml.sysml_repository import SysMLRepository


class Editors:
    """Group editor dialogs and tables delegated from :class:`AutoMLApp`."""

    def __init__(self, app: Any) -> None:
        self.app = app

    # ------------------------------------------------------------------
    # Item definition
    # ------------------------------------------------------------------
    def show_item_definition_editor(self):  # pragma: no cover - UI code
        app = self.app
        """Open editor for item description and assumptions."""
        if hasattr(app, "_item_def_tab") and app._item_def_tab.winfo_exists():
            app.doc_nb.select(app._item_def_tab)
            return
        app._item_def_tab = app.lifecycle_ui._new_tab("Item Definition")
        win = app._item_def_tab
        ttk.Label(win, text="Item Description:").pack(anchor="w")
        app._item_desc_text = tk.Text(win, height=8, wrap="word")
        app._item_desc_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        ttk.Label(win, text="Assumptions:").pack(anchor="w")
        app._item_assum_text = tk.Text(win, height=8, wrap="word")
        app._item_assum_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        app._item_desc_text.insert("1.0", app.item_definition.get("description", ""))
        app._item_assum_text.insert("1.0", app.item_definition.get("assumptions", ""))

        def save() -> None:
            app.item_definition["description"] = app._item_desc_text.get("1.0", "end").strip()
            app.item_definition["assumptions"] = app._item_assum_text.get("1.0", "end").strip()

        ttk.Button(win, text="Save", command=save).pack(anchor="e", padx=5, pady=5)

    # ------------------------------------------------------------------
    # Safety concept
    # ------------------------------------------------------------------
    def show_safety_concept_editor(self):  # pragma: no cover - UI code
        app = self.app
        """Open editor for safety & security concept descriptions and assumptions."""
        if hasattr(app, "_safety_concept_tab") and app._safety_concept_tab.winfo_exists():
            app.doc_nb.select(app._safety_concept_tab)
            return
        app._safety_concept_tab = app.lifecycle_ui._new_tab("Safety & Security Concept")
        win = app._safety_concept_tab
        ttk.Label(
            win,
            text="Functional & Cybersecurity Concept Description and Assumptions:",
        ).pack(anchor="w")
        f_frame = ttk.Frame(win)
        f_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        app._fsc_text = tk.Text(f_frame, height=8, wrap="word")
        f_scroll = ttk.Scrollbar(f_frame, orient=tk.VERTICAL, command=app._fsc_text.yview)
        app._fsc_text.configure(yscrollcommand=f_scroll.set)
        app._fsc_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        f_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Label(
            win,
            text="Technical & Cybersecurity Concept Description & Assumptions:",
        ).pack(anchor="w")
        t_frame = ttk.Frame(win)
        t_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        app._tsc_text = tk.Text(t_frame, height=8, wrap="word")
        t_scroll = ttk.Scrollbar(t_frame, orient=tk.VERTICAL, command=app._tsc_text.yview)
        app._tsc_text.configure(yscrollcommand=t_scroll.set)
        app._tsc_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        t_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        c_frame = ttk.Frame(win)
        c_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        app._csc_text = tk.Text(c_frame, height=8, wrap="word")
        c_scroll = ttk.Scrollbar(c_frame, orient=tk.VERTICAL, command=app._csc_text.yview)
        app._csc_text.configure(yscrollcommand=c_scroll.set)
        app._csc_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        c_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        app._fsc_text.insert("1.0", app.safety_concept.get("functional", ""))
        app._tsc_text.insert("1.0", app.safety_concept.get("technical", ""))
        app._csc_text.insert("1.0", app.safety_concept.get("cybersecurity", ""))

        def save() -> None:
            app.safety_concept["functional"] = app._fsc_text.get("1.0", "end").strip()
            app.safety_concept["technical"] = app._tsc_text.get("1.0", "end").strip()
            app.safety_concept["cybersecurity"] = app._csc_text.get("1.0", "end").strip()

        ttk.Button(win, text="Save", command=save).pack(anchor="e", padx=5, pady=5)

    # ------------------------------------------------------------------
    # Requirements editor
    # ------------------------------------------------------------------
    def show_requirements_editor(self):  # pragma: no cover - UI heavy
        app = self.app
        """Open an editor to manage global requirements."""
        app.update_requirement_statuses()
        if hasattr(app, "_req_tab") and app._req_tab.winfo_exists():
            app.doc_nb.select(app._req_tab)
            return
        app._req_tab = app.lifecycle_ui._new_tab("Requirements")
        win = app._req_tab

        columns = ["ID", "ASIL", "CAL", "Type", "Status", "Parent", "Trace", "Links", "Text"]
        tree_frame = ttk.Frame(win)
        style = ttk.Style(tree_frame)
        style.configure("ReqEditor.Treeview", rowheight=20)
        tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
            style="ReqEditor.Treeview",
        )
        tree.configure(height=10)
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        for col in columns:
            tree.heading(col, text=col)
            if col == "Text":
                width = 300
            elif col in ("Trace", "Links"):
                width = 200
            else:
                width = 120
            tree.column(col, width=width, anchor="center")
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        def _get_requirement_allocations(rid: str) -> list[str]:
            repo = SysMLRepository.get_instance()
            names: list[str] = []
            for diag in repo.diagrams.values():
                dname = diag.name or diag.diag_id
                for obj in getattr(diag, "objects", []):
                    for r in obj.get("requirements", []):
                        if r.get("id") == rid:
                            oname = obj.get("properties", {}).get("name", obj.get("obj_type"))
                            names.append(f"{dname}:{oname}")
            return sorted(set(names))

        def refresh_tree() -> None:
            tree.delete(*tree.get_children())
            max_lines = 1
            for req in global_requirements.values():
                rid = req.get("id", "")
                trace = ", ".join(_get_requirement_allocations(rid))
                links = ", ".join(
                    f"{r.get('type')} {r.get('id')}" for r in req.get("relations", [])
                )
                text = textwrap.fill(req.get("text", ""), width=40)
                max_lines = max(max_lines, text.count("\n") + 1)
                tree.insert(
                    "",
                    "end",
                    iid=rid,
                    values=[
                        rid,
                        req.get("asil", ""),
                        req.get("cal", ""),
                        req.get("req_type", ""),
                        req.get("status", "draft"),
                        req.get("parent_id", ""),
                        trace,
                        links,
                        text,
                    ],
                )
            style.configure("ReqEditor.Treeview", rowheight=20 * max_lines)

        refresh_tree()

        # Buttons -------------------------------------------------------
        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Add", command=lambda: app.add_requirement(tree, refresh_tree)).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Edit", command=lambda: app.edit_requirement(tree, refresh_tree)).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Delete", command=lambda: app.delete_requirement(tree, refresh_tree)).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Link", command=lambda: app.link_requirement(tree, refresh_tree)).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Unlink", command=lambda: app.unlink_requirement(tree, refresh_tree)).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Export", command=app.export_requirements_to_csv).pack(side=tk.LEFT)

    # ------------------------------------------------------------------
    # Requirements matrix
    # ------------------------------------------------------------------
    def show_requirements_matrix(self):
        app = self.app
        """Display a matrix table of requirements vs. basic events."""
        app.update_requirement_statuses()
        basic_events = [n for n in app.get_all_nodes(app.root_node)
                        if n.node_type.upper() == "BASIC EVENT"]
        reqs = list(global_requirements.values())
        reqs.sort(key=lambda r: r.get("req_type", ""))

        if hasattr(app, "_new_tab"):
            win = app._new_tab("Requirements Matrix")
        else:
            win = tk.Toplevel(app.root)
            win.title("Requirements Matrix")

        columns = [
            "Req ID",
            "ASIL",
            "CAL",
            "Type",
            "Status",
            "Parent",
            "Text",
        ] + [be.user_name or f"BE {be.unique_id}" for be in basic_events]
        tree = ttk.Treeview(win, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120 if col not in ["Text"] else 300, anchor="center")
        tree.pack(fill=tk.BOTH, expand=True)


        for req in reqs:
            row = [
                req.get("id", ""),
                req.get("asil", ""),
                req.get("cal", ""),
                req.get("req_type", ""),
                req.get("status", "draft"),
                req.get("parent_id", ""),
                req.get("text", ""),
            ]
            for be in basic_events:
                linked = any(r.get("id") == req.get("id") for r in getattr(be, "safety_requirements", []))
                row.append("X" if linked else "")
            tree.insert("", "end", values=row)

        # Show allocation and safety goal traceability below the table
        frame = tk.Frame(win)
        frame.pack(fill=tk.BOTH, expand=True)
        vbar = ttk.Scrollbar(frame, orient="vertical")
        text = tk.Text(frame, wrap="word", yscrollcommand=vbar.set, height=8)
        text.tag_configure("added", foreground="blue")
        text.tag_configure("removed", foreground="red")
        vbar.config(command=text.yview)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)

        base_data = app.versions[-1]["data"] if app.versions else None

        def alloc_from_data(req_id):
            if not base_data:
                return ""
            names = []
            def traverse(d):
                if any(r.get("id") == req_id for r in d.get("safety_requirements", [])):
                    names.append(d.get("user_name") or f"Node {d.get('unique_id')}")
                for ch in d.get("children", []):
                    traverse(ch)
            for t in base_data.get("top_events", []):
                traverse(t)
            for fmea in base_data.get("fmeas", []):
                for e in fmea.get("entries", []):
                    if any(r.get("id") == req_id for r in e.get("safety_requirements", [])):
                        name = e.get("description") or e.get("user_name", f"BE {e.get('unique_id','')}")
                        names.append(f"{fmea['name']}:{name}")
            return ", ".join(names)

        def goals_from_data(req_id):
            if not base_data:
                return ""
            nodes = []
            def gather(n):
                nodes.append(n)
                for ch in n.get("children", []):
                    gather(ch)
            for t in base_data.get("top_events", []):
                gather(t)
            id_map = {n["unique_id"]: n for n in nodes}
            def collect_goal_names(nd, acc):
                if nd.get("node_type", "").upper() == "TOP EVENT":
                    acc.add(nd.get("safety_goal_description") or nd.get("user_name") or f"SG {nd.get('unique_id')}")
                for p in nd.get("parents", []):
                    pid = p.get("unique_id")
                    if pid and pid in id_map:
                        collect_goal_names(id_map[pid], acc)
            goals = set()
            for n in nodes:
                if any(r.get("id") == req_id for r in n.get("safety_requirements", [])):
                    collect_goal_names(n, goals)
            for fmea in base_data.get("fmeas", []):
                for e in fmea.get("entries", []):
                    if any(r.get("id") == req_id for r in e.get("safety_requirements", [])):
                        parents = e.get("parents", [])
                        if parents:
                            pid = parents[0].get("unique_id")
                            if pid and pid in id_map:
                                collect_goal_names(id_map[pid], goals)
            return ", ".join(sorted(goals))

        import difflib

        def insert_diff(widget, old, new):
            matcher = difflib.SequenceMatcher(None, old, new)
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag == "equal":
                    widget.insert(tk.END, new[j1:j2])
                elif tag == "delete":
                    widget.insert(tk.END, old[i1:i2], "removed")
                elif tag == "insert":
                    widget.insert(tk.END, new[j1:j2], "added")
                elif tag == "replace":
                    widget.insert(tk.END, old[i1:i2], "removed")
                    widget.insert(tk.END, new[j1:j2], "added")

        def insert_list_diff(widget, old, new):
            old_items = [s.strip() for s in old.split(',') if s.strip()]
            new_items = [s.strip() for s in new.split(',') if s.strip()]
            old_set = set(old_items)
            new_set = set(new_items)
            first = True
            for item in new_items:
                if not first:
                    widget.insert(tk.END, ", ")
                first = False
                if item not in old_set:
                    widget.insert(tk.END, item, "added")
                else:
                    widget.insert(tk.END, item)
            for item in old_items:
                if item not in new_set:
                    if not first:
                        widget.insert(tk.END, ", ")
                    first = False
                    widget.insert(tk.END, item, "removed")

        for req in reqs:
            rid = req.get("id")
            alloc = ", ".join(app.get_requirement_allocation_names(rid))
            goals = ", ".join(app.get_requirement_goal_names(rid))
            text.insert(tk.END, f"[{rid}] {req.get('text','')}\n")
            text.insert(tk.END, "  Allocated to: ")
            if base_data:
                insert_list_diff(text, alloc_from_data(rid), alloc)
            else:
                text.insert(tk.END, alloc)
            text.insert(tk.END, "\n  Safety Goals: ")
            if base_data:
                insert_diff(text, goals_from_data(rid), goals)
            else:
                text.insert(tk.END, goals)
            text.insert(tk.END, "\n\n")

        tk.Button(win, text="Open Requirements Editor", command=app.show_requirements_editor).pack(pady=5)


    # ------------------------------------------------------------------
    # FMEA/FMeda table
    # ------------------------------------------------------------------
    def _show_fmea_table_impl(self, fmea=None, fmeda=False):
        app = self.app
        """Internal implementation for rendering FMEA/FMeda tables."""
        # Use failure modes defined on gates or within FMEA/FMEDA documents.
        # Do not include FTA base events as selectable failure modes.
        basic_events = app.get_non_basic_failure_modes()
        entries = app.fmea_entries if fmea is None else fmea['entries']
        title = f"FMEA Table - {fmea['name']}" if fmea else "FMEA Table"
        win = app.lifecycle_ui._new_tab(title)

        # give the table a nicer look similar to professional FMEA tools
        style = ttk.Style(app.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        apply_translucid_button_style(style)
        style.configure(
            "FMEA.Treeview",
            font=("Segoe UI", 10),
            rowheight=60,
            background="#ffffff",
            fieldbackground="#ffffff",
            foreground="black",
        )
        style.configure(
            "FMEA.Treeview.Heading",
            font=("Segoe UI", 10, "bold"),
            background="#b5bdc9",
            foreground="black",
            relief="raised",
        )
        style.map(
            "FMEA.Treeview.Heading",
            background=[("active", "#4a6ea9"), ("!active", "#b5bdc9")],
            foreground=[("active", "white"), ("!active", "black")],
        )

        columns = [
            "Component",
            "Parent",
            "Failure Mode",
            "Failure Effect",
            "Cause",
            "S",
            "O",
            "D",
            "RPN",
            "Requirements",
            "Malfunction",
        ]
        if fmeda:
            columns.extend([
                "Safety Goal",
                "FaultType",
                "Fraction",
                "FIT",
                "DiagCov",
                "Mechanism",
            ])
        columns.extend(["Created", "Author", "Modified", "ModifiedBy"])
        btn_frame = ttk.Frame(win)
        btn_frame.pack(side=tk.TOP, pady=2)
        add_btn = ttk.Button(btn_frame, text="Add Failure Mode")
        add_btn.pack(side=tk.LEFT, padx=2)
        remove_btn = ttk.Button(btn_frame, text="Remove from FMEA")
        remove_btn.pack(side=tk.LEFT, padx=2)
        del_btn = ttk.Button(btn_frame, text="Delete Selected")
        del_btn.pack(side=tk.LEFT, padx=2)
        comment_btn = ttk.Button(btn_frame, text="Comment")
        comment_btn.pack(side=tk.LEFT, padx=2)
        toolbox = getattr(app, "safety_mgmt_toolbox", None)
        if fmea and toolbox and toolbox.document_read_only("FMEA", fmea["name"]):
            for b in (add_btn, remove_btn, del_btn, comment_btn):
                b.state(["disabled"])
        if fmeda:
            def calculate_fmeda():
                if bom_var.get():
                    load_bom()
                else:
                    refresh_tree()
                metrics = app.compute_fmeda_metrics(entries)
                asil = metrics["asil"]
                dc = metrics["dc"]
                spfm_m = metrics["spfm_metric"]
                lpfm_m = metrics["lpfm_metric"]
                thresh = ASIL_TARGETS.get(asil, ASIL_TARGETS["QM"])
                ok_dc = dc >= thresh["dc"]
                ok_spf = spfm_m >= thresh["spfm"]
                ok_lpf = lpfm_m >= thresh["lpfm"]
                msg = (
                    f"Total FIT: {app.reliability_total_fit:.2f}\n"
                    f"DC: {dc:.2f} {'PASS' if ok_dc else 'FAIL'}\n"
                    f"SPFM: {spfm_m:.2f} {'PASS' if ok_spf else 'FAIL'}\n"
                    f"LPFM: {lpfm_m:.2f} {'PASS' if ok_lpf else 'FAIL'}\n"
                    f"ASIL {asil}"
                )
                messagebox.showinfo("FMEDA", msg)

            calc_btn = ttk.Button(btn_frame, text="Calculate FMEDA", command=calculate_fmeda)
            calc_btn.pack(side=tk.LEFT, padx=2)
            ttk.Label(btn_frame, text="BOM:").pack(side=tk.LEFT, padx=2)
            bom_var = tk.StringVar(value=fmea.get('bom', ''))
            bom_combo = ttk.Combobox(
                btn_frame,
                textvariable=bom_var,
                values=[ra.name for ra in app.reliability_analyses],
                state="readonly",
                width=20,
            )
            bom_combo.pack(side=tk.LEFT, padx=2)

            def add_component():
                dlg = tk.Toplevel(win)
                dlg.title("New Component")
                ttk.Label(dlg, text="Name").grid(row=0, column=0, padx=5, pady=5, sticky="e")
                name_var = tk.StringVar()
                ttk.Entry(dlg, textvariable=name_var).grid(row=0, column=1, padx=5, pady=5)
                ttk.Label(dlg, text="Type").grid(row=1, column=0, padx=5, pady=5, sticky="e")
                type_var = tk.StringVar(value="capacitor")
                type_cb = ttk.Combobox(
                    dlg,
                    textvariable=type_var,
                    values=list(COMPONENT_ATTR_TEMPLATES.keys()),
                    state="readonly",
                )
                type_cb.grid(row=1, column=1, padx=5, pady=5)
                ttk.Label(dlg, text="Quantity").grid(row=2, column=0, padx=5, pady=5, sticky="e")
                qty_var = tk.IntVar(value=1)
                ttk.Entry(dlg, textvariable=qty_var).grid(row=2, column=1, padx=5, pady=5)
                ttk.Label(dlg, text="Qualification").grid(row=3, column=0, padx=5, pady=5, sticky="e")
                qual_var = tk.StringVar(value="None")
                ttk.Combobox(dlg, textvariable=qual_var, values=QUALIFICATIONS, state="readonly").grid(row=3, column=1, padx=5, pady=5)
                passive_var = tk.BooleanVar(value=False)
                ttk.Checkbutton(dlg, text="Passive", variable=passive_var).grid(row=4, column=0, columnspan=2, pady=5)

                attr_frame = ttk.Frame(dlg)
                attr_frame.grid(row=5, column=0, columnspan=2)
                attr_vars = {}

                def refresh_attr_fields(*_):
                    for child in attr_frame.winfo_children():
                        child.destroy()
                    attr_vars.clear()
                    template = COMPONENT_ATTR_TEMPLATES.get(type_var.get(), {})
                    for i, (k, v) in enumerate(template.items()):
                        ttk.Label(attr_frame, text=k).grid(row=i, column=0, padx=5, pady=5, sticky="e")
                        if isinstance(v, list):
                            var = tk.StringVar(value=v[0])
                            ttk.Combobox(attr_frame, textvariable=var, values=v, state="readonly").grid(row=i, column=1, padx=5, pady=5)
                        else:
                            var = tk.StringVar(value=str(v))
                            ttk.Entry(attr_frame, textvariable=var).grid(row=i, column=1, padx=5, pady=5)
                        attr_vars[k] = var

                type_cb.bind("<<ComboboxSelected>>", refresh_attr_fields)
                refresh_attr_fields()

                def ok():
                    comp = ReliabilityComponent(
                        name_var.get(),
                        type_var.get(),
                        qty_var.get(),
                        {},
                        qual_var.get(),
                        is_passive=passive_var.get(),
                    )
                    for k, var in attr_vars.items():
                        comp.attributes[k] = var.get()
                    app.reliability_components.append(comp)
                    dlg.destroy()
                    refresh_tree()

                ttk.Button(dlg, text="Add", command=ok).grid(row=6, column=0, columnspan=2, pady=5)
                dlg.grab_set()
                dlg.wait_window()

            ttk.Button(btn_frame, text="Add Component", command=add_component).pack(side=tk.LEFT, padx=2)

            selected_libs = app.selected_mechanism_libraries

            def choose_libs():
                dlg = tk.Toplevel(win)
                dlg.title("Select Libraries")
                vars = {}
                for i, lib in enumerate(app.mechanism_libraries):
                    var = tk.BooleanVar(value=lib in selected_libs)
                    tk.Checkbutton(dlg, text=lib.name, variable=var).pack(anchor="w")
                    vars[i] = (var, lib)

                def ok():
                    selected_libs.clear()
                    for _, (v, lib) in vars.items():
                        if v.get():
                            selected_libs.append(lib)
                    dlg.destroy()

                ttk.Button(dlg, text="OK", command=ok).pack(pady=5)
                dlg.grab_set()
                dlg.wait_window()

            ttk.Button(btn_frame, text="Libraries", command=choose_libs).pack(side=tk.LEFT, padx=2)

            def load_bom(*_):
                name = bom_var.get()
                ra = next((r for r in app.reliability_analyses if r.name == name), None)
                if ra:
                    app.reliability_components = copy.deepcopy(ra.components)
                    app.reliability_total_fit = ra.total_fit
                    app.spfm = ra.spfm
                    app.lpfm = ra.lpfm
                    if fmea is not None:
                        fmea['bom'] = name
                    refresh_tree()

            bom_combo.bind("<<ComboboxSelected>>", load_bom)

        tree_frame = ttk.Frame(win)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="tree headings",
            style="FMEA.Treeview",
        )
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        for col in columns:
            tree.heading(col, text=col)
            width = 120
            if col in ["Requirements", "Failure Effect", "Cause", "Safety Goal", "Malfunction"]:
                width = 200
            elif col == "Parent":
                width = 150
            elif col in ["FaultType", "Fraction", "FIT", "DiagCov", "Mechanism"]:
                width = 80
            elif col in ["Created", "Modified"]:
                width = 130
            elif col in ["Author", "ModifiedBy"]:
                width = 100
            tree.column(col, width=width, anchor="center")
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        metrics_lbl = tk.Label(win, text="", anchor="w")
        metrics_lbl.pack(anchor="w", padx=5, pady=2)

        # alternating row colours and high RPN highlight
        tree.tag_configure("component", background="#e2e2e2", font=("Segoe UI", 10, "bold"))
        tree.tag_configure("evenrow", background="#ffffff")
        tree.tag_configure("oddrow", background="#f5f5f5")
        tree.tag_configure("highrpn", background="#ffe6e6")

        node_map = {}
        comp_items = {}
        # expose the current FMEA tree and node mapping for external tools
        app._fmea_tree = tree
        app._fmea_node_map = node_map

        def refresh_tree():
            tree.delete(*tree.get_children())
            node_map.clear()
            comp_items.clear()
            # remove any duplicate nodes based on unique_id
            unique = {}
            for be in entries:
                unique[be.unique_id] = be
            entries[:] = list(unique.values())
            events = entries

            comp_fit = component_fit_map(app.reliability_components)
            frac_totals = {}
            for be in events:
                src = app.get_failure_mode_node(be)
                comp_name = app.get_component_name_for_node(src)
                fit = comp_fit.get(comp_name)
                frac = src.fmeda_fault_fraction
                if frac > 1.0:
                    frac /= 100.0
                if fit is not None:
                    value = fit * frac
                else:
                    value = getattr(src, "fmeda_fit", 0.0)

                be.fmeda_fit = value
                src.fmeda_fit = value

                if src.fmeda_fault_type == "permanent":
                    spfm = value * (1 - src.fmeda_diag_cov)
                    lpfm = 0.0
                else:
                    lpfm = value * (1 - src.fmeda_diag_cov)
                    spfm = 0.0

                be.fmeda_spfm = spfm
                be.fmeda_lpfm = lpfm
                src.fmeda_spfm = spfm
                src.fmeda_lpfm = lpfm
                frac_totals[comp_name] = frac_totals.get(comp_name, 0.0) + frac

            warnings = [f"{name} fractions={val:.2f}" for name, val in frac_totals.items() if abs(val - 1.0) > 0.01]
            if warnings:
                messagebox.showwarning("Distribution", "Fault fraction sum != 1:\n" + "\n".join(warnings))

            for idx, be in enumerate(events):
                src = app.get_failure_mode_node(be)
                comp = app.get_component_name_for_node(src) or "N/A"
                parent = src.parents[0] if src.parents else None
                parent_name = parent.user_name if parent and getattr(parent, "node_type", "").upper() not in GATE_NODE_TYPES else ""
                if comp not in comp_items:
                    comp_items[comp] = tree.insert(
                        "",
                        "end",
                        text=comp,
                        values=[comp] + [""] * (len(columns) - 1),
                        tags=("component",),
                    )
                comp_iid = comp_items[comp]
                req_ids = "; ".join(
                    [f"{req['req_type']}:{req['text']}" for req in getattr(src, "safety_requirements", [])]
                )
                rpn = src.fmea_severity * src.fmea_occurrence * src.fmea_detection
                failure_mode = src.description or (src.user_name or f"BE {src.unique_id}")
                vals = [
                    "",
                    parent_name,
                    failure_mode,
                    src.fmea_effect,
                    src.fmea_cause,
                    src.fmea_severity,
                    src.fmea_occurrence,
                    src.fmea_detection,
                    rpn,
                    req_ids,
                    src.fmeda_malfunction,
                ]
                if fmeda:
                    sg_value = src.fmeda_safety_goal
                    goals = app.get_top_event_safety_goals(src)
                    if goals:
                        sg_value = ", ".join(goals)
                    vals.extend([
                        sg_value,
                        src.fmeda_fault_type,
                        f"{src.fmeda_fault_fraction:.2f}",
                        f"{src.fmeda_fit:.2f}",
                        f"{src.fmeda_diag_cov:.2f}",
                        getattr(src, "fmeda_mechanism", ""),
                    ])
                vals.extend([
                    getattr(src, "created", ""),
                    getattr(src, "author", ""),
                    getattr(src, "modified", ""),
                    getattr(src, "modified_by", ""),
                ])
                tags = ["evenrow" if idx % 2 == 0 else "oddrow"]
                if rpn >= 100:
                    tags.append("highrpn")
                iid = tree.insert(comp_iid, "end", text="", values=vals, tags=tags)
                node_map[iid] = be
            for iid in comp_items.values():
                tree.item(iid, open=True)

            if fmeda:
                metrics = app.compute_fmeda_metrics(events)
                asil = metrics["asil"]
                dc = metrics["dc"]
                spfm_metric = metrics["spfm_metric"]
                lpfm_metric = metrics["lpfm_metric"]
                thresh = ASIL_TARGETS.get(asil, ASIL_TARGETS["QM"])
                ok_dc = dc >= thresh["dc"]
                ok_spf = spfm_metric >= thresh["spfm"]
                ok_lpf = lpfm_metric >= thresh["lpfm"]
                text = (
                    f"Total FIT: {app.reliability_total_fit:.2f}  DC: {dc:.2f}{CHECK_MARK if ok_dc else CROSS_MARK}"
                    f"  SPFM: {spfm_metric:.2f}{CHECK_MARK if ok_spf else CROSS_MARK}"
                    f"  LPFM: {lpfm_metric:.2f}{CHECK_MARK if ok_lpf else CROSS_MARK}"
                    f"  (ASIL {asil})"
                )
                if metrics.get("goal_metrics"):
                    parts = []
                    for sg, gm in metrics["goal_metrics"].items():
                        ok = gm["ok_dc"] and gm["ok_spfm"] and gm["ok_lpfm"]
                        symbol = CHECK_MARK if ok else CROSS_MARK
                        parts.append(f"{sg}:{symbol}")
                    text += " [" + "; ".join(parts) + "]"
                overall_ok = ok_dc and ok_spf and ok_lpf
                if metrics.get("goal_metrics"):
                    overall_ok = overall_ok and all(
                        gm["ok_dc"] and gm["ok_spfm"] and gm["ok_lpfm"]
                        for gm in metrics["goal_metrics"].values()
                    )
                color = "#c8ffc8" if overall_ok else "#ffc8c8"
                metrics_lbl.config(text=text, bg=color)

        if fmeda and bom_var.get():
            load_bom()
        else:
            refresh_tree()

        def on_double(event):
            sel = tree.focus()
            node = node_map.get(sel)
            if node:
                mechs = []
                for lib in selected_libs:
                    mechs.extend(lib.mechanisms)
                comp_name = app.get_component_name_for_node(node)
                is_passive = any(c.name == comp_name and c.is_passive for c in app.reliability_components)
                FMEARowDialog(win, node, app, entries, mechanisms=mechs, hide_diagnostics=is_passive, is_fmeda=fmeda)
                refresh_tree()

        tree.bind("<Double-1>", on_double)

        def add_failure_mode():
            dialog = SelectBaseEventDialog(win, basic_events, allow_new=True)
            node = dialog.selected
            if node == "NEW":
                node = FaultTreeNode("", "Basic Event")
                entries.append(node)
                mechs = []
                for lib in selected_libs:
                    mechs.extend(lib.mechanisms)
                comp_name = getattr(node, "fmea_component", "")
                is_passive = any(c.name == comp_name and c.is_passive for c in app.reliability_components)
                FMEARowDialog(win, node, app, entries, mechanisms=mechs, hide_diagnostics=is_passive, is_fmeda=fmeda)
            elif node:
                # gather all failure modes under the same component/parent
                if node.parents:
                    parent_id = node.parents[0].unique_id
                    related = [
                        be
                        for be in basic_events
                        if be.parents and be.parents[0].unique_id == parent_id
                    ]
                else:
                    comp = getattr(node, "fmea_component", "")
                    related = [
                        be
                        for be in basic_events
                        if not be.parents and getattr(be, "fmea_component", "") == comp
                    ]
                if node not in related:
                    related.append(node)
                existing_ids = {be.unique_id for be in entries}
                for be in related:
                    if be.unique_id not in existing_ids:
                        entries.append(be)
                        existing_ids.add(be.unique_id)
                    mechs = []
                    for lib in selected_libs:
                        mechs.extend(lib.mechanisms)
                    comp_name = app.get_component_name_for_node(be)
                is_passive = any(c.name == comp_name and c.is_passive for c in app.reliability_components)
                FMEARowDialog(win, be, app, entries, mechanisms=mechs, hide_diagnostics=is_passive, is_fmeda=fmeda)
            refresh_tree()
            if fmea is not None:
                app.lifecycle_ui.touch_doc(fmea)

        add_btn.config(command=add_failure_mode)

        def remove_from_fmea():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Remove Entry", "Select a row to remove.")
                return
            for iid in sel:
                node = node_map.get(iid)
                if node in entries:
                    entries.remove(node)
            refresh_tree()
            if fmea is not None:
                app.lifecycle_ui.touch_doc(fmea)

        remove_btn.config(command=remove_from_fmea)

        def delete_failure_mode():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Delete Failure Mode", "Select a row to delete.")
                return
            if not messagebox.askyesno("Delete Failure Mode", "Remove selected failure modes from the FMEA?"):
                return
            for iid in sel:
                node = node_map.get(iid)
                if node in entries:
                    entries.remove(node)
            refresh_tree()
            if fmea is not None:
                app.lifecycle_ui.touch_doc(fmea)

        del_btn.config(command=delete_failure_mode)

        def comment_fmea_entry():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Comment", "Select a row to comment.")
                return
            node = node_map.get(sel[0])
            if not node:
                return
            app.selected_node = node
            app.comment_target = ("fmea", node.unique_id)
            app.open_review_toolbox()

        comment_btn.config(command=comment_fmea_entry)

        def on_close():
            if fmea is not None:
                app.lifecycle_ui.touch_doc(fmea)
                if fmeda:
                    app.export_fmeda_to_csv(fmea, fmea['file'])
                else:
                    app.export_fmea_to_csv(fmea, fmea['file'])
                if fmeda:
                    fmea['bom'] = bom_var.get()
            win.destroy()

        if hasattr(win, "protocol"):
            win.protocol("WM_DELETE_WINDOW", on_close)
        else:
            win.bind("<Destroy>", lambda e: on_close() if e.widget is win else None)


