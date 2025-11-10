"""Tests for analysis comparison utilities."""

from __future__ import annotations

import pandas as pd
import pytest

from qtomography.analysis import compare_methods


def test_compare_methods_requires_linear_and_wls():
    df = pd.DataFrame(
        {
            "sample": ["s1", "s2"],
            "method": ["linear", "linear"],
            "purity": [0.8, 0.9],
        }
    )

    result = compare_methods(df, ["purity"])
    assert result.status == "missing_methods"
    assert "当前方法" in result.message or "Linear" in result.message


def test_compare_methods_requires_common_samples():
    df = pd.DataFrame(
        {
            "sample": ["s1", "s2"],
            "method": ["linear", "wls"],
            "purity": [0.8, 0.7],
        }
    )

    result = compare_methods(df, ["purity"])
    assert result.status == "no_common_samples"


def test_compare_methods_returns_metric_summaries_with_wls_stats():
    rows = [
        {"sample": "s1", "method": "linear", "purity": 0.8, "trace": 1.0},
        {"sample": "s2", "method": "linear", "purity": 0.9, "trace": 0.95},
        {
            "sample": "s1",
            "method": "wls",
            "purity": 0.75,
            "trace": 0.98,
            "n_iterations": 50,
            "n_evaluations": 120,
            "success": True,
        },
        {
            "sample": "s2",
            "method": "wls",
            "purity": 0.85,
            "trace": 0.96,
            "n_iterations": 60,
            "n_evaluations": 140,
            "success": False,
        },
    ]
    df = pd.DataFrame(rows)

    result = compare_methods(df, ["purity", "trace"], detailed=True)

    assert result.status == "ok"
    assert result.common_samples == ["s1", "s2"]
    assert result.total_samples == 2
    assert len(result.metrics) == 2

    purity_comparison = result.metrics[0]
    assert pytest.approx(0.85) == purity_comparison.linear.mean
    assert pytest.approx(0.8) == purity_comparison.wls.mean
    assert pytest.approx(0.05) == purity_comparison.difference.mean
    assert purity_comparison.linear.minimum is not None  # detailed stats populated

    assert result.wls_stats is not None
    wls_stats = result.wls_stats
    assert pytest.approx(55.0) == wls_stats.avg_iterations
    assert pytest.approx(130.0) == wls_stats.avg_evaluations
