"""Validate saved arithmetic/affinity evidence and publish measured FMA rates."""
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import statistics

root = Path(__file__).resolve().parents[3]
out = root/'outputs/hardware-flops-20261105'
source_hash = hashlib.sha256(Path(__file__).with_name('fma_bench.cpp').read_bytes()).hexdigest()
records = []
metadata = {}
assembly = {}
for machine, directory in (('lingsheng',out/'lingsheng/compute'),
                           ('amd9755',out/'amd9755/amd9755')):
    meta = json.loads((directory/'metadata.json').read_text(encoding='utf-8'))
    assert meta['status'] == 'PASS' and meta['source_sha256'] == source_hash
    assert meta['compile']['returncode'] == 0 and meta['disassembly_returncode'] == 0
    assert hashlib.sha256((directory/'fma_bench').read_bytes()).hexdigest() == meta['binary_sha256']
    metadata[machine] = meta
    disassembly = (directory/'disassembly.txt').read_text(encoding='utf-8')
    assembly[machine] = []
    for bits in (32,64):
        match = re.search(r'^\w+ <\(anonymous namespace\)::kernel'+str(bits)+r'\([^\n]+\)>:\n(.*?)(?=\n\w+ <|\Z)',
                          disassembly,re.M|re.S)
        assert match, (machine,bits)
        body = match.group(1).splitlines()
        fmas = [i for i,line in enumerate(body) if re.search(r'\bfmla\b|\bvfmadd231p[sd]\b',line)]
        expected = 48 if machine == 'lingsheng' else 32
        assert len(fmas) == expected, (machine,bits,len(fmas))
        hot = body[fmas[0]:fmas[-1]+1]
        assert len(hot) == expected
        assert all(re.search(r'\bfmla\b|\bvfmadd231p[sd]\b',line) for line in hot)
        assert all('[' not in line and '%rsp' not in line for line in hot)
        assembly[machine].append(dict(precision=f'fp{bits}', fma_instructions_per_iteration=expected,
                                     no_memory_access_in_fma_loop=True))
    suite = json.loads((directory/'suite.json').read_text(encoding='utf-8'))
    for case in suite:
        d = case['benchmark']
        cpus = case['used_cpus']
        assert d['status'] == 'PASS' and d['threads'] == len(cpus)
        assert len(d['workers']) == len(cpus) and len(d['samples']) == 3
        assert len(set(cpus)) == len(cpus)
        bits = int(d['precision'][2:])
        widths = {w['vector_bytes'] for w in d['workers']}
        assert widths == {64}
        for w, cpu in zip(d['workers'],cpus):
            assert w['requested_cpu'] == w['actual_cpu'] == cpu
            assert w['affinity_width'] == 1 and not w['error']
            if machine == 'lingsheng':
                assert w['sve_vl_bytes'] == w['vector_bytes'] == 64
        rates, sample_details = [], []
        for s in d['samples']:
            assert len(s['threads']) == len(cpus)
            assert [t['cpu'] for t in s['threads']] == cpus
            exact_ops = 0
            for t,w in zip(s['threads'],d['workers']):
                assert t['cpu_start'] == t['cpu_end'] == t['cpu']
                assert t['max_abs_error'] == 0
                lanes = w['vector_bytes']*8//bits
                assert t['checksum'] == d['accumulators']*lanes
                exact_ops += t['iterations']*d['accumulators']*2*lanes*2
            wall = max(t['end'] for t in s['threads'])-min(t['start'] for t in s['threads'])
            assert math.isclose(s['flops'], exact_ops, rel_tol=1e-12)
            assert math.isclose(s['seconds'], wall, rel_tol=1e-12)
            rate = exact_ops/wall/1e9
            assert math.isclose(s['gflops'],rate,rel_tol=1e-12)
            rates.append(rate)
            durations = [t['seconds'] for t in s['threads']]
            sample_details.append(dict(repeat=s['repeat'],gflops=rate,wall_seconds=wall,
                start_skew_seconds=max(t['start'] for t in s['threads'])-min(t['start'] for t in s['threads']),
                min_worker_seconds=min(durations),median_worker_seconds=statistics.median(durations),
                max_worker_seconds=max(durations)))
        median = statistics.median(rates)
        assert math.isclose(median,d['median_gflops'],rel_tol=1e-12)
        records.append(dict(machine=machine,hostname=d['hostname'],scope=case['label'],
            precision=d['precision'],cores=len(cpus),isa=d['isa'],vector_bytes=64,
            median_gflops=median,min_gflops=min(rates),max_gflops=max(rates),
            mad_gflops=statistics.median(abs(x-median) for x in rates),samples=sample_details))

assert len(records) == 10
summary = dict(status='PASS',date='2026-11-05',metric='register-resident SIMD FMA throughput',
               flop_convention='1 multiply + 1 add = 2 FLOPs per active lane',
               source_sha256=source_hash,records=records,assembly_validation=assembly,
               limitations=['LingSheng has 608 online physical cores; only 592 scheduler-allowed cores measured.',
               'node5005 was directly accessed over SSH and was not reserved exclusively.',
               'No GPU/SME matrix operations, memory bandwidth, BLAS GEMM or LQCD solver throughput measured.',
               'Single-core and whole-node clocks may differ; frequency records are before/after snapshots.',
               'Three samples per case, approximately two seconds per worker; all original samples retained.'])
(out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
with (out/'samples.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f)
    w.writerow(['machine','hostname','scope','precision','cores','repeat','gflops','wall_seconds',
                'start_skew_seconds','min_worker_seconds','median_worker_seconds','max_worker_seconds'])
    for r in records:
        for s in r['samples']:
            w.writerow([r['machine'],r['hostname'],r['scope'],r['precision'],r['cores'],
                        *[s[k] for k in ('repeat','gflops','wall_seconds','start_skew_seconds',
                                        'min_worker_seconds','median_worker_seconds','max_worker_seconds')]])
index = {(r['machine'],r['scope'],r['precision']):r for r in records}
table = []
for machine,scope,label in [('lingsheng','single_core','灵晟单核'),
                            ('lingsheng','all_allowed_physical_cores','灵晟单节点可用核'),
                            ('amd9755','single_core','EPYC 9755 单核'),
                            ('amd9755','one_socket','EPYC 9755 单路'),
                            ('amd9755','all_allowed_physical_cores','EPYC 9755 双路节点')]:
    a,b = (index[(machine,scope,p)] for p in ('fp32','fp64'))
    unit,scale = ('GFLOPS',1) if a['cores']==1 else ('TFLOPS',1000)
    table.append(f"| {label} | {a['cores']} | {a['median_gflops']/scale:.3f} {unit} | {b['median_gflops']/scale:.3f} {unit} |")
arm=metadata['lingsheng']; amd=metadata['amd9755']
sample_rows='\n'.join(f"| {r['machine']} | {r['scope']} | {r['precision']} | "+
                      ' / '.join(f"{s['gflops']:.3f}" for s in r['samples'])+' |' for r in records)
report=f'''# 灵晟与 EPYC 9755 单核、整节点 FP32 / FP64 实测

2026-11-05，独立寄存器FMA微基准，以下均为三轮中位数；不是理论规格峰值、
LINPACK、GEMM或格点求解器的实测吞吐。FMA按每个活跃lane一次乘加计2 FLOPs。

| 测量范围 | 实际物理核数 | 单精度 FP32 | 双精度 FP64 |
|---|---:|---:|---:|
{chr(10).join(table)}

1 TFLOPS = 1000 GFLOPS = 10^12 FLOP/s。单核结果已经使用该核的全部SIMD lane。
9755单核FMA约为灵晟单核的2.66倍，但灵晟可用核更多，因此两端整节点吞吐接近。
这些数值不能直接推算Wilson–Clover/MG速度：内存带宽、访问布局、通信、同步和
算法迭代数均未由本基准覆盖。

## 硬件与运行边界

- 灵晟计算节点`{arm['hostname']}`，Donau作业2040261。系统在线608物理核、2socket、
  16个CPU NUMA域；作业允许每域37核，总592核。本报告未把592核乘比例包装成608核实测。
  单核选择CPU{arm['selected_single_cpu']}；每个worker实际SVE向量长度64字节，FP32为16lane、FP64为8lane。
- node5005：2×AMD EPYC 9755，每颗128核，总256物理核，8 NUMA域，SMT关闭。
  单核选择CPU{amd['selected_single_cpu']}；单路测试使用一个实际socket的128核，双路使用256核。
  实际执行AVX512 FMA。通过SSH直接运行，没有排他调度分配；开始时load为{amd['load_before']}。
- 两端均在实际目标节点`-O3 -std=c++17 -pthread -march=native`本机编译；没有fast-math。
  灵晟使用Bisheng Clang19.1.7，9755使用GCC14.4.0。精确版本、二进制hash和动态依赖在metadata。
- CPU前后频率快照已保留，但未作为负载期间平均频率。单核boost和全核频率可能不同。

## 算法、计数与校验

基准在寄存器中使用多个独立累加器，ARM为24个、AVX512为16个。每轮先加后减精确
二进制常数，所有lane最终必须精确回到1，checksum为非零且最大误差为0。
`asm volatile`保证这些FMA没有被编译器消掉。各worker逐个绑定一个物理核，
每轮开始和结束的实际CPU均核对，所有case都PASS。

反汇编验证：SVE FP32/FP64内层各48条向量FMA；AVX512内层各32条。
计时循环内无load/store、无溢出寄存器栈访问。每worker操作数为
`iterations × accumulators × 2遍 × SIMD lane数 × 2 FLOPs`。
整节点吞吐按全部线程准确操作数之和除以最早开始到最晚结束的墙时计算，
包含启动偏差和线程被抢占的影响；没有把单核结果直接乘核数。

每case先校准预热，再保留3轮、每线程目标约2秒。线程创建、绑核、校准和结果校验
不计入kernel时间，kernel初始化及末尾保存寄存器结果包含在内。
各worker独立校准，工作量可能不同，因此该结果是此负载的整体实测吞吐，
不保证等于厂商硬件理论最大值。未测SME矩阵运算或任何GPU。

## 所有样本

下表统一以GFLOPS表示。9755双路FP32三轮有可见波动，全部保留，未删除慢样本。

| 平台 | 范围 | 精度 | 三轮 GFLOPS |
|---|---|---|---:|
{sample_rows}

## 复现和证据

- [基准源码](../../benchmarks/hardware/fma-20261105/fma_bench.cpp)
- [运行说明](../../benchmarks/hardware/fma-20261105/README.md)
- [机器可读汇总](summary.json)、[逐轮计数和同步偏差](samples.csv)
- [灵晟原始证据](lingsheng-evidence.tar.gz)、[9755原始证据](amd9755-evidence.tar.gz)

原始证据包含源码、运行脚本、JSON、全部worker计时/亲和/checksum、反汇编和编译信息。
灵晟远端目录`/home/share/nsls_lwb/.cache/hardware-flops-v20261105`；
9755目录`/public2/home/lwb_720/.cache/hardware-flops-v20261105`。
前置探测作业2040175因环境没有默认g++、在编译器查询处退出，不计入性能样本。
正式作业显式指定clang++后完整成功。
'''
(out/'report.md').write_text(report,encoding='utf-8')
print(json.dumps(dict(status='PASS',records=len(records),samples=sum(len(r['samples']) for r in records),
                     source_sha256=source_hash,table=table),ensure_ascii=False,indent=2))
