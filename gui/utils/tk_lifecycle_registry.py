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
"""Owner-thread registry for every externally retained Tk callback."""

from __future__ import annotations

from dataclasses import dataclass
import inspect
import threading
from typing import Any, Callable


@dataclass
class TkRegistration:
    """Auditable description of one Tk registration."""

    identifier: Any
    kind: str
    component: object
    target_identity: int
    location: str
    disposed: bool = False
    target: object | None = None
    detail: str = ""
    previous: object | None = None


def _callable_identity(callback: Callable[..., Any]) -> tuple[int, int]:
    return (id(getattr(callback, "__self__", None)), id(getattr(callback, "__func__", callback)))


class TkLifecycleRegistry:
    """Register, deduplicate and deterministically remove Tk resources.

    A registry belongs to one Tcl interpreter and may only be drained by the
    thread that constructed that interpreter.  Components may share a registry;
    disposing one component never suppresses callbacks owned by another.
    """

    def __init__(self, root: object, owner_thread_id: int) -> None:
        self.root = root
        self.owner_thread_id = owner_thread_id
        self._entries: list[TkRegistration] = []
        self._keys: dict[tuple[Any, ...], TkRegistration] = {}
        self._active_components: dict[int, bool] = {}

    @property
    def registrations(self) -> tuple[TkRegistration, ...]:
        return tuple(self._entries)

    def _assert_owner(self) -> None:
        if threading.get_ident() != self.owner_thread_id:
            raise RuntimeError("Tk registrations must be removed on their owner thread")

    def _location(self) -> str:
        frame = inspect.currentframe()
        own_file = __file__
        while frame:
            frame = frame.f_back
            if frame and frame.f_code.co_filename != own_file:
                return f"{frame.f_code.co_filename}:{frame.f_lineno}"
        return "<unknown>"

    def _active(self, component: object) -> bool:
        explicit = self._active_components.get(id(component), True)
        return explicit and bool(getattr(component, "active", getattr(component, "_active", True)))

    def _wrapped(self, component: object, callback: Callable[..., Any], entry_box: list[Any]):
        def guarded(*args: Any, **kwargs: Any) -> Any:
            if entry_box and entry_box[0].disposed:
                return None
            if not self._active(component):
                return None
            return callback(*args, **kwargs)
        return guarded

    def _remember(self, key: tuple[Any, ...], entry: TkRegistration) -> Any:
        self._keys[key] = entry
        self._entries.append(entry)
        self._active_components.setdefault(id(entry.component), True)
        return entry.identifier

    def after(self, component: object, target: object, milliseconds: int,
              callback: Callable[..., Any]) -> Any:
        key = ("after", id(component), id(target), milliseconds, _callable_identity(callback))
        if key in self._keys and not self._keys[key].disposed:
            return self._keys[key].identifier
        box: list[Any] = []
        guarded = self._wrapped(component, callback, box)
        identifier = target.after(milliseconds, guarded)
        entry = TkRegistration(identifier, "after", component, id(target), self._location(), target=target)
        box.append(entry)
        return self._remember(key, entry)

    register_after = after

    def after_idle(self, component: object, target: object, callback: Callable[..., Any]) -> Any:
        key = ("after_idle", id(component), id(target), _callable_identity(callback))
        if key in self._keys and not self._keys[key].disposed:
            return self._keys[key].identifier
        box: list[Any] = []
        identifier = target.after_idle(self._wrapped(component, callback, box))
        entry = TkRegistration(identifier, "after_idle", component, id(target), self._location(), target=target)
        box.append(entry)
        return self._remember(key, entry)

    register_after_idle = after_idle

    def bind(self, component: object, target: object, sequence: str,
             callback: Callable[..., Any], add: str | bool = "+") -> Any:
        return self._bind("bind", component, target, sequence, callback, add)

    register_binding = bind

    def bind_all(self, component: object, target: object, sequence: str,
                 callback: Callable[..., Any], add: str | bool = "+") -> Any:
        return self._bind("bind_all", component, target, sequence, callback, add)

    register_global_binding = bind_all

    def _bind(self, kind: str, component: object, target: object, sequence: str,
              callback: Callable[..., Any], add: str | bool) -> Any:
        key = (kind, id(component), id(target), sequence, _callable_identity(callback))
        if key in self._keys and not self._keys[key].disposed:
            return self._keys[key].identifier
        box: list[Any] = []
        binder = target.bind_all if kind == "bind_all" else target.bind
        guarded = self._wrapped(component, callback, box)
        try:
            identifier = binder(sequence, guarded, add)
        except TypeError:  # lightweight widget doubles may omit Tk's add flag
            identifier = binder(sequence, guarded)
        entry = TkRegistration(identifier, kind, component, id(target), self._location(), target=target, detail=sequence)
        box.append(entry)
        return self._remember(key, entry)

    def trace_add(self, component: object, variable: object, mode: str,
                  callback: Callable[..., Any]) -> Any:
        key = ("trace", id(component), id(variable), mode, _callable_identity(callback))
        if key in self._keys and not self._keys[key].disposed:
            return self._keys[key].identifier
        box: list[Any] = []
        identifier = variable.trace_add(mode, self._wrapped(component, callback, box))
        entry = TkRegistration(identifier, "trace", component, id(variable), self._location(), target=variable, detail=mode)
        box.append(entry)
        return self._remember(key, entry)

    register_trace = trace_add

    def protocol(self, component: object, window: object, name: str,
                 callback: Callable[..., Any]) -> Any:
        key = ("protocol", id(component), id(window), name, _callable_identity(callback))
        if key in self._keys and not self._keys[key].disposed:
            return self._keys[key].identifier
        previous = window.protocol(name)
        box: list[Any] = []
        guarded = self._wrapped(component, callback, box)
        identifier = window.protocol(name, guarded)
        entry = TkRegistration(identifier or name, "protocol", component, id(window), self._location(), target=window, detail=name, previous=previous)
        box.append(entry)
        return self._remember(key, entry)

    register_protocol = protocol

    def create_command(self, component: object, name: str,
                       callback: Callable[..., Any]) -> str:
        key = ("command", id(component), id(self.root), name, _callable_identity(callback))
        if key in self._keys and not self._keys[key].disposed:
            return name
        box: list[Any] = []
        self.root.createcommand(name, self._wrapped(component, callback, box))
        entry = TkRegistration(name, "command", component, id(self.root), self._location(), target=self.root, detail=name)
        box.append(entry)
        return self._remember(key, entry)

    register_tcl_command = create_command

    def cancel(self, identifier: Any) -> bool:
        self._assert_owner()
        entry = next((item for item in self._entries if item.identifier == identifier and not item.disposed), None)
        if entry is None:
            return False
        self._cancel_entry(entry)
        return True

    def _cancel_entry(self, entry: TkRegistration) -> None:
        """Remove an exact entry (Tk identifiers are not globally unique)."""
        target = entry.target
        if entry.kind in ("after", "after_idle"):
            target.after_cancel(entry.identifier)
        elif entry.kind == "bind":
            target.unbind(entry.detail, entry.identifier)
        elif entry.kind == "bind_all":
            target.unbind_all(entry.detail)
        elif entry.kind == "trace":
            target.trace_remove(entry.detail, entry.identifier)
        elif entry.kind == "protocol":
            target.protocol(entry.detail, entry.previous or "")
        elif entry.kind == "command":
            target.deletecommand(entry.detail)
        entry.disposed = True
        entry.target = None
        entry.previous = None

    cancel_after = cancel
    remove_binding = cancel
    remove_trace = cancel
    remove_protocol = cancel
    delete_command = cancel

    def dispose_component(self, component: object) -> None:
        self._assert_owner()
        self._active_components[id(component)] = False
        # LIFO ensures dependent callbacks/commands disappear before owners.
        for entry in reversed(self._entries):
            if entry.component is component and not entry.disposed:
                self._cancel_entry(entry)

    def dispose(self) -> None:
        self._assert_owner()
        for entry in reversed(self._entries):
            if not entry.disposed:
                self._cancel_entry(entry)
