import tkinter as tk
import math


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
    ):
        super().__init__(master)
        self.duration = duration
        self.overrideredirect(True)

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
        # Text at bottom center
        self.canvas.create_text(
            self.canvas_size / 2,
            self.canvas_size - 40,
            text="Automotive Modeling Language\nby\nKarel Capek Robotics",
            justify="center",
            font=("Helvetica", 12),
            fill="white",
        )

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

    def _fade_in(self):
        if not getattr(self, "_alpha_supported", False):
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
        """Draw a sky-to-ground gradient to hint at a distant horizon."""
        # Color stops: dark blue sky -> warm horizon -> dark ground
        stops = [
            (0.0, (10, 10, 40)),     # night sky
            (0.5, (255, 165, 0)),    # orange horizon
            (1.0, (0, 20, 0)),       # ground
        ]
        steps = self.canvas_size
        for i in range(steps):
            ratio = i / steps
            # Find two surrounding color stops
            for idx in range(len(stops) - 1):
                if stops[idx][0] <= ratio <= stops[idx + 1][0]:
                    left_pos, left_col = stops[idx]
                    right_pos, right_col = stops[idx + 1]
                    break
            # Normalize ratio between the two stops
            local = (ratio - left_pos) / (right_pos - left_pos)
            r = int(left_col[0] + (right_col[0] - left_col[0]) * local)
            g = int(left_col[1] + (right_col[1] - left_col[1]) * local)
            b = int(left_col[2] + (right_col[2] - left_col[2]) * local)
            color = f"#{r:02x}{g:02x}{b:02x}"
            self.canvas.create_line(0, i, self.canvas_size, i, fill=color)

    def _project(self, x, y, z):
        """Project 3D point onto 2D canvas."""
        distance = 5
        factor = self.canvas_size / (2 * (z + distance))
        x = x * factor + self.canvas_size / 2
        y = y * factor + self.canvas_size / 2
        return x, y

    def _draw_cube(self):
        self.canvas.delete("cube")
        self.canvas.delete("shadow")
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
        angle = math.radians(self.angle)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        projected = []
        rotated = []
        for x, y, z in self.vertices:
            # rotate around Y axis
            x1 = x * cos_a - z * sin_a
            z1 = x * sin_a + z * cos_a
            # rotate around X axis for slight 3D
            y1 = y * cos_a - z1 * sin_a
            z2 = y * sin_a + z1 * cos_a
            rotated.append((x1, y1, z2))
            projected.append(self._project(x1, y1, z2))

        # Draw semi-transparent faces for a glassy look
        faces = [
            (0, 1, 2, 3),
            (4, 5, 6, 7),
            (0, 1, 5, 4),
            (2, 3, 7, 6),
            (0, 3, 7, 4),
            (1, 2, 6, 5),
        ]
        # Sort faces by average depth so farthest are drawn first
        depths = [
            (sum(rotated[i][2] for i in face) / 4.0, face)
            for face in faces
        ]
        for _, face in sorted(depths):
            pts = [coord for i in face for coord in projected[i]]
            self.canvas.create_polygon(
                pts,
                fill="cyan",
                outline="",
                stipple="gray25",
                tags="cube",
            )

        # Bright cyan edges with white highlight for shininess
        for i, j in self.edges:
            x1, y1 = projected[i]
            x2, y2 = projected[j]
            self.canvas.create_line(
                x1,
                y1,
                x2,
                y2,
                fill="cyan",
                width=2,
                tags="cube",
            )
            self.canvas.create_line(
                x1,
                y1,
                x2,
                y2,
                fill="white",
                width=1,
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
        # Glow effect: draw a thicker translucent outline underneath
        self.canvas.create_polygon(
            pts,
            outline="cyan",
            fill="",
            width=6,
            stipple="gray50",
            tags="gear_glow",
        )
        # Sharp gear outline on top
        self.canvas.create_polygon(
            pts, outline="white", fill="", width=2, tags="gear"
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
        self.destroy()
