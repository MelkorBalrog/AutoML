# Author: Miguel Marina <karel.capek.robotics@gmail.com>
import json
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple
import os
import datetime
import analysis.user_config as user_config

GLOBAL_PHASE = "GLOBAL"


def _diagram_type_abbreviation(diag_type: str | None) -> str:
    """Return an upper-case abbreviation for *diag_type*.

    The abbreviation is constructed from the first letter of each word in the
    diagram type. For example ``"Internal Block Diagram"`` becomes ``"IBD"``.
    """
    return "" if not diag_type else "".join(word[0] for word in diag_type.split()).upper()

@dataclass
class SysMLElement:
    """Basic AutoML element stored in the repository."""
    elem_id: str
    elem_type: str
    name: str = ""
    properties: Dict[str, str] = field(default_factory=dict)
    stereotypes: Dict[str, str] = field(default_factory=dict)
    owner: Optional[str] = None
    created: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    author: str = field(default_factory=lambda: user_config.CURRENT_USER_NAME)
    author_email: str = field(default_factory=lambda: user_config.CURRENT_USER_EMAIL)
    modified: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    modified_by: str = field(default_factory=lambda: user_config.CURRENT_USER_NAME)
    modified_by_email: str = field(default_factory=lambda: user_config.CURRENT_USER_EMAIL)
    phase: Optional[str] = None

    # ------------------------------------------------------------
    def display_name(self) -> str:
        """Return element name annotated with its creation phase."""
        return f"{self.name} ({self.phase})" if self.phase else self.name

@dataclass
class SysMLRelationship:
    rel_id: str
    rel_type: str
    source: str
    target: str
    stereotype: Optional[str] = None
    properties: Dict[str, str] = field(default_factory=dict)
    created: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    author: str = field(default_factory=lambda: user_config.CURRENT_USER_NAME)
    author_email: str = field(default_factory=lambda: user_config.CURRENT_USER_EMAIL)
    modified: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    modified_by: str = field(default_factory=lambda: user_config.CURRENT_USER_NAME)
    modified_by_email: str = field(default_factory=lambda: user_config.CURRENT_USER_EMAIL)
    phase: Optional[str] = None

@dataclass
class SysMLDiagram:
    diag_id: str
    diag_type: str
    name: str = ""
    package: Optional[str] = None
    description: str = ""
    color: str = "#FFFFFF"
    father: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    elements: List[str] = field(default_factory=list)
    relationships: List[str] = field(default_factory=list)
    objects: List[dict] = field(default_factory=list)
    connections: List[dict] = field(default_factory=list)
    created: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    author: str = field(default_factory=lambda: user_config.CURRENT_USER_NAME)
    author_email: str = field(default_factory=lambda: user_config.CURRENT_USER_EMAIL)
    modified: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    modified_by: str = field(default_factory=lambda: user_config.CURRENT_USER_NAME)
    modified_by_email: str = field(default_factory=lambda: user_config.CURRENT_USER_EMAIL)
    phase: Optional[str] = None
    locked: bool = False

    # ------------------------------------------------------------
    def display_name(self) -> str:
        """Return diagram name annotated with its type and creation phase."""
        name = self.name or self.diag_id
        abbr = _diagram_type_abbreviation(self.diag_type)
        if abbr and not name.endswith(f" : {abbr}"):
            name = f"{name} : {abbr}"
        return f"{name} ({self.phase})" if self.phase else name

class SysMLRepository:
    """Singleton repository for all AutoML elements and relationships."""
    _instance = None

    def __init__(self):
        self.elements: Dict[str, SysMLElement] = {}
        self.relationships: List[SysMLRelationship] = []
        self.diagrams: Dict[str, SysMLDiagram] = {}
        # map element_id -> diagram_id for implementation links
        self.element_diagrams: Dict[str, str] = {}
        # maintain undo and redo history of repository snapshots
        self._undo_stack: list[dict] = []
        self._redo_stack: list[dict] = []
        self.active_phase: Optional[str] = None
        # Phases reused by the currently active lifecycle phase. Elements or
        # diagrams belonging to any of these phases should remain visible even
        # though they were not created in ``active_phase``.
        self.reuse_phases: set[str] = set()
        # Work product types reused by the active phase. Any diagrams of these
        # types originating from other phases are visible but read-only.
        self.reuse_products: set[str] = set()
        # Diagrams made immutable after phase freeze
        self.frozen_diagrams: set[str] = set()
        self.root_package = self.create_element("Package", name="Root")

    def touch_element(self, elem_id: str) -> None:
        elem = self.elements.get(elem_id)
        if elem:
            elem.modified = datetime.datetime.now().isoformat()
            elem.modified_by = user_config.CURRENT_USER_NAME
            elem.modified_by_email = user_config.CURRENT_USER_EMAIL

    def touch_diagram(self, diag_id: str) -> None:
        diag = self.diagrams.get(diag_id)
        if diag:
            diag.modified = datetime.datetime.now().isoformat()
            diag.modified_by = user_config.CURRENT_USER_NAME
            diag.modified_by_email = user_config.CURRENT_USER_EMAIL

    def touch_relationship(self, rel_id: str) -> None:
        rel = next((r for r in self.relationships if r.rel_id == rel_id), None)
        if rel:
            rel.modified = datetime.datetime.now().isoformat()
            rel.modified_by = user_config.CURRENT_USER_NAME
            rel.modified_by_email = user_config.CURRENT_USER_EMAIL

    @classmethod
    def get_instance(cls) -> "SysMLRepository":
        if cls._instance is None:
            cls._instance = SysMLRepository()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> "SysMLRepository":
        """Return a fresh repository instance, clearing all current data."""
        cls._instance = SysMLRepository()
        return cls._instance

    # ------------------------------------------------------------
    # Undo support
    # ------------------------------------------------------------
    def _strip_object_positions(self, data: dict) -> dict:
        """Return a copy of *data* without concrete object positions.

        The helper is used to determine whether two repository states differ
        only by object coordinates within diagrams.  When this is the case we
        can merge the states to keep the undo history compact.
        """

        cleaned = json.loads(json.dumps(data))

        def scrub(obj: Any) -> None:
            if isinstance(obj, dict):
                for field in ("x", "y", "modified", "modified_by", "modified_by_email"):
                    obj.pop(field, None)
                for value in obj.values():
                    scrub(value)
            elif isinstance(obj, list):
                for item in obj:
                    scrub(item)

        scrub(cleaned)
        return cleaned

    def push_undo_state(self, strategy: str = "v4", sync_app: bool = True) -> None:
        """Save the current repository state for undo.

        Repeated calls that do not change the repository would otherwise
        accumulate duplicate snapshots.  This became especially noticeable
        when dragging objects on a diagram: both the mouse press and the
        subsequent synchronization wrote the same state to the undo stack,
        requiring multiple ``undo`` operations to revert a single move.
        Skipping storage of consecutive identical states keeps the history
        concise and ensures that each user action corresponds to a single
        undo step.
        """

        state = self.to_dict()
        stripped = self._strip_object_positions(state)

        handler = getattr(
            self, f"_push_undo_state_{strategy}", self._push_undo_state_v1
        )
        changed = handler(state, stripped)

        if changed:
            if len(self._undo_stack) > 50:
                self._undo_stack.pop(0)
            self._redo_stack.clear()
            if sync_app:
                try:
                    from AutoML import AutoMLApp

                    app = getattr(AutoMLApp, "_instance", None)
                    if app:
                        app.push_undo_state(strategy=strategy, sync_repo=False)
                except Exception:
                    pass

    # ------------------------------------------------------------
    # Variants for push_undo_state
    # ------------------------------------------------------------
    def _push_undo_state_v1(self, state: dict, stripped: dict) -> bool:
        if self._undo_stack:
            last = self._undo_stack[-1]
            if last == state:
                return False
            if self._strip_object_positions(last) == stripped:
                if (
                    len(self._undo_stack) >= 2
                    and self._strip_object_positions(self._undo_stack[-2]) == stripped
                ):
                    self._undo_stack[-1] = state
                    return True
                self._undo_stack.append(state)
                return True
        else:
            self._undo_stack.append(state)
            return True

        self._undo_stack.append(state)
        return True

    def _push_undo_state_v2(self, state: dict, stripped: dict) -> bool:
        if self._undo_stack and self._undo_stack[-1] == state:
            return False
        if self._undo_stack and self._strip_object_positions(self._undo_stack[-1]) == stripped:
            if self._last_move_base == stripped:
                self._undo_stack[-1] = state
            else:
                self._undo_stack.append(state)
                self._last_move_base = stripped
            return True
        self._last_move_base = None
        self._undo_stack.append(state)
        return True

    def _push_undo_state_v3(self, state: dict, stripped: dict) -> bool:
        if self._undo_stack and self._undo_stack[-1] == state:
            return False
        self._undo_stack.append(state)
        if len(self._undo_stack) >= 3:
            s1 = self._strip_object_positions(self._undo_stack[-3])
            s2 = self._strip_object_positions(self._undo_stack[-2])
            if s1 == s2 == stripped:
                self._undo_stack.pop(-2)
        if len(self._undo_stack) > 50:
            self._undo_stack.pop(0)
        self._redo_stack.clear()
        return True

    def _push_undo_state_v4(self, state: dict, stripped: dict) -> bool:
        if self._undo_stack and self._undo_stack[-1] == state:
            return False
        self._undo_stack.append(state)
        if len(self._undo_stack) >= 3:
            s1 = self._strip_object_positions(self._undo_stack[-3])
            s2 = self._strip_object_positions(self._undo_stack[-2])
            if s1 == s2 == stripped:
                self._undo_stack.pop(-2)
        return True

    def undo(self, strategy: str = "v4") -> bool:
        """Revert to the most recent saved state."""
        if strategy == "v1":
            return self._undo_v1()
        elif strategy == "v2":
            return self._undo_v2()
        elif strategy == "v3":
            return self._undo_v3()
        else:
            return self._undo_v4()

    def redo(self, strategy: str = "v4") -> bool:
        """Restore the next state from the redo stack."""
        if strategy == "v1":
            return self._redo_v1()
        elif strategy == "v2":
            return self._redo_v2()
        elif strategy == "v3":
            return self._redo_v3()
        else:
            return self._redo_v4()

    # Undo/redo variants
    def _undo_v1(self) -> bool:
        if not self._undo_stack:
            return False
        current = self.to_dict()
        if self._undo_stack and self._undo_stack[-1] == current:
            self._undo_stack.pop()
            if not self._undo_stack:
                return False
        state = self._undo_stack.pop()
        self._redo_stack.append(current)
        if len(self._redo_stack) > 50:
            self._redo_stack.pop(0)
        self.from_dict(state)
        return True

    def _undo_v2(self) -> bool:
        if not self._undo_stack:
            return False
        current = self.to_dict()
        if self._undo_stack and self._undo_stack[-1] == current:
            self._undo_stack.pop()
            if not self._undo_stack:
                return False
        state = self._undo_stack.pop()
        self._redo_stack.append(current)
        if len(self._redo_stack) > 50:
            self._redo_stack.pop(0)
        self.from_dict(state)
        return True

    def undo(self, strategy: str = "v4") -> bool:
        """Revert to the most recent saved state."""
        handler = getattr(self, f"_undo_{strategy}", self._undo_v1)
        return handler()

    def redo(self, strategy: str = "v4") -> bool:
        """Restore the next state from the redo stack."""
        handler = getattr(self, f"_redo_{strategy}", self._redo_v1)
        return handler()

    # Undo/redo variants
    def _undo_v1(self) -> bool:
        if not self._undo_stack:
            return False
        current = self.to_dict()
        if self._undo_stack and self._undo_stack[-1] == current:
            self._undo_stack.pop()
            if not self._undo_stack:
                return False
        state = self._undo_stack.pop()
        self._redo_stack.append(current)
        if len(self._redo_stack) > 50:
            self._redo_stack.pop(0)
        self.from_dict(state)
        return True

    def _undo_v2(self) -> bool:
        if not self._undo_stack:
            return False
        current = self.to_dict()
        if self._undo_stack and self._undo_stack[-1] == current:
            self._undo_stack.pop()
            if not self._undo_stack:
                return False
        state = self._undo_stack.pop()
        self._redo_stack.append(current)
        if len(self._redo_stack) > 50:
            self._redo_stack.pop(0)
        self.from_dict(state)
        return True

    def _undo_v3(self) -> bool:
        if not self._undo_stack:
            return False
        current = self.to_dict()
        if self._undo_stack and self._undo_stack[-1] == current:
            self._undo_stack.pop()
            if not self._undo_stack:
                return False
        state = self._undo_stack.pop()
        self._redo_stack.append(current)
        if len(self._redo_stack) > 50:
            self._redo_stack.pop(0)
        self.from_dict(state)
        return True

    def _undo_v4(self) -> bool:
        if not self._undo_stack:
            return False
        current = self.to_dict()
        if self._undo_stack and self._undo_stack[-1] == current:
            self._undo_stack.pop()
            if not self._undo_stack:
                return False
        state = self._undo_stack.pop()
        self._redo_stack.append(current)
        if len(self._redo_stack) > 50:
            self._redo_stack.pop(0)
        self.from_dict(state)
        return True

    def _redo_v1(self) -> bool:
        if not self._redo_stack:
            return False
        current = self.to_dict()
        state = self._redo_stack.pop()
        self._undo_stack.append(current)
        if len(self._undo_stack) > 50:
            self._undo_stack.pop(0)
        self.from_dict(state)
        return True

    def _redo_v2(self) -> bool:
        if not self._redo_stack:
            return False
        current = self.to_dict()
        state = self._redo_stack.pop()
        self._undo_stack.append(current)
        if len(self._undo_stack) > 50:
            self._undo_stack.pop(0)
        self.from_dict(state)
        return True

    def _redo_v3(self) -> bool:
        if not self._redo_stack:
            return False
        current = self.to_dict()
        state = self._redo_stack.pop()
        self._undo_stack.append(current)
        if len(self._undo_stack) > 50:
            self._undo_stack.pop(0)
        self.from_dict(state)
        return True

    def _redo_v4(self) -> bool:
        if not self._redo_stack:
            return False
        current = self.to_dict()
        state = self._redo_stack.pop()
        self._undo_stack.append(current)
        if len(self._undo_stack) > 50:
            self._undo_stack.pop(0)
        self.from_dict(state)
        return True

    def ensure_unique_element_name(self, name: str, self_elem_id: str | None = None) -> str:
        """Return a unique element name based on *name* across all elements."""
        if not name:
            return name
        existing = {
            e.name
            for eid, e in self.elements.items()
            if eid != self_elem_id and e.name
        }
        base = name
        suffix = 1
        while name in existing:
            name = f"{base}_{suffix}"
            suffix += 1
        return name

    def _default_name(self, elem_type: str) -> str:
        """Return a generated default name for ``elem_type``."""
        base = elem_type.replace(" ", "") or "Element"
        existing = {
            e.name
            for e in self.elements.values()
            if e.name and e.name.startswith(base)
        }
        suffix = 1
        name = f"{base}{suffix}"
        while name in existing:
            suffix += 1
            name = f"{base}{suffix}"
        return name

    def create_element(self, elem_type: str, name: str = "", properties: Optional[Dict[str, str]] = None, owner: Optional[str] = None) -> SysMLElement:
        self.push_undo_state()
        elem_id = str(uuid.uuid4())
        if not name:
            name = self._default_name(elem_type)
        unique_name = self.ensure_unique_element_name(name)
        elem = SysMLElement(
            elem_id,
            elem_type,
            unique_name,
            properties or {},
            owner=owner,
            author=user_config.CURRENT_USER_NAME,
            author_email=user_config.CURRENT_USER_EMAIL,
            modified_by=user_config.CURRENT_USER_NAME,
            modified_by_email=user_config.CURRENT_USER_EMAIL,
            phase=None if self.active_phase == GLOBAL_PHASE else self.active_phase,
        )
        self.elements[elem_id] = elem
        try:
            from analysis import safety_management as sm
            toolbox = getattr(sm, "ACTIVE_TOOLBOX", None)
            if toolbox and getattr(toolbox, "work_products", []):
                toolbox.freeze_active_phase()
        except Exception:
            pass
        return elem

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------
    def create_package(self, name: str, parent: Optional[str] = None) -> SysMLElement:
        """Create a Package element optionally under a parent Package."""
        if parent is None:
            parent = self.root_package.elem_id
        return self.create_element("Package", name=name, owner=parent)

    def create_diagram(
        self,
        diag_type: str,
        name: str = "",
        diag_id: Optional[str] = None,
        package: Optional[str] = None,
        description: str = "",
        color: str = "#FFFFFF",
        father: Optional[str] = None,
    ) -> SysMLDiagram:
        self.push_undo_state()
        if diag_id is None:
            diag_id = str(uuid.uuid4())
        if package is None:
            package = self.root_package.elem_id
        if name:
            same_name_diagrams = [
                d
                for d in self.diagrams.values()
                if d.name == name
                or d.name.startswith(f"{name} ")
                or d.name.startswith(f"{name}_")
            ]
            if same_name_diagrams:
                if any(d.diag_type != diag_type for d in same_name_diagrams):
                    for d in same_name_diagrams:
                        existing_names = {
                            dd.name for dd in self.diagrams.values() if dd.diag_id != d.diag_id
                        }
                        base_existing = f"{name} {d.diag_type}"
                        new_existing = base_existing
                        suffix = 1
                        while new_existing in existing_names:
                            new_existing = f"{base_existing}_{suffix}"
                            suffix += 1
                        d.name = new_existing
                    name = f"{name} {diag_type}"
                else:
                    existing = {
                        d.name
                        for d in self.diagrams.values()
                        if d.diag_type == diag_type and d.name
                    }
                    base = name
                    suffix = 1
                    while name in existing or any(
                        n.startswith(f"{name} ") or n.startswith(f"{name}_") for n in existing
                    ):
                        name = f"{base}_{suffix}"
                        suffix += 1
            existing_all = {d.name for d in self.diagrams.values()}
            base = name
            suffix = 1
            while name in existing_all or any(
                n.startswith(f"{name} ") or n.startswith(f"{name}_") for n in existing_all
            ):
                name = f"{base}_{suffix}"
                suffix += 1
        diagram = SysMLDiagram(
            diag_id,
            diag_type,
            name,
            package,
            description,
            color,
            father,
            author=user_config.CURRENT_USER_NAME,
            author_email=user_config.CURRENT_USER_EMAIL,
            modified_by=user_config.CURRENT_USER_NAME,
            modified_by_email=user_config.CURRENT_USER_EMAIL,
            phase=None if self.active_phase == GLOBAL_PHASE else self.active_phase,
        )
        self.diagrams[diag_id] = diagram
        try:
            from analysis import safety_management as sm
            toolbox = getattr(sm, "ACTIVE_TOOLBOX", None)
            if toolbox and getattr(toolbox, "work_products", []):
                toolbox.freeze_active_phase()
        except Exception:
            pass
        return diagram

    def add_element_to_diagram(self, diag_id: str, elem_id: str) -> None:
        diag = self.diagrams.get(diag_id)
        if diag and elem_id not in diag.elements:
            if self.diagram_read_only(diag_id):
                return
            try:
                from analysis import safety_management as sm

                toolbox = getattr(sm, "ACTIVE_TOOLBOX", None)
            except Exception:  # pragma: no cover - optional toolbox
                toolbox = None
            if toolbox:
                src_id = self.element_diagrams.get(elem_id)
                src = self.diagrams.get(src_id) if src_id else None
                if src:
                    allowed = toolbox.analysis_inputs(
                        diag.diag_type, reviewed=True, approved=True
                    )
                    if src.diag_type not in allowed:
                        return
            self.push_undo_state()
            diag.elements.append(elem_id)

    def add_relationship_to_diagram(self, diag_id: str, rel_id: str) -> None:
        diag = self.diagrams.get(diag_id)
        if diag and rel_id not in diag.relationships:
            if self.diagram_read_only(diag_id):
                return
            self.push_undo_state()
            diag.relationships.append(rel_id)

    def delete_element(self, elem_id: str) -> None:
        """Remove an element and any relationships referencing it."""
        if self.element_read_only(elem_id):
            return
        self.push_undo_state()
        if elem_id in self.elements:
            del self.elements[elem_id]
        self.relationships = [r for r in self.relationships if r.source != elem_id and r.target != elem_id]

    def delete_package(self, pkg_id: str) -> None:
        """Delete a package and reassign its contents to the parent package."""
        pkg = self.elements.get(pkg_id)
        if not pkg or pkg.elem_type != "Package" or pkg_id == self.root_package.elem_id:
            return
        self.push_undo_state()
        parent = pkg.owner or self.root_package.elem_id
        for elem in self.elements.values():
            if elem.owner == pkg_id:
                elem.owner = parent
        for diag in self.diagrams.values():
            if diag.package == pkg_id:
                diag.package = parent
        self.delete_element(pkg_id)

    def delete_diagram(self, diag_id: str) -> None:
        if self.diagram_read_only(diag_id):
            return
        self.push_undo_state()
        if diag_id in self.diagrams:
            del self.diagrams[diag_id]
        # remove any element links to this diagram
        for k, v in list(self.element_diagrams.items()):
            if v == diag_id:
                del self.element_diagrams[k]

    def rename_phase(self, old: str, new: str) -> None:
        """Replace references to lifecycle phase ``old`` with ``new``.

        Elements, relationships, diagrams and their contained objects or
        connections referencing ``old`` will be updated. The active phase is
        also adjusted when it matches ``old``.
        """

        if not old or not new or old == new:
            return

        for elem in self.elements.values():
            if elem.phase == old:
                elem.phase = new

        for rel in self.relationships:
            if rel.phase == old:
                rel.phase = new

        for diag in self.diagrams.values():
            if diag.phase == old:
                diag.phase = new
            for obj in getattr(diag, "objects", []):
                if obj.get("phase") == old:
                    obj["phase"] = new
            for conn in getattr(diag, "connections", []):
                if conn.get("phase") == old:
                    conn["phase"] = new

        if self.active_phase == old:
            self.active_phase = new

    def get_element(self, elem_id: str) -> Optional[SysMLElement]:
        return self.elements.get(elem_id)

    def get_qualified_name(self, elem_id: str) -> str:
        elem = self.elements[elem_id]
        parts = [elem.name or elem.elem_id]
        current = elem.owner
        while current:
            parent = self.elements[current]
            parts.append(parent.name or parent.elem_id)
            current = parent.owner
        return "::".join(reversed(parts))

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.serialize())

    def load(self, path: str) -> None:
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.elements.clear()
        self.relationships.clear()
        self.diagrams.clear()
        for e in data.get("elements", []):
            elem = SysMLElement(**e)
            self.elements[elem.elem_id] = elem
        for r in data.get("relationships", []):
            rel = SysMLRelationship(**r)
            self.relationships.append(rel)
        for d in data.get("diagrams", []):
            diag = SysMLDiagram(**d)
            self.diagrams[diag.diag_id] = diag
        self.element_diagrams = data.get("element_diagrams", {})
        self.root_package = None
        for elem in self.elements.values():
            if elem.elem_type == "Package" and elem.owner is None:
                self.root_package = elem
                break
        if self.root_package is None:
            self.root_package = self.create_element("Package", name="Root")

    def create_relationship(
        self,
        rel_type: str,
        source: str,
        target: str,
        stereotype: Optional[str] = None,
        properties: Optional[Dict[str, str]] = None,
        record_undo: bool = True,
    ) -> SysMLRelationship:
        if record_undo:
            self.push_undo_state()
        rel_id = str(uuid.uuid4())
        rel = SysMLRelationship(
            rel_id,
            rel_type,
            source,
            target,
            stereotype or rel_type.lower(),
            properties or {},
            author=user_config.CURRENT_USER_NAME,
            author_email=user_config.CURRENT_USER_EMAIL,
            modified_by=user_config.CURRENT_USER_NAME,
            modified_by_email=user_config.CURRENT_USER_EMAIL,
            phase=None if self.active_phase == GLOBAL_PHASE else self.active_phase,
        )
        self.relationships.append(rel)
        return rel

    # ------------------------------------------------------------
    # Phase visibility helpers
    # ------------------------------------------------------------
    def element_visible(self, elem_id: str) -> bool:
        """Return True if ``elem_id`` should be visible in the active phase."""
        elem = self.elements.get(elem_id)
        if not elem:
            return False
        if self.active_phase is None:
            return True
        if self.active_phase == GLOBAL_PHASE:
            return elem.phase is None
        if elem.phase is None:
            return False
        if elem.phase == self.active_phase or elem.phase in getattr(self, "reuse_phases", set()):
            return True
        diag_id = self.element_diagrams.get(elem_id)
        if diag_id:
            diag = self.diagrams.get(diag_id)
            if diag and diag.diag_type in getattr(self, "reuse_products", set()):
                return True
        return False

    def diagram_visible(self, diag_id: str) -> bool:
        """Return True if ``diag_id`` should be visible in the active phase."""
        diag = self.diagrams.get(diag_id)
        if not diag:
            return False
        if "safety-management" in getattr(diag, "tags", []):
            return True
        if self.active_phase is None:
            return True
        if self.active_phase == GLOBAL_PHASE:
            return diag.phase is None
        if diag.diag_type == "Governance Diagram" and diag.phase is None:
            return True
        if diag.phase is None:
            return False
        if diag.phase == self.active_phase or diag.phase in getattr(self, "reuse_phases", set()):
            return True
        return diag.diag_type in getattr(self, "reuse_products", set())

    def element_read_only(self, elem_id: str) -> bool:
        """Return ``True`` if ``elem_id`` originates from a reused phase or work product."""
        elem = self.elements.get(elem_id)
        if not elem:
            return False
        if self.active_phase is None or elem.phase is None:
            return False
        if elem.phase != self.active_phase and elem.phase in getattr(self, "reuse_phases", set()):
            return True
        diag_id = self.element_diagrams.get(elem_id)
        if diag_id:
            diag = self.diagrams.get(diag_id)
            if diag and diag.diag_type in getattr(self, "reuse_products", set()) and diag.phase != self.active_phase:
                return True
        return False

    def diagram_read_only(self, diag_id: str) -> bool:
        """Return ``True`` if ``diag_id`` is locked or originates from a reused phase/work product."""
        diag = self.diagrams.get(diag_id)
        if not diag:
            return False
        if getattr(diag, "locked", False):
            return True
        if self.active_phase is None or diag.phase is None:
            return False
        if diag.phase != self.active_phase and diag.phase in getattr(self, "reuse_phases", set()):
            return True
        return diag.phase != self.active_phase and diag.diag_type in getattr(self, "reuse_products", set())

    # ------------------------------------------------------------
    def freeze_diagram(self, diag_id: str) -> None:
        """Mark a diagram as immutable."""
        self.frozen_diagrams.add(diag_id)
        diag = self.diagrams.get(diag_id)
        if diag:
            diag.locked = True

    # ------------------------------------------------------------
    def unfreeze_diagram(self, diag_id: str) -> None:
        """Allow modifications to a previously frozen diagram."""
        self.frozen_diagrams.discard(diag_id)
        diag = self.diagrams.get(diag_id)
        if diag:
            diag.locked = False

    # ------------------------------------------------------------
    def rename_phase(self, old: str, new: str) -> None:
        """Rename lifecycle phase ``old`` to ``new`` across repository data."""
        if old == new:
            return
        if self.active_phase == old:
            self.active_phase = new
        if old in self.reuse_phases:
            self.reuse_phases.remove(old)
            self.reuse_phases.add(new)
        for elem in self.elements.values():
            if elem.phase == old:
                elem.phase = new
        for rel in self.relationships:
            if rel.phase == old:
                rel.phase = new
        for diag in self.diagrams.values():
            if diag.phase == old:
                diag.phase = new
            for obj in diag.objects:
                if obj.get("phase") == old:
                    obj["phase"] = new
            for conn in diag.connections:
                if conn.get("phase") == old:
                    conn["phase"] = new

    def element_read_only(self, elem_id: str) -> bool:
        """Return ``True`` if ``elem_id`` originates from a reused phase or work product."""
        elem = self.elements.get(elem_id)
        if not elem:
            return False
        if self.active_phase is None or elem.phase is None:
            return False
        if elem.phase != self.active_phase and elem.phase in getattr(self, "reuse_phases", set()):
            return True
        linked = self.get_linked_diagram(elem_id)
        if linked:
            diag = self.diagrams.get(linked)
            if diag and diag.diag_type in getattr(self, "reuse_products", set()):
                return True
        return False

    def visible_elements(self) -> dict[str, SysMLElement]:
        """Return mapping of element IDs to elements visible in the active phase."""
        return {eid: e for eid, e in self.elements.items() if self.element_visible(eid)}

    def visible_diagrams(self) -> dict[str, SysMLDiagram]:
        """Return mapping of diagram IDs to diagrams visible in the active phase."""
        return {did: d for did, d in self.diagrams.items() if self.diagram_visible(did)}

    def object_visible(self, obj: dict, diag_id: Optional[str] = None) -> bool:
        """Return True if a diagram object should be visible in the active phase."""
        diag = self.diagrams.get(diag_id) if diag_id else None
        if diag and ("safety-management" in getattr(diag, "tags", []) or diag.diag_type in getattr(self, "reuse_products", set())):
            return True
        if self.active_phase is None:
            return True
        if self.active_phase == GLOBAL_PHASE:
            return obj.get("phase") is None
        if diag and diag.diag_type == "Governance Diagram" and obj.get("phase") is None:
            return True
        if obj.get("phase") is None:
            return False
        return obj.get("phase") == self.active_phase or obj.get("phase") in getattr(self, "reuse_phases", set())

    def connection_visible(self, conn: dict, diag_id: Optional[str] = None) -> bool:
        """Return True if a diagram connection should be visible in the active phase."""
        diag = self.diagrams.get(diag_id) if diag_id else None
        if diag and ("safety-management" in getattr(diag, "tags", []) or diag.diag_type in getattr(self, "reuse_products", set())):
            return True
        if self.active_phase is None:
            return True
        if self.active_phase == GLOBAL_PHASE:
            return conn.get("phase") is None
        if diag and diag.diag_type == "Governance Diagram" and conn.get("phase") is None:
            return True
        if conn.get("phase") is None:
            return False
        return conn.get("phase") == self.active_phase or conn.get("phase") in getattr(self, "reuse_phases", set())

    def visible_objects(self, diag_id: str) -> list[dict]:
        """Return list of objects in diagram ``diag_id`` visible in the active phase."""
        diag = self.diagrams.get(diag_id)
        if not diag:
            return []
        return [o for o in getattr(diag, "objects", []) if self.object_visible(o, diag_id)]

    def visible_connections(self, diag_id: str) -> list[dict]:
        """Return list of connections in diagram ``diag_id`` visible in the active phase."""
        diag = self.diagrams.get(diag_id)
        if not diag:
            return []
        return [c for c in getattr(diag, "connections", []) if self.connection_visible(c, diag_id)]

    # ------------------------------------------------------------
    # Diagram linkage helpers
    # ------------------------------------------------------------
    def link_diagram(self, elem_id: str, diag_id: Optional[str], record_undo: bool = True) -> None:
        """Associate an element with a diagram implementing it."""
        if record_undo:
            self.push_undo_state()
        if diag_id:
            self.element_diagrams[elem_id] = diag_id
        else:
            self.element_diagrams.pop(elem_id, None)

    def get_linked_diagram(self, elem_id: str) -> Optional[str]:
        return self.element_diagrams.get(elem_id)

    def serialize(self) -> str:
        data = {
            "elements": [asdict(elem) for elem in self.elements.values()],
            "relationships": [asdict(rel) for rel in self.relationships],
            "diagrams": [asdict(diag) for diag in self.diagrams.values()],
            "element_diagrams": self.element_diagrams,
        }
        return json.dumps(data, indent=2)

    def to_dict(self) -> dict:
        """Return a dictionary representation of the repository."""
        return json.loads(self.serialize())

    def from_dict(self, data: dict) -> None:
        """Load repository contents from a dictionary."""
        self.elements.clear()
        self.relationships.clear()
        self.diagrams.clear()
        for e in data.get("elements", []):
            elem = SysMLElement(**e)
            self.elements[elem.elem_id] = elem
        for r in data.get("relationships", []):
            rel = SysMLRelationship(**r)
            self.relationships.append(rel)
        for d in data.get("diagrams", []):
            diag = SysMLDiagram(**d)
            self.diagrams[diag.diag_id] = diag
        self.element_diagrams = data.get("element_diagrams", {})
        self.root_package = None
        for elem in self.elements.values():
            if elem.elem_type == "Package" and elem.owner is None:
                self.root_package = elem
                break
        if self.root_package is None:
            self.root_package = self.create_element("Package", name="Root")

        self._resolve_part_definition_ids()

    def _resolve_part_definition_ids(self) -> None:
        """Ensure part definitions reference block IDs instead of names."""
        name_map = {
            e.name: e.elem_id
            for e in self.elements.values()
            if e.elem_type == "Block" and e.name
        }
        for elem in self.elements.values():
            if elem.elem_type != "Part":
                continue
            def_val = elem.properties.get("definition")
            if def_val and def_val not in self.elements:
                mapped = name_map.get(def_val)
                if mapped:
                    elem.properties["definition"] = mapped
        for diag in self.diagrams.values():
            for obj in getattr(diag, "objects", []):
                if obj.get("obj_type") != "Part":
                    continue
                def_val = obj.get("properties", {}).get("definition")
                if def_val and def_val not in self.elements:
                    mapped = name_map.get(def_val)
                    if mapped:
                        obj.setdefault("properties", {})["definition"] = mapped

    def find_requirements(self, req_id: str) -> List[Tuple[str, int]]:
        """Return list of (diagram_id, obj_id) where ``req_id`` is allocated."""
        matches: List[Tuple[str, int]] = []
        for diag_id, diag in self.diagrams.items():
            for obj in getattr(diag, "objects", []):
                for req in obj.get("requirements", []):
                    rid = req.get("id") if isinstance(req, dict) else req
                    if rid == req_id:
                        matches.append((diag_id, obj.get("obj_id")))
                        break
        return matches

    def get_activity_actions(self) -> list[str]:
        """Return all action names and activity diagram names."""
        names = []
        for diag in self.diagrams.values():
            if diag.diag_type != "Activity Diagram":
                continue
            if diag.name:
                names.append(diag.name)
            for obj in diag.objects:
                typ = obj.get("obj_type") or obj.get("type")
                if typ in ("Action Usage", "Action", "CallBehaviorAction"):
                    name = obj.get("properties", {}).get("name", "")
                    elem_id = obj.get("element_id")
                    if not name and elem_id in self.elements:
                        name = self.elements[elem_id].name
                    if name:
                        names.append(name)
            for elem_id in getattr(diag, "elements", []):
                elem = self.elements.get(elem_id)
                if elem and elem.elem_type in ("Action Usage", "Action", "CallBehaviorAction"):
                    if elem.name:
                        names.append(elem.name)
        return sorted(set(n for n in names if n))

    # ------------------------------------------------------------
    def generate_requirements(
        self, diag_id: str, _visited: set[str] | None = None
    ) -> list[tuple[str, str]]:
        """Generate simple requirements from SysML diagrams.

        Parameters
        ----------
        diag_id:
            Identifier of the diagram to process.
        _visited:
            Internal set used to avoid infinite recursion when activity
            diagrams reference each other via ``CallBehaviorAction`` objects.

        Returns
        -------
        list[tuple[str, str]]
            Generated requirement texts paired with their types.  Activity
            diagrams yield "vehicle" requirements describing the predecessor
            relationship between connected actions.  For other SysML diagrams a
            generic "functional" requirement expressing that two elements are
            connected is produced.
        """

        if _visited is None:
            _visited = set()
        if diag_id in _visited:
            return []
        _visited.add(diag_id)

        diag = self.diagrams.get(diag_id)
        if not diag:
            return []

        reqs: list[tuple[str, str]] = []

        # Map object ids to human readable names for requirement text.
        id_to_name: dict[int, str] = {}
        for obj in getattr(diag, "objects", []):
            obj_id = obj.get("obj_id")
            name = obj.get("properties", {}).get("name") or ""
            elem_id = obj.get("element_id")
            if not name and elem_id in self.elements:
                name = self.elements[elem_id].name
            if not name:
                name = str(obj_id)
            id_to_name[obj_id] = name

            # Recursively include requirements from called activities.
            if (
                diag.diag_type == "Activity Diagram"
                and obj.get("obj_type") == "CallBehaviorAction"
            ):
                beh_id = obj.get("properties", {}).get("behavior")
                if beh_id:
                    reqs.extend(self.generate_requirements(beh_id, _visited))

        for conn in getattr(diag, "connections", []):
            src = id_to_name.get(conn.get("src"))
            dst = id_to_name.get(conn.get("dst"))
            if not src or not dst:
                continue
            if diag.diag_type == "Activity Diagram":
                text = f"{src} shall precede {dst}."
                req_type = "vehicle"
            else:
                text = f"{src} shall be connected to {dst}."
                req_type = "functional"
            reqs.append((text, req_type))

        return reqs

