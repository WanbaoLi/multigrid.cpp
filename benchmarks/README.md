# 性能测量和独立验算

这里放需要反复运行的测量程序。测量结果和原始日志写到仓库外的运行目录。

| 子目录 | 用途与入口 |
|---|---|
| `runtime/` | `benchmark_runtime.py` 测真实组态的完整求解；`verify_runtime_columns.py` 用独立参考程序检查12列 |
| `native/` | `bench_native.cpp` 测细层、SAP、粗层等组件，辅助定位瓶颈 |
| `hardware/` | 测实际节点的 SIMD FMA 吞吐和内存带宽 |
| `reference-libraries/` | 与 DDalphaAMG、Grid、openQCD 做可选对照 |

项目的最终性能指标是复用建层后一个源点完整12列的求解时间；组件测量用于
解释瓶颈。日常运行一个传播子使用 `tools/solve_propagator.py`，编译和测试入口
见 `tools/x86/test.md`。
