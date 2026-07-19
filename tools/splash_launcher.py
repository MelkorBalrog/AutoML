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

"""Utility for displaying a splash screen during application start-up."""

import importlib
import sys
from pathlib import Path
import threading
import traceback
import tkinter as tk

from .worker_lifecycle import project_workers
from types import ModuleType
from typing import Callable, Optional

if getattr(sys, "frozen", False):  # pragma: no cover - path handling for executables
    _ROOT = Path(sys._MEIPASS)
else:
    _ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from config.automl_constants import AUTHOR, AUTHOR_EMAIL, AUTHOR_LINKEDIN
except ModuleNotFoundError:  # pragma: no cover - fallback for bundled executables
    AUTHOR = "Miguel Marina"
    AUTHOR_EMAIL = "karel.capek.robotics@gmail.com"
    AUTHOR_LINKEDIN = "https://www.linkedin.com/in/progman32/"
try:
    from mainappsrc.version import VERSION
except ModuleNotFoundError:  # pragma: no cover - fallback when version missing
    VERSION = "0.0.0"


class SplashLauncher:
    """Show the splash screen until the application is ready.

    Parameters
    ----------
    loader:
        Optional callable responsible for initialising the application.  If
        provided it should return the module object whose ``main`` function
        will be invoked once the splash screen closes.  When omitted the
        launcher simply imports :mod:`module_name`.
    module_name:
        Name of the module to import when ``loader`` is not supplied.
    """

    def __init__(
        self,
        loader: Optional[Callable[[], ModuleType]] = None,
        module_name: str = "AutoML",
    ) -> None:
        self.loader = loader
        self.module_name = module_name
        self._module: Optional[ModuleType] = None
        self._owner_thread_id: Optional[int] = None
        self._root_creation_site = ""

    def _load_module(self) -> None:
        """Initialise the application on the splash interpreter's thread."""
        self._assert_owner_thread("load application module", self._root)
        if self.loader:
            self._module = self.loader()
        else:
            self._module = importlib.import_module(self.module_name)

    def _assert_owner_thread(self, operation: str, window: object) -> None:
        """Assert in development builds that centralized Tk work is thread-safe."""
        if not __debug__ or self._owner_thread_id is None:
            return
        current_thread_id = threading.get_ident()
        assert current_thread_id == self._owner_thread_id, (
            "Tk operation attempted outside the interpreter owner thread: "
            f"current_thread={current_thread_id!r}, "
            f"owner_thread={self._owner_thread_id!r}, operation={operation!r}, "
            f"widget={window!r}, creation_site={self._root_creation_site!r}"
        )

    def _close_splash(self) -> None:
        """Close the splash from its interpreter owner thread."""
        self._assert_owner_thread("close splash", self._splash)
        self._splash.close()

    def _destroy_root(self) -> None:
        """Destroy the splash Tcl interpreter from its owner thread."""
        self._assert_owner_thread("destroy splash root", self._root)
        project_workers.assert_stopped()
        self._root.destroy()

    def _launch_headless(self) -> None:
        """Load and launch without a splash when Tk cannot create a root."""
        module = self.loader() if self.loader else importlib.import_module(self.module_name)
        if module and hasattr(module, "main"):
            module.main()

    def _create_splash(self) -> None:
        """Create the splash window and bind owner-thread destruction."""
        from gui.windows.splash_screen import SplashScreen

        self._splash = SplashScreen(
            self._root,
            version=VERSION,
            author=AUTHOR,
            email=AUTHOR_EMAIL,
            linkedin=AUTHOR_LINKEDIN,
            duration=0,
            on_close=self._destroy_root,
        )

    def launch(self) -> None:
        """Display the splash screen and run the application's main function."""
        try:
            self._root = tk.Tk()
        except tk.TclError:
            self._launch_headless()
            return
        self._owner_thread_id = threading.get_ident()
        self._root_creation_site = "".join(traceback.format_stack()[:-1])
        self._assert_owner_thread("withdraw splash root", self._root)
        self._root.withdraw()
        # Defer splash import to avoid circular initialization during package execution.
        self._create_splash()
        self._load_module()
        self._close_splash()
        self._assert_owner_thread("run splash event loop", self._root)
        self._root.mainloop()
        if self._module and hasattr(self._module, "main"):
            self._assert_owner_thread("create application root and run event loop", self._root)
            self._module.main()
