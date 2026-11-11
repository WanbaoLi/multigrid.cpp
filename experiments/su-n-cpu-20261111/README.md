# 论文 SU(N) CPU 原型

论文引用的公开代码是 `sunw`，仓库地址为
`https://github.com/sunwayihep/sunw`，本地固定提交
`95c31d65a4de683849f83c168eddb236e5c6b4fc`。`sunw`负责 SU(N) Wilson 规范场
生成，原始 Makefile 默认 CUDA；它不是论文多右手 Dslash 求解器的完整源码。

本目录实现一个独立 CPU 原型，先验证论文第四章的核心计算模型：

- 规范场 `U` 支持任意颜色数 `N`，每个格点有四个正向链接；
- 费米子场支持任意右手数 `R`，字段为 `R × 4 × V × N`；
- `apply_independent` 逐个右手计算；
- `apply_fused` 在同一格点、方向和颜色循环中复用规范矩阵，内部处理多个右手；
- 单位规范场上两种实现逐元素比较，误差要求 `1e-14`。

这里的 `N` 是颜色数，`R` 是右手数量，`V` 是格点总数。它们不是同一个量。
原型采用双精度复数和 DeGrand–Rossi 自旋基；支持单位场、随机 SU(N) 链接和
二进制 SU(3) 规范场输入，用于验证算子与多右手计算模式；`sunw` 仍负责物理
SU(N) 组态生成。

## node5005 编译和运行

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j8
./build/sun_cpu --self-test
./build/sun_cpu 3 12 64 3 24 24 24 64 random operator
./build/sun_cpu 3 12 64 2 24 24 24 64 gauge-su3.bin propagator -.277 prop
```

命令参数依次为 `N`、`R`、OpenMP 线程数、总重复次数，以及 `Lx Ly Lz Lt`；
最后可选规范场文件、模式和质量参数。`operator` 输出融合 Dslash 计时，
`solve` 输出合并 BiCGStab，`propagator` 对每个右手保留独立 Krylov 历史。
`propagator` 的完整12列结果才是传播子参考实现；融合 Dslash 的局部速度不是
完整传播子加速比。

## 当前边界

论文的 CUDA Batched GEMM/Tensor Core 路径不能直接搬到 EPYC CPU；node5005
使用 AVX-512 和 OpenMP。下一步处理 `sunw` 原生输出格式、block Krylov，
以及与 `multigrid.cpp` 独立实验后端的接口。

不会把这个原型直接替换现有 SU(3) 生产路径，也不会把单位规范场性能当成真实组态传播子时间。

node5005 真实 SU(3) 输入可由已有共同 stout 后场拼成：

```bash
python assemble_gauge.py \
  /home/share/nsls_lwb/.cache/fair-solve-20261105-v4/input/gauge-untwisted.npy \
  gauge-su3.bin
./sun_cpu 3 12 16 3 24 24 24 64 gauge-su3.bin propagator .5 su3-prop
```

这个原型的输入布局是 `[t,z,y,x,mu,row,col]` 的 `complex128` 连续数组；
它只处理 SU(3) 的规范场作为算子输入，颜色数大于3时使用 `random` 生成的
数学 SU(N) 链接。论文引用的 `sunw` 生成结果需要先转换成同一布局，不能直接
把未知文件格式当作可读输入。

node5005 真实 SU(3) 结果：24³×64、12列、64线程、质量 `-0.277`，独立
BiCGStab 两次为 32.665 秒和 30.927 秒；最大每列真实残差为 `9.80e-11`。
这是通用 Wilson CPU 参考实现，未使用 Clover 或多重网格。简单共享历史的合并
BiCGStab 在同一组态上触发 `rho breakdown`，因此没有被采用。
