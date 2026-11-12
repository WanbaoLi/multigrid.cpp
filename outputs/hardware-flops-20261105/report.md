# 灵晟与 EPYC 9755 单核、整节点 FP32 / FP64 实测

2026-11-05，独立寄存器FMA微基准，以下均为三轮中位数；不是理论规格峰值、
LINPACK、GEMM或格点求解器的实测吞吐。FMA按每个活跃lane一次乘加计2 FLOPs。

| 测量范围 | 实际物理核数 | 单精度 FP32 | 双精度 FP64 |
|---|---:|---:|---:|
| 灵晟单核 | 1 | 99.200 GFLOPS | 49.600 GFLOPS |
| 灵晟单节点可用核 | 592 | 58.129 TFLOPS | 29.060 TFLOPS |
| EPYC 9755 单核 | 1 | 263.922 GFLOPS | 131.949 GFLOPS |
| EPYC 9755 单路 | 128 | 26.957 TFLOPS | 13.474 TFLOPS |
| EPYC 9755 双路节点 | 256 | 51.650 TFLOPS | 26.380 TFLOPS |

1 TFLOPS = 1000 GFLOPS = 10^12 FLOP/s。单核结果已经使用该核的全部SIMD lane。
9755单核FMA约为灵晟单核的2.66倍，但灵晟可用核更多，因此两端整节点吞吐接近。
这些数值不能直接推算Wilson–Clover/MG速度：内存带宽、访问布局、通信、同步和
算法迭代数均未由本基准覆盖。

## 硬件与运行边界

- 灵晟计算节点`cn19473`，Donau作业2040261。系统在线608物理核、2socket、
  16个CPU NUMA域；作业允许每域37核，总592核。本报告未把592核乘比例包装成608核实测。
  单核选择CPU16；每个worker实际SVE向量长度64字节，FP32为16lane、FP64为8lane。
- node5005：2×AMD EPYC 9755，每颗128核，总256物理核，8 NUMA域，SMT关闭。
  单核选择CPU16；单路测试使用一个实际socket的128核，双路使用256核。
  实际执行AVX512 FMA。通过SSH直接运行，没有排他调度分配；开始时load为[0.41, 0.31, 0.28]。
- 两端均在实际目标节点`-O3 -std=c++17 -pthread -march=native`本机编译；没有fast-math。
  灵晟使用Bisheng Clang19.1.7，9755使用GCC14.4.0。精确版本、二进制hash和动态依赖在metadata。
- CPU前后频率快照已保留，但未作为负载期间平均频率。单核boost和全核频率可能不同。

## 算法、计数与校验

基准在寄存器中使用多个独立累加器，ARM为24个、AVX512为16个。每轮先加后减精确
二进制常数，所有lane最终必须精确回到1，checksum为非零且最大误差为0。
`asm volatile`保证这些FMA没有被编译器消掉。各worker逐个绑定一个物理核，
每轮开始和结束的实际CPU均核对，所有case都PASS。

反汇编验证：SVE FP32/FP64内层各48条向量FMA；AVX512内层各32条。
计时循环内无load/store、无溢出寄存器栈访问。每worker操作数为
`iterations × accumulators × 2遍 × SIMD lane数 × 2 FLOPs`。
整节点吞吐按全部线程准确操作数之和除以最早开始到最晚结束的墙时计算，
包含启动偏差和线程被抢占的影响；没有把单核结果直接乘核数。

每case先校准预热，再保留3轮、每线程目标约2秒。线程创建、绑核、校准和结果校验
不计入kernel时间，kernel初始化及末尾保存寄存器结果包含在内。
各worker独立校准，工作量可能不同，因此该结果是此负载的整体实测吞吐，
不保证等于厂商硬件理论最大值。未测SME矩阵运算或任何GPU。

## 所有样本

下表统一以GFLOPS表示。9755双路FP32三轮有可见波动，全部保留，未删除慢样本。

| 平台 | 范围 | 精度 | 三轮 GFLOPS |
|---|---|---|---:|
| lingsheng | single_core | fp32 | 99.200 / 99.200 / 99.200 |
| lingsheng | single_core | fp64 | 49.600 / 49.597 / 49.600 |
| lingsheng | all_allowed_physical_cores | fp32 | 58128.803 / 58125.328 / 58674.820 |
| lingsheng | all_allowed_physical_cores | fp64 | 29060.497 / 29061.368 / 29058.243 |
| amd9755 | single_core | fp32 | 263.922 / 263.870 / 263.942 |
| amd9755 | single_core | fp64 | 131.950 / 131.949 / 131.945 |
| amd9755 | one_socket | fp32 | 26957.310 / 26899.265 / 27009.379 |
| amd9755 | one_socket | fp64 | 13473.519 / 13481.359 / 13415.827 |
| amd9755 | all_allowed_physical_cores | fp32 | 51649.883 / 48340.760 / 52938.748 |
| amd9755 | all_allowed_physical_cores | fp64 | 26252.018 / 26379.759 / 26451.115 |

## 复现和证据

- [基准源码](../../benchmarks/hardware/fma-20261105/fma_bench.cpp)
- [运行说明](../../benchmarks/hardware/fma-20261105/README.md)
- [机器可读汇总](summary.json)、[逐轮计数和同步偏差](samples.csv)
- [灵晟原始证据](lingsheng-evidence.tar.gz)、[9755原始证据](amd9755-evidence.tar.gz)

原始证据包含源码、运行脚本、JSON、全部worker计时/亲和/checksum、反汇编和编译信息。
灵晟远端目录`/home/share/nsls_lwb/.cache/hardware-flops-v20261105`；
9755目录`/public2/home/lwb_720/.cache/hardware-flops-v20261105`。
前置探测作业2040175因环境没有默认g++、在编译器查询处退出，不计入性能样本。
正式作业显式指定clang++后完整成功。
