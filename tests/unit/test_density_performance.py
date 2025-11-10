"""
DensityMatrix性能测试

测试DensityMatrix类在各种操作下的性能表现
"""

import pytest
import numpy as np
import time
from qtomography.domain.density import DensityMatrix


class TestPerformance:
    """性能测试类"""
    
    def test_creation_performance(self):
        """测试创建性能"""
        # 测试不同维度的创建时间
        dimensions = [2, 4, 8, 16]
        
        for dim in dimensions:
            matrix = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
            matrix = (matrix + matrix.conj().T) / 2  # 确保Hermitian
            matrix = matrix / np.trace(matrix)  # 归一化
            
            start_time = time.time()
            rho = DensityMatrix(matrix)
            end_time = time.time()
            
            creation_time = end_time - start_time
            print(f"创建 {dim}x{dim} 密度矩阵耗时: {creation_time:.6f} 秒")
            
            # 性能要求：创建时间应该小于1秒
            assert creation_time < 1.0, f"创建 {dim}x{dim} 密度矩阵太慢"
    
    def test_fidelity_calculation_performance(self):
        """测试保真度计算性能"""
        # 测试不同维度的保真度计算时间
        dimensions = [2, 4, 8]
        
        for dim in dimensions:
            # 创建两个随机密度矩阵
            matrix1 = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
            matrix1 = (matrix1 + matrix1.conj().T) / 2
            matrix1 = matrix1 / np.trace(matrix1)
            
            matrix2 = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
            matrix2 = (matrix2 + matrix2.conj().T) / 2
            matrix2 = matrix2 / np.trace(matrix2)
            
            rho1 = DensityMatrix(matrix1)
            rho2 = DensityMatrix(matrix2)
            
            start_time = time.time()
            fidelity = rho1.fidelity(rho2)
            end_time = time.time()
            
            calculation_time = end_time - start_time
            print(f"计算 {dim}x{dim} 密度矩阵保真度耗时: {calculation_time:.6f} 秒")
            
            # 性能要求：保真度计算时间应该小于0.1秒
            assert calculation_time < 0.1, f"计算 {dim}x{dim} 保真度太慢"
    
    def test_property_calculation_performance(self):
        """测试属性计算性能"""
        # 创建大维度密度矩阵
        dim = 16
        matrix = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
        matrix = (matrix + matrix.conj().T) / 2
        matrix = matrix / np.trace(matrix)
        
        rho = DensityMatrix(matrix)
        
        # 测试各种属性计算时间
        properties = ['trace', 'purity', 'eigenvalues']
        
        for prop in properties:
            start_time = time.time()
            getattr(rho, prop)
            end_time = time.time()
            
            calculation_time = end_time - start_time
            print(f"计算 {prop} 属性耗时: {calculation_time:.6f} 秒")
            
            # 性能要求：属性计算时间应该小于0.01秒
            assert calculation_time < 0.01, f"计算 {prop} 属性太慢"
    
    def test_physical_constraint_performance(self):
        """测试物理约束处理性能"""
        # 创建不满足物理条件的矩阵
        dim = 8
        matrix = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
        matrix = (matrix + matrix.conj().T) / 2
        matrix = matrix * 2  # 故意破坏归一化
        
        start_time = time.time()
        rho = DensityMatrix(matrix)  # 会自动应用物理约束
        end_time = time.time()
        
        constraint_time = end_time - start_time
        print(f"应用物理约束耗时: {constraint_time:.6f} 秒")
        
        # 性能要求：物理约束处理时间应该小于0.1秒
        assert constraint_time < 0.1, "应用物理约束太慢"
    
    def test_batch_operations_performance(self):
        """测试批量操作性能"""
        # 测试批量创建和操作
        num_matrices = 100
        dim = 4
        
        matrices = []
        for _ in range(num_matrices):
            matrix = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
            matrix = (matrix + matrix.conj().T) / 2
            matrix = matrix / np.trace(matrix)
            matrices.append(matrix)
        
        # 批量创建
        start_time = time.time()
        density_matrices = [DensityMatrix(matrix) for matrix in matrices]
        end_time = time.time()
        
        creation_time = end_time - start_time
        print(f"批量创建 {num_matrices} 个 {dim}x{dim} 密度矩阵耗时: {creation_time:.6f} 秒")
        
        # 性能要求：批量创建时间应该小于1秒
        assert creation_time < 1.0, "批量创建太慢"
        
        # 批量计算保真度
        start_time = time.time()
        fidelities = []
        for i in range(0, len(density_matrices), 2):
            if i + 1 < len(density_matrices):
                fidelity = density_matrices[i].fidelity(density_matrices[i + 1])
                fidelities.append(fidelity)
        end_time = time.time()
        
        fidelity_time = end_time - start_time
        print(f"批量计算 {len(fidelities)} 个保真度耗时: {fidelity_time:.6f} 秒")
        
        # 性能要求：批量保真度计算时间应该小于2秒
        assert fidelity_time < 2.0, "批量保真度计算太慢"
    
    def test_memory_usage(self):
        """测试内存使用"""
        import psutil
        import os
        
        # 获取当前进程
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 创建大量密度矩阵
        matrices = []
        for _ in range(1000):
            matrix = np.random.randn(4, 4) + 1j * np.random.randn(4, 4)
            matrix = (matrix + matrix.conj().T) / 2
            matrix = matrix / np.trace(matrix)
            matrices.append(DensityMatrix(matrix))
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_usage = final_memory - initial_memory
        
        print(f"创建1000个4x4密度矩阵内存使用: {memory_usage:.2f} MB")
        
        # 内存使用应该合理（小于100MB）
        assert memory_usage < 100, f"内存使用过多: {memory_usage:.2f} MB"


class TestScalability:
    """可扩展性测试"""
    
    @pytest.mark.parametrize("dimension", [2, 4, 8, 16, 32])
    def test_dimension_scalability(self, dimension):
        """测试维度可扩展性"""
        # 创建指定维度的物理密度矩阵
        # 方法1：使用最大混合态（总是物理的）
        if dimension <= 8:
            matrix = np.eye(dimension) / dimension
        else:
            # 对于大维度，使用最大混合态（总是物理的）
            matrix = np.eye(dimension) / dimension
        
        start_time = time.time()
        rho = DensityMatrix(matrix)
        end_time = time.time()
        
        creation_time = end_time - start_time
        print(f"维度 {dimension}: 创建时间 {creation_time:.6f} 秒")
        
        # 验证基本属性
        assert rho.dimension == dimension
        assert rho.is_physical()
        assert np.isclose(rho.trace, 1.0)
    
    def test_large_matrix_handling(self):
        """测试大矩阵处理"""
        # 测试64x64矩阵 - 使用更稳定的方法生成物理密度矩阵
        dim = 64
        
        # 方法1：使用最大混合态（总是物理的）
        matrix = np.eye(dim) / dim
        
        start_time = time.time()
        rho = DensityMatrix(matrix)
        end_time = time.time()
        
        creation_time = end_time - start_time
        print(f"64x64 矩阵创建时间: {creation_time:.6f} 秒")
        
        # 验证基本属性
        assert rho.dimension == dim
        assert rho.is_physical()
        
        # 测试属性计算
        start_time = time.time()
        purity = rho.purity
        eigenvalues = rho.eigenvalues
        end_time = time.time()
        
        property_time = end_time - start_time
        print(f"64x64 矩阵属性计算时间: {property_time:.6f} 秒")
        
        # 验证结果合理性
        assert 0 <= purity <= 1
        assert len(eigenvalues) == dim
        assert np.all(eigenvalues >= 0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
