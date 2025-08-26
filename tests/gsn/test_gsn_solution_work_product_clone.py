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

import types
import math
from mainappsrc.models.gsn import GSNNode, GSNDiagram
from gui.gsn_config_window import GSNElementConfig, _collect_work_products
from analysis import SafetyManagementToolbox
from mainappsrc.models.sysml.sysml_repository import SysMLRepository


class DummyVar:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value


class DummyText:
    def __init__(self, text=""):
        self.text = text

    def get(self, *_args, **_kwargs):
        return self.text


def test_solution_clones_existing_work_product():
    root = GSNNode("Root", "Goal")
    diag = GSNDiagram(root)
    original = GSNNode("Orig", "Solution")
    original.work_product = "WP1"
    diag.add_node(original)
    node = GSNNode("New", "Solution")
    diag.add_node(node)

    cfg = GSNElementConfig.__new__(GSNElementConfig)
    cfg.node = node
    cfg.diagram = diag
    cfg.name_var = DummyVar(node.user_name)
    cfg.desc_text = DummyText(node.description)
    cfg.work_var = DummyVar("WP1")
    cfg.link_var = DummyVar("")
    cfg.spi_var = DummyVar("")
    cfg.destroy = lambda: None

    cfg._on_ok()

    assert node.original is original
    assert not node.is_primary_instance
    assert node.user_name == original.user_name
    # Clones should retain their own unique identifier so diagram
    # connections can distinguish between primary and cloned instances.
    assert node.unique_id != original.unique_id


def test_solution_requires_matching_spi_for_clone():
    root = GSNNode("Root", "Goal")
    diag = GSNDiagram(root)
    original = GSNNode("Orig", "Solution")
    original.work_product = "WP1"
    original.spi_target = "Brake Time (SOTIF)"
    diag.add_node(original)

    node = GSNNode("New", "Solution")
    diag.add_node(node)
    cfg = GSNElementConfig.__new__(GSNElementConfig)
    cfg.node = node
    cfg.diagram = diag
    cfg.name_var = DummyVar(node.user_name)
    cfg.desc_text = DummyText(node.description)
    cfg.work_var = DummyVar("WP1")
    cfg.link_var = DummyVar("")
    cfg.spi_var = DummyVar("Other SPI (SOTIF)")
    cfg.destroy = lambda: None
    cfg._on_ok()

    assert node.original is node

    node2 = GSNNode("New2", "Solution")
    diag.add_node(node2)
    cfg2 = GSNElementConfig.__new__(GSNElementConfig)
    cfg2.node = node2
    cfg2.diagram = diag
    cfg2.name_var = DummyVar(node2.user_name)
    cfg2.desc_text = DummyText(node2.description)
    cfg2.work_var = DummyVar("WP1")
    cfg2.link_var = DummyVar("")
    cfg2.spi_var = DummyVar("Brake Time (SOTIF)")
    cfg2.destroy = lambda: None
    cfg2._on_ok()

    assert node2.original is original


def test_format_text_shows_calculated_spi():
    root = GSNNode("Root", "Goal")
    sol = GSNNode("Sol", "Solution")
    sol.spi_target = "Brake Time (SOTIF)"
    diag = GSNDiagram(root)
    diag.add_node(sol)

    class TopEvent:
        def __init__(self):
            self.user_name = "Brake Time"
            self.validation_desc = "Brake Time"
            self.validation_target = 1e-4
            self.spi_probability = 1e-5

    diag.app = types.SimpleNamespace(top_events=[TopEvent()])
    text = diag._format_text(sol)
    expected_spi = math.log10(1e-4 / 1e-5)
    assert f"SPI: {expected_spi:.2f}" in text


def test_format_text_shows_validation_target_when_no_probability():
    root = GSNNode("Root", "Goal")
    sol = GSNNode("Sol", "Solution")
    sol.spi_target = "Brake Time (SOTIF)"
    diag = GSNDiagram(root)
    diag.add_node(sol)

    class TopEvent:
        def __init__(self):
            self.user_name = "Brake Time"
            self.validation_desc = "Brake Time"
            self.validation_target = "1e-5"

    diag.app = types.SimpleNamespace(top_events=[TopEvent()])
    text = diag._format_text(sol)
    assert "SPI: 1e-5/h" in text


def test_collect_work_products_returns_unique_sorted():
    root = GSNNode("Root", "Goal")
    diag = GSNDiagram(root)
    n1 = GSNNode("S1", "Solution")
    n1.work_product = "B"
    diag.add_node(n1)
    n2 = GSNNode("S2", "Solution")
    n2.work_product = "A"
    diag.add_node(n2)
    n3 = GSNNode("S3", "Solution")
    n3.work_product = "A"  # duplicate
    diag.add_node(n3)

    assert _collect_work_products(diag) == ["A", "B"]


def test_collect_work_products_includes_toolbox_entries():
    SysMLRepository.reset_instance()
    root = GSNNode("Root", "Goal")
    diag = GSNDiagram(root)
    toolbox = SafetyManagementToolbox()
    toolbox.add_work_product("Architecture Diagram", "Safety Analysis", "rationale")

    class App:
        def __init__(self):
            self.safety_mgmt_toolbox = toolbox

    diag.app = App()

    assert _collect_work_products(diag) == [
        "Architecture Diagram",
        "Architecture Diagram - Safety Analysis",
        "Safety Analysis",
    ]


def test_collect_work_products_includes_toolbox_diagrams():
    """Diagrams registered in the toolbox should appear even without work products."""

    root = GSNNode("Root", "Goal")
    diag = GSNDiagram(root)

    class Toolbox:
        def list_diagrams(self):
            return ["DiagB", "DiagA"]

        def get_work_products(self):
            return []

    class App:
        def __init__(self):
            self.safety_mgmt_toolbox = Toolbox()

    diag.app = App()

    # Result should be sorted and include all diagrams
    assert _collect_work_products(diag) == ["DiagA", "DiagB"]


def test_collect_work_products_reuses_app_lists():
    """Names from app combo-box helpers should be included."""

    root = GSNNode("Root", "Goal")
    diag = GSNDiagram(root)

    class App:
        def get_architecture_box_list(self):
            return ["Arch1"]

        def get_analysis_box_list(self):
            return ["RA1"]

    assert _collect_work_products(diag, App()) == ["Arch1", "RA1"]


def test_collect_work_products_falls_back_to_app_objects():
    """Fallback to app attributes when helper functions are absent."""

    root = GSNNode("Root", "Goal")
    diag = GSNDiagram(root)

    class Diagram:
        name = "Diag1"

    class Analysis:
        name = "Analysis1"

    class App:
        arch_diagrams = [Diagram()]
        reliability_analyses = [Analysis()]

    assert _collect_work_products(diag, App()) == ["Analysis1", "Diag1"]


def test_config_dialog_populates_comboboxes(monkeypatch):
    """Work product and SPI combos should list existing entries."""

    root = GSNNode("Root", "Goal")
    diag = GSNDiagram(root)
    existing = GSNNode("Orig", "Solution")
    existing.work_product = "WP1"
    existing.spi_target = "SPI1 (SOTIF)"
    diag.add_node(existing)

    node = GSNNode("New", "Solution")
    diag.add_node(node)

    # ------------------------------------------------------------------
    # Stub tkinter widgets so the dialog can be created headlessly
    # ------------------------------------------------------------------
    class DummyWidget:
        def __init__(self, *a, **k):
            self.configured = {}

        def grid(self, *a, **k):
            pass

        def pack(self, *a, **k):
            pass

        def insert(self, *a, **k):
            pass

        def configure(self, **k):
            self.configured.update(k)

    class DummyText(DummyWidget):
        def get(self, *a, **k):
            return ""

    class DummyCombobox(DummyWidget):
        def __init__(self, *a, textvariable=None, values=None, state=None, **k):
            super().__init__(*a, **k)
            self.textvariable = textvariable
            self.state = state
            self.init_values = values

    combo_holder = []

    def combo_stub(*a, **k):
        cb = DummyCombobox(*a, **k)
        combo_holder.append(cb)
        return cb

    class DummyVar:
        def __init__(self, value=""):
            self._value = value

        def get(self):
            return self._value

        def set(self, v):
            self._value = v

    # Patch tkinter components used by the dialog
    monkeypatch.setattr("gui.gsn_config_window.tk.Toplevel.__init__", lambda self, master=None: None)
    monkeypatch.setattr("gui.gsn_config_window.tk.Toplevel.title", lambda self, *a, **k: None)
    monkeypatch.setattr("gui.gsn_config_window.tk.Toplevel.geometry", lambda self, *a, **k: None)
    monkeypatch.setattr("gui.gsn_config_window.tk.Toplevel.columnconfigure", lambda self, *a, **k: None)
    monkeypatch.setattr("gui.gsn_config_window.tk.Toplevel.rowconfigure", lambda self, *a, **k: None)
    monkeypatch.setattr("gui.gsn_config_window.tk.Toplevel.transient", lambda self, *a, **k: None)
    monkeypatch.setattr("gui.gsn_config_window.tk.Toplevel.grab_set", lambda self, *a, **k: None)
    monkeypatch.setattr("gui.gsn_config_window.tk.Toplevel.wait_window", lambda self, *a, **k: None)
    monkeypatch.setattr("gui.gsn_config_window.tk.Label", lambda *a, **k: DummyWidget())
    monkeypatch.setattr("gui.gsn_config_window.tk.Entry", lambda *a, **k: DummyWidget())
    monkeypatch.setattr("gui.gsn_config_window.tk.Text", lambda *a, **k: DummyText())
    monkeypatch.setattr("gui.gsn_config_window.ttk.Button", lambda *a, **k: DummyWidget())
    monkeypatch.setattr("gui.gsn_config_window.ttk.Frame", lambda *a, **k: DummyWidget())
    monkeypatch.setattr("gui.gsn_config_window.ttk.Combobox", combo_stub)
    monkeypatch.setattr("gui.gsn_config_window.tk.StringVar", lambda value="": DummyVar(value))

    cfg = GSNElementConfig(None, node, diag)

    wp_cb, spi_cb = combo_holder
    assert wp_cb.init_values is None
    assert spi_cb.init_values is None
    assert wp_cb.configured["values"] == ["WP1"]
    assert spi_cb.configured["values"] == ["SPI1 (SOTIF)"]
    # Both comboboxes should remain blank until the user picks an option.
    assert cfg.work_var.get() == ""
    assert cfg.spi_var.get() == ""


def test_config_dialog_lists_project_spis(monkeypatch):
    """SPI combo should list project validation targets."""

    root = GSNNode("Root", "Goal")
    diag = GSNDiagram(root)
    node = GSNNode("New", "Solution")
    diag.add_node(node)

    class TopEvent:
        def __init__(self, desc):
            self.validation_desc = ""
            self.safety_goal_description = desc

    class App:
        def __init__(self):
            self.top_events = [TopEvent("SPI1")]

        def get_spi_targets(self):
            return ["SPI1 (SOTIF)"]

    class Master:
        def __init__(self):
            self.app = App()

    # ------------------------------------------------------------------
    # Stub tkinter widgets similar to the previous test
    # ------------------------------------------------------------------
    class DummyWidget:
        def __init__(self, *a, **k):
            self.configured = {}

        def grid(self, *a, **k):
            pass

        def pack(self, *a, **k):
            pass

        def insert(self, *a, **k):
            pass

        def configure(self, **k):
            self.configured.update(k)

    class DummyText(DummyWidget):
        def get(self, *a, **k):
            return ""

    class DummyCombobox(DummyWidget):
        def __init__(self, *a, textvariable=None, values=None, state=None, **k):
            super().__init__(*a, **k)
            self.textvariable = textvariable
            self.state = state
            self.init_values = values

    combo_holder = []

    def combo_stub(*a, **k):
        cb = DummyCombobox(*a, **k)
        combo_holder.append(cb)
        return cb

    class DummyVar:
        def __init__(self, value=""):
            self._value = value

        def get(self):
            return self._value

        def set(self, v):
            self._value = v

    monkeypatch.setattr("gui.gsn_config_window.tk.Toplevel.__init__", lambda self, master=None: None)
    monkeypatch.setattr("gui.gsn_config_window.tk.Toplevel.title", lambda self, *a, **k: None)
    monkeypatch.setattr("gui.gsn_config_window.tk.Toplevel.geometry", lambda self, *a, **k: None)
    monkeypatch.setattr("gui.gsn_config_window.tk.Toplevel.columnconfigure", lambda self, *a, **k: None)
    monkeypatch.setattr("gui.gsn_config_window.tk.Toplevel.rowconfigure", lambda self, *a, **k: None)
    monkeypatch.setattr("gui.gsn_config_window.tk.Toplevel.transient", lambda self, *a, **k: None)
    monkeypatch.setattr("gui.gsn_config_window.tk.Toplevel.grab_set", lambda self, *a, **k: None)
    monkeypatch.setattr("gui.gsn_config_window.tk.Toplevel.wait_window", lambda self, *a, **k: None)
    monkeypatch.setattr("gui.gsn_config_window.tk.Label", lambda *a, **k: DummyWidget())
    monkeypatch.setattr("gui.gsn_config_window.tk.Entry", lambda *a, **k: DummyWidget())
    monkeypatch.setattr("gui.gsn_config_window.tk.Text", lambda *a, **k: DummyText())
    monkeypatch.setattr("gui.gsn_config_window.ttk.Button", lambda *a, **k: DummyWidget())
    monkeypatch.setattr("gui.gsn_config_window.ttk.Frame", lambda *a, **k: DummyWidget())
    monkeypatch.setattr("gui.gsn_config_window.ttk.Combobox", combo_stub)
    monkeypatch.setattr("gui.gsn_config_window.tk.StringVar", lambda value="": DummyVar(value))

    cfg = GSNElementConfig(Master(), node, diag)

    # work product combobox is first, spi combobox second
    _, spi_cb = combo_holder
    assert spi_cb.configured["values"] == ["SPI1 (SOTIF)"]
    assert cfg.spi_var.get() == ""


def test_config_dialog_lists_toolbox_work_products(monkeypatch):
    """Work product combo should list toolbox entries."""
    SysMLRepository.reset_instance()
    root = GSNNode("Root", "Goal")
    diag = GSNDiagram(root)
    node = GSNNode("New", "Solution")
    diag.add_node(node)

    toolbox = SafetyManagementToolbox()
    toolbox.add_work_product("Architecture Diagram", "Safety Analysis", "")

    class App:
        def __init__(self):
            self.safety_mgmt_toolbox = toolbox

    class Master:
        def __init__(self):
            self.app = App()

    class DummyWidget:
        def __init__(self, *a, **k):
            self.configured = {}

        def grid(self, *a, **k):
            pass

        def pack(self, *a, **k):
            pass

        def insert(self, *a, **k):
            pass

        def configure(self, **k):
            self.configured.update(k)

    class DummyText(DummyWidget):
        def get(self, *a, **k):
            return ""

    class DummyCombobox(DummyWidget):
        def __init__(self, *a, textvariable=None, values=None, state=None, **k):
            super().__init__(*a, **k)
            self.textvariable = textvariable
            self.state = state
            self.init_values = values

    combo_holder = []

    def combo_stub(*a, **k):
        cb = DummyCombobox(*a, **k)
        combo_holder.append(cb)
        return cb

    class DummyVar:
        def __init__(self, value=""):
            self._value = value

        def get(self):
            return self._value

        def set(self, v):
            self._value = v

    monkeypatch.setattr("gui.gsn_config_window.tk.Toplevel.__init__", lambda self, master=None: None)
    monkeypatch.setattr("gui.gsn_config_window.tk.Toplevel.title", lambda self, *a, **k: None)
    monkeypatch.setattr("gui.gsn_config_window.tk.Toplevel.geometry", lambda self, *a, **k: None)
    monkeypatch.setattr("gui.gsn_config_window.tk.Toplevel.columnconfigure", lambda self, *a, **k: None)
    monkeypatch.setattr("gui.gsn_config_window.tk.Toplevel.rowconfigure", lambda self, *a, **k: None)
    monkeypatch.setattr("gui.gsn_config_window.tk.Toplevel.transient", lambda self, *a, **k: None)
    monkeypatch.setattr("gui.gsn_config_window.tk.Toplevel.grab_set", lambda self, *a, **k: None)
    monkeypatch.setattr("gui.gsn_config_window.tk.Toplevel.wait_window", lambda self, *a, **k: None)
    monkeypatch.setattr("gui.gsn_config_window.tk.Label", lambda *a, **k: DummyWidget())
    monkeypatch.setattr("gui.gsn_config_window.tk.Entry", lambda *a, **k: DummyWidget())
    monkeypatch.setattr("gui.gsn_config_window.tk.Text", lambda *a, **k: DummyText())
    monkeypatch.setattr("gui.gsn_config_window.ttk.Button", lambda *a, **k: DummyWidget())
    monkeypatch.setattr("gui.gsn_config_window.ttk.Frame", lambda *a, **k: DummyWidget())
    monkeypatch.setattr("gui.gsn_config_window.ttk.Combobox", combo_stub)
    monkeypatch.setattr("gui.gsn_config_window.tk.StringVar", lambda value="": DummyVar(value))

    GSNElementConfig(Master(), node, diag)

    wp_cb = combo_holder[0]
    assert wp_cb.configured["values"] == [
        "Architecture Diagram",
        "Architecture Diagram - Safety Analysis",
        "Safety Analysis",
    ]


def test_config_dialog_lists_toolbox_diagrams(monkeypatch):
    """Work product combo should list diagrams tracked in the toolbox."""

    root = GSNNode("Root", "Goal")
    diag = GSNDiagram(root)
    node = GSNNode("New", "Solution")
    diag.add_node(node)

    class Toolbox:
        def list_diagrams(self):
            return ["DiagB", "DiagA"]

        def get_work_products(self):
            return []

    class App:
        def __init__(self):
            self.safety_mgmt_toolbox = Toolbox()

    class Master:
        def __init__(self):
            self.app = App()

    class DummyWidget:
        def __init__(self, *a, **k):
            self.configured = {}

        def grid(self, *a, **k):
            pass

        def pack(self, *a, **k):
            pass

        def insert(self, *a, **k):
            pass

        def configure(self, **k):
            self.configured.update(k)

    class DummyText(DummyWidget):
        def get(self, *a, **k):
            return ""

    class DummyCombobox(DummyWidget):
        def __init__(self, *a, textvariable=None, values=None, state=None, **k):
            super().__init__(*a, **k)
            self.textvariable = textvariable
            self.state = state
            self.init_values = values

    combo_holder = []

    def combo_stub(*a, **k):
        cb = DummyCombobox(*a, **k)
        combo_holder.append(cb)
        return cb

    class DummyVar:
        def __init__(self, value=""):
            self._value = value

        def get(self):
            return self._value

        def set(self, v):
            self._value = v

    monkeypatch.setattr("gui.gsn_config_window.tk.Toplevel.__init__", lambda self, master=None: None)
    monkeypatch.setattr("gui.gsn_config_window.tk.Toplevel.title", lambda self, *a, **k: None)
    monkeypatch.setattr("gui.gsn_config_window.tk.Toplevel.geometry", lambda self, *a, **k: None)
    monkeypatch.setattr("gui.gsn_config_window.tk.Toplevel.columnconfigure", lambda self, *a, **k: None)
    monkeypatch.setattr("gui.gsn_config_window.tk.Toplevel.rowconfigure", lambda self, *a, **k: None)
    monkeypatch.setattr("gui.gsn_config_window.tk.Toplevel.transient", lambda self, *a, **k: None)
    monkeypatch.setattr("gui.gsn_config_window.tk.Toplevel.grab_set", lambda self, *a, **k: None)
    monkeypatch.setattr("gui.gsn_config_window.tk.Toplevel.wait_window", lambda self, *a, **k: None)
    monkeypatch.setattr("gui.gsn_config_window.tk.Label", lambda *a, **k: DummyWidget())
    monkeypatch.setattr("gui.gsn_config_window.tk.Entry", lambda *a, **k: DummyWidget())
    monkeypatch.setattr("gui.gsn_config_window.tk.Text", lambda *a, **k: DummyText())
    monkeypatch.setattr("gui.gsn_config_window.ttk.Button", lambda *a, **k: DummyWidget())
    monkeypatch.setattr("gui.gsn_config_window.ttk.Frame", lambda *a, **k: DummyWidget())
    monkeypatch.setattr("gui.gsn_config_window.ttk.Combobox", combo_stub)
    monkeypatch.setattr("gui.gsn_config_window.tk.StringVar", lambda value="": DummyVar(value))

    cfg = GSNElementConfig(Master(), node, diag)

    wp_cb = combo_holder[0]
    assert wp_cb.configured["values"] == ["DiagA", "DiagB"]
    # The combobox should start without a selected value so the user must
    # explicitly choose a work product.
    assert cfg.work_var.get() == ""

