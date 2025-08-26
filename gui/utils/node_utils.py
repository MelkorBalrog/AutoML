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

"""Utility helpers for node operations."""

from typing import Any


def resolve_original(node: Any) -> Any:
    """Follow a clone chain to locate the primary instance.

    Parameters
    ----------
    node:
        The node whose original primary instance should be returned. The
        object is expected to provide ``is_primary_instance`` and ``original``
        attributes.

    Returns
    -------
    Any
        The primary instance at the root of the clone chain. If ``node`` is
        already a primary instance or lacks an original reference, the same
        object is returned.
    """

    # Walk the clone chain until we find a primary instance.
    while (
        getattr(node, "is_primary_instance", True) is False
        and getattr(node, "original", None) is not None
        and node.original is not node
    ):
        node = node.original
    return node
