# DensityMatrix 测试文档

## 测试结构

```
tests/
├── conftest.py                    # pytest配置和fixtures
├── unit/                          # 单元测试
│   ├── test_density.py           # DensityMatrix核心功能测试
│   └── test_density_performance.py # 性能测试
├── integration/                   # 集成测试
│   └── test_matlab_comparison.py # MATLAB结果对比测试
├── fixtures/                      # 测试数据
│   └── test_data/                # 测试数据文件
└── README.md                     # 本文档
```

## 测试覆盖

### 1. 单元测试 (test_density.py)

#### 基本功能测试
- ✅ 基本创建和验证
- ✅ 属性计算（纯度、迹、特征值）
- ✅ 物理约束处理
- ✅ 保真度计算
- ✅ 各种创建方法
- ✅ 边界条件和异常情况

#### 测试类
- `TestDensityMatrixCreation` - 创建测试
- `TestDensityMatrixProperties` - 属性测试
- `TestPhysicalConstraints` - 物理约束测试
- `TestFidelityCalculation` - 保真度计算测试
- `TestMatrixOperations` - 矩阵操作测试
- `TestEqualityAndComparison` - 相等性测试
- `TestConvenienceFunctions` - 便捷函数测试
- `TestEdgeCases` - 边界情况测试
- `TestStringRepresentation` - 字符串表示测试

### 2. 性能测试 (test_density_performance.py)

#### 性能指标
- ✅ 创建性能（不同维度）
- ✅ 保真度计算性能
- ✅ 属性计算性能
- ✅ 物理约束处理性能
- ✅ 批量操作性能
- ✅ 内存使用测试
- ✅ 可扩展性测试

#### 性能要求
- 创建时间 < 1秒（任意维度）
- 保真度计算 < 0.1秒
- 属性计算 < 0.01秒
- 物理约束处理 < 0.1秒

### 3. 集成测试 (test_matlab_comparison.py)

#### MATLAB对比
- ✅ makephysical函数对比
- ✅ fidelity函数对比
- ✅ 线性重构对比
- ✅ 数值精度对比
- ✅ 边界情况对比
- ✅ 矩阵操作对比
- ✅ 容差处理对比
- ✅ 批量处理对比

## 运行测试

### 1. 运行所有测试
```bash
cd qtomography
python run_tests.py
```

### 2. 运行特定测试
```bash
# 运行单元测试
pytest tests/unit/test_density.py -v

# 运行性能测试
pytest tests/unit/test_density_performance.py -v

# 运行集成测试
pytest tests/integration/test_matlab_comparison.py -v
```

### 3. 运行特定测试类
```bash
# 运行创建测试
pytest tests/unit/test_density.py::TestDensityMatrixCreation -v

# 运行保真度测试
pytest tests/unit/test_density.py::TestFidelityCalculation -v
```

### 4. 运行特定测试方法
```bash
# 运行基本创建测试
pytest tests/unit/test_density.py::TestDensityMatrixCreation::test_basic_creation -v
```

## 测试数据

### 1. 生成测试数据
```bash
python scripts/generate_test_data.py
```

### 2. 测试数据格式
- `.npy` - NumPy数组文件
- `.mat` - MATLAB数据文件
- `.json` - JSON格式数据

## 测试配置

### 1. pytest.ini
- 测试发现配置
- 输出选项
- 标记定义
- 过滤警告

### 2. conftest.py
- 公共fixtures
- 测试数据生成器
- 参数化测试数据

## 测试覆盖率

目标覆盖率：> 90%

### 覆盖范围
- 所有公共方法
- 所有属性
- 所有异常情况
- 所有边界条件

## 持续集成

### 1. 自动化测试
- 每次提交自动运行测试
- 测试失败阻止合并
- 性能回归检测

### 2. 测试报告
- 测试结果报告
- 覆盖率报告
- 性能基准报告

## 故障排除

### 1. 常见问题
- 导入错误：检查Python路径
- 依赖缺失：安装所需包
- 测试失败：查看详细错误信息

### 2. 调试技巧
- 使用 `-v` 参数查看详细输出
- 使用 `--tb=long` 查看完整错误信息
- 使用 `-s` 参数查看print输出

## 贡献指南

### 1. 添加新测试
- 遵循现有命名约定
- 添加适当的文档字符串
- 使用fixtures减少重复代码

### 2. 测试最佳实践
- 测试应该独立且可重复
- 使用断言验证结果
- 测试边界条件和异常情况
- 保持测试简单和清晰
