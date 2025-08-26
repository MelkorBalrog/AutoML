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

import types

from gui import architecture


def _window():
    win = architecture.GovernanceDiagramWindow.__new__(
        architecture.GovernanceDiagramWindow
    )
    win.repo = types.SimpleNamespace(diagrams={}, relationships=[], active_phase=None)
    win.diagram_id = "d"
    win.repo.diagrams["d"] = types.SimpleNamespace(diag_type="Governance Diagram")
    return win


def test_standard_used_by_phase_valid():
    win = _window()
    src = architecture.SysMLObject(1, "Standard", 0, 0, properties={"name": "STD"})
    dst = architecture.SysMLObject(2, "Lifecycle Phase", 0, 0, properties={"name": "P"})
    valid, _ = architecture.GovernanceDiagramWindow.validate_connection(
        win, src, dst, "Used By"
    )
    assert valid


def test_phase_used_by_standard_invalid():
    win = _window()
    src = architecture.SysMLObject(1, "Lifecycle Phase", 0, 0, properties={"name": "P"})
    dst = architecture.SysMLObject(2, "Standard", 0, 0, properties={"name": "STD"})
    valid, msg = architecture.GovernanceDiagramWindow.validate_connection(
        win, src, dst, "Used By"
    )
    assert not valid
    assert "not allowed" in msg.lower()
