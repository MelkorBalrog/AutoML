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

"""Immutable, widget-independent diagram toolbox definitions.

This module is intentionally unaware of Tk.  It contains semantic identifiers
only; a view may resolve command identifiers and icon keys for its own widget
hierarchy without retaining a source widget or Tcl command.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True, slots=True)
class ToolboxButtonDefinition:
    """One stable semantic control in a diagram toolbox."""

    button_id: str
    label: str
    icon_key: str
    command_identifier: str
    section_id: str
    enabled_rule: bool = True
    visible_rule: bool = True

    # Compatibility names used by existing diagram projections.
    @property
    def tool(self) -> str:
        return self.command_identifier

    @property
    def command_id(self) -> str:
        return self.command_identifier

    @property
    def section(self) -> str:
        return self.section_id

    @property
    def enabled(self) -> bool:
        return self.enabled_rule

    @property
    def visible(self) -> bool:
        return self.visible_rule

    @property
    def initializer(self):
        return None


@dataclass(frozen=True, slots=True)
class ToolboxSectionDefinition:
    """A stable, ordered section belonging to one category."""

    section_id: str
    label: str
    buttons: tuple[ToolboxButtonDefinition, ...]
    category_id: str


@dataclass(frozen=True, slots=True)
class DiagramToolboxDefinition:
    """Complete ordered semantic table for a diagram type."""

    diagram_type: str
    sections: tuple[ToolboxSectionDefinition, ...]

    @property
    def section_ids(self) -> tuple[str, ...]:
        return tuple(section.section_id for section in self.sections)

    @property
    def button_ids(self) -> tuple[str, ...]:
        return tuple(button.button_id for section in self.sections for button in section.buttons)

    @property
    def category_ids(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(section.category_id for section in self.sections))


_REGISTRY: dict[str, DiagramToolboxDefinition] = {}
DIAGRAM_TOOLBOX_REGISTRY: Mapping[str, DiagramToolboxDefinition] = MappingProxyType(_REGISTRY)


def register_toolbox_definition(definition: DiagramToolboxDefinition) -> None:
    """Register an already-frozen definition for its diagram type."""
    _REGISTRY[definition.diagram_type] = definition


def toolbox_definition_for(diagram_type: str) -> DiagramToolboxDefinition:
    """Return the immutable definition registered for ``diagram_type``."""
    return _REGISTRY[diagram_type]


def _button(category: str, section: str, index: int, label: str, command: str | None = None):
    section_id = f"{category}/{section}"
    command = command or label
    return ToolboxButtonDefinition(
        f"{section_id}/{index}:{command}", label, label, command, section_id
    )


def governance_toolbox_definition(
    legacy_definitions: Mapping[str, Mapping[str, object]],
) -> DiagramToolboxDefinition:
    """Freeze the complete successful Governance descriptor exactly once.

    ``legacy_definitions`` is an ordered snapshot combining ``_toolbox_defs``
    and ``_core_toolbox_template``.  No global configuration is read here.
    """
    rows: list[tuple[str, str, str, str]] = [
        ("Governance Core", "core-elements", label, command)
        for label, command in (
            ("Select", "Select"), ("Task", "Task"), ("Initial", "Initial"),
            ("Final", "Final"), ("Decision", "Decision"), ("Merge", "Merge"),
            ("System Boundary", "System Boundary"),
        )
    ]
    rows.append(("Governance Core", "core-relationships", "Flow", "Flow"))
    rows.extend(("Governance Core", "actions", label, command) for label, command in (
        ("Add Work Product", "@add_work_product"),
        ("Add Generic Work Product", "@add_generic_work_product"),
        ("Add Lifecycle Phase", "@add_lifecycle_phase"),
    ))
    for category, data in legacy_definitions.items():
        rows.extend((category, "elements", str(item), str(item)) for item in data.get("nodes", ()))
        rows.extend((category, "relationships", str(item), str(item))
                    for item in data.get("relations", ()))
        for group, external in data.get("externals", {}).items():
            rows.extend((category, f"external:{group}:elements", str(item), str(item))
                        for item in external.get("nodes", ()))
            rows.extend((category, f"external:{group}:relationships", str(item), str(item))
                        for item in external.get("relations", ()))

    grouped: dict[tuple[str, str], list[ToolboxButtonDefinition]] = {}
    for category, section, label, command in rows:
        key = (category, section)
        grouped.setdefault(key, []).append(_button(category, section, len(grouped.get(key, ())), label, command))
    sections = tuple(
        ToolboxSectionDefinition(
            f"{category}/{section}", section, tuple(buttons), category
        )
        for (category, section), buttons in grouped.items()
    )
    return DiagramToolboxDefinition("Governance Diagram", sections)


def with_rules(
    definition: DiagramToolboxDefinition,
    enabled: Mapping[str, bool],
    visible: Mapping[str, bool],
) -> DiagramToolboxDefinition:
    """Return a frozen copy with evaluated per-control rules applied."""
    return replace(definition, sections=tuple(
        replace(section, buttons=tuple(
            replace(button,
                    enabled_rule=enabled.get(button.button_id, button.enabled_rule),
                    visible_rule=visible.get(button.button_id, button.visible_rule))
            for button in section.buttons
        )) for section in definition.sections
    ))
