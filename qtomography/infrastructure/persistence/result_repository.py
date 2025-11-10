"""重构结果的持久化与加载工具。

本模块定义两类对象：

- :class:`ReconstructionRecord`：封装一次重构的密度矩阵、指标与元数据；
- :class:`ResultRepository`：提供 JSON / CSV 的保存与读取能力。

设计目标：
1. 统一 JSON / CSV 的读写格式，便于跨平台共享结果；
2. 保持与 numpy 数组兼容的序列化形式；
3. 为应用层和 CLI 提供稳定的持久化接口。
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import numpy as np

__all__ = ["ReconstructionRecord", "ResultRepository"]


@dataclass
class ReconstructionRecord:
    """单次重构结果的数据结构。"""

    method: str
    dimension: int
    probabilities: np.ndarray
    density_matrix: np.ndarray
    metrics: Dict[str, float]
    metadata: Optional[Dict[str, str]] = None
    timestamp: Optional[str] = field(default=None)

    def to_serializable(self) -> Dict[str, Any]:
        """转换为可写入 JSON/CSV 的字典。"""

        ts = self.timestamp or datetime.now(timezone.utc).isoformat()
        return {
            "method": self.method,
            "dimension": self.dimension,
            "probabilities": self.probabilities.tolist(),
            "density_matrix": {
                "real": self.density_matrix.real.tolist(),
                "imag": self.density_matrix.imag.tolist(),
            },
            "metrics": {k: float(v) for k, v in self.metrics.items()},
            "metadata": self.metadata or {},
            "timestamp": ts,
        }

    @classmethod
    def from_serializable(cls, payload: Dict[str, Any]) -> "ReconstructionRecord":
        """从 JSON/CSV 载荷构建 :class:`ReconstructionRecord`。"""

        matrix = np.array(payload["density_matrix"]["real"], dtype=float)
        matrix = matrix + 1j * np.array(payload["density_matrix"]["imag"], dtype=float)
        return cls(
            method=payload["method"],
            dimension=int(payload["dimension"]),
            probabilities=np.array(payload["probabilities"], dtype=float),
            density_matrix=matrix,
            metrics={k: float(v) for k, v in payload.get("metrics", {}).items()},
            metadata=payload.get("metadata", {}),
            timestamp=payload.get("timestamp"),
        )


class ResultRepository:
    """重构结果的持久化仓库。"""

    def __init__(self, root: Path | str, *, fmt: str = "json", prefix: str = "record") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.fmt = fmt.lower()
        if self.fmt not in {"json", "csv"}:
            raise ValueError("fmt 参数只能是 'json' 或 'csv'")
        self.prefix = prefix

    # ------------------------------------------------------------------
    def save(self, record: ReconstructionRecord) -> Path:
        """保存单条记录并返回文件路径。"""

        payload = record.to_serializable()
        if self.fmt == "json":
            return self._save_json(payload)
        return self._save_csv(payload)

    def load_all(self) -> List[ReconstructionRecord]:
        """读取仓库中全部记录。"""

        if self.fmt == "json":
            return self._load_all_json()
        return self._load_all_csv()

    def to_dataframe(self):
        """将所有记录转换为 pandas.DataFrame。"""

        try:
            import pandas as pd
        except ImportError as exc:
            raise RuntimeError("转换为 DataFrame 需要安装 pandas") from exc

        records = [rec.to_serializable() for rec in self.load_all()]
        return pd.DataFrame(records)

    @staticmethod
    def _sanitize_token(token: str) -> str:
        """将任意字符串转换为适合作为文件名的安全形式。"""

        sanitized = re.sub(r"[^0-9A-Za-z_-]", "-", str(token))
        sanitized = re.sub(r"-{2,}", "-", sanitized).strip("-")
        return sanitized or "record"

    # ------------------------------------------------------------------
    def _save_json(self, payload: Dict[str, Any]) -> Path:
        timestamp_raw = payload["timestamp"]
        safe_timestamp = self._sanitize_token(timestamp_raw)
        filename = f"{self.prefix}_{payload['dimension']}_{safe_timestamp}.json"
        path = self.root / filename
        with path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        return path

    def _load_all_json(self) -> List[ReconstructionRecord]:
        records: List[ReconstructionRecord] = []
        for json_path in sorted(self.root.glob(f"{self.prefix}_*.json")):
            try:
                payload = json.loads(json_path.read_text(encoding="utf-8"))
                records.append(ReconstructionRecord.from_serializable(payload))
            except Exception:
                continue
        return records

    # ------------------------------------------------------------------
    def _save_csv(self, payload: Dict[str, Any]) -> Path:
        path = self.root / f"{self.prefix}.csv"
        is_new = not path.exists()
        with path.open("a", newline="", encoding="utf-8") as fh:
            fieldnames = [
                "timestamp",
                "method",
                "dimension",
                "probabilities",
                "density_matrix",
                "metrics",
                "metadata",
            ]
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            if is_new:
                writer.writeheader()
            row = {
                "timestamp": payload["timestamp"],
                "method": payload["method"],
                "dimension": payload["dimension"],
                "probabilities": json.dumps(payload["probabilities"], ensure_ascii=False),
                "density_matrix": json.dumps(payload["density_matrix"], ensure_ascii=False),
                "metrics": json.dumps(payload["metrics"], ensure_ascii=False),
                "metadata": json.dumps(payload.get("metadata", {}), ensure_ascii=False),
            }
            writer.writerow(row)
        return path

    def _load_all_csv(self) -> List[ReconstructionRecord]:
        path = self.root / f"{self.prefix}.csv"
        if not path.exists():
            return []
        records: List[ReconstructionRecord] = []
        with path.open("r", newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                try:
                    payload = {
                        "timestamp": row["timestamp"],
                        "method": row["method"],
                        "dimension": int(row["dimension"]),
                        "probabilities": json.loads(row["probabilities"]),
                        "density_matrix": json.loads(row["density_matrix"]),
                        "metrics": json.loads(row["metrics"]),
                        "metadata": json.loads(row.get("metadata") or "{}"),
                    }
                    records.append(ReconstructionRecord.from_serializable(payload))
                except Exception:
                    continue
        return records
