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

"""GUI regression tests for ClosableNotebook detachment pipeline."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import pytest

from gui.utils.closable_notebook import ClosableNotebook


@pytest.mark.gui
class TestDetachmentPipeline:
    """Grouped tests ensuring detachment uses transfer pipeline."""

    def test_detach_uses_transfer_manager_and_window(self, monkeypatch):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")

        nb = ClosableNotebook(root)
        frame = tk.Frame(nb)
        frame.toolbox = tk.Frame(frame)
        nb.add(frame, text="Tab")

        class StubWindow:
            def __init__(self, *_args, **_kwargs) -> None:
                self.win = tk.Toplevel(root)
                self.nb = ttk.Notebook(self.win)
                self.added: list[tuple[tk.Widget, str]] = []
                self.toolboxes: list[tk.Widget] = []
                self.hooks: list[tk.Widget] = []

            def add_moved_widget(self, widget: tk.Widget, text: str) -> None:
                self.added.append((widget, text))
                self._ensure_toolbox(widget)
                self._activate_hooks(widget)

            def _ensure_toolbox(self, widget: tk.Widget) -> None:  # noqa: ANN001 - stub API
                tb = getattr(widget, "toolbox", None)
                if isinstance(tb, tk.Widget):
                    self.toolboxes.append(tb)

            def _activate_hooks(self, widget: tk.Widget) -> None:  # noqa: ANN001 - stub API
                self.hooks.append(widget)

        stub_windows: list[StubWindow] = []
        monkeypatch.setattr(
            "gui.utils.closable_notebook.DetachedWindow",
            lambda *args, **kwargs: stub_windows.append(StubWindow(*args, **kwargs))
            or stub_windows[-1],
        )

        class StubManager:
            def __init__(self) -> None:
                self.calls: list[tuple[tk.Widget, str, tk.Widget]] = []

            def detach_tab(
                self, source: tk.Widget, tab_id: str, target: tk.Widget
            ) -> tk.Widget:
                self.calls.append((source, tab_id, target))
                source.forget(tab_id)
                target.add(frame, text="Tab")
                return frame

        manager = StubManager()
        monkeypatch.setattr("gui.utils.closable_notebook.WidgetTransferManager", lambda: manager)

        nb._detach_tab(nb.tabs()[0], x=10, y=10)

        assert stub_windows, "DetachedWindow should have been instantiated"
        window = stub_windows[0]
        assert window.added and window.added[0][0] is frame
        assert window.toolboxes and window.toolboxes[0] is frame.toolbox
        assert window.hooks == [frame]
        assert manager.calls and manager.calls[0][0] is nb
        assert nb._floating_windows and nb._floating_windows[0] is window.win

        window.win.destroy()
        root.destroy()


@pytest.mark.gui
class TestDetachmentCloseRestore:
    """Grouped tests covering close and restore flows for detachment."""

    def test_failure_restores_tab_and_skips_window_tracking(self, monkeypatch):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")

        nb = ClosableNotebook(root)
        frame = tk.Frame(nb)
        nb.add(frame, text="Tab")

        class StubWindow:
            def __init__(self, *_args, **_kwargs) -> None:
                self.win = tk.Toplevel(root)
                self.nb = ttk.Notebook(self.win)

            def add_moved_widget(self, *_args, **_kwargs) -> None:
                pass

        monkeypatch.setattr(
            "gui.utils.closable_notebook.DetachedWindow",
            lambda *args, **kwargs: StubWindow(*args, **kwargs),
        )

        class FailingManager:
            def detach_tab(self, *_args, **_kwargs) -> tk.Widget:
                raise RuntimeError("boom")

        monkeypatch.setattr(
            "gui.utils.closable_notebook.WidgetTransferManager",
            lambda: FailingManager(),
        )

        tab_id = nb.tabs()[0]
        nb._detach_tab(tab_id, x=5, y=5)

        assert nb.tabs() and nb.tabs()[0] == tab_id
        assert not nb._floating_windows

        root.destroy()
