# 真实24³×64 CPU五方求解比较（2026-10-14）

全部在同一双路Xeon Platinum 8458P节点完成，五种实现串行运行。
同一LIME后处理规范场、mass=-0.277、csw=1、时间反周期、一个spin-color点源。
每次零初值，复用setup；只比较第二次纯求解时间。

| 实现 | 算法 | 核数 | 第二次/s | 独立真残差 | 相对优化PyQCU |
|---|---|---:|---:|---:|---:|
| openQCD | deflated SAP-GCR | 72 | 0.624859 | 9.170e-09 | 202.98x |
| DDalphaAMG | 三层AMG + FGMRES | 88 | 1.132391 | 3.836e-09 | 112.00x |
| Grid | 偶奇混合精度BiCGStab/迭代精化 | 88 | 2.154677 | 5.114e-10 | 58.86x |
| PyQCU real/imag + compile BiCGStab | 实虚拆分 + torch.compile + BiCGStab | 88 | 126.830895 | 6.250e-09 | 1.00x |
| multigrid.cpp MG/GCR | MG + full GCR(8) | 88 | 197.983442 | 9.878e-09 | 0.64x |

- DDalphaAMG外迭代11次；openQCD外迭代10次；Grid为4次精化、130次单精度内迭代+12次最终双精度迭代；PyQCU 263次；C++ GCR 461次。不同迭代定义不应直接混算。
- 三个新库完整算子随机场对照误差均小于8e-16；输出解转换回原布局后，由独立multigrid.cpp算子重新计算残差，全部通过1e-8。
- 三个新库与QUDA解的相对差为1.52e-7至1.62e-7；这里QUDA作为数值参考，不参与本轮CPU计时排名。
- openQCD线程数受几何分块限制，24³×64不能整分成88线程，本次采用4 MPI ranks×18线程=72核；DDalphaAMG和Grid均为8×11=88核。
- 所有时间仅对应一列传播子，没有实测完整12列。所有性能比均为当前算法/精度/数据布局组合的整体差异，不是同算法的纯SIMD或语言比较。
- 直接部署本次最快的是openQCD；需要AMG库接口时DDalphaAMG值得优先采用；面向跨ISA SIMD框架，优先评估Grid。目标神威/灵晟尚未实测，需实现或验证专用后端。

原始结果路径：`lqcd/.cache/cpu_libraries/run-11w7BvKI/summary.json`（历史外部运行数据，源码目录不包含）。
独立解互比路径：`lqcd/.cache/cpu_libraries/run-11w7BvKI/solution_checks.json`。
[构建与复现说明](README.md)
[神威/灵晟移植分析及官方资料](portability.md)
