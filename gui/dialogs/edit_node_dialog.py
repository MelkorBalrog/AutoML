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

"""Dialog for editing nodes and related requirement management."""


import tkinter as tk
from tkinter import ttk, simpledialog
import tkinter.font as tkFont

from gui.controls import messagebox
from gui.controls.mac_button_style import apply_purplish_button_style
from analysis.models import (
    global_requirements,
    ensure_requirement_defaults,
    REQUIREMENT_TYPE_OPTIONS,
    CAL_LEVEL_OPTIONS,
    ASIL_LEVEL_OPTIONS,
    ASIL_DECOMP_SCHEMES,
)
from analysis.fmeda_utils import GATE_NODE_TYPES
from analysis.risk_assessment import AutoMLHelper
if __package__ and __package__.startswith("AutoML"):
    from AutoML.config.automl_constants import VALID_SUBTYPES
else:  # pragma: no cover - script context
    from config.automl_constants import VALID_SUBTYPES

AutoML_Helper = AutoMLHelper()

def format_requirement(req, include_id=True):
    """Return a formatted requirement string without empty ASIL/CAL fields."""
    parts = []
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

class EditNodeDialog(simpledialog.Dialog):
    def __init__(self, parent, node, app):
        self.node = node
        self.app = app
        super().__init__(parent, title="Edit Node")

    def _build_safety_requirements(self, safety_frame, row):
        """Populate safety requirement controls at the given row."""
        if not hasattr(self.node, "safety_requirements"):
            self.node.safety_requirements = []
        ttk.Label(safety_frame, text="Safety Requirements:").grid(
            row=row, column=0, padx=5, pady=5, sticky="ne"
        )
        self.safety_req_frame = ttk.Frame(safety_frame)
        self.safety_req_frame.grid(row=row, column=1, padx=5, pady=5, sticky="w")
        self.safety_req_listbox = tk.Listbox(self.safety_req_frame, height=4, width=50)
        self.safety_req_listbox.grid(row=0, column=0, columnspan=3, sticky="w")
        for req in self.node.safety_requirements:
            self.safety_req_listbox.insert(tk.END, format_requirement(req))
        self.add_req_button = ttk.Button(
            self.safety_req_frame, text="Add New", command=self.add_safety_requirement
        )
        self.add_req_button.grid(row=1, column=0, padx=2, pady=2)
        self.edit_req_button = ttk.Button(
            self.safety_req_frame, text="Edit", command=self.edit_safety_requirement
        )
        self.edit_req_button.grid(row=1, column=1, padx=2, pady=2)
        self.delete_req_button = ttk.Button(
            self.safety_req_frame, text="Delete", command=self.delete_safety_requirement
        )
        self.delete_req_button.grid(row=1, column=2, padx=2, pady=2)
        self.add_existing_req_button = ttk.Button(
            self.safety_req_frame,
            text="Add Existing",
            command=self.add_existing_requirement,
        )
        self.add_existing_req_button.grid(row=1, column=3, padx=2, pady=2)
        self.decomp_req_button = ttk.Button(
            self.safety_req_frame, text="Decompose", command=self.decompose_safety_requirement
        )
        self.decomp_req_button.grid(row=1, column=4, padx=2, pady=2)
        self.update_decomp_button = ttk.Button(
            self.safety_req_frame,
            text="Update Scheme",
            command=self.update_decomposition_scheme,
        )
        self.update_decomp_button.grid(row=1, column=5, padx=2, pady=2)
        return row + 1

    def body(self, master):
        self.resizable(False, False)
        dialog_font = tkFont.Font(family="Arial", size=10)

        nb = ttk.Notebook(master)
        nb.pack(fill=tk.BOTH, expand=True)
        general_frame = ttk.Frame(nb)
        safety_frame = ttk.Frame(nb)
        self.safety_frame = safety_frame
        adv_frame = ttk.Frame(nb)
        nb.add(general_frame, text="General")
        nb.add(safety_frame, text="Safety")
        nb.add(adv_frame, text="Advanced")

        ttk.Label(general_frame, text="Node ID:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.id_entry = tk.Entry(general_frame, font=dialog_font, state="disabled")
        self.id_entry.insert(0, f"Node {self.node.unique_id}")
        self.id_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(general_frame, text="User Name:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.user_name_entry = tk.Entry(general_frame, font=dialog_font)
        self.user_name_entry.insert(0, self.node.user_name)
        self.user_name_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(general_frame, text="Description:").grid(row=2, column=0, padx=5, pady=5, sticky="ne")
        self.desc_text = tk.Text(general_frame, width=40, height=3, font=dialog_font, wrap="word")
        self.desc_text.insert("1.0", self.node.description)
        self.desc_text.grid(row=2, column=1, padx=5, pady=5)
        self.desc_text.bind("<Return>", self.on_enter_pressed)

        ttk.Label(general_frame, text="\nRationale:").grid(row=3, column=0, padx=5, pady=5, sticky="ne")
        self.rationale_text = tk.Text(general_frame, width=40, height=3, font=dialog_font, wrap="word")
        self.rationale_text.insert("1.0", self.node.rationale)
        self.rationale_text.grid(row=3, column=1, padx=5, pady=5)
        self.rationale_text.bind("<Return>", self.on_enter_pressed)

        row_next = 4
        if self.node.node_type.upper() in ["CONFIDENCE LEVEL", "ROBUSTNESS SCORE"]:
            ttk.Label(general_frame, text="Value (1-5):").grid(row=row_next, column=0, padx=5, pady=5, sticky="e")
            self.value_combo = ttk.Combobox(general_frame, values=["1", "2", "3", "4", "5"],
                                            state="readonly", width=5, font=dialog_font)
            current_val = self.node.quant_value if self.node.quant_value is not None else 1
            self.value_combo.set(str(int(current_val)))
            self.value_combo.grid(row=row_next, column=1, padx=5, pady=5)
            row_next += 1
            row_next = self._build_safety_requirements(safety_frame, row_next)

        elif self.node.node_type.upper() == "BASIC EVENT":
            ttk.Label(safety_frame, text="Failure Probability:").grid(row=row_next, column=0, padx=5, pady=5, sticky="e")
            self.prob_entry = tk.Entry(
                safety_frame,
                font=dialog_font,
                validate="key",
                validatecommand=(self.register(self.validate_float), "%P"),
            )
            self.prob_entry.grid(row=row_next, column=1, padx=5, pady=5)
            row_next += 1



            ttk.Label(safety_frame, text="Probability Formula:").grid(row=row_next, column=0, padx=5, pady=5, sticky="e")
            self.formula_var = tk.StringVar(value=getattr(self.node, 'prob_formula', 'linear'))
            self.formula_combo = ttk.Combobox(safety_frame, textvariable=self.formula_var,
                         values=['linear', 'exponential', 'constant'],
                         state='readonly', width=12)
            self.formula_combo.grid(row=row_next, column=1, padx=5, pady=5, sticky='w')
            self.formula_var.trace_add("write", lambda *a: self.update_probability())
            row_next += 1

            self.update_probability()
            row_next = self._build_safety_requirements(safety_frame, row_next)

        elif self.node.node_type.upper() in GATE_NODE_TYPES:
            ttk.Label(general_frame, text="Gate Type:").grid(row=row_next, column=0, padx=5, pady=5, sticky="e")
            self.gate_var = tk.StringVar(value=self.node.gate_type if self.node.gate_type else "AND")
            self.gate_combo = ttk.Combobox(general_frame, textvariable=self.gate_var, values=["AND", "OR"],
                                           state="readonly", width=10)
            self.gate_combo.grid(row=row_next, column=1, padx=5, pady=5)
            row_next += 1


            if self.node.node_type.upper() == "TOP EVENT":
                ttk.Label(safety_frame, text="Severity (1-3):").grid(row=row_next, column=0, padx=5, pady=5, sticky="e")
                self.sev_combo = ttk.Combobox(safety_frame, values=["1", "2", "3"],
                                              state="disabled", width=5, font=dialog_font)
                current_sev = self.node.severity if self.node.severity is not None else 3
                self.sev_combo.set(str(int(current_sev)))
                self.sev_combo.grid(row=row_next, column=1, padx=5, pady=5)
                row_next += 1

                ttk.Label(safety_frame, text="Controllability (1-3):").grid(row=row_next, column=0, padx=5, pady=5, sticky="e")
                self.cont_combo = ttk.Combobox(safety_frame, values=["1", "2", "3"],
                                              state="disabled", width=5, font=dialog_font)
                current_cont = self.node.controllability if self.node.controllability is not None else 3
                self.cont_combo.set(str(int(current_cont)))
                self.cont_combo.grid(row=row_next, column=1, padx=5, pady=5)
                row_next += 1

                ttk.Label(safety_frame, text="Safety Goal Description:").grid(row=row_next, column=0, padx=5, pady=5, sticky="ne")
                self.safety_goal_text = tk.Text(safety_frame, width=40, height=3, font=dialog_font, wrap="word")
                self.safety_goal_text.insert("1.0", self.node.safety_goal_description)
                self.safety_goal_text.grid(row=row_next, column=1, padx=5, pady=5)
                self.safety_goal_text.bind("<Return>", self.on_enter_pressed)
                row_next += 1

                ttk.Label(safety_frame, text="Safety Goal ASIL:").grid(row=row_next, column=0, padx=5, pady=5, sticky="e")
                self.sg_asil_var = tk.StringVar(value=self.node.safety_goal_asil if self.node.safety_goal_asil else "QM")
                self.sg_asil_combo = ttk.Combobox(
                    safety_frame,
                    textvariable=self.sg_asil_var,
                    values=ASIL_LEVEL_OPTIONS,
                    state="disabled",
                    width=8,
                )
                self.sg_asil_combo.grid(row=row_next, column=1, padx=5, pady=5, sticky="w")
                row_next += 1

                ttk.Label(safety_frame, text="Safe State:").grid(row=row_next, column=0, padx=5, pady=5, sticky="e")
                self.safe_state_entry = tk.Entry(safety_frame, width=40, font=dialog_font)
                self.safe_state_entry.insert(0, self.node.safe_state)
                self.safe_state_entry.grid(row=row_next, column=1, padx=5, pady=5, sticky="w")
                row_next += 1

                ttk.Label(safety_frame, text="Malfunction:").grid(row=row_next, column=0, padx=5, pady=5, sticky="e")
                stored_mal = getattr(self.node, 'malfunction', '')
                self.mal_var = tk.StringVar(value="")
                self.mal_combo = ttk.Combobox(
                    safety_frame,
                    textvariable=self.mal_var,
                    values=sorted(self.app.malfunctions),
                    state="readonly",
                    width=30,
                )
                self.mal_combo.grid(row=row_next, column=1, padx=5, pady=5, sticky="w")
                self.mal_sel_var = tk.StringVar(value=stored_mal)
                def mal_sel(_):
                    self.mal_sel_var.set(self.mal_var.get())
                self.mal_combo.bind("<<ComboboxSelected>>", mal_sel)
                row_next += 1
                ttk.Label(safety_frame, textvariable=self.mal_sel_var, foreground="blue").grid(row=row_next, column=1, padx=5, pady=5, sticky="w")
                row_next += 1

                ttk.Label(safety_frame, text="FTTI:").grid(row=row_next, column=0, padx=5, pady=5, sticky="e")
                self.ftti_entry = tk.Entry(
                    safety_frame,
                    width=20,
                    font=dialog_font,
                    validate="key",
                    validatecommand=(self.register(self.validate_float), "%P"),
                )
                self.ftti_entry.insert(0, getattr(self.node, "ftti", ""))
                self.ftti_entry.grid(row=row_next, column=1, padx=5, pady=5, sticky="w")
                row_next += 1

                # Diagnostic coverage and fault metric targets are not exposed in
                # the safety tab. They remain attributes of the node but are
                # configured elsewhere.

                ttk.Label(safety_frame, text="Validation Target (1/h):").grid(row=row_next, column=0, padx=5, pady=5, sticky="e")
                self.val_target_var = tk.StringVar(value=str(getattr(self.node, "validation_target", 1.0)))
                tk.Entry(
                    safety_frame,
                    textvariable=self.val_target_var,
                    width=8,
                    validate="key",
                    validatecommand=(self.register(self.validate_float), "%P"),
                ).grid(row=row_next, column=1, padx=5, pady=5, sticky="w")
                row_next += 1

                ttk.Label(safety_frame, text="Validation Target Desc:").grid(row=row_next, column=0, padx=5, pady=5, sticky="ne")
                self.val_desc_text = tk.Text(safety_frame, width=40, height=3, font=dialog_font, wrap="word")
                self.val_desc_text.insert("1.0", getattr(self.node, "validation_desc", ""))
                self.val_desc_text.grid(row=row_next, column=1, padx=5, pady=5)
                self.val_desc_text.bind("<Return>", self.on_enter_pressed)
                row_next += 1

                ttk.Label(safety_frame, text="Acceptance Criteria:").grid(row=row_next, column=0, padx=5, pady=5, sticky="ne")
                self.ac_text = tk.Text(safety_frame, width=40, height=3, font=dialog_font, wrap="word")
                self.ac_text.insert("1.0", getattr(self.node, "acceptance_criteria", ""))
                self.ac_text.grid(row=row_next, column=1, padx=5, pady=5)
                self.ac_text.bind("<Return>", self.on_enter_pressed)
                row_next += 1

        # Provide a default safety requirement section if the tab is empty.
        if not safety_frame.winfo_children():
            self._build_safety_requirements(safety_frame, 0)

        if self.node.node_type.upper() not in ["TOP EVENT", "BASIC EVENT"]:
            self.is_page_var = tk.BooleanVar(value=self.node.is_page)
            ttk.Checkbutton(general_frame, text="Is Page Gate?", variable=self.is_page_var)\
                .grid(row=row_next, column=0, columnspan=2, padx=5, pady=5, sticky="w")
            row_next += 1

        if "CONFIDENCE" in self.node.node_type.upper():
            base_name = "Confidence"
        elif "ROBUSTNESS" in self.node.node_type.upper():
            base_name = "Robustness"
        elif "TOP EVENT" in self.node.node_type.upper():
            base_name = "Prototype Assurance Level (PAL)"
        elif "GATE" in self.node.node_type.upper() or "RIGOR" in self.node.node_type.upper():
            base_name = "Rigor"
        else:
            base_name = "Other"

        if self.node.display_label.startswith("Maturity"):
            base_name = "Maturity"

        valid_subtypes = VALID_SUBTYPES.get(base_name, [])
        if not valid_subtypes:
            valid_subtypes = ["None"]
        ttk.Label(adv_frame, text="Subtype:").grid(row=row_next, column=0, padx=5, pady=5, sticky="e")
        initial_subtype = self.node.input_subtype if self.node.input_subtype else valid_subtypes[0]
        self.subtype_var = tk.StringVar(value=initial_subtype)
        state = "disabled" if base_name == "Maturity" else "readonly"
        self.subtype_combo = ttk.Combobox(adv_frame, textvariable=self.subtype_var, values=valid_subtypes,
                                          state=state, width=20)
        self.subtype_combo.grid(row=row_next, column=1, padx=5, pady=5, sticky="w")
        row_next += 1

        return self.user_name_entry

    class RequirementDialog(simpledialog.Dialog):
        def __init__(self, parent, title, initial_req=None, asil_readonly=False):
            self.initial_req = initial_req or {}
            self.asil_readonly = asil_readonly
            super().__init__(parent, title=title)
        
        def body(self, master):
            # Instead of master.resizable(), use self.top
            self.resizable(False, False)
            dialog_font = tk.font.Font(family="Arial", size=10)
            ttk.Label(master, text="Requirement Type:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
            self.type_var = tk.StringVar()
            self.type_combo = ttk.Combobox(
                master,
                textvariable=self.type_var,
                values=REQUIREMENT_TYPE_OPTIONS,
                state="readonly",
                width=20,
            )
            self.type_combo.grid(row=0, column=1, padx=5, pady=5)
            self.type_combo.bind("<<ComboboxSelected>>", self._toggle_fields)
            
            ttk.Label(master, text="Custom Requirement ID:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
            self.custom_id_entry = tk.Entry(master, width=20, font=dialog_font)
            # Preload using "custom_id" if available; otherwise, fallback to "id"
            self.custom_id_entry.insert(0, self.initial_req.get("custom_id") or self.initial_req.get("id", ""))
            self.custom_id_entry.grid(row=1, column=1, padx=5, pady=5)

            ttk.Label(master, text="Requirement Text:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
            self.req_entry = tk.Entry(master, width=40, font=dialog_font)
            self.req_entry.grid(row=2, column=1, padx=5, pady=5)

            self.asil_label = ttk.Label(master, text="ASIL:")
            self.asil_label.grid(row=3, column=0, sticky="e", padx=5, pady=5)
            self.req_asil_var = tk.StringVar()
            state = "disabled" if self.asil_readonly else "readonly"
            self.req_asil_combo = ttk.Combobox(
                master,
                textvariable=self.req_asil_var,
                values=ASIL_LEVEL_OPTIONS,
                state=state,
                width=8,
            )
            self.req_asil_combo.grid(row=3, column=1, padx=5, pady=5, sticky="w")

            self.cal_label = ttk.Label(master, text="CAL:")
            self.cal_label.grid(row=4, column=0, sticky="e", padx=5, pady=5)
            self.req_cal_var = tk.StringVar()
            self.req_cal_combo = ttk.Combobox(
                master,
                textvariable=self.req_cal_var,
                values=CAL_LEVEL_OPTIONS,
                state="readonly",
                width=8,
            )
            self.req_cal_combo.grid(row=4, column=1, padx=5, pady=5, sticky="w")
            ttk.Label(master, text="Validation Target (1/h):").grid(row=5, column=0, sticky="e", padx=5, pady=5)
            self.val_var = tk.StringVar(value=str(self.initial_req.get("validation_criteria", 0.0)))
            tk.Entry(master, textvariable=self.val_var, state="readonly", width=10).grid(row=5, column=1, padx=5, pady=5, sticky="w")

            self.type_var.set(self.initial_req.get("req_type", "vehicle"))
            self.req_entry.insert(0, self.initial_req.get("text", ""))
            self.req_asil_var.set(self.initial_req.get("asil", "QM"))
            self.req_cal_var.set(self.initial_req.get("cal", CAL_LEVEL_OPTIONS[0]))
            self._toggle_fields()
            return self.req_entry

        def apply(self):
            req_type = self.type_var.get().strip()
            req_text = self.req_entry.get().strip()
            custom_id = self.custom_id_entry.get().strip()
            asil = self.req_asil_var.get().strip()
            cal = self.req_cal_var.get().strip()
            self.result = {
                "req_type": req_type,
                "text": req_text,
                "custom_id": custom_id,
            }
            if req_type not in (
                "operational",
                "functional modification",
                "production",
                "service",
                "product",
                "legal",
                "organizational",
            ):
                self.result["asil"] = asil
                self.result["cal"] = cal

        def validate(self):
            custom_id = self.custom_id_entry.get().strip()
            # If a custom ID is provided, ensure it's unique unless we're editing this requirement
            if custom_id:
                existing = global_requirements.get(custom_id)
                if existing and custom_id not in (
                    self.initial_req.get("custom_id"),
                    self.initial_req.get("id"),
                ):
                    messagebox.showerror(
                        "Duplicate ID",
                        f"Requirement ID '{custom_id}' already exists. Please choose a unique ID.",
                    )
                    return False
            return True

        def _toggle_fields(self, event=None):
            req_type = self.type_var.get()
            hide = req_type in (
                "operational",
                "functional modification",
                "production",
                "service",
                "product",
                "legal",
                "organizational",
            )
            widgets = [self.asil_label, self.req_asil_combo, self.cal_label, self.req_cal_combo]
            if hide:
                for w in widgets:
                    w.grid_remove()
            else:
                self.asil_label.grid(row=3, column=0, sticky="e", padx=5, pady=5)
                self.req_asil_combo.grid(row=3, column=1, padx=5, pady=5, sticky="w")
                self.cal_label.grid(row=4, column=0, sticky="e", padx=5, pady=5)
                self.req_cal_combo.grid(row=4, column=1, padx=5, pady=5, sticky="w")

    class SelectExistingRequirementsDialog(simpledialog.Dialog):
            """
            A dialog that displays all global requirements in a list with checkboxes.
            The user can select one or more existing requirements to add (as clones) to the current node.
            """
            def __init__(self, parent, title="Select Existing Requirements"):
                # We'll use a dict to track checkbox variables keyed by requirement ID.
                self.selected_vars = {}
                super().__init__(parent, title=title)
    
            def body(self, master):
                ttk.Label(master, text="Select one or more existing requirements:").pack(padx=5, pady=5)
    
                # Create a container canvas and a vertical scrollbar
                container = ttk.Frame(master)
                container.pack(fill=tk.BOTH, expand=True)
    
                canvas = tk.Canvas(container, borderwidth=0)
                scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
                self.check_frame = ttk.Frame(canvas)
    
                # Configure the scrollable region when the frame's size changes
                self.check_frame.bind(
                    "<Configure>",
                    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
                )
    
                canvas.create_window((0, 0), window=self.check_frame, anchor="nw")
                canvas.configure(yscrollcommand=scrollbar.set)
    
                # Pack canvas and scrollbar side by side
                canvas.pack(side="left", fill="both", expand=True)
                scrollbar.pack(side="right", fill="y")
    
                # For each requirement in the global registry, create a Checkbutton.
                for req_id, req in global_requirements.items():
                    var = tk.BooleanVar(value=False)
                    self.selected_vars[req_id] = var
                    text = format_requirement(req)
                    ttk.Checkbutton(self.check_frame, text=text, variable=var).pack(anchor="w", padx=2, pady=2)
                return self.check_frame
    
            def apply(self):
                # Return a list of requirement IDs that were selected.
                self.result = [req_id for req_id, var in self.selected_vars.items() if var.get()]
        
    def add_existing_requirement(self):
        """
        Opens a dialog to let the user select one or more existing requirements from the global registry.
        The selected requirements are then allocated to the current node (as clones sharing the same custom ID).
        """
        global global_requirements  # Ensure we refer to the module-level variable
        if not global_requirements:
            messagebox.showinfo("No Existing Requirements", "There are no existing requirements to add.")
            return
        dialog = self.SelectExistingRequirementsDialog(self, title="Select Existing Requirements")
        if dialog.result:
            # For each selected requirement, allocate it to the node if not already present.
            if not hasattr(self.node, "safety_requirements"):
                self.node.safety_requirements = []
            for req_id in dialog.result:
                req = global_requirements.get(req_id)
                if req and not any(r["id"] == req_id for r in self.node.safety_requirements):
                    self.node.safety_requirements.append(req)
                    if self.node.node_type.upper() == "BASIC EVENT":
                        req["asil"] = self.infer_requirement_asil_from_node(self.node)
                    else:
                        pass  # ASIL recalculated when joint review closes
                    self.safety_req_listbox.insert(
                        tk.END,
                        format_requirement(req),
                    )
        else:
            messagebox.showinfo("No Selection", "No existing requirements were selected.")
   
    def add_new_requirement(self,custom_id, req_type, text, asil="QM", cal=CAL_LEVEL_OPTIONS[0]):
        # When a requirement is created, register it in the global registry.
        phase = None
        toolbox = getattr(getattr(self, "app", None), "safety_mgmt_toolbox", None)
        if toolbox is not None:
            phase = getattr(toolbox, "active_module", None)
        req = {
            "id": custom_id,
            "req_type": req_type,
            "text": text,
            "custom_id": custom_id,
            "status": "draft",
            "parent_id": "",
            "phase": phase,
        }
        ensure_requirement_defaults(req)
        if req_type not in (
            "operational",
            "functional modification",
            "production",
            "service",
            "product",
            "legal",
            "organizational",
        ):
            req["asil"] = asil
            req["cal"] = cal
        global_requirements[custom_id] = req
        print(f"Added new requirement: {req}")
        return req
        
    def list_all_requirements(self):
        # This function returns a list of formatted strings for all requirements
        return [
            format_requirement(req)
            for req in global_requirements.values()
        ]

    # --- Traceability helpers ---
    def get_requirement_allocation_names(self, req_id):
        """Return a list of node or FMEA entry names where the requirement appears."""
        names = []
        repo = SysMLRepository.get_instance()
        for diag_id, obj_id in repo.find_requirements(req_id):
            diag = repo.diagrams.get(diag_id)
            obj = next((o for o in getattr(diag, "objects", []) if o.get("obj_id") == obj_id), None)
            dname = diag.name if diag else ""
            oname = obj.get("properties", {}).get("name", "") if obj else ""
            if dname and oname:
                names.append(f"{dname}:{oname}")
            elif dname or oname:
                names.append(dname or oname)
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

    def _collect_goal_names(self, node, acc):
        if node.node_type.upper() == "TOP EVENT":
            acc.add(node.safety_goal_description or (node.user_name or f"SG {node.unique_id}"))
        for p in getattr(node, "parents", []):
            self._collect_goal_names(p, acc)

    def get_requirement_goal_names(self, req_id):
        """Return a list of safety goal names linked to the requirement."""
        goals = set()
        for n in self.app.get_all_nodes(self.app.root_node):
            reqs = getattr(n, "safety_requirements", [])
            if any((r.get("id") if isinstance(r, dict) else getattr(r, "id", None)) == req_id for r in reqs):
                self._collect_goal_names(n, goals)
        for fmea in self.app.fmeas:
            for e in fmea.get("entries", []):
                reqs = e.get("safety_requirements", []) if isinstance(e, dict) else getattr(e, "safety_requirements", [])
                if any((r.get("id") if isinstance(r, dict) else getattr(r, "id", None)) == req_id for r in reqs):
                    if isinstance(e, dict):
                        parent_list = e.get("parents") or []
                    else:
                        parent_list = getattr(e, "parents", []) or []
                    parent = parent_list[0] if parent_list else None
                    if isinstance(parent, dict) and "unique_id" in parent:
                        node = self.app.find_node_by_id_all(parent["unique_id"])
                    else:
                        node = parent if hasattr(parent, "unique_id") else None
                    if node:
                        self._collect_goal_names(node, goals)
        return sorted(goals)

    def format_requirement_with_trace(self, req):
        """Return requirement text including allocation and safety goal lists."""
        rid = req.get("id", "")
        alloc = ", ".join(self.get_requirement_allocation_names(rid))
        goals = ", ".join(self.get_requirement_goal_names(rid))
        base = format_requirement(req)
        return f"{base} (Alloc: {alloc}; SGs: {goals})"

    def infer_requirement_asil_from_node(self, node):
        """Return the highest ASIL of safety goals above the given node."""
        goals = set()
        self._collect_goal_names(node, goals)
        asil = "QM"
        for g in goals:
            a = self.app.get_safety_goal_asil(g)
            if ASIL_ORDER.get(a, 0) > ASIL_ORDER.get(asil, 0):
                asil = a
        return asil

    def refresh_model(self):
        """Delegate refresh logic to the main application."""
        # ``EditNodeDialog`` doesn't maintain its own model; instead it should
        # trigger a full refresh on the application so that any edits made in
        # the dialog propagate through the entire analysis chain.
        if hasattr(self, "app"):
            self.app.refresh_model()

    def invalidate_reviews_for_hara(self, name):
        """Reopen reviews associated with the given risk assessment."""
        for r in self.reviews:
            if name in getattr(r, "hara_names", []):
                r.closed = False
                r.approved = False
                r.reviewed = False
                for p in r.participants:
                    p.done = False
                    p.approved = False
        self.update_hara_statuses()
        self.update_fta_statuses()

    def invalidate_reviews_for_fta(self, node_id):
        """Reopen reviews that include the given FTA top event."""
        for r in self.reviews:
            if node_id in getattr(r, "fta_ids", []):
                r.closed = False
                r.approved = False
                r.reviewed = False
                for p in r.participants:
                    p.done = False
                    p.approved = False
        self.update_fta_statuses()

    def invalidate_reviews_for_requirement(self, req_id):
        """Reopen reviews that include the given requirement."""
        for r in self.reviews:
            if req_id in self.get_requirements_for_review(r):
                r.closed = False
                r.approved = False
                r.reviewed = False
                for p in r.participants:
                    p.done = False
                    p.approved = False
        self.update_requirement_statuses()

    def invalidate_reviews_for_hara(self, name):
        """Reopen reviews associated with the given risk assessment."""
        for r in self.reviews:
            if name in getattr(r, "hara_names", []):
                r.closed = False
                r.approved = False
                r.reviewed = False
                for p in r.participants:
                    p.done = False
                    p.approved = False
        self.update_hara_statuses()
        self.update_fta_statuses()

    def invalidate_reviews_for_requirement(self, req_id):
        """Reopen reviews that include the given requirement."""
        for r in self.reviews:
            if req_id in self.get_requirements_for_review(r):
                r.closed = False
                r.approved = False
                r.reviewed = False
                for p in r.participants:
                    p.done = False
                    p.approved = False
        self.update_requirement_statuses()








    
    def add_safety_requirement(self):
        """
        Opens the custom dialog to create a new requirement.
        Also, provides a button (or similar mechanism) to add existing requirements.
        """
        global global_requirements  # Ensure we refer to the module-level global_requirements
        # Use self.master (the Toplevel parent of this dialog) instead of self.
        asil_default = self.infer_requirement_asil_from_node(self.node) if self.node.node_type.upper() == "BASIC EVENT" else "QM"
        dialog = self.RequirementDialog(
            self.master,
            title="Add Safety Requirement",
            initial_req={"asil": asil_default},
            asil_readonly=self.node.node_type.upper() == "BASIC EVENT",
        )
        if dialog.result is None or dialog.result["text"] == "":
            return
        custom_id = dialog.result.get("custom_id", "").strip()
        if not custom_id:
            custom_id = str(uuid.uuid4())
        # Check global registry: if exists, update; otherwise, register new.
        if custom_id in global_requirements:
            req = global_requirements[custom_id]
            req_type = dialog.result["req_type"]
            req["req_type"] = req_type
            req["text"] = dialog.result["text"]
            if req_type not in (
                "operational",
                "functional modification",
                "production",
                "service",
                "product",
                "legal",
                "organizational",
            ):
                req["asil"] = (
                    asil_default
                    if self.node.node_type.upper() == "BASIC EVENT"
                    else dialog.result.get("asil", "QM"),
                )
                req["cal"] = dialog.result.get("cal", CAL_LEVEL_OPTIONS[0])
            else:
                req.pop("asil", None)
                req.pop("cal", None)
        else:
            req_type = dialog.result["req_type"]
            req = {
                "id": custom_id,
                "req_type": req_type,
                "text": dialog.result["text"],
                "custom_id": custom_id,
                "validation_criteria": 0.0,
                "status": "draft",
                "parent_id": "",
            }
            ensure_requirement_defaults(req)
            if req_type not in (
                "operational",
                "functional modification",
                "production",
                "service",
                "product",
                "legal",
                "organizational",
            ):
                req["asil"] = (
                    asil_default
                    if self.node.node_type.upper() == "BASIC EVENT"
                    else dialog.result.get("asil", "QM"),
                )
                req["cal"] = dialog.result.get("cal", CAL_LEVEL_OPTIONS[0])
            global_requirements[custom_id] = req

        self.app.update_validation_criteria(custom_id)

        # Allocate this requirement to the current node if not already present.
        if not hasattr(self.node, "safety_requirements"):
            self.node.safety_requirements = []
        if not any(r["id"] == custom_id for r in self.node.safety_requirements):
            self.node.safety_requirements.append(req)
            if self.node.node_type.upper() != "BASIC EVENT":
                pass  # ASIL updated after joint review
            self.safety_req_listbox.insert(
                tk.END,
                format_requirement(req),
            )

    def edit_safety_requirement(self):
        """
        Opens the edit dialog for a selected safety requirement.
        After editing, updates the global registry so that all nodes sharing that requirement are synchronized.
        """
        selected = self.safety_req_listbox.curselection()
        if not selected:
            messagebox.showwarning("Edit Requirement", "Select a requirement to edit.")
            return
        index = selected[0]
        current_req = self.node.safety_requirements[index]
        initial_req = current_req.copy()
        # Pass self.master as the parent here as well.
        dialog = self.RequirementDialog(
            self.master,
            title="Edit Safety Requirement",
            initial_req=initial_req,
            asil_readonly=self.node.node_type.upper() == "BASIC EVENT",
        )
        if dialog.result is None or dialog.result["text"] == "":
            return
        new_custom_id = dialog.result["custom_id"].strip() or current_req.get("custom_id") or current_req.get("id") or str(uuid.uuid4())
        req_type = dialog.result["req_type"]
        current_req["req_type"] = req_type
        current_req["text"] = dialog.result["text"]
        current_req["status"] = "draft"
        if req_type not in (
            "operational",
            "functional modification",
            "production",
            "service",
            "product",
            "legal",
            "organizational",
        ):
            if self.node.node_type.upper() == "BASIC EVENT":
                # Leave the ASIL untouched for decomposed requirements when
                # editing within a base event so the value set during
                # decomposition remains intact.
                pass
            else:
                current_req["asil"] = dialog.result.get("asil", "QM")
            current_req["cal"] = dialog.result.get("cal", CAL_LEVEL_OPTIONS[0])
        else:
            current_req.pop("asil", None)
            current_req.pop("cal", None)
        current_req["custom_id"] = new_custom_id
        current_req["id"] = new_custom_id
        global_requirements[new_custom_id] = current_req
        self.app.update_validation_criteria(new_custom_id)
        self.app.invalidate_reviews_for_requirement(new_custom_id)
        self.node.safety_requirements[index] = current_req
        self.safety_req_listbox.delete(index)
        if self.node.node_type.upper() != "BASIC EVENT":
            pass  # ASIL updated after joint review completion
        self.safety_req_listbox.insert(
            index,
            format_requirement(current_req),
        )

    def delete_safety_requirement(self):
        selected = self.safety_req_listbox.curselection()
        if not selected:
            messagebox.showwarning("Delete Requirement", "Select a requirement to delete.")
            return
        index = selected[0]
        req_id = self.node.safety_requirements[index]["id"]
        del self.node.safety_requirements[index]
        if self.node.node_type.upper() != "BASIC EVENT":
            pass  # ASIL recalculated after joint review
        self.safety_req_listbox.delete(index)

    def decompose_safety_requirement(self):
        selected = self.safety_req_listbox.curselection()
        if not selected:
            messagebox.showwarning("Decompose", "Select a requirement to decompose.")
            return
        index = selected[0]
        req = self.node.safety_requirements[index]
        dlg = DecompositionDialog(self, req.get("asil", "QM"))
        if not dlg.result:
            return
        asil_a, asil_b = dlg.result
        base_text = req.get("text", "")
        req_id_a = str(uuid.uuid4())
        req_id_b = str(uuid.uuid4())
        r1 = {
            "id": req_id_a,
            "req_type": req.get("req_type", "vehicle"),
            "text": base_text + " (A)",
            "custom_id": req_id_a,
            "validation_criteria": 0.0,
            "status": "draft",
            "parent_id": req.get("id"),
        }
        r2 = {
            "id": req_id_b,
            "req_type": req.get("req_type", "vehicle"),
            "text": base_text + " (B)",
            "custom_id": req_id_b,
            "validation_criteria": 0.0,
            "status": "draft",
            "parent_id": req.get("id"),
        }
        if req.get("asil") is not None:
            r1["asil"] = asil_a
            r2["asil"] = asil_b
        if req.get("cal") is not None:
            r1["cal"] = req.get("cal", CAL_LEVEL_OPTIONS[0])
            r2["cal"] = req.get("cal", CAL_LEVEL_OPTIONS[0])
        req["status"] = "draft"
        global_requirements[req.get("id")] = req
        global_requirements[req_id_a] = r1
        global_requirements[req_id_b] = r2
        self.app.update_validation_criteria(req_id_a)
        self.app.update_validation_criteria(req_id_b)
        del self.node.safety_requirements[index]
        self.node.safety_requirements.insert(index, r2)
        self.node.safety_requirements.insert(index, r1)
        if self.node.node_type.upper() != "BASIC EVENT":
            pass  # ASIL will update after joint review
        self.app.invalidate_reviews_for_requirement(req.get("id"))
        self.app.invalidate_reviews_for_requirement(req_id_a)
        self.app.invalidate_reviews_for_requirement(req_id_b)
        self.safety_req_listbox.delete(index)
        self.safety_req_listbox.insert(
            index,
            f"[{r1['id']}] [{r1['req_type']}] [{r1.get('asil','')}] [{r1.get('cal','')}] {r1['text']}",
        )
        self.safety_req_listbox.insert(
            index + 1,
            f"[{r2['id']}] [{r2['req_type']}] [{r2.get('asil','')}] [{r2.get('cal','')}] {r2['text']}",
        )

    def update_decomposition_scheme(self):
        selected = self.safety_req_listbox.curselection()
        if not selected:
            messagebox.showwarning("Update Decomposition", "Select a decomposed requirement.")
            return
        index = selected[0]
        req = self.node.safety_requirements[index]
        parent_id = req.get("parent_id")
        if not parent_id:
            messagebox.showwarning("Update Decomposition", "Selected requirement is not decomposed.")
            return
        pair_indices = [i for i, r in enumerate(self.node.safety_requirements) if r.get("parent_id") == parent_id]
        if len(pair_indices) != 2:
            messagebox.showerror("Update Decomposition", "Could not identify decomposition pair.")
            return
        parent_req = global_requirements.get(parent_id, {})
        dlg = DecompositionDialog(self, parent_req.get("asil", "QM"))
        if not dlg.result:
            return
        asil_a, asil_b = dlg.result
        pair_indices.sort()
        req_a = self.node.safety_requirements[pair_indices[0]]
        req_b = self.node.safety_requirements[pair_indices[1]]
        req_a["asil"] = asil_a
        req_b["asil"] = asil_b
        req_a["status"] = "draft"
        req_b["status"] = "draft"
        global_requirements[req_a["id"]] = req_a
        global_requirements[req_b["id"]] = req_b
        self.app.invalidate_reviews_for_requirement(req_a["id"])
        self.app.invalidate_reviews_for_requirement(req_b["id"])
        for idx, r in zip(pair_indices, (req_a, req_b)):
            self.safety_req_listbox.delete(idx)
            self.safety_req_listbox.insert(idx, f"[{r['id']}] [{r['req_type']}] [{r.get('asil','')}] {r['text']}")
        if self.node.node_type.upper() != "BASIC EVENT":
            pass  # ASIL recalculated when joint review closes

    def buttonbox(self):
        box = ttk.Frame(self)
        apply_purplish_button_style()
        ttk.Button(
            box,
            text="OK",
            width=10,
            command=self.ok,
            style="Purple.TButton",
            default=tk.ACTIVE,
        ).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(
            box,
            text="Cancel",
            width=10,
            command=self.cancel,
            style="Purple.TButton",
        ).pack(side=tk.LEFT, padx=5, pady=5)
        self.bind("<Escape>", lambda event: self.cancel())
        box.pack()

    def on_enter_pressed(self, event):
        event.widget.insert("insert", "\n")
        return "break"

    def validate_float(self, value):
        """Validation helper that accepts scientific notation.

        Tk's ``validatecommand`` fires on every keystroke, so this method
        permits intermediate states such as ``"1e"`` or ``"1e-"`` that are
        part of entering a number in scientific notation. The final value is
        still checked via ``float`` for correctness.
        """

        if value in ("", "-", "+", ".", "-.", "+.", "e", "E", "e-", "e+", "E-", "E+"):
            return True
        try:
            float(value)
            return True
        except ValueError:
            lower = value.lower()
            if lower.endswith("e"):
                try:
                    float(lower[:-1])
                    return True
                except ValueError:
                    return False
            if lower.endswith(("e-", "e+")):
                try:
                    float(lower[:-2])
                    return True
                except ValueError:
                    return False
            return False

    def update_probability(self, *_):
        if hasattr(self, "prob_entry"):
            formula = self.formula_var.get() if hasattr(self, "formula_var") else None
            if str(formula).strip().lower() == "constant":
                if not self.prob_entry.get().strip():
                    try:
                        val = float(getattr(self.node, "failure_prob", 0.0))
                    except (TypeError, ValueError):
                        val = 0.0
                    self.prob_entry.insert(0, str(val))
                return
            prob = self.app.compute_failure_prob(self.node, formula=formula)
            self.prob_entry.delete(0, tk.END)
            self.prob_entry.insert(0, f"{prob:.10g}")

    def validate(self):
        return True

    def apply(self):
        target_node = self.node if self.node.is_primary_instance else self.node.original

        old_desc = target_node.description
        target_node.user_name = self.user_name_entry.get().strip()
        target_node.description = self.desc_text.get("1.0", "end-1c")
        target_node.rationale = self.rationale_text.get("1.0", "end-1c")
        
        if self.node.node_type.upper() in ["CONFIDENCE LEVEL", "ROBUSTNESS SCORE"]:
            try:
                val = float(self.value_combo.get().strip())
                if not (1 <= val <= 5):
                    raise ValueError
                target_node.quant_value = val
            except ValueError:
                messagebox.showerror("Invalid Input", "Select a value between 1 and 5.")
        elif self.node.node_type.upper() == "BASIC EVENT":
            target_node.fault_ref = target_node.description
            desc = target_node.description.strip()
            if old_desc != desc and old_desc in self.app.faults:
                self.app.faults.remove(old_desc)
                for e in self.app.get_all_fmea_entries():
                    if getattr(e, 'fmea_cause', '') == old_desc:
                        e.fmea_cause = desc
            if desc and desc not in self.app.faults:
                self.app.faults.append(desc)
            target_node.prob_formula = self.formula_var.get()
            if target_node.prob_formula == "constant":
                try:
                    target_node.failure_prob = float(self.prob_entry.get().strip())
                except ValueError:
                    target_node.failure_prob = 0.0
            else:
                target_node.failure_prob = self.app.compute_failure_prob(
                    target_node, failure_mode_ref=getattr(target_node, 'failure_mode_ref', None), formula=target_node.prob_formula)
        elif self.node.node_type.upper() in GATE_NODE_TYPES:
            target_node.gate_type = self.gate_var.get().strip().upper()
            if old_desc != target_node.description:
                for e in self.app.get_all_fmea_entries():
                    src = self.app.get_failure_mode_node(e)
                    if src.unique_id == target_node.unique_id:
                        e.description = target_node.description
                        e.user_name = target_node.user_name
            target_node.failure_mode_ref = None
            if self.node.node_type.upper() == "TOP EVENT":
                try:
                    sev = float(self.sev_combo.get().strip())
                    if not (1 <= sev <= 3):
                        raise ValueError
                    target_node.severity = sev
                except ValueError:
                    messagebox.showerror("Invalid Input", "Select a severity between 1 and 3.")
                try:
                    cont = float(self.cont_combo.get().strip())
                    if not (1 <= cont <= 3):
                        raise ValueError
                    target_node.controllability = cont
                except ValueError:
                    messagebox.showerror("Invalid Input", "Select a controllability between 1 and 3.")
                target_node.is_page = False
                target_node.safety_goal_description = self.safety_goal_text.get("1.0", "end-1c")
                target_node.safety_goal_asil = self.sg_asil_var.get().strip()
                target_node.safe_state = self.safe_state_entry.get().strip()
                new_mal = self.mal_var.get().strip() or self.mal_sel_var.get().strip()
                if new_mal:
                    events = []
                    if target_node in self.app.top_events:
                        events = self.app.top_events
                    elif target_node in getattr(self.app, "cta_events", []):
                        events = getattr(self.app, "cta_events", [])
                    elif target_node in getattr(self.app, "paa_events", []):
                        events = getattr(self.app, "paa_events", [])
                    for te in events:
                        if te is not target_node and getattr(te, "malfunction", "") == new_mal:
                            messagebox.showerror(
                                "Duplicate Malfunction",
                                "This malfunction is already assigned to another top level event.",
                            )
                            new_mal = getattr(self.node, "malfunction", "")
                            self.mal_sel_var.set(new_mal)
                            break
                if target_node.malfunction and target_node.malfunction != new_mal:
                    self.app.rename_malfunction(target_node.malfunction, new_mal)
                target_node.malfunction = new_mal
                target_node.ftti = self.ftti_entry.get().strip()
                # Safety metrics targets are no longer edited here. Preserve
                # existing values on the node.
                try:
                    target_node.validation_target = float(self.val_target_var.get())
                except Exception:
                    target_node.validation_target = 1.0
                target_node.validation_desc = self.val_desc_text.get("1.0", "end-1c")
                target_node.acceptance_criteria = self.ac_text.get("1.0", "end-1c")
            else:
                target_node.is_page = self.is_page_var.get()

        if hasattr(self, "subtype_var"):
            target_node.input_subtype = self.subtype_var.get()

        self.app.sync_nodes_by_id(target_node)
        AutoML_Helper.calculate_assurance_recursive(
            self.app.root_node,
            self.app.top_events,
        )
        self.app.update_views()

class DecompositionDialog(simpledialog.Dialog):
    def __init__(self, parent, asil):
        self.asil = asil
        super().__init__(parent, title="Requirement Decomposition")

    def body(self, master):
        ttk.Label(master, text="Select decomposition scheme:").pack(padx=5, pady=5)
        schemes = ASIL_DECOMP_SCHEMES.get(self.asil, [])
        self.scheme_var = tk.StringVar()
        options = [f"{self.asil} -> {a}+{b}" for a, b in schemes] or ["None"]
        self.combo = ttk.Combobox(master, textvariable=self.scheme_var, values=options, state="readonly")
        if options:
            self.combo.current(0)
        self.combo.pack(padx=5, pady=5)
        return self.combo

    def apply(self):
        val = self.scheme_var.get()
        if "->" in val:
            parts = val.split("->", 1)[1].split("+")
            self.result = (parts[0].strip(), parts[1].strip())
        else:
            self.result = None

