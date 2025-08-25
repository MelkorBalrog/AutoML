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
"""Clipboard management for diagram elements.

This module centralises copy, cut and paste behaviour for both the
analysis tree and all diagram windows.  The logic previously lived inside
``AutoMLApp`` but has been extracted into this dedicated helper to keep
``AutoMLApp`` small and focused on high level orchestration.
"""

from __future__ import annotations

import copy
import uuid
from typing import Iterable, Any

from gui.controls import messagebox
from mainappsrc.models.gsn.nodes import GSNNode, ALLOWED_AWAY_TYPES
from mainappsrc.models.fta.fault_tree_node import FaultTreeNode
from gui.windows.architecture import ARCH_WINDOWS
from . import config_utils

AutoML_Helper = config_utils.AutoML_Helper


class DiagramClipboardManager:
    """Manage node and diagram clipboard operations."""

    def __init__(self, app: Any) -> None:
        self.app = app
        self.clipboard_node: Any | None = None
        self.clipboard_relation: str | None = None
        self.cut_mode: bool = False
        self.diagram_clipboard: Any | None = None
        self.diagram_clipboard_type: str | None = None
        self.diagram_clipboard_parent_name: str | None = None

    # ------------------------------------------------------------------
    # Strategies for delegating to focused diagram windows
    def _diagram_copy_strategy1(self) -> bool:
        win = self.app.window_controllers._focused_cbn_window()
        if win and getattr(win, "selected_node", None) and getattr(win, "copy_selected", None):
            self.app.selected_node = None
            self.clipboard_node = None
            self.cut_mode = False
            win.copy_selected()
            return True
        return False

    def _diagram_copy_strategy2(self) -> bool:
        win = self.app.window_controllers._focused_gsn_window()
        if win and getattr(win, "selected_node", None) and getattr(win, "copy_selected", None):
            self.app.selected_node = None
            self.clipboard_node = None
            self.cut_mode = False
            win.copy_selected()
            return True
        return False

    def _diagram_copy_strategy3(self) -> bool:
        win = getattr(self.app, "active_arch_window", None)
        if win and getattr(win, "selected_obj", None) and getattr(win, "copy_selected", None):
            self.app.selected_node = None
            self.clipboard_node = None
            self.cut_mode = False
            win.copy_selected()
            return True
        return False

    def _diagram_copy_strategy4(self) -> bool:
        for ref in list(ARCH_WINDOWS):
            win = ref()
            if win and getattr(win, "selected_obj", None) and getattr(win, "copy_selected", None):
                self.app.selected_node = None
                self.clipboard_node = None
                self.cut_mode = False
                win.copy_selected()
                return True
        return False

    def _diagram_cut_strategy1(self) -> bool:
        win = self.app.window_controllers._focused_cbn_window()
        if win and getattr(win, "selected_node", None) and getattr(win, "cut_selected", None):
            self.app.selected_node = None
            self.clipboard_node = None
            self.cut_mode = False
            win.cut_selected()
            return True
        return False

    def _diagram_cut_strategy2(self) -> bool:
        win = self.app.window_controllers._focused_gsn_window()
        if win and getattr(win, "selected_node", None) and getattr(win, "cut_selected", None):
            self.app.selected_node = None
            self.clipboard_node = None
            self.cut_mode = False
            win.cut_selected()
            return True
        return False

    def _diagram_cut_strategy3(self) -> bool:
        win = getattr(self.app, "active_arch_window", None)
        if win and getattr(win, "selected_obj", None) and getattr(win, "cut_selected", None):
            self.app.selected_node = None
            self.clipboard_node = None
            self.cut_mode = False
            win.cut_selected()
            return True
        return False

    def _diagram_cut_strategy4(self) -> bool:
        for ref in list(ARCH_WINDOWS):
            win = ref()
            if win and getattr(win, "selected_obj", None) and getattr(win, "cut_selected", None):
                self.app.selected_node = None
                self.clipboard_node = None
                self.cut_mode = False
                win.cut_selected()
                return True
        return False

    # ------------------------------------------------------------------
    def _reset_gsn_clone(self, node: Any) -> None:
        if isinstance(node, GSNNode):
            node.unique_id = str(uuid.uuid4())
            old_children = list(getattr(node, "children", []))
            node.children = []
            node.parents = []
            node.context_children = []
            node.is_primary_instance = False
            if getattr(node, "original", None) is None:
                node.original = node
            for child in old_children:
                self._reset_gsn_clone(child)

    def _clone_for_paste_strategy1(self, node: Any, parent: Any | None = None):
        if hasattr(node, "clone"):
            if parent and getattr(node, "node_type", None) in {"Context", "Assumption", "Justification"}:
                return node.clone(parent)
            return node.clone()
        clone = copy.deepcopy(node)
        self._reset_gsn_clone(clone)
        return clone

    def _clone_for_paste_strategy2(self, node: Any, parent: Any | None = None):
        if isinstance(node, GSNNode):
            if parent and node.node_type in {"Context", "Assumption", "Justification"}:
                return node.clone(parent)
            return node.clone()
        clone = copy.deepcopy(node)
        self._reset_gsn_clone(clone)
        return clone

    def _clone_for_paste_strategy3(self, node: Any, parent: Any | None = None):
        try:
            if parent and getattr(node, "node_type", None) in {"Context", "Assumption", "Justification"}:
                return node.clone(parent)  # type: ignore[attr-defined]
            return node.clone()  # type: ignore[attr-defined]
        except Exception:
            clone = copy.deepcopy(node)
            self._reset_gsn_clone(clone)
            return clone

    def _clone_for_paste_strategy4(self, node: Any, parent: Any | None = None):
        clone = copy.deepcopy(node)
        self._reset_gsn_clone(clone)
        return clone

    def _clone_for_paste(self, node: Any, parent: Any | None = None):
        for strat in (
            self._clone_for_paste_strategy1,
            self._clone_for_paste_strategy2,
            self._clone_for_paste_strategy3,
            self._clone_for_paste_strategy4,
        ):
            try:
                clone = strat(node, parent)
                if clone is not None:
                    return clone
            except ValueError:
                messagebox.showwarning("Clone", "Cannot clone this node type.")
                return None
            except Exception:
                continue
        messagebox.showwarning("Clone", "Cannot clone this node type.")
        return None

    def _prepare_node_for_paste(self, target):
        if isinstance(self.clipboard_node, GSNNode) and target in getattr(self.clipboard_node, "parents", []):
            return self._clone_for_paste(self.clipboard_node)
        if isinstance(self.clipboard_node, FaultTreeNode) or type(self.clipboard_node).__name__ == "FaultTreeNode":
            return self._clone_for_paste(self.clipboard_node)
        return self.clipboard_node

    # ------------------------------------------------------------------
    def copy_node(self) -> None:
        for strat in (
            self._diagram_copy_strategy1,
            self._diagram_copy_strategy2,
            self._diagram_copy_strategy3,
            self._diagram_copy_strategy4,
        ):
            if strat():
                return
        node = self.app.selected_node
        if (node is None or node == self.app.root_node) and hasattr(self.app, "analysis_tree"):
            sel = self.app.analysis_tree.selection()
            if sel:
                tags = self.app.analysis_tree.item(sel[0], "tags")
                if tags:
                    node = self.app.find_node_by_id(self.app.root_node, int(tags[0]))
        if node and node != self.app.root_node:
            self.clipboard_node = node
            self.app.selected_node = node
            self.cut_mode = False
            if node.parents:
                parent = node.parents[0]
                context_children = getattr(parent, "context_children", [])
                rel = "context" if node in context_children else "solved"
            else:
                rel = "solved"
            self.clipboard_relation = rel
            return
        messagebox.showwarning("Copy", "Select a non-root node to copy.")

    def cut_node(self) -> None:
        for strat in (
            self._diagram_cut_strategy1,
            self._diagram_cut_strategy2,
            self._diagram_cut_strategy3,
            self._diagram_cut_strategy4,
        ):
            if strat():
                return
        node = self.app.selected_node
        if (node is None or node == self.app.root_node) and hasattr(self.app, "analysis_tree"):
            sel = self.app.analysis_tree.selection()
            if sel:
                tags = self.app.analysis_tree.item(sel[0], "tags")
                if tags:
                    node = self.app.find_node_by_id(self.app.root_node, int(tags[0]))
        if node and node != self.app.root_node:
            self.clipboard_node = node
            self.app.selected_node = node
            self.cut_mode = True
            if node.parents:
                parent = node.parents[0]
                context_children = getattr(parent, "context_children", [])
                rel = "context" if node in context_children else "solved"
            else:
                rel = "solved"
            self.clipboard_relation = rel
            return
        if getattr(self.app, "active_arch_window", None) or ARCH_WINDOWS:
            return
        messagebox.showwarning("Cut", "Select a non-root node to cut.")

    # ------------------------------------------------------------------
    def paste_node(self) -> None:
        if self.clipboard_node:
            target = None
            sel = self.app.analysis_tree.selection()
            if sel:
                tags = self.app.analysis_tree.item(sel[0], "tags")
                if tags:
                    target = self.app.find_node_by_id(self.app.root_node, int(tags[0]))
            if not target:
                target = self.app.selected_node or self.app.root_node
            if not target:
                win = self.app.window_controllers._focused_gsn_window()
                if win and getattr(win, "diagram", None):
                    target = win.diagram.root
            if not target:
                win = self.app.window_controllers._focused_cbn_window()
                if win and getattr(win, "diagram", None):
                    target = win.diagram.root
            if not target:
                target = self.app.root_node
            if not target:
                win = self.app.window_controllers._focused_gsn_window()
                if win and getattr(win, "diagram", None):
                    target = win.diagram.root
            if not target:
                win = self.app.window_controllers._focused_cbn_window()
                if win and getattr(win, "diagram", None):
                    target = win.diagram.root
            if not target:
                messagebox.showwarning("Paste", "Select a target node to paste into.")
                return
            if target.node_type.upper() in ["CONFIDENCE LEVEL", "ROBUSTNESS SCORE"]:
                messagebox.showwarning("Paste", "Cannot paste into a base event.")
                return
            if not target.is_primary_instance:
                target = target.original
            if target.unique_id == self.clipboard_node.unique_id:
                messagebox.showwarning("Paste", "Cannot paste a node onto itself.")
                return
            if self.cut_mode:
                for child in target.children:
                    if child.unique_id == self.clipboard_node.unique_id:
                        messagebox.showwarning(
                            "Paste", "This node is already a child of the target."
                        )
                        return
            if self.cut_mode:
                if self.clipboard_node in self.app.top_events:
                    self.app.top_events.remove(self.clipboard_node)
                for p in list(self.clipboard_node.parents):
                    if self.clipboard_node in p.children:
                        p.children.remove(self.clipboard_node)
                self.clipboard_node.parents = []
                if self.clipboard_node.node_type.upper() == "TOP EVENT":
                    self.clipboard_node.node_type = "RIGOR LEVEL"
                    self.clipboard_node.severity = None
                    self.clipboard_node.is_page = False
                    self.clipboard_node.input_subtype = "Failure"
                self.clipboard_node.is_primary_instance = True
                relation = getattr(self, "clipboard_relation", "solved")
                if hasattr(target, "add_child"):
                    target.add_child(self.clipboard_node, relation=relation)
                else:
                    if relation == "context":
                        target.context_children.append(self.clipboard_node)
                    else:
                        target.children.append(self.clipboard_node)
                    self.clipboard_node.parents.append(target)
                if isinstance(self.clipboard_node, GSNNode):
                    old_diag = self._find_gsn_diagram(self.clipboard_node)
                    new_diag = self._find_gsn_diagram(target)
                    if old_diag and old_diag is not new_diag and self.clipboard_node in old_diag.nodes:
                        old_diag.nodes.remove(self.clipboard_node)
                    if new_diag and self.clipboard_node not in new_diag.nodes:
                        new_diag.add_node(self.clipboard_node)
                self.clipboard_node.x = target.x + 100
                self.clipboard_node.y = target.y + 100
                self.clipboard_node.display_label = self.clipboard_node.display_label.replace(
                    " (clone)", ""
                )
                self.clipboard_node = None
                self.cut_mode = False
                messagebox.showinfo("Paste", "Node moved successfully (cut & pasted).")
            else:
                target_diag = self._find_gsn_diagram(target)
                node_for_pos = self._prepare_node_for_paste(target)
                target.children.append(node_for_pos)
                node_for_pos.parents.append(target)
                if isinstance(node_for_pos, GSNNode):
                    if target_diag and node_for_pos not in target_diag.nodes:
                        target_diag.add_node(node_for_pos)
                node_for_pos.x = target.x + 100
                node_for_pos.y = target.y + 100
                if hasattr(node_for_pos, "display_label"):
                    node_for_pos.display_label = node_for_pos.display_label.replace(
                        " (clone)", ""
                    )
                messagebox.showinfo("Paste", "Node pasted successfully (copied).")
            try:
                AutoML_Helper.calculate_assurance_recursive(
                    self.app.root_node,
                    self.app.top_events,
                )
            except AttributeError:
                pass
            self.app.update_views()
            return
        clip_type = getattr(self, "diagram_clipboard_type", None)
        win = self.app.window_controllers._focused_cbn_window()
        if win and getattr(self, "diagram_clipboard", None):
            if not clip_type or clip_type == "Causal Bayesian Network":
                if getattr(win, "paste_selected", None):
                    win.paste_selected()
                    return
        win = self.app.window_controllers._focused_gsn_window()
        if win and getattr(self, "diagram_clipboard", None):
            if not clip_type or clip_type == "GSN":
                if getattr(win, "paste_selected", None):
                    win.paste_selected()
                    return
        win = self.app.window_controllers._focused_arch_window(clip_type)
        if win and getattr(self, "diagram_clipboard", None):
            if getattr(win, "paste_selected", None):
                win.paste_selected()
                return
        messagebox.showwarning("Paste", "Clipboard is empty.")

    # ------------------------------------------------------------------
    def _copy_attrs_no_xy_strategy1(self, target, source, attrs: Iterable[str]):
        tx, ty = getattr(target, "x", None), getattr(target, "y", None)
        for attr in attrs:
            setattr(target, attr, getattr(source, attr, None))
        if tx is not None:
            target.x = tx
        if ty is not None:
            target.y = ty

    def _copy_attrs_no_xy_strategy2(self, target, source, attrs: Iterable[str]):
        tx, ty = getattr(target, "x", None), getattr(target, "y", None)
        values = {a: getattr(source, a, None) for a in attrs if hasattr(source, a)}
        for a, v in values.items():
            setattr(target, a, v)
        if tx is not None:
            target.x = tx
        if ty is not None:
            target.y = ty

    def _copy_attrs_no_xy_strategy3(self, target, source, attrs: Iterable[str]):
        tx, ty = getattr(target, "x", None), getattr(target, "y", None)
        for attr in attrs:
            if attr in {"x", "y"}:
                continue
            setattr(target, attr, getattr(source, attr, None))
        if tx is not None:
            target.x = tx
        if ty is not None:
            target.y = ty

    def _copy_attrs_no_xy_strategy4(self, target, source, attrs: Iterable[str]):
        tx, ty = getattr(target, "x", None), getattr(target, "y", None)
        for attr in attrs:
            try:
                setattr(target, attr, getattr(source, attr))
            except Exception:
                continue
        if tx is not None:
            target.x = tx
        if ty is not None:
            target.y = ty

    def _copy_attrs_no_xy(self, target, source, attrs: Iterable[str]):
        for strat in (
            self._copy_attrs_no_xy_strategy1,
            self._copy_attrs_no_xy_strategy2,
            self._copy_attrs_no_xy_strategy3,
            self._copy_attrs_no_xy_strategy4,
        ):
            try:
                strat(target, source, attrs)
                return
            except Exception:
                continue

    # ------------------------------------------------------------------
    def _find_gsn_diagram(self, node):
        for diag in getattr(self.app, "gsn_diagrams", []):
            if node in getattr(diag, "nodes", []):
                return diag

        def _search_modules(modules):
            for mod in modules:
                for diag in getattr(mod, "diagrams", []):
                    if node in getattr(diag, "nodes", []):
                        return diag
                result = _search_modules(getattr(mod, "modules", []))
                if result:
                    return result
            return None

        return _search_modules(getattr(self.app, "gsn_modules", []))

    def _get_diag_type(self, win):
        repo = getattr(win, "repo", None)
        diag_id = getattr(win, "diagram_id", None)
        if repo and diag_id:
            diag = repo.diagrams.get(diag_id)
            if diag:
                return diag.diag_type
        return None
