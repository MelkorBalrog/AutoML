#!/usr/bin/env python3
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

"""Tests for :mod:`gui.utils.node_utils`."""

from gui.utils.node_utils import resolve_original


class DummyNode:
    """Simple stand-in object for testing clone resolution."""

    def __init__(self, is_primary_instance=True, original=None):
        self.is_primary_instance = is_primary_instance
        self.original = original if original is not None else self


def test_resolve_primary_instance_returns_same_node():
    primary = DummyNode(is_primary_instance=True)
    assert resolve_original(primary) is primary


def test_resolve_original_traverses_chain():
    primary = DummyNode(is_primary_instance=True)
    clone1 = DummyNode(is_primary_instance=False, original=primary)
    clone2 = DummyNode(is_primary_instance=False, original=clone1)
    assert resolve_original(clone2) is primary
