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

import sys
from pathlib import Path
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))


def test_governance_elements_toolbox_excludes_select():
    arch_path = Path(__file__).resolve().parents[1] / "gui" / "architecture.py"
    text = arch_path.read_text()
    marker = "# Create toolbox for additional governance elements grouped by class"
    if marker not in text:
        pytest.skip("Governance elements toolbox markers not found")
    text = text.split(marker, 1)[1]
    text = text.split("# Repack toolbox to include selector", 1)[0]
    assert 'text="Select"' not in text

