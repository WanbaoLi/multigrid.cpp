node5005 同一 f94/c30 二进制关闭/开启 source-owned coarse assembly 的完整冷启动验收通过。连续计时从读取 canonical prepared fixture 到新建层次后的首次完整12列求解；中位耗时 119.805597788 → 35.541159944 秒，减少 70.3343%，加速 3.370897 倍。全部七个样本保留，包括开启模式的37.786秒样本。

| 测量 | 关闭 | 开启 |
|---|---:|---:|
| 完整冷启动中位秒 | 119.805597788 | 35.541159944 |
| native setup 中位秒 | 112.308311270 | 28.048254719 |
| 首次完整12列 API 中位秒 | 6.243569154 | 6.286511273 |

顺序严格为关闭0、开启0、开启1、关闭1、关闭2、开启2、关闭3。关闭冷样本为 [121.2597652329132, 119.28278489317745, 120.32841068226844, 118.7530347649008] 秒；开启为 [37.786292837932706, 35.425441703759134, 35.541159943677485] 秒。范围完全分离，关闭/开启相对跨度分别为 2.0923%/6.6426%；控制中位漂移 0.6111%，首末漂移 2.1109%，全部通过预设门。

独立进程 warm A/C/B 各1次预热和3次steady，中位数分别 6.190662868、6.196084196、6.138981923 秒。保守最坏候选回归 1.4852%，小于2%门限，证明该次同二进制开关比较通过暖求解非回归门。没有达到暖求解3%晋升门，原canonical old6b/64暖最佳未动；独立cold-selection保留 f94/c30 开启模式。

五个暖进程（两个parent和A/C/B）与七个冷进程都独立检查全部12列。最大独立标量C++真残差 9.169762991574491e-09，门限1e-8；逐列解相对冻结gold的最大误差 9.915888557081041e-08，门限1e-6。所有raw-v4校验通过，canonical prepared gauge SHA固定126d658999367b0ece3801c61cd143542d7db0dddc37ab60e6e668e18faa6834。source manifest e018411c…、实际lib c30f755b…；源提交 f94f27d2a07ff3363bea43c1a3b2ca45277de674。没有以新源码冒充旧库构建来源。

配置固定16MPI、每NUMA两个rank、placement/setup16线程、solve12线程、batch2、block6/6/6/4、seed1024，实际所有16rank CPU/NUMA掩码一致。source-owned是context/setup开关，每个冷样本都新建层次；默认12次homogeneous smooth加2轮各3次adaptive setup不变。修改假设来自真实092闭合profile和事前proposal；此前实际node5005默认24与候选5个CTest及16个两轮basis/stencil精确对照通过，详见相邻setup-source-owned-x86证据。339738624字节粗矩阵按源块唯一写者分担计算，主线程MPI_SUM恢复全局stencil；没有改随机种子、Gram–Schmidt、求解器迭代或浮点阈值。

实际rank0/8运行库映射在同epoch两个parent暖进程的setup前20秒内抓取，另用保守setup结束下界核对；并非声称逐个冷PID都被采样。GOMP/MPI/stdC++/glibc文件路径、严格双SHA及startup loader环境一致，runtime gate通过。observer识别实际libc-2.28.so，未把libcrypto或伪libc名称当glibc。runtime proof SHA67b80c6ad75755d5d15560b5f3844a8d808c258b8f85c80045900d4d82aeedd9。

这是预处理canonical场到首次12列的冷层次指标，未从原LIME重新stout。实际raw-LIME入口另见 ../raw-cold/report.md（old6b，124.976906秒）；不能把本35.54秒标成已测raw-LIME结果。OS/存储缓存不受控，没有drop_caches；时钟排除Python/MPI启动、source/library检查、输出数组、析构和独立验算。各阶段独立rank最大值不能相加重建连续冷计时。

节点由用户授权直SSH使用；Slurm显示DOWN*且无队列任务，未获得调度器独占，因此仍标记nonexclusive。bounded task rc0、精确task tag无存活进程、worker PID3651059已退出。worker在idle边界输出实际终止marker，STOP在其后写入；第一次清理脚本只认更窄日志措辞而拒绝，后按真实worker源码marker重核，没有修改任何任务结果或数值证据。

原始元数据、全部逐列日志、读层收据、运行库proof、controller/helpers、ledger、source archives及决策快照在evidence中，数组和二进制不导出。archive SHAa206640487b043d4f62e2d100b5b69f71b4b5a659ca99514d15b307a57f3b9f0，27970个文件逐一校验。summary.json与samples.csv只从这些实际记录归纳。实际命令见evidence中的attempt.json和phase7 state；可执行入口/辅助包保留于远端 /public2/home/lwb_720/.cache/mg-opt-setup-owned-20261104，原ROOT/source和canonical ledger均未修改。
