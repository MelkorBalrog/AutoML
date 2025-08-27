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

"""Project window lifecycle tests."""

import os
import sys
import tkinter as tk
import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from gui.utils.closable_notebook import ClosableNotebook
from mainappsrc.managers.project_manager import ProjectManager


pytestmark = [
    pytest.mark.ProjectLifecycle,
    pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available"),
]


def test_new_model_closes_floating_windows():
    root = tk.Tk()
    root.withdraw()
    nb = ClosableNotebook(root)
    win = tk.Toplevel(root)
    nb._floating_windows.append(win)

    class MB:
        def askyesnocancel(self, *args, **kwargs):
            return False

    class DummyApp:
        def __init__(self, notebook: ClosableNotebook):
            self.messagebox = MB()
            self.doc_nb = notebook

        def has_unsaved_changes(self) -> bool:
            return False

    app = DummyApp(nb)
    pm = ProjectManager(app)

    called = {"flag": False}
    orig_close = nb.close_all_floating

    def fake_close() -> None:
        called["flag"] = True
        orig_close()
        raise SystemExit

    nb.close_all_floating = fake_close  # type: ignore[assignment]

    with pytest.raises(SystemExit):
        pm.new_model()

    assert called["flag"]
    assert nb._floating_windows == []
    assert not win.winfo_exists()
    root.destroy()


def test_reset_on_load_closes_floating_windows(monkeypatch):
    root = tk.Tk()
    root.withdraw()
    nb = ClosableNotebook(root)
    win = tk.Toplevel(root)
    nb._floating_windows.append(win)

    class DummyApp:
        def __init__(self, notebook: ClosableNotebook):
            self.doc_nb = notebook

    app = DummyApp(nb)
    pm = ProjectManager(app)

    called = {"flag": False}
    orig_close = nb.close_all_floating

    def fake_close() -> None:
        called["flag"] = True
        orig_close()
        raise SystemExit

    nb.close_all_floating = fake_close  # type: ignore[assignment]

    monkeypatch.setattr(
        "mainappsrc.managers.project_manager.model_loader.cleanup", lambda: None
    )

    with pytest.raises(SystemExit):
        pm._reset_on_load()

    assert called["flag"]
    assert nb._floating_windows == []
    assert not win.winfo_exists()
    root.destroy()

