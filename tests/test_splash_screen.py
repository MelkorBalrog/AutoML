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

    def test_title_background(self):
        bg_items = self.splash.canvas.find_withtag("title_bg")
        text_items = self.splash.canvas.find_withtag("title_text")
        self.assertEqual(len(bg_items), 1)
        self.assertEqual(len(text_items), 2)
        self.assertEqual(self.splash.canvas.itemcget(bg_items[0], "fill"), "black")
        for t in text_items:
            self.assertEqual(self.splash.canvas.itemcget(t, "fill"), "white")

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
