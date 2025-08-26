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

from gui.controls import messagebox
from gui.architecture import GovernanceDiagramWindow, SysMLObject
from analysis import SafetyManagementToolbox
from analysis.safety_management import GovernanceModule
from mainappsrc.models.sysml.sysml_repository import SysMLRepository
import pytest


@pytest.mark.parametrize("analysis", ["FI2TC", "TC2FI"])
def test_delete_work_product_updates_toolbox(monkeypatch, analysis):
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    diag = repo.create_diagram("Governance Diagram", name="Gov1")
    diag.tags.append("safety-management")

    toolbox = SafetyManagementToolbox()
    toolbox.add_work_product("Gov1", analysis, "")

    disabled: list[str] = []

    class DummyApp:
        def can_remove_work_product(self, name):
            return True

        def disable_work_product(self, name):
            disabled.append(name)

        safety_mgmt_toolbox = toolbox

    win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
    win.repo = repo
    win.diagram_id = diag.diag_id
    win.objects = []
    win.connections = []
    win.selected_conn = None
    win.zoom = 1.0
    win.remove_object = GovernanceDiagramWindow.remove_object.__get__(win, GovernanceDiagramWindow)
    win._sync_to_repository = lambda: None
    win.redraw = lambda: None
    win.update_property_view = lambda: None
    win.remove_part_model = GovernanceDiagramWindow.remove_part_model.__get__(win, GovernanceDiagramWindow)
    win.remove_element_model = GovernanceDiagramWindow.remove_element_model.__get__(win, GovernanceDiagramWindow)

    wp = SysMLObject(1, "Work Product", 0, 0, properties={"name": analysis})
    win.objects.append(wp)
    win.selected_objs = [wp]
    win.selected_obj = wp
    win.app = DummyApp()

    monkeypatch.setattr(messagebox, "askyesno", lambda *args, **kwargs: True)
    monkeypatch.setattr(messagebox, "showerror", lambda *args, **kwargs: None)

    win.delete_selected()

    assert disabled == [analysis]
    assert toolbox.work_products == []


@pytest.mark.parametrize("analysis", ["FI2TC", "TC2FI"])
def test_cancel_delete_work_product_keeps_toolbox(monkeypatch, analysis):
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    diag = repo.create_diagram("Governance Diagram", name="Gov1")
    diag.tags.append("safety-management")

    toolbox = SafetyManagementToolbox()
    toolbox.add_work_product("Gov1", analysis, "")

    disabled: list[str] = []

    class DummyApp:
        def can_remove_work_product(self, name):
            return True

        def disable_work_product(self, name):
            disabled.append(name)

        safety_mgmt_toolbox = toolbox

    win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
    win.repo = repo
    win.diagram_id = diag.diag_id
    win.objects = []
    win.connections = []
    win.selected_conn = None
    win.zoom = 1.0
    win.remove_object = GovernanceDiagramWindow.remove_object.__get__(win, GovernanceDiagramWindow)
    win._sync_to_repository = lambda: None
    win.redraw = lambda: None
    win.update_property_view = lambda: None
    win.remove_part_model = GovernanceDiagramWindow.remove_part_model.__get__(win, GovernanceDiagramWindow)
    win.remove_element_model = GovernanceDiagramWindow.remove_element_model.__get__(win, GovernanceDiagramWindow)

    wp = SysMLObject(1, "Work Product", 0, 0, properties={"name": analysis})
    win.objects.append(wp)
    win.selected_objs = [wp]
    win.selected_obj = wp
    win.app = DummyApp()

    monkeypatch.setattr(messagebox, "askyesno", lambda *args, **kwargs: False)
    monkeypatch.setattr(messagebox, "showerror", lambda *args, **kwargs: None)

    win.delete_selected()

    assert disabled == []
    assert len(toolbox.work_products) == 1


def test_delete_process_area_removes_children(monkeypatch):
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    diag = repo.create_diagram("Governance Diagram", name="Gov1")
    diag.tags.append("safety-management")

    toolbox = SafetyManagementToolbox()
    toolbox.add_work_product("Gov1", "FI2TC", "")

    disabled: list[str] = []

    class DummyApp:
        def can_remove_work_product(self, name):
            return True

        def disable_work_product(self, name):
            disabled.append(name)

        safety_mgmt_toolbox = toolbox

    win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
    win.repo = repo
    win.diagram_id = diag.diag_id
    win.objects = []
    win.connections = []
    win.selected_conn = None
    win.zoom = 1.0
    win.remove_object = GovernanceDiagramWindow.remove_object.__get__(win, GovernanceDiagramWindow)
    win._sync_to_repository = lambda: None
    win.redraw = lambda: None
    win.update_property_view = lambda: None
    win.remove_part_model = GovernanceDiagramWindow.remove_part_model.__get__(win, GovernanceDiagramWindow)
    win.remove_element_model = GovernanceDiagramWindow.remove_element_model.__get__(win, GovernanceDiagramWindow)

    area = SysMLObject(1, "System Boundary", 0, 0, properties={"name": "Hazard & Threat Analysis"})
    wp = SysMLObject(2, "Work Product", 0, 0, properties={"name": "FI2TC", "parent": "1"})
    win.objects.extend([area, wp])
    win.selected_objs = [area]
    win.selected_obj = area
    win.app = DummyApp()

    monkeypatch.setattr(messagebox, "askyesno", lambda *args, **kwargs: True)
    monkeypatch.setattr(messagebox, "showerror", lambda *args, **kwargs: None)

    win.delete_selected()

    assert disabled == ["FI2TC"]
    assert toolbox.work_products == []
    assert win.objects == []


def test_delete_process_area_removes_boundary_children(monkeypatch):
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    diag = repo.create_diagram("Governance Diagram", name="Gov1")
    diag.tags.append("safety-management")

    toolbox = SafetyManagementToolbox()
    toolbox.add_work_product("Gov1", "Architecture Diagram", "")

    disabled: list[str] = []

    class DummyApp:
        def can_remove_work_product(self, name):
            return True

        def disable_work_product(self, name):
            disabled.append(name)

        safety_mgmt_toolbox = toolbox

    win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
    win.repo = repo
    win.diagram_id = diag.diag_id
    win.objects = []
    win.connections = []
    win.selected_conn = None
    win.zoom = 1.0
    win.remove_object = GovernanceDiagramWindow.remove_object.__get__(win, GovernanceDiagramWindow)
    win._sync_to_repository = lambda: None
    win.redraw = lambda: None
    win.update_property_view = lambda: None
    win.remove_part_model = GovernanceDiagramWindow.remove_part_model.__get__(win, GovernanceDiagramWindow)
    win.remove_element_model = GovernanceDiagramWindow.remove_element_model.__get__(win, GovernanceDiagramWindow)

    area = SysMLObject(1, "System Boundary", 0, 0, properties={"name": "System Design (Item Definition)"})
    wp = SysMLObject(2, "Work Product", 0, 0, properties={"name": "Architecture Diagram", "boundary": "1"})
    win.objects.extend([area, wp])
    win.selected_objs = [area]
    win.selected_obj = area
    win.app = DummyApp()

    monkeypatch.setattr(messagebox, "askyesno", lambda *args, **kwargs: True)
    monkeypatch.setattr(messagebox, "showerror", lambda *args, **kwargs: None)

    win.delete_selected()

    assert disabled == ["Architecture Diagram"]
    assert toolbox.work_products == []
    assert win.objects == []


def test_delete_one_of_multiple_work_products_keeps_enablement(monkeypatch):
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    diag = repo.create_diagram("Governance Diagram", name="Gov1")
    diag.tags.append("safety-management")

    toolbox = SafetyManagementToolbox()
    toolbox.add_work_product("Gov1", "FI2TC", "")
    toolbox.add_work_product("Gov1", "FI2TC", "")

    disabled: list[str] = []

    class DummyApp:
        def can_remove_work_product(self, name):
            return True

        def disable_work_product(self, name):
            disabled.append(name)

        safety_mgmt_toolbox = toolbox

    win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
    win.repo = repo
    win.diagram_id = diag.diag_id
    win.objects = []
    win.connections = []
    win.selected_conn = None
    win.zoom = 1.0
    win.remove_object = GovernanceDiagramWindow.remove_object.__get__(win, GovernanceDiagramWindow)
    win._sync_to_repository = lambda: None
    win.redraw = lambda: None
    win.update_property_view = lambda: None
    win.remove_part_model = GovernanceDiagramWindow.remove_part_model.__get__(win, GovernanceDiagramWindow)
    win.remove_element_model = GovernanceDiagramWindow.remove_element_model.__get__(win, GovernanceDiagramWindow)

    wp1 = SysMLObject(1, "Work Product", 0, 0, properties={"name": "FI2TC"})
    wp2 = SysMLObject(2, "Work Product", 0, 0, properties={"name": "FI2TC"})
    win.objects.extend([wp1, wp2])
    win.selected_objs = [wp1]
    win.selected_obj = wp1
    win.app = DummyApp()

    monkeypatch.setattr(messagebox, "askyesno", lambda *a, **k: True)
    monkeypatch.setattr(messagebox, "showerror", lambda *a, **k: None)

    win.delete_selected()

    assert disabled == []
    assert len(toolbox.work_products) == 1
    assert win.objects == [wp2]


def test_delete_one_of_multiple_gsn_work_products(monkeypatch):
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    diag = repo.create_diagram("Governance Diagram", name="Gov1")
    diag.tags.append("safety-management")

    toolbox = SafetyManagementToolbox()
    toolbox.modules = [GovernanceModule(name="P1", diagrams=["Gov1"])]
    toolbox.diagrams = {"Gov1": diag.diag_id}
    toolbox.set_active_module("P1")
    toolbox.add_work_product("Gov1", "GSN", "")
    toolbox.add_work_product("Gov1", "GSN", "")

    disabled: list[str] = []

    class DummyApp:
        def can_remove_work_product(self, name):
            return True

        def disable_work_product(self, name):
            disabled.append(name)

        safety_mgmt_toolbox = toolbox

    win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
    win.repo = repo
    win.diagram_id = diag.diag_id
    win.objects = []
    win.connections = []
    win.selected_conn = None
    win.zoom = 1.0
    win.remove_object = GovernanceDiagramWindow.remove_object.__get__(win, GovernanceDiagramWindow)
    win._sync_to_repository = lambda: None
    win.redraw = lambda: None
    win.update_property_view = lambda: None
    win.remove_part_model = GovernanceDiagramWindow.remove_part_model.__get__(win, GovernanceDiagramWindow)
    win.remove_element_model = GovernanceDiagramWindow.remove_element_model.__get__(win, GovernanceDiagramWindow)

    wp1 = SysMLObject(1, "Work Product", 0, 0, properties={"name": "GSN"})
    wp2 = SysMLObject(2, "Work Product", 0, 0, properties={"name": "GSN"})
    win.objects.extend([wp1, wp2])
    win.selected_objs = [wp1]
    win.selected_obj = wp1
    win.app = DummyApp()

    monkeypatch.setattr(messagebox, "askyesno", lambda *a, **k: True)
    monkeypatch.setattr(messagebox, "showerror", lambda *a, **k: None)

    win.delete_selected()

    assert disabled == []
    assert toolbox.is_enabled("GSN")
    toolbox.set_active_module(None)
    toolbox.set_active_module("P1")
    assert toolbox.is_enabled("GSN")
    assert win.objects == [wp2]


def test_delete_work_product_in_one_diagram_keeps_other(monkeypatch):
    SysMLRepository._instance = None
    repo = SysMLRepository.get_instance()
    diag1 = repo.create_diagram("Governance Diagram", name="Gov1")
    diag2 = repo.create_diagram("Governance Diagram", name="Gov2")
    for d in (diag1, diag2):
        d.tags.append("safety-management")

    toolbox = SafetyManagementToolbox()
    toolbox.modules = [GovernanceModule(name="P1", diagrams=["Gov1", "Gov2"])]
    toolbox.diagrams = {"Gov1": diag1.diag_id, "Gov2": diag2.diag_id}
    toolbox.set_active_module("P1")
    toolbox.add_work_product("Gov1", "FI2TC", "")
    toolbox.add_work_product("Gov2", "FI2TC", "")

    disabled: list[str] = []

    class DummyApp:
        def can_remove_work_product(self, name):
            return True

        def disable_work_product(self, name):
            disabled.append(name)

        safety_mgmt_toolbox = toolbox

    win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
    win.repo = repo
    win.diagram_id = diag1.diag_id
    win.objects = []
    win.connections = []
    win.selected_conn = None
    win.zoom = 1.0
    win.remove_object = GovernanceDiagramWindow.remove_object.__get__(win, GovernanceDiagramWindow)
    win._sync_to_repository = lambda: None
    win.redraw = lambda: None
    win.update_property_view = lambda: None
    win.remove_part_model = GovernanceDiagramWindow.remove_part_model.__get__(win, GovernanceDiagramWindow)
    win.remove_element_model = GovernanceDiagramWindow.remove_element_model.__get__(win, GovernanceDiagramWindow)

    wp = SysMLObject(1, "Work Product", 0, 0, properties={"name": "FI2TC"})
    win.objects.append(wp)
    win.selected_objs = [wp]
    win.selected_obj = wp
    win.app = DummyApp()

    monkeypatch.setattr(messagebox, "askyesno", lambda *a, **k: True)
    monkeypatch.setattr(messagebox, "showerror", lambda *a, **k: None)

    win.delete_selected()

    assert disabled == []
    assert toolbox.is_enabled("FI2TC")
    assert len([wp for wp in toolbox.work_products if wp.analysis == "FI2TC"]) == 1
