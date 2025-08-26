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
"""Wrapper service providing PDF and HTML report generation."""

from __future__ import annotations

from mainappsrc.core.reporting_export import Reporting_Export


class ReportingExportService:
    """Facade around :class:`~mainappsrc.core.reporting_export.Reporting_Export`.

    The service delegates to the underlying exporter while exposing a
    concise surface for generating PDF and HTML reports.  Other helper
    methods are transparently forwarded via ``__getattr__`` so existing
    callers continue to function.
    """

    def __init__(self, app: object) -> None:
        self._exporter = Reporting_Export(app)

    # ------------------------------------------------------------------
    # Focused report generation helpers
    def _generate_pdf_report(self):
        """Generate raw PDF data using the underlying exporter."""
        return self._exporter._generate_pdf_report()

    def generate_pdf_report(self):
        """Create a PDF report and return the output path."""
        return self._exporter.generate_pdf_report()

    def generate_report(self):
        """Create an HTML report and return its path."""
        return self._exporter.generate_report()

    def build_html_report(self):
        """Build HTML report content without writing to disk."""
        return self._exporter.build_html_report()

    # ------------------------------------------------------------------
    # Delegate any other attribute access to the wrapped exporter
    def __getattr__(self, item):  # pragma: no cover - simple delegation
        return getattr(self._exporter, item)


__all__ = ["ReportingExportService"]
