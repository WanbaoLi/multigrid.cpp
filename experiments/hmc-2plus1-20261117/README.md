# 灵晟 2+1 味 Wilson–Clover HMC 首次运行

已完成真实的小体积海夸克加权 HMC，保存4份组态并独立回读验算。
这是精确稠密行列式的算法验证，**不是物理点系综或24格子生产 RHMC**。
实现步骤、公式及生产扩展范围见 [HMC说明](../../docs/hmc-2plus1.md)。

| 项目 | 实测/设置 |
|---|---|
| 时间（北京时间） | 2026-11-17 22:05:02–22:15:18 |
| 灵晟作业 / 节点 | `2155448`，`SUCCEEDED`，cn12038 |
| 测得源码 | `codex/hmc-2plus1-20261117`，`e6659702c5a994158c39ace81439572c32c4a9cb` |
| 资源 | 单进程、申请4 CPU/16000 MB、Torch 2线程、共享节点 |
| 格子 | 2×2×2×2（16格点，Dirac矩阵192×192） |
| 作用量 | Wilson plaquette + 两轻一奇异 Wilson–Clover |
| 参数 | β=5.6，mₗ=0.5，mₛ=0.8，cSW=1，seed=1729 |
| 边界/涂抹 | 规范链接不扭转；费米子时间反周期；无 stout |
| 精度/软件 | complex128/float64 CPU，PyTorch 1.12.1 |
| 积分 | leapfrog，每条长度0.5，10步；Metropolis接受/拒绝 |
| 链 | 80条；前40条指定为预热段；第50/60/70/80条保存 |
| 接受率 | 全链78/80=97.5%；后40条39/40=97.5% |
| 链运行时间 | 453.502 s（不含编译、CTest、最终独立回读） |
| 后40条均值 | plaquette=0.6136133；exp(-ΔH)=1.0027438 |

有拒绝时保留旧场，轨迹号照常前进；文件按固定轨迹间隔保存，没有筛掉拒绝样本。
先验指定40条预热和每10条保存**不证明热化、去相关或有效样本数**。质量未调谐，
格距未设定。共享节点的时间也不用于硬件性能或24格子外推。

## 验证

- 计算节点全部24项 CTest通过；其中9项 HMC检查全部执行，无跳过。
- 规范力、海夸克力、总力的有限差分绝对误差分别约 `2.76e-11`、`1.11e-10`、`1.72e-10`。
- 前后积分的链接/动量误差为 `3.78e-15` / `1.78e-15`；步数4→8时能量误差比为0.24928。
- 4份文件均通过 SciDAC CRC和SHA256；独立 NumPy plaquette与生成记录一致。
- 保存场最大酉性误差 `7.84e-14`，最大 SU(3) 行列式误差 `1.04e-13`。
- 两个质量下，与原有独立 C++ 标量算子作用于随机源的最大相对差 `2.40e-16`。
- 每次作用量评估都检查奇异味行列式为正；不会静默以绝对值替代负的单味权重。

`arm-validation.json`、`configuration-verification.json` 和 `chain-summary.json`
保留上述检查及完整80条接受/拒绝记录；`summary.json` 为紧凑汇总。

第一轮作业 `2155394` 在cn12046上完成编译，但PyTorch 1.12批量矩阵指数使可逆性
误差 `4.48e-12` 超过原阈值 `2e-12`，因此没有生成组态。没有放宽阈值；源码改用
厄米动量的特征分解指数后，第二轮通过。首次诊断保留在
`first-attempt-validation.json`，两次运行源码/目录分开冻结。

## 文件与复现

生成的场、检查点和原始日志保留在源码仓库之外：

- 灵晟：`/home/share/nsls_lwb/lqcd-run/hmc-2plus1-20261117-run02/chain/`。
- 本机：`C:/Users/lwb/.cache/hmc-2plus1-20261117-results/chain/`。
- 下载包：`C:/Users/lwb/.cache/hmc-2plus1-20261117-results/hmc-2plus1-L2-configurations.zip`。

包内含4份 LIME、参数/轨迹记录、独立验算与说明。SHA256、各场身份见
`artifacts.json`；原始日志在上述本机目录的 `raw/` 下，未提交日志或数组。
文件兼容性本轮仅验收项目已有的 SciDAC读取器/CRC，没有宣称通过第三方QIO/PyQUDA互通测试。

精确复现用测得源码提交，提交计算任务（输出目录必须新建）：

```bash
dsub -q q_hpcapp -A common -nn 1 -N 1 -R 'cpu=4,mem=16000MB' -T 3600 \
  --cwd /path/to/external/submission -o /path/to/external/job.log \
  /bin/bash /path/to/frozen/source/tools/hmc/run_ls.sh /path/to/new/output
```

`plan.json` 记录冻结源码位置、提交和资源，`build.sha256` 记录独立C++程序。
入口复用先前已安装的mpi4py 4.1.1/cp310依赖目录，固定HPCKit 25.2.1；
HMC本身是单进程，MPI只用于已有读取器的COMM_SELF校验，没有MG或MPI域分解加速。
