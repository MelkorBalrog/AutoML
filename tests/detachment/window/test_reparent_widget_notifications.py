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
import typing as t
import tkinter as tk

import pytest

from gui.utils import tk_utils


class _DummyTk:
    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []
        self.children: dict[str, set[str]] = {}
        self.renames: list[tuple[str, str]] = []

    def register_widget(self, widget: "_DummyWidget") -> None:
        parent_path = getattr(widget.master, "_w", ".") if widget.master else "."
        path = getattr(widget, "_w", None)
        if path is None:
            return
        parent_key = str(parent_path) or "."
        self.children.setdefault(parent_key, set()).add(str(path))

    def call(self, *args: str) -> t.Any:
        call = tuple(str(a) for a in args)
        self.calls.append(call)
        if not args:
            return None
        if args[0] == "tk::unsupported::reparent":
            raise tk.TclError("unsupported")
        if args[0] == "winfo" and len(args) >= 3 and args[1] == "children":
            parent = str(args[2]) or "."
            return tuple(sorted(self.children.get(parent, ())))
        if args[0] == "rename" and len(args) == 3:
            old_path, new_path = str(args[1]), str(args[2])
            self.renames.append((old_path, new_path))
            updated: dict[str, set[str]] = {}
            for parent, kids in self.children.items():
                new_parent = parent
                if parent == old_path or parent.startswith(f"{old_path}."):
                    new_parent = parent.replace(old_path, new_path, 1)
                updated.setdefault(new_parent, set())
                for kid in kids:
                    new_kid = kid
                    if kid == old_path or kid.startswith(f"{old_path}."):
                        new_kid = kid.replace(old_path, new_path, 1)
                    updated[new_parent].add(new_kid)
            self.children = updated
            parent_key = new_path.rsplit(".", 1)[0] if "." in new_path else "."
            parent_key = parent_key or "."
            self.children.setdefault(parent_key, set()).add(new_path)
            return ""
        return ""


class _DummyWidget:
    def __init__(
        self,
        widget_id: int,
        name: str | None = None,
        master: "_DummyWidget | None" = None,
    ) -> None:
        self._id = widget_id
        self._name = name or f"w{widget_id}"
        self.children: dict[str, _DummyWidget] = {}
        if master is not None:
            self.tk = master.tk
            self.master = master
        else:
            self.tk = _DummyTk()
            self.master = None
        parent_path = getattr(self.master, "_w", ".") if self.master else "."
        if parent_path in ("", "."):
            self._w = f".{self._name}"
        else:
            self._w = f"{parent_path}.{self._name}"
        if master is not None and hasattr(master, "children"):
            master.children[self._name] = self
        self.tk.register_widget(self)
        self._manager = ""

    def update_idletasks(self) -> None:  # pragma: no cover - trivial
        return

    def winfo_id(self) -> int:
        return self._id

    def winfo_manager(self) -> str:
        return self._manager


@pytest.mark.detachment
@pytest.mark.reparenting
class TestTkReparentNotifications:
    def test_linux_reparent_notifies_tk(self, monkeypatch: pytest.MonkeyPatch) -> None:
        root = _DummyWidget(1, name="root")
        original_parent = _DummyWidget(19, name="orig", master=root)
        parent = _DummyWidget(20, name="parent", master=root)
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
        root = _DummyWidget(2, name="root")
        original_parent = _DummyWidget(19, name="orig", master=root)
        parent = _DummyWidget(21, name="parent", master=root)
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

    def test_reparent_updates_widget_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        root = _DummyWidget(4, name="root")
        original_parent = _DummyWidget(60, name="orig", master=root)
        target_parent = _DummyWidget(70, name="target", master=root)
        widget = _DummyWidget(80, name="child", master=original_parent)

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
        assert widget._w.startswith(target_parent._w)
        assert widget.tk.renames

    def test_reparent_generates_unique_name_on_conflict(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = _DummyWidget(5, name="root")
        parent = _DummyWidget(90, name="parent", master=root)
        existing = _DummyWidget(91, name="child", master=parent)
        original_parent = _DummyWidget(92, name="orig", master=root)
        widget = _DummyWidget(93, name="child", master=original_parent)

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

        tk_utils.reparent_widget(widget, parent)

        assert widget.master is parent
        assert widget._name != existing._name
        assert widget._w.startswith(parent._w)

    def test_python_parent_references_update(self, monkeypatch):
        root = _DummyWidget(3, name="root")
        original_parent = _DummyWidget(30, name="orig", master=root)
        target_parent = _DummyWidget(40, name="target", master=root)
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
