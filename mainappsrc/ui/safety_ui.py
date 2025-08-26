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

"""UI mixin providing safety-related dialogs and editors."""

import csv
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk


class SafetyUIMixin:
    """Mixin exposing safety-related UI helper methods."""

    def show_fmeda_list(self) -> None:
        self.fmeda_manager.show_fmeda_list()

    def show_triggering_condition_list(self) -> None:
        if hasattr(self, "_tc_tab") and self._tc_tab.winfo_exists():
            self.doc_nb.select(self._tc_tab)
            return
        self._tc_tab = self.lifecycle_ui._new_tab("Triggering Conditions")
        win = self._tc_tab

        lb = tk.Listbox(win, height=10, width=40)
        lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        def refresh() -> None:
            lb.delete(0, tk.END)
            self.update_triggering_condition_list()
            for tc in self.triggering_conditions:
                lb.insert(tk.END, tc)

        win.refresh_from_repository = refresh

        def add_tc() -> None:
            name = simpledialog.askstring("Triggering Condition", "Name:")
            if name:
                self.add_triggering_condition(name.strip())
                refresh()

        def edit_tc() -> None:
            sel = lb.curselection()
            if not sel:
                return
            current = lb.get(sel[0])
            name = simpledialog.askstring(
                "Triggering Condition", "Name:", initialvalue=current
            )
            if name and name != current:
                self.rename_triggering_condition(current, name.strip())
                refresh()

        def del_tc() -> None:
            sel = list(lb.curselection())
            for idx in reversed(sel):
                name = lb.get(idx)
                if messagebox.askyesno(
                    "Delete", f"Delete triggering condition '{name}'?"
                ):
                    self.delete_triggering_condition(name)
            refresh()

        def export_csv() -> None:
            path = filedialog.asksaveasfilename(
                defaultextension=".csv", filetypes=[("CSV", "*.csv")]
            )
            if not path:
                return
            with open(path, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["Name"])
                for name in self.triggering_conditions:
                    w.writerow([name])
            messagebox.showinfo("Export", "Triggering conditions exported.")

        btn = ttk.Frame(win)
        btn.pack(side=tk.RIGHT, fill=tk.Y)
        ttk.Button(btn, text="Add", command=add_tc).pack(fill=tk.X)
        ttk.Button(btn, text="Edit", command=edit_tc).pack(fill=tk.X)
        ttk.Button(btn, text="Delete", command=del_tc).pack(fill=tk.X)
        ttk.Button(btn, text="Export CSV", command=export_csv).pack(fill=tk.X)
        refresh()

    def show_hazard_list(self) -> None:
        self.risk_app.show_hazard_list(self)

    def show_malfunction_editor(self) -> None:
        """Open a tab to manage global malfunctions."""
        if hasattr(self, "_mal_tab") and self._mal_tab.winfo_exists():
            self.doc_nb.select(self._mal_tab)
            return
        self._mal_tab = self.lifecycle_ui._new_tab("Malfunctions")
        win = self._mal_tab

        lb = tk.Listbox(win, height=10, width=40)
        lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        def refresh() -> None:
            lb.delete(0, tk.END)
            for m in self.malfunctions:
                lb.insert(tk.END, m)

        def add() -> None:
            name = simpledialog.askstring("Add Malfunction", "Name:")
            if name:
                self.add_malfunction(name)
                refresh()

        def rename() -> None:
            sel = lb.curselection()
            if not sel:
                return
            current = lb.get(sel[0])
            name = simpledialog.askstring(
                "Rename Malfunction", "Name:", initialvalue=current
            )
            if not name:
                return
            if any(m.lower() == name.lower() for m in self.malfunctions if m != current):
                messagebox.showinfo("Malfunction", "Already exists")
                return
            self.rename_malfunction(current, name)
            refresh()

        def delete() -> None:
            sel = lb.curselection()
            if not sel:
                return
            current = lb.get(sel[0])
            if not messagebox.askyesno(
                "Delete", f"Delete '{current}' and its FTA?"
            ):
                return
            self.delete_top_events_for_malfunction(current)
            self.malfunctions.remove(current)
            refresh()

        btn = ttk.Frame(win)
        btn.pack(side=tk.RIGHT, fill=tk.Y)
        ttk.Button(btn, text="Add", command=add).pack(fill=tk.X)
        ttk.Button(btn, text="Rename", command=rename).pack(fill=tk.X)
        ttk.Button(btn, text="Delete", command=delete).pack(fill=tk.X)
        refresh()

    def show_fault_list(self) -> None:
        """Open a tab to manage the list of faults."""
        if hasattr(self, "_fault_tab") and self._fault_tab.winfo_exists():
            self.doc_nb.select(self._fault_tab)
            return
        self._fault_tab = self.lifecycle_ui._new_tab("Faults")
        win = self._fault_tab

        lb = tk.Listbox(win, height=10, width=40)
        lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        def refresh() -> None:
            lb.delete(0, tk.END)
            for f in self.faults:
                lb.insert(tk.END, f)

        def add() -> None:
            name = simpledialog.askstring("Add Fault", "Name:")
            if name:
                self.add_fault(name)
                refresh()

        def rename() -> None:
            sel = lb.curselection()
            if not sel:
                return
            current = lb.get(sel[0])
            name = simpledialog.askstring("Rename Fault", "Name:", initialvalue=current)
            if not name:
                return
            self.rename_fault(current, name)
            refresh()

        def delete() -> None:
            sel = lb.curselection()
            if not sel:
                return
            current = lb.get(sel[0])
            if messagebox.askyesno("Delete", f"Delete '{current}'?"):
                self.faults.remove(current)
                refresh()

        btn = ttk.Frame(win)
        btn.pack(side=tk.RIGHT, fill=tk.Y)
        ttk.Button(btn, text="Add", command=add).pack(fill=tk.X)
        ttk.Button(btn, text="Rename", command=rename).pack(fill=tk.X)
        ttk.Button(btn, text="Delete", command=delete).pack(fill=tk.X)
        refresh()

    def show_failure_list(self) -> None:
        """Open a tab to manage the list of failures."""
        if hasattr(self, "_failure_tab") and self._failure_tab.winfo_exists():
            self.doc_nb.select(self._failure_tab)
            return
        self._failure_tab = self.lifecycle_ui._new_tab("Failures")
        win = self._failure_tab

        lb = tk.Listbox(win, height=10, width=40)
        lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        def refresh() -> None:
            lb.delete(0, tk.END)
            for fl in self.failures:
                lb.insert(tk.END, fl)

        def add() -> None:
            name = simpledialog.askstring("Add Failure", "Name:")
            if name:
                self.add_failure(name)
                refresh()

        def rename() -> None:
            sel = lb.curselection()
            if not sel:
                return
            current = lb.get(sel[0])
            name = simpledialog.askstring("Rename Failure", "Name:", initialvalue=current)
            if not name:
                return
            self.rename_failure(current, name)
            refresh()

        def delete() -> None:
            sel = lb.curselection()
            if not sel:
                return
            current = lb.get(sel[0])
            if messagebox.askyesno("Delete", f"Delete '{current}'?"):
                self.failures.remove(current)
                refresh()

        btn = ttk.Frame(win)
        btn.pack(side=tk.RIGHT, fill=tk.Y)
        ttk.Button(btn, text="Add", command=add).pack(fill=tk.X)
        ttk.Button(btn, text="Rename", command=rename).pack(fill=tk.X)
        ttk.Button(btn, text="Delete", command=delete).pack(fill=tk.X)
        refresh()

    def show_hazard_editor(self) -> None:
        self.risk_app.show_hazard_editor(self)

    def show_fault_editor(self) -> None:
        """Backward compatible alias for :meth:`show_fault_list`."""
        self.show_fault_list()

    def show_failure_editor(self) -> None:
        """Backward compatible alias for :meth:`show_failure_list`."""
        self.show_failure_list()

    def show_functional_insufficiency_list(self) -> None:
        if hasattr(self, "_fi_tab") and self._fi_tab.winfo_exists():
            self.doc_nb.select(self._fi_tab)
            return
        self._fi_tab = self.lifecycle_ui._new_tab("Functional Insufficiencies")
        win = self._fi_tab

        lb = tk.Listbox(win, height=10, width=40)
        lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        def refresh() -> None:
            lb.delete(0, tk.END)
            self.update_functional_insufficiency_list()
            for fi in self.functional_insufficiencies:
                lb.insert(tk.END, fi)

        win.refresh_from_repository = refresh

        def export_csv() -> None:
            path = filedialog.asksaveasfilename(
                defaultextension=".csv", filetypes=[("CSV", "*.csv")]
            )
            if not path:
                return
            with open(path, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["Name"])
                for name in self.functional_insufficiencies:
                    w.writerow([name])
            messagebox.showinfo(
                "Export", "Functional insufficiencies exported."
            )

        def add_fi() -> None:
            name = simpledialog.askstring(
                "Functional Insufficiency", "Name:"
            )
            if name:
                self.add_functional_insufficiency(name.strip())
                refresh()

        def edit_fi() -> None:
            sel = lb.curselection()
            if not sel:
                return
            current = lb.get(sel[0])
            name = simpledialog.askstring(
                "Functional Insufficiency", "Name:", initialvalue=current
            )
            if name and name != current:
                self.rename_functional_insufficiency(current, name.strip())
                refresh()

        def del_fi() -> None:
            sel = list(lb.curselection())
            for idx in reversed(sel):
                name = lb.get(idx)
                if messagebox.askyesno(
                    "Delete", f"Delete functional insufficiency '{name}'?"
                ):
                    self.delete_functional_insufficiency(name)
            refresh()

        btn = ttk.Frame(win)
        btn.pack(side=tk.RIGHT, fill=tk.Y)
        ttk.Button(btn, text="Add", command=add_fi).pack(fill=tk.X)
        ttk.Button(btn, text="Edit", command=edit_fi).pack(fill=tk.X)
        ttk.Button(btn, text="Delete", command=del_fi).pack(fill=tk.X)
        ttk.Button(btn, text="Export CSV", command=export_csv).pack(fill=tk.X)
        refresh()

    def show_malfunctions_editor(self) -> None:
        """Manage the global list of malfunctions."""
        if hasattr(self, "_mal_tab") and self._mal_tab.winfo_exists():
            self.doc_nb.select(self._mal_tab)
            return
        self._mal_tab = self.lifecycle_ui._new_tab("Malfunctions")
        win = self._mal_tab

        lb = tk.Listbox(win, height=10, width=30)
        lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        for m in sorted(self.malfunctions):
            lb.insert(tk.END, m)

        def add_mal() -> None:
            name = simpledialog.askstring("New Malfunction", "Name:")
            if not name:
                return
            name = name.strip()
            if not name:
                return
            if any(name.lower() == x.lower() for x in self.malfunctions):
                messagebox.showinfo("Malfunction", "Already exists")
                return
            self.malfunctions.append(name)
            lb.insert(tk.END, name)

        def edit_mal() -> None:
            sel = lb.curselection()
            if not sel:
                return
            idx = sel[0]
            current = self.malfunctions[idx]
            name = simpledialog.askstring(
                "Edit Malfunction", "Name:", initialvalue=current
            )
            if not name:
                return
            name = name.strip()
            if not name:
                return
            if any(
                name.lower() == x.lower() for i, x in enumerate(self.malfunctions) if i != idx
            ):
                messagebox.showinfo("Malfunction", "Already exists")
                return
            self.malfunctions[idx] = name
            lb.delete(idx)
            lb.insert(idx, name)
            lb.select_set(idx)
            self.update_views()

        def del_mal() -> None:
            sel = lb.curselection()
            if not sel:
                return
            idx = sel[0]
            name = self.malfunctions[idx]
            if not messagebox.askyesno(
                "Delete", f"Delete malfunction '{name}' and its FTA?"
            ):
                return
            self.delete_top_events_for_malfunction(name)
            del self.malfunctions[idx]
            lb.delete(idx)
            self.update_views()

        btn = ttk.Frame(win)
        btn.pack(side=tk.RIGHT, fill=tk.Y)
        ttk.Button(btn, text="Add", command=add_mal).pack(fill=tk.X)
        ttk.Button(btn, text="Edit", command=edit_mal).pack(fill=tk.X)
        ttk.Button(btn, text="Delete", command=del_mal).pack(fill=tk.X)

