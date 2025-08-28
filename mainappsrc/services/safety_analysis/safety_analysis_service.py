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
"""Service facade for safety analysis helpers."""

from __future__ import annotations

from typing import Iterable
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

import csv
from analysis.fmeda_utils import (
    GATE_NODE_TYPES,
)
from analysis import utils as analysis_utils
from analysis.models import (
    COMPONENT_ATTR_TEMPLATES,
    QUALIFICATIONS,
    component_fit_map,
)
from analysis.user_config import CURRENT_USER_NAME
from gui.controls.mac_button_style import apply_translucid_button_style
from gui.styles.style_manager import StyleManager
from gui.windows.fault_prioritization import SelectFaultDialog
import gui.utils.config_utils as config_utils
from mainappsrc.managers.fmeda_manager import FMEDAManager
from mainappsrc.models.fta.fault_tree_node import FaultTreeNode
from mainappsrc.subapps.fta_subapp import FTASubApp


class FMEAService:
    """Service class responsible for FMEA list management."""

    def __init__(self, app: tk.Misc) -> None:
        self.app = app
        self.fmeas: list[dict] = []
        self._fmea_tab: tk.Widget | None = None

    # ------------------------------------------------------------------
    def load_fmeas(self, data: dict) -> None:
        """Load FMEA documents from project data."""
        self.fmeas.clear()
        for fmea_data in data.get("fmeas", []):
            entries = [
                FaultTreeNode.from_dict(e)
                for e in fmea_data.get("entries", [])
            ]
            self.fmeas.append(
                {
                    "name": fmea_data.get("name", "FMEA"),
                    "file": fmea_data.get("file", f"fmea_{len(self.fmeas)}.csv"),
                    "entries": entries,
                    "created": fmea_data.get(
                        "created", datetime.datetime.now().isoformat()
                    ),
                    "author": fmea_data.get("author", CURRENT_USER_NAME),
                    "modified": fmea_data.get(
                        "modified", datetime.datetime.now().isoformat()
                    ),
                    "modified_by": fmea_data.get(
                        "modified_by", CURRENT_USER_NAME
                    ),
                }
            )
        if not self.fmeas and "fmea_entries" in data:
            entries = [
                FaultTreeNode.from_dict(e) for e in data.get("fmea_entries", [])
            ]
            self.fmeas.append(
                {"name": "Default FMEA", "file": "fmea_default.csv", "entries": entries}
            )

    # ------------------------------------------------------------------
    def show_fmea_list(self) -> None:
        """Display the list of FMEA documents."""
        app = self.app
        if self._fmea_tab is not None and self._fmea_tab.winfo_exists():
            app.doc_nb.select(self._fmea_tab)
            return
        self._fmea_tab = app._new_tab("FMEA List")
        win = self._fmea_tab
        columns = ("Name", "Created", "Author", "Modified", "ModifiedBy")
        tree = ttk.Treeview(win, columns=columns, show="headings")
        for c in columns:
            tree.heading(c, text=c)
            width = 150 if c == "Name" else 120
            tree.column(c, width=width)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        item_map: dict[str, dict] = {}
        toolbox = getattr(app, "safety_mgmt_toolbox", None)
        for fmea in self.fmeas:
            name = fmea.get("name", "")
            if toolbox and not toolbox.document_visible("FMEA", name):
                continue
            iid = tree.insert(
                "",
                "end",
                values=(
                    name,
                    fmea.get("created", ""),
                    fmea.get("author", ""),
                    fmea.get("modified", ""),
                    fmea.get("modified_by", ""),
                ),
            )
            item_map[iid] = fmea

        def open_selected(event=None):
            iid = tree.focus()
            doc = item_map.get(iid)
            if not doc:
                return
            win.destroy()
            self._fmea_tab = None
            app.show_fmea_table(doc)

        def add_fmea():
            name = simpledialog.askstring("New FMEA", "Enter FMEA name:")
            if name:
                file_name = f"fmea_{name}.csv"
                now = datetime.datetime.now().isoformat()
                doc = {
                    "name": name,
                    "entries": [],
                    "file": file_name,
                    "created": now,
                    "author": CURRENT_USER_NAME,
                    "modified": now,
                    "modified_by": CURRENT_USER_NAME,
                }
                self.fmeas.append(doc)
                if hasattr(app, "safety_mgmt_toolbox"):
                    app.safety_mgmt_toolbox.register_created_work_product(
                        "FMEA", doc["name"]
                    )
                iid = tree.insert(
                    "",
                    "end",
                    values=(name, now, CURRENT_USER_NAME, now, CURRENT_USER_NAME),
                )
                item_map[iid] = doc
                app.update_views()

        def delete_fmea():
            iid = tree.focus()
            doc = item_map.get(iid)
            if not doc:
                return
            if toolbox and toolbox.document_read_only("FMEA", doc["name"]):
                messagebox.showinfo(
                    "Read-only", "Re-used FMEAs cannot be deleted"
                )
                return
            self.fmeas.remove(doc)
            if toolbox:
                toolbox.register_deleted_work_product("FMEA", doc["name"])
            tree.delete(iid)
            item_map.pop(iid, None)
            app.update_views()

        def rename_fmea():
            iid = tree.focus()
            doc = item_map.get(iid)
            if not doc:
                return
            if toolbox and toolbox.document_read_only("FMEA", doc["name"]):
                messagebox.showinfo(
                    "Read-only", "Re-used FMEAs cannot be renamed"
                )
                return
            current = doc.get("name", "")
            name = simpledialog.askstring(
                "Rename FMEA", "Enter new name:", initialvalue=current
            )
            if not name:
                return
            old = doc["name"]
            doc["name"] = name
            if toolbox:
                toolbox.rename_document("FMEA", old, name)
            app.touch_doc(doc)
            tree.item(
                iid,
                values=(
                    name,
                    doc["created"],
                    doc["author"],
                    doc["modified"],
                    doc["modified_by"],
                ),
            )
            app.update_views()

        tree.bind("<Double-1>", open_selected)
        btn_frame = ttk.Frame(win)
        btn_frame.pack(side=tk.RIGHT, fill=tk.Y)
        ttk.Button(btn_frame, text="Open", command=open_selected).pack(fill=tk.X)
        ttk.Button(btn_frame, text="Add", command=add_fmea).pack(fill=tk.X)
        ttk.Button(btn_frame, text="Rename", command=rename_fmea).pack(fill=tk.X)
        ttk.Button(btn_frame, text="Delete", command=delete_fmea).pack(fill=tk.X)

    # ------------------------------------------------------------------
    def get_settings_dict(self) -> dict:
        """Return a serialisable representation of FMEA settings.

        The FMEA subsystem currently does not expose configurable options,
        but project export expects a settings dictionary.  Providing this
        method avoids :class:`AttributeError` during export and offers a
        future extension point for persisting user configuration.
        """

        return {}

class SafetyAnalysis_FTA_FMEA(FTASubApp, FMEAService, FMEDAManager):
    """Facade combining FTA, FMEA and FMEDA behaviours."""

    def __init__(self, app: tk.Misc) -> None:
        # Internal storage for FMEA and FMEDA documents used by property
        # accessors defined later in this class.  Parent initialisers will
        # populate these via the property setters to avoid recursion.
        self._fmeas: list[dict] = []
        self._fmedas: list[dict] = []

        # Initialise parent helper classes that require the application
        # instance and make the application available to other helpers.
        FMEAService.__init__(self, app)
        FMEDAManager.__init__(self, app)
        self.app = app

    # ------------------------------------------------------------------
    # FTA convenience wrappers
    # ------------------------------------------------------------------
    def create_fta_diagram(self) -> None:
        """Initialize a new FTA diagram with a single top level event."""
        self.app._create_fta_tab("FTA")
        self.app.add_top_level_event()
        if getattr(self.app, "fta_root_node", None):
            self.app.window_controllers.open_page_diagram(self.app.fta_root_node)

    @staticmethod
    def auto_generate_fta_diagram(fta_model, output_path):
        return FTASubApp.auto_generate_fta_diagram(fta_model, output_path)

    def enable_fta_actions(self, enabled: bool) -> None:
        """Enable or disable FTA-related menu actions on the main app."""
        if hasattr(self.app, "fta_menu"):
            state = tk.NORMAL if enabled else tk.DISABLED
            for key in (
                "add_gate",
                "add_basic_event",
                "add_gate_from_failure_mode",
                "add_fault_event",
            ):
                self.app.fta_menu.entryconfig(self.app._fta_menu_indices[key], state=state)

    def show_cut_sets(self) -> None:
        """Display minimal cut sets for all top level events."""
        top_events = getattr(self.app, "top_events", [])
        if not top_events:
            return
        win = tk.Toplevel(self.app.root)
        win.title("FTA Cut Sets")
        columns = ("Top Event", "Cut Set #", "Basic Events")
        tree = ttk.Treeview(win, columns=columns, show="headings")
        for c in columns:
            tree.heading(c, text=c)
        tree.pack(fill=tk.BOTH, expand=True)

        for te in top_events:
            nodes_by_id = {}

            def map_nodes(n):
                nodes_by_id[n.unique_id] = n
                for child in n.children:
                    map_nodes(child)

            map_nodes(te)
            cut_sets = self.calculate_cut_sets(self.app, te)
            te_label = te.user_name or f"Top Event {te.unique_id}"
            for idx, cs in enumerate(cut_sets, start=1):
                names = ", ".join(
                    f"{nodes_by_id[uid].user_name or nodes_by_id[uid].node_type} [{uid}]"
                    for uid in sorted(cs)
                )
                tree.insert("", "end", values=(te_label, idx, names))
                te_label = ""

        def export_csv():
            path = filedialog.asksaveasfilename(
                defaultextension=".csv", filetypes=[("CSV", "*.csv")]
            )
            if not path:
                return
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Top Event", "Cut Set #", "Basic Events"])
                for iid in tree.get_children():
                    writer.writerow(tree.item(iid, "values"))

        ttk.Button(win, text="Export CSV", command=export_csv).pack(pady=5)

    # ------------------------------------------------------------------
    # Delegated helpers used by existing code paths
    # ------------------------------------------------------------------
    def update_hara_statuses(self):
        return self.app.risk_app.update_hara_statuses(self.app)

    def update_fta_statuses(self):
        return self.app.risk_app.update_fta_statuses(self.app)

    def update_basic_event_probabilities(self):
        return self.app.probability_reliability.update_basic_event_probabilities()

    def update_base_event_requirement_asil(self):
        return self.app.risk_app.update_base_event_requirement_asil(self.app)

    def update_hazard_severity(self, hazard: str, severity: int | str) -> None:
        return self.app.risk_app.update_hazard_severity(self.app, hazard, severity)

    # ------------------------------------------------------------------
    # List maintenance helpers
    # ------------------------------------------------------------------
    def update_odd_elements(self) -> None:
        self.app.odd_elements = []
        for lib in getattr(self.app, "odd_libraries", []):
            self.app.odd_elements.extend(lib.get("elements", []))

    def update_hazard_list(self) -> None:
        hazards: list[str] = []
        severity_map: dict[str, int] = {}

        for doc in self.app.hara_docs:
            for e in doc.entries:
                h = getattr(e, "hazard", "").strip()
                if not h:
                    continue
                if h not in hazards:
                    hazards.append(h)
                sev = getattr(e, "severity", None)
                if sev is not None:
                    try:
                        severity_map[h] = int(sev)
                    except Exception:
                        severity_map[h] = 1

        for doc in self.app.hazop_docs:
            for e in doc.entries:
                h = getattr(e, "hazard", "").strip()
                if not h:
                    continue
                if h not in hazards:
                    hazards.append(h)
                sev = getattr(e, "severity", None)
                if sev is not None and h not in severity_map:
                    try:
                        severity_map[h] = int(sev)
                    except Exception:
                        severity_map[h] = 1

        for h in hazards:
            if h in severity_map:
                self.app.hazard_severity[h] = severity_map[h]
            elif h not in self.app.hazard_severity:
                self.app.hazard_severity[h] = 1

        self.app.hazards = hazards

    def update_failure_list(self) -> None:
        failures: list[str] = []
        for entry in self.app.data_access_queries.get_all_fmea_entries():
            eff = getattr(entry, "fmea_effect", "").strip()
            if eff and eff not in failures:
                failures.append(eff)
        self.app.failures = failures

    def update_triggering_condition_list(self) -> None:
        names: list[str] = []
        for n in self.app.get_all_triggering_conditions():
            nm = n.user_name or f"TC {n.unique_id}"
            if nm not in names:
                names.append(nm)
        for doc in self.app.fi2tc_docs + self.app.tc2fi_docs:
            for e in doc.entries:
                val = e.get("triggering_conditions", "")
                for part in val.split(";"):
                    p = part.strip()
                    if p and p not in names:
                        names.append(p)
        self.app.triggering_conditions = names

    def update_functional_insufficiency_list(self) -> None:
        names: list[str] = []
        for n in self.app.get_all_functional_insufficiencies():
            nm = n.user_name or f"FI {n.unique_id}"
            if nm not in names:
                names.append(nm)
        for doc in self.app.fi2tc_docs + self.app.tc2fi_docs:
            for e in doc.entries:
                val = e.get("functional_insufficiencies", "")
                for part in val.split(";"):
                    p = part.strip()
                    if p and p not in names:
                        names.append(p)
        self.app.functional_insufficiencies = names

    # ------------------------------------------------------------------
    # Attribute proxies
    # ------------------------------------------------------------------
    @property
    def fmeas(self) -> list[dict]:
        """Expose loaded FMEA documents."""
        return getattr(self, "_fmeas", [])

    @fmeas.setter
    def fmeas(self, value: list[dict]) -> None:
        self._fmeas = value

    @property
    def fmedas(self) -> list[dict]:
        """Expose loaded FMEDA documents."""
        return getattr(self, "_fmedas", [])

    @fmedas.setter
    def fmedas(self, value: list[dict]) -> None:
        self._fmedas = value

    # ------------------------------------------------------------------
    # FTA helpers
    # ------------------------------------------------------------------
    def _load_fault_tree_events(self, data: dict, ensure_root: bool) -> None:
        """Initialise FTA, CTA and PAA events from *data*."""
        app = self.app
        if "top_events" in data:
            app.top_events = [FaultTreeNode.from_dict(e) for e in data["top_events"]]
        elif "root_node" in data:
            root = FaultTreeNode.from_dict(data["root_node"])
            app.top_events = [root]
        else:
            app.top_events = []

        app.cta_events = [FaultTreeNode.from_dict(e) for e in data.get("cta_events", [])]
        app.paa_events = [FaultTreeNode.from_dict(e) for e in data.get("paa_events", [])]

        if (
            ensure_root
            and not app.top_events
            and "top_events" not in data
            and "root_node" not in data
        ):
            new_root = FaultTreeNode("Vehicle Level Function", "TOP EVENT")
            new_root.x, new_root.y = 300, 200
            app.top_events.append(new_root)
        app.root_node = app.top_events[0] if app.top_events else None

    def calculate_cut_sets(self, node):
        return FTASubApp.calculate_cut_sets(self, self.app, node)

    def build_simplified_fta_model(self, top_event):
        return FTASubApp.build_simplified_fta_model(self, self.app, top_event)

    def get_all_basic_events(self, app=None):
        """Return all basic events in the current fault tree model."""
        return FTASubApp.get_all_basic_events(self, app or self.app)

    def all_children_are_base_events(self, node):
        return FTASubApp.all_children_are_base_events(self, self.app, node)

    def add_fault(self, name: str) -> None:
        self.app.risk_app.add_fault(self.app, name)

    def _prompt_fault_selection(self, app):
        dialog = SelectFaultDialog(app.root, sorted(app.faults), allow_new=True)
        fault = dialog.selected
        if fault == "NEW":
            fault = simpledialog.askstring("New Fault", "Name:")
            if not fault:
                return None
            fault = fault.strip()
            if not fault:
                return None
            self.add_fault(fault)
        return fault

    def _determine_parent_node(self, app):
        if app.selected_node:
            parent_node = app.selected_node
            if not parent_node.is_primary_instance:
                messagebox.showwarning(
                    "Invalid Operation", "Cannot add to a clone node. Select the original."
                )
                return None
            return parent_node
        sel = app.analysis_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Select a parent node to paste into.")
            return None
        try:
            node_id = int(app.analysis_tree.item(sel[0], "tags")[0])
        except (IndexError, ValueError):
            messagebox.showwarning("No selection", "Select a parent node from the tree.")
            return None
        return app.find_node_by_id_all(node_id)

    def add_fault_event(self) -> None:
        app = self.app
        app.push_undo_state()
        fault = self._prompt_fault_selection(app)
        if not fault:
            return
        parent_node = self._determine_parent_node(app)
        if not parent_node:
            return
        if parent_node.node_type.upper() in [
            "CONFIDENCE LEVEL",
            "ROBUSTNESS SCORE",
            "BASIC EVENT",
        ]:
            messagebox.showwarning("Invalid", "Base events cannot have children.")
            return
        new_node = FaultTreeNode("", "Basic Event", parent=parent_node)
        new_node.failure_prob = 0.0
        new_node.fault_ref = fault
        new_node.description = fault
        fit_total = 0.0
        for entry in app.get_all_fmea_entries():
            causes = [
                c.strip() for c in getattr(entry, "fmea_cause", "").split(";") if c.strip()
            ]
            if fault in causes:
                fit_total += getattr(entry, "fmeda_fit", 0.0)
                if not getattr(new_node, "prob_formula", None):
                    new_node.prob_formula = getattr(entry, "prob_formula", "linear")
        if fit_total > 0:
            new_node.fmeda_fit = fit_total
            new_node.failure_prob = app.compute_failure_prob(new_node)
        new_node.x = parent_node.x + 100
        new_node.y = parent_node.y + 100
        parent_node.children.append(new_node)
        new_node.parents.append(parent_node)
        app.update_views()

    def add_top_level_event(self) -> None:
        app = self.app
        new_event = FaultTreeNode("", "TOP EVENT")
        new_event.x, new_event.y = 300, 200
        new_event.is_top_event = True
        diag_mode = getattr(app, "diagram_mode", "FTA")
        if diag_mode == "CTA":
            app.cta_events.append(new_event)
            app.cta_root_node = new_event
            wp = "CTA"
        elif diag_mode == "PAA":
            app.paa_events.append(new_event)
            app.paa_root_node = new_event
            wp = "Prototype Assurance Analysis"
        else:
            app.top_events.append(new_event)
            app.fta_root_node = new_event
            wp = "FTA"
        app.root_node = new_event
        if hasattr(app, "safety_mgmt_toolbox"):
            app.safety_mgmt_toolbox.register_created_work_product(
                wp, new_event.user_name
            )
        app._update_shared_product_goals()
        app.update_views()

    def generate_top_event_summary(self, top_event):
        return FTASubApp.generate_top_event_summary(self, self.app, top_event)

    def generate_recommendations_for_top_event(self, node):
        return FTASubApp.generate_recommendations_for_top_event(self, self.app, node)

    def derive_requirements_for_event(self, event):
        return FTASubApp.derive_requirements_for_event(self, self.app, event)

    def get_available_failure_modes_for_gates(self, current_gate=None):
        modes = self.app.get_non_basic_failure_modes()
        used = {
            getattr(g, "failure_mode_ref", None)
            for g in self.app.get_all_gates()
            if g is not current_gate and getattr(g, "failure_mode_ref", None)
        }
        return [m for m in modes if getattr(m, "unique_id", None) not in used]

    def get_faults_for_failure_mode(self, failure_mode_node) -> list[str]:
        fm_node = self.app.get_failure_mode_node(failure_mode_node)
        fm_id = fm_node.unique_id
        faults: list[str] = []
        for be in self.get_all_basic_events():
            if getattr(be, "failure_mode_ref", None) == fm_id:
                fault = getattr(be, "fault_ref", "") or getattr(be, "description", "")
                if fault:
                    faults.append(fault)
        return sorted(set(faults))

    def get_fit_for_fault(self, fault_name: str) -> float:
        comp_fit = component_fit_map(self.app.reliability_components)
        total = 0.0
        for fm in self.app.get_all_fmea_entries():
            causes = [
                c.strip() for c in getattr(fm, "fmea_cause", "").split(";") if c.strip()
            ]
            if fault_name in causes:
                comp_name = self.app.get_component_name_for_node(fm)
                base = comp_fit.get(comp_name)
                frac = getattr(fm, "fmeda_fault_fraction", 0.0)
                if frac > 1.0:
                    frac /= 100.0
                value = base * frac if base is not None else getattr(fm, "fmeda_fit", 0.0)
                total += value
        return total

    def get_top_event(self, node):
        return FTASubApp.get_top_event(self, self.app, node)

    def move_top_event_up(self):
        return FTASubApp.move_top_event_up(self, self.app)

    def move_top_event_down(self):
        return FTASubApp.move_top_event_down(self, self.app)

    def delete_top_events_for_malfunction(self, name: str) -> None:
        app = self.app
        app.push_undo_state()
        removed = [te for te in app.top_events if getattr(te, "malfunction", "") == name]
        if not removed:
            return
        for te in removed:
            if hasattr(app, "safety_mgmt_toolbox"):
                analysis = (
                    "Prototype Assurance Analysis"
                    if getattr(app, "diagram_mode", "") == "PAA"
                    else "FTA"
                )
                app.safety_mgmt_toolbox.register_deleted_work_product(
                    analysis, te.name
                )
            app.top_events.remove(te)
            if hasattr(app, "safety_mgmt_toolbox"):
                app.safety_mgmt_toolbox.register_deleted_work_product(
                    analysis, te.user_name
                )
        if app.root_node in removed:
            app.root_node = app.top_events[0] if app.top_events else FaultTreeNode("", "TOP EVENT")
        app.update_views()

    # ------------------------------------------------------------------
    # FMEA / FMEDA helpers
    # ------------------------------------------------------------------
    def export_fmea_to_csv(self, fmea, path):
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
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            for be in fmea["entries"]:
                src = self.app.get_failure_mode_node(be)
                comp = self.app.get_component_name_for_node(src) or "N/A"
                parent = src.parents[0] if src.parents else None
                parent_name = (
                    parent.user_name
                    if parent and getattr(parent, "node_type", "").upper() not in GATE_NODE_TYPES
                    else ""
                )
                req_ids = "; ".join(
                    [
                        f"{req['req_type']}:{req['text']}"
                        for req in getattr(be, "safety_requirements", [])
                    ]
                )
                rpn = be.fmea_severity * be.fmea_occurrence * be.fmea_detection
                failure_mode = be.description or (be.user_name or f"BE {be.unique_id}")
                row = [
                    comp,
                    parent_name,
                    failure_mode,
                    be.fmea_effect,
                    be.fmea_cause,
                    be.fmea_severity,
                    be.fmea_occurrence,
                    be.fmea_detection,
                    rpn,
                    req_ids,
                    getattr(be, "fmeda_malfunction", ""),
                ]
                writer.writerow(row)

    def export_fmeda_to_csv(self, fmeda, path):
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
            "Safety Goal",
            "FaultType",
            "Fraction",
            "FIT",
            "DiagCov",
            "Mechanism",
        ]
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            for be in fmeda["entries"]:
                src = self.app.get_failure_mode_node(be)
                comp = self.app.get_component_name_for_node(src) or "N/A"
                parent = src.parents[0] if src.parents else None
                parent_name = (
                    parent.user_name
                    if parent and getattr(parent, "node_type", "").upper() not in GATE_NODE_TYPES
                    else ""
                )
                req_ids = "; ".join(
                    [
                        f"{req['req_type']}:{req['text']}"
                        for req in getattr(be, "safety_requirements", [])
                    ]
                )
                rpn = be.fmea_severity * be.fmea_occurrence * be.fmea_detection
                failure_mode = be.description or (be.user_name or f"BE {be.unique_id}")
                row = [
                    comp,
                    parent_name,
                    failure_mode,
                    be.fmea_effect,
                    be.fmea_cause,
                    be.fmea_severity,
                    be.fmea_occurrence,
                    be.fmea_detection,
                    rpn,
                    req_ids,
                    getattr(be, "fmeda_malfunction", ""),
                    ", ".join(self.app.get_top_event_safety_goals(be))
                    or getattr(be, "fmeda_safety_goal", ""),
                    getattr(be, "fmeda_fault_type", ""),
                    be.fmeda_fault_fraction,
                    be.fmeda_fit,
                    be.fmeda_diag_cov,
                    getattr(be, "fmeda_mechanism", ""),
                ]
                writer.writerow(row)

    def compute_fmeda_metrics(self, events):
        return self.app.risk_app.compute_fmeda_metrics(self.app, events)

    def calculate_fmeda_metrics(self, events):
        return self.app.risk_app.calculate_fmeda_metrics(self.app, events)

    def show_fmea_list(self):
        return FMEAService.show_fmea_list(self)

    def show_fmea_table(self, fmea=None, fmeda: bool = False):
        return self.app._show_fmea_table_impl(fmea, fmeda)

    def show_fmeda_list(self):
        return FMEDAManager.show_fmeda_list(self)

    # ------------------------------------------------------------------
    # Risk and library helpers
    # ------------------------------------------------------------------
    def get_hazop_by_name(self, name):
        return self.app.risk_app.get_hazop_by_name(self.app, name)

    def get_hara_by_name(self, name):
        return self.app.risk_app.get_hara_by_name(self.app, name)

    def get_safety_goal_asil(self, sg_name):
        return self.app.risk_app.get_safety_goal_asil(self.app, sg_name)

    def get_hara_goal_asil(self, sg_name):
        return self.app.risk_app.get_hara_goal_asil(self.app, sg_name)

    def get_cyber_goal_cal(self, goal_id):
        return self.app.risk_app.get_cyber_goal_cal(self.app, goal_id)

    def get_top_event_safety_goals(self, node):
        return self.app.data_access_queries.get_top_event_safety_goals(node)

    def get_safety_goals_for_malfunctions(self, malfunctions: list[str]) -> list[str]:
        goals: list[str] = []
        for te in self.app.top_events:
            mal = getattr(te, "malfunction", "")
            if mal and mal in malfunctions:
                sg = te.safety_goal_description or te.user_name or ""
                if sg and sg not in goals:
                    goals.append(sg)
        return goals

    def is_malfunction_used(self, name: str) -> bool:
        if not name:
            return False
        for te in self.app.top_events:
            if getattr(te, "malfunction", "") == name:
                return True
        for n in self.app.structure_tree_operations.get_all_nodes_in_model():
            mals = [
                m.strip()
                for m in getattr(n, "fmeda_malfunction", "").split(";")
                if m.strip()
            ]
            if name in mals:
                return True
        return False

    def add_malfunction(self, name: str) -> None:
        return self.app.risk_app.add_malfunction(self.app, name)

    def add_failure(self, name: str) -> None:
        return self.app.risk_app.add_failure(self.app, name)

    def add_hazard(self, name: str, severity: int | str = 1) -> None:
        return self.app.risk_app.add_hazard(self.app, name, severity)

    def add_triggering_condition(self, name: str) -> None:
        return self.app.risk_app.add_triggering_condition(self.app, name)

    def delete_triggering_condition(self, name: str) -> None:
        return self.app.risk_app.delete_triggering_condition(self.app, name)

    def add_functional_insufficiency(self, name: str) -> None:
        return self.app.risk_app.add_functional_insufficiency(self.app, name)

    def delete_functional_insufficiency(self, name: str) -> None:
        return self.app.risk_app.delete_functional_insufficiency(self.app, name)

    # ------------------------------------------------------------------
    # Data access wrappers
    # ------------------------------------------------------------------
    def get_all_gates(self, app=None):
        """Return all gate nodes in the current fault tree model."""
        return FTASubApp.get_all_gates(self, app or self.app)

    def get_all_failure_modes(self):
        return self.app.data_access_queries.get_all_failure_modes()

    def get_all_fmea_entries(self):
        return self.app.data_access_queries.get_all_fmea_entries()

    def get_non_basic_failure_modes(self):
        return self.app.data_access_queries.get_non_basic_failure_modes()

    def get_failure_mode_node(self, node):
        return self.app.data_access_queries.get_failure_mode_node(node)

    def get_component_name_for_node(self, node):
        return self.app.data_access_queries.get_component_name_for_node(node)

    def get_failure_modes_for_malfunction(self, malfunction: str) -> list[str]:
        return self.app.data_access_queries.get_failure_modes_for_malfunction(malfunction)

    # ------------------------------------------------------------------
    # Hazard and FTA views
    # ------------------------------------------------------------------
    def show_hazard_list(self):
        return self.app.risk_app.show_hazard_list(self.app)

    def show_hazard_explorer(self):
        return self.app.risk_app.show_hazard_explorer(self.app)

    def show_common_cause_view(self):
        win = tk.Toplevel(self.app.root)
        win.title("Common Cause Toolbox")
        var_fmea = tk.BooleanVar(value=True)
        var_fmeda = tk.BooleanVar(value=True)
        var_fta = tk.BooleanVar(value=True)
        chk_frame = ttk.Frame(win)
        chk_frame.pack(anchor="w")
        ttk.Checkbutton(chk_frame, text="FMEA", variable=var_fmea).pack(side=tk.LEFT)
        ttk.Checkbutton(chk_frame, text="FMEDA", variable=var_fmeda).pack(side=tk.LEFT)
        ttk.Checkbutton(chk_frame, text="FTA", variable=var_fta).pack(side=tk.LEFT)
        tree_frame = ttk.Frame(win)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        tree = ttk.Treeview(tree_frame, columns=["Cause", "Events"], show="headings")
        for c in ["Cause", "Events"]:
            tree.heading(c, text=c)
            tree.column(c, width=150)
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        def refresh():
            tree.delete(*tree.get_children())
            events_by_cause = {}
            if var_fmea.get():
                for fmea in self.fmeas:
                    for be in fmea["entries"]:
                        cause = be.description
                        label = f"{fmea['name']}:{be.user_name or be.description or be.unique_id}"
                        events_by_cause.setdefault(cause, set()).add(label)
            if var_fmeda.get():
                for fmeda in self.fmedas:
                    for be in fmeda["entries"]:
                        cause = be.description
                        label = f"{fmeda['name']}:{be.user_name or be.description or be.unique_id}"
                        events_by_cause.setdefault(cause, set()).add(label)
            if var_fta.get():
                for be in self.get_all_basic_events():
                    cause = be.description or ""
                    label = be.user_name or f"BE {be.unique_id}"
                    events_by_cause.setdefault(cause, set()).add(label)
            for cause, evts in events_by_cause.items():
                if len(evts) > 1:
                    tree.insert("", "end", values=[cause, ", ".join(sorted(evts))])

        refresh()

        def export_csv():
            path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
            if not path:
                return
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Cause", "Events"])
                for iid in tree.get_children():
                    writer.writerow(tree.item(iid, "values"))
            messagebox.showinfo("Export", "Common cause data exported")

        btn_frame = ttk.Frame(win)
        btn_frame.pack()
        ttk.Button(btn_frame, text="Refresh", command=refresh).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(btn_frame, text="Export CSV", command=export_csv).pack(side=tk.LEFT, padx=5, pady=5)

    def show_cause_effect_chain(self):
        data = self.app.build_cause_effect_data()
        if not data:
            messagebox.showinfo("Cause & Effect", "No data available")
            return

        win = tk.Toplevel(self.app.root)
        win.title("Cause & Effect Chain")

        nb = ttk.Notebook(win)
        nb.pack(fill=tk.BOTH, expand=True)

        table_frame = ttk.Frame(nb)
        diagram_frame = ttk.Frame(nb)
        nb.add(table_frame, text="Table")
        nb.add(diagram_frame, text="Diagram")

        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        diagram_frame.columnconfigure(0, weight=1)
        diagram_frame.rowconfigure(0, weight=1)

        cols = (
            "Hazard",
            "Malfunction",
            "Threats",
            "Attack Paths",
            "Failure Modes",
            "Faults",
            "Threat Scenarios",
            "Attack Paths",
            "FIs",
            "TCs",
        )

        tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        canvas = tk.Canvas(diagram_frame, bg=StyleManager.get_instance().canvas_bg)
        cvs_vsb = ttk.Scrollbar(diagram_frame, orient="vertical", command=canvas.yview)
        cvs_hsb = ttk.Scrollbar(diagram_frame, orient="horizontal", command=canvas.xview)
        canvas.configure(yscrollcommand=cvs_vsb.set, xscrollcommand=cvs_hsb.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        cvs_vsb.grid(row=0, column=1, sticky="ns")
        cvs_hsb.grid(row=1, column=0, sticky="ew")

        row_map = {}
        for row in data:
            iid = tree.insert(
                "",
                "end",
                values=(
                    row["hazard"],
                    row["malfunction"],
                    ", ".join(sorted(row["threats"].keys())),
                    ", ".join(sorted(row["attack_paths"])),
                    ", ".join(sorted(row["failure_modes"].keys())),
                    ", ".join(sorted(row["faults"])),
                    ", ".join(sorted(row["threats"].keys())),
                    ", ".join(sorted(row["attack_paths"])),
                    ", ".join(sorted(row["fis"])),
                    ", ".join(sorted(row["tcs"])),
                ),
            )
            row_map[iid] = row

        def draw_row(row):
            import textwrap

            nodes, edges, pos = self.app._build_cause_effect_graph(row)

            color_map = {
                "hazard": "#F08080",
                "malfunction": "#ADD8E6",
                "failure_mode": "#FFA500",
                "fault": "#D3D3D3",
                "fi": "#FFFFE0",
                "tc": "#90EE90",
                "attack_path": "#E0FFFF",
                "threat": "#FFB6C1",
            }

            canvas.delete("all")
            scale = 80
            x_off = 50
            y_off = 50
            box_w = 80
            box_h = 40

            def to_canvas(x: float, y: float) -> tuple[float, float]:
                return x_off + scale * x, y_off + scale * y

            for u, v in edges:
                x1, y1 = to_canvas(*pos[u])
                x2, y2 = to_canvas(*pos[v])
                canvas.create_line(x1, y1, x2, y2, arrow=tk.LAST, tags="edge")
                canvas.create_text(
                    (x1 + x2) / 2,
                    (y1 + y2) / 2,
                    text="caused by",
                    font=("TkDefaultFont", 8),
                    tags="edge",
                )

            for n, (x, y) in pos.items():
                label, kind = nodes.get(n, (n, ""))
                color = color_map.get(kind, "white")
                cx, cy = to_canvas(x, y)
                canvas.create_rectangle(
                    cx - box_w / 2,
                    cy - box_h / 2,
                    cx + box_w / 2,
                    cy + box_h / 2,
                    fill=color,
                    outline=StyleManager.get_instance().outline_color,
                    tags="node",
                )
                label = textwrap.fill(str(label), 20)
                canvas.create_text(
                    cx,
                    cy,
                    text=label,
                    width=box_w - 10,
                    font=("TkDefaultFont", 8),
                    tags="node",
                )

            canvas.config(scrollregion=canvas.bbox("all"))
            canvas.xview_moveto(0)
            canvas.yview_moveto(0)
            canvas.update_idletasks()

        def on_select(event):
            sel = tree.selection()
            if sel:
                row = row_map.get(sel[0])
                if row:
                    draw_row(row)
                    nb.select(diagram_frame)

        tree.bind("<<TreeviewSelect>>", on_select)

        if row_map:
            first_iid = next(iter(row_map))
            tree.selection_set(first_iid)
            draw_row(row_map[first_iid])
            nb.select(diagram_frame)

        def export_csv():
            path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
            if not path:
                return
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(cols)
                for iid in tree.get_children():
                    writer.writerow(tree.item(iid, "values"))
            messagebox.showinfo("Export", "Cause & effect data exported")

        ttk.Button(win, text="Export CSV", command=export_csv).pack(pady=5)

    # ------------------------------------------------------------------
    # Model refresh and requirement utilities
    # ------------------------------------------------------------------
    def refresh_model(self):
        app = self.app
        app.ensure_asil_consistency()
        for fm in app.get_all_failure_modes():
            app.propagate_failure_mode_attributes(fm)

        def iter_analysis_events():
            for be in self.get_all_basic_events():
                yield be
            for e in app.fmea_entries:
                yield e
            for doc in self.fmeas:
                for e in doc.get("entries", []):
                    yield e
            for doc in self.fmedas:
                for e in doc.get("entries", []):
                    yield e

        for entry in iter_analysis_events():
            mals = [m.strip() for m in getattr(entry, "fmeda_malfunction", "").split(";") if m.strip()]
            goals = self.get_safety_goals_for_malfunctions(mals) or self.get_top_event_safety_goals(entry)
            if goals:
                sg = ", ".join(goals)
                entry.fmeda_safety_goal = sg
                first = goals[0]
                te = next((t for t in app.top_events if first in [t.user_name, t.safety_goal_description]), None)
                if te:
                    entry.fmeda_dc_target = getattr(te, "sg_dc_target", 0.0)
                    entry.fmeda_spfm_target = getattr(te, "sg_spfm_target", 0.0)
                    entry.fmeda_lpfm_target = getattr(te, "sg_lpfm_target", 0.0)

        self.update_basic_event_probabilities()
        app.sync_cyber_risk_to_goals()

    def refresh_all(self):
        app = self.app
        app.update_views()
        config_utils.regenerate_requirement_patterns()
        app.gsn_manager.refresh()
        for attr in dir(app):
            if attr.endswith("_window"):
                win = getattr(app, attr)
                if hasattr(win, "winfo_exists") and win.winfo_exists():
                    if hasattr(win, "refresh_docs"):
                        win.refresh_docs()
                    if hasattr(win, "refresh"):
                        win.refresh()

    def collect_requirements_recursive(self, node):
        reqs = list(getattr(node, "safety_requirements", []))
        for child in node.children:
            reqs.extend(self.collect_requirements_recursive(child))
        return reqs

if __package__ and __package__.startswith("AutoML"):
    from AutoML.config.automl_constants import PMHF_TARGETS
else:  # pragma: no cover - script context
    from config.automl_constants import PMHF_TARGETS

class SafetyAnalysisService:
    """Wrap :class:`SafetyAnalysis_FTA_FMEA` and expose utility helpers."""

    def __init__(self, app: object) -> None:
        self.app = app
        self._impl = SafetyAnalysis_FTA_FMEA(app)

    def __getattr__(self, name: str):
        return getattr(self._impl, name)

    # ------------------------------------------------------------------
    # FMEDA metric helpers
    def compute_fmeda_metrics(self, events: Iterable[FaultTreeNode]):
        """Compute FMEDA metrics for ``events``."""

        return analysis_utils.compute_fmeda_metrics(
            events,
            getattr(self.app, "reliability_components", []),
            self.get_safety_goal_asil,
        )

    # ------------------------------------------------------------------
    # Probability and reliability helpers moved from probability_reliability.py

    def update_probability_tables(
        self,
        exposure: dict | None,
        controllability: dict | None,
        severity: dict | None,
    ) -> None:
        """Delegate probability table updates to shared utility."""

        analysis_utils.update_probability_tables(
            exposure, controllability, severity
        )

    # ------------------------------------------------------------------
    def compute_failure_prob(self, node, failure_mode_ref=None, formula=None):
        """Return probability of failure for ``node`` based on FIT rate."""

        return analysis_utils.compute_failure_prob(
            self.app, node, failure_mode_ref, formula
        )

    # ------------------------------------------------------------------
    def update_basic_event_probabilities(self):
        """Update failure probabilities for all basic events."""

        analysis_utils.update_basic_event_probabilities(self.app)

    # ------------------------------------------------------------------
    def calculate_pmfh(self):
        """Calculate probabilistic metric for hardware failures."""

        analysis_utils.calculate_pmfh(self.app)

    # ------------------------------------------------------------------
    def calculate_overall(self):
        """Calculate overall assurance levels for top events."""

        analysis_utils.calculate_overall(self.app)

    # ------------------------------------------------------------------
    def _build_probability_frame(
        self,
        parent,
        title: str,
        levels: range,
        values: dict,
        row: int,
        dialog_font: tkFont.Font,
    ) -> dict:
        """Create a labelled frame of probability entries."""

        return analysis_utils.build_probability_frame(
            self.app, parent, title, levels, values, row, dialog_font
        )

    # ------------------------------------------------------------------
    def assurance_level_text(self, level):
        return analysis_utils.assurance_level_text(self.app, level)

    # ------------------------------------------------------------------
    def metric_to_text(self, metric_type, value):
        return analysis_utils.metric_to_text(self.app, metric_type, value)

    # ------------------------------------------------------------------
    def analyze_common_causes(self, node):
        return analysis_utils.analyze_common_causes(self.app, node)

    # ------------------------------------------------------------------
    def build_cause_effect_data(self):
        """Collect cause and effect chain information."""

        return analysis_utils.build_cause_effect_data(self.app)

    # ------------------------------------------------------------------
    def _build_cause_effect_graph(self, row):
        """Return nodes, edges and positions for a cause-and-effect diagram."""

        return analysis_utils.build_cause_effect_graph(row)

    # ------------------------------------------------------------------
    def render_cause_effect_diagram(self, row):
        """Render *row* as a PIL image matching the on-screen diagram."""

        return analysis_utils.render_cause_effect_diagram(row)

    # ------------------------------------------------------------------
    def sync_cyber_risk_to_goals(self):
        return analysis_utils.sync_cyber_risk_to_goals(self.app)


__all__ = ["SafetyAnalysisService", "FMEAService", "SafetyAnalysis_FTA_FMEA"]
