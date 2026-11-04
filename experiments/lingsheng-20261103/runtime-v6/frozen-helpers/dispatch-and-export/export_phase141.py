"""Small closed-task evidence export; retain incomplete runtime group as failed."""
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import statistics
import sys
import tarfile
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
sys.path.insert(0,str(root/'aux-phase5-worker8-v5'))
import file_integrity as integrity
from raw_scalar_helper import source_bytes
spec=importlib.util.spec_from_file_location('evidence_redaction',root/'source/tools/optimization/export_evidence.py')
redaction=importlib.util.module_from_spec(spec);spec.loader.exec_module(redaction)
def sha(path):return integrity.read_dual(path)['openssl_sha256']
def read(path):return json.loads(source_bytes(path,sha(path)))
statepath=root/'141-phase5-worker8-v5-state.json';state=read(statepath)
statuspath=root/'queue8/141-phase5-worker8-v5.status.json';status=read(statuspath)
assert status['status']=='failed'and status['returncode']==1 and status['cleanup']['complete']and not status['cleanup']['surviving_pids']
assert state['status']=='failed'and state['complete']is False and read(root/'campaign/best.json')['attempt']=='052-reduce-on'
selected={statepath,statuspath,root/'queue8/141-phase5-worker8-v5.finished.json',
    root/'worker8-startup.json',root/'worker8-allocation.json',root/'phase5-worker8-v5-141-launch.json',
    root/'prepared-phase5-worker8-v5-141/contract.json',root/'prepared-phase5-worker8-v5-141/task.json',
    root/'queue8/142-old-runtime-environment-probe.status.json',root/'runtime-environment-probe142-plan.json',
    root/'runtime-environment-probe142/rank0.json',root/'runtime-environment-probe142/rank8.json',
    root/'runtime_environment_probe142.py',root/'publish_runtime_probe142.py'}
trials={}
for group in state['groups'].values():
    for name,row in group['trials'].items():
        attempt=root/'campaign/attempts'/name
        for basename in ('attempt.json','source-manifest.json','plan.json','report.json','reused-build.json','benchmark-000.log','independent-000.log'):
            path=attempt/basename
            if path.is_file():selected.add(path)
        path=attempt/'measurements/full12/result.json'
        if path.is_file():selected.add(path)
        path=root/'141-phase5-worker8-v5-runtime-audit'/(name+'.json')
        if path.is_file():selected.add(path)
        item=dict(status=row['status'])
        if row['status']=='measured':
            report=read(attempt/'report.json');v=report['verification']
            assert report['complete']and report['measurements_complete']and v['complete']and v['passed']and v['columns']==12
            assert report['library_sha256']=='d8b2e05221920ca2c34e102f83d7fa468cbaa421dec835624f31cdaa07a01a82'
            assert report['source_manifest_sha256']=='78b429dc13a8b113792aa45bd27fc93134a8c4b39359da9ade05558c93d590ae'
            assert math.isfinite(v['max_true_residual'])and v['max_true_residual']<=1e-8
            assert len(v['solution_relative_errors'])==12 and all(math.isfinite(x)and x<=1e-6 for x in v['solution_relative_errors'])
            samples=[r['wall_seconds']for r in report['samples']if not r['warmup']]
            item.update(steady_seconds=samples,median_seconds=statistics.median(samples),
                scalar_max_residual=v['max_true_residual'],gold_max_relative_error=v['solution_relative_error'],
                report_sha256=sha(attempt/'report.json'),configuration=report['configuration'])
        trials[name]=item
out=root/'exports/phase5-worker8-141-closed';out.mkdir(parents=True,exist_ok=False)
summary=dict(complete=False,task_terminal=True,status='failed',best_unchanged='052-reduce-on',
    fixed_team=state['groups']['fixed-team'].get('decision'),trials=trials,
    runtime_conclusion='Incomplete: old-default failed before original setup; no runtime-group adoption or performance conclusion',
    attribution='Frozen bench applies explicit context LD_LIBRARY_PATH after MPI launch. v5 incorrectly added MPI prefix even for an explicit override. New code must model both cases and preserve actual sidecars.',
    ordinary_failed_case_samples=0,large_arrays_opened=False,original_files_modified=False)
integrity.write_json_private(out/'summary.json',summary);selected.add(out/'summary.json')
rows=[];archive=out/'evidence.tar.gz'
with tarfile.open(archive,'x:gz')as tar:
    for path in sorted(selected):
        assert path.is_relative_to(root)and path.is_file()and not path.is_symlink()and path.stat().st_size<16*1024**2
        original_sha=sha(path);payload=source_bytes(path,original_sha)
        if path.suffix=='.json':
            payload=(json.dumps(redaction.redact(json.loads(payload)),indent=2)+'\n').encode()
        else:payload=redaction.redact(payload.decode()).encode()
        name=str(path.relative_to(root));member=tarfile.TarInfo(name);member.size=len(payload);member.mode=0o600
        tar.addfile(member,io.BytesIO(payload))
        rows.append(dict(path=name,original_sha256=original_sha,export_sha256=hashlib.sha256(payload).hexdigest(),bytes=len(payload),
            transformation='Existing exporter redact; JSON formatted; originals untouched'))
integrity.write_json_private(out/'manifest.json',dict(files=rows))
receipt=dict(complete=True,experiment_complete=False,task_status='failed',archive=str(archive),archive_sha256=sha(archive),
    archive_bytes=archive.stat().st_size,files=len(rows),manifest_sha256=sha(out/'manifest.json'),summary_sha256=sha(out/'summary.json'))
integrity.write_json_private(out/'receipt.json',receipt)
print(json.dumps(receipt),flush=True)
