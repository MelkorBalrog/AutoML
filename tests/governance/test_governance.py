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

from mainappsrc.models.gov.governance import RelationshipStatus, can_view_gsn_argumentation
from analysis.safety_management import ALLOWED_USAGE, ALLOWED_ANALYSIS_USAGE


def test_visibility_requires_all_relationships():
    rel = RelationshipStatus(used_by=True, used_after_review=True, used_after_approval=True)
    assert can_view_gsn_argumentation(rel)


def test_visibility_fails_if_any_relationship_missing():
    rel = RelationshipStatus(used_by=True, used_after_review=False, used_after_approval=True)
    assert not can_view_gsn_argumentation(rel)
    rel = RelationshipStatus(used_by=True, used_after_review=True, used_after_approval=False)
    assert not can_view_gsn_argumentation(rel)
    rel = RelationshipStatus(used_by=False, used_after_review=True, used_after_approval=True)
    assert not can_view_gsn_argumentation(rel)


def test_gsn_safety_case_dependency_allowed():
    pair = ("GSN Argumentation", "Safety & Security Case")
    assert pair in ALLOWED_USAGE
    assert pair in ALLOWED_ANALYSIS_USAGE
