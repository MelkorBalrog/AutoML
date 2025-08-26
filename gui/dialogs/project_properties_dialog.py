#!/usr/bin/env python3
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

"""Tkinter dialog for editing project properties."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk, messagebox
from typing import Dict


class ProjectPropertiesDialog:
    """Encapsulate project property editing UI and persistence."""

    def __init__(self, app) -> None:
        self.app = app
        self.project_manager = app.project_manager

    def show(self) -> None:
        """Display the dialog and persist changes on save."""
        prop_win = tk.Toplevel(self.app.root)
        prop_win.title("Project Properties")
        prop_win.resizable(False, False)
        dialog_font = tkFont.Font(family="Arial", size=10)

        ttk.Label(prop_win, text="PDF Report Name:", font=dialog_font).grid(
            row=0, column=0, padx=10, pady=10, sticky="w"
        )
        pdf_entry = ttk.Entry(prop_win, width=40, font=dialog_font)
        pdf_entry.insert(
            0, self.app.project_properties.get("pdf_report_name", "AutoML-Analyzer PDF Report")
        )
        pdf_entry.grid(row=0, column=1, padx=10, pady=10)

        var_detailed = tk.BooleanVar(
            value=self.app.project_properties.get("pdf_detailed_formulas", True)
        )
        ttk.Checkbutton(
            prop_win,
            text="Show Detailed Formulas in PDF Report",
            variable=var_detailed,
        ).grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="w")

        smt = getattr(self.app, "safety_mgmt_toolbox", None)
        all_frozen = False
        if smt:
            diagrams = smt.list_diagrams()
            all_frozen = diagrams and all(smt.diagram_frozen(d) for d in diagrams)
        var_freeze = tk.BooleanVar(
            value=self.app.project_properties.get("freeze_governance_diagrams", bool(all_frozen))
        )
        ttk.Checkbutton(
            prop_win,
            text="Freeze Governance Diagrams",
            variable=var_freeze,
        ).grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="w")

        exp_vars = self.app.probability_reliability._build_probability_frame(
            prop_win,
            "Exposure Probabilities P(E|HB)",
            range(1, 5),
            self.app.project_properties.get("exposure_probabilities", {}),
            3,
            dialog_font,
        )
        ctrl_vars = self.app.probability_reliability._build_probability_frame(
            prop_win,
            "Controllability Probabilities P(C|E)",
            range(1, 4),
            self.app.project_properties.get("controllability_probabilities", {}),
            4,
            dialog_font,
        )
        sev_vars = self.app.probability_reliability._build_probability_frame(
            prop_win,
            "Severity Probabilities P(S|C)",
            range(1, 4),
            self.app.project_properties.get("severity_probabilities", {}),
            5,
            dialog_font,
        )

        def save_props() -> None:
            new_name = pdf_entry.get().strip()
            if not new_name:
                messagebox.showwarning(
                    "Project Properties", "PDF Report Name cannot be empty."
                )
                return
            self.project_manager.apply_project_properties(
                new_name,
                var_detailed.get(),
                exp_vars,
                ctrl_vars,
                sev_vars,
                var_freeze.get(),
            )
            messagebox.showinfo("Project Properties", "Project properties updated.")
            prop_win.destroy()

        ttk.Button(prop_win, text="Save", command=save_props, width=10).grid(
            row=6, column=0, columnspan=2, pady=10
        )
        prop_win.update_idletasks()
        prop_win.minsize(prop_win.winfo_width(), prop_win.winfo_height())
        prop_win.transient(self.app.root)
        prop_win.grab_set()
        self.app.root.wait_window(prop_win)
