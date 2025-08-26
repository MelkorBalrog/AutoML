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

"""Editing and styling helpers extracted from AutoML core.

This module defines :class:`Editing_Labels_Styling` which groups together
label editing and styling utilities that previously lived directly on
``AutoMLApp``.  The helper delegates attribute access back to the parent
application instance so existing code can continue to call these methods
without modification.
"""


from pathlib import Path
import tkinter as tk
from tkinter import simpledialog

from gui.controls import messagebox
from gui.dialogs.dialog_utils import askstring_fixed
from .style_manager import StyleManager
from gui.utils.icon_factory import create_icon
from gui.dialogs.edit_node_dialog import EditNodeDialog


class Editing_Labels_Styling:
    """Collection of label editing and styling helpers."""

    def __init__(self, app) -> None:
        self.app = app

    def __getattr__(self, name):  # pragma: no cover - simple delegation
        return getattr(self.app, name)

    # ------------------------------------------------------------------
    # Methods migrated from ``AutoMLApp``
    # ------------------------------------------------------------------
    def edit_controllability(self):
        messagebox.showinfo(
            "Controllability",
            "Controllability is determined from the risk assessment and cannot be edited here.",
        )

    def edit_description(self):
        if self.selected_node:
            new_desc = askstring_fixed(
                simpledialog,
                "Edit Description",
                "Enter new description:",
                initialvalue=self.selected_node.description,
            )
            if new_desc is not None:
                self.selected_node.description = new_desc
                # Propagate the updated description across clones/original.
                self.sync_nodes_by_id(self.selected_node)
                self.update_views()
        else:
            messagebox.showwarning("Edit Description", "Select a node first.")

    def edit_gate_type(self):
        if self.selected_node and self.selected_node.node_type.upper() in self.GATE_NODE_TYPES:
            new_gt = simpledialog.askstring(
                "Edit Gate Type",
                "Enter new gate type (AND/OR):",
                initialvalue=self.selected_node.gate_type,
            )
            if new_gt is not None and new_gt.upper() in ["AND", "OR"]:
                self.selected_node.gate_type = new_gt.upper()
                # Reflect gate type changes everywhere.
                self.sync_nodes_by_id(self.selected_node)
                self.update_views()
            else:
                messagebox.showerror("Error", "Gate type must be AND or OR.")
        else:
            messagebox.showwarning("Edit Gate Type", "Select a gate-type node.")

    def edit_page_flag(self):
        if not self.selected_node:
            messagebox.showwarning("Edit Page Flag", "Select a node first.")
            return
        # If this is a clone, update its original.
        target = (
            self.selected_node
            if self.selected_node.is_primary_instance
            else self.selected_node.original
        )

        if target.node_type.upper() in ["TOP EVENT", "BASIC EVENT"]:
            messagebox.showwarning("Edit Page Flag", "This node type cannot be a page.")
            return

        # Ask for the new page flag value.
        response = messagebox.askyesno(
            "Edit Page Flag", f"Should node '{target.name}' be a page gate?"
        )
        target.is_page = response

        # Sync the changes to all clones.
        self.sync_nodes_by_id(target)
        self.update_views()

    def edit_rationale(self):
        if self.selected_node:
            new_rat = simpledialog.askstring(
                "Edit Rationale",
                "Enter new rationale:",
                initialvalue=self.selected_node.rationale,
            )
            if new_rat is not None:
                self.selected_node.rationale = new_rat
                # Synchronize rationale changes with related clones.
                self.sync_nodes_by_id(self.selected_node)
                self.update_views()
        else:
            messagebox.showwarning("Edit Rationale", "Select a node first.")

    def edit_selected(self):
        sel = self.analysis_tree.selection()
        target = None
        if sel:
            try:
                node_id = int(self.analysis_tree.item(sel[0], "tags")[0])
            except (IndexError, ValueError):
                return
            target = self.find_node_by_id_all(node_id)
        elif self.selected_node:
            target = self.selected_node
        if not target:
            messagebox.showwarning("No selection", "Select a node to edit.")
            return

        # If the node is a clone, resolve it to its original.
        if (
            not target.is_primary_instance
            and hasattr(target, "original")
            and target.original
        ):
            target = target.original

        EditNodeDialog(self.root, target, self)
        self.update_views()

    def edit_user_name(self):
        self.user_manager.edit_user_name()

    def edit_value(self):
        if self.selected_node and self.selected_node.node_type.upper() in [
            "CONFIDENCE LEVEL",
            "ROBUSTNESS SCORE",
        ]:
            try:
                new_val = simpledialog.askfloat(
                    "Edit Value",
                    "Enter new value (1-5):",
                    initialvalue=self.selected_node.quant_value,
                )
                if new_val is not None and 1 <= new_val <= 5:
                    self.selected_node.quant_value = new_val
                    # Keep all nodes sharing this ID up to date.
                    self.sync_nodes_by_id(self.selected_node)
                    self.update_views()
                else:
                    messagebox.showerror("Error", "Value must be between 1 and 5.")
            except Exception:
                messagebox.showerror("Error", "Invalid input.")
        else:
            messagebox.showwarning(
                "Edit Value", "Select a Confidence or Robustness node."
            )

    def rename_failure(self, old: str, new: str) -> None:
        return self.risk_app.rename_failure(self, old, new)

    def rename_fault(self, old: str, new: str) -> None:
        return self.risk_app.rename_fault(self, old, new)

    def rename_functional_insufficiency(self, old: str, new: str) -> None:
        return self.risk_app.rename_functional_insufficiency(self, old, new)

    def rename_hazard(self, old: str, new: str) -> None:
        return self.risk_app.rename_hazard(self, old, new)

    def rename_malfunction(self, old: str, new: str) -> None:
        return self.risk_app.rename_malfunction(self, old, new)

    def rename_selected_tree_item(self):
        self.tree_app.rename_selected_tree_item(self)

    def rename_triggering_condition(self, old: str, new: str) -> None:
        return self.risk_app.rename_triggering_condition(self, old, new)

    def apply_style(self, filename: str) -> None:
        path = (
            Path(__file__).resolve().parents[2]
            / "config"
            / "styles"
            / filename
        )
        StyleManager.get_instance().load_style(path)
        self.root.event_generate("<<StyleChanged>>", when="tail")

    def format_failure_mode_label(self, node):
        comp = self.get_component_name_for_node(node)
        label = (
            node.description
            if node.description
            else (node.user_name or f"Node {node.unique_id}")
        )
        return f"{comp}: {label}" if comp else label

    def _resize_prop_columns(self, event: tk.Event | None = None) -> None:
        """Resize property view columns so the value column fills the tab."""
        if not hasattr(self, "prop_view"):
            return

        # Determine the width of the containing frame rather than the treeview
        # itself, as the tree may not yet have expanded to the full tab width.
        container = self.prop_view.master
        container.update_idletasks()
        tree_width = container.winfo_width()
        field_width = self.prop_view.column("field")["width"]

        # If the container hasn't been fully laid out yet (width too small),
        # try again on the next loop iteration so the value column starts at
        # the full tab width. DO NOT REMOVE.
        if tree_width <= field_width + 1:
            self.prop_view.after(50, self._resize_prop_columns)
            return
        new_width = max(tree_width - field_width, 20)
        self.prop_view.column("value", width=new_width, stretch=True)

    def _spi_label(self, sg):
        """Return a human-readable label for a product goal's SPI."""
        return (
            getattr(sg, "validation_desc", "")
            or getattr(sg, "safety_goal_description", "")
            or getattr(sg, "user_name", "")
            or f"SG {getattr(sg, 'unique_id', '')}"
        )

    def _product_goal_name(self, sg) -> str:
        """Return the display name for a product goal."""
        return getattr(sg, "user_name", "") or f"SG {getattr(sg, 'unique_id', '')}"

    def _create_icon(self, shape: str, color: str) -> tk.PhotoImage:
        """Delegate icon creation to the shared icon factory."""
        return create_icon(shape, color)

