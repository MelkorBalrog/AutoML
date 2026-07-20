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

"""GUI stress driver entered through :func:`AutoML.main`.

The bootstrap is replaced only to provide a deterministic, empty project;
launcher cleanup, diagnostics, and worker assertions still use the normal
application entry point.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from types import SimpleNamespace

import AutoML
from gui.utils.dockable_diagram_window import DiagramContext, DockableDiagramWindow, ToolboxDefinition
from mainappsrc.core.application_lifecycle import ApplicationLifecycleController


class StressVisual:
    """Small real-Tk visual implementing the production docking contract."""

    def __init__(self, parent: tk.Misc, context: DiagramContext) -> None:
        self.context = context
        self.widget = ttk.Frame(parent)
        self.toolbox = ttk.Frame(self.widget)
        self.toolbox.pack()
        self._callback: str | None = None

    def attach(self, parent: tk.Misc, context: DiagramContext) -> None:
        assert self.widget.master is parent and context is self.context

    def activate(self) -> None:
        if self._callback is None:
            self._callback = self.widget.after_idle(lambda: None)

    def deactivate(self) -> None:
        if self._callback is not None:
            try:
                self.widget.after_cancel(self._callback)
            except tk.TclError:
                pass
            self._callback = None

    def snapshot(self):
        return self.context.state

    def dispose(self) -> None:
        self.widget.destroy()


def supported_diagram_types() -> tuple[str, ...]:
    """Read the configured diagram inventory rather than duplicating it."""
    rules = json.loads(Path("config/rules/diagram_rules.json").read_text(encoding="utf-8"))
    return tuple(rules["arch_diagram_types"])


class StressApplication:
    """One complete root lifetime and its isolated diagram hosts."""

    def __init__(self, iterations: int) -> None:
        self.root = tk.Tk()
        self.root.withdraw()
        self.controller = ApplicationLifecycleController(self.root)
        self.controller.attach(self)
        self.iterations = iterations
        self.records: list[tuple[int, str, int, int]] = []
        self.lifecycle_ui = SimpleNamespace(_detached_tab_windows={})
        self.diagram_windows: list[DockableDiagramWindow] = []

    def run(self) -> None:
        notebook = ttk.Notebook(self.root)
        notebook.pack()
        contexts = {
            name: DiagramContext(model=name, toolbox=ToolboxDefinition(name, ("select", "create")))
            for name in supported_diagram_types()
        }
        docks = {name: DockableDiagramWindow(context, StressVisual) for name, context in contexts.items()}
        self.diagram_windows = list(docks.values())
        for name, dock in docks.items():
            dock.attach(notebook, title=name)

        for iteration in range(self.iterations):
            identities = {name: id(dock.visual.toolbox) for name, dock in docks.items()}
            popouts = self._open_popouts(iteration, docks, contexts)
            self._close_popouts(iteration, popouts, docks, identities)
            self._reintegrate(notebook, docks, contexts)
            self.root.update_idletasks()
        assert len(self.records) == self.iterations * len(contexts)
        self.controller.shutdown()

    def _open_popouts(self, iteration, docks, contexts):
        popouts = []
        for name, dock in docks.items():
            self.controller.require_running()  # centralized owner-thread assertion
            dock.activate()
            top = tk.Toplevel(self.root)
            popped = DockableDiagramWindow(contexts[name], StressVisual)
            popped.attach(top, title=name)
            popouts.append((top, popped))
            self.records.append((iteration, name, id(popped.visual.toolbox), id(popped.content_frame)))
            self.root.focus_force()
            top.focus_force()
            assert dock.visual.toolbox is not popped.visual.toolbox
        return popouts

    @staticmethod
    def _close_popouts(iteration, popouts, docks, identities) -> None:
        close_order = reversed(popouts) if iteration % 2 else popouts
        for top, popped in close_order:
            popped.dispose()
            top.destroy()
            assert {name: id(dock.visual.toolbox) for name, dock in docks.items()} == identities

    @staticmethod
    def _reintegrate(notebook, docks, contexts) -> None:
        for name, dock in reversed(tuple(docks.items())):
            before = contexts[name].toolbox
            dock.dispose()
            dock.attach(notebook, title=name)
            assert contexts[name].toolbox is before


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--startups", type=int, default=3)
    args = parser.parse_args()
    if args.iterations < 100 or args.startups < 2:
        parser.error("qualification requires at least 100 iterations and two startups")
    for _ in range(args.startups):
        module = SimpleNamespace(main=lambda: StressApplication(args.iterations).run())
        AutoML._bootstrap = lambda: module
        AutoML.main()


if __name__ == "__main__":
    main()
