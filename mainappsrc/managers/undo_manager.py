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

"""Centralised undo/redo state management."""

from __future__ import annotations

import json
from typing import Any

from mainappsrc.models.sysml.sysml_repository import SysMLRepository


class UndoRedoManager:
    """Manage undo/redo stacks for :class:`AutoMLApp`."""

    def __init__(self, app: Any):
        self.app = app
        self._undo_stack: list[dict] = []
        self._redo_stack: list[dict] = []
        self._last_move_base: dict | None = None
        self._move_run_length = 0

    # ------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------
    def _strip_object_positions(self, data: dict) -> dict:
        """Return a copy of *data* without concrete object positions."""

        cleaned = json.loads(json.dumps(data))

        def scrub(obj: Any) -> None:
            if isinstance(obj, dict):
                for field in ("x", "y", "modified", "modified_by", "modified_by_email"):
                    obj.pop(field, None)
                for value in obj.values():
                    scrub(value)
            elif isinstance(obj, list):
                for item in obj:
                    scrub(item)

        scrub(cleaned)
        return cleaned

    # ------------------------------------------------------------
    # State recording
    # ------------------------------------------------------------
    def push_undo_state(self, strategy: str = "v4", sync_repo: bool = True) -> None:
        """Save the current model state for undo operations."""

        repo = SysMLRepository.get_instance()
        if sync_repo:
            repo.push_undo_state(strategy=strategy, sync_app=False)
        try:
            state = self.app.export_model_data(include_versions=False)
            stripped = self._strip_object_positions(state)
        except AttributeError:
            state = {}
            stripped = {}

        handler = getattr(self, f"_push_undo_state_{strategy}", self._push_undo_state_v1)
        changed = handler(state, stripped)

        if changed and len(self._undo_stack) > 20:
            self._undo_stack.pop(0)
        if changed:
            self._redo_stack.clear()

    def _push_undo_state_v1(self, state: dict, stripped: dict) -> bool:
        if self._undo_stack:
            last = self._undo_stack[-1]
            if last == state:
                return False
            if self._strip_object_positions(last) == stripped:
                if (
                    len(self._undo_stack) >= 2
                    and self._strip_object_positions(self._undo_stack[-2]) == stripped
                ):
                    self._undo_stack[-1] = state
                    return True
                self._undo_stack.append(state)
                return True
        else:
            self._undo_stack.append(state)
            return True

        self._undo_stack.append(state)
        return True

    def _push_undo_state_v2(self, state: dict, stripped: dict) -> bool:
        if self._undo_stack and self._undo_stack[-1] == state:
            return False
        if self._undo_stack and self._strip_object_positions(self._undo_stack[-1]) == stripped:
            if self._last_move_base == stripped:
                self._undo_stack[-1] = state
            else:
                self._undo_stack.append(state)
                self._last_move_base = stripped
            return True
        self._last_move_base = None
        self._undo_stack.append(state)
        return True

    def _push_undo_state_v3(self, state: dict, stripped: dict) -> bool:
        if self._undo_stack and self._undo_stack[-1] == state:
            return False
        if self._undo_stack and self._strip_object_positions(self._undo_stack[-1]) == stripped:
            if self._move_run_length:
                self._undo_stack[-1] = state
            else:
                self._undo_stack.append(state)
            self._move_run_length += 1
            return True
        self._move_run_length = 0
        self._undo_stack.append(state)
        return True

    def _push_undo_state_v4(self, state: dict, stripped: dict) -> bool:
        if self._undo_stack and self._undo_stack[-1] == state:
            return False
        self._undo_stack.append(state)
        if len(self._undo_stack) >= 3:
            s1 = self._strip_object_positions(self._undo_stack[-3])
            s2 = self._strip_object_positions(self._undo_stack[-2])
            if s1 == s2 == stripped:
                self._undo_stack.pop(-2)
        return True

    # ------------------------------------------------------------
    # Undo/Redo public interface
    # ------------------------------------------------------------
    def undo(self, strategy: str = "v4") -> None:
        """Revert the repository and model data to the previous state."""

        repo = SysMLRepository.get_instance()
        handler = getattr(self, f"_undo_{strategy}", self._undo_v1)
        changed = handler(repo)
        if not changed:
            return
        for tab in getattr(self.app, "diagram_tabs", {}).values():
            for child in tab.winfo_children():
                if hasattr(child, "refresh_from_repository"):
                    child.refresh_from_repository()
        self.app.refresh_all()

    def redo(self, strategy: str = "v4") -> None:
        """Reapply a state previously reverted with :meth:`undo`."""

        repo = SysMLRepository.get_instance()
        handler = getattr(self, f"_redo_{strategy}", self._redo_v1)
        changed = handler(repo)
        if not changed:
            return
        for tab in getattr(self.app, "diagram_tabs", {}).values():
            for child in tab.winfo_children():
                if hasattr(child, "refresh_from_repository"):
                    child.refresh_from_repository()
        self.app.refresh_all()

    def clear_history(self) -> None:
        """Remove all undo and redo history."""

        self._undo_stack.clear()
        self._redo_stack.clear()
        repo = SysMLRepository.get_instance()
        getattr(repo, "_undo_stack", []).clear()
        getattr(repo, "_redo_stack", []).clear()

    # ------------------------------------------------------------
    # Undo variants
    # ------------------------------------------------------------
    def _undo_v1(self, repo: Any) -> bool:
        if not self._undo_stack:
            return False
        current = self.app.export_model_data(include_versions=False)
        repo.undo(strategy="v1")
        if self._undo_stack and self._undo_stack[-1] == current:
            self._undo_stack.pop()
            if not self._undo_stack:
                return False
        state = self._undo_stack.pop()
        self._redo_stack.append(current)
        if len(self._redo_stack) > 20:
            self._redo_stack.pop(0)
        self.app.apply_model_data(state)
        return True

    def _undo_v2(self, repo: Any) -> bool:
        if not self._undo_stack:
            return False
        current = self.app.export_model_data(include_versions=False)
        repo.undo(strategy="v2")
        if self._undo_stack and self._undo_stack[-1] == current:
            self._undo_stack.pop()
            if not self._undo_stack:
                return False
        state = self._undo_stack.pop()
        self._redo_stack.append(current)
        if len(self._redo_stack) > 20:
            self._redo_stack.pop(0)
        self.app.apply_model_data(state)
        return True

    def _undo_v3(self, repo: Any) -> bool:
        if not self._undo_stack:
            return False
        current = self.app.export_model_data(include_versions=False)
        repo.undo(strategy="v3")
        if self._undo_stack and self._undo_stack[-1] == current:
            self._undo_stack.pop()
            if not self._undo_stack:
                return False
        state = self._undo_stack.pop()
        self._redo_stack.append(current)
        if len(self._redo_stack) > 20:
            self._redo_stack.pop(0)
        self.app.apply_model_data(state)
        return True

    def _undo_v4(self, repo: Any) -> bool:
        if not self._undo_stack:
            return False
        current = self.app.export_model_data(include_versions=False)
        repo.undo(strategy="v4")
        if self._undo_stack and self._undo_stack[-1] == current:
            self._undo_stack.pop()
            if not self._undo_stack:
                self._redo_stack.append(current)
                if len(self._redo_stack) > 20:
                    self._redo_stack.pop(0)
                return True
        state = self._undo_stack.pop()
        self._redo_stack.append(current)
        if len(self._redo_stack) > 20:
            self._redo_stack.pop(0)
        self.app.apply_model_data(state)
        return True

    # ------------------------------------------------------------
    # Redo variants
    # ------------------------------------------------------------
    def _redo_v1(self, repo: Any) -> bool:
        if not self._redo_stack:
            return False
        current = self.app.export_model_data(include_versions=False)
        repo.redo(strategy="v1")
        state = self._redo_stack.pop()
        self._undo_stack.append(current)
        if len(self._undo_stack) > 20:
            self._undo_stack.pop(0)
        self.app.apply_model_data(state)
        return True

    def _redo_v2(self, repo: Any) -> bool:
        if not self._redo_stack:
            return False
        current = self.app.export_model_data(include_versions=False)
        repo.redo(strategy="v2")
        state = self._redo_stack.pop()
        self._undo_stack.append(current)
        if len(self._undo_stack) > 20:
            self._undo_stack.pop(0)
        self.app.apply_model_data(state)
        return True

    def _redo_v3(self, repo: Any) -> bool:
        if not self._redo_stack:
            return False
        current = self.app.export_model_data(include_versions=False)
        repo.redo(strategy="v3")
        state = self._redo_stack.pop()
        self._undo_stack.append(current)
        if len(self._undo_stack) > 20:
            self._undo_stack.pop(0)
        self.app.apply_model_data(state)
        return True

    def _redo_v4(self, repo: Any) -> bool:
        if not self._redo_stack:
            return False
        current = self.app.export_model_data(include_versions=False)
        repo.redo(strategy="v4")
        state = self._redo_stack.pop()
        self._undo_stack.append(current)
        if len(self._undo_stack) > 20:
            self._undo_stack.pop(0)
        self.app.apply_model_data(state)
        return True
