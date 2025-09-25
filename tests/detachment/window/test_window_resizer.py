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
import typing as t

import pytest

from gui.utils import window_resizer
from gui.utils.window_resizer import WindowResizeController


class DummyToplevel:
    """Stub a Tk toplevel widget for resize propagation tests."""

    def __init__(self) -> None:
        self.bindings: dict[str, list[t.Callable[[t.Any], None]]] = {}
        self.wm_resizable_calls: list[tuple[bool, bool]] = []
        self._hwnd = 101
        self._funcids: dict[str, tuple[str, t.Callable[[t.Any], None]]] = {}
        self.unbind_calls: list[tuple[str, str | None]] = []

    def bind(self, sequence: str, callback, add: str | None = None) -> str:  # noqa: ANN001
        self.bindings.setdefault(sequence, []).append(callback)
        funcid = f"{sequence}-{len(self.bindings[sequence])}"
        self._funcids[funcid] = (sequence, callback)
        return funcid

    def unbind(self, sequence: str, funcid: str | None = None) -> None:
        self.unbind_calls.append((sequence, funcid))
        if funcid is None:
            self.bindings.pop(sequence, None)
            return
        stored = self._funcids.pop(funcid, None)
        if stored is None:
            return
        seq, callback = stored
        callbacks = self.bindings.get(seq)
        if callbacks and callback in callbacks:
            callbacks.remove(callback)
        if not callbacks:
            self.bindings.pop(seq, None)

    def wm_resizable(self, width: bool, height: bool) -> None:  # noqa: ANN001
        self.wm_resizable_calls.append((width, height))

    def winfo_exists(self) -> bool:
        return True

    def winfo_id(self) -> int:
        return self._hwnd


class DummyMaster:
    """Capture calls that tweak grid propagation on parent containers."""

    def __init__(self) -> None:
        self.row_config: dict[int, dict[str, int]] = {}
        self.column_config: dict[int, dict[str, int]] = {}

    def grid_rowconfigure(self, index: int, weight: int) -> None:
        self.row_config[index] = {"weight": weight}

    def grid_columnconfigure(self, index: int, weight: int) -> None:
        self.column_config[index] = {"weight": weight}


class DummyWidget:
    """Mimic geometry manager behaviour for resize propagation tests."""

    def __init__(self, manager: str = "pack", master: DummyMaster | None = None) -> None:
        self.manager = manager
        self.master = master
        self.configured: dict[str, int] = {}
        self.pack_calls: list[dict[str, object]] = []
        self.grid_calls: list[dict[str, object]] = []
        self.place_calls: list[dict[str, object]] = []
        self.events: list[tuple[str, str, dict[str, object]]] = []
        self.update_calls = 0
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

    def event_generate(self, sequence: str, when: str = "tail", **kwargs: object) -> None:
        self.events.append((sequence, when, kwargs))

    def update_idletasks(self) -> None:
        self.update_calls += 1

    def winfo_exists(self) -> bool:
        return self._exists


@pytest.fixture
def top() -> DummyToplevel:
    return DummyToplevel()


@pytest.fixture
def configure_event(top: DummyToplevel) -> types.SimpleNamespace:
    """Return a synthetic configure event targeting *top*."""

    return types.SimpleNamespace(widget=top, width=640, height=360)


@pytest.mark.detachment
@pytest.mark.window_resizer
class TestWindowResizeController:
    def test_binds_configure_handler(self, top: DummyToplevel) -> None:
        widget = DummyWidget()
        controller = WindowResizeController(top, widget)
        assert (True, True) in top.wm_resizable_calls
        assert widget in controller.tracked_widgets
        assert controller.size is None
        assert "<Configure>" in top.bindings

    def test_updates_pack_managed_widget(
        self, top: DummyToplevel, configure_event: types.SimpleNamespace
    ) -> None:
        widget = DummyWidget(manager="pack")
        controller = WindowResizeController(top, widget)
        callback = top.bindings["<Configure>"][0]
        callback(configure_event)
        assert controller.size == (640, 360)
        assert widget.configured == {"width": 640, "height": 360}
        assert widget.pack_calls[-1] == {"expand": True, "fill": "both"}
        assert widget.update_calls == 1
        assert widget.events[-1][0] == "<<HostWindowResized>>"

    def test_updates_grid_managed_widget(
        self, top: DummyToplevel, configure_event: types.SimpleNamespace
    ) -> None:
        master = DummyMaster()
        widget = DummyWidget(manager="grid", master=master)
        controller = WindowResizeController(top)
        controller.add_target(widget)
        callback = top.bindings["<Configure>"][0]
        callback(configure_event)
        assert widget.configured["width"] == 640
        assert widget.configured["height"] == 360
        assert widget.grid_calls[-1]["sticky"] == "nsew"
        assert master.row_config[0]["weight"] == 1
        assert master.column_config[0]["weight"] == 1

    def test_drops_destroyed_widgets(
        self, top: DummyToplevel, configure_event: types.SimpleNamespace
    ) -> None:
        widget = DummyWidget()
        controller = WindowResizeController(top, widget)
        widget._exists = False
        callback = top.bindings["<Configure>"][0]
        callback(configure_event)
        assert widget not in controller.tracked_widgets

    def test_win32_hook_installed_when_available(
        self, top: DummyToplevel, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: list[tuple[int, t.Callable[[int, int], None]]] = []

        class Hook:
            def __init__(self, hwnd: int, callback: t.Callable[[int, int], None]) -> None:
                calls.append((hwnd, callback))

        monkeypatch.setattr(window_resizer, "create_window_size_hook", Hook)
        controller = WindowResizeController(top)
        widget = DummyWidget()
        controller.add_target(widget)
        assert controller._win32_hook is not None
        assert calls and calls[0][0] == top.winfo_id()
        callback = calls[0][1]
        callback(480, 360)
        assert widget.configured["width"] == 480
        assert widget.configured["height"] == 360

    def test_win32_hook_missing_is_tolerated(
        self, top: DummyToplevel, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(window_resizer, "create_window_size_hook", lambda *a, **k: None)
        controller = WindowResizeController(top)
        assert controller._win32_hook is None

    def test_close_releases_resources(
        self, top: DummyToplevel, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class Hook:
            def __init__(self, _hwnd: int, _callback: t.Callable[[int, int], None]) -> None:
                self.uninstalled = False

            def uninstall(self) -> None:
                self.uninstalled = True

        created: list[Hook] = []

        def factory(hwnd: int, callback: t.Callable[[int, int], None]) -> Hook:
            hook = Hook(hwnd, callback)
            created.append(hook)
            return hook

        monkeypatch.setattr(window_resizer, "create_window_size_hook", factory)
        controller = WindowResizeController(top)
        binding_id = controller._binding_id
        controller.close()
        assert controller.tracked_widgets == ()
        assert controller._win32_hook is None
        assert top.unbind_calls
        assert ("<Configure>", binding_id) in top.unbind_calls
        destroy_unbinds = [entry for entry in top.unbind_calls if entry[0] == "<Destroy>"]
        assert destroy_unbinds
        assert created and created[0].uninstalled
        controller.close()  # idempotent cleanup should not raise
