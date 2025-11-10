"""
优化版ProjectorSet - 使用高性能LRU缓存

关键优化：
1. 基于OrderedDict实现LRU缓存，利用C语言优化
2. 自动处理LRU逻辑，代码简洁
3. 线程安全，支持高并发访问
4. 专门为投影算符等大对象缓存设计
"""

from __future__ import annotations

import math
from typing import ClassVar, Tuple, Optional
import threading

import numpy as np

from ..infrastructure.cache.optimized_lru import ProjectorLRUCache


class OptimizedProjectorSet:
    """优化版投影算符生成器，使用高性能LRU缓存。

    参数:
        dimension: 希尔伯特空间的维度 n。
        cache: 是否启用类级缓存。默认 True, 用于避免重复生成。
        max_cache_bytes: 缓存最大字节数，默认 1GB。
    """

    # 类级缓存，使用优化的LRU实现
    _CACHE: ClassVar[Optional[ProjectorLRUCache]] = None
    _CACHE_LOCK = threading.RLock()

    def __init__(
        self, 
        dimension: int, 
        *, 
        cache: bool = True,
        max_cache_bytes: int = 1024 * 1024 * 1024  # 1GB
    ) -> None:
        if dimension < 2:
            raise ValueError("维度必须大于等于 2 才能构建投影算符")
        self.dimension = dimension

        if cache:
            # 初始化类级缓存（单例模式）
            with self._CACHE_LOCK:
                if self._CACHE is None:
                    self._CACHE = ProjectorLRUCache(max_bytes=max_cache_bytes)
            
            # 尝试从缓存获取
            cached_data = self._CACHE.get(dimension)
            if cached_data is not None:
                # 缓存命中，直接使用
                bases, projectors, measurement = cached_data
            else:
                # 缓存未命中，计算并存储
                bases = self._build_bases(dimension)
                projectors = self._build_projectors(bases)
                measurement = self._build_measurement_matrix(projectors)
                
                # 存储到缓存
                self._CACHE.put(dimension, (bases, projectors, measurement))
        else:
            # 不使用缓存，直接计算
            bases = self._build_bases(dimension)
            projectors = self._build_projectors(bases)
            measurement = self._build_measurement_matrix(projectors)

        # 使用副本存放到实例，防止使用者修改返回值而污染缓存
        self._bases = bases.copy()
        self._projectors = projectors.copy()
        self._measurement_matrix = measurement.copy()

    # ------------------------------------------------------------------
    @property
    def bases(self) -> np.ndarray:
        """返回所有测量基向量 (n2, n)。"""
        return self._bases.copy()

    @property
    def projectors(self) -> np.ndarray:
        """返回对应的投影算符矩阵 (n2, n, n)。"""
        return self._projectors.copy()

    @property
    def measurement_matrix(self) -> np.ndarray:
        """返回线性重构所需的测量矩阵 M (n2, n2)。"""
        return self._measurement_matrix.copy()

    # ------------------------------------------------------------------
    @classmethod
    def get(cls, dimension: int) -> "OptimizedProjectorSet":
        """从缓存获取指定维度的投影集, 若不存在则创建。"""
        return cls(dimension, cache=True)

    @classmethod
    def clear_cache(cls) -> None:
        """清空所有缓存记录 (主要用于测试或调试情况)。"""
        with cls._CACHE_LOCK:
            if cls._CACHE is not None:
                cls._CACHE.clear()

    @classmethod
    def get_cache_stats(cls) -> dict:
        """获取缓存统计信息。"""
        with cls._CACHE_LOCK:
            if cls._CACHE is not None:
                return cls._CACHE.get_stats()
            return {}

    @classmethod
    def set_cache_limit(cls, max_bytes: int) -> None:
        """设置缓存大小限制。"""
        with cls._CACHE_LOCK:
            if cls._CACHE is not None:
                cls._CACHE.max_bytes = max_bytes

    # ------------------------------------------------------------------
    @staticmethod
    def _build_bases(dimension: int) -> np.ndarray:
        """生成完整的测量基向量集合。"""
        bases = []
        # 1. 标准基 |0>, |1>, ..., |n-1>
        for i in range(dimension):
            vec = np.zeros(dimension, dtype=complex)
            vec[i] = 1.0
            bases.append(vec)

        # 2. 组合基 (|i> + |j>) / sqrt(2)
        #    以及 (|i> - i|j>) / sqrt(2)
        sqrt2_inv = 1.0 / math.sqrt(2.0)
        for i in range(dimension):
            for j in range(i + 1, dimension):
                # 构造 (|i> + |j>) / \sqrt{2}, 与 MATLAB 版本保持一致
                plus = np.zeros(dimension, dtype=complex)
                plus[i] = 1.0
                plus[j] = 1.0
                bases.append(plus * sqrt2_inv)

                # 构造 (|i> - i|j>) / \sqrt{2}, 用于捕捉相位差异
                minus_i = np.zeros(dimension, dtype=complex)
                minus_i[i] = 1.0
                minus_i[j] = -1j
                bases.append(minus_i * sqrt2_inv)

        return np.stack(bases, axis=0)

    @staticmethod
    def _build_projectors(bases: np.ndarray) -> np.ndarray:
        """依据测量基构造投影算符。"""
        n_bases, dimension = bases.shape
        projectors = np.zeros((n_bases, dimension, dimension), dtype=complex)
        
        for i, base in enumerate(bases):
            # 投影算符 P = |ψ><ψ|
            projectors[i] = np.outer(base, base.conj())
        
        return projectors

    @staticmethod
    def _build_measurement_matrix(projectors: np.ndarray) -> np.ndarray:
        """构建线性重构所需的测量矩阵 M。"""
        n_bases, dimension, _ = projectors.shape
        
        # 将每个投影算符展平为向量
        # P_i 是 d×d 矩阵，展平为 d² 维向量
        measurement_matrix = np.zeros((n_bases, dimension * dimension), dtype=complex)
        
        for i, projector in enumerate(projectors):
            # 将投影算符展平为向量（按行展平）
            measurement_matrix[i] = projector.flatten()
        
        return measurement_matrix


# 性能测试函数
def benchmark_projector_performance():
    """测试优化版ProjectorSet的性能"""
    import time
    
    print("=== 优化版ProjectorSet性能测试 ===\n")
    
    # 测试不同维度的性能
    dimensions = [4, 8, 16, 32]
    num_iterations = 100
    
    for dim in dimensions:
        print(f"测试维度 {dim}:")
        
        # 测试缓存命中性能
        start_time = time.time()
        for _ in range(num_iterations):
            projector_set = OptimizedProjectorSet.get(dim)
            # 访问属性触发计算
            _ = projector_set.bases
            _ = projector_set.projectors
            _ = projector_set.measurement_matrix
        cache_time = time.time() - start_time
        
        print(f"  缓存命中耗时: {cache_time:.4f}秒 ({cache_time/num_iterations*1000:.2f}ms/次)")
        
        # 测试缓存未命中性能（第一次创建）
        OptimizedProjectorSet.clear_cache()
        start_time = time.time()
        projector_set = OptimizedProjectorSet(dim, cache=True)
        _ = projector_set.bases
        _ = projector_set.projectors
        _ = projector_set.measurement_matrix
        no_cache_time = time.time() - start_time
        
        print(f"  首次创建耗时: {no_cache_time:.4f}秒")
        print(f"  缓存加速比: {no_cache_time / (cache_time/num_iterations):.2f}倍")
        
        # 显示缓存统计
        stats = OptimizedProjectorSet.get_cache_stats()
        print(f"  缓存统计: {stats}")
        print()


if __name__ == "__main__":
    # 运行性能测试
    benchmark_projector_performance()
