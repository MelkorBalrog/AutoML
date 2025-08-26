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

from gui.architecture import GovernanceDiagramWindow, SysMLObject, DiagramConnection
from mainappsrc.models.sysml.sysml_repository import SysMLRepository


def test_delete_connection_refreshes_enablement(monkeypatch):
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    diag = repo.create_diagram("Governance Diagram", name="Gov1")
    diag.tags.append("safety-management")

    win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
    win.repo = repo
    win.diagram_id = diag.diag_id
    win.objects = []
    win.connections = []
    win.selected_conn = None
    win.selected_objs = []
    win.zoom = 1.0
    win._sync_to_repository = lambda: None
    win.redraw = lambda: None
    win.update_property_view = lambda: None
    win.get_object = GovernanceDiagramWindow.get_object.__get__(win, GovernanceDiagramWindow)

    o1 = SysMLObject(1, "Action", 0, 0)
    o2 = SysMLObject(2, "Action", 0, 0)
    win.objects.extend([o1, o2])
    conn = DiagramConnection(src=1, dst=2, conn_type="Flow")
    win.connections.append(conn)
    win.selected_conn = conn

    called = []

    class DummyApp:
        def refresh_tool_enablement(self):
            called.append(True)

    win.app = DummyApp()

    win.delete_selected()

    assert called == [True]
    assert win.connections == []
