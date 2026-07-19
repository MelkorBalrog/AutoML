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

# Ensure repository root is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.crash_report_logger import (
    CrashLoggerV3,
    CrashLoggerV4,
    crash_handler_v1,
    crash_handler_v2,
)


def _raise(exception):
    try:
        raise exception
    except Exception:
        return sys.exc_info()


def test_crash_handler_v1(tmp_path):
    path = tmp_path / "v1.log"
    exc_info = _raise(ValueError("boom"))
    crash_handler_v1(*exc_info, path=path)
    assert path.exists()
    assert "ValueError: boom" in path.read_text()


def test_crash_handler_v2(tmp_path):
    path = tmp_path / "v2.log"
    exc_info = _raise(RuntimeError("oops"))
    crash_handler_v2(*exc_info, path=path)
    assert path.exists()
    assert "RuntimeError: oops" in path.read_text()


def test_crash_handler_v3(tmp_path):
    path = tmp_path / "v3.log"
    handler = CrashLoggerV3(path)
    handler(*_raise(KeyError("missing")))
    assert path.exists()
    assert "KeyError: 'missing'" in path.read_text()


def test_crash_handler_v4(tmp_path):
    directory = tmp_path / "logs"
    handler = CrashLoggerV4(directory)
    handler(*_raise(Exception("crash")))
    files = list(directory.glob("crash_*.log"))
    assert files, "log file not created"
    assert "Exception: crash" in files[0].read_text()


class TestSynchronousHealthReporting:
    """Grouped checks for thread-free crash health reporting."""

    def test_unhealthy_report_is_recorded(self):
        from tools.crash_report_logger import SynchronousHealthReporter

        reporter = SynchronousHealthReporter()
        report = reporter.report("shutdown", healthy=False, detail="failure")
        assert report.healthy is False
        assert reporter.reports == [report]
