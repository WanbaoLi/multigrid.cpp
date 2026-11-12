# 灵晟 HBM、DDR 与双路 EPYC 9755 带宽实测

2026-11-06。下表使用48 GiB工作集，5轮中位数，单位GB/s（10^9 bytes/s）。
灵晟DDR/HBW在同一节点、同一作业内按相同592个物理核和相同数组大小顺序执行。

| 平台和内存 | 实际物理核数 | Read | Copy | Triad |
|---|---:|---:|---:|---:|
| 灵晟 DDR | 592 | 666.36 | 461.38 | 511.19 |
| 灵晟 HBW（平台 HBM） | 592 | 4777.25 | 4813.42 | 4486.21 |
| 双路 EPYC 9755 DDR | 256 | 981.86 | 555.51 | 644.06 |

Triad下，HBM约为本机DDR的8.78倍、
双9755 DDR的6.97倍。
这是该访问模式下的实测有效带宽，不是理论峰值或求解器加速比。

## 范围与核验

- 灵晟主对照作业2051113，节点`cn19468`，592个允许物理核、16个CPU NUMA域。
  DDR绑定nodes0–15；HBW绑定nodes16–31，CPU域和内存域分别一一配对。
  系统608核中每域留1核给系统，本次没有外推608核带宽。
  先前FMA节点cn19473忙碌，当前测的是同型号计算节点，不是同一台物理主机。
- 两类内存各分配48个数组，每数组1GiB、每域3GiB；总48GiB，远大于缓存。
  9755为node5005双路2×128核，8个NUMA域，每数组2GiB、每域6GiB，总48GiB。
- 所有线程固定到不同物理核，计时前后CPU检查通过。每数组在触页前严格设置NUMA绑定；
  before/after的move_pages样本与numa_maps完整VMA页面数均完全位于目标内存节点。
- 主对照使用HPCKit26.1 KUPL对每个完整数组做额外分类：DDR全部verify=0，HBW全部verify=1。
  新旧SDK分类探针发现：旧25.1将node31判为0，而26.1判为1；两者对nodes16–30均判为1。
  因此16域主表采用26.1，旧25.1的16域混合分类样本不计入主表。
- 同一CPU-native二进制执行灵晟两种内存测试；Bisheng19.1.7、SVE64B。
  AMD用GCC14.4、AVX512。两个平台源码一致，-O3 -std=c++17 -pthread -march=native，无fast-math。
  反汇编确认被测函数采用普通load/store，未调用memcpy/memmove、未使用非临时存储。
- 每个kernel先预热，之后5轮，每轮连续16遍，无计时内逐遍团队屏障。
  总带宽采用全队最早开始到最晚结束墙时，包含启动偏差、调度与争用；不是逐核峰值相加。
  每轮全输出checksum/误差检查通过；分配、初始化、页面检查和结果校验排除在计时外。

## 带宽口径

Read只读取一个double数组，每元素8字节；Copy `a=b`按一读一写16字节；
Triad `a=b+3*c`按两读一写24字节。两个平台都使用ordinary temporal stores。
实际控制器总线流量还可能含写分配/RFO，因此这些有效GB/s不是物理总线字节计数。
本测试是独立实现的STREAM式访问内核，不是官方STREAM程序的认证成绩。

DDR线程扫描表明更多线程未必更快：灵晟256核的Triad约619GB/s，592核旧扫描约506GB/s。
这反映该启动/同步和NUMA配置下的观测，不宜只用“全核”代表最优带宽。
主表保留全节点资源口径，下面保留所有线程扫描与不同工作集样本。
9755没有排他调度分配；所有数据均为当次共享机器条件下结果。

## 全部有效配置

| 配置 | 核数 | 总工作集GiB | Read GB/s | Copy GB/s | Triad GB/s |
|---|---:|---:|---:|---:|---:|
| lingsheng-ddr-full-node | 592 | 48.0 | 666.36 | 461.38 | 511.19 |
| lingsheng-hbw-full-node | 592 | 48.0 | 4777.25 | 4813.42 | 4486.21 |
| dual9755-ddr-full-node | 256 | 48.0 | 981.86 | 555.51 | 644.06 |
| scan-lingsheng-ddr-threads16-size1024 | 256 | 48.0 | 649.30 | 593.05 | 619.40 |
| scan-lingsheng-ddr-threads16-size512 | 256 | 24.0 | 649.12 | 595.41 | 618.19 |
| scan-lingsheng-ddr-threads8-size512 | 128 | 24.0 | 636.97 | 589.54 | 612.40 |
| scan-lingsheng-ddr-threadsall-size512 | 592 | 24.0 | 666.10 | 472.14 | 505.98 |
| scan-amd-ddr-threads16-size1024 | 128 | 24.0 | 843.85 | 534.15 | 599.93 |
| scan-amd-ddr-threads8-size1024 | 64 | 24.0 | 431.83 | 364.48 | 401.04 |
| scan-amd-ddr-threadsall-size1024 | 256 | 24.0 | 1039.29 | 563.40 | 644.15 |
| diagnostic-ls-ddr-15-domains | 555 | 22.5 | 623.70 | 424.75 | 480.72 |
| diagnostic-ls-hbw-15-domains | 555 | 22.5 | 4442.63 | 4210.48 | 4202.15 |
| diagnostic-ls-hbw-15-domains-8threads | 120 | 22.5 | 1916.30 | 2347.65 | 2031.29 |
| diagnostic-ls-hbw-15-domains-large | 555 | 45.0 | 4495.01 | 4379.44 | 4209.86 |
| diagnostic-ls-hbw-16-domains-small | 592 | 24.0 | 6185.29 | 5321.47 | 5144.48 |

## 复现与证据

[基准源码](../../benchmarks/hardware/bandwidth-20261105/bandwidth_bench.cpp) ·
[说明](../../benchmarks/hardware/bandwidth-20261105/README.md) ·
[汇总JSON](summary.json) · [全部逐轮数据](samples.csv)

[灵晟完整原始证据](lingsheng-evidence.tar.gz) · [9755完整原始证据](amd9755-evidence.tar.gz)

远端目录：灵晟`/home/share/nsls_lwb/.cache/hardware-bandwidth-v20261105`；
9755`/public2/home/lwb_720/.cache/hardware-bandwidth-v20261105`。
源码只新增独立硬件微基准，没有修改求解器。
初次maxnode过窄的mbind、缺少NUMA开发包、未分配HBM的作业和旧SDK分类混合样本均排除，
不把绑定失败、HBM不可用或未完成状态当作带宽零值。
