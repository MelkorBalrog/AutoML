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

"""Regression tests for detaching the Safety Management Explorer."""

import os
import sys
import types
import tkinter as tk
import pytest

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(root_dir)


class _Repo:
    diagrams = {}

    @classmethod
    def get_instance(cls):  # pragma: no cover - simple stub
        return cls()


sys.modules.setdefault(
    "mainappsrc.models.sysml.sysml_repository", types.SimpleNamespace(SysMLRepository=_Repo)
)


def _setup_analysis_stub() -> None:
    from dataclasses import dataclass, field

    @dataclass
    class GovernanceModule:
        name: str
        modules: list["GovernanceModule"] = field(default_factory=list)
        diagrams: list[str] = field(default_factory=list)

    class SafetyManagementToolbox:
        def __init__(self):
            self.modules = []
            self.diagrams = {"Gov1": object()}

        def list_diagrams(self):
            pass

    analysis_pkg = types.ModuleType("analysis")
    sm_module = types.ModuleType("analysis.safety_management")
    sm_module.SafetyManagementToolbox = SafetyManagementToolbox
    sm_module.GovernanceModule = GovernanceModule
    analysis_pkg.safety_management = sm_module
    sys.modules.setdefault("analysis", analysis_pkg)
    sys.modules.setdefault("analysis.safety_management", sm_module)


_setup_analysis_stub()

from gui.utils.closable_notebook import ClosableNotebook  # noqa: E402
from gui.explorers.safety_management_explorer import SafetyManagementExplorer  # noqa: E402


class _DummyApp:
    pass


class TestSafetyManagementExplorerDetachment:
    def test_governance_diagrams_visible_after_detach(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("Tk not available")
        nb = ClosableNotebook(root)
        from analysis.safety_management import SafetyManagementToolbox

        toolbox = SafetyManagementToolbox()
        explorer = SafetyManagementExplorer(nb, app=_DummyApp(), toolbox=toolbox)
        nb.add(explorer, text="SME")
        nb.update_idletasks()

        assert explorer.tree.get_children(explorer.root_iid)

        class Event:
            ...

        press = Event()
        press.x = 5
        press.y = 5
        nb._on_tab_press(press)
        nb._dragging = True
        release = Event()
        release.x_root = nb.winfo_rootx() + nb.winfo_width() + 40
        release.y_root = nb.winfo_rooty() + nb.winfo_height() + 40
        nb._on_tab_release(release)

        win = nb._floating_windows[0]
        new_nb = next(w for w in win.winfo_children() if isinstance(w, ClosableNotebook))
        new_explorer = new_nb.nametowidget(new_nb.tabs()[0])

        assert new_explorer.toolbox is toolbox
        assert new_explorer.tree.get_children(new_explorer.root_iid)
        root.destroy()
