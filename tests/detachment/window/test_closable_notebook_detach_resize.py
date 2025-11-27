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

"""Regression tests for detaching tabs into floating windows."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import pytest

from gui.utils.closable_notebook import ClosableNotebook


@pytest.mark.detachment
@pytest.mark.window_resizer
class TestClosableNotebookDetachment:
    """Ensure detached tabs register with the floating window resizer."""

    def test_detach_tab_registers_resizer(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")

        notebook = ClosableNotebook(root)
        frame = tk.Frame(notebook)
        notebook.add(frame, text="Diagram")

        class StubWindow:
            def __init__(self, *_args, **_kwargs) -> None:
                self.win = tk.Toplevel(root)
                self.nb = ttk.Notebook(self.win)
                self.added: list[tuple[tk.Widget, str]] = []

            def add_moved_widget(self, widget: tk.Widget, text: str) -> None:
                self.added.append((widget, text))

            def _ensure_toolbox(self, widget: tk.Widget) -> None:  # noqa: ANN001 - stub API
                self.added.append((widget, "toolbox"))

            def _activate_hooks(self, widget: tk.Widget) -> None:  # noqa: ANN001 - stub API
                self.added.append((widget, "hooks"))

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
                target.add(frame, text="Diagram")
                return frame

        manager = StubManager()
        monkeypatch.setattr(
            "gui.utils.closable_notebook.WidgetTransferManager", lambda: manager
        )

        notebook._detach_tab(str(frame), x=10, y=10)

        assert stub_windows, "DetachedWindow should have been instantiated"
        window = stub_windows[0]
        assert window.added[0] == (frame, "Diagram")
        assert manager.calls and manager.calls[0][0] is notebook

        window.win.destroy()
        root.destroy()
