"""Rebuild the short resource-request report from archived acceptance JSON."""
import json
import statistics
import sys
from pathlib import Path
import matplotlib
sys.stdout.reconfigure(encoding='utf-8')
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/assets/lingsheng-report'
OUT.mkdir(parents=True,exist_ok=True)
font=Path('C:/Windows/Fonts/msyh.ttc')
if font.exists():
    font_manager.fontManager.addfont(str(font))
    plt.rcParams['font.family']=font_manager.FontProperties(fname=str(font)).get_name()
plt.rcParams.update({'axes.unicode_minus':False,'font.size':11,'axes.spines.top':False,'axes.spines.right':False})
blue='#2266aa'; orange='#df8e36'
records={}
for machine in ('lingsheng','node5005'):
    for length in (24,32):
        r=json.loads((ROOT/f'experiments/single-node-health-20261113/{machine}-L{length}.json').read_text(encoding='utf-8-sig'))
        records[machine,length]=r
def pure(r,key):
    return statistics.median(s['native_solver_seconds'] for s in r[key+'_samples'][1:])
def save(fig,name):
    fig.savefig(OUT/name,dpi=170,bbox_inches='tight',facecolor='white')
    plt.close(fig)

fig,ax=plt.subplots(figsize=(12,3.3)); ax.axis('off')
labels=['规范场读取\n一次 stout smear','Clover 构造\n多重网格建层','复用层次\n单 source 的12列','FP64 真残差\n独立标量验证']
for i,label in enumerate(labels):
    x=.02+i*.25
    ax.add_patch(FancyBboxPatch((x,.48),.20,.34,boxstyle='round,pad=0.015',facecolor='#eaf2fb',edgecolor=blue,transform=ax.transAxes))
    ax.text(x+.1,.65,label,ha='center',va='center',transform=ax.transAxes)
    if i<3: ax.annotate('',xy=(x+.24,.65),xytext=(x+.21,.65),xycoords='axes fraction',arrowprops={'arrowstyle':'->','color':blue})
ax.text(.5,.25,'求解核心：SAP块内 Wilson–Clover ｜ 限制/插值 ｜ 粗网格求解\nARM SVE向量化 ｜ MPI边界交换 ｜ OpenMP/NUMA绑核 ｜ KUPL热数据分配',ha='center',va='center',transform=ax.transAxes)
ax.set_title('项目自研 CPU 多重网格：一次预处理，多次复用求解',pad=14)
save(fig,'workflow.png')

fig,axes=plt.subplots(1,2,figsize=(13,3.8))
for ax,key,title in zip(axes,('single','twelve'),('预热后单列纯求解','预热后完整12列纯求解')):
    for j,(machine,label,color) in enumerate((('lingsheng','灵晟单节点',blue),('node5005','AMD EPYC 9755 128-Core × 2',orange))):
        vals=[pure(records[machine,n],key) for n in (24,32)]
        bars=ax.bar([i+(j-.5)*.34 for i in range(2)],vals,width=.32,label=label,color=color)
        ax.bar_label(bars,fmt='%.2f',padding=3)
    ax.set_xticks([0,1],['24³×64','32³×64']); ax.set_ylabel('秒'); ax.set_title(title)
    ax.margins(y=.25); ax.legend(fontsize=9); ax.grid(axis='y',alpha=.15)
fig.suptitle('单节点对比：均16 MPI；灵晟32线程/MPI，AMD 12线程/MPI',fontsize=11)
fig.tight_layout(rect=(0,0,1,.94)); save(fig,'performance.png')

sizes=[(24,64),(32,64),(64,128),(64,256)]
volumes=[n**3*t for n,t in sizes]
fig,axes=plt.subplots(1,2,figsize=(11,3.5))
for ax,values,title,unit in ((axes[0],[v/volumes[0] for v in volumes],'格点总量：相对24³×64','倍'),(axes[1],[v*192*12/2**30 for v in volumes],'仅一个 source 的12列 FP64 输出','GiB（全局合计）')):
    bars=ax.bar(range(4),values,color=[blue,blue,orange,orange]); ax.bar_label(bars,fmt='%.2f',padding=3)
    ax.set_xticks(range(4),[f'{n}³×{t}' for n,t in sizes]); ax.set_title(title); ax.set_ylabel(unit); ax.margins(y=.25)
fig.tight_layout(); save(fig,'volume.png')

fig,ax=plt.subplots(figsize=(10,3.5))
values=[472932,236466,472932,236466]
bars=ax.bar(range(4),values,color=[blue,orange,orange,orange])
for bar in bars[1:]: bar.set_hatch('//')
ax.bar_label(bars,labels=['472932\n实测峰值','236466\n等比预测','472932\n等比预测','236466\n等比预测'],padding=4)
ax.axhline(480000,color='#b64242',linestyle='--',label='每节点申请内存480000 MB')
ax.set_xticks(range(4),['64³×128\n2节点','64³×128\n4节点','64³×256\n4节点','64³×256\n8节点'])
ax.set_ylabel('每节点内存（调度器 MB 口径）'); ax.set_ylim(0,630000)
ax.set_title('以C64两节点记录为基准的容量预测（不代表已完成求解）')
ax.legend(loc='upper right',fontsize=9); save(fig,'memory.png')

rows=[]
for machine,name in (('lingsheng','灵晟单节点'),('node5005','AMD EPYC 9755 128-Core × 2')):
    for n in (24,32):
        r=records[machine,n]
        rows.append(f'| {name} | {n}³×64 | {pure(r,"single"):.3f} | {pure(r,"twelve"):.3f} | {r["twelve_summary"]["steady_median_seconds"]:.3f} |')
report='''# 灵晟测试报告

**用途：申请多节点资源开展大格点 LQCD 传播子求解测试。** 求解数据截至2026年11月14日；硬件调度信息于2026年11月15日复核。

## 1. 项目与已完成工作

GitHub：[**WanbaoLi/multigrid.cpp**](https://github.com/WanbaoLi/multigrid.cpp)。
项目实现面向CPU的 Wilson–Clover 多重网格传播子求解，支持x86和灵晟ARM后端，保留独立标量程序进行精度验证。以下性能来自项目自研求解器。

![计算流程](assets/lingsheng-report/workflow.png)

| 灵晟开发与优化 | 当前状态 |
|---|---|
| 实现Wilson–Clover半自旋投影/恢复、SVE向量核与寻址复用，并完成实机验证 | 已完成 |
| 实现SAP块内偶奇Schur预条件、粗网格偶奇求解 | 已完成 |
| 实现每NUMA域一个MPI的绑核方案：单节点16 MPI、求解32线程/MPI，按两列批量处理 | 已完成 |
| 实现MPI halo通信与内部计算重叠、批量归约 | 已完成 |
| 接入KUPL，对部分热数据进行HBW分配，并验证SDK分类及页面驻留 | 已完成 |
| 共享单节点只读系数，完成24³×64、32³×64单列和12列精度及性能验证 | 已完成 |
| 实现多节点本地数据/halo驻留、basis手征零块压缩、建层临时数据释放和Krylov缓存控制，完成两节点C24验证 | 已完成 |
| 完成64³×128多节点建层及预热后1列、12列求解验证 | 未完成 |
| 通过跨向量复用halo页进一步降低内存峰值（已有实验实现，尚未验证） | 未完成 |
| 生成规范场：开发并验证生产用LQCD规范场生成流程 | 未完成 |

## 2. 当前性能与精度

统一16 MPI、零初值、一次stout、复用同一层次；MG/SAP热路径FP32，外部场和完整真残差检查FP64，**相对真残差≤10⁻⁸**。预热后取第2、3次中位数。纯求解不含读取、smear、Clover构造、建层、输出和外部独立验证；API墙钟另计。

| 平台 | 格子 | 单列纯求解/s | 12列纯求解/s | 12列API墙钟/s |
|---|---|---:|---:|---:|
'''+ '\n'.join(rows)+'''

![预热后求解性能](assets/lingsheng-report/performance.png)

灵晟使用32求解线程/MPI，AMD使用12线程/MPI；这是各自现有配置的端到端对照，不能据此单独归因于CPU架构。单节点数据均通过单列及12列独立算子检查，灵晟最大独立残差低于4.9×10⁻⁹。灵晟C24/C32建层分别约224.6/487.8秒，建层可跨source复用。分块分别为6×6×6×4、8×8×8×4。

## 3. 当前限制与优化重点

2026年11月15日复核灵晟计算节点cn12118的调度器信息：双路72F5、16个CPU NUMA域，608个物理核中592个可供应用使用；报告频率为2000 MHz。内存总量578560 MB，系统预留61440 MB，可供应用调度517120 MB，均保留调度器原单位。上述为节点配置读数，不是负载下持续频率、内存带宽或HBM容量实测。

- **主频与控制开销：** 计算节点探针报告最高频率约2 GHz，尚无全核持续频率测量。小矩阵、间接寻址、归约和线程同步依赖单核效率，不能直接用整机峰值浮点算力推算求解时间。
- **HBM使用范围：** KUPL已验证部分热数据进入HBW；当前自设预算为1 GiB/MPI，并非硬件容量上限，原始副本仍保留。C64两节点时每MPI的FP32 basis约2.25 GiB，超过该预算，无法整块放入当前热数据分配策略。尚无“全求解数据驻留HBM”或“带宽已打满”的证据。
- **库与指令：** 使用HPCKit 25.1、HMPI和KUPL，当前热算术主要由项目SVE内核完成；未将KML BLAS/SME作为已验收的主求解路径。粗网格48×48复数小矩阵调用需要同时评估布局转换、调用开销和线程嵌套。
- **收敛与通信：** 灵晟C32平均外层迭代约43.6次，C24约24.1次；格点增大和迭代增加共同放大耗时。多节点32进程通信门禁已通过；目前可运行基线使用限定网段的TCP，仍需官方协助验证高性能互连配置。

## 4. 大格点内存与资源申请

![格点与输出容量增长](assets/lingsheng-report/volume.png)

64³×128的格点总量是24³×64的约37.9倍。仅FP64的12列传播子输出就需全局72 GiB；此外还需要规范场、Clover、粗化basis、24个建层向量、Krylov缓存和MPI边界区。传输的薄面元素少，不等于其分块布局触及的驻留页少。

**C64两节点实测：** 已完成读取、smear、规范场装载和首轮24个建层向量；调度器单节点峰值记录为472932 MB，接近申请的480000 MB。随后远端MPI daemon失联，建层未完成；日志未直接确认内核OOM，故只能判断内存余量不足、内存压力可疑。**尚无有效C64单列或12列求解时间。**

容量预测采用：**预计每节点内存＝已测每节点内存×新旧格点总量之比×原节点数/新节点数**。它只作资源规划；实际halo、分块、缓存和建层峰值会改变比例。

![多节点内存预测](assets/lingsheng-report/memory.png)

**本次申请：4个整节点，每节点16 MPI、每MPI 32线程；每节点预留480000 MB内存，首轮墙钟4小时。** 对应64 MPI、2048个计算线程，整节点计费CPU配额约2432（当前限制1216）。采用时间拓扑1×1×1×64、本地格点64³×2、聚合块8×8×8×2。当前均匀时间切分下，3节点的48 MPI不能整除时间长度128，下一档可行配置为4节点。

申请目标：完成64³×128的建层与独立精度验证，测量预热后1列和12列纯求解时间、真实内存峰值，并验证HBW驻留及高性能互连效果。四节点结果尚未实测；进一步降低内存的实验也未作为验收结果。

数据依据：[单节点验收](https://github.com/WanbaoLi/multigrid.cpp/blob/b182d74/docs/single-node-health-20261113.md)、[多节点实验记录](https://github.com/WanbaoLi/multigrid.cpp/blob/b182d74/experiments/distributed-C64-20261114/README.md)。单节点测量版本`efe57de`，C64尝试版本`88e8bbe`；未验证halo页实验位于`codex/c64-halo-pages`。
'''
# Absolute image URLs keep the delivered Markdown usable without a local assets folder.
report=report.replace('(assets/lingsheng-report/', '(https://raw.githubusercontent.com/WanbaoLi/multigrid.cpp/develop/docs/assets/lingsheng-report/')
(ROOT/'docs/灵晟测试报告.md').write_text(report,encoding='utf-8')
print('\n'.join(rows))
print('Generated',ROOT/'docs/灵晟测试报告.md')
