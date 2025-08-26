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

"""Requirement management utilities for AutoML."""

import csv
import json
from typing import Dict, Any, Set
from functools import partial

import tkinter as tk
from tkinter import ttk, simpledialog, filedialog

from gui.controls import messagebox
from gui.dialogs.req_dialog import ReqDialog
from gui.toolboxes import _RequirementRelationDialog
if __package__ and __package__.startswith("AutoML"):
    from AutoML.config.automl_constants import PMHF_TARGETS
else:  # pragma: no cover - script context
    from config.automl_constants import PMHF_TARGETS
from mainappsrc.models.fta.fault_tree_node import FaultTreeNode
from analysis.models import ASIL_ORDER, global_requirements, ensure_requirement_defaults
from gui.windows.architecture import link_requirements, unlink_requirements

try:  # pragma: no cover - optional dependency
    from mainappsrc.models.sysml.sysml_repository import SysMLRepository
except Exception:  # pragma: no cover
    SysMLRepository = None  # type: ignore


class RequirementsManagerSubApp:
    """Encapsulate requirement traceability helpers."""

    def __init__(self, app: Any) -> None:
        self.app = app

    # ------------------------------------------------------------------
    def export_state(self) -> Dict[str, Any]:
        """Serialize requirement editor state for project export.

        The requirements manager currently stores no mutable state beyond what
        is held in the main application model. The export therefore returns an
        empty mapping, acting as a placeholder for future requirement editor
        data.
        """
        return {}

    # ------------------------------------------------------------------
    def get_requirement_allocation_names(self, req_id: str) -> list[str]:
        """Return names of model elements linked to ``req_id``."""
        names: list[str] = []
        repo = SysMLRepository.get_instance() if SysMLRepository else None
        if repo:
            for diag_id, obj_id in repo.find_requirements(req_id):
                diag = repo.diagrams.get(diag_id)
                obj = next((o for o in getattr(diag, "objects", []) if o.get("obj_id") == obj_id), None)
                dname = diag.name if diag else ""
                oname = obj.get("properties", {}).get("name", "") if obj else ""
                if dname and oname:
                    names.append(f"{dname}:{oname}")
                elif dname or oname:
                    names.append(dname or oname)
            for diag in repo.diagrams.values():
                for obj in getattr(diag, "objects", []):
                    reqs = obj.get("requirements", [])
                    if any(r.get("id") == req_id for r in reqs):
                        name = obj.get("properties", {}).get("name") or obj.get("obj_type", "")
                        names.append(name)
        for n in self.app.get_all_nodes(self.app.root_node):
            reqs = getattr(n, "safety_requirements", [])
            if any((r.get("id") if isinstance(r, dict) else getattr(r, "id", None)) == req_id for r in reqs):
                names.append(n.user_name or f"Node {n.unique_id}")
        for fmea in self.app.fmeas:
            for e in fmea.get("entries", []):
                reqs = e.get("safety_requirements", []) if isinstance(e, dict) else getattr(e, "safety_requirements", [])
                if any((r.get("id") if isinstance(r, dict) else getattr(r, "id", None)) == req_id for r in reqs):
                    if isinstance(e, dict):
                        name = e.get("description") or e.get("user_name", f"BE {e.get('unique_id','')}")
                    else:
                        name = getattr(e, "description", "") or getattr(e, "user_name", f"BE {getattr(e, 'unique_id', '')}")
                    names.append(f"{fmea['name']}:{name}")
        return names

    # ------------------------------------------------------------------
    def _collect_goal_names(self, node: Any, acc: Set[str]) -> None:
        if node.node_type.upper() == "TOP EVENT":
            acc.add(node.safety_goal_description or (node.user_name or f"SG {node.unique_id}"))
        for p in getattr(node, "parents", []):
            self._collect_goal_names(p, acc)

    def get_requirement_goal_names(self, req_id: str) -> list[str]:
        """Return a list of safety goal names linked to ``req_id``."""
        goals: Set[str] = set()
        for n in self.app.get_all_nodes(self.app.root_node):
            reqs = getattr(n, "safety_requirements", [])
            if any((r.get("id") if isinstance(r, dict) else getattr(r, "id", None)) == req_id for r in reqs):
                self._collect_goal_names(n, goals)
        for fmea in self.app.fmeas:
            for e in fmea.get("entries", []):
                reqs = e.get("safety_requirements", []) if isinstance(e, dict) else getattr(e, "safety_requirements", [])
                if any((r.get("id") if isinstance(r, dict) else getattr(r, "id", None)) == req_id for r in reqs):
                    parent_list = e.get("parents") if isinstance(e, dict) else getattr(e, "parents", None)
                    parent = parent_list[0] if parent_list else None
                    if isinstance(parent, dict) and "unique_id" in parent:
                        node = self.app.find_node_by_id_all(parent["unique_id"])
                    else:
                        node = parent if hasattr(parent, "unique_id") else None
                    if node:
                        self._collect_goal_names(node, goals)
        return sorted(goals)

    # ------------------------------------------------------------------
    def compute_requirement_asil(self, req_id: str) -> str:
        """Return highest ASIL across all safety goals linked to the requirement."""

        asil = "QM"
        for g in self.get_requirement_goal_names(req_id):
            a = self.app.get_safety_goal_asil(g)
            if ASIL_ORDER.get(a, 0) > ASIL_ORDER.get(asil, 0):
                asil = a
        return asil

    # ------------------------------------------------------------------
    def update_requirement_statuses(self) -> None:
        """Synchronize each requirement's status based on associated reviews."""

        status_order = [
            "draft",
            "in review",
            "peer reviewed",
            "pending approval",
            "approved",
        ]
        rank = {s: i for i, s in enumerate(status_order)}

        for rid, req in global_requirements.items():
            if req.get("status") == "obsolete":
                continue

            current = req.get("status", "draft")
            current_rank = rank.get(current, 0)

            for review in getattr(self.app, "reviews", []):
                req_ids = self.app.review_manager.get_requirements_for_review(review)
                if rid not in req_ids:
                    continue
                if review.mode == "joint":
                    candidate = (
                        "approved"
                        if review.approved and self.app.review_is_closed_for(review)
                        else "pending approval"
                    )
                else:
                    candidate = "peer reviewed" if getattr(review, "reviewed", False) else "in review"

                cand_rank = rank.get(candidate, 0)
                if cand_rank > current_rank:
                    current = candidate
                    current_rank = cand_rank

            req["status"] = current

    # ------------------------------------------------------------------
    def format_requirement(self, req: Dict[str, Any], include_id: bool = True) -> str:
        """Return a formatted requirement string without empty ASIL/CAL fields."""
        parts: list[str] = []
        if include_id and req.get("id"):
            parts.append(f"[{req['id']}]")
        if req.get("req_type"):
            parts.append(f"[{req['req_type']}]")
        asil = req.get("asil")
        if asil:
            parts.append(f"[{asil}]")
        cal = req.get("cal")
        if cal:
            parts.append(f"[{cal}]")
        parts.append(req.get("text", ""))
        return " ".join(parts)

    # ------------------------------------------------------------------
    def format_requirement_with_trace(self, req: Dict[str, Any]) -> str:
        rid = req.get("id", "")
        alloc = ", ".join(self.get_requirement_allocation_names(rid))
        goals = ", ".join(self.get_requirement_goal_names(rid))
        base = self.format_requirement(req)
        return f"{base} (Alloc: {alloc}; SGs: {goals})"

    # ------------------------------------------------------------------
    def show_safety_goals_matrix(self) -> None:
        """Display product goals and derived requirements in a tree view."""
        app = self.app
        if hasattr(app, "_sg_matrix_tab") and app._sg_matrix_tab.winfo_exists():
            app.doc_nb.select(app._sg_matrix_tab)
            return
        app._sg_matrix_tab = app.lifecycle_ui._new_tab("Product Goals Matrix")
        win = app._sg_matrix_tab
        columns = [
            "ID",
            "ASIL",
            "Target PMHF",
            "CAL",
            "SafeState",
            "FTTI",
            "Acc Rate",
            "On Hours",
            "Val Target",
            "Profile",
            "Val Desc",
            "Acceptance",
            "Description",
            "Text",
        ]
        tree = ttk.Treeview(win, columns=columns, show="tree headings")
        tree.heading("ID", text="Requirement ID")
        tree.heading("ASIL", text="ASIL")
        tree.heading("Target PMHF", text="Target PMHF (1/h)")
        tree.heading("CAL", text="CAL")
        tree.heading("SafeState", text="Safe State")
        tree.heading("FTTI", text="FTTI")
        tree.heading("Acc Rate", text="Acc Rate (1/h)")
        tree.heading("On Hours", text="On Hours")
        tree.heading("Val Target", text="Val Target")
        tree.heading("Profile", text="Profile")
        tree.heading("Val Desc", text="Val Desc")
        tree.heading("Acceptance", text="Acceptance")
        tree.heading("Description", text="Description")
        tree.heading("Text", text="Text")
        tree.column("ID", width=120)
        tree.column("ASIL", width=60)
        tree.column("Target PMHF", width=120)
        tree.column("CAL", width=60)
        tree.column("SafeState", width=100)
        tree.column("FTTI", width=80)
        tree.column("Acc Rate", width=100)
        tree.column("On Hours", width=100)
        tree.column("Val Target", width=120)
        tree.column("Profile", width=120)
        tree.column("Val Desc", width=200)
        tree.column("Acceptance", width=200)
        tree.column("Description", width=200)
        tree.column("Text", width=300)
        vsb = ttk.Scrollbar(win, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(win, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        win.columnconfigure(0, weight=1)
        win.rowconfigure(0, weight=1)
        for te in app.top_events:
            sg_text = te.safety_goal_description or (te.user_name or f"SG {te.unique_id}")
            sg_id = te.user_name or f"SG {te.unique_id}"
            cal = app.get_cyber_goal_cal(sg_id)
            asil = te.safety_goal_asil or "QM"
            target = PMHF_TARGETS.get(asil, 1.0)
            parent_iid = tree.insert(
                "",
                "end",
                text=sg_text,
                values=[
                    sg_id,
                    te.safety_goal_asil,
                    f"{target:.1e}",
                    cal,
                    te.safe_state,
                    getattr(te, "ftti", ""),
                    str(getattr(te, "acceptance_rate", "")),
                    getattr(te, "operational_hours_on", ""),
                    getattr(te, "validation_target", ""),
                    getattr(te, "mission_profile", ""),
                    getattr(te, "validation_desc", ""),
                    getattr(te, "acceptance_criteria", ""),
                    sg_text,
                    "",
                ],
            )
            reqs = app.collect_requirements_recursive(te)
            seen_ids = set()
            for req in reqs:
                req_id = req.get("id")
                if req_id in seen_ids:
                    continue
                seen_ids.add(req_id)
                tree.insert(
                    parent_iid,
                    "end",
                    text="",
                    values=[
                        req_id,
                        req.get("asil", ""),
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        req.get("text", ""),
                    ],
                )

    # ------------------------------------------------------------------
    def show_product_goals_editor(self) -> None:
        """Allow editing of top-level product goals."""
        app = self.app
        if hasattr(app, "_sg_tab") and app._sg_tab.winfo_exists():
            app.doc_nb.select(app._sg_tab)
            return
        app._sg_tab = app.lifecycle_ui._new_tab("Product Goals")
        win = app._sg_tab

        columns = [
            "ID",
            "ASIL",
            "Target PMHF",
            "Safe State",
            "FTTI",
            "Acc Rate",
            "On Hours",
            "Val Target",
            "Profile",
            "Val Desc",
            "Acceptance",
            "Description",
        ]
        tree = ttk.Treeview(win, columns=columns, show="headings", selectmode="browse")
        for c in columns:
            heading = "Target PMHF (1/h)" if c == "Target PMHF" else c
            tree.heading(c, text=heading)
            tree.column(
                c,
                width=120 if c not in ("Description", "Val Desc", "Acceptance") else 300,
                anchor="center",
            )
        tree.pack(fill=tk.BOTH, expand=True)

        def refresh_tree() -> None:
            tree.delete(*tree.get_children())
            for sg in app.top_events:
                name = sg.safety_goal_description or (sg.user_name or f"SG {sg.unique_id}")
                sg.safety_goal_asil = app.get_hara_goal_asil(name)
                pmhf_target = PMHF_TARGETS.get(sg.safety_goal_asil, 1.0)
                tree.insert(
                    "",
                    "end",
                    iid=sg.unique_id,
                    values=[
                        sg.user_name or f"SG {sg.unique_id}",
                        sg.safety_goal_asil,
                        f"{pmhf_target:.2e}",
                        sg.safe_state,
                        getattr(sg, "ftti", ""),
                        str(getattr(sg, "acceptance_rate", "")),
                        getattr(sg, "operational_hours_on", ""),
                        getattr(sg, "validation_target", ""),
                        getattr(sg, "mission_profile", ""),
                        getattr(sg, "validation_desc", ""),
                        getattr(sg, "acceptance_criteria", ""),
                        sg.safety_goal_description,
                    ],
                )

        class SGDialog(simpledialog.Dialog):
            def __init__(self, parent, app, title, initial=None):
                self.app = app
                self.initial = initial
                super().__init__(parent, title=title)

            def body(self, master):
                nb = ttk.Notebook(master)
                nb.pack(fill=tk.BOTH, expand=True)

                fs_tab = ttk.Frame(nb)
                sotif_tab = ttk.Frame(nb)
                cyber_tab = ttk.Frame(nb)
                nb.add(fs_tab, text="Functional Safety")
                nb.add(sotif_tab, text="SOTIF")
                nb.add(cyber_tab, text="Cybersecurity")

                name = getattr(self.initial, "safety_goal_description", "") or getattr(
                    self.initial, "user_name", ""
                )

                # --- Functional Safety fields ---
                ttk.Label(fs_tab, text="ID:").grid(row=0, column=0, sticky="e")
                self.id_var = tk.StringVar(value=getattr(self.initial, "user_name", ""))
                self.id_entry = tk.Entry(fs_tab, textvariable=self.id_var)
                self.id_entry.grid(row=0, column=1, padx=5, pady=5)

                ttk.Label(fs_tab, text="ASIL:").grid(row=1, column=0, sticky="e")
                self.asil_var = tk.StringVar(value=self.app.get_hara_goal_asil(name))
                ttk.Label(fs_tab, textvariable=self.asil_var).grid(
                    row=1, column=1, padx=5, pady=5, sticky="w"
                )

                ttk.Label(fs_tab, text="Target PMHF (1/h):").grid(row=2, column=0, sticky="e")
                pmhf = PMHF_TARGETS.get(self.asil_var.get(), 1.0)
                self.pmhf_var = tk.StringVar(value=f"{pmhf:.2e}")
                tk.Entry(fs_tab, textvariable=self.pmhf_var, state="readonly").grid(
                    row=2, column=1, padx=5, pady=5, sticky="w"
                )

                ttk.Label(fs_tab, text="Safe State:").grid(row=3, column=0, sticky="e")
                self.state_var = tk.StringVar(value=getattr(self.initial, "safe_state", ""))
                tk.Entry(fs_tab, textvariable=self.state_var).grid(
                    row=3, column=1, padx=5, pady=5
                )

                ttk.Label(fs_tab, text="FTTI:").grid(row=4, column=0, sticky="e")
                self.ftti_var = tk.StringVar(value=getattr(self.initial, "ftti", ""))
                tk.Entry(
                    fs_tab,
                    textvariable=self.ftti_var,
                    validate="key",
                    validatecommand=(
                        master.register(self.app.validation_consistency.validate_float),
                        "%P",
                    ),
                ).grid(row=4, column=1, padx=5, pady=5)

                ttk.Label(fs_tab, text="Description:").grid(row=5, column=0, sticky="ne")
                self.desc_text = tk.Text(fs_tab, width=30, height=3, wrap="word")
                self.desc_text.insert(
                    "1.0", getattr(self.initial, "safety_goal_description", "")
                )
                self.desc_text.grid(row=5, column=1, padx=5, pady=5)

                # --- SOTIF fields ---
                self.app.sotif_manager.build_goal_dialog(self, sotif_tab, self.initial)

                # --- Cybersecurity fields ---
                self.cal_var = self.app.cyber_manager.add_goal_dialog_fields(
                    cyber_tab, name
                )
                return self.id_entry

            def apply(self):
                desc = self.desc_text.get("1.0", "end-1c").strip()
                sg_name = desc or self.id_var.get().strip()
                asil = self.app.get_hara_goal_asil(sg_name)
                self.result = {
                    "id": self.id_var.get().strip(),
                    "asil": asil,
                    "state": self.state_var.get().strip(),
                    "ftti": self.ftti_var.get().strip(),
                    "desc": desc,
                }
                self.result.update(self.app.sotif_manager.collect_goal_data(self))

        def add_sg() -> None:
            dlg = SGDialog(win, app, "Add Product Goal")
            if dlg.result:
                node = FaultTreeNode(dlg.result["id"], "TOP EVENT")
                node.safety_goal_asil = dlg.result["asil"]
                node.safe_state = dlg.result["state"]
                node.ftti = dlg.result["ftti"]
                node.acceptance_rate = float(dlg.result.get("accept_rate", 0.0) or 0.0)
                node.operational_hours_on = float(dlg.result.get("op_hours", 0.0) or 0.0)
                node.update_validation_target()
                node.mission_profile = dlg.result.get("profile", "")
                node.validation_desc = dlg.result["val_desc"]
                node.acceptance_criteria = dlg.result["accept"]
                node.safety_goal_description = dlg.result["desc"]
                app.top_events.append(node)
                refresh_tree()
                app.update_views()

        def edit_sg() -> None:
            sel = tree.selection()
            if not sel:
                return
            uid = int(sel[0])
            sg = app.find_node_by_id_all(uid)
            dlg = SGDialog(win, app, "Edit Product Goal", sg)
            if dlg.result:
                sg.user_name = dlg.result["id"]
                sg.safety_goal_asil = dlg.result["asil"]
                sg.safe_state = dlg.result["state"]
                sg.ftti = dlg.result["ftti"]
                sg.acceptance_rate = float(dlg.result.get("accept_rate", 0.0) or 0.0)
                sg.operational_hours_on = float(dlg.result.get("op_hours", 0.0) or 0.0)
                sg.update_validation_target()
                sg.mission_profile = dlg.result.get("profile", "")
                sg.validation_desc = dlg.result["val_desc"]
                sg.acceptance_criteria = dlg.result["accept"]
                sg.safety_goal_description = dlg.result["desc"]
                refresh_tree()
                app.update_views()

        def del_sg() -> None:
            sel = tree.selection()
            if not sel:
                return
            uid = int(sel[0])
            sg = app.find_node_by_id_all(uid)
            if sg and messagebox.askyesno("Delete", "Delete product goal?"):
                app.top_events = [t for t in app.top_events if t.unique_id != uid]
                refresh_tree()
                app.update_views()

        tree.bind("<Double-1>", lambda e: edit_sg())

        btn = ttk.Frame(win)
        btn.pack(fill=tk.X)
        ttk.Button(btn, text="Add", command=add_sg).pack(side=tk.LEFT)
        ttk.Button(btn, text="Edit", command=edit_sg).pack(side=tk.LEFT)
        ttk.Button(btn, text="Delete", command=del_sg).pack(side=tk.LEFT)

        refresh_tree()

    # ------------------------------------------------------------------
    def show_traceability_matrix(self) -> None:
        """Display a traceability matrix linking FTA basic events to FMEA components."""
        app = self.app
        basic_events = [
            n
            for n in app.get_all_nodes(app.root_node)
            if n.node_type.upper() == "BASIC EVENT"
        ]
        win = tk.Toplevel(app.root)
        win.title("FTA-FMEA Traceability")
        columns = ["Basic Event", "Component"]
        tree = ttk.Treeview(win, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=200, anchor="center")
        tree.pack(fill=tk.BOTH, expand=True)

        for be in basic_events:
            comp = app.get_component_name_for_node(be) or "N/A"
            tree.insert(
                "",
                "end",
                values=[be.user_name or f"BE {be.unique_id}", comp],
            )

    # ------------------------------------------------------------------
    def refresh_phase_requirements_menu(self) -> None:
        """Populate the phase requirements menu from safety management toolbox."""
        app = self.app
        if not hasattr(app, "phase_req_menu"):
            return
        app.phase_req_menu.delete(0, tk.END)
        toolbox = getattr(app, "safety_mgmt_toolbox", None)
        if not toolbox:
            return
        phases = sorted(toolbox.list_modules())
        for phase in phases:
            app.phase_req_menu.add_command(
                label=phase,
                command=partial(app.generate_phase_requirements, phase),
            )
        if phases:
            app.phase_req_menu.add_separator()
        app.phase_req_menu.add_command(
            label="Lifecycle",
            command=app.generate_lifecycle_requirements,
        )

    # ------------------------------------------------------------------
    def collect_reqs(self, node_dict: Dict[str, Any], target: Dict[str, Any]) -> None:
        for r in node_dict.get("safety_requirements", []):
            rid = r.get("id")
            if rid and rid not in target:
                target[rid] = r
        for ch in node_dict.get("children", []):
            self.collect_reqs(ch, target)

    # ------------------------------------------------------------------
    def build_requirement_diff_html(self, review: Any) -> str:
        if not self.app.versions:
            return ""
        base_data = self.app.versions[-1]["data"]
        current = self.app.export_model_data(include_versions=False)

        def filter_data(data: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "top_events": [t for t in data.get("top_events", []) if t["unique_id"] in review.fta_ids],
                "fmeas": [f for f in data.get("fmeas", []) if f["name"] in review.fmea_names],
                "fmedas": [d for d in data.get("fmedas", []) if d.get("name") in getattr(review, "fmeda_names", [])],
            }

        data1 = filter_data(base_data)
        data2 = filter_data(current)
        map1 = self.app.node_map_from_data(data1["top_events"])
        map2 = self.app.node_map_from_data(data2["top_events"])

        reqs1: Dict[str, Any] = {}
        reqs2: Dict[str, Any] = {}
        for nid in review.fta_ids:
            if nid in map1:
                self.collect_reqs(map1[nid], reqs1)
            if nid in map2:
                self.collect_reqs(map2[nid], reqs2)

        fmea1 = {f["name"]: f for f in data1.get("fmeas", [])}
        fmea2 = {f["name"]: f for f in data2.get("fmeas", [])}
        for name in review.fmea_names:
            for e in fmea1.get(name, {}).get("entries", []):
                for r in e.get("safety_requirements", []):
                    rid = r.get("id")
                    if rid and rid not in reqs1:
                        reqs1[rid] = r
            for e in fmea2.get(name, {}).get("entries", []):
                for r in e.get("safety_requirements", []):
                    rid = r.get("id")
                    if rid and rid not in reqs2:
                        reqs2[rid] = r
        for f in data1.get("fmedas", []):
            for e in f.get("entries", []):
                for r in e.get("safety_requirements", []):
                    rid = r.get("id")
                    if rid and rid not in reqs1:
                        reqs1[rid] = r
        for f in data2.get("fmedas", []):
            for e in f.get("entries", []):
                for r in e.get("safety_requirements", []):
                    rid = r.get("id")
                    if rid and rid not in reqs2:
                        reqs2[rid] = r

        import difflib, html

        def html_diff(a: str, b: str) -> str:
            matcher = difflib.SequenceMatcher(None, a, b)
            parts: list[str] = []
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag == "equal":
                    parts.append(html.escape(a[i1:i2]))
                elif tag == "delete":
                    parts.append(f"<span style='color:red'>{html.escape(a[i1:i2])}</span>")
                elif tag == "insert":
                    parts.append(f"<span style='color:blue'>{html.escape(b[j1:j2])}</span>")
                elif tag == "replace":
                    parts.append(f"<span style='color:red'>{html.escape(a[i1:i2])}</span>")
                    parts.append(f"<span style='color:blue'>{html.escape(b[j1:j2])}</span>")
            return "".join(parts)

        lines: list[str] = []
        all_ids = sorted(set(reqs1) | set(reqs2))
        for rid in all_ids:
            r1 = reqs1.get(rid)
            r2 = reqs2.get(rid)
            if r1 and not r2:
                lines.append(f"Removed: {html.escape(self.format_requirement_with_trace(r1))}")
            elif r2 and not r1:
                lines.append(f"Added: {html.escape(self.format_requirement_with_trace(r2))}")
            elif json.dumps(r1, sort_keys=True) != json.dumps(r2, sort_keys=True):
                lines.append("Updated: " + html_diff(self.format_requirement_with_trace(r1), self.format_requirement_with_trace(r2)))

        for nid in review.fta_ids:
            n1 = map1.get(nid, {})
            n2 = map2.get(nid, {})
            sg_old = f"{n1.get('safety_goal_description','')} [{n1.get('safety_goal_asil','')}]"
            sg_new = f"{n2.get('safety_goal_description','')} [{n2.get('safety_goal_asil','')}]"
            label = n2.get('user_name') or n1.get('user_name') or f"Node {nid}"
            if sg_old != sg_new:
                lines.append(f"Safety Goal for {html.escape(label)}: " + html_diff(sg_old, sg_new))
            if n1.get('safe_state','') != n2.get('safe_state',''):
                lines.append(f"Safe State for {html.escape(label)}: " + html_diff(n1.get('safe_state',''), n2.get('safe_state','')))
        return "<br>".join(lines)

    # ------------------------------------------------------------------
    # Requirement editor helpers
    # ------------------------------------------------------------------
    def add_requirement(self, tree: ttk.Treeview, refresh_cb) -> None:
        dlg = ReqDialog(self.app.root, title="Add Requirement")
        if getattr(dlg, "result", None):
            req = ensure_requirement_defaults(dlg.result)
            global_requirements[req["id"]] = req
            refresh_cb()

    def edit_requirement(self, tree: ttk.Treeview, refresh_cb) -> None:
        sel = tree.selection()
        if not sel:
            return
        rid = tree.item(sel[0], "values")[0]
        req = global_requirements.get(rid, {"id": rid})
        dlg = ReqDialog(self.app.root, requirement=req, title="Edit Requirement")
        if getattr(dlg, "result", None):
            new_req = ensure_requirement_defaults(dlg.result)
            if new_req["id"] != rid:
                global_requirements.pop(rid, None)
            global_requirements[new_req["id"]] = new_req
            refresh_cb()

    def delete_requirement(self, tree: ttk.Treeview, refresh_cb) -> None:
        for item in tree.selection():
            rid = tree.item(item, "values")[0]
            global_requirements.pop(rid, None)
            tree.delete(item)
        refresh_cb()

    def link_requirement(self, tree: ttk.Treeview, refresh_cb) -> None:
        sel = tree.selection()
        if not sel:
            return
        rid = tree.item(sel[0], "values")[0]
        req = global_requirements.get(rid)
        if not req:
            return
        dlg = _RequirementRelationDialog(
            self.app.root, req, getattr(self.app, "safety_mgmt_toolbox", None)
        )
        if getattr(dlg, "result", None):
            rel, targets = dlg.result
            for tgt in targets:
                link_requirements(rid, rel, tgt)
            refresh_cb()

    def unlink_requirement(self, tree: ttk.Treeview, refresh_cb) -> None:
        sel = tree.selection()
        if not sel:
            return
        rid = tree.item(sel[0], "values")[0]
        req = global_requirements.get(rid)
        if not req:
            return
        dlg = _RequirementRelationDialog(
            self.app.root, req, getattr(self.app, "safety_mgmt_toolbox", None)
        )
        if getattr(dlg, "result", None):
            rel, targets = dlg.result
            existing = [
                r.get("id") for r in req.get("relations", []) if r.get("type") == rel
            ]
            for tgt in existing:
                if tgt not in targets:
                    unlink_requirements(rid, rel, tgt)
            refresh_cb()

    def export_requirements_to_csv(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV Files", "*.csv")]
        )
        if not path:
            return
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "ID",
                    "ASIL",
                    "CAL",
                    "Type",
                    "Status",
                    "Parent",
                    "Trace",
                    "Links",
                    "Text",
                ]
            )
            for req in global_requirements.values():
                rid = req.get("id", "")
                trace = ", ".join(self.get_requirement_allocation_names(rid))
                links = ", ".join(
                    f"{r.get('type')} {r.get('id')}" for r in req.get("relations", [])
                )
                writer.writerow(
                    [
                        rid,
                        req.get("asil", ""),
                        req.get("cal", ""),
                        req.get("req_type", ""),
                        req.get("status", "draft"),
                        req.get("parent_id", ""),
                        trace,
                        links,
                        req.get("text", ""),
                    ]
                )
        messagebox.showinfo("Export", "Requirements exported")
