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

import tkinter as tk
import tkinter.font as tkFont
import textwrap
from tkinter import ttk, simpledialog
from gui.controls import messagebox
from gui import format_name_with_phase, add_treeview_scrollbars, TranslucidButton
try:  # Guard against environments where the tooltip module is unavailable
    from gui.utils.tooltip import ToolTip
except Exception:  # pragma: no cover - fallback for minimal installs
    ToolTip = None  # type: ignore
import math
import re
import types
import weakref
import copy
from pathlib import Path
from dataclasses import dataclass, field, asdict, replace
from typing import Dict, List, Tuple, Callable

from mainappsrc.models.sysml.sysml_repository import SysMLRepository, SysMLDiagram, SysMLElement
from gui.styles.style_manager import StyleManager
from gui.utils.drawing_helper import fta_drawing_helper
from config import load_diagram_rules, load_json_with_comments
import json
from gui.utils.icon_factory import create_icon
from gui.controls.button_utils import set_uniform_button_width
from tools.memory_manager import manager as memory_manager

from mainappsrc.models.sysml.sysml_spec import SYSML_PROPERTIES
from analysis.models import (
    global_requirements,
    ASIL_ORDER,
    StpaDoc,
    REQUIREMENT_WORK_PRODUCTS,
    REQUIREMENT_TYPE_OPTIONS,
)
from analysis.safety_management import (
    ALLOWED_PROPAGATIONS,
    ALLOWED_ANALYSIS_USAGE,
    ACTIVE_TOOLBOX,
    SAFETY_ANALYSIS_WORK_PRODUCTS,
    ALLOWED_USAGE,
    UNRESTRICTED_USAGE_SOURCES,
)

def _labelframe(master, *, text: str):
    """Create a themed ``ttk.LabelFrame`` and fall back when style unsupported."""
    try:
        return ttk.LabelFrame(master, text=text, style="Toolbox.TLabelframe")
    except TypeError:
        return ttk.LabelFrame(master, text=text)

# ---------------------------------------------------------------------------
# Appearance customization
# ---------------------------------------------------------------------------
# Colors for AutoML object types come from the global StyleManager so diagrams
# can be easily re-themed.
OBJECT_COLORS = StyleManager.get_instance().styles


_next_obj_id = 1
# Pixel distance used when detecting clicks on connection lines
CONNECTION_SELECT_RADIUS = 15


_CONFIG_PATH = (
    Path(__file__).resolve().parents[1] / "config" / "rules" / "diagram_rules.json"
)
_CONFIG = load_diagram_rules(_CONFIG_PATH)

_REQ_PATTERN_PATH = (
    Path(__file__).resolve().parents[1]
    / "config"
    / "patterns"
    / "requirement_patterns.json"
)


def _load_requirement_relations(path: Path = _REQ_PATTERN_PATH) -> list[str]:
    """Return unique relationship labels referenced by requirement patterns."""

    try:
        patterns = load_json_with_comments(path)
    except Exception:  # pragma: no cover - fallback if file missing
        return []
    rels: set[str] = set()
    for item in patterns:
        trig = item.get("Trigger", "")
        rels.update(re.findall(r"\[(.+?)\]", trig))
    return sorted(rels)


REQ_PATTERN_RELATIONS = _load_requirement_relations()

# Track open Architecture windows so toolbox layouts can refresh when rules change
ARCH_WINDOWS: set[weakref.ReferenceType] = set()

# Diagram types that belong to the generic "Architecture Diagram" work product
ARCH_DIAGRAM_TYPES = set(_CONFIG.get("arch_diagram_types", []))

# Elements available in the Safety & AI Lifecycle toolbox
SAFETY_AI_NODES = _CONFIG.get("ai_nodes", [])
SAFETY_AI_NODE_TYPES = set(SAFETY_AI_NODES)

# Relation labels treated as Safety & AI links
SAFETY_AI_RELATIONS = _CONFIG.get("ai_relations", [])
SAFETY_AI_RELATION_SET = set(SAFETY_AI_RELATIONS)

# Elements available in the Governance Elements toolbox
_PLAN_TYPES = {
    "Safety Plan",
    "Security Plan",
    "Mitigation Plan",
    "Deployment Plan",
    "Maintenance Plan",
    "Decommission Plan",
    "Verification Plan",
}

# Create Safety & AI Lifecycle toolbox frame
# Create toolbox for additional governance elements
# Create toolbox for additional governance elements grouped by class
# Repack toolbox to include selector


def _normalize_plan_types(items: list[str]) -> list[str]:
    """Replace specific plan variants with generic 'Plan' and deduplicate."""
    seen: set[str] = set()
    normalized: list[str] = []
    for item in items:
        item = "Plan" if item in _PLAN_TYPES else item
        if item not in seen:
            seen.add(item)
            normalized.append(item)
    return normalized


GOV_ELEMENT_NODES = _normalize_plan_types(
    _CONFIG.get("governance_element_nodes", [])
)
GOV_ELEMENT_RELATIONS = sorted(
    set(SAFETY_AI_RELATIONS) | set(REQ_PATTERN_RELATIONS)
)

# Process areas available in governance diagrams
PROCESS_AREA_OPTIONS = [
    "System Design (Item Definition)",
    "Hazard & Threat Analysis",
    "Risk Assessment",
    "Safety & Security Management",
    "Safety Analysis",
    "Scenario",
]

# Mapping of work products to the process areas that allow them
WORK_PRODUCT_AREA_MAP = {
    "Architecture Diagram": "System Design (Item Definition)",
    "Safety & Security Concept": "System Design (Item Definition)",
    "Mission Profile": "Safety Analysis",
    "Reliability Analysis": "Safety Analysis",
    "Causal Bayesian Network Analysis": "Safety Analysis",
    "Safety & Security Case": "Safety & Security Management",
    "GSN Argumentation": "Safety & Security Management",
    "Product Goal Specification": "System Design (Item Definition)",
    **{wp: "System Design (Item Definition)" for wp in REQUIREMENT_WORK_PRODUCTS},
    "HAZOP": "Hazard & Threat Analysis",
    "STPA": "Hazard & Threat Analysis",
    "Threat Analysis": "Hazard & Threat Analysis",
    "FI2TC": "Hazard & Threat Analysis",
    "TC2FI": "Hazard & Threat Analysis",
    "Risk Assessment": "Risk Assessment",
    "FTA": "Safety Analysis",
    "CTA": "Safety Analysis",
    "Prototype Assurance Analysis": "Safety Analysis",
    "FMEA": "Safety Analysis",
    "FMEDA": "Safety Analysis",
    "Scenario Library": "Scenario",
    "ODD": "Scenario",
}


def _work_products_for_area(area: str) -> list[str]:
    return [wp for wp, a in WORK_PRODUCT_AREA_MAP.items() if a == area]


def _repo_phase(repo: SysMLRepository) -> str | None:
    """Safely return the repository's active phase."""
    return getattr(repo, "active_phase", None)

# Create Safety & AI Lifecycle toolbox frame
# Create toolbox for additional governance elements grouped by class
# Repack toolbox to include selector

# expose the icon factory under the old name used throughout the module
draw_icon = create_icon


def _make_gov_element_classes(nodes: list[str]) -> dict[str, list[str]]:
    base = {
        "Entities": [n for n in ["Organization", "Business Unit", "Role"] if n in nodes],
        "Artifacts": [n for n in ["Data", "Document", "Record", "Field Data"] if n in nodes],
        "Governance": [
            n
            for n in [
                "Policy",
                "Principle",
                "Procedure",
                "Guideline",
                "Standard",
                "Metric",
                "Safety Compliance",
            ]
            if n in nodes
        ],
        "Processes": [
            n
            for n in [
                "Process",
                "Activity",
                "Task",
                "Operation",
                "Manufacturing Process",
            ]
            if n in nodes
        ],
        "Components": [
            n
            for n in [
                "Driving Function",
                "Software Component",
                "Component",
                "System",
                "Vehicle",
                "Fleet",
                "Model",
            ]
            if n in nodes
        ],
        "Verification": [n for n in ["Test Suite"] if n in nodes],
        "Events": [n for n in ["Incident", "Safety Issue"] if n in nodes],
    }
    known = {n for vals in base.values() for n in vals}
    # Exclude lifecycle phases from the generic management group since a
    # dedicated toolbox command exists for adding them. Keeping them here would
    # create a duplicate button in the governance elements toolbox.
    other = [n for n in nodes if n not in known and n != "Lifecycle Phase"]
    if other:
        base["Safety & Security Mgmt"] = other
    return base


GOV_ELEMENT_CLASSES = _make_gov_element_classes(GOV_ELEMENT_NODES)

# Map node types to their toolbox group for cross-category relationship lookups
NODE_TO_GROUP: dict[str, str] = {}
for group, nodes in GOV_ELEMENT_CLASSES.items():
    for n in nodes:
        NODE_TO_GROUP[n] = group
if SAFETY_AI_NODES:
    for n in SAFETY_AI_NODES:
        NODE_TO_GROUP[n] = "Safety & AI Lifecycle"

# Elements from the governance toolbox that may participate in
# Safety & AI relationships
GOVERNANCE_NODE_TYPES = set(
    _normalize_plan_types(_CONFIG.get("governance_node_types", []))
)
GOV_CORE_NODES = [n for n in ["Work Product", "Lifecycle Phase"] if n in GOVERNANCE_NODE_TYPES]
for n in GOV_CORE_NODES:
    NODE_TO_GROUP[n] = "Governance Core"

# Directed relationship rules for connections between Safety & AI elements.
# Each entry maps a connection type to allowed source and target element
# combinations. Rules are only enforced when both endpoints are Safety & AI
# nodes.
SAFETY_AI_RELATION_RULES: dict[str, dict[str, set[str]]] = {
    conn: {src: set(dests) for src, dests in srcs.items()}
    for conn, srcs in _CONFIG.get("safety_ai_relation_rules", {}).items()
}

# Basic source/target constraints per diagram and connection type
CONNECTION_RULES: dict[str, dict[str, dict[str, set[str]]]] = {
    diag: {
        conn: {src: set(dests) for src, dests in srcs.items()}
        for conn, srcs in conns.items()
    }
    for diag, conns in _CONFIG.get("connection_rules", {}).items()
}

# Maximum number of connections allowed per node type
NODE_CONNECTION_LIMITS: dict[str, int] = _CONFIG.get("node_connection_limits", {})

# Node types that require guards on outgoing flows
GUARD_NODES = set(_CONFIG.get("guard_nodes", []))


def _connection_rule_allows(
    diag_type: str, conn_type: str, src_type: str, dst_type: str
) -> tuple[bool, str]:
    """Return whether connection rules permit the given source and target."""
    conn_rules = CONNECTION_RULES.get(diag_type, {}).get(conn_type)
    if not conn_rules:
        return True, ""
    if diag_type == "Governance Diagram" and conn_type != "Flow":
        src_type = _GOV_TYPE_ALIASES.get(src_type, src_type)
        dst_type = _GOV_TYPE_ALIASES.get(dst_type, dst_type)
    targets = conn_rules.get(src_type, set())
    if dst_type not in targets:
        return False, f"{conn_type} from {src_type} to {dst_type} is not allowed"
    return True, ""


def _relations_for(nodes: list[str]) -> list[str]:
    """Return connection labels relevant to ``nodes`` based on diagram rules."""

    rels: set[str] = set()
    node_set = set(nodes)

    # Only consider relationships defined for Governance diagrams.  Iterating
    # over all diagram rules caused every connection label to appear in each
    # toolbox even when a node had no valid targets for that relation.
    gov_rules = CONNECTION_RULES.get("Governance Diagram", {})
    for rel, srcs in gov_rules.items():
        for src, dests in srcs.items():
            # A relation is relevant only when an element in ``node_set`` can
            # connect to another element in ``node_set`` using that relation.
            # Previously, relations were surfaced whenever a node could act as
            # either source *or* target.  This caused connections that required
            # nodes outside the toolbox to appear.  Filtering to pairs within
            # the toolbox ensures each displayed relationship is actionable for
            # the current context.
            if src in node_set and node_set.intersection(dests):
                rels.add(rel)
    # Apply the same filtering to Safety & AI specific rules.
    for rel, srcs in SAFETY_AI_RELATION_RULES.items():
        for src, dests in srcs.items():
            if src in node_set and node_set.intersection(dests):
                rels.add(rel)
    return sorted(rels)


def _external_relations_for(nodes: list[str]) -> dict[str, dict[str, list[str]]]:
    """Return mapping of related toolbox groups for ``nodes``.

    Each key is another toolbox group name and the value lists the external
    elements and relationships that can connect to ``nodes`` based on the
    current diagram rules.
    """

    externals: dict[str, dict[str, set[str]]] = {}
    node_set = set(nodes)

    def add(group: str, node: str, rel: str) -> None:
        data = externals.setdefault(group, {"nodes": set(), "relations": set()})
        data["nodes"].add(node)
        data["relations"].add(rel)

    gov_rules = CONNECTION_RULES.get("Governance Diagram", {})
    for rel, srcs in gov_rules.items():
        for src, dests in srcs.items():
            src_group = NODE_TO_GROUP.get(src)
            for dest in dests:
                dest_group = NODE_TO_GROUP.get(dest)
                if src in node_set and dest not in node_set and dest_group:
                    add(dest_group, dest, rel)
                elif dest in node_set and src not in node_set and src_group:
                    add(src_group, src, rel)

    for rel, srcs in SAFETY_AI_RELATION_RULES.items():
        for src, dests in srcs.items():
            src_group = NODE_TO_GROUP.get(src)
            for dest in dests:
                dest_group = NODE_TO_GROUP.get(dest)
                if src in node_set and dest not in node_set and dest_group:
                    add(dest_group, dest, rel)
                elif dest in node_set and src not in node_set and src_group:
                    add(src_group, src, rel)

    result: dict[str, dict[str, list[str]]] = {}
    for grp, data in externals.items():
        result[grp] = {
            "nodes": sorted(data["nodes"]),
            "relations": sorted(data["relations"]),
        }
    return result


def _dedup_category(data: dict, seen: set[str] | None = None) -> None:
    """Remove duplicate relations within ``data`` and its externals.

    When ``seen`` is provided the set is used to track relationships across
    categories so each relationship only appears once in the toolbox overall.
    Any relations kept in ``data`` or its externals are added to ``seen`` for
    subsequent calls.
    """

    if seen is None:
        seen = set()
    rels: list[str] = []
    for r in data.get("relations", []) or []:
        if r not in seen:
            seen.add(r)
            rels.append(r)
    data["relations"] = rels
    for sub in data.get("externals", {}).values():
        sub_rels: list[str] = []
        for r in sub.get("relations", []) or []:
            if r not in seen:
                seen.add(r)
                sub_rels.append(r)
        sub["relations"] = sub_rels


def _toolbox_defs() -> dict[str, dict[str, list[str] | dict]]:
    """Return mapping of toolbox name to node/relation lists."""
    defs: dict[str, dict[str, list[str] | dict]] = {}
    for group, nodes in GOV_ELEMENT_CLASSES.items():
        if not nodes:
            continue
        defs[group] = {
            "nodes": nodes,
            "relations": _relations_for(nodes),
            "externals": _external_relations_for(nodes),
        }
    if SAFETY_AI_NODES:
        defs["Safety & AI Lifecycle"] = {
            "nodes": SAFETY_AI_NODES,
            "relations": _relations_for(SAFETY_AI_NODES),
            "externals": _external_relations_for(SAFETY_AI_NODES),
        }
    if GOV_CORE_NODES:
        # Governance core elements like Work Products and Lifecycle Phases are
        # inserted via dedicated actions rather than direct toolbox buttons.
        # Still derive their relationships so users can connect existing
        # boundary elements.
        core = {
            "nodes": [],
            "relations": _relations_for(GOV_CORE_NODES),
            "externals": _external_relations_for(GOV_CORE_NODES),
        }
        _dedup_category(core)
        defs["Governance Core"] = core
    return defs


def _gov_connection_text(node_type: str) -> str:
    """Return tooltip text listing governance connections for ``node_type``."""
    node_type = _GOV_TYPE_ALIASES.get(node_type, node_type)
    rules = CONNECTION_RULES.get("Governance Diagram", {})
    outgoing: dict[str, list[str]] = {}
    incoming: dict[str, list[str]] = {}
    for rel, srcs in rules.items():
        targets = srcs.get(node_type)
        if targets:
            outgoing[rel] = sorted(targets)
        for src, dests in srcs.items():
            if node_type in dests:
                incoming.setdefault(rel, []).append(src)
    if not outgoing and not incoming:
        return ""

    rows: list[tuple[str, str, str]] = []
    for rel in sorted(set(outgoing) | set(incoming)):
        outs = ", ".join(outgoing.get(rel, []))
        ins = ", ".join(sorted(incoming.get(rel, [])))
        rows.append((rel, outs, ins))

    headers = ("Relation", "To Others", "From Others")
    col_widths = [
        max(len(row[i]) for row in rows + [headers]) for i in range(3)
    ]
    lines = [
        " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)),
        "-+-".join("-" * col_widths[i] for i in range(3)),
    ]
    for row in rows:
        lines.append(
            " | ".join(row[i].ljust(col_widths[i]) for i in range(3))
        )
    return "\n".join(lines)

# Node type aliases used when validating governance diagram connections.
# Governance tasks are implemented using SysML ``Action`` elements but are
# presented as "Task" to users.  Mapping aliases before applying connection
# rules ensures that configuration updates targeting "Task" also affect these
# underlying "Action" nodes.
_GOV_TYPE_ALIASES = {"Action": "Task"}

# Object types whose names are displayed below the shape
_BOTTOM_LABEL_TYPES = {
    "Hazard",
    "Incident",
    "Safety Issue",
    "Safety Goal",
    "Organization",
    "Model",
    "Business Unit",
    "Process",
    "Policy",
    "Principle",
    "Guideline",
    "Standard",
    "Metric",
    "Safety Compliance",
    "Data",
    "Field Data",
    "Risk Assessment",
    "Fleet",
    "Vehicle",
    "Driving Function",
    "Manufacturing Process",
    "Operation",
}


# Object types that cannot be resized
_FIXED_SIZE_TYPES = {
    "Initial",
    "Final",
    "Actor",
    "Role",
    "Decision",
    "Merge",
    "Work Product",
} | _BOTTOM_LABEL_TYPES


# Connection types excluding Safety & AI relations used for membership checks
_BASE_CONN_TYPES = {
    "Association",
    "Include",
    "Extend",
    "Flow",
    "Propagate",
    "Propagate by Review",
    "Propagate by Approval",
    "Used By",
    "Used after Review",
    "Used after Approval",
    "Re-use",
    "Trace",
    "Satisfied by",
    "Derived from",
    "Connector",
    "Generalize",
    "Generalization",
    "Communication Path",
    "Aggregation",
    "Composite Aggregation",
    "Control Action",
    "Feedback",
    "Approves",
    "Audits",
    "Authorizes",
    "Constrained by",
    "Consumes",
    "Curation",
    "Delivers",
    "Executes",
    "Monitors",
    "Performs",
    "Produces",
    "Responsible for",
    "Uses",
    "Constrains",
    "Establish",
    "Implement",
    "Validate",
    "Verify",
    "Manufacture",
    "Operate",
    "Inspect",
    "Triage",
    "Improve",
    "Develops",
    "Mitigates",
    "Assesses",
    "Plans",
    "Reviews",
}

_BASE_CONN_TYPES.update(REQ_PATTERN_RELATIONS)

# Ordered list of base connection tools for toolbox composition
_BASE_CONN_TOOLS = [
    "Association",
    "Include",
    "Extend",
    "Flow",
    "Propagate",
    "Propagate by Review",
    "Propagate by Approval",
    "Used By",
    "Used after Review",
    "Used after Approval",
    "Re-use",
    "Trace",
    "Satisfied by",
    "Derived from",
    "Connector",
    "Generalize",
    "Generalization",
    "Communication Path",
    "Aggregation",
    "Composite Aggregation",
    "Control Action",
    "Feedback",
    "Approves",
    "Audits",
    "Authorizes",
    "Constrained by",
    "Consumes",
    "Delivers",
    "Executes",
    "Monitors",
    "Performs",
    "Produces",
    "Responsible for",
    "Uses",
    "Constrains",
    "Establish",
    "Implement",
    "Validate",
    "Verify",
    "Manufacture",
    "Operate",
    "Inspect",
    "Triage",
    "Improve",
    "Develops",
    "Mitigates",
    "Assesses",
    "Plans",
    "Reviews",
]

# Connection types that can link one work product to another.  When a user
# drags one of these relations onto empty canvas, creating the target should
# prompt for a generic work product name instead of inserting an unnamed
# document.
_WORK_PRODUCT_CONN_TYPES = {
    "Trace",
    "Propagate",
    "Propagate by Review",
    "Propagate by Approval",
    "Used By",
    "Used after Review",
    "Used after Approval",
    "Re-use",
    "Satisfied by",
    "Derived from",
}

# Connection types that default to forward arrows
_ARROW_FORWARD_BASE = {
    "Flow",
    "Propagate",
    "Propagate by Review",
    "Propagate by Approval",
    "Used By",
    "Used after Review",
    "Used after Approval",
    "Re-use",
    "Satisfied by",
    "Derived from",
}

# Connection types added above should use forward arrowheads by default
_ARROW_FORWARD_BASE.update(
    {
        "Approves",
        "Audits",
        "Authorizes",
        "Constrained by",
        "Consumes",
        "Curation",
        "Delivers",
        "Executes",
        "Monitors",
        "Performs",
        "Produces",
        "Responsible for",
        "Uses",
        "Constrains",
        "Establish",
        "Implement",
        "Validate",
        "Verify",
        "Manufacture",
        "Operate",
        "Inspect",
        "Triage",
        "Improve",
        "Develops",
        "Mitigates",
        "Assesses",
        "Plans",
        "Reviews",
    }
)

_ARROW_FORWARD_BASE.update(REQ_PATTERN_RELATIONS)


def _all_connection_tools() -> tuple[str, ...]:
    """Return all connection tools including Safety & AI relations."""
    rels = list(_BASE_CONN_TOOLS)
    for r in GOV_ELEMENT_RELATIONS:
        if r not in rels:
            rels.append(r)
    return tuple(rels)


def _arrow_forward_types() -> set[str]:
    """Return connection types that use forward arrowheads."""
    return _ARROW_FORWARD_BASE | SAFETY_AI_RELATION_SET


def _enforce_connection_rules() -> None:
    """Remove existing connections that violate current configuration rules."""
    repo = SysMLRepository.get_instance()
    removed: set[str] = set()
    for diag in repo.diagrams.values():
        diag_rules = CONNECTION_RULES.get(diag.diag_type, {})
        obj_map = {}
        for o in diag.objects:
            oid = o.get("obj_id") if isinstance(o, dict) else getattr(o, "obj_id", None)
            obj_type = o.get("obj_type") if isinstance(o, dict) else getattr(o, "obj_type", None)
            obj_map[oid] = obj_type
        new_conns = []
        for conn in diag.connections:
            src_id = conn.get("src") if isinstance(conn, dict) else getattr(conn, "src", None)
            dst_id = conn.get("dst") if isinstance(conn, dict) else getattr(conn, "dst", None)
            src_type = obj_map.get(src_id)
            dst_type = obj_map.get(dst_id)
            if not src_type or not dst_type:
                rel_id = conn.get("element_id") if isinstance(conn, dict) else getattr(conn, "element_id", "")
                removed.add(rel_id)
                continue
            conn_type = conn.get("conn_type") if isinstance(conn, dict) else getattr(conn, "conn_type", None)
            if diag.diag_type == "Governance Diagram" and conn_type != "Flow":
                src_type = _GOV_TYPE_ALIASES.get(src_type, src_type)
                dst_type = _GOV_TYPE_ALIASES.get(dst_type, dst_type)
            valid = True
            rules = diag_rules.get(conn_type)
            if rules is not None:
                targets = rules.get(src_type)
                if not targets or dst_type not in targets:
                    valid = False
            if valid:
                new_conns.append(conn)
            else:
                rel_id = conn.get("element_id") if isinstance(conn, dict) else getattr(conn, "element_id", "")
                removed.add(rel_id)
        if len(new_conns) != len(diag.connections):
            diag.connections = new_conns
            if diag.relationships:
                diag.relationships = [r for r in diag.relationships if r not in removed]
            repo.touch_diagram(diag.diag_id)
    if removed:
        repo.relationships = [r for r in repo.relationships if r.rel_id not in removed]


def reload_config() -> None:
    """Reload diagram rule configuration at runtime."""
    global _CONFIG, ARCH_DIAGRAM_TYPES, SAFETY_AI_NODES, SAFETY_AI_NODE_TYPES
    global SAFETY_AI_RELATIONS, SAFETY_AI_RELATION_SET, GOVERNANCE_NODE_TYPES
    global GOV_ELEMENT_NODES, GOV_ELEMENT_RELATIONS, GOV_ELEMENT_CLASSES
    global SAFETY_AI_RELATION_RULES, CONNECTION_RULES, NODE_CONNECTION_LIMITS, GUARD_NODES
    global NODE_TO_GROUP, GOV_CORE_NODES, REQ_PATTERN_RELATIONS, _BASE_CONN_TYPES
    global _ARROW_FORWARD_BASE
    _CONFIG = load_diagram_rules(_CONFIG_PATH)
    ARCH_DIAGRAM_TYPES = set(_CONFIG.get("arch_diagram_types", []))
    SAFETY_AI_NODES = _CONFIG.get("ai_nodes", [])
    SAFETY_AI_NODE_TYPES = set(SAFETY_AI_NODES)
    SAFETY_AI_RELATIONS = _CONFIG.get("ai_relations", [])
    SAFETY_AI_RELATION_SET = set(SAFETY_AI_RELATIONS)
    REQ_PATTERN_RELATIONS = _load_requirement_relations()
    GOV_ELEMENT_NODES = _normalize_plan_types(
        _CONFIG.get("governance_element_nodes", [])
    )
    GOV_ELEMENT_RELATIONS = sorted(
        set(SAFETY_AI_RELATIONS) | set(REQ_PATTERN_RELATIONS)
    )
    _BASE_CONN_TYPES.update(REQ_PATTERN_RELATIONS)
    _ARROW_FORWARD_BASE.update(REQ_PATTERN_RELATIONS)
    GOV_ELEMENT_CLASSES = _make_gov_element_classes(GOV_ELEMENT_NODES)
    GOVERNANCE_NODE_TYPES = set(
        _normalize_plan_types(_CONFIG.get("governance_node_types", []))
    )
    NODE_TO_GROUP = {}
    for group, nodes in GOV_ELEMENT_CLASSES.items():
        for n in nodes:
            NODE_TO_GROUP[n] = group
    if SAFETY_AI_NODES:
        for n in SAFETY_AI_NODES:
            NODE_TO_GROUP[n] = "Safety & AI Lifecycle"
    GOV_CORE_NODES = [n for n in ["Work Product", "Lifecycle Phase"] if n in GOVERNANCE_NODE_TYPES]
    for n in GOV_CORE_NODES:
        NODE_TO_GROUP[n] = "Governance Core"
    SAFETY_AI_RELATION_RULES = {
        conn: {src: set(dests) for src, dests in srcs.items()}
        for conn, srcs in _CONFIG.get("safety_ai_relation_rules", {}).items()
    }
    CONNECTION_RULES = {
        diag: {
            conn: {src: set(dests) for src, dests in srcs.items()}
            for conn, srcs in conns.items()
        }
        for diag, conns in _CONFIG.get("connection_rules", {}).items()
    }
    NODE_CONNECTION_LIMITS = _CONFIG.get("node_connection_limits", {})
    GUARD_NODES = set(_CONFIG.get("guard_nodes", []))
    _enforce_connection_rules()
    for ref in list(ARCH_WINDOWS):
        win = ref()
        if win:
            win._rebuild_toolboxes()
        else:
            ARCH_WINDOWS.discard(ref)


def _work_product_name(diag_type: str) -> str:
    """Return work product name for a given diagram type."""
    return "Architecture Diagram" if diag_type in ARCH_DIAGRAM_TYPES else diag_type


def _diag_matches_wp(diag_type: str, work_product: str) -> bool:
    """Return True if *diag_type* is part of *work_product*."""
    if work_product == "Architecture Diagram":
        return diag_type in ARCH_DIAGRAM_TYPES
    return diag_type == work_product


def stpa_tool_enabled(app) -> bool:
    """Return True if STPA Analysis should be available for the diagram.

    The STPA Analysis tool is only enabled when the active governance phase
    declares a "Used" style relationship from an Architecture Diagram to the
    STPA work product and any lifecycle conditions on that relationship are
    satisfied.  In practice this means:

    * "Used By" relations always enable the button.
    * "Used after Review" requires the diagram to be reviewed or approved.
    * "Used after Approval" requires the diagram to be approved.
    * The relationship must be part of the active lifecycle phase if one is
      selected in the safety management toolbox.
    """

    toolbox = getattr(app, "safety_mgmt_toolbox", None) or ACTIVE_TOOLBOX
    if not toolbox:
        return True
    review = getattr(app, "current_review", None)
    reviewed = getattr(review, "reviewed", False)
    approved = getattr(review, "approved", False)
    return "Architecture Diagram" in toolbox.analysis_inputs(
        "STPA", reviewed=reviewed, approved=approved
    )


def _get_next_id() -> int:
    global _next_obj_id
    val = _next_obj_id
    _next_obj_id += 1
    return val


def _format_label(
    _win, name: str, _phase: str | None, obj: "SysMLObject | None" = None
) -> str:
    """Return *name* possibly annotated with a stereotype.

    When rendering governance diagrams every object should display its
    stereotype.  If *obj* is provided and the current diagram is a governance
    diagram, the object's element type (respecting any governance type aliases)
    is converted to a stereotype prefix.  For all other diagrams, or when no
    object is supplied, the name is returned unchanged.
    """

    label = name or ""
    if obj is not None:
        repo = getattr(_win, "repo", None)
        diag_id = getattr(_win, "diagram_id", None)
        diag = repo.diagrams.get(diag_id) if repo and diag_id is not None else None
        if diag and diag.diag_type == "Governance Diagram":
            elem_type = obj.obj_type
            if repo and obj.element_id in repo.elements:
                elem_type = repo.elements[obj.element_id].elem_type
            if elem_type in {"Decision", "Initial", "Final", "Merge"}:
                return ""
            if elem_type == "System Boundary":
                return label
            stereo = _GOV_TYPE_ALIASES.get(elem_type, elem_type).lower()
            label = f"<<{stereo}>>\n{label}".strip()
    return label


def _parse_float(val: str | None, default: float) -> float:
    """Convert *val* to ``float`` or return ``default`` if conversion fails."""
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _part_prop_key(raw: str) -> str:
    """Return canonical property name for a raw part property entry."""
    if not raw:
        return ""
    part = raw.split(":", 1)[0]
    part = part.split("[", 1)[0]
    return part.strip()


def _part_elem_keys(elem) -> set[str]:
    """Return canonical keys for a Part element."""
    if not elem:
        return set()
    name = elem.name or ""
    comp = elem.properties.get("component", "")
    if comp and (not name or name.startswith("Part")):
        name = comp
    if "_" in name and name.rsplit("_", 1)[1].isdigit():
        name = name.rsplit("_", 1)[0]
    base = _part_prop_key(name)
    keys = {base}
    definition = elem.properties.get("definition")
    if definition:
        keys.add(f"{base}:{definition}")
    return keys

def _part_elem_key(elem) -> str:
    """Return a single canonical key (for backward compatibility)."""
    keys = _part_elem_keys(elem)
    return next(iter(keys), "")


def parse_part_property(raw: str) -> tuple[str, str]:
    """Return (property name, block name) parsed from a part property entry."""
    raw = raw.strip()
    prop = raw
    block = raw
    if ":" in raw:
        prop, block = raw.split(":", 1)
    prop = prop.split("[", 1)[0].strip()
    block = block.split("[", 1)[0].strip()
    return (prop or block, block)


def _find_parent_blocks(repo: SysMLRepository, block_id: str) -> set[str]:
    """Return all blocks that directly use ``block_id`` as a part or are
    associated with it."""
    parents: set[str] = set()
    # check IBDs for parts referencing this block
    for parent_id, diag_id in repo.element_diagrams.items():
        diag = repo.diagrams.get(diag_id)
        if not diag:
            continue
        for obj in getattr(diag, "objects", []):
            if obj.get("obj_type") != "Part":
                continue
            if obj.get("properties", {}).get("definition") == block_id:
                parents.add(parent_id)
                break
    # also follow Association and Generalization relationships
    for rel in repo.relationships:
        if rel.rel_type not in ("Association", "Generalization"):
            continue
        if rel.rel_type == "Generalization":
            if rel.source == block_id and rel.target in repo.elements:
                parents.add(rel.target)
            continue
        if rel.source == block_id and rel.target in repo.elements:
            parents.add(rel.target)
        elif rel.target == block_id and rel.source in repo.elements:
            parents.add(rel.source)
    # include father block from internal block diagram linkage
    diag_id = repo.get_linked_diagram(block_id)
    diag = repo.diagrams.get(diag_id)
    if diag and getattr(diag, "father", None) in repo.elements:
        parents.add(diag.father)
    return parents


def _collect_parent_parts(repo: SysMLRepository, block_id: str, visited=None) -> list[str]:
    """Recursively gather parts from all parent blocks of ``block_id``."""
    if visited is None:
        visited = set()
    parts: list[str] = []
    for parent in _find_parent_blocks(repo, block_id):
        if parent in visited:
            continue
        visited.add(parent)
        elem = repo.elements.get(parent)
        if elem:
            parts.extend(
                [
                    p.strip()
                    for p in elem.properties.get("partProperties", "").split(",")
                    if p.strip()
                ]
            )
        parts.extend(_collect_parent_parts(repo, parent, visited))
    seen = []
    for p in parts:
        if p not in seen:
            seen.append(p)
    return seen


def extend_block_parts_with_parents(repo: SysMLRepository, block_id: str) -> None:
    """Merge parts from generalization parents into ``block_id``."""

    block = repo.elements.get(block_id)
    if not block:
        return

    def _parent_parts() -> list[str]:
        return _collect_parent_parts(repo, block_id)

    names = [p.strip() for p in block.properties.get("partProperties", "").split(",") if p.strip()]
    for p in _parent_parts():
        if p not in names:
            names.append(p)

    joined = ", ".join(names)
    block.properties["partProperties"] = joined
    for d in repo.diagrams.values():
        for o in getattr(d, "objects", []):
            if o.get("element_id") == block_id:
                o.setdefault("properties", {})["partProperties"] = joined


def _find_blocks_with_part(repo: SysMLRepository, part_id: str) -> set[str]:
    """Return all blocks that directly include ``part_id`` as a part."""
    blocks: set[str] = set()
    for blk_id, diag_id in repo.element_diagrams.items():
        diag = repo.diagrams.get(diag_id)
        if not diag:
            continue
        for obj in getattr(diag, "objects", []):
            if obj.get("obj_type") != "Part":
                continue
            if obj.get("properties", {}).get("definition") == part_id:
                blocks.add(blk_id)
                break
    return blocks


def _find_blocks_with_aggregation(repo: SysMLRepository, part_id: str) -> set[str]:
    """Return blocks that have an aggregation relationship to ``part_id``."""
    blocks: set[str] = set()
    for rel in repo.relationships:
        if (
            rel.rel_type in ("Aggregation", "Composite Aggregation")
            and rel.target == part_id
        ):
            blocks.add(rel.source)
    return blocks


def _aggregation_exists(repo: SysMLRepository, whole_id: str, part_id: str) -> bool:
    """Return ``True`` if ``whole_id`` or its ancestors already aggregate ``part_id``."""

    src_ids = [whole_id] + _collect_generalization_parents(repo, whole_id)
    diag_id = repo.get_linked_diagram(whole_id)
    diag = repo.diagrams.get(diag_id)
    father = getattr(diag, "father", None) if diag else None
    if father:
        src_ids.append(father)
        src_ids.extend(_collect_generalization_parents(repo, father))

    for rel in repo.relationships:
        if (
            rel.rel_type in ("Aggregation", "Composite Aggregation")
            and rel.source in src_ids
            and rel.target == part_id
        ):
            return True

    for sid in src_ids[1:]:
        diag_id = repo.get_linked_diagram(sid)
        diag = repo.diagrams.get(diag_id)
        if not diag:
            continue
        for obj in getattr(diag, "objects", []):
            if (
                obj.get("obj_type") == "Part"
                and obj.get("properties", {}).get("definition") == part_id
            ):
                return True
    return False


def _reverse_aggregation_exists(
    repo: SysMLRepository, whole_id: str, part_id: str
) -> bool:
    """Return ``True`` if ``part_id`` or its ancestors aggregate ``whole_id``."""

    src_ids = [part_id] + _collect_generalization_parents(repo, part_id)
    for rel in repo.relationships:
        if (
            rel.rel_type in ("Aggregation", "Composite Aggregation")
            and rel.source in src_ids
            and rel.target == whole_id
        ):
            return True
    return False


def _parse_multiplicity_range(mult: str) -> tuple[int, int | None]:
    """Return (lower, upper) bounds parsed from *mult*."""

    mult = mult.strip()
    if not mult:
        return 1, 1
    if ".." in mult:
        low, high = mult.split("..", 1)
        low_val = int(low) if low.isdigit() else 0
        if high == "*" or not high:
            return low_val, None
        return low_val, int(high)
    if mult == "*":
        return 0, None
    if mult.isdigit():
        val = int(mult)
        return val, val
    return 1, None


def _is_default_part_name(def_name: str, part_name: str) -> bool:
    """Return ``True`` if *part_name* is derived from ``def_name``."""

    if not part_name:
        return True
    if part_name == def_name:
        return True
    pattern = re.escape(def_name) + r"\[\d+\]$"
    return re.fullmatch(pattern, part_name) is not None

def _multiplicity_limit_exceeded(
    repo: SysMLRepository,
    parent_id: str,
    def_id: str,
    diagram_objects: list,
    self_elem_id: str | None = None,
) -> bool:
    """Return ``True`` if assigning *def_id* would exceed multiplicity."""

    rels = [
        r
        for r in repo.relationships
        if r.source == parent_id
        and r.target == def_id
        and r.rel_type in ("Aggregation", "Composite Aggregation")
    ]
    if not rels:
        return False

    limit: int | None = 0
    for rel in rels:
        mult = rel.properties.get("multiplicity", "1")

        low, high = _parse_multiplicity_range(mult)
        if high is None:
            limit = None
            break
        limit += high

    if limit is None:
        return False

    # gather all diagrams containing parts for this block
    diag_ids: set[str] = set()
    linked = repo.get_linked_diagram(parent_id)
    if linked:
        diag_ids.add(linked)
    for d in repo.diagrams.values():
        if d.diag_type != "Internal Block Diagram":
            continue
        for o in getattr(d, "objects", []):
            if o.get("obj_type") == "Block Boundary" and o.get("element_id") == parent_id:
                diag_ids.add(d.diag_id)
                break

    seen: set[str] = set()
    count = 0
    for did in diag_ids:
        diag = repo.diagrams.get(did)
        if not diag:
            continue
        for o in getattr(diag, "objects", []):
            if (
                o.get("obj_type") == "Part"
                and o.get("properties", {}).get("definition") == def_id
            ):
                elem_id = o.get("element_id")
                if elem_id != self_elem_id and elem_id not in seen:
                    seen.add(elem_id)
                    count += 1

    for obj in diagram_objects:
        data = obj.__dict__ if hasattr(obj, "__dict__") else obj
        if (
            data.get("obj_type") == "Part"
            and data.get("properties", {}).get("definition") == def_id
        ):
            elem_id = data.get("element_id")
            if elem_id != self_elem_id and elem_id not in seen:
                seen.add(elem_id)
                count += 1

    return count >= limit


def _part_name_exists(
    repo: SysMLRepository,
    parent_id: str,
    name: str,
    self_elem_id: str | None = None,
) -> bool:
    """Return ``True`` if another part with ``name`` already exists."""

    if not name:
        return False

    diag_ids: set[str] = set()
    linked = repo.get_linked_diagram(parent_id)
    if linked:
        diag_ids.add(linked)
    for d in repo.diagrams.values():
        if d.diag_type != "Internal Block Diagram":
            continue
        for o in getattr(d, "objects", []):
            if o.get("obj_type") == "Block Boundary" and o.get("element_id") == parent_id:
                diag_ids.add(d.diag_id)
                break

    for did in diag_ids:
        diag = repo.diagrams.get(did)
        if not diag:
            continue
        for obj in getattr(diag, "objects", []):
            if obj.get("obj_type") != "Part":
                continue
            if obj.get("element_id") == self_elem_id:
                continue
            elem_id = obj.get("element_id")
            if elem_id in repo.elements and repo.elements[elem_id].name == name:
                return True

    return False

def _find_generalization_children(repo: SysMLRepository, parent_id: str) -> set[str]:
    """Return all blocks that generalize ``parent_id``."""
    children: set[str] = set()
    for rel in repo.relationships:
        if rel.rel_type == "Generalization" and rel.target == parent_id:
            children.add(rel.source)
    return children


def _collect_generalization_parents(
    repo: SysMLRepository, block_id: str, visited: set[str] | None = None
) -> list[str]:
    """Return all parent blocks of ``block_id`` reachable through generalizations."""

    if visited is None:
        visited = set()
    parents: list[str] = []
    for rel in repo.relationships:
        if rel.rel_type == "Generalization" and rel.source == block_id:
            target = rel.target
            if target in visited:
                continue
            visited.add(target)
            parents.append(target)
            parents.extend(_collect_generalization_parents(repo, target, visited))
    return parents


def _shared_generalization_parent(
    repo: SysMLRepository, a_id: str, b_id: str
) -> bool:
    """Return ``True`` if *a_id* and *b_id* share a common direct parent."""

    a_parents = {
        rel.target
        for rel in repo.relationships
        if rel.rel_type == "Generalization" and rel.source == a_id
    }
    if not a_parents:
        return False
    b_parents = {
        rel.target
        for rel in repo.relationships
        if rel.rel_type == "Generalization" and rel.source == b_id
    }
    return bool(a_parents & b_parents)


def rename_block(repo: SysMLRepository, block_id: str, new_name: str) -> None:
    """Rename ``block_id`` and propagate changes to related blocks."""
    if repo.element_read_only(block_id):
        return
    repo.push_undo_state()
    block = repo.elements.get(block_id)
    if not block or block.elem_type != "Block":
        return
    old_name = block.name
    new_name = repo.ensure_unique_element_name(new_name, block_id)
    if old_name == new_name:
        return
    block.name = new_name
    # update part elements referencing this block
    for elem in repo.elements.values():
        if elem.elem_type != "Part":
            continue
        def_val = elem.properties.get("definition")
        if def_val == block_id or def_val == old_name:
            elem.name = new_name
            elem.properties["definition"] = block_id
    for diag in repo.diagrams.values():
        for obj in getattr(diag, "objects", []):
            if obj.get("obj_type") != "Part":
                continue
            def_val = obj.get("properties", {}).get("definition")
            if def_val == old_name:
                obj.setdefault("properties", {})["definition"] = block_id
    # update blocks that include this block as a part
    related = _find_blocks_with_part(repo, block_id) | _find_blocks_with_aggregation(repo, block_id)
    for parent_id in related:
        parent = repo.elements.get(parent_id)
        if not parent:
            continue
        parts = [p.strip() for p in parent.properties.get("partProperties", "").split(",") if p.strip()]
        changed = False
        for idx, val in enumerate(parts):
            base = val.split("[")[0].strip()
            suffix = val[len(base):]
            if base == old_name or base == block_id:
                parts[idx] = new_name + suffix
                changed = True
        if changed:
            for child_id in _find_generalization_children(repo, parent_id):
                remove_inherited_block_properties(repo, child_id, parent_id)
            parent.properties["partProperties"] = ", ".join(parts)
            for d in repo.diagrams.values():
                for o in getattr(d, "objects", []):
                    if o.get("element_id") == parent_id:
                        o.setdefault("properties", {})["partProperties"] = parent.properties["partProperties"]
            for child_id in _find_generalization_children(repo, parent_id):
                inherit_block_properties(repo, child_id)
    # propagate property inheritance to children blocks
    for child_id in _find_generalization_children(repo, block_id):
        inherit_block_properties(repo, child_id)

    # update any Block Boundary objects referencing this block
    for diag in repo.diagrams.values():
        updated = False
        for obj in getattr(diag, "objects", []):
            if obj.get("element_id") == block_id:
                if obj.get("obj_type") == "Block Boundary" or obj.get("obj_type") == "Block":
                    obj.setdefault("properties", {})["name"] = new_name
                    updated = True
        if updated:
            repo.touch_diagram(diag.diag_id)

    # update Block objects referencing this block
    for diag in repo.diagrams.values():
        updated = False
        for obj in getattr(diag, "objects", []):
            if obj.get("obj_type") == "Block" and obj.get("element_id") == block_id:
                obj.setdefault("properties", {})["name"] = new_name
                updated = True
        if updated:
            repo.touch_diagram(diag.diag_id)


def add_aggregation_part(
    repo: SysMLRepository,
    whole_id: str,
    part_id: str,
    multiplicity: str = "",
    app=None,
) -> None:
    """Add *part_id* as a part of *whole_id* block."""
    repo.push_undo_state()
    whole = repo.elements.get(whole_id)
    part = repo.elements.get(part_id)
    if not whole or not part:
        return
    if part_id == whole_id:
        return
    if part_id in _collect_generalization_parents(repo, whole_id):
        return
    if _reverse_aggregation_exists(repo, whole_id, part_id):
        return
    name = part.name or part_id
    entry = f"{name}[{multiplicity}]" if multiplicity else name
    parts = [p.strip() for p in whole.properties.get("partProperties", "").split(",") if p.strip()]
    base = [p.split("[")[0].strip() for p in parts]
    if name in base:
        for idx, b in enumerate(base):
            if b == name:
                parts[idx] = entry
                break
    else:
        parts.append(entry)
    whole.properties["partProperties"] = ", ".join(parts)
    for d in repo.diagrams.values():
        for o in getattr(d, "objects", []):
            if o.get("element_id") == whole_id:
                o.setdefault("properties", {})["partProperties"] = ", ".join(parts)

    # ensure a Part element exists representing the aggregation
    rel = next(
        (
            r
            for r in repo.relationships
            if r.rel_type == "Aggregation"
            and r.source == whole_id
            and r.target == part_id
        ),
        None,
    )
    if not rel:
        rel = next(
            (
                r
                for r in repo.relationships
                if r.rel_type == "Composite Aggregation"
                and r.source == whole_id
                and r.target == part_id
            ),
            None,
        )
    if not rel:
        rel = repo.create_relationship("Aggregation", whole_id, part_id, record_undo=False)
    if multiplicity:
        rel.properties["multiplicity"] = multiplicity
    else:
        rel.properties.pop("multiplicity", None)
    if not rel.properties.get("part_elem"):
        part_elem = repo.create_element(
            "Part",
            name=repo.elements.get(part_id).name or part_id,
            properties={"definition": part_id},
            owner=repo.root_package.elem_id,
        )
        repo._undo_stack.pop()
        rel.properties["part_elem"] = part_elem.elem_id

    # propagate changes to any generalization children
    for child_id in _find_generalization_children(repo, whole_id):
        remove_inherited_block_properties(repo, child_id, whole_id)
        inherit_block_properties(repo, child_id)
    # ensure multiplicity instances if composite diagram exists
    add_multiplicity_parts(repo, whole_id, part_id, multiplicity, app=app)


def add_composite_aggregation_part(
    repo: SysMLRepository,
    whole_id: str,
    part_id: str,
    multiplicity: str = "",
    app=None,
) -> None:
    """Add *part_id* as a composite part of *whole_id* block and create the
    part object in the whole's Internal Block Diagram if present."""
    repo.push_undo_state()

    add_aggregation_part(repo, whole_id, part_id, multiplicity, app=app)
    diag_id = repo.get_linked_diagram(whole_id)
    diag = repo.diagrams.get(diag_id)
    # locate the relationship for future reference
    rel = next(
        (
            r
            for r in repo.relationships
            if r.rel_type == "Composite Aggregation"
            and r.source == whole_id
            and r.target == part_id
        ),
        None,
    )
    if not rel:
        rel = repo.create_relationship("Composite Aggregation", whole_id, part_id, record_undo=False)
    if multiplicity:
        rel.properties["multiplicity"] = multiplicity
    else:
        rel.properties.pop("multiplicity", None)
    if not diag or diag.diag_type != "Internal Block Diagram":
        if rel and not rel.properties.get("part_elem"):
            part_elem = repo.create_element(
                "Part",
                name=repo.elements.get(part_id).name or part_id,
                properties={"definition": part_id, "force_ibd": "true"},
                owner=repo.root_package.elem_id,
            )
            repo._undo_stack.pop()
            rel.properties["part_elem"] = part_elem.elem_id
        elif rel and rel.properties.get("part_elem"):
            pid = rel.properties["part_elem"]
            elem = repo.elements.get(pid)
            if elem:
                elem.properties["force_ibd"] = "true"
        return
    diag.objects = getattr(diag, "objects", [])
    existing_defs = {
        o.get("properties", {}).get("definition")
        for o in diag.objects
        if o.get("obj_type") == "Part"
    }
    if part_id in existing_defs:
        return
    if rel and rel.properties.get("part_elem") and rel.properties["part_elem"] in repo.elements:
        part_elem = repo.elements[rel.properties["part_elem"]]
        part_elem.properties["force_ibd"] = "true"
    else:
        part_elem = repo.create_element(
            "Part",
            name=repo.elements.get(part_id).name or part_id,
            properties={"definition": part_id, "force_ibd": "true"},
            owner=repo.root_package.elem_id,
        )
        if rel:
            rel.properties["part_elem"] = part_elem.elem_id
    repo.add_element_to_diagram(diag.diag_id, part_elem.elem_id)
    obj_dict = {
        "obj_id": _get_next_id(),
        "obj_type": "Part",
        "x": 50.0,
        "y": 50.0 + 60.0 * len(existing_defs),
        "element_id": part_elem.elem_id,
        "properties": {"definition": part_id},
        "locked": True,
        "phase": _repo_phase(repo),
    }
    diag.objects.append(obj_dict)
    _add_ports_for_part(repo, diag, obj_dict, app=app)
    if app:
        for win in getattr(app, "ibd_windows", []):
            if getattr(win, "diagram_id", None) == diag.diag_id:
                win.objects.append(SysMLObject(**obj_dict))
                win.redraw()
                win._sync_to_repository()

    # ensure additional instances per multiplicity
    add_multiplicity_parts(repo, whole_id, part_id, multiplicity, app=app)

    # propagate composite part addition to any generalization children
    for child_id in _find_generalization_children(repo, whole_id):
        inherit_block_properties(repo, child_id)


def add_multiplicity_parts(
    repo: SysMLRepository,
    whole_id: str,
    part_id: str,
    multiplicity: str,
    count: int | None = None,
    app=None,
) -> list[dict]:
    """Ensure ``count`` part instances exist according to ``multiplicity``."""

    low, high = _parse_multiplicity_range(multiplicity)

    diag_id = repo.get_linked_diagram(whole_id)
    diag = repo.diagrams.get(diag_id)
    if not diag or diag.diag_type != "Internal Block Diagram":
        return []
    diag.objects = getattr(diag, "objects", [])
    existing = [
        o
        for o in diag.objects
        if o.get("obj_type") == "Part"
        and o.get("properties", {}).get("definition") == part_id
    ]
    total = len(existing)

    desired = count if count is not None else low
    if high is not None:
        desired = min(desired, high)
    if count is not None:
        target_total = total + desired
        if high is not None:
            target_total = min(target_total, high)
    else:
        target_total = total
        if total < low:
            target_total = low
        if high is not None and target_total > high:
            target_total = high


    added: list[dict] = []
    base_name = repo.elements.get(part_id).name or part_id

    # remove extra part objects if multiplicity decreased
    if total > target_total:
        to_remove = existing[target_total:]
        remove_ids = {o["obj_id"] for o in to_remove}
        for obj in to_remove:
            diag.objects.remove(obj)
            repo.delete_element(obj.get("element_id"))
            repo._undo_stack.pop()
        diag.objects = [
            o
            for o in diag.objects
            if not (
                o.get("obj_type") == "Port"
                and o.get("properties", {}).get("parent") in {str(rid) for rid in remove_ids}
            )
        ]
        existing = existing[:target_total]
        total = target_total
        if app:
            for win in getattr(app, "ibd_windows", []):
                if getattr(win, "diagram_id", None) == diag.diag_id:
                    win.objects = [
                        o
                        for o in win.objects
                        if getattr(o, "obj_id", None) not in remove_ids
                    ]
                    win.redraw()
                    win._sync_to_repository()

    # rename remaining part elements if they still have default names
    for idx, obj in enumerate(existing):
        elem = repo.elements.get(obj.get("element_id"))
        if elem:
            expected = repo.ensure_unique_element_name(
                f"{base_name}[{idx + 1}]", elem.elem_id
            )
            if _is_default_part_name(base_name, elem.name) and elem.name != expected:
                elem.name = expected

    base_x = 50.0
    base_y = 50.0 + 60.0 * len(diag.objects)
    for i in range(total, target_total):
        part_elem = repo.create_element(
            "Part",
            name=f"{base_name}[{i + 1}]",
            properties={"definition": part_id, "force_ibd": "true"},
            owner=repo.root_package.elem_id,
        )
        repo.add_element_to_diagram(diag.diag_id, part_elem.elem_id)
        obj_dict = {
            "obj_id": _get_next_id(),
            "obj_type": "Part",
            "x": base_x,
            "y": base_y,
            "element_id": part_elem.elem_id,
            "properties": {"definition": part_id},
            "locked": True,
            "phase": _repo_phase(repo),
        }
        base_y += 60.0
        diag.objects.append(obj_dict)
        _add_ports_for_part(repo, diag, obj_dict, app=app)
        if app:
            for win in getattr(app, "ibd_windows", []):
                if getattr(win, "diagram_id", None) == diag.diag_id:
                    win.objects.append(SysMLObject(**obj_dict))
                    win.redraw()
                    win._sync_to_repository()
        added.append(obj_dict)
    # rename all part elements to ensure sequential numbering
    all_objs = [
        o
        for o in diag.objects
        if o.get("obj_type") == "Part"
        and o.get("properties", {}).get("definition") == part_id
    ]
    for idx, obj in enumerate(all_objs):
        elem = repo.elements.get(obj.get("element_id"))
        if elem:
            expected = repo.ensure_unique_element_name(
                f"{base_name}[{idx + 1}]", elem.elem_id
            )
            if _is_default_part_name(base_name, elem.name) and elem.name != expected:
                elem.name = expected

    return added


def _enforce_ibd_multiplicity(
    repo: SysMLRepository, block_id: str, app=None
) -> list[dict]:
    """Ensure ``block_id``'s IBD obeys aggregation multiplicities.

    Returns a list of added part object dictionaries."""

    added: list[dict] = []
    src_ids = [block_id] + _collect_generalization_parents(repo, block_id)
    for rel in repo.relationships:
        if (
            rel.rel_type in ("Aggregation", "Composite Aggregation")
            and rel.source in src_ids
        ):
            mult = rel.properties.get("multiplicity", "")
            if mult:
                added.extend(
                    add_multiplicity_parts(repo, block_id, rel.target, mult, app=app)
                )
    return added


def _sync_ibd_composite_parts(
    repo: SysMLRepository, block_id: str, app=None
) -> list[dict]:
    """Ensure *block_id*'s IBD includes parts for existing composite aggregations.

    Returns the list of added part object dictionaries."""

    diag_id = repo.get_linked_diagram(block_id)
    diag = repo.diagrams.get(diag_id)
    if not diag or diag.diag_type != "Internal Block Diagram":
        return []
    diag.objects = getattr(diag, "objects", [])
    existing_defs = {
        o.get("properties", {}).get("definition")
        for o in diag.objects
        if o.get("obj_type") == "Part"
    }
    src_ids = [block_id] + _collect_generalization_parents(repo, block_id)
    rels = [
        rel
        for rel in repo.relationships
        if rel.rel_type == "Composite Aggregation" and rel.source in src_ids
    ]
    added: list[dict] = []
    base_x = 50.0
    base_y = 50.0 + 60.0 * len(existing_defs)
    for rel in rels:
        pid = rel.target
        if pid in existing_defs:
            continue
        if rel.properties.get("part_elem") and rel.properties["part_elem"] in repo.elements:
            part_elem = repo.elements[rel.properties["part_elem"]]
            part_elem.properties["force_ibd"] = "true"
        else:
            part_elem = repo.create_element(
                "Part",
                name=repo.elements.get(pid).name or pid,
                properties={"definition": pid, "force_ibd": "true"},
                owner=repo.root_package.elem_id,
            )
            rel.properties["part_elem"] = part_elem.elem_id
        repo.add_element_to_diagram(diag.diag_id, part_elem.elem_id)
        obj_dict = {
            "obj_id": _get_next_id(),
            "obj_type": "Part",
            "x": base_x,
            "y": base_y,
            "element_id": part_elem.elem_id,
            "properties": {"definition": pid},
            "locked": True,
            "phase": _repo_phase(repo),
        }
        base_y += 60.0
        diag.objects.append(obj_dict)
        added.append(obj_dict)
        added += _add_ports_for_part(repo, diag, obj_dict, app=app)
        if app:
            for win in getattr(app, "ibd_windows", []):
                if getattr(win, "diagram_id", None) == diag.diag_id:
                    win.objects.append(SysMLObject(**obj_dict))
                    win.redraw()
                    win._sync_to_repository()
    return added


def _sync_ibd_aggregation_parts(
    repo: SysMLRepository, block_id: str, app=None
) -> list[dict]:
    """Ensure ``block_id``'s IBD includes parts for regular aggregations.

    Returns the list of added part object dictionaries."""

    diag_id = repo.get_linked_diagram(block_id)
    diag = repo.diagrams.get(diag_id)
    if not diag or diag.diag_type != "Internal Block Diagram":
        return []
    diag.objects = getattr(diag, "objects", [])
    existing_defs = {
        o.get("properties", {}).get("definition")
        for o in diag.objects
        if o.get("obj_type") == "Part"
    }
    src_ids = [block_id] + _collect_generalization_parents(repo, block_id)
    rels = [
        rel
        for rel in repo.relationships
        if rel.rel_type == "Aggregation" and rel.source in src_ids
    ]
    added: list[dict] = []
    base_x = 50.0
    base_y = 50.0 + 60.0 * len(existing_defs)
    for rel in rels:
        pid = rel.target
        if pid in existing_defs:
            continue
        if rel.properties.get("part_elem") and rel.properties["part_elem"] in repo.elements:
            part_elem = repo.elements[rel.properties["part_elem"]]
        else:
            part_elem = repo.create_element(
                "Part",
                name=repo.elements.get(pid).name or pid,
                properties={"definition": pid},
                owner=repo.root_package.elem_id,
            )
            rel.properties["part_elem"] = part_elem.elem_id
        repo.add_element_to_diagram(diag.diag_id, part_elem.elem_id)
        obj_dict = {
            "obj_id": _get_next_id(),
            "obj_type": "Part",
            "x": base_x,
            "y": base_y,
            "element_id": part_elem.elem_id,
            "properties": {"definition": pid},
            "phase": _repo_phase(repo),
        }
        base_y += 60.0
        diag.objects.append(obj_dict)
        added.append(obj_dict)
        added += _add_ports_for_part(repo, diag, obj_dict, app=app)
        if app:
            for win in getattr(app, "ibd_windows", []):
                if getattr(win, "diagram_id", None) == diag.diag_id:
                    win.objects.append(SysMLObject(**obj_dict))
                    win.redraw()
                    win._sync_to_repository()
    return added


def _sync_ibd_partproperty_parts(
    repo: SysMLRepository,
    block_id: str,
    names: list[str] | None = None,
    app=None,
    visible: bool = False,
    hidden: bool | None = None,
) -> list[dict]:
    """Ensure ``block_id``'s IBD includes parts for given ``names``.

    If *names* is ``None``, the block's ``partProperties`` attribute is parsed.
    Returns the list of added part object dictionaries.

    ``hidden`` is provided for backwards compatibility and overrides the
    ``visible`` flag when specified."""

    if hidden is not None:
        visible = not hidden

    diag_id = repo.get_linked_diagram(block_id)
    diag = repo.diagrams.get(diag_id)
    if not diag or diag.diag_type != "Internal Block Diagram":
        return []
    block = repo.elements.get(block_id)
    if not block:
        return []

    diag.objects = getattr(diag, "objects", [])
    existing_defs = {
        o.get("properties", {}).get("definition")
        for o in diag.objects
        if o.get("obj_type") == "Part"
    }
    existing_keys: set[str] = set()
    for o in diag.objects:
        if o.get("obj_type") == "Part" and o.get("element_id") in repo.elements:
            existing_keys.update(_part_elem_keys(repo.elements[o.get("element_id")]))
    if names is None:
        entries = [p for p in block.properties.get("partProperties", "").split(",") if p.strip()]
    else:
        entries = [n for n in names if n.strip()]
    parsed_raw = [parse_part_property(e) for e in entries]
    seen_keys = set()
    parsed = []
    for prop_name, block_name in parsed_raw:
        key = _part_prop_key(prop_name)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        parsed.append((prop_name, block_name))
    added: list[dict] = []
    boundary = next((o for o in diag.objects if o.get("obj_type") == "Block Boundary"), None)
    existing_count = sum(1 for o in diag.objects if o.get("obj_type") == "Part")
    if boundary:
        base_x = boundary["x"] - boundary["width"] / 2 + 30.0
        base_y = boundary["y"] - boundary["height"] / 2 + 30.0 + 60.0 * existing_count
    else:
        base_x = 50.0
        base_y = 50.0 + 60.0 * existing_count
    for prop_name, block_name in parsed:
        target_id = next(
            (
                eid
                for eid, elem in repo.elements.items()
                if elem.elem_type == "Block" and elem.name == block_name
            ),
            None,
        )
        if not target_id:
            continue
        base = _part_prop_key(prop_name)
        cand_key = f"{base}:{target_id}"
        if cand_key in existing_keys or base in existing_keys:
            continue
        # enforce multiplicity based on aggregation relationships
        limit = None
        for rel in repo.relationships:
            if (
                rel.source == block_id
                and rel.target == target_id
                and rel.rel_type in ("Aggregation", "Composite Aggregation")
            ):
                mult = rel.properties.get("multiplicity", "")
                low, high = _parse_multiplicity_range(mult)
                if high is not None:
                    limit = high
                break
        if limit is not None:
            current = sum(
                1
                for o in diag.objects
                if o.get("obj_type") == "Part"
                and o.get("properties", {}).get("definition") == target_id
            )
            if current >= limit:
                continue
        part_elem = repo.create_element(
            "Part",
            name=prop_name,
            properties={"definition": target_id, "force_ibd": "true"},
            owner=repo.root_package.elem_id,
        )
        repo.add_element_to_diagram(diag.diag_id, part_elem.elem_id)
        obj_dict = {
            "obj_id": _get_next_id(),
            "obj_type": "Part",
            "x": base_x,
            "y": base_y,
            "width": 80.0,
            "height": 40.0,
            "element_id": part_elem.elem_id,
            "properties": {"definition": target_id},
            "hidden": not visible,
            "phase": _repo_phase(repo),
        }
        base_y += 60.0
        diag.objects.append(obj_dict)
        added.append(obj_dict)
        existing_keys.update(_part_elem_keys(part_elem))
        existing_defs.add(target_id)
        if app:
            for win in getattr(app, "ibd_windows", []):
                if getattr(win, "diagram_id", None) == diag.diag_id:
                    win.objects.append(SysMLObject(**obj_dict))
                    win.redraw()
                    win._sync_to_repository()

    boundary = next(
        (o for o in diag.objects if o.get("obj_type") == "Block Boundary"), None
    )
    if boundary and any(not a.get("hidden", False) for a in added):
        b_obj = SysMLObject(**boundary)
        objs = [SysMLObject(**o) for o in diag.objects]
        ensure_boundary_contains_parts(b_obj, objs)
        boundary["width"] = b_obj.width
        boundary["height"] = b_obj.height
        boundary["x"] = b_obj.x
        boundary["y"] = b_obj.y
        if app:
            for win in getattr(app, "ibd_windows", []):
                if getattr(win, "diagram_id", None) == diag.diag_id:
                    for obj in win.objects:
                        if obj.obj_type == "Block Boundary":
                            obj.width = b_obj.width
                            obj.height = b_obj.height
                            obj.x = b_obj.x
                            obj.y = b_obj.y
                            win.redraw()
                            win._sync_to_repository()

    return added


def _propagate_boundary_parts(
    repo: SysMLRepository, block_id: str, parts: list[dict], app=None
) -> None:
    """Insert *parts* into diagrams containing boundaries for ``block_id``."""

    for diag in repo.diagrams.values():
        if diag.diag_type != "Internal Block Diagram":
            continue
        boundary = next(
            (
                o
                for o in getattr(diag, "objects", [])
                if o.get("obj_type") == "Block Boundary" and o.get("element_id") == block_id
            ),
            None,
        )
        if not boundary:
            continue
        diag.objects = getattr(diag, "objects", [])
        existing = {o.get("element_id") for o in diag.objects if o.get("obj_type") == "Part"}
        base_x = boundary["x"] - boundary["width"] / 2 + 30.0
        base_y = boundary["y"] - boundary["height"] / 2 + 30.0
        for obj in parts:
            if obj.get("element_id") in existing:
                continue
            new_obj = obj.copy()
            new_obj["obj_id"] = _get_next_id()
            new_obj["x"] = base_x
            new_obj["y"] = base_y
            new_obj["hidden"] = False
            new_obj["phase"] = _repo_phase(repo)
            diag.objects.append(new_obj)
            repo.add_element_to_diagram(diag.diag_id, new_obj["element_id"])
            base_y += 60.0
            if app:
                for win in getattr(app, "ibd_windows", []):
                    if getattr(win, "diagram_id", None) == diag.diag_id:
                        win.objects.append(SysMLObject(**new_obj))
                        win.redraw()
                        win._sync_to_repository()



def _sync_block_parts_from_ibd(repo: SysMLRepository, diag_id: str) -> None:
    """Ensure the block linked to ``diag_id`` lists all part definitions."""

    diag = repo.diagrams.get(diag_id)
    if not diag or diag.diag_type != "Internal Block Diagram":
        return
    block_id = (
        getattr(diag, "father", None)
        or next((eid for eid, did in repo.element_diagrams.items() if did == diag_id), None)
    )
    if not block_id or block_id not in repo.elements:
        return
    block = repo.elements[block_id]
    names = [
        p.strip()
        for p in block.properties.get("partProperties", "").split(",")
        if p.strip()
    ]
    bases = {n.split("[")[0].strip() for n in names}
    for obj in getattr(diag, "objects", []):
        if obj.get("obj_type") != "Part":
            continue
        def_id = obj.get("properties", {}).get("definition")
        if def_id and def_id in repo.elements:
            pname = repo.elements[def_id].name or def_id
            if pname not in bases:
                names.append(pname)
                bases.add(pname)
    if names:
        joined = ", ".join(names)
        block.properties["partProperties"] = joined
        for d in repo.diagrams.values():
            for o in getattr(d, "objects", []):
                if o.get("element_id") == block_id:
                    o.setdefault("properties", {})["partProperties"] = joined
        for child_id in _find_generalization_children(repo, block_id):
            inherit_block_properties(repo, child_id)


def _ensure_ibd_boundary(repo: SysMLRepository, diagram: SysMLDiagram, block_id: str, app=None) -> list[dict]:
    """Create a boundary object for the IBD father block if needed."""

    diagram.objects = getattr(diagram, "objects", [])
    boundary = next((o for o in diagram.objects if o.get("obj_type") == "Block Boundary"), None)
    added: list[dict] = []
    if not boundary:
        obj_dict = {
            "obj_id": _get_next_id(),
            "obj_type": "Block Boundary",
            "x": 100.0,
            "y": 80.0,
            "width": 200.0,
            "height": 120.0,
            "element_id": block_id,
            "properties": {"name": repo.elements.get(block_id).name or block_id},
            "phase": _repo_phase(repo),
        }
        diagram.objects.insert(0, obj_dict)
        added.append(obj_dict)
        added += _add_ports_for_boundary(repo, diagram, obj_dict, app=app)
    else:
        if boundary.get("element_id") != block_id:
            boundary["element_id"] = block_id
        added += _add_ports_for_boundary(repo, diagram, boundary, app=app)
    # propagate parts for the boundary from the block's own IBD or definition
    diag_id = repo.get_linked_diagram(block_id)
    src = repo.diagrams.get(diag_id)
    parts: list[dict] = []
    if src and src.diag_type == "Internal Block Diagram":
        parts = [o for o in getattr(src, "objects", []) if o.get("obj_type") == "Part"]
    else:
        block = repo.elements.get(block_id)
        if block:
            entries = [p for p in block.properties.get("partProperties", "").split(",") if p.strip()]
            base_x = boundary["x"] - boundary["width"] / 2 + 30.0
            base_y = boundary["y"] - boundary["height"] / 2 + 30.0
            for prop_name, blk_name in [parse_part_property(e) for e in entries]:
                target_id = next(
                    (eid for eid, elem in repo.elements.items() if elem.elem_type == "Block" and elem.name == blk_name),
                    None,
                )
                if not target_id:
                    continue
                part_elem = repo.create_element(
                    "Part",
                    name=prop_name,
                    properties={"definition": target_id, "force_ibd": "true"},
                    owner=repo.root_package.elem_id,
                )
                obj = {
                    "obj_id": _get_next_id(),
                    "obj_type": "Part",
                    "x": base_x,
                    "y": base_y,
                    "width": 80.0,
                    "height": 40.0,
                    "element_id": part_elem.elem_id,
                    "properties": {"definition": target_id},
                    "hidden": False,
                    "phase": _repo_phase(repo),
                }
                base_y += 60.0
                parts.append(obj)
    if parts:
        _propagate_boundary_parts(repo, block_id, parts, app=app)
    return added


def _remove_ibd_boundary(repo: SysMLRepository, diagram: SysMLDiagram) -> None:
    """Remove boundary object and ports from the diagram."""

    diagram.objects = getattr(diagram, "objects", [])
    boundary = next((o for o in diagram.objects if o.get("obj_type") == "Block Boundary"), None)
    if not boundary:
        return
    bid = boundary.get("obj_id")
    diagram.objects = [o for o in diagram.objects if not (o.get("obj_type") == "Port" and o.get("properties", {}).get("parent") == str(bid))]
    diagram.objects.remove(boundary)


def set_ibd_father(
    repo: SysMLRepository, diagram: SysMLDiagram, father_id: str | None, app=None
) -> list[dict]:
    """Assign *father_id* as the block represented by *diagram*.

    Links the diagram to the block and syncs composite parts. Returns any added
    part object dictionaries."""

    prev = getattr(diagram, "father", None)
    diagram.father = father_id
    if prev and prev != father_id:
        repo.link_diagram(prev, None)
    if father_id:
        repo.link_diagram(father_id, diagram.diag_id)
    added = _sync_ibd_composite_parts(repo, father_id, app=app) if father_id else []
    if father_id:
        added += _ensure_ibd_boundary(repo, diagram, father_id, app=app)
        added += _sync_ibd_partproperty_parts(repo, father_id, app=app, visible=True)
        parts = [o for o in getattr(diagram, "objects", []) if o.get("obj_type") == "Part"]
        _propagate_boundary_parts(repo, father_id, parts, app=app)
    else:
        _remove_ibd_boundary(repo, diagram)
    return added


def link_block_to_ibd(
    repo: SysMLRepository, block_id: str, diag_id: str | None, app=None
) -> list[dict]:
    """Link *block_id* to *diag_id* and ensure the IBD boundary is created."""

    if diag_id and diag_id in repo.diagrams:
        diagram = repo.diagrams[diag_id]
        if diagram.diag_type == "Internal Block Diagram":
            return set_ibd_father(repo, diagram, block_id, app=app)
    repo.link_diagram(block_id, diag_id)
    return []


def update_block_parts_from_ibd(repo: SysMLRepository, diagram: SysMLDiagram) -> None:
    """Sync the father block's ``partProperties`` from diagram part objects."""

    if diagram.diag_type != "Internal Block Diagram":
        return
    block_id = getattr(diagram, "father", None)
    if not block_id:
        block_id = next((eid for eid, did in repo.element_diagrams.items() if did == diagram.diag_id), None)
    if not block_id or block_id not in repo.elements:
        return
    block = repo.elements[block_id]
    existing = [p.strip() for p in block.properties.get("partProperties", "").split(",") if p.strip()]
    diag_entries: list[tuple[str, str]] = []
    diag_bases: set[str] = set()
    for obj in getattr(diagram, "objects", []):
        if obj.get("obj_type") != "Part":
            continue
        name = ""
        elem_id = obj.get("element_id")
        if elem_id and elem_id in repo.elements:
            elem = repo.elements[elem_id]
            name = elem.name or elem.properties.get("component", "")
        if not name:
            def_id = obj.get("properties", {}).get("definition")
            if def_id and def_id in repo.elements:
                name = repo.elements[def_id].name or def_id
        if not name:
            name = obj.get("properties", {}).get("component", "")
        base = name.split("[")[0].strip() if name else ""
        def_id = obj.get("properties", {}).get("definition")
        base_def = ""
        if def_id and def_id in repo.elements:
            base_def = (repo.elements[def_id].name or def_id).split("[")[0].strip()
        key = base_def or base
        if key and key not in diag_bases:
            diag_entries.append((key, name or key))
            diag_bases.add(key)

    merged_names = list(existing)
    bases = {n.split("[")[0].strip() for n in merged_names}
    for base, name in diag_entries:
        if base not in bases:
            merged_names.append(name)
            bases.add(base)

    if merged_names != existing:
        joined = ", ".join(merged_names)
        block.properties["partProperties"] = joined
        for d in repo.diagrams.values():
            for o in getattr(d, "objects", []):
                if o.get("element_id") == block_id:
                    o.setdefault("properties", {})["partProperties"] = joined
        for child_id in _find_generalization_children(repo, block_id):
            inherit_block_properties(repo, child_id)
        repo.touch_element(block_id)


def remove_aggregation_part(
    repo: SysMLRepository,
    whole_id: str,
    part_id: str,
    remove_object: bool = False,
    app=None,
) -> None:
    """Remove *part_id* from *whole_id* block's part list.

    If *remove_object* is True, also delete any part object representing
    *part_id* in the Internal Block Diagram linked to *whole_id*.
    """
    repo.push_undo_state()
    whole = repo.elements.get(whole_id)
    part = repo.elements.get(part_id)
    if not whole or not part:
        return
    name = part.name or part_id
    parts = [p.strip() for p in whole.properties.get("partProperties", "").split(",") if p.strip()]
    new_parts = [p for p in parts if p.split("[")[0].strip() != name]
    if len(new_parts) != len(parts):
        if new_parts:
            whole.properties["partProperties"] = ", ".join(new_parts)
        else:
            whole.properties.pop("partProperties", None)
        for d in repo.diagrams.values():
            for o in getattr(d, "objects", []):
                if o.get("element_id") == whole_id:
                    if new_parts:
                        o.setdefault("properties", {})["partProperties"] = ", ".join(new_parts)
                    else:
                        o.setdefault("properties", {}).pop("partProperties", None)

    # propagate removals to any generalization children
    for child_id in _find_generalization_children(repo, whole_id):
        child = repo.elements.get(child_id)
        if not child:
            continue
        child_parts = [
            p.strip() for p in child.properties.get("partProperties", "").split(",") if p.strip()
        ]
        child_parts = [p for p in child_parts if p.split("[")[0].strip() != name]
        if child_parts:
            child.properties["partProperties"] = ", ".join(child_parts)
        else:
            child.properties.pop("partProperties", None)
        for d in repo.diagrams.values():
            for o in getattr(d, "objects", []):
                if o.get("element_id") == child_id:
                    if child_parts:
                        o.setdefault("properties", {})["partProperties"] = ", ".join(child_parts)
                    else:
                        o.setdefault("properties", {}).pop("partProperties", None)
    if remove_object:
        diag_id = repo.get_linked_diagram(whole_id)
        diag = repo.diagrams.get(diag_id)
        if diag and diag.diag_type == "Internal Block Diagram":
            diag.objects = getattr(diag, "objects", [])
            before = len(diag.objects)
            diag.objects = [
                o
                for o in diag.objects
                if not (
                    o.get("obj_type") == "Part"
                    and o.get("properties", {}).get("definition") == part_id
                )
            ]
            if len(diag.objects) != before and app:
                for win in getattr(app, "ibd_windows", []):
                    if getattr(win, "diagram_id", None) == diag_id:
                        win.objects = [
                            o
                            for o in win.objects
                            if not (
                                o.obj_type == "Part"
                                and o.properties.get("definition") == part_id
                            )
                        ]
                        win.redraw()
                        win._sync_to_repository()
        # remove stored part element if any
        rel = next(
            (
                r
                for r in repo.relationships
                if r.rel_type in ("Composite Aggregation", "Aggregation")
                and r.source == whole_id
                and r.target == part_id
            ),
            None,
        )
        if rel:
            pid = rel.properties.pop("part_elem", None)
            if pid and pid in repo.elements:
                repo.delete_element(pid)
                repo._undo_stack.pop()


def _propagate_part_removal(
    repo: SysMLRepository,
    block_id: str,
    prop_name: str,
    target_id: str,
    remove_object: bool = False,
    app=None,
) -> None:
    """Helper used by :func:`remove_partproperty_entry` to drop a part.

    This delegates to :func:`remove_aggregation_part` which already handles
    updating descendant blocks and any diagrams linked to ``block_id`` when
    ``remove_object`` is ``True``.
    """

    remove_aggregation_part(
        repo,
        block_id,
        target_id,
        remove_object=remove_object,
        app=app,
    )


def _remove_parts_from_ibd(
    repo: SysMLRepository, block_id: str, target_id: str, app=None
) -> None:
    """Remove part objects referencing ``target_id`` from ``block_id``'s IBD."""

    diag_id = repo.get_linked_diagram(block_id)
    diag = repo.diagrams.get(diag_id)
    if not diag or diag.diag_type != "Internal Block Diagram":
        return
    diag.objects = getattr(diag, "objects", [])
    before = len(diag.objects)
    diag.objects = [
        o
        for o in diag.objects
        if not (
            o.get("obj_type") == "Part"
            and o.get("properties", {}).get("definition") == target_id
        )
    ]
    if len(diag.objects) != before and app:
        for win in getattr(app, "ibd_windows", []):
            if getattr(win, "diagram_id", None) == diag_id:
                win.objects = [
                    o
                    for o in win.objects
                    if not (
                        o.obj_type == "Part"
                        and o.properties.get("definition") == target_id
                    )
                ]
                win.redraw()
                win._sync_to_repository()


def _propagate_ibd_part_removal(
    repo: SysMLRepository, block_id: str, target_id: str, app=None
) -> None:
    """Recursively remove part objects from descendants of ``block_id``."""

    for child_id in _find_generalization_children(repo, block_id):
        _remove_parts_from_ibd(repo, child_id, target_id, app=app)
        _propagate_ibd_part_removal(repo, child_id, target_id, app=app)


def remove_partproperty_entry(
    repo: SysMLRepository, block_id: str, entry: str, app=None
) -> None:
    """Remove a part property entry and update descendant diagrams."""
    repo.push_undo_state()

    block = repo.elements.get(block_id)
    if not block:
        return
    prop_name, blk_name = parse_part_property(entry)
    target_id = next(
        (
            eid
            for eid, elem in repo.elements.items()
            if elem.elem_type == "Block" and elem.name == blk_name
        ),
        None,
    )
    if not target_id:
        return

    parts = [p.strip() for p in block.properties.get("partProperties", "").split(",") if p.strip()]
    parts = [p for p in parts if _part_prop_key(p) != _part_prop_key(entry)]
    if parts:
        block.properties["partProperties"] = ", ".join(parts)
    else:
        block.properties.pop("partProperties", None)
    for d in repo.diagrams.values():
        for o in getattr(d, "objects", []):
            if o.get("element_id") == block_id:
                if parts:
                    o.setdefault("properties", {})["partProperties"] = ", ".join(parts)
                else:
                    o.setdefault("properties", {}).pop("partProperties", None)

    _propagate_part_removal(
        repo,
        block_id,
        prop_name,
        target_id,
        remove_object=True,
        app=app,
    )
    _remove_parts_from_ibd(repo, block_id, target_id, app=app)
    _propagate_ibd_part_removal(repo, block_id, target_id, app=app)


def inherit_block_properties(repo: SysMLRepository, block_id: str) -> None:
    """Merge parent block properties into the given block."""
    extend_block_parts_with_parents(repo, block_id)
    block = repo.elements.get(block_id)
    if not block:
        return
    for parent_id in _find_parent_blocks(repo, block_id):
        parent = repo.elements.get(parent_id)
        if not parent:
            continue
        for prop in SYSML_PROPERTIES.get("BlockUsage", []):
            if prop == "partProperties":
                continue
            if prop == "operations":
                child_ops = parse_operations(block.properties.get(prop, ""))
                child_names = {o.name for o in child_ops}
                for op in parse_operations(parent.properties.get(prop, "")):
                    if op.name not in child_names:
                        child_ops.append(op)
                        child_names.add(op.name)
                block.properties[prop] = operations_to_json(child_ops)
            else:
                child_vals = [
                    v.strip() for v in block.properties.get(prop, "").split(",") if v.strip()
                ]
                parent_vals = [
                    v.strip() for v in parent.properties.get(prop, "").split(",") if v.strip()
                ]
                for v in parent_vals:
                    if v not in child_vals:
                        child_vals.append(v)
                if child_vals:
                    block.properties[prop] = ", ".join(child_vals)
    for d in repo.diagrams.values():
        for o in getattr(d, "objects", []):
            if o.get("element_id") == block_id:
                o.setdefault("properties", {}).update(block.properties)


def remove_inherited_block_properties(repo: SysMLRepository, child_id: str, parent_id: str) -> None:
    """Remove properties of *parent_id* from *child_id* block."""
    child = repo.elements.get(child_id)
    parent = repo.elements.get(parent_id)
    if not child or not parent:
        return

    # handle partProperties separately
    child_parts = [
        v.strip() for v in child.properties.get("partProperties", "").split(",") if v.strip()
    ]
    parent_parts = [
        v.strip() for v in parent.properties.get("partProperties", "").split(",") if v.strip()
    ]
    parent_bases = {p.split("[")[0].strip() for p in parent_parts}

    removed_parts = [
        v for v in child_parts if v.split("[")[0].strip() in parent_bases
    ]

    child_parts = [
        v for v in child_parts if v.split("[")[0].strip() not in parent_bases
    ]

    if child_parts:
        child.properties["partProperties"] = ", ".join(child_parts)
    else:
        child.properties.pop("partProperties", None)

    # remove inherited part objects from child IBDs
    for entry in removed_parts:
        _pname, blk_name = parse_part_property(entry)
        target_id = next(
            (
                eid
                for eid, elem in repo.elements.items()
                if elem.elem_type == "Block" and elem.name == blk_name
            ),
            None,
        )
        if target_id:
            _remove_parts_from_ibd(repo, child_id, target_id)
            _propagate_ibd_part_removal(repo, child_id, target_id)

    for prop in SYSML_PROPERTIES.get("BlockUsage", []):
        if prop == "partProperties":
            continue
        if prop == "operations":
            child_ops = parse_operations(child.properties.get(prop, ""))
            parent_ops = parse_operations(parent.properties.get(prop, ""))
            parent_names = {o.name for o in parent_ops}
            child_ops = [op for op in child_ops if op.name not in parent_names]
            if child_ops:
                child.properties[prop] = operations_to_json(child_ops)
            else:
                child.properties.pop(prop, None)
        else:
            child_vals = [v.strip() for v in child.properties.get(prop, "").split(",") if v.strip()]
            parent_vals = [
                v.strip() for v in parent.properties.get(prop, "").split(",") if v.strip()
            ]
            child_vals = [v for v in child_vals if v not in parent_vals]
            if child_vals:
                child.properties[prop] = ", ".join(child_vals)
            else:
                child.properties.pop(prop, None)

    # propagate changes to diagrams referencing the child block
    for d in repo.diagrams.values():
        for o in getattr(d, "objects", []):
            if o.get("element_id") == child_id:
                o.setdefault("properties", {}).update(child.properties)

    # ensure child's internal block diagram matches updated parts
    _sync_ibd_partproperty_parts(repo, child_id, hidden=False)


def inherit_father_parts(repo: SysMLRepository, diagram: SysMLDiagram) -> list[dict]:
    """Copy parts from the diagram's father block into the diagram.

    Returns a list with the inherited object dictionaries (parts and ports)."""
    father = getattr(diagram, "father", None)
    if not father:
        return []
    father_diag_id = repo.get_linked_diagram(father)
    father_diag = repo.diagrams.get(father_diag_id)
    if not father_diag:
        return []
    diagram.objects = getattr(diagram, "objects", [])
    added: list[dict] = []
    # Track existing parts by element id and canonical name to avoid duplicates
    existing = {o.get("element_id") for o in diagram.objects if o.get("obj_type") == "Part"}
    existing_keys: set[str] = set()
    for eid in existing:
        if eid in repo.elements:
            existing_keys.update(_part_elem_keys(repo.elements[eid]))

    # Map of source part obj_id -> new obj_id so ports can be updated
    part_map: dict[int, int] = {}

    # Pre-filter father diagram objects so the logic matches older releases
    father_parts = [
        o for o in getattr(father_diag, "objects", []) if o.get("obj_type") == "Part"
    ]

    # ------------------------------------------------------------------
    # Copy parts from the father diagram
    # ------------------------------------------------------------------
    for obj in father_parts:
        if obj.get("obj_type") != "Part":
            continue
        if obj.get("element_id") in existing:
            continue
        key_set: set[str] = set()
        if obj.get("element_id") in repo.elements:
            key_set = _part_elem_keys(repo.elements[obj.get("element_id")])
        if any(k in existing_keys for k in key_set):
            continue
        new_obj = obj.copy()
        new_obj["obj_id"] = _get_next_id()
        new_obj["phase"] = _repo_phase(repo)
        diagram.objects.append(new_obj)
        repo.add_element_to_diagram(diagram.diag_id, obj.get("element_id"))
        added.append(new_obj)
        part_map[obj.get("obj_id")] = new_obj["obj_id"]
        existing.add(obj.get("element_id"))
        if key_set:
            existing_keys.update(key_set)

    # ------------------------------------------------------------------
    # Copy ports belonging to the inherited parts so orientation and other
    # attributes are preserved. Only ports referencing a copied part are
    # considered.
    # ------------------------------------------------------------------
    for obj in getattr(father_diag, "objects", []):
        if obj.get("obj_type") != "Port":
            continue
        parent_id = obj.get("properties", {}).get("parent")
        if not parent_id:
            continue
        try:
            parent_id_int = int(parent_id)
        except Exception:
            continue
        new_parent = part_map.get(parent_id_int)
        if not new_parent:
            continue
        new_obj = obj.copy()
        new_obj["obj_id"] = _get_next_id()
        new_obj.setdefault("properties", {})["parent"] = str(new_parent)
        new_obj["phase"] = _repo_phase(repo)
        diagram.objects.append(new_obj)
        added.append(new_obj)
    # update child block partProperties with inherited names
    child_id = next(
        (eid for eid, did in repo.element_diagrams.items() if did == diagram.diag_id),
        None,
    )
    if child_id and father in repo.elements:
        child = repo.elements[child_id]
        father_elem = repo.elements[father]
        names = [
            p.strip() for p in child.properties.get("partProperties", "").split(",") if p.strip()
        ]
        father_names = [
            p.strip()
            for p in father_elem.properties.get("partProperties", "").split(",")
            if p.strip()
        ]
        for n in father_names:
            if n not in names:
                names.append(n)
        joined = ", ".join(names)
        child.properties["partProperties"] = joined
        for d in repo.diagrams.values():
            for o in getattr(d, "objects", []):
                if o.get("element_id") == child_id:
                    o.setdefault("properties", {})["partProperties"] = joined
        inherit_block_properties(repo, child_id)
    return added


@dataclass
class SysMLObject:
    obj_id: int
    obj_type: str
    x: float
    y: float
    element_id: str | None = None
    width: float = 80.0
    height: float = 40.0
    properties: Dict[str, str] = field(default_factory=dict)
    requirements: List[dict] = field(default_factory=list)
    locked: bool = False
    hidden: bool = False
    collapsed: Dict[str, bool] = field(default_factory=dict)
    phase: str | None = field(default_factory=lambda: SysMLRepository.get_instance().active_phase)

    # ------------------------------------------------------------
    def display_name(self) -> str:
        """Return the object's name annotated with its creation phase."""
        name = self.properties.get("name", "")
        return f"{name} ({self.phase})" if name and self.phase else name


@dataclass
class OperationParameter:
    """Representation of a SysML parameter."""

    name: str
    type: str = ""
    direction: str = "in"


@dataclass
class OperationDefinition:
    """Operation with a list of parameters and an optional return type."""

    name: str
    parameters: List[OperationParameter] = field(default_factory=list)
    return_type: str = ""


def calculate_allocated_asil(requirements: List[dict]) -> str:
    """Return highest ASIL level from the given requirement list."""
    asil = "QM"
    for req in requirements:
        level = req.get("asil") or global_requirements.get(req.get("id"), {}).get("asil", "QM")
        if ASIL_ORDER.get(level, 0) > ASIL_ORDER.get(asil, 0):
            asil = level
    return asil


def link_requirement_to_object(obj, req_id: str, diagram_id: str | None = None) -> None:
    """Link requirement *req_id* to *obj* and update global traces.

    ``obj`` may be a :class:`SysMLObject` instance or a plain dictionary
    representing a diagram object.  If ``obj`` is a Work Product the
    requirement ID is stored in its ``trace_to`` property instead of the
    ``requirements`` list.
    """

    req = global_requirements.get(req_id)
    if not req or obj is None:
        return

    # Determine identifier used for trace bookkeeping
    elem_id = getattr(obj, "element_id", None) or obj.get("element_id") if isinstance(obj, dict) else None
    trace = elem_id or diagram_id
    traces = req.setdefault("traces", [])
    if trace and trace not in traces:
        traces.append(trace)

    obj_type = getattr(obj, "obj_type", None) or obj.get("obj_type") if isinstance(obj, dict) else None

    if obj_type == "Work Product":
        # Work products use the ``trace_to`` property
        if isinstance(obj, dict):
            current = [s.strip() for s in obj.get("trace_to", "").split(",") if s.strip()]
            if req_id not in current:
                current.append(req_id)
                obj["trace_to"] = ", ".join(current)
        else:
            val = obj.properties.get("trace_to", "")
            current = [s.strip() for s in val.split(",") if s.strip()]
            if req_id not in current:
                current.append(req_id)
                obj.properties["trace_to"] = ", ".join(current)
    else:
        if isinstance(obj, dict):
            reqs = obj.setdefault("requirements", [])
            if not any(r.get("id") == req_id for r in reqs):
                reqs.append(req)
        else:
            if not any(r.get("id") == req_id for r in obj.requirements):
                obj.requirements.append(req)


def unlink_requirement_from_object(obj, req_id: str, diagram_id: str | None = None) -> None:
    """Remove requirement *req_id* from *obj* and global traces."""

    if obj is None:
        return

    elem_id = getattr(obj, "element_id", None) or obj.get("element_id") if isinstance(obj, dict) else None
    trace = elem_id or diagram_id
    req = global_requirements.get(req_id)
    if req and trace:
        traces = req.get("traces", [])
        if trace in traces:
            traces.remove(trace)

    obj_type = getattr(obj, "obj_type", None) or obj.get("obj_type") if isinstance(obj, dict) else None

    if obj_type == "Work Product":
        if isinstance(obj, dict):
            vals = [s.strip() for s in obj.get("trace_to", "").split(",") if s.strip()]
            if req_id in vals:
                vals.remove(req_id)
                if vals:
                    obj["trace_to"] = ", ".join(vals)
                else:
                    obj.pop("trace_to", None)
        else:
            vals = [s.strip() for s in obj.properties.get("trace_to", "").split(",") if s.strip()]
            if req_id in vals:
                vals.remove(req_id)
                if vals:
                    obj.properties["trace_to"] = ", ".join(vals)
                else:
                    obj.properties.pop("trace_to", None)
    else:
        if isinstance(obj, dict):
            obj["requirements"] = [r for r in obj.get("requirements", []) if r.get("id") != req_id]
        else:
            obj.requirements = [r for r in obj.requirements if r.get("id") != req_id]


# ---------------------------------------------------------------------------
def link_trace_between_objects(src_obj, dst_obj, diagram_id: str):
    """Create a ``Trace`` connection between two diagram objects.

    Both ``src_obj`` and ``dst_obj`` may be :class:`SysMLObject` instances or
    plain dictionaries representing diagram objects. The connection is stored in
    the diagram's connection list and mirrored as bidirectional ``Trace``
    relationships between the underlying elements when available.
    """

    repo = SysMLRepository.get_instance()

    src_id = getattr(src_obj, "obj_id", None) or src_obj.get("obj_id")
    dst_id = getattr(dst_obj, "obj_id", None) or dst_obj.get("obj_id")
    if src_id is None or dst_id is None:
        return None

    conn = DiagramConnection(src_id, dst_id, "Trace", arrow="both", stereotype="trace")

    diag = repo.diagrams.get(diagram_id)
    if diag is not None:
        diag.connections = getattr(diag, "connections", [])
        diag.connections.append(conn.__dict__)
        # Remove any leftover placeholder Trace objects that may exist from
        # earlier versions where traces were represented as nodes.
        diag.objects = [
            o for o in getattr(diag, "objects", []) if o.get("obj_type") != "Trace"
        ]

    src_elem = getattr(src_obj, "element_id", None) or src_obj.get("element_id")
    dst_elem = getattr(dst_obj, "element_id", None) or dst_obj.get("element_id")
    if src_elem and dst_elem:
        rel1 = repo.create_relationship("Trace", src_elem, dst_elem)
        rel2 = repo.create_relationship("Trace", dst_elem, src_elem)
        repo.add_relationship_to_diagram(diagram_id, rel1.rel_id)
        repo.add_relationship_to_diagram(diagram_id, rel2.rel_id)

    return conn


# ---------------------------------------------------------------------------
def link_requirements(src_id: str, relation: str, dst_id: str) -> None:
    """Create a requirement relationship and mirror the inverse."""

    src = global_requirements.get(src_id)
    dst = global_requirements.get(dst_id)
    if not src or not dst:
        return
    from analysis import safety_management as _sm
    toolbox = getattr(_sm, "ACTIVE_TOOLBOX", None)
    if toolbox and not toolbox.can_link_requirements(
        src.get("req_type", ""), dst.get("req_type", ""), relation
    ):
        return
    rel = {"type": relation, "id": dst_id}
    rels = src.setdefault("relations", [])
    if rel not in rels:
        rels.append(rel)
    inverse = None
    if relation == "satisfied by":
        inverse = "satisfies"
    elif relation == "derived from":
        inverse = "derives"
    if inverse:
        inv = {"type": inverse, "id": src_id}
        dlist = dst.setdefault("relations", [])
        if inv not in dlist:
            dlist.append(inv)


def unlink_requirements(src_id: str, relation: str, dst_id: str) -> None:
    """Remove a requirement relationship."""

    src = global_requirements.get(src_id)
    dst = global_requirements.get(dst_id)
    if not src or not dst:
        return
    src_rels = src.get("relations", [])
    src["relations"] = [r for r in src_rels if not (r.get("type") == relation and r.get("id") == dst_id)]
    inverse = None
    if relation == "satisfied by":
        inverse = "satisfies"
    elif relation == "derived from":
        inverse = "derives"
    if inverse:
        dst_rels = dst.get("relations", [])
        dst["relations"] = [r for r in dst_rels if not (r.get("type") == inverse and r.get("id") == src_id)]


def remove_orphan_ports(objs: List[SysMLObject]) -> None:
    """Delete ports that don't reference an existing parent part."""
    part_ids = {o.obj_id for o in objs if o.obj_type in ("Part", "Block Boundary")}
    filtered: List[SysMLObject] = []
    for o in objs:
        if o.obj_type == "Port":
            pid = o.properties.get("parent")
            if not pid or int(pid) not in part_ids:
                continue
        filtered.append(o)
    objs[:] = filtered


def rename_port(
    repo: SysMLRepository, port: SysMLObject, objs: List[SysMLObject], new_name: str
) -> None:
    """Rename *port* and update its parent's port list."""
    if port.element_id and repo.element_read_only(port.element_id):
        return
    old_name = port.properties.get("name", "")
    if old_name == new_name:
        return
    port.properties["name"] = new_name
    if port.element_id and port.element_id in repo.elements:
        repo.elements[port.element_id].name = new_name
        repo.elements[port.element_id].properties["name"] = new_name
    parent_id = port.properties.get("parent")
    if not parent_id:
        return
    try:
        pid = int(parent_id)
    except (TypeError, ValueError):
        return
    parent = next((o for o in objs if o.obj_id == pid), None)
    if not parent:
        return
    ports = [p.strip() for p in parent.properties.get("ports", "").split(",") if p.strip()]
    if old_name in ports:
        ports[ports.index(old_name)] = new_name
    elif new_name not in ports:
        ports.append(new_name)
    joined = ", ".join(ports)
    parent.properties["ports"] = joined
    if parent.element_id and parent.element_id in repo.elements:
        repo.elements[parent.element_id].properties["ports"] = joined


def remove_port(
    repo: SysMLRepository, port: SysMLObject, objs: List[SysMLObject]
) -> None:
    """Remove *port* from *objs* and update the parent's port list."""

    parent_id = port.properties.get("parent")
    if parent_id:
        try:
            pid = int(parent_id)
        except (TypeError, ValueError):
            pid = None
        if pid is not None:
            parent = next((o for o in objs if o.obj_id == pid), None)
            if parent:
                ports = [p.strip() for p in parent.properties.get("ports", "").split(",") if p.strip()]
                if port.properties.get("name") in ports:
                    ports.remove(port.properties.get("name"))
                    joined = ", ".join(ports)
                    parent.properties["ports"] = joined
                    if parent.element_id and parent.element_id in repo.elements:
                        repo.elements[parent.element_id].properties["ports"] = joined


def snap_port_to_parent_obj(port: SysMLObject, parent: SysMLObject) -> None:
    """Position *port* along the closest edge of *parent*."""
    px = port.x
    py = port.y
    left = parent.x - parent.width / 2
    right = parent.x + parent.width / 2
    top = parent.y - parent.height / 2
    bottom = parent.y + parent.height / 2
    d_left = abs(px - left)
    d_right = abs(px - right)
    d_top = abs(py - top)
    d_bottom = abs(py - bottom)
    min_d = min(d_left, d_right, d_top, d_bottom)
    if min_d == d_left:
        port.x = left
        port.y = min(max(py, top), bottom)
        port.properties["side"] = "W"
    elif min_d == d_right:
        port.x = right
        port.y = min(max(py, top), bottom)
        port.properties["side"] = "E"
    elif min_d == d_top:
        port.y = top
        port.x = min(max(px, left), right)
        port.properties["side"] = "N"
    else:
        port.y = bottom
        port.x = min(max(px, left), right)
        port.properties["side"] = "S"


def update_ports_for_part(part: SysMLObject, objs: List[SysMLObject]) -> None:
    """Snap all ports referencing *part* to its border."""
    for o in objs:
        if o.obj_type == "Port" and o.properties.get("parent") == str(part.obj_id):
            snap_port_to_parent_obj(o, part)


def update_ports_for_boundary(boundary: SysMLObject, objs: List[SysMLObject]) -> None:
    """Snap all ports referencing *boundary* to its border."""
    for o in objs:
        if o.obj_type == "Port" and o.properties.get("parent") == str(boundary.obj_id):
            snap_port_to_parent_obj(o, boundary)


def _boundary_min_size(boundary: SysMLObject, objs: List[SysMLObject]) -> tuple[float, float]:
    """Return minimum width and height for *boundary* to contain all parts."""
    parts = [
        o for o in objs if o.obj_type == "Part" and not getattr(o, "hidden", False)
    ]
    if not parts:
        return (20.0, 20.0)
    pad = 20.0
    left = min(p.x - p.width / 2 for p in parts)
    right = max(p.x + p.width / 2 for p in parts)
    top = min(p.y - p.height / 2 for p in parts)
    bottom = max(p.y + p.height / 2 for p in parts)
    return right - left + pad, bottom - top + pad


def ensure_boundary_contains_parts(boundary: SysMLObject, objs: List[SysMLObject]) -> None:
    """Expand *boundary* if any part lies outside its borders."""
    parts = [
        o for o in objs if o.obj_type == "Part" and not getattr(o, "hidden", False)
    ]
    if not parts:
        return
    min_w, min_h = _boundary_min_size(boundary, objs)
    if boundary.width < min_w:
        boundary.width = min_w
    if boundary.height < min_h:
        boundary.height = min_h
    left = min(p.x - p.width / 2 for p in parts)
    right = max(p.x + p.width / 2 for p in parts)
    top = min(p.y - p.height / 2 for p in parts)
    bottom = max(p.y + p.height / 2 for p in parts)
    boundary.x = (left + right) / 2
    boundary.y = (top + bottom) / 2


def _add_ports_for_part(
    repo: SysMLRepository,
    diag: SysMLDiagram,
    part_obj: dict,
    app=None,
) -> list[dict]:
    """Create port objects for ``part_obj`` based on its block definition."""

    part_elem = repo.elements.get(part_obj.get("element_id"))
    if not part_elem:
        return []
    block_id = part_elem.properties.get("definition")
    names: list[str] = []
    if block_id and block_id in repo.elements:
        block_elem = repo.elements[block_id]
        names.extend([
            p.strip()
            for p in block_elem.properties.get("ports", "").split(",")
            if p.strip()
        ])
    names.extend([
        p.strip() for p in part_elem.properties.get("ports", "").split(",") if p.strip()
    ])
    if not names:
        return []
    added: list[dict] = []
    parent = SysMLObject(
        part_obj.get("obj_id"),
        "Part",
        part_obj.get("x", 0.0),
        part_obj.get("y", 0.0),
        element_id=part_obj.get("element_id"),
        width=part_obj.get("width", 80.0),
        height=part_obj.get("height", 40.0),
        properties=part_obj.get("properties", {}).copy(),
        locked=part_obj.get("locked", False),
        phase=part_obj.get("phase"),
    )
    for name in names:
        port = SysMLObject(
            _get_next_id(),
            "Port",
            parent.x + parent.width / 2 + 20,
            parent.y,
            properties={
                "name": name,
                "parent": str(parent.obj_id),
                "side": "E",
                "labelX": "8",
                "labelY": "-8",
            },
            phase=_repo_phase(repo),
        )
        snap_port_to_parent_obj(port, parent)
        port_dict = asdict(port)
        diag.objects.append(port_dict)
        added.append(port_dict)
        if app:
            for win in getattr(app, "ibd_windows", []):
                if getattr(win, "diagram_id", None) == diag.diag_id:
                    win.objects.append(port)
                    win.redraw()
                    win._sync_to_repository()
    part_obj.setdefault("properties", {})["ports"] = ", ".join(names)
    part_elem.properties["ports"] = ", ".join(names)
    return added


def _add_ports_for_boundary(
    repo: SysMLRepository,
    diag: SysMLDiagram,
    boundary_obj: dict,
    app=None,
) -> list[dict]:
    """Create port objects for a boundary based on its block definition."""

    block = repo.elements.get(boundary_obj.get("element_id"))
    if not block:
        return []
    names = [p.strip() for p in block.properties.get("ports", "").split(",") if p.strip()]
    if not names:
        return []
    added: list[dict] = []
    parent = SysMLObject(
        boundary_obj.get("obj_id"),
        "Block Boundary",
        boundary_obj.get("x", 0.0),
        boundary_obj.get("y", 0.0),
        width=boundary_obj.get("width", 160.0),
        height=boundary_obj.get("height", 100.0),
        phase=boundary_obj.get("phase"),
    )
    for name in names:
        port = SysMLObject(
            _get_next_id(),
            "Port",
            parent.x + parent.width / 2 + 20,
            parent.y,
            properties={
                "name": name,
                "parent": str(parent.obj_id),
                "side": "E",
                "labelX": "8",
                "labelY": "-8",
            },
            phase=_repo_phase(repo),
        )
        snap_port_to_parent_obj(port, parent)
        port_dict = asdict(port)
        diag.objects.append(port_dict)
        added.append(port_dict)
        if app:
            for win in getattr(app, "ibd_windows", []):
                if getattr(win, "diagram_id", None) == diag.diag_id:
                    win.objects.append(port)
                    win.redraw()
                    win._sync_to_repository()
    boundary_obj.setdefault("properties", {})["ports"] = ", ".join(names)
    block.properties["ports"] = ", ".join(names)
    return added


def _sync_ports_for_part(repo: SysMLRepository, diag: SysMLDiagram, part_obj: dict) -> None:
    """Update port objects for ``part_obj`` to match its definition."""

    part_elem = repo.elements.get(part_obj.get("element_id"))
    if not part_elem:
        return
    block_id = part_elem.properties.get("definition")
    names: list[str] = []
    if block_id and block_id in repo.elements:
        block_elem = repo.elements[block_id]
        names.extend([
            p.strip()
            for p in block_elem.properties.get("ports", "").split(",")
            if p.strip()
        ])
    names.extend([
        p.strip() for p in part_elem.properties.get("ports", "").split(",") if p.strip()
    ])
    names = list(dict.fromkeys(names))
    part_obj.setdefault("properties", {})["ports"] = ", ".join(names)
    part_elem.properties["ports"] = ", ".join(names)

    existing = [
        o
        for o in list(diag.objects)
        if o.get("obj_type") == "Port" and o.get("properties", {}).get("parent") == str(part_obj.get("obj_id"))
    ]
    existing_names = {o.get("properties", {}).get("name") for o in existing}
    parent = SysMLObject(
        part_obj.get("obj_id"),
        "Part",
        part_obj.get("x", 0.0),
        part_obj.get("y", 0.0),
        width=part_obj.get("width", 80.0),
        height=part_obj.get("height", 40.0),
        phase=part_obj.get("phase"),
    )
    for name in names:
        if name in existing_names:
            continue
        port = SysMLObject(
            _get_next_id(),
            "Port",
            parent.x + parent.width / 2 + 20,
            parent.y,
            properties={
                "name": name,
                "parent": str(parent.obj_id),
                "side": "E",
                "labelX": "8",
                "labelY": "-8",
            },
            phase=_repo_phase(repo),
        )
        snap_port_to_parent_obj(port, parent)
        diag.objects.append(asdict(port))
    for obj in existing:
        if obj.get("properties", {}).get("name") not in names:
            diag.objects.remove(obj)


def _sync_ports_for_boundary(repo: SysMLRepository, diag: SysMLDiagram, boundary_obj: dict) -> None:
    """Update port objects for ``boundary_obj`` to match its block definition."""

    block_id = boundary_obj.get("element_id")
    block_elem = repo.elements.get(block_id)
    if not block_elem:
        return
    names = [p.strip() for p in block_elem.properties.get("ports", "").split(",") if p.strip()]
    boundary_obj.setdefault("properties", {})["ports"] = ", ".join(names)

    existing = [
        o
        for o in list(diag.objects)
        if o.get("obj_type") == "Port" and o.get("properties", {}).get("parent") == str(boundary_obj.get("obj_id"))
    ]
    existing_names = {o.get("properties", {}).get("name") for o in existing}
    parent = SysMLObject(
        boundary_obj.get("obj_id"),
        "Block Boundary",
        boundary_obj.get("x", 0.0),
        boundary_obj.get("y", 0.0),
        width=boundary_obj.get("width", 160.0),
        height=boundary_obj.get("height", 100.0),
        phase=boundary_obj.get("phase"),
    )
    for name in names:
        if name in existing_names:
            continue
        port = SysMLObject(
            _get_next_id(),
            "Port",
            parent.x + parent.width / 2 + 20,
            parent.y,
            properties={
                "name": name,
                "parent": str(parent.obj_id),
                "side": "E",
                "labelX": "8",
                "labelY": "-8",
            },
            phase=_repo_phase(repo),
        )
        snap_port_to_parent_obj(port, parent)
        diag.objects.append(asdict(port))
    for obj in existing:
        if obj.get("properties", {}).get("name") not in names:
            diag.objects.remove(obj)


def propagate_block_port_changes(repo: SysMLRepository, block_id: str) -> None:
    """Propagate port updates on ``block_id`` to all parts referencing it."""

    block = repo.elements.get(block_id)
    if not block or block.elem_type != "Block":
        return
    names = [p.strip() for p in block.properties.get("ports", "").split(",") if p.strip()]
    for elem in repo.elements.values():
        if elem.elem_type != "Part" or elem.properties.get("definition") != block_id:
            continue
        elem.properties["ports"] = ", ".join(names)
        for diag in repo.diagrams.values():
            if diag.diag_type != "Internal Block Diagram":
                continue
            diag.objects = getattr(diag, "objects", [])
            updated = False
            for obj in diag.objects:
                if obj.get("obj_type") == "Part" and obj.get("element_id") == elem.elem_id:
                    obj.setdefault("properties", {})["ports"] = ", ".join(names)
                    _sync_ports_for_part(repo, diag, obj)
                    updated = True
            if updated:
                repo.touch_diagram(diag.diag_id)

    # update boundaries referencing this block
    for diag in repo.diagrams.values():
        if diag.diag_type != "Internal Block Diagram":
            continue
        diag.objects = getattr(diag, "objects", [])
        updated = False
        for obj in diag.objects:
            if obj.get("obj_type") == "Block Boundary" and obj.get("element_id") == block_id:
                obj.setdefault("properties", {})["ports"] = ", ".join(names)
                _sync_ports_for_boundary(repo, diag, obj)
                updated = True
        if updated:
            repo.touch_diagram(diag.diag_id)


def propagate_block_part_changes(repo: SysMLRepository, block_id: str) -> None:
    """Propagate attribute updates on ``block_id`` to all parts referencing it."""

    block = repo.elements.get(block_id)
    if not block or block.elem_type != "Block":
        return
    props = ["operations", "partProperties", "behaviors"]
    for elem in repo.elements.values():
        if elem.elem_type != "Part" or elem.properties.get("definition") != block_id:
            continue
        elem.name = repo.ensure_unique_element_name(block.name, elem.elem_id)

        for prop in props:
            if prop in block.properties:
                elem.properties[prop] = block.properties[prop]
            else:
                elem.properties.pop(prop, None)


def _propagate_block_requirement_changes(
    repo: SysMLRepository, parent_id: str, child_id: str
) -> None:
    """Add requirements from ``parent_id`` objects to ``child_id`` objects."""

    parent_req_ids: set[str] = set()
    for diag in repo.diagrams.values():
        for obj in getattr(diag, "objects", []):
            if obj.get("element_id") != block_id:
                continue
            for req in obj.get("requirements", []):
                if req not in reqs:
                    reqs.append(req)
    return reqs


def _collect_block_requirements(repo: SysMLRepository, block_id: str) -> list[dict]:
    """Return a unique list of requirements associated with ``block_id``."""

    reqs: list[dict] = []
    seen: set[str] = set()
    for diag in repo.diagrams.values():
        for obj in getattr(diag, "objects", []):
            if obj.get("element_id") != block_id:
                continue
            for req in obj.get("requirements", []):
                rid = req.get("id")
                if rid is not None:
                    if rid in seen:
                        continue
                    seen.add(rid)
                reqs.append(req)
    return reqs


def _propagate_requirements(repo: SysMLRepository, src_reqs: list[dict], dst_id: str) -> None:
    """Merge *src_reqs* into all objects referencing *dst_id*."""
    if not src_reqs:
        return
    for diag in repo.diagrams.values():
        updated = False
        for obj in getattr(diag, "objects", []):
            if obj.get("element_id") != dst_id:
                continue
            obj.setdefault("requirements", [])
            existing = {r.get("id") for r in obj["requirements"]}
            for req in src_reqs:
                if req.get("id") not in existing:
                    obj["requirements"].append(req)
                    existing.add(req.get("id"))
                    updated = True
        if updated:
            repo.touch_diagram(diag.diag_id)


def propagate_block_changes(repo: SysMLRepository, block_id: str, visited: set[str] | None = None) -> None:
    """Propagate updates on ``block_id`` to blocks that generalize it."""

    if visited is None:
        visited = set()
    if block_id in visited:
        return
    visited.add(block_id)
    reqs = _collect_block_requirements(repo, block_id)
    for child_id in _find_generalization_children(repo, block_id):
        inherit_block_properties(repo, child_id)
        propagate_block_port_changes(repo, child_id)
        _propagate_requirements(repo, reqs, child_id)
        _sync_ibd_partproperty_parts(repo, child_id, hidden=False)
        propagate_block_changes(repo, child_id, visited)


def parse_operations(raw: str) -> List[OperationDefinition]:
    """Return a list of operations parsed from *raw* JSON or comma text."""
    if not raw:
        return []
    try:
        data = json.loads(raw)
        ops = []
        for o in data:
            params = [OperationParameter(**p) for p in o.get("parameters", [])]
            ops.append(OperationDefinition(o.get("name", ""), params, o.get("return_type", "")))
        return ops
    except Exception:
        return [OperationDefinition(n) for n in [p.strip() for p in raw.split(",") if p.strip()]]


def format_operation(op: OperationDefinition) -> str:
    """Return a readable string for an operation."""
    plist = ", ".join(f"{p.name}: {p.type}" if p.type else p.name for p in op.parameters)
    ret = f" : {op.return_type}" if op.return_type else ""
    return f"{op.name}({plist}){ret}"


def operations_to_json(ops: List[OperationDefinition]) -> str:
    return json.dumps([asdict(o) for o in ops])


@dataclass
class BehaviorAssignment:
    """Mapping of a block operation to an activity diagram."""

    operation: str
    diagram: str


def parse_behaviors(raw: str) -> List[BehaviorAssignment]:
    """Return a list of BehaviorAssignments from *raw* JSON."""
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return [BehaviorAssignment(**b) for b in data]
    except Exception:
        return []


def behaviors_to_json(behaviors: List[BehaviorAssignment]) -> str:
    return json.dumps([asdict(b) for b in behaviors])


def get_block_behavior_elements(repo: "SysMLRepository", block_id: str) -> List["SysMLElement"]:
    """Return Action, Activity and Operation elements that define behaviors of ``block_id``."""
    elements: List["SysMLElement"] = []
    block = repo.elements.get(block_id)
    if not block:
        return elements
    behaviors = parse_behaviors(block.properties.get("behaviors", ""))
    for beh in behaviors:
        # operations with matching name
        for elem in repo.elements.values():
            if elem.elem_type == "Operation" and elem.name == beh.operation:
                elements.append(elem)
        diag = repo.diagrams.get(beh.diagram)
        if not diag:
            continue
        # elements referenced in the diagram
        for obj in getattr(diag, "objects", []):
            elem_id = obj.get("element_id")
            typ = obj.get("obj_type") or obj.get("type")
            if elem_id and typ in ("Action", "Action Usage", "CallBehaviorAction", "Activity"):
                elem = repo.elements.get(elem_id)
                if elem:
                    elements.append(elem)
        for elem_id in getattr(diag, "elements", []):
            elem = repo.elements.get(elem_id)
            if elem and elem.elem_type in ("Action", "Activity"):
                elements.append(elem)
    seen: set[str] = set()
    unique = []
    for e in elements:
        if e.elem_id not in seen:
            unique.append(e)
            seen.add(e.elem_id)
    return unique


@dataclass
class DiagramConnection:
    src: int
    dst: int
    conn_type: str
    style: str = "Straight"  # Straight, Squared, Custom
    points: List[Tuple[float, float]] = field(default_factory=list)
    src_pos: Tuple[float, float] | None = None  # relative anchor (x,y)
    dst_pos: Tuple[float, float] | None = None
    name: str = ""
    arrow: str = "none"  # none, forward, backward, both
    mid_arrow: bool = False
    guard: List[str] = field(default_factory=list)
    guard_ops: List[str] = field(default_factory=list)
    element_id: str = ""
    multiplicity: str = ""
    stereotype: str = ""
    phase: str | None = field(default_factory=lambda: SysMLRepository.get_instance().active_phase)

    def __post_init__(self) -> None:
        if isinstance(self.guard, str):
            self.guard = [self.guard]
        elif self.guard is None:
            self.guard = []
        if isinstance(self.guard_ops, str):
            self.guard_ops = [self.guard_ops]
        elif self.guard_ops is None:
            self.guard_ops = []


def format_control_flow_label(
    conn: DiagramConnection, repo: "SysMLRepository", diag_type: str | None
) -> str:
    """Return the label to display for a connection.

    For control flow diagrams, guards are combined with configured logical
    operators and shown before the action or activity name.
    """
    label = conn.name or ""
    has_prefix = label.startswith("<<")
    if conn.conn_type == "Control Action" and not label and conn.element_id:
        elem = repo.elements.get(conn.element_id)
        if elem:
            label = elem.name or ""
    stereo = conn.stereotype or conn.conn_type.lower()
    special_case = (
        diag_type == "Control Flow Diagram"
        and conn.conn_type in ("Control Action", "Feedback")
        or diag_type == "Governance Diagram"
    )
    if special_case:
        base = label if has_prefix else (f"<<{stereo}>> {label}".strip() if stereo else label)
        if conn.guard:
            lines: List[str] = []
            for i, g in enumerate(conn.guard):
                if i == 0:
                    lines.append(g)
                else:
                    op = conn.guard_ops[i - 1] if i - 1 < len(conn.guard_ops) else "AND"
                    lines.append(f"{op} {g}")
            guard_text = "\n".join(lines)
            return f"[{guard_text}] / {base}" if base else f"[{guard_text}]"
        return base
    if stereo and not has_prefix:
        return f"<<{stereo}>> {label}".strip() if label else f"<<{stereo}>>"
    return label


def diagram_type_abbreviation(diag_type: str | None) -> str:
    """Return an abbreviation for a diagram type.

    The abbreviation is formed by taking the first letter of each word in the
    diagram type and uppercasing it. For example, "Control Flow Diagram" becomes
    "CFD" and "Internal Block Diagram" becomes "IBD".
    """
    if not diag_type:
        return ""
    return "".join(word[0] for word in diag_type.split()).upper()


def format_diagram_name(diagram: "SysMLDiagram | None") -> str:
    """Return the diagram name with its stereotype abbreviation appended.

    The abbreviation is added only once, even if the diagram name already
    contains it. This avoids duplicated suffixes when the caller repeatedly
    formats the same name or when a user manually includes the abbreviation in
    the diagram name.
    """
    if not diagram:
        return ""
    abbr = diagram_type_abbreviation(diagram.diag_type)
    name = diagram.name or diagram.diag_id
    if abbr and not name.endswith(f" : {abbr}"):
        name = f"{name} : {abbr}"
    return name


class SysMLDiagramWindow(tk.Frame):
    """Base frame for AutoML diagrams with zoom and pan support."""

    def __init__(
        self,
        master,
        title,
        tools,
        diagram_id: str | None = None,
        app=None,
        history=None,
        relation_tools: list[str] | None = None,
        tool_groups: dict[str, list[str]] | None = None,
        icon_size: int = 16,
    ):
        super().__init__(master)
        self.app = app
        self.diagram_history: list[str] = list(history) if history else []
        self.master.title(title) if isinstance(self.master, tk.Toplevel) else None
        if isinstance(self.master, tk.Toplevel):
            self.master.geometry("800x600")

        self.repo = SysMLRepository.get_instance()
        self.icon_size = icon_size
        if diagram_id and diagram_id in self.repo.diagrams:
            diagram = self.repo.diagrams[diagram_id]
        else:
            diagram = self.repo.create_diagram(title, name=title, diag_id=diagram_id)
        self.diagram_id = diagram.diag_id
        if isinstance(self.master, tk.Toplevel):
            self.master.protocol("WM_DELETE_WINDOW", self.on_close)

        # Load any saved objects and connections for this diagram
        self.objects: List[SysMLObject] = []
        for data in self.repo.visible_objects(diagram.diag_id):
            if "requirements" not in data:
                data["requirements"] = []
            data.setdefault("phase", _repo_phase(self.repo))
            obj = SysMLObject(**data)
            if obj.obj_type == "Part":
                asil = calculate_allocated_asil(obj.requirements)
                obj.properties.setdefault("asil", asil)
                if obj.element_id and obj.element_id in self.repo.elements:
                    self.repo.elements[obj.element_id].properties.setdefault(
                        "asil", asil
                    )
            self.objects.append(obj)
        self.sort_objects()
        self.connections: List[DiagramConnection] = [
            DiagramConnection(**data)
            for data in self.repo.visible_connections(diagram.diag_id)
        ]
        if self.objects:
            global _next_obj_id
            _next_obj_id = max(o.obj_id for o in self.objects) + 1

        self.zoom = 1.0
        self.font = tkFont.Font(family="Arial", size=int(8 * self.zoom))
        self.current_tool = None
        self.start = None
        self.selected_obj: SysMLObject | None = None
        self.selected_objs: list[SysMLObject] = []
        self.selected_conn: DiagramConnection | None = None
        self.drag_offset = (0, 0)
        self.dragging_point_index: int | None = None
        self.dragging_endpoint: str | None = None  # "src" or "dst"
        self.conn_drag_offset: tuple[float, float] | None = None
        self.dragging_conn_mid: tuple[float, float] | None = None
        self.dragging_conn_vec: tuple[float, float] | None = None
        self.resizing_obj: SysMLObject | None = None
        self.resize_edge: str | None = None
        self.select_rect_start: tuple[float, float] | None = None
        self.select_rect_id: int | None = None
        self.temp_line_end: tuple[float, float] | None = None
        self.endpoint_drag_pos: tuple[float, float] | None = None
        self.rc_dragged = False

        # Provide default drawing helper for gradient fills and shapes
        self.drawing_helper = fta_drawing_helper

        self.toolbox_container = ttk.Frame(self)
        self.toolbox_container.pack(side=tk.LEFT, fill=tk.Y)
        self.toolbox_container.pack_propagate(False)
        self.toolbox_canvas = tk.Canvas(self.toolbox_container, highlightthickness=0)
        self.toolbox_canvas.pack(side=tk.LEFT, fill=tk.Y)
        self.toolbox_scroll = ttk.Scrollbar(
            self.toolbox_container, orient=tk.VERTICAL, command=self.toolbox_canvas.yview
        )
        self.toolbox_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.toolbox_canvas.configure(yscrollcommand=self.toolbox_scroll.set)
        self.toolbox = ttk.Frame(self.toolbox_canvas)
        self._toolbox_window = self.toolbox_canvas.create_window(
            (0, 0), window=self.toolbox, anchor="nw"
        )
        self.toolbox.bind(
            "<Configure>",
            lambda e: self.toolbox_canvas.configure(
                scrollregion=self.toolbox_canvas.bbox("all")
            ),
        )
        self.toolbox_canvas.bind(
            "<Configure>",
            lambda e: self.toolbox_canvas.itemconfig(
                self._toolbox_window, width=e.width
            ),
        )

        # Prepare icon cache for toolbox buttons
        self._icons: dict[str, tk.PhotoImage] = {}
        self._icons["Back"] = create_icon("arrow", size=self.icon_size)
        self.back_btn = TranslucidButton(
            self.toolbox,
            text="Go Back",
            image=self._icons["Back"],
            compound=tk.LEFT,
            command=self.go_back,
        )
        self.back_btn.pack(fill=tk.X, padx=2, pady=2)
        self.back_btn.configure(state=tk.NORMAL if self.diagram_history else tk.DISABLED)
        for name in list(tools) + (relation_tools or []):
            self._icon_for(name)

        self.tool_buttons: dict[str, ttk.Button] = {}
        self.tools_frame = ttk.Frame(self.toolbox)
        self.tools_frame.pack(fill=tk.X, padx=2, pady=2)

        # Group element tools by category when provided
        if tool_groups:
            groups = tool_groups
        else:
            groups = {"": tools}
        self.element_frames: dict[str, ttk.Frame] = {}
        for name, group_tools in groups.items():
            if name:
                frame = _labelframe(
                    self.tools_frame,
                    text=f"{name} (elements)",
                )
            else:
                frame = ttk.Frame(self.tools_frame)
            frame.pack(fill=tk.X, padx=2, pady=2)
            self.element_frames[name] = frame
            for tool in group_tools:
                btn = TranslucidButton(
                    frame,
                    text=tool,
                    image=self._icon_for(tool),
                    compound=tk.LEFT,
                    command=lambda t=tool: self.select_tool(t),
                )
                btn.pack(fill=tk.X, padx=2, pady=2)
                self.tool_buttons[tool] = btn

        if relation_tools:
            self.rel_frame = _labelframe(
                self.toolbox,
                text="Relationships",
            )
            self.rel_frame.pack(fill=tk.X, padx=2, pady=2)
            for tool in relation_tools:
                TranslucidButton(
                    self.rel_frame,
                    text=tool,
                    image=self._icon_for(tool),
                    compound=tk.LEFT,
                    command=lambda t=tool: self.select_tool(t),
                ).pack(fill=tk.X, padx=2, pady=2)

        if getattr(self.app, "prop_view", None):
            self.prop_view = self.app.prop_view
        else:
            self.prop_frame = _labelframe(
                self.toolbox,
                text="Properties",
            )
            self.prop_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
            prop_tree_frame = ttk.Frame(self.prop_frame)
            prop_tree_frame.pack(fill=tk.BOTH, expand=True)
            self.prop_view = ttk.Treeview(
                prop_tree_frame,
                columns=("field", "value"),
                show="headings",
                height=8,
            )
            self.prop_view.heading("field", text="Field")
            self.prop_view.heading("value", text="Value")
            # --------------------------------------------------------------
            # NEVER DELETE OR TOUCH THIS:
            # Keep the field column fixed so the value column can grow to fill
            # the Properties tab width for readability.
            # --------------------------------------------------------------
            self.prop_view.column("field", width=80, anchor="w", stretch=False)
            self.prop_view.column("value", width=180, anchor="w", stretch=True)
            add_treeview_scrollbars(self.prop_view, prop_tree_frame)
            # Bind resize handlers on the treeview, its container, and the
            # toolbox so the value column always fills the tab width from the
            # moment the window appears. DO NOT REMOVE.
            self.prop_view.bind("<Configure>", self._resize_prop_columns)
            self.prop_view.bind("<Map>", self._resize_prop_columns)
            prop_tree_frame.bind("<Configure>", self._resize_prop_columns)
            self.toolbox.bind("<Configure>", self._resize_prop_columns)
            prop_tree_frame.after(0, self._resize_prop_columns)
            self.toolbox.after(0, self._resize_prop_columns)
            self.after(0, self._resize_prop_columns)
            self._resize_prop_columns()

        canvas_frame = ttk.Frame(self)
        canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(canvas_frame, bg=StyleManager.get_instance().canvas_bg)
        vbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        hbar = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vbar.grid(row=0, column=1, sticky="ns")
        hbar.grid(row=1, column=0, sticky="ew")
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)

        if ToolTip:
            self._conn_tip = ToolTip(self.canvas, "", automatic=False)
        else:  # pragma: no cover - tooltip module unavailable
            self._conn_tip = None
        self._conn_tip_obj = None

        # Keep references to gradient images used for element backgrounds
        self.gradient_cache: dict[int, tk.PhotoImage] = {}
        # Track bounding boxes for compartment toggle buttons
        self.compartment_buttons: list[tuple[int, str, tuple[float, float, float, float]]] = []

        self.canvas.bind("<Button-1>", self.on_left_press)
        self.canvas.bind("<B1-Motion>", self.on_left_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_left_release)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        self.canvas.bind("<ButtonPress-3>", self.on_rc_press)
        self.canvas.bind("<B3-Motion>", self.on_rc_drag)
        self.canvas.bind("<ButtonRelease-3>", self.on_rc_release)
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Control-MouseWheel>", self.on_ctrl_mousewheel)
        # Copy, cut, paste, undo, and redo are bound globally on the application
        # root to ensure each action fires only once. Only Delete remains here.
        self.bind("<Delete>", self.delete_selected)
        # Refresh from/sync to the repository whenever the window gains or loses focus
        self.bind("<FocusIn>", self._on_focus_in)
        self.canvas.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self.canvas.bind("<FocusOut>", self._on_focus_out)
        if isinstance(self.master, tk.Toplevel):
            self.master.bind("<FocusIn>", self._on_focus_in)
            self.master.bind("<FocusOut>", self._on_focus_out)

        self.after_idle(self._fit_toolbox)
        self.redraw()
        self.update_property_view()
        if not isinstance(self.master, tk.Toplevel):
            self.pack(fill=tk.BOTH, expand=True)

    def _on_focus_in(self, event=None):
        if self.app:
            self.app.active_arch_window = self
        self._sync_to_repository()
        self.refresh_from_repository(event)

    def _on_focus_out(self, event=None):
        self._sync_to_repository()

    def _fit_toolbox(self) -> None:
        """Resize the toolbox to the smallest width that shows all button text."""
        self.toolbox.update_idletasks()

        def max_button_width(widget: tk.Misc) -> int:
            width = 0
            for child in widget.winfo_children():
                if isinstance(child, ttk.Button):
                    width = max(width, child.winfo_reqwidth())
                else:
                    width = max(width, max_button_width(child))
            return width

        # Account for the external padding applied when packing buttons so the
        # canvas is only as wide as necessary to show them.
        button_width = max_button_width(self.toolbox) + 4
        scroll_width = self.toolbox_scroll.winfo_reqwidth()

        self.toolbox_container.configure(width=button_width + scroll_width)
        self.toolbox_canvas.configure(width=button_width)
        self.toolbox_canvas.itemconfig(self._toolbox_window, width=button_width)

        def _set_uniform_width(widget: tk.Misc) -> None:
            for child in getattr(widget, "winfo_children", lambda: [])():
                if hasattr(child, "pack_configure"):
                    try:
                        child.pack_configure(fill=tk.X, expand=True)
                    except Exception:
                        pass
                _set_uniform_width(child)

        _set_uniform_width(self.toolbox)
        set_uniform_button_width(self.toolbox)

        # Shrink the property view to match the button area so it does not force
        # the toolbox wider than needed. Allow the value column to stretch so it
        # can grow to fill the available space within the Properties tab.
        field_width = button_width // 2
        self.prop_view.column("field", width=field_width, stretch=False)
        self.prop_view.column(
            "value", width=button_width - field_width, stretch=True
        )

    def _fit_governance_toolbox(
        self, container: tk.Misc, canvas: tk.Canvas, window: int
    ) -> None:
        """Match the governance toolbox width to the primary toolbox."""
        # Ensure geometry measurements are up to date
        self.toolbox_canvas.update_idletasks()
        self.toolbox_container.update_idletasks()

        canvas_width = self.toolbox_canvas.winfo_width() or self.toolbox_canvas.winfo_reqwidth()
        container_width = (
            self.toolbox_container.winfo_width()
            or self.toolbox_container.winfo_reqwidth()
        )

        container.configure(width=container_width)
        canvas.configure(width=canvas_width)
        canvas.itemconfig(window, width=canvas_width)

    # ------------------------------------------------------------------
    # NEVER DELETE OR TOUCH THIS: required for keeping the value column
    # aligned with the Properties tab width.
    # ------------------------------------------------------------------
    def _resize_prop_columns(self, event: tk.Event | None = None) -> None:
        """Adjust property view columns so the value column fills the tab."""
        if not hasattr(self, "prop_view"):
            return

        # Base sizing on the containing frame width instead of the tree itself,
        # which may not have expanded to fill the tab yet.
        container = self.prop_view.master
        container.update_idletasks()
        tree_width = container.winfo_width()
        field_width = self.prop_view.column("field")["width"]

        # If the widget isn't sized yet (width too small) postpone the resize so
        # the value column starts at the full tab width. DO NOT REMOVE.
        if tree_width <= field_width + 1:
            self.prop_view.after(50, self._resize_prop_columns)
            return

        new_width = max(tree_width - field_width, 20)
        self.prop_view.column("value", width=new_width, stretch=True)

    def update_property_view(self) -> None:
        """Display properties and metadata for the selected object."""
        if self.app and hasattr(self.app, "show_properties"):
            self.app.show_properties(obj=self.selected_obj)
            return
        if not hasattr(self, "prop_view"):
            return
        self.prop_view.delete(*self.prop_view.get_children())
        obj = self.selected_obj
        if not obj:
            return
        self.prop_view.insert("", "end", values=("Type", obj.obj_type))
        name = obj.properties.get("name", "")
        if name:
            self.prop_view.insert("", "end", values=("Name", name))
        for k, v in obj.properties.items():
            if k == "name":
                continue
            self.prop_view.insert("", "end", values=(k, v))
        if obj.element_id:
            elem = self.repo.elements.get(obj.element_id)
            if elem:
                self.prop_view.insert("", "end", values=("Author", getattr(elem, "author", "")))
                self.prop_view.insert("", "end", values=("Created", getattr(elem, "created", "")))
                self.prop_view.insert("", "end", values=("Modified", getattr(elem, "modified", "")))
                self.prop_view.insert("", "end", values=("ModifiedBy", getattr(elem, "modified_by", "")))

    def select_tool(self, tool):
        if self.repo.diagram_read_only(self.diagram_id) and tool != "Select":
            return
        self.current_tool = tool
        self.start = None
        self.temp_line_end = None
        self.selected_obj = None
        self.selected_objs = []
        self.selected_conn = None
        self.dragging_point_index = None
        self.dragging_endpoint = None
        self.conn_drag_offset = None
        cursor = "arrow"
        if tool != "Select":
            cursor = "crosshair" if tool in _all_connection_tools() else "tcross"
        self.canvas.configure(cursor=cursor)
        self.update_property_view()

    def _icon_for(self, name: str) -> tk.PhotoImage:
        if not hasattr(self, "_icons"):
            self._icons = {}
        icon = self._icons.get(name)
        if icon is None:
            style = StyleManager.get_instance()
            shape = self._shape_for_tool(name)
            if shape == "relation":
                color = "black"
            else:
                color = style.get_color(name)
                if color == "#FFFFFF" and name.startswith("Add "):
                    base = name[4:]
                    if base.startswith("Generic "):
                        base = base[8:]
                    color = style.get_color(base)
                if color == "#FFFFFF":
                    color = "black"
            size = getattr(self, "icon_size", 16)
            if size == 16:
                icon = draw_icon(shape, color)
            else:
                icon = draw_icon(shape, color, size=size)
            self._icons[name] = icon
        return icon

    def _shape_for_tool(self, name: str) -> str:
        if name.startswith("Add "):
            name = name[4:]
            if name.startswith("Generic "):
                name = name[8:]
        name = "AI Database" if name == "Database" else name
        mapping = {
            "Select": "arrow",
            "Actor": "human",
            "Use Case": "ellipse",
            "Block": "component",
            "Part": "puzzle",
            "Port": "ring",
            "Initial": "circle",
            "Final": "circle",
            "Action": "action",
            "CallBehaviorAction": "action",
            "Decision": "diamond",
            "Merge": "diamond",
            "Fork": "bar",
            "Join": "bar",
            "ANN": "neural",
            "Data acquisition": "arrow",
            "AI Database": "cylinder",
            "System Boundary": "rect",
            "Business Unit": "department",
            "Data": "cylinder",
            "Document": "document",
            "Guideline": "compass",
            "Metric": "chart",
            "Organization": "building",
            "Policy": "scroll",
            "Principle": "scale",
            "Procedure": "document",
            "Record": "document",
            "Role": "human",
            "Standard": "ribbon",
            "Process": "gear",
            "Process Area": "gear",
            "Activity": "rect",
            "Task": "trapezoid",
            "Operation": "wrench",
            "Driving Function": "steering",
            "Software Component": "component",
            "Test Suite": "test",
            "System": "nested",
            "Plan": "document",
            "Component": "component",
            "Manufacturing Process": "hexagon",
            "Vehicle": "vehicle",
            "Fleet": "vehicle",
            "Safety Compliance": "shield_check",
            "Incident": "star",
            "Safety Issue": "triangle",
            "Field Data": "cylinder",
            "Model": "document",
            "Lifecycle Phase": "folder",
            "Work Product": "document",
            # Use more descriptive icon shapes for governance elements
            "Hazard": "hazard",
            "Risk Assessment": "clipboard",
            "Safety Goal": "shield",
            "Security Threat": "bug",
            "Report": "document",
            "Safety Case": "document",
        }
        if name in mapping:
            return mapping[name]
        relation_names = {
            "Flow",
            "Association",
            "Communication Path",
            "Generalize",
            "Include",
            "Extend",
            "Generalization",
            "Aggregation",
            "Composite Aggregation",
            "Connector",
            "Control Action",
            "Feedback",
            "Approves",
            "Audits",
            "Authorizes",
            "Constrained by",
            "Consumes",
            "Curation",
            "Delivers",
            "Executes",
            "Monitors",
            "Performs",
            "Produces",
            "Responsible for",
            "Uses",
            "Constrains",
            "Establish",
            "Implement",
            "Validate",
            "Verify",
            "Manufacture",
            "Operate",
            "Inspect",
            "Triage",
            "Improve",
        }
        relation_names.update(GOV_ELEMENT_RELATIONS)
        relation_names.update(SAFETY_AI_RELATIONS)
        if name in relation_names or any(
            k in name for k in ["Propagate", "Used", "Trace", "Satisfied", "Derived", "Re-use"]
        ):
            return "relation"
        return "rect"

        # ------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------
    def validate_connection(
        self, src: SysMLObject, dst: SysMLObject, conn_type: str
    ) -> tuple[bool, str]:
        """Return (valid, message) for a potential connection."""
        diag = self.repo.diagrams.get(self.diagram_id)
        diag_type = diag.diag_type if diag else ""

        if conn_type in _BASE_CONN_TYPES or conn_type in SAFETY_AI_RELATION_SET:
            if src == dst:
                return False, "Cannot connect an element to itself"

        # Config-driven source/target constraints
        ok, msg = _connection_rule_allows(
            diag_type, conn_type, src.obj_type, dst.obj_type
        )
        if not ok:
            return False, msg

        if diag_type == "Block Diagram":
            if conn_type == "Generalization":
                if _shared_generalization_parent(
                    self.repo, src.element_id, dst.element_id
                ):
                    return False, "Blocks already share a generalized parent"
                if dst.element_id in _collect_generalization_parents(
                    self.repo, src.element_id
                ) or src.element_id in _collect_generalization_parents(
                    self.repo, dst.element_id
                ):
                    return False, "Blocks cannot generalize each other"
            elif conn_type in ("Aggregation", "Composite Aggregation"):
                if _aggregation_exists(self.repo, src.element_id, dst.element_id):
                    return False, "Aggregation already defined for this block"
                if _reverse_aggregation_exists(self.repo, src.element_id, dst.element_id):
                    return False, "Blocks cannot aggregate each other"

        elif diag_type == "Internal Block Diagram":
            if conn_type == "Connector":
                if src.obj_type == "Block Boundary" or dst.obj_type == "Block Boundary":
                    return False, "Connectors must link Parts or Ports"
                if src.obj_type == "Port" and dst.obj_type == "Port":
                    dir_a = src.properties.get("direction", "inout").lower()
                    dir_b = dst.properties.get("direction", "inout").lower()
                    if {dir_a, dir_b} != {"in", "out"}:
                        return False, "Ports must connect one 'in' and one 'out'"
                    def flow_dir(conn: DiagramConnection, port_id: int) -> str | None:
                        if conn.arrow == "both":
                            return None
                        if port_id == conn.src:
                            if conn.arrow == "forward":
                                return "out"
                            if conn.arrow == "backward":
                                return "in"
                        elif port_id == conn.dst:
                            if conn.arrow == "forward":
                                return "in"
                            if conn.arrow == "backward":
                                return "out"
                        return None
                    new_dir_a = "out" if dir_a == "out" else "in"
                    new_dir_b = "out" if dir_b == "out" else "in"
                    connections = getattr(self, "connections", None)
                    if connections is None:
                        return False, "Inconsistent data flow on port"
                    for c in connections:
                        if c.conn_type != "Connector":
                            continue
                        if src.obj_id in (c.src, c.dst):
                            ex = flow_dir(c, src.obj_id)
                            if ex and ex != new_dir_a:
                                return False, "Inconsistent data flow on port"
                        if dst.obj_id in (c.src, c.dst):
                            ex = flow_dir(c, dst.obj_id)
                            if ex and ex != new_dir_b:
                                return False, "Inconsistent data flow on port"

        elif diag_type == "Control Flow Diagram":
            if conn_type in ("Control Action", "Feedback"):
                max_offset = (src.width + dst.width) / 2
                if abs(src.x - dst.x) > max_offset:
                    return False, "Connections must be vertical"

        elif diag_type == "Activity Diagram":
            if src.obj_type == "Final":
                return False, "Flows cannot originate from Final nodes"
            if dst.obj_type == "Initial":
                return False, "Flows cannot terminate at an Initial node"
        elif diag_type == "Governance Diagram":
            if conn_type in (
                "Propagate",
                "Propagate by Review",
                "Propagate by Approval",
            ):
                src_name = src.properties.get("name")
                dst_name = dst.properties.get("name")
                if (src_name, dst_name) not in ALLOWED_PROPAGATIONS:
                    return False, f"Propagation from {src_name} to {dst_name} is not allowed"
            elif conn_type == "Trace":
                from analysis.models import REQUIREMENT_WORK_PRODUCTS
                req_wps = set(REQUIREMENT_WORK_PRODUCTS)
                sname = src.properties.get("name")
                dname = dst.properties.get("name")
                if sname in req_wps and dname in req_wps:
                    return False, (
                        "Requirement work products must use 'Satisfied by' or 'Derived from'"
                    )
                if (
                    sname in SAFETY_ANALYSIS_WORK_PRODUCTS
                    and dname in SAFETY_ANALYSIS_WORK_PRODUCTS
                ):
                    return False, "Trace links cannot connect safety analysis work products"
            elif conn_type in SAFETY_AI_RELATION_SET:
                # Safety & AI connections rely solely on JSON-defined diagram rules.
                # The generic constraint check above already enforces allowed
                # source and target combinations, so no additional validation is
                # required here.
                pass
            elif conn_type in (
                "Used By",
                "Used after Review",
                "Used after Approval",
            ):
                special_doc_link = (
                    src.obj_type in {"Guideline", "Policy", "Principle", "Standard"}
                    and dst.obj_type == "Lifecycle Phase"
                )
                if not special_doc_link:
                    sname = src.properties.get("name")
                    dname = dst.properties.get("name")
                    if sname not in UNRESTRICTED_USAGE_SOURCES and (
                        sname, dname
                    ) not in ALLOWED_USAGE:
                        return False, (
                            "No metamodel dependency between these work products"
                        )
                    if dname not in SAFETY_ANALYSIS_WORK_PRODUCTS and (
                        sname, dname
                    ) not in ALLOWED_USAGE:
                        return False, f"{conn_type} links must target a safety analysis work product"
                    if (
                        sname in SAFETY_ANALYSIS_WORK_PRODUCTS
                        and dname in SAFETY_ANALYSIS_WORK_PRODUCTS
                    ):
                        if sname != "Mission Profile":
                            if (sname, dname) in ALLOWED_PROPAGATIONS:
                                return False, "Use a Propagate relationship between safety analysis work products"
                            if (sname, dname) not in ALLOWED_ANALYSIS_USAGE:
                                return False, "No metamodel dependency between these safety analyses"
                # Prevent multiple 'Used' relationships between the same
                # work products within the active lifecycle phase. Only one
                # of "Used By", "Used after Review" or "Used after Approval"
                # may exist for a given source/target pair.
                phase = _repo_phase(self.repo)
                used_stereos = {
                    "used by",
                    "used after review",
                    "used after approval",
                }
                for rel in self.repo.relationships:
                    if (
                        rel.source == src.element_id
                        and rel.target == dst.element_id
                        and rel.stereotype in used_stereos
                        and rel.phase == phase
                    ):
                        return False, (
                            "A 'Used' relationship between these work products "
                            "already exists in this phase",
                        )

        for node in (src, dst):
            limit = NODE_CONNECTION_LIMITS.get(node.obj_type)
            if limit is not None:
                used = self._decision_used_corners(node.obj_id)
                if len(used) >= limit:
                    return False, f"{node.obj_type} nodes support at most {limit} connections"

        return True, ""

    def _constrain_horizontal_movement(
        self, obj: SysMLObject, new_x: float
    ) -> float:
        """Return adjusted x to keep control flow connectors vertical."""
        diag = self.repo.diagrams.get(self.diagram_id)
        if not diag or diag.diag_type != "Control Flow Diagram":
            return new_x
        adjusted_x = new_x
        for conn in self.connections:
            if conn.conn_type in ("Control Action", "Feedback") and (
                conn.src == obj.obj_id or conn.dst == obj.obj_id
            ):
                other_id = conn.dst if conn.src == obj.obj_id else conn.src
                for other in self.objects:
                    if other.obj_id == other_id:
                        max_diff = (obj.width + other.width) / 2
                        diff = adjusted_x - other.x
                        if diff > max_diff:
                            adjusted_x = other.x + max_diff
                        elif diff < -max_diff:
                            adjusted_x = other.x - max_diff
        return adjusted_x

    def _constrain_control_flow_x(
        self, conn: DiagramConnection, new_x: float
    ) -> float:
        """Clamp connector x within the horizontal overlap of its objects."""
        diag = self.repo.diagrams.get(self.diagram_id)
        if not diag or diag.diag_type != "Control Flow Diagram":
            return new_x
        src = next((o for o in self.objects if o.obj_id == conn.src), None)
        dst = next((o for o in self.objects if o.obj_id == conn.dst), None)
        if not src or not dst:
            return new_x
        min_x = max(src.x - src.width / 2, dst.x - dst.width / 2)
        max_x = min(src.x + src.width / 2, dst.x + dst.width / 2)
        if new_x < min_x:
            return min_x
        if new_x > max_x:
            return max_x
        return new_x

    def on_left_press(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        if self.repo.diagram_read_only(self.diagram_id):
            conn = self.find_connection(x, y)
            if conn:
                self.selected_conn = conn
                self.selected_obj = None
                self.selected_objs = []
            else:
                obj = self.find_object(x, y, prefer_port=True)
                self.selected_conn = None
                self.selected_obj = obj
                self.selected_objs = [obj] if obj else []
            self.update_property_view()
            return
        if getattr(self, "_conn_tip", None):
            self._conn_tip.hide()
            self._conn_tip_obj = None
        conn_tools = _all_connection_tools()
        prefer = self.current_tool in conn_tools
        t = self.current_tool
        if t in (None, "Select"):
            conn = self.find_connection(x, y)
            if conn:
                if (event.state & 0x0001) and conn.style == "Custom":
                    conn.points.append((x / self.zoom, y / self.zoom))
                    self._sync_to_repository()
                self.selected_conn = conn
                self.selected_obj = None
                self.selected_objs = []
                self.dragging_point_index = None
                self.dragging_endpoint = None
                self.dragging_conn_mid = None
                self.dragging_conn_vec = None
                self.update_property_view()
                if conn.style == "Custom":
                    for idx, (px, py) in enumerate(conn.points):
                        hx = px * self.zoom
                        hy = py * self.zoom
                        if abs(hx - x) <= 4 and abs(hy - y) <= 4:
                            self.dragging_point_index = idx
                            self.conn_drag_offset = (x - hx, y - hy)
                            break
                elif conn.style == "Squared":
                    src_obj = self.get_object(conn.src)
                    dst_obj = self.get_object(conn.dst)
                    if src_obj and dst_obj:
                        mx = (
                            conn.points[0][0] * self.zoom
                            if conn.points
                            else ((src_obj.x + dst_obj.x) / 2 * self.zoom)
                        )
                        my = (src_obj.y + dst_obj.y) / 2 * self.zoom
                        if abs(mx - x) <= 4 and abs(my - y) <= 4:
                            self.dragging_point_index = 0
                            self.conn_drag_offset = (x - mx, 0)
                elif (
                    self.repo.diagrams.get(self.diagram_id).diag_type
                    == "Control Flow Diagram"
                    and conn.conn_type in ("Control Action", "Feedback")
                ):
                    src_obj = self.get_object(conn.src)
                    dst_obj = self.get_object(conn.dst)
                    if src_obj and dst_obj:
                        x_val = (
                            conn.points[0][0]
                            if conn.points
                            else (
                                max(
                                    src_obj.x - src_obj.width / 2,
                                    dst_obj.x - dst_obj.width / 2,
                                )
                                + min(
                                    src_obj.x + src_obj.width / 2,
                                    dst_obj.x + dst_obj.width / 2,
                                )
                            )
                            / 2
                        )
                        x_val = SysMLDiagramWindow._constrain_control_flow_x(
                            self, conn, x_val
                        )
                        mx = x_val * self.zoom
                        my = (src_obj.y + dst_obj.y) / 2 * self.zoom
                        if abs(mx - x) <= 4 and abs(my - y) <= 4:
                            self.dragging_point_index = 0
                            self.conn_drag_offset = (x - mx, 0)
                elif (
                    self.repo.diagrams.get(self.diagram_id).diag_type
                    == "Governance Diagram"
                    and conn.style == "Straight"
                ):
                    src_obj = self.get_object(conn.src)
                    dst_obj = self.get_object(conn.dst)
                    if src_obj and dst_obj:
                        sx, sy = self.edge_point(
                            src_obj,
                            dst_obj.x * self.zoom,
                            dst_obj.y * self.zoom,
                            conn.src_pos,
                        )
                        ex, ey = self.edge_point(
                            dst_obj,
                            src_obj.x * self.zoom,
                            src_obj.y * self.zoom,
                            conn.dst_pos,
                        )
                        mx = (sx + ex) / 2
                        my = (sy + ey) / 2
                        if abs(mx - x) <= 4 and abs(my - y) <= 4:
                            self.dragging_conn_mid = (mx, my)
                            self.conn_drag_offset = (x - mx, y - my)
                            self.dragging_conn_vec = (ex - sx, ey - sy)
                # check for dragging endpoints
                src_obj = self.get_object(conn.src)
                dst_obj = self.get_object(conn.dst)
                if src_obj and dst_obj:
                    sx, sy = self.edge_point(
                        src_obj,
                        dst_obj.x * self.zoom,
                        dst_obj.y * self.zoom,
                        conn.src_pos,
                    )
                    dxp, dyp = self.edge_point(
                        dst_obj,
                        src_obj.x * self.zoom,
                        src_obj.y * self.zoom,
                        conn.dst_pos,
                    )
                    if abs(sx - x) <= 6 and abs(sy - y) <= 6:
                        self.dragging_endpoint = "src"
                        self.conn_drag_offset = (x - sx, y - sy)
                        self.endpoint_drag_pos = None
                    elif abs(dxp - x) <= 6 and abs(dyp - y) <= 6:
                        self.dragging_endpoint = "dst"
                        self.conn_drag_offset = (x - dxp, y - dyp)
                        self.endpoint_drag_pos = None
                self.redraw()
                return

        obj = self.find_object(x, y, prefer_port=prefer)

        if obj and obj.obj_type == "Block" and t in (None, "Select"):
            hit = self.hit_compartment_toggle(obj, x, y)
            if hit:
                obj.collapsed[hit] = not obj.collapsed.get(hit, False)
                self._resize_block_to_content(obj)
                self._sync_to_repository()
                self.redraw()
                return

        if t in _all_connection_tools():
            if self.start is None:
                if obj:
                    self.start = obj
                    # Do not highlight objects while adding a connection
                    self.selected_obj = None
                    self.update_property_view()
                    self.temp_line_end = (x, y)
                    self.redraw()
            else:
                if obj and obj != self.start:
                    valid, msg = self.validate_connection(self.start, obj, t)
                    if valid:
                        if t == "Control Action":
                            arrow_default = "forward"
                        elif t == "Feedback":
                            arrow_default = "backward"
                        elif t == "Trace":
                            arrow_default = "both"
                        elif t in (
                            "Flow",
                            "Generalize",
                            "Generalization",
                            "Include",
                            "Extend",
                            "Propagate",
                            "Propagate by Review",
                            "Propagate by Approval",
                            "Used By",
                            "Used after Review",
                            "Used after Approval",
                            "Re-use",
                            "Satisfied by",
                            "Derived from",
                        ):
                            arrow_default = "forward"
                        else:
                            arrow_default = "none"
                        conn_stereo = (
                            "control action"
                            if t == "Control Action"
                            else "feedback" if t == "Feedback" else t.lower()
                        )
                        conn = DiagramConnection(
                            self.start.obj_id,
                            obj.obj_id,
                            t,
                            arrow=arrow_default,
                            stereotype=conn_stereo,
                        )
                        ok = True
                        if self.start.obj_type in ("Decision", "Merge"):
                            pref = self._nearest_diamond_corner(
                                self.start, obj.x * self.zoom, obj.y * self.zoom
                            )
                            w = self.start.width * self.zoom / 2
                            h = self.start.height * self.zoom / 2
                            cx = self.start.x * self.zoom
                            cy = self.start.y * self.zoom
                            rel = ((pref[0] - cx) / w, (pref[1] - cy) / h)
                            ok = self._assign_decision_corner(
                                conn, self.start, "src_pos", rel
                            )
                        if ok and obj.obj_type in ("Decision", "Merge"):
                            pref = self._nearest_diamond_corner(
                                obj, self.start.x * self.zoom, self.start.y * self.zoom
                            )
                            w = obj.width * self.zoom / 2
                            h = obj.height * self.zoom / 2
                            cx = obj.x * self.zoom
                            cy = obj.y * self.zoom
                            rel = ((pref[0] - cx) / w, (pref[1] - cy) / h)
                            ok = self._assign_decision_corner(conn, obj, "dst_pos", rel)
                        if ok:
                            self.connections.append(conn)
                        else:
                            messagebox.showwarning(
                                "Invalid Connection",
                                "Decision nodes support at most 4 connections",
                            )
                            conn = None
                        src_id = self.start.element_id
                        dst_id = obj.element_id
                        if conn and src_id and dst_id:
                            rel_stereo = (
                                "control action"
                                if t == "Control Action"
                                else "feedback" if t == "Feedback" else None
                            )
                            if t == "Trace":
                                rel1 = self.repo.create_relationship(
                                    t, src_id, dst_id, stereotype=rel_stereo
                                )
                                rel2 = self.repo.create_relationship(
                                    t, dst_id, src_id, stereotype=rel_stereo
                                )
                                self.repo.add_relationship_to_diagram(
                                    self.diagram_id, rel1.rel_id
                                )
                                self.repo.add_relationship_to_diagram(
                                    self.diagram_id, rel2.rel_id
                                )
                            else:
                                rel = self.repo.create_relationship(
                                    t, src_id, dst_id, stereotype=rel_stereo
                                )
                                self.repo.add_relationship_to_diagram(
                                    self.diagram_id, rel.rel_id
                                )
                                if t == "Generalization":
                                    inherit_block_properties(self.repo, src_id)
                        if conn:
                            self._sync_to_repository()
                            ConnectionDialog(self, conn)
                    else:
                        messagebox.showwarning("Invalid Connection", msg)
                self.start = None
                self.temp_line_end = None
                self.selected_obj = None
                self.update_property_view()
                # Return to select mode after completing a connection
                self.current_tool = "Select"
                self.canvas.configure(cursor="arrow")
                self.redraw()
        elif t and t != "Select":
            if t == "Existing Element":
                names = []
                id_map = {}
                diag = self.repo.diagrams.get(self.diagram_id)
                allowed = {"Actor", "Block"} if diag and diag.diag_type == "Control Flow Diagram" else None
                toolbox = getattr(getattr(self, "app", None), "safety_mgmt_toolbox", None)
                allowed_sources = (
                    toolbox.analysis_inputs(diag.diag_type)
                    if toolbox and diag
                    else None
                )
                for eid, el in self.repo.elements.items():
                    if el.elem_type != "Package" and (not allowed or el.elem_type in allowed):
                        if allowed_sources is not None:
                            src_id = self.repo.element_diagrams.get(eid)
                            src_diag = self.repo.diagrams.get(src_id) if src_id else None
                            if not src_diag or src_diag.diag_type not in allowed_sources:
                                continue
                            if not toolbox.document_visible(src_diag.diag_type, src_diag.name):
                                continue
                        name = el.name or eid
                        names.append(name)
                        id_map[name] = eid
                if not names:
                    messagebox.showinfo("Add Element", "No elements available")
                    return
                dlg = SysMLObjectDialog.SelectElementDialog(self, names, title="Select Element")
                selected = dlg.result
                if not selected:
                    return
                elem_id = id_map[selected]
                element = self.repo.elements.get(elem_id)
                self.repo.add_element_to_diagram(self.diagram_id, elem_id)
                new_obj = SysMLObject(
                    _get_next_id(),
                    "Existing Element",
                    x / self.zoom,
                    y / self.zoom,
                    element_id=elem_id,
                    properties={"name": element.name if element else selected},
                    phase=_repo_phase(self.repo),
                )
            else:
                if t == "Port":
                    parent_obj = (
                        obj if obj and obj.obj_type in ("Part", "Block Boundary") else None
                    )
                    if parent_obj is None:
                        # Default to the IBD boundary if present
                        parent_obj = next(
                            (o for o in self.objects if o.obj_type == "Block Boundary"),
                            None,
                        )
                    if parent_obj is None:
                        return
                pkg = self.repo.diagrams[self.diagram_id].package
                element = self.repo.create_element(t, owner=pkg)
                self.repo.add_element_to_diagram(self.diagram_id, element.elem_id)
                new_obj = SysMLObject(
                    _get_next_id(),
                    t,
                    x / self.zoom,
                    y / self.zoom,
                    element_id=element.elem_id,
                    phase=_repo_phase(self.repo),
                )
            if t == "Block":
                new_obj.height = 140.0
                new_obj.width = 160.0
            elif t == "System Boundary":
                new_obj.width = 200.0
                new_obj.height = 120.0
            elif t in ("Decision", "Merge"):
                new_obj.width = 40.0
                new_obj.height = 40.0
            elif t == "Initial":
                new_obj.width = 20.0
                new_obj.height = 20.0
            elif t == "Final":
                new_obj.width = 30.0
                new_obj.height = 30.0
            elif t in ("Fork", "Join"):
                new_obj.width = 60.0
                new_obj.height = 10.0
            elif t == "AI Database":
                new_obj.width = 80.0
                new_obj.height = 60.0
                new_obj.properties.setdefault("name", "AI Database")
            elif t == "ANN":
                new_obj.width = 120.0
                new_obj.height = 80.0
                new_obj.properties.setdefault("name", "ANN")
            elif t == "Data acquisition":
                new_obj.width = 120.0
                new_obj.height = 80.0
                new_obj.properties.setdefault(
                    "compartments", "data source1;data source2;data source 3"
                )
                new_obj.properties.setdefault("name", "Data acquisition")
            key = f"{t.replace(' ', '')}Usage"

            for prop in SYSML_PROPERTIES.get(key, []):
                new_obj.properties.setdefault(prop, "")
            if t == "Port":
                new_obj.properties.setdefault("labelX", "8")
                new_obj.properties.setdefault("labelY", "-8")
                if parent_obj:
                    new_obj.properties["parent"] = str(parent_obj.obj_id)
                    self.snap_port_to_parent(new_obj, parent_obj)
                    # Persist the port by adding it to the parent object's list
                    pname = new_obj.properties.get("name") or ""
                    ports = [
                        p.strip()
                        for p in parent_obj.properties.get("ports", "").split(",")
                        if p.strip()
                    ]
                    if not pname:
                        base = "Port"
                        idx = 1
                        existing = set(ports)
                        existing.update(
                            p.properties.get("name")
                            for p in self.objects
                            if p.obj_type == "Port"
                            and p.properties.get("parent") == str(parent_obj.obj_id)
                        )
                        pname = base
                        while pname in existing:
                            pname = f"{base}{idx}"
                            idx += 1
                        new_obj.properties["name"] = pname
                        element.name = pname
                    if pname not in ports:
                        ports.append(pname)
                        parent_obj.properties["ports"] = ", ".join(ports)
                        if parent_obj.element_id and parent_obj.element_id in self.repo.elements:
                            self.repo.elements[parent_obj.element_id].properties["ports"] = (
                                parent_obj.properties["ports"]
                            )
            element.properties.update(new_obj.properties)
            self.ensure_text_fits(new_obj)
            if t == "System Boundary":
                self.objects.insert(0, new_obj)
            else:
                self.objects.append(new_obj)
            self.sort_objects()
            self._sync_to_repository()
            self.selected_obj = new_obj
            # After placing one object, revert to select mode so additional
            # clicks do not keep adding elements unintentionally
            self.current_tool = "Select"
            self.canvas.configure(cursor="arrow")
            self.redraw()
            self.update_property_view()
        else:
            if obj:
                self.selected_obj = obj
                self.selected_objs = [obj]
                self.drag_offset = (x / self.zoom - obj.x, y / self.zoom - obj.y)
                self.resizing_obj = None
                self.resize_edge = self.hit_resize_handle(obj, x, y)
                if self.resize_edge:
                    self.resizing_obj = obj
                self.redraw()
                self.update_property_view()
            else:
                conn = self.find_connection(x, y)
                if conn:
                    if (event.state & 0x0001) and conn.style == "Custom":
                        conn.points.append((x / self.zoom, y / self.zoom))
                        self._sync_to_repository()
                    self.selected_conn = conn
                    self.selected_obj = None
                    self.selected_objs = []
                    self.dragging_point_index = None
                    self.dragging_endpoint = None
                    self.update_property_view()
                    if conn.style == "Custom":
                        for idx, (px, py) in enumerate(conn.points):
                            hx = px * self.zoom
                            hy = py * self.zoom
                            if abs(hx - x) <= 4 and abs(hy - y) <= 4:
                                self.dragging_point_index = idx
                                self.conn_drag_offset = (x - hx, y - hy)
                                break
                    elif conn.style == "Squared":
                        src_obj = self.get_object(conn.src)
                        dst_obj = self.get_object(conn.dst)
                        if src_obj and dst_obj:
                            mx = (
                                conn.points[0][0] * self.zoom
                                if conn.points
                                else ((src_obj.x + dst_obj.x) / 2 * self.zoom)
                            )
                            my = (src_obj.y + dst_obj.y) / 2 * self.zoom
                            if abs(mx - x) <= 4 and abs(my - y) <= 4:
                                self.dragging_point_index = 0
                                self.conn_drag_offset = (x - mx, 0)
                    # check for dragging endpoints
                    src_obj = self.get_object(conn.src)
                    dst_obj = self.get_object(conn.dst)
                    if src_obj and dst_obj:
                        sx, sy = self.edge_point(
                            src_obj,
                            dst_obj.x * self.zoom,
                            dst_obj.y * self.zoom,
                            conn.src_pos,
                        )
                        dxp, dyp = self.edge_point(
                            dst_obj,
                            src_obj.x * self.zoom,
                            src_obj.y * self.zoom,
                            conn.dst_pos,
                        )
                        if abs(sx - x) <= 6 and abs(sy - y) <= 6:
                            self.dragging_endpoint = "src"
                            self.conn_drag_offset = (x - sx, y - sy)
                            self.endpoint_drag_pos = None
                        elif abs(dxp - x) <= 6 and abs(dyp - y) <= 6:
                            self.dragging_endpoint = "dst"
                            self.conn_drag_offset = (x - dxp, y - dyp)
                            self.endpoint_drag_pos = None
                    self.redraw()
                else:
                    # allow clicking on the resize handle even if outside the object
                    if self.selected_obj:
                        self.resize_edge = self.hit_resize_handle(self.selected_obj, x, y)
                        if self.resize_edge:
                            self.resizing_obj = self.selected_obj
                            return
                    self.selected_obj = None
                    self.selected_objs = []
                    self.selected_conn = None
                    self.resizing_obj = None
                    self.resize_edge = None
                    if self.current_tool == "Select":
                        self.select_rect_start = (x, y)
                        self.select_rect_id = self.canvas.create_rectangle(
                            x, y, x, y, dash=(2, 2), outline="blue"
                        )
                    self.redraw()
                    self.update_property_view()

    def on_left_drag(self, event):
        if self.repo.diagram_read_only(self.diagram_id):
            return
        if getattr(self, "_conn_tip", None):
            self._conn_tip.hide()
            self._conn_tip_obj = None
        if self.start and self.current_tool in _all_connection_tools():
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            self.temp_line_end = (x, y)
            self.redraw()
            return
        if self.select_rect_start:
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            self.canvas.coords(
                self.select_rect_id,
                self.select_rect_start[0],
                self.select_rect_start[1],
                x,
                y,
            )
            self._update_drag_selection(x, y)
            return
        if (
            getattr(self, "dragging_conn_mid", None)
            and self.selected_conn
            and self.current_tool == "Select"
        ):
            x = self.canvas.canvasx(event.x) - self.conn_drag_offset[0]
            y = self.canvas.canvasy(event.y) - self.conn_drag_offset[1]
            src_obj = self.get_object(self.selected_conn.src)
            dst_obj = self.get_object(self.selected_conn.dst)
            vec = getattr(self, "dragging_conn_vec", None)
            if src_obj and dst_obj and vec:
                dx, dy = vec
                sx, sy = self._line_rect_intersection(x, y, -dx, -dy, src_obj)
                ex, ey = self._line_rect_intersection(x, y, dx, dy, dst_obj)
                rx = (sx / self.zoom - src_obj.x) / (src_obj.width / 2)
                ry = (sy / self.zoom - src_obj.y) / (src_obj.height / 2)
                if src_obj.obj_type in ("Decision", "Merge"):
                    if not self._assign_decision_corner(
                        self.selected_conn, src_obj, "src_pos", (rx, ry)
                    ):
                        pass
                else:
                    self.selected_conn.src_pos = (rx, ry)
                rx = (ex / self.zoom - dst_obj.x) / (dst_obj.width / 2)
                ry = (ey / self.zoom - dst_obj.y) / (dst_obj.height / 2)
                if dst_obj.obj_type in ("Decision", "Merge"):
                    if not self._assign_decision_corner(
                        self.selected_conn, dst_obj, "dst_pos", (rx, ry)
                    ):
                        pass
                else:
                    self.selected_conn.dst_pos = (rx, ry)
            self.redraw()
            return
        if (
            self.dragging_endpoint is not None
            and self.selected_conn
            and self.current_tool == "Select"
        ):
            x = self.canvas.canvasx(event.x) - self.conn_drag_offset[0]
            y = self.canvas.canvasy(event.y) - self.conn_drag_offset[1]
            if self.dragging_endpoint == "src":
                obj = self.get_object(self.selected_conn.src)
            else:
                obj = self.get_object(self.selected_conn.dst)
            if obj:
                cx = obj.x * self.zoom
                cy = obj.y * self.zoom
                w = obj.width * self.zoom / 2
                h = obj.height * self.zoom / 2
                thresh = max(w, h) + CONNECTION_SELECT_RADIUS
                if math.hypot(x - cx, y - cy) <= thresh:
                    self.endpoint_drag_pos = None
                    ex, ey = self.edge_point(obj, x, y, apply_radius=False)
                    rx = (ex / self.zoom - obj.x) / (obj.width / 2)
                    ry = (ey / self.zoom - obj.y) / (obj.height / 2)
                    if self.dragging_endpoint == "src":
                        if obj.obj_type in ("Decision", "Merge"):
                            if not self._assign_decision_corner(
                                self.selected_conn, obj, "src_pos", (rx, ry)
                            ):
                                pass
                        else:
                            self.selected_conn.src_pos = (rx, ry)
                    else:
                        if obj.obj_type in ("Decision", "Merge"):
                            if not self._assign_decision_corner(
                                self.selected_conn, obj, "dst_pos", (rx, ry)
                            ):
                                pass
                        else:
                            self.selected_conn.dst_pos = (rx, ry)
                else:
                    self.endpoint_drag_pos = (x, y)
            self.redraw()
            return
        if (
            self.dragging_point_index is not None
            and self.selected_conn
            and self.current_tool == "Select"
        ):
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            px = (x - self.conn_drag_offset[0]) / self.zoom
            py = (y - self.conn_drag_offset[1]) / self.zoom
            if self.selected_conn.style == "Squared":
                if not self.selected_conn.points:
                    self.selected_conn.points.append((px, 0))
                else:
                    self.selected_conn.points[0] = (px, 0)
            elif (
                self.repo.diagrams.get(self.diagram_id).diag_type
                == "Control Flow Diagram"
                and self.selected_conn.conn_type in ("Control Action", "Feedback")
            ):
                px = SysMLDiagramWindow._constrain_control_flow_x(
                    self, self.selected_conn, px
                )
                if not self.selected_conn.points:
                    self.selected_conn.points.append((px, 0))
                else:
                    self.selected_conn.points[0] = (px, 0)
            else:
                self.selected_conn.points[self.dragging_point_index] = (px, py)
            self.redraw()
            return
        if not self.selected_obj:
            return
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        if self.resizing_obj:
            obj = self.resizing_obj
            if obj.obj_type in _FIXED_SIZE_TYPES:
                return
            min_w, min_h = (10.0, 10.0)
            child_left = child_right = child_top = child_bottom = None
            if obj.obj_type == "Block":
                min_w, min_h = self._min_block_size(obj)
            elif obj.obj_type in ("Action", "CallBehaviorAction"):
                min_w, min_h = self._min_action_size(obj)
            elif obj.obj_type == "Data acquisition":
                min_w, min_h = self._min_data_acquisition_size(obj)
            elif obj.obj_type == "Block Boundary":
                min_w, min_h = _boundary_min_size(obj, self.objects)
            elif obj.obj_type == "System Boundary":
                wps = [
                    o
                    for o in self.objects
                    if o.obj_type == "Work Product"
                    and o.properties.get("parent") == str(obj.obj_id)
                ]
                if wps:
                    child_left = min(w.x - w.width / 2 for w in wps)
                    child_right = max(w.x + w.width / 2 for w in wps)
                    child_top = min(w.y - w.height / 2 for w in wps)
                    child_bottom = max(w.y + w.height / 2 for w in wps)
                    min_w = max(min_w, child_right - child_left)
                    min_h = max(min_h, child_bottom - child_top)
                if getattr(self, "font", None):
                    label_lines = self._object_label_lines(obj)
                    if label_lines:
                        text_w = max(self.font.measure(line) for line in label_lines)
                        text_h = self.font.metrics("linespace") * len(label_lines)
                        min_w = max(min_w, (text_w + 10 * self.zoom) / self.zoom)
                        min_h = max(min_h, (text_h + 10 * self.zoom) / self.zoom)
            left = obj.x - obj.width / 2
            right = obj.x + obj.width / 2
            top = obj.y - obj.height / 2
            bottom = obj.y + obj.height / 2
            if "e" in self.resize_edge:
                new_right = x / self.zoom
                if child_right is not None and new_right < child_right:
                    new_right = child_right
                if new_right - left < min_w:
                    new_right = left + min_w
                right = new_right
            if "w" in self.resize_edge:
                new_left = x / self.zoom
                if child_left is not None and new_left > child_left:
                    new_left = child_left
                if right - new_left < min_w:
                    new_left = right - min_w
                left = new_left
            if obj.obj_type not in ("Fork", "Join", "Existing Element"):
                if "s" in self.resize_edge:
                    new_bottom = y / self.zoom
                    if child_bottom is not None and new_bottom < child_bottom:
                        new_bottom = child_bottom
                    if new_bottom - top < min_h:
                        new_bottom = top + min_h
                    bottom = new_bottom
                if "n" in self.resize_edge:
                    new_top = y / self.zoom
                    if child_top is not None and new_top > child_top:
                        new_top = child_top
                    if bottom - new_top < min_h:
                        new_top = bottom - min_h
                    top = new_top
            new_w = right - left
            new_h = bottom - top
            obj.x = (left + right) / 2
            obj.y = (top + bottom) / 2
            obj.width = new_w
            obj.height = new_h
            if obj.obj_type == "Part":
                update_ports_for_part(obj, self.objects)
            if obj.obj_type == "Block Boundary":
                update_ports_for_boundary(obj, self.objects)
                ensure_boundary_contains_parts(obj, self.objects)
            self.redraw()
            return
        if self.selected_obj.obj_type == "Port" and "parent" in self.selected_obj.properties:
            parent = self.get_object(int(self.selected_obj.properties["parent"]))
            if parent:
                self.selected_obj.x = x / self.zoom
                self.selected_obj.y = y / self.zoom
                self.snap_port_to_parent(self.selected_obj, parent)
        else:
            old_x = self.selected_obj.x
            old_y = self.selected_obj.y
            new_x = x / self.zoom - self.drag_offset[0]
            new_x = self._constrain_horizontal_movement(self.selected_obj, new_x)
            self.selected_obj.x = new_x
            self.selected_obj.y = y / self.zoom - self.drag_offset[1]
            if self.selected_obj.obj_type == "Work Product":
                self._constrain_to_parent(self.selected_obj)
            dx = self.selected_obj.x - old_x
            dy = self.selected_obj.y - old_y
            if self.selected_obj.obj_type in ("Part", "Block Boundary"):
                for p in self.objects:
                    if p.obj_type == "Port" and p.properties.get("parent") == str(
                        self.selected_obj.obj_id
                    ):
                        p.x += dx
                        p.y += dy
                        self.snap_port_to_parent(p, self.selected_obj)
            if self.selected_obj.obj_type == "Block Boundary":
                for o in self.objects:
                    if o.obj_type == "Part":
                        o.x += dx
                        o.y += dy
                        for p in self.objects:
                            if (
                                p.obj_type == "Port"
                                and p.properties.get("parent") == str(o.obj_id)
                            ):
                                p.x += dx
                                p.y += dy
            if self.selected_obj.obj_type == "System Boundary":
                for o in self.objects:
                    if (
                        o.obj_type == "Work Product"
                        and o.properties.get("parent") == str(self.selected_obj.obj_id)
                    ):
                        offx = float(o.properties.get("px", o.x - old_x))
                        offy = float(o.properties.get("py", o.y - old_y))
                        o.x = self.selected_obj.x + offx
                        o.y = self.selected_obj.y + offy
                        self._constrain_to_parent(o, self.selected_obj)
                    elif o.properties.get("boundary") == str(self.selected_obj.obj_id):
                        o.x += dx
                        o.y += dy
            boundary = self.get_ibd_boundary()
            if boundary:
                ensure_boundary_contains_parts(boundary, self.objects)
        self.redraw()
        self._sync_to_repository()
        if self.app:
            self.app.update_views()

    def _connection_targets(self, source: SysMLObject, conn_type: str) -> list[str]:
        """Return valid target object types for a connection."""
        diag = self.repo.diagrams.get(self.diagram_id)
        diag_type = diag.diag_type if diag else ""
        conn_rules = CONNECTION_RULES.get(diag_type, {})
        src_type = source.obj_type
        if diag_type == "Governance Diagram" and conn_type != "Flow":
            src_type = _GOV_TYPE_ALIASES.get(src_type, src_type)
        targets = conn_rules.get(conn_type, {}).get(src_type, set())
        return sorted(t for t in targets if t != "Port")

    def _create_element_at(self, obj_type: str, x: float, y: float) -> SysMLObject:
        """Create a new element and diagram object at ``(x, y)``."""
        pkg = self.repo.diagrams[self.diagram_id].package
        element = self.repo.create_element(obj_type, owner=pkg)
        self.repo.add_element_to_diagram(self.diagram_id, element.elem_id)
        new_obj = SysMLObject(
            _get_next_id(),
            obj_type,
            x / self.zoom,
            y / self.zoom,
            element_id=element.elem_id,
            phase=_repo_phase(self.repo),
        )
        if obj_type == "Block":
            new_obj.height = 140.0
            new_obj.width = 160.0
        elif obj_type == "System Boundary":
            new_obj.width = 200.0
            new_obj.height = 120.0
        elif obj_type in ("Decision", "Merge"):
            new_obj.width = new_obj.height = 40.0
        elif obj_type == "Initial":
            new_obj.width = new_obj.height = 20.0
        elif obj_type == "Final":
            new_obj.width = new_obj.height = 30.0
        elif obj_type in ("Fork", "Join"):
            new_obj.width = 60.0
            new_obj.height = 10.0
        self.objects.append(new_obj)
        self.sort_objects()
        self._sync_to_repository()
        self.redraw()
        return new_obj

    def _connect_objects(self, src: SysMLObject, dst: SysMLObject, conn_type: str) -> None:
        """Connect two objects and create repository relationship."""
        if self.repo.diagram_read_only(self.diagram_id):
            return
        valid, msg = self.validate_connection(src, dst, conn_type)
        if not valid:
            messagebox.showwarning("Invalid Connection", msg)
            return
        if conn_type == "Control Action":
            arrow_default = "forward"
        elif conn_type == "Feedback":
            arrow_default = "backward"
        elif conn_type == "Trace":
            arrow_default = "both"
        elif conn_type in _arrow_forward_types():
            arrow_default = "forward"
        else:
            arrow_default = "none"
        conn_stereo = (
            "control action"
            if conn_type == "Control Action"
            else "feedback" if conn_type == "Feedback" else conn_type.lower()
        )
        conn = DiagramConnection(src.obj_id, dst.obj_id, conn_type, arrow=arrow_default, stereotype=conn_stereo)
        if conn_type == "Connector":
            src_flow = src.properties.get("flow") if src.obj_type == "Port" else None
            dst_flow = dst.properties.get("flow") if dst.obj_type == "Port" else None
            if src_flow or dst_flow:
                conn.mid_arrow = True
                if src_flow and dst_flow:
                    dir_a = src.properties.get("direction", "out").lower()
                    dir_b = dst.properties.get("direction", "out").lower()
                    if dir_a == "out":
                        conn.name = src_flow
                        conn.arrow = "forward"
                    elif dir_b == "out":
                        conn.name = dst_flow
                        conn.arrow = "backward"
                    else:
                        conn.name = src_flow
                        conn.arrow = "both"
                elif src_flow:
                    conn.name = src_flow
                    dir_attr = src.properties.get("direction", "out")
                    if dir_attr == "in":
                        conn.arrow = "backward"
                    elif dir_attr == "out":
                        conn.arrow = "forward"
                    else:
                        conn.arrow = "both"
                else:
                    conn.name = dst_flow
                    dir_attr = dst.properties.get("direction", "out")
                    if dir_attr == "in":
                        conn.arrow = "forward"
                    elif dir_attr == "out":
                        conn.arrow = "backward"
                    else:
                        conn.arrow = "both"
        self._assign_decision_corners(conn)
        self.connections.append(conn)
        if src.element_id and dst.element_id:
            rel_stereo = (
                "control action"
                if conn_type == "Control Action"
                else "feedback" if conn_type == "Feedback" else None
            )
            if conn_type == "Trace":
                rel1 = self.repo.create_relationship(conn_type, src.element_id, dst.element_id, stereotype=rel_stereo)
                rel2 = self.repo.create_relationship(conn_type, dst.element_id, src.element_id, stereotype=rel_stereo)
                self.repo.add_relationship_to_diagram(self.diagram_id, rel1.rel_id)
                self.repo.add_relationship_to_diagram(self.diagram_id, rel2.rel_id)
            else:
                rel = self.repo.create_relationship(conn_type, src.element_id, dst.element_id, stereotype=rel_stereo)
                self.repo.add_relationship_to_diagram(self.diagram_id, rel.rel_id)
                if conn_type == "Generalization":
                    inherit_block_properties(self.repo, src.element_id)
        self._sync_to_repository()
        ConnectionDialog(self, conn)
        self.redraw()

    def _create_obj_and_conn(
        self, source: SysMLObject, x: float, y: float, conn_type: str, obj_type: str
    ) -> None:
        """Create an object of ``obj_type`` at ``(x, y)`` and connect it to ``source``."""
        if self.repo.diagram_read_only(self.diagram_id):
            return
        if (
            obj_type == "Document"
            and source.obj_type == "Work Product"
            and conn_type in _WORK_PRODUCT_CONN_TYPES
        ):
            name = simpledialog.askstring("Add Work Product", "Enter work product name:")
            if not name:
                return
            name = name.strip()
            if not name:
                return
            existing = {wp.lower() for wp in getattr(self.app, "WORK_PRODUCT_INFO", {})}
            if name.lower() in existing:
                messagebox.showerror(
                    "Duplicate Work Product",
                    f"'{name}' is already a defined work product.",
                )
                return
            new_obj = self._place_work_product(
                name, x / self.zoom, y / self.zoom, lock_name=False
            )
        else:
            new_obj = self._create_element_at(obj_type, x, y)
        if new_obj:
            self._connect_objects(source, new_obj, conn_type)

    def on_left_release(self, event):
        if self.repo.diagram_read_only(self.diagram_id):
            return
        if getattr(self, "_conn_tip", None):
            self._conn_tip.hide()
            self._conn_tip_obj = None
        if self.start and self.current_tool in _all_connection_tools():
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            obj = self.find_object(x, y, prefer_port=True)
            source = self.start
            conn_type = self.current_tool
            # Reset to select mode regardless of outcome
            self.start = None
            self.temp_line_end = None
            self.current_tool = "Select"
            self.canvas.configure(cursor="arrow")
            self.redraw()
            if obj and obj != source:
                self._connect_objects(source, obj, conn_type)
            else:
                targets = self._connection_targets(source, conn_type)
                if targets:
                    menu = tk.Menu(self, tearoff=0)
                    for t in targets:
                        menu.add_command(
                            label=t,
                            command=lambda tt=t: self._create_obj_and_conn(
                                source, x, y, conn_type, tt
                            ),
                        )
                    try:
                        menu.tk_popup(event.x_root, event.y_root)
                    finally:
                        menu.grab_release()
            return
        if self.select_rect_start:
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            self.canvas.coords(
                self.select_rect_id,
                self.select_rect_start[0],
                self.select_rect_start[1],
                x,
                y,
            )
            self._update_drag_selection(x, y)
            self.canvas.delete(self.select_rect_id)
            self.select_rect_start = None
            self.select_rect_id = None
        self.start = None
        self.temp_line_end = None
        # Return to select mode after completing a connection
        self.current_tool = "Select"
        self.canvas.configure(cursor="arrow")
        self.resizing_obj = None
        self.resize_edge = None
        if self.dragging_point_index is not None and self.selected_conn:
            self._sync_to_repository()
        self.dragging_point_index = None
        if getattr(self, "dragging_conn_mid", None) and self.selected_conn:
            self._sync_to_repository()
        self.dragging_conn_mid = None
        self.dragging_conn_vec = None
        if self.dragging_endpoint is not None and self.selected_conn:
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            obj = self.find_object(x, y, prefer_port=True)
            src_obj = self.get_object(self.selected_conn.src)
            dst_obj = self.get_object(self.selected_conn.dst)
            if obj and obj not in (src_obj, dst_obj):
                if self.dragging_endpoint == "src":
                    valid, msg = self.validate_connection(
                        obj, dst_obj, self.selected_conn.conn_type
                    )
                else:
                    valid, msg = self.validate_connection(
                        src_obj, obj, self.selected_conn.conn_type
                    )
                if valid and src_obj and dst_obj and obj.element_id:
                    for rel in self.repo.relationships:
                        if (
                            rel.source == src_obj.element_id
                            and rel.target == dst_obj.element_id
                            and rel.rel_type == self.selected_conn.conn_type
                        ):
                            if self.selected_conn.conn_type == "Generalization":
                                if self.dragging_endpoint == "dst":
                                    msgbox = "Changing inheritance will remove all inherited parts, properties and attributes. Continue?"
                                    if not messagebox.askyesno("Change Inheritance", msgbox):
                                        break
                                    remove_inherited_block_properties(
                                        self.repo, src_obj.element_id, dst_obj.element_id
                                    )
                                    rel.target = obj.element_id
                                    self.selected_conn.dst = obj.obj_id
                                    inherit_block_properties(self.repo, src_obj.element_id)
                                else:
                                    msgbox = "Changing inheritance will remove all inherited parts, properties and attributes. Continue?"
                                    if not messagebox.askyesno("Change Inheritance", msgbox):
                                        break
                                    remove_inherited_block_properties(
                                        self.repo, src_obj.element_id, dst_obj.element_id
                                    )
                                    rel.source = obj.element_id
                                    self.selected_conn.src = obj.obj_id
                                    inherit_block_properties(self.repo, obj.element_id)
                            else:
                                if self.selected_conn.conn_type in (
                                    "Aggregation",
                                    "Composite Aggregation",
                                ):
                                    msg = "Delete aggregation and its part?"
                                    if messagebox.askyesno(
                                        "Remove Aggregation", msg
                                    ):
                                        remove_aggregation_part(
                                            self.repo,
                                            src_obj.element_id,
                                            dst_obj.element_id,
                                            remove_object=self.selected_conn.conn_type
                                            == "Composite Aggregation",
                                            app=getattr(self, "app", None),
                                        )
                                if self.dragging_endpoint == "dst":
                                    rel.target = obj.element_id
                                    self.selected_conn.dst = obj.obj_id
                                    new_whole = src_obj.element_id
                                    new_part = obj.element_id
                                else:
                                    rel.source = obj.element_id
                                    self.selected_conn.src = obj.obj_id
                                    new_whole = obj.element_id
                                    new_part = dst_obj.element_id
                                if self.selected_conn.conn_type == "Composite Aggregation":
                                    add_composite_aggregation_part(
                                        self.repo,
                                        new_whole,
                                        new_part,
                                        self.selected_conn.multiplicity,
                                        app=getattr(self, "app", None),
                                    )
                                elif self.selected_conn.conn_type == "Aggregation":
                                    add_aggregation_part(
                                        self.repo,
                                        new_whole,
                                        new_part,
                                        self.selected_conn.multiplicity,
                                        app=getattr(self, "app", None),
                                    )
                                else:
                                    if self.dragging_endpoint == "dst":
                                        rel.target = obj.element_id
                                        self.selected_conn.dst = obj.obj_id
                                    else:
                                        rel.source = obj.element_id
                                        self.selected_conn.src = obj.obj_id
                            break
                    self._assign_decision_corners(self.selected_conn)
                    self._sync_to_repository()
                elif not valid:
                    messagebox.showwarning("Invalid Connection", msg)
            elif obj is None:
                if self.selected_conn in self.connections:
                    self.connections.remove(self.selected_conn)
                    if (
                        src_obj
                        and dst_obj
                        and src_obj.element_id
                        and dst_obj.element_id
                    ):
                        for rel in list(self.repo.relationships):
                            if (
                                rel.source == src_obj.element_id
                                and rel.target == dst_obj.element_id
                                and rel.rel_type == self.selected_conn.conn_type
                            ):
                                self.repo.relationships.remove(rel)
                                diag = self.repo.diagrams.get(self.diagram_id)
                                if diag and rel.rel_id in diag.relationships:
                                    diag.relationships.remove(rel.rel_id)
                                if self.selected_conn.conn_type == "Generalization":
                                    remove_inherited_block_properties(
                                        self.repo,
                                        src_obj.element_id,
                                        dst_obj.element_id,
                                    )
                                    inherit_block_properties(
                                        self.repo, src_obj.element_id
                                    )
                                elif self.selected_conn.conn_type in (
                                    "Aggregation",
                                    "Composite Aggregation",
                                ):
                                    remove_aggregation_part(
                                        self.repo,
                                        src_obj.element_id,
                                        dst_obj.element_id,
                                        remove_object=self.selected_conn.conn_type
                                        == "Composite Aggregation",
                                        app=getattr(self, "app", None),
                                    )
                                break
                    self.selected_conn = None
                    self._sync_to_repository()
            else:
                self._sync_to_repository()
            self.dragging_endpoint = None
            self.conn_drag_offset = None
            self.endpoint_drag_pos = None
        else:
            self.dragging_endpoint = None
            self.conn_drag_offset = None
            self.endpoint_drag_pos = None
        if self.selected_obj and self.current_tool == "Select":
            if self.selected_obj.obj_type not in ("System Boundary", "Work Product"):
                b = self.find_boundary_for_obj(self.selected_obj)
                if b:
                    self.selected_obj.properties["boundary"] = str(b.obj_id)
                else:
                    self.selected_obj.properties.pop("boundary", None)
            elif self.selected_obj.obj_type == "Work Product":
                b = self.find_boundary_for_obj(self.selected_obj)
                if b:
                    self.selected_obj.properties["boundary"] = str(b.obj_id)
                else:
                    self.selected_obj.properties.pop("boundary", None)
            self._sync_to_repository()
        self.redraw()

    def on_mouse_move(self, event):
        if self.start and self.current_tool in (
            "Association",
            "Include",
            "Extend",
            "Flow",
            "Propagate",
            "Propagate by Review",
            "Propagate by Approval",
            "Used By",
            "Used after Review",
            "Used after Approval",
            "Re-use",
            "Trace",
            "Connector",
            "Generalization",
            "Generalize",
            "Communication Path",
            "Aggregation",
            "Composite Aggregation",
            "Control Action",
            "Feedback",
        ):
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            self.temp_line_end = (x, y)
            self.redraw()

    def on_mouse_move(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        if self.start and self.current_tool in (
            "Association",
            "Include",
            "Extend",
            "Flow",
            "Propagate",
            "Propagate by Review",
            "Propagate by Approval",
            "Used By",
            "Used after Review",
            "Used after Approval",
            "Re-use",
            "Trace",
            "Connector",
            "Generalization",
            "Generalize",
            "Communication Path",
            "Aggregation",
            "Composite Aggregation",
            "Control Action",
            "Feedback",
        ):
            self.temp_line_end = (x, y)
            self.redraw()
            return
        if getattr(self, "_conn_tip", None):
            diag = self.repo.diagrams.get(self.diagram_id)
            obj = self.find_object(x, y)
            if (
                diag
                and diag.diag_type == "Governance Diagram"
                and obj
                and obj is not self._conn_tip_obj
            ):
                text = _gov_connection_text(obj.obj_type)
                if text:
                    self._conn_tip.text = text
                    x_root = getattr(event, "x_root", event.x)
                    y_root = getattr(event, "y_root", event.y)
                    self._conn_tip.show(x_root, y_root)
                    self._conn_tip_obj = obj
                else:
                    self._conn_tip.hide()
                    self._conn_tip_obj = None
            elif not obj and self._conn_tip_obj is not None:
                self._conn_tip.hide()
                self._conn_tip_obj = None

    def on_double_click(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        conn = self.find_connection(x, y)
        obj = None
        if conn is None:
            obj = self.find_object(x, y)
        if conn:
            ConnectionDialog(self, conn)
            self.redraw()
        elif obj:
            if self._open_linked_diagram(obj):
                return
            # Persist current diagram state before opening the dialog so that
            # focus changes triggered by the dialog do not clear unsaved
            # objects from the repository. After the dialog closes, sync again
            # to store any edits made by the user.
            self._sync_to_repository()
            SysMLObjectDialog(self, obj)
            self._sync_to_repository()
            self.redraw()
            if getattr(self, "app", None):
                self.app.update_views()

    def on_rc_press(self, event):
        self.rc_dragged = False
        self.canvas.scan_mark(event.x, event.y)

    def on_rc_drag(self, event):
        self.rc_dragged = True
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def on_rc_release(self, event):
        if not self.rc_dragged:
            x = self.canvas.canvasx(event.x) / self.zoom
            y = self.canvas.canvasy(event.y) / self.zoom
            area = self.find_boundary_at(x, y)
            if area:
                name = area.properties.get("name", "")
                wp_name = self._select_work_product_for_area(name)
                if wp_name:
                    self._place_work_product(wp_name, x, y, area=area)
                return
            self.show_context_menu(event)

    def show_context_menu(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        diag = self.repo.diagrams.get(self.diagram_id)
        conn = self.find_connection(x, y)
        obj = None
        if not conn:
            obj = self.find_object(x, y)
            if not obj:
                if diag and diag.diag_type == "Internal Block Diagram":
                    menu = tk.Menu(self, tearoff=0)
                    menu.add_command(label="Set Father", command=self._set_diagram_father)
                    menu.tk_popup(event.x_root, event.y_root)
                return
        self.selected_obj = obj
        self.selected_conn = conn
        menu = tk.Menu(self, tearoff=0)
        if obj:
            menu.add_command(label="Properties", command=lambda: self._edit_object(obj))
            diag_id = self.repo.get_linked_diagram(obj.element_id)
            if diag_id and diag_id in self.repo.diagrams or obj.properties.get("view"):
                menu.add_command(
                    label="Open Linked Diagram", command=lambda: self._open_linked_diagram(obj)
                )
            menu.add_separator()
            menu.add_command(label="Copy", command=self.copy_selected)
            menu.add_command(label="Cut", command=self.cut_selected)
            menu.add_command(label="Paste", command=self.paste_selected)
            if diag and diag.diag_type == "Internal Block Diagram" and obj.obj_type == "Part":
                menu.add_separator()
                menu.add_command(
                    label="Remove Part from Diagram",
                    command=lambda: self.remove_part_diagram(obj),
                )
                menu.add_command(
                    label="Remove Part from Model",
                    command=lambda: self.remove_part_model(obj),
                )
            if diag and diag.diag_type == "Governance Diagram":
                menu.add_separator()
                menu.add_command(
                    label="Bring to Front", command=lambda o=obj: self.bring_to_front(o)
                )
                menu.add_command(
                    label="Send to Back", command=lambda o=obj: self.send_to_back(o)
                )
                menu.add_command(
                    label="Move Forward", command=lambda o=obj: self.move_forward(o)
                )
                menu.add_command(
                    label="Move Backward", command=lambda o=obj: self.move_backward(o)
                )
            menu.add_separator()
            menu.add_command(label="Delete", command=self.delete_selected)
        elif conn:
            menu.add_command(label="Properties", command=lambda: ConnectionDialog(self, conn))
            menu.add_separator()
            menu.add_command(label="Delete", command=self.delete_selected)
        menu.tk_popup(event.x_root, event.y_root)

    def bring_to_front(self, obj: SysMLObject) -> None:
        """Move ``obj`` to the top of the draw order."""
        if obj in self.objects:
            self.objects.remove(obj)
            self.objects.append(obj)
            self.redraw()

    def send_to_back(self, obj: SysMLObject) -> None:
        """Move ``obj`` to the bottom of the draw order."""
        if obj in self.objects:
            self.objects.remove(obj)
            self.objects.insert(0, obj)
            self.redraw()

    def move_forward(self, obj: SysMLObject) -> None:
        """Raise ``obj`` one step in the draw order."""
        if obj in self.objects:
            idx = self.objects.index(obj)
            if idx < len(self.objects) - 1:
                self.objects[idx], self.objects[idx + 1] = self.objects[idx + 1], self.objects[idx]
                self.redraw()

    def move_backward(self, obj: SysMLObject) -> None:
        """Lower ``obj`` one step in the draw order."""
        if obj in self.objects:
            idx = self.objects.index(obj)
            if idx > 0:
                self.objects[idx], self.objects[idx - 1] = self.objects[idx - 1], self.objects[idx]
                self.redraw()

    def _edit_object(self, obj):
        self._sync_to_repository()
        SysMLObjectDialog(self, obj)
        self._sync_to_repository()
        self.redraw()
        if self.app:
            self.app.update_views()
        self.update_property_view()
        if getattr(self, "app", None):
            self.app.update_views()

    def _open_linked_diagram(self, obj) -> bool:
        diag_id = self.repo.get_linked_diagram(obj.element_id)
        if not diag_id and obj.obj_type == "Part":
            def_id = obj.properties.get("definition")
            if def_id:
                diag_id = self.repo.get_linked_diagram(def_id)
        view_id = obj.properties.get("view")
        if (
            obj.obj_type in ("CallBehaviorAction", "Action")
            and diag_id
            and view_id
            and view_id in self.repo.diagrams
        ):
            if messagebox.askyesno("Open Diagram", "Open Behavior Diagram?\nChoose No for View"):
                chosen = diag_id
            else:
                chosen = view_id
        else:
            chosen = diag_id or view_id
        if not chosen or chosen not in self.repo.diagrams:
            return False
        # Avoid opening duplicate windows for the same diagram within the
        # current container. If a child frame already displays the chosen
        # diagram, simply return.
        for child in self.master.winfo_children():
            if getattr(child, "diagram_id", None) == chosen:
                return True
        diag = self.repo.diagrams[chosen]
        history = self.diagram_history + [self.diagram_id]
        if diag.diag_type == "Use Case Diagram":
            UseCaseDiagramWindow(self.master, self.app, diagram_id=chosen, history=history)
        elif diag.diag_type == "Activity Diagram":
            ActivityDiagramWindow(self.master, self.app, diagram_id=chosen, history=history)
        elif diag.diag_type == "Governance Diagram":
            GovernanceDiagramWindow(self.master, self.app, diagram_id=chosen, history=history)
        elif diag.diag_type == "Block Diagram":
            BlockDiagramWindow(self.master, self.app, diagram_id=chosen, history=history)
        elif diag.diag_type == "Internal Block Diagram":
            InternalBlockDiagramWindow(self.master, self.app, diagram_id=chosen, history=history)
        self._sync_to_repository()
        self.destroy()
        return True

    def _set_diagram_father(self) -> None:
        diag = self.repo.diagrams.get(self.diagram_id)
        if not diag or diag.diag_type != "Internal Block Diagram":
            return
        dlg = DiagramPropertiesDialog(self, diag)
        for data in getattr(dlg, "added_parts", []):
            self.objects.append(SysMLObject(**data))
        self._sync_to_repository()
        self.redraw()
        if self.app:
            self.app.update_views()

    def go_back(self):
        if not self.diagram_history:
            return
        prev_id = self.diagram_history.pop()
        diag = self.repo.diagrams.get(prev_id)
        if not diag:
            return
        if diag.diag_type == "Use Case Diagram":
            UseCaseDiagramWindow(
                self.master, self.app, diagram_id=prev_id, history=self.diagram_history
            )
        elif diag.diag_type == "Activity Diagram":
            ActivityDiagramWindow(
                self.master, self.app, diagram_id=prev_id, history=self.diagram_history
            )
        elif diag.diag_type == "Governance Diagram":
            GovernanceDiagramWindow(
                self.master, self.app, diagram_id=prev_id, history=self.diagram_history
            )
        elif diag.diag_type == "Block Diagram":
            BlockDiagramWindow(
                self.master, self.app, diagram_id=prev_id, history=self.diagram_history
            )
        elif diag.diag_type == "Internal Block Diagram":
            InternalBlockDiagramWindow(
                self.master, self.app, diagram_id=prev_id, history=self.diagram_history
            )
        self._sync_to_repository()
        self.destroy()

    def on_ctrl_mousewheel(self, event):
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    # ------------------------------------------------------------
    # Utility methods
    # ------------------------------------------------------------
    def _find_object_strategy1(
        self, x: float, y: float, prefer_port: bool = False
    ) -> SysMLObject | None:
        if prefer_port:
            for obj in reversed(self.objects):
                if obj.obj_type != "Port":
                    continue
                ox = obj.x * self.zoom
                oy = obj.y * self.zoom
                w = obj.width * self.zoom / 2
                h = obj.height * self.zoom / 2
                if ox - w <= x <= ox + w and oy - h <= y <= oy + h:
                    return obj

        for obj in reversed(self.objects):
            ox = obj.x * self.zoom
            oy = obj.y * self.zoom
            w = obj.width * self.zoom / 2
            h = obj.height * self.zoom / 2
            if obj.obj_type in ("Initial", "Final"):
                r = min(w, h)
                if (x - ox) ** 2 + (y - oy) ** 2 <= r**2:
                    return obj
            elif ox - w <= x <= ox + w and oy - h <= y <= oy + h:
                return obj
        return None

    def _find_object_strategy2(
        self, x: float, y: float, prefer_port: bool = False
    ) -> SysMLObject | None:
        if prefer_port:
            for obj in self.objects:
                if obj.obj_type != "Port":
                    continue
                ox = obj.x * self.zoom
                oy = obj.y * self.zoom
                w = obj.width * self.zoom / 2
                h = obj.height * self.zoom / 2
                if ox - w <= x <= ox + w and oy - h <= y <= oy + h:
                    return obj

        for obj in self.objects:
            ox = obj.x * self.zoom
            oy = obj.y * self.zoom
            w = obj.width * self.zoom / 2
            h = obj.height * self.zoom / 2
            if ox - w <= x <= ox + w and oy - h <= y <= oy + h:
                return obj
        return None

    def _find_object_strategy3(
        self, x: float, y: float, prefer_port: bool = False
    ) -> SysMLObject | None:
        closest = None
        best = float("inf")
        for obj in self.objects:
            ox = obj.x * self.zoom
            oy = obj.y * self.zoom
            w = obj.width * self.zoom / 2
            h = obj.height * self.zoom / 2
            if ox - w <= x <= ox + w and oy - h <= y <= oy + h:
                dist = (x - ox) ** 2 + (y - oy) ** 2
                if dist < best:
                    best = dist
                    closest = obj
        return closest

    def _find_object_strategy4(
        self, x: float, y: float, prefer_port: bool = False
    ) -> SysMLObject | None:
        rx, ry = round(x), round(y)
        for obj in reversed(self.objects):
            ox = round(obj.x * self.zoom)
            oy = round(obj.y * self.zoom)
            w = round(obj.width * self.zoom / 2)
            h = round(obj.height * self.zoom / 2)
            if ox - w <= rx <= ox + w and oy - h <= ry <= oy + h:
                return obj
        return None

    def find_object(self, x: float, y: float, prefer_port: bool = False) -> SysMLObject | None:
        for strat in (
            self._find_object_strategy1,
            self._find_object_strategy2,
            self._find_object_strategy3,
            self._find_object_strategy4,
        ):
            obj = strat(x, y, prefer_port)
            if obj:
                return obj
        return None

    def hit_resize_handle(self, obj: SysMLObject, x: float, y: float) -> str | None:
        if obj.obj_type in _FIXED_SIZE_TYPES:
            return None
        margin = 5
        ox = obj.x * self.zoom
        oy = obj.y * self.zoom
        w = obj.width * self.zoom / 2
        h = obj.height * self.zoom / 2
        left = ox - w
        right = ox + w
        top = oy - h
        bottom = oy + h
        near_left = abs(x - left) <= margin
        near_right = abs(x - right) <= margin
        near_top = abs(y - top) <= margin
        near_bottom = abs(y - bottom) <= margin
        if near_left and near_top:
            return "nw"
        if near_right and near_top:
            return "ne"
        if near_left and near_bottom:
            return "sw"
        if near_right and near_bottom:
            return "se"
        if near_left:
            return "w"
        if near_right:
            return "e"
        if near_top:
            return "n"
        if near_bottom:
            return "s"
        return None

    def hit_compartment_toggle(self, obj: SysMLObject, x: float, y: float) -> str | None:
        """Return the label of the compartment toggle hit at *(x, y)* or ``None``."""
        for oid, label, (x1, y1, x2, y2) in self.compartment_buttons:
            if oid == obj.obj_id and x1 <= x <= x2 and y1 <= y <= y2:
                return label
        return None

    def _dist_to_segment(self, p, a, b) -> float:
        px, py = p
        ax, ay = a
        bx, by = b
        if ax == bx and ay == by:
            return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
        t = ((px - ax) * (bx - ax) + (py - ay) * (by - ay)) / ((bx - ax) ** 2 + (by - ay) ** 2)
        t = max(0, min(1, t))
        lx = ax + t * (bx - ax)
        ly = ay + t * (by - ay)
        return ((px - lx) ** 2 + (py - ly) ** 2) ** 0.5

    def _segment_intersection(self, p1, p2, p3, p4):
        """Return intersection point (x, y, t) of segments *p1*-*p2* and *p3*-*p4* or None."""
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        x4, y4 = p4
        denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
        if denom == 0:
            return None
        t = ((x3 - x1) * (y4 - y3) - (y3 - y1) * (x4 - x3)) / denom
        u = ((x3 - x1) * (y2 - y1) - (y3 - y1) * (x2 - x1)) / denom
        if 0 <= t <= 1 and 0 <= u <= 1:
            ix = x1 + t * (x2 - x1)
            iy = y1 + t * (y2 - y1)
            return ix, iy, t
        return None

    def _nearest_diamond_corner(self, obj: SysMLObject, tx: float, ty: float) -> Tuple[float, float]:
        """Return the diamond corner of *obj* closest to the target (*tx*, *ty*)."""
        x = obj.x * self.zoom
        y = obj.y * self.zoom
        w = obj.width * self.zoom / 2
        h = obj.height * self.zoom / 2
        corners = [
            (x, y - h),
            (x + w, y),
            (x, y + h),
            (x - w, y),
        ]
        return min(corners, key=lambda p: (p[0] - tx) ** 2 + (p[1] - ty) ** 2)

    def _corner_index(self, pos: tuple[float, float]) -> int:
        rx, ry = pos
        if abs(rx) >= abs(ry):
            return 1 if rx >= 0 else 3
        else:
            return 2 if ry >= 0 else 0

    def _decision_used_corners(
        self, obj_id: int, exclude: DiagramConnection | None = None
    ) -> set[int]:
        used: set[int] = set()
        for conn in self.connections:
            if conn is exclude:
                continue
            if conn.src == obj_id and conn.src_pos:
                used.add(self._corner_index(conn.src_pos))
            if conn.dst == obj_id and conn.dst_pos:
                used.add(self._corner_index(conn.dst_pos))
        return used

    def _choose_decision_corner(
        self, node: SysMLObject, other: SysMLObject, used: set[int]
    ) -> tuple[float, float] | None:
        corners = [(0.0, -1.0), (1.0, 0.0), (0.0, 1.0), (-1.0, 0.0)]
        w = node.width * self.zoom / 2
        h = node.height * self.zoom / 2
        corner_pts = [
            (node.x * self.zoom, node.y * self.zoom - h),
            (node.x * self.zoom + w, node.y * self.zoom),
            (node.x * self.zoom, node.y * self.zoom + h),
            (node.x * self.zoom - w, node.y * self.zoom),
        ]
        pref = self._nearest_diamond_corner(node, other.x * self.zoom, other.y * self.zoom)
        pref_idx = corner_pts.index(pref)
        order = [pref_idx, (pref_idx + 1) % 4, (pref_idx + 3) % 4, (pref_idx + 2) % 4]
        for idx in order:
            if idx not in used:
                return corners[idx]
        return None

    def _assign_decision_corner(
        self,
        conn: DiagramConnection,
        node: SysMLObject,
        attr: str,
        pref: tuple[float, float] | None = None,
    ) -> bool:
        """Assign a connection endpoint to a unique corner of *node*.

        ``attr`` is either ``"src_pos"`` or ``"dst_pos"`` identifying which
        endpoint to update.  ``pref`` optionally provides a preferred relative
        location.  The method ensures that each decision/merge node is limited to
        four connections, one per corner.  Returns ``True`` if a corner was
        assigned, ``False`` when no free corner is available.
        """

        corners = [(0.0, -1.0), (1.0, 0.0), (0.0, 1.0), (-1.0, 0.0)]

        # Determine which corners are already occupied by other connections
        used: set[int] = set()
        for other in self.connections:
            if other is conn:
                continue
            if other.src == node.obj_id and other.src_pos:
                rx, ry = other.src_pos
            elif other.dst == node.obj_id and other.dst_pos:
                rx, ry = other.dst_pos
            else:
                continue
            if abs(rx) >= abs(ry):
                used.add(1 if rx >= 0 else 3)
            else:
                used.add(2 if ry >= 0 else 0)

        # If a preferred corner was provided, try to use it
        if pref is not None:
            rx, ry = pref
            if abs(rx) >= abs(ry):
                idx = 1 if rx >= 0 else 3
            else:
                idx = 2 if ry >= 0 else 0
            if idx in used:
                return False
            setattr(conn, attr, corners[idx])
            return True

        # Choose the corner nearest to the other object, falling back to the
        # first available corner if necessary
        other = self.get_object(conn.dst if attr == "src_pos" else conn.src)
        if other:
            x = node.x * self.zoom
            y = node.y * self.zoom
            w = node.width * self.zoom / 2
            h = node.height * self.zoom / 2
            corner_pts = [(x, y - h), (x + w, y), (x, y + h), (x - w, y)]
            tx = other.x * self.zoom
            ty = other.y * self.zoom
            pref_idx = min(range(4), key=lambda i: (corner_pts[i][0] - tx) ** 2 + (corner_pts[i][1] - ty) ** 2)
            order = [pref_idx, (pref_idx + 1) % 4, (pref_idx + 3) % 4, (pref_idx + 2) % 4]
            for idx in order:
                if idx not in used:
                    setattr(conn, attr, corners[idx])
                    return True

        for idx, corner in enumerate(corners):
            if idx not in used:
                setattr(conn, attr, corner)
                return True
        return False

    def _assign_decision_corners(self, conn: DiagramConnection) -> None:
        src_obj = self.get_object(conn.src)
        dst_obj = self.get_object(conn.dst)
        corners = [(0.0, -1.0), (1.0, 0.0), (0.0, 1.0), (-1.0, 0.0)]

        if src_obj and src_obj.obj_type in ("Decision", "Merge") and dst_obj:
            used = self._decision_used_corners(src_obj.obj_id, exclude=conn)
            pair_idx = None
            for other in self.connections:
                if other is conn:
                    continue
                if other.src == dst_obj.obj_id and other.dst == src_obj.obj_id and other.dst_pos:
                    pair_idx = self._corner_index(other.dst_pos)
                    break
            corner = None
            if pair_idx is not None:
                opp_idx = (pair_idx + 2) % 4
                if opp_idx not in used:
                    corner = corners[opp_idx]
            if corner is None:
                corner = self._choose_decision_corner(src_obj, dst_obj, used)
            if corner:
                conn.src_pos = corner

        if dst_obj and dst_obj.obj_type in ("Decision", "Merge") and src_obj:
            used = self._decision_used_corners(dst_obj.obj_id, exclude=conn)
            pair_idx = None
            for other in self.connections:
                if other is conn:
                    continue
                if other.src == dst_obj.obj_id and other.dst == src_obj.obj_id and other.src_pos:
                    pair_idx = self._corner_index(other.src_pos)
                    break
            corner = None
            if pair_idx is not None:
                opp_idx = (pair_idx + 2) % 4
                if opp_idx not in used:
                    corner = corners[opp_idx]
            if corner is None:
                corner = self._choose_decision_corner(dst_obj, src_obj, used)
            if corner:
                conn.dst_pos = corner

    def find_connection(self, x: float, y: float) -> DiagramConnection | None:
        diag = self.repo.diagrams.get(self.diagram_id)
        for conn in self.connections:
            src = self.get_object(conn.src)
            dst = self.get_object(conn.dst)
            if not src or not dst:
                continue
            # Control flow connectors are drawn as a vertical line between
            # elements. Mirror that behavior so they can be located when
            # selecting.
            if diag and diag.diag_type == "Control Flow Diagram" and conn.conn_type in (
                "Control Action",
                "Feedback",
            ):
                a_left = src.x - src.width / 2
                a_right = src.x + src.width / 2
                b_left = dst.x - dst.width / 2
                b_right = dst.x + dst.width / 2
                cx_val = (
                    conn.points[0][0]
                    if conn.points
                    else (max(a_left, b_left) + min(a_right, b_right)) / 2
                )
                cx_val = SysMLDiagramWindow._constrain_control_flow_x(
                    self, conn, cx_val
                )
                cx = cx_val * self.zoom
                ayc = src.y * self.zoom
                byc = dst.y * self.zoom
                if ayc <= byc:
                    cy1 = ayc + src.height / 2 * self.zoom
                    cy2 = byc - dst.height / 2 * self.zoom
                else:
                    cy1 = ayc - src.height / 2 * self.zoom
                    cy2 = byc + dst.height / 2 * self.zoom
                if (
                    self._dist_to_segment((x, y), (cx, cy1), (cx, cy2))
                    <= CONNECTION_SELECT_RADIUS
                ):
                    return conn
                continue

            if conn.src == conn.dst:
                sx, sy = self.edge_point(src, 0, 0, (1, 0))
                size = max(src.width, src.height) * 0.5 * self.zoom
                points = [
                    (sx, sy),
                    (sx + size, sy),
                    (sx + size, sy - size),
                    (sx, sy - size),
                    (sx, sy),
                ]
            else:
                sx, sy = self.edge_point(
                    src,
                    dst.x * self.zoom,
                    dst.y * self.zoom,
                    conn.src_pos,
                )
                points = [(sx, sy)]
                if conn.style == "Squared":
                    if conn.points:
                        mx = conn.points[0][0] * self.zoom
                    else:
                        mx = (src.x + dst.x) / 2 * self.zoom
                    points.extend([(mx, points[-1][1]), (mx, dst.y * self.zoom)])
                elif conn.style == "Custom":
                    for px, py in conn.points:
                        xpt = px * self.zoom
                        ypt = py * self.zoom
                        last = points[-1]
                        points.extend([(xpt, last[1]), (xpt, ypt)])
                ex, ey = self.edge_point(
                    dst,
                    src.x * self.zoom,
                    src.y * self.zoom,
                    conn.dst_pos,
                )
                points.append((ex, ey))
            for a, b in zip(points[:-1], points[1:]):
                if self._dist_to_segment((x, y), a, b) <= CONNECTION_SELECT_RADIUS:
                    return conn
        return None

    def snap_port_to_parent(self, port: SysMLObject, parent: SysMLObject) -> None:
        snap_port_to_parent_obj(port, parent)

    def edge_point(
        self,
        obj: SysMLObject,
        tx: float,
        ty: float,
        rel: tuple[float, float] | None = None,
        apply_radius: bool = True,
    ) -> Tuple[float, float]:
        cx = obj.x * self.zoom
        cy = obj.y * self.zoom

        def _intersect(vx: float, vy: float, w: float, h: float, r: float) -> Tuple[float, float]:
            """Return intersection of a ray from the origin with a rounded rectangle."""
            if vx == 0 and vy == 0:
                return 0.0, 0.0

            wi, hi = w - r, h - r
            signx = 1 if vx >= 0 else -1
            signy = 1 if vy >= 0 else -1
            candidates: list[tuple[float, float, float]] = []

            if vx != 0:
                t_v = (signx * w) / vx
                if t_v >= 0:
                    y_v = vy * t_v
                    if abs(y_v) <= hi:
                        candidates.append((t_v, signx * w, y_v))

            if vy != 0:
                t_h = (signy * h) / vy
                if t_h >= 0:
                    x_h = vx * t_h
                    if abs(x_h) <= wi:
                        candidates.append((t_h, x_h, signy * h))

            if r > 0:
                cx_arc, cy_arc = signx * wi, signy * hi
                a = vx * vx + vy * vy
                b = -2 * (vx * cx_arc + vy * cy_arc)
                c = cx_arc * cx_arc + cy_arc * cy_arc - r * r
                disc = b * b - 4 * a * c
                if disc >= 0:
                    sqrt_disc = math.sqrt(disc)
                    for t_arc in ((-b - sqrt_disc) / (2 * a), (-b + sqrt_disc) / (2 * a)):
                        if t_arc >= 0:
                            x_arc = vx * t_arc
                            y_arc = vy * t_arc
                            if signx * x_arc >= wi and signy * y_arc >= hi:
                                candidates.append((t_arc, x_arc, y_arc))

            if not candidates:
                return 0.0, 0.0

            t, ix, iy = min(candidates, key=lambda c: c[0])
            return ix, iy

        if obj.obj_type == "Port":
            # Ports are drawn as 12x12 squares regardless of object width/height.
            # Compute the intersection with this square so connectors touch its edge
            # rather than reaching the center.
            w = h = 6 * self.zoom
            if rel is not None:
                rx, ry = rel
                vx = rx * w
                vy = ry * h
            else:
                vx = tx - cx
                vy = ty - cy
            ix, iy = _intersect(vx, vy, w, h, 0.0)
            return cx + ix, cy + iy

        w = obj.width * self.zoom / 2
        h = obj.height * self.zoom / 2
        radius = 0.0
        if apply_radius:
            if obj.obj_type == "Block":
                radius = 6 * self.zoom
            elif obj.obj_type == "System Boundary":
                radius = 12 * self.zoom
            elif obj.obj_type in ("Action Usage", "Action", "CallBehaviorAction"):
                radius = 8 * self.zoom

        if rel is not None:
            rx, ry = rel
            if obj.obj_type in ("Decision", "Merge"):
                if abs(rx) >= abs(ry):
                    return (cx + (w if rx >= 0 else -w), cy)
                else:
                    return (cx, cy + (h if ry >= 0 else -h))
            vx = rx * obj.width / 2 * self.zoom
            vy = ry * obj.height / 2 * self.zoom
            ix, iy = _intersect(vx, vy, w, h, radius if apply_radius else 0.0)
            return cx + ix, cy + iy

        dx = tx - cx
        dy = ty - cy
        if obj.obj_type in ("Initial", "Final"):
            r = min(w, h)
            dist = (dx**2 + dy**2) ** 0.5 or 1
            return cx + dx / dist * r, cy + dy / dist * r
        if obj.obj_type in ("Decision", "Merge"):
            points = [
                (cx, cy - h),
                (cx + w, cy),
                (cx, cy + h),
                (cx - w, cy),
            ]
            best = None
            for i in range(len(points)):
                p3 = points[i]
                p4 = points[(i + 1) % len(points)]
                inter = SysMLDiagramWindow._segment_intersection(
                    self, (cx, cy), (tx, ty), p3, p4
                )
                if inter:
                    ix, iy, t = inter
                    if best is None or t < best[2]:
                        best = (ix, iy, t)
            if best:
                return best[0], best[1]

        ix, iy = _intersect(dx, dy, w, h, radius)
        return cx + ix, cy + iy

    def _line_rect_intersection(
        self,
        px: float,
        py: float,
        dx: float,
        dy: float,
        obj: SysMLObject,
    ) -> Tuple[float, float]:
        cx = obj.x * self.zoom
        cy = obj.y * self.zoom
        hw = obj.width * self.zoom / 2
        hh = obj.height * self.zoom / 2
        left, right = cx - hw, cx + hw
        top, bottom = cy - hh, cy + hh
        candidates: list[tuple[float, float, float]] = []
        if dx != 0:
            t = (left - px) / dx
            if t >= 0:
                y = py + t * dy
                if top <= y <= bottom:
                    candidates.append((t, left, y))
            t = (right - px) / dx
            if t >= 0:
                y = py + t * dy
                if top <= y <= bottom:
                    candidates.append((t, right, y))
        if dy != 0:
            t = (top - py) / dy
            if t >= 0:
                x = px + t * dx
                if left <= x <= right:
                    candidates.append((t, x, top))
            t = (bottom - py) / dy
            if t >= 0:
                x = px + t * dx
                if left <= x <= right:
                    candidates.append((t, x, bottom))
        if not candidates:
            return px, py
        t, ix, iy = min(candidates, key=lambda c: c[0])
        return ix, iy

    def sync_ports(self, part: SysMLObject) -> None:
        names: List[str] = []
        block_id = part.properties.get("definition")
        if block_id and block_id in self.repo.elements:
            block_elem = self.repo.elements[block_id]
            names.extend(
                [p.strip() for p in block_elem.properties.get("ports", "").split(",") if p.strip()]
            )
        names.extend([p.strip() for p in part.properties.get("ports", "").split(",") if p.strip()])
        existing_ports = [
            o
            for o in self.objects
            if o.obj_type == "Port" and o.properties.get("parent") == str(part.obj_id)
        ]
        existing: dict[str, SysMLObject] = {}
        for p in list(existing_ports):
            name = p.properties.get("name")
            if name in existing:
                self.objects.remove(p)
            else:
                existing[name] = p
        for n in names:
            if n not in existing:
                port = SysMLObject(
                    _get_next_id(),
                    "Port",
                    part.x + part.width / 2 + 20,
                    part.y,
                    properties={
                        "name": n,
                        "parent": str(part.obj_id),
                        "side": "E",
                        "labelX": "8",
                        "labelY": "-8",
                    },
                    phase=_repo_phase(self.repo),
                )
                self.snap_port_to_parent(port, part)
                self.objects.append(port)
                existing[n] = port
        for n, obj in list(existing.items()):
            if n not in names:
                self.objects.remove(obj)
        self.sort_objects()

    def sync_boundary_ports(self, boundary: SysMLObject) -> None:
        names: List[str] = []
        block_id = boundary.element_id
        if block_id and block_id in self.repo.elements:
            block_elem = self.repo.elements[block_id]
            names.extend([
                p.strip() for p in block_elem.properties.get("ports", "").split(",") if p.strip()
            ])
        existing_ports = [
            o
            for o in self.objects
            if o.obj_type == "Port" and o.properties.get("parent") == str(boundary.obj_id)
        ]
        existing: dict[str, SysMLObject] = {}
        for p in list(existing_ports):
            name = p.properties.get("name")
            if name in existing:
                self.objects.remove(p)
            else:
                existing[name] = p
        for n in names:
            if n not in existing:
                port = SysMLObject(
                    _get_next_id(),
                    "Port",
                    boundary.x + boundary.width / 2 + 20,
                    boundary.y,
                    properties={
                        "name": n,
                        "parent": str(boundary.obj_id),
                        "side": "E",
                        "labelX": "8",
                        "labelY": "-8",
                    },
                    phase=_repo_phase(self.repo),
                )
                self.snap_port_to_parent(port, boundary)
                self.objects.append(port)
                existing[n] = port
        for n, obj in list(existing.items()):
            if n not in names:
                self.objects.remove(obj)
        self.sort_objects()

    def zoom_in(self):
        self.zoom *= 1.2
        self.font.config(size=int(8 * self.zoom))
        self.redraw()

    def zoom_out(self):
        self.zoom /= 1.2
        self.font.config(size=int(8 * self.zoom))
        self.redraw()

    def _block_compartments(self, obj: SysMLObject) -> list[tuple[str, str]]:
        """Return the list of compartments displayed for a Block."""
        parts = "\n".join(
            p.strip()
            for p in obj.properties.get("partProperties", "").split(",")
            if p.strip()
        )
        operations = "\n".join(
            format_operation(op)
            for op in parse_operations(obj.properties.get("operations", ""))
        )
        ports = "\n".join(
            p.strip() for p in obj.properties.get("ports", "").split(",") if p.strip()
        )
        reliability = "\n".join(
            f"{label}={obj.properties.get(key, '')}"
            for label, key in (
                ("FIT", "fit"),
                ("Qual", "qualification"),
                ("FM", "failureModes"),
            )
            if obj.properties.get(key, "")
        )
        requirements = "\n".join(r.get("id") for r in obj.requirements)
        return [
            ("Parts", parts),
            ("Operations", operations),
            ("Ports", ports),
            ("Reliability", reliability),
            ("Requirements", requirements),
        ]

    def _min_block_size(self, obj: SysMLObject) -> tuple[float, float]:
        """Return minimum width and height to display all Block text."""
        name = _format_label(self, obj.properties.get('name', ''), obj.phase, obj)
        header = f"<<block>> {name}".strip()
        width_px = self.font.measure(header) + 8 * self.zoom
        compartments = self._block_compartments(obj)
        total_lines = 1
        button_w = 12 * self.zoom
        for label, text in compartments:
            collapsed = obj.collapsed.get(label, False)
            lines = text.splitlines() if text else [""]
            if collapsed:
                # When collapsed only show the compartment name, not the first
                # element. Previously the first line of the compartment content
                # was appended which caused the label to display e.g.
                # "Parts: Motor". The design has changed to only display the
                # compartment title when collapsed so that it simply reads
                # "Parts".
                disp = f"{label}:"
                width_px = max(width_px, self.font.measure(disp) + button_w + 8 * self.zoom)
                total_lines += 1
            else:
                disp = f"{label}:"
                width_px = max(width_px, self.font.measure(disp) + button_w + 8 * self.zoom)
                for line in lines:
                    width_px = max(width_px, self.font.measure(line) + 8 * self.zoom)
                total_lines += 1 + len(lines)
        height_px = total_lines * 20 * self.zoom
        return width_px / self.zoom, height_px / self.zoom

    def _resize_block_to_content(self, obj: SysMLObject) -> None:
        """Resize a Block so its compartments fit its current state."""
        if obj.obj_type != "Block":  # pragma: no cover - safety check
            return
        _, min_h = self._min_block_size(obj)
        obj.height = min_h

    def _min_action_size(self, obj: SysMLObject) -> tuple[float, float]:
        """Return minimum width and height to display Action text without wrapping."""
        full_width_obj = replace(obj, width=10_000)
        lines = self._object_label_lines(full_width_obj)
        if not lines:
            return (10.0, 10.0)
        text_width = max(self.font.measure(line) for line in lines)
        text_height = self.font.metrics("linespace") * len(lines)
        padding = 6 * self.zoom
        return (text_width + padding) / self.zoom, (text_height + padding) / self.zoom

    def _min_data_acquisition_size(self, obj: SysMLObject) -> tuple[float, float]:
        """Return minimum width and height to display Data acquisition compartments."""
        compartments = obj.properties.get(
            "compartments", "data source1;data source2;data source 3"
        ).split(";")
        lines = [line for comp in compartments for line in comp.splitlines()]
        if not lines:
            lines = [""]
        text_width = max(self.font.measure(line) for line in lines)
        padding = 8 * self.zoom
        total_lines = sum(max(len(comp.splitlines()), 1) for comp in compartments)
        text_height = self.font.metrics("linespace") * max(total_lines, 1)
        return (text_width + padding) / self.zoom, (text_height + padding) / self.zoom

    def _wrap_text_to_width(self, text: str, width_px: float) -> list[str]:
        """Return *text* wrapped to fit within *width_px* pixels."""
        if self.font.measure(text) <= width_px:
            return [text]
        words = text.split()
        if not words:
            words = [text]

        if len(words) == 1 and self.font.measure(words[0]) > width_px:
            # single long word - wrap by characters
            lines: list[str] = []
            current = ""
            for ch in words[0]:
                if self.font.measure(current + ch) <= width_px:
                    current += ch
                else:
                    if current:
                        lines.append(current)
                    current = ch
            if current:
                lines.append(current)
            return lines

        lines: list[str] = []
        current = words[0]
        for word in words[1:]:
            candidate = current + " " + word
            if self.font.measure(candidate) <= width_px:
                current = candidate
            else:
                lines.append(current)
                if self.font.measure(word) <= width_px:
                    current = word
                else:
                    # break long word
                    part = ""
                    for ch in word:
                        if self.font.measure(part + ch) <= width_px:
                            part += ch
                        else:
                            if part:
                                lines.append(part)
                            part = ch
                    current = part
        if current:
            lines.append(current)
        return lines

    def _object_label_lines(self, obj: SysMLObject) -> list[str]:
        """Return the lines of text displayed inside *obj*."""
        if obj.obj_type == "System Boundary" or obj.obj_type == "Block Boundary":
            name = _format_label(self, obj.properties.get("name", ""), obj.phase, obj)
            return [name] if name else []

        if obj.obj_type in ("Block", "Port"):
            # Blocks and ports use custom drawing logic
            return []

        name = obj.properties.get("name", "")
        has_name = False
        def_id = obj.properties.get("definition")
        if obj.element_id and obj.element_id in self.repo.elements:
            elem = self.repo.elements[obj.element_id]
            name = elem.name or elem.properties.get("component", "")
            def_id = def_id or elem.properties.get("definition")
            def_name = ""
            if def_id and def_id in self.repo.elements:
                def_name = self.repo.elements[def_id].name or def_id
            has_name = bool(name) and not _is_default_part_name(def_name, name)

        if not has_name:
            name = ""
        if obj.obj_type == "Part":
            asil = calculate_allocated_asil(obj.requirements)
            if obj.properties.get("asil") != asil:
                obj.properties["asil"] = asil
                if obj.element_id and obj.element_id in self.repo.elements:
                    self.repo.elements[obj.element_id].properties["asil"] = asil
            def_id = obj.properties.get("definition")
            mult = None
            comp = obj.properties.get("component", "")
            if def_id and def_id in self.repo.elements:
                def_name = self.repo.elements[def_id].name or def_id
                diag = self.repo.diagrams.get(self.diagram_id)
                block_id = (
                    getattr(diag, "father", None)
                    or next(
                        (
                            eid
                            for eid, did in self.repo.element_diagrams.items()
                            if did == self.diagram_id
                        ),
                        None,
                    )
                )
                if block_id:
                    for rel in self.repo.relationships:
                        if (
                            rel.rel_type in ("Aggregation", "Composite Aggregation")
                            and rel.source == block_id
                            and rel.target == def_id
                        ):
                            mult = rel.properties.get("multiplicity", "1")
                            if mult in ("", "1"):
                                mult = None
                            break
                base = name
                index = None
                m = re.match(r"^(.*)\[(\d+)\]$", name)
                if m:
                    base = m.group(1)
                    index = int(m.group(2))
                if index is not None:
                    base = f"{base} {index}"
                name = base
                if obj.element_id and obj.element_id in self.repo.elements and not comp:
                    comp = self.repo.elements[obj.element_id].properties.get("component", "")
                if comp and comp == def_name:
                    comp = ""
                if mult:
                    if ".." in mult:
                        upper = mult.split("..", 1)[1] or "*"
                        disp = f"{index or 1}..{upper}"
                    elif mult == "*":
                        disp = f"{index or 1}..*"
                    else:
                        disp = f"{index or 1}..{mult}"
                    def_part = f"{def_name} [{disp}]"
                else:
                    def_part = def_name
                if comp:
                    def_part = f"{comp} / {def_part}"
                if name and def_part != name:
                    name = f"{name} : {def_part}"
                elif not name:
                    name = f" : {def_part}"

        name = _format_label(self, name, obj.phase, obj)
        lines: list[str] = []
        diag_id = self.repo.get_linked_diagram(obj.element_id)
        if diag_id and diag_id in self.repo.diagrams:
            diag = self.repo.diagrams[diag_id]
            diag_name = _format_label(self, diag.name or diag_id, diag.phase)
            lines.append(diag_name)

        if obj.obj_type in ("Action", "CallBehaviorAction") and name:
            max_width = obj.width * self.zoom - 6 * self.zoom
            if max_width > 0:
                for part in name.splitlines():
                    wrapped = self._wrap_text_to_width(part, max_width)
                    lines.extend(wrapped)
            else:
                lines.extend(name.splitlines())
        elif obj.obj_type == "Work Product" and name:
            lines.extend(name.split())
        else:
            lines.extend(name.splitlines())

        key = obj.obj_type.replace(" ", "")
        if not key.endswith("Usage"):
            key += "Usage"
        for prop in SYSML_PROPERTIES.get(key, []):
            if obj.obj_type == "Part" and prop in (
                "fit",
                "qualification",
                "failureModes",
                "asil",
            ):
                continue
            val = obj.properties.get(prop)
            if val:
                lines.append(f"{prop}: {val}")

        if obj.obj_type == "Part":
            rel_items = []
            for lbl, key in (
                ("ASIL", "asil"),
                ("FIT", "fit"),
                ("Qual", "qualification"),
                ("FM", "failureModes"),
            ):
                val = obj.properties.get(key)
                if val:
                    rel_items.append(f"{lbl}: {val}")
            if rel_items:
                lines.extend(rel_items)
            reqs = "; ".join(r.get("id") for r in obj.requirements)
            if reqs:
                lines.append(f"Reqs: {reqs}")

        return lines

    def ensure_text_fits(self, obj: SysMLObject) -> None:
        """Expand the object's size so its label is fully visible."""
        if obj.obj_type == "Block":
            b_w, b_h = self._min_block_size(obj)
            min_w, min_h = b_w, b_h
        elif obj.obj_type == "Data acquisition":
            min_w, min_h = self._min_data_acquisition_size(obj)
            obj.width = max(obj.width, min_w)
            obj.height = max(obj.height, min_h)
            return
        elif obj.obj_type == "Role":
            return
        else:
            label_lines = self._object_label_lines(obj)
            if not label_lines:
                return

            text_width = max(self.font.measure(line) for line in label_lines)
            text_height = self.font.metrics("linespace") * len(label_lines)
            if obj.obj_type in ("Action", "CallBehaviorAction"):
                padding = 6 * self.zoom
                if text_width + padding <= obj.width * self.zoom:
                    min_w = obj.width
                else:
                    min_w = (text_width + padding) / self.zoom
            else:
                padding = 10 * self.zoom
                min_w = (text_width + padding) / self.zoom
            min_h = (text_height + padding) / self.zoom

        if obj.obj_type in ("Block",):
            # _min_block_size already accounts for text padding
            pass
        elif obj.obj_type in (
            "Fork",
            "Join",
            "Initial",
            "Final",
            "Decision",
            "Merge",
        ):
            min_h = obj.height  # height remains unchanged for these types
        if min_w > obj.width:
            obj.width = min_w
        if obj.obj_type not in (
            "Fork",
            "Join",
            "Initial",
            "Final",
            "Decision",
            "Merge",
        ) and min_h > obj.height:
            obj.height = min_h
    def sort_objects(self) -> None:
        """Order objects so boundaries render behind and their ports above."""

        def key(o: SysMLObject) -> int:
            if o.obj_type in ("System Boundary", "Block Boundary", "Existing Element"):
                return 0
            if o.obj_type == "Port":
                parent_id = o.properties.get("parent")
                if parent_id:
                    try:
                        pid = int(parent_id)
                    except (TypeError, ValueError):
                        pid = None
                    if pid is not None:
                        for obj in self.objects:
                            if obj.obj_id == pid and obj.obj_type == "Block Boundary":
                                return 2
            return 1

        self.objects.sort(key=key)

    def redraw(self):
        self.canvas.configure(bg=StyleManager.get_instance().canvas_bg)
        self.canvas.delete("all")
        self.gradient_cache.clear()
        self.compartment_buttons = []
        self.sort_objects()
        remove_orphan_ports(self.objects)
        for obj in list(self.objects):
            if getattr(obj, "hidden", False):
                continue
            if obj.obj_type == "Part":
                self.sync_ports(obj)
            if obj.obj_type == "Block Boundary":
                self.sync_boundary_ports(obj)
            self.ensure_text_fits(obj)
            self.draw_object(obj)
        for conn in self.connections:
            src = self.get_object(conn.src)
            dst = self.get_object(conn.dst)
            if (
                src
                and dst
                and not getattr(src, "hidden", False)
                and not getattr(dst, "hidden", False)
            ):
                if (
                    conn is self.selected_conn
                    and self.dragging_endpoint is not None
                    and self.endpoint_drag_pos
                ):
                    continue
                self.draw_connection(src, dst, conn, conn is self.selected_conn)
        if (
            self.selected_conn
            and self.dragging_endpoint is not None
            and self.endpoint_drag_pos
        ):
            other = (
                self.get_object(self.selected_conn.dst)
                if self.dragging_endpoint == "src"
                else self.get_object(self.selected_conn.src)
            )
            if other:
                rel = (
                    self.selected_conn.dst_pos
                    if self.dragging_endpoint == "src"
                    else self.selected_conn.src_pos
                )
                sx, sy = self.edge_point(other, *self.endpoint_drag_pos, rel)
                ex, ey = self.endpoint_drag_pos
                forward = self.selected_conn.arrow in ("forward", "both")
                backward = self.selected_conn.arrow in ("backward", "both")
                if self.dragging_endpoint == "src":
                    arrow_start = backward
                    arrow_end = forward
                else:
                    arrow_start = backward
                    arrow_end = forward
                if arrow_start and arrow_end:
                    style = tk.BOTH
                elif arrow_end:
                    style = tk.LAST
                elif arrow_start:
                    style = tk.FIRST
                else:
                    style = tk.NONE
                self.canvas.create_line(
                    sx,
                    sy,
                    ex,
                    ey,
                    dash=(2, 2),
                    arrow=style,
                    tags=("connection", "_temp_conn"),
                )
        if (
            self.start
            and self.temp_line_end
            and self.current_tool in _all_connection_tools()
        ):
            sx, sy = self.edge_point(self.start, *self.temp_line_end)
            ex, ey = self.temp_line_end
            self.canvas.create_line(
                sx,
                sy,
                ex,
                ey,
                dash=(2, 2),
                arrow=tk.LAST,
                tags=("connection", "_temp_conn"),
            )

        # Animate the temporary connection line so the dashes appear to move
        # toward the mouse cursor, providing visual feedback consistent across
        # all relationship types.
        find = getattr(self.canvas, "find_withtag", None)
        if find and find("_temp_conn"):
            if getattr(self, "_temp_conn_anim", None) is None:
                self._temp_conn_offset = 0
                self._animate_temp_connection()
        else:
            anim = getattr(self, "_temp_conn_anim", None)
            if anim:
                after_cancel = getattr(self.canvas, "after_cancel", None)
                if after_cancel:
                    after_cancel(anim)
                self._temp_conn_anim = None
        self.canvas.tag_raise("connection")
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def _animate_temp_connection(self):  # pragma: no cover - requires tkinter
        find = getattr(self.canvas, "find_withtag", None)
        configure = getattr(self.canvas, "itemconfigure", None)
        if not (find and configure):
            self._temp_conn_anim = None
            return
        line = find("_temp_conn")
        if line:
            offset = getattr(self, "_temp_conn_offset", 0)
            offset = (offset + 2) % 8
            self._temp_conn_offset = offset
            configure(line[0], dashoffset=offset)
            after = getattr(self.canvas, "after", None)
            if after:
                self._temp_conn_anim = after(100, self._animate_temp_connection)
        else:
            self._temp_conn_anim = None

    def _create_round_rect(self, x1, y1, x2, y2, radius=10, **kwargs):
        """Draw a rectangle with rounded corners on the canvas."""
        rad = min(radius, abs(x2 - x1) / 2, abs(y2 - y1) / 2)
        points = [
            x1 + rad,
            y1,
            x2 - rad,
            y1,
            x2,
            y1,
            x2,
            y1 + rad,
            x2,
            y2 - rad,
            x2,
            y2,
            x2 - rad,
            y2,
            x1 + rad,
            y2,
            x1,
            y2,
            x1,
            y2 - rad,
            x1,
            y1 + rad,
            x1,
            y1,
        ]
        return self.canvas.create_polygon(points, smooth=True, splinesteps=36, **kwargs)

    def _create_gradient_image(self, width: int, height: int, color: str) -> tk.PhotoImage:
        """Return a left-to-right gradient image from white to *color*."""
        width = max(1, int(width))
        height = max(1, int(height))
        try:
            img = tk.PhotoImage(width=width, height=height)
        except RuntimeError:  # pragma: no cover - headless tests
            return None
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        for x in range(width):
            ratio = x / (width - 1) if width > 1 else 1
            nr = int(255 * (1 - ratio) + r * ratio)
            ng = int(255 * (1 - ratio) + g * ratio)
            nb = int(255 * (1 - ratio) + b * ratio)
            img.put(f"#{nr:02x}{ng:02x}{nb:02x}", to=(x, 0, x + 1, height))
        return img

    def _draw_gradient_rect(self, x1: float, y1: float, x2: float, y2: float, color: str, obj_id: int) -> None:
        """Draw a gradient rectangle on the canvas and cache the image."""
        img = self._create_gradient_image(abs(int(x2 - x1)), abs(int(y2 - y1)), color)
        if img is None:
            return
        self.canvas.create_image(min(x1, x2), min(y1, y2), anchor="nw", image=img)
        self.gradient_cache[obj_id] = img

    def _draw_cylinder(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        color: str,
        outline: str,
        obj_id: int,
    ) -> None:
        """Draw a cylinder shape matching the AI database icon."""

        oval_h = min(10 * self.zoom, (y2 - y1) / 2)
        self._draw_gradient_rect(x1, y1, x2, y2, color, obj_id)
        self.canvas.create_rectangle(x1, y1, x2, y2, outline=outline, fill="")
        self.canvas.create_oval(
            x1,
            y1 - oval_h,
            x2,
            y1 + oval_h,
            fill=color,
            outline=outline,
        )
        self.canvas.create_oval(
            x1,
            y2 - oval_h,
            x2,
            y2 + oval_h,
            fill=color,
            outline=outline,
        )


    def _draw_open_arrow(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        color: str = "black",
        width: int = 1,
        tags: str = "connection",
    ) -> None:
        """Draw an open triangular arrow head from *start* to *end*.

        This helper creates the classic hollow triangle used for
        generalization relationships. The interior is filled with the
        canvas background so the outline color defines the arrow shape.
        """
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.hypot(dx, dy)
        if length == 0:
            return
        size = 10 * self.zoom
        angle = math.atan2(dy, dx)
        spread = math.radians(20)
        p1 = (
            end[0] - size * math.cos(angle - spread),
            end[1] - size * math.sin(angle - spread),
        )
        p2 = (
            end[0] - size * math.cos(angle + spread),
            end[1] - size * math.sin(angle + spread),
        )
        # Draw the arrowhead as a small white triangle with the requested
        # outline color. Using a filled polygon ensures the arrowhead remains
        # visible regardless of the canvas background color.
        self.canvas.create_polygon(
            end,
            p1,
            p2,
            fill="white",
            outline=color,
            width=width,
            tags=tags,
        )

    def _draw_line_arrow(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        color: str = "black",
        width: int = 1,
        tags: str = "connection",
    ) -> None:
        """Draw an open arrow using only line segments.

        The arrow head is composed of two lines so that the center line of
        the connection meets the arrow tip directly, providing a cleaner
        look for port direction indicators.
        """
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.hypot(dx, dy)
        if length == 0:
            return
        # Use a slightly smaller arrow head so the direction indicator
        # fits nicely on the tiny port square.
        size = 6 * self.zoom
        angle = math.atan2(dy, dx)
        spread = math.radians(20)
        p1 = (
            end[0] - size * math.cos(angle - spread),
            end[1] - size * math.sin(angle - spread),
        )
        p2 = (
            end[0] - size * math.cos(angle + spread),
            end[1] - size * math.sin(angle + spread),
        )
        self.canvas.create_line(
            end[0],
            end[1],
            p1[0],
            p1[1],
            fill=color,
            width=width,
            tags=tags,
        )
        self.canvas.create_line(
            end[0],
            end[1],
            p2[0],
            p2[1],
            fill=color,
            width=width,
            tags=tags,
        )

    def _draw_line_arrow(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        color: str = "black",
        width: int = 1,
        tags: str = "connection",
    ) -> None:
        """Draw an open arrow using only line segments.

        The arrow head is composed of two lines so that the center line of
        the connection meets the arrow tip directly, providing a cleaner
        look for port direction indicators.
        """
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.hypot(dx, dy)
        if length == 0:
            return
        # Use a tiny arrow head so the indicator does not dwarf the port.
        size = 3 * self.zoom
        angle = math.atan2(dy, dx)
        spread = math.radians(20)
        p1 = (
            end[0] - size * math.cos(angle - spread),
            end[1] - size * math.sin(angle - spread),
        )
        p2 = (
            end[0] - size * math.cos(angle + spread),
            end[1] - size * math.sin(angle + spread),
        )
        self.canvas.create_line(
            end[0],
            end[1],
            p1[0],
            p1[1],
            fill=color,
            width=width,
            tags=tags,
        )
        self.canvas.create_line(
            end[0],
            end[1],
            p2[0],
            p2[1],
            fill=color,
            width=width,
            tags=tags,
        )

    def _draw_filled_arrow(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        color: str = "black",
        width: int = 1,
        tags: str = "connection",
    ) -> None:
        """Draw a filled triangular arrow from *start* to *end*."""
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.hypot(dx, dy)
        if length == 0:
            return
        size = 10 * self.zoom
        angle = math.atan2(dy, dx)
        spread = math.radians(20)
        p1 = (
            end[0] - size * math.cos(angle - spread),
            end[1] - size * math.sin(angle - spread),
        )
        p2 = (
            end[0] - size * math.cos(angle + spread),
            end[1] - size * math.sin(angle + spread),
        )
        self.canvas.create_polygon(
            end,
            p1,
            p2,
            fill=color,
            outline=color,
            width=width,
            tags=tags,
        )

    def _draw_open_diamond(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        color: str = "black",
        width: int = 1,
        tags: str = "connection",
    ) -> None:
        """Draw an open diamond from *start* to *end*."""
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.hypot(dx, dy)
        if length == 0:
            return
        size = 10 * self.zoom
        angle = math.atan2(dy, dx)
        p1 = (
            end[0] - size * math.cos(angle),
            end[1] - size * math.sin(angle),
        )
        p2 = (
            p1[0] - size * math.sin(angle) / 2,
            p1[1] + size * math.cos(angle) / 2,
        )
        p3 = (
            end[0] - 2 * size * math.cos(angle),
            end[1] - 2 * size * math.sin(angle),
        )
        p4 = (
            p1[0] + size * math.sin(angle) / 2,
            p1[1] - size * math.cos(angle) / 2,
        )
        self.canvas.create_polygon(
            end,
            p2,
            p3,
            p4,
            fill=self.canvas.cget("background"),
            outline=color,
            width=width,
            tags=tags,
        )

    def _draw_filled_diamond(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        color: str = "black",
        width: int = 1,
        tags: str = "connection",
    ) -> None:
        """Draw a filled diamond from *start* to *end*."""
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.hypot(dx, dy)
        if length == 0:
            return
        size = 10 * self.zoom
        angle = math.atan2(dy, dx)
        p1 = (
            end[0] - size * math.cos(angle),
            end[1] - size * math.sin(angle),
        )
        p2 = (
            p1[0] - size * math.sin(angle) / 2,
            p1[1] + size * math.cos(angle) / 2,
        )
        p3 = (
            end[0] - 2 * size * math.cos(angle),
            end[1] - 2 * size * math.sin(angle),
        )
        p4 = (
            p1[0] + size * math.sin(angle) / 2,
            p1[1] - size * math.cos(angle) / 2,
        )
        self.canvas.create_polygon(
            end,
            p2,
            p3,
            p4,
            fill=color,
            outline=color,
            width=width,
            tags=tags,
        )

    def _draw_center_triangle(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        color: str = "black",
        width: int = 1,
        tags: str = "connection",
    ) -> None:
        """Draw a small triangular arrow pointing from *start* to *end*.

        The triangle is centered on the line segment defined by the start
        and end points and scales with the current zoom level.
        """
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.hypot(dx, dy)
        if length == 0:
            return
        mx = (start[0] + end[0]) / 2
        my = (start[1] + end[1]) / 2
        # Slightly enlarge the arrowhead to make flow direction clearer
        size = 10 * self.zoom
        angle = math.atan2(dy, dx)
        spread = math.radians(20)
        p1 = (mx, my)
        p2 = (
            mx - size * math.cos(angle - spread),
            my - size * math.sin(angle - spread),
        )
        p3 = (
            mx - size * math.cos(angle + spread),
            my - size * math.sin(angle + spread),
        )
        self.canvas.create_polygon(
            p1,
            p2,
            p3,
            fill=color,
            outline=color,
            width=width,
            tags=tags,
        )

    def _draw_subdiagram_marker(self, right: float, bottom: float) -> None:
        """Draw a small indicator showing a linked lower level diagram."""

        size = 8 * self.zoom
        pad = 2 * self.zoom
        x1 = right - size - pad
        y1 = bottom - size - pad
        x2 = right - pad
        y2 = bottom - pad
        self.canvas.create_rectangle(
            x1,
            y1,
            x2,
            y2,
            outline=StyleManager.get_instance().outline_color,
            fill="white",
        )
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        self.canvas.create_text(
            cx,
            cy,
            text="∞",
            font=("Arial", int(6 * self.zoom)),
            fill="black",
        )

    def _draw_car(
        self,
        cx: float,
        cy: float,
        w: float,
        h: float,
        color: str,
        outline: str,
    ) -> None:
        """Draw a simple car silhouette centered at (*cx*, *cy*)."""
        body_bottom = cy + h * 0.3
        body_top = cy - h * 0.1
        roof_rear_y = cy - h * 0.5
        roof_front_y = cy - h * 0.3
        roof_front_x = cx - w * 0.6
        roof_rear_x = cx + w * 0.3
        pts = [
            (cx - w, body_bottom),
            (cx + w, body_bottom),
            (cx + w, body_top),
            (roof_rear_x, roof_rear_y),
            (roof_front_x, roof_front_y),
            (cx - w, body_top),
        ]
        self.drawing_helper._fill_gradient_polygon(self.canvas, pts, color)
        self.canvas.create_polygon(
            [c for pt in pts for c in pt],
            outline=outline,
            fill="",
        )
        wheel_r = min(w, h) * 0.2
        wheel_y = body_bottom
        wheel_offset = w * 0.6
        self.canvas.create_oval(
            cx - wheel_offset - wheel_r,
            wheel_y - wheel_r,
            cx - wheel_offset + wheel_r,
            wheel_y + wheel_r,
            outline=outline,
            fill=outline,
        )
        self.canvas.create_oval(
            cx + wheel_offset - wheel_r,
            wheel_y - wheel_r,
            cx + wheel_offset + wheel_r,
            wheel_y + wheel_r,
            outline=outline,
            fill=outline,
        )

    def _draw_icon_shape(
        self, shape: str, x: float, y: float, r: float, color: str
    ) -> None:
        """Draw *shape* centered at ``(x, y)`` with radius *r* using the icon image."""
        size = max(1, int(r * 2))
        cache = getattr(self, "_scaled_icons", {})
        key = (shape, color, size)
        icon = cache.get(key)
        if icon is None:
            base = draw_icon(shape, color)
            if size != 16:
                icon = base.zoom(size, size).subsample(16, 16)
            else:
                icon = base
            cache[key] = icon
            self._scaled_icons = cache
        self.canvas.create_image(
            x - size / 2, y - size / 2, anchor="nw", image=icon
        )

    def _draw_gear(
        self, x: float, y: float, r: float, color: str, outline: str
    ) -> None:
        """Draw a gear centered at (*x*, *y*) with radius *r*."""
        pts: list[tuple[float, float]] = []
        teeth = 8
        for i in range(teeth * 2):
            angle = math.radians(360 / (teeth * 2) * i)
            rad = r if i % 2 == 0 else r * 0.7
            px = x + rad * math.cos(angle)
            py = y + rad * math.sin(angle)
            pts.append((px, py))
        self.drawing_helper._fill_gradient_polygon(self.canvas, pts, color)
        self.canvas.create_polygon(
            [coord for pt in pts for coord in pt], outline=outline, fill=""
        )
        hole = r * 0.4
        self.canvas.create_oval(
            x - hole,
            y - hole,
            x + hole,
            y + hole,
            outline=outline,
            fill=StyleManager.get_instance().get_canvas_color(),
        )

    def _draw_wrench(
        self, x: float, y: float, r: float, color: str, outline: str
    ) -> None:
        """Draw a wrench centered at (*x*, *y*) with radius *r*.

        The 16×16 pixel icon from :mod:`gui.utils.icon_factory` serves as the template
        but the head is rendered as a squared polygon and the entire wrench is
        drawn using polygon primitives to avoid overlapping shapes.
        """
        size = 16
        mid = size / 2
        bg = StyleManager.get_instance().get_canvas_color()

        # --- Gear ring -------------------------------------------------
        pts: list[tuple[float, float]] = []
        teeth = 8
        for i in range(teeth * 2):
            angle = math.radians(360 / (teeth * 2) * i)
            rad = r if i % 2 == 0 else r * 0.82
            px = x + rad * math.cos(angle)
            py = y + rad * math.sin(angle)
            pts.append((px, py))
        self.drawing_helper._fill_gradient_polygon(self.canvas, pts, color)
        self.canvas.create_polygon(
            [coord for pt in pts for coord in pt], outline=outline, fill=""
        )
        hole_r = r * 0.62
        self.canvas.create_oval(
            x - hole_r,
            y - hole_r,
            x + hole_r,
            y + hole_r,
            outline="",
            fill=bg,
        )

        # --- Wrench inside the gear -----------------------------------
        wr = hole_r * 0.95
        scale = (2 * wr) / size
        head_cy = 5
        head_r = 5
        inner = head_r - 2
        notch_start = mid + 1

        def _pt(px: float, py: float) -> tuple[float, float]:
            return x - wr + px * scale, y - wr + py * scale

        outer = [
            _pt(mid - 1, size - 2),  # bottom-left of handle
            _pt(mid - 1, head_cy + head_r),
            _pt(mid - head_r, head_cy + head_r),
            _pt(mid - head_r, head_cy - head_r),
            _pt(mid + head_r, head_cy - head_r),
            _pt(notch_start, head_cy - 1),
            _pt(notch_start, head_cy + 1),
            _pt(mid + head_r, head_cy + head_r),
            _pt(mid + 1, head_cy + head_r),
            _pt(mid + 1, size - 2),
        ]
        hole = [
            _pt(mid - inner, head_cy + inner),
            _pt(mid - inner, head_cy - inner),
            _pt(mid + inner, head_cy - inner),
            _pt(notch_start, head_cy - 1),
            _pt(notch_start, head_cy + 1),
            _pt(mid + inner, head_cy + inner),
        ]
        theta = -math.pi / 4
        ct, st = math.cos(theta), math.sin(theta)

        def _rot(pt: tuple[float, float]) -> tuple[float, float]:
            px, py = pt
            dx, dy = px - x, py - y
            return x + dx * ct - dy * st, y + dx * st + dy * ct

        outer = [_rot(p) for p in outer]
        hole = [_rot(p) for p in hole]

        self.drawing_helper._fill_gradient_polygon(self.canvas, outer, color)
        self.canvas.create_polygon(
            [coord for pt in outer for coord in pt], outline=outline, fill=""
        )
        self.canvas.create_polygon(
            [coord for pt in hole for coord in pt], fill=bg, outline=""
        )

    def draw_object(self, obj: SysMLObject):
        x = obj.x * self.zoom
        y = obj.y * self.zoom
        w = obj.width * self.zoom / 2
        h = obj.height * self.zoom / 2
        color = StyleManager.get_instance().get_color(obj.obj_type)
        outline = StyleManager.get_instance().outline_color
        if color == "#FFFFFF":
            if obj.obj_type == "AI Database":
                color = "#cfe2f3"
            elif obj.obj_type == "ANN":
                color = "#d5e8d4"
            elif obj.obj_type == "Data acquisition":
                color = "#ffe6cc"
            elif obj.obj_type == "Process":
                color = "#e6f2ff"
            elif obj.obj_type == "Activity":
                color = "#fff2cc"
            elif obj.obj_type == "Task":
                color = "#d9ead3"
            elif obj.obj_type == "Operation":
                color = "#ead1dc"
            elif obj.obj_type == "Driving Function":
                color = "#d0e0e3"
            elif obj.obj_type in ("Software Component", "Component"):
                color = "#fff2cc"
            elif obj.obj_type == "Test Suite":
                color = "#f4cccc"
            elif obj.obj_type == "System":
                color = "#c9daf8"
            elif obj.obj_type == "Plan":
                color = "#f9cb9c"
            elif obj.obj_type == "Manufacturing Process":
                color = "#b4a7d6"
            elif obj.obj_type == "Vehicle":
                color = "#a2c4c9"
            elif obj.obj_type == "Fleet":
                color = "#a4c2f4"
            elif obj.obj_type == "Safety Compliance":
                color = "#cfe2f3"
            elif obj.obj_type == "Incident":
                color = "#f4cccc"
            elif obj.obj_type == "Safety Issue":
                color = "#fce5cd"
            elif obj.obj_type == "Field Data":
                color = "#e2f0d9"
            elif obj.obj_type == "Model":
                color = "#d9d2e9"
        if obj.obj_type == "Actor":
            sx = obj.width / 80.0 * self.zoom
            sy = obj.height / 40.0 * self.zoom
            self.canvas.create_oval(
                x - 10 * sx,
                y - 30 * sy,
                x + 10 * sx,
                y - 10 * sy,
                outline=outline,
                fill=color,
            )
            self.canvas.create_line(x, y - 10 * sy, x, y + 20 * sy, fill=outline)
            self.canvas.create_line(x - 15 * sx, y, x + 15 * sx, y, fill=outline)
            self.canvas.create_line(
                x,
                y + 20 * sy,
                x - 10 * sx,
                y + 40 * sy,
                fill=outline,
            )
            self.canvas.create_line(
                x,
                y + 20 * sy,
                x + 10 * sx,
                y + 40 * sy,
                fill=outline,
            )
        elif obj.obj_type == "Role":
            sx = obj.width / 80.0 * self.zoom
            sy = obj.height / 40.0 * self.zoom
            self.canvas.create_oval(
                x - 10 * sx,
                y - 30 * sy,
                x + 10 * sx,
                y - 10 * sy,
                outline=outline,
                fill=color,
            )
            self.canvas.create_line(x, y - 10 * sy, x, y + 20 * sy, fill=outline)
            self.canvas.create_line(x - 15 * sx, y, x + 15 * sx, y, fill=outline)
            self.canvas.create_line(
                x,
                y + 20 * sy,
                x - 10 * sx,
                y + 40 * sy,
                fill=outline,
            )
            self.canvas.create_line(
                x,
                y + 20 * sy,
                x + 10 * sx,
                y + 40 * sy,
                fill=outline,
            )
        elif obj.obj_type == "Business Unit":
            # Building with a small flag on top to denote a unit
            self._draw_gradient_rect(x - w, y - h, x + w, y + h, color, obj.obj_id)
            self.canvas.create_rectangle(
                x - w,
                y - h,
                x + w,
                y + h,
                outline=outline,
                fill="",
            )
            # simple windows
            win_w = w * 0.4
            win_h = h * 0.3
            for dx in (-w * 0.6, 0):
                self.canvas.create_rectangle(
                    x + dx,
                    y - h * 0.2,
                    x + dx + win_w,
                    y + h * 0.1,
                    fill=StyleManager.get_instance().get_canvas_color(),
                    outline=outline,
                )
            # flag
            pole_x = x + w * 0.3
            pole_top = y - h - h * 0.6
            self.canvas.create_line(
                pole_x,
                y - h,
                pole_x,
                pole_top,
                fill=outline,
                width=max(2, self.zoom),
            )
            self.canvas.create_polygon(
                pole_x,
                pole_top,
                pole_x + w * 0.4,
                pole_top + h * 0.2,
                pole_x,
                pole_top + h * 0.4,
                fill=outline,
                outline=outline,
            )
        elif obj.obj_type in ("Data", "Field Data", "AI Database"):
            self._draw_cylinder(x - w, y - h, x + w, y + h, color, outline, obj.obj_id)
            if obj.obj_type == "AI Database":
                label = obj.properties.get("name", obj.obj_type)
                self.canvas.create_text(
                    x,
                    y + h + 20 * self.zoom,
                    text=label,
                    font=self.font,
                )
        elif obj.obj_type == "Document":
            self._draw_gradient_rect(x - w, y - h, x + w, y + h, color, obj.obj_id)
            self.canvas.create_rectangle(
                x - w,
                y - h,
                x + w,
                y + h,
                outline=outline,
                fill="",
            )
            fold = 10 * self.zoom
            self.canvas.create_polygon(
                x + w - fold,
                y - h,
                x + w,
                y - h,
                x + w,
                y - h + fold,
                fill=StyleManager.get_instance().get_canvas_color(),
                outline=outline,
            )
        elif obj.obj_type == "Guideline":
            r = min(w, h)
            self.drawing_helper._fill_gradient_circle(self.canvas, x, y, r, color)
            self.canvas.create_oval(
                x - r,
                y - r,
                x + r,
                y + r,
                outline=outline,
                fill="",
            )
            self.canvas.create_line(
                x,
                y,
                x,
                y - r,
                fill=outline,
                width=max(2, self.zoom),
            )
            self.canvas.create_polygon(
                x,
                y - r,
                x + r * 0.3,
                y - r * 0.3,
                x - r * 0.3,
                y - r * 0.3,
                fill=outline,
                outline=outline,
            )
        elif obj.obj_type == "Metric":
            # Bar chart with three bars
            bar_w = w * 0.4
            spacing = w * 0.1
            heights = [h * 0.6, h * 0.9, h * 0.4]
            for i, bh in enumerate(heights):
                bx1 = x - w + i * (bar_w + spacing)
                bx2 = bx1 + bar_w
                by2 = y + h
                by1 = by2 - bh
                self._draw_gradient_rect(bx1, by1, bx2, by2, color, obj.obj_id)
                self.canvas.create_rectangle(
                    bx1,
                    by1,
                    bx2,
                    by2,
                    outline=outline,
                    fill="",
                )
        elif obj.obj_type == "Organization":
            # Office building with windows
            self._draw_gradient_rect(x - w, y - h, x + w, y + h, color, obj.obj_id)
            self.canvas.create_rectangle(
                x - w,
                y - h,
                x + w,
                y + h,
                outline=outline,
                fill="",
            )
            cols, rows = 3, 2
            win_w = (2 * w * 0.6) / cols
            win_h = (2 * h * 0.6) / rows
            start_x = x - w + w * 0.2
            start_y = y - h + h * 0.2
            for i in range(cols):
                for j in range(rows):
                    wx1 = start_x + i * win_w
                    wy1 = start_y + j * win_h
                    wx2 = wx1 + win_w * 0.7
                    wy2 = wy1 + win_h * 0.7
                    self.canvas.create_rectangle(
                        wx1,
                        wy1,
                        wx2,
                        wy2,
                        fill=StyleManager.get_instance().get_canvas_color(),
                        outline=outline,
                    )
        elif obj.obj_type == "Policy":
            # Scroll with rolled ends
            roll_r = min(w, h) * 0.3
            body_left = x - w + roll_r
            body_right = x + w - roll_r
            self._draw_gradient_rect(body_left, y - h, body_right, y + h, color, obj.obj_id)
            self.canvas.create_rectangle(
                body_left,
                y - h,
                body_right,
                y + h,
                outline=outline,
                fill="",
            )
            self.canvas.create_oval(
                x - w,
                y - h,
                x - w + 2 * roll_r,
                y + h,
                outline=outline,
                fill=color,
            )
            self.canvas.create_oval(
                x + w - 2 * roll_r,
                y - h,
                x + w,
                y + h,
                outline=outline,
                fill=color,
            )
        elif obj.obj_type == "Principle":
            # Scales of justice
            self.canvas.create_line(x, y - h, x, y + h, fill=outline, width=max(2, self.zoom))
            self.canvas.create_line(x - w * 0.8, y - h * 0.3, x + w * 0.8, y - h * 0.3, fill=outline, width=max(2, self.zoom))
            self.canvas.create_line(x - w * 0.4, y - h * 0.3, x - w * 0.6, y + h * 0.4, fill=outline)
            self.canvas.create_line(x - w * 0.4, y - h * 0.3, x - w * 0.2, y + h * 0.4, fill=outline)
            self.canvas.create_oval(x - w * 0.7, y + h * 0.4, x - w * 0.3, y + h * 0.8, fill=color, outline=outline)
            self.canvas.create_line(x + w * 0.4, y - h * 0.3, x + w * 0.2, y + h * 0.4, fill=outline)
            self.canvas.create_line(x + w * 0.4, y - h * 0.3, x + w * 0.6, y + h * 0.4, fill=outline)
            self.canvas.create_oval(x + w * 0.3, y + h * 0.4, x + w * 0.7, y + h * 0.8, fill=color, outline=outline)
        elif obj.obj_type == "Procedure":
            offset = w * 0.3
            pts = [
                (x - w + offset, y - h),
                (x + w, y - h),
                (x + w - offset, y + h),
                (x - w, y + h),
            ]
            self.drawing_helper._fill_gradient_polygon(self.canvas, pts, color)
            self.canvas.create_polygon(
                [c for pt in pts for c in pt], outline=outline, fill=""
            )
        elif obj.obj_type == "Record":
            self._draw_gradient_rect(x - w, y - h, x + w, y + h, color, obj.obj_id)
            self.canvas.create_rectangle(
                x - w,
                y - h,
                x + w,
                y + h,
                outline=outline,
                fill="",
            )
            tab_h = min(15 * self.zoom, h)
            tab_w = w * 0.4
            self.canvas.create_rectangle(
                x - w,
                y - h,
                x - w + tab_w,
                y - h + tab_h,
                outline=outline,
                fill=StyleManager.get_instance().get_canvas_color(),
            )
        elif obj.obj_type == "Standard":
            r = min(w, h) * 0.6
            cy = y - h * 0.2
            self.drawing_helper._fill_gradient_circle(self.canvas, x, cy, r, color)
            self.canvas.create_oval(x - r, cy - r, x + r, cy + r, outline=outline, fill="")
            self.canvas.create_polygon(
                x - r, cy + r * 0.2, x - r * 0.2, y + h, x, cy + r * 0.2,
                fill=color, outline=outline
            )
            self.canvas.create_polygon(
                x + r, cy + r * 0.2, x + r * 0.2, y + h, x, cy + r * 0.2,
                fill=color, outline=outline
            )
            label_font = tkFont.Font(font=self.font)
            label_font.configure(weight="bold")
            self.canvas.create_text(
                x,
                cy - r - 5 * self.zoom,
                text="ISO/IEEE/IEC",
                font=label_font,
                anchor="s",
            )
        elif obj.obj_type in (
            "Process",
            "Manufacturing Process",
        ):
            r = min(w, h)
            self._draw_gear(x, y, r, color, outline)
        elif obj.obj_type == "Operation":
            r = min(w, h)
            self._draw_wrench(x, y, r, color, outline)
        elif obj.obj_type == "Activity":
            self._draw_gradient_rect(x - w, y - h, x + w, y + h, color, obj.obj_id)
            self._create_round_rect(
                x - w,
                y - h,
                x + w,
                y + h,
                radius=12 * self.zoom,
                outline=outline,
                fill="",
            )
        elif obj.obj_type == "Task":
            offset = w * 0.3
            pts = [
                (x - w + offset, y - h),
                (x + w - offset, y - h),
                (x + w, y + h),
                (x - w, y + h),
            ]
            self.drawing_helper._fill_gradient_polygon(self.canvas, pts, color)
            self.canvas.create_polygon(
                [c for pt in pts for c in pt], outline=outline, fill=""
            )
        elif obj.obj_type == "Driving Function":
            r = min(w, h)
            self.drawing_helper._fill_gradient_circle(self.canvas, x, y, r, color)
            self.canvas.create_oval(x - r, y - r, x + r, y + r, outline=outline, fill="")
            inner = r * 0.4
            self.canvas.create_oval(x - inner, y - inner, x + inner, y + inner, outline=outline, fill=StyleManager.get_instance().get_canvas_color())
            self.canvas.create_line(x - r, y, x + r, y, fill=outline, width=max(2, self.zoom))
            self.canvas.create_line(x, y - r, x, y + r, fill=outline, width=max(2, self.zoom))
        elif obj.obj_type in ("Software Component", "Component"):
            self._draw_gradient_rect(x - w, y - h, x + w, y + h, color, obj.obj_id)
            self.canvas.create_rectangle(
                x - w,
                y - h,
                x + w,
                y + h,
                outline=outline,
                fill="",
            )
            side = w * 0.4
            comp_h = h * 0.4
            self.canvas.create_rectangle(
                x - w - side * 0.1,
                y - h + comp_h * 0.2,
                x - w + side,
                y - h + comp_h * 1.2,
                outline=outline,
                fill=StyleManager.get_instance().get_canvas_color(),
            )
            self.canvas.create_rectangle(
                x - w - side * 0.1,
                y + h - comp_h * 1.2,
                x - w + side,
                y + h - comp_h * 0.2,
                outline=outline,
                fill=StyleManager.get_instance().get_canvas_color(),
            )
        elif obj.obj_type == "Test Suite":
            self._draw_gradient_rect(x - w, y - h, x + w, y + h, color, obj.obj_id)
            self.canvas.create_rectangle(
                x - w,
                y - h,
                x + w,
                y + h,
                outline=outline,
                fill="",
            )
            self.canvas.create_line(x - w, y, x + w, y, fill=outline)
            self.canvas.create_line(x, y - h, x, y + h, fill=outline)
            label = obj.properties.get("name", obj.obj_type)
            self.canvas.create_text(
                x, y + h + 10 * self.zoom, text=label, font=self.font
            )
        elif obj.obj_type == "System":
            self._draw_gradient_rect(x - w, y - h, x + w, y + h, color, obj.obj_id)
            self.canvas.create_rectangle(
                x - w,
                y - h,
                x + w,
                y + h,
                outline=outline,
                fill="",
            )
            pad = 6 * self.zoom
            self.canvas.create_rectangle(
                x - w + pad,
                y - h + pad,
                x + w - pad,
                y + h - pad,
                outline=outline,
                fill="",
            )
        elif obj.obj_type == "Plan":
            self._draw_gradient_rect(x - w, y - h, x + w, y + h, color, obj.obj_id)
            self.canvas.create_rectangle(
                x - w,
                y - h,
                x + w,
                y + h,
                outline=outline,
                fill="",
            )
            fold = 10 * self.zoom
            self.canvas.create_polygon(
                x + w - fold,
                y - h,
                x + w,
                y - h,
                x + w,
                y - h + fold,
                fill=StyleManager.get_instance().get_canvas_color(),
                outline=outline,
            )
        elif obj.obj_type == "Vehicle":
            self._draw_car(x, y, w, h, color, outline)
        elif obj.obj_type == "Fleet":
            offset = 6 * self.zoom
            self._draw_car(x - offset, y - offset, w, h, color, outline)
            self._draw_car(x + offset, y + offset, w, h, color, outline)
        elif obj.obj_type == "Safety Compliance":
            pts = [
                (x - w * 0.8, y - h * 0.7),
                (x + w * 0.8, y - h * 0.7),
                (x + w * 0.6, y + h * 0.1),
                (x, y + h),
                (x - w * 0.6, y + h * 0.1),
            ]
            self.drawing_helper._fill_gradient_polygon(self.canvas, pts, color)
            self.canvas.create_polygon([c for pt in pts for c in pt], outline=outline, fill="")
            chk_start = (x - w * 0.4, y)
            chk_mid = (x - w * 0.1, y + h * 0.3)
            chk_end = (x + w * 0.5, y - h * 0.2)
            self.canvas.create_line(*chk_start, *chk_mid, fill=outline, width=max(2, self.zoom))
            self.canvas.create_line(*chk_mid, *chk_end, fill=outline, width=max(2, self.zoom))
        elif obj.obj_type == "Incident":
            r = min(obj.width, obj.height) * self.zoom / 2
            pts = []
            for i in range(8):
                angle = math.radians(45 * i)
                radius = r if i % 2 == 0 else r * 0.5
                px = x + radius * math.cos(angle)
                py = y + radius * math.sin(angle)
                pts.append((px, py))
            self.drawing_helper._fill_gradient_polygon(self.canvas, pts, color)
            self.canvas.create_polygon(
                [c for pt in pts for c in pt], outline=outline, fill=""
            )
        elif obj.obj_type == "Safety Issue":
            pts = [(x, y - h), (x + w, y + h), (x - w, y + h)]
            self.drawing_helper._fill_gradient_polygon(self.canvas, pts, color)
            self.canvas.create_polygon(
                [c for pt in pts for c in pt], outline=outline, fill=""
            )
        elif obj.obj_type == "Model":
            self._draw_gradient_rect(x - w, y - h, x + w, y + h, color, obj.obj_id)
            self.canvas.create_rectangle(
                x - w,
                y - h,
                x + w,
                y + h,
                outline=outline,
                fill="",
            )
            off = w * 0.3
            self.canvas.create_rectangle(
                x - w + off,
                y - h + off,
                x + w + off,
                y + h + off,
                outline=outline,
                fill=StyleManager.get_instance().get_canvas_color(),
            )
            self.canvas.create_line(x + w, y - h, x + w + off, y - h + off, fill=outline)
            self.canvas.create_line(x + w, y + h, x + w + off, y + h + off, fill=outline)
            self.canvas.create_line(x - w, y + h, x - w + off, y + h + off, fill=outline)
        elif obj.obj_type == "Hazard":
            # Warning triangle with exclamation mark
            pts = [(x, y - h), (x + w, y + h), (x - w, y + h)]
            self.drawing_helper._fill_gradient_polygon(self.canvas, pts, color)
            self.canvas.create_polygon(
                [c for pt in pts for c in pt], outline=outline, fill=""
            )
            mark_top = y - h * 0.2
            mark_bottom = y + h * 0.5
            self.canvas.create_line(
                x,
                mark_top,
                x,
                mark_bottom,
                fill=outline,
                width=max(2, self.zoom),
            )
            dot_r = max(2, self.zoom * 1.5)
            self.canvas.create_oval(
                x - dot_r / 2,
                mark_bottom + dot_r / 4,
                x + dot_r / 2,
                mark_bottom + dot_r * 1.25,
                fill=outline,
                outline=outline,
            )
        elif obj.obj_type == "Risk Assessment":
            # Clipboard with a check mark
            clip_h = min(10 * self.zoom, h * 0.3)
            board_top = y - h + clip_h
            self._draw_gradient_rect(x - w, board_top, x + w, y + h, color, obj.obj_id)
            self.canvas.create_rectangle(
                x - w,
                board_top,
                x + w,
                y + h,
                outline=outline,
                fill="",
            )
            clip_w = w * 0.6
            self.canvas.create_rectangle(
                x - clip_w,
                y - h,
                x + clip_w,
                board_top,
                outline=outline,
                fill=color,
            )
            chk_start = (x - w * 0.6, y)
            chk_mid = (x - w * 0.2, y + h * 0.4)
            chk_end = (x + w * 0.6, y - h * 0.2)
            self.canvas.create_line(*chk_start, *chk_mid, fill=outline, width=max(2, self.zoom))
            self.canvas.create_line(*chk_mid, *chk_end, fill=outline, width=max(2, self.zoom))
        elif obj.obj_type == "Safety Goal":
            # Shield shape
            pts = [
                (x - w * 0.8, y - h * 0.7),
                (x + w * 0.8, y - h * 0.7),
                (x + w * 0.6, y + h * 0.1),
                (x, y + h),
                (x - w * 0.6, y + h * 0.1),
            ]
            self.drawing_helper._fill_gradient_polygon(self.canvas, pts, color)
            self.canvas.create_polygon(
                [c for pt in pts for c in pt], outline=outline, fill=""
            )
        elif obj.obj_type in (
            "Report",
            "Safety Case",
        ):
            self._draw_gradient_rect(x - w, y - h, x + w, y + h, color, obj.obj_id)
            self.canvas.create_rectangle(
                x - w,
                y - h,
                x + w,
                y + h,
                outline=outline,
                fill="",
            )
            fold = 10 * self.zoom
            self.canvas.create_polygon(
                x + w - fold,
                y - h,
                x + w,
                y - h,
                x + w,
                y - h + fold,
                fill=StyleManager.get_instance().get_canvas_color(),
                outline=outline,
            )
        elif obj.obj_type == "Security Threat":
            # Simple bug silhouette to represent a threat
            body_w = w * 0.6
            body_h = h * 0.6
            self.canvas.create_oval(
                x - body_w,
                y - body_h / 2,
                x + body_w,
                y + body_h / 2,
                fill=color,
                outline=outline,
            )
            head_r = min(w, h) * 0.25
            self.canvas.create_oval(
                x - head_r,
                y - body_h / 2 - head_r * 1.2,
                x + head_r,
                y - body_h / 2 + head_r * 0.2,
                fill=color,
                outline=outline,
            )
            leg_y = [y - body_h / 4, y, y + body_h / 4]
            leg_len = w * 0.9
            for ly in leg_y:
                self.canvas.create_line(x - body_w, ly, x - leg_len, ly, fill=outline)
                self.canvas.create_line(x + body_w, ly, x + leg_len, ly, fill=outline)
            # antennae
            self.canvas.create_line(
                x - head_r * 0.5,
                y - body_h / 2 - head_r * 1.2,
                x - head_r,
                y - body_h / 2 - head_r * 1.8,
                fill=outline,
            )
            self.canvas.create_line(
                x + head_r * 0.5,
                y - body_h / 2 - head_r * 1.2,
                x + head_r,
                y - body_h / 2 - head_r * 1.8,
                fill=outline,
            )
        elif obj.obj_type == "Use Case":
            self.drawing_helper._fill_gradient_oval(
                self.canvas, x, y, w, h, color
            )
            self.canvas.create_oval(
                x - w,
                y - h,
                x + w,
                y + h,
                fill="",
                outline=outline,
            )
        elif obj.obj_type == "System Boundary":
            self._draw_gradient_rect(x - w, y - h, x + w, y + h, color, obj.obj_id)
            self._create_round_rect(
                x - w,
                y - h,
                x + w,
                y + h,
                radius=12 * self.zoom,
                dash=(4, 2),
                outline=outline,
                fill="",
            )
            label = _format_label(self, obj.properties.get("name", ""), obj.phase, obj)
            if label:
                # Wrap and scale the label so it always fits within the boundary box
                avail_w = max(obj.width * self.zoom - 16 * self.zoom, 1)
                avail_h = max(obj.height * self.zoom - 16 * self.zoom, 1)

                try:
                    font = tkFont.Font(font=self.font)
                    char_w = max(font.measure("M"), 1)
                    line_h = max(font.metrics("linespace"), 1)
                except Exception:
                    font = None
                    char_w = 8
                    line_h = 16

                max_chars = max(int(avail_h / char_w), 1)
                max_lines = max(int(avail_w / line_h), 1)

                wrap_width = max_chars
                wrapped = textwrap.fill(label, width=wrap_width)
                lines = wrapped.count("\n") + 1

                # Reduce font size until the wrapped text fits horizontally
                if font is not None:
                    while lines > max_lines and font.cget("size") > 6:
                        font.configure(size=font.cget("size") - 1)
                        char_w = max(font.measure("M"), 1)
                        line_h = max(font.metrics("linespace"), 1)
                        max_chars = max(int(avail_h / char_w), 1)
                        max_lines = max(int(avail_w / line_h), 1)
                        wrap_width = max_chars
                        wrapped = textwrap.fill(label, width=wrap_width)
                        lines = wrapped.count("\n") + 1

                # Truncate wrapped lines if they still exceed available space
                wrapped_lines = wrapped.splitlines()
                if len(wrapped_lines) > max_lines:
                    wrapped_lines = wrapped_lines[:max_lines]
                    wrapped = "\n".join(wrapped_lines)
                    lines = len(wrapped_lines)

                # create a compartment on the left for the vertical title
                label_w = lines * line_h + 16 * self.zoom
                label_w = min(label_w, obj.width * self.zoom)
                cx = x - w + label_w
                self.canvas.create_line(
                    cx,
                    y - h + self.zoom,
                    cx,
                    y + h - self.zoom,
                    fill=outline,
                )

                lx = x - w + label_w / 2
                ly = y + 4 * self.zoom
                self.canvas.create_text(
                    lx,
                    ly,
                    text=wrapped,
                    anchor="center",
                    angle=90,
                    font=font or self.font,
                    justify="center",
                )
        elif obj.obj_type == "Block Boundary":
            self._create_round_rect(
                x - w,
                y - h,
                x + w,
                y + h,
                radius=12 * self.zoom,
                dash=(4, 2),
                outline=outline,
                fill="",
            )
            label = _format_label(self, obj.properties.get("name", ""), obj.phase, obj)
            if label:
                lx = x
                ly = y - h - 4 * self.zoom
                self.canvas.create_text(
                    lx,
                    ly,
                    text=label,
                    anchor="s",
                    font=self.font,
                )
        elif obj.obj_type == "Work Product":
            raw_name = obj.properties.get("name", "")
            label = _format_label(self, raw_name, obj.phase)
            diagram_products = {
                "Architecture Diagram",
                "Safety & Security Concept",
                "Product Goal Specification",
                *REQUIREMENT_WORK_PRODUCTS,
            }
            analysis_products = {
                "HAZOP",
                "STPA",
                "Threat Analysis",
                "FI2TC",
                "TC2FI",
                "Risk Assessment",
                "FTA",
                "FMEA",
                "FMEDA",
            }
            if raw_name in diagram_products:
                color = "#cfe2f3"
            elif raw_name in analysis_products:
                color = "#d5e8d4"
            else:
                color = "#ffffff"
            radius = 8 * self.zoom
            self._draw_gradient_rect(x - w, y - h, x + w, y + h, color, obj.obj_id)
            bg = StyleManager.get_instance().get_canvas_color()
            self.canvas.create_arc(
                x - w,
                y - h,
                x - w + 2 * radius,
                y - h + 2 * radius,
                start=90,
                extent=90,
                fill=bg,
                outline="",
            )
            self.canvas.create_arc(
                x + w - 2 * radius,
                y - h,
                x + w,
                y - h + 2 * radius,
                start=0,
                extent=90,
                fill=bg,
                outline="",
            )
            self.canvas.create_arc(
                x + w - 2 * radius,
                y + h - 2 * radius,
                x + w,
                y + h,
                start=270,
                extent=90,
                fill=bg,
                outline="",
            )
            self.canvas.create_arc(
                x - w,
                y + h - 2 * radius,
                x - w + 2 * radius,
                y + h,
                start=180,
                extent=90,
                fill=bg,
                outline="",
            )
            self._create_round_rect(
                x - w,
                y - h,
                x + w,
                y + h,
                radius=radius,
                outline=outline,
                fill="",
            )
            fold = 10 * self.zoom
            fold_color = "#fdfdfd"
            self.canvas.create_polygon(
                x + w - fold,
                y - h,
                x + w,
                y - h,
                x + w,
                y - h + fold,
                fill=fold_color,
                outline=outline,
            )
            self.canvas.create_line(
                x + w - fold,
                y - h,
                x + w - fold,
                y - h + fold,
                fill=outline,
            )
            if raw_name:
                self.canvas.create_text(
                    x,
                    y,
                    text=raw_name.replace(" ", "\n"),
                    anchor="center",
                    font=self.font,
                    width=obj.width * self.zoom,
                )
        elif obj.obj_type == "Lifecycle Phase":
            color = "#F4D698"
            tab_h = 10 * self.zoom
            tab_w = min(obj.width * self.zoom / 2, 40 * self.zoom)
            body_top = y - h + tab_h
            self._draw_gradient_rect(x - w, body_top, x + w, y + h, color, obj.obj_id)
            self.canvas.create_rectangle(
                x - w,
                body_top,
                x + w,
                y + h,
                outline=outline,
                fill="",
            )
            self.canvas.create_rectangle(
                x - w,
                y - h,
                x - w + tab_w,
                body_top,
                outline=outline,
                fill=color,
            )
            label = _format_label(self, obj.properties.get("name", ""), obj.phase, obj)
            if label:
                self.canvas.create_text(
                    x,
                    y,
                    text=label,
                    anchor="center",
                    font=self.font,
                    width=obj.width * self.zoom,
                )
        elif obj.obj_type == "Existing Element":
            element = self.repo.elements.get(obj.element_id)
            if element:
                color = StyleManager.get_instance().get_color(element.elem_type)
            outline = color
            self._draw_gradient_rect(x - w, y - h, x + w, y + h, color, obj.obj_id)
            self._create_round_rect(
                x - w,
                y - h,
                x + w,
                y + h,
                radius=12 * self.zoom,
                dash=(),
                outline=outline,
                fill="",
            )
            diag = self.repo.diagrams.get(self.diagram_id)
            if not diag or diag.diag_type != "Control Flow Diagram":
                label = _format_label(self, obj.properties.get("name", ""), obj.phase, obj)
                if label:
                    lx = x
                    ly = y - h - 4 * self.zoom
                    self.canvas.create_text(
                        lx,
                        ly,
                        text=label,
                        anchor="s",
                        font=self.font,
                    )
        elif obj.obj_type in ("Action Usage", "Action", "CallBehaviorAction", "Part", "Port"):
            dash = ()
            if obj.obj_type == "Part":
                dash = (4, 2)
            if obj.obj_type == "Port":
                side = obj.properties.get("side", "E")
                sz = 6 * self.zoom
                self._draw_gradient_rect(x - sz, y - sz, x + sz, y + sz, color, obj.obj_id)
                self.canvas.create_rectangle(
                    x - sz,
                    y - sz,
                    x + sz,
                    y + sz,
                    fill="",
                    outline=outline,
                )
                arrow_len = sz * 1.2
                half = arrow_len / 2
                direction = obj.properties.get("direction", "out")

                if side in ("E", "W"):
                    if side == "E":
                        inside = -half
                        outside = half
                    else:
                        inside = half
                        outside = -half
                    if direction == "in":
                        self.canvas.create_line(x + outside, y, x + inside, y)
                        self._draw_line_arrow(
                            (x + outside, y),
                            (x + inside, y),
                            color=outline,
                            tags="connection",
                        )
                    elif direction == "out":
                        self.canvas.create_line(x + inside, y, x + outside, y)
                        self._draw_line_arrow(
                            (x + inside, y),
                            (x + outside, y),
                            color=outline,
                            tags="connection",
                        )
                    else:
                        self.canvas.create_line(x - half, y, x + half, y)
                        self._draw_line_arrow(
                            (x, y),
                            (x + half, y),
                            color=outline,
                            tags="connection",
                        )
                        self._draw_line_arrow(
                            (x, y),
                            (x - half, y),
                            color=outline,
                            tags="connection",
                        )
                else:  # N or S
                    if side == "S":
                        inside = -half
                        outside = half
                    else:
                        inside = half
                        outside = -half
                    if direction == "in":
                        self.canvas.create_line(x, y + outside, x, y + inside)
                        self._draw_line_arrow(
                            (x, y + outside),
                            (x, y + inside),
                            color=outline,
                            tags="connection",
                        )
                    elif direction == "out":
                        self.canvas.create_line(x, y + inside, x, y + outside)
                        self._draw_line_arrow(
                            (x, y + inside),
                            (x, y + outside),
                            color=outline,
                            tags="connection",
                        )
                    else:
                        self.canvas.create_line(x, y - half, x, y + half)
                        self._draw_line_arrow(
                            (x, y),
                            (x, y + half),
                            color=outline,
                            tags="connection",
                        )
                        self._draw_line_arrow(
                            (x, y),
                            (x, y - half),
                            color=outline,
                            tags="connection",
                        )

                lx_off = _parse_float(obj.properties.get("labelX"), 8.0)
                ly_off = _parse_float(obj.properties.get("labelY"), -8.0)
                lx = x + lx_off * self.zoom
                ly = y + ly_off * self.zoom
                port_label = _format_label(
                    self, obj.properties.get("name", ""), obj.phase, obj
                )
                self.canvas.create_text(
                    lx,
                    ly,
                    text=port_label,
                    anchor="center",
                    font=self.font,
                )
            else:
                if obj.obj_type in ("Action Usage", "Action", "CallBehaviorAction"):
                    self._draw_gradient_rect(x - w, y - h, x + w, y + h, color, obj.obj_id)
                    self._create_round_rect(
                        x - w,
                        y - h,
                        x + w,
                        y + h,
                        radius=8 * self.zoom,
                        dash=dash,
                        fill="",
                        outline=outline,
                    )
                else:
                    self._draw_gradient_rect(x - w, y - h, x + w, y + h, color, obj.obj_id)
                    self.canvas.create_rectangle(
                        x - w,
                        y - h,
                        x + w,
                        y + h,
                        dash=dash,
                        fill="",
                        outline=outline,
                    )
        elif obj.obj_type == "Block":
            left, top = x - w, y - h
            right, bottom = x + w, y + h
            self._draw_gradient_rect(left, top, right, bottom, color, obj.obj_id)
            self._create_round_rect(
                left,
                top,
                right,
                bottom,
                radius=6 * self.zoom,
                fill="",
                outline=outline,
            )
            name = _format_label(self, obj.properties.get('name', ''), obj.phase, obj)
            header = f"<<block>> {name}".strip()
            self.canvas.create_line(left, top + 20 * self.zoom, right, top + 20 * self.zoom)
            self.canvas.create_text(
                left + 4 * self.zoom,
                top + 10 * self.zoom,
                text=header,
                anchor="w",
                font=self.font,
            )
            compartments = self._block_compartments(obj)
            cy = top + 20 * self.zoom
            for label, text in compartments:
                lines = text.splitlines() if text else [""]
                collapsed = obj.collapsed.get(label, False)
                self.canvas.create_line(left, cy, right, cy)
                btn_sz = 8 * self.zoom
                bx1 = left + 2 * self.zoom
                by1 = cy + (20 * self.zoom - btn_sz) / 2
                bx2 = bx1 + btn_sz
                by2 = by1 + btn_sz
                self.canvas.create_rectangle(
                    bx1,
                    by1,
                    bx2,
                    by2,
                    outline=StyleManager.get_instance().outline_color,
                    fill="white",
                )
                self.canvas.create_text((bx1 + bx2) / 2, (by1 + by2) / 2, text="-" if not collapsed else "+", font=self.font)
                self.compartment_buttons.append((obj.obj_id, label, (bx1, by1, bx2, by2)))
                tx = bx2 + 2 * self.zoom
                if collapsed:
                    # Only display the compartment title when collapsed rather
                    # than showing the first item's text. This keeps the
                    # collapsed view concise and avoids confusion when the
                    # compartment contains multiple elements.
                    self.canvas.create_text(
                        tx,
                        cy + 10 * self.zoom,
                        text=f"{label}:",
                        anchor="w",
                        font=self.font,
                    )
                    cy += 20 * self.zoom
                else:
                    self.canvas.create_text(
                        tx,
                        cy + 10 * self.zoom,
                        text=f"{label}:",
                        anchor="w",
                        font=self.font,
                    )
                    cy += 20 * self.zoom
                    for line in lines:
                        self.canvas.create_text(
                            left + 4 * self.zoom,
                            cy + 10 * self.zoom,
                            text=line,
                            anchor="w",
                            font=self.font,
                        )
                        cy += 20 * self.zoom
        elif obj.obj_type in ("Initial", "Final"):
            if obj.obj_type == "Initial":
                r = min(obj.width, obj.height) / 2 * self.zoom
                self.canvas.create_oval(x - r, y - r, x + r, y + r, fill="black")
            else:
                r = min(obj.width, obj.height) / 2 * self.zoom
                inner = max(r - 5 * self.zoom, 0)
                self.canvas.create_oval(x - r, y - r, x + r, y + r)
                self.canvas.create_oval(x - inner, y - inner, x + inner, y + inner, fill="black")
        elif obj.obj_type in ("Decision", "Merge"):
                self.canvas.create_polygon(
                    x,
                    y - h,
                    x + w,
                    y,
                    x,
                    y + h,
                    x - w,
                    y,
                    fill=color,
                    outline=outline,
                )
        elif obj.obj_type == "ANN":
            # Draw three layers of neurons connected
            layers = [3, 6, 2]
            spacing_x = obj.width * self.zoom / (len(layers) - 1)
            max_neurons = max(layers)
            spacing_y = obj.height * self.zoom / (max_neurons - 1 if max_neurons > 1 else 1)
            layer_x = x - obj.width * self.zoom / 2

            # Calculate neuron positions for each layer without drawing
            neuron_positions: list[list[tuple[float, float]]] = []
            for count in layers:
                xs = layer_x
                ys = y - ((count - 1) * spacing_y) / 2
                positions = []
                for i in range(count):
                    cx = xs
                    cy = ys + i * spacing_y
                    positions.append((cx, cy))
                neuron_positions.append(positions)
                layer_x += spacing_x

            # Draw connections first so they appear behind the neuron nodes
            for i in range(len(neuron_positions) - 1):
                for src in neuron_positions[i]:
                    for dst in neuron_positions[i + 1]:
                        self.canvas.create_line(src[0], src[1], dst[0], dst[1], fill=outline)

            # Now draw the neuron nodes on top of the connections
            for layer in neuron_positions:
                for cx, cy in layer:
                    r = 5 * self.zoom
                    fta_drawing_helper._fill_gradient_circle(self.canvas, cx, cy, r, color)
                    self.canvas.create_oval(
                        cx - r,
                        cy - r,
                        cx + r,
                        cy + r,
                        outline=outline,
                        fill="",
                    )

            label = obj.properties.get("name", obj.obj_type)
            self.canvas.create_text(x, y + h + 10 * self.zoom, text=label, font=self.font)
        elif obj.obj_type == "Data acquisition":
            left, top = x - w, y - h
            right, bottom = x + w, y + h
            self._draw_gradient_rect(left, top, right, bottom, color, obj.obj_id)
            self.canvas.create_rectangle(left, top, right, bottom, outline=outline, fill="")
            compartments = obj.properties.get(
                "compartments", "data source1;data source2;data source 3"
            ).split(";")
            n = max(len(compartments), 1)
            step = (bottom - top) / n
            for idx in range(1, n):
                self.canvas.create_line(left, top + idx * step, right, top + idx * step)
            for idx, text in enumerate(compartments):
                cy = top + idx * step + step / 2
                self.canvas.create_text(x, cy, text=text, font=self.font)
            label = obj.properties.get("name", obj.obj_type)
            self.canvas.create_text(x, bottom + 10 * self.zoom, text=label, font=self.font)
        elif obj.obj_type in ("Fork", "Join"):
            half = obj.width / 2 * self.zoom
            self.canvas.create_rectangle(
                x - half, y - 5 * self.zoom, x + half, y + 5 * self.zoom, fill="black"
            )
        else:
            self._create_round_rect(
                x - w,
                y - h,
                x + w,
                y + h,
                radius=6 * self.zoom,
                fill=color,
                outline=outline,
            )

        if obj.obj_type not in (
            "Block",
            "System Boundary",
            "Block Boundary",
            "Port",
            "Work Product",
            "AI Database",
            "ANN",
            "Data acquisition",
            "Test Suite",
            "Lifecycle Phase",
        ):
            if hasattr(self, "_object_label_lines"):
                label_lines = self._object_label_lines(obj)
            else:
                label_lines = SysMLDiagramWindow._object_label_lines(self, obj)
            if obj.obj_type in ("Actor", "Stakeholder", "Role"):
                sy = obj.height / 40.0 * self.zoom
                label_x = x
                label_y = y + 40 * sy + 10 * self.zoom
                self.canvas.create_text(
                    label_x,
                    label_y,
                    text="\n".join(label_lines),
                    anchor="n",
                    font=self.font,
                )
            elif obj.obj_type in ("Initial", "Final"):
                label_y = y + obj.height / 2 * self.zoom + 10 * self.zoom
                self.canvas.create_text(
                    x,
                    label_y,
                    text="\n".join(label_lines),
                    anchor="n",
                    font=self.font,
                )
            elif obj.obj_type in _BOTTOM_LABEL_TYPES:
                offset = 10 * self.zoom
                if obj.obj_type == "Operation":
                    offset += 10 * self.zoom
                label_y = y + obj.height / 2 * self.zoom + offset
                self.canvas.create_text(
                    x,
                    label_y,
                    text="\n".join(label_lines),
                    anchor="n",
                    font=self.font,
                )
            else:
                self.canvas.create_text(
                    x,
                    y,
                    text="\n".join(label_lines),
                    anchor="center",
                    font=self.font,
                )

        show_marker = False
        if obj.obj_type in ("Block", "Action Usage", "Action", "CallBehaviorAction"):
            diag_id = self.repo.get_linked_diagram(obj.element_id)
            view_id = obj.properties.get("view")
            show_marker = bool(
                (diag_id and diag_id in self.repo.diagrams)
                or (view_id and view_id in self.repo.diagrams)
            )
        if show_marker:
            self._draw_subdiagram_marker(x + w, y + h)

        if obj in self.selected_objs:
            bx = x - w
            by = y - h
            ex = x + w
            ey = y + h
            self.canvas.create_rectangle(bx, by, ex, ey, outline="red", dash=(2, 2))
            if obj == self.selected_obj and obj.obj_type != "Actor":
                s = 4
                for hx, hy in [(bx, by), (bx, ey), (ex, by), (ex, ey)]:
                    self.canvas.create_rectangle(
                        hx - s,
                        hy - s,
                        hx + s,
                        hy + s,
                        outline="red",
                        fill="white",
                    )

    def _label_offset(self, conn: DiagramConnection, diag_type: str | None) -> float:
        """Return a vertical offset for a connection label.

        When multiple connections exist between the same two objects, their
        stereotype labels are offset so they do not overlap. The offset is
        determined by the index of ``conn`` among all labeled connections
        between the object pair.
        """
        pair = {conn.src, conn.dst}
        labeled: list[DiagramConnection] = []
        connections = getattr(self, "connections", [])
        for c in connections:
            if {c.src, c.dst} == pair:
                if format_control_flow_label(c, self.repo, diag_type):
                    labeled.append(c)
        if len(labeled) <= 1:
            return 0.0
        idx = next((i for i, c in enumerate(labeled) if c is conn), 0)
        return (idx - (len(labeled) - 1) / 2) * 15 * self.zoom

    def draw_connection(
        self, a: SysMLObject, b: SysMLObject, conn: DiagramConnection, selected: bool = False
    ):
        axc, ayc = a.x * self.zoom, a.y * self.zoom
        bxc, byc = b.x * self.zoom, b.y * self.zoom
        dash = ()
        diag = self.repo.diagrams.get(self.diagram_id)
        diag_type = diag.diag_type if diag else None
        label = format_control_flow_label(conn, self.repo, diag_type)
        if diag and diag.diag_type == "Control Flow Diagram" and conn.conn_type in ("Control Action", "Feedback"):
            a_left = a.x - a.width / 2
            a_right = a.x + a.width / 2
            b_left = b.x - b.width / 2
            b_right = b.x + b.width / 2
            x_val = (
                conn.points[0][0]
                if conn.points
                else (max(a_left, b_left) + min(a_right, b_right)) / 2
            )
            x_val = SysMLDiagramWindow._constrain_control_flow_x(
                self, conn, x_val
            )
            if conn.points:
                conn.points[0] = (x_val, 0)
            x = x_val * self.zoom
            if ayc <= byc:
                y1 = ayc + a.height / 2 * self.zoom
                y2 = byc - b.height / 2 * self.zoom
            else:
                y1 = ayc - a.height / 2 * self.zoom
                y2 = byc + b.height / 2 * self.zoom
            color = "red" if selected else "black"
            width = 2 if selected else 1
            self.canvas.create_line(
                x,
                y1,
                x,
                y2,
                arrow=tk.LAST,
                dash=(),
                fill=color,
                width=width,
                tags="connection",
            )
            if label:
                offset = (
                    self._label_offset(conn, diag_type)
                    if hasattr(self, "_label_offset")
                    else 0
                )
                self.canvas.create_text(
                    x + offset,
                    (y1 + y2) / 2 - 10 * self.zoom,
                    text=label,
                    font=self.font,
                    tags="connection",
                )
            if selected:
                s = 3
                for hx, hy in [(x, y1), (x, y2), (x, (y1 + y2) / 2)]:
                    self.canvas.create_rectangle(
                        hx - s,
                        hy - s,
                        hx + s,
                        hy + s,
                        outline="red",
                        fill="white",
                        tags="connection",
                    )
            return
        if a.obj_id == b.obj_id:
            ax, ay = self.edge_point(a, 0, 0, (1, 0))
            bx, by = ax, ay
        else:
            ax, ay = self.edge_point(a, bxc, byc, conn.src_pos)
            bx, by = self.edge_point(b, axc, ayc, conn.dst_pos)
        if conn.conn_type in ("Include", "Extend"):
            dash = (4, 2)
            if label and ">> " in label:
                label = label.replace(">> ", ">>\n", 1)
        elif conn.conn_type in ("Generalize", "Generalization", "Communication Path"):
            dash = (2, 2)
        src_flow = a.properties.get("flow") if a.obj_type == "Port" else None
        dst_flow = b.properties.get("flow") if b.obj_type == "Port" else None
        points = [(ax, ay)]
        if a.obj_id == b.obj_id:
            size = max(a.width, a.height) * 0.5 * self.zoom
            points.extend(
                [
                    (ax + size, ay),
                    (ax + size, ay - size),
                    (ax, ay - size),
                ]
            )
        elif conn.style == "Squared":
            if conn.points:
                mx = conn.points[0][0] * self.zoom
            else:
                mx = (ax + bx) / 2
            points.extend([(mx, ay), (mx, by)])
        elif conn.style == "Custom":
            for px, py in conn.points:
                x = px * self.zoom
                y = py * self.zoom
                last = points[-1]
                points.extend([(x, last[1]), (x, y)])
        points.append((bx, by))
        flat = [coord for pt in points for coord in pt]
        color = "red" if selected else "black"
        width = 2 if selected else 1
        arrow_style = tk.NONE
        open_arrow = conn.conn_type in ("Include", "Extend")
        diamond_src = conn.conn_type in ("Aggregation", "Composite Aggregation")
        filled_diamond = conn.conn_type == "Composite Aggregation"
        forward = conn.arrow in ("forward", "both")
        backward = conn.arrow in ("backward", "both")
        mid_forward = forward
        mid_backward = backward
        if conn.conn_type == "Connector" and (src_flow or dst_flow):
            arrow_style = tk.NONE
            conn.mid_arrow = True
            if src_flow and dst_flow:
                dir_a = a.properties.get("direction", "out").lower()
                dir_b = b.properties.get("direction", "out").lower()
                if dir_a == "out":
                    label = src_flow
                    mid_forward, mid_backward = True, False
                elif dir_b == "out":
                    label = dst_flow
                    mid_forward, mid_backward = False, True
                else:
                    label = src_flow
                    mid_forward, mid_backward = True, True
            elif src_flow:
                label = src_flow
                dir_attr = a.properties.get("direction", "out")
                if dir_attr == "in":
                    mid_forward, mid_backward = False, True
                elif dir_attr == "out":
                    mid_forward, mid_backward = True, False
                else:
                    mid_forward, mid_backward = True, True
            else:
                label = dst_flow
                dir_attr = b.properties.get("direction", "out")
                if dir_attr == "in":
                    mid_forward, mid_backward = True, False
                elif dir_attr == "out":
                    mid_forward, mid_backward = False, True
                else:
                    mid_forward, mid_backward = True, True
            label = f"<<{conn.stereotype or conn.conn_type.lower()}>> {label}".strip()
        self.canvas.create_line(
            *flat,
            arrow=arrow_style,
            dash=dash,
            fill=color,
            width=width,
            tags="connection",
        )
        if open_arrow:
            if forward:
                self._draw_open_arrow(
                    points[-2], points[-1], color=color, width=width, tags="connection"
                )
            if backward:
                self._draw_open_arrow(
                    points[1], points[0], color=color, width=width, tags="connection"
                )
        elif conn.conn_type in ("Generalize", "Generalization"):
            # SysML uses an open triangular arrow head for generalization
            # relationships. Use the open arrow drawing helper so the arrow
            # interior matches the canvas background (typically white).
            if forward:
                self._draw_open_arrow(
                    points[-2], points[-1], color=color, width=width, tags="connection"
                )
            if backward:
                self._draw_filled_arrow(
                    points[1], points[0], color=color, width=width, tags="connection"
                )
        elif diamond_src:
            if filled_diamond:
                self._draw_filled_diamond(
                    points[1], points[0], color=color, width=width, tags="connection"
                )
            else:
                self._draw_open_diamond(
                    points[1], points[0], color=color, width=width, tags="connection"
                )
        else:
            if forward:
                self._draw_filled_arrow(
                    points[-2], points[-1], color=color, width=width, tags="connection"
                )
            if backward:
                self._draw_filled_arrow(
                    points[1], points[0], color=color, width=width, tags="connection"
                )
        flow_port = None
        flow_name = ""
        if a.obj_type == "Port" and a.properties.get("flow"):
            flow_port = a
            flow_name = a.properties.get("flow", "")
        elif b.obj_type == "Port" and b.properties.get("flow"):
            flow_port = b
            flow_name = b.properties.get("flow", "")

        if conn.mid_arrow or flow_port:
            mid_idx = len(points) // 2
            if mid_idx > 0:
                mstart = points[mid_idx - 1]
                mend = points[mid_idx]
                if flow_port:
                    direction = flow_port.properties.get("direction", "")
                    if flow_port is b:
                        direction = "in" if direction == "out" else "out" if direction == "in" else direction
                    if direction == "inout":
                        self._draw_center_triangle(
                            mstart, mend, color=color, width=width, tags="connection"
                        )
                        self._draw_center_triangle(
                            mend, mstart, color=color, width=width, tags="connection"
                        )
                    elif direction == "in":
                        self._draw_center_triangle(
                            mend, mstart, color=color, width=width, tags="connection"
                        )
                    else:
                        self._draw_center_triangle(
                            mstart, mend, color=color, width=width, tags="connection"
                        )
                    mx = (mstart[0] + mend[0]) / 2
                    my = (mstart[1] + mend[1]) / 2
                    self.canvas.create_text(
                        mx,
                        my - 10 * self.zoom,
                        text=flow_name,
                        font=self.font,
                        tags="connection",
                    )
                else:
                    if mid_forward or not mid_backward:
                        self._draw_center_triangle(
                            mstart, mend, color=color, width=width, tags="connection"
                        )
                    if mid_backward:
                        self._draw_center_triangle(
                            mend, mstart, color=color, width=width, tags="connection"
                        )
        if selected:
            if conn.style == "Custom":
                for px, py in conn.points:
                    hx = px * self.zoom
                    hy = py * self.zoom
                    s = 3
                    self.canvas.create_rectangle(
                    hx - s,
                    hy - s,
                    hx + s,
                    hy + s,
                    outline="red",
                    fill="white",
                    tags="connection",
                )
            elif conn.style == "Squared":
                if conn.points:
                    mx = conn.points[0][0] * self.zoom
                else:
                    mx = (ax + bx) / 2
                hy = (ay + by) / 2
                s = 3
                self.canvas.create_rectangle(
                    mx - s,
                    hy - s,
                    mx + s,
                    hy + s,
                    outline="red",
                    fill="white",
                    tags="connection",
                )
            elif diag and diag.diag_type == "Governance Diagram" and conn.style == "Straight":
                mx, my = (ax + bx) / 2, (ay + by) / 2
                s = 3
                self.canvas.create_rectangle(
                    mx - s,
                    my - s,
                    mx + s,
                    my + s,
                    outline="red",
                    fill="white",
                    tags="connection",
                )
            # draw endpoint handles
            for hx, hy in [(ax, ay), (bx, by)]:
                s = 3
                self.canvas.create_rectangle(
                    hx - s,
                    hy - s,
                    hx + s,
                    hy + s,
                    outline="red",
                    fill="white",
                    tags="connection",
                )
        if conn.multiplicity and conn.conn_type in ("Aggregation", "Composite Aggregation"):
            end_x, end_y = points[-1]
            prev_x, prev_y = points[-2]
            dx = prev_x - end_x
            dy = prev_y - end_y
            length = math.hypot(dx, dy)
            if length:
                offset = 15 * self.zoom
                mx = end_x + dx / length * offset
                my = end_y + dy / length * offset
            else:
                mx, my = end_x, end_y
            self.canvas.create_text(
                mx,
                my - 10 * self.zoom,
                text=conn.multiplicity,
                font=self.font,
                tags="connection",
            )
        if label:
            mx, my = (ax + bx) / 2, (ay + by) / 2
            offset = (
                self._label_offset(conn, diag_type)
                if hasattr(self, "_label_offset")
                else 0
            )
            if math.isclose(ax, bx):
                self.canvas.create_text(
                    mx + offset,
                    my - 10 * self.zoom,
                    text=label,
                    font=self.font,
                    tags="connection",
                )
            else:
                self.canvas.create_text(
                    mx,
                    my - 10 * self.zoom - offset,
                    text=label,
                    font=self.font,
                    tags="connection",
                )

    def get_object(self, oid: int) -> SysMLObject | None:
        for o in self.objects:
            if o.obj_id == oid:
                return o
        return None

    def get_ibd_boundary(self) -> SysMLObject | None:
        """Return the Block Boundary object if present."""
        for o in self.objects:
            if o.obj_type == "Block Boundary":
                return o
        return None

    def _object_within(self, obj: SysMLObject, boundary: SysMLObject) -> bool:
        left = boundary.x - boundary.width / 2
        right = boundary.x + boundary.width / 2
        top = boundary.y - boundary.height / 2
        bottom = boundary.y + boundary.height / 2
        ox = obj.x
        oy = obj.y
        return left <= ox <= right and top <= oy <= bottom

    def find_boundary_for_obj(self, obj: SysMLObject) -> SysMLObject | None:
        for b in self.objects:
            if b.obj_type == "System Boundary" and self._object_within(obj, b):
                return b
        return None

    def find_boundary_at(self, x: float, y: float) -> SysMLObject | None:
        """Return the process area containing (x, y) if any.

        Coordinates are in diagram space, not canvas pixels.
        """
        for b in reversed(self.objects):
            if b.obj_type != "System Boundary":
                continue
            left = b.x - b.width / 2
            right = b.x + b.width / 2
            top = b.y - b.height / 2
            bottom = b.y + b.height / 2
            if left <= x <= right and top <= y <= bottom:
                return b
        return None

    def _update_drag_selection(self, x: float, y: float) -> None:
        if not self.select_rect_start:
            return
        x0, y0 = self.select_rect_start
        left, right = sorted([x0, x])
        top, bottom = sorted([y0, y])
        selected: list[SysMLObject] = []
        for obj in self.objects:
            ox = obj.x * self.zoom
            oy = obj.y * self.zoom
            w = obj.width * self.zoom / 2
            h = obj.height * self.zoom / 2
            if left <= ox - w and ox + w <= right and top <= oy - h and oy + h <= bottom:
                selected.append(obj)
        self.selected_objs = selected
        self.selected_obj = selected[0] if len(selected) == 1 else None
        self.redraw()
        self.update_property_view()

    # ------------------------------------------------------------
    # Clipboard operations
    # ------------------------------------------------------------
    def _clone_object_strategy1(self, obj: SysMLObject) -> dict | None:
        return asdict(obj)

    def _clone_object_strategy2(self, obj: SysMLObject) -> dict | None:
        try:
            return json.loads(json.dumps(self._clone_object_strategy1(obj)))
        except Exception:
            return None

    def _clone_object_strategy3(self, obj: SysMLObject) -> dict | None:
        try:
            return copy.deepcopy(self._clone_object_strategy1(obj))
        except Exception:
            return None

    def _clone_object_strategy4(self, obj: SysMLObject) -> dict | None:
        return {
            "obj_id": obj.obj_id,
            "obj_type": obj.obj_type,
            "x": obj.x,
            "y": obj.y,
            "element_id": obj.element_id,
            "width": obj.width,
            "height": obj.height,
            "properties": copy.deepcopy(obj.properties),
            "requirements": copy.deepcopy(obj.requirements),
            "locked": obj.locked,
            "hidden": obj.hidden,
            "collapsed": copy.deepcopy(obj.collapsed),
            "phase": obj.phase,
        }

    def _clone_object(self, obj: SysMLObject) -> dict | None:
        for strat in (
            self._clone_object_strategy1,
            self._clone_object_strategy2,
            self._clone_object_strategy3,
            self._clone_object_strategy4,
        ):
            snap = strat(obj)
            if snap:
                return snap
        return None

    def _reconstruct_object_strategy1(self, snap: dict, offset=(20, 20)) -> SysMLObject:
        data = copy.deepcopy(snap)
        data["obj_id"] = _get_next_id()
        data["x"] = data.get("x", 0) + offset[0]
        data["y"] = data.get("y", 0) + offset[1]
        data.setdefault("phase", _repo_phase(self.repo))
        return SysMLObject(**data)

    def _reconstruct_object_strategy2(self, snap: dict, offset=(20, 20)) -> SysMLObject:
        data = json.loads(json.dumps(snap))
        data["obj_id"] = _get_next_id()
        data["x"] = data.get("x", 0) + offset[0]
        data["y"] = data.get("y", 0) + offset[1]
        data.setdefault("phase", _repo_phase(self.repo))
        return SysMLObject(**data)

    def _reconstruct_object_strategy3(self, snap: dict, offset=(20, 20)) -> SysMLObject:
        return SysMLObject(
            obj_id=_get_next_id(),
            obj_type=snap.get("obj_type", "Block"),
            x=snap.get("x", 0) + offset[0],
            y=snap.get("y", 0) + offset[1],
            element_id=snap.get("element_id"),
            width=snap.get("width", 80.0),
            height=snap.get("height", 40.0),
            properties=copy.deepcopy(snap.get("properties", {})),
            requirements=copy.deepcopy(snap.get("requirements", [])),
            locked=snap.get("locked", False),
            hidden=snap.get("hidden", False),
            collapsed=copy.deepcopy(snap.get("collapsed", {})),
            phase=snap.get("phase", _repo_phase(self.repo)),
        )

    def _reconstruct_object_strategy4(self, snap: dict, offset=(20, 20)) -> SysMLObject:
        data = {**snap}
        data.setdefault("width", 80.0)
        data.setdefault("height", 40.0)
        data.setdefault("properties", {})
        data.setdefault("requirements", [])
        data.setdefault("collapsed", {})
        data["obj_id"] = _get_next_id()
        data["x"] = data.get("x", 0) + offset[0]
        data["y"] = data.get("y", 0) + offset[1]
        data.setdefault("phase", _repo_phase(self.repo))
        return SysMLObject(**data)

    def _reconstruct_object(self, snap: dict, offset=(20, 20)) -> SysMLObject | None:
        for strat in (
            self._reconstruct_object_strategy1,
            self._reconstruct_object_strategy2,
            self._reconstruct_object_strategy3,
            self._reconstruct_object_strategy4,
        ):
            try:
                return strat(copy.deepcopy(snap), offset)
            except Exception:
                continue
        return None

    # ------------------------------------------------------------
    def _task_parent_name_strategy1(self, obj: SysMLObject) -> str | None:
        pid = obj.properties.get("parent") or obj.properties.get("boundary")
        if pid:
            parent = self.get_object(int(pid))
            if parent:
                return parent.properties.get("name")
        return None

    def _task_parent_name_strategy2(self, obj: SysMLObject) -> str | None:
        return obj.properties.get("parent_name")

    def _task_parent_name_strategy3(self, obj: SysMLObject) -> str | None:
        return obj.properties.get("boundary_name")

    def _task_parent_name_strategy4(self, obj: SysMLObject) -> str | None:
        return None

    def _task_parent_name(self, obj: SysMLObject) -> str | None:
        for strat in (
            self._task_parent_name_strategy1,
            self._task_parent_name_strategy2,
            self._task_parent_name_strategy3,
            self._task_parent_name_strategy4,
        ):
            name = strat(obj)
            if name:
                return name
        return None

    def _find_or_place_boundary_strategy1(self, name: str, x: float, y: float):
        if (
            self.selected_obj
            and self.selected_obj.obj_type == "System Boundary"
            and self.selected_obj.properties.get("name") == name
        ):
            return self.selected_obj
        return None

    def _find_or_place_boundary_strategy2(self, name: str, x: float, y: float):
        for obj in self.objects:
            if obj.obj_type == "System Boundary" and obj.properties.get("name") == name:
                return obj
        return None

    def _find_or_place_boundary_strategy3(self, name: str, x: float, y: float):
        for obj in self.objects:
            if (
                obj.obj_type == "System Boundary"
                and obj.properties.get("name", "").lower() == name.lower()
            ):
                return obj
        return None

    def _find_or_place_boundary_strategy4(self, name: str, x: float, y: float):
        return self._place_process_area(name, x, y)

    def _find_or_place_boundary(self, name: str, x: float, y: float):
        for strat in (
            self._find_or_place_boundary_strategy1,
            self._find_or_place_boundary_strategy4,
            self._find_or_place_boundary_strategy2,
            self._find_or_place_boundary_strategy3,
        ):
            boundary = strat(name, x, y)
            if boundary:
                return boundary
        return None
    def copy_selected(self, _event=None):
        if self.selected_obj and self.app:
            self.app.active_arch_window = self
            self.app.selected_node = None
            self.app.diagram_clipboard.clipboard_node = None
            self.app.diagram_clipboard.cut_mode = False
            diag = self.repo.diagrams.get(self.diagram_id)
            if self.selected_obj.obj_type == "System Boundary":
                children = [
                    o
                    for o in self.objects
                    if o.obj_type == "Work Product"
                    and o.properties.get("parent") == str(self.selected_obj.obj_id)
                ]
                items = [self.selected_obj, *children]
                self.app.diagram_clipboard.diagram_clipboard = copy.deepcopy(items)
                self.app.diagram_clipboard.diagram_clipboard_parent_name = None
            else:
                snap = self._clone_object(self.selected_obj)
                if not snap:
                    return
                self.app.diagram_clipboard.diagram_clipboard = snap
                parent_name = None
                if self.selected_obj.obj_type in ("Work Product", "Task"):
                    parent_name = self._task_parent_name(self.selected_obj)
                self.app.diagram_clipboard.diagram_clipboard_parent_name = parent_name
            self.app.diagram_clipboard.diagram_clipboard_type = diag.diag_type if diag else None

    def cut_selected(self, _event=None):
        if self.repo.diagram_read_only(self.diagram_id):
            return
        if self.selected_obj and self.app:
            self.app.active_arch_window = self
            self.app.selected_node = None
            self.app.diagram_clipboard.clipboard_node = None
            self.app.diagram_clipboard.cut_mode = True
            diag = self.repo.diagrams.get(self.diagram_id)
            if self.selected_obj.obj_type == "System Boundary":
                children = [
                    o
                    for o in self.objects
                    if o.obj_type == "Work Product"
                    and o.properties.get("parent") == str(self.selected_obj.obj_id)
                ]
                items = [self.selected_obj, *children]
                self.app.diagram_clipboard.diagram_clipboard = copy.deepcopy(items)
                self.app.diagram_clipboard.diagram_clipboard_parent_name = None
                for child in children:
                    self.remove_object(child)
                self.remove_object(self.selected_obj)
            else:
                snap = self._clone_object(self.selected_obj)
                if not snap:
                    return
                self.app.diagram_clipboard.diagram_clipboard = snap
                parent_name = None
                if self.selected_obj.obj_type in ("Work Product", "Task"):
                    parent_name = self._task_parent_name(self.selected_obj)
                self.app.diagram_clipboard.diagram_clipboard_parent_name = parent_name
                self.remove_object(self.selected_obj)
            self.app.diagram_clipboard.diagram_clipboard_type = diag.diag_type if diag else None
            self.selected_obj = None
            self._sync_to_repository()
            self.redraw()
            self.update_property_view()

    def paste_selected(self, _event=None):
        if self.repo.diagram_read_only(self.diagram_id):
            return
        if self.app:
            self.app.active_arch_window = self
        if self.app and getattr(self.app.diagram_clipboard, "diagram_clipboard", None):
            if self.app.diagram_clipboard.diagram_clipboard_type:
                diag = self.repo.diagrams.get(self.diagram_id)
                if diag and diag.diag_type != self.app.diagram_clipboard.diagram_clipboard_type:
                    messagebox.showwarning(
                        "Paste",
                        "Clipboard contains incompatible diagram element.",
                    )
                    return
            import copy

            clip = self.app.diagram_clipboard.diagram_clipboard
            if isinstance(clip, list):
                import copy as _copy

                originals = clip
                copies = _copy.deepcopy(clip)
                old_area_id = originals[0].obj_id
                area = copies[0]
                area.obj_id = _get_next_id()
                area.x += 20
                area.y += 20
                self.objects.insert(0, area)
                diag = self.repo.diagrams.get(self.diagram_id)
                if diag and area.element_id and area.element_id not in diag.elements:
                    diag.elements.append(area.element_id)
                for child in copies[1:]:
                    child.obj_id = _get_next_id()
                    child.x += 20
                    child.y += 20
                    if child.properties.get("parent") == str(old_area_id):
                        child.properties["parent"] = str(area.obj_id)
                    self._constrain_to_parent(child, area)
                    self.objects.append(child)
                    if diag and child.element_id and child.element_id not in diag.elements:
                        diag.elements.append(child.element_id)
                self.sort_objects()
                self.selected_obj = area
            else:
                new_obj = self._reconstruct_object(clip)
                if not new_obj:
                    return
                if (
                    new_obj.obj_type in ("Work Product", "Task")
                    and getattr(self.app.diagram_clipboard, "diagram_clipboard_parent_name", None)
                ):
                    parent_name = self.app.diagram_clipboard.diagram_clipboard_parent_name
                    parent_obj = self._find_or_place_boundary(
                        parent_name, new_obj.x, new_obj.y
                    )
                    if parent_obj:
                        if new_obj.obj_type == "Work Product":
                            new_obj.properties["parent"] = str(parent_obj.obj_id)
                        else:
                            new_obj.properties["boundary"] = str(parent_obj.obj_id)
                        self._constrain_to_parent(new_obj, parent_obj)
                if new_obj.obj_type == "System Boundary":
                    self.objects.insert(0, new_obj)
                else:
                    self.objects.append(new_obj)
                self.sort_objects()
                diag = self.repo.diagrams.get(self.diagram_id)
                if diag and new_obj.element_id and new_obj.element_id not in diag.elements:
                    diag.elements.append(new_obj.element_id)
                self.selected_obj = new_obj
            self._sync_to_repository()
            self.redraw()
            self.update_property_view()

    def _remove_wp_and_disable(self, name: str, wp) -> None:
        toolbox = getattr(self.app, "safety_mgmt_toolbox", None) or ACTIVE_TOOLBOX
        removed = False
        if toolbox:
            diag = self.repo.diagrams.get(self.diagram_id)
            diagram_name = diag.name if diag else ""
            removed = toolbox.remove_work_product(diagram_name, name)
            if not toolbox.is_enabled(name):
                if any(
                    o is not wp
                    and o.obj_type == "Work Product"
                    and o.properties.get("name") == name
                    for o in self.objects
                ):
                    toolbox.add_work_product(diagram_name, name, "")
            if removed and not toolbox.is_enabled(name):
                getattr(self.app, "disable_work_product", lambda *_: None)(name)
        self.remove_element_model(wp)

    def delete_selected(self, _event=None):
        if self.repo.diagram_read_only(self.diagram_id):
            return
        if self.selected_objs:
            confirmed = messagebox.askyesno(
                "Delete", "Delete element permanently?"
            )
            if not confirmed:
                return
            for obj in list(self.selected_objs):
                if obj.obj_type == "System Boundary":
                    wps = [
                        o
                        for o in self.objects
                        if o.obj_type == "Work Product"
                        and (
                            o.properties.get("parent") == str(obj.obj_id)
                            or o.properties.get("boundary") == str(obj.obj_id)
                        )
                    ]
                    for wp in wps:
                        name = wp.properties.get("name", "")
                        if getattr(self.app, "can_remove_work_product", None):
                            if not self.app.can_remove_work_product(name):
                                messagebox.showerror(
                                    "Delete",
                                    f"Cannot delete work product '{name}' with existing artifacts.",
                                )
                                break
                    else:
                        for wp in wps:
                            name = wp.properties.get("name", "")
                            self._remove_wp_and_disable(name, wp)
                        self.remove_element_model(obj)
                    continue
                if obj.obj_type == "Work Product":
                    name = obj.properties.get("name", "")
                    if getattr(self.app, "can_remove_work_product", None):
                        if not self.app.can_remove_work_product(name):
                            messagebox.showerror(
                                "Delete",
                                f"Cannot delete work product '{name}' with existing artifacts.",
                            )
                            continue
                    self._remove_wp_and_disable(name, obj)
                elif obj.obj_type == "System Boundary":
                    children = [
                        o
                        for o in list(self.objects)
                        if o.obj_type == "Work Product"
                        and o.properties.get("parent") == str(obj.obj_id)
                    ]
                    for wp in children:
                        name = wp.properties.get("name", "")
                        if getattr(self.app, "can_remove_work_product", None):
                            if not self.app.can_remove_work_product(name):
                                messagebox.showerror(
                                    "Delete",
                                    f"Cannot delete work product '{name}' with existing artifacts.",
                                )
                                break
                    else:
                        for wp in children:
                            name = wp.properties.get("name", "")
                            self._remove_wp_and_disable(name, wp)
                        self.remove_element_model(obj)
                        continue
                if obj.obj_type == "Part":
                    self.remove_part_model(obj)
                else:
                    self.remove_element_model(obj)
            self.selected_objs = []
            self.selected_obj = None
            if getattr(self.app, "refresh_tool_enablement", None):
                self.app.refresh_tool_enablement()
            return
        if self.selected_conn:
            if self.selected_conn in self.connections:
                src_elem = self.get_object(self.selected_conn.src)
                dst_elem = self.get_object(self.selected_conn.dst)
                if (
                    self.selected_conn.conn_type == "Generalization"
                    and src_elem
                    and dst_elem
                ):
                    msg = (
                        "Removing this inheritance will delete all inherited parts, "
                        "properties and attributes. Continue?"
                    )
                    if not messagebox.askyesno("Remove Inheritance", msg):
                        return
                elif self.selected_conn.conn_type in (
                    "Aggregation",
                    "Composite Aggregation",
                ):
                    msg = "Delete aggregation and its part?"
                    if not messagebox.askyesno("Remove Aggregation", msg):
                        return
                self.connections.remove(self.selected_conn)
                # remove matching repository relationship
                if src_elem and dst_elem and src_elem.element_id and dst_elem.element_id:
                    for rel in list(self.repo.relationships):
                        if (
                            rel.source == src_elem.element_id
                            and rel.target == dst_elem.element_id
                            and rel.rel_type == self.selected_conn.conn_type
                        ):
                            self.repo.relationships.remove(rel)
                            diag = self.repo.diagrams.get(self.diagram_id)
                            if diag and rel.rel_id in diag.relationships:
                                diag.relationships.remove(rel.rel_id)
                            if self.selected_conn.conn_type == "Generalization":
                                remove_inherited_block_properties(
                                    self.repo, src_elem.element_id, dst_elem.element_id
                                )
                                inherit_block_properties(self.repo, src_elem.element_id)
                            elif self.selected_conn.conn_type in ("Aggregation", "Composite Aggregation"):
                                remove_aggregation_part(
                                    self.repo,
                                    src_elem.element_id,
                                    dst_elem.element_id,
                                    remove_object=self.selected_conn.conn_type == "Composite Aggregation",
                                    app=getattr(self, "app", None),
                                )
                            break
                self.selected_conn = None
                self._sync_to_repository()
                self.redraw()
                self.update_property_view()
                if getattr(self.app, "refresh_tool_enablement", None):
                    self.app.refresh_tool_enablement()

    def remove_object(self, obj: SysMLObject) -> None:
        if self.repo.diagram_read_only(self.diagram_id) or getattr(obj, "locked", False):
            return
        removed_ids = {obj.obj_id}
        if obj in self.objects:
            self.objects.remove(obj)
        if obj.obj_type == "Part":
            before = {o.obj_id for o in self.objects}
            remove_orphan_ports(self.objects)
            removed_ids.update(before - {o.obj_id for o in self.objects})
        elif obj.obj_type == "Port":
            remove_port(self.repo, obj, self.objects)
        self.connections = [
            c for c in self.connections if c.src not in removed_ids and c.dst not in removed_ids
        ]
        diag = self.repo.diagrams.get(self.diagram_id)
        if diag and obj.element_id in diag.elements:
            diag.elements.remove(obj.element_id)

        prev_parts = None
        block_id = None
        if obj.obj_type == "Part" and diag:
            block_id = getattr(diag, "father", None) or next(
                (eid for eid, did in self.repo.element_diagrams.items() if did == self.diagram_id),
                None,
            )
            if block_id and block_id in self.repo.elements:
                block = self.repo.elements[block_id]
                prev_parts = block.properties.get("partProperties")

        self._sync_to_repository()

        if prev_parts is not None and block_id and block_id in self.repo.elements:
            block = self.repo.elements[block_id]
            if prev_parts:
                block.properties["partProperties"] = prev_parts
            else:
                block.properties.pop("partProperties", None)
            for d in self.repo.diagrams.values():
                for o in getattr(d, "objects", []):
                    if o.get("element_id") == block_id:
                        if prev_parts:
                            o.setdefault("properties", {})["partProperties"] = prev_parts
                        else:
                            o.setdefault("properties", {}).pop("partProperties", None)

    # ------------------------------------------------------------
    # Part removal helpers
    # ------------------------------------------------------------
    def remove_part_diagram(self, obj: SysMLObject) -> None:
        """Remove *obj* from the current diagram but keep it in the model."""
        if obj.obj_type != "Part":
            return
        obj.hidden = True
        self.selected_obj = None
        self._sync_to_repository()
        self.redraw()
        self.update_property_view()

    def remove_part_model(self, obj: SysMLObject) -> None:
        """Remove *obj* from the repository and all diagrams."""
        if obj.obj_type != "Part":
            return
        self.remove_object(obj)
        part_id = obj.element_id
        repo = self.repo
        # remove from other diagrams
        for diag in repo.diagrams.values():
            diag.objects = [o for o in getattr(diag, "objects", []) if o.get("element_id") != part_id]
            if part_id in getattr(diag, "elements", []):
                diag.elements.remove(part_id)
        # update any open windows
        app = getattr(self, "app", None)
        if app:
            for win in getattr(app, "ibd_windows", []):
                win.objects = [o for o in win.objects if o.element_id != part_id]
                remove_orphan_ports(win.objects)
                win.redraw()
                win._sync_to_repository()
        # update block properties
        diag = repo.diagrams.get(self.diagram_id)
        block_id = getattr(diag, "father", None) or next((eid for eid, did in repo.element_diagrams.items() if did == self.diagram_id), None)
        name = ""
        elem = repo.elements.get(part_id)
        if elem:
            name = elem.name or elem.properties.get("component", "")
            def_id = elem.properties.get("definition")
            if not name and def_id and def_id in repo.elements:
                name = repo.elements[def_id].name or def_id
        if block_id and name and block_id in repo.elements:
            block = repo.elements[block_id]
            parts = [p.strip() for p in block.properties.get("partProperties", "").split(",") if p.strip()]
            parts = [p for p in parts if p.split("[")[0].strip() != name]
            if parts:
                block.properties["partProperties"] = ", ".join(parts)
            else:
                block.properties.pop("partProperties", None)
            for d in repo.diagrams.values():
                for o in getattr(d, "objects", []):
                    if o.get("element_id") == block_id:
                        if parts:
                            o.setdefault("properties", {})["partProperties"] = ", ".join(parts)
                        else:
                            o.setdefault("properties", {}).pop("partProperties", None)
        repo.delete_element(part_id)
        repo._undo_stack.pop()
        self._sync_to_repository()
        self.redraw()
        self.update_property_view()

    def remove_element_model(self, obj: SysMLObject) -> None:
        """Remove *obj* and its element from all diagrams and the repository."""
        elem_id = obj.element_id
        if not elem_id:
            self.remove_object(obj)
            return
        self.remove_object(obj)
        repo = self.repo
        for diag in repo.diagrams.values():
            removed_ids = [o.get("obj_id") for o in getattr(diag, "objects", []) if o.get("element_id") == elem_id]
            if removed_ids:
                diag.objects = [o for o in diag.objects if o.get("element_id") != elem_id]
                diag.connections = [
                    c
                    for c in getattr(diag, "connections", [])
                    if c.get("src") not in removed_ids and c.get("dst") not in removed_ids
                ]
            if elem_id in getattr(diag, "elements", []):
                diag.elements.remove(elem_id)
        # remove part elements that reference this element
        to_delete = [
            eid
            for eid, e in repo.elements.items()
            if e.elem_type == "Part" and e.properties.get("definition") == elem_id
        ]
        for pid in to_delete:
            for diag in repo.diagrams.values():
                removed = [o.get("obj_id") for o in getattr(diag, "objects", []) if o.get("element_id") == pid]
                if removed:
                    diag.objects = [o for o in diag.objects if o.get("element_id") != pid]
                    diag.connections = [
                        c
                        for c in getattr(diag, "connections", [])
                        if c.get("src") not in removed and c.get("dst") not in removed
                    ]
                if pid in getattr(diag, "elements", []):
                    diag.elements.remove(pid)
            repo.delete_element(pid)
            if repo._undo_stack:
                repo._undo_stack.pop()

        repo.delete_element(elem_id)
        if repo._undo_stack:
            repo._undo_stack.pop()

        self._sync_to_repository()
        self.redraw()
        self.update_property_view()

    def _sync_to_repository(self) -> None:
        """Persist current objects and connections back to the repository."""
        self.repo.push_undo_state(sync_app=False)
        undo = getattr(self.app, "push_undo_state", None)
        if undo:
            undo(sync_repo=False)
        diag = self.repo.diagrams.get(self.diagram_id)
        if diag:
            existing_objs = getattr(diag, "objects", [])
            hidden_objs = [
                o for o in existing_objs if not self.repo.object_visible(o, self.diagram_id)
            ]
            diag.objects = hidden_objs + [obj.__dict__ for obj in self.objects]
            existing_conns = getattr(diag, "connections", [])
            hidden_conns = [
                c
                for c in existing_conns
                if not self.repo.connection_visible(c, self.diagram_id)
            ]
            diag.connections = hidden_conns + [conn.__dict__ for conn in self.connections]
            update_block_parts_from_ibd(self.repo, diag)
            self.repo.touch_diagram(self.diagram_id)
            _sync_block_parts_from_ibd(self.repo, self.diagram_id)
            if diag.diag_type == "Internal Block Diagram":
                block_id = (
                    getattr(diag, "father", None)
                    or next(
                        (
                            eid
                            for eid, did in self.repo.element_diagrams.items()
                            if did == self.diagram_id
                        ),
                        None,
                    )
                )
                if block_id:
                    added_mult = _enforce_ibd_multiplicity(
                        self.repo, block_id, app=getattr(self, "app", None)
                    )
                    if added_mult and not getattr(self, "app", None):
                        for data in added_mult:
                            if not any(
                                o.obj_id == data["obj_id"] for o in self.objects
                            ):
                                self.objects.append(SysMLObject(**data))

    def refresh_from_repository(self, _event=None) -> None:
        """Reload diagram objects from the repository and redraw."""
        diag = self.repo.diagrams.get(self.diagram_id)
        if not diag:
            return
        self.objects = []
        for data in self.repo.visible_objects(diag.diag_id):
            if "requirements" not in data:
                data["requirements"] = []
            data.setdefault("phase", _repo_phase(self.repo))
            obj = SysMLObject(**data)
            if obj.obj_type == "Part":
                asil = calculate_allocated_asil(obj.requirements)
                obj.properties.setdefault("asil", asil)
                if obj.element_id and obj.element_id in self.repo.elements:
                    self.repo.elements[obj.element_id].properties.setdefault(
                        "asil", asil
                    )
            if obj.element_id:
                targets = [
                    self.repo.elements[r.target].name
                    for r in self.repo.relationships
                    if r.rel_type == "Trace"
                    and r.source == obj.element_id
                    and r.target in self.repo.elements
                ]
                if targets:
                    obj.properties["trace_to"] = ", ".join(sorted(targets))
            self.objects.append(obj)
        self.sort_objects()
        self.connections = []
        for data in self.repo.visible_connections(diag.diag_id):
            data.setdefault("stereotype", data.get("conn_type", "").lower())
            self.connections.append(DiagramConnection(**data))
        if self.objects:
            global _next_obj_id
            _next_obj_id = max(o.obj_id for o in self.objects) + 1
        self.redraw()
        self.update_property_view()

    def on_close(self):
        self._sync_to_repository()
        self.destroy()


class SysMLObjectDialog(simpledialog.Dialog):
    """Simple dialog for editing AutoML object properties."""

    def __init__(self, master, obj: SysMLObject):
        if not hasattr(obj, "requirements"):
            obj.requirements = []
        self.obj = obj
        super().__init__(master, title=f"Edit {obj.obj_type}")

    class SelectRequirementsDialog(simpledialog.Dialog):
        def __init__(self, parent, title="Select Requirements"):
            self.selected_vars = {}
            super().__init__(parent, title=title)

        def body(self, master):
            ttk.Label(master, text="Select requirements:").pack(padx=5, pady=5)
            container = ttk.Frame(master)
            container.pack(fill=tk.BOTH, expand=True)
            canvas = tk.Canvas(container, borderwidth=0)
            scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
            self.check_frame = ttk.Frame(canvas)
            self.check_frame.bind(
                "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            canvas.create_window((0, 0), window=self.check_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            for req_id, req in global_requirements.items():
                var = tk.BooleanVar(value=False)
                self.selected_vars[req_id] = var
                text = f"[{req['id']}] {req['text']}"
                ttk.Checkbutton(self.check_frame, text=text, variable=var).pack(
                    anchor="w", padx=2, pady=2
                )
            return self.check_frame

        def apply(self):
            self.result = [rid for rid, var in self.selected_vars.items() if var.get()]

    class SelectComponentsDialog(simpledialog.Dialog):
        """Dialog to choose which components should become parts."""

        def __init__(self, parent, components):
            self.components = components
            self.selected = {}
            super().__init__(parent, title="Select Components")

        def body(self, master):
            ttk.Label(master, text="Select components:").pack(padx=5, pady=5)
            frame = ttk.Frame(master)
            frame.pack(fill=tk.BOTH, expand=True)
            canvas = tk.Canvas(frame, borderwidth=0)
            scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
            self.check_frame = ttk.Frame(canvas)
            self.check_frame.bind(
                "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            canvas.create_window((0, 0), window=self.check_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            for comp in self.components:
                var = tk.BooleanVar(value=True)
                self.selected[comp] = var
                ttk.Checkbutton(self.check_frame, text=comp.name, variable=var).pack(
                    anchor="w", padx=2, pady=2
                )
            return self.check_frame

        def apply(self):
            self.result = [c for c, var in self.selected.items() if var.get()]

    class SelectTraceDialog(simpledialog.Dialog):
        """Dialog to choose target elements for trace links."""

        def __init__(
            self,
            parent,
            repo: SysMLRepository,
            work_products: list[str],
            source_id: int | None,
            source_diag: str | None,
        ):
            self.repo = repo
            self.work_products = work_products
            self.source_id = source_id
            self.source_diag = source_diag
            self.selection: list[str] = []
            super().__init__(parent, title="Select Trace Targets")

        def body(self, master):  # pragma: no cover - requires tkinter
            ttk.Label(master, text="Select targets:").pack(anchor="w", padx=5, pady=5)
            self.lb = tk.Listbox(master, selectmode=tk.MULTIPLE, width=40)
            self._tokens: list[str] = []
            for diag in self.repo.diagrams.values():
                if not any(_diag_matches_wp(diag.diag_type, wp) for wp in self.work_products):
                    continue
                dname = diag.name or diag.diag_id
                for obj in getattr(diag, "objects", []):
                    if diag.diag_id == self.source_diag and obj.get("obj_id") == self.source_id:
                        continue
                    name = obj.get("properties", {}).get("name") or obj.get("obj_type", "")
                    token = f"{diag.diag_id}:{obj.get('obj_id')}"
                    self._tokens.append(token)
                    self.lb.insert(tk.END, f"{dname}:{name}")
            self.lb.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            return self.lb

        def apply(self):  # pragma: no cover - requires tkinter
            sels = self.lb.curselection()
            self.selection = [self._tokens[i] for i in sels]

    class SelectNamesDialog(simpledialog.Dialog):
        """Dialog to choose which part names should be added."""

        def __init__(self, parent, names, title="Select Parts"):
            self.names = names
            self.selected = {}
            super().__init__(parent, title=title)

        def body(self, master):
            ttk.Label(master, text="Select parts:").pack(padx=5, pady=5)
            frame = ttk.Frame(master)
            frame.pack(fill=tk.BOTH, expand=True)
            canvas = tk.Canvas(frame, borderwidth=0)
            scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
            self.check_frame = ttk.Frame(canvas)
            self.check_frame.bind(
                "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            canvas.create_window((0, 0), window=self.check_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            for name in self.names:
                var = tk.BooleanVar(value=True)
                self.selected[name] = var
                ttk.Checkbutton(self.check_frame, text=name, variable=var).pack(
                    anchor="w", padx=2, pady=2
                )
            return self.check_frame

        def apply(self):
            self.result = [n for n, var in self.selected.items() if var.get()]

    class SelectElementDialog(simpledialog.Dialog):
        """Dialog to choose a single existing element."""

        def __init__(self, parent, names, title="Select Element"):
            self.names = names
            self.result = None
            super().__init__(parent, title=title)

        def body(self, master):
            ttk.Label(master, text="Select element:").pack(padx=5, pady=5)
            self.listbox = tk.Listbox(master)
            for name in self.names:
                self.listbox.insert(tk.END, name)
            self.listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            return self.listbox

        def apply(self):
            sel = self.listbox.curselection()
            if sel:
                self.result = self.names[sel[0]]

    class ManagePartsDialog(simpledialog.Dialog):
        """Dialog to toggle visibility of contained parts."""

        def __init__(self, parent, names, visible, hidden):
            self.names = names
            self.visible = visible
            self.hidden = hidden
            self.selected = {}
            super().__init__(parent, title="Add Contained Parts")

        def body(self, master):
            ttk.Label(master, text="Select parts to show:").pack(padx=5, pady=5)
            frame = ttk.Frame(master)
            frame.pack(fill=tk.BOTH, expand=True)
            canvas = tk.Canvas(frame, borderwidth=0)
            scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
            self.check_frame = ttk.Frame(canvas)
            self.check_frame.bind(
                "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            canvas.create_window((0, 0), window=self.check_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            for name in self.names:
                var = tk.BooleanVar(value=name in self.visible)
                self.selected[name] = var
                ttk.Checkbutton(self.check_frame, text=name, variable=var).pack(
                    anchor="w", padx=2, pady=2
                )
            return self.check_frame

        def apply(self):
            self.result = [n for n, var in self.selected.items() if var.get()]

    def body(self, master):
        # Disable window resizing so the layout remains consistent
        self.resizable(False, False)

        # Use a notebook to keep the dialog compact by grouping fields
        self.nb = ttk.Notebook(master)
        self.nb.grid(row=0, column=0, columnspan=3, sticky="nsew")

        gen_frame = ttk.Frame(self.nb)
        prop_frame = ttk.Frame(self.nb)
        rel_frame = ttk.Frame(self.nb)
        link_frame = ttk.Frame(self.nb)
        req_frame = ttk.Frame(self.nb)

        self.nb.add(gen_frame, text="General")
        self.nb.add(prop_frame, text="Properties")
        self.nb.add(rel_frame, text="Reliability")
        self.nb.add(link_frame, text="Links")
        self.nb.add(req_frame, text="Requirements")

        gen_row = 0
        ttk.Label(gen_frame, text="Name:").grid(row=gen_row, column=0, sticky="e", padx=4, pady=4)
        self.name_var = tk.StringVar(value=self.obj.properties.get("name", ""))
        readonly = self.obj.properties.get("name_locked") == "1"
        name_state = "readonly" if readonly else "normal"
        ttk.Entry(gen_frame, textvariable=self.name_var, state=name_state).grid(
            row=gen_row, column=1, padx=4, pady=4
        )
        gen_row += 1
        ttk.Label(gen_frame, text="Width:").grid(row=gen_row, column=0, sticky="e", padx=4, pady=2)
        self.width_var = tk.StringVar(value=str(self.obj.width))
        width_state = (
            "readonly"
            if self.obj.obj_type in ("Initial", "Final", "Actor", "Decision", "Merge")
            else "normal"
        )
        ttk.Entry(gen_frame, textvariable=self.width_var, state=width_state).grid(
            row=gen_row, column=1, padx=4, pady=2
        )
        gen_row += 1
        if self.obj.obj_type not in ("Fork", "Join"):
            ttk.Label(gen_frame, text="Height:").grid(
                row=gen_row, column=0, sticky="e", padx=4, pady=2
            )
            self.height_var = tk.StringVar(value=str(self.obj.height))
            height_state = (
                "readonly"
                if self.obj.obj_type
                in ("Initial", "Final", "Actor", "Decision", "Merge")
                else "normal"
            )
            ttk.Entry(gen_frame, textvariable=self.height_var, state=height_state).grid(
                row=gen_row, column=1, padx=4, pady=2
            )
            gen_row += 1
        else:
            self.height_var = tk.StringVar(value=str(self.obj.height))
        self.entries = {}
        self.listboxes = {}
        self._operations: List[OperationDefinition] = []
        self._behaviors: List[BehaviorAssignment] = []
        prop_row = 0
        rel_row = 0
        if self.obj.obj_type == "Part":
            self.obj.properties.setdefault("asil", calculate_allocated_asil(self.obj.requirements))
        key = f"{self.obj.obj_type.replace(' ', '')}Usage"
        if key not in SYSML_PROPERTIES and self.obj.obj_type == "Block Boundary":
            key = "BlockUsage"
        list_props = {
            "ports",
            "operations",
            "behaviors",
            "failureModes",
        }
        editable_list_props = {"ports"}
        if self.obj.obj_type != "Block":
            list_props.add("partProperties")
            editable_list_props.add("partProperties")
        reliability_props = {
            "analysis",
            "component",
            "fit",
            "qualification",
            "failureModes",
            "asil",
        }
        app = getattr(self.master, "app", None)
        props = SYSML_PROPERTIES.get(key, [])
        if self.obj.obj_type == "Block":
            props = [p for p in props if p != "partProperties"]
        for prop in props:
            frame = rel_frame if prop in reliability_props else prop_frame
            row = rel_row if prop in reliability_props else prop_row
            ttk.Label(frame, text=f"{prop}:").grid(row=row, column=0, sticky="e", padx=4, pady=2)
            if prop == "operations":
                lb = tk.Listbox(frame, height=4)
                self._operations = parse_operations(self.obj.properties.get(prop, ""))
                for op in self._operations:
                    lb.insert(tk.END, format_operation(op))
                lb.grid(row=row, column=1, padx=4, pady=2, sticky="we")
                btnf = ttk.Frame(frame)
                btnf.grid(row=row, column=2, padx=2)
                ttk.Button(btnf, text="Add", command=self.add_operation).pack(side=tk.TOP)
                ttk.Button(btnf, text="Edit", command=self.edit_operation).pack(side=tk.TOP)
                ttk.Button(btnf, text="Remove", command=self.remove_operation).pack(side=tk.TOP)
                self.listboxes[prop] = lb
            elif prop == "behaviors":
                lb = tk.Listbox(frame, height=4)
                self._behaviors = parse_behaviors(self.obj.properties.get(prop, ""))
                repo = SysMLRepository.get_instance()
                for beh in self._behaviors:
                    name = repo.diagrams.get(beh.diagram)
                    label = f"{beh.operation} -> {name.name if name else beh.diagram}"
                    lb.insert(tk.END, label)
                lb.grid(row=row, column=1, padx=4, pady=2, sticky="we")
                btnf = ttk.Frame(frame)
                btnf.grid(row=row, column=2, padx=2)
                ttk.Button(btnf, text="Add", command=self.add_behavior).pack(side=tk.TOP)
                ttk.Button(btnf, text="Edit", command=self.edit_behavior).pack(side=tk.TOP)
                ttk.Button(btnf, text="Remove", command=self.remove_behavior).pack(side=tk.TOP)
                self.listboxes[prop] = lb
            elif prop in list_props:
                lb = tk.Listbox(frame, height=4)
                items = [
                    p.strip() for p in self.obj.properties.get(prop, "").split(",") if p.strip()
                ]
                for it in items:
                    lb.insert(tk.END, it)
                lb.grid(row=row, column=1, padx=4, pady=2, sticky="we")
                btnf = ttk.Frame(frame)
                btnf.grid(row=row, column=2, padx=2)
                if prop == "ports":
                    ttk.Button(btnf, text="Add", command=self.add_port).pack(side=tk.TOP)
                else:
                    ttk.Button(
                        btnf, text="Add", command=lambda p=prop: self.add_list_item(p)
                    ).pack(side=tk.TOP)
                if prop in editable_list_props:
                    if prop == "ports":
                        ttk.Button(btnf, text="Edit", command=self.edit_port).pack(side=tk.TOP)
                    else:
                        ttk.Button(
                            btnf, text="Edit", command=lambda p=prop: self.edit_list_item(p)
                        ).pack(side=tk.TOP)
                ttk.Button(
                    btnf, text="Remove", command=lambda p=prop: self.remove_list_item(p)
                ).pack(side=tk.TOP)
                self.listboxes[prop] = lb
            elif prop == "direction":
                var = tk.StringVar(value=self.obj.properties.get(prop, "in"))
                conns = [
                    c
                    for c in self.master.connections
                    if c.conn_type == "Connector" and self.obj.obj_id in (c.src, c.dst)
                ]
                state = "readonly" if conns else "normal"
                ttk.Combobox(
                    frame,
                    textvariable=var,
                    values=["in", "out", "inout"],
                    state=state,
                ).grid(row=row, column=1, padx=4, pady=2)
                self.entries[prop] = var
            elif self.obj.obj_type == "Use Case" and prop == "useCaseDefinition":
                repo = SysMLRepository.get_instance()
                diags = [
                    d
                    for d in repo.diagrams.values()
                    if d.diag_type == "Use Case Diagram" and d.diag_id != self.master.diagram_id
                ]
                idmap = {d.name or d.diag_id: d.diag_id for d in diags}
                self.ucdef_map = idmap
                cur_id = self.obj.properties.get(prop, "")
                cur_name = next((n for n, i in idmap.items() if i == cur_id), "")
                var = tk.StringVar(value=cur_name)
                ttk.Combobox(frame, textvariable=var, values=list(idmap.keys())).grid(
                    row=row, column=1, padx=4, pady=2
                )
                self.entries[prop] = var
            elif self.obj.obj_type == "Use Case" and prop == "includedUseCase":
                repo = SysMLRepository.get_instance()
                targets = [
                    repo.elements[t].name or t
                    for rel in repo.relationships
                    if rel.rel_type == "Include" and rel.source == self.obj.element_id
                    if (t := rel.target) in repo.elements
                ]
                ttk.Label(frame, text=", ".join(targets)).grid(
                    row=row, column=1, sticky="w", padx=4, pady=2
                )
            elif prop == "analysis" and app:
                analyses = getattr(app, "reliability_analyses", [])
                names = [ra.name for ra in analyses]
                var = tk.StringVar(value=self.obj.properties.get(prop, ""))
                cb = ttk.Combobox(frame, textvariable=var, values=names, state="readonly")
                cb.grid(row=row, column=1, padx=4, pady=2)
                self.entries[prop] = var
                self._analysis_map = {ra.name: ra for ra in analyses}

                def sync_analysis(_):
                    name = var.get()
                    ra = self._analysis_map.get(name)
                    if not ra:
                        return
                    if "fit" in self.entries:
                        self.entries["fit"].set(f"{ra.total_fit:.2f}")
                    else:
                        self.obj.properties["fit"] = f"{ra.total_fit:.2f}"
                    # update part list preview from analysis BOM
                    names = [c.name for c in ra.components]
                    joined = ", ".join(names)
                    if "partProperties" in self.listboxes:
                        lb = self.listboxes["partProperties"]
                        lb.delete(0, tk.END)
                        for n in names:
                            lb.insert(tk.END, n)
                    else:
                        self.obj.properties["partProperties"] = joined

                cb.bind("<<ComboboxSelected>>", sync_analysis)
            elif prop == "component" and app:
                comps = [
                    c
                    for ra in getattr(app, "reliability_analyses", [])
                    for c in ra.components
                    if c.comp_type != "circuit"
                ]
                comps.extend(
                    c
                    for c in getattr(app, "reliability_components", [])
                    if c.comp_type != "circuit"
                )
                names = list({c.name for c in comps})
                var = tk.StringVar(value=self.obj.properties.get(prop, ""))
                cb = ttk.Combobox(frame, textvariable=var, values=names, state="readonly")
                cb.grid(row=row, column=1, padx=4, pady=2)
                self.entries[prop] = var
                self._comp_map = {c.name: c for c in comps}

                def sync_component(_):
                    name = var.get()
                    comp = self._comp_map.get(name)
                    if not comp:
                        return
                    if "fit" in self.entries:
                        self.entries["fit"].set(f"{comp.fit:.2f}")
                    else:
                        self.obj.properties["fit"] = f"{comp.fit:.2f}"
                    if "qualification" in self.entries:
                        self.entries["qualification"].set(comp.qualification)
                    else:
                        self.obj.properties["qualification"] = comp.qualification
                    modes = self._get_failure_modes(app, comp.name)
                    if "failureModes" in self.entries:
                        self.entries["failureModes"].set(modes)
                    else:
                        self.obj.properties["failureModes"] = modes

                cb.bind("<<ComboboxSelected>>", sync_component)
            else:
                var = tk.StringVar(value=self.obj.properties.get(prop, ""))
                state = "normal"
                if self.obj.obj_type == "Block" and prop in ("fit", "qualification"):
                    state = "readonly"
                if self.obj.obj_type == "Part" and prop == "asil":
                    state = "readonly"
                ttk.Entry(frame, textvariable=var, state=state).grid(
                    row=row, column=1, padx=4, pady=2
                )
                self.entries[prop] = var
            if prop in reliability_props:
                rel_row += 1
            else:
                prop_row += 1

        # Display inherited reliability values only for Blocks
        if self.obj.obj_type == "Block":
            for prop in ("fit", "qualification"):
                if prop not in self.entries and self.obj.properties.get(prop, ""):
                    ttk.Label(rel_frame, text=f"{prop}:").grid(
                        row=rel_row, column=0, sticky="e", padx=4, pady=2
                    )
                    var = tk.StringVar(value=self.obj.properties.get(prop, ""))
                    ttk.Entry(rel_frame, textvariable=var, state="readonly").grid(
                        row=rel_row, column=1, padx=4, pady=2
                    )
                    self.entries[prop] = var
                    rel_row += 1

        repo = SysMLRepository.get_instance()
        current_diagram = repo.diagrams.get(getattr(self.master, "diagram_id", ""))
        self.current_diagram = current_diagram
        toolbox = getattr(app, "safety_mgmt_toolbox", None)
        wp_map = {wp.analysis: wp for wp in toolbox.get_work_products()} if toolbox else {}
        diag_type = getattr(current_diagram, "diag_type", "")
        analysis_name = _work_product_name(diag_type)
        diagram_wp = wp_map.get(analysis_name)
        diag_trace_opts = sorted(getattr(diagram_wp, "traceable", [])) if diagram_wp else []
        self._target_work_product = (
            self.obj.properties.get("name", "")
            if self.obj.obj_type == "Work Product"
            else getattr(diagram_wp, "analysis", analysis_name)
        )
        link_row = 0
        trace_shown = False
        if self.obj.obj_type == "Block":
            diags = [d for d in repo.diagrams.values() if d.diag_type == "Internal Block Diagram"]
            ids = {d.name or d.diag_id: d.diag_id for d in diags}
            ttk.Label(link_frame, text="Internal Block Diagram:").grid(
                row=link_row, column=0, sticky="e", padx=4, pady=2
            )
            self.diag_map = ids
            cur_id = repo.get_linked_diagram(self.obj.element_id)
            cur_name = next((n for n, i in ids.items() if i == cur_id), "")
            self.diagram_var = tk.StringVar(value=cur_name)
            ttk.Combobox(link_frame, textvariable=self.diagram_var, values=list(ids.keys())).grid(
                row=link_row, column=1, padx=4, pady=2
            )
            link_row += 1
        elif self.obj.obj_type == "Work Product":
            name = self.obj.properties.get("name", "")
            targets = wp_map.get(name)
            trace_opts = sorted(getattr(targets, "traceable", [])) if targets else []
            if trace_opts:
                ttk.Label(link_frame, text="Trace To:").grid(
                    row=link_row, column=0, sticky="e", padx=4, pady=2
                )
                lb = tk.Listbox(link_frame, height=4, selectmode=tk.MULTIPLE)
                for opt in trace_opts:
                    lb.insert(tk.END, opt)
                current = [
                    s.strip()
                    for s in self.obj.properties.get("trace_to", "").split(",")
                    if s.strip()
                ]
                for idx, opt in enumerate(trace_opts):
                    if opt in current:
                        lb.selection_set(idx)
                lb.grid(row=link_row, column=1, padx=4, pady=2, sticky="we")
                self.trace_list = lb
                link_row += 1
                trace_shown = True
        elif self.obj.obj_type == "Use Case":
            diagrams = [d for d in repo.diagrams.values() if d.diag_type == "Governance Diagram"]
            self.behavior_map = {d.name or d.diag_id: d.diag_id for d in diagrams}
            ttk.Label(link_frame, text="Behavior Diagram:").grid(
                row=link_row, column=0, sticky="e", padx=4, pady=2
            )
            cur_id = repo.get_linked_diagram(self.obj.element_id)
            cur_name = next((n for n, i in self.behavior_map.items() if i == cur_id), "")
            self.behavior_var = tk.StringVar(value=cur_name)
            ttk.Combobox(
                link_frame, textvariable=self.behavior_var, values=list(self.behavior_map.keys())
            ).grid(row=link_row, column=1, padx=4, pady=2)
            link_row += 1
            if diag_trace_opts:
                ttk.Label(link_frame, text="Trace To:").grid(
                    row=link_row, column=0, sticky="e", padx=4, pady=2
                )
                lb = tk.Listbox(link_frame, height=4, selectmode=tk.MULTIPLE)
                for opt in diag_trace_opts:
                    lb.insert(tk.END, opt)
                current = [
                    s.strip()
                    for s in self.obj.properties.get("trace_to", "").split(",")
                    if s.strip()
                ]
                for idx, opt in enumerate(diag_trace_opts):
                    if opt in current:
                        lb.selection_set(idx)
                lb.grid(row=link_row, column=1, padx=4, pady=2, sticky="we")
                self.trace_list = lb
                link_row += 1
                trace_shown = True
        elif self.obj.obj_type in ("Action Usage", "Action"):
            if (
                self.obj.obj_type == "Action"
                and current_diagram
                and current_diagram.diag_type == "Governance Diagram"
            ):
                diagrams = [
                    d for d in repo.diagrams.values() if d.diag_type == "Governance Diagram"
                ]
            else:
                diagrams = [
                    d
                    for d in repo.diagrams.values()
                    if d.diag_type in ("Activity Diagram", "Governance Diagram")
                ]
            self.behavior_map = {d.name or d.diag_id: d.diag_id for d in diagrams}
            ttk.Label(link_frame, text="Behavior Diagram:").grid(
                row=link_row, column=0, sticky="e", padx=4, pady=2
            )
            cur_id = repo.get_linked_diagram(self.obj.element_id)
            cur_name = next((n for n, i in self.behavior_map.items() if i == cur_id), "")
            self.behavior_var = tk.StringVar(value=cur_name)
            ttk.Combobox(
                link_frame, textvariable=self.behavior_var, values=list(self.behavior_map.keys())
            ).grid(row=link_row, column=1, padx=4, pady=2)
            link_row += 1
        elif self.obj.obj_type == "CallBehaviorAction":
            bdiags = [
                d
                for d in repo.diagrams.values()
                if d.diag_type in ("Activity Diagram", "Governance Diagram")
            ]
            self.behavior_map = {d.name or d.diag_id: d.diag_id for d in bdiags}
            ttk.Label(link_frame, text="Behavior Diagram:").grid(
                row=link_row, column=0, sticky="e", padx=4, pady=2
            )
            cur_id = repo.get_linked_diagram(self.obj.element_id)
            cur_name = next((n for n, i in self.behavior_map.items() if i == cur_id), "")
            self.behavior_var = tk.StringVar(value=cur_name)
            ttk.Combobox(
                link_frame, textvariable=self.behavior_var, values=list(self.behavior_map.keys())
            ).grid(row=link_row, column=1, padx=4, pady=2)
            link_row += 1
            vdiags = [d for d in repo.diagrams.values() if d.diag_type == "Internal Block Diagram"]
            self.view_map = {d.name or d.diag_id: d.diag_id for d in vdiags}
            ttk.Label(link_frame, text="View:").grid(
                row=link_row, column=0, sticky="e", padx=4, pady=2
            )
            view_id = self.obj.properties.get("view", "")
            vname = next((n for n, i in self.view_map.items() if i == view_id), "")
            self.view_var = tk.StringVar(value=vname)
            ttk.Combobox(
                link_frame, textvariable=self.view_var, values=list(self.view_map.keys())
            ).grid(row=link_row, column=1, padx=4, pady=2)
            link_row += 1
        elif self.obj.obj_type == "Part":
            blocks = [e for e in repo.elements.values() if e.elem_type == "Block"]
            idmap = {b.name or b.elem_id: b.elem_id for b in blocks}
            ttk.Label(link_frame, text="Definition:").grid(
                row=link_row, column=0, sticky="e", padx=4, pady=2
            )
            self.def_map = idmap
            cur_id = self.obj.properties.get("definition", "")
            cur_name = next((n for n, i in idmap.items() if i == cur_id), "")
            self.def_var = tk.StringVar(value=cur_name)
            self.def_cb = ttk.Combobox(
                link_frame, textvariable=self.def_var, values=list(idmap.keys())
            )
            self.def_cb.grid(row=link_row, column=1, padx=4, pady=2)
            self.def_cb.bind("<<ComboboxSelected>>", self._on_def_selected)
            self._current_def_id = cur_id
            link_row += 1

        if diag_trace_opts and not trace_shown:
            ttk.Label(link_frame, text="Trace To:").grid(
                row=link_row, column=0, sticky="e", padx=4, pady=2
            )
            self.trace_list = tk.Listbox(link_frame, height=4)
            self.trace_list.grid(row=link_row, column=1, padx=4, pady=2, sticky="we")
            btnf = ttk.Frame(link_frame)
            btnf.grid(row=link_row, column=2, padx=2)
            ttk.Button(btnf, text="Add", command=lambda: self.add_trace(diag_trace_opts)).pack(side=tk.TOP)
            ttk.Button(btnf, text="Remove", command=self.remove_trace).pack(side=tk.TOP)
            self._trace_targets = []
            for token in [t.strip() for t in self.obj.properties.get("trace_to", "").split(",") if t.strip()]:
                self._trace_targets.append(token)
                self.trace_list.insert(tk.END, self._format_trace_label(token))
            link_row += 1
            trace_shown = True

        # Requirement allocation section
        req_row = 0
        ttk.Label(req_frame, text="Requirements:").grid(
            row=req_row, column=0, sticky="ne", padx=4, pady=2
        )
        can_trace_reqs = True
        if toolbox:
            diag_name = getattr(diagram_wp, "analysis", None)
            req_wp = next(iter(REQUIREMENT_WORK_PRODUCTS), None)
            if diag_name and req_wp:
                can_trace_reqs = toolbox.can_trace(diag_name, req_wp)
        state = "normal" if can_trace_reqs else "disabled"
        self.req_list = tk.Listbox(req_frame, height=4, state=state)
        self.req_list.grid(row=req_row, column=1, padx=4, pady=2, sticky="we")
        if can_trace_reqs:
            btnf = ttk.Frame(req_frame)
            btnf.grid(row=req_row, column=2, padx=2)
            ttk.Button(btnf, text="Add", command=self.add_requirement).pack(side=tk.TOP)
            ttk.Button(btnf, text="Remove", command=self.remove_requirement).pack(side=tk.TOP)
        else:
            if ToolTip:
                ToolTip(
                    self.req_list,
                    "Requirement allocation is disabled for this diagram due to governance restrictions.",
                )
        for r in self.obj.requirements:
            self.req_list.insert(tk.END, f"[{r.get('id')}] {r.get('text','')}")
        req_row += 1
        self._update_asil()

    def add_port(self):
        name = simpledialog.askstring("Port", "Name:", parent=self)
        if name:
            self.listboxes["ports"].insert(tk.END, name)

    def remove_port(self):
        sel = list(self.listboxes["ports"].curselection())
        for idx in reversed(sel):
            self.listboxes["ports"].delete(idx)

    def edit_port(self):
        lb = self.listboxes["ports"]
        sel = lb.curselection()
        if not sel:
            return
        idx = sel[0]
        cur = lb.get(idx)
        name = simpledialog.askstring("Port", "Name:", initialvalue=cur, parent=self)
        if name:
            lb.delete(idx)
            lb.insert(idx, name)

    def add_list_item(self, prop: str):
        val = simpledialog.askstring(prop, "Value:", parent=self)
        if val:
            self.listboxes[prop].insert(tk.END, val)

    def remove_list_item(self, prop: str):
        lb = self.listboxes[prop]
        sel = list(lb.curselection())
        for idx in reversed(sel):
            lb.delete(idx)

    def edit_list_item(self, prop: str):
        lb = self.listboxes[prop]
        sel = lb.curselection()
        if not sel:
            return
        idx = sel[0]
        cur = lb.get(idx)
        val = simpledialog.askstring(prop, "Value:", initialvalue=cur, parent=self)
        if val:
            lb.delete(idx)
            lb.insert(idx, val)

    def add_trace(self, trace_wps):
        repo = SysMLRepository.get_instance()
        dlg = self.SelectTraceDialog(
            self,
            repo,
            trace_wps,
            getattr(self.obj, "obj_id", None),
            getattr(self.master, "diagram_id", None),
        )
        for token in getattr(dlg, "selection", []):
            if token not in self._trace_targets:
                self._trace_targets.append(token)
                self.trace_list.insert(tk.END, self._format_trace_label(token))

    def remove_trace(self):
        sel = list(self.trace_list.curselection())
        for idx in reversed(sel):
            self.trace_list.delete(idx)
            del self._trace_targets[idx]

    def _format_trace_label(self, token: str) -> str:
        repo = SysMLRepository.get_instance()
        parts = token.split(":", 1)
        if len(parts) != 2:
            return token
        diag_id, obj_id = parts
        diag = repo.diagrams.get(diag_id)
        dname = getattr(diag, "name", diag_id) if diag else diag_id
        obj = None
        if diag:
            obj = next(
                (o for o in getattr(diag, "objects", []) if str(o.get("obj_id")) == obj_id),
                None,
            )
        oname = (
            obj.get("properties", {}).get("name") or obj.get("obj_type")
            if obj
            else obj_id
        )
        return f"{dname}:{oname}"

    class OperationDialog(simpledialog.Dialog):
        def __init__(self, parent, operation=None):
            self.operation = operation
            super().__init__(parent, title="Operation")

        def body(self, master):
            ttk.Label(master, text="Name:").grid(row=0, column=0, padx=4, pady=2, sticky="e")
            self.name_var = tk.StringVar(value=getattr(self.operation, "name", ""))
            ttk.Entry(master, textvariable=self.name_var).grid(row=0, column=1, padx=4, pady=2)
            ttk.Label(master, text="Parameters (name:type:dir)").grid(
                row=1, column=0, columnspan=2, padx=4, pady=2
            )
            self.param_text = tk.Text(master, height=4, width=30)
            if self.operation:
                lines = [f"{p.name}:{p.type}:{p.direction}" for p in self.operation.parameters]
                self.param_text.insert("1.0", "\n".join(lines))
            self.param_text.grid(row=2, column=0, columnspan=2, padx=4, pady=2)
            ttk.Label(master, text="Return type:").grid(row=3, column=0, padx=4, pady=2, sticky="e")
            self.ret_var = tk.StringVar(value=getattr(self.operation, "return_type", ""))
            ttk.Entry(master, textvariable=self.ret_var).grid(row=3, column=1, padx=4, pady=2)

        def apply(self):
            name = self.name_var.get().strip()
            params = []
            for line in self.param_text.get("1.0", tk.END).splitlines():
                line = line.strip()
                if not line:
                    continue
                parts = line.split(":")
                if len(parts) == 1:
                    params.append(OperationParameter(name=parts[0]))
                elif len(parts) == 2:
                    params.append(OperationParameter(name=parts[0], type=parts[1]))
                else:
                    params.append(
                        OperationParameter(name=parts[0], type=parts[1], direction=parts[2])
                    )
            self.result = OperationDefinition(name, params, self.ret_var.get().strip())

    class BehaviorDialog(simpledialog.Dialog):
        def __init__(self, parent, operations: list[str], diag_map: dict[str, str], assignment=None):
            self.operations = operations
            self.diag_map = diag_map
            self.assignment = assignment
            super().__init__(parent, title="Behavior")

        def body(self, master):
            ttk.Label(master, text="Operation:").grid(row=0, column=0, padx=4, pady=2, sticky="e")
            self.op_var = tk.StringVar(value=getattr(self.assignment, "operation", ""))
            ttk.Combobox(master, textvariable=self.op_var, values=self.operations, state="readonly").grid(
                row=0, column=1, padx=4, pady=2
            )
            ttk.Label(master, text="Diagram:").grid(row=1, column=0, padx=4, pady=2, sticky="e")
            cur_name = next((n for n, i in self.diag_map.items() if i == getattr(self.assignment, "diagram", "")), "")
            self.diag_var = tk.StringVar(value=cur_name)
            ttk.Combobox(master, textvariable=self.diag_var, values=list(self.diag_map.keys()), state="readonly").grid(
                row=1, column=1, padx=4, pady=2
            )

        def apply(self):
            op = self.op_var.get().strip()
            diag_id = self.diag_map.get(self.diag_var.get(), "")
            self.result = BehaviorAssignment(operation=op, diagram=diag_id)

    def add_operation(self):
        dlg = self.OperationDialog(self)
        if dlg.result:
            self._operations.append(dlg.result)
            self.listboxes["operations"].insert(tk.END, format_operation(dlg.result))

    def edit_operation(self):
        lb = self.listboxes["operations"]
        sel = lb.curselection()
        if not sel:
            return
        idx = sel[0]
        op = self._operations[idx]
        dlg = self.OperationDialog(self, op)
        if dlg.result:
            self._operations[idx] = dlg.result
            lb.delete(idx)
            lb.insert(idx, format_operation(dlg.result))

    def remove_operation(self):
        lb = self.listboxes["operations"]
        sel = list(lb.curselection())
        for idx in reversed(sel):
            lb.delete(idx)
            del self._operations[idx]

    def add_behavior(self):
        repo = SysMLRepository.get_instance()
        diagrams = [
            d
            for d in repo.diagrams.values()
            if d.diag_type in ("Activity Diagram", "Governance Diagram")
        ]
        diag_map = {d.name or d.diag_id: d.diag_id for d in diagrams}
        ops = [op.name for op in self._operations]
        dlg = self.BehaviorDialog(self, ops, diag_map)
        if dlg.result:
            self._behaviors.append(dlg.result)
            name = repo.diagrams.get(dlg.result.diagram)
            label = f"{dlg.result.operation} -> {name.name if name else dlg.result.diagram}"
            self.listboxes["behaviors"].insert(tk.END, label)

    def edit_behavior(self):
        lb = self.listboxes["behaviors"]
        sel = lb.curselection()
        if not sel:
            return
        idx = sel[0]
        repo = SysMLRepository.get_instance()
        diagrams = [
            d
            for d in repo.diagrams.values()
            if d.diag_type in ("Activity Diagram", "Governance Diagram")
        ]
        diag_map = {d.name or d.diag_id: d.diag_id for d in diagrams}
        ops = [op.name for op in self._operations]
        dlg = self.BehaviorDialog(self, ops, diag_map, self._behaviors[idx])
        if dlg.result:
            self._behaviors[idx] = dlg.result
            name = repo.diagrams.get(dlg.result.diagram)
            label = f"{dlg.result.operation} -> {name.name if name else dlg.result.diagram}"
            lb.delete(idx)
            lb.insert(idx, label)

    def remove_behavior(self):
        lb = self.listboxes["behaviors"]
        sel = list(lb.curselection())
        for idx in reversed(sel):
            lb.delete(idx)
            del self._behaviors[idx]

    def add_requirement(self):
        if not global_requirements:
            messagebox.showinfo("No Requirements", "No requirements defined.")
            return
        dialog = self.SelectRequirementsDialog(self)
        if dialog.result:
            diag_id = getattr(self.master, "diagram_id", None)
            for rid in dialog.result:
                req = global_requirements.get(rid)
                if not req:
                    continue
                toolbox = ACTIVE_TOOLBOX
                if toolbox:
                    req_wp = toolbox.requirement_work_product(req.get("req_type", ""))
                    target = self._target_work_product or ""
                    if not toolbox.can_trace(req_wp, target):
                        messagebox.showwarning(
                            "Invalid Trace",
                            f"Requirement {req['id']} cannot trace to {target}",
                        )
                        continue
                if not any(r.get("id") == rid for r in self.obj.requirements):
                    self.obj.requirements.append(req)
                    self.req_list.insert(tk.END, f"[{req['id']}] {req.get('text','')}")
                before = [r.get("id") for r in getattr(self.obj, "requirements", [])]
                link_requirement_to_object(self.obj, rid, diag_id)
                if rid not in before and self.obj.obj_type != "Work Product":
                    req = global_requirements.get(rid)
                    if req:
                        self.req_list.insert(tk.END, f"[{req['id']}] {req.get('text','')}")
                elif self.obj.obj_type == "Work Product":
                    # Always reflect selection for work products
                    req = global_requirements.get(rid)
                    if req and rid not in [self.req_list.get(i).split("]", 1)[0][1:] for i in range(self.req_list.size())]:
                        self.req_list.insert(tk.END, f"[{req['id']}] {req.get('text','')}")
        self._update_asil()

    def remove_requirement(self):
        sel = list(self.req_list.curselection())
        diag_id = getattr(self.master, "diagram_id", None)
        for idx in reversed(sel):
            if self.obj.obj_type == "Work Product":
                item = self.req_list.get(idx)
                rid = item.split("]", 1)[0][1:]
            else:
                rid = self.obj.requirements[idx].get("id")
            unlink_requirement_from_object(self.obj, rid, diag_id)
            self.req_list.delete(idx)
        self._update_asil()

    def _update_asil(self) -> None:
        """Recompute ASIL based on allocated requirements."""
        if self.obj.obj_type != "Part":
            return
        asil = calculate_allocated_asil(self.obj.requirements)
        self.obj.properties["asil"] = asil
        if "asil" in self.entries:
            self.entries["asil"].set(asil)
        repo = SysMLRepository.get_instance()
        if self.obj.element_id and self.obj.element_id in repo.elements:
            repo.elements[self.obj.element_id].properties["asil"] = asil

    def _get_failure_modes(self, app, comp_name: str) -> str:
        """Return comma separated failure modes for a component name."""
        modes = set()
        for e in getattr(app, "fmea_entries", []):
            if getattr(e, "fmea_component", "") == comp_name:
                label = getattr(e, "description", "") or getattr(e, "user_name", "")
                if label:
                    modes.add(label)
        for fmea in getattr(app, "fmeas", []):
            for e in fmea.get("entries", []):
                if getattr(e, "fmea_component", "") == comp_name:
                    label = getattr(e, "description", "") or getattr(e, "user_name", "")
                    if label:
                        modes.add(label)
        return ", ".join(sorted(modes))

    def _on_def_selected(self, event=None):
        """Callback when the definition combobox is changed."""
        repo = SysMLRepository.get_instance()
        name = self.def_var.get()
        def_id = self.def_map.get(name)
        if not def_id:
            self._current_def_id = ""
            return

        parent_id = None
        if hasattr(self.master, "diagram_id"):
            diag = repo.diagrams.get(self.master.diagram_id)
            if diag and diag.diag_type == "Internal Block Diagram":
                parent_id = getattr(diag, "father", None) or next(
                    (eid for eid, did in repo.element_diagrams.items() if did == diag.diag_id),
                    None,
                )

        if parent_id and _multiplicity_limit_exceeded(
            repo,
            parent_id,
            def_id,
            getattr(self.master, "objects", []),
            self.obj.element_id,
        ):
            messagebox.showinfo(
                "Add Part",
                "Maximum number of parts of that type has been reached",
            )
            prev_name = next(
                (n for n, i in self.def_map.items() if i == self._current_def_id),
                "",
            )
            self.def_var.set(prev_name)
            return

        self._current_def_id = def_id

    def apply(self):
        repo = SysMLRepository.get_instance()
        parent_id = None
        if self.obj.properties.get("name_locked") != "1":
            new_name = self.name_var.get()
            if self.obj.obj_type == "Part" and hasattr(self.master, "diagram_id"):
                diag = repo.diagrams.get(self.master.diagram_id)
                if diag and diag.diag_type == "Internal Block Diagram":
                    parent_id = getattr(diag, "father", None) or next(
                        (eid for eid, did in repo.element_diagrams.items() if did == diag.diag_id),
                        None,
                    )
            if parent_id and _part_name_exists(repo, parent_id, new_name, self.obj.element_id):
                messagebox.showinfo("Add Part", "A part with that name already exists")
                new_name = self.obj.properties.get("name", "")
            new_name = repo.ensure_unique_element_name(new_name, self.obj.element_id)
            if self.obj.obj_type == "Port" and hasattr(self.master, "objects"):
                rename_port(repo, self.obj, self.master.objects, new_name)
            self.obj.properties["name"] = new_name
            if self.obj.element_id and self.obj.element_id in repo.elements:
                elem = repo.elements[self.obj.element_id]
                if self.obj.obj_type in ("Block", "Block Boundary") and elem.elem_type == "Block":
                    rename_block(repo, elem.elem_id, new_name)
                else:
                    elem.name = new_name
            if self.obj.obj_type == "Port" and hasattr(self.master, "objects"):
                rename_port(repo, self.obj, self.master.objects, new_name)
        else:
            new_name = self.obj.properties.get("name", "")
        for prop, var in self.entries.items():
            self.obj.properties[prop] = var.get()
            if self.obj.element_id and self.obj.element_id in repo.elements:
                repo.elements[self.obj.element_id].properties[prop] = var.get()
        removed_parts = []
        prev_parts = []
        if (
            self.obj.element_id
            and self.obj.element_id in repo.elements
            and "partProperties" in repo.elements[self.obj.element_id].properties
        ):
            prev_parts = [
                p.strip()
                for p in repo.elements[self.obj.element_id]
                .properties.get("partProperties", "")
                .split(",")
                if p.strip()
            ]

        for prop, lb in self.listboxes.items():
            if prop == "operations":
                self.obj.properties[prop] = operations_to_json(self._operations)
                if self.obj.element_id and self.obj.element_id in repo.elements:
                    repo.elements[self.obj.element_id].properties[prop] = self.obj.properties[prop]
            elif prop == "behaviors":
                self.obj.properties[prop] = behaviors_to_json(self._behaviors)
                if self.obj.element_id and self.obj.element_id in repo.elements:
                    repo.elements[self.obj.element_id].properties[prop] = self.obj.properties[prop]
            else:
                items = [lb.get(i) for i in range(lb.size())]
                joined = ", ".join(items)
                self.obj.properties[prop] = joined
                if self.obj.element_id and self.obj.element_id in repo.elements:
                    repo.elements[self.obj.element_id].properties[prop] = joined
                if prop == "partProperties" and prev_parts:
                    prev_keys = {_part_prop_key(p) for p in prev_parts}
                    new_keys = {_part_prop_key(i) for i in items}
                    removed_parts = [p for p in prev_parts if _part_prop_key(p) not in new_keys]

        trace_lb = getattr(self, "trace_list", None)
        if trace_lb:
            targets = getattr(self, "_trace_targets", None)
            if targets is None:
                targets = [trace_lb.get(i) for i in getattr(trace_lb, "curselection", lambda: [])()]

            current_diag = getattr(self.master, "diagram_id", None)
            # Remove existing trace connections involving this object
            if current_diag and hasattr(self.master, "connections"):
                self.master.connections = [
                    c
                    for c in self.master.connections
                    if not (
                        c.conn_type == "Trace"
                        and (c.src == self.obj.obj_id or c.dst == self.obj.obj_id)
                    )
                ]
                diag_ref = repo.diagrams.get(current_diag)
                if diag_ref:
                    diag_ref.connections = [
                        c
                        for c in getattr(diag_ref, "connections", [])
                        if not (
                            c.get("conn_type") == "Trace"
                            and (
                                c.get("src") == self.obj.obj_id
                                or c.get("dst") == self.obj.obj_id
                            )
                        )
                    ]

            removed = {
                r.rel_id
                for r in repo.relationships
                if r.rel_type == "Trace"
                and (r.source == self.obj.element_id or r.target == self.obj.element_id)
            }
            if removed:
                repo.relationships = [r for r in repo.relationships if r.rel_id not in removed]
                for diag in repo.diagrams.values():
                    diag.relationships = [rid for rid in diag.relationships if rid not in removed]

            stored_tokens: list[str] = []
            for token in targets:
                parts = token.split(":", 1)
                if len(parts) != 2:
                    stored_tokens.append(token)
                    target_elem = next(
                        (e for e in repo.elements.values() if e.name == token),
                        None,
                    )
                    if target_elem and self.obj.element_id:
                        repo.create_relationship("Trace", self.obj.element_id, target_elem.elem_id)
                        repo.create_relationship("Trace", target_elem.elem_id, self.obj.element_id)
                    continue
                diag_id, obj_id = parts
                diag = repo.diagrams.get(diag_id)
                if not diag:
                    continue
                obj = next(
                    (o for o in getattr(diag, "objects", []) if str(o.get("obj_id")) == obj_id),
                    None,
                )
                if not obj:
                    continue
                if diag_id == current_diag:
                    link_trace_between_objects(self.obj, obj, current_diag)
                else:
                    stored_tokens.append(token)
                    target_elem = obj.get("element_id")
                    if target_elem and self.obj.element_id:
                        repo.create_relationship("Trace", self.obj.element_id, target_elem)
                        repo.create_relationship("Trace", target_elem, self.obj.element_id)

            joined = ", ".join(stored_tokens)
            if joined:
                self.obj.properties["trace_to"] = joined
            else:
                self.obj.properties.pop("trace_to", None)
            if self.obj.element_id and self.obj.element_id in repo.elements:
                elem_props = repo.elements[self.obj.element_id].properties
                if joined:
                    elem_props["trace_to"] = joined
                else:
                    elem_props.pop("trace_to", None)

        if self.obj.element_id and self.obj.element_id in repo.elements:
            elem_type = repo.elements[self.obj.element_id].elem_type
            if elem_type == "Block" and self.obj.obj_type in ("Block", "Block Boundary"):
                propagate_block_port_changes(repo, self.obj.element_id)
                propagate_block_part_changes(repo, self.obj.element_id)
                propagate_block_changes(repo, self.obj.element_id)
                app_ref = getattr(self.master, "app", None)
                added = _sync_ibd_partproperty_parts(
                    repo,
                    self.obj.element_id,
                    app=app_ref,
                    visible=True,
                )
                for data in added:
                    data["hidden"] = False
                _propagate_boundary_parts(repo, self.obj.element_id, added, app=app_ref)
                father_diag_id = repo.get_linked_diagram(self.obj.element_id)
                for diag in repo.diagrams.values():
                    if (
                        diag.diag_type == "Internal Block Diagram"
                        and getattr(diag, "father", None) == self.obj.element_id
                        and diag.diag_id != father_diag_id
                    ):
                        added_child = inherit_father_parts(repo, diag)
                        for obj in added_child:
                            if obj.get("obj_type") == "Part":
                                obj["hidden"] = False
                        if app_ref:
                            for win in getattr(app_ref, "ibd_windows", []):
                                if getattr(win, "diagram_id", None) == diag.diag_id:
                                    for obj in added_child:
                                        win.objects.append(SysMLObject(**obj))
                                    win.redraw()
                                    win._sync_to_repository()
        try:
            if self.obj.obj_type not in (
                "Initial",
                "Final",
                "Decision",
                "Merge",
            ):
                self.obj.width = float(self.width_var.get())
                self.obj.height = float(self.height_var.get())
        except ValueError:
            pass

        if hasattr(self.master, "ensure_text_fits"):
            self.master.ensure_text_fits(self.obj)

        self._update_asil()

        # ensure block shows BOM components as part names when an analysis is set
        if (
            self.obj.obj_type == "Block"
            and "analysis" in self.obj.properties
            and hasattr(self, "_analysis_map")
        ):
            ra = self._analysis_map.get(self.obj.properties["analysis"], None)
            if ra:
                cur = [
                    p.strip()
                    for p in self.obj.properties.get("partProperties", "").split(",")
                    if p.strip()
                ]
                names = [c.name for c in ra.components]
                for n in names:
                    if n not in cur:
                        cur.append(n)
                joined = ", ".join(cur)
                self.obj.properties["partProperties"] = joined
                if self.obj.element_id and self.obj.element_id in repo.elements:
                    repo.elements[self.obj.element_id].properties["partProperties"] = joined
                if self.obj.element_id:
                    inherit_block_properties(repo, self.obj.element_id)
                    self.obj.properties["partProperties"] = repo.elements[
                        self.obj.element_id
                    ].properties["partProperties"]

        # Update linked diagram if applicable
        link_id = None
        if hasattr(self, "behavior_var") and self.behavior_var.get():
            link_id = self.behavior_map.get(self.behavior_var.get())
        elif hasattr(self, "diagram_var"):
            link_id = self.diag_map.get(self.diagram_var.get())
        if hasattr(self, "behavior_var") or hasattr(self, "diagram_var"):
            if (
                self.obj.obj_type == "Block"
                and hasattr(self, "diagram_var")
                and link_id
                and link_id in repo.diagrams
                and repo.diagrams[link_id].diag_type == "Internal Block Diagram"
            ):
                link_block_to_ibd(
                    repo,
                    self.obj.element_id,
                    link_id,
                    app=getattr(self.master, "app", None),
                )
            else:
                repo.link_diagram(self.obj.element_id, link_id)
        if hasattr(self, "view_var"):
            view_id = self.view_map.get(self.view_var.get())
            if view_id:
                self.obj.properties["view"] = view_id
                if self.obj.element_id and self.obj.element_id in repo.elements:
                    repo.elements[self.obj.element_id].properties["view"] = view_id
            else:
                self.obj.properties.pop("view", None)
                if self.obj.element_id and self.obj.element_id in repo.elements:
                    repo.elements[self.obj.element_id].properties.pop("view", None)
        if hasattr(self, "def_var"):
            name = self.def_var.get()
            def_id = self.def_map.get(name)
            if def_id:
                parent_id = None
                if hasattr(self.master, "diagram_id"):
                    diag = repo.diagrams.get(self.master.diagram_id)
                    if diag and diag.diag_type == "Internal Block Diagram":
                        parent_id = getattr(diag, "father", None) or next(
                            (eid for eid, did in repo.element_diagrams.items() if did == diag.diag_id),
                            None,
                        )
                if parent_id:
                    rel = next(
                        (
                            r
                            for r in repo.relationships
                            if r.source == parent_id
                            and r.target == def_id
                            and r.rel_type in ("Aggregation", "Composite Aggregation")
                        ),
                        None,
                    )
                    limit_exceeded = _multiplicity_limit_exceeded(
                        repo,
                        parent_id,
                        def_id,
                        getattr(self.master, "objects", []),
                        self.obj.element_id,
                    )
                    if limit_exceeded:
                        messagebox.showinfo(
                            "Add Part",
                            "Maximum number of parts of that type has been reached",
                        )
                        def_id = None
                if def_id:
                    self.obj.properties["definition"] = def_id
                    if self.obj.element_id and self.obj.element_id in repo.elements:
                        repo.elements[self.obj.element_id].properties["definition"] = def_id
        if hasattr(self, "ucdef_var"):
            name = self.ucdef_var.get()
            def_id = self.ucdef_map.get(name)
            if def_id:
                self.obj.properties["useCaseDefinition"] = def_id
                if self.obj.element_id and self.obj.element_id in repo.elements:
                    repo.elements[self.obj.element_id].properties["useCaseDefinition"] = def_id

        # ------------------------------------------------------------
        # Add parts from selected analysis BOM
        # ------------------------------------------------------------
        if (
            self.obj.obj_type == "Block"
            and "analysis" in self.obj.properties
            and hasattr(self, "diag_map")
        ):
            diag_id = repo.get_linked_diagram(self.obj.element_id)
            if diag_id:
                ra_name = self.obj.properties.get("analysis", "")
                ra = getattr(self, "_analysis_map", {}).get(ra_name)
                if ra and ra.components:
                    comps = list(ra.components)
                    dlg = self.SelectComponentsDialog(self, comps)
                    selected = dlg.result or []
                    if selected:
                        diag = repo.diagrams.get(diag_id)
                        if diag is not None:
                            diag.objects = getattr(diag, "objects", [])
                            existing = {
                                o.get("properties", {}).get("component")
                                for o in diag.objects
                                if o.get("obj_type") == "Part"
                            }
                            base_x = 50.0
                            base_y = 50.0
                            offset = 60.0
                            for idx, c in enumerate(selected):
                                if c.name in existing:
                                    continue
                                elem = repo.create_element(
                                    "Part",
                                    name=c.name,
                                    properties={
                                        "component": c.name,
                                        "fit": f"{c.fit:.2f}",
                                        "qualification": c.qualification,
                                        "failureModes": self._get_failure_modes(
                                            getattr(self.master, "app", None), c.name
                                        ),
                                    },
                                    owner=repo.root_package.elem_id,
                                )
                                repo.add_element_to_diagram(diag_id, elem.elem_id)
                                obj = SysMLObject(
                                    _get_next_id(),
                                    "Part",
                                    base_x,
                                    base_y + offset * idx,
                                    element_id=elem.elem_id,
                                    properties=elem.properties.copy(),
                                    phase=_repo_phase(repo),
                                )
                                diag.objects.append(obj.__dict__)
                                # update any open windows for this diagram
                                app = getattr(self.master, "app", None)
                                if app:
                                    for win in getattr(app, "ibd_windows", []):
                                        if win.diagram_id == diag_id:
                                            win.objects.append(obj)
                                            win.redraw()
                                            win._sync_to_repository()
                            # update block partProperties with newly added components
                            new_names = [c.name for c in selected if c.name not in existing]
                            if new_names:
                                cur = self.obj.properties.get("partProperties", "")
                                names = [n.strip() for n in cur.split(",") if n.strip()]
                                for name in new_names:
                                    if name not in names:
                                        names.append(name)
                                joined = ", ".join(names)
                                self.obj.properties["partProperties"] = joined
                                if self.obj.element_id and self.obj.element_id in repo.elements:
                                    repo.elements[self.obj.element_id].properties[
                                        "partProperties"
                                    ] = joined
                                # update all diagram objects referencing this block element
                                for d in repo.diagrams.values():
                                    for o in getattr(d, "objects", []):
                                        if o.get("element_id") == self.obj.element_id:
                                            o.setdefault("properties", {})[
                                                "partProperties"
                                            ] = joined
                                # include parent block parts
                                if self.obj.element_id:
                                    inherit_block_properties(repo, self.obj.element_id)
                                    joined = repo.elements[self.obj.element_id].properties[
                                        "partProperties"
                                    ]
                                    self.obj.properties["partProperties"] = joined
                            repo.diagrams[diag_id] = diag
                            repo.touch_diagram(diag_id)
                            if self.obj.element_id:
                                repo.touch_element(self.obj.element_id)
                            if hasattr(self.master, "_sync_to_repository"):
                                self.master._sync_to_repository()


class ConnectionDialog(simpledialog.Dialog):
    """Edit connection style and custom routing points."""

    def __init__(self, master, connection: DiagramConnection):
        self.connection = connection
        super().__init__(master, title="Connection Properties")

    def body(self, master):
        # Disable window resizing so the property layout stays consistent
        self.resizable(False, False)
        ttk.Label(master, text="Name:").grid(row=0, column=0, sticky="e", padx=4, pady=4)
        self.name_var = tk.StringVar(value=self.connection.name)
        ttk.Entry(master, textvariable=self.name_var).grid(row=0, column=1, columnspan=2, padx=4, pady=4, sticky="we")

        ttk.Label(master, text="Style:").grid(row=1, column=0, sticky="e", padx=4, pady=4)
        self.style_var = tk.StringVar(value=self.connection.style)
        ttk.Combobox(master, textvariable=self.style_var,
                     values=["Straight", "Squared", "Custom"]).grid(row=1, column=1, padx=4, pady=4)

        ttk.Label(master, text="Points:").grid(row=2, column=0, sticky="ne", padx=4, pady=4)
        self.point_list = tk.Listbox(master, height=4)
        for px, py in self.connection.points:
            self.point_list.insert(tk.END, f"{px:.1f},{py:.1f}")
        self.point_list.grid(row=2, column=1, padx=4, pady=4, sticky="we")
        btnf = ttk.Frame(master)
        btnf.grid(row=2, column=2, padx=2)
        ttk.Button(btnf, text="Add", command=self.add_point).pack(side=tk.TOP)
        ttk.Button(btnf, text="Remove", command=self.remove_point).pack(side=tk.TOP)

        ttk.Label(master, text="Arrows:").grid(row=3, column=0, sticky="e", padx=4, pady=4)
        self.arrow_var = tk.StringVar(value=self.connection.arrow)
        self.arrow_cb = ttk.Combobox(
            master,
            textvariable=self.arrow_var,
            values=["none", "forward", "backward", "both"],
        )
        self.arrow_cb.grid(row=3, column=1, padx=4, pady=4)
        self.mid_var = tk.BooleanVar(value=self.connection.mid_arrow)
        self.mid_check = ttk.Checkbutton(
            master, text="Arrow", variable=self.mid_var
        )
        self.mid_check.grid(row=3, column=2, padx=4, pady=4)
        if self.connection.conn_type in (
            "Flow",
            "Generalize",
            "Generalization",
            "Include",
            "Extend",
        ):
            self.arrow_cb.configure(state="disabled")
            self.mid_check.configure(state="disabled")
        row = 4
        if self.connection.conn_type == "Control Action":
            repo = SysMLRepository.get_instance()
            src_obj = self.master.get_object(self.connection.src)
            beh_elems = get_block_behavior_elements(repo, getattr(src_obj, "element_id", ""))
            self.elem_map = {e.name or e.elem_id: e.elem_id for e in beh_elems}
            ttk.Label(master, text="Element:").grid(row=row, column=0, sticky="e", padx=4, pady=4)
            cur_name = next(
                (n for n, i in self.elem_map.items() if i == self.connection.element_id),
                "",
            )
            self.elem_var = tk.StringVar(value=cur_name)
            ttk.Combobox(
                master,
                textvariable=self.elem_var,
                values=list(self.elem_map.keys()),
            ).grid(row=row, column=1, padx=4, pady=4, sticky="we")
            row += 1
            ttk.Label(master, text="Guard:").grid(row=row, column=0, sticky="ne", padx=4, pady=4)
            self.guard_list = tk.Listbox(master, height=4)
            for g in self.connection.guard:
                self.guard_list.insert(tk.END, g)
            self.guard_list.grid(row=row, column=1, padx=4, pady=4, sticky="we")
            gbtn = ttk.Frame(master)
            gbtn.grid(row=row, column=2, padx=2)
            ttk.Button(gbtn, text="Add", command=self.add_guard).pack(side=tk.TOP)
            ttk.Button(gbtn, text="Remove", command=self.remove_guard).pack(side=tk.TOP)
            row += 1
            ttk.Label(master, text="Guard Ops:").grid(row=row, column=0, sticky="ne", padx=4, pady=4)
            self.guard_ops_list = tk.Listbox(master, height=4)
            for op in self.connection.guard_ops:
                self.guard_ops_list.insert(tk.END, op)
            self.guard_ops_list.grid(row=row, column=1, padx=4, pady=4, sticky="we")
            opbtn = ttk.Frame(master)
            opbtn.grid(row=row, column=2, padx=2)
            self.guard_op_choice = tk.StringVar(value="AND")
            ttk.Combobox(opbtn, textvariable=self.guard_op_choice, values=["AND", "OR"], state="readonly").pack(side=tk.TOP)
            ttk.Button(opbtn, text="Add", command=self.add_guard_op).pack(side=tk.TOP)
            ttk.Button(opbtn, text="Remove", command=self.remove_guard_op).pack(side=tk.TOP)
            row += 1
        elif (
            getattr(
                self.master.repo.diagrams.get(self.master.diagram_id), "diag_type", ""
            )
            == "Governance Diagram"
        ):
            src_obj = self.master.get_object(self.connection.src)
            if src_obj and src_obj.obj_type == "Decision":
                ttk.Label(master, text="Guard:").grid(
                    row=row, column=0, sticky="ne", padx=4, pady=4
                )
                self.guard_list = tk.Listbox(master, height=4)
                for g in self.connection.guard:
                    self.guard_list.insert(tk.END, g)
                self.guard_list.grid(row=row, column=1, padx=4, pady=4, sticky="we")
                gbtn = ttk.Frame(master)
                gbtn.grid(row=row, column=2, padx=2)
                ttk.Button(gbtn, text="Add", command=self.add_guard).pack(side=tk.TOP)
                ttk.Button(gbtn, text="Remove", command=self.remove_guard).pack(side=tk.TOP)
                row += 1
                ttk.Label(master, text="Guard Ops:").grid(
                    row=row, column=0, sticky="ne", padx=4, pady=4
                )
                self.guard_ops_list = tk.Listbox(master, height=4)
                for op in self.connection.guard_ops:
                    self.guard_ops_list.insert(tk.END, op)
                self.guard_ops_list.grid(row=row, column=1, padx=4, pady=4, sticky="we")
                opbtn = ttk.Frame(master)
                opbtn.grid(row=row, column=2, padx=2)
                self.guard_op_choice = tk.StringVar(value="AND")
                ttk.Combobox(
                    opbtn,
                    textvariable=self.guard_op_choice,
                    values=["AND", "OR"],
                    state="readonly",
                ).pack(side=tk.TOP)
                ttk.Button(opbtn, text="Add", command=self.add_guard_op).pack(
                    side=tk.TOP
                )
                ttk.Button(opbtn, text="Remove", command=self.remove_guard_op).pack(
                    side=tk.TOP
                )
                row += 1

        if self.connection.conn_type in ("Aggregation", "Composite Aggregation"):
            ttk.Label(master, text="Multiplicity:").grid(row=row, column=0, sticky="e", padx=4, pady=4)
            self.mult_var = tk.StringVar(value=self.connection.multiplicity)
            ttk.Combobox(
                master,
                textvariable=self.mult_var,
                values=["1", "0..1", "1..*", "0..*", "2", "3", "4", "5"],
            ).grid(row=row, column=1, padx=4, pady=4, sticky="we")

    def add_point(self):
        x = simpledialog.askfloat("Point", "X:", parent=self)
        y = simpledialog.askfloat("Point", "Y:", parent=self)
        if x is not None and y is not None:
            self.point_list.insert(tk.END, f"{x},{y}")

    def remove_point(self):
        sel = list(self.point_list.curselection())
        for idx in reversed(sel):
            self.point_list.delete(idx)

    def add_guard(self):
        txt = simpledialog.askstring("Guard", "Condition:", parent=self)
        if txt:
            self.guard_list.insert(tk.END, txt)

    def remove_guard(self):
        sel = list(self.guard_list.curselection())
        for idx in reversed(sel):
            self.guard_list.delete(idx)

    def add_guard_op(self):
        op = self.guard_op_choice.get()
        self.guard_ops_list.insert(tk.END, op)

    def remove_guard_op(self):
        sel = list(self.guard_ops_list.curselection())
        for idx in reversed(sel):
            self.guard_ops_list.delete(idx)

    def apply(self):
        self.connection.name = self.name_var.get()
        self.connection.style = self.style_var.get()
        pts = []
        for i in range(self.point_list.size()):
            txt = self.point_list.get(i)
            try:
                x_str, y_str = txt.split(",")
                pts.append((float(x_str), float(y_str)))
            except ValueError:
                continue
        self.connection.points = pts
        self.connection.arrow = self.arrow_var.get()
        self.connection.mid_arrow = self.mid_var.get()
        if hasattr(self, "mult_var"):
            self.connection.multiplicity = self.mult_var.get()
        if hasattr(self, "guard_list"):
            self.connection.guard = [self.guard_list.get(i) for i in range(self.guard_list.size())]
        if hasattr(self, "guard_ops_list"):
            self.connection.guard_ops = [
                self.guard_ops_list.get(i) for i in range(self.guard_ops_list.size())
            ]
        if hasattr(self, "elem_var"):
            sel = self.elem_var.get()
            self.connection.element_id = self.elem_map.get(sel, "")
            if self.connection.element_id:
                repo = SysMLRepository.get_instance()
                elem = repo.elements.get(self.connection.element_id)
                if elem and not self.connection.name:
                    self.connection.name = elem.name
                if hasattr(self.master, "repo"):
                    self.master.repo.add_element_to_diagram(
                        self.master.diagram_id, self.connection.element_id
                    )
        if hasattr(self.master, "_sync_to_repository"):
            self.master._sync_to_repository()
        if self.connection.conn_type in ("Aggregation", "Composite Aggregation"):
            if hasattr(self.master, "repo"):
                whole = self.master.get_object(self.connection.src).element_id
                part = self.master.get_object(self.connection.dst).element_id
                if self.connection.conn_type == "Composite Aggregation":
                    add_composite_aggregation_part(
                        self.master.repo,
                        whole,
                        part,
                        self.connection.multiplicity,
                        app=getattr(self.master, "app", None),
                    )
                else:
                    add_aggregation_part(
                        self.master.repo,
                        whole,
                        part,
                        self.connection.multiplicity,
                        app=getattr(self.master, "app", None),
                    )
                if hasattr(self.master, "_sync_to_repository"):
                    self.master._sync_to_repository()


class UseCaseDiagramWindow(SysMLDiagramWindow):
    def __init__(self, master, app, diagram_id: str | None = None, history=None):
        tool_groups = {
            "Nodes": ["Actor", "Use Case"],
            "Boundary": ["System Boundary"],
        }
        tools = [t for group in tool_groups.values() for t in group]
        rel_tools = [
            "Association",
            "Communication Path",
            "Generalize",
            "Include",
            "Extend",
        ]
        try:
            super().__init__(
                master,
                "Use Case Diagram",
                tools,
                diagram_id,
                app=app,
                history=history,
                relation_tools=rel_tools,
                tool_groups=tool_groups,
            )
        except TypeError:
            super().__init__(
                master,
                "Use Case Diagram",
                tools + rel_tools,
                diagram_id,
                app=app,
                history=history,
            )
        if not hasattr(self, "tools_frame"):
            self.tools_frame = self.toolbox


class ActivityDiagramWindow(SysMLDiagramWindow):
    def __init__(self, master, app, diagram_id: str | None = None, history=None):
        tool_groups = {
            "Actions": ["Action", "CallBehaviorAction"],
            "Control Nodes": [
                "Initial",
                "Final",
                "Decision",
                "Merge",
                "Fork",
                "Join",
            ],
            "Boundary": ["System Boundary"],
        }
        tools = [t for group in tool_groups.values() for t in group]
        rel_tools = ["Flow"]
        try:
            super().__init__(
                master,
                "Activity Diagram",
                tools,
                diagram_id,
                app=app,
                history=history,
                relation_tools=rel_tools,
                tool_groups=tool_groups,
            )
        except TypeError:
            super().__init__(
                master,
                "Activity Diagram",
                tools + rel_tools,
                diagram_id,
                app=app,
                history=history,
            )
        if not hasattr(self, "tools_frame"):
            self.tools_frame = self.toolbox
        ttk.Button(
            self.toolbox,
            text="Add Block Operations",
            command=self.add_block_operations,
        ).pack(fill=tk.X, padx=2, pady=2)

    class SelectOperationsDialog(simpledialog.Dialog):
        def __init__(self, parent, operations):
            self.operations = operations
            self.selected = {}
            super().__init__(parent, title="Select Operations")

        def body(self, master):
            ttk.Label(master, text="Select operations:").pack(padx=5, pady=5)
            frame = ttk.Frame(master)
            frame.pack(fill=tk.BOTH, expand=True)
            canvas = tk.Canvas(frame, borderwidth=0)
            scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
            self.check_frame = ttk.Frame(canvas)
            self.check_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=self.check_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            for label, op, diag in self.operations:
                var = tk.BooleanVar(value=True)
                self.selected[(op, diag)] = var
                ttk.Checkbutton(self.check_frame, text=label, variable=var).pack(anchor="w", padx=2, pady=2)
            return self.check_frame

        def apply(self):
            self.result = [(op, diag) for (op, diag), var in self.selected.items() if var.get()]

    def add_block_operations(self):
        repo = self.repo
        blocks = []
        for elem in repo.elements.values():
            if elem.elem_type != "Block":
                continue
            for beh in parse_behaviors(elem.properties.get("behaviors", "")):
                if beh.diagram == self.diagram_id:
                    blocks.append(elem)
                    break
        operations = []
        for blk in blocks:
            ops = parse_operations(blk.properties.get("operations", ""))
            behs = {b.operation: b.diagram for b in parse_behaviors(blk.properties.get("behaviors", ""))}
            for op in ops:
                diag_id = behs.get(op.name)
                if diag_id:
                    label = f"{blk.name}.{format_operation(op)}"
                    operations.append((label, op.name, diag_id))
        if not operations:
            messagebox.showinfo("Add Block Operations", "No operations available")
            return
        dlg = self.SelectOperationsDialog(self, operations)
        selected = dlg.result or []
        if not selected:
            return
        diag = repo.diagrams.get(self.diagram_id)
        base_x = 50.0
        base_y = 50.0
        offset = 60.0
        for idx, (op_name, d_id) in enumerate(selected):
            elem = repo.create_element("CallBehaviorAction", name=op_name, owner=diag.package)
            repo.add_element_to_diagram(self.diagram_id, elem.elem_id)
            repo.link_diagram(elem.elem_id, d_id)
            obj = SysMLObject(
                _get_next_id(),
                "CallBehaviorAction",
                base_x,
                base_y + offset * idx,
                element_id=elem.elem_id,
                properties={"name": op_name},
                phase=_repo_phase(repo),
            )
            diag.objects.append(obj.__dict__)
            self.objects.append(obj)
        self.redraw()
        self._sync_to_repository()


class GovernanceDiagramWindow(SysMLDiagramWindow):
    def __init__(self, master, app, diagram_id: str | None = None, history=None):
        tool_groups = {
            "Tasks": ["Action"],
            "Control Nodes": ["Initial", "Final", "Decision", "Merge"],
            "Boundary": ["System Boundary"],
        }
        tools = ["Select"] + [t for group in tool_groups.values() for t in group]
        # Include flow connections in the left-hand governance relationships
        # toolbox so users can create them alongside other governance tools.
        rel_tools: list[str] = ["Flow"]
        try:
            super().__init__(
                master,
                "Governance Diagram",
                tools,
                diagram_id,
                app=app,
                history=history,
                relation_tools=rel_tools,
                tool_groups=tool_groups,
            )
        except TypeError:
            super().__init__(
                master,
                "Governance Diagram",
                tools + rel_tools,
                diagram_id,
                app=app,
                history=history,
            )
        if not hasattr(self, "tools_frame"):
            self.tools_frame = self.toolbox

        tool_buttons = getattr(self, "tool_buttons", None)
        btn = tool_buttons.get("Action") if tool_buttons else None
        if btn:
            btn.configure(text="Task")
            self.tool_buttons["Task"] = self.tool_buttons.pop("Action")
        # Ensure legacy control nodes are removed from the toolbox
        tool_btns = getattr(self, "tool_buttons", {})
        for legacy in ("Fork", "Join"):
            extra = tool_btns.pop(legacy, None)
            if extra:
                try:
                    extra.destroy()
                except Exception:  # pragma: no cover - headless tests
                    pass

        # ------------------------------------------------------------------
        # Toolbox selector built from diagram rules
        # ------------------------------------------------------------------
        self._toolbox_frames: dict[str, list] = {}
        try:
            self.toolbox_var = tk.StringVar()
        except Exception:  # pragma: no cover - headless tests
            class _Var:
                def __init__(self):
                    self._v = ""

                def get(self):
                    return self._v

                def set(self, v):
                    self._v = v

            self.toolbox_var = _Var()
        if hasattr(self.toolbox, "tk"):
            self.toolbox_selector = ttk.Combobox(
                self.toolbox, state="readonly", textvariable=self.toolbox_var
            )
            self.toolbox_selector.pack(fill=tk.X, padx=2, pady=2)
            self.toolbox_selector.bind("<<ComboboxSelected>>", lambda e: self._switch_toolbox())
        else:  # pragma: no cover - headless tests
            self.toolbox_selector = types.SimpleNamespace(
                pack=lambda *a, **k: None,
                bind=lambda *a, **k: None,
                configure=lambda *a, **k: None,
            )

        self._rebuild_toolboxes()
        ARCH_WINDOWS.add(weakref.ref(self))

        canvas_frame = self.canvas.master
        canvas_frame.pack_forget()

        canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self._activate_parent_phase()
        self.refresh_from_repository()
        self.select_tool("Select")
        self._pending_wp_name: str | None = None
        self._pending_wp_step: str = ""
        self._pending_wp_lock: bool = True

    def _activate_parent_phase(self) -> None:
        """Activate the lifecycle phase containing this diagram.

        When a Governance diagram window is opened, switch the application's active
        lifecycle phase to the module that owns the diagram. Any tooling not
        enabled for that phase is hidden via ``on_lifecycle_selected`` or
        ``refresh_tool_enablement``.
        """

        app = getattr(self, "app", None)
        if not app or not getattr(app, "safety_mgmt_toolbox", None):
            return
        toolbox = app.safety_mgmt_toolbox
        diag = self.repo.diagrams.get(self.diagram_id)
        if not diag:
            return
        name = diag.name or ""
        phase = toolbox.module_for_diagram(name)
        if not phase:
            return
        toolbox.activate_phase(phase, app)

    def _on_focus_in(self, event=None):
        self._activate_parent_phase()
        super()._on_focus_in(event)

    # ------------------------------------------------------------------
    # Dynamic toolbox construction
    # ------------------------------------------------------------------
    def _rebuild_toolboxes(self) -> None:
        defs = _toolbox_defs()
        ai_data = defs.pop("Safety & AI Lifecycle", None)
        # Exclude relationships already available in the global relationships
        # toolbox.  Without this filtering a relation like ``Flow`` added to the
        # left-hand toolbox via ``relation_tools`` would also appear under each
        # category that referenced it, leading to duplicate buttons when
        # switching categories.
        global_rels = set(getattr(self, "relation_tools", []) or [])
        if global_rels:
            for data in defs.values():
                data["relations"] = [
                    r for r in data.get("relations", []) if r not in global_rels
                ]
                for sub in data.get("externals", {}).values():
                    sub["relations"] = [
                        r for r in sub.get("relations", []) if r not in global_rels
                    ]
            if ai_data:
                ai_data["relations"] = [
                    r for r in ai_data.get("relations", []) if r not in global_rels
                ]
                for sub in ai_data.get("externals", {}).values():
                    sub["relations"] = [
                        r for r in sub.get("relations", []) if r not in global_rels
                    ]
        seen_rels: set[str] = set()
        for name, data in defs.items():
            if name == "Governance Core":
                _dedup_category(data)
            else:
                _dedup_category(data, seen_rels)
        if ai_data:
            _dedup_category(ai_data, seen_rels)
        if hasattr(self.tools_frame, "pack_forget"):
            self.tools_frame.pack_forget()
        if getattr(self, "rel_frame", None) and hasattr(self.rel_frame, "pack_forget"):
            self.rel_frame.pack_forget()
        for frames in getattr(self, "_toolbox_frames", {}).values():
            for fr in frames:
                if fr not in (self.tools_frame, getattr(self, "rel_frame", None)) and hasattr(fr, "destroy"):
                    fr.destroy()
        self._toolbox_frames = {}
        self._frame_loaders: dict[str, Callable[[], object]] = {}
        if hasattr(self.toolbox, "tk"):
            action_frame = ttk.Frame(self.toolbox)
            cmds = [
                ("Add Work Product", self.add_work_product),
                ("Add Generic Work Product", self.add_generic_work_product),
                ("Add Lifecycle Phase", self.add_lifecycle_phase),
            ]
            for name, cmd in cmds:
                TranslucidButton(
                    action_frame,
                    text=name,
                    image=self._icon_for(name),
                    compound=tk.LEFT,
                    command=cmd,
                ).pack(fill=tk.X, padx=2, pady=2)
        else:  # pragma: no cover - headless tests
            action_frame = types.SimpleNamespace(
                pack=lambda *a, **k: None,
                pack_forget=lambda *a, **k: None,
                destroy=lambda *a, **k: None,
            )

        def build_frame(name: str, data: dict):
            if not data:
                return types.SimpleNamespace(
                    pack=lambda *a, **k: None,
                    pack_forget=lambda *a, **k: None,
                    destroy=lambda *a, **k: None,
                )
            if hasattr(self.toolbox, "tk"):
                frame = _labelframe(self.toolbox, text=name)
                if data.get("nodes"):
                    elem = _labelframe(
                        frame,
                        text="Elements",
                    )
                    elem.pack(fill=tk.X, padx=2, pady=2)
                    for node in data["nodes"]:
                        TranslucidButton(
                            elem,
                            text=node,
                            image=self._icon_for(node),
                            compound=tk.LEFT,
                            command=lambda t=node: self.select_tool(t),
                        ).pack(fill=tk.X, padx=2, pady=2)
                if data.get("relations"):
                    rel = _labelframe(
                        frame,
                        text="Relationships",
                    )
                    rel.pack(fill=tk.X, padx=2, pady=2)
                    for rel_name in data["relations"]:
                        TranslucidButton(
                            rel,
                            text=rel_name,
                            image=self._icon_for(rel_name),
                            compound=tk.LEFT,
                            command=lambda t=rel_name: self.select_tool(t),
                        ).pack(fill=tk.X, padx=2, pady=2)
                for grp, sub in data.get("externals", {}).items():
                    sub_frame = _labelframe(
                        frame,
                        text=f"Related {grp}",
                    )
                    sub_frame.pack(fill=tk.X, padx=2, pady=2)
                    if sub.get("nodes"):
                        selem = _labelframe(
                            sub_frame,
                            text="Elements",
                        )
                        selem.pack(fill=tk.X, padx=2, pady=2)
                        for node in sub["nodes"]:
                            TranslucidButton(
                                selem,
                                text=node,
                                image=self._icon_for(node),
                                compound=tk.LEFT,
                                command=lambda t=node: self.select_tool(t),
                            ).pack(fill=tk.X, padx=2, pady=2)
                    if sub.get("relations"):
                        srel = _labelframe(
                            sub_frame,
                            text="Relationships",
                        )
                        srel.pack(fill=tk.X, padx=2, pady=2)
                        for rel_name in sub["relations"]:
                            TranslucidButton(
                                srel,
                                text=rel_name,
                                image=self._icon_for(rel_name),
                                compound=tk.LEFT,
                                command=lambda t=rel_name: self.select_tool(t),
                            ).pack(fill=tk.X, padx=2, pady=2)
            else:  # pragma: no cover - headless tests
                frame = types.SimpleNamespace(
                    pack=lambda *a, **k: None,
                    pack_forget=lambda *a, **k: None,
                    destroy=lambda *a, **k: None,
                )
            return frame

        # Build loaders for each category. Governance Core includes the action
        # buttons while other categories only load their specific frames when
        # first displayed.
        for name, data in defs.items():
            frames = [self.tools_frame]
            if name == "Governance Core":
                frames.append(action_frame)
            self._toolbox_frames[name] = frames
            self._frame_loaders[name] = lambda data=data, name=name: build_frame(name, data)

        if ai_data:
            self._toolbox_frames["Safety & AI Lifecycle"] = [self.tools_frame]
            self._frame_loaders["Safety & AI Lifecycle"] = lambda data=ai_data: build_frame(
                "Safety & AI Lifecycle", data
            )

        options = sorted(self._toolbox_frames.keys())
        if "Governance Core" in options:
            options.remove("Governance Core")
            options = ["Governance Core"] + options
        self.toolbox_selector.configure(values=options)
        current = self.toolbox_var.get()
        if current not in options:
            self.toolbox_var.set(options[0] if options else "")
        self._switch_toolbox()

    def _switch_toolbox(self) -> None:
        choice = self.toolbox_var.get()
        for frames in self._toolbox_frames.values():
            for frame in frames:
                if frame and hasattr(frame, "pack_forget"):
                    frame.pack_forget()
        frames = self._toolbox_frames.get(choice, [])
        key = f"toolbox:{choice}"
        if choice in getattr(self, "_frame_loaders", {}):
            loader = self._frame_loaders.pop(choice)
            frame = memory_manager.lazy_load(key, loader)
            frames.append(frame)
        else:
            memory_manager.mark_active(key)
        for frame in frames:
            if frame and hasattr(frame, "pack"):
                frame.pack(fill=tk.X, padx=2, pady=2)
        memory_manager.cleanup()

    class _SelectDialog(simpledialog.Dialog):  # pragma: no cover - requires tkinter
        def __init__(self, parent, title: str, options: list[str]):
            self.options = options
            self.selection = ""
            super().__init__(parent, title)

        def body(self, master):  # pragma: no cover - requires tkinter
            ttk.Label(master, text="Select:").pack(padx=5, pady=5)
            self.var = tk.StringVar(value=self.options[0] if self.options else "")
            combo = ttk.Combobox(
                master,
                textvariable=self.var,
                values=self.options,
                state="readonly",
            )
            combo.pack(padx=5, pady=5)
            return combo

        def apply(self):  # pragma: no cover - requires tkinter
            self.selection = self.var.get()

    def add_work_product(self):  # pragma: no cover - requires tkinter
        if not getattr(self, "canvas", None):
            objs = getattr(self, "objects", [])
            areas = [o for o in objs if o.obj_type == "System Boundary"]
            existing = {a.properties.get("name", ""): a for a in areas}
            if len(areas) == 1:
                # Give the user a chance to select a different area; if they
                # cancel the dialog we automatically use the existing one.
                area_name = self._select_process_area()
                if not area_name:
                    area = areas[0]
                    area_name = area.properties.get("name", "")
                else:
                    area = existing.get(area_name)
                    if area is None:
                        area = self._place_process_area(area_name, 100.0, 100.0)
            else:
                area_name = self._select_process_area()
                if not area_name:
                    return
                area = existing.get(area_name)
                if area is None:
                    area = self._place_process_area(area_name, 100.0, 100.0)
            wp_name = self._select_work_product_for_area(area_name)
            if not wp_name:
                return
            self._place_work_product(wp_name, 100.0, 100.0, area=area)
        else:
            self._pending_wp_step = "loc"
            try:
                self.canvas.configure(cursor="crosshair")
            except Exception:
                pass

    def _select_process_area(self) -> str:  # pragma: no cover - requires tkinter
        dlg = self._SelectDialog(self, "Add Process Area", PROCESS_AREA_OPTIONS)
        return getattr(dlg, "selection", "")

    def _select_work_product_for_area(self, area_name: str) -> str:  # pragma: no cover - requires tkinter
        options = _work_products_for_area(area_name)
        dlg = self._SelectDialog(self, "Add Work Product", options)
        return getattr(dlg, "selection", "")

    def add_generic_work_product(self):  # pragma: no cover - requires tkinter
        name = simpledialog.askstring("Add Work Product", "Enter work product name:")
        if not name:
            return
        name = name.strip()
        if not name:
            return
        existing = {wp.lower() for wp in getattr(self.app, "WORK_PRODUCT_INFO", {})}
        if name.lower() in existing:
            messagebox.showerror(
                "Duplicate Work Product",
                f"'{name}' is already a defined work product.",
            )
            return
        if not getattr(self, "canvas", None):
            self._place_work_product(name, 100.0, 100.0, lock_name=False)
        else:
            self._pending_wp_name = name
            self._pending_wp_lock = False
            try:
                self.canvas.configure(cursor="crosshair")
            except Exception:
                pass

    def _place_work_product(
        self,
        name: str,
        x: float,
        y: float,
        *,
        lock_name: bool = True,
        area: SysMLObject | None = None,
    ) -> SysMLObject:
        if getattr(self.app, "push_undo_state", None):
            self.app.push_undo_state()
        props = {"name": name}
        if lock_name:
            props["name_locked"] = "1"
        if area:
            props["parent"] = str(area.obj_id)
        obj = SysMLObject(
            _get_next_id(),
            "Work Product",
            x,
            y,
            width=60.0,
            height=80.0,
            properties=props,
            phase=_repo_phase(self.repo),
        )
        if area:
            self._constrain_to_parent(obj, area)
        self.objects.append(obj)
        self.sort_objects()
        self._sync_to_repository()
        self.redraw()
        toolbox = getattr(self.app, "safety_mgmt_toolbox", None)
        if toolbox:
            diag = self.repo.diagrams.get(self.diagram_id)
            diagram_name = diag.name if diag else ""
            toolbox.add_work_product(diagram_name, name, "")
        if getattr(self.app, "enable_work_product", None):
            self.app.enable_work_product(name)
        if getattr(self.app, "refresh_tool_enablement", None):
            self.app.refresh_tool_enablement()
        if getattr(self.app, "push_undo_state", None):
            self.app.push_undo_state()
        return obj

    def _place_process_area(self, name: str, x: float, y: float) -> SysMLObject:
        obj = SysMLObject(
            _get_next_id(),
            "System Boundary",
            x,
            y,
            width=200.0,
            height=150.0,
            properties={"name": name, "name_locked": "1"},
            phase=_repo_phase(self.repo),
        )
        self.objects.insert(0, obj)
        self.sort_objects()
        self._sync_to_repository()
        self.redraw()
        if getattr(self.app, "enable_process_area", None):
            self.app.enable_process_area(name)
        return obj

    def _constrain_to_parent(
        self, obj: SysMLObject, area: SysMLObject | None = None
    ) -> None:
        if obj.obj_type != "Work Product":
            return
        if area is None:
            pid = obj.properties.get("parent") or obj.properties.get("boundary")
            if not pid:
                return
            area = self.get_object(int(pid))
        if not area:
            return
        left = area.x - area.width / 2 + obj.width / 2
        right = area.x + area.width / 2 - obj.width / 2
        top = area.y - area.height / 2 + obj.height / 2
        bottom = area.y + area.height / 2 - obj.height / 2
        # Clamp coordinates to the process area so work products cannot escape.
        obj.x = min(max(obj.x, left), right)
        obj.y = min(max(obj.y, top), bottom)
        obj.properties["px"] = str(obj.x - area.x)
        obj.properties["py"] = str(obj.y - area.y)

    def on_left_press(self, event):  # pragma: no cover - requires tkinter
        if self.repo.diagram_read_only(self.diagram_id):
            return
        pending_click = getattr(self, "_pending_wp_click", False)
        if pending_click:
            self._pending_wp_click = False
            x = self.canvas.canvasx(event.x) / self.zoom
            y = self.canvas.canvasy(event.y) / self.zoom
            area_opts = [
                "System Design (Item Definition)",
                "Hazard & Threat Analysis",
                "Risk Assessment",
                "Safety & Security Management",
                "Safety Analysis",
                "Scenario",
            ]
            dlg = self._SelectDialog(self, "Add Process Area", area_opts)
            area_name = getattr(dlg, "selection", "")
            if not area_name:
                try:
                    self.canvas.configure(cursor="arrow")
                except Exception:
                    pass
                return
            area_obj = self._place_process_area(area_name, x, y)
            wp_options = [
                "Architecture Diagram",
                "Safety & Security Concept",
                "Mission Profile",
                "Reliability Analysis",
                "Causal Bayesian Network Analysis",
                "Safety & Security Case",
                "GSN Argumentation",
                *REQUIREMENT_WORK_PRODUCTS,
                "HAZOP",
                "STPA",
                "Threat Analysis",
                "FI2TC",
                "TC2FI",
                "Risk Assessment",
                "Product Goal Specification",
                "FTA",
                "FMEA",
                "FMEDA",
                "Scenario Library",
                "ODD",
            ]
            wp_options = list(dict.fromkeys(wp_options))
            area_map = {
                "Architecture Diagram": "System Design (Item Definition)",
                "Safety & Security Concept": "System Design (Item Definition)",
                "Mission Profile": "Safety Analysis",
                "Reliability Analysis": "Safety Analysis",
                "Causal Bayesian Network Analysis": "Safety Analysis",
                "Safety & Security Case": "Safety & Security Management",
                "GSN Argumentation": "Safety & Security Management",
                "Product Goal Specification": "System Design (Item Definition)",
                **{wp: "System Design (Item Definition)" for wp in REQUIREMENT_WORK_PRODUCTS},
                "HAZOP": "Hazard & Threat Analysis",
                "STPA": "Hazard & Threat Analysis",
                "Threat Analysis": "Hazard & Threat Analysis",
                "FI2TC": "Hazard & Threat Analysis",
                "TC2FI": "Hazard & Threat Analysis",
                "Risk Assessment": "Risk Assessment",
                "FTA": "Safety Analysis",
                "FMEA": "Safety Analysis",
                "FMEDA": "Safety Analysis",
                "Scenario Library": "Scenario",
                "ODD": "Scenario",
            }
            wp_options = [opt for opt in wp_options if area_map.get(opt) == area_name]
            dlg2 = self._SelectDialog(self, "Add Work Product", wp_options)
            name = getattr(dlg2, "selection", "")
            if name:
                self._place_work_product(name, area_obj.x, area_obj.y, boundary=area_obj)
            try:
                self.canvas.configure(cursor="arrow")
            except Exception:
                pass
            return

        pending_wp = getattr(self, "_pending_wp_name", None)
        step = getattr(self, "_pending_wp_step", "")
        if step == "loc":
            x = self.canvas.canvasx(event.x) / self.zoom
            y = self.canvas.canvasy(event.y) / self.zoom
            self._pending_wp_step = ""
            try:
                self.canvas.configure(cursor="arrow")
            except Exception:
                pass
            area = self.find_boundary_at(x, y)
            if area:
                area_name = area.properties.get("name", "")
                wp_name = self._select_work_product_for_area(area_name)
                if not wp_name:
                    return
                self._place_work_product(wp_name, x, y, area=area)
                return
            area_name = self._select_process_area()
            if not area_name:
                return
            area = self._place_process_area(area_name, x, y)
            wp_name = self._select_work_product_for_area(area_name)
            if not wp_name:
                return
            self._place_work_product(wp_name, x, y, area=area)
            return
        if pending_wp:
            x = self.canvas.canvasx(event.x) / self.zoom
            y = self.canvas.canvasy(event.y) / self.zoom
            self._pending_wp_name = None
            lock = getattr(self, "_pending_wp_lock", True)
            self._pending_wp_lock = True
            self._place_work_product(pending_wp, x, y, lock_name=lock)
            try:
                self.canvas.configure(cursor="arrow")
            except Exception:
                pass
            return
        orig_tool = self.current_tool
        if orig_tool == "Task":
            self.current_tool = "Action"
        try:
            super().on_left_press(event)
        finally:
            self.current_tool = orig_tool

    def add_lifecycle_phase(self):  # pragma: no cover - requires tkinter
        toolbox = getattr(self.app, "safety_mgmt_toolbox", None)
        if not toolbox:
            return

        def _collect(mod, prefix=""):
            path = f"{prefix}{mod.name}" if prefix else mod.name
            names.append(path)
            for sub in mod.modules:
                _collect(sub, path + "/")

        names: List[str] = []
        for mod in getattr(toolbox, "modules", []):
            _collect(mod)
        if not names:
            return

        dlg = self._SelectDialog(self, "Add Lifecycle Phase", names)
        name = getattr(dlg, "selection", "")
        if not name:
            return
        obj = SysMLObject(
            _get_next_id(),
            "Lifecycle Phase",
            100.0,
            100.0,
            width=120.0,
            height=80.0,
            properties={"name": name, "name_locked": "1"},
            phase=_repo_phase(self.repo),
        )
        self.objects.append(obj)
        self.sort_objects()
        self._sync_to_repository()
        self.redraw()


class BlockDiagramWindow(SysMLDiagramWindow):
    def __init__(self, master, app, diagram_id: str | None = None, history=None):
        tool_groups = {"Blocks": ["Block"]}
        tools = [t for group in tool_groups.values() for t in group]
        rel_tools = [
            "Association",
            "Generalization",
            "Aggregation",
            "Composite Aggregation",
        ]
        try:
            super().__init__(
                master,
                "Block Diagram",
                tools,
                diagram_id,
                app=app,
                history=history,
                relation_tools=rel_tools,
                tool_groups=tool_groups,
            )
        except TypeError:
            super().__init__(
                master,
                "Block Diagram",
                tools + rel_tools,
                diagram_id,
                app=app,
                history=history,
            )
        if not hasattr(self, "tools_frame"):
            self.tools_frame = self.toolbox
        ttk.Button(
            self.toolbox,
            text="Add Blocks",
            command=self.add_blocks,
        ).pack(fill=tk.X, padx=2, pady=2)

    def _add_block_relationships(self) -> None:
        """Add connections for any existing relationships between blocks."""
        repo = self.repo
        diag = repo.diagrams.get(self.diagram_id)
        if not diag:
            return
        obj_map = {
            o.element_id: o.obj_id
            for o in self.objects
            if o.obj_type == "Block" and o.element_id
        }
        existing = {
            (c.src, c.dst, c.conn_type)
            for c in self.connections
        } | {
            (c.dst, c.src, c.conn_type)
            for c in self.connections
        }
        for rel in repo.relationships:
            if rel.rel_type not in (
                "Association",
                "Generalization",
                "Aggregation",
                "Composite Aggregation",
            ):
                continue
            if rel.source in obj_map and rel.target in obj_map:
                src_id = obj_map[rel.source]
                dst_id = obj_map[rel.target]
                if (src_id, dst_id, rel.rel_type) in existing:
                    continue
                if (dst_id, src_id, rel.rel_type) in existing:
                    continue
                conn = DiagramConnection(
                    src_id,
                    dst_id,
                    rel.rel_type,
                    arrow="forward" if rel.rel_type == "Generalization" else "none",
                    stereotype=rel.stereotype or "",
                )
                self.connections.append(conn)
                diag.connections.append(conn.__dict__)
                repo.add_relationship_to_diagram(self.diagram_id, rel.rel_id)

    def add_blocks(self) -> None:
        repo = self.repo
        diag = repo.diagrams.get(self.diagram_id)
        if not diag:
            return
        existing = {
            o.element_id
            for o in self.objects
            if o.obj_type == "Block" and o.element_id
        }
        candidates = set()
        for d in repo.diagrams.values():
            if d.diag_type != "Block Diagram" or d.diag_id == self.diagram_id:
                continue
            for obj in getattr(d, "objects", []):
                if obj.get("obj_type") == "Block" and obj.get("element_id"):
                    candidates.add(obj["element_id"])
        names = []
        id_map = {}
        for bid in candidates:
            if bid in existing or bid not in repo.elements:
                continue
            name = repo.elements[bid].name or bid
            names.append(name)
            id_map[name] = bid
        if not names:
            messagebox.showinfo("Add Blocks", "No blocks available")
            return
        dlg = SysMLObjectDialog.SelectNamesDialog(self, names, title="Add Blocks")
        selected = dlg.result or []
        if not selected:
            return
        base_x = 50.0
        base_y = 50.0
        offset = 180.0
        for idx, name in enumerate(selected):
            blk_id = id_map.get(name)
            if not blk_id:
                continue
            repo.add_element_to_diagram(self.diagram_id, blk_id)
            elem = repo.elements.get(blk_id)
            props = elem.properties.copy() if elem else {}
            props["name"] = elem.name if elem else blk_id
            obj = SysMLObject(
                _get_next_id(),
                "Block",
                base_x,
                base_y + offset * idx,
                element_id=blk_id,
                width=160.0,
                height=140.0,
                properties=props,
                phase=_repo_phase(repo),
            )
            diag.objects.append(obj.__dict__)
            self.objects.append(obj)
        if hasattr(self, "_add_block_relationships"):
            self._add_block_relationships()
        self.redraw()
        self._sync_to_repository()


class InternalBlockDiagramWindow(SysMLDiagramWindow):
    def __init__(self, master, app, diagram_id: str | None = None, history=None):
        tool_groups = {"Structure": ["Part"], "Ports": ["Port"]}
        tools = [t for group in tool_groups.values() for t in group]
        rel_tools = ["Connector"]
        try:
            super().__init__(
                master,
                "Internal Block Diagram",
                tools,
                diagram_id,
                app=app,
                history=history,
                relation_tools=rel_tools,
                tool_groups=tool_groups,
            )
        except TypeError:
            super().__init__(
                master,
                "Internal Block Diagram",
                tools + rel_tools,
                diagram_id,
                app=app,
                history=history,
            )
        if not hasattr(self, "tools_frame"):
            self.tools_frame = self.toolbox
        ttk.Button(
            self.toolbox,
            text="Add Contained Parts",
            command=self.add_contained_parts,
        ).pack(fill=tk.X, padx=2, pady=2)

    def _get_failure_modes(self, comp_name: str) -> str:
        """Return comma separated failure modes for a component name."""
        app = getattr(self, "app", None)
        modes = set()
        for e in getattr(app, "fmea_entries", []):
            if getattr(e, "fmea_component", "") == comp_name:
                label = getattr(e, "description", "") or getattr(e, "user_name", "")
                if label:
                    modes.add(label)
        for fmea in getattr(app, "fmeas", []):
            for entry in fmea.get("entries", []):
                if getattr(entry, "fmea_component", "") == comp_name:
                    label = getattr(entry, "description", "") or getattr(entry, "user_name", "")
                    if label:
                        modes.add(label)
        return ", ".join(sorted(modes))

    def _get_part_name(self, obj: SysMLObject) -> str:
        repo = self.repo
        name = ""
        has_name = False
        def_id = obj.properties.get("definition")
        if obj.element_id and obj.element_id in repo.elements:
            elem = repo.elements[obj.element_id]
            name = elem.name or elem.properties.get("component", "")
            def_id = def_id or elem.properties.get("definition")
            def_name = ""
            if def_id and def_id in repo.elements:
                def_name = repo.elements[def_id].name or def_id
            has_name = bool(name) and not _is_default_part_name(def_name, name)
        if not has_name:
            name = obj.properties.get("component", "")

        def_id = obj.properties.get("definition")
        def_name = ""
        mult = ""
        comp = obj.properties.get("component", "")
        if def_id and def_id in repo.elements:
            def_name = repo.elements[def_id].name or def_id
            diag = repo.diagrams.get(self.diagram_id)
            block_id = (
                getattr(diag, "father", None)
                or next(
                    (eid for eid, did in repo.element_diagrams.items() if did == self.diagram_id),
                    None,
                )
            )
            if block_id:
                for rel in repo.relationships:
                    if (
                        rel.rel_type in ("Aggregation", "Composite Aggregation")
                        and rel.source == block_id
                        and rel.target == def_id
                    ):
                        mult = rel.properties.get("multiplicity", "1")
                        if mult in ("", "1"):
                            mult = ""
                        break

        if obj.element_id and obj.element_id in repo.elements and not comp:
            comp = repo.elements[obj.element_id].properties.get("component", "")
        if comp and comp == def_name:
            comp = ""

        base = name
        index = None
        m = re.match(r"^(.*)\[(\d+)\]$", name)
        if m:
            base = m.group(1)
            index = int(m.group(2))
            base = f"{base} {index}"

        label = base
        if def_name:
            if mult:
                if ".." in mult:
                    upper = mult.split("..", 1)[1] or "*"
                    disp = f"{index or 1}..{upper}"
                elif mult == "*":
                    disp = f"{index or 1}..*"
                else:
                    disp = f"{index or 1}..{mult}"
                def_part = f"{def_name} [{disp}]"
            else:
                def_part = def_name
            if comp:
                def_part = f"{comp} / {def_part}"
            if label and def_part != label:
                label = f"{label} : {def_part}"
            elif not label:
                label = f" : {def_part}"

        return label

    def _get_part_key(self, obj: SysMLObject) -> str:
        """Return canonical key for identifying ``obj`` regardless of renaming."""
        repo = self.repo
        def_id = obj.properties.get("definition")
        if not def_id and obj.element_id and obj.element_id in repo.elements:
            def_id = repo.elements[obj.element_id].properties.get("definition")
        name = ""
        if def_id and def_id in repo.elements:
            name = repo.elements[def_id].name or def_id
        else:
            name = self._get_part_name(obj)
        return _part_prop_key(name)

    def add_contained_parts(self) -> None:
        repo = self.repo
        block_id = next((eid for eid, did in repo.element_diagrams.items() if did == self.diagram_id), None)
        if not block_id or block_id not in repo.elements:
            messagebox.showinfo("Add Contained Parts", "No block is linked to this diagram")
            return
        block = repo.elements[block_id]
        diag = repo.diagrams.get(self.diagram_id)

        # inherit and sync aggregation/composite parts
        added_parent = inherit_father_parts(repo, diag) if diag else []
        for data in added_parent:
            self.objects.append(SysMLObject(**data))
        added_agg = _sync_ibd_aggregation_parts(repo, block_id, app=getattr(self, "app", None))
        added_comp = _sync_ibd_composite_parts(repo, block_id, app=getattr(self, "app", None))
        for data in added_agg + added_comp:
            self.objects.append(SysMLObject(**data))

        ra_name = block.properties.get("analysis", "")
        analyses = getattr(self.app, "reliability_analyses", [])
        ra_map = {ra.name: ra for ra in analyses}
        ra = ra_map.get(ra_name)
        if ra_name and (not ra or not ra.components):
            messagebox.showinfo("Add Contained Parts", "Analysis has no components")
            return
        comps = list(ra.components) if ra_name and ra and ra.components else []

        # existing parts on the diagram
        visible: dict[str, list[SysMLObject]] = {}
        hidden: dict[str, list[SysMLObject]] = {}
        def_objs: dict[str, list[SysMLObject]] = {}
        for obj in self.objects:
            if obj.obj_type != "Part":
                continue
            key = getattr(self, "_get_part_key", self._get_part_name)(obj)
            def_id = obj.properties.get("definition")
            def_objs.setdefault(def_id or "", []).append(obj)
            if getattr(obj, "hidden", False):
                hidden.setdefault(key, []).append(obj)
            else:
                visible.setdefault(key, []).append(obj)

        part_names = [n.strip() for n in block.properties.get("partProperties", "").split(",") if n.strip()]
        comp_names = [c.name for c in comps]
        prop_map = { _part_prop_key(n): n for n in part_names }
        all_keys = set(prop_map) | set(visible) | set(hidden) | { _part_prop_key(n) for n in comp_names }
        display_map: dict[str, str] = {}
        for key in all_keys:
            if key in prop_map:
                display_map[key] = prop_map[key]
            elif key in visible:
                display_map[key] = self._get_part_name(visible[key][0])
            elif key in hidden:
                display_map[key] = self._get_part_name(hidden[key][0])
            else:
                comp = next((c for c in comps if _part_prop_key(c.name) == key), None)
                display_map[key] = comp.name if comp else key

        names_list = [display_map[k] for k in sorted(display_map)]
        visible_names = {display_map[k] for k in visible}
        hidden_names = {display_map[k] for k in hidden}

        placeholder_map: dict[str, tuple[str, str]] = {}
        for rel in repo.relationships:
            if rel.rel_type in ("Aggregation", "Composite Aggregation") and rel.source == block_id:
                mult = rel.properties.get("multiplicity", "")
                if not mult:
                    continue
                target = rel.target
                low, high = _parse_multiplicity_range(mult)
                expected = high if high is not None else low
                existing = def_objs.get(target, [])
                for i in range(len(existing), expected):
                    def_name = repo.elements[target].name or target
                    if ".." in mult:
                        upper = mult.split("..", 1)[1] or "*"
                        disp = f"{i+1}..{upper}"
                    elif mult == "*":
                        disp = f"{i+1}..*"
                    elif mult.isdigit() and mult == str(expected):
                        disp = mult
                    else:
                        disp = f"{i+1}..{mult}"
                    label = f" : {def_name} [{disp}]"
                    placeholder_map[label] = (target, mult)
                    names_list.append(label)

        dlg = SysMLObjectDialog.ManagePartsDialog(
            self, names_list, visible_names, hidden_names
        )
        selected = dlg.result
        if selected is None:
            # User cancelled the dialog -> keep current visibility unchanged
            return
        selected_keys = { _part_prop_key(n) for n in selected if n not in placeholder_map }
        selected_placeholders = [placeholder_map[n] for n in selected if n in placeholder_map]

        to_add_comps = [c for c in comps if _part_prop_key(c.name) in selected_keys and _part_prop_key(c.name) not in visible and _part_prop_key(c.name) not in hidden]
        to_add_names = [n for n in part_names if _part_prop_key(n) in selected_keys and _part_prop_key(n) not in visible and _part_prop_key(n) not in hidden]
        added_ph: list[dict] = []
        for def_id, mult in selected_placeholders:
            added_ph.extend(
                add_multiplicity_parts(
                    repo, block_id, def_id, mult, count=1, app=getattr(self, "app", None)
                )
            )
        if added_ph and not self.app:
            for data in added_ph:
                if not any(o.obj_id == data["obj_id"] for o in self.objects):
                    self.objects.append(SysMLObject(**data))

        for key, objs in visible.items():
            if key not in selected_keys:
                for obj in objs:
                    obj.hidden = True
        for key, objs in hidden.items():
            if key in selected_keys:
                for obj in objs:
                    obj.hidden = False

        base_x = 50.0
        base_y = 50.0
        offset = 60.0
        added = []
        for idx, comp in enumerate(to_add_comps):
            elem = repo.create_element(
                "Part",
                name=comp.name,
                properties={
                    "component": comp.name,
                    "fit": f"{comp.fit:.2f}",
                    "qualification": comp.qualification,
                    "failureModes": self._get_failure_modes(comp.name),
                },
                owner=repo.root_package.elem_id,
            )
            repo.add_element_to_diagram(self.diagram_id, elem.elem_id)
            obj = SysMLObject(
                _get_next_id(),
                "Part",
                base_x,
                base_y + offset * idx,
                element_id=elem.elem_id,
                properties=elem.properties.copy(),
                phase=_repo_phase(repo),
            )
            diag.objects.append(obj.__dict__)
            self.objects.append(obj)
            added.append(comp.name)

        if to_add_names:
            # Directly sync new part property parts to the repository without
            # updating windows. We then insert the returned objects ourselves so
            # we can ensure they are visible immediately.
            added_props = _sync_ibd_partproperty_parts(
                repo, block_id, names=to_add_names, app=None, hidden=True
            )
            for data in added_props:
                data["hidden"] = False
                # Avoid duplicates if the sync function already populated this
                # window via the application.
                if not any(o.obj_id == data["obj_id"] for o in self.objects):
                    self.objects.append(SysMLObject(**data))

        if added:
            names = [
                n.strip()
                for n in block.properties.get("partProperties", "").split(",")
                if n.strip()
            ]
            for name in added:
                if name not in names:
                    names.append(name)
            joined = ", ".join(names)
            block.properties["partProperties"] = joined
            inherit_block_properties(repo, block_id)
            joined = repo.elements[block_id].properties["partProperties"]
            for d in repo.diagrams.values():
                for o in getattr(d, "objects", []):
                    if o.get("element_id") == block_id:
                        o.setdefault("properties", {})["partProperties"] = joined

        # enforce multiplicity for aggregated parts
        added_mult = _enforce_ibd_multiplicity(
            repo, block_id, app=getattr(self, "app", None)
        )
        if added_mult and not self.app:
            for data in added_mult:
                if not any(o.obj_id == data["obj_id"] for o in self.objects):
                    self.objects.append(SysMLObject(**data))

        boundary = getattr(self, "get_ibd_boundary", lambda: None)()
        if boundary:
            ensure_boundary_contains_parts(boundary, self.objects)

        self.redraw()
        self._sync_to_repository()
        if self.app:
            self.app.update_views()


class ControlFlowDiagramWindow(SysMLDiagramWindow):
    def __init__(self, master, app, diagram_id: str | None = None, history=None):
        tool_groups = {"Elements": ["Existing Element"]}
        if stpa_tool_enabled(app):
            tool_groups["Analysis"] = ["STPA Analysis"]
        tools = [t for group in tool_groups.values() for t in group]
        rel_tools = ["Control Action", "Feedback"]
        try:
            super().__init__(
                master,
                "Control Flow Diagram",
                tools,
                diagram_id,
                app=app,
                history=history,
                relation_tools=rel_tools,
                tool_groups=tool_groups,
            )
        except TypeError:
            super().__init__(
                master,
                "Control Flow Diagram",
                tools + rel_tools,
                diagram_id,
                app=app,
                history=history,
            )
        if not hasattr(self, "tools_frame"):
            self.tools_frame = self.toolbox

    def select_tool(self, tool):
        if tool == "STPA Analysis":
            repo = SysMLRepository.get_instance()
            self.app.open_stpa_window()
            diag_id = self.diagram_id
            doc = next((d for d in self.app.stpa_docs if d.diagram == diag_id), None)
            if not doc:
                diag = repo.diagrams.get(diag_id)
                name = diag.name or diag.diag_id if diag else f"STPA {len(self.app.stpa_docs)+1}"
                doc = StpaDoc(name, diag_id, [])
                self.app.stpa_docs.append(doc)
            self.app.active_stpa = doc
            self.app.stpa_entries = doc.entries
            if hasattr(self.app, "_stpa_window"):
                self.app._stpa_window.refresh_docs()
                self.app._stpa_window.doc_var.set(doc.name)
                self.app._stpa_window.select_doc()
            return
        super().select_tool(tool)


class NewDiagramDialog(simpledialog.Dialog):
    """Dialog to create a new diagram and assign a name and type."""

    def __init__(self, master):
        self.name = ""
        self.diag_type = "Use Case Diagram"
        super().__init__(master, title="New Diagram")

    def body(self, master):
        ttk.Label(master, text="Name:").grid(row=0, column=0, padx=4, pady=4, sticky="e")
        self.name_var = tk.StringVar()
        ttk.Entry(master, textvariable=self.name_var).grid(row=0, column=1, padx=4, pady=4)
        ttk.Label(master, text="Type:").grid(row=1, column=0, padx=4, pady=4, sticky="e")
        self.type_var = tk.StringVar(value=self.diag_type)
        ttk.Combobox(
            master,
            textvariable=self.type_var,
                values=[
                    "Use Case Diagram",
                    "Activity Diagram",
                    "Block Diagram",
                    "Internal Block Diagram",
                    "Control Flow Diagram",
                ],
        ).grid(row=1, column=1, padx=4, pady=4)

    def apply(self):
        self.name = self.name_var.get()
        self.diag_type = self.type_var.get()


class DiagramPropertiesDialog(simpledialog.Dialog):
    """Dialog to edit a diagram's metadata."""

    def __init__(self, master, diagram: SysMLDiagram):
        self.diagram = diagram
        self.added_parts: list[dict] = []
        super().__init__(master, title="Diagram Properties")

    def body(self, master):
        self.resizable(False, False)
        ttk.Label(master, text="Name:").grid(row=0, column=0, sticky="e", padx=4, pady=2)
        self.name_var = tk.StringVar(value=self.diagram.name)
        ttk.Entry(master, textvariable=self.name_var).grid(row=0, column=1, padx=4, pady=2)
        ttk.Label(master, text="Description:").grid(row=1, column=0, sticky="e", padx=4, pady=2)
        self.desc_var = tk.StringVar(value=getattr(self.diagram, "description", ""))
        ttk.Entry(master, textvariable=self.desc_var).grid(row=1, column=1, padx=4, pady=2)
        ttk.Label(master, text="Color:").grid(row=2, column=0, sticky="e", padx=4, pady=2)
        self.color_var = tk.StringVar(value=getattr(self.diagram, "color", "#FFFFFF"))
        ttk.Entry(master, textvariable=self.color_var).grid(row=2, column=1, padx=4, pady=2)
        row = 3
        if self.diagram.diag_type == "Governance Diagram":
            app = getattr(self.master, "app", None)
            toolbox = getattr(app, "safety_mgmt_toolbox", None)
            frozen = toolbox.diagram_frozen(self.diagram.name) if toolbox else False
            self.freeze_var = tk.BooleanVar(value=frozen)
            ttk.Checkbutton(master, text="Frozen", variable=self.freeze_var).grid(
                row=row, column=0, columnspan=2, sticky="w", padx=4, pady=2
            )
        elif self.diagram.diag_type == "Internal Block Diagram":
            repo = SysMLRepository.get_instance()
            blocks = [e for e in repo.elements.values() if e.elem_type == "Block"]
            idmap = {b.name or b.elem_id: b.elem_id for b in blocks}
            ttk.Label(master, text="Father:").grid(row=row, column=0, sticky="e", padx=4, pady=2)
            self.father_map = idmap
            cur_id = getattr(self.diagram, "father", "")
            cur_name = next((n for n, i in idmap.items() if i == cur_id), "")
            self.father_var = tk.StringVar(value=cur_name)
            ttk.Combobox(master, textvariable=self.father_var, values=list(idmap.keys())).grid(
                row=row, column=1, padx=4, pady=2
            )
        else:
            self.father_map = {}
            self.father_var = tk.StringVar()

    def apply(self):
        self.diagram.name = self.name_var.get()
        self.diagram.description = self.desc_var.get()
        self.diagram.color = self.color_var.get()
        if self.diagram.diag_type == "Governance Diagram":
            app = getattr(self.master, "app", None)
            toolbox = getattr(app, "safety_mgmt_toolbox", None)
            if toolbox and hasattr(self, "freeze_var"):
                toolbox.set_diagram_frozen(self.diagram.name, bool(self.freeze_var.get()))
        elif self.diagram.diag_type == "Internal Block Diagram":
            father_id = self.father_map.get(self.father_var.get())
            repo = SysMLRepository.get_instance()
            self.added_parts = set_ibd_father(
                repo, self.diagram, father_id, app=getattr(self.master, "app", None)
            )
            self.added_parts.extend(inherit_father_parts(repo, self.diagram))


class PackagePropertiesDialog(simpledialog.Dialog):
    """Dialog to edit a package's name."""

    def __init__(self, master, package: SysMLElement):
        self.package = package
        super().__init__(master, title="Package Properties")

    def body(self, master):
        self.resizable(False, False)
        ttk.Label(master, text="Name:").grid(row=0, column=0, sticky="e", padx=4, pady=2)
        self.name_var = tk.StringVar(value=self.package.name)
        ttk.Entry(master, textvariable=self.name_var).grid(row=0, column=1, padx=4, pady=2)

    def apply(self):
        self.package.name = self.name_var.get()


class ElementPropertiesDialog(simpledialog.Dialog):
    """Dialog to edit a generic element's name and properties."""

    def __init__(self, master, element: SysMLElement):
        self.element = element
        super().__init__(master, title=f"{element.elem_type} Properties")

    def body(self, master):
        self.resizable(False, False)
        ttk.Label(master, text="Name:").grid(row=0, column=0, sticky="e", padx=4, pady=2)
        self.name_var = tk.StringVar(value=self.element.name)
        ttk.Entry(master, textvariable=self.name_var).grid(row=0, column=1, padx=4, pady=2)
        self.entries = {}
        key = f"{self.element.elem_type.replace(' ', '')}Usage"
        row = 1
        for prop in SYSML_PROPERTIES.get(key, []):
            if prop == "partProperties":
                # Part properties are configured through dedicated dialogs.
                # Skip them in the generic properties window.
                continue
            ttk.Label(master, text=f"{prop}:").grid(row=row, column=0, sticky="e", padx=4, pady=2)
            var = tk.StringVar(value=self.element.properties.get(prop, ""))
            ttk.Entry(master, textvariable=var).grid(row=row, column=1, padx=4, pady=2)
            self.entries[prop] = var
            row += 1

    def apply(self):
        repo = SysMLRepository.get_instance()
        new_name = self.name_var.get()
        if self.element.elem_type == "Block":
            rename_block(repo, self.element.elem_id, new_name)
        else:
            self.element.name = new_name
        for prop, var in self.entries.items():
            self.element.properties[prop] = var.get()


class ArchitectureManagerDialog(tk.Frame):
    """Manage packages and diagrams in a hierarchical tree."""

    def __init__(self, master, app=None):
        if isinstance(master, tk.Toplevel):
            container = master
        else:
            container = master
        super().__init__(container)
        self.app = app
        if isinstance(master, tk.Toplevel):
            master.title("AutoML Explorer")
            master.geometry("350x400")
            self.pack(fill=tk.BOTH, expand=True)
        self.repo = SysMLRepository.get_instance()

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.tree = ttk.Treeview(tree_frame)
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        # style-aware icons to visually distinguish packages, diagrams and objects
        style = StyleManager.get_instance()

        def _color(name: str, fallback: str = "black") -> str:
            c = style.get_color(name)
            return fallback if c == "#FFFFFF" else c

        self.pkg_icon = self._create_icon("folder", _color("Lifecycle Phase", "#b8860b"))
        self.diagram_icons = {
            "Use Case Diagram": self._create_icon("usecase_diag", _color("Use Case Diagram", "blue")),
            "Activity Diagram": self._create_icon("activity_diag", _color("Activity Diagram", "green")),
            "Governance Diagram": self._create_icon("activity_diag", _color("Governance Diagram", "green")),
            "Block Diagram": self._create_icon("block_diag", _color("Block Diagram", "orange")),
            "Internal Block Diagram": self._create_icon("ibd_diag", _color("Internal Block Diagram", "purple")),
        }
        self.elem_icons = {
            "Actor": self._create_icon("human", _color("Actor")),
            "Use Case": self._create_icon("ellipse", _color("Use Case")),
            "Block": self._create_icon("component", _color("Block")),
            "Part": self._create_icon("puzzle", _color("Part")),
            "Port": self._create_icon("ring", _color("Port")),
            "Decision": self._create_icon("diamond", _color("Decision")),
            "Merge": self._create_icon("diamond", _color("Merge")),
            "Fork": self._create_icon("bar", _color("Fork")),
            "Join": self._create_icon("bar", _color("Join")),
            "Initial": self._create_icon("circle", _color("Initial")),
            "Final": self._create_icon("circle", _color("Final")),
            "Action": self._create_icon("action", _color("Action")),
            "CallBehaviorAction": self._create_icon("action", _color("CallBehaviorAction")),
            "AI Database": self._create_icon("cylinder", _color("AI Database")),
            "ANN": self._create_icon("neural", _color("ANN")),
            "Data acquisition": self._create_icon("arrow", _color("Data acquisition")),
            "Business Unit": self._create_icon("department", _color("Business Unit")),
            "Data": self._create_icon("cylinder", _color("Data")),
            "Field Data": self._create_icon("cylinder", _color("Field Data")),
            "Document": self._create_icon("document", _color("Document")),
            "Guideline": self._create_icon("compass", _color("Guideline")),
            "Metric": self._create_icon("chart", _color("Metric")),
            "Organization": self._create_icon("building", _color("Organization")),
            "Policy": self._create_icon("scroll", _color("Policy")),
            "Principle": self._create_icon("scale", _color("Principle")),
            "Procedure": self._create_icon("document", _color("Procedure")),
            "Record": self._create_icon("document", _color("Record")),
            "Role": self._create_icon("human", _color("Role")),
            "Standard": self._create_icon("ribbon", _color("Standard")),
            "Safety Compliance": self._create_icon("shield_check", _color("Safety Compliance")),
            "Process": self._create_icon("gear", _color("Process")),
            "Process Area": self._create_icon("gear", _color("Process Area")),
            "Work Product": self._create_icon("document", _color("Work Product")),
            "Operation": self._create_icon("wrench", _color("Operation")),
            "Driving Function": self._create_icon("steering", _color("Driving Function")),
        }
        self.default_diag_icon = self._create_icon("document", "gray")
        self.default_elem_icon = self._create_icon("rect", _color("Existing Element", "gray"))
        btns = ttk.Frame(self)
        btns.pack(fill=tk.X, padx=4, pady=4)
        ttk.Button(btns, text="Open", command=self.open).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="Properties", command=self.properties).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="New Package", command=self.new_package).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="New Diagram", command=self.new_diagram).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="Cut", command=self.cut).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="Paste", command=self.paste).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="Delete", command=self.delete).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="Close", command=self.destroy).pack(side=tk.RIGHT, padx=2)
        self.populate()
        self.tree.bind("<Button-3>", self.on_right_click)
        self.tree.bind("<Double-1>", self.on_double)
        self.tree.bind("<ButtonPress-1>", self.on_drag_start)
        self.tree.bind("<B1-Motion>", self.on_drag_motion)
        self.tree.bind("<ButtonRelease-1>", self.on_drag_release)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.bind("<FocusIn>", lambda _e: self.populate())
        self.drag_item = None
        self.cut_item = None

    def populate(self):
        """Populate the tree view with packages, diagrams and elements."""
        self.tree.delete(*self.tree.get_children())
        from collections import defaultdict

        rel_children = defaultdict(list)
        for rel in self.repo.relationships:
            rel_children[rel.source].append((rel.rel_id, rel.target, rel.rel_type))

        visited: set[str] = set()

        # collect all elements that already appear on a diagram so they don't
        # show up twice in the hierarchy
        diagram_elems = {
            elem_id
            for diag in self.repo.diagrams.values()
            for elem_id in (
                list(getattr(diag, "elements", []))
                + [
                    getattr(o, "element_id", o.get("element_id"))
                    for o in getattr(diag, "objects", [])
                    if getattr(o, "element_id", o.get("element_id"))
                ]
            )
        }

        def add_elem(elem_id: str, parent: str):
            if elem_id in visited:
                return
            visited.add(elem_id)
            elem = self.repo.elements[elem_id]
            icon = self.elem_icons.get(elem.elem_type, self.default_elem_icon)
            if self.tree.exists(elem_id):
                node = elem_id
            else:
                node = self.tree.insert(
                    parent,
                    "end",
                    iid=elem_id,
                    text=format_name_with_phase(elem.name or elem_id, elem.phase),
                    values=(elem.elem_type,),
                    image=icon,
                )
            for rel_id, tgt_id, rtype in rel_children.get(elem_id, []):
                if tgt_id in self.repo.elements:
                    rel_iid = f"rel_{rel_id}"
                    if self.tree.exists(rel_iid):
                        rel_node = rel_iid
                    else:
                        rel_node = self.tree.insert(
                            node, "end", iid=rel_iid, text=rtype, values=("Relationship",)
                        )
                    add_elem(tgt_id, rel_node)
            visited.remove(elem_id)

        root_pkg = getattr(self.repo, "root_package", None)
        if not root_pkg or root_pkg.elem_id not in self.repo.elements:
            # ensure a valid root package exists
            self.repo.root_package = self.repo.create_element("Package", name="Root")
            root_pkg = self.repo.root_package

        def add_pkg(pkg_id, parent=""):
            pkg = self.repo.elements[pkg_id]
            if self.tree.exists(pkg_id):
                node = pkg_id
            else:
                node = self.tree.insert(
                    parent,
                    "end",
                    iid=pkg_id,
                    text=format_name_with_phase(pkg.name or pkg_id, pkg.phase),
                    open=True,
                    image=self.pkg_icon,
                )
            for p in self.repo.elements.values():
                if p.elem_type == "Package" and p.owner == pkg_id:
                    add_pkg(p.elem_id, node)
            for e in self.repo.elements.values():
                if (
                    e.owner == pkg_id
                    and e.elem_type not in ("Package", "Part")
                    and e.name
                    and e.elem_id not in diagram_elems
                ):
                    add_elem(e.elem_id, node)
            for d in self.repo.diagrams.values():
                if d.package == pkg_id and "safety-management" not in getattr(d, "tags", []):
                    label = format_name_with_phase(d.name or d.diag_id, d.phase)
                    icon = self.diagram_icons.get(d.diag_type, self.default_diag_icon)
                    diag_iid = f"diag_{d.diag_id}"
                    if self.tree.exists(diag_iid):
                        diag_node = diag_iid
                    else:
                        diag_node = self.tree.insert(
                            node,
                            "end",
                            iid=diag_iid,
                            text=label,
                            values=(d.diag_type,),
                            image=icon,
                        )
                    objs = sorted(
                        d.objects,
                        key=lambda o: (
                            1 if getattr(o, "obj_type", o.get("obj_type")) == "Port" else 0
                        ),
                    )
                    for obj in objs:
                        props = getattr(obj, "properties", obj.get("properties", {}))
                        name = format_name_with_phase(
                            props.get("name", getattr(obj, "obj_type", obj.get("obj_type"))),
                            getattr(obj, "phase", obj.get("phase")),
                        )
                        oid = getattr(obj, "obj_id", obj.get("obj_id"))
                        otype = getattr(obj, "obj_type", obj.get("obj_type"))
                        icon = self.elem_icons.get(otype, self.default_elem_icon)
                        parent_node = diag_node
                        if (
                            otype == "Port"
                            and props.get("parent")
                            and self.tree.exists(f"obj_{d.diag_id}_{props.get('parent')}")
                        ):
                            parent_node = f"obj_{d.diag_id}_{props.get('parent')}"
                        obj_iid = f"obj_{d.diag_id}_{oid}"
                        if self.tree.exists(obj_iid):
                            continue
                        self.tree.insert(
                            parent_node,
                            "end",
                            iid=obj_iid,
                            text=name,
                            values=(obj.get("obj_type"),),
                            image=icon,
                        )

        add_pkg(root_pkg.elem_id)
        if self.app:
            self.app.update_views()

    def on_tree_select(self, _event):
        """Show metadata for the selected repository item in the app's property view."""
        if not self.app or not hasattr(self.app, "show_properties"):
            return
        item = self.tree.focus()
        if not item:
            return
        name = self.tree.item(item, "text")
        meta = {"Name": name}
        repo = self.repo
        if item.startswith("diag_"):
            diag = repo.diagrams.get(item[5:])
            if diag:
                meta.update(
                    {
                        "Type": diag.diag_type,
                        "Author": getattr(diag, "author", ""),
                        "Created": getattr(diag, "created", ""),
                        "Modified": getattr(diag, "modified", ""),
                        "ModifiedBy": getattr(diag, "modified_by", ""),
                    }
                )
        elif item in repo.elements:
            elem = repo.elements[item]
            meta.update(
                {
                    "Type": elem.elem_type,
                    "Author": getattr(elem, "author", ""),
                    "Created": getattr(elem, "created", ""),
                    "Modified": getattr(elem, "modified", ""),
                    "ModifiedBy": getattr(elem, "modified_by", ""),
                }
            )
        self.app.show_properties(meta=meta)

    def selected(self):
        sel = self.tree.selection()
        if sel:
            return sel[0]
        item = self.tree.focus()
        return item if item else None

    def open(self):
        item = self.selected()
        if not item:
            return
        if item.startswith("diag_"):
            self.open_diagram(item[5:])
        elif item.startswith("obj_"):
            diag_id, oid = item[4:].split("_", 1)
            win = self.open_diagram(diag_id)
            if win:
                for o in win.objects:
                    if o.obj_id == int(oid):
                        win.selected_obj = o
                        win.redraw()
                        break

    def on_double(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            if item.startswith("diag_"):
                self.open_diagram(item[5:])
            elif item.startswith("obj_"):
                self.open()

    def open_diagram(self, diag_id: str):
        diag = self.repo.diagrams.get(diag_id)
        if not diag:
            return None

        # If an application instance is available, open the diagram using
        # the main document notebook so duplicate tabs are avoided.
        if self.app and hasattr(self.app, "window_controllers") and hasattr(
            self.app, "diagram_tabs"
        ):
            self.app.window_controllers.open_arch_window(diag_id)
            tab = self.app.diagram_tabs.get(diag_id)
            if tab and tab.winfo_exists():
                for child in tab.winfo_children():
                    if isinstance(child, SysMLDiagramWindow):
                        return child
            return None

        master = self.master if self.master else self
        win = None
        if diag.diag_type == "Use Case Diagram":
            win = UseCaseDiagramWindow(master, self.app, diagram_id=diag_id)
        elif diag.diag_type == "Activity Diagram":
            win = ActivityDiagramWindow(master, self.app, diagram_id=diag_id)
        elif diag.diag_type == "Governance Diagram":
            win = GovernanceDiagramWindow(master, self.app, diagram_id=diag_id)
        elif diag.diag_type == "Block Diagram":
            win = BlockDiagramWindow(master, self.app, diagram_id=diag_id)
        elif diag.diag_type == "Internal Block Diagram":
            win = InternalBlockDiagramWindow(master, self.app, diagram_id=diag_id)
        return win

    def new_package(self):
        item = self.selected() or self.repo.root_package.elem_id
        if item.startswith("diag_"):
            item = self.repo.diagrams[item[5:]].package
        name = simpledialog.askstring("New Package", "Name:")
        if name:
            self.repo.create_package(name, parent=item)
            self.populate()

    def new_diagram(self):
        item = self.selected() or self.repo.root_package.elem_id
        if item.startswith("diag_"):
            item = self.repo.diagrams[item[5:]].package
        dlg = NewDiagramDialog(self)
        if dlg.name:
            self.repo.create_diagram(dlg.diag_type, name=dlg.name, package=item)
            self.populate()

    def delete(self):
        item = self.selected()
        if not item:
            return
        if item.startswith("diag_"):
            self.repo.delete_diagram(item[5:])
        elif item.startswith("obj_"):
            diag_id, oid = item[4:].split("_", 1)
            diag = self.repo.diagrams.get(diag_id)
            if diag:
                diag.objects = [o for o in diag.objects if str(o.get("obj_id")) != oid]
        else:
            if item == self.repo.root_package.elem_id:
                messagebox.showerror("Delete", "Cannot delete the root package.")
            else:
                self.repo.delete_package(item)
        self.populate()

    def properties(self):
        item = self.selected()
        if not item:
            return
        if item.startswith("diag_"):
            diag = self.repo.diagrams.get(item[5:])
            if diag:
                DiagramPropertiesDialog(self, diag)
                self.populate()
        elif item.startswith("obj_"):
            diag_id, oid = item[4:].split("_", 1)
            diag = self.repo.diagrams.get(diag_id)
            if diag:
                obj_data = next(
                    (o for o in diag.objects if str(o.get("obj_id")) == oid),
                    None,
                )
                if obj_data:
                    obj = SysMLObject(**obj_data)
                    SysMLObjectDialog(self, obj)
                    diag.objects = [
                        obj.__dict__ if str(o.get("obj_id")) == oid else o for o in diag.objects
                    ]
                self.populate()
        else:
            elem = self.repo.elements.get(item)
            if elem:
                if elem.elem_type == "Package":
                    PackagePropertiesDialog(self, elem)
                else:
                    ElementPropertiesDialog(self, elem)
                self.populate()

    def on_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        self.tree.selection_set(item)
        menu = tk.Menu(self.tree, tearoff=0)
        menu.add_command(label="Rename", command=lambda: self.rename_item(item))
        menu.tk_popup(event.x_root, event.y_root)

    def rename_item(self, item=None):
        item = item or self.selected()
        if not item:
            return
        if item.startswith("diag_"):
            diag = self.repo.diagrams.get(item[5:])
            if diag and "safety-management" in getattr(diag, "tags", []):
                return
            if diag:
                name = simpledialog.askstring("Rename Diagram", "Name:", initialvalue=diag.name)
                if name:
                    diag.name = name
                    self.populate()
        elif item.startswith("obj_"):
            return
        else:
            elem = self.repo.elements.get(item)
            if elem:
                name = simpledialog.askstring("Rename", "Name:", initialvalue=elem.name)
                if name:
                    name = self.repo.ensure_unique_element_name(name, elem.elem_id)
                    if elem.elem_type == "Block":
                        rename_block(self.repo, elem.elem_id, name)
                    else:
                        elem.name = name
                    self.populate()

    # ------------------------------------------------------------------
    # Cut/Paste and Drag & Drop Handling
    # ------------------------------------------------------------------
    def cut(self):
        item = self.selected()
        if item:
            self.cut_item = item

    def paste(self):
        if not self.cut_item:
            return
        target = self.selected() or self.repo.root_package.elem_id
        if target.startswith("diag_"):
            target = self.repo.diagrams[target[5:]].package
        self._move_item(self.cut_item, target)
        self.cut_item = None
        self.populate()

    def on_drag_start(self, event):
        self.drag_item = self.tree.identify_row(event.y)
        if self.drag_item:
            self.tree.selection_set(self.drag_item)

    def on_drag_motion(self, _event):
        pass

    def on_drag_release(self, event):
        if not self.drag_item:
            return
        target = self.tree.identify_row(event.y)
        if not target:
            self.drag_item = None
            return
        if target == self.drag_item:
            self.drag_item = None
            return
        if self.drag_item.startswith("obj_"):
            messagebox.showerror("Drop Error", "Objects cannot be moved in the explorer.")
            self.drag_item = None
            return
        if target.startswith("obj_"):
            messagebox.showerror("Drop Error", "Cannot drop items on an object.")
            self.drag_item = None
            return
        region = self.tree.identify_region(event.x, event.y)
        if region in ("separator", "nothing"):
            parent = self.tree.parent(target)
            index = self.tree.index(target)
            self.tree.move(self.drag_item, parent, index)
            self._move_item(self.drag_item, parent)
        else:
            if target.startswith("diag_"):
                diag = self.repo.diagrams.get(target[5:])
                self._drop_on_diagram(self.drag_item, diag)
            else:
                self.tree.move(self.drag_item, target, "end")
                self._move_item(self.drag_item, target)
        self.drag_item = None
        self.populate()

    def _move_item(self, item, new_parent):
        if item.startswith("obj_") or new_parent.startswith("obj_"):
            messagebox.showerror("Drop Error", "Cannot drop items on an object.")
            return
        if new_parent == "":
            new_parent = self.repo.root_package.elem_id
        if item.startswith("diag_"):
            self.repo.diagrams[item[5:]].package = new_parent
        else:
            elem = self.repo.elements.get(item)
            if elem:
                elem.owner = new_parent

    def _drop_on_diagram(self, elem_id, diagram):
        repo = self.repo
        if elem_id.startswith("obj_"):
            messagebox.showerror("Drop Error", "Objects cannot be dropped on a diagram.")
            return
        # Dropping a diagram onto an Activity or Governance Diagram creates a behavior reference
        if elem_id.startswith("diag_"):
            src_diag = repo.diagrams.get(elem_id[5:])
            if src_diag and diagram.diag_type == "Activity Diagram" and src_diag.diag_type in (
                "Activity Diagram",
                "Internal Block Diagram",
                "Governance Diagram",
            ):
                elem_type = "Action" if diagram.diag_type == "Governance Diagram" else "CallBehaviorAction"
                act = repo.create_element(
                    elem_type, name=src_diag.name, owner=diagram.package
                )
                repo.add_element_to_diagram(diagram.diag_id, act.elem_id)
                props = {"name": src_diag.name}
                if src_diag.diag_type == "Internal Block Diagram":
                    props["view"] = src_diag.diag_id
                    repo.link_diagram(act.elem_id, None)
                else:
                    repo.link_diagram(act.elem_id, src_diag.diag_id)
                obj = SysMLObject(
                    _get_next_id(),
                    elem_type,
                    50.0,
                    50.0,
                    element_id=act.elem_id,
                    properties=props,
                    phase=_repo_phase(repo),
                )
                diagram.objects.append(obj.__dict__)
                if getattr(self, "app", None) and hasattr(self.app, "push_undo_state"):
                    self.app.push_undo_state()
                return
            if (
                src_diag
                and diagram.diag_type == "Governance Diagram"
                and src_diag.diag_type == "Governance Diagram"
            ):
                act = repo.create_element("Action", name=src_diag.name, owner=diagram.package)
                repo.add_element_to_diagram(diagram.diag_id, act.elem_id)
                props = {"name": src_diag.name}
                repo.link_diagram(act.elem_id, src_diag.diag_id)
                obj = SysMLObject(
                    _get_next_id(),
                    "Action",
                    50.0,
                    50.0,
                    element_id=act.elem_id,
                    properties=props,
                    phase=_repo_phase(repo),
                )
                diagram.objects.append(obj.__dict__)
                if getattr(self, "app", None) and hasattr(self.app, "push_undo_state"):
                    self.app.push_undo_state()
                return
            messagebox.showerror("Drop Error", "This item cannot be dropped on that diagram.")
            return

        allowed = diagram.diag_type == "Block Diagram"
        if allowed and repo.elements[elem_id].elem_type == "Package":
            block = repo.create_element("Block", name=repo.elements[elem_id].name, owner=elem_id)
            repo.add_element_to_diagram(diagram.diag_id, block.elem_id)
            obj = SysMLObject(
                _get_next_id(),
                "Block",
                50.0,
                50.0,
                element_id=block.elem_id,
                phase=_repo_phase(repo),
            )
            diagram.objects.append(obj.__dict__)
            if getattr(self, "app", None) and hasattr(self.app, "push_undo_state"):
                self.app.push_undo_state()
        else:
            messagebox.showerror("Drop Error", "This item cannot be dropped on that diagram.")

    def _create_icon(self, shape: str, color: str = "black") -> tk.PhotoImage:
        """Delegate icon drawing to the shared :func:`draw_icon`."""
        return draw_icon(shape, color)
