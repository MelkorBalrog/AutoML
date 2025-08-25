# Author: Miguel Marina <karel.capek.robotics@gmail.com>
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
import os
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

tk_msg = types.ModuleType("tkinter.messagebox")
tk_msg.showerror = lambda *a, **k: None
tk_msg.showinfo = lambda *a, **k: None
sys.modules.setdefault("tkinter.messagebox", tk_msg)

rl_platypus = types.ModuleType("reportlab.platypus")

class DummyDoc:
    def __init__(self, path, *a, **k):
        self.path = path

    def build(self, *a, **k):
        Path(self.path).write_text("pdf")


class Dummy:
    def __init__(self, *a, **k):
        pass

    def setStyle(self, *a, **k):
        return None


rl_platypus.Table = Dummy
rl_platypus.TableStyle = Dummy
rl_platypus.Spacer = Dummy
rl_platypus.Image = Dummy
rl_platypus.PageBreak = Dummy
rl_platypus.SimpleDocTemplate = DummyDoc
rl_platypus.Paragraph = lambda *a, **k: None
sys.modules.setdefault("reportlab.platypus", rl_platypus)

rl_styles = types.ModuleType("reportlab.lib.styles")
rl_styles.getSampleStyleSheet = lambda: {
    "Title": None,
    "Normal": None,
    "Heading2": None,
    "Heading3": None,
    "Heading4": None,
}
rl_styles.ParagraphStyle = Dummy
sys.modules.setdefault("reportlab.lib.styles", rl_styles)

rl_pagesizes = types.ModuleType("reportlab.lib.pagesizes")
rl_pagesizes.letter = (0, 0)
rl_pagesizes.landscape = lambda x: x
sys.modules.setdefault("reportlab.lib.pagesizes", rl_pagesizes)

rl_units = types.ModuleType("reportlab.lib.units")
rl_units.inch = 1
sys.modules.setdefault("reportlab.lib.units", rl_units)

rl_colors = types.ModuleType("reportlab.lib.colors")
rl_colors.lightblue = rl_colors.grey = rl_colors.lightgrey = "c"
sys.modules.setdefault("reportlab.lib.colors", rl_colors)

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from AutoML import AutoMLApp
from tkinter import filedialog
from mainappsrc.core.reporting_export import Reporting_Export


def test_generate_pdf_report_exports_template(tmp_path, monkeypatch):
    pdf_path = tmp_path / "out.pdf"
    template_path = tmp_path / "template.json"
    template_path.write_text(json.dumps({"elements": {}, "sections": []}))

    monkeypatch.setattr(filedialog, "asksaveasfilename", lambda **k: str(pdf_path))
    monkeypatch.setattr(filedialog, "askopenfilename", lambda **k: str(template_path))

    app = AutoMLApp.__new__(AutoMLApp)
    app.project_properties = {}
    app.reporting_export = Reporting_Export(app)
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
    app = AutoMLApp.__new__(AutoMLApp)
    app.project_properties = {}
    app.fi2tc_docs = []
    app.tc2fi_docs = []
    app.reporting_export = Reporting_Export(app)
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
    app = AutoMLApp.__new__(AutoMLApp)
    app.project_properties = {}
    app.fi2tc_docs = []
    app.tc2fi_docs = []
    app.reporting_export = Reporting_Export(app)
    app._generate_pdf_report()
    assert pdf_path.exists()
    assert pdf_path.with_suffix(".json").exists()


def test_generate_pdf_report_respects_pdf_extension(tmp_path, monkeypatch):
    pdf_txt_path = tmp_path / "out.txt"
    template_path = tmp_path / "template.json"
    template_path.write_text(json.dumps({"elements": {}, "sections": []}))

    monkeypatch.setattr(filedialog, "asksaveasfilename", lambda **k: str(pdf_txt_path))
    monkeypatch.setattr(filedialog, "askopenfilename", lambda **k: str(template_path))

    app = AutoMLApp.__new__(AutoMLApp)
    app.project_properties = {}
    app.reporting_export = Reporting_Export(app)
    app._generate_pdf_report()

    pdf_path = pdf_txt_path.with_suffix(".pdf")
    assert pdf_path.exists()
    assert pdf_path.with_suffix(".json").exists()
    assert not pdf_txt_path.exists()