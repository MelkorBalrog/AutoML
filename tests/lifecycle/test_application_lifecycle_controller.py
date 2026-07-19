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

"""Grouped lifecycle tests for close, failure, and repetition scenarios."""

from __future__ import annotations

import threading

import pytest

from mainappsrc.core.application_lifecycle import ApplicationLifecycleController


class FakeRoot:
    def __init__(self):
        self.calls = []
        self._tclCommands = []

    def after_info(self):
        return ()

    def winfo_children(self):
        return ()

    def unbind_all(self, sequence):
        self.calls.append(("unbind", sequence))

    def quit(self):
        self.calls.append("quit")

    def destroy(self):
        self.calls.append("destroy")

    def deletecommand(self, command):
        self.calls.append(("deletecommand", command))


class FakeApp:
    def __init__(self):
        self.lifecycle_ui = type("UI", (), {"_detached_tab_windows": {}})()


class TestShutdownRequests:
    """Direct and repeated shutdown behavior."""

    def test_direct_shutdown_quits_and_destroys_exactly_once(self):
        root = FakeRoot()
        lifecycle = ApplicationLifecycleController(root)
        lifecycle.attach(FakeApp())

        assert lifecycle.shutdown() is True
        assert root.calls.count("quit") == 1
        assert root.calls.count("destroy") == 1

    def test_repeated_shutdown_is_idempotent_and_rejects_operations(self):
        root = FakeRoot()
        lifecycle = ApplicationLifecycleController(root)

        lifecycle.shutdown()

        assert lifecycle.shutdown() is False
        with pytest.raises(RuntimeError, match="shutdown has started"):
            lifecycle.require_running()


class TestOwnerThreadPolicy:
    """Every shutdown entry point is constrained to the Tk owner thread."""

    def test_shutdown_from_another_thread_is_rejected(self):
        lifecycle = ApplicationLifecycleController(FakeRoot())
        errors = []
        worker = threading.Thread(target=lambda: _capture_shutdown(lifecycle, errors))
        worker.start()
        worker.join()

        assert len(errors) == 1
        assert "owner thread" in str(errors[0])


class TestStartupShutdownRepetition:
    """Fresh roots receive independent exactly-once lifecycle state."""

    def test_repeated_startup_shutdown_cycles(self):
        roots = [FakeRoot(), FakeRoot()]

        for root in roots:
            ApplicationLifecycleController(root).shutdown()

        assert all(root.calls[-2:] == ["quit", "destroy"] for root in roots)


def _capture_shutdown(lifecycle, errors):
    try:
        lifecycle.shutdown()
    except RuntimeError as exc:
        errors.append(exc)
