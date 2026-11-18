# 2+1 味 Wilson–Clover HMC：实现步骤与当前边界

项目提供三条使用 complex128/float64 的 2+1 味 Wilson–Clover 生成路径。

| `--sea-action` | 热浴与验收 | MD 力 | 用途 |
|---|---|---|---|
| `determinant`（默认） | 密集精确行列式 | 自动微分 | 最高 32 点的独立基准 |
| `pseudofermion` | 密集谱分解 | 多移位 CG、有理奇异味力 | 最高 32 点的伪费米子正确性验证 |
| `matrix-free` | 奇偶 Schur 算子和有理矩阵幂 | 多移位 CG、按极点分批反传 | 单节点无矩阵 RHMC 验证 |

无矩阵路径以局部 Clover 本征值和 Wilson hopping 范数的充分条件检查单奇异味
行列式为正，并在固定区间检查有理近似。本轮参数为 mₗ=0.5、mₛ=0.8、cSW=1。
当前充分条件对拟用于生产的负质量有局限，L24 生产还需要分布式力和谱监测。
[灵晟试跑与验算数据](../experiments/ls-performance-20261119/README.md)

```bash
python tools/hmc/generate.py --output /outside/source/matrixfree-64 \
  --sea-action matrix-free --lattice 2 2 4 4 --beta 5.6 \
  --mass-light 0.5 --mass-strange 0.8 --csw 1 --integrator omelyan \
  --trajectories 4 --warmup 1 --length 0.1 --steps 1 --save-every 1 --seed 1729
python tools/hmc/verify_configs.py /outside/source/matrixfree-64 \
  --reference /outside/source/build/multigrid
```

下面先介绍精确行列式基准，再给出扩展到生产规模的步骤。

## 1. 先确定要生成哪一种理论

需要给定：格子 `Lx,Ly,Lz,Lt`、规范作用量、β、两个轻海夸克的共同裸质量 mₗ、
奇异海夸克裸质量 mₛ、Clover 系数 cSW、费米子边界、是否使用链路涂抹及其参数。
海夸克参数不能从一次传播子求解的价夸克参数自动推定。

当前演示为 Wilson plaquette 规范作用量，β=5.6、mₗ=0.5、mₛ=0.8、cSW=1，
规范场周期、费米子时间反周期，无 stout。质量较重、格子很小，不设定物理格距，
不声称处在物理点。保存的链接始终**不带时间扭转**；算子在时间缝上施加一次负号。

## 2. 正确的 2+1 味权重

目标配分函数是

`Z = ∫ [dU] exp(-Sg[U]) det(Ml[U])² det(Ms[U])`。

Z 是配分函数；U 是各格点四方向的 SU(3) 链接；[dU] 是群 Haar 积分测度；Sg 是
规范作用量；Ml、Ms 分别为轻、奇异质量下的 Wilson–Clover 算子；det 是行列式。
两轻味简并，因此出现平方；奇异味只有一次。现有归一化算子 M 与通常非归一化
Dirac 算子相差只依赖固定质量的常数，常数不改变规范场分布或力。

当前直接使用

`Seff = Sg - 2 log|det(Ml)| - log|det(Ms)|`。

Seff 是积分掉海夸克后的有效作用量。代码每次评估要求奇异行列式相位为正实数；
遇到负号、奇异或非有限值立即报错，不静默丢掉单味行列式符号。小体积运行保存
该检查的证据；这不证明任意质量和任意规范场上都没有符号问题。

规范作用量为 `Sg = β ∑(1-ReTr(P)/3)`，P 是每个基本方格的四链乘积，求和遍历
格点和六个方向平面，ReTr 表示迹的实部，3 来自颜色数。Clover 场强使用四叶回路，
与 `src/core/clover.cpp` 的系数、DR 自旋基和质量归一化对齐。

## 3. 一条 HMC 轨迹

1. 从当前链接 U 开始，为每条链接刷新8个独立标准实高斯数 pₐ；a 标记 SU(3) 的
   8个生成元 Tₐ，归一化为 `Tr(Tₐ Tᵦ)=δₐᵦ/2`，δₐᵦ 是单位矩阵元素。
2. 构造 `H = Seff + ½∑pₐ²`。H 是扩充相空间的 Hamiltonian，第二项是动能。
3. 计算 `Fₐ = d Seff(exp(iεTₐ)U)/dε | ε=0`。Fₐ 是链接左乘群旋转方向上的力。
   自动微分同时穿过 hopping、四叶 Clover 和两个质量的行列式，不冻结 Clover。
4. 用固定步长 δτ 和步数做 leapfrog：半步动量、整步群更新、整/半步动量。
   群更新为 `U ← exp(i δτ ∑pₐTₐ) U`，i 是虚数单位；不在每步重投影，以免破坏可逆性。
5. 计算 `ΔH = H末 - H初`，以 `min(1,exp(-ΔH))` 接受提议。拒绝时完整保留旧 U。
   不能只保留接受轨迹，否则会改变 Markov 链的采样分布。
6. 按固定轨迹间隔测量/保存，记录接受率、ΔH、plaquette、SU(3) 误差、参数、种子、
   源码提交和文件 SHA256。前若干条可标为预热，但真正热化需要额外收敛诊断。

经典 HMC 依据为 Duane、Kennedy、Pendleton、Roweth，*Hybrid Monte Carlo*，
Phys. Lett. B195 (1987) 216，[DOI](https://doi.org/10.1016/0370-2693(87)91197-X)。

## 4. 必须先过的验证

`tests/hmc/test_reference.py` 覆盖：生成元归一化、γ5 Hermiticity、规范协变性、
2+1 行列式权重、规范/海夸克/总力的中心有限差分、非零 Clover 力、前后积分可逆性、
SU(3) 约束和二阶积分步长缩放。

两个质量的稠密算子与原有独立标量 C++ `multigrid --operator` 的随机向量像比较。
LIME 文件用现有 SciDAC 读取器独立核对 CRC 并逐值回读；每份实机文件还用独立
NumPy plaquette 和 C++ 算子像复核。测试通过才生成组态，文件验证在轨迹计时外。

默认 CMake 不引入 PyTorch 依赖；显式启用：

```bash
cmake -S . -B /outside/source/build -DCMAKE_BUILD_TYPE=Release \
  -DLQCD_TEST_HMC_REFERENCE=ON -DPython3_EXECUTABLE=/path/to/python
cmake --build /outside/source/build -j4
ctest --test-dir /outside/source/build --output-on-failure
```

Python 需要 NumPy 和 CPU PyTorch。若启用 `LQCD_HMC_REQUIRE_LIME_READER=ON`，还需
mpi4py 及正确 MPI 环境，LIME 回读不能跳过。不启用该项且环境无 MPI 时，报告会
明确记录该项 skipped，不能把它当成已验证的文件兼容性。

```bash
python tools/hmc/generate.py --output /outside/source/new-chain \
  --lattice 2 2 2 2 --beta 5.6 --mass-light 0.5 --mass-strange 0.8 --csw 1 \
  --trajectories 80 --warmup 40 --length 0.5 --steps 10 --save-every 10 --seed 1729
python tools/hmc/verify_configs.py /outside/source/new-chain \
  --reference /outside/source/build/multigrid
```

输出 `hmc_*.lime`、`result.json` 和保存了链接/RNG状态/轨迹号的 `latest-state.pt`。
后者是检查点工件，当前 CLI 尚不提供 resume；不要重新使用种子后声称是检查点续跑。
输出目录必须不存在，完整结果必须检查 `complete` 和 `verification.json`。

灵晟入口 `tools/hmc/run_ls.sh NEW_OUTPUT` 在计算节点编译、跑 CTest、生成并回读；
只需要4个允许 CPU、16 GB调度内存，本轮不测量节点性能，不申请独占大节点。

## 5. 从此基准走到24格子生产 2+1 味

1. **保持同一个目标作用量。** 确认海夸克质量、cSW、规范改进项、边界与涂抹。
2. **以伪费米子取代稠密行列式。** 两轻味使用 `Al=Ml†Ml` 的逆；单奇异味通常
   使用 RHMC 的 `As^(-1/2)`，As=Ms†Ms，† 表示共轭转置。伪费米子热浴也需匹配
   相应矩阵幂，不能只替换力里的求逆。
3. **验证有理近似。** 给出谱区间、逼近误差、分式系数和 shifted solves 的残差。
   RHMC 参见 [Clark & Kennedy, hep-lat/0608015](https://arxiv.org/abs/hep-lat/0608015)。
4. **实现稀疏的解析力与 MPI halo。** Wilson 链力、Clover 四叶回路力以及可选
   涂抹的链式导数都需匹配。若作奇偶预处理，不能遗漏被消去的局部 Clover 行列式。
5. **接入项目 MG/Krylov。** 规范场在每个 MD 步变化，旧建层不能不经验证地永久复用。
   刷新/重建策略与解容差必须通过可逆性和 ΔH 测试；不能把传播子接口直接反复调用
   当成已实现的 HMC 力。动力学力、热浴、接受判定的精度预算应分别设定。
6. **再做加速和物理验收。** Hasenbusch 质量分裂、多时间尺度、Omelyan、轨迹长度
   调整先在预热确定，随后固定参数。检查长链热化、自相关、有效样本数、拓扑，做
   格距与海夸克质量调谐；这一步之后才能称物理生产系综。

本次小体积实际 HMC 组态证明的是算法/算子/文件链路；80条轨迹、指定40条预热段、
每10条保存不构成热化或独立样本的证明，也不外推24格子速度。

## 6. 原生 Schur 内核和 MPI 版 RHMC

可选 C++/OpenMP 内核为 FP64 Krylov 求解提供半自旋 Schur 算子。设置
`LQCD_HMC_SCHUR_LIBRARY` 后，单进程矩阵自由 RHMC 会调用该内核。
MPI 入口要求安装 mpi4py，按时间方向等分，四个全局格长必须为偶数，
MPI rank 数须整除全局时间格长。正常求解时每个 rank 仅保留本地场及边界，
保存时由 rank 0 汇集并写出 SciDAC LIME。

```bash
cmake -S . -B /outside/source/build -DCMAKE_BUILD_TYPE=Release \
  -DLQCD_BUILD_HMC_KERNELS=ON
cmake --build /outside/source/build -j4 --target lqcd_hmc_kernels multigrid
export LQCD_HMC_SCHUR_LIBRARY=/outside/source/build/liblqcd_hmc_kernels.so
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
mpirun -n 4 python tools/hmc/generate_mpi.py --output /outside/source/mpi-chain \
  --lattice 4 4 4 4 --beta 5.6 --mass-light 0.5 --mass-strange 0.8 --csw 1 \
  --trajectories 4 --warmup 1 --length 0.06 --steps 1 --save-every 1 --threads 1
python tools/hmc/verify_configs.py /outside/source/mpi-chain \
  --reference /outside/source/build/multigrid
```

力通过自动微分处理海夸克项和边界伴随通信。奇异味使用固定有理谱区间，
行列式符号和谱区间在每次热浴和端点计算时检查。上述重质量用于验证。
MPI 随机种子为基础种子加
rank 编号，变更分解会改变随机流。同一场上的性能比较应显式复用动量及伪费米子噪声。

`--md-order` 设置奇异味 MD 力在每侧积分尾部的求积阶数，两个尾部共
`2 × md-order` 个极点。默认 32。该参数仅修改积分所用的力，热浴和
Metropolis 端点仍使用各自通过精度检查的有理式。报告包括各阶段用时、
极点数及固定谱区间上的网格误差。

`--md-tolerance` 只调整 MD 中轻味与奇异味线性系统的相对真残差门槛，
默认 `1e-12`。热浴和 Metropolis 继续使用各自原有的精度设置。

`--gauge-steps 2` 将规范场力放入 Omelyan 内层，在每个费米子漂移区间做
两步规范场积分。省略该参数时使用单时间尺度。两种积分器使用相同的端点
Hamiltonian 和 Metropolis 判定。

MPI 生成器随每份 SciDAC LIME 保存各 rank 的 `.rng.npy` 状态。将上一段的
`result.json` 传给 `--resume-from`，指定新的输出目录，并沿用原来的格点、
质量、MPI rank 数、种子和积分参数。程序从报告中最后一条已保存的轨迹继续
编号，并检查 LIME 与 RNG 的 SHA256。续跑时 `--trajectories` 和
`--warmup` 分别表示新段的轨迹数和预热数。可以用 `--warmup 0` 直接追加样本。

`--packed-faces` 让原生 Schur 核直接读取本地自旋场与时间方向的半自旋
边界缓冲区，省去每次调用把整个本地场复制到扩展缓冲区的操作。
`--direct-clover` 可独立选择四叶 Clover 的解析伴随导数。

接近冷场的负 Wilson 奇异质量可用自由算子的最小奇异值减去规范场扰动
的范数上界来认证。该下界为正时，连接自由算子和当前算子的整条直线保持
γ₅ Hermiticity 和非奇异性，因而保持正行列式符号。运行时用
`--strange-interval LOW HIGH` 指定固定的有理谱区间。粗糙规范场可能超出
这个充分条件的适用范围，此时运行停止并保留已经写出的报告。自由谱采用
时间反周期边界条件。[自由 Wilson 算子的动量空间形式](https://pmc.ncbi.nlm.nih.gov/articles/PMC6394278/#Equ30)
