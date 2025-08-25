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

"""Event handler mixins for :class:`AutoMLApp`."""

from __future__ import annotations


class EventHandlersMixin:
    """Collection of simple event callback wrappers."""

    def on_treeview_click(self, event):
        self.tree_app.on_treeview_click(self, event)

    def on_analysis_tree_double_click(self, event):
        self.tree_app.on_analysis_tree_double_click(self, event)

    def on_analysis_tree_right_click(self, event):
        self.tree_app.on_analysis_tree_right_click(self, event)

    def on_analysis_tree_select(self, _event):
        self.tree_app.on_analysis_tree_select(self, _event)

