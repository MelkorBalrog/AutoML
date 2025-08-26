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

import sys, types, pathlib
from unittest.mock import MagicMock

# Ensure repository root on path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

# Stub PIL modules for AutoML import
sys.modules.setdefault("PIL", types.ModuleType("PIL"))
sys.modules.setdefault("PIL.Image", types.ModuleType("PIL.Image"))
sys.modules.setdefault("PIL.ImageDraw", types.ModuleType("PIL.ImageDraw"))
sys.modules.setdefault("PIL.ImageFont", types.ModuleType("PIL.ImageFont"))
sys.modules.setdefault("PIL.ImageTk", types.ModuleType("PIL.ImageTk"))

from AutoML import AutoMLApp
import AutoML
from mainappsrc.managers.undo_manager import UndoRedoManager
from mainappsrc.managers.project_manager import ProjectManager

class DummyNotebook:
    def __init__(self):
        self._tabs = ["t1"]
        self._closing_tab = None

    def tabs(self):
        return list(self._tabs)

    def event_generate(self, _):
        pass

    def forget(self, tab_id):
        if tab_id in self._tabs:
            self._tabs.remove(tab_id)


def _base_app(monkeypatch):
    app = AutoMLApp.__new__(AutoMLApp)
    app.undo_manager = UndoRedoManager(app)
    app.doc_nb = DummyNotebook()
    app.analysis_tree = MagicMock()
    app.analysis_tree.get_children.return_value = []
    app.analysis_tree.delete = MagicMock()
    app.close_page_diagram = MagicMock()
    app.page_diagram = object()
    app.use_case_windows = [MagicMock()]
    app.activity_windows = [MagicMock()]
    app.block_windows = [MagicMock()]
    app.ibd_windows = [MagicMock()]
    app.diagram_font = MagicMock()
    app.hara_docs = []
    app.hazop_docs = []
    app.fmea_entries = []
    app.safety_analysis = types.SimpleNamespace(
        fmeas=[], fmedas=[], _load_fault_tree_events=lambda *a, **k: None
    )
    app.fmeas = []
    app.fmedas = []
    app.safety_mgmt_toolbox = MagicMock()
    app.safety_mgmt_toolbox.doc_phases = {}
    app.safety_mgmt_toolbox.active_module = None
    app.safety_mgmt_toolbox.register_created_work_product = MagicMock()
    app.probability_reliability = MagicMock()
    app.probability_reliability.update_probability_tables = lambda *a, **k: None
    app.project_manager = ProjectManager(app)
    app.messagebox = MagicMock()

    monkeypatch.setattr(AutoML, "SysMLRepository", MagicMock(), raising=False)
    monkeypatch.setattr(AutoML, "AutoMLHelper", MagicMock())
    monkeypatch.setattr(AutoML, "AutoML_Helper", MagicMock(), raising=False)
    monkeypatch.setattr(
        AutoML, "update_probability_tables", lambda *a, **k: None, raising=False
    )
    monkeypatch.setattr(AutoML.messagebox, "askyesnocancel", lambda *a, **k: False)
    return app


def test_new_model_no_fta_tab(monkeypatch):
    app = _base_app(monkeypatch)
    app.has_unsaved_changes = MagicMock(return_value=False)
    app.apply_model_data = MagicMock()
    app.set_last_saved_state = MagicMock()
    app._create_fta_tab = MagicMock()

    app.new_model()
    app._create_fta_tab.assert_not_called()
    assert "FTA" not in app.doc_nb.tabs()


def test_reset_on_load_no_fta_tab(monkeypatch):
    app = _base_app(monkeypatch)
    app._create_fta_tab = MagicMock()

    app._reset_on_load()
    app._create_fta_tab.assert_not_called()
    assert app.doc_nb.tabs() == []
