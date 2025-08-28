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

"""Utility helpers for analysis package."""

import csv
import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import List

from analysis.user_config import CURRENT_USER_NAME
from mainappsrc.models.fta.fault_tree_node import FaultTreeNode
from mainappsrc.subapps.fta_subapp import FTASubApp


# Mapping tables from risk assessment ratings to probabilities.
#
# The chosen values reflect rule‑of‑thumb probabilities commonly used in
# functional‑safety workshops: each step increases the likelihood by roughly an
# order of magnitude. They provide a starting point when field data is not yet
# available and align with interpretations published in industry literature.
# Projects with better data can refine these mappings as needed.
EXPOSURE_PROBABILITIES = {1: 1e-4, 2: 1e-3, 3: 1e-2, 4: 1e-1}
CONTROLLABILITY_PROBABILITIES = {1: 1e-3, 2: 1e-2, 3: 1e-1}
SEVERITY_PROBABILITIES = {1: 1e-3, 2: 1e-2, 3: 1e-1}


def update_probability_tables(
    exposure: dict | None = None,
    controllability: dict | None = None,
    severity: dict | None = None,
) -> None:
    """Replace default probability mappings with values from *exposure*,
    *controllability* and *severity*.

    Each argument should be a mapping from rating level to probability. Missing
    arguments leave the current mapping unchanged. The dictionaries are updated
    in-place so references held elsewhere remain valid.
    """

    if exposure is not None:
        EXPOSURE_PROBABILITIES.clear()
        EXPOSURE_PROBABILITIES.update(
            {int(k): float(v) for k, v in dict(exposure).items()}
        )
    if controllability is not None:
        CONTROLLABILITY_PROBABILITIES.clear()
        CONTROLLABILITY_PROBABILITIES.update(
            {int(k): float(v) for k, v in dict(controllability).items()}
        )
    if severity is not None:
        SEVERITY_PROBABILITIES.clear()
        SEVERITY_PROBABILITIES.update(
            {int(k): float(v) for k, v in dict(severity).items()}
        )


def normalize_probability_mapping(mapping: dict | None) -> dict:
    """Return *mapping* with integer keys and float values.

    Project files store probability tables with string keys.  This helper
    converts such mappings back to the numeric form expected by the rest of the
    application.  ``None`` yields an empty dictionary.
    """

    if not mapping:
        return {}
    return {int(k): float(v) for k, v in dict(mapping).items()}


def exposure_to_probability(level: int) -> float:
    """Return ``P(E|HB)`` for the given exposure rating.

    The mapping follows a common industry heuristic where exposure levels 1–4
    correspond to probabilities ``1e-4``, ``1e-3``, ``1e-2`` and ``1e-1``.
    """
    return EXPOSURE_PROBABILITIES.get(int(level), 1.0)


def controllability_to_probability(level: int) -> float:
    """Return ``P(C|E)`` for the given controllability rating.

    Ratings 1–3 map to probabilities ``1e-3``, ``1e-2`` and ``1e-1``
    respectively.
    """
    return CONTROLLABILITY_PROBABILITIES.get(int(level), 1.0)


def severity_to_probability(level: int) -> float:
    """Return ``P(S|C)`` for the given severity rating.

    Severity levels 1–3 map to ``1e-3``, ``1e-2`` and ``1e-1`` respectively.
    """
    return SEVERITY_PROBABILITIES.get(int(level), 1.0)


def append_unique_insensitive(items: List[str], name: str) -> None:
    """Append ``name`` to ``items`` if not already present (case-insensitive)."""
    if not name:
        return
    name = name.strip()
    if not name:
        return
    lower = name.lower()
    for existing in items:
        if existing.lower() == lower:
            return
    items.append(name)


def derive_validation_target(acceptance_rate: float,
                             exposure_given_hb: float,
                             uncontrollable_given_exposure: float,
                             severity_given_uncontrollable: float) -> float:
    """Derive a validation target from an acceptance criterion.

    This implements the ISO 21448 relationship for the rate of hazardous
    behaviour :math:`R_{HB}`. All rates are expressed in **events per hour**.

    The acceptance criterion :math:`A_H` is decomposed into conditional
    probabilities for exposure (``exposure_given_hb``), lack of
    controllability (``uncontrollable_given_exposure``) and severity
    (``severity_given_uncontrollable``). The resulting validation target is
    calculated using:

    ``R_HB = A_H / (P_E|HB * P_C|E * P_S|C)``

    For example, ``A_H = 1e-8/h`` with ``P_E|HB = 0.05``, ``P_C|E = 0.1``
    and ``P_S|C = 0.01`` yields ``R_HB = 2e-4/h``.

    Parameters
    ----------
    acceptance_rate:
        Acceptance criterion for the harm :math:`A_H` in events per hour.
    exposure_given_hb:
        Conditional probability of being exposed to the scenario given the
        hazardous behaviour, :math:`P_{E|HB}`.
    uncontrollable_given_exposure:
        Probability that the hazardous behaviour is not controllable once
        exposure occurs, :math:`P_{C|E}`.
    severity_given_uncontrollable:
        Probability of the relevant severity assuming the control action
        fails, :math:`P_{S|C}`.

    Returns
    -------
    float
        The acceptable rate of the hazardous behaviour ``R_HB`` (events per
        hour) that can be used as a validation target.

    Raises
    ------
    ValueError
        If any of the probability terms is less than or equal to zero.
    """

    denominator = (
        exposure_given_hb *
        uncontrollable_given_exposure *
        severity_given_uncontrollable
    )

    if denominator <= 0:
        raise ValueError(
            "Probability factors must be positive to derive a validation target"
        )

    return acceptance_rate / denominator


def load_fmeas(service, data: dict) -> None:
    """Load FMEA documents into *service* from project *data*."""

    service.fmeas.clear()
    for fmea_data in data.get("fmeas", []):
        entries = [
            FaultTreeNode.from_dict(e) for e in fmea_data.get("entries", [])
        ]
        service.fmeas.append(
            {
                "name": fmea_data.get("name", "FMEA"),
                "file": fmea_data.get("file", f"fmea_{len(service.fmeas)}.csv"),
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
    if not service.fmeas and "fmea_entries" in data:
        entries = [FaultTreeNode.from_dict(e) for e in data.get("fmea_entries", [])]
        service.fmeas.append(
            {"name": "Default FMEA", "file": "fmea_default.csv", "entries": entries}
        )


def show_fmea_list(service) -> None:
    """Display the list of FMEA documents for *service*."""

    app = service.app
    if service._fmea_tab is not None and service._fmea_tab.winfo_exists():
        app.doc_nb.select(service._fmea_tab)
        return
    service._fmea_tab = app._new_tab("FMEA List")
    win = service._fmea_tab
    columns = ("Name", "Created", "Author", "Modified", "ModifiedBy")
    tree = ttk.Treeview(win, columns=columns, show="headings")
    for c in columns:
        tree.heading(c, text=c)
        width = 150 if c == "Name" else 120
        tree.column(c, width=width)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    item_map: dict[str, dict] = {}
    toolbox = getattr(app, "safety_mgmt_toolbox", None)
    for fmea in service.fmeas:
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
        service._fmea_tab = None
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
            service.fmeas.append(doc)
            if hasattr(app, "safety_mgmt_toolbox"):
                app.safety_mgmt_toolbox.register_created_work_product("FMEA", doc["name"])
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
            messagebox.showinfo("Read-only", "Re-used FMEAs cannot be deleted")
            return
        service.fmeas.remove(doc)
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
            messagebox.showinfo("Read-only", "Re-used FMEAs cannot be renamed")
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


def get_fmea_settings_dict(service) -> dict:
    """Return a serialisable representation of FMEA settings."""

    return {}


def create_fta_diagram(service) -> None:
    """Initialize a new FTA diagram with a single top level event."""

    app = service.app
    app._create_fta_tab("FTA")
    app.add_top_level_event()
    if getattr(app, "fta_root_node", None):
        app.window_controllers.open_page_diagram(app.fta_root_node)


def auto_generate_fta_diagram(fta_model, output_path):
    """Delegate auto-generation of FTA diagrams."""

    return FTASubApp.auto_generate_fta_diagram(fta_model, output_path)


def enable_fta_actions(service, enabled: bool) -> None:
    """Enable or disable FTA-related menu actions on the main app."""

    app = service.app
    if hasattr(app, "fta_menu"):
        state = tk.NORMAL if enabled else tk.DISABLED
        for key in (
            "add_gate",
            "add_basic_event",
            "add_gate_from_failure_mode",
            "add_fault_event",
        ):
            app.fta_menu.entryconfig(app._fta_menu_indices[key], state=state)


def show_cut_sets(service) -> None:
    """Display minimal cut sets for all top level events."""

    app = service.app
    top_events = getattr(app, "top_events", [])
    if not top_events:
        return
    win = tk.Toplevel(app.root)
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
        cut_sets = service.calculate_cut_sets(app, te)
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
