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

"""Session isolation tests for governance toolboxes."""

import types
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import gui.architecture as arch
from gui.architecture import GovernanceDiagramWindow
from mainappsrc.models.sysml.sysml_repository import SysMLRepository


class DummyWidget:
    def __init__(self, *a, **k):
        pass

    def pack(self, *a, **k):
        pass

    def pack_forget(self, *a, **k):
        pass

    def bind(self, *a, **k):
        pass

    def configure(self, *a, **k):
        pass

    def destroy(self, *a, **k):
        pass


class DummyFrame:
    def __init__(self):
        self.destroyed = False

    def pack(self, *a, **k):
        pass

    def pack_forget(self, *a, **k):
        pass

    def destroy(self):
        self.destroyed = True

    def winfo_exists(self):
        return not self.destroyed


class TestGovernanceToolboxSessionIsolation:
    """Grouped tests for toolbox isolation across diagram windows."""

    def _init(self, repo):
        def fake_sysml_init(
            self,
            master,
            title,
            tools,
            diagram_id=None,
            app=None,
            history=None,
            relation_tools=None,
            tool_groups=None,
        ):
            self.app = app
            self.repo = repo
            self.diagram_id = diagram_id
            self.toolbox = DummyWidget()
            self.tools_frame = DummyWidget()
            self.rel_frame = DummyWidget()
            self.toolbox_selector = DummyWidget()
            self.toolbox_var = types.SimpleNamespace(get=lambda: "Governance Core", set=lambda v: None)
            self._toolbox_frames = {}
            self._frame_loaders = {"Governance Core": DummyFrame}
            self.canvas = types.SimpleNamespace(master=DummyWidget(), configure=lambda *a, **k: None)

        return fake_sysml_init

    def test_frames_not_shared_between_windows(self, monkeypatch):
        SysMLRepository._instance = None
        repo = SysMLRepository.get_instance()
        monkeypatch.setattr(arch.SysMLDiagramWindow, "__init__", self._init(repo))
        monkeypatch.setattr(arch, "draw_icon", lambda *a, **k: None)
        monkeypatch.setattr(arch.GovernanceDiagramWindow, "_rebuild_toolboxes", lambda self: None)

        win1 = GovernanceDiagramWindow(None, None, diagram_id="D1")
        win2 = GovernanceDiagramWindow(None, None, diagram_id="D2")

        for win in (win1, win2):
            win.toolbox_var = types.SimpleNamespace(get=lambda: "Governance Core", set=lambda v: None)

        win1._switch_toolbox()
        frame1 = win1._toolbox_frames["Governance Core"][0]

        win2._switch_toolbox()
        frame2 = win2._toolbox_frames["Governance Core"][0]

        assert frame1 is not frame2
        assert frame1.winfo_exists()
        assert frame2.winfo_exists()
