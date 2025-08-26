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

"""Tests for :class:`SafetyUIService`."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mainappsrc.services.safety_ui import SafetyUIService
from mainappsrc.core.automl_core import AutoMLApp


class _DummyFmeda:
    def __init__(self):
        self.called = False

    def show_fmeda_list(self):
        self.called = True


class _DummyApp:
    def __init__(self):
        self.fmeda_manager = _DummyFmeda()


def test_service_delegates_calls():
    app = _DummyApp()
    service = SafetyUIService(app)
    service.show_fmeda_list()
    assert app.fmeda_manager.called


def test_automlapp_attribute_delegation():
    app = AutoMLApp.__new__(AutoMLApp)
    app.ui_service = type("_UI", (), {"lifecycle_ui": object()})()
    app.safety_ui_service = type("_S", (), {"demo": lambda self: "ok"})()
    assert app.demo() == "ok"
