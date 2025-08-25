#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

"""Generate requirement patterns from diagram rule configuration.

This module derives requirement pattern definitions for both Safety & AI
connections and Governance diagram relationships.  It mirrors the standalone
``generate_from_diagram_rules.py`` utility supplied by the user but exposes a
``generate_patterns_from_config`` function so existing code can reuse the
generator programmatically.  Resulting requirement templates follow the
ISO/IEC/IEEE 29148 structure

    [CND] <span style="color:#2e86c1;font-weight:bold">&lt;subject&gt;</span> shall
    <span style="color:#28b463;font-weight:bold">&lt;action&gt;</span>
    [<span style="color:#f39c12;font-weight:bold">&lt;object&gt;</span>]
    [<span style="color:#c0392b;font-weight:bold">&lt;constraint&gt;</span>].

The main entry point :func:`regenerate_requirement_patterns` reloads the
``config/rules/diagram_rules.json`` file, regenerates all patterns and writes
the result to ``config/patterns/requirement_patterns.json``.  This helper is
invoked by the application whenever the model changes so requirement patterns
stay in sync with diagram rule updates and governance diagram creation.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

# ============================================================================
# JSON loader that accepts //, /* */, single quotes and trailing commas
# ============================================================================


def clean_and_load_json(path: str, quiet: bool = False) -> dict:
    """Return JSON object from ``path`` accepting common non‑JSON features.

    A copy of the cleaned text is written alongside the original using the
    ``.normalized.json`` suffix to ease troubleshooting should validation fail.
    """

    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    # Remove block and line comments
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//[^\n]*", "", text)

    # Replace single quotes with double quotes in a conservative manner
    def _sq_to_dq(m: re.Match[str]) -> str:
        s = m.group(0)[1:-1]
        s = s.replace(r'\"', '"')
        s = s.replace('"', r'\"')
        s = s.replace(r"\'", "'")
        return '"' + s + '"'

    text = re.sub(r"'([^'\\]|\\.)*'", _sq_to_dq, text)

    # Quote unquoted object keys
    text = re.sub(
        r"([{,]\s*)([A-Za-z_][A-Za-z0-9_\- ]*)(\s*):",
        lambda m: f'{m.group(1)}"{m.group(2).strip()}"{m.group(3)}:',
        text,
    )

    # Remove trailing commas
    text = re.sub(r",\s*([}\]])", r"\1", text)

    norm_path = os.path.splitext(path)[0] + ".normalized.json"
    with open(norm_path, "w", encoding="utf-8") as nf:
        nf.write(text)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:  # pragma: no cover - debugging aid
        snippet = text[max(0, e.pos - 120) : e.pos + 120]
        sys.stderr.write("\n[ERROR] Invalid JSON after cleaning.\n")
        sys.stderr.write(
            f"  Original file: {path}\n  Normalized copy: {norm_path}\n  Pos {e.pos}: …{snippet}…\n{e}\n"
        )
        raise SystemExit(1)

    if not quiet:
        print(f"[CLEAN] OK -> {norm_path}")
    return data


# ============================================================================
# Template helpers
# ============================================================================

SUFFIXES = [
    ("", False, False),  # base
    ("-COND", True, False),  # with condition
    ("-COND-CONST", True, True),  # condition + constraint
    ("-CONST", False, True),  # with constraint
]


def tidy_sentence(s: str) -> str:
    if not s:
        return s
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s+([,.;:])", r"\1", s)
    s = s.strip()
    if s and s[-1] not in ".?!":
        s += "."
    return s


def normalize_base_template(tmpl: str) -> str:
    t = (tmpl or "").strip()
    if t.startswith("When <condition>, "):
        t = t[len("When <condition>, ") :]
    if t.endswith(" constrained by <constraint>."):
        t = t[: -len(" constrained by <constraint>.")]
        t = t.rstrip(". ")
        t += "."
    if not t.endswith("."):
        t += "."
    return t


def build_cond_template(base: str) -> str:
    base = base.strip()
    if not base.endswith("."):
        base += "."
    return f"When <condition>, {base[0].upper()}{base[1:]}"


def build_const_template(base: str) -> str:
    base = base.strip()
    if base.endswith("."):
        base = base[:-1]
    return f"{base} constrained by <constraint>."


def build_cond_const_template(base: str) -> str:
    return build_const_template(build_cond_template(base))


def ensure_variables(
    base_vars: Iterable[str], need_cond: bool, need_const: bool
) -> List[str]:
    out = list(base_vars)
    if need_cond and "<condition>" not in out:
        out.append("<condition>")
    if need_const and "<constraint>" not in out:
        out.append("<constraint>")
    seen: set[str] = set()
    dedup: List[str] = []
    for v in out:
        if v not in seen:
            dedup.append(v)
            seen.add(v)
    return dedup


def id_token(s: str) -> str:
    return re.sub(r"[^\w]+", "_", (s or "")).strip("_")


def make_trigger(prefix: str, src: str, rel: str, tgt: str) -> str:
    return f"{prefix}: {src} --[{rel}]--> {tgt}"


def is_action_type(name: str) -> bool:
    """Return True if *name* represents an action-like node type."""
    return bool(re.search(r"(action|activity|procedure|task|operation)", (name or ""), re.I))


# ===== Safety & AI templates =====


def _objects_phrase(objects: int) -> str:
    parts = []
    for i in range(1, objects + 1):
        parts.append(f"the <object{i}_id> (<object{i}_class>)")
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    return ", ".join(parts[:-1]) + f", and {parts[-1]}"


def make_sa_template(
    subject: str, action: str, objects: int = 1, subject_is_object0: bool = False
) -> str:
    action_clean = (action or "").strip()
    obj_phrase = _objects_phrase(objects)
    if action_clean.lower() == "collect field data":
        tmpl = f"{subject} shall {action_clean} from {obj_phrase}"
    else:
        tmpl = f"{subject} shall {action_clean} {obj_phrase}"
    if not subject_is_object0:
        tmpl += " using the <object0_id> (<object0_class>)."
    else:
        tmpl += "."
    return tidy_sentence(tmpl)


def make_sa_variables_base(objects: int = 1, include_subject: bool = False) -> List[str]:
    """Return variable placeholders for Safety & AI patterns.

    Parameters
    ----------
    objects:
        Number of object placeholders to include beyond the subject/tool.
    include_subject:
        When ``True`` the returned list starts with ``<subject_id>`` and
        ``<subject_class>``.  Otherwise ``<object0_id>``/``<object0_class>`` are
        used to represent an auxiliary object such as a tool.
    """

    if include_subject:
        out = ["<subject_id>", "<subject_class>", "<object1_id>", "<object1_class>"]
    else:
        out = ["<object0_id>", "<object0_class>", "<object1_id>", "<object1_class>"]
    for i in range(2, objects + 1):
        out.append(f"<object{i}_id>")
        out.append(f"<object{i}_class>")
    out.append("<acceptance_criteria>")
    return out


def make_sequence_template(
    subject: str, rel_chain: List[str], subject_is_object0: bool = False
) -> str:
    parts: List[str] = []
    for idx, rel in enumerate(rel_chain):
        rel_l = (rel or "").strip().lower()
        obj = f"the <object{idx+1}_id> (<object{idx+1}_class>)"
        if idx == 0:
            if subject_is_object0:
                parts.append(f"{rel_l} {obj}")
            else:
                parts.append(
                    f"{rel_l} {obj} using the <object0_id> (<object0_class>)"
                )
        else:
            parts.append(f"{rel_l} {obj}")
    if len(parts) > 1:
        seq = ", ".join(parts[:-1]) + f", and {parts[-1]}"
    else:
        seq = parts[0]
    return tidy_sentence(f"{subject} shall {seq}")


def make_grouped_action_template(subject: str, count: int) -> str:
    """Return template listing multiple actions as sub-items."""
    items: List[str] = []
    for i in range(1, count + 1):
        letter = chr(ord("a") + i - 1)
        items.append(f"{letter}) <object{i}_id> (<object{i}_class>)")
    joined = "; ".join(items)
    return tidy_sentence(f"{subject} shall execute: {joined}")


# ===== Governance templates =====


def make_gov_variables_base() -> List[str]:
    return ["<owner>", "<due_date>", "<evidence_ref>"]


def gov_template_for_relation(relation_label: str, targets: int = 1) -> str:
    r = (relation_label or "").strip().lower()

    passive = {
        "satisfied by": "shall be satisfied by the <object1_id> (<object1_class>).",
        "used by": "shall be used by the <object1_id> (<object1_class>).",
        "derived from": "shall be derived from the <object1_id> (<object1_class>).",
    }
    if r in passive:
        return tidy_sentence(
            f"<subject_id> (<subject_class>) {passive[r].replace('the <object1_id> (<object1_class>)', _objects_phrase(targets))}"
        )

    with_prep = {
        "flow": "shall flow to the <object1_id> (<object1_class>).",
        "trace": "shall trace to the <object1_id> (<object1_class>).",
        "communication path": "shall communicate with the <object1_id> (<object1_class>).",
        "constrained by": "shall comply with the <object1_id> (<object1_class>).",
        "used after review": "shall be used after review the <object1_id> (<object1_class>).",
        "used after approval": "shall be used after approval the <object1_id> (<object1_class>).",
        "propagate by review": "shall propagate by review the <object1_id> (<object1_class>).",
        "propagate by approval": "shall propagate by approval the <object1_id> (<object1_class>).",
    }
    if r in with_prep:
        return tidy_sentence(
            f"<subject_id> (<subject_class>) {with_prep[r].replace('the <object1_id> (<object1_class>)', _objects_phrase(targets))}"
        )

    quoted = {
        "approves": "shall approve '<object1_id> (<object1_class>)'.",
        "performs": "shall perform '<object1_id> (<object1_class>)'.",
    }
    if r in quoted:
        phrase = quoted[r]
        if targets > 1:
            multi = _objects_phrase(targets).replace("the ", "")
            phrase = phrase.replace("<object1_id> (<object1_class>)", multi)
        return tidy_sentence(f"<subject_id> (<subject_class>) {phrase}")
    return tidy_sentence(
        f"<subject_id> (<subject_class>) shall {r} {_objects_phrase(targets)}"
    )


def rule_info(
    requirement_rules: Dict[str, dict],
    relation_label: str,
    default_subject: str,
    default_action: str,
    default_targets: int = 1,
) -> Tuple[str, str, int, str | None, List[str] | None]:
    rr = (
        requirement_rules.get(relation_label.lower(), {})
        if isinstance(requirement_rules, dict)
        else {}
    )
    subj = rr.get("subject", default_subject)
    act = rr.get("action", default_action)
    tgt = rr.get("targets", default_targets)
    template = rr.get("template")
    variables = rr.get("variables") if isinstance(rr.get("variables"), list) else None
    if not isinstance(tgt, int) or tgt < 1:
        tgt = default_targets
    return subj, act, tgt, template, variables


# ============================================================================
# Pattern generation
# ============================================================================


def generate_patterns_from_rules(rules: dict) -> List[dict]:
    out: List[dict] = []

    req_rules = {}
    rr = rules.get("requirement_rules", {})
    if isinstance(rr, dict):
        req_rules = {k.lower(): v for k, v in rr.items()}
    conn_rules = rules.get("connection_rules", {}) or {}
    gov_root = conn_rules.get("Governance Diagram", {}) or {}
    ai_nodes = set(rules.get("ai_nodes", []))
    grouped_pairs: set[tuple[str, str]] = set()
    if isinstance(gov_root, dict):
        action_map: dict[str, dict[str, List[str]]] = {}
        for relation_label, src_map in gov_root.items():
            if not isinstance(src_map, dict):
                continue
            for src_type, tgt_list in (src_map or {}).items():
                if (
                    isinstance(tgt_list, list)
                    and src_type not in ai_nodes
                    and len(tgt_list) > 0
                    and all(is_action_type(t) and t not in ai_nodes for t in tgt_list)
                ):
                    action_map.setdefault(src_type, {})[relation_label] = tgt_list

        for src_type, rel_map in action_map.items():
            targets: List[str] = []
            for tlist in rel_map.values():
                for t in tlist:
                    if t not in targets:
                        targets.append(t)
            if len(targets) < 2:
                continue
            subjects: List[str] = []
            ok = True
            for rel in rel_map.keys():
                subj, _act, _tgt_count, tmpl_override, var_override = rule_info(
                    req_rules, rel, "Engineering team", rel.lower()
                )
                if tmpl_override or var_override:
                    ok = False
                    break
                subjects.append(subj)
            if not ok or not subjects or any(s != subjects[0] for s in subjects):
                continue
            subj = subjects[0]
            if subj == "Engineering team":
                subj = "<subject_id> (<subject_class>)"
            template = make_grouped_action_template(subj, len(targets))
            variables = make_gov_variables_base()
            rel_labels = sorted(rel_map.keys())
            relation_key = (
                rel_labels[0].lower().replace(" ", "_")
                if len(rel_labels) == 1
                else "actions"
            )
            base_id = f"GOV-{relation_key}-{id_token(src_type)}-group"
            trigger_rel = "/".join(rel_labels)
            trigger = make_trigger("Gov", src_type, trigger_rel, ", ".join(targets))
            notes = "Auto-generated from diagram rules (Governance)."
            for suf, need_cond, need_const in SUFFIXES:
                pid = base_id + suf
                t = (
                    build_cond_const_template(template)
                    if (need_cond and need_const)
                    else build_cond_template(template)
                    if need_cond
                    else build_const_template(template)
                    if need_const
                    else normalize_base_template(template)
                )
                vs = ensure_variables(variables, need_cond, need_const)
                out.append(
                    {
                        "Pattern ID": pid,
                        "Trigger": trigger,
                        "Template": t,
                        "Variables": vs,
                        "Notes": notes,
                    }
                )
            for rel in rel_map.keys():
                grouped_pairs.add((rel, src_type))

        for relation_label, src_map in gov_root.items():
            if not isinstance(src_map, dict):
                continue
            for src_type, tgt_list in (src_map or {}).items():
                if not isinstance(tgt_list, list):
                    continue
                if (relation_label, src_type) in grouped_pairs:
                    continue
                for tgt_type in (tgt_list or []):
                    is_ai = src_type in ai_nodes or tgt_type in ai_nodes
                    (
                        subj,
                        act,
                        tgt_count,
                        tmpl_override,
                        var_override,
                    ) = rule_info(
                        req_rules, relation_label, "Engineering team", relation_label.lower()
                    )
                    if is_ai:
                        trigger = make_trigger("Safety&AI", src_type, relation_label, tgt_type)
                        notes = "Auto-generated from diagram rules (Safety&AI)."
                        ai_variants = [
                            ("", subj, False),
                            ("-ROLE", "<subject_id> (<subject_class>)", True),
                        ]
                        for role_suf, subj_text, include_subject in ai_variants:
                            if tmpl_override:
                                template = tmpl_override
                                variables = var_override or []
                            else:
                                template = make_sa_template(
                                    subj_text, act, tgt_count, subject_is_object0=include_subject
                                )
                                variables = make_sa_variables_base(
                                    tgt_count, include_subject=include_subject
                                )
                            base_id = (
                                f"SA-{relation_label.lower().replace(' ', '_')}-{id_token(src_type)}-{id_token(tgt_type)}{role_suf}"
                            )
                            for suf, need_cond, need_const in SUFFIXES:
                                pid = base_id + suf
                                t = (
                                    build_cond_const_template(template)
                                    if (need_cond and need_const)
                                    else build_cond_template(template)
                                    if need_cond
                                    else build_const_template(template)
                                    if need_const
                                    else normalize_base_template(template)
                                )
                                vs = ensure_variables(
                                    variables, need_cond, need_const
                                )
                                out.append(
                                    {
                                        "Pattern ID": pid,
                                        "Trigger": trigger,
                                        "Template": t,
                                        "Variables": vs,
                                        "Notes": notes,
                                    }
                                )
                        continue
                    else:
                        if tmpl_override:
                            template = tmpl_override
                            variables = var_override or []
                        else:
                            template = gov_template_for_relation(relation_label, tgt_count)
                            variables = make_gov_variables_base()
                        base_id = f"GOV-{relation_label.lower().replace(' ', '_')}-{id_token(src_type)}-{id_token(tgt_type)}"
                        trigger = make_trigger("Gov", src_type, relation_label, tgt_type)
                        notes = "Auto-generated from diagram rules (Governance)."
                    for suf, need_cond, need_const in SUFFIXES:
                        pid = base_id + suf
                        t = (
                            build_cond_const_template(template)
                            if (need_cond and need_const)
                            else build_cond_template(template)
                            if need_cond
                            else build_const_template(template)
                            if need_const
                            else normalize_base_template(template)
                        )
                        vs = ensure_variables(variables, need_cond, need_const)
                        out.append(
                            {
                                "Pattern ID": pid,
                                "Trigger": trigger,
                                "Template": t,
                                "Variables": vs,
                                "Notes": notes,
                            }
                        )

    # Sequence rules --------------------------------------------------------
    seq_rules = rules.get("requirement_sequences", {}) or {}
    sa_rules = gov_root
    if isinstance(seq_rules, dict) and isinstance(sa_rules, dict):
        for seq_label, info in seq_rules.items():
            rel_chain = info.get("relations") or []
            if not isinstance(rel_chain, list) or len(rel_chain) < 2:
                continue
            first_map = sa_rules.get(rel_chain[0], {})
            if not isinstance(first_map, dict):
                continue
            paths = []
            for src_type, tgt_list in (first_map or {}).items():
                for tgt in (tgt_list or []):
                    paths.append([(src_type, tgt)])
            for rel in rel_chain[1:]:
                rel_map = sa_rules.get(rel, {})
                if not isinstance(rel_map, dict):
                    paths = []
                    break
                new_paths = []
                for path in paths:
                    last_tgt = path[-1][1]
                    for nxt in rel_map.get(last_tgt, []):
                        new_paths.append(path + [(last_tgt, nxt)])
                paths = new_paths
            for path in paths:
                src_type = path[0][0]
                final_tgt = path[-1][1]
                tgt_count = len(path)

                # Generate text-subject and entity-subject variants
                subject_entities = ["role", "organization", "business_unit"]
                variants = [
                    (seq_label, info.get("subject", "Engineering team"), False)
                ]
                for ent in subject_entities:
                    variants.append(
                        (
                            f"{seq_label}_{ent}_subject",
                            "<subject_id> (<subject_class>)",
                            True,
                        )
                    )

                for label_variant, subj, use_role_subject in variants:
                    tmpl_override = info.get("template")
                    var_override = info.get("variables")
                    if tmpl_override:
                        template = tmpl_override
                        variables = var_override or []
                    else:
                        template = make_sequence_template(
                            subj, rel_chain, subject_is_object0=use_role_subject
                        )
                        variables = make_sa_variables_base(
                            tgt_count, include_subject=use_role_subject
                        )
                    base_id = (
                        f"SEQ-{id_token(label_variant)}-{id_token(src_type)}-{id_token(final_tgt)}"
                    )
                    trigger_parts = [src_type]
                    for rel, edge in zip(rel_chain, path):
                        trigger_parts.append(f"--[{rel}]--> {edge[1]}")
                    trigger = "Sequence: " + " ".join(trigger_parts)
                    notes = "Auto-generated from sequence rules."
                    for suf, need_cond, need_const in SUFFIXES:
                        pid = base_id + suf
                        t = (
                            build_cond_const_template(template)
                            if (need_cond and need_const)
                            else build_cond_template(template)
                            if need_cond
                            else build_const_template(template)
                            if need_const
                            else normalize_base_template(template)
                        )
                        vs = ensure_variables(variables, need_cond, need_const)
                        out.append(
                            {
                                "Pattern ID": pid,
                                "Trigger": trigger,
                                "Template": t,
                                "Variables": vs,
                                "Notes": notes,
                            }
                        )

    # De-duplicate and sort --------------------------------------------------
    uniq: Dict[str, dict] = {}
    for rec in out:
        if rec["Pattern ID"] not in uniq:
            uniq[rec["Pattern ID"]] = rec
    return [uniq[k] for k in sorted(uniq.keys())]


# Backwards compatible function name used by existing modules
def generate_patterns_from_config(rules: dict) -> List[dict]:
    return generate_patterns_from_rules(rules)


def regenerate_requirement_patterns(
    diagram_rules_path: str | Path | None = None,
    out_path: str | Path | None = None,
    pretty: bool = True,
) -> None:
    """Reload rules and write ``requirement_patterns.json`` to disk."""

    diag_path = Path(
        diagram_rules_path
        or Path(__file__).resolve().parents[1]
        / "config"
        / "rules"
        / "diagram_rules.json"
    )
    out_path = Path(
        out_path
        or Path(__file__).resolve().parents[1]
        / "config"
        / "patterns"
        / "requirement_patterns.json"
    )
    rules = clean_and_load_json(str(diag_path), quiet=True)
    patterns = generate_patterns_from_config(rules)
    with open(out_path, "w", encoding="utf-8") as f:
        if pretty:
            json.dump(patterns, f, indent=2, ensure_ascii=False)
        else:
            json.dump(patterns, f, ensure_ascii=False)


# ============================================================================
# Command line interface
# ============================================================================


def main(argv: Iterable[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Limpia diagram_rules.json y genera patrones (BASE/-COND/"
            "-CONST/-COND-CONST), incluyendo GOV-Flow."
        )
    )
    ap.add_argument("--diagram-rules", required=True, help="Ruta a diagram_rules.json (puede estar 'sucio')")
    ap.add_argument("--out", required=True, help="Ruta del .json de salida con patrones")
    ap.add_argument("--pretty", action="store_true", help="Formatear JSON de salida")
    args = ap.parse_args(list(argv) if argv is not None else None)

    rules = clean_and_load_json(args.diagram_rules)
    patterns = generate_patterns_from_config(rules)

    out_path = Path(args.out).resolve()
    with open(out_path, "w", encoding="utf-8") as f:
        if args.pretty:
            json.dump(patterns, f, indent=2, ensure_ascii=False)
        else:
            json.dump(patterns, f, ensure_ascii=False)

    print(f"[DONE] Patterns: {len(patterns)}")
    print(f"[FILE] Output: {out_path}")
    print(
        f"[FILE] Normalized rules: {os.path.splitext(Path(args.diagram_rules).resolve())[0]}.normalized.json"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI utility
    raise SystemExit(main())

