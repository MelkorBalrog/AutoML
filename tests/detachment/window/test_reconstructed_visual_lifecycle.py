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

"""Grouped host reconstruction, state, toolbox, and callback lifecycle tests."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import pytest

from gui.utils.dockable_diagram_window import (
    DiagramContext,
    DiagramVisualState,
    DockableDiagramWindow,
    ToolboxDefinition,
)
from gui.utils.widget_transfer_manager import WidgetTransferManager


class _Visual:
    def __init__(self, parent: tk.Misc, context: DiagramContext) -> None:
        self.context = context
        self.widget = ttk.Frame(parent)
        self.toolbox = ttk.Frame(self.widget)
        self.toolbox.pack(side="left")
        self.selector = ttk.Combobox(self.toolbox)
        self.selector.pack()
        self.active = False
        self.binding: str | None = None
        self.callback = self.widget.after(60_000, lambda: None)

    def attach(self, parent: tk.Misc, context: DiagramContext) -> None:
        assert self.widget.master is parent
        assert context is self.context

    def activate(self) -> None:
        if self.binding is None:
            self.binding = self.selector.bind("<<ComboboxSelected>>", lambda _event: None)
        self.active = True

    def deactivate(self) -> None:
        if self.binding is not None:
            self.selector.unbind("<<ComboboxSelected>>", self.binding)
            self.binding = None
        self.active = False

    def snapshot(self) -> DiagramVisualState:
        return self.context.state

    def dispose(self) -> None:
        self.widget.destroy()


@pytest.fixture
def lifecycle_hosts():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk is unavailable")
    root.withdraw()
    first = ttk.Notebook(root)
    first.pack()
    top = tk.Toplevel(root)
    second = ttk.Notebook(top)
    second.pack()
    yield root, first, top, second
    root.destroy()


@pytest.mark.detachment
@pytest.mark.dockable
class TestReconstructedDiagramVisualLifecycle:
    """Grouped reconstruction, parentage, state, and cleanup checks."""

    def test_popout_and_reintegration_build_distinct_tcl_children(self, lifecycle_hosts):
        _root, first, _top, second = lifecycle_hosts
        state = DiagramVisualState(("node-7",), 1.75, 0.25, 0.5, "relationships")
        context = DiagramContext({"diagram": 7}, ToolboxDefinition("sysml"), state)
        dock = DockableDiagramWindow(context, _Visual)
        initial = dock.attach(first, title="Diagram")
        initial_path = str(initial)
        initial_toolbox = dock.visual.toolbox
        initial._dock_window = dock

        detached = WidgetTransferManager().detach_tab(first, first.tabs()[0], second)
        detached._dock_window = dock
        assert detached is not initial
        assert str(detached.master) == detached.tk.call("winfo", "parent", str(detached))
        assert detached.master is second
        assert dock.visual.toolbox is not initial_toolbox
        assert context.state == state
        assert not bool(detached.bind("<<ComboboxSelected>>"))

        reintegrated = WidgetTransferManager().detach_tab(second, second.tabs()[0], first)
        assert reintegrated is not detached
        assert str(reintegrated) != initial_path
        assert reintegrated.master is first
        assert context.state.selection == ("node-7",)
        assert context.state.zoom == 1.75
        assert (context.state.scroll_x, context.state.scroll_y) == (0.25, 0.5)
        assert context.state.active_toolbox == "relationships"

    def test_host_toolboxes_and_disposal_are_isolated(self, lifecycle_hosts):
        _root, first, _top, second = lifecycle_hosts
        context = DiagramContext(toolbox=ToolboxDefinition("shared", ("select", "node")))
        docked = DockableDiagramWindow(context, _Visual)
        popped = DockableDiagramWindow(context, _Visual)
        docked.attach(first, title="Docked")
        popped.attach(second, title="Popped")
        docked_widget = docked.content_frame
        docked_toolbox = docked.visual.toolbox
        popped_toolbox = popped.visual.toolbox

        popped.dispose()
        assert popped.content_frame is None
        assert docked.content_frame is docked_widget
        assert docked_widget.winfo_exists()
        assert docked.visual.toolbox is docked_toolbox
        assert docked_toolbox is not popped_toolbox
        assert context.toolbox.tools == ("select", "node")
