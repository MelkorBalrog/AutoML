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
"""Service wrapper for :mod:`mainappsrc.core.undo_manager`."""

from __future__ import annotations

from typing import Any

from mainappsrc.core.undo_manager import UndoRedoManager


class UndoRedoService:
    """Expose :class:`UndoRedoManager` as a service.

    This thin wrapper enables dependency injection of the undo/redo
    functionality and provides a stable service façade for the
    application. Attribute access is delegated to the underlying manager
    so existing calls continue to work unchanged.
    """

    def __init__(self, app: Any) -> None:  # pragma: no cover - simple container
        self._manager = UndoRedoManager(app)

    def __getattr__(self, name: str):  # pragma: no cover - delegation
        return getattr(self._manager, name)


__all__ = ["UndoRedoService"]
