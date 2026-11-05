"""Export closed deliverable build, failed source-pin attempt and actual retry."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tarfile
root=Path('/public2/home/lwb_720/.cache/mg-opt-delivery-833-20261105');sys.path.insert(0,str(root))
import file_integrity as integrity
def sha(p):return integrity.read_dual(p)['openssl_sha256']
def read(p):return json.loads(p.read_text())
q=read(root/'000-summary.json');state=read(root/'full12-v2-summary.json')
assert q['complete']and q['status']=='passed'and q['source_commit']=='833f8732f6b06e370074efbb610fc7a85fe11a46'
assert state['complete']and state['stable']and len(state['outcomes'])==2
selected={root/'000-summary.json',root/'full12-v2-summary.json',root/'launch.json',root/'full12-v2-launch.json',root/'worker.log',root/'full12-v2-worker.log'}
for queue,name,expected in [('queue','000-correctness','passed'),('queue','100-delivery-full12','failed'),('full12-v2-queue','110-full12-v2','passed')]:
    s=read(root/queue/(name+'.status.json'));assert s['status']==expected and s['cleanup']['complete']and not s['cleanup']['surviving_pids']
    selected.update([root/queue/(name+'.status.json'),root/queue/(name+'.finished.json')])
for name in('000-delivery-tests','100-delivery-full12-a','110-delivery-full12-a','111-delivery-full12-b'):
    owner=root/'campaign/attempts'/name;record=read(owner/'attempt.json')
    selected.update(p for p in owner.rglob('*')if p.is_file()and not p.is_symlink()and
        not({'build','source'}&set(p.relative_to(owner).parts))and p.suffix in('.json','.log','.txt','.csv'))
    for stage,s in record['stages'].items():
        if name=='100-delivery-full12-a':assert stage=='benchmark'and s['status']=='failed'
        else:assert s['status']=='passed'and s['returncode']==0
        assert s['cleanup']['complete']and not s['cleanup']['surviving_pids'];assert sha(owner/s['log'])==s['log_sha256']
    if name.startswith(('110-','111-')):
        r=read(owner/'report.json');v=r['verification'];assert v['passed']and v['columns']==12 and v['max_true_residual']<=1e-8 and max(v['solution_relative_errors'])<=1e-6
for p in root.iterdir():
    if p.is_file()and p.suffix in('.py','.json','.log'):selected.add(p)
spec=importlib.util.spec_from_file_location('existing_redactor',root/'source/tools/optimization/export_evidence.py')
redactor=importlib.util.module_from_spec(spec);spec.loader.exec_module(redactor)
out=root/'exports/delivery833-complete';out.mkdir(parents=True,exist_ok=False)
summary=dict(complete=True,build_and_selected_ctest=q['tests'],source_commit=q['source_commit'],library_sha256=q['library_sha256'],results=state,
    failed_attempt100_preserved=True,reason='Initial driver pinned historical711 benchmark while deliverable uses reviewed686 strengthening metadata/independent identity checks; failed before numerical execution. New110/111 explicitly pin686; no timing/physics change.',
    all12_independent=True,direct_ssh_not_scheduler_exclusive=True)
integrity.write_json_private(out/'summary.json',summary);selected.add(out/'summary.json');rows=[]
with tarfile.open(out/'evidence.tar.gz','x:gz')as tar:
    for p in sorted(selected):
        assert p.is_relative_to(root)and not p.is_symlink()and p.stat().st_size<32*1024**2
        digest=sha(p);fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
        try:
            before=integrity.metadata(os.fstat(fd));size=before['bytes'];parts=[];offset=0
            while offset<size:
                part=os.pread(fd,min(1024**2,size-offset),offset);assert 0<len(part)<=size-offset;parts.append(part);offset+=len(part)
            assert os.pread(fd,1,size)==b''and before==integrity.metadata(os.fstat(fd))==integrity.metadata(p.stat())
        finally:os.close(fd)
        value=b''.join(parts);assert integrity.small_dual(value)==digest
        if p.suffix=='.json':value=(json.dumps(redactor.redact(json.loads(value)),indent=2)+'\n').encode()
        else:value=redactor.redact(value.decode()).encode()
        rel=str(p.relative_to(root));m=tarfile.TarInfo(rel);m.size=len(value);m.mode=0o600;tar.addfile(m,io.BytesIO(value))
        rows.append(dict(path=rel,bytes=len(value),original_sha256=digest,export_sha256=hashlib.sha256(value).hexdigest(),transformation='Existing redactor; originals unchanged'))
integrity.write_json_private(out/'manifest.json',dict(files=rows));receipt=dict(complete=True,files=len(rows),archive_sha256=sha(out/'evidence.tar.gz'),archive_bytes=(out/'evidence.tar.gz').stat().st_size,manifest_sha256=sha(out/'manifest.json'))
integrity.write_json_private(out/'receipt.json',receipt);print(json.dumps(receipt),flush=True)
