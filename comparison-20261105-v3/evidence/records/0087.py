import hashlib,io,json,tarfile
from pathlib import Path
root=Path('/home/share/nsls_lwb/.cache/fair-solve-20261105-v3');old=root.with_name('fair-solve-20261105-v2')
assert json.loads((root/'summary.json').read_text())['complete']
assert json.loads((root/'compute-complete.json').read_text())['complete']
out=root/'export';out.mkdir(exist_ok=False);paths=[]
for folder,label in((root,'v3'),(old,'v2')):
    for p in folder.rglob('*'):
        if not p.is_file()or p.is_symlink()or p.suffix not in('.json','.log','.py','.sh','.txt'):continue
        rel=p.relative_to(folder)
        if rel.parts[0]in('input','build-login','export')or p.stat().st_size>20*1024**2:continue
        paths.append((p,label+'/'+str(rel)))
rows=[]
with tarfile.open(out/'evidence.tar.gz','x:gz')as tar:
    for p,rel in sorted(paths):
        raw=p.read_bytes();entry=tarfile.TarInfo(rel);entry.size=len(raw);entry.mode=0o600;tar.addfile(entry,io.BytesIO(raw))
        rows.append(dict(path=rel,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
m=dict(complete=True,files=rows,archive_sha256=hashlib.sha256((out/'evidence.tar.gz').read_bytes()).hexdigest())
(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps(dict(complete=True,files=len(rows),archive_sha256=m['archive_sha256'])),flush=True)
