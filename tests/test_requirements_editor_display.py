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
"""Requirements editor display tests."""

from pathlib import Path
import sys
import tkinter as tk
import types
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analysis.models import global_requirements
from mainappsrc.core.editors import Editors


class TestRequirementsEditorDisplay:
    """Group requirements editor GUI display tests."""

    def _make_app(self):
        try:
            root = tk.Tk()
        except tk.TclError:  # pragma: no cover - skip if no display
            pytest.skip("Tk display not available")
        root.withdraw()
        lifecycle_ui = types.SimpleNamespace(_new_tab=lambda name: tk.Frame(root))
        app = types.SimpleNamespace(
            update_requirement_statuses=lambda: None,
            lifecycle_ui=lifecycle_ui,
            doc_nb=types.SimpleNamespace(select=lambda tab: None),
            add_requirement=lambda *a, **k: None,
            edit_requirement=lambda *a, **k: None,
            delete_requirement=lambda *a, **k: None,
            link_requirement=lambda *a, **k: None,
            unlink_requirement=lambda *a, **k: None,
            export_requirements_to_csv=lambda: None,
        )
        return root, app

    def setup_method(self):
        global_requirements.clear()
        global_requirements["R1"] = {"id": "R1", "text": "Req"}

    def test_tree_frame_packed(self):
        root, app = self._make_app()
        Editors(app).show_requirements_editor()
        frame = app._req_tab.winfo_children()[0]
        assert frame.winfo_manager()
        root.destroy()

    def test_tree_columns_present(self):
        root, app = self._make_app()
        Editors(app).show_requirements_editor()
        frame = app._req_tab.winfo_children()[0]
        tree = frame.winfo_children()[0]
        assert tree.cget("columns") == (
            "ID",
            "ASIL",
            "CAL",
            "Type",
            "Status",
            "Parent",
            "Trace",
            "Links",
            "Text",
        )
        root.destroy()
