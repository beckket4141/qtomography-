"""重构结果的可视化工具。"""

from __future__ import annotations

from typing import Sequence

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  # 注册 3D 支持

from qtomography.domain.density import DensityMatrix
from qtomography.infrastructure.persistence import ReconstructionRecord

__all__ = ["ReconstructionVisualizer"]


class ReconstructionVisualizer:
    """提供与原 MATLAB 脚本类似的绘图辅助方法。"""

    def plot_density_heatmap(self, density: DensityMatrix, *, title: str = "") -> plt.Figure:
        """绘制密度矩阵实部/虚部的热力图。"""

        matrix = density.matrix
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))

        im0 = axes[0].imshow(matrix.real, cmap="RdBu", interpolation="nearest")
        axes[0].set_title("Real part")
        fig.colorbar(im0, ax=axes[0], shrink=0.8)

        im1 = axes[1].imshow(matrix.imag, cmap="RdBu", interpolation="nearest")
        axes[1].set_title("Imag part")
        fig.colorbar(im1, ax=axes[1], shrink=0.8)

        if title:
            fig.suptitle(title)
        fig.tight_layout()
        return fig

    def plot_real_imag_3d(self, density: DensityMatrix, *, title: str = "") -> tuple[plt.Figure, plt.Figure]:
        """以三维柱状图绘制实部与虚部（两张独立图，完全匹配 plot_density_matrix_python.py）。
        
        Returns:
            (fig_real, fig_imag): 实部图和虚部图的图形对象
        """

        matrix = density.matrix
        dim = matrix.shape[0]

        # 1. 智能标签生成（匹配MATLAB逻辑）
        labels = self._generate_quantum_labels(dim)

        # 2. 实部处理
        real_part = matrix.real

        # 3. 虚部处理（添加阈值过滤，匹配MATLAB逻辑）
        threshold = 1e-4
        imag_part = np.zeros_like(matrix, dtype=float)
        for i in range(dim):
            for j in range(dim):
                if np.abs(matrix[i, j]) > threshold:
                    imag_part[i, j] = matrix[i, j].imag
                else:
                    imag_part[i, j] = 0.0  # 振幅太小的元素虚部设为0

        # 4. 精确坐标对齐（学习 plot_density_matrix_python.py）
        # 使用 +0.5 偏移，确保柱子中心对齐到网格中心
        x = np.arange(dim) + 0.5
        y = np.arange(dim) + 0.5
        dx = dy = 0.8  # 柱子宽度，留出间隙

        # 5. 绘制实部图（独立图形）
        fig_real = plt.figure(figsize=(10, 8))
        ax_real = fig_real.add_subplot(111, projection='3d')
        
        # 准备实部数据
        dz_real = real_part.flatten()
        
        # 创建颜色映射（使用viridis渐变色）
        if dz_real.max() > dz_real.min():
            colors_real = plt.cm.viridis((dz_real - dz_real.min()) / (dz_real.max() - dz_real.min()))
        else:
            colors_real = plt.cm.viridis(np.ones_like(dz_real) * 0.5)
        
        # 逐个绘制柱子（精确对齐）
        for i in range(dim):
            for j in range(dim):
                idx = i * dim + j
                ax_real.bar3d(
                    x[j] - dx / 2, y[i] - dy / 2, 0,  # 底部位置（左下角）
                    dx, dy, dz_real[idx],  # 宽度和高度
                    color=colors_real[idx],
                    alpha=0.8,
                    shade=True,
                    edgecolor='black',
                    linewidth=0.5
                )
        
        # 设置标签 - 确保刻度与柱子对齐
        ax_real.set_xticks(x)
        ax_real.set_yticks(y)
        ax_real.set_xticklabels(labels, rotation=45, ha='right', fontsize=10)
        ax_real.set_yticklabels(labels, rotation=-45, ha='left', fontsize=10)
        
        # 设置坐标轴范围，确保网格对齐
        ax_real.set_xlim(-0.1, dim + 0.1)
        ax_real.set_ylim(-0.1, dim + 0.1)
        
        # 固定Z轴范围（匹配MATLAB）
        ax_real.set_zlim(0, 0.5)
        ax_real.set_zticks(np.arange(0, 0.6, 0.1))
        
        # 设置标签和标题
        ax_real.set_xlabel('Basis State', fontsize=12)
        ax_real.set_ylabel('Basis State', fontsize=12)
        ax_real.set_zlabel('Real Part', fontsize=12)
        ax_real.set_title(f'Density Matrix Real Part - {dim}D Quantum System', fontsize=14, fontweight='bold')
        
        # 设置观察角度（优化视角）
        ax_real.view_init(elev=30, azim=30)
        
        # 添加总标题（如果提供）
        if title:
            fig_real.suptitle(title, fontsize=12, y=0.98)
        
        plt.tight_layout()

        # 6. 绘制虚部图（独立图形）
        fig_imag = plt.figure(figsize=(10, 8))
        ax_imag = fig_imag.add_subplot(111, projection='3d')
        
        # 准备虚部数据
        dz_imag = imag_part.flatten()
        
        # 计算虚部的实际范围（包括负值）
        dz_min = dz_imag.min()
        dz_max = dz_imag.max()
        dz_range = dz_max - dz_min
        
        # 如果范围太小，使用默认范围
        if dz_range < 1e-10:
            dz_min = -0.25
            dz_max = 0.25
            dz_range = 0.5
        else:
            # 扩展范围以便更好地显示
            dz_center = (dz_min + dz_max) / 2
            dz_range = max(dz_range * 1.1, 0.5)  # 至少0.5的范围
            dz_min = dz_center - dz_range / 2
            dz_max = dz_center + dz_range / 2
        
        # 创建颜色映射（使用RdBu区分正负值）
        if dz_range > 1e-10:
            # 归一化到[-1, 1]范围用于颜色映射
            dz_normalized = (dz_imag - dz_min) / dz_range * 2 - 1  # 映射到[-1, 1]
            colors_imag = plt.cm.RdBu((dz_normalized + 1) / 2)  # 映射到[0, 1]用于colormap
        else:
            colors_imag = plt.cm.RdBu(np.ones_like(dz_imag) * 0.5)
        
        # 逐个绘制柱子（处理负值）
        for i in range(dim):
            for j in range(dim):
                idx = i * dim + j
                z_value = dz_imag[idx]
                
                if z_value >= 0:
                    # 正值：从0向上绘制
                    ax_imag.bar3d(
                        x[j] - dx / 2, y[i] - dy / 2, 0,  # 底部在0
                        dx, dy, z_value,  # 高度为正值
                        color=colors_imag[idx],
                        alpha=0.8,
                        shade=True,
                        edgecolor='black',
                        linewidth=0.5
                    )
                else:
                    # 负值：从0向下绘制
                    ax_imag.bar3d(
                        x[j] - dx / 2, y[i] - dy / 2, z_value,  # 底部在负值位置
                        dx, dy, abs(z_value),  # 高度为绝对值
                        color=colors_imag[idx],
                        alpha=0.8,
                        shade=True,
                        edgecolor='black',
                        linewidth=0.5
                    )
        
        # 设置标签 - 确保刻度与柱子对齐
        ax_imag.set_xticks(x)
        ax_imag.set_yticks(y)
        ax_imag.set_xticklabels(labels, rotation=45, ha='right', fontsize=10)
        ax_imag.set_yticklabels(labels, rotation=-45, ha='left', fontsize=10)
        
        # 设置坐标轴范围，确保网格对齐
        ax_imag.set_xlim(-0.1, dim + 0.1)
        ax_imag.set_ylim(-0.1, dim + 0.1)
        
        # 设置Z轴 - 动态范围以包含负值（但保持合理范围）
        # 如果范围太大，限制在合理范围内
        if dz_max > 0.5 or dz_min < -0.5:
            # 超出MATLAB范围时，使用动态范围但限制最大范围
            z_ticks = np.linspace(dz_min, dz_max, 6)
            ax_imag.set_zlim(dz_min, dz_max)
            ax_imag.set_zticks(z_ticks)
            ax_imag.set_zticklabels([f'{tick:.3f}' for tick in z_ticks])
        else:
            # 在合理范围内，使用固定范围（匹配MATLAB）
            ax_imag.set_zlim(0, 0.5)
            ax_imag.set_zticks(np.arange(0, 0.6, 0.1))
        
        # 设置标签和标题
        ax_imag.set_xlabel('Basis State', fontsize=12)
        ax_imag.set_ylabel('Basis State', fontsize=12)
        ax_imag.set_zlabel('Imaginary Part', fontsize=12)
        ax_imag.set_title(f'Density Matrix Imaginary Part - {dim}D Quantum System', fontsize=14, fontweight='bold')
        
        # 设置观察角度（优化视角）
        ax_imag.view_init(elev=30, azim=30)
        
        # 添加总标题（如果提供）
        if title:
            fig_imag.suptitle(title, fontsize=12, y=0.98)
        
        plt.tight_layout()

        return fig_real, fig_imag

    def _generate_quantum_labels(self, dimension: int) -> list[str]:
        """生成量子态标签（匹配MATLAB逻辑）。
        
        如果维度是完全平方数，使用 |pq> 格式（如 |00>, |01>）
        否则使用 |02d> 格式（如 |00>, |01>, |02>）
        
        Args:
            dimension: 量子系统维度
            
        Returns:
            标签列表
        """
        labels = []
        root_n = np.sqrt(dimension)
        
        # 检查是否为完全平方数
        if abs(root_n - round(root_n)) < 1e-12:
            # 完全平方数：使用 |pq> 格式
            a_dim = int(round(root_n))
            b_dim = int(round(root_n))
            for k in range(dimension):
                p = (k) // b_dim
                q = (k) % b_dim
                labels.append(f"|{p}{q}>")
        else:
            # 非完全平方数：使用 |02d> 格式
            for i in range(dimension):
                labels.append(f"|{i:02d}>")
        
        return labels

    def plot_amplitude_phase(self, density: DensityMatrix, *, title: str = "") -> plt.Figure:
        """绘制振幅与相位的三维柱状图。"""

        matrix = density.matrix
        dim = matrix.shape[0]
        labels = [f"Basis-{i + 1}" for i in range(dim)]

        amplitude = np.abs(matrix)
        threshold = 1e-4
        phase_matrix = np.zeros((dim, dim), dtype=float)
        for i in range(dim):
            for j in range(dim):
                if i == j:
                    continue
                val = matrix[i, j]
                if np.abs(val) < threshold:
                    continue
                phase_matrix[i, j] = np.angle(val)
        phase_pi = phase_matrix / np.pi

        fig = plt.figure(figsize=(12, 5))

        ax_amp = fig.add_subplot(1, 2, 1, projection="3d")
        xpos, ypos = np.meshgrid(np.arange(dim), np.arange(dim))
        xpos = xpos.ravel()
        ypos = ypos.ravel()
        zpos = np.zeros_like(xpos, dtype=float)
        dx = dy = 0.6
        dz_amp = amplitude.ravel()
        ax_amp.bar3d(xpos, ypos, zpos, dx, dy, dz_amp, shade=True, color="#1f77b4")
        ax_amp.set_xticks(np.arange(dim) + dx / 2)
        ax_amp.set_xticklabels(labels, rotation=45, ha="right")
        ax_amp.set_yticks(np.arange(dim) + dy / 2)
        ax_amp.set_yticklabels(labels, rotation=45, ha="right")
        ax_amp.set_zlabel("|ρ|")
        ax_amp.set_title("Amplitude (bar3d)")

        ax_phase = fig.add_subplot(1, 2, 2, projection="3d")
        dz_phase = phase_pi.ravel()
        ax_phase.bar3d(xpos, ypos, zpos, dx, dy, dz_phase, shade=True, color="#ff7f0e")
        ax_phase.set_xticks(np.arange(dim) + dx / 2)
        ax_phase.set_xticklabels(labels, rotation=45, ha="right")
        ax_phase.set_yticks(np.arange(dim) + dy / 2)
        ax_phase.set_yticklabels(labels, rotation=45, ha="right")
        ax_phase.set_zlabel("Phase / π")
        ax_phase.set_title("Phase (bar3d)")

        phase_min = np.min(dz_phase)
        phase_max = np.max(dz_phase)
        if np.isclose(phase_min, phase_max):
            ax_phase.set_zlim(-2, 2)
            ax_phase.set_zticks(np.linspace(-2, 2, 5))
        else:
            ax_phase.set_zlim(phase_min, phase_max)

        if title:
            fig.suptitle(title)
        fig.subplots_adjust(left=0.08, right=0.92, bottom=0.1, top=0.9, wspace=0.35)
        return fig

    def plot_metric(
        self,
        records: Sequence[ReconstructionRecord],
        metric: str,
        *,
        title: str = "",
    ) -> plt.Figure:
        """绘制指标随记录的变化曲线。"""

        values = []
        labels = []
        for idx, record in enumerate(records):
            if metric in record.metrics:
                values.append(record.metrics[metric])
                labels.append(record.timestamp or f"sample-{idx}")

        if not values:
            raise ValueError(f"记录集中未找到指标 '{metric}'")

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(range(len(values)), values, marker="o")
        ax.set_xlabel("Record index")
        ax.set_ylabel(metric)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.grid(True, linestyle="--", alpha=0.5)
        if title:
            ax.set_title(title)
        fig.tight_layout()
        return fig
