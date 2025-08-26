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
"""Lazy loading utilities for AutoML project data."""

from __future__ import annotations

from typing import Any, Callable, Dict, Set

from mainappsrc.models.sysml.sysml_repository import SysMLRepository
from analysis.models import global_requirements, ensure_requirement_defaults
from mainappsrc.models.gsn import GSNModule


class LazyModelLoader:
    """Load and unload project sections on demand."""

    def __init__(self, app: Any, data: Dict[str, Any], ensure_root: bool = True) -> None:
        self.app = app
        self._data = data
        self._ensure_root = ensure_root
        self._loaded: Set[str] = set()

    # ------------------------------------------------------------------
    def load_core(self) -> None:
        """Load project properties without heavy sections."""
        self.app._load_project_properties(self._data)

    # ------------------------------------------------------------------
    def load_section(self, name: str) -> None:
        """Load a named section if not already loaded."""
        if name in self._loaded:
            return
        loader = getattr(self, f"_load_{name}", None)
        if loader is None:
            raise KeyError(name)
        loader()
        self._loaded.add(name)

    # ------------------------------------------------------------------
    def unload_section(self, name: str) -> None:
        """Unload a previously loaded section."""
        if name not in self._loaded:
            return
        deleter = getattr(self, f"_unload_{name}", None)
        if deleter:
            deleter()
        self._loaded.discard(name)

    # ------------------------------------------------------------------
    def load_all(self) -> None:
        """Load all known sections."""
        for name in ("sysml_repository", "fault_tree_events", "global_requirements", "gsn_modules"):
            try:
                self.load_section(name)
            except KeyError:
                continue

    # Section loaders ---------------------------------------------------
    def _load_sysml_repository(self) -> None:
        repo_data = self._data.get("sysml_repository")
        if repo_data:
            repo = SysMLRepository.get_instance()
            repo.from_dict(repo_data)

    def _unload_sysml_repository(self) -> None:
        SysMLRepository.reset_instance()

    def _load_fault_tree_events(self) -> None:
        app = self.app
        app._load_fault_tree_events(self._data, self._ensure_root)

    def _unload_fault_tree_events(self) -> None:
        app = self.app
        app.top_events = []
        app.cta_events = []
        app.paa_events = []
        app.root_node = None

    def _load_global_requirements(self) -> None:
        global_requirements.clear()
        for rid, req in self._data.get("global_requirements", {}).items():
            global_requirements[rid] = ensure_requirement_defaults(req)

    def _unload_global_requirements(self) -> None:
        global_requirements.clear()

    def _load_gsn_modules(self) -> None:
        self.app.gsn_modules = [GSNModule.from_dict(m) for m in self._data.get("gsn_modules", [])]

    def _unload_gsn_modules(self) -> None:
        self.app.gsn_modules = []
