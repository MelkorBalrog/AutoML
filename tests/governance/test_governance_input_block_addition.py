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
import pytest
from mainappsrc.models.sysml.sysml_repository import SysMLRepository
from analysis import safety_management as sm


@pytest.mark.parametrize("target", ["Control Flow Diagram", "HAZOP", "Risk Assessment"])
def test_existing_elements_require_governance(target):
    repo = SysMLRepository.reset_instance()
    arch = repo.create_diagram("Architecture Diagram", name="AD")
    elem = repo.create_element("Block", name="B1")
    repo.add_element_to_diagram(arch.diag_id, elem.elem_id)
    repo.link_diagram(elem.elem_id, arch.diag_id)
    tgt = repo.create_diagram(target, name="T")

    toolbox = types.SimpleNamespace(analysis_inputs=lambda t, **k: set())
    sm.ACTIVE_TOOLBOX = toolbox

    repo.add_element_to_diagram(tgt.diag_id, elem.elem_id)
    assert elem.elem_id not in tgt.elements

    toolbox.analysis_inputs = lambda t, **k: {"Architecture Diagram"}
    repo.add_element_to_diagram(tgt.diag_id, elem.elem_id)
    assert elem.elem_id in tgt.elements

    sm.ACTIVE_TOOLBOX = None
