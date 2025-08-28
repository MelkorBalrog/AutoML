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

"""Background generation utilities for workspace areas."""

from __future__ import annotations

import random
from PIL import Image, ImageDraw


def generate_workspace_background(width: int, height: int) -> Image.Image:
    """Return a PIL image with a beveled blue background.

    The design mirrors the application's splash screen with slanted bands
    and a vertical gradient.  *width* and *height* define the output size in
    pixels.
    """

    W, H = max(1, width), max(1, height)
    c_top = (0, 102, 153)
    c_bottom = (0, 45, 95)
    band_base = (0, 75, 130)
    band_dark = (0, 40, 90)
    n_bands_primary = 10
    n_bands_secondary = 18
    margin = 0.06
    rng = random.Random(42)

    img = Image.new("RGBA", (W, H))
    for y in range(H):
        for x in range(W):
            t = 0.65 * x / W + 0.35 * y / H
            r = int(c_top[0] * (1 - t) + c_bottom[0] * t)
            g = int(c_top[1] * (1 - t) + c_bottom[1] * t)
            b = int(c_top[2] * (1 - t) + c_bottom[2] * t)
            img.putpixel((x, y), (r, g, b, 255))

    draw = ImageDraw.Draw(img, "RGBA")

    def band_poly(x0: float, width: float, skew: float, notch: float, top_off: float, bottom_off: float):
        y_top = int(margin * H + top_off)
        y_bot = int((1 - margin) * H - bottom_off)
        x1 = x0 + width
        notch_y = y_top + 0.55 * (y_bot - y_top)
        return [
            (x0, y_top),
            (x0 + skew, y_bot),
            (x1 + skew, y_bot),
            (x1 + 0.95 * skew - notch, notch_y),
            (x1, y_top),
        ]

    for xi in sorted(
        rng.uniform(margin * W * 0.5, W * (0.85 - margin))
        for _ in range(n_bands_primary)
    ):
        width = rng.uniform(W * 0.018, W * 0.05)
        skew = rng.uniform(W * 0.12, W * 0.22)
        notch = rng.uniform(W * 0.01, W * 0.03)
        top_off = rng.uniform(0, H * 0.03)
        bot_off = rng.uniform(0, H * 0.03)
        poly = band_poly(xi, width, skew, notch, top_off, bot_off)
        color = band_base if rng.random() > 0.5 else band_dark
        draw.polygon(poly, fill=color + (int(0.35 * 255),))

    for xi in sorted(
        rng.uniform(margin * W * 0.35, W * (0.9 - margin))
        for _ in range(n_bands_secondary)
    ):
        width = rng.uniform(W * 0.003, W * 0.012)
        skew = rng.uniform(W * 0.1, W * 0.24)
        notch = rng.uniform(W * 0.004, W * 0.009)
        top_off = rng.uniform(0, H * 0.02)
        bot_off = rng.uniform(0, H * 0.02)
        poly = band_poly(xi, width, skew, notch, top_off, bot_off)
        bright = tuple(min(int(c * 1.2), 255) for c in band_base)
        draw.polygon(poly, fill=bright + (int(0.55 * 255),))

    return img

__all__ = ["generate_workspace_background"]
