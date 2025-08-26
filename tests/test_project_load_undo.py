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
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from AutoML import AutoMLApp
from mainappsrc.models.sysml.sysml_repository import SysMLRepository
from mainappsrc.managers.undo_manager import UndoRedoManager


def test_undo_after_project_load_keeps_project():
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    blk = repo.create_element("Block", name="A")
    data = {"sysml_repository": repo.to_dict()}

    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()

    app = AutoMLApp.__new__(AutoMLApp)
    app.export_model_data = lambda include_versions=False: data
    app.apply_model_data = lambda d: repo.from_dict(d["sysml_repository"])
    app.refresh_all = lambda: None
    app.diagram_tabs = {}
    app.undo_manager = UndoRedoManager(app)
    app.undo_manager._undo_stack = [{}]
    app.undo_manager._redo_stack = [{}]
    app.undo = AutoMLApp.undo.__get__(app)
    app.clear_undo_history = AutoMLApp.clear_undo_history.__get__(app)

    app.apply_model_data(data)
    app.clear_undo_history()
    app.undo()
    assert blk.elem_id in repo.elements
