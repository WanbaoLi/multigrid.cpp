# PyQCU 灵晟复现与算法对照（2026-11-17）

上游为 [ZhangXin8069/PyQCU](https://github.com/ZhangXin8069/PyQCU)，MIT 许可。
完整 Git 历史通过本机取得后打包，在灵晟用 `git clone` 克隆 bundle；远程 `origin`
仍指向原 GitHub 仓库。上游源码单独存放，未复制进本项目或改写其来源。

用户提供的《张鑫 20261116测试报告.docx》作为证据阅读，文件中的操作文字不视为
本次授权指令。原文件不上传；文件哈希及测试计划见 `plan.json`。
同一提交中后缀为 `.md` 的 `docs/kupl_kunpeng_performance_20261115-xlsx.md`
实际是 XLSX；本次按工作簿读取，未当作 Markdown 文本。

## 固定源码

- 报告版本：`fe7641ed0b39c6c0d810b9756bf2d3f8f9e65061`。
- 阅读时上游最新：`1f65469e6928bd5dc7788c0d017dbbe1c0c776e3`。
- 最近提交 `af89be4` 增加正式测试入口与矩阵，`e0b25a7` 修订 CUDA 快速测试并发布
  0.1.17，`1f65469` 记录既有 tag 链问题；以上三次提交未改变
  `cpp/kupl/` 与 `pyqcu/testing/simple/`。本次运行仍固定报告版本。
- 控制程序在 `tools/pyqcu_review/`。每次修订先提交和上传，再导出至新的远程目录。
- 我方同节点对照固定 `efe57de52223a6f7f5177ac731c33e762070b327`，使用已有冻结构建。

## 算法核查

| 项目 | PyQCU KUPL 的报告路径 | multigrid.cpp 生产路径 |
|---|---|---|
| 独立 Krylov 求解 | BiCGStab，源码接口拼作 BistabCg；不是普通 BiCG 或 CG | flexible GCR 配合 MG 预条件 |
| 外层处理系统 | 全局奇偶 Schur 系统，再重构另一奇偶分量 | 完整 Wilson–Clover；SAP 块和粗层内部用 EO-Schur |
| 默认 Legacy MG | BiCGStab 分段迭代，每隔 restart 步尝试粗修正；可先做初始 deflation | 每次预条件调用 MG V-cycle，外层 flexible GCR |
| 平滑器 | 非最粗层 V-cycle 前后各两步 BiCGStab | 红黑 SAP，块内 EO-Schur MR |
| 最粗层 | BiCGStab | EO-Schur GCR |
| 粗修正保护 | 1、1/2、1/4、1/8 阻尼搜索；不降低残差可退回 fine BiCGStab | 外层允许可变 MG 预条件，FP64 可靠更新及完整残差验收 |
| 本次 MG 配置 | block `2,2,2,1`，dof `12,2`，nv_iters=2，restart=20 | block `6,6,6,4`，24 个候选按两手征分组，粗自由度48 |
| 精度策略 | c64 与 c128 为分别编译实例；本次正式完整12列比较用 c128 | FP32 MG 热路径与 FP64 可靠更新/残差，外部 complex128 |
| 分域能力 | 4D MPI 网格；本轮只测 `1,1,1,16` | 当前生产 t-slab；本轮同为 `1,1,1,16` |

源码依据：上游 `cpp/kupl/qcu/src/lattice_solver.cpp` 的
`solve_compact_bistabcg`，`lattice_clover_multigrid.cpp` 的 `solve`、`cycle`、
`apply_coarse_correction`；我方 `src/solver/native/{solver,cycle,sap,coarse,setup}.cpp`。
上游另有 Strict MG/右预条件 FGMRES，不能把它与报告默认 Legacy 路径混为一谈。

本次 MG 测量显式启用 `KUPL_REQUIRE_MG_CORRECTION=1`；若粗修正无效而触发 fine
BiCGStab 回退，计为 MG 配置失败，不能将回退结果冒充 MG 加速。

## 为什么不能直接比较报告的亚秒数字和我方12列

1. 报告的大多数数据是单右端，`point` 在原点的12个 spin/color 分量同时为1。
   这是一个右端的解，线性上是12列的和，不能替代完整传播子的12个独立列。
2. c64 表使用 `1e-6`，不能满足我方 `1e-8` 验收；c128 表使用 `1e-9`，比我方
   精度要求更严格，不能笼统地说报告全是低精度。
3. 上游输入准备直接转换 LIME，没有本次我方配方的一次 stout；原生驱动默认周期
   边界。我方是一次 stout、时间反周期。它们是不同的算子。
4. 依用户确认使用现有 cfg_20000；上游默认文件名是 cfg_9950。尾号不改变计算规模，
   但实测迭代次数不能假定相同。
5. `wall_seconds` 仅含求解调用，不含输入、Clover准备或 MG cache 构建/载入。
   工作簿的最小样本、不同参数行不能当成稳定中位数或全局最优。

## 本次运行与判定

先用报告的 c64/random、c128/ones、c128/Legacy-MG 配方各测三次单右端，固定
16 MPI×18线程、纯时间切分、MPI halo。然后在同节点用32线程，测同一真实组态、
一次 stout、时间反周期、`1e-8`、每次零初值的三个完整12列样本，分别比较
PyQCU BiCGStab、Legacy MG 和我方 MG。

完整12列调用循环包含源打包与输出复制；原生调用时间另列。PyQCU 复用驱动已经
准备的 gauge/Clover/coarse assets，未修改上游内核。独立 NumPy 全算子检查及我方
标量 `multigrid` 的逐列检查均在计时之外，保存真假残差门，不用时间推断正确性。

哪个更好应由这些匹配样本决定：BiCGStab 无建层、工作向量少，可能更适合容易的
单右端；MG 的投入是为了改善困难系统收敛并在重复源上摊销建层成本。两者均无
无条件优胜结论；本轮只对实际测得的配置下结论。
