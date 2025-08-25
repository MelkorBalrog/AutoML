#!/usr/bin/env python3

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

"""Wrapper launcher for AutoML.

This script ensures required third-party packages are available before
executing :mod:`AutoML`.  When run inside the PyInstaller-built
executable the dependencies are already bundled so the installation step
is skipped.
"""
import argparse
import importlib
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Ensure bundled executables can import sibling packages
if getattr(sys, "frozen", False):
    _ROOT = Path(sys._MEIPASS)
else:
    _ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from tools.crash_report_logger import install_best
from tools.memory_manager import manager as memory_manager
from tools.splash_launcher import SplashLauncher
from mainappsrc.version import VERSION
from mainappsrc.core.automl_core import (
    AutoMLApp,
    FaultTreeNode,
    AutoML_Helper,
    messagebox,
    GATE_NODE_TYPES,
)
from mainappsrc.core.safety_analysis import SafetyAnalysis_FTA_FMEA
from mainappsrc.page_diagram import PageDiagram
import tkinter.font as tkFont
from gui.utils.drawing_helper import fta_drawing_helper
from config.automl_constants import PMHF_TARGETS
from analysis.models import HazopDoc
from gui.dialogs.edit_node_dialog import EditNodeDialog
from analysis.risk_assessment import AutoMLHelper

__all__ = [
    "AutoMLApp",
    "FaultTreeNode",
    "AutoML_Helper",
    "messagebox",
    "GATE_NODE_TYPES",
    "PMHF_TARGETS",
    "HazopDoc",
    "EditNodeDialog",
    "SafetyAnalysis_FTA_FMEA",
    "AutoMLHelper",
    "PageDiagram",
    "tkFont",
    "fta_drawing_helper",
]

# Hint PyInstaller to bundle AutoML and its dependencies (e.g. gui package)
if False:  # pragma: no cover
    import AutoML  # noqa: F401
    Path(r"C:\\Program Files\\gs\\gs10.04.0\\bin\\gswin64c.exe")

REQUIRED_PACKAGES = [
    "pillow",
    "openpyxl",
    "networkx",
    "matplotlib",
    "reportlab",
    "adjustText",
]

GS_PATH = Path(r"C:\\Program Files\\gs\\gs10.04.0\\bin\\gswin64c.exe")


def parse_args() -> None:
    """Handle command line arguments for the launcher."""

    parser = argparse.ArgumentParser(
        description=(
            f"Launch the AutoML application (v{VERSION}) with centralized project "
            "configuration management"
        )
    )
    parser.add_argument("--version", action="version", version=VERSION)
    parser.parse_args()


def _install_ghostscript_via_winget() -> bool:
    """Attempt installation using winget."""
    try:
        subprocess.check_call([
            "winget",
            "install",
            "--id",
            "Ghostscript.Ghostscript",
            "-e",
            "--silent",
        ])
        return True
    except Exception:
        return False


def _install_ghostscript_via_choco() -> bool:
    """Attempt installation using Chocolatey."""
    try:
        subprocess.check_call(["choco", "install", "ghostscript", "-y"])
        return True
    except Exception:
        return False


def _install_ghostscript_via_powershell() -> bool:
    """Download and install Ghostscript via PowerShell."""
    url = "https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/download/gs10040/gs10040w64.exe"
    script = (
        f"Invoke-WebRequest -Uri {url} -OutFile gs.exe;"
        "Start-Process gs.exe -ArgumentList '/S' -NoNewWindow -Wait"
    )
    try:
        subprocess.check_call(["powershell", "-Command", script])
        return True
    except Exception:
        return False


def _install_ghostscript_via_pip() -> bool:
    """Fallback installation using pip ghostscript wrapper."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "ghostscript"])
        return True
    except Exception:
        return False


def ensure_ghostscript() -> None:
    """Ensure Ghostscript is available on Windows systems.

    The function attempts four different installation mechanisms to provide
    robustness across environments.  If all methods fail, a ``RuntimeError``
    is raised to signal the missing dependency.
    """
    if os.name != "nt":
        return
    if GS_PATH.exists():
        return
    installers = [
        _install_ghostscript_via_winget,
        _install_ghostscript_via_choco,
        _install_ghostscript_via_powershell,
        _install_ghostscript_via_pip,
    ]
    for installer in installers:
        if installer():
            if GS_PATH.exists():
                return
    raise RuntimeError("Ghostscript installation failed")


def ensure_packages() -> None:
    """Install any missing runtime dependencies.

    When running from a PyInstaller executable, the packages are already
    bundled and pip is not available, so the function simply returns.
    """
    if getattr(sys, "frozen", False):
        return

    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing.append(pkg)

    if not missing:
        return

    def install(pkg: str) -> None:
        proc = subprocess.Popen([sys.executable, "-m", "pip", "install", pkg])
        memory_manager.register_process(pkg, proc)
        proc.wait()

    with ThreadPoolExecutor() as executor:
        executor.map(install, missing)
    memory_manager.cleanup()


def _bootstrap() -> object:
    """Run startup checks while the splash screen is displayed.

    Returns
    -------
    Module
        The main application module which provides a ``main`` entry point.
    """

    parse_args()
    install_best()
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(ensure_packages),
            executor.submit(ensure_ghostscript),
        ]
        for f in futures:
            f.result()
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    # Insert both the launcher directory and the 'mainappsrc' module location to ensure
    # the project-specific AutoML module is discovered rather than any similarly
    # named third-party package that may be installed in the environment.
    mainappsrc_path = base_path / "mainappsrc"
    for path in (str(mainappsrc_path), str(base_path)):
        if path not in sys.path:
            sys.path.insert(0, path)
    return importlib.import_module("mainappsrc.automl_core")


def main() -> None:
    """Entry point used by both source and bundled executions."""
    SplashLauncher(loader=_bootstrap, post_delay=5000).launch()
    memory_manager.cleanup()

if __name__ == "__main__":
    main()
