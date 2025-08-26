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

"""Tests for the syncing service wrapper."""

from __future__ import annotations

from mainappsrc.services.syncing import SyncingAndIdsService
from mainappsrc.core import syncing_and_ids


def test_syncing_service_delegates(monkeypatch):
    """Service should forward attribute access to underlying implementation."""

    called = {}

    def dummy(self, value):
        called["hit"] = value
        return 123

    monkeypatch.setattr(syncing_and_ids.Syncing_And_IDs, "dummy", dummy, raising=False)

    service = SyncingAndIdsService(object())
    assert service.dummy(5) == 123
    assert called["hit"] == 5

