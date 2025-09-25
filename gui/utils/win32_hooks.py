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

import logging
import sys
import typing as t

LOGGER = logging.getLogger(__name__)

_IS_WINDOWS = sys.platform.startswith("win")

if _IS_WINDOWS:  # pragma: win32-no-cover - exercised via integration on Windows
    import ctypes
    from ctypes import wintypes

    LRESULT = wintypes.LPARAM
    WNDPROC = ctypes.WINFUNCTYPE(
        LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
    )

    GWL_WNDPROC = -4
    WM_SIZE = 0x0005
    WM_WINDOWPOSCHANGED = 0x0047
    SWP_NOSIZE = 0x0001

    _USER32 = ctypes.windll.user32
    _KERNEL32 = ctypes.windll.kernel32

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

    _CALL_WINDOW_PROC = _USER32.CallWindowProcW
    _CALL_WINDOW_PROC.argtypes = [
        ctypes.c_void_p,
        wintypes.HWND,
        wintypes.UINT,
        wintypes.WPARAM,
        wintypes.LPARAM,
    ]
    _CALL_WINDOW_PROC.restype = LRESULT

    _DEF_WINDOW_PROC = _USER32.DefWindowProcW
    _DEF_WINDOW_PROC.argtypes = [
        wintypes.HWND,
        wintypes.UINT,
        wintypes.WPARAM,
        wintypes.LPARAM,
    ]
    _DEF_WINDOW_PROC.restype = LRESULT

    _SET_WINDOW_LONG_PTR = getattr(_USER32, "SetWindowLongPtrW", None)
    _SET_WINDOW_LONG_PTR_USES_PTR = True
    if _SET_WINDOW_LONG_PTR is not None:
        _SET_WINDOW_LONG_PTR.argtypes = [
            wintypes.HWND,
            ctypes.c_int,
            ctypes.c_void_p,
        ]
        _SET_WINDOW_LONG_PTR.restype = ctypes.c_void_p
    else:  # pragma: no cover - 32-bit Windows fallback
        _SET_WINDOW_LONG_PTR = _USER32.SetWindowLongW
        _SET_WINDOW_LONG_PTR.argtypes = [
            wintypes.HWND,
            ctypes.c_int,
            ctypes.c_long,
        ]
        _SET_WINDOW_LONG_PTR.restype = ctypes.c_long
        _SET_WINDOW_LONG_PTR_USES_PTR = False

    def _set_window_proc(hwnd: wintypes.HWND, new_proc: int | None) -> int:
        """Assign *new_proc* as the window procedure for *hwnd*."""

        pointer_value = 0 if new_proc is None else new_proc
        if _SET_WINDOW_LONG_PTR_USES_PTR:
            pointer_arg = ctypes.c_void_p(pointer_value)
        else:  # pragma: no cover - 32-bit Windows fallback
            pointer_arg = ctypes.c_long(pointer_value)
        _KERNEL32.SetLastError(0)
        previous_raw = _SET_WINDOW_LONG_PTR(hwnd, GWL_WNDPROC, pointer_arg)
        previous = getattr(previous_raw, "value", previous_raw)
        if not previous:
            error = ctypes.get_last_error()
            if error:
                raise ctypes.WinError(error)
        return int(previous)

    class _Win32WindowProcHook:
        """Hook the Windows procedure for a Tk toplevel to mirror WM_SIZE."""

        def __init__(self, hwnd: int, callback: t.Callable[[int, int], None]) -> None:
            self.hwnd = wintypes.HWND(hwnd)
            self._callback = callback
            self._original: int | None = None
            self._wnd_proc = WNDPROC(self._procedure)
            self._install()

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

        def _procedure(self, hwnd, msg, wparam, lparam):  # noqa: ANN001
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
            original = self._original
            if original:
                return _CALL_WINDOW_PROC(original, hwnd, msg, wparam, lparam)
            return _DEF_WINDOW_PROC(hwnd, msg, wparam, lparam)

        @staticmethod
        def _extract_wm_size_dimensions(lparam: int) -> tuple[int, int]:
            width = lparam & 0xFFFF
            height = (lparam >> 16) & 0xFFFF
            return int(width), int(height)

        @staticmethod
        def _extract_windowpos_dimensions(lparam: int) -> tuple[int, int] | None:
            if not lparam:
                return None
            windowpos = ctypes.cast(lparam, ctypes.POINTER(_WINDOWPOS)).contents
            if windowpos.flags & SWP_NOSIZE:
                return None
            return int(windowpos.cx), int(windowpos.cy)

        def __del__(self) -> None:
            try:
                self.uninstall()
            except Exception:
                LOGGER.debug("Ignoring error while uninstalling Win32 hook", exc_info=True)
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
    try:
        return _Win32WindowProcHook(hwnd, callback)
    except Exception:  # pragma: no cover - relies on system-level availability
        LOGGER.exception("Unable to create Windows size hook")
        return None


__all__ = ["create_window_size_hook"]

