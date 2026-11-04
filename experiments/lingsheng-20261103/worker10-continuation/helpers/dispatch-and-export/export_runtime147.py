"""Export completed runtime2x2 evidence without scientific field reads."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import statistics
import sys
import tarfile
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103');sys.path.insert(0,str(root/'aux-runtime-worker10-v7'))
import file_integrity as integrity
def sha(path,expected=None):return integrity.read_dual(path,expected)['openssl_sha256']
def read(path):return json.loads(path.read_text())
def payload(path,digest):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        before=integrity.metadata(os.fstat(fd));size=before['bytes'];assert size<16*1024**2;offset=0;parts=[]
        while offset<size:
            part=os.pread(fd,min(1024**2,size-offset),offset);assert 0<len(part)<=size-offset;parts.append(part);offset+=len(part)
        assert os.pread(fd,1,size)==b''and before==integrity.metadata(os.fstat(fd))==integrity.metadata(path.stat())
    finally:os.close(fd)
    result=b''.join(parts);assert integrity.small_dual(result)==digest;return result
name='147-runtime-only-worker10-v6';statepath=root/(name+'-state.json');state=read(statepath)
statuspath=root/'queue10'/(name+'.status.json');status=read(statuspath);group=state['groups']['runtime']
assert state['complete']and state['status']=='complete'and group['complete']and group['runtime_audit']['complete']
assert status['status']=='passed'and status['returncode']==0 and status['cleanup']['complete']and not status['cleanup']['surviving_pids']
assert group['decision']['status']=='no_adoption'and state['expected_best']=='052-reduce-on'
selected={statepath,statuspath,root/'queue10'/(name+'.finished.json'),root/'worker10-startup.json',root/'worker10-allocation.json',
    root/'worker9-pending-cancel-intent.json',root/'worker9-pending-cancel-result.json',root/'runtime147-launch.json',
    root/'prepared-runtime147-worker10/contract.json',root/'prepared-runtime147-worker10/task.json',
    root/'runtime-shim-manifest-worker10-v3.json',root/'runtime-capture-old-smoke146/maps.json',root/'runtime-capture-old-smoke146/result.json',
    root/'queue10/146-old-runtime-capture-smoke-worker10.status.json',root/'runtime-capture-old-smoke146-launch.json'}
summary=dict(complete=True,passed=True,ordinary_timing=True,adopted=False,decision=group['decision'],assessments=group['assessments'],
    runtime_audit_complete=True,actual_runtime_environment_not_normalized=True,host=state['contract']['host'],allocation=state['contract']['allocation'],
    source_manifest_sha256=state['frozen_source_manifest_sha256'],library_sha256=state['frozen_library_sha256'],cases={})
for case,row in group['trials'].items():
    attempt=root/'campaign/attempts'/case;report=read(attempt/'report.json');v=report['verification']
    assert row['status']=='measured'and report['complete']and v['complete']and v['passed']and v['columns']==12
    assert v['max_true_residual']<=1e-8 and len(v['solution_relative_errors'])==12 and max(v['solution_relative_errors'])<=1e-6
    assert report['library_sha256']==state['frozen_library_sha256']and report['source_manifest_sha256']==state['frozen_source_manifest_sha256']
    times=[r['wall_seconds']for r in report['samples']if not r['warmup']]
    summary['cases'][case]=dict(steady_seconds=times,median_seconds=statistics.median(times),scalar_max=v['max_true_residual'],gold_max=v['solution_relative_error'],
        report_sha256=sha(attempt/'report.json'),configuration=report['configuration'])
    for directory in[attempt/'checksum-audit',attempt/'measurements']:
        selected.update(p for p in directory.rglob('*')if p.is_file()and not p.is_symlink()and p.suffix in('.json','.log','.txt'))
    for file in['attempt.json','source-manifest.json','report.json','plan.json','reused-build.json','benchmark-000.log','independent-000.log']:
        p=attempt/file
        if p.is_file():selected.add(p)
    selected.add(Path(row['runtime_audit_path']))
spec=importlib.util.spec_from_file_location('existing_export_redactor',root/'source/tools/optimization/export_evidence.py')
redactor=importlib.util.module_from_spec(spec);spec.loader.exec_module(redactor)
out=root/'exports/runtime147-complete';out.mkdir(parents=True,exist_ok=False)
integrity.write_json_private(out/'summary.json',summary);selected.add(out/'summary.json');rows=[]
with tarfile.open(out/'evidence.tar.gz','x:gz')as tar:
    for path in sorted(selected):
        assert path.is_file()and not path.is_symlink()and path.is_relative_to(root)
        digest=sha(path);value=payload(path,digest)
        if path.suffix=='.json':value=(json.dumps(redactor.redact(json.loads(value)),indent=2)+'\n').encode()
        else:value=redactor.redact(value.decode()).encode()
        name=str(path.relative_to(root));member=tarfile.TarInfo(name);member.size=len(value);member.mode=0o600;tar.addfile(member,io.BytesIO(value))
        rows.append(dict(path=name,original_sha256=digest,export_sha256=hashlib.sha256(value).hexdigest(),bytes=len(value),transformation='Existing redactor; JSON formatting; originals unchanged'))
integrity.write_json_private(out/'manifest.json',dict(files=rows));receipt=dict(complete=True,passed=True,adopted=False,files=len(rows),
    archive=str(out/'evidence.tar.gz'),archive_sha256=sha(out/'evidence.tar.gz'),archive_bytes=(out/'evidence.tar.gz').stat().st_size,manifest_sha256=sha(out/'manifest.json'))
integrity.write_json_private(out/'receipt.json',receipt);print(json.dumps(receipt),flush=True)
