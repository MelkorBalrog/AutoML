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
"""Tests for the validation consistency service."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

# Ensure project root on path for direct module imports when running from the
# tests directory.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mainappsrc.services.validation import ValidationConsistencyService


class TestServiceInitialization:
    def test_service_initialised_during_setup(self) -> None:
        """AutoML service setup must assign the validation service."""
        code = (ROOT / "mainappsrc/core/service_init_mixin.py").read_text()
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                if any(
                    isinstance(t, ast.Attribute)
                    and t.attr == "validation_consistency"
                    and isinstance(t.value, ast.Name)
                    and t.value.id == "self"
                    for t in node.targets
                ):
                    if (
                        isinstance(node.value, ast.Call)
                        and getattr(node.value.func, "id", None)
                        == "ValidationConsistencyService"
                    ):
                        break
        else:  # pragma: no cover - assertion message only
            raise AssertionError(
                "ServiceInitMixin.setup_services does not assign ValidationConsistencyService"
            )


class TestValidateFloat:
    def setup_method(self) -> None:
        self.service = ValidationConsistencyService(object())

    def test_accepts_numeric_strings(self) -> None:
        assert self.service.validate_float("1.5") is True

    def test_rejects_invalid_strings(self) -> None:
        assert self.service.validate_float("abc") is False
