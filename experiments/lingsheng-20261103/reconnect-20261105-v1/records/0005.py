"""Archive closed actual full12 Halo V2 results, including independent evidence."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import statistics
import sys
import tarfile
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103');sys.path.insert(0,str(root/'aux-solve-profile-v7'))
import file_integrity as integrity
from raw_scalar_helper import source_bytes
def sha(p,e=None):return integrity.read_dual(p,e)['openssl_sha256']
def read(p):return json.loads(source_bytes(p,sha(p)))
def payload(p,digest):
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        before=integrity.metadata(os.fstat(fd));size=before['bytes'];assert size<32*1024**2
        offset=0;parts=[]
        while offset<size:
            part=os.pread(fd,min(1024**2,size-offset),offset);assert 0<len(part)<=size-offset;parts.append(part);offset+=len(part)
        assert os.pread(fd,1,size)==b''and before==integrity.metadata(os.fstat(fd))==integrity.metadata(p.stat())
    finally:os.close(fd)
    value=b''.join(parts);assert integrity.small_dual(value)==digest;return value
name='154-halo-v2-ordinary-remainder-worker10';camp=root/'campaign-halo-v2-ordinary-w10v4'
statepath=root/'v2-w10v5-state.json';state=read(statepath);statuspath=root/'queue10'/(name+'.status.json');status=read(statuspath)
assert state['complete']and state['status']=='complete'and state['best']=='052-reduce-on'and state['winner']is None
assert status['status']=='passed'and status['returncode']==0 and status['cleanup']['complete']and not status['cleanup']['surviving_pids']
assert read(root/'campaign/best.json')['attempt']=='052-reduce-on'
selected={statepath,statuspath,root/'queue10'/(name+'.finished.json'),root/(name+'-launch.json'),root/(name+'-actual-parent-guard-v4.json'),root/'worker10-startup.json',root/'worker10-allocation.json'}
for d in(root/'prepared-halo154-worker10',root/'prepared-halo154-live-v4'):
    if d.exists():selected.update(p for p in d.iterdir()if p.is_file()and p.suffix=='.json')
ordinary={}
for case in('control-a','new-off','halo-on','control-b','halo-profile'):
    owner=camp/'attempts'/('v2-w10v5-'+case);record=read(owner/'attempt.json')
    selected.update(p for p in owner.rglob('*')if p.is_file()and not p.is_symlink()and
        ('build'not in p.relative_to(owner).parts)and('source'not in p.relative_to(owner).parts)and p.suffix in('.json','.log','.txt','.csv'))
    for k,s in record['stages'].items():
        assert s['status']=='passed'and s['returncode']==0 and s['cleanup']['complete']and not s['cleanup']['surviving_pids']
        sha(owner/s['log'],s['log_sha256'])
    reportpath=owner/'report.json'if case!='halo-profile'else Path(state['actual_halo_diagnostic']['report'])
    report=read(reportpath);v=report['verification']
    assert report['complete']and v['complete']and v['passed']and v['columns']==12 and v['max_true_residual']<=1e-8
    assert len(v['solution_relative_errors'])==12 and max(v['solution_relative_errors'])<=1e-6
    ordinary[case]=dict(unranked=case=='halo-profile',steady=[s['wall_seconds']for s in report['samples']if not s['warmup']],
        scalar_max=v['max_true_residual'],gold_max=v['solution_relative_error'],report_sha256=sha(reportpath))
    ordinary[case]['median']=statistics.median(ordinary[case]['steady'])
diagowner=camp/'attempts/v2-w10v5-halo-profile';diagrecord=read(diagowner/'attempt.json')
diagstage=diagrecord['stages']['diagnostic'];text=(diagowner/diagstage['log']).read_text()
native=[]
for line in text.splitlines():
    if 'native_halo_profile'in line:
        pos=line.find('{')
        if pos>=0:
            try:native.append(json.loads(line[pos:]))
            except json.JSONDecodeError:pass
summary=dict(complete=True,physical_full12_verified=True,adopted=False,best='052-reduce-on',ordinary=ordinary,
    assessments=state['assessments'],halo_increment=state['halo_increment'],actual_halo_diagnostic=state['actual_halo_diagnostic'],
    native_halo_rows=native,task_cleanup=status['cleanup'],
    conclusion='V2 correct; 1.70/1.89 percent gains below frozen3percent two-control gate. Batched-only counters must not be compared with all coarse halo calls.')
spec=importlib.util.spec_from_file_location('redactor',root/'source/tools/optimization/export_evidence.py')
redactor=importlib.util.module_from_spec(spec);spec.loader.exec_module(redactor)
out=root/'exports/halo154-full';out.mkdir(parents=True,exist_ok=False)
integrity.write_json_private(out/'summary.json',summary);selected.add(out/'summary.json');rows=[]
with tarfile.open(out/'evidence.tar.gz','x:gz')as tar:
    for p in sorted(selected):
        assert p.is_relative_to(root)and not p.is_symlink();digest=sha(p);value=payload(p,digest)
        if p.suffix=='.json':value=(json.dumps(redactor.redact(json.loads(value)),indent=2)+'\n').encode()
        else:value=redactor.redact(value.decode()).encode()
        rel=str(p.relative_to(root));m=tarfile.TarInfo(rel);m.size=len(value);m.mode=0o600;tar.addfile(m,io.BytesIO(value))
        rows.append(dict(path=rel,bytes=len(value),original_sha256=digest,export_sha256=hashlib.sha256(value).hexdigest(),transformation='Existing redactor; originals unchanged'))
integrity.write_json_private(out/'manifest.json',dict(files=rows))
receipt=dict(complete=True,files=len(rows),archive_sha256=sha(out/'evidence.tar.gz'),archive_bytes=(out/'evidence.tar.gz').stat().st_size,manifest_sha256=sha(out/'manifest.json'))
integrity.write_json_private(out/'receipt.json',receipt)
print(json.dumps(dict(receipt=receipt,native_halo_rows=native[:2],native_halo_records=len(native))),flush=True)
