<!--
# Author: Miguel Marina <karel.capek.robotics@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 Capek System Safety & Robotic Solutions
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed without any warranty; see the GNU GPL for details.
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <https://www.gnu.org/licenses/>.
-->

# GUI lifecycle stress qualification

Run the repeatable real-Tk qualification on Linux with:

```bash
xvfb-run -a python -m pytest -q -m gui_stress tests/gui/stress
```

The runner enters through `AutoML.main`, creates and shuts down the application
three times, and performs 100 complete workflows in each lifetime. Every diagram
type in `config/rules/diagram_rules.json` is opened, activated, popped into its
own toplevel, focus-alternated with the root, closed in alternating order, and
reintegrated. Each iteration records both toolbox-object and visual-host-object
identity. Assertions ensure that focus or disposal of one host never destroys,
replaces, or aliases another host's toolbox.

## Pass criteria

The command must exit zero, complete all 300 workflows, and produce none of
these stderr diagnostics (matching is case-insensitive): `Tcl_AsyncDelete`,
`invalid command name`, `callback after disposal`, `widget after destruction`,
or `owner thread`. The last signature makes the centralized owner-thread
assertions fail the run. A skip because no display server is available is not a
qualification pass; use Xvfb or a native display.

Supporting tests are grouped by owner-thread enforcement, callback lifecycle,
toolbox reconstruction, popout lifecycle, shutdown ordering, and repeated
startup/shutdown so qualification evidence remains reviewable and scalable.
