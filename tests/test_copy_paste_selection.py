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

# Provide dummy PIL modules so AutoML can be imported without Pillow
sys.modules.setdefault("PIL", types.ModuleType("PIL"))
sys.modules.setdefault("PIL.Image", types.ModuleType("PIL.Image"))
sys.modules.setdefault("PIL.ImageDraw", types.ModuleType("PIL.ImageDraw"))
sys.modules.setdefault("PIL.ImageFont", types.ModuleType("PIL.ImageFont"))
sys.modules.setdefault("PIL.ImageTk", types.ModuleType("PIL.ImageTk"))

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from AutoML import AutoMLApp, FaultTreeNode
from mainappsrc.managers.diagram_clipboard_manager import DiagramClipboardManager
from gui.controls import messagebox


class DummyTree:
    def __init__(self, node):
        self._sel = ("item1",)
        self._meta = {"item1": {"tags": (str(node.unique_id),)}}
    def selection(self):
        return self._sel
    def item(self, iid, attr):
        return self._meta[iid][attr]


class CopyPasteSelectionTests(unittest.TestCase):
    def setUp(self):
        self.app = AutoMLApp.__new__(AutoMLApp)
        self.app.diagram_clipboard = DiagramClipboardManager(self.app)
        self.app.root_node = FaultTreeNode("root", "TOP EVENT")
        child = FaultTreeNode("child", "GATE", parent=self.app.root_node)
        self.app.root_node.children.append(child)
        self.child = child
        self.app.selected_node = None
        self.app.diagram_clipboard.clipboard_node = None
        self.app.analysis_tree = DummyTree(child)
        self.app.find_node_by_id = AutoMLApp.find_node_by_id.__get__(self.app)
        self.app.top_events = []
        self.app.update_views = lambda: None
        self.app.diagram_clipboard.cut_mode = False

    def test_copy_uses_tree_selection_when_no_selected_node(self):
        self.app.copy_node()
        self.assertIs(self.app.diagram_clipboard.clipboard_node, self.child)

    def test_cut_uses_tree_selection_when_no_selected_node(self):
        self.app.cut_node()
        self.assertIs(self.app.diagram_clipboard.clipboard_node, self.child)
        self.assertTrue(self.app.diagram_clipboard.cut_mode)

    def test_copy_prefers_tree_selection_over_root(self):
        self.app.selected_node = self.app.root_node
        self.app.copy_node()
        self.assertIs(self.app.diagram_clipboard.clipboard_node, self.child)

    def test_cut_prefers_tree_selection_over_root(self):
        self.app.selected_node = self.app.root_node
        self.app.cut_node()
        self.assertIs(self.app.diagram_clipboard.clipboard_node, self.child)
        self.assertTrue(self.app.diagram_clipboard.cut_mode)

    def test_paste_warns_when_clipboard_empty_first(self):
        warnings = []
        orig = messagebox.showwarning
        messagebox.showwarning = lambda title, msg: warnings.append((title, msg))
        try:
            self.app.paste_node()
        finally:
            messagebox.showwarning = orig
        self.assertEqual(warnings[0][1], "Clipboard is empty.")


if __name__ == "__main__":
    unittest.main()

