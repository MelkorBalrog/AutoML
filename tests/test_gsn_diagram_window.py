import tkinter as tk
import types
import csv
import tempfile
from unittest import mock

import gui.gsn_diagram_window as gdw
from gui.gsn_diagram_window import GSNDiagramWindow
from gsn import GSNNode, GSNDiagram, GSNModule


def test_gsn_diagram_window_button_labels():
    labels = GSNDiagramWindow.TOOLBOX_BUTTONS
    assert "Goal" in labels
    assert "Solved By" in labels
    assert "In Context Of" in labels
    assert "Zoom In" in labels
    assert "Module" in labels


def test_zoom_methods_adjust_factor():
    win = GSNDiagramWindow.__new__(GSNDiagramWindow)
    win.zoom = 1.0
    win.refresh = lambda: None
    GSNDiagramWindow.zoom_in(win)
    assert win.zoom > 1.0
    GSNDiagramWindow.zoom_out(win)
    assert abs(win.zoom - 1.0) < 1e-6


def test_temp_connection_line_is_dotted():
    """Dragging in connect mode should draw a dotted preview line."""
    win = GSNDiagramWindow.__new__(GSNDiagramWindow)
    win.zoom = 1.0
    win._connect_mode = "solved"
    win._connect_parent = GSNNode("p", "Goal", x=10, y=20)
    win._drag_node = None
    lines = []

    class CanvasStub:
        def canvasx(self, x):
            return x

        def canvasy(self, y):
            return y

        def create_line(self, *args, **kwargs):
            lines.append(kwargs)

        def delete(self, *args, **kwargs):
            pass

    win.canvas = CanvasStub()
    event = type("Event", (), {"x": 100, "y": 100})
    win._on_drag(event)
    assert lines and lines[0].get("dash") == (2, 2)
    assert lines[0].get("arrow") == tk.LAST


def test_temp_connection_line_has_arrow_in_context_mode():
    """Context connections preview with an arrow."""
    win = GSNDiagramWindow.__new__(GSNDiagramWindow)
    win.zoom = 1.0
    win._connect_mode = "context"
    win._connect_parent = GSNNode("p", "Goal", x=10, y=20)
    win._drag_node = None
    lines = []

    class CanvasStub:
        def canvasx(self, x):
            return x

        def canvasy(self, y):
            return y

        def create_line(self, *args, **kwargs):
            lines.append(kwargs)

        def delete(self, *args, **kwargs):
            pass

    win.canvas = CanvasStub()
    event = type("Event", (), {"x": 50, "y": 50})
    win._on_drag(event)
    assert lines and lines[0].get("dash") == (2, 2)
    assert lines[0].get("arrow") == tk.LAST


def test_on_release_creates_context_link():
    """Releasing in context mode should mark the relation accordingly."""
    win = GSNDiagramWindow.__new__(GSNDiagramWindow)
    parent = GSNNode("p", "Goal")
    child = GSNNode("c", "Context")

    class CanvasStub:
        def __init__(self):
            self.cursor = None

        def canvasx(self, x):
            return x

        def canvasy(self, y):
            return y

        def delete(self, *a, **k):
            pass

        def configure(self, **kwargs):
            if "cursor" in kwargs:
                self.cursor = kwargs["cursor"]

    win.canvas = CanvasStub()
    win._node_at = lambda x, y: child
    win.refresh = lambda: None

    GSNDiagramWindow.connect_in_context(win)
    assert win.canvas.cursor == "hand2"
    win._connect_parent = parent
    event = type("Event", (), {"x": 0, "y": 0})
    win._on_release(event)
    assert child in parent.children
    assert child in parent.context_children
    assert win.canvas.cursor == ""


def test_solved_by_cursor_and_reset():
    """Solved-by connections change the cursor and reset after completion."""
    win = GSNDiagramWindow.__new__(GSNDiagramWindow)
    parent = GSNNode("p", "Goal")
    child = GSNNode("c", "Goal")

    class CanvasStub:
        def __init__(self):
            self.cursor = None

        def canvasx(self, x):
            return x

        def canvasy(self, y):
            return y

        def delete(self, *a, **k):
            pass

        def configure(self, **kwargs):
            if "cursor" in kwargs:
                self.cursor = kwargs["cursor"]

    win.canvas = CanvasStub()
    win._node_at = lambda x, y: child
    win.refresh = lambda: None

    GSNDiagramWindow.connect_solved_by(win)
    assert win.canvas.cursor == "tcross"
    win._connect_parent = parent
    event = type("Event", (), {"x": 0, "y": 0})
    win._on_release(event)
    assert child in parent.children
    assert child not in parent.context_children
    assert win.canvas.cursor == ""


def test_refresh_updates_scrollregion():
    """Refresh should configure the canvas scrollregion."""
    win = GSNDiagramWindow.__new__(GSNDiagramWindow)
    win.selected_node = None
    win.zoom = 1.0

    class DiagramStub:
        def _traverse(self):
            return []

        def draw(self, canvas, zoom):
            pass

    win.diagram = DiagramStub()

    class CanvasStub:
        def __init__(self):
            self.config = {}

        def delete(self, *a, **k):
            pass

        def bbox(self, tag):
            return (0, 0, 100, 100)

        def configure(self, **kwargs):
            self.config.update(kwargs)

        def create_rectangle(self, *args, **kwargs):
            pass

    win.canvas = CanvasStub()
    win.id_to_node = {}
    win.refresh()
    assert win.canvas.config.get("scrollregion") == (0, 0, 100, 100)


def test_click_and_drag_uses_canvas_coordinates():
    """Selection and dragging should honour canvas scrolling."""
    win = GSNDiagramWindow.__new__(GSNDiagramWindow)
    win.zoom = 1.0
    win._connect_mode = None
    win.refresh = lambda: None
    node = GSNNode("n", "Goal", x=150, y=250)

    class CanvasStub:
        def __init__(self):
            self.off_x = 100
            self.off_y = 200

        def canvasx(self, x):
            return x + self.off_x

        def canvasy(self, y):
            return y + self.off_y

        def find_overlapping(self, x1, y1, x2, y2):
            if x1 <= 150 <= x2 and y1 <= 250 <= y2:
                return [1]
            return []

        def gettags(self, item):
            return ("node-id",) if item == 1 else ()

        def delete(self, *args, **kwargs):
            pass

        def after(self, *args, **kwargs):
            return None

        def after_cancel(self, *args, **kwargs):
            pass

        def create_line(self, *args, **kwargs):
            pass

        def bbox(self, tag):
            return (0, 0, 0, 0)

    win.canvas = CanvasStub()
    win.id_to_node = {"node-id": node}

    event = type("Evt", (), {"x": 50, "y": 50})
    win._on_click(event)
    assert win.selected_node is node

    drag = type("Evt", (), {"x": 60, "y": 60})
    win._on_drag(drag)
    assert node.x == 160 and node.y == 260


def test_add_module_uses_existing_modules(monkeypatch):
    app = types.SimpleNamespace(gsn_modules=[GSNModule("Pkg1"), GSNModule("Pkg2")])
    diagram = GSNDiagram(GSNNode("r", "Goal"))
    win = GSNDiagramWindow.__new__(GSNDiagramWindow)
    win.app = app
    win.diagram = diagram
    win.selected_node = None
    win.refresh = lambda: None
    class DummyDialog:
        def __init__(self, *a, **k):
            self.selection = "Pkg2"

    monkeypatch.setattr(gdw, "ModuleSelectDialog", DummyDialog)
    GSNDiagramWindow.add_module(win)
    names = [n.user_name for n in diagram.nodes if n.node_type == "Module"]
    assert names == ["Pkg2"]


def test_right_click_node_shows_menu(monkeypatch):
    """Right-clicking a node should show edit and delete options."""
    win = GSNDiagramWindow.__new__(GSNDiagramWindow)
    node = GSNNode("n", "Goal")
    win.id_to_node = {node.unique_id: node}
    win.id_to_relation = {}
    win.canvas = type(
        "CanvasStub",
        (),
        {
            "canvasx": lambda self, x: x,
            "canvasy": lambda self, y: y,
            "find_overlapping": lambda self, a, b, c, d: [1],
            "gettags": lambda self, item: (node.unique_id,),
        },
    )()
    captured = {}

    class MenuStub:
        def __init__(self, *a, **k):
            captured["menu"] = self
            self.items = []

        def add_command(self, label, command):
            self.items.append(label)

        def tk_popup(self, x, y):
            pass

        def grab_release(self):
            pass

    monkeypatch.setattr(tk, "Menu", MenuStub)
    win._edit_node = lambda n: None
    win._delete_node = lambda n: None
    win._move_node_forward = lambda n: None
    win._move_node_back = lambda n: None
    event = type("Evt", (), {"x": 0, "y": 0, "x_root": 0, "y_root": 0})
    GSNDiagramWindow._on_right_click(win, event)
    assert captured["menu"].items == [
        "Edit",
        "Delete",
        "Move Forward",
        "Move Back",
    ]


def test_right_click_connection_shows_menu(monkeypatch):
    """Right-clicking a connection should show edit and delete options."""
    win = GSNDiagramWindow.__new__(GSNDiagramWindow)
    parent = GSNNode("p", "Goal")
    child = GSNNode("c", "Goal")
    rel_id = win._rel_id(parent, child)
    win.id_to_node = {}
    win.id_to_relation = {rel_id: (parent, child)}
    win.canvas = type(
        "CanvasStub",
        (),
        {
            "canvasx": lambda self, x: x,
            "canvasy": lambda self, y: y,
            "find_overlapping": lambda self, a, b, c, d: [1],
            "gettags": lambda self, item: (rel_id,),
        },
    )()
    captured = {}

    class MenuStub:
        def __init__(self, *a, **k):
            captured["menu"] = self
            self.items = []

        def add_command(self, label, command):
            self.items.append(label)

        def tk_popup(self, x, y):
            pass

        def grab_release(self):
            pass

    monkeypatch.setattr(tk, "Menu", MenuStub)
    win._edit_connection = lambda p, c: None
    win._delete_connection = lambda p, c: None
    event = type("Evt", (), {"x": 0, "y": 0, "x_root": 0, "y_root": 0})
    GSNDiagramWindow._on_right_click(win, event)
    assert captured["menu"].items == ["Edit", "Delete"]


def test_move_node_forward_and_back_adjusts_layers():
    """Moving nodes should reorder them without disturbing connectors."""
    win = GSNDiagramWindow.__new__(GSNDiagramWindow)
    parent = GSNNode("p", "Goal")
    child = GSNNode("c", "Goal")
    rel_id = win._rel_id(parent, child)
    win.id_to_relation = {rel_id: (parent, child)}

    class CanvasStub:
        def __init__(self):
            self.raised = []
            self.lowered = []

        def tag_raise(self, tag):
            self.raised.append(tag)

        def tag_lower(self, tag):
            self.lowered.append(tag)

    win.canvas = CanvasStub()
    node = GSNNode("n", "Goal")

    win._move_node_forward(node)
    assert node.unique_id in win.canvas.raised
    assert rel_id in win.canvas.lowered
    assert f"{rel_id}-arrow" in win.canvas.raised

    win.canvas.raised.clear()
    win.canvas.lowered.clear()

    win._move_node_back(node)
    assert node.unique_id in win.canvas.lowered
    assert rel_id in win.canvas.lowered
    assert f"{rel_id}-arrow" in win.canvas.raised


def test_refresh_sets_app_for_spi_lookup():
    root = GSNNode("Root", "Goal")
    sol = GSNNode("Sol", "Solution")
    sol.spi_target = "Brake Time (SOTIF)"
    root.add_child(sol)
    diag = GSNDiagram(root)
    diag.add_node(sol)

    class TopEvent:
        def __init__(self):
            self.user_name = "Brake Time"
            self.validation_desc = "Brake Time"
            self.validation_target = "1e-5"

    app = types.SimpleNamespace(top_events=[TopEvent()])

    win = GSNDiagramWindow.__new__(GSNDiagramWindow)
    win.app = app
    win.diagram = diag
    win.zoom = 1.0
    win.selected_node = None
    win.id_to_node = {}
    win.id_to_relation = {}

    captured = {}

    def draw(canvas, zoom):
        captured["text"] = diag._format_text(sol)

    diag.draw = draw
    diag._traverse = lambda: [root, sol]

    class CanvasStub:
        def delete(self, *a, **k):
            pass

        def bbox(self, tag):
            return (0, 0, 0, 0)

        def configure(self, **k):
            pass

    win.canvas = CanvasStub()

    GSNDiagramWindow.refresh(win)
    assert diag.app is app
    assert "SPI: 1e-5/h" in captured.get("text", "")


def test_export_csv_writes_nodes(tmp_path, monkeypatch):
    root = GSNNode("Root", "Goal")
    child = GSNNode("Child", "Solution")
    root.add_child(child)
    diag = GSNDiagram(root)
    diag.add_node(child)
    win = GSNDiagramWindow.__new__(GSNDiagramWindow)
    win.diagram = diag
    path = tmp_path / "out.csv"
    monkeypatch.setattr(gdw.filedialog, "asksaveasfilename", lambda **k: str(path))
    GSNDiagramWindow.export_csv(win)
    with open(path, newline="") as f:
        rows = list(csv.reader(f))
    assert rows[0] == ["ID", "Name", "Type", "Description", "Children", "Context"]
    assert [root.unique_id, "Root", "Goal", "", child.unique_id, ""] in rows
    assert [child.unique_id, "Child", "Solution", "", "", ""] in rows


def test_gsn_diagram_window_binds_undo_redo():
    win = GSNDiagramWindow.__new__(GSNDiagramWindow)
    bindings = {}

    def fake_bind(seq, func):
        bindings[seq] = func

    win.bind = fake_bind
    calls = []
    win.app = types.SimpleNamespace(
        undo=lambda: calls.append("undo"),
        redo=lambda: calls.append("redo"),
    )
    GSNDiagramWindow._bind_shortcuts(win)
    assert "<Control-z>" in bindings and "<Control-y>" in bindings
    bindings["<Control-z>"](None)
    bindings["<Control-y>"](None)
    assert calls == ["undo", "redo"]
