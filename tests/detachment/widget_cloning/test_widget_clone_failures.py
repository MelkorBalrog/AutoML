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

"""Ensure widget trees detach even when configuration copying fails."""

from __future__ import annotations

import tkinter as tk
from types import SimpleNamespace
import pytest

from gui.utils.closable_notebook import ClosableNotebook
from gui.explorers.safety_case_explorer import SafetyCaseExplorer
from gui.architecture import GovernanceDiagramWindow
from mainappsrc.models.sysml.sysml_repository import SysMLRepository


class TestExplorerCloning:
    """Grouped tests validating explorer detachment robustness."""

    def test_detach_explorer_ignores_config_failures(self, monkeypatch):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        case = SimpleNamespace(name="Case1", solutions=[], phase=None)
        library = SimpleNamespace(list_cases=lambda: [case], cases=[case])
        explorer = SafetyCaseExplorer(nb, library=library)
        nb.add(explorer, text="Explorer")
        nb.update_idletasks()

        original = ClosableNotebook._copy_widget_config

        def failing(self, src, dst):
            if isinstance(src, tk.Button):
                raise RuntimeError("boom")
            return original(self, src, dst)

        monkeypatch.setattr(ClosableNotebook, "_copy_widget_config", failing)

        tab_id = nb.tabs()[0]
        nb._detach_tab(tab_id, 20, 20)
        win = nb._floating_windows[0]
        nb2 = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        clone = nb2.nametowidget(nb2.tabs()[0])
        assert clone.tree.get_children("")
        win.destroy()
        root.destroy()


class TestDiagramCloning:
    """Grouped tests validating diagram detachment robustness."""

    def test_detach_diagram_ignores_config_failures(self, monkeypatch):
        SysMLRepository.reset_instance()
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        repo = SysMLRepository.get_instance()
        diag = repo.create_diagram("Governance", name="Gov")
        win = GovernanceDiagramWindow(nb, app=SimpleNamespace(), diagram_id=diag.diag_id)
        nb.add(win, text="Gov")
        nb.update_idletasks()

        original = ClosableNotebook._copy_widget_config

        def failing(self, src, dst):
            if isinstance(src, tk.Button):
                raise RuntimeError("boom")
            return original(self, src, dst)

        monkeypatch.setattr(ClosableNotebook, "_copy_widget_config", failing)

        nb._detach_tab(nb.tabs()[0], 20, 20)
        win2 = nb._floating_windows[0]
        nb2 = next(w for w in win2.winfo_children() if isinstance(w, ClosableNotebook))
        clone = next(w for w in nb2.winfo_children() if isinstance(w, GovernanceDiagramWindow))
        assert isinstance(clone.canvas, tk.Canvas)
        win2.destroy()
        root.destroy()
