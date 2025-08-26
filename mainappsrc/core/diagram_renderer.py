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

"""Centralised renderer for AutoML diagrams.

This class consolidates drawing, capture and view helpers that were
previously spread across :mod:`automl_core`.  The application now
invokes these operations via :class:`DiagramRenderer` which keeps
:mod:`automl_core` slimmer and easier to maintain.
"""

from typing import Any, Iterable, Set

import csv
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from gui.styles.style_manager import StyleManager
from gui.utils.drawing_helper import fta_drawing_helper
from gui.utils.config_utils import AutoML_Helper, GATE_NODE_TYPES


class DiagramRenderer:
    """Delegate drawing and capture operations for AutoML diagrams."""

    def __init__(self, app: Any) -> None:
        self.app = app

    # ------------------------------------------------------------------
    # Basic node and subtree drawing
    # ------------------------------------------------------------------
    def draw_subtree_with_filter(self, canvas: tk.Canvas, root_event, visible_nodes: Iterable) -> None:
        visible_nodes = list(visible_nodes)
        visible_ids = {n.unique_id for n in visible_nodes}
        self.draw_connections_subtree(canvas, root_event, set(), visible_ids)
        for n in visible_nodes:
            self.draw_node_on_canvas_pdf(canvas, n)

    def draw_subtree(self, canvas: tk.Canvas, root_event) -> None:
        canvas.delete("all")
        visible_nodes = list(self.iter_visible_nodes(canvas, root_event))
        visible_ids = {n.unique_id for n in visible_nodes}
        self.draw_connections_subtree(canvas, root_event, set(), visible_ids)
        for n in visible_nodes:
            self.draw_node_on_canvas_pdf(canvas, n)
        canvas.config(scrollregion=canvas.bbox("all"))

    def iter_visible_nodes(self, canvas: tk.Canvas, root_event) -> Iterable:
        """Yield nodes that fall within the current canvas viewport."""
        x0 = canvas.canvasx(0)
        y0 = canvas.canvasy(0)
        x1 = canvas.canvasx(canvas.winfo_width())
        y1 = canvas.canvasy(canvas.winfo_height())
        padding = 50 * self.app.zoom
        for n in self.app.get_all_nodes(root_event):
            eff_x = n.x * self.app.zoom
            eff_y = n.y * self.app.zoom
            if x0 - padding <= eff_x <= x1 + padding and y0 - padding <= eff_y <= y1 + padding:
                yield n

    def draw_connections_subtree(self, canvas: tk.Canvas, node, drawn_ids: Set[int], visible_ids: Set[int] | None = None) -> None:
        if id(node) in drawn_ids:
            return
        drawn_ids.add(id(node))
        if node.is_page and node.node_type.upper() != "TOP EVENT":
            return
        region_width = 100 * self.app.zoom
        parent_bottom = (node.x * self.app.zoom, node.y * self.app.zoom + 40 * self.app.zoom)
        N = len(node.children)
        for i, child in enumerate(node.children):
            if visible_ids is None or node.unique_id in visible_ids or child.unique_id in visible_ids:
                parent_conn = (
                    node.x * self.app.zoom - region_width / 2 + (i + 0.5) * (region_width / N),
                    parent_bottom[1],
                )
                child_top = (child.x * self.app.zoom, child.y * self.app.zoom - 45 * self.app.zoom)
                fta_drawing_helper.draw_90_connection(
                    canvas, parent_conn, child_top, outline_color="dimgray", line_width=1
                )
        for child in node.children:
            self.draw_connections_subtree(canvas, child, drawn_ids, visible_ids)

    def draw_node_on_canvas_pdf(self, canvas: tk.Canvas, node) -> None:
        # For cloned nodes, use the original's values.
        if not node.is_primary_instance and getattr(node, "original", None):
            base_label = node.original.display_label
            subtype = node.original.input_subtype or "N/A"
            equation_text = node.original.equation
            detailed_eq = node.original.detailed_equation
        else:
            base_label = node.display_label
            subtype = node.input_subtype or "N/A"
            equation_text = node.equation
            detailed_eq = node.detailed_equation

        # Extract the score type from the base label ("Required Rigor [4]" -> "Required Rigor").
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
    # Canvas operations used by main FTA view
    # ------------------------------------------------------------------
    def draw_connections(self, node, drawn_ids: Set[int] | None = None) -> None:
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

    def draw_node(self, node) -> None:
        source = node if node.is_primary_instance else node.original

        display_label = source.display_label if node.is_primary_instance else source.display_label + " (clone)"
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

        fill_color = self.app.get_node_fill_color(node, getattr(self.app.canvas, "diagram_mode", None))
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
                c.node_id == node.unique_id and not c.resolved for c in self.app.review_data.comments
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
    # Page diagram drawing helpers (delegation to pages_and_paa)
    # ------------------------------------------------------------------
    def draw_node_on_page_canvas(self, *args, **kwargs):  # pragma: no cover - delegation
        return self.app.pages_and_paa.draw_node_on_page_canvas(*args, **kwargs)

    def draw_page_grid(self, *args, **kwargs):  # pragma: no cover - delegation
        return self.app.pages_and_paa.draw_page_grid(*args, **kwargs)

    def draw_page_nodes_subtree(self, *args, **kwargs):  # pragma: no cover - delegation
        return self.app.pages_and_paa.draw_page_nodes_subtree(*args, **kwargs)

    def draw_page_connections_subtree(self, *args, **kwargs):  # pragma: no cover - delegation
        return self.app.pages_and_paa.draw_page_connections_subtree(*args, **kwargs)

    def draw_page_subtree(self, *args, **kwargs):  # pragma: no cover - delegation
        return self.app.pages_and_paa.draw_page_subtree(*args, **kwargs)

    # ------------------------------------------------------------------
    # Rendering and canvas management
    # ------------------------------------------------------------------
    def render_cause_effect_diagram(self, row) -> Any:
        """Render *row* as a PIL image matching the on-screen diagram."""
        try:
            from PIL import Image, ImageDraw, ImageFont
        except Exception:
            return None
        import textwrap, math

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

        scale = 80
        x_off = 50
        y_off = 50
        box_w = 80
        box_h = 40

        max_x = max(x for x, _ in pos.values())
        max_y = max(y for _, y in pos.values())
        width = int(x_off * 2 + scale * max_x + box_w)
        height = int(y_off * 2 + scale * max_y + box_h)

        img = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()

        def to_canvas(x: float, y: float) -> tuple[float, float]:
            return x_off + scale * x, y_off + scale * y

        for u, v in edges:
            x1, y1 = to_canvas(*pos[u])
            x2, y2 = to_canvas(*pos[v])
            draw.line((x1, y1, x2, y2), fill="black")
            dx, dy = x2 - x1, y2 - y1
            length = math.hypot(dx, dy) or 1
            ux, uy = dx / length, dy / length
            arrow = 10
            px, py = x2 - arrow * ux, y2 - arrow * uy
            perp = (-uy, ux)
            left = (px + perp[0] * arrow / 2, py + perp[1] * arrow / 2)
            right = (px - perp[0] * arrow / 2, py - perp[1] * arrow / 2)
            draw.polygon([ (x2, y2), left, right ], fill="black")
            if hasattr(draw, "text"):
                draw.text(((x1 + x2) / 2, (y1 + y2) / 2), "caused by", fill="black", font=font, anchor="mm")

        for n, (x, y) in pos.items():
            label, kind = nodes.get(n, (n, ""))
            color = color_map.get(kind, "white")
            cx, cy = to_canvas(x, y)
            rect = [cx - box_w / 2, cy - box_h / 2, cx + box_w / 2, cy + box_h / 2]
            draw.rectangle(
                rect,
                fill=color,
                outline=StyleManager.get_instance().outline_color,
            )
            text = textwrap.fill(str(label), 20)
            bbox = draw.multiline_textbbox((0, 0), text, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            draw.multiline_text((cx - tw / 2, cy - th / 2), text, font=font, align="center")

        return img

    def redraw_canvas(self) -> None:
        if not hasattr(self.app, "canvas") or self.app.canvas is None or not self.app.canvas.winfo_exists():
            return
        self.app.canvas.delete("all")
        if hasattr(self.app, "fta_drawing_helper"):
            self.app.fta_drawing_helper.clear_cache()
        drawn_ids: Set[int] = set()
        for top_event in self.app.top_events:
            self.draw_connections(top_event, drawn_ids)
        all_nodes = []
        for top_event in self.app.top_events:
            all_nodes.extend(self.app.get_all_nodes(top_event))
        for node in all_nodes:
            self.draw_node(node)
        self.app.canvas.config(scrollregion=self.app.canvas.bbox("all"))

    def zoom_in(self) -> None:
        self.app.zoom *= 1.2
        self.app.diagram_font.config(size=int(8 * self.app.zoom))
        self.redraw_canvas()

    def zoom_out(self) -> None:
        self.app.zoom /= 1.2
        self.app.diagram_font.config(size=int(8 * self.app.zoom))
        self.redraw_canvas()

    def create_diagram_image(self):  # pragma: no cover - delegation
        return self.app.reporting_export.create_diagram_image()

    def create_diagram_image_without_grid(self):  # pragma: no cover - delegation
        return self.app.reporting_export.create_diagram_image_without_grid()

    def save_diagram_png(self):  # pragma: no cover - delegation
        return self.app.diagram_export_app.save_diagram_png()

    def close_page_diagram(self) -> None:
        app = self.app
        if app.page_history:
            prev = app.page_history.pop()
            for widget in app.canvas_frame.winfo_children():
                widget.destroy()
            if prev is None:
                app.canvas = tk.Canvas(app.canvas_frame, bg=StyleManager.get_instance().canvas_bg)
                app.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                app.hbar = ttk.Scrollbar(app.canvas_frame, orient=tk.HORIZONTAL, command=app.canvas.xview)
                app.hbar.pack(side=tk.BOTTOM, fill=tk.X)
                app.vbar = ttk.Scrollbar(app.canvas_frame, orient=tk.VERTICAL, command=app.canvas.yview)
                app.vbar.pack(side=tk.RIGHT, fill=tk.Y)
                app.canvas.config(
                    xscrollcommand=app.hbar.set,
                    yscrollcommand=app.vbar.set,
                    scrollregion=(0, 0, 2000, 2000),
                )
                app.canvas.bind("<ButtonPress-3>", app.on_right_mouse_press)
                app.canvas.bind("<B3-Motion>", app.on_right_mouse_drag)
                app.canvas.bind("<Button-1>", app.on_canvas_click)
                app.canvas.bind("<B1-Motion>", app.on_canvas_drag)
                app.canvas.bind("<ButtonRelease-1>", app.on_canvas_release)
                app.canvas.bind("<Double-Button-1>", app.on_canvas_double_click)
                app.canvas.bind("<ButtonRelease-3>", app.on_right_mouse_release)
                app.update_views()
                app.page_diagram = None
            else:
                app.window_controllers.open_page_diagram(prev)
        else:
            for widget in app.canvas_frame.winfo_children():
                widget.destroy()
            app.canvas = tk.Canvas(app.canvas_frame, bg=StyleManager.get_instance().canvas_bg)
            app.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            app.hbar = ttk.Scrollbar(app.canvas_frame, orient=tk.HORIZONTAL, command=app.canvas.xview)
            app.hbar.pack(side=tk.BOTTOM, fill=tk.X)
            app.vbar = ttk.Scrollbar(app.canvas_frame, orient=tk.VERTICAL, command=app.canvas.yview)
            app.vbar.pack(side=tk.RIGHT, fill=tk.Y)
            app.canvas.config(
                xscrollcommand=app.hbar.set,
                yscrollcommand=app.vbar.set,
                scrollregion=(0, 0, 2000, 2000),
            )
            app.canvas.bind("<ButtonPress-3>", app.on_right_mouse_press)
            app.canvas.bind("<B3-Motion>", app.on_right_mouse_drag)
            app.canvas.bind("<Button-1>", app.on_canvas_click)
            app.canvas.bind("<B1-Motion>", app.on_canvas_drag)
            app.canvas.bind("<ButtonRelease-1>", app.on_canvas_release)
            app.canvas.bind("<Double-Button-1>", app.on_canvas_double_click)
            app.canvas.bind("<ButtonRelease-3>", app.on_right_mouse_release)
            app.update_views()
            app.page_diagram = None

    # ------------------------------------------------------------------
    # Capture helpers
    # ------------------------------------------------------------------
    def capture_event_diagram(self, *args, **kwargs):  # pragma: no cover - no implementation
        """Return a PIL Image of the current event diagram if supported."""
        return None

    def capture_page_diagram(self, page_node):  # pragma: no cover - delegation
        return self.app.pages_and_paa.capture_page_diagram(page_node)

    def capture_diff_diagram(self, top_event):  # pragma: no cover - delegation
        return self.app.review_manager.capture_diff_diagram(top_event)

    def capture_sysml_diagram(self, diagram):
        """Return a PIL Image of the given SysML diagram."""
        from io import BytesIO
        from PIL import Image
        from gui.windows.use_case_diagram_window import UseCaseDiagramWindow
        from gui.windows.activity_diagram_window import ActivityDiagramWindow
        from gui.windows.block_diagram_window import BlockDiagramWindow
        from gui.windows.internal_block_diagram_window import InternalBlockDiagramWindow
        from gui.windows.control_flow_diagram_window import ControlFlowDiagramWindow
        from gui.windows.governance_diagram_window import GovernanceDiagramWindow

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

    def capture_cbn_diagram(self, doc):
        """Return a PIL Image of the given Causal Bayesian Network diagram."""
        from io import BytesIO
        from PIL import Image
        from gui.causal_bayesian_network_window import CausalBayesianNetworkWindow

        temp = tk.Toplevel(self.app.root)
        temp.withdraw()
        try:
            win = CausalBayesianNetworkWindow(temp, self.app)
            win.doc_var.set(doc.name)
            win.select_doc()
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
        finally:
            temp.destroy()
        return img.convert("RGB") if img else None

    def capture_gsn_diagram(self, diagram):
        """Return a PIL Image of the given GSN diagram."""
        from io import BytesIO
        from PIL import Image
        from gui.causal_bayesian_network_window import CausalBayesianNetworkWindow

        temp = tk.Toplevel(self.app.root)
        temp.withdraw()
        canvas = tk.Canvas(temp, bg=StyleManager.get_instance().canvas_bg, width=2000, height=2000)
        canvas.pack()

        try:
            diagram.draw(canvas)
        except Exception:
            temp.destroy()
            return None

        canvas.update()
        bbox = canvas.bbox("all")
        if not bbox:
            temp.destroy()
            return None
        x, y, x2, y2 = bbox
        width, height = x2 - x, y2 - y
        ps = canvas.postscript(colormode="color", x=x, y=y, width=width, height=height)
        ps_bytes = BytesIO(ps.encode("utf-8"))
        try:
            img = Image.open(ps_bytes)
            img.load(scale=3)
        except Exception:
            img = None
        temp.destroy()
        return img.convert("RGB") if img else None

    # ------------------------------------------------------------------
    # High-level views
    # ------------------------------------------------------------------
    def show_cause_effect_chain(self) -> None:
        """Display a table linking hazards to downstream events with an optional diagram."""
        data = self.app.build_cause_effect_data()
        if not data:
            messagebox.showinfo("Cause & Effect", "No data available")
            return

        win = tk.Toplevel(self.app.root)
        win.title("Cause & Effect Chain")

        nb = ttk.Notebook(win)
        nb.pack(fill=tk.BOTH, expand=True)

        table_frame = ttk.Frame(nb)
        diagram_frame = ttk.Frame(nb)
        nb.add(table_frame, text="Table")
        nb.add(diagram_frame, text="Diagram")

        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        diagram_frame.columnconfigure(0, weight=1)
        diagram_frame.rowconfigure(0, weight=1)

        cols = (
            "Hazard",
            "Malfunction",
            "Threats",
            "Attack Paths",
            "Failure Modes",
            "Faults",
            "Threat Scenarios",
            "Attack Paths",
            "FIs",
            "TCs",
        )

        tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        canvas = tk.Canvas(diagram_frame, bg=StyleManager.get_instance().canvas_bg)
        cvs_vsb = ttk.Scrollbar(diagram_frame, orient="vertical", command=canvas.yview)
        cvs_hsb = ttk.Scrollbar(diagram_frame, orient="horizontal", command=canvas.xview)
        canvas.configure(yscrollcommand=cvs_vsb.set, xscrollcommand=cvs_hsb.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        cvs_vsb.grid(row=0, column=1, sticky="ns")
        cvs_hsb.grid(row=1, column=0, sticky="ew")

        row_map = {}
        for row in data:
            iid = tree.insert(
                "",
                "end",
                values=(
                    row["hazard"],
                    row["malfunction"],
                    ", ".join(sorted(row["threats"].keys())),
                    ", ".join(sorted(row["attack_paths"])),
                    ", ".join(sorted(row["failure_modes"].keys())),
                    ", ".join(sorted(row["faults"])),
                    ", ".join(sorted(row["threats"].keys())),
                    ", ".join(sorted(row["attack_paths"])),
                    ", ".join(sorted(row["fis"])),
                    ", ".join(sorted(row["tcs"])),
                ),
            )
            row_map[iid] = row

        def draw_row(row):
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

        def on_select(event):
            sel = tree.selection()
            if sel:
                row = row_map.get(sel[0])
                if row:
                    draw_row(row)
                    nb.select(diagram_frame)

        tree.bind("<<TreeviewSelect>>", on_select)

        if row_map:
            first_iid = next(iter(row_map))
            tree.selection_set(first_iid)
            draw_row(row_map[first_iid])
            nb.select(diagram_frame)

        def export_csv():
            path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
            if not path:
                return
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(cols)
                for iid in tree.get_children():
                    writer.writerow(tree.item(iid, "values"))
            messagebox.showinfo("Export", "Cause & effect data exported")

        ttk.Button(win, text="Export CSV", command=export_csv).pack(pady=5)

    def show_common_cause_view(self) -> None:
        win = tk.Toplevel(self.app.root)
        win.title("Common Cause Toolbox")
        var_fmea = tk.BooleanVar(value=True)
        var_fmeda = tk.BooleanVar(value=True)
        var_fta = tk.BooleanVar(value=True)
        chk_frame = ttk.Frame(win)
        chk_frame.pack(anchor="w")
        ttk.Checkbutton(chk_frame, text="FMEA", variable=var_fmea).pack(side=tk.LEFT)
        ttk.Checkbutton(chk_frame, text="FMEDA", variable=var_fmeda).pack(side=tk.LEFT)
        ttk.Checkbutton(chk_frame, text="FTA", variable=var_fta).pack(side=tk.LEFT)
        tree_frame = ttk.Frame(win)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        tree = ttk.Treeview(tree_frame, columns=["Cause", "Events"], show="headings")
        for c in ["Cause", "Events"]:
            tree.heading(c, text=c)
            tree.column(c, width=150)
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        def refresh():
            tree.delete(*tree.get_children())
            events_by_cause = {}
            if var_fmea.get():
                for fmea in self.app.fmeas:
                    for be in fmea["entries"]:
                        cause = be.description
                        label = f"{fmea['name']}:{be.user_name or be.description or be.unique_id}"
                        events_by_cause.setdefault(cause, set()).add(label)
            if var_fmeda.get():
                for fmeda in self.app.fmedas:
                    for be in fmeda["entries"]:
                        cause = be.description
                        label = f"{fmeda['name']}:{be.user_name or be.description or be.unique_id}"
                        events_by_cause.setdefault(cause, set()).add(label)
            if var_fta.get():
                for be in self.app.get_all_basic_events():
                    cause = be.description or ""
                    label = be.user_name or f"BE {be.unique_id}"
                    events_by_cause.setdefault(cause, set()).add(label)
            for cause, evts in events_by_cause.items():
                if len(evts) > 1:
                    tree.insert("", "end", values=[cause, ", ".join(sorted(evts))])

        refresh()

        def export_csv():
            path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
            if not path:
                return
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Cause", "Events"])
                for iid in tree.get_children():
                    writer.writerow(tree.item(iid, "values"))
            messagebox.showinfo("Export", "Common cause data exported")

        btn_frame = ttk.Frame(win)
        btn_frame.pack()
        ttk.Button(btn_frame, text="Refresh", command=refresh).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(btn_frame, text="Export CSV", command=export_csv).pack(side=tk.LEFT, padx=5, pady=5)
