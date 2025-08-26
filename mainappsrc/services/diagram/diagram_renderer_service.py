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

"""High level wrapper around diagram rendering utilities.

This service consolidates the legacy :mod:`diagram_renderer`,
:mod:`page_diagram` and :mod:`node_utils` modules under a single
interface.  Export operations are delegated to the existing
``diagram_export_subapp`` managed by :class:`AutoMLApp`.
"""

from __future__ import annotations

from typing import Any

from ...core.diagram_renderer import DiagramRenderer
from ...core.page_diagram import PageDiagram
from gui.utils.node_utils import resolve_original


class DiagramRendererService:
    """Facade for diagram rendering and export helpers."""

    def __init__(self, app: Any) -> None:
        self.app = app
        self._renderer = DiagramRenderer(app)

    # ------------------------------------------------------------------
    # Delegation to underlying DiagramRenderer
    # ------------------------------------------------------------------
    def __getattr__(self, name: str):
        return getattr(self._renderer, name)

    # ------------------------------------------------------------------
    # Page diagram helpers
    # ------------------------------------------------------------------
    def create_page_diagram(self, page_node, canvas):
        """Return a :class:`PageDiagram` instance."""
        return PageDiagram(self.app, page_node, canvas)

    @staticmethod
    def resolve_original(node):
        """Expose :func:`resolve_original` from ``node_utils``."""
        return resolve_original(node)

    # ------------------------------------------------------------------
    # Export helpers delegated to DiagramExportSubApp
    # ------------------------------------------------------------------
    def save_diagram_png(self):  # pragma: no cover - GUI export
        return self.app.diagram_export_app.save_diagram_png()

    def capture_page_diagram(self, page_node):  # pragma: no cover - GUI export
        return self.app.diagram_export_app.capture_page_diagram(page_node)

    def capture_gsn_diagram(self, diagram):  # pragma: no cover - GUI export
        return self.app.diagram_export_app.capture_gsn_diagram(diagram)

    def capture_sysml_diagram(self, diagram):  # pragma: no cover - GUI export
        return self.app.diagram_export_app.capture_sysml_diagram(diagram)

    def capture_cbn_diagram(self, doc):  # pragma: no cover - GUI export
        return self.app.diagram_export_app.capture_cbn_diagram(doc)

