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
"""Tests for :mod:`DataAccessQueriesService`."""

from types import SimpleNamespace
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import mainappsrc.services.data_access.data_access_queries_service as svc_module


class DummyQueries:
    def __init__(self, app):
        self.app = app
    def sample(self, value):
        return value * 2


def test_service_delegates_attributes(monkeypatch):
    monkeypatch.setattr(svc_module, "DataAccess_Queries", DummyQueries)
    service = svc_module.DataAccessQueriesService(app=SimpleNamespace())
    assert service.sample(5) == 10
