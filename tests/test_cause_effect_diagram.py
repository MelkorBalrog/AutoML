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

import os
import sys
import types
import unittest

# ---------------------------------------------------------------------------
# Provide a light-weight stub of the Pillow API used by AutoML.  The real
# Pillow package isn't available in the execution environment, but the
# cause-and-effect diagram generator relies on a few classes from it.  The
# stub records the size of images that would have been created so tests can
# verify the canvas is large enough to contain all nodes.
# ---------------------------------------------------------------------------
created_sizes = []

class _FakeImage:
    def __init__(self, size):
        self.size = size

    def save(self, *_args, **_kwargs):
        pass

def _image_new(_mode, size, _color):
    created_sizes.append(size)
    return _FakeImage(size)

class _FakeDraw:
    def __init__(self, _img):
        pass

    def line(self, *_a, **_k):
        pass

    def polygon(self, *_a, **_k):
        pass

    def rectangle(self, *_a, **_k):
        pass

    def multiline_textbbox(self, *_a, **_k):
        # Return a dummy bounding box
        return (0, 0, 10, 10)

    def multiline_text(self, *_a, **_k):
        pass

class _FakeFontModule:
    @staticmethod
    def load_default():
        return object()

PIL_stub = types.ModuleType("PIL")
PIL_stub.Image = types.SimpleNamespace(new=_image_new)
PIL_stub.ImageDraw = types.SimpleNamespace(Draw=lambda img: _FakeDraw(img))
PIL_stub.ImageFont = _FakeFontModule
PIL_stub.ImageTk = object

# ---------------------------------------------------------------------------
# Minimal numpy stub supporting the features required by auto_generate_fta_diagram
# ---------------------------------------------------------------------------
class _Vector:
    def __init__(self, data):
        self.x, self.y = data

    def __sub__(self, other):
        return _Vector((self.x - other.x, self.y - other.y))

    def __add__(self, other):
        return _Vector((self.x + other.x, self.y + other.y))

    def __truediv__(self, scalar):
        return _Vector((self.x / scalar, self.y / scalar))

    def __mul__(self, scalar):
        return _Vector((self.x * scalar, self.y * scalar))

    __rmul__ = __mul__

    def __iter__(self):
        yield self.x
        yield self.y

def _array(data):
    return _Vector(data)

def _norm(vec):
    return (vec.x ** 2 + vec.y ** 2) ** 0.5

numpy_stub = types.ModuleType("numpy")
numpy_stub.array = _array
numpy_stub.linalg = types.SimpleNamespace(norm=_norm)
# Provide minimal helpers so other tests using :mod:`pytest` don't fail when
# ``numpy`` is present in :data:`sys.modules`.
numpy_stub.isscalar = lambda x: isinstance(x, (int, float, bool))
numpy_stub.bool_ = bool
sys.modules.setdefault("numpy", numpy_stub)
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from AutoML import AutoMLApp
import AutoML as _AutoML
_AutoML.Image = PIL_stub.Image
_AutoML.ImageDraw = PIL_stub.ImageDraw
_AutoML.ImageFont = PIL_stub.ImageFont


class DummyNode:
    def __init__(self, unique_id, node_type, name, gate_type=None, children=None, input_subtype=""):
        self.unique_id = unique_id
        self.node_type = node_type
        self.name = name
        self.gate_type = gate_type
        self.children = children or []
        self.input_subtype = input_subtype


class CauseEffectDiagramTests(unittest.TestCase):
    def setUp(self):
        # Inject PIL stub so AutoML's image utilities work without Pillow
        self._orig_pil = sys.modules.get("PIL")
        sys.modules["PIL"] = PIL_stub
        import AutoML as _AutoML
        _AutoML.Image = PIL_stub.Image
        _AutoML.ImageDraw = PIL_stub.ImageDraw
        _AutoML.ImageFont = PIL_stub.ImageFont
        # Create a minimal AutoMLApp instance without initialising Tk
        self.app = AutoMLApp.__new__(AutoMLApp)

    def tearDown(self):
        if self._orig_pil is not None:
            sys.modules["PIL"] = self._orig_pil
        else:
            sys.modules.pop("PIL", None)

    def test_build_simplified_fta_model_includes_basic_events(self):
        be1 = DummyNode(2, "BASIC EVENT", "Cause 1")
        be2 = DummyNode(3, "BASIC EVENT", "Cause 2")
        top = DummyNode(1, "TOP EVENT", "Hazard", gate_type="AND", children=[be1, be2])

        model = self.app.build_simplified_fta_model(top)

        node_ids = {n["id"] for n in model["nodes"]}
        self.assertEqual(node_ids, {"1", "2", "3"})

        edge_pairs = {(e["source"], e["target"]) for e in model["edges"]}
        self.assertEqual(edge_pairs, {("1", "2"), ("1", "3")})

    def test_auto_generate_diagram_canvas_large_enough(self):
        """Ensure generated diagram is not clipped when only one node exists."""
        created_sizes.clear()
        top = DummyNode(1, "TOP EVENT", "Hazard")
        model = self.app.build_simplified_fta_model(top)
        AutoMLApp.auto_generate_fta_diagram(model, "out.png")
        self.assertTrue(created_sizes, "Image.new was not called")
        width, height = created_sizes[0]
        self.assertGreaterEqual(width, 120)
        self.assertGreaterEqual(height, 60)

if __name__ == "__main__":
    unittest.main()
