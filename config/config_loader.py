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

"""Utilities for reading JSON configuration files with comments.

The project relies on a central ``diagram_rules.json`` file that users edit by
hand.  Allowing JavaScript‐style comments makes the file approachable but the
standard :func:`json.loads` routine is very strict and rejects them.  This
module exposes :func:`load_json_with_comments` which performs lightweight
parsing to strip comments and optional trailing commas before handing the
resulting string to the JSON loader.

The implementation purposely avoids removing text inside string literals and
therefore works with URLs such as ``"http://example"``.
"""

from pathlib import Path
from typing import Any
import json
import re
import sys
import importlib.resources as resources
from tools.memory_manager import manager as memory_manager


def _ensure_list_of_strings(val: Any, name: str) -> None:
    """Raise :class:`ValueError` if *val* is not a list of strings."""
    if not isinstance(val, list) or any(not isinstance(v, str) for v in val):
        raise ValueError(f"{name} must be a list of strings")


def validate_diagram_rules(data: Any) -> dict[str, Any]:
    """Validate diagram rule configuration structure.

    Parameters
    ----------
    data:
        Parsed JSON object representing the diagram rules configuration.

    Returns
    -------
    dict
        The validated configuration.

    Raises
    ------
    ValueError
        If the configuration does not follow the expected structure.
    """

    if not isinstance(data, dict):
        raise ValueError("Configuration root must be a JSON object")

    list_fields = [
        "ai_nodes",
        "ai_relations",
        "arch_diagram_types",
        "governance_node_types",
        "governance_element_nodes",
        "gate_node_types",
        "guard_nodes",
    ]
    for field in list_fields:
        if field in data:
            _ensure_list_of_strings(data[field], field)

    if "requirement_rules" in data or "relationship_rules" in data:
        rr = data.get("requirement_rules", data.get("relationship_rules", {}))
        if not isinstance(rr, dict):
            raise ValueError("requirement_rules must be an object")
        for label, info in rr.items():
            if not isinstance(info, dict):
                raise ValueError(f"requirement_rules[{label}] must be an object")
            action = info.get("action")
            if not isinstance(action, str):
                raise ValueError(
                    f"requirement_rules[{label}]['action'] must be a string"
                )
            if "subject" in info and not isinstance(info["subject"], str):
                raise ValueError(
                    f"requirement_rules[{label}]['subject'] must be a string"
                )
            if "constraint" in info and not isinstance(info["constraint"], bool):
                raise ValueError(
                    f"requirement_rules[{label}]['constraint'] must be a boolean"
                )
            if "targets" in info:
                tgt = info["targets"]
                if not isinstance(tgt, int) or tgt < 1:
                    raise ValueError(
                        f"requirement_rules[{label}]['targets'] must be a positive integer"
                    )
            if "template" in info and not isinstance(info["template"], str):
                raise ValueError(
                    f"requirement_rules[{label}]['template'] must be a string"
                )
            if "variables" in info:
                vars_ = info["variables"]
                if not isinstance(vars_, list) or any(
                    not isinstance(v, str) for v in vars_
                ):
                    raise ValueError(
                        f"requirement_rules[{label}]['variables'] must be a list of strings"
                    )

    if "requirement_sequences" in data:
        rs = data["requirement_sequences"]
        if not isinstance(rs, dict):
            raise ValueError("requirement_sequences must be an object")
        for label, info in rs.items():
            if not isinstance(info, dict):
                raise ValueError(
                    f"requirement_sequences[{label}] must be an object"
                )
            rels = info.get("relations")
            if (
                not isinstance(rels, list)
                or len(rels) < 2
                or any(not isinstance(r, str) for r in rels)
            ):
                raise ValueError(
                    f"requirement_sequences[{label}]['relations'] must be a list of at least two strings"
                )
            if "subject" in info and not isinstance(info["subject"], str):
                raise ValueError(
                    f"requirement_sequences[{label}]['subject'] must be a string"
                )
            if "role_subject" in info and not isinstance(info["role_subject"], bool):
                raise ValueError(
                    f"requirement_sequences[{label}]['role_subject'] must be a boolean"
                )
            if "action" in info and not isinstance(info["action"], str):
                raise ValueError(
                    f"requirement_sequences[{label}]['action'] must be a string"
                )
            if "template" in info and not isinstance(info["template"], str):
                raise ValueError(
                    f"requirement_sequences[{label}]['template'] must be a string"
                )
            if "variables" in info:
                _ensure_list_of_strings(
                    info["variables"],
                    f"requirement_sequences[{label}]['variables']",
                )

    if "node_roles" in data:
        nr = data["node_roles"]
        if not isinstance(nr, dict):
            raise ValueError("node_roles must be an object")
        allowed = {"subject", "action", "condition", "constraint", "object"}
        for node, role in nr.items():
            if role not in allowed:
                raise ValueError(
                    f"node_roles[{node}] has invalid role '{role}'"
                )

    if "connection_rules" in data:
        cr = data["connection_rules"]
        if not isinstance(cr, dict):
            raise ValueError("connection_rules must be an object")
        for diag, conns in cr.items():
            if not isinstance(conns, dict):
                raise ValueError(f"connection_rules[{diag}] must be an object")
            for conn, srcs in conns.items():
                if not isinstance(srcs, dict):
                    raise ValueError(
                        f"connection_rules[{diag}][{conn}] must be an object"
                    )
                for src, dests in srcs.items():
                    _ensure_list_of_strings(
                        dests, f"connection_rules[{diag}][{conn}][{src}]"
                    )

    if "node_connection_limits" in data:
        ncl = data["node_connection_limits"]
        if not isinstance(ncl, dict) or any(
            not isinstance(v, int) for v in ncl.values()
        ):
            raise ValueError(
                "node_connection_limits must map node types to integer limits"
            )

    return data


def validate_requirement_patterns(data: Any) -> list[dict[str, Any]]:
    """Validate requirement pattern configuration structure.

    Parameters
    ----------
    data:
        Parsed JSON object representing the requirement pattern configuration.

    Returns
    -------
    list
        The validated list of pattern dictionaries.

    Raises
    ------
    ValueError
        If the configuration does not follow the expected structure.
    """

    if not isinstance(data, list):
        raise ValueError("Configuration root must be a list")

    for idx, pat in enumerate(data):
        if not isinstance(pat, dict):
            raise ValueError(f"Pattern at index {idx} must be an object")

        required = ["Pattern ID", "Trigger", "Template", "Variables"]
        for field in required:
            if field not in pat:
                raise ValueError(f"Pattern at index {idx} missing '{field}'")
        if not isinstance(pat["Pattern ID"], str):
            raise ValueError(f"Pattern ID at index {idx} must be a string")
        if not isinstance(pat["Trigger"], str):
            raise ValueError(f"Trigger at index {idx} must be a string")
        if not isinstance(pat["Template"], str):
            raise ValueError(f"Template at index {idx} must be a string")
        _ensure_list_of_strings(pat["Variables"], f"pattern[{idx}]['Variables']")
        if "Notes" in pat and not isinstance(pat["Notes"], str):
            raise ValueError(f"Notes at index {idx} must be a string")

    return data


def validate_report_template(data: Any) -> dict[str, Any]:
    """Validate PDF report template structure."""

    if not isinstance(data, dict):
        raise ValueError("Configuration root must be a JSON object")
    elements = data.get("elements", {})
    if not isinstance(elements, dict):
        raise ValueError("'elements' must be an object")
    for name, kind in elements.items():
        if not isinstance(name, str) or not isinstance(kind, str):
            raise ValueError("elements must map names to string types")

    sections = data.get("sections", [])
    if not isinstance(sections, list):
        raise ValueError("'sections' must be a list")
    for idx, sec in enumerate(sections):
        if not isinstance(sec, dict):
            raise ValueError(f"sections[{idx}] must be an object")
        title = sec.get("title")
        content = sec.get("content")
        if not isinstance(title, str):
            raise ValueError(f"sections[{idx}]['title'] must be a string")
        if not isinstance(content, str):
            raise ValueError(f"sections[{idx}]['content'] must be a string")

        for placeholder in re.findall(r"<([^<>]+)>", content):
            name = placeholder.strip().split()[0]
            if name.startswith("/"):
                name = name[1:]
            if name.endswith("/"):
                name = name[:-1]
            if name.lower() in {
                "b",
                "i",
                "u",
                "em",
                "strong",
                "p",
                "br",
                "span",
                "div",
                "img",
                "a",
            }:
                continue
            if name not in elements:
                raise ValueError(
                    f"sections[{idx}] references unknown element '{name}'"
                )

    return data


def _strip_comments(text: str) -> str:
    """Return *text* with // and /* ... */ comments removed.

    The function walks the string character by character so that comment tokens
    inside quoted strings remain untouched.
    """

    result: list[str] = []
    in_str = False
    escape = False
    i = 0
    while i < len(text):
        ch = text[i]
        if escape:
            result.append(ch)
            escape = False
            i += 1
            continue
        if ch == "\\":
            result.append(ch)
            escape = True
            i += 1
            continue
        if ch == '"':
            in_str = not in_str
            result.append(ch)
            i += 1
            continue
        if not in_str and text.startswith("//", i):
            # Skip to end of line
            j = text.find("\n", i)
            if j == -1:
                break
            i = j + 1
            continue
        if not in_str and text.startswith("/*", i):
            j = text.find("*/", i + 2)
            if j == -1:
                break
            i = j + 2
            continue
        result.append(ch)
        i += 1
    return "".join(result)


def _load_json_with_comments_uncached(p: Path) -> Any:
    """Internal helper performing the actual file reading."""
    candidates = [p]
    if getattr(sys, "frozen", False):  # pragma: no cover - only in bundled app
        exe_dir = Path(sys.executable).resolve().parent
        candidates.append(exe_dir / p.name)
        candidates.append(exe_dir / "config" / p.name)
    cwd = Path.cwd()
    candidates.append(cwd / p.name)
    candidates.append(cwd / "config" / p.name)

    text = None
    for cand in candidates:
        try:
            text = _strip_comments(cand.read_text())
            break
        except FileNotFoundError:
            continue
    if text is None:
        try:
            idx = p.parts.index("config")
            pkg = ".".join(p.parts[idx:-1])
        except ValueError:
            pkg = p.parent.name

        try:
            with resources.as_file(resources.files(pkg) / p.name) as res:
                text = _strip_comments(res.read_text())
        except ModuleNotFoundError as exc:  # pragma: no cover - resources missing
            raise FileNotFoundError(f"Unable to locate resource for {p}") from exc
    text = re.sub(r",\s*(?=[}\]])", "", text)
    return json.loads(text)


def load_json_with_comments(path: str | Path) -> Any:
    """Load a JSON file allowing // and /* */ comments and trailing commas.

    Results are cached via :mod:`tools.memory_manager` to avoid repeated disk
    reads when the same configuration file is requested multiple times.
    """
    p = Path(path)
    key = f"json:{p.resolve()}"
    return memory_manager.lazy_load(key, lambda: _load_json_with_comments_uncached(p))


def load_diagram_rules(path: str | Path) -> dict[str, Any]:
    """Load and validate the diagram rules configuration file."""
    data = load_json_with_comments(path)
    data = validate_diagram_rules(data)

    gov_rules = data.get("connection_rules", {}).get("Governance Diagram", {})

    ai_nodes = set(data.get("ai_nodes", []))
    gov_nodes = set(data.get("governance_element_nodes", []))
    all_nodes = ai_nodes | gov_nodes

    for mapping in gov_rules.values():
        for node in all_nodes:
            mapping.setdefault(node, [])

    return data


def load_requirement_patterns(path: str | Path) -> list[dict[str, Any]]:
    """Load and validate the requirement pattern configuration file."""
    data = load_json_with_comments(path)
    return validate_requirement_patterns(data)


def load_report_template(path: str | Path) -> dict[str, Any]:
    """Load and validate the PDF report template configuration file."""
    data = load_json_with_comments(path)
    return validate_report_template(data)
