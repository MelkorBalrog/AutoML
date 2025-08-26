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
"""Service wrapper around user configuration helpers."""

from __future__ import annotations

from analysis import user_config as _uc


class UserConfigService:
    """Provide a service interface over ``analysis.user_config``."""

    def load_all_users(self) -> dict:
        return _uc.load_all_users()

    def get_last_user(self) -> str:
        return _uc.get_last_user()

    def load_user_config(self):
        return _uc.load_user_config()

    def save_user_config(self, name: str, email: str) -> None:
        _uc.save_user_config(name, email)

    def set_last_user(self, name: str) -> None:
        _uc.set_last_user(name)

    def set_current_user(self, name: str, email: str) -> None:
        _uc.set_current_user(name, email)

    @property
    def current_user_name(self) -> str:
        return _uc.CURRENT_USER_NAME

    @property
    def current_user_email(self) -> str:
        return _uc.CURRENT_USER_EMAIL


user_config_service = UserConfigService()

__all__ = ["UserConfigService", "user_config_service"]
