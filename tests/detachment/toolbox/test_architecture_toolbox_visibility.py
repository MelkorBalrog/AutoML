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

"""Grouped tests verifying detached architecture windows retain toolboxes."""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import ttk
import pytest

from gui.utils.closable_notebook import ClosableNotebook


class ArchitectureDiagram(ttk.Frame):
    """Minimal architecture diagram exposing a ``tools_frame``."""

    def __init__(self, master: tk.Widget):
        super().__init__(master)
        self.rebuilt = False
        self.switched = False
        self.activated = False
        self.clicked = False
        self.toolbox = ttk.Frame(self)
        self.toolbox.pack(side="left")
        self.tools_frame = ttk.Frame(self.toolbox)
        self.tools_frame.pack(side="left")
        self.button = ttk.Button(self.tools_frame, text="Tool", command=self._on_click)
        self.button.pack()

    def _on_click(self) -> None:
        self.clicked = True

    def _rebuild_toolboxes(self) -> None:
        self.rebuilt = True

    def _activate_parent_phase(self) -> None:
        self.activated = True

    def _switch_toolbox(self) -> None:
        self.switched = True


def _detach_architecture_diagram() -> tuple[tk.Misc, tk.Toplevel, ArchitectureDiagram]:
    """Create an architecture diagram, detach it and return root, window and clone."""

    root = tk.Tk()
    nb = ClosableNotebook(root)
    diagram = ArchitectureDiagram(nb)
    nb.add(diagram, text="A")
    nb.update_idletasks()

    class Event:
        ...

    press = Event()
    press.x = 5
    press.y = 5
    nb._on_tab_press(press)
    nb._dragging = True
    release = Event()
    release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
    release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
    nb._on_tab_release(release)

    win = nb._floating_windows[0]
    new_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
    clone = new_nb.nametowidget(new_nb.tabs()[0])
    return root, win, clone


class TestArchitectureToolboxVisibility:
    """Grouped tests for detached architecture toolbox behaviour."""

    def test_toolbox_packed(self) -> None:
        try:
            root, _win, clone = _detach_architecture_diagram()
        except tk.TclError:
            pytest.skip("Tk not available")
        assert clone.rebuilt is True
        assert clone.switched is True
        assert clone.activated is True
        assert clone.tools_frame.winfo_manager() == "pack"
        root.destroy()

    def test_toolbox_button_responsive(self) -> None:
        try:
            root, win, clone = _detach_architecture_diagram()
        except tk.TclError:
            pytest.skip("Tk not available")
        x = clone.button.winfo_rootx() + 1
        y = clone.button.winfo_rooty() + 1
        assert win.winfo_containing(x, y) == clone.button
        clone.button.invoke()
        assert clone.clicked is True
        root.destroy()

from types import SimpleNamespace

from gui.architecture import (
    ActivityDiagramWindow,
    BlockDiagramWindow,
    ControlFlowDiagramWindow,
    GovernanceDiagramWindow,
    InternalBlockDiagramWindow,
    UseCaseDiagramWindow,
)
from mainappsrc.models.sysml.sysml_repository import SysMLRepository


DIAGRAM_TOOLBOX_WINDOWS = (
    (UseCaseDiagramWindow, "Use Case Diagram"),
    (ActivityDiagramWindow, "Activity Diagram"),
    (GovernanceDiagramWindow, "Governance"),
    (BlockDiagramWindow, "Block Definition Diagram"),
    (InternalBlockDiagramWindow, "Internal Block Diagram"),
    (ControlFlowDiagramWindow, "Control Flow Diagram"),
)


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
class TestDiagramToolboxDescriptorViewEquivalence:
    """Apply one ordered semantic-tool/view contract to every specific toolbox."""

    @staticmethod
    def _walk(widget: tk.Misc):
        for child in widget.winfo_children():
            yield child
            yield from TestDiagramToolboxDescriptorViewEquivalence._walk(child)

    @classmethod
    def _button_descriptor(cls, window: tk.Misc) -> tuple[str, ...]:
        toolbox = window.toolbox
        return tuple(
            child.cget("text") for child in cls._walk(toolbox)
            if isinstance(child, (tk.Button, ttk.Button)) and child.winfo_exists()
        )

    @pytest.mark.parametrize(("window_class", "diagram_type"), DIAGRAM_TOOLBOX_WINDOWS)
    def test_real_detached_view_exactly_matches_source_descriptor(
        self, window_class: type, diagram_type: str
    ) -> None:
        SysMLRepository.reset_instance()
        root = tk.Tk()
        notebook = ClosableNotebook(root)
        notebook.pack(fill=tk.BOTH, expand=True)
        diagram = SysMLRepository.get_instance().create_diagram(diagram_type, name="Qualified")
        source = window_class(
            notebook, app=SimpleNamespace(), diagram_id=diagram.diag_id
        )
        notebook.add(source, text="Qualified")
        root.update_idletasks()
        expected = self._button_descriptor(source)

        class Event:
            pass

        press = Event()
        press.x = press.y = 5
        notebook._on_tab_press(press)
        notebook._dragging = True
        release = Event()
        release.x_root = notebook.winfo_rootx() + notebook.winfo_width() + 40
        release.y_root = notebook.winfo_rooty() + notebook.winfo_height() + 40
        notebook._on_tab_release(release)
        floating = notebook._floating_windows[-1]
        detached = next(
            widget for widget in self._walk(floating)
            if isinstance(widget, window_class)
        )

        assert self._button_descriptor(detached) == expected
        assert detached.toolbox.winfo_exists()
        root.destroy()
