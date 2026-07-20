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

"""Explicit, reconstruction-based lifecycle for hosted diagrams.

Tk widgets are children of one Tcl parent for their entire lifetime.  This
module consequently never reparents a widget: changing host snapshots the
model state, disposes the old visual, and asks a factory for a new visual.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import threading
from types import MappingProxyType
import typing as t

import tkinter as tk
from tkinter import ttk

from .tk_utils import cancel_after_events


@dataclass(frozen=True)
class ToolboxDefinition:
    """Shareable toolbox description containing no Tk objects."""

    identifier: str = "default"
    tools: tuple[str, ...] = ()
    metadata: t.Mapping[str, t.Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if any(isinstance(value, tk.Misc) for value in self.metadata.values()):
            raise TypeError("toolbox definitions must not contain Tk objects")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass
class DiagramVisualState:
    """Serializable state restored whenever a diagram visual is rebuilt."""

    selection: tuple[t.Any, ...] = ()
    zoom: float = 1.0
    scroll_x: float = 0.0
    scroll_y: float = 0.0
    active_toolbox: str | None = None
    values: dict[str, t.Any] = field(default_factory=dict)


@dataclass
class DiagramContext:
    """Widget-free model and presentation state shared by host visuals."""

    model: t.Any = None
    toolbox: ToolboxDefinition = field(default_factory=ToolboxDefinition)
    state: DiagramVisualState = field(default_factory=DiagramVisualState)

    def __post_init__(self) -> None:
        if isinstance(self.model, tk.Misc):
            raise TypeError("diagram models must not be Tk objects")


@t.runtime_checkable
class DiagramVisual(t.Protocol):
    """Required visual lifecycle; implementations must be owner-thread only."""

    @property
    def widget(self) -> tk.Widget: ...

    def attach(self, parent: tk.Misc, context: DiagramContext) -> None: ...
    def activate(self) -> None: ...
    def deactivate(self) -> None: ...
    def snapshot(self) -> DiagramVisualState: ...
    def dispose(self) -> None: ...


VisualFactory = t.Callable[[tk.Misc, DiagramContext], DiagramVisual]


class DockableDiagramWindow:
    """Own exactly one host-local visual and reconstruct it on host changes."""

    def __init__(
        self,
        context: DiagramContext,
        visual_factory: VisualFactory,
    ) -> None:
        if not isinstance(context, DiagramContext):
            raise TypeError("DockableDiagramWindow requires a DiagramContext")
        if not callable(visual_factory):
            raise TypeError("DockableDiagramWindow requires a visual factory")
        self.context = context
        self._visual_factory = visual_factory
        self._visual: DiagramVisual | None = None
        self._notebook: ttk.Notebook | None = None
        self._owner_thread = threading.get_ident()

    @property
    def visual(self) -> DiagramVisual | None:
        return self._visual

    @property
    def content_frame(self) -> tk.Widget | None:
        return None if self._visual is None else self._visual.widget

    def _assert_owner_thread(self) -> None:
        if threading.get_ident() != self._owner_thread:
            raise RuntimeError("diagram visuals may only change on the Tk owner thread")

    def attach(
        self,
        parent: tk.Misc,
        *,
        index: int | None = None,
        title: str = "Diagram",
    ) -> tk.Widget:
        """Build and activate a distinct visual underneath *parent*."""

        self._assert_owner_thread()
        self.dispose()
        visual = self._visual_factory(parent, self.context)
        if not isinstance(visual, DiagramVisual):
            raise TypeError("visual factory result does not implement lifecycle contract")
        if visual.widget.master is not parent:
            raise RuntimeError("visual factory constructed a widget under the wrong parent")
        visual.attach(parent, self.context)
        self._visual = visual
        if isinstance(parent, ttk.Notebook):
            tabs = parent.tabs()
            if index is None or index >= len(tabs):
                parent.add(visual.widget, text=title)
            else:
                parent.insert(index, visual.widget, text=title)
            parent.select(visual.widget)
            self._notebook = parent
        visual.activate()
        return visual.widget

    def activate(self) -> None:
        self._assert_owner_thread()
        if self._visual is None:
            raise RuntimeError("cannot activate a disposed diagram visual")
        self._visual.activate()

    def deactivate(self) -> None:
        self._assert_owner_thread()
        if self._visual is not None:
            self.context.state = self._visual.snapshot()
            self._visual.deactivate()

    def dispose(self) -> None:
        """Snapshot and destroy only this host's visual instance."""

        self._assert_owner_thread()
        visual = self._visual
        if visual is None:
            return
        self.context.state = visual.snapshot()
        visual.deactivate()
        cancel_after_events(visual.widget)
        visual.dispose()
        self._visual = None
        self._notebook = None

    def dock(self, notebook: ttk.Notebook, index: int, title: str) -> None:
        """Compatibility spelling for reconstruction under a notebook."""

        self.attach(notebook, index=index, title=title)

    def float(self, width: int, height: int, x: int, y: int, title: str) -> None:
        raise RuntimeError("use attach() with an explicitly owned Toplevel host")
