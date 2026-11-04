"""Prepare a parent-proof envelope around an unchanged reviewed task."""
import argparse
from pathlib import Path
import sys
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103');sys.path.insert(0,str(root/'aux-solve-profile-v7'))
import file_integrity as integrity
from raw_scalar_helper import source_bytes
import json
def sha(path,expected=None):return integrity.read_dual(path,expected)['openssl_sha256']
def read(path,expected=None):return json.loads(source_bytes(path,sha(path,expected)))
def main():
    p=argparse.ArgumentParser();p.add_argument('--id',required=True);p.add_argument('--task',type=Path,required=True)
    p.add_argument('--task-sha',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert a.id in('150-best-solve-profile-worker10','148-halo-v2-full-worker10','149-clover-arm-qualify-worker10')
    task=read(a.task,a.task_sha);assert task['argv'][0]=='/home/share/nsls_lwb/.cache/multigrid-arm-20261025-env/bin/python'and task['argv'][1]=='-u'
    assert not list((root/'queue10').glob(a.id+'.*'))
    guard=root/'worker10_live_task_guard_v2.py'
    plan=dict(complete=True,id=a.id,guard_sha256=sha(guard),original_task=dict(path=str(a.task),sha256=a.task_sha),
        original_entry_sha256=sha(Path(task['argv'][2])),task_timeout_seconds=task['timeout'],numerical_or_acceptance_gate_changes=False)
    a.output.mkdir(exist_ok=False)
    integrity.write_json_private(a.output/'guard-plan.json',plan)
    wrapped=dict(task,argv=[*task['argv'][:2],str(guard),'--plan',str(a.output/'guard-plan.json'),'--plan-sha',sha(a.output/'guard-plan.json')])
    integrity.write_json_private(a.output/'task.json',wrapped)
    print(json.dumps(dict(prepared_not_queued=True,original_task_sha256=a.task_sha,guard_plan_sha256=sha(a.output/'guard-plan.json'),task_sha256=sha(a.output/'task.json'))),flush=True)
if __name__=='__main__':main()
