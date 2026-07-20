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
from tkinter import ttk
from types import SimpleNamespace

import pytest

from gui.utils.closable_notebook import ClosableNotebook
from gui.architecture import GovernanceDiagramWindow
from gui.windows.architecture import _core_toolbox_template, _toolbox_defs
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


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="Tk display not available")
class TestGovernanceToolboxDetachmentContract:
    """Grouped real-Tk qualification checks for semantic toolbox reconstruction."""

    REQUIRED_CONTROLS = {
        "Task", "Initial", "Final", "Decision", "Merge", "System Boundary",
        "Data", "Document", "Record", "Field Data", "Guideline", "Policy", "Principle",
    }

    @staticmethod
    def _widgets(widget: tk.Misc):
        for child in widget.winfo_children():
            yield child
            yield from TestGovernanceToolboxDetachmentContract._widgets(child)

    @classmethod
    def _buttons(cls, window: GovernanceDiagramWindow) -> list[tk.Widget]:
        return [widget for widget in cls._widgets(window.toolbox)
                if isinstance(widget, (tk.Button, ttk.Button))]

    @staticmethod
    def _ids(window: GovernanceDiagramWindow) -> tuple[tuple[str, ...], tuple[str, ...]]:
        state = window.toolbox_state
        return (state.category_ids, tuple(button.button_id for category in state.categories
                                          for button in category.buttons))

    @staticmethod
    def _diagram(root: tk.Tk) -> tuple[ClosableNotebook, GovernanceDiagramWindow]:
        SysMLRepository.reset_instance()
        notebook = ClosableNotebook(root)
        notebook.pack(fill=tk.BOTH, expand=True)
        diagram = SysMLRepository.get_instance().create_diagram("Governance", name="Gov")
        window = GovernanceDiagramWindow(notebook, app=SimpleNamespace(), diagram_id=diagram.diag_id)
        notebook.add(window, text="Gov")
        root.update_idletasks()
        return notebook, window

    @classmethod
    def _detached(cls, notebook: ClosableNotebook) -> GovernanceDiagramWindow:
        class Event:
            pass
        press = Event()
        press.x = press.y = 5
        notebook._on_tab_press(press)
        notebook._dragging = True
        release = Event()
        release.x_root = notebook.winfo_rootx() + notebook.winfo_width() + 40
        release.y_root = notebook.winfo_rooty() + notebook.winfo_height() + 40
        notebook._on_tab_release(release)
        floating = notebook._floating_windows[-1]
        return next(widget for widget in cls._widgets(floating)
                    if isinstance(widget, GovernanceDiagramWindow))

    @staticmethod
    def _assert_scroll_geometry(window: GovernanceDiagramWindow) -> None:
        canvas = window.toolbox_canvas
        canvas.update_idletasks()
        bbox = canvas.bbox("all")
        region = tuple(map(float, canvas.cget("scrollregion").split()))
        assert bbox is not None and len(region) == 4
        assert region[0] <= bbox[0] and region[1] <= bbox[1]
        assert region[2] >= bbox[2] and region[3] >= bbox[3]

    @staticmethod
    def _definition_controls() -> set[str]:
        def controls(definition):
            yield from definition.get("nodes", ())
            yield from definition.get("relations", ())
            for external in definition.get("externals", {}).values():
                yield from controls(external)

        definitions = (*_toolbox_defs().values(), _core_toolbox_template())
        return {item for definition in definitions for item in controls(definition)}

    @classmethod
    def _assert_live_buttons(cls, clone: GovernanceDiagramWindow) -> None:
        retained_images = {str(image) for image in clone._icons.values()}
        for button in cls._buttons(clone):
            command = button.cget("command")
            image = button.cget("image")
            assert command and clone.tk.call("info", "commands", command)
            assert image and image in retained_images
            clone.current_tool = "__before_invoke__"
            button.invoke()
            assert clone.current_tool != "__before_invoke__"

    def test_ordered_categories_controls_commands_and_icons_survive(self, monkeypatch) -> None:
        # Avoid modal dialogs while retaining the real command wiring.
        for method in ("add_work_product", "add_generic_work_product", "add_lifecycle_phase"):
            monkeypatch.setattr(GovernanceDiagramWindow, method,
                                lambda self, tool=method: self.select_tool(tool))
        root = tk.Tk()
        notebook, original = self._diagram(root)
        original.toolbox_var.set(original.toolbox_state.category_ids[-1])
        original._switch_toolbox()
        active = original.toolbox_var.get()
        expected_ids = self._ids(original)
        clone = self._detached(notebook)

        assert self._ids(clone) == expected_ids
        assert clone.toolbox_var.get() == active
        report = clone.verify_toolbox_view()
        assert report["expected_category_ids"] == report["actual_category_ids"]
        assert report["expected_button_ids"] == report["actual_button_ids"]
        labels = {button.cget("text") for button in self._buttons(clone)}
        assert self.REQUIRED_CONTROLS <= labels
        assert "Task" in clone.tool_buttons and clone.tool_buttons["Task"].cget("text") == "Task"
        assert self._definition_controls() <= labels
        self._assert_live_buttons(clone)
        root.destroy()

    @pytest.mark.parametrize("cycle", ["focus", "resize"])
    def test_focus_and_resize_cycles_keep_one_stable_complete_view(self, cycle: str) -> None:
        root = tk.Tk()
        notebook, original = self._diagram(root)
        clone = self._detached(notebook)
        expected = self._ids(clone)
        view_identity = id(clone.toolbox)
        for index in range(100):
            if cycle == "focus":
                clone.canvas.focus_force()
                clone.toolbox_selector.focus_force()
            else:
                clone.master.winfo_toplevel().geometry(f"{900 + index % 7}x{600 + index % 5}")
            root.update_idletasks()
            assert self._ids(clone) == expected
            assert id(clone.toolbox) == view_identity
            assert clone.winfo_exists() and clone.toolbox.winfo_exists()
            self._assert_scroll_geometry(clone)
        root.destroy()

    def test_repeated_detach_and_dock_preserves_descriptor_view_equivalence(self) -> None:
        root = tk.Tk()
        notebook, _original = self._diagram(root)
        expected = None
        for _ in range(100):
            clone = self._detached(notebook)
            expected = expected or self._ids(clone)
            assert self._ids(clone) == expected
            report = clone.verify_toolbox_view()
            assert report["expected_category_ids"] == report["actual_category_ids"]
            assert report["expected_button_ids"] == report["actual_button_ids"]
            floating = notebook._floating_windows[-1]
            floating.event_generate("<<NoOp>>")
            floating.protocol("WM_DELETE_WINDOW")
            floating.tk.call(floating.protocol("WM_DELETE_WINDOW"))
            root.update_idletasks()
            assert len(notebook.tabs()) == 1
        root.destroy()
