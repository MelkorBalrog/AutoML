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
"""Tests for :mod:`ViewUpdateService`."""

import types
import tkinter as tk
import pytest

from mainappsrc.services.view import ViewUpdateService


def test_service_delegates_to_view_updater(monkeypatch):
    """Service should forward calls to the underlying ``ViewUpdater``."""

    calls = []

    class DummyUpdater:
        def __init__(self, app):
            pass

        def update_views(self):
            calls.append("update")

    monkeypatch.setattr(
        "mainappsrc.services.view.view_update_service.ViewUpdater", DummyUpdater
    )

    app = types.SimpleNamespace()
    service = ViewUpdateService(app)
    service.update_views()

    assert calls == ["update"]


def test_automl_app_uses_view_update_service(monkeypatch):
    """``AutoMLApp`` should route view refreshes through the service."""

    from AutoML import AutoMLApp
    from mainappsrc.core import automl_core as automl_module

    calls = []

    class DummyService:
        def __init__(self, app):
            calls.append("init")

        def update_views(self):
            calls.append("update")

    monkeypatch.setattr(automl_module, "ViewUpdateService", DummyService)

    try:
        root = tk.Tk()
        root.withdraw()
    except tk.TclError:
        pytest.skip("Tk not available")

    app = AutoMLApp(root)
    app.update_views()

    assert calls == ["init", "update"]
    root.destroy()
