import numpy as np
import pandas as pd
import json

from qtomography.app.controller import ReconstructionConfig, ReconstructionController


def _write_probabilities(tmp_path, data):
    frame = pd.DataFrame(data)
    csv = tmp_path / "probs.csv"
    frame.to_csv(csv, header=False, index=False)
    return csv


def test_run_batch_linear_only(tmp_path):
    data = np.array([[0.5], [0.5], [0.25], [0.25]], dtype=float)
    input_file = _write_probabilities(tmp_path, data)
    output_dir = tmp_path / "out"

    config = ReconstructionConfig(
        input_path=input_file,
        output_dir=output_dir,
        methods=("linear",),
        dimension=2,
    )

    controller = ReconstructionController()
    result = controller.run_batch(config)

    assert result.summary_path.exists()
    assert result.records_dir.exists()
    assert result.num_samples == 1

    summary = pd.read_csv(result.summary_path)
    assert "method" in summary.columns
    assert summary.loc[0, "method"] == "linear"


def test_run_batch_linear_and_wls(tmp_path):
    data = np.array([[0.6], [0.4], [0.3], [0.3]], dtype=float)
    input_file = _write_probabilities(tmp_path, data)
    output_dir = tmp_path / "out"

    config = ReconstructionConfig(
        input_path=input_file,
        output_dir=output_dir,
        methods=("linear", "wls"),
        dimension=2,
        wls_max_iterations=200,
    )

    controller = ReconstructionController()
    result = controller.run_batch(config)

    summary = pd.read_csv(result.summary_path)
    assert set(summary["method"]) == {"linear", "wls"}
    # objective should be finite for WLS row
    wls_row = summary[summary["method"] == "wls"].iloc[0]
    assert np.isfinite(wls_row["objective"])


def test_run_batch_with_bell_analysis(tmp_path):
    data = np.full((16, 1), 1/16, dtype=float)
    input_file = _write_probabilities(tmp_path, data)
    output_dir = tmp_path / "bell"

    config = ReconstructionConfig(
        input_path=input_file,
        output_dir=output_dir,
        methods=("linear",),
        dimension=4,
        analyze_bell=True,
    )

    controller = ReconstructionController()
    result = controller.run_batch(config)

    summary = pd.read_csv(result.summary_path)
    assert "bell_max_fidelity" in summary.columns
    assert (summary["bell_max_fidelity"] <= 1.0).all()

    repo_files = list(result.records_dir.glob("*.json"))
    assert repo_files


def test_run_batch_metrics_fields(tmp_path):
    data = np.array([[0.5], [0.3], [0.1], [0.1]], dtype=float)
    input_file = _write_probabilities(tmp_path, data)
    output_dir = tmp_path / "metrics"

    config = ReconstructionConfig(
        input_path=input_file,
        output_dir=output_dir,
        methods=("linear", "wls"),
        dimension=2,
        wls_max_iterations=200,
    )

    controller = ReconstructionController()
    result = controller.run_batch(config)

    summary = pd.read_csv(result.summary_path)

    assert {"condition_number", "eigenvalue_entropy"}.issubset(summary.columns)

    linear_row = summary[summary["method"] == "linear"].iloc[0]
    assert np.isfinite(linear_row["condition_number"])
    assert np.isfinite(linear_row["eigenvalue_entropy"])
    assert linear_row["condition_number"] > 0

    wls_row = summary[summary["method"] == "wls"].iloc[0]
    assert np.isfinite(wls_row["eigenvalue_entropy"])
    assert pd.isna(wls_row["condition_number"])

    records = list(result.records_dir.glob("*.json"))
    assert records
    linear_record = None
    for record_path in records:
        with record_path.open(encoding="utf-8") as f:
            payload = json.load(f)
        if payload.get("method") == "linear":
            linear_record = payload
            break
    assert linear_record is not None

    metrics = linear_record["metrics"]
    assert "condition_number" in metrics
    assert "eigenvalue_entropy" in metrics
    # 使用近似相等比较浮点数，避免精度问题
    assert np.isclose(metrics["condition_number"], linear_row["condition_number"])
    assert np.isclose(metrics["eigenvalue_entropy"], linear_row["eigenvalue_entropy"])
