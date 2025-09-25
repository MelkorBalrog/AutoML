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

"""Regression tests for Tk reparent notifications and geometry restoration."""

from __future__ import annotations

import types
import tkinter as tk

import pytest

from gui.utils import tk_utils


class _DummyTk:
    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []

    def call(self, *args: str) -> None:
        self.calls.append(tuple(str(a) for a in args))
        if args and args[0] == "tk::unsupported::reparent":
            raise tk.TclError("unsupported")


class _DummyWidget:
    def __init__(
        self,
        widget_id: int,
        name: str | None = None,
        master: "_DummyWidget | None" = None,
    ) -> None:
        self._id = widget_id
        self.tk = _DummyTk()
        self._name = name or f"w{widget_id}"
        self.children: dict[str, _DummyWidget] = {}
        self.master = master
        if master is not None and hasattr(master, "children"):
            master.children[self._name] = self

        self._manager = ""
        self._bindtags: tuple[str, ...] = (self._name, "all")
        self._bindings: dict[str, str] = {}
        self._toplevel = f".{self._name}_top"

    def update_idletasks(self) -> None:  # pragma: no cover - trivial
        return

    def winfo_id(self) -> int:
        return self._id

    def winfo_manager(self) -> str:
        return self._manager

    def winfo_children(self) -> tuple["_DummyWidget", ...]:
        return tuple(self.children.values())

    def winfo_toplevel(self) -> str:
        return self._toplevel

    def bindtags(
        self, tags: tuple[str, ...] | list[str] | None = None
    ) -> tuple[str, ...]:
        if tags is None:
            return self._bindtags
        converted = tuple(tags)
        self._bindtags = converted
        return converted

    def bind(self, sequence: str | None = None, func: str | None = None) -> str | tuple[str, ...]:
        if sequence is None:
            return tuple(self._bindings)
        if func is None:
            return self._bindings.get(sequence, "")
        self._bindings[str(sequence)] = str(func)
        return self._bindings[str(sequence)]


@pytest.mark.detachment
@pytest.mark.reparenting
class TestTkReparentNotifications:
    def test_linux_reparent_notifies_tk(self, monkeypatch: pytest.MonkeyPatch) -> None:
        original_parent = _DummyWidget(19, name="orig")
        parent = _DummyWidget(20, name="parent")
        widget = _DummyWidget(10, name="child", master=original_parent)

        monkeypatch.setattr(tk_utils.sys, "platform", "linux")

        called: dict[str, object] = {}

        class _FakeX11:
            def XOpenDisplay(self, _name: object) -> int:
                called["open"] = True
                return 1

            def XReparentWindow(
                self, display: int, wid: int, pid: int, x: int, y: int
            ) -> None:
                called["reparent"] = (display, wid, pid, x, y)

            def XFlush(self, display: int) -> None:
                called["flush"] = display

            def XCloseDisplay(self, display: int) -> None:
                called["close"] = display

        monkeypatch.setattr(
            tk_utils.ctypes,
            "cdll",
            types.SimpleNamespace(LoadLibrary=lambda _name: _FakeX11()),
        )

        counter = {"count": 0}

        original_notify = tk_utils._notify_tk_reparent

        def _spy(widget: _DummyWidget, parent_widget: _DummyWidget) -> None:
            counter["count"] += 1
            original_notify(widget, parent_widget)

        monkeypatch.setattr(tk_utils, "_notify_tk_reparent", _spy)

        tk_utils.reparent_widget(widget, parent)

        assert counter["count"] == 1
        assert called["reparent"] == (1, widget.winfo_id(), parent.winfo_id(), 0, 0)

    def test_windows_reparent_notifies_tk(self, monkeypatch: pytest.MonkeyPatch) -> None:
        original_parent = _DummyWidget(19, name="orig")
        parent = _DummyWidget(21, name="parent")
        widget = _DummyWidget(11, name="child", master=original_parent)

        monkeypatch.setattr(tk_utils.sys, "platform", "win32")

        class _FakeUser32:
            def __init__(self) -> None:
                self.calls: list[tuple[int, int]] = []

            def SetParent(self, wid: int, pid: int) -> int:
                self.calls.append((wid, pid))
                return 1

        fake_user32 = _FakeUser32()
        monkeypatch.setattr(
            tk_utils.ctypes,
            "windll",
            types.SimpleNamespace(user32=fake_user32),
            raising=False,
        )

        counter = {"count": 0}

        original_notify = tk_utils._notify_tk_reparent

        def _spy(widget: _DummyWidget, parent_widget: _DummyWidget) -> None:
            counter["count"] += 1
            original_notify(widget, parent_widget)

        monkeypatch.setattr(tk_utils, "_notify_tk_reparent", _spy)

        tk_utils.reparent_widget(widget, parent)

        assert counter["count"] == 1
        assert fake_user32.calls == [(widget.winfo_id(), parent.winfo_id())]

    def test_python_parent_references_update(self, monkeypatch):
        original_parent = _DummyWidget(30, name="orig")
        target_parent = _DummyWidget(40, name="target")
        widget = _DummyWidget(50, name="child", master=original_parent)

        monkeypatch.setattr(tk_utils.sys, "platform", "linux")

        class _FakeX11:
            def XOpenDisplay(self, _name):
                return 1

            def XReparentWindow(self, display, wid, pid, x, y):
                return None

            def XFlush(self, display):
                return None

            def XCloseDisplay(self, display):
                return None

        monkeypatch.setattr(
            tk_utils.ctypes,
            "cdll",
            types.SimpleNamespace(LoadLibrary=lambda _name: _FakeX11()),
        )

        tk_utils.reparent_widget(widget, target_parent)

        assert widget.master is target_parent
        assert "child" not in original_parent.children
        assert target_parent.children["child"] is widget

    def test_tk_native_reparent_restores_geometry(self, monkeypatch):
        class _TkWidget(_DummyWidget):
            def __init__(self) -> None:
                super().__init__(90, name="tk_child")
                self._manager = "pack"
                self.pack_forget_called = False
                self.pack_configured: dict[str, object] | None = None

            def pack_info(self) -> dict[str, object]:
                return {"side": "top", "in": "orig"}

            def pack_forget(self) -> None:
                self.pack_forget_called = True

            def pack_configure(self, **kwargs: object) -> None:
                self.pack_configured = kwargs

        widget = _TkWidget()
        parent = _DummyWidget(91, name="tk_parent")

        widget.tk = types.SimpleNamespace(
            call=lambda *args: None if args[0] == "tk::unsupported::reparent" else None
        )

        restore_calls: list[tuple[object, object, object]] = []
        original_restore = tk_utils._restore_geometry_state

        def _spy_restore(w: object, p: object, state: object) -> None:
            restore_calls.append((w, p, state))
            original_restore(w, p, state)

        monkeypatch.setattr(tk_utils, "_restore_geometry_state", _spy_restore)

        tk_utils.reparent_widget(widget, parent)

        assert restore_calls and restore_calls[0][0] is widget
        assert widget.pack_configured is not None
        assert widget.pack_configured.get("in_") is parent


@pytest.mark.detachment
@pytest.mark.reparenting
class TestTkGeometryRestoration:
    def test_pack_geometry_restored(self) -> None:
        class _PackWidget(_DummyWidget):
            def __init__(self) -> None:
                super().__init__(60, name="pack_child")
                self._manager = "pack"
                self.pack_forget_called = False
                self.pack_configured: dict[str, object] | None = None

            def pack_info(self) -> dict[str, object]:
                return {"side": "left", "fill": "both", "in": "orig"}

            def pack_forget(self) -> None:
                self.pack_forget_called = True

            def pack_configure(self, **kwargs: object) -> None:
                self.pack_configured = kwargs

        widget = _PackWidget()
        parent = _DummyWidget(61, name="new_parent")

        state = tk_utils._capture_geometry_state(widget)
        tk_utils._restore_geometry_state(widget, parent, state)

        assert widget.pack_forget_called is True
        assert widget.pack_configured is not None
        assert widget.pack_configured.get("in_") is parent
        assert widget.pack_configured.get("side") == "left"

    def test_grid_geometry_restored(self) -> None:
        class _GridWidget(_DummyWidget):
            def __init__(self) -> None:
                super().__init__(70, name="grid_child")
                self._manager = "grid"
                self.grid_forget_called = False
                self.grid_configured: dict[str, object] | None = None

            def grid_info(self) -> dict[str, object]:
                return {"row": "1", "column": "2", "in": "orig"}

            def grid_forget(self) -> None:
                self.grid_forget_called = True

            def grid_configure(self, **kwargs: object) -> None:
                self.grid_configured = kwargs

        widget = _GridWidget()
        parent = _DummyWidget(71, name="new_grid_parent")

        state = tk_utils._capture_geometry_state(widget)
        tk_utils._restore_geometry_state(widget, parent, state)

        assert widget.grid_forget_called is True
        assert widget.grid_configured is not None
        assert widget.grid_configured.get("in_") is parent
        assert widget.grid_configured.get("row") == "1"

    def test_place_geometry_restored(self) -> None:
        class _PlaceWidget(_DummyWidget):
            def __init__(self) -> None:
                super().__init__(80, name="place_child")
                self._manager = "place"
                self.place_forget_called = False
                self.place_configured: dict[str, object] | None = None

            def place_info(self) -> dict[str, object]:
                return {"x": "10", "y": "20", "in": "orig"}

            def place_forget(self) -> None:
                self.place_forget_called = True

            def place_configure(self, **kwargs: object) -> None:
                self.place_configured = kwargs

        widget = _PlaceWidget()
        parent = _DummyWidget(81, name="new_place_parent")

        state = tk_utils._capture_geometry_state(widget)
        tk_utils._restore_geometry_state(widget, parent, state)

        assert widget.place_forget_called is True
        assert widget.place_configured is not None
        assert widget.place_configured.get("in_") is parent
        assert widget.place_configured.get("x") == "10"


@pytest.mark.detachment
@pytest.mark.reparenting
class TestTkBindtagRetargeting:
    def test_bindtags_and_scripts_retarget_to_new_toplevel(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        original_parent = _DummyWidget(100, name="orig")
        target_parent = _DummyWidget(110, name="target")
        widget = _DummyWidget(120, name="child", master=original_parent)
        subchild = _DummyWidget(130, name="subchild", master=widget)

        original_parent._toplevel = ".orig"
        widget._toplevel = ".orig"
        subchild._toplevel = ".orig"
        target_parent._toplevel = ".new"

        widget.bindtags(("widget", ".orig", "all"))
        subchild.bindtags(("sub", ".orig"))
        widget.bind("<Configure>", "doit .orig resize")
        subchild.bind("<Visibility>", "childcmd .orig update")

        def _fake_notify(node: _DummyWidget, parent_node: _DummyWidget) -> None:
            tk_utils._sync_widget_parents(node, parent_node)
            node._toplevel = parent_node._toplevel
            for descendant in node.winfo_children():
                descendant._toplevel = parent_node._toplevel

        monkeypatch.setattr(tk_utils, "_notify_tk_reparent", _fake_notify)
        monkeypatch.setattr(
            tk_utils, "_restore_geometry_state", lambda *args, **kwargs: None
        )
        monkeypatch.setattr(tk_utils.sys, "platform", "linux")

        class _FakeX11:
            def XOpenDisplay(self, _name: object) -> int:
                return 1

            def XReparentWindow(
                self, display: int, wid: int, pid: int, x: int, y: int
            ) -> None:
                return None

            def XFlush(self, display: int) -> None:
                return None

            def XCloseDisplay(self, display: int) -> None:
                return None

        monkeypatch.setattr(
            tk_utils.ctypes,
            "cdll",
            types.SimpleNamespace(LoadLibrary=lambda _name: _FakeX11()),
        )

        tk_utils.reparent_widget(widget, target_parent)

        assert widget.bindtags() == ("widget", ".new", "all")
        assert subchild.bindtags() == ("sub", ".new")
        assert ".new" in widget.bind("<Configure>")
        assert ".orig" not in widget.bind("<Configure>")
        assert ".new" in subchild.bind("<Visibility>")
        assert ".orig" not in subchild.bind("<Visibility>")
