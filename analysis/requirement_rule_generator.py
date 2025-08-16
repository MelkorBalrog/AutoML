#!/usr/bin/env python3
"""Utilities to derive requirement patterns from diagram rule configuration.

This module inspects the diagram rules configuration and generates requirement
pattern definitions for all supported Safety & AI relationship combinations.
Each base pattern is expanded to include conditional and constraint variants so
that ``analysis.governance`` can pick up new rules automatically whenever the
configuration changes.
"""

from __future__ import annotations

from copy import deepcopy
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List

# ---------------------------------------------------------------------------
# Template variant helpers (adapted from generate_project_compatible_patterns.py)

def _normalize_base_template(tmpl: str) -> str:
    """Return canonical form of ``tmpl`` without condition/constraint clauses."""
    t = tmpl.strip()
    cond_prefix = "When <condition>, "
    if t.startswith(cond_prefix):
        t = t[len(cond_prefix) :]
    constrained_phrase = " constrained by <constraint>."
    if t.endswith(constrained_phrase):
        t = t[: -len(constrained_phrase)]
        t = t.rstrip()
        if t.endswith("."):
            t = t[:-1]
        t = t + "."
    t = t.strip()
    if not t.endswith("."):
        t += "."
    return t

def _build_cond_template(base_tmpl: str) -> str:
    base = base_tmpl.strip()
    if not base.endswith("."):
        base += "."
    return f"When <condition>, {base[0].upper()}{base[1:]}"

def _build_const_template(base_tmpl: str) -> str:
    base = base_tmpl.strip()
    if base.endswith("."):
        base = base[:-1]
    return f"{base} constrained by <constraint>."

def _build_cond_const_template(base_tmpl: str) -> str:
    return _build_const_template(_build_cond_template(base_tmpl))

def _ensure_variables(base_vars: Iterable[str], need_cond: bool, need_const: bool) -> List[str]:
    out = list(base_vars)
    if need_cond and "<condition>" not in out:
        out.append("<condition>")
    if need_const and "<constraint>" not in out:
        out.append("<constraint>")
    seen = set()
    result = []
    for v in out:
        if v not in seen:
            result.append(v)
            seen.add(v)
    return result

_SUFFIXES = [
    ("", False, False),
    ("-COND", True, False),
    ("-COND-CONST", True, True),
    ("-CONST", False, True),
]

def _pattern_id_base(pid: str) -> str:
    for suff in ("-COND-CONST", "-COND", "-CONST"):
        if pid.endswith(suff):
            return pid[: -len(suff)]
    return pid

def _expand_variants(pat: Dict[str, Any]) -> List[Dict[str, Any]]:
    pid = pat.get("Pattern ID", "").strip()
    base_id = _pattern_id_base(pid)
    base_tmpl = _normalize_base_template(pat.get("Template", ""))
    vars_ = list(pat.get("Variables", []))
    trig = pat.get("Trigger", "")
    notes = pat.get("Notes", "")

    result: List[Dict[str, Any]] = []
    for suffix, need_cond, need_const in _SUFFIXES:
        vid = base_id + suffix
        tmpl = (
            _build_cond_const_template(base_tmpl)
            if need_cond and need_const
            else _build_cond_template(base_tmpl)
            if need_cond
            else _build_const_template(base_tmpl)
            if need_const
            else base_tmpl
        )
        vars_needed = _ensure_variables(vars_, need_cond, need_const)
        result.append(
            {
                "Pattern ID": vid,
                "Trigger": trig,
                "Template": tmpl,
                "Variables": vars_needed,
                "Notes": notes,
            }
        )
    return result

# ---------------------------------------------------------------------------
# Pattern generation from diagram rules

def _slug(name: str) -> str:
    """Return a filesystem-friendly identifier component."""
    return re.sub(r"\W+", "_", name).strip("_")

def generate_patterns_from_config(cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate requirement pattern definitions from ``cfg``.

    Only Safety & AI relation rules are considered as they map directly to
    requirement rules.  Each allowed ``(source, relation, target)`` combination
    yields four variants (base, ``-COND``, ``-CONST`` and ``-COND-CONST``).
    """

    req_rules = {k.lower(): v for k, v in cfg.get("requirement_rules", {}).items()}
    sa_rules = cfg.get("safety_ai_relation_rules", {})
    patterns: List[Dict[str, Any]] = []

    for relation, sources in sa_rules.items():
        rule = req_rules.get(relation.lower())
        if not rule:
            continue
        action = rule.get("action", "")
        subject = rule.get("subject", "Engineering team")
        notes = "Instantiate on detected edge; add measurable criteria."

        for src, targets in sources.items():
            for dst in targets:
                pid = f"SA-{_slug(relation.lower())}-{_slug(src)}-{_slug(dst)}"
                trig = f"Safety&AI: {src} --[{relation}]--> {dst}"
                tmpl = (
                    f"{subject} shall {action} the <target_id> (<target_class>) "
                    f"using the <source_id> (<source_class>)."
                )
                base_pat = {
                    "Pattern ID": pid,
                    "Trigger": trig,
                    "Template": tmpl,
                    "Variables": [
                        "<source_id>",
                        "<source_class>",
                        "<target_id>",
                        "<target_class>",
                        "<acceptance_criteria>",
                    ],
                    "Notes": notes,
                }
                patterns.extend(_expand_variants(base_pat))
    # Deterministic ordering for stability
    return sorted(patterns, key=lambda p: p["Pattern ID"])

# Convenience CLI ------------------------------------------------------------

def main(argv: Iterable[str] | None = None) -> int:
    """Command line entry point."""
    import argparse

    ap = argparse.ArgumentParser(description="Generate requirement patterns from diagram rules")
    ap.add_argument("--config", default=Path("config/diagram_rules.json"), type=Path, help="Diagram rules JSON path")
    ap.add_argument("--out", default=Path("config/requirement_patterns.json"), type=Path, help="Output JSON path")
    ap.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    args = ap.parse_args(list(argv) if argv is not None else None)

    cfg = json.loads(args.config.read_text())
    pats = generate_patterns_from_config(cfg)
    if args.pretty:
        args.out.write_text(json.dumps(pats, ensure_ascii=False, indent=2) + "\n")
    else:
        args.out.write_text(json.dumps(pats, ensure_ascii=False))
    print(f"Wrote {len(pats)} patterns to {args.out}")
    return 0

if __name__ == "__main__":  # pragma: no cover - CLI utility
    raise SystemExit(main())
