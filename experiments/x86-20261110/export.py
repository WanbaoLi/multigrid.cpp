import hashlib,json,statistics,subprocess,tarfile
from pathlib import Path
r=Path('/public2/home/lwb_720/.cache/mg-x86-20261110')
assert(r/'confirmation-complete.json').exists()
assert not list((r/'queue').glob('*.running.json')) and not list((r/'queue').glob('*.ready.json'))
provenance=[]
for source,lib in ((Path('/public2/home/lwb_720/.cache/mg-opt-delivery-833-20261105/source'),Path('/public2/home/lwb_720/.cache/mg-opt-delivery-833-20261105/campaign/attempts/000-delivery-tests/build/liblqcd_cpu.so')),
                   (r/'source',r/'build/liblqcd_cpu.so'),(r/'source-projector',r/'build-projector/liblqcd_cpu.so'),(r/'source-tile',r/'build-tile/liblqcd_cpu.so')):
 tracked=subprocess.check_output(['git','-C',str(source),'ls-files','-z']).decode().split('\0')
 files={p:hashlib.sha256((source/p).read_bytes()).hexdigest()for p in tracked if p}
 provenance.append(dict(source=str(source),commit=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip(),
     status=subprocess.check_output(['git','-C',str(source),'status','--porcelain'],text=True),
     tracked_files=files,manifest_sha256=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
     library=str(lib),library_sha256=hashlib.sha256(lib.read_bytes()).hexdigest()))
with(r/'source-provenance.json').open('x')as f:json.dump(dict(sources=provenance,
    note='Driver snapshot-sha argument stored the Git commit in the result source_manifest_sha256 field. That field is a commit identifier, not a file-manifest hash. This separate tracked-file manifest provides the actual source digests; original measurements are preserved.'),f,indent=2)
rows=[]
for mode in ('old-control','new0','new1','new2','old-closing','proj0','proj1','old-projector-closing','tile0','tile16','tile64','old-tile-closing','new2-confirm2','old-final-control'):
 s=json.loads((r/mode/'full12/result.json').read_text());v=s['verification']
 assert v['passed'] and v['columns']==12 and v['max_true_residual']<=1e-8 and v['solution_relative_error']<=1e-6
 times=[x['wall_seconds'] for x in s['samples'] if not x['warmup']]
 rows.append(dict(mode=mode,first=s['samples'][0]['wall_seconds'],steady=times,median=statistics.median(times),
  max_residual=v['max_true_residual'],max_solution_error=v['solution_relative_error'],library_sha256=s['library_sha256'],
  iterations=[[st['iterations']for st in x['stats']]for x in s['samples']],
  refinement_steps=[[st['refinement_steps']for st in x['stats']]for x in s['samples']]))
summary=dict(complete=True,rows=rows,control_drift=abs(rows[0]['median']-rows[-1]['median'])/min(rows[0]['median'],rows[-1]['median']))
with(r/'summary.json').open('x')as f:json.dump(summary,f,indent=2)
candidate=min((row for row in rows if not row['mode'].startswith('old')),key=lambda row:min(row['steady']))
decision=dict(promoted=False,stable_source_commit=provenance[0]['commit'],stable_library=str(provenance[0]['library']),
 stable_library_sha256=provenance[0]['library_sha256'],candidate_fastest_observed_mode=candidate['mode'],
 candidate_fastest_observed_seconds=min(candidate['steady']),
 reason='Paired-row first-process gain did not repeat in the independent confirmation; signed projectors and RHS site tiles did not clearly beat original controls. Retain the reliable original833 implementation. This is a bounded tested set, not a global optimum.')
with(r/'best.json').open('x')as f:json.dump(decision,f,indent=2)
with(r/'register-assembly.log').open('x')as f:
 subprocess.run(['objdump','-d','-C','--start-address=0x2a390','--stop-address=0x2b100',str(r/'build/liblqcd_cpu.so')],stdout=f,stderr=subprocess.STDOUT,check=True)
files=set(r.glob('*.py'))|set(r.glob('*.sh'))|set(r.glob('*.json'))|set(r.glob('*.log'))
files|=set((r/'queue').glob('*.json'))|set((r/'queue').glob('*.log'))
files|=set((r/'perf-v2').glob('*.json'))|set((r/'perf-v2').glob('*.txt'))|set((r/'perf-v2').glob('*.log'))
for mode in ('old-control','new0','new1','new2','old-closing','proj0','proj1','old-projector-closing','tile0','tile16','tile64','old-tile-closing','new2-confirm2','old-final-control','diagnostic-v2'):
 d=r/mode/'full12';files|=set(d.glob('*.json'))|set((d/'independent').glob('*.json'))|set((d/'independent').glob('*.log'))|set((d/'independent').glob('*.residual'))
for name in ('build','build-projector','build-tile'):
 files|={r/name/'CMakeCache.txt',r/name/'Testing/Temporary/LastTest.log'}
manifest=[]
for p in sorted(files):
 if p.is_file():
  assert p.stat().st_size<30*1024**2,p
  manifest.append(dict(path=str(p.relative_to(r)),size=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
with(r/'evidence-manifest.json').open('x')as f:json.dump(dict(complete=True,files=manifest),f,indent=2)
with tarfile.open(r/'evidence.tar.gz','x:gz')as out:
 for row in manifest:out.add(r/row['path'],arcname=row['path'],recursive=False)
 out.add(r/'evidence-manifest.json',arcname='evidence-manifest.json')
print(json.dumps(summary,indent=2))
