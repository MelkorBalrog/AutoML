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

import tkinter as tk
from tkinter import ttk, simpledialog
from pathlib import Path
import json
import re
import tkinter.font as tkFont
from typing import Any

from config import load_report_template, validate_report_template
from gui.controls import messagebox
from gui.controls.mac_button_style import apply_translucid_button_style


def layout_report_template(
    data: dict[str, Any], page_width: int = 595, margin: int = 40, line_height: int = 16
):
    """Return layout instructions for *data*.

    The function is intentionally simple: text lines are stacked vertically and
    element placeholders are represented as boxes of fixed height.  It returns a
    tuple ``(items, height)`` where *items* is a list of dictionaries describing
    things to draw (text, title or element) and *height* is the total required
    canvas height.
    """

    items: list[dict[str, Any]] = []
    y = margin
    elements = data.get("elements", {})

    def _tokenize(text: str):
        replaced = text
        for placeholder in elements:
            replaced = replaced.replace(
                f"<{placeholder}>", f"[[[element:{placeholder}]]]"
            )
        replaced = re.sub(
            r'<img\s+src="([^"]+)"\s*/?>',
            lambda m: f"[[[img:{m.group(1)}]]]",
            replaced,
        )
        replaced = re.sub(
            r'<a\s+href="([^"]+)">([^<]*)</a>',
            lambda m: f"[[[link:{m.group(1)}|{m.group(2)}]]]",
            replaced,
        )
        return re.split(r"(\[\[\[[^\]]+\]\]\])", replaced)

    for sec in data.get("sections", []):
        title = sec.get("title", "")
        items.append({"type": "title", "text": title, "x": margin, "y": y})
        y += line_height
        content = sec.get("content", "")
        tokens = _tokenize(content)
        for tok in tokens:
            if not tok:
                continue
            if tok.startswith("[[[") and tok.endswith("]]]"):
                inner = tok[3:-3]
                if inner.startswith("element:"):
                    name = inner.split(":", 1)[1]
                    kind = elements.get(name, "")
                    items.append(
                        {
                            "type": "element",
                            "name": name,
                            "kind": kind,
                            "x": margin,
                            "y": y,
                        }
                    )
                    y += 100
                elif inner.startswith("img:"):
                    src = inner.split(":", 1)[1]
                    items.append({"type": "image", "src": src, "x": margin, "y": y})
                    y += 100
                elif inner.startswith("link:"):
                    href, text = inner.split(":", 1)[1].split("|", 1)
                    items.append(
                        {
                            "type": "link",
                            "href": href,
                            "text": text,
                            "x": margin,
                            "y": y,
                        }
                    )
                    y += line_height
            else:
                text = tok.replace("<br/>", "\n")
                for line in text.split("\n"):
                    items.append({"type": "text", "text": line, "x": margin, "y": y})
                    y += line_height
        y += line_height
    height = y + margin
    return items, height


class ElementDialog(simpledialog.Dialog):
    """Dialog for adding or editing a single element placeholder."""

    def __init__(self, parent, element: dict[str, str]):
        self.element = element
        super().__init__(parent, title="Element")

    def body(self, master):
        tk.Label(master, text="Name:").grid(row=0, column=0, padx=4, pady=4, sticky="e")
        self.name_var = tk.StringVar(value=self.element.get("name", ""))
        ttk.Entry(master, textvariable=self.name_var).grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        tk.Label(master, text="Type:").grid(row=1, column=0, padx=4, pady=4, sticky="e")
        self.type_var = tk.StringVar(value=self.element.get("type", ""))
        ttk.Entry(master, textvariable=self.type_var).grid(row=1, column=1, padx=4, pady=4, sticky="ew")
        master.columnconfigure(1, weight=1)
        return master

    def apply(self):
        self.result = {
            "name": self.name_var.get().strip(),
            "type": self.type_var.get().strip(),
        }


class ElementsDialog(simpledialog.Dialog):
    """Dialog for editing element placeholders."""

    def __init__(self, parent, elements: dict[str, str]):
        self.elements = dict(elements)
        super().__init__(parent, title="Edit Elements")

    def body(self, master):
        self.tree = ttk.Treeview(master, columns=("type",), show="headings")
        self.tree.heading("type", text="Type")
        self.tree.grid(row=0, column=0, columnspan=3, sticky="nsew")
        ybar = ttk.Scrollbar(master, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=ybar.set)
        ybar.grid(row=0, column=3, sticky="ns")

        btn_add = ttk.Button(master, text="Add", command=self._add)
        btn_add.grid(row=1, column=0, padx=2, pady=4, sticky="w")
        btn_edit = ttk.Button(master, text="Edit", command=self._edit)
        btn_edit.grid(row=1, column=1, padx=2, pady=4, sticky="w")
        btn_del = ttk.Button(master, text="Delete", command=self._delete)
        btn_del.grid(row=1, column=2, padx=2, pady=4, sticky="w")

        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)
        self._populate()
        return master

    def _populate(self):
        self.tree.delete(*self.tree.get_children(""))
        for name, kind in sorted(self.elements.items()):
            self.tree.insert("", "end", name, values=(kind,))

    def _add(self):
        dlg = ElementDialog(self, {})
        if dlg.result:
            self.elements[dlg.result["name"]] = dlg.result["type"]
            self._populate()

    def _edit(self):
        item = self.tree.focus()
        if not item:
            return
        dlg = ElementDialog(
            self, {"name": item, "type": self.elements.get(item, "")}
        )
        if dlg.result:
            if item in self.elements:
                del self.elements[item]
            self.elements[dlg.result["name"]] = dlg.result["type"]
            self._populate()

    def _delete(self):
        item = self.tree.focus()
        if item and item in self.elements:
            del self.elements[item]
            self._populate()

    def apply(self):
        self.result = self.elements


class SectionDialog(simpledialog.Dialog):
    """Dialog for editing a single section."""

    def __init__(self, parent, section: dict[str, str]):
        self.section = section
        super().__init__(parent, title="Edit Section")

    def body(self, master):
        tk.Label(master, text="Title:").grid(row=0, column=0, padx=4, pady=4, sticky="e")
        self.title_var = tk.StringVar(value=self.section.get("title", ""))
        ttk.Entry(master, textvariable=self.title_var).grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        tk.Label(master, text="Content:").grid(row=1, column=0, padx=4, pady=4, sticky="ne")
        self.content_txt = tk.Text(master, width=40, height=10)
        self.content_txt.insert("1.0", self.section.get("content", ""))
        self.content_txt.grid(row=1, column=1, padx=4, pady=4, sticky="nsew")
        tk.Label(
            master,
            text=(
                "Use <element_name> to insert configured elements. "
                "Use <img src=\"path\"/> for images and "
                "<a href=\"url\">text</a> for links."
            ),
        ).grid(row=2, column=0, columnspan=2, padx=4, pady=(0, 4), sticky="w")
        master.columnconfigure(1, weight=1)
        master.rowconfigure(1, weight=1)
        return master

    def apply(self):
        self.result = {
            "title": self.title_var.get().strip(),
            "content": self.content_txt.get("1.0", tk.END).strip(),
        }


class ReportTemplateEditor(tk.Frame):
    """Visual editor for PDF report template configuration."""

    def __init__(self, master, app, config_path: Path | None = None):
        super().__init__(master)
        apply_translucid_button_style()
        self.app = app
        self.config_path = Path(
            config_path
            or Path(__file__).resolve().parents[1]
            / "config"
            / "templates"
            / "product_report_template.json"
        )
        try:
            self.data = load_report_template(self.config_path)
        except Exception as exc:  # pragma: no cover - GUI fallback
            messagebox.showerror(
                "Report Template", f"Failed to load configuration:\n{exc}"
            )
            self.data = {"sections": [], "elements": {}}
        self.data.setdefault("elements", {})

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        paned = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        paned.grid(row=0, column=0, columnspan=2, sticky="nsew")

        tree_frame = ttk.Frame(paned)
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(tree_frame, show="tree headings")
        self.tree.heading("#0", text="Sections")
        self.tree.column("#0", width=200, stretch=False)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", self._edit_section)
        self.tree.grid(row=0, column=0, sticky="nsew")

        ybar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        xbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
        ybar.grid(row=0, column=1, sticky="ns")
        xbar.grid(row=1, column=0, sticky="ew")

        btn_frame = ttk.Frame(tree_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, sticky="ew")
        btn_add = ttk.Button(btn_frame, text="Add", command=self._add_section)
        btn_add.pack(side="left", padx=4, pady=4)
        btn_del = ttk.Button(btn_frame, text="Delete", command=self._delete_section)
        btn_del.pack(side="left", padx=4, pady=4)

        preview_frame = ttk.Frame(paned)
        preview_frame.rowconfigure(0, weight=1)
        preview_frame.columnconfigure(0, weight=1)

        self.preview = tk.Canvas(preview_frame, background="white")
        self.preview.grid(row=0, column=0, sticky="nsew")
        ybar2 = ttk.Scrollbar(preview_frame, orient="vertical", command=self.preview.yview)
        xbar2 = ttk.Scrollbar(preview_frame, orient="horizontal", command=self.preview.xview)
        self.preview.configure(yscrollcommand=ybar2.set, xscrollcommand=xbar2.set)
        ybar2.grid(row=0, column=1, sticky="ns")
        xbar2.grid(row=1, column=0, sticky="ew")

        paned.add(tree_frame, weight=1)
        paned.add(preview_frame, weight=3)
        elem_btn = ttk.Button(self, text="Elements...", command=self._edit_elements)
        elem_btn.grid(row=1, column=0, sticky="w", padx=4, pady=4)
        btn = ttk.Button(self, text="Save", command=self.save)
        btn.grid(row=1, column=1, sticky="e", padx=4, pady=4)

        self._populate_tree()
        self._render_preview()

    def _populate_tree(self):
        self.tree.delete(*self.tree.get_children(""))
        for idx, sec in enumerate(self.data.get("sections", [])):
            self.tree.insert("", "end", f"sec|{idx}", text=sec.get("title", ""))
        self._render_preview()

    def _on_select(self, _event=None):
        self._render_preview()

    def _edit_section(self, _event=None):
        item = self.tree.focus()
        if not item:
            return
        idx = int(item.split("|", 1)[1])
        section = self.data["sections"][idx]
        dlg = SectionDialog(self, section)
        if dlg.result:
            self.data["sections"][idx] = dlg.result
            self._populate_tree()
            self.tree.selection_set(item)

    def _add_section(self):
        dlg = SectionDialog(self, {})
        if dlg.result:
            self.data.setdefault("sections", [])
            self.data["sections"].append(dlg.result)
            self._populate_tree()
            idx = len(self.data["sections"]) - 1
            item = f"sec|{idx}"
            self.tree.selection_set(item)
            try:
                self.tree.focus(item)
            except Exception:
                pass

    def _delete_section(self):
        item = self.tree.focus()
        if not item:
            return
        idx = int(item.split("|", 1)[1])
        if 0 <= idx < len(self.data.get("sections", [])):
            del self.data["sections"][idx]
            self._populate_tree()

    def _edit_elements(self):
        dlg = ElementsDialog(self, self.data.get("elements", {}))
        if dlg.result is not None:
            self.data["elements"] = dlg.result
            self._render_preview()

    def save(self):
        try:
            validate_report_template(self.data)
        except Exception as exc:  # pragma: no cover - GUI fallback
            messagebox.showerror("Report Template", str(exc))
            return
        self.config_path.write_text(json.dumps(self.data, indent=2))
        self._render_preview()

    def _render_preview(self):  # pragma: no cover - requires Tk canvas
        self.preview.delete("all")
        items, height = layout_report_template(self.data)
        page_width = 595
        self.preview.config(scrollregion=(0, 0, page_width, height))
        self.preview.create_rectangle(1, 1, page_width - 1, height - 1, outline="#ccc")
        font = tkFont.Font(family="Arial", size=10)
        bold = tkFont.Font(family="Arial", size=10, weight="bold")
        for item in items:
            if item["type"] == "title":
                self.preview.create_text(item["x"], item["y"], text=item["text"], anchor="nw", font=bold)
            elif item["type"] == "text":
                self.preview.create_text(item["x"], item["y"], text=item["text"], anchor="nw", font=font)
            elif item["type"] == "element":
                w, h = 200, 80
                x, y = item["x"], item["y"]
                self.preview.create_rectangle(x, y, x + w, y + h, outline="black")
                self.preview.create_text(x + w / 2, y + h / 2, text=item["name"], font=font)
            elif item["type"] == "image":
                w, h = 200, 80
                x, y = item["x"], item["y"]
                self.preview.create_rectangle(x, y, x + w, y + h, outline="black")
                self.preview.create_text(x + w / 2, y + h / 2, text="Image", font=font)
            elif item["type"] == "link":
                self.preview.create_text(
                    item["x"],
                    item["y"],
                    text=item["text"],
                    anchor="nw",
                    font=font,
                    fill="blue",
                )
