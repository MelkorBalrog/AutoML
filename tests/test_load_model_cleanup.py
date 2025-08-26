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

import sys, types, json
from unittest.mock import MagicMock

# Stub PIL modules for AutoML import
sys.modules.setdefault("PIL", types.ModuleType("PIL"))
sys.modules.setdefault("PIL.Image", types.ModuleType("PIL.Image"))
sys.modules.setdefault("PIL.ImageDraw", types.ModuleType("PIL.ImageDraw"))
sys.modules.setdefault("PIL.ImageFont", types.ModuleType("PIL.ImageFont"))
sys.modules.setdefault("PIL.ImageTk", types.ModuleType("PIL.ImageTk"))

from AutoML import AutoMLApp
import AutoML
from mainappsrc.managers.undo_manager import UndoRedoManager


class DummyNotebook:
    def __init__(self):
        self._tabs = ["t1", "t2"]

    def tabs(self):
        return list(self._tabs)

    def event_generate(self, _):
        pass

    def forget(self, tab_id):
        if tab_id in self._tabs:
            self._tabs.remove(tab_id)


def _minimal_app(monkeypatch):
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

    def fake_create_tab():
        app.canvas = MagicMock()
    monkeypatch.setattr(app, "_create_fta_tab", fake_create_tab)
    monkeypatch.setattr(AutoML, "SysMLRepository", MagicMock())
    monkeypatch.setattr(AutoML, "AutoMLHelper", MagicMock())
    monkeypatch.setattr(AutoML, "AutoML_Helper", MagicMock(), raising=False)
    return app


def test_reset_on_load_clears_state(monkeypatch):
    app = _minimal_app(monkeypatch)
    app._reset_on_load()
    assert app.use_case_windows == []
    assert app.doc_nb.tabs() == []
    app.close_page_diagram.assert_called()


def test_load_model_invokes_reset(tmp_path, monkeypatch):
    model = tmp_path / "model.json"
    model.write_text("{}")

    app = AutoMLApp.__new__(AutoMLApp)
    app._loaded_model_paths = []
    app.apply_model_data = MagicMock()
    app.set_last_saved_state = MagicMock()
    app._reset_on_load = MagicMock()
    app.has_unsaved_changes = lambda: False

    monkeypatch.setattr(AutoML.filedialog, "askopenfilename", lambda **k: str(model))
    monkeypatch.setattr(AutoML.messagebox, "showerror", lambda *a, **k: None)

    app.load_model()
    app._reset_on_load.assert_called_once()
    app.apply_model_data.assert_called_once_with({})
    assert app._loaded_model_paths == [str(model)]
