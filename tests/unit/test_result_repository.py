"""ResultRepository 单元测试。"""

import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from qtomography.infrastructure.persistence.result_repository import (
    ReconstructionRecord,
    ResultRepository,
)


@pytest.fixture
def sample_record():
    return ReconstructionRecord(
        method="linear",
        dimension=2,
        probabilities=np.array([0.5, 0.5, 0.25, 0.25], dtype=float),
        density_matrix=np.array([[0.5, 0.1 + 0.2j], [0.1 - 0.2j, 0.5]]),
        metrics={"fidelity": 0.99},
        metadata={"experiment": "demo"},
        timestamp="2025-10-07T12:00:00",
    )


def test_save_and_load_json(tmp_path: Path, sample_record: ReconstructionRecord):
    repo = ResultRepository(tmp_path, fmt="json")
    path = repo.save(sample_record)
    assert path.exists()

    loaded = repo.load_all()
    assert len(loaded) == 1
    rec = loaded[0]
    np.testing.assert_allclose(rec.density_matrix, sample_record.density_matrix)
    assert rec.method == sample_record.method
    assert rec.metrics["fidelity"] == pytest.approx(0.99)


def test_save_and_load_csv(tmp_path: Path, sample_record: ReconstructionRecord):
    repo = ResultRepository(tmp_path, fmt="csv")
    repo.save(sample_record)

    loaded = repo.load_all()
    assert len(loaded) == 1
    rec = loaded[0]
    assert rec.metadata["experiment"] == "demo"

def test_save_json_sanitizes_timestamp(tmp_path: Path, sample_record: ReconstructionRecord):
    repo = ResultRepository(tmp_path, fmt="json")
    dirty_record = replace(sample_record, timestamp="2025/10/07 12:00:00")
    path = repo.save(dirty_record)
    assert path.exists()
    assert '/' not in path.name
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["timestamp"] == "2025/10/07 12:00:00"


def test_to_dataframe_requires_pandas(tmp_path: Path, sample_record: ReconstructionRecord):
    repo = ResultRepository(tmp_path, fmt="json")
    repo.save(sample_record)

    try:
        import pandas  # noqa: F401
    except ImportError:
        with pytest.raises(RuntimeError):
            repo.to_dataframe()
    else:
        df = repo.to_dataframe()
        assert "method" in df.columns
