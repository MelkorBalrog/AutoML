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

import unittest
import tkinter as tk
from PIL import ImageFont

from gui.splash_screen import SplashScreen
from gui.utils import DIALOG_BG_COLOR


class SplashScreenTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError:
            self.skipTest("Tk not available")
        self.root.withdraw()
        self._closed = False
        self.splash = SplashScreen(
            self.root, duration=0, on_close=lambda: setattr(self, "_closed", True)
        )

    def tearDown(self):
        try:
            self.splash.destroy()
        except Exception:
            pass
        finally:
            self.root.destroy()

    def test_gear_has_glow(self):
        self.splash._draw_gear()
        glow_items = self.splash.canvas.find_withtag("gear_glow")
        self.assertGreater(len(glow_items), 0)
        gear_items = self.splash.canvas.find_withtag("gear")
        self.assertEqual(len(gear_items), 1)

    def test_title_shadow(self):
        shadow_items = self.splash.canvas.find_withtag("title_shadow")
        text_items = self.splash.canvas.find_withtag("title_text")
        self.assertEqual(len(shadow_items), 2)
        self.assertEqual(len(text_items), 2)
        image_items = [t for t in text_items if self.splash.canvas.type(t) == "image"]
        text_nodes = [t for t in text_items if self.splash.canvas.type(t) == "text"]
        self.assertEqual(len(image_items), 1)
        self.assertEqual(len(text_nodes), 1)
        self.assertEqual(self.splash.canvas.itemcget(text_nodes[0], "fill"), "white")
        shadow_text = [s for s in shadow_items if self.splash.canvas.type(s) == "text"]
        self.assertEqual(
            self.splash.canvas.itemcget(shadow_text[0], "fill"), "black"
        )

    def test_title_orange_with_black_border(self):
        img = self.splash._title_pil
        colors = {
            img.getpixel((x, y))[:3]
            for x in range(img.width)
            for y in range(img.height)
            if img.getpixel((x, y))[3] > 0
        }
        self.assertIn((255, 140, 0), colors)
        self.assertIn((0, 0, 0), colors)

    def test_background_gradient(self):
        bg_items = self.splash.canvas.find_withtag("void_bg")
        self.assertEqual(len(bg_items), 1)
        top = self.splash._bg_pil.getpixel((0, 0))
        bottom = self.splash._bg_pil.getpixel(
            (self.splash.canvas_size - 1, self.splash.canvas_size - 1)
        )
        self.assertEqual(f"#{top[0]:02x}{top[1]:02x}{top[2]:02x}", "#006699")
        self.assertEqual(
            f"#{bottom[0]:02x}{bottom[1]:02x}{bottom[2]:02x}", "#002d5f"
        )

    def test_close_fades_to_invisible(self):
        if not getattr(self.splash, "_alpha_supported", False):
            self.skipTest("alpha not supported")
        # bring splash to full opacity
        for _ in range(25):
            self.splash._fade_in()
        self.splash.close()
        while float(self.splash.attributes("-alpha")) > 0.0:
            self.splash._fade_out()
        self.assertAlmostEqual(float(self.splash.attributes("-alpha")), 0.0)
        self.assertTrue(self._closed)


if __name__ == "__main__":
    unittest.main()
