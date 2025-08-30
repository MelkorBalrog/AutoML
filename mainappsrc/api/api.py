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
"""Thin C API wrapper exposing core services via a compiled DLL."""

from __future__ import annotations

import ctypes
import json
import inspect
from importlib import import_module
from pathlib import Path
import subprocess
import sysconfig
from typing import Any, Callable

from mainappsrc.services import _SERVICE_ATTRS

_LIB_NAME = "libcore_api.so"
_SRC_PATH = Path(__file__).with_suffix(".c")
_LIB_PATH = Path(__file__).with_name(_LIB_NAME)


def _build_library() -> None:
    """Compile the C source into a shared library if missing."""
    include_dir = sysconfig.get_config_var("INCLUDEPY")
    lib_dir = sysconfig.get_config_var("LIBDIR")
    ldlib = sysconfig.get_config_var("LDLIBRARY")
    cflags = sysconfig.get_config_var("CFLAGS").split()
    ldflags = sysconfig.get_config_var("LDFLAGS").split()
    libs = sysconfig.get_config_var("LIBS").split()
    libname = ldlib[3:-3]
    subprocess.check_call(
        [
            "gcc",
            "-shared",
            "-o",
            str(_LIB_PATH),
            "-fPIC",
            str(_SRC_PATH),
            f"-I{include_dir}",
            f"-L{lib_dir}",
            f"-l{libname}",
            *cflags,
            *ldflags,
            *libs,
        ]
    )


if not _LIB_PATH.exists():
    _build_library()

_lib = ctypes.CDLL(str(_LIB_PATH))
_lib.automl_initialize.restype = ctypes.c_int
_lib.automl_initialize()

_lib.add.argtypes = (ctypes.c_int, ctypes.c_int)
_lib.add.restype = ctypes.c_int

_lib.automl_call.argtypes = (
    ctypes.c_char_p,
    ctypes.c_char_p,
    ctypes.c_char_p,
    ctypes.POINTER(ctypes.c_char_p),
)
_lib.automl_call.restype = ctypes.c_int
_lib.automl_free.argtypes = (ctypes.c_void_p,)
_lib.automl_free.restype = None


def add(left: int, right: int) -> int:
    """Return the sum of two integers using the compiled C library."""
    return int(_lib.add(left, right))


def call_service(module: str, function: str, args_json: str = "[]") -> object:
    """Invoke *function* from *module* with JSON-encoded arguments."""

    result_ptr = ctypes.c_char_p()
    status = _lib.automl_call(
        module.encode("utf-8"),
        function.encode("utf-8"),
        args_json.encode("utf-8"),
        ctypes.byref(result_ptr),
    )
    if status != 0:
        raise RuntimeError("service invocation failed")
    result_json = result_ptr.value.decode("utf-8")
    _lib.automl_free(result_ptr)
    return json.loads(result_json)


def _make_wrapper(module_name: str, func_path: str) -> Callable[..., Any]:
    def _wrapper(*args: Any, **kwargs: Any) -> Any:
        payload: Any
        if kwargs:
            payload = {"args": args, **kwargs} if args else kwargs
        else:
            payload = list(args)
        return call_service(module_name, func_path, json.dumps(payload))

    return _wrapper


__all__ = ["add", "call_service"]

for attr, (module_name, attr_name) in _SERVICE_ATTRS.items():
    module = import_module(module_name)
    target = getattr(module, attr_name)
    if inspect.isclass(target):
        members = inspect.getmembers(target, inspect.isfunction)
    else:
        members = inspect.getmembers(target, predicate=callable)
    for name, _ in members:
        if name.startswith("_"):
            continue
        wrapper_name = f"{attr_name}_{name}"
        globals()[wrapper_name] = _make_wrapper(module_name, f"{attr_name}.{name}")
        __all__.append(wrapper_name)


def automl_core_call(function: str, *args: Any, **kwargs: Any) -> Any:
    """Execute a function from :mod:`automl_core` via the DLL."""
    payload: Any
    if kwargs:
        payload = {"args": args, **kwargs} if args else kwargs
    else:
        payload = list(args)
    return call_service("mainappsrc.core.automl_core", function, json.dumps(payload))


__all__.append("automl_core_call")
