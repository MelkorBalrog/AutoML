# Author: Miguel Marina <karel.capek.robotics@gmail.com>
import math
import tkinter as tk
import tkinter.font as tkFont
from gui.style_manager import StyleManager

TEXT_BOX_COLOR = "#CFD8DC"

# Basic mapping of a few common color names to their hex equivalents. The
# gradient routines expect ``#RRGGBB`` colors; previously passing a named color
# such as ``"lightyellow"`` caused a ``ValueError`` when converting to integers.
# The small table below covers the named colors used by the drawing helpers and
# can be extended easily if additional names are required.
_NAMED_COLORS = {
    "lightgray": "#d3d3d3",
    "lightgrey": "#d3d3d3",
    "lightblue": "#add8e6",
    "lightyellow": "#ffffe0",
}

# Basic mapping of a few common color names to their hex equivalents. The
# gradient routines expect ``#RRGGBB`` colors; previously passing a named color
# such as ``"lightyellow"`` caused a ``ValueError`` when converting to integers.
# The small table below covers the named colors used by the drawing helpers and
# can be extended easily if additional names are required.
_NAMED_COLORS = {
    "lightgray": "#d3d3d3",
    "lightgrey": "#d3d3d3",
    "lightblue": "#add8e6",
    "lightyellow": "#ffffe0",
}

class FTADrawingHelper:
    """
    A helper class that provides drawing functions for fault tree diagrams.
    These methods can be used to draw shapes (gates, events, connectors, etc.)
    onto a tkinter Canvas.
    """
    def __init__(self):
        pass

    def clear_cache(self):
        """No-op for API compatibility."""
        pass

    def _resolve_outline(self, color: str | None) -> str:
        """Return *color* or the style manager's default outline color."""
        if color is None:
            return StyleManager.get_instance().get_outline_color()
        return color

    def _interpolate_color(self, color: str, ratio: float) -> str:
        """Return *color* blended with white by *ratio* (0..1)."""
        # ``color`` may be provided as ``#RRGGBB`` or a Tk-style name such as
        # ``"lightgray"``.  Map known names to their hex representation so the
        # interpolation math can operate on integers.
        if not color.startswith("#"):
            color = _NAMED_COLORS.get(color.lower(), color)

        # Fallback to black if the color string is still not a valid ``#RRGGBB``
        # value to avoid raising ``ValueError`` during drawing.
        try:
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
        except (ValueError, IndexError):  # pragma: no cover - defensive
            r = g = b = 0
        nr = int(255 * (1 - ratio) + r * ratio)
        ng = int(255 * (1 - ratio) + g * ratio)
        nb = int(255 * (1 - ratio) + b * ratio)
        return f"#{nr:02x}{ng:02x}{nb:02x}"

    def _fill_gradient_polygon(self, canvas, points, color: str) -> None:
        """Fill *points* polygon with a horizontal white → color gradient."""
        xs = [p[0] for p in points]
        left = math.floor(min(xs))
        right = math.ceil(max(xs))
        if right <= left:
            return
        x = left
        while x <= right:
            ratio = (x - left) / (right - left) if right > left else 1
            fill = self._interpolate_color(color, ratio)
            yvals = []
            for i in range(len(points)):
                x1, y1 = points[i]
                x2, y2 = points[(i + 1) % len(points)]
                if (x1 <= x <= x2) or (x2 <= x <= x1):
                    if abs(x1 - x2) < 1e-6:
                        if abs(x1 - x) < 0.25:
                            yvals.extend([y1, y2])
                        continue
                    t = (x - x1) / (x2 - x1)
                    yvals.append(y1 + t * (y2 - y1))
            yvals.sort()
            for j in range(0, len(yvals), 2):
                if j + 1 < len(yvals):
                    canvas.create_line(x, yvals[j], x, yvals[j + 1], fill=fill)
            x += 0.5

    def _fill_gradient_circle(
        self,
        canvas,
        cx: float,
        cy: float,
        radius: float,
        color: str,
        tag: str | None = None,
    ) -> list[int]:
        """Fill circle with gradient from white to *color* and return created line IDs."""
        left = math.floor(cx - radius)
        right = math.ceil(cx + radius)
        if right <= left:
            return []
        ids: list[int] = []
        x = left
        while x <= right:
            ratio = (x - left) / (right - left) if right > left else 1
            fill = self._interpolate_color(color, ratio)
            dx = x - cx
            dy = math.sqrt(max(radius ** 2 - dx ** 2, 0))
            line_id = canvas.create_line(x, cy - dy, x, cy + dy, fill=fill, tags=tag)
            ids.append(line_id)
            x += 0.5
        return ids

    def _fill_gradient_oval(
        self,
        canvas,
        cx: float,
        cy: float,
        rx: float,
        ry: float,
        color: str,
        tag: str | None = None,
    ) -> list[int]:
        """Fill ellipse with gradient from white to *color* and return created line IDs."""
        left = math.floor(cx - rx)
        right = math.ceil(cx + rx)
        if right <= left or rx == 0 or ry == 0:
            return []
        ids: list[int] = []
        x = left
        while x <= right:
            ratio = (x - left) / (right - left) if right > left else 1
            fill = self._interpolate_color(color, ratio)
            dx = x - cx
            dy = ry * math.sqrt(max(1 - (dx / rx) ** 2, 0))
            line_id = canvas.create_line(x, cy - dy, x, cy + dy, fill=fill, tags=tag)
            ids.append(line_id)
            x += 0.5
        return ids

    def _fill_gradient_rect(self, canvas, left: float, top: float, right: float, bottom: float, color: str) -> None:
        """Fill rectangle with gradient from white to *color*."""
        if right <= left:
            return
        x = left
        while x <= right:
            ratio = (x - left) / (right - left) if right > left else 1
            fill = self._interpolate_color(color, ratio)
            canvas.create_line(x, top, x, bottom, fill=fill)
            x += 0.5

    def get_text_size(self, text, font_obj):
        """Return the (width, height) in pixels needed to render the text with the given font."""
        lines = text.split("\n")
        max_width = max(font_obj.measure(line) for line in lines)
        height = font_obj.metrics("linespace") * len(lines)
        return max_width, height

    def draw_page_clone_shape(
        self,
        canvas,
        x,
        y,
        scale=40.0,
        top_text="Desc:\n\nRationale:",
        bottom_text="Node",
        fill="lightgray",
        outline_color=None,
        line_width=1,
        font_obj=None,
        obj_id: str = "",
    ):
        """Draw a page connector for a cloned node using GSN's shared-marker notation."""
        outline_color = self._resolve_outline(outline_color)
        # Draw the base triangle.
        self.draw_triangle_shape(
            canvas,
            x,
            y,
            scale=scale,
            top_text=top_text,
            bottom_text=bottom_text,
            fill=fill,
            outline_color=outline_color,
            line_width=line_width,
            font_obj=font_obj,
            obj_id=obj_id,
        )
        # Add a small shared marker in the upper-right corner to indicate a clone.
        marker_x = x + scale / 2
        marker_y = y - scale * 0.3
        self.draw_shared_marker(canvas, marker_x, marker_y, 1)

    def draw_shared_marker(self, canvas, x, y, zoom):
        """Draw a small shared marker at the given canvas coordinates."""
        size = 10 * zoom
        v1 = (x, y)
        v2 = (x - size, y)
        v3 = (x, y - size)
        canvas.create_polygon(
            [v1, v2, v3],
            fill="black",
            outline=StyleManager.get_instance().outline_color,
        )

    def _segment_intersection(self, p1, p2, p3, p4):
        """Return intersection point (x, y, t) of segments *p1*-*p2* and *p3*-*p4* or None."""
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        x4, y4 = p4
        denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
        if denom == 0:
            return None
        t = ((x3 - x1) * (y4 - y3) - (y3 - y1) * (x4 - x3)) / denom
        u = ((x3 - x1) * (y2 - y1) - (y3 - y1) * (x2 - x1)) / denom
        if 0 <= t <= 1 and 0 <= u <= 1:
            ix = x1 + t * (x2 - x1)
            iy = y1 + t * (y2 - y1)
            return ix, iy, t
        return None

    def point_on_shape(self, shape, target_pt):
        """Return the intersection of the line to *target_pt* with *shape*."""
        typ = shape.get("type")
        if typ == "circle":
            cx, cy = shape.get("center", (0, 0))
            r = shape.get("radius", 0)
            dx = target_pt[0] - cx
            dy = target_pt[1] - cy
            dist = math.hypot(dx, dy) or 1
            return (cx + dx / dist * r, cy + dy / dist * r)
        elif typ == "rect":
            cx, cy = shape.get("center", (0, 0))
            w = shape.get("width", 0) / 2
            h = shape.get("height", 0) / 2
            dx = target_pt[0] - cx
            dy = target_pt[1] - cy
            if abs(dx) > abs(dy):
                if dx > 0:
                    cx += w
                    cy += dy * (w / abs(dx)) if dx != 0 else 0
                else:
                    cx -= w
                    cy += dy * (w / abs(dx)) if dx != 0 else 0
            else:
                if dy > 0:
                    cy += h
                    cx += dx * (h / abs(dy)) if dy != 0 else 0
                else:
                    cy -= h
                    cx += dx * (h / abs(dy)) if dy != 0 else 0
            return cx, cy
        elif typ == "ellipse":
            cx, cy = shape.get("center", (0, 0))
            w = shape.get("width", 0) / 2
            h = shape.get("height", 0) / 2
            dx = target_pt[0] - cx
            dy = target_pt[1] - cy
            if w == 0 or h == 0:
                return cx, cy
            scale = math.hypot(dx / w, dy / h) or 1
            return cx + dx / scale, cy + dy / scale
        elif typ == "polygon":
            cx, cy = shape.get("center", (0, 0))
            points = shape.get("points", [])
            if len(points) < 3:
                return target_pt
            best = None
            for i in range(len(points)):
                p3 = points[i]
                p4 = points[(i + 1) % len(points)]
                inter = self._segment_intersection((cx, cy), target_pt, p3, p4)
                if inter:
                    ix, iy, t = inter
                    if best is None or t < best[2]:
                        best = (ix, iy, t)
            if best:
                return best[0], best[1]
        return target_pt

    def draw_90_connection(self, canvas, parent_pt, child_pt, outline_color=None, line_width=1,
                           fixed_length=40, parent_shape=None, child_shape=None):
        """Draw a 90° connection line from a parent point to a child point.

        If *parent_shape* or *child_shape* dictionaries are provided, the start
        and end points are adjusted so the connector touches the object's surface.
        """
        outline_color = self._resolve_outline(outline_color)
        if parent_shape:
            parent_pt = self.point_on_shape(parent_shape, child_pt)
        if child_shape:
            child_pt = self.point_on_shape(child_shape, parent_pt)

        if parent_pt == child_pt:
            size = fixed_length
            x, y = parent_pt
            canvas.create_line(
                x,
                y,
                x,
                y - size,
                x + size,
                y - size,
                x + size,
                y,
                x,
                y,
                fill=outline_color,
                width=line_width,
            )
            return

        fixed_y = parent_pt[1] + fixed_length
        canvas.create_line(parent_pt[0], parent_pt[1], parent_pt[0], fixed_y,
                           fill=outline_color, width=line_width)
        canvas.create_line(parent_pt[0], fixed_y, child_pt[0], fixed_y,
                           fill=outline_color, width=line_width)
        canvas.create_line(child_pt[0], fixed_y, child_pt[0], child_pt[1],
                           fill=outline_color, width=line_width)

    def compute_rotated_and_gate_vertices(self, scale):
        """Compute vertices for a rotated AND gate shape scaled by 'scale'."""
        vertices = [(0, 0), (0, 2), (1, 2)]
        num_points = 50
        for i in range(num_points + 1):
            theta = math.pi / 2 - math.pi * i / num_points
            vertices.append((1 + math.cos(theta), 1 + math.sin(theta)))
        vertices.append((0, 0))
        def rotate_point(pt):
            x, y = pt
            return (2 - y, x)
        rotated = [rotate_point(pt) for pt in vertices]
        translated = [(vx + 2, vy + 1) for (vx, vy) in rotated]
        scaled = [(vx * scale, vy * scale) for (vx, vy) in translated]
        return scaled

    def draw_rotated_and_gate_shape(
        self,
        canvas,
        x,
        y,
        scale=40.0,
        top_text="Desc:\n\nRationale:",
        bottom_text="Event",
        fill="lightgray",
        outline_color=None,
        line_width=1,
        font_obj=None,
        obj_id: str = "",
    ):
        """Draw a rotated AND gate shape with top and bottom text labels."""
        outline_color = self._resolve_outline(outline_color)
        if font_obj is None:
            font_obj = tkFont.Font(family="Arial", size=10)
        raw_verts = self.compute_rotated_and_gate_vertices(scale)
        flipped = [(vx, -vy) for (vx, vy) in raw_verts]
        xs = [v[0] for v in flipped]
        ys = [v[1] for v in flipped]
        cx, cy = (sum(xs) / len(xs), sum(ys) / len(ys))
        final_points = [(vx - cx + x, vy - cy + y) for (vx, vy) in flipped]
        self._fill_gradient_polygon(canvas, final_points, fill)
        canvas.create_polygon(
            final_points,
            fill="",
            outline=outline_color,
            width=line_width,
            smooth=False,
        )

        # Draw the top label box
        t_width, t_height = self.get_text_size(top_text, font_obj)
        padding = 6
        top_box_width = t_width + 2 * padding
        top_box_height = t_height + 2 * padding
        top_y = min(pt[1] for pt in final_points) - top_box_height - 5
        top_box_x = x - top_box_width / 2
        self._fill_gradient_rect(
            canvas,
            top_box_x,
            top_y,
            top_box_x + top_box_width,
            top_y + top_box_height,
            "#CFD8DC",
        )
        canvas.create_rectangle(
            top_box_x,
            top_y,
            top_box_x + top_box_width,
            top_y + top_box_height,
            fill="",
            outline=outline_color,
            width=line_width,
            tags=(obj_id,),
        )
        canvas.create_text(top_box_x + top_box_width / 2,
                           top_y + top_box_height / 2,
                           text=top_text,
                           font=font_obj,
                           anchor="center",
                           width=top_box_width,
                           tags=(obj_id,))

        # Draw the bottom label box
        b_width, b_height = self.get_text_size(bottom_text, font_obj)
        bottom_box_width = b_width + 2 * padding
        bottom_box_height = b_height + 2 * padding
        shape_lowest_y = max(pt[1] for pt in final_points)
        bottom_y = shape_lowest_y - (2 * bottom_box_height)
        bottom_box_x = x - bottom_box_width / 2
        self._fill_gradient_rect(
            canvas,
            bottom_box_x,
            bottom_y,
            bottom_box_x + bottom_box_width,
            bottom_y + bottom_box_height,
            "#CFD8DC",
        )
        canvas.create_rectangle(
            bottom_box_x,
            bottom_y,
            bottom_box_x + bottom_box_width,
            bottom_y + bottom_box_height,
            fill="",
            outline=outline_color,
            width=line_width,
            tags=(obj_id,),
        )
        canvas.create_text(bottom_box_x + bottom_box_width / 2,
                           bottom_y + bottom_box_height / 2,
                           text=bottom_text,
                           font=font_obj,
                           anchor="center",
                           width=bottom_box_width,
                           tags=(obj_id,))

    def draw_rotated_or_gate_shape(
        self,
        canvas,
        x,
        y,
        scale=40.0,
        top_text="Desc:\n\nRationale:",
        bottom_text="Event",
        fill="lightgray",
        outline_color=None,
        line_width=1,
        font_obj=None,
        obj_id: str = "",
    ):
        """Draw a rotated OR gate shape with text labels."""
        outline_color = self._resolve_outline(outline_color)
        if font_obj is None:
            font_obj = tkFont.Font(family="Arial", size=10)
        def cubic_bezier(P0, P1, P2, P3, t):
            return ((1 - t) ** 3 * P0[0] + 3 * (1 - t) ** 2 * t * P1[0] +
                    3 * (1 - t) * t ** 2 * P2[0] + t ** 3 * P3[0],
                    (1 - t) ** 3 * P0[1] + 3 * (1 - t) ** 2 * t * P1[1] +
                    3 * (1 - t) * t ** 2 * P2[1] + t ** 3 * P3[1])
        num_points = 30
        t_values = [i / num_points for i in range(num_points + 1)]
        seg1 = [cubic_bezier((0, 0), (0.6, 0), (0.6, 2), (0, 2), t) for t in t_values]
        seg2 = [cubic_bezier((0, 2), (1, 2), (2, 1.6), (2, 1), t) for t in t_values]
        seg3 = [cubic_bezier((2, 1), (2, 0.4), (1, 0), (0, 0), t) for t in t_values]
        points = seg1[:-1] + seg2[:-1] + seg3
        rotated = [(2 - p[1], p[0]) for p in points]
        translated = [(pt[0] + 2, pt[1] + 1) for pt in rotated]
        scaled = [(sx * scale, sy * scale) for (sx, sy) in translated]
        flipped = [(vx, -vy) for (vx, vy) in scaled]
        xs = [p[0] for p in flipped]
        ys = [p[1] for p in flipped]
        cx, cy = (sum(xs) / len(xs), sum(ys) / len(ys))
        final_points = [(vx - cx + x, vy - cy + y) for (vx, vy) in flipped]
        self._fill_gradient_polygon(canvas, final_points, fill)
        canvas.create_polygon(
            final_points,
            fill="",
            outline=outline_color,
            width=line_width,
            smooth=True,
        )

        # Draw the top label box
        padding = 6
        t_width, t_height = self.get_text_size(top_text, font_obj)
        top_box_width = t_width + 2 * padding
        top_box_height = t_height + 2 * padding
        top_y = min(pt[1] for pt in final_points) - top_box_height - 5
        top_box_x = x - top_box_width / 2
        self._fill_gradient_rect(
            canvas,
            top_box_x,
            top_y,
            top_box_x + top_box_width,
            top_y + top_box_height,
            "#CFD8DC",
        )
        canvas.create_rectangle(
            top_box_x,
            top_y,
            top_box_x + top_box_width,
            top_y + top_box_height,
            fill="",
            outline=outline_color,
            width=line_width,
            tags=(obj_id,),
        )
        canvas.create_text(top_box_x + top_box_width / 2,
                           top_y + top_box_height / 2,
                           text=top_text, font=font_obj, anchor="center",
                           width=top_box_width,
                           tags=(obj_id,))

        # Draw the bottom label box
        b_width, b_height = self.get_text_size(bottom_text, font_obj)
        bottom_box_width = b_width + 2 * padding
        bottom_box_height = b_height + 2 * padding
        shape_lowest_y = max(pt[1] for pt in final_points)
        bottom_y = shape_lowest_y - (2 * bottom_box_height)
        bottom_box_x = x - bottom_box_width / 2
        self._fill_gradient_rect(
            canvas,
            bottom_box_x,
            bottom_y,
            bottom_box_x + bottom_box_width,
            bottom_y + bottom_box_height,
            "#CFD8DC",
        )
        canvas.create_rectangle(
            bottom_box_x,
            bottom_y,
            bottom_box_x + bottom_box_width,
            bottom_y + bottom_box_height,
            fill="",
            outline=outline_color,
            width=line_width,
            tags=(obj_id,),
        )
        canvas.create_text(bottom_box_x + bottom_box_width / 2,
                           bottom_y + bottom_box_height / 2,
                           text=bottom_text, font=font_obj,
                           anchor="center", width=bottom_box_width,
                           tags=(obj_id,))

    def draw_rotated_and_gate_clone_shape(
        self,
        canvas,
        x,
        y,
        scale=40.0,
        top_text="Desc:\n\nRationale:",
        bottom_text="Node",
        fill="lightgray",
        outline_color=None,
        line_width=1,
        font_obj=None,
        obj_id: str = "",
    ):
        """Draw a rotated AND gate shape and mark it as a clone using GSN notation."""
        outline_color = self._resolve_outline(outline_color)
        self.draw_rotated_and_gate_shape(
            canvas,
            x,
            y,
            scale=scale,
            top_text=top_text,
            bottom_text=bottom_text,
            fill=fill,
            outline_color=outline_color,
            line_width=line_width,
            font_obj=font_obj,
            obj_id=obj_id,
        )
        # Add shared marker at the upper-right corner of the gate.
        marker_x = x + scale / 2
        marker_y = y - scale * 0.3
        self.draw_shared_marker(canvas, marker_x, marker_y, 1)

    def draw_rotated_or_gate_clone_shape(
        self,
        canvas,
        x,
        y,
        scale=40.0,
        top_text="Desc:\n\nRationale:",
        bottom_text="Node",
        fill="lightgray",
        outline_color=None,
        line_width=1,
        font_obj=None,
        obj_id: str = "",
    ):
        """Draw a rotated OR gate shape and mark it as a clone using GSN notation."""
        outline_color = self._resolve_outline(outline_color)
        self.draw_rotated_or_gate_shape(
            canvas,
            x,
            y,
            scale=scale,
            top_text=top_text,
            bottom_text=bottom_text,
            fill=fill,
            outline_color=outline_color,
            line_width=line_width,
            font_obj=font_obj,
            obj_id=obj_id,
        )
        # Add shared marker at the upper-right corner of the gate.
        marker_x = x + scale / 2
        marker_y = y - scale * 0.3
        self.draw_shared_marker(canvas, marker_x, marker_y, 1)

    def draw_triangle_shape(
        self,
        canvas,
        x,
        y,
        scale=40.0,
        top_text="Desc:\n\nRationale:",
        bottom_text="Event",
        fill="lightgray",
        outline_color=None,
        line_width=1,
        font_obj=None,
        obj_id: str = "",
    ):
        outline_color = self._resolve_outline(outline_color)
        if font_obj is None:
            font_obj = tkFont.Font(family="Arial", size=10)
        effective_scale = scale * 2  
        h = effective_scale * math.sqrt(3) / 2
        v1 = (0, -2 * h / 3)
        v2 = (-effective_scale / 2, h / 3)
        v3 = (effective_scale / 2, h / 3)
        vertices = [
            (x + v1[0], y + v1[1]),
            (x + v2[0], y + v2[1]),
            (x + v3[0], y + v3[1]),
        ]
        self._fill_gradient_polygon(canvas, vertices, fill)
        canvas.create_polygon(vertices, fill="", outline=outline_color, width=line_width)
        
        t_width, t_height = self.get_text_size(top_text, font_obj)
        padding = 6
        top_box_width = t_width + 2 * padding
        top_box_height = t_height + 2 * padding
        top_box_x = x - top_box_width / 2
        top_box_y = min(v[1] for v in vertices) - top_box_height
        self._fill_gradient_rect(
            canvas,
            top_box_x,
            top_box_y,
            top_box_x + top_box_width,
            top_box_y + top_box_height,
            "#CFD8DC",
        )
        canvas.create_rectangle(
            top_box_x,
            top_box_y,
            top_box_x + top_box_width,
            top_box_y + top_box_height,
            fill="",
            outline=outline_color,
            width=line_width,
            tags=(obj_id,),
        )
        canvas.create_text(top_box_x + top_box_width / 2,
                           top_box_y + top_box_height / 2,
                           text=top_text,
                           font=font_obj, anchor="center", width=top_box_width,
                           tags=(obj_id,))
        
        b_width, b_height = self.get_text_size(bottom_text, font_obj)
        bottom_box_width = b_width + 2 * padding
        bottom_box_height = b_height + 2 * padding
        bottom_box_x = x - bottom_box_width / 2
        bottom_box_y = max(v[1] for v in vertices) + padding - 2 * bottom_box_height
        self._fill_gradient_rect(
            canvas,
            bottom_box_x,
            bottom_box_y,
            bottom_box_x + bottom_box_width,
            bottom_box_y + bottom_box_height,
            "#CFD8DC",
        )
        canvas.create_rectangle(
            bottom_box_x,
            bottom_box_y,
            bottom_box_x + bottom_box_width,
            bottom_box_y + bottom_box_height,
            fill="",
            outline=outline_color,
            width=line_width,
            tags=(obj_id,),
        )
        canvas.create_text(bottom_box_x + bottom_box_width / 2,
                           bottom_box_y + bottom_box_height / 2,
                           text=bottom_text,
                           font=font_obj, anchor="center", width=bottom_box_width,
                           tags=(obj_id,))
                           
    def draw_circle_event_shape(
        self,
        canvas,
        x,
        y,
        radius,
        top_text="",
        bottom_text="",
        fill="lightyellow",
        outline_color=None,
        line_width=1,
        font_obj=None,
        base_event=False,
        obj_id: str = "",
    ):
        """Draw a circular event shape with optional text labels."""
        outline_color = self._resolve_outline(outline_color)
        if font_obj is None:
            font_obj = self._scaled_font(radius * 2)
        left = x - radius
        top = y - radius
        right = x + radius
        bottom = y + radius
        self._fill_gradient_circle(canvas, x, y, radius, fill)
        canvas.create_oval(
            left,
            top,
            right,
            bottom,
            fill="",
            outline=outline_color,
            width=line_width,
            tags=(obj_id,),
        )
        t_width, t_height = self.get_text_size(top_text, font_obj)
        padding = 6
        top_box_width = t_width + 2 * padding
        top_box_height = t_height + 2 * padding
        top_box_x = x - top_box_width / 2
        top_box_y = top - top_box_height
        self._fill_gradient_rect(
            canvas,
            top_box_x,
            top_box_y,
            top_box_x + top_box_width,
            top_box_y + top_box_height,
            "#CFD8DC",
        )
        canvas.create_rectangle(
            top_box_x,
            top_box_y,
            top_box_x + top_box_width,
            top_box_y + top_box_height,
            fill="",
            outline=outline_color,
            width=line_width,
            tags=(obj_id,),
        )
        canvas.create_text(top_box_x + top_box_width / 2,
                           top_box_y + top_box_height / 2,
                           text=top_text,
                           font=font_obj, anchor="center",
                           width=top_box_width,
                           tags=(obj_id,))
        b_width, b_height = self.get_text_size(bottom_text, font_obj)
        bottom_box_width = b_width + 2 * padding
        bottom_box_height = b_height + 2 * padding
        bottom_box_x = x - bottom_box_width / 2
        bottom_box_y = bottom - 2 * bottom_box_height
        self._fill_gradient_rect(
            canvas,
            bottom_box_x,
            bottom_box_y,
            bottom_box_x + bottom_box_width,
            bottom_box_y + bottom_box_height,
            "#CFD8DC",
        )
        canvas.create_rectangle(
            bottom_box_x,
            bottom_box_y,
            bottom_box_x + bottom_box_width,
            bottom_box_y + bottom_box_height,
            fill="",
            outline=outline_color,
            width=line_width,
            tags=(obj_id,),
        )
        canvas.create_text(bottom_box_x + bottom_box_width / 2,
                           bottom_box_y + bottom_box_height / 2,
                           text=bottom_text,
                           font=font_obj, anchor="center",
                           width=bottom_box_width,
                           tags=(obj_id,))
                           
    def draw_triangle_clone_shape(
        self,
        canvas,
        x,
        y,
        scale=40.0,
        top_text="Desc:\n\nRationale:",
        bottom_text="Node",
        fill="lightgray",
        outline_color=None,
        line_width=1,
        font_obj=None,
        obj_id: str = "",
    ):
        """Draw a triangle-shaped event and mark it as a clone using GSN notation."""
        outline_color = self._resolve_outline(outline_color)
        if font_obj is None:
            font_obj = tkFont.Font(family="Arial", size=10)
        # Draw the base triangle as usual.
        self.draw_triangle_shape(
            canvas,
            x,
            y,
            scale=scale,
            top_text=top_text,
            bottom_text=bottom_text,
            fill=fill,
            outline_color=outline_color,
            line_width=line_width,
            font_obj=font_obj,
            obj_id=obj_id,
        )
        # Add a shared marker to indicate the node is a clone.
        marker_x = x + scale / 2
        marker_y = y - scale * 0.3
        self.draw_shared_marker(canvas, marker_x, marker_y, 1)
                           
# Create a single FTADrawingHelper object that can be used by other classes
fta_drawing_helper = FTADrawingHelper()

class GSNDrawingHelper(FTADrawingHelper):
    """Drawing helper providing shapes for GSN argumentation diagrams."""

    def _scaled_font(self, scale: float) -> tkFont.Font:
        """Return a font scaled proportionally to *scale*."""
        size = max(1, int(scale / 4))
        return tkFont.Font(family="Arial", size=size)

    def draw_goal_shape(
        self,
        canvas,
        x,
        y,
        scale=60.0,
        text="Goal",
        fill="lightyellow",
        outline_color=None,
        line_width=1,
        font_obj=None,
        obj_id: str = "",
    ):
        outline_color = self._resolve_outline(outline_color)
        if font_obj is None:
            font_obj = self._scaled_font(scale)
        padding = 4
        t_width, t_height = self.get_text_size(text, font_obj)
        w = max(scale, t_width + 2 * padding)
        h = max(scale * 0.6, t_height + 2 * padding)
        left = x - w / 2
        top = y - h / 2
        right = x + w / 2
        bottom = y + h / 2
        self._fill_gradient_rect(canvas, left, top, right, bottom, fill)
        canvas.create_rectangle(
            left,
            top,
            right,
            bottom,
            fill="",
            outline=outline_color,
            width=line_width,
            tags=(obj_id,),
        )
        canvas.create_text(
            x,
            y,
            text=text,
            font=font_obj,
            anchor="center",
            width=w - 2 * padding,
            tags=(obj_id,),
        )

    def draw_module_shape(
        self,
        canvas,
        x,
        y,
        scale=60.0,
        text="Module",
        fill="lightyellow",
        outline_color=None,
        line_width=1,
        font_obj=None,
        obj_id: str = "",
    ):
        outline_color = self._resolve_outline(outline_color)
        if font_obj is None:
            font_obj = self._scaled_font(scale)
        padding = 4
        t_width, t_height = self.get_text_size(text, font_obj)
        w = max(scale, t_width + 2 * padding)
        base_h = max(scale * 0.6, t_height + 2 * padding)
        tab_h = base_h * 0.25
        left = x - w / 2
        base_top = y - base_h / 2
        right = x + w / 2
        bottom = y + base_h / 2
        tab_top = base_top - tab_h
        tab_w = w * 0.4
        self._fill_gradient_rect(canvas, left, base_top, right, bottom, fill)
        self._fill_gradient_rect(canvas, left, tab_top, left + tab_w, base_top, fill)
        canvas.create_polygon(
            left,
            base_top,
            left,
            bottom,
            right,
            bottom,
            right,
            tab_top,
            left + tab_w,
            tab_top,
            left + tab_w,
            base_top,
            left,
            base_top,
            fill="",
            outline=outline_color,
            width=line_width,
            tags=(obj_id,),
        )
        canvas.create_text(
            x,
            (base_top + bottom) / 2,
            text=text,
            font=font_obj,
            anchor="center",
            width=w - 2 * padding,
            tags=(obj_id,),
        )

    def _draw_arrow(
        self,
        canvas,
        start_pt,
        end_pt,
        *,
        fill="black",
        outline=None,
        obj_id: str = "",
    ) -> None:
        """Draw a triangular arrow head from *start_pt* to *end_pt*."""
        x1, y1 = start_pt
        x2, y2 = end_pt
        dx = x2 - x1
        dy = y2 - y1
        length = math.hypot(dx, dy)
        if length == 0:
            return
        if outline is None:
            outline = StyleManager.get_instance().outline_color
        ux, uy = dx / length, dy / length
        arrow_length = 10
        arrow_width = 6
        base_x = x2 - arrow_length * ux
        base_y = y2 - arrow_length * uy
        perp_x = -uy
        perp_y = ux
        points = [
            (x2, y2),
            (
                base_x + (arrow_width / 2) * perp_x,
                base_y + (arrow_width / 2) * perp_y,
            ),
            (
                base_x - (arrow_width / 2) * perp_x,
                base_y - (arrow_width / 2) * perp_y,
            ),
        ]
        canvas.create_polygon(
            points,
            fill=fill,
            outline=outline,
            tags=(obj_id, f"{obj_id}-arrow") if obj_id else None,
        )

    def draw_solved_by_connection(
        self,
        canvas,
        parent_pt,
        child_pt,
        outline_color=None,
        line_width=1,
        obj_id: str = "",
    ):
        """Draw a curved connector indicating a 'solved by' relationship."""
        outline_color = self._resolve_outline(outline_color)
        px, py = parent_pt
        cx, cy = child_pt
        if parent_pt == child_pt:
            size = 20
            path = [
                px,
                py,
                px,
                py - size,
                px + size,
                py - size,
                px + size,
                py,
                px,
                py,
            ]
            canvas.create_line(
                *path, fill=outline_color, width=line_width, tags=(obj_id,)
            )
        else:
            dx = cx - px
            dy = cy - py
            if abs(dx) > abs(dy):
                offset = dx / 2
                path = [
                    px,
                    py,
                    px + offset,
                    py,
                    cx - offset,
                    cy,
                    cx,
                    cy,
                ]
            else:
                offset = dy / 2
                path = [
                    px,
                    py,
                    px,
                    py + offset,
                    cx,
                    cy - offset,
                    cx,
                    cy,
                ]
            canvas.create_line(
                *path,
                smooth=True,
                fill=outline_color,
                width=line_width,
                tags=(obj_id,),
            )
        start = (path[-4], path[-3])
        end = (path[-2], path[-1])
        if start == end:
            start = parent_pt
        self._draw_arrow(
            canvas,
            start,
            end,
            fill=outline_color,
            outline=outline_color,
            obj_id=obj_id,
        )

    def draw_in_context_connection(
        self,
        canvas,
        parent_pt,
        child_pt,
        outline_color=None,
        line_width=1,
        obj_id: str = "",
    ):
        """Draw a dashed curved connector for an 'in context of' relationship."""
        outline_color = self._resolve_outline(outline_color)
        px, py = parent_pt
        cx, cy = child_pt
        dash = (4, 2)
        if parent_pt == child_pt:
            size = 20
            path = [
                px,
                py,
                px,
                py - size,
                px + size,
                py - size,
                px + size,
                py,
                px,
                py,
            ]
            canvas.create_line(
                *path,
                fill=outline_color,
                width=line_width,
                dash=dash,
                tags=(obj_id,),
            )
        else:
            dx = cx - px
            dy = cy - py
            if abs(dx) > abs(dy):
                offset = dx / 2
                path = [
                    px,
                    py,
                    px + offset,
                    py,
                    cx - offset,
                    cy,
                    cx,
                    cy,
                ]
            else:
                offset = dy / 2
                path = [
                    px,
                    py,
                    px,
                    py + offset,
                    cx,
                    cy - offset,
                    cx,
                    cy,
                ]
            canvas.create_line(
                *path,
                smooth=True,
                fill=outline_color,
                width=line_width,
                dash=dash,
                tags=(obj_id,),
            )
        start = (path[-4], path[-3])
        end = (path[-2], path[-1])
        if start == end:
            start = parent_pt
        self._draw_arrow(
            canvas,
            start,
            end,
            fill="white",
            outline=outline_color,
            obj_id=obj_id,
        )

    def draw_strategy_shape(
        self,
        canvas,
        x,
        y,
        scale=60.0,
        text="Strategy",
        fill="lightyellow",
        outline_color=None,
        line_width=1,
        font_obj=None,
        obj_id: str = "",
    ):
        outline_color = self._resolve_outline(outline_color)
        if font_obj is None:
            font_obj = self._scaled_font(scale)
        padding = 4
        t_width, t_height = self.get_text_size(text, font_obj)
        w = max(scale, t_width + 2 * padding)
        h = max(scale * 0.5, t_height + 2 * padding)
        offset = w * 0.2
        points = [
            (x - w / 2 + offset, y - h / 2),
            (x + w / 2, y - h / 2),
            (x + w / 2 - offset, y + h / 2),
            (x - w / 2, y + h / 2),
        ]
        self._fill_gradient_polygon(canvas, points, fill)
        canvas.create_polygon(points, outline=outline_color, width=line_width, fill="", tags=(obj_id,))
        canvas.create_text(
            x,
            y,
            text=text,
            font=font_obj,
            anchor="center",
            width=w - 2 * padding,
            tags=(obj_id,),
        )

    def draw_solution_shape(
        self,
        canvas,
        x,
        y,
        scale=40.0,
        text="Solution",
        fill="lightyellow",
        outline_color=None,
        line_width=1,
        font_obj=None,
        obj_id: str = "",
    ):
        outline_color = self._resolve_outline(outline_color)
        radius = scale / 2
        if font_obj is None:
            font_obj = self._scaled_font(scale)
        left = x - radius
        top = y - radius
        right = x + radius
        bottom = y + radius
        self._fill_gradient_circle(canvas, x, y, radius, fill)
        canvas.create_oval(
            left,
            top,
            right,
            bottom,
            fill="",
            outline=outline_color,
            width=line_width,
            tags=(obj_id,),
        )
        canvas.create_text(
            x,
            y,
            text=text,
            font=font_obj,
            anchor="center",
            width=scale - 8,
            tags=(obj_id,),
        )

    def draw_assumption_shape(
        self,
        canvas,
        x,
        y,
        scale=60.0,
        text="Assumption",
        fill="lightyellow",
        outline_color=None,
        line_width=1,
        font_obj=None,
        obj_id: str = "",
    ):
        outline_color = self._resolve_outline(outline_color)
        if font_obj is None:
            font_obj = self._scaled_font(scale)
        padding = 4
        t_width, t_height = self.get_text_size(text, font_obj)
        w = max(scale, t_width + 2 * padding)
        h = max(scale * 0.5, t_height + 2 * padding)
        left = x - w / 2
        top = y - h / 2
        right = x + w / 2
        bottom = y + h / 2
        canvas.create_oval(
            left,
            top,
            right,
            bottom,
            fill=fill,
            outline=outline_color,
            width=line_width,
            tags=(obj_id,),
        )
        canvas.create_text(
            x,
            y,
            text=text,
            font=font_obj,
            anchor="center",
            width=w - 2 * padding,
            tags=(obj_id,),
        )
        label_font = tkFont.Font(font=font_obj)
        label_font.configure(weight="bold")
        offset = padding
        canvas.create_text(
            right + offset,
            bottom - offset,
            text="A",
            font=label_font,
            anchor="sw",
            tags=(obj_id,),
        )

    def draw_justification_shape(
        self,
        canvas,
        x,
        y,
        scale=60.0,
        text="Justification",
        fill="lightyellow",
        outline_color=None,
        line_width=1,
        font_obj=None,
        obj_id: str = "",
    ):
        outline_color = self._resolve_outline(outline_color)
        if font_obj is None:
            font_obj = self._scaled_font(scale)
        padding = 4
        t_width, t_height = self.get_text_size(text, font_obj)
        w = max(scale, t_width + 2 * padding)
        h = max(scale * 0.5, t_height + 2 * padding)
        left = x - w / 2
        top = y - h / 2
        right = x + w / 2
        bottom = y + h / 2
        canvas.create_oval(
            left,
            top,
            right,
            bottom,
            fill=fill,
            outline=outline_color,
            width=line_width,
            tags=(obj_id,),
        )
        canvas.create_text(
            x,
            y,
            text=text,
            font=font_obj,
            anchor="center",
            width=w - 2 * padding,
            tags=(obj_id,),
        )
        label_font = tkFont.Font(font=font_obj)
        label_font.configure(weight="bold")
        offset = padding
        canvas.create_text(
            right + offset,
            bottom - offset,
            text="J",
            font=label_font,
            anchor="sw",
            tags=(obj_id,),
        )

    def draw_context_shape(
        self,
        canvas,
        x,
        y,
        scale=60.0,
        text="Context",
        fill="lightyellow",
        outline_color=None,
        line_width=1,
        font_obj=None,
        obj_id: str = "",
    ):
        outline_color = self._resolve_outline(outline_color)
        if font_obj is None:
            font_obj = self._scaled_font(scale)
        padding = 4
        t_width, t_height = self.get_text_size(text, font_obj)
        w = max(scale, t_width + 2 * padding)
        h = max(scale * 0.5, t_height + 2 * padding)
        left = x - w / 2
        top = y - h / 2
        right = x + w / 2
        bottom = y + h / 2
        radius = h / 2
        canvas.create_rectangle(
            left + radius,
            top,
            right - radius,
            bottom,
            fill=fill,
            outline="",
            width=0,
            tags=(obj_id,),
        )
        canvas.create_oval(
            left,
            top,
            left + h,
            bottom,
            fill=fill,
            outline="",
            width=0,
            tags=(obj_id,),
        )
        canvas.create_oval(
            right - h,
            top,
            right,
            bottom,
            fill=fill,
            outline="",
            width=0,
            tags=(obj_id,),
        )
        canvas.create_line(
            left + radius,
            top,
            right - radius,
            top,
            fill=outline_color,
            width=line_width,
        )
        canvas.create_line(
            left + radius,
            bottom,
            right - radius,
            bottom,
            fill=outline_color,
            width=line_width,
        )
        canvas.create_arc(
            left,
            top,
            left + h,
            bottom,
            start=90,
            extent=180,
            style=tk.ARC,
            outline=outline_color,
            width=line_width,
        )
        canvas.create_arc(
            right - h,
            top,
            right,
            bottom,
            start=270,
            extent=180,
            style=tk.ARC,
            outline=outline_color,
            width=line_width,
        )
        canvas.create_text(
            x,
            y,
            text=text,
            font=font_obj,
            anchor="center",
            width=w - 2 * padding,
            tags=(obj_id,),
        )

    def _draw_module_reference_box(
        self,
        canvas,
        x,
        top,
        w,
        module_text,
        outline_color,
        line_width,
        font_obj,
        obj_id,
    ):
        """Draw the module identifier box used by away elements."""
        padding = 2
        m_width, m_height = self.get_text_size(module_text, font_obj)
        box_w = max(w * 0.6, m_width + 2 * padding)
        box_h = m_height + 2 * padding
        left = x - box_w / 2
        right = x + box_w / 2
        bottom = top + box_h
        canvas.create_rectangle(
            left,
            top,
            right,
            bottom,
            fill="white",
            outline=outline_color,
            width=line_width,
            tags=(obj_id,),
        )
        canvas.create_text(
            x,
            (top + bottom) / 2,
            text=module_text,
            font=font_obj,
            anchor="center",
            width=box_w - 2 * padding,
            tags=(obj_id,),
        )
        return bottom

    def draw_away_goal_shape(
        self,
        canvas,
        x,
        y,
        scale=60.0,
        text="Goal",
        module_text="",
        fill="lightyellow",
        outline_color=None,
        line_width=1,
        font_obj=None,
        obj_id: str = "",
    ):
        """Draw an away goal shape with module reference."""
        outline_color = self._resolve_outline(outline_color)
        if font_obj is None:
            font_obj = self._scaled_font(scale)
        padding = 4
        t_width, t_height = self.get_text_size(text, font_obj)
        w = max(scale, t_width + 2 * padding)
        h = max(scale * 0.6, t_height + 2 * padding)
        left = x - w / 2
        top = y - h / 2
        right = x + w / 2
        bottom = y + h / 2
        canvas.create_rectangle(
            left,
            top,
            right,
            bottom,
            fill=fill,
            outline=outline_color,
            width=line_width,
            tags=(obj_id,),
        )
        line_y = top + h * 0.6
        canvas.create_line(left, line_y, right, line_y, fill=outline_color, width=line_width)
        module_scale = (bottom - line_y) * 0.5
        self.draw_module_shape(
            canvas,
            x,
            line_y + (bottom - line_y) / 2,
            scale=module_scale,
            text="",
            fill="lightgray",
            outline_color=outline_color,
            line_width=line_width,
            font_obj=self._scaled_font(module_scale),
            obj_id=obj_id,
        )
        canvas.create_text(
            x,
            top + (line_y - top) / 2,
            text=text,
            font=font_obj,
            anchor="center",
            width=w - 2 * padding,
            tags=(obj_id,),
        )
        box_font = self._scaled_font(scale * 0.4)
        self._draw_module_reference_box(
            canvas,
            x,
            bottom,
            w,
            module_text,
            outline_color,
            line_width,
            box_font,
            obj_id,
        )

    def draw_away_solution_shape(
        self,
        canvas,
        x,
        y,
        scale=60.0,
        text="Solution",
        module_text="",
        fill="lightyellow",
        outline_color=None,
        line_width=1,
        font_obj=None,
        obj_id: str = "",
    ):
        """Draw an away solution as a rectangle with a semi-circle on top."""
        outline_color = self._resolve_outline(outline_color)
        if font_obj is None:
            font_obj = self._scaled_font(scale)
        padding = 4
        t_width, t_height = self.get_text_size(text, font_obj)
        w = max(scale, t_width + 2 * padding)
        h = max(scale * 0.6, t_height + 2 * padding)
        radius = w / 2
        left = x - w / 2
        rect_top = y - h / 2
        right = x + w / 2
        rect_bottom = y + h / 2
        top = rect_top - radius
        canvas.create_rectangle(
            left,
            rect_top,
            right,
            rect_bottom,
            fill=fill,
            outline=outline_color,
            width=line_width,
            tags=(obj_id,),
        )
        canvas.create_arc(
            left,
            top,
            right,
            top + 2 * radius,
            start=0,
            extent=180,
            fill=fill,
            outline=outline_color,
            width=line_width,
            tags=(obj_id,),
        )
        canvas.create_text(
            x,
            rect_top + (rect_bottom - rect_top) / 2,
            text=text,
            font=font_obj,
            anchor="center",
            width=w - 2 * padding,
            tags=(obj_id,),
        )
        box_font = self._scaled_font(scale * 0.4)
        self._draw_module_reference_box(
            canvas,
            x,
            rect_bottom,
            w,
            module_text,
            outline_color,
            line_width,
            box_font,
            obj_id,
        )

    def draw_away_context_shape(
        self,
        canvas,
        x,
        y,
        scale=60.0,
        text="Context",
        module_text="",
        fill="lightyellow",
        outline_color=None,
        line_width=1,
        font_obj=None,
        obj_id: str = "",
    ):
        """Draw an away context: rectangle with rounded bottom."""
        outline_color = self._resolve_outline(outline_color)
        if font_obj is None:
            font_obj = self._scaled_font(scale)
        padding = 4
        t_width, t_height = self.get_text_size(text, font_obj)
        w = max(scale, t_width + 2 * padding)
        h = max(scale * 0.6, t_height + 2 * padding)
        radius = w / 2
        left = x - w / 2
        right = x + w / 2
        rect_top = y - h / 2
        rect_bottom = y + h / 2 - radius
        canvas.create_rectangle(
            left,
            rect_top,
            right,
            rect_bottom,
            fill=fill,
            outline=outline_color,
            width=line_width,
            tags=(obj_id,),
        )
        canvas.create_arc(
            left,
            rect_bottom,
            right,
            rect_bottom + 2 * radius,
            start=180,
            extent=180,
            fill=fill,
            outline=outline_color,
            width=line_width,
            tags=(obj_id,),
        )
        canvas.create_text(
            x,
            rect_top + (rect_bottom - rect_top) / 2,
            text=text,
            font=font_obj,
            anchor="center",
            width=w - 2 * padding,
            tags=(obj_id,),
        )
        box_font = self._scaled_font(scale * 0.4)
        self._draw_module_reference_box(
            canvas,
            x,
            rect_bottom + 2 * radius,
            w,
            module_text,
            outline_color,
            line_width,
            box_font,
            obj_id,
        )

    def _draw_away_assumption_or_justification(
        self,
        canvas,
        x,
        y,
        scale,
        text,
        label,
        module_text,
        fill,
        outline_color,
        line_width,
        font_obj,
        obj_id,
    ):
        outline_color = self._resolve_outline(outline_color)
        if font_obj is None:
            font_obj = self._scaled_font(scale)
        padding = 4
        t_width, t_height = self.get_text_size(text, font_obj)
        w = max(scale, t_width + 2 * padding)
        h = max(scale * 0.6, t_height + 2 * padding)
        radius = w / 2
        left = x - w / 2
        right = x + w / 2
        rect_bottom = y + h / 2
        rect_top = y - h / 2 + radius
        canvas.create_rectangle(
            left,
            rect_top,
            right,
            rect_bottom,
            fill=fill,
            outline=outline_color,
            width=line_width,
            tags=(obj_id,),
        )
        canvas.create_arc(
            left,
            rect_top - 2 * radius,
            right,
            rect_top,
            start=0,
            extent=180,
            fill=fill,
            outline=outline_color,
            width=line_width,
            tags=(obj_id,),
        )
        canvas.create_text(
            x,
            rect_top + (rect_bottom - rect_top) / 2,
            text=text,
            font=font_obj,
            anchor="center",
            width=w - 2 * padding,
            tags=(obj_id,),
        )
        label_font = tkFont.Font(font=font_obj)
        label_font.configure(weight="bold")
        offset = padding
        canvas.create_text(
            right - offset,
            rect_top - radius + offset,
            text=label,
            font=label_font,
            anchor="ne",
            tags=(obj_id,),
        )
        box_font = self._scaled_font(scale * 0.4)
        self._draw_module_reference_box(
            canvas,
            x,
            rect_bottom,
            w,
            module_text,
            outline_color,
            line_width,
            box_font,
            obj_id,
        )

    def draw_away_assumption_shape(
        self,
        canvas,
        x,
        y,
        scale=60.0,
        text="Assumption",
        module_text="",
        fill="lightyellow",
        outline_color=None,
        line_width=1,
        font_obj=None,
        obj_id: str = "",
    ):
        """Draw an away assumption shape."""
        self._draw_away_assumption_or_justification(
            canvas,
            x,
            y,
            scale,
            text,
            "A",
            module_text,
            fill,
            outline_color,
            line_width,
            font_obj,
            obj_id,
        )

    def draw_away_justification_shape(
        self,
        canvas,
        x,
        y,
        scale=60.0,
        text="Justification",
        module_text="",
        fill="lightyellow",
        outline_color=None,
        line_width=1,
        font_obj=None,
        obj_id: str = "",
    ):
        """Draw an away justification shape."""
        self._draw_away_assumption_or_justification(
            canvas,
            x,
            y,
            scale,
            text,
            "J",
            module_text,
            fill,
            outline_color,
            line_width,
            font_obj,
            obj_id,
        )

    def draw_away_module_shape(
        self,
        canvas,
        x,
        y,
        scale=60.0,
        **kwargs,
    ):
        self.draw_module_shape(canvas, x, y, scale=scale, **kwargs)


# Create a single GSNDrawingHelper object for convenience

gsn_drawing_helper = GSNDrawingHelper()
