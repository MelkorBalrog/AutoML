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

"""Tests for the :mod:`mainappsrc.services.editing.editors_service` module."""

from __future__ import annotations

from mainappsrc.services.editing.editors_service import EditorsService
from mainappsrc.core import editors


def test_editors_service_delegates(monkeypatch):
    """EditorsService forwards attribute access to underlying Editors instance."""

    called = {}

    def dummy(self):
        called["hit"] = True
        return 42

    monkeypatch.setattr(editors.Editors, "dummy", dummy)

    service = EditorsService(object())
    assert service.dummy() == 42
    assert called["hit"]
