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
from gui import CapsuleButton, _StyledButton

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from gui.closable_notebook import ClosableNotebook


class TestTabDetachBasics:
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
        assert len(nb._floating_windows) == 1
        win = nb._floating_windows[0]
        new_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        new_frame = new_nb.nametowidget(new_nb.tabs()[0])
        assert new_frame is frame

        press2 = Event(); press2.x = 5; press2.y = 5
        new_nb._on_tab_press(press2)
        new_nb._dragging = True
        release2 = Event()
        release2.x_root = nb.winfo_rootx() + 10
        release2.y_root = nb.winfo_rooty() + 10
        new_nb._on_tab_release(release2)

        assert len(nb.tabs()) == 1
        assert new_frame.master is nb
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

class TestFloatingWindowBehavior:
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

        assert len(nb._floating_windows) == 1
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

        win = nb._floating_windows[0]
        new_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        new_frame = new_nb.nametowidget(new_nb.tabs()[0])
        assert new_frame.master is new_nb
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

        win = nb._floating_windows[0]
        new_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        assert len(new_nb.tabs()) == 1
        new_frame = new_nb.nametowidget(new_nb.tabs()[0])
        assert isinstance(new_frame, ttk.Frame)
        root.destroy()

    def test_detach_moves_widget(self):
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

        win = nb._floating_windows[0]
        new_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        new_frame = new_nb.nametowidget(new_nb.tabs()[0])
        assert new_frame is frame
        root.destroy()


class TestFloatingWindowLayout:
    def test_detached_tab_fits_initial_window(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        frame = ttk.Frame(nb)
        ttk.Label(frame, text="hi").pack(expand=True, fill="both")
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

        win = nb._floating_windows[0]
        new_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        new_frame = new_nb.nametowidget(new_nb.tabs()[0])
        new_nb.update_idletasks()
        assert new_frame.winfo_width() == new_nb.winfo_width()
        assert new_frame.winfo_height() == new_nb.winfo_height()
        root.destroy()

    def test_detached_tab_resizes_with_window(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        frame = ttk.Frame(nb)
        ttk.Label(frame, text="hi").pack(expand=True, fill="both")
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

        win = nb._floating_windows[0]
        new_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        new_frame = new_nb.nametowidget(new_nb.tabs()[0])
        old_w, old_h = new_frame.winfo_width(), new_frame.winfo_height()
        win.geometry("400x400")
        win.update_idletasks()
        new_nb.update_idletasks()
        assert new_frame.winfo_width() == new_nb.winfo_width() >= old_w
        assert new_frame.winfo_height() == new_nb.winfo_height() >= old_h
        root.destroy()

class TestCloning:
    def test_clone_handles_required_args(self, monkeypatch):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)

        class RequiredButton(ttk.Button):
            def __init__(self, master, text):
                super().__init__(master, text=text)

        btn = RequiredButton(nb, text="ok")
        nb.add(btn, text="Tab1")
        nb.update_idletasks()

        monkeypatch.setattr(nb, "_move_tab", lambda tab_id, target: False)

        class Event: ...

        press = Event(); press.x = 5; press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True
        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)

        win = nb._floating_windows[0]
        new_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        new_btn = new_nb.nametowidget(new_nb.tabs()[0])
        assert new_btn.cget("text") == "ok"
        root.destroy()

    def test_clone_handles_attribute_args(self, monkeypatch):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)

        class AttrWidget(ttk.Frame):
            def __init__(self, master, text):
                super().__init__(master)
                self._text = text

        widget = AttrWidget(nb, text="hello")
        nb.add(widget, text="Tab1")
        nb.update_idletasks()

        monkeypatch.setattr(nb, "_move_tab", lambda tab_id, target: False)

        class Event: ...

        press = Event(); press.x = 5; press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True
        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)

        win = nb._floating_windows[0]
        new_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        new_widget = new_nb.nametowidget(new_nb.tabs()[0])
        assert getattr(new_widget, "_text", None) == "hello"
        root.destroy()

    def test_clone_copies_entry_content(self, monkeypatch):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        entry = ttk.Entry(nb)
        entry.insert(0, "data")
        nb.add(entry, text="Tab1")
        nb.update_idletasks()

        monkeypatch.setattr(nb, "_move_tab", lambda tab_id, target: False)

        class Event: ...

        press = Event(); press.x = 5; press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True
        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)

        win = nb._floating_windows[0]
        new_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        new_entry = new_nb.nametowidget(new_nb.tabs()[0])
        assert new_entry.get() == "data"
        root.destroy()

    def test_clone_preserves_layout(self, monkeypatch):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        frame = ttk.Frame(nb)
        label = ttk.Label(frame, text="hi")
        label.pack()
        nb.add(frame, text="Tab1")
        nb.update_idletasks()

        monkeypatch.setattr(nb, "_move_tab", lambda tab_id, target: False)

        class Event: ...

        press = Event(); press.x = 5; press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True
        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)

        win = nb._floating_windows[0]
        new_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        new_frame = new_nb.nametowidget(new_nb.tabs()[0])
        children = new_frame.winfo_children()
        assert len(children) == 1
        new_label = children[0]
        assert isinstance(new_label, ttk.Label)
        assert new_label.cget("text") == "hi"
        assert new_label.winfo_manager()
        root.destroy()

    def test_clone_styled_button(self, monkeypatch):
        """Styled button detachment should clone required text argument."""
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        btn = _StyledButton(nb, text="ok")
        nb.add(btn, text="Tab1")
        nb.update_idletasks()

        monkeypatch.setattr(nb, "_move_tab", lambda tab_id, target: False)

        class Event: ...

        press = Event(); press.x = 5; press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True
        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)

        win = nb._floating_windows[0]
        new_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        new_btn = new_nb.nametowidget(new_nb.tabs()[0])
        assert isinstance(new_btn, _StyledButton)
        assert new_btn.cget("text") == "ok"
        root.destroy()


class TestDetachCleanup:
    def test_clone_capsule_with_none_text(self, monkeypatch):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        btn = CapsuleButton(nb, text="ok")
        btn._text = None
        nb.add(btn, text="Tab1")
        nb.update_idletasks()

        monkeypatch.setattr(nb, "_move_tab", lambda tab_id, target: False)

        class Event: ...

        press = Event(); press.x = 5; press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True
        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)

        win = nb._floating_windows[0]
        new_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        new_btn = new_nb.nametowidget(new_nb.tabs()[0])
        assert isinstance(new_btn, CapsuleButton)
        root.destroy()

    def test_detach_cancels_after_events(self, monkeypatch):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)

        class Blinker(ttk.Label):
            def __init__(self, master):
                super().__init__(master, text="hi")
                self._anim = self.after(10, self._blink)

            def _blink(self):
                self._anim = self.after(10, self._blink)

        lbl = Blinker(nb)
        nb.add(lbl, text="Tab1")
        nb.update_idletasks()

        errors = []

        def handler(exc, val, tb):
            errors.append(val)

        root.report_callback_exception = handler
        monkeypatch.setattr(nb, "_move_tab", lambda tab_id, target: False)

        class Event: ...

        press = Event(); press.x = 5; press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True
        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)

        root.update()
        assert not errors
        root.destroy()
