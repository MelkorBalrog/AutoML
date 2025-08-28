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


from __future__ import annotations

import os
import ctypes
import tkinter as tk
import tkinter.font as tkfont
from typing import Callable, Optional

from gui.utils.closable_notebook import cancel_after_events


_SYSTEM_COLORS = {
    "SystemButtonFace": 15,  # COLOR_BTNFACE
    "SystemWindow": 5,  # COLOR_WINDOW
    "SystemWindowText": 8,  # COLOR_WINDOWTEXT
}

_CAPSULE_HOVER_TAG = "CapsuleButtonHover"


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    """Return an RGB tuple for *value*.

    ``value`` may be a ``#`` prefixed hex string or a Tk colour name such as
    ``SystemButtonFace``.  Hex strings are parsed directly.  For system colour
    names on Windows we query ``GetSysColor`` to avoid creating temporary Tk
    roots that can trigger ``after`` callbacks.  If a Tk root exists we fall
    back to ``winfo_rgb`` for other named colours.
    """

    if value.startswith("#"):
        value = value.lstrip("#")
        lv = len(value)
        return tuple(int(value[i : i + lv // 3], 16) for i in range(0, lv, lv // 3))

    if os.name == "nt" and value in _SYSTEM_COLORS:
        idx = _SYSTEM_COLORS[value]
        colorref = ctypes.windll.user32.GetSysColor(idx)
        r = colorref & 0xFF
        g = (colorref >> 8) & 0xFF
        b = (colorref >> 16) & 0xFF
        return r, g, b

    root = tk._default_root  # type: ignore[attr-defined]
    if root is None:
        raise ValueError(f"unknown colour name: {value}")
    try:
        r, g, b = root.winfo_rgb(value)
    except tk.TclError as exc:  # Invalid colour name
        raise ValueError(str(exc)) from exc
    return r // 256, g // 256, b // 256


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return '#%02x%02x%02x' % rgb


def _lighten(color: str, factor: float = 1.2) -> str:
    """Return a brighter, lightly green-tinted version of ``color``.

    The original RGB channels are scaled by *factor* and then blended with a
    hint of white and pastel green to create a subtle glow used for hover
    effects.
    """

    r, g, b = _hex_to_rgb(color)
    r = min(int(r * factor), 255)
    g = min(int(g * factor), 255)
    b = min(int(b * factor), 255)
    # Blend with white and a touch of light green (#ccffcc)
    r = int(r * 0.6 + 255 * 0.3 + 204 * 0.1)
    g = int(g * 0.6 + 255 * 0.3 + 255 * 0.1)
    b = int(b * 0.6 + 255 * 0.3 + 204 * 0.1)
    return _rgb_to_hex((min(r, 255), min(g, 255), min(b, 255)))


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


def _glow_color(color: str, factor: float = 1.5, mix: float = 0.1) -> str:
    """Lighten ``color`` and blend it slightly with light green.

    The ``mix`` parameter controls how much of the light green ``#ccffcc`` is
    blended into the brightened colour.
    """

    bright = _lighten(color, factor)
    return _interpolate_color(bright, "#ccffcc", mix)


def _glow_image(img: tk.PhotoImage, factor: float = 1.5, mix: float = 0.1) -> tk.PhotoImage:
    """Return a glowing copy of ``img`` while preserving transparency.

    ``tk.PhotoImage`` provides no direct access to per-pixel alpha values, so
    when Pillow is available the image is converted to an ``RGBA`` bitmap where
    the colour channels are brightened and a hint of light green is blended in
    before the original alpha channel is reapplied.  If Pillow cannot be
    imported we fall back to a pure Tk based implementation that skips pixels
    reported as transparent.
    """

    try:  # Prefer Pillow for correct alpha handling
        from PIL import Image, ImageEnhance, ImageTk, ImageColor  # type: ignore

        # ``ImageTk.getimage`` may return a view on the original ``PhotoImage``
        # data.  Copy it so modifications do not bleed back into the caller's
        # image which should remain untouched for the normal button state.
        pil_img = ImageTk.getimage(img).copy().convert("RGBA")
        r, g, b, a = pil_img.split()
        rgb = Image.merge("RGB", (r, g, b))
        bright = ImageEnhance.Brightness(rgb).enhance(factor)
        green = Image.new("RGB", pil_img.size, ImageColor.getrgb("#ccffcc"))
        blended = Image.blend(bright, green, mix)
        light = Image.merge("RGBA", (*blended.split(), a))
        return ImageTk.PhotoImage(light)
    except Exception:  # pragma: no cover - Pillow may be unavailable
        w, h = img.width(), img.height()
        new = tk.PhotoImage(width=w, height=h)
        for x in range(w):
            for y in range(h):
                pixel = img.get(x, y)
                if pixel in ("", "{}", None):
                    # Leave fully transparent pixels untouched
                    continue
                if isinstance(pixel, tuple):
                    color = _rgb_to_hex(pixel[:3])
                else:
                    color = pixel
                new.put(_glow_color(color, factor, mix), (x, y))
        return new


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
        width: int | str = 80,
        height: int | str = 26,
        bg: str = "#c3d7ff",
        hover_bg: Optional[str] = None,
        state: str | None = None,
        image: tk.PhotoImage | None = None,
        compound: str = tk.CENTER,
        gradient: list[str] | None = None,
        hover_gradient: list[str] | None = None,
        **kwargs,
    ) -> None:
        width = int(width)
        height = int(height)
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
        # ``default`` is a standard ``Button`` option used by dialogs to mark
        # the widget activated when the user presses Return.  ``Canvas`` does
        # not recognise it, so silently drop the option to avoid a Tk error
        # when our custom button is used as a stand-in for ``tk.Button``.
        kwargs.pop("default", None)
        self._text = text
        self._image = image
        self._glow_cache: tk.PhotoImage | None = None
        self._compound = compound
        self._current_image = self._image
        req_width = max(width, self._content_width(height))
        init_kwargs["width"] = req_width
        init_kwargs.update(kwargs)
        super().__init__(master, **init_kwargs)
        self._state: set[str] = set()
        if state in {"disabled", tk.DISABLED}:  # type: ignore[arg-type]
            self._state.add("disabled")
        self._command = command
        self._normal_color = bg
        self._hover_color = hover_bg or _glow_color(bg)
        self._pressed_color = _darken(bg, 0.8)
        self._current_color = self._normal_color
        self._normal_gradient = gradient or ["#e6e6fa", "#c3dafe", "#87ceeb", "#e0ffff"]
        self._hover_gradient = hover_gradient or [
            _glow_color(c) for c in self._normal_gradient
        ]
        self._current_gradient = self._normal_gradient
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
        self._animate_id: str | None = None
        self._draw_button()
        self._add_hover_bindings()
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Motion>", self._on_motion)
        # Apply the initial state after the button has been drawn.
        self._apply_state()

    def _add_hover_bindings(self) -> None:
        tags = self.bindtags()
        if _CAPSULE_HOVER_TAG not in tags:
            self.bindtags((_CAPSULE_HOVER_TAG,) + tags)
        self.bind_class(_CAPSULE_HOVER_TAG, "<Enter>", self._enter_event)
        self.bind_class(_CAPSULE_HOVER_TAG, "<Leave>", self._leave_event)

    @staticmethod
    def _enter_event(event: tk.Event) -> None:
        widget = event.widget
        if isinstance(widget, CapsuleButton):
            widget._on_enter(event)

    @staticmethod
    def _leave_event(event: tk.Event) -> None:
        widget = event.widget
        if isinstance(widget, CapsuleButton):
            widget._on_leave(event)

    def _content_width(self, height: int | str) -> int:
        """Return the minimum width to display current text and image."""
        height = int(height)
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
        if not self._current_gradient:
            return
        colors = self._current_gradient
        stops = [i / (len(colors) - 1) for i in range(len(colors))]
        r = self._radius
        for y in range(h):
            t = y / (h - 1) if h > 1 else 0
            for i in range(len(stops) - 1):
                if stops[i] <= t <= stops[i + 1]:
                    local_t = (t - stops[i]) / (stops[i + 1] - stops[i])
                    color = _interpolate_color(colors[i], colors[i + 1], local_t)
                    break
            dy = abs(y - h / 2)
            x_offset = int(r - (r ** 2 - dy ** 2) ** 0.5) if dy <= r else 0
            self._gradient_items.append(
                self.create_line(x_offset, y, w - x_offset, y, fill=color)
            )

    def _set_gradient(self, gradient: list[str]) -> None:
        self._current_gradient = gradient
        for item in self._gradient_items:
            self.delete(item)
        self._gradient_items = []
        self._draw_gradient(int(self["width"]), int(self["height"]))
        for item in self._gradient_items:
            if self._shine_items:
                self.tag_lower(item, self._shine_items[0])
        overlays = (
            self._shine_items
            + self._shade_items
            + self._glow_items
            + self._border_dark
            + self._border_light
            + self._border_gap
            + self._outer_shadow
        )
        for itm in overlays:
            self.tag_raise(itm)
        if self._image_item:
            self.tag_raise(self._image_item)
        if self._text_item:
            self.tag_raise(self._text_item)

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
        img = self._current_image
        text = self._text
        compound = self._compound
        if img and text:
            font = tkfont.nametofont("TkDefaultFont")
            text_w = font.measure(text)
            text_h = font.metrics("linespace")
            img_w = img.width()
            img_h = img.height()
            spacing = 4
            if compound == tk.LEFT:
                total = text_w + img_w + spacing
                start = (w - total) // 2
                img_x = start + img_w // 2
                text_x = start + img_w + spacing + text_w // 2
                self._image_item = self.create_image(img_x, cy, image=img)
                self._text_item = self.create_text(text_x, cy, text=text, fill="black")
            elif compound == tk.RIGHT:
                total = text_w + img_w + spacing
                start = (w - total) // 2
                text_x = start + text_w // 2
                img_x = start + text_w + spacing + img_w // 2
                self._text_item = self.create_text(text_x, cy, text=text, fill="black")
                self._image_item = self.create_image(img_x, cy, image=img)
            elif compound == tk.TOP:
                total = text_h + img_h + spacing
                start = (h - total) // 2
                img_y = start + img_h // 2
                text_y = start + img_h + spacing + text_h // 2
                self._image_item = self.create_image(cx, img_y, image=img)
                self._text_item = self.create_text(cx, text_y, text=text, fill="black")
            elif compound == tk.BOTTOM:
                total = text_h + img_h + spacing
                start = (h - total) // 2
                text_y = start + text_h // 2
                img_y = start + text_h + spacing + img_h // 2
                self._text_item = self.create_text(cx, text_y, text=text, fill="black")
                self._image_item = self.create_image(cx, img_y, image=img)
            else:  # centre overlay
                self._image_item = self.create_image(cx, cy, image=img)
                self._text_item = self.create_text(cx, cy, text=text, fill="black")
        elif img:
            self._image_item = self.create_image(cx, cy, image=img)
        elif text:
            self._text_item = self.create_text(cx, cy, text=text, fill="black")



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
        if not self.winfo_exists():
            return
        for item in self._shape_items:
            self._safe_itemconfigure(item, fill=color)
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
            if not self._safe_itemconfigure(item, **{option: color}):
                # ``outline`` is not supported by some item types (e.g. text),
                # so retry with ``fill`` to avoid crashes.
                self._safe_itemconfigure(item, fill=color)

    def _safe_itemconfigure(self, item: int, **kwargs) -> bool:
        """Safely configure canvas items.

        Returns ``True`` if the configuration succeeded, ``False`` otherwise.
        Any ``TclError`` raised because the widget or item no longer exists is
        silently ignored.
        """
        if not self.winfo_exists():
            return False
        try:
            self.itemconfigure(item, **kwargs)
        except tk.TclError:
            return False
        return True

    def _get_glow_image(self) -> tk.PhotoImage:
        """Return a cached glowing version of the current image."""
        if self._glow_cache is None and self._image is not None:
            self._glow_cache = _glow_image(self._image)
        # ``_image`` may be ``None`` when no icon is used; ``_current_image``
        # is then also ``None`` so callers should guard accordingly.
        return self._glow_cache  # type: ignore[return-value]

    def _add_glow(self) -> None:
        """Lighten the button edges without covering the surface."""
        if self._glow_items or not self.winfo_exists():
            return
        w, h = int(self["width"]), int(self["height"])
        r = self._radius
        glow_color = _glow_color(self._normal_color, 1.3)
        bottom_color = _glow_color(self._normal_color, 1.6)
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
        self._glow_items.append(
            self.create_rectangle(
                r,
                h - 3,
                w - r,
                h,
                outline="",
                fill=bottom_color,
            )
        )
        # Ensure existing text and icons remain visible above the glow overlay
        if self._image_item:
            self.tag_raise(self._image_item)
        if self._text_item:
            self.tag_raise(self._text_item)

    def _remove_glow(self) -> None:
        if not self.winfo_exists():
            self._glow_items = []
            return
        for item in self._glow_items:
            try:
                self.delete(item)
            except tk.TclError:
                pass
        self._glow_items = []

    def _toggle_shine(self, visible: bool) -> None:
        if not self.winfo_exists():
            return
        state = tk.NORMAL if visible else tk.HIDDEN
        for item in self._shine_items + self._shade_items:
            self._safe_itemconfigure(item, state=state)

    def _animate(self) -> None:
        """Schedule a lightweight animation callback."""
        if not self.winfo_exists():
            return
        self._animate_id = self.after(50, self._animate)

    def _on_motion(self, event: tk.Event) -> None:
        try:
            if "disabled" in self._state or not self.winfo_exists():
                return
            w, h = int(self["width"]), int(self["height"])
            inside = 0 <= event.x < w and 0 <= event.y < h
            if inside:
                if self._current_color == self._normal_color:
                    self._set_color(self._hover_color)
                if (
                    self._image_item
                    and self._image
                    and self._current_image is self._image
                ):
                    glow = self._get_glow_image()
                    if glow and self._safe_itemconfigure(self._image_item, image=glow):
                        self._current_image = glow
                self._add_glow()
                self._set_gradient(self._hover_gradient)
            else:
                if self._current_color != self._normal_color:
                    self._set_color(self._normal_color)
                if self._image_item and self._current_image is not self._image:
                    if self._safe_itemconfigure(self._image_item, image=self._image):
                        self._current_image = self._image
                self._remove_glow()
                self._set_gradient(self._normal_gradient)
        except tk.TclError:
            pass

    def _on_enter(self, _event: tk.Event) -> None:
        try:
            if "disabled" not in self._state and self.winfo_exists():
                self._set_color(self._hover_color)
                if self._image_item and self._image:
                    glow = self._get_glow_image()
                    if glow and self._safe_itemconfigure(self._image_item, image=glow):
                        self._current_image = glow
                self._add_glow()
                self._set_gradient(self._hover_gradient)
        except tk.TclError:
            pass

    def _on_leave(self, _event: tk.Event) -> None:
        try:
            if "disabled" not in self._state and self.winfo_exists():
                self._set_color(self._normal_color)
                if self._image_item and self._current_image is not self._image:
                    if self._safe_itemconfigure(self._image_item, image=self._image):
                        self._current_image = self._image
                self._remove_glow()
                self._set_gradient(self._normal_gradient)
        except tk.TclError:
            pass

    def _on_press(self, _event: tk.Event) -> None:
        try:
            if "disabled" not in self._state and self.winfo_exists():
                self._remove_glow()
                self._toggle_shine(False)
                self._set_color(self._pressed_color)
                self._set_gradient(self._normal_gradient)
        except tk.TclError:
            pass

    def _on_release(self, event: tk.Event) -> None:
        try:
            if "disabled" in self._state or not self.winfo_exists():
                return
            w, h = int(self["width"]), int(self["height"])
            inside = 0 <= event.x < w and 0 <= event.y < h
            if inside:
                self._set_color(self._hover_color)
                self._toggle_shine(True)
                self._add_glow()
                self._set_gradient(self._hover_gradient)
                if self._command:
                    self._command()
            else:
                self._set_color(self._normal_color)
                self._toggle_shine(True)
                self._remove_glow()
                self._set_gradient(self._normal_gradient)
        except tk.TclError:
            pass

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
            self._hover_color = hover_bg or _glow_color(bg)
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
            self._glow_cache = None
            self._current_image = self._image
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

    # ------------------------------------------------------------
    # Cleanup helpers

    def destroy(self) -> None:  # type: ignore[override]
        """Cancel scheduled callbacks then destroy the widget."""
        try:
            cancel_after_events(self)
        except Exception:
            pass
        self._animate_id = None
        super().destroy()
