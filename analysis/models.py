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

# Author: Miguel Marina <karel.capek.robotics@gmail.com>
from dataclasses import dataclass, field, asdict
import datetime
from typing import Optional
from analysis.user_config import CURRENT_USER_NAME, CURRENT_USER_EMAIL


@dataclass
class Metadata:
    """Track creation and modification info."""

    created: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    author: str = field(default_factory=lambda: CURRENT_USER_NAME)
    author_email: str = field(default_factory=lambda: CURRENT_USER_EMAIL)
    modified: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    modified_by: str = field(default_factory=lambda: CURRENT_USER_NAME)
    modified_by_email: str = field(default_factory=lambda: CURRENT_USER_EMAIL)

@dataclass
class MissionProfile:
    name: str
    tau_on: float = 0.0
    tau_off: float = 0.0
    board_temp: float = 25.0
    board_temp_min: float = 25.0
    board_temp_max: float = 25.0
    ambient_temp: float = 25.0
    ambient_temp_min: float = 25.0
    ambient_temp_max: float = 25.0
    humidity: float = 50.0
    duty_cycle: float = 1.0
    notes: str = ""

    @property
    def temperature(self) -> float:
        """Alias for backward compatibility (returns board temperature)."""
        return self.board_temp

    @temperature.setter
    def temperature(self, value: float) -> None:
        self.board_temp = value


    @property
    def tau(self) -> float:
        """Return the total TAU for backward compatibility."""
        return self.tau_on + self.tau_off

@dataclass
class ReliabilityComponent:
    name: str
    comp_type: str
    quantity: int = 1
    attributes: dict = field(default_factory=dict)
    qualification: str = ""
    fit: float = 0.0
    is_passive: bool = False
    sub_boms: list = field(default_factory=list)

    def __hash__(self) -> int:
        """Allow instances to be used as dictionary keys based on identity."""
        return id(self)

QUALIFICATIONS = [
    "AEC-Q100",
    "AEC-Q101",
    "AEC-Q200",
    "IECQ",
    "MIL-STD-883",
    "MIL-PRF-38534",
    "MIL-PRF-38535",
    "Space",
    "None",
]

# Multiplicative FIT adjustment factors applied to passive components based on
# their qualification certificate.  Values below 1.0 decrease the calculated
# FIT rate.  Active components currently use a factor of ``1.0`` regardless of
# qualification.
PASSIVE_QUAL_FACTORS = {
    "AEC-Q200": 0.8,
    "IECQ": 0.9,
    "MIL-STD-883": 0.85,
    "MIL-PRF-38534": 0.85,
    "MIL-PRF-38535": 0.85,
    "Space": 0.75,
    "AEC-Q100": 1.0,
    "AEC-Q101": 1.0,
    "None": 1.0,
}


def safe_float(value, default=0.0):
    """Safely convert ``value`` to ``float`` returning ``default`` on error."""
    try:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return default
        return float(value)
    except (TypeError, ValueError):
        return default

@dataclass
class ReliabilityAnalysis:
    """Store the results of a reliability calculation including the BOM."""

    name: str
    standard: str
    profile: str
    components: list
    total_fit: float
    spfm: float
    lpfm: float
    dc: float

@dataclass
class HazopEntry:
    function: str
    malfunction: str
    mtype: str
    scenario: str
    conditions: str
    hazard: str
    safety: bool
    rationale: str
    covered: bool
    covered_by: str
    component: str = ""

    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        """Return a serialisable representation of this HAZOP entry."""

        data = asdict(self)
        data["safety"] = bool(self.safety)
        data["covered"] = bool(self.covered)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "HazopEntry":
        """Construct a HAZOP entry from *data* mapping."""

        return cls(
            function=data.get("function", ""),
            malfunction=data.get("malfunction", ""),
            mtype=data.get("mtype", ""),
            scenario=data.get("scenario", ""),
            conditions=data.get("conditions", ""),
            hazard=data.get("hazard", ""),
            safety=bool(data.get("safety", False)),
            rationale=data.get("rationale", ""),
            covered=bool(data.get("covered", False)),
            covered_by=data.get("covered_by", ""),
            component=data.get("component", ""),
        )

@dataclass
class HaraEntry:
    malfunction: str
    hazard: str
    scenario: str
    severity: int
    sev_rationale: str
    controllability: int
    cont_rationale: str
    exposure: int
    exp_rationale: str
    asil: str
    safety_goal: str
    cyber: Optional["CyberRiskEntry"] = None

@dataclass
class HazopDoc:
    """Container for a HAZOP with a name and list of entries."""
    name: str
    entries: list
    meta: Metadata = field(default_factory=Metadata)

    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        """Return a serialisable representation of this HAZOP document."""

        return {
            "name": self.name,
            "entries": [entry.to_dict() for entry in self.entries],
            "meta": asdict(self.meta),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HazopDoc":
        """Recreate a HAZOP document from *data* mapping."""

        entries = [HazopEntry.from_dict(item) for item in data.get("entries", [])]
        meta = Metadata(**data.get("meta", {})) if data.get("meta") else Metadata()
        return cls(name=data.get("name", ""), entries=entries, meta=meta)

@dataclass
class HaraDoc:
    """Container for a HARA derived from one or more HAZOPs."""
    name: str
    hazops: list
    entries: list
    approved: bool = False
    status: str = "draft"
    meta: Metadata = field(default_factory=Metadata)
    stpa: str = ""
    threat: str = ""
    fi2tc: str = ""
    tc2fi: str = ""

@dataclass
class StpaEntry:
    action: str
    not_providing: str
    providing: str
    incorrect_timing: str
    stopped_too_soon: str
    safety_constraints: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        """Return a serialisable representation of this STPA entry."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "StpaEntry":
        """Create an STPA entry from *data* mapping."""
        return cls(
            data.get("action", ""),
            data.get("not_providing", ""),
            data.get("providing", ""),
            data.get("incorrect_timing", ""),
            data.get("stopped_too_soon", ""),
            list(data.get("safety_constraints", [])),
        )


@dataclass
class StpaDoc:
    name: str
    diagram: str
    entries: list[StpaEntry]
    meta: Metadata = field(default_factory=Metadata)

    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        """Return a serialisable representation of this STPA document."""
        return {
            "name": self.name,
            "diagram": self.diagram,
            "entries": [e.to_dict() for e in self.entries],
            "meta": asdict(self.meta),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StpaDoc":
        """Reconstruct an STPA document from *data* mapping."""
        return cls(
            name=data.get("name", ""),
            diagram=data.get("diagram", ""),
            entries=[StpaEntry.from_dict(e) for e in data.get("entries", [])],
            meta=Metadata(**data.get("meta", {})),
        )

@dataclass
class FI2TCDoc:
    """Container for an FI2TC analysis."""
    name: str
    entries: list
    meta: Metadata = field(default_factory=Metadata)

@dataclass
class TC2FIDoc:
    """Container for a TC2FI analysis."""
    name: str
    entries: list
    meta: Metadata = field(default_factory=Metadata)


@dataclass
class DiagnosticMechanism:
    """Diagnostic mechanism such as those from ISO 26262 Annex D."""

    name: str
    coverage: float
    description: str = ""
    detail: str = ""
    requirement: str = ""


@dataclass
class MechanismLibrary:
    """Collection of diagnostic mechanisms."""

    name: str
    mechanisms: list = field(default_factory=list)


@dataclass
class CybersecurityGoal:
    """Cybersecurity goal with linked risk assessments and CAL."""

    goal_id: str
    description: str
    cal: str = "CAL1"
    risk_assessments: list = field(default_factory=list)

    def compute_cal(self) -> None:
        """Compute CAL as highest level among linked risk assessments."""
        order = {level: idx for idx, level in enumerate(CAL_LEVEL_OPTIONS, start=1)}
        highest = CAL_LEVEL_OPTIONS[0]
        for ra in self.risk_assessments:
            cal = getattr(ra, "cal", None)
            if cal is None and isinstance(ra, dict):
                cal = ra.get("cal")
            if cal in order and order[cal] > order.get(highest, 0):
                highest = cal
        self.cal = highest


@dataclass
class AttackPath:
    """Single attack path description."""

    description: str


@dataclass
class ThreatScenario:
    """Threat scenario organized by STRIDE category."""

    stride: str
    scenario: str
    attack_paths: list[AttackPath] = field(default_factory=list)


@dataclass
class DamageScenario:
    """Potential damage scenario for a given asset/function."""

    scenario: str
    dtype: str = ""
    threats: list[ThreatScenario] = field(default_factory=list)


@dataclass
class FunctionThreat:
    """Link a function to its damage scenarios."""

    name: str
    damage_scenarios: list[DamageScenario] = field(default_factory=list)


@dataclass
class ThreatEntry:
    """Single row in a threat analysis table."""

    asset: str
    functions: list[FunctionThreat] = field(default_factory=list)


@dataclass
class ThreatDoc:
    """Container for a threat analysis document."""

    name: str
    diagram: str
    entries: list[ThreatEntry]
    meta: Metadata = field(default_factory=Metadata)


# ---------------------------------------------------------------------------
# Cybersecurity Risk Assessment
# ---------------------------------------------------------------------------
IMPACT_LEVELS = ["Negligible", "Moderate", "Major", "Severe"]

# Mapping of feasibility and impact severity to overall risk level
RISK_LEVEL_TABLE = {
    "High": {
        "Severe": "High",
        "Major": "High",
        "Moderate": "Medium",
        "Negligible": "Low",
    },
    "Medium": {
        "Severe": "High",
        "Major": "Medium",
        "Moderate": "Low",
        "Negligible": "Low",
    },
    "Low": {
        "Severe": "Medium",
        "Major": "Low",
        "Moderate": "Low",
        "Negligible": "Low",
    },
}

# Mapping of impact severity and attack vector to Cybersecurity Assurance Level
CAL_TABLE = {
    "Physical-Local": {"Severe": "CAL2", "Major": "CAL1", "Moderate": "CAL1"},
    "Adjacent Network": {"Severe": "CAL3", "Major": "CAL2", "Moderate": "CAL1"},
    "Network-Remote": {"Severe": "CAL4", "Major": "CAL3", "Moderate": "CAL2"},
}


@dataclass
class CyberRiskEntry:
    """Store cybersecurity risk assessment values for a threat scenario."""

    damage_scenario: str
    threat_scenario: str
    attack_vector: str
    feasibility: str
    financial_impact: str
    safety_impact: str
    operational_impact: str
    privacy_impact: str
    cybersecurity_goal: str = ""
    attack_paths: list = field(default_factory=list)
    overall_impact: str = field(init=False)
    risk_level: str = field(init=False)
    cal: str = field(init=False)

    def __post_init__(self) -> None:
        self.overall_impact = self.compute_overall_impact()
        self.risk_level = self.compute_risk_level()
        self.cal = self.compute_cal()

    def compute_overall_impact(self) -> str:
        """Return the highest impact among all impact categories."""
        order = {name: idx for idx, name in enumerate(IMPACT_LEVELS)}
        impacts = [
            self.financial_impact,
            self.safety_impact,
            self.operational_impact,
            self.privacy_impact,
        ]
        return max(impacts, key=lambda x: order.get(x, 0))

    def compute_risk_level(self) -> str:
        """Compute overall risk level from feasibility and impact severity."""
        table = RISK_LEVEL_TABLE.get(self.feasibility, {})
        return table.get(self.overall_impact, "")

    def compute_cal(self) -> str:
        """Determine CAL from overall impact and attack vector."""
        if self.attack_vector in ("Physical", "Local"):
            col = "Physical-Local"
        elif self.attack_vector == "Adjacent":
            col = "Adjacent Network"
        else:
            col = "Network-Remote"
        return CAL_TABLE.get(col, {}).get(self.overall_impact, "")

COMPONENT_ATTR_TEMPLATES = {
    "capacitor": {
        "dielectric": ["ceramic", "electrolytic", "tantalum"],
        "capacitance_uF": "",
        "voltage_V": "",
        "esr_ohm": "",
        "tolerance_pct": "",
    },
    "resistor": {
        "resistance_ohm": "",
        "power_W": "",
        "tolerance_pct": "",
    },
    "inductor": {
        "inductance_H": "",
        "current_A": "",
        "saturation_A": "",
    },
    "diode": {
        "type": ["standard", "zener", "schottky"],
        "reverse_V": "",
        "forward_current_A": "",
        "forward_voltage_V": "",
        "power_W": "",
        "surge_current_A": "",
    },
    "transistor": {
        "transistor_type": ["BJT", "MOSFET"],
        "pins": "",
        "voltage_V": "",
        "current_A": "",
        "gain_hfe": "",
        "rds_on_mohm": "",
        "gate_charge_nC": "",
    },
    "ic": {
        "type": ["digital", "analog", "mcu"],
        "pins": "",
        "transistors": "",
    },
    "connector": {"pins": ""},
    "relay": {"cycles": "", "current_A": "", "voltage_V": ""},
    "switch": {"cycles": "", "current_A": "", "voltage_V": ""},
}

RELIABILITY_MODELS = {
    "IEC 62380": {
        "capacitor": {
            "text": "Base*(1+T/100)*Duty*(1+V/100)",
            "formula": lambda a, mp: (0.02 if a.get("dielectric", "ceramic") == "ceramic" else 0.04)
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * (1 + safe_float(a.get("voltage_V", 0)) / 100.0)
            * mp.duty_cycle,
        },
        "resistor": {
            "text": "0.005*(1+T/100)*Duty*(1+P/10)",
            "formula": lambda a, mp: 0.005
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * (1 + safe_float(a.get("power_W", 0)) / 10.0)
            * mp.duty_cycle,
        },
        "inductor": {
            "text": "0.004*(1+T/100)*Duty*(1+I/10)",
            "formula": lambda a, mp: 0.004
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * (1 + safe_float(a.get("current_A", 0)) / 10.0)
            * mp.duty_cycle,
        },
        "diode": {
            "text": "0.008*(1+T/100)*Duty*(1+VR/100)",
            "formula": lambda a, mp: 0.008
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * (1 + safe_float(a.get("reverse_V", 0)) / 100.0)
            * mp.duty_cycle,
        },
        "transistor": {
            "text": "Base*(1+T/100)*Duty*(1+I/10) (base=0.01 BJT, 0.012 MOSFET)",
            "formula": lambda a, mp: (0.01 if a.get("transistor_type", "BJT") == "BJT" else 0.012)
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * (1 + safe_float(a.get("current_A", 0)) / 10.0)
            * mp.duty_cycle,
        },
        "ic": {
            "text": "Base*(1+T/100)*Duty*(1+pins/1000)*(1+trans/1e6) (base=0.04 analog, 0.03 digital, 0.05 MCU)",
            "formula": lambda a, mp: (0.04 if a.get("type", "digital") == "analog" else 0.05 if a.get("type") == "mcu" else 0.03)
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * mp.duty_cycle
            * (1 + safe_float(a.get("pins", 0)) / 1000.0)
            * (1 + safe_float(a.get("transistors", 0)) / 1_000_000.0),
        },
        "connector": {
            "text": "0.002*(1+T/100)*Duty*(1+pins/100)",
            "formula": lambda a, mp: 0.002
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * (1 + safe_float(a.get("pins", 0)) / 100.0)
            * mp.duty_cycle,
        },
        "relay": {
            "text": "0.03*(1+T/100)*Duty*(cycles/1e6)*(1+I/10)",
            "formula": lambda a, mp: 0.03
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * mp.duty_cycle
            * (safe_float(a.get("cycles", 1e6)) / 1e6)
            * (1 + safe_float(a.get("current_A", 0)) / 10.0),
        },
        "switch": {
            "text": "0.02*(1+T/100)*Duty*(cycles/1e6)*(1+I/10)",
            "formula": lambda a, mp: 0.02
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * mp.duty_cycle
            * (safe_float(a.get("cycles", 1e6)) / 1e6)
            * (1 + safe_float(a.get("current_A", 0)) / 10.0),
        },
    },
    "SN 29500": {
        "capacitor": {
            "text": "0.03*(1+T/100)*Duty*(1+V/100)",
            "formula": lambda a, mp: 0.03
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * (1 + safe_float(a.get("voltage_V", 0)) / 100.0)
            * mp.duty_cycle,
        },
        "resistor": {
            "text": "0.006*(1+T/100)*Duty*(1+P/10)",
            "formula": lambda a, mp: 0.006
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * (1 + safe_float(a.get("power_W", 0)) / 10.0)
            * mp.duty_cycle,
        },
        "inductor": {
            "text": "0.005*(1+T/100)*Duty*(1+I/10)",
            "formula": lambda a, mp: 0.005
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * (1 + safe_float(a.get("current_A", 0)) / 10.0)
            * mp.duty_cycle,
        },
        "diode": {
            "text": "0.009*(1+T/100)*Duty*(1+VR/100)",
            "formula": lambda a, mp: 0.009
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * (1 + safe_float(a.get("reverse_V", 0)) / 100.0)
            * mp.duty_cycle,
        },
        "transistor": {
            "text": "Base*(1+T/100)*Duty*(1+I/10) (base=0.012 BJT, 0.014 MOSFET)",
            "formula": lambda a, mp: (0.012 if a.get("transistor_type", "BJT") == "BJT" else 0.014)
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * (1 + safe_float(a.get("current_A", 0)) / 10.0)
            * mp.duty_cycle,
        },
        "ic": {
            "text": "Base*(1+T/100)*Duty*(1+pins/1000)*(1+trans/1e6) (base=0.05 analog, 0.04 digital, 0.06 MCU)",
            "formula": lambda a, mp: (0.05 if a.get("type", "digital") == "analog" else 0.06 if a.get("type") == "mcu" else 0.04)
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * mp.duty_cycle
            * (1 + safe_float(a.get("pins", 0)) / 1000.0)
            * (1 + safe_float(a.get("transistors", 0)) / 1_000_000.0),
        },
        "connector": {
            "text": "0.003*(1+T/100)*Duty*(1+pins/100)",
            "formula": lambda a, mp: 0.003
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * (1 + safe_float(a.get("pins", 0)) / 100.0)
            * mp.duty_cycle,
        },
        "relay": {
            "text": "0.035*(1+T/100)*Duty*(cycles/1e6)*(1+I/10)",
            "formula": lambda a, mp: 0.035
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * mp.duty_cycle
            * (safe_float(a.get("cycles", 1e6)) / 1e6)
            * (1 + safe_float(a.get("current_A", 0)) / 10.0),
        },
        "switch": {
            "text": "0.025*(1+T/100)*Duty*(cycles/1e6)*(1+I/10)",
            "formula": lambda a, mp: 0.025
            * (1 + max(mp.board_temp_max, mp.ambient_temp_max) / 100.0)
            * mp.duty_cycle
            * (safe_float(a.get("cycles", 1e6)) / 1e6)
            * (1 + safe_float(a.get("current_A", 0)) / 10.0),
        },
    },
}

global_requirements = {}


def ensure_requirement_defaults(req: dict) -> dict:
    """Ensure a requirement dictionary has mandatory default fields.

    Parameters
    ----------
    req:
        Requirement dictionary to normalise.

    Returns
    -------
    dict
        The updated requirement dictionary with default fields present.

    Notes
    -----
    Each requirement now carries a ``traces`` list capturing diagram or
    element identifiers that reference the requirement.  When older
    models are loaded the field may be missing; this helper guarantees the
    key exists so callers can rely on it.  Requirements may also be
    associated with a lifecycle ``phase``.  Older models without this
    information should default to ``None`` so they remain visible
    globally.
    """

    req.setdefault("traces", [])
    req.setdefault("phase", None)
    return req

# Requirement type options used throughout the GUI when creating or
# editing safety requirements.  The list retains the original "vehicle"
# and "operational" categories and adds new ones for functional,
# technical and AI safety as well as functional modifications.
# Updated requirement categories including functional, technical and AI
# safety, functional modifications and cybersecurity.
REQUIREMENT_TYPE_OPTIONS = [
    "vehicle",
    "operational",
    "operational safety",
    "functional safety",
    "technical safety",
    "AI safety",
    "functional modification",
    "cybersecurity",
    "production",
    "service",
    "decommissioning",
    "product",
    "legal",
    "organizational",
]

# Work product names corresponding to each requirement category. These are used
# when declaring governance work products so each requirement type can be
# managed individually.
REQUIREMENT_WORK_PRODUCTS = [
    "Requirement Specification",
    "Vehicle Requirement Specification",
    "Operational Requirement Specification",
    "Operational Safety Requirement Specification",
    "Functional Safety Requirement Specification",
    "Technical Safety Requirement Specification",
    "AI Safety Requirement Specification",
    "Functional Modification Requirement Specification",
    "Cybersecurity Requirement Specification",
    "Production Requirement Specification",
    "Service Requirement Specification",
    "Decommissioning Requirement Specification",
    "Product Requirement Specification",
    "Legal Requirement Specification",
    "Organizational Requirement Specification",
]
# ASIL level options including decomposition levels
ASIL_LEVEL_OPTIONS = [
    "QM", "QM(A)", "QM(B)", "QM(C)", "QM(D)",
    "A", "A(B)", "B", "B(C)", "C", "C(D)", "D"
]

# Cybersecurity Assurance Levels defined in ISO 21434
CAL_LEVEL_OPTIONS = ["CAL1", "CAL2", "CAL3", "CAL4"]

ASIL_ORDER = {"QM":0, "A":1, "B":2, "C":3, "D":4}
ASIL_TARGETS = {
    "D": {"spfm":0.99, "lpfm":0.90, "dc":0.99},
    "C": {"spfm":0.97, "lpfm":0.90, "dc":0.97},
    "B": {"spfm":0.90, "lpfm":0.60, "dc":0.90},
    "A": {"spfm":0.0, "lpfm":0.0, "dc":0.0},
    "QM": {"spfm":0.0, "lpfm":0.0, "dc":0.0},
}

# Mapping of ASIL decomposition schemes as allowed by ISO 26262. Each
# parent ASIL level maps to a list of two-element tuples representing the
# resulting ASIL assignments for the decomposed requirements.
# Decomposition schemes following ISO 26262 guidance.  Each key is the
# original ASIL level and maps to the allowed pairs for the decomposed
# requirements.  Options marked as ``QM(X)`` indicate decomposition with
# additional justification and analysis for the original level ``X``.
# Decomposition of an ASIL A requirement is not defined.
ASIL_DECOMP_SCHEMES = {
    # Top-level decomposition logic updated per new guidelines
    "D": [
        ("ASIL B(D)", "ASIL B(D)"),
        ("ASIL C(D)", "ASIL QM(D)"),
        ("ASIL A(D)", "ASIL C(D)"),
        ("ASIL B(D)", "ASIL QM(D)"),
    ],
    "C": [
        ("ASIL B(C)", "ASIL A(C)"),
        ("ASIL C(C)", "ASIL QM(C)"),
    ],
    "B": [
        ("ASIL A(B)", "ASIL A(B)"),
        ("ASIL B(B)", "ASIL QM(B)"),
    ],
    "A": [
        ("ASIL A(A)", "ASIL QM(A)"),
    ],
}

# ASIL determination table following the ISO 26262 risk graph used in the HARA
# view. The keys are tuples ``(severity, controllability, exposure)`` using the
# numeric levels 1–3 for severity/controllability and 1–4 for exposure.  The
# mapping below implements the conditions from the HARA specification so that
# ``calc_asil`` returns the correct ASIL value for each combination.
ASIL_TABLE = {
    # Severity 1 rows
    (1, 1, 1): "QM", (1, 1, 2): "QM", (1, 1, 3): "QM", (1, 1, 4): "QM",
    (1, 2, 1): "QM", (1, 2, 2): "QM", (1, 2, 3): "QM", (1, 2, 4): "A",
    (1, 3, 1): "QM", (1, 3, 2): "QM", (1, 3, 3): "QM", (1, 3, 4): "B",

    # Severity 2 rows
    (2, 1, 1): "QM", (2, 1, 2): "QM", (2, 1, 3): "QM", (2, 1, 4): "A",
    (2, 2, 1): "QM", (2, 2, 2): "QM", (2, 2, 3): "A", (2, 2, 4): "B",
    (2, 3, 1): "QM", (2, 3, 2): "A", (2, 3, 3): "B", (2, 3, 4): "C",

    # Severity 3 rows
    (3, 1, 1): "QM", (3, 1, 2): "QM", (3, 1, 3): "A", (3, 1, 4): "B",
    (3, 2, 1): "QM", (3, 2, 2): "A", (3, 2, 3): "B", (3, 2, 4): "C",
    (3, 3, 1): "A", (3, 3, 2): "B", (3, 3, 3): "C", (3, 3, 4): "D",
}

def calc_asil(sev: int, cont: int, expo: int) -> str:
    """Return ASIL based on severity, controllability and exposure."""
    return ASIL_TABLE.get((sev, cont, expo), "QM")


def component_fit_map(components: list) -> dict:
    """Return a mapping of component names to aggregated FIT values.

    The returned FIT values include quantity and recursively handle any
    ``sub_boms`` so nested BOM structures are flattened. Quantities of parent
    components multiply the FIT contribution of their children.
    """

    mapping = {}

    def add(comp, mult=1.0):
        mapping[comp.name] = mapping.get(comp.name, 0.0) + comp.fit * comp.quantity * mult
        for bom in getattr(comp, "sub_boms", []):
            for sub in bom:
                add(sub, mult * comp.quantity)

    for c in components:
        add(c)

    return mapping

