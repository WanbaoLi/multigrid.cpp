# 新自产输出的发布边界：准备版本，未执行HPC实验

`phase7_publication.py` 和 `phase7_cold_entry.py` 是独立新协议，不修改冻结的
`file_integrity.py`、v4验证器、cold程序或其时钟，也不用于挽救092的失败冷样本。

触发依据是092实际观测：新传播子已写出并由所有rank加入，第一次定长读取满足
精确字节数、空EOF、双SHA一致，但读前后mtime/ctime变化约10.87毫秒。原严格
读取正确拒绝，原cold报告尚未发布样本，不能把该次读取或该轮冷时间改成通过。

新协议只适用于本次新进程自产的 `NEW_OUTPUT/propagator.npy`，且此前没有发布
其期望摘要。入口要求原始输出路径不存在、没有最终或父级符号链接；整个cold主程序
通过原冻结adapter执行。回调发生在原cold/API时钟已经停止之后，参考数据和其他
文件读取直接交给原strict实现。已经有expected摘要时明确拒绝调用本协议。

最多进行三次完整读取：

1. 首次strict通过时，直接发布该strict结果。
2. 首次strict拒绝时，只有mtime/ctime变化这一种失败可以继续：设备、inode、
   长度恒定；初始path/FD一致、末尾FD/path一致；精确总字节和空EOF；两种摘要
   对相同字节一致；原strict错误必须仅是身份稳定门失败。该读取保持失败，并在
   下一次读取前把不可覆盖、已fsync的unpublished收据写到新文件。
3. 随后必须两次完整strict读取都通过，摘要都与首次未发布候选相同；两个完整窗口
   的四个path/FD metadata都必须与首次拒绝结束metadata完全相同。任何字节、长度、
   inode、EOF、算法差异或再次时间戳变化立即终止，不进行第四次读取。

每个进度收据单独保留，终态另写 `receipt.json`；`protocol.json`记录每份进度SHA、
入口/协议/原adapter/strict reader的SHA和实际调用次数。原数据和时间戳完全不写。
没有sleep、metadata-only采信、改写旧expected或将首次拒绝改成通过的行为。

发布以后，原v4独立验证器仍以发布摘要进行原strict PRE/POST读取、12列独立C++
残差和gold对照。输入/gold/已有输出的验证没有metadata容错。控制与候选的新冷样本
都必须使用同一发布协议；这些读取、收据和验证不进入冷/API计时。

本地验证：`python -m unittest discover -s work -p test_phase7_publication.py`。
WSL/Linux10项全部通过；Windows8项通过，2项生产`os.pread`入口测试明确跳过。
覆盖首次strict通过、首次纯时间戳拒绝后的两个稳定窗口、读取次数上限、inode/长度/
字节/EOF/算法变化拒绝、二次时间戳变化拒绝、expected存在拒绝、首拒绝中断前持久化、
真实小文件入口与不可变输入隔离、实际entry三读分支及4份进度SHA、输出重复和
dangling symlink拒绝。没有运行求解器
或声称HPC发布协议已验证。
