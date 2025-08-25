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

"""Utilities to refresh AutoML application views."""

from __future__ import annotations

from typing import TYPE_CHECKING

from gui.toolboxes.safety_management_toolbox import SafetyManagementToolbox
from mainappsrc.models.sysml.sysml_repository import SysMLRepository
from analysis.models import REQUIREMENT_WORK_PRODUCTS

if TYPE_CHECKING:  # pragma: no cover - for type checking only
    from .automl_core import AutoMLApp


class ViewUpdater:
    """Encapsulate view-refreshing logic for :class:`AutoMLApp`."""

    def __init__(self, app: AutoMLApp) -> None:
        self.app = app

    def _insert_module(self, tree, mod, parent, index_map):
        """Insert a module into the analysis tree if the parent exists.

        The GUI can trigger refreshes while elements are being modified. If a
        parent item was removed between refreshes, attempting to insert under
        that missing parent would raise ``TclError``. Guard against this by
        verifying the parent still exists before inserting.
        """

        if not tree.exists(parent):
            return

        node = tree.insert(
            parent,
            "end",
            text=mod.name,
            open=True,
            image=getattr(self.app, "pkg_icon", None),
        )
        for sub in sorted(mod.modules, key=lambda m: m.name):
            self._insert_module(tree, sub, node, index_map)
        for name in sorted(mod.diagrams):
            idx = index_map.get(name)
            if idx is not None:
                tree.insert(
                    node,
                    "end",
                    text=name,
                    tags=("gov", str(idx)),
                    image=getattr(self.app, "gsn_diagram_icon", None),
                )

    def update_views(self) -> None:
        """Refresh project views based on current model state."""

        app = self.app
        app.refresh_model()
        # Compute occurrence counts from the current tree
        app.occurrence_counts = app.compute_occurrence_counts()

        if hasattr(app, "analysis_tree"):
            tree = app.analysis_tree
            tree.delete(*tree.get_children())

            repo = SysMLRepository.get_instance()
            global_enabled = getattr(app, "enabled_work_products", set())
            smt = getattr(app, "safety_mgmt_toolbox", None)
            if smt and getattr(smt, "work_products", None):
                phase_enabled = smt.enabled_products()
            else:
                phase_enabled = global_enabled
            enabled = global_enabled & phase_enabled

            # --- Safety & Security Management Section ---
            app.management_diagrams = sorted(
                [
                    d
                    for d in repo.visible_diagrams().values()
                    if "safety-management" in getattr(d, "tags", [])
                ],
                key=lambda d: d.name or d.diag_id,
            )
            mgmt_root = tree.insert("", "end", text="Safety & Security Management", open=True)
            gov_root = tree.insert(
                mgmt_root,
                "end",
                text="Safety & Security Governance Diagrams",
                open=True,
            )
            app.safety_mgmt_toolbox = getattr(app, "safety_mgmt_toolbox", SafetyManagementToolbox())
            toolbox = app.safety_mgmt_toolbox
            app.governance_manager.attach_toolbox(toolbox)
            toolbox.list_diagrams()
            app.update_lifecycle_cb()
            app.refresh_tool_enablement()

            def _visible(analysis_name: str, doc_name: str) -> bool:
                return toolbox.document_visible(analysis_name, doc_name)

            index_map = {
                (d.name or d.diag_id): idx
                for idx, d in enumerate(app.management_diagrams)
            }

            def _in_any_module(name, modules):
                for mod in modules:
                    if name in mod.diagrams or _in_any_module(name, mod.modules):
                        return True
                return False

            for mod in sorted(toolbox.modules, key=lambda m: m.name):
                self._insert_module(tree, mod, gov_root, index_map)

            for name in sorted(toolbox.diagrams.keys()):
                if not _in_any_module(name, toolbox.modules):
                    idx = index_map.get(name)
                    if idx is not None:
                        tree.insert(
                            gov_root,
                            "end",
                            text=name,
                            tags=("gov", str(idx)),
                            image=getattr(app, "gsn_diagram_icon", None),
                        )

            # --- GSN Diagrams Section ---
            def _collect_gsn_diagrams(module):
                diagrams = list(module.diagrams)
                for sub in module.modules:
                    diagrams.extend(_collect_gsn_diagrams(sub))
                return diagrams

            app.all_gsn_diagrams = sorted(
                list(getattr(app, "gsn_diagrams", []))
                + [
                    d
                    for m in getattr(app, "gsn_modules", [])
                    for d in _collect_gsn_diagrams(m)
                ],
                key=lambda d: d.root.user_name or d.diag_id,
            )
            app.gsn_diagram_map = {d.diag_id: d for d in app.all_gsn_diagrams}
            app.gsn_module_map = {}

            gsn_root = tree.insert(mgmt_root, "end", text="GSN Diagrams", open=True)

            def add_gsn_module(module, parent):
                mid = str(id(module))
                node = tree.insert(
                    parent,
                    "end",
                    text=module.name,
                    open=True,
                    tags=("gsnmod", mid),
                    image=getattr(app, "gsn_module_icon", None),
                )
                app.gsn_module_map[mid] = module
                for sub in sorted(module.modules, key=lambda m: m.name):
                    add_gsn_module(sub, node)
                for diag in sorted(
                    module.diagrams, key=lambda d: d.root.user_name or d.diag_id
                ):
                    add_gsn_diagram(diag, node)

            def add_gsn_diagram(diag, parent):
                tree.insert(
                    parent,
                    "end",
                    text=diag.root.user_name or diag.diag_id,
                    tags=("gsn", diag.diag_id),
                    image=getattr(app, "gsn_diagram_icon", None),
                )

            for mod in sorted(getattr(app, "gsn_modules", []), key=lambda m: m.name):
                add_gsn_module(mod, gsn_root)
            for diag in sorted(
                getattr(app, "gsn_diagrams", []), key=lambda d: d.root.user_name or d.diag_id
            ):
                add_gsn_diagram(diag, gsn_root)

            tree.insert(
                mgmt_root,
                "end",
                text="Safety & Security Case Explorer",
                tags=("safetycase", "0"),
            )

            # --- Verification Reviews Section ---
            app.joint_reviews = [
                r for r in getattr(app, "reviews", []) if getattr(r, "mode", "") == "joint"
            ]
            rev_root = tree.insert(mgmt_root, "end", text="Verification Reviews", open=True)
            for idx, review in enumerate(app.joint_reviews):
                tree.insert(
                    rev_root,
                    "end",
                    text=review.name,
                    tags=("jrev", str(idx)),
                )

            # --- System Design (Item Definition) Section ---
            sys_root = tree.insert(
                "",
                "end",
                text="System Design (Item Definition)",
                open=True,
                tags=("itemdef", "0"),
            )
            app.arch_diagrams = sorted(
                [
                    d
                    for d in repo.visible_diagrams().values()
                    if "safety-management" not in getattr(d, "tags", [])
                ],
                key=lambda d: d.name or d.diag_id,
            )
            arch_root = None
            if "Architecture Diagram" in enabled or getattr(app, "arch_diagrams", []):
                arch_root = tree.insert(sys_root, "end", text="Architecture Diagrams", open=True)

            def add_pkg(pkg_id: str, parent: str) -> None:
                pkg = repo.elements.get(pkg_id)
                if not pkg or pkg.elem_type != "Package":
                    return
                node = parent
                if pkg_id != repo.root_package.elem_id:
                    node = tree.insert(
                        parent,
                        "end",
                        text=pkg.name or pkg_id,
                        open=True,
                        tags=("pkg", pkg_id),
                        image=getattr(app, "pkg_icon", None),
                    )
                sub_pkgs = sorted(
                    [
                        e.elem_id
                        for e in repo.elements.values()
                        if e.elem_type == "Package" and e.owner == pkg_id
                    ],
                    key=lambda i: repo.elements[i].name or i,
                )
                for child_id in sub_pkgs:
                    add_pkg(child_id, node)
                diags = sorted(
                    [
                        d
                        for d in repo.visible_diagrams().values()
                        if d.package == pkg_id
                        and "safety-management" not in getattr(d, "tags", [])
                    ],
                    key=lambda d: d.name or d.diag_id,
                )
                for diag in diags:
                    icon = getattr(app, "diagram_icons", {}).get(diag.diag_type)
                    tree.insert(
                        node,
                        "end",
                        text=diag.name or diag.diag_id,
                        tags=("arch", diag.diag_id),
                        image=icon,
                    )

            root_pkg = getattr(repo, "root_package", None)
            if root_pkg is not None:
                add_pkg(root_pkg.elem_id, arch_root)
            else:
                for diag in app.arch_diagrams:
                    icon = getattr(app, "diagram_icons", {}).get(diag.diag_type)
                    tree.insert(
                        arch_root,
                        "end",
                        text=diag.name or diag.diag_id,
                        tags=("arch", diag.diag_id),
                        image=icon,
                    )

            # --- Safety & Security Concept and Requirements Tools ---
            if "Safety & Security Concept" in enabled:
                tree.insert(
                    sys_root,
                    "end",
                    text="Safety & Security Concept",
                    tags=("safetyconcept", "0"),
                )
            if any(wp in enabled for wp in REQUIREMENT_WORK_PRODUCTS):
                tree.insert(sys_root, "end", text="Requirements Editor", tags=("reqs", "0"))
                tree.insert(
                    sys_root,
                    "end",
                    text="Requirements Explorer",
                    tags=("reqexp", "0"),
                )

            # --- Hazard & Threat Analysis Section ---
            haz_root = None

            def _ensure_haz_root():
                nonlocal haz_root
                if haz_root is None:
                    haz_root = tree.insert("", "end", text="Hazard & Threat Analysis", open=True)

            if "HAZOP" in enabled or getattr(app, "hazop_docs", []):
                _ensure_haz_root()
                hazop_root = tree.insert(haz_root, "end", text="HAZOPs", open=True)
                for idx, doc in enumerate(app.hazop_docs):
                    if not _visible("HAZOP", doc.name):
                        continue
                    tree.insert(hazop_root, "end", text=doc.name, tags=("hazop", str(idx)))
            if "STPA" in enabled or getattr(app, "stpa_docs", []):
                _ensure_haz_root()
                stpa_root = tree.insert(haz_root, "end", text="STPA Analyses", open=True)
                for idx, doc in enumerate(app.stpa_docs):
                    if not _visible("STPA", doc.name):
                        continue
                    tree.insert(stpa_root, "end", text=doc.name, tags=("stpa", str(idx)))
            if "Threat Analysis" in enabled or getattr(app, "threat_docs", []):
                _ensure_haz_root()
                threat_root = tree.insert(haz_root, "end", text="Threat Analyses", open=True)
                for idx, doc in enumerate(app.threat_docs):
                    if not _visible("Threat Analysis", doc.name):
                        continue
                    tree.insert(threat_root, "end", text=doc.name, tags=("threat", str(idx)))
            if "FI2TC" in enabled or getattr(app, "fi2tc_docs", []):
                _ensure_haz_root()
                fi2tc_root = tree.insert(haz_root, "end", text="FI2TC Analyses", open=True)
                for idx, doc in enumerate(app.fi2tc_docs):
                    if not _visible("FI2TC", doc.name):
                        continue
                    tree.insert(fi2tc_root, "end", text=doc.name, tags=("fi2tc", str(idx)))
            if "TC2FI" in enabled or getattr(app, "tc2fi_docs", []):
                _ensure_haz_root()
                tc2fi_root = tree.insert(haz_root, "end", text="TC2FI Analyses", open=True)
                for idx, doc in enumerate(app.tc2fi_docs):
                    if not _visible("TC2FI", doc.name):
                        continue
                    tree.insert(tc2fi_root, "end", text=doc.name, tags=("tc2fi", str(idx)))

            # --- Risk Assessment Section ---
            risk_root = None

            def _ensure_risk_root():
                nonlocal risk_root
                if risk_root is None:
                    risk_root = tree.insert("", "end", text="Risk Assessment", open=True)

            if "Risk Assessment" in enabled or getattr(app, "hara_docs", []):
                _ensure_risk_root()
                assessment_root = tree.insert(risk_root, "end", text="Risk Assessments", open=True)
                for idx, doc in enumerate(app.hara_docs):
                    if not _visible("Risk Assessment", doc.name):
                        continue
                    tree.insert(assessment_root, "end", text=doc.name, tags=("hara", str(idx)))
            if "Product Goal Specification" in enabled:
                _ensure_risk_root()
                tree.insert(risk_root, "end", text="Product Goals", tags=("sg", "0"))

            # --- Safety Analysis Section ---
            safety_root = None

            def _ensure_safety_root():
                nonlocal safety_root
                if safety_root is None:
                    safety_root = tree.insert("", "end", text="Safety Analysis", open=True)

            paa_events = [
                te
                for te in getattr(app, "top_events", [])
                if getattr(te, "analysis_mode", "FTA") == "PAA"
            ] + list(getattr(app, "paa_events", []))
            fta_events = [
                te
                for te in getattr(app, "top_events", [])
                if getattr(te, "analysis_mode", "FTA") != "PAA"
            ]

            if "Prototype Assurance Analysis" in enabled or paa_events:
                _ensure_safety_root()
                paa_root = tree.insert(safety_root, "end", text="PAAs", open=True)
                seen_ids = set()
                for idx, te in enumerate(paa_events):
                    if te.unique_id in seen_ids:
                        continue
                    seen_ids.add(te.unique_id)
                    if not _visible("Prototype Assurance Analysis", te.name):
                        continue
                    tree.insert(paa_root, "end", text=te.name, tags=("paa", str(te.unique_id)))

            if "FTA" in enabled or fta_events:
                _ensure_safety_root()
                fta_root = tree.insert(safety_root, "end", text="FTAs", open=True)
                for idx, te in enumerate(fta_events):
                    if not _visible("FTA", te.name):
                        continue
                    tree.insert(fta_root, "end", text=te.name, tags=("fta", str(te.unique_id)))
            if "CTA" in enabled or getattr(app, "cta_events", []):
                _ensure_safety_root()
                cta_root = tree.insert(safety_root, "end", text="CTAs", open=True)
                for idx, te in enumerate(getattr(app, "cta_events", [])):
                    if not _visible("CTA", te.name):
                        continue
                    tree.insert(cta_root, "end", text=te.name, tags=("cta", str(te.unique_id)))
            if "FMEA" in enabled or getattr(app, "fmeas", []):
                _ensure_safety_root()
                fmea_root = tree.insert(safety_root, "end", text="FMEAs", open=True)
                for idx, fmea in enumerate(app.fmeas):
                    name = fmea["name"]
                    if not _visible("FMEA", name):
                        continue
                    tree.insert(fmea_root, "end", text=name, tags=("fmea", str(idx)))
            if "FMEDA" in enabled or getattr(app, "fmedas", []):
                _ensure_safety_root()
                fmeda_root = tree.insert(safety_root, "end", text="FMEDAs", open=True)
                for idx, doc in enumerate(app.fmedas):
                    name = doc["name"]
                    if not _visible("FMEDA", name):
                        continue
                    tree.insert(fmeda_root, "end", text=name, tags=("fmeda", str(idx)))

        if hasattr(app, "page_diagram") and app.page_diagram is not None:
            if app.page_diagram.canvas.winfo_exists():
                app.page_diagram.redraw_canvas()
            else:
                app.page_diagram = None
        elif hasattr(app, "canvas") and app.canvas is not None and app.canvas.winfo_exists():
            if app.selected_node is not None:
                app.redraw_canvas()
            else:
                app.canvas.delete("all")


__all__ = ["ViewUpdater"]

