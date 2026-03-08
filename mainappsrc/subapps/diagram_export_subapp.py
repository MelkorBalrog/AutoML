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

"""Diagram export utilities for :class:`AutoMLApp`."""

from tkinter import filedialog
from PIL import Image, ImageDraw, ImageFont


class DiagramExportSubApp:
    """Provide diagram export helpers."""

    def __init__(self, app: "AutoMLApp") -> None:
        self.app = app

    # ------------------------------------------------------------------
    def save_diagram_png(self) -> None:
        app = self.app
        mb = app.messagebox
        margin = 50
        all_nodes = app.get_all_nodes(app.root_node)
        if not all_nodes:
            mb.showerror("Error", "No nodes to export.")
            return
        min_x = min(n.x for n in all_nodes) - margin
        min_y = min(n.y for n in all_nodes) - margin
        max_x = max(n.x for n in all_nodes) + margin
        max_y = max(n.y for n in all_nodes) + margin
        scale_factor = 4
        width = int((max_x - min_x) * scale_factor)
        height = int((max_y - min_y) * scale_factor)
        img = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(img)
        grid_size = app.grid_size
        for x in range(0, int(max_x - min_x) + 1, grid_size):
            x_pos = int(x * scale_factor)
            draw.line([(x_pos, 0), (x_pos, height)], fill="#ddd")
        for y in range(0, int(max_y - min_y) + 1, grid_size):
            y_pos = int(y * scale_factor)
            draw.line([(0, y_pos), (width, y_pos)], fill="#ddd")
        try:
            font = ImageFont.truetype("arial.ttf", 10 * scale_factor)
        except IOError:
            font = ImageFont.load_default()
        for node in all_nodes:
            eff_x = int((node.x - min_x) * scale_factor)
            eff_y = int((node.y - min_y) * scale_factor)
            radius = int(45 * scale_factor)
            bbox = [eff_x - radius, eff_y - radius, eff_x + radius, eff_y + radius]
            node_color = app.get_node_fill_color(
                node, getattr(app.canvas, "diagram_mode", None)
            )
            draw.ellipse(bbox, outline="dimgray", fill=node_color)
            text = node.name
            text_size = draw.textsize(text, font=font)
            text_x = eff_x - text_size[0] // 2
            text_y = eff_y - text_size[1] // 2
            draw.text((text_x, text_y), text, fill="black", font=font)
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png", filetypes=[("PNG files", "*.png")]
        )
        if file_path:
            try:
                img.save(file_path, "PNG")
                mb.showinfo(
                    "Saved", "High-resolution diagram exported as PNG."
                )
            except Exception as exc:
                mb.showerror("Save Error", f"An error occurred: {exc}")

    # ------------------------------------------------------------------
    def get_page_nodes(self, node):
        """Return a list of descendant nodes representing sub-pages."""
        result = []
        if node.is_page and node != self.app.root_node:
            result.append(node)
        for child in node.children:
            result.extend(self.get_page_nodes(child))
        return result

    # ------------------------------------------------------------------
    def capture_page_diagram(self, page_node):
        """Return a PIL image of *page_node* rendered off-screen."""
        from io import BytesIO
        import tkinter as tk
        from PIL import Image

        from .page_diagram import PageDiagram
        from gui.style_manager import StyleManager

        temp = tk.Toplevel(self.app.root)
        temp.withdraw()
        canvas = tk.Canvas(
            temp,
            bg=StyleManager.get_instance().canvas_bg,
            width=2000,
            height=2000,
        )
        canvas.pack()

        pd = PageDiagram(self.app, page_node, canvas)
        pd.redraw_canvas()

        canvas.delete("grid")
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
    def capture_gsn_diagram(self, diagram):
        """Return a PIL image of a GSN diagram."""
        from io import BytesIO
        import tkinter as tk
        from PIL import Image
        from gui.style_manager import StyleManager

        temp = tk.Toplevel(self.app.root)
        temp.withdraw()
        canvas = tk.Canvas(
            temp,
            bg=StyleManager.get_instance().canvas_bg,
            width=2000,
            height=2000,
        )
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
    def capture_sysml_diagram(self, diagram):
        """Return a PIL image of the given SysML diagram."""
        from io import BytesIO
        import tkinter as tk
        from PIL import Image
        from gui.style_manager import StyleManager

        app = self.app
        temp = tk.Toplevel(app.root)
        temp.withdraw()

        win = None
        if diagram.diag_type == "Use Case Diagram":
            win = app.use_case_diagram_app.create_export_window(temp, diagram)
        elif diagram.diag_type == "Activity Diagram":
            win = app.activity_diagram_app.create_export_window(temp, diagram)
        elif diagram.diag_type == "Block Diagram":
            win = app.block_diagram_app.create_export_window(temp, diagram)
        elif diagram.diag_type == "Internal Block Diagram":
            win = app.internal_block_diagram_app.create_export_window(temp, diagram)
        elif diagram.diag_type == "Control Flow Diagram":
            win = app.control_flow_diagram_app.create_export_window(temp, diagram)
        elif diagram.diag_type == "Governance Diagram":
            win = app.governance_manager.create_export_window(temp, diagram)
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

    # ------------------------------------------------------------------
    def capture_cbn_diagram(self, doc):
        """Return a PIL image of a Causal Bayesian Network diagram."""
        from io import BytesIO
        import tkinter as tk
        from PIL import Image
        from gui.style_manager import StyleManager

        app = self.app
        temp = tk.Toplevel(app.root)
        temp.withdraw()
        try:
            win = app.risk_app.create_cbn_export_window(app, temp)
            win.doc_var.set(doc.name)
            win.select_doc()
            win.canvas.update()
            bbox = win.canvas.bbox("all")
            if not bbox:
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

    # ------------------------------------------------------------------
    def capture_diff_diagram(self, top_event):
        """Return an image of the FTA diff versus the last version."""
        app = self.app
        if not app.versions:
            return self.capture_page_diagram(top_event)

        from io import BytesIO
        import json
        import sys
        import tkinter as tk
        from PIL import Image
        import difflib
        from gui.style_manager import StyleManager

        current = app.export_model_data(include_versions=False)
        base_data = app.versions[-1]["data"]

        def filter_events(data):
            return [t for t in data.get("top_events", []) if t["unique_id"] == top_event.unique_id]

        data1 = {"top_events": filter_events(base_data)}
        data2 = {"top_events": filter_events(current)}

        map1 = app.node_map_from_data(data1["top_events"])
        map2 = app.node_map_from_data(data2["top_events"])

        def build_conn_set(events):
            conns = set()
            def visit(d):
                for ch in d.get("children", []):
                    conns.add((d["unique_id"], ch["unique_id"]))
                    visit(ch)
            for t in events:
                visit(t)
            return conns

        conns1 = build_conn_set(data1["top_events"])
        conns2 = build_conn_set(data2["top_events"])

        conn_status = {}
        for c in conns1 | conns2:
            if c in conns1 and c not in conns2:
                conn_status[c] = "removed"
            elif c in conns2 and c not in conns1:
                conn_status[c] = "added"
            else:
                conn_status[c] = "existing"

        status = {}
        for nid in set(map1) | set(map2):
            if nid in map1 and nid not in map2:
                status[nid] = "removed"
            elif nid in map2 and nid not in map1:
                status[nid] = "added"
            else:
                if json.dumps(map1[nid], sort_keys=True) != json.dumps(map2[nid], sort_keys=True):
                    status[nid] = "added"
                else:
                    status[nid] = "existing"

        module = sys.modules.get(app.__class__.__module__)
        FaultTreeNodeCls = getattr(module, 'FaultTreeNode', None)
        if not FaultTreeNodeCls and app.top_events:
            FaultTreeNodeCls = type(app.top_events[0])
        new_roots = [FaultTreeNodeCls.from_dict(t) for t in data2["top_events"]]
        removed_ids = [nid for nid, st in status.items() if st == "removed"]
        for rid in removed_ids:
            if rid in map1:
                nd = map1[rid]
                new_roots.append(FaultTreeNodeCls.from_dict(nd))

        allow_ids = set()
        def collect_ids(d):
            allow_ids.add(d["unique_id"])
            for ch in d.get("children", []):
                collect_ids(ch)
        if top_event.unique_id in map1:
            collect_ids(map1[top_event.unique_id])
        if top_event.unique_id in map2:
            collect_ids(map2[top_event.unique_id])

        node_objs = {}
        def collect_nodes(n):
            if n.unique_id not in node_objs:
                node_objs[n.unique_id] = n
            for ch in n.children:
                collect_nodes(ch)
        for r in new_roots:
            collect_nodes(r)

        temp = tk.Toplevel(app.root)
        temp.withdraw()
        canvas = tk.Canvas(
            temp,
            bg=StyleManager.get_instance().canvas_bg,
            width=2000,
            height=2000,
        )
        canvas.pack()

        def draw_connections(n):
            if n.unique_id not in allow_ids:
                for ch in n.children:
                    draw_connections(ch)
                return
            region_width = 60
            parent_bottom = (n.x, n.y + 20)
            for i, ch in enumerate(n.children):
                if ch.unique_id not in allow_ids:
                    continue
                parent_conn = (
                    n.x - region_width / 2 + (i + 0.5) * (region_width / len(n.children)),
                    parent_bottom[1],
                )
                child_top = (ch.x, ch.y - 25)
                edge_st = conn_status.get((n.unique_id, ch.unique_id), "existing")
                if status.get(n.unique_id) == "removed" or status.get(ch.unique_id) == "removed":
                    edge_st = "removed"
                color = "gray"
                if edge_st == "added":
                    color = "blue"
                elif edge_st == "removed":
                    color = "red"
                if app.fta_drawing_helper:
                    app.fta_drawing_helper.draw_90_connection(
                        canvas, parent_conn, child_top, outline_color=color, line_width=1
                    )
                draw_connections(ch)

        def draw_node(n):
            if n.unique_id not in allow_ids:
                for ch in n.children:
                    draw_node(ch)
                return
            st = status.get(n.unique_id, "existing")
            color = "dimgray"
            if st == "added":
                color = "blue"
            elif st == "removed":
                color = "red"

            source = n if getattr(n, "is_primary_instance", True) else getattr(n, "original", n)
            subtype_text = source.input_subtype if source.input_subtype else "N/A"
            display_label = source.display_label
            old_data = map1.get(n.unique_id)
            new_data = map2.get(n.unique_id)

            def req_lines(reqs):
                return "; ".join(app.format_requirement_with_trace(r) for r in reqs)

            if old_data and new_data:
                desc_segments = [("Desc: ", "black")] + diff_segments(
                    old_data.get("description", ""), new_data.get("description", "")
                )
                rat_segments = [("Rationale: ", "black")] + diff_segments(
                    old_data.get("rationale", ""), new_data.get("rationale", "")
                )
            else:
                desc_segments = [("Desc: " + source.description, "black")]
                rat_segments = [("Rationale: " + source.rationale, "black")]
            req_segments = []
            segments = [
                (f"Type: {source.node_type}\n", "black"),
                (f"Subtype: {subtype_text}\n", "black"),
                (f"{display_label}\n", "black"),
            ] + desc_segments + [("\n\n", "black")] + rat_segments

            top_text = "".join(seg[0] for seg in segments)
            bottom_text = n.name
            fill = app.get_node_fill_color(n, getattr(canvas, "diagram_mode", None))
            eff_x, eff_y = n.x, n.y
            typ = n.node_type.upper()
            items_before = canvas.find_all()
            if typ in app.GATE_NODE_TYPES:
                if n.gate_type and n.gate_type.upper() == "OR":
                    if app.fta_drawing_helper:
                        app.fta_drawing_helper.draw_rotated_or_gate_shape(
                            canvas,
                            eff_x,
                            eff_y,
                            scale=40,
                            top_text=top_text,
                            bottom_text=bottom_text,
                            fill=fill,
                            outline_color=color,
                            line_width=2,
                        )
                else:
                    if app.fta_drawing_helper:
                        app.fta_drawing_helper.draw_rotated_and_gate_shape(
                            canvas,
                            eff_x,
                            eff_y,
                            scale=40,
                            top_text=top_text,
                            bottom_text=bottom_text,
                            fill=fill,
                            outline_color=color,
                            line_width=2,
                        )
            else:
                if app.fta_drawing_helper:
                    app.fta_drawing_helper.draw_circle_event_shape(
                        canvas,
                        eff_x,
                        eff_y,
                        45,
                        top_text=top_text,
                        bottom_text=bottom_text,
                        fill=fill,
                        outline_color=color,
                        line_width=2,
                    )

            items_after = canvas.find_all()
            text_id = None
            for item in items_after:
                if item in items_before:
                    continue
                if canvas.type(item) == "text" and canvas.itemcget(item, "text") == top_text:
                    text_id = item
                    break

            if text_id and any(c in ("red", "blue") for _, c in segments):
                bbox = canvas.bbox(text_id)
                cx = (bbox[0] + bbox[2]) / 2
                cy = (bbox[1] + bbox[3]) / 2
                canvas.itemconfigure(text_id, state="hidden")
                draw_segment_text(canvas, cx, cy, segments, app.diagram_font)
            for ch in n.children:
                draw_node(ch)

        def diff_segments(old, new):
            matcher = difflib.SequenceMatcher(None, old, new)
            segments = []
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag == "equal":
                    segments.append((old[i1:i2], "black"))
                elif tag == "delete":
                    segments.append((old[i1:i2], "red"))
                elif tag == "insert":
                    segments.append((new[j1:j2], "blue"))
                elif tag == "replace":
                    segments.append((old[i1:i2], "red"))
                    segments.append((new[j1:j2], "blue"))
            return segments

        def draw_segment_text(canvas, cx, cy, segments, font_obj):
            lines = [[]]
            for text, color in segments:
                parts = text.split("\n")
                for idx, part in enumerate(parts):
                    if idx > 0:
                        lines.append([])
                    lines[-1].append((part, color))
            line_height = font_obj.metrics("linespace")
            total_height = line_height * len(lines)
            start_y = cy - total_height / 2
            for line in lines:
                line_width = sum(font_obj.measure(part) for part, _ in line)
                start_x = cx - line_width / 2
                x = start_x
                for part, color in line:
                    if part:
                        canvas.create_text(
                            x,
                            start_y,
                            text=part,
                            anchor="nw",
                            fill=color,
                            font=font_obj,
                        )
                        x += font_obj.measure(part)
                start_y += line_height

        for r in new_roots:
            draw_connections(r)
            draw_node(r)

        existing_pairs = set()
        for p in node_objs.values():
            for ch in p.children:
                existing_pairs.add((p.unique_id, ch.unique_id))
        for (pid, cid), st in conn_status.items():
            if st != "removed":
                continue
            if (pid, cid) in existing_pairs:
                continue
            if pid in node_objs and cid in node_objs and pid in allow_ids and cid in allow_ids:
                parent = node_objs[pid]
                child = node_objs[cid]
                parent_pt = (parent.x, parent.y + 20)
                child_pt = (child.x, child.y - 25)
                if app.fta_drawing_helper:
                    app.fta_drawing_helper.draw_90_connection(
                        canvas, parent_pt, child_pt, outline_color="red", line_width=1
                    )

        canvas.update()
        bbox = canvas.bbox("all")
        if not bbox:
            temp.destroy()
            return None
        x, y, x2, y2 = bbox
        ps = canvas.postscript(colormode="color", x=x, y=y, width=x2 - x, height=y2 - y)
        ps_bytes = BytesIO(ps.encode("utf-8"))
        try:
            img = Image.open(ps_bytes)
            img.load(scale=3)
        except Exception:
            img = None
        temp.destroy()
        return img.convert("RGB") if img else None
