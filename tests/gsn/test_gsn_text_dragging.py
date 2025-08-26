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

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from gui.drawing_helper import GSNDrawingHelper


class DummyCanvas:
    def __init__(self):
        self.text_calls = []

    def create_rectangle(self, *a, **k):
        pass

    def create_polygon(self, *a, **k):
        pass

    def create_oval(self, *a, **k):
        pass

    def create_line(self, *a, **k):
        pass

    def create_text(self, *a, **k):
        self.text_calls.append(k)


def test_goal_text_has_obj_id_tag(monkeypatch):
    canvas = DummyCanvas()
    helper = GSNDrawingHelper()

    class DummyFont:
        def measure(self, _):
            return 10

        def metrics(self, _):
            return 10

    monkeypatch.setattr("gui.drawing_helper.tkFont.Font", lambda *a, **k: DummyFont())

    helper.draw_goal_shape(canvas, 0, 0, text="Goal", obj_id="nid")
    assert any(call.get("tags") == ("nid",) for call in canvas.text_calls)
