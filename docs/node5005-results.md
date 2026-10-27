# node5005：EPYC 9755、8 NUMA 实测（2026-10-22）

当前代码无需修改即可在 `node5005` 运行。通过 SSH 检查实际硬件，在该节点重新编译本机指令集版本，NUMA launcher 自动选择 **8 MPI ×32 OpenMP 线程，共 256 个物理核**。默认细层 SAP 和粗层 Schur 奇偶预处理均启用。

## 硬件与 NUMA

`lscpu`：2 路 AMD EPYC 9755，每路 128 核；共 256 核，SMT 关闭（每核 1 线程）。CPU 亲和集合为 `0-255`。

| Socket | NUMA | CPU 范围 |
|---|---|---|
| 0 | 0、1、2、3 | 0-31、32-63、64-95、96-127 |
| 1 | 4、5、6、7 | 128-159、160-191、192-223、224-255 |

NUMA 距离：本域 10，同 socket 的其他域 12，跨 socket 32。每域约 290,000 MB 内存。launcher 自动去重物理核、绑定 rank 及域内 OpenMP places，无需手填 256 或 32。

共享文件系统上的源码哈希与 88 核验证版本一致。AMD 二进制使用单独的 `build/node5005-runtime`；GCC 14.4.0 的 `-march=native -mtune=native` 在该节点解析为 **znver5**，没有覆盖或复用 Intel 构建。MPI 为 conda pyquda 环境中的 Open MPI 5.0.10。

## 同一真实 24³×64 配置

输入仍是 `beta6.20_mu-0.2770_ms-0.2310_L24x64_cfg_20000.lime` 经既定一次 stout 后导出的 fixture；mass=-0.277、csw=1、时间反周期，block=6×6×6×4，24 个 test vectors、48 个粗自由度，两层 MG，seed=1024。每次零初值，复用自行生成的 hierarchy。

| 项目 | node5005，8×32 核 |
|---|---:|
| Setup | 74.462 s |
| 首次单列完整 host API | 2.031385 s |
| **第二次单列完整 host API** | **1.901557 s** |
| 后续 4 次稳态中位数 | 1.956641 s |
| 第二次 backend solver-only | 1.625773 s |
| **实际完整 12 列** | **23.084941 s** |
| 单列累计外迭代 | 17 |
| QUDA probe 算子相对误差 | 3.8904×10⁻¹⁶ |
| 单列解相对保存 QUDA 解的差异 | 1.4890×10⁻⁷ |
| **12 列独立完整残差最大值** | **3.75×10⁻⁹** |

完整 host API 包括 Python wrapper、布局转换及 runtime 完整残差门；排除 setup、文件 I/O 和额外的独立验算。5 次单列样本为 `2.031385、1.901557、1.827771、2.011725、2.082687 s`。完整 12 列使用同样的 8×32 线程配置，无 block Krylov 或上次解热启动。

新 AMD 构建的 **13/13 CTest 通过**。12 列输出由该节点编译的独立标量 C++ Wilson-Clover 算子逐列验算，全部满足 `1e-8`。

## 扩展性观察

后续已完成同机 32/64/128/256 核扫描及 perf、PMPI 和控制实验，见 [强扩展诊断](node5005-perf.md)。下文保留首次自动 8×32 测量的上下文。

此前同一源码在 88 核 Xeon 上为第二次 1.884575 s、稳态中位数 1.905824 s、12 列 24.528831 s。因此当前默认配置在 256 核上与 88 核大致持平，12 列略快；这是不同节点、不同时间的实测，不能解读为线性加速或最优配置。

代码中仍有两项扩展限制：时间方向粗格点为 16，分给 8 个 rank 后每 rank 仅 2 个 t-plane，二者都是边界，当前 matvec 没有内部 aggregate plane 可用于隐藏通信；setup 资产和 double reference 场仍有全局副本，粗层 Krylov 仍有 MPI 标量归约。它们说明了进一步调优需要关注的方向，尚未用详细 profiling 对耗时占比逐项归因。本次只测自动 8×32，未扫描其他拓扑或线程数。

## 复现

在 `node5005` 的共享工作区 `/public2/home/lwb_720/lqcd` 执行：

```bash
MPI_PREFIX=/public2/home/lwb_720/miniconda3/envs/pyquda \
LQCD_TEST_PYTHON=/public2/home/lwb_720/miniconda3/envs/pyquda/bin/python \
BUILD_DIR=$PWD/multigrid.cpp/build/node5005-runtime \
LQCD_CPU_NATIVE=ON BUILD_JOBS=32 \
bash multigrid.cpp/tools/build_runtime.sh
ctest --test-dir multigrid.cpp/build/node5005-runtime -j 2 --output-on-failure

LQCD_CPU_LIBRARY=$PWD/multigrid.cpp/build/node5005-runtime/liblqcd_cpu.so \
LQCD_HALO_PROFILE=0 OPENBLAS_NUM_THREADS=1 \
/public2/home/lwb_720/miniconda3/envs/pyquda/bin/python -u \
multigrid.cpp/tools/run_numa.py \
--mpirun /public2/home/lwb_720/miniconda3/envs/pyquda/bin/mpirun -- \
/public2/home/lwb_720/miniconda3/envs/pyquda/bin/python -u \
multigrid.cpp/benchmarks/runtime/benchmark_runtime.py --repeats 5 --twelve-rhs \
--output .cache/node5005-20261022/reproduction

/public2/home/lwb_720/miniconda3/envs/pyquda/bin/python \
multigrid.cpp/benchmarks/runtime/verify_runtime_columns.py \
.cache/node5005-20261022/reproduction \
--reference multigrid.cpp/build/node5005-runtime/multigrid --threads 16
```

复现时保持 `LQCD_SAP_EO`、`LQCD_COARSE_EO`、`LQCD_ADAPTIVE_CORRECTION` 和 `LQCD_SETUP_UPDATE` 未设置，以验证默认值；不要设置 `NATIVE_*` 实验覆盖项。

原始样本、12 列残差、拓扑/测试日志、编译选项和源码/二进制哈希均记录在 [node5005-results.json](node5005-results.json)。配置记录见 [epyc9755_256.json](../profiles/epyc9755_256.json)，其中核数是这次实测的记录，运行时仍自动发现资源。
