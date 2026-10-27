# 代码阅读顺序

完整四章中文导读见 [项目结构、Multigrid算法与CPU后端](project-algorithm-guide.md)，
包含P/R映射、实际格子示例、三层红黑/奇偶关系、异步时序图与硬件内核。

生产运行由 runtime 进入共享 native backend 的 `setup()`。建议按下面顺序阅读，先理解数据
所有权，再看数值算法和 SIMD 细节：

1. `src/solver/native/backend.cpp`：创建 hierarchy、调用 setup、进入 apply/solve，
   保持 rank-local 词典序场，并处理 mass/kappa 归一化。
2. `src/solver/native/setup.cpp`：生成随机 test vectors，执行齐次 SAP 和自适应
   更新，做每个 aggregate 的手征 MGS，组装 `P` 与 `A_c=P†DP`。
3. `src/solver/native/cycle.cpp`：实现一次 V-cycle，依次执行 restriction、粗格点
   修正、prolongation 和 fine SAP。
4. `src/solver/native/sap.cpp` 与 `coarse.cpp`：分别阅读细格点块内 EO-Schur MR
   和粗格点 EO-Schur GCR；两者都保留旧的 full 诊断路径。
5. `src/solver/native/solver.cpp`：查看 float flexible GCR、double reliable
   residual refresh 及最终精度门槛。
6. `src/solver/native/double_operator.cpp`：本地 double 完整算子、物理时间面 halo
   及通信与内部格点计算重叠。`fine_operator.cpp`、`hierarchy.cpp`：阅读 float halo、
   block/site 地址、clover inverse、邻居表和 MPI 所有权。
7. `src/backends/x86/wilson_kernel.hpp` 或 `src/backends/arm/wilson_kernel.hpp`：最后再看 half-spin projection、split
   real/imag 布局和 OpenMP SIMD 热循环。`environment.cpp/.hpp` 提供 MPI 归约、
   配置和 profile 类型；`halo_profile.cpp` 只负责可选诊断；`validation.cpp`
   负责独立算子、P/R、RAP 和组成门。

## 三种字段形态

生产 `Field` 是当前 rank 的本地 t-slab 词典序 spin-color 场，每个 site 有
12 个 complex<double>。仅独立 scalar reference 和 setup 算子门保留全格点
`Field`；不能把这种验证用途混进生产求解。fine split field 是硬件内核共用的
内部形式：每个 aggregate 的 site 被整理为 split real/imag 数组，必要时再按
局部空间奇偶放置。local coarse field 只保存当前 MPI rank 拥有的 coarse
aggregates；未拥有的 coarse site 不参与 dot/norm，邻居通过 t-face halo 获取。
不要把 local coarse 向量误当成全局 replicated 向量。

常用几何变量如下：

- `block_sites`：一个 fine aggregate 内的 site 数，等于
  `bx*by*bz*bt`；细块局部数组按它分段。
- `coarse_dof`：每个 coarse site 的自由度。24 个 test vectors 按
  gamma5-compatible 两个 spin aggregate 分开，因此当前为 `2*24=48`。
- `first_aggregate`、`end_aggregate`：当前 rank 在
  coarse aggregate 线性编号中的半开区间 `[first_aggregate,end_aggregate)`。MPI t-slab 只分割这个
  区间；double 字段只保存对应的本地连续 site，float fine 暂保留全局编号工作区。
- `aggregates_per_tslice`：一个 coarse t-plane 的 aggregate 数；它决定 fine/coarse halo 的
  face 大小。fine 内部工作按物理 t 切片划分，coarse 仍按 aggregate 划分。

## 两层 EO 数学

对任意 fine 或 coarse block，把局部算子按 site parity 排列为

```text
A = [ A_e  H_eo ]       S_e = A_e - H_eo A_o^-1 H_oe
    [ H_oe A_o ]       b_e' = b_e - H_eo A_o^-1 b_o
```

求解器在偶分量上做有限次 MR/GCR；然后用
`x_o=A_o^-1(b_o-H_oe x_e)` 重构奇分量。细层 EO 是块内 Dirichlet Schur
smoother，粗层 EO 是 coarse GCR 的预条件求解。外层始终对完整 Wilson-Clover
算子计算 double residual，避免把近似 Schur 停止条件误当成最终精度。

## 计算与通信

每次 fine/coarse matvec 先发布邻居 t-face 的非阻塞 MPI receive/send。OpenMP
worker 计算不依赖 ghost 的内部站点；MPI 主线程完成 wait 后，所有
线程计算边界。fine/double 仅把物理首尾时间面延后，coarse 仍以 aggregate
为粒度。`LQCD_HALO_OVERLAP=0` 可用于同一消息协议的阻塞
对照。所有 dot/norm 的标量归约仍是 collective；它们决定的停止分支必须由
所有 rank 一致执行。

## 为什么保留独立 reference

`src/reference/` 是独立的 Wilson-Clover 数值路径，测试和 12 列传播子验算用它
重新计算完整算子。验算调用 core 中的标量 double Wilson-Clover 算子，不调用 生产 float MG 的 SIMD 核、Schur 求解或缓存解，因此可独立检查完整方程的布局、边界、归一化和最终残差。DDalphaAMG、Grid
和 openQCD 则位于 `benchmarks/reference-libraries/`，只用于外部算法和性能
对照，不是生产 backend。
