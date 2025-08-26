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

"""Unit tests for :class:`UISetupService`."""

import tkinter as tk
import pytest

from mainappsrc.services.ui import UISetupService
from mainappsrc.core.app_lifecycle_ui import AppLifecycleUI


class _DummyApp:
    pass


def test_ui_setup_service_initializes_icons():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk not available")
    app = _DummyApp()
    service = UISetupService(app, root)
    service.initialize(root)
    try:
        assert isinstance(service.lifecycle_ui, AppLifecycleUI)
        assert hasattr(service, "pkg_icon")
    finally:
        root.destroy()
