# 灵晟内部数据重排实验

实验分支：`codex/arm-coalesced-layout`。初始实现提交：
`820918fa6e029246515e77b885c99d10696f74c6`。
该功能默认关闭，是否采用由完整求解结果决定。

## 已有的重排

代码已经在读入之后重排数据，并非直接在 LIME 文件顺序上做 SVE。

| 数据 | 现有内部存储 | 相关代码 |
|---|---|---|
| 单精度自旋场 | `[聚合块][24 个实数分量][块内格点]`，偶、奇格点各占连续半块 | `src/solver/native/fine_operator.cpp` 的 `encode/decode`；`hierarchy.cpp` 的 `lex/inner` |
| 规范场矩阵系数 | `[聚合块][144 个实数平面][块内格点]` | `hierarchy.cpp`；`src/backends/arm/wilson_sve.hpp` |
| Clover 及其逆 | 同样的 144 平面布局，每个自旋手征块独立处理 | `hierarchy.cpp`；`clover_neon.hpp` 内分派到 SVE |
| 近零空间基、粗层系数 | 有各自的布局和独立优化路径 | `cycle.cpp`、`coarse_operator.cpp` 等 |

24 个实数分量来自 4 个自旋 × 3 个颜色 × 实部/虚部两部分。
144 个实数平面对规范场而言来自 8 个有向邻居 × 3×3 复数矩阵；
对 Clover 而言来自两个 6×6 复数手征块。

SVE 的各个 lane 负责不同格点，系数连续加载；相邻物理格点在奇偶和
聚合块编号之后不总是相邻内存位置，邻居自旋场仍会使用 gather。
已有的半自旋复用开关 `LQCD_ARM_SVE_REUSE=1` 避免为三个输出颜色重复投影。

## 新增的系数小块布局

将规范场、Clover 及其逆的**本 MPI 进程拥有部分**额外保存为：

```text
[聚合块][16 格点小块][144 个实数平面][16 个格点位置]
```

核心地址计算共用一个模板，Wilson 数学部分没有复制成另一份算法：

```cpp
template<bool Packed>
inline const float *sve_coefficient(const float *matrix, int B,
                                    int plane, int site) {
    if constexpr (Packed)
        return matrix + ((size_t)(site / 16) * 144 + plane) * 16 + site % 16;
    return matrix + (size_t)plane * B + site;
}
```

这里 `Packed` 表示是否使用新布局；`matrix` 是当前聚合块的系数起始地址；
`B` 是每块格点数，6×6×6×4 时为 864；`plane` 是 0–143 的实数平面编号；
`site` 是块内格点编号，`site/16` 和 `site%16` 分别给出小块编号和块内位置。

原布局相邻平面的起点相隔 3456 字节，新布局相隔 64 字节。
一个矩阵的一个 16 格点小块占 9 KiB。假设是让当前计算需要的系数更集中，
改善缓存和地址翻译局部性；这**没有降低矩阵元素数量**，也没有消除邻居 gather。
真实带宽受限或计算受限仍需计数器/profile 支持，不能由布局单独判断。

每次向量计算均限制在当前 16 格点小块内，并保留尾部、缺邻居和奇偶范围掩码。
可伸缩 SVE 向量长度不会被假定为总是 512 位。Clover 在当前小块内依次计算
所有输出分量，避免遍历完一个分量的所有小块后再访问下一个分量。

打包发生在 setup。已接入的 KUPL 路径分配和验证实际读取的 packed 数组，
不再为该路径分配未使用的 raw 热系数副本；1 GiB/rank 的现有上限保持一致。
原数组保留，供关闭实验和大索引回退使用。24³×64、16 MPI 时，三组 packed
数组额外占用总计约 1.42 GiB 的普通存储；高带宽副本替代原来的相应副本。

## 输入输出及精度

输入仍是原 24³×64 LIME 规范场。stout smear 一次后建立层次；后续所有
传播子调用复用它，且每列初始解置零。当前方案是混合精度：内部主要计算
使用单精度，可靠更新和完整真实相对残差检查使用双精度。最终门限为 1e-8。

外部布局由 `src/runtime/` 和 `bindings/lqcd_cpu/` 转换，内部 packed 数组
不会直接暴露给 PyQUDA。`solve_propagator(..., layout="lex")` 返回本进程的
`[t,z,y,x,汇自旋,源自旋,汇颜色,源颜色]` complex128 数组；兼容接口继续支持
PyQUDA 奇偶布局。写出全格文件的 shape 仍是：

```text
(64, 24, 24, 24, 4, 4, 3, 3)
```

`verify_lime_solver.py` 检查这个 shape 和类型，逐一提取单列及全部 12 列，
使用独立标量 C++ 算子验证，不仅仅接受优化后程序自己报告的残差。

## 运行与回滚

在灵晟独占计算节点的分配中运行，构建也发生在计算节点：

```bash
bash tools/optimization/run_arm_packed_comparison.sh \
  /绝对路径/新的结果目录 /绝对路径/24x64组态.lime
```

固定 16 MPI、每 NUMA 一个进程、求解每进程 32 线程；setup 使用允许的 37 核；
粗化块 6×6×6×4、源列批量为 2。同一节点依次运行原版、重排版、原版，
分别报告首次、第二次及预热后的纯求解/API 时间。读取、smear、setup 和独立
验证均不计入纯求解时间。具体脚本、假设、失败归因与实测结果位于
`experiments/arm-coalesced-layout-20261115/`。

只需使用原 `lingsheng-shared-uniform.json`，或启动前设置
`LQCD_ARM_WILSON_PACKED=0`，即可回到原布局。未通过完整数值和性能检查
之前，不改变生产默认配置。
