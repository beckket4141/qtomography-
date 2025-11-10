"""（兼容层）重构结果持久化工具。

真实实现已迁移至 :mod:`qtomography.infrastructure.persistence`。
"""

from qtomography.infrastructure.persistence import ReconstructionRecord, ResultRepository

__all__ = ["ReconstructionRecord", "ResultRepository"]
