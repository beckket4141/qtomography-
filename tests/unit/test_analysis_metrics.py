"""Tests for Stage 4 analysis metric helpers."""

from __future__ import annotations

import numpy as np
import pytest

from qtomography.analysis.metrics import condition_number, eigenvalue_entropy


def test_eigenvalue_entropy_normalises_and_uses_natural_log():
    eigenvalues = np.array([0.2, 0.3, 0.5], dtype=float)
    entropy = eigenvalue_entropy(eigenvalues)

    expected = -np.sum((eigenvalues / np.sum(eigenvalues)) * np.log(eigenvalues / np.sum(eigenvalues)))
    assert pytest.approx(expected, rel=1e-12) == entropy


def test_eigenvalue_entropy_supports_base_2():
    eigenvalues = np.array([0.5, 0.5], dtype=float)
    entropy = eigenvalue_entropy(eigenvalues, base="2")
    assert pytest.approx(1.0, abs=1e-12) == entropy


def test_condition_number_returns_large_when_all_values_below_tolerance():
    singular_values = np.array([0.0, 0.0])
    cond = condition_number(singular_values)
    assert cond == pytest.approx(1e16)


def test_condition_number_ignores_small_values_using_default_tolerance():
    singular_values = np.array([10.0, 1e-3, 1e-12])
    cond = condition_number(singular_values)
    assert cond == pytest.approx(10.0 / 1e-3)


def test_condition_number_returns_ratio_with_explicit_tolerance():
    singular_values = np.array([10.0, 2.0, 1.0])
    cond = condition_number(singular_values, tolerance=1e-6)
    assert cond == pytest.approx(10.0)
