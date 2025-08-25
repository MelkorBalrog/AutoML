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
import types

sys.path.append(str(Path(__file__).resolve().parents[1]))

PIL_stub = types.ModuleType("PIL")
PIL_stub.Image = types.SimpleNamespace()
PIL_stub.ImageTk = types.SimpleNamespace()
PIL_stub.ImageDraw = types.SimpleNamespace()
PIL_stub.ImageFont = types.SimpleNamespace()
sys.modules.setdefault("PIL", PIL_stub)
sys.modules.setdefault("PIL.Image", PIL_stub.Image)
sys.modules.setdefault("PIL.ImageTk", PIL_stub.ImageTk)
sys.modules.setdefault("PIL.ImageDraw", PIL_stub.ImageDraw)
sys.modules.setdefault("PIL.ImageFont", PIL_stub.ImageFont)

from AutoML import AutoMLApp
import tkinter as tk
import pytest
from gui.requirement_patterns_toolbox import RequirementPatternsEditor


def test_requirement_patterns_toolbox_single_instance():
    """Opening requirement patterns toolbox twice doesn't duplicate editor."""

    class DummyTab:
        def winfo_exists(self):
            return True

    class DummyNotebook:
        def add(self, tab, text):
            pass

        def select(self, tab):
            pass

    class DummyEditor:
        created = 0

        def __init__(self, master, app, path):
            DummyEditor.created += 1

        def pack(self, **kwargs):
            pass

        def winfo_exists(self):
            return True

    import gui.requirement_patterns_toolbox as rpt

    rpt.RequirementPatternsEditor = DummyEditor

    class DummyApp:
        open_requirement_patterns_toolbox = AutoMLApp.open_requirement_patterns_toolbox

        def __init__(self):
            self.doc_nb = DummyNotebook()

        def _new_tab(self, title):
            return DummyTab()

    app = DummyApp()
    app.open_requirement_patterns_toolbox()
    app.open_requirement_patterns_toolbox()
    assert DummyEditor.created == 1


def test_pattern_tree_wraps_text(tmp_path):
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk not available")

    cfg = tmp_path / "patterns.json"
    cfg.write_text("[]")

    editor = RequirementPatternsEditor(root, object(), cfg)
    editor.data = [{"Trigger": "A " * 30, "Template": "B " * 30}]
    editor._populate_pattern_tree()
    vals = editor.tree.item(editor.tree.get_children()[0], "values")
    assert vals[0] == "1"
    assert "\n" in vals[1]
    assert "\n" in vals[2]
    root.destroy()
