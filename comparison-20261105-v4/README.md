# 单source、单组态优化实验

用户取消多个源点分组，只调优单source、单组态的完整12列。
共同一次stout后组态、原点单位源、相对残差阈值1e-8、592核。
纯求解为完整12列原生求解API墙时，setup/读写另计；每个模式测一次。

当前实现是混合精度：预条件器和外层工作向量主要FP32，可靠解累计及完整残差FP64。
LQCD_OUTER_FLOAT=0采用FP64外层GCR，但预条件器仍FP32，且底层批求解退化为
逐列调用。因此增加mixed-single作为单列混合精度对照，避免把批处理差别全归为精度。
Double外层仍然需要按实测选择，不因硬件FP64峰值高就默认更快。

baseline：LQCD_OUTER_FLOAT=1，batch2。
double-outer：LQCD_OUTER_FLOAT=0，batch2入口但内部逐列。
mixed-single：LQCD_OUTER_FLOAT=1，batch1。
每个独立进程使用同轮相同已测试库，分别建层，模式设定在进程启动前。全部源列零初值。
普通计时verbose0；后续必要的阶段诊断另测，不混入普通计时。
profile155提示线程等待和fine/local热点，精度实验用于确定方向。

实际顺序：`outer-precision.md`、`reliable-fusion.md`、`sap-schedule.md`。
后两轮分别测试FP64可靠残差融合，以及有效颜色块调度与单source内块/列任务展开。
实验开关默认关闭；旧稳定版保留，不能因数学等价或测试通过就宣称更快。

## 框架与复现

站点根目录`/home/share/nsls_lwb/.cache/fair-solve-20261105-v4`。
复用已有`tools/optimization/worker.py`任务队列与`tools/run_numa.py`NUMA绑定。
`build_outer.sh`、`build_reliable.sh`、`build_sap.sh`固定各轮提交，计算节点native编译。
`sequence_validated.py`、`sequence_reliable.py`、`sequence_sap.py`顺序执行，测试失败即停止。
任务与输出目录只允许新身份创建；恢复时先读状态，不能覆盖关闭的记录。
`compare_modes.py`比较全部12列；`validate_reliable.py`和`validate_sap.py`还运行
独立原标量C++程序检查全部12列的真实残差。

第一版`run_outer_mode.sh`使用生产API不允许的NATIVE变量，在数值计算前失败；
正式执行`run_outer_validated.sh`，新增经集合校验的LQCD选项，没有绕过保护。
失败记录保留。`evidence/`保留日志、计时、残差、清理状态和构建证据。
全部秩的完整传播子和大组态留在超算，排除在Git小文件归档之外。
可写经验在本目录及`experiments/lingsheng-20261103/`，官方资料skill保持只读。
