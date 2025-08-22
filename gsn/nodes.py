"""Basic data structures for GSN argumentation diagrams."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
import uuid
import logging

ALLOWED_AWAY_TYPES = {"Goal", "Solution", "Context", "Assumption", "Justification"}


logger = logging.getLogger(__name__)


@dataclass
class GSNNode:
    """Represents a node in a GSN argumentation diagram.

    Parameters
    ----------
    user_name:
        Human readable label for the node (name).
    description:
        Optional description shown beneath the name when rendering.
    node_type:
        One of ``Goal``, ``Strategy``, ``Solution``, ``Assumption``,
        ``Justification`` or ``Context``.
    x, y:
        Optional coordinates used when rendering the diagram.
    """

    user_name: str
    node_type: str
    description: str = ""
    x: float = 50
    y: float = 50
    children: List["GSNNode"] = field(default_factory=list)
    parents: List["GSNNode"] = field(default_factory=list)
    # Track which child links are "in context" relationships.  We keep a
    # separate list rather than encoding the relationship directly in
    # ``children`` so existing code that iterates over ``children`` continues
    # to work unchanged.
    context_children: List["GSNNode"] = field(default_factory=list)
    is_primary_instance: bool = True
    original: Optional["GSNNode"] = field(default=None, repr=False)
    unique_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    work_product: str = ""
    evidence_link: str = ""
    spi_target: str = ""
    evidence_sufficient: bool = False
    manager_notes: str = ""

    def __post_init__(self) -> None:  # pragma: no cover - trivial
        # A freshly created node is considered its own original instance.
        if self.original is None:
            self.original = self

    # ------------------------------------------------------------------
    def add_child(self, child: "GSNNode", relation: str = "solved") -> None:
        """Attach *child* to this node, updating parent/child lists.

        Parameters
        ----------
        child:
            The :class:`GSNNode` to attach as a child.
        relation:
            Either ``"solved"`` for a solved-by connection or ``"context"``
            for an in-context-of relationship.  Defaults to ``"solved"``.

        Raises
        ------
        ValueError
            If the requested relationship between the two node types is not
            allowed by the GSN standard.
        """

        if relation not in {"solved", "context"}:
            raise ValueError(f"Unknown relationship: {relation}")

        if relation == "solved":
            allowed = {
                "Goal": {"Goal", "Strategy", "Solution", "Module"},
                "Strategy": {"Goal"},
                "Module": {"Goal", "Strategy", "Solution", "Module"},
            }
            if self.node_type not in allowed or child.node_type not in allowed[self.node_type]:
                raise ValueError(
                    f"{self.node_type} cannot be solved by {child.node_type}"
                )
        else:  # relation == "context"
            allowed = {
                "Goal": {"Context", "Assumption", "Justification"},
                "Strategy": {"Context", "Assumption", "Justification"},
                "Solution": {"Context", "Assumption", "Justification"},
                "Module": {"Context", "Assumption", "Justification"},
                "Context": {"Context", "Assumption", "Justification"},
                "Assumption": {"Context", "Assumption", "Justification"},
                "Justification": {"Context", "Assumption", "Justification"},
            }
            if self.node_type not in allowed or child.node_type not in allowed[self.node_type]:
                raise ValueError(
                    f"{self.node_type} cannot have context {child.node_type}"
                )

        if child not in self.children:
            self.children.append(child)
        if self not in child.parents:
            child.parents.append(self)
        if relation == "context":
            if child not in self.context_children:
                self.context_children.append(child)
        elif child in self.context_children:
            self.context_children.remove(child)

    # ------------------------------------------------------------------
    def clone(self, parent: Optional["GSNNode"] = None) -> "GSNNode":
        """Return a copy of this node referencing the same original.

        The clone shares the ``original`` reference with the primary
        instance, enabling multiple diagram occurrences similar to away
        solutions in GSN 2.0.
        """
        if self.node_type not in ALLOWED_AWAY_TYPES:
            raise ValueError(
                f"Cloning not supported for node type '{self.node_type}'."
            )
        clone = GSNNode(
            self.user_name,
            self.node_type,
            description=self.description,
            x=self.x,
            y=self.y,
            is_primary_instance=False,
            original=self.original,
            work_product=self.work_product,
            evidence_link=self.evidence_link,
            evidence_sufficient=self.evidence_sufficient,
            manager_notes=self.manager_notes,
        )
        clone.work_product = self.work_product
        clone.spi_target = self.spi_target
        clone.manager_notes = self.manager_notes
        if parent is not None:
            # Context, Assumption and Justification clones must attach via an
            # ``in-context-of`` relationship rather than the default
            # ``solved-by`` link used for goals and solutions.
            relation = (
                "context"
                if self.node_type in {"Context", "Assumption", "Justification"}
                else "solved"
            )
            parent.add_child(clone, relation=relation)
        return clone

    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        """Return a JSON-serialisable representation of this node."""
        return {
            "unique_id": self.unique_id,
            "user_name": self.user_name,
            "description": self.description,
            "node_type": self.node_type,
            "x": self.x,
            "y": self.y,
            "children": [c.unique_id for c in self.children],
            "context": [c.unique_id for c in self.context_children],
            "is_primary_instance": self.is_primary_instance,
            "original": self.original.unique_id if self.original else None,
            "work_product": self.work_product,
            "evidence_link": self.evidence_link,
            "spi_target": self.spi_target,
            "evidence_sufficient": self.evidence_sufficient,
            "manager_notes": self.manager_notes,
        }

    # ------------------------------------------------------------------
    @classmethod
    def from_dict(cls, data: dict, nodes: Optional[dict] = None) -> "GSNNode":
        """Reconstruct a :class:`GSNNode` from *data*.

        The *nodes* mapping is used internally to resolve references
        between nodes when loading a full diagram.
        """
        nodes = nodes if nodes is not None else {}
        node = cls(
            data.get("user_name", ""),
            data.get("node_type", "Goal"),
            description=data.get("description", ""),
            x=data.get("x", 50),
            y=data.get("y", 50),
            is_primary_instance=data.get("is_primary_instance", True),
            unique_id=data.get("unique_id", str(uuid.uuid4())),
            work_product=data.get("work_product", ""),
            evidence_link=data.get("evidence_link", ""),
            spi_target=data.get("spi_target", ""),
            evidence_sufficient=data.get("evidence_sufficient", False),
            manager_notes=data.get("manager_notes", ""),
        )
        nodes[node.unique_id] = node
        # Temporarily store child and original references for second pass.
        # ``context`` links are tracked separately to distinguish relationship
        # types during deserialisation.
        node._tmp_children = list(data.get("children", []))  # type: ignore[attr-defined]
        node._tmp_context = list(data.get("context", []))  # type: ignore[attr-defined]
        node._tmp_original = data.get("original")  # type: ignore[attr-defined]
        return node

    # ------------------------------------------------------------------
    @staticmethod
    def resolve_references(nodes: dict) -> None:
        """Resolve child and original references after initial loading."""
        for node in nodes.values():
            # ``children`` in previously saved models may contain context
            # node identifiers as well as solved-by relationships.  To avoid
            # loading errors when enforcing strict relationship validation we
            # ignore any IDs that are also listed in ``context`` and handle
            # them only as context links below.
            context_ids = set(getattr(node, "_tmp_context", []))
            children_ids = getattr(node, "_tmp_children", [])
            for cid in children_ids:
                if cid in context_ids:
                    continue
                child = nodes.get(cid)
                if child:
                    try:
                        node.add_child(child, relation="solved")
                    except ValueError as exc:
                        logger.debug(
                            "Skipping invalid legacy solved link %s -> %s: %s",
                            node.unique_id,
                            cid,
                            exc,
                        )
            for cid in context_ids:
                child = nodes.get(cid)
                if child:
                    try:
                        node.add_child(child, relation="context")
                    except ValueError as exc:
                        logger.debug(
                            "Skipping invalid legacy context link %s -> %s: %s",
                            node.unique_id,
                            cid,
                            exc,
                        )
            orig_id = getattr(node, "_tmp_original", None)
            if orig_id and orig_id in nodes:
                node.original = nodes[orig_id]
            # cleanup temporary attributes
            if hasattr(node, "_tmp_children"):
                delattr(node, "_tmp_children")
            if hasattr(node, "_tmp_context"):
                delattr(node, "_tmp_context")
            if hasattr(node, "_tmp_original"):
                delattr(node, "_tmp_original")
