# 操作系统面试清单（结合 QTomography 项目）

本清单用于演练常见的操作系统类面试题，每个主题都给出：可能的问题、项目中的代码锚点、以及可回顾的《图解系统-暗黑风格-小林coding-v1.0.pdf》页码。

## 1. CPU 与调度基础

- 面试题：项目如何避免耗时任务阻塞界面？请说明使 GUI 保持响应的调度方式。
- 代码锚点：`python/excel_tomography_gui.py:250`（手动 `threading.Thread`）、`python/qtomography/gui/services/controller_runner.py:45`（`run_batch_async` 未来回调）。
- 延伸：对比协作式与抢占式调度（PDF p168），结合项目说明上下文切换的触发场景。

## 2. 线程池与任务取消

- 面试题：讲述一次批量重构提交到线程池的完整生命周期，取消信号如何传递？
- 代码锚点：`python/qtomography/app/controller.py:1315`（临时 `ThreadPoolExecutor` + `Event` 取消通路）。
- 延伸：如果工作线程被 I/O 阻塞会怎样？它与 OS 运行队列的关系（PDF p337、p393）。

## 3. 同步与锁

- 面试题：为什么优化版 LRU 缓存使用 `threading.RLock` 而不是普通 `Lock`？
- 代码锚点：`python/qtomography/infrastructure/cache/optimized_lru.py:29`，`python/qtomography/domain/projectors_optimized.py:36`。
- 延伸：若移除锁会出现哪些竞态？联系缓存一致性（PDF p65-p67）说明原因。

## 4. 内存占用与缓存策略

- 面试题：投影算符缓存如何以内存换性能？操作系统的虚拟内存怎样支撑这一结构？
- 代码锚点：`python/qtomography/domain/projectors_optimized.py:72`（测量矩阵构建）、`optimized_lru.py`。
- 延伸：解释进程/线程切换时的缺页与 TLB 刷新（PDF p137、p456）。

## 5. 用户态与内核态交互

- 面试题：CLI 执行重构时会触发哪些系统调用？
- 代码锚点：`python/qtomography/cli/main.py:197`（通过 `pandas` 与仓库存储访问文件）、`python/qtomography/infrastructure/persistence/result_repository.py:118`。
- 延伸：描述用户态与内核态的边界（PDF p121），并分析 Python GIL 对系统调用并发的影响。

## 6. 进程创建与环境配置

- 面试题：为什么 `run_excel_alignment_tests.py` 在启动 pytest 之前复制并修改 `os.environ`？
- 代码锚点：`python/run_excel_alignment_tests.py:17-30`。
- 延伸：Windows 与 POSIX 环境块继承的差异？缺失 `PYTHONPATH` 的风险是什么？

## 7. 阻塞 I/O 与非阻塞 I/O

- 面试题：比较当前阻塞式子进程方案与事件驱动方案的差异。
- 代码锚点：`python/excel_tomography_cli.py:139`，`python/excel_tomography_gui.py:279`。
- 延伸：概述传统 read/send 的四次拷贝以及零拷贝（`sendfile`）的改进（PDF p377-p384）。何时考虑迁移到 Reactor/Proactor？

## 8. 文件系统语义

- 面试题：`ResultRepository` 如何保证写入的持久性？如果进程中途退出会怎样？
- 代码锚点：`python/qtomography/infrastructure/persistence/result_repository.py:127-175`。
- 延伸：讨论元数据净化与跨平台文件名安全，同时关联磁盘调度开销（PDF p303-p307）。

## 9. 日志与资源清理

- 面试题：GUI 日志的生命周期是什么？为什么必须正确关闭处理器（handler）？
- 代码锚点：`python/qtomography/gui/app.py:38-53`。
- 延伸：文件描述符未关闭会泄漏哪些 OS 资源？联系内核引用计数与缓冲刷新机制。

## 10. 跨平台界面调用

- 面试题：`os.startfile` 与 `xdg-open` 体现了哪些系统集成差异？
- 代码锚点：`python/excel_tomography_gui.py:335-338`。
- 延伸：说明各平台底层系统调用（ShellExecute、xdg）及可能的权限要求。

## 11. 测试与 CI 考量

- 面试题：如何模拟高并发负载验证锁策略？推荐哪些 OS 工具（如 `perf`、Process Explorer）？
- 代码锚点：`python/tests/`（可以编写压测用例触发缓存与线程池）。
- 延伸：测试过程中如何监控上下文切换与 CPU 亲和性（PDF p49-p51）。

## 12. 进阶扩展

- 面试题：如果将线程池替换为多进程处理 CPU 密集任务，会带来哪些 OS 层面的变化？
- 代码锚点：`docs/teach/多进程批处理技术详解.md`（潜在扩展方案）。
- 延伸：讨论 IPC 选择（管道、共享内存）、写时复制语义与进程启动开销。

---

练习建议：
1. 每题准备 60 秒左右的回答，明确点出代码路径与 OS 概念。
2. 面前保持 PDF 页码索引用于快速复习。
3. 每个主题准备一个真实案例（修复的问题、做过的优化、遇到的限制）帮助回答更落地。
