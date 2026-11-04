V2 ordinary full12 controller，准备版本。没有部署、排队、构建、启动求解或产生新的性能成绩。

`halo_v2_trial.py`直接复用已经测试的760666c native ELF，不调用CMake或CTest。冻结的`phase6_halo.py`（SHA3f3537…）作为只读依赖，保留其control、decide、bracket_gate、halo_effect_gate、plan/configuration和coarse_coverage方法；原文件没有修改。新的入口、阶段记录和benchmark路由使用`raw_protocol_derived.py`（SHAa07ccf…）的`benchmark_command`，每个新验证阶段都明确使用derived25b6… helper。该helper只处理已审阅的自产scratch gauge发布边界，prop/gold/固定reference与精度门保持严格不变。

必须直接用Python启动本入口。每个benchmark阶段的argv已经包含一次raw wrapper；不能再通过`raw_controller_v4.py`包裹本入口，否则它会把`--benchmark`参数值识别成第二个入口。本控制器在启动时拒绝已有outer run_stage hook。controller、原3f、factory和所有helper都由外部entry SHA与manifest SHA固定。

执行前需要两份不同性质的真实证据：

- V2的完整ARM full-scope状态及其closed passed/cleanup worker任务。状态必须绑定实际`test_attempt`、760源码manifest、canonical `.so` SHA、所有已通过stage和日志SHA、真实false代码生成检查，以及16/32/64字节的四rank SVE继承长度、库SHA和非零grouped-halo调用。118的codegen-only状态会被明确拒绝。完整测试可以复用原000 passed构建与unit；本控制器本身永不重编或把旧测试时间当性能。
- 新allocation内旧052的完整、独立12列已验证profile状态和closed passed/cleanup任务。主机、allocation、源码/库、物理配置必须精确匹配旧052，且使用新的derived helper。不能复用090/103的旧allocation时间或重标它们的硬件身份。profile只用于瓶颈/实际工作证据，不参加普通排名。

当前真实V2 ARM库为`e24e387876329698070784ce80cf4f9a453f7e6fbe315c3e62f2264377e6c330`，source manifest为`d93dde39cb162bd12c845c05e480b73c49dac5385c0fab368abaf8e43bc9fda7`。118仅完成代码生成及20项CPP CTest（1个AVX512专用项输出SKIP），尚不能提供上述完整ARM MPI/SVE proof。普通试验暂时不能执行，也没有预造full proof文件。

独立campaign默认为`ROOT/campaign-halo-v2-ordinary`；原`ROOT/campaign`、tests-only的`ROOT/campaign-halo-v2`及三个源码树都保持原样。初始化时原字节导入052的source/archive/report/artifact和main best pointer，保留旧absolute path、allocation、时间和验证字段，并写`historical_only`来源proof。历史052只作来源与配置基线，不能冒充新控制样本。所有新候选、控制及诊断均有自己的新完整12列验证。独立campaign可记录本次winner/private best，主campaign best SHA在每阶段前后核对，绝不自动晋升主best。

普通顺序固定为旧052控制A、V2同一进程/同一hierarchy中的halo-off与halo-on、单独新hierarchy的halo诊断、旧052控制B。普通配置各1次完整12列warmup和7次steady；诊断为1次warmup+3次steady+独立verbose求解，全部诊断时间不排名。所有解从零初值开始，每个输出仍由独立scalar C++ reference全12列残差≤1e-8和冻结解相对差≤1e-6验收。实际CPU/NUMA masks、配置、repeat IDs和比较key也必须一致。

采用门完全保留原3f：普通candidate相对A和B均至少快3%，范围必须分离、spread≤10%、A/B漂移≤5%；halo还必须在同binary/hierarchy中相对off具有正且范围分离的增量。诊断必须有真实grouped calls、packed reductions，并覆盖profile已观察到的restart和不同列refresh。额外记录142条独立GCR工作是否逐字段相同；GCR表示广义共轭残差方法，RHS表示独立右端项列。message calls与RHS等效operator工作不同，独立rank-max计时包络不能相加。

初始完整普通组规划floor为4000秒，另留45秒；它不包括已通过的build/tests。重入时逐个核对passed stage/log后扣去已完成普通scope的预算，不重复收取旧6600秒入口。每个新stage仍要求自己的硬timeout+45秒；超出剩余时间返回pending。执行timeout保留原失败stage并标明没有数值判定，不能自动重跑；新allocation必须新profile、新prefix和全套新普通控制。`--resume --resume-reason`仅用于同一controller/source/allocation/配置下复用不含失败stage的已通过检查点，不能更换参数后沿用旧秒数。

实际118机制限制必须保留：false自身栈帧496字节，比V1的576小80，但仍比旧052的448大48；入口64字节先恢复再tail branch。false没有halo字段load或三种grouped helper，MGS（改进Gram–Schmidt）活跃列循环仍29条并保留一次states基址栈load，旧052为28条。没有任何静态计数足以证明端到端收益，因此不能把本准备写成方向已成功。

本地验证包括synthetic正/负full-proof结构、scope误用拒绝、错误库/VL/rank/cleanup/stage拒绝、原3f门的overlap拒绝、单次derived argv与7steady、路径逃逸和Linux实际pread/EOF/双hash。另用真实090/103全部142条记录检查字段名/172restart/427refresh/19746packed reductions，检查旧103实际SVE四rank继承长度与max_width形状，并明确拒绝真实118作为full proof。旧V1的shape回归保持它自己的库SHA，没有重标为V2通过。最初Windows测试只因路径分隔符比较失败，已保留日志并修正测试路径比较；生产数值/门限没有变化。

在Windows工作区复现：`python work/test_halo_v2_trial.py`。Linux独立package复现：`HALO_V2_REVIEW_EVIDENCE=./validation-evidence python3 test_halo_v2_trial.py`。没有安装依赖或运行HPC求解。

未来由root在完整证据生成后填入以下变量，直接作为一个有界serial worker任务运行。`MG_ROOT`是远端实验根目录，`MG_AUX`是本冻结helper目录，`MG_PYTHON`是已验证Python，`MG_PROFILE`与`MG_PROFILE_STATUS`为新profile及其任务状态，`MG_TESTS`与`MG_TESTS_STATUS`为真正完整ARM测试状态及其任务状态；四个对应`*_SHA`是它们事前冻结的实际SHA。`MG_ENTRY_SHA`和`MG_MANIFEST_SHA`来自本package manifest的冻结结果，`MG_HOST`是allocation实际主机。以下变量不是已经存在的full-proof文件或测量成绩。

```bash
"$MG_PYTHON" "$MG_AUX/halo_v2_trial.py" --execute \
  --root "$MG_ROOT" --auxiliary "$MG_AUX" --prefix halo-v2-w7 \
  --profile-state "$MG_PROFILE" --profile-state-sha "$MG_PROFILE_SHA" \
  --profile-status "$MG_PROFILE_STATUS" --profile-status-sha "$MG_PROFILE_STATUS_SHA" \
  --tests-state "$MG_TESTS" --tests-state-sha "$MG_TESTS_SHA" \
  --tests-status "$MG_TESTS_STATUS" --tests-status-sha "$MG_TESTS_STATUS_SHA" \
  --library-sha e24e387876329698070784ce80cf4f9a453f7e6fbe315c3e62f2264377e6c330 \
  --expected-entry-sha "$MG_ENTRY_SHA" --expected-manifest-sha "$MG_MANIFEST_SHA" \
  --expected-host "$MG_HOST"
```

默认不带`--execute`只打印准备计划。没有publisher、自动enqueue或自动profile；actual full-proof与新profile未齐时不得启动普通求解。
