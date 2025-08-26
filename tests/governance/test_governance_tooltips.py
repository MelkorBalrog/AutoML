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

import sys
import types
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from gui.architecture import SysMLDiagramWindow, SysMLObject
from mainappsrc.models.sysml.sysml_repository import SysMLRepository
from config import load_diagram_rules


class DummyCanvas:
    def canvasx(self, x):
        return x

    def canvasy(self, y):
        return y

    def configure(self, **kwargs):
        pass


class DummyTip:
    def __init__(self, widget, text, automatic=False):
        self.text = text

    def show(self, x=None, y=None):
        pass

    def hide(self):
        pass


def _expected_text(cfg, node_type: str) -> str:
    rules = cfg["connection_rules"]["Governance Diagram"]
    outgoing = {}
    incoming = {}
    for rel, srcs in rules.items():
        targets = srcs.get(node_type, [])
        if targets:
            outgoing[rel] = sorted(targets)
        for src, dests in srcs.items():
            if node_type in dests:
                incoming.setdefault(rel, []).append(src)
    if not outgoing and not incoming:
        return ""

    rows = []
    for rel in sorted(set(outgoing) | set(incoming)):
        outs = ", ".join(outgoing.get(rel, []))
        ins = ", ".join(sorted(incoming.get(rel, [])))
        rows.append((rel, outs, ins))

    headers = ("Relation", "To Others", "From Others")
    col_widths = [
        max(len(row[i]) for row in rows + [headers]) for i in range(3)
    ]
    lines = [
        " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)),
        "-+-".join("-" * col_widths[i] for i in range(3)),
    ]
    for row in rows:
        lines.append(
            " | ".join(row[i].ljust(col_widths[i]) for i in range(3))
        )
    return "\n".join(lines)


def test_governance_element_tooltips(monkeypatch):
    cfg = load_diagram_rules(
        Path(__file__).resolve().parents[1]
        / "config"
        / "rules"
        / "diagram_rules.json"
    )
    SysMLRepository.reset_instance()
    repo = SysMLRepository.get_instance()
    diag = repo.create_diagram("Governance Diagram", name="Gov")

    role = SysMLObject(1, "Role", 0.0, 0.0)
    org = SysMLObject(2, "Organization", 200.0, 0.0)
    op = SysMLObject(3, "Operation", 400.0, 0.0)

    win = SysMLDiagramWindow.__new__(SysMLDiagramWindow)
    win.canvas = DummyCanvas()
    win._conn_tip = DummyTip(win.canvas, "")
    win._conn_tip_obj = None
    win.repo = repo
    win.diagram_id = diag.diag_id
    win.current_tool = "Select"
    win.start = None
    win.zoom = 1.0
    win.objects = [role, org, op]
    win.find_object = SysMLDiagramWindow.find_object.__get__(win)

    win.on_mouse_move(types.SimpleNamespace(x=0, y=0))
    assert win._conn_tip.text == _expected_text(cfg, "Role")

    win.on_mouse_move(types.SimpleNamespace(x=200, y=0))
    assert win._conn_tip.text == _expected_text(cfg, "Organization")

    win.on_mouse_move(types.SimpleNamespace(x=400, y=0))
    assert win._conn_tip.text == _expected_text(cfg, "Operation")


def test_tooltip_hides_during_drag(monkeypatch):
    SysMLRepository.reset_instance()
    repo = SysMLRepository.get_instance()
    diag = repo.create_diagram("Governance Diagram", name="Gov")

    role = SysMLObject(1, "Role", 0.0, 0.0)

    win = SysMLDiagramWindow.__new__(SysMLDiagramWindow)
    win.canvas = DummyCanvas()
    win._conn_tip = DummyTip(win.canvas, "")
    win._conn_tip_obj = None
    win.repo = repo
    win.diagram_id = diag.diag_id
    win.current_tool = "Select"
    win.start = None
    win.zoom = 1.0
    win.objects = [role]
    win.connections = []
    win.find_object = SysMLDiagramWindow.find_object.__get__(win)
    win.redraw = lambda: None
    win.update_property_view = lambda: None
    win._sync_to_repository = lambda: None
    win.select_rect_start = None
    win.select_rect_id = None
    win.dragging_conn_mid = None
    win.dragging_conn_vec = None
    win.dragging_endpoint = None
    win.dragging_point_index = None
    win.conn_drag_offset = (0, 0)
    win.resizing_obj = None
    win.resize_edge = None
    win.selected_conn = None
    win.selected_objs = []
    win.drag_offset = (0, 0)
    win.app = None

    win.on_mouse_move(types.SimpleNamespace(x=0, y=0))
    assert win._conn_tip_obj == role

    hidden = {"called": False}

    def hide():
        hidden["called"] = True

    win._conn_tip.hide = hide

    win.on_left_press(types.SimpleNamespace(x=0, y=0, state=0))
    win.on_left_drag(types.SimpleNamespace(x=10, y=0))
    win.on_left_release(types.SimpleNamespace(x=10, y=0))

    assert hidden["called"]
    assert win._conn_tip_obj is None
