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

    def test_gear_gradient(self):
        self.splash._draw_gear()
        fill_items = self.splash.canvas.find_withtag("gear_fill")
        self.assertGreater(len(fill_items), 1)
        outer_color = self.splash.canvas.itemcget(fill_items[0], "fill")
        inner_color = self.splash.canvas.itemcget(fill_items[-1], "fill")
        self.assertEqual(outer_color, "#ccffcc")
        self.assertEqual(inner_color, "#ffffff")

    def test_title_shadow(self):
        shadow_items = self.splash.canvas.find_withtag("title_shadow")
        text_items = self.splash.canvas.find_withtag("title_text")
        self.assertEqual(len(shadow_items), 2)
        self.assertEqual(len(text_items), 2)
        colors = {
            self.splash.canvas.itemcget(item, "text"): self.splash.canvas.itemcget(item, "fill")
            for item in text_items
        }
        self.assertEqual(colors["AutoML"], "orange")
        self.assertEqual(colors["Automotive Modeling Language"], "white")
        for item in shadow_items:
            self.assertEqual(self.splash.canvas.type(item), "text")
            self.assertEqual(self.splash.canvas.itemcget(item, "fill"), "black")

    def test_title_font_matches_subtitle(self):
        self.assertEqual(self.splash._title_font_name, self.splash._sub_font_name)

    def test_title_size_is_one_and_half(self):
        self.assertEqual(self.splash._title_size, int(self.splash._sub_size * 1.5))

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
