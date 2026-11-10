# 2026-11-10：node5005按Zen 5架构优化单source

本轮只处理同一组态、同一个source的完整12列，不做多个source分组。
最终结果及采用决定以同目录`summary.json`和`best.json`为准。

**本轮尚未证实稳定加速，保留原833稳定版。** 两行模式初测中位6.111847秒，
独立新进程复测6.183829秒，收益未稳定重复。因此6.111322秒只能标为候选最快
观测样本，不能作为已经交付的稳定速度；旧版历史最快仍为6.120672秒，
本轮的旧版对照以表格及summary的实际记录为准，不能混选不同日期样本算加速比。

## 芯片与计算模式

实机是双路AMD EPYC9755、256个物理核、8个NUMA域，无SMT；每8核共享L3。
AMD官方架构说明：Zen5每CCD最多8核共享32MiB L3，每核1MiB L2、完整512位向量数据通路。
实际L1数据缓存48KiB。[官方架构白皮书](https://docs.amd.com/api/khub/documents/UIqhAbjRhgnzgzzdVU4pUw/content)、
[软件优化指南58455](https://docs.amd.com/v/u/en-US/58455_1.00)。
没有把理论峰值当实际吞吐，也没有将只支持16个时间聚合分片的程序直接改为32MPI。

实测旧稳定版完整12列profile，代表rank0/8用户周期采样中等待36.36%/41.38%，
rank0的packed Wilson约29%、独立Clover约1.96%。这不是整节点墙时分解。
源码及profile促成以下实验，而非任意参数扫描：

| 模式 | 计算组织变化 | 首轮稳态中位数，秒 | 判断 |
| --- | --- | ---: | --- |
| 旧稳定版833，开始对照 | 原版 | 6.190465 | 基线 |
| 第一轮新库关闭 | 原路径 | 6.184439 | 接近旧版 |
| Clover输入驻留 | 六个复输入驻留ZMM供六行复用 | 6.174988 | 收益太小 |
| Clover双行流水 | 同时算两行，复用输入并增加独立累加链 | 6.111847 | 唯一值得复核的候选 |
| 第一轮旧版结束对照 | 原版 | 6.161594 | 前后漂移0.47% |
| 符号投影新库关闭 | 原路径 | 6.205625 | 未胜旧版 |
| 符号投影开启 | 将±1/±i复乘换成加减、交换实虚部 | 6.170247 | 未明显胜旧版 |
| 第二轮旧版结束对照 | 原版 | 6.177046 | 保留 |
| 站点分块新库关闭 | 原路径 | 6.243229 | 新代码布局存在开销 |
| 双列16站点片段 | 系数约18KiB，小片段先算两列再前进 | 6.267779 | 比关闭还慢 |
| 双列64站点片段 | 系数约72KiB，减少调用次数 | 6.179250 | 追回退化，未明显胜旧版 |
| 第三轮旧版结束对照 | 原版 | 6.188180 | 保留 |
| 两行模式独立进程复核 | 第一轮精确源码/库，保持模式2 | 6.183829 | 首轮收益未重复 |
| 最终旧版对照 | 原版 | 6.161810 | 保留原稳定版 |

输入驻留汇编确认使用ZMM、未出现向量栈spill；但源加载只是Clover部分流量，
不能因此承诺大幅收益。双行模式的独立累加链在本机更有利，需独立进程复核。
符号投影减少运算并未明显加速，说明不能只按浮点指令数判断。
站点分块的16/64对照支持“细分带来的调用/尾部处理开销抵消缓存复用”的解释；
没有测cache-miss硬件事件，不声称量化了缓存命中率或内存带宽。

## 公平性和精度

共同stout后24×24×24×64规范场，质量−0.277、Clover系数1.160920226，
原点单位源，时间反周期，DR自旋基、mass归一化。规范场字节摘要
`126d658999367b0ece3801c61cd143542d7db0dddc37ab60e6e668e18faa6834`。
16MPI、每rank放置/建层16线程，求解12线程（192个求解线程），双列批处理。
256核可用不等于256核都在求解；这沿用此前最快的已验证配置。
直接SSH，未取得调度独占保证，保留所有前后对照。

每组新进程自己建层，一次完整12列预热、三次完整12列稳态，全部列零初值。
主表是MPI最慢rank的完整Python求解API墙时，包含布局转换及可靠残差检查；
排除读组态、stout、建层、输出和独立验算。profile的诊断时间不混入普通样本。
首次时间、全部样本和逐列迭代/额外修正次数都在`summary.json`，不只保存最快值。

三轮分别完成33、22、33项CTest检查，涵盖掩码/尾部、Wilson局部/全局/packed、
core、MPI2批处理、Python批处理和MG调参一致性；共88项，全部通过。
每组普通计时检查全部12列完整真残差；保存的最后一轮全部12列还由原始标量
C++程序独立验算，并与冻结参考传播子比较。门限分别1e-8与1e-6。
各组精确误差、参考程序及传播子摘要见导出的证据，未使用单列乘12或外部MG替代。

## 记录与限制

远端根目录`/public2/home/lwb_720/.cache/mg-x86-20261110`。复用已有worker、
NUMA启动器、canonical完整12列驱动和独立标量校验，不重写科学验证。
历史`benchmark_runtime.py`入口依赖其源码上级的
`PyQCU/data/lime_mg_20261013/input.h5`等文件，本轮目录没有这套旧HDF5资产，
没有把本轮标成该旧入口已通过；实际使用现有`bench_full12.py`的共同stout后fixture，
由其独立12列标量/参考校验验收。旧入口复现仍需要恢复匹配HDF5资产。

首次采样任务000因驱动要求至少三个稳态样本，在参数校验阶段失败，未做数值计算；
001按工具约束重试成功，原失败保留。结果的`source_manifest_sha256`字段误传
40字符Git提交ID，不能当作64字符清单摘要。保留原记录；`source-provenance.json`
另存实际源码Git状态、逐文件摘要、真实清单摘要及库摘要，输入、精度和时间不受影响。

实验开关均默认关闭，必须新进程启动前设定。旧稳定版及三个独立源码/构建目录保留。
不能把较新但变慢的试验库当作最佳。详细假设、归因和恢复方法见`README.md`。

## 编译与运行

在node5005的项目Git克隆中，原稳定源码可单独取出编译（不重置工作区）：

```bash
git worktree add --detach ../mg-x86-stable 833f8732f6b06e370074efbb610fc7a85fe11a46
cd ../mg-x86-stable
task_pybin=/public2/home/lwb_720/miniconda3/envs/pyquda/bin
export PATH="$task_pybin:/public2/home/lwb_720/miniconda3/bin:$PATH"
cmake -S . -B build/x86 -DCMAKE_BUILD_TYPE=Release \
  -DMULTIGRID_NATIVE=ON -DLQCD_BUILD_RUNTIME=ON \
  -DCMAKE_C_COMPILER=/public2/home/lwb_720/miniconda3/bin/gcc \
  -DCMAKE_CXX_COMPILER=/public2/home/lwb_720/miniconda3/bin/g++ \
  -DMPI_C_COMPILER="$task_pybin/mpicc" -DMPI_CXX_COMPILER="$task_pybin/mpicxx" \
  -DLQCD_TEST_PYTHON="$task_pybin/python"
cmake --build build/x86 -j16
```

native编译在node5005进行。GCC14.4、该环境MPI、Release O3和本机ISA；没有打开
fast-math或降低精度。重新编译生成的新二进制需要重新验证，不能继承旧库摘要和成绩。
三轮候选的实际构建命令分别在`build.sh`、`build_projector.sh`、`build_tile.sh`，
对应固定cc3804e、7a64984、edd611b源码，未在同一个构建目录覆盖旧库。

复用超算上已完成的构建和共同stout后输入，重跑原稳定版完整基准：

```bash
ssh itp
ssh node5005
export PATH=/public2/home/lwb_720/miniconda3/envs/pyquda/bin:$PATH
export OPENBLAS_NUM_THREADS=1 OMP_PROC_BIND=close
python /public2/home/lwb_720/.cache/mg-x86-20261110/measure.py old-manual-001
```

每次须换新名称，例如old-manual-002，输出不会覆盖。脚本调用NUMA启动器，
16MPI×16放置线程、建层后改为12求解线程，执行一次预热和三次完整12列，随后
调用原标量程序独立验算全部列。原生调用/内部求解计时也保留在逐列stats中；
不能把它们与本报告的完整Python API时间混用。
输出为远端根目录下`old-manual-001/full12/result.json`，总命令运行时间含建层和验证，
应读取其中`samples[].wall_seconds`并排除warmup=true样本作为纯求解时间。

源码、脚本、证据已经保存在本地项目；大传播子、共同组态、perf原始数据及站点库
留在超算。额外的本地Git与库备份见项目相邻目录`multigrid-x86-20261110-backup`。
