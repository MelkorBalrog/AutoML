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

"""Safety & Security management data structures.

This module defines simple data classes used by the GUI and other modules to
collect work products, lifecycle information and workflows related to safety
governance."""

"""Helpers for managing safety governance information.

This module originally provided a thin container for safety governance
artifacts.  The user request requires the toolbox to control which work
products are available in the main application.  To support this the
toolbox now tracks which analysis types have been declared in governance
diagrams and how many actual documents of each type exist.  When a work
product type is removed from governance but there are existing documents
of that type, the removal is rejected to prevent orphaned analyses.

The toolbox also notifies listeners (typically the GUI) whenever the set
of enabled work products changes so menu items can be enabled/disabled.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Callable, Optional

from mainappsrc.models.sysml.sysml_repository import SysMLRepository
from .requirement_rule_generator import regenerate_requirement_patterns


GLOBAL_PHASE = "GLOBAL"
ACTIVE_TOOLBOX: Optional["SafetyManagementToolbox"] = None

# Relationships that allow propagation of results between work products. Each
# entry is a directed edge from source to target analysis name.
ALLOWED_PROPAGATIONS: set[tuple[str, str]] = {
    ("HAZOP", "Risk Assessment"),
    ("FI2TC", "Risk Assessment"),
    ("TC2FI", "Risk Assessment"),
    ("Threat Analysis", "Cyber Risk Assessment"),
    ("Cyber Risk Assessment", "Risk Assessment"),
    ("Risk Assessment", "FMEA"),
    ("Risk Assessment", "FMEDA"),
    ("Risk Assessment", "FTA"),
    ("Risk Assessment", "Prototype Assurance Analysis"),
    ("Risk Assessment", "Product Goal Specification"),
    ("FMEA", "FTA"),
    ("FMEDA", "FTA"),
    ("FMEA", "Prototype Assurance Analysis"),
    ("FMEDA", "Prototype Assurance Analysis"),
    ("FTA", "Product Goal Specification"),
    ("FTA", "CTA"),
    ("Prototype Assurance Analysis", "Product Goal Specification"),
}

# Valid "Used" relationships between safety analysis work products. These
# represent genuine dependencies in the metamodel that do not result in
# automatic result propagation.
ALLOWED_ANALYSIS_USAGE: set[tuple[str, str]] = {
    # Mission profile may feed many analyses, but it is handled separately
    # in connection validation so it is omitted here.
    ("Reliability Analysis", "FMEA"),
    ("Reliability Analysis", "FMEDA"),
    ("ODD", "Scenario Library"),
    ("Scenario Library", "HAZOP"),
    ("GSN Argumentation", "Safety & Security Case"),
}

# Work products that support governed inputs from other work products
SAFETY_ANALYSIS_WORK_PRODUCTS: set[str] = {
    "HAZOP",
    "HARA",
    "STPA",
    "Threat Analysis",
    "Cyber Risk Assessment",
    "FI2TC",
    "TC2FI",
    "Risk Assessment",
    "Mission Profile",
    "FMEA",
    "FMEDA",
    "FTA",
    "CTA",
    "Prototype Assurance Analysis",
    "Reliability Analysis",
    "Causal Bayesian Network Analysis",
    "Safety & Security Case",
    "GSN Argumentation",
    "Scenario Library",
    "ODD",
}

# Work products that may be used as inputs for any analysis without
# additional dependency checks
UNRESTRICTED_USAGE_SOURCES: set[str] = {"Architecture Diagram"}

# Explicit work product dependencies allowed for "Used" style relationships.
# Each tuple maps a source work product to a target analysis that genuinely
# depends on it.  Relationships outside this set are rejected to prevent
# meaningless connections between unrelated work products.
ALLOWED_USAGE: set[tuple[str, str]] = set(ALLOWED_PROPAGATIONS)
ALLOWED_USAGE.update(
    {
        ("Mission Profile", "Reliability Analysis"),
        ("Mission Profile", "FTA"),
        ("Mission Profile", "Prototype Assurance Analysis"),
        ("Requirement Specification", "HAZOP"),
        ("ODD", "Scenario Library"),
        ("Scenario Library", "HAZOP"),
        ("Reliability Analysis", "FMEA"),
        ("Reliability Analysis", "FMEDA"),
        ("GSN Argumentation", "Safety & Security Case"),
        ("STPA", "Architecture Diagram"),
    }
)

@dataclass
class SafetyWorkProduct:
    """Describe a work product generated from a diagram or analysis."""

    diagram: str
    analysis: str
    rationale: str = ""
    # Names of work products this item may trace to according to governance.
    traceable: List[str] = field(default_factory=list)
    # Analysis types this work product may serve as input for
    analyzable: List[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        """Return a serialisable representation of this work product."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "SafetyWorkProduct":
        """Create a work product from *data* mapping."""
        return cls(
            data.get("diagram", ""),
            data.get("analysis", ""),
            data.get("rationale", ""),
            list(data.get("traceable", [])),
            list(data.get("analyzable", [])),
        )


@dataclass
class LifecycleStage:
    """Represent a single stage in a safety lifecycle."""

    name: str


@dataclass
class Workflow:
    """Ordered list of steps for a named workflow."""

    name: str
    steps: List[str]


@dataclass
class GovernanceModule:
    """Container for organising governance diagrams into folders."""

    name: str
    modules: List["GovernanceModule"] = field(default_factory=list)
    diagrams: List[str] = field(default_factory=list)
    frozen: bool = False

    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        """Serialise this module including submodules."""
        return {
            "name": self.name,
            "modules": [m.to_dict() for m in self.modules],
            "diagrams": list(self.diagrams),
            "frozen": self.frozen,
        }

    # ------------------------------------------------------------------
    @classmethod
    def from_dict(cls, data: dict) -> "GovernanceModule":
        """Recreate a module hierarchy from *data*."""
        mod = cls(data.get("name", ""))
        mod.modules = [cls.from_dict(m) for m in data.get("modules", [])]
        mod.diagrams = list(data.get("diagrams", []))
        mod.frozen = data.get("frozen", False)
        return mod


@dataclass
class SafetyManagementToolbox:
    """Collect work products and governance artifacts for safety management.

    The toolbox lets users register work products from various diagrams and
    analyses with an associated rationale. It also stores lifecycle stages and
    named workflows so projects can describe their safety governance.
    """

    work_products: List[SafetyWorkProduct] = field(default_factory=list)
    lifecycle: List[str] = field(default_factory=list)
    workflows: Dict[str, List[str]] = field(default_factory=dict)
    diagrams: Dict[str, str] = field(default_factory=dict)
    modules: List[GovernanceModule] = field(default_factory=list)
    active_module: Optional[str] = None
    # Track how many documents of each analysis type exist.  This allows the
    # toolbox to prevent removal of work product declarations when documents
    # are present.
    work_product_counts: Dict[str, int] = field(default_factory=dict)
    # Map analysis names to document names and their creating module so work
    # products can be filtered by lifecycle phase. Documents without an entry
    # are visible in all phases for backwards compatibility.
    doc_phases: Dict[str, Dict[str, str]] = field(default_factory=dict)
    # Optional callback invoked whenever the enabled work product set changes.
    on_change: Optional[Callable[[], None]] = field(default=None, repr=False)
    # Phases and diagrams that have been frozen due to created work products
    frozen_modules: set[str] = field(default_factory=set)
    frozen_diagrams: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        global ACTIVE_TOOLBOX
        ACTIVE_TOOLBOX = self

    # ------------------------------------------------------------------
    def module_frozen(self, name: Optional[str]) -> bool:
        if not name:
            return False
        mod = self._find_module(name, self.modules)
        return bool(mod and getattr(mod, "frozen", False))

    # ------------------------------------------------------------------
    def set_diagram_frozen(self, name: str, frozen: bool) -> None:
        """Toggle immutability of a governance diagram."""
        diag_id = self.diagrams.get(name)
        if not diag_id:
            return
        repo = SysMLRepository.get_instance()
        if frozen:
            repo.freeze_diagram(diag_id)
            self.frozen_diagrams.add(name)
        else:
            repo.unfreeze_diagram(diag_id)
            self.frozen_diagrams.discard(name)

    # ------------------------------------------------------------------
    def set_all_diagrams_frozen(self, frozen: bool) -> None:
        """Freeze or unfreeze every registered governance diagram."""
        for name in self.list_diagrams():
            self.set_diagram_frozen(name, frozen)

    # ------------------------------------------------------------------
    def diagram_frozen(self, name: str) -> bool:
        """Return ``True`` if the named diagram is frozen."""
        return name in self.frozen_diagrams

    # ------------------------------------------------------------------
    def freeze_active_phase(self) -> None:
        """Mark the currently active module as frozen and lock its diagrams."""
        if not self.active_module or self.module_frozen(self.active_module):
            return
        mod = self._find_module(self.active_module, self.modules)
        if not mod:
            return
        diags = self.diagrams_in_module(self.active_module)
        if not diags:
            return
        mod.frozen = True
        repo = SysMLRepository.get_instance()
        for name in diags:
            diag_id = self.diagrams.get(name)
            if not diag_id:
                continue
            diag = repo.diagrams.get(diag_id)
            if diag:
                diag.locked = True
        self._freeze_active_phase()

    # ------------------------------------------------------------------
    def add_work_product(self, diagram: str, analysis: str, rationale: str) -> None:
        """Add a work product linking a diagram to an analysis with rationale."""
        mod = self.module_for_diagram(diagram)
        if self.module_frozen(mod):
            return
        self.work_products.append(SafetyWorkProduct(diagram, analysis, rationale))
        if self.on_change:
            self.on_change()

    # ------------------------------------------------------------------
    def remove_work_product(self, diagram: str, analysis: str) -> bool:
        """Remove a work product declaration if no documents of that type exist.

        Parameters
        ----------
        diagram: str
            Name of the governance diagram containing the declaration.
        analysis: str
            The analysis/work product type to remove.

        Returns
        -------
        bool
            ``True`` when the declaration was removed, ``False`` if it could
            not be removed because there are existing work products of this
            type or the declaration was not found.
        """

        mod = self.module_for_diagram(diagram)
        if self.module_frozen(mod):
            return False
        if self.work_product_counts.get(analysis, 0) > 0:
            return False

        for idx, wp in enumerate(list(self.work_products)):
            if wp.diagram == diagram and wp.analysis == analysis:
                del self.work_products[idx]
                if self.on_change:
                    self.on_change()
                return True
        return False

    # ------------------------------------------------------------------
    def register_created_work_product(self, analysis: str, name: str) -> None:
        """Record creation of a work product document of type ``analysis``."""
        self.work_product_counts[analysis] = self.work_product_counts.get(analysis, 0) + 1
        if self.active_module:
            self.doc_phases.setdefault(analysis, {})[name] = self.active_module
            self.freeze_active_phase()

    # ------------------------------------------------------------------
    def register_loaded_work_product(self, analysis: str, name: str) -> None:
        """Record a document loaded from disk without changing its phase."""
        self.work_product_counts[analysis] = self.work_product_counts.get(analysis, 0) + 1

    # ------------------------------------------------------------------
    def register_deleted_work_product(self, analysis: str, name: str) -> None:
        """Record deletion of a work product document of type ``analysis``."""
        if self.work_product_counts.get(analysis, 0) > 0:
            self.work_product_counts[analysis] -= 1
        if name:
            self.doc_phases.get(analysis, {}).pop(name, None)

    # ------------------------------------------------------------------
    def _freeze_active_phase(self) -> None:
        """Freeze the currently active phase and its governance diagrams."""
        if not self.active_module:
            return
        if self.active_module in self.frozen_modules:
            return
        repo = SysMLRepository.get_instance()
        self.frozen_modules.add(self.active_module)
        for diag_name in self.diagrams_in_module(self.active_module):
            self.frozen_diagrams.add(diag_name)
            diag_id = self.diagrams.get(diag_name)
            if diag_id:
                repo.freeze_diagram(diag_id)

    # ------------------------------------------------------------------
    def rename_document(self, analysis: str, old: str, new: str) -> None:
        """Update phase mapping when a document is renamed."""
        phase = self.doc_phases.get(analysis, {}).pop(old, None)
        if phase:
            self.doc_phases.setdefault(analysis, {})[new] = phase

    # ------------------------------------------------------------------
    def _reuse_map(self) -> Dict[str, Dict[str, set[str]]]:
        """Return mapping of phase -> reused work products and phases."""
        repo = SysMLRepository.get_instance()
        mapping: Dict[str, Dict[str, set[str]]] = {}
        for diag_id in self.diagrams.values():
            diag = repo.diagrams.get(diag_id)
            if not diag:
                continue
            obj_map = {
                obj.get("obj_id"): (
                    obj.get("obj_type"),
                    obj.get("properties", {}).get("name"),
                )
                for obj in getattr(diag, "objects", [])
            }
            for conn in getattr(diag, "connections", []):
                if conn.get("conn_type") != "Re-use":
                    continue
                src = obj_map.get(conn.get("src"))
                dst = obj_map.get(conn.get("dst"))
                if not src or not dst:
                    continue
                if src[0] != "Lifecycle Phase":
                    continue
                phase = src[1]
                data = mapping.setdefault(phase, {"work_products": set(), "phases": set()})
                if dst[0] == "Work Product":
                    data["work_products"].add(dst[1])
                elif dst[0] == "Lifecycle Phase":
                    data["phases"].add(dst[1])
        return mapping

    # ------------------------------------------------------------------
    def document_visible(self, analysis: str, name: str) -> bool:
        """Return ``True`` if the document should be visible in the active phase."""
        if not self.active_module:
            return True
        phase = self.doc_phases.get(analysis, {}).get(name)
        if phase is None:
            repo = SysMLRepository.get_instance()
            diag = next(
                (
                    d
                    for d in repo.diagrams.values()
                    if d.diag_type == analysis and d.name == name
                ),
                None,
            )
            phase = diag.phase if diag else None
        if phase is None:
            return False
        if phase == self.active_module:
            return True
        reuse = self._reuse_map().get(self.active_module, {})
        if analysis in reuse.get("work_products", set()):
            return True
        if phase in reuse.get("phases", set()):
            return True
        return False

    # ------------------------------------------------------------------
    def document_read_only(self, analysis: str, name: str) -> bool:
        """Return ``True`` when *analysis* document *name* is reused.

        Documents originating from a different lifecycle phase but made
        visible via a ``Re-use`` relationship should not be editable. This
        helper mirrors :meth:`document_visible` but returns ``True`` only when
        the document is visible in the active phase due to reuse rather than
        because it was created there.
        """
        if not self.active_module:
            return False
        phase = self.doc_phases.get(analysis, {}).get(name)
        if phase is None:
            repo = SysMLRepository.get_instance()
            diag = next(
                (
                    d
                    for d in repo.diagrams.values()
                    if d.diag_type == analysis and d.name == name
                ),
                None,
            )
            phase = diag.phase if diag else None
        if phase is None or phase == self.active_module:
            return False
        reuse = self._reuse_map().get(self.active_module, {})
        if analysis in reuse.get("work_products", set()):
            return True
        if phase in reuse.get("phases", set()):
            return True
        return False

    # ------------------------------------------------------------------
    def _work_products_in_diagrams(self, names: set[str]) -> set[str]:
        """Return work product names declared within ``names`` diagrams.

        The lookup inspects diagram objects directly so copied work product
        elements from other lifecycle phases still govern tools in the active
        phase. Only objects with ``obj_type`` set to ``"Work Product"`` and a
        non-empty ``name`` property contribute to the result.
        """

        repo = SysMLRepository.get_instance()
        result: set[str] = set()
        for diag_name in names:
            diag_id = self.diagrams.get(diag_name)
            if not diag_id:
                continue
            diag = repo.diagrams.get(diag_id)
            if not diag:
                continue
            for obj in getattr(diag, "objects", []):
                odict = obj if isinstance(obj, dict) else obj.__dict__
                if odict.get("obj_type") == "Work Product":
                    wp_name = odict.get("properties", {}).get("name", "")
                    if wp_name:
                        result.add(wp_name)
        return result

    # ------------------------------------------------------------------
    def enabled_products(self) -> set[str]:
        """Return analysis names declared in the active lifecycle phase."""

        # Work products become available to the application only when they are
        # declared on a governance diagram that belongs to the active phase.
        # ``Re-use`` links may pull additional work products or entire phases
        # into the active one so those must be considered as well.  When no
        # phase is active we expose every declared work product so that a brand
        # new project still shows its analyses.
        if not self.active_module:
            return {wp.analysis for wp in self.work_products}

        names = self.diagrams_in_module(self.active_module)
        reuse = self._reuse_map().get(self.active_module, {})
        reused_wps = reuse.get("work_products", set())
        reused_phases = reuse.get("phases", set())

        enabled: set[str] = self._work_products_in_diagrams(names)
        for wp in self.work_products:
            if wp.diagram in names:
                enabled.add(wp.analysis)
                continue
            if wp.analysis in reused_wps:
                enabled.add(wp.analysis)
                continue
            mod = self.module_for_diagram(wp.diagram)
            if mod in reused_phases:
                enabled.add(wp.analysis)
        return enabled

    # ------------------------------------------------------------------
    def is_enabled(self, analysis: str) -> bool:
        """Check whether ``analysis`` has been enabled via governance."""
        return analysis in self.enabled_products()

    # ------------------------------------------------------------------
    def set_active_module(self, name: Optional[str]) -> None:
        """Select the active lifecycle phase by module *name*."""
        self.active_module = name
        repo = SysMLRepository.get_instance()
        repo.active_phase = name
        if name:
            reuse = self._reuse_map().get(name, {})
            repo.reuse_phases = set(reuse.get("phases", set()))
            repo.reuse_products = set(reuse.get("work_products", set()))
        else:
            repo.reuse_phases = set()
            repo.reuse_products = set()
        if self.on_change:
            self.on_change()

    # ------------------------------------------------------------------
    def _find_module(self, name: str, modules: List[GovernanceModule]) -> Optional[GovernanceModule]:
        for mod in modules:
            if mod.name == name:
                return mod
            found = self._find_module(name, mod.modules)
            if found:
                return found
        return None

    # ------------------------------------------------------------------
    def diagrams_in_module(self, name: str) -> set[str]:
        """Return all diagram names contained within module *name*.

        The special ``GLOBAL`` module contains all governance diagrams that do
        not declare a lifecycle phase."""

        repo = SysMLRepository.get_instance()
        if name == GLOBAL_PHASE:
            names = set(self.list_diagrams())

            def _remove_mods(mods: List[GovernanceModule]) -> None:
                for m in mods:
                    names.difference_update(m.diagrams)
                    _remove_mods(m.modules)

            _remove_mods(self.modules)
            names = {
                n
                for n in names
                if not getattr(repo.diagrams.get(self.diagrams.get(n)), "phase", None)
            }
            return names

        mod = self._find_module(name, self.modules)
        names: set[str] = set()
        if mod:
            def _collect(m: GovernanceModule) -> None:
                names.update(m.diagrams)
                for sub in m.modules:
                    _collect(sub)

            _collect(mod)

        names.update(
            d.name
            for d in repo.diagrams.values()
            if d.diag_type == "Governance Diagram"
            and "safety-management" in getattr(d, "tags", [])
            and d.phase == name
        )
        return names

    # ------------------------------------------------------------------
    def diagrams_for_module(self, name: str) -> set[str]:
        """Return all diagram names contained within module *name*.

        This is a compatibility wrapper around :meth:`diagrams_in_module` used
        by some GUI components."""
        return self.diagrams_in_module(name)

    # ------------------------------------------------------------------
    def module_for_diagram(self, diagram: str) -> Optional[str]:
        """Return the module name directly containing ``diagram``.

        Parameters
        ----------
        diagram:
            Human readable name of the diagram to locate.

        Returns
        -------
        Optional[str]
            The name of the module containing the diagram or ``None`` when the
            diagram is not assigned to any module."""

        def _search(mods: List[GovernanceModule]) -> Optional[str]:
            for mod in mods:
                if diagram in mod.diagrams:
                    return mod.name
                found = _search(mod.modules)
                if found:
                    return found
            return None

        found = _search(self.modules)
        if found:
            return found

        # Fallback to the repository metadata when the diagram has a lifecycle
        # phase assigned but is not tracked inside the toolbox hierarchy.
        repo = SysMLRepository.get_instance()
        diag = next((d for d in repo.diagrams.values() if d.name == diagram), None)
        if not diag:
            return None
        return getattr(diag, "phase", None) or GLOBAL_PHASE

    def phase_for_document(self, analysis: str, name: str) -> Optional[str]:
        """Return lifecycle phase assigned to ``analysis`` document ``name``."""

        phase = self.doc_phases.get(analysis, {}).get(name)
        if phase is None:
            repo = SysMLRepository.get_instance()
            diag = next(
                (
                    d
                    for d in repo.diagrams.values()
                    if d.diag_type == analysis and d.name == name
                ),
                None,
            )
            phase = (diag.phase if diag else None) or (GLOBAL_PHASE if diag else None)
        return phase

    def activate_phase(self, phase: str, app=None) -> None:
        """Synchronize *app* and toolbox with the given lifecycle *phase*."""

        if not phase:
            return
        if app and hasattr(app, "lifecycle_var"):
            try:
                app.lifecycle_var.set(phase)
            except Exception:
                pass
        if app and hasattr(app, "on_lifecycle_selected"):
            try:
                app.on_lifecycle_selected()
            except Exception:
                pass
        else:
            self.set_active_module(phase)
        if app and hasattr(app, "refresh_tool_enablement"):
            try:
                app.refresh_tool_enablement()
            except Exception:
                pass
        smw = getattr(app, "safety_mgmt_window", None)
        if smw and hasattr(smw, "phase_var"):
            try:
                if smw.phase_var.get() != phase:
                    smw.phase_var.set(phase)
                    if hasattr(smw, "refresh_diagrams"):
                        smw.refresh_diagrams()
            except Exception:
                pass

    def activate_document_phase(self, analysis: str, name: str, app=None) -> None:
        """Activate phase for document ``name`` of ``analysis``."""

        phase = self.phase_for_document(analysis, name)
        if phase:
            self.activate_phase(phase, app)

    def list_modules(self) -> List[str]:
        """Return names of all governance modules including submodules.

        Always include the special ``GLOBAL`` phase representing diagrams
        without an assigned lifecycle phase."""

        names: List[str] = []

        def _collect(mods: List[GovernanceModule]) -> None:
            for m in mods:
                names.append(m.name)
                _collect(m.modules)

        _collect(self.modules)
        if GLOBAL_PHASE not in names:
            names.append(GLOBAL_PHASE)
        return names

    # ------------------------------------------------------------------
    def _unique_module_name(self, name: str, exclude: Optional[str] = None) -> str:
        """Return a module name unique within the toolbox.

        Parameters
        ----------
        name: str
            Desired module name.
        exclude: Optional[str]
            Optional module name to exclude from uniqueness checks. This is
            useful when renaming an existing module.
        """
        existing = set(self.list_modules())
        if exclude:
            existing.discard(exclude)
        base = name
        suffix = 1
        while name in existing:
            name = f"{base}_{suffix}"
            suffix += 1
        return name

    # ------------------------------------------------------------------
    def add_module(self, name: str, parent: Optional[GovernanceModule] = None) -> GovernanceModule:
        """Create a new governance module with a unique name.

        The new module is added either to the top-level module list or as a
        submodule of ``parent`` when provided. The final module name is returned
        in the created :class:`GovernanceModule` instance.
        """
        unique = self._unique_module_name(name)
        mod = GovernanceModule(unique)
        if parent:
            parent.modules.append(mod)
        else:
            self.modules.append(mod)
        return mod

    # ------------------------------------------------------------------
    def rename_module(self, old: str, new: str) -> None:
        """Rename a governance module ensuring uniqueness.

        If ``new`` conflicts with an existing module name the method appends
        a numeric suffix to make it unique. The :attr:`active_module` is updated
        when it references the renamed module.
        """

        if not new or old == new or old in self.frozen_modules:
            return

        if not self._find_module(old, self.modules):
            return

        new = self._unique_module_name(new, exclude=old)

        def _rename(mods: List[GovernanceModule]) -> bool:
            for mod in mods:
                if mod.name == old:
                    mod.name = new
                    if self.active_module == old:
                        self.active_module = new
                    return True
                if _rename(mod.modules):
                    return True
            return False

        _rename(self.modules)

        repo = SysMLRepository.get_instance()
        repo.rename_phase(old, new)

        for docs in self.doc_phases.values():
            for doc, phase in list(docs.items()):
                if phase == old:
                    docs[doc] = new

    # ------------------------------------------------------------------
    def propagation_type(self, source: str, target: str) -> Optional[str]:
        """Return propagation relationship type from ``source`` to ``target``.

        The method searches all governance diagrams for a connection linking
        the two named work products using one of the propagation relationship
        types. ``None`` is returned when no such link exists."""

        repo = SysMLRepository.get_instance()
        # Consider traces across all governance diagrams regardless of the
        # active module so relationships defined in earlier phases still
        # propagate to later analyses.
        diag_ids = list(self.diagrams.values())
        for diag_id in diag_ids:
            diag = repo.diagrams.get(diag_id)
            if not diag:
                continue
            src_id = dst_id = None
            for obj in getattr(diag, "objects", []):
                if obj.get("obj_type") != "Work Product":
                    continue
                name = obj.get("properties", {}).get("name")
                if name == source:
                    src_id = obj.get("obj_id")
                elif name == target:
                    dst_id = obj.get("obj_id")
            if src_id is None or dst_id is None:
                continue
            for c in getattr(diag, "connections", []):
                stereo = (c.get("stereotype") or c.get("conn_type") or "").lower()
                if (
                    c.get("src") == src_id
                    and c.get("dst") == dst_id
                    and stereo
                    in {"propagate", "propagate by review", "propagate by approval"}
                ):
                    mapping = {
                        "propagate": "Propagate",
                        "propagate by review": "Propagate by Review",
                        "propagate by approval": "Propagate by Approval",
                    }
                    return c.get("conn_type") or mapping[stereo]
        return None

    # ------------------------------------------------------------------
    def can_propagate(
        self,
        source: str,
        target: str,
        *,
        reviewed: bool = False,
        joint_review: bool = False,
    ) -> bool:
        """Return ``True`` if results may propagate from ``source`` to ``target``.

        ``Propagate`` links always allow propagation. ``Propagate by Review``
        requires that a peer review has been performed (``reviewed``). ``Propagate
        by Approval`` requires a completed joint review (``joint_review``).
        ``False`` is returned when no propagation relationship exists."""

        rel = self.propagation_type(source, target)
        if rel == "Propagate":
            return True
        if rel == "Propagate by Review":
            return reviewed
        if rel == "Propagate by Approval":
            return joint_review
        return False

    # ------------------------------------------------------------------
    def _trace_mapping(self) -> Dict[str, set[str]]:
        """Return mapping of work product name to traceable targets."""
        repo = SysMLRepository.get_instance()
        # Use all known governance diagrams; restricting to the active module
        # prevents cross-phase links (e.g. Prototype traces feeding Series
        # Development analyses) from being honoured.
        diag_ids = list(self.diagrams.values())
        mapping: Dict[str, set[str]] = {}
        for diag_id in diag_ids:
            if not repo.diagram_visible(diag_id):
                continue
            diag = repo.diagrams.get(diag_id)
            if not diag:
                continue
            id_to_name: Dict[int, str] = {}
            for obj in getattr(diag, "objects", []):
                if obj.get("obj_type") == "Work Product":
                    name = obj.get("properties", {}).get("name")
                    if name:
                        id_to_name[obj.get("obj_id")] = name
            for conn in getattr(diag, "connections", []):
                stereo = (conn.get("stereotype") or conn.get("conn_type") or "").lower()
                if stereo == "trace":
                    sname = id_to_name.get(conn.get("src"))
                    tname = id_to_name.get(conn.get("dst"))
                    if sname and tname:
                        mapping.setdefault(sname, set()).add(tname)
                        mapping.setdefault(tname, set()).add(sname)
        return mapping

    # ------------------------------------------------------------------
    def _analysis_mapping(self) -> Dict[str, Dict[str, set[str]]]:
        """Return mapping of work product name to analysis targets by relation."""
        repo = SysMLRepository.get_instance()
        # Analyse all governance diagrams; limiting to the active module would
        # hide relationships defined in other lifecycle phases.
        diag_ids = list(self.diagrams.values())
        mapping: Dict[str, Dict[str, set[str]]] = {}
        for diag_id in diag_ids:
            if not repo.diagram_visible(diag_id):
                continue
            diag = repo.diagrams.get(diag_id)
            if not diag:
                continue
            id_to_name: Dict[int, str] = {}
            for obj in getattr(diag, "objects", []):
                if obj.get("obj_type") == "Work Product":
                    name = obj.get("properties", {}).get("name")
                    if name:
                        id_to_name[obj.get("obj_id")] = name
            for conn in getattr(diag, "connections", []):
                stereo = (conn.get("stereotype") or conn.get("conn_type") or "").lower()
                if stereo in {"used by", "used after review", "used after approval"}:
                    sname = id_to_name.get(conn.get("src"))
                    tname = id_to_name.get(conn.get("dst"))
                    if sname and tname:
                        if sname == "STPA" and tname == "Architecture Diagram":
                            sname, tname = tname, sname
                        if (
                            sname in SAFETY_ANALYSIS_WORK_PRODUCTS
                            and tname in SAFETY_ANALYSIS_WORK_PRODUCTS
                            and sname != "Mission Profile"
                            and (sname, tname) not in ALLOWED_ANALYSIS_USAGE
                        ):
                            # Skip invalid safety analysis links that lack a
                            # dependency in the metamodel.
                            continue
                        mapping.setdefault(sname, {}).setdefault(stereo, set()).add(tname)
        return mapping

    # ------------------------------------------------------------------
    def _req_relation_mapping(self) -> Dict[str, Dict[str, set[str]]]:
        """Return mapping of requirement work products to relation targets.

        The returned dictionary is structured as ``source -> relation ->
        {targets}`` where *relation* is the connection stereotype used between
        work products such as ``"satisfied by"`` or ``"derived from"``.
        """
        repo = SysMLRepository.get_instance()
        diag_ids = self.diagrams.values()
        if self.active_module:
            names = self.diagrams_in_module(self.active_module)
            diag_ids = [self.diagrams.get(n) for n in names if self.diagrams.get(n)]
        mapping: Dict[str, Dict[str, set[str]]] = {}
        for diag_id in diag_ids:
            if not repo.diagram_visible(diag_id):
                continue
            diag = repo.diagrams.get(diag_id)
            if not diag:
                continue
            id_to_name: Dict[int, str] = {}
            for obj in getattr(diag, "objects", []):
                if obj.get("obj_type") == "Work Product":
                    name = obj.get("properties", {}).get("name")
                    if name:
                        id_to_name[obj.get("obj_id")] = name
            for conn in getattr(diag, "connections", []):
                stereo = (conn.get("stereotype") or conn.get("conn_type") or "").lower()
                if stereo in {"satisfied by", "derived from"}:
                    sname = id_to_name.get(conn.get("src"))
                    tname = id_to_name.get(conn.get("dst"))
                    from analysis.models import REQUIREMENT_WORK_PRODUCTS
                    req_wps = set(REQUIREMENT_WORK_PRODUCTS)
                    if (
                        sname in req_wps
                        and tname in req_wps
                    ):
                        mapping.setdefault(sname, {}).setdefault(stereo, set()).add(tname)
        return mapping

    # ------------------------------------------------------------------
    def _normalize_work_product(self, name: str) -> str:
        """Translate requirement types to their work product names."""
        from analysis.models import REQUIREMENT_TYPE_OPTIONS, REQUIREMENT_WORK_PRODUCTS

        try:
            idx = REQUIREMENT_TYPE_OPTIONS.index(name)
            return REQUIREMENT_WORK_PRODUCTS[idx + 1]
        except ValueError:
            return name

    # ------------------------------------------------------------------
    def can_trace(self, source: str, target: str) -> bool:
        """Return ``True`` if ``source`` may trace to ``target``."""
        from analysis.models import REQUIREMENT_WORK_PRODUCTS

        source = self._normalize_work_product(source)
        target = self._normalize_work_product(target)
        if source in REQUIREMENT_WORK_PRODUCTS and target in REQUIREMENT_WORK_PRODUCTS:
            return False
        traces = self._trace_mapping()
        if target in traces.get(source, set()):
            return True
        general = REQUIREMENT_WORK_PRODUCTS[0]
        specific_wps = set(REQUIREMENT_WORK_PRODUCTS[1:])
        if source in specific_wps and target in traces.get(general, set()):
            return True
        if target in specific_wps and source in traces.get(general, set()):
            return True
        return False

    # ------------------------------------------------------------------
    def can_link_requirements(self, src_type: str, dst_type: str, relation: str) -> bool:
        """Return ``True`` if requirements of ``src_type`` may relate to
        ``dst_type`` using ``relation`` (e.g., ``"satisfied by"``)."""

        from analysis.models import REQUIREMENT_WORK_PRODUCTS

        src_wp = self._normalize_work_product(src_type)
        dst_wp = self._normalize_work_product(dst_type)
        rels = self._req_relation_mapping()
        rel = relation.lower()
        if dst_wp in rels.get(src_wp, {}).get(rel, set()):
            return True
        general = REQUIREMENT_WORK_PRODUCTS[0]
        specific = set(REQUIREMENT_WORK_PRODUCTS[1:])
        gen_targets = rels.get(general, {}).get(rel, set())
        if src_wp in specific and (dst_wp in gen_targets or general in gen_targets):
            return True
        if dst_wp in specific and (src_wp in gen_targets or general in gen_targets):
            return True
        return False

    # ------------------------------------------------------------------
    def requirement_work_product(self, req_type: str) -> str:
        """Return the work product name for ``req_type`` if known."""
        return self._normalize_work_product(req_type)

    # ------------------------------------------------------------------
    def requirement_targets(self, req_type: str) -> set[str]:
        """Return allowed work product targets for ``req_type``."""
        wp = self.requirement_work_product(req_type)
        if not wp:
            return set()
        traces = self._trace_mapping()
        return set(traces.get(wp, set()))

    # ------------------------------------------------------------------
    def analysis_targets(
        self, source: str, *, reviewed: bool = False, approved: bool = False
    ) -> set[str]:
        """Return allowed analysis targets for ``source`` work product.

        Traces are followed transitively so if ``source`` traces to another work
        product which in turn is "Used By" an analysis then that analysis is
        considered a valid target for ``source`` as well.  "Used after Review"
        and "Used after Approval" relations only become visible when the
        corresponding state flag is provided.
        """
        analyses = self._analysis_mapping()
        traces = self._trace_mapping()

        # Discover all work products reachable from ``source`` via trace links
        seen: set[str] = set()
        queue = [source]
        reachable: set[str] = set()
        while queue:
            cur = queue.pop(0)
            if cur in seen:
                continue
            seen.add(cur)
            reachable.add(cur)
            queue.extend(traces.get(cur, set()) - seen)

        targets: set[str] = set()
        for src in reachable:
            rels = analyses.get(src, {})
            targets |= rels.get("used by", set())
            if reviewed or approved:
                targets |= rels.get("used after review", set())
            if approved:
                targets |= rels.get("used after approval", set())
        return targets

    # ------------------------------------------------------------------
    def analysis_inputs(
        self, target: str, *, reviewed: bool = False, approved: bool = False
    ) -> set[str]:
        """Return work products that may serve as input to ``target`` analysis.

        Any work product that traces to another work product with a direct
        relationship to ``target`` is also considered an input.  Visibility of
        "Used after Review" and "Used after Approval" relations depends on the
        provided state flags.
        """
        analyses = self._analysis_mapping()
        traces = self._trace_mapping()

        # When a lifecycle phase is active only analyses declared in that phase
        # (or pulled in via re-use links) should expose their governed inputs.
        if self.active_module and target not in self.enabled_products():
            return set()

        enabled_sources: set[str] | None = None
        if self.active_module:
            names = self.diagrams_in_module(self.active_module)
            reuse = self._reuse_map().get(self.active_module, {})
            reused_wps = reuse.get("work_products", set())
            reused_phases = reuse.get("phases", set())
            enabled_sources = set()
            for wp in self.work_products:
                mod = self.module_for_diagram(wp.diagram)
                if (
                    wp.diagram in names
                    or wp.analysis in reused_wps
                    or mod in reused_phases
                ):
                    enabled_sources.add(wp.analysis)

        direct: set[str] = set()
        for src, rels in analyses.items():
            if enabled_sources is not None and src not in enabled_sources:
                continue
            if target in rels.get("used by", set()):
                direct.add(src)
            if target in rels.get("used after review", set()) and (reviewed or approved):
                direct.add(src)
            if target in rels.get("used after approval", set()) and approved:
                direct.add(src)

        sources = set(direct)
        queue = list(direct)
        while queue:
            cur = queue.pop(0)
            for neigh in traces.get(cur, set()):
                if neigh not in sources:
                    if enabled_sources is not None and neigh not in enabled_sources:
                        continue
                    sources.add(neigh)
                    queue.append(neigh)
        if enabled_sources is not None:
            sources &= enabled_sources
        return sources

    # ------------------------------------------------------------------
    def analysis_usage_type(self, source: str, target: str) -> Optional[str]:
        """Return the relationship type for using ``source`` as input to ``target``.

        Direct connections are checked first. If none are found, trace links are
        followed transitively to locate an intermediate work product connected to
        ``target``.
        """
        analyses = self._analysis_mapping()
        traces = self._trace_mapping()

        visited: set[str] = set()
        queue = [source]
        mapping = {
            "used by": "Used By",
            "used after review": "Used after Review",
            "used after approval": "Used after Approval",
        }
        while queue:
            cur = queue.pop(0)
            if cur in visited:
                continue
            visited.add(cur)
            rels = analyses.get(cur, {})
            for key, human in mapping.items():
                if target in rels.get(key, set()):
                    return human
            queue.extend(traces.get(cur, set()) - visited)
        return None

    # ------------------------------------------------------------------
    def can_use_as_input(
        self,
        source: str,
        target: str,
        *,
        reviewed: bool = False,
        approved: bool = False,
    ) -> bool:
        """Return ``True`` if ``source`` may be used as input to ``target``."""
        rel = self.analysis_usage_type(source, target)
        if rel == "Used By":
            return True
        if rel == "Used after Review":
            return reviewed or approved
        if rel == "Used after Approval":
            return approved
        return False

    # ------------------------------------------------------------------
    def requirement_diagram_targets(self, req_type: str) -> set[str]:
        """Return diagrams containing allowed targets for ``req_type``."""
        targets = self.requirement_targets(req_type)
        return {
            wp.diagram
            for wp in self.work_products
            if wp.analysis in targets
        }

    def build_lifecycle(self, stages: List[str]) -> None:
        """Define the project lifecycle stages."""
        self.lifecycle = stages

    def define_workflow(self, name: str, steps: List[str]) -> None:
        """Record an ordered list of steps for a workflow."""
        self.workflows[name] = steps

    def get_work_products(self) -> List[SafetyWorkProduct]:
        """Return all registered work products including traceability info."""
        traces = self._trace_mapping()
        analyses = self._analysis_mapping()
        products: List[SafetyWorkProduct] = []
        for wp in self.work_products:
            wp.traceable = sorted(traces.get(wp.analysis, set()))
            rels = analyses.get(wp.analysis, {})
            combined: set[str] = set()
            for vals in rels.values():
                combined |= vals
            wp.analyzable = sorted(combined)
            products.append(wp)
        return products

    def get_workflow(self, name: str) -> List[str]:
        """Return the steps for the requested workflow."""
        return self.workflows.get(name, [])

    # ------------------------------------------------------------------
    # Diagram management helpers
    # ------------------------------------------------------------------
    def create_diagram(self, name: str) -> str:
        """Create a new Governance Diagram tracked by this toolbox.

        Parameters
        ----------
        name: str
            Human readable name of the diagram.

        Returns
        -------
        str
            The repository identifier of the created diagram.
        """
        was_empty = not self.diagrams
        repo = SysMLRepository.get_instance()
        diag = repo.create_diagram("Governance Diagram", name=name)
        diag.tags.append("safety-management")
        # ``diag`` may have been renamed by the repository to ensure
        # uniqueness. Track the actual diagram name so internal mappings stay
        # consistent with repository contents.
        self.diagrams[diag.name] = diag.diag_id
        if was_empty:
            regenerate_requirement_patterns()
        return diag.diag_id

    def delete_diagram(self, name: str) -> None:
        """Remove a diagram from the toolbox and repository."""
        if name in self.frozen_diagrams:
            return
        diag_id = self.diagrams.get(name)
        if not diag_id:
            return
        repo = SysMLRepository.get_instance()
        if repo.diagram_read_only(diag_id):
            return
        repo.delete_diagram(diag_id)
        del self.diagrams[name]

    def rename_diagram(self, old: str, new: str) -> str:
        """Rename a managed diagram ensuring the name remains unique.

        Parameters
        ----------
        old: str
            Current diagram name.
        new: str
            Desired new name for the diagram.
        """
        if old in self.frozen_diagrams:
            return old
        diag_id = self.diagrams.get(old)
        if not diag_id or not new:
            return old
        repo = SysMLRepository.get_instance()
        if repo.diagram_read_only(diag_id):
            return old
        diag = repo.diagrams.get(diag_id)
        if not diag:
            return old

        # Ensure the new name is unique across all diagrams
        existing = {d.name for d in repo.diagrams.values() if d.diag_id != diag_id}
        base = new
        suffix = 1
        while new in existing:
            new = f"{base}_{suffix}"
            suffix += 1

        diag.name = new
        repo.touch_diagram(diag_id)
        del self.diagrams[old]
        self.diagrams[new] = diag_id
        return new

    def list_diagrams(self) -> List[str]:
        """Return the names of all managed diagrams.

        Any Governance Diagram in the repository tagged with
        ``"safety-management"`` should appear in the toolbox even if it
        was created outside of :meth:`create_diagram`. To ensure the list is
        complete we rescan the repository on each call and synchronize the
        internal ``diagrams`` mapping.
        """
        self._sync_diagrams()
        return list(self.diagrams.keys())

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        """Return a JSON serialisable representation of the toolbox.

        All dataclass members, including the folder hierarchy stored in
        :attr:`modules`, are converted into primitive Python types so they can
        be saved using :mod:`json` or similar libraries.
        """
        return {
            "work_products": [wp.__dict__ for wp in self.work_products],
            "lifecycle": list(self.lifecycle),
            "workflows": {k: list(v) for k, v in self.workflows.items()},
            "diagrams": dict(self.diagrams),
            "modules": [m.to_dict() for m in self.modules],
            "active_module": self.active_module,
            "doc_phases": {k: dict(v) for k, v in self.doc_phases.items()},
            "frozen_modules": list(self.frozen_modules),
            "frozen_diagrams": list(self.frozen_diagrams),
        }

    # ------------------------------------------------------------------
    @classmethod
    def from_dict(cls, data: dict) -> "SafetyManagementToolbox":
        """Create a toolbox instance from serialized *data*.

        The folder structure is reconstructed using
        :meth:`GovernanceModule.from_dict` ensuring that the Safety & Security Management
        Explorer reflects the saved hierarchy on reload.
        """
        toolbox = cls()
        toolbox.work_products = [
            SafetyWorkProduct(**wp) for wp in data.get("work_products", [])
        ]
        toolbox.lifecycle = list(data.get("lifecycle", []))
        toolbox.workflows = {
            k: list(v) for k, v in data.get("workflows", {}).items()
        }
        toolbox.diagrams = dict(data.get("diagrams", {}))
        toolbox.modules = [
            GovernanceModule.from_dict(m) for m in data.get("modules", [])
        ]
        toolbox.active_module = data.get("active_module")
        toolbox.doc_phases = {
            k: dict(v) for k, v in data.get("doc_phases", {}).items()
        }
        toolbox.frozen_modules = set(data.get("frozen_modules", []))
        toolbox.frozen_diagrams = set(data.get("frozen_diagrams", []))
        repo = SysMLRepository.get_instance()
        for name in toolbox.frozen_diagrams:
            diag_id = toolbox.diagrams.get(name)
            if diag_id:
                repo.freeze_diagram(diag_id)
        return toolbox

    # ------------------------------------------------------------------
    def diagram_hierarchy(self) -> List[List[str]]:
        """Return governance diagrams arranged into hierarchy levels.

        Diagrams appear in successive levels when a task in one diagram links
        to another diagram. Any diagrams not referenced by others start at the
        top level. Each level lists diagram names sorted alphabetically.
        """
        self._sync_diagrams()
        repo = SysMLRepository.get_instance()

        edges: dict[str, set[str]] = {d: set() for d in self.diagrams.values()}
        reverse: dict[str, set[str]] = {d: set() for d in self.diagrams.values()}

        for diag_id in edges:
            diag = repo.diagrams.get(diag_id)
            if not diag:
                continue
            for obj in getattr(diag, "objects", []):
                # ``objects`` may contain plain dictionaries from the repository
                # or ``SysMLObject`` instances used by the GUI.  Support both.
                elem_id = (
                    obj.get("element_id") if isinstance(obj, dict) else getattr(obj, "element_id", None)
                )
                if not elem_id:
                    continue

                target = repo.get_linked_diagram(elem_id)

                if not target:
                    # Some diagrams reference others through object properties
                    # rather than explicit repository links. These appear as
                    # ``view`` or ``diagram`` identifiers within the object's
                    # property mapping. Support both dictionary and dataclass
                    # representations.
                    props = (
                        obj.get("properties", {})
                        if isinstance(obj, dict)
                        else getattr(obj, "properties", {})
                    )
                    target = props.get("view") or props.get("diagram")

                if target in edges:
                    edges[diag_id].add(target)
                    reverse[target].add(diag_id)

        roots = sorted(
            (d for d in edges if not reverse[d]),
            key=lambda d: repo.diagrams[d].name,
        )
        levels: List[List[str]] = []
        visited: set[str] = set()
        current = roots
        while current:
            levels.append(sorted(repo.diagrams[d].name for d in current))
            visited.update(current)
            next_level: set[str] = set()
            for d in current:
                next_level.update(child for child in edges[d] if child not in visited)
            current = sorted(next_level, key=lambda d: repo.diagrams[d].name)

        remaining = sorted(
            [d for d in edges if d not in visited],
            key=lambda d: repo.diagrams[d].name,
        )
        for d in remaining:
            levels.append([repo.diagrams[d].name])

        return levels

    def _replace_name_in_modules(
        self, old: str, new: str, mods: List[GovernanceModule]
    ) -> None:
        """Recursively replace diagram name ``old`` with ``new`` in modules."""
        for mod in mods:
            mod.diagrams = [new if d == old else d for d in mod.diagrams]
            self._replace_name_in_modules(old, new, mod.modules)

    def _prune_module_diagrams(self, existing: set[str], mods: List[GovernanceModule]) -> None:
        """Remove diagram names from modules that are not in ``existing``."""
        for mod in mods:
            mod.diagrams = [d for d in mod.diagrams if d in existing]
            self._prune_module_diagrams(existing, mod.modules)

    # ------------------------------------------------------------------
    def _sync_diagrams(self) -> None:
        """Synchronize ``self.diagrams`` with repository contents.

        Any diagram tagged ``"safety-management"`` is added to the mapping
        and entries for diagrams that no longer exist are dropped.
        """
        repo = SysMLRepository.get_instance()
        # Map current repository diagrams by identifier so we can detect
        # renamed diagrams. ``self.diagrams`` stores the reverse mapping of
        # name -> id.
        current: dict[str, str] = {
            d.diag_id: d.name
            for d in repo.diagrams.values()
            if "safety-management" in getattr(d, "tags", [])
        }

        # Remember the previous name for each diagram so folder references can
        # be updated when a diagram is renamed outside the explorer.
        previous: dict[str, str] = {v: k for k, v in self.diagrams.items()}

        self.diagrams.clear()
        for diag_id, name in current.items():
            old_name = previous.get(diag_id)
            if old_name and old_name != name:
                self._replace_name_in_modules(old_name, name, self.modules)
            self.diagrams[name] = diag_id

        # Remove stale diagram names from modules when diagrams were deleted
        # or renamed.
        self._prune_module_diagrams(set(self.diagrams.keys()), self.modules)

