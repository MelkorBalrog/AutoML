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

"""Tests for GSNDiagramWindow node selection helpers.

These tests exercise the four different ``_node_at`` strategies used by
``GSNDiagramWindow`` to locate a node under a given cursor position.  The
regression ensures that clicking on empty canvas space does not randomly
select a node which previously happened due to ``Canvas.find_closest`` always
returning an item.
"""


import pytest

from mainappsrc.models.gsn import GSNNode
from gui.gsn_diagram_window import GSNDiagramWindow


class _FakeCanvas:
    """Minimal stand-in for :class:`tkinter.Canvas` used for testing."""

    def __init__(self) -> None:
        self._item_tags: dict[int, tuple[str, ...]] = {}
        self._tag_bbox: dict[str, tuple[int, int, int, int]] = {}

    def register(self, item_id: int, tag: str, bbox: tuple[int, int, int, int]) -> None:
        self._item_tags[item_id] = (tag,)
        self._tag_bbox[tag] = bbox

    def canvasx(self, value: float) -> float:  # pragma: no cover - trivial
        return value

    def canvasy(self, value: float) -> float:  # pragma: no cover - trivial
        return value

    def find_overlapping(self, x1, y1, x2, y2):
        result = []
        for item, tags in self._item_tags.items():
            x1b, y1b, x2b, y2b = self._tag_bbox[tags[0]]
            if not (x2 < x1b or x1 > x2b or y2 < y1b or y1 > y2b):
                result.append(item)
        return result

    def find_closest(self, _x, _y):  # pragma: no cover - deterministic
        return list(self._item_tags.keys())

    def gettags(self, item):  # pragma: no cover - trivial
        return self._item_tags.get(item, ())

    def bbox(self, item_or_tag):  # pragma: no cover - trivial
        if isinstance(item_or_tag, str):
            return self._tag_bbox.get(item_or_tag)
        for tag in self._item_tags.get(item_or_tag, ()):  # pragma: no cover
            return self._tag_bbox.get(tag)
        return None


class _FakeDiagram:
    def __init__(self, nodes):  # pragma: no cover - simple container
        self._nodes = nodes

    def _traverse(self):  # pragma: no cover - simple iterator
        return list(self._nodes)


@pytest.fixture
def window() -> GSNDiagramWindow:
    node = GSNNode("Goal", "Goal", x=0, y=0)
    canvas = _FakeCanvas()
    canvas.register(1, "n1", (0, 0, 10, 10))
    diagram = _FakeDiagram([node])
    win = GSNDiagramWindow.__new__(GSNDiagramWindow)
    win.canvas = canvas
    win.id_to_node = {"n1": node}
    win.diagram = diagram
    win.zoom = 1.0
    return win


@pytest.mark.parametrize(
    "method",
    [
        "_node_at_strategy1",
        "_node_at_strategy2",
        "_node_at_strategy3",
        "_node_at_strategy4",
        "_node_at",
    ],
)
def test_click_outside_returns_none(window: GSNDiagramWindow, method: str) -> None:
    strat = getattr(window, method)
    assert strat(100, 100) is None


@pytest.mark.parametrize(
    "method",
    [
        "_node_at_strategy1",
        "_node_at_strategy2",
        "_node_at_strategy3",
        "_node_at_strategy4",
        "_node_at",
    ],
)
def test_click_inside_returns_node(window: GSNDiagramWindow, method: str) -> None:
    strat = getattr(window, method)
    assert strat(5, 5) is window.id_to_node["n1"]

