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

import unittest
import types
import os
import sys
import pytest

# Provide dummy PIL modules so AutoML can be imported without Pillow
sys.modules.setdefault("PIL", types.ModuleType("PIL"))
sys.modules.setdefault("PIL.Image", types.ModuleType("PIL.Image"))
sys.modules.setdefault("PIL.ImageDraw", types.ModuleType("PIL.ImageDraw"))
sys.modules.setdefault("PIL.ImageFont", types.ModuleType("PIL.ImageFont"))
sys.modules.setdefault("PIL.ImageTk", types.ModuleType("PIL.ImageTk"))

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from AutoML import AutoMLApp, FaultTreeNode
from mainappsrc.models.gsn import GSNNode, GSNDiagram
from gui.controls import messagebox


class DummyTree:
    def selection(self):
        return ()
    def item(self, iid, attr):
        return None


class GSNCopyPasteTests(unittest.TestCase):
    def setUp(self):
        self.app = AutoMLApp.__new__(AutoMLApp)
        self.app.root_node = FaultTreeNode("root", "TOP EVENT")
        self.app.analysis_tree = DummyTree()
        self.app.top_events = []
        self.app.update_views = lambda: None

        root = GSNNode("G1", "Goal")
        child = GSNNode("S1", "Strategy")
        root.add_child(child)
        other = GSNNode("G2", "Goal")
        diagram = GSNDiagram(root)
        diagram.add_node(child)
        diagram.add_node(other)
        self.diagram = diagram
        self.child = child
        self.other = other

        self.app.gsn_diagrams = [diagram]
        self.app.gsn_modules = []
        self.app.selected_node = child

        # suppress message boxes during tests
        self._orig_info = messagebox.showinfo
        self._orig_warn = messagebox.showwarning
        messagebox.showinfo = lambda *a, **k: None
        messagebox.showwarning = lambda *a, **k: None

    def tearDown(self):
        messagebox.showinfo = self._orig_info
        messagebox.showwarning = self._orig_warn

    def test_pasted_unsupported_node_rejected(self):
        self.app.copy_node()
        self.app.selected_node = self.other  # paste into a different goal
        self.app.paste_node()
        self.assertEqual(len(self.diagram.nodes), 3)
        self.assertEqual(len(self.other.children), 0)

    def test_context_relation_preserved_on_paste(self):
        for typ in ("Context", "Assumption", "Justification"):
            root = GSNNode("Root", "Goal")
            node = GSNNode("Ctx", typ)
            root.add_child(node, relation="context")
            diag = GSNDiagram(root)
            diag.add_node(node)
            app = AutoMLApp.__new__(AutoMLApp)
            app.root_node = root
            app.analysis_tree = DummyTree()
            app.top_events = []
            app.update_views = lambda: None
            app.selected_node = node
            orig_info = messagebox.showinfo
            orig_warn = messagebox.showwarning
            messagebox.showinfo = lambda *a, **k: None
            messagebox.showwarning = lambda *a, **k: None
            try:
                app.copy_node()
                app.selected_node = root
                app.paste_node()
            finally:
                messagebox.showinfo = orig_info
                messagebox.showwarning = orig_warn
            assert len(root.context_children) == 2
            pasted = root.context_children[-1]
            assert pasted is not node
            assert pasted.original is node

    def test_context_relation_preserved_on_paste(self):
        root = GSNNode("Root", "Goal")
        ctx = GSNNode("Ctx", "Context")
        root.context_children.append(ctx)
        ctx.parents.append(root)
        diag = GSNDiagram(root)
        diag.add_node(ctx)
        app = AutoMLApp.__new__(AutoMLApp)
        app.root_node = root
        app.analysis_tree = DummyTree()
        app.top_events = []
        app.update_views = lambda: None
        app.selected_node = ctx
        orig_info = messagebox.showinfo
        orig_warn = messagebox.showwarning
        messagebox.showinfo = lambda *a, **k: None
        messagebox.showwarning = lambda *a, **k: None
        try:
            app.copy_node()
            app.selected_node = root
            app.paste_node()
        finally:
            messagebox.showinfo = orig_info
            messagebox.showwarning = orig_warn
        assert len(root.context_children) == 2
        pasted = root.context_children[-1]
        assert pasted is not ctx
        assert pasted.original is ctx

    def test_context_relation_preserved_on_paste(self):
        root = GSNNode("Root", "Goal")
        ctx = GSNNode("Ctx", "Context")
        root.context_children.append(ctx)
        ctx.parents.append(root)
        diag = GSNDiagram(root)
        diag.add_node(ctx)
        app = AutoMLApp.__new__(AutoMLApp)
        app.root_node = root
        app.analysis_tree = DummyTree()
        app.top_events = []
        app.update_views = lambda: None
        app.selected_node = ctx
        orig_info = messagebox.showinfo
        orig_warn = messagebox.showwarning
        messagebox.showinfo = lambda *a, **k: None
        messagebox.showwarning = lambda *a, **k: None
        try:
            app.copy_node()
            app.selected_node = root
            app.paste_node()
        finally:
            messagebox.showinfo = orig_info
            messagebox.showwarning = orig_warn
        assert len(root.context_children) == 2
        pasted = root.context_children[-1]
        assert pasted is not ctx
        assert pasted.original is ctx

if __name__ == "__main__":
    unittest.main()
