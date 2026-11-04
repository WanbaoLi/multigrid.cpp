"""Deploy new names and record actual predecessor evidence; never submit."""
import fcntl
import importlib.util
import json
from pathlib import Path
import subprocess
import tarfile
import time

import file_integrity as integrity

ROOT=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
ARCHIVE_SHA='58f8112657643348d7f16d3330c7bc9a90eed377293263ca544605421fde488b'
ENTRY_SHA='e820d32771f537f7dcca5134db453f71e38479921c019ce19559bca304cbe8e6'


def sha(path, expected=None):
    return integrity.read_dual(path,expected)['openssl_sha256']


def main():
    assert Path(__file__).resolve().parent==ROOT
    sha(ROOT/'file_integrity.py','34200de5efea2b362880886354c7436fdfb6300bb1c3730b57823aa8acebf427')
    sha(ROOT/'submit_worker8_terminal_v2.py',ENTRY_SHA)
    archive=ROOT/'worker8-preparation.tgz';sha(archive,ARCHIVE_SHA)
    with tarfile.open(archive)as tar:
        members=tar.getmembers()
        for member in members:
            assert member.isfile()and Path(member.name).name==member.name
            assert not (ROOT/member.name).exists()and not (ROOT/member.name).is_symlink(),member.name
        for member in members:
            integrity.write_private_new(ROOT/member.name,[tar.extractfile(member).read()])
    manifest=ROOT/'worker8-launch-manifest.json'
    for name,row in json.loads(manifest.read_text())['files'].items():sha(ROOT/name,row['sha256'])
    spec=importlib.util.spec_from_file_location('worker8_login',ROOT/'worker8_login_record.py')
    login=importlib.util.module_from_spec(spec);spec.loader.exec_module(login)
    import shutil
    previous,query=login.query(shutil.which('djob'),'2022100')
    assert previous['state']=='SUCCEEDED'and previous['exitCode']==0 and previous['jobExitCode']==0
    assert previous['jobName']=='mg-opt-worker7'and previous['taskExecNodes']=='cn19483'
    for name in ('queue7','queue8'):
        assert not list((ROOT/name).glob('*.running.json'))and not list((ROOT/name).glob('*.ready.json'))
    statuses={str(p):sha(p)for p in sorted((ROOT/'queue7').glob('*.status.json'))}
    assert statuses
    for path in statuses:
        value=json.loads(Path(path).read_text())
        assert value['status']in('passed','failed','timeout')and value['task_tag']
        assert value['cleanup']['complete']is True and value['cleanup']['surviving_pids']==[]
    with (ROOT/'queue7/worker.lock').open('r')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert (ROOT/'worker7.log').read_text().strip().splitlines()[-1]=='Bounded worker finished; no active task'
        proof=dict(complete=True,previous_job='2022100',worker_stopped=True,all_owned_tasks_cleaned=True,
            exit_kind='natural-idle',scheduler_end_time=previous['endTime'],scheduler_query=query,
            task_status_sha256=statuses,worker_log_sha256=sha(ROOT/'worker7.log'),
            idle_lock_observed_unheld=True,epoch=time.time(),stop_marker_synthesized=False)
        output=ROOT/'worker7-natural-idle-proof-v2.json';integrity.write_json_private(output,proof)
    plan=ROOT/'worker8-reviewed-submit-plan.json'
    argv=['python3',str(ROOT/'submit_worker8_terminal_v2.py'),'--root',str(ROOT),
        '--plan',str(plan),'--plan-sha',sha(plan),'--wrapper-manifest',str(manifest),
        '--wrapper-manifest-sha',sha(manifest),'--stop-proof',str(output),'--stop-proof-sha',sha(output)]
    result=subprocess.run(argv,capture_output=True,text=True,timeout=60)
    receipt=ROOT/'worker8-reviewed-dryrun-v2.json'
    integrity.write_json_private(receipt,dict(complete=result.returncode==0,argv=argv,returncode=result.returncode,
        stdout=result.stdout,stderr=result.stderr,entry_sha256=ENTRY_SHA))
    print(json.dumps(dict(dryrun=str(receipt),sha256=sha(receipt),returncode=result.returncode,
        stdout=result.stdout,stderr=result.stderr)),flush=True)
    assert result.returncode==0


if __name__=='__main__':main()
