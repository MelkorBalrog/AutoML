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

"""Centralised drawing helpers for AutoML diagrams."""

import tkinter as tk
from gui.utils.config_utils import AutoML_Helper
from analysis.fmeda_utils import GATE_NODE_TYPES
from gui.utils.drawing_helper import fta_drawing_helper, init_diagram_canvas
from gui.styles.style_manager import StyleManager


class DrawingManager:
    """Handle diagram rendering tasks for :class:`AutoMLApp`."""

    def __init__(self, app: "AutoMLApp") -> None:
        self.app = app

    def initialize_canvas(self, canvas: tk.Canvas) -> None:
        """Apply standard diagram bindings to *canvas*."""
        init_diagram_canvas(canvas, self.app)

    # ------------------------------------------------------------------
    # Generic subtree drawing
    # ------------------------------------------------------------------
    def draw_subtree_with_filter(self, canvas, root_event, visible_nodes):
        self.draw_connections_subtree(canvas, root_event, set())
        for n in visible_nodes:
            self.draw_node_on_canvas_pdf(canvas, n)

    def draw_subtree(self, canvas, root_event):
        canvas.delete("all")
        self.draw_connections_subtree(canvas, root_event, set())
        for n in self.app.get_all_nodes(root_event):
            self.draw_node_on_canvas_pdf(canvas, n)
        canvas.config(scrollregion=canvas.bbox("all"))

    def draw_connections_subtree(self, canvas, node, drawn_ids):
        if id(node) in drawn_ids:
            return
        drawn_ids.add(id(node))
        if node.is_page and node.node_type.upper() != "TOP EVENT":
            return
        region_width = 100 * self.app.zoom
        parent_bottom = (node.x * self.app.zoom, node.y * self.app.zoom + 40 * self.app.zoom)
        N = len(node.children)
        for i, child in enumerate(node.children):
            parent_conn = (
                node.x * self.app.zoom - region_width / 2 + (i + 0.5) * (region_width / N),
                parent_bottom[1],
            )
            child_top = (child.x * self.app.zoom, child.y * self.app.zoom - 45 * self.app.zoom)
            fta_drawing_helper.draw_90_connection(
                canvas, parent_conn, child_top, outline_color="dimgray", line_width=1
            )
        for child in node.children:
            self.draw_connections_subtree(canvas, child, drawn_ids)

    def draw_node_on_canvas_pdf(self, canvas, node):
        if not node.is_primary_instance and hasattr(node, "original") and node.original:
            base_label = node.original.display_label
            subtype = node.original.input_subtype or "N/A"
            equation_text = node.original.equation
            detailed_eq = node.original.detailed_equation
        else:
            base_label = node.display_label
            subtype = node.input_subtype or "N/A"
            equation_text = node.equation
            detailed_eq = node.detailed_equation

        score_type = base_label.split("[")[0].strip()
        fill_color = self.app.get_node_fill_color(node, getattr(canvas, "diagram_mode", None))
        eff_x = node.x * self.app.zoom
        eff_y = node.y * self.app.zoom

        if self.app.project_properties.get("pdf_detailed_formulas", True):
            top_text = (
                f"Type: {node.node_type}\n"
                f"Score: {score_type}\n"
                f"Subtype: {subtype}\n"
                f"Desc: {node.description}"
            )
        else:
            if node.quant_value is not None:
                score_value = float(node.quant_value)
                discrete = AutoML_Helper.discretize_level(score_value)
            else:
                discrete = "N/A"
            top_text = (
                f"Type: {node.node_type}\n"
                f"{score_type} = {discrete}\n"
                f"Subtype: {subtype}"
            )

        bottom_text = node.name
        node_type_upper = node.node_type.upper()

        if node.is_page:
            fta_drawing_helper.draw_triangle_shape(
                canvas,
                eff_x,
                eff_y,
                scale=40 * self.app.zoom,
                top_text=top_text,
                bottom_text=bottom_text,
                fill=fill_color,
                outline_color="dimgray",
                line_width=1,
                font_obj=self.app.diagram_font,
            )
        elif node_type_upper in ["CONFIDENCE LEVEL", "ROBUSTNESS SCORE"]:
            fta_drawing_helper.draw_circle_event_clone_shape(
                canvas,
                eff_x,
                eff_y,
                45 * self.app.zoom,
                top_text=top_text,
                bottom_text=bottom_text,
                fill=fill_color,
                outline_color="dimgray",
                line_width=1,
                font_obj=self.app.diagram_font,
            )
        elif node_type_upper in GATE_NODE_TYPES:
            if node.gate_type.upper() == "OR":
                fta_drawing_helper.draw_rotated_or_gate_clone_shape(
                    canvas,
                    eff_x,
                    eff_y,
                    scale=40 * self.app.zoom,
                    top_text=top_text,
                    bottom_text=bottom_text,
                    fill=fill_color,
                    outline_color="dimgray",
                    line_width=1,
                    font_obj=self.app.diagram_font,
                )
            else:
                fta_drawing_helper.draw_rotated_and_gate_clone_shape(
                    canvas,
                    eff_x,
                    eff_y,
                    scale=40 * self.app.zoom,
                    top_text=top_text,
                    bottom_text=bottom_text,
                    fill=fill_color,
                    outline_color="dimgray",
                    line_width=1,
                    font_obj=self.app.diagram_font,
                )
        else:
            fta_drawing_helper.draw_circle_event_clone_shape(
                canvas,
                eff_x,
                eff_y,
                45 * self.app.zoom,
                top_text=top_text,
                bottom_text=bottom_text,
                fill=fill_color,
                outline_color="dimgray",
                line_width=1,
                font_obj=self.app.diagram_font,
            )

        if self.app.project_properties.get("pdf_detailed_formulas", True):
            canvas.create_text(
                eff_x - 80 * self.app.zoom,
                eff_y - 15 * self.app.zoom,
                text=equation_text,
                anchor="e",
                fill="gray",
                font=self.app.diagram_font,
            )
            canvas.create_text(
                eff_x - 80 * self.app.zoom,
                eff_y + 15 * self.app.zoom,
                text=detailed_eq,
                anchor="e",
                fill="gray",
                font=self.app.diagram_font,
            )

    # ------------------------------------------------------------------
    # Main canvas drawing
    # ------------------------------------------------------------------
    def draw_connections(self, node, drawn_ids=None):
        if drawn_ids is None:
            drawn_ids = set()
        if id(node) in drawn_ids:
            return
        drawn_ids.add(id(node))
        if node.is_page and node.is_primary_instance:
            return
        if node.children:
            region_width = 100 * self.app.zoom
            parent_bottom = (node.x * self.app.zoom, node.y * self.app.zoom + 40 * self.app.zoom)
            N = len(node.children)
            for i, child in enumerate(node.children):
                parent_conn = (
                    node.x * self.app.zoom - region_width / 2 + (i + 0.5) * (region_width / N),
                    parent_bottom[1],
                )
                child_top = (child.x * self.app.zoom, child.y * self.app.zoom - 45 * self.app.zoom)
                fta_drawing_helper.draw_90_connection(
                    self.app.canvas, parent_conn, child_top, outline_color="dimgray", line_width=1
                )
            for child in node.children:
                self.draw_connections(child, drawn_ids)

    def draw_node(self, node):
        source = node if node.is_primary_instance else node.original
        if node.is_primary_instance:
            display_label = source.display_label
        else:
            display_label = source.display_label + " (clone)"

        subtype_text = source.input_subtype if source.input_subtype else "N/A"
        top_text = (
            f"Type: {source.node_type}\n"
            f"Subtype: {subtype_text}\n"
            f"{display_label}\n"
            f"Desc: {source.description}\n\n"
            f"Rationale: {source.rationale}"
        )
        bottom_text = source.name
        eff_x = node.x * self.app.zoom
        eff_y = node.y * self.app.zoom

        if node == self.app.selected_node:
            outline_color = "red"
            line_width = 2
        elif node.unique_id in self.app.diff_nodes:
            outline_color = "blue"
            line_width = 2
        else:
            outline_color = "dimgray"
            line_width = 1

        fill_color = self.app.get_node_fill_color(
            node, getattr(self.app.canvas, "diagram_mode", None)
        )
        font_obj = self.app.diagram_font
        node_type_upper = source.node_type.upper()

        if not node.is_primary_instance:
            if source.is_page:
                fta_drawing_helper.draw_triangle_shape(
                    self.app.canvas,
                    eff_x,
                    eff_y,
                    scale=40 * self.app.zoom,
                    top_text=top_text,
                    bottom_text=bottom_text,
                    fill=fill_color,
                    outline_color=outline_color,
                    line_width=line_width,
                    font_obj=font_obj,
                    obj_id=node.unique_id,
                )
            elif node_type_upper in GATE_NODE_TYPES:
                if source.gate_type.upper() == "OR":
                    fta_drawing_helper.draw_rotated_or_gate_clone_shape(
                        self.app.canvas,
                        eff_x,
                        eff_y,
                        scale=40 * self.app.zoom,
                        top_text=top_text,
                        bottom_text=bottom_text,
                        fill=fill_color,
                        outline_color=outline_color,
                        line_width=line_width,
                        font_obj=font_obj,
                        obj_id=node.unique_id,
                    )
                else:
                    fta_drawing_helper.draw_rotated_and_gate_clone_shape(
                        self.app.canvas,
                        eff_x,
                        eff_y,
                        scale=40 * self.app.zoom,
                        top_text=top_text,
                        bottom_text=bottom_text,
                        fill=fill_color,
                        outline_color=outline_color,
                        line_width=line_width,
                        font_obj=font_obj,
                        obj_id=node.unique_id,
                    )
            elif node_type_upper in ["CONFIDENCE LEVEL", "ROBUSTNESS SCORE"]:
                fta_drawing_helper.draw_circle_event_clone_shape(
                    self.app.canvas,
                    eff_x,
                    eff_y,
                    45 * self.app.zoom,
                    top_text=top_text,
                    bottom_text=bottom_text,
                    fill=fill_color,
                    outline_color=outline_color,
                    line_width=line_width,
                    font_obj=font_obj,
                    obj_id=node.unique_id,
                )
            else:
                fta_drawing_helper.draw_circle_event_clone_shape(
                    self.app.canvas,
                    eff_x,
                    eff_y,
                    45 * self.app.zoom,
                    top_text=top_text,
                    bottom_text=bottom_text,
                    fill=fill_color,
                    outline_color=outline_color,
                    line_width=line_width,
                    font_obj=font_obj,
                    obj_id=node.unique_id,
                )
        else:
            if node_type_upper in GATE_NODE_TYPES:
                if source.is_page and source != self.app.root_node:
                    fta_drawing_helper.draw_triangle_shape(
                        self.app.canvas,
                        eff_x,
                        eff_y,
                        scale=40 * self.app.zoom,
                        top_text=top_text,
                        bottom_text=bottom_text,
                        fill=fill_color,
                        outline_color=outline_color,
                        line_width=line_width,
                        font_obj=font_obj,
                        obj_id=node.unique_id,
                    )
                else:
                    if source.gate_type.upper() == "OR":
                        fta_drawing_helper.draw_rotated_or_gate_shape(
                            self.app.canvas,
                            eff_x,
                            eff_y,
                            scale=40 * self.app.zoom,
                            top_text=top_text,
                            bottom_text=bottom_text,
                            fill=fill_color,
                            outline_color=outline_color,
                            line_width=line_width,
                            font_obj=font_obj,
                            obj_id=node.unique_id,
                        )
                    else:
                        fta_drawing_helper.draw_rotated_and_gate_shape(
                            self.app.canvas,
                            eff_x,
                            eff_y,
                            scale=40 * self.app.zoom,
                            top_text=top_text,
                            bottom_text=bottom_text,
                            fill=fill_color,
                            outline_color=outline_color,
                            line_width=line_width,
                            font_obj=font_obj,
                            obj_id=node.unique_id,
                        )
            elif node_type_upper in ["CONFIDENCE LEVEL", "ROBUSTNESS SCORE"]:
                fta_drawing_helper.draw_circle_event_shape(
                    self.app.canvas,
                    eff_x,
                    eff_y,
                    45 * self.app.zoom,
                    top_text=top_text,
                    bottom_text=bottom_text,
                    fill=fill_color,
                    outline_color=outline_color,
                    line_width=line_width,
                    font_obj=font_obj,
                    obj_id=node.unique_id,
                )
            else:
                fta_drawing_helper.draw_circle_event_shape(
                    self.app.canvas,
                    eff_x,
                    eff_y,
                    45 * self.app.zoom,
                    top_text=top_text,
                    bottom_text=bottom_text,
                    fill=fill_color,
                    outline_color=outline_color,
                    line_width=line_width,
                    font_obj=font_obj,
                    obj_id=node.unique_id,
                )

        if source.equation:
            self.app.canvas.create_text(
                eff_x - 80 * self.app.zoom,
                eff_y - 15 * self.app.zoom,
                text=source.equation,
                anchor="e",
                fill="gray",
                font=self.app.diagram_font,
            )
        if source.detailed_equation:
            self.app.canvas.create_text(
                eff_x - 80 * self.app.zoom,
                eff_y + 15 * self.app.zoom,
                text=source.detailed_equation,
                anchor="e",
                fill="gray",
                font=self.app.diagram_font,
            )

        if self.app.occurrence_counts.get(node.unique_id, 0) > 1:
            marker_x = eff_x + 30 * self.app.zoom
            marker_y = eff_y - 30 * self.app.zoom
            fta_drawing_helper.draw_shared_marker(self.app.canvas, marker_x, marker_y, self.app.zoom)

        if self.app.review_data:
            unresolved = any(
                c.node_id == node.unique_id and not c.resolved
                for c in self.app.review_data.comments
            )
            if unresolved:
                self.app.canvas.create_oval(
                    eff_x + 35 * self.app.zoom,
                    eff_y + 35 * self.app.zoom,
                    eff_x + 45 * self.app.zoom,
                    eff_y + 45 * self.app.zoom,
                    fill="yellow",
                    outline=StyleManager.get_instance().outline_color,
                )

    # ------------------------------------------------------------------
    # Page diagram delegation
    # ------------------------------------------------------------------
    def draw_page_subtree(self, page_root):
        return self.app.pages_and_paa.draw_page_subtree(page_root)

    def draw_page_grid(self):
        return self.app.pages_and_paa.draw_page_grid()

    def draw_page_connections_subtree(self, node, visited_ids):
        return self.app.pages_and_paa.draw_page_connections_subtree(node, visited_ids)

    def draw_page_nodes_subtree(self, node):
        return self.app.pages_and_paa.draw_page_nodes_subtree(node)

    def draw_node_on_page_canvas(self, *args, **kwargs):
        return self.app.pages_and_paa.draw_node_on_page_canvas(*args, **kwargs)

    # ------------------------------------------------------------------
    # Cause-effect diagram rendering
    # ------------------------------------------------------------------
    def draw_cause_effect_row(self, canvas, row):
        import textwrap

        nodes, edges, pos = self.app._build_cause_effect_graph(row)

        color_map = {
            "hazard": "#F08080",
            "malfunction": "#ADD8E6",
            "failure_mode": "#FFA500",
            "fault": "#D3D3D3",
            "fi": "#FFFFE0",
            "tc": "#90EE90",
            "attack_path": "#E0FFFF",
            "threat": "#FFB6C1",
        }

        canvas.delete("all")

        scale = 80
        x_off = 50
        y_off = 50
        box_w = 80
        box_h = 40

        def to_canvas(x: float, y: float) -> tuple[float, float]:
            return x_off + scale * x, y_off + scale * y

        for u, v in edges:
            x1, y1 = to_canvas(*pos[u])
            x2, y2 = to_canvas(*pos[v])
            canvas.create_line(x1, y1, x2, y2, arrow=tk.LAST, tags="edge")
            canvas.create_text(
                (x1 + x2) / 2,
                (y1 + y2) / 2,
                text="caused by",
                font=("TkDefaultFont", 8),
                tags="edge",
            )

        for n, (x, y) in pos.items():
            label, kind = nodes.get(n, (n, ""))
            color = color_map.get(kind, "white")
            cx, cy = to_canvas(x, y)
            canvas.create_rectangle(
                cx - box_w / 2,
                cy - box_h / 2,
                cx + box_w / 2,
                cy + box_h / 2,
                fill=color,
                outline=StyleManager.get_instance().outline_color,
                tags="node",
            )
            label = textwrap.fill(str(label), 20)
            canvas.create_text(
                cx,
                cy,
                text=label,
                width=box_w - 10,
                font=("TkDefaultFont", 8),
                tags="node",
            )

        canvas.config(scrollregion=canvas.bbox("all"))
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)
        canvas.update_idletasks()
