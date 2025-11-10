"""最大似然 (MLE) 层析重构实现 - 已弃用，请使用 WLS。

此模块已弃用，实际实现的是加权最小二乘 (WLS) 算法，而非真正的最大似然估计。
请使用 qtomography.domain.reconstruction.wls 模块。
"""

import warnings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qtomography.domain.density import DensityMatrix
    from qtomography.domain.projectors import ProjectorSet
    from typing import Optional, Literal
    import numpy as np

# 发出弃用警告
warnings.warn(
    "qtomography.domain.reconstruction.mle 模块已弃用。"
    "该模块实际实现的是加权最小二乘 (WLS) 算法，而非真正的最大似然估计。"
    "请使用 qtomography.domain.reconstruction.wls 模块。"
    "此兼容层将在未来版本中移除。",
    DeprecationWarning,
    stacklevel=2
)

# 从 WLS 模块导入并重新导出
from .wls import WLSReconstructor as MLEReconstructor, WLSReconstructionResult as MLEReconstructionResult

__all__ = ["MLEReconstructor", "MLEReconstructionResult"]