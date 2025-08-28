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

import datetime
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from analysis.fmeda_utils import compute_fmeda_metrics as _compute_fmeda_metrics
from analysis.user_config import CURRENT_USER_NAME
from mainappsrc.models.fta.fault_tree_node import FaultTreeNode


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

from mainappsrc.core.safety_analysis import SafetyAnalysis_FTA_FMEA


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
        """Compute FMEDA metrics for ``events``.

        Parameters
        ----------
        events:
            Iterable of :class:`FaultTreeNode` instances representing
            failure modes to analyse.
        """
        return _compute_fmeda_metrics(
            list(events),
            getattr(self.app, "reliability_components", []),
            self.get_safety_goal_asil,
        )


__all__ = ["SafetyAnalysisService", "FMEAService"]
