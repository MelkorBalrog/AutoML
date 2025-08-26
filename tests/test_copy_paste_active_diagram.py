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
from types import SimpleNamespace

from AutoML import AutoMLApp, AutoML_Helper, messagebox
from mainappsrc.managers.diagram_clipboard_manager import DiagramClipboardManager
from mainappsrc.models.gsn import GSNNode, GSNDiagram


class CopyPasteActiveDiagramTests(unittest.TestCase):
    def setUp(self):
        AutoML_Helper.calculate_assurance_recursive = staticmethod(lambda *a, **k: None)
        messagebox.showwarning = lambda *a, **k: None
        messagebox.showinfo = lambda *a, **k: None

    def _make_app(self):
        app = AutoMLApp.__new__(AutoMLApp)
        app.diagram_clipboard = DiagramClipboardManager(app)
        app.top_events = []
        app.update_views = lambda: None
        app._make_doc_tab_visible = lambda _id: None
        app.refresh_all = lambda: None
        app.analysis_tree = SimpleNamespace(selection=lambda: [])
        app.gsn_modules = []
        return app

    def test_copy_and_cut_paste_use_focused_diagram(self):
        for mode in ("copy", "cut"):
            with self.subTest(mode=mode):
                app = self._make_app()
                root1 = GSNNode("Root1", "Goal", x=0, y=0)
                node = GSNNode("Child", "Solution", x=10, y=10)
                node.display_label = "Child"
                root1.add_child(node)
                diag1 = GSNDiagram(root1)
                root2 = GSNNode("Root2", "Goal", x=0, y=0)
                diag2 = GSNDiagram(root2)
                app.gsn_diagrams = [diag1, diag2]
                app.root_node = root1
                app.diagram_clipboard.clipboard_node = node
                app.diagram_clipboard.cut_mode = mode == "cut"
                tab1 = SimpleNamespace(gsn_window=SimpleNamespace(diagram=diag1), winfo_children=lambda: [])
                tab2 = SimpleNamespace(gsn_window=SimpleNamespace(diagram=diag2), winfo_children=lambda: [])
                notebook = SimpleNamespace(select=lambda: "tab2", nametowidget=lambda tid: {"tab1": tab1, "tab2": tab2}[tid])
                event = SimpleNamespace(widget=notebook)
                app.doc_nb = notebook
                app.diagram_tabs = {"d1": tab1, "d2": tab2}
                app._on_tab_change(event)
                app.paste_node()
                if mode == "copy":
                    self.assertEqual(len(diag1.root.children), 1)
                    self.assertEqual(len(diag2.root.children), 1)
                    self.assertIs(diag2.root.children[0], node)
                else:
                    self.assertEqual(len(diag1.root.children), 0)
                    self.assertEqual(len(diag2.root.children), 1)
                    self.assertIs(diag2.root.children[0], node)


if __name__ == "__main__":
    unittest.main()
