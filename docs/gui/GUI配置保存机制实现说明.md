# GUI配置保存机制实现说明

> **最后更新**: 2025年11月  
> **状态**: ✅ 当前实现

## 📋 概述

本文档说明 **QTomography GUI**（本仓库）的配置保存功能实现机制，采用**分层架构 + 值对象模式 + 仓储模式 + 用例模式**，实现了配置的持久化、验证和UI同步。

> **注意**：本文档描述的是本仓库（`QT_to_Python_1`）中 `python/qtomography/gui/` 目录下的GUI配置保存机制实现。

---

## 🏗️ 架构设计

### 整体架构图

```
┌─────────────────────────────────────────────────┐
│              UI Layer (表示层)                    │
│  MainWindow                                     │
│  - _load_config_to_ui()  (配置 → UI)           │
│  - _save_ui_to_config()  (UI → 配置)           │
│  - 菜单: 保存/加载/另存为/从文件加载              │
└─────────────────────────────────────────────────┘
                    │
                    │ 调用用例
                    ↓
┌─────────────────────────────────────────────────┐
│         Application Layer (应用层)               │
│  GUIConfigUseCase                               │
│  - get_current_config()                        │
│  - update_config()                              │
│  - save_config_to_file()                        │
│  - load_config_from_file()                      │
│  - reset_to_default()                           │
└─────────────────────────────────────────────────┘
                    │
                    │ 调用仓储
                    ↓
┌─────────────────────────────────────────────────┐
│      Infrastructure Layer (基础设施层)          │
│  GUIConfigRepository                            │
│  - save_config()                                │
│  - load_config()                                 │
│  - get_current_config()                         │
│  - save_config_to_file()                        │
│  - load_config_from_file()                      │
└─────────────────────────────────────────────────┘
                    │
                    │ 操作值对象
                    ↓
┌─────────────────────────────────────────────────┐
│          Domain Layer (领域层)                  │
│  GUIConfig (值对象)                              │
│  - SpectralConfig                                │
│  - DataConfig                                    │
│  - ExecuteConfig                                 │
│  - WindowConfig                                  │
│  - to_dict() / from_dict()                      │
│  - with_updates()                                │
└─────────────────────────────────────────────────┘
                    │
                    │ JSON序列化
                    ↓
┌─────────────────────────────────────────────────┐
│            JSON File (配置文件)                  │
│  ~/.qtomography/gui_config.json                │
└─────────────────────────────────────────────────┘
```

---

## 🔑 核心组件

### 1. 值对象（Value Object）- 领域层

**位置**: `gui/domain/gui_config.py`

**职责**: 封装配置数据，提供验证和转换方法

**特点**:
- 使用 `@dataclass(frozen=True)` 定义，**不可变对象**
- 在 `__post_init__()` 中进行参数验证
- 提供工厂方法创建默认配置

**关键类**:

```python
@dataclass(frozen=True)
class SpectralConfig:
    """Spectral decomposition panel configuration."""
    folder_path: str = ""
    output_dir: str = ""
    dimension_hint: str = "自动推断"
    theory_mode: str = "4D_custom"
    # ... 其他字段
    
    def __post_init__(self):
        """验证配置值"""
        if self.dimension_hint not in {"自动推断", "4", "16"}:
            raise ValueError(...)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SpectralConfig:
        """从字典创建"""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
    
    def with_updates(self, **kwargs) -> SpectralConfig:
        """创建更新后的副本（值对象不可变）"""

@dataclass(frozen=True)
class GUIConfig:
    """Complete GUI configuration value object."""
    spectral: SpectralConfig
    data: DataConfig
    execute: ExecuteConfig
    window: WindowConfig
```

**优势**:
- ✅ 数据不可变性，避免意外修改
- ✅ 集中验证逻辑
- ✅ 类型安全

---

### 2. 仓储（Repository）- 基础设施层

**位置**: `gui/infrastructure/repositories/gui_config_repository.py`

**职责**: 管理配置的持久化（文件读写）

**关键方法**:

```python
class GUIConfigRepository:
    """Repository for GUI configuration persistence."""
    
    def __init__(self, config_file_path: Optional[Path] = None):
        # 默认: ~/.qtomography/gui_config.json
    
    def save_config(self, config: GUIConfig) -> bool:
        """保存配置到文件"""
        config_data = config.to_dict()
        with open(self.config_file_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    def load_config(self) -> GUIConfig:
        """从文件加载配置（文件不存在时返回默认值）"""
        if not self.config_file_path.exists():
            return GUIConfig.create_default()
        # ...
    
    def save_config_to_file(self, filepath: Path) -> bool:
        """保存到指定文件（另存为）"""
    
    def load_config_from_file(self, filepath: Path) -> bool:
        """从指定文件加载并保存为默认配置"""
```

**优势**:
- ✅ 统一的数据访问接口
- ✅ 自动处理文件不存在的情况
- ✅ 错误处理和默认值回退

---

### 3. 用例（Use Case）- 应用层

**位置**: `gui/application/use_cases/gui_config_use_case.py`

**职责**: 封装配置管理的业务场景

**关键方法**:

```python
class GUIConfigUseCase:
    """Use case for GUI configuration management."""
    
    def get_current_config(self) -> GUIConfig:
        """获取当前配置"""
    
    def update_config(
        self,
        config_updates: Union[Mapping[str, Any], GUIConfig],
        validate: bool = True,
    ) -> bool:
        """更新配置（支持部分更新和嵌套键）"""
        # 支持 "spectral.dimension_hint" 这样的嵌套键
    
    def save_config_to_file(self, filepath: Path) -> bool:
        """保存配置到指定文件"""
    
    def load_config_from_file(self, filepath: Path) -> bool:
        """从指定文件加载配置"""
    
    def reset_to_default(self) -> bool:
        """重置为默认配置"""
```

**优势**:
- ✅ 支持部分更新（只需传入要修改的字段）
- ✅ 支持嵌套键更新（如 "spectral.dimension_hint"）
- ✅ 业务逻辑封装
- ✅ 支持验证开关

---

### 4. UI层 - 表示层

**位置**: `gui/main_window.py`

**职责**: 用户界面，与用户交互

**关键方法**:

```python
class MainWindow(QMainWindow):
    def __init__(self):
        self._config_use_case = GUIConfigUseCase()
        self._load_config_to_ui()  # 启动时自动加载
    
    def _load_config_to_ui(self):
        """从配置加载到UI（配置 → UI）"""
        config = self._config_use_case.get_current_config()
        self.spectral_panel.load_config(config.spectral.to_dict())
        self.data_panel.load_config(config.data.to_dict())
        # ...
    
    def _save_ui_to_config(self):
        """从UI保存到配置（UI → 配置）"""
        spectral_dict = self.spectral_panel.save_config()
        # ...
        config_updates = {
            "spectral": SpectralConfig.from_dict(spectral_dict).to_dict(),
            # ...
        }
        self._config_use_case.update_config(config_updates)
    
    def _save_config_as_default(self):
        """保存为默认配置（菜单触发）"""
        self._save_ui_to_config()
        # 显示提示消息
    
    def _load_default_config(self):
        """加载默认配置（菜单触发）"""
        self._load_config_to_ui()
    
    def _save_config_as(self):
        """另存配置为...（菜单触发）"""
        filepath = QFileDialog.getSaveFileName(...)
        if filepath:
            self._save_ui_to_config()  # 先保存UI状态到配置
            self._config_use_case.save_config_to_file(Path(filepath))
    
    def _load_config_from_file(self):
        """从文件加载配置（菜单触发）"""
        filepath = QFileDialog.getOpenFileName(...)
        self._config_use_case.load_config_from_file(filepath)
        self._load_config_to_ui()
```

**关键点**:
- ✅ **双向绑定**：`_load_config_to_ui()` 和 `_save_ui_to_config()`
- ✅ **显式保存**：通过菜单按钮触发，用户主动控制
- ✅ **启动时自动加载**：符合用户期望
- ✅ **错误处理**：使用异常处理和用户提示

---

## 🔄 数据流

### 1. 启动时自动加载配置

```
应用启动
    ↓
MainWindow.__init__()
    ↓
self._config_use_case = GUIConfigUseCase()
    ↓
_load_config_to_ui()
    ↓
GUIConfigUseCase.get_current_config()
    ↓
GUIConfigRepository.load_config()
    ↓
读取 ~/.qtomography/gui_config.json
    ↓
GUIConfig.from_dict()
    ↓
设置UI控件值
```

### 2. 用户保存配置

```
用户点击菜单"保存当前配置为默认"
    ↓
_save_config_as_default()
    ↓
_save_ui_to_config()
    ↓
收集UI控件值 → 字典
    ↓
创建值对象 (SpectralConfig.from_dict(), ...)
    ↓
GUIConfigUseCase.update_config()
    ↓
GUIConfigRepository.save_config()
    ↓
GUIConfig.to_dict()
    ↓
写入 ~/.qtomography/gui_config.json
    ↓
显示"配置已保存"提示
```

### 3. 从文件加载配置

```
用户点击菜单"从文件加载配置..."
    ↓
选择JSON文件
    ↓
GUIConfigUseCase.load_config_from_file()
    ↓
GUIConfigRepository.load_config_from_file()
    ↓
读取JSON文件
    ↓
GUIConfig.from_dict()
    ↓
保存为默认配置
    ↓
_load_config_to_ui()
    ↓
更新UI控件
```

---

## 💡 设计模式

### 1. 值对象模式（Value Object Pattern）

**目的**: 封装不可变的配置数据

**实现**:
- 使用 `@dataclass(frozen=True)` 确保不可变性
- 修改时创建新对象（`with_updates()`）

**优势**:
- 避免意外修改
- 线程安全
- 易于测试

### 2. 仓储模式（Repository Pattern）

**目的**: 抽象数据持久化逻辑

**实现**:
- `GUIConfigRepository` 封装文件读写
- UI和应用层不直接操作文件

**优势**:
- 数据访问逻辑集中
- 易于切换存储方式（文件/数据库）
- 易于测试（可Mock）

### 3. 用例模式（Use Case Pattern）

**目的**: 封装业务场景

**实现**:
- `GUIConfigUseCase` 封装配置管理流程
- 支持部分更新、验证等业务逻辑

**优势**:
- 业务逻辑清晰
- 易于扩展
- 可复用

---

## 📝 配置文件格式

### JSON格式示例

```json
{
  "spectral": {
    "folder_path": "D:/data/spectral",
    "output_dir": "D:/output",
    "dimension_hint": "自动推断",
    "theory_mode": "4D_custom",
    "figure_format": "png",
    "save_plots": true,
    "save_reports": true,
    "save_json": false
  },
  "data": {
    "last_file": "D:/data/input.csv"
  },
  "execute": {
    "output_dir": "D:/output"
  },
  "window": {
    "geometry": "base64_encoded_geometry_string",
    "state": "base64_encoded_state_string"
  }
}
```

**特点**:
- 使用UTF-8编码
- 缩进2空格，便于阅读
- 支持中文（`ensure_ascii=False`）

---

## 🎯 功能特性

### 1. 显式保存/加载

- ✅ **保存当前配置为默认**：将当前UI状态保存为默认配置
- ✅ **加载默认配置**：从默认配置文件加载并应用到UI
- ✅ **另存配置为...**：将当前配置保存到指定文件
- ✅ **从文件加载配置...**：从指定文件加载配置并保存为默认
- ✅ **重置为默认配置**：重置所有配置为默认值

### 2. 启动时自动加载

- ✅ 应用启动时自动加载默认配置（如果存在）
- ✅ 自动恢复窗口大小、位置、分割器状态
- ✅ 自动恢复各面板的选项和路径

### 3. 配置验证

- ✅ 值对象在 `__post_init__()` 中验证配置值
- ✅ 无效配置会抛出 `ValueError`
- ✅ 文件损坏时自动回退到默认配置

### 4. 错误处理

- ✅ 文件不存在时返回默认配置
- ✅ 文件损坏时返回默认配置并记录警告
- ✅ 保存失败时显示错误提示
- ✅ 路径不存在时忽略（不报错）

---

## 🔧 技术细节

### QByteArray 转换问题修复

**问题**: PySide6 中 `QByteArray.toBase64()` 返回 `QByteArray`，不是字符串

**解决方案**:
```python
geometry_bytes = self.saveGeometry()
geometry_base64 = geometry_bytes.toBase64()
geometry_str = geometry_base64.data().decode("utf-8", errors="ignore")
```

### 嵌套键更新支持

用例支持嵌套键更新，例如：
```python
config_updates = {
    "spectral.dimension_hint": "4",
    "spectral.theory_mode": "16D_custom",
}
use_case.update_config(config_updates)
```

---

## ✅ 优势总结

### 1. 架构清晰
- 分层明确：UI → 用例 → 仓储 → 值对象
- 职责单一：每层只负责自己的职责

### 2. 易于维护
- 配置验证集中在值对象
- 文件操作集中在仓储
- 业务逻辑集中在用例

### 3. 易于测试
- 值对象可独立测试
- 仓储可Mock测试
- UI可集成测试

### 4. 易于扩展
- 添加新配置字段：只需修改值对象
- 切换存储方式：只需修改仓储
- 添加新功能：只需添加新用例

### 5. 类型安全
- 使用类型注解
- 值对象提供类型检查
- IDE支持更好

### 6. 用户友好
- 显式保存，用户可控
- 启动时自动加载，符合期望
- 支持多配置文件，灵活使用

---

## 📌 关键要点

1. **值对象不可变**：使用 `frozen=True`，修改时创建新对象
2. **双向绑定**：`_load_config_to_ui()` 和 `_save_ui_to_config()`
3. **显式保存**：通过菜单按钮触发，用户主动控制
4. **启动时自动加载**：符合用户期望，提升体验
5. **验证逻辑**：在值对象的 `__post_init__()` 中验证
6. **错误处理**：文件不存在时返回默认值，不中断应用

---

## 🔗 相关文件

- **值对象**: `gui/domain/gui_config.py`
- **仓储**: `gui/infrastructure/repositories/gui_config_repository.py`
- **用例**: `gui/application/use_cases/gui_config_use_case.py`
- **UI层**: `gui/main_window.py`
- **配置文件**: `~/.qtomography/gui_config.json`

---

**文档版本**: v1.1  
**最后更新**: 2025-11-07  
**实现状态**: ✅ 已完成  
**适用仓库**: QTomography GUI (本仓库)

