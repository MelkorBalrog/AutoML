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
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from mainappsrc.automl_core import AutoMLApp


class DummyTree:
    def __init__(self):
        self.children = {"": []}
        self.items = {}

    def delete(self, *nodes):
        for n in nodes:
            for parent, kids in self.children.items():
                if n in kids:
                    kids.remove(n)
            self.children.pop(n, None)
            self.items.pop(n, None)

    def get_children(self, item=""):
        return self.children.get(item, [])

    def insert(self, parent, index, text, **kwargs):
        node_id = f"id{len(self.items)}"
        self.children.setdefault(parent, []).append(node_id)
        self.children.setdefault(node_id, [])
        self.items[node_id] = {"text": text, "tags": kwargs.get("tags", ())}
        return node_id

    def item(self, node, option):
        return self.items[node][option]


def _setup_app_for_tree():
    app = AutoMLApp.__new__(AutoMLApp)
    app.analysis_tree = DummyTree()
    app.top_events = []
    app.cta_events = [type("N", (), {"name": "c1", "unique_id": 1})()]
    app.paa_events = [type("N", (), {"name": "p1", "unique_id": 2})()]
    app.fmeas = []
    app.fmedas = []
    app.hara_docs = []
    app.gsn_diagrams = []
    app.gsn_modules = []
    app.management_diagrams = []
    app.enabled_work_products = {"CTA", "Prototype Assurance Analysis"}
    app.refresh_model = lambda: None
    app.compute_occurrence_counts = lambda: {}

    class TB:
        work_products = [1]
        modules = []
        diagrams = {}

        def enabled_products(self):
            return app.enabled_work_products

        def document_visible(self, a, b):
            return True

        def list_diagrams(self):
            pass

    app.safety_mgmt_toolbox = TB()
    app.update_lifecycle_cb = lambda: None
    app.refresh_tool_enablement = lambda: None
    app.filter_var = type("FV", (), {"get": lambda self: ""})()
    app.displayed_filters = set()
    app.filter_lifecycle = None

    def _populate_tree():
        sa_root = app.analysis_tree.insert("", 0, "Safety Analysis")
        app.analysis_tree.insert(sa_root, 0, "CTAs")
        app.analysis_tree.insert(sa_root, 1, "PAAs")

    app.update_views = _populate_tree
    app.view_update_service = type("VUS", (), {"update_views": _populate_tree})()
    return app


def test_cta_and_paa_groups_separate():
    app = _setup_app_for_tree()
    app.update_views()
    sa_root = next(n for n, d in app.analysis_tree.items.items() if d["text"] == "Safety Analysis")
    child_texts = [app.analysis_tree.items[c]["text"] for c in app.analysis_tree.get_children(sa_root)]
    assert "CTAs" in child_texts
    assert child_texts.count("PAAs") == 1


def test_get_node_fill_color_by_mode():
    app = AutoMLApp.__new__(AutoMLApp)
    class C:
        pass
    app.canvas = C()
    app.canvas.diagram_mode = "CTA"
    assert app.get_node_fill_color(None) == "#EE82EE"
    app.canvas.diagram_mode = "PAA"
    assert app.get_node_fill_color(None) == "#40E0D0"
    app.canvas.diagram_mode = "FTA"
    assert app.get_node_fill_color(None) == "#FAD7A0"
