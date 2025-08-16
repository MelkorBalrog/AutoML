"""Basic governance diagram support for safety workflows."""

from dataclasses import dataclass, field
from typing import Any, Iterator, List, Tuple

from pathlib import Path
from config import load_diagram_rules, load_json_with_comments
from .requirement_rule_generator import generate_patterns_from_config

import networkx as nx
import re

_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config/diagram_rules.json"
_CONFIG = load_diagram_rules(_CONFIG_PATH)

# Element and relationship types associated with AI & safety lifecycle nodes.
_AI_NODES = set(_CONFIG.get("ai_nodes", []))
_AI_RELATIONS = set(_CONFIG.get("ai_relations", []))

# Map relationship labels or connection types to requirement actions.  Each
# entry defines the verb to use, whether the destination element acts as a
# constraint instead of an object, and an optional default subject.  The
# resulting requirement follows the ISO/IEC/IEEE 29148 pattern
# ``[CND] <SUB> shall <ACT> [OBJ] [CON].``
_REQUIREMENT_RULES: dict[str, dict[str, str | bool]] = _CONFIG.get(
    "requirement_rules", _CONFIG.get("relationship_rules", {})
)

# Map node types to default requirement roles so that the generator can
# identify the subject, object or constraint directly from the model.
_NODE_ROLES = _CONFIG.get("node_roles", {})

# Optional requirement pattern definitions allowing users to customise
# requirement text based on specific relationship triggers.  Each pattern
# entry is keyed by ``(source_type, label, dest_type)`` so that users can
# modify or extend the patterns in ``config/requirement_patterns.json``
# without touching the code.
_PATTERN_PATH = Path(__file__).resolve().parents[1] / "config/requirement_patterns.json"
try:
    _PATTERN_DEFS = load_json_with_comments(_PATTERN_PATH)
except FileNotFoundError:  # pragma: no cover - optional file
    _PATTERN_DEFS = []

# Automatically derive requirement patterns from the diagram rules so that any
# configuration updates are reflected without manual pattern maintenance.
_PATTERN_DEFS.extend(generate_patterns_from_config(_CONFIG))

_TRIGGER_RE = re.compile(r"[^:]+:\s*(.*?)\s*--\[(.*?)\]-->\s*(.*)")
_PATTERN_MAP: dict[tuple[str, str, str], list[dict[str, str]]] = {}
for pat in _PATTERN_DEFS:
    trig = pat.get("Trigger", "")
    tmpl = pat.get("Template", "")
    m = _TRIGGER_RE.fullmatch(trig)
    if not m:
        continue
    src_t, label, dst_t = [g.strip().lower() for g in m.groups()]
    key = (src_t, label.lower(), dst_t)
    _PATTERN_MAP.setdefault(key, []).append(pat)


def _apply_pattern(
    pat: dict[str, str],
    src: str,
    dst: str,
    src_type: str,
    dst_type: str,
    cond: str | None,
    constraint: str | None,
) -> tuple[str, list[str]]:
    """Instantiate a pattern template with diagram values.

    Returns the instantiated text along with any template variables that
    could not be resolved automatically.  Variables are taken from the
    pattern's ``Variables`` list and stripped of the surrounding angle
    brackets so they can be presented to users for manual completion.
    """

    template = pat.get("Template", "")
    variables = [v.strip("<>") for v in pat.get("Variables", [])]

    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        if key == "source_id" or key == src_type:
            variables[:] = [v for v in variables if v != key]
            return src
        if key == "source_class":
            variables[:] = [v for v in variables if v != key]
            return src_type
        if key == "target_id" or key == dst_type:
            variables[:] = [v for v in variables if v != key]
            return dst
        if key == "target_class":
            variables[:] = [v for v in variables if v != key]
            return dst_type
        if key == "condition":
            variables[:] = [v for v in variables if v != key]
            return cond or ""
        if key == "constraint":
            variables[:] = [v for v in variables if v != key]
            return constraint or ""
        return ""

    result = re.sub(r"<([^>]+)>", repl, template)
    return result, variables


def reload_config() -> None:
    """Reload governance-related configuration."""
    global _CONFIG, _AI_NODES, _AI_RELATIONS, _REQUIREMENT_RULES, _NODE_ROLES, _PATTERN_DEFS, _PATTERN_MAP
    _CONFIG = load_diagram_rules(_CONFIG_PATH)
    _AI_NODES = set(_CONFIG.get("ai_nodes", []))
    _AI_RELATIONS = set(_CONFIG.get("ai_relations", []))
    _REQUIREMENT_RULES = _CONFIG.get(
        "requirement_rules", _CONFIG.get("relationship_rules", {})
    )
    _NODE_ROLES = _CONFIG.get("node_roles", {})

    try:
        _PATTERN_DEFS = load_json_with_comments(_PATTERN_PATH)
    except FileNotFoundError:  # pragma: no cover - optional file
        _PATTERN_DEFS = []

    # Regenerate patterns derived from the current diagram rule configuration
    _PATTERN_DEFS.extend(generate_patterns_from_config(_CONFIG))
    _PATTERN_MAP = {}
    for pat in _PATTERN_DEFS:
        trig = pat.get("Trigger", "")
        tmpl = pat.get("Template", "")
        m = _TRIGGER_RE.fullmatch(trig)
        if not m:
            continue
        src_t, label, dst_t = [g.strip().lower() for g in m.groups()]
        key = (src_t, label.lower(), dst_t)
        _PATTERN_MAP.setdefault(key, []).append(pat)


@dataclass
class GeneratedRequirement:
    """Structured requirement composed from diagram elements.

    The dataclass exposes the individual requirement components (condition,
    subject, action, object and constraint) alongside the requirement
    category.  Each field except ``action`` is optional and therefore given a
    default value.  This ordering avoids the ``TypeError`` raised when optional
    fields precede required ones in a :func:`dataclass` definition and mirrors
    how requirements are instantiated in the generator.
    """

    action: str
    condition: str | None = None
    subject: str | None = None
    obj: str | None = None
    constraint: str | None = None
    origin: str | None = None
    source: str | None = None
    req_type: str = "organizational"
    text_override: str | None = None
    variables: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        if self.text_override is not None:
            return self.text_override
        parts: List[str] = []
        if self.condition:
            parts.append(f"If {self.condition},")
        if self.origin:
            parts.append(f"after '{self.origin}',")
        subject = self.subject or "Task"
        main = f"{subject} shall {self.action}"
        if self.obj:
            main += f" '{self.obj}'"
        if self.constraint:
            main += f" '{self.constraint}'"
        main += "."
        parts.append(main)
        return " ".join(parts)

    def __iter__(self) -> Iterator[str]:
        yield self.text
        yield self.req_type

    def __getitem__(self, idx: int) -> str:
        return (self.text, self.req_type)[idx]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.text

    def __contains__(self, item: str) -> bool:  # pragma: no cover - trivial
        return (
            item in self.text
            or item in self.req_type
            or (self.origin and item in self.origin)
            or (self.source and item in self.source)
        )


def _requirement_complexity(req: GeneratedRequirement | tuple[str, str]) -> int:
    """Return a simple complexity score for a requirement.

    Generated requirements become more complex as additional components such
    as conditions, objects or constraints are present.  Tuple requirements are
    scored by their textual length.  The score is only used for relative
    comparisons so the exact values are not important.
    """

    if isinstance(req, GeneratedRequirement):
        return sum(
            1
            for attr in (
                req.condition,
                req.obj,
                req.constraint,
                req.origin,
                req.text_override,
            )
            if attr
        )
    return len(req[0])


@dataclass
class GovernanceDiagram:
    """A very small governance diagram using a directed graph.

    Nodes in the graph represent tasks and edges represent sequence flows.
    The diagram is intentionally lightweight but can be tailored and extended
    by users to model project-specific safety governance workflows.
    """

    graph: nx.DiGraph = field(default_factory=nx.DiGraph)
    # Explicit mapping of edges to their metadata so the diagram works even
    # when :mod:`networkx` is not fully featured.
    edge_data: dict[tuple[str, str], dict[str, str | None]] = field(
        default_factory=dict
    )
    # Track the original diagram object type for each task so requirements can
    # be categorised.  Tasks originating from AI & safety nodes produce AI
    # safety requirements.
    node_types: dict[str, str] = field(default_factory=dict)
    # Optional mapping of task names to their data source compartments.
    node_sources: dict[str, list[str]] = field(default_factory=dict)

    def _role_for(self, name: str) -> str:
        """Return the requirement role for a node name."""
        ntype = self.node_types.get(name, "")
        return _NODE_ROLES.get(ntype, "object")

    def _default_action(self, name: str) -> str:
        """Return a generic verb phrase for a task name.

        Data acquisition nodes previously used the raw node label as the
        action, which could generate awkward requirements such as
        "Engineering team shall Data acquisition from …" when the node name
        itself was "Data acquisition".  This helper normalizes common node
        types to more natural verbs so generated requirements follow the
        expected subject–action–object structure.
        """

        ntype = self.node_types.get(name)
        if ntype == "Data acquisition":
            return "acquire data"
        return name.lower()

    def add_task(
        self,
        name: str,
        node_type: str = "Action",
        compartments: list[str] | None = None,
    ) -> None:
        """Add a task node to the diagram.

        Parameters
        ----------
        name:
            Task identifier to add to the diagram.
        node_type:
            Original diagram object type.
        compartments:
            Optional list of compartment labels for ``Data acquisition`` nodes
            describing the sources of acquired data.
        """
        self.graph.add_node(name)
        self.node_types[name] = node_type
        if compartments:
            self.node_sources[name] = [c for c in compartments if c]

    def add_flow(
        self,
        src: str,
        dst: str,
        condition: str | None = None,
        conn_type: str = "Flow",
    ) -> None:
        """Add a directed flow between two existing tasks.

        Parameters
        ----------
        src, dst:
            Names of the existing source and destination tasks.
        condition:
            Optional textual condition that must hold for the flow to occur.
        conn_type:
            Connection type from the original diagram; defaults to ``"Flow"``.
        """

        if not self.graph.has_node(src) or not self.graph.has_node(dst):
            raise ValueError("Both tasks must exist before creating a flow")
        self.graph.add_edge(src, dst)
        self.edge_data[(src, dst)] = {
            "kind": "flow",
            "condition": condition,
            "label": None,
            "conn_type": conn_type,
        }

    def add_relationship(
        self,
        src: str,
        dst: str,
        condition: str | None = None,
        label: str | None = None,
        conn_type: str | None = None,
        from_repo: bool = False,
    ) -> None:
        """Add a non-flow relationship between two existing tasks.

        Parameters
        ----------
        src, dst:
            Names of the existing source and destination tasks.
        condition:
            Optional textual condition that must hold for the relationship.
        label:
            Optional label describing the relationship between the tasks.
        conn_type:
            Connection type from the original diagram, used to determine the
            requirement category.
        """

        if not self.graph.has_node(src) or not self.graph.has_node(dst):
            raise ValueError("Both tasks must exist before creating a relationship")
        self.graph.add_edge(src, dst)
        self.edge_data[(src, dst)] = {
            "kind": "relationship",
            "condition": condition,
            "label": label,
            "conn_type": conn_type,
            "from_repo": from_repo,
        }

    def tasks(self) -> List[str]:
        """Return all task node names in the diagram."""
        return list(self.graph.nodes())

    def flows(self) -> List[Tuple[str, str]]:
        """Return all directed flow edges in the diagram."""
        edges: List[Tuple[str, str]] = []
        for u, v in self.graph.edges():
            data = self.edge_data.get((u, v))
            if data is None or data.get("kind") == "flow":
                edges.append((u, v))
        return edges

    def relationships(self) -> List[Tuple[str, str]]:
        """Return all non-flow relationships in the diagram."""
        return [
            (u, v)
            for (u, v), data in self.edge_data.items()
            if data.get("kind") == "relationship"
        ]

    def generate_requirements(self) -> List[GeneratedRequirement | tuple[str, str]]:
        """Generate structured requirements from the diagram."""

        requirements: List[GeneratedRequirement | tuple[str, str]] = []

        decision_sources: dict[str, str] = {}
        for src, dst in self.graph.edges():
            if self.node_types.get(dst) == "Decision":
                decision_sources[dst] = src

        for src, dst in self.graph.edges():
            if self.node_types.get(dst) == "Decision":
                continue

            data = self.edge_data.get(
                (src, dst), {"kind": "flow", "condition": None, "label": None}
            )
            cond = data.get("condition")
            kind = data.get("kind")
            label = data.get("label")
            conn_type = data.get("conn_type")

            # Skip standalone reuse links between lifecycle phases. The
            # corresponding transition requirement will incorporate reuse
            # information so an additional requirement would be redundant.
            if (
                conn_type == "Re-use"
                and self.node_types.get(src) == "Lifecycle Phase"
                and self.node_types.get(dst) == "Lifecycle Phase"
            ):
                continue

            req_type = "organizational"
            if (
                conn_type in _AI_RELATIONS
                or self.node_types.get(src) in _AI_NODES
                or self.node_types.get(dst) in _AI_NODES
            ):
                req_type = "AI safety"

            # Express lifecycle phase transitions explicitly.
            if (
                kind == "flow"
                and self.node_types.get(src) == "Lifecycle Phase"
                and self.node_types.get(dst) == "Lifecycle Phase"
            ):
                reuse_edge = self.edge_data.get((dst, src), {})
                has_reuse = reuse_edge.get("conn_type") == "Re-use"
                text = f"{src} shall transition to '{dst}'"
                if has_reuse:
                    text += f" reusing outputs from '{src}'"
                if cond:
                    text += f" only after {cond}"
                text += "."
                requirements.append((text, req_type))
                continue

            origin = None
            subject = src
            obj: str | None = dst
            constraint: str | None = None
            action: str
            explicit_subject = None

            if data.get("origin_src"):
                origin = src
            elif self.node_types.get(src) == "Decision":
                origin = decision_sources.get(src)
                if origin and kind == "flow":
                    subject = origin
            if kind == "flow":
                action = "precede"
            else:
                key = (label or conn_type or "").lower()
                rule = _REQUIREMENT_RULES.get(key, {})
                action = str(rule.get("action", label or "relate to"))
                explicit_subject = rule.get("subject")
                if explicit_subject:
                    subject = str(explicit_subject)
                    if origin is None and data.get("from_repo"):
                        origin = src
                if rule.get("constraint"):
                    constraint = dst
                    obj = None
                elif not label and not rule:
                    action = "be related to"

            if obj is not None and explicit_subject is None:
                s_role = self._role_for(subject)
                d_role = self._role_for(obj)
                if s_role != "subject" and d_role == "subject":
                    subject, obj = obj, subject
            text_override: str | None = None
            src_type = self.node_types.get(src, "")
            dst_type = self.node_types.get(dst, "")
            patterns = _PATTERN_MAP.get(
                (src_type.lower(), (label or conn_type or "").lower(), dst_type.lower()),
                [],
            )
            base = cond_pat = cond_const_pat = const_pat = None
            for pat in patterns:
                tmpl = pat.get("Template", "")
                has_cond = "<condition>" in tmpl or "<acceptance_criteria>" in tmpl
                has_const = "<constraint>" in tmpl
                if has_cond and has_const and not cond_const_pat:
                    cond_const_pat = pat
                elif has_const and not has_cond and not const_pat:
                    const_pat = pat
                elif has_cond and not has_const and not cond_pat:
                    cond_pat = pat
                elif not has_cond and not has_const and not base:
                    base = pat
            pattern = None
            if cond and constraint and cond_const_pat:
                pattern = cond_const_pat
            elif constraint and const_pat:
                pattern = const_pat
            elif cond and cond_pat and not base:
                pattern = cond_pat
            else:
                pattern = base or cond_pat or const_pat or cond_const_pat
            pattern_vars: list[str] = []
            if pattern:
                text_override, pattern_vars = _apply_pattern(
                    pattern, src, dst, src_type, dst_type, cond, constraint
                )
                if (
                    cond
                    and "<condition>" not in pattern.get("Template", "")
                    and "<acceptance_criteria>" not in pattern.get("Template", "")
                ):
                    text_override = f"If {cond}, {text_override}"

            requirements.append(
                GeneratedRequirement(
                    action=action,
                    condition=cond,
                    subject=subject,
                    obj=obj,
                    constraint=constraint,
                    origin=origin if (origin and kind != "flow") else None,
                    source=src,
                    req_type=req_type,
                    text_override=text_override,
                    variables=pattern_vars,
                )
            )

        # Create explicit requirements for Data acquisition nodes listing their
        # configured compartments as data sources.  Each compartment becomes a
        # separate requirement so that individual data sources remain traceable.
        for node, sources in self.node_sources.items():

            req_type = (
                "AI safety" if self.node_types.get(node) in _AI_NODES else "organizational"
            )
            subject = "Engineering team" if req_type == "AI safety" else "Organization"
            action = f"{self._default_action(node)} from"
            for src in sources:
                requirements.append(
                    GeneratedRequirement(
                        action=action,
                        subject=subject,
                        obj=src,
                        req_type=req_type,
                    )
                )

        for node in self.graph.nodes():
            role = self._role_for(node)
            if role != "action" and self.node_types.get(node) != "Data acquisition":
                continue
            req_type = (
                "AI safety" if self.node_types.get(node) in _AI_NODES else "organizational"
            )
            subject = "Engineering team" if req_type == "AI safety" else "Organization"
            requirements.append(
                GeneratedRequirement(
                    action=self._default_action(node),
                    subject=subject,
                    req_type=req_type,
                )
            )
        # When many similar requirements are produced, keep only the most
        # detailed one for a given subject/action pair.  This avoids clutter
        # from generic requirements when a more specific alternative exists.
        grouped: dict[tuple[str | None, str, str | None], GeneratedRequirement | tuple[str, str]] = {}
        for req in requirements:
            if isinstance(req, GeneratedRequirement):
                key = (req.subject, req.action, req.obj)
            else:
                key = (req[0], "text", None)
            existing = grouped.get(key)
            if not existing or _requirement_complexity(req) > _requirement_complexity(existing):
                grouped[key] = req

        # Drop generic requirements with no object when a more specific
        # requirement with the same subject and action is available.
        result: list[GeneratedRequirement | tuple[str, str]] = []
        for key, req in grouped.items():
            if isinstance(req, GeneratedRequirement) and req.obj is None:
                subj, act, _ = key
                if any(
                    isinstance(other, GeneratedRequirement)
                    and other.subject == subj
                    and other.obj is not None
                    and (
                        other.action == act
                        or other.action.startswith(f"{act} ")
                    )
                    for other in grouped.values()
                    if other is not req
                ):
                    continue
            result.append(req)

        return result

    @classmethod
    def default_from_work_products(cls, names: List[str]) -> "GovernanceDiagram":
        """Create a default sequential diagram from the given work products."""
        diagram = cls()
        for name in names:
            diagram.add_task(name)
        tasks = diagram.tasks()
        for src, dst in zip(tasks, tasks[1:]):
            diagram.add_flow(src, dst)
        return diagram

    @classmethod
    def from_repository(cls, repo: Any, diag_id: str) -> "GovernanceDiagram":
        """Build a :class:`GovernanceDiagram` from a repository diagram.

        Parameters
        ----------
        repo:
            Repository instance providing ``diagrams`` and ``elements`` maps.
        diag_id:
            Identifier of the governance diagram to convert.
        """

        diagram = cls()
        src_diagram = repo.diagrams.get(diag_id)
        if not src_diagram:
            return diagram

        id_to_name: dict[int, str] = {}
        decision_sources: dict[int, str] = {}
        for obj in getattr(src_diagram, "objects", []):
            odict = obj if isinstance(obj, dict) else obj.__dict__
            obj_type = odict.get("obj_type")
            obj_id = odict.get("obj_id")
            if obj_type == "Decision":
                decision_sources[obj_id] = ""
            elem_id = odict.get("element_id")
            name = ""
            if elem_id and elem_id in repo.elements:
                name = repo.elements[elem_id].name
            if not name:
                name = odict.get("properties", {}).get("name", "")
            if name:
                props = odict.get("properties", {})
                comp_str = props.get("compartments", "")
                comps = [c for c in comp_str.split(";") if c]
                diagram.add_task(
                    name,
                    node_type=obj_type or "Action",
                    compartments=comps or None,
                )
                id_to_name[obj_id] = name

        # Map decision nodes to their predecessor action
        for conn in getattr(src_diagram, "connections", []):
            cdict = conn if isinstance(conn, dict) else conn.__dict__
            if cdict.get("conn_type") != "Flow":
                continue
            src_name = id_to_name.get(cdict.get("src"))
            dst_id = cdict.get("dst")
            if src_name and dst_id in decision_sources:
                decision_sources[dst_id] = src_name

        # Map decision nodes to their predecessor action
        for conn in getattr(src_diagram, "connections", []):
            cdict = conn if isinstance(conn, dict) else conn.__dict__
            src_id = cdict.get("src")
            dst_id = cdict.get("dst")
            name = cdict.get("name")
            props = cdict.get("properties", {})
            cond = props.get("condition")
            if not cond:
                guard = cdict.get("guard")
                if guard:
                    ops = cdict.get("guard_ops") or []
                    sep = f" {ops[0]} " if ops else " AND "
                    cond = sep.join(guard)
                elif name and cdict.get("conn_type") == "Flow":
                    cond = name
            conn_type = cdict.get("conn_type")
            cond_prop = cdict.get("properties", {}).get("condition")
            guards = cdict.get("guard") or []
            guard_ops = cdict.get("guard_ops") or []
            if isinstance(guards, str):
                guards = [guards]
            if isinstance(guard_ops, str):
                guard_ops = [guard_ops]
            guard_text: str | None = None
            if guards:
                parts: list[str] = []
                for i, g in enumerate(guards):
                    if i == 0:
                        parts.append(g)
                    else:
                        op = guard_ops[i - 1] if i - 1 < len(guard_ops) else "AND"
                        parts.append(f"{op} {g}")
                guard_text = " ".join(parts)
            if cdict.get("conn_type") == "Flow":
                cond = cond_prop or guard_text or name
                src = id_to_name.get(src_id)
                dst = id_to_name.get(dst_id)
                if src and dst:
                    diagram.add_flow(src, dst, cond)
                elif src_id in decision_sources and dst:
                    prev = decision_sources.get(src_id)
                    if prev:
                        diagram.add_flow(prev, dst, cond)
            else:
                src = id_to_name.get(src_id) or decision_sources.get(src_id)
                dst = id_to_name.get(dst_id)
                if not src or not dst:
                    continue
                cond = cond_prop or guard_text
                if cond is None and name is not None:
                    diagram.add_relationship(src, dst, condition=name, conn_type=conn_type)
                    diagram.edge_data[(src, dst)]["origin_src"] = True
                else:
                    diagram.add_relationship(
                        src,
                        dst,
                        condition=cond,
                        label=name,
                        conn_type=conn_type,
                        from_repo=True,
                    )

        return diagram

if __name__ == "__main__":  # pragma: no cover - example usage for docs
    demo = GovernanceDiagram()
    demo.add_task("Draft Plan")
    demo.add_task("Review Plan")
    demo.add_flow("Draft Plan", "Review Plan")
    demo.add_relationship(
        "Review Plan", "Draft Plan", condition="changes requested", label="rework"
    )
    for requirement in demo.generate_requirements():
        print(requirement)
