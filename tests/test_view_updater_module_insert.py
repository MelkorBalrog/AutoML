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

"""Tests for :mod:`mainappsrc.core.view_updater` module helpers."""

from mainappsrc.core.view_updater import ViewUpdater


class _DummyTree:
    """Minimal tree stub tracking insert calls."""

    def __init__(self):
        self.called = False

    def exists(self, item):
        return False

    def insert(self, parent, index, **kwargs):
        self.called = True


class _DummyModule:
    name = "mod"
    modules = []
    diagrams = []


class _DummyApp:
    pkg_icon = None
    gsn_diagram_icon = None


def test_insert_module_missing_parent_ignored():
    """_insert_module returns early when parent item is absent."""

    updater = ViewUpdater(_DummyApp())
    tree = _DummyTree()
    updater._insert_module(tree, _DummyModule(), "missing", {})
    assert not tree.called
