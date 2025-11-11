from __future__ import annotations

"""测量设计支持的投影算符提供者，支持多种策略。

向后兼容的 `ProjectorSet` 包装器，支持可扩展的测量设计。
当前支持：
- MUB (mutually unbiased bases)：相互无偏基
- SIC-POVM：对称信息完备的 POVM
- nopovm：非 POVM 测量设计（标准基+组合基）
"""

from typing import ClassVar, Tuple

import numpy as np

from qtomography.domain.measurement.mub import build_mub_projectors
from qtomography.domain.measurement.sic import build_sic_projectors
from qtomography.domain.measurement.nopovm import build_nopovm_projectors


class ProjectorSet:
    """为维度 `n` 提供投影算符，使用指定的测量设计。

    参数:
        dimension: 希尔伯特空间维度 n
        design: 测量设计名称，可选值：
            - "mub": 相互无偏基 多组PVM（Mutually Unbiased Bases）
            - "sic": 对称信息完备 单组POVM（Symmetric Informationally Complete POVM）
            - "nopovm": 非 POVM 测量设计（标准基+组合基）
        cache: 是否启用缓存
    """

    # 缓存键: (dimension, design) -> (bases, projectors, measurement_matrix, groups)
    _CACHE: ClassVar[dict[tuple[int, str], Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]]] = {}

    def __init__(self, dimension: int, *, design: str = "mub", cache: bool = True) -> None:
        if dimension < 2:
            raise ValueError("维度必须 >= 2")
        self.dimension = dimension
        self.design = design.lower()

        key = (dimension, self.design)
        if cache and key in self._CACHE:
            bases, projectors, measurement, groups = self._CACHE[key]
        else:
            if self.design == "mub":
                # 使用full模式（d(d+1) 个投影）作为新的默认设置
                mub = build_mub_projectors(dimension, variant="full")
                # bases：为向后兼容，仅在 d=2 时提供 4 个代表性向量
         #       if dimension == 2:
        #            bases = np.array([
       #                 [1+0j, 0+0j],
      #                  [0+0j, 1+0j],
     #                   [1/np.sqrt(2)+0j, 1/np.sqrt(2)+0j],
    #                    [1/np.sqrt(2)+0j, -1j/np.sqrt(2)],
    #                ], dtype=complex)
   #             else:
                bases = np.zeros((dimension, dimension), dtype=complex)
                projectors = mub.projectors
                groups = mub.groups
                measurement = mub.measurement_matrix
            elif self.design == "sic":
                sic = build_sic_projectors(dimension)
                bases = np.zeros((dimension, dimension), dtype=complex)
                projectors = sic.projectors
                groups = sic.groups
                measurement = sic.measurement_matrix
            elif self.design == "nopovm":
                nopovm = build_nopovm_projectors(dimension)
                bases = np.zeros((dimension, dimension), dtype=complex)
                projectors = nopovm.projectors
                groups = nopovm.groups
                measurement = nopovm.measurement_matrix
            else:
                raise ValueError(f"未知的测量设计: {self.design}")
            if cache:
                self._CACHE[key] = (bases, projectors, measurement, groups)

        # 防御性副本，确保缓存安全
        self._bases = bases.copy()
        self._projectors = projectors.copy()
        self._measurement_matrix = measurement.copy()
        self._groups = groups.copy()

    # ------------------------------------------------------------------
    @property
    def bases(self) -> np.ndarray:
        """返回基向量（如果可用），用于向后兼容。"""
        return self._bases.copy()

    @property
    def projectors(self) -> np.ndarray:
        """(m, n, n) 秩为 1 的投影算符数组。"""
        return self._projectors.copy()

    @property
    def measurement_matrix(self) -> np.ndarray:
        """(m, n*n) 测量矩阵，每行是展平的投影算符。"""
        return self._measurement_matrix.copy()

    @property
    def groups(self) -> np.ndarray:
        """每个投影算符的分组标识 (m,)，用于按组归一化。"""
        return self._groups.copy()

    # ------------------------------------------------------------------
    @classmethod
    def get(cls, dimension: int, *, design: str = "mub") -> "ProjectorSet":
        """从缓存获取或构建指定设计的投影算符集合。"""

        return cls(dimension, design=design, cache=True)

    @classmethod
    def clear_cache(cls) -> None:
        """清空内存缓存（用于测试/工具函数）。"""

        cls._CACHE.clear()
