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

"""Window management and opening helpers for AutoMLApp."""


import tkinter as tk
from tkinter import ttk, simpledialog

from analysis.mechanisms import (
    MechanismLibrary,
    DiagnosticMechanism,
)
from gui.windows.architecture import ArchitectureManagerDialog
from gui.explorers.safety_management_explorer import SafetyManagementExplorer


class Open_Windows_Features:
    """Encapsulate window opening and management utilities."""

    def __init__(self, app: "AutoMLApp") -> None:  # pragma: no cover - simple container
        self.app = app

    # Basic window delegates -------------------------------------------------
    def open_reliability_window(self) -> None:
        self.app.reliability_app.open_reliability_window(self.app)

    def open_fmeda_window(self) -> None:
        self.app.reliability_app.open_fmeda_window(self.app)

    def open_hazop_window(self) -> None:
        self.app.risk_app.open_hazop_window(self.app)

    def open_risk_assessment_window(self) -> None:
        self.app.risk_app.open_risk_assessment_window(self.app)

    def open_stpa_window(self) -> None:
        self.app.risk_app.open_stpa_window(self.app)

    def open_threat_window(self) -> None:
        self.app.risk_app.open_threat_window(self.app)

    def open_fi2tc_window(self) -> None:
        self.app.risk_app.open_fi2tc_window(self.app)

    def open_tc2fi_window(self) -> None:
        self.app.risk_app.open_tc2fi_window(self.app)

    def open_fault_prioritization_window(self) -> None:
        self.app.reliability_app.open_fault_prioritization_window(self.app)

    # Complex window helpers -------------------------------------------------
    def open_safety_management_toolbox(self, show_diagrams: bool = True) -> None:
        """Open the Safety & Security Management editor and browser."""
        app = self.app
        tab_exists = (
            hasattr(app, "_safety_mgmt_tab") and app._safety_mgmt_tab.winfo_exists()
        )
        window_exists = (
            hasattr(app, "safety_mgmt_window")
            and getattr(app.safety_mgmt_window, "winfo_exists", lambda: False)()
        )
        if tab_exists:
            app.doc_nb.select(app._safety_mgmt_tab)
            if window_exists:
                return
            parent = app._safety_mgmt_tab
        else:
            parent = app._safety_mgmt_tab = app.lifecycle_ui._new_tab(
                "Safety & Security Management"
            )

        from gui.safety_management_toolbox import SafetyManagementWindow
        from analysis import SafetyManagementToolbox

        if not hasattr(app, "safety_mgmt_toolbox"):
            app.safety_mgmt_toolbox = SafetyManagementToolbox()
            app.governance_manager.attach_toolbox(app.safety_mgmt_toolbox)

        app.safety_mgmt_window = SafetyManagementWindow(
            parent, app, app.safety_mgmt_toolbox, show_diagrams=show_diagrams
        )
        if hasattr(app.safety_mgmt_window, "pack"):
            app.safety_mgmt_window.pack(fill=tk.BOTH, expand=True)

        refresh = getattr(app, "refresh_all", None)
        if callable(refresh):
            refresh()

    def open_management_window(self, *args, **kwargs):
        return self.app.lifecycle_ui.open_management_window(*args, **kwargs)

    def manage_architecture(self) -> None:
        app = self.app
        if hasattr(app, "_arch_tab") and app._arch_tab.winfo_exists():
            app.doc_nb.select(app._arch_tab)
        else:
            app._arch_tab = app.lifecycle_ui._new_tab("AutoML Explorer")
            app._arch_window = ArchitectureManagerDialog(app._arch_tab, app)
            app._arch_window.pack(fill=tk.BOTH, expand=True)
        app.refresh_all()

    def manage_safety_management(self) -> None:
        app = self.app
        if not hasattr(app, "safety_mgmt_toolbox"):
            from analysis import SafetyManagementToolbox as _SMT

            app.safety_mgmt_toolbox = _SMT()
        tab_exists = hasattr(app, "_safety_exp_tab") and app._safety_exp_tab.winfo_exists()
        win_exists = (
            hasattr(app, "_safety_exp_window")
            and getattr(app._safety_exp_window, "winfo_exists", lambda: False)()
        )
        if tab_exists:
            app.doc_nb.select(app._safety_exp_tab)
            if win_exists:
                app.refresh_all()
                return
        else:
            app._safety_exp_tab = app.lifecycle_ui._new_tab(
                "Safety & Security Management Explorer"
            )
        app._safety_exp_window = SafetyManagementExplorer(
            app._safety_exp_tab, app, app.safety_mgmt_toolbox
        )
        app._safety_exp_window.pack(fill=tk.BOTH, expand=True)
        app.refresh_all()

    def manage_mechanism_libraries(self) -> None:
        app = self.app
        if hasattr(app, "_mech_tab") and app._mech_tab.winfo_exists():
            app.doc_nb.select(app._mech_tab)
            return
        app._mech_tab = app.lifecycle_ui._new_tab("Mechanism Libraries")
        win = app._mech_tab
        lib_lb = tk.Listbox(win, height=8, width=25)
        lib_lb.grid(row=0, column=0, rowspan=4, sticky="nsew")
        mech_tree = ttk.Treeview(
            win, columns=("cov", "req", "desc", "detail"), show="headings"
        )
        mech_tree.heading("cov", text="Coverage")
        mech_tree.column("cov", width=80)
        mech_tree.heading("req", text="Requirement")
        mech_tree.column("req", width=200)
        mech_tree.heading("desc", text="Description")
        mech_tree.column("desc", width=200)
        mech_tree.heading("detail", text="Detail")
        mech_tree.column("detail", width=300)
        mech_tree.grid(row=0, column=1, columnspan=4, sticky="nsew")
        win.grid_rowconfigure(0, weight=1)
        win.grid_columnconfigure(0, weight=0)
        for c in range(1, 5):
            win.grid_columnconfigure(c, weight=1)

        def refresh_libs():
            lib_lb.delete(0, tk.END)
            for lib in app.mechanism_libraries:
                lib_lb.insert(tk.END, lib.name)
            refresh_mechs()

        def refresh_mechs(*_):
            mech_tree.delete(*mech_tree.get_children())
            sel = lib_lb.curselection()
            if not sel:
                return
            lib = app.mechanism_libraries[sel[0]]
            for mech in lib.mechanisms:
                mech_tree.insert(
                    "",
                    tk.END,
                    values=(
                        f"{mech.coverage:.2f}",
                        getattr(mech, "requirement", ""),
                        mech.description,
                        mech.detail,
                    ),
                    text=mech.name,
                )

        tip_win = None

        def hide_tip():
            nonlocal tip_win
            if tip_win is not None:
                tip_win.destroy()
                tip_win = None

        def show_tip(event, text):
            nonlocal tip_win
            hide_tip()
            if not text:
                return
            tip_win = tk.Toplevel(win)
            tip_win.wm_overrideredirect(True)
            tip_win.wm_geometry(
                f"+{win.winfo_rootx()+event.x+20}+{win.winfo_rooty()+event.y+20}"
            )
            lbl = tk.Label(
                tip_win,
                text=text,
                justify="left",
                background="lightyellow",
                relief="solid",
                borderwidth=1,
                wraplength=300,
            )
            lbl.pack()

        def on_tree_motion(event):
            row = mech_tree.identify_row(event.y)
            col = mech_tree.identify_column(event.x)
            if row and col in ("#3", "#4"):
                field = "desc" if col == "#3" else "detail"
                text = mech_tree.set(row, field)
                show_tip(event, text)
            else:
                hide_tip()

        def add_lib():
            name = simpledialog.askstring("New Library", "Library name:")
            if not name:
                return
            app.mechanism_libraries.append(MechanismLibrary(name))
            refresh_libs()

        def edit_lib():
            sel = lib_lb.curselection()
            if not sel:
                return
            lib = app.mechanism_libraries[sel[0]]
            name = simpledialog.askstring("Edit Library", "Library name:", initialvalue=lib.name)
            if name:
                lib.name = name
                refresh_libs()

        def del_lib():
            sel = lib_lb.curselection()
            if not sel:
                return
            del app.mechanism_libraries[sel[0]]
            refresh_libs()

        def clone_lib():
            sel = lib_lb.curselection()
            if not sel:
                return
            lib = app.mechanism_libraries[sel[0]]
            name = simpledialog.askstring(
                "Clone Library",
                "Library name:",
                initialvalue=f"{lib.name} Copy",
            )
            if not name:
                return
            existing = {l.name for l in app.mechanism_libraries}
            base = name
            idx = 1
            while name in existing:
                name = f"{base} ({idx})"
                idx += 1
            new_mechs = [
                DiagnosticMechanism(
                    m.name,
                    m.coverage,
                    m.description,
                    m.detail,
                    getattr(m, "requirement", ""),
                )
                for m in lib.mechanisms
            ]
            app.mechanism_libraries.append(MechanismLibrary(name, new_mechs))
            refresh_libs()

        def add_mech():
            sel = lib_lb.curselection()
            if not sel:
                return
            lib = app.mechanism_libraries[sel[0]]

            class MForm(simpledialog.Dialog):
                def body(self, master):
                    self.resizable(True, True)
                    master.grid_columnconfigure(1, weight=1)
                    for r in (2, 3):
                        master.grid_rowconfigure(r, weight=1)
                    ttk.Label(master, text="Name").grid(row=0, column=0, sticky="e")
                    self.name_var = tk.StringVar()
                    ttk.Entry(master, textvariable=self.name_var).grid(row=0, column=1, sticky="ew")
                    ttk.Label(master, text="Coverage").grid(row=1, column=0, sticky="e")
                    self.cov_var = tk.StringVar(value="1.0")
                    ttk.Entry(master, textvariable=self.cov_var).grid(row=1, column=1, sticky="ew")
                    ttk.Label(master, text="Description").grid(row=2, column=0, sticky="ne")
                    self.desc_text = tk.Text(master, width=40, height=3, wrap="word")
                    self.desc_text.grid(row=2, column=1, sticky="nsew")
                    ttk.Label(master, text="Detail").grid(row=3, column=0, sticky="ne")
                    self.detail_text = tk.Text(master, width=40, height=4, wrap="word")
                    self.detail_text.grid(row=3, column=1, sticky="nsew")
                    ttk.Label(master, text="Requirement").grid(row=4, column=0, sticky="e")
                    self.req_var = tk.StringVar()
                    ttk.Entry(master, textvariable=self.req_var).grid(row=4, column=1, sticky="ew")

                def apply(self):
                    self.result = (
                        self.name_var.get(),
                        float(self.cov_var.get() or 1.0),
                        self.desc_text.get("1.0", "end-1c"),
                        self.detail_text.get("1.0", "end-1c"),
                        self.req_var.get(),
                    )

            form = MForm(win)
            if hasattr(form, "result"):
                name, cov, desc, detail, req = form.result
                lib.mechanisms.append(
                    DiagnosticMechanism(name, cov, desc, detail, req)
                )
                refresh_mechs()

        def edit_mech():
            sel_lib = lib_lb.curselection()
            sel_mech = mech_tree.selection()
            if not sel_lib or not sel_mech:
                return
            lib = app.mechanism_libraries[sel_lib[0]]
            idx = mech_tree.index(sel_mech[0])
            mech = lib.mechanisms[idx]

            class MForm(simpledialog.Dialog):
                def body(self, master):
                    self.resizable(True, True)
                    master.grid_columnconfigure(1, weight=1)
                    for r in (2, 3):
                        master.grid_rowconfigure(r, weight=1)
                    ttk.Label(master, text="Name").grid(row=0, column=0, sticky="e")
                    self.name_var = tk.StringVar(value=mech.name)
                    ttk.Entry(master, textvariable=self.name_var).grid(row=0, column=1, sticky="ew")
                    ttk.Label(master, text="Coverage").grid(row=1, column=0, sticky="e")
                    self.cov_var = tk.StringVar(value=str(mech.coverage))
                    ttk.Entry(master, textvariable=self.cov_var).grid(row=1, column=1, sticky="ew")
                    ttk.Label(master, text="Description").grid(row=2, column=0, sticky="ne")
                    self.desc_text = tk.Text(master, width=40, height=3, wrap="word")
                    self.desc_text.insert("1.0", mech.description)
                    self.desc_text.grid(row=2, column=1, sticky="nsew")
                    ttk.Label(master, text="Detail").grid(row=3, column=0, sticky="ne")
                    self.detail_text = tk.Text(master, width=40, height=4, wrap="word")
                    self.detail_text.insert("1.0", mech.detail)
                    self.detail_text.grid(row=3, column=1, sticky="nsew")
                    ttk.Label(master, text="Requirement").grid(row=4, column=0, sticky="e")
                    self.req_var = tk.StringVar(value=getattr(mech, "requirement", ""))
                    ttk.Entry(master, textvariable=self.req_var).grid(row=4, column=1, sticky="ew")

                def apply(self):
                    mech.name = self.name_var.get()
                    mech.coverage = float(self.cov_var.get() or 1.0)
                    mech.description = self.desc_text.get("1.0", "end-1c")
                    mech.detail = self.detail_text.get("1.0", "end-1c")
                    mech.requirement = self.req_var.get()

            MForm(win)
            refresh_mechs()

        def del_mech():
            sel_lib = lib_lb.curselection()
            sel_mech = mech_tree.selection()
            if not sel_lib or not sel_mech:
                return
            lib = app.mechanism_libraries[sel_lib[0]]
            idx = mech_tree.index(sel_mech[0])
            del lib.mechanisms[idx]
            refresh_mechs()

        btnf = ttk.Frame(win)
        btnf.grid(row=1, column=1, columnspan=3, sticky="ew")
        ttk.Button(btnf, text="Add Lib", command=add_lib).pack(side=tk.LEFT)
        ttk.Button(btnf, text="Edit Lib", command=edit_lib).pack(side=tk.LEFT)
        ttk.Button(btnf, text="Del Lib", command=del_lib).pack(side=tk.LEFT)
        ttk.Button(btnf, text="Clone Lib", command=clone_lib).pack(side=tk.LEFT)
        ttk.Button(btnf, text="Add Mech", command=add_mech).pack(side=tk.LEFT, padx=5)
        ttk.Button(btnf, text="Edit Mech", command=edit_mech).pack(side=tk.LEFT)
        ttk.Button(btnf, text="Del Mech", command=del_mech).pack(side=tk.LEFT)

        lib_lb.bind("<<ListboxSelect>>", refresh_mechs)
        lib_lb.bind("<Double-1>", lambda e: edit_lib())
        mech_tree.bind("<Double-1>", lambda e: edit_mech())
        mech_tree.bind("<Motion>", on_tree_motion)
        mech_tree.bind("<Leave>", lambda e: hide_tip())
        refresh_libs()
