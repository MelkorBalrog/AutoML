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

"""Service orchestrating user-interface setup helpers."""

from __future__ import annotations

from ...ui.ui_setup import UISetupMixin
from gui.styles.style_setup_mixin import StyleSetupMixin
from ...core.icon_setup_mixin import IconSetupMixin
from ...ui.app_lifecycle_ui import AppLifecycleUI


class UISetupService(UISetupMixin, StyleSetupMixin, IconSetupMixin):
    """Facade coordinating UI setup and lifecycle utilities."""

    def __init__(self, app: object, root) -> None:
        self.app = app
        self.lifecycle_ui = AppLifecycleUI(app, root)

    def __getattr__(self, name):  # pragma: no cover - simple delegation
        return getattr(self.app, name)

    def initialize(self, root) -> None:
        """Run style and icon setup."""
        self.setup_style(root)
        self.setup_icons()


__all__ = ["UISetupService"]
