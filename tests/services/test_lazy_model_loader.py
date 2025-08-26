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
"""Tests for lazy model loading service."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mainappsrc.services.lazy_model_loader import LazyModelLoader
from mainappsrc.models.sysml.sysml_repository import SysMLRepository


class DummyApp:
    def __init__(self) -> None:
        self.project_properties: dict = {}
        self.gsn_modules = []
        self.top_events = []
        self.cta_events = []
        self.paa_events = []
        self.root_node = None

    def _load_project_properties(self, data: dict) -> None:  # pragma: no cover - simple
        self.project_properties.update(data.get("project_properties", {}))

    def _load_fault_tree_events(self, data: dict, ensure_root: bool) -> None:  # pragma: no cover - simple
        pass


class TestLazyModelLoader:
    def setup_method(self) -> None:
        SysMLRepository.reset_instance()
        self.data = {
            "project_properties": {"pdf_report_name": "X"},
            "sysml_repository": {
                "elements": [{"elem_id": "E1", "elem_type": "Block"}],
                "relationships": [],
                "diagrams": [],
                "element_diagrams": {},
            },
        }
        self.app = DummyApp()
        self.loader = LazyModelLoader(self.app, self.data)
        self.loader.load_core()

    def test_repository_loaded_on_demand(self) -> None:
        repo = SysMLRepository.get_instance()
        assert len(repo.elements) == 1  # root package only
        self.loader.load_section("sysml_repository")
        assert len(repo.elements) == 2

    def test_repository_unload(self) -> None:
        repo = SysMLRepository.get_instance()
        self.loader.load_section("sysml_repository")
        assert len(repo.elements) == 2
        self.loader.unload_section("sysml_repository")
        repo = SysMLRepository.get_instance()
        assert len(repo.elements) == 1
