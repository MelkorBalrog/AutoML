# Author: Miguel Marina <karel.capek.robotics@gmail.com>
import tkinter as tk
from tkinter import ttk, simpledialog

from gui import messagebox, TranslucidButton
from gui.toolboxes import (
    configure_table_style,
    _RequirementDialog,
    _SelectRequirementsDialog,
    ToolTip,
)
from analysis.models import (
    StpaEntry,
    StpaDoc,
    global_requirements,
)
from mainappsrc.models.sysml.sysml_repository import SysMLRepository
from gui.architecture import (
    DiagramConnection,
    format_control_flow_label,
    format_diagram_name,
)
from analysis.safety_management import SAFETY_ANALYSIS_WORK_PRODUCTS


class StpaWindow(tk.Frame):
    COLS = [
        "action",
        "not_providing",
        "providing",
        "incorrect_timing",
        "stopped_too_soon",
        "safety_constraints",
    ]

    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        if isinstance(master, tk.Toplevel):
            master.title("STPA Analysis")
        top = ttk.Frame(self)
        top.pack(fill=tk.X)
        ttk.Label(top, text="STPA:").pack(side=tk.LEFT)
        self.doc_var = tk.StringVar()
        self.doc_cb = ttk.Combobox(top, textvariable=self.doc_var, state="readonly")
        self.doc_cb.pack(side=tk.LEFT, padx=2)
        TranslucidButton(top, text="New", command=self.new_doc).pack(side=tk.LEFT)
        TranslucidButton(top, text="Rename", command=self.rename_doc).pack(side=tk.LEFT)
        TranslucidButton(top, text="Edit", command=self.edit_doc).pack(side=tk.LEFT)
        TranslucidButton(top, text="Delete", command=self.delete_doc).pack(side=tk.LEFT)
        self.doc_cb.bind("<<ComboboxSelected>>", self.select_doc)
        self.diag_lbl = ttk.Label(top, text="")
        self.diag_lbl.pack(side=tk.LEFT, padx=10)

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        configure_table_style("Stpa.Treeview", rowheight=80)
        self.tree = ttk.Treeview(
            tree_frame,
            columns=self.COLS,
            show="headings",
            style="Stpa.Treeview",
            height=4,
        )
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        for c in self.COLS:
            heading = "Control Action" if c == "action" else c.replace("_", " ").title()
            self.tree.heading(c, text=heading)
            width = 200 if c == "safety_constraints" else 150
            self.tree.column(c, width=width)
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        btn = ttk.Frame(self)
        btn.pack(fill=tk.X)
        TranslucidButton(btn, text="Add", command=self.add_row).pack(
            side=tk.LEFT, padx=2, pady=2
        )
        TranslucidButton(btn, text="Edit", command=self.edit_row).pack(
            side=tk.LEFT, padx=2, pady=2
        )
        TranslucidButton(btn, text="Delete", command=self.del_row).pack(
            side=tk.LEFT, padx=2, pady=2
        )

        self.refresh_docs()
        self.refresh()
        if not isinstance(master, tk.Toplevel):
            self.pack(fill=tk.BOTH, expand=True)

    # ------------------------------------------------------------------
    # Document management
    # ------------------------------------------------------------------
    def refresh_docs(self):
        toolbox = getattr(self.app, "safety_mgmt_toolbox", None)
        names = [
            d.name
            for d in self.app.stpa_docs
            if not toolbox or toolbox.document_visible("STPA", d.name)
        ]
        self.doc_cb.configure(values=names)
        repo = SysMLRepository.get_instance()
        if (
            self.app.active_stpa
            and self.app.active_stpa.name in names
        ):
            self.doc_var.set(self.app.active_stpa.name)
            diag = repo.diagrams.get(self.app.active_stpa.diagram)
            self.diag_lbl.config(text=f"Diagram: {format_diagram_name(diag)}")
        elif names:
            self.doc_var.set(names[0])
            for d in self.app.stpa_docs:
                if d.name == names[0]:
                    self.app.active_stpa = d
                    self.app.stpa_entries = d.entries
                    diag = repo.diagrams.get(d.diagram)
                    self.diag_lbl.config(text=f"Diagram: {format_diagram_name(diag)}")
                    break
        else:
            self.doc_var.set("")
            self.app.active_stpa = None
            self.app.stpa_entries = []
            self.diag_lbl.config(text="")

    def select_doc(self, *_):
        name = self.doc_var.get()
        repo = SysMLRepository.get_instance()
        for d in self.app.stpa_docs:
            if d.name == name:
                self.app.active_stpa = d
                self.app.stpa_entries = d.entries
                diag = repo.diagrams.get(d.diagram)
                self.diag_lbl.config(text=f"Diagram: {format_diagram_name(diag)}")
                toolbox = getattr(self.app, "safety_mgmt_toolbox", None)
                if toolbox:
                    toolbox.activate_document_phase("STPA", name, self.app)
                break
        self.refresh()

    class NewStpaDialog(simpledialog.Dialog):
        def __init__(self, parent, app):
            self.app = app
            super().__init__(parent, title="New STPA")

        def body(self, master):
            ttk.Label(master, text="Name").grid(row=0, column=0, sticky="e")
            self.name_var = tk.StringVar()
            name_entry = ttk.Entry(master, textvariable=self.name_var)
            name_entry.grid(row=0, column=1)
            ttk.Label(master, text="Control Flow Diagram").grid(
                row=1, column=0, sticky="e"
            )
            repo = SysMLRepository.get_instance()
            self.diag_map = {}
            diags: list[str] = []
            toolbox = getattr(self.app, "safety_mgmt_toolbox", None)
            review = getattr(self.app, "current_review", None)
            reviewed = getattr(review, "reviewed", False)
            approved = getattr(review, "approved", False)
            allowed = (
                toolbox.analysis_inputs("STPA", reviewed=reviewed, approved=approved)
                if toolbox
                else SAFETY_ANALYSIS_WORK_PRODUCTS
            )
            if "Architecture Diagram" in allowed:
                for d in repo.diagrams.values():
                    if d.diag_type != "Control Flow Diagram":
                        continue
                    if toolbox and not toolbox.document_visible("Architecture Diagram", d.name):
                        continue
                    disp = format_diagram_name(d)
                    self.diag_map[disp] = d.diag_id
                    diags.append(disp)
            self.diag_var = tk.StringVar()
            ttk.Combobox(
                master, textvariable=self.diag_var, values=diags, state="readonly"
            ).grid(row=1, column=1)
            return name_entry

        def apply(self):
            selected = self.diag_var.get()
            self.result = (self.name_var.get(), self.diag_map.get(selected, ""))

    class EditStpaDialog(simpledialog.Dialog):
        def __init__(self, parent, app):
            self.app = app
            super().__init__(parent, title="Edit STPA")

        def body(self, master):
            ttk.Label(master, text="Control Flow Diagram").grid(
                row=0, column=0, sticky="e"
            )
            repo = SysMLRepository.get_instance()
            self.diag_map = {}
            diags: list[str] = []
            toolbox = getattr(self.app, "safety_mgmt_toolbox", None)
            review = getattr(self.app, "current_review", None)
            reviewed = getattr(review, "reviewed", False)
            approved = getattr(review, "approved", False)
            allowed = (
                toolbox.analysis_inputs("STPA", reviewed=reviewed, approved=approved)
                if toolbox
                else SAFETY_ANALYSIS_WORK_PRODUCTS
            )
            if "Architecture Diagram" in allowed:
                for d in repo.diagrams.values():
                    if d.diag_type != "Control Flow Diagram":
                        continue
                    if toolbox and not toolbox.document_visible("Architecture Diagram", d.name):
                        continue
                    disp = format_diagram_name(d)
                    self.diag_map[disp] = d.diag_id
                    diags.append(disp)
            self.diag_var = tk.StringVar()
            current = ""
            if self.app.active_stpa:
                diag = repo.diagrams.get(self.app.active_stpa.diagram)
                current = format_diagram_name(diag) if diag else ""
            ttk.Combobox(
                master, textvariable=self.diag_var, values=diags, state="readonly"
            ).grid(row=0, column=1)
            if current:
                self.diag_var.set(current)
            return master

        def apply(self):
            self.result = self.diag_map.get(self.diag_var.get(), "")

    def new_doc(self):
        dlg = self.NewStpaDialog(self, self.app)
        if not getattr(dlg, "result", None):
            return
        name, diag_id = dlg.result
        doc = StpaDoc(name, diag_id, [])
        self.app.stpa_docs.append(doc)
        self.app.active_stpa = doc
        self.app.stpa_entries = doc.entries
        # Record the lifecycle phase for the new document
        if hasattr(self.app, "safety_mgmt_toolbox"):
            self.app.safety_mgmt_toolbox.register_created_work_product(
                "STPA", doc.name
            )
        self.refresh_docs()
        self.refresh()
        self.app.update_views()

    def rename_doc(self):
        if not self.app.active_stpa:
            return
        old = self.app.active_stpa.name
        name = simpledialog.askstring(
            "Rename STPA", "Name:", initialvalue=old
        )
        if not name:
            return
        self.app.active_stpa.name = name
        if hasattr(self.app, "safety_mgmt_toolbox"):
            self.app.safety_mgmt_toolbox.rename_document("STPA", old, name)
        self.refresh_docs()
        self.app.update_views()

    def edit_doc(self):
        if not self.app.active_stpa:
            return
        dlg = self.EditStpaDialog(self, self.app)
        if not getattr(dlg, "result", None):
            return
        repo = SysMLRepository.get_instance()
        diag_id = dlg.result
        self.app.active_stpa.diagram = diag_id
        self.app.stpa_entries = self.app.active_stpa.entries
        diag = repo.diagrams.get(diag_id)
        self.diag_lbl.config(text=f"Diagram: {format_diagram_name(diag)}")
        self.refresh()
        self.app.update_views()

    def delete_doc(self):
        doc = self.app.active_stpa
        if not doc:
            return
        if not messagebox.askyesno("Delete", f"Delete STPA '{doc.name}'?"):
            return
        self.app.stpa_docs.remove(doc)
        if hasattr(self.app, "safety_mgmt_toolbox"):
            self.app.safety_mgmt_toolbox.register_deleted_work_product(
                "STPA", doc.name
            )
        if self.app.stpa_docs:
            self.app.active_stpa = self.app.stpa_docs[0]
        else:
            self.app.active_stpa = None
        self.app.stpa_entries = (
            self.app.active_stpa.entries if self.app.active_stpa else []
        )
        self.refresh_docs()
        self.refresh()
        self.app.update_views()

    # ------------------------------------------------------------------
    # Row handling
    # ------------------------------------------------------------------
    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for row in self.app.stpa_entries:
            reqs = []
            for rid in row.safety_constraints:
                req = global_requirements.get(rid, {})
                text = req.get("text", "")
                reqs.append(f"[{rid}] {text}" if text else rid)
            vals = [
                row.action,
                row.not_providing,
                row.providing,
                row.incorrect_timing,
                row.stopped_too_soon,
                ";".join(reqs),
            ]
            self.tree.insert("", "end", values=vals)

    def _get_control_actions(self):
        """Return labels of control action connections for the selected diagram."""

        repo = SysMLRepository.get_instance()
        toolbox = getattr(self.app, "safety_mgmt_toolbox", None)
        review = getattr(self.app, "current_review", None)
        reviewed = getattr(review, "reviewed", False)
        approved = getattr(review, "approved", False)
        if toolbox and "Architecture Diagram" not in toolbox.analysis_inputs(
            "STPA", reviewed=reviewed, approved=approved
        ):
            return []
        diag_id = getattr(getattr(self.app, "active_stpa", None), "diagram", "")
        diagram = repo.diagrams.get(diag_id)
        if not diagram or diagram.diag_type != "Control Flow Diagram":
            return []

        labels: set[str] = set()
        # First gather labels from explicit diagram connections
        for conn_dict in getattr(diagram, "connections", []):
            conn_type = conn_dict.get("conn_type")
            stereotype = (conn_dict.get("stereotype") or "").lower()
            if conn_type != "Control Action" and stereotype != "control action":
                continue
            conn_dict.setdefault("conn_type", "Control Action")
            conn = DiagramConnection(**conn_dict)
            label = format_control_flow_label(conn, repo, diagram.diag_type)
            if label:
                labels.add(label)

        if labels:
            return sorted(labels)

        # Fall back to diagram relationships if no connections are present
        for rel_id in getattr(diagram, "relationships", []):
            rel = next((r for r in repo.relationships if r.rel_id == rel_id), None)
            if not rel:
                continue
            rel_stereo = (rel.stereotype or "").lower()
            if rel.rel_type != "Control Action" and rel_stereo != "control action":
                continue
            conn = DiagramConnection(0, 0, "Control Action", stereotype=rel.stereotype or "")
            conn.name = rel.properties.get("name", "")
            elem_id = rel.properties.get("element_id")
            if elem_id:
                conn.element_id = elem_id
            guards = rel.properties.get("guard")
            if isinstance(guards, str):
                guards = [guards]
            if guards:
                conn.guard = guards
            guard_ops = rel.properties.get("guard_ops")
            if isinstance(guard_ops, str):
                guard_ops = [guard_ops]
            if guard_ops:
                conn.guard_ops = guard_ops
            label = format_control_flow_label(conn, repo, diagram.diag_type)
            if label:
                labels.add(label)

        return sorted(labels)

    class RowDialog(simpledialog.Dialog):
        def __init__(self, parent, row=None):
            self.parent = parent
            self.app = parent.app
            self.row = row or StpaEntry("", "", "", "", "", [])
            super().__init__(parent, title="Edit STPA Row")

        def body(self, master):
            ttk.Label(master, text="Control Action").grid(row=0, column=0, sticky="e")
            actions = self.parent._get_control_actions()
            self.action_var = tk.StringVar(value=self.row.action)
            action_cb = ttk.Combobox(
                master, textvariable=self.action_var, state="readonly"
            )
            action_cb.grid(row=0, column=1, padx=5, pady=5)
            # Explicitly configure the combobox values so Tkinter updates its list
            # correctly. Passing ``values`` during construction can sometimes
            # result in an empty drop-down on some platforms.
            action_cb.configure(values=actions)
            if not self.row.action and actions:
                # Select the first control action by default so the combo box is
                # never shown empty to the user.
                self.action_var.set(actions[0])
            # Add a tooltip that always shows the full control action text.
            self._action_tt = ToolTip(action_cb, self.action_var.get())

            def _update_tooltip(_event=None):
                self._action_tt.text = self.action_var.get()

            _update_tooltip()
            action_cb.bind("<<ComboboxSelected>>", _update_tooltip)

            ttk.Label(master, text="Not Providing causes Hazard").grid(
                row=1, column=0, sticky="e"
            )
            self.np_var = tk.Entry(master, width=40)
            self.np_var.insert(0, self.row.not_providing)
            self.np_var.grid(row=1, column=1, padx=5, pady=5)

            ttk.Label(master, text="Providing causes Hazard").grid(
                row=2, column=0, sticky="e"
            )
            self.p_var = tk.Entry(master, width=40)
            self.p_var.insert(0, self.row.providing)
            self.p_var.grid(row=2, column=1, padx=5, pady=5)

            ttk.Label(master, text="Incorrect Timing/Order").grid(
                row=3, column=0, sticky="e"
            )
            self.it_var = tk.Entry(master, width=40)
            self.it_var.insert(0, self.row.incorrect_timing)
            self.it_var.grid(row=3, column=1, padx=5, pady=5)

            ttk.Label(master, text="Stopped Too Soon/ Applied Too Long").grid(
                row=4, column=0, sticky="e"
            )
            self.st_var = tk.Entry(master, width=40)
            self.st_var.insert(0, self.row.stopped_too_soon)
            self.st_var.grid(row=4, column=1, padx=5, pady=5)

            ttk.Label(master, text="Safety Constraints").grid(
                row=5, column=0, sticky="ne"
            )
            sc_frame = ttk.Frame(master)
            sc_frame.grid(row=5, column=1, padx=5, pady=5)
            self.sc_lb = tk.Listbox(sc_frame, selectmode="extended", height=4, width=40)
            self.sc_lb.grid(row=0, column=0, columnspan=4)
            for rid in self.row.safety_constraints:
                req = global_requirements.get(rid, {"text": ""})
                self.sc_lb.insert(tk.END, f"[{rid}] {req.get('text','')}")
            TranslucidButton(sc_frame, text="Add New", command=self.add_sc_new).grid(
                row=1, column=0
            )
            TranslucidButton(
                sc_frame, text="Add Existing", command=self.add_sc_existing
            ).grid(row=1, column=1)
            TranslucidButton(sc_frame, text="Edit", command=self.edit_sc).grid(
                row=1, column=2
            )
            TranslucidButton(sc_frame, text="Delete", command=self.del_sc).grid(
                row=1, column=3
            )
            return action_cb

        def add_sc_new(self):
            dlg = _RequirementDialog(
                self,
                type_options=[
                    "operational",
                    "functional modification",
                    "production",
                    "service",
                    "product",
                    "legal",
                    "organizational",
                ],
            )
            if dlg.result:
                req = dlg.result
                global_requirements[req["id"]] = req
                self.sc_lb.insert(tk.END, f"[{req['id']}] {req['text']}")

        def add_sc_existing(self):
            dlg = _SelectRequirementsDialog(self)
            if dlg.result:
                for val in dlg.result:
                    if val not in self.sc_lb.get(0, tk.END):
                        self.sc_lb.insert(tk.END, val)

        def edit_sc(self):
            sel = self.sc_lb.curselection()
            if not sel:
                return
            text = self.sc_lb.get(sel[0])
            rid = text.split("]", 1)[0][1:]
            req = global_requirements.get(
                rid, {"id": rid, "text": text, "req_type": "operational"}
            )
            dlg = _RequirementDialog(
                self,
                req,
                req_type=req.get("req_type", "operational"),
                type_options=[
                    "operational",
                    "functional modification",
                    "production",
                    "service",
                    "product",
                    "legal",
                    "organizational",
                ],
            )
            if dlg.result:
                req = dlg.result
                global_requirements[req["id"]] = req
                self.sc_lb.delete(sel[0])
                self.sc_lb.insert(sel[0], f"[{req['id']}] {req['text']}")

        def del_sc(self):
            for idx in reversed(self.sc_lb.curselection()):
                self.sc_lb.delete(idx)

        def apply(self):
            self.row.action = self.action_var.get()
            self.row.not_providing = self.np_var.get()
            self.row.providing = self.p_var.get()
            self.row.incorrect_timing = self.it_var.get()
            self.row.stopped_too_soon = self.st_var.get()
            self.row.safety_constraints = [
                self.sc_lb.get(i).split("]", 1)[0][1:] for i in range(self.sc_lb.size())
            ]

    def add_row(self):
        if not self.app.active_stpa:
            messagebox.showwarning("Add", "Create an STPA first")
            return
        dlg = self.RowDialog(self)
        if getattr(dlg, "row", None):
            self.app.stpa_entries.append(dlg.row)
        self.refresh()

    def edit_row(self):
        sel = self.tree.focus()
        if not sel:
            return
        idx = self.tree.index(sel)
        self.RowDialog(self, self.app.stpa_entries[idx])
        self.refresh()

    def del_row(self):
        sel = self.tree.selection()
        for iid in sel:
            idx = self.tree.index(iid)
            if idx < len(self.app.stpa_entries):
                del self.app.stpa_entries[idx]
        self.refresh()

    def _on_double_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        self.tree.selection_set(item)
        self.tree.focus(item)
        self.edit_row()
