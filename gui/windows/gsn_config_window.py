"""Configuration dialog for editing GSN node properties."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from mainappsrc.models.gsn import GSNNode, GSNDiagram


def _collect_work_products(diagram: GSNDiagram, app=None) -> list[str]:
    """Return sorted unique work product names for *diagram*.

    The list includes ``work_product`` attributes from existing solution
    nodes and any registered work products from the application's safety
    management toolbox.  When supplied, *app* should provide a
    ``safety_mgmt_toolbox`` attribute with a ``get_work_products`` method.
    """

    products = {
        getattr(n, "work_product", "")
        for n in getattr(diagram, "nodes", [])
        if getattr(n, "work_product", "")
    }

    if app is None:
        app = getattr(diagram, "app", None)
    toolbox = getattr(app, "safety_mgmt_toolbox", None)
    if toolbox:
        # Include diagrams tracked by the toolbox even when not part of a
        # registered work product so users can reference them directly.
        for name in getattr(toolbox, "list_diagrams", lambda: [])():
            if name:
                products.add(name)

        for wp in getattr(toolbox, "get_work_products", lambda: [])():
            if isinstance(wp, dict):
                diag_name = wp.get("diagram", "")
                analysis_name = wp.get("analysis", "")
            else:
                diag_name = getattr(wp, "diagram", "")
                analysis_name = getattr(wp, "analysis", "")

            if diag_name:
                products.add(diag_name)
            if analysis_name:
                products.add(analysis_name)
            if diag_name and analysis_name:
                products.add(f"{diag_name} - {analysis_name}")

    if app:
        # Reuse helpers that supply items for the Analyses & Architecture
        # combo boxes so the work product list remains consistent with those
        # dialogs.  Fallback to common attributes when the helpers are absent.
        for name in getattr(app, "get_architecture_box_list", lambda: [])():
            if name:
                products.add(name)
        for name in getattr(app, "get_analysis_box_list", lambda: [])():
            if name:
                products.add(name)

        if not hasattr(app, "get_architecture_box_list"):
            for diag in getattr(app, "arch_diagrams", []):
                name = getattr(diag, "name", "") or getattr(diag, "diag_id", "")
                if name:
                    products.add(name)
        if not hasattr(app, "get_analysis_box_list"):
            for ra in getattr(app, "reliability_analyses", []):
                name = getattr(ra, "name", "")
                if name:
                    products.add(name)

    return sorted(products)

def _collect_spi_targets(diagram: GSNDiagram, app=None) -> list[str]:
    """Return sorted list of SPI targets available for *diagram*.

    Besides existing solution nodes in the diagram, this also includes
    validation targets defined on the application's top level product goals
    when an ``app`` instance is provided.  Duplicates and empty entries are
    removed.  If a product goal lacks a target description, fall back to the
    safety goal description or the node's name so that at least one identifier
    is presented to the user.
    """

    targets = {
        getattr(n, "spi_target", "")
        for n in getattr(diagram, "nodes", [])
        if getattr(n, "spi_target", "")
    }
    if app is None:
        app = getattr(diagram, "app", None)
    if app:
        if hasattr(app, "get_spi_targets"):
            targets.update(app.get_spi_targets())
        else:
            for te in getattr(app, "top_events", []):
                name = (
                    getattr(te, "validation_desc", "")
                    or getattr(te, "safety_goal_description", "")
                    or getattr(te, "user_name", "")
                )
                if name:
                    targets.add(name)
    return sorted(targets)


class GSNElementConfig(tk.Toplevel):
    """Simple dialog to edit a GSN element's properties."""

    def __init__(self, master, node: GSNNode, diagram: GSNDiagram):
        super().__init__(master)
        self.node = node
        self.diagram = diagram
        self.title("Edit GSN Element")
        self.geometry("400x360")
        self.columnconfigure(1, weight=1)
        # Allow both text fields to expand when the dialog is resized
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        tk.Label(self, text="Name:").grid(row=0, column=0, sticky="e", padx=4, pady=4)
        self.name_var = tk.StringVar(value=node.user_name)
        tk.Entry(self, textvariable=self.name_var, width=40).grid(
            row=0, column=1, padx=4, pady=4, sticky="ew"
        )
        tk.Label(self, text="Description:").grid(row=1, column=0, sticky="ne", padx=4, pady=4)
        self.desc_text = tk.Text(self, width=40, height=5)
        self.desc_text.insert("1.0", getattr(node, "description", ""))
        self.desc_text.grid(row=1, column=1, padx=4, pady=4, sticky="nsew")

        tk.Label(self, text="Notes:").grid(row=2, column=0, sticky="ne", padx=4, pady=4)
        self.notes_text = tk.Text(self, width=40, height=5)
        self.notes_text.insert("1.0", getattr(node, "manager_notes", ""))
        self.notes_text.grid(row=2, column=1, padx=4, pady=4, sticky="nsew")

        self.work_var = tk.StringVar(value=getattr(node, "work_product", ""))
        self.link_var = tk.StringVar(value=getattr(node, "evidence_link", ""))
        row = 3
        self.spi_var = tk.StringVar(value=getattr(node, "spi_target", ""))
        if node.node_type == "Solution":
            tk.Label(self, text="Work Product:").grid(
                row=row, column=0, sticky="e", padx=4, pady=4
            )
            work_products = _collect_work_products(diagram, getattr(master, "app", None))
            if self.work_var.get() and self.work_var.get() not in work_products:
                work_products.append(self.work_var.get())
            wp_cb = ttk.Combobox(
                self,
                textvariable=self.work_var,
                state="readonly",
            )
            wp_cb.grid(row=row, column=1, padx=4, pady=4, sticky="ew")
            # Explicitly configure the combobox values after creation so Tk
            # updates the drop-down list reliably across platforms.  Passing
            # ``values`` to the constructor can result in an empty list on
            # some systems.
            wp_cb.configure(values=work_products)
            # Leave the selection blank until the user picks a work product.
            # ``state='readonly'`` prevents arbitrary text input while still
            # allowing an empty initial value.
            row += 1
            tk.Label(self, text="Evidence Link:").grid(
                row=row, column=0, sticky="e", padx=4, pady=4
            )
            tk.Entry(self, textvariable=self.link_var, width=40).grid(
                row=row, column=1, padx=4, pady=4, sticky="ew"
            )
            row += 1
            tk.Label(self, text="Validation Target:").grid(
                row=row, column=0, sticky="e", padx=4, pady=4
            )
            spi_targets = _collect_spi_targets(diagram, getattr(master, "app", None))
            if self.spi_var.get() and self.spi_var.get() not in spi_targets:
                spi_targets.append(self.spi_var.get())
            spi_cb = ttk.Combobox(
                self,
                textvariable=self.spi_var,
                state="readonly",
            )
            spi_cb.grid(row=row, column=1, padx=4, pady=4, sticky="ew")
            spi_cb.configure(values=spi_targets)
            row += 1
        btns = ttk.Frame(self)
        btns.grid(row=row, column=0, columnspan=2, pady=4)
        ttk.Button(btns, text="OK", command=self._on_ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=4)
        self.transient(master)
        self.grab_set()
        self.wait_window(self)

    # ------------------------------------------------------------------
    def _sync_clones_strategy1(self, original, attrs):
        for attr in attrs:
            setattr(original, attr, getattr(self.node, attr))
        original.is_primary_instance = True
        original.original = original
        for n in getattr(self.diagram, "nodes", []):
            if n is not original and getattr(n, "original", None) is original:
                for attr in attrs:
                    setattr(n, attr, getattr(original, attr))
                n.original = original
                n.is_primary_instance = False

    def _sync_clones_strategy2(self, original, attrs):
        values = {a: getattr(self.node, a) for a in attrs}
        for a, v in values.items():
            setattr(original, a, v)
        original.is_primary_instance = True
        original.original = original
        clones = [n for n in getattr(self.diagram, "nodes", []) if n is not original and getattr(n, "original", None) is original]
        for c in clones:
            for a, v in values.items():
                setattr(c, a, v)
            c.original = original
            c.is_primary_instance = False

    def _sync_clones_strategy3(self, original, attrs):
        for attr in attrs:
            value = getattr(self.node, attr)
            setattr(original, attr, value)
        original.is_primary_instance = True
        original.original = original
        for n in list(getattr(self.diagram, "nodes", [])):
            if n is original:
                continue
            if getattr(n, "original", None) is original:
                for attr in attrs:
                    setattr(n, attr, getattr(original, attr))
                n.original = original
                n.is_primary_instance = False

    def _sync_clones_strategy4(self, original, attrs):
        mapping = [(a, getattr(self.node, a)) for a in attrs]
        for a, v in mapping:
            setattr(original, a, v)
        original.is_primary_instance = True
        original.original = original
        nodes = getattr(self.diagram, "nodes", [])
        for n in nodes:
            if n is original or getattr(n, "original", None) is not original:
                continue
            for a, v in mapping:
                setattr(n, a, getattr(original, a))
            n.original = original
            n.is_primary_instance = False

    def _sync_clones(self, original, attrs):
        for strat in (
            self._sync_clones_strategy1,
            self._sync_clones_strategy2,
            self._sync_clones_strategy3,
            self._sync_clones_strategy4,
        ):
            try:
                strat(original, attrs)
                return
            except Exception:
                continue

    def _on_ok(self):
        self.node.user_name = self.name_var.get()
        self.node.description = self.desc_text.get("1.0", tk.END).strip()
        notes_text = getattr(self, "notes_text", None)
        if notes_text:
            self.node.manager_notes = notes_text.get("1.0", tk.END).strip()
        attrs = ["user_name", "description", "manager_notes"]
        if self.node.node_type == "Solution":
            # ``GSNElementConfig`` is sometimes instantiated in tests without
            # running ``__init__``.  Guard against missing StringVar
            # attributes so :meth:`_on_ok` can operate on these lightweight
            # instances as well.
            work_var = getattr(self, "work_var", None)
            link_var = getattr(self, "link_var", None)
            spi_var = getattr(self, "spi_var", None)
            if work_var:
                self.node.work_product = work_var.get()
            if link_var:
                self.node.evidence_link = link_var.get()
            if spi_var:
                self.node.spi_target = spi_var.get()
            attrs.extend(["work_product", "evidence_link", "spi_target"])
            original = None
            for n in getattr(self.diagram, "nodes", []):
                if (
                    n is not self.node
                    and n.node_type == "Solution"
                    and getattr(n, "work_product", "") == self.node.work_product
                    and getattr(n, "spi_target", "") == self.node.spi_target
                ):
                    original = n if n.is_primary_instance else n.original
                    break
            if original is None:
                original = self.node.original or self.node
        else:
            original = self.node.original or self.node
        self.node.original = original
        self.node.is_primary_instance = self.node is original
        self._sync_clones(original, attrs)
        self.destroy()
