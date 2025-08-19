from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from typing import Callable, Optional


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return '#%02x%02x%02x' % rgb


def _lighten(color: str, factor: float = 1.2) -> str:
    r, g, b = _hex_to_rgb(color)
    r = min(int(r * factor), 255)
    g = min(int(g * factor), 255)
    b = min(int(b * factor), 255)
    return _rgb_to_hex((r, g, b))


def _darken(color: str, factor: float = 0.8) -> str:
    r, g, b = _hex_to_rgb(color)
    r = max(int(r * factor), 0)
    g = max(int(g * factor), 0)
    b = max(int(b * factor), 0)
    return _rgb_to_hex((r, g, b))


def _interpolate_color(c1: str, c2: str, t: float) -> str:
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return _rgb_to_hex((r, g, b))


class CapsuleButton(tk.Canvas):
    """A capsule-shaped button that lightens on hover and appears recessed.

    The widget renders a rounded button using canvas primitives so it does not
    rely on platform specific themes.  A subtle dark/light border is drawn
    around the capsule to give the impression that the button sits inside a
    hole matching its shape.  When the mouse cursor enters the button area the
    fill colour is lightened to mimic a highlight effect.
    """

    def __init__(
        self,
        master: tk.Widget,
        text: str,
        command: Optional[Callable[[], None]] = None,
        width: int = 80,
        height: int = 26,
        bg: str = "#c3d7ff",
        hover_bg: Optional[str] = None,
        state: str | None = None,
        image: tk.PhotoImage | None = None,
        compound: str = tk.CENTER,
        **kwargs,
    ) -> None:
        init_kwargs = {
            "height": height,
            "highlightthickness": 0,
        }
        control_bg = _darken(bg, 0.9)
        try:
            master.configure(bg=control_bg)
            init_kwargs["bg"] = control_bg
        except tk.TclError:
            try:
                init_kwargs["bg"] = master.cget("background")
            except tk.TclError:
                pass
        # ``style`` and ``state`` are ttk-specific options.  Strip them from
        # ``kwargs`` before forwarding to ``Canvas.__init__`` and track the
        # ``state`` value ourselves.  ``image`` and ``compound`` are also Tk
        # button options which ``Canvas`` does not understand, so remove them
        # here and handle them manually.
        kwargs.pop("style", None)
        kwargs.pop("image", None)
        kwargs.pop("compound", None)
        self._text = text
        self._image = image
        self._compound = compound
        req_width = max(width, self._content_width(height))
        init_kwargs["width"] = req_width
        init_kwargs.update(kwargs)
        super().__init__(master, **init_kwargs)
        self._state: set[str] = set()
        if state in {"disabled", tk.DISABLED}:  # type: ignore[arg-type]
            self._state.add("disabled")
        self._command = command
        self._normal_color = bg
        self._hover_color = hover_bg or _lighten(bg, 1.2)
        self._pressed_color = _darken(bg, 0.8)
        self._current_color = self._normal_color
        self._radius = height // 2
        self._shape_items: list[int] = []
        self._shade_items: list[int] = []
        self._shine_items: list[int] = []
        self._glow_items: list[int] = []
        # Border items are split into dark and light segments to create a
        # recessed "hole" effect around the button outline.  ``_border_outline``
        # draws a thin dark line between the button and its hole for an extra
        # sense of depth.
        self._border_dark: list[int] = []
        self._border_light: list[int] = []
        self._border_gap: list[int] = []
        self._outer_shadow: list[int] = []
        self._text_item: Optional[int] = None
        # Drop-shadow canvas items were previously stored in
        # ``_text_shadow_item`` and ``_icon_shadow_item``.  The shadow effect
        # made text and icons appear doubled, so these attributes and the
        # associated rendering have been removed entirely.  Icon highlight
        # items are still tracked to provide a subtle sheen without duplicating
        # content.
        self._image_item: Optional[int] = None
        self._icon_highlight_item: Optional[int] = None
        self._draw_button()
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Motion>", self._on_motion)
        # Apply the initial state after the button has been drawn.
        self._apply_state()

    def _content_width(self, height: int) -> int:
        """Return the minimum width to display current text and image."""
        font = tkfont.nametofont("TkDefaultFont")
        text_w = font.measure(self._text) if self._text else 0
        img_w = self._image.width() if self._image else 0
        spacing = 4 if self._text and self._image else 0
        padding = height  # space for rounded ends
        return max(text_w + img_w + spacing + padding, height)

    def _draw_button(self) -> None:
        self.delete("all")
        w = int(self["width"])
        h = int(self["height"])
        r = self._radius
        color = self._current_color
        # Draw the filled shapes without outlines so the seams between the
        # rectangle and arcs are not visible.
        self._shape_items = [
            self.create_arc(
                (0, 0, 2 * r, h),
                start=90,
                extent=180,
                style=tk.CHORD,
                outline="",
                fill=color,
            ),
            self.create_rectangle((r, 0, w - r, h), outline="", fill=color),
            self.create_arc(
                (w - 2 * r, 0, w, h),
                start=-90,
                extent=180,
                style=tk.CHORD,
                outline="",
                fill=color,
            ),
        ]
        self._gradient_items = []
        self._draw_gradient(w, h)
        self._shine_items = []
        self._shade_items = []
        self._glow_items = []
        self._draw_highlight(w, h)
        self._draw_shade(w, h)
        self._draw_content(w, h)
        self._draw_border(w, h)

    def _draw_gradient(self, w: int, h: int) -> None:
        colors = ["#e6e6fa", "#c3dafe", "#87ceeb", "#e0ffff"]
        stops = [0.0, 0.33, 0.66, 1.0]
        r = self._radius
        for y in range(h):
            t = y / (h - 1) if h > 1 else 0
            for i in range(len(stops) - 1):
                if stops[i] <= t <= stops[i + 1]:
                    local_t = (t - stops[i]) / (stops[i + 1] - stops[i])
                    color = _interpolate_color(colors[i], colors[i + 1], local_t)
                    break
            dy = abs(y - h / 2)
            if dy <= r:
                x_offset = int(r - (r ** 2 - dy ** 2) ** 0.5)
            else:
                x_offset = 0
            self._gradient_items.append(
                self.create_line(x_offset, y, w - x_offset, y, fill=color)
            )

    def _draw_highlight(self, w: int, h: int) -> None:
        """Draw shiny highlight to create a glassy lavender sheen."""
        r = self._radius
        self._shine_items = [
            self.create_oval(
                r,
                1,
                w - r,
                h // 2,
                outline="",
                fill="#e6e6fa",
                stipple="gray25",
            )
        ]
        small_r = max(r // 3, 2)
        centers = [(r // 2, h // 2), (w - r // 2, h // 2)]
        for cx, cy in centers:
            for i in range(3):
                rad = max(small_r - i * (small_r // 3), 1)
                self._shine_items.append(
                    self.create_oval(
                        cx - rad,
                        cy - rad,
                        cx + rad,
                        cy + rad,
                        outline="",
                        fill="#f5f5ff",
                        stipple="gray25",
                    )
                )

    def _draw_shade(self, w: int, h: int) -> None:
        """Add cool blue and aqua shades to suggest depth."""
        r = self._radius
        self._shade_items = [
            # Bright medium sky blue
            self.create_oval(
                r,
                h // 2,
                w - r,
                h - 1,
                outline="",
                fill="#87ceeb",
                stipple="gray50",
            ),
            # Fading light cyan/aqua
            self.create_oval(
                r,
                (3 * h) // 4,
                w - r,
                h - 1,
                outline="",
                fill="#e0ffff",
                stipple="gray25",
            ),
        ]


    def _draw_content(self, w: int, h: int) -> None:
        """Render optional image and text without drop shadows."""
        cx, cy = w // 2, h // 2
        self._text_item = None
        # Shadow items were removed to avoid doubled rendering of
        # text and icons.  Only the main content and optional icon highlight
        # are recreated when drawing the button.
        self._image_item = None
        self._icon_highlight_item = None
        if self._image and self._text and self._compound == tk.LEFT:
            font = tkfont.nametofont("TkDefaultFont")
            text_w = font.measure(self._text)
            img_w = self._image.width()
            spacing = 4
            total = text_w + img_w + spacing
            start = (w - total) // 2
            img_x = start + img_w // 2
            text_x = start + img_w + spacing + text_w // 2
            self._image_item = self.create_image(img_x, cy, image=self._image)
            self._text_item = self.create_text(text_x, cy, text=self._text)
        elif self._image:
            self._image_item = self.create_image(cx, cy, image=self._image)
        else:
            self._text_item = self.create_text(cx, cy, text=self._text)



    def _draw_border(self, w: int, h: int) -> None:
        """Draw border and inner outline to mimic an inset capsule."""
        r = self._radius
        shadow = _darken(self._current_color, 0.5)
        self._outer_shadow = [
            self.create_arc((-2, -2, 2 * r + 2, h + 2), start=90, extent=180, style=tk.ARC, outline=shadow, width=2),
            self.create_line(r, -2, w - r, -2, fill=shadow, width=2),
            self.create_arc((w - 2 * r - 2, -2, w + 2, h + 2), start=-90, extent=180, style=tk.ARC, outline=shadow, width=2),
            self.create_line(-2, r, -2, h - r, fill=shadow, width=2),
            self.create_line(r, h + 2, w - r, h + 2, fill=shadow, width=2),
            self.create_line(w + 2, r, w + 2, h - r, fill=shadow, width=2),
        ]
        inner = _darken(self._current_color, 0.7)
        self._border_outline = [
            self.create_arc((1, 1, 2 * r - 1, h - 1), start=90, extent=180, style=tk.ARC, outline=inner),
            self.create_line(r, 1, w - r, 1, fill=inner),
            self.create_arc((w - 2 * r + 1, 1, w - 1, h - 1), start=-90, extent=180, style=tk.ARC, outline=inner),
            self.create_line(1, r, 1, h - r, fill=inner),
            self.create_line(r, h - 1, w - r, h - 1, fill=inner),
            self.create_line(w - 1, r, w - 1, h - r, fill=inner),
        ]
        dark = _darken(self._current_color, 0.8)
        light = _lighten(self._current_color, 1.2)
        gap = _darken(self._current_color, 0.7)
        inset = 1
        # Dark top/left edges
        self._border_dark = [
            self.create_arc((0, 0, 2 * r, h), start=90, extent=180, style=tk.ARC, outline=dark, width=2),
            self.create_line(r, 0, w - r, 0, fill=dark, width=2),
            self.create_line(0, r, 0, h - r, fill=dark, width=2),
        ]
        # Thin dark outline inside the border to accentuate the recessed effect
        self._border_gap = [
            self.create_arc((inset, inset, 2 * r - inset, h - inset), start=90, extent=180, style=tk.ARC, outline=gap, width=1),
            self.create_line(r, inset, w - r, inset, fill=gap, width=1),
            self.create_line(inset, r, inset, h - r, fill=gap, width=1),
            self.create_arc((w - 2 * r + inset, inset, w - inset, h - inset), start=-90, extent=180, style=tk.ARC, outline=gap, width=1),
            self.create_line(r, h - inset, w - r, h - inset, fill=gap, width=1),
            self.create_line(w - inset, r, w - inset, h - r, fill=gap, width=1),
        ]
        # Light bottom/right edges
        self._border_light = [
            self.create_arc((w - 2 * r, 0, w, h), start=-90, extent=180, style=tk.ARC, outline=light, width=2),
            self.create_line(r, h, w - r, h, fill=light, width=2),
            self.create_line(w, r, w, h - r, fill=light, width=2),
        ]

    def _set_color(self, color: str) -> None:
        for item in self._shape_items:
            self.itemconfigure(item, fill=color)
        inner = _darken(color, 0.7)
        dark = _darken(color, 0.8)
        light = _lighten(color, 1.2)
        gap = _darken(color, 0.7)
        shadow = _darken(color, 0.5)
        self._apply_border_color(self._border_dark, dark)
        self._apply_border_color(self._border_light, light)
        self._apply_border_color(self._border_gap, gap)
        self._apply_border_color(self._outer_shadow, shadow)
        self._current_color = color

    def _apply_border_color(self, items: list[int], color: str) -> None:
        """Apply a colour to border items safely.

        Canvas items support different configuration options depending on their
        type.  Lines expect a ``fill`` option while arcs and ovals normally use
        ``outline``.  On some platforms Tk raises ``TclError`` if an unsupported
        option is passed.  To make the widget robust we determine the preferred
        option and gracefully fall back to ``fill`` when ``outline`` is not
        available.
        """
        for item in items:
            item_type = self.type(item)
            option = "fill" if item_type == "line" else "outline"
            try:
                self.itemconfigure(item, **{option: color})
            except tk.TclError:
                # ``outline`` is not supported by some item types (e.g. text),
                # so retry with ``fill`` to avoid crashes.
                self.itemconfigure(item, fill=color)

    def _add_glow(self) -> None:
        """Lighten the button edges without covering the surface."""
        if self._glow_items:
            return
        w, h = int(self["width"]), int(self["height"])
        r = self._radius
        glow_color = _lighten(self._current_color, 1.3)
        self._glow_items = [
            self.create_arc((-1, -1, 2 * r + 1, h + 1), start=90, extent=180, style=tk.ARC, outline=glow_color, width=2),
            # Offset the horizontal glow lines by one pixel so the caps extend
            # beyond the button edge.  Without this adjustment the highlight
            # appears slightly narrower than the button itself.
            self.create_line(r - 1, -1, w - r + 1, -1, fill=glow_color, width=2),
            self.create_arc((w - 2 * r - 1, -1, w + 1, h + 1), start=-90, extent=180, style=tk.ARC, outline=glow_color, width=2),
            self.create_line(-1, r, -1, h - r, fill=glow_color, width=2),
            self.create_line(r - 1, h + 1, w - r + 1, h + 1, fill=glow_color, width=2),
            self.create_line(w + 1, r, w + 1, h - r, fill=glow_color, width=2),
        ]

    def _remove_glow(self) -> None:
        for item in self._glow_items:
            self.delete(item)
        self._glow_items = []

    def _toggle_shine(self, visible: bool) -> None:
        state = tk.NORMAL if visible else tk.HIDDEN
        for item in self._shine_items + self._shade_items:
            self.itemconfigure(item, state=state)

    def _on_motion(self, event: tk.Event) -> None:
        if "disabled" in self._state:
            return
        w, h = int(self["width"]), int(self["height"])
        inside = 0 <= event.x < w and 0 <= event.y < h
        if inside:
            if self._current_color == self._normal_color:
                self._set_color(self._hover_color)
            self._add_glow()
        else:
            if self._current_color != self._normal_color:
                self._set_color(self._normal_color)
            self._remove_glow()

    def _on_enter(self, _event: tk.Event) -> None:
        if "disabled" not in self._state:
            self._set_color(self._hover_color)
            self._add_glow()

    def _on_leave(self, _event: tk.Event) -> None:
        if "disabled" not in self._state:
            self._set_color(self._normal_color)
            self._remove_glow()

    def _on_press(self, _event: tk.Event) -> None:
        if "disabled" not in self._state:
            self._remove_glow()
            self._toggle_shine(False)
            self._set_color(self._pressed_color)

    def _on_release(self, event: tk.Event) -> None:
        if "disabled" in self._state:
            return
        w, h = int(self["width"]), int(self["height"])
        inside = 0 <= event.x < w and 0 <= event.y < h
        if inside:
            self._set_color(self._hover_color)
            self._toggle_shine(True)
            self._add_glow()
            if self._command:
                self._command()
        else:
            self._set_color(self._normal_color)
            self._toggle_shine(True)
            self._remove_glow()

    def _apply_state(self) -> None:
        """Update the visual appearance to reflect the current state."""
        if "disabled" in self._state:
            # A light gray color roughly matching ttk's disabled buttons
            self._remove_glow()
            self._toggle_shine(True)
            self._set_color("#d9d9d9")
        else:
            self._toggle_shine(True)
            self._set_color(self._normal_color)

    def configure(self, **kwargs) -> None:  # pragma: no cover - thin wrapper
        """Allow dynamic configuration similar to standard Tk buttons."""
        text = kwargs.pop("text", None)
        command = kwargs.pop("command", None)
        bg = kwargs.pop("bg", None)
        hover_bg = kwargs.pop("hover_bg", None)
        image = kwargs.pop("image", None)
        compound = kwargs.pop("compound", None)
        width = kwargs.pop("width", None)
        height = kwargs.pop("height", None)
        state = kwargs.pop("state", None)
        kwargs.pop("style", None)
        super().configure(**kwargs)
        changed = False
        self._update_command(command)
        if self._update_text(text):
            changed = True
        if self._update_image(image, compound):
            changed = True
        self._update_colors(bg, hover_bg)
        self._update_geometry(width, height, changed)
        self._update_state(state)
        # Always re-apply the current state so that disabled buttons retain
        # their disabled appearance even after reconfiguration.
        self._apply_state()

    config = configure

    def _update_command(self, command: Optional[Callable[[], None]]) -> None:
        if command is not None:
            self._command = command

    def _update_text(self, text: Optional[str]) -> bool:
        if text is None or text == self._text:
            return False
        self._text = text
        return True

    def _update_colors(self, bg: Optional[str], hover_bg: Optional[str]) -> None:
        if bg is not None:
            self._normal_color = bg
            self._hover_color = hover_bg or _lighten(bg, 1.2)
            self._pressed_color = _darken(bg, 0.8)
            self._set_color(self._normal_color)
        elif hover_bg is not None:
            self._hover_color = hover_bg

    def _update_image(
        self, image: tk.PhotoImage | None, compound: Optional[str]
    ) -> bool:
        changed = False
        if image is not None:
            self._image = image
            changed = True
        if compound is not None:
            self._compound = compound
            changed = True
        return changed

    def _update_geometry(
        self, width: Optional[int], height: Optional[int], redraw: bool
    ) -> None:
        h = height if height is not None else int(self["height"])
        req_w = self._content_width(h)
        w = width if width is not None else int(self["width"])
        if w < req_w:
            w = req_w
        super().configure(width=w, height=h)
        self._radius = h // 2
        if redraw or w != int(self["width"]) or h != int(self["height"]):
            self._draw_button()

    def _update_state(self, state: Optional[str]) -> None:
        if state is None:
            return
        if state in ("disabled", tk.DISABLED):  # type: ignore[arg-type]
            self.state(["disabled"])
        else:
            self.state(["!disabled"])

    def state(self, states: list[str] | tuple[str, ...] | None = None) -> list[str]:
        """Mimic the ``ttk.Widget.state`` method for simple disabled handling."""
        if states is None:
            return list(self._state)
        for s in states:
            if s.startswith("!"):
                self._state.discard(s[1:])
            else:
                self._state.add(s)
        self._apply_state()
        return list(self._state)
