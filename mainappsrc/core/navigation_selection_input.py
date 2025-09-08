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

import tkinter as tk
from typing import TYPE_CHECKING

from analysis.fmeda_utils import GATE_NODE_TYPES
from gui.dialogs.edit_node_dialog import EditNodeDialog
from gui.toolboxes.search_toolbox import SearchToolbox
from gui.utils.dockable_diagram_window import DockableDiagramWindow

if TYPE_CHECKING:  # pragma: no cover - for type checking only
    from .automl_core import AutoMLApp


class Navigation_Selection_Input:
    """Handle navigation, selection and input events for :class:`AutoMLApp`."""

    def __init__(self, app: "AutoMLApp") -> None:
        self.app = app

    # ------------------------------------------------------------------
    # Basic navigation helpers
    # ------------------------------------------------------------------
    def go_back(self) -> None:
        app = self.app
        if app.page_history:
            previous_page = app.page_history.pop()
            app.window_controllers.open_page_diagram(previous_page, push_history=False)

    def back_all_pages(self):
        return self.app.fta_app.back_all_pages(self.app)

    def focus_on_node(self, node) -> None:
        app = self.app
        app.selected_node = node
        try:
            if hasattr(app, "canvas") and app.canvas is not None and app.canvas.winfo_exists():
                app.redraw_canvas()
                bbox = app.canvas.bbox("all")
                if bbox:
                    app.canvas.xview_moveto(max(0, (node.x * app.zoom - app.canvas.winfo_width() / 2) / bbox[2]))
                    app.canvas.yview_moveto(max(0, (node.y * app.zoom - app.canvas.winfo_height() / 2) / bbox[3]))
        except tk.TclError:  # pragma: no cover - GUI dependent
            pass

    # ------------------------------------------------------------------
    # Canvas interaction
    # ------------------------------------------------------------------
    def on_canvas_click(self, event):
        app = self.app
        x = app.canvas.canvasx(event.x) / app.zoom
        y = app.canvas.canvasy(event.y) / app.zoom
        clicked_node = None
        for n in app.get_all_nodes(app.root_node):
            radius = 60 if n.node_type.upper() in GATE_NODE_TYPES else 45
            if (x - n.x) ** 2 + (y - n.y) ** 2 < radius ** 2:
                clicked_node = n
                break
        app.selected_node = clicked_node
        if clicked_node:
            app.push_undo_state(force=True)
            app.dragging_node = clicked_node
            app.drag_offset_x = x - clicked_node.x
            app.drag_offset_y = y - clicked_node.y
        else:
            app.dragging_node = None
        app.redraw_canvas()

    def on_canvas_double_click(self, event):
        app = self.app
        x = app.canvas.canvasx(event.x) / app.zoom
        y = app.canvas.canvasy(event.y) / app.zoom
        clicked_node = None
        for n in app.get_all_nodes(app.root_node):
            radius = 60 if n.node_type.upper() in GATE_NODE_TYPES else 45
            if (x - n.x) ** 2 + (y - n.y) ** 2 < radius ** 2:
                clicked_node = n
                break
        if clicked_node:
            if not clicked_node.is_primary_instance:
                app.window_controllers.open_page_diagram(getattr(clicked_node, "original", clicked_node))
            else:
                if clicked_node.is_page:
                    app.window_controllers.open_page_diagram(clicked_node)
                else:
                    EditNodeDialog(app.root, clicked_node, app)
            app.update_views()

    def on_canvas_drag(self, event):
        app = self.app
        if app.dragging_node:
            x = app.canvas.canvasx(event.x) / app.zoom
            y = app.canvas.canvasy(event.y) / app.zoom
            new_x = x - app.drag_offset_x
            new_y = y - app.drag_offset_y
            dx = new_x - app.dragging_node.x
            dy = new_y - app.dragging_node.y
            app.dragging_node.x = new_x
            app.dragging_node.y = new_y
            if app.dragging_node.is_primary_instance:
                app.move_subtree(app.dragging_node, dx, dy)
            app.redraw_canvas()

    def on_canvas_release(self, event):
        app = self.app
        if app.dragging_node:
            app.dragging_node.x = round(app.dragging_node.x / app.grid_size) * app.grid_size
            app.dragging_node.y = round(app.dragging_node.y / app.grid_size) * app.grid_size
            app.push_undo_state()
        app.dragging_node = None
        app.drag_offset_x = 0
        app.drag_offset_y = 0

    # ------------------------------------------------------------------
    # Tree view interactions
    # ------------------------------------------------------------------
    def on_treeview_click(self, event):
        return self.app.tree_app.on_treeview_click(self.app, event)

    def on_analysis_tree_double_click(self, event):
        return self.app.tree_app.on_analysis_tree_double_click(self.app, event)

    def on_analysis_tree_right_click(self, event):
        return self.app.tree_app.on_analysis_tree_right_click(self.app, event)

    def on_analysis_tree_select(self, _event):
        return self.app.tree_app.on_analysis_tree_select(self.app, _event)

    def on_tool_list_double_click(self, event):
        app = self.app
        lb = event.widget
        sel = lb.curselection()
        if not sel:
            index = lb.nearest(getattr(event, "y", 0))
            if index is None or index < 0:
                return
            lb.selection_clear(0, tk.END)
            lb.selection_set(index)
            sel = (index,)
        name = lb.get(sel[0])
        analysis_names = app.tool_to_work_product.get(name, set())
        if isinstance(analysis_names, str):
            analysis_names = {analysis_names}
        if analysis_names:
            enabled = set(getattr(app, "enabled_work_products", set()))
            if app.safety_mgmt_toolbox:
                enabled.update(app.safety_mgmt_toolbox.enabled_products())
            if not any(n in enabled for n in analysis_names):
                return
        action = app.tool_actions.get(name)
        if action:
            action()

    # ------------------------------------------------------------------
    # Mouse wheel and right-click behaviour
    # ------------------------------------------------------------------
    def on_ctrl_mousewheel(self, event):
        app = self.app
        if event.delta > 0:
            app.zoom_in()
        else:
            app.zoom_out()

    def on_ctrl_mousewheel_page(self, event):
        app = self.app
        if event.delta > 0:
            app.page_diagram.zoom_in()
        else:
            app.page_diagram.zoom_out()

    def on_right_mouse_press(self, event):
        app = self.app
        app.rc_dragged = False
        app.canvas.scan_mark(event.x, event.y)

    def on_right_mouse_drag(self, event):
        app = self.app
        app.rc_dragged = True
        app.canvas.scan_dragto(event.x, event.y, gain=1)

    def on_right_mouse_release(self, event):
        app = self.app
        if not getattr(app, "rc_dragged", False):
            self.show_context_menu(event)
        app.rc_dragged = False

    def show_context_menu(self, event):
        app = self.app
        x = app.canvas.canvasx(event.x) / app.zoom
        y = app.canvas.canvasy(event.y) / app.zoom
        clicked_node = None
        for n in app.get_all_nodes(app.root_node):
            radius = 60 if n.node_type.upper() in GATE_NODE_TYPES else 45
            if (x - n.x) ** 2 + (y - n.y) ** 2 < radius ** 2:
                clicked_node = n
                break
        if not clicked_node:
            return
        app.selected_node = clicked_node
        menu = tk.Menu(app.root, tearoff=0)
        menu.add_command(label="Edit", command=lambda: app.edit_selected())
        menu.add_command(label="Remove Connection", command=lambda: app.remove_connection(clicked_node))
        menu.add_command(label="Delete Node", command=lambda: app.delete_node_and_subtree(clicked_node))
        menu.add_command(label="Remove Node", command=lambda: app.remove_node())
        menu.add_command(label="Copy", command=lambda: app.copy_node())
        menu.add_command(label="Cut", command=lambda: app.cut_node())
        menu.add_command(label="Paste", command=lambda: app.paste_node())
        menu.add_separator()
        menu.add_command(label="Edit User Name", command=lambda: app.user_manager.edit_user_name())
        menu.add_command(label="Edit Description", command=lambda: app.edit_description())
        menu.add_command(label="Edit Rationale", command=lambda: app.edit_rationale())
        menu.add_command(label="Edit Value", command=lambda: app.edit_value())
        menu.add_command(label="Edit Gate Type", command=lambda: app.edit_gate_type())
        menu.add_command(label="Edit Severity", command=lambda: app.edit_severity())
        menu.add_command(label="Edit Controllability", command=lambda: app.edit_controllability())
        menu.add_command(label="Edit Page Flag", command=lambda: app.edit_page_flag())
        menu.add_separator()
        diag_mode = getattr(app.canvas, "diagram_mode", "FTA")
        if diag_mode == "PAA":
            menu.add_command(label="Add Gate", command=lambda: app.add_node_of_type("GATE"))
            menu.add_command(label="Add Confidence", command=lambda: app.add_node_of_type("Confidence Level"))
            menu.add_command(label="Add Robustness", command=lambda: app.add_node_of_type("Robustness Score"))
        elif diag_mode == "CTA":
            menu.add_command(label="Add Triggering Condition", command=lambda: app.add_node_of_type("Triggering Condition"))
            menu.add_command(label="Add Functional Insufficiency", command=lambda: app.add_node_of_type("Functional Insufficiency"))
        else:
            menu.add_command(label="Add Gate", command=lambda: app.add_node_of_type("GATE"))
            menu.add_command(label="Add Basic Event", command=lambda: app.add_node_of_type("Basic Event"))
            menu.add_command(label="Add Gate from Failure Mode", command=app.add_gate_from_failure_mode)
            menu.add_command(label="Add Fault Event", command=app.add_fault_event)
        menu.tk_popup(event.x_root, event.y_root)

    # ------------------------------------------------------------------
    # Toolbox interactions
    # ------------------------------------------------------------------
    def open_search_toolbox(self):
        app = self.app
        if getattr(app, "search_tab", None) and app.search_tab.winfo_exists():
            app.doc_nb.select(app.search_tab)
            return
        dock_window = DockableDiagramWindow(app.doc_nb)
        app.search_tab = SearchToolbox(dock_window.content_frame, app)
        app.search_tab._dock_window = dock_window
        dock_window.dock(app.doc_nb, len(app.doc_nb.tabs()), "Search")
        app.doc_nb.select(app.search_tab)
