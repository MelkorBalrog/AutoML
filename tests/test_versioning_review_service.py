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

"""Tests for :mod:`VersioningReviewService` grouped by operation type."""

import types
from mainappsrc.services.versioning import VersioningReviewService


class TestVersionOperations:
    """Ensure version management calls are delegated."""

    def test_add_version_delegates(self, monkeypatch):
        called = {}

        def fake_add(self):
            called["flag"] = True

        review_mgr = types.SimpleNamespace(add_version=fake_add)
        svc = VersioningReviewService(types.SimpleNamespace(review_manager=review_mgr))
        svc.add_version()
        assert called["flag"] is True

    def test_compare_versions_delegates(self, monkeypatch):
        called = {}

        def fake_compare(self):
            called["flag"] = True

        review_mgr = types.SimpleNamespace(compare_versions=fake_compare)
        svc = VersioningReviewService(types.SimpleNamespace(review_manager=review_mgr))
        svc.compare_versions()
        assert called["flag"] is True


class TestReviewOperations:
    """Ensure review helper calls are delegated."""

    def test_open_review_toolbox_delegates(self):
        called = {}

        def fake_open(self):
            called["flag"] = True

        review_mgr = types.SimpleNamespace(open_review_toolbox=fake_open)
        svc = VersioningReviewService(types.SimpleNamespace(review_manager=review_mgr))
        svc.open_review_toolbox()
        assert called["flag"] is True
