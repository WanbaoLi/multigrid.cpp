"""Export closed small records; exclude scientific fields and binaries."""
import hashlib,io,json,tarfile
from pathlib import Path
root=Path('/home/share/nsls_lwb/.cache/fair-solve-20261105-v2')
for node in('login','compute'):
    assert json.loads((root/(node+'-sequence-complete.json')).read_text())['complete']
    for p in(root/(node+'-queue')).glob('*.status.json'):
        r=json.loads(p.read_text());assert r['status']=='passed'and r['cleanup']['complete']and not r['cleanup']['surviving_pids']
paths=[]
for p in root.rglob('*'):
    if not p.is_file()or p.is_symlink()or 'build-login'in p.parts:continue
    rel=p.relative_to(root)
    if rel.parts[0]in('input','export'):continue
    if p.suffix in('.py','.sh','.json','.log','.txt')and p.stat().st_size<20*1024**2:paths.append(p)
out=root/'export';out.mkdir(exist_ok=False);rows=[]
with tarfile.open(out/'evidence.tar.gz','x:gz')as tar:
    for p in sorted(paths):
        raw=p.read_bytes();rel=str(p.relative_to(root));entry=tarfile.TarInfo(rel);entry.size=len(raw);entry.mode=0o600;tar.addfile(entry,io.BytesIO(raw))
        rows.append(dict(path=rel,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
manifest=dict(complete=True,files=rows,archive_sha256=hashlib.sha256((out/'evidence.tar.gz').read_bytes()).hexdigest())
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(dict(complete=True,files=len(rows),archive_sha256=manifest['archive_sha256'])),flush=True)
