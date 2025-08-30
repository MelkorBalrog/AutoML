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
"""Service API wrappers exposed through the DLL bridge."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from mainappsrc.api import api


class TestConfigServiceApi:
    def test_reload_local_config(self) -> None:
        """The wrapper should forward to the configuration service."""

        assert api.config_service_reload_local_config() is None


class TestAutomlCoreApi:
    def test_reload_local_config(self) -> None:
        """The generic core caller should invoke module functions."""

        assert api.automl_core_call("_reload_local_config") is None
