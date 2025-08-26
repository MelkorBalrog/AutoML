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

import os
import sys
import pytest
import tkinter as tk
from tkinter import ttk

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from gui.closable_notebook import ClosableNotebook


class TestTabDetach:
    def test_tab_detach_and_reattach(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        frame = ttk.Frame(nb)
        nb.add(frame, text="Tab1")
        nb.update_idletasks()

        class Event: ...

        press = Event(); press.x = 5; press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True
        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)

        assert len(nb.tabs()) == 0
        new_nb = frame.master
        assert isinstance(new_nb, ClosableNotebook)

        press2 = Event(); press2.x = 5; press2.y = 5
        new_nb._on_tab_press(press2)
        new_nb._dragging = True
        release2 = Event()
        release2.x_root = nb.winfo_rootx() + 10
        release2.y_root = nb.winfo_rooty() + 10
        new_nb._on_tab_release(release2)

        assert len(nb.tabs()) == 1
        assert frame.master is nb
        root.destroy()

    def test_tab_detach_without_motion(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        frame = ttk.Frame(nb)
        nb.add(frame, text="Tab1")
        nb.update_idletasks()

        class Event: ...

        press = Event(); press.x = 5; press.y = 5
        nb._on_tab_press(press)
        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        release.x = nb.winfo_width() + 40
        release.y = nb.winfo_height() + 40
        nb._on_tab_release(release)

        assert len(nb.tabs()) == 0
        root.destroy()

    def test_detached_window_kept_alive(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        frame = ttk.Frame(nb)
        nb.add(frame, text="Tab1")
        nb.update_idletasks()

        class Event: ...

        press = Event(); press.x = 5; press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True
        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)

        assert nb._floating_windows
        win = nb._floating_windows[0]
        assert win.winfo_exists()
        root.destroy()

    def test_tab_stays_detached(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        frame = ttk.Frame(nb)
        nb.add(frame, text="Tab1")
        nb.update_idletasks()

        class Event: ...

        press = Event(); press.x = 5; press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True
        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)

        assert frame.master is not nb
        root.destroy()

    def test_detached_window_shows_content(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        frame = ttk.Frame(nb)
        nb.add(frame, text="Tab1")
        nb.update_idletasks()

        class Event: ...

        press = Event(); press.x = 5; press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True
        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)

        new_nb = frame.master
        assert isinstance(new_nb, ClosableNotebook)
        assert new_nb.tabs() == (str(frame),)
        root.destroy()

    def test_pack_fallback_reparents_tab(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")

        nb = ClosableNotebook(root)
        frame = ttk.Frame(nb)
        nb.add(frame, text="Tab1")
        nb.update_idletasks()

        class FailingNotebook(ClosableNotebook):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._fail = True

            def add(self, child, **kw):  # pragma: no cover - exercised via _move_tab
                if self._fail:
                    self._fail = False
                    raise tk.TclError("force fallback")
                return super().add(child, **kw)

        target = FailingNotebook(root)
        target.pack()

        assert nb._move_tab(str(frame), target)
        assert frame.master is target
        assert target.tabs() == (str(frame),)
        root.destroy()

    def test_detach_packs_content_when_move_fails(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")

        class FailingNotebook(ClosableNotebook):
            def _move_tab(self, *_a, **_kw):  # pragma: no cover - exercised via _detach_tab
                return False

        nb = FailingNotebook(root)
        frame = ttk.Frame(nb)
        nb.add(frame, text="Tab1")
        nb.update_idletasks()

        class Event: ...

        press = Event(); press.x = 5; press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True
        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)

        assert nb._floating_windows
        win = nb._floating_windows[0]
        assert frame.master is win
        root.destroy()
