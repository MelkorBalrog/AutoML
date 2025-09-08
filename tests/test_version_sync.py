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

from __future__ import annotations

"""Regression tests ensuring version consistency."""


import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mainappsrc.version import VERSION


def _readme_version() -> str:
    """Extract the version string from the README."""
    for line in ROOT.joinpath("README.md").read_text(encoding="utf-8").splitlines():
        stripped = line.strip().lower()
        if stripped.startswith("version:"):
            return stripped.split(":", maxsplit=1)[1].strip()
    raise AssertionError("version line not found")


def test_readme_matches_version() -> None:
    """README version must match the source version."""

    assert _readme_version() == VERSION


def test_cli_reports_same_version() -> None:
    """The ``--version`` flag should report the package version."""

    result = subprocess.run(
        [sys.executable, str(ROOT / "AutoML.py"), "--version"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == VERSION


