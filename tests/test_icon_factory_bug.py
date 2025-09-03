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

import gui.utils.icon_factory as icon_factory


def test_bug_icon_coords_non_negative(monkeypatch):
    size = 16

    class DummyImage:
        def __init__(self, *args, **kwargs):
            self.coords = []

        def put(self, color, pos=None, to=None):
            if pos is not None:
                self.coords.append(pos)
            elif to is not None:
                x1, y1, x2, y2 = to
                for x in range(x1, x2):
                    for y in range(y1, y2):
                        self.coords.append((x, y))

    monkeypatch.setattr(icon_factory.tk, "PhotoImage", DummyImage)
    img = icon_factory.create_icon("bug", "#ff0000", size=size)
    assert all(0 <= x < size and 0 <= y < size for x, y in img.coords)
