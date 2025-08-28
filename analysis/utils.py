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

"""Utility helpers for analysis package."""

from typing import Iterable, List, Dict, Tuple
import math
import tkinter as tk
from tkinter import ttk, font as tkFont

from analysis.constants import CHECK_MARK, CROSS_MARK
from analysis.fmeda_utils import compute_fmeda_metrics as _compute_fmeda_metrics

try:  # pragma: no cover - fallback for script context
    from AutoML.config.automl_constants import PMHF_TARGETS
except Exception:  # pragma: no cover - fallback for script context
    from config.automl_constants import PMHF_TARGETS

from analysis.user_config import CURRENT_USER_NAME
from mainappsrc.models.fta.fault_tree_node import FaultTreeNode
from mainappsrc.subapps.fta_subapp import FTASubApp


# Mapping tables from risk assessment ratings to probabilities.
#
# The chosen values reflect rule‑of‑thumb probabilities commonly used in
# functional‑safety workshops: each step increases the likelihood by roughly an
# order of magnitude. They provide a starting point when field data is not yet
# available and align with interpretations published in industry literature.
# Projects with better data can refine these mappings as needed.
EXPOSURE_PROBABILITIES = {1: 1e-4, 2: 1e-3, 3: 1e-2, 4: 1e-1}
CONTROLLABILITY_PROBABILITIES = {1: 1e-3, 2: 1e-2, 3: 1e-1}
SEVERITY_PROBABILITIES = {1: 1e-3, 2: 1e-2, 3: 1e-1}


def update_probability_tables(
    exposure: dict | None = None,
    controllability: dict | None = None,
    severity: dict | None = None,
) -> None:
    """Replace default probability mappings with values from *exposure*,
    *controllability* and *severity*.

    Each argument should be a mapping from rating level to probability. Missing
    arguments leave the current mapping unchanged. The dictionaries are updated
    in-place so references held elsewhere remain valid.
    """

    if exposure is not None:
        EXPOSURE_PROBABILITIES.clear()
        EXPOSURE_PROBABILITIES.update(
            {int(k): float(v) for k, v in dict(exposure).items()}
        )
    if controllability is not None:
        CONTROLLABILITY_PROBABILITIES.clear()
        CONTROLLABILITY_PROBABILITIES.update(
            {int(k): float(v) for k, v in dict(controllability).items()}
        )
    if severity is not None:
        SEVERITY_PROBABILITIES.clear()
        SEVERITY_PROBABILITIES.update(
            {int(k): float(v) for k, v in dict(severity).items()}
        )


def normalize_probability_mapping(mapping: dict | None) -> dict:
    """Return *mapping* with integer keys and float values.

    Project files store probability tables with string keys.  This helper
    converts such mappings back to the numeric form expected by the rest of the
    application.  ``None`` yields an empty dictionary.
    """

    if not mapping:
        return {}
    return {int(k): float(v) for k, v in dict(mapping).items()}


def exposure_to_probability(level: int) -> float:
    """Return ``P(E|HB)`` for the given exposure rating.

    The mapping follows a common industry heuristic where exposure levels 1–4
    correspond to probabilities ``1e-4``, ``1e-3``, ``1e-2`` and ``1e-1``.
    """
    return EXPOSURE_PROBABILITIES.get(int(level), 1.0)


def controllability_to_probability(level: int) -> float:
    """Return ``P(C|E)`` for the given controllability rating.

    Ratings 1–3 map to probabilities ``1e-3``, ``1e-2`` and ``1e-1``
    respectively.
    """
    return CONTROLLABILITY_PROBABILITIES.get(int(level), 1.0)


def severity_to_probability(level: int) -> float:
    """Return ``P(S|C)`` for the given severity rating.

    Severity levels 1–3 map to ``1e-3``, ``1e-2`` and ``1e-1`` respectively.
    """
    return SEVERITY_PROBABILITIES.get(int(level), 1.0)


def append_unique_insensitive(items: List[str], name: str) -> None:
    """Append ``name`` to ``items`` if not already present (case-insensitive)."""
    if not name:
        return
    name = name.strip()
    if not name:
        return
    lower = name.lower()
    for existing in items:
        if existing.lower() == lower:
            return
    items.append(name)


def derive_validation_target(acceptance_rate: float,
                             exposure_given_hb: float,
                             uncontrollable_given_exposure: float,
                             severity_given_uncontrollable: float) -> float:
    """Derive a validation target from an acceptance criterion.

    This implements the ISO 21448 relationship for the rate of hazardous
    behaviour :math:`R_{HB}`. All rates are expressed in **events per hour**.

    The acceptance criterion :math:`A_H` is decomposed into conditional
    probabilities for exposure (``exposure_given_hb``), lack of
    controllability (``uncontrollable_given_exposure``) and severity
    (``severity_given_uncontrollable``). The resulting validation target is
    calculated using:

    ``R_HB = A_H / (P_E|HB * P_C|E * P_S|C)``

    For example, ``A_H = 1e-8/h`` with ``P_E|HB = 0.05``, ``P_C|E = 0.1``
    and ``P_S|C = 0.01`` yields ``R_HB = 2e-4/h``.

    Parameters
    ----------
    acceptance_rate:
        Acceptance criterion for the harm :math:`A_H` in events per hour.
    exposure_given_hb:
        Conditional probability of being exposed to the scenario given the
        hazardous behaviour, :math:`P_{E|HB}`.
    uncontrollable_given_exposure:
        Probability that the hazardous behaviour is not controllable once
        exposure occurs, :math:`P_{C|E}`.
    severity_given_uncontrollable:
        Probability of the relevant severity assuming the control action
        fails, :math:`P_{S|C}`.

    Returns
    -------
    float
        The acceptable rate of the hazardous behaviour ``R_HB`` (events per
        hour) that can be used as a validation target.

    Raises
    ------
    ValueError
        If any of the probability terms is less than or equal to zero.
    """

    denominator = (
        exposure_given_hb *
        uncontrollable_given_exposure *
        severity_given_uncontrollable
    )

    if denominator <= 0:
        raise ValueError(
            "Probability factors must be positive to derive a validation target"
        )

    return acceptance_rate / denominator


# ---------------------------------------------------------------------------
# Safety analysis helpers moved from ``safety_analysis_service``
# ---------------------------------------------------------------------------


def compute_fmeda_metrics(
    events: Iterable[object],
    reliability_components: Iterable[object],
    get_safety_goal_asil,
):
    """Compute FMEDA metrics for ``events``."""

    return _compute_fmeda_metrics(
        list(events), reliability_components, get_safety_goal_asil
    )


def compute_failure_prob(
    app: object,
    node: object,
    failure_mode_ref: object | None = None,
    formula: str | None = None,
):
    """Return probability of failure for ``node`` based on FIT rate."""

    tau = 1.0
    if getattr(app, "mission_profiles", None):
        tau = app.mission_profiles[0].tau
    if tau <= 0:
        tau = 1.0
    fm = (
        app.find_node_by_id_all(failure_mode_ref)
        if failure_mode_ref
        else app.get_failure_mode_node(node)
    )
    if (
        getattr(node, "fault_ref", "")
        and failure_mode_ref is None
        and getattr(node, "failure_mode_ref", None) is None
    ):
        fit = app.get_fit_for_fault(node.fault_ref)
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
    comp_name = app.get_component_name_for_node(fm)
    qty = next(
        (c.quantity for c in getattr(app, "reliability_components", []) if c.name == comp_name),
        1,
    )
    if qty <= 0:
        qty = 1
    lam = (fit / qty) / 1e9
    if f == "exponential":
        return 1 - math.exp(-lam * t)
    return lam * t


def update_basic_event_probabilities(app: object) -> None:
    """Update failure probabilities for all basic events."""

    for be in app.get_all_basic_events():
        be.failure_prob = compute_failure_prob(app, be)


def calculate_pmfh(app: object) -> None:
    """Calculate probabilistic metric for hardware failures."""

    update_basic_event_probabilities(app)
    spf = 0.0
    lpf = 0.0
    for be in app.get_all_basic_events():
        fm = app.get_failure_mode_node(be)
        fit = getattr(be, "fmeda_fit", None)
        if fit is None or fit == 0.0:
            fit = getattr(fm, "fmeda_fit", 0.0)
            if (
                not fit
                and getattr(be, "fault_ref", "")
                and getattr(be, "failure_mode_ref", None) is None
            ):
                fault = be.fault_ref
                for entry in app.get_all_fmea_entries():
                    causes = [
                        c.strip()
                        for c in getattr(entry, "fmea_cause", "").split(";")
                        if c.strip()
                    ]
                    if fault in causes:
                        fit += getattr(entry, "fmeda_fit", 0.0)
        dc = getattr(be, "fmeda_diag_cov", getattr(fm, "fmeda_diag_cov", 0.0))
        if getattr(be, "fmeda_fault_type", "") == "permanent":
            spf += fit * (1 - dc)
        else:
            lpf += fit * (1 - dc)
    app.spfm = spf
    app.lpfm = lpf

    pmhf = 0.0
    for te in getattr(app, "top_events", []):
        asil = getattr(te, "safety_goal_asil", "") or ""
        if asil in PMHF_TARGETS:
            prob = app.helper.calculate_probability_recursive(te)
            te.probability = prob
            pmhf += prob

    app.update_views()
    lines = [f"Total PMHF: {pmhf:.2e}"]
    overall_ok = True
    for te in getattr(app, "top_events", []):
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
    app.pmhf_var.set("\n".join(lines))
    app.pmhf_label.config(
        foreground="green" if overall_ok else "red",
        font=("Segoe UI", 10, "bold"),
    )

    app.refresh_safety_case_table()
    app.refresh_safety_performance_indicators()


def calculate_overall(app: object) -> None:
    """Calculate overall assurance levels for top events."""

    helper = app.helper
    for top_event in getattr(app, "top_events", []):
        helper.calculate_assurance_recursive(top_event, app.top_events)
    app.update_views()
    results = ""
    for top_event in getattr(app, "top_events", []):
        if getattr(top_event, "quant_value", None) is not None:
            disc = helper.discretize_level(top_event.quant_value)
            results += (
                f"Top Event {top_event.display_label}\n"
                f"(Continuous: {top_event.quant_value:.2f}, Discrete: {disc})\n\n"
            )
    app.messagebox.showinfo("Calculation", results.strip())


def build_probability_frame(
    app: object,
    parent: tk.Misc,
    title: str,
    levels: range,
    values: Dict[int, float],
    row: int,
    dialog_font: tkFont.Font,
) -> Dict[int, tk.StringVar]:
    """Create a labelled frame of probability entries."""

    try:
        frame = ttk.LabelFrame(parent, text=title, style="Toolbox.TLabelframe")
    except TypeError:
        frame = ttk.LabelFrame(parent, text=title)
    frame.grid(row=row, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

    vars_dict: Dict[int, tk.StringVar] = {}
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
            validatecommand=(parent.register(app.validate_float), "%P"),
        ).grid(row=0, column=idx * 2 + 1, padx=2, pady=2)
        vars_dict[lvl] = var
    return vars_dict


def assurance_level_text(app: object, level):
    """Return assurance level description."""

    return app.fta_app.assurance_level_text(level)


def metric_to_text(app: object, metric_type, value):
    """Return textual representation for metric."""

    return app.fta_app.metric_to_text(app, metric_type, value)


def analyze_common_causes(app: object, node):
    """Delegate common cause analysis to FTA app."""

    return app.fta_app.analyze_common_causes(app, node)


def build_cause_effect_data(app: object) -> Dict[Tuple[str, str], Dict[str, object]]:
    """Collect cause and effect chain information."""

    rows: Dict[Tuple[str, str], Dict[str, object]] = {}
    for doc in getattr(app, "hara_docs", []):
        for e in getattr(doc, "entries", []):
            haz = getattr(e, "hazard", "").strip()
            mal = getattr(e, "malfunction", "").strip()
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

    for doc in getattr(app, "fi2tc_docs", []) + getattr(app, "tc2fi_docs", []):
        for e in getattr(doc, "entries", []):
            haz = e.get("vehicle_effect", "").strip()
            if not haz:
                continue
            fis = [f.strip() for f in e.get("functional_insufficiencies", "").split(";") if f.strip()]
            tcs = [t.strip() for t in e.get("triggering_conditions", "").split(";") if t.strip()]
            for (hz, mal), info in rows.items():
                if hz == haz:
                    info["fis"].update(fis)
                    info["tcs"].update(tcs)

    for be in app.get_all_basic_events():
        mals = [m.strip() for m in getattr(be, "fmeda_malfunction", "").split(";") if m.strip()]
        for (hz, mal), info in rows.items():
            if mal in mals:
                fm = app.get_failure_mode_node(be)
                fm_name = fm.user_name or f"FM {fm.unique_id}"
                info.setdefault("failure_modes", {}).setdefault(fm_name, set()).add(
                    be.user_name or f"BE {be.unique_id}"
                )
                fault = getattr(be, "fault_ref", "").strip()
                if fault:
                    info.setdefault("faults", set()).add(fault)

    return rows


def build_cause_effect_graph(
    row: Dict[str, object]
) -> Tuple[Dict[str, Tuple[str, str]], List[Tuple[str, str]], Dict[str, Tuple[int, int]]]:
    """Return nodes, edges and positions for a cause-and-effect diagram."""

    nodes: Dict[str, Tuple[str, str]] = {}
    edges: List[Tuple[str, str]] = []

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

    for threat, paths in sorted(row.get("threats", {}).items()):
        thr_y = 0
        pos[f"thr:{threat}"] = (8, thr_y)
        y_path = thr_y
        for path in sorted(paths):
            pos[f"ap:{path}"] = (12, y_path)
            y_path += 2

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


def render_cause_effect_diagram(row: Dict[str, object]):
    """Render *row* as a PIL image matching the on-screen diagram."""

    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:  # pragma: no cover - optional dependency
        return None
    import textwrap

    nodes, edges, pos = build_cause_effect_graph(row)
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


def sync_cyber_risk_to_goals(app: object):
    """Synchronise cyber risk to goals via risk application."""

    return app.risk_app.sync_cyber_risk_to_goals(app)
