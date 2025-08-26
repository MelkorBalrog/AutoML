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
"""Tests for :mod:`mainappsrc.services.reporting`."""

from types import SimpleNamespace

import pytest

from mainappsrc.services.reporting import ReportingExportService


class DummyExporter:
    def __init__(self, app):
        self.app = app

    def generate_pdf_report(self):
        return "pdf"

    def generate_report(self):
        return "report"

    def extra(self):
        return "extra"


@pytest.fixture
def patch_exporter(monkeypatch):
    monkeypatch.setattr(
        "mainappsrc.core.reporting_export.Reporting_Export", DummyExporter
    )


def test_service_delegates_pdf_generation(patch_exporter):
    service = ReportingExportService(SimpleNamespace())
    assert service.generate_pdf_report() == "pdf"
    assert service.generate_report() == "report"
    assert service.extra() == "extra"
