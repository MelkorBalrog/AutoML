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

import os
import sys
import types

# Ensure repository root is on the Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Provide dummy PIL modules so AutoML can be imported without Pillow
sys.modules.setdefault("PIL", types.ModuleType("PIL"))
sys.modules.setdefault("PIL.Image", types.ModuleType("PIL.Image"))
sys.modules.setdefault("PIL.ImageTk", types.ModuleType("PIL.ImageTk"))
sys.modules.setdefault("PIL.ImageDraw", types.ModuleType("PIL.ImageDraw"))
sys.modules.setdefault("PIL.ImageFont", types.ModuleType("PIL.ImageFont"))

from AutoML import AutoMLApp
from gui.architecture import GovernanceDiagramWindow, SysMLObject
from mainappsrc.models.sysml.sysml_repository import SysMLRepository
from mainappsrc.managers.undo_manager import UndoRedoManager


def test_governance_diagram_undo_redo_work_product():
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    diag = repo.create_diagram("Governance Diagram", name="Gov")

    app = AutoMLApp.__new__(AutoMLApp)
    app.export_model_data = lambda include_versions=False: {}
    app.apply_model_data = lambda data: None
    app.refresh_all = lambda: None
    app.diagram_tabs = {}
    app.undo_manager = UndoRedoManager(app)
    app.enable_work_product = lambda *a, **k: None
    app.refresh_tool_enablement_called = 0
    def refresh_tool_enablement(*args, **kwargs):
        app.refresh_tool_enablement_called += 1
    app.refresh_tool_enablement = refresh_tool_enablement
    app._refresh_phase_requirements_menu = lambda: None
    app.update_views = lambda: None
    app.push_undo_state = AutoMLApp.push_undo_state.__get__(app)
    app.undo = AutoMLApp.undo.__get__(app)
    app.redo = AutoMLApp.redo.__get__(app)

    win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
    win.app = app
    win.repo = repo
    win.diagram_id = diag.diag_id
    win.objects = []
    win.connections = []
    win.sort_objects = lambda: None
    win.redraw = lambda: None
    win.update_property_view = lambda: None

    win._place_work_product("WP1", 10.0, 20.0)
    assert len(repo.diagrams[diag.diag_id].objects) == 1
    app.refresh_tool_enablement_called = 0

    app.undo()
    assert len(repo.diagrams[diag.diag_id].objects) == 0

    app.redo()
    assert len(repo.diagrams[diag.diag_id].objects) == 1
    assert app.refresh_tool_enablement_called == 2
