"""Verify every exported evidence payload against the frozen remote manifest."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent/'evidence'
manifest=json.loads((root/'evidence-manifest.json').read_text())
assert manifest['complete']
for row in manifest['files']:
 path=root/row['path']
 assert path.resolve().is_relative_to(root.resolve())
 data=path.read_bytes()
 assert len(data)==row['size'] and hashlib.sha256(data).hexdigest()==row['sha256'],row['path']
print('PASS:',len(manifest['files']),'exported payloads')
