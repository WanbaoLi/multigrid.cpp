"""Validate saved streaming results and create the memory-bandwidth comparison."""
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics

root=Path(__file__).resolve().parents[3]
out=root/'outputs/hardware-bandwidth-20261106'
ls=out/'lingsheng'
amd=out/'amd9755/amd9755-r4'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
records=[]
samples=[]
for machine,directory in (('lingsheng',ls/'compute-r5'),('amd9755',amd)):
    metadata=read(directory/'metadata.json')
    assert metadata['compile']['returncode']==0 and metadata['objdump_returncode']==0
    assert hashlib.sha256((directory/'bandwidth_bench').read_bytes()).hexdigest()==metadata['binary_sha256']
    assert hashlib.sha256((out/machine/'bandwidth_bench.cpp').read_bytes()).hexdigest()==metadata['source_sha256']
assert read(ls/'compute-r5/metadata.json')['source_sha256']==read(amd/'metadata.json')['source_sha256']
assert 'SUCCEEDED' in (ls/'job-2051113.txt').read_text(encoding='utf-8')

def validate(path,label,expected_sdk=None):
    d=read(path)
    assert d['status']=='PASS' and d['precision']=='fp64'
    assert not d['per_pass_team_barriers'] and d['store_policy']=='ordinary_temporal_stores'
    assert d['passes']==16 and d['repeats']==5
    assert len(d['workers'])==d['threads']
    assert len({w['cpu'] for w in d['workers']})==d['threads']
    for w in d['workers']:
        assert w['cpu']==w['actual_cpu'] and w['affinity_width']==1 and not w['error']
        assert w['vector_bytes']==64
        if d['isa']=='aarch64-sve':assert w['sve_vl_bytes']==64
    groups={g['group']:g for g in d['placement']}
    assert len(groups)==d['groups']
    assert len({g['memory_node'] for g in groups.values()})==d['groups']
    for g in groups.values():
        for a in g['arrays']:
            assert a['bytes']==d['bytes_per_array_per_group'] and a['mbind_rc']==0
            for stage in ('before','after'):
                r=a[stage]
                assert r['verified'] and r['move_pages_rc']==0
                assert r['samples_on_target']==r['sampled_pages']>0
                assert r['numa_maps_verified']
                assert r['node_pages']=={str(g['memory_node']):a['bytes']//r['kernel_page_bytes']}
            if expected_sdk is not None:
                assert a['sdk_verify_before']==a['sdk_verify_after']==expected_sdk
    worker_ranges={}
    for group in groups:
        workers=[w for w in d['workers'] if w['group']==group]
        elements=d['bytes_per_array_per_group']//8
        for i,w in enumerate(workers):worker_ranges[w['cpu']]=elements*(i+1)//len(workers)-elements*i//len(workers)
    kernels={}
    for k in d['kernels']:
        bpe={'read':8,'copy':16,'triad':24}[k['kernel']]
        assert k['logical_bytes_per_element']==bpe and len(k['samples'])==5
        rates=[]
        for s in k['samples']:
            assert len(s['threads'])==d['threads']
            wall=max(t['end'] for t in s['threads'])-min(t['start'] for t in s['threads'])
            logical=d['bytes_per_array_per_group']*d['groups']*(bpe//8)*d['passes']
            assert s['logical_bytes']==logical
            assert math.isclose(s['seconds'],wall,rel_tol=1e-12)
            assert math.isclose(s['gb_per_second'],logical/wall/1e9,rel_tol=1e-12)
            for t in s['threads']:
                assert t['cpu_start']==t['cpu_end']==t['cpu'] and t['max_abs_error']==0
                n=worker_ranges[t['cpu']]
                expected=2*n*d['passes'] if k['kernel']=='read' else (2 if k['kernel']=='copy' else 11)*n
                assert t['checksum']==expected
            rates.append(s['gb_per_second'])
            samples.append(dict(label=label,hostname=d['hostname'],cores=d['threads'],groups=d['groups'],
                                kernel=k['kernel'],repeat=s['repeat'],seconds=wall,logical_bytes=logical,
                                gb_per_second=s['gb_per_second'],
                                start_skew_seconds=max(t['start'] for t in s['threads'])-min(t['start'] for t in s['threads'])))
        assert math.isclose(statistics.median(rates),k['median_gb_per_second'],rel_tol=1e-12)
        kernels[k['kernel']]=dict(median_gb_per_second=statistics.median(rates),
                                  min_gb_per_second=min(rates),max_gb_per_second=max(rates),samples=rates)
    result=dict(label=label,path=str(path.relative_to(root)),hostname=d['hostname'],cores=d['threads'],
                groups=d['groups'],array_bytes=d['bytes_per_array_per_group'],
                total_working_set_bytes=3*d['bytes_per_array_per_group']*d['groups'],
                isa=d['isa'],sdk_class=expected_sdk,kernels=kernels)
    records.append(result)
    return result,d

ddr,dd=validate(ls/'ddr261-large.json','lingsheng-ddr-full-node',0)
hbw,hh=validate(ls/'hbw261-large.json','lingsheng-hbw-full-node',1)
epyc,ee=validate(amd/'ddr-threads32-size2048.json','dual9755-ddr-full-node')
assert ddr['hostname']==hbw['hostname']
assert dd['threads']==hh['threads']==592 and dd['groups']==hh['groups']==16
assert [w['cpu'] for w in dd['workers']]==[w['cpu'] for w in hh['workers']]
assert ddr['total_working_set_bytes']==hbw['total_working_set_bytes']==epyc['total_working_set_bytes']==48*2**30
assert ee['threads']==256 and ee['groups']==8

for f in sorted((ls/'compute-r5').glob('ddr-*.json')):validate(f,'scan-lingsheng-'+f.stem,0)
for f in sorted(amd.glob('ddr-*.json')):
    if f.name!='ddr-threads32-size2048.json':validate(f,'scan-amd-'+f.stem)
validate(ls/'matched-ddr.json','diagnostic-ls-ddr-15-domains')
validate(ls/'matched-hbw.json','diagnostic-ls-hbw-15-domains',1)
validate(ls/'hbw15.json','diagnostic-ls-hbw-15-domains-8threads',1)
validate(ls/'hbw-large.json','diagnostic-ls-hbw-15-domains-large',1)
validate(ls/'hbw261.json','diagnostic-ls-hbw-16-domains-small',1)
classes=read(ls/'classes-r2.json')
assert next(c for c in classes['classes'] if c['target']==31)['old_verify']==0
assert next(c for c in classes['classes'] if c['target']==31)['new_verify']==1
summary=dict(status='PASS',date='2026-11-06',metric='logical streaming bandwidth with temporal stores',
    headline=[ddr,hbw,epyc],records=records,
    ratios={k:dict(hbw_over_ddr=hbw['kernels'][k]['median_gb_per_second']/ddr['kernels'][k]['median_gb_per_second'],
                   hbw_over_dual9755=hbw['kernels'][k]['median_gb_per_second']/epyc['kernels'][k]['median_gb_per_second'])
            for k in ('read','copy','triad')},
    sdk_classification_probe=classes,
    limitations=['Different compute allocations used for diagnostic sweeps; headline LingSheng DDR/HBW share one node and one job.',
        'The original FLOPS node cn19473 was busy; bandwidth is measured on the same class of LingSheng compute node, not that literal host.',
        'Ordinary write allocate traffic may exceed the logical bytes; no memory-controller counters were measured.',
        'Not an official STREAM build; independently implemented identical Read/Copy/Triad semantics on both platforms.',
        'Node5005 was accessed over SSH without exclusive reservation.',
        'No solver speedup or theoretical maximum inferred from this bandwidth result.'])
(out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
with (out/'samples.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(samples[0]));w.writeheader();w.writerows(samples)

def row(label,r):return '| '+label+' | '+str(r['cores'])+' | '+' | '.join(f"{r['kernels'][k]['median_gb_per_second']:.2f}" for k in ('read','copy','triad'))+' |'
table='\n'.join([row('灵晟 DDR',ddr),row('灵晟 HBW（平台 HBM）',hbw),row('双路 EPYC 9755 DDR',epyc)])
rows='\n'.join('| '+r['label']+' | '+str(r['cores'])+' | '+str(r['total_working_set_bytes']/2**30)+' | '+' | '.join(f"{r['kernels'][k]['median_gb_per_second']:.2f}" for k in ('read','copy','triad'))+' |' for r in records)
text=f'''# 灵晟 HBM、DDR 与双路 EPYC 9755 带宽实测

2026-11-06。下表使用48 GiB工作集，5轮中位数，单位GB/s（10^9 bytes/s）。
灵晟DDR/HBW在同一节点、同一作业内按相同592个物理核和相同数组大小顺序执行。

| 平台和内存 | 实际物理核数 | Read | Copy | Triad |
|---|---:|---:|---:|---:|
{table}

Triad下，HBM约为本机DDR的{summary['ratios']['triad']['hbw_over_ddr']:.2f}倍、
双9755 DDR的{summary['ratios']['triad']['hbw_over_dual9755']:.2f}倍。
这是该访问模式下的实测有效带宽，不是理论峰值或求解器加速比。

## 范围与核验

- 灵晟主对照作业2051113，节点`{ddr['hostname']}`，592个允许物理核、16个CPU NUMA域。
  DDR绑定nodes0–15；HBW绑定nodes16–31，CPU域和内存域分别一一配对。
  系统608核中每域留1核给系统，本次没有外推608核带宽。
  先前FMA节点cn19473忙碌，当前测的是同型号计算节点，不是同一台物理主机。
- 两类内存各分配48个数组，每数组1GiB、每域3GiB；总48GiB，远大于缓存。
  9755为node5005双路2×128核，8个NUMA域，每数组2GiB、每域6GiB，总48GiB。
- 所有线程固定到不同物理核，计时前后CPU检查通过。每数组在触页前严格设置NUMA绑定；
  before/after的move_pages样本与numa_maps完整VMA页面数均完全位于目标内存节点。
- 主对照使用HPCKit26.1 KUPL对每个完整数组做额外分类：DDR全部verify=0，HBW全部verify=1。
  新旧SDK分类探针发现：旧25.1将node31判为0，而26.1判为1；两者对nodes16–30均判为1。
  因此16域主表采用26.1，旧25.1的16域混合分类样本不计入主表。
- 同一CPU-native二进制执行灵晟两种内存测试；Bisheng19.1.7、SVE64B。
  AMD用GCC14.4、AVX512。两个平台源码一致，-O3 -std=c++17 -pthread -march=native，无fast-math。
  反汇编确认被测函数采用普通load/store，未调用memcpy/memmove、未使用非临时存储。
- 每个kernel先预热，之后5轮，每轮连续16遍，无计时内逐遍团队屏障。
  总带宽采用全队最早开始到最晚结束墙时，包含启动偏差、调度与争用；不是逐核峰值相加。
  每轮全输出checksum/误差检查通过；分配、初始化、页面检查和结果校验排除在计时外。

## 带宽口径

Read只读取一个double数组，每元素8字节；Copy `a=b`按一读一写16字节；
Triad `a=b+3*c`按两读一写24字节。两个平台都使用ordinary temporal stores。
实际控制器总线流量还可能含写分配/RFO，因此这些有效GB/s不是物理总线字节计数。
本测试是独立实现的STREAM式访问内核，不是官方STREAM程序的认证成绩。

DDR线程扫描表明更多线程未必更快：灵晟256核的Triad约619GB/s，592核旧扫描约506GB/s。
这反映该启动/同步和NUMA配置下的观测，不宜只用“全核”代表最优带宽。
主表保留全节点资源口径，下面保留所有线程扫描与不同工作集样本。
9755没有排他调度分配；所有数据均为当次共享机器条件下结果。

## 全部有效配置

| 配置 | 核数 | 总工作集GiB | Read GB/s | Copy GB/s | Triad GB/s |
|---|---:|---:|---:|---:|---:|
{rows}

## 复现与证据

[基准源码](../../benchmarks/hardware/bandwidth-20261105/bandwidth_bench.cpp) ·
[说明](../../benchmarks/hardware/bandwidth-20261105/README.md) ·
[汇总JSON](summary.json) · [全部逐轮数据](samples.csv)

[灵晟完整原始证据](lingsheng-evidence.tar.gz) · [9755完整原始证据](amd9755-evidence.tar.gz)

远端目录：灵晟`/home/share/nsls_lwb/.cache/hardware-bandwidth-v20261105`；
9755`/public2/home/lwb_720/.cache/hardware-bandwidth-v20261105`。
源码只新增独立硬件微基准，没有修改求解器。
初次maxnode过窄的mbind、缺少NUMA开发包、未分配HBM的作业和旧SDK分类混合样本均排除，
不把绑定失败、HBM不可用或未完成状态当作带宽零值。
'''
(out/'report.md').write_text(text,encoding='utf-8')
print('PASS',len(records),'configurations',len(samples),'samples')
print(table)
