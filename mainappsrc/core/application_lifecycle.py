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

"""Single-owner lifecycle control for the AutoML Tk application."""

from __future__ import annotations

import threading
import logging
from collections.abc import Callable
from typing import Any

from gui.utils.tk_utils import cancel_after_events

LOGGER = logging.getLogger(__name__)


class ApplicationLifecycleController:
    """Own shutdown and guarantee that Tk teardown occurs exactly once."""

    def __init__(self, root: Any) -> None:
        self.root = root
        self.owner_thread_id = threading.get_ident()
        self._lock = threading.Lock()
        self._shutdown_started = False
        self._app: Any | None = None

    @property
    def shutdown_started(self) -> bool:
        """Whether the controller has stopped accepting UI operations."""
        with self._lock:
            return self._shutdown_started

    def attach(self, app: Any) -> None:
        """Associate the (possibly partially initialized) application."""
        self.require_owner_thread()
        self._app = app
        app.lifecycle_controller = self

    def require_owner_thread(self) -> None:
        """Reject Tk lifecycle work attempted by a non-owner thread."""
        current = threading.get_ident()
        if current != self.owner_thread_id:
            raise RuntimeError(
                "Tk lifecycle operation must run on its owner thread "
                f"(owner={self.owner_thread_id}, current={current})"
            )

    def require_running(self) -> None:
        """Reject creation or mutation of UI components after shutdown starts."""
        self.require_owner_thread()
        if self.shutdown_started:
            raise RuntimeError("application shutdown has started")

    def shutdown(self) -> bool:
        """Dispose application-owned Tk state and terminate the root once."""
        self.require_owner_thread()
        with self._lock:
            if self._shutdown_started:
                return False
            self._shutdown_started = True

        app = self._app
        self._run_step("cancel callbacks", cancel_after_events, self.root)
        if app is not None:
            self._remove_traces_and_bindings(app)
            self._dispose_detached_windows(app)
            self._dispose_toolboxes(app)
            self._dispose_diagrams(app)
            self._remove_tcl_commands(app)
            self._clear_project_tk_references(app)

        from tools.worker_lifecycle import project_workers

        project_workers.assert_stopped()
        # These are deliberately the only application-root quit/destroy calls.
        self.root.quit()
        self.root.destroy()
        self._app = None
        self.root = None
        return True

    @staticmethod
    def _run_step(description: str, operation: Callable[..., Any], *args: Any) -> None:
        try:
            operation(*args)
        except Exception as exc:  # keep later independent disposal steps running
            LOGGER.warning("Lifecycle step '%s' failed: %s", description, exc)

    def _remove_traces_and_bindings(self, app: Any) -> None:
        for owner in (app, self.root):
            cleanup = getattr(owner, "remove_traces_and_bindings", None)
            if callable(cleanup):
                self._run_step("remove traces and bindings", cleanup)
        for sequence in ("<Control-n>", "<Control-s>", "<Control-o>",
                         "<Control-z>", "<Control-y>", "<Control-f>"):
            unbind = getattr(self.root, "unbind_all", None)
            if callable(unbind):
                self._run_step("unbind shortcut", unbind, sequence)

    def _dispose_detached_windows(self, app: Any) -> None:
        lifecycle_ui = getattr(app, "lifecycle_ui", None)
        windows = getattr(lifecycle_ui, "_detached_tab_windows", {})
        for window in list(windows.values()):
            self._dispose_component(window, "detached window")
        if hasattr(windows, "clear"):
            windows.clear()

    def _dispose_toolboxes(self, app: Any) -> None:
        for name in ("safety_mgmt_toolbox", "review_toolbox", "search_toolbox"):
            component = getattr(app, name, None)
            if component is not None:
                self._dispose_component(component, name)

    def _dispose_diagrams(self, app: Any) -> None:
        page = getattr(app, "page_diagram", None)
        if page is not None:
            self._dispose_component(page, "page diagram")
        for name in ("use_case_windows", "activity_windows", "block_windows",
                     "ibd_windows", "control_flow_windows", "diagram_windows"):
            windows = getattr(app, name, None)
            if windows is None:
                continue
            for window in list(windows):
                self._dispose_component(window, name)
            if hasattr(windows, "clear"):
                windows.clear()

    def _dispose_component(self, component: Any, description: str) -> None:
        operation = getattr(component, "dispose", None)
        if not callable(operation):
            operation = getattr(component, "destroy", None)
        if callable(operation):
            self._run_step(f"dispose {description}", operation)

    def _remove_tcl_commands(self, app: Any) -> None:
        for owner in (app, self.root):
            commands = getattr(owner, "_tclCommands", None)
            if not commands:
                continue
            deletecommand = getattr(self.root, "deletecommand", None)
            if not callable(deletecommand):
                continue
            for command in list(commands):
                self._run_step("remove Tcl command", deletecommand, command)
            commands.clear()

    @staticmethod
    def _clear_project_tk_references(app: Any) -> None:
        for name in ("active_arch_window", "review_window", "page_diagram",
                     "diagram_canvas", "selected_node", "root_node"):
            if hasattr(app, name):
                setattr(app, name, None)


__all__ = ["ApplicationLifecycleController"]
