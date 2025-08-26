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


from __future__ import annotations

"""Mix-in providing GUI style configuration for :class:`AutoMLApp`."""

from tkinter import ttk

from mainappsrc.subapps.style_subapp import StyleSubApp


class StyleSetupMixin:
    """Configure application styles and themed assets."""

    def setup_style(self, root) -> None:
        """Initialise ttk style and apply the user's theme.

        Parameters
        ----------
        root:
            The Tk root window used by the application.
        """
        self.style = ttk.Style()
        self.style_app = StyleSubApp(root, self.style)
        self.style_app.apply()
        self._btn_imgs = self.style_app.btn_images
        if hasattr(self, "lifecycle_ui"):
            self.lifecycle_ui._init_nav_button_style()
