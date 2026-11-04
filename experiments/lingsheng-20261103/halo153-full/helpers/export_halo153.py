"""Export completed three-case runtime confirmation evidence without scientific field reads."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import statistics
import sys
import tarfile
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103');sys.path.insert(0,str(root/'aux-solve-profile-v7'))
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
name='153-halo-v2-remainder-worker10';statepath=root/(name+'-state.json');state=read(statepath)
statuspath=root/'queue10'/(name+'.status.json');status=read(statuspath)
assert state['complete']and state['status']=='passed'and state['scope']=='full'and state['full_numerical_complete']and state['mpi_status']==state['sve_matrix_status']=='passed'
assert status['status']=='passed'and status['returncode']==0 and status['cleanup']['complete']and not status['cleanup']['surviving_pids']
recovery=state['ctest_recovery'];assert recovery['complete']and len(recovery['full_test_coverage'])==13 and len(recovery['completed_tests'])==11 and len(recovery['executed_remaining_tests'])==2
assert recovery['numerical_tests_or_limits_changed']is False
owner=root/'campaign-halo-v2/attempts/000-halo-v2-tests';record=read(owner/'attempt.json')
selected={statepath,statuspath,root/'queue10'/(name+'.finished.json'),root/(name+'-launch.json'),root/(name+'-actual-parent-guard-v4.json'),
    root/'worker10-startup.json',root/'worker10-allocation.json',owner/'attempt.json',owner/'source-manifest.json'}
for old in('148-halo-v2-full-worker10',):
    selected.update([root/(old+'-state.json'),root/(old+'-launch.json'),root/(old+'-actual-parent-guard-v2.json'),
        root/'queue10'/(old+'.status.json'),root/'queue10'/(old+'.finished.json')])
for directory in(root/'prepared-halo148-worker10',root/'prepared-halo148-live-v2',root/'prepared-halo153-worker10'):
    selected.update(p for p in directory.iterdir()if p.is_file()and p.suffix=='.json')
for key,row in record['stages'].items():
    if key=='mpi-numerical-ctest':assert row['status']=='timeout'and row['timeout_seconds']==1000
    else:assert row['status']=='passed'and row['returncode']==0
    assert row['cleanup']['complete']and not row['cleanup']['surviving_pids']
    selected.add(owner/row['log'])
for relative in state['codegen_files']:selected.add(root/'campaign-halo-v2'/relative)
for row in recovery['pinned_files']:
    p=Path(row['path'])
    if p.suffix in('.json','.log','.txt','.cmake','.py'):selected.add(p)
for width in(16,32,64):
    ranks=state['sve_matrix'][str(width)]['ranks']
    assert ranks['complete']and ranks['library_sha256']==state['library_sha256']and len(ranks['ranks'])==4 and all(r['actual_bytes']==width for r in ranks['ranks'])
summary=dict(complete=True,passed=True,physical_full12_verified=False,ordinary_timing=False,source_head=state['source_head'],
    source_manifest_sha256=state['snapshot']['source_manifest_sha256'],library_sha256=state['library_sha256'],host=state['host'],allocation=state['allocation'],
    reused_original_compile_and_unit_checkpoints=True,full_mpi_tests=13,previously_completed_mpi_tests=11,fresh_remainder_tests=2,
    original148_status='failed whole-suite1000second timeout, preserved',completed_scope153='all13 coverage plus compiled SVE audit and dense/MPI4 widths16/32/64',
    actual_vector_lengths=[16,32,64],ctest_recovery=recovery,task_cleanup=status['cleanup'],
    actual_numerical_source_edited=False,binary_rebuilt=False,main_best_modified=False,
    next='Separate ordinary full12 task154; no physical score inferred from small-input qualification')
spec=importlib.util.spec_from_file_location('existing_redactor',root/'source/tools/optimization/export_evidence.py')
redactor=importlib.util.module_from_spec(spec);spec.loader.exec_module(redactor)
out=root/'exports/halo153-full';out.mkdir(parents=True,exist_ok=False)
integrity.write_json_private(out/'summary.json',summary);selected.add(out/'summary.json');rows=[]
with tarfile.open(out/'evidence.tar.gz','x:gz')as tar:
    for path in sorted(selected):
        assert path.is_file()and not path.is_symlink()and path.is_relative_to(root)
        digest=sha(path);value=payload(path,digest)
        if path.suffix=='.json':value=(json.dumps(redactor.redact(json.loads(value)),indent=2)+'\n').encode()
        else:value=redactor.redact(value.decode()).encode()
        rel=str(path.relative_to(root));member=tarfile.TarInfo(rel);member.size=len(value);member.mode=0o600;tar.addfile(member,io.BytesIO(value))
        rows.append(dict(path=rel,original_sha256=digest,export_sha256=hashlib.sha256(value).hexdigest(),bytes=len(value),transformation='Existing redactor; originals unchanged'))
integrity.write_json_private(out/'manifest.json',dict(files=rows));receipt=dict(complete=True,passed=True,files=len(rows),
    archive=str(out/'evidence.tar.gz'),archive_sha256=sha(out/'evidence.tar.gz'),archive_bytes=(out/'evidence.tar.gz').stat().st_size,manifest_sha256=sha(out/'manifest.json'))
integrity.write_json_private(out/'receipt.json',receipt);print(json.dumps(receipt),flush=True)
