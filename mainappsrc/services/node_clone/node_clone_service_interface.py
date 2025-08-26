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
"""Interface wrapping core :class:`NodeCloneService`."""

from __future__ import annotations

from typing import Optional

from mainappsrc.core.node_clone_service import NodeCloneService


class NodeCloneServiceInterface:
    """Thin wrapper exposing :class:`NodeCloneService` as a service.

    The interface isolates callers from the concrete implementation in the
    core module.  It simply delegates to an internal
    :class:`NodeCloneService` instance.
    """

    def __init__(self, service: Optional[NodeCloneService] = None) -> None:
        self._service = service or NodeCloneService()

    def clone_node_preserving_id(self, node, parent=None):
        """Delegate cloning to the underlying service."""
        return self._service.clone_node_preserving_id(node, parent)


__all__ = ["NodeCloneServiceInterface"]
