/*
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
*/

#include <Python.h>
#include <string.h>

#ifdef _WIN32
#  define DLL_EXPORT __declspec(dllexport)
#else
#  define DLL_EXPORT __attribute__((visibility("default")))
#endif

static int g_initialized = 0;

DLL_EXPORT int automl_initialize(void) {
    if (!g_initialized) {
        Py_Initialize();
        g_initialized = 1;
    }
    return 0;
}

static PyObject *get_attr_path(PyObject *base, const char *path) {
    char *temp = PyMem_Malloc(strlen(path) + 1);
    if (!temp) {
        return NULL;
    }
    strcpy(temp, path);
    char *token = strtok(temp, ".");
    PyObject *obj = base;
    while (token && obj) {
        PyObject *next = PyObject_GetAttrString(obj, token);
        Py_DECREF(obj);
        obj = next;
        token = strtok(NULL, ".");
    }
    PyMem_Free(temp);
    return obj;
}

DLL_EXPORT int automl_call(const char *module_name,
                           const char *func_name,
                           const char *args_json,
                           char **result_json) {
    if (!g_initialized) {
        return -1;
    }

    PyObject *module = PyImport_ImportModule(module_name);
    if (!module) {
        PyErr_Clear();
        return -1;
    }
    PyObject *func = get_attr_path(module, func_name);
    if (!func || !PyCallable_Check(func)) {
        Py_XDECREF(func);
        PyErr_Clear();
        return -1;
    }

    PyObject *args = NULL;
    PyObject *kwargs = NULL;

    if (args_json && strlen(args_json) > 0) {
        PyObject *json_module = PyImport_ImportModule("json");
        PyObject *loads = PyObject_GetAttrString(json_module, "loads");
        PyObject *parsed = PyObject_CallFunction(loads, "s", args_json);
        Py_DECREF(loads);
        Py_DECREF(json_module);
        if (!parsed) {
            Py_DECREF(func);
            PyErr_Clear();
            return -1;
        }
        if (PyList_Check(parsed) || PyTuple_Check(parsed)) {
            args = PySequence_Tuple(parsed);
            Py_DECREF(parsed);
            kwargs = NULL;
        } else if (PyDict_Check(parsed)) {
            args = PyTuple_New(0);
            kwargs = parsed;
        } else {
            args = PyTuple_Pack(1, parsed);
            Py_DECREF(parsed);
            kwargs = NULL;
        }
    } else {
        args = PyTuple_New(0);
        kwargs = NULL;
    }

    PyObject *result = PyObject_Call(func, args, kwargs);
    Py_DECREF(func);
    Py_DECREF(args);
    Py_XDECREF(kwargs);
    if (!result) {
        PyErr_Clear();
        return -1;
    }

    PyObject *json_module = PyImport_ImportModule("json");
    PyObject *dumps = PyObject_GetAttrString(json_module, "dumps");
    PyObject *res_json = PyObject_CallFunctionObjArgs(dumps, result, NULL);
    Py_DECREF(result);
    Py_DECREF(dumps);
    Py_DECREF(json_module);
    if (!res_json) {
        PyErr_Clear();
        return -1;
    }
    const char *c = PyUnicode_AsUTF8(res_json);
    if (!c) {
        Py_DECREF(res_json);
        PyErr_Clear();
        return -1;
    }
    size_t len = strlen(c);
    *result_json = PyMem_Malloc(len + 1);
    if (!*result_json) {
        Py_DECREF(res_json);
        return -1;
    }
    strcpy(*result_json, c);
    Py_DECREF(res_json);
    return 0;
}

DLL_EXPORT void automl_free(char *ptr) {
    PyMem_Free(ptr);
}

DLL_EXPORT void automl_finalize(void) {
    if (g_initialized) {
        Py_Finalize();
        g_initialized = 0;
    }
}

DLL_EXPORT int add(int left, int right) {
    return left + right;
}

