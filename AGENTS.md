# AGENTS.md

## Cursor Cloud specific instructions

These notes capture non-obvious, durable context for running and developing
this codebase in the Cursor Cloud environment. Dependency installation is
handled automatically by the environment update script, so it is intentionally
omitted here.

### What this product is

AutoML (`AutoML-Analyzer`) is a **Tkinter desktop GUI** for automotive
safety/cybersecurity modeling (ISO 26262 / 21448 / 21434 / 8800): FTA, FMEA,
HAZOP, HARA, GSN, SysML-style architecture, requirements, etc. It is a single
desktop application — there is no server/web component and no database.

- Launcher entry point: `python AutoML.py` (a wrapper that bootstraps and then
  runs `mainappsrc/core/automl_core.py:main`). See the README "Getting Started"
  and "Dependencies" sections for the standard workflow.
- Version lives in `mainappsrc/version.py`.

### Displays (important — this is a GUI app)

Anything that touches Tk needs an X display.

- **Interactive/visual runs**: the Cursor Desktop pane is a TigerVNC session on
  `DISPLAY=:1`. Launch the GUI there so it is visible in the Desktop pane, e.g.
  `DISPLAY=:1 python AutoML.py`.
- **Headless test runs**: use a virtual framebuffer. Either `xvfb-run -a python -m pytest ...`
  or start a persistent server once (`Xvfb :99 -screen 0 1600x1000x24 &`) and
  export `DISPLAY=:99`. Tests that call `tk.Tk()` self-skip with `pytest.skip`
  when no display is available, so running without a display silently skips much
  of the suite — always run tests under Xvfb.

### Running the test suite

- Command: `DISPLAY=:99 python -m pytest -q` (the `pytest` console script is in
  `~/.local/bin`, which is not on `PATH`; invoke via `python -m pytest`).
- The GUI lifecycle stress qualification is documented in
  `docs/developer_gui_stress.md` (`xvfb-run -a python -m pytest -q -m gui_stress tests/gui/stress`).
- **pytest must be `<9`.** The repo ships a stub `PyQt6/__init__.py` that raises a
  plain `ImportError`, and several tests rely on `pytest.importorskip("PyQt6")`
  skipping on that. pytest 9.1 changed `importorskip` to only catch
  `ModuleNotFoundError` by default, which turns those skips into collection
  errors. The update script pins `pytest<9`.
- **A large number of tests currently fail on `main` due to pre-existing source
  bugs, not the environment.** At the time this file was written ~1085 passed
  and ~470 failed. Examples of genuine code defects (undefined names /
  attributes) reachable from the tests and the GUI: `GovernanceManager` used but
  never imported in `mainappsrc/core/automl_core.py`, an undefined `dock_window`
  in the same file, `collect_work_product_names` in `gui/explorers/gsn_explorer.py`,
  and `config_service.reload_local_config`. Treat these as application bugs to fix
  in feature work; do not assume the environment is broken because tests fail.

### Vendored dependency stubs (surprising import behavior)

The repo root contains lightweight stand-ins: `matplotlib/`, `PyQt6/`,
`networkx/`, and `reportlab/`. Because the repo root is first on `sys.path`,
`import matplotlib` resolves to the **in-repo stub**, not the pip-installed
matplotlib, when running from the repo root. `networkx` and `reportlab` stubs
detect and defer to a real installation; `matplotlib` and `PyQt6` do not. This
is intentional so the headless test suite and GUI can run without the heavy real
packages. Keep this in mind when a matplotlib/PyQt feature "isn't installed" —
you are hitting the stub.

### Linting

There is no configured linter (no flake8/ruff/black/pre-commit config). Use
`python -m compileall AutoML.py mainappsrc gui analysis tools config` as a quick
syntax check.

### Misc

- `examples/MiniExample.autml` is Fernet-encrypted (password-protected); it can't
  be opened without the password.
- Ghostscript is only auto-installed/required on Windows; on Linux the code
  treats it as available.
