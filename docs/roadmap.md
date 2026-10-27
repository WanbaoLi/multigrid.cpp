# 第一阶段：自研 CPU + MPI + SIMD Wilson-Clover multigrid

## 不可替代的验收标准

自研生产路径，24³×64真实LIME配置、csw=1、mass=-.277、时间反周期，
每次零初值，完整双精度真相对残差≤1e-8，第二次完整PyQUDA-compatible API<5秒。
Setup、编译、I/O单列；任何外部库包装的速度不算自研成绩。

## 八项小任务

| ID | 任务 | 当前交付 |
|---|---|---|
| S1 | 论文与数值规格 | `native-algorithm.md`；DR基、归一化、gamma5手征聚合、R=P†、Ac=RDP |
| S2 | 公共API与硬件后端分离 | `include/lqcd/lqcd.h`、runtime/registry；生产x86，ARM/SW未实现，DD适配器仅reference |
| S3 | 场布局和内存策略 | PyQUDA EO-x / lex-tzyx，内部block-EO+split-complex，NUMA域绑定和64字节对齐 |
| S4 | 自研x86细格核与SAP | half-spin投影、OpenMP SIMD、Clover逆、块内EO-Schur MR及odd重建 |
| S5 | 自研setup及粗网格 | 随机齐次SAP、手征MGS、近似逆自适应更新、Galerkin粗化、coarse GCR |
| S6 | 完整求解与MPI | flexible GCR、mixed precision+double可靠残差；粗层EO-GCR、本地粗向量、异步t-slab halo及全局归约 |
| S7 | PyQUDA与数值验收 | 真实字段对象、零源/错误路径/生命周期、P†P/RAP、12列独立C++验解 |
| S8 | 88核调优及复现 | 每NUMA一MPI、域内OpenMP；自动2×44核第二次2.302秒；完整结果及限制归档 |

当前结果以 `numa-results.md` / `numa-results.json` 为准。
DDalphaAMG 仅作为可选参考适配器，不定义生产后端或验收目标。

## 后续硬件原则

MPI格点分解、NUMA放置、host线程、SIMD宽度、从核执行分别配置。
AMD 9755必须按实际拓扑扫描；256核不是256个几何MPI ranks。
灵晟如果每CPU确为8 NUMA×38核，双路是16个NUMA；16×36、8×36是不同候选，
必须测量并保留halo/粗层分解约束。神威48个从核不等同48个OpenMP线程。
目前x86实测通过不代表ARM/SW已支持。

## 后续工作（不混入本阶段完成声明）

MPI setup资产仍复制，double验证仍收集全场；消除副本和推广4D分解后才能
评估多节点规模。ARM/SVE/SME和SW从核后端尚待实现。当前只实现两层、csw=1、
反周期时间、单活上下文；其他模式显式拒绝。保留独立reference求解器作oracle。
