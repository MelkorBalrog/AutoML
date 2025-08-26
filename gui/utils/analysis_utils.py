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

from __future__ import annotations

"""Analysis utility mixins for :class:`AutoMLApp`."""


from analysis.mechanisms import (
    MechanismLibrary,
    ANNEX_D_MECHANISMS,
    PAS_8800_MECHANISMS,
)


class AnalysisUtilsMixin:
    """Reusable analysis helpers extracted from ``automl_core``."""

    def classify_scenarios(self):
        """Return two lists of scenario names grouped by category."""
        use_case: list[str] = []
        sotif: list[str] = []
        for lib in self.scenario_libraries:
            for sc in lib.get("scenarios", []):
                if isinstance(sc, dict):
                    name = sc.get("name", "")
                    if (
                        sc.get("tcs")
                        or sc.get("fis")
                        or sc.get("tc")
                        or sc.get("fi")
                        or sc.get("type") == "sotif"
                    ):
                        sotif.append(name)
                    else:
                        use_case.append(name)
                else:
                    use_case.append(sc)
        return {"use_case": use_case, "sotif": sotif}

    def load_default_mechanisms(self):
        """Ensure the built-in diagnostic mechanism libraries are present."""
        defaults = {
            "ISO 26262 Annex D": ANNEX_D_MECHANISMS,
            "PAS 8800": PAS_8800_MECHANISMS,
        }
        existing = {lib.name: lib for lib in self.mechanism_libraries}
        for name, mechanisms in defaults.items():
            lib = existing.get(name)
            if lib is None:
                lib = MechanismLibrary(name, mechanisms.copy())
                self.mechanism_libraries.append(lib)
                existing[name] = lib
            if lib not in self.selected_mechanism_libraries:
                self.selected_mechanism_libraries.append(lib)

