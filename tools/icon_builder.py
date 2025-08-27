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

#!/usr/bin/env python3
from __future__ import annotations

"""Utility to programmatically generate a high-definition AutoML icon.

Provides four drawing strategies, each producing a small 3D cube with a gear
inside.  Strategy ``v4`` offers the most detailed rendering and is the default
used by build scripts.  Icons may be scaled via a ``--scale`` option to improve
their definition for executable packages.
"""

import struct
from pathlib import Path
from typing import Callable, Dict, List, Tuple

Size = Tuple[int, int]
Color = Tuple[int, int, int, int]
BASE_SIZE: Size = (32, 32)

# cube layout constants
_CUBE_OX = 6
_CUBE_OY = 6
_CUBE_SIZE = 11
_CUBE_OFFSET = 4
_GEAR_CX = _CUBE_OX + _CUBE_SIZE // 2
_GEAR_CY = _CUBE_OY + _CUBE_OFFSET + _CUBE_SIZE // 2
_GEAR_R = 4

def _write_ico(path: Path, pixels: List[List[Color]]) -> None:
    """Write *pixels* to *path* as a 32-bit ICO file."""
    height = len(pixels)
    width = len(pixels[0]) if height else 0
    row_bytes = width * 4
    bmp_header_size = 40
    and_mask = b"\x00" * ((row_bytes // 4) * height)

    bmp_size = bmp_header_size + row_bytes * height + len(and_mask)
    ico_header = struct.pack("<3H", 0, 1, 1)
    entry = struct.pack("<BBBBHHII", width, height, 0, 0, 1, 32, bmp_size, 6 + 16)
    bmp_header = struct.pack(
        "<IIIHHIIIIII",
        bmp_header_size,
        width,
        height * 2,
        1,
        32,
        0,
        row_bytes * height,
        0,
        0,
        0,
        0,
    )
    body = bytearray()
    for y in reversed(range(height)):
        for x in range(width):
            r, g, b, a = pixels[y][x]
            body.extend(struct.pack("<BBBB", b, g, r, a))
    data = ico_header + entry + bmp_header + body + and_mask
    Path(path).write_bytes(data)


def _blank(color: Color, size: Size = BASE_SIZE) -> List[List[Color]]:
    return [[color for _ in range(size[0])] for _ in range(size[1])]


def _scale_pixels(pixels: List[List[Color]], scale: int) -> List[List[Color]]:
    """Return *pixels* scaled by *scale* using nearest-neighbour sampling."""
    if scale <= 1:
        return pixels
    height = len(pixels)
    width = len(pixels[0]) if height else 0
    scaled = [[(0, 0, 0, 0) for _ in range(width * scale)] for _ in range(height * scale)]
    for y in range(height):
        for x in range(width):
            color = pixels[y][x]
            for sy in range(scale):
                row = scaled[y * scale + sy]
                for sx in range(scale):
                    row[x * scale + sx] = color
    return scaled


def _put(pixels: List[List[Color]], x: int, y: int, color: Color) -> None:
    if 0 <= x < BASE_SIZE[0] and 0 <= y < BASE_SIZE[1]:
        pixels[y][x] = color


def _fill_top(pixels: List[List[Color]], ox: int, oy: int, size: int, offset: int, color: Color) -> None:
    for dy in range(offset):
        y = oy + dy
        start = ox + offset - 1 - dy
        for x in range(start, start + size):
            _put(pixels, x, y, color)


def _fill_front(pixels: List[List[Color]], ox: int, oy: int, size: int, offset: int, color: Color) -> None:
    for dy in range(size):
        y = oy + offset + dy
        for x in range(ox, ox + size):
            _put(pixels, x, y, color)


def _fill_side(pixels: List[List[Color]], ox: int, oy: int, size: int, offset: int, color: Color) -> None:
    for dy in range(size):
        y = oy + offset + dy
        start = ox + size + dy
        for x in range(start, start + offset):
            _put(pixels, x, y, color)


def _outline_cube(pixels: List[List[Color]], ox: int, oy: int, size: int, offset: int, color: Color) -> None:
    for x in range(ox, ox + size):
        _put(pixels, x, oy + offset, color)
        _put(pixels, x, oy + offset + size - 1, color)
    for y in range(oy + offset, oy + offset + size):
        _put(pixels, ox, y, color)
        _put(pixels, ox + size - 1, y, color)
    for dy in range(offset + 1):
        _put(pixels, ox + offset - 1 - dy, oy + dy, color)
        _put(pixels, ox + offset - 1 + size - 1 + dy, oy + dy, color)
    for x in range(ox + offset - 1, ox + offset - 1 + size):
        _put(pixels, x, oy, color)
    for dy in range(size + 1):
        _put(pixels, ox + size + dy, oy + offset + dy, color)
    for dy in range(offset + 1):
        _put(pixels, ox + size - 1 + dy, oy + offset - 1 - dy, color)


def _draw_cube(
    pixels: List[List[Color]],
    front: Color,
    top: Color,
    side: Color,
    outline: Color,
    wireframe: bool = False,
) -> None:
    ox, oy, size, offset = _CUBE_OX, _CUBE_OY, _CUBE_SIZE, _CUBE_OFFSET
    if not wireframe:
        _fill_top(pixels, ox, oy, size, offset, top)
        _fill_front(pixels, ox, oy, size, offset, front)
        _fill_side(pixels, ox, oy, size, offset, side)
    _outline_cube(pixels, ox, oy, size, offset, outline)


def _fill_gear_body(pixels: List[List[Color]], cx: int, cy: int, r: int, color: Color) -> None:
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= (r - 1) ** 2:
                _put(pixels, x, y, color)


def _draw_teeth(pixels: List[List[Color]], cx: int, cy: int, r: int, color: Color, width: int) -> None:
    dirs = [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(-1,-1),(1,-1)]
    for dx, dy in dirs:
        for t in range(r, r + width + 1):
            _put(pixels, cx + dx * t, cy + dy * t, color)


def _punch_hole(pixels: List[List[Color]], cx: int, cy: int, bg: Color) -> None:
    for y in range(cy - 1, cy + 2):
        for x in range(cx - 1, cx + 2):
            _put(pixels, x, y, bg)


def _draw_gear(
    pixels: List[List[Color]],
    cx: int,
    cy: int,
    r: int,
    inner: Color,
    teeth: Color,
    bg: Color,
    *,
    hole: bool = False,
    teeth_width: int = 1,
) -> None:
    _fill_gear_body(pixels, cx, cy, r, inner)
    _draw_teeth(pixels, cx, cy, r, teeth, teeth_width)
    if hole:
        _punch_hole(pixels, cx, cy, bg)


def _cube_with_gear(
    bg: Color,
    front: Color,
    top: Color,
    side: Color,
    outline: Color,
    gear_inner: Color,
    gear_teeth: Color,
    *,
    wireframe: bool = False,
    hole: bool = False,
    teeth_width: int = 1,
) -> List[List[Color]]:
    pixels = _blank(bg)
    _draw_cube(pixels, front, top, side, outline, wireframe)
    _draw_gear(pixels, _GEAR_CX, _GEAR_CY, _GEAR_R, gear_inner, gear_teeth, bg, hole=hole, teeth_width=teeth_width)
    return pixels


def _save_icon(path: Path, pixels: List[List[Color]], scale: int) -> None:
    scaled = _scale_pixels(pixels, scale)
    _write_ico(path, scaled)


def build_icon_v1(path: Path, scale: int) -> None:
    pixels = _cube_with_gear(
        bg=(30, 30, 30, 255),
        front=(0, 0, 0, 0),
        top=(0, 0, 0, 0),
        side=(0, 0, 0, 0),
        outline=(255, 255, 255, 255),
        gear_inner=(30, 30, 30, 255),
        gear_teeth=(255, 255, 255, 255),
        wireframe=True,
    )
    _save_icon(path, pixels, scale)


def build_icon_v2(path: Path, scale: int) -> None:
    pixels = _cube_with_gear(
        bg=(20, 20, 20, 255),
        front=(60, 120, 200, 255),
        top=(90, 150, 220, 255),
        side=(40, 80, 160, 255),
        outline=(255, 255, 255, 255),
        gear_inner=(200, 200, 200, 255),
        gear_teeth=(255, 255, 255, 255),
    )
    _save_icon(path, pixels, scale)


def build_icon_v3(path: Path, scale: int) -> None:
    pixels = _cube_with_gear(
        bg=(20, 20, 20, 255),
        front=(60, 120, 200, 255),
        top=(110, 170, 240, 255),
        side=(40, 80, 160, 255),
        outline=(255, 255, 255, 255),
        gear_inner=(200, 200, 200, 255),
        gear_teeth=(255, 255, 255, 255),
        hole=True,
    )
    _save_icon(path, pixels, scale)


def build_icon_v4(path: Path, scale: int) -> None:
    pixels = _cube_with_gear(
        bg=(20, 20, 20, 255),
        front=(70, 130, 210, 255),
        top=(120, 180, 250, 255),
        side=(50, 90, 170, 255),
        outline=(255, 255, 255, 255),
        gear_inner=(210, 210, 210, 255),
        gear_teeth=(255, 255, 255, 255),
        hole=True,
        teeth_width=2,
    )
    _save_icon(path, pixels, scale)

_BUILDERS: Dict[str, Callable[[Path, int], None]] = {
    "v1": build_icon_v1,
    "v2": build_icon_v2,
    "v3": build_icon_v3,
    "v4": build_icon_v4,
}


def build_icon(path: Path, strategy: str = "v4", scale: int = 4) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    _BUILDERS[strategy](path, scale)
    return path


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("bin/AutoML.ico"))
    parser.add_argument("--strategy", choices=sorted(_BUILDERS), default="v4")
    parser.add_argument(
        "--scale",
        type=int,
        default=4,
        help="Scale factor applied to base 32x32 icon (default: 4 for 128x128)",
    )
    args = parser.parse_args()
    build_icon(args.output, args.strategy, scale=args.scale)
    print(f"Icon written to {args.output}")


if __name__ == "__main__":
    main()
