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

"""Confusion matrix utilities."""

from typing import Dict


def compute_metrics(tp: float, fp: float, tn: float, fn: float) -> Dict[str, float]:
    """Compute common classification metrics from confusion matrix counts.

    Parameters
    ----------
    tp, fp, tn, fn:
        True positives, false positives, true negatives and false negatives.

    Returns
    -------
    dict
        Dictionary with keys ``accuracy``, ``precision``, ``recall`` and ``f1``.
        A nested ``units`` mapping records the dimension of each metric.
    """
    tp = float(tp)
    fp = float(fp)
    tn = float(tn)
    fn = float(fn)
    total = tp + fp + tn + fn
    accuracy = (tp + tn) / total if total else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "units": {
            "accuracy": "ratio",
            "precision": "ratio",
            "recall": "ratio",
            "f1": "ratio",
        },
    }


def compute_rates(
    tp: float | None = None,
    fp: float | None = None,
    tn: float | None = None,
    fn: float | None = None,
    hours: float = 0.0,
    validation_target: float | None = None,
    p: float | None = None,
    n: float | None = None,
) -> Dict[str, float]:
    """Derive confusion matrix counts from dataset size and limits.

    The helper operates on explicit confusion matrix counts (``tp``, ``fp``,
    ``tn``, ``fn``) or, when these are not provided, derives them from
    dataset sizes ``p`` and ``n`` together with an allowed hazardous event
    rate ``validation_target`` (events/hour) over a mission duration
    ``hours``.

    Parameters
    ----------
    tp, fp, tn, fn:
        Confusion matrix counts. If any are ``None`` then ``p`` and ``n``
        must be supplied and counts are derived assuming the per-hour limit
        ``validation_target`` applies equally to false positives and false
        negatives.
    hours:
        Total test duration in hours (mission profile ``TAU ON``).
    validation_target:
        Optional allowed hazardous events per hour for the selected
        validation target.
    p, n:
        Dataset sizes for actual positives and negatives. Required when
        explicit confusion matrix counts are not supplied.

    Returns
    -------
    dict
        Dictionary containing the confusion matrix counts (``tp``, ``fp``,
        ``tn``, ``fn``) and totals ``p`` and ``n``.
        A nested ``units`` mapping documents the measurement unit for
        each value.
    """

    hours = float(hours)
    if tp is None or fp is None or tn is None or fn is None:
        if p is None or n is None:
            raise ValueError(
                "Either confusion matrix counts or dataset sizes P and N must be provided"
            )
        p = float(p)
        n = float(n)
        rate = float(validation_target or 0.0)
        fp = rate * hours
        fn = rate * hours
        tp = max(p - fn, 0.0)
        tn = max(n - fp, 0.0)
    else:
        tp = float(tp)
        fp = float(fp)
        tn = float(tn)
        fn = float(fn)
        p = tp + fn
        n = tn + fp

    return {
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "p": p,
        "n": n,
        "units": {
            "tp": "count",
            "fp": "count",
            "tn": "count",
            "fn": "count",
            "p": "count",
            "n": "count",
            "hours": "h",
            "validation_target": "events/h",
        },
    }


def compute_metrics_from_target(
    *, hours: float, validation_target: float | None, p: float, n: float
) -> Dict[str, float]:
    """Compute metrics and confusion matrix counts from a validation target.

    This helper mirrors the workflow of the *ODD elements* confusion matrix
    window where accuracy, precision, recall and F1 score are first derived
    from a product goal's validation target and mission profile duration
    (``TAU ON``).  The resulting metrics are then used to recover the
    confusion matrix counts ``tp``, ``fp``, ``tn`` and ``fn``.

    Parameters
    ----------
    hours:
        Total test duration in hours (mission profile ``TAU ON``).
    validation_target:
        Allowed hazardous events per hour for the selected validation target.
    p, n:
        Dataset sizes for actual positives and negatives.

    Returns
    -------
    dict
        Dictionary containing classification metrics (``accuracy``,
        ``precision``, ``recall`` and ``f1``) together with the confusion
        matrix counts and totals (``tp``, ``fp``, ``tn``, ``fn``, ``p``,
        ``n``). A nested ``units`` mapping annotates every entry with its
        corresponding unit.
    """

    hours = float(hours)
    p = float(p)
    n = float(n)
    rate = float(validation_target or 0.0)
    errors = rate * hours

    total = p + n
    accuracy = (total - 2 * errors) / total if total else 0.0
    precision = (p - errors) / p if p else 0.0
    recall = (p - errors) / p if p else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    tp = recall * p
    fn = p - tp
    fp = tp * (1 / precision - 1) if precision else 0.0
    tn = n - fp

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "p": p,
        "n": n,
        "units": {
            "accuracy": "ratio",
            "precision": "ratio",
            "recall": "ratio",
            "f1": "ratio",
            "tp": "count",
            "fp": "count",
            "tn": "count",
            "fn": "count",
            "p": "count",
            "n": "count",
            "hours": "h",
            "validation_target": "events/h",
        },
    }
