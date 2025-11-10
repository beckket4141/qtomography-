# 3D可视化功能增强 - 实部虚部3D图

_Date: 2025-10-07_
_Status: ✅ 已完成并测试_

## 📋 需求背景

用户希望为密度矩阵的**实部和虚部**添加与幅度-相位图类似的**3D柱状图可视化**，以便更直观地展示密度矩阵的结构。

## ✨ 新增功能

### **方法：`plot_real_imag_3d`**

```python
def plot_real_imag_3d(self, density: DensityMatrix, *, title: str = "") -> plt.Figure:
    """Draw real/imaginary parts as 3D bar charts."""
```

**功能说明：**
- 左图：实部（Real part），蓝色 `#1f77b4`
- 右图：虚部（Imaginary part），橙色 `#ff7f0e`
- 使用 `bar3d` 与现有的 `plot_amplitude_phase` 保持一致的风格
- Z轴标签：`Re(ρ)` 和 `Im(ρ)`

## 📊 可视化方法全览
> 2025-10-08 更新：ReconstructionVisualizer 实现已迁入 qtomography/infrastructure/visualization，qtomography.visualization 仍提供兼容导入。

现在 `ReconstructionVisualizer` 提供以下可视化方法：

| 方法 | 类型 | 展示内容 | 说明 |
|------|------|----------|------|
| `plot_density_heatmap` | 2D热图 | 实部 & 虚部 | 传统2D彩色热图 |
| `plot_real_imag_3d` | 3D柱状图 | 实部 & 虚部 | ✨ **新增** - 3D bar3d展示 |
| `plot_amplitude_phase` | 3D柱状图 | 幅度 & 相位 | 3D bar3d展示 |
| `plot_metric` | 2D折线图 | 指标趋势 | 批量分析 |

## 💡 使用示例

### 基本使用

```python
from qtomography.domain.density import DensityMatrix
from qtomography.infrastructure.visualization import ReconstructionVisualizer
import numpy as np

# 创建密度矩阵
rho = np.array([[0.6, 0.2-0.1j], 
                [0.2+0.1j, 0.4]], dtype=complex)
density = DensityMatrix(rho)

# 创建可视化器
visualizer = ReconstructionVisualizer()

# 生成3D实部虚部图
fig = visualizer.plot_real_imag_3d(density, title="Density Matrix - Real & Imaginary Parts")
fig.savefig("real_imag_3d.png", dpi=150, bbox_inches="tight")
```

### 完整可视化流程

```python
# 1. 2D热图
fig1 = visualizer.plot_density_heatmap(density, title="2D Heatmap")
fig1.savefig("heatmap_2d.png")

# 2. 3D实部虚部图 (新功能)
fig2 = visualizer.plot_real_imag_3d(density, title="3D Real & Imaginary")
fig2.savefig("real_imag_3d.png")

# 3. 3D幅度相位图
fig3 = visualizer.plot_amplitude_phase(density, title="3D Amplitude & Phase")
fig3.savefig("amp_phase_3d.png")
```

## 🧪 测试覆盖

### 单元测试

在 `tests/unit/test_visualization.py` 中新增测试：

```python
def test_plot_real_imag_3d(tmp_path):
    vis = ReconstructionVisualizer()
    density = _sample_density()
    fig = vis.plot_real_imag_3d(density, title="real-imag-3d")
    fig.savefig(tmp_path / "real_imag_3d.png")
    plt.close(fig)
```

### 测试结果

```bash
$ python -m pytest python/tests/unit/test_visualization.py -v

python/tests/unit/test_visualization.py::test_plot_density_heatmap PASSED   [ 25%]
python/tests/unit/test_visualization.py::test_plot_real_imag_3d PASSED      [ 50%]
python/tests/unit/test_visualization.py::test_plot_amplitude_phase PASSED   [ 75%]
python/tests/unit/test_visualization.py::test_plot_metric PASSED            [100%]

======================== 4 passed, 3 warnings in 1.40s ========================
```

✅ **所有测试通过！**

## 📝 实现细节

### 代码结构

```python
def plot_real_imag_3d(self, density: DensityMatrix, *, title: str = "") -> plt.Figure:
    matrix = density.matrix
    dim = matrix.shape[0]
    labels = [f"Basis-{i + 1}" for i in range(dim)]
    
    real_part = matrix.real
    imag_part = matrix.imag
    
    fig = plt.figure(figsize=(12, 5))
    
    # 准备3D柱状图的位置数据
    xpos, ypos = np.meshgrid(np.arange(dim), np.arange(dim))
    xpos = xpos.ravel()
    ypos = ypos.ravel()
    zpos = np.zeros_like(xpos, dtype=float)
    dx = dy = 0.6
    
    # 左图：实部
    ax_real = fig.add_subplot(1, 2, 1, projection="3d")
    dz_real = real_part.ravel()
    ax_real.bar3d(xpos, ypos, zpos, dx, dy, dz_real, shade=True, color="#1f77b4")
    ax_real.set_zlabel("Re(ρ)")
    ax_real.set_title("Real part (bar3d)")
    
    # 右图：虚部
    ax_imag = fig.add_subplot(1, 2, 2, projection="3d")
    dz_imag = imag_part.ravel()
    ax_imag.bar3d(xpos, ypos, zpos, dx, dy, dz_imag, shade=True, color="#ff7f0e")
    ax_imag.set_zlabel("Im(ρ)")
    ax_imag.set_title("Imaginary part (bar3d)")
    
    if title:
        fig.suptitle(title)
    fig.tight_layout()
    return fig
```

### 设计考虑

1. **一致性**：与 `plot_amplitude_phase` 保持相同的布局和风格
2. **颜色选择**：
   - 实部：蓝色 `#1f77b4` （与matplotlib默认颜色一致）
   - 虚部：橙色 `#ff7f0e` （与现有相位图颜色一致）
3. **坐标轴标签**：使用数学符号 `Re(ρ)` 和 `Im(ρ)` 更专业
4. **图像尺寸**：`figsize=(12, 5)` 确保两个子图有足够空间

## 🎯 应用场景

1. **量子态分析**：直观展示密度矩阵的实部和虚部结构
2. **论文发表**：提供专业的3D可视化图表
3. **教学演示**：帮助理解复数矩阵的结构
4. **调试验证**：快速检查重构结果的合理性

## 📂 相关文件

- **实现**: `python/qtomography/infrastructure/visualization/reconstruction_visualizer.py`
- **测试**: `python/tests/unit/test_visualization.py`
- **演示**: `python/examples/demo_3d_visualization.py`

## ✅ 完成清单

- [x] 实现 `plot_real_imag_3d` 方法
- [x] 添加单元测试
- [x] 所有测试通过
- [x] 代码风格与现有方法一致
- [x] 文档完善

## 🚀 后续可能的增强

如有需要，可以进一步添加：

1. **表面图选项**：使用 `plot_surface` 替代 `bar3d`
2. **颜色映射**：根据数值大小使用渐变色
3. **交互式3D**：使用 `plotly` 支持旋转缩放
4. **组合视图**：将4个图（2D热图 + 2个3D图）放在一起

---

**状态：✅ 已完成并通过测试**  
**影响：增强了可视化工具的完整性，用户现在可以以2D和3D两种方式查看实部/虚部和幅度/相位**

