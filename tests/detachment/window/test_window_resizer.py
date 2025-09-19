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

"""Unit tests for :mod:`gui.utils.window_resizer`."""

from __future__ import annotations

import types

import pytest

from gui.utils.window_resizer import WindowResizeController


class DummyToplevel:
    """Minimal stand-in for :class:`tkinter.Toplevel` used in tests."""

    def __init__(self) -> None:
        self.bindings: dict[str, list] = {}
        self.wm_resizable_calls: list[tuple[bool, bool]] = []

    def bind(self, sequence: str, callback, add: str | None = None) -> str:  # noqa: ANN001
        self.bindings.setdefault(sequence, []).append(callback)
        return f"{sequence}-{len(self.bindings[sequence])}"

    def wm_resizable(self, x: bool, y: bool) -> None:  # noqa: ANN001
        self.wm_resizable_calls.append((x, y))

    def winfo_exists(self) -> bool:
        return True


class DummyMaster:
    """Capture ``grid_rowconfigure``/``grid_columnconfigure`` calls."""

    def __init__(self) -> None:
        self.row_config: dict[int, dict[str, int]] = {}
        self.column_config: dict[int, dict[str, int]] = {}

    def grid_rowconfigure(self, index: int, weight: int) -> None:
        self.row_config[index] = {"weight": weight}

    def grid_columnconfigure(self, index: int, weight: int) -> None:
        self.column_config[index] = {"weight": weight}


class DummyWidget:
    """Small helper that mimics geometry manager interactions."""

    def __init__(self, manager: str = "pack", master: DummyMaster | None = None) -> None:
        self.manager = manager
        self.master = master
        self.configured: dict[str, int] = {}
        self.pack_calls: list[dict[str, object]] = []
        self.grid_calls: list[dict[str, object]] = []
        self.place_calls: list[dict[str, object]] = []
        self.events: list[tuple[str, str, dict[str, object]]] = []
        self.updated = 0
        self._exists = True

    def configure(self, **kwargs: int) -> None:
        self.configured.update(kwargs)

    def winfo_manager(self) -> str:
        return self.manager

    def pack_configure(self, **kwargs: object) -> None:
        self.pack_calls.append(kwargs)

    def grid_configure(self, **kwargs: object) -> None:
        self.grid_calls.append(kwargs)

    def place_configure(self, **kwargs: object) -> None:
        self.place_calls.append(kwargs)

    def grid_info(self) -> dict[str, int]:
        return {"row": 0, "column": 0}

    def winfo_children(self) -> list:
        return []

    def event_generate(self, sequence: str, when: str = "tail", **kwargs: object) -> None:
        self.events.append((sequence, when, kwargs))

    def update_idletasks(self) -> None:
        self.updated += 1

    def winfo_exists(self) -> bool:
        return self._exists


@pytest.fixture
def event(top: DummyToplevel) -> types.SimpleNamespace:
    """Return a configure event targeting *top*."""

    return types.SimpleNamespace(widget=top, width=400, height=240)


@pytest.fixture
def top() -> DummyToplevel:
    return DummyToplevel()


def test_resizer_binds_and_tracks_primary(top: DummyToplevel) -> None:
    widget = DummyWidget()
    controller = WindowResizeController(top, widget)
    assert (True, True) in top.wm_resizable_calls
    assert widget in controller.tracked_widgets
    assert controller.size is None
    assert "<Configure>" in top.bindings


def test_resizer_updates_pack_widget(top: DummyToplevel, event: types.SimpleNamespace) -> None:
    widget = DummyWidget(manager="pack")
    controller = WindowResizeController(top, widget)
    callback = top.bindings["<Configure>"][0]
    callback(event)
    assert controller.size == (400, 240)
    assert widget.configured == {"width": 400, "height": 240}
    assert widget.pack_calls[-1] == {"expand": True, "fill": "both"}
    assert widget.updated == 1
    assert widget.events[-1][0] == "<<HostWindowResized>>"


def test_resizer_updates_grid_widget(top: DummyToplevel, event: types.SimpleNamespace) -> None:
    master = DummyMaster()
    widget = DummyWidget(manager="grid", master=master)
    controller = WindowResizeController(top)
    controller.add_target(widget)
    callback = top.bindings["<Configure>"][0]
    callback(event)
    assert widget.configured["width"] == 400
    assert widget.configured["height"] == 240
    assert widget.grid_calls[-1]["sticky"] == "nsew"
    assert master.row_config[0]["weight"] == 1
    assert master.column_config[0]["weight"] == 1


def test_resizer_drops_destroyed_widgets(top: DummyToplevel, event: types.SimpleNamespace) -> None:
    widget = DummyWidget()
    controller = WindowResizeController(top, widget)
    widget._exists = False
    callback = top.bindings["<Configure>"][0]
    callback(event)
    assert widget not in controller.tracked_widgets
