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

"""UI helpers extracted from AutoML core.

This module defines :class:`AppLifecycleUI` which encapsulates window and
tab lifecycle utilities originally implemented on :class:`AutoMLApp`.  The
class delegates most attribute access to the parent application instance so
existing code can continue to operate without modification.
"""


import datetime
import tkinter as tk
from tkinter import ttk

from gui.utils import logger
from gui.controls import messagebox
from gui.utils.detachable_tab_window import DetachableTabWindow, DetachedTabMetadata
from gui.utils.dockable_diagram_window import DockableDiagramWindow
from gui.windows.architecture import (
    ActivityDiagramWindow,
    BlockDiagramWindow,
    ControlFlowDiagramWindow,
    GovernanceDiagramWindow,
    InternalBlockDiagramWindow,
    UseCaseDiagramWindow,
)
from analysis.user_config import CURRENT_USER_NAME
from mainappsrc.models.sysml.sysml_repository import SysMLRepository


EXPLORER_HOVER_DELAY = 200


class AppLifecycleUI:
    """Collection of UI lifecycle helper methods.

    The class delegates attribute access to *app* so it can be used either as
    a mixin or as a composed helper instance attached to the main application.
    """

    def __init__(self, app, root) -> None:
        # ``app`` provides the primary application object whose attributes are
        # required by many lifecycle helpers.  ``root`` stores the root window
        # for animation callbacks.
        self.app = app
        self.root = root
        self._explorer_hover_job = None
        self._explorer_animating = False
        self._explorer_animation_id = None
        self._explorer_pending_action = None
        self._detached_tab_windows: dict[ttk.Frame, DetachableTabWindow] = {}

    def __getattr__(self, name):  # pragma: no cover - simple delegation
        return getattr(self.app, name)

    # ------------------------------------------------------------------
    # Methods migrated from ``AutoMLApp``
    # ------------------------------------------------------------------
    def show_properties(self, obj=None, meta=None):
        """Display metadata for *obj* or *meta* dictionary in the properties tab."""
        if not hasattr(self, "prop_view"):
            return
        self.prop_view.delete(*self.prop_view.get_children())
        if obj:
            if not obj:
                return
            if hasattr(self, "analysis_tree"):
                try:
                    self.analysis_tree.selection_set(())
                    self.analysis_tree.focus("")
                except Exception:
                    pass
            self.prop_view.insert("", "end", values=("Type", obj.obj_type))
            name = obj.properties.get("name", "")
            if name:
                self.prop_view.insert("", "end", values=("Name", name))
            for k, v in obj.properties.items():
                if k == "name":
                    continue
                self.prop_view.insert("", "end", values=(k, v))
            if obj.element_id:
                elem = SysMLRepository.get_instance().elements.get(obj.element_id)
                if elem:
                    self.prop_view.insert("", "end", values=("Author", getattr(elem, "author", "")))
                    self.prop_view.insert("", "end", values=("Created", getattr(elem, "created", "")))
                    self.prop_view.insert("", "end", values=("Modified", getattr(elem, "modified", "")))
                    self.prop_view.insert(
                        "", "end", values=("ModifiedBy", getattr(elem, "modified_by", ""))
                    )
        elif meta:
            for k, v in meta.items():
                self.prop_view.insert("", "end", values=(k, v))
        if hasattr(self, "status_meta_vars"):
            for key in self.status_meta_vars:
                self.status_meta_vars[key].set("")
            if obj:
                self.status_meta_vars["Type"].set(obj.obj_type)
                name = obj.properties.get("name", "")
                if name:
                    self.status_meta_vars["Name"].set(name)
                if obj.element_id:
                    elem = SysMLRepository.get_instance().elements.get(obj.element_id)
                    if elem:
                        self.status_meta_vars["Author"].set(
                            getattr(elem, "author", "")
                        )
            elif meta:
                for k, v in meta.items():
                    if k in self.status_meta_vars:
                        self.status_meta_vars[k].set(v)

    def _add_tool_category(self, cat: str, names: list[str]) -> None:
        """Create a notebook tab for tool *cat* without duplicating existing tabs."""

        for tid, title in self._tool_tab_titles.items():
            if title == cat:
                lb = self.tool_listboxes.get(cat)
                if lb is None:
                    frame = self.tools_nb.nametowidget(tid)
                    lb = tk.Listbox(frame, height=10)
                    vsb = ttk.Scrollbar(frame, orient="vertical", command=lb.yview)
                    lb.configure(yscrollcommand=vsb.set)
                    lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                    vsb.pack(side=tk.RIGHT, fill=tk.Y)
                    lb.bind("<Double-1>", self.on_tool_list_double_click)
                    self.tool_listboxes[cat] = lb
                existing = set(lb.get(0, tk.END))
                for n in names:
                    if n not in existing:
                        lb.insert(tk.END, n)
                return
        frame = ttk.Frame(self.tools_nb)
        display = cat
        if len(display) > self.MAX_TOOL_TAB_TEXT_LENGTH:
            display = display[: self.MAX_TOOL_TAB_TEXT_LENGTH - 1] + "\N{HORIZONTAL ELLIPSIS}"
        self.tools_nb.add(frame, text=display)
        tab_id = self.tools_nb.tabs()[-1]
        self._tool_tab_titles[tab_id] = cat
        self._tool_all_tabs.append(tab_id)
        self._tool_tab_offset = max(0, len(self._tool_all_tabs) - self.MAX_VISIBLE_TABS)
        self._update_tool_tab_visibility()
        lb = tk.Listbox(frame, height=10)
        vsb = ttk.Scrollbar(frame, orient="vertical", command=lb.yview)
        lb.configure(yscrollcommand=vsb.set)
        lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        lb.bind("<Double-1>", self.on_tool_list_double_click)
        self.tool_listboxes[cat] = lb
        for n in names:
            lb.insert(tk.END, n)

    def _remove_tool_category(self, cat: str) -> None:
        """Remove toolbox category *cat* along with its tab and widgets."""
        lb = self.tool_listboxes.pop(cat, None)
        tab_id = None
        for tid, title in self._tool_tab_titles.items():
            if title == cat:
                tab_id = tid
                break
        if tab_id:
            parent = lb.master if lb is not None else self.tools_nb.nametowidget(tab_id)
            try:
                self.tools_nb.forget(tab_id)
            except tk.TclError:
                pass
            self._tool_tab_titles.pop(tab_id, None)
            if tab_id in self._tool_all_tabs:
                self._tool_all_tabs.remove(tab_id)
                self._tool_tab_offset = max(0, len(self._tool_all_tabs) - self.MAX_VISIBLE_TABS)
                self._update_tool_tab_visibility()
            try:
                parent.destroy()
            except Exception:
                pass

    def _on_tool_tab_motion(self, event):
        """Show tooltip for notebook tabs when hovering over them."""
        try:
            idx = self.tools_nb.index(f"@{event.x},{event.y}")
        except tk.TclError:
            self._tools_tip.hide()
            return
        tab_id = self.tools_nb.tabs()[idx]
        text = self._tool_tab_titles.get(tab_id, self.tools_nb.tab(tab_id, "text"))
        bbox = self.tools_nb.bbox(idx)
        if not bbox:
            self._tools_tip.hide()
            return
        x = self.tools_nb.winfo_rootx() + bbox[0] + bbox[2] // 2
        y = self.tools_nb.winfo_rooty() + bbox[1] + bbox[3]
        if self._tools_tip.text != text:
            self._tools_tip.text = text
        self._tools_tip.show(x, y)

    def _on_doc_tab_motion(self, event):
        """Show tooltip for document notebook tabs when hovering over them."""
        try:
            idx = self.doc_nb.index(f"@{event.x},{event.y}")
        except tk.TclError:
            self._doc_tip.hide()
            return
        text = self.doc_nb.tab(idx, "text")
        bbox = self.doc_nb.bbox(idx)
        if not bbox:
            self._doc_tip.hide()
            return
        x = self.doc_nb.winfo_rootx() + bbox[0] + bbox[2] // 2
        y = self.doc_nb.winfo_rooty() + bbox[1] + bbox[3]
        if self._doc_tip.text != text:
            self._doc_tip.text = text
        self._doc_tip.show(x, y)

    def toggle_logs(self):
        logger.toggle_log()

    # ------------------------------------------------------------------
    # Explorer panel show/hide helpers
    def on_explorer_tab_enter(self, _event=None):
        if (
            self._explorer_hover_job
            or self.explorer_pane.winfo_manager()
            or self._explorer_animating
        ):
            return
        self._explorer_hover_job = self.root.after(
            EXPLORER_HOVER_DELAY, self._show_explorer_from_hover
        )

    def _show_explorer_from_hover(self):
        self._explorer_hover_job = None
        self.show_explorer(animate=True)

    def on_explorer_tab_leave(self, _event=None):
        if self._explorer_hover_job:
            self.root.after_cancel(self._explorer_hover_job)
            self._explorer_hover_job = None

    def show_explorer(self, animate=False):
        """Display the explorer pane."""
        if self._explorer_animating:
            self._explorer_pending_action = "show"
            return
        if self.explorer_pane.winfo_manager():
            self._cancel_explorer_hide()
            return
        self._explorer_tab.pack_forget()
        self.main_pane.add(self.explorer_pane, before=self.doc_frame)
        self.main_pane.paneconfig(self.explorer_pane, width=0)
        if animate:
            self._animate_explorer_show(0)
        else:
            self.main_pane.paneconfig(self.explorer_pane, width=self._explorer_width)

    def _animate_explorer_show(self, width):
        self._explorer_animating = True
        if width >= self._explorer_width:
            self.main_pane.paneconfig(self.explorer_pane, width=self._explorer_width)
            self._explorer_animating = False
            self._explorer_animation_id = None
            self._run_pending_explorer_action()
            return
        self.main_pane.paneconfig(self.explorer_pane, width=width)
        step = max(self._explorer_width // 10, 1)
        self._explorer_animation_id = self.root.after(
            15, lambda: self._animate_explorer_show(width + step)
        )

    def hide_explorer(self, animate=False):
        """Hide the explorer pane."""
        if self._explorer_animating:
            self._explorer_pending_action = "hide"
            return
        if self._explorer_pinned or not self.explorer_pane.winfo_manager():
            return
        self._cancel_explorer_hide()
        if animate:
            self._animate_explorer_hide(self.explorer_pane.winfo_width())
        else:
            self.main_pane.forget(self.explorer_pane)
            self._explorer_tab.pack(side=tk.LEFT, fill=tk.Y)

    def _animate_explorer_hide(self, width):
        self._explorer_animating = True
        if width <= 0:
            self.main_pane.forget(self.explorer_pane)
            self._explorer_tab.pack(side=tk.LEFT, fill=tk.Y)
            self._explorer_animating = False
            self._explorer_animation_id = None
            self._run_pending_explorer_action()
            return
        self.main_pane.paneconfig(self.explorer_pane, width=width)
        step = max(self._explorer_width // 10, 1)
        self._explorer_animation_id = self.root.after(
            15, lambda: self._animate_explorer_hide(width - step)
        )

    def _schedule_explorer_hide(self, delay=1000):
        if self._explorer_pinned:
            return
        if self._explorer_auto_hide_id:
            self.root.after_cancel(self._explorer_auto_hide_id)
        self._explorer_auto_hide_id = self.root.after(
            delay, lambda: self.hide_explorer(animate=True)
        )

    def _cancel_explorer_hide(self):
        if self._explorer_auto_hide_id:
            self.root.after_cancel(self._explorer_auto_hide_id)
            self._explorer_auto_hide_id = None

    def toggle_explorer_pin(self):
        """Toggle between auto-hide and pinned explorer modes."""
        self._explorer_pinned = not self._explorer_pinned
        self._explorer_pin_btn.config(text="Unpin" if self._explorer_pinned else "Pin")
        if self._explorer_pinned:
            self._cancel_explorer_hide()
        else:
            self._schedule_explorer_hide()

    def _run_pending_explorer_action(self):
        action = self._explorer_pending_action
        self._explorer_pending_action = None
        if action == "show":
            self.show_explorer(animate=True)
        elif action == "hide":
            self.hide_explorer(animate=True)

    def _limit_explorer_size(self):
        """Ensure the explorer pane does not exceed the maximum width."""
        if self.explorer_pane.winfo_manager():
            width = self.explorer_pane.winfo_width()
            if width > self._explorer_width:
                self.main_pane.paneconfig(self.explorer_pane, width=self._explorer_width)

    def touch_doc(self, doc):
        """Update modification metadata for the given document."""
        doc["modified"] = datetime.datetime.now().isoformat()
        doc["modified_by"] = CURRENT_USER_NAME
        self.refresh_all()

    def _add_lifecycle_requirements_menu(self, menu: tk.Menu) -> None:
        """Insert a menu entry for lifecycle requirements."""
        menu.add_command(
            label="Lifecycle Requirements",
            command=self.generate_lifecycle_requirements,
        )

    def open_metrics_tab(self):
        """Open a tab displaying project metrics."""
        from gui.metrics_tab import MetricsTab

        tab = self._new_tab("Metrics")
        MetricsTab(tab, self).pack(fill=tk.BOTH, expand=True)

    def _register_close(self, win, collection):
        def _close():
            if win in collection:
                collection.remove(win)
            win.destroy()

        return _close

    def _on_tab_close(self, event):
        tab_id = self.doc_nb._closing_tab
        if hasattr(self, "_tab_titles"):
            self._tab_titles.pop(tab_id, None)
        tab = self.doc_nb.nametowidget(tab_id)
        self._detached_tab_windows.pop(tab, None)
        for mode, info in list(getattr(self, "analysis_tabs", {}).items()):
            if info["tab"] is tab:
                del self.analysis_tabs[mode]
                if tab is getattr(self, "canvas_tab", None):
                    self.canvas_tab = None
                    self.canvas_frame = None
                    self.canvas = None
                    self.hbar = None
                    self.vbar = None
                    self.page_diagram = None
                tab.destroy()
                return
        if tab is getattr(self, "search_tab", None):
            self.search_tab = None
            tab.destroy()
            return
        for child in tab.winfo_children():
            if hasattr(child, "on_close"):
                child.on_close()
        for did, t in list(self.diagram_tabs.items()):
            if t == tab:
                del self.diagram_tabs[did]
                break
        tab.destroy()
        if hasattr(self, "_doc_all_tabs") and tab_id in self._doc_all_tabs:
            self._doc_all_tabs.remove(tab_id)
            self._doc_tab_offset = min(
                self._doc_tab_offset,
                max(0, len(self._doc_all_tabs) - self.MAX_VISIBLE_TABS),
            )
            self._update_doc_tab_visibility()
        self.refresh_all()

    def _on_tab_change(self, event):
        """Refresh diagrams when their tab becomes active."""
        tab_id = event.widget.select()
        self._make_doc_tab_visible(tab_id)
        tab = (
            event.widget.nametowidget(tab_id)
            if hasattr(event.widget, "nametowidget")
            else tab_id
        )
        try:
            tab_name = event.widget.tab(tab_id, "text")
        except Exception:
            tab_name = str(tab_id)
        win = getattr(tab, "arch_window", None)
        wp = ""
        if win:
            self.active_arch_window = win
            wp = self._get_diag_type(win)
        else:
            gsn_win = getattr(tab, "gsn_window", None)
            if gsn_win:
                self.active_gsn_window = gsn_win
                win = gsn_win
                wp = "GSN"
        cls_name = win.__class__.__name__ if win else ""
        if hasattr(self, "status_meta_vars"):
            if "Tab" in self.status_meta_vars:
                self.status_meta_vars["Tab"].set(tab_name)
            if "WorkProduct" in self.status_meta_vars:
                self.status_meta_vars["WorkProduct"].set(wp)
            if "Class" in self.status_meta_vars:
                self.status_meta_vars["Class"].set(cls_name)
        canvas = None
        widgets = [tab, *getattr(tab, "winfo_children", lambda: [])()]
        for child in widgets:
            if hasattr(child, "diagram_mode"):
                canvas = child
                break
        if canvas is not None:
            self.canvas_tab = tab
            self.canvas = canvas
            self.diagram_mode = getattr(canvas, "diagram_mode", "FTA")
            info = getattr(self, "analysis_tabs", {}).get(self.diagram_mode)
            if info and info["tab"] is tab:
                self.hbar = info["hbar"]
                self.vbar = info["vbar"]
            if self.diagram_mode == "CTA" and self.cta_root_node:
                self.root_node = self.cta_root_node
                mode = getattr(self, "diagram_mode", "CTA")
            elif self.diagram_mode == "PAA" and self.paa_root_node:
                self.root_node = self.paa_root_node
                mode = getattr(self, "diagram_mode", "PAA")
            elif self.fta_root_node:
                mode = getattr(self, "diagram_mode", "FTA")
                self.root_node = self.fta_root_node
            self._update_analysis_menus(mode)
        else:
            self.enable_fta_actions(False)
            self.cta_manager.enable_actions(False)
            self.enable_paa_actions(False)
        gsn_win = getattr(tab, "gsn_window", None)
        if gsn_win:
            self.selected_node = gsn_win.diagram.root
        self.refresh_all()
        if tab is getattr(self, "_safety_case_tab", None):
            self.refresh_safety_case_table()
        for child in widgets:
            if hasattr(child, "refresh_from_repository"):
                child.refresh_from_repository()
            elif hasattr(child, "refresh"):
                child.refresh()

        toolbox = getattr(self, "safety_mgmt_toolbox", None)
        if toolbox and getattr(self, "diagram_tabs", None):
            for diag_id, widget in self.diagram_tabs.items():
                if widget == tab:
                    repo = SysMLRepository.get_instance()
                    diag = repo.diagrams.get(diag_id)
                    if diag and diag.diag_type == "Governance Diagram":
                        toolbox.list_diagrams()
                        name = next(
                            (n for n, did in toolbox.diagrams.items() if did == diag_id),
                            diag.name,
                        )
                        module = toolbox.module_for_diagram(name)
                        if module != getattr(toolbox, "active_module", None):
                            self.governance_manager.set_active_module(module)
                    break

    def _init_nav_button_style(self) -> None:
        """Configure custom style for tab navigation buttons."""
        self.style.configure(
            "Nav.TButton",
            background="#e7edf5",
            borderwidth=2,
            relief="raised",
            lightcolor="#ffffff",
            darkcolor="#7a8a99",
        )
        self.style.map(
            "Nav.TButton",
            background=[("active", "#f2f6fa"), ("pressed", "#dae2ea")],
            relief=[("pressed", "sunken"), ("!pressed", "raised")],
        )

    def _update_tool_tab_visibility(self) -> None:
        visible: list[str] = []
        for idx, tab_id in enumerate(self._tool_all_tabs):
            state = "normal" if self._tool_tab_offset <= idx < self._tool_tab_offset + self.MAX_VISIBLE_TABS else "hidden"
            try:
                self.tools_nb.tab(tab_id, state=state)
            except Exception:
                visible.append(tab_id)
                continue
            if state == "normal":
                visible.append(tab_id)
        current = self.tools_nb.select()
        if current not in visible and visible:
            self.tools_nb.select(visible[0])
        if hasattr(self, "tools_left_btn") and hasattr(self, "tools_right_btn"):
            if len(self._tool_all_tabs) <= self.MAX_VISIBLE_TABS:
                if len(self._tool_all_tabs) <= 1:
                    self.tools_left_btn.state(["disabled"])
                    self.tools_right_btn.state(["disabled"])
                else:
                    self.tools_left_btn.state(["!disabled"])
                    self.tools_right_btn.state(["!disabled"])
            else:
                if self._tool_tab_offset <= 0:
                    self.tools_left_btn.state(["disabled"])
                else:
                    self.tools_left_btn.state(["!disabled"])
                if self._tool_tab_offset + self.MAX_VISIBLE_TABS >= len(self._tool_all_tabs):
                    self.tools_right_btn.state(["disabled"])
                else:
                    self.tools_right_btn.state(["!disabled"])

    def _update_doc_tab_visibility(self) -> None:
        visible: list[str] = []
        for idx, tab_id in enumerate(self._doc_all_tabs):
            state = "normal" if self._doc_tab_offset <= idx < self._doc_tab_offset + self.MAX_VISIBLE_TABS else "hidden"
            try:
                self.doc_nb.tab(tab_id, state=state)
            except Exception:
                visible.append(tab_id)
                continue
            if state == "normal":
                visible.append(tab_id)
        current = self.doc_nb.select()
        if current not in visible and visible:
            self.doc_nb.select(visible[0])
        if hasattr(self, "_tab_left_btn") and hasattr(self, "_tab_right_btn"):
            if len(self._doc_all_tabs) <= self.MAX_VISIBLE_TABS:
                if len(self._doc_all_tabs) <= 1:
                    self._tab_left_btn.state(["disabled"])
                    self._tab_right_btn.state(["disabled"])
                else:
                    self._tab_left_btn.state(["!disabled"])
                    self._tab_right_btn.state(["!disabled"])
            else:
                if self._doc_tab_offset <= 0:
                    self._tab_left_btn.state(["disabled"])
                else:
                    self._tab_left_btn.state(["!disabled"])
                if self._doc_tab_offset + self.MAX_VISIBLE_TABS >= len(self._doc_all_tabs):
                    self._tab_right_btn.state(["disabled"])
                else:
                    self._tab_right_btn.state(["!disabled"])

    def _make_doc_tab_visible(self, tab_id: str) -> None:
        all_tabs = getattr(self, "_doc_all_tabs", [])
        if tab_id not in all_tabs:
            return
        index = all_tabs.index(tab_id)
        offset = getattr(self, "_doc_tab_offset", 0)
        if index < offset:
            self._doc_tab_offset = index
            self._update_doc_tab_visibility()
        elif index >= offset + self.MAX_VISIBLE_TABS:
            self._doc_tab_offset = index - self.MAX_VISIBLE_TABS + 1
            self._update_doc_tab_visibility()

    def _select_prev_tool_tab(self) -> None:
        """Scroll tool tabs to show the previous hidden tab."""
        if len(self._tool_all_tabs) <= self.MAX_VISIBLE_TABS:
            tabs = self.tools_nb.tabs()
            if not tabs:
                return
            current = self.tools_nb.select()
            try:
                index = tabs.index(current)
            except ValueError:
                index = 0
            self.tools_nb.select(tabs[index - 1])
            return
        if self._tool_tab_offset > 0:
            self._tool_tab_offset -= 1
            self._update_tool_tab_visibility()

    def _select_next_tool_tab(self) -> None:
        """Scroll tool tabs to show the next hidden tab."""
        if len(self._tool_all_tabs) <= self.MAX_VISIBLE_TABS:
            tabs = self.tools_nb.tabs()
            if not tabs:
                return
            current = self.tools_nb.select()
            try:
                index = tabs.index(current)
            except ValueError:
                index = 0
            self.tools_nb.select(tabs[(index + 1) % len(tabs)])
            return
        if self._tool_tab_offset + self.MAX_VISIBLE_TABS < len(self._tool_all_tabs):
            self._tool_tab_offset += 1
            self._update_tool_tab_visibility()

    def _select_prev_tab(self) -> None:
        """Scroll document tabs to show the previous hidden tab."""
        if len(self._doc_all_tabs) <= self.MAX_VISIBLE_TABS:
            tabs = self.doc_nb.tabs()
            if not tabs:
                return
            current = self.doc_nb.select()
            try:
                index = tabs.index(current)
            except ValueError:
                index = 0
            self.doc_nb.select(tabs[index - 1])
            return
        if self._doc_tab_offset > 0:
            self._doc_tab_offset -= 1
            self._update_doc_tab_visibility()

    def _select_next_tab(self) -> None:
        """Scroll document tabs to show the next hidden tab."""
        if len(self._doc_all_tabs) <= self.MAX_VISIBLE_TABS:
            tabs = self.doc_nb.tabs()
            if not tabs:
                return
            current = self.doc_nb.select()
            try:
                index = tabs.index(current)
            except ValueError:
                index = 0
            self.doc_nb.select(tabs[(index + 1) % len(tabs)])
            return
        if self._doc_tab_offset + self.MAX_VISIBLE_TABS < len(self._doc_all_tabs):
            self._doc_tab_offset += 1
            self._update_doc_tab_visibility()

    def snap_out_selected_tab(self) -> None:
        """Detach the currently selected document tab into a floating window."""

        if not hasattr(self, "doc_nb"):
            return
        try:
            if not self.doc_nb.winfo_exists():
                return
        except tk.TclError:
            return

        tab_id = self.doc_nb.select()
        if not tab_id:
            return
        try:
            tab = self.doc_nb.nametowidget(tab_id)
        except (KeyError, tk.TclError):
            return
        try:
            if not tab.winfo_exists():
                return
        except tk.TclError:
            return
        if tab in self._detached_tab_windows:
            window = self._detached_tab_windows[tab]
            window.detach()
            return
        title = self._tab_titles.get(tab_id, self.doc_nb.tab(tab_id, "text"))
        metadata = DetachedTabMetadata(
            title=title,
            diagram_id=self._diagram_id_for_tab(tab),
            index=self.doc_nb.index(tab_id),
        )
        detachable = DetachableTabWindow(
            self.root,
            tab,
            self.doc_nb,
            metadata,
            on_dock=self._on_tab_redocked,
        )
        self._detached_tab_windows[tab] = detachable
        detachable.detach()
        self._remove_doc_tab_from_tracking(tab_id)

    def _remove_doc_tab_from_tracking(self, tab_id: str) -> None:
        if hasattr(self, "_doc_all_tabs") and tab_id in self._doc_all_tabs:
            self._doc_all_tabs.remove(tab_id)
            self._doc_tab_offset = min(
                self._doc_tab_offset,
                max(0, len(self._doc_all_tabs) - self.MAX_VISIBLE_TABS),
            )
            self._update_doc_tab_visibility()

    def _on_tab_redocked(self, tab: ttk.Frame) -> None:
        tab_id = str(tab)
        if tab in self._detached_tab_windows:
            self._detached_tab_windows.pop(tab, None)
        if hasattr(self, "_tab_titles"):
            tab_text = getattr(tab, "title", None)
            if tab_text is None and hasattr(self, "doc_nb"):
                try:
                    tab_text = self.doc_nb.tab(tab_id, "text")
                except Exception:
                    tab_text = None
            if tab_text is not None:
                self._tab_titles.setdefault(tab_id, tab_text)
        if hasattr(self, "_doc_all_tabs"):
            if tab_id not in self._doc_all_tabs:
                self._doc_all_tabs.append(tab_id)
            self._doc_tab_offset = max(0, len(self._doc_all_tabs) - self.MAX_VISIBLE_TABS)
            self._update_doc_tab_visibility()
        try:
            self.doc_nb.select(tab_id)
        except Exception:
            pass

    def _diagram_id_for_tab(self, tab: ttk.Frame) -> str | None:
        for diag_id, widget in getattr(self, "diagram_tabs", {}).items():
            if widget is tab:
                return diag_id
        return None

    def _new_tab(self, title: str) -> ttk.Frame:
        """Create or select a tab in the document notebook."""

        if not hasattr(self, "_tab_titles"):
            self._tab_titles = {}

        for tab_id in self.doc_nb.tabs():
            if self._tab_titles.get(tab_id, self.doc_nb.tab(tab_id, "text")) == title:
                self.doc_nb.select(tab_id)
                return self.doc_nb.nametowidget(tab_id)

        tab = ttk.Frame(self.doc_nb)
        dock_window = DockableDiagramWindow(tab)
        tab._dock_window = dock_window
        display = self._truncate_tab_title(title)
        dock_window.dock(self.doc_nb, len(self.doc_nb.tabs()), display)
        tab_id = self.doc_nb.tabs()[-1]
        self._tab_titles[tab_id] = title
        if not hasattr(self, "_doc_all_tabs"):
            self._doc_all_tabs = []
            self._doc_tab_offset = 0
        self._doc_all_tabs.append(tab_id)
        self._doc_tab_offset = max(0, len(self._doc_all_tabs) - self.MAX_VISIBLE_TABS)
        try:
            self._update_doc_tab_visibility()
        except Exception:
            pass
        self.doc_nb.select(tab_id)
        return tab

    def _truncate_tab_title(self, title: str) -> str:
        """Return a shortened title suitable for display in a tab."""
        if len(title) <= self.MAX_TAB_TEXT_LENGTH:
            return title
        return title[: self.MAX_TAB_TEXT_LENGTH - 1] + "\N{HORIZONTAL ELLIPSIS}"

    def open_management_window(self, idx: int) -> None:
        """Open a safety management diagram from the repository."""
        if idx < 0 or idx >= len(self.management_diagrams):
            return
        diag = self.management_diagrams[idx]
        existing = self.diagram_tabs.get(diag.diag_id)
        if existing and str(existing) in self.doc_nb.tabs():
            if existing.winfo_exists():
                self.doc_nb.select(existing)
                self.refresh_all()
                return
        else:
            self.diagram_tabs.pop(diag.diag_id, None)
        tab = self._new_tab(self._format_diag_title(diag))
        self.diagram_tabs[diag.diag_id] = tab
        if diag.diag_type == "Use Case Diagram":
            UseCaseDiagramWindow(tab, self, diagram_id=diag.diag_id)
        elif diag.diag_type == "Activity Diagram":
            ActivityDiagramWindow(tab, self, diagram_id=diag.diag_id)
        elif diag.diag_type == "Governance Diagram":
            GovernanceDiagramWindow(tab, self, diagram_id=diag.diag_id)
        elif diag.diag_type == "Block Diagram":
            BlockDiagramWindow(tab, self, diagram_id=diag.diag_id)
        elif diag.diag_type == "Internal Block Diagram":
            InternalBlockDiagramWindow(tab, self, diagram_id=diag.diag_id)
        elif diag.diag_type == "Control Flow Diagram":
            ControlFlowDiagramWindow(tab, self, diagram_id=diag.diag_id)
        self.refresh_all()

    def _window_has_focus(self, win):
        try:
            focused = win.focus_get()
            if focused and focused.winfo_toplevel() is win.winfo_toplevel():
                return True
        except Exception:
            pass
        return getattr(win, "has_focus", False)

    def _window_in_selected_tab(self, win):
        nb = getattr(self, "doc_nb", None)
        if not nb:
            return True
        try:
            sel = nb.select()
            if sel:
                tab = nb.nametowidget(sel)
                if (
                    getattr(tab, "gsn_window", None) is win
                    or getattr(tab, "arch_window", None) is win
                ):
                    return True
        except Exception:
            pass
        return False

    def show_about(self):
        """Display information about the tool."""
        symbol = "\u2699"
        message = (
            f"{symbol} AutoML Automotive Modeling Language\n\n"
            "Model items, scenarios, functions, structure and interfaces.\n"
            "Perform systems safety analyses, including cybersecurity, per ISO 26262, "
            "ISO 21448, ISO 21434 and ISO 8800.\n\n"
            f"Version: {self.version}"
        )
        messagebox.showinfo("About AutoML", message)

    def _reregister_document(self, analysis: str, name: str) -> None:
        phase = self.safety_mgmt_toolbox.doc_phases.get(analysis, {}).get(name)
        current = self.safety_mgmt_toolbox.active_module
        try:
            self.safety_mgmt_toolbox.active_module = phase
            self.safety_mgmt_toolbox.register_created_work_product(analysis, name)
        finally:
            self.safety_mgmt_toolbox.active_module = current

