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

"""Thread-safe Tk call helper."""

from __future__ import annotations

import threading
import tkinter as tk
from typing import Any, Callable


def run_on_main_thread(func: Callable[..., Any], *args: Any, root: tk.Misc | None = None) -> Any:
    """Execute *func* on Tk's main thread and return its result.

    If called from the main thread the function runs immediately. Otherwise the
    call is scheduled via ``root.after`` and the invoking thread blocks until
    completion using a :class:`threading.Event`.

    Parameters
    ----------
    func:
        Callable to execute on the main thread.
    *args:
        Positional arguments passed to *func*.
    root:
        Optional Tk root. If omitted the default root is used.
    """
    if threading.current_thread() is threading.main_thread():
        return func(*args)

    if root is None:
        root = tk._default_root  # type: ignore[attr-defined]
    if root is None:
        raise RuntimeError("Tk root is not available")

    result: dict[str, Any] = {}
    done = threading.Event()

    def _run() -> None:
        try:
            result["value"] = func(*args)
        finally:
            done.set()

    root.after(0, _run)
    done.wait()
    return result.get("value")


__all__ = ["run_on_main_thread"]
