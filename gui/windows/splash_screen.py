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
import math
import random
from dataclasses import dataclass


@dataclass
class StarField:
    """Render a simple star field on a Tkinter canvas."""

    canvas: tk.Canvas
    width: int
    height: int
    star_count: int = 50

    def draw(self) -> None:
        """Draw randomly positioned stars across the sky region."""
        sky_limit = int(self.height * 0.55)
        for _ in range(self.star_count):
            x = random.randint(0, self.width)
            y = random.randint(0, sky_limit)
            size = random.choice((1, 2))
            self.canvas.create_oval(
                x,
                y,
                x + size,
                y + size,
                fill="white",
                outline="",
                tags="star",
            )


class SplashScreen(tk.Toplevel):
    """Simple splash screen with rotating cube and gear."""

    def __init__(
        self,
        master,
        version: str = "Unknown",
        author: str = "Your Name",
        email: str = "email@example.com",
        linkedin: str = "https://www.linkedin.com/in/yourprofile",
        duration: int = 3000,
        on_close=None,
    ):
        super().__init__(master)
        self.duration = duration
        self.overrideredirect(True)
        self._on_close = on_close

        # Track whether transparency is supported
        try:
            self.attributes("-alpha", 0.0)
            self._alpha_supported = True
        except tk.TclError:
            self._alpha_supported = False

        # Shadow window to create simple 3D effect
        self.shadow = tk.Toplevel(master)
        self.shadow.overrideredirect(True)
        self.shadow.configure(bg="black")
        self._shadow_alpha_target = 0.3
        try:
            # Start fully transparent for fade in
            self.shadow.attributes("-alpha", 0.0)
        except tk.TclError:
            self._shadow_alpha_target = None

        self.canvas_size = 300
        # Black background so colors pop
        self.canvas = tk.Canvas(
            self,
            width=self.canvas_size,
            height=self.canvas_size,
            highlightthickness=0,
            bg="black",
        )
        self.canvas.pack()
        self._draw_gradient()
        self._draw_stars()
        self._draw_floor()
        self._center()
        # Initialize cube geometry
        self.angle = 0.0
        self.vertices = [
            (-1, -1, -1),
            (1, -1, -1),
            (1, 1, -1),
            (-1, 1, -1),
            (-1, -1, 1),
            (1, -1, 1),
            (1, 1, 1),
            (-1, 1, 1),
        ]
        self.edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),
            (4, 5), (5, 6), (6, 7), (7, 4),
            (0, 4), (1, 5), (2, 6), (3, 7),
        ]
        self.faces = [
            (0, 1, 2, 3),
            (4, 5, 6, 7),
            (0, 1, 5, 4),
            (2, 3, 7, 6),
            (1, 2, 6, 5),
            (0, 3, 7, 4),
        ]
        self._draw_title()

        # Version and author info at top right
        info_text = f"v{version}\n{author}\n{email}\n{linkedin}"
        self.canvas.create_text(
            self.canvas_size - 10,
            10,
            text=info_text,
            anchor="ne",
            justify="right",
            font=("Helvetica", 9),
            fill="white",
        )
        # Start animation and fade-in effect
        self.after(10, self._animate)
        self.after(10, self._fade_in)

    def close(self):
        """Begin fade-out sequence and invoke on_close callback when done."""
        if getattr(self, "_alpha_supported", False):
            self._fade_out()
        else:
            self._close()

    def _fade_in(self):
        if not getattr(self, "_alpha_supported", False):
            if self.duration > 0:
                self.after(self.duration, self._close)
            return
        alpha = min(self.attributes("-alpha") + 0.05, 1.0)
        self.attributes("-alpha", alpha)
        if self._shadow_alpha_target is not None:
            try:
                self.shadow.attributes("-alpha", alpha * self._shadow_alpha_target)
            except tk.TclError:
                pass
        if alpha < 1.0:
            self.after(50, self._fade_in)
        else:
            if self.duration > 0:
                self.after(self.duration, self._fade_out)

    def _fade_out(self):
        if not getattr(self, "_alpha_supported", False):
            self._close()
            return
        alpha = max(self.attributes("-alpha") - 0.05, 0.0)
        self.attributes("-alpha", alpha)
        if self._shadow_alpha_target is not None:
            try:
                self.shadow.attributes("-alpha", alpha * self._shadow_alpha_target)
            except tk.TclError:
                pass
        if alpha > 0.0:
            self.after(50, self._fade_out)
        else:
            self._close()

    def _center(self):
        self.update_idletasks()
        w = self.canvas_size
        h = self.canvas_size
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        # Position shadow slightly offset from the splash window
        self.shadow.geometry(f"{w}x{h}+{x + 5}+{y + 5}")
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.shadow.lower(self)

    def _draw_gradient(self):
        """Fill the background with pure black for a void effect."""
        self.canvas.create_rectangle(
            0,
            0,
            self.canvas_size,
            self.canvas_size,
            fill="black",
            outline="",
            tags="void_bg",
        )

    def _draw_stars(self) -> None:
        """No stars in the void."""
        return
    def _draw_cloud(self):
        """Draw a small turquoise-magenta-white cloud on the sky."""
        cx, cy = 80, 80
        ovals = [
            (cx - 40, cy - 20, cx + 40, cy + 20),
            (cx - 20, cy - 30, cx + 60, cy + 10),
            (cx - 60, cy - 30, cx + 20, cy + 10),
        ]
        for x1, y1, x2, y2 in ovals:
            self.canvas.create_oval(
                x1, y1, x2, y2, fill="#40E0D0", outline="#FF00FF", width=2
            )
        # subtle white highlight
        self.canvas.create_oval(
            cx - 30,
            cy - 20,
            cx + 20,
            cy + 10,
            fill="white",
            outline="",
            stipple="gray50",
        )

    def _draw_title(self) -> None:
        """Render project title with a subtle white shadow."""
        x = self.canvas_size / 2
        y = self.canvas_size - 40
        main_text = "Automotive Modeling Language"
        sub_text = "by Karel Capek Robotics"
        title_font = ("Helvetica", 14, "bold")
        sub_font = ("Helvetica", 12, "bold")
        offset = 1

        # White shadow drawn slightly offset behind the main text
        self.canvas.create_text(
            x + offset,
            y + offset,
            text=main_text,
            font=title_font,
            fill="white",
            tags="title_shadow",
        )
        self.canvas.create_text(
            x + offset,
            y + 20 + offset,
            text=sub_text,
            font=sub_font,
            fill="white",
            tags="title_shadow",
        )

        # Foreground text in bold black
        self.canvas.create_text(
            x,
            y,
            text=main_text,
            font=title_font,
            fill="black",
            tags="title_text",
        )
        self.canvas.create_text(
            x,
            y + 20,
            text=sub_text,
            font=sub_font,
            fill="black",
            tags="title_text",
        )

    def _draw_floor(self):
        """Draw a white horizon line against the void."""
        horizon = int(self.canvas_size * 0.55)
        self.canvas.create_line(
            0,
            horizon,
            self.canvas_size,
            horizon,
            fill="white",
            tags="horizon",
        )

    def _project(self, x, y, z):
        """Project 3D point onto 2D canvas."""
        distance = 5
        factor = self.canvas_size / (2 * (z + distance))
        x = x * factor + self.canvas_size / 2
        y = y * factor + self.canvas_size / 2
        return x, y

    def _shade_color(self, diffuse: float) -> str:
        """Return a teal shade adjusted by *diffuse* light value."""
        base = (0, 120, 120)
        r = int(base[0] + (255 - base[0]) * diffuse)
        g = int(base[1] + (255 - base[1]) * diffuse)
        b = int(base[2] + (255 - base[2]) * diffuse)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _face_data(
        self, face, points, points3d, light_dir, view_dir
    ):
        """Return drawing data for a single cube face."""
        pts2d = [points[i] for i in face]
        pts3d = [points3d[i] for i in face]
        z_avg = sum(p[2] for p in pts3d) / len(pts3d)
        u = (
            pts3d[1][0] - pts3d[0][0],
            pts3d[1][1] - pts3d[0][1],
            pts3d[1][2] - pts3d[0][2],
        )
        v = (
            pts3d[2][0] - pts3d[0][0],
            pts3d[2][1] - pts3d[0][1],
            pts3d[2][2] - pts3d[0][2],
        )
        nx = u[1] * v[2] - u[2] * v[1]
        ny = u[2] * v[0] - u[0] * v[2]
        nz = u[0] * v[1] - u[1] * v[0]
        norm = math.sqrt(nx * nx + ny * ny + nz * nz) or 1
        nx, ny, nz = nx / norm, ny / norm, nz / norm
        diffuse = max(0, nx * light_dir[0] + ny * light_dir[1] + nz * light_dir[2])
        rx = 2 * diffuse * nx - light_dir[0]
        ry = 2 * diffuse * ny - light_dir[1]
        rz = 2 * diffuse * nz - light_dir[2]
        spec = max(0, rx * view_dir[0] + ry * view_dir[1] + rz * view_dir[2]) ** 20
        color = self._shade_color(diffuse)
        return z_avg, pts2d, color, spec

    def _draw_cube(self):
        self.canvas.delete("cube")
        self.canvas.delete("shadow")
        self.canvas.delete("cube_face")
        # Simple oval shadow to give cube a floating appearance
        shadow_w = 80
        shadow_h = 20
        cx = self.canvas_size / 2
        cy = self.canvas_size / 2 + 60
        self.canvas.create_oval(
            cx - shadow_w / 2,
            cy - shadow_h / 2,
            cx + shadow_w / 2,
            cy + shadow_h / 2,
            fill="black",
            outline="",
            tags="shadow",
            stipple="gray50",
        )
        angle_y = math.radians(self.angle)
        angle_x = math.radians(self.angle * 0.6)
        cos_y, sin_y = math.cos(angle_y), math.sin(angle_y)
        cos_x, sin_x = math.cos(angle_x), math.sin(angle_x)
        points = []
        points3d = []
        for x, y, z in self.vertices:
            # rotate around Y axis then X axis for 3D effect
            x1 = x * cos_y - z * sin_y
            z1 = x * sin_y + z * cos_y
            y1 = y * cos_x - z1 * sin_x
            z2 = y * sin_x + z1 * cos_x
            points3d.append((x1, y1, z2))
            points.append(self._project(x1, y1, z2))

        lx, ly, lz = 1, -1, 2
        lnorm = math.sqrt(lx * lx + ly * ly + lz * lz)
        light_dir = (lx / lnorm, ly / lnorm, lz / lnorm)
        view_dir = (0, 0, 1)
        faces_to_draw = [
            self._face_data(face, points, points3d, light_dir, view_dir)
            for face in self.faces
        ]

        for z_avg, pts2d, color, spec in sorted(faces_to_draw, key=lambda item: item[0]):
            self.canvas.create_polygon(
                pts2d,
                fill=color,
                outline="",
                stipple="gray50",
                tags="cube_face",
            )
            if spec > 0.01:
                self.canvas.create_polygon(
                    pts2d,
                    fill="white",
                    outline="",
                    stipple="gray25",
                    tags="cube_face",
                )

        for i, j in self.edges:
            x1, y1 = points[i]
            x2, y2 = points[j]
            self.canvas.create_line(
                x1,
                y1,
                x2,
                y2,
                fill="cyan",
                width=2,
                tags="cube",
            )

    def _draw_gear(self):
        self.canvas.delete("gear")
        self.canvas.delete("gear_glow")
        teeth = 8
        inner = 20
        outer = 30
        pts = []
        angle = math.radians(self.angle * 2)
        for i in range(teeth * 2):
            r = outer if i % 2 == 0 else inner
            theta = angle + i * math.pi / teeth
            x = self.canvas_size / 2 + r * math.cos(theta)
            y = self.canvas_size / 2 + r * math.sin(theta)
            pts.append((x, y))
        # Draw expanding outlines for a simple glow effect
        for width, colour in [(6, "#00ffff"), (4, "#66ffff")]:
            self.canvas.create_polygon(
                pts, outline=colour, fill="", width=width, tags="gear_glow"
            )
        self.canvas.create_polygon(
            pts, outline="lightgray", fill="", width=2, tags="gear"
        )

    def _animate(self):
        self.angle = (self.angle + 2) % 360
        self._draw_cube()
        self._draw_gear()
        self.after(50, self._animate)

    def _close(self):
        """Destroy splash screen and accompanying shadow window."""
        try:
            self.shadow.destroy()
        except Exception:
            pass
        super().destroy()
        if self._on_close:
            self._on_close()
