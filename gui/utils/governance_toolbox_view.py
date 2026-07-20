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

"""One deterministic Tk projection of the governance toolbox semantics."""

from __future__ import annotations

from enum import Enum, auto
import tkinter as tk
from tkinter import ttk
import typing as t


class ToolboxViewLifecycle(Enum):
    """Explicit states make partially initialized views unobservable."""

    CREATING = auto()
    READY = auto()
    DISPOSING = auto()
    DISPOSED = auto()


class GovernanceToolboxView:
    """Build and own every category from one immutable semantic definition.

    ``context`` supplies ``select_tool``, action methods, and ``_icon_for``.
    It is deliberately supplied rather than captured by closures so a rebuilt
    detached diagram binds commands to its own diagram context.
    """

    ACTIONS = {
        "@add_work_product": "add_work_product",
        "@add_generic_work_product": "add_generic_work_product",
        "@add_lifecycle_phase": "add_lifecycle_phase",
    }

    def __init__(self, parent: tk.Misc, definition: t.Any, context: t.Any) -> None:
        self.parent = parent
        self.definition = definition
        self.context = context
        self.state = ToolboxViewLifecycle.CREATING
        self.frames: dict[str, tk.Widget] = {}
        self.buttons: dict[str, tk.Widget] = {}
        self.images: dict[str, t.Any] = {}
        self._build()
        self.state = ToolboxViewLifecycle.READY

    @property
    def category_ids(self) -> tuple[str, ...]:
        return tuple(self.frames)

    @property
    def button_ids(self) -> tuple[str, ...]:
        return tuple(self.buttons)

    def _command(self, identifier: str) -> t.Callable[[], None]:
        method = self.ACTIONS.get(identifier)
        if method:
            return getattr(self.context, method)
        return lambda identifier=identifier: self.context.select_tool(identifier)

    @staticmethod
    def _section_label(identifier: str) -> str:
        parts = identifier.split(":")
        if parts[0] == "external" and len(parts) > 2:
            return f"Related {parts[1]} — {parts[-1].title()}"
        return parts[-1].title()

    def _build(self) -> None:
        for category in self.definition.categories:
            frame = ttk.LabelFrame(self.parent, text=category.category_id)
            self.frames[category.category_id] = frame
            for descriptor in category.sections:
                section = ttk.LabelFrame(
                    frame, text=self._section_label(descriptor.label)
                )
                section.pack(fill=tk.X, padx=2, pady=2)
                for button in descriptor.buttons:
                    self._build_button(section, button)

    def _build_button(self, section: tk.Widget, button: t.Any) -> None:
        image = self.context._icon_for(button.icon_key)
        self.images[button.button_id] = image
        widget = ttk.Button(
            section, text=button.label, image=image, compound=tk.LEFT,
            command=self._command(button.command_id),
        )
        widget.pack(fill=tk.X, padx=2, pady=2)
        if not button.enabled:
            widget.configure(state=tk.DISABLED)
        if not button.visible:
            widget.pack_forget()
        self.buttons[button.button_id] = widget
        if button.initializer is not None:
            button.initializer(widget, self.context)

    def show(self, category_id: str) -> None:
        if self.state is not ToolboxViewLifecycle.READY:
            return
        for frame in self.frames.values():
            frame.pack_forget()
        frame = self.frames.get(category_id)
        if frame is not None:
            frame.pack(fill=tk.X, padx=2, pady=2)

    def update_context(self, context: t.Any) -> None:
        """Rebind commands without reconstructing or repopulating widgets."""
        self.context = context
        for category in self.definition.categories:
            for button in category.buttons:
                self.buttons[button.button_id].configure(command=self._command(button.command_id))

    def refresh_geometry(self, canvas: tk.Canvas, window: int) -> None:
        """Update width and scrolling while preserving the complete view."""
        canvas.update_idletasks()
        width = canvas.winfo_width() or canvas.winfo_reqwidth()
        canvas.itemconfigure(window, width=width)
        canvas.configure(scrollregion=canvas.bbox("all"))

    def dispose(self) -> None:
        if self.state is ToolboxViewLifecycle.DISPOSED:
            return
        self.state = ToolboxViewLifecycle.DISPOSING
        for frame in self.frames.values():
            if frame.winfo_exists():
                frame.destroy()
        self.frames.clear()
        self.buttons.clear()
        self.images.clear()
        self.state = ToolboxViewLifecycle.DISPOSED


def build_governance_toolbox(
    parent: tk.Misc, definition: t.Any, diagram_context: t.Any,
) -> GovernanceToolboxView:
    """The sole builder for docked and detached governance toolboxes."""
    return GovernanceToolboxView(parent, definition, diagram_context)
