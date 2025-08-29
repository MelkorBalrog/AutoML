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

import threading
import time
import tkinter as tk
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from gui.utils.thread_safe_call import run_on_main_thread


class TestThreadSafeCall:
    def test_run_on_main_thread_executes_in_main(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            return  # pragma: no cover - skip if no display

        result: dict[str, threading.Thread] = {}

        def worker() -> None:
            def capture() -> None:
                result["thread"] = threading.current_thread()
            run_on_main_thread(capture)

        thread = threading.Thread(target=worker)
        thread.start()
        while thread.is_alive():
            root.update()
            time.sleep(0.01)
        thread.join()
        root.destroy()
        assert result["thread"] is threading.main_thread()
