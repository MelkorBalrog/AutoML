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

from mainappsrc.ui.ui_setup import UISetupMixin


def test_enable_paa_actions_includes_gate():
    called = []

    class DummyMenu:
        def entryconfig(self, index, state):
            called.append(index)

    obj = type("O", (UISetupMixin,), {})()
    obj.paa_menu = DummyMenu()
    obj._paa_menu_indices = {"add_confidence": 0, "add_robustness": 1, "add_gate": 2}
    obj.enable_paa_actions(True)

    assert 2 in called
