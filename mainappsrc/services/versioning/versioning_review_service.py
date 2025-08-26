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
"""Versioning and review service wrapper."""

from __future__ import annotations

from typing import Any


class VersioningReviewService:
    """Delegate review and version operations to :class:`ReviewManager`."""

    def __init__(self, app: Any) -> None:  # pragma: no cover - simple container
        self.app = app

    def add_version(self):
        return self.app.review_manager.add_version()

    def compare_versions(self):
        return self.app.review_manager.compare_versions()

    def open_review_document(self, review):
        return self.app.review_manager.open_review_document(review)

    def open_review_toolbox(self):
        return self.app.review_manager.open_review_toolbox()

    def start_joint_review(self):
        return self.app.review_manager.start_joint_review()

    def start_peer_review(self):
        return self.app.review_manager.start_peer_review()

    def merge_review_comments(self):
        return self.app.review_manager.merge_review_comments()

    def send_review_email(self, review):
        return self.app.review_manager.send_review_email(review)

    def review_is_closed(self):
        return self.app.review_manager.review_is_closed()

    def review_is_closed_for(self, review):
        return self.app.review_manager.review_is_closed_for(review)

    def invalidate_reviews_for_hara(self, name):
        return self.app.review_manager.invalidate_reviews_for_hara(name)

    def invalidate_reviews_for_requirement(self, req_id):
        return self.app.review_manager.invalidate_reviews_for_requirement(req_id)

    def get_review_targets(self):
        return self.app.review_manager.get_review_targets()


__all__ = ["VersioningReviewService"]
