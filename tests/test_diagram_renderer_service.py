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

"""Tests for :class:`DiagramRendererService`."""

from __future__ import annotations

from unittest.mock import MagicMock

from mainappsrc.services.diagram import DiagramRendererService


class DummyApp:
    def __init__(self):
        self.diagram_export_app = MagicMock()


class DummyNode:
    def __init__(self, primary=None):
        self.is_primary_instance = primary is None
        self.original = primary or self


def test_resolve_original_returns_primary():
    app = DummyApp()
    service = DiagramRendererService(app)
    base = DummyNode()
    clone = DummyNode(primary=base)
    assert service.resolve_original(clone) is base


def test_save_diagram_png_delegates():
    app = DummyApp()
    service = DiagramRendererService(app)
    service.save_diagram_png()
    assert app.diagram_export_app.save_diagram_png.called
