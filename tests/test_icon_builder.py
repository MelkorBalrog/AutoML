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

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import tools.icon_builder as ib


def test_all_strategies(tmp_path):
    strategies = ["v1", "v2", "v3", "v4"]
    for strat in strategies:
        out = tmp_path / f"icon_{strat}.ico"
        ib.build_icon(out, strat)
        assert out.exists()
        assert out.stat().st_size > 0
        with out.open("rb") as f:
            header = f.read(8)
        assert header.startswith(b"\x00\x00")
        assert header[6] == header[7] == 128


def test_custom_scale(tmp_path):
    out = tmp_path / "icon_custom.ico"
    ib.build_icon(out, "v4", scale=2)
    with out.open("rb") as f:
        data = f.read(8)
    assert data[6] == data[7] == 64
