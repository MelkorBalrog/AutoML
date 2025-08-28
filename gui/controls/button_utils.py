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

"""Utility helpers for consistent button presentation across toolboxes."""


import tkinter as tk
from tkinter import ttk

from .capsule_button import _lighten


def set_uniform_button_width(widget: tk.Misc) -> None:
    """Ensure all ``ttk.Button`` children of *widget* share the same width.

    ``CapsuleButton`` derivatives like ``TranslucidButton`` express width in
    *pixels* rather than character units.  Simply matching on label length can
    therefore yield inconsistent button sizes or truncated text.  By measuring
    each button's requested pixel width we can apply a uniform size that fits
    all labels.
    """
    widget.update_idletasks()
    buttons: list[ttk.Button] = []

    def _collect(w: tk.Misc) -> None:
        for child in w.winfo_children():
            if isinstance(child, ttk.Button):
                buttons.append(child)
            else:
                _collect(child)

    _collect(widget)
    if not buttons:
        return

    max_width = max(btn.winfo_reqwidth() for btn in buttons)
    for btn in buttons:
        try:
            btn.configure(width=max_width)
        except Exception:  # pragma: no cover - defensive
            pass


def max_button_reqwidth(widget: tk.Misc) -> int:
    """Return the widest requested width of ``ttk.Button`` descendants.

    Traverses *widget*'s children recursively while gracefully handling widgets
    that have already been destroyed.  If a child no longer exists, it is
    ignored so callers can safely compute widths during dynamic UI updates
    without triggering :class:`tk.TclError` exceptions.
    """

    max_width = 0
    try:
        children = widget.winfo_children()
    except tk.TclError:
        return 0
    for child in children:
        try:
            if not child.winfo_exists():
                continue
            if isinstance(child, ttk.Button):
                max_width = max(max_width, child.winfo_reqwidth())
            else:
                max_width = max(max_width, max_button_reqwidth(child))
        except tk.TclError:  # pragma: no cover - defensive
            continue
    return max_width

def _lighten_color(color: str, factor: float = 1.2) -> str:
    """Return a subtly glowing version of *color*.

    The base colour channels are scaled by *factor* and then blended with
    white and a hint of pastel green.  This mirrors the behaviour of the
    :func:`_lighten` helper used by :class:`gui.controls.capsule_button.CapsuleButton` so
    hover images across the application share the same gentle glow.
    """

    r = int(color[1:3], 16)
    g = int(color[3:5], 16)
    b = int(color[5:7], 16)
    r = min(int(r * factor), 255)
    g = min(int(g * factor), 255)
    b = min(int(b * factor), 255)
    # Blend with white and a touch of light green (#ccffcc)
    r = int(r * 0.6 + 255 * 0.3 + 204 * 0.1)
    g = int(g * 0.6 + 255 * 0.3 + 255 * 0.1)
    b = int(b * 0.6 + 255 * 0.3 + 204 * 0.1)
    return f"#{min(r,255):02x}{min(g,255):02x}{min(b,255):02x}"

def _blend_with(color: str, overlay: tuple[int, int, int], alpha: float) -> str:
    """Blend *color* towards *overlay* by *alpha*."""
    r = int(color[1:3], 16)
    g = int(color[3:5], 16)
    b = int(color[5:7], 16)
    r = int(r + (overlay[0] - r) * alpha)
    g = int(g + (overlay[1] - g) * alpha)
    b = int(b + (overlay[2] - b) * alpha)
    return f"#{r:02x}{g:02x}{b:02x}"


def _blend_with(color: str, overlay: tuple[int, int, int], alpha: float) -> str:
    """Blend *color* towards *overlay* by *alpha*."""
    r = int(color[1:3], 16)
    g = int(color[3:5], 16)
    b = int(color[5:7], 16)
    r = int(r + (overlay[0] - r) * alpha)
    g = int(g + (overlay[1] - g) * alpha)
    b = int(b + (overlay[2] - b) * alpha)
    return f"#{r:02x}{g:02x}{b:02x}"


def _blend_with(color: str, overlay: tuple[int, int, int], alpha: float) -> str:
    """Blend *color* towards *overlay* by *alpha*."""
    r = int(color[1:3], 16)
    g = int(color[3:5], 16)
    b = int(color[5:7], 16)
    r = int(r + (overlay[0] - r) * alpha)
    g = int(g + (overlay[1] - g) * alpha)
    b = int(b + (overlay[2] - b) * alpha)
    return f"#{r:02x}{g:02x}{b:02x}"


def _lighten_image(
    img: tk.PhotoImage,
    factor: float = 1.4,
    *,
    bottom_factor: float = 1.8,
    bottom_ratio: float = 0.3,
    top_alpha: float = 0.7,
    bottom_alpha: float = 0.9,
) -> tk.PhotoImage:
    """Return a new image with all pixels lightened.

    Pixels are first blended towards either white (top) or light green (bottom)
    to seed a visible glow.  The blended colour is then lightened by ``factor``
    (with an extra ``bottom_factor`` boost for lower pixels) so the tint remains
    bright.  Alpha values are preserved where present.
    """
    w, h = img.width(), img.height()
    new_img = tk.PhotoImage(width=w, height=h)
    highlight_start = int(h * (1 - bottom_ratio))
    for x in range(w):
        for y in range(h):
            pixel = img.get(x, y)
            # ``PhotoImage.get`` may return a tuple or an empty string for
            # transparency.  Normalise to ``#rrggbb`` when a colour is present.
            alpha_px = None
            if isinstance(pixel, tuple):
                if len(pixel) == 4:
                    if pixel[3] == 0:
                        continue
                    alpha_px = pixel[3]
                pixel = f"#{pixel[0]:02x}{pixel[1]:02x}{pixel[2]:02x}"
            if not pixel:
                continue
            lf = factor * bottom_factor if y >= highlight_start else factor
            overlay = (179, 255, 179) if y >= highlight_start else (255, 255, 255)
            alpha = bottom_alpha if y >= highlight_start else top_alpha

            # Blend first to inject the glow colour, then lighten so the tint is
            # preserved yet brighter.
            blended = _blend_with(pixel, overlay, alpha)
            light = _lighten_color(blended, lf)

            if alpha_px is not None:
                new_img.put(f"{light}{alpha_px:02x}", (x, y))
            else:
                new_img.put(light, (x, y))
    return new_img


def add_hover_highlight(
    button: ttk.Button, image: tk.PhotoImage, factor: float = 1.4
) -> tk.PhotoImage:
    """Swap *button* image to a lighter variant on hover.

    The returned :class:`tk.PhotoImage` is the generated hover image including a
    subtle light glow toward the bottom edge.  A reference to both normal and
    hover images is stored on the button to avoid them being garbage collected.
    """

    hover_img = _lighten_image(image, factor)
    button.configure(image=image)
    # Preserve references so Tk does not discard the images
    button._normal_image = image  # type: ignore[attr-defined]
    button._hover_image = hover_img  # type: ignore[attr-defined]
    button.bind("<Enter>", lambda _e: button.configure(image=hover_img))
    button.bind("<Leave>", lambda _e: button.configure(image=image))
    return hover_img


def enable_listbox_hover_highlight(root: tk.Misc) -> None:
    """Highlight listbox and treeview rows on mouse hover.

    A gentle square shading from white to light green is applied to the row
    currently under the cursor.  Bindings are attached at the class level so
    the behaviour is enabled for all ``tk.Listbox`` and ``ttk.Treeview``
    widgets created within *root*.
    """

    def _lb_on_motion(event: tk.Event) -> None:
        lb = event.widget
        if isinstance(lb, str):
            resolver = getattr(root, "nametowidget", lambda name: name)
            try:
                lb = resolver(lb)
            except Exception:
                return
        # Accept any object implementing the listbox API so tests can supply
        # lightweight stand-ins without requiring a full tk.Listbox instance.
        required = {"size", "nearest", "itemconfig", "itemcget", "cget"}
        if not all(hasattr(lb, attr) for attr in required):
            return
        size = lb.size()
        if size == 0:
            return

        index = lb.nearest(event.y)
        if index < 0 or index >= size:
            prev = getattr(lb, "_hover_index", None)
            if prev is not None and 0 <= prev < size:
                lb.itemconfig(prev, background=getattr(lb, "_default_bg", "white"))
                lb._hover_index = None  # type: ignore[attr-defined]
            return
        prev = getattr(lb, "_hover_index", None)
        if prev is not None and prev != index and 0 <= prev < size:
            lb.itemconfig(prev, background=getattr(lb, "_default_bg", "white"))
        if getattr(lb, "_default_bg", None) is None:
            lb._default_bg = lb.itemcget(index, "background") or lb.cget("background")  # type: ignore[attr-defined]
        hover = _blend_with(lb._default_bg, (204, 255, 204), 0.5)  # type: ignore[arg-type]
        lb.itemconfig(index, background=hover)
        lb._hover_index = index  # type: ignore[attr-defined]

    def _lb_on_leave(event: tk.Event) -> None:
        lb = event.widget
        if isinstance(lb, str):
            resolver = getattr(root, "nametowidget", lambda name: name)
            try:
                lb = resolver(lb)
            except Exception:
                return
        if not hasattr(lb, "itemconfig"):
            return
        prev = getattr(lb, "_hover_index", None)
        if prev is not None:
            lb.itemconfig(prev, background=getattr(lb, "_default_bg", "white"))
            lb._hover_index = None  # type: ignore[attr-defined]

    def _tv_on_motion(event: tk.Event) -> None:
        tree_widget = event.widget
        if isinstance(tree_widget, str):
            try:
                tree_widget = root.nametowidget(tree_widget)
            except (KeyError, tk.TclError):
                return
        tree: ttk.Treeview = tree_widget  # type: ignore[assignment]
        item = tree.identify_row(event.y)
        prev = getattr(tree, "_hover_item", None)
        if prev and prev != item:
            if tree.exists(prev):
                tags = list(tree.item(prev, "tags"))
                if "hover" in tags:
                    tags.remove("hover")
                    tree.item(prev, tags=tags)
            tree._hover_item = None  # type: ignore[attr-defined]
        if item:
            if not getattr(tree, "_hover_tagged", False):
                style = ttk.Style(tree)
                style_name = tree.cget("style") or "Treeview"
                bg = style.lookup(style_name, "background") or "#ffffff"
                hover = _blend_with(bg, (204, 255, 204), 0.5)  # type: ignore[arg-type]
                tree.tag_configure("hover", background=hover)
                tree._hover_tagged = True  # type: ignore[attr-defined]
            tags = list(tree.item(item, "tags"))
            if "hover" not in tags:
                tags.append("hover")
                tree.item(item, tags=tags)
            tree._hover_item = item  # type: ignore[attr-defined]

    def _tv_on_leave(event: tk.Event) -> None:
        tree_widget = event.widget
        if isinstance(tree_widget, str):
            try:
                tree_widget = root.nametowidget(tree_widget)
            except (KeyError, tk.TclError):
                return
        tree: ttk.Treeview = tree_widget  # type: ignore[assignment]
        prev = getattr(tree, "_hover_item", None)
        if prev and tree.exists(prev):
            tags = list(tree.item(prev, "tags"))
            if "hover" in tags:
                tags.remove("hover")
                tree.item(prev, tags=tags)
        tree._hover_item = None  # type: ignore[attr-defined]

    root.bind_class("Listbox", "<Motion>", _lb_on_motion, add="+")
    root.bind_class("Listbox", "<Leave>", _lb_on_leave, add="+")
    root.bind_class("Treeview", "<Motion>", _tv_on_motion, add="+")
    root.bind_class("Treeview", "<Leave>", _tv_on_leave, add="+")
