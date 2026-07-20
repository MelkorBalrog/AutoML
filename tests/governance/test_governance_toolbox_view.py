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

"""Grouped unit checks for governance semantic projection and lifecycle."""

from types import SimpleNamespace

from gui.utils import governance_toolbox_view as subject


class _Widget:
    def __init__(self, parent=None, **options):
        self.parent = parent
        self.options = options
        self.exists = True
        self.packed = False

    def pack(self, **_options):
        self.packed = True

    def pack_forget(self):
        self.packed = False

    def configure(self, **options):
        self.options.update(options)

    def destroy(self):
        self.exists = False

    def winfo_exists(self):
        return self.exists


class TestGovernanceSemanticToolboxView:
    """Definition projection, command binding, and disposal are one category."""

    def test_builder_exposes_ids_retains_images_and_owns_lifecycle(self, monkeypatch):
        monkeypatch.setattr(subject.ttk, "LabelFrame", _Widget)
        monkeypatch.setattr(subject.ttk, "Button", _Widget)
        calls = []
        context = SimpleNamespace(
            _icon_for=lambda key: f"image:{key}",
            select_tool=lambda command: calls.append(command),
        )
        button = SimpleNamespace(
            button_id="entities/role", label="Role", tool="Role",
            section="elements", icon_key="role-icon", command_id="Role",
            enabled=True, visible=True, initializer=None,
        )
        definition = SimpleNamespace(categories=(SimpleNamespace(
            category_id="Entities", buttons=(button,), sections=(SimpleNamespace(
                section_id="elements", label="elements", buttons=(button,),
            ),),
        ),))

        view = subject.build_governance_toolbox(_Widget(), definition, context)

        assert view.state is subject.ToolboxViewLifecycle.READY
        assert view.category_ids == ("Entities",)
        assert view.button_ids == ("entities/role",)
        assert view.images == {"entities/role": "image:role-icon"}
        view.buttons["entities/role"].options["command"]()
        assert calls == ["Role"]
        view.dispose()
        assert view.state is subject.ToolboxViewLifecycle.DISPOSED
        assert not view.frames and not view.buttons and not view.images
