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

    class _Win32WindowProcHook:
        """Hook the Windows procedure for a Tk toplevel to mirror WM_SIZE."""

        def __init__(self, hwnd: int, callback: t.Callable[[int, int], None]) -> None:
            self.hwnd = wintypes.HWND(hwnd)
            self._callback = callback
            self._original: wintypes.LPARAM | None = None
            self._wnd_proc = WNDPROC(self._procedure)
            self._install()

        def _install(self) -> None:
            user32 = ctypes.windll.user32
            previous = user32.SetWindowLongPtrW(self.hwnd, GWL_WNDPROC, self._wnd_proc)
            if not previous:
                error = ctypes.GetLastError()
                raise ctypes.WinError(error)
            self._original = previous

        def uninstall(self) -> None:
            if self._original is None:
                return
            user32 = ctypes.windll.user32
            user32.SetWindowLongPtrW(self.hwnd, GWL_WNDPROC, self._original)
            self._original = None

        def _procedure(self, hwnd, msg, wparam, lparam):  # noqa: ANN001
            if msg in (WM_SIZE, WM_WINDOWPOSCHANGED):
                try:
                    width, height = self._extract_dimensions(lparam)
                    self._callback(width, height)
                except Exception:  # pragma: no cover - logging only
                    LOGGER.exception("Failed to propagate WM_SIZE event")
            user32 = ctypes.windll.user32
            return user32.CallWindowProcW(self._original, hwnd, msg, wparam, lparam)

        @staticmethod
        def _extract_dimensions(lparam: int) -> tuple[int, int]:
            width = lparam & 0xFFFF
            height = (lparam >> 16) & 0xFFFF
            return int(width), int(height)

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
