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

"""Crash report logging utilities with multiple implementations."""


import datetime
import logging
import os
import sys
import threading
import traceback
from pathlib import Path

from tools.thread_manager import manager as thread_manager

# Default directory for crash logs
LOG_DIR = Path(__file__).resolve().parent


def crash_handler_v1(exc_type, exc, tb, path: Path | None = None) -> Path:
    """Write traceback to a fixed file using basic file IO."""
    log_path = path or LOG_DIR / "crash_v1.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as fh:
        traceback.print_exception(exc_type, exc, tb, file=fh)
    return log_path


def crash_handler_v2(exc_type, exc, tb, path: Path | None = None) -> Path:
    """Use :mod:`logging` to persist the crash details."""
    log_path = path or LOG_DIR / "crash_v2.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=log_path, level=logging.ERROR, force=True)
    logging.error("Unhandled exception", exc_info=(exc_type, exc, tb))
    return log_path


class CrashLoggerV3:
    """Callable class writing traceback to a provided path."""

    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def __call__(self, exc_type, exc, tb) -> Path:
        with open(self.path, "w", encoding="utf-8") as fh:
            fh.write("Unhandled exception\n")
            traceback.print_exception(exc_type, exc, tb, file=fh)
        return self.path


def crash_handler_v3(exc_type, exc, tb, path: Path | None = None) -> Path:
    """Helper using :class:`CrashLoggerV3` for a default path."""
    return CrashLoggerV3(path or LOG_DIR / "crash_v3.log")(exc_type, exc, tb)


class CrashLoggerV4:
    """Timestamped crash logger producing unique files."""

    def __init__(self, directory: Path | str = LOG_DIR):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def __call__(self, exc_type, exc, tb) -> Path:
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        log_path = self.directory / f"crash_{timestamp}.log"
        with open(log_path, "w", encoding="utf-8") as fh:
            fh.write(f"Timestamp: {timestamp}\n")
            fh.write("Unhandled exception\n")
            traceback.print_exception(exc_type, exc, tb, file=fh)
        return log_path


class _LoopWatchdog:
    """Watchdog that terminates the process if not regularly fed."""

    def __init__(self, timeout: float, handler):
        self.timeout = timeout
        self.handler = handler
        self._timer: threading.Timer | None = None

    def _trigger(self) -> None:
        exc = TimeoutError("Watchdog timeout")
        self.handler(TimeoutError, exc, None)
        os._exit(1)

    def _reset(self) -> None:
        if self._timer is not None:
            self._timer.cancel()
        self._timer = threading.Timer(self.timeout, self._trigger)
        self._timer.daemon = True
        self._timer.start()

    def start(self) -> None:
        self._reset()

    def feed(self) -> None:
        self._reset()


def watchdog_v1(timeout: float = 5.0, path: Path | str | None = None) -> _LoopWatchdog:
    """Watchdog using :func:`crash_handler_v1` for logging."""

    path_obj = Path(path) if path else None
    wd = _LoopWatchdog(timeout, lambda et, e, tb: crash_handler_v1(et, e, tb, path_obj))
    wd.start()
    return wd


def watchdog_v2(timeout: float = 5.0, path: Path | str | None = None) -> _LoopWatchdog:
    """Watchdog using :func:`crash_handler_v2` for logging."""

    path_obj = Path(path) if path else None
    wd = _LoopWatchdog(timeout, lambda et, e, tb: crash_handler_v2(et, e, tb, path_obj))
    wd.start()
    return wd


def watchdog_v3(timeout: float = 5.0, path: Path | str | None = None) -> _LoopWatchdog:
    """Watchdog using :func:`crash_handler_v3` for logging."""

    path_obj = Path(path) if path else None
    wd = _LoopWatchdog(timeout, lambda et, e, tb: crash_handler_v3(et, e, tb, path_obj))
    wd.start()
    return wd


def watchdog_v4(timeout: float = 5.0, directory: Path | str = LOG_DIR) -> _LoopWatchdog:
    """Watchdog using :class:`CrashLoggerV4` for unique log files."""

    logger = CrashLoggerV4(directory)
    wd = _LoopWatchdog(timeout, logger)
    wd.start()
    return wd


# The most complete watchdog implementation
watchdog_best = watchdog_v4


def install_v1() -> None:
    sys.excepthook = crash_handler_v1


def install_v2() -> None:
    sys.excepthook = crash_handler_v2


def install_v3() -> None:
    sys.excepthook = crash_handler_v3


def install_v4(directory: Path | str = LOG_DIR) -> None:
    sys.excepthook = CrashLoggerV4(directory)


# The most complete implementation is version 4
install_best = install_v4


def start_watchdog_thread(
    timeout: float = 5.0, interval: float = 1.0
) -> tuple[threading.Event, threading.Thread]:
    """Start a background thread feeding the crash watchdog."""

    wd = watchdog_best(timeout)
    stop_event = threading.Event()

    def _feed() -> None:
        while not stop_event.is_set():
            wd.feed()
            stop_event.wait(interval)

    thread = thread_manager.register(
        "crash_watchdog",
        _feed,
        daemon=True,
        stop_event=stop_event,
    )
    return stop_event, thread


def stop_watchdog_thread(stop_event: threading.Event) -> None:
    """Stop the background watchdog feeding thread."""

    stop_event.set()
    thread = thread_manager.unregister("crash_watchdog")
    if thread:
        thread.join()

__all__ = [
    "crash_handler_v1",
    "crash_handler_v2",
    "CrashLoggerV3",
    "crash_handler_v3",
    "CrashLoggerV4",
    "_LoopWatchdog",
    "watchdog_v1",
    "watchdog_v2",
    "watchdog_v3",
    "watchdog_v4",
    "watchdog_best",
    "install_v1",
    "install_v2",
    "install_v3",
    "install_v4",
    "install_best",
    "start_watchdog_thread",
    "stop_watchdog_thread",
]
