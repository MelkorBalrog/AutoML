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

from gui.splash_screen import SplashScreen


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
        bg_items = self.splash.canvas.find_withtag("title_bg")
        shadow_items = self.splash.canvas.find_withtag("title_shadow")
        text_items = self.splash.canvas.find_withtag("title_text")
        self.assertEqual(len(bg_items), 0)
        self.assertEqual(len(shadow_items), 2)
        self.assertEqual(len(text_items), 2)
        for t in text_items:
            self.assertEqual(self.splash.canvas.itemcget(t, "fill"), "black")
        for s in shadow_items:
            self.assertEqual(self.splash.canvas.itemcget(s, "fill"), "white")

    def test_horizon_line(self):
        horizon_items = self.splash.canvas.find_withtag("horizon")
        self.assertEqual(len(horizon_items), 1)
        self.assertEqual(
            self.splash.canvas.itemcget(horizon_items[0], "fill"), "white"
        )

    def test_void_gradient(self):
        bg_items = self.splash.canvas.find_withtag("void_bg")
        self.assertGreater(len(bg_items), 0)
        top_color = self.splash.canvas.itemcget(bg_items[0], "fill")
        bottom_color = self.splash.canvas.itemcget(bg_items[-1], "fill")
        self.assertEqual(top_color, "#90ee90")
        self.assertEqual(bottom_color, "#000000")

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

    def test_void_background(self):
        top_item = min(
            self.splash.canvas.find_overlapping(0, 0, self.splash.canvas_size, 0)
        )
        top_color = self.splash.canvas.itemcget(top_item, "fill").lower()
        horizon_y = int(self.splash.canvas_size * 0.55)
        horizon_item = min(
            self.splash.canvas.find_overlapping(
                0, horizon_y, self.splash.canvas_size, horizon_y
            )
        )
        horizon_color = self.splash.canvas.itemcget(horizon_item, "fill").lower()
        self.assertEqual(top_color, "black")
        self.assertEqual(horizon_color, "white")


if __name__ == "__main__":
    unittest.main()
