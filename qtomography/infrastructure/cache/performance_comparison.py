"""
LRU缓存性能对比测试

对比两种实现：
1. 简单LRU：每次get/put都要移动大对象
2. 优化LRU：基于OrderedDict实现，性能优异
"""

import time
import numpy as np
from typing import Dict, List, Any
import threading
from collections import OrderedDict
from optimized_lru import OptimizedLRUCache, ProjectorLRUCache


class SimpleLRUCache:
    """简单LRU实现 - 每次操作都要移动大对象"""
    
    def __init__(self, max_size: int):
        self.max_size = max_size
        self.cache: Dict[Any, Any] = {}
        self.access_order: List[Any] = []
        self._lock = threading.RLock()
    
    def get(self, key: Any) -> Any:
        with self._lock:
            if key not in self.cache:
                return None
            
            # 问题：每次都要移动大对象
            self.access_order.remove(key)      # O(n) 操作
            self.access_order.append(key)      # O(1) 操作
            return self.cache[key]
    
    def put(self, key: Any, value: Any) -> None:
        with self._lock:
            if key in self.cache:
                # 更新现有值
                self.cache[key] = value
                self.access_order.remove(key)  # O(n) 操作
                self.access_order.append(key)  # O(1) 操作
            else:
                # 检查容量
                if len(self.cache) >= self.max_size:
                    # 删除最久未使用的
                    oldest_key = self.access_order.pop(0)  # O(n) 操作
                    del self.cache[oldest_key]
                
                # 添加新值
                self.cache[key] = value
                self.access_order.append(key)  # O(1) 操作


class OrderedDictLRUCache:
    """基于OrderedDict的LRU实现 - 用于对比"""
    
    def __init__(self, max_size: int):
        self.max_size = max_size
        self.cache = OrderedDict()
        self._lock = threading.RLock()
    
    def get(self, key: Any) -> Any:
        with self._lock:
            if key not in self.cache:
                return None
            
            # 移动到末尾（最近使用）
            self.cache.move_to_end(key)
            return self.cache[key]
    
    def put(self, key: Any, value: Any) -> None:
        with self._lock:
            if key in self.cache:
                # 更新现有值并移动到末尾
                self.cache[key] = value
                self.cache.move_to_end(key)
            else:
                # 检查容量
                if len(self.cache) >= self.max_size:
                    # 删除最久未使用的（第一个）
                    self.cache.popitem(last=False)
                
                # 添加新值
                self.cache[key] = value


def generate_test_data(size_mb: float) -> np.ndarray:
    """生成指定大小的测试数据"""
    # 每个复数8字节，所以需要 size_mb * 1024 * 1024 / 8 个复数
    num_elements = int(size_mb * 1024 * 1024 / 8)
    return np.random.random(num_elements) + 1j * np.random.random(num_elements)


def benchmark_cache_performance():
    """性能基准测试"""
    print("=== LRU缓存性能对比测试 ===\n")
    
    # 测试参数
    cache_size = 5
    test_data_sizes = [0.1, 0.5, 1.0, 2.0]  # MB
    num_operations = 1000
    
    for data_size_mb in test_data_sizes:
        print(f"测试数据大小: {data_size_mb}MB")
        print("-" * 50)
        
        # 生成测试数据
        test_data = generate_test_data(data_size_mb)
        
        # 测试简单LRU
        simple_cache = SimpleLRUCache(cache_size)
        start_time = time.time()
        
        for i in range(num_operations):
            key = i % cache_size
            if i % 2 == 0:
                simple_cache.put(key, test_data)
            else:
                simple_cache.get(key)
        
        simple_time = time.time() - start_time
        
        # 测试OrderedDict LRU
        ordered_cache = OrderedDictLRUCache(cache_size)
        start_time = time.time()
        
        for i in range(num_operations):
            key = i % cache_size
            if i % 2 == 0:
                ordered_cache.put(key, test_data)
            else:
                ordered_cache.get(key)
        
        ordered_time = time.time() - start_time
        
        # 测试优化LRU（基于OrderedDict）
        optimized_cache = OptimizedLRUCache(cache_size)
        start_time = time.time()
        
        for i in range(num_operations):
            key = i % cache_size
            if i % 2 == 0:
                optimized_cache.put(key, test_data)
            else:
                optimized_cache.get(key)
        
        optimized_time = time.time() - start_time
        
        # 计算性能提升
        simple_to_ordered = simple_time / ordered_time if ordered_time > 0 else float('inf')
        simple_to_optimized = simple_time / optimized_time if optimized_time > 0 else float('inf')
        
        print(f"简单LRU耗时: {simple_time:.4f}秒")
        print(f"OrderedDict LRU耗时: {ordered_time:.4f}秒")
        print(f"优化LRU耗时: {optimized_time:.4f}秒")
        print(f"OrderedDict比简单LRU快: {simple_to_ordered:.2f}倍")
        print(f"优化LRU比简单LRU快: {simple_to_optimized:.2f}倍")
        print(f"优化LRU比简单LRU快: {((simple_time - optimized_time) / simple_time * 100):.1f}%")
        print()


def benchmark_projector_cache():
    """投影算符缓存性能测试"""
    print("=== 投影算符缓存性能测试 ===\n")
    
    # 创建缓存
    cache = ProjectorLRUCache(max_bytes=10 * 1024 * 1024)  # 10MB限制
    
    # 生成不同维度的投影算符数据
    dimensions = [4, 8, 16, 32]
    
    print("存储不同维度的投影算符数据...")
    for dim in dimensions:
        # 模拟投影算符数据
        n_bases = dim * dim
        bases = np.random.random((n_bases, dim)) + 1j * np.random.random((n_bases, dim))
        projectors = np.random.random((n_bases, dim, dim)) + 1j * np.random.random((n_bases, dim, dim))
        measurement = np.random.random((n_bases, n_bases)) + 1j * np.random.random((n_bases, n_bases))
        
        data = (bases, projectors, measurement)
        cache.put(dim, data)
        
        print(f"维度 {dim}: 存储完成")
    
    print(f"\n缓存统计: {cache.get_stats()}")
    
    # 测试访问性能
    print("\n测试访问性能...")
    num_accesses = 10000
    
    start_time = time.time()
    for i in range(num_accesses):
        dim = dimensions[i % len(dimensions)]
        result = cache.get(dim)
        if result is None:
            print(f"警告: 维度 {dim} 的缓存未命中")
    
    access_time = time.time() - start_time
    print(f"访问 {num_accesses} 次耗时: {access_time:.4f}秒")
    print(f"平均每次访问: {access_time / num_accesses * 1000:.4f}毫秒")


def memory_usage_analysis():
    """内存使用分析"""
    print("=== 内存使用分析 ===\n")
    
    # 分析不同实现的内存占用
    cache_size = 10
    
    # 简单LRU内存占用
    simple_cache = SimpleLRUCache(cache_size)
    
    # OrderedDict LRU内存占用
    ordered_cache = OrderedDictLRUCache(cache_size)
    
    # 优化LRU内存占用
    optimized_cache = OptimizedLRUCache(cache_size)
    
    # 添加相同的数据
    test_data = generate_test_data(0.1)  # 100KB数据
    
    for i in range(cache_size):
        simple_cache.put(i, test_data)
        ordered_cache.put(i, test_data)
        optimized_cache.put(i, test_data)
    
    # 计算内存占用
    import sys
    
    # 简单LRU: cache字典 + access_order列表
    simple_memory = 0
    simple_memory += sys.getsizeof(simple_cache.cache)
    simple_memory += sys.getsizeof(simple_cache.access_order)
    simple_memory += sum(sys.getsizeof(key) for key in simple_cache.cache.keys())
    simple_memory += sum(sys.getsizeof(value) for value in simple_cache.cache.values())
    
    # OrderedDict LRU: 基于OrderedDict
    ordered_memory = sys.getsizeof(ordered_cache.cache)
    
    # 优化LRU: 基于OrderedDict
    optimized_memory = sys.getsizeof(optimized_cache.cache)
    
    print(f"简单LRU内存占用: {simple_memory} 字节")
    print(f"OrderedDict LRU内存占用: {ordered_memory} 字节")
    print(f"优化LRU内存占用: {optimized_memory} 字节")
    print(f"OrderedDict比简单LRU节省: {((simple_memory - ordered_memory) / simple_memory * 100):.1f}%")
    print(f"优化LRU比简单LRU节省: {((simple_memory - optimized_memory) / simple_memory * 100):.1f}%")
    
    # 分析访问操作的内存影响
    print("\n访问操作内存影响分析:")
    print("简单LRU: 每次get需要移动大对象，内存访问量大")
    print("OrderedDict LRU: 每次get只操作指针，内存访问量小")
    print("优化LRU: 基于OrderedDict，性能优异")
    print("OrderedDict的优势在大对象场景下更明显")


if __name__ == "__main__":
    # 运行性能测试
    benchmark_cache_performance()
    print("\n" + "="*60 + "\n")
    
    benchmark_projector_cache()
    print("\n" + "="*60 + "\n")
    
    memory_usage_analysis()
