# Kunpeng-920 ARM 后端

`arm` 与 `x86` 共用 `src/solver/native/` 中的 MG、EO SAP、粗层 EO、可靠更新、
Krylov 与 MPI halo；不复制一套求解器。`src/backends/arm/` 提供硬件工厂、NEON
Clover/inverse 矩阵乘和 portable Wilson dispatch，`src/backends/portable/` 保留共享
Wilson 数学。公开 C ABI、DeGrand–Rossi 基底、PyQUDA EO-x/lex 布局和 `.npy` 格式不变。

CMake 根据实际构建目标选择 `arm` 或 `x86`，Python 默认按本机架构选择后端；CLI
允许显式 `--backend arm`。未编译的后端返回 unsupported。此实现为 CPU 后端，
不创建 `cann` 的 CPU 别名：Ascend/CANN 属于另外的 NPU 环境。

## Skill 和 ISA 依据

已建立并安装 `kunpeng-lingsheng-cpu` skill，仓库副本位于
`LQCD_Skills/kunpeng-lingsheng-cpu/`，安装副本位于 `.codex/skills/kunpeng-lingsheng-cpu/`。
它包含官方 Arm ACLE/NEON、GCC、Linux HWCAP 文档和灵晟 LX2 论文链接，以及只读
`probe_cpu.py`。实际 `ssh ls` 的 `login04` 为双路 Kunpeng-920、128核、4 NUMA；
HWCAP 显示 ASIMD=true、SVE/SVE2/SME=false。论文中的计算节点能力不能套用于登录节点。

本次 ARM 构建使用 GCC10.3.1、`-O3 -march=native -mtune=native -fopenmp`、
MPICH4.3.1、CMake3.31.6；运行依赖 NumPy2.0.2、mpi4py4.1.1。工具安装在独立 venv，
无系统改动。原系统 CMake 安装不完整，远端无法解析外网 DNS，因此由本地下载 ARM64
wheel 后离线安装。MPI 库由 `/usr/local/lib` 提供，mpi4py 实际链接同一 MPICH。

NEON Clover 以四个物理 site 为向量，保留未对齐范围和标量尾部；ARM 实机测试覆盖
独立 double oracle，反汇编确认出现 `fmul v*.4s` / `fmla v*.4s`。当前没有 SVE/SME
内核，Wilson hopping 是通用 OpenMP SIMD，不能据首版功能测试声称 ARM 性能最优。

## 构建和运行

在实际 ARM 执行主机原生编译，使用与 mpi4py 匹配的 MPI：

```bash
cmake -S multigrid.cpp -B multigrid.cpp/build/arm \
  -DCMAKE_BUILD_TYPE=Release -DLQCD_BUILD_RUNTIME=ON -DMULTIGRID_NATIVE=ON \
  -DMPI_C_COMPILER=/usr/local/bin/mpicc \
  -DMPI_CXX_COMPILER=/usr/local/bin/mpicxx
cmake --build multigrid.cpp/build/arm -j4
export LD_LIBRARY_PATH=/usr/local/lib:${LD_LIBRARY_PATH:-}
export LQCD_CPU_LIBRARY=$PWD/multigrid.cpp/build/arm/liblqcd_cpu.so
export OPENBLAS_NUM_THREADS=1 LQCD_RHS_BATCH=2
python multigrid.cpp/tools/run_numa.py --threads 2 -- \
  python -u multigrid.cpp/tools/solve_propagator.py --backend arm \
  --gauge configuration.lime --mass -0.277 \
  --stout-steps 1 --stout-rho .125 --stout-dir-ignore 4 \
  --repeats 2 --save-gauge --output results/arm-new
```

NUMA 启动器支持 Open MPI 与 MPICH/Hydra，检测后使用各自参数，仍限制为单机。
核数由可用 cpuset/NUMA 发现，`--threads` 是每进程线程数，不写死128核或38核。
示例限制核数以验证登录节点功能；性能测试应使用实际计算节点分配。

本次 `ssh ls` 上的隔离环境可直接复用：

```bash
source "$HOME/.cache/multigrid-arm-20261025-env/bin/activate"
cd "$HOME/.cache/multigrid-arm-20261025/source/multigrid.cpp"
export LD_LIBRARY_PATH=/usr/local/lib:${LD_LIBRARY_PATH:-}
export LQCD_CPU_LIBRARY="$HOME/.cache/multigrid-arm-20261025/build/liblqcd_cpu.so"
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 LQCD_RHS_BATCH=2
```

随后执行上面的启动命令，替换为此目录中的 `tools/` 路径、真实输入路径和一个全新
输出目录。完整12列在每轮都从零初值求解，第二轮复用同一个 MG hierarchy。

## 数值验收

- x86 重构后 29/29 CTest 全部通过，包括原有 MPI、batch、LIME/stout 和完整传播子。
- Kunpeng 上内核、LIME、stout、MPI2 MG 调参等 11/11 CTest 通过；另两个无需 PyQUDA
  的 CPU 接口测试在串行/MPI2 上通过，覆盖两随机源、EO/lex、mass/kappa、batch、
  零源和不可用后端恢复，独立 NumPy 全残差门 `1e-10`。
- `8^4` 非平凡 SU(3) LIME、一步 stout、csw1.160920226、mass.05、非原点源
  `(3,1,2,5)` 的完整12列已在 ARM MPI2×OMP2 下求出；第二轮2.898s，仅为功能计时。
  导出12列独立 scalar C++ 最大残差 `1.037875e-9`，实际 PyQUDA MPI2 加载逐元素一致。

真实24³×64原始 LIME 也完成了两轮完整传播子求解，参数为 mass=-.277、
csw=1.160920226、一步 stout/rho=.125/四方向、原点单位源、时间反周期。
使用4 MPI×8 OpenMP，分布在4个 NUMA 的 `[0-7]`、`[32-39]`、`[64-71]`、
`[96-103]`；每列每轮都从零初值开始，第二轮共用第一轮的 hierarchy。

| 阶段 | 秒 |
|---|---:|
| MG setup | 459.663 |
| 第一轮完整12列 | 145.209 |
| 第二轮完整12列 | 144.675 |
| 第二轮求解器内部合计（6个双RHS batch，仅计一次） | 142.776 |

两轮各列均为24–25次迭代，未触发 correction/refinement；运行时最大 double
全残差 `4.818863e-9`。这是共享登录节点、32核、首版 portable hopping 的功能记录，
不是灵晟 LX2 计算节点的性能结果，也没有达到原来的5s性能目标。第一轮有2秒短
perf采样，第二轮未采样。采样无丢样：求解阶段 `local_range` 28.47%、portable local
Wilson 22.88%、portable global Wilson 22.27%（均为符号 self cycles）；setup 的独立
8核采样中 `assemble_local_block` 占94.79%，是后续分别优化的依据。

真实格子输出：
`ls:/home/share/nsls_lwb/.cache/multigrid-arm-20261025/lime24-output32/propagator.npy`
（complex128，约1.9GiB，global `[t,z,y,x,sink_spin,source_spin,sink_color,source_color]`）。
同目录的 `result.json` 记录输入/库 SHA256、布局、各列残差与计时；本地副本为
`.cache/arm-port-20261025/lime24-result32.json`。输入 SHA256 为
`47969c7fe9b4a4716d5eab40e5a1dbdaef09abdb055934000e034a99d20d2d30`。

导出的真实格子12列也全部通过独立 scalar C++ 检查，最大相对残差
`4.818862816205033e-9`。共享文件系统上 NumPy `tofile()` 的大块临时写入曾停在
`OdcDioWriteIovec`，故改用系统 Python 标准库、只拷贝原始16字节复数的临时 C++
列提取工具和节点本地 `/tmp`，再调用原独立 `multigrid --validate-solution`。
提取工具在小格点上的全部12列与 NumPy 切片逐字节一致，不改变解的数值。
验证文件记录正式传播子的 SHA256、独立 reference 的 SHA256、12列残差与完整状态：
`.cache/arm-port-20261025/lime24-scalar-verification/verification.json`。
远端同名子目录位于本次远端工作目录内，包含复核脚本和逐列日志。

远端构建/输出位于 `/home/share/nsls_lwb/.cache/multigrid-arm-20261025/`；本地证据位于
`.cache/arm-port-20261025/`。原 PyQCU、旧 x86 构建和基准数据保留；PyQCU 的 CANN
Python 兼容层和 KUPL CPU 代码用于参考，不作为本后端的外部运行依赖。
