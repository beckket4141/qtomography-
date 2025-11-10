"""（兼容层）重构结果持久化模块。

该模块已迁移至 :mod:`qtomography.infrastructure.persistence.result_repository`。
保留此文件仅为兼容旧的导入路径，新代码请改用新的命名空间。
"""

from __future__ import annotations

from qtomography.infrastructure.persistence.result_repository import (
    ReconstructionRecord,
    ResultRepository,
)

__all__ = ["ReconstructionRecord", "ResultRepository"]
