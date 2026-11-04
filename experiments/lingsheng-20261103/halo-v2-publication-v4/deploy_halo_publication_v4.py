import hashlib,json,tarfile
from pathlib import Path
root=Path('/home/share/nsls_lwb/.cache/mg-opt-20261103')
archive=root/'halo-v2-trial-publication-v4-helpers.tar.gz'
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='235bb615e288f783648fb7039477f28191e699981627ff9ca90a2bd2714a5ed0'
out=root/'aux-halo-v2-publication-v4';out.mkdir(exist_ok=False)
with tarfile.open(archive,'r:gz')as t:
 for m in t.getmembers():
  p=Path(m.name);assert m.isfile() and not p.is_absolute()and '..'not in p.parts
  f=out/p;f.parent.mkdir(parents=True,exist_ok=True)
  with f.open('xb')as w:w.write(t.extractfile(m).read())
mp=out/'halo-v2-trial-publication-v4-helpers.json'
assert hashlib.sha256(mp.read_bytes()).hexdigest()=='60f0cd04049a98aed888e393fa0fdae6fa2826798d18604ac9be236ab1b03e9f'
manifest=json.loads(mp.read_text())
for name,sha in manifest['files'].items():assert hashlib.sha256((out/name).read_bytes()).hexdigest()==sha
print(json.dumps(dict(complete=True,deployed=True,queued=False,files=len(manifest['files']),manifest_sha256=hashlib.sha256(mp.read_bytes()).hexdigest())))
