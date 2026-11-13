# Python 调用接口

`lqcd_cpu/` 是当前求解流程使用的 Python 包，调用方式为
`from lqcd_cpu import Solver`。Python 负责读场、stout、组织求解和保存结果；
数值求解由 `Solver` 通过 `ctypes` 调用 C++ 动态库完成。

| 文件 | 职责 |
|---|---|
| `lqcd_cpu/__init__.py` | `Solver`、C ABI 调用、字段布局转换和 MPI 集体调用检查 |
| `lqcd_cpu/io.py` | 读取 LIME 规范场 |
| `lqcd_cpu/smearing.py` | stout 预处理 |
| `lqcd_cpu/propagator.py` | 读场、建层、完整12列求解的工作流程 |
| `lqcd_cpu/propagator_io.py` | 传播子数据读写 |
| `lqcd_cpu/__main__.py` | Python 模块命令入口 |

从项目根目录手动导入时，设置 `PYTHONPATH="$PWD/bindings"`。
`tools/solve_propagator.py` 和 MPI 运行库测试直接使用此包。
