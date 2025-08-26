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

"""Tests for :mod:`mainappsrc.services.project_structure.structure_tree_operations_service`."""

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import types
from mainappsrc.services.project_structure import StructureTreeOperationsService
from mainappsrc.core import structure_tree_operations as sto


class TestStructureTreeOperationsService:
    """Group tests for :class:`StructureTreeOperationsService`."""

    def test_app_initializer_uses_service(self):
        code = Path("mainappsrc/core/app_initializer.py").read_text()
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                if any(
                    isinstance(t, ast.Attribute)
                    and t.attr == "structure_tree_operations"
                    and isinstance(t.value, ast.Name)
                    and t.value.id == "app"
                    for t in node.targets
                ):
                    call = node.value
                    if isinstance(call, ast.Call) and getattr(call.func, "id", None) == "StructureTreeOperationsService":
                        break
        else:
            raise AssertionError(
                "AppInitializer.initialize does not assign StructureTreeOperationsService to app.structure_tree_operations"
            )

    def test_move_subtree_delegates(self, monkeypatch):
        captured = {}

        def fake_move_subtree(self, node, dx, dy):
            captured["args"] = (node, dx, dy)

        monkeypatch.setattr(sto.Structure_Tree_Operations, "move_subtree", fake_move_subtree)
        service = StructureTreeOperationsService(app=types.SimpleNamespace())
        sentinel = object()
        service.move_subtree(sentinel, 1, 2)
        assert captured["args"] == (sentinel, 1, 2)
