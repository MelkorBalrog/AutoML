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

"""Explorer window for safety governance diagrams."""

import tkinter as tk
from tkinter import ttk, simpledialog
from gui.controls import messagebox
from gui import format_name_with_phase
from mainappsrc.models.sysml.sysml_repository import SysMLRepository
from dataclasses import dataclass, field
from typing import List, Dict
import re

from analysis.safety_management import SafetyManagementToolbox, GovernanceModule
from gui.utils.icon_factory import create_icon
from gui.styles.style_manager import StyleManager


def _strip_phase_suffix(name: str) -> str:
    """Return *name* without any trailing ``" (...)"`` phase text."""
    if not name:
        return ""
    return re.sub(r" \([^()]+\)$", "", name)


class SafetyManagementExplorer(tk.Frame):
    """Browse and organise safety governance diagrams in folders."""

    def __init__(self, master, app=None, toolbox: SafetyManagementToolbox | None = None):
        if isinstance(master, tk.Toplevel):
            container = master
        else:
            container = master
        super().__init__(container)
        self.app = app
        self.toolbox = toolbox or SafetyManagementToolbox()
        if isinstance(master, tk.Toplevel):
            master.title("Safety & Security Management Explorer")
            master.geometry("350x400")
            self.pack(fill=tk.BOTH, expand=True)

        btns = ttk.Frame(self)
        btns.pack(side=tk.TOP, fill=tk.X, padx=4, pady=4)
        ttk.Button(btns, text="Open", command=self.open_item).pack(side=tk.LEFT)
        ttk.Button(btns, text="New Folder", command=self.new_folder).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="New Diagram", command=self.new_diagram).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="Rename", command=self.rename_item).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="Delete", command=self.delete_item).pack(side=tk.LEFT, padx=2)
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

        self.folder_icon = self._create_icon("folder", _color("Lifecycle Phase", "#b8860b"))
        self.diagram_icon = self._create_icon("document", _color("Document", "#4682b4"))
        self.item_map: Dict[str, tuple[str, object]] = {}
        self.root_iid = ""

        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<ButtonPress-1>", self._on_drag_start)
        self.tree.bind("<ButtonRelease-1>", self._on_drop)
        self.populate()

    # ------------------------------------------------------------------
    def populate(self):
        """Fill the tree with folders and diagrams."""
        self.item_map.clear()
        self.tree.delete(*self.tree.get_children(""))
        self.toolbox.list_diagrams()
        repo = SysMLRepository.get_instance()

        self.root_iid = self.tree.insert(
            "", "end", text="Diagrams", image=self.folder_icon, open=True
        )
        self.item_map[self.root_iid] = ("root", None)

        def _add_module(parent: str, mod: GovernanceModule) -> None:
            for sub in mod.modules:
                label = _strip_phase_suffix(sub.name)
                sub_id = self.tree.insert(parent, "end", text=label, image=self.folder_icon)
                self.item_map[sub_id] = ("module", sub)
                _add_module(sub_id, sub)
            for name in mod.diagrams:
                plain = _strip_phase_suffix(name)
                diag_iid = self.tree.insert(parent, "end", text=plain, image=self.diagram_icon)
                # Store the full diagram name so lookups succeed even when the
                # displayed label omits phase information.
                self.item_map[diag_iid] = ("diagram", name)

        for mod in self.toolbox.modules:
            label = _strip_phase_suffix(mod.name)
            mod_id = self.tree.insert(
                self.root_iid, "end", text=label, image=self.folder_icon
            )
            self.item_map[mod_id] = ("module", mod)
            _add_module(mod_id, mod)

        for name in sorted(self.toolbox.diagrams.keys()):
            if not self._in_any_module(name, self.toolbox.modules):
                label = _strip_phase_suffix(name)
                iid = self.tree.insert(
                    self.root_iid, "end", text=label, image=self.diagram_icon
                )
                # As above, keep the real name mapped to the tree item so
                # actions can resolve the diagram identifier.
                self.item_map[iid] = ("diagram", name)

    # ------------------------------------------------------------------
    def refresh(self):
        """Refresh the explorer view to reflect the current model state."""
        self.populate()

    # ------------------------------------------------------------------
    def _refresh_diagram_list(self) -> None:
        """Update diagram dropdowns in the toolbox window, if present."""
        smw = getattr(getattr(self, "app", None), "safety_mgmt_window", None)
        if smw and hasattr(smw, "refresh_diagrams"):
            try:
                smw.refresh_diagrams()
            except Exception:
                pass

    # ------------------------------------------------------------------
    def new_folder(self):
        name = simpledialog.askstring("New Folder", "Name:", parent=self)
        if not name:
            return
        sel = self.tree.selection()
        if sel:
            typ, obj = self.item_map.get(sel[0], (None, None))
            if typ == "module" and obj is not None:
                self.toolbox.add_module(name, obj)
            else:  # root or other selections add to top level
                self.toolbox.add_module(name)
        else:
            self.toolbox.add_module(name)
        self.populate()

    # ------------------------------------------------------------------
    def new_diagram(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showerror(
                "New Diagram", "Please select a folder or the root for the diagram"
            )
            return
        typ, obj = self.item_map.get(sel[0], (None, None))
        if typ not in {"module", "root"}:
            messagebox.showerror(
                "New Diagram", "Please select a folder or the root for the diagram"
            )
            return
        name = simpledialog.askstring("New Diagram", "Name:", parent=self)
        if not name:
            return
        diag_id = self.toolbox.create_diagram(name)
        repo = SysMLRepository.get_instance()
        actual = repo.diagrams.get(diag_id).name
        if typ == "module" and obj is not None:
            obj.diagrams.append(actual)
        self.populate()
        self._refresh_diagram_list()

    # ------------------------------------------------------------------
    def rename_item(self):
        sel = self.tree.selection()
        if not sel:
            return
        typ, obj = self.item_map.get(sel[0], (None, None))
        if typ == "diagram":
            new = simpledialog.askstring(
                "Rename Diagram", "Name:", initialvalue=obj, parent=self
            )
            if not new or new == obj:
                return
            actual = self.toolbox.rename_diagram(obj, new)
            self._replace_name_in_modules(obj, actual, self.toolbox.modules)
        elif typ == "module":
            new = simpledialog.askstring(
                "Rename Folder", "Name:", initialvalue=obj.name, parent=self
            )
            if not new or new == obj.name:
                return
            self.toolbox.rename_module(obj.name, new)
        else:
            return
        self.populate()
        self._refresh_diagram_list()

    # ------------------------------------------------------------------
    def delete_item(self):
        sel = self.tree.selection()
        if not sel:
            return
        typ, obj = self.item_map.get(sel[0], (None, None))
        if typ == "diagram":
            self.toolbox.delete_diagram(obj)
            self._remove_name(obj, self.toolbox.modules)
        elif typ == "module":
            if obj.modules or obj.diagrams:
                return
            parent = self.tree.parent(sel[0])
            if parent:
                ptyp, pobj = self.item_map.get(parent, (None, None))
                if ptyp == "module":
                    pobj.modules.remove(obj)
            else:
                self.toolbox.modules.remove(obj)
        self.populate()
        self._refresh_diagram_list()

    # ------------------------------------------------------------------
    def open_item(self):
        sel = self.tree.selection()
        if not sel:
            return
        typ, obj = self.item_map.get(sel[0], (None, None))
        if typ != "diagram":
            return
        self.toolbox.list_diagrams()
        diag_id = self.toolbox.diagrams.get(obj)
        if not diag_id:
            messagebox.showerror("Open Diagram", f"Diagram '{obj}' not found")
            return
        if self.app:
            self.app.window_controllers.open_arch_window(diag_id)

    # ------------------------------------------------------------------
    def _on_double_click(self, _event):  # pragma: no cover - UI event
        self.open_item()

    # ------------------------------------------------------------------
    def _on_drag_start(self, event):  # pragma: no cover - UI event
        """Record the tree item being dragged."""
        iid = self.tree.identify_row(event.y)
        self._drag_item = iid if iid else None

    # ------------------------------------------------------------------
    def _on_drop(self, event):  # pragma: no cover - UI event
        """Handle dropping of a tree item onto another item or the root."""
        if not getattr(self, "_drag_item", None):
            return

        target = self.tree.identify_row(event.y)
        if target == self._drag_item:
            self._drag_item = None
            return

        item_type, item_obj = self.item_map.get(self._drag_item, (None, None))
        tgt_type, tgt_obj = self.item_map.get(target, (None, None))
        if tgt_type == "diagram":
            target = self.tree.parent(target)
            tgt_type, tgt_obj = self.item_map.get(target, (None, None))

        if target and tgt_type in {"module", "root"}:
            parent_mod = tgt_obj if tgt_type == "module" else None
            new_parent = target
        else:
            parent_mod = None
            new_parent = self.root_iid
        if SafetyManagementExplorer._is_descendant(self, new_parent, self._drag_item):
            self._drag_item = None
            return

        self.tree.move(self._drag_item, new_parent, "end")

        if item_type == "diagram":
            self._remove_name(item_obj, self.toolbox.modules)
            if parent_mod:
                parent_mod.diagrams.append(item_obj)
        elif item_type == "module":
            self._remove_module(item_obj, self.toolbox.modules)
            if parent_mod:
                parent_mod.modules.append(item_obj)
            else:
                self.toolbox.modules.append(item_obj)

        self._drag_item = None

    # ------------------------------------------------------------------
    def _is_descendant(self, item: str, ancestor: str) -> bool:
        """Return ``True`` if *item* is a descendant of *ancestor*."""
        while item:
            if item == ancestor:
                return True
            item = self.tree.parent(item)
        return False

    # ------------------------------------------------------------------
    def _in_any_module(self, name: str, mods: List[GovernanceModule]) -> bool:
        target = _strip_phase_suffix(name)
        for mod in mods:
            if any(_strip_phase_suffix(d) == target for d in mod.diagrams) or self._in_any_module(name, mod.modules):
                return True
        return False

    def _replace_name_in_modules(self, old: str, new: str, mods: List[GovernanceModule]) -> None:
        old_plain = _strip_phase_suffix(old)
        new_plain = _strip_phase_suffix(new)
        for mod in mods:
            mod.diagrams = [new_plain if _strip_phase_suffix(d) == old_plain else d for d in mod.diagrams]
            self._replace_name_in_modules(old_plain, new_plain, mod.modules)

    def _remove_name(self, name: str, mods: List[GovernanceModule]) -> None:
        target = _strip_phase_suffix(name)
        for mod in mods:
            mod.diagrams = [d for d in mod.diagrams if _strip_phase_suffix(d) != target]
            self._remove_name(name, mod.modules)

    def _remove_module(self, target: GovernanceModule, mods: List[GovernanceModule]) -> bool:
        for mod in mods:
            if mod is target:
                mods.remove(mod)
                return True
            if self._remove_module(target, mod.modules):
                return True
        return False

    # ------------------------------------------------------------------
    def _create_icon(self, shape: str, color: str = "black"):
        """Proxy to the shared icon factory."""
        return create_icon(shape, color)
