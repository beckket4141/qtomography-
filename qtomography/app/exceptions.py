"""统一的应用层异常类型。"""

from __future__ import annotations

from typing import Optional

__all__ = ["ReconstructionError", "ReconstructionCancelled"]


class ReconstructionError(RuntimeError):
    """批量重构过程中出现的一般性错误。"""


class ReconstructionCancelled(ReconstructionError):
    """用户主动取消批量重构任务时抛出的异常。"""

    def __init__(
        self,
        stage: str,
        *,
        sample_index: Optional[int] = None,
        total_samples: int = 0,
        completed_steps: int = 0,
        total_steps: int = 0,
        message: Optional[str] = None,
    ) -> None:
        if message is None:
            if sample_index is not None and total_samples:
                message = (
                    f"重构在阶段“{stage}”被取消（样本 {sample_index + 1}/{total_samples}）。"
                )
            else:
                message = f"重构在阶段“{stage}”被取消。"

        super().__init__(message)
        self.stage = stage
        self.sample_index = sample_index
        self.total_samples = total_samples
        self.completed_steps = completed_steps
        self.total_steps = total_steps

    @property
    def fraction(self) -> float:
        if self.total_steps <= 0:
            return 0.0
        return min(max(self.completed_steps / self.total_steps, 0.0), 1.0)

