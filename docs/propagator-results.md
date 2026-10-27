# 完整 LIME 传播子验收（2026-10-23）

本页保留最初8×32配置的验收记录。后续16×16、SIMD和两列批量求解的最新结果、
实际输出文件及perf证据见 [x86优化验收](x86-performance.md)。

从原始 `beta6.20_mu-0.2770_ms-0.2310_L24x64_cfg_20000.lime` 出发，CPU读取、SciDAC校验、一步四维stout(rho=.125)、自研Clover/MG setup和12列点源求解已跑通。原文件不需要先导出HDF5，不调用PyTorch或QUDA进行生产求解。

两套真实配置使用mass=-.277、时间反周期、block6×6×6×4、8 MPI×32线程；默认单位点源，mass归一化 M S=δ，每轮12列均从零初值开始。输出包括完整全局 `propagator.npy` 和物理/性能清单；实际由8个MPI rank的PyQUDA `LatticePropagator.load()` 读回，逐元素精确一致。

| 配置 | csw来源 | stout/s | setup/s | 12列第一轮/s | 第二轮/s | 第三轮/s | 后两轮中位数/s | 独立最大残差 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | explicit | 1.347 | 69.834 | 5.075076 | 5.705666 | 5.485409 | 5.595537 | 3.748e-09 |
| 1.16092023 | lime | 1.347 | 70.637 | 8.874655 | 8.752647 | 9.009644 | 8.881145 | 4.746e-09 |

文件的csw为1.160920226；此前性能fixture显式改用了1，不能混为相同物理算子。csw=1每列17次迭代；文件csw版本每列24–25次，完整传播子仍未达到5秒。求解时间包括12列源构造、公共API/布局转换、可靠更新/完整double残差、传播子轴序整理；不含stout、setup和输出文件。输出本轮约2.7s，单独记录；它不进入第二次求解成绩。

CPU stout与旧QUDA post-stout gauge的相对误差 **5.334654e-16**。csw=1第一列对旧QUDA解，在按单位源幅度换算后相对误差 **1.489045e-07**。两个配置全部12列均由独立scalar C++ operator重算完整残差，不使用生产SIMD核。

新增通用csw接入也在非平凡SU(3) 8⁴格点对照独立GPU QUDA double/no-reconstruct算子：mass=.05/-.277，csw=0/1/1.160920226，mass/kappa两种归一化，共12组，最大相对误差 **3.90e-16**。GPU只生成数值oracle，不参与生产LIME工作流或本表CPU计时。

验证包括：

- node5005 **22/22 CTest**；新增LIME F/D原字节checksum、独立stout stencil/Taylor指数、MPI slab输出/PyQUDA文件契约、完整小格点工作流。原有MPI2/4、EO四组合、SIMD尾部和异步halo测试也通过。
- 小工作流覆盖非原点源 `(3,1,2,5)`、源位于rank1、奇parity、12列各自单位源、mass/kappa输出尺度，以及独立NumPy全残差。
- 当前gpu2025 Intel机器另建 `build/propagator`，core及4个新工作流/IO测试全部通过，没有覆盖旧性能基线。node5005独立build为 `build/node5005-propagator`；两个native编译库不要跨CPU型号混用。
- 真实两配置的标准NumPy传播子均由8rank PyQUDA MPI-IO实际加载，global lexical与local EO轴序/值精确匹配。

使用方法见 [完整传播子流程](propagator.md)。本轮输出保存在：

- `.cache/propagator-20261023/fixture-match/propagator.npy`：与旧benchmark相同csw=1、单位点源。
- `.cache/propagator-20261023/lime-csw/propagator.npy`：文件csw=1.160920226、单位点源。

[机器可读结果与哈希](propagator-results.json) 保存所有36列/配置的统计、三轮样本、独立验算、实际PyQUDA加载结果及源码/库校验。原始日志在 `.cache/propagator-20261023/`。生产CLI默认不smear；本轮通过 `--stout-steps 1` 显式开启，规范场从未重复smear。
