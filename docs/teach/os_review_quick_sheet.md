# 操作系统知识快速复习（基于 QTomography 项目）

> 目的：用项目中真实的调用场景串联《图解系统-暗黑风格-小林coding-v1.0.pdf》里的核心操作系统知识，面试前快速自检。

## 1. 线程与任务调度

- 代码定位  
  - `python/qtomography/app/controller.py:1315` 使用 `ThreadPoolExecutor` 把批处理放到后台线程，结合取消事件控制执行。  
  - `python/qtomography/gui/services/controller_runner.py:29` 通过 `threading.Event` 协调 Qt 主线程与工作线程。  
  - `python/excel_tomography_gui.py:250` 在 Tk GUI 中手动创建后台线程避免界面阻塞。
- PDF 复习  
  - p337：阻塞 / 非阻塞 I/O 与同步 / 异步 I/O 的差别。  
  - p393-394：多线程模型与线程上下文切换成本。  
  - p168：调度器何时触发上下文切换。
- 自检问题  
  1. 线程池里的线程和 GUI 主线程处于同一进程，为什么仍需要 `Event` 来同步？  
  2. 如果线程任务阻塞在系统调用上（例如 `subprocess.run`），调度器会如何处理？  
  3. 解释一次线程上下文切换保存 / 恢复了哪些现场，结合 p168、p393。

## 2. 线程安全与锁策略

- 代码定位  
  - `python/qtomography/infrastructure/cache/optimized_lru.py:29` 与 `:88` 使用 `threading.RLock` 为 LRU 缓存提供可重入互斥。  
  - `python/qtomography/domain/projectors_optimized.py:36` 通过类级 `RLock` 确保缓存初始化的原子性。  
  - `python/qtomography/gui/services/controller_runner.py:45` 的回调在 Qt 线程中执行，需要考虑信号槽线程安全。
- PDF 复习  
  - p409：互斥锁在多线程 Reactor 框架中的作用。  
  - p411：通过锁避免 `accept` 惊群的示例，理解锁粒度的取舍。  
  - p65-67：缓存一致性与“写传播 + 锁”保证事务串形化。
- 自检问题  
  1. 为什么缓存实现选择 `RLock` 而不是普通 `Lock`？结合项目中递归访问或同线程重入的场景回答。  
  2. 如果去掉 `RLock`，在高并发 `get`/`put` 时可能触发哪些竞态？  
  3. p409 提到的“操作共享队列前加锁”与项目中 `ProjectorLRUCache` 的做法有哪些共通点？  

## 3. I/O 模型与系统调用

- 代码定位  
  - `python/excel_tomography_gui.py:279`、`:348` 与 `python/excel_tomography_cli.py:156` 调用 `subprocess.run` 触发阻塞式系统调用。  
  - `python/run_excel_alignment_tests.py:17` 复制并注入 `PYTHONPATH` 触发子进程加载路径。  
  - `python/qtomography/infrastructure/persistence/result_repository.py:127`、`:145`、`:175` 管理磁盘读写（JSON/CSV）。
- PDF 复习  
  - p377-384：零拷贝、DMA、`sendfile` 在 I/O 路径中的优化作用。  
  - p337：阻塞 I/O 的两个等待阶段。  
  - p406：Reactor 框架中 `accept / read / send` 系统调用的触发时机。
- 自检问题  
  1. GUI 后台线程里直接执行阻塞 `subprocess.run` 是否安全？如何结合 p337 的 I/O 流程理解其行为？  
  2. `ResultRepository` 写 JSON 时为什么要区分 `w`、`a`、`r` 三种模式？与内核缓冲区刷新机制（p303-304）有什么联系？  
  3. 如果改用异步 I/O（参照 p406 Proactor 思路），当前 CLI/GUI 架构需要调整哪些模块？

## 4. 文件系统与数据持久化

- 代码定位  
  - `python/qtomography/infrastructure/persistence/result_repository.py:118` 利用 `Path` 安全拼接路径并筛选文件名。  
  - `python/qtomography/gui/app.py:38` 创建日志目录与文件句柄，体现文件权限与句柄管理。  
  - `python/excel_tomography_gui.py:335` / `:338` 根据平台调用 `os.startfile` 或 `xdg-open` 打开目录，体现不同操作系统的 shell 集成方式。
- PDF 复习  
  - p303-307：磁盘调度算法与磁头寻道成本。  
  - p137：Swap 与页缓存关系，理解为何频繁 I/O 需要关注内存压力。  
  - p90：存储层级（寄存器→缓存→内存→磁盘）的性能差异。
- 自检问题  
  1. `ResultRepository` 在高频写入时如何避免频繁落盘？结合 p303 的磁盘调度思路给出改进点。  
  2. GUI 里打开目录时为何要区分 Windows 与类 Unix？背后的系统调用差异（p121 系统调用章节）。  
  3. 如果日志文件句柄未正确关闭，会占用哪些 OS 资源？与 p90 存储层级的缓存策略如何互相影响？

## 5. 进程与环境管理

- 代码定位  
  - `python/qtomography/cli/main.py:20` 使用 `argparse` 驻留在主进程，结合 `ResultRepository` 与 `run_batch` 构成长时间运行任务。  
  - `python/run_gui.py:9` 通过修改 `sys.path` 在启动脚本中注入模块搜索路径（影响后续子进程继承的环境）。  
  - `python/run_excel_alignment_tests.py:17`-`:30` 设置环境变量并把它传入 `pytest` 子进程。
- PDF 复习  
  - p121：用户态与内核态、系统调用切换流程。  
  - p176：用户级线程在遇到系统调用阻塞时的局限。  
  - p49-51：多进程在多核环境下的调度与缓存命中考量。
- 自检问题  
  1. 为什么在运行 `pytest` 前要复制并修改 `os.environ`？说明环境块在 Windows 子进程中的继承机制。  
  2. 结合 p176，说明如果 `run_batch` 内部未来扩展为多进程，会对当前线程池封装产生哪些影响。  
  3. CLI 进程长时间驻留时，如何监控它的文件描述符与内存占用（关联 p121 的内核资源管理）？

---

### 使用建议

1. 先按章节回顾 PDF 中对应页码，再结合代码阅读，确保每个问题都能联系到具体实现。  
2. 面试前进行口头演练：用项目真实场景回答每个「自检问题」，把抽象概念落在代码细节。  
3. 若发现知识盲区，优先回到 PDF 原文或仓库里的教学文档（如 `docs/teach/多进程批处理技术详解.md`）补充。

