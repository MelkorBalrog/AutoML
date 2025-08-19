import tkinter as tk
from tkinter import ttk
from pathlib import Path
import json
import textwrap
import re
from config import (
    load_diagram_rules,
    validate_diagram_rules,
    load_requirement_patterns,
    validate_requirement_patterns,
)
from gui import messagebox


PLACEHOLDER_COLORS = {
    "subject": "#2e86c1",
    "action": "#27ae60",
    "object": "#d35400",
    "constraint": "#8e44ad",
}


def _extract_action(trigger: str) -> str:
    """Return the action name from a trigger string."""
    match = re.search(r"\[([^\]]+)\]", trigger)
    return match.group(1) if match else ""


def highlight_placeholders(widget: tk.Text, action_word: str = "") -> None:
    """Apply color and bold styling to requirement placeholders in ``widget``.

    Parameters
    ----------
    widget:
        Text widget containing the template.
    action_word:
        Optional action verb to highlight when no ``<action>`` placeholder is
        present.
    """

    text = widget.get("1.0", "end-1c")
    for tag, color in PLACEHOLDER_COLORS.items():
        widget.tag_remove(tag, "1.0", "end")
        widget.tag_configure(tag, foreground=color, font=(None, -12, "bold"))
        for m in re.finditer(rf"<{tag}[^>]*>", text):
            start = f"1.0+{m.start()}c"
            end = f"1.0+{m.end()}c"
            widget.tag_add(tag, start, end)

    if action_word and "<action" not in text:
        widget.tag_remove("action_word", "1.0", "end")
        widget.tag_configure(
            "action_word",
            foreground=PLACEHOLDER_COLORS["action"],
            font=(None, -12, "bold"),
        )
        for m in re.finditer(re.escape(action_word), text, re.IGNORECASE):
            start = f"1.0+{m.start()}c"
            end = f"1.0+{m.end()}c"
            widget.tag_add("action_word", start, end)


class PatternConfig(tk.Toplevel):
    """Dialog for editing a requirement pattern's fields."""

    def __init__(self, master, pattern: dict):
        super().__init__(master)
        self.title("Edit Requirement Pattern")
        self.pattern = pattern
        self.result: dict | None = None

        self.columnconfigure(1, weight=1)

        self.pid_var = tk.StringVar(value=pattern.get("Pattern ID", ""))
        self.trigger_var = tk.StringVar(value=pattern.get("Trigger", ""))
        tmpl = pattern.get("Template", "")
        self.template_text = tk.Text(self, height=3, wrap="word")
        self.template_text.insert("1.0", tmpl)
        self.vars_var = tk.StringVar(
            value=", ".join(pattern.get("Variables", []))
        )
        self.notes_var = tk.StringVar(value=pattern.get("Notes", ""))
        self._highlight_template(self.template_text, pattern.get("Trigger", ""))

        row = 0
        tk.Label(self, text="Pattern ID:").grid(
            row=row, column=0, sticky="e", padx=4, pady=4
        )
        ttk.Entry(self, textvariable=self.pid_var).grid(
            row=row, column=1, sticky="ew", padx=4, pady=4
        )
        row += 1

        tk.Label(self, text="Trigger:").grid(
            row=row, column=0, sticky="e", padx=4, pady=4
        )
        ttk.Entry(self, textvariable=self.trigger_var).grid(
            row=row, column=1, sticky="ew", padx=4, pady=4
        )
        row += 1

        tk.Label(self, text="Template:").grid(
            row=row, column=0, sticky="ne", padx=4, pady=4
        )
        self.template_text.grid(row=row, column=1, sticky="ew", padx=4, pady=4)
        self.template_text.bind(
            "<KeyRelease>",
            lambda _e: self._highlight_template(self.template_text, self.trigger_var.get()),
        )
        row += 1

        tk.Label(self, text="Variables:").grid(
            row=row, column=0, sticky="e", padx=4, pady=4
        )
        ttk.Entry(self, textvariable=self.vars_var).grid(
            row=row, column=1, sticky="ew", padx=4, pady=4
        )
        row += 1

        tk.Label(self, text="Notes:").grid(
            row=row, column=0, sticky="e", padx=4, pady=4
        )
        ttk.Entry(self, textvariable=self.notes_var).grid(
            row=row, column=1, sticky="ew", padx=4, pady=4
        )
        row += 1

        btns = ttk.Frame(self)
        btns.grid(row=row, column=0, columnspan=2, pady=4)
        ttk.Button(btns, text="OK", command=self._on_ok).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(
            side=tk.LEFT, padx=4
        )

        self.transient(master)
        self.grab_set()

    def _on_ok(self) -> None:
        self.result = {
            "Pattern ID": self.pid_var.get().strip(),
            "Trigger": self.trigger_var.get().strip(),
            "Template": self.template_text.get("1.0", "end-1c").strip(),
            "Variables": [
                v.strip() for v in self.vars_var.get().split(",") if v.strip()
            ],
            "Notes": self.notes_var.get().strip(),
        }
        self.destroy()

    def _highlight_template(self, widget: tk.Text, trigger: str) -> None:
        action = _extract_action(trigger)
        highlight_placeholders(widget, action)


class RuleConfig(tk.Toplevel):
    """Dialog for editing a requirement rule definition."""

    def __init__(self, master, rule: dict | None = None):
        super().__init__(master)
        rule = rule or {}
        self.title("Edit Requirement Rule")
        self.result: dict | None = None

        self.columnconfigure(1, weight=1)

        self.label_var = tk.StringVar(value=rule.get("label", ""))
        self.action_var = tk.StringVar(value=rule.get("action", ""))
        self.subject_var = tk.StringVar(value=rule.get("subject", ""))
        self.targets_var = tk.IntVar(value=rule.get("targets", 1))
        tmpl = rule.get("template", "")
        self.template_text = tk.Text(self, height=3, wrap="word")
        self.template_text.insert("1.0", tmpl)
        self.vars_var = tk.StringVar(
            value=", ".join(rule.get("variables", []))
        )
        self.constraint_var = tk.BooleanVar(value=rule.get("constraint", False))

        row = 0
        tk.Label(self, text="Label:").grid(
            row=row, column=0, sticky="e", padx=4, pady=4
        )
        ttk.Entry(self, textvariable=self.label_var).grid(
            row=row, column=1, sticky="ew", padx=4, pady=4
        )
        row += 1

        tk.Label(self, text="Action:").grid(
            row=row, column=0, sticky="e", padx=4, pady=4
        )
        ttk.Entry(self, textvariable=self.action_var).grid(
            row=row, column=1, sticky="ew", padx=4, pady=4
        )
        row += 1

        tk.Label(self, text="Subject:").grid(
            row=row, column=0, sticky="e", padx=4, pady=4
        )
        ttk.Entry(self, textvariable=self.subject_var).grid(
            row=row, column=1, sticky="ew", padx=4, pady=4
        )
        row += 1

        tk.Label(self, text="Template:").grid(
            row=row, column=0, sticky="ne", padx=4, pady=4
        )
        self.template_text.grid(row=row, column=1, sticky="ew", padx=4, pady=4)
        self.template_text.bind(
            "<KeyRelease>",
            lambda _e: highlight_placeholders(self.template_text, self.action_var.get()),
        )
        highlight_placeholders(self.template_text, self.action_var.get())
        row += 1

        tk.Label(self, text="Variables:").grid(
            row=row, column=0, sticky="e", padx=4, pady=4
        )
        ttk.Entry(self, textvariable=self.vars_var).grid(
            row=row, column=1, sticky="ew", padx=4, pady=4
        )
        row += 1

        tk.Label(self, text="Targets:").grid(
            row=row, column=0, sticky="e", padx=4, pady=4
        )
        ttk.Spinbox(self, from_=1, to=10, textvariable=self.targets_var, width=5).grid(
            row=row, column=1, sticky="w", padx=4, pady=4
        )
        row += 1

        ttk.Checkbutton(
            self, text="Requires constraint", variable=self.constraint_var
        ).grid(row=row, column=1, sticky="w", padx=4, pady=4)
        row += 1

        btns = ttk.Frame(self)
        btns.grid(row=row, column=0, columnspan=2, pady=4)
        ttk.Button(btns, text="OK", command=self._on_ok).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(
            side=tk.LEFT, padx=4
        )

        self.transient(master)
        self.grab_set()

    def _on_ok(self) -> None:
        label = self.label_var.get().strip()
        action = self.action_var.get().strip()
        if not label or not action:
            self.destroy()
            return
        res = {"label": label, "action": action}
        subj = self.subject_var.get().strip()
        if subj:
            res["subject"] = subj
        tmpl = self.template_text.get("1.0", "end-1c").strip()
        if tmpl:
            res["template"] = tmpl
            vars_ = [v.strip() for v in self.vars_var.get().split(",") if v.strip()]
            if vars_:
                res["variables"] = vars_
        tgt = self.targets_var.get()
        if tgt > 1:
            res["targets"] = tgt
        if self.constraint_var.get():
            res["constraint"] = True
        self.result = res
        self.destroy()


class SequenceConfig(tk.Toplevel):
    """Dialog for editing a requirement sequence definition."""

    def __init__(self, master, seq: dict | None = None):
        super().__init__(master)
        seq = seq or {}
        self.title("Edit Sequence Rule")
        self.result: dict | None = None

        self.columnconfigure(1, weight=1)

        self.label_var = tk.StringVar(value=seq.get("label", ""))
        self.rels_var = tk.StringVar(
            value=", ".join(seq.get("relations", []))
        )
        self.action_var = tk.StringVar(value=seq.get("action", ""))
        self.subject_var = tk.StringVar(value=seq.get("subject", ""))
        self.template_var = tk.StringVar(value=seq.get("template", ""))
        self.vars_var = tk.StringVar(
            value=", ".join(seq.get("variables", []))
        )

        row = 0
        tk.Label(self, text="Label:").grid(
            row=row, column=0, sticky="e", padx=4, pady=4
        )
        ttk.Entry(self, textvariable=self.label_var).grid(
            row=row, column=1, sticky="ew", padx=4, pady=4
        )
        row += 1

        tk.Label(self, text="Relations:").grid(
            row=row, column=0, sticky="e", padx=4, pady=4
        )
        ttk.Entry(self, textvariable=self.rels_var).grid(
            row=row, column=1, sticky="ew", padx=4, pady=4
        )
        row += 1

        tk.Label(self, text="Action:").grid(
            row=row, column=0, sticky="e", padx=4, pady=4
        )
        ttk.Entry(self, textvariable=self.action_var).grid(
            row=row, column=1, sticky="ew", padx=4, pady=4
        )
        row += 1

        tk.Label(self, text="Subject:").grid(
            row=row, column=0, sticky="e", padx=4, pady=4
        )
        ttk.Entry(self, textvariable=self.subject_var).grid(
            row=row, column=1, sticky="ew", padx=4, pady=4
        )
        row += 1

        tk.Label(self, text="Template:").grid(
            row=row, column=0, sticky="e", padx=4, pady=4
        )
        ttk.Entry(self, textvariable=self.template_var).grid(
            row=row, column=1, sticky="ew", padx=4, pady=4
        )
        row += 1

        tk.Label(self, text="Variables:").grid(
            row=row, column=0, sticky="e", padx=4, pady=4
        )
        ttk.Entry(self, textvariable=self.vars_var).grid(
            row=row, column=1, sticky="ew", padx=4, pady=4
        )
        row += 1

        btns = ttk.Frame(self)
        btns.grid(row=row, column=0, columnspan=2, pady=4)
        ttk.Button(btns, text="OK", command=self._on_ok).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(
            side=tk.LEFT, padx=4
        )

        self.transient(master)
        self.grab_set()

    def _on_ok(self) -> None:
        label = self.label_var.get().strip()
        rels = [r.strip() for r in self.rels_var.get().split(",") if r.strip()]
        if not label or len(rels) < 2:
            self.destroy()
            return
        res = {"label": label, "relations": rels}
        act = self.action_var.get().strip()
        if act:
            res["action"] = act
        subj = self.subject_var.get().strip()
        if subj:
            res["subject"] = subj
        tmpl = self.template_var.get().strip()
        if tmpl:
            res["template"] = tmpl
            vars_ = [v.strip() for v in self.vars_var.get().split(",") if v.strip()]
            if vars_:
                res["variables"] = vars_
        self.result = res
        self.destroy()

class RequirementPatternsEditor(tk.Frame):
    """Visual editor for requirement pattern configuration and rules."""

    def __init__(self, master, app, config_path: Path | None = None):
        super().__init__(master)
        self.app = app
        self.config_path = Path(
            config_path
            or Path(__file__).resolve().parents[1] / "config/requirement_patterns.json"
        )
        self.rules_path = (
            Path(__file__).resolve().parents[1] / "config/diagram_rules.json"
        )
        try:
            self.data = load_requirement_patterns(self.config_path)
        except Exception as exc:  # pragma: no cover - GUI fallback
            messagebox.showerror(
                "Requirement Patterns", f"Failed to load configuration:\n{exc}"
            )
            self.data = []
        try:
            self.rules_cfg = load_diagram_rules(self.rules_path)
            self.req_rules = self.rules_cfg.get("requirement_rules", {})
            self.req_seqs = self.rules_cfg.get("requirement_sequences", {})
        except Exception as exc:  # pragma: no cover - GUI fallback
            messagebox.showerror(
                "Requirement Rules", f"Failed to load configuration:\n{exc}"
            )
            self.rules_cfg = {}
            self.req_rules = {}
            self.req_seqs = {}

        self._ensure_role_subject_variants()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        nb = ttk.Notebook(self)
        nb.grid(row=0, column=0, sticky="nsew")

        # ------------------------------------------------------------------
        # Patterns tab
        # ------------------------------------------------------------------
        pat_frame = ttk.Frame(nb)
        pat_frame.rowconfigure(0, weight=1)
        pat_frame.columnconfigure(0, weight=1)
        nb.add(pat_frame, text="Patterns")

        tree_frame = ttk.Frame(pat_frame)
        tree_frame.grid(row=0, column=0, sticky="nsew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            tree_frame, columns=("idx", "trigger", "template"), show="headings"
        )
        self.tree.heading("idx", text="#")
        self.tree.heading("trigger", text="Trigger")
        self.tree.heading("template", text="Template")
        self.tree.column("idx", width=30, stretch=False, anchor="center")
        self.tree.column("trigger", width=250, stretch=True)
        self.tree.column("template", width=250, stretch=True)
        self.tree.bind("<Double-1>", self._edit_item)
        self.tree.grid(row=0, column=0, sticky="nsew")

        ybar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        xbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
        ybar.grid(row=0, column=1, sticky="ns")
        xbar.grid(row=1, column=0, sticky="ew")

        btn_frame = ttk.Frame(pat_frame)
        btn_frame.grid(row=1, column=0, sticky="e", pady=4, padx=4)
        ttk.Button(btn_frame, text="Add", command=self.add_pattern).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(btn_frame, text="Delete", command=self.delete_pattern).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(btn_frame, text="Save", command=self.save_patterns).pack(
            side=tk.LEFT, padx=2
        )

        # ------------------------------------------------------------------
        # Rules tab
        # ------------------------------------------------------------------
        rule_frame = ttk.Frame(nb)
        rule_frame.rowconfigure(0, weight=1)
        rule_frame.columnconfigure(0, weight=1)
        nb.add(rule_frame, text="Rules")

        r_tree_frame = ttk.Frame(rule_frame)
        r_tree_frame.grid(row=0, column=0, sticky="nsew")
        r_tree_frame.rowconfigure(0, weight=1)
        r_tree_frame.columnconfigure(0, weight=1)

        self.rule_tree = ttk.Treeview(
            r_tree_frame,
            columns=("idx", "label", "action", "subject", "template", "targets", "constraint"),
            show="headings",
        )
        for col, text in (
            ("idx", "#"),
            ("label", "Label"),
            ("action", "Action"),
            ("subject", "Subject"),
            ("template", "Template"),
            ("targets", "Targets"),
            ("constraint", "Constraint"),
        ):
            self.rule_tree.heading(col, text=text)
            if col == "idx":
                self.rule_tree.column(col, width=30, stretch=False, anchor="center")
            else:
                self.rule_tree.column(col, width=120, stretch=True)
        self.rule_tree.bind("<Double-1>", self._edit_rule)
        self.rule_tree.grid(row=0, column=0, sticky="nsew")

        rybar = ttk.Scrollbar(r_tree_frame, orient="vertical", command=self.rule_tree.yview)
        rxbar = ttk.Scrollbar(r_tree_frame, orient="horizontal", command=self.rule_tree.xview)
        self.rule_tree.configure(yscrollcommand=rybar.set, xscrollcommand=rxbar.set)
        rybar.grid(row=0, column=1, sticky="ns")
        rxbar.grid(row=1, column=0, sticky="ew")

        r_btn = ttk.Frame(rule_frame)
        r_btn.grid(row=1, column=0, sticky="e", pady=4, padx=4)
        ttk.Button(r_btn, text="Add", command=self.add_rule).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(r_btn, text="Delete", command=self.delete_rule).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(r_btn, text="Save", command=self.save_rules).pack(
            side=tk.LEFT, padx=2
        )

        # ------------------------------------------------------------------
        # Sequences tab
        # ------------------------------------------------------------------
        seq_frame = ttk.Frame(nb)
        seq_frame.rowconfigure(0, weight=1)
        seq_frame.columnconfigure(0, weight=1)
        nb.add(seq_frame, text="Sequences")

        s_tree_frame = ttk.Frame(seq_frame)
        s_tree_frame.grid(row=0, column=0, sticky="nsew")
        s_tree_frame.rowconfigure(0, weight=1)
        s_tree_frame.columnconfigure(0, weight=1)

        self.seq_tree = ttk.Treeview(
            s_tree_frame,
            columns=(
                "idx",
                "label",
                "relations",
                "action",
                "subject",
                "role_subject",
                "template",
            ),
            show="headings",
        )
        for col, text in (
            ("idx", "#"),
            ("label", "Label"),
            ("relations", "Relations"),
            ("action", "Action"),
            ("subject", "Subject"),
            ("role_subject", "Role Subject"),
            ("template", "Template"),
        ):
            self.seq_tree.heading(col, text=text)
            if col == "idx":
                self.seq_tree.column(col, width=30, stretch=False, anchor="center")
            else:
                self.seq_tree.column(col, width=120, stretch=True)
        self.seq_tree.bind("<Double-1>", self._edit_sequence)
        self.seq_tree.grid(row=0, column=0, sticky="nsew")

        sybar = ttk.Scrollbar(s_tree_frame, orient="vertical", command=self.seq_tree.yview)
        sxbar = ttk.Scrollbar(s_tree_frame, orient="horizontal", command=self.seq_tree.xview)
        self.seq_tree.configure(yscrollcommand=sybar.set, xscrollcommand=sxbar.set)
        sybar.grid(row=0, column=1, sticky="ns")
        sxbar.grid(row=1, column=0, sticky="ew")

        s_btn = ttk.Frame(seq_frame)
        s_btn.grid(row=1, column=0, sticky="e", pady=4, padx=4)
        ttk.Button(s_btn, text="Add", command=self.add_sequence).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(s_btn, text="Delete", command=self.delete_sequence).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(s_btn, text="Save", command=self.save_rules).pack(
            side=tk.LEFT, padx=2
        )

        self._populate_pattern_tree()
        self._populate_rule_tree()
        self._populate_seq_tree()

    # ------------------------------------------------------------------
    # Pattern helpers
    # ------------------------------------------------------------------
    def _populate_pattern_tree(self):
        self.tree.delete(*self.tree.get_children(""))
        wrapped: list[tuple[int, str, str]] = []
        max_lines = 1
        for idx, pat in enumerate(self.data):
            trig = textwrap.fill(pat.get("Trigger", ""), 40)
            tmpl_raw = pat.get("Template", "")
            act = _extract_action(pat.get("Trigger", ""))
            if act and act in tmpl_raw:
                tmpl_raw = tmpl_raw.replace(act, f"<action : {act}>")
            tmpl = textwrap.fill(tmpl_raw, 40)
            lines = max(trig.count("\n") + 1, tmpl.count("\n") + 1)
            max_lines = max(max_lines, lines)
            wrapped.append((idx, trig, tmpl))

        style = ttk.Style(self.tree)
        base = style.lookup("Treeview", "rowheight") or 20
        try:
            base_h = int(base)
        except Exception:
            base_h = 20
        style.configure("PatternTree.Treeview", rowheight=base_h * max_lines)
        self.tree.configure(style="PatternTree.Treeview")

        for idx, trig, tmpl in wrapped:
            self.tree.insert("", "end", iid=str(idx), values=(idx + 1, trig, tmpl))

    def _edit_item(self, _event=None):
        item = self.tree.focus()
        if not item:
            return
        idx = int(item)
        pat = self.data[idx]
        dlg = PatternConfig(self, pat)
        self.wait_window(dlg)
        if dlg.result is None:
            return
        pat.update(dlg.result)
        self._populate_pattern_tree()

    def add_pattern(self):
        self.data.append({})
        self._populate_pattern_tree()
        self.tree.selection_set(str(len(self.data) - 1))
        self._edit_item()

    def delete_pattern(self):
        item = self.tree.focus()
        if not item:
            return
        idx = int(item)
        del self.data[idx]
        self._populate_pattern_tree()

    def save_patterns(self):
        try:
            validate_requirement_patterns(self.data)
        except ValueError as exc:  # pragma: no cover - GUI feedback
            messagebox.showerror(
                "Requirement Patterns", f"Invalid configuration:\n{exc}"
            )
            return
        try:
            self.config_path.write_text(json.dumps(self.data, indent=2) + "\n")
            if hasattr(self.app, "reload_config"):
                self.app.reload_config()
            messagebox.showinfo("Requirement Patterns", "Configuration saved")
            self._populate_pattern_tree()
        except Exception as exc:  # pragma: no cover - GUI feedback
            messagebox.showerror(
                "Requirement Patterns", f"Failed to save configuration:\n{exc}"
            )
    # Backwards compatibility
    save = save_patterns

    # ------------------------------------------------------------------
    # Rule helpers
    # ------------------------------------------------------------------
    def _populate_rule_tree(self):
        self.rule_tree.delete(*self.rule_tree.get_children(""))
        for idx, (label, info) in enumerate(sorted(self.req_rules.items()), 1):
            tmpl = info.get("template", "")
            act = info.get("action", "")
            if act and act in tmpl:
                tmpl = tmpl.replace(act, f"<action : {act}>")
            self.rule_tree.insert(
                "",
                "end",
                iid=label,
                values=(
                    idx,
                    label,
                    act,
                    info.get("subject", ""),
                    tmpl,
                    info.get("targets", 1),
                    "yes" if info.get("constraint") else "",
                ),
            )

    def _edit_rule(self, _event=None):
        item = self.rule_tree.focus()
        if not item:
            return
        label = self.rule_tree.set(item, "label")
        info = dict(self.req_rules.get(label, {}))
        info["label"] = label
        dlg = RuleConfig(self, info)
        self.wait_window(dlg)
        if dlg.result is None:
            return
        new_label = dlg.result.pop("label")
        tgt = dlg.result.pop("targets", 1)
        if label in self.req_rules:
            del self.req_rules[label]
        if tgt > 1:
            dlg.result["targets"] = tgt
        self.req_rules[new_label] = dlg.result
        self._populate_rule_tree()

    def add_rule(self):
        dlg = RuleConfig(self, {})
        self.wait_window(dlg)
        if dlg.result is None:
            return
        label = dlg.result.pop("label")
        tgt = dlg.result.pop("targets", 1)
        if tgt > 1:
            dlg.result["targets"] = tgt
        self.req_rules[label] = dlg.result
        self._populate_rule_tree()

    def delete_rule(self):
        item = self.rule_tree.focus()
        if not item:
            return
        label = self.rule_tree.set(item, "label")
        if label in self.req_rules:
            del self.req_rules[label]
        self._populate_rule_tree()

    def save_rules(self):
        self._ensure_role_subject_variants()
        self.rules_cfg["requirement_rules"] = self.req_rules
        self.rules_cfg["requirement_sequences"] = self.req_seqs
        try:
            validate_diagram_rules(self.rules_cfg)
        except ValueError as exc:  # pragma: no cover - GUI feedback
            messagebox.showerror(
                "Requirement Rules", f"Invalid configuration:\n{exc}"
            )
            return
        try:
            self.rules_path.write_text(
                json.dumps(self.rules_cfg, indent=2) + "\n"
            )
            if hasattr(self.app, "reload_config"):
                self.app.reload_config()
            # Refresh patterns after regeneration
            try:
                self.data = load_requirement_patterns(self.config_path)
            except Exception:
                pass
            self._populate_pattern_tree()
            self._populate_seq_tree()
            messagebox.showinfo("Requirement Rules", "Configuration saved")
        except Exception as exc:  # pragma: no cover - GUI feedback
            messagebox.showerror(
                "Requirement Rules", f"Failed to save configuration:\n{exc}"
            )

    # ------------------------------------------------------------------
    # Sequence helpers
    # ------------------------------------------------------------------
    def _ensure_role_subject_variants(self) -> None:
        variants: dict[str, dict] = {}
        for label, info in list(self.req_seqs.items()):
            if info.get("role_subject") or label.endswith("_role_subject"):
                continue
            if info.get("subject"):
                role_label = f"{label}_role_subject"
                variant = dict(info)
                variant.pop("subject", None)
                variant["role_subject"] = True
                variants[role_label] = variant
        self.req_seqs.update(variants)

    def _populate_seq_tree(self):
        self._ensure_role_subject_variants()
        self.seq_tree.delete(*self.seq_tree.get_children(""))
        for idx, (label, info) in enumerate(sorted(self.req_seqs.items()), 1):
            rels = " -> ".join(info.get("relations", []))
            self.seq_tree.insert(
                "",
                "end",
                iid=label,
                values=(
                    idx,
                    label,
                    rels,
                    info.get("action", ""),
                    info.get("subject", ""),
                    "Y" if info.get("role_subject") else "",
                    info.get("template", ""),
                ),
            )

    def _edit_sequence(self, _event=None):
        item = self.seq_tree.focus()
        if not item:
            return
        label = self.seq_tree.set(item, "label")
        if label.endswith("_role_subject"):
            return
        info = dict(self.req_seqs.get(label, {}))
        info["label"] = label
        dlg = SequenceConfig(self, info)
        self.wait_window(dlg)
        if dlg.result is None:
            return
        new_label = dlg.result.pop("label")
        rels = dlg.result.pop("relations", [])
        if label in self.req_seqs:
            del self.req_seqs[label]
            self.req_seqs.pop(f"{label}_role_subject", None)
        dlg.result["relations"] = rels
        self.req_seqs[new_label] = dlg.result
        self._populate_seq_tree()

    def add_sequence(self):
        dlg = SequenceConfig(self, {})
        self.wait_window(dlg)
        if dlg.result is None:
            return
        label = dlg.result.pop("label")
        rels = dlg.result.pop("relations", [])
        dlg.result["relations"] = rels
        if label in self.req_seqs:
            del self.req_seqs[label]
        self.req_seqs.pop(f"{label}_role_subject", None)
        self.req_seqs[label] = dlg.result
        self._populate_seq_tree()

    def delete_sequence(self):
        item = self.seq_tree.focus()
        if not item:
            return
        label = self.seq_tree.set(item, "label")
        if label in self.req_seqs:
            del self.req_seqs[label]
        if label.endswith("_role_subject"):
            base_label = label[: -len("_role_subject")]
            self.req_seqs.pop(base_label, None)
        else:
            self.req_seqs.pop(f"{label}_role_subject", None)
        self._populate_seq_tree()
