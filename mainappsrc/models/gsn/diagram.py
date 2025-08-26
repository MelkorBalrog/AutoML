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

"""Simple rendering support for GSN diagrams."""

from dataclasses import dataclass, field
from typing import Iterable, List
import uuid
import math

import tkinter.font as tkFont

from .nodes import GSNNode
from gui.drawing_helper import GSNDrawingHelper


@dataclass
class GSNDiagram:
    """A very small helper to render a GSN argumentation diagram.

    This class is intentionally lightweight; it mirrors a subset of the
    fault tree diagram functionality so that GSN diagrams can reuse the
    existing drawing infrastructure.
    """

    root: GSNNode
    drawing_helper: GSNDrawingHelper = field(default_factory=GSNDrawingHelper)
    diag_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    nodes: List[GSNNode] = field(default_factory=list)

    def __post_init__(self) -> None:  # pragma: no cover - simple bookkeeping
        if self.root not in self.nodes:
            self.nodes.append(self.root)

    # ------------------------------------------------------------------
    def ensure_unique_name(self, name: str, self_node: GSNNode | None = None) -> str:
        """Return a unique node name based on ``name`` within the diagram."""
        if not name:
            return name
        existing = {n.user_name for n in self.nodes if n is not self_node and n.user_name}
        base = name
        suffix = 1
        while name in existing:
            name = f"{base}_{suffix}"
            suffix += 1
        return name

    def add_node(self, node: GSNNode) -> None:
        """Register *node* with the diagram without connecting it."""
        if all(existing is not node for existing in self.nodes):
            if getattr(node, "is_primary_instance", True):
                node.user_name = self.ensure_unique_name(node.user_name, node)
            self.nodes.append(node)

    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        """Return a JSON-serialisable representation of this diagram."""
        return {
            "diag_id": self.diag_id,
            "root": self.root.unique_id,
            "nodes": [n.to_dict() for n in self.nodes],
        }

    # ------------------------------------------------------------------
    @classmethod
    def from_dict(cls, data: dict) -> "GSNDiagram":
        """Reconstruct a :class:`GSNDiagram` from *data*."""
        node_map: dict[str, GSNNode] = {}
        for nd in data.get("nodes", []):
            GSNNode.from_dict(nd, nodes=node_map)
        GSNNode.resolve_references(node_map)
        root_id = data.get("root")
        root = node_map.get(root_id)
        diag = cls(root, diag_id=data.get("diag_id", str(uuid.uuid4())))
        diag.nodes = list(node_map.values())
        return diag

    # ------------------------------------------------------------------
    def _traverse(self) -> Iterable[GSNNode]:
        # ``nodes`` already contains all diagram nodes, including ones that
        # are not connected yet.  Simply iterate over the list to avoid
        # skipping orphan elements and to maintain a stable drawing order.
        return list(self.nodes)

    # ------------------------------------------------------------------
    def draw(self, canvas, zoom: float = 1.0) -> None:  # pragma: no cover - requires tkinter
        """Render the diagram on a :class:`tkinter.Canvas` instance."""
        # draw nodes first and record their bounding shapes
        shapes: dict[str, dict] = {}
        for node in self._traverse():
            self._draw_node(canvas, node, zoom)
            # ``canvas`` objects used in unit tests sometimes provide only a
            # subset of the real :class:`tkinter.Canvas` API.  Accessing a
            # missing ``bbox`` method would therefore raise an ``AttributeError``
            # and break the drawing routine.  Use ``getattr`` so that stub
            # canvases without ``bbox`` simply skip shape calculations.
            bbox = getattr(canvas, "bbox", lambda *a, **k: None)(node.unique_id)
            if not bbox:
                continue
            left, top, right, bottom = bbox
            cx, cy = (left + right) / 2, (top + bottom) / 2
            w, h = right - left, bottom - top
            typ = node.node_type.lower()
            if typ == "solution":
                shapes[node.unique_id] = {
                    "type": "circle",
                    "center": (cx, cy),
                    "radius": w / 2,
                }
            elif typ in {"assumption", "justification", "context"}:
                shapes[node.unique_id] = {
                    "type": "ellipse",
                    "center": (cx, cy),
                    "width": w,
                    "height": h,
                }
            elif typ == "strategy":
                offset = w * 0.2
                points = [
                    (cx - w / 2 + offset, cy - h / 2),
                    (cx + w / 2, cy - h / 2),
                    (cx + w / 2 - offset, cy + h / 2),
                    (cx - w / 2, cy + h / 2),
                ]
                shapes[node.unique_id] = {
                    "type": "polygon",
                    "center": (cx, cy),
                    "points": points,
                }
            else:
                shapes[node.unique_id] = {
                    "type": "rect",
                    "center": (cx, cy),
                    "width": w,
                    "height": h,
                }

        # draw connectors; place lines behind nodes but arrowheads on top
        for parent in self._traverse():
            for child in parent.children:
                # Use a stable tag for connections so tests can locate the
                # created canvas items.  The ``parent->child`` syntax mirrors
                # other diagram components and keeps tags human readable.
                rel_id = f"{parent.unique_id}->{child.unique_id}"
                p_pt = (parent.x * zoom, parent.y * zoom)
                c_pt = (child.x * zoom, child.y * zoom)
                p_shape = shapes.get(parent.unique_id)
                c_shape = shapes.get(child.unique_id)
                if p_shape and c_shape:
                    # Use the actual geometric centres of both shapes to
                    # determine the connector's endpoints.  Relying on the
                    # stored node coordinates can leave a visible gap when the
                    # drawn shape is offset (e.g. due to additional markers or
                    # varying text dimensions).  By intersecting the line
                    # between the shapes' centres with their outlines we ensure
                    # that relationships always touch the surface regardless of
                    # the node type.
                    p_pt = self.drawing_helper.point_on_shape(
                        p_shape, c_shape["center"]
                    )
                    c_pt = self.drawing_helper.point_on_shape(
                        c_shape, p_shape["center"]
                    )
                else:
                    if p_shape:
                        p_pt = self.drawing_helper.point_on_shape(p_shape, c_pt)
                    if c_shape:
                        c_pt = self.drawing_helper.point_on_shape(c_shape, p_pt)
                if child in parent.context_children:
                    self.drawing_helper.draw_in_context_connection(
                        canvas, p_pt, c_pt, obj_id=rel_id
                    )
                else:
                    self.drawing_helper.draw_solved_by_connection(
                        canvas, p_pt, c_pt, obj_id=rel_id
                    )
                lower = getattr(canvas, "tag_lower", None)
                if lower:
                    lower(rel_id)
                raise_ = getattr(canvas, "tag_raise", None)
                if raise_:
                    raise_(f"{rel_id}-arrow")

    # ------------------------------------------------------------------
    def _parse_spi_target(self, target: str) -> tuple[str, str]:
        """Split ``target`` into product goal name and SPI type."""
        if target.endswith(")") and "(" in target:
            name, typ = target.rsplit(" (", 1)
            return name, typ[:-1]
        return target, ""

    # ------------------------------------------------------------------
    def _lookup_spi_probability(self, target: str) -> float | None:
        """Return probability for SPI target ``target`` if available."""
        app = getattr(self, "app", None)
        if not app:
            return None
        name, spi_type = self._parse_spi_target(target)
        for te in getattr(app, "top_events", []):
            te_name = getattr(te, "user_name", "") or f"SG {getattr(te, 'unique_id', '')}"
            if te_name == name:
                attr = "probability" if spi_type == "FUSA" else "spi_probability"
                return getattr(te, attr, None)
        return None

    # ------------------------------------------------------------------
    def _lookup_validation_target(self, target: str) -> str | None:
        """Return validation target for product goal ``target`` if available."""
        app = getattr(self, "app", None)
        if not app:
            return None
        name, spi_type = self._parse_spi_target(target)
        for te in getattr(app, "top_events", []):
            te_name = getattr(te, "user_name", "") or f"SG {getattr(te, 'unique_id', '')}"
            if te_name == name:
                if spi_type == "FUSA":
                    if __package__ and __package__.startswith("AutoML"):
                        from AutoML.config.automl_constants import PMHF_TARGETS  # avoid circular import at module load
                    else:  # pragma: no cover - script context
                        from config.automl_constants import PMHF_TARGETS  # avoid circular import at module load
                    asil = getattr(te, "safety_goal_asil", "")
                    return PMHF_TARGETS.get(asil, None)
                return getattr(te, "validation_target", None)
        return None

    # ------------------------------------------------------------------
    def _find_module_name_strategy1(self, node: GSNNode) -> str:
        for parent in getattr(getattr(node, "original", node), "parents", []):
            if getattr(parent, "node_type", "") == "Module":
                return getattr(parent, "user_name", "")
        return ""

    def _find_module_name_strategy2(self, node: GSNNode) -> str:
        for parent in getattr(node, "parents", []):
            if getattr(parent, "node_type", "") == "Module":
                return getattr(parent, "user_name", "")
        return ""

    def _find_module_name_strategy3(self, node: GSNNode) -> str:
        parents = []
        if getattr(node, "original", None):
            parents.extend(getattr(node.original, "parents", []))
        parents.extend(getattr(node, "parents", []))
        for parent in parents:
            if getattr(parent, "node_type", "") == "Module":
                return getattr(parent, "user_name", "")
        return ""

    def _find_module_name_strategy4(self, node: GSNNode) -> str:
        try:
            return next(
                p.user_name
                for p in getattr(getattr(node, "original", node), "parents", [])
                if getattr(p, "node_type", "") == "Module"
            )
        except StopIteration:
            return ""

    def _find_module_name(self, node: GSNNode) -> str:
        for strat in (
            self._find_module_name_strategy1,
            self._find_module_name_strategy2,
            self._find_module_name_strategy3,
            self._find_module_name_strategy4,
        ):
            try:
                name = strat(node)
                if name:
                    return name
            except Exception:
                continue
        return ""

    # ------------------------------------------------------------------
    def _draw_node(self, canvas, node: GSNNode, zoom: float) -> None:  # pragma: no cover - requires tkinter
        x, y = node.x * zoom, node.y * zoom
        typ = node.node_type.lower()
        text = self._format_text(node)

        try:
            font_obj = tkFont.Font(family="Arial", size=max(int(10 * zoom), 1))
            width, height = self.drawing_helper.get_text_size(text, font_obj)
        except Exception:  # pragma: no cover - headless fallback
            font_obj = None
            width = height = 0
        padding = 10 * zoom
        base_scale = 60 * zoom

        is_primary = node.is_primary_instance and getattr(node, "original", node) is node
        module_name = ""
        if not is_primary:
            module_name = self._find_module_name(node)

        def _call(method, *args, **kwargs):
            try:
                method(*args, **kwargs)
            except TypeError:  # pragma: no cover - fallback for simplified helpers
                kwargs.pop("text", None)
                kwargs.pop("top_text", None)
                kwargs.pop("bottom_text", None)
                kwargs.pop("font_obj", None)
                kwargs.pop("module_text", None)
                method(*args, **kwargs)

        if typ == "solution":
            # Render solution nodes using the same font size as other elements
            # and grow the circle to accommodate the text if needed.
            padding = 6 * zoom
            base_scale = 40 * zoom

            try:
                font_obj = tkFont.Font(family="Arial", size=max(int(10 * zoom), 1))
                t_width, t_height = self.drawing_helper.get_text_size(text, font_obj)
            except Exception:  # pragma: no cover - headless fallback
                font_obj = None
                t_width = t_height = 0

            scale = max(base_scale, max(t_width, t_height) + 2 * padding)
            draw_func = (
                self.drawing_helper.draw_solution_shape
                if is_primary
                else self.drawing_helper.draw_away_solution_shape
            )
            kwargs = {
                "text": text,
                "font_obj": font_obj,
                "obj_id": node.unique_id,
            }
            if not is_primary:
                kwargs["module_text"] = module_name
            _call(draw_func, canvas, x, y, scale, **kwargs)
        elif typ == "goal":
            ratio = 0.6
            scale = max(base_scale, width + padding, (height + padding) / ratio)
            draw_func = (
                self.drawing_helper.draw_goal_shape
                if is_primary
                else self.drawing_helper.draw_away_goal_shape
            )
            kwargs = {
                "text": text,
                "font_obj": font_obj,
                "obj_id": node.unique_id,
            }
            if not is_primary:
                kwargs["module_text"] = module_name
            _call(draw_func, canvas, x, y, scale, **kwargs)
        elif typ == "module":
            ratio = 0.6
            scale = max(base_scale, width + padding, (height + padding) / ratio)
            _call(
                self.drawing_helper.draw_module_shape,
                canvas,
                x,
                y,
                scale,
                text=text,
                font_obj=font_obj,
                obj_id=node.unique_id,
            )
        elif typ == "strategy":
            ratio = 0.5
            scale = max(base_scale, width + padding, (height + padding) / ratio)
            _call(
                self.drawing_helper.draw_strategy_shape,
                canvas,
                x,
                y,
                scale,
                text=text,
                font_obj=font_obj,
                obj_id=node.unique_id,
            )
        elif typ in {"assumption", "justification", "context"}:
            ratio = 0.5
            scale = max(base_scale, width + padding, (height + padding) / ratio)
            draw_func = self._context_draw_func(typ, is_primary)
            kwargs = {
                "text": text,
                "font_obj": font_obj,
                "obj_id": node.unique_id,
            }
            if not is_primary:
                kwargs["module_text"] = module_name
            _call(draw_func, canvas, x, y, scale, **kwargs)

    def _context_draw_func(self, typ: str, is_primary: bool):
        if is_primary:
            return {
                "assumption": self.drawing_helper.draw_assumption_shape,
                "justification": self.drawing_helper.draw_justification_shape,
                "context": self.drawing_helper.draw_context_shape,
            }[typ]
        return {
            "assumption": self.drawing_helper.draw_away_assumption_shape,
            "justification": self.drawing_helper.draw_away_justification_shape,
            "context": self.drawing_helper.draw_away_context_shape,
        }[typ]

    def _format_text(self, node: GSNNode) -> str:
        """Return node label including description if present."""
        if node.node_type == "Solution":
            lines = [node.user_name]
            if getattr(node, "spi_target", ""):
                prob = self._lookup_spi_probability(node.spi_target)
                v_target = self._lookup_validation_target(node.spi_target)
                label = None
                try:
                    if v_target not in (None, "") and prob not in (None, ""):
                        v_val = float(v_target)
                        p_val = float(prob)
                        if v_val > 0 and p_val > 0:
                            spi = math.log10(v_val / p_val)
                            label = f"SPI: {spi:.2f}"
                except Exception:
                    label = None
                if not label:
                    if v_target not in (None, ""):
                        label = f"SPI: {v_target}/h"
                    elif prob not in (None, ""):
                        label = f"SPI: {prob:.2e}/h"
                    else:
                        label = f"SPI: {node.spi_target}"
                lines.append(label)
            if getattr(node, "description", ""):
                lines.append(node.description)
            return "\n".join(lines)
        if getattr(node, "description", ""):
            return f"{node.user_name}\n{node.description}"
        return node.user_name

    # ------------------------------------------------------------------
    def _wrap_text(self, text: str, font_obj, max_width: float) -> str:
        """Wrap *text* so that each line fits within *max_width* pixels.

        The wrapping honours existing newline characters and attempts to
        break lines at whitespace.  A very small and self-contained helper is
        used instead of :mod:`textwrap` so that we can operate on pixel
        measurements provided by ``font_obj``.
        """
        lines = []
        for line in text.split("\n"):
            if not line:
                lines.append("")
                continue
            current = ""
            for word in line.split():
                candidate = f"{current} {word}".strip()
                if current and font_obj.measure(candidate) > max_width:
                    lines.append(current)
                    current = word
                else:
                    current = candidate
            if current:
                lines.append(current)
        return "\n".join(lines)
