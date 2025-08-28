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

"""Tests for serialisation of analysis document dataclasses."""

from analysis.models import HazopDoc, HazopEntry, StpaDoc, StpaEntry


class TestAnalysisDocSerialization:
    """Grouped tests for analysis document ``to_dict`` helpers."""

    def test_hazop_doc_to_dict(self) -> None:
        entry = HazopEntry(
            function="F",
            malfunction="M",
            mtype="T",
            scenario="S",
            conditions="C",
            hazard="H",
            safety=True,
            rationale="R",
            covered=False,
            covered_by="",
            component="",
        )
        doc = HazopDoc("HZ1", [entry])
        data = doc.to_dict()
        assert data["name"] == "HZ1"
        assert data["entries"][0]["hazard"] == "H"

    def test_stpa_doc_to_dict(self) -> None:
        entry = StpaEntry(
            action="A",
            not_providing="N",
            providing="P",
            incorrect_timing="T",
            stopped_too_soon="S",
            safety_constraints=["SC"],
        )
        doc = StpaDoc("STPA1", "diag", [entry])
        data = doc.to_dict()
        assert data["diagram"] == "diag"
        assert data["entries"][0]["action"] == "A"
