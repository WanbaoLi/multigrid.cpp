"""Export complete round1 records while a separate round2 may run."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tarfile
root=Path('/public2/home/lwb_720/.cache/mg-opt-clover-reuse-v1-20261104');sys.path.insert(0,str(root/'quality-round2-helpers'))
import file_integrity as integrity
def sha(path,expected=None):return integrity.read_dual(path,expected)['openssl_sha256']
def read(path):return json.loads(path.read_text())
def payload(path,digest):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        before=integrity.metadata(os.fstat(fd));size=before['bytes'];assert size<16*1024**2
        parts=[];offset=0
        while offset<size:
            part=os.pread(fd,min(1024**2,size-offset),offset);assert 0<len(part)<=size-offset;parts.append(part);offset+=len(part)
        assert os.pread(fd,1,size)==b''and before==integrity.metadata(os.fstat(fd))==integrity.metadata(path.stat())
    finally:os.close(fd)
    value=b''.join(parts);assert integrity.small_dual(value)==digest;return value
status=read(root/'quality-round2-queue/000-correctness.status.json');summary=read(root/'quality-round2-summary.json')
assert status['status']=='passed'and status['returncode']==0 and status['cleanup']['complete']and not status['cleanup']['surviving_pids']and summary['complete']
source=root/'source';spec=importlib.util.spec_from_file_location('existing_redactor',source/'tools/optimization/export_evidence.py')
redactor=importlib.util.module_from_spec(spec);spec.loader.exec_module(redactor)
selected={root/'quality-round2-summary.json',root/'quality-round2-launch.json',root/'quality-round2-queue/000-correctness.status.json',
    root/'quality-round2-queue/000-correctness.finished.json',root/'000-summary.json',root/'deployment.json',root/'start_quality_round2_current_idle_v2.py'}
for name in summary['outcomes']:
    attempt=root/'campaign/attempts'/name;report=read(attempt/'report.json');v=report['verification']
    sha(attempt/'report.json',summary['outcomes'][name]['report_sha256'])
    assert v['complete']and v['passed']and v['columns']==12 and v['max_true_residual']<=1e-8 and v['solution_relative_error']<=1e-6
    for directory in [attempt/'checksum-audit',attempt/'measurements']:
        selected.update(p for p in directory.rglob('*')if p.is_file()and not p.is_symlink()and p.suffix in('.json','.log','.txt'))
    for file in ['attempt.json','source-manifest.json','report.json','plan.json','reused-build.json','benchmark-000.log','independent-000.log']:
        path=attempt/file
        if path.is_file():selected.add(path)
    selected.add(root/(name+'-summary.json'));selected.add(root/(name+'.log'))
for directory in [root/'quality-helpers',root/'quality-v2-helpers',root/'quality-v3-helpers',root/'quality-round2-helpers']:
    selected.update(p for p in directory.iterdir()if p.is_file()and p.suffix in('.py','.json'))
for name in ['quality-200-control-a.log','quality-210-control-a.log','quality-queue/000-correctness.status.json','quality-v2-queue/000-correctness.status.json']:
    path=root/name
    if path.is_file():selected.add(path)
out=root/'exports/quality-round2';out.mkdir(parents=True,exist_ok=False);rows=[]
with tarfile.open(out/'evidence.tar.gz','x:gz')as tar:
    for path in sorted(selected):
        assert path.is_file()and not path.is_symlink()and path.is_relative_to(root)
        digest=sha(path);value=payload(path,digest)
        if path.suffix=='.json':value=(json.dumps(redactor.redact(json.loads(value)),indent=2)+'\n').encode()
        else:value=redactor.redact(value.decode()).encode()
        name=str(path.relative_to(root));member=tarfile.TarInfo(name);member.size=len(value);member.mode=0o600;tar.addfile(member,io.BytesIO(value))
        rows.append(dict(path=name,original_sha256=digest,export_sha256=hashlib.sha256(value).hexdigest(),bytes=len(value),transformation='Existing redactor; JSON formatted; no original changes'))
integrity.write_json_private(out/'manifest.json',dict(files=rows));receipt=dict(complete=True,passed=True,files=len(rows),archive=str(out/'evidence.tar.gz'),
    archive_sha256=sha(out/'evidence.tar.gz'),archive_bytes=(out/'evidence.tar.gz').stat().st_size,manifest_sha256=sha(out/'manifest.json'))
integrity.write_json_private(out/'receipt.json',receipt);print(json.dumps(receipt),flush=True)
