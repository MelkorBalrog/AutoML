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

import sys
import json
import types
from pathlib import Path

# Stub required third-party modules before importing application modules
PIL_stub = types.ModuleType("PIL")
PIL_stub.Image = types.SimpleNamespace(new=lambda *a, **k: None)
PIL_stub.ImageDraw = types.SimpleNamespace(
    Draw=lambda *a, **k: types.SimpleNamespace(
        rectangle=lambda *a, **k: None, text=lambda *a, **k: None
    )
)
PIL_stub.ImageTk = types.SimpleNamespace()
PIL_stub.ImageFont = types.SimpleNamespace()
sys.modules.setdefault("PIL", PIL_stub)
sys.modules.setdefault("PIL.Image", PIL_stub.Image)
sys.modules.setdefault("PIL.ImageDraw", PIL_stub.ImageDraw)
sys.modules.setdefault("PIL.ImageTk", PIL_stub.ImageTk)
sys.modules.setdefault("PIL.ImageFont", PIL_stub.ImageFont)

from AutoML import AutoMLApp, filedialog


def test_generate_pdf_report_exports_template(tmp_path, monkeypatch):
    pdf_path = tmp_path / "out.pdf"
    template_path = tmp_path / "template.json"
    template_path.write_text(json.dumps({"elements": {}, "sections": []}))

    monkeypatch.setattr(filedialog, "asksaveasfilename", lambda **k: str(pdf_path))
    monkeypatch.setattr(filedialog, "askopenfilename", lambda **k: str(template_path))

    app = type("A", (), {"project_properties": {}, "_generate_pdf_report": AutoMLApp._generate_pdf_report})()
    app._generate_pdf_report()

    assert pdf_path.exists()
    assert pdf_path.with_suffix(".json").exists()


def test_generate_pdf_report_handles_diagram_and_analysis(tmp_path, monkeypatch):
    pdf_path = tmp_path / "out.pdf"
    template_path = tmp_path / "template.json"
    template_path.write_text(
                json.dumps(
                    {
                        "elements": {
                            "bd": "diagram:block",
                            "haz": "analysis:hazard",
                            "thr": "analysis:threat",
                            "fta": "analysis:fault_tree",
                            "fmea": "analysis:fmea",
                            "fmeda": "analysis:fmeda",
                        },
                        "sections": [
                            {"title": "T", "content": "<bd><haz><thr><fta><fmea><fmeda>"}
                        ],
                    }
                )
            )
    monkeypatch.setattr(filedialog, "asksaveasfilename", lambda **k: str(pdf_path))
    monkeypatch.setattr(filedialog, "askopenfilename", lambda **k: str(template_path))
    app = type("A", (), {"project_properties": {}, "_generate_pdf_report": AutoMLApp._generate_pdf_report})()
    app.fi2tc_docs = []
    app.tc2fi_docs = []
    app._generate_pdf_report()
    assert pdf_path.exists()
    assert pdf_path.with_suffix(".json").exists()


def test_generate_pdf_report_handles_extended_placeholders(tmp_path, monkeypatch):
    pdf_path = tmp_path / "out.pdf"
    template_path = tmp_path / "template.json"
    template_path.write_text(
        json.dumps(
                    {
                        "elements": {
                            "uc": "diagram:use case",
                            "act": "diagram:activity",
                            "ibd": "diagram:internal block",
                            "aa": "activity_actions",
                            "rm": "req_matrix_alloc",
                            "pg": "product_goals",
                            "fsc": "fsc_info",
                            "tr1": "trace_matrix_pg_fsr",
                            "tr2": "trace_matrix_fsc",
                            "desc": "item_description",
                            "asm": "assumptions",
                            "odd": "odd_library",
                            "scen": "scenario_library",
                            "rel": "analysis:reliability",
                            "mp": "mission_profile",
                            "pmhf": "pmhf",
                            "spfm": "spfm",
                            "lpfm": "lpfm",
                            "dc": "dc",
                            "sc": "safety_case",
                            "thr": "analysis:threat",
                            "fi2tc": "fi2tc",
                            "tc2fi": "tc2fi",
                            "trig": "triggering_conditions",
                            "fi": "functional_insufficiencies",
                            "fmod": "functional_modifications",
                            "spi": "spi_table",
                        },
                        "sections": [
                            {
                                "title": "T",
                                "content": "<uc><act><ibd><aa><rm><pg><fsc><tr1><tr2><desc><asm><odd><scen><rel><mp><pmhf><spfm><lpfm><dc><sc><thr><fi2tc><tc2fi><trig><fi><fmod><spi>",
                            }
                        ],
                    }
                )
    )
    monkeypatch.setattr(filedialog, "asksaveasfilename", lambda **k: str(pdf_path))
    monkeypatch.setattr(filedialog, "askopenfilename", lambda **k: str(template_path))
    app = type("A", (), {"project_properties": {}, "_generate_pdf_report": AutoMLApp._generate_pdf_report})()
    app.fi2tc_docs = []
    app.tc2fi_docs = []
    app._generate_pdf_report()
    assert pdf_path.exists()
    assert pdf_path.with_suffix(".json").exists()
