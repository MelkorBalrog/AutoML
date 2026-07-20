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
"""Grouped lifecycle registry tests which do not require a display server."""

import threading

from gui.utils.tk_lifecycle_registry import TkLifecycleRegistry


class FakeTk:
    def __init__(self):
        self.callbacks = {}
        self.removed = []
        self._next = 0

    def _add(self, callback):
        self._next += 1
        name = f"id{self._next}"
        self.callbacks[name] = callback
        return name

    def after(self, _delay, callback): return self._add(callback)
    def after_idle(self, callback): return self._add(callback)
    def after_cancel(self, name): self.removed.append(("after", name))
    def bind(self, sequence, callback, add="+"): return self._add(callback)
    def bind_all(self, sequence, callback, add="+"): return self._add(callback)
    def unbind(self, sequence, name): self.removed.append((sequence, name))
    def unbind_all(self, sequence): self.removed.append(("all", sequence))
    def protocol(self, name, callback=None):
        if callback is None: return "old"
        self.callbacks[name] = callback
    def createcommand(self, name, callback): self.callbacks[name] = callback
    def deletecommand(self, name): self.removed.append(("command", name))


class FakeVariable(FakeTk):
    def trace_add(self, mode, callback): return self._add(callback)
    def trace_remove(self, mode, name): self.removed.append((mode, name))


class Component:
    active = True


class TestRegistrationAndDeduplication:
    def test_duplicate_after_has_one_auditable_registration(self):
        tk, owner = FakeTk(), Component()
        registry = TkLifecycleRegistry(tk, threading.get_ident())
        callback = lambda: None
        assert registry.after(owner, tk, 1, callback) == registry.after(owner, tk, 1, callback)
        assert len(registry.registrations) == 1
        assert "test_tk_lifecycle_registry.py:" in registry.registrations[0].location


class TestCancellationAndRemoval:
    def test_component_disposal_is_reverse_registration_order(self):
        tk, owner = FakeTk(), Component()
        registry = TkLifecycleRegistry(tk, threading.get_ident())
        first = registry.after(owner, tk, 1, lambda: None)
        second = registry.after(owner, tk, 2, lambda: None)
        registry.dispose_component(owner)
        assert tk.removed == [("after", second), ("after", first)]

    def test_trace_and_global_binding_are_removed(self):
        tk, variable, owner = FakeTk(), FakeVariable(), Component()
        registry = TkLifecycleRegistry(tk, threading.get_ident())
        registry.trace_add(owner, variable, "write", lambda *_: None)
        registry.bind_all(owner, tk, "<Escape>", lambda _event: None)
        registry.dispose_component(owner)
        assert ("all", "<Escape>") in tk.removed
        assert any(item[0] == "write" for item in variable.removed)


class TestCallbackSafetyAndIsolation:
    def test_callback_is_suppressed_after_owner_disposal(self):
        tk, owner, calls = FakeTk(), Component(), []
        registry = TkLifecycleRegistry(tk, threading.get_ident())
        identifier = registry.after(owner, tk, 1, lambda: calls.append(True))
        callback = tk.callbacks[identifier]
        registry.dispose_component(owner)
        callback()
        assert calls == []

    def test_disposing_one_window_does_not_suppress_another(self):
        tk, first, second, calls = FakeTk(), Component(), Component(), []
        registry = TkLifecycleRegistry(tk, threading.get_ident())
        one = registry.after(first, tk, 1, lambda: calls.append("first"))
        two = registry.after(second, tk, 1, lambda: calls.append("second"))
        registry.dispose_component(first)
        tk.callbacks[one]()
        tk.callbacks[two]()
        assert calls == ["second"]
