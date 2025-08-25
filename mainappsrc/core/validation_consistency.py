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

"""Validation and work product consistency helpers."""


import tkinter as tk
from analysis.models import global_requirements


class Validation_Consistency:
    """Helper functions for input validation and work product management."""

    def __init__(self, app):
        self.app = app

    # ------------------------------------------------------------------
    def validate_float(self, value: str) -> bool:
        """Return ``True`` if ``value`` resembles a floating-point number."""

        if value in ("", "-", "+", ".", "-.", "+.", "e", "E", "e-", "e+", "E-", "E+"):
            return True
        try:
            float(value)
            return True
        except ValueError:
            lower = value.lower()
            if lower.endswith("e"):
                try:
                    float(lower[:-1])
                    return True
                except ValueError:
                    return False
            if lower.endswith(("e-", "e+")):
                try:
                    float(lower[:-2])
                    return True
                except ValueError:
                    return False
            return False

    # ------------------------------------------------------------------
    def compute_validation_criteria(self, req_id):
        app = self.app
        goals = app.get_requirement_goal_names(req_id)
        vals = []
        for g in goals:
            sg = app.find_safety_goal_node(g)
            if not sg:
                continue
            try:
                acc = float(getattr(sg, "validation_target", 1.0))
            except (TypeError, ValueError):
                acc = 1.0
            try:
                sev = float(getattr(sg, "severity", 3)) / 3.0
            except (TypeError, ValueError):
                sev = 1.0
            try:
                cont = float(getattr(sg, "controllability", 3)) / 3.0
            except (TypeError, ValueError):
                cont = 1.0
            vals.append(acc * sev * cont)
        return sum(vals) / len(vals) if vals else 0.0

    def update_validation_criteria(self, req_id):
        req = global_requirements.get(req_id)
        if not req:
            return
        req["validation_criteria"] = self.compute_validation_criteria(req_id)

    def update_all_validation_criteria(self):
        for rid in global_requirements:
            self.update_validation_criteria(rid)

    # ------------------------------------------------------------------
    def enable_process_area(self, area: str) -> str:
        app = self.app
        area = " ".join(area.split())
        if area not in app.tool_listboxes:
            app.tool_categories[area] = []
            app.lifecycle_ui._add_tool_category(area, [])
        return area

    def _update_tool_mapping(self, mapping, tool_name, name) -> None:
        existing = mapping.get(tool_name)
        if isinstance(existing, set):
            existing.add(name)
        elif existing:
            mapping[tool_name] = {existing, name}
        else:
            mapping.setdefault(tool_name, set()).add(name)

    def enable_work_product(self, name: str, *, refresh: bool = True) -> None:
        app = self.app
        info = app.WORK_PRODUCT_INFO.get(name)
        area = tool_name = method_name = None
        if info:
            area, tool_name, method_name = info
            area = self.enable_process_area(area)
            if tool_name not in app.tool_actions:
                action = getattr(app, method_name, None)
                if action:
                    app.tool_actions[tool_name] = action
                    lb = app.tool_listboxes.get(area)
                    if lb and tool_name not in lb.get(0, tk.END):
                        lb.insert(tk.END, tool_name)
            mapping = getattr(app, "tool_to_work_product", {})
            self._update_tool_mapping(mapping, tool_name, name)
        for menu, idx in app.work_product_menus.get(name, []):
            try:
                menu.entryconfig(idx, state=tk.NORMAL)
            except tk.TclError:
                pass
        app.enabled_work_products.add(name)
        parent = app.WORK_PRODUCT_PARENTS.get(name)
        if parent and parent not in app.enabled_work_products:
            self.enable_work_product(parent, refresh=False)
        if refresh and hasattr(app, "update_views"):
            try:
                app.update_views()
            except Exception:
                pass

    def can_remove_work_product(self, name: str) -> bool:
        app = self.app
        attr_map = {
            "HAZOP": "hazop_docs",
            "Risk Assessment": "hara_docs",
            "STPA": "stpa_docs",
            "Threat Analysis": "threat_docs",
            "FI2TC": "fi2tc_docs",
            "TC2FI": "tc2fi_docs",
            "Causal Bayesian Network Analysis": "cbn_docs",
            "FMEA": "reliability_analyses",
            "FMEDA": "fmeda_components",
            "FTA": "top_events",
            "Prototype Assurance Analysis": "top_events",
            "Architecture Diagram": "arch_diagrams",
            "Scenario Library": "scenario_libraries",
            "ODD": "odd_libraries",
            "Qualitative Analysis": (
                "hazop_docs",
                "stpa_docs",
                "threat_docs",
                "fi2tc_docs",
                "tc2fi_docs",
                "hara_docs",
            ),
            "Mission Profile": "mission_profiles",
            "Reliability Analysis": "reliability_analyses",
        }
        attr = attr_map.get(name)
        if not attr:
            return True
        if isinstance(attr, (tuple, list, set)):
            return all(not getattr(app, a, []) for a in attr)
        return not getattr(app, attr, [])

    def disable_work_product(
        self, name: str, *, force: bool = False, refresh: bool = True
    ) -> bool:
        app = self.app
        if not force and not self.can_remove_work_product(name):
            return False
        app.enabled_work_products.discard(name)
        for menu, idx in app.work_product_menus.get(name, []):
            state = tk.DISABLED
            for other, entries in app.work_product_menus.items():
                if (
                    other != name
                    and other in app.enabled_work_products
                    and (menu, idx) in entries
                ):
                    state = tk.NORMAL
                    break
            try:
                menu.entryconfig(idx, state=state)
            except tk.TclError:
                pass
        info = app.WORK_PRODUCT_INFO.get(name)
        if info:
            area, tool_name, _ = info
            if tool_name:
                still_in_use = False
                for wp in app.enabled_work_products:
                    wp_info = app.WORK_PRODUCT_INFO.get(wp)
                    if wp_info and wp_info[1] == tool_name:
                        still_in_use = True
                        break
                if not still_in_use:
                    lb = app.tool_listboxes.get(area)
                    if lb:
                        for i in range(lb.size()):
                            if lb.get(i) == tool_name:
                                lb.delete(i)
                                break
                        if lb.size() == 0:
                            app.tool_listboxes.pop(area, None)
                            app.tool_categories.pop(area, None)
                            lifecycle = getattr(app, "lifecycle_ui", None)
                            if lifecycle and hasattr(lifecycle, "_remove_tool_category"):
                                lifecycle._remove_tool_category(area)
                    app.tool_actions.pop(tool_name, None)
        parent = app.WORK_PRODUCT_PARENTS.get(name)
        if parent and parent in app.enabled_work_products:
            if not any(
                app.WORK_PRODUCT_PARENTS.get(wp) == parent
                for wp in app.enabled_work_products
            ):
                self.disable_work_product(parent, force=True, refresh=False)
        if refresh and hasattr(app, "update_views"):
            try:
                app.update_views()
            except Exception:
                pass
        return True

    # ------------------------------------------------------------------
    def ensure_fta_tab(self):
        app = self.app
        mode = getattr(app, "diagram_mode", "FTA")
        tab_info = app.analysis_tabs.get(mode)
        if not tab_info or not tab_info["tab"].winfo_exists():
            app._create_fta_tab(mode)
        else:
            app.canvas_tab = tab_info["tab"]
            app.canvas = tab_info["canvas"]
            app.hbar = tab_info["hbar"]
            app.vbar = tab_info["vbar"]

    def enable_paa_actions(self, enabled: bool) -> None:
        app = self.app
        if hasattr(app, "paa_menu"):
            state = tk.NORMAL if enabled else tk.DISABLED
            for key in ("add_confidence", "add_robustness"):
                app.paa_menu.entryconfig(app._paa_menu_indices[key], state=state)

