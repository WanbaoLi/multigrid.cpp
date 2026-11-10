"""Verify every exported evidence payload against the frozen remote manifest."""
import hashlib,json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent/'evidence'
manifest=json.loads((root/'evidence-manifest.json').read_text())
assert manifest['complete']
for row in manifest['files']:
 path=root/row['path']
 assert path.resolve().is_relative_to(root.resolve())
 data=(subprocess.check_output(['git','-C',str(root.parents[2]),'show','HEAD:'+path.relative_to(root.parents[2]).as_posix()])
       if '--git' in sys.argv else path.read_bytes())
 assert len(data)==row['size'] and hashlib.sha256(data).hexdigest()==row['sha256'],row['path']
print('PASS:',len(manifest['files']),'exported payloads')
