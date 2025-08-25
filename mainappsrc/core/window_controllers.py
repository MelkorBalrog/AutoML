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

"""Window management helpers for AutoML.

The :class:`WindowControllers` class centralizes logic related to opening
and focusing diagram windows.  It is instantiated by :class:`AutoMLApp`
and delegates to existing sub-apps and repository utilities.
"""

from typing import Optional
import tkinter as tk
from tkinter import ttk

from gui.windows.architecture import (
    ARCH_WINDOWS,
    UseCaseDiagramWindow,
    ActivityDiagramWindow,
    GovernanceDiagramWindow,
    BlockDiagramWindow,
    InternalBlockDiagramWindow,
    ControlFlowDiagramWindow,
)
from gui.windows.causal_bayesian_network_window import CBN_WINDOWS
from gui.windows.gsn_diagram_window import GSN_WINDOWS
from gui.styles.style_manager import StyleManager
from mainappsrc.models.sysml.sysml_repository import SysMLRepository
from mainappsrc.core.page_diagram import PageDiagram


class WindowControllers:
    """Provide helpers to open and focus diagram windows."""

    def __init__(self, app: "AutoMLApp") -> None:
        self.app = app

    # ------------------------------------------------------------------
    # Diagram opening helpers
    def open_use_case_diagram(self) -> None:
        self.app.use_case_diagram_app.open()

    def open_activity_diagram(self) -> None:
        self.app.activity_diagram_app.open()

    def open_block_diagram(self) -> None:
        self.app.block_diagram_app.open()

    def open_internal_block_diagram(self) -> None:
        self.app.internal_block_diagram_app.open()

    def open_control_flow_diagram(self) -> None:
        self.app.control_flow_diagram_app.open()

    def open_causal_bayesian_network_window(self) -> None:
        self.app.risk_app.open_causal_bayesian_network_window(self.app)

    def open_gsn_diagram(self, diagram) -> None:
        self.app.gsn_manager.open_diagram(diagram)

    def open_arch_window(self, diag_id: str) -> None:
        """Open an existing architecture diagram from the repository."""
        repo = SysMLRepository.get_instance()
        diag = repo.diagrams.get(diag_id)
        if not diag:
            return
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

    def open_page_diagram(self, node, push_history: bool = True) -> None:
        app = self.app
        app.ensure_fta_tab()
        resolved_node = app.resolve_original(node)
        if push_history and hasattr(app, "page_diagram") and app.page_diagram is not None:
            app.page_history.append(app.page_diagram.root_node)
        for widget in app.canvas_frame.winfo_children():
            widget.destroy()

        header_frame = ttk.Frame(app.canvas_frame)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.columnconfigure(0, weight=1)

        header = tk.Label(
            header_frame,
            text=f"Page Diagram: {resolved_node.name}",
            font=("Arial", 14, "bold"),
        )
        header.grid(row=0, column=0, sticky="w", padx=(5, 0))
        back_button = ttk.Button(header_frame, text="Go Back", command=app.go_back)
        back_button.grid(row=0, column=1, sticky="e", padx=5)

        page_canvas = tk.Canvas(app.canvas_frame, bg=StyleManager.get_instance().canvas_bg)
        page_canvas.grid(row=1, column=0, sticky="nsew")
        page_canvas.diagram_mode = getattr(app, "diagram_mode", "FTA")
        vbar = ttk.Scrollbar(app.canvas_frame, orient=tk.VERTICAL, command=page_canvas.yview)
        vbar.grid(row=1, column=1, sticky="ns")
        hbar = ttk.Scrollbar(app.canvas_frame, orient=tk.HORIZONTAL, command=page_canvas.xview)
        hbar.grid(row=2, column=0, sticky="ew")
        page_canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        app.page_canvas = page_canvas
        app.canvas_frame.rowconfigure(0, weight=0)
        app.canvas_frame.rowconfigure(1, weight=1)
        app.canvas_frame.rowconfigure(2, weight=0)
        app.canvas_frame.columnconfigure(0, weight=1)

        app.page_diagram = PageDiagram(app, resolved_node, page_canvas)
        app.page_diagram.redraw_canvas()
        app.refresh_all()

    # ------------------------------------------------------------------
    # Window focus helpers
    def _gsn_window_strategy1(self):
        win = getattr(self.app, "active_gsn_window", None)
        if win and (self.app._window_has_focus(win) or self.app._window_in_selected_tab(win)):
            return win
        return None

    def _gsn_window_strategy2(self):
        for ref in list(GSN_WINDOWS):
            win = ref()
            if win and (self.app._window_has_focus(win) or self.app._window_in_selected_tab(win)):
                return win
        return None

    def _gsn_window_strategy3(self):
        win = getattr(self.app, "active_gsn_window", None)
        if win and self.app._window_in_selected_tab(win):
            return win
        return None

    def _gsn_window_strategy4(self):
        for ref in list(GSN_WINDOWS):
            win = ref()
            if win and self.app._window_in_selected_tab(win):
                return win
        return None

    def _focused_gsn_window(self):
        for strat in (
            self._gsn_window_strategy3,
            self._gsn_window_strategy4,
            self._gsn_window_strategy1,
            self._gsn_window_strategy2,
        ):
            win = strat()
            if win:
                return win
        return None

    def _cbn_window_strategy1(self):
        win = getattr(self.app, "_cbn_window", None)
        if win and self.app._window_has_focus(win):
            return win
        return None

    def _cbn_window_strategy2(self):
        for ref in list(CBN_WINDOWS):
            win = ref()
            if win and self.app._window_has_focus(win):
                return win
        return None

    def _cbn_window_strategy3(self):
        win = getattr(self.app, "_cbn_window", None)
        if win:
            return win
        return None

    def _cbn_window_strategy4(self):
        for ref in list(CBN_WINDOWS):
            win = ref()
            if win:
                return win
        return None

    def _focused_cbn_window(self):
        for strat in (
            self._cbn_window_strategy1,
            self._cbn_window_strategy2,
            self._cbn_window_strategy3,
            self._cbn_window_strategy4,
        ):
            win = strat()
            if win:
                return win
        return None

    def _arch_window_strategy1(self, clip_type: Optional[str] = None):
        win = getattr(self.app, "active_arch_window", None)
        if win and (not clip_type or self.app._get_diag_type(win) == clip_type):
            if self.app._window_has_focus(win) or self.app._window_in_selected_tab(win):
                return win
        return None

    def _arch_window_strategy2(self, clip_type: Optional[str] = None):
        for ref in list(ARCH_WINDOWS):
            win = ref()
            if win and (not clip_type or self.app._get_diag_type(win) == clip_type):
                if self.app._window_has_focus(win) or self.app._window_in_selected_tab(win):
                    return win
        return None

    def _arch_window_strategy3(self, clip_type: Optional[str] = None):
        win = getattr(self.app, "active_arch_window", None)
        if win and (not clip_type or self.app._get_diag_type(win) == clip_type):
            if self.app._window_in_selected_tab(win):
                return win
        return None

    def _arch_window_strategy4(self, clip_type: Optional[str] = None):
        for ref in list(ARCH_WINDOWS):
            win = ref()
            if win and (not clip_type or self.app._get_diag_type(win) == clip_type):
                if self.app._window_in_selected_tab(win):
                    return win
        return None

    def _focused_arch_window(self, clip_type: Optional[str] = None):
        nb = getattr(self.app, "doc_nb", None)
        if nb:
            try:
                sel = nb.select()
                if sel:
                    tab = nb.nametowidget(sel)
                    win = getattr(tab, "arch_window", None)
                    if win and (not clip_type or self.app._get_diag_type(win) == clip_type):
                        return win
            except Exception:
                pass
        for strat in (
            self._arch_window_strategy1,
            self._arch_window_strategy2,
            self._arch_window_strategy3,
            self._arch_window_strategy4,
        ):
            win = strat(clip_type)
            if win:
                return win
        return None
