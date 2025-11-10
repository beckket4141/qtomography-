"""
DensityMatrix类的单元测试

测试覆盖：
1. 基本创建和验证
2. 属性计算
3. 物理约束处理
4. 保真度计算
5. 各种创建方法
6. 边界条件和异常情况
"""

import pytest
import numpy as np
from qtomography.domain.density import DensityMatrix, make_physical, compute_fidelity


class TestDensityMatrixCreation:
    """测试DensityMatrix的创建"""
    
    def test_basic_creation(self):
        """测试基本创建"""
        matrix = np.array([[1, 0], [0, 0]], dtype=complex)
        rho = DensityMatrix(matrix)
        
        assert rho.dimension == 2
        assert rho.is_physical()
        # 注意：sanitize_within_tol()会改变矩阵，所以不能直接比较
        # 但应该保持物理性
        assert np.isclose(rho.trace, 1.0, atol=1e-10)
        assert np.all(rho.eigenvalues >= 0)
    
    def test_creation_with_tolerance(self):
        """测试带容差的创建"""
        matrix = np.array([[1, 0], [0, 0]], dtype=complex)
        rho = DensityMatrix(matrix, tolerance=1e-15)
        
        assert rho.tolerance == 1e-15
        assert rho.is_physical()
    
    def test_invalid_input_types(self):
        """测试无效输入类型"""
        # 非numpy数组（字符串）
        with pytest.raises(TypeError):
            DensityMatrix("not a matrix")
        
        # 非numpy数组（数字）
        with pytest.raises(TypeError):
            DensityMatrix(42)
        
        # 非2维数组
        with pytest.raises(ValueError):
            DensityMatrix(np.array([1, 2, 3]))
        
        # 非方阵
        with pytest.raises(ValueError):
            DensityMatrix(np.array([[1, 2], [3, 4], [5, 6]]))
        
        # 空矩阵
        with pytest.raises(ValueError):
            DensityMatrix(np.array([]).reshape(0, 0))
    
    def test_from_array_classmethod(self):
        """测试from_array类方法"""
        array = np.array([[1, 0], [0, 0]], dtype=complex)
        rho = DensityMatrix.from_array(array)
        
        assert isinstance(rho, DensityMatrix)
        assert rho.dimension == 2
        assert rho.is_physical()
    
    def test_from_linear_reconstruction(self):
        """测试from_linear_reconstruction类方法"""
        # 2维系统的线性重构结果
        rho_vector = np.array([0.5, 0.1, 0.1, 0.5], dtype=complex)
        rho = DensityMatrix.from_linear_reconstruction(rho_vector, dimension=2)
        
        assert isinstance(rho, DensityMatrix)
        assert rho.dimension == 2
        assert rho.is_physical()
        
        # 验证重塑和共轭操作
        expected_matrix = np.array([[0.5, 0.1], [0.1, 0.5]], dtype=complex)
        assert np.allclose(rho.matrix, expected_matrix, atol=1e-10)
    
    def test_maximally_mixed_state(self):
        """测试最大混合态创建"""
        rho = DensityMatrix.maximally_mixed(2)
        
        assert rho.dimension == 2
        assert rho.is_physical()
        assert np.isclose(rho.purity, 0.5)  # 2维最大混合态纯度 = 1/2
        assert np.isclose(rho.trace, 1.0)
        
        # 验证是最大混合态
        expected = np.eye(2) / 2
        assert np.allclose(rho.matrix, expected, atol=1e-10)
    
    def test_pure_state_creation(self):
        """测试纯态创建"""
        state_vector = np.array([1, 0], dtype=complex)
        rho = DensityMatrix.pure_state(state_vector)
        
        assert rho.dimension == 2
        assert rho.is_physical()
        assert np.isclose(rho.purity, 1.0)  # 纯态纯度 = 1
        
        # 验证是纯态（纯态应该保持原样）
        expected = np.outer(state_vector, state_vector.conj())
        assert np.allclose(rho.matrix, expected, atol=1e-10)


class TestDensityMatrixProperties:
    """测试DensityMatrix的属性"""
    
    def test_dimension_property(self):
        """测试维度属性"""
        for dim in [2, 3, 4]:
            matrix = np.eye(dim) / dim
            rho = DensityMatrix(matrix)
            assert rho.dimension == dim
    
    def test_trace_property(self):
        """测试迹属性"""
        matrix = np.array([[0.6, 0.2], [0.2, 0.4]], dtype=complex)
        rho = DensityMatrix(matrix)
        
        assert np.isclose(rho.trace, 1.0, atol=1e-10)
    
    def test_purity_property(self):
        """测试纯度属性"""
        # 纯态
        pure_state = np.array([1, 0], dtype=complex)
        rho_pure = DensityMatrix.pure_state(pure_state)
        assert np.isclose(rho_pure.purity, 1.0)
        
        # 最大混合态
        rho_mixed = DensityMatrix.maximally_mixed(2)
        assert np.isclose(rho_mixed.purity, 0.5)
        
        # 一般混合态
        matrix = np.array([[0.6, 0.2], [0.2, 0.4]], dtype=complex)
        rho = DensityMatrix(matrix)
        purity = rho.purity
        assert 0 < purity < 1
    
    def test_eigenvalues_property(self):
        """测试特征值属性"""
        matrix = np.array([[0.6, 0.2], [0.2, 0.4]], dtype=complex)
        rho = DensityMatrix(matrix)
        
        eigenvals = rho.eigenvalues
        assert len(eigenvals) == 2
        assert np.all(eigenvals >= 0)  # 所有特征值非负
        assert np.isclose(np.sum(eigenvals), 1.0)  # 特征值之和为1


class TestPhysicalConstraints:
    """测试物理约束"""
    
    def test_hermitian_property(self):
        """测试Hermitian性"""
        # 物理密度矩阵应该是Hermitian的
        matrix = np.array([[0.6, 0.2+0.1j], [0.2-0.1j, 0.4]], dtype=complex)
        rho = DensityMatrix(matrix)
        assert rho.is_hermitian()
    
    def test_positive_semidefinite_property(self):
        """测试正半定性"""
        # 物理密度矩阵应该是正半定的
        matrix = np.array([[0.6, 0.2], [0.2, 0.4]], dtype=complex)
        rho = DensityMatrix(matrix)
        assert rho.is_positive_semidefinite()
    
    def test_normalized_property(self):
        """测试归一化"""
        # 物理密度矩阵应该归一化
        matrix = np.array([[0.6, 0.2], [0.2, 0.4]], dtype=complex)
        rho = DensityMatrix(matrix)
        assert rho.is_normalized()
    
    def test_physical_property(self):
        """测试综合物理条件"""
        # 物理密度矩阵应该满足所有条件
        matrix = np.array([[0.6, 0.2+0.1j], [0.2-0.1j, 0.4]], dtype=complex)
        rho = DensityMatrix(matrix)
        assert rho.is_physical()
    
    def test_sanitize_within_tol_method(self):
        """测试sanitize_within_tol方法"""
        # 创建不满足物理条件的矩阵
        matrix = np.array([[1.5, 0.1], [0.1, -0.3]], dtype=complex)
        rho = DensityMatrix(matrix)
        
        # 应该自动修正为物理的
        assert rho.is_physical()
        assert np.isclose(rho.trace, 1.0)
        assert np.all(rho.eigenvalues >= 0)
    
    def test_external_tolerance_control(self):
        """测试外部容差控制功能"""
        # 创建一个有轻微数值误差的矩阵
        matrix = np.array([[0.6, 0.2], [0.2, 0.4]], dtype=complex)
        rho = DensityMatrix(matrix, enforce='none')
        
        # 测试严格容差
        assert rho.is_hermitian(tol=1e-12)
        assert rho.is_positive_semidefinite(tol=1e-12)
        assert rho.is_normalized(tol=1e-12)
        assert rho.is_physical(tol=1e-12)
        
        # 测试宽松容差
        assert rho.is_hermitian(tol=1e-6)
        assert rho.is_positive_semidefinite(tol=1e-6)
        assert rho.is_normalized(tol=1e-6)
        assert rho.is_physical(tol=1e-6)
    
    def test_use_auto_parameter(self):
        """测试use_auto参数功能"""
        matrix = np.array([[0.6, 0.2], [0.2, 0.4]], dtype=complex)
        rho = DensityMatrix(matrix, enforce='none')
        
        # 测试启用自适应容差（默认行为）
        assert rho.is_hermitian(use_auto=True)
        assert rho.is_positive_semidefinite(use_auto=True)
        assert rho.is_normalized(use_auto=True)
        assert rho.is_physical(use_auto=True)
        
        # 测试禁用自适应容差
        assert rho.is_hermitian(tol=1e-10, use_auto=False)
        assert rho.is_positive_semidefinite(tol=1e-10, use_auto=False)
        assert rho.is_normalized(tol=1e-10, use_auto=False)
        assert rho.is_physical(tol=1e-10, use_auto=False)
    
    def test_hermitian_relative_tolerance(self):
        """测试Hermitian性检查的相对容差"""
        # 创建一个有轻微非Hermitian性的矩阵
        matrix = np.array([[0.6, 0.2+1e-8], [0.2-1e-8, 0.4]], dtype=complex)
        rho = DensityMatrix(matrix, enforce='none')
        
        # 使用相对容差检查
        assert not rho.is_hermitian(tol=1e-10)  # 严格容差应该检测到
        assert rho.is_hermitian(tol=1e-6)       # 宽松容差应该通过
    
    def test_physical_diagnostics_consistency(self):
        """测试physical_diagnostics与检查方法的一致性"""
        matrix = np.array([[0.6, 0.2], [0.2, 0.4]], dtype=complex)
        rho = DensityMatrix(matrix, enforce='none')
        
        # 获取诊断信息
        diag = rho.physical_diagnostics()
        
        # 验证诊断信息中的检查结果与直接调用方法一致
        assert diag['is_hermitian'] == rho.is_hermitian()
        assert diag['is_positive_semidefinite'] == rho.is_positive_semidefinite()
        assert diag['is_normalized'] == rho.is_normalized()
        assert diag['is_physical'] == rho.is_physical()
        
        # 测试带参数的诊断
        diag_strict = rho.physical_diagnostics(tol=1e-12)
        assert diag_strict['is_hermitian'] == rho.is_hermitian(tol=1e-12)
        assert diag_strict['is_positive_semidefinite'] == rho.is_positive_semidefinite(tol=1e-12)
        assert diag_strict['is_normalized'] == rho.is_normalized(tol=1e-12)
        assert diag_strict['is_physical'] == rho.is_physical(tol=1e-12)


class TestFidelityCalculation:
    """测试保真度计算"""
    
    def test_fidelity_identical_matrices(self):
        """测试相同矩阵的保真度"""
        matrix = np.array([[0.6, 0.2], [0.2, 0.4]], dtype=complex)
        rho1 = DensityMatrix(matrix)
        rho2 = DensityMatrix(matrix)
        
        fidelity = rho1.fidelity(rho2)
        assert np.isclose(fidelity, 1.0, atol=1e-8)
    
    def test_fidelity_orthogonal_matrices(self):
        """测试正交矩阵的保真度"""
        rho1 = DensityMatrix.pure_state(np.array([1, 0]))
        rho2 = DensityMatrix.pure_state(np.array([0, 1]))
        
        fidelity = rho1.fidelity(rho2)
        # 正交纯态的保真度应该接近0，但由于数值误差可能不是严格的0
        assert np.isclose(fidelity, 0.0, atol=1e-4)
    
    def test_fidelity_symmetric(self):
        """测试保真度的对称性"""
        matrix1 = np.array([[0.6, 0.2], [0.2, 0.4]], dtype=complex)
        matrix2 = np.array([[0.4, 0.3], [0.3, 0.6]], dtype=complex)
        
        rho1 = DensityMatrix(matrix1)
        rho2 = DensityMatrix(matrix2)
        
        fidelity_12 = rho1.fidelity(rho2)
        fidelity_21 = rho2.fidelity(rho1)
        
        assert np.isclose(fidelity_12, fidelity_21, atol=1e-8)
    
    def test_fidelity_range(self):
        """测试保真度范围 [0, 1]"""
        matrix1 = np.array([[0.6, 0.2], [0.2, 0.4]], dtype=complex)
        matrix2 = np.array([[0.4, 0.3], [0.3, 0.6]], dtype=complex)
        
        rho1 = DensityMatrix(matrix1)
        rho2 = DensityMatrix(matrix2)
        
        fidelity = rho1.fidelity(rho2)
        assert 0 <= fidelity <= 1
    
    def test_fidelity_different_dimensions(self):
        """测试不同维度矩阵的保真度计算"""
        rho1 = DensityMatrix(np.array([[1, 0], [0, 0]]))
        rho2 = DensityMatrix(np.array([[1, 0, 0], [0, 0, 0], [0, 0, 0]]))
        
        with pytest.raises(ValueError):
            rho1.fidelity(rho2)


class TestMatrixOperations:
    """测试矩阵操作"""
    
    def test_matrix_square_root(self):
        """测试矩阵平方根"""
        matrix = np.array([[0.6, 0.2], [0.2, 0.4]], dtype=complex)
        rho = DensityMatrix(matrix)
        
        sqrt_matrix = rho.matrix_square_root()
        
        # 验证平方根性质
        reconstructed = sqrt_matrix @ sqrt_matrix
        assert np.allclose(reconstructed, matrix, atol=1e-10)
    
    def test_real_imag_parts(self):
        """测试实部和虚部"""
        matrix = np.array([[0.6+0.1j, 0.2-0.3j], [0.2+0.3j, 0.4-0.2j]], dtype=complex)
        rho = DensityMatrix(matrix)
        
        real_part = rho.get_real_part()
        imag_part = rho.get_imag_part()
        
        # 注意：sanitize_within_tol()会改变矩阵，所以比较的是处理后的矩阵
        assert np.allclose(real_part, np.real(rho.matrix), atol=1e-10)
        assert np.allclose(imag_part, np.imag(rho.matrix), atol=1e-10)
    
    def test_amplitude_phase(self):
        """测试振幅和相位"""
        matrix = np.array([[0.6+0.1j, 0.2-0.3j], [0.2+0.3j, 0.4-0.2j]], dtype=complex)
        rho = DensityMatrix(matrix)
        
        amplitude = rho.get_amplitude()
        phase = rho.get_phase()
        
        # 注意：sanitize_within_tol()会改变矩阵，所以比较的是处理后的矩阵
        assert np.allclose(amplitude, np.abs(rho.matrix), atol=1e-10)
        assert np.allclose(phase, np.angle(rho.matrix), atol=1e-10)


class TestEqualityAndComparison:
    """测试相等性和比较"""
    
    def test_equality_identical_matrices(self):
        """测试相同矩阵的相等性"""
        matrix = np.array([[0.6, 0.2], [0.2, 0.4]], dtype=complex)
        rho1 = DensityMatrix(matrix)
        rho2 = DensityMatrix(matrix)
        
        assert rho1 == rho2
    
    def test_equality_different_matrices(self):
        """测试不同矩阵的相等性"""
        matrix1 = np.array([[0.6, 0.2], [0.2, 0.4]], dtype=complex)
        matrix2 = np.array([[0.4, 0.3], [0.3, 0.6]], dtype=complex)
        
        rho1 = DensityMatrix(matrix1)
        rho2 = DensityMatrix(matrix2)
        
        assert rho1 != rho2
    
    def test_equality_with_tolerance(self):
        """测试带容差的相等性"""
        matrix1 = np.array([[0.6, 0.2], [0.2, 0.4]], dtype=complex)
        matrix2 = matrix1 + 1e-12  # 添加微小差异
        
        rho1 = DensityMatrix(matrix1, tolerance=1e-10)
        rho2 = DensityMatrix(matrix2, tolerance=1e-10)
        
        assert rho1 == rho2  # 在容差范围内应该相等
    
    def test_equality_different_types(self):
        """测试不同类型对象的相等性"""
        matrix = np.array([[0.6, 0.2], [0.2, 0.4]], dtype=complex)
        rho = DensityMatrix(matrix)
        
        assert rho != "not a density matrix"
        assert rho != 42
        assert rho != None


class TestConvenienceFunctions:
    """测试便捷函数"""
    
    def test_make_physical_function(self):
        """测试make_physical便捷函数"""
        # 创建不满足物理条件的矩阵
        matrix = np.array([[1.5, 0.1], [0.1, -0.3]], dtype=complex)
        
        # 使用便捷函数
        physical_matrix = make_physical(matrix)
        
        # 验证结果
        rho = DensityMatrix(physical_matrix)
        assert rho.is_physical()
        assert np.isclose(rho.trace, 1.0)
        assert np.all(rho.eigenvalues >= 0)
    
    def test_compute_fidelity_function(self):
        """测试compute_fidelity便捷函数"""
        matrix1 = np.array([[0.6, 0.2], [0.2, 0.4]], dtype=complex)
        matrix2 = np.array([[0.4, 0.3], [0.3, 0.6]], dtype=complex)
        
        fidelity = compute_fidelity(matrix1, matrix2)
        
        # 验证结果
        rho1 = DensityMatrix(matrix1)
        rho2 = DensityMatrix(matrix2)
        expected_fidelity = rho1.fidelity(rho2)
        
        assert np.isclose(fidelity, expected_fidelity, atol=1e-8)


class TestEdgeCases:
    """测试边界情况"""
    
    def test_single_element_matrix(self):
        """测试单元素矩阵"""
        matrix = np.array([[1]], dtype=complex)
        rho = DensityMatrix(matrix)
        
        assert rho.dimension == 1
        assert rho.is_physical()
        assert np.isclose(rho.trace, 1.0)
        assert np.isclose(rho.purity, 1.0)
    
    def test_large_dimension_matrix(self):
        """测试大维度矩阵"""
        dim = 10
        matrix = np.eye(dim) / dim
        rho = DensityMatrix(matrix)
        
        assert rho.dimension == dim
        assert rho.is_physical()
        assert np.isclose(rho.trace, 1.0)
    
    def test_numerical_precision(self):
        """测试数值精度"""
        # 测试接近机器精度的数值
        matrix = np.array([[1-1e-15, 1e-16], [1e-16, 1e-15]], dtype=complex)
        rho = DensityMatrix(matrix)
        
        assert rho.is_physical()
        assert np.isclose(rho.trace, 1.0, atol=1e-10)
    
    def test_complex_matrix(self):
        """测试复数矩阵"""
        matrix = np.array([[0.5+0.1j, 0.2-0.3j], [0.2+0.3j, 0.5-0.1j]], dtype=complex)
        rho = DensityMatrix(matrix)
        
        assert rho.is_physical()
        assert rho.is_hermitian()


class TestStringRepresentation:
    """测试字符串表示"""
    
    def test_str_representation(self):
        """测试__str__方法"""
        matrix = np.array([[0.6, 0.2], [0.2, 0.4]], dtype=complex)
        rho = DensityMatrix(matrix)
        
        str_repr = str(rho)
        assert "DensityMatrix" in str_repr
        assert "dim=2" in str_repr
        assert "purity" in str_repr
    
    def test_repr_representation(self):
        """测试__repr__方法"""
        matrix = np.array([[0.6, 0.2], [0.2, 0.4]], dtype=complex)
        rho = DensityMatrix(matrix)
        
        repr_str = repr(rho)
        assert "DensityMatrix" in repr_str
        assert "dimension=2" in repr_str
        assert "purity" in repr_str
        assert "trace" in repr_str
        assert "is_physical" in repr_str


if __name__ == "__main__":
    pytest.main([__file__])
