"""Utilities for comparing reconstruction methods (e.g., Linear vs WLS)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence

import numpy as np
import pandas as pd

__all__ = [
    "MetricStats",
    "MetricComparison",
    "WLSOptimizationStats",
    "ComparisonResult",
    "compare_methods",
]


@dataclass
class MetricStats:
    mean: float
    std: float
    median: float
    minimum: Optional[float] = None
    q25: Optional[float] = None
    q75: Optional[float] = None
    maximum: Optional[float] = None


@dataclass
class MetricComparison:
    name: str
    linear: MetricStats
    wls: MetricStats
    difference: MetricStats


@dataclass
class WLSOptimizationStats:
    success_rate: float
    success_count: int
    total_count: int
    avg_iterations: float
    std_iterations: float
    avg_evaluations: Optional[float]
    std_evaluations: Optional[float]


@dataclass
class ComparisonResult:
    status: str  # ok, missing_methods, no_common_samples
    message: str
    metrics: List[MetricComparison]
    detailed: bool
    common_samples: List[str]
    total_samples: int
    available_methods: List[str]
    wls_stats: Optional[WLSOptimizationStats]


def compare_methods(
    df: pd.DataFrame,
    metrics: Sequence[str],
    *,
    detailed: bool = False,
) -> ComparisonResult:
    """Build a comparison summary for Linear vs WLS reconstructions."""

    available_methods = sorted({str(method) for method in df.get("method", [])})
    
    # 兼容性：将"mle"映射为"wls"
    if "mle" in available_methods and "wls" not in available_methods:
        df = df.copy()
        df.loc[df["method"] == "mle", "method"] = "wls"
        available_methods = sorted({str(method) for method in df.get("method", [])})
    
    if "linear" not in available_methods or "wls" not in available_methods:
        message = "\n[警告] 需要同时包含 Linear 和 WLS 样本才能进行对比"
        if available_methods:
            message += f"\n   当前方法: {available_methods}"
        return ComparisonResult(
            status="missing_methods",
            message=message,
            metrics=[],
            detailed=detailed,
            common_samples=[],
            total_samples=len(df),
            available_methods=available_methods,
            wls_stats=None,
        )

    linear_df = (
        df[df["method"] == "linear"].set_index("sample")
        if "linear" in df["method"].values
        else pd.DataFrame()
    )
    wls_df = (
        df[df["method"] == "wls"].set_index("sample")
        if "wls" in df["method"].values
        else pd.DataFrame()
    )

    common_samples = sorted(set(linear_df.index).intersection(wls_df.index))
    total_samples = len(set(linear_df.index).union(wls_df.index))
    if not common_samples:
        message = "\n[警告] 没有找到配对样本（Linear 与 WLS 没有共同 sample）"
        return ComparisonResult(
            status="no_common_samples",
            message=message,
            metrics=[],
            detailed=detailed,
            common_samples=[],
            total_samples=total_samples,
            available_methods=available_methods,
            wls_stats=None,
        )

    linear_df = linear_df.loc[common_samples]
    wls_df = wls_df.loc[common_samples]

    metric_results: list[MetricComparison] = []
    for metric in metrics:
        if metric not in df.columns:
            continue
        series_linear = linear_df[metric]
        series_wls = wls_df[metric]
        stats_linear = _build_stats(series_linear, detailed=detailed)
        stats_wls = _build_stats(series_wls, detailed=detailed)
        stats_diff = _difference_stats(stats_linear, stats_wls)
        metric_results.append(
            MetricComparison(
                name=metric,
                linear=stats_linear,
                wls=stats_wls,
                difference=stats_diff,
            )
        )

    wls_stats = _build_wls_stats(wls_df)

    return ComparisonResult(
        status="ok",
        message="",
        metrics=metric_results,
        detailed=detailed,
        common_samples=common_samples,
        total_samples=total_samples,
        available_methods=available_methods,
        wls_stats=wls_stats,
    )


def _build_stats(series: pd.Series, *, detailed: bool) -> MetricStats:
    mean = float(series.mean())
    std = float(series.std(ddof=0))
    median = float(series.median())

    if not detailed:
        return MetricStats(mean=mean, std=std, median=median)

    minimum = float(series.min())
    q25 = float(series.quantile(0.25))
    q75 = float(series.quantile(0.75))
    maximum = float(series.max())
    return MetricStats(
        mean=mean,
        std=std,
        median=median,
        minimum=minimum,
        q25=q25,
        q75=q75,
        maximum=maximum,
    )


def _difference_stats(linear: MetricStats, wls: MetricStats) -> MetricStats:
    def _diff(a: Optional[float], b: Optional[float]) -> Optional[float]:
        if a is None or b is None:
            return None
        return float(a - b)

    return MetricStats(
        mean=linear.mean - wls.mean,
        std=linear.std - wls.std,
        median=linear.median - wls.median,
        minimum=_diff(linear.minimum, wls.minimum),
        q25=_diff(linear.q25, wls.q25),
        q75=_diff(linear.q75, wls.q75),
        maximum=_diff(linear.maximum, wls.maximum),
    )


def _build_wls_stats(df: pd.DataFrame) -> Optional[WLSOptimizationStats]:
    if df.empty or "n_iterations" not in df.columns or "success" not in df.columns:
        return None

    success_count = int(df["success"].sum())
    total_count = len(df)
    success_rate = 100.0 * success_count / total_count if total_count else 0.0
    avg_iterations = float(df["n_iterations"].mean())
    std_iterations = float(df["n_iterations"].std(ddof=0))

    avg_evaluations = None
    std_evaluations = None
    if "n_evaluations" in df.columns:
        avg_evaluations = float(df["n_evaluations"].mean())
        std_evaluations = float(df["n_evaluations"].std(ddof=0))

    return WLSOptimizationStats(
        success_rate=success_rate,
        success_count=success_count,
        total_count=total_count,
        avg_iterations=avg_iterations,
        std_iterations=std_iterations,
        avg_evaluations=avg_evaluations,
        std_evaluations=std_evaluations,
    )

