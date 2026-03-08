# SPDX-License-Identifier: GPL-3.0-or-later
# Author: Miguel Marina <karel.capek.robotics@gmail.com>
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

import tkinter as tk
from tkinter import simpledialog, ttk
from gui.controls import messagebox
from gui.controls.mac_button_style import apply_translucid_button_style
from gui.styles.style_manager import StyleManager
from gui.dialogs.dialog_utils import askstring_fixed
from dataclasses import dataclass, field
from typing import List
import difflib
import sys
import re
from pathlib import Path
from config import load_diagram_rules
import json
import time
try:
    from PIL import Image, ImageTk
except ModuleNotFoundError:  # pragma: no cover - pillow optional
    Image = ImageTk = None

# Node types treated as gates when deriving component names
_CONFIG_PATH = (
    Path(__file__).resolve().parents[1] / "config" / "rules" / "diagram_rules.json"
)
_CONFIG = load_diagram_rules(_CONFIG_PATH)
GATE_NODE_TYPES = set(_CONFIG.get("gate_node_types", []))


def reload_config() -> None:
    """Reload gate node types from configuration."""
    global _CONFIG, GATE_NODE_TYPES
    _CONFIG = load_diagram_rules(_CONFIG_PATH)
    GATE_NODE_TYPES = set(_CONFIG.get("gate_node_types", []))

EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")

# Access the drawing helper defined in the main application if available.
fta_drawing_helper = getattr(sys.modules.get('__main__'), 'fta_drawing_helper', None)

@dataclass
class ReviewParticipant:
    name: str
    email: str
    role: str  # 'reviewer', 'approver', or 'moderator'
    done: bool = False
    approved: bool = False
    reject_reason: str = ""
    start_time: float = 0.0
    time_spent: float = 0.0

@dataclass
class ReviewComment:
    comment_id: int
    node_id: int
    text: str
    reviewer: str
    target_type: str = "node"  # 'node', 'requirement', 'fmea', or 'fmea_field'
    req_id: str = ""
    field: str = ""
    resolved: bool = False
    resolution: str = ""

@dataclass
class ReviewData:
    name: str = ""
    description: str = ""
    mode: str = "peer"  # 'peer' or 'joint'
    moderators: List[ReviewParticipant] = field(default_factory=list)
    participants: List[ReviewParticipant] = field(default_factory=list)
    comments: List[ReviewComment] = field(default_factory=list)
    fta_ids: List[int] = field(default_factory=list)
    fmea_names: List[str] = field(default_factory=list)
    fmeda_names: List[str] = field(default_factory=list)
    hazop_names: List[str] = field(default_factory=list)
    hara_names: List[str] = field(default_factory=list)
    stpa_names: List[str] = field(default_factory=list)
    fi2tc_names: List[str] = field(default_factory=list)
    tc2fi_names: List[str] = field(default_factory=list)
    due_date: str = ""
    closed: bool = False
    approved: bool = False
    reviewed: bool = False

class ParticipantDialog(simpledialog.Dialog):
    def __init__(self, parent, joint: bool, initial_mods=None, initial_parts=None):
        self.joint = joint
        self.initial_mods = initial_mods or []
        self.initial_parts = initial_parts or []
        self.mod_rows = []
        self.part_rows = []
        super().__init__(parent, title="Review Participants")

    def body(self, master):
        self.resizable(False, False)
        nb = ttk.Notebook(master)
        nb.pack(fill=tk.BOTH, expand=True)

        mod_tab = ttk.Frame(nb)
        part_tab = ttk.Frame(nb)
        nb.add(mod_tab, text="Moderators")
        nb.add(part_tab, text="Participants")

        tk.Label(mod_tab, text="Moderators:").pack(anchor="w")
        header = tk.Frame(mod_tab)
        header.pack(fill=tk.X)
        tk.Label(header, text="Name", width=15).pack(side=tk.LEFT)
        tk.Label(header, text="Email", width=20).pack(side=tk.LEFT, padx=5)
        self.mod_frame = tk.Frame(mod_tab)
        self.mod_frame.pack(fill=tk.BOTH, expand=True)
        tk.Button(mod_tab, text="Add Moderator", command=self.add_mod_row).pack(pady=5)
        for m in (self.initial_mods or [None]):
            self.add_mod_row(m)

        tk.Label(part_tab, text="Participants:").pack(anchor="w")
        phead = tk.Frame(part_tab)
        phead.pack(fill=tk.X)
        tk.Label(phead, text="Name", width=15).pack(side=tk.LEFT)
        tk.Label(phead, text="Email", width=20).pack(side=tk.LEFT, padx=5)
        if self.joint:
            tk.Label(phead, text="Role", width=10).pack(side=tk.LEFT, padx=5)
        self.part_frame = tk.Frame(part_tab)
        self.part_frame.pack(fill=tk.BOTH, expand=True)
        tk.Button(part_tab, text="Add Participant", command=self.add_part_row).pack(pady=5)
        for p in (self.initial_parts or [None]):
            self.add_part_row(p)

    def add_mod_row(self, data=None):
        frame = tk.Frame(self.mod_frame)
        frame.pack(fill=tk.X, pady=2)
        name = tk.Entry(frame, width=15)
        name.pack(side=tk.LEFT)
        email = tk.Entry(frame, width=20)
        email.pack(side=tk.LEFT, padx=5)
        if isinstance(data, ReviewParticipant):
            name.insert(0, data.name)
            email.insert(0, data.email)
        self.mod_rows.append((name, email))

    def add_part_row(self, data=None):
        frame = tk.Frame(self.part_frame)
        frame.pack(fill=tk.X, pady=2)
        name = tk.Entry(frame, width=15)
        name.pack(side=tk.LEFT)
        email = tk.Entry(frame, width=20)
        email.pack(side=tk.LEFT, padx=5)
        if self.joint:
            role_cb = ttk.Combobox(frame, values=["reviewer", "approver"], state="readonly", width=10)
            role_cb.current(0)
            role_cb.pack(side=tk.LEFT, padx=5)
        else:
            role_cb = None
        if isinstance(data, ReviewParticipant):
            name.insert(0, data.name)
            email.insert(0, data.email)
            if role_cb:
                role_cb.set(data.role)
        self.part_rows.append((name, email, role_cb))

    def apply(self):
        moderators = []
        seen = {}
        for name_e, email_e in self.mod_rows:
            name = name_e.get().strip()
            if not name:
                continue
            email = email_e.get().strip()
            if email and not EMAIL_REGEX.fullmatch(email):
                messagebox.showerror("Email", f"Invalid email address: {email}")
                self.result = None
                return
            if name in seen:
                messagebox.showerror("Participants", f"{name} already added")
                self.result = None
                return
            seen[name] = "moderator"
            moderators.append(ReviewParticipant(name, email, "moderator"))

        participants = []
        for name_entry, email_entry, role_cb in self.part_rows:
            name = name_entry.get().strip()
            if not name:
                continue
            email = email_entry.get().strip()
            if email and not EMAIL_REGEX.fullmatch(email):
                messagebox.showerror("Email", f"Invalid email address: {email}")
                self.result = None
                return
            role = role_cb.get() if role_cb else "reviewer"
            if name in seen:
                messagebox.showerror("Participants", f"{name} already added")
                self.result = None
                return
            seen[name] = role
            participants.append(ReviewParticipant(name, email, role))

        self.result = (moderators, participants)


class EmailConfigDialog(simpledialog.Dialog):
    """Prompt for SMTP configuration and login credentials."""

    def __init__(self, parent, default_email=""):
        self.default_email = default_email
        super().__init__(parent, title="Email Settings")

    def body(self, master):
        self.resizable(False, False)
        nb = ttk.Notebook(master)
        nb.pack(fill=tk.BOTH, expand=True)

        server_tab = ttk.Frame(nb)
        cred_tab = ttk.Frame(nb)
        nb.add(server_tab, text="Server")
        nb.add(cred_tab, text="Credentials")

        tk.Label(server_tab, text="SMTP Server:").grid(row=0, column=0, sticky="w")
        self.server_entry = tk.Entry(server_tab)
        self.server_entry.insert(0, "smtp.gmail.com")
        self.server_entry.grid(row=0, column=1, pady=2)

        tk.Label(server_tab, text="Port:").grid(row=1, column=0, sticky="w")
        self.port_entry = tk.Entry(server_tab)
        self.port_entry.insert(0, "465")
        self.port_entry.grid(row=1, column=1, pady=2)

        tk.Label(cred_tab, text="Email:").grid(row=0, column=0, sticky="w")
        self.email_entry = tk.Entry(cred_tab)
        if self.default_email:
            self.email_entry.insert(0, self.default_email)
        self.email_entry.grid(row=0, column=1, pady=2)

        tk.Label(cred_tab, text="Password:").grid(row=1, column=0, sticky="w")
        self.pass_entry = tk.Entry(cred_tab, show="*")
        self.pass_entry.grid(row=1, column=1, pady=2)
        tk.Label(cred_tab, text="Use an app password for Gmail with 2FA.",
                 font=(None, 8)).grid(row=2, column=0, columnspan=2, pady=(2,0))
        return self.email_entry

    def apply(self):
        try:
            port = int(self.port_entry.get().strip())
        except ValueError:
            messagebox.showerror("Email", "Invalid port number")
            self.result = None
            return
        self.result = {
            "server": self.server_entry.get().strip(),
            "port": port,
            "email": self.email_entry.get().strip(),
            "password": self.pass_entry.get(),
        }


class ReviewScopeDialog(simpledialog.Dialog):
    def __init__(self, parent, app):
        self.app = app
        super().__init__(parent, title="Select Review Scope")

    def body(self, master):
        self.resizable(False, False)
        tk.Label(master, text="FTAs:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.fta_vars = []
        fta_frame = tk.Frame(master)
        fta_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        for te in self.app.top_events:
            label = te.user_name or te.description or f"Node {te.unique_id}"
            var = tk.BooleanVar()
            cb = tk.Checkbutton(fta_frame, text=label, variable=var, anchor="w")
            cb.pack(fill=tk.X, anchor="w")
            self.fta_vars.append((var, te.unique_id))

        tk.Label(master, text="FMEAs:").grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.fmea_vars = []
        fmea_frame = tk.Frame(master)
        fmea_frame.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        for f in self.app.fmeas:
            var = tk.BooleanVar()
            cb = tk.Checkbutton(fmea_frame, text=f['name'], variable=var, anchor="w")
            cb.pack(fill=tk.X, anchor="w")
            self.fmea_vars.append((var, f['name']))
        tk.Label(master, text="FMEDAs:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.fmeda_vars = []
        fmeda_frame = tk.Frame(master)
        fmeda_frame.grid(row=1, column=2, padx=5, pady=5, sticky="nsew")
        for d in self.app.fmedas:
            var = tk.BooleanVar()
            cb = tk.Checkbutton(fmeda_frame, text=d['name'], variable=var, anchor="w")
            cb.pack(fill=tk.X, anchor="w")
            self.fmeda_vars.append((var, d['name']))
        tk.Label(master, text="HAZOPs:").grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.hazop_vars = []
        hazop_frame = tk.Frame(master)
        hazop_frame.grid(row=1, column=3, padx=5, pady=5, sticky="nsew")
        for d in self.app.hazop_docs:
            var = tk.BooleanVar()
            cb = tk.Checkbutton(hazop_frame, text=d.name, variable=var, anchor="w")
            cb.pack(fill=tk.X, anchor="w")
            self.hazop_vars.append((var, d.name))
        tk.Label(master, text="Risk Assessments:").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.hara_vars = []
        hara_frame = tk.Frame(master)
        hara_frame.grid(row=1, column=4, padx=5, pady=5, sticky="nsew")
        for d in self.app.hara_docs:
            var = tk.BooleanVar()
            cb = tk.Checkbutton(hara_frame, text=d.name, variable=var, anchor="w")
            cb.pack(fill=tk.X, anchor="w")
            self.hara_vars.append((var, d.name))

        tk.Label(master, text="STPAs:").grid(row=0, column=5, padx=5, pady=5, sticky="w")
        self.stpa_vars = []
        stpa_frame = tk.Frame(master)
        stpa_frame.grid(row=1, column=5, padx=5, pady=5, sticky="nsew")
        for d in self.app.stpa_docs:
            var = tk.BooleanVar()
            cb = tk.Checkbutton(stpa_frame, text=d.name, variable=var, anchor="w")
            cb.pack(fill=tk.X, anchor="w")
            self.stpa_vars.append((var, d.name))

        tk.Label(master, text="FI2TCs:").grid(row=0, column=6, padx=5, pady=5, sticky="w")
        self.fi2tc_vars = []
        fi2tc_frame = tk.Frame(master)
        fi2tc_frame.grid(row=1, column=6, padx=5, pady=5, sticky="nsew")
        for d in self.app.fi2tc_docs:
            var = tk.BooleanVar()
            cb = tk.Checkbutton(fi2tc_frame, text=d.name, variable=var, anchor="w")
            cb.pack(fill=tk.X, anchor="w")
            self.fi2tc_vars.append((var, d.name))

        tk.Label(master, text="TC2FIs:").grid(row=0, column=7, padx=5, pady=5, sticky="w")
        self.tc2fi_vars = []
        tc2fi_frame = tk.Frame(master)
        tc2fi_frame.grid(row=1, column=7, padx=5, pady=5, sticky="nsew")
        for d in self.app.tc2fi_docs:
            var = tk.BooleanVar()
            cb = tk.Checkbutton(tc2fi_frame, text=d.name, variable=var, anchor="w")
            cb.pack(fill=tk.X, anchor="w")
            self.tc2fi_vars.append((var, d.name))

        tk.Label(master, text="Check items to include in the review").grid(row=2, column=0, columnspan=8, pady=(2,5))

    def apply(self):
        fta_ids = [uid for var, uid in self.fta_vars if var.get()]
        fmea_names = [name for var, name in self.fmea_vars if var.get()]
        fmeda_names = [name for var, name in self.fmeda_vars if var.get()]
        hazop_names = [name for var, name in self.hazop_vars if var.get()]
        hara_names = [name for var, name in self.hara_vars if var.get()]
        stpa_names = [name for var, name in self.stpa_vars if var.get()]
        fi2tc_names = [name for var, name in self.fi2tc_vars if var.get()]
        tc2fi_names = [name for var, name in self.tc2fi_vars if var.get()]
        self.result = (
            fta_ids,
            fmea_names,
            fmeda_names,
            hazop_names,
            hara_names,
            stpa_names,
            fi2tc_names,
            tc2fi_names,
        )


class UserSelectDialog(simpledialog.Dialog):
    """Prompt for user selection via combo box with email."""

    def __init__(self, parent, participants, initial_name=""):
        self.participants = participants
        self.initial_name = initial_name
        super().__init__(parent, title="Select User")

    def body(self, master):
        self.resizable(False, False)
        tk.Label(master, text="Name:").grid(row=0, column=0, sticky="w")
        names = [p.name for p in self.participants]
        self.name_var = tk.StringVar()
        self.name_combo = ttk.Combobox(master, values=names, textvariable=self.name_var, state="readonly")
        self.name_combo.grid(row=0, column=1, pady=5)
        self.name_combo.bind("<<ComboboxSelected>>", self.on_select)
        if self.initial_name and self.initial_name in names:
            self.name_combo.set(self.initial_name)
        elif names:
            self.name_combo.current(0)

        tk.Label(master, text="Email:").grid(row=1, column=0, sticky="w")
        self.email_entry = tk.Entry(master)
        self.email_entry.grid(row=1, column=1, pady=5)
        self.on_select()
        return self.name_combo

    def on_select(self, event=None):
        name = self.name_var.get()
        email = ""
        for p in self.participants:
            if p.name == name:
                email = p.email
                break
        self.email_entry.delete(0, tk.END)
        if email:
            self.email_entry.insert(0, email)

    def apply(self):
        self.result = (self.name_var.get().strip(), self.email_entry.get().strip())

class ReviewToolbox(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        apply_translucid_button_style()
        self.app = app
        if isinstance(master, tk.Toplevel):
            master.title("Review Toolbox")
            master.protocol("WM_DELETE_WINDOW", self.on_close)

        review_frame = tk.Frame(self)
        review_frame.pack(fill=tk.X)
        tk.Label(review_frame, text="Review:").pack(side=tk.LEFT)
        self.review_var = tk.StringVar()
        self.review_combo = ttk.Combobox(review_frame, textvariable=self.review_var,
                                         state="readonly")
        self.review_combo.pack(side=tk.LEFT, padx=5)
        self.review_combo.bind("<<ComboboxSelected>>", self.on_review_change)
        self.status_var = tk.StringVar()
        tk.Label(review_frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=5)
        self.desc_var = tk.StringVar()
        tk.Label(self, textvariable=self.desc_var, wraplength=400, justify="left").pack(fill=tk.X, padx=5)
        self.mod_var = tk.StringVar()
        tk.Label(self, textvariable=self.mod_var).pack(fill=tk.X, padx=5)
        self.due_var = tk.StringVar()
        tk.Label(self, textvariable=self.due_var).pack(fill=tk.X, padx=5)

        user_frame = tk.Frame(self)
        user_frame.pack(fill=tk.X)
        tk.Label(user_frame, text="Current user:").pack(side=tk.LEFT)
        self.user_var = tk.StringVar(value=app.current_user)
        self.user_combo = ttk.Combobox(user_frame, textvariable=self.user_var,
                                       state="readonly")
        self.user_combo.pack(side=tk.LEFT, padx=5)
        self.user_combo.bind("<<ComboboxSelected>>", self.on_user_change)

        target_frame = tk.Frame(self)
        target_frame.pack(fill=tk.X)
        tk.Label(target_frame, text="Target:").pack(side=tk.LEFT)
        self.target_var = tk.StringVar()
        self.target_combo = ttk.Combobox(target_frame, textvariable=self.target_var,
                                         state="readonly")
        self.target_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.target_combo.bind("<<ComboboxSelected>>", self.on_target_change)

        comment_frame = tk.Frame(self)
        comment_frame.pack(fill=tk.BOTH, expand=True)
        self.comment_list = tk.Listbox(comment_frame, width=50)
        c_scroll = tk.Scrollbar(comment_frame, orient=tk.VERTICAL,
                               command=self.comment_list.yview)
        self.comment_list.configure(yscrollcommand=c_scroll.set)
        self.comment_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        c_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.comment_list.bind("<<ListboxSelect>>", self.on_select)
        self.comment_list.bind("<Double-1>", self.open_comment)

        self.comment_display = tk.Text(self, height=4, state="disabled", wrap="word")
        self.comment_display.pack(fill=tk.X, padx=5, pady=5)

        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X)
        tk.Button(btn_frame, text="Add Comment", command=self.add_comment).pack(side=tk.LEFT)
        self.resolve_btn = tk.Button(btn_frame, text="Resolve", command=self.resolve_comment)
        self.resolve_btn.pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Mark Done", command=self.mark_done).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Open Document", command=self.open_document).pack(side=tk.LEFT)
        self.approve_btn = tk.Button(btn_frame, text="Approve", command=self.approve)
        self.approve_btn.pack(side=tk.LEFT)
        self.reject_btn = tk.Button(btn_frame, text="Reject", command=self.reject)
        self.reject_btn.pack(side=tk.LEFT)
        self.edit_btn = tk.Button(btn_frame, text="Edit Review", command=self.edit_review)
        self.edit_btn.pack(side=tk.LEFT)

        self.update_buttons()

        self.refresh_reviews()
        self.refresh_targets()
        self.refresh_comments()
        self.update_buttons()
        self.start_participant_timer()

    def on_close(self):
        self.app.review_window = None
        self.destroy()

    def refresh_reviews(self):
        self.app.update_hara_statuses()
        names = [r.name for r in self.app.reviews]
        self.review_combo['values'] = names
        if self.app.review_data:
            self.review_var.set(self.app.review_data.name)
            if self.app.review_data.approved:
                self.status_var.set("approved")
            elif self.app.review_data.reviewed:
                self.status_var.set("reviewed")
            else:
                self.status_var.set("open")
            self.desc_var.set(self.app.review_data.description)
            mods = ", ".join(m.name for m in self.app.review_data.moderators)
            self.mod_var.set(f"Moderators: {mods}")
            self.due_var.set(f"Due: {self.app.review_data.due_date}")
        else:
            self.review_var.set("")
            self.status_var.set("")
            self.desc_var.set("")
            self.mod_var.set("")
            self.due_var.set("")

    def on_review_change(self, event=None):
        name = self.review_var.get()
        for r in self.app.reviews:
            if r.name == name:
                self.app.review_data = r
                break
        if self.app.review_data:
            if self.app.review_data.approved:
                self.status_var.set("approved")
            elif self.app.review_data.reviewed:
                self.status_var.set("reviewed")
            else:
                self.status_var.set("open")
        else:
            self.status_var.set("open")
        if self.app.review_data:
            self.desc_var.set(self.app.review_data.description)
            mods = ", ".join(m.name for m in self.app.review_data.moderators)
            self.mod_var.set(f"Moderators: {mods}")
            self.due_var.set(f"Due: {self.app.review_data.due_date}")
        else:
            self.desc_var.set("")
            self.mod_var.set("")
            self.due_var.set("")
        self.refresh_comments()
        self.refresh_targets()
        self.update_buttons()
        self.start_participant_timer()
        try:
            if hasattr(self.app, "canvas") and self.app.canvas.winfo_exists():
                self.app.redraw_canvas()
        except tk.TclError:
            pass

    def refresh_comments(self):
        self.comment_list.delete(0, tk.END)
        if not self.app.review_data:
            return
        names = [p.name for p in self.app.review_data.participants]
        names.extend(m.name for m in self.app.review_data.moderators)
        self.user_combo['values'] = names
        if self.app.current_user:
            self.user_var.set(self.app.current_user)
        for c in self.app.review_data.comments:
            node = self.app.find_node_by_id_all(c.node_id)
            node_name = node.name if node else f"ID {c.node_id}"
            if c.target_type == "requirement" and c.req_id:
                node_name += f" [Req {c.req_id}]"
            elif c.target_type == "fmea":
                node_name += " [FMEA]"
            elif c.target_type == "fmea_field" and c.field:
                node_name += f" [FMEA {c.field}]"

            status = "(resolved)" if c.resolved else ""
        self.comment_list.insert(tk.END, f"{c.comment_id}: {node_name} - {c.reviewer} {status}")
        self.update_buttons()

    def start_participant_timer(self):
        if not self.app.review_data:
            return
        user = self.app.current_user
        for p in self.app.review_data.participants:
            if p.name == user and p.start_time == 0:
                p.start_time = time.time()
                break

    def on_select(self, event):
        if not self.app.review_data:
            return
        selection = self.comment_list.curselection()
        if selection:
            c = self.app.review_data.comments[selection[0]]
            node = self.app.find_node_by_id_all(c.node_id)
            if node:
                self.app.focus_on_node(node)
            self.show_comment(c)

    def add_comment(self):
        target = self.app.comment_target
        if not target:
            label = self.target_var.get()
            if label:
                target = self.target_map.get(label)
        if not target and not self.app.selected_node:
            messagebox.showwarning("Add Comment", "Select a node first")
            return
        if self.app.review_is_closed():
            messagebox.showwarning("Review", "This review is closed")
            return
        all_parts = self.app.review_data.participants + self.app.review_data.moderators
        dlg = UserSelectDialog(self, all_parts, initial_name=self.app.current_user)
        if not dlg.result:
            return
        reviewer, _ = dlg.result
        allowed = [p.name for p in all_parts]
        if reviewer not in allowed:
            messagebox.showerror("User", "Name not found in participants")
            return
        self.app.current_user = reviewer
        text = simpledialog.askstring("Comment", "Enter comment:")
        if not text:
            return
        comment_id = len(self.app.review_data.comments) + 1
        if target and target[0] == "requirement":
            node_id = target[1]
            req_id = target[2] if len(target) > 2 else ""
            c = ReviewComment(
                comment_id,
                node_id,
                text,
                reviewer,
                target_type="requirement",
                req_id=req_id,
            )
        elif target and target[0] == "fmea":
            node_id = target[1]
            c = ReviewComment(comment_id, node_id, text, reviewer, target_type="fmea")
        elif target and target[0] == "fmea_field":
            node_id = target[1]
            c = ReviewComment(comment_id, node_id, text, reviewer,
                             target_type="fmea_field", field=target[2])

        elif target and target[0] == "node":
            node_id = target[1]
            c = ReviewComment(comment_id, node_id, text, reviewer)
        else:
            c = ReviewComment(comment_id, self.app.selected_node.unique_id, text, reviewer)
        self.app.review_data.comments.append(c)
        self.app.comment_target = None
        self.refresh_comments()

    def resolve_comment(self):
        idx = self.comment_list.curselection()
        if not idx:
            return
        if self.app.review_is_closed():
            messagebox.showwarning("Review", "This review is closed")
            return
        if self.app.current_user not in [m.name for m in self.app.review_data.moderators]:
            messagebox.showerror("Resolve", "Only a moderator can resolve comments")
            return
        c = self.app.review_data.comments[idx[0]]
        resolution = simpledialog.askstring("Resolve Comment", "Enter resolution comment:")
        if resolution is None:
            return
        c.resolved = True
        c.resolution = resolution
        self.refresh_comments()
        self.check_completion()

    def mark_done(self):
        if self.app.review_is_closed():
            messagebox.showwarning("Review", "This review is closed")
            return
        user = self.app.current_user
        for p in self.app.review_data.participants:
            if p.name == user:
                if p.start_time:
                    p.time_spent = time.time() - p.start_time
                p.done = True
        messagebox.showinfo("Review", "Marked as done")
        self.update_buttons()
        self.check_completion()

    def approve(self):
        if self.app.review_is_closed():
            messagebox.showwarning("Review", "This review is closed")
            return
        if self.app.review_data.mode == 'joint':
            all_done = all(p.done for p in self.app.review_data.participants if p.role == 'reviewer')
            if not all_done:
                messagebox.showwarning("Approve", "Not all reviewers are done")
                return
        unresolved = [c for c in self.app.review_data.comments if not c.resolved]
        if unresolved:
            messagebox.showwarning("Approve", "There are unresolved comments")
            return
        user = self.app.current_user
        for p in self.app.review_data.participants:
            if p.name == user and p.role == 'approver':
                p.approved = True
                p.reject_reason = ""
                break
        messagebox.showinfo("Approve", "Approval recorded")
        self.check_completion()

    def reject(self):
        if self.app.review_is_closed():
            messagebox.showwarning("Review", "This review is closed")
            return
        user = self.app.current_user
        for p in self.app.review_data.participants:
            if p.name == user and p.role == 'approver':
                reason = simpledialog.askstring("Reject", "Enter rejection reason:")
                if reason is None:
                    return
                p.approved = False
                p.reject_reason = reason
                p.done = True
                break
        messagebox.showinfo("Reject", "Rejection recorded")
        self.check_completion()

    def edit_review(self):
        if not self.app.review_data:
            return
        if self.app.current_user not in [m.name for m in self.app.review_data.moderators]:
            messagebox.showerror("Edit", "Only a moderator can edit the review")
            return
        dialog = ParticipantDialog(
            self,
            self.app.review_data.mode == 'joint',
            initial_mods=self.app.review_data.moderators,
            initial_parts=self.app.review_data.participants,
        )
        if not dialog.result:
            return
        moderators, participants = dialog.result
        if not moderators:
            messagebox.showerror("Review", "At least one moderator required")
            return
        self.app.review_data.moderators = moderators
        self.app.review_data.participants = participants
        desc = askstring_fixed(
            simpledialog,
            "Description",
            "Edit description:",
            initialvalue=self.app.review_data.description,
        )
        if desc is not None:
            self.app.review_data.description = desc
        due = simpledialog.askstring("Due Date", "Edit due date (YYYY-MM-DD):", initialvalue=self.app.review_data.due_date)
        if due is not None:
            self.app.review_data.due_date = due
        self.refresh_reviews()
        self.refresh_comments()

    def open_document(self):
        if not self.app.review_data:
            messagebox.showwarning("Document", "No review selected")
            return
        self.app.open_review_document(self.app.review_data)

    def open_comment(self, event):
        selection = self.comment_list.curselection()
        if not selection:
            return
        c = self.app.review_data.comments[selection[0]]
        self.show_comment(c)

    def on_user_change(self, event):
        self.app.current_user = self.user_var.get()
        self.start_participant_timer()
        self.update_buttons()

    def show_comment(self, comment):
        self.comment_display.config(state="normal")
        self.comment_display.delete("1.0", tk.END)
        text = comment.text
        if comment.resolution:
            text += f"\n\nResolution: {comment.resolution}"
        self.comment_display.insert("1.0", text)
        self.comment_display.config(state="disabled")

    def update_buttons(self):
        role = None
        for p in (self.app.review_data.participants if self.app.review_data else []):
            if p.name == self.app.current_user:
                role = p.role
                break
        if (
            self.app.review_data
            and self.app.review_data.mode == 'joint'
            and role == 'approver'
            and not self.app.review_is_closed()
        ):
            self.approve_btn.pack(side=tk.LEFT)
            self.reject_btn.pack(side=tk.LEFT)
        else:
            self.approve_btn.pack_forget()
            self.reject_btn.pack_forget()
        if self.app.review_data and self.app.current_user in [m.name for m in self.app.review_data.moderators]:
            self.edit_btn.pack(side=tk.LEFT)
            if not self.app.review_is_closed():
                self.resolve_btn.pack(side=tk.LEFT)
            else:
                self.resolve_btn.pack_forget()
        else:
            self.resolve_btn.pack_forget()
            self.edit_btn.pack_forget()

    def check_completion(self):
        r = self.app.review_data
        if not r:
            return
        if r.mode == 'peer':
            if all(p.done for p in r.participants) and all(c.resolved for c in r.comments):
                r.closed = True
                r.reviewed = True
                self.app.update_hara_statuses()
                self.app.update_fta_statuses()
                self.app.update_requirement_statuses()
                if hasattr(self.app, "_risk_window") and self.app._risk_window.winfo_exists():
                    self.app._risk_window.refresh_docs()
                self.refresh_reviews()
        else:
            approvers = [p for p in r.participants if p.role == 'approver']
            if approvers and all(p.approved for p in approvers) and all(c.resolved for c in r.comments):
                was_closed = r.closed
                newly_approved = False
                if not r.approved:
                    r.approved = True
                    newly_approved = True
                r.closed = True
                if newly_approved:
                    self.app.add_version()
                self.app.update_hara_statuses()
                self.app.update_fta_statuses()
                self.app.update_requirement_statuses()
                if not was_closed and r.closed:
                    self.app.ensure_asil_consistency()
                    self.app.update_base_event_requirement_asil()
                if hasattr(self.app, "_risk_window") and self.app._risk_window.winfo_exists():
                    self.app._risk_window.refresh_docs()
                self.refresh_reviews()

    def refresh_targets(self):
        items, self.target_map = self.app.get_review_targets()
        self.target_combo['values'] = items
        if items:
            self.target_var.set(items[0])

    def on_target_change(self, event=None):
        label = self.target_var.get()
        target = self.target_map.get(label)
        self.app.comment_target = None
        if not target:
            return
        node = self.app.find_node_by_id_all(target[1]) if len(target) > 1 else None
        if node:
            self.app.selected_node = node
            self.app.focus_on_node(node)
        if target[0] == 'requirement':
            # store both node id and requirement id so add_comment can
            # create the ReviewComment correctly
            self.app.comment_target = ('requirement', target[1], target[2])
        elif target[0] == 'fmea':
            self.app.comment_target = ('fmea', target[1])

class ReviewDocumentDialog(tk.Frame):
    def __init__(self, master, app, review):
        super().__init__(master)
        self.app = app
        self.review = review
        # Use the drawing helper provided by the app or fall back to the global
        # helper retrieved from the running program.
        self.dh = getattr(app, 'fta_drawing_helper', None) or fta_drawing_helper
        if isinstance(master, tk.Toplevel):
            master.title(f"Review Document - {review.name}")
            master.resizable(True, True)

        container = tk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)

        self.outer = tk.Canvas(container)
        vbar = tk.Scrollbar(container, orient=tk.VERTICAL, command=self.outer.yview)
        hbar = tk.Scrollbar(container, orient=tk.HORIZONTAL, command=self.outer.xview)
        self.outer.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)
        self.outer.grid(row=0, column=0, sticky="nsew")
        vbar.grid(row=0, column=1, sticky="ns")
        hbar.grid(row=1, column=0, sticky="ew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        self.inner = tk.Frame(self.outer)
        self.inner_id = self.outer.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind(
            "<Configure>",
            lambda e: self.outer.configure(scrollregion=self.outer.bbox("all")),
        )
        self.outer.bind(
            "<Configure>",
            lambda e: self.outer.itemconfigure(self.inner_id, width=e.width),
        )
        self.inner.grid_columnconfigure(0, weight=1)
        self.images = []
        self.populate()

    def draw_tree(self, canvas, node, diff_nodes=None):
        def draw_connections(n):
            region_width = 100
            parent_bottom = (n.x, n.y + 40)
            for i, ch in enumerate(n.children):
                parent_conn = (
                    n.x - region_width / 2 + (i + 0.5) * (region_width / len(n.children)),
                    parent_bottom[1],
                )
                child_top = (ch.x, ch.y - 45)
                if self.dh:
                    color = "blue" if diff_nodes and ch.unique_id in diff_nodes else "dimgray"
                    self.dh.draw_90_connection(
                        canvas, parent_conn, child_top,
                        outline_color=color, line_width=1
                    )
                draw_connections(ch)

        def draw_node_simple(n):
            fill = self.app.get_node_fill_color(n, getattr(canvas, "diagram_mode", None))
            eff_x, eff_y = n.x, n.y
            top_text = n.node_type
            if n.input_subtype:
                top_text += f" ({n.input_subtype})"
            if n.description:
                top_text += f"\n{n.description}"
            bottom_text = n.name
            typ = n.node_type.upper()
            outline = "blue" if n.unique_id in self.diff_nodes else "dimgray"
            lw = 2 if n.unique_id in self.diff_nodes else 1
            if n.is_page:
                if self.dh:
                    self.dh.draw_triangle_shape(
                        canvas,
                        eff_x,
                        eff_y,
                        scale=40,
                        top_text=top_text,
                        bottom_text=bottom_text,
                        fill=fill,
                        outline_color="blue" if diff_nodes and n.unique_id in diff_nodes else "dimgray",
                        line_width=1,
                    )
            elif typ in ["GATE", "RIGOR LEVEL", "TOP EVENT"]:
                if n.gate_type and n.gate_type.upper() == "OR":
                    if self.dh:
                        self.dh.draw_rotated_or_gate_shape(
                            canvas,
                            eff_x,
                            eff_y,
                            scale=40,
                            top_text=top_text,
                            bottom_text=bottom_text,
                            fill=fill,
                            outline_color="blue" if diff_nodes and n.unique_id in diff_nodes else "dimgray",
                            line_width=1,
                        )
                else:
                    if self.dh:
                        self.dh.draw_rotated_and_gate_shape(
                            canvas,
                            eff_x,
                            eff_y,
                            scale=40,
                            top_text=top_text,
                            bottom_text=bottom_text,
                            fill=fill,
                            outline_color="blue" if diff_nodes and n.unique_id in diff_nodes else "dimgray",
                            line_width=1,
                        )
            else:
                if self.dh:
                    self.dh.draw_circle_event_shape(
                        canvas,
                        eff_x,
                        eff_y,
                        45,
                        top_text=top_text,
                        bottom_text=bottom_text,
                        fill=fill,
                        outline_color="blue" if diff_nodes and n.unique_id in diff_nodes else "dimgray",
                        line_width=1,
                    )

        def draw_all(n):
            draw_node_simple(n)
            for ch in n.children:
                draw_all(ch)

        canvas.delete("all")
        draw_connections(node)
        draw_all(node)
        canvas.config(scrollregion=canvas.bbox("all"))

    def diff_segments(self, old, new):
        matcher = difflib.SequenceMatcher(None, old, new)
        segments = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                segments.append((old[i1:i2], "black"))
            elif tag == "delete":
                segments.append((old[i1:i2], "red"))
            elif tag == "insert":
                segments.append((new[j1:j2], "blue"))
            elif tag == "replace":
                segments.append((old[i1:i2], "red"))
                segments.append((new[j1:j2], "blue"))
        return segments

    def insert_diff_text(self, widget, old, new):
        matcher = difflib.SequenceMatcher(None, old, new)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                widget.insert(tk.END, old[i1:i2])
            elif tag == "delete":
                widget.insert(tk.END, old[i1:i2], "removed")
            elif tag == "insert":
                widget.insert(tk.END, new[j1:j2], "added")
            elif tag == "replace":
                widget.insert(tk.END, old[i1:i2], "removed")
                widget.insert(tk.END, new[j1:j2], "added")

    def draw_segment_text(self, canvas, cx, cy, segments, font_obj):
        lines = [[]]
        for text, color in segments:
            parts = text.split("\n")
            for idx, part in enumerate(parts):
                if idx > 0:
                    lines.append([])
                lines[-1].append((part, color))
        line_height = font_obj.metrics("linespace")
        total_height = line_height * len(lines)
        start_y = cy - total_height / 2
        for line in lines:
            line_width = sum(font_obj.measure(part) for part, _ in line)
            start_x = cx - line_width / 2
            x = start_x
            for part, color in line:
                if part:
                    canvas.create_text(x, start_y, text=part, anchor="nw", fill=color, font=font_obj)
                    x += font_obj.measure(part)
            start_y += line_height

    def draw_diff_tree(self, canvas, roots, status, conn_status, node_objs, allow_ids, map1, map2):
        def draw_connections(n):
            if n.unique_id not in allow_ids:
                for ch in n.children:
                    draw_connections(ch)
                return
            region_width = 60
            parent_bottom = (n.x, n.y + 20)
            for i, ch in enumerate(n.children):
                if ch.unique_id not in allow_ids:
                    continue
                parent_conn = (
                    n.x - region_width / 2 + (i + 0.5) * (region_width / len(n.children)),
                    parent_bottom[1],
                )
                child_top = (ch.x, ch.y - 25)
                if self.dh:
                    edge_st = conn_status.get((n.unique_id, ch.unique_id), "existing")
                    if status.get(n.unique_id) == "removed" or status.get(ch.unique_id) == "removed":
                        edge_st = "removed"
                    color = "gray"
                    if edge_st == "added":
                        color = "blue"
                    elif edge_st == "removed":
                        color = "red"
                    self.dh.draw_90_connection(canvas, parent_conn, child_top, outline_color=color, line_width=1)
                draw_connections(ch)

        def draw_node(n):
            if n.unique_id not in allow_ids:
                for ch in n.children:
                    draw_node(ch)
                return
            st = status.get(n.unique_id, "existing")
            color = "dimgray"
            if st == "added":
                color = "blue"
            elif st == "removed":
                color = "red"

            source = n if getattr(n, "is_primary_instance", True) else getattr(n, "original", n)
            subtype_text = source.input_subtype if source.input_subtype else "N/A"
            display_label = source.display_label
            old_data = map1.get(n.unique_id)
            new_data = map2.get(n.unique_id)
            show_goal = source.node_type.upper() == "TOP EVENT"
            def req_lines(reqs):
                return "; ".join(
                    self.app.format_requirement_with_trace(r) for r in reqs
                )

            if old_data and new_data:
                desc_segments = [("Desc: ", "black")] + self.diff_segments(
                    old_data.get("description", ""),
                    new_data.get("description", ""),
                )
                rat_segments = [("Rationale: ", "black")] + self.diff_segments(
                    old_data.get("rationale", ""),
                    new_data.get("rationale", ""),
                )
                if show_goal:
                    sg_segments = [("SG: ", "black")] + self.diff_segments(
                        f"{old_data.get('safety_goal_description','')} [{old_data.get('safety_goal_asil','')}]",
                        f"{new_data.get('safety_goal_description','')} [{new_data.get('safety_goal_asil','')}]")
                    ss_segments = [("Safe State: ", "black")] + self.diff_segments(
                        old_data.get('safe_state', ''), new_data.get('safe_state', '')
                    )
                else:
                    sg_segments = []
                    ss_segments = []
                req_segments = [("Reqs: ", "black")] + self.diff_segments(
                    req_lines(old_data.get("safety_requirements", [])),
                    req_lines(new_data.get("safety_requirements", [])),
                )
            else:
                desc_segments = [("Desc: " + source.description, "black")]
                rat_segments = [("Rationale: " + source.rationale, "black")]
                if show_goal:
                    sg_segments = [(
                        "SG: " + f"{source.safety_goal_description} [{source.safety_goal_asil}]",
                        "black",
                    )]
                    ss_segments = [(
                        "Safe State: " + getattr(source, 'safe_state', ''),
                        "black",
                    )]
                else:
                    sg_segments = []
                    ss_segments = []
                req_segments = [
                    ("Reqs: " + req_lines(getattr(source, "safety_requirements", [])), "black")
                ]

            segments = [
                (f"Type: {source.node_type}\n", "black"),
                (f"Subtype: {subtype_text}\n", "black"),
                (f"{display_label}\n", "black"),
            ] + desc_segments + [("\n\n", "black")] + rat_segments
            if sg_segments:
                segments += [("\n\n", "black")] + sg_segments + [("\n\n", "black")] + ss_segments

            top_text = "".join(seg[0] for seg in segments)
            bottom_text = n.name
            fill = self.app.get_node_fill_color(n, getattr(canvas, "diagram_mode", None))
            eff_x, eff_y = n.x, n.y
            typ = n.node_type.upper()
            items_before = canvas.find_all()
            if typ in ["GATE", "RIGOR LEVEL", "TOP EVENT"]:
                if n.gate_type and n.gate_type.upper() == "OR":
                    if self.dh:
                        self.dh.draw_rotated_or_gate_shape(canvas, eff_x, eff_y, scale=40, top_text=top_text, bottom_text=bottom_text, fill=fill, outline_color=color, line_width=2)
                else:
                    if self.dh:
                        self.dh.draw_rotated_and_gate_shape(canvas, eff_x, eff_y, scale=40, top_text=top_text, bottom_text=bottom_text, fill=fill, outline_color=color, line_width=2)
            else:
                if self.dh:
                    self.dh.draw_circle_event_shape(canvas, eff_x, eff_y, 45, top_text=top_text, bottom_text=bottom_text, fill=fill, outline_color=color, line_width=2)

            items_after = canvas.find_all()
            text_id = None
            for item in items_after:
                if item in items_before:
                    continue
                if canvas.type(item) == "text" and canvas.itemcget(item, "text") == top_text:
                    text_id = item
                    break

            if text_id and any(c in ("red", "blue") for _, c in segments):
                bbox = canvas.bbox(text_id)
                cx = (bbox[0] + bbox[2]) / 2
                cy = (bbox[1] + bbox[3]) / 2
                canvas.itemconfigure(text_id, state="hidden")
                self.draw_segment_text(canvas, cx, cy, segments, self.app.diagram_font)
            for ch in n.children:
                draw_node(ch)

        canvas.delete("all")
        for r in roots:
            draw_connections(r)
            draw_node(r)

        existing_pairs = set()
        for p in node_objs.values():
            for ch in p.children:
                existing_pairs.add((p.unique_id, ch.unique_id))

        for (pid, cid), st in conn_status.items():
            if st != "removed":
                continue
            if (pid, cid) in existing_pairs:
                continue
            if pid in node_objs and cid in node_objs and pid in allow_ids and cid in allow_ids:
                parent = node_objs[pid]
                child = node_objs[cid]
                parent_pt = (parent.x, parent.y + 20)
                child_pt = (child.x, child.y - 25)
                if self.dh:
                    self.dh.draw_90_connection(canvas, parent_pt, child_pt, outline_color="red", line_width=1)

        canvas.config(scrollregion=canvas.bbox("all"))

    def populate(self):
        row = 0
        current = self.app.export_model_data(include_versions=False)
        base_data = (
            self.app.versions[-1]["data"]
            if self.app.versions
            else {"top_events": [], "fmeas": [], "fmedas": []}
        )

        def filter_data(data):
            return {
                "top_events": [
                    t
                    for t in data.get("top_events", [])
                    if t["unique_id"] in self.review.fta_ids
                ],
                "fmeas": [
                    f
                    for f in data.get("fmeas", [])
                    if f.get("name") in self.review.fmea_names
                ],
                "fmedas": [
                    d
                    for d in data.get("fmedas", [])
                    if d.get("name") in getattr(self.review, "fmeda_names", [])
                ],
                "hazops": [
                    d
                    for d in data.get("hazops", [])
                    if d.get("name") in getattr(self.review, "hazop_names", [])
                ],
                "haras": [
                    d
                    for d in data.get("haras", [])
                    if d.get("name") in getattr(self.review, "hara_names", [])
                ],
                "stpas": [
                    d
                    for d in data.get("stpas", [])
                    if d.get("name") in getattr(self.review, "stpa_names", [])
                ],
                "fi2tc_docs": [
                    d
                    for d in data.get("fi2tc_docs", [])
                    if d.get("name") in getattr(self.review, "fi2tc_names", [])
                ],
                "tc2fi_docs": [
                    d
                    for d in data.get("tc2fi_docs", [])
                    if d.get("name") in getattr(self.review, "tc2fi_names", [])
                ],
            }

        data1 = filter_data(base_data)
        data2 = filter_data(current)

        map1 = self.app.node_map_from_data(data1["top_events"])
        map2 = self.app.node_map_from_data(data2["top_events"])

        def build_conn_set(events):
            conns = set()
            def visit(d):
                for ch in d.get("children", []):
                    conns.add((d["unique_id"], ch["unique_id"]))
                    visit(ch)
            for t in events:
                visit(t)
            return conns

        conns1 = build_conn_set(data1["top_events"])
        conns2 = build_conn_set(data2["top_events"])

        conn_status = {}
        for c in conns1 | conns2:
            if c in conns1 and c not in conns2:
                conn_status[c] = "removed"
            elif c in conns2 and c not in conns1:
                conn_status[c] = "added"
            else:
                conn_status[c] = "existing"

        status = {}
        for nid in set(map1) | set(map2):
            if nid in map1 and nid not in map2:
                status[nid] = "removed"
            elif nid in map2 and nid not in map1:
                status[nid] = "added"
            else:
                if json.dumps(map1[nid], sort_keys=True) != json.dumps(map2[nid], sort_keys=True):
                    status[nid] = "added"
                else:
                    status[nid] = "existing"

        module = sys.modules.get(self.app.__class__.__module__)
        FaultTreeNodeCls = getattr(module, 'FaultTreeNode', None)
        if not FaultTreeNodeCls and self.app.top_events:
            FaultTreeNodeCls = type(self.app.top_events[0])

        new_roots = [FaultTreeNodeCls.from_dict(t) for t in data2["top_events"]]
        removed_ids = [nid for nid, st in status.items() if st == "removed"]
        for rid in removed_ids:
            if rid in map1:
                nd = map1[rid]
                new_roots.append(FaultTreeNodeCls.from_dict(nd))

        relevant_ids = set()
        def collect_ids(d):
            relevant_ids.add(d["unique_id"])
            for ch in d.get("children", []):
                collect_ids(ch)
        for t in data1["top_events"]:
            collect_ids(t)
        for t in data2["top_events"]:
            collect_ids(t)

        node_objs = {}
        def collect_nodes(n):
            if n.unique_id not in node_objs:
                node_objs[n.unique_id] = n
            for ch in n.children:
                collect_nodes(ch)
        for rnode in new_roots:
            collect_nodes(rnode)

        old_fmea = {
            f["name"]: {e["unique_id"]: e for e in f.get("entries", [])}
            for f in data1.get("fmeas", [])
        }
        new_fmea = {
            f["name"]: {e["unique_id"]: e for e in f.get("entries", [])}
            for f in data2.get("fmeas", [])
        }
        old_fmeda = {d["name"]: d.get("entries", []) for d in data1.get("fmedas", [])}
        new_fmeda = {d["name"]: d.get("entries", []) for d in data2.get("fmedas", [])}
        old_hazop = {d["name"]: d.get("entries", []) for d in data1.get("hazops", [])}
        new_hazop = {d["name"]: d.get("entries", []) for d in data2.get("hazops", [])}
        old_hara = {d["name"]: d.get("entries", []) for d in data1.get("haras", [])}
        new_hara = {d["name"]: d.get("entries", []) for d in data2.get("haras", [])}
        old_stpa = {d["name"]: d.get("entries", []) for d in data1.get("stpas", [])}
        new_stpa = {d["name"]: d.get("entries", []) for d in data2.get("stpas", [])}
        old_fi2tc = {d["name"]: d.get("entries", []) for d in data1.get("fi2tc_docs", [])}
        new_fi2tc = {d["name"]: d.get("entries", []) for d in data2.get("fi2tc_docs", [])}
        old_tc2fi = {d["name"]: d.get("entries", []) for d in data1.get("tc2fi_docs", [])}
        new_tc2fi = {d["name"]: d.get("entries", []) for d in data2.get("tc2fi_docs", [])}

        reqs1 = {}
        reqs2 = {}

        def collect_reqs(node_dict, target):
            for r in node_dict.get("safety_requirements", []):
                rid = r.get("id")
                if rid and rid not in target:
                    target[rid] = r
            for ch in node_dict.get("children", []):
                collect_reqs(ch, target)

        for nid in self.review.fta_ids:
            if nid in map1:
                collect_reqs(map1[nid], reqs1)
            if nid in map2:
                collect_reqs(map2[nid], reqs2)

        for name in self.review.fmea_names:
            for e in old_fmea.get(name, {}).values():
                for r in e.get("safety_requirements", []):
                    rid = r.get("id")
                    if rid and rid not in reqs1:
                        reqs1[rid] = r
            for e in new_fmea.get(name, {}).values():
                for r in e.get("safety_requirements", []):
                    rid = r.get("id")
                    if rid and rid not in reqs2:
                        reqs2[rid] = r
        for name in getattr(self.review, "fmeda_names", []):
            for e in old_fmeda.get(name, []):
                for r in e.get("safety_requirements", []):
                    rid = r.get("id")
                    if rid and rid not in reqs1:
                        reqs1[rid] = r
            for e in new_fmeda.get(name, []):
                for r in e.get("safety_requirements", []):
                    rid = r.get("id")
                    if rid and rid not in reqs2:
                        reqs2[rid] = r

        heading_font = ("TkDefaultFont", 10, "bold")
        for nid in self.review.fta_ids:
            node = self.app.find_node_by_id_all(nid)
            if not node:
                continue
            tk.Label(self.inner, text=f"FTA: {node.name}", font=heading_font).grid(row=row, column=0, sticky="w", padx=5, pady=5)
            row += 1
            frame = tk.Frame(self.inner)
            frame.grid(row=row, column=0, padx=5, pady=5, sticky="nsew")
            c = tk.Canvas(
                frame,
                width=600,
                height=400,
                bg=StyleManager.get_instance().canvas_bg,
            )
            hbar = tk.Scrollbar(frame, orient=tk.HORIZONTAL, command=c.xview)
            vbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=c.yview)
            c.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
            c.grid(row=0, column=0, sticky="nsew")
            vbar.grid(row=0, column=1, sticky="ns")
            hbar.grid(row=1, column=0, sticky="ew")
            frame.rowconfigure(0, weight=1)
            frame.columnconfigure(0, weight=1)
            c.bind("<ButtonPress-1>", lambda e, cv=c: cv.scan_mark(e.x, e.y))
            c.bind("<B1-Motion>", lambda e, cv=c: cv.scan_dragto(e.x, e.y, gain=1))

            img = self.app.capture_diff_diagram(node)
            if img and Image and ImageTk:
                img = img.resize((img.width // 2, img.height // 2), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.images.append(photo)
                c.create_image(0, 0, image=photo, anchor="nw")
                c.config(scrollregion=(0, 0, img.width, img.height))
            row += 1
        for name in self.review.fmea_names:
            cur_fmea = next((f for f in data2.get("fmeas", []) if f["name"] == name), None)
            if not cur_fmea and name not in old_fmea:
                continue
            tk.Label(self.inner, text=f"FMEA: {name}", font=heading_font).grid(row=row, column=0, sticky="w", padx=5, pady=5)
            row += 1
            frame = tk.Frame(self.inner)
            frame.grid(row=row, column=0, sticky="nsew", padx=5, pady=5)
            columns = [
                "Component",
                "Parent",
                "Failure Mode",
                "Failure Effect",
                "Cause",
                "S",
                "O",
                "D",
                "RPN",
                "Requirements",
            ]
            tree = ttk.Treeview(frame, columns=columns, show="headings", height=8)
            vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
            hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
            for col in columns:
                tree.heading(col, text=col)
                width = 100
                if col in ["Failure Effect", "Cause", "Requirements"]:
                    width = 180
                tree.column(col, width=width, anchor="center")
            tree.grid(row=0, column=0, sticky="nsew")
            vsb.grid(row=0, column=1, sticky="ns")
            hsb.grid(row=1, column=0, sticky="ew")
            frame.grid_columnconfigure(0, weight=1)
            frame.grid_rowconfigure(0, weight=1)

            tree.tag_configure("added", background="#cce5ff")
            tree.tag_configure("removed", background="#f8d7da")
            tree.tag_configure("existing", background="#e2e3e5")

            entries1 = old_fmea.get(name, {})
            entries2 = {e["unique_id"]: e for e in (cur_fmea.get("entries", []) if cur_fmea else [])}

            for uid in set(entries1) | set(entries2):
                if uid in entries1 and uid not in entries2:
                    st = "removed"
                    entry = entries1[uid]
                elif uid in entries2 and uid not in entries1:
                    st = "added"
                    entry = entries2[uid]
                else:
                    if json.dumps(entries1[uid], sort_keys=True) != json.dumps(entries2[uid], sort_keys=True):
                        st = "added"
                        entry = entries2[uid]
                    else:
                        st = "existing"
                        entry = entries2[uid]

                parent = entry.get("parents", [{}])
                parent = parent[0] if parent else {}
                if parent and parent.get("node_type", "").upper() not in GATE_NODE_TYPES and parent.get("user_name"):
                    comp = parent.get("user_name")
                    parent_name = parent.get("user_name")
                else:
                    comp = entry.get("fmea_component", "") or "N/A"
                    parent_name = ""
                rpn = int(entry.get("fmea_severity", 1)) * int(entry.get("fmea_occurrence", 1)) * int(entry.get("fmea_detection", 1))
                req_ids = "; ".join(
                    f"{r.get('req_type', '')}:{r.get('text', '')}"
                    for r in entry.get("safety_requirements", [])
                )
                failure_mode = entry.get("description") or entry.get("user_name", f"BE {uid}")
                vals = [
                    comp,
                    parent_name,
                    failure_mode,
                    entry.get("fmea_effect", ""),
                    entry.get("fmea_cause", ""),
                    entry.get("fmea_severity", ""),
                    entry.get("fmea_occurrence", ""),
                    entry.get("fmea_detection", ""),
                    rpn,
                    req_ids,
                ]
                tree.insert("", "end", values=vals, tags=(st,))

        row += 1
        for name in getattr(self.review, 'hazop_names', []):
            old_entries = old_hazop.get(name, [])
            new_entries = new_hazop.get(name, [])
            if not old_entries and not new_entries:
                continue
            tk.Label(self.inner, text=f"HAZOP: {name}", font=heading_font).grid(row=row, column=0, sticky='w', padx=5, pady=5)
            row += 1
            frame = tk.Frame(self.inner)
            frame.grid(row=row, column=0, sticky='nsew', padx=5, pady=5)
            columns = ("function","malfunction","type","scenario","conditions","hazard","safety","rationale","covered","covered_by")
            tree = ttk.Treeview(frame, columns=columns, show='headings', height=8)
            vsb = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
            hsb = ttk.Scrollbar(frame, orient='horizontal', command=tree.xview)
            tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=100, anchor='center')
            tree.grid(row=0, column=0, sticky='nsew')
            vsb.grid(row=0, column=1, sticky='ns')
            hsb.grid(row=1, column=0, sticky='ew')
            frame.grid_columnconfigure(0, weight=1)
            frame.grid_rowconfigure(0, weight=1)
            for e in new_entries:
                vals = [e.get("function",""), e.get("malfunction",""), e.get("mtype",""), e.get("scenario",""), e.get("conditions",""), e.get("hazard",""), "Yes" if e.get("safety") else "No", e.get("rationale",""), "Yes" if e.get("covered") else "No", e.get("covered_by","")]
                tree.insert("", "end", values=vals)
        for name in getattr(self.review, 'hara_names', []):
            old_entries = old_hara.get(name, [])
            new_entries = new_hara.get(name, [])
            if not old_entries and not new_entries:
                continue
            tk.Label(self.inner, text=f"Risk Assessment: {name}", font=heading_font).grid(row=row, column=0, sticky='w', padx=5, pady=5)
            row += 1
            frame = tk.Frame(self.inner)
            frame.grid(row=row, column=0, sticky='nsew', padx=5, pady=5)
            columns = ("malfunction","hazard","severity","sev_rationale","controllability","cont_rationale","exposure","exp_rationale","asil","safety_goal")
            tree = ttk.Treeview(frame, columns=columns, show='headings', height=8)
            vsb = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
            hsb = ttk.Scrollbar(frame, orient='horizontal', command=tree.xview)
            tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=100, anchor='center')
            tree.grid(row=0, column=0, sticky='nsew')
            vsb.grid(row=0, column=1, sticky='ns')
            hsb.grid(row=1, column=0, sticky='ew')
            frame.grid_columnconfigure(0, weight=1)
            frame.grid_rowconfigure(0, weight=1)
            for e in new_entries:
                vals = [e.get("malfunction",""), e.get("hazard",""), e.get("severity",""), e.get("sev_rationale",""), e.get("controllability",""), e.get("cont_rationale",""), e.get("exposure",""), e.get("exp_rationale",""), e.get("asil",""), e.get("safety_goal","")]
                tree.insert("", "end", values=vals)
        for name in getattr(self.review, 'stpa_names', []):
            old_entries = old_stpa.get(name, [])
            new_entries = new_stpa.get(name, [])
            if not old_entries and not new_entries:
                continue
            tk.Label(self.inner, text=f"STPA: {name}", font=heading_font).grid(row=row, column=0, sticky='w', padx=5, pady=5)
            row += 1
            frame = tk.Frame(self.inner)
            frame.grid(row=row, column=0, sticky='nsew', padx=5, pady=5)
            columns = ("action","not_providing","providing","incorrect_timing","stopped_too_soon","safety_constraints")
            tree = ttk.Treeview(frame, columns=columns, show='headings', height=8)
            vsb = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
            hsb = ttk.Scrollbar(frame, orient='horizontal', command=tree.xview)
            tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
            for col in columns:
                head = "Control Action" if col == "action" else col.replace('_',' ').title()
                tree.heading(col, text=head)
                tree.column(col, width=150, anchor='center')
            tree.grid(row=0, column=0, sticky='nsew')
            vsb.grid(row=0, column=1, sticky='ns')
            hsb.grid(row=1, column=0, sticky='ew')
            frame.grid_columnconfigure(0, weight=1)
            frame.grid_rowconfigure(0, weight=1)
            for e in new_entries:
                vals = [e.get(k, "") if k != "safety_constraints" else "; ".join(e.get(k, [])) for k in columns]
                tree.insert("", "end", values=vals)
        for name in getattr(self.review, 'fi2tc_names', []):
            old_entries = old_fi2tc.get(name, [])
            new_entries = new_fi2tc.get(name, [])
            if not old_entries and not new_entries:
                continue
            tk.Label(self.inner, text=f"FI2TC: {name}", font=heading_font).grid(row=row, column=0, sticky='w', padx=5, pady=5)
            row += 1
            frame = tk.Frame(self.inner)
            frame.grid(row=row, column=0, sticky='nsew', padx=5, pady=5)
            columns = ("id","system_function","allocation","interfaces","functional_insufficiencies","scene","scenario","driver_behavior","occurrence","vehicle_effect","severity","design_measures","verification","measure_effectiveness","triggering_conditions","mitigation","acceptance")
            tree = ttk.Treeview(frame, columns=columns, show='headings', height=8)
            vsb = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
            hsb = ttk.Scrollbar(frame, orient='horizontal', command=tree.xview)
            tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
            for col in columns:
                tree.heading(col, text=col.replace('_',' ').title())
                tree.column(col, width=120, anchor='center')
            tree.grid(row=0, column=0, sticky='nsew')
            vsb.grid(row=0, column=1, sticky='ns')
            hsb.grid(row=1, column=0, sticky='ew')
            frame.grid_columnconfigure(0, weight=1)
            frame.grid_rowconfigure(0, weight=1)
            for e in new_entries:
                vals = [e.get(k, "") for k in columns]
                tree.insert("", "end", values=vals)
        for name in getattr(self.review, 'tc2fi_names', []):
            old_entries = old_tc2fi.get(name, [])
            new_entries = new_tc2fi.get(name, [])
            if not old_entries and not new_entries:
                continue
            tk.Label(self.inner, text=f"TC2FI: {name}", font=heading_font).grid(row=row, column=0, sticky='w', padx=5, pady=5)
            row += 1
            frame = tk.Frame(self.inner)
            frame.grid(row=row, column=0, sticky='nsew', padx=5, pady=5)
            columns = ("id","known_use_case","occurrence","impacted_function","arch_elements","interfaces","functional_insufficiencies","vehicle_effect","severity","design_measures","verification","measure_effectiveness","scene","scenario","driver_behavior","triggering_conditions","mitigation","acceptance")
            tree = ttk.Treeview(frame, columns=columns, show='headings', height=8)
            vsb = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
            hsb = ttk.Scrollbar(frame, orient='horizontal', command=tree.xview)
            tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
            for col in columns:
                tree.heading(col, text=col.replace('_',' ').title())
                tree.column(col, width=120, anchor='center')
            tree.grid(row=0, column=0, sticky='nsew')
            vsb.grid(row=0, column=1, sticky='ns')
            hsb.grid(row=1, column=0, sticky='ew')
            frame.grid_columnconfigure(0, weight=1)
            frame.grid_rowconfigure(0, weight=1)
            for e in new_entries:
                vals = [e.get(k, "") for k in columns]
                tree.insert("", "end", values=vals)

        row += 1

        if reqs1 or reqs2:
            tk.Label(self.inner, text="Requirements", font=heading_font).grid(row=row, column=0, sticky="w", padx=5, pady=5)
            row += 1
            frame = tk.Frame(self.inner)
            frame.grid(row=row, column=0, sticky="nsew", padx=5, pady=5)
            vbar = tk.Scrollbar(frame, orient="vertical")
            text = tk.Text(frame, wrap="word", yscrollcommand=vbar.set, height=8)
            text.tag_configure("added", foreground="blue")
            text.tag_configure("removed", foreground="red")
            vbar.config(command=text.yview)
            text.grid(row=0, column=0, sticky="nsew")
            vbar.grid(row=0, column=1, sticky="ns")
            frame.grid_columnconfigure(0, weight=1)
            frame.grid_rowconfigure(0, weight=1)

            def fmt(r):
                return self.app.format_requirement_with_trace(r)

            all_ids = sorted(set(reqs1) | set(reqs2))
            for rid in all_ids:
                r1 = reqs1.get(rid)
                r2 = reqs2.get(rid)
                if r1 and not r2:
                    text.insert(tk.END, f"Removed: ")
                    self.insert_diff_text(text, fmt(r1), "")
                elif r2 and not r1:
                    text.insert(tk.END, f"Added: ")
                    self.insert_diff_text(text, "", fmt(r2))
                else:
                    if json.dumps(r1, sort_keys=True) != json.dumps(r2, sort_keys=True):
                        text.insert(tk.END, f"Updated: ")
                        self.insert_diff_text(text, fmt(r1), fmt(r2))
                    else:
                        text.insert(tk.END, fmt(r2))
                text.insert(tk.END, "\n")

            for nid in self.review.fta_ids:
                n1 = map1.get(nid, {})
                n2 = map2.get(nid, {})
                node_type = (n2.get('type') or n1.get('type', '')).upper()
                sg_old = f"{n1.get('safety_goal_description','')} [{n1.get('safety_goal_asil','')}]"
                sg_new = f"{n2.get('safety_goal_description','')} [{n2.get('safety_goal_asil','')}]"
                label = n2.get('user_name') or n1.get('user_name') or f"Node {nid}"
                if node_type == 'TOP EVENT':
                    if sg_old != sg_new:
                        text.insert(tk.END, f"Safety Goal for {label}: ")
                        self.insert_diff_text(text, sg_old, sg_new)
                        text.insert(tk.END, "\n")
                    if n1.get('safe_state','') != n2.get('safe_state',''):
                        text.insert(tk.END, f"Safe State for {label}: ")
                        self.insert_diff_text(text, n1.get('safe_state',''), n2.get('safe_state',''))
                        text.insert(tk.END, "\n")

            row += 1

class VersionCompareDialog(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        if isinstance(master, tk.Toplevel):
            master.title("Compare Versions")
            master.protocol("WM_DELETE_WINDOW", self.on_close)
            master.resizable(True, True)

        names = [v["name"] for v in self.app.versions]
        tk.Label(self, text="Base version:").pack(padx=5, pady=2)
        self.base_var = tk.StringVar()
        self.base_combo = ttk.Combobox(self, values=names, textvariable=self.base_var, state="readonly")
        self.base_combo.pack(fill=tk.X, padx=5)
        self.base_combo.bind("<<ComboboxSelected>>", self.compare)

        tk.Label(self, text="Compare with:").pack(padx=5, pady=2)
        self.other_var = tk.StringVar()
        self.other_combo = ttk.Combobox(self, values=names, textvariable=self.other_var, state="readonly")
        self.other_combo.pack(fill=tk.X, padx=5)
        self.other_combo.bind("<<ComboboxSelected>>", self.compare)

        # canvas to display FTA differences
        canvas_frame = tk.Frame(self)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tree_canvas = tk.Canvas(
            canvas_frame,
            width=600,
            height=300,
            bg=StyleManager.get_instance().canvas_bg,
        )
        vbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.tree_canvas.yview)
        hbar = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.tree_canvas.xview)
        self.tree_canvas.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)
        self.tree_canvas.grid(row=0, column=0, sticky="nsew")
        vbar.grid(row=0, column=1, sticky="ns")
        hbar.grid(row=1, column=0, sticky="ew")
        canvas_frame.rowconfigure(0, weight=1)
        canvas_frame.columnconfigure(0, weight=1)

        # table for FMEA differences - mimic the full FMEA table
        columns = [
            "FMEA",
            "Component",
            "Parent",
            "Failure Mode",
            "Failure Effect",
            "Cause",
            "S",
            "O",
            "D",
            "RPN",
            "Requirements",
        ]
        fmea_frame = tk.Frame(self)
        fmea_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.fmea_tree = ttk.Treeview(fmea_frame, columns=columns, show="headings")
        for col in columns:
            self.fmea_tree.heading(col, text=col)
            width = 120
            if col in ["Failure Effect", "Cause", "Requirements"]:
                width = 180
            elif col == "Parent":
                width = 150
            self.fmea_tree.column(col, width=width, anchor="center")
        vsb_fmea = ttk.Scrollbar(fmea_frame, orient="vertical", command=self.fmea_tree.yview)
        hsb_fmea = ttk.Scrollbar(fmea_frame, orient="horizontal", command=self.fmea_tree.xview)
        self.fmea_tree.configure(yscrollcommand=vsb_fmea.set, xscrollcommand=hsb_fmea.set)
        self.fmea_tree.grid(row=0, column=0, sticky="nsew")
        vsb_fmea.grid(row=0, column=1, sticky="ns")
        hsb_fmea.grid(row=1, column=0, sticky="ew")
        fmea_frame.rowconfigure(0, weight=1)
        fmea_frame.columnconfigure(0, weight=1)
        self.fmea_tree.tag_configure("added", background="#cce5ff")
        self.fmea_tree.tag_configure("removed", background="#f8d7da")
        self.fmea_tree.tag_configure("existing", background="#e2e3e5")

        columns_fmeda = [
            "FMEDA","Component","Parent","Failure Mode","Malfunction","Safety Goal","FaultType","Fraction","FIT","DiagCov","Mechanism"
        ]
        fmeda_frame = tk.Frame(self)
        fmeda_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.fmeda_tree = ttk.Treeview(fmeda_frame, columns=columns_fmeda, show="headings")
        for col in columns_fmeda:
            self.fmeda_tree.heading(col, text=col)
            width = 100
            if col in ["Malfunction","Safety Goal"]:
                width = 150
            self.fmeda_tree.column(col, width=width, anchor="center")
        vsb_fmeda = ttk.Scrollbar(fmeda_frame, orient="vertical", command=self.fmeda_tree.yview)
        hsb_fmeda = ttk.Scrollbar(fmeda_frame, orient="horizontal", command=self.fmeda_tree.xview)
        self.fmeda_tree.configure(yscrollcommand=vsb_fmeda.set, xscrollcommand=hsb_fmeda.set)
        self.fmeda_tree.grid(row=0, column=0, sticky="nsew")
        vsb_fmeda.grid(row=0, column=1, sticky="ns")
        hsb_fmeda.grid(row=1, column=0, sticky="ew")
        fmeda_frame.rowconfigure(0, weight=1)
        fmeda_frame.columnconfigure(0, weight=1)
        self.fmeda_tree.tag_configure("added", background="#cce5ff")
        self.fmeda_tree.tag_configure("removed", background="#f8d7da")
        self.fmeda_tree.tag_configure("existing", background="#e2e3e5")

        columns_hazop = [
            "HAZOP",
            "Function",
            "Malfunction",
            "Type",
            "Scenario",
            "Conditions",
            "Hazard",
            "Safety",
            "Rationale",
            "Covered",
            "Covered By",
        ]
        hazop_frame = tk.Frame(self)
        hazop_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.hazop_tree = ttk.Treeview(hazop_frame, columns=columns_hazop, show="headings")
        for col in columns_hazop:
            self.hazop_tree.heading(col, text=col)
            width = 100
            if col in ["Function", "Malfunction", "Scenario", "Rationale"]:
                width = 150
            self.hazop_tree.column(col, width=width, anchor="center")
        vsb_hazop = ttk.Scrollbar(hazop_frame, orient="vertical", command=self.hazop_tree.yview)
        hsb_hazop = ttk.Scrollbar(hazop_frame, orient="horizontal", command=self.hazop_tree.xview)
        self.hazop_tree.configure(yscrollcommand=vsb_hazop.set, xscrollcommand=hsb_hazop.set)
        self.hazop_tree.grid(row=0, column=0, sticky="nsew")
        vsb_hazop.grid(row=0, column=1, sticky="ns")
        hsb_hazop.grid(row=1, column=0, sticky="ew")
        hazop_frame.rowconfigure(0, weight=1)
        hazop_frame.columnconfigure(0, weight=1)
        self.hazop_tree.tag_configure("added", background="#cce5ff")
        self.hazop_tree.tag_configure("removed", background="#f8d7da")
        self.hazop_tree.tag_configure("existing", background="#e2e3e5")

        columns_hara = [
            "Assessment",
            "Malfunction",
            "Hazard",
            "Severity",
            "Sev Rationale",
            "Controllability",
            "Cont Rationale",
            "Exposure",
            "Exp Rationale",
            "ASIL",
            "Safety Goal",
        ]
        hara_frame = tk.Frame(self)
        hara_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.hara_tree = ttk.Treeview(hara_frame, columns=columns_hara, show="headings")
        for col in columns_hara:
            self.hara_tree.heading(col, text=col)
            width = 100
            if col in ["Malfunction", "Hazard", "Sev Rationale", "Cont Rationale", "Exp Rationale", "Safety Goal"]:
                width = 150
            self.hara_tree.column(col, width=width, anchor="center")
        vsb_hara = ttk.Scrollbar(hara_frame, orient="vertical", command=self.hara_tree.yview)
        hsb_hara = ttk.Scrollbar(hara_frame, orient="horizontal", command=self.hara_tree.xview)
        self.hara_tree.configure(yscrollcommand=vsb_hara.set, xscrollcommand=hsb_hara.set)
        self.hara_tree.grid(row=0, column=0, sticky="nsew")
        vsb_hara.grid(row=0, column=1, sticky="ns")
        hsb_hara.grid(row=1, column=0, sticky="ew")
        hara_frame.rowconfigure(0, weight=1)
        hara_frame.columnconfigure(0, weight=1)
        self.hara_tree.tag_configure("added", background="#cce5ff")
        self.hara_tree.tag_configure("removed", background="#f8d7da")
        self.hara_tree.tag_configure("existing", background="#e2e3e5")

        columns_stpa = [
            "STPA",
            "Action",
            "Not Providing",
            "Providing",
            "Incorrect Timing",
            "Stopped Too Soon",
            "Safety Constraints",
        ]
        stpa_frame = tk.Frame(self)
        stpa_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.stpa_tree = ttk.Treeview(stpa_frame, columns=columns_stpa, show="headings")
        for col in columns_stpa:
            self.stpa_tree.heading(col, text=col)
            width = 150 if col == "Safety Constraints" else 120
            self.stpa_tree.column(col, width=width, anchor="center")
        vsb_stpa = ttk.Scrollbar(stpa_frame, orient="vertical", command=self.stpa_tree.yview)
        hsb_stpa = ttk.Scrollbar(stpa_frame, orient="horizontal", command=self.stpa_tree.xview)
        self.stpa_tree.configure(yscrollcommand=vsb_stpa.set, xscrollcommand=hsb_stpa.set)
        self.stpa_tree.grid(row=0, column=0, sticky="nsew")
        vsb_stpa.grid(row=0, column=1, sticky="ns")
        hsb_stpa.grid(row=1, column=0, sticky="ew")
        stpa_frame.rowconfigure(0, weight=1)
        stpa_frame.columnconfigure(0, weight=1)
        self.stpa_tree.tag_configure("added", background="#cce5ff")
        self.stpa_tree.tag_configure("removed", background="#f8d7da")
        self.stpa_tree.tag_configure("existing", background="#e2e3e5")

        columns_fi2tc = [
            "FI2TC",
            "System Function",
            "Allocation",
            "Interfaces",
            "Functional Insufficiencies",
            "Scene",
            "Scenario",
            "Driver Behavior",
            "Occurrence",
            "Vehicle Effect",
            "Severity",
            "Design Measures",
            "Verification",
            "Measure Effectiveness",
            "Triggering Conditions",
            "Mitigation",
            "Acceptance",
        ]
        fi2tc_frame = tk.Frame(self)
        fi2tc_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.fi2tc_tree = ttk.Treeview(fi2tc_frame, columns=columns_fi2tc, show="headings")
        for col in columns_fi2tc:
            self.fi2tc_tree.heading(col, text=col)
            self.fi2tc_tree.column(col, width=120, anchor="center")
        vsb_fi2tc = ttk.Scrollbar(fi2tc_frame, orient="vertical", command=self.fi2tc_tree.yview)
        hsb_fi2tc = ttk.Scrollbar(fi2tc_frame, orient="horizontal", command=self.fi2tc_tree.xview)
        self.fi2tc_tree.configure(yscrollcommand=vsb_fi2tc.set, xscrollcommand=hsb_fi2tc.set)
        self.fi2tc_tree.grid(row=0, column=0, sticky="nsew")
        vsb_fi2tc.grid(row=0, column=1, sticky="ns")
        hsb_fi2tc.grid(row=1, column=0, sticky="ew")
        fi2tc_frame.rowconfigure(0, weight=1)
        fi2tc_frame.columnconfigure(0, weight=1)
        self.fi2tc_tree.tag_configure("added", background="#cce5ff")
        self.fi2tc_tree.tag_configure("removed", background="#f8d7da")
        self.fi2tc_tree.tag_configure("existing", background="#e2e3e5")

        columns_tc2fi = [
            "TC2FI",
            "Known Use Case",
            "Occurrence",
            "Impacted Function",
            "Arch Elements",
            "Interfaces",
            "Functional Insufficiencies",
            "Vehicle Effect",
            "Severity",
            "Design Measures",
            "Verification",
            "Measure Effectiveness",
            "Scene",
            "Scenario",
            "Driver Behavior",
            "Triggering Conditions",
            "Mitigation",
            "Acceptance",
        ]
        tc2fi_frame = tk.Frame(self)
        tc2fi_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tc2fi_tree = ttk.Treeview(tc2fi_frame, columns=columns_tc2fi, show="headings")
        for col in columns_tc2fi:
            self.tc2fi_tree.heading(col, text=col)
            self.tc2fi_tree.column(col, width=120, anchor="center")
        vsb_tc2fi = ttk.Scrollbar(tc2fi_frame, orient="vertical", command=self.tc2fi_tree.yview)
        hsb_tc2fi = ttk.Scrollbar(tc2fi_frame, orient="horizontal", command=self.tc2fi_tree.xview)
        self.tc2fi_tree.configure(yscrollcommand=vsb_tc2fi.set, xscrollcommand=hsb_tc2fi.set)
        self.tc2fi_tree.grid(row=0, column=0, sticky="nsew")
        vsb_tc2fi.grid(row=0, column=1, sticky="ns")
        hsb_tc2fi.grid(row=1, column=0, sticky="ew")
        tc2fi_frame.rowconfigure(0, weight=1)
        tc2fi_frame.columnconfigure(0, weight=1)
        self.tc2fi_tree.tag_configure("added", background="#cce5ff")
        self.tc2fi_tree.tag_configure("removed", background="#f8d7da")
        self.tc2fi_tree.tag_configure("existing", background="#e2e3e5")

        # box for requirement changes similar to ReviewDocument
        req_frame = tk.Frame(self)
        req_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        tk.Label(req_frame, text="Requirements").pack(anchor="w")
        vbar_req = tk.Scrollbar(req_frame, orient=tk.VERTICAL)
        self.req_text = tk.Text(
            req_frame,
            wrap="word",
            yscrollcommand=vbar_req.set,
            height=8,
        )
        vbar_req.config(command=self.req_text.yview)
        vbar_req.pack(side=tk.RIGHT, fill=tk.Y)
        self.req_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.req_text.tag_configure("added", foreground="blue")
        self.req_text.tag_configure("removed", foreground="red")

        # text box for detailed log of changes
        log_frame = tk.Frame(self)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        vbar_log = tk.Scrollbar(log_frame, orient=tk.VERTICAL)
        self.log_line_numbers = tk.Text(
            log_frame,
            width=4,
            padx=4,
            takefocus=0,
            fg="white",
            bg="black",
            yscrollcommand=vbar_log.set,
            state="disabled",
        )
        self.log_text = tk.Text(
            log_frame,
            wrap="word",
            yscrollcommand=lambda *args: (
                vbar_log.set(*args),
                self.log_line_numbers.yview_moveto(args[0]),
            ),
            height=8,
        )
        vbar_log.config(
            command=lambda *args: (
                self.log_text.yview(*args),
                self.log_line_numbers.yview(*args),
            )
        )
        self.log_line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vbar_log.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.tag_configure("added", foreground="blue")
        self.log_text.tag_configure("removed", foreground="red")
        self.log_text.bind("<<Modified>>", self._on_log_text_modified)
        self._update_log_line_numbers()

        if names:
            self.base_combo.current(0)
            if len(names) > 1:
                self.other_combo.current(1)
            else:
                self.other_combo.current(0)
            self.compare()

    def insert_diff(self, old, new):
        """Insert a colorized diff between old and new strings."""
        matcher = difflib.SequenceMatcher(None, old, new)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                self.log_text.insert(tk.END, old[i1:i2])
            elif tag == "delete":
                self.log_text.insert(tk.END, old[i1:i2], "removed")
            elif tag == "insert":
                self.log_text.insert(tk.END, new[j1:j2], "added")
            elif tag == "replace":
                self.log_text.insert(tk.END, old[i1:i2], "removed")
                self.log_text.insert(tk.END, new[j1:j2], "added")

    def _on_log_text_modified(self, event=None):
        """Update line numbers when the log text changes."""
        self.log_text.edit_modified(False)
        self._update_log_line_numbers()

    def _update_log_line_numbers(self):
        """Refresh the line number column for the log text."""
        self.log_line_numbers.config(state="normal")
        self.log_line_numbers.delete("1.0", tk.END)
        line_count = int(self.log_text.index("end-1c").split(".")[0])
        numbers = "\n".join(str(i) for i in range(1, line_count + 1))
        self.log_line_numbers.insert("1.0", numbers)
        self.log_line_numbers.config(state="disabled")

    def diff_segments(self, old, new):
        """Return [(text, color)] representing the diff between old and new."""
        matcher = difflib.SequenceMatcher(None, old, new)
        segments = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                segments.append((old[i1:i2], "black"))
            elif tag == "delete":
                segments.append((old[i1:i2], "red"))
            elif tag == "insert":
                segments.append((new[j1:j2], "blue"))
            elif tag == "replace":
                segments.append((old[i1:i2], "red"))
                segments.append((new[j1:j2], "blue"))
        return segments

    def draw_segment_text(self, canvas, cx, cy, segments, font_obj):
        """Draw colored text segments centered on (cx, cy)."""
        # Split segments into lines
        lines = [[]]
        for text, color in segments:
            parts = text.split("\n")
            for idx, part in enumerate(parts):
                if idx > 0:
                    lines.append([])
                lines[-1].append((part, color))

        line_height = font_obj.metrics("linespace")
        total_height = line_height * len(lines)
        start_y = cy - total_height / 2
        for line in lines:
            line_width = sum(font_obj.measure(part) for part, _ in line)
            start_x = cx - line_width / 2
            x = start_x
            for part, color in line:
                if part:
                    canvas.create_text(
                        x,
                        start_y,
                        text=part,
                        anchor="nw",
                        fill=color,
                        font=font_obj,
                    )
                    x += font_obj.measure(part)
            start_y += line_height

    def draw_small_tree(self, canvas, node):
        def draw_connections(n):
            region_width = 60
            parent_bottom = (n.x, n.y + 20)
            for i, ch in enumerate(n.children):
                parent_conn = (
                    n.x - region_width / 2 + (i + 0.5) * (region_width / len(n.children)),
                    parent_bottom[1],
                )
                child_top = (ch.x, ch.y - 25)
                if self.app.fta_drawing_helper:
                    self.app.fta_drawing_helper.draw_90_connection(
                        canvas, parent_conn, child_top, outline_color="dimgray", line_width=1
                    )
                draw_connections(ch)

        def draw_node_simple(n):
            fill = self.app.get_node_fill_color(n, getattr(canvas, "diagram_mode", None))
            eff_x, eff_y = n.x, n.y
            top_text = n.node_type
            bottom_text = n.name
            typ = n.node_type.upper()
            if typ in ["GATE", "RIGOR LEVEL", "TOP EVENT"]:
                if n.gate_type and n.gate_type.upper() == "OR":
                    self.app.fta_drawing_helper.draw_rotated_or_gate_shape(
                        canvas,
                        eff_x,
                        eff_y,
                        scale=40,
                        top_text=top_text,
                        bottom_text=bottom_text,
                        fill=fill,
                        outline_color="dimgray",
                        line_width=1,
                    )
                else:
                    self.app.fta_drawing_helper.draw_rotated_and_gate_shape(
                        canvas,
                        eff_x,
                        eff_y,
                        scale=40,
                        top_text=top_text,
                        bottom_text=bottom_text,
                        fill=fill,
                        outline_color="dimgray",
                        line_width=1,
                    )
            else:
                self.app.fta_drawing_helper.draw_circle_event_shape(
                    canvas,
                    eff_x,
                    eff_y,
                    45,
                    top_text=top_text,
                    bottom_text=bottom_text,
                    fill=fill,
                    outline_color="dimgray",
                    line_width=1,
                )

        def draw_all(n):
            draw_node_simple(n)
            for ch in n.children:
                draw_all(ch)

        canvas.delete("all")
        draw_connections(node)
        draw_all(node)
        canvas.config(scrollregion=canvas.bbox("all"))

    def compare(self, event=None):
        import json  # ensure available even if module-level import is altered
        base = self.base_var.get()
        other = self.other_var.get()
        if not base or not other:
            return
        data1 = data2 = None
        for v in self.app.versions:
            if v["name"] == base:
                data1 = v["data"]
            if v["name"] == other:
                data2 = v["data"]
        if data1 is None or data2 is None:
            return

        map1 = self.app.node_map_from_data(data1["top_events"])
        map2 = self.app.node_map_from_data(data2["top_events"])

        def build_conn_set(events):
            conns = set()
            def visit(d):
                for ch in d.get("children", []):
                    conns.add((d["unique_id"], ch["unique_id"]))
                    visit(ch)
            for t in events:
                visit(t)
            return conns

        conns1 = build_conn_set(data1["top_events"])
        conns2 = build_conn_set(data2["top_events"])
        conn_status = {}
        for c in conns1 | conns2:
            if c in conns1 and c not in conns2:
                conn_status[c] = "removed"
            elif c in conns2 and c not in conns1:
                conn_status[c] = "added"
            else:
                conn_status[c] = "existing"

        status = {}
        for nid in set(map1) | set(map2):
            if nid in map1 and nid not in map2:
                status[nid] = "removed"
            elif nid in map2 and nid not in map1:
                status[nid] = "added"
            else:
                if json.dumps(map1[nid], sort_keys=True) != json.dumps(map2[nid], sort_keys=True):
                    status[nid] = "added"
                else:
                    status[nid] = "existing"

        module = sys.modules.get(self.app.__class__.__module__)
        FaultTreeNodeCls = getattr(module, 'FaultTreeNode', None)
        if not FaultTreeNodeCls and self.app.top_events:
            FaultTreeNodeCls = type(self.app.top_events[0])
        if not FaultTreeNodeCls:
            return

        new_roots = [FaultTreeNodeCls.from_dict(t) for t in data2["top_events"]]
        removed_ids = [nid for nid, st in status.items() if st == "removed"]
        for rid in removed_ids:
            nd = map1[rid]
            new_roots.append(FaultTreeNodeCls.from_dict(nd))

        # Build lookup of nodes actually drawn so extra connections can be
        # rendered even when the structure changed.
        node_objs = {}

        def collect_nodes(n):
            if n.unique_id not in node_objs:
                node_objs[n.unique_id] = n
            for ch in n.children:
                collect_nodes(ch)

        for r in new_roots:
            collect_nodes(r)

        self.tree_canvas.delete("all")

        def draw_connections(n):
            region_width = 60
            parent_bottom = (n.x, n.y + 20)
            for i, ch in enumerate(n.children):
                parent_conn = (
                    n.x - region_width / 2 + (i + 0.5) * (region_width / len(n.children)),
                    parent_bottom[1],
                )
                child_top = (ch.x, ch.y - 25)
                if self.app.fta_drawing_helper:
                    edge_st = conn_status.get((n.unique_id, ch.unique_id), "existing")
                    if status.get(n.unique_id) == "removed" or status.get(ch.unique_id) == "removed":
                        edge_st = "removed"
                    color = "gray"
                    if edge_st == "added":
                        color = "blue"
                    elif edge_st == "removed":
                        color = "red"
                    self.app.fta_drawing_helper.draw_90_connection(
                        self.tree_canvas,
                        parent_conn,
                        child_top,
                        outline_color=color,
                        line_width=1,
                    )
                draw_connections(ch)

        def draw_node(n):
            st = status.get(n.unique_id, "existing")
            color = "dimgray"
            if st == "added":
                color = "blue"
            elif st == "removed":
                color = "red"

            # Use the same information as the main diagram
            source = n if getattr(n, "is_primary_instance", True) else getattr(n, "original", n)
            subtype_text = source.input_subtype if source.input_subtype else "N/A"
            display_label = source.display_label
            old_data = map1.get(n.unique_id)
            new_data = map2.get(n.unique_id)
            show_goal = source.node_type.upper() == "TOP EVENT"

            def req_lines(reqs):
                return "; ".join(
                    self.app.format_requirement_with_trace(r) for r in reqs
                )

            if old_data and new_data:
                desc_segments = [("Desc: ", "black")] + self.diff_segments(
                    old_data.get("description", ""), new_data.get("description", "")
                )
                rat_segments = [("Rationale: ", "black")] + self.diff_segments(
                    old_data.get("rationale", ""), new_data.get("rationale", "")
                )
                if show_goal:
                    sg_segments = [("SG: ", "black")] + self.diff_segments(
                        f"{old_data.get('safety_goal_description','')} [{old_data.get('safety_goal_asil','')}]",
                        f"{new_data.get('safety_goal_description','')} [{new_data.get('safety_goal_asil','')}]"
                    )
                    ss_segments = [("Safe State: ", "black")] + self.diff_segments(
                        old_data.get('safe_state', ''), new_data.get('safe_state', '')
                    )
                else:
                    sg_segments = []
                    ss_segments = []
                # requirements shown in separate box
                req_segments = []
            else:
                desc_segments = [("Desc: " + source.description, "black")]
                rat_segments = [("Rationale: " + source.rationale, "black")]
                if show_goal:
                    sg_segments = [(
                        "SG: " + f"{source.safety_goal_description} [{source.safety_goal_asil}]",
                        "black",
                    )]
                    ss_segments = [(
                        "Safe State: " + getattr(source, 'safe_state', ''),
                        "black",
                    )]
                else:
                    sg_segments = []
                    ss_segments = []
                # requirements shown in separate box
                req_segments = []

            segments = [
                (f"Type: {source.node_type}\n", "black"),
                (f"Subtype: {subtype_text}\n", "black"),
                (f"{display_label}\n", "black"),
            ] + desc_segments + [("\n\n", "black")] + rat_segments
            if sg_segments:
                segments += [("\n\n", "black")] + sg_segments + [("\n\n", "black")] + ss_segments

            top_text = "".join(seg[0] for seg in segments)
            bottom_text = n.name

            fill = self.app.get_node_fill_color(n, getattr(canvas, "diagram_mode", None))
            eff_x, eff_y = n.x, n.y
            typ = n.node_type.upper()
            items_before = self.tree_canvas.find_all()
            if typ in ["GATE", "RIGOR LEVEL", "TOP EVENT"]:
                if n.gate_type and n.gate_type.upper() == "OR":
                    self.app.fta_drawing_helper.draw_rotated_or_gate_shape(
                        self.tree_canvas,
                        eff_x,
                        eff_y,
                        scale=40,
                        top_text=top_text,
                        bottom_text=bottom_text,
                        fill=fill,
                        outline_color=color,
                        line_width=2,
                    )
                else:
                    self.app.fta_drawing_helper.draw_rotated_and_gate_shape(
                        self.tree_canvas,
                        eff_x,
                        eff_y,
                        scale=40,
                        top_text=top_text,
                        bottom_text=bottom_text,
                        fill=fill,
                        outline_color=color,
                        line_width=2,
                    )
            else:
                self.app.fta_drawing_helper.draw_circle_event_shape(
                    self.tree_canvas,
                    eff_x,
                    eff_y,
                    45,
                    top_text=top_text,
                    bottom_text=bottom_text,
                    fill=fill,
                    outline_color=color,
                    line_width=2,
                )

            items_after = self.tree_canvas.find_all()
            text_id = None
            for item in items_after:
                if item in items_before:
                    continue
                if self.tree_canvas.type(item) == "text" and self.tree_canvas.itemcget(item, "text") == top_text:
                    text_id = item
                    break

            if text_id and any(c in ("red", "blue") for _, c in segments):
                bbox = self.tree_canvas.bbox(text_id)
                cx = (bbox[0] + bbox[2]) / 2
                cy = (bbox[1] + bbox[3]) / 2
                self.tree_canvas.itemconfigure(text_id, state="hidden")
                self.draw_segment_text(self.tree_canvas, cx, cy, segments, self.app.diagram_font)
            for ch in n.children:
                draw_node(ch)

        for r in new_roots:
            draw_connections(r)
            draw_node(r)

        # Draw removed links between nodes that still exist in the new
        # structure. These won't be part of the tree so handle them
        # separately using the collected node objects.
        existing_pairs = set()
        for p in node_objs.values():
            for ch in p.children:
                existing_pairs.add((p.unique_id, ch.unique_id))

        for (pid, cid), st in conn_status.items():
            if st != "removed":
                continue
            if (pid, cid) in existing_pairs:
                continue
            if pid in node_objs and cid in node_objs:
                parent = node_objs[pid]
                child = node_objs[cid]
                parent_pt = (parent.x, parent.y + 20)
                child_pt = (child.x, child.y - 25)
                if self.app.fta_drawing_helper:
                    self.app.fta_drawing_helper.draw_90_connection(
                        self.tree_canvas,
                        parent_pt,
                        child_pt,
                        outline_color="red",
                        line_width=1,
                    )

        self.tree_canvas.config(scrollregion=self.tree_canvas.bbox("all"))

        # ----- FMEA diff -----
        self.fmea_tree.delete(*self.fmea_tree.get_children())
        self.req_text.delete("1.0", tk.END)
        self.log_text.delete("1.0", tk.END)

        # collect requirement sets for both versions
        reqs1, reqs2 = {}, {}

        def collect_reqs(node_dict, target):
            for r in node_dict.get("safety_requirements", []):
                rid = r.get("id")
                if rid and rid not in target:
                    target[rid] = r
            for ch in node_dict.get("children", []):
                collect_reqs(ch, target)

        for t in data1["top_events"]:
            collect_reqs(t, reqs1)
        for t in data2["top_events"]:
            collect_reqs(t, reqs2)
        for f in data1.get("fmeas", []):
            for e in f.get("entries", []):
                for r in e.get("safety_requirements", []):
                    rid = r.get("id")
                    if rid and rid not in reqs1:
                        reqs1[rid] = r
        for f in data2.get("fmeas", []):
            for e in f.get("entries", []):
                for r in e.get("safety_requirements", []):
                    rid = r.get("id")
                    if rid and rid not in reqs2:
                        reqs2[rid] = r
        for f in data1.get("fmedas", []):
            for e in f.get("entries", []):
                for r in e.get("safety_requirements", []):
                    rid = r.get("id")
                    if rid and rid not in reqs1:
                        reqs1[rid] = r
        for f in data2.get("fmedas", []):
            for e in f.get("entries", []):
                for r in e.get("safety_requirements", []):
                    rid = r.get("id")
                    if rid and rid not in reqs2:
                        reqs2[rid] = r

        def fmt(r):
            return self.app.format_requirement_with_trace(r)

        all_ids = sorted(set(reqs1) | set(reqs2))
        for rid in all_ids:
            r1 = reqs1.get(rid)
            r2 = reqs2.get(rid)
            if r1 and not r2:
                self.req_text.insert(tk.END, "Removed: ")
                self.insert_diff_text(self.req_text, fmt(r1), "")
            elif r2 and not r1:
                self.req_text.insert(tk.END, "Added: ")
                self.insert_diff_text(self.req_text, "", fmt(r2))
            else:
                if json.dumps(r1, sort_keys=True) != json.dumps(r2, sort_keys=True):
                    self.req_text.insert(tk.END, "Updated: ")
                    self.insert_diff_text(self.req_text, fmt(r1), fmt(r2))
                else:
                    self.req_text.insert(tk.END, fmt(r2))
            self.req_text.insert(tk.END, "\n")

        for nid in set(map1) | set(map2):
            n1 = map1.get(nid, {})
            n2 = map2.get(nid, {})
            node_type = (n2.get('type') or n1.get('type', '')).upper()
            sg_old = f"{n1.get('safety_goal_description','')} [{n1.get('safety_goal_asil','')}]"
            sg_new = f"{n2.get('safety_goal_description','')} [{n2.get('safety_goal_asil','')}]"
            label = n2.get('user_name') or n1.get('user_name') or f"Node {nid}"
            if node_type == 'TOP EVENT':
                if sg_old != sg_new:
                    self.req_text.insert(tk.END, f"Safety Goal for {label}: ")
                    self.insert_diff_text(self.req_text, sg_old, sg_new)
                    self.req_text.insert(tk.END, "\n")
                if n1.get('safe_state','') != n2.get('safe_state',''):
                    self.req_text.insert(tk.END, f"Safe State for {label}: ")
                    self.insert_diff_text(self.req_text, n1.get('safe_state',''), n2.get('safe_state',''))
                    self.req_text.insert(tk.END, "\n")

        # --- log FTA textual changes ---
        for nid, st in status.items():
            if st == "added":
                node = map2[nid]
                self.log_text.insert(
                    tk.END, f"Added node {node.get('user_name', nid)}\n", "added"
                )
            elif st == "removed":
                node = map1[nid]
                self.log_text.insert(
                    tk.END, f"Removed node {node.get('user_name', nid)}\n", "removed"
                )
            else:
                n1 = map1[nid]
                n2 = map2[nid]
                if n1.get("description", "") != n2.get("description", ""):
                    self.log_text.insert(
                        tk.END,
                        f"Description change for {n1.get('user_name', nid)}: ",
                    )
                    self.insert_diff(n1.get("description", ""), n2.get("description", ""))
                    self.log_text.insert(tk.END, "\n")
                if n1.get("rationale", "") != n2.get("rationale", ""):
                    self.log_text.insert(
                        tk.END,
                        f"Rationale change for {n1.get('user_name', nid)}: ",
                    )
                    self.insert_diff(n1.get("rationale", ""), n2.get("rationale", ""))
                    self.log_text.insert(tk.END, "\n")
                sg1 = f"{n1.get('safety_goal_description','')} [{n1.get('safety_goal_asil','')}]"
                sg2 = f"{n2.get('safety_goal_description','')} [{n2.get('safety_goal_asil','')}]"
                node_type = (n2.get('type') or n1.get('type', '')).upper()
                if node_type == 'TOP EVENT':
                    if sg1 != sg2:
                        self.log_text.insert(
                            tk.END,
                            f"Safety Goal change for {n1.get('user_name', nid)}: ",
                        )
                        self.insert_diff(sg1, sg2)
                        self.log_text.insert(tk.END, "\n")
                    if n1.get('safe_state','') != n2.get('safe_state',''):
                        self.log_text.insert(
                            tk.END,
                            f"Safe State change for {n1.get('user_name', nid)}: ",
                        )
                        self.insert_diff(n1.get('safe_state',''), n2.get('safe_state',''))
                        self.log_text.insert(tk.END, "\n")
                def req_lines(reqs):
                    lines = [self.app.format_requirement_with_trace(r) for r in reqs]
                    return "\n".join(lines)

                req1 = req_lines(n1.get("safety_requirements", []))
                req2 = req_lines(n2.get("safety_requirements", []))
                if req1 != req2:
                    self.log_text.insert(
                        tk.END,
                        f"Requirements change for {n1.get('user_name', nid)}: ",
                    )
                    self.insert_diff(req1, req2)
                    self.log_text.insert(tk.END, "\n")

        fmea1 = {f["name"]: f for f in data1.get("fmeas", [])}
        fmea2 = {f["name"]: f for f in data2.get("fmeas", [])}
        all_names = set(fmea1) | set(fmea2)
        for name in sorted(all_names):
            entries1 = {e["unique_id"]: e for e in fmea1.get(name, {}).get("entries", [])}
            entries2 = {e["unique_id"]: e for e in fmea2.get(name, {}).get("entries", [])}
            for uid in set(entries1) | set(entries2):
                if uid in entries1 and uid not in entries2:
                    st = "removed"
                    entry = entries1[uid]
                elif uid in entries2 and uid not in entries1:
                    st = "added"
                    entry = entries2[uid]
                else:
                    if json.dumps(entries1[uid], sort_keys=True) != json.dumps(entries2[uid], sort_keys=True):
                        st = "added"
                        entry = entries2[uid]
                    else:
                        st = "existing"
                        entry = entries2[uid]

                failure = entry.get("description", entry.get("user_name", f"BE {uid}"))
                parent = entry.get("parents", [{}])
                parent = parent[0] if parent else {}
                if parent and parent.get("node_type", "").upper() not in GATE_NODE_TYPES and parent.get("user_name"):
                    comp = parent.get("user_name")
                    parent_name = parent.get("user_name")
                else:
                    comp = entry.get("fmea_component", "") or "N/A"
                    parent_name = ""
                rpn = (
                    int(entry.get("fmea_severity", 1))
                    * int(entry.get("fmea_occurrence", 1))
                    * int(entry.get("fmea_detection", 1))
                )
                reqs = "; ".join(
                    f"{r.get('req_type', '')}:{r.get('text', '')}"
                    for r in entry.get("safety_requirements", [])
                )
                row = [
                    name,
                    comp,
                    parent_name,
                    failure,
                    entry.get("fmea_effect", ""),
                    entry.get("fmea_cause", ""),
                    entry.get("fmea_severity", ""),
                    entry.get("fmea_occurrence", ""),
                    entry.get("fmea_detection", ""),
                    rpn,
                    reqs,
                ]
                self.fmea_tree.insert("", "end", values=row, tags=(st,))
                if st != "existing":
                    if uid in entries1 and uid in entries2 and st == "added":
                        prefix = "Updated"
                    else:
                        prefix = "Added" if st == "added" else "Removed"
                    self.log_text.insert(tk.END, f"{prefix} FMEA entry {failure}\n", st)
                    if prefix == "Updated":
                        e1 = entries1[uid]
                        e2 = entries2[uid]
                        for fld in [
                            "description",
                            "fmea_effect",
                            "fmea_cause",
                            "fmea_severity",
                            "fmea_occurrence",
                            "fmea_detection",
                        ]:
                            v1 = str(e1.get(fld, ""))
                            v2 = str(e2.get(fld, ""))
                            if v1 != v2:
                                self.log_text.insert(tk.END, f"  {fld}: ")
                                self.insert_diff(v1, v2)
                                self.log_text.insert(tk.END, "\n")

        # ----- FMEDA diff -----
        self.fmeda_tree.delete(*self.fmeda_tree.get_children())
        fmd1 = {f["name"]: f for f in data1.get("fmedas", [])}
        fmd2 = {f["name"]: f for f in data2.get("fmedas", [])}
        for name in sorted(set(fmd1) | set(fmd2)):
            ent1 = {e["unique_id"]: e for e in fmd1.get(name, {}).get("entries", [])}
            ent2 = {e["unique_id"]: e for e in fmd2.get(name, {}).get("entries", [])}
            for uid in set(ent1) | set(ent2):
                if uid in ent1 and uid not in ent2:
                    st = "removed"
                    entry = ent1[uid]
                elif uid in ent2 and uid not in ent1:
                    st = "added"
                    entry = ent2[uid]
                else:
                    if json.dumps(ent1[uid], sort_keys=True) != json.dumps(ent2[uid], sort_keys=True):
                        st = "added"
                        entry = ent2[uid]
                    else:
                        st = "existing"
                        entry = ent2[uid]
                parent = entry.get("parents", [{}])
                parent = parent[0] if parent else {}
                if parent and parent.get("node_type", "").upper() not in GATE_NODE_TYPES and parent.get("user_name"):
                    comp = parent.get("user_name")
                    parent_name = parent.get("user_name")
                else:
                    comp = entry.get("fmea_component", "") or "N/A"
                    parent_name = ""
                row = [
                    name,
                    comp,
                    parent_name,
                    entry.get("description", entry.get("user_name", f"BE {uid}")),
                    entry.get("fmeda_malfunction", ""),
                    entry.get("fmeda_safety_goal", ""),
                    entry.get("fmeda_fault_type", ""),
                    entry.get("fmeda_fault_fraction", ""),
                    entry.get("fmeda_fit", ""),
                    entry.get("fmeda_diag_cov", ""),
                    entry.get("fmeda_mechanism", ""),
                ]
                self.fmeda_tree.insert("", "end", values=row, tags=(st,))

        # ----- HAZOP diff -----
        self.hazop_tree.delete(*self.hazop_tree.get_children())
        haz1 = {d["name"]: d for d in data1.get("hazops", [])}
        haz2 = {d["name"]: d for d in data2.get("hazops", [])}
        for name in sorted(set(haz1) | set(haz2)):
            e1 = haz1.get(name, {}).get("entries", [])
            e2 = haz2.get(name, {}).get("entries", [])
            seen = set()
            for e in e2:
                row = [
                    name,
                    e.get("function", ""),
                    e.get("malfunction", ""),
                    e.get("mtype", ""),
                    e.get("scenario", ""),
                    e.get("conditions", ""),
                    e.get("hazard", ""),
                    "Yes" if e.get("safety") else "No",
                    e.get("rationale", ""),
                    "Yes" if e.get("covered") else "No",
                    e.get("covered_by", ""),
                ]
                tag = "existing" if e in e1 else "added"
                self.hazop_tree.insert("", "end", values=row, tags=(tag,))
                seen.add(json.dumps(e, sort_keys=True))
            for e in e1:
                if json.dumps(e, sort_keys=True) not in seen:
                    row = [
                        name,
                        e.get("function", ""),
                        e.get("malfunction", ""),
                        e.get("mtype", ""),
                        e.get("scenario", ""),
                        e.get("conditions", ""),
                        e.get("hazard", ""),
                        "Yes" if e.get("safety") else "No",
                        e.get("rationale", ""),
                        "Yes" if e.get("covered") else "No",
                        e.get("covered_by", ""),
                    ]
                    # Insert removed HAZOP entry
                    self.hazop_tree.insert("", "end", values=row, tags=("removed",))

        # ----- Risk Assessment diff -----
        self.hara_tree.delete(*self.hara_tree.get_children())
        hr1 = {d["name"]: d for d in data1.get("haras", [])}
        hr2 = {d["name"]: d for d in data2.get("haras", [])}
        for name in sorted(set(hr1) | set(hr2)):
            e1 = hr1.get(name, {}).get("entries", [])
            e2 = hr2.get(name, {}).get("entries", [])
            seen = set()
            for e in e2:
                row = [
                    name,
                    e.get("malfunction", ""),
                    e.get("hazard", ""),
                    e.get("severity", ""),
                    e.get("sev_rationale", ""),
                    e.get("controllability", ""),
                    e.get("cont_rationale", ""),
                    e.get("exposure", ""),
                    e.get("exp_rationale", ""),
                    e.get("asil", ""),
                    e.get("safety_goal", ""),
                ]
                tag = "existing" if e in e1 else "added"
                self.hara_tree.insert("", "end", values=row, tags=(tag,))
                seen.add(json.dumps(e, sort_keys=True))
            for e in e1:
                if json.dumps(e, sort_keys=True) not in seen:
                    row = [
                        name,
                        e.get("malfunction", ""),
                        e.get("hazard", ""),
                        e.get("severity", ""),
                        e.get("sev_rationale", ""),
                        e.get("controllability", ""),
                        e.get("cont_rationale", ""),
                        e.get("exposure", ""),
                        e.get("exp_rationale", ""),
                        e.get("asil", ""),
                        e.get("safety_goal", ""),
                    ]
                    self.hara_tree.insert("", "end", values=row, tags=("removed",))

        # ----- STPA diff -----
        self.stpa_tree.delete(*self.stpa_tree.get_children())
        st1 = {d["name"]: d for d in data1.get("stpas", [])}
        st2 = {d["name"]: d for d in data2.get("stpas", [])}
        for name in sorted(set(st1) | set(st2)):
            e1 = st1.get(name, {}).get("entries", [])
            e2 = st2.get(name, {}).get("entries", [])
            seen = set()
            for e in e2:
                row = [
                    name,
                    e.get("action", ""),
                    e.get("not_providing", ""),
                    e.get("providing", ""),
                    e.get("incorrect_timing", ""),
                    e.get("stopped_too_soon", ""),
                    "; ".join(e.get("safety_constraints", [])),
                ]
                tag = "existing" if e in e1 else "added"
                self.stpa_tree.insert("", "end", values=row, tags=(tag,))
                seen.add(json.dumps(e, sort_keys=True))
            for e in e1:
                if json.dumps(e, sort_keys=True) not in seen:
                    row = [
                        name,
                        e.get("action", ""),
                        e.get("not_providing", ""),
                        e.get("providing", ""),
                        e.get("incorrect_timing", ""),
                        e.get("stopped_too_soon", ""),
                        "; ".join(e.get("safety_constraints", [])),
                    ]
                    self.stpa_tree.insert("", "end", values=row, tags=("removed",))

        # ----- FI2TC diff -----
        self.fi2tc_tree.delete(*self.fi2tc_tree.get_children())
        fi1 = {d["name"]: d for d in data1.get("fi2tc_docs", [])}
        fi2 = {d["name"]: d for d in data2.get("fi2tc_docs", [])}
        for name in sorted(set(fi1) | set(fi2)):
            e1 = fi1.get(name, {}).get("entries", [])
            e2 = fi2.get(name, {}).get("entries", [])
            seen = set()
            for e in e2:
                row = [e.get(k, "") for k in [
                    "id","system_function","allocation","interfaces","functional_insufficiencies","scene","scenario","driver_behavior","occurrence","vehicle_effect","severity","design_measures","verification","measure_effectiveness","triggering_conditions","mitigation","acceptance" ]]
                row.insert(0, name)
                tag = "existing" if e in e1 else "added"
                self.fi2tc_tree.insert("", "end", values=row, tags=(tag,))
                seen.add(json.dumps(e, sort_keys=True))
            for e in e1:
                if json.dumps(e, sort_keys=True) not in seen:
                    row = [e.get(k, "") for k in [
                        "id","system_function","allocation","interfaces","functional_insufficiencies","scene","scenario","driver_behavior","occurrence","vehicle_effect","severity","design_measures","verification","measure_effectiveness","triggering_conditions","mitigation","acceptance" ]]
                    row.insert(0, name)
                    self.fi2tc_tree.insert("", "end", values=row, tags=("removed",))

        # ----- TC2FI diff -----
        self.tc2fi_tree.delete(*self.tc2fi_tree.get_children())
        tc1 = {d["name"]: d for d in data1.get("tc2fi_docs", [])}
        tc2 = {d["name"]: d for d in data2.get("tc2fi_docs", [])}
        for name in sorted(set(tc1) | set(tc2)):
            e1 = tc1.get(name, {}).get("entries", [])
            e2 = tc2.get(name, {}).get("entries", [])
            seen = set()
            for e in e2:
                row = [e.get(k, "") for k in [
                    "id","known_use_case","occurrence","impacted_function","arch_elements","interfaces","functional_insufficiencies","vehicle_effect","severity","design_measures","verification","measure_effectiveness","scene","scenario","driver_behavior","triggering_conditions","mitigation","acceptance" ]]
                row.insert(0, name)
                tag = "existing" if e in e1 else "added"
                self.tc2fi_tree.insert("", "end", values=row, tags=(tag,))
                seen.add(json.dumps(e, sort_keys=True))
            for e in e1:
                if json.dumps(e, sort_keys=True) not in seen:
                    row = [e.get(k, "") for k in [
                        "id","known_use_case","occurrence","impacted_function","arch_elements","interfaces","functional_insufficiencies","vehicle_effect","severity","design_measures","verification","measure_effectiveness","scene","scenario","driver_behavior","triggering_conditions","mitigation","acceptance" ]]
                    row.insert(0, name)
                    self.tc2fi_tree.insert("", "end", values=row, tags=("removed",))



    def on_close(self):
        self.app.diff_nodes = []
        try:
            if hasattr(self.app, "canvas") and self.app.canvas.winfo_exists():
                self.app.redraw_canvas()
        except tk.TclError:
            pass
        self.destroy()
