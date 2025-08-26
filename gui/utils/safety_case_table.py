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

"""Table view showing solutions for a safety & security case."""

import math
import tkinter as tk
from tkinter import simpledialog

from analysis.constants import CHECK_MARK
from analysis.safety_case import SafetyCase
from gui.controls import messagebox
from gui.toolboxes import _wrap_val
from gui.utils.table_controller import TableController
if __package__ and __package__.startswith("AutoML"):
    from AutoML.config.automl_constants import PMHF_TARGETS
else:  # pragma: no cover - script context
    from config.automl_constants import PMHF_TARGETS


class SafetyCaseTable(tk.Frame):
    """Display solution nodes of a :class:`SafetyCase` in an interactive table."""

    def __init__(self, master, case: SafetyCase, app=None):
        if isinstance(master, tk.Toplevel):
            container = master
        else:
            container = master
        super().__init__(container)
        self.case = case
        self.app = app
        self._node_lookup = {}
        if isinstance(master, tk.Toplevel):
            master.title(f"Safety & Security Report: {case.name}")
            master.geometry("900x300")
            self.pack(fill=tk.BOTH, expand=True)

        columns = (
            "solution",
            "description",
            "work_product",
            "evidence_link",
            "validation_target",
            "achieved_probability",
            "spi",
            "evidence_ok",
            "notes",
        )
        self.columns = columns
        headers = {
            "solution": "Solution",
            "description": "Description",
            "work_product": "Work Product",
            "evidence_link": "Evidence Link",
            "validation_target": "Validation Target",
            "achieved_probability": "Achieved Probability",
            "spi": "SPI",
            "evidence_ok": "Evidence OK",
            "notes": "Notes",
        }
        widths = {col: 120 for col in columns}
        for col in ("description", "evidence_link", "notes"):
            widths[col] = 200
        wraps = {c: 40 for c in ("description", "evidence_link", "notes")}
        self.controller = TableController(
            self,
            columns=columns,
            headers=headers,
            style_name="SafetyCase.Treeview",
            column_widths=widths,
            wraplengths=wraps,
            rowheight=80,
        )
        self.controller.pack(fill=tk.BOTH, expand=True)
        btns = tk.Frame(self)
        btns.pack(fill=tk.X)
        tk.Button(btns, text="Move Up", command=self.controller.move_up).pack(
            side=tk.LEFT
        )
        tk.Button(btns, text="Move Down", command=self.controller.move_down).pack(
            side=tk.LEFT
        )
        self.tree = self.controller.tree

        self.tree.bind("<Double-1>", self._on_double_click, add="+")

        self.populate()

    # ------------------------------------------------------------------
    def _parse_spi_target(self, target: str) -> tuple[str, str]:
        if hasattr(self.app, "_parse_spi_target"):
            return self.app._parse_spi_target(target)
        if target.endswith(")") and "(" in target:
            name, typ = target.rsplit(" (", 1)
            return name, typ[:-1]
        return target, ""

    # ------------------------------------------------------------------
    def _product_goal_name(self, sg) -> str:
        if hasattr(self.app, "_product_goal_name"):
            return self.app._product_goal_name(sg)
        return getattr(sg, "user_name", "") or f"SG {getattr(sg, 'unique_id', '')}"

    # ------------------------------------------------------------------
    def populate(self):
        """Fill the table with solution nodes from the case."""
        self.tree.delete(*self.tree.get_children())
        self._node_lookup = {}
        app = getattr(self, "app", None)
        for row_idx, sol in enumerate(self.case.solutions, start=1):
            self._node_lookup[sol.unique_id] = sol
            v_target = ""
            prob = ""
            spi_val = ""
            if app is not None:
                target = getattr(sol, "spi_target", "")
                if target:
                    pg_name, spi_type = self._parse_spi_target(target)
                    te = None
                    for sg in getattr(app, "top_events", []):
                        if self._product_goal_name(sg) == pg_name:
                            te = sg
                            break
                    if te:
                        if spi_type == "FUSA":
                            p = getattr(te, "probability", "")
                            vt = PMHF_TARGETS.get(getattr(te, "safety_goal_asil", ""), "")
                        else:
                            p = getattr(te, "spi_probability", "")
                            vt = getattr(te, "validation_target", "")
                        p_val = vt_val = None
                        if p not in ("", None):
                            try:
                                p_val = float(p)
                                prob = f"{p_val:.2e}"
                            except Exception:
                                prob = ""
                        if vt not in ("", None):
                            try:
                                vt_val = float(vt)
                                v_target = f"{vt_val:.2e}"
                            except Exception:
                                v_target = ""
                        try:
                            if vt_val not in (None, 0) and p_val not in (None, 0):
                                spi_val = f"{math.log10(vt_val / p_val):.2f}"
                        except Exception:
                            spi_val = ""
            self.tree.insert(
                "",
                "end",
                values=(
                    row_idx,
                    _wrap_val(sol.user_name),
                    _wrap_val(getattr(sol, "description", ""), 40),
                    _wrap_val(getattr(sol, "work_product", "")),
                    _wrap_val(getattr(sol, "evidence_link", ""), 40),
                    _wrap_val(v_target),
                    _wrap_val(prob),
                    _wrap_val(spi_val),
                    _wrap_val(
                        CHECK_MARK if getattr(sol, "evidence_sufficient", False) else ""
                    ),
                    _wrap_val(getattr(sol, "manager_notes", ""), 40),
                ),
                tags=(sol.unique_id,),
            )
        self._adjust_text()

    # ------------------------------------------------------------------
    def _adjust_text(self, event=None):
        if hasattr(self, "controller"):
            self.controller.adjust_text()
    # ------------------------------------------------------------------
    def _on_double_click(self, event):
        row = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not row or not col:
            return
        idx = int(col[1:]) - 1
        if idx == 0:
            return
        col_name = self.columns[idx - 1]
        tags = self.tree.item(row, "tags")
        if not tags:
            return
        uid = tags[0]
        node = self._node_lookup.get(uid)
        if not node:
            return
        if col_name == "evidence_ok":
            current = self.tree.set(row, "evidence_ok")
            new_val = "" if current == CHECK_MARK else CHECK_MARK
            if messagebox.askokcancel("Evidence", "Are you sure?"):
                if self.app and hasattr(self.app, "push_undo_state"):
                    self.app.push_undo_state()
                node.evidence_sufficient = new_val == CHECK_MARK
                self.tree.set(row, "evidence_ok", new_val)
        elif col_name == "achieved_probability" and getattr(self, "app", None) is not None:
            target = getattr(node, "spi_target", "")
            pg_name, spi_type = self._parse_spi_target(target)
            te = None
            for sg in getattr(self.app, "top_events", []):
                if self._product_goal_name(sg) == pg_name:
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
                    if self.app and hasattr(self.app, "push_undo_state"):
                        self.app.push_undo_state()
                    setattr(te, attr, float(new_val))
                    self.populate()
                    if hasattr(self.app, "refresh_safety_performance_indicators"):
                        self.app.refresh_safety_performance_indicators()
                    if hasattr(self.app, "update_views"):
                        self.app.update_views()
        elif col_name == "notes":
            current = self.tree.set(row, "notes")
            new_val = simpledialog.askstring(
                "Notes", "Enter notes:", initialvalue=current
            )
            if new_val is not None:
                if self.app and hasattr(self.app, "push_undo_state"):
                    self.app.push_undo_state()
                node.manager_notes = new_val
                self.tree.set(row, "notes", new_val)
