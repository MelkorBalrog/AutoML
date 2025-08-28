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

"""Regression tests for detached governance diagram widgets."""

from __future__ import annotations

import os
import tkinter as tk
from types import SimpleNamespace

import pytest

from gui.utils.closable_notebook import ClosableNotebook
from gui.architecture import GovernanceDiagramWindow
from mainappsrc.models.sysml.sysml_repository import SysMLRepository


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
class TestGovernanceDiagramDetachment:
    def _detach(self, nb: ClosableNotebook) -> GovernanceDiagramWindow:
        class Event:
            pass

        press = Event()
        press.x = 5
        press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True
        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)
        win = nb._floating_windows[-1]
        new_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        return next(w for w in new_nb.winfo_children() if isinstance(w, GovernanceDiagramWindow))

    def test_detached_canvas_retains_items_and_colors(self) -> None:
        SysMLRepository.reset_instance()
        root = tk.Tk()
        nb = ClosableNotebook(root)
        repo = SysMLRepository.get_instance()
        diag = repo.create_diagram("Governance", name="Gov")
        win = GovernanceDiagramWindow(nb, app=SimpleNamespace(), diagram_id=diag.diag_id)
        win.canvas.create_rectangle(10, 10, 40, 40, fill="green", outline="blue", tags=("node",))
        clicked: list[tk.Event] = []
        win.canvas.bind("<Button-1>", lambda e: clicked.append(e))
        nb.add(win, text="Gov")
        nb.update_idletasks()
        clone = self._detach(nb)
        item = clone.canvas.find_all()[0]
        assert clone.canvas.itemcget(item, "fill") == "green"
        assert clone.canvas.itemcget(item, "outline") == "blue"
        assert "node" in clone.canvas.gettags(item)
        clone.canvas.event_generate("<Button-1>", x=15, y=15)
        assert clicked, "Canvas binding lost after detachment"
        root.destroy()

    def test_detached_diagram_displays_toolbox_on_left(self) -> None:
        SysMLRepository.reset_instance()
        root = tk.Tk()
        nb = ClosableNotebook(root)
        repo = SysMLRepository.get_instance()
        diag = repo.create_diagram("Governance", name="Gov")
        win = GovernanceDiagramWindow(nb, app=SimpleNamespace(), diagram_id=diag.diag_id)
        nb.add(win, text="Gov")
        nb.update_idletasks()
        clone = self._detach(nb)
        assert isinstance(clone.canvas, tk.Canvas)
        toolbox = clone.toolbox
        assert isinstance(toolbox, tk.Widget)
        assert toolbox.pack_info().get("side") == "left"
        root.destroy()

    def test_detached_diagram_has_single_canvas_with_content(self) -> None:
        SysMLRepository.reset_instance()
        root = tk.Tk()
        nb = ClosableNotebook(root)
        repo = SysMLRepository.get_instance()
        diag = repo.create_diagram("Governance", name="Gov")
        win = GovernanceDiagramWindow(nb, app=SimpleNamespace(), diagram_id=diag.diag_id)
        win.canvas.create_rectangle(5, 5, 20, 20, fill="red")
        nb.add(win, text="Gov")
        nb.update_idletasks()
        clone = self._detach(nb)

        def canvases(widget: tk.Widget) -> list[tk.Canvas]:
            found: list[tk.Canvas] = []
            for child in widget.winfo_children():
                if isinstance(child, tk.Canvas):
                    found.append(child)
                found.extend(canvases(child))
            return found

        all_canvases = canvases(clone)
        populated = [c for c in all_canvases if c.find_all()]
        assert len(populated) == 1
        root.destroy()
