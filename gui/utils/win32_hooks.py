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
"""Windows-specific helpers for intercepting resize notifications."""

from __future__ import annotations

import atexit
import logging
import sys
import threading
import typing as t
import weakref

LOGGER = logging.getLogger(__name__)

_IS_WINDOWS = sys.platform.startswith("win")
SHUTTING_DOWN = False


def begin_shutdown() -> None:
    """Mark the module as shutting down to stop further callbacks."""

    global SHUTTING_DOWN
    SHUTTING_DOWN = True


def _python_is_finalizing() -> bool:
    """Return ``True`` when the Python interpreter is shutting down."""

    is_finalizing = getattr(sys, "is_finalizing", None)
    if is_finalizing is None:
        return False
    return bool(is_finalizing())


if _IS_WINDOWS:  # pragma: win32-no-cover - exercised via integration on Windows
    import ctypes
    from ctypes import wintypes

    _HOOKS: "weakref.WeakSet[_Win32WindowProcHook]" = weakref.WeakSet()
    _HOOK_LOCK = threading.RLock()

    LRESULT = wintypes.LPARAM
    WNDPROC = ctypes.WINFUNCTYPE(
        LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
    )

    GWL_WNDPROC = -4
    WM_SIZE = 0x0005
    WM_WINDOWPOSCHANGED = 0x0047
    SWP_NOSIZE = 0x0001

    def _load_win32_library(name: str) -> ctypes.WinDLL | None:
        try:
            return ctypes.WinDLL(name, use_last_error=True)
        except OSError:
            LOGGER.warning("Unable to load %s.dll; Win32 hooks disabled", name)
            return None

    _USER32 = _load_win32_library("user32")
    _KERNEL32 = _load_win32_library("kernel32")

    def _bind_function(
        library: ctypes.WinDLL | None,
        name: str,
        argtypes: list[t.Any],
        restype: t.Any,
    ) -> t.Callable[..., t.Any] | None:
        if library is None:
            return None
        func = getattr(library, name, None)
        if func is None:
            LOGGER.warning("Missing %s in %s; Win32 hooks disabled", name, library)
            return None
        func.argtypes = argtypes
        func.restype = restype
        return func

    _CALL_WINDOW_PROC = _bind_function(
        _USER32,
        "CallWindowProcW",
        [ctypes.c_void_p, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM],
        LRESULT,
    )

    _DEF_WINDOW_PROC = _bind_function(
        _USER32,
        "DefWindowProcW",
        [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM],
        LRESULT,
    )

    _SET_WINDOW_LONG_PTR = getattr(_USER32, "SetWindowLongPtrW", None) if _USER32 else None
    _SET_WINDOW_LONG_PTR_USES_PTR = True
    if _SET_WINDOW_LONG_PTR is not None:
        _SET_WINDOW_LONG_PTR.argtypes = [
            wintypes.HWND,
            ctypes.c_int,
            ctypes.c_void_p,
        ]
        _SET_WINDOW_LONG_PTR.restype = ctypes.c_void_p
    elif _USER32 is not None:  # pragma: no cover - 32-bit Windows fallback
        _SET_WINDOW_LONG_PTR = getattr(_USER32, "SetWindowLongW", None)
        if _SET_WINDOW_LONG_PTR is not None:
            _SET_WINDOW_LONG_PTR.argtypes = [
                wintypes.HWND,
                ctypes.c_int,
                ctypes.c_long,
            ]
            _SET_WINDOW_LONG_PTR.restype = ctypes.c_long
            _SET_WINDOW_LONG_PTR_USES_PTR = False
    else:
        _SET_WINDOW_LONG_PTR_USES_PTR = True

    _SET_LAST_ERROR = getattr(_KERNEL32, "SetLastError", None) if _KERNEL32 else None

    class _WINDOWPOS(ctypes.Structure):
        _fields_ = [
            ("hwnd", wintypes.HWND),
            ("hwndInsertAfter", wintypes.HWND),
            ("x", ctypes.c_int),
            ("y", ctypes.c_int),
            ("cx", ctypes.c_int),
            ("cy", ctypes.c_int),
            ("flags", ctypes.c_uint),
        ]

    _WIN32_APIS_READY = bool(
        _USER32
        and _KERNEL32
        and _CALL_WINDOW_PROC
        and _DEF_WINDOW_PROC
        and _SET_WINDOW_LONG_PTR
        and _SET_LAST_ERROR
    )

    def _set_window_proc(hwnd: wintypes.HWND, new_proc: int | None) -> int:
        """Assign *new_proc* as the window procedure for *hwnd*."""

        if not _WIN32_APIS_READY or _SET_WINDOW_LONG_PTR is None or _SET_LAST_ERROR is None:
            raise RuntimeError("Win32 hooks are not available")

        pointer_value = 0 if new_proc is None else new_proc
        if _SET_WINDOW_LONG_PTR_USES_PTR:
            pointer_arg = ctypes.c_void_p(pointer_value)
        else:  # pragma: no cover - 32-bit Windows fallback
            pointer_arg = ctypes.c_long(pointer_value)
        _SET_LAST_ERROR(0)
        previous_raw = _SET_WINDOW_LONG_PTR(hwnd, GWL_WNDPROC, pointer_arg)
        previous = getattr(previous_raw, "value", previous_raw)
        if not previous:
            error = ctypes.get_last_error()
            if error:
                raise ctypes.WinError(error)
        return int(previous)

    def _register_hook(hook: "_Win32WindowProcHook") -> None:
        with _HOOK_LOCK:
            _HOOKS.add(hook)

    def _discard_hook(hook: "_Win32WindowProcHook") -> None:
        with _HOOK_LOCK:
            try:
                _HOOKS.discard(hook)
            except Exception:
                pass

    class _Win32WindowProcHook:
        """Hook the Windows procedure for a Tk toplevel to mirror WM_SIZE."""

        def __init__(self, hwnd: int, callback: t.Callable[[int, int], None]) -> None:
            if not _WIN32_APIS_READY:
                raise RuntimeError("Win32 hooks are not available")
            self.hwnd = wintypes.HWND(hwnd)
            self._callback = callback
            self._original: int | None = None
            self._wnd_proc = WNDPROC(self._procedure)
            self._install()
            _register_hook(self)

        def _install(self) -> None:
            proc_pointer = ctypes.cast(self._wnd_proc, ctypes.c_void_p).value
            if proc_pointer is None:
                raise RuntimeError("Unable to obtain window procedure pointer")
            previous = _set_window_proc(self.hwnd, proc_pointer)
            self._original = previous if previous else None

        def uninstall(self) -> None:
            if self._original is None:
                return
            try:
                _set_window_proc(self.hwnd, self._original)
            finally:
                self._original = None
                _discard_hook(self)

        def _forward_to_original(self, hwnd, msg, wparam, lparam):  # noqa: ANN001
            original = self._original
            if original and _CALL_WINDOW_PROC is not None:
                return _CALL_WINDOW_PROC(original, hwnd, msg, wparam, lparam)
            if _DEF_WINDOW_PROC is not None:
                return _DEF_WINDOW_PROC(hwnd, msg, wparam, lparam)
            raise RuntimeError("Win32 hooks are not available")

        def _procedure(self, hwnd, msg, wparam, lparam):  # noqa: ANN001
            if SHUTTING_DOWN:
                return self._forward_to_original(hwnd, msg, wparam, lparam)

            try:
                finalizing = _python_is_finalizing()
            except Exception:
                finalizing = True

            if finalizing:
                return self._forward_to_original(hwnd, msg, wparam, lparam)

            dimensions: tuple[int, int] | None = None
            if msg == WM_SIZE:
                dimensions = self._extract_wm_size_dimensions(lparam)
            elif msg == WM_WINDOWPOSCHANGED:
                dimensions = self._extract_windowpos_dimensions(lparam)
            if dimensions is not None:
                try:
                    width, height = dimensions
                    self._callback(width, height)
                except Exception:  # pragma: no cover - logging only
                    LOGGER.exception("Failed to propagate WM_SIZE event")
            return self._forward_to_original(hwnd, msg, wparam, lparam)

        @staticmethod
        def _extract_wm_size_dimensions(lparam: int) -> tuple[int, int]:
            width = lparam & 0xFFFF
            height = (lparam >> 16) & 0xFFFF
            return int(width), int(height)

        @staticmethod
        def _extract_windowpos_dimensions(lparam: int) -> tuple[int, int] | None:
            if not lparam:
                return None
            try:
                windowpos = ctypes.cast(lparam, ctypes.POINTER(_WINDOWPOS)).contents
            except (ValueError, OSError):
                LOGGER.debug(
                    "Unable to cast WINDOWPOS from lParam during resize notification",
                    exc_info=True,
                )
                return None
            if windowpos.flags & SWP_NOSIZE:
                return None
            return int(windowpos.cx), int(windowpos.cy)

        def __del__(self) -> None:  # pragma: no cover - defensive cleanup
            if _python_is_finalizing():
                _discard_hook(self)
                return
            try:
                self.uninstall()
            except Exception:
                LOGGER.debug("Ignoring error while uninstalling Win32 hook", exc_info=True)
                _discard_hook(self)

    def _uninstall_registered_hooks() -> None:
        begin_shutdown()
        with _HOOK_LOCK:
            hooks = list(_HOOKS)
        for hook in hooks:
            try:
                hook.uninstall()
            except Exception:
                LOGGER.debug("Ignoring error during registered hook uninstall", exc_info=True)

    if _WIN32_APIS_READY:
        atexit.register(_uninstall_registered_hooks)
else:  # pragma: no cover - exercised only on non-Windows platforms

    class _Win32WindowProcHook:  # type: ignore[no-redef]
        """Placeholder hook used on non-Windows platforms."""

        def __init__(self, hwnd: int, callback: t.Callable[[int, int], None]) -> None:  # noqa: D401
            raise RuntimeError("Win32 hooks are not supported on this platform")

        def uninstall(self) -> None:  # pragma: no cover - never invoked
            raise RuntimeError("Win32 hooks are not supported on this platform")


def create_window_size_hook(
    hwnd: int, callback: t.Callable[[int, int], None]
) -> _Win32WindowProcHook | None:
    """Return a Windows hook that mirrors size changes, if supported."""

    if not _IS_WINDOWS:
        return None
    if _IS_WINDOWS and "_WIN32_APIS_READY" in globals() and not _WIN32_APIS_READY:
        return None
    try:
        return _Win32WindowProcHook(hwnd, callback)
    except Exception:  # pragma: no cover - relies on system-level availability
        LOGGER.exception("Unable to create Windows size hook")
        return None


__all__ = ["SHUTTING_DOWN", "begin_shutdown", "create_window_size_hook"]
