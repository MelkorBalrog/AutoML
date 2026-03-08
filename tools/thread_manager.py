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

from __future__ import annotations

"""Basic thread monitoring and recovery utilities.

The :class:`ThreadManager` keeps track of registered threads and uses a
background :class:`ThreadMonitor` to ensure they remain alive.  If a
thread terminates unexpectedly it will be restarted using the original
callable and arguments.  This lightweight approach helps keep the tool in
sync and improves overall robustness.
"""

import logging
from dataclasses import dataclass
import threading
from typing import Any, Callable, Dict, Optional, Tuple


logger = logging.getLogger(__name__)


@dataclass
class _ThreadInfo:
    target: Optional[Callable[..., Any]]
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]
    daemon: bool
    thread: threading.Thread
    stop_callback: Optional[Callable[[], None]]
    stop_event: Optional[threading.Event]


class ThreadMonitor(threading.Thread):
    """Background observer that restarts stopped threads."""

    def __init__(self, manager: "ThreadManager", interval: float = 1.0) -> None:
        super().__init__(daemon=True)
        self._manager = manager
        self._interval = interval
        # Internal event used to signal monitor shutdown; named to avoid
        # clashing with ``threading.Thread`` internal ``_stop`` method.
        self._stop_event = threading.Event()

    def run(self) -> None:  # pragma: no cover - trivial loop
        while not self._stop_event.is_set():
            self._manager._check_threads()
            self._stop_event.wait(self._interval)

    def stop(self) -> None:
        """Signal the monitor to terminate."""
        self._stop_event.set()


class ThreadManager:
    """Register and monitor worker threads."""

    _DEFAULT_JOIN_TIMEOUT = 5.0

    def __init__(self, interval: float = 1.0) -> None:
        self._threads: Dict[str, _ThreadInfo] = {}
        self._lock = threading.Lock()
        self._monitor = ThreadMonitor(self, interval)
        self._monitor.start()

    def register(
        self,
        name: str,
        target: Callable[..., Any],
        *,
        args: Tuple[Any, ...] | None = None,
        kwargs: Optional[Dict[str, Any]] = None,
        daemon: bool = True,
        stop_callback: Optional[Callable[[], None]] = None,
        stop_event: Optional[threading.Event] = None,
    ) -> threading.Thread:
        """Register and start *target* as a monitored thread."""
        if args is None:
            args = ()
        if kwargs is None:
            kwargs = {}
        thread = threading.Thread(target=target, args=args, kwargs=kwargs, daemon=daemon)
        thread.start()
        with self._lock:
            self._threads[name] = _ThreadInfo(
                target,
                args,
                kwargs,
                daemon,
                thread,
                stop_callback,
                stop_event,
            )
        return thread

    def register_current(self, name: str) -> threading.Thread:
        """Register the currently running thread without starting a new one."""
        thread = threading.current_thread()
        with self._lock:
            self._threads[name] = _ThreadInfo(
                None, (), {}, thread.daemon, thread, None, None
            )
        return thread

    def unregister(self, name: str) -> Optional[threading.Thread]:
        """Stop monitoring *name* and return the thread if present."""
        with self._lock:
            info = self._threads.pop(name, None)
        return info.thread if info else None

    def _check_threads(self) -> None:
        with self._lock:
            for name, info in list(self._threads.items()):
                if not info.thread.is_alive():
                    if info.target is None:
                        continue
                    thread = threading.Thread(
                        target=info.target,
                        args=info.args,
                        kwargs=info.kwargs,
                        daemon=info.daemon,
                    )
                    thread.start()
                    self._threads[name] = _ThreadInfo(
                        info.target,
                        info.args,
                        info.kwargs,
                        info.daemon,
                        thread,
                        info.stop_callback,
                        info.stop_event,
                    )

    def stop_all(self, *, timeout: Optional[float] = None) -> None:
        """Stop monitoring, request shutdown, and wait for all threads to finish."""

        join_timeout = self._DEFAULT_JOIN_TIMEOUT if timeout is None else timeout
        self._monitor.stop()
        self._monitor.join(timeout=join_timeout)
        if self._monitor.is_alive():
            logger.warning(
                "Thread monitor did not terminate within %.1f seconds", join_timeout
            )

        with self._lock:
            threads = list(self._threads.items())
            self._threads.clear()

        for name, info in threads:
            if info.stop_event is not None:
                info.stop_event.set()
            if info.stop_callback is not None:
                try:
                    info.stop_callback()
                except Exception:  # pragma: no cover - defensive logging
                    logger.exception("Error while stopping thread '%s'", name)

        for name, info in threads:
            if not info.thread.is_alive() or info.thread is threading.current_thread():
                continue
            info.thread.join(timeout=join_timeout)
            if info.thread.is_alive():
                logger.warning(
                    "Thread '%s' did not exit within %.1f seconds", name, join_timeout
                )


manager = ThreadManager()
