# 单源点单组态优化：外层精度

用户取消多个源点分组，只调优单source、单组态的完整12列。
共同一次stout后组态、原点单位源、相对残差阈值1e-8、592核。
纯求解为完整12列原生求解API墙时，setup/读写另计；每个模式测一次。

当前实现是混合精度：预条件器和外层工作向量主要FP32，可靠解累计及完整残差FP64。
NATIVE_OUTER_FLOAT=0采用FP64外层GCR，但预条件器仍FP32，且底层批求解退化为
逐列调用。因此增加mixed-single作为单列混合精度对照，避免把批处理差别全归为精度。
Double外层仍然需要按实测选择，不因硬件FP64峰值高就默认更快。

baseline：NATIVE_OUTER_FLOAT=1，batch2，当前默认。
double-outer：NATIVE_OUTER_FLOAT=0，batch2入口但内部逐列。
mixed-single：NATIVE_OUTER_FLOAT=1，batch1。
每个独立进程复用原始已验证库，分别建层，模式设定在进程启动前。全部源列零初值。
普通计时verbose0；后续必要的阶段诊断另测，不混入普通计时。
旧版源数值未改；profile155提示线程等待和fine/local热点，精度实验用于确定方向。
