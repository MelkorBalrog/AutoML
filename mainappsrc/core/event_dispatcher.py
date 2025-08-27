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

"""Event binding utilities for :class:`AutoMLApp`.

The :class:`EventDispatcher` centralises keyboard shortcut and tab-related
bindings so that the main application class is less cluttered and easier to
reason about.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - circular import guard
    from .AutoML import AutoMLApp


class EventDispatcher:
    """Register UI event bindings for :class:`AutoMLApp`."""

    def __init__(self, app: AutoMLApp) -> None:
        self.app = app

    # ------------------------------------------------------------------
    # Keyboard shortcuts
    # ------------------------------------------------------------------
    def register_keyboard_shortcuts(self) -> None:
        """Attach all global keyboard shortcuts."""
        root = self.app.root
        root.bind('<<StyleChanged>>', self.app.refresh_styles)
        root.bind("<Control-n>", lambda event: self.app.project_manager.new_model())
        root.bind("<Control-s>", lambda event: self.app.project_manager.save_model())
        root.bind("<Control-o>", lambda event: self.app.project_manager.load_model())
        root.bind("<Control-f>", lambda event: self.app.open_search_toolbox())
        root.bind("<Control-r>", lambda event: self.app.calculate_overall())
        root.bind("<Control-m>", lambda event: self.app.calculate_pmfh())
        root.bind("<Control-=>", lambda event: self.app.zoom_in())
        root.bind("<Control-minus>", lambda event: self.app.zoom_out())
        root.bind("<Control-u>", lambda event: self.app.user_manager.edit_user_name())
        root.bind("<Control-d>", lambda event: self.app.edit_description())
        root.bind("<Control-l>", lambda event: self.app.edit_rationale())
        root.bind("<Control-g>", lambda event: self.app.edit_gate_type())
        root.bind("<Control-e>", lambda event: self.app.edit_severity())
        root.bind(
            "<Control-Shift-c>",
            lambda event: self.app.add_node_of_type("Confidence Level"),
        )
        root.bind(
            "<Control-Shift-r>",
            lambda event: self.app.add_node_of_type("Robustness Score"),
        )
        root.bind(
            "<Control-Shift-g>",
            lambda event: self.app.add_node_of_type("GATE"),
        )
        root.bind(
            "<Control-Shift-b>",
            lambda event: self.app.add_node_of_type("Basic Event"),
        )
        root.bind(
            "<Control-Shift-t>",
            lambda event: self.app.add_node_of_type("Triggering Condition"),
        )
        root.bind(
            "<Control-Shift-f>",
            lambda event: self.app.add_node_of_type("Functional Insufficiency"),
        )
        root.bind_all("<Control-c>", lambda event: self.app.copy_node(), add="+")
        root.bind_all("<Control-x>", lambda event: self.app.cut_node(), add="+")
        root.bind_all("<Control-v>", lambda event: self.app.paste_node(), add="+")
        root.bind(
            "<Control-p>",
            lambda event: self.app.save_diagram_png(),
        )
        root.bind_all("<Control-z>", self.app._undo_hotkey, add="+")
        root.bind_all("<Control-y>", self.app._redo_hotkey, add="+")
        root.bind("<F1>", lambda event: self.app.show_about())

    # ------------------------------------------------------------------
    # Tab and widget events
    # ------------------------------------------------------------------
    def register_tab_events(self) -> None:
        """Bind events for explorer, tools and document tabs."""
        app = self.app
        lifecycle = getattr(app, "lifecycle_ui", app)
        app._explorer_tab.bind(
            "<Enter>",
            getattr(lifecycle, "on_explorer_tab_enter", lambda _e: app.show_explorer(animate=True)),
        )
        app._explorer_tab.bind(
            "<Leave>",
            getattr(lifecycle, "on_explorer_tab_leave", lambda _e: None),
        )
        app.explorer_pane.bind("<Enter>", lambda _e: app._cancel_explorer_hide())
        app.explorer_pane.bind("<Leave>", lambda _e: app._schedule_explorer_hide())
        app.explorer_pane.bind("<Configure>", lambda _e: app._limit_explorer_size())

        app.analysis_tree.bind("<Double-1>", app.on_analysis_tree_double_click)
        app.analysis_tree.bind("<Button-3>", app.on_analysis_tree_right_click)
        app.analysis_tree.bind("<<TreeviewSelect>>", app.on_analysis_tree_select)

        app.lifecycle_cb.bind("<<ComboboxSelected>>", app.on_lifecycle_selected)

        app.prop_view.bind("<Configure>", app._resize_prop_columns)
        app.prop_view.bind("<Map>", app._resize_prop_columns)
        app.prop_frame.bind("<Configure>", app._resize_prop_columns)

        app.tools_nb.bind("<Motion>", app.lifecycle_ui._on_tool_tab_motion)
        app.tools_nb.bind("<Leave>", lambda _e: app._tools_tip.hide())

        app.doc_nb.bind("<<NotebookTabClosed>>", app.lifecycle_ui._on_tab_close)
        app.doc_nb.bind("<<NotebookTabChanged>>", app.lifecycle_ui._on_tab_change)
        app.doc_nb.bind("<Motion>", app.lifecycle_ui._on_doc_tab_motion)
        app.doc_nb.bind("<Leave>", lambda _e: app._doc_tip.hide())
