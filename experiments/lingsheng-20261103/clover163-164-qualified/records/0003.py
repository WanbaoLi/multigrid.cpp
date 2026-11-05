"""Read an authenticated site startup and derive its queue without cloning names.

This is a read-only preparation helper. It never submits jobs, changes a worker,
loads a parallel runtime, or labels historical measurements as current evidence.
Use only after the site's existing login/compute startup authentication passes.
"""
import ast
import hashlib
import json
import math
from pathlib import Path
import re


def require(value,message):
    if not value:raise ValueError(message)


def pinned_bytes(path,expected):
    path=Path(path)
    require(path.is_absolute()and path==path.resolve(strict=True)and not path.is_symlink(),'Canonical regular input required')
    before=path.stat();require(path.is_file()and before.st_size<=1024**2,'Small metadata/source only')
    value=path.read_bytes();after=path.stat()
    require((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==
            (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)and len(value)==before.st_size,'Input changed while reading')
    require(re.fullmatch('[0-9a-f]{64}',expected or '')and hashlib.sha256(value).hexdigest()==expected,'Pinned input differs')
    return value


def load(startup_path,startup_sha,entry_path,allocation_path):
    """Derive queue from the exact entry whose hash the actual startup records."""
    startup_path=Path(startup_path);entry_path=Path(entry_path);allocation_path=Path(allocation_path)
    startup=json.loads(pinned_bytes(startup_path,startup_sha))
    require(startup.get('complete')is True,'Compute startup/preflight must complete')
    root=startup_path.parent
    require(entry_path.parent==allocation_path.parent==root,'Allocation assets must share their authenticated root')
    entry=pinned_bytes(entry_path,startup['entry_sha256']).decode()
    constants={}
    for node in ast.parse(entry).body:
        if isinstance(node,ast.Assign)and len(node.targets)==1 and isinstance(node.targets[0],ast.Name)and node.targets[0].id in('QUEUE','ALLOCATION','HOST'):
            constants[node.targets[0].id]=ast.literal_eval(node.value)
    queue=constants.get('QUEUE')
    require(isinstance(queue,str)and re.fullmatch('queue[0-9]+',queue),'Entry must bind one literal queue')
    require(constants.get('ALLOCATION')==startup['allocation']and constants.get('HOST')==startup['host'],'Entry and actual startup epoch differ')
    allocation=json.loads(pinned_bytes(allocation_path,startup['allocation_record_sha256']))
    job=allocation['scheduler_authentication']['job']
    require(str(job['jobId'])==startup['scheduler_job']==allocation['scheduler_job']and job['taskExecNodes']==startup['host'],'Authenticated scheduler identity differs')
    require(allocation['allocation']==startup['allocation']and allocation['complete']is True,'Login and compute allocation differ')
    cpus=startup['before_worker_exec_parent_state']['cpus']
    require(cpus==sorted(set(cpus))and cpus and all(type(c)is int and c>=0 for c in cpus),'Actual parent CPU set required')
    require(startup['before_worker_exec_parent_state']['gomp_kupl_loaded']is False,'Worker parent loaded a parallel runtime')
    groups=job['resGroups'];require(len(groups)==1 and groups[0]['resAlloc']['cpu']==len(cpus)and job['exclusive']is True,'Exact exclusive CPU allocation required')
    deadline=startup['safe_deadline_epoch']
    require(isinstance(deadline,(int,float))and math.isfinite(deadline),'Finite safe deadline required')
    return dict(complete=True,root=str(root),queue=str(root/queue),host=startup['host'],allocation=startup['allocation'],
        scheduler_job=startup['scheduler_job'],cpus=cpus,safe_deadline_epoch=deadline,
        startup_path=str(startup_path),startup_sha256=startup_sha,entry_path=str(entry_path),entry_sha256=startup['entry_sha256'],
        allocation_path=str(allocation_path),allocation_sha256=startup['allocation_record_sha256'])


def dependency(context,task_id,status_sha,state_path,state_sha,source_head=None):
    """Check current-epoch qualification through the derived queue, never another."""
    require(re.fullmatch('[a-z0-9][a-z0-9_-]{0,79}',task_id or ''),'Safe task identity required')
    status_path=Path(context['queue'])/(task_id+'.status.json')
    status=json.loads(pinned_bytes(status_path,status_sha));state=json.loads(pinned_bytes(Path(state_path),state_sha))
    require(status['status']=='passed'and status['returncode']==0 and status['host']==context['host'],'Dependency task did not pass on this host')
    require(status['cleanup']['complete']is True and status['cleanup']['surviving_pids']==[],'Dependency descendants remain')
    require(state['complete']is True and state['status']in('passed','complete')and state['host']==context['host']and state['allocation']==context['allocation'],'Dependency belongs to another or unfinished epoch')
    if source_head is not None:require(state['source_head']==source_head,'Dependency source differs')
    return dict(complete=True,status_path=str(status_path),status_sha256=status_sha,state_path=str(state_path),state_sha256=state_sha,
        task_id=task_id,queue=context['queue'],allocation=context['allocation'])
