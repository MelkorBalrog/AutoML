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

"""Tiny fallback implementation of :mod:`networkx`.

The repository bundles a very small subset of NetworkX so the test suite can
run without the heavy optional dependency.  When a real installation of
NetworkX exists somewhere else on ``sys.path`` we defer to that version to
provide the full feature set expected by end users.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import os
import sys


# ---------------------------------------------------------------------------
# Detect an external installation
_package_dir = os.path.abspath(os.path.dirname(__file__))
_repo_root = os.path.abspath(os.path.join(_package_dir, os.pardir))
_search_paths = [p for p in sys.path if os.path.abspath(p) != _repo_root]
_spec = importlib.machinery.PathFinder.find_spec(__name__, _search_paths)

# Keep a reference to the stub module object executing this file so we can
# restore it if loading the external package fails part way through.
_stub_module = sys.modules[__name__]

if _spec is not None:
    _real_module = importlib.util.module_from_spec(_spec)
    # ``networkx`` imports submodules during initialization.  Those imports
    # consult :data:`sys.modules` for the package, so we must register the real
    # module *before* executing it to ensure its internal imports resolve
    # correctly.
    sys.modules[__name__] = _real_module
    try:
        _spec.loader.exec_module(_real_module)  # type: ignore[union-attr]
    except Exception:
        # If anything goes wrong while importing the external dependency we
        # silently fall back to the lightweight in-repo stub.  Re‑register the
        # original module so the rest of this file can define the fallback API.
        sys.modules[__name__] = _stub_module
        _spec = None
    else:
        globals().update(_real_module.__dict__)

if _spec is None:
    class DiGraph:
        """Very small subset of :class:`networkx.DiGraph`.

        Nodes are tracked in dictionaries mapping to sets of successors and
        predecessors which conveniently preserves insertion order in modern
        Python versions while providing efficient membership checks.
        """

        def __init__(self, *args, **kwargs):
            # Maps a node -> set of nodes with an incoming edge from ``node``
            self._succ = {}
            # Maps a node -> set of nodes with an outgoing edge to ``node``
            self._pred = {}

        # ------------------------------------------------------------------
        # Basic mutation helpers
        def add_node(self, node, **kwargs):
            """Add *node* to the graph if it isn't present."""
            self._succ.setdefault(node, set())
            self._pred.setdefault(node, set())

        def add_edge(self, u, v, **kwargs):
            """Insert a directed edge ``u -> v``."""
            self.add_node(u)
            self.add_node(v)
            self._succ[u].add(v)
            self._pred[v].add(u)

        # ------------------------------------------------------------------
        # Query helpers used by AutoML
        def has_node(self, node):
            return node in self._succ

        def successors(self, node):
            return list(self._succ.get(node, []))

        def predecessors(self, node):
            return list(self._pred.get(node, []))

        def nodes(self):
            return list(self._succ.keys())

        def edges(self):
            return [(u, v) for u, vs in self._succ.items() for v in vs]


    def draw_networkx_edges(*args, **kwargs):
        pass


    def draw_networkx_nodes(*args, **kwargs):
        pass


    def draw(*args, **kwargs):
        pass


    def draw_networkx_edge_labels(*args, **kwargs):
        pass

