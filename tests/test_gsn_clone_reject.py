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

import pytest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from mainappsrc.models.gsn.nodes import GSNNode
from mainappsrc.models.gsn.diagram import GSNDiagram
from AutoML import AutoMLApp, AutoML_Helper
from mainappsrc.managers.diagram_clipboard_manager import DiagramClipboardManager
from gui.controls import messagebox


def test_clone_rejects_unsupported_types():
    strategy = GSNNode("S", "Strategy")
    with pytest.raises(ValueError):
        strategy.clone()
    module = GSNNode("M", "Module")
    with pytest.raises(ValueError):
        module.clone()


def test_paste_rejects_disallowed_clone():
    root = GSNNode("Root", "Goal")
    strat = GSNNode("Strat", "Strategy")
    root.add_child(strat)
    diag = GSNDiagram(root)
    app = AutoMLApp.__new__(AutoMLApp)
    app.diagram_clipboard = DiagramClipboardManager(app)
    app.root_node = root
    app.top_events = []
    app.diagram_clipboard.clipboard_node = strat
    app.selected_node = root
    app.analysis_tree = type("T", (), {"selection": lambda self: [], "item": lambda *a, **k: {}})()
    app.diagram_clipboard.cut_mode = False
    app.update_views = lambda: None
    app._find_gsn_diagram = lambda n: diag
    AutoML_Helper.calculate_assurance_recursive = lambda *a, **k: None
    called = {}
    messagebox.showwarning = lambda *a, **k: called.setdefault("msg", a[1] if len(a) > 1 else "")
    app.paste_node()
    assert len(root.children) == 1
    assert called
