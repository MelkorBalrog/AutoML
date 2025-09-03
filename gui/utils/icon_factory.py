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

import tkinter as tk
from typing import Optional
import math


def _put_safe(img: tk.PhotoImage, color: str, x: int, y: int, size: int) -> None:
    """Draw a pixel only when coordinates fall inside the image bounds."""
    if 0 <= x < size and 0 <= y < size:
        img.put(color, (x, y))


def _draw_bug(img: tk.PhotoImage, c: str, outline: str, size: int) -> None:
    """Render a beetle-like bug icon with guarded pixel writes."""
    mid = size // 2
    body_top = 5
    body_bottom = size - 3
    rx = size // 2 - 3
    ry = (body_bottom - body_top) // 2
    cy = (body_top + body_bottom) // 2
    for y in range(body_top, body_bottom):
        for x in range(size):
            norm = ((x - mid) ** 2) / (rx * rx) + ((y - cy) ** 2) / (ry * ry)
            if norm <= 1:
                img.put(c, (x, y))
            if 1 <= norm <= 1.2:
                img.put(outline, (x, y))
    head_r = 3
    head_cy = body_top - head_r + 1
    for y in range(head_cy - head_r, head_cy + head_r + 1):
        for x in range(mid - head_r, mid + head_r + 1):
            dist = (x - mid) ** 2 + (y - head_cy) ** 2
            if dist <= head_r * head_r:
                _put_safe(img, c, x, y, size)
            if head_r * head_r <= dist <= (head_r + 1) * (head_r + 1):
                _put_safe(img, outline, x, y, size)
    for i, ly in enumerate([cy - 2, cy, cy + 2]):
        for dx in range(3):
            _put_safe(img, outline, mid - rx - dx, ly + (dx % 2 - 1), size)
            _put_safe(img, outline, mid + rx + dx, ly + (dx % 2 - 1), size)
    for x, y in [
        (mid - 1, head_cy - head_r - 1),
        (mid - 2, head_cy - head_r - 2),
        (mid + 1, head_cy - head_r - 1),
        (mid + 2, head_cy - head_r - 2),
    ]:
        _put_safe(img, outline, x, y, size)


def create_icon(
    shape: str,
    color: str = "black",
    bg: Optional[str] = None,
    size: int = 16,
) -> tk.PhotoImage:
    """Return a ``size``×``size`` :class:`tk.PhotoImage` for *shape*.

    Icons now have filled interiors and simple outlines so they look like
    miniature versions of the objects they represent. By default the returned
    image has a transparent background so the icons blend with any widget.
    The implementation is deliberately lightweight and only uses
    ``tk.PhotoImage`` drawing primitives so it works in the same environments
    as the previous icon helpers.

    Parameters
    ----------
    shape:
        The geometric shape to draw (e.g. ``"circle"``).
    color:
        Fill color for the shape.
    bg:
        Optional background color. When omitted the background is transparent.
    size:
        Width and height of the icon in pixels.
    """
    img = tk.PhotoImage(width=size, height=size)
    if bg:
        img.put(bg, to=(0, 0, size - 1, size - 1))
    c = color
    outline = "black"
    try:
        tr = int(c[1:3], 16)
        tg = int(c[3:5], 16)
        tb = int(c[5:7], 16)
    except (ValueError, IndexError):  # pragma: no cover - defensive
        tr = tg = tb = 0

    def _grad(x: int) -> str:
        """Return white → color gradient value for column *x*."""
        ratio = x / (size - 1)
        nr = int(255 * (1 - ratio) + tr * ratio)
        ng = int(255 * (1 - ratio) + tg * ratio)
        nb = int(255 * (1 - ratio) + tb * ratio)
        return f"#{nr:02x}{ng:02x}{nb:02x}"
    if shape == "circle":
        r = size // 2 - 3
        cx = cy = size // 2
        for y in range(size):
            for x in range(size):
                dist = (x - cx) ** 2 + (y - cy) ** 2
                if dist <= r * r:
                    img.put(c, (x, y))
                if r * r <= dist <= (r + 1) * (r + 1):
                    img.put(outline, (x, y))
    elif shape == "ellipse":
        rx = size // 2 - 2
        ry = size // 2 - 4
        cx = cy = size // 2
        for y in range(size):
            for x in range(size):
                norm = ((x - cx) ** 2) / (rx * rx) + ((y - cy) ** 2) / (ry * ry)
                if norm <= 1:
                    img.put(c, (x, y))
                if 1 <= norm <= 1.2:
                    img.put(outline, (x, y))
    elif shape == "human":
        cx = size // 2
        head_r = 3
        head_cy = 4
        for y in range(head_cy - head_r, head_cy + head_r + 1):
            for x in range(cx - head_r, cx + head_r + 1):
                dist = (x - cx) ** 2 + (y - head_cy) ** 2
                if dist <= head_r * head_r:
                    img.put(c, (x, y))
                if head_r * head_r <= dist <= (head_r + 1) * (head_r + 1):
                    img.put(outline, (x, y))
        # Draw limbs in black for better visibility regardless of the head color
        for y in range(head_cy + head_r, size - 3):
            img.put(outline, (cx, y))
        arm_y = head_cy + head_r + 2
        for x in range(cx - 4, cx + 5):
            img.put(outline, (x, arm_y))
        leg_start = size - 4
        for i in range(4):
            img.put(outline, (cx - i, leg_start + i))
            img.put(outline, (cx + i, leg_start + i))
    elif shape == "diamond":
        mid = size // 2
        for y in range(2, size - 2):
            span = mid - abs(mid - y)
            img.put(c, to=(mid - span, y, mid + span + 1, y + 1))
            img.put(outline, (mid - span, y))
            img.put(outline, (mid + span, y))
    elif shape == "rect":
        img.put(c, to=(3, 3, size - 3, size - 3))
        for x in range(3, size - 3):
            img.put(outline, (x, 3))
            img.put(outline, (x, size - 4))
        for y in range(3, size - 3):
            img.put(outline, (3, y))
            img.put(outline, (size - 4, y))
    elif shape == "parallelogram":
        offset = size // 4
        top = 3
        bottom = size - 3
        for y in range(top, bottom):
            t = (y - top) / (bottom - top - 1)
            x1 = int(3 + offset - offset * t)
            x2 = int(size - 3 - offset * t)
            img.put(c, to=(x1, y, x2, y + 1))
            if y in (top, bottom - 1):
                for x in range(x1, x2):
                    img.put(outline, (x, y))
            img.put(outline, (x1, y))
            img.put(outline, (x2 - 1, y))
    elif shape == "folder":
        img.put(c, to=(1, 5, size - 2, size - 2))
        img.put(c, to=(1, 3, size // 2, 5))
        for x in range(1, size - 1):
            img.put(outline, (x, 5))
            img.put(outline, (x, size - 2))
        for y in range(5, size - 1):
            img.put(outline, (1, y))
            img.put(outline, (size - 2, y))
        for x in range(1, size // 2):
            img.put(outline, (x, 3))
        for y in range(3, 5):
            img.put(outline, (1, y))
    elif shape == "arrow":
        mid = size // 2
        # Draw a thin horizontal shaft
        for x in range(2, size - 5):
            img.put(c, (x, mid))
        # Add a filled triangular arrow head on the right
        head = size - 5
        for i in range(5):
            x = head + i
            for y in range(mid - i, mid + i + 1):
                img.put(c, (x, y))
            img.put(outline, (x, mid - i))
            img.put(outline, (x, mid + i))
        img.put(outline, (size - 1, mid))
    elif shape == "relation":
        mid = size // 2
        # Draw a line with an open arrow head on the left. A previous revision
        # inadvertently inverted the arrow head so the tip appeared wide instead
        # of pointed. Draw the head with its tip at x=0.
        for x in range(4, size - 2):
            img.put(c, (x, mid))
        for i in range(4):
            img.put(c, (i, mid - i))
            img.put(c, (i, mid + i))
    elif shape == "triangle":
        mid = size // 2
        height = size - 4
        for y in range(height):
            span = (y * mid) // height
            img.put(c, to=(mid - span, 2 + y, mid + span + 1, 3 + y))
            img.put(outline, (mid - span, 2 + y))
            img.put(outline, (mid + span, 2 + y))
        for x in range(2, size - 2):
            img.put(outline, (x, height + 2))
    elif shape == "hazard":
        mid = size // 2
        height = size - 4
        for y in range(height):
            span = (y * mid) // height
            img.put(c, to=(mid - span, 2 + y, mid + span + 1, 3 + y))
            img.put(outline, (mid - span, 2 + y))
            img.put(outline, (mid + span, 2 + y))
        for x in range(2, size - 2):
            img.put(outline, (x, height + 2))
        for y in range(5, height):
            img.put(outline, (mid, y))
        for dy in range(height + 1, height + 3):
            img.put(outline, (mid, dy))
    elif shape == "clipboard":
        img.put(c, to=(2, 4, size - 2, size - 2))
        for x in range(2, size - 2):
            img.put(outline, (x, 4))
            img.put(outline, (x, size - 2))
        for y in range(4, size - 2):
            img.put(outline, (2, y))
            img.put(outline, (size - 2, y))
        for x in range(4, size - 4):
            img.put(c, (x, 2))
            img.put(outline, (x, 2))
            img.put(outline, (x, 4))
        img.put(outline, (4, 2))
        img.put(outline, (size - 5, 2))
        for i in range(3):
            img.put(outline, (5 + i, 9 + i))
        for i in range(5):
            img.put(outline, (8 + i, 11 - i))
    elif shape == "shield":
        mid = size // 2
        height = size - 4
        for y in range(height):
            if y < 4:
                span = mid - 1
            else:
                span = max(mid - (y - 3), 0)
            img.put(c, to=(mid - span, 2 + y, mid + span + 1, 3 + y))
            img.put(outline, (mid - span, 2 + y))
            img.put(outline, (mid + span, 2 + y))
        img.put(outline, (mid, size - 2))
    elif shape == "bug":
        _draw_bug(img, c, outline, size)
    elif shape == "building":
        img.put(c, to=(3,3,size-3,size-1))
        for x in range(3, size-3):
            img.put(outline, (x,3))
            img.put(outline, (x,size-2))
        for y in range(3, size-2):
            img.put(outline, (3,y))
            img.put(outline, (size-4,y))
        for x in range(5, size-5, 4):
            for y in range(5, size-4, 4):
                img.put(bg or "white", to=(x,y,x+2,y+2))
                for i in range(3):
                    img.put(outline,(x+i,y))
                    img.put(outline,(x+i,y+2))
                for j in range(3):
                    img.put(outline,(x,y+j))
                    img.put(outline,(x+2,y+j))
    elif shape == "department":
        img.put(c, to=(3,5,size-3,size-1))
        for x in range(3, size-3):
            img.put(outline,(x,5))
            img.put(outline,(x,size-2))
        for y in range(5, size-2):
            img.put(outline,(3,y))
            img.put(outline,(size-4,y))
        pole = size-5
        for y in range(1,5):
            img.put(outline,(pole,y))
        img.put(c, to=(pole,1,size-2,3))
        for x in range(pole, size-2):
            img.put(outline,(x,1))
            img.put(outline,(x,3))
        img.put(outline,(pole,2))
        img.put(outline,(size-2,2))
    elif shape == "scroll":
        img.put(c, to=(4,3,size-4,size-3))
        for x in range(4,size-4):
            img.put(outline,(x,3))
            img.put(outline,(x,size-3))
        for y in range(3,size-3):
            img.put(outline,(4,y))
            img.put(outline,(size-4,y))
        for y in range(3,size-3):
            img.put(c,(2,y)); img.put(c,(size-3,y))
            img.put(outline,(2,y)); img.put(outline,(size-3,y))
    elif shape == "scale":
        mid=size//2
        for y in range(3,size-3):
            img.put(outline,(mid,y))
        arm_y=6
        for x in range(mid-6,mid+7):
            img.put(outline,(x,arm_y))
        for dx in range(4):
            img.put(outline,(mid-4+dx,arm_y+dx+1))
            img.put(outline,(mid+4-dx,arm_y+dx+1))
        for x in range(mid-6,mid-1):
            for y in range(arm_y+5,arm_y+7):
                img.put(c,(x,y))
                img.put(outline,(x,y))
        for x in range(mid+1,mid+6):
            for y in range(arm_y+5,arm_y+7):
                img.put(c,(x,y))
                img.put(outline,(x,y))
    elif shape == "compass":
        mid=size//2
        r=size//2-2
        for y in range(size):
            for x in range(size):
                d=(x-mid)**2+(y-mid)**2
                if d<=r*r:
                    img.put(c,(x,y))
                if r*r<=d<= (r+1)*(r+1):
                    img.put(outline,(x,y))
        for y in range(mid):
            img.put(outline,(mid,y))
        for i in range(3):
            img.put(outline,(mid-i,i))
            img.put(outline,(mid+i,i))
    elif shape == "ribbon":
        mid=size//2
        r=size//2-3
        cy=mid-2
        for y in range(size):
            for x in range(size):
                d=(x-mid)**2+(y-cy)**2
                if d<=r*r:
                    img.put(c,(x,y))
                if r*r<=d<= (r+1)*(r+1):
                    img.put(outline,(x,y))
        for i in range(3):
            img.put(c,(mid-r+i,cy+r))
            img.put(c,(mid+r-i,cy+r))
            img.put(outline,(mid-r+i,cy+r))
            img.put(outline,(mid+r-i,cy+r))
    elif shape == "chart":
        heights=[8,12,5]
        for i,h in enumerate(heights):
            x1=2+i*5
            for x in range(x1,x1+3):
                for y in range(size-2-h,size-2):
                    img.put(c,(x,y))
                img.put(outline,(x,size-2-h))
                img.put(outline,(x,size-2))
            for y in range(size-2-h,size-2):
                img.put(outline,(x1,y))
                img.put(outline,(x1+2,y))
    elif shape == "shield_check":
        mid=size//2
        for y in range(2,size-2):
            span=mid-1 if y<5 else max(mid-(y-4),0)
            img.put(c,to=(mid-span,y,mid+span+1,y+1))
            img.put(outline,(mid-span,y))
            img.put(outline,(mid+span,y))
        img.put(outline,(mid,size-2))
        for i in range(3):
            img.put(outline,(4+i,9+i))
        for i in range(5):
            img.put(outline,(7+i,13-i))
    elif shape == "gear":
        mid=size//2
        r1=size//2-1
        r2=int(r1*0.7)
        points=[]
        teeth=8
        for i in range(teeth*2):
            ang=math.radians(360/(teeth*2)*i)
            rad=r1 if i%2==0 else r2
            x=int(mid+rad*math.cos(ang))
            y=int(mid+rad*math.sin(ang))
            points.append((x,y))
        for y in range(size):
            xs=[]
            for i in range(len(points)):
                x1,y1=points[i]; x2,y2=points[(i+1)%len(points)]
                if y1==y2 or y<min(y1,y2) or y>=max(y1,y2):
                    continue
                x=x1+(y-y1)*(x2-x1)/(y2-y1)
                xs.append(int(x))
            xs.sort()
            for j in range(0,len(xs),2):
                img.put(c,to=(xs[j],y,xs[j+1]+1,y+1))
        for x,y in points:
            img.put(outline,(x,y))
    elif shape == "wrench":
        mid = size // 2
        bgc = bg or "white"
        # --- Gear ring -------------------------------------------------
        r_out = size // 2 - 1
        r_root = int(r_out * 0.82)
        pts = []
        teeth = 8
        for i in range(teeth * 2):
            ang = math.radians(360 / (teeth * 2) * i)
            rad = r_out if i % 2 == 0 else r_root
            x = mid + rad * math.cos(ang)
            y = mid + rad * math.sin(ang)
            pts.append((x, y))
        for y in range(size):
            xs = []
            for i in range(len(pts)):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % len(pts)]
                if y1 == y2 or y < min(y1, y2) or y >= max(y1, y2):
                    continue
                x = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                xs.append(int(x))
            xs.sort()
            for j in range(0, len(xs), 2):
                for x in range(xs[j], xs[j + 1] + 1):
                    img.put(_grad(x), (x, y))
        for x, y in pts:
            img.put(outline, (int(round(x)), int(round(y))))
        hole = int(r_out * 0.62)
        for y in range(mid - hole, mid + hole + 1):
            for x in range(mid - hole, mid + hole + 1):
                if (x - mid) ** 2 + (y - mid) ** 2 <= hole * hole:
                    img.put(bgc, (x, y))
        # --- Wrench inside the gear ------------------------------------
        wr = hole * 0.95
        sf = wr / (size / 2)
        head_cy = 5
        head_r = 5
        inner = head_r - 2
        notch_start = mid + 1

        def _wpt(px: float, py: float) -> tuple[float, float]:
            return (px - mid) * sf + mid, (py - mid) * sf + mid

        outer = [
            _wpt(mid - 1, size - 2),
            _wpt(mid - 1, head_cy + head_r),
            _wpt(mid - head_r, head_cy + head_r),
            _wpt(mid - head_r, head_cy - head_r),
            _wpt(mid + head_r, head_cy - head_r),
            _wpt(notch_start, head_cy - 1),
            _wpt(notch_start, head_cy + 1),
            _wpt(mid + head_r, head_cy + head_r),
            _wpt(mid + 1, head_cy + head_r),
            _wpt(mid + 1, size - 2),
        ]
        hole_pts = [
            _wpt(mid - inner, head_cy + inner),
            _wpt(mid - inner, head_cy - inner),
            _wpt(mid + inner, head_cy - inner),
            _wpt(notch_start, head_cy - 1),
            _wpt(notch_start, head_cy + 1),
            _wpt(mid + inner, head_cy + inner),
        ]
        theta = -math.pi / 4
        ct, st = math.cos(theta), math.sin(theta)

        def _rot(pt: tuple[float, float]) -> tuple[float, float]:
            px, py = pt
            dx, dy = px - mid, py - mid
            return mid + dx * ct - dy * st, mid + dx * st + dy * ct

        outer = [_rot(p) for p in outer]
        hole_pts = [_rot(p) for p in hole_pts]

        for y in range(size):
            xs = []
            for i in range(len(outer)):
                x1, y1 = outer[i]
                x2, y2 = outer[(i + 1) % len(outer)]
                if y1 == y2 or y < min(y1, y2) or y >= max(y1, y2):
                    continue
                x = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                xs.append(int(x))
            xs.sort()
            for j in range(0, len(xs), 2):
                for x in range(xs[j], xs[j + 1] + 1):
                    img.put(_grad(x), (x, y))
        for x, y in outer:
            img.put(outline, (int(round(x)), int(round(y))))

        for y in range(size):
            xs = []
            for i in range(len(hole_pts)):
                x1, y1 = hole_pts[i]
                x2, y2 = hole_pts[(i + 1) % len(hole_pts)]
                if y1 == y2 or y < min(y1, y2) or y >= max(y1, y2):
                    continue
                x = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                xs.append(int(x))
            xs.sort()
            for j in range(0, len(xs), 2):
                for x in range(xs[j], xs[j + 1] + 1):
                    img.put(bgc, (x, y))
    elif shape == "steering":
        mid=size//2
        r=size//2-2
        for y in range(size):
            for x in range(size):
                d=(x-mid)**2+(y-mid)**2
                if d<=r*r:
                    img.put(c,(x,y))
                if r*r<=d<= (r+1)*(r+1):
                    img.put(outline,(x,y))
        inner=int(r*0.4)
        for y in range(size):
            for x in range(size):
                d=(x-mid)**2+(y-mid)**2
                if d<=inner*inner:
                    img.put(bg or "white",(x,y))
                    if inner*inner<=d<= (inner+1)*(inner+1):
                        img.put(outline,(x,y))
        for x in range(mid-r,mid+r+1):
            img.put(outline,(x,mid))
        for y in range(mid-r,mid+r+1):
            img.put(outline,(mid,y))
    elif shape == "cylinder":
        # Represent a database cylinder with elliptical caps and a filled body
        left, right = 2, size - 2
        top, bottom = 4, size - 4
        cx = size // 2
        rx = (right - left) // 2
        ry = 2

        # Fill the central body
        img.put(c, to=(left, top, right, bottom))

        # Fill the top ellipse
        for y in range(top - ry, top + 1):
            for x in range(left, right):
                norm = ((x - cx) ** 2) / (rx * rx) + ((y - top) ** 2) / (ry * ry)
                if norm <= 1:
                    img.put(c, (x, y))

        # Fill the bottom ellipse
        for y in range(bottom, bottom + ry + 1):
            for x in range(left, right):
                norm = ((x - cx) ** 2) / (rx * rx) + ((y - bottom) ** 2) / (ry * ry)
                if norm <= 1:
                    img.put(c, (x, y))

        # Draw the outlines for the ellipses
        for x in range(left, right):
            y = int(ry * math.sqrt(max(0, 1 - ((x - cx) ** 2) / (rx * rx))))
            img.put(outline, (x, top - y))
            img.put(outline, (x, top + y))
            img.put(outline, (x, bottom - y))
            img.put(outline, (x, bottom + y))

        # Draw the vertical side outlines
        for y in range(top, bottom):
            img.put(outline, (left, y))
            img.put(outline, (right - 1, y))
    elif shape == "document":
        img.put(c, to=(2, 2, size - 2, size - 2))
        fold = bg or "white"
        for i in range(4):
            img.put(fold, to=(size - 6 + i, 2, size - 2, 6 - i))
        for x in range(2, size - 2):
            img.put(outline, (x, 2))
            img.put(outline, (x, size - 2))
        for y in range(2, size - 2):
            img.put(outline, (2, y))
            img.put(outline, (size - 2, y))
    elif shape == "action":
        # Outline rectangle with an internal arrow to hint at behaviour
        for x in range(2, size - 2):
            img.put(outline, (x, 2))
            img.put(outline, (x, size - 2))
        for y in range(2, size - 2):
            img.put(outline, (2, y))
            img.put(outline, (size - 2, y))
        mid = size // 2
        for x in range(4, size - 6):
            img.put(c, (x, mid))
        head = size - 6
        for i in range(3):
            for y in range(mid - i, mid + i + 1):
                img.put(c, (head + i, y))
    elif shape == "bar":
        top = size // 2 - 2
        img.put(c, to=(2, top, size - 2, top + 4))
        for x in range(2, size - 2):
            img.put(outline, (x, top))
            img.put(outline, (x, top + 3))
    elif shape == "nested":
        for x in range(1, size - 1):
            img.put(outline, (x, 1))
            img.put(outline, (x, size - 2))
        for y in range(1, size - 1):
            img.put(outline, (1, y))
            img.put(outline, (size - 2, y))
        for x in range(4, size - 4):
            img.put(outline, (x, 4))
            img.put(outline, (x, size - 5))
        for y in range(4, size - 4):
            img.put(outline, (4, y))
            img.put(outline, (size - 5, y))
    elif shape == "hexagon":
        mid = size // 2
        for y in range(2, size - 2):
            if y < 4:
                span = y - 2
            elif y > size - 5:
                span = size - 3 - y
            else:
                span = mid - 2
            img.put(c, to=(mid - span, y, mid + span + 1, y + 1))
            img.put(outline, (mid - span, y))
            img.put(outline, (mid + span, y))
    elif shape == "trapezoid":
        max_offset = 4
        for y in range(2, size - 2):
            offset = max_offset * (y - 2) // (size - 4)
            img.put(c, to=(2 + offset, y, size - 2 - offset, y + 1))
            img.put(outline, (2 + offset, y))
            img.put(outline, (size - 3 - offset, y))
    elif shape == "component":
        img.put(c, to=(3, 3, size - 3, size - 3))
        for x in range(3, size - 3):
            img.put(outline, (x, 3))
            img.put(outline, (x, size - 4))
        for y in range(3, size - 3):
            img.put(outline, (3, y))
            img.put(outline, (size - 4, y))
        # side tabs
        img.put(c, to=(0, 5, 3, 7))
        img.put(c, to=(0, 9, 3, 11))
        for x in range(0, 3):
            img.put(outline, (x, 5))
            img.put(outline, (x, 6))
            img.put(outline, (x, 7))
            img.put(outline, (x, 9))
            img.put(outline, (x, 10))
            img.put(outline, (x, 11))
    elif shape == "testsuite":
        img.put(c, to=(3, 3, size - 3, size - 3))
        for x in range(3, size - 3):
            img.put(outline, (x, 3))
            img.put(outline, (x, size - 4))
        for y in range(3, size - 3):
            img.put(outline, (3, y))
            img.put(outline, (size - 4, y))
        mid = size // 2
        for x in range(3, size - 3):
            img.put(outline, (x, mid))
        for y in range(3, size - 3):
            img.put(outline, (mid, y))
    elif shape == "vehicle":
        # Draw a small car silhouette with a sloped roof and wheels
        body_top = size - 6
        body_bottom = size - 3
        img.put(c, to=(2, body_top, size - 2, body_bottom))
        for x in range(2, size - 2):
            img.put(outline, (x, body_top))
            img.put(outline, (x, body_bottom - 1))
        for y in range(body_top, body_bottom):
            img.put(outline, (2, y))
            img.put(outline, (size - 3, y))
        roof_top = body_top - 3
        for y in range(roof_top, body_top):
            offset = body_top - y
            img.put(c, to=(2 + offset, y, size - 2 - offset, y + 1))
            for x in range(2 + offset, size - 2 - offset):
                if y == roof_top:
                    img.put(outline, (x, y))
            img.put(outline, (2 + offset, y))
            img.put(outline, (size - 3 - offset, y))
        wheel_y = body_bottom - 1
        for cx in (4, size - 5):
            for dx in (-1, 0, 1):
                for dy in (0, 1):
                    if dx * dx + dy * dy <= 1:
                        img.put(outline, (cx + dx, wheel_y + dy))
    elif shape == "fleet":
        # Draw two overlapping cars to represent a fleet
        for dx, dy in ((-2, -2), (0, 0)):
            body_top = size - 6 + dy
            body_bottom = size - 3 + dy
            img.put(c, to=(2 + dx, body_top, size - 2 + dx, body_bottom))
            for x in range(2 + dx, size - 2 + dx):
                img.put(outline, (x, body_top))
                img.put(outline, (x, body_bottom - 1))
            for y in range(body_top, body_bottom):
                img.put(outline, (2 + dx, y))
                img.put(outline, (size - 3 + dx, y))
            roof_top = body_top - 3
            for y in range(roof_top, body_top):
                offset = body_top - y
                img.put(c, to=(2 + dx + offset, y, size - 2 + dx - offset, y + 1))
                for x in range(2 + dx + offset, size - 2 + dx - offset):
                    if y == roof_top:
                        img.put(outline, (x, y))
                img.put(outline, (2 + dx + offset, y))
                img.put(outline, (size - 3 + dx - offset, y))
            wheel_y = body_bottom - 1
            for cx in (4 + dx, size - 5 + dx):
                for dx2 in (-1, 0, 1):
                    for dy2 in (0, 1):
                        if dx2 * dx2 + dy2 * dy2 <= 1:
                            img.put(outline, (cx + dx2, wheel_y + dy2))
    elif shape == "pentagon":
        mid = size // 2
        for y in range(2, size - 2):
            if y < 6:
                span = (y - 2) * (mid - 2) // 4
                left = mid - span
                right = mid + span + 1
            else:
                left = 2
                right = size - 2
            img.put(c, to=(left, y, right, y + 1))
            img.put(outline, (left, y))
            img.put(outline, (right - 1, y))
        for x in range(2, size - 2):
            img.put(outline, (x, size - 3))
    elif shape == "star":
        mid = size // 2
        for i in range(size):
            img.put(c, (mid, i))
            img.put(c, (i, mid))
            img.put(c, (i, i))
            img.put(c, (i, size - i - 1))
            img.put(outline, (mid, i))
            img.put(outline, (i, mid))
            img.put(outline, (i, i))
            img.put(outline, (i, size - i - 1))
    elif shape == "minus":
        mid = size // 2
        for x in range(3, size - 3):
            img.put(c, (x, mid))
        for x in range(3, size - 3):
            img.put(outline, (x, mid - 1))
            img.put(outline, (x, mid + 1))
    elif shape == "plus":
        mid = size // 2
        for x in range(3, size - 3):
            img.put(c, (x, mid))
        for y in range(3, size - 3):
            img.put(c, (mid, y))
        for x in range(3, size - 3):
            img.put(outline, (x, mid - 1))
            img.put(outline, (x, mid + 1))
        for y in range(3, size - 3):
            img.put(outline, (mid - 1, y))
            img.put(outline, (mid + 1, y))
    elif shape == "cross":
        for i in range(3, size - 3):
            img.put(c, (i, i))
            img.put(c, (i, size - i - 1))
            img.put(outline, (i, i))
            img.put(outline, (i, size - i - 1))
    elif shape == "gear":
        mid = size // 2
        r = size // 2 - 4
        for y in range(size):
            for x in range(size):
                dist = (x - mid) ** 2 + (y - mid) ** 2
                if dist <= r * r:
                    img.put(c, (x, y))
                if r * r <= dist <= (r + 1) * (r + 1):
                    img.put(outline, (x, y))
        for t in (-r, r):
            for x in range(mid - 1, mid + 2):
                img.put(c, (x, mid + t))
                img.put(outline, (x, mid + t))
            for y in range(mid - 1, mid + 2):
                img.put(c, (mid + t, y))
                img.put(outline, (mid + t, y))
    elif shape == "sigma":
        for x in range(3, size - 3):
            img.put(c, (x, 3))
            img.put(c, (x, size - 4))
            img.put(outline, (x, 3))
            img.put(outline, (x, size - 4))
        for i in range(6):
            img.put(c, (3 + i, 3 + i))
            img.put(c, (size - 4 - i, 3 + i))
            img.put(outline, (3 + i, 3 + i))
            img.put(outline, (size - 4 - i, 3 + i))
    elif shape == "disk":
        img.put(c, to=(2, 2, size - 2, size - 2))
        if bg:
            img.put(bg, to=(size - 6, 2, size - 2, 6))
            img.put(bg, to=(3, 3, size - 3, 6))
        for x in range(2, size - 2):
            img.put(outline, (x, 2))
            img.put(outline, (x, size - 2))
        for y in range(2, size - 2):
            img.put(outline, (2, y))
            img.put(outline, (size - 2, y))
    elif shape == "neural":
        nodes_left = [(4, 4), (4, 12)]
        nodes_mid = [(8, 4), (8, 12)]
        node_out = (12, 8)

        def draw_node(x: int, y: int) -> None:
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx * dx + dy * dy <= 1:
                        img.put(outline, (x + dx, y + dy))

        def draw_line(p1, p2) -> None:
            x1, y1 = p1
            x2, y2 = p2
            steps = max(abs(x2 - x1), abs(y2 - y1))
            for i in range(steps + 1):
                x = int(round(x1 + (x2 - x1) * i / steps))
                y = int(round(y1 + (y2 - y1) * i / steps))
                img.put(outline, (x, y))

        for s in nodes_left:
            for h in nodes_mid:
                draw_line(s, h)
        for h in nodes_mid:
            draw_line(h, node_out)
        for p in nodes_left + nodes_mid + [node_out]:
            draw_node(*p)
    elif shape == "hexagon":
        mid = size // 2
        for y in range(3, size - 3):
            offset = abs(mid - y) // 2
            start = 3 + offset
            end = size - 3 - offset
            img.put(c, to=(start, y, end, y + 1))
            img.put(outline, (start, y))
            img.put(outline, (end - 1, y))
        for x in range(4, size - 4):
            img.put(outline, (x, 3))
            img.put(outline, (x, size - 4))
    elif shape == "test":
        img.put(c, to=(3, 3, size - 3, size - 3))
        for x in range(3, size - 3):
            img.put(outline, (x, 3))
            img.put(outline, (x, size - 4))
        for y in range(3, size - 3):
            img.put(outline, (3, y))
            img.put(outline, (size - 4, y))
        mid = size // 2
        for x in range(4, size - 4):
            img.put(outline, (x, mid))
        for y in range(4, size - 4):
            img.put(outline, (mid, y))
    elif shape == "star":
        points = [
            (8, 3),
            (10, 5),
            (13, 5),
            (11, 8),
            (13, 11),
            (10, 11),
            (8, 13),
            (6, 11),
            (3, 11),
            (5, 8),
            (3, 5),
            (6, 5),
        ]
        for y in range(3, 13):
            xs = []
            for i in range(len(points)):
                x1, y1 = points[i]
                x2, y2 = points[(i + 1) % len(points)]
                if y1 == y2:
                    continue
                if y < min(y1, y2) or y >= max(y1, y2):
                    continue
                x = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                xs.append(int(x))
            xs.sort()
        for j in range(0, len(xs), 2):
            img.put(c, to=(xs[j], y, xs[j + 1] + 1, y + 1))
        for x, y in points:
            img.put(outline, (x, y))
    elif shape == "ring":
        # Draw a circular ring to represent a connection port
        cx = cy = size // 2
        outer = size // 2 - 2
        inner = outer - 3
        for y in range(size):
            for x in range(size):
                dist = (x - cx) ** 2 + (y - cy) ** 2
                if inner * inner <= dist <= outer * outer:
                    img.put(c, (x, y))
                if outer * outer <= dist <= (outer + 1) * (outer + 1):
                    img.put(outline, (x, y))
                if inner * inner <= dist <= (inner + 1) * (inner + 1):
                    img.put(outline, (x, y))
    elif shape == "usecase_diag":
        # Stick figure and ellipse to suggest a use case diagram
        cx = 4
        head_r = 2
        head_cy = 4
        for y in range(head_cy - head_r, head_cy + head_r + 1):
            for x in range(cx - head_r, cx + head_r + 1):
                dist = (x - cx) ** 2 + (y - head_cy) ** 2
                if dist <= head_r * head_r:
                    img.put(c, (x, y))
                if head_r * head_r <= dist <= (head_r + 1) * (head_r + 1):
                    img.put(outline, (x, y))
        # Draw stick figure limbs in black for clearer contrast
        for y in range(head_cy + head_r, size - 3):
            img.put(outline, (cx, y))
        arm_y = head_cy + head_r + 1
        for x in range(cx - 2, cx + 3):
            img.put(outline, (x, arm_y))
        leg_start = size - 4
        for i in range(3):
            img.put(outline, (cx - i, leg_start + i))
            img.put(outline, (cx + i, leg_start + i))
        rx = 4
        ry = 3
        ecx = size - 5
        ecy = size // 2
        for y in range(ecy - ry, ecy + ry + 1):
            for x in range(ecx - rx, ecx + rx + 1):
                norm = ((x - ecx) ** 2) / (rx * rx) + ((y - ecy) ** 2) / (ry * ry)
                if norm <= 1:
                    img.put(c, (x, y))
                if 1 <= norm <= 1.2:
                    img.put(outline, (x, y))
    elif shape == "activity_diag":
        # Simple flow arrow with a diamond decision
        mid = size // 2
        for x in range(2, size - 5):
            img.put(c, (x, mid))
        head = size - 5
        for i in range(4):
            img.put(c, (head + i, mid - i))
            img.put(c, (head + i, mid + i))
        dmid = size // 2
        for i in range(3):
            img.put(c, (head - 3 + i, dmid - i))
            img.put(c, (head - 3 + i, dmid + i))
            img.put(c, (head - 5 + i, dmid))
    elif shape == "block_diag":
        for x in range(2, size - 2):
            img.put(outline, (x, 2))
            img.put(outline, (x, size - 2))
        for y in range(2, size - 2):
            img.put(outline, (2, y))
            img.put(outline, (size - 2, y))
        for y in range(4, size - 4, 6):
            for x in range(4, size - 4, 6):
                img.put(c, to=(x, y, x + 3, y + 3))
    elif shape == "ibd_diag":
        for x in range(2, size - 2):
            img.put(outline, (x, 2))
            img.put(outline, (x, size - 2))
        for y in range(2, size - 2):
            img.put(outline, (2, y))
            img.put(outline, (size - 2, y))
        img.put(c, to=(4, 4, 7, 7))
        img.put(c, to=(9, 9, 12, 12))
        for i in range(3):
            img.put(c, (7 + i, 6))
            img.put(c, (7 + i, 9))
    elif shape == "puzzle":
        # Simple jigsaw puzzle piece for "Part" elements
        img.put(c, to=(3, 5, size - 3, size - 3))
        # top tab
        for y in range(0, 5):
            for x in range(6, 10):
                img.put(c, (x, y))
        # right socket
        for y in range(7, 11):
            for x in range(size - 3, size):
                img.put(bg or "white", (x, y))
        # outlines
        for x in range(3, size - 3):
            img.put(outline, (x, 5))
            img.put(outline, (x, size - 3))
        for y in range(5, size - 3):
            img.put(outline, (3, y))
            img.put(outline, (size - 3, y))
        for x in range(6, 10):
            img.put(outline, (x, 0))
            img.put(outline, (x, 4))
        for y in range(7, 11):
            img.put(outline, (size - 1, y))
            img.put(outline, (size - 4, y))
    else:
        img.put(c, to=(2, 2, size - 2, size - 2))
        for x in range(2, size - 2):
            img.put(outline, (x, 2))
            img.put(outline, (x, size - 2))
        for y in range(2, size - 2):
            img.put(outline, (2, y))
            img.put(outline, (size - 2, y))
    return img
