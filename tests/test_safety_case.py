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

import os
import sys
import types
import math
import csv

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Stub out Pillow modules so AutoML can be imported without the dependency
sys.modules.setdefault("PIL", types.ModuleType("PIL"))
sys.modules.setdefault("PIL.Image", types.ModuleType("PIL.Image"))
sys.modules.setdefault("PIL.ImageTk", types.ModuleType("PIL.ImageTk"))
sys.modules.setdefault("PIL.ImageDraw", types.ModuleType("PIL.ImageDraw"))
sys.modules.setdefault("PIL.ImageFont", types.ModuleType("PIL.ImageFont"))

from mainappsrc.models.gsn import GSNNode, GSNDiagram
from AutoML import AutoMLApp
if __package__ and __package__.startswith("AutoML"):
    from AutoML.config.automl_constants import PMHF_TARGETS
else:  # pragma: no cover - script context
    from config.automl_constants import PMHF_TARGETS
from analysis.constants import CHECK_MARK
from mainappsrc.core.undo_manager import UndoRedoManager


class DummyTree:
    def __init__(self, master=None, *, columns=None, show=None, selectmode=None):
        self.columns = list(columns or [])
        self.data = {}
        self.counter = 0
        self.bindings = {}
        self.next_column = "Evidence OK"
        self.selection_value = ()

    def heading(self, column, text=""):
        pass

    def column(self, column, width=None, anchor=None):
        pass

    def pack(self, **kwargs):
        pass

    def insert(self, parent, index, values=None, tags=()):
        iid = f"i{self.counter}"
        self.counter += 1
        self.data[iid] = {"values": list(values or []), "tags": tags}
        return iid

    def get_children(self, item=""):
        return list(self.data.keys())

    def delete(self, iid):
        self.data.pop(iid, None)

    def bind(self, event, callback):
        self.bindings[event] = callback

    def identify_row(self, y):
        return next(iter(self.data.keys()), "")

    def identify_column(self, x):
        idx = self.columns.index(self.next_column) + 1
        return f"#{idx}"

    def item(self, iid, option):
        if option == "tags":
            return self.data.get(iid, {}).get("tags", ())
        if option == "values":
            return self.data.get(iid, {}).get("values", [])
        return None

    def set(self, iid, column, value=None):
        idx = self.columns.index(column)
        if value is None:
            return self.data[iid]["values"][idx]
        self.data[iid]["values"][idx] = value

    def winfo_exists(self):
        return True

    def selection(self):
        return self.selection_value

    def selection_set(self, row):
        self.selection_value = (row,)


class DummyTab:
    def winfo_exists(self):
        return True

    def winfo_children(self):
        return []


class DummyButton:
    def __init__(self, *a, **k):
        pass

    def pack(self, *a, **k):
        pass


class DummyMenu:
    def __init__(self, *a, **k):
        pass

    def add_command(self, *a, **k):
        pass

    def post(self, *a, **k):
        pass


def test_edit_probability_updates_spi(monkeypatch):
    root = GSNNode("G", "Goal")
    sol = GSNNode("E", "Solution")
    sol.spi_target = "SG1 (SOTIF)"
    root.add_child(sol)
    diag = GSNDiagram(root)
    diag.add_node(sol)

    te = types.SimpleNamespace(
        user_name="SG1",
        validation_target=1e-5,
        spi_probability=1e-4,
        validation_desc="",
        safety_goal_description="",
        acceptance_criteria="AC",
        unique_id=1,
    )

    app = AutoMLApp.__new__(AutoMLApp)
    app.doc_nb = types.SimpleNamespace(select=lambda tab: None)
    app._new_tab = lambda title: DummyTab()
    app.all_gsn_diagrams = [diag]
    app.push_undo_state = lambda: None
    app.top_events = [te]
    app.update_views = lambda: None

    monkeypatch.setattr("AutoML.ttk.Treeview", DummyTree)
    monkeypatch.setattr("AutoML.ttk.Button", DummyButton)
    monkeypatch.setattr("AutoML.tk.Menu", DummyMenu)
    monkeypatch.setattr("AutoML.simpledialog.askfloat", lambda *a, **k: 2e-4)

    AutoMLApp.show_safety_case(app)
    tree = app._safety_case_tree
    row = next(iter(tree.data))
    tree.next_column = "Achieved Probability"
    event = types.SimpleNamespace(x=0, y=0)
    tree.bindings["<Double-Button-1>"](event)
    assert te.spi_probability == 2e-4
    row = next(iter(tree.data))
    assert tree.data[row]["values"][5] == f"{2e-4:.2e}"
    expected_spi = math.log10(1e-5 / 2e-4)
    assert tree.data[row]["values"][6] == f"{expected_spi:.2f}"

    class CaptureTree(DummyTree):
        instances = []

        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            CaptureTree.instances.append(self)

    monkeypatch.setattr("AutoML.ttk.Treeview", CaptureTree)
    AutoMLApp.show_safety_performance_indicators(app)
    spi_tree = CaptureTree.instances[-1]
    iid = next(iter(spi_tree.data))
    assert spi_tree.data[iid]["values"][2] == f"{2e-4:.2e}"
    expected_spi = math.log10(1e-5 / 2e-4)
    assert spi_tree.data[iid]["values"][3] == f"{expected_spi:.2f}"


def test_safety_case_shows_validation_target(monkeypatch):
    root = GSNNode("G", "Goal")
    sol = GSNNode("E", "Solution")
    sol.spi_target = "SG1 (SOTIF)"
    root.add_child(sol)
    diag = GSNDiagram(root)
    diag.add_node(sol)

    te = types.SimpleNamespace(
        user_name="SG1",
        validation_target=1e-5,
        spi_probability=1e-4,
        validation_desc="",
        safety_goal_description="",
        acceptance_criteria="AC",
        unique_id=1,
    )

    app = AutoMLApp.__new__(AutoMLApp)
    app.doc_nb = types.SimpleNamespace(select=lambda tab: None)
    app._new_tab = lambda title: DummyTab()
    app.all_gsn_diagrams = [diag]
    app.push_undo_state = lambda: None
    app.top_events = [te]

    monkeypatch.setattr("AutoML.ttk.Treeview", DummyTree)
    monkeypatch.setattr("AutoML.ttk.Button", DummyButton)
    monkeypatch.setattr("AutoML.tk.Menu", DummyMenu)

    AutoMLApp.show_safety_case(app)
    tree = app._safety_case_tree
    assert tree.columns[4] == "Validation Target"
    assert tree.columns[6] == "SPI"
    iid = next(iter(tree.data))
    assert tree.data[iid]["values"][4] == f"{1e-5:.2e}"
    expected_spi = math.log10(1e-5 / 1e-4)
    assert tree.data[iid]["values"][6] == f"{expected_spi:.2f}"


def test_pmfh_autopopulates_validation_target_and_probability(monkeypatch):
    root = GSNNode("G", "Goal")
    sol = GSNNode("E", "Solution")
    sol.spi_target = "SG1 (FUSA)"
    root.add_child(sol)
    diag = GSNDiagram(root)
    diag.add_node(sol)

    te = types.SimpleNamespace(
        user_name="SG1",
        safety_goal_asil="D",
        validation_target=1.0,
        probability=0.0,
        validation_desc="",
        safety_goal_description="",
        acceptance_criteria="AC",
        unique_id=1,
    )

    app = AutoMLApp.__new__(AutoMLApp)
    app.doc_nb = types.SimpleNamespace(select=lambda tab: None)
    app._new_tab = lambda title: DummyTab()
    app.all_gsn_diagrams = [diag]
    app.push_undo_state = lambda: None
    app.top_events = [te]
    app.pmhf_var = types.SimpleNamespace(set=lambda text: None)
    app.pmhf_label = types.SimpleNamespace(config=lambda **k: None)
    app.update_views = lambda: None

    monkeypatch.setattr("AutoML.AutoML_Helper.calculate_probability_recursive", lambda te: 2e-6)
    monkeypatch.setattr("AutoML.AutoMLApp.update_basic_event_probabilities", lambda self: None)
    monkeypatch.setattr("AutoML.AutoMLApp.get_all_basic_events", lambda self: [])
    monkeypatch.setattr("AutoML.AutoMLApp.get_failure_mode_node", lambda self, be: None)
    monkeypatch.setattr("AutoML.AutoMLApp.get_all_fmea_entries", lambda self: [])
    monkeypatch.setattr("AutoML.ttk.Treeview", DummyTree)
    monkeypatch.setattr("AutoML.ttk.Button", DummyButton)
    monkeypatch.setattr("AutoML.tk.Menu", DummyMenu)

    AutoMLApp.calculate_pmfh(app)
    AutoMLApp.show_safety_case(app)

    tree = app._safety_case_tree
    iid = next(iter(tree.data))
    assert tree.data[iid]["values"][4] == f"{PMHF_TARGETS['D']:.2e}"
    assert tree.data[iid]["values"][5] == f"{2e-6:.2e}"
    expected_spi = math.log10(PMHF_TARGETS['D'] / 2e-6)
    assert tree.data[iid]["values"][6] == f"{expected_spi:.2f}"


def test_edit_probability_in_spi_explorer(monkeypatch):
    root = GSNNode("G", "Goal")
    sol = GSNNode("E", "Solution")
    sol.spi_target = "SG1 (SOTIF)"
    root.add_child(sol)
    diag = GSNDiagram(root)
    diag.add_node(sol)

    te = types.SimpleNamespace(
        user_name="SG1",
        validation_target=1e-5,
        spi_probability=1e-4,
        validation_desc="",
        safety_goal_description="",
        acceptance_criteria="AC",
        unique_id=1,
    )

    app = AutoMLApp.__new__(AutoMLApp)
    app.doc_nb = types.SimpleNamespace(select=lambda tab: None)
    app._new_tab = lambda title: DummyTab()
    app.all_gsn_diagrams = [diag]
    app.push_undo_state = lambda: None
    app.top_events = [te]
    app.refresh_safety_case_table = lambda: None
    app.update_views = lambda: None

    monkeypatch.setattr("AutoML.ttk.Treeview", DummyTree)
    monkeypatch.setattr("AutoML.ttk.Button", DummyButton)
    monkeypatch.setattr("AutoML.tk.Menu", DummyMenu)
    monkeypatch.setattr("AutoML.simpledialog.askfloat", lambda *a, **k: 5e-5)

    AutoMLApp.show_safety_performance_indicators(app)
    tree = app._spi_tree
    iid = next(iter(tree.data))
    tree.selection_set(iid)
    app._edit_spi_item()
    iid = next(iter(tree.data))
    assert te.spi_probability == 5e-5
    assert tree.data[iid]["values"][2] == f"{5e-5:.2e}"
    expected_spi = math.log10(1e-5 / 5e-5)
    assert tree.data[iid]["values"][3] == f"{expected_spi:.2f}"


def test_spi_shows_pmhf_and_validation(monkeypatch):
    te = types.SimpleNamespace(
        user_name="SG1",
        validation_target=1e-5,
        probability=2e-6,
        spi_probability=2e-6,
        safety_goal_asil="D",
        validation_desc="",
        safety_goal_description="",
        acceptance_criteria="AC",
        unique_id=1,
    )

    app = AutoMLApp.__new__(AutoMLApp)
    app.doc_nb = types.SimpleNamespace(select=lambda tab: None)
    app._new_tab = lambda title: DummyTab()
    app.push_undo_state = lambda: None
    app.top_events = [te]

    monkeypatch.setattr("AutoML.ttk.Treeview", DummyTree)
    monkeypatch.setattr("AutoML.ttk.Button", DummyButton)
    monkeypatch.setattr("AutoML.tk.Menu", DummyMenu)

    AutoMLApp.show_safety_performance_indicators(app)
    tree = app._spi_tree
    assert len(tree.data) == 2
    targets = {row["values"][1]: row for row in tree.data.values()}
    assert f"{1e-5:.2e}" in targets
    assert f"{PMHF_TARGETS['D']:.2e}" in targets
    pmhf_row = targets[f"{PMHF_TARGETS['D']:.2e}"]
    expected_spi = math.log10(PMHF_TARGETS['D'] / 2e-6)
    assert pmhf_row["values"][3] == f"{expected_spi:.2f}"


def test_pmhf_skips_sotif_probabilities(monkeypatch):
    sotif = types.SimpleNamespace(
        user_name="SG1",
        validation_target=1e-5,
        spi_probability=1e-4,
        validation_desc="",
        safety_goal_description="",
        acceptance_criteria="AC",
        unique_id=1,
    )
    fusa = types.SimpleNamespace(
        user_name="SG2",
        safety_goal_asil="D",
        validation_desc="",
        safety_goal_description="",
        acceptance_criteria="AC",
        unique_id=2,
    )

    app = AutoMLApp.__new__(AutoMLApp)
    app.doc_nb = types.SimpleNamespace(select=lambda tab: None)
    app._new_tab = lambda title: DummyTab()
    app.push_undo_state = lambda: None
    app.top_events = [sotif, fusa]
    app.pmhf_var = types.SimpleNamespace(set=lambda text: None)
    app.pmhf_label = types.SimpleNamespace(config=lambda **k: None)
    app.refresh_safety_case_table = lambda: None
    app.update_views = lambda: None

    calls = []

    def fake_prob(te):
        calls.append(te)
        return 2e-6 if te is fusa else 3e-5

    monkeypatch.setattr("AutoML.AutoML_Helper.calculate_probability_recursive", fake_prob)
    monkeypatch.setattr("AutoML.AutoMLApp.update_basic_event_probabilities", lambda self: None)
    monkeypatch.setattr("AutoML.AutoMLApp.get_all_basic_events", lambda self: [])
    monkeypatch.setattr("AutoML.AutoMLApp.get_failure_mode_node", lambda self, be: None)
    monkeypatch.setattr("AutoML.AutoMLApp.get_all_fmea_entries", lambda self: [])
    monkeypatch.setattr("AutoML.ttk.Treeview", DummyTree)
    monkeypatch.setattr("AutoML.ttk.Button", DummyButton)
    monkeypatch.setattr("AutoML.tk.Menu", DummyMenu)

    AutoMLApp.show_safety_performance_indicators(app)

    AutoMLApp.calculate_pmfh(app)

    assert sotif.spi_probability == 1e-4
    assert fusa.probability == 2e-6
    assert sotif not in calls

    tree = app._spi_tree
    rows = {row["values"][1]: row for row in tree.data.values()}
    sotif_row = rows[f"{1e-5:.2e}"]
    fusa_row = rows[f"{PMHF_TARGETS['D']:.2e}"]
    assert sotif_row["values"][2] == f"{1e-4:.2e}"
    assert fusa_row["values"][2] == f"{2e-6:.2e}"


def test_edit_notes_updates_node(monkeypatch):
    root = GSNNode("G", "Goal")
    sol = GSNNode("E", "Solution")
    root.add_child(sol)
    diag = GSNDiagram(root)
    diag.add_node(sol)

    app = AutoMLApp.__new__(AutoMLApp)
    app.doc_nb = types.SimpleNamespace(select=lambda tab: None)
    app._new_tab = lambda title: DummyTab()
    app.all_gsn_diagrams = [diag]
    app.push_undo_state = lambda: None

    monkeypatch.setattr("AutoML.ttk.Treeview", DummyTree)
    monkeypatch.setattr("AutoML.ttk.Button", DummyButton)
    monkeypatch.setattr("AutoML.tk.Menu", DummyMenu)
    monkeypatch.setattr("AutoML.simpledialog.askstring", lambda *a, **k: "new note")

    AutoMLApp.show_safety_case(app)
    tree = app._safety_case_tree
    row = next(iter(tree.data))
    tree.next_column = "Notes"
    event = types.SimpleNamespace(x=0, y=0)
    tree.bindings["<Double-Button-1>"](event)

    assert sol.manager_notes == "new note"
    assert tree.data[row]["values"][8] == "new note"

def test_safety_case_lists_and_toggles(monkeypatch):
    root = GSNNode("G", "Goal")
    sol = GSNNode("E", "Solution")
    root.add_child(sol)
    diag = GSNDiagram(root)
    diag.add_node(sol)

    app = AutoMLApp.__new__(AutoMLApp)
    app.doc_nb = types.SimpleNamespace(select=lambda tab: None)
    app._new_tab = lambda title: DummyTab()
    app.all_gsn_diagrams = [diag]
    app.push_undo_state = lambda: None

    monkeypatch.setattr("AutoML.ttk.Treeview", DummyTree)
    monkeypatch.setattr("AutoML.ttk.Button", DummyButton)
    monkeypatch.setattr("AutoML.tk.Menu", DummyMenu)
    monkeypatch.setattr("AutoML.messagebox.askokcancel", lambda *a, **k: True)

    AutoMLApp.show_safety_case(app)
    tree = app._safety_case_tree
    assert len(tree.data) == 1
    iid = next(iter(tree.data))
    assert tree.data[iid]["values"][0] == "E"

    event = types.SimpleNamespace(x=0, y=0)
    tree.bindings["<Double-Button-1>"](event)
    assert sol.evidence_sufficient
    assert tree.data[iid]["values"][7] == CHECK_MARK

    app.refresh_safety_case_table()
    iid = next(iter(tree.data))
    assert tree.data[iid]["values"][7] == CHECK_MARK


def test_safety_case_cancel_does_not_toggle(monkeypatch):
    root = GSNNode("G", "Goal")
    sol = GSNNode("E", "Solution")
    root.add_child(sol)
    diag = GSNDiagram(root)
    diag.add_node(sol)

    app = AutoMLApp.__new__(AutoMLApp)
    app.doc_nb = types.SimpleNamespace(select=lambda tab: None)
    app._new_tab = lambda title: types.SimpleNamespace(
        winfo_exists=lambda: True, winfo_children=lambda: []
    )
    app.all_gsn_diagrams = [diag]
    app.push_undo_state = lambda: None

    monkeypatch.setattr("AutoML.ttk.Treeview", DummyTree)
    monkeypatch.setattr("AutoML.ttk.Button", DummyButton)
    monkeypatch.setattr("AutoML.tk.Menu", DummyMenu)
    monkeypatch.setattr("AutoML.messagebox.askokcancel", lambda *a, **k: False)


def test_safety_case_edit_updates_table(monkeypatch):
    root = GSNNode("G", "Goal")
    sol = GSNNode("E", "Solution")
    root.add_child(sol)
    diag = GSNDiagram(root)
    diag.add_node(sol)

    app = AutoMLApp.__new__(AutoMLApp)
    app.doc_nb = types.SimpleNamespace(select=lambda tab: None)
    app._new_tab = lambda title: DummyTab()
    app.all_gsn_diagrams = [diag]
    app.push_undo_state = lambda: None

    monkeypatch.setattr("AutoML.ttk.Treeview", DummyTree)
    monkeypatch.setattr("AutoML.ttk.Button", DummyButton)
    monkeypatch.setattr("AutoML.tk.Menu", DummyMenu)

    called = {}

    def fake_config(master, node, diag):
        called["ok"] = True
        node.work_product = "WP"
        node.manager_notes = "note"

    monkeypatch.setattr("AutoML.GSNElementConfig", fake_config)

    AutoMLApp.show_safety_case(app)
    tree = app._safety_case_tree
    iid = next(iter(tree.data))
    tree.selection_set(iid)
    app._edit_safety_case_item()
    assert called.get("ok")
    iid = next(iter(tree.data))
    assert tree.data[iid]["values"][2] == "WP"
    assert tree.data[iid]["values"][8] == "note"


def test_safety_case_undo_redo_toggle(monkeypatch):
    root = GSNNode("G", "Goal")
    sol = GSNNode("E", "Solution")
    root.add_child(sol)
    diag = GSNDiagram(root)
    diag.add_node(sol)

    app = AutoMLApp.__new__(AutoMLApp)
    app.doc_nb = types.SimpleNamespace(select=lambda tab: None)
    app._new_tab = lambda title: DummyTab()
    app.all_gsn_diagrams = [diag]
    app.gsn_diagrams = [diag]
    app.update_views = lambda: None
    app.undo_manager = UndoRedoManager(app)

    def export_model_data(include_versions=False):
        return {
            "gsn_diagrams": [d.to_dict() for d in app.gsn_diagrams],
            "gsn_modules": [],
        }

    def apply_model_data(data):
        app.gsn_diagrams = [GSNDiagram.from_dict(d) for d in data.get("gsn_diagrams", [])]
        app.all_gsn_diagrams = list(app.gsn_diagrams)

    app.export_model_data = export_model_data
    app.apply_model_data = apply_model_data
    app.push_undo_state = AutoMLApp.push_undo_state.__get__(app)
    app.undo = AutoMLApp.undo.__get__(app)
    app.redo = AutoMLApp.redo.__get__(app)

    monkeypatch.setattr("AutoML.ttk.Treeview", DummyTree)
    monkeypatch.setattr("AutoML.ttk.Button", DummyButton)
    monkeypatch.setattr("AutoML.tk.Menu", DummyMenu)
    monkeypatch.setattr("AutoML.messagebox.askokcancel", lambda *a, **k: True)

    AutoMLApp.show_safety_case(app)
    tree = app._safety_case_tree
    event = types.SimpleNamespace(x=0, y=0)
    tree.bindings["<Double-Button-1>"](event)
    assert app.gsn_diagrams[0].nodes[1].evidence_sufficient

    app.undo()
    assert not app.gsn_diagrams[0].nodes[1].evidence_sufficient

    app.redo()
    assert app.gsn_diagrams[0].nodes[1].evidence_sufficient


def test_export_safety_case_writes_rows(tmp_path, monkeypatch):
    root = GSNNode("G", "Goal")
    sol = GSNNode("S", "Solution")
    sol.user_name = "Sol"
    sol.description = "Desc"
    sol.work_product = "WP"
    sol.evidence_link = "Link"
    root.add_child(sol)
    diag = GSNDiagram(root)
    diag.add_node(sol)

    app = AutoMLApp.__new__(AutoMLApp)
    app.doc_nb = types.SimpleNamespace(select=lambda tab: None)
    app._new_tab = lambda title: DummyTab()
    app.all_gsn_diagrams = [diag]
    app.top_events = []

    monkeypatch.setattr("AutoML.ttk.Treeview", DummyTree)
    monkeypatch.setattr("AutoML.ttk.Button", DummyButton)
    monkeypatch.setattr("AutoML.tk.Menu", DummyMenu)
    monkeypatch.setattr("AutoML.messagebox.showinfo", lambda *a, **k: None)

    path = tmp_path / "out.csv"
    monkeypatch.setattr("AutoML.filedialog.asksaveasfilename", lambda **k: str(path))

    AutoMLApp.show_safety_case(app)
    app.export_safety_case_csv()

    with open(path, newline="") as f:
        rows = list(csv.reader(f))
    assert rows[0] == [
        "Solution",
        "Description",
        "Work Product",
        "Evidence Link",
        "Validation Target",
        "Achieved Probability",
        "SPI",
        "Evidence OK",
        "Notes",
    ]
    assert rows[1][:4] == ["Sol", "Desc", "WP", "Link"]
