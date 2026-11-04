"""Export closed profile150 with all small verification evidence and raw perf."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tarfile
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103');sys.path.insert(0,str(root/'aux-solve-profile-v7'))
import file_integrity as integrity
from raw_scalar_helper import source_bytes
import os
def sha(path,expected=None):return integrity.read_dual(path,expected)['openssl_sha256']
def read(path,expected=None):return json.loads(source_bytes(path,sha(path,expected)))
def payload_bytes(path,expected):
    integrity.read_dual(path,expected)
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        before=integrity.metadata(os.fstat(fd));size=before['bytes'];offset=0;parts=[]
        integrity.require(size<=128*1024**2,'Bounded profile export payload required')
        while offset<size:
            part=os.pread(fd,min(1024**2,size-offset),offset)
            integrity.require(0<len(part)<=size-offset,'Exact profile export read count failure')
            parts.append(part);offset+=len(part)
        integrity.require(os.pread(fd,1,size)==b''and before==integrity.metadata(os.fstat(fd))==integrity.metadata(path.stat()),'Profile export changed during immutable read')
    finally:os.close(fd)
    value=b''.join(parts);integrity.require(integrity.small_dual(value)==expected,'Profile export payload differs');return value

name='150-best-solve-profile-worker10';attempt=root/'campaign/attempts'/name
status=read(root/'queue10'/(name+'.status.json'));state=read(root/(name+'-state.json'))
assert status['status']=='passed'and status['returncode']==0 and status['cleanup']['complete']and not status['cleanup']['surviving_pids']
assert state['complete']and state['budget']['complete']and state['best']=='052-reduce-on'
report=read(Path(state['report']),state['report_sha256']);v=report['verification']
assert report['complete']and v['complete']and v['passed']and v['columns']==12
assert v['max_true_residual']<=1e-8 and len(v['solution_relative_errors'])==12 and max(v['solution_relative_errors'])<=1e-6
profile=root/'solve-profile-worker10-150'/name;wrapper=read(profile/'wrapper-v7-summary.json')
assert wrapper['complete']and wrapper['passed']and wrapper['actual_profiled_stats_checked']
spec=importlib.util.spec_from_file_location('existing_redactor',root/'source/tools/optimization/export_evidence.py')
redactor=importlib.util.module_from_spec(spec);spec.loader.exec_module(redactor)
selected={root/(name+'-state.json'),root/'queue10'/(name+'.status.json'),root/'queue10'/(name+'.finished.json'),
    root/'prepared-profile150-worker10/contract.json',root/'prepared-profile150-worker10/task.json',
    root/'150-best-solve-profile-worker10-launch.json',root/'150-best-solve-profile-worker10-actual-parent-guard-v2.json',
    root/'prepared-profile150-live-v2/guard-plan.json',root/'prepared-profile150-live-v2/task.json',attempt/'attempt.json',attempt/'source-manifest.json',attempt/'plan.json',
    attempt/'benchmark-000.log',attempt/'independent-000.log'}
for directory in (attempt/'checksum-audit',attempt/'measurements',profile):
    selected.update(p for p in directory.rglob('*')if p.is_file()and not p.is_symlink()and
        (p.suffix in('.json','.log','.txt','.csv')or p.name.endswith('.perf.data')))
out=root/'exports/profile150-complete';out.mkdir(parents=True,exist_ok=False)
summary=dict(complete=True,passed=True,unranked=True,source_manifest_sha256=state['source_manifest_sha256'],library_sha256=state['library_sha256'],
    scalar_max_residual=v['max_true_residual'],gold_max_relative_error=v['solution_relative_error'],columns=12,
    sampled_call='Final verbose full12 checked through native true-residual stats; output not saved',
    independent_saved_output='Final light full12 sample independently checked by original scalar executable and coordinate-matched stored solution',
    exact_cycle_analysis_sha256=sha(profile/'exact-period-analysis.json'),budget=state['budget'],task_cleanup=status['cleanup'],
    original_files_modified=False)
integrity.write_json_private(out/'summary.json',summary);selected.add(out/'summary.json')
rows=[]
with tarfile.open(out/'evidence.tar.gz','x:gz')as tar:
    for path in sorted(selected):
        assert path.is_relative_to(root)and not path.is_symlink()and path.stat().st_size<128*1024**2
        digest=sha(path);payload=payload_bytes(path,digest)
        if path.name.endswith('.perf.data'):change='none; raw recorded user perf data'
        elif path.suffix=='.json':payload=(json.dumps(redactor.redact(json.loads(payload)),indent=2)+'\n').encode();change='Existing redactor; JSON formatting'
        else:payload=redactor.redact(payload.decode()).encode();change='Existing redactor'
        name=str(path.relative_to(root));member=tarfile.TarInfo(name);member.size=len(payload);member.mode=0o600
        tar.addfile(member,io.BytesIO(payload));rows.append(dict(path=name,bytes=len(payload),original_sha256=digest,
            export_sha256=hashlib.sha256(payload).hexdigest(),transformation=change))
integrity.write_json_private(out/'manifest.json',dict(files=rows))
receipt=dict(complete=True,passed=True,files=len(rows),archive=str(out/'evidence.tar.gz'),archive_sha256=sha(out/'evidence.tar.gz'),
    archive_bytes=(out/'evidence.tar.gz').stat().st_size,manifest_sha256=sha(out/'manifest.json'))
integrity.write_json_private(out/'receipt.json',receipt);print(json.dumps(receipt),flush=True)
