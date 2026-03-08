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
import tkinter as tk
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
    post_delay:
        Milliseconds to keep the splash screen visible after initialisation
        completes.
    """

    def __init__(
        self,
        loader: Optional[Callable[[], ModuleType]] = None,
        module_name: str = "AutoML",
        post_delay: int = 0,
    ) -> None:
        self.loader = loader
        self.module_name = module_name
        self.post_delay = post_delay
        self._module: Optional[ModuleType] = None

    def _load_module(self) -> None:
        """Initialise the application in a background thread."""
        if self.loader:
            self._module = self.loader()
        else:
            self._module = importlib.import_module(self.module_name)
        # Once loading is complete, close the splash screen on the main thread
        self._root.after(self.post_delay, self._splash.close)

    def launch(self) -> None:
        """Display the splash screen and run the application's main function."""
        try:
            self._root = tk.Tk()
        except tk.TclError:
            # Headless environment; load module directly without splash
            module = self.loader() if self.loader else importlib.import_module(self.module_name)
            if module and hasattr(module, "main"):
                module.main()
            return
        self._root.withdraw()
        # Defer splash import to avoid circular initialization during package
        # execution
        try:
            from gui.windows.splash_screen import SplashScreen
            self._splash = SplashScreen(
                self._root,
                version=VERSION,
                author=AUTHOR,
                email=AUTHOR_EMAIL,
                linkedin=AUTHOR_LINKEDIN,
                duration=0,
                on_close=self._root.destroy,
            )
        except Exception:
            # If splash initialisation fails (e.g. image dependencies unavailable),
            # continue startup without the splash screen.
            self._root.destroy()
            module = self.loader() if self.loader else importlib.import_module(self.module_name)
            if module and hasattr(module, "main"):
                module.main()
            return
        threading.Thread(target=self._load_module, daemon=True).start()
        self._root.mainloop()
        if self._module and hasattr(self._module, "main"):
            self._module.main()
