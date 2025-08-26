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

import datetime
from analysis.utils import (
    derive_validation_target,
    exposure_to_probability,
    controllability_to_probability,
    severity_to_probability,
)
from analysis.risk_assessment import boolify
from analysis.user_config import CURRENT_USER_NAME
from gui.controls import messagebox


class FaultTreeNode:
    def __init__(self, user_name, node_type, parent=None):
        from AutoML import AutoML_Helper
        self.unique_id = AutoML_Helper.get_next_unique_id()
        # Assign a sequential default name if none is provided
        self.user_name = user_name if user_name else f"Node {self.unique_id}"
        self.node_type = node_type
        self.children = []
        self.parents = []
        if parent is not None:
            self.parents.append(parent)
        self.quant_value = None
        # Import here to avoid circular dependency during module import
        from AutoML import GATE_NODE_TYPES
        self.gate_type = "AND" if node_type.upper() in GATE_NODE_TYPES else None
        self.description = ""
        self.rationale = ""
        self.x = 50
        self.y = 50
        # Severity and controllability now use a 1-3 scale
        # Default to the lowest level until linked to a risk assessment entry
        self.severity = 1 if node_type.upper() == "TOP EVENT" else None
        self.controllability = 1 if node_type.upper() == "TOP EVENT" else None
        self.exposure = 1 if node_type.upper() == "TOP EVENT" else None
        self.input_subtype = None
        self.display_label = ""
        self.equation = ""
        self.detailed_equation = ""
        self.is_page = False
        self.is_primary_instance = True
        self.original = self
        self.created = datetime.datetime.now().isoformat()
        self.author = CURRENT_USER_NAME
        self.modified = self.created
        self.modified_by = CURRENT_USER_NAME
        self.safety_goal_description = ""
        self.safety_goal_asil = ""
        self.safe_state = ""
        self.ftti = ""
        self.validation_target = 1.0
        self.validation_desc = ""
        self.mission_profile = ""
        self.acceptance_criteria = ""
        self.acceptance_rate = 0.0
        self.operational_hours_on = 0.0
        self.exposure_given_hb = 1.0
        self.uncontrollable_given_exposure = 1.0
        self.severity_given_uncontrollable = 1.0
        self.status = "draft"
        self.approved = False
        # Targets for safety goal metrics
        self.sg_dc_target = 0.0
        self.sg_spfm_target = 0.0
        self.sg_lpfm_target = 0.0
        self.vehicle_safety_requirements = []          # List of vehicle safety requirements
        self.operational_safety_requirements = []        # List of operational safety requirements
        # Each requirement is a dict with keys: "id", "req_type" and "text"
        self.safety_requirements = []
        # --- FMEA attributes for basic events (AIAG style) ---
        self.fmea_effect = ""       # Description of effect/failure mode
        self.fmea_cause = ""        # Potential cause of failure
        self.fmea_severity = 1       # 1-10 scale
        self.fmea_occurrence = 1     # 1-10 scale
        self.fmea_detection = 1      # 1-10 scale
        self.fmea_component = ""     # Optional component name for FMEA-only nodes
        # --- FMEDA attributes ---
        self.fmeda_malfunction = ""
        self.fmeda_safety_goal = ""
        self.fmeda_diag_cov = 0.0
        self.fmeda_fit = 0.0
        self.fmeda_spfm = 0.0
        self.fmeda_lpfm = 0.0
        self.fmeda_fault_type = "permanent"
        self.fmeda_fault_fraction = 0.0
        # FMEDA specific targets if not derived from FTA
        self.fmeda_dc_target = 0.0
        self.fmeda_spfm_target = 0.0
        self.fmeda_lpfm_target = 0.0
        # Reference to a unique failure mode this node represents
        self.failure_mode_ref = None
        # Reference to a fault represented by a basic event
        self.fault_ref = ""
        # Malfunction name for top level events
        self.malfunction = ""
        self.name_readonly = False
        self.product_goal = None
        # Probability values for classical FTA calculations
        self.failure_prob = 0.0
        self.probability = 0.0
        # Formula used to derive probability from FIT rate
        self.prob_formula = "linear"  # linear, exponential, or constant
        # Review status for top events
        self.status = "draft"

    def update_validation_target(self):
        """Recalculate validation target from current risk ratings."""
        self.exposure_given_hb = exposure_to_probability(getattr(self, "exposure", 1))
        self.uncontrollable_given_exposure = controllability_to_probability(getattr(self, "controllability", 1))
        self.severity_given_uncontrollable = severity_to_probability(getattr(self, "severity", 1))
        self.validation_target = derive_validation_target(
            self.acceptance_rate,
            self.exposure_given_hb,
            self.uncontrollable_given_exposure,
            self.severity_given_uncontrollable,
        )
        return self.validation_target

    @property
    def name(self):
        orig = getattr(self, "original", self)
        uid = orig.unique_id if not self.is_primary_instance else self.unique_id
        base_name = self.user_name
        # Avoid repeating the ID if the user_name already matches the default
        if not base_name or base_name == f"Node {uid}":
            return f"Node {uid}"
        return f"Node {uid}: {base_name}"

    def to_dict(self):
        d = {
            "unique_id": self.unique_id,
            "user_name": self.user_name,
            "type": self.node_type,
            "quant_value": self.quant_value,
            "gate_type": self.gate_type,
            "description": self.description,
            "rationale": self.rationale,
            "x": self.x,
            "y": self.y,
            "severity": self.severity,
            "controllability": self.controllability,
            "exposure": self.exposure,
            "input_subtype": self.input_subtype,
            "is_page": self.is_page,
            "is_primary_instance": self.is_primary_instance,
            "safety_goal_description": self.safety_goal_description,
            "safety_goal_asil": self.safety_goal_asil,
            "safe_state": self.safe_state,
            "ftti": self.ftti,
            "validation_target": self.validation_target,
            "validation_desc": self.validation_desc,
            "mission_profile": self.mission_profile,
            "acceptance_criteria": self.acceptance_criteria,
            "acceptance_rate": self.acceptance_rate,
            "operational_hours_on": self.operational_hours_on,
            "exposure_given_hb": self.exposure_given_hb,
            "uncontrollable_given_exposure": self.uncontrollable_given_exposure,
            "severity_given_uncontrollable": self.severity_given_uncontrollable,
            "status": self.status,
            "approved": self.approved,
            "sg_dc_target": self.sg_dc_target,
            "sg_spfm_target": self.sg_spfm_target,
            "sg_lpfm_target": self.sg_lpfm_target,
            "fmea_effect": self.fmea_effect,
            "fmea_cause": self.fmea_cause,
            "fmea_severity": self.fmea_severity,
            "fmea_occurrence": self.fmea_occurrence,
            "fmea_detection": self.fmea_detection,
            "fmea_component": self.fmea_component,
            "fmeda_malfunction": self.fmeda_malfunction,
            "fmeda_safety_goal": self.fmeda_safety_goal,
            "fmeda_diag_cov": self.fmeda_diag_cov,
            "fmeda_fit": self.fmeda_fit,
            "fmeda_spfm": self.fmeda_spfm,
            "fmeda_lpfm": self.fmeda_lpfm,
            "fmeda_fault_type": self.fmeda_fault_type,
            "fmeda_fault_fraction": self.fmeda_fault_fraction,
            "fmeda_dc_target": self.fmeda_dc_target,
            "fmeda_spfm_target": self.fmeda_spfm_target,
            "fmeda_lpfm_target": self.fmeda_lpfm_target,
            "failure_mode_ref": self.failure_mode_ref,
            "fault_ref": self.fault_ref,
            "malfunction": self.malfunction,
            # Save the safety requirements list (which now includes custom_id)
            "safety_requirements": self.safety_requirements,
            "failure_prob": self.failure_prob,
            "probability": self.probability,
            "prob_formula": self.prob_formula,
            "status": self.status,
            "product_goal_name": self.product_goal.get("name") if getattr(self, "product_goal", None) else "",
            "name_readonly": self.name_readonly,
            "children": [child.to_dict() for child in self.children]
        }
        if not self.is_primary_instance and self.original and (self.original.unique_id != self.unique_id):
            d["original_id"] = self.original.unique_id
        return d

    @staticmethod
    def from_dict(data, parent=None):
        node = FaultTreeNode.__new__(FaultTreeNode)
        node.user_name = data.get("user_name", "")
        node.node_type = data.get("type", "")
        node.children = [FaultTreeNode.from_dict(child_data, parent=node) for child_data in data.get("children", [])]
        node.parents = []
        if parent is not None:
            node.parents.append(parent)
        node.quant_value = data.get("quant_value")
        node.gate_type = data.get("gate_type", "AND")
        node.description = data.get("description", "")
        node.rationale = data.get("rationale", "")
        node.x = data.get("x", 50)
        node.y = data.get("y", 50)
        node.severity = data.get("severity", 1) if node.node_type.upper() == "TOP EVENT" else None
        node.controllability = data.get("controllability", 1) if node.node_type.upper() == "TOP EVENT" else None
        node.exposure = data.get("exposure", 1) if node.node_type.upper() == "TOP EVENT" else None
        node.input_subtype = data.get("input_subtype", None)
        node.is_page = boolify(data.get("is_page", False), False)
        node.is_primary_instance = boolify(data.get("is_primary_instance", True), True)
        node.safety_goal_description = data.get("safety_goal_description", "")
        node.safety_goal_asil = data.get("safety_goal_asil", "")
        node.safe_state = data.get("safe_state", "")
        node.ftti = data.get("ftti", "")
        node.validation_target = data.get("validation_target", 1.0)
        node.validation_desc = data.get("validation_desc", "")
        node.mission_profile = data.get("mission_profile", "")
        node.acceptance_criteria = data.get("acceptance_criteria", "")
        node.acceptance_rate = data.get("acceptance_rate", 0.0)
        node.operational_hours_on = data.get("operational_hours_on", 0.0)
        node.exposure_given_hb = data.get("exposure_given_hb", 1.0)
        node.uncontrollable_given_exposure = data.get("uncontrollable_given_exposure", 1.0)
        node.severity_given_uncontrollable = data.get("severity_given_uncontrollable", 1.0)
        node.status = data.get("status", "draft")
        node.approved = data.get("approved", False)
        node.sg_dc_target = data.get("sg_dc_target", 0.0)
        node.sg_spfm_target = data.get("sg_spfm_target", 0.0)
        node.sg_lpfm_target = data.get("sg_lpfm_target", 0.0)
        node.fmea_effect = data.get("fmea_effect", "")
        node.fmea_cause = data.get("fmea_cause", "")
        node.fmea_severity = data.get("fmea_severity", 1)
        node.fmea_occurrence = data.get("fmea_occurrence", 1)
        node.fmea_detection = data.get("fmea_detection", 1)
        node.fmea_component = data.get("fmea_component", "")
        node.fmeda_malfunction = data.get("fmeda_malfunction", "")
        node.fmeda_safety_goal = data.get("fmeda_safety_goal", "")
        node.fmeda_diag_cov = data.get("fmeda_diag_cov", 0.0)
        node.fmeda_fit = data.get("fmeda_fit", 0.0)
        node.fmeda_spfm = data.get("fmeda_spfm", 0.0)
        node.fmeda_lpfm = data.get("fmeda_lpfm", 0.0)
        node.fmeda_fault_type = data.get("fmeda_fault_type", "permanent")
        node.fmeda_fault_fraction = data.get("fmeda_fault_fraction", 0.0)
        node.fmeda_dc_target = data.get("fmeda_dc_target", 0.0)
        node.fmeda_spfm_target = data.get("fmeda_spfm_target", 0.0)
        node.fmeda_lpfm_target = data.get("fmeda_lpfm_target", 0.0)
        node.failure_mode_ref = data.get("failure_mode_ref")
        node.fault_ref = data.get("fault_ref", "")
        node.malfunction = data.get("malfunction", "")
        # NEW: Load safety_requirements (or default to empty list)
        node.safety_requirements = data.get("safety_requirements", [])
        node.failure_prob = data.get("failure_prob", 0.0)
        node.probability = data.get("probability", 0.0)
        node.prob_formula = data.get("prob_formula", "linear")
        node.status = data.get("status", "draft")
        node.name_readonly = data.get("name_readonly", False)
        pg_name = data.get("product_goal_name", "")
        node.product_goal = {"name": pg_name} if pg_name else None
        node.display_label = ""
        node.equation = ""
        node.detailed_equation = ""
        if "unique_id" in data:
            node.unique_id = data["unique_id"]
        else:
            from AutoML import AutoML_Helper
            node.unique_id = AutoML_Helper.get_next_unique_id()
        if not node.is_primary_instance and "original_id" in data:
            node._original_id = data["original_id"]
        else:
            node._original_id = None
        return node

    @classmethod
    def create_basic_event_from_fmea(cls, parent_node, selected):
        """Create and attach a basic event node from an FMEA/FMEDA entry.

        Parameters
        ----------
        parent_node:
            The :class:`FaultTreeNode` under which the new event will be
            attached.
        selected:
            An object exposing a ``to_dict`` method and optional
            ``unique_id`` attribute representing the failure mode.

        Returns
        -------
        FaultTreeNode
            The newly created node.
        """

        data = selected.to_dict()
        data.pop("unique_id", None)
        data["children"] = []
        new_node = cls.from_dict(data, parent_node)
        if hasattr(selected, "unique_id"):
            new_node.failure_mode_ref = selected.unique_id
        parent_node.children.append(new_node)
        new_node.parents.append(parent_node)
        return new_node

    # ------------------------------------------------------------------
    def clone(self, parent=None):
        """Return a copy of this node referencing the same original."""
        import copy
        from AutoML import AutoML_Helper

        clone = copy.deepcopy(self)
        clone.unique_id = AutoML_Helper.get_next_unique_id()
        clone.children = []
        clone.parents = []
        clone.is_primary_instance = False
        clone.original = self.original if getattr(self, "original", None) else self
        if parent is not None:
            clone.parents.append(parent)
            parent.children.append(clone)
        return clone

    @staticmethod
    def add_basic_event_from_fmea(core):
        """Add a basic event selected from FMEA/FMEDA entries."""
        from gui.controls import messagebox
        from gui.dialogs.select_base_event_dialog import SelectBaseEventDialog

        core.push_undo_state()
        events = list(core.fmea_entries)
        for doc in core.fmeas:
            events.extend(doc.get("entries", []))
        for doc in core.fmedas:
            events.extend(doc.get("entries", []))
        if not events:
            messagebox.showinfo(
                "No Failure Modes",
                "No FMEA or FMEDA failure modes available.",
            )
            return
        dialog = SelectBaseEventDialog(core.root, events)
        selected = dialog.selected
        if not selected:
            return
        if core.selected_node:
            parent_node = core.selected_node
            if not parent_node.is_primary_instance:
                messagebox.showwarning(
                    "Invalid Operation",
                    "Cannot add to a clone node. Select the original.",
                )
                return
        else:
            sel = core.analysis_tree.selection()
            if not sel:
                messagebox.showwarning(
                    "No selection", "Select a parent node to paste into."
                )
                return
            try:
                node_id = int(core.analysis_tree.item(sel[0], "tags")[0])
            except Exception:
                return

def add_failure_mode(
    core,
    win,
    basic_events,
    entries,
    selected_libs,
    refresh_tree,
    fmea=None,
    fmeda=False,
):
    """Add failure modes to an FMEA or FMEDA table.

    Parameters
    ----------
    core:
        The application core invoking this helper.
    win:
        Parent window for dialogs.
    basic_events:
        Available basic events to choose from.
    entries:
        Current FMEA/FMeda entry list to append to.
    selected_libs:
        Libraries providing failure mechanisms.
    refresh_tree:
        Callback to update the displayed tree after modifications.
    fmea:
        Optional FMEA document being edited.
    fmeda:
        Flag indicating FMEDA mode.
    """

    from gui.dialogs.select_base_event_dialog import SelectBaseEventDialog
    from gui.dialogs.fmea_row_dialog import FMEARowDialog

    dialog = SelectBaseEventDialog(win, basic_events, allow_new=True)
    node = dialog.selected
    if node == "NEW":
        node = FaultTreeNode("", "Basic Event")
        entries.append(node)
        mechs = []
        for lib in selected_libs:
            mechs.extend(lib.mechanisms)
        comp_name = getattr(node, "fmea_component", "")
        is_passive = any(
            c.name == comp_name and c.is_passive for c in core.reliability_components
        )
        FMEARowDialog(
            win,
            node,
            core,
            entries,
            mechanisms=mechs,
            hide_diagnostics=is_passive,
            is_fmeda=fmeda,
        )
    elif node:
        if node.parents:
            parent_id = node.parents[0].unique_id
            related = [
                be
                for be in basic_events
                if be.parents and be.parents[0].unique_id == parent_id
            ]
        else:
            comp = getattr(node, "fmea_component", "")
            related = [
                be
                for be in basic_events
                if not be.parents and getattr(be, "fmea_component", "") == comp
            ]
        if node not in related:
            related.append(node)
        existing_ids = {be.unique_id for be in entries}
        for be in related:
            if be.unique_id not in existing_ids:
                entries.append(be)
                existing_ids.add(be.unique_id)
            mechs = []
            for lib in selected_libs:
                mechs.extend(lib.mechanisms)
            comp_name = core.get_component_name_for_node(be)
            is_passive = any(
                c.name == comp_name and c.is_passive for c in core.reliability_components
            )
            FMEARowDialog(
                win,
                be,
                core,
                entries,
                mechanisms=mechs,
                hide_diagnostics=is_passive,
                is_fmeda=fmeda,
            )
    refresh_tree()
    if fmea is not None:
        core.lifecycle_ui.touch_doc(fmea)

def refresh_tree(app, tree):
    """Populate a Treeview with the application's top events."""
    if __package__ and __package__.startswith("AutoML"):
        from AutoML.config.automl_constants import PMHF_TARGETS
    else:  # pragma: no cover - script context
        from config.automl_constants import PMHF_TARGETS

    tree.delete(*tree.get_children())
    for sg in app.top_events:
        name = sg.safety_goal_description or (sg.user_name or f"SG {sg.unique_id}")
        sg.safety_goal_asil = app.get_hara_goal_asil(name)
        pmhf_target = PMHF_TARGETS.get(sg.safety_goal_asil, 1.0)
        tree.insert(
            "",
            "end",
            iid=sg.unique_id,
            values=[
                sg.user_name or f"SG {sg.unique_id}",
                sg.safety_goal_asil,
                f"{pmhf_target:.2e}",
                sg.safe_state,
                getattr(sg, "ftti", ""),
                str(getattr(sg, "acceptance_rate", "")),
                getattr(sg, "operational_hours_on", ""),
                getattr(sg, "validation_target", ""),
                getattr(sg, "mission_profile", ""),
                getattr(sg, "validation_desc", ""),
                getattr(sg, "acceptance_criteria", ""),
                sg.safety_goal_description,
            ],
        )


def _resolve_parent_node(app, parent_node):
    """Return a valid parent node or ``None`` if selection is invalid."""
    if parent_node is None:
        sel = app.analysis_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Select a parent node from the tree.")
            return None
        try:
            node_id = int(app.analysis_tree.item(sel[0], "tags")[0])
        except Exception:  # noqa: BLE001 - broad to guard against malformed selections
            messagebox.showwarning("No selection", "Select a parent node from the tree.")
            return None
        parent_node = app.find_node_by_id_all(node_id)
    return parent_node

ALLOWED_NODE_TYPES = {
    "FTA": {"GATE", "BASIC EVENT"},
    "CTA": {"TRIGGERING CONDITION", "FUNCTIONAL INSUFFICIENCY"},
    "PAA": {"CONFIDENCE LEVEL", "ROBUSTNESS SCORE"},
}

def _infer_diagram_mode(app, event_upper: str) -> str:
    """Infer diagram mode, allowing FTA/CTA nodes when active mode is PAA."""

    canvas_mode = getattr(getattr(app, "canvas", None), "diagram_mode", None)
    mode = (canvas_mode or getattr(app, "diagram_mode", "FTA")).upper()
    if mode != "PAA":  # enforce gating when not in PAA mode
        return mode
    for candidate, types in ALLOWED_NODE_TYPES.items():
        if candidate != "PAA" and event_upper in types:
            return candidate
    return mode

def add_node_of_type(app, event_type):
    """Attach a new ``FaultTreeNode`` of ``event_type`` under the current selection."""

    app.push_undo_state()
    event_upper = event_type.upper()
    diag_mode = _infer_diagram_mode(app, event_upper)

    if event_upper not in ALLOWED_NODE_TYPES.get(diag_mode, set()):
        msg = (
            f"Only {allowed_nodes} nodes are allowed in Prototype Assurance Analysis."
            if diag_mode == "PAA"
            else f"Node type '{event_type}' is not allowed in {diag_mode} diagrams."
        )
        messagebox.showwarning("Invalid", msg)
        return

    parent_node = app.selected_node
    if parent_node and not parent_node.is_primary_instance:
        messagebox.showwarning(
            "Invalid Operation",
            "Cannot add new elements to a clone node.\nPlease select the original node instead.",
        )
        return

    parent_node = _resolve_parent_node(app, parent_node)
    if not parent_node:
        return

    if parent_node.node_type.upper() in {"CONFIDENCE LEVEL", "ROBUSTNESS SCORE", "BASIC EVENT"}:
        messagebox.showwarning("Invalid", "Base events cannot have children.")
        return

    new_node = FaultTreeNode("", event_type, parent_node)
    new_node.x = parent_node.x
    new_node.y = parent_node.y + 100
    parent_node.children.append(new_node)
    new_node.parents.append(parent_node)
    app.update_views()
    return new_node
