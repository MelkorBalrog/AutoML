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
"""Service facade for safety analysis helpers."""

from __future__ import annotations

from typing import Iterable
import math
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont

from .fmea_service import FMEAService
from mainappsrc.models.fta.fault_tree_node import FaultTreeNode
from analysis.constants import CHECK_MARK, CROSS_MARK
from analysis.fmeda_utils import compute_fmeda_metrics as _compute_fmeda_metrics
from analysis.utils import update_probability_tables as _update_probability_tables

if __package__ and __package__.startswith("AutoML"):
    from AutoML.config.automl_constants import PMHF_TARGETS
else:  # pragma: no cover - script context
    from config.automl_constants import PMHF_TARGETS

class SafetyAnalysisService:
    """Wrap :class:`SafetyAnalysis_FTA_FMEA` and expose utility helpers."""

    def __init__(self, app: object) -> None:
        from mainappsrc.core.safety_analysis import SafetyAnalysis_FTA_FMEA

        self.app = app
        self._impl = SafetyAnalysis_FTA_FMEA(app)

    def __getattr__(self, name: str):
        return getattr(self._impl, name)

    # ------------------------------------------------------------------
    # FMEDA metric helpers
    def compute_fmeda_metrics(self, events: Iterable[FaultTreeNode]):
        """Compute FMEDA metrics for ``events``.

        Parameters
        ----------
        events:
            Iterable of :class:`FaultTreeNode` instances representing
            failure modes to analyse.
        """
        return _compute_fmeda_metrics(
            list(events),
            getattr(self.app, "reliability_components", []),
            self.get_safety_goal_asil,
        )

    # ------------------------------------------------------------------
    # Probability and reliability helpers moved from probability_reliability.py

    def update_probability_tables(
        self,
        exposure: dict | None,
        controllability: dict | None,
        severity: dict | None,
    ) -> None:
        """Delegate probability table updates to shared utility."""
        _update_probability_tables(exposure, controllability, severity)

    # ------------------------------------------------------------------
    def compute_failure_prob(self, node, failure_mode_ref=None, formula=None):
        """Return probability of failure for ``node`` based on FIT rate."""
        tau = 1.0
        if self.app.mission_profiles:
            tau = self.app.mission_profiles[0].tau
        if tau <= 0:
            tau = 1.0
        fm = (
            self.app.find_node_by_id_all(failure_mode_ref)
            if failure_mode_ref
            else self.app.get_failure_mode_node(node)
        )
        if (
            getattr(node, "fault_ref", "")
            and failure_mode_ref is None
            and getattr(node, "failure_mode_ref", None) is None
        ):
            fit = self.app.get_fit_for_fault(node.fault_ref)
        else:
            fit = getattr(fm, "fmeda_fit", getattr(node, "fmeda_fit", 0.0))
        t = tau
        formula = formula or getattr(node, "prob_formula", getattr(fm, "prob_formula", "linear"))
        f = str(formula).strip().lower()
        if f == "constant":
            try:
                return float(getattr(node, "failure_prob", 0.0))
            except (TypeError, ValueError):
                return 0.0
        if fit <= 0:
            return 0.0
        comp_name = self.app.get_component_name_for_node(fm)
        qty = next((c.quantity for c in self.app.reliability_components if c.name == comp_name), 1)
        if qty <= 0:
            qty = 1
        lam = (fit / qty) / 1e9
        if f == "exponential":
            return 1 - math.exp(-lam * t)
        else:
            return lam * t

    # ------------------------------------------------------------------
    def update_basic_event_probabilities(self):
        """Update failure probabilities for all basic events."""
        for be in self.app.get_all_basic_events():
            be.failure_prob = self.compute_failure_prob(be)

    # ------------------------------------------------------------------
    def calculate_pmfh(self):
        self.update_basic_event_probabilities()
        spf = 0.0
        lpf = 0.0
        for be in self.app.get_all_basic_events():
            fm = self.app.get_failure_mode_node(be)
            fit = getattr(be, "fmeda_fit", None)
            if fit is None or fit == 0.0:
                fit = getattr(fm, "fmeda_fit", 0.0)
                if (
                    not fit
                    and getattr(be, "fault_ref", "")
                    and getattr(be, "failure_mode_ref", None) is None
                ):
                    fault = be.fault_ref
                    for entry in self.app.get_all_fmea_entries():
                        causes = [c.strip() for c in getattr(entry, "fmea_cause", "").split(";") if c.strip()]
                        if fault in causes:
                            fit += getattr(entry, "fmeda_fit", 0.0)
            dc = getattr(be, "fmeda_diag_cov", getattr(fm, "fmeda_diag_cov", 0.0))
            if be.fmeda_fault_type == "permanent":
                spf += fit * (1 - dc)
            else:
                lpf += fit * (1 - dc)
        self.app.spfm = spf
        self.app.lpfm = lpf

        pmhf = 0.0
        for te in self.app.top_events:
            asil = getattr(te, "safety_goal_asil", "") or ""
            if asil in PMHF_TARGETS:
                prob = self.app.helper.calculate_probability_recursive(te)
                te.probability = prob
                pmhf += prob

        self.app.update_views()
        lines = [f"Total PMHF: {pmhf:.2e}"]
        overall_ok = True
        for te in self.app.top_events:
            asil = getattr(te, "safety_goal_asil", "") or ""
            if asil not in PMHF_TARGETS:
                continue
            target = PMHF_TARGETS.get(asil, 1.0)
            ok = te.probability <= target
            overall_ok = overall_ok and ok
            symbol = CHECK_MARK if ok else CROSS_MARK
            lines.append(
                f"{te.user_name or te.display_label}: {te.probability:.2e} <= {target:.1e} {symbol}"
            )
        self.app.pmhf_var.set("\n".join(lines))
        self.app.pmhf_label.config(
            foreground="green" if overall_ok else "red",
            font=("Segoe UI", 10, "bold"),
        )

        self.app.refresh_safety_case_table()
        self.app.refresh_safety_performance_indicators()

    # ------------------------------------------------------------------
    def calculate_overall(self):
        helper = self.app.helper
        for top_event in self.app.top_events:
            helper.calculate_assurance_recursive(top_event, self.app.top_events)
        self.app.update_views()
        results = ""
        for top_event in self.app.top_events:
            if top_event.quant_value is not None:
                disc = helper.discretize_level(top_event.quant_value)
                results += (
                    f"Top Event {top_event.display_label}\n"
                    f"(Continuous: {top_event.quant_value:.2f}, Discrete: {disc})\n\n"
                )
        self.app.messagebox.showinfo("Calculation", results.strip())

    # ------------------------------------------------------------------
    def _build_probability_frame(
        self,
        parent,
        title: str,
        levels: range,
        values: dict,
        row: int,
        dialog_font: tkFont.Font,
    ) -> dict:
        """Create a labelled frame of probability entries."""
        try:
            frame = ttk.LabelFrame(parent, text=title, style="Toolbox.TLabelframe")
        except TypeError:
            frame = ttk.LabelFrame(parent, text=title)
        frame.grid(row=row, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

        vars_dict: dict[int, tk.StringVar] = {}
        for idx, lvl in enumerate(levels):
            ttk.Label(frame, text=f"{lvl}:", font=dialog_font).grid(
                row=0, column=idx * 2, padx=2, pady=2
            )
            var = tk.StringVar(value=str(values.get(lvl, 0.0)))
            ttk.Entry(
                frame,
                textvariable=var,
                width=8,
                font=dialog_font,
                validate="key",
                validatecommand=(parent.register(self.app.validate_float), "%P"),
            ).grid(row=0, column=idx * 2 + 1, padx=2, pady=2)
            vars_dict[lvl] = var
        return vars_dict

    # ------------------------------------------------------------------
    def assurance_level_text(self, level):
        return self.app.fta_app.assurance_level_text(level)

    # ------------------------------------------------------------------
    def metric_to_text(self, metric_type, value):
        return self.app.fta_app.metric_to_text(self.app, metric_type, value)

    # ------------------------------------------------------------------
    def analyze_common_causes(self, node):
        return self.app.fta_app.analyze_common_causes(self.app, node)

    # ------------------------------------------------------------------
    def build_cause_effect_data(self):
        """Collect cause and effect chain information."""
        rows = {}
        for doc in self.app.hara_docs:
            for e in doc.entries:
                haz = e.hazard.strip()
                mal = e.malfunction.strip()
                if not haz or not mal:
                    continue
                key = (haz, mal)
                info = rows.setdefault(
                    key,
                    {
                        "hazard": haz,
                        "malfunction": mal,
                        "fis": set(),
                        "tcs": set(),
                        "failure_modes": {},
                        "faults": set(),
                        "threats": {},
                        "attack_paths": set(),
                    },
                )
                info = rows[key]
                cyber = getattr(e, "cyber", None)
                if cyber:
                    threat = getattr(cyber, "threat_scenario", "").strip()
                    if threat:
                        paths = [
                            p.get("path", "").strip()
                            for p in getattr(cyber, "attack_paths", [])
                            if p.get("path", "").strip()
                        ]
                        info["threats"].setdefault(threat, set()).update(paths)
                        info["attack_paths"].update(paths)

        for doc in self.app.fi2tc_docs + self.app.tc2fi_docs:
            for e in doc.entries:
                haz = e.get("vehicle_effect", "").strip()
                if not haz:
                    continue
                fis = [f.strip() for f in e.get("functional_insufficiencies", "").split(";") if f.strip()]
                tcs = [t.strip() for t in e.get("triggering_conditions", "").split(";") if t.strip()]
                for (hz, mal), info in rows.items():
                    if hz == haz:
                        info["fis"].update(fis)
                        info["tcs"].update(tcs)

        for be in self.app.get_all_basic_events():
            mals = [m.strip() for m in getattr(be, "fmeda_malfunction", "").split(";") if m.strip()]
            for (hz, mal), info in rows.items():
                if mal in mals:
                    fm_label = self.app.format_failure_mode_label(be)
                    faults = set(self.app.get_faults_for_failure_mode(be))
                    info["failure_modes"].setdefault(fm_label, set()).update(faults)
                    info["faults"].update(faults)

        for te in self.app.top_events:
            te_mal = getattr(te, "malfunction", "").strip()
            if not te_mal:
                continue
            basic_nodes = [
                n for n in self.app.get_all_nodes_table(te) if n.node_type.upper() == "BASIC EVENT"
            ]
            for be in basic_nodes:
                for (hz, mal), info in rows.items():
                    if mal == te_mal:
                        fm_label = self.app.format_failure_mode_label(be)
                        faults = set(self.app.get_faults_for_failure_mode(be))
                        fault = getattr(be, "fault_ref", "") or getattr(be, "description", "")
                        if fault:
                            faults.add(fault)
                        info["failure_modes"].setdefault(fm_label, set()).update(faults)
                        info["faults"].update(faults)

        return sorted(rows.values(), key=lambda r: (r["hazard"].lower(), r["malfunction"].lower()))

    # ------------------------------------------------------------------
    def _build_cause_effect_graph(self, row):
        """Return nodes, edges and positions for a cause-and-effect diagram."""
        nodes: dict[str, tuple[str, str]] = {}
        edges: list[tuple[str, str]] = []

        haz_label = row["hazard"]
        mal_label = row["malfunction"]
        haz_id = f"haz:{haz_label}"
        mal_id = f"mal:{mal_label}"
        nodes[haz_id] = (haz_label, "hazard")
        nodes[mal_id] = (mal_label, "malfunction")
        edges.append((haz_id, mal_id))

        for fm, faults in sorted(row.get("failure_modes", {}).items()):
            fm_id = f"fm:{fm}"
            nodes[fm_id] = (fm, "failure_mode")
            edges.append((mal_id, fm_id))
            for fault in sorted(faults):
                fault_id = f"fault:{fault}"
                nodes[fault_id] = (fault, "fault")
                edges.append((fm_id, fault_id))
        for fi in sorted(row.get("fis", [])):
            fi_id = f"fi:{fi}"
            nodes[fi_id] = (fi, "fi")
            edges.append((haz_id, fi_id))
        for tc in sorted(row.get("tcs", [])):
            tc_id = f"tc:{tc}"
            nodes[tc_id] = (tc, "tc")
            edges.append((haz_id, tc_id))

        for threat, paths in sorted(row.get("threats", {}).items()):
            thr_id = f"thr:{threat}"
            nodes[thr_id] = (threat, "threat")
            edges.append((mal_id, thr_id))
            for path in sorted(paths):
                ap_id = f"ap:{path}"
                nodes[ap_id] = (path, "attack_path")
                edges.append((thr_id, ap_id))

        pos = {haz_id: (0, 0), mal_id: (4, 0)}
        y_fm = 0
        for fm, faults in sorted(row.get("failure_modes", {}).items()):
            fm_y = y_fm * 4
            pos[f"fm:{fm}"] = (8, fm_y)
            y_fault = fm_y
            for fault in sorted(faults):
                pos[f"fault:{fault}"] = (12, y_fault)
                y_fault += 2
            y_fm += 1
        y_fi = -2
        for fi in sorted(row.get("fis", [])):
            pos[f"fi:{fi}"] = (2, y_fi)
            y_fi -= 2
        y_tc = y_fi
        for tc in sorted(row.get("tcs", [])):
            pos[f"tc:{tc}"] = (2, y_tc)
            y_tc -= 2
        y_ts = y_tc
        for ts, paths in sorted(row.get("threats", {}).items()):
            pos[f"threat:{ts}"] = (2, y_ts)
            y_ap = y_ts
            for ap in sorted(paths):
                pos[f"ap:{ap}"] = (3, y_ap)
                y_ap -= 2
            y_ts = min(y_ts, y_ap) - 2

        y_item = y_fm * 4
        for threat, paths in sorted(row.get("threats", {}).items()):
            thr_y = y_item
            pos[f"thr:{threat}"] = (8, thr_y)
            y_path = thr_y
            for path in sorted(paths):
                pos[f"ap:{path}"] = (12, y_path)
                y_path += 2
            y_item += 4

        y_thr = y_fm
        for threat, paths in sorted(row.get("threats", {}).items()):
            thr_y = y_thr * 4
            pos[f"thr:{threat}"] = (8, thr_y)
            y_ap = thr_y
            for path in sorted(paths):
                pos[f"ap:{path}"] = (12, y_ap)
                y_ap += 2
            y_thr += 1

        used_nodes: set[str] = set()
        for u, v in edges:
            used_nodes.add(u)
            used_nodes.add(v)
        for key in list(nodes.keys()):
            if key not in used_nodes:
                nodes.pop(key, None)
        for key in list(pos.keys()):
            if key not in used_nodes:
                pos.pop(key, None)

        min_x = min(x for x, _ in pos.values())
        min_y = min(y for _, y in pos.values())
        if min_x < 0 or min_y < 0:
            for key, (x, y) in list(pos.items()):
                pos[key] = (x - min_x, y - min_y)

        return nodes, edges, pos

    # ------------------------------------------------------------------
    def render_cause_effect_diagram(self, row):
        """Render *row* as a PIL image matching the on-screen diagram."""
        try:
            from PIL import Image, ImageDraw, ImageFont
        except Exception:
            return None
        import textwrap

        nodes, edges, pos = self._build_cause_effect_graph(row)
        color_map = {
            "hazard": "#F08080",
            "malfunction": "#ADD8E6",
            "failure_mode": "#FFA500",
            "fault": "#D3D3D3",
            "fi": "#FFFFE0",
            "tc": "#E6E6FA",
            "threat": "#FFC0CB",
            "attack_path": "#FFFACD",
        }

        width = (max(x for x, _ in pos.values()) + 1) * 200
        height = (max(y for _, y in pos.values()) + 1) * 100
        img = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()

        for u, v in edges:
            x1, y1 = pos[u]
            x2, y2 = pos[v]
            draw.line((x1 * 200 + 100, y1 * 100 + 50, x2 * 200 + 100, y2 * 100 + 50), fill="black")

        for key, (label, typ) in nodes.items():
            x, y = pos[key]
            cx, cy = x * 200 + 100, y * 100 + 50
            r = 40
            fill = color_map.get(typ, "#FFFFFF")
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=fill, outline="black")
            text = textwrap.fill(str(label), 20)
            bbox = draw.multiline_textbbox((0, 0), text, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            draw.multiline_text((cx - tw / 2, cy - th / 2), text, font=font, align="center")

        return img

    # ------------------------------------------------------------------
    def sync_cyber_risk_to_goals(self):
        return self.app.risk_app.sync_cyber_risk_to_goals(self.app)


__all__ = ["SafetyAnalysisService", "FMEAService"]
