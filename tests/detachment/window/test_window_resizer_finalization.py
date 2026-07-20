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

"""Grouped explicit-disposal and post-Tk garbage-collection regressions."""

from __future__ import annotations

import gc
import weakref

import gui.utils.window_resizer as window_resizer


class _StubWindow:
    def __init__(self) -> None:
        self.operations: list[str] = []

    def winfo_toplevel(self):
        return self

    def wm_resizable(self, *_args) -> None:
        self.operations.append("resizable")

    def bind(self, sequence, _callback, *_args) -> str:
        self.operations.append(f"bind:{sequence}")
        return f"bind-{sequence}"

    def unbind(self, sequence, identifier) -> None:
        self.operations.append(f"unbind:{sequence}:{identifier}")

    def winfo_id(self) -> int:
        return 42

    def destroy(self) -> None:
        self.operations.append("destroy")


class _StubHook:
    def __init__(self) -> None:
        self.dispose_calls = 0

    def dispose(self) -> None:
        self.dispose_calls += 1


class TestExplicitResizeControllerDisposal:
    """Idempotence and deterministic resource release."""

    def test_dispose_unregisters_owned_resources_exactly_once(self, monkeypatch) -> None:
        window = _StubWindow()
        hook = _StubHook()
        monkeypatch.setattr(window_resizer, "create_window_size_hook", lambda *_args: hook)
        controller = window_resizer.WindowResizeController(window)

        controller.dispose()
        controller.dispose()

        assert hook.dispose_calls == 1
        assert sum(item.startswith("unbind:<Configure>") for item in window.operations) == 1
        assert sum(item.startswith("unbind:<Destroy>") for item in window.operations) == 1
        assert controller.disposed is True
        assert controller.win is None
        assert controller.tracked_widgets == ()


class TestPostRootDestructionGarbageCollection:
    """Garbage collection is deliberately free of Tk and native-hook work."""

    def test_gc_after_root_destroy_performs_no_lifecycle_operation(self, monkeypatch) -> None:
        window = _StubWindow()
        hook = _StubHook()
        monkeypatch.setattr(window_resizer, "create_window_size_hook", lambda *_args: hook)
        controller = window_resizer.WindowResizeController(window)
        controller.dispose()
        window.destroy()
        operation_count = len(window.operations)
        hook_call_count = hook.dispose_calls
        reference = weakref.ref(controller)

        del controller
        gc.collect()

        assert reference() is None
        assert len(window.operations) == operation_count
        assert hook.dispose_calls == hook_call_count
