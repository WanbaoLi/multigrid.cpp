"""Export closed actual ARM Clover qualification without hashing scientific fields."""
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
def sha(p):return integrity.read_dual(p)['openssl_sha256']
def read(p):return json.loads(source_bytes(p,sha(p)))
name='158-clover-arm-qualify-worker13';statepath=root/(name+'-state.json');state=read(statepath)
statuspath=root/'queue13'/(name+'.status.json');status=read(statuspath)
assert state['complete']and state['status']=='passed'and state['actual_sve_widths']==[16,32,64]and state['selected_tests']==32
assert status['status']=='passed'and status['returncode']==0 and status['cleanup']['complete']and not status['cleanup']['surviving_pids']
owner=root/'campaign-clover-reuse-v1/attempts/000-arm-clover-tests';record=read(owner/'attempt.json')
assert record['snapshot']==state['snapshot']and record['snapshot']['git_head']=='861613c703117c6b5b671e245a7142e217b09501'
selected={statepath,statuspath,root/'queue13'/(name+'.finished.json'),root/'queue13'/(name+'.log'),root/(name+'-launch.json'),
    root/'worker13-startup.json',root/'worker13-allocation.json',owner/'attempt.json',owner/'source-manifest.json'}
for row in record['stages'].values():
    assert row['status']=='passed'and row['returncode']==0 and row['cleanup']['complete']and not row['cleanup']['surviving_pids']
    sha(owner/row['log']);selected.add(owner/row['log'])
selected.update(p for p in(owner/'codegen').iterdir()if p.is_file())
for directory in('prepared-clover158-worker13','prepared-clover159-worker13','prepared-clover160-worker13'):
    selected.update(p for p in(root/directory).iterdir()if p.is_file()and p.suffix=='.json')
for n in('159-clover-full12-worker13','160-clover-full12-worker13'):
    selected.add(root/(n+'-launch.json'))
failed=read(root/'queue13/159-clover-full12-worker13.status.json');assert failed['status']=='failed'and failed['cleanup']['complete']and not failed['cleanup']['surviving_pids']
for ext in('.status.json','.finished.json','.log'):selected.add(root/'queue13'/('159-clover-full12-worker13'+ext))
for n in('arm_clover_qualify_v1.py','clover_codegen_audit.py','phase6_sve_probe.py','arm-clover-v1-files.json'):
    selected.add(root/'aux-arm-clover-v1'/n)
for n in('prepare_clover158_worker13.py','prepare_clover159_worker13.py','prepare_clover160_worker13.py','clover_full12_worker13_v1.py',
    'clover_full12_worker13_v2.py','test_clover_full12_worker13_v1.py','check_clover160_dependencies.py','export_clover158.py'):
    selected.add(root/n)
out=root/'exports/clover158-qualified';out.mkdir(parents=True,exist_ok=False)
summary=dict(complete=True,passed=True,physical_full12=False,ordinary_performance=False,source_head=state['source_head'],
    library_sha256=state['library_sha256'],source_manifest_sha256=state['snapshot']['source_manifest_sha256'],host=state['host'],
    allocation=state['allocation'],selected_ctest=32,actual_sve_dense_and_mpi2_widths=[16,32,64],task_cleanup=status['cleanup'],
    failed159_preserved='Wrong queue12 metadata dependency path, before experiment state/attempt or numerical launch. New160 uses shared path helper and actual closed158 dependency integration check. Source/binary/tolerance unchanged.')
integrity.write_json_private(out/'summary.json',summary);selected.add(out/'summary.json')
spec=importlib.util.spec_from_file_location('redactor',root/'source/tools/optimization/export_evidence.py');redactor=importlib.util.module_from_spec(spec);spec.loader.exec_module(redactor)
rows=[]
with tarfile.open(out/'evidence.tar.gz','x:gz')as tar:
    for p in sorted(selected):
        assert p.is_relative_to(root)and not p.is_symlink()and p.stat().st_size<16*1024**2
        digest=sha(p);value=source_bytes(p,digest)
        if p.suffix=='.json':value=(json.dumps(redactor.redact(json.loads(value)),indent=2)+'\n').encode()
        else:value=redactor.redact(value.decode()).encode()
        rel=str(p.relative_to(root));m=tarfile.TarInfo(rel);m.size=len(value);m.mode=0o600;tar.addfile(m,io.BytesIO(value))
        rows.append(dict(path=rel,bytes=len(value),original_sha256=digest,export_sha256=hashlib.sha256(value).hexdigest(),transformation='Existing redactor; originals unchanged'))
integrity.write_json_private(out/'manifest.json',dict(files=rows));receipt=dict(complete=True,files=len(rows),archive_sha256=sha(out/'evidence.tar.gz'),archive_bytes=(out/'evidence.tar.gz').stat().st_size,manifest_sha256=sha(out/'manifest.json'))
integrity.write_json_private(out/'receipt.json',receipt);print(json.dumps(receipt),flush=True)
