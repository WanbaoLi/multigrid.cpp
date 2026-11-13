# F64P14：64³×128 测试组态

选用文件 `beta6.41_mu-0.2334_ms-0.2030_L64x128_cfg_1000.lime`。

- 来源：`kunshan:/public/home/huzhch_p/Configure_clover/beta6.41_mu-0.2334_ms-0.2030_L64x128/`
- 灵晟目标：`/home/share/nsls_lwb/inputs/F64P14/`
- 原文件大小：`19327493608` 字节。
- 原文件 SHA256：`30790de7907dc66a6555bd62fb276d365aceedb07cb9eb3bc7e567847a250183`。
- LIME 头部：`64 64 64 128`，SciDAC binary record 为双精度；文件名对应的组态参数为 `beta=6.41`、`mass=-0.2334`、`clover=1.140825606017`。

大组态不进入 Git。下列工具以 SSH 别名读取本机凭据，不复制私钥；分块保存在目标文件旁的 `.parts/` 中。必须等待合并后大小与 SHA256 全部匹配，才会发布正式文件名。`.partial` 和 `.parts` 均不是可用输入。发生断线时，重试前重新读取远端分块大小，从已有字节位置继续。同一目标文件只能运行一个续传进程。

从本机项目根目录启动（需 Python 和 SSH）：

```powershell
python -u tools/transfer_lime_parallel.py `
  --source-host kunshan `
  --source /public/home/huzhch_p/Configure_clover/beta6.41_mu-0.2334_ms-0.2030_L64x128/beta6.41_mu-0.2334_ms-0.2030_L64x128_cfg_1000.lime `
  --destination-host ls `
  --destination /home/share/nsls_lwb/inputs/F64P14/beta6.41_mu-0.2334_ms-0.2030_L64x128_cfg_1000.lime `
  --bytes 19327493608 `
  --sha256 30790de7907dc66a6555bd62fb276d365aceedb07cb9eb3bc7e567847a250183 `
  --parallel 4 --chunk-bytes 1073741824 `
  --manifest "$env:TEMP/F64P14-cfg1000-transfer.json"
```

上传完成的依据是正式文件和 `complete=true` 的传输 manifest，以及目标文件的独立 `sha256sum`；本说明中的来源和目标路径本身不表示文件已传完。

当前多节点限制：`src/support/shared_coefficient.cpp` 的共享系数模式明确要求所有 rank 在一个物理节点。普通模式虽然有跨 rank 的 halo/reduction，但 `src/solver/native/backend.cpp` 和 `hierarchy.cpp` 仍为每个 rank 保存全局规范场、Clover、basis 和若干 FP32 数组。关闭共享开关不会自动变成可扩展的内存模型。因此 64³×128 的多节点实测前，要先解决内存分布和节点内共享问题，再做实际内存预算与精度验证；不能直接用当前单节点 health 脚本宣称多节点可运行。
