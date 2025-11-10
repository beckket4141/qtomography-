"""High-level reconstruction controller.

This module coordinates tomography reconstruction workflows on behalf of the application layer.

Responsibilities:
    1. Validate batch configuration objects (`ReconstructionConfig`).
    2. Invoke linear and MLE reconstructors in a unified pipeline.
    3. Persist reconstruction records and derived metrics.
    4. Produce summary reports (CSV).

Design notes:
    - Facade pattern: expose a simple entry point for complex processing.
    - Strategy pattern: allow runtime selection of reconstruction algorithms.
    - Template Method: enforce a consistent per-sample processing skeleton.

Usage example:
    >>> from qtomography.app.controller import ReconstructionConfig, run_batch
    >>> config = ReconstructionConfig(
    ...     input_path="data/measurements.csv",
    ...     output_dir="output/",
    ...     methods=["linear", "mle"],
    ...     dimension=4,
    ... )
    >>> result = run_batch(config)
    >>> print(f"processed {result.num_samples} samples")
    >>> df = result.to_dataframe()
"""




# ============================================================
# 标准库导入
# ============================================================



from __future__ import annotations  # 启用延迟注解评估（PEP 563），支持前向引用



import logging  # 统一日志记录
from concurrent.futures import Executor, Future, ThreadPoolExecutor  # 异步执行支持
from dataclasses import dataclass  # 用于创建配置和结果类，自动生成__init__、__repr__ 等方法
from pathlib import Path           # 跨平台路径操作
from threading import Event  # 用于任务取消
from typing import Callable, Iterable, List, Optional, Sequence, Tuple, Union  # 类型标注



# ============================================================
# 第三方库导入
# ============================================================



import numpy as np    # 数值计算和数组操作

import pandas as pd   # 数据加载（CSV、Excel）和汇总表生成



# ============================================================
# 项目内部导入
# ============================================================



from qtomography.analysis import (  # 分析层工具
    analyze_density_matrix,

    condition_number,

    eigenvalue_entropy,

)

from qtomography.app.exceptions import ReconstructionCancelled, ReconstructionError
from qtomography.domain.reconstruction.linear import LinearReconstructor  # 线性重构算法
from qtomography.domain.reconstruction.wls import WLSReconstructor        # WLS 重构算法
from qtomography.domain.reconstruction.rhor_strict import RrhoStrictReconstructor  # RρR Strict 重构算法
from qtomography.domain.projectors import ProjectorSet

from qtomography.infrastructure.persistence.result_repository import (

    ReconstructionRecord,  # 单次重构结果的数据记录

    ResultRepository,      # 结果持久化仓库（负责保存/加载 JSON/CSV）

)
from qtomography.domain.ports.persistence import IResultRepository


logging.getLogger(__name__).addHandler(logging.NullHandler())



# ============================================================
# 辅助计算函数（阶段3.1 新增 - 2025-10-07）
# ============================================================



# ============================================================
# 模块级常量
# ============================================================



# 允许使用的重构方法集合（用于配置验证）
_ALLOWED_METHODS = {"linear", "wls", "rhor"}




@dataclass(frozen=True)

class ReconstructionConfig:
    
    """重构任务的批处理配置（Reconstruction Batch Configuration）。
    

    这是一个不可变配置类（frozen=True），用于封装重构工作流的所有参数。
    使用 dataclass 装饰器可以自动生成初始化方法和字符串表示。
    

    属性：

        input_path: 输入数据文件路径

            - 支持格式：CSV (.csv/.txt)、Excel (.xlsx/.xls)

            - 数据格式：每列一个样本，行数应为 dimension² （测量概率向量）

            

        output_dir: 输出目录路径

            - 自动创建子目录：records/（JSON 结果）、summary.csv（汇总表）
            

        methods: 要使用的重构算法列表

    design: str = "mub"  # measurement design: mub|sic|nopovm
            - 可选值：["linear"]、["wls"]、["linear", "wls"]、["both"]

            - "both" 会自动展开为["linear", "wls"]

            - 默认：("linear", "wls") - 同时运行两种算法

            

        dimension: 量子系统维度（Hilbert 空间维数）
            - 若为 None，会根据输入行数自动推断（需为完全平方数）
            - 例：dimension=4 表示 4 维系统（需要16个测量概率）
            

        sheet: Excel 文件的工作表名称或索引
            - 仅对 .xlsx/.xls 文件有效

            - 可以是字符串（工作表名）或整数（0-based 索引）
            - 默认：None（使用第一个工作表）
            

        linear_regularization: 线性重构的 Tikhonov 正则化参数λ

            - 用于求解 (A^T A + λI) x = A^T b

            - None 表示不使用正则化（直接最小二乘）

            - 典型范围：1e-8 ~ 1e-3

            

        wls_regularization: WLS 重构的正则化参数

            - 用于目标函数：χ²+ λ·Tr(ρ²)（鼓励纯态）

            - None 表示不使用正则化

            - 典型范围：1e-6 ~ 1e-2

            

        wls_max_iterations: WLS 优化的最大迭代次数
            - 默认：2000（L-BFGS-B 优化器）

            - 若未收敛，会在日志中记录警告
            

        tolerance: 数值稳定性容差（用于特征值裁剪、概率归一化等）
            - 默认：1e-9

            - 小于此值的特征值会被置零（保持正定性）

            

        cache_projectors: 是否缓存投影算子矩阵

            - True：加快批处理速度（投影算子只计算一次）

            - False：每次重构重新计算（节省内存）
            - 建议批处理时设为 True
    

    验证规则：
        - dimension 必须 >= 2（至少是 2 维系统）

        - tolerance 必须 > 0

        - mle_max_iterations 必须 > 0

        - methods 中的算法名必须在 {"linear", "mle"} 中
    
    

    使用示例：
        >>> config = ReconstructionConfig(

        ...     input_path="measurements.csv",

        ...     output_dir="results/",

        ...     methods=["mle"],

        ...     dimension=4,

        ...     mle_regularization=1e-5,

        ... )

        >>> # 配置是不可变的，不能修改

        >>> # config.dimension = 8  # ❌ 会报错（frozen=True）
    """



    # ========== 必需参数 ==========

    input_path: Path  # 输入文件路径（会在__post_init__中转换为 Path 对象）
    output_dir: Path  # 输出目录路径（会在__post_init__中转换为 Path 对象）
    

    # ========== 算法选择 ==========

    methods: Sequence[str] = ("linear", "wls")  # 默认同时运行两种算法

    design: str = "mub"  # measurement design: mub|sic|nopovm

    

    # ========== 系统参数 ==========

    dimension: Optional[int] = None  # None 表示自动推断

    

    # ========== 数据加载参数 ==========

    sheet: Optional[Union[str, int]] = None  # Excel 工作表（CSV 忽略此参数）

    

    # ========== 正则化参数 ==========

    linear_regularization: Optional[float] = None  # 线性重构的 λ

    wls_regularization: Optional[float] = None     # WLS 重构的 λ

    

    # ========== 优化参数 ==========

    wls_max_iterations: int = 2000  # WLS 最大迭代次数
    tolerance: float = 1e-9         # 数值容差
    

    # ========== 性能参数 ==========

    cache_projectors: bool = True  # 是否缓存投影算子（批处理推荐 True）
    analyze_bell: bool = False       # 是否在重构后执行 Bell 态分析


    def __post_init__(self) -> None:

        """初始化后的验证和标准化处理。
        

        注意：由于frozen=True，这里使用object.__setattr__来修改属性。
        普通的 self.attribute = value 会因为不可变性而报错。
        

        处理流程：
            1. 将字符串路径转换为Path对象

            2. 验证数值参数的有效性（dimension、tolerance、iterations）
            3. 标准化和验证 methods 参数（例如将 "both" 展开）
        

        抛出：
            ValueError: 如果任何验证失败
        
        """

        # 1. 路径标准化（确保是 Path 对象，支持跨平台操作）
        object.__setattr__(self, "input_path", Path(self.input_path))

        object.__setattr__(self, "output_dir", Path(self.output_dir))
        
        
        # 2. 验证 dimension（如果提供）
        if self.dimension is not None and self.dimension < 2:

            raise ValueError("dimension must be >= 2 if provided")
        
        
        # 3. 验证 tolerance（必须为正数）
        if self.tolerance <= 0:

            raise ValueError("tolerance must be positive")
        
        
        # 4. 验证 WLS 迭代次数（必须为正整数）
        if self.wls_max_iterations <= 0:

            raise ValueError("wls_max_iterations must be positive")
        
        
        # 5. 标准化并验证重构方法（例如"both" → ["linear", "wls"]）
        normalized_methods = _normalize_methods(self.methods)

        object.__setattr__(self, "methods", normalized_methods)




@dataclass

class SummaryResult:

    """控制器返回的汇总信息（Summary Result）。
    

    这是批处理完成后的返回值，封装了所有输出信息和统计数据。
    使用 dataclass（非 frozen）允许后续修改，但通常不建议修改返回结果。
    

    属性：

        summary_path: 汇总 CSV 文件的路径
            - 文件格式：sample,method,purity,trace,residual_norm/objective

            - 每行对应一个样本的一种算法的重构结果

            

        records_dir: 详细记录的存储目录
            - 包含每个样本的完整重构结果（JSON 格式）
            - 文件命名：{sample_index}_{method}.json

            

        num_samples: 处理的样本总数

            - 等于输入数据的列数
            
        methods: 实际使用的重构算法列表
            - 已排序和去重的元组
            - 例：("linear", "mle")

            

        rows: 汇总表的原始数据（列表形式）
            - 每个元素是一个字典，包含：
              * sample: 样本索引

              * method: 算法名称

              * purity: 纯度 Tr(ρ²)

              * trace: 迹 Tr(ρ)

              * residual_norm (linear) 或 objective (mle): 算法特定指标

    

    使用示例：
        >>> result = controller.run_batch(config)

        >>> print(f"处理了{result.num_samples} 个样本")

        >>> df = result.to_dataframe()

        >>> print(df[df['method'] == 'mle']['purity'].mean())  # MLE 平均纯度

    """



    summary_path: Path            # CSV 汇总文件路径
    records_dir: Path             # JSON 详细记录目录

    num_samples: int              # 样本总数

    methods: Tuple[str, ...]      # 使用的算法（元组，不可变）
    rows: List[dict]              # 汇总表原始数据（列表，可变）


    def to_dataframe(self) -> pd.DataFrame:

        """将汇总数据转换为 pandas DataFrame。
        

        返回：
            pd.DataFrame: 包含所有样本所有算法结果的数据表
                - 列：sample, method, purity, trace, [residual_norm/objective]

                - 行数：num_samples × len(methods)

        

        使用示例：
            >>> df = result.to_dataframe()

            >>> df.groupby('method')['purity'].describe()  # 按算法分组统计
            >>> df.to_excel('summary.xlsx', index=False)   # 导出到 Excel

        """

        return pd.DataFrame(self.rows)



@dataclass(frozen=True)
class ProgressEvent:
    """封装批处理进度信息，供 GUI 或 CLI 显示使用。"""

    stage: str
    total_samples: int
    sample_index: Optional[int] = None
    method: Optional[str] = None
    message: str = ""
    completed_steps: int = 0
    total_steps: int = 0

    @property
    def fraction(self) -> float:
        """返回整体进度百分比（0.0 ~ 1.0）。"""
        if self.total_steps <= 0:
            return 0.0
        return min(max(self.completed_steps / self.total_steps, 0.0), 1.0)



class ReconstructionController:

    """重构工作流的协调器（Reconstruction Workflow Coordinator）。
    

    这是应用层的核心类，负责编排整个批处理流程：

        1. 加载和验证输入数据
        2. 实例化重构算法（Linear、MLE）
        3. 遍历所有样本执行重构
        4. 持久化结果到 JSON 文件

        5. 生成汇总 CSV 报告

    

    设计原则：
        - 单一职责：只负责流程编排，不实现具体算法

        - 依赖倒置：依赖抽象接口（duck typing），不依赖具体实现
        - 开闭原则：新增重构算法无需修改此类（只需修改 _ALLOWED_METHODS）
    

    使用场景：
        - 批量处理多个量子态样本
        - 对比不同重构算法的效果
        - 自动化实验数据处理流水线

    

    使用示例：
        >>> controller = ReconstructionController()

        >>> config = ReconstructionConfig(

        ...     input_path="data.csv",

        ...     output_dir="output/",

        ...     methods=["linear", "mle"],

        ...     dimension=4,

        ... )

        >>> result = controller.run_batch(config)

        >>> print(f"完成 {result.num_samples} 个样本的重构")

    """

    def __init__(
        self,
        *,
        progress_callback: Optional[Callable[[ProgressEvent], None]] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """
        初始化控制器。

        参数：
            progress_callback: 默认的进度回调函数，可在 run_batch 时覆盖。
            logger: 可选的日志记录器，未提供时使用模块级 logger。
        """

        self._progress_callback = progress_callback
        self._logger = logger or logging.getLogger(__name__)

    def set_progress_callback(self, callback: Optional[Callable[[ProgressEvent], None]]) -> None:
        """动态设置（或清除）默认的进度回调。"""

        self._progress_callback = callback

    # -- 内部工具 -----------------------------------------------------
    def _emit_progress(
        self,
        callback: Optional[Callable[[ProgressEvent], None]],
        *,
        stage: str,
        total_samples: int,
        sample_index: Optional[int] = None,
        method: Optional[str] = None,
        message: str = "",
        completed_steps: int = 0,
        total_steps: int = 0,
    ) -> None:
        """调用进度回调，自动捕获并记录异常。"""

        cb = callback or self._progress_callback
        if cb is None:
            return

        event = ProgressEvent(
            stage=stage,
            total_samples=total_samples,
            sample_index=sample_index,
            method=method,
            message=message,
            completed_steps=completed_steps,
            total_steps=total_steps,
        )
        try:
            cb(event)
        except Exception:
            self._logger.exception("Progress callback raised an exception.")

    def _check_cancellation(
        self,
        cancel_event: Optional[Event],
        *,
        stage: str,
        total_samples: int,
        sample_index: Optional[int] = None,
        completed_steps: int = 0,
        total_steps: int = 0,
    ) -> None:
        """检测取消信号，若已取消则抛出自定义异常。"""

        if cancel_event is not None and cancel_event.is_set():
            self._logger.info(
                "Batch reconstruction cancelled at stage '%s' (sample=%s).",
                stage,
                sample_index if sample_index is not None else "-",
            )
            raise ReconstructionCancelled(
                stage,
                sample_index=sample_index,
                total_samples=total_samples,
                completed_steps=completed_steps,
                total_steps=total_steps,
            )

    def run_batch(
        self,
        config: ReconstructionConfig,
        *,
        repo_factory: Optional[Callable[[Path], IResultRepository]] = None,
        progress_callback: Optional[Callable[[ProgressEvent], None]] = None,
        cancel_event: Optional[Event] = None,
    ) -> SummaryResult:

        """执行批量重构任务（核心方法）。
        

        这是整个控制器的核心方法，协调完整的批处理流程。
        

        参数：
            config: 重构配置对象（ReconstructionConfig）
            repo_factory: 可选的持久化仓库工厂，便于在 GUI/测试中注入自定义实现
            progress_callback: 单次调用期望的进度回调，会覆盖控制器默认回调
            cancel_event: 线程事件，用于在长耗时任务中取消执行
        

        返回：
            SummaryResult: 包含所有输出路径和统计信息的汇总结果
        

        处理流程：
            [1] 准备阶段：
                - 验证配置并创建输出目录
                - 加载测量概率数据（CSV/Excel）
                - 推断或验证系统维度
            
            [2] 初始化阶段：
                - 创建结果存储目录和仓库对象（JSON 持久化）
                - 根据 config.methods 实例化重构器
                  * Linear: 线性最小二乘/Tikhonov 正则化
                  * MLE: 最大似然估计 + L-BFGS-B 优化
            

            [3] 批处理阶段（遍历所有样本）：
                - 对每个样本：
                  a) 执行线性重构（如果启用）
                  b) 使用线性结果作为 MLE 初始值（如果同时启用）
                  c) 执行  重构（如果启用）

                  d) 将每个结果保存为独立的 JSON 文件

                  e) 提取关键指标到汇总表

            

            [4] 汇总阶段：

                - 将所有指标写入 summary.csv

                - 返回 SummaryResult 对象

        

        重要特性：

            - **智能初始化**：MLE 会自动使用线性结果作为初始点（提高收敛速度）
            - **投影算子缓存**：同一 dimension 的投影算子只计算一次
            - **容错设计**：即使单个样本失败，其他样本仍会继续处理
            - **元数据追溯**：每个结果都记录源文件和样本索引

        

        抛出：
            ValueError: 如果输入数据格式错误或维度不匹配

            FileNotFoundError: 如果输入文件不存在
            IOError: 如果输出目录无法创建

        

        使用示例：
            >>> controller = ReconstructionController()

            >>> config = ReconstructionConfig(

            ...     input_path="measurements.csv",

            ...     output_dir="results/",

            ...     methods=["linear", "mle"],

            ...     dimension=4,

            ... )

            >>> result = controller.run_batch(config)

            >>> print(f"完成 {result.num_samples} 个样本")

            >>> df = result.to_dataframe()

            >>> print(df.groupby('method')['purity'].mean())

        """

        progress_cb = progress_callback or self._progress_callback
        self._logger.info(
            "Starting batch reconstruction for input '%s' with methods %s.",
            config.input_path,
            tuple(config.methods),
        )
        total_steps = 0
        completed_steps = 0
        sample_count = 0

        try:
            # ========== [1] 准备阶段 ==========
    
            # 验证配置并创建输出目录
            config = self._prepare_config(config)
            
            
            # 加载输入数据（shape: [num_probabilities, num_samples]）
            data = _load_probabilities(config.input_path, config.sheet)
            
            
            # 推断或验证系统维度（行数必须是 dimension²）
            dimension = config.dimension or _infer_dimension(data.shape[0])
            sample_count = data.shape[1]  # 输入数据的列数 = 样本数量

            # Pre-check: per-group normalization using ProjectorSet.groups (counts or per-group probs)
            try:
                projector = ProjectorSet.get(dimension, design=config.design)
                groups = getattr(projector, "groups", None)
                if groups is not None and groups.size == data.shape[0]:
                    tol = getattr(config, "tolerance", 1e-12)
                    arr = data.astype(float).copy()
                    for g in np.unique(groups):
                        idx = np.where(groups == g)[0]
                        sums = np.sum(arr[idx, :], axis=0)
                        if np.any(np.isclose(sums, 0.0, atol=tol)):
                            raise ValueError("Found zero group-sum in some samples; cannot normalize.")
                        arr[idx, :] = arr[idx, :] / sums
                    data = arr
            except Exception:
                # Fallback: algorithms handle normalization internally if needed
                pass    
    
    
            # ========== [2] 初始化阶段 ==========
    
            # 创建结果存储目录和仓库对象
            records_dir = config.output_dir / "records"
    
            records_dir.mkdir(parents=True, exist_ok=True)
    
            # 面向端口 + 依赖注入：默认适配器为 JSON 实现
            def _default_repo_factory(root: Path) -> IResultRepository:
                return ResultRepository(root, fmt="json")
    
            repo_factory = repo_factory or _default_repo_factory
            repo: IResultRepository = repo_factory(records_dir)
    
    
    
            # 用于收集汇总表数据（每行对应一个样本的一种算法）
            summary_rows: List[dict] = []
    
    
    
            # 根据配置实例化线性重构器（可选）
            linear: Optional[LinearReconstructor] = None
    
            if "linear" in config.methods:
    
                linear = LinearReconstructor(
                    dimension,
    
                    tolerance=config.tolerance,
    
                    regularization=config.linear_regularization,
    
                    cache_projectors=config.cache_projectors,  # 批处理推荐 True
                    design=getattr(config, "design", "mub"),
    
                )
    
    
    
            # 根据配置实例化 WLS 重构器（可选）
            wls: Optional[WLSReconstructor] = None

            if "wls" in config.methods:

                wls = WLSReconstructor(
                    dimension,
    
                    tolerance=config.tolerance,
    
                    regularization=config.wls_regularization,

                    max_iterations=config.wls_max_iterations,
    
                    cache_projectors=config.cache_projectors,  # 批处理推荐 True
                    design=getattr(config, "design", "mub"),
    
                )
    
    
    
            # 根据配置实例化 RρR Strict 重构器（可选）
            rhor: Optional[RrhoStrictReconstructor] = None

            if "rhor" in config.methods:
                rhor = RrhoStrictReconstructor(
                    dimension,
                    design=getattr(config, "design", "mub"),
                    tolerance=config.tolerance,
                    max_iterations=getattr(config, "rhor_max_iterations", 5000),
                    tol_state=getattr(config, "rhor_tol_state", 1e-8),
                    tol_ll=getattr(config, "rhor_tol_ll", 1e-9),
                    cache_projectors=config.cache_projectors,
                )

            enabled_method_count = int(linear is not None) + int(wls is not None) + int(rhor is not None)
            if enabled_method_count == 0:
                enabled_method_count = 1
            total_steps = max(1, sample_count * enabled_method_count)
    
            self._logger.debug(
                "Batch prepared: %s samples, enabled methods=%s.",
                sample_count,
                tuple(
                    method
                    for method, enabled in (
                        ("linear", linear is not None),
                        ("wls", wls is not None),
                        ("rhor", rhor is not None),
                    )
                    if enabled
                ),
            )
            self._emit_progress(
                progress_cb,
                stage="prepare",
                total_samples=sample_count,
                message=f"准备完成，共 {sample_count} 个样本。",
                completed_steps=completed_steps,
                total_steps=total_steps,
            )
            self._check_cancellation(
                cancel_event,
                stage="prepare",
                total_samples=sample_count,
                completed_steps=completed_steps,
                total_steps=total_steps,
            )
    
    
    
            # ========== [3] 批处理阶段 ==========
            for idx in range(sample_count):
    
                self._check_cancellation(
                    cancel_event,
                    stage="sample",
                    total_samples=sample_count,
                    sample_index=idx,
                    completed_steps=completed_steps,
                    total_steps=total_steps,
                )
                self._emit_progress(
                    progress_cb,
                    stage="sample",
                    total_samples=sample_count,
                    sample_index=idx,
                    message=f"处理样本 {idx + 1}/{sample_count}",
                    completed_steps=completed_steps,
                    total_steps=total_steps,
                )
                self._logger.debug("Processing sample %s/%s.", idx + 1, sample_count)
    
                # 提取当前样本的概率向量（长度 = dimension²）
                probs = data[:, idx]
                
                
    
                # 创建元数据（用于结果追溯）
                metadata = {
                    "source_file": config.input_path.name,
                    "sample_index": idx,
                    "design": getattr(config, "design", "mub"),
                }
    
    
    
                # ----- [3.1] 线性重构（如果启用）-----
    
                linear_result = None
    
                if linear is not None:
    
                    # 执行线性重构（最小二乘或 Tikhonov 正则化）
                    linear_result = linear.reconstruct_with_details(probs)
                    
                    
    
                    # 创建持久化记录（包含密度矩阵、指标、元数据）
                    # 📝 阶段 3.1: 扩展指标字段
                    record = _create_record(
    
                        method="linear",
    
                        dimension=dimension,
    
                        probabilities=linear_result.normalized_probabilities,  # 归一化后的概率
                        density_matrix=linear_result.density.matrix,           # 重构的密度矩阵
                        metrics={
    
                            # 原有字段
                            "purity": linear_result.density.purity,             # 纯度 Tr(ρ²)
                            "trace": float(np.real(linear_result.density.trace)),  # 迹 Tr(ρ)（应接近 1）
                            "residual_norm": float(np.linalg.norm(linear_result.residuals))  # 残差范数 ||Ax-b||
    
                            if linear_result.residuals.size
    
                            else 0.0,
    
                            # 📝 P1 新增字段（阶段 3.1）
                            "rank": linear_result.rank,                         # 矩阵秩
                            "min_eigenvalue": float(np.min(linear_result.density.eigenvalues)),  # 最小特征值
                            "max_eigenvalue": float(np.max(linear_result.density.eigenvalues)),  # 最大特征值
                            # 📝 P2 新增字段（阶段 3.1）
                            "condition_number": condition_number(linear_result.singular_values),  # 条件数
                            "eigenvalue_entropy": eigenvalue_entropy(linear_result.density.eigenvalues),  # 特征值熵
    
                        },
    
                        metadata=metadata,
    
                    )
    
                    
                    
                    bell_metrics = None
    
                    if config.analyze_bell:
    
                        try:
    
                            bell_result = analyze_density_matrix(
    
                                linear_result.density, dimension=dimension
    
                            )
    
                            bell_metrics = bell_result.to_dict()
    
                            record.metrics.update({
    
                                f"bell_{key}": value
    
                                for key, value in bell_metrics.items()
    
                                if key not in {"dimension", "local_dimension"}
    
                            })
    
                            record.metrics["bell_dimension"] = bell_metrics["dimension"]
    
                            record.metrics["bell_local_dimension"] = bell_metrics["local_dimension"]
    
                        except ValueError:
    
                            bell_metrics = None
    
    
    
                    # 保存到 JSON 文件（例：records/0_linear.json）
                    repo.save(record)
                    
                    
    
                    # 添加到汇总表（用于生成 summary.csv）
                    # 📝 阶段 3.1 P1/P0: 扩展字段 + 确保从 record.metrics 读取（同步）
                    summary_entry = {

                        "sample": idx,

                        "method": "linear",
                        "design": getattr(config, "design", "mub"),
    
                        # 原有字段（从 record.metrics 读取）
                        "purity": record.metrics["purity"],
    
                        "trace": record.metrics["trace"],
    
                        "residual_norm": record.metrics.get("residual_norm", 0.0),
    
                        # 📝 P1 新增字段（阶段 3.1）
                        "rank": record.metrics["rank"],
    
                        "min_eigenvalue": record.metrics["min_eigenvalue"],
    
                        "max_eigenvalue": record.metrics["max_eigenvalue"],
    
                        # 📝 P2 新增字段（阶段 3.1）
                        "condition_number": record.metrics["condition_number"],
    
                        "eigenvalue_entropy": record.metrics["eigenvalue_entropy"],
    
                    }
    
                    if bell_metrics:
    
                        summary_entry.update({
    
                            f"bell_{key}": value
    
                            for key, value in bell_metrics.items()
    
                            if key not in {"dimension", "local_dimension"}
    
                        })
    
                        summary_entry["bell_dimension"] = bell_metrics["dimension"]
    
                        summary_entry["bell_local_dimension"] = bell_metrics["local_dimension"]
    
                    summary_rows.append(summary_entry)
    
                    completed_steps += 1
                    self._emit_progress(
                        progress_cb,
                        stage="linear",
                        total_samples=sample_count,
                        sample_index=idx,
                        method="linear",
                        message=f"线性重构完成 {idx + 1}/{sample_count}",
                        completed_steps=completed_steps,
                        total_steps=total_steps,
                    )
                    self._check_cancellation(
                        cancel_event,
                        stage="linear",
                        total_samples=sample_count,
                        sample_index=idx,
                        completed_steps=completed_steps,
                        total_steps=total_steps,
                    )
    
    
    
                # ----- [3.2] WLS 重构（如果启用） -----

                if wls is not None:
    
                    # 智能初始化：如果线性结果存在，用作 MLE 的初始点（加速收敛）
                    initial_density = (
    
                        linear_result.density.matrix if linear_result is not None else None
    
                    )
                    
                    
    
                    # 执行 WLS 重构（迭代优化，保证正定性）
                    self._check_cancellation(
                        cancel_event,
                        stage="wls",
                        total_samples=sample_count,
                        sample_index=idx,
                        completed_steps=completed_steps,
                        total_steps=total_steps,
                    )
                    self._logger.debug("Running WLS for sample %s/%s.", idx + 1, sample_count)
                    wls_result = wls.reconstruct_with_details(
    
                        probs,
    
                        initial_density=initial_density,  # 初始猜测（None 则用单位矩阵）
    
                    )
    
                    
    
                    # 创建持久化记录
                    # 📝 阶段 3.1: 扩展指标字段
                    record = _create_record(

                        method="wls",

                        dimension=dimension,

                        probabilities=wls_result.normalized_probabilities,  # 归一化后的概率
                        density_matrix=wls_result.density.matrix,           # 重构的密度矩阵
                        metrics={
    
                            # 原有字段
                            "purity": wls_result.density.purity,             # 纯度 Tr(ρ²)
                            "trace": float(np.real(wls_result.density.trace)),  # 迹 Tr(ρ)
                            "objective": wls_result.objective_value,         # 目标函数值（χ²）
                            # 📝 P1 新增字段（阶段 3.1）
                            "n_iterations": wls_result.n_iterations,         # 优化器迭代次数
                            "n_evaluations": wls_result.n_function_evaluations,  # 函数评估次数

                            "success": wls_result.success,                   # 优化是否成功

                            "status": wls_result.status,                     # 优化器状态码

                            "min_eigenvalue": float(np.min(wls_result.density.eigenvalues)),  # 最小特征值
                            "max_eigenvalue": float(np.max(wls_result.density.eigenvalues)),  # 最大特征值
                            # 📝 P2 新增字段（阶段 3.1）
                            "eigenvalue_entropy": eigenvalue_entropy(wls_result.density.eigenvalues),  # 特征值熵
    
                        },
    
                        metadata=metadata,
    
                    )
    
                    
                    
                    bell_metrics_mle = None
    
                    if config.analyze_bell:
    
                        try:
    
                            bell_result = analyze_density_matrix(

                                wls_result.density, dimension=dimension

                            )
    
                            bell_metrics_mle = bell_result.to_dict()
    
                            record.metrics.update({
    
                                f"bell_{key}": value
    
                                for key, value in bell_metrics_mle.items()
    
                                if key not in {"dimension", "local_dimension"}
    
                            })
    
                            record.metrics["bell_dimension"] = bell_metrics_mle["dimension"]
    
                            record.metrics["bell_local_dimension"] = bell_metrics_mle["local_dimension"]
    
                        except ValueError:
    
                            bell_metrics_mle = None
    
    
    
                    # 保存到 JSON 文件（例：records/0_wls.json）
                    repo.save(record)
                    
                    
    
                    # 添加到汇总表
                    # 📝 阶段 3.1 P1/P0: 扩展字段 + 确保从 record.metrics 读取（同步）
                    summary_entry = {

                        "sample": idx,

                        "method": "wls",
                        "design": getattr(config, "design", "mub"),
    
                        # 原有字段（从 record.metrics 读取）
                        "purity": record.metrics["purity"],
    
                        "trace": record.metrics["trace"],
    
                        "objective": record.metrics["objective"],
    
                        # 📝 P1 新增字段（阶段 3.1）
                        "n_iterations": record.metrics["n_iterations"],
    
                        "n_evaluations": record.metrics["n_evaluations"],
    
                        "success": record.metrics["success"],
    
                        "status": record.metrics["status"],
    
                        "min_eigenvalue": record.metrics["min_eigenvalue"],
    
                        "max_eigenvalue": record.metrics["max_eigenvalue"],
    
                        # 📝 P2 新增字段（阶段 3.1）
                        "eigenvalue_entropy": record.metrics["eigenvalue_entropy"],
    
                    }
    
                    if bell_metrics_mle:
    
                        summary_entry.update({
    
                            f"bell_{key}": value
    
                            for key, value in bell_metrics_mle.items()
    
                            if key not in {"dimension", "local_dimension"}
    
                        })
    
                        summary_entry["bell_dimension"] = bell_metrics_mle["dimension"]
    
                        summary_entry["bell_local_dimension"] = bell_metrics_mle["local_dimension"]
    
                    summary_rows.append(summary_entry)
    
                    completed_steps += 1
                    self._emit_progress(
                        progress_cb,
                        stage="wls",
                        total_samples=sample_count,
                        sample_index=idx,
                        method="wls",
                        message=f"WLS 重构完成 {idx + 1}/{sample_count}",
                        completed_steps=completed_steps,
                        total_steps=total_steps,
                    )
                    self._check_cancellation(
                        cancel_event,
                        stage="wls",
                        total_samples=sample_count,
                        sample_index=idx,
                        completed_steps=completed_steps,
                        total_steps=total_steps,
                    )
    
    
                # ----- [3.3] RρR Strict 重构（如果启用） -----

                if rhor is not None:
                    self._check_cancellation(
                        cancel_event,
                        stage="rhor",
                        total_samples=sample_count,
                        sample_index=idx,
                        completed_steps=completed_steps,
                        total_steps=total_steps,
                    )
                    self._logger.debug("Running RρR Strict for sample %s/%s.", idx + 1, sample_count)
                    rhor_result = rhor.reconstruct_with_details(probs)

                    # 创建持久化记录
                    record = _create_record(
                        method="rhor",
                        dimension=dimension,
                        probabilities=rhor_result.expected_probabilities,
                        density_matrix=rhor_result.density.matrix,
                        metrics={
                            "purity": rhor_result.density.purity,
                            "trace": float(np.real(rhor_result.density.trace)),
                            "log_likelihood": rhor_result.log_likelihood,
                            "iterations": rhor_result.iterations,
                            "converged": rhor_result.converged,
                            "min_eigenvalue": float(np.min(rhor_result.density.eigenvalues)),
                            "max_eigenvalue": float(np.max(rhor_result.density.eigenvalues)),
                            "eigenvalue_entropy": eigenvalue_entropy(rhor_result.density.eigenvalues),
                            "support_dim": rhor_result.diagnostics.get("support_dim", -1),
                        },
                        metadata=metadata,
                    )

                    # Bell 态分析（如果启用）
                    bell_metrics_rhor = None
                    if config.analyze_bell and dimension == 4:
                        try:
                            bell_result = analyze_density_matrix(
                                rhor_result.density,
                                dimension=dimension,
                            )
    
                            bell_metrics_rhor = bell_result.to_dict()
    
                            record.metrics.update({
    
                                f"bell_{key}": value
    
                                for key, value in bell_metrics_rhor.items()
    
                                if key not in {"dimension", "local_dimension"}
    
                            })
    
                            record.metrics["bell_dimension"] = bell_metrics_rhor["dimension"]
                            record.metrics["bell_local_dimension"] = bell_metrics_rhor["local_dimension"]
                        except Exception:
                            bell_metrics_rhor = None

                    # 保存到 JSON 文件
                    repo.save(record)

                    # 添加到汇总表
                    summary_entry = {
                        "sample": idx,
                        "method": "rhor",
                        "design": getattr(config, "design", "mub"),
                        "purity": record.metrics["purity"],
                        "trace": record.metrics["trace"],
                        "log_likelihood": record.metrics["log_likelihood"],
                        "iterations": record.metrics["iterations"],
                        "converged": record.metrics["converged"],
                        "min_eigenvalue": record.metrics["min_eigenvalue"],
                        "max_eigenvalue": record.metrics["max_eigenvalue"],
                        "eigenvalue_entropy": record.metrics["eigenvalue_entropy"],
                        "support_dim": record.metrics["support_dim"],
                    }

                    if bell_metrics_rhor:
                        summary_entry.update({
                            f"bell_{key}": value
                            for key, value in bell_metrics_rhor.items()
                            if key not in {"dimension", "local_dimension"}
                        })
                        summary_entry["bell_dimension"] = bell_metrics_rhor["dimension"]
                        summary_entry["bell_local_dimension"] = bell_metrics_rhor["local_dimension"]
                    summary_rows.append(summary_entry)

                    completed_steps += 1
                    self._emit_progress(
                        progress_cb,
                        stage="rhor",
                        total_samples=sample_count,
                        sample_index=idx,
                        method="rhor",
                        message=f"RρR Strict 重构完成 {idx + 1}/{sample_count}",
                        completed_steps=completed_steps,
                        total_steps=total_steps,
                    )
                    self._check_cancellation(
                        cancel_event,
                        stage="rhor",
                        total_samples=sample_count,
                        sample_index=idx,
                        completed_steps=completed_steps,
                        total_steps=total_steps,
                    )
    
    
    
            # ========== [4] 汇总阶段 ==========
    
            self._emit_progress(
                progress_cb,
                stage="aggregate",
                total_samples=sample_count,
                message="正在生成汇总报告...",
                completed_steps=completed_steps,
                total_steps=total_steps,
            )
            self._check_cancellation(
                cancel_event,
                stage="aggregate",
                total_samples=sample_count,
                completed_steps=completed_steps,
                total_steps=total_steps,
            )
    
            # 生成 CSV 汇总表（包含所有样本所有算法的关键指标）
            summary_path = config.output_dir / "summary.csv"
    
            if summary_rows:
    
                df = pd.DataFrame(summary_rows)
                
                
    
                # 📝 P0: 显式定义列顺序（阶段 3.1 - 审查反馈）
                standard_columns = [
    
                    # 通用字段
                    "sample", "method", "purity", "trace",
    
                    # Linear 专属
                    "residual_norm", "rank",
    
                    # MLE 专属
                    "objective", "n_iterations", "n_evaluations", "success", "status",
    
                    # 通用扩展字段
                    "min_eigenvalue", "max_eigenvalue",
    
                    # 📝 P2 字段（阶段 3.1）
                    "condition_number", "eigenvalue_entropy",
    
                ]
                
                
    
                # 保留已存在的列 + Bell 分析列（动态）
                available_cols = [c for c in standard_columns if c in df.columns]
    
                bell_cols = [c for c in df.columns if c.startswith("bell_") and c not in available_cols]
    
                ordered_cols = available_cols + bell_cols
                
                
    
                # 按固定顺序保存
                df[ordered_cols].to_csv(summary_path, index=False)
    
            else:
    
                # 如果没有任何结果（例如空输入），创建空 CSV（带表头）
                summary_path.write_text("sample,method,purity,trace\n", encoding="utf-8")
    
    
    
            completed_steps = max(completed_steps, total_steps)
            self._emit_progress(
                progress_cb,
                stage="complete",
                total_samples=sample_count,
                message="批处理完成。",
                completed_steps=completed_steps,
                total_steps=total_steps,
            )
            self._logger.info(
                "Batch reconstruction completed. Summary CSV written to '%s'.",
                summary_path,
            )
    
            # 返回汇总结果对象
            return SummaryResult(
    
                summary_path=summary_path,
    
                records_dir=records_dir,
    
                num_samples=sample_count,
    
                methods=tuple(config.methods),
    
                rows=summary_rows,
    
            )
    
    
    
        except ReconstructionCancelled as exc:
            self._emit_progress(
                progress_cb,
                stage="cancelled",
                total_samples=sample_count,
                message=str(exc),
                completed_steps=completed_steps,
                total_steps=total_steps or 1,
            )
            self._logger.info("Batch reconstruction cancelled: %s", exc)
            raise
        except Exception as exc:
            fallback_total = total_steps or max(sample_count, 1) or 1
            self._emit_progress(
                progress_cb,
                stage="failed",
                total_samples=sample_count,
                message=f"Batch reconstruction failed: {exc}",
                completed_steps=completed_steps,
                total_steps=fallback_total,
            )
            self._logger.exception("Batch reconstruction failed.")
            raise ReconstructionError("Batch reconstruction failed; see logs for details.") from exc

    def run_batch_async(
        self,
        config: ReconstructionConfig,
        *,
        repo_factory: Optional[Callable[[Path], IResultRepository]] = None,
        progress_callback: Optional[Callable[[ProgressEvent], None]] = None,
        cancel_event: Optional[Event] = None,
        executor: Optional[Executor] = None,
    ) -> Future:
        """
        以后台线程的方式执行批处理，返回 Future 对象。

        当未显式提供 executor 时，将临时创建一个单线程 ThreadPoolExecutor，
        并在任务结束后自动关闭。
        """

        exec_to_use = executor or ThreadPoolExecutor(max_workers=1, thread_name_prefix="qtomo-batch")
        owns_executor = executor is None

        future = exec_to_use.submit(
            self.run_batch,
            config,
            repo_factory=repo_factory,
            progress_callback=progress_callback,
            cancel_event=cancel_event,
        )

        if owns_executor:

            def _cleanup(_f: Future) -> None:
                exec_to_use.shutdown(wait=False)

            future.add_done_callback(_cleanup)

        return future

    @staticmethod
    def _prepare_config(config: ReconstructionConfig) -> ReconstructionConfig:

        """准备配置（验证并创建输出目录）。
        

        参数：
            config: 重构配置对象

        

        返回：
            ReconstructionConfig: 相同的配置对象（副作用：创建目录）
        

        副作用：
            - 创建 output_dir 目录（如果不存在）
            - 创建所有必要的父目录（parents=True）
        """

        output_dir = config.output_dir

        output_dir.mkdir(parents=True, exist_ok=True)  # 创建输出目录及所有父目录

        return config




# ============================================================
# 模块级便利函数
# ============================================================



def run_batch(config: ReconstructionConfig, *, repo_factory: Optional[Callable[[Path], IResultRepository]] = None) -> SummaryResult:

    """批量重构的便利函数（无需手动实例化 Controller）。
    

    这是一个模块级函数，内部创建 ReconstructionController 并调用其 run_batch 方法。
    适合单次使用的场景，无需手动管理 Controller 生命周期。
    

    参数：
        config: 重构配置对象

    

    返回：
        SummaryResult: 包含所有输出路径和统计信息的汇总结果
    

    使用示例：
        >>> from qtomography.app.controller import ReconstructionConfig, run_batch

        >>> config = ReconstructionConfig(

        ...     input_path="data.csv",

        ...     output_dir="output/",

        ...     methods=["linear", "mle"],

        ... )

        >>> result = run_batch(config)  # 直接调用，无需创建 Controller

    """

    controller = ReconstructionController()

    return controller.run_batch(config, repo_factory=repo_factory)




# ============================================================
# 私有辅助函数
# ============================================================



def _normalize_methods(methods: Sequence[str]) -> Tuple[str, ...]:

    """标准化和验证重构方法列表。
    

    处理逻辑：
        1. 接受字符串或序列（例："wls" 或 ["linear", "wls"]）
        2. 将"both"自动展开为["linear", "wls"]

        3. 验证所有方法名都在 _ALLOWED_METHODS 中
        4. 去重并排序（保证返回值的确定性）
    

    参数：
        methods: 重构方法名或方法名序列
            - 可以是字符串："linear"、"wls"、"both"

            - 可以是列表：["linear"]、"wls"]、["linear", "wls"]

    

    返回：
        Tuple[str, ...]: 已排序和去重的方法名元组
            - 例：("linear", "mle")

    

    抛出：
        ValueError: 如果包含不支持的方法名或方法列表为空
    

    使用示例：
        >>> _normalize_methods("both")

        ('linear', 'wls')

        >>> _normalize_methods(["wls", "linear", "wls"])  # 去重

        ('linear', 'wls')

        >>> _normalize_methods(["invalid"])

        ValueError: Unsupported reconstruction methods: ['invalid']

    """

    # 统一转换为集合（自动去重）
    if isinstance(methods, str):

        tokens = {methods}

    else:

        tokens = {m for m in methods}
    
    
    # 展开 "both" 为所有允许的方法
    if "both" in tokens:

        tokens.discard("both")

        tokens.update(_ALLOWED_METHODS)
    
    
    # 验证所有方法都在允许列表中
    invalid = tokens - _ALLOWED_METHODS

    if invalid:

        raise ValueError(f"Unsupported reconstruction methods: {sorted(invalid)}")
    
    
    # 确保至少有一个方法
    if not tokens:

        raise ValueError("At least one reconstruction method must be specified")
    
    
    # 返回排序后的元组（确保确定性）
    return tuple(sorted(tokens))




def _load_probabilities(path: Path, sheet: Optional[Union[str, int]]) -> np.ndarray:

    """从 CSV 或 Excel 文件加载测量概率数据。
    

    支持的文件格式：
        - CSV/TXT: .csv、.txt（逗号分隔）
        - Excel: .xlsx、.xls

    

    数据格式要求：
        - 无表头（header=None）
        - 每行表示一个测量基的概率
        - 每列表示一个样本
        - 行数必须是完全平方数（dimension²）
    

    参数：
        path: 输入文件路径（Path 对象）
        sheet: Excel 工作表名称或索引（仅对 Excel 有效）
            - None: 使用第一个工作表

            - str: 工作表名称（例："Sheet1"）
            - int: 工作表索引（0-based）
    

    返回：
        np.ndarray: 概率矩阵
            - shape: [num_measurements, num_samples]

            - dtype: float
    

    抛出：
        ValueError: 如果文件格式不支持
        FileNotFoundError: 如果文件不存在
        pd.errors.ParserError: 如果文件格式错误
    

    使用示例：
        >>> data = _load_probabilities(Path("data.csv"), sheet=None)

        >>> print(data.shape)  # (16, 100) - 16 个测量，100 个样本

    """

    suffix = path.suffix.lower()
    
    
    # 根据文件扩展名选择加载方法
    if suffix in {".xlsx", ".xls"}:

        # Excel 文件：使用 pandas read_excel
        frame = pd.read_excel(path, sheet_name=sheet, header=None)
        
        # 如果返回的是字典（多个工作表），取第一个
        if isinstance(frame, dict):
            frame = list(frame.values())[0]

    elif suffix in {".csv", ".txt"}:

        # CSV/TXT 文件：使用 pandas read_csv
        frame = pd.read_csv(path, header=None)

    else:

        raise ValueError(f"Unsupported input format: {suffix}")
    
    
    # 转换为 numpy 数组（浮点数）
    data = frame.to_numpy(dtype=float)
    
    
    # 处理一维输入（单个样本）：转换为列向量
    if data.ndim == 1:

        data = data.reshape(-1, 1)
    
    
    return data




def _infer_dimension(row_count: int) -> int:
    """Infer Hilbert-space dimension d from measurement row count m.

    Supports m = d^2 (SIC/minimal IC) and m = d(d+1) (MUB).
    """
    root = int(np.sqrt(row_count))
    if root * root == row_count:
        return root
    # try MUB: m = d(d+1)
    disc = 1 + 4 * row_count
    s = int(np.sqrt(disc))
    if s * s == disc:
        d1 = (-1 + s) // 2
        if d1 * (d1 + 1) == row_count and d1 >= 2:
            return int(d1)
    raise ValueError(
        f"Row count {row_count} does not match d^2 or d(d+1); pass dimension explicitly."
    )

def _infer_dimension_general(row_count: int) -> int:
    """Backward alias of _infer_dimension for updated logic."""
    return _infer_dimension(row_count)
def _create_record(

    method: str,

    dimension: int,

    probabilities: np.ndarray,

    density_matrix: np.ndarray,

    metrics: dict,

    metadata: Optional[dict] = None,

) -> ReconstructionRecord:

    """创建重构结果的持久化记录对象。
    

    这是一个工厂函数，将重构结果封装为 ReconstructionRecord 对象。
    用于 JSON 序列化和持久化存储。
    

    参数：
        method: 重构方法名（"linear" 或 "mle"）
        dimension: 量子系统维度

        probabilities: 归一化后的测量概率向量
        density_matrix: 重构的密度矩阵（复数矩阵）
        metrics: 性能指标字典

            - 例：{"purity": 0.98, "trace": 1.0, "residual_norm": 0.02}

        metadata: 可选的元数据（例：{"source_file": "data.csv", "sample_index": 0}）
    

    返回：
        ReconstructionRecord: 可序列化的记录对象
    

    类型转换：
        - metrics 中的所有数值自动转换为 float

        - metadata 中的所有值自动转换为 str

        - numpy 数组保持原样（ReconstructionRecord 会处理序列化）
    

    使用示例：
        >>> record = _create_record(

        ...     method="mle",

        ...     dimension=4,

        ...     probabilities=normalized_probs,

        ...     density_matrix=rho,

        ...     metrics={"purity": 0.99, "trace": 1.0},

        ...     metadata={"source": "experiment_1.csv"},

        ... )

        >>> repo.save(record)  # 保存到 JSON

    """

    return ReconstructionRecord(

        method=method,

        dimension=dimension,

        probabilities=probabilities,

        density_matrix=density_matrix,

        # 确保 metrics 中的数值都是标准 Python float（避免 JSON 序列化问题）
        metrics={str(k): float(v) if isinstance(v, (int, float)) else v for k, v in metrics.items()},

        # 确保 metadata 中的所有值都是字符串
        metadata={str(k): str(v) for k, v in (metadata or {}).items()},

    )











