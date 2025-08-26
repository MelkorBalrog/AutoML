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
import os
import sys
import subprocess

from mainappsrc.models.gsn import GSNNode, GSNDiagram
from gui.gsn_config_window import GSNElementConfig
from gui.gsn_diagram_window import GSNDiagramWindow


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


def test_solution_config_sets_evidence_link():
    root = GSNNode("Root", "Goal")
    diag = GSNDiagram(root)
    node = GSNNode("Sol", "Solution")
    diag.add_node(node)

    cfg = GSNElementConfig.__new__(GSNElementConfig)
    cfg.node = node
    cfg.diagram = diag
    cfg.name_var = DummyVar(node.user_name)
    cfg.desc_text = DummyText(node.description)
    cfg.work_var = DummyVar("WP1")
    cfg.link_var = DummyVar("http://example.com")
    cfg.spi_var = DummyVar("")
    cfg.destroy = lambda: None

    cfg._on_ok()

    assert node.evidence_link == "http://example.com"


def test_solution_config_sets_manager_notes():
    root = GSNNode("Root", "Goal")
    diag = GSNDiagram(root)
    node = GSNNode("Sol", "Solution")
    diag.add_node(node)

    cfg = GSNElementConfig.__new__(GSNElementConfig)
    cfg.node = node
    cfg.diagram = diag
    cfg.name_var = DummyVar(node.user_name)
    cfg.desc_text = DummyText(node.description)
    cfg.notes_text = DummyText("Review this later")
    cfg.work_var = DummyVar("")
    cfg.link_var = DummyVar("")
    cfg.spi_var = DummyVar("")
    cfg.destroy = lambda: None

    cfg._on_ok()

    assert node.manager_notes == "Review this later"


def test_double_click_opens_evidence_link(monkeypatch):
    opened = {}

    def fake_open(url):
        opened["url"] = url
        return True

    monkeypatch.setattr("webbrowser.open", fake_open)

    root = GSNNode("Root", "Goal")
    diag = GSNDiagram(root)
    node = GSNNode("Sol", "Solution")
    node.evidence_link = "http://example.com"
    diag.add_node(node)

    wnd = GSNDiagramWindow.__new__(GSNDiagramWindow)
    wnd.diagram = diag
    wnd.refresh = lambda: None
    wnd._node_at = lambda x, y: node
    wnd.canvas = type(
        "CanvasStub",
        (),
        {
            "canvasx": staticmethod(lambda x: x),
            "canvasy": staticmethod(lambda y: y),
        },
    )()

    event = types.SimpleNamespace(x=0, y=0)
    GSNDiagramWindow._on_double_click(wnd, event)

    assert opened["url"] == "http://example.com"


def test_double_click_opens_work_product(monkeypatch):
    opened = {}

    def open_wp(name):
        opened["name"] = name

    root = GSNNode("Root", "Goal")
    diag = GSNDiagram(root)
    node = GSNNode("Sol", "Solution")
    node.work_product = "WP1"
    diag.add_node(node)

    wnd = GSNDiagramWindow.__new__(GSNDiagramWindow)
    wnd.diagram = diag
    wnd.app = types.SimpleNamespace(open_work_product=open_wp)
    wnd.refresh = lambda: None
    wnd._node_at = lambda x, y: node
    wnd.canvas = type(
        "CanvasStub",
        (),
        {
            "canvasx": staticmethod(lambda x: x),
            "canvasy": staticmethod(lambda y: y),
        },
    )()

    event = types.SimpleNamespace(x=0, y=0)
    GSNDiagramWindow._on_double_click(wnd, event)

    assert opened["name"] == "WP1"


def test_double_click_prompts_when_both(monkeypatch):
    opened = {}

    monkeypatch.setattr(
        "gui.gsn_diagram_window.messagebox.askyesnocancel",
        lambda *a, **k: True,
    )

    def open_wp(name):
        opened["wp"] = name

    monkeypatch.setattr("webbrowser.open", lambda url: opened.setdefault("url", url))

    root = GSNNode("Root", "Goal")
    diag = GSNDiagram(root)
    node = GSNNode("Sol", "Solution")
    node.work_product = "WP1"
    node.evidence_link = "http://example.com"
    diag.add_node(node)

    wnd = GSNDiagramWindow.__new__(GSNDiagramWindow)
    wnd.diagram = diag
    wnd.app = types.SimpleNamespace(open_work_product=open_wp)
    wnd.refresh = lambda: None
    wnd._node_at = lambda x, y: node
    wnd.canvas = type(
        "CanvasStub",
        (),
        {
            "canvasx": staticmethod(lambda x: x),
            "canvasy": staticmethod(lambda y: y),
        },
    )()

    event = types.SimpleNamespace(x=0, y=0)
    GSNDiagramWindow._on_double_click(wnd, event)

    assert opened == {"wp": "WP1"}


def test_double_click_prompts_link_choice(monkeypatch):
    opened = {}

    monkeypatch.setattr(
        "gui.gsn_diagram_window.messagebox.askyesnocancel",
        lambda *a, **k: False,
    )

    def open_wp(name):
        opened["wp"] = name

    monkeypatch.setattr("webbrowser.open", lambda url: opened.setdefault("url", url))

    root = GSNNode("Root", "Goal")
    diag = GSNDiagram(root)
    node = GSNNode("Sol", "Solution")
    node.work_product = "WP1"
    node.evidence_link = "http://example.com"
    diag.add_node(node)

    wnd = GSNDiagramWindow.__new__(GSNDiagramWindow)
    wnd.diagram = diag
    wnd.app = types.SimpleNamespace(open_work_product=open_wp)
    wnd.refresh = lambda: None
    wnd._node_at = lambda x, y: node
    wnd.canvas = type(
        "CanvasStub",
        (),
        {
            "canvasx": staticmethod(lambda x: x),
            "canvasy": staticmethod(lambda y: y),
        },
    )()

    event = types.SimpleNamespace(x=0, y=0)
    GSNDiagramWindow._on_double_click(wnd, event)

    assert opened == {"url": "http://example.com"}


def test_double_click_uses_tool_action():
    called = {}

    def action():
        called["ok"] = True

    root = GSNNode("Root", "Goal")
    diag = GSNDiagram(root)
    node = GSNNode("Sol", "Solution")
    node.work_product = "WP1"
    diag.add_node(node)

    wnd = GSNDiagramWindow.__new__(GSNDiagramWindow)
    wnd.diagram = diag
    wnd.app = types.SimpleNamespace(tool_actions={"WP1": action})
    wnd.refresh = lambda: None
    wnd._node_at = lambda x, y: node
    wnd.canvas = type(
        "CanvasStub",
        (),
        {
            "canvasx": staticmethod(lambda x: x),
            "canvasy": staticmethod(lambda y: y),
        },
    )()

    event = types.SimpleNamespace(x=0, y=0)
    GSNDiagramWindow._on_double_click(wnd, event)

    assert called["ok"]


def test_double_click_falls_back_to_webbrowser(monkeypatch, tmp_path):
    opened = {}

    def fake_run(cmd, check=False):
        opened["cmd"] = cmd

    monkeypatch.setattr(subprocess, "run", fake_run)
    if hasattr(os, "startfile"):
        monkeypatch.setattr(os, "startfile", lambda p: opened.setdefault("startfile", p))

    path = tmp_path / "wp.txt"
    path.write_text("data")

    root = GSNNode("Root", "Goal")
    diag = GSNDiagram(root)
    node = GSNNode("Sol", "Solution")
    node.work_product = str(path)
    diag.add_node(node)

    wnd = GSNDiagramWindow.__new__(GSNDiagramWindow)
    wnd.diagram = diag
    wnd.refresh = lambda: None
    wnd._node_at = lambda x, y: node
    wnd.canvas = type(
        "CanvasStub",
        (),
        {
            "canvasx": staticmethod(lambda x: x),
            "canvasy": staticmethod(lambda y: y),
        },
    )()

    event = types.SimpleNamespace(x=0, y=0)
    GSNDiagramWindow._on_double_click(wnd, event)

    if os.name == "nt":
        assert opened["startfile"] == str(path)
    elif sys.platform == "darwin":
        assert opened["cmd"] == ["open", str(path)]
    else:
        assert opened["cmd"] == ["xdg-open", str(path)]

