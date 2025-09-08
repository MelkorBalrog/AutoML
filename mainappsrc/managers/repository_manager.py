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

"""Utilities for managing SysML and FTA repositories."""

import tkinter as tk
from tkinter import ttk
from typing import Optional

from gui.styles.style_manager import StyleManager
from mainappsrc.models.sysml.sysml_repository import SysMLRepository
from gui.windows.architecture import (
    UseCaseDiagramWindow,
    ActivityDiagramWindow,
    BlockDiagramWindow,
    InternalBlockDiagramWindow,
    ControlFlowDiagramWindow,
    GovernanceDiagramWindow,
)
from gui.utils.dockable_diagram_window import DockableDiagramWindow


class RepositoryManager:
    """Handle operations on SysML and FTA repositories.

    This class centralises logic that previously lived on ``AutoMLApp`` for
    opening diagrams, capturing SysML content and managing FTA specific state.
    ``AutoMLApp`` now delegates repository related responsibilities to this
    manager which simplifies the main application class and improves
    separation of concerns.
    """

    def __init__(self, app: "AutoMLApp") -> None:
        self.app = app

    # ------------------------------------------------------------------
    # SysML repository helpers
    # ------------------------------------------------------------------
    def capture_sysml_diagram(self, diagram):
        """Return a PIL Image of the given SysML diagram."""
        from io import BytesIO
        from PIL import Image
        from gui.causal_bayesian_network_window import (
            CausalBayesianNetworkWindow,
        )

        temp = tk.Toplevel(self.app.root)
        temp.withdraw()
        if diagram.diag_type == "Use Case Diagram":
            win = UseCaseDiagramWindow(temp, self.app, diagram_id=diagram.diag_id)
        elif diagram.diag_type == "Activity Diagram":
            win = ActivityDiagramWindow(temp, self.app, diagram_id=diagram.diag_id)
        elif diagram.diag_type == "Block Diagram":
            win = BlockDiagramWindow(temp, self.app, diagram_id=diagram.diag_id)
        elif diagram.diag_type == "Internal Block Diagram":
            win = InternalBlockDiagramWindow(temp, self.app, diagram_id=diagram.diag_id)
        elif diagram.diag_type == "Control Flow Diagram":
            win = ControlFlowDiagramWindow(temp, self.app, diagram_id=diagram.diag_id)
        elif diagram.diag_type == "Governance Diagram":
            win = GovernanceDiagramWindow(temp, self.app, diagram_id=diagram.diag_id)
        else:
            temp.destroy()
            return None

        win.redraw()
        win.canvas.update()
        bbox = win.canvas.bbox("all")
        if not bbox:
            temp.destroy()
            return None

        x, y, x2, y2 = bbox
        width, height = x2 - x, y2 - y
        ps = win.canvas.postscript(colormode="color", x=x, y=y, width=width, height=height)
        ps_bytes = BytesIO(ps.encode("utf-8"))
        try:
            img = Image.open(ps_bytes)
            img.load(scale=3)
        except Exception:
            img = None
        temp.destroy()
        return img.convert("RGB") if img else None

    def open_arch_window(self, diag_id: str) -> None:
        """Open an existing architecture diagram from the repository."""
        self.app.window_controllers.open_arch_window(diag_id)

    def open_management_window(self, idx: int) -> None:
        """Open a safety management diagram from the repository."""
        if idx < 0 or idx >= len(self.app.management_diagrams):
            return
        diag = self.app.management_diagrams[idx]
        existing = self.app.diagram_tabs.get(diag.diag_id)
        if existing and str(existing) in self.app.doc_nb.tabs():
            if existing.winfo_exists():
                self.app.doc_nb.select(existing)
                self.app.refresh_all()
                return
        else:
            self.app.diagram_tabs.pop(diag.diag_id, None)
        tab = self.app._new_tab(self.app._format_diag_title(diag))
        self.app.diagram_tabs[diag.diag_id] = tab
        if diag.diag_type == "Use Case Diagram":
            UseCaseDiagramWindow(tab, self.app, diagram_id=diag.diag_id)
        elif diag.diag_type == "Activity Diagram":
            ActivityDiagramWindow(tab, self.app, diagram_id=diag.diag_id)
        elif diag.diag_type == "Governance Diagram":
            GovernanceDiagramWindow(tab, self.app, diagram_id=diag.diag_id)
        elif diag.diag_type == "Block Diagram":
            BlockDiagramWindow(tab, self.app, diagram_id=diag.diag_id)
        elif diag.diag_type == "Internal Block Diagram":
            InternalBlockDiagramWindow(tab, self.app, diagram_id=diag.diag_id)
        elif diag.diag_type == "Control Flow Diagram":
            ControlFlowDiagramWindow(tab, self.app, diagram_id=diag.diag_id)
        self.app.refresh_all()

    # ------------------------------------------------------------------
    # FTA repository helpers
    # ------------------------------------------------------------------
    def _create_fta_tab(self, diagram_mode: str = "FTA"):
        """Create the main FTA tab with canvas and bindings."""
        tabs = getattr(self.app, "analysis_tabs", {})
        existing = tabs.get(diagram_mode)

        if existing and existing["tab"].winfo_exists():
            self.app.canvas_tab = existing["tab"]
            self.app.canvas_frame = existing["tab"]
            self.app.canvas = existing["canvas"]
            self.app.hbar = existing["hbar"]
            self.app.vbar = existing["vbar"]
            self.app.diagram_mode = diagram_mode
            self.app.doc_nb.select(self.app.canvas_tab)
            self.app._update_analysis_menus(diagram_mode)
            return

        dock_window = DockableDiagramWindow(self.app.doc_nb)
        canvas_tab = dock_window.content_frame
        canvas_tab._dock_window = dock_window
        title = "FTA" if diagram_mode == "FTA" else diagram_mode
        dock_window.dock(self.app.doc_nb, len(self.app.doc_nb.tabs()), title)

        canvas = tk.Canvas(canvas_tab, bg=StyleManager.get_instance().canvas_bg)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        hbar = ttk.Scrollbar(canvas_tab, orient=tk.HORIZONTAL, command=canvas.xview)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        vbar = ttk.Scrollbar(canvas_tab, orient=tk.VERTICAL, command=canvas.yview)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set, scrollregion=(0, 0, 2000, 2000))
        canvas.bind("<ButtonPress-3>", self.app.on_right_mouse_press)
        canvas.bind("<B3-Motion>", self.app.on_right_mouse_drag)
        canvas.bind("<ButtonRelease-3>", self.app.on_right_mouse_release)
        canvas.bind("<Button-1>", self.app.on_canvas_click)
        canvas.bind("<B1-Motion>", self.app.on_canvas_drag)
        canvas.bind("<ButtonRelease-1>", self.app.on_canvas_release)
        canvas.bind("<Double-1>", self.app.on_canvas_double_click)
        canvas.bind("<Control-MouseWheel>", self.app.on_ctrl_mousewheel)

        canvas.diagram_mode = diagram_mode
        self.app.analysis_tabs[diagram_mode] = {
            "tab": canvas_tab,
            "canvas": canvas,
            "hbar": hbar,
            "vbar": vbar,
            "dock_window": dock_window,
        }
        self.app.canvas_tab = canvas_tab
        self.app.canvas_frame = canvas_tab
        self.app.canvas = canvas
        self.app.hbar = hbar
        self.app.vbar = vbar
        self.app.diagram_mode = diagram_mode
        self.app.doc_nb.select(canvas_tab)
        self.app._update_analysis_menus(diagram_mode)

    def create_fta_diagram(self):
        """Initialize an FTA diagram and its top-level event."""
        self._create_fta_tab("FTA")
        self.app.add_top_level_event()
        if getattr(self.app, "fta_root_node", None):
            self.app.window_controllers.open_page_diagram(self.app.fta_root_node)

    def enable_fta_actions(self, enabled: bool) -> None:
        """Enable or disable FTA-related menu actions."""
        mode = getattr(self.app, "diagram_mode", "FTA")
        if hasattr(self.app, "fta_menu"):
            state = tk.NORMAL if enabled else tk.DISABLED
            for key in (
                "add_gate",
                "add_basic_event",
                "add_gate_from_failure_mode",
                "add_fault_event",
            ):
                self.app.fta_menu.entryconfig(self.app._fta_menu_indices[key], state=state)

    def _reset_fta_state(self):
        """Clear references to the FTA tab and its canvas."""
        self.app.canvas_tab = None
        self.app.canvas_frame = None
        self.app.canvas = None
        self.app.hbar = None
        self.app.vbar = None
        self.app.page_diagram = None

    def ensure_fta_tab(self):
        """Recreate the FTA tab if it was closed."""
        mode = getattr(self.app, "diagram_mode", "FTA")
        tab_info = self.app.analysis_tabs.get(mode)
        if not tab_info or not tab_info["tab"].winfo_exists():
            self._create_fta_tab(mode)
        else:
            self.app.canvas_tab = tab_info["tab"]
            self.app.canvas = tab_info["canvas"]
            self.app.hbar = tab_info["hbar"]
            self.app.vbar = tab_info["vbar"]

    def update_fta_statuses(self):
        """Update status for each top level event based on linked reviews."""
        for te in self.app.top_events:
            status = "draft"
            for review in self.app.reviews:
                if te.unique_id in getattr(review, "fta_ids", []):
                    if (
                        review.mode == "joint"
                        and review.approved
                        and self.app.review_is_closed_for(review)
                    ):
                        status = "closed"
                        break
                    else:
                        status = "in review"
            te.status = status
