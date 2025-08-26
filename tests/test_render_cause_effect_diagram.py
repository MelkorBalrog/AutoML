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

import sys
import os
import unittest

import tests.test_cause_effect_diagram as base_stub

# Ensure the shared Pillow stub exposes ImageTk
PIL_stub = sys.modules.get("PIL")
if PIL_stub is None:
    raise RuntimeError("Pillow stub not loaded")
PIL_stub.ImageTk = object

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from AutoML import AutoMLApp

class CauseEffectPDFTests(unittest.TestCase):
    def setUp(self):
        self.app = AutoMLApp.__new__(AutoMLApp)
        # Attach a renderer instance; __init__ is bypassed in tests.
        from mainappsrc.services.diagram import DiagramRendererService
        self.app.diagram_service = DiagramRendererService(self.app)

    def test_render_cause_effect_diagram_size(self):
        row = {
            "hazard": "Hazard",
            "malfunction": "Malfunction",
            "failure_modes": {},
            "faults": set(),
            "fis": set(),
            "tcs": set(),
            "attack_paths": set(),
            "threats": {},
        }
        img = self.app.diagram_service.render_cause_effect_diagram(row)
        self.assertIsNotNone(img)
        w, h = img.size
        self.assertGreaterEqual(w, 120)
        self.assertGreaterEqual(h, 60)

    def test_graph_includes_threats_and_attack_paths(self):
        row = {
            "hazard": "Hazard",
            "malfunction": "Malfunction",
            "failure_modes": {},
            "faults": set(),
            "fis": set(),
            "tcs": set(),
            "attack_paths": {"AP1"},
            "threats": {"Threat1": {"AP1"}},
        }
        nodes, edges, pos = self.app._build_cause_effect_graph(row)
        self.assertIn("ap:AP1", nodes)
        self.assertIn("thr:Threat1", nodes)
        edge_set = set(edges)
        self.assertIn(("mal:Malfunction", "thr:Threat1"), edge_set)
        self.assertIn(("thr:Threat1", "ap:AP1"), edge_set)
        self.assertEqual(pos["thr:Threat1"][0], 8)
        self.assertEqual(pos["ap:AP1"][0], 12)

    def test_no_orphan_threat_node(self):
        row = {
            "hazard": "Hazard",
            "malfunction": "Malfunction",
            "failure_modes": {},
            "faults": set(),
            "fis": set(),
            "tcs": set(),
            "attack_paths": {"AP1"},
            "threats": {"Threat1": {"AP1"}},
        }
        nodes, edges, pos = self.app._build_cause_effect_graph(row)
        used = {n for edge in edges for n in edge}
        self.assertNotIn("threat", nodes)
        for n in nodes:
            self.assertIn(n, used)
        for n in pos:
            self.assertIn(n, used)

if __name__ == "__main__":
    unittest.main()
