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
from analysis.models import global_requirements
from config import load_report_template
from gui.utils.config_utils import AutoML_Helper, _REPORT_TEMPLATE_PATH
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

    def build_cause_effect_data(self):
        """Return cause-effect table rows for PDF rendering."""
        return self.app.build_cause_effect_data()

    def build_requirement_diff_html(self, review):
        return self.app.requirements_manager.build_requirement_diff_html(review)

    def generate_recommendations_for_top_event(self, node):
        """Return recommendations for a given top event node."""
        return self.app.generate_recommendations_for_top_event(node)

    def get_extra_recommendations_list(self, description, level):
        """Return extra recommendations for description at a given level."""
        return self.app.get_extra_recommendations_list(description, level)

    def get_all_nodes_in_model(self):
        """Return all nodes currently present in the model."""
        return self.app.get_all_nodes_in_model()

    def get_all_nodes(self, node=None):
        """Return all nodes starting at ``node``.

        This delegates to :meth:`AutoMLApp.get_all_nodes` so reporting code can
        traverse the diagram hierarchy without directly depending on the
        :class:`AutoMLApp` instance.
        """
        return self.app.get_all_nodes(node)

    def get_all_basic_events(self):
        """Return all basic events currently defined in the model."""
        return self.app.get_all_basic_events()

    @property
    def root_node(self):
        """Return the current root node of the application model."""
        return getattr(self.app, "root_node", None)

    @property
    def top_events(self):
        """Return top events currently defined in the application.

        This delegates to the underlying :class:`AutoMLApp` to expose its
        ``top_events`` list so callers can iterate over safety goals without
        reaching into the app object directly.
        """
        return getattr(self.app, "top_events", [])

    # ------------------------------------------------------------------
    # Reporting helpers
    def _generate_pdf_report(self) -> None:
        """Generate a PDF report based on the configurable template."""

        report_title = self.app.project_properties.get(
            "pdf_report_name", "AutoML-Analyzer PDF Report"
        )
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")]
        )
        if not path:
            return
        path = Path(path)
        if path.suffix.lower() != ".pdf":
            path = path.with_suffix(".pdf")

        template_path = filedialog.askopenfilename(
            title="Select Report Template",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialdir=_REPORT_TEMPLATE_PATH.parent,
            initialfile=_REPORT_TEMPLATE_PATH.name,
        )
        if not template_path:
            return

        try:
            from reportlab.lib.pagesizes import letter, landscape
            from reportlab.lib.units import inch
            from reportlab.platypus import (
                Paragraph,
                Spacer,
                SimpleDocTemplate,
                Image as RLImage,
                Table,
                TableStyle,
                PageBreak,
            )
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            from io import BytesIO
            from PIL import Image, ImageDraw
        except Exception:
            messagebox.showerror(
                "Report",
                "Reportlab and Pillow packages are required to generate PDF reports.",
            )
            return

        try:
            template = load_report_template(template_path)
        except Exception as exc:
            messagebox.showerror("Report", f"Failed to load report template\n{exc}")
            return

        doc = SimpleDocTemplate(
            str(path),
            pagesize=landscape(letter),
            leftMargin=0.8 * inch,
            rightMargin=0.8 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )
        styles = getSampleStyleSheet()
        pdf_styles = styles
        preformatted_style = ParagraphStyle(
            name="Preformatted",
            parent=pdf_styles["Normal"],
            fontName="Courier",
            fontSize=8,
            leading=10,
        )

        def scale_image(img, max_width=500, max_height=300):
            w, h = img.size
            scale = min(max_width / w, max_height / h, 1)
            return w * scale, h * scale

        story = [Paragraph(report_title, styles["Title"]), Spacer(1, 12)]

        def _element_base_matrix():
            header_style = ParagraphStyle(
                name="SafetyGoalsHeader",
                parent=pdf_styles["Normal"],
                fontSize=10,
                leading=12,
                alignment=1,
            )
            data = [
                [
                    Paragraph("<b>Robustness \\ Confidence</b>", header_style),
                    Paragraph("<b>1 (Level 1)</b>", header_style),
                    Paragraph("<b>2 (Level 2)</b>", header_style),
                    Paragraph("<b>3 (Level 3)</b>", header_style),
                    Paragraph("<b>4 (Level 4)</b>", header_style),
                    Paragraph("<b>5 (Level 5)</b>", header_style),
                ],
                [
                    Paragraph("<b>1 (Level 1)</b>", header_style),
                    Paragraph("PAL5", pdf_styles["Normal"]),
                    Paragraph("PAL5", pdf_styles["Normal"]),
                    Paragraph("PAL4", pdf_styles["Normal"]),
                    Paragraph("PAL4", pdf_styles["Normal"]),
                    Paragraph("PAL4", pdf_styles["Normal"]),
                ],
                [
                    Paragraph("<b>2 (Level 2)</b>", header_style),
                    Paragraph("PAL5", pdf_styles["Normal"]),
                    Paragraph("PAL5", pdf_styles["Normal"]),
                    Paragraph("PAL4", pdf_styles["Normal"]),
                    Paragraph("PAL3", pdf_styles["Normal"]),
                    Paragraph("PAL3", pdf_styles["Normal"]),
                ],
                [
                    Paragraph("<b>3 (Level 3)</b>", header_style),
                    Paragraph("PAL4", pdf_styles["Normal"]),
                    Paragraph("PAL4", pdf_styles["Normal"]),
                    Paragraph("PAL3", pdf_styles["Normal"]),
                    Paragraph("PAL3", pdf_styles["Normal"]),
                    Paragraph("PAL1", pdf_styles["Normal"]),
                ],
                [
                    Paragraph("<b>4 (Level 4)</b>", header_style),
                    Paragraph("PAL4", pdf_styles["Normal"]),
                    Paragraph("PAL3", pdf_styles["Normal"]),
                    Paragraph("PAL3", pdf_styles["Normal"]),
                    Paragraph("PAL1", pdf_styles["Normal"]),
                    Paragraph("PAL1", pdf_styles["Normal"]),
                ],
                [
                    Paragraph("<b>5 (Level 5)</b>", header_style),
                    Paragraph("PAL4", pdf_styles["Normal"]),
                    Paragraph("PAL3", pdf_styles["Normal"]),
                    Paragraph("PAL1", pdf_styles["Normal"]),
                    Paragraph("PAL1", pdf_styles["Normal"]),
                    Paragraph("PAL1", pdf_styles["Normal"]),
                ],
            ]
            table = Table(data, colWidths=[80, 70, 70, 70, 70, 70])
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
                        ("BACKGROUND", (0, 0), (0, -1), colors.lightblue),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ]
                )
            )
            return [
                Paragraph("Table 1: Base Assurance Inversion Matrix", pdf_styles["Heading3"]),
                Spacer(1, 6),
                table,
                Spacer(1, 12),
            ]

        def _element_discretization():
            header_style = ParagraphStyle(
                name="DiscretizationHeader",
                parent=pdf_styles["Normal"],
                fontSize=10,
                leading=12,
                alignment=1,
            )
            data = [
                [
                    Paragraph("<b>Continuous Value (Rounded)</b>", header_style),
                    Paragraph("<b>Prototype Assurance Level (PAL)</b>", header_style),
                ],
                [Paragraph("< 1.5", header_style), Paragraph("Level 1 (PAL1)", pdf_styles["Normal"])],
                [Paragraph("1.5 – < 2.5", header_style), Paragraph("Level 2 (PAL2)", pdf_styles["Normal"])],
                [Paragraph("2.5 – < 3.5", header_style), Paragraph("Level 3 (PAL3)", pdf_styles["Normal"])],
                [Paragraph("3.5 – < 4.5", header_style), Paragraph("Level 4 (PAL4)", pdf_styles["Normal"])],
                [Paragraph("≥ 4.5", header_style), Paragraph("Level 5 (PAL5)", pdf_styles["Normal"])],
            ]
            table = Table(data, colWidths=[150, 200])
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ]
                )
            )
            return [
                Paragraph("Table 2: Output Discretization Mapping", pdf_styles["Heading3"]),
                Spacer(1, 6),
                table,
                Spacer(1, 12),
            ]

        def _element_hazop():
            items: list = []
            if getattr(self, "hazop_docs", []):
                items.append(PageBreak())
                items.append(Paragraph("HAZOP Analyses", pdf_styles["Heading2"]))
                items.append(Spacer(1, 12))
                for hz_doc in self.hazop_docs:
                    items.append(Paragraph(hz_doc.name, pdf_styles["Heading3"]))
                    data = [["Function", "Malfunction", "Hazard", "Safety"]]
                    for e in hz_doc.entries:
                        data.append([e.function, e.malfunction, e.hazard, "Yes" if e.safety else "No"])
                    table = Table(data, repeatRows=1)
                    table.setStyle(
                        TableStyle(
                            [
                                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                ("FONTSIZE", (0, 0), (-1, -1), 8),
                            ]
                        )
                    )
                    items.append(table)
                    items.append(Spacer(1, 12))
            return items

        def _element_fi2tc():
            items: list = []
            if getattr(self, "fi2tc_docs", []):
                items.append(PageBreak())
                items.append(Paragraph("FI2TC Analyses", pdf_styles["Heading2"]))
                items.append(Spacer(1, 12))
                for fi_doc in self.fi2tc_docs:
                    items.append(Paragraph(fi_doc.name, pdf_styles["Heading3"]))
                    data = [["System Function", "Functional Insufficiencies", "Triggering Conditions", "Severity"]]
                    for row in fi_doc.entries:
                        data.append([
                            row.get("system_function", ""),
                            row.get("functional_insufficiencies", ""),
                            row.get("triggering_conditions", ""),
                            row.get("severity", ""),
                        ])
                    table = Table(data, repeatRows=1)
                    table.setStyle(
                        TableStyle(
                            [
                                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                ("FONTSIZE", (0, 0), (-1, -1), 8),
                            ]
                        )
                    )
                    items.append(table)
                    items.append(Spacer(1, 12))
            return items

        def _element_tc2fi():
            items: list = []
            if getattr(self, "tc2fi_docs", []):
                items.append(PageBreak())
                items.append(Paragraph("TC2FI Analyses", pdf_styles["Heading2"]))
                items.append(Spacer(1, 12))
                for tc_doc in self.tc2fi_docs:
                    items.append(Paragraph(tc_doc.name, pdf_styles["Heading3"]))
                    data = [["Known Use Case", "Functional Insufficiencies", "Triggering Conditions", "Severity"]]
                    for row in tc_doc.entries:
                        data.append([
                            row.get("known_use_case", ""),
                            row.get("functional_insufficiencies", ""),
                            row.get("triggering_conditions", ""),
                            row.get("severity", ""),
                        ])
                    table = Table(data, repeatRows=1)
                    table.setStyle(
                        TableStyle(
                            [
                                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                ("FONTSIZE", (0, 0), (-1, -1), 8),
                            ]
                        )
                    )
                    items.append(table)
                    items.append(Spacer(1, 12))
            return items

        def _element_risk():
            items: list = []
            if getattr(self, "hara_docs", []):
                items.append(PageBreak())
                items.append(Paragraph("Risk Assessment", pdf_styles["Heading2"]))
                items.append(Spacer(1, 12))
                for hara_doc in self.hara_docs:
                    items.append(Paragraph(hara_doc.name, pdf_styles["Heading3"]))
                    data = [[
                        "Malfunction",
                        "Hazard",
                        "Severity",
                        "Exposure",
                        "Controllability",
                        "ASIL",
                        "Safety Goal",
                    ]]
                    for e in hara_doc.entries:
                        data.append([
                            e.malfunction,
                            e.hazard,
                            str(e.severity),
                            str(e.exposure),
                            str(e.controllability),
                            e.asil,
                            e.safety_goal,
                        ])
                    table = Table(data, repeatRows=1)
                    table.setStyle(
                        TableStyle(
                            [
                                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                ("FONTSIZE", (0, 0), (-1, -1), 8),
                            ]
                        )
                    )
                    items.append(table)
                    items.append(Spacer(1, 12))
            return items

        def _element_cbn():
            items: list = []
            if getattr(self, "cbn_docs", []):
                items.append(PageBreak())
                items.append(Paragraph("Causal Bayesian Network Analyses", pdf_styles["Heading2"]))
                items.append(Spacer(1, 12))
                for cbn_doc in self.cbn_docs:
                    items.append(Paragraph(cbn_doc.name, pdf_styles["Heading3"]))
                    img = self.capture_cbn_diagram(cbn_doc)
                    if img is not None:
                        buf = BytesIO()
                        img.save(buf, format="PNG")
                        buf.seek(0)
                        desired_width, desired_height = scale_image(img)
                        rl_img = RLImage(buf, width=desired_width, height=desired_height)
                        items.append(rl_img)
                        items.append(Spacer(1, 12))
                    network = cbn_doc.network
                    for var in network.nodes:
                        items.append(Paragraph(var, pdf_styles["Heading4"]))
                        data = [["Combination", "P(True)", "P(Parents)", "P(All)"]]
                        parents = network.parents.get(var, [])
                        for combo, p_true, combo_prob, joint_prob in network.cpd_rows(var):
                            combo_str = (
                                ", ".join(f"{p}={v}" for p, v in zip(parents, combo))
                                if parents
                                else "(prior)"
                            )
                            data.append([
                                combo_str,
                                f"{p_true:.3f}",
                                f"{combo_prob:.3f}",
                                f"{joint_prob:.3f}",
                            ])
                        table = Table(data, repeatRows=1)
                        table.setStyle(
                            TableStyle(
                                [
                                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                                ]
                            )
                        )
                        items.append(table)
                        items.append(Spacer(1, 12))
            return items

        def _element_safety_goals():
            items: list = []
            level_labels = {1: "PAL1", 2: "PAL2", 3: "PAL3", 4: "PAL4", 5: "PAL5"}

            def get_immediate_parent_assurance(node):
                if node.parents:
                    assurances = []
                    for p in node.parents:
                        parent = p if p.is_primary_instance else p.original
                        try:
                            val = int(parent.quant_value)
                        except (TypeError, ValueError):
                            val = 1
                        assurances.append(val)
                    return max(assurances) if assurances else int(
                        node.quant_value if node.quant_value is not None else 1
                    )
                else:
                    return int(node.quant_value if node.quant_value is not None else 1)

            grouped_by_linked: dict = {}
            for node in self.get_all_nodes_in_model():
                if hasattr(node, "safety_requirements") and node.safety_requirements:
                    safety_goal = (
                        node.safety_goal_description.strip()
                        if node.safety_goal_description.strip() != ""
                        else node.name
                    )
                    parent_assur = get_immediate_parent_assurance(node)
                    assurance_str = f"Level {parent_assur} ({level_labels.get(parent_assur, 'N/A')})"
                    linked_rec = self.generate_recommendations_for_top_event(node)
                    extra_recs = self.get_extra_recommendations_list(
                        node.description, AutoML_Helper.discretize_level(node.quant_value)
                    )
                    if not extra_recs:
                        extra_recs = ["No Extra Recommendation"]
                    grouped_by_linked.setdefault(linked_rec, {})
                    for extra in extra_recs:
                        grouped_by_linked.setdefault(linked_rec, {}).setdefault(extra, [])
                        grouped_by_linked[linked_rec][extra].append(
                            f"- {safety_goal} (Assurance: {assurance_str})"
                        )

            sg_data = [
                [
                    Paragraph("<b>Linked Recommendation</b>", pdf_styles["Normal"]),
                    Paragraph(
                        "<b>Safety Goals Grouped by Extra Recommendation</b>",
                        pdf_styles["Normal"],
                    ),
                ]
            ]
            for linked_rec, extra_groups in grouped_by_linked.items():
                nested_text = ""
                for extra_rec, goals in extra_groups.items():
                    nested_text += f"<b>{extra_rec}:</b><br/>" + "<br/>".join(goals) + "<br/><br/>"
                sg_data.append([
                    Paragraph(linked_rec, pdf_styles["Normal"]),
                    Paragraph(nested_text, pdf_styles["Normal"]),
                ])
            if len(sg_data) > 1:
                table = Table(sg_data, colWidths=[200, 400])
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("FONTSIZE", (0, 0), (-1, -1), 10),
                            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                        ]
                    )
                )
                items.append(Paragraph("Safety Goals Summary:", pdf_styles["Heading2"]))
                items.append(Spacer(1, 12))
                items.append(table)
                items.append(Spacer(1, 12))
                items.append(PageBreak())
            return items

        def _element_top_events():
            items: list = []
            cause_effect_rows = self.build_cause_effect_data()
            processed_ids = set()
            for idx, event in enumerate(self.top_events, start=1):
                if event.unique_id in processed_ids:
                    continue
                processed_ids.add(event.unique_id)
                items.append(
                    Paragraph(
                        f"Top-Level Event #{idx}: {event.name}", pdf_styles["Heading2"]
                    )
                )
                items.append(Spacer(1, 12))
                argumentation_text = self.generate_argumentation_report(event)
                if isinstance(argumentation_text, list):
                    argumentation_text = "\n".join(str(x) for x in argumentation_text)
                argumentation_text = argumentation_text.replace("\n", "<br/>")
                items.append(Paragraph(argumentation_text, preformatted_style))
                items.append(Spacer(1, 12))

                event_img = self.capture_event_diagram(event)
                if event_img is not None:
                    buf = BytesIO()
                    event_img.save(buf, format="PNG")
                    buf.seek(0)
                    desired_width, desired_height = scale_image(event_img)
                    rl_img = RLImage(buf, width=desired_width, height=desired_height)
                    items.append(Paragraph("Detailed Diagram (Subtree):", pdf_styles["Heading3"]))
                    items.append(Spacer(1, 12))
                    items.append(rl_img)
                    items.append(Spacer(1, 12))

                ce_row = next(
                    (
                        r
                        for r in cause_effect_rows
                        if r["malfunction"] == getattr(event, "malfunction", "")
                    ),
                    None,
                )
                if ce_row:
                    ce_img = self.render_cause_effect_diagram(ce_row)
                    if ce_img:
                        buf = BytesIO()
                        ce_img.save(buf, format="PNG")
                        buf.seek(0)
                        desired_width, desired_height = scale_image(ce_img)
                        rl_img2 = RLImage(buf, width=desired_width, height=desired_height)
                        items.append(
                            Paragraph("Cause and Effect Diagram:", pdf_styles["Heading3"])
                        )
                        items.append(Spacer(1, 12))
                        items.append(rl_img2)
                        items.append(Spacer(1, 12))
                items.append(PageBreak())
            return items

        def _element_page_diagrams():
            items: list = []
            unique_page_nodes = {}
            for evt in self.top_events:
                for pg in self.get_page_nodes(evt):
                    if pg.is_primary_instance:
                        unique_page_nodes[pg.unique_id] = pg

            if unique_page_nodes:
                items.append(Paragraph("Page Diagrams:", pdf_styles["Heading2"]))
                items.append(Spacer(1, 12))

            for page_node in unique_page_nodes.values():
                page_img = self.capture_page_diagram(page_node)
                if page_img is not None:
                    buf = BytesIO()
                    page_img.save(buf, format="PNG")
                    buf.seek(0)
                    desired_width, desired_height = scale_image(page_img)
                    rl_page_img = RLImage(buf, width=desired_width, height=desired_height)
                    items.append(
                        Paragraph(
                            f"Page Diagram for: {page_node.name}", pdf_styles["Heading3"]
                        )
                    )
                    items.append(Spacer(1, 12))
                    items.append(rl_page_img)
                    items.append(Spacer(1, 12))
                else:
                    items.append(
                        Paragraph(
                            "A page diagram could not be captured.",
                            pdf_styles["Normal"],
                        )
                    )
                    items.append(Spacer(1, 12))
            return items

        def _element_sysml_diagrams():
            items: list = []
            repo = SysMLRepository.get_instance()
            diagrams = list(repo.diagrams.values())
            if diagrams:
                items.append(Paragraph("SysML Diagrams:", pdf_styles["Heading2"]))
                items.append(Spacer(1, 12))

            for diag in diagrams:
                img = self.capture_sysml_diagram(diag)
                if img is not None:
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    buf.seek(0)
                    desired_width, desired_height = scale_image(img)
                    rl_img = RLImage(buf, width=desired_width, height=desired_height)
                    items.append(Paragraph(diag.name, pdf_styles["Heading3"]))
                    items.append(Spacer(1, 12))
                    items.append(rl_img)
                    items.append(Spacer(1, 12))
            return items

        def _element_fmea_tables():
            items: list = []
            if getattr(self, "fmeas", []):
                items.append(PageBreak())
                items.append(Paragraph("FMEA Tables", pdf_styles["Heading2"]))
                items.append(Spacer(1, 12))
                for fmea in self.fmeas:
                    items.append(Paragraph(fmea['name'], pdf_styles["Heading3"]))
                    data = [[
                        "Component",
                        "Parent",
                        "Failure Mode",
                        "Failure Effect",
                        "Cause",
                        "S",
                        "O",
                        "D",
                        "RPN",
                        "Requirements",
                        "Malfunction",
                    ]]
                    for be in fmea['entries']:
                        src = self.get_failure_mode_node(be)
                        comp = self.get_component_name_for_node(src) or "N/A"
                        parent = src.parents[0] if src.parents else None
                        parent_name = (
                            parent.user_name
                            if parent and getattr(parent, "node_type", "").upper() not in GATE_NODE_TYPES
                            else ""
                        )
                        req_ids = "; ".join([r.get("id") for r in getattr(be, 'safety_requirements', [])])
                        rpn = be.fmea_severity * be.fmea_occurrence * be.fmea_detection
                        failure_mode = be.description or (be.user_name or f"BE {be.unique_id}")
                        row = [
                            comp,
                            parent_name,
                            failure_mode,
                            be.fmea_effect,
                            getattr(be, 'fmea_cause', ''),
                            be.fmea_severity,
                            be.fmea_occurrence,
                            be.fmea_detection,
                            rpn,
                            req_ids,
                            getattr(be, 'fmeda_malfunction', ''),
                        ]
                        data.append(row)
                    table = Table(data, repeatRows=1)
                    table.setStyle(
                        TableStyle(
                            [
                                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                ("FONTSIZE", (0, 0), (-1, -1), 8),
                            ]
                        )
                    )
                    items.append(table)
                    items.append(Spacer(1, 12))
            return items

        def _element_fmeda_tables():
            items: list = []
            if getattr(self, "fmedas", []):
                items.append(PageBreak())
                items.append(Paragraph("FMEDA Tables", pdf_styles["Heading2"]))
                items.append(Spacer(1, 12))
                for fmeda in self.fmedas:
                    items.append(Paragraph(fmeda['name'], pdf_styles["Heading3"]))
                    data = [[
                        "Component",
                        "Parent",
                        "Failure Mode",
                        "Malfunction",
                        "Safety Goal",
                        "Fault Type",
                        "Fraction",
                        "FIT",
                        "DiagCov",
                        "Mechanism",
                    ]]
                    for be in fmeda['entries']:
                        src = self.get_failure_mode_node(be)
                        comp = self.get_component_name_for_node(src) or "N/A"
                        parent = src.parents[0] if src.parents else None
                        parent_name = (
                            parent.user_name
                            if parent and getattr(parent, "node_type", "").upper() not in GATE_NODE_TYPES
                            else ""
                        )
                        failure_mode = be.description or (be.user_name or f"BE {be.unique_id}")
                        row = [
                            comp,
                            parent_name,
                            failure_mode,
                            getattr(be, 'fmeda_malfunction', ''),
                            getattr(be, 'fmeda_safety_goal', ''),
                            getattr(be, 'fmeda_fault_type', ''),
                            f"{getattr(be, 'fmeda_fault_fraction', 0)}",
                            f"{getattr(be, 'fmeda_fit', 0)}",
                            f"{getattr(be, 'fmeda_diag_cov', 0)}",
                            getattr(be, 'fmeda_mechanism', ''),
                        ]
                        data.append(row)
                    table = Table(data, repeatRows=1)
                    table.setStyle(
                        TableStyle(
                            [
                                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                ("FONTSIZE", (0, 0), (-1, -1), 8),
                            ]
                        )
                    )
                    items.append(table)
                    items.append(Spacer(1, 12))
            return items

        def _element_traceability():
            items: list = []
            basic_events = [
                n
                for n in self.get_all_nodes(self.root_node)
                if n.node_type.upper() == "BASIC EVENT"
            ]
            if basic_events:
                items.append(PageBreak())
                items.append(Paragraph("FTA-FMEA Traceability", pdf_styles["Heading2"]))
                data = [["Basic Event", "Component"]]
                for be in basic_events:
                    comp = self.get_component_name_for_node(be) or "N/A"
                    data.append([be.user_name or f"BE {be.unique_id}", comp])
                table = Table(data, repeatRows=1)
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                            ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ]
                    )
                )
                items.append(table)
                items.append(Spacer(1, 12))
            return items

        def _element_cut_sets():
            items: list = []
            cut_sets_exist = any(self.calculate_cut_sets(te) for te in self.top_events)
            if cut_sets_exist:
                items.append(PageBreak())
                items.append(Paragraph("FTA Cut Sets", pdf_styles["Heading2"]))
                data = [["Top Event", "Cut Set #", "Basic Events"]]
                for te in self.top_events:
                    nodes_by_id = {}

                    def map_nodes(n):
                        nodes_by_id[n.unique_id] = n
                        for child in n.children:
                            map_nodes(child)

                    map_nodes(te)
                    cut_sets = self.calculate_cut_sets(te)
                    te_label = te.user_name or f"Top Event {te.unique_id}"
                    for idx, cs in enumerate(cut_sets, start=1):
                        names = ", ".join(
                            f"{nodes_by_id[uid].user_name or nodes_by_id[uid].node_type} [{uid}]"
                            for uid in sorted(cs)
                        )
                        data.append([te_label if idx == 1 else "", str(idx), names])
                        te_label = ""
                table = Table(data, repeatRows=1)
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ]
                    )
                )
                items.append(table)
                items.append(Spacer(1, 12))
            return items

        def _element_common_cause():
            items: list = []
            events_by_cause = {}
            for fmea in getattr(self, "fmeas", []):
                for be in fmea['entries']:
                    cause = be.description
                    label = f"{fmea['name']}:{be.user_name or be.description or be.unique_id}"
                    events_by_cause.setdefault(cause, set()).add(label)
            for fmeda in getattr(self, "fmedas", []):
                for be in fmeda['entries']:
                    cause = be.description
                    label = f"{fmeda['name']}:{be.user_name or be.description or be.unique_id}"
                    events_by_cause.setdefault(cause, set()).add(label)
            for be in self.get_all_basic_events():
                cause = be.description or ""
                label = be.user_name or f"BE {be.unique_id}"
                events_by_cause.setdefault(cause, set()).add(label)
            cc_rows = [[cause, ", ".join(sorted(evts))] for cause, evts in events_by_cause.items() if len(evts) > 1]
            if cc_rows:
                items.append(PageBreak())
                items.append(Paragraph("Common Cause Analysis", pdf_styles["Heading2"]))
                data = [["Cause", "Events"]] + cc_rows
                table = Table(data, repeatRows=1)
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ]
                    )
                )
                items.append(table)
                items.append(Spacer(1, 12))
            return items

        def _element_safety_security_reports():
            items: list = []
            library = getattr(self, "safety_case_library", None)
            if library and getattr(library, "cases", None):
                items.append(PageBreak())
                items.append(Paragraph("Safety & Security Reports", pdf_styles["Heading2"]))
                items.append(Spacer(1, 12))
                data = [["Name"]]
                for case in library.cases:
                    data.append([case.name])
                table = Table(data, repeatRows=1)
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ]
                    )
                )
                items.append(table)
                items.append(Spacer(1, 12))
            return items

        def _element_spi_table():
            items: list = []
            tree = getattr(self, "_spi_tree", None)
            if tree:
                columns = list(tree["columns"])
                data = [list(columns)]
                for iid in tree.get_children(""):
                    data.append(list(tree.item(iid, "values")))
                table = Table(data, repeatRows=1)
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ]
                    )
                )
                items.append(table)
                items.append(Spacer(1, 12))
            return items

        requirement_element_map = {
            "req_vehicle": ("vehicle", "Vehicle"),
            "req_operational": ("operational", "Operational"),
            "req_operational_safety": ("operational safety", "Operational Safety"),
            "req_functional_safety": ("functional safety", "Functional Safety"),
            "req_technical_safety": ("technical safety", "Technical Safety"),
            "req_ai_safety": ("AI safety", "AI Safety"),
            "req_functional_modification": ("functional modification", "Functional Modification"),
            "req_cybersecurity": ("cybersecurity", "Cybersecurity"),
            "req_production": ("production", "Production"),
            "req_service": ("service", "Service"),
            "req_field_monitoring": ("field monitoring", "Field Monitoring"),
            "req_decommissioning": ("decommissioning", "Decommissioning"),
            "req_product": ("product", "Product"),
            "req_legal": ("legal", "Legal"),
            "req_organizational": ("organizational", "Organizational"),
            "req_spi": ("spi", "Spi"),
        }

        def _make_requirement_table(req_type: str, title: str):
            items: list = []
            reqs = [
                r for r in global_requirements.values() if r.get("req_type") == req_type
            ]
            if reqs:
                items.append(PageBreak())
                items.append(Paragraph(f"{title} Requirements", pdf_styles["Heading2"]))
                items.append(Spacer(1, 12))
                data = [["ID", "Text", "ASIL", "CAL"]]
                for r in sorted(reqs, key=lambda x: x.get("id", "")):
                    data.append(
                        [
                            r.get("id", ""),
                            r.get("text", ""),
                            r.get("asil", ""),
                            r.get("cal", ""),
                        ]
                    )
                table = Table(data, repeatRows=1)
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ]
                    )
                )
                items.append(table)
                items.append(Spacer(1, 12))
            return items

        def _build_element(name: str, kind: str | None):
            if kind:
                if kind == "diagram":
                    label = name
                elif kind.startswith("diagram:"):
                    label = kind.split(":", 1)[1]
                else:
                    label = None
                if label is not None:
                    img = Image.new("RGB", (400, 200), "white")
                    if hasattr(img, "save"):
                        draw = ImageDraw.Draw(img)
                        if hasattr(draw, "rectangle"):
                            draw.rectangle([0, 0, 399, 199], outline="black")
                        if hasattr(draw, "text"):
                            draw.text((10, 10), f"{label} diagram", fill="black")
                        buf = BytesIO()
                        img.save(buf, format="PNG")
                        buf.seek(0)
                        return [RLImage(buf)]
                    return [Paragraph(f"[{label} diagram]", pdf_styles["Normal"])]
                if kind.startswith("analysis:"):
                    analysis_type = kind.split(":", 1)[1]
                    return [
                        Paragraph(
                            f"[{analysis_type} analysis from diagrams]",
                            pdf_styles["Normal"],
                        )
                    ]
            if kind == "base_matrix":
                return _element_base_matrix()
            if kind == "discretization":
                return _element_discretization()
            if kind == "hazop":
                return _element_hazop()
            if kind == "fi2tc":
                return _element_fi2tc()
            if kind == "tc2fi":
                return _element_tc2fi()
            if kind == "risk":
                return _element_risk()
            if kind == "cbn":
                return _element_cbn()
            if kind == "safety_goals":
                return _element_safety_goals()
            if kind == "top_events":
                return _element_top_events()
            if kind == "page_diagrams":
                return _element_page_diagrams()
            if kind == "sysml_diagrams":
                return _element_sysml_diagrams()
            if kind == "fmea_tables":
                return _element_fmea_tables()
            if kind == "fmeda_tables":
                return _element_fmeda_tables()
            if kind == "traceability":
                return _element_traceability()
            if kind == "cut_sets":
                return _element_cut_sets()
            if kind == "common_cause":
                return _element_common_cause()
            if kind == "safety_security_reports":
                return _element_safety_security_reports()
            if kind == "spi_table":
                return _element_spi_table()
            if kind == "activity_actions":
                data = [["Action"], ["Start"], ["Stop"]]
                table = Table(data, repeatRows=1)
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ]
                    )
                )
                return [table]
            if kind == "req_matrix_alloc":
                data = [["Requirement", "Allocation"], ["REQ-1", "Block A"], ["REQ-2", "Block B"]]
                table = Table(data, repeatRows=1)
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ]
                    )
                )
                return [table]
            if kind == "product_goals":
                return [
                    Paragraph("Goal 1", pdf_styles["Normal"]),
                    Paragraph("Goal 2", pdf_styles["Normal"]),
                ]
            if kind == "fsc_info":
                return [
                    Paragraph(
                        "[functional safety concept information]",
                        pdf_styles["Normal"],
                    )
                ]
            if kind == "trace_matrix_pg_fsr":
                data = [["Product Goal", "FSR"], ["PG1", "FSR1"], ["PG2", "FSR2"]]
                table = Table(data, repeatRows=1)
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ]
                    )
                )
                return [table]
            if kind == "trace_matrix_fsc":
                data = [["TSR", "FSR"], ["TSR1", "FSR1"], ["TSR2", "FSR2"]]
                table = Table(data, repeatRows=1)
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ]
                    )
                )
                return [table]
            if kind == "item_description":
                text = getattr(self, "item_definition", {}).get("description", "")
                if not text:
                    text = "[item description]"
                return [Paragraph(text, pdf_styles["Normal"])]
            if kind == "assumptions":
                text = getattr(self, "item_definition", {}).get("assumptions", "")
                if not text:
                    text = "[assumptions]"
                return [Paragraph(text, pdf_styles["Normal"])]
            if name in requirement_element_map:
                req_type, title = requirement_element_map[name]
                return _make_requirement_table(req_type, title)
            return [Paragraph(f"[{name}]", styles["Normal"])]

        elements = template.get("elements", {})
        import re as _re

        def _tokenize(text: str):
            replaced = text
            for placeholder in elements:
                replaced = replaced.replace(
                    f"<{placeholder}>", f"[[[element:{placeholder}]]]"
                )
            replaced = _re.sub(
                r'<img\s+src="([^"]+)"\s*/?>',
                lambda m: f"[[[img:{m.group(1)}]]]",
                replaced,
            )
            replaced = _re.sub(
                r'<a\s+href="([^"]+)">([^<]*)</a>',
                lambda m: f"[[[link:{m.group(1)}|{m.group(2)}]]]",
                replaced,
            )
            return _re.split(r"(\[\[\[[^\]]+\]\]\])", replaced)

        for sec in template.get("sections", []):
            story.append(Paragraph(sec.get("title", ""), styles["Heading2"]))
            tokens = _tokenize(sec.get("content", ""))
            for tok in tokens:
                if not tok:
                    continue
                if tok.startswith("[[[") and tok.endswith("]]]"):
                    inner = tok[3:-3]
                    if inner.startswith("element:"):
                        name = inner.split(":", 1)[1]
                        story.extend(_build_element(name, elements.get(name)))
                    elif inner.startswith("img:"):
                        src = inner.split(":", 1)[1]
                        try:
                            story.append(RLImage(src))
                        except Exception:
                            story.append(
                                Paragraph(f"[Missing image: {src}]", styles["Normal"])
                            )
                    elif inner.startswith("link:"):
                        href, text = inner.split(":", 1)[1].split("|", 1)
                        story.append(
                            Paragraph(
                                f'<link href="{href}">{text}</link>', styles["Normal"]
                            )
                        )
                else:
                    text = tok.strip()
                    if text:
                        for line in text.split("\n"):
                            if line:
                                story.append(Paragraph(line, styles["Normal"]))
            story.append(Spacer(1, 12))

        try:
            doc.build(story)
            json_path = Path(path).with_suffix(".json")
            json_path.write_text(json.dumps(template, indent=2))
            lines = logger.log_message(
                f"PDF report generated at {path}",
                level="INFO",
            )
            logger.show_temporarily(lines=lines)
        except Exception as exc:
            lines = logger.log_message(
                f"Failed to generate PDF: {exc}",
                level="ERROR",
            )
            logger.show_temporarily(lines=lines)

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
            "safety_mgmt_toolbox": (
                app.safety_mgmt_toolbox.to_dict()
                if getattr(app, "safety_mgmt_toolbox", None)
                else {}
            ),
            "enabled_work_products": list(
                getattr(app, "enabled_work_products", [])
            ),
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
