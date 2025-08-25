import types
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from gui.architecture import GovernanceDiagramWindow
from gui import architecture


def test_governance_core_has_add_buttons(monkeypatch):
    class DummyFrame:
        def __init__(self, master=None, text=None):
            self.master = master
            self.text = text
            self.children = []
            if master and hasattr(master, "children"):
                master.children.append(self)

        def pack(self, *args, **kwargs):
            pass

        def pack_forget(self, *args, **kwargs):
            pass

        def destroy(self, *args, **kwargs):
            pass

    class DummyButton:
        def __init__(self, master=None, text="", image=None, compound=None, command=None):
            self.master = master
            self.text = text
            self.command = command
            if master and hasattr(master, "children"):
                master.children.append(self)

        def pack(self, *args, **kwargs):
            pass

        def configure(self, **kwargs):
            self.text = kwargs.get("text", self.text)

        def destroy(self):
            pass

    class DummyTranslucidButton(DummyButton):
        pass

    monkeypatch.setattr(architecture.ttk, "Frame", DummyFrame)
    monkeypatch.setattr(architecture.ttk, "LabelFrame", DummyFrame)
    monkeypatch.setattr(architecture.ttk, "Button", DummyButton)
    monkeypatch.setattr(architecture, "TranslucidButton", DummyTranslucidButton)

    win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
    toolbox = DummyFrame()
    toolbox.tk = True
    win.toolbox = toolbox
    win.tools_frame = DummyFrame(toolbox)
    win.rel_frame = DummyFrame(toolbox)
    win._icon_for = lambda name: None
    win.toolbox_selector = types.SimpleNamespace(configure=lambda **k: None)
    win.toolbox_var = types.SimpleNamespace(get=lambda: "Governance Core", set=lambda v: None)
    win._toolbox_frames = {}
    win._rebuild_toolboxes()
    win._switch_toolbox()
    assert "Governance Core" in win._toolbox_frames
    core_frames = win._toolbox_frames["Governance Core"]
    assert win.rel_frame not in core_frames
    actions = core_frames[1]
    buttons = getattr(actions, "children", [])
    labels = [child.text for child in buttons]
    assert {
        "Add Work Product",
        "Add Generic Work Product",
        "Add Lifecycle Phase",
    } <= set(labels)
    assert "Add Process Area" not in labels
    assert all(isinstance(child, DummyTranslucidButton) for child in buttons)

    rel_sections = [
        child
        for child in getattr(core_frames[-1], "children", [])
        if getattr(child, "text", "") == "Relationships"
    ]
    assert len(rel_sections) == 1
    rel_labels = [child.text for child in getattr(rel_sections[0], "children", [])]
    assert len(rel_labels) == len(set(rel_labels))
