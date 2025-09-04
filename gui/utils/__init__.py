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

"""Utility helpers exposed for backward-compatible imports.

This package re-exports commonly used utilities so that modules can simply
``import gui.utils`` and access members such as :mod:`logger` or
``DIALOG_BG_COLOR``.  Keeping these aliases here preserves compatibility with
older code that expected these objects to live directly under
``gui.utils``.
"""

# The logging helper is implemented in ``logger.py`` but we import it here so
# ``from gui.utils import logger`` continues to work.
from . import logger  # noqa: F401
from .node_utils import resolve_original  # noqa: F401
from .detached_window import DetachedWindow  # noqa: F401
from .widget_transfer_manager import WidgetTransferManager  # noqa: F401

# Treeview convenience helpers live in the top level ``gui`` package. Importing
# them here preserves backward compatibility for modules that relied on
# ``from gui.utils import add_treeview_scrollbars``.
# ``add_treeview_scrollbars`` is defined in the top-level ``gui`` package. To
# avoid circular import issues during package initialisation we lazily resolve
# the real implementation on first use and forward the call.
def add_treeview_scrollbars(*args, **kwargs):
    """Forward to :func:`gui.add_treeview_scrollbars` for legacy imports."""

    from .. import add_treeview_scrollbars as _impl

    return _impl(*args, **kwargs)


# Default background colour used by dialog windows across the application.
# This constant is defined here to allow both ``from gui.utils import
# DIALOG_BG_COLOR`` and ``from gui import DIALOG_BG_COLOR`` (which imports it
# via ``gui.__init__``).
DIALOG_BG_COLOR = "#A9BCE2"


__all__ = [
    "logger",
    "DIALOG_BG_COLOR",
    "add_treeview_scrollbars",
    "resolve_original",
    "DetachedWindow",
    "WidgetTransferManager",
]
