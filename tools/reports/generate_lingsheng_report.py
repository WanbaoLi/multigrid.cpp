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
sys.path.insert(0,str(Path(__file__).resolve().parent))
from lingsheng_report_sections import sections,resources

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

fig,ax=plt.subplots(figsize=(11,4.5))
bottom=0
for amount,label,color in ((432,'建层FP64 basis及粗halo：约432 GiB','#2266aa'),
                          (216,'24个建层向量及驻留halo：约216 GiB','#df8e36'),
                          (99,'规范场、Clover及halo：约99 GiB','#5c9f83'),
                          (126,'FP32系数/链接/逆矩阵/basis：约126 GiB','#9267aa')):
    ax.bar(0,amount,bottom=bottom,color=color,label=label)
    ax.text(0,bottom+amount/2,str(amount),ha='center',va='center',color='white')
    bottom+=amount
ax.text(0,bottom+20,'约873 GiB\n尚未计入全部临时缓存',ha='center')
ax.set_xticks([0],['64³×128建层阶段主要数据预算'])
ax.set_ylabel('两节点全局合计内存（GiB）'); ax.set_ylim(0,1100)
ax.set_title('当前两节点布局：多重网格主要建层数据的全局内存预算')
ax.legend(loc='upper left',bbox_to_anchor=(1.01,1),fontsize=9)
save(fig,'volume.png')

fig,ax=plt.subplots(figsize=(11,4.1))
# Planning proxy only: the remote host's final peak was lost, so this is NOT
# a measured sum of simultaneous node peaks, nor a completed-solve peak.
baseline=472932*2
for i,(ratio,nodes) in enumerate(((1,4),(5.0625,16),(16,64),(16,128))):
    demand=baseline*ratio/1024**2
    reserve=480000*nodes/1024**2
    a=ax.bar(i-.18,demand,width=.34,color=orange,hatch='//',label='失败前峰值等比推算' if i==0 else None)
    b=ax.bar(i+.18,reserve,width=.34,color=blue,label='申请节点的总内存预留' if i==0 else None)
    ax.bar_label(a,fmt='%.2f',padding=4); ax.bar_label(b,fmt='%.2f',padding=4)
ax.set_xticks(range(4),['64³×128\n4节点规划','96³×192\n16节点规划','128³×256\n64节点规划','128³×256\n128节点扩展测试'])
ax.set_ylabel('整项作业总内存（TiB）')
ax.set_ylim(0,73); ax.set_title('16—128节点规划：大格点容量与强扩展测试（斜线柱均为预测）')
ax.legend(loc='upper left',fontsize=9)
save(fig,'memory.png')

fig,axes=plt.subplots(1,2,figsize=(12,4.7))
for ax in axes: ax.axis('off')
for rank in range(16):
    x=.015+(rank%4)*.24; y=.8-(rank//4)*.19
    axes[0].add_patch(FancyBboxPatch((x,y),.22,.15,boxstyle='round,pad=.008',facecolor='#eaf2fb',edgecolor=blue,transform=axes[0].transAxes))
    axes[0].text(x+.11,y+.075,f'NUMA {rank}\nMPI {rank} · 32线程',ha='center',va='center',fontsize=8,transform=axes[0].transAxes)
axes[0].set_title('灵晟单节点：16个CPU NUMA域 → 16 MPI')
axes[0].text(.48,.03,'显式CPU亲和性；进程之间的CPU集合不重叠',ha='center',transform=axes[0].transAxes,fontsize=9)
for j,(y,label,color) in enumerate(((.76,'MPI本地：64个SAP块',blue),(.52,'红/黑分两轮：每轮32块 → 32个OpenMP线程',orange),(.28,'每线程一个块任务 → SVE跨块内格点运算','#5c9f83'))):
    axes[1].add_patch(FancyBboxPatch((.03,y),.94,.13,boxstyle='round,pad=.012',facecolor=color,edgecolor=color,transform=axes[1].transAxes))
    axes[1].text(.5,y+.065,label,ha='center',va='center',color='white',fontsize=9,transform=axes[1].transAxes)
    if j<2: axes[1].annotate('',xy=(.5,y-.09),xytext=(.5,y-.01),xycoords='axes fraction',arrowprops={'arrowstyle':'->','color':blue})
axes[1].set_title('每MPI内：OpenMP块并行 + SVE格点并行')
axes[1].text(.5,.03,'块数对应已测C24/C32配置；不代表任意格子都相同',ha='center',transform=axes[1].transAxes,fontsize=9)
fig.tight_layout(); save(fig,'parallel.png')

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
| 完成4—128节点大格点适配、精度验证及扩展性测试 | 未完成 |

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

数据依据：[单节点验收](https://github.com/WanbaoLi/multigrid.cpp/blob/b182d74/docs/single-node-health-20261113.md)、[多节点实验记录](https://github.com/WanbaoLi/multigrid.cpp/blob/b182d74/experiments/distributed-C64-20261114/README.md)。单节点测量版本`efe57de`，C64尝试版本`88e8bbe`；未验证halo页实验位于`codex/c64-halo-pages`。
'''
# Absolute image URLs keep the delivered Markdown usable without a local assets folder.
background,design,tests=sections(ROOT)
probe=json.loads((ROOT/'experiments/lingsheng-report-20261115/sve-probe.json').read_text(encoding='utf-8-sig'))
assert probe['state']=='SUCCEEDED' and all(t['passed'] for t in probe['tests'])
cases=[]
for n in (24,32):
    r=records['lingsheng',n]
    cases.append(f'| {n}³×64 | {r["mass"]} | {r["csw"]} | '+ '×'.join(map(str,r['block_xyzt']))+' |')
tests+='质量参数`mass`与Clover系数`csw`如下；两种输入均执行一次四方向stout，强度`rho=0.125`。时间采用反周期边界，外部场使用DeGrand–Rossi自旋基，setup随机种子1024。完整输入哈希见文末验收记录。\n\n| 已验收格子 | mass（质量参数） | csw（Clover系数） | 聚合块 |\n|---|---:|---:|---|\n'+'\n'.join(cases)+'\n\n'
tests+='新增探针同时记录：页大小4096字节，可访问内存节点0—31，Linux可见总内存592446008 KiB、无swap；lscpu报告32个NUMA节点，包含16个CPU域与仅内存域，CPU配置范围1200—2000 MHz。未测满载持续频率和真实内存带宽。该物理内存读数与调度器578560 MB基本一致，因此本文GiB/TiB换算按其MiB计数口径处理。\n\n'
report=report.replace('## 1. 项目与已完成工作',background+'## 2. 项目与已完成工作')
report=report.replace('## 2. 当前性能与精度',design+'## 4. 当前性能与精度')
report=report.replace('## 3. 当前限制与优化重点',tests+'## 6. 当前限制与优化重点')
first=report.index('## 4. 大格点内存与资源申请')
last=report.index('数据依据：',first)
report=report[:first]+resources()+report[last:]
report=report.replace('(assets/lingsheng-report/', '(https://raw.githubusercontent.com/WanbaoLi/multigrid.cpp/develop/docs/assets/lingsheng-report/')
(ROOT/'docs/灵晟测试报告.md').write_text(report,encoding='utf-8')
print('\n'.join(rows))
print('Generated',ROOT/'docs/灵晟测试报告.md')
