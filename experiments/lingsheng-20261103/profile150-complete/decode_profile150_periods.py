"""Postprocess existing diagnostic data with exact period sums, no recording."""
from collections import defaultdict
import json
from pathlib import Path
import subprocess
import sys
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
sys.path.insert(0,str(root/'aux-solve-profile-v7'));import file_integrity as integrity
directory=root/'solve-profile-worker10-150/150-best-solve-profile-worker10'
summary=[]
for rank in (0,8):
    prefix=directory/('rank%05d'%rank);out=prefix.with_suffix('.leaf-periods.csv');log=prefix.with_suffix('.leaf-periods.log')
    argv=['perf','report','--stdio','--no-children','--call-graph','none','--sort','comm,pid,dso,symbol',
        '--percent-limit','0','--field-separator',';','--fields','period,sample,comm,pid,dso,symbol','--input',str(prefix.with_suffix('.perf.data'))]
    with out.open('xb')as stream,log.open('xb')as errors:result=subprocess.run(argv,stdout=stream,stderr=errors,timeout=90)
    assert result.returncode==0
    ds=defaultdict(int);symbols=defaultdict(int);threads=defaultdict(int);total=0;samples=0
    for line in out.read_text().splitlines():
        if not line.strip()or line.startswith('#'):continue
        fields=[v.strip()for v in line.split(';')]
        assert len(fields)>=6 and fields[0].isdigit()and fields[1].isdigit()
        period=int(fields[0]);samples+=int(fields[1]);tid=int(fields[3].split(':',1)[0])
        total+=period;ds[fields[4]]+=period;symbols[(fields[4],fields[5])]+=period;threads[tid]+=period
    runtime=json.loads(prefix.with_suffix('.runtime.json').read_text());pid=runtime['pid']
    def rows(items):return[dict(key=key,period=value,fraction=value/total)for key,value in sorted(items,key=lambda row:-row[1])]
    summary.append(dict(rank=rank,total_period=total,total_samples=samples,thread_count=len(threads),main_tid=pid,
        dso=rows(ds.items()),top_symbols=rows(symbols.items())[:30],main_thread_period=threads.get(pid,0),
        thread_periods=rows(threads.items()),data_sha256=integrity.read_dual(prefix.with_suffix('.perf.data'))['openssl_sha256'],
        csv_sha256=integrity.read_dual(out)['openssl_sha256'],argv=argv))
output=directory/'exact-period-analysis.json'
integrity.write_json_private(output,dict(complete=True,unranked=True,scope='User cycles in one final diagnostic full12 at selected ranks only',
    warning='CPU-cycle fractions across threads are not elapsed-time savings; OpenMP wait includes arrival skew',ranks=summary))
print(json.dumps(dict(complete=True,path=str(output),sha256=integrity.read_dual(output)['openssl_sha256'],
    ranks=[dict(rank=r['rank'],samples=r['total_samples'],threads=r['thread_count'],dso=r['dso'][:4],top_symbols=r['top_symbols'][:8])for r in summary]),indent=2))
