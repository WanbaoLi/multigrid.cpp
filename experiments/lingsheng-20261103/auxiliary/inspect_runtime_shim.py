#!/usr/bin/env python3
"""Create only a private GOMP symlink and inspect loader traces on ls login.

No solver entry point, ctypes load, MPI launch, or OpenMP region is executed.
The returned manifest is local evidence for the separately reviewed controller.
"""
import argparse
import json
from pathlib import Path
import shlex
import subprocess


REMOTE = r'''
import hashlib,json,os,pathlib,shutil,subprocess,sys
p=json.loads(PAYLOAD)
root=pathlib.Path(p['root']); directory=pathlib.Path(p['directory'])
sys.path.insert(0,str(root));import file_integrity as integrity
old=pathlib.Path('/work_ssd/system/os_jasmine_v01/vroot/usr/lib64/libgomp.so.1.0.0')
sdk=pathlib.Path('/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001/compiler/gcc/lib64/libgomp.so.1.0.0')
old_sha='252cbdb01681c56080bba6a94d3461bf5704a03f987a42517341ad464d19da27'
sdk_sha='642029e630ff46a26f12343760e75c745354ada14ad7eab980e85e35eaa149a1'
integrity.read_dual(old,old_sha);integrity.read_dual(sdk,sdk_sha)
assert directory.is_absolute() and not directory.is_relative_to(root)
if not directory.exists():directory.mkdir(mode=0o700)
assert not directory.is_symlink() and directory.stat().st_uid==os.getuid()
assert directory.stat().st_mode & 0o077==0
link=directory/'libgomp.so.1'
if not link.is_symlink() and not link.exists():link.symlink_to(old)
assert list(directory.iterdir())==[link] and link.is_symlink() and link.resolve(strict=True)==old
best=json.loads((root/'campaign/best.json').read_text())
library=root/'campaign/attempts'/best['attempt']/'artifacts/liblqcd_cpu.so'
integrity.read_dual(library,best['library_sha256'])
seed=json.loads((root/'queue6/090-best-profile-worker6.finished.json').read_text())
base=seed['environment']['LD_LIBRARY_PATH'];python=seed['argv'][0]
mpiexec='/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001/hmpi/bisheng/release/hmpi/bin/mpiexec'
assert pathlib.Path(mpiexec).is_file()
std=pathlib.Path('/home/share/test_mpi/my_software/hpckit/HPCKit/25.1.0.SPC001/compiler/gcc/lib64/libstdc++.so.6').resolve(strict=True)
std_sha=integrity.read_dual(std)['openssl_sha256']
def paths(text,prefix):
 out=set()
 for line in text.splitlines():
  words=(line.split('=>',1)[1] if '=>'in line else line).strip().split()
  if words and words[0].startswith('/') and pathlib.Path(words[0]).name.startswith(prefix):
   out.add(str(pathlib.Path(words[0]).resolve(strict=True)))
 return sorted(out)
checks=[]
probe="import json,os,pathlib;print(json.dumps(dict(allowed=sorted(os.sched_getaffinity(0)),gomp_maps=[line.split()[-1] for line in pathlib.Path('/proc/self/maps').read_text().splitlines() if 'libgomp.so' in line])))"
for label,search in [('sdk',base),('old',str(directory)+':'+base)]:
 env=dict(os.environ)
 for key in ('LD_PRELOAD','LD_DEBUG','LD_DEBUG_OUTPUT','PERF_COUNTER_ROOT'):env.pop(key,None)
 env.update(LD_LIBRARY_PATH=search,OMP_PROC_BIND='close',OMP_PLACES='cores')
 trace=subprocess.run(['ldd','-r',str(library)],env=env,cwd=str(root),text=True,capture_output=True,timeout=30)
 launcher=subprocess.run([python,'-c',probe],env=env,cwd=str(root),text=True,capture_output=True,timeout=30)
 actual=json.loads(launcher.stdout) if launcher.returncode==0 else None
 gomps=paths(trace.stdout,'libgomp.so');stds=paths(trace.stdout,'libstdc++.so')
 expected=str(old if label=='old' else sdk)
 ok=trace.returncode==0 and not any(x in trace.stdout+trace.stderr for x in ('not found','undefined symbol')) and gomps==[expected] and stds==[str(std)] and actual is not None and not actual['gomp_maps']
 closure=[]
 for executable in (python,mpiexec):
  traced=subprocess.run(['ldd','-r',str(pathlib.Path(executable).resolve(strict=True))],env=env,cwd=str(root),text=True,capture_output=True,timeout=30)
  traced_gomp=paths(traced.stdout,'libgomp.so')
  closure_ok=traced.returncode==0 and not any(x in traced.stdout+traced.stderr for x in ('not found','undefined symbol')) and not traced_gomp
  ok=ok and closure_ok
  closure.append(dict(path=str(pathlib.Path(executable).resolve(strict=True)),passed=closure_ok,
   returncode=traced.returncode,resolved_libgomp=traced_gomp,stdout=traced.stdout,stderr=traced.stderr))
 checks.append(dict(label=label,passed=ok,ld_library_path=search,ld_preload_present=False,launcher_loader_closure=closure,
  ldd_r=dict(argv=['ldd','-r',str(library)],returncode=trace.returncode,stdout=trace.stdout,stderr=trace.stderr),
  resolved_libgomp=gomps,resolved_libstdcpp=stds,stdlib_launcher=dict(returncode=launcher.returncode,**(actual or {}))))
assert checks[0]['stdlib_launcher']['allowed']==checks[1]['stdlib_launcher']['allowed']
result=dict(protocol='phase5-single-gomp-search-directory-v1',complete=True,passed=all(x['passed']for x in checks),
 scope='Login loader relocation traces and pure stdlib child only; no solver/OpenMP/ctypes/MPI execution',
 root=str(root),directory=str(directory),link=str(link),link_target=str(old),directory_mode=oct(directory.stat().st_mode&0o777),
 old_gomp=dict(path=str(old),sha256=old_sha),sdk_gomp=dict(path=str(sdk),sha256=sdk_sha),
 sdk_stdcpp=dict(path=str(std),sha256=std_sha),base_ld_library_path=base,
 inspected_best=best,inspected_library=str(library),checks=checks,
 constructor_boundary='The single-directory search does not load GOMP in stdlib launcher. Constructor still executes if a later native import/dlopen needs GOMP; compute-node maps and thread affinity remain mandatory.')
print(json.dumps(result,indent=2))
assert result['passed']
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='/home/share/nsls_lwb/.cache/mg-opt-20261103')
    parser.add_argument('--directory',default='/home/share/nsls_lwb/.cache/runtime-oldgomp-only-20261104')
    parser.add_argument('--output',type=Path,default=Path('outputs/optimization-20261103/phase5-shim/loader-shim-manifest.json'))
    args=parser.parse_args()
    script=REMOTE.replace('PAYLOAD',repr(json.dumps(dict(root=args.root,directory=args.directory))))
    result=subprocess.run(['ssh','-n','ls','python3 -c '+shlex.quote(script)],text=True,capture_output=True,timeout=120)
    if result.returncode:
        raise RuntimeError(result.stderr+'\n'+result.stdout)
    evidence=json.loads(result.stdout)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    if args.output.exists():
        raise FileExistsError('Retain prior evidence; choose a fresh output')
    args.output.write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(output=str(args.output),passed=evidence['passed'],
        mappings=[dict(label=x['label'],gomp=x['resolved_libgomp'],std=x['resolved_libstdcpp'],
          launcher_allowed_count=len(x['stdlib_launcher']['allowed']))for x in evidence['checks']]),indent=2))


if __name__=='__main__':main()
