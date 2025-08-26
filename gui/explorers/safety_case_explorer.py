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

"""Explorer for safety & security cases derived from GSN diagrams."""

import tkinter as tk
from tkinter import ttk, simpledialog
from typing import Dict, Tuple


class DiagramSelectDialog(simpledialog.Dialog):  # pragma: no cover - requires tkinter
    """Dialog presenting a read-only list of diagram names."""

    def __init__(self, parent, title: str, options: list[str], initial: str | None = None):
        self.options = options
        self.initial = initial
        self.selection = ""
        super().__init__(parent, title)

    def body(self, master):  # pragma: no cover - requires tkinter
        ttk.Label(master, text="Diagram:").pack(padx=5, pady=5)
        self.var = tk.StringVar(
            value=self.initial if self.initial is not None else (self.options[0] if self.options else "")
        )
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

from analysis.safety_case import SafetyCaseLibrary, SafetyCase
from gui.controls import messagebox
from gui import format_name_with_phase
from gui.utils.safety_case_table import SafetyCaseTable
from gui.utils.icon_factory import create_icon
from gui.styles.style_manager import StyleManager


class SafetyCaseExplorer(tk.Frame):
    """Manage and browse safety & security cases."""

    def __init__(self, master, app=None, library: SafetyCaseLibrary | None = None):
        if isinstance(master, tk.Toplevel):
            container = master
        else:
            container = master
        super().__init__(container)
        self.app = app
        self.library = library or SafetyCaseLibrary()
        if isinstance(master, tk.Toplevel):
            master.title("Safety & Security Case Explorer")
            master.geometry("350x400")
            self.pack(fill=tk.BOTH, expand=True)

        btns = ttk.Frame(self)
        btns.pack(side=tk.TOP, fill=tk.X, padx=4, pady=4)
        ttk.Button(btns, text="Open", command=self.open_item).pack(side=tk.LEFT)
        ttk.Button(btns, text="New Case", command=self.new_case).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="Edit", command=self.edit_case).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="Delete", command=self.delete_case).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="Refresh", command=self.populate).pack(side=tk.RIGHT)

        tree_frame = ttk.Frame(self)
        tree_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.tree = ttk.Treeview(tree_frame)
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        style = StyleManager.get_instance()

        def _color(name: str, default: str) -> str:
            c = style.get_color(name)
            return default if c == "#FFFFFF" else c

        self.case_icon = self._create_icon(
            "shield", _color("Safety & Security Report", "#b8860b")
        )
        self.solution_icon = self._create_icon("shield_check", _color("Solution", "#1e90ff"))
        self.item_map: Dict[str, Tuple[str, object]] = {}

        self.tree.bind("<Double-1>", self._on_double_click)
        self.populate()

    # ------------------------------------------------------------------
    def populate(self):
        """Fill the tree with safety & security reports and their solutions."""
        self.item_map.clear()
        self.tree.delete(*self.tree.get_children(""))
        for case in self.library.list_cases():
            phase = getattr(case, "phase", None)
            iid = self.tree.insert(
                "",
                "end",
                text=format_name_with_phase(case.name, phase),
                image=self.case_icon,
            )
            self.item_map[iid] = ("case", case)
            for sol in case.solutions:
                sid = self.tree.insert(
                    iid,
                    "end",
                    text=format_name_with_phase(sol.user_name, getattr(sol, "phase", None)),
                    image=self.solution_icon,
                )
                self.item_map[sid] = ("solution", sol)

    # ------------------------------------------------------------------
    def refresh(self):
        """Refresh the explorer view to reflect the current model state."""
        self.populate()

    # ------------------------------------------------------------------
    def _available_diagrams(self):
        """Return GSN diagrams visible to the safety & security report."""
        if not self.app:
            return []

        diagrams = list(getattr(self.app, "gsn_diagrams", []))
        for mod in getattr(self.app, "gsn_modules", []):
            diagrams.extend(self._collect_module_diagrams(mod))
        if not diagrams:
            diagrams = list(getattr(self.app, "all_gsn_diagrams", []))

        toolbox = getattr(self.app, "safety_mgmt_toolbox", None)
        if toolbox:
            reviewed = getattr(getattr(self.app, "current_review", None), "reviewed", False)
            approved = getattr(getattr(self.app, "current_review", None), "approved", False)
            inputs = toolbox.analysis_inputs(
                "Safety & Security Case", reviewed=reviewed, approved=approved
            )
            if "GSN Argumentation" not in inputs:
                return []
            doc_visible = getattr(toolbox, "document_visible", None)
            if doc_visible:
                phases = getattr(toolbox, "doc_phases", {}).get("GSN Argumentation", {})
                diagrams = [
                    d
                    for d in diagrams
                    if doc_visible("GSN Argumentation", d.root.user_name)
                    or d.root.user_name not in phases
                ]
        return diagrams

    # ------------------------------------------------------------------
    def _collect_module_diagrams(self, module):
        diagrams = list(getattr(module, "diagrams", []))
        for sub in getattr(module, "modules", []):
            diagrams.extend(self._collect_module_diagrams(sub))
        return diagrams

    # ------------------------------------------------------------------
    def new_case(self):
        """Create a new safety & security report derived from a GSN diagram."""
        diagrams = self._available_diagrams()
        if not diagrams:
            messagebox.showerror("New Case", "No GSN diagrams available")
            return
        name = simpledialog.askstring(
            "New Safety & Security Report", "Name:", parent=self
        )
        if not name:
            return
        diag_names = [d.root.user_name for d in diagrams]
        dlg = DiagramSelectDialog(self, "GSN Diagram", diag_names)
        diag_name = dlg.selection
        if not diag_name:
            return
        diag = next((d for d in diagrams if d.root.user_name == diag_name), None)
        if not diag:
            messagebox.showerror("New Case", "Diagram not found")
            return
        self.library.create_case(name, diag)
        self.populate()

    # ------------------------------------------------------------------
    def edit_case(self):
        """Rename the selected safety & security report or change its diagram."""
        sel = self.tree.selection()
        if not sel:
            return
        typ, obj = self.item_map.get(sel[0], (None, None))
        if typ != "case":
            return
        new_name = simpledialog.askstring(
            "Rename Safety & Security Report",
            "Name:",
            initialvalue=obj.name,
            parent=self,
        )
        if not new_name:
            return
        diagrams = self._available_diagrams()
        diag_names = [d.root.user_name for d in diagrams]
        dlg = DiagramSelectDialog(
            self, "GSN Diagram", diag_names, obj.diagram.root.user_name
        )
        new_diag_name = dlg.selection
        if not new_diag_name:
            return
        new_diag = next((d for d in diagrams if d.root.user_name == new_diag_name), None)
        if not new_diag:
            messagebox.showerror("Edit Case", "Diagram not found")
            return
        obj.name = new_name
        obj.diagram = new_diag
        obj.collect_solutions()
        self.populate()

    # ------------------------------------------------------------------
    def delete_case(self):
        sel = self.tree.selection()
        if not sel:
            return
        typ, obj = self.item_map.get(sel[0], (None, None))
        if typ != "case":
            return
        if messagebox.askokcancel("Delete", f"Delete '{obj.name}'?"):
            self.library.delete_case(obj)
            self.populate()

    # ------------------------------------------------------------------
    def open_item(self):
        sel = self.tree.selection()
        if not sel:
            return
        typ, obj = self.item_map.get(sel[0], (None, None))
        if typ == "case":
            # Prefer opening reports within the application's document notebook
            # so they appear as a new tab in the main working area instead of a
            # separate window. The ``SafetyCaseTable`` already provides
            # scrollbars via its internal ``TableController`` so users can
            # navigate large reports easily.
            if self.app and hasattr(self.app, "_new_tab"):
                tab = self.app._new_tab(f"Safety & Security Report: {obj.name}")
                table = SafetyCaseTable(tab, obj, app=self.app)
                table.pack(fill=tk.BOTH, expand=True)
            else:  # Fallback to a new toplevel window if no app context
                win = tk.Toplevel(self)
                SafetyCaseTable(win, obj, app=self.app)
        elif typ == "solution" and self.app:
            for case in self.library.cases:
                if obj in case.solutions:
                    opener = getattr(getattr(self.app, "window_controllers", None), "open_gsn_diagram", None)
                    if opener:
                        opener(case.diagram)
                    break

    # ------------------------------------------------------------------
    def _on_double_click(self, event):
        self.open_item()

    # ------------------------------------------------------------------
    def _create_icon(self, shape: str, color: str = "black") -> tk.PhotoImage:
        """Proxy to the shared icon factory."""
        return create_icon(shape, color)
