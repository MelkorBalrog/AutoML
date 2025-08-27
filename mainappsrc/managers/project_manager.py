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

from __future__ import annotations

"""Project persistence utilities for AutoMLApp."""

from tkinter import filedialog, simpledialog
import tkinter as tk
import datetime
from gui.dialogs.dialog_utils import askstring_fixed
from analysis.utils import (
    EXPOSURE_PROBABILITIES,
    CONTROLLABILITY_PROBABILITIES,
    SEVERITY_PROBABILITIES,
)
from analysis.risk_assessment import boolify
from analysis.user_config import CURRENT_USER_NAME
from analysis.models import (
    MissionProfile,
    ReliabilityComponent,
    ReliabilityAnalysis,
    HazopEntry,
    HazopDoc,
    HaraEntry,
    HaraDoc,
    StpaEntry,
    StpaDoc,
    DiagnosticMechanism,
    MechanismLibrary,
    global_requirements,
    ensure_requirement_defaults,
)
from analysis.safety_management import SafetyManagementToolbox
from mainappsrc.models.gsn import GSNModule, GSNDiagram
from mainappsrc.models.fta.fault_tree_node import FaultTreeNode
from mainappsrc.models.sysml.sysml_repository import SysMLRepository
from mainappsrc.services.config import config_service
from tools.model_loader import model_loader


class ProjectManager:
    """Load and save AutoML projects."""

    def __init__(self, app: "AutoMLApp") -> None:
        self.app = app

    # ------------------------------------------------------------------
    def apply_project_properties(
        self,
        name: str,
        detailed: bool,
        exp_vars: dict[int, tk.Variable],
        ctrl_vars: dict[int, tk.Variable],
        sev_vars: dict[int, tk.Variable],
        freeze: bool,
    ) -> None:
        """Persist updated project properties and refresh probability tables."""
        app = self.app
        app.project_properties["pdf_report_name"] = name
        app.project_properties["pdf_detailed_formulas"] = detailed
        app.project_properties["exposure_probabilities"] = {
            lvl: float(var.get() or 0.0) for lvl, var in exp_vars.items()
        }
        app.project_properties["controllability_probabilities"] = {
            lvl: float(var.get() or 0.0) for lvl, var in ctrl_vars.items()
        }
        app.project_properties["severity_probabilities"] = {
            lvl: float(var.get() or 0.0) for lvl, var in sev_vars.items()
        }
        app.project_properties["freeze_governance_diagrams"] = freeze
        update_probability_tables(
            app.project_properties["exposure_probabilities"],
            app.project_properties["controllability_probabilities"],
            app.project_properties["severity_probabilities"],
        )
        smt = getattr(app, "safety_mgmt_toolbox", None)
        if smt:
            app.governance_manager.freeze_governance_diagrams(freeze)

    # ------------------------------------------------------------------
    def new_model(self) -> None:
        """Reset the application state and start a new model."""
        app = self.app
        mb = app.messagebox
        if app.has_unsaved_changes():
            result = mb.askyesnocancel(
                "Unsaved Changes", "Save changes before starting a new model?"
            )
            if result is None:
                return
            if result:
                self.save_model()
        if hasattr(app, "doc_nb"):
            app.doc_nb.close_all_floating()
        if hasattr(app, "page_diagram") and app.page_diagram is not None:
            app.close_page_diagram()
        for tab_id in list(app.doc_nb.tabs()):
            app.doc_nb._closing_tab = tab_id
            app.doc_nb.event_generate("<<NotebookTabClosed>>")
            if tab_id in app.doc_nb.tabs():
                try:
                    app.doc_nb.forget(tab_id)
                except Exception:
                    pass
        app._reset_fta_state()
        import importlib
        from analysis.risk_assessment import AutoMLHelper as _AutoMLHelper

        automl_mod = importlib.import_module("AutoML")
        helper_cls = getattr(automl_mod, "AutoMLHelper", _AutoMLHelper)
        global AutoML_Helper, unique_node_id_counter
        AutoML_Helper = (
            config_service.automl_helper
        ) = automl_mod.AutoML_Helper = helper_cls()
        unique_node_id_counter = (
            config_service.unique_node_id_counter
        ) = automl_mod.unique_node_id_counter = 1
        SysMLRepository.reset_instance()
        app.zoom = 1.0
        app.diagram_font.config(size=int(8 * app.zoom))
        app.top_events = []
        app.cta_events = []
        app.paa_events = []
        app.root_node = None
        app.selected_node = None
        app.page_history = []
        app.project_properties = {
            "pdf_report_name": "AutoML-Analyzer PDF Report",
            "pdf_detailed_formulas": True,
            "exposure_probabilities": EXPOSURE_PROBABILITIES.copy(),
            "controllability_probabilities": CONTROLLABILITY_PROBABILITIES.copy(),
            "severity_probabilities": SEVERITY_PROBABILITIES.copy(),
        }
        app.probability_reliability.update_probability_tables(
            app.project_properties["exposure_probabilities"],
            app.project_properties["controllability_probabilities"],
            app.project_properties["severity_probabilities"],
        )
        app.apply_model_data({}, ensure_root=False)
        app.undo_manager.clear_history()
        app.analysis_tree.delete(*app.analysis_tree.get_children())
        app.update_views()
        app.set_last_saved_state()
        if app.canvas:
            app.canvas.update()

    # ------------------------------------------------------------------
    def _reset_on_load(self) -> None:
        model_loader.cleanup()
        app = self.app
        if hasattr(app, "doc_nb"):
            app.doc_nb.close_all_floating()
        if getattr(app, "page_diagram", None) is not None:
            app.close_page_diagram()
        for tab_id in list(getattr(app.doc_nb, "tabs", lambda: [])()):
            app.doc_nb._closing_tab = tab_id
            app.doc_nb.event_generate("<<NotebookTabClosed>>")
            if tab_id in getattr(app.doc_nb, "tabs", lambda: [])():
                try:
                    app.doc_nb.forget(tab_id)
                except Exception:
                    pass
        for win in (
            list(getattr(app, "use_case_windows", []))
            + list(getattr(app, "activity_windows", []))
            + list(getattr(app, "block_windows", []))
            + list(getattr(app, "ibd_windows", []))
        ):
            try:
                win.destroy()
            except Exception:
                pass
        app.use_case_windows = []
        app.activity_windows = []
        app.block_windows = []
        app.ibd_windows = []
        import importlib
        from analysis.risk_assessment import AutoMLHelper as _AutoMLHelper

        automl_mod = importlib.import_module("AutoML")
        helper_cls = getattr(automl_mod, "AutoMLHelper", _AutoMLHelper)
        global AutoML_Helper, unique_node_id_counter
        AutoML_Helper = (
            config_service.automl_helper
        ) = automl_mod.AutoML_Helper = helper_cls()
        unique_node_id_counter = (
            config_service.unique_node_id_counter
        ) = automl_mod.unique_node_id_counter = 1
        SysMLRepository.reset_instance()
        app.top_events = []
        app.cta_events = []
        app.paa_events = []
        app.root_node = None
        app.selected_node = None
        app.page_history = []
        app.undo_manager.clear_history()
        if getattr(app, "analysis_tree", None):
            app.analysis_tree.delete(*app.analysis_tree.get_children())
        app._reset_fta_state()

    def _prompt_save_before_load(self):
        message = "You have unsaved changes. Save before loading a project?"
        return self.app.messagebox.askyesnocancel("Load Model", message)

    # ------------------------------------------------------------------
    def save_model(self) -> None:
        app = self.app
        mb = app.messagebox
        path = filedialog.asksaveasfilename(
            defaultextension=".autml",
            filetypes=[("AutoML Project", "*.autml"), ("JSON", "*.json")],
        )
        if not path:
            return
        try:
            from cryptography.fernet import Fernet  # type: ignore
        except Exception:
            import subprocess, sys
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "cryptography"])
                from cryptography.fernet import Fernet  # type: ignore
            except Exception:
                mb.showerror(
                    "Save Model", "cryptography package is required for encrypted save."
                )
                return
        import base64, gzip, hashlib, json, os
        for fmea in app.fmeas:
            app.export_fmea_to_csv(fmea, fmea["file"])
        for fmeda in app.fmedas:
            app.export_fmeda_to_csv(fmeda, fmeda["file"])
        data = app.export_model_data()
        if path.endswith(".autml"):
            try:
                from cryptography.fernet import Fernet  # type: ignore
            except Exception:
                mb.showwarning(
                    "Save Model",
                    (
                        "cryptography package is required for encrypted save. "
                        "Saving unencrypted JSON instead."
                    ),
                )
                path = os.path.splitext(path)[0] + ".json"
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
            else:
                password = askstring_fixed(
                    simpledialog,
                    "Password",
                    "Enter encryption password:",
                    show="*",
                )
                if password is None:
                    return
                raw = json.dumps(data).encode("utf-8")
                compressed = gzip.compress(raw)
                key = base64.urlsafe_b64encode(hashlib.sha256(password.encode()).digest())
                token = Fernet(key).encrypt(compressed)
                with open(path, "wb") as f:
                    f.write(token)
        else:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        mb.showinfo(
            "Saved", "Model saved with all configuration and safety goal information."
        )
        app.set_last_saved_state()

    # ------------------------------------------------------------------
    def load_model(self) -> None:
        import json, re, base64, gzip, hashlib, importlib
        app = self.app
        mb = app.messagebox
        if getattr(app, "has_unsaved_changes", lambda: False)():
            resp = self._prompt_save_before_load()
            if resp is None:
                return
            if resp:
                self.save_model()
        path = filedialog.askopenfilename(
            defaultextension=".autml",
            filetypes=[("AutoML Project", "*.autml"), ("JSON", "*.json")],
        )
        if not path:
            return
        if path.endswith(".autml"):
            try:
                from cryptography.fernet import Fernet, InvalidToken  # type: ignore
            except Exception:
                import subprocess, sys
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "cryptography"])
                    from cryptography.fernet import Fernet, InvalidToken  # type: ignore
                except Exception:
                    mb.showerror(
                        "Load Model", "cryptography package is required for encrypted files."
                    )
                    return
            password = askstring_fixed(
                simpledialog,
                "Password",
                "Enter decryption password:",
                show="*",
            )
            if password is None:
                return
            key = base64.urlsafe_b64encode(hashlib.sha256(password.encode()).digest())
            with open(path, "rb") as f:
                token = f.read()
            try:
                compressed = Fernet(key).decrypt(token)
            except InvalidToken:
                mb.showerror("Load Model", "Decryption failed. Check password.")
                return
            try:
                raw = gzip.decompress(compressed).decode("utf-8")
                data = json.loads(raw)
            except Exception as exc:
                mb.showerror("Load Model", f"Failed to parse model: {exc}")
                return
        else:
            with open(path, "r") as f:
                raw = f.read()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as exc:
                def clean(text: str) -> str:
                    text = re.sub(r"//.*", "", text)
                    text = re.sub(r"#.*", "", text)
                    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
                    text = re.sub(r",\s*(\]|\})", r"\1", text)
                    return text
                try:
                    data = json.loads(clean(raw))
                except json.JSONDecodeError:
                    mb.showerror("Load Model", f"Failed to parse JSON file:\n{exc}")
                    return
        self._reset_on_load()
        self.apply_model_data(data)
        app.set_last_saved_state()
        app._loaded_model_paths.append(path)

    # ------------------------------------------------------------------
    def apply_model_data(self, data: dict, ensure_root: bool = True) -> None:
        """Load model state from a dictionary."""

        model_loader.cleanup()
        app = self.app

        current = list(getattr(app, "enabled_work_products", set()))
        for name in current:
            try:
                app.validation_consistency.disable_work_product(name)
            except Exception:
                pass
        app.enabled_work_products = set()
        app._load_project_properties(data)

        repo_data = data.get("sysml_repository")
        if repo_data:
            repo = SysMLRepository.get_instance()
            repo.from_dict(repo_data)

        app._load_fault_tree_events(data, ensure_root)

        global_requirements.clear()
        for rid, req in data.get("global_requirements", {}).items():
            global_requirements[rid] = ensure_requirement_defaults(req)

        app.gsn_modules = [
            model_loader.proxy(f"gsn_module_{i}", lambda m=m: GSNModule.from_dict(m))
            for i, m in enumerate(data.get("gsn_modules", []))
        ]
        app.gsn_diagrams = [
            model_loader.proxy(f"gsn_diagram_{i}", lambda d=d: GSNDiagram.from_dict(d))
            for i, d in enumerate(data.get("gsn_diagrams", []))
        ]

        app.safety_mgmt_toolbox = SafetyManagementToolbox.from_dict(
            data.get("safety_mgmt_toolbox", {})
        )
        toolbox = app.safety_mgmt_toolbox
        app.governance_manager.attach_toolbox(toolbox)
        app._refresh_phase_requirements_menu()
        app.governance_manager.set_active_module(toolbox.active_module)
        for te in app.top_events:
            toolbox.register_loaded_work_product("FTA", te.user_name)
        for te in getattr(app, "cta_events", []):
            toolbox.register_loaded_work_product("CTA", te.user_name)
        for te in getattr(app, "paa_events", []):
            toolbox.register_loaded_work_product(
                "Prototype Assurance Analysis", te.user_name
            )

        for name in data.get("enabled_work_products", []):
            try:
                app.validation_consistency.enable_work_product(name)
            except Exception:
                app.enabled_work_products.add(name)

        app.fmea_service.load_fmeas(data)

        app.fmedas = []
        for doc in data.get("fmedas", []):
            entries = [FaultTreeNode.from_dict(e) for e in doc.get("entries", [])]
            app.fmedas.append(
                {
                    "name": doc.get("name", "FMEDA"),
                    "file": doc.get("file", f"fmeda_{len(app.fmedas)}.csv"),
                    "entries": entries,
                    "bom": doc.get("bom", ""),
                    "created": doc.get("created", datetime.datetime.now().isoformat()),
                    "author": doc.get("author", CURRENT_USER_NAME),
                    "modified": doc.get("modified", datetime.datetime.now().isoformat()),
                    "modified_by": doc.get("modified_by", CURRENT_USER_NAME),
                }
            )

        app.update_failure_list()

        node_map = {}
        for te in app.top_events:
            for n in app.get_all_nodes(te):
                node_map[n.unique_id] = n
        for entry in app.get_all_fmea_entries():
            orig = node_map.get(entry.unique_id)
            if orig and entry is not orig:
                entry.is_primary_instance = False
                entry.original = orig

        app.mechanism_libraries = []
        for lib in data.get("mechanism_libraries", []):
            mechs = [DiagnosticMechanism(**m) for m in lib.get("mechanisms", [])]
            app.mechanism_libraries.append(
                MechanismLibrary(lib.get("name", ""), mechs)
            )
        app.selected_mechanism_libraries = []
        for name in data.get("selected_mechanism_libraries", []):
            found = next((l for l in app.mechanism_libraries if l.name == name), None)
            if found:
                app.selected_mechanism_libraries.append(found)
        if not app.mechanism_libraries:
            app.load_default_mechanisms()

        app.mission_profiles = []
        for mp_data in data.get("mission_profiles", []):
            try:
                mp = MissionProfile(**mp_data)
                total = mp.tau_on + mp.tau_off
                mp.duty_cycle = mp.tau_on / total if total else 0.0
                app.mission_profiles.append(mp)
            except TypeError:
                pass

        app.reliability_analyses = []
        for ra in data.get("reliability_analyses", []):
            def load_comp(cdata):
                comp = ReliabilityComponent(
                    cdata.get("name", ""),
                    cdata.get("comp_type", ""),
                    cdata.get("quantity", 1),
                    cdata.get("attributes", {}),
                    cdata.get("qualification", cdata.get("safety_req", "")),
                    cdata.get("fit", 0.0),
                    cdata.get("is_passive", False),
                )
                comp.sub_boms = [
                    [load_comp(sc) for sc in bom]
                    for bom in cdata.get("sub_boms", [])
                ]
                return comp

            comps = [load_comp(c) for c in ra.get("components", [])]
            app.reliability_analyses.append(
                ReliabilityAnalysis(
                    ra.get("name", ""),
                    ra.get("standard", ""),
                    ra.get("profile", ""),
                    comps,
                    ra.get("total_fit", 0.0),
                    ra.get("spfm", 0.0),
                    ra.get("lpfm", 0.0),
                    ra.get("dc", 0.0),
                )
            )

        app.hazop_docs = []
        for d in data.get("hazops", []):
            entries = []
            for h in d.get("entries", []):
                h["safety"] = boolify(h.get("safety", False), False)
                h["covered"] = boolify(h.get("covered", False), False)
                entries.append(HazopEntry(**h))
            doc = HazopDoc(d.get("name", f"HAZOP {len(app.hazop_docs)+1}"), entries)
            app.hazop_docs.append(doc)
            toolbox.register_loaded_work_product("HAZOP", doc.name)
        hazop_entries = data.get("hazop_entries", [])
        if not app.hazop_docs and hazop_entries:
            entries = []
            for h in hazop_entries:
                h["safety"] = boolify(h.get("safety", False), False)
                h["covered"] = boolify(h.get("covered", False), False)
                entries.append(HazopEntry(**h))
            doc = HazopDoc("Default", entries)
            app.hazop_docs.append(doc)
            toolbox.register_loaded_work_product("HAZOP", doc.name)
        app.active_hazop = app.hazop_docs[0] if app.hazop_docs else None
        app.hazop_entries = app.active_hazop.entries if app.active_hazop else []

        app.hara_docs = []
        for d in data.get("haras", []):
            entries = []
            for e in d.get("entries", []):
                cdata = e.get("cyber")
                cyber = app.cyber_manager.build_risk_entry(cdata)
                entries.append(
                    HaraEntry(
                        e.get("malfunction", ""),
                        e.get("hazard", ""),
                        e.get("scenario", ""),
                        e.get("severity", 1),
                        e.get("sev_rationale", ""),
                        e.get("controllability", 1),
                        e.get("cont_rationale", ""),
                        e.get("exposure", 1),
                        e.get("exp_rationale", ""),
                        e.get("asil", "QM"),
                        e.get("safety_goal", ""),
                        cyber,
                    )
                )
            hazops = d.get("hazops")
            if not hazops:
                hazop = d.get("hazop")
                hazops = [hazop] if hazop else []
                doc = HaraDoc(
                    d.get("name", f"Risk Assessment {len(app.hara_docs)+1}"),
                    hazops,
                    entries,
                    d.get("approved", False),
                    d.get("status", "draft"),
                    stpa=d.get("stpa", ""),
                    threat=d.get("threat", ""),
                    fi2tc=d.get("fi2tc", ""),
                    tc2fi=d.get("tc2fi", ""),
                )
            app.hara_docs.append(doc)
            toolbox.register_loaded_work_product("Risk Assessment", doc.name)
        if not app.hara_docs and data.get("hara_entries"):
            hazop_name = app.hazop_docs[0].name if app.hazop_docs else ""
            entries = []
            for e in data.get("hara_entries", []):
                cdata = e.get("cyber")
                cyber = app.cyber_manager.build_risk_entry(cdata)
                entries.append(
                    HaraEntry(
                        e.get("malfunction", ""),
                        e.get("hazard", ""),
                        e.get("scenario", ""),
                        e.get("severity", 1),
                        e.get("sev_rationale", ""),
                        e.get("controllability", 1),
                        e.get("cont_rationale", ""),
                        e.get("exposure", 1),
                        e.get("exp_rationale", ""),
                        e.get("asil", "QM"),
                        e.get("safety_goal", ""),
                        cyber,
                    )
                )
            doc = HaraDoc(
                "Default",
                [hazop_name] if hazop_name else [],
                entries,
                False,
                "draft",
                stpa="",
                threat="",
                fi2tc="",
                tc2fi="",
            )
            app.hara_docs.append(doc)
            toolbox.register_loaded_work_product("Risk Assessment", doc.name)
        app.active_hara = app.hara_docs[0] if app.hara_docs else None
        app.hara_entries = app.active_hara.entries if app.active_hara else []
        app.update_hazard_list()

        app.stpa_docs = []
        for d in data.get("stpas", []):
            entries = [
                StpaEntry(
                    e.get("action", ""),
                    e.get("not_providing", ""),
                    e.get("providing", ""),
                    e.get("incorrect_timing", ""),
                    e.get("stopped_too_soon", ""),
                    e.get("safety_constraints", []),
                )
                for e in d.get("entries", [])
            ]
            doc = StpaDoc(
                d.get("name", f"STPA {len(app.stpa_docs)+1}"),
                d.get("diagram", ""),
                entries,
            )
            app.stpa_docs.append(doc)
            toolbox.register_loaded_work_product("STPA", doc.name)
        if not app.stpa_docs and data.get("stpa_entries"):
            entries = [
                StpaEntry(
                    e.get("action", ""),
                    e.get("not_providing", ""),
                    e.get("providing", ""),
                    e.get("incorrect_timing", ""),
                    e.get("stopped_too_soon", ""),
                    e.get("safety_constraints", []),
                )
                for e in data.get("stpa_entries", [])
            ]
            doc = StpaDoc(
                "Default",
                data.get("stpa_diagram", ""),
                entries,
            )
            app.stpa_docs.append(doc)
            toolbox.register_loaded_work_product("STPA", doc.name)
        app.active_stpa = app.stpa_docs[0] if app.stpa_docs else None
        app.update_views()
