from dataclasses import dataclass, field

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
    """Convert ``value`` to ``float`` returning ``default`` on error."""
    try:
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

@dataclass
class HaraEntry:
    malfunction: str
    hazard: str
    severity: int
    sev_rationale: str
    controllability: int
    cont_rationale: str
    exposure: int
    exp_rationale: str
    asil: str
    safety_goal: str

@dataclass
class HazopDoc:
    """Container for a HAZOP with a name and list of entries."""
    name: str
    entries: list

@dataclass
class HaraDoc:
    """Container for a HARA derived from one or more HAZOPs."""
    name: str
    hazops: list
    entries: list
    approved: bool = False
    status: str = "draft"

@dataclass
class FI2TCDoc:
    """Container for an FI2TC analysis."""
    name: str
    entries: list

@dataclass
class TC2FIDoc:
    """Container for a TC2FI analysis."""
    name: str
    entries: list

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
# ASIL level options including decomposition levels
ASIL_LEVEL_OPTIONS = [
    "QM", "QM(A)", "QM(B)", "QM(C)", "QM(D)",
    "A", "A(B)", "B", "B(C)", "C", "C(D)", "D"
]

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
