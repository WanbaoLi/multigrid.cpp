"""Export closed small evidence, retaining full arrays on the compute filesystem."""
import hashlib, json, subprocess, tarfile
from pathlib import Path
root=Path('/home/share/nsls_lwb/.cache/fair-solve-20261105-v4')
assert (root/'sap-complete.json').exists()
assert not list((root/'compute-queue').glob('*.running.json'))
assert not list((root/'compute-queue').glob('*.ready.json'))
paths=set(root.glob('*.py'))|set(root.glob('*.sh'))|set(root.glob('*.log'))
paths|=set(root.glob('*summary*.json'))|set(root.glob('*complete*.json'))|set(root.glob('*startup*.json'))
paths|=set((root/'compute-queue').glob('*.json'))|set((root/'compute-queue').glob('*.log'))
paths|=set((root/'results').glob('*/result.json'))
for folder in ('reliable-validation','sap-validation'):
    for suffix in ('*.json','*.log','*.residual'):
        paths|=set((root/folder).glob(suffix))
builds=[]
for name in ('outer','reliable','sap'):
    source=root/('source-'+name);build=root/('build-'+name)
    lib=build/'liblqcd_cpu.so'
    builds.append(dict(name=name, source_commit=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip(),
        source_dirty=subprocess.check_output(['git','-C',str(source),'status','--porcelain'],text=True),
        library_sha256=hashlib.sha256(lib.read_bytes()).hexdigest()))
    paths|={build/'CMakeCache.txt',build/'Testing/Temporary/LastTest.log'}
manifest=[]
for path in sorted(paths):
    if path.is_file():
        assert path.stat().st_size<20*1024*1024,path
        data=path.read_bytes()
        manifest.append(dict(path=str(path.relative_to(root)),size=len(data),sha256=hashlib.sha256(data).hexdigest()))
meta=root/'evidence-manifest.json'
with meta.open('x') as f:json.dump(dict(complete=True,files=manifest,builds=builds),f,indent=2)
with tarfile.open(root/'evidence-v4.tar.gz','x:gz') as archive:
    for row in manifest:
        archive.add(root/row['path'],arcname=row['path'],recursive=False)
    archive.add(meta,arcname=meta.name,recursive=False)
print(len(manifest),'files',flush=True)
