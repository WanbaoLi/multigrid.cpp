# 神威 / 灵晟移植判断

当前实测平台是双路 Intel Xeon Platinum 8458P，并不是神威或灵晟。
此次只验证三个上游CPU库在本机的完整Clover-Wilson反演。
本机的AVX/SSE优化效果不能外推成SW64、SVE或SME上的实测性能。

| 库 | 本次利用的并行/SIMD | 通用路径 | 移植重点 |
|---|---|---|---|
| DDalphaAMG | MPI+OpenMP，SSE内核及本机编译器优化，三层AMG | C语言算法与非SSE实现可作为起点 | 替换SSE算子/转移/粗层核，调整NUMA及通信，保持MG层级和可靠残差 |
| Grid | MPI+OpenMP，AVX512，native assembly Wilson kernel | 明确的SIMD抽象层；GEN、NEON和A64FX/SVE选项 | 灵晟优先评估SVE向量长度/ABI，SME不属于本次已验证后端；神威需添加SW64/CPE执行及数据移动后端 |
| openQCD | MPI+OpenMP，AVX/FMA3手写路径，deflated SAP-GCR | 非x64/AVX的C实现 | 重写关键SIMD算子、SAP和向量核；注意线程几何限制；若需从核卸载，还要重构执行与数据移动 |

选择取决于目标：当前Xeon节点比较中先看实测表；如果建设跨ISA的长期
SIMD基础设施，Grid的后端分层值得优先采用；如果想复用有效的AMG算法和
C接口，DDalphaAMG是合适基线；openQCD可提供成熟的deflation/SAP方案。
这些是基于源码结构的工程判断，并非目标超算已适配的证明。

神威的新一代机器具有MPE/CPE组织和显式局部数据移动需求。仅将C程序在
管理核上编译成功、或替换一组SIMD指令，不能保证利用从核算力；需要针对
具体处理器、编译器及运行时实现从核执行、数据分块与传输。
[神威平台应用开发者的架构与移植论文](https://gmd.copernicus.org/articles/15/5739/2022/)。

深圳超算中心的灵晟介绍提到CPU内生矩阵加速，以及SVE/SME混合调度。
因此后续可重点评估SIMD细格算子与矩阵形式粗层算子的组合，但不能由这些
介绍推断当前Grid或DDalphaAMG已经支持LX2。需要平台SDK、支持的数据类型、
向量长度、编译器和MPI/OpenMP线程能力后再做性能验证。
[深圳超算中心官方介绍](https://nsccsz.cn/nsccsz2024/zxdt2024/202607/62596f1c-27e8-49c6-9f77-6943b1327b82.shtml)。

上游参考：

- [DDalphaAMG CPU源码](https://github.com/etmc/DDalphaAMG)
- [Grid CPU SIMD与MPI/OpenMP说明](https://github.com/paboyle/Grid)
- [openQCD架构与求解器说明](https://luscher.web.cern.ch/luscher/openQCD/)

本次选这三个而不是QPhiX，是为了同时覆盖AMG、可移植SIMD框架以及成熟
deflation/SAP算法；QPhiX的Xeon专用优化很有价值，但不优先作为跨到神威的
移植基线。该选择不意味着已经比较过所有库在目标超算上的速度。
