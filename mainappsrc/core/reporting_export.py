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

"""Reporting and export helpers for :class:`AutoMLApp`."""

import csv
import json
import html
from dataclasses import asdict
from pathlib import Path
from io import BytesIO

from tkinter import filedialog

from gui.utils import logger

try:  # pragma: no cover - pillow optional
    from PIL import Image
except ModuleNotFoundError:  # pragma: no cover
    Image = None

from analysis.fmeda_utils import GATE_NODE_TYPES
from mainappsrc.models.sysml.sysml_repository import SysMLRepository


class Reporting_Export:
    """Encapsulate reporting and export related methods."""

    def __init__(self, app) -> None:
        self.app = app

    # ------------------------------------------------------------------
    # Delegations to sub-apps and managers
    def build_text_report(self, node, indent: int = 0):
        return self.app.fta_app.build_text_report(self.app, node, indent)

    def build_unified_recommendation_table(self):
        return self.app.fta_app.build_unified_recommendation_table(self.app)

    def build_dynamic_recommendations_table(self):  # pragma: no cover - passthrough
        return self.app.fta_app.build_dynamic_recommendations_table(self.app)

    def build_base_events_table_html(self):  # pragma: no cover - passthrough
        return self.app.fta_app.build_base_events_table_html(self.app)

    def build_requirement_diff_html(self, review):
        return self.app.requirements_manager.build_requirement_diff_html(review)

    # ------------------------------------------------------------------
    # Reporting helpers
    def _generate_pdf_report(self) -> None:
        """Export a PDF report using a JSON template."""
        pdf_path = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF", "*.pdf")]
        )
        if not pdf_path:
            return

        template_path = filedialog.askopenfilename(
            defaultextension=".json", filetypes=[("JSON", "*.json")]
        )
        if not template_path:
            return

        try:
            with open(template_path, "r", encoding="utf-8") as tpl:
                template = json.load(tpl)
            debug_path = Path(pdf_path).with_suffix(".json")
            with open(debug_path, "w", encoding="utf-8") as dbg:
                json.dump(template, dbg)

            from reportlab.platypus import SimpleDocTemplate, Paragraph
            from reportlab.lib.styles import getSampleStyleSheet

            styles = getSampleStyleSheet()
            title = self.app.project_properties.get(
                "pdf_report_name", "AutoML-Analyzer PDF Report"
            )
            doc = SimpleDocTemplate(pdf_path)
            doc.build([Paragraph(title, styles["Title"])])
            logger.log_message(f"PDF report generated at {pdf_path}")
        except Exception as exc:  # pragma: no cover - best effort error path
            logger.log_message(f"Failed to generate PDF report: {exc}", "ERROR")

    def generate_pdf_report(self) -> None:
        """Public wrapper for :meth:`_generate_pdf_report`."""
        self._generate_pdf_report()

    def generate_report(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".html", filetypes=[("HTML", "*.html")]
        )
        if path:
            html_content = self.build_html_report()
            with open(path, "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.log_message(f"HTML report generated at {path}")

    def build_html_report(self) -> str:
        def node_to_html(n):
            txt = f"{n.name} ({n.node_type}"
            if n.node_type.upper() in GATE_NODE_TYPES:
                txt += f", {n.gate_type}"
            txt += ")"
            if n.display_label:
                txt += f" => {n.display_label}"
            if n.description:
                txt += f"<br>Desc: {n.description}"
            if n.rationale:
                txt += f"<br>Rationale: {n.rationale}"
            content = f"<details open><summary>{txt}</summary>\n"
            for c in n.children:
                content += node_to_html(c)
            content += "</details>\n"
            return content

        return (
            f"""<!DOCTYPE html>
                    <html>
                    <head>
                    <meta charset=\"UTF-8\">
                    <title>AutoML-Analyzer</title>
                    <style>body {{ font-family: Arial; }} details {{ margin-left: 20px; }}</style>
                    </head>
                    <body>
                    <h1>AutoML-Analyzer</h1>
                    {node_to_html(self.app.root_node)}
                    </body>
                    </html>"""
        )

    # ------------------------------------------------------------------
    # Export helpers
    def export_model_data(self, include_versions: bool = True):
        app = self.app
        app.update_odd_elements()
        reviews = []
        for r in getattr(app, "reviews", []):
            reviews.append(
                {
                    "name": r.name,
                    "description": r.description,
                    "mode": r.mode,
                    "moderators": [asdict(m) for m in r.moderators],
                    "approved": r.approved,
                    "reviewed": getattr(r, "reviewed", False),
                    "due_date": r.due_date,
                    "closed": r.closed,
                    "participants": [asdict(p) for p in r.participants],
                    "comments": [asdict(c) for c in r.comments],
                    "fta_ids": r.fta_ids,
                    "fmea_names": r.fmea_names,
                    "fmeda_names": getattr(r, 'fmeda_names', []),
                    "hazop_names": getattr(r, 'hazop_names', []),
                    "hara_names": getattr(r, 'hara_names', []),
                    "stpa_names": getattr(r, 'stpa_names', []),
                    "fi2tc_names": getattr(r, 'fi2tc_names', []),
                    "tc2fi_names": getattr(r, 'tc2fi_names', []),
                }
            )
        review_data = getattr(app, "review_data", None)
        current_name = review_data.name if review_data else None
        repo = SysMLRepository.get_instance()
        data = {
            "top_events": [event.to_dict() for event in getattr(app, "top_events", [])],
            "cta_events": [event.to_dict() for event in getattr(app, "cta_events", [])],
            "paa_events": [event.to_dict() for event in getattr(app, "paa_events", [])],
            "fmeas": [
                {
                    "name": f["name"],
                    "file": f["file"],
                    "entries": [e.to_dict() for e in f["entries"]],
                    "created": f.get("created", ""),
                    "author": f.get("author", ""),
                    "modified": f.get("modified", ""),
                    "modified_by": f.get("modified_by", ""),
                }
                for f in app.fmeas
            ],
            "fmedas": [
                {
                    "name": d["name"],
                    "file": d["file"],
                    "entries": [e.to_dict() for e in d["entries"]],
                    "bom": d.get("bom", ""),
                    "created": d.get("created", ""),
                    "author": d.get("author", ""),
                    "modified": d.get("modified", ""),
                    "modified_by": d.get("modified_by", ""),
                }
                for d in app.fmedas
            ],
            "mechanism_libraries": [
                {
                    "name": lib.name,
                    "mechanisms": [asdict(m) for m in lib.mechanisms],
                }
                for lib in app.mechanism_libraries
            ],
            "selected_mechanism_libraries": [
                lib.name for lib in app.selected_mechanism_libraries
            ],
            "mission_profiles": [
                {
                    **asdict(mp),
                    "duty_cycle": mp.tau_on / (mp.tau_on + mp.tau_off)
                    if (mp.tau_on + mp.tau_off)
                    else 0.0,
                }
                for mp in app.mission_profiles
            ],
            "reliability_analyses": [
                {
                    **asdict(ra),
                    "fault_trees": [
                        {"name": ft.name, "events": [asdict(ev) for ev in ft.events]}
                        for ft in ra.fault_trees
                    ],
                }
                for ra in app.reliability_analyses
            ],
            "reliability_components": [asdict(c) for c in app.reliability_components],
            "reliability_total_fit": app.reliability_total_fit,
            "spfm": app.spfm,
            "lpfm": app.lpfm,
            "reliability_dc": app.reliability_dc,
            "item_definition": app.item_definition,
            "safety_concept": app.safety_concept,
            "fmeda_components": [asdict(c) for c in app.fmeda_components],
            "user": app.current_user,
            "hazop_docs": [d.to_dict() for d in app.hazop_docs],
            "hara_docs": [d.to_dict() for d in app.hara_docs],
            "stpa_docs": [d.to_dict() for d in app.stpa_docs],
            "threat_docs": [d.to_dict() for d in app.threat_docs],
            "fi2tc_docs": [d.to_dict() for d in app.fi2tc_docs],
            "tc2fi_docs": [d.to_dict() for d in app.tc2fi_docs],
            "current_review": current_name,
            "reviews": reviews,
            "project_properties": app.project_properties,
            "mechanism_libraries_selected": [
                lib.name for lib in app.selected_mechanism_libraries
            ],
            "scenario_libraries": [asdict(lib) for lib in app.scenario_libraries],
            "odd_libraries": [asdict(lib) for lib in app.odd_libraries],
            "odd_elements": [asdict(e) for e in app.odd_elements],
            "versions": app.versions if include_versions else [],
            "fmea_settings": app.fmea_service.get_settings_dict(),
            "req_editor": app.requirements_manager.export_state(),
            "sysml_repository": repo.export_state() if repo else {},
            "diagrams": [d.to_dict() for d in app.arch_diagrams],
            "management_diagrams": [
                d.to_dict() for d in getattr(app, "management_diagrams", [])
            ],
            "gsn_modules": [m.to_dict() for m in app.gsn_modules],
            "gsn_diagrams": [d.to_dict() for d in app.gsn_diagrams],
        }
        return data

    def export_product_goal_requirements(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV", "*.csv")]
        )
        if not path:
            return
        columns = [
            "Product Goal",
            "PG ASIL",
            "Safe State",
            "Requirement ID",
            "Req ASIL",
            "Text",
        ]
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            for te in self.app.top_events:
                sg_text = te.safety_goal_description or (
                    te.user_name or f"SG {te.unique_id}"
                )
                sg_asil = te.safety_goal_asil
                reqs = self.app.collect_requirements_recursive(te)
                seen = set()
                for req in reqs:
                    rid = req.get("id")
                    if rid in seen:
                        continue
                    seen.add(rid)
                    writer.writerow(
                        [
                            sg_text,
                            sg_asil,
                            te.safe_state,
                            rid,
                            req.get("asil", ""),
                            req.get("text", ""),
                        ]
                    )
        logger.log_message(f"Product goal requirements exported to {path}")

    def export_cybersecurity_goal_requirements(self) -> None:
        self.app.cyber_manager.export_goal_requirements()

    def create_diagram_image(self):  # pragma: no cover - GUI helper
        canvas = getattr(self.app, "canvas", None)
        if not canvas:
            return None
        canvas.update()
        bbox = canvas.bbox("all")
        if not bbox:
            return None
        x, y, w, h = bbox[0], bbox[1], bbox[2] - bbox[0], bbox[3] - bbox[1]
        ps = canvas.postscript(colormode="color", x=x, y=y, width=w, height=h)
        ps_bytes = BytesIO(ps.encode("utf-8"))
        if Image is None:  # pragma: no cover - pillow optional
            return None
        img = Image.open(ps_bytes)
        img.load(scale=3)
        return img.convert("RGB")

    def create_diagram_image_without_grid(self):  # pragma: no cover - GUI helper
        app = self.app
        target_canvas = None
        if hasattr(app, "canvas") and app.canvas is not None and app.canvas.winfo_exists():
            target_canvas = app.canvas
        elif hasattr(app, "page_diagram") and app.page_diagram is not None:
            target_canvas = app.page_diagram.canvas
        if target_canvas is None:
            return None
        grid_items = target_canvas.find_withtag("grid")
        target_canvas.delete("grid")
        target_canvas.update()
        bbox = target_canvas.bbox("all")
        if not bbox:
            return None
        x, y, w, h = bbox[0], bbox[1], bbox[2] - bbox[0], bbox[3] - bbox[1]
        ps = target_canvas.postscript(colormode="color", x=x, y=y, width=w, height=h)
        ps_bytes = BytesIO(ps.encode("utf-8"))
        if Image is None:  # pragma: no cover - pillow optional
            return None
        img = Image.open(ps_bytes)
        img.load(scale=3)
        if target_canvas == getattr(app, "canvas", None):
            app.redraw_canvas()
        else:
            app.page_diagram.redraw_canvas()
        return img.convert("RGB")
