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
"""Tests for :mod:`AppInitializationService`."""

import types
import tkinter as tk
import pytest

from mainappsrc.services.app_init import AppInitializationService


def test_service_initialises_managers(monkeypatch):
    """Service should create project properties and clipboard managers."""

    class DummyPPM:
        pass

    class DummyDCM:
        pass

    class DummyInitializer:
        def __init__(self, app):
            self.app = app

        def initialize(self):
            self.app.project_properties = {}

    monkeypatch.setattr(
        "mainappsrc.services.app_init.app_initialization_service.AppInitializer",
        DummyInitializer,
    )
    monkeypatch.setattr(
        "mainappsrc.services.app_init.app_initialization_service.ProjectPropertiesManager",
        lambda props: DummyPPM(),
    )
    monkeypatch.setattr(
        "mainappsrc.services.app_init.app_initialization_service.DiagramClipboardManager",
        lambda app: DummyDCM(),
    )

    app = types.SimpleNamespace()
    service = AppInitializationService(app)
    service.initialize()

    assert isinstance(service.project_properties_manager, DummyPPM)
    assert isinstance(service.diagram_clipboard_manager, DummyDCM)


def test_automl_app_uses_service(monkeypatch):
    """AutoMLApp should rely on the initialisation service."""

    from AutoML import AutoMLApp
    from mainappsrc.core import automl_core as automl_module

    calls = []

    class DummyService:
        def __init__(self, app):
            calls.append("init")
            self.app = app
            self.project_properties_manager = object()
            self.diagram_clipboard_manager = object()

        def initialize(self):
            calls.append("initialize")
            self.app.project_properties_manager = self.project_properties_manager
            self.app.diagram_clipboard = self.diagram_clipboard_manager

    monkeypatch.setattr(automl_module, "AppInitializationService", DummyService)

    try:
        root = tk.Tk()
        root.withdraw()
    except tk.TclError:
        pytest.skip("Tk not available")

    app = AutoMLApp(root)
    assert calls == ["init", "initialize"]
    assert hasattr(app, "project_properties_manager")
    assert hasattr(app, "diagram_clipboard")
    root.destroy()
