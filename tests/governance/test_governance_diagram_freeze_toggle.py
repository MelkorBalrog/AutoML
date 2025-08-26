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

sys.path.append(str(Path(__file__).resolve().parents[1]))

from analysis.safety_management import SafetyManagementToolbox
from mainappsrc.models.sysml.sysml_repository import SysMLRepository


def test_manual_freeze_persists_across_save():
    SysMLRepository.reset_instance()
    repo = SysMLRepository.get_instance()
    tb = SafetyManagementToolbox()
    diag_id = tb.create_diagram("Gov1")
    tb.set_diagram_frozen("Gov1", True)
    assert repo.diagram_read_only(diag_id)

    repo_data = repo.to_dict()
    tb_data = tb.to_dict()

    SysMLRepository.reset_instance()
    repo = SysMLRepository.get_instance()
    repo.from_dict(repo_data)
    tb2 = SafetyManagementToolbox.from_dict(tb_data)
    diag_id2 = tb2.diagrams["Gov1"]
    assert repo.diagram_read_only(diag_id2)

    tb2.set_diagram_frozen("Gov1", False)
    assert not repo.diagram_read_only(diag_id2)
