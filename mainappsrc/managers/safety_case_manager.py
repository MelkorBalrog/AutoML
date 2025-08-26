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

"""Management helpers for Safety Case related views."""

import csv
import math
import tkinter as tk
from tkinter import ttk, simpledialog, filedialog

from gui.controls import messagebox
from analysis.constants import CHECK_MARK
if __package__ and __package__.startswith("AutoML"):
    from AutoML.config.automl_constants import PMHF_TARGETS
else:  # pragma: no cover - script context
    from config.automl_constants import PMHF_TARGETS
from gui.explorers.safety_case_explorer import SafetyCaseExplorer
from mainappsrc.managers.sotif_manager import SOTIFManager


class SafetyCaseManager:
    """Encapsulate Safety Case and SPI helpers for :class:`AutoMLApp`."""

    def __init__(self, app: "AutoMLApp") -> None:
        self.app = app

    # ------------------------------------------------------------------
    def parse_spi_target(self, target: str) -> tuple[str, str]:
        """Split ``target`` into product goal name and SPI type."""

        if target.endswith(")") and "(" in target:
            name, typ = target.rsplit(" (", 1)
            return name, typ[:-1]
        return target, ""

    # ------------------------------------------------------------------
    def get_spi_targets(self) -> list[str]:
        """Return sorted list of SPI options formatted as 'Product Goal (Type)'."""

        app = self.app
        targets: set[str] = set()
        for sg in getattr(app, "top_events", []):
            pg_name = app._product_goal_name(sg)
            targets.update(app.sotif_manager.get_spi_targets_for_goal(sg, pg_name))
            asil = getattr(sg, "safety_goal_asil", "")
            if asil in PMHF_TARGETS:
                targets.add(f"{pg_name} (FUSA)")
        return sorted(targets)

    # ------------------------------------------------------------------
    def show_safety_performance_indicators(self) -> None:
        """Display Safety Performance Indicators."""

        app = self.app
        if hasattr(app, "_spi_tab") and app._spi_tab.winfo_exists():
            app.doc_nb.select(app._spi_tab)
            self.refresh_safety_performance_indicators()
            return
        app._spi_tab = app.lifecycle_ui._new_tab("Safety Performance Indicators")
        win = app._spi_tab

        columns = [
            "Product Goal",
            "Validation Target",
            "Achieved Probability",
            "SPI",
            "Target Description",
            "Acceptance Criteria",
        ]
        tree = ttk.Treeview(win, columns=columns, show="headings", selectmode="browse")
        for c in columns:
            tree.heading(c, text=c)
            width = 120
            if c in ("Target Description", "Acceptance Criteria"):
                width = 300
            tree.column(c, width=width, anchor="center")
        tree.pack(fill=tk.BOTH, expand=True)
        app._spi_tree = tree
        app._spi_lookup = {}

        def edit_selected():
            sel = tree.selection()
            if not sel:
                return
            iid = sel[0]
            sg_info = app._spi_lookup.get(iid)
            if not sg_info:
                return
            sg, spi_type = sg_info
            if spi_type != "SOTIF":
                return
            new_val = simpledialog.askfloat(
                "Achieved Probability",
                "Enter achieved probability:",
                initialvalue=getattr(sg, "spi_probability", 0.0),
            )
            if new_val is not None:
                app.push_undo_state()
                sg.spi_probability = float(new_val)
                self.refresh_safety_case_table()
                self.refresh_safety_performance_indicators()
                app.update_views()

        btn = ttk.Button(win, text="Edit", command=edit_selected)
        btn.pack(pady=4)
        app._edit_spi_item = edit_selected

        self.refresh_safety_performance_indicators()

    # ------------------------------------------------------------------
    def refresh_safety_performance_indicators(self) -> None:
        """Populate the SPI explorer table."""

        app = self.app
        tree = getattr(app, "_spi_tree", None)
        if not tree or not getattr(tree, "winfo_exists", lambda: True)():
            return
        for iid in list(tree.get_children("")):
            tree.delete(iid)
        app._spi_lookup = {}

        manager = getattr(app, "sotif_manager", None)
        if manager is None:
            manager = SOTIFManager(app)
            app.sotif_manager = manager
        for sg, values in manager.iter_spi_rows():
            iid = tree.insert("", "end", values=values)
            app._spi_lookup[iid] = (sg, "SOTIF")

        for sg in getattr(app, "top_events", []):
            asil = getattr(sg, "safety_goal_asil", "")
            if asil in PMHF_TARGETS:
                target = PMHF_TARGETS[asil]
                v_str = f"{target:.2e}"
                fusa_prob = getattr(sg, "probability", "")
                p_str = f"{fusa_prob:.2e}" if fusa_prob not in ("", None) else ""
                spi_val = ""
                try:
                    if fusa_prob not in ("", None):
                        p_val = float(fusa_prob)
                        if target > 0 and p_val > 0:
                            spi_val = f"{math.log10(target / p_val):.2f}"
                except Exception:
                    spi_val = ""
                iid = tree.insert(
                    "",
                    "end",
                    values=[
                        sg.user_name or f"SG {sg.unique_id}",
                        v_str,
                        p_str,
                        spi_val,
                        "Target PMHF",
                        getattr(sg, "acceptance_criteria", ""),
                    ],
                )
                app._spi_lookup[iid] = (sg, "FUSA")

    # ------------------------------------------------------------------
    def refresh_safety_case_table(self) -> None:
        """Populate the Safety & Security Case table with solution nodes."""

        app = self.app
        tree = getattr(app, "_safety_case_tree", None)
        if not tree or not getattr(tree, "winfo_exists", lambda: True)():
            return
        for iid in list(tree.get_children("")):
            tree.delete(iid)
        app._solution_lookup = {}
        for diag in getattr(app, "all_gsn_diagrams", []):
            for node in getattr(diag, "nodes", []):
                if (
                    getattr(node, "node_type", "").lower() == "solution"
                    and getattr(node, "is_primary_instance", True)
                ):
                    app._solution_lookup[node.unique_id] = (node, diag)
                    prob = ""
                    v_target = ""
                    spi_val = ""
                    p_val = None
                    vt_val = None
                    target = getattr(node, "spi_target", "")
                    if target:
                        pg_name, spi_type = self.parse_spi_target(target)
                        te = None
                        for candidate in getattr(app, "top_events", []):
                            if app._product_goal_name(candidate) == pg_name:
                                te = candidate
                                break
                        if te:
                            if spi_type == "FUSA":
                                p = getattr(te, "probability", "")
                                vt = PMHF_TARGETS.get(getattr(te, "safety_goal_asil", ""), "")
                            else:
                                p = getattr(te, "spi_probability", "")
                                vt = getattr(te, "validation_target", "")
                            if p not in ("", None):
                                try:
                                    p_val = float(p)
                                    prob = f"{p_val:.2e}"
                                except Exception:
                                    prob = ""
                                    p_val = None
                            if vt not in ("", None):
                                try:
                                    vt_val = float(vt)
                                    v_target = f"{vt_val:.2e}"
                                except Exception:
                                    v_target = ""
                                    vt_val = None
                            try:
                                if vt_val not in (None, 0) and p_val not in (None, 0):
                                    spi_val = f"{math.log10(vt_val / p_val):.2f}"
                            except Exception:
                                spi_val = ""
                    tree.insert(
                        "",
                        "end",
                        values=[
                            node.user_name,
                            node.description,
                            node.work_product,
                            node.evidence_link,
                            v_target,
                            prob,
                            spi_val,
                            CHECK_MARK if getattr(node, "evidence_sufficient", False) else "",
                            getattr(node, "manager_notes", ""),
                        ],
                        tags=(node.unique_id,),
                    )

    # ------------------------------------------------------------------
    def show_safety_case(self) -> None:
        """Display table of all solution nodes from GSN diagrams."""

        app = self.app
        if hasattr(app, "_safety_case_tab") and app._safety_case_tab.winfo_exists():
            app.doc_nb.select(app._safety_case_tab)
            self.refresh_safety_case_table()
            return
        app._safety_case_tab = app.lifecycle_ui._new_tab("Safety & Security Case")
        win = app._safety_case_tab

        columns = [
            "Solution",
            "Description",
            "Work Product",
            "Evidence Link",
            "Validation Target",
            "Achieved Probability",
            "SPI",
            "Evidence OK",
            "Notes",
        ]
        if hasattr(win, "tk"):
            tree_frame = ttk.Frame(win)
            tree_frame.pack(fill=tk.BOTH, expand=True)
            tree = ttk.Treeview(
                tree_frame, columns=columns, show="headings", selectmode="browse"
            )
            for c in columns:
                tree.heading(c, text=c)
                width = 120
                if c in ("Description", "Evidence Link", "Notes"):
                    width = 200
                tree.column(c, width=width, anchor="center")
            vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
            hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
            tree.grid(row=0, column=0, sticky="nsew")
            vsb.grid(row=0, column=1, sticky="ns")
            hsb.grid(row=1, column=0, sticky="ew")
            tree_frame.rowconfigure(0, weight=1)
            tree_frame.columnconfigure(0, weight=1)
        else:
            tree = ttk.Treeview(win, columns=columns, show="headings", selectmode="browse")
            for c in columns:
                tree.heading(c, text=c)
                width = 120
                if c in ("Description", "Evidence Link", "Notes"):
                    width = 200
                tree.column(c, width=width, anchor="center")
            tree.pack(fill=tk.BOTH, expand=True)
        app._safety_case_tree = tree
        app._solution_lookup = {}

        def on_double_click(event):
            row = tree.identify_row(event.y)
            col = tree.identify_column(event.x)
            if not row or not col:
                return
            idx = int(col[1:]) - 1
            col_name = columns[idx]
            tags = tree.item(row, "tags")
            if not tags:
                return
            uid = tags[0]
            node_diag = app._solution_lookup.get(uid)
            if not node_diag:
                return
            node = node_diag[0]
            if col_name == "Evidence OK":
                current = tree.set(row, "Evidence OK")
                new_val = "" if current == CHECK_MARK else CHECK_MARK
                if messagebox.askokcancel("Evidence", "Are you sure?"):
                    app.push_undo_state()
                    tree.set(row, "Evidence OK", new_val)
                    node.evidence_sufficient = new_val == CHECK_MARK
            elif col_name == "Achieved Probability":
                target = getattr(node, "spi_target", "")
                pg_name, spi_type = self.parse_spi_target(target)
                te = None
                for sg in getattr(app, "top_events", []):
                    if app._product_goal_name(sg) == pg_name:
                        te = sg
                        break
                if te:
                    attr = "probability" if spi_type == "FUSA" else "spi_probability"
                    new_val = simpledialog.askfloat(
                        "Achieved Probability",
                        "Enter achieved probability:",
                        initialvalue=getattr(te, attr, 0.0),
                    )
                    if new_val is not None:
                        app.push_undo_state()
                        setattr(te, attr, float(new_val))
                        self.refresh_safety_case_table()
                        self.refresh_safety_performance_indicators()
                        app.update_views()
            elif col_name == "Notes":
                current = tree.set(row, "Notes")
                new_val = simpledialog.askstring(
                    "Notes", "Enter notes:", initialvalue=current
                )
                if new_val is not None:
                    app.push_undo_state()
                    tree.set(row, "Notes", new_val)
                    node.manager_notes = new_val

        for seq in ("<Double-Button-1>", "<Double-1>"):
            tree.bind(seq, on_double_click)

        def edit_selected(row=None):
            if row is None:
                sel = tree.selection()
                if not sel:
                    return
                row = sel[0]
            tags = tree.item(row, "tags")
            if not tags:
                return
            uid = tags[0]
            node_diag = app._solution_lookup.get(uid)
            if not node_diag:
                return
            node, diag = node_diag
            app.push_undo_state()
            GSNElementConfig(win, node, diag)
            self.refresh_safety_case_table()

        app._edit_safety_case_item = edit_selected

        def export_csv():
            path = filedialog.asksaveasfilename(
                defaultextension=".csv", filetypes=[("CSV", "*.csv")]
            )
            if not path:
                return
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                for iid in tree.get_children():
                    writer.writerow(tree.item(iid, "values"))
            messagebox.showinfo("Export", "Safety & Security Case exported")

        app.export_safety_case_csv = export_csv

        btn = ttk.Button(win, text="Edit", command=edit_selected)
        btn.pack(pady=4)
        ttk.Button(win, text="Export CSV", command=export_csv).pack(pady=4)

        menu = tk.Menu(win, tearoff=0)
        menu.add_command(label="Edit", command=edit_selected)
        menu.add_command(label="Export CSV", command=export_csv)

        def on_right_click(event):
            row = tree.identify_row(event.y)
            if row:
                tree.selection_set(row)
                menu.post(event.x_root, event.y_root)

        tree.bind("<Button-3>", on_right_click)

        self.refresh_safety_case_table()

    # ------------------------------------------------------------------
    def manage_safety_cases(self) -> None:
        app = self.app
        if not hasattr(app, "safety_case_library"):
            from analysis import SafetyCaseLibrary as _SCL

            app.safety_case_library = _SCL()
        if hasattr(app, "_safety_case_exp_tab") and app._safety_case_exp_tab.winfo_exists():
            app.doc_nb.select(app._safety_case_exp_tab)
        else:
            app._safety_case_exp_tab = app.lifecycle_ui._new_tab(
                "Safety & Security Case Explorer"
            )
            app._safety_case_window = SafetyCaseExplorer(
                app._safety_case_exp_tab, app, app.safety_case_library
            )
            app._safety_case_window.pack(fill=tk.BOTH, expand=True)
        app.refresh_all()

