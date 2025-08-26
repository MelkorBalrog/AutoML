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

"""Fault tree analysis helpers separated from the main application."""

import re

from analysis.fmeda_utils import GATE_NODE_TYPES
if __package__ and __package__.startswith("AutoML"):
    from AutoML.config.automl_constants import dynamic_recommendations, VALID_SUBTYPES
else:  # pragma: no cover - script context
    from config.automl_constants import dynamic_recommendations, VALID_SUBTYPES
from gui.controls import messagebox
from mainappsrc.models.fta.fault_tree_node import FaultTreeNode


class FTASubApp:
    """Encapsulate fault-tree specific behaviours."""

    def generate_recommendations_for_top_event(self, app, node):
        level = app.helper.discretize_level(node.quant_value) if node.quant_value is not None else 1
        rec = dynamic_recommendations.get(level, {})
        rec_text = f"<b>Recommendations for Prototype Assurance Level (PAL) {level}:</b><br/>"
        for category in [
            "Testing Requirements",
            "IFTD Responsibilities",
            "Preventive Maintenance Actions",
            "Relevant AVSC Guidelines",
        ]:
            if category in rec:
                rec_text += f"<b>{category}:</b><br/><ul><li>{rec[category]}</li></ul><br/>"
        return rec_text

    def back_all_pages(self, app):
        if app.page_history:
            first_page = app.page_history[0]
            app.page_history = []
            for widget in app.canvas_frame.winfo_children():
                widget.destroy()
            app.window_controllers.open_page_diagram(first_page)
        else:
            app.close_page_diagram()

    def move_top_event_up(self, app):
        sel = app.analysis_tree.selection()
        if not sel:
            messagebox.showwarning("Move Up", "Select a top-level event to move.")
            return
        try:
            node_id = int(app.analysis_tree.item(sel[0], "tags")[0])
        except Exception:
            return
        index = next((i for i, event in enumerate(app.top_events) if event.unique_id == node_id), None)
        if index is None:
            messagebox.showwarning("Move Up", "The selected node is not a top-level event.")
            return
        if index == 0:
            messagebox.showinfo("Move Up", "This event is already at the top.")
            return
        app.top_events[index], app.top_events[index - 1] = app.top_events[index - 1], app.top_events[index]
        app.update_views()

    def move_top_event_down(self, app):
        sel = app.analysis_tree.selection()
        if not sel:
            messagebox.showwarning("Move Down", "Select a top-level event to move.")
            return
        try:
            node_id = int(app.analysis_tree.item(sel[0], "tags")[0])
        except Exception:
            return
        index = next((i for i, event in enumerate(app.top_events) if event.unique_id == node_id), None)
        if index is None:
            messagebox.showwarning("Move Down", "The selected node is not a top-level event.")
            return
        if index == len(app.top_events) - 1:
            messagebox.showinfo("Move Down", "This event is already at the bottom.")
            return
        app.top_events[index], app.top_events[index + 1] = app.top_events[index + 1], app.top_events[index]
        app.update_views()

    def get_top_level_nodes(self, app):
        all_nodes = app.get_all_nodes()
        return [node for node in all_nodes if not node.parents]

    def get_all_nodes_no_filter(self, app, node):
        nodes = [node]
        for child in node.children:
            nodes.extend(self.get_all_nodes_no_filter(app, child))
        return nodes

    def derive_requirements_for_event(self, app, event):
        req_set = set()
        for node in self.get_all_nodes(app, event):
            if hasattr(node, "safety_requirements"):
                for req in node.safety_requirements:
                    req_set.add(f"[{req['id']}] [{req['req_type']}] {req['text']}")
        return req_set

    def get_combined_safety_requirements(self, app, node):
        req_list = []
        if hasattr(node, "safety_requirements") and node.safety_requirements:
            req_list.extend(node.safety_requirements)
        if not node.is_primary_instance and hasattr(node, "original") and node.original.safety_requirements:
            req_list.extend(node.original.safety_requirements)
        return req_list

    def get_top_event(self, app, node):
        current = node
        while current.parents:
            for parent in current.parents:
                if parent.node_type.upper() == "TOP EVENT":
                    return parent
            current = current.parents[0]
        return node

    def aggregate_safety_requirements(self, app, node, all_nodes):
        aggregated = set()
        for req in node.get("safety_requirements", []):
            aggregated.add(req["id"])
        if node.get("original_id"):
            original = all_nodes.get(node["original_id"])
            if original:
                aggregated.update(self.aggregate_safety_requirements(app, original, all_nodes))
        for parent in node.get("parents", []):
            for req in parent.get("safety_requirements", []):
                aggregated.add(req["id"])
        for child in node.get("children", []):
            aggregated.update(self.aggregate_safety_requirements(app, child, all_nodes))
        node["aggregated_safety_requirements"] = sorted(aggregated)
        return aggregated

    def generate_top_event_summary(self, app, top_event):
        all_nodes = self.get_all_nodes_no_filter(app, top_event)
        base_nodes = [n for n in all_nodes if n.node_type.upper() in ["CONFIDENCE LEVEL", "ROBUSTNESS SCORE"]]
        bullet_lines = []
        for bn in base_nodes:
            orig = bn if bn.is_primary_instance else bn.original
            identifier = orig.name if orig.name else f"Node {orig.unique_id}"
            score = f"{orig.quant_value:.2f}" if orig.quant_value is not None else "N/A"
            rationale = orig.rationale.strip() if orig.rationale and orig.rationale.strip() != "" else "No rationale provided"
            bullet_lines.append(f"• {identifier}: Score = {score}, Rationale: {rationale}")
        base_summary = "\n".join(bullet_lines) if bullet_lines else "No base nodes available."
        overall_assurance = top_event.quant_value if top_event.quant_value is not None else 1.0
        if overall_assurance >= 4.5:
            assurance_descr = "PAL5"
        elif overall_assurance >= 3.5:
            assurance_descr = "PAL4"
        elif overall_assurance >= 2.5:
            assurance_descr = "PAL3"
        elif overall_assurance >= 1.5:
            assurance_descr = "PAL2"
        else:
            assurance_descr = "PAL1"
        try:
            overall_severity = float(top_event.severity) if top_event.severity is not None else 3.0
        except Exception:
            overall_severity = 3.0
        try:
            overall_cont = float(top_event.controllability) if top_event.controllability is not None else 3.0
        except Exception:
            overall_cont = 3.0
        summary_sentence = (
            f"Top-Level Event: {top_event.name}\n\n"
            f"Assurance Requirement:\n"
            f"  - Required Prototype Assurance Level (PAL): {assurance_descr} (Score: {overall_assurance:.2f})\n"
            f"  - Severity Rating: {overall_severity:.2f}\n"
            f"  - Controllability: {overall_cont:.2f}\n\n"
            f"Rationale:\n"
            f"  Based on analysis of its base nodes, the following factors contributed to this level:\n"
            f"{base_summary}"
        )
        return summary_sentence

    def get_all_nodes(self, app, node=None):
        if node is None:
            result = []
            for te in app.top_events:
                result.extend(self.get_all_nodes(app, te))
            return result

        visited = set()

        def rec(n):
            if n.unique_id in visited:
                return []
            visited.add(n.unique_id)
            if n != app.root_node and any(parent.is_page for parent in n.parents):
                return []
            result = [n]
            for c in n.children:
                result.extend(rec(c))
            return result

        return rec(node)

    def get_all_nodes_table(self, app, root_node):
        collector = []

        def rec(n):
            collector.append(n)
            for child in n.children:
                rec(child)

        rec(root_node)
        return collector

    def get_all_nodes_in_model(self, app):
        all_nodes = []
        events = app.top_events + getattr(app, "cta_events", []) + getattr(app, "paa_events", [])
        for te in events:
            nodes = self.get_all_nodes_table(app, te)
            all_nodes.extend(nodes)
        return all_nodes

    def get_all_basic_events(self, app):
        return [n for n in self.get_all_nodes_in_model(app) if n.node_type.upper() == "BASIC EVENT"]

    def get_all_gates(self, app):
        return [n for n in self.get_all_nodes_in_model(app) if n.node_type.upper() in GATE_NODE_TYPES]

    def metric_to_text(self, app, metric_type, value):
        if value is None:
            return "unknown"
        disc = app.helper.discretize_level(value)
        if metric_type == "maturity":
            return "high maturity" if disc == 5 else "low maturity" if disc == 1 else f"a maturity of {disc}"
        elif metric_type == "rigor":
            return "high rigor" if disc == 5 else "low rigor" if disc == 1 else f"a rigor of {disc}"
        elif metric_type == "severity":
            return "high severity" if disc >= 3 else "low severity" if disc == 1 else f"a severity of {disc}"
        else:
            return str(disc)

    def assurance_level_text(self, level):
        mapping = {1: "PAL1", 2: "PAL2", 3: "PAL3", 4: "PAL4", 5: "PAL5"}
        return mapping.get(level, str(level))

    def calculate_cut_sets(self, app, node):
        if not node.children:
            return [{node.unique_id}]
        gate = (node.gate_type or "AND").upper() if node.node_type.upper() in GATE_NODE_TYPES else "AND"
        child_cut_sets = [self.calculate_cut_sets(app, child) for child in node.children]
        if gate == "OR":
            result = []
            for cuts in child_cut_sets:
                result.extend(cuts)
            return result
        elif gate == "AND":
            result = [set()]
            for cuts in child_cut_sets:
                temp = []
                for partial in result:
                    for cs in cuts:
                        temp.append(partial.union(cs))
                result = temp
            return result
        else:
            result = []
            for cuts in child_cut_sets:
                result.extend(cuts)
            return result

    def build_hierarchical_argumentation(self, app, node, indent=0):
        indent_str = "    " * indent
        node_name = node.user_name if node.user_name else f"Node {node.unique_id}"
        details = f"{node.node_type}"
        if node.input_subtype:
            details += f" ({node.input_subtype})"
        if node.description:
            details += f": {node.description}"
        metric_type = "maturity" if node.node_type.upper() in ["CONFIDENCE LEVEL", "ROBUSTNESS SCORE"] else "rigor"
        metric_descr = self.metric_to_text(app, metric_type, node.quant_value)
        line = f"{indent_str}- {node_name} ({details}) -> {metric_descr}"
        if node.rationale and node.node_type.upper() not in ["CONFIDENCE LEVEL", "ROBUSTNESS SCORE"]:
            line += f" [Rationale: {node.rationale.strip()}]"
        child_lines = [self.build_hierarchical_argumentation(app, child, indent + 1) for child in node.children]
        if child_lines:
            line += "\n" + "\n".join(child_lines)
        return line

    def build_hierarchical_argumentation_common(self, app, node, indent=0, described=None):
        if described is None:
            described = set()
        indent_str = "    " * indent
        node_name = node.user_name if node.user_name else f"Node {node.unique_id}"
        if node.unique_id not in described:
            details = f"{node.node_type}"
            if node.input_subtype:
                details += f" ({node.input_subtype})"
            if node.description:
                details += f": {node.description}"
            described.add(node.unique_id)
        else:
            details = f"{node.node_type} (see common cause: {node_name})"
        metric_type = "maturity" if node.node_type.upper() in ["CONFIDENCE LEVEL", "ROBUSTNESS SCORE"] else "rigor"
        metric_descr = self.metric_to_text(app, metric_type, node.quant_value)
        line = f"{indent_str}- {node_name} ({details}) -> {metric_descr}"
        if node.rationale and node.node_type.upper() not in ["CONFIDENCE LEVEL", "ROBUSTNESS SCORE"]:
            line += f" [Rationale: {node.rationale.strip()}]"
        child_lines = [self.build_hierarchical_argumentation_common(app, child, indent + 1, described) for child in node.children]
        if child_lines:
            line += "\n" + "\n".join(child_lines)
        return line

    def build_page_argumentation(self, app, page_node):
        return self.build_hierarchical_argumentation(app, page_node)

    def build_unified_recommendation_table(self, app):
        from reportlab.platypus import LongTable, Paragraph
        from reportlab.lib import colors
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.platypus import TableStyle

        style_sheet = getSampleStyleSheet()
        body_style = style_sheet["BodyText"]
        header_style = ParagraphStyle(
            name="RecHeader",
            parent=body_style,
            fontSize=5,
            leading=6,
            wordWrap="CJK",
            alignment=1,
        )

        all_nodes = self.get_all_nodes_in_model(app)
        if not all_nodes:
            return None
        primary_nodes = [n for n in all_nodes if n.is_primary_instance]
        rec_to_nodes = {}
        for node in primary_nodes:
            if node.quant_value is not None and node.description:
                discrete = app.helper.discretize_level(node.quant_value)
                extra_dict = dynamic_recommendations.get(discrete, {}).get("Extra Recommendations", {})
                desc_lower = node.description.lower()
                for keyword, rec_text in extra_dict.items():
                    if keyword.lower() in desc_lower:
                        rec_to_nodes.setdefault(rec_text, []).append(node)
        if not rec_to_nodes:
            return None
        data = [[
            Paragraph("<b>Extra Recommendation</b>", header_style),
            Paragraph("<b>Metric Details</b>", header_style),
        ]]
        for rec_text, nodes in rec_to_nodes.items():
            first_row = True
            for node in nodes:
                metric_str = (
                    node.display_label
                    if node.display_label and not node.display_label.startswith("Node")
                    else (f"{node.quant_value:.2f}" if node.quant_value is not None else "N/A")
                )
                desc = (node.description or "N/A").strip().replace("\n", "<br/>")
                rat = (node.rationale or "N/A").strip().replace("\n", "<br/>")
                node_details = (
                    f"{node.unique_id}: {node.name}" \
                    f"<br/><b>Metric:</b> {metric_str}" \
                    f"<br/><b>Description:</b> {desc}" \
                    f"<br/><b>Rationale:</b> {rat}"
                )
                if first_row:
                    data.append([Paragraph(rec_text, body_style), Paragraph(node_details, body_style)])
                    first_row = False
                else:
                    data.append(["", Paragraph(node_details, body_style)])

        col_widths = [200, 450]
        table = LongTable(data, colWidths=col_widths, repeatRows=1, splitByRow=True)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.orange),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTSIZE", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 2),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        return table

    def get_extra_recommendations_list(self, app, description, level):
        if not description:
            return []
        desc = description.lower()
        level_extras = dynamic_recommendations.get(level, {}).get("Extra Recommendations", {})
        rec_list = []
        for keyword, rec in level_extras.items():
            if keyword.lower() in desc:
                rec_list.append(rec)
        return rec_list

    def get_extra_recommendations_from_level(self, app, description, level):
        if not description:
            return ""
        desc = description.lower()
        level_extras = dynamic_recommendations.get(level, {}).get("Extra Recommendations", {})
        malfunction_words = ["unintended", "no", "not", "excessive", "incorrect"]
        recommendations = []
        for keyword, rec in level_extras.items():
            if re.search(r"\b" + re.escape(keyword) + r"\b", desc):
                pattern = r"\b" + re.escape(keyword) + r"\b(?:\W+\w+){0,5}\W+(?:" + "|".join(malfunction_words) + r")\b"
                if re.search(pattern, desc):
                    recommendations.append(rec)
        if recommendations:
            return "\nExtra Testing Recommendations:\n" + "\n".join(f"- {r}" for r in recommendations)
        return ""

    def get_recommendation_from_description(self, app, description, level):
        if not description:
            return ""
        desc = description.lower()
        level_extras = dynamic_recommendations.get(level, {}).get("Extra Recommendations", {})
        rec_list = []
        for keyword, rec in level_extras.items():
            if keyword.lower() in desc:
                rec_list.append(rec)
        return " ".join(rec_list)

    def build_argumentation(self, app, node):
        if not node.children:
            return ""
        header = ""
        if node.node_type.upper() == "TOP EVENT":
            disc = app.helper.discretize_level(node.quant_value)
            assurance_descr = self.assurance_level_text(disc)
            severity_str = f"{node.severity}" if node.severity is not None else "N/A"
            controllability_str = f"{node.controllability}" if node.controllability is not None else "N/A"
            header += (
                "Prototype Assurance Level (PAL) Explanation:<br/>"
                f"Based on the aggregated scores of its child nodes, this top event has been assigned an Prototype Assurance Level (PAL) of <b>{assurance_descr}</b> "
                f"with a severity rating of <b>{severity_str}</b> and controllability <b>{controllability_str}</b>.<br/><br/>"
            )
            header += self.generate_recommendations_for_top_event(app, node) + "<br/>"
        nodes_by_id = {}

        def map_nodes(n):
            nodes_by_id[n.unique_id] = n
            for child in n.children:
                map_nodes(child)

        map_nodes(node)
        cut_sets = self.calculate_cut_sets(app, node)
        cut_set_table = "Cut Set Table:<br/>"
        for i, cs in enumerate(cut_sets, start=1):
            cs_ids = ", ".join(f"Node {uid}" for uid in sorted(cs))
            cut_set_table += f"Cut Set {i}: {cs_ids}<br/>"
        node_definitions = "Node Definitions:<br/>"
        unique_ids = set()
        for cs in cut_sets:
            unique_ids.update(cs)
        for uid in sorted(unique_ids):
            n = nodes_by_id.get(uid)
            if n is None:
                continue
            subtype = (
                n.input_subtype
                if n.input_subtype is not None
                else (VALID_SUBTYPES["Confidence"][0] if n.node_type.upper() == "CONFIDENCE LEVEL" else VALID_SUBTYPES.get("Prototype Assurance Level (PAL)", ["Default"])[0])
            )
            desc = n.description.strip() if n.description else "No description provided."
            node_definitions += f"Node {uid}: {n.name}<br/>"
            node_definitions += f"Type: {n.node_type}, Subtype: {subtype}<br/>"
            node_definitions += f"Description: {desc}<br/><br/>"
        diagram_note = "Cause-and-Effect Diagram is generated below.<br/>"
        return header + cut_set_table + "<br/>" + node_definitions + "<br/>" + diagram_note

    def auto_create_argumentation(self, app, node, suppress_top_event_recommendations=False):
        level = app.helper.discretize_level(node.quant_value) if node.quant_value is not None else 1
        if node.node_type.upper() == "TOP EVENT" and not suppress_top_event_recommendations:
            assurance_descr = self.assurance_level_text(level)
            severity_str = f"{node.severity}" if node.severity is not None else "N/A"
            controllability_str = f"{node.controllability}" if node.controllability is not None else "N/A"
            header = (
                f"Prototype Assurance Level (PAL) Explanation:\n"
                f"This top event is assigned an Prototype Assurance Level (PAL) of '{assurance_descr}' with a severity rating of {severity_str} and controllability {controllability_str}.\n\n"
            )
            rec_from_desc = self.get_recommendation_from_description(app, node.description, level)
            if rec_from_desc:
                base_arg = header + "Dynamic Recommendation:\n" + rec_from_desc
            else:
                rec = dynamic_recommendations.get(level, {})
                rec_lines = []
                for category in ["Testing Requirements", "IFTD Responsibilities", "Preventive Maintenance Actions", "Relevant AVSC Guidelines"]:
                    if category in rec:
                        rec_lines.append(f"{category}: {rec[category]}")
                rec_text = "\n".join(rec_lines)
                base_arg = header + "Recommendations:\n" + rec_text
        elif node.node_type.upper() == "TOP EVENT" and suppress_top_event_recommendations:
            base_arg = (
                f"Top Event: Input score: {node.quant_value:.2f}"
                if node.quant_value is not None
                else "Top Event: No input score provided."
            )
        else:
            base_arg = (
                f"Input score: {node.quant_value:.2f}"
                if node.quant_value is not None
                else "No input score provided."
            )
        own_text = ""
        if node.description:
            own_text += f"Description: {node.description}\n"
        if node.rationale and node.node_type.upper() not in ["CONFIDENCE LEVEL", "ROBUSTNESS SCORE"]:
            own_text += f"Rationale: {node.rationale}\n"
        if node.safety_requirements:
            reqs = ", ".join(r.get("id", "") for r in node.safety_requirements)
            own_text += f"Linked Safety Requirements: {reqs}"
        if node.node_type.upper() != "TOP EVENT" and not node.children:
            rec_from_desc = self.get_recommendation_from_description(app, node.description, level)
            if rec_from_desc:
                own_text += f"\nExtra Recommendations: {rec_from_desc}"
        return base_arg + ("\n" + own_text if own_text else "")

    def analyze_common_causes(self, app, node):
        occurrence = {}

        def traverse(n):
            if n.unique_id in occurrence:
                occurrence[n.unique_id]["count"] += 1
            else:
                occurrence[n.unique_id] = {"node": n, "count": 1}
            for child in n.children:
                traverse(child)

        traverse(node)
        report_lines = ["Common Cause Analysis:"]
        for uid, info in occurrence.items():
            if info["count"] > 1:
                n = info["node"]
                name = n.user_name if n.user_name else f"Node {n.unique_id}"
                report_lines.append(
                    f" - {name} (Type: {n.node_type}) appears {info['count']} times. Description: {n.description or 'No description'}"
                )
        if len(report_lines) == 1:
            report_lines.append(" None found.")
        return "\n".join(report_lines)

    def build_text_report(self, app, node, indent=0):
        report = "    " * indent + f"{node.name} ({node.node_type}"
        if node.node_type.upper() in GATE_NODE_TYPES:
            report += f", {node.gate_type}"
        report += ")"
        if node.display_label:
            report += f" => {node.display_label}"
        arg_text = self.build_argumentation(app, node)
        if arg_text:
            report += f"\n{'    ' * (indent + 1)}Argumentation: {arg_text}"
        report += "\n\n"
        for child in node.children:
            report += self.build_text_report(app, child, indent + 1)
        return report

    def all_children_are_base_events(self, app, node):
        if not node.children:
            return False
        for child in node.children:
            t = child.node_type.upper()
            if t not in ["CONFIDENCE LEVEL", "ROBUSTNESS SCORE"]:
                return False
        return True

    def build_simplified_fta_model(self, app, top_event):
        nodes = []
        edges = []
        visited = set()

        def traverse(node):
            if node.unique_id in visited:
                return
            visited.add(node.unique_id)
            node_type_up = node.node_type.upper()
            node_info = {"id": str(node.unique_id), "label": node.name}
            if node_type_up in GATE_NODE_TYPES and not self.all_children_are_base_events(app, node):
                node_info["gate_type"] = node.gate_type
            if getattr(node, "input_subtype", ""):
                node_info["subtype"] = node.input_subtype
            nodes.append(node_info)
            for child in getattr(node, "children", []):
                edges.append({"source": str(node.unique_id), "target": str(child.unique_id)})
                traverse(child)

        traverse(top_event)
        return {"nodes": nodes, "edges": edges}

    @staticmethod
    def auto_generate_fta_diagram(fta_model, output_path):
        import networkx as nx
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np
        import math

        G = nx.DiGraph()
        node_labels = {}
        node_colors = {}
        for node in fta_model["nodes"]:
            node_id = node["id"]
            label = node.get("label", f"Node {node_id}")
            gate_type = node.get("gate_type", "")
            if gate_type:
                label += f"\n({gate_type.upper()})"
            G.add_node(node_id)
            node_labels[node_id] = label
            subtype = node.get("subtype", "").lower()
            if "vehicle level function" in subtype:
                node_colors[node_id] = "lightcoral"
            elif "ai error" in subtype:
                node_colors[node_id] = "lightyellow"
            elif "failure" in subtype:
                node_colors[node_id] = "lightblue"
            elif "functional insufficiency" in subtype:
                node_colors[node_id] = "lightgreen"
            else:
                node_colors[node_id] = "white"
        for edge in fta_model["edges"]:
            src = edge["source"]
            tgt = edge["target"]
            if not G.has_node(src) or not G.has_node(tgt):
                continue
            G.add_edge(src, tgt)
        if fta_model["nodes"]:
            top_event_id = fta_model["nodes"][0]["id"]
        else:
            img = Image.new("RGB", (400, 300), "white")
            draw = ImageDraw.Draw(img)
            draw.text((200, 150), "No nodes to display", fill="black", anchor="mm")
            img.save(output_path)
            return
        layers = {}
        layers[top_event_id] = 0
        queue = [top_event_id]
        visited = set([top_event_id])
        while queue:
            current = queue.pop(0)
            current_layer = layers[current]
            for child in G.successors(current):
                if child not in visited:
                    visited.add(child)
                    layers[child] = current_layer + 1
                    queue.append(child)
        max_layer = max(layers.values()) if layers else 0
        for n in G.nodes():
            if n not in layers:
                max_layer += 1
                layers[n] = max_layer
        layer_dict = {}
        for node_id, layer in layers.items():
            layer_dict.setdefault(layer, []).append(node_id)
        horizontal_gap = 2.0
        vertical_gap = 1.0
        pos = {}
        for layer in sorted(layer_dict.keys()):
            node_list = layer_dict[layer]

            def avg_parent_position(n):
                parents = list(G.predecessors(n))
                if not parents:
                    return 0
                return sum(layer_dict[layers[p]].index(p) for p in parents) / len(parents)

            node_list.sort(key=avg_parent_position)
            middle = (len(node_list) - 1) / 2.0
            for i, n in enumerate(node_list):
                x = layer * horizontal_gap
                y = (i - middle) * vertical_gap
                pos[n] = (x, y)

        def get_node_bbox(p, box_size=0.3):
            return (p[0] - box_size, p[1] - box_size, p[0] + box_size, p[1] + box_size)

        def bboxes_overlap(b1, b2):
            return not (b1[2] < b2[0] or b1[0] > b2[2] or b1[3] < b2[1] or b1[1] > b2[3])

        for n1 in pos:
            for n2 in pos:
                if n1 == n2:
                    continue
                if bboxes_overlap(get_node_bbox(pos[n1]), get_node_bbox(pos[n2])):
                    pos[n2] = (pos[n2][0], pos[n2][1] - 0.5)

        max_x = max(p[0] for p in pos.values()) if pos else 0
        max_y = max(abs(p[1]) for p in pos.values()) if pos else 0
        width = int((max_x + 1) * 200)
        height = int((max_y + 1) * 200)
        img = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()
        for node_id, (x, y) in pos.items():
            px = int(x * 200)
            py = int((y + max_y) * 200)
            color = node_colors.get(node_id, "white")
            draw.rectangle([px - 40, py - 20, px + 40, py + 20], fill=color, outline="black")
            draw.text((px, py), node_labels[node_id], fill="black", anchor="mm", font=font)
        for src, tgt in G.edges():
            x1, y1 = pos[src]
            x2, y2 = pos[tgt]
            draw.line([
                int(x1 * 200), int((y1 + max_y) * 200), int(x2 * 200), int((y2 + max_y) * 200)
            ], fill="black")
        img.save(output_path)
