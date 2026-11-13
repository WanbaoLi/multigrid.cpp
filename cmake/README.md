# 构建规则

根目录的 `CMakeLists.txt` 包含这里的两份规则：

- `Tests.cmake`：定义测试可执行程序并向 CTest 注册单元测试、MPI 测试和
  Python 运行库测试。
- `DDalphaAMG.cmake`：在 `LQCD_DD_REFERENCE=ON` 时构建可选 DDalphaAMG
  参考适配器的外部依赖。默认生产构建关闭此选项。

这些 `.cmake` 文件随源码维护。构建时生成的 `CMakeCache.txt`、`CMakeFiles/`
和测试日志属于构建目录，由 `.gitignore` 排除。
